#!/usr/bin/env bash
# Install one tested image; keep runtime secrets and nginx certificates on the host.
set -Eeuo pipefail
release=${1:?release directory required}
image=${2:?image tag required}
[[ "$release" =~ ^/opt/histree/releases/[a-zA-Z0-9_-]+$ && "$image" =~ ^histree-api:[a-f0-9]{40}$ ]] || exit 2
[[ -d "$release" && ! -L "$release" && -f /opt/histree/runtime.env ]]
exec 9>/opt/histree/release.lock
flock -n 9 || { echo 'Another release is in progress' >&2; exit 1; }
cd "$release"
sha256sum -c image.tar.gz.sha256
docker load -i image.tar.gz
[[ $(docker image inspect --format '{{.Architecture}}' "$image") == amd64 ]]
[[ $(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image") == "${image#histree-api:}" ]]
# Verify the exact native harness before touching the running container.
timeout 90s docker run --rm --memory=1400m --pids-limit=256 "$image" node apps/api/dsh/smoke.mjs
timeout 90s docker run --rm --memory=1400m --pids-limit=256 -e HISTREE_REMOTE_SMOKE=1 "$image" node apps/api/dsh/smoke.mjs
timeout 90s docker run --rm --memory=1400m --pids-limit=256 "$image" node apps/api/dsh/guess-smoke.mjs
nginx -t
previous=$(cat /opt/histree/current-release 2>/dev/null || true)
[[ -z "$previous" || "$previous" =~ ^/opt/histree/releases/[a-zA-Z0-9_-]+$ ]]
if [[ -n "$previous" ]]; then test -f "$previous/.image"; test -f "$previous/compose.yml"; fi
runtime_before=$(sha256sum /opt/histree/runtime.env | cut -d' ' -f1)
rollback() {
  status=$?
  trap - ERR
  echo 'Release failed; restoring previous application' >&2
  if [[ -n "$previous" ]]; then
    HISTREE_IMAGE=$(cat "$previous/.image") docker compose -p histree -f "$previous/compose.yml" up -d --wait --wait-timeout 120 || echo 'Rollback failed; inspect host logs' >&2
  else
    docker compose -p histree -f compose.yml down || true
  fi
  exit "$status"
}
trap rollback ERR
export HISTREE_IMAGE="$image"
docker compose -p histree -f compose.yml up -d --wait --wait-timeout 120
docker cp release-manifest.json histree-api:/tmp/histree-release-manifest.json
docker exec -i histree-api node --input-type=module - http://127.0.0.1:3000 /tmp/histree-release-manifest.json < verify.mjs
[[ $(sha256sum /opt/histree/runtime.env | cut -d' ' -f1) == "$runtime_before" ]]
printf '%s\n' "$image" > .image
printf '%s\n' "$previous" > previous-release
printf '%s\n' "$release" > /opt/histree/current-release.next
mv /opt/histree/current-release.next /opt/histree/current-release
trap - ERR
printf 'Released %s\n' "$image"
# Only collect after successful acceptance and pointer update. Cleanup failure must
# not trigger application rollback; leave the healthy release running and fail CI.
if ! python3 "$release/cleanup-releases.py" --apply --lock-fd 9; then
  echo 'Retention failed; deployed app remains running. Inspect cleanup-audits.' >&2
  exit 1
fi
