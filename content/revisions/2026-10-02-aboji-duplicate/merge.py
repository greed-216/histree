"""Merge the published Yelü Abaoji duplicate into the Abaoji person.

Read-only by default. --apply retargets only the enumerated references, adds the
historical name as an alias, and hides the empty duplicate; old batches remain.
"""
import argparse
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / 'plan.json').read_text())
assert '契丹王邪律阿保机' in (ROOT / plan['evidence'][0]).read_text()
assert '阿保机姓邪律氏' in (ROOT / plan['evidence'][1]).read_text()
parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()

ids = {}
for path in (ROOT / 'content').rglob('sql/key-map.json'):
    mapping = json.loads(path.read_text())
    for key in (plan['canonical_key'], plan['duplicate_key']):
        if key in mapping:
            assert key not in ids or ids[key] == mapping[key], (path, key)
            ids[key] = mapping[key]
assert len(ids) == 2, ids
canonical, duplicate = ids[plan['canonical_key']], ids[plan['duplicate_key']]
assert canonical != duplicate

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
assert canonical_row['name'] == '阿保机' and canonical_row['status'] == 'published'
assert duplicate_row['name'] == '耶律阿保机' and duplicate_row['status'] in ('published', 'draft')
old_rel_a = req('person_relationship', 'person_a=eq.' + duplicate)
old_rel_b = req('person_relationship', 'person_b=eq.' + duplicate)
assert old_rel_a == []
assert {row['id'] for row in old_rel_b} == set(plan['retargeted_person_relationship_ids'])
assert all(row['status'] == 'published' for row in old_rel_b)
assert not any(row['person_a'] == old_rel_b[0]['person_a'] and
               row['relation_type'] == old_rel_b[0]['relation_type']
               for row in req('person_relationship', 'person_b=eq.' + canonical))

old_edges = req('person_event', 'person_id=eq.' + duplicate)
all_edges = {x['id']: x for x in old_edges}
for edge_id in plan['retargeted_person_event_ids']:
    all_edges[edge_id] = one('person_event', edge_id)
assert set(all_edges) == set(plan['retargeted_person_event_ids'])
assert all(x['person_id'] in (duplicate, canonical) and x['status'] == 'published'
           for x in all_edges.values())
canonical_events = {x['event_id'] for x in req('person_event', 'person_id=eq.' + canonical)}
assert all(x['event_id'] not in canonical_events for x in all_edges.values()
           if x['person_id'] == duplicate)

old_claims = req('fact_claim', 'subject_table=eq.person&subject_id=eq.' + duplicate)
all_claims = {x['id']: x for x in old_claims}
for claim_id in plan['retargeted_person_claim_ids']:
    all_claims[claim_id] = one('fact_claim', claim_id)
assert set(all_claims) == set(plan['retargeted_person_claim_ids'])
assert all(x['subject_table'] == 'person' and x['subject_id'] in (duplicate, canonical)
           and x['status'] == 'published' for x in all_claims.values())

for alias in plan['aliases_to_add']:
    encoded = urllib.parse.quote(alias, safe='')
    name_matches = req('person', 'select=id,name&status=eq.published&name=eq.' + encoded)
    alias_matches = req('person', 'select=id,name&status=eq.published&aliases=cs.' +
                        urllib.parse.quote('{"' + alias + '"}', safe=''))
    assert all(row['id'] in (canonical, duplicate) for row in name_matches + alias_matches), alias

if args.apply:
    for row in all_edges.values():
        if row['person_id'] == duplicate:
            changed = req('person_event', 'id=eq.' + row['id'], 'PATCH', {'person_id': canonical})
            assert len(changed) == 1 and changed[0]['person_id'] == canonical
    for row in old_rel_b:
        changed = req('person_relationship', 'id=eq.' + row['id'], 'PATCH', {'person_b': canonical})
        assert len(changed) == 1 and changed[0]['person_b'] == canonical
    for row in all_claims.values():
        if row['subject_id'] == duplicate:
            changed = req('fact_claim', 'id=eq.' + row['id'], 'PATCH', {'subject_id': canonical})
            assert len(changed) == 1 and changed[0]['subject_id'] == canonical
    aliases = set(canonical_row.get('aliases') or [])
    if not set(plan['aliases_to_add']).issubset(aliases):
        changed = req('person', 'id=eq.' + canonical, 'PATCH',
                      {'aliases': sorted(aliases | set(plan['aliases_to_add']))})
        assert len(changed) == 1 and set(plan['aliases_to_add']).issubset(changed[0]['aliases'])
    if duplicate_row['status'] == 'published':
        changed = req('person', 'id=eq.' + duplicate, 'PATCH', {'status': 'draft'})
        assert len(changed) == 1 and changed[0]['status'] == 'draft'
    assert req('person_event', 'person_id=eq.' + duplicate) == []
    assert req('person_relationship', 'person_a=eq.' + duplicate) == []
    assert req('person_relationship', 'person_b=eq.' + duplicate) == []
    assert req('fact_claim', 'subject_table=eq.person&subject_id=eq.' + duplicate) == []
    headers['apikey'] = env['SUPABASE_ANON_KEY']
    headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    assert req('person', 'id=eq.' + duplicate) == []
    public = one('person', canonical)
    assert set(plan['aliases_to_add']).issubset(public['aliases'])
    assert all(one('person_event', row_id)['person_id'] == canonical
               for row_id in plan['retargeted_person_event_ids'])
    assert all(one('person_relationship', row_id)['person_b'] == canonical
               for row_id in plan['retargeted_person_relationship_ids'])
    assert all(one('fact_claim', row_id)['subject_id'] == canonical
               for row_id in plan['retargeted_person_claim_ids'])
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True,
        'at': datetime.now(timezone.utc).isoformat(),
        'canonical_person_id': canonical,
        'hidden_duplicate_person_id': duplicate,
        'retargeted_person_event_ids': plan['retargeted_person_event_ids'],
        'retargeted_person_claim_ids': plan['retargeted_person_claim_ids'],
        'retargeted_person_relationship_ids': plan['retargeted_person_relationship_ids'],
        'anonymous_readback_verified': True,
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight',
       'canonical': '阿保机', 'aliases': plan['aliases_to_add'],
       'edges': len(all_edges), 'person_claims': len(all_claims)})
