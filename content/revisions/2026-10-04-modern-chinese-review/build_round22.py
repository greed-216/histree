# coding: utf-8
"""Curated titles and explanations for 936 paragraphs 21 through 28."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-21/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-04';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');curated=read(P/'curated-936-part04.json')
events={ids[e['key']]:e['key'].removeprefix('event_zztj_280_0936_') for e in batch['events']};assert len(events)==len(curated)==57
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
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if ('fact_claim',rid,'claim_text') in pending and c['subject_table']=='event' and c['subject_id'] in events and c['field_path']=='description':
  event=rows['event'][c['subject_id']]
  if c['claim_text'] in [event['title']+'。',event['description']]:
   patch('fact_claim',rid,'claim_text',curated[events[c['subject_id']]][0]+'。','本条概述只展开该引用支持的核心动作；完整多书补充说明放在事件正文，不混入单条原文事实。原文、校核说明和引用主体保持当前值。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-22';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第21—28段相关事件中尚待审的标题和正文，以及与原事件概述完全匹配的事实说明；已经审阅的共享事件保留当前值。其他字段保持各自审查状态。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
