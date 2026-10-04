# coding: utf-8
"""Review 935 paragraphs 12 through 20 event prose and corresponding core claims."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-61/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
assert read(P/'935-part02-full-quotation-check.json')['count']==195
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-02';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');curated=read(P/'curated-935-part02.json')
events={ids[e['key']]:e['key'] for e in batch['events'] if e['key'] in curated};assert len(events)==len(curated)==36
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
 if '/tongjian-' not in source['url'] and events[c['subject_id']]!='event_zztj_279_0935_yang_tan_moves_dingzhou':continue
 if ('fact_claim',rid,'claim_text') in pending:
  patch('fact_claim',rid,'claim_text',curated[events[c['subject_id']]][1],'核读同一事件的同一出处原文，事件正文与核心事实说明保持一致；其他史书补证保持独立字段。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-62';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='935年第12—20段36个事件的标题、正文和对应核心事实说明；逐条核读原文和补证，区分建议、诏令、评价、追叙和已发生行动。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
