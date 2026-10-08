#!/usr/bin/env bash
# Run on ECS to expose the combined frontend/API through the existing IP HTTPS vhost.
set -euo pipefail
ip=${1:?Public IPv4 required}
[[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
conf=/etc/nginx/conf.d/histree.conf
curl --fail --silent http://127.0.0.1:3000/ | grep -q '<div id="root"></div>'
install -d -m 700 /opt/histree/nginx-backups
backup=$(mktemp /opt/histree/nginx-backups/ip-frontend-XXXXXXXX.conf)
cp -p "$conf" "$backup"
rollback() {
  cp -p "$backup" "$conf"
  nginx -t && systemctl reload nginx
  echo "Previous IP vhost restored from $backup" >&2
}
trap rollback ERR
python3 - "$conf" "$ip" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]); ip = sys.argv[2]; text = p.read_text()
assert f'server_name {ip};' in text
if '# Histree IP frontend' not in text:
    old = '  location / { return 404; }'
    assert text.count(old) == 1, 'Unexpected IP vhost: review before changing'
    block = '''  # Histree IP frontend
  location / {
    client_max_body_size 10m;
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 180s;
  }'''
    text = text.replace(old, block, 1)
text = text.replace('  listen 443 ssl;', '  listen 443 ssl default_server;', 1)
p.write_text(text)
PY
nginx -t
systemctl reload nginx
verified=false
for attempt in {1..10}; do
  if curl --fail --silent --show-error --max-time 5 "https://$ip/people" | grep -q '<div id="root"></div>'; then
    verified=true; break
  fi
  sleep 1
done
[[ "$verified" == true ]]
trap - ERR
printf 'IP frontend enabled: https://%s/\nRollback configuration: %s\n' "$ip" "$backup"
