"""Correct Wang Jingren's duplicate identity in Tongjian 906 p035.

Default is read-only; --apply retargets the published edge and claim, then
hides the duplicate person. The original batch remains an audit archive.
"""
import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--apply', action='store_true')
args = ap.parse_args()
old_batch = ROOT / 'content/books/zizhi-tongjian/vol-265/year-0906/part-01'
new_batch = ROOT / 'content/books/zizhi-tongjian/vol-265/year-0906/part-05'
ids = json.loads((old_batch / 'sql/key-map.json').read_text()) | json.loads((new_batch / 'sql/key-map.json').read_text())
canonical = ids['person_王茂章']
duplicate = ids['person_王景仁']
edge = ids['participation_zztj_265_0906_qian_liu_recommends_wang_jingren_person_王景仁']
person_claim = ids['claim_zztj_265_0906_05_0022']
edge_claim = ids['claim_zztj_265_0906_05_0023']
env = dict(line.split('=', 1) for line in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in line and not line.startswith('#'))
headers = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'],
           'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'],
           'Content-Type': 'application/json', 'Prefer': 'return=representation'}

def req(table, expression, method='GET', body=None):
    request = urllib.request.Request(
        env['SUPABASE_URL'] + '/rest/v1/' + table + '?' + expression,
        headers=headers, method=method,
        data=None if body is None else json.dumps(body, ensure_ascii=False).encode())
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)

def one(table, row_id):
    rows = req(table, 'id=eq.' + row_id)
    assert len(rows) == 1, (table, row_id)
    return rows[0]

canonical_row = one('person', canonical)
duplicate_row = one('person', duplicate)
assert canonical_row['name'] == '王茂章' and canonical_row['status'] == 'published'
assert duplicate_row['name'] == '王景仁' and duplicate_row['status'] in ('published', 'draft')
assert '王景仁' not in (duplicate_row.get('aliases') or [])
alias_set = set(canonical_row.get('aliases') or [])
assert alias_set <= alias_set | {'王景仁'}
edge_row = one('person_event', edge)
assert edge_row['person_id'] in (duplicate, canonical) and edge_row['status'] == 'published'
person_claim_row = one('fact_claim', person_claim)
assert person_claim_row['subject_table'] == 'person'
assert person_claim_row['subject_id'] in (duplicate, canonical)
assert person_claim_row['status'] == 'published'
edge_claim_row = one('fact_claim', edge_claim)
assert edge_claim_row['subject_table'] == 'person_event' and edge_claim_row['subject_id'] == edge
assert edge_claim_row['status'] == 'published'
assert req('person_relationship', 'person_a=eq.' + duplicate) == []
assert req('person_relationship', 'person_b=eq.' + duplicate) == []
assert {row['id'] for row in req('person_event', 'person_id=eq.' + duplicate)} in ({edge}, set())
assert {row['id'] for row in req('fact_claim', 'subject_table=eq.person&subject_id=eq.' + duplicate)} in ({person_claim}, set())
assert req('person_event', 'person_id=eq.' + canonical + '&event_id=eq.' + edge_row['event_id']) == [] if edge_row['person_id'] == duplicate else True

if args.apply:
    if edge_row['person_id'] == duplicate:
        result = req('person_event', 'id=eq.' + edge, 'PATCH', {'person_id': canonical})
        assert len(result) == 1 and result[0]['person_id'] == canonical
    if person_claim_row['subject_id'] == duplicate:
        result = req('fact_claim', 'id=eq.' + person_claim, 'PATCH', {'subject_id': canonical})
        assert len(result) == 1 and result[0]['subject_id'] == canonical
    if '王景仁' not in alias_set:
        result = req('person', 'id=eq.' + canonical, 'PATCH', {'aliases': sorted(alias_set | {'王景仁'})})
        assert len(result) == 1 and '王景仁' in result[0]['aliases']
    if duplicate_row['status'] == 'published':
        result = req('person', 'id=eq.' + duplicate, 'PATCH', {'status': 'draft'})
        assert len(result) == 1 and result[0]['status'] == 'draft'
    headers['apikey'] = env['SUPABASE_ANON_KEY']
    headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    assert req('person', 'id=eq.' + duplicate) == []
    visible = one('person', canonical)
    assert '王景仁' in visible['aliases']
    assert one('person_event', edge)['person_id'] == canonical
    assert one('fact_claim', person_claim)['subject_id'] == canonical
    assert one('fact_claim', edge_claim)['subject_id'] == edge
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True,
        'at': datetime.now(timezone.utc).isoformat(),
        'canonical_person_id': canonical,
        'hidden_duplicate_person_id': duplicate,
        'retargeted_person_event_id': edge,
        'retargeted_claim_id': person_claim,
        'anonymous_readback_verified': True,
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight', 'canonical': '王茂章', 'alias': '王景仁'})
