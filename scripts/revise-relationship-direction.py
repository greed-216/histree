"""Apply reviewed relation corrections with old-value guards; default is read-only."""
import argparse, hashlib, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); args = ap.parse_args()
folder = ROOT / 'content/revisions/2026-09-30-relationship-direction'
revision = json.loads((folder / 'relations.json').read_text())
env = dict(l.strip().split('=', 1) for l in (ROOT / 'apps/api/.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
headers = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'], 'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'], 'Content-Type': 'application/json', 'Prefer': 'return=representation'}
def request(query, method='GET', body=None):
    req = urllib.request.Request(env['SUPABASE_URL'] + '/rest/v1/person_relationship?' + query, headers=headers, method=method, data=None if body is None else json.dumps(body).encode())
    with urllib.request.urlopen(req, timeout=40) as response: return json.load(response)
for row in revision['relations']:
    actual = request('id=eq.' + row['id']); assert len(actual) == 1
    current = {k: actual[0][k] for k in row['before']}
    assert current in [row['before'], row['after']], 'Changed since review: ' + row['key']
print('Preflight verified:', len(revision['relations']))
if args.apply:
    for row in revision['relations']:
        query = 'id=eq.' + row['id'] + ''.join('&' + k + '=eq.' + urllib.parse.quote(v) for k, v in row['before'].items())
        request(query, 'PATCH', row['after'])
    headers['apikey'] = env['SUPABASE_ANON_KEY']; headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    for row in revision['relations']:
        actual = request('id=eq.' + row['id']); assert len(actual) == 1 and actual[0]['status'] == 'published'
        assert all(actual[0][k] == v for k, v in row['after'].items()), row['key']
    (folder / 'publication.json').write_text(json.dumps({'verified': True, 'revision_sha256': hashlib.sha256((folder / 'relations.json').read_bytes()).hexdigest(), 'count': len(revision['relations']), 'verified_at': datetime.now(timezone.utc).isoformat(), 'method': 'Guarded PATCH; anonymous readback; original IDs and claims retained'}, indent=2) + '\n')
    print('Anonymous readback verified')
