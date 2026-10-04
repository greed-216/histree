# coding: utf-8
"""Read every scoped row anonymously and audit all initially nonempty display fields."""
import gzip, hashlib, importlib.util, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/review-public-history-copy.py').exists())
def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert read(P / 'round-35/readback-audit.json')['verified']
snapshot_path = Path('/private/tmp/histree-public-prose-20261004.json')
snapshot = read(snapshot_path)
assert sha(snapshot_path) == read(P / 'progress.json')['inventory_sha256']
rows = {table: {r['id']: dict(r) for r in records} for table, records in snapshot['tables'].items()}
for path in sorted(P.glob('round-*/changes.json')):
    proof = path.with_name('readback-audit.json')
    if not proof.exists(): continue
    assert read(proof)['verified'] and read(proof)['plan_sha256'] == sha(path)
    for change in read(path)['changes']:
        rows[change['table']][change['id']].update(change['after'])
part = ROOT / 'content/books/zizhi-tongjian/vol-280/year-0936/part-03'
batch = read(part / 'content-batch.json')
ids = read(part / 'sql/key-map.json')
mapping = {'people': 'person', 'events': 'event', 'person_events': 'person_event',
           'person_relationships': 'person_relationship', 'claims': 'fact_claim', 'sources': 'source'}
scoped = {(table, ids[r['key']]) for key, table in mapping.items() for r in batch[key]}
with gzip.open(P / 'review-ledger.jsonl.gz', 'rt', encoding='utf-8') as f:
    fields = [r for r in map(json.loads, f) if (r['table'], r['id']) in scoped]
assert len(fields) == 879
assert all(r['status'] == 'reviewed_verified' for r in fields)
evidence = []
for round_name in sorted({r['round'] for r in fields}):
    proof_path = P / round_name / 'readback-audit.json'
    proof = read(proof_path)
    assert proof['verified']
    plan_path = P / round_name / ('review-plan.jsonl.gz' if round_name == 'round-09' else 'changes.json')
    assert proof['plan_sha256'] == sha(plan_path)
    evidence.append(dict(round=round_name, readback_audit_sha256=sha(proof_path)))
spec = importlib.util.spec_from_file_location('copy_review', ROOT / 'scripts/review-public-history-copy.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
client = m.Client()
public_counts = {}
for table in sorted({table for table, _ in scoped}):
    selected = sorted(rid for t, rid in scoped if t == table)
    for offset in range(0, len(selected), 80):
        chunk = selected[offset:offset + 80]
        selection = 'id,subject_table,subject_id,field_path,claim_text,source_id,citation,note,status,source:source_id(id,url)' if table == 'fact_claim' else '*'
        actual = client.request(table, {'id': 'in.(' + ','.join(chunk) + ')', 'select': selection})
        assert {r['id'] for r in actual} == set(chunk)
        for r in actual:
            expected = rows[table][r['id']]
            assert all(r[k] == v for k, v in expected.items() if k != 'updated_at'), (table, r['id'])
            if table == 'fact_claim':
                original = next(x for x in snapshot['tables']['fact_claim'] if x['id'] == r['id'])
                assert m.quote(r['note']) == m.quote(original['note'])
                assert r['source'] and r['source']['id'] == r['source_id']
                assert r['source']['url'] == rows['source'][r['source_id']]['url']
    public_counts[table] = len(selected)
    print(table, len(selected), flush=True)
assert read(P / 'part03-full-quotation-check.json')['count'] == 259
proof = dict(batch=str(part.relative_to(ROOT)), primary_paragraphs=read(part / 'coverage.json')['paragraphs'],
             verified_at=datetime.now(timezone.utc).isoformat(), reviewed_scoped_fields=len(fields),
             total_scoped_fields=len(fields), pending_fields=[], all_scoped_fields_reviewed=True,
             full_site_complete=False, by_table=dict(Counter(r['table'] for r in fields)),
             public_row_counts=public_counts, all_scoped_rows_read_back=True,
             all_expected_and_protected_fields_verified=True, verbatim_quotes_unchanged=259,
             source_urls_verified=True, pinned_quotation_audit_sha256=sha(P / 'part03-full-quotation-check.json'),
             evidence=evidence, batch_sha256=sha(part / 'content-batch.json'),
             source_files=[dict(path=str(f.relative_to(ROOT)), sha256=sha(f)) for f in sorted((part / 'sources').rglob('source.txt'))])
(P / '936-part03-scope-audit.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
print('879 scoped display fields reviewed and all scoped rows anonymously verified; full-site goal remains active.', flush=True)
