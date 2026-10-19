#!/usr/bin/env python3
"""Read-only MySQL/Supabase migration inventory. Never prints connection secrets.

Requires PyMySQL. Defaults to the ignored .env.migration.local and apps/api/.env.
This inventories API-visible source objects; it is not a consistent database backup.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import ssl
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def read_env(path):
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def failure(error):
    # Server error messages can contain hosts, account names, or connection strings.
    code = error.args[0] if error.args and isinstance(error.args[0], int) else None
    return {'ok': False, 'error_type': type(error).__name__, 'error_code': code,
            'http_status': getattr(error, 'code', None)}


def read_request(request, timeout=40):
    """Bounded retries for read-only HTTP requests; never used for paid/model writes."""
    for attempt in range(4):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            if error.code != 429 and error.code < 500:
                raise
            if attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)


def connect_mysql(env, use_database=False):
    import pymysql
    mode = env.get('MYSQL_SSL_MODE', 'disabled').lower()
    if mode not in ('disabled', 'require', 'verify-full'):
        raise ValueError('Unsupported MYSQL_SSL_MODE')
    tls = None
    if mode != 'disabled':
        tls = ssl.create_default_context(cafile=env.get('MYSQL_SSL_CA') or None)
        if mode == 'require':
            tls.check_hostname = False
            tls.verify_mode = ssl.CERT_NONE
    connection = pymysql.connect(
        host=env['MYSQL_HOST'], port=int(env.get('MYSQL_PORT', '3306')),
        user=env['MYSQL_USER'], password=env['MYSQL_PASSWORD'], charset='utf8mb4',
        connect_timeout=10, read_timeout=20, write_timeout=20,
        autocommit=False, ssl=tls,
        database=env['MYSQL_DATABASE'] if use_database else None,
    )
    if mode != 'disabled':
        with connection.cursor() as cursor:
            cursor.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
            cipher = cursor.fetchone()
        if not cipher or not cipher[1]:
            connection.close()
            raise RuntimeError('Requested TLS was not negotiated')
    return connection


def target_inventory(env):
    import pymysql
    connection = connect_mysql(env)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT VERSION(), @@character_set_server, @@collation_server, @@time_zone')
            version, charset, collation, zone = cursor.fetchone()
            cursor.execute("SHOW SESSION STATUS LIKE 'Ssl_cipher'")
            cipher = cursor.fetchone()
            cursor.execute('SHOW DATABASES')
            visible = {row[0] for row in cursor.fetchall()}
            cursor.execute('SHOW GRANTS')
            grants = [row[0].split(' TO ')[0] for row in cursor.fetchall()]
            database = env['MYSQL_DATABASE']
            cursor.execute('SELECT TABLE_NAME,TABLE_TYPE,TABLE_ROWS,DATA_LENGTH,INDEX_LENGTH '
                           'FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s ORDER BY TABLE_NAME',
                           (database,))
            tables = [{'name': r[0], 'type': r[1], 'estimated_rows': r[2],
                       'data_bytes': r[3], 'index_bytes': r[4]} for r in cursor.fetchall()]
            # USE is a connection setting, not a database mutation.
            access = True
            access_error = None
            try:
                connection.select_db(database)
            except pymysql.MySQLError as error:
                access = False
                access_error = failure(error)
            return {'ok': True, 'version': version, 'server_charset': charset,
                    'server_collation': collation, 'server_time_zone': zone,
                    'tls_cipher': cipher[1] if cipher else None,
                    'configured_database_visible': database in visible,
                    'configured_database_accessible': access, 'access_error': access_error,
                    'tables': tables, 'grants': grants,
                    'empty_database_verified': access and not tables}
    finally:
        connection.rollback()
        connection.close()


def source_inventory(env):
    base = env['SUPABASE_URL'].rstrip('/') + '/rest/v1/'
    key = env['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': key, 'Authorization': 'Bearer ' + key}
    with read_request(urllib.request.Request(base, headers=headers), timeout=25) as response:
        specification = json.load(response)
    definitions = specification.get('definitions', {})

    def count(table):
        request = urllib.request.Request(base + table + '?select=*&limit=0',
                                         headers={**headers, 'Prefer': 'count=exact'}, method='HEAD')
        with read_request(request, timeout=40) as response:
            raw_count = response.headers.get('Content-Range', '').split('/')[-1]
        return table, {'count': int(raw_count) if raw_count.isdigit() else None,
                       'columns': definitions[table].get('properties', {}),
                       'required': definitions[table].get('required', [])}

    with ThreadPoolExecutor(max_workers=3) as pool:
        tables = dict(pool.map(count, sorted(definitions)))
    return {'ok': True, 'tables': tables,
            'rpcs': sorted(p[5:] for p in specification.get('paths', {}) if p.startswith('/rpc/')),
            'scope': 'API-visible public schema only; counts are not a transactional snapshot'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mysql-env', type=Path, default=ROOT / '.env.migration.local')
    parser.add_argument('--source-env', type=Path, default=ROOT / 'apps/api/.env')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'mode': 'read-only'}
    for name, callback, path in [('mysql', target_inventory, args.mysql_env),
                                 ('supabase', source_inventory, args.source_env)]:
        try:
            report[name] = callback(read_env(path))
        except Exception as error:
            report[name] = failure(error)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, 'w') as output:
            output.write(encoded)
    summary = {'mode': report['mode'],
               'mysql': {k: v for k, v in report['mysql'].items() if k not in ('tables', 'grants')},
               'source_counts': {name: value['count'] for name, value in report.get('supabase', {}).get('tables', {}).items()}}
    if not report.get('supabase', {}).get('ok'):
        summary['supabase'] = report['supabase']
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (report['mysql'].get('configured_database_accessible')
                 and report['supabase'].get('ok')) else 1


if __name__ == '__main__':
    raise SystemExit(main())
