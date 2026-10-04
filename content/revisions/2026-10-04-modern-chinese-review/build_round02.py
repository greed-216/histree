# coding: utf-8
"""Curated first round; no database writes and no published archive rewrites."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
snapshot=read(Path('/private/tmp/histree-public-prose-20261004.json'))
assert len(snapshot['completed_tables'])==8,'Complete the public inventory first'
rows={table:{r['id']:r for r in records} for table,records in snapshot['tables'].items()}
# Overlay only independently verified earlier rounds; the frozen inventory remains unchanged.
for old_plan in sorted(P.glob('round-*/changes.json')):
 audit=old_plan.with_name('readback-audit.json')
 if not audit.exists():continue
 proof=read(audit);assert proof['verified'] and proof['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
curated=read(P/'curated-936-jinan.json');roles=read(P/'roles-936-jinan.json');profiles=read(P/'people-936-jinan.json')
parts=[ROOT/'content/books/zizhi-tongjian/vol-280/year-0936'/part for part in ['part-07']]
archives=[];event_ids={};role_ids={};scope_claim_ids=set();relations={}
for part in parts:
 b=read(part/'content-batch.json');ids=read(part/'sql/key-map.json')
 archives.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(s.relative_to(ROOT)),sha256=sha(s)) for s in sorted((part/'sources').rglob('source.txt'))]))
 for event in b['events']:
  code=event['key'].removeprefix('event_zztj_280_0936_');assert code in curated
  event_ids[ids[event['key']]]=code
 for edge in b['person_events']:role_ids[ids[edge['key']]]=edge['role']
 scope_claim_ids.update(ids[c['key']] for c in b['claims'])
 for rel in b['person_relationships']:relations[ids[rel['key']]]=rel
assert len(curated)==len(event_ids)==52
assert all(rid in rows['event'] for rid in event_ids)
assert all(rid in rows['person_event'] for rid in role_ids)
changes={};unchanged=[]
def patch(table,rid,after,review):
 baseline=rows[table][rid];after={k:v for k,v in after.items() if baseline[k]!=v}
 if not after:
  unchanged.append(dict(table=table,id=rid,fields=list(after),review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,before={},after={},baseline=baseline,review=review)
 c=changes[key]
 for field,value in after.items():c['before'][field]=baseline[field];c['after'][field]=value
for rid,code in event_ids.items():
 title,description=curated[code]
 patch('event',rid,dict(title=title,description=description),'核读本事件对应主书原文和已发布补证，展开主语与动作，区分回述、言辞、意向及有争议的时间，不改史实和原纪年。')
for rid,original in role_ids.items():
 baseline=rows['person_event'][rid];assert baseline['role']==original,(rid,'role was independently revised')
 assert original in roles,original
 patch('person_event',rid,dict(role=roles[original]),'依据这条参与记录的已发布事实引用，将省略主体的军职和动作说明展开成白话；本人不在场时仍明确说明。')
for rid,p in rows['person'].items():
 if p['name'] in profiles:patch('person',rid,dict(description=profiles[p['name']]),'依据936年已发布连续原文及独立补证重写人物简介；姓名、别名、生卒年和身份UUID保持原样。')
for rid in scope_claim_ids:
 c=rows['fact_claim'][rid];text=c['claim_text'];subject=c['subject_id']
 if c['subject_table']=='event' and subject in event_ids and c['field_path']=='description':
  event=rows['event'][subject]
  if text in [event['title']+'。',event['description']]:
   patch('fact_claim',rid,dict(claim_text=curated[event_ids[subject]][0]+'。'),'只重写本条原文直接支持的事件概述，不将其他书证的细节并入单条引用；原文摘录和定位保持原样。')
 if c['subject_table']=='person_event' and subject in role_ids and c['field_path']=='role':
  original=role_ids[subject]
  # Only the exact original role phrase, outside verbatim note, is rewritten.
  if original in text:patch('fact_claim',rid,dict(claim_text=text.replace(original,roles[original])),'与对应参与角色的白话修订一致，原文、出处、主体和引用ID均保留。')
 if c['subject_table']=='person' and c['field_path']=='description' and text.startswith('本段记'):
  for old,new in sorted(roles.items(),key=lambda x:-len(x[0])):
   if text.endswith('：'+old+'。'):
    name=text[len('本段记'):].split('：',1)[0]
    patch('fact_claim',rid,dict(claim_text=name+'：'+new+'。'),'将人物在本条中的角色说明改为白话，保留事实引用指向和逐字原文。');break
for rid,rel in relations.items():
 current=rows['person_relationship'][rid]
 assert current['description']==rel['description']
 unchanged.append(dict(table='person_relationship',id=rid,fields=['description'],review='已是明确白话，说明A相对于B的亲属身份；端点、方向和类型均无需改动。'))
round_dir=P/'round-02';assert not (round_dir/'publication.json').exists(), 'Do not rebuild an applied revision';plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年连续第42—47段中的52个事件标题和说明、89条参与角色、5位人物简介及其对应事实概述；核对4条亲属关系。原文和其余尚未审阅字段不改。',inventory_sha256=sha(Path('/private/tmp/histree-public-prose-20261004.json')),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
write(round_dir/'changes.json',plan)

from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(x['table'] for x in changes.values())),scope_roles=len(role_ids)))
