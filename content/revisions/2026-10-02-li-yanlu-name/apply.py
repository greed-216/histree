"""Guarded display-name correction; default is read-only."""
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
paths = [ROOT / x for x in plan['primary_batches']]
original_batches = [json.loads((x / 'content-batch.json').read_text()) for x in paths]
maps = [json.loads((x / 'sql/key-map.json').read_text()) for x in paths]
key = plan['person_key']
assert maps[0][key] == maps[1][key]
uid = maps[0][key]

claims = {}
for batch, mapping in zip(original_batches, maps):
    for row in batch['claims']:
        if '彦鲁（杨崇本子）' in row['claim_text'] or row['key'] == 'claim_zztj_269_0915_02_0044':
            claims[mapping[row['key']]] = row
assert len(claims) == 6, list(x['key'] for x in claims.values())
rel_key = 'relationship_person_杨崇本_person_彦鲁（杨崇本子）_父亲'
rel_id = maps[0][rel_key]

env = dict(line.split('=', 1) for line in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in line and not line.startswith('#'))
headers = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'],
           'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'],
           'Content-Type': 'application/json', 'Prefer': 'return=representation'}

def request(table, expression, method='GET', body=None):
    url = env['SUPABASE_URL'] + '/rest/v1/' + table + '?' + expression
    req = urllib.request.Request(url, headers=headers, method=method,
                                 data=None if body is None else json.dumps(body, ensure_ascii=False).encode())
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.load(response)

def one(table, row_id):
    rows = request(table, 'id=eq.' + row_id)
    assert len(rows) == 1, (table, row_id)
    return rows[0]

person = one('person', uid)
assert person['status'] == 'published'
assert person['name'] in ('彦鲁（杨崇本子）', plan['canonical_name'])
assert not request('person', 'name=eq.' + urllib.parse.quote(plan['canonical_name']) + '&id=neq.' + uid)
relation = one('person_relationship', rel_id)
assert relation['status'] == 'published' and relation['person_b'] == uid
assert relation['description'] in ('杨崇本是彦鲁（杨崇本子）的父亲。', '杨崇本是李彦鲁的父亲。')
assert all(one('person_event', mapping[k])['person_id'] == uid
           for mapping, k in [(maps[0], 'participation_zztj_269_0914_yang_chongben_poisoned_by_son_person_彦鲁（杨崇本子）'),
                              (maps[1], 'participation_zztj_269_0915_li_baoheng_kills_yanlu_person_彦鲁（杨崇本子）')])
old_person = next(x for x in original_batches[0]['people'] if x['key'] == key)
replacement_person = {
    'name': plan['canonical_name'],
    'aliases': sorted(set(person.get('aliases') or []) | set(plan['aliases'])),
    'description': '《资治通鉴》卷269乾化四年末仅称彦鲁；贞明元年同卷明称李彦鲁，为杨崇本之子。',
}
assert person['description'] in (old_person['description'], replacement_person['description'])
replacement_claims = {}
for row_id, old in claims.items():
    live = one('fact_claim', row_id)
    assert live['status'] == 'published' and live['subject_table'] == old['subject_table']
    patch = {'claim_text': old['claim_text'].replace('彦鲁（杨崇本子）', '李彦鲁')}
    if old['key'] == 'claim_zztj_269_0914_03_0111':
        patch['note'] = '原文：李继徽为其子彦鲁所毒而死，；核对说明：914年原文未写姓，915年同卷第6段明称李彦鲁；原文摘录保持不变。'
    if old['key'] == 'claim_zztj_269_0915_02_0044':
        patch['note'] = old['note'].replace('规范显示名后续改为李彦鲁', '规范显示名已校正为李彦鲁')
    for field, value in patch.items():
        assert live[field] in (old[field], value), (old['key'], field)
    replacement_claims[row_id] = patch

if args.apply:
    for table, row_id, patch in [
        ('person', uid, replacement_person),
        ('person_relationship', rel_id, {'description': '杨崇本是李彦鲁的父亲。'}),
    ] + [('fact_claim', row_id, patch) for row_id, patch in replacement_claims.items()]:
        live = one(table, row_id)
        if all(live[k] == v for k, v in patch.items()):
            continue
        changed = request(table, 'id=eq.' + row_id, 'PATCH', patch)
        assert len(changed) == 1 and all(changed[0][k] == v for k, v in patch.items()), (table, row_id)
    headers['apikey'] = env['SUPABASE_ANON_KEY']
    headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    public = one('person', uid)
    assert public['status'] == 'published' and all(public[k] == v for k, v in replacement_person.items())
    assert one('person_relationship', rel_id)['description'] == '杨崇本是李彦鲁的父亲。'
    assert all(all(one('fact_claim', row_id)[k] == v for k, v in patch.items())
               for row_id, patch in replacement_claims.items())
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True, 'at': datetime.now(timezone.utc).isoformat(),
        'person_id': uid, 'canonical_name': plan['canonical_name'],
        'updated_claim_ids': sorted(replacement_claims),
        'anonymous_readback_verified': True,
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight', 'person_key': key,
       'claim_updates': len(replacement_claims), 'relationship_updates': 1})
