"""Correct published person summaries while preserving immutable source batches."""
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
env = dict(line.split('=', 1) for line in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in line and not line.startswith('#'))
base = env['SUPABASE_URL'] + '/rest/v1/person?id=eq.'

def request(url, method='GET', data=None, anonymous=False):
    token = env['SUPABASE_ANON_KEY'] if anonymous else env['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': token, 'Authorization': 'Bearer ' + token,
               'Content-Type': 'application/json', 'Prefer': 'return=representation'}
    req = urllib.request.Request(url, headers=headers, method=method,
                                 data=None if data is None else json.dumps(data).encode())
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.load(response)

checked = []
for item in plan['entries']:
    ids = json.loads((ROOT / item['batch'] / 'sql/key-map.json').read_text())
    uid = ids[item['person_key']]
    rows = request(base + uid)
    assert len(rows) == 1 and rows[0]['id'] == uid and rows[0]['name'] == item['name']
    assert rows[0]['status'] == 'published'
    assert rows[0]['description'] in (item['old_description'], item['new_description']), item['person_key']
    checked.append((item, uid))

if args.apply:
    for item, uid in checked:
        url = base + uid
        if request(url)[0]['description'] != item['new_description']:
            rows = request(url, 'PATCH', {'description': item['new_description']})
            assert len(rows) == 1 and rows[0]['description'] == item['new_description'], item['person_key']
        rows = request(url, anonymous=True)
        assert len(rows) == 1 and rows[0]['description'] == item['new_description'], item['person_key']
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True, 'anonymous_readback_verified': True,
        'count': len(checked), 'person_keys': [item['person_key'] for item, _ in checked],
        'at': datetime.now(timezone.utc).isoformat(),
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight', 'persons': len(checked)})
