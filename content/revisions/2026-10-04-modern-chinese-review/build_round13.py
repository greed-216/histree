# coding: utf-8
"""Curated participation wording for 936 paragraphs 37 through 41."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-12/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-06';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');curated=read(P/'curated-936-part06-roles.json')
changes={};unchanged=[]
def patch(table,rid,field,new,review):
 base=rows[table][rid];old=base[field]
 if old==new:unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,baseline=base,before={},after={},review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=new
roles={};used=set()
for original in batch['person_events']:
 rid=ids[original['key']];role=rows['person_event'][rid]['role'];assert role in curated
 roles[rid]=curated[role];used.add(role)
 patch('person_event',rid,'role',curated[role],'逐条核读本参与的原文，展开动作和涉及人物；计划、请求、意见和实际行动区分表述，不改变人物、事件或关系方向。')
assert len(roles)==58 and set(curated)==used
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if c['subject_table']=='person_event' and c['subject_id'] in roles and c['field_path']=='role':
  participation=rows['person_event'][c['subject_id']];name=rows['person'][participation['person_id']]['name']
  assert c['claim_text']==name+'：'+participation['role']+'。'
  patch('fact_claim',rid,'claim_text',name+'：'+roles[c['subject_id']]+'。','对应参与角色改为白话，逐条核对该条引用只支持的动作；姓名、原文、核对说明和出处保持不变。')
 elif c['subject_table']=='person' and c['field_path']=='description':
  name=rows['person'][c['subject_id']]['name'];prefix='本段记'+name+'：'
  assert c['claim_text'].startswith(prefix) and c['claim_text'].endswith('。')
  oldrole=c['claim_text'][len(prefix):-1];assert oldrole in curated
  patch('fact_claim',rid,'claim_text',name+'：'+curated[oldrole]+'。','将人物事实说明中的录入模板展开为该引用所述行动，不把一条行动扩写成完整生平。人物总介绍仍待独立审阅。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-13';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第37—41段的58条参与角色及对应事实说明，人物引用中同样的角色说明一并展开为白话；人物总介绍等其他未审字段保留待审。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
