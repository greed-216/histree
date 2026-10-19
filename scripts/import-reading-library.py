#!/usr/bin/env python3
"""MySQL reader import. Offline verification by default; writes require --apply and explicit env."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'apps/api/mysql/migrations/20261019_library.sql'
FIELDS = json.loads((ROOT / 'scripts/reading-library-tables.json').read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def records(directory, book):
    path = (directory / book['file']).resolve()
    if path.parent != directory.resolve() or sha(path.read_bytes()) != book['file_sha256']:
        raise ValueError('Prepared file changed or escaped plan directory')
    digest = hashlib.sha256()
    count = 0
    with gzip.open(path, 'rt', encoding='utf-8') as source:
        for line in source:
            digest.update(line.encode())
            record = json.loads(line)
            table, row = record['table'], record['row']
            if table not in FIELDS or table == 'library_source_link' or set(row) != set(FIELDS[table]):
                raise ValueError('Unexpected corpus table/columns')
            if table == 'library_paragraph':
                if row['book_key'] != book['book_key'] or sha(row['content'].encode()) != row['content_sha256']:
                    raise ValueError('Original paragraph checksum mismatch')
                count += 1
            yield table, row
    if digest.hexdigest() != book['dataset_sha256'] or count != book['paragraph_count']:
        raise ValueError('Prepared corpus manifest mismatch')


def verify_database(connection, book):
    digest = hashlib.sha256()
    ordinal, total = -1, 0
    with connection.cursor() as cursor:
        while True:
            cursor.execute('SELECT id,ordinal,content,content_sha256 FROM library_paragraph WHERE book_key=%s AND ordinal>%s ORDER BY ordinal LIMIT 1000', [book['book_key'], ordinal])
            rows = cursor.fetchall()
            for pid, order, content, checksum in rows:
                if sha(content.encode()) != checksum:
                    raise ValueError('Database original text mismatch')
                digest.update((pid + '\0' + checksum + '\n').encode())
                ordinal, total = order, total + 1
            if len(rows) < 1000:
                break
        cursor.execute('SELECT COUNT(*) FROM library_section WHERE book_key=%s', [book['book_key']])
        sections = cursor.fetchone()[0]
    if total != book['paragraph_count'] or sections != book['section_count'] or digest.hexdigest() != book['content_digest']:
        raise ValueError('Database reading corpus is incomplete or changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--mysql-env', type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--create-tables', action='store_true')
    args = parser.parse_args()
    directory = args.manifest.resolve().parent
    plan = json.loads(args.manifest.read_text())
    if plan['format_version'] != 1 or plan['schema_sha256'] != sha(SCHEMA.read_bytes()):
        raise ValueError('Corpus schema changed after preparation')
    # Fully verify all input before any DB connection or write.
    for book in plan['books']:
        for _ in records(directory, book):
            pass
    link_path = (directory / plan['source_links_file']).resolve()
    if link_path.parent != directory or sha(link_path.read_bytes()) != plan['source_links_sha256']:
        raise ValueError('Source mappings changed')
    links = json.loads(link_path.read_text())
    if any(set(row) != set(FIELDS['library_source_link']) for row in links):
        raise ValueError('Invalid source mapping fields')
    if not args.mysql_env:
        if args.apply:
            raise ValueError('--apply requires an explicit --mysql-env')
        print(json.dumps({'verified_books': len(plan['books']), 'verified_paragraphs': sum(b['paragraph_count'] for b in plan['books']), 'database_writes': 0}))
        return
    spec = importlib.util.spec_from_file_location('preflight', ROOT / 'scripts/mysql-migration-preflight.py')
    preflight = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preflight)
    connection = preflight.connect_mysql(preflight.read_env(args.mysql_env), True)
    try:
        with connection.cursor() as cursor:
            if not args.apply:
                cursor.execute('SET TRANSACTION READ ONLY')
            else:
                cursor.execute("SELECT GET_LOCK('histree-content-publish',0)")
                if cursor.fetchone()[0] != 1:
                    raise ValueError('Another content publisher is active')
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('library_book','library_asset','library_section','library_paragraph','library_source_link')")
            present = {row[0] for row in cursor.fetchall()}
            if not args.apply:
                for book in plan['books']:
                    if 'library_book' not in present:
                        break
                    cursor.execute('SELECT dataset_sha256,status FROM library_book WHERE book_key=%s', [book['book_key']])
                    old = cursor.fetchone()
                    if old:
                        if old != (book['dataset_sha256'], 'available'):
                            raise ValueError('Existing reader version differs')
                        verify_database(connection, book)
                print(json.dumps({'preflight_books': len(plan['books']), 'tables_present': sorted(present), 'database_writes': 0}))
                return
            if len(present) != 5:
                if not args.create_tables:
                    raise ValueError('Library migration required; no corpus rows written')
                for statement in SCHEMA.read_text().split(';'):
                    if statement.strip():
                        cursor.execute(statement)
        connection.commit()
        for book in plan['books']:
            with connection.cursor() as cursor:
                cursor.execute('SELECT dataset_sha256,status FROM library_book WHERE book_key=%s', [book['book_key']])
                old = cursor.fetchone()
            if old:
                if old != (book['dataset_sha256'], 'available'):
                    raise ValueError('Existing reader version differs')
                verify_database(connection, book)
                continue
            connection.begin()
            try:
                with connection.cursor() as cursor:
                    cols = ('book_key','title','source_version','sort_order','section_count','paragraph_count','dataset_sha256','metadata')
                    cursor.execute('INSERT INTO library_book(' + ','.join(cols) + ') VALUES(' + ','.join(['%s'] * len(cols)) + ')', [book[c] for c in cols])
                    table, pending = '', []
                    def flush():
                        if not pending:
                            return
                        names = list(FIELDS[table])
                        if table == 'library_asset':
                            for row in pending:
                                cursor.execute('SELECT source_file,source_sha256 FROM library_asset WHERE id=%s', [row['id']])
                                old_asset = cursor.fetchone()
                                if old_asset:
                                    if old_asset != (row['source_file'], row['source_sha256']):
                                        raise ValueError('Existing original asset changed')
                                    continue
                                cursor.execute('INSERT INTO library_asset(' + ','.join(names) + ') VALUES(%s,%s,%s)', [row[n] for n in names])
                        else:
                            cursor.executemany('INSERT INTO ' + table + '(' + ','.join(names) + ') VALUES(' + ','.join(['%s'] * len(names)) + ')', [[r[n] for n in names] for r in pending])
                    for current, row in records(directory, book):
                        if current != table or len(pending) >= 200:
                            flush()
                            table, pending = current, []
                        pending.append(row)
                    flush()
                verify_database(connection, book)
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE library_book SET status='available' WHERE book_key=%s", [book['book_key']])
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        connection.begin()
        with connection.cursor() as cursor:
            # Batch network round trips while retaining immutable mapping guards.
            for offset in range(0, len(links), 100):
                chunk = links[offset:offset + 100]
                ids = sorted({row['source_id'] for row in chunk})
                placeholders = ','.join(['%s'] * len(ids))
                query = 'SELECT source_id,archive_url_sha256,paragraph_id,snapshot_sha256 FROM library_source_link WHERE source_id IN (' + placeholders + ')'
                cursor.execute(query, ids)
                existing = {(sid, url): (pid, checksum) for sid, url, pid, checksum in cursor.fetchall()}
                pending = []
                columns = list(FIELDS['library_source_link'])
                for row in chunk:
                    old = existing.get((row['source_id'], row['archive_url_sha256']))
                    expected = (row['paragraph_id'], row['snapshot_sha256'])
                    if old is not None and old != expected:
                        raise ValueError('Existing source mapping changed')
                    if old is None:
                        pending.append([row[n] for n in columns])
                if pending:
                    cursor.executemany('INSERT INTO library_source_link(' + ','.join(columns) + ') VALUES(%s,%s,%s,%s)', pending)
                cursor.execute(query, ids)
                actual = {(sid, url): (pid, checksum) for sid, url, pid, checksum in cursor.fetchall()}
                if any(actual.get((row['source_id'], row['archive_url_sha256'])) != (row['paragraph_id'], row['snapshot_sha256']) for row in chunk):
                    raise ValueError('Source mapping readback mismatch')
        connection.commit()
        print(json.dumps({'imported_verified_books': len(plan['books']), 'source_links': len(links)}))
    finally:
        connection.rollback()
        connection.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'failed': type(error).__name__, 'reason': str(error) if isinstance(error, ValueError) else 'Operation failed; connection diagnostics suppressed'}))
        raise SystemExit(1)
