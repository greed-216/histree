# coding: utf-8
"""Curated evidence notes, dates and locations for 936 paragraphs 13 through 20."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-52/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-04';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');notes=read(P/'notes-935-part04-remaining.json')
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
pending={(x['table'],x['id'],x['field']) for x in ledger if x['status']=='pending'}
changes={};unchanged=[]
def patch(table,rid,field,new,review):
 assert (table,rid,field) in pending
 base=rows[table][rid];old=base[field]
 if old==new:unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,baseline=base,before={},after={},review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=new
 if table=='event' and field=='time_original':c['preserved_original_dates']='保留936年、清泰末及九月、十月、十一月和原干支日期；追叙背景的未知年份仍未知，原文没有单列的日期仍未载，不换算公历日。'
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if ('fact_claim',rid,'note') in pending and c['note'].split('；核对说明：',1)[1] in notes:
  quote,old=c['note'].split('；核对说明：',1);assert old in notes
  assert quote==original['note'].split('；核对说明：',1)[0]
  patch('fact_claim',rid,'note',quote+'；核对说明：'+notes[old],'逐条核读引用与解释，展开书名、人物、日期异说和校核理由；保留具体保留意见，引用字形不变。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-53';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='935年第29—37段批次余下38类具体核对说明，展开书名、日期、关系及异说；仅修改解释区，引用原字与保护字段不变。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
