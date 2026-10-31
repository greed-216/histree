# coding: utf-8
"""Portable correction-engine contracts: memory DB, literal files, no network/env."""
import copy
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid

import history_revision as H

NS = uuid.UUID('bcd1b8fa-53db-5a41-b31d-00fe35e75b11')
UID = lambda name: str(uuid.uuid5(NS, name))
TIME = '2026-01-01T00:00:00.000000+00:00'
TARGET = H.digest(b'synthetic-correction-target')
IDS = {name: UID(name) for name in ('old-person', 'sentinel', 'old-event', 'old-pe',
                                     'source', 'old-claim', 'old-dating', 'new-person',
                                     'new-event', 'new-relation', 'new-pe', 'new-claim',
                                     'new-dating', 'new-claim-relation')}
IDS['new-person'] = str(uuid.uuid5(H.CONTENT_NAMESPACE, 'person_synthetic_revision_new'))
REQUIRED = {
    'person': {'id', 'name'}, 'event': {'id', 'title'},
    'person_relationship': {'id', 'person_a', 'person_b', 'relation_type'},
    'person_event': {'id', 'person_id', 'event_id', 'role'},
    'fact_claim': {'id', 'subject_id', 'subject_table', 'field_path', 'claim_text'},
    'claim_structure': set(H.FIELDS['claim_structure']),
    'event_dating': {'id', 'event_id', 'claim_id', 'claim_sha256', 'precision_kind', 'basis'},
    'claim_relation': {'id', 'claim_id', 'related_claim_id', 'claim_sha256', 'related_sha256', 'relation_kind', 'note'},
}


def row(table, **values):
    result = dict.fromkeys(H.FIELDS[table])
    for field in set(result) & H.JSON_FIELDS:
        result[field] = []
    if 'created_at' in result:
        result['created_at'] = TIME
    if 'status' in result:
        result['status'] = 'published'
    if table == 'event':
        result['location_precision'] = 'unknown'
    result.update(values)
    return result


def fixture(root):
    raw = '\ufeff甲于九百年修城。\n'.encode('utf-8')
    path = root / 'raw/source.txt'; path.parent.mkdir(parents=True); path.write_bytes(raw)
    note = '原文：甲于九百年修城。；核对说明：合成主体与行动已核。'
    source_url = 'https://example.invalid/fixed-source'
    old_person = row('person', id=IDS['old-person'], name='合成甲', era='合成时代', description='正确旧档案。')
    sentinel = row('person', id=IDS['sentinel'], name='无关人物', description='不能改动。')
    old_event = row('event', id=IDS['old-event'], title='旧修城', start_year=900, end_year=900)
    old_pe = row('person_event', id=IDS['old-pe'], person_id=IDS['old-person'], event_id=IDS['old-event'], role='原角色保留')
    source = dict(id=IDS['source'], author=None, created_at=TIME, edition='合成固定底本',
                  note='合成出处', source_type='primary', title='合成原文', url=source_url)
    source_text = dict(source_id=IDS['source'], archive_url_sha256=H.digest(source_url.encode()),
                       archive_url=source_url, content=raw.decode(), content_sha256=H.digest(raw),
                       archive_blob_sha256=H.digest(raw), archive_commit='a' * 40, created_at=TIME)
    old_claim = row('fact_claim', id=IDS['old-claim'], subject_id=IDS['old-pe'], subject_table='person_event',
                    source_id=IDS['source'], field_path='role', claim_text='旧参与记载。', citation='合成逐字出处', note=note)
    structure = row('claim_structure', claim_id=IDS['old-claim'], note_sha256=H.digest(note.encode()),
                    quote_text='甲于九百年修城。', review_note='合成主体与行动已核。', review_state='recorded')
    old_dating = row('event_dating', id=IDS['old-dating'], event_id=IDS['old-event'], claim_id=IDS['old-claim'],
                     claim_sha256='1' * 64, earliest_year=900, latest_year=900, precision_kind='year',
                     basis='原文明记九百年。', review_state='reviewed')
    initial = {'person': [old_person, sentinel], 'event': [old_event], 'person_event': [old_pe],
               'source': [source], 'source_text': [source_text], 'fact_claim': [old_claim],
               'claim_structure': [structure], 'event_dating': [old_dating]}
    new_person = dict(id=IDS['new-person'], name='合成乙', aliases=[], era='合成时代',
                      birth_year=None, death_year=None, description='应连接的合成人物。', biography=None, status='published')
    new_event = dict(id=IDS['new-event'], title='新修城', description='乙于九百零一年修城。',
                     start_year=901, end_year=901, status='published')
    new_claim = dict(id=IDS['new-claim'], subject_table='person_event', subject_id=IDS['new-pe'],
                     field_path='role', source_id=IDS['source'], claim_text='乙参与新修城。',
                     citation='合成逐字出处', note=note, confidence=None, status='published')
    inserts = {
        'person': [new_person], 'event': [new_event],
        'person_relationship': [dict(id=IDS['new-relation'], person_a=IDS['new-person'], person_b=IDS['old-person'],
                                      relation_type='合成关系', description='明确合成关系。', status='published')],
        'person_event': [dict(id=IDS['new-pe'], person_id=IDS['new-person'], event_id=IDS['new-event'], role='主持新修城', status='published')],
        'fact_claim': [new_claim],
        'claim_structure': [dict(claim_id=IDS['new-claim'], note_sha256=H.digest(note.encode()), quote_text='甲于九百年修城。',
                                 review_note='合成主体与行动已核。', review_state='recorded')],
        'event_dating': [dict(id=IDS['new-dating'], event_id=IDS['new-event'], claim_id=IDS['new-claim'], claim_sha256='2' * 64,
                              earliest_year=901, latest_year=901, precision_kind='year', era_key=None, basis='合成独立年代。', review_state='reviewed')],
        'claim_relation': [dict(id=IDS['new-claim-relation'], claim_id=IDS['new-claim'], related_claim_id=IDS['old-claim'],
                                claim_sha256='2' * 64, related_sha256='1' * 64, relation_kind='identity_candidate', review_state='reviewed', note='合成关联依据。')],
    }
    protected = [dict(table=table, identity=H.identity(table, item), full_before=copy.deepcopy(item))
                 for table, values in initial.items() for item in values if table != 'person_event']
    membership = dict(table='person_event', any_of=[dict(person_id=IDS['old-person'])], expected_ids=[IDS['old-pe']])
    plan = dict(kind='reviewed_history_correction', target_fingerprint=TARGET,
                protected_paths={'raw/source.txt': H.digest(raw)},
                source_bindings=[dict(raw_path='raw/source.txt', raw_sha256=H.digest(raw), quote='甲于九百年修城。')],
                updates=[dict(table='person_event', id=IDS['old-pe'], key='pe_synthetic_old', before=dict(person_id=IDS['old-person']),
                              after=dict(person_id=IDS['new-person']), full_before=old_pe)], inserts=inserts,
                protected_rows=protected, membership_guards=[membership], invariants_after=[dict(membership, expected_ids=[])],
                new_people=[dict(new_person, key='person_synthetic_revision_new')])
    return plan, initial


class MemoryDatabase:
    def __init__(self, initial, writable=True):
        self.rows = {table: {H.token(table, value): copy.deepcopy(value) for value in values} for table, values in initial.items()}
        self.columns = {table: set(fields) for table, fields in H.FIELDS.items()}
        self.columns.update({table: set(values[0]) for table, values in initial.items() if table not in H.FIELDS})
        self.required_columns = REQUIRED
        self.target_fingerprint = TARGET; self.writable = writable; self.locked = False
        self.backup = None; self.calls = []; self.commits = 0; self.rollbacks = 0
        self.fail_table = None; self.after_update = None

    def schema(self, tables):
        self.calls.append(('schema', tuple(sorted(tables))))
        for table in tables:
            H.require(table in self.columns, 'Missing table')

    def begin(self, readonly):
        self.calls.append(('begin', readonly)); self.backup = copy.deepcopy(self.rows)

    def acquire_lock(self):
        H.require(self.writable, 'Read-only DB'); self.locked = True; self.calls.append(('lock',))

    def assert_lock(self):
        H.require(self.locked, 'Missing publication lock')

    def release_lock(self):
        self.locked = False; self.calls.append(('unlock',))

    def get_many(self, table, identities, lock=False):
        if lock: self.assert_lock()
        return {H.token(table, pk): copy.deepcopy(self.rows.get(table, {})[H.token(table, pk)])
                for pk in identities if H.token(table, pk) in self.rows.get(table, {})}

    def membership(self, guard, lock=False):
        if lock: self.assert_lock()
        return [value[H.KEYS[guard['table']][0]] for value in self.rows.get(guard['table'], {}).values()
                if any(all(value.get(k) == v for k, v in clause.items()) for clause in guard['any_of'])]

    def insert_many(self, table, values):
        self.assert_lock(); self.calls.append(('insert', table))
        if table == self.fail_table: raise ValueError('Injected middle insertion conflict')
        for value in values:
            pk = H.token(table, value); H.require(pk not in self.rows.setdefault(table, {}), 'Duplicate insert')
            self.rows[table][pk] = row(table, **value)

    def update(self, table, pk, after):
        self.assert_lock(); self.calls.append(('update', table)); self.rows[table][H.token(table, pk)].update(copy.deepcopy(after))
        if self.after_update: self.after_update(self)

    def commit(self):
        self.commits += 1; self.backup = None

    def rollback(self):
        self.rollbacks += 1
        if self.backup is not None: self.rows = self.backup; self.backup = None

    def close(self):
        self.rollback(); self.release_lock()


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name).resolve()
        self.addCleanup(self.tmp.cleanup); self.plan, initial = fixture(self.root)
        self.db = MemoryDatabase(initial); self.before = copy.deepcopy(self.db.rows)

    def mutation_calls(self):
        return [call for call in self.db.calls if call[0] in ('insert', 'update')]

    def apply(self):
        return H.apply_plan(self.plan, self.root, self.db)

    def assert_rolled_back(self):
        self.assertEqual(self.db.rows, self.before); self.assertEqual(self.db.commits, 0); self.assertFalse(self.db.locked)

    def test_real_adapter_bulk_queries_preserve_composite_keys_and_bound_size(self):
        calls = []
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def execute(self, sql, params):
                calls.append((sql, params))
                self.params = params
            def fetchall(self):
                return [dict(source_id=self.params[i], archive_url_sha256=self.params[i+1], content='literal')
                        for i in range(0, len(self.params), 2)]
        db = object.__new__(H.Database)
        db.writable = True; db.locked = True
        db.connection = SimpleNamespace(cursor=lambda *args: Cursor())
        db.columns = {'source_text': {'source_id', 'archive_url_sha256', 'content'}}
        db.store = SimpleNamespace(normalize=lambda table, row: row)
        ids = [dict(source_id=UID('bulk-' + str(i)), archive_url_sha256=H.digest(str(i).encode())) for i in range(201)]
        fake_mysql = SimpleNamespace(cursors=SimpleNamespace(DictCursor=object()))
        with patch.dict(sys.modules, {'pymysql': fake_mysql}):
            result = db.get_many('source_text', ids, lock=True)
        self.assertEqual(len(result), 201)
        self.assertEqual([len(params)//2 for _, params in calls], [100, 100, 1])
        self.assertTrue(all(sql.endswith(' FOR UPDATE') and 'SELECT *' in sql for sql, _ in calls))
        self.assertEqual(set(result), {H.token('source_text', pk) for pk in ids})

    def test_real_adapter_batch_insert_is_plain_insert_and_rejects_pk_update(self):
        calls = []
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def executemany(self, sql, params): calls.append((sql, params))
        db = object.__new__(H.Database); db.writable = True; db.locked = True
        db.connection = SimpleNamespace(cursor=lambda *args: Cursor())
        db.columns = {'person': set(H.FIELDS['person'])}
        db.store = SimpleNamespace(value=lambda table, field, value: value)
        rows = [dict(id=UID('insert-' + str(i)), name='synthetic') for i in range(201)]
        with patch.object(db, 'assert_lock'):
            db.insert_many('person', rows)
            with self.assertRaisesRegex(ValueError, 'primary key'):
                db.update('person', dict(id=IDS['old-person']), dict(id=IDS['sentinel']))
        self.assertEqual([len(params) for _, params in calls], [100, 100, 1])
        self.assertTrue(all(sql.startswith('INSERT INTO `person`') and 'IGNORE' not in sql and 'DUPLICATE' not in sql for sql, _ in calls))

    def test_readonly_preflight_has_no_mutations(self):
        self.assertEqual(H.check_plan(self.plan, self.root, self.db)['status'], 'before_state_matches')
        self.assertEqual(self.mutation_calls(), []); self.assertEqual(self.db.rows, self.before)

    def test_update_and_all_insert_types_commit_in_fk_order(self):
        result = self.apply(); self.assertEqual(result['status'], 'committed_pending_anonymous')
        self.assertNotIn('verified', result); self.assertEqual(self.db.commits, 1); self.assertFalse(self.db.locked)
        self.assertEqual([c[1] for c in self.db.calls if c[0] == 'insert'], list(H.ORDER))
        actual = self.db.rows['person_event'][(IDS['old-pe'],)]
        self.assertEqual(actual['person_id'], IDS['new-person']); self.assertEqual(actual['role'], '原角色保留')
        self.assertEqual(self.db.rows['person'][(IDS['sentinel'],)], self.before['person'][(IDS['sentinel'],)])
        self.assertEqual(H.verify_db(self.plan, self.root, self.db, result)['status'], 'after_state_matches')

    def test_full_old_row_stale_or_missing_rejects_before_writes(self):
        for alteration in ('stale', 'missing'):
            self.db.rows = copy.deepcopy(self.before)
            if alteration == 'stale': self.db.rows['person_event'][(IDS['old-pe'],)]['role'] = 'unreviewed'
            else: del self.db.rows['person_event'][(IDS['old-pe'],)]
            with self.assertRaisesRegex(ValueError, 'Full row guard'): self.apply()
            self.assertEqual(self.mutation_calls(), [])

    def test_changed_old_fields_must_match_full_before(self):
        self.plan['updates'][0]['before']['person_id'] = IDS['sentinel']
        with self.assertRaisesRegex(ValueError, 'before differs'): self.apply()
        self.assertEqual(self.db.calls, [])

    def test_full_before_requires_even_nullable_unmodified_columns(self):
        del self.plan['updates'][0]['full_before']['created_at']
        with self.assertRaisesRegex(ValueError, 'every actual column'): self.apply()
        self.assertEqual(self.mutation_calls(), [])

    def test_target_mismatch_rejects_before_lock_or_write(self):
        self.db.target_fingerprint = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'Target fingerprint'): self.apply()
        self.assertEqual(self.mutation_calls(), []); self.assertFalse(self.db.locked)

    def test_duplicate_update_insert_and_protected_identities_rejected(self):
        original = copy.deepcopy(self.plan)
        mutations = [lambda p: p['updates'].append(copy.deepcopy(p['updates'][0])),
                     lambda p: p['inserts']['person'].append(copy.deepcopy(p['inserts']['person'][0])),
                     lambda p: p['protected_rows'].append(copy.deepcopy(p['protected_rows'][0]))]
        for mutate in mutations:
            self.plan = copy.deepcopy(original); mutate(self.plan)
            with self.assertRaisesRegex(ValueError, 'Duplicate'): self.apply()
        self.assertEqual(self.mutation_calls(), [])

    def test_sources_library_delete_and_arbitrary_tables_cannot_mutate(self):
        for table in list(H.READ_ONLY_KEYS) + ['source;DROP TABLE person', 'DELETE', 'topic']:
            value = copy.deepcopy(self.plan); value['inserts'][table] = []
            with self.assertRaisesRegex(ValueError, 'allowlist'): H.validate_plan(value, self.root)
        self.assertEqual(self.db.calls, [])

    def test_primary_key_created_at_and_unknown_column_updates_rejected(self):
        for field, value in [('id', IDS['sentinel']), ('created_at', 'changed'), ('arbitrary_sql', 'DROP')]:
            plan = copy.deepcopy(self.plan); old = plan['updates'][0]['full_before']; old[field] = old.get(field, 'old')
            plan['updates'][0].update(before={field: old[field]}, after={field: value})
            with self.assertRaises(ValueError): H.validate_plan(plan, self.root)

    def test_already_present_new_id_is_never_an_idempotent_skip(self):
        value = self.plan['inserts']['person'][0]; self.db.rows['person'][(value['id'],)] = row('person', **value)
        with self.assertRaisesRegex(ValueError, 'INSERT ID already exists'): self.apply()
        self.assertEqual(self.mutation_calls(), [])

    def test_claim_structure_reviewed_is_an_invalid_enum(self):
        self.plan['inserts']['claim_structure'][0]['review_state'] = 'reviewed'
        with self.assertRaisesRegex(ValueError, 'review_state'): self.apply()
        self.assertEqual(self.db.calls, [])

    def test_zero_year_is_rejected_for_every_historical_year_column_before_db(self):
        for table, fields in [('person', ('birth_year', 'death_year')), ('event', ('start_year', 'end_year')),
                              ('event_dating', ('earliest_year', 'latest_year'))]:
            for field in fields:
                with self.subTest(table=table, field=field):
                    plan = copy.deepcopy(self.plan); plan['inserts'][table][0][field] = 0
                    if table == 'person': plan['new_people'][0][field] = 0
                    with self.assertRaisesRegex(ValueError, 'no year zero'):
                        H.apply_plan(plan, self.root, self.db)
                    self.assertEqual(self.db.calls, [])
                    for year in (-1, 1, None):
                        H.validate_values(table, {field: year})
        # The same validator covers UPDATE new values and full old rows too.
        event = next(g['full_before'] for g in self.plan['protected_rows'] if g['table'] == 'event')
        self.plan['updates'].append(dict(table='event', id=event['id'], full_before=event,
                                        before={'start_year': 900}, after={'start_year': 0}))
        with self.assertRaisesRegex(ValueError, 'no year zero'): H.apply_plan(self.plan, self.root, self.db)
        self.assertEqual(self.db.calls, [])

    def test_nonnullable_null_bad_hash_and_bad_timestamp_are_rejected_before_connect(self):
        for table, field, value in [('person', 'name', None), ('event_dating', 'claim_sha256', 'bad'), ('person', 'created_at', '2026-01-01')]:
            plan = copy.deepcopy(self.plan); plan['inserts'][table][0][field] = value
            if table == 'person': plan['new_people'][0][field] = value
            with self.assertRaises(ValueError): H.validate_plan(plan, self.root)
        self.assertEqual(self.db.calls, [])

    def test_protected_library_metadata_and_locator_rows_accept_json_and_numeric_fields(self):
        asset = H.digest(b'asset')
        values = {'library_book': dict(book_key='synthetic-book', metadata={}, paragraph_count=1),
                  'library_asset': dict(id=asset, source_file='raw/source.txt', source_sha256=H.digest(b'raw')),
                  'library_paragraph': dict(id='synthetic-book-p1', char_start=0, char_end=12, flags=[]),
                  'library_source_link': dict(source_id=IDS['source'], archive_url_sha256='a' * 64,
                                              snapshot_sha256='b' * 64, paragraph_id='synthetic-book-p1')}
        for table, value in values.items():
            self.db.rows[table] = {H.token(table, value): copy.deepcopy(value)}
            self.db.columns[table] = set(value)
            self.plan['protected_rows'].append(dict(table=table, identity=H.identity(table, value), full_before=value))
        H.check_plan(self.plan, self.root, self.db)
        self.assertEqual(self.mutation_calls(), [])

    def test_middle_insertion_failure_rolls_back_all_earlier_tables(self):
        self.db.fail_table = 'claim_relation'
        with self.assertRaisesRegex(ValueError, 'middle insertion'): self.apply()
        self.assertGreater(len(self.mutation_calls()), 1); self.assert_rolled_back()

    def test_afterguard_detects_unmodified_updated_field_tamper(self):
        self.db.after_update = lambda db: db.rows['person_event'][(IDS['old-pe'],)].update(role='late unreviewed role')
        with self.assertRaisesRegex(ValueError, 'Full row guard'): self.apply()
        self.assert_rolled_back()

    def test_afterguard_detects_readonly_composite_source_bytes_tamper(self):
        key = next(iter(self.db.rows['source_text']))
        self.db.after_update = lambda db: db.rows['source_text'][key].update(content='changed raw text')
        with self.assertRaisesRegex(ValueError, 'Full row guard'): self.apply()
        self.assert_rolled_back()

    def test_afterguard_locks_insert_defaults_not_only_explicit_columns(self):
        self.db.after_update = lambda db: db.rows['person'][(IDS['new-person'],)].update(created_at='2026-02-01T00:00:00.000000+00:00')
        with self.assertRaisesRegex(ValueError, 'Full row guard'): self.apply()
        self.assert_rolled_back()

    def test_membership_extra_row_and_wrong_post_invariant_rollback(self):
        self.plan['invariants_after'][0]['expected_ids'] = [IDS['old-pe']]
        with self.assertRaisesRegex(ValueError, 'Membership guard'): self.apply()
        self.assert_rolled_back()
        self.plan['invariants_after'][0]['expected_ids'] = []
        extra = row('person_event', id=UID('unexpected-member'), person_id=IDS['old-person'], event_id=IDS['old-event'], role='extra')
        self.db.rows['person_event'][(extra['id'],)] = extra
        with self.assertRaisesRegex(ValueError, 'Membership guard'): self.apply()

    def test_membership_requires_after_predicate_and_uuid_equality_only(self):
        for change in ('missing-after', 'sql', 'duplicate-id'):
            value = copy.deepcopy(self.plan)
            if change == 'missing-after': value['invariants_after'] = []
            elif change == 'sql': value['membership_guards'][0]['any_of'] = [{'role': 'arbitrary'}]
            else: value['membership_guards'][0]['expected_ids'] *= 2
            with self.assertRaises(ValueError): H.validate_plan(value, self.root)

    def test_raw_bytes_quotes_and_symlink_paths_are_not_normalized(self):
        value = copy.deepcopy(self.plan); value['source_bindings'][0]['quote'] = '甲 于九百年修城。'
        with self.assertRaisesRegex(ValueError, 'Quote absent'): H.validate_plan(value, self.root)
        source = self.root / 'raw/source.txt'; source.write_bytes(source.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'SHA changed'): self.apply()
        self.assertEqual(self.db.calls, [])
        value = copy.deepcopy(self.plan); value['protected_paths'] = {'../outside': 'a' * 64}
        with self.assertRaisesRegex(ValueError, 'relative'): H.validate_plan(value, self.root)

    def test_file_change_during_transaction_aborts_commit(self):
        self.db.after_update = lambda db: (self.root / 'raw/source.txt').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'SHA changed'): self.apply()
        self.assert_rolled_back()

    def test_readonly_adapter_cannot_apply_and_verify_does_not_mutate(self):
        self.db.writable = False
        with self.assertRaisesRegex(ValueError, 'writable'): self.apply()
        self.assertEqual(self.mutation_calls(), [])
        self.db.writable = True; receipt = self.apply(); count = len(self.mutation_calls())
        H.verify_db(self.plan, self.root, self.db, receipt)
        self.assertEqual(len(self.mutation_calls()), count)
        self.db.rows['person'][(IDS['new-person'],)]['family'] = ['unreviewed']
        with self.assertRaisesRegex(ValueError, 'Full row guard'): H.verify_db(self.plan, self.root, self.db, receipt)

    def indexed_fixture(self):
        # Existing unindexed fixture IDs remain fixed. Only this indexing test
        # rekeys three identities whose logical keys the index must resolve.
        logical = {'source': 'synthetic-source', 'new-pe': 'pe_synthetic_revision_new',
                   'new-claim': 'claim_synthetic_revision_new'}
        replacements = {IDS[name]: str(uuid.uuid5(H.CONTENT_NAMESPACE, key)) for name, key in logical.items()}
        plan = copy.deepcopy(self.plan)
        initial = {table: list(copy.deepcopy(values).values()) for table, values in self.before.items()}
        text = json.dumps([plan, initial])
        for old, new in replacements.items(): text = text.replace(old, new)
        plan, initial = json.loads(text)
        plan['key_map'] = {replacements[IDS[name]]: key for name, key in logical.items()}
        plan['key_map'][IDS['new-person']] = 'person_synthetic_revision_new'
        plan['new_claims'] = copy.deepcopy(plan['inserts']['fact_claim'])
        return plan, MemoryDatabase(initial)

    def test_index_metadata_uses_shared_uuid_namespace_and_exact_insert_rows(self):
        plan, db = self.indexed_fixture()
        plan['new_claims'][0]['key'] = 'claim_synthetic_revision_new'
        result = H.apply_plan(plan, self.root, db)
        self.assertEqual(result['status'], 'committed_pending_anonymous')
        self.assertEqual(db.commits, 1)

    def test_key_map_wrong_namespace_duplicate_key_and_invalid_shape_reject_before_db(self):
        valid = {IDS['new-person']: 'person_synthetic_revision_new'}
        for change in ('wrong-ns', 'duplicate-key', 'not-map', 'nontext-key', 'noncanonical-id'):
            with self.subTest(change=change):
                plan = copy.deepcopy(self.plan); plan['key_map'] = copy.deepcopy(valid)
                if change == 'wrong-ns': plan['key_map'] = {UID('old-namespace'): 'person_synthetic_revision_new'}
                elif change == 'duplicate-key': plan['key_map'][UID('duplicate')] = 'person_synthetic_revision_new'
                elif change == 'not-map': plan['key_map'] = []
                elif change == 'nontext-key': plan['key_map'] = {IDS['new-person']: 1}
                else: plan['key_map'] = {IDS['new-person'].upper(): 'person_synthetic_revision_new'}
                with self.assertRaises(ValueError): H.apply_plan(plan, self.root, self.db)
                self.assertEqual(self.db.calls, [])

    def test_new_person_wrong_namespace_or_nonperson_key_reject_before_db(self):
        for change in ('wrong-ns', 'prefix'):
            plan = copy.deepcopy(self.plan)
            key = 'person_synthetic_revision_new' if change == 'wrong-ns' else 'event_synthetic_revision_new'
            ident = UID('new-person') if change == 'wrong-ns' else str(uuid.uuid5(H.CONTENT_NAMESPACE, key))
            plan['inserts']['person'][0]['id'] = ident
            plan['new_people'][0].update(id=ident, key=key)
            with self.assertRaisesRegex(ValueError, 'person_|namespace'): H.apply_plan(plan, self.root, self.db)
        self.assertEqual(self.db.calls, [])

    def test_new_claims_missing_extra_duplicate_changed_or_unmapped_reject_before_db(self):
        for change in ('missing', 'extra', 'duplicate', 'changed', 'extra-default', 'no-map', 'unmapped-source', 'wrong-key', 'non-list'):
            with self.subTest(change=change):
                plan, db = self.indexed_fixture()
                if change == 'missing': plan['new_claims'] = []
                elif change == 'extra': plan['new_claims'].append(dict(plan['new_claims'][0], id=UID('extra-index-row')))
                elif change == 'duplicate': plan['new_claims'].append(copy.deepcopy(plan['new_claims'][0]))
                elif change == 'changed': plan['new_claims'][0]['claim_text'] = 'unreviewed index text'
                elif change == 'extra-default': plan['new_claims'][0]['created_at'] = TIME
                elif change == 'no-map': del plan['key_map']
                elif change == 'unmapped-source': del plan['key_map'][plan['new_claims'][0]['source_id']]
                elif change == 'wrong-key': plan['new_claims'][0]['key'] = 'claim_wrong'
                else: plan['new_claims'] = {}
                with self.assertRaises(ValueError): H.apply_plan(plan, self.root, db)
                self.assertEqual(db.calls, [])

    def test_new_claim_index_requires_published_complete_fields(self):
        for field, value in [('status', 'draft'), ('note', None), ('claim_text', ''), ('citation', None)]:
            with self.subTest(field=field):
                plan, db = self.indexed_fixture()
                plan['new_claims'][0][field] = value; plan['inserts']['fact_claim'][0][field] = value
                with self.assertRaises(ValueError): H.apply_plan(plan, self.root, db)
                self.assertEqual(db.calls, [])

    def test_new_people_metadata_must_match_actual_person_insert(self):
        self.plan['new_people'][0]['name'] = 'different'
        with self.assertRaisesRegex(ValueError, 'metadata differs'): self.apply()
        self.assertEqual(self.db.calls, [])

    def test_cli_bad_sha_and_bad_evidence_do_not_connect(self):
        path = self.root / 'plan.json'; path.write_bytes(H.encoded(self.plan))
        args = [str(path), '--root', str(self.root), '--mysql-env', str(self.root / 'explicit-only.env')]
        with patch.object(H, 'Database', side_effect=AssertionError('No connection allowed')):
            with self.assertRaisesRegex(ValueError, 'exact'): H.main(args + ['--apply', '--expected-plan-sha256', '0' * 64])
            (self.root / 'raw/source.txt').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'SHA changed'): H.main(args)

    def test_cli_receipt_is_not_anonymous_verified_and_cannot_be_auto_resumed(self):
        path = self.root / 'plan.json'; path.write_bytes(H.encoded(self.plan)); digest = H.digest(path.read_bytes())
        args = [str(path), '--root', str(self.root), '--mysql-env', str(self.root / 'explicit-only.env')]
        with patch.object(H, 'Database', return_value=self.db), redirect_stdout(StringIO()):
            H.main(args + ['--apply', '--expected-plan-sha256', digest])
        receiptpath = path.with_name('publication-mysql.json'); receipt = json.loads(receiptpath.read_bytes())
        self.assertEqual(receipt['status'], 'committed_pending_anonymous'); self.assertNotIn('verified', receipt)
        self.assertEqual(receipt['plan_sha256'], digest); self.assertEqual(receipt['new_people'], self.plan['new_people'])
        with self.assertRaisesRegex(ValueError, 'Receipt exists'), patch.object(H, 'Database', side_effect=AssertionError('Must not reconnect')):
            H.main(args + ['--apply', '--expected-plan-sha256', digest])

    def test_cli_plan_bytes_are_rechecked_before_commit(self):
        path = self.root / 'plan.json'; path.write_bytes(H.encoded(self.plan)); digest = H.digest(path.read_bytes())
        self.db.after_update = lambda db: path.write_bytes(path.read_bytes() + b' ')
        args = [str(path), '--root', str(self.root), '--mysql-env', str(self.root / 'explicit-only.env'), '--apply', '--expected-plan-sha256', digest]
        with patch.object(H, 'Database', return_value=self.db), self.assertRaisesRegex(ValueError, 'SHA changed'):
            H.main(args)
        self.assert_rolled_back(); self.assertFalse(path.with_name('publication-mysql.json').exists())


if __name__ == '__main__':
    unittest.main()
