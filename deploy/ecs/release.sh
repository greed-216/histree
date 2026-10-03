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
# Add only the three game routes to the existing HTTPS gateway, preserving certificates.
if [[ -f /etc/nginx/conf.d/histree.conf ]]; then
  cp /etc/nginx/conf.d/histree.conf "$release/nginx.previous"
  python3 - <<'PY_NGINX'
from pathlib import Path
config = Path('/etc/nginx/conf.d/histree.conf')
text = config.read_text()
marker = '  location = /api/v1/ask {'
block = '  location ~ ^/api/v1/ask/guess/(status|start|act)$ {\n    proxy_pass http://127.0.0.1:3000;\n    proxy_http_version 1.1;\n    proxy_set_header Host $host;\n    proxy_set_header X-Forwarded-For $remote_addr;\n    proxy_set_header X-Forwarded-Proto https;\n    proxy_read_timeout 180s;\n  }\n'
if 'location ~ ^/api/v1/ask/guess/(status|start|act)$' not in text:
    if text.count(marker) != 1:
        raise RuntimeError('Unexpected Histree nginx configuration')
    config.write_text(text.replace(marker, block + marker, 1))
PY_NGINX
  if ! nginx -t || ! systemctl reload nginx; then
    cp "$release/nginx.previous" /etc/nginx/conf.d/histree.conf
    nginx -t && systemctl reload nginx
    exit 1
  fi
fi
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
docker exec histree-api node -e "fetch('http://127.0.0.1:3000/api/v1/ask/status',{headers:{'x-histree-gateway-key':process.env.HISTREE_GATEWAY_SECRET||''}}).then(async r=>{if(!r.ok)process.exit(1);console.log(await r.text())}).catch(()=>process.exit(1))"
docker exec histree-api node -e "fetch('http://127.0.0.1:3000/api/v1/ask/guess/status',{headers:{'x-histree-gateway-key':process.env.HISTREE_GATEWAY_SECRET||''}}).then(async r=>{if(!r.ok)process.exit(1);console.log(await r.text())}).catch(()=>process.exit(1))"
