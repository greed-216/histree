# coding: utf-8
"""Execute one reviewed_history_correction with full-row transactional guards.

Default CLI is a read-only before-state check. --apply requires an exact file SHA;
--verify-db independently checks the after state and never resumes partial work.
Only eight fixed tables may be changed; six additional source/library tables are
read-only guards. This module does no DDL, DELETE, HTTP or anonymous acceptance.
API adapters own their connection and implement Database's bounded row methods.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import uuid

ORDER = ('person', 'event', 'person_relationship', 'person_event', 'fact_claim',
         'claim_structure', 'event_dating', 'claim_relation')
FIELDS = {
    'person': 'aliases biography birth_year courtesy_name created_at death_year description era faction family historical_evaluation id image_url name native_place references social_relations status tags'.split(),
    'event': 'created_at description dynasty end_year id image_url impact_level location_lat location_lng location_modern_name location_name location_note location_precision phases references start_year status tags time_original title'.split(),
    'person_relationship': 'created_at description id person_a person_b relation_type status'.split(),
    'person_event': 'created_at event_id id person_id role status'.split(),
    'fact_claim': 'citation claim_text confidence created_at field_path id note source_id status subject_id subject_table'.split(),
    'claim_structure': 'claim_id note_sha256 quote_text review_note review_state'.split(),
    'event_dating': 'id event_id claim_id claim_sha256 earliest_year latest_year precision_kind era_key basis review_state'.split(),
    'claim_relation': 'id claim_id related_claim_id claim_sha256 related_sha256 relation_kind review_state note'.split(),
}
NOT_NULL = {
    'person': {'id', 'name', 'created_at', 'status'},
    'event': {'id', 'title', 'created_at', 'status', 'location_precision'},
    'person_relationship': {'id', 'created_at', 'person_a', 'person_b', 'relation_type', 'status'},
    'person_event': {'id', 'created_at', 'person_id', 'event_id', 'role', 'status'},
    'fact_claim': {'id', 'created_at', 'claim_text', 'field_path', 'subject_id', 'subject_table', 'status'},
    'claim_structure': set(FIELDS['claim_structure']),
    'event_dating': {'id', 'event_id', 'claim_id', 'claim_sha256', 'precision_kind', 'basis', 'review_state'},
    'claim_relation': set(FIELDS['claim_relation']),
}
READ_ONLY_KEYS = {'source': ('id',), 'source_text': ('source_id', 'archive_url_sha256'),
                  'library_source_link': ('source_id', 'archive_url_sha256'),
                  'library_paragraph': ('id',), 'library_asset': ('id',),
                  'library_book': ('book_key',)}
KEYS = {table: ('claim_id',) if table == 'claim_structure' else ('id',) for table in ORDER}
KEYS.update(READ_ONLY_KEYS)
UUID_FIELDS = {'id', 'person_id', 'event_id', 'person_a', 'person_b', 'subject_id',
               'source_id', 'claim_id', 'related_claim_id'}
JSON_FIELDS = {'aliases', 'family', 'references', 'social_relations', 'tags', 'phases'}
INTEGER_FIELDS = {'birth_year', 'death_year', 'start_year', 'end_year', 'earliest_year',
                  'latest_year', 'impact_level'}
NUMBER_FIELDS = {'location_lat', 'location_lng', 'confidence'}
ENUMS = {'status': ('draft', 'published'),
         'location_precision': ('site', 'approximate', 'region', 'unknown'),
         'precision_kind': ('year', 'approximate', 'range', 'relative', 'era', 'unknown'),
         'relation_kind': ('corroborates', 'conflicts', 'identity_candidate')}
FOREIGN_KEYS = {
    'person_relationship': {('person_a', 'person', 'id'), ('person_b', 'person', 'id')},
    'person_event': {('person_id', 'person', 'id'), ('event_id', 'event', 'id')},
    'fact_claim': {('source_id', 'source', 'id')},
    'claim_structure': {('claim_id', 'fact_claim', 'id')},
    'event_dating': {('claim_id', 'fact_claim', 'id'), ('event_id', 'event', 'id')},
    'claim_relation': {('claim_id', 'fact_claim', 'id'), ('related_claim_id', 'fact_claim', 'id')},
}
LOCK = 'histree-content-publish'
BATCH_SIZE = 100


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def equal(left, right):
    return encoded(left) == encoded(right)


def uuid_value(value):
    require(isinstance(value, str), 'UUID must be text')
    try:
        require(str(uuid.UUID(value)) == value, 'UUID must use canonical lowercase form')
    except (ValueError, AttributeError) as error:
        raise ValueError('Invalid canonical UUID') from error


def identity(table, row):
    return {field: row[field] for field in KEYS[table]}


def token(table, row):
    return tuple(row[field] for field in KEYS[table])


def validate_identity(table, value):
    require(table in KEYS, 'Table outside fixed guard allowlist')
    require(isinstance(value, dict) and set(value) == set(KEYS[table]), 'Wrong primary-key identity')
    for field, item in value.items():
        if field.endswith('sha256') or table == 'library_asset':
            require(isinstance(item, str) and re.fullmatch('[a-f0-9]{64}', item), 'Invalid hash identity')
        elif table in ('library_paragraph', 'library_book'):
            require(isinstance(item, str) and 0 < len(item) <= 128 and not any(ord(c) < 32 for c in item), 'Invalid library identity')
        else:
            uuid_value(item)


def validate_values(table, row):
    require(isinstance(row, dict) and row, 'Row must be a nonempty object')
    if table not in FIELDS:
        require(table in READ_ONLY_KEYS, 'Unknown read-only table')
        require(all(isinstance(field, str) and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', field) for field in row), 'Invalid read-only column')
        encoded(row)
        return
    require(set(row) <= set(FIELDS[table]), 'Unknown mutable column: ' + table)
    for field, value in row.items():
        require(isinstance(field, str) and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', field), 'Invalid column identifier')
        if value is None:
            require(field not in NOT_NULL[table], 'NULL in nonnullable column: ' + field)
            continue
        if field in JSON_FIELDS:
            require(isinstance(value, (dict, list)), 'JSON column requires structured JSON: ' + field)
        elif field in UUID_FIELDS and table not in ('library_paragraph', 'library_asset'):
            uuid_value(value)
        elif field in INTEGER_FIELDS:
            require(type(value) is int, 'Integer column requires an integer: ' + field)
            if field.endswith('_year'):
                require(value != 0, 'Historical dates have no year zero')
        elif field in NUMBER_FIELDS:
            require(type(value) in (int, float) and math.isfinite(value), 'Invalid numerical value')
        else:
            require(isinstance(value, str), 'Text column requires text: ' + field)
        if field.endswith('sha256'):
            require(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value), 'Invalid SHA256 column')
        if field == 'created_at':
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0, 'created_at requires UTC')
        if table in FIELDS and field in ENUMS:
            require(value in ENUMS[field], 'Unsupported enum value: ' + field)
        if field == 'review_state' and table in FIELDS:
            allowed = ('recorded', 'deferred', 'unparsed') if table == 'claim_structure' else ('proposed', 'reviewed')
            require(value in allowed, 'Unsupported review_state for ' + table)
    encoded(row)  # Reject NaN and non-JSON values in nested JSON too.


def relative_file(root, name):
    require(isinstance(name, str) and name and '\x00' not in name, 'Invalid protected path')
    relative = Path(name)
    require(not relative.is_absolute() and '..' not in relative.parts, 'Path must be relative to content root')
    current = root
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), 'Symlink in protected path')
    path = current.resolve()
    require(root in path.parents and path.is_file(), 'Protected file absent or outside root')
    return path


def validate_files(plan, root):
    root = Path(root).resolve()
    require(root.is_dir(), 'Content root is absent')
    protected = plan.get('protected_paths')
    require(isinstance(protected, dict) and protected, 'Nonempty protected_paths mapping required')
    cache = {}
    for name, expected in protected.items():
        require(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected), 'Invalid protected SHA')
        raw = relative_file(root, name).read_bytes()
        require(digest(raw) == expected, 'Protected file SHA changed: ' + name)
        cache[name] = raw
    bindings = plan.get('source_bindings')
    require(isinstance(bindings, list) and bindings, 'Explicit raw source bindings required')
    for binding in bindings:
        name = binding['raw_path']
        require(name in protected and binding['raw_sha256'] == protected[name], 'Source must bind a protected raw file')
        quote = binding['quote']
        require(isinstance(quote, str) and quote and quote in cache[name].decode('utf-8'), 'Quote absent from exact raw source')
    return root


def validate_membership(guards):
    require(isinstance(guards, list), 'Membership guards must be a list')
    signatures = set()
    for guard in guards:
        table = guard['table']
        require(table in ORDER, 'Membership queries only support fixed single-key mutable tables')
        clauses, expected = guard['any_of'], guard['expected_ids']
        require(isinstance(clauses, list) and 0 < len(clauses) <= 1000, 'Empty/oversized membership predicate')
        require(isinstance(expected, list) and all(isinstance(value, str) for value in expected) and len(expected) == len(set(expected)), 'Duplicate/invalid membership expected ID')
        for value in expected:
            uuid_value(value)
        seen = set()
        for clause in clauses:
            require(isinstance(clause, dict) and clause and set(clause) <= set(FIELDS[table]) & UUID_FIELDS, 'Membership permits only UUID equality columns')
            for value in clause.values():
                uuid_value(value)
            require(encoded(clause) not in seen, 'Duplicate membership clause')
            seen.add(encoded(clause))
        signature = encoded({'table': table, 'any_of': sorted(clauses, key=encoded)})
        require(signature not in signatures, 'Duplicate membership guard')
        signatures.add(signature)
    return signatures


def validate_plan(plan, root):
    require(isinstance(plan, dict) and plan.get('kind') == 'reviewed_history_correction', 'Unsupported plan kind')
    require(isinstance(plan.get('target_fingerprint'), str) and re.fullmatch('[a-f0-9]{64}', plan['target_fingerprint']), 'Target fingerprint must be SHA256')
    plan = json.loads(encoded(plan))  # Own immutable-by-convention copy; caller mutation cannot affect execution.
    validate_files(plan, root)
    updates, inserts, protected = plan.get('updates', []), plan.get('inserts', {}), plan.get('protected_rows', [])
    require(isinstance(updates, list) and isinstance(inserts, dict) and isinstance(protected, list), 'Invalid plan row collections')
    require(set(inserts) <= set(ORDER), 'INSERT table outside fixed mutation allowlist')
    seen = set()
    for update in updates:
        table = update['table']
        require(table in ORDER, 'UPDATE table outside fixed mutation allowlist')
        old, before, after = update['full_before'], update['before'], update['after']
        validate_values(table, old); validate_values(table, before); validate_values(table, after)
        require(set(before) == set(after) and before, 'Changed old/new field sets must match')
        require(not (set(after) & (set(KEYS[table]) | {'created_at'})), 'Cannot update primary key/created_at')
        require(all(field in old and equal(old[field], value) for field, value in before.items()), 'Changed before differs from full_before')
        require(all(not equal(before[field], value) for field, value in after.items()), 'No-op changed field')
        pk = identity(table, old); validate_identity(table, pk)
        require(update.get('id') == next(iter(pk.values())), 'UPDATE ID differs from full_before primary key')
        item = (table, token(table, old)); require(item not in seen, 'Duplicate mutation identity'); seen.add(item)
    for table, values in inserts.items():
        require(isinstance(values, list), 'INSERT rows must be a list')
        for row in values:
            validate_values(table, row); validate_identity(table, identity(table, row))
            item = (table, token(table, row)); require(item not in seen, 'Duplicate mutation identity'); seen.add(item)
    require(seen, 'Plan has no mutations')
    for guard in protected:
        table, pk, old = guard['table'], guard['identity'], guard['full_before']
        validate_identity(table, pk); validate_values(table, old)
        require(equal(identity(table, old), pk), 'Protected identity differs from full_before')
        item = (table, token(table, old)); require(item not in seen, 'Duplicate/changed protected identity'); seen.add(item)
    before_signatures = validate_membership(plan.get('membership_guards', []))
    after_signatures = validate_membership(plan.get('invariants_after', []))
    require(before_signatures <= after_signatures, 'Every membership preguard needs an explicit matching after predicate')
    people = plan.get('new_people', [])
    require(isinstance(people, list), 'new_people must be a list')
    by_id = {row['id']: row for row in inserts.get('person', [])}
    require(len(people) == len(by_id) and {row['id'] for row in people} == set(by_id), 'new_people must describe every inserted person exactly once')
    for person in people:
        require(isinstance(person.get('key'), str) and person['key'], 'New person metadata needs a logical key')
        require(all(field == 'key' or field in by_id[person['id']] and equal(value, by_id[person['id']][field]) for field, value in person.items()), 'New person metadata differs from INSERT')
    return plan


class Database:
    """Owned MySQL connection. All identifiers are fixed table/column allowlists."""
    def __init__(self, mysql_env, writable=False):
        from mysql_content_store import MysqlContentStore
        self.store = MysqlContentStore(Path(mysql_env), writable=False)
        self.connection = self.store.connection
        self.target_fingerprint = self.store.target_fingerprint
        self.writable = writable
        self.columns = self.store.columns
        self.required_columns = {}
        self.locked = False

    def schema(self, tables):
        for table in tables:
            require(table in KEYS and table in self.columns, 'Missing/unsupported table: ' + table)
            if table in FIELDS:
                require(self.columns[table] == set(FIELDS[table]), 'Mutable schema columns differ: ' + table)
        with self.connection.cursor() as cursor:
            for table in tables:
                cursor.execute('SELECT ENGINE FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=%s', (table,))
                require(cursor.fetchone() == ('InnoDB',), 'Nontransactional table: ' + table)
                cursor.execute('SELECT column_name FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name=%s AND index_name=%s ORDER BY seq_in_index', (table, 'PRIMARY'))
                require(tuple(row[0] for row in cursor.fetchall()) == KEYS[table], 'Unexpected primary key: ' + table)
                if table in FOREIGN_KEYS:
                    cursor.execute('SELECT column_name,referenced_table_name,referenced_column_name FROM information_schema.key_column_usage WHERE table_schema=DATABASE() AND table_name=%s AND referenced_table_name IS NOT NULL', (table,))
                    require(FOREIGN_KEYS[table] <= set(cursor.fetchall()), 'Required FK missing: ' + table)
                cursor.execute('SELECT column_name,is_nullable,column_default,extra FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=%s', (table,))
                self.required_columns[table] = {name for name, nullable, default, extra in cursor.fetchall() if nullable == 'NO' and default is None and 'auto_increment' not in extra}

    def begin(self, readonly):
        self.connection.rollback()  # Only our own metadata-read transaction exists here.
        with self.connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
            cursor.execute('SET TRANSACTION READ ONLY' if readonly else 'SET TRANSACTION READ WRITE')
        self.connection.begin()

    def acquire_lock(self):
        require(self.writable, 'Writable adapter required')
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK('histree-content-publish',0)")
            require(cursor.fetchone()[0] == 1, 'Another content publisher is active')
        self.locked = True

    def assert_lock(self):
        require(self.writable and self.locked, 'Global publication lock is required')
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT IS_USED_LOCK('histree-content-publish')=CONNECTION_ID()")
            require(cursor.fetchone()[0] == 1, 'Global publication lock was lost')

    def release_lock(self):
        if self.locked:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT RELEASE_LOCK('histree-content-publish')")
            self.locked = False

    def column(self, table, field):
        require(table in KEYS and field in self.columns.get(table, ()) and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', field), 'Invalid bounded SQL column')
        return '`' + field + '`'

    def get_many(self, table, identities, lock=False):
        require(not lock or self.writable and self.locked, 'Locking read needs publication lock')
        import pymysql
        result = {}
        for start in range(0, len(identities), BATCH_SIZE):
            chunk = identities[start:start + BATCH_SIZE]
            for pk in chunk:
                validate_identity(table, pk)
            predicate = ' OR '.join('(' + ' AND '.join(self.column(table, field) + '=%s' for field in KEYS[table]) + ')' for _ in chunk)
            params = [pk[field] for pk in chunk for field in KEYS[table]]
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute('SELECT * FROM `' + table + '` WHERE ' + predicate + (' FOR UPDATE' if lock else ''), params)
                for value in cursor.fetchall():
                    row = self.store.normalize(table, value); key = token(table, row)
                    require(key not in result, 'Duplicate DB primary key')
                    result[key] = row
        return result

    def membership(self, guard, lock=False):
        table = guard['table']; pk = KEYS[table][0]
        require(not lock or self.writable and self.locked, 'Membership locking read needs publication lock')
        predicate = ' OR '.join('(' + ' AND '.join(self.column(table, field) + '=%s' for field in clause) + ')' for clause in guard['any_of'])
        params = [value for clause in guard['any_of'] for value in clause.values()]
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT ' + self.column(table, pk) + ' FROM `' + table + '` WHERE ' + predicate + ' ORDER BY ' + self.column(table, pk) + ' LIMIT %s' + (' FOR UPDATE' if lock else ''), params + [len(guard['expected_ids']) + 1])
            return [row[0] for row in cursor.fetchall()]

    def value(self, table, field, value):
        if field == 'created_at' and value is not None:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0, 'created_at requires UTC')
            return parsed.replace(tzinfo=None)
        return self.store.value(table, field, value)

    def insert_many(self, table, rows):
        require(table in ORDER and self.writable, 'INSERT outside mutation allowlist'); self.assert_lock()
        shapes = {}
        for row in rows:
            validate_values(table, row); validate_identity(table, identity(table, row))
            shapes.setdefault(tuple(sorted(row)), []).append(row)
        with self.connection.cursor() as cursor:
            for fields, values in shapes.items():
                sql = 'INSERT INTO `' + table + '` (' + ','.join(self.column(table, field) for field in fields) + ') VALUES (' + ','.join('%s' for _ in fields) + ')'
                for start in range(0, len(values), BATCH_SIZE):
                    cursor.executemany(sql, [[self.value(table, field, row[field]) for field in fields] for row in values[start:start + BATCH_SIZE]])

    def update(self, table, pk, after):
        require(table in ORDER and self.writable, 'UPDATE outside mutation allowlist'); self.assert_lock()
        validate_identity(table, pk); validate_values(table, after)
        require(not (set(after) & (set(KEYS[table]) | {'created_at'})), 'Cannot update primary key/created_at')
        fields = list(after)
        with self.connection.cursor() as cursor:
            sql = 'UPDATE `' + table + '` SET ' + ','.join(self.column(table, field) + '=%s' for field in fields) + ' WHERE ' + ' AND '.join(self.column(table, field) + '=%s' for field in KEYS[table])
            cursor.execute(sql, [self.value(table, field, after[field]) for field in fields] + [pk[field] for field in KEYS[table]])
            require(cursor.rowcount == 1, 'UPDATE did not affect exactly one row')

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        try:
            self.connection.rollback()
            self.release_lock()
        finally:
            self.connection.close()


def schema_guard(plan, db):
    tables = {u['table'] for u in plan.get('updates', [])} | set(plan.get('inserts', {})) | {g['table'] for g in plan.get('protected_rows', [])} | {g['table'] for name in ('membership_guards', 'invariants_after') for g in plan.get(name, [])}
    db.schema(tables)
    require(db.target_fingerprint == plan['target_fingerprint'], 'Target fingerprint differs from reviewed plan')
    for entry in plan.get('updates', []) + plan.get('protected_rows', []):
        require(set(entry['full_before']) == db.columns[entry['table']], 'full_before must contain every actual column: ' + entry['table'])
    for table, values in plan.get('inserts', {}).items():
        for row in values:
            require(db.required_columns[table] <= set(row) <= db.columns[table], 'INSERT omits required/contains unknown columns: ' + table)


def fetch_entries(db, entries, lock):
    grouped = {}
    for entry in entries:
        grouped.setdefault(entry['table'], []).append(entry['identity'])
    found = {}
    for table, ids in grouped.items():
        found[table] = db.get_many(table, ids, lock=lock)
    return found


def state_entries(plan, after=False):
    entries = []
    for update in plan.get('updates', []):
        row = dict(update['full_before'], **update['after']) if after else update['full_before']
        entries.append(dict(table=update['table'], identity=identity(update['table'], row), expected=row, exact=True))
    for guard in plan.get('protected_rows', []):
        entries.append(dict(table=guard['table'], identity=guard['identity'], expected=guard['full_before'], exact=True))
    for table, values in plan.get('inserts', {}).items():
        for row in values:
            entries.append(dict(table=table, identity=identity(table, row), expected=row if after else None, exact=False))
    return entries


def guard_state(db, entries, membership, lock=False):
    found = fetch_entries(db, entries, lock)
    actual = []
    for entry in entries:
        table = entry['table']; row = found[table].get(token(table, entry['identity'])); expected = entry['expected']
        if expected is None:
            require(row is None, 'INSERT ID already exists: ' + table)
        elif entry['exact']:
            require(row is not None and equal(row, expected), 'Full row guard changed: ' + table)
        else:
            require(row is not None and all(field in row and equal(row[field], value) for field, value in expected.items()), 'Inserted explicit fields differ: ' + table)
        if row is not None:
            actual.append(dict(table=table, identity=entry['identity'], full_after=copy.deepcopy(row)))
    for guard in membership:
        require(sorted(db.membership(guard, lock=lock)) == sorted(guard['expected_ids']), 'Membership guard changed: ' + guard['table'])
    return actual


def summary(plan):
    return dict(updates=len(plan.get('updates', [])), inserts={table: len(rows) for table, rows in plan.get('inserts', {}).items()}, protected_rows=len(plan.get('protected_rows', [])), membership_guards=len(plan.get('membership_guards', [])))


def check_plan(plan, root, db):
    plan = validate_plan(plan, root); schema_guard(plan, db)
    db.begin(readonly=True)
    try:
        guard_state(db, state_entries(plan), plan.get('membership_guards', []))
        validate_files(plan, root)
        return dict(status='before_state_matches', target_fingerprint=db.target_fingerprint, counts=summary(plan), read_only=True)
    finally:
        db.rollback()


def apply_plan(plan, root, db):
    plan = validate_plan(plan, root); schema_guard(plan, db)
    require(db.writable, 'Apply requires a writable owned adapter')
    db.acquire_lock()
    try:
        db.begin(readonly=False); db.assert_lock()
        guard_state(db, state_entries(plan), plan.get('membership_guards', []), lock=True)
        # Insert dependent objects in FK order before updating references to them.
        for table in ORDER:
            if plan.get('inserts', {}).get(table):
                db.insert_many(table, plan['inserts'][table])
        # Capture server defaults once, then require every inserted field to remain
        # unchanged through updates and the final guard, including created_at.
        inserted = [entry for entry in state_entries(plan, after=True) if not entry['exact']]
        inserted_actual = guard_state(db, inserted, [], lock=True) if inserted else []
        for table in ORDER:
            for update in plan.get('updates', []):
                if update['table'] == table:
                    db.update(table, identity(table, update['full_before']), update['after'])
        entries = [entry for entry in state_entries(plan, after=True) if entry['exact']]
        entries += [dict(table=row['table'], identity=row['identity'], expected=row['full_after'], exact=True) for row in inserted_actual]
        actual = guard_state(db, entries, plan.get('invariants_after', []), lock=True)
        validate_files(plan, root); db.assert_lock(); db.commit()
        return dict(status='committed_pending_anonymous', target_fingerprint=db.target_fingerprint, counts=summary(plan), after_rows=actual, new_people=copy.deepcopy(plan.get('new_people', [])))
    except BaseException:
        db.rollback()
        raise
    finally:
        db.release_lock()


def verify_db(plan, root, db, receipt=None):
    plan = validate_plan(plan, root); schema_guard(plan, db)
    entries = state_entries(plan, after=True)
    if receipt is not None:
        require(receipt['target_fingerprint'] == plan['target_fingerprint'], 'Receipt target differs')
        captured = {(row['table'], token(row['table'], row['identity'])): row['full_after'] for row in receipt['after_rows']}
        for entry in entries:
            if not entry['exact']:
                key = (entry['table'], token(entry['table'], entry['identity']))
                require(key in captured, 'Receipt lacks inserted full row')
                require(all(equal(captured[key].get(k), value) for k, value in entry['expected'].items()), 'Receipt differs from planned INSERT')
                entry.update(expected=captured[key], exact=True)
    db.begin(readonly=True)
    try:
        guard_state(db, entries, plan.get('invariants_after', []))
        validate_files(plan, root)
        return dict(status='after_state_matches', target_fingerprint=db.target_fingerprint, counts=summary(plan), read_only=True, inserted_full_rows_bound=receipt is not None)
    finally:
        db.rollback()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--mysql-env', required=True, type=Path)
    parser.add_argument('--receipt', type=Path)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--apply', action='store_true')
    actions.add_argument('--verify-db', action='store_true')
    parser.add_argument('--expected-plan-sha256')
    args = parser.parse_args(argv); root = args.root.resolve()
    planpath = args.plan.resolve(); require(root in planpath.parents and not args.plan.is_symlink(), 'Plan must be a regular file inside content root')
    raw = planpath.read_bytes(); plan_sha = digest(raw); plan = json.loads(raw)
    validate_plan(plan, root)  # All local evidence checks precede any connection.
    receiptpath = (args.receipt or planpath.with_name('publication-mysql.json')).resolve()
    require(receiptpath != planpath and root in receiptpath.parents, 'Receipt path must be distinct and inside content root')
    # Bind the reviewed bytes during the transaction as well as before it.
    # This is an execution guard, not a self-referential field in the saved plan.
    plan['protected_paths'][str(planpath.relative_to(root))] = plan_sha
    if args.apply:
        require(args.expected_plan_sha256 == plan_sha, '--apply requires exact --expected-plan-sha256')
        require(not receiptpath.exists(), 'Receipt exists; use --verify-db, never auto-resume')
    prior = json.loads(receiptpath.read_bytes()) if args.verify_db and receiptpath.exists() else None
    if prior is not None:
        require(prior['plan_sha256'] == plan_sha, 'Receipt plan SHA differs')
    db = Database(args.mysql_env, writable=args.apply)
    try:
        result = apply_plan(plan, root, db) if args.apply else verify_db(plan, root, db, prior) if args.verify_db else check_plan(plan, root, db)
        require(planpath.read_bytes() == raw, 'Plan file changed during execution')
        result.update(plan_sha256=plan_sha)
        if args.apply:
            # Exclusive creation: a competing receipt is never overwritten.
            receiptpath.parent.mkdir(parents=True, exist_ok=True)
            with receiptpath.open('x', encoding='utf-8') as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # MySQL exceptions may contain private connection details; never echo them.
        safe = str(error) if isinstance(error, (ValueError, KeyError)) else 'Database/IO operation failed; no anonymous acceptance claimed'
        print(json.dumps(dict(error_type=type(error).__name__, error=safe), ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
