# coding: utf-8
"""Expand one reviewed complete sentence; protect each individual quotation."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path=Path('/private/tmp/histree-public-prose-20261004.json');snapshot=read(snapshot_path);assert sha(snapshot_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-15/readback-audit.json')['verified']
rows={r['id']:r for r in snapshot['tables']['source']};overlays=[]
for path in sorted(P.glob('round-*/changes.json')):
 proof=path.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(path)
 overlays.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
 for c in read(path)['changes']:
  if c['table']=='source':rows[c['id']].update(c['after'])
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:fields=[json.loads(line) for line in f]
pending={(x['id'],x['field']) for x in fields if x['table']=='source' and x['status']=='pending'}
copy=read(P/'source-explanation-sentences.json');changes=[];unchanged=[]
for rid in sorted(rows):
 row=rows[rid];before={};after={}
 for field in ['edition','note']:
  if (rid,field) not in pending:continue
  old=row[field]
  if field=='edition':
   if old not in copy['edition']:continue
   new=copy['edition'][old]
  else:
   parts=old.split('；',1);explanation=parts[-1]
   if explanation not in copy['note_explanation']:continue
   new=('；'.join([parts[0],copy['note_explanation'][explanation]]) if len(parts)==2 else copy['note_explanation'][explanation])
   if len(parts)==2:assert old.split('；',1)[0]==new.split('；',1)[0]
  if new==old:unchanged.append(dict(table='source',id=rid,fields=[field],baseline=row,review='完整句式已经清楚，保留原值；仍需匿名回查。'))
  else:before[field]=old;after[field]=new
 if after:changes.append(dict(table='source',id=rid,baseline=row,before=before,after=after,review='精确匹配已审完整版本或核对句式，展开为现代汉语；待核状态和独立证据限制保留。书名、卷年段定位、URL和作者均保持原值，不涉及原文文件或史实判断。'))
D=P/'round-16';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='全站仍待审出处中精确匹配已审完整版本和核对句式的字段；只改展示解释，不改引用位置、来源URL或核对状态。',inventory_sha256=sha(snapshot_path),verified_overlays=overlays,changes=changes,reviewed_unchanged=unchanged,archives=[],full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(dict(changes=len(changes),changed_fields=sum(len(c['after']) for c in changes),unchanged_fields=len(unchanged)))
