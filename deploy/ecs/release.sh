#!/usr/bin/env bash
set -euo pipefail
release=${1:?release directory required}
image=${2:?image tag required}
[[ "$release" == /opt/histree/releases/* && "$image" =~ ^histree-api:[a-f0-9]+$ ]] || exit 2
cd "$release"
sha256sum -c image.tar.gz.sha256
docker load -i image.tar.gz
[[ $(docker image inspect --format '{{.Architecture}}' "$image") == amd64 ]]
# Check the exact new image before replacing the running API.
docker run --rm --memory=1400m --pids-limit=256 "$image" node apps/api/dsh/smoke.mjs
previous=$(cat /opt/histree/current-release 2>/dev/null || true)
export HISTREE_IMAGE="$image"
if docker compose -p histree -f compose.yml up -d --wait --wait-timeout 120; then
  printf '%s\n' "$release" > /opt/histree/current-release
  printf '%s\n' "$image" > .image
else
  if [[ -n "$previous" && -f "$previous/.image" ]]; then
    HISTREE_IMAGE=$(cat "$previous/.image") docker compose -p histree -f "$previous/compose.yml" up -d --wait --wait-timeout 120
  fi
  exit 1
fi
curl --fail --silent http://127.0.0.1:3000/api/v1/ask/status
