# coding: utf-8
"""Curated titles and explanations for 936 55 events in paragraphs 13 through 20."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-41/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
assert read(P/'part01-full-quotation-check.json')['count']==151
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-01';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');curated=read(P/'curated-936-part01.json')
events={ids[e['key']]:e['key'].removeprefix('event_zztj_280_0936_') for e in batch['events'] if e['key'].removeprefix('event_zztj_280_0936_') in curated};assert len(events)==len(curated)==30
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
pending={(x['table'],x['id'],x['field']) for x in ledger if x['status']=='pending'}
changes={};unchanged=[]
def patch(table,rid,field,new,review):
 base=rows[table][rid];old=base[field]
 if old==new:unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,baseline=base,before={},after={},review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=new
manual=read(P/'claims-936-part01-supplements.json');manual.update({'0052':'述律平是吕琦谈话中提及的契丹太后，原文没有说她在场。','0054':'耶律倍是吕琦谈话中提及的赞华，当时居于后唐境内；原文没有说他在场。','0057':'荝剌是吕琦谈话中提及、契丹曾请求送回的人物。'});roles=read(P/'roles-936-part01.json')
participations={ids[x['key']]:x for x in batch['person_events']}
role_evidence=[]
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if c['subject_table']=='person_event' and c['field_path']=='role':
  pe=rows['person_event'][c['subject_id']];role=roles[participations[c['subject_id']]['key']]
  name=rows['person'][pe['person_id']]['name'];role_evidence.append((c,pe,name,role))
active={(c['table'],c['id']) for c in read(P/'round-41/changes.json')['changes']};deferred=[]
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid];code=original['key'][-4:]
 if ('fact_claim',rid,'claim_text') not in pending:continue
 if code in manual:new=manual[code]
 elif c['subject_table']=='person_event':
  evidence=[x for x in role_evidence if x[0]['id']==rid];assert len(evidence)==1
  _,pe,name,role=evidence[0];new=name+'：'+role+'。'
 elif c['subject_table']=='person' and c['field_path']=='description':
  candidates=[x for x in role_evidence if x[1]['person_id']==c['subject_id'] and x[0]['source_id']==c['source_id'] and x[0]['note'].split('；核对说明：',1)[0]==c['note'].split('；核对说明：',1)[0]]
  assert candidates,(code,c['claim_text']);wanted={x[2]+'：'+x[3]+'。' for x in candidates};assert len(wanted)==1;new=next(iter(wanted))
 elif c['subject_table']=='event' and c['field_path']=='description':
  original_event=next(e for e in batch['events'] if ids[e['key']]==c['subject_id'])
  assert c['claim_text']==original_event['description'],(code,c['claim_text'])
  new=curated[original_event['key'].removeprefix('event_zztj_280_0936_')][0]+'。'
 elif c['subject_table']=='event' and c['field_path']=='time_original':
  new=rows['event'][c['subject_id']]['time_original']
 elif c['subject_table']=='person_relationship':
  new=rows['person_relationship'][c['subject_id']]['description'];assert c['claim_text']==new
 else:raise AssertionError((code,c['field_path']))
 patch('fact_claim',rid,'claim_text',new,'核读该条完整引用，展开书名、人物、动作和时间解释；事件、人物与参与事实按同一引用对应，不把计划、传闻或评价写成既成事实。引用及身份、出处保留。')
assert read(P/'round-41/readback-audit.json')['verified']
assert len(changes)+len(unchanged)==48
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-48';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第1—8段此前等待第41轮核对说明更新的48条事实正文；基于独立验证后的最新原值，引用与解释区保留，逐条对应人物动作及事件时间说明。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,deferred_active_write_ids=deferred,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
