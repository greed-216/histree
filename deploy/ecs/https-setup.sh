#!/usr/bin/env bash
# Run once on the ECS host after the API is healthy. Requires ports 80/443 reachable.
set -euo pipefail
ip=${1:?Public IPv4 required}
[[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 2
certbot=/opt/histree/certbot/bin/certbot
install -d -m 755 /var/www/histree-acme
cat > /etc/nginx/conf.d/histree.conf <<NGINX
server {
  listen 80;
  server_name $ip;
  location ^~ /.well-known/acme-challenge/ { root /var/www/histree-acme; }
  location / { return 404; }
}
NGINX
nginx -t
systemctl enable --now nginx
systemctl reload nginx
"$certbot" certonly --non-interactive --agree-tos --register-unsafely-without-email \
  --preferred-profile shortlived --webroot -w /var/www/histree-acme --ip-address "$ip"
cat > /etc/nginx/conf.d/histree.conf <<NGINX
server {
  listen 80;
  server_name $ip;
  location ^~ /.well-known/acme-challenge/ { root /var/www/histree-acme; }
  location / { return 308 https://$ip\$request_uri; }
}
server {
  listen 443 ssl default_server;
  server_name $ip;
  ssl_certificate /etc/letsencrypt/live/$ip/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/$ip/privkey.pem;
  ssl_protocols TLSv1.2 TLSv1.3;
  client_max_body_size 16k;
  location ~ ^/api/v1/ask/guess/(status|start|act)$ {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 180s;
  }
  location ~ ^/api/v1/ask/guess/(status|start|act)$ {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 140s;
  }
  location = /api/v1/ask {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Proto https;
    proxy_buffering off;
    proxy_read_timeout 150s;
  }
  location = /api/v1/ask/status {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$remote_addr;
  }
  # Histree IP frontend
  location / {
    client_max_body_size 10m;
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$remote_addr;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 180s;
  }
}
NGINX
# SELinux may require this for nginx -> loopback Docker.
if command -v getenforce >/dev/null && [[ $(getenforce) != Disabled ]]; then
  setsebool -P httpd_can_network_connect 1
fi
nginx -t
systemctl reload nginx
install -d -m 755 /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/histree-nginx.sh <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
nginx -t
systemctl reload nginx
HOOK
chmod 755 /etc/letsencrypt/renewal-hooks/deploy/histree-nginx.sh
cat > /etc/systemd/system/histree-certbot.service <<'UNIT'
[Unit]
Description=Renew Histree HTTPS certificate
After=network-online.target
Wants=network-online.target
[Service]
Type=oneshot
ExecStart=/opt/histree/certbot/bin/certbot renew --quiet
UNIT
cat > /etc/systemd/system/histree-certbot.timer <<'UNIT'
[Unit]
Description=Check Histree certificate renewal twice daily
[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=1800
Persistent=true
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now histree-certbot.timer
docker exec histree-api node -e "fetch('http://127.0.0.1:3000/api/v1/ask/status').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"
