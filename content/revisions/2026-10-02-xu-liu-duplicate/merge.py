"""Merge the 904 retrospective Xu Yanruo/Liu Yin duplicate into its 901 event.

Default mode reads only. --apply retargets five claims and hides three duplicate
rows, preserving the original batch and source snapshots as publication audit.
"""
import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
plan = json.loads((HERE / 'plan.json').read_text())
old_batch = ROOT / 'content/books/zizhi-tongjian/vol-262/year-0901/part-07'
new_batch = ROOT / 'content/books/zizhi-tongjian/vol-265/year-0904/part-04'
old_ids = json.loads((old_batch / 'sql/key-map.json').read_text())
new_ids = json.loads((new_batch / 'sql/key-map.json').read_text())
ids = old_ids | new_ids
claims = {row['key']: row for row in json.loads((new_batch / 'content-batch.json').read_text())['claims']}
env = dict(line.split('=', 1) for line in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in line and not line.startswith('#'))
headers = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'],
           'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'],
           'Content-Type': 'application/json', 'Prefer': 'return=representation'}

def query(table, expression, method='GET', data=None):
    url = env['SUPABASE_URL'] + '/rest/v1/' + table + '?' + expression
    request = urllib.request.Request(url, headers=headers, method=method,
                                     data=None if data is None else json.dumps(data).encode())
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)

def one(table, key):
    rows = query(table, 'id=eq.' + ids[key])
    assert len(rows) == 1, (table, key, len(rows))
    return rows[0]

event_from = plan['event']['from']
event_to = plan['event']['to']
assert one('event', event_to)['status'] == 'published'
assert one('event', event_from)['status'] in ('published', 'draft')
assert query('event_causality', 'cause_event_id=eq.' + ids[event_from]) == []
assert query('event_causality', 'effect_event_id=eq.' + ids[event_from]) == []

edges = plan['edges']
for edge in edges:
    assert one('person_event', edge['to'])['status'] == 'published'
    assert one('person_event', edge['from'])['status'] in ('published', 'draft')
actual_edges = query('person_event', 'event_id=eq.' + ids[event_from])
assert {row['id'] for row in actual_edges} == {ids[edge['from']] for edge in edges}

for key, target in plan['claim_subject_remap'].items():
    source = claims[key]['subject_key']
    row = one('fact_claim', key)
    assert row['subject_table'] == claims[key]['subject_table']
    assert row['subject_id'] in (ids[source], ids[target]), (key, row['subject_id'])
    assert row['status'] == 'published'
old_event_claims = {row['id'] for row in query('fact_claim', 'subject_table=eq.event&subject_id=eq.' + ids[event_from])}
expected_old_claims = {ids[key] for key in plan['claim_subject_remap'] if claims[key]['subject_table'] == 'event'}
assert old_event_claims in (set(), expected_old_claims), old_event_claims

if args.apply:
    for key, target in plan['claim_subject_remap'].items():
        result = query('fact_claim', 'id=eq.' + ids[key], 'PATCH', {'subject_id': ids[target]})
        assert len(result) == 1 and result[0]['subject_id'] == ids[target]
    for edge in edges:
        result = query('person_event', 'id=eq.' + ids[edge['from']], 'PATCH', {'status': 'draft'})
        assert len(result) == 1 and result[0]['status'] == 'draft'
    result = query('event', 'id=eq.' + ids[event_from], 'PATCH', {'status': 'draft'})
    assert len(result) == 1 and result[0]['status'] == 'draft'

headers['apikey'] = env['SUPABASE_ANON_KEY']
headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
if args.apply:
    assert len(query('event', 'id=eq.' + ids[event_to])) == 1
    assert query('event', 'id=eq.' + ids[event_from]) == []
    for edge in edges:
        assert query('person_event', 'id=eq.' + ids[edge['from']]) == []
    for key, target in plan['claim_subject_remap'].items():
        result = query('fact_claim', 'id=eq.' + ids[key])
        assert len(result) == 1 and result[0]['subject_id'] == ids[target]
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True, 'at': datetime.now(timezone.utc).isoformat(),
        'canonical_event_id': ids[event_to], 'hidden_duplicate_event_id': ids[event_from],
        'retargeted_claims': len(plan['claim_subject_remap']),
        'hidden_duplicate_edges': len(edges), 'anonymous_readback_verified': True,
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight',
       'claim_subject_remap': len(plan['claim_subject_remap']),
       'duplicate_edges': len(edges), 'canonical_event': event_to})
