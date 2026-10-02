"""Correct the published display name for Ma Cong; default is read-only."""
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
batch = ROOT / 'content/books/zizhi-tongjian/vol-267/year-0910/part-02'
ids = json.loads((batch / 'sql/key-map.json').read_text())
targets = {
    'person': ('person', 'person_马宾'),
    'relationship': ('person_relationship', 'relationship_person_马殷_person_马宾_兄长'),
    'person_claim': ('fact_claim', 'claim_zztj_267_0910_02_0056'),
    'edge_claim': ('fact_claim', 'claim_zztj_267_0910_02_0057'),
    'relationship_claim': ('fact_claim', 'claim_zztj_267_0910_02_0060'),
}
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

rows = {label: one(table, ids[key]) for label, (table, key) in targets.items()}
person = rows['person']
assert person['status'] == 'published' and person['name'] in ('马宾', '马賨')
assert person['id'] == ids['person_马宾']
assert rows['relationship']['person_b'] == person['id']
assert rows['relationship']['status'] == 'published'
assert rows['person_claim']['subject_id'] == person['id']
assert rows['edge_claim']['subject_id'] == ids['participation_zztj_267_0910_ma_yin_tiance_person_马宾']
assert rows['relationship_claim']['subject_id'] == rows['relationship']['id']
assert all(rows[k]['status'] == 'published' for k in ('person_claim', 'edge_claim', 'relationship_claim'))
assert {r['id'] for r in req('person_event', 'person_id=eq.' + person['id'])} == {
    ids['participation_zztj_267_0910_ma_yin_tiance_person_马宾']}

replacement = {
    'person': {'name': '马賨', 'aliases': sorted(set(person.get('aliases') or []) | {'马宾', '馬賨'}),
               'description': '《资治通鉴》卷267开平四年条所见楚王马殷之弟马賨；选定电子底本此处作“宾”，胡三省音注本作“賨”。'},
    'relationship': {'description': '马殷是马賨的兄长。'},
    'person_claim': {'claim_text': '本段记马賨：马殷之弟，任天策府左相。',
                     'note': '原文：楚王殷求为天策上将，诏加天策上将军。殷始开天策府，以弟宾为左相，存为右相。；核对说明：选定电子底本作“宾”，《资治通鉴》胡三省音注本作“賨”并注读音；《旧五代史》卷31后续称马賨。规范展示作马賨，原文保留。'},
    'edge_claim': {'claim_text': '马賨：马殷之弟，任天策府左相。',
                   'note': '原文：楚王殷求为天策上将，诏加天策上将军。殷始开天策府，以弟宾为左相，存为右相。；核对说明：底本“宾”按胡三省音注本校作“賨”，参与的稳定 ID 不变。'},
    'relationship_claim': {'claim_text': '马殷是马賨的兄长。',
                           'note': '原文：以弟宾为左相；核对说明：选定电子底本“宾”，胡三省音注本作“賨”；同一楚王之弟，不另建人物或关系。'},
}
original_batch = json.loads((batch / 'content-batch.json').read_text())
original_groups = {'person': 'people', 'relationship': 'person_relationships',
                   'person_claim': 'claims', 'edge_claim': 'claims',
                   'relationship_claim': 'claims'}
for label, patch in replacement.items():
    row = rows[label]
    original = next(value for value in original_batch[original_groups[label]]
                    if value['key'] == targets[label][1])
    for field, new_value in patch.items():
        old_value = row[field]
        assert old_value in (new_value, original[field]), (label, field)

if args.apply:
    for label, patch in replacement.items():
        table, key = targets[label]
        if all(rows[label][k] == v for k, v in patch.items()):
            continue
        changed = req(table, 'id=eq.' + ids[key], 'PATCH', patch)
        assert len(changed) == 1 and all(changed[0][k] == v for k, v in patch.items()), label
    headers['apikey'] = env['SUPABASE_ANON_KEY']
    headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    for label, (table, key) in targets.items():
        visible = one(table, ids[key])
        assert visible['status'] == 'published'
        assert all(visible[k] == v for k, v in replacement[label].items()), label
    (HERE / 'publication.json').write_text(json.dumps({
        'verified': True, 'at': datetime.now(timezone.utc).isoformat(),
        'canonical_person_id': person['id'], 'canonical_name': '马賨',
        'retained_original_batch': str(batch.relative_to(ROOT)),
        'anonymous_readback_verified': True,
    }, ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight', 'person': '马賨', 'stable_id': person['id']})
