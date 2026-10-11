"""Apply reviewed relation corrections with old-value guards; default is read-only."""
import argparse, hashlib, json, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); args = ap.parse_args()
folder = ROOT / 'content/revisions/2026-09-30-relationship-direction'
revision = json.loads((folder / 'relations.json').read_text())
from mysql_content_store import MysqlContentStore
store=MysqlContentStore(args.mysql_env,args.apply,args.public_api_url)
def request(query,method='GET',body=None):return store.request('person_relationship',query,method,body)
for row in revision['relations']:
    actual = request('id=eq.' + row['id']); assert len(actual) == 1
    current = {k: actual[0][k] for k in row['before']}
    assert current in [row['before'], row['after']], 'Changed since review: ' + row['key']
print('Preflight verified:', len(revision['relations']))
if args.apply:
    for row in revision['relations']:
        query = 'id=eq.' + row['id'] + ''.join('&' + k + '=eq.' + urllib.parse.quote(v) for k, v in row['before'].items())
        request(query, 'PATCH', row['after'])
    store.public=True
    for row in revision['relations']:
        actual = request('id=eq.' + row['id']); assert len(actual) == 1 and actual[0]['status'] == 'published'
        assert all(actual[0][k] == v for k, v in row['after'].items()), row['key']
    (folder / 'publication-mysql.json').write_text(json.dumps({'verified': True, 'revision_sha256': hashlib.sha256((folder / 'relations.json').read_bytes()).hexdigest(), 'count': len(revision['relations']), 'verified_at': datetime.now(timezone.utc).isoformat(), 'method': 'Guarded PATCH; anonymous readback; original IDs and claims retained'}, indent=2) + '\n')
    print('Anonymous readback verified')
