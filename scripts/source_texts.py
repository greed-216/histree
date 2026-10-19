"""Immutable source excerpts shared by backfill and the existing book publisher.

Read exact Git blobs; never use a mutable worktree copy or download at reading time.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'apps/api/mysql/migrations/20261019_source_text.sql'
UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')


@lru_cache(maxsize=256)
def full_commit(commit):
    result = subprocess.run(['git', 'rev-parse', '--verify', commit + '^{commit}'], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.decode().strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob_spec(url):
    parsed = urlsplit(url)
    match = re.fullmatch(r'/greed-216/histree/blob/([0-9a-f]{7,40})/(.+)', parsed.path)
    if parsed.scheme != 'https' or parsed.netloc != 'github.com' or not match or parsed.query:
        raise ValueError('Source needs a fixed Histree Git archive URL')
    path = unquote(match[2])
    if not path.startswith(('content/', 'resources/derived/', 'resources/originals/')) or '..' in Path(path).parts or not path.endswith(('.txt', '.jsonl')) or '\n' in path or '\r' in path:
        raise ValueError('Unsupported source archive path')
    if parsed.fragment and not re.fullmatch(r'L[1-9]\d*(?:-L[1-9]\d*)?', parsed.fragment):
        raise ValueError('Unsupported source line locator')
    if path.endswith('.jsonl') and not parsed.fragment:
        raise ValueError('JSONL source requires an explicit line locator')
    return (match[1] if len(match[1]) == 40 else full_commit(match[1])) + ':' + path


def load_blobs(urls, root=ROOT):
    urls = sorted(set(urls))
    if not urls:
        return {}
    specs = sorted({blob_spec(url) for url in urls})
    result = subprocess.run(['git', 'cat-file', '--batch'], input=('\n'.join(specs) + '\n').encode(),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=root, check=True)
    offset = 0
    blobs = {}
    for spec in specs:
        end = result.stdout.index(b'\n', offset)
        header = result.stdout[offset:end].split()
        if len(header) != 3 or header[1] != b'blob':
            raise ValueError('Missing archived source blob: ' + spec)
        length = int(header[2])
        raw = result.stdout[end + 1:end + 1 + length]
        # Strict UTF-8 and round-trip retain every original byte, including final newlines.
        if not raw or len(raw) > 16 * 1024 * 1024 or raw.decode('utf-8').encode('utf-8') != raw:
            raise ValueError('Invalid or oversized source snapshot')
        blobs[spec] = raw
        offset = end + length + 2
    return {url: blobs[blob_spec(url)] for url in urls}


def source_rows(sources, claims, ids, skipped=None):
    used = {c.get('source_id') or ids.get(c.get('source_key')) for c in claims}
    rows = []
    for source in sources:
        sid = source.get('id') or ids.get(source.get('key'))
        if sid not in used:
            continue
        if not sid or not UUID.fullmatch(sid):
            raise ValueError('Missing stable source UUID')
        try:
            blob_spec(source['url'])
        except ValueError as error:
            if skipped is None:
                raise
            skipped.append({'source_id': sid, 'archive_url': source['url'], 'reason': str(error)})
            continue
        rows.append({'source_id': sid, 'archive_url': source['url']})
    return rows


def fill_content(rows):
    blobs = load_blobs(row['archive_url'] for row in rows)
    unique = {}
    for row in rows:
        blob = blobs[row['archive_url']]
        raw = blob
        parsed = urlsplit(row['archive_url'])
        if parsed.fragment:
            numbers = [int(n) for n in re.findall(r'\d+', parsed.fragment)]
            first, last = numbers[0], numbers[-1]
            lines = raw.decode('utf-8').splitlines(keepends=True)
            if first > last or last > len(lines):
                raise ValueError('Archive line locator out of range')
            selected = lines[first - 1:last]
            if parsed.path.endswith('.jsonl'):
                # Preserve text field characters; do not expose serialized JSON as prose.
                values = [json.loads(line)['text'] for line in selected]
                if not all(isinstance(value, str) for value in values):
                    raise ValueError('Archive JSONL text is invalid')
                raw = '\n'.join(values).encode('utf-8')
            else:
                raw = ''.join(selected).encode('utf-8')
        record = dict(row, archive_url_sha256=digest(row['archive_url'].encode()),
                      content=raw.decode('utf-8'), content_sha256=digest(raw), archive_blob_sha256=digest(blob),
                      archive_commit=blob_spec(row['archive_url']).split(':', 1)[0])
        unique[(record['source_id'], record['archive_url_sha256'])] = record
    return sorted(unique.values(), key=lambda row: (row['source_id'], row['archive_url_sha256']))


def batch_texts(batch, ids):
    return fill_content(source_rows(batch['sources'], batch['claims'], ids))


def published_texts(skipped=None):
    skipped = [] if skipped is None else skipped
    rows = []
    for path in sorted((ROOT / 'content').rglob('content-batch.json')):
        audits = [json.loads(p.read_text()) for name in ('publication-mysql.json', 'publication.json')
                  if (p := path.parent / name).exists()]
        verified = [a for a in audits if a.get('verified')]
        if not verified:
            continue
        if not any(a.get('batch_sha256') == digest(path.read_bytes()) for a in verified):
            raise ValueError('Published batch hash mismatch: ' + str(path))
        batch = json.loads(path.read_text())
        ids = json.loads((path.parent / 'sql/key-map.json').read_text())
        rows.extend(source_rows(batch['sources'], batch['claims'], ids, skipped))
    for path in sorted((ROOT / 'content/revisions').rglob('plan.json')):
        audit = path.parent / 'publication-mysql.json'
        if not audit.exists():
            continue
        proof = json.loads(audit.read_text())
        plan = json.loads(path.read_text())
        if not proof.get('verified') or not plan.get('sources'):
            continue
        if proof.get('plan_sha256') != digest(path.read_bytes()):
            raise ValueError('Published revision hash mismatch: ' + str(path))
        rows.extend(source_rows(plan['sources'], plan.get('new_claims', []), {}, skipped))
    return fill_content(rows)


def validate_rows(rows):
    seen = set()
    for row in rows:
        if not UUID.fullmatch(row['source_id']):
            raise ValueError('Invalid source UUID')
        blob_spec(row['archive_url'])
        if row['archive_url_sha256'] != digest(row['archive_url'].encode()) or row['content_sha256'] != digest(row['content'].encode()):
            raise ValueError('Source content or archive URL hash mismatch')
        if not row['content'] or len(row['content'].encode()) > 16 * 1024 * 1024 or not re.fullmatch(r'[a-f0-9]{64}', row['archive_blob_sha256']) or row['archive_commit'] != blob_spec(row['archive_url']).split(':', 1)[0]:
            raise ValueError('Invalid source provenance or content size')
        key = (row['source_id'], row['archive_url_sha256'])
        if key in seen:
            raise ValueError('Duplicate source snapshot')
        seen.add(key)


def preflight(connection, rows, pending_sources=None):
    """No writes. Compare all rows before an import starts, including old-value guards."""
    pending_sources = pending_sources or {}
    validate_rows(rows)
    sources = {}
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='source_text'")
        has_table = cursor.fetchone()[0] == 1
        ids = sorted({row['source_id'] for row in rows})
        for offset in range(0, len(ids), 100):
            chunk = ids[offset:offset + 100]
            cursor.execute('SELECT id,url FROM source WHERE id IN (' + ','.join(['%s'] * len(chunk)) + ')', chunk)
            sources.update(cursor.fetchall())
    for row in rows:
        if sources.get(row['source_id'], pending_sources.get(row['source_id'])) != row['archive_url']:
            raise ValueError('Source URL changed or source missing: ' + row['source_id'])
    existing = stored_rows(connection, rows) if has_table else {}
    reused = 0
    for row in rows:
        old = existing.get((row['source_id'], row['archive_url_sha256']))
        if old:
            if old != record_values(row):
                raise ValueError('Existing source text changed: ' + row['source_id'])
            reused += 1
    return {'table_exists': has_table, 'new': len(rows) - reused, 'reused': reused}


FIELDS = ('source_id', 'archive_url_sha256', 'archive_url', 'content', 'content_sha256', 'archive_blob_sha256', 'archive_commit')


def record_values(row):
    return tuple(row[k] for k in FIELDS)


def stored_rows(connection, rows, lock=False):
    result = {}
    ids = sorted({row['source_id'] for row in rows})
    with connection.cursor() as cursor:
        for offset in range(0, len(ids), 100):
            chunk = ids[offset:offset + 100]
            cursor.execute('SELECT ' + ','.join(FIELDS) + ' FROM source_text WHERE source_id IN (' + ','.join(['%s'] * len(chunk)) + ')' + (' FOR UPDATE' if lock else ''), chunk)
            for row in cursor.fetchall():
                result[(row[0], row[1])] = tuple(row)
    return result


def insert_texts(connection, rows):
    """Caller owns the transaction. Never overwrite an existing snapshot."""
    existing = stored_rows(connection, rows, lock=True)
    missing = []
    for row in rows:
        old = existing.get((row['source_id'], row['archive_url_sha256']))
        if old:
            if old != record_values(row):
                raise ValueError('Existing source text changed: ' + row['source_id'])
        else:
            missing.append(record_values(row))
    with connection.cursor() as cursor:
        for offset in range(0, len(missing), 100):
            cursor.executemany('INSERT INTO source_text(' + ','.join(FIELDS) + ') VALUES(%s,%s,%s,%s,%s,%s,%s)', missing[offset:offset + 100])


def verify_texts(connection, rows):
    actual = stored_rows(connection, rows)
    for row in rows:
        if actual.get((row['source_id'], row['archive_url_sha256'])) != record_values(row):
            raise ValueError('Source text readback mismatch: ' + row['source_id'])
