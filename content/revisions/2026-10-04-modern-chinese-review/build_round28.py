# coding: utf-8
"""Expand a complete location caveat, without changing historical places or coordinates."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path=Path('/private/tmp/histree-public-prose-20261004.json');snapshot=read(snapshot_path);assert sha(snapshot_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-26/readback-audit.json')['verified']
all_rows={t:{r['id']:dict(r) for r in records} for t,records in snapshot['tables'].items()};rows=all_rows['event'];overlays=[]
for path in sorted(P.glob('round-*/changes.json')):
 proof=path.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(path)
 overlays.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
 for c in read(path)['changes']:
  all_rows[c['table']][c['id']].update(c['after'])
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:fields=[json.loads(line) for line in f]
pending={x['id'] for x in fields if x['table']=='event' and x['field']=='location_note' and x['status']=='pending'}
old='仅保留史载地名；未核坐标。';new='地点沿用史书记载的名称，现代坐标尚未核实。'
matching=[rid for rid in sorted(rows) if rid in pending and rows[rid]['location_note']==old]
selected=matching[:1000];assert len(selected)==1000
changes=[dict(table='event',id=rid,baseline=rows[rid],before=dict(location_note=old),after=dict(location_note=new),review='匹配已核读的完整地点解释句子，展开为白话；仅说明地名沿史书记载、坐标尚未核实，不改变地名、坐标、时间、标题或正文。其余展示字段仍保留各自审查状态。') for rid in selected]
corrections=[]
old_label='《新五代史·末帝纪》记七月戊申攻克魏州。'
new_label='《新五代史》记七月戊申攻克魏州。'
matching_claims=[r for r in all_rows['fact_claim'].values() if r['claim_text']==old_label]
assert len(matching_claims)==1
r=matching_claims[0]
assert any(x['table']=='fact_claim' and x['id']==r['id'] and x['field']=='claim_text' and x['status']=='reviewed_verified' and x['round']=='round-26' for x in fields)
changes.append(dict(table='fact_claim',id=r['id'],baseline=r,before=dict(claim_text=old_label),after=dict(claim_text=new_label),review='去掉易被误认作正式篇名的“末帝纪”标签，仅写《新五代史》；戊申、攻克魏州及原文、具体卷次定位和来源链接保持不变。此字段已在round-26审阅，本次纠正不重复计入新增已审字段。'))
corrections.append(dict(table='fact_claim',id=r['id'],field='claim_text',previous_round='round-26'))
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-04'
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-28';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='全站待审事件的完整地点解释句式，按稳定ID继续处理1000条；另纠正一条已审《新五代史》事实的书目标签，该字段不重复计入新增进度。其余字段和未选记录不据此标为已审。',inventory_sha256=sha(snapshot_path),verified_overlays=overlays,exact_sentence_selection=dict(before=old,after=new,pending_matches_before=len(matching),selected=len(selected),matching_still_pending_after=len(matching)-len(selected)),changes=changes,reviewed_unchanged=[],archives=archives,already_reviewed_corrections=corrections,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print(plan['exact_sentence_selection'])
