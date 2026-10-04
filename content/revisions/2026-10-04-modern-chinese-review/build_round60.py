# coding: utf-8
"""Curated evidence notes, dates and locations for 936 paragraphs 13 through 20."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-59/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-03';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');notes=read(P/'notes-935-part04-remaining.json')
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
times=read(P/'times-935-part03.json');facts=read(P/'claims-935-part03-remaining.json')
for original in batch['events']:
 rid=ids[original['key']];r=rows['event'][rid]
 if ('event',rid,'time_original') not in pending:continue
 old=r['time_original'];new=times.get(old,old)
 if new==old:assert old in ['935年七月乙巳','935年七月丁巳','935年九月丙申','935年九月己酉','935年九月戊寅']
 patch('event',rid,'time_original',new,'对照原文明载纪时及相对时序，白话展开未知日期和概括性经历；原年、月、干支与未载日期保持不变，不换算公历。')
 if new!=old:changes[('event',rid)]['preserved_original_dates']='935年、六月、七月、九月及乙巳、丁巳、丙申、己酉、戊寅原样保留；原起始年、起止年月或各次年月未载的仍未知，不换算公历日期。'
for original in batch['claims']:
 rid=ids[original['key']];r=rows['fact_claim'][rid]
 if ('fact_claim',rid,'claim_text') not in pending:continue
 code=original['key'][-4:];assert code in facts
 patch('fact_claim',rid,'claim_text',facts[code],'逐条核读该条引用的动作、身份、纪时与补书差异；主书与补证各按独立引用说明，不把提议或诏命当已执行，不改变引用和已验证解释区。')
for original in batch['sources']:
 rid=ids[original['key']];r=rows['source'][rid]
 if ('source',rid,'title') not in pending:continue
 assert r['title'].startswith(('资治通鉴·','旧五代史·','新五代史·')),r['title']
 patch('source',rid,'title',r['title'],'完整书名、卷次及片段名称已清楚，作为出处定位保留原值，URL和原文快照不变。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-60';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='935年第21—28段事件纪时、剩余69条事实正文及待审出处标题；主书、补书分别表述，未知日期保持未知，原文与保护字段不变。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
