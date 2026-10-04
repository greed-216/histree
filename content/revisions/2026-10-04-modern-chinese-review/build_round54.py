# coding: utf-8
"""Curated evidence notes, dates and locations for 936 paragraphs 13 through 20."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-53/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
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
times=read(P/'times-935-part04.json')
for original in batch['events']:
 rid=ids[original['key']];r=rows['event'][rid]
 if ('event',rid,'time_original') not in pending:continue
 old=r['time_original'];new=times.get(old,old)
 if new==old:assert old in ['935年十月己卯','935年十月庚辰','935年十月辛巳','935年十一月壬子','935年十一月壬子杀李仿之后','935年十一月乙卯','935年十二月壬申']
 patch('event',rid,'time_original',new,'核读逐字引用与本条时序，展开相对时间和未知日期，保留原年、月、干支及两书不同日期，不换算公历日。')
 if new!=old:changes[('event',rid)]['preserved_original_dates']='原935年、917年、十月、十一月、十二月及己卯、庚辰、辛巳、壬子、乙卯、壬申、乙酉、己丑保持原字。未知年月日仍未知，追述仍为追述，不换算公历。'
for original in batch['sources']:
 rid=ids[original['key']];r=rows['source'][rid]
 if ('source',rid,'title') not in pending:continue
 assert r['title'].startswith(('资治通鉴·','旧五代史·','新五代史·','宋史·')),r['title']
 patch('source',rid,'title',r['title'],'出处标题已使用完整书名、卷次及片段定位，专名保持原样，不更改来源URL和电子底本。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-54';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='935年第29—37段55个事件的时间解释与12个待审出处标题；相对时间展开为白话，具体年月干支及未知日期保留，事实字段另行审阅。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
