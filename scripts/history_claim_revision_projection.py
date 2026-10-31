"""Pure projection of accepted reviewed_history_correction claims into book indexes.

Reads bound correction plans/receipts, never writes files or accesses a database.
Frozen batch records and arbitrary caller metadata survive in a deep copy.
"""
import copy
import hashlib
import json
import re
import uuid
from pathlib import Path

NS = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/greed-216/histree/content')
KIND = 'reviewed_history_correction'
PROJECTION_FIELDS = ('source_key', 'subject_key', 'citation', 'subject_table')


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _state(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _book(source_key, books):
    _require(all(isinstance(prefixes, (tuple, list)) and prefixes
                 and all(isinstance(p, str) and p for p in prefixes)
                 for _, prefixes in books.values()), 'Invalid book source prefixes')
    matches = [key for key, (_, prefixes) in books.items()
               if isinstance(source_key, str) and source_key.startswith(tuple(prefixes))]
    _require(len(matches) == 1, 'Correction source book is unknown or ambiguous')
    return matches[0]


def _projection(row, keys):
    for field in ('id', 'source_id', 'subject_id'):
        _require(isinstance(row.get(field), str) and row[field] in keys,
                 'Correction references unknown UUID: ' + field)
    _require(isinstance(row.get('citation'), str), 'Correction citation is not text')
    _require(isinstance(row.get('subject_table'), str) and row['subject_table'],
             'Correction subject_table is missing')
    return dict(source_key=keys[row['source_id']], subject_key=keys[row['subject_id']],
                citation=row['citation'], subject_table=row['subject_table'])


def _accepted(root):
    plans = []
    for path in sorted((root / 'content/revisions').rglob('plan.json')):
        _require(path.resolve().is_relative_to(root), 'Correction path escapes root')
        raw = path.read_bytes()
        plan = json.loads(raw)
        _require(isinstance(plan, dict), 'Correction plan is not an object')
        if plan.get('kind') != KIND:
            continue
        receipt_path = path.parent / 'publication-mysql.json'
        if not receipt_path.exists():
            continue
        _require(receipt_path.resolve().is_relative_to(root), 'Correction path escapes root')
        receipt = json.loads(receipt_path.read_bytes())
        _require(isinstance(receipt, dict), 'Correction receipt is not an object')
        # An unexecuted draft has no authority over the derived index.
        if receipt.get('verified') is not True:
            continue
        _require(path.resolve().is_relative_to(root) and receipt_path.resolve().is_relative_to(root),
                 'Correction path escapes root')
        digest = hashlib.sha256(raw).hexdigest()
        _require(receipt.get('plan_sha256') == digest, 'Correction plan hash changed')
        _require(receipt.get('anonymous_readback_verified') is True,
                 'Correction anonymous acceptance is missing or false')
        target = plan.get('target_fingerprint')
        _require(isinstance(target, str) and re.fullmatch('[0-9a-f]{64}', target) is not None
                 and receipt.get('target_fingerprint') == target, 'Correction target differs')
        new = plan.get('new_claims', [])
        updates = plan.get('updates', [])
        _require(isinstance(new, list) and isinstance(updates, list), 'Invalid correction rows')
        audit = receipt.get('audit')
        _require(isinstance(audit, dict) and isinstance(audit.get('inserts'), dict),
                 'Correction claim insert audit is missing')
        count = audit['inserts'].get('fact_claim')
        _require(type(count) is int and count == len(new), 'Correction claim insert audit differs')
        keys = plan.get('key_map')
        _require(isinstance(keys, dict), 'Correction key_map is missing')
        for ident, key in keys.items():
            _require(isinstance(ident, str) and isinstance(key, str) and bool(key)
                     and str(uuid.uuid5(NS, key)) == ident, 'Correction stable UUID/key differs')
        _require(len(set(keys.values())) == len(keys), 'Correction stable key has multiple UUIDs')
        plans.append(dict(plan=plan, keys=keys, path=str(path.relative_to(root)), digest=digest))
    return plans


def _has_provenance(record, refs):
    files = record.get('revision_files', [])
    hashes = record.get('revision_plan_sha256s', {})
    _require(isinstance(files, list) and isinstance(hashes, dict), 'Invalid revision provenance')
    for path, digest in refs:
        if files and files[0] == path and 'revision_plan_sha256' in record:
            _require(record['revision_plan_sha256'] == digest, 'Index singular revision hash differs')
        if path not in files or hashes.get(path) != digest:
            return False
    return True


def _annotate(record, refs):
    files = record.setdefault('revision_files', [])
    hashes = record.setdefault('revision_plan_sha256s', {})
    _require(isinstance(files, list) and isinstance(hashes, dict), 'Invalid revision provenance')
    for path, digest in refs:
        if files and files[0] == path and 'revision_plan_sha256' in record:
            _require(record['revision_plan_sha256'] == digest, 'Index singular revision hash differs')
        _require(path not in hashes or hashes[path] == digest, 'Index revision hash differs')
        if path not in files:
            files.append(path)
        hashes[path] = digest
    # Preserve the older singular hash (and every other extra) if already present.
    if refs:
        record.setdefault('revision_plan_sha256', refs[0][1])


def project_claim_revisions(root, indexes, books):
    """Return deep-copied indexes with only verified new-kind claim changes projected.

    ``key_map`` maps UUID to stable key. Update ``before`` and ``after`` must
    contain the same changed fields, guarded by a complete ``full_before`` row.
    Receipt insertion evidence is ``audit.inserts.fact_claim`` (an integer).
    All chains are connected by complete row values, never directory chronology.
    """
    root = Path(root).resolve()
    result = copy.deepcopy(indexes)
    accepted = _accepted(root)
    if not accepted:
        return result
    located = {}
    for book, records in result.items():
        _require(isinstance(records, dict), 'Book claim index is not a dictionary')
        for key, record in records.items():
            _require(key not in located, 'Claim appears in multiple book indexes')
            located[key] = (book, record)
    changes = {}
    creations = {}
    for meta in accepted:
        plan, keys = meta['plan'], meta['keys']
        ref = (meta['path'], meta['digest'])
        for row in plan.get('new_claims', []):
            _require(isinstance(row, dict), 'New correction claim is not a row')
            proj = _projection(row, keys)
            key = keys[row['id']]
            _require(all(isinstance(row.get(f), str) and bool(row[f])
                         for f in ('field_path', 'claim_text', 'note')), 'New claim row is incomplete')
            _require('key' not in row or row['key'] == key, 'New claim stable key differs')
            _require(row.get('status') == 'published', 'New correction claim is not published')
            _require(key not in creations, 'Duplicate correction new claim')
            _book(proj['source_key'], books)
            creations[key] = dict(row=copy.deepcopy(row), projection=proj, ref=ref)
        for update in plan.get('updates', []):
            _require(isinstance(update, dict), 'Correction update is not a row')
            if update.get('table') != 'fact_claim':
                continue
            before, after, full = [update.get(k) for k in ('before', 'after', 'full_before')]
            _require(isinstance(before, dict) and isinstance(after, dict) and isinstance(full, dict)
                     and before and before.keys() == after.keys(), 'Correction changed fields differ')
            ident, key = update.get('id'), update.get('key')
            _require(isinstance(ident, str) and ident in keys and key == keys[ident] and full.get('id') == ident,
                     'Correction update UUID/key differs')
            _require('id' not in after, 'Correction cannot change claim UUID')
            _require(all(k in full and full[k] == v for k, v in before.items()),
                     'Correction full_before does not match before fields')
            final = dict(full, **after)
            _require(full != final, 'Correction update is a self cycle')
            old_proj, new_proj = _projection(full, keys), _projection(final, keys)
            _book(old_proj['source_key'], books)
            _book(new_proj['source_key'], books)
            edge = dict(before=copy.deepcopy(full), after=final, old=old_proj, new=new_proj, ref=ref)
            changes.setdefault(key, []).append(edge)
    for key in sorted(set(changes) | set(creations)):
        edges = changes.get(key, [])
        outgoing, incoming = {}, {}
        for edge in edges:
            a, b = _state(edge['before']), _state(edge['after'])
            _require(a not in outgoing, 'Correction chain branches or repeats an edge')
            _require(b not in incoming, 'Correction chain converges or repeats an edge')
            outgoing[a], incoming[b] = edge, edge
        ordered = []
        if edges:
            starts = set(outgoing) - set(incoming)
            _require(len(starts) == 1, 'Correction chain has a cycle or disconnected roots')
            node = next(iter(starts))
            visited = set()
            while node in outgoing:
                _require(node not in visited, 'Correction chain cycles')
                visited.add(node)
                edge = outgoing[node]
                ordered.append(edge)
                node = _state(edge['after'])
            _require(len(ordered) == len(edges), 'Correction chain is disconnected or cyclic')
        creation = creations.get(key)
        if creation and ordered:
            _require(_state(creation['row']) == _state(ordered[0]['before']),
                     'New claim does not connect to its correction chain')
        refs = ([creation['ref']] if creation else []) + [e['ref'] for e in ordered]
        states = ([creation['projection']] if creation else [ordered[0]['old']]) + [e['new'] for e in ordered]
        old_book, record = located.get(key, (None, None))
        if record is None:
            _require(creation is not None, 'Correction cites an unknown indexed claim: ' + key)
            record = dict(claim_key=key, batch_files=[])
        else:
            _require(record.get('claim_key') == key, 'Index claim key differs')
            current = {f: record.get(f) for f in PROJECTION_FIELDS}
            matches = [i for i, state in enumerate(states) if state == current]
            _require(matches, 'Index does not match correction before/after values')
            _require(old_book == _book(current['source_key'], books), 'Index book does not match source')
            # A frozen input must match the initial state. Already projected rows
            # are accepted only with the corresponding hash-bound provenance.
            if creation:
                _require(_has_provenance(record, [creation['ref']]), 'New correction claim collides with old index')
            _require(any(_has_provenance(record, ([creation['ref']] if creation else [])
                                         + [e['ref'] for e in ordered[:i]]) for i in matches),
                     'Index final values lack accepted revision provenance')
        record.update(states[-1])
        _annotate(record, refs)
        dest = _book(record['source_key'], books)
        if old_book is not None:
            del result[old_book][key]
        _require(key not in result.setdefault(dest, {}), 'Migrated claim collides in destination')
        result[dest][key] = record
    return result


def retain_verified_existing_claims(root, indexes, books, selected_books):
    """Retain only missing, independently proven append-only revision claims.

    This is not a legacy revision interpreter. Each candidate already present in
    a selected source-index must exactly match a published ``new_claims`` row in
    every cited, hash-bound and anonymously accepted plan. No update/remap is
    inferred. Existing rows in any rebuilt book index always take precedence.
    """
    root = Path(root).resolve()
    result = copy.deepcopy(indexes)
    present = {key for records in result.values() for key in records}
    selected = [selected_books] if isinstance(selected_books, str) else list(selected_books)
    _require(all(book in books for book in selected), 'Unknown selected book')
    cache = {}

    def accepted_file(ref):
        _require(isinstance(ref, str) and ref, 'Existing claim revision path is missing')
        relative = Path(ref)
        path = root / relative
        _require(not relative.is_absolute() and '..' not in relative.parts
                 and path.resolve().is_relative_to(root / 'content/revisions')
                 and path.name == 'plan.json', 'Existing claim revision path escapes revision root')
        if ref in cache:
            return cache[ref]
        _require(path.is_file(), 'Existing claim revision plan is missing')
        receipt_path = path.with_name('publication-mysql.json')
        _require(receipt_path.resolve().is_relative_to(root) and receipt_path.is_file(),
                 'Existing claim receipt is missing or escapes root')
        raw = path.read_bytes()
        plan, receipt = json.loads(raw), json.loads(receipt_path.read_bytes())
        _require(isinstance(plan, dict) and isinstance(receipt, dict), 'Invalid existing claim proof')
        digest = hashlib.sha256(raw).hexdigest()
        _require(receipt.get('verified') is True and receipt.get('anonymous_readback_verified') is True,
                 'Existing claim revision lacks verified anonymous acceptance')
        _require(receipt.get('plan_sha256') == digest, 'Existing claim plan hash changed')
        target = plan.get('target_fingerprint')
        _require(isinstance(target, str) and re.fullmatch('[0-9a-f]{64}', target) is not None
                 and receipt.get('target_fingerprint') == target, 'Existing claim target differs')
        _require(isinstance(plan.get('new_claims'), list) and isinstance(plan.get('updates', []), list),
                 'Existing claim plan has no append-only rows')
        cache[ref] = (plan, digest)
        return cache[ref]

    for book in sorted(set(selected)):
        path = root / 'content/books' / book / 'source-index.json'
        _require(path.resolve().is_relative_to(root / 'content/books'), 'Existing book index escapes root')
        if not path.exists():
            continue
        data = json.loads(path.read_bytes())
        _require(isinstance(data, dict) and data.get('book') == books[book][0]
                 and isinstance(data.get('claims'), list), 'Existing source index has unknown book/shape')
        seen = set()
        for record in data['claims']:
            _require(isinstance(record, dict), 'Existing source index claim is not a record')
            key = record.get('claim_key')
            _require(isinstance(key, str) and key and key not in seen, 'Existing source index duplicates/omits claim key')
            seen.add(key)
            if key in present:
                continue
            _require(all(isinstance(record.get(f), str) and record[f]
                         for f in PROJECTION_FIELDS), 'Existing claim projection fields are missing')
            _require(_book(record['source_key'], books) == book, 'Existing claim source belongs to another book')
            files = record.get('revision_files')
            hashes = record.get('revision_plan_sha256s', {})
            singular = record.get('revision_plan_sha256')
            _require(isinstance(files, list) and files and all(isinstance(f, str) for f in files)
                     and len(set(files)) == len(files)
                     and isinstance(hashes, dict), 'Existing claim has no unambiguous revision provenance')
            _require('batch_files' not in record or isinstance(record['batch_files'], list),
                     'Existing claim batch_files is not a list')
            expected = dict(id=str(uuid.uuid5(NS, key)),
                            source_id=str(uuid.uuid5(NS, record['source_key'])),
                            subject_id=str(uuid.uuid5(NS, record['subject_key'])),
                            subject_table=record['subject_table'], citation=record['citation'], status='published')
            if 'id' in record:
                _require(record['id'] == expected['id'], 'Existing claim stable UUID differs')
            refs = []
            for i, ref in enumerate(files):
                plan, digest = accepted_file(ref)
                mapped = hashes.get(ref)
                _require(mapped == digest or (len(files) == 1 and singular == digest),
                         'Existing index revision hash is missing or differs')
                if ref in hashes:
                    _require(mapped == digest, 'Existing index revision hash differs')
                if i == 0 and singular is not None:
                    _require(singular == digest, 'Existing singular revision hash differs')
                matches = [r for r in plan['new_claims'] if isinstance(r, dict) and r.get('id') == expected['id']]
                _require(len(matches) == 1 and all(matches[0].get(f) == value for f, value in expected.items()),
                         'Existing index does not match a published append-only claim row')
                _require(all(isinstance(matches[0].get(f), str) and matches[0][f]
                             for f in ('field_path', 'claim_text', 'note')), 'Existing appended claim row is incomplete')
                _require(not any(isinstance(u, dict) and u.get('table') == 'fact_claim'
                                 and u.get('id') == expected['id'] for u in plan.get('updates', [])),
                         'Existing claim proof is an update, not append-only retention')
                refs.append((ref, digest))
            retained = copy.deepcopy(record)
            _annotate(retained, refs)
            result.setdefault(book, {})[key] = retained
            present.add(key)
    return result
