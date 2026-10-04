# coding: utf-8
"""Curated evidence notes, dates and locations for 936 paragraphs 21 through 28."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-30/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-03';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');times=read(P/'times-936-part03.json')
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
 if table=='event' and field=='time_original':c['preserved_original_dates']='保留936年、五月、六月、七月及原干支日期；追述背景仍不确定起年，奏报日与行动日分开，未单独记载的具体日期仍未记载，不换算公历。'
for original in batch['events']:
 rid=ids[original['key']];c=rows['event'][rid]
 if ('event',rid,'time_original') not in pending:continue
 new=times.get(c['time_original'],c['time_original'])
 if new==c['time_original']:assert new.startswith('936年') and '条下' not in new and '主' not in new and '旧' not in new
 patch('event',rid,'time_original',new,'对照本事件原文和各书日期，展开追述、奏报、发生过程及未确定日期的说明；原纪年和干支保持不变，不换算公历，不把相对时间确定为某日。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-35';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第13—20段尚待审的事件时间说明，展开书名、人物和相对时序；原纪年和干支保留，已清楚的日期读回核验。其他字段分别审查。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
