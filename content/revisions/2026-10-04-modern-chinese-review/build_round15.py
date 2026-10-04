# coding: utf-8
"""Curated evidence notes, dates and locations for 936 paragraphs 37 through 41."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-14/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-06';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json')
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
for original in batch['sources']:
 rid=ids[original['key']];source=rows['source'][rid]
 for field in ['title','edition','note']:
  if ('source',rid,field) not in pending:continue
  value=source[field]
  if field=='edition':
   assert value=='选定TXT逐字导出；电子本，纸本及异文待核。'
   value='从选定的TXT电子文本逐字导出；纸质版本及不同版本文字差异尚待核对。'
  elif field=='note':
   prefix,explanation=value.split('；',1)
   assert explanation in ['已核上下文及传主，纸本及异文待核。','电子底本待考，分段待核']
   value=prefix+'；'+('已核对上下文和传主，纸质版本及不同版本文字差异尚待核对。' if explanation.startswith('已核') else '电子版本的来源尚待考证，自动分段尚待核对。')
  patch('source',rid,field,value,'核读书目标题和说明，展开版本、异文及分段的待核状态；书名、卷次和段落ID保留，URL和作者不变，不将待核升级为已核。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-15';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第37—41段所引用、仍待审阅的出处标题、电子版本说明和备注；保留原文链接、卷年段定位及待核状态。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
