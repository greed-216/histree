#!/usr/bin/env python3
# coding: utf-8
"""Native MySQL8 correction regression after the existing schema bootstrap.

Process MYSQL_* only; localhost/127.0.0.1 plus histree_test_* and a loopback socket
are mandatory. No DDL, HTTP, production env lookup or existing correction plan.
Fixed owned IDs are checked absent before seeding, deleted by exact PK only, and
all preexisting table PK sets must survive cleanup. --check-safety opens no socket.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import history_revision as H
from mysql_connection import connect_mysql

SCRIPTS = Path(__file__).resolve().parent


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


FIXTURE = load_module('native_revision_fixture', 'test-history-revision.py')
SAFETY = load_module('native_revision_safety', 'test-history-sidecars-mysql.py')
BOOK = 'revision-mysql-fixture-v1'
SECTION = BOOK + '-s1'
PARAGRAPH = BOOK + '-p1'
ASSET = H.digest(b'native-revision-owned-asset-v1')
TABLE_KEYS = {table: key for table, key in H.KEYS.items()}
TABLE_KEYS['library_section'] = ('id',)
CLEAN_ORDER = ('claim_relation', 'event_dating', 'claim_structure', 'fact_claim',
               'person_event', 'person_relationship', 'library_source_link',
               'library_paragraph', 'library_section', 'library_asset', 'library_book',
               'source_text', 'event', 'person', 'source')
SEED_ORDER = ('source', 'person', 'event', 'person_event', 'fact_claim',
              'claim_structure', 'event_dating', 'source_text', 'library_book',
              'library_asset', 'library_section', 'library_paragraph', 'library_source_link')


def primary_keys(connection):
    result = {}
    with connection.cursor() as cursor:
        for table, fields in TABLE_KEYS.items():
            cursor.execute('SELECT ' + ','.join('`' + field + '`' for field in fields) + ' FROM `' + table + '`')
            result[table] = set(cursor.fetchall())
    return result


def get_owned(db, table, key):
    import pymysql
    fields = TABLE_KEYS[table]
    with db.connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute('SELECT * FROM `' + table + '` WHERE ' + ' AND '.join('`' + field + '`=%s' for field in fields), list(key))
        rows = cursor.fetchall()
    H.require(len(rows) <= 1, 'Owned fixture primary key is not unique')
    return db.store.normalize(table, rows[0]) if rows else None


def own_ids(initial, plan):
    owned = {table: set() for table in TABLE_KEYS}
    for table, rows in initial.items():
        owned[table].update(tuple(row[k] for k in TABLE_KEYS[table]) for row in rows)
    for table, rows in plan['inserts'].items():
        owned[table].update(tuple(row[k] for k in TABLE_KEYS[table]) for row in rows)
    return owned


def insert_fixture(db, table, row):
    H.require(table in TABLE_KEYS, 'Fixture write outside fixed tables')
    fields = list(row)
    with db.connection.cursor() as cursor:
        cursor.execute('INSERT INTO `' + table + '` (' + ','.join('`' + field + '`' for field in fields) +
                       ') VALUES (' + ','.join('%s' for _ in fields) + ')',
                       [db.value(table, field, row[field]) for field in fields])


def cleanup(db, owned):
    # No broad predicate, DELETE cascade or truncation: only these known PKs.
    with db.connection.cursor() as cursor:
        for table in CLEAN_ORDER:
            fields = TABLE_KEYS[table]
            for key in sorted(owned[table]):
                H.require(key in owned[table], 'Cleanup identity is not owned')
                cursor.execute('DELETE FROM `' + table + '` WHERE ' + ' AND '.join('`' + field + '`=%s' for field in fields), list(key))
    db.connection.commit()


def owned_state(db, owned):
    return {(table, key): get_owned(db, table, key) for table, ids in owned.items() for key in ids}


def revision_number(db):
    with db.connection.cursor() as cursor:
        cursor.execute('SELECT revision FROM content_revision WHERE id=1')
        return cursor.fetchone()[0]


def library_rows(root, initial, plan):
    source = initial['source'][0]; text = initial['source_text'][0]
    raw = (root / 'raw/source.txt').read_bytes(); display = raw.decode('utf-8').lstrip('\ufeff').strip()
    values = {
        'library_book': [dict(book_key=BOOK, title='合成纠错原文', source_version='v1', sort_order=999999,
                              section_count=1, paragraph_count=1, dataset_sha256=H.digest(raw), metadata={}, status='available')],
        'library_asset': [dict(id=ASSET, source_file='raw/source.txt', source_sha256=H.digest(raw))],
        'library_section': [dict(id=SECTION, book_key=BOOK, sort_order=1, title='合成第一卷', volume=1,
                                 kind='volume', has_issues=0, metadata={})],
        'library_paragraph': [dict(id=PARAGRAPH, book_key=BOOK, section_id=SECTION, ordinal=1, kind='body',
                                   content=display, content_sha256=H.digest(display.encode()), asset_id=ASSET,
                                   char_start=0, char_end=len(raw.decode('utf-8')), flags=[])],
        'library_source_link': [dict(source_id=source['id'], archive_url_sha256=text['archive_url_sha256'],
                                     snapshot_sha256=text['content_sha256'], paragraph_id=PARAGRAPH)],
    }
    initial.update(values)
    for table, rows in values.items():
        if table != 'library_section':
            plan['protected_rows'].extend(dict(table=table, identity=H.identity(table, row), full_before=copy.deepcopy(row)) for row in rows)


def run(values):
    # This allowlist is evaluated before any env file or DB adapter is created.
    env = SAFETY.test_environment(values)
    db = None; seeded = False; owned = None; baseline = None; checks = 0
    with tempfile.TemporaryDirectory(prefix='histree-revision-native-') as temporary:
        root = Path(temporary).resolve(); plan, initial = FIXTURE.fixture(root); library_rows(root, initial, plan)
        envpath = root / 'isolated-mysql.env'
        envpath.write_text(''.join(key + '=' + value + '\n' for key, value in env.items()))
        try:
            db = H.Database(envpath, writable=True)
            SAFETY.connection_identity(db.connection, env)
            plan['target_fingerprint'] = db.target_fingerprint
            owned = own_ids(initial, plan); baseline = primary_keys(db.connection)
            H.require(all(not (owned[table] & baseline[table]) for table in TABLE_KEYS), 'Owned fixture IDs already exist; refusing to touch them')
            for table in SEED_ORDER:
                for row in initial.get(table, []): insert_fixture(db, table, row)
            db.connection.commit(); seeded = True
            # Use the real normalized full rows, including all default columns.
            for update in plan['updates']:
                update['full_before'] = get_owned(db, update['table'], (update['id'],))
            for guard in plan['protected_rows']:
                key = tuple(guard['identity'][field] for field in H.KEYS[guard['table']])
                guard['full_before'] = get_owned(db, guard['table'], key)
            H.require(H.check_plan(plan, root, db)['status'] == 'before_state_matches', 'Native preflight failed'); checks += 1
            original = owned_state(db, owned)
            from history_identity import matching_edges
            edge = get_owned(db, 'person_event', (FIXTURE.IDS['old-pe'],))
            matches = matching_edges(db.store, 'person_event', [edge])
            H.require([r['id'] for r in matches] == [edge['id']], 'Native endpoint lookup missed the existing participant')
            H.require(not matching_edges(db.store, 'person_event', [dict(edge, role='different role')]), 'Native endpoint lookup ignored role')
            H.require(owned_state(db, owned) == original, 'Read-only endpoint lookup changed fixture rows'); checks += 1
            wrong = copy.deepcopy(plan); wrong['updates'][0]['full_before']['role'] = 'wrong old value'
            before_revision = revision_number(db)
            try: H.apply_plan(wrong, root, db)
            except ValueError as error: H.require('Full row guard' in str(error), 'Wrong old row did not hit full guard')
            else: raise AssertionError('Wrong old row was written')
            H.require(owned_state(db, owned) == original and revision_number(db) == before_revision, 'Old-value failure changed DB'); checks += 1
            # A separate session owns the exact lock used by all publishers.
            locker = connect_mysql(env, True)
            try:
                SAFETY.connection_identity(locker, env)
                with locker.cursor() as cursor:
                    cursor.execute("SELECT GET_LOCK('histree-content-publish',0)"); H.require(cursor.fetchone()[0] == 1, 'Fixture cannot acquire test lock')
                try: H.apply_plan(plan, root, db)
                except ValueError as error: H.require('publisher is active' in str(error), 'Wrong global lock failure')
                else: raise AssertionError('Apply ignored another publisher lock')
            finally: locker.close()
            H.require(owned_state(db, owned) == original, 'Lock failure changed DB'); checks += 1
            # A real FK conflict at the last INSERT must roll back earlier inserts.
            bad_fk = copy.deepcopy(plan); bad_fk['inserts']['claim_relation'][0]['related_claim_id'] = FIXTURE.UID('absent-claim')
            try: H.apply_plan(bad_fk, root, db)
            except Exception as error: H.require(getattr(error, 'args', [None])[0] == 1452, 'Expected native FK rejection')
            else: raise AssertionError('Missing referenced claim was accepted')
            H.require(owned_state(db, owned) == original and revision_number(db) == before_revision, 'FK failure did not fully roll back'); checks += 1
            # Late SQL mutations in this same transaction model a writer/trigger
            # touching an unreviewed field after the initial guard. Both must abort.
            real_update = db.update
            for conflict in ('unmodified-role', 'raw-source-bytes', 'library-locator'):
                def late(table, pk, after, mode=conflict):
                    real_update(table, pk, after)
                    with db.connection.cursor() as cursor:
                        if mode == 'unmodified-role':
                            cursor.execute('UPDATE person_event SET role=%s WHERE id=%s', ('late conflict', FIXTURE.IDS['old-pe']))
                        elif mode == 'raw-source-bytes':
                            cursor.execute('UPDATE source_text SET content=%s WHERE source_id=%s AND archive_url_sha256=%s', ('late source conflict', initial['source'][0]['id'], initial['source_text'][0]['archive_url_sha256']))
                        else:
                            cursor.execute('UPDATE library_paragraph SET char_end=char_end+1 WHERE id=%s', (PARAGRAPH,))
                with patch.object(db, 'update', side_effect=late):
                    try: H.apply_plan(plan, root, db)
                    except ValueError as error: H.require('Full row guard' in str(error), 'Expected final full-row guard')
                    else: raise AssertionError('Late guard conflict committed')
                H.require(owned_state(db, owned) == original and revision_number(db) == before_revision, 'Late conflict rollback left data behind'); checks += 1
            result = H.apply_plan(plan, root, db)
            H.require(result['status'] == 'committed_pending_anonymous' and 'verified' not in result, 'Native engine claimed anonymous verification')
            H.require(result['counts']['updates'] == 1 and all(n == 1 for n in result['counts']['inserts'].values()), 'Unexpected native mutation counts')
            actual = get_owned(db, 'person_event', (FIXTURE.IDS['old-pe'],))
            H.require(actual['person_id'] == FIXTURE.IDS['new-person'] and actual['role'] == '原角色保留', 'Old unmodified field was lost')
            for guard in plan['protected_rows']:
                key = tuple(guard['identity'][field] for field in H.KEYS[guard['table']])
                H.require(get_owned(db, guard['table'], key) == guard['full_before'], 'Protected business/source/library row changed')
            H.require(H.verify_db(plan, root, db, result)['status'] == 'after_state_matches', 'Native read-only after verification failed'); checks += 1
            committed = owned_state(db, owned); committed_revision = revision_number(db)
            try: H.apply_plan(plan, root, db)
            except ValueError: pass
            else: raise AssertionError('An already committed plan was silently replayed')
            H.require(owned_state(db, owned) == committed and revision_number(db) == committed_revision, 'Replay rejection changed data'); checks += 1
            print(json.dumps(dict(native_mysql=True, passed=checks, mutations=result['counts'], late_guard_rollbacks=3,
                                  fk_rollback=1, anonymous_verified=False, ddl=0, http=0, production_env_reads=0), sort_keys=True))
        finally:
            if db is not None:
                try:
                    db.connection.rollback(); db.release_lock()
                    if seeded:
                        cleanup(db, owned)
                        H.require(primary_keys(db.connection) == baseline, 'Cleanup changed preexisting rows or left owned rows behind')
                        print('PASS: exact owned-ID cleanup; every preexisting business/source/library PK preserved')
                finally: db.close()
    return 0


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args == ['--check-safety']:
        SAFETY.safety_checks(); return 0
    H.require(not args, 'Only --check-safety is supported; pass isolated MYSQL_* via process env')
    return run(os.environ)


if __name__ == '__main__':
    raise SystemExit(main())
