"""Private MySQL connection helpers for reviewed content tools."""
from pathlib import Path
import ssl, time, urllib.request, urllib.error
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
