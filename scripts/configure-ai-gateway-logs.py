#!/usr/bin/env python3
"""Add credential-free AI request correlation to the existing nginx config."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--config', type=Path, default=Path('/etc/nginx/conf.d/histree.conf'))
args = parser.parse_args()
text = args.config.read_text().replace('$http_x_histree_request_id', '$upstream_http_x_histree_request_id')
markers = [
    '  location ~ ^/api/v1/ask/guess/(status|start|act)$ {\n',
    '  location = /api/v1/ask {\n',
    '  location = /api/v1/ask/status {\n',
]
for marker in markers:
    if text.count(marker) != 1:
        raise SystemExit('Unexpected Histree nginx configuration; no changes written')
    line = '    access_log /var/log/nginx/histree-ai.log histree_gateway;\n'
    if marker + line not in text:
        text = text.replace(marker, marker + line, 1)
if 'log_format histree_gateway ' not in text:
    fields = '{"time":"$time_iso8601","requestId":"$upstream_http_x_histree_request_id","method":"$request_method","path":"$uri","status":$status,"requestSeconds":"$request_time","connectSeconds":"$upstream_connect_time","headerSeconds":"$upstream_header_time","upstreamSeconds":"$upstream_response_time"}'
    text = "log_format histree_gateway escape=json '" + fields + "';\n" + text
args.config.write_text(text)
print('AI request correlation configured; run nginx -t before reloading')
