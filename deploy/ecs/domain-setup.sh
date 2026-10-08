#!/usr/bin/env bash
# Run on ECS after DNS/ICP readiness and a healthy combined application release.
set -euo pipefail
domain=${1:-histree.wiki}
[[ "$domain" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}$ ]] || exit 2
certbot=/opt/histree/certbot/bin/certbot
conf=/etc/nginx/conf.d/histree-domain.conf
curl --fail --silent http://127.0.0.1:3000/ | grep -q '<div id="root"></div>'
backup=$(mktemp)
had_config=false
if [[ -f "$conf" ]]; then cp "$conf" "$backup"; had_config=true; fi
rollback() {
  if $had_config; then cp "$backup" "$conf"; else rm -f "$conf"; fi
  nginx -t && systemctl reload nginx
  rm -f "$backup"
}
trap rollback ERR
install -d -m 755 /var/www/histree-acme
# Keep an existing domain vhost intact while renewing its certificate.
if ! $had_config; then
  cat > "$conf" <<NGINX
server {
  listen 80;
  server_name $domain;
  location ^~ /.well-known/acme-challenge/ { root /var/www/histree-acme; }
  location / { return 503; }
}
NGINX
  nginx -t
  systemctl reload nginx
fi
"$certbot" certonly --non-interactive --agree-tos --register-unsafely-without-email \
  --webroot -w /var/www/histree-acme -d "$domain"
cat > "$conf" <<NGINX
server {
  listen 80;
  server_name $domain;
  location ^~ /.well-known/acme-challenge/ { root /var/www/histree-acme; }
  location / { return 308 https://$domain\$request_uri; }
}
server {
  listen 443 ssl;
  server_name $domain;
  ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  client_max_body_size 10m;
  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Proto https;
    proxy_buffering off;
    proxy_read_timeout 180s;
  }
}
NGINX
nginx -t
systemctl reload nginx
curl --fail --silent --resolve "$domain:443:127.0.0.1" "https://$domain/" | grep -q '<div id="root"></div>'
systemctl is-active --quiet histree-certbot.timer
trap - ERR
rm -f "$backup"
