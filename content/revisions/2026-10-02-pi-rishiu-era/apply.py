"""Correct Pi Rixiu's broad era with a source-linked claim; read-only by default."""
import argparse
import hashlib
import json
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / 'plan.json').read_text())
parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
evidence = ROOT / plan['evidence_file']
assert hashlib.sha256(evidence.read_bytes()).hexdigest() == plan['evidence_sha256']
assert plan['evidence_excerpt'] in evidence.read_text()
paragraph = json.loads((evidence.parent / 'paragraph.json').read_text())
assert paragraph['id'] == 'xin-tangshu-685ef499825e-p012889'
namespace = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/greed-216/histree/content')
def uid(key): return str(uuid.uuid5(namespace, key))
ids = json.loads((ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-03/sql/key-map.json').read_text())
assert ids[plan['person_key']] == plan['person_id']
assert ids[plan['parent_relationship_key']] == uid(plan['parent_relationship_key'])
source = dict(id=uid(plan['source_key']), title='新唐书·卷五十九', source_type='primary',
              author='欧阳修等', edition='选定EPUB转换TXT逐字导出；电子本，纸本及异文待核。',
              url='https://github.com/greed-216/histree/blob/' + plan['source_commit'] + '/' + plan['evidence_file'],
              note=paragraph['citation'])
claim = dict(id=uid(plan['claim_key']), subject_table='person', subject_id=plan['person_id'],
             field_path='era', claim_text='《新唐书》载皮日休咸通间任太常博士，人物时代校为晚唐。',
             source_id=source['id'], citation=paragraph['citation'],
             note='原文：' + plan['evidence_excerpt'] + '；核对说明：咸通为唐代年号；原批次916年为儿子皮光业活动年份，不能作为皮日休的时代。',
             status='published')
env = dict(line.split('=', 1) for line in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in line and not line.startswith('#'))
headers = {'apikey': env['SUPABASE_SERVICE_ROLE_KEY'],
           'Authorization': 'Bearer ' + env['SUPABASE_SERVICE_ROLE_KEY'],
           'Content-Type': 'application/json', 'Prefer': 'return=representation'}
def req(table, expression='', method='GET', body=None):
    request = urllib.request.Request(env['SUPABASE_URL'] + '/rest/v1/' + table + '?' + expression,
                                     headers=headers, method=method,
                                     data=None if body is None else json.dumps(body, ensure_ascii=False).encode())
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)
def one(table, row_id):
    result = req(table, 'id=eq.' + row_id)
    assert len(result) <= 1
    return result[0] if result else None
person = one('person', plan['person_id'])
assert person and person['name'] == plan['name'] and person['status'] == 'published'
assert person['era'] in (plan['before_era'], plan['after_era'])
assert person['description'] in (plan['before_description'], plan['after_description'])
relation = one('person_relationship', ids[plan['parent_relationship_key']])
assert relation and relation['status'] == 'published' and relation['person_a'] == plan['person_id']
for table, row in [('source', source), ('fact_claim', claim)]:
    old = one(table, row['id'])
    if old:
        assert all(old.get(k) == value for k, value in row.items()), (table, row['id'])
if args.apply:
    for table, row in [('source', source), ('fact_claim', claim)]:
        if not one(table, row['id']):
            created = req(table, '', 'POST', row)
            assert len(created) == 1 and created[0]['id'] == row['id']
    if person['era'] != plan['after_era'] or person['description'] != plan['after_description']:
        changed = req('person', 'id=eq.' + plan['person_id'], 'PATCH',
                      {'era': plan['after_era'], 'description': plan['after_description']})
        assert len(changed) == 1 and changed[0]['era'] == plan['after_era']
    headers['apikey'] = env['SUPABASE_ANON_KEY']
    headers['Authorization'] = 'Bearer ' + env['SUPABASE_ANON_KEY']
    actual = one('person', plan['person_id'])
    assert actual and actual['era'] == plan['after_era'] and actual['description'] == plan['after_description']
    assert one('source', source['id'])['url'] == source['url']
    assert one('fact_claim', claim['id'])['source_id'] == source['id']
    (HERE / 'publication.json').write_text(json.dumps({'verified': True,
        'at': datetime.now(timezone.utc).isoformat(), 'person_id': plan['person_id'],
        'source_id': source['id'], 'claim_id': claim['id'], 'anonymous_readback_verified': True},
        ensure_ascii=False, indent=2) + '\n')
print({'mode': 'apply' if args.apply else 'preflight', 'person': plan['name'],
       'era': plan['after_era']})
