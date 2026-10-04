# coding: utf-8
"""Expand a complete location caveat, without changing historical places or coordinates."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snapshot_path=Path('/private/tmp/histree-public-prose-20261004.json');snapshot=read(snapshot_path);assert sha(snapshot_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-34/readback-audit.json')['verified']
all_rows={t:{r['id']:dict(r) for r in records} for t,records in snapshot['tables'].items()};rows=all_rows['event'];overlays=[]
for path in sorted(P.glob('round-*/changes.json')):
 proof=path.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(path)
 overlays.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
 for c in read(path)['changes']:
  all_rows[c['table']][c['id']].update(c['after'])
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:fields=[json.loads(line) for line in f]
part03=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-03';ids=read(part03/'sql/key-map.json')
changes=[];corrections=[]
values={
 '0247':'《旧五代史》明确记载沙彦珣在七月初三召集士兵入城，讨伐叛乱士兵。',
 '0111':'《旧五代史》在己酉记载安叔千奏报，安重荣强行带走驻军五百骑，反叛后进入太原。'}
for code,new in values.items():
 rid=ids['claim_zztj_280_0936_03_'+code];r=all_rows['fact_claim'][rid]
 assert any(x['table']=='fact_claim' and x['id']==rid and x['field']=='claim_text' and x['status']=='reviewed_verified' and x['round']=='round-34' for x in fields)
 changes.append(dict(table='fact_claim',id=rid,baseline=r,before=dict(claim_text=r['claim_text']),after=dict(claim_text=new),review='复核军事语境，将“入城诛乱军”说明为讨伐而不推定俘后处刑；将“驱掠戍兵”说明为强行带走驻军，避免添加独立劫掠地点或行动。此字段已审，不重复计入新增进度。'))
 corrections.append(dict(table='fact_claim',id=rid,field='claim_text',previous_round='round-34'))
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-03'
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-36';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='复核两条已审军事行动说明的措辞，不将入城讨伐写成确定的俘后处刑，也不把强行带走驻军写成独立劫掠行动；不重复计入新增已审字段。',inventory_sha256=sha(snapshot_path),verified_overlays=overlays,changes=changes,reviewed_unchanged=[],archives=archives,already_reviewed_corrections=corrections,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print('Prepared two wording corrections; no newly reviewed fields.')
