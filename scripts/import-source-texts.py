#!/usr/bin/env python3
"""Prepare/backfill published excerpts. Default is offline preparation or read-only preflight.

prepare --output PLAN; import PLAN [--mysql-env ENV] [--apply --create-table]
"""
import argparse
import json
import sys
from pathlib import Path
import source_texts as texts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--output', type=Path, required=True)
    apply = commands.add_parser('import')
    apply.add_argument('plan', type=Path)
    apply.add_argument('--mysql-env', type=Path)
    apply.add_argument('--apply', action='store_true')
    apply.add_argument('--create-table', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        skipped = []
        rows = texts.published_texts(skipped)
        plan = {'format_version': 1, 'schema_sha256': texts.digest(texts.SCHEMA.read_bytes()), 'rows': rows, 'skipped': skipped}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(plan, ensure_ascii=False) + '\n')
        print(json.dumps({'prepared': len(rows), 'skipped': len({r['archive_url'] for r in skipped}), 'utf8_bytes': sum(len(r['content'].encode()) for r in rows), 'database_writes': 0}))
        return
    plan = json.loads(args.plan.read_text())
    rows = plan['rows']
    texts.validate_rows(rows)
    # Recheck the Git bytes too; a self-consistent edited JSON plan is not an archive.
    if plan['format_version'] != 1 or texts.fill_content([{'source_id': r['source_id'], 'archive_url': r['archive_url']} for r in rows]) != rows:
        raise ValueError('Plan differs from fixed source archives')
    if plan['schema_sha256'] != texts.digest(texts.SCHEMA.read_bytes()):
        raise ValueError('Source schema changed after preparation')
    if not args.mysql_env:
        if args.apply:
            raise ValueError('--apply requires an explicit --mysql-env')
        print(json.dumps({'verified_archives': len(rows), 'database_writes': 0, 'database_checked': False}))
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location('preflight', texts.ROOT / 'scripts/mysql-migration-preflight.py')
    preflight = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preflight)
    connection = preflight.connect_mysql(preflight.read_env(args.mysql_env), True)
    try:
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY' if not args.apply else "SELECT GET_LOCK('histree-content-publish',0)")
            if args.apply and cursor.fetchone()[0] != 1:
                raise ValueError('Another content publisher is active')
        summary = texts.preflight(connection, rows)
        if not args.apply:
            print(json.dumps(dict(summary, database_writes=0)))
            return
        if not summary['table_exists']:
            if not args.create_table:
                raise ValueError('source_text migration required; use --create-table explicitly')
            with connection.cursor() as cursor:
                cursor.execute(texts.SCHEMA.read_text())
        texts.insert_texts(connection, rows)
        texts.verify_texts(connection, rows)
        connection.commit()
        print(json.dumps(dict(summary, imported_verified=len(rows))))
    finally:
        connection.rollback()
        connection.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Avoid printing credentials/hosts embedded in database diagnostics.
        print(json.dumps({'failed': type(error).__name__, 'reason': str(error) if isinstance(error, ValueError) else 'Operation failed; connection diagnostics suppressed'}))
        sys.exit(1)
