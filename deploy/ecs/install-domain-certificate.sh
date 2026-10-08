#!/usr/bin/env bash
# Install an issued PEM certificate on ECS. Default: TLS ready, website pending ICP.
set -euo pipefail
umask 077
domain=${1:?domain required}
certificate=${2:?PEM full chain path required}
private_key=${3:?PEM private key path required}
mode=${4:-pending}
[[ "$domain" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}$ ]] || exit 2
[[ "$mode" == pending || "$mode" == serve ]] || exit 2
[[ -f "$certificate" && -f "$private_key" ]] || exit 2
openssl x509 -in "$certificate" -checkhost "$domain" -noout
openssl x509 -in "$certificate" -checkend 0 -noout
openssl verify -purpose sslserver -verify_hostname "$domain" -untrusted "$certificate" "$certificate"
cert_public=$(openssl x509 -in "$certificate" -pubkey -noout | openssl pkey -pubin -outform DER | sha256sum)
key_public=$(openssl pkey -in "$private_key" -pubout -outform DER | sha256sum)
[[ "$cert_public" == "$key_public" ]] || { echo 'Certificate and private key do not match' >&2; exit 1; }
install -d -m 700 "/opt/histree/tls/$domain"
tls=$(mktemp -d "/opt/histree/tls/$domain/issued-XXXXXXXX")
install -m 644 "$certificate" "$tls/fullchain.pem"
install -m 600 "$private_key" "$tls/privkey.pem"
conf=/etc/nginx/conf.d/histree-domain.conf
backup=$(mktemp)
had_config=false
if [[ -f "$conf" ]]; then cp "$conf" "$backup"; had_config=true; fi
rollback() {
  if $had_config; then cp "$backup" "$conf"; else rm -f "$conf"; fi
  nginx -t && systemctl reload nginx
  rm -f "$backup"
  echo 'Previous nginx configuration restored' >&2
}
trap rollback ERR
cat > "$conf" <<NGINX
server {
  listen 80;
  server_name $domain;
  location / { return 308 https://$domain\$request_uri; }
}
server {
  listen 443 ssl;
  server_name $domain;
  ssl_certificate $tls/fullchain.pem;
  ssl_certificate_key $tls/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  client_max_body_size 10m;
NGINX
if [[ "$mode" == pending ]]; then
  cat >> "$conf" <<'NGINX'
  location / {
    default_type text/plain;
    charset utf-8;
    add_header Retry-After 86400 always;
    return 503 "ICP备案办理中，网站尚未开放。\n";
  }
NGINX
else
  curl --fail --silent http://127.0.0.1:3000/ | grep -q '<div id="root"></div>'
  cat >> "$conf" <<'NGINX'
  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto https;
    proxy_buffering off;
    proxy_read_timeout 180s;
  }
NGINX
fi
printf '}\n' >> "$conf"
nginx -t
systemctl reload nginx
expected=503
[[ "$mode" == serve ]] && expected=200
verified=false
# nginx reload returns before new workers necessarily accept TLS connections.
for attempt in {1..10}; do
  if status=$(curl --silent --show-error --max-time 5 --resolve "$domain:443:127.0.0.1" -o /dev/null -w '%{http_code}' "https://$domain/"); then
    if [[ "$status" == "$expected" ]]; then verified=true; break; fi
  fi
  sleep 1
done
[[ "$verified" == true ]]
trap - ERR
rm -f "$backup"
openssl x509 -in "$tls/fullchain.pem" -noout -subject -issuer -dates -fingerprint -sha256
printf 'TLS directory: %s\nWebsite mode: %s\nHTTPS status: %s\n' "$tls" "$mode" "$status"
