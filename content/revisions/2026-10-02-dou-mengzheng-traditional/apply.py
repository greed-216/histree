"""Add the attested traditional form to the existing Dou Mengzheng person."""
import argparse
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / 'plan.json').read_text())
parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
source = (ROOT / plan['evidence_file']).read_text()
assert plan['evidence_excerpt'] in source
ids = json.loads((ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-03/sql/key-map.json').read_text())
assert ids[plan['person_key']] == plan['person_id']
env = dict(line.split('=', 1) for line in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in line and not line.startswith('#'))
headers = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'],
           'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'],
           'Content-Type': 'application/json', 'Prefer': 'return=representation'}

def req(table, expression, method='GET', body=None):
    request = urllib.request.Request(env['SUPABASE_URL'] + '/rest/v1/' + table + '?' + expression,
                                     headers=headers, method=method,
                                     data=None if body is None else json.dumps(body, ensure_ascii=False).encode())
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)

person = req('person', 'id=eq.' + plan['person_id'])
assert len(person) == 1 and person[0]['name'] == plan['name'] and person[0]['status'] == 'published'
assert person[0]['aliases'] in ([], [plan['alias']])
claim = req('fact_claim', 'id=eq.' + plan['evidence_claim_id'])
assert len(claim) == 1 and claim[0]['subject_table'] == 'person'
assert claim[0]['subject_id'] == plan['person_id'] and claim[0]['status'] == 'published'
assert plan['evidence_excerpt'] in claim[0]['note']
encoded = urllib.parse.quote(plan['alias'], safe='')
others = req('person', 'select=id&status=eq.published&name=eq.' + encoded)
others += req('person', 'select=id&status=eq.published&aliases=cs.' +
              urllib.parse.quote('{"' + plan['alias'] + '"}', safe=''))
assert all(row['id'] == plan['person_id'] for row in others)
if args.apply:
    if person[0]['aliases'] != [plan['alias']]:
        changed = req('person', 'id=eq.' + plan['person_id'], 'PATCH', {'aliases': [plan['alias']]})
        assert len(changed) == 1 and changed[0]['aliases'] == [plan['alias']]
    headers['apikey'] = env['SUPABASE_ANON_KEY']
    headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    public = req('person', 'id=eq.' + plan['person_id'])
    assert len(public) == 1 and public[0]['aliases'] == [plan['alias']]
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True, 'at': datetime.now(timezone.utc).isoformat(),
        'person_id': plan['person_id'], 'alias': plan['alias'],
        'evidence_claim_id': plan['evidence_claim_id'],
        'anonymous_readback_verified': True,
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight', 'alias': plan['alias']})
