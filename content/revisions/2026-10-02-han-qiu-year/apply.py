"""Correct the published Han Qiu description without rewriting its batch archive."""
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
batch = ROOT / plan['batch']
ids = json.loads((batch / 'sql/key-map.json').read_text())
uid = ids[plan['person_key']]
env = dict(line.split('=', 1) for line in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in line and not line.startswith('#'))
headers = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'],
           'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'],
           'Content-Type': 'application/json', 'Prefer': 'return=representation'}
url = env['SUPABASE_URL'] + '/rest/v1/person?id=eq.' + uid

def request(method='GET', data=None):
    call = urllib.request.Request(url, headers=headers, method=method,
                                  data=None if data is None else json.dumps(data).encode())
    with urllib.request.urlopen(call, timeout=40) as response:
        return json.load(response)

rows = request()
assert len(rows) == 1 and rows[0]['name'] == '韩球' and rows[0]['status'] == 'published'
assert rows[0]['description'] in (plan['old_description'], plan['new_description'])
if args.apply:
    rows = request('PATCH', {'description': plan['new_description']})
    assert len(rows) == 1 and rows[0]['description'] == plan['new_description']
    headers['apikey'] = env['SUPABASE_ANON_KEY']
    headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    rows = request()
    assert len(rows) == 1 and rows[0]['description'] == plan['new_description']
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True, 'anonymous_readback_verified': True,
        'person_id': uid, 'at': datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight', 'person_key': plan['person_key']})
