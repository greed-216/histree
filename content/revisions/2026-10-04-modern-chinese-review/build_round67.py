# coding: utf-8
"""Review 935 paragraphs 12 through 20 event prose and corresponding core claims."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-66/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
assert read(P/'935-part01-full-quotation-check.json')['count']==110
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-01';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');curated=read(P/'curated-935-part01.json')
events={ids[e['key']]:e['key'] for e in batch['events'] if e['key'] in curated};assert len(events)==len(curated)==18
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
pending={(x['table'],x['id'],x['field']) for x in ledger if x['status']=='pending'}
changes={};unchanged=[]
def patch(table,rid,field,new,review):
 base=rows[table][rid];old=base[field]
 if old==new:unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,baseline=base,before={},after={},review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=new
for rid,code in events.items():
 for field,new in zip(['title','description'],curated[code]):
  if ('event',rid,field) not in pending:continue
  patch('event',rid,field,new,'核读本事件主书引用和独立补证，使用完整姓名、白话动作和具体书名；承诺、预计、计划、争议与实际发生的事分别说明。不改变时间、地点和主体。')
for claim in batch['claims']:
 rid=ids[claim['key']];c=rows['fact_claim'][rid]
 if c['subject_table']!='event' or c['field_path']!='description' or c['subject_id'] not in events:continue
 source=rows['source'][c['source_id']]
 if '/tongjian-' not in source['url']:continue
 if ('fact_claim',rid,'claim_text') in pending:
  patch('fact_claim',rid,'claim_text',curated[events[c['subject_id']]][1],'核读同一事件的同一出处原文，事件正文与核心事实说明保持一致；其他史书补证保持独立字段。')
role_text=read(P/'roles-935-part01.json')
manual_facts={}
roles={};role_evidence=[]
for original in batch['person_events']:
 rid=ids[original['key']];base=rows['person_event'][rid];new=role_text[original['key']];roles[rid]=new
 if ('person_event',rid,'role') in pending:patch('person_event',rid,'role',new,'逐项核读参与引用，写清行动与涉及人物，区分请求、方案、意见和实际行动；人物和事件ID保持原值。')
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if c['subject_table']=='person_event' and c['subject_id'] in roles and c['field_path']=='role':
  participation=rows['person_event'][c['subject_id']];name=rows['person'][participation['person_id']]['name'];role_evidence.append((c,participation,name,roles[c['subject_id']]))
  if ('fact_claim',rid,'claim_text') in pending:patch('fact_claim',rid,'claim_text',name+'：'+roles[c['subject_id']]+'。','对应参与事实展开为该引用所支持的动作；逐字引用、校核说明和出处保持不变。')
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if c['subject_table']=='person' and c['field_path']=='description' and ('fact_claim',rid,'claim_text') in pending:
  if rid in manual_facts:
   patch('fact_claim',rid,'claim_text',manual_facts[rid],'明确书名、人名及原文“弟子”的歧义，不推定为师徒或叔侄关系。')
   continue
  candidates=[x for x in role_evidence if x[1]['person_id']==c['subject_id'] and x[0]['source_id']==c['source_id'] and x[0]['note'].split('；核对说明：',1)[0]==c['note'].split('；核对说明：',1)[0]]
  if not candidates:continue
  wanted={x[2]+'：'+x[3]+'。' for x in candidates};assert len(wanted)==1
  patch('fact_claim',rid,'claim_text',next(iter(wanted)),'人物事实与参与引用逐字一致并对应同一主体，按该条动作展开；不扩写人物完整生平，不改变引用、身份或关系。')
for original in batch['person_relationships']:
 rid=ids[original['key']];r=rows['person_relationship'][rid]
 new=r['description']
 assert r['relation_type'] in ['兄弟','母亲','丈夫','族亲','父亲'],r
 if ('person_relationship',rid,'description') in pending:patch('person_relationship',rid,'description',new,'逐条核读原文明示的父女、父子、夫妻和兄弟长幼关系，现有说明已用姓名写明方向；保留关系文案及端点，不推定生母或添建反向边。')
 for claim_original in batch['claims']:
  c=rows['fact_claim'][ids[claim_original['key']]]
  if c['subject_table']=='person_relationship' and c['subject_id']==rid and ('fact_claim',c['id'],'claim_text') in pending:
   if not c['claim_text'].endswith(('的兄弟。','的母亲。','的丈夫。','的族亲。','的父亲。')):continue
   patch('fact_claim',c['id'],'claim_text',c['claim_text'],'原文关系明确，现有事实句已完整说明双方姓名、身份与方向；逐字引用、称号和关系端点保持不变，不补出生母或未载亲属。')

archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-67';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='935年第1—11段18个事件、30条人物参与及同出处对应事实；核读8条亲属关系，清楚的方向说明保留，身份和原文不变。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
