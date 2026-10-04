# coding: utf-8
"""Expand one reviewed complete sentence; protect each individual quotation."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
OLD='参与身份依据本句；人名沿用已有主体，原文不改字。'
NEW='参与角色依据所引原文，人物沿用已有记录；引用保持底本字形。'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path=Path('/private/tmp/histree-public-prose-20261004.json');snapshot=read(snapshot_path);assert sha(snapshot_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-11/readback-audit.json')['verified']
rows={r['id']:r for r in snapshot['tables']['fact_claim']};overlays=[]
for path in sorted(P.glob('round-*/changes.json')):
 proof=path.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(path)
 overlays.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
 for c in read(path)['changes']:
  if c['table']=='fact_claim':rows[c['id']].update(c['after'])
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:fields=[json.loads(line) for line in f]
pending={x['id'] for x in fields if x['table']=='fact_claim' and x['field']=='note' and x['status']=='pending'}
matched=[]
for rid in sorted(pending):
 row=rows[rid];note=row['note']
 if note and note.startswith('原文：') and '；核对说明：' in note and note.split('；核对说明：',1)[1]==OLD:matched.append(row)
assert len(matched)==5765
selected=matched;changes=[]
for row in selected:
 quote=row['note'].split('；核对说明：',1)[0]
 changes.append(dict(table='fact_claim',id=row['id'],baseline=row,before=dict(note=row['note']),after=dict(note=quote+'；核对说明：'+NEW),review='将已审完整句式中的“本句”“已有主体”“不改字”展开为引用原文、已有记录和底本字形；不改变具体参与角色、人物姓名或身份，不增加史实判断。逐条保留原文区。'))
D=P/'round-12';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='同一已审完整核对句式的剩余5765条待审说明；只改解释，不改引用、事实正文和其他字段。',inventory_sha256=sha(snapshot_path),old_explanation=OLD,new_explanation=NEW,total_pending_matching=len(matched),remaining_matching_after_this_plan=len(matched)-len(selected),verified_overlays=overlays,changes=changes,reviewed_unchanged=[],archives=[],full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(dict(changes=len(changes),same_sentence_pending=len(matched),remaining=len(matched)-len(selected)))
