# coding: utf-8
"""Curated evidence notes, dates and locations for 936 paragraphs 37 through 41."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-13/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-06';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');notes=read(P/'notes-936-part06.json');claims=read(P/'claims-936-part06.json')
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
 if table=='event' and field=='time_original':c['preserved_original_dates']='保留936年、清泰末、十一月或闰十一月及原干支日期；各书日期异说分别保留，追述持续时间不当作开始日期，不换算公历日。'
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if ('fact_claim',rid,'note') in pending:
  quote,old=c['note'].split('；核对说明：',1);assert old in notes
  assert quote==original['note'].split('；核对说明：',1)[0]
  patch('fact_claim',rid,'note',quote+'；核对说明：'+notes[old],'逐条核读引用与解释，展开书名、人物、日期异说和校核理由；保留具体保留意见，引用字形不变。')
 if ('fact_claim',rid,'claim_text') in pending:
  assert c['claim_text'] in claims,c['claim_text']
  patch('fact_claim',rid,'claim_text',claims[c['claim_text']],'本条所引史料独立表述，展开史书简称、动作和日期；保留原纪年与计划、异说的限定，不混入其他来源细节。')
for original in batch['events']:
 rid=ids[original['key']];event=rows['event'][rid]
 if ('event',rid,'time_original') in pending:
  assert event['time_original'] in claims,event['time_original']
  patch('event',rid,'time_original',claims[event['time_original']],'明确年份、月份、日期未载或不同史书日期差异，保留原纪年和干支；不改变实际日期字段。')
 if ('event',rid,'location_note') in pending:
  assert event['location_note']=='仅保留史载地名；未核坐标。',event['location_note']
  patch('event',rid,'location_note','地点沿用史书记载的名称，现代坐标尚未核实。','将地点核对说明展开为白话；地点名称及坐标保持原值。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-14';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第37—41段尚待审的事实核对说明、事实正文，以及40个事件的时间和地点解释；已核字段不重复计数。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
