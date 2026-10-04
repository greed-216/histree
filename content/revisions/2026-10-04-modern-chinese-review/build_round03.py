# coding: utf-8
"""Build the reviewed 936 Jinan evidence explanations; preserve frozen archives."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path)
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 audit=old_plan.with_name('readback-audit.json')
 if not audit.exists():continue
 proof=read(audit);assert proof['verified'] and proof['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
notes=read(P/'notes-936-jinan.json');claims=read(P/'claims-936-jinan.json');inputs=read(P/'next-936-jinan-claims.json')['claims']
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-07';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json')
changes={};unchanged=[]
def patch(table,rid,field,value,review):
 base=rows[table][rid];old=base[field]
 if old==value:
  unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,before={},after={},baseline=base,review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=value
 if table=='event' and field=='time_original':c['preserved_original_dates']='保留936年、闰十一月及原有干支日；仅展开投降、去世等动作和未载具体日期的解释。追叙不强定为936年，其他史书异时序继续并列。'
for x in inputs:
 c=rows['fact_claim'][x['public_id']];note=c['note'];quote,old=note.split('；核对说明：',1)
 assert quote==x['claim']['note'].split('；核对说明：',1)[0]
 assert old in notes,old
 patch('fact_claim',c['id'],'note',quote+'；核对说明：'+notes[old],'逐项阅读这条核对说明，展开书名、人物代称、时间和疑字处理理由；原文逐字保留，不改出处和事实身份。')
 if x['claim_text_needs_review']:
  assert c['claim_text'] in claims,c['claim_text']
  patch('fact_claim',c['id'],'claim_text',claims[c['claim_text']],'依据本条所引用记载展开史书简称和动作；保留计划、追叙及异说，不把补证写成已确定唯一结论。')
for event in batch['events']:
 rid=ids[event['key']];old=rows['event'][rid]['time_original'];assert old in claims,old
 patch('event',rid,'time_original',claims[old],'对照同一事件的时间事实说明展开白话，保留原年、月、干支日及日期未载或异说的限定。')
round_dir=P/'round-03';assert not (round_dir/'publication.json').exists()
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
write(round_dir/'changes.json',dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第42—47段的260条事实核对说明、尚未审阅的92条事实说明及52个事件的时间解释；引用原文及档案保持不变。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False))
from collections import Counter
print(dict(changed_rows=len(changes),changed_fields=sum(len(c['after']) for c in changes.values()),by_table=dict(Counter(c['table'] for c in changes.values())),unchanged_reviewed_fields=len(unchanged)))
