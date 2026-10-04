# coding: utf-8
"""Curated titles and explanations for 936 55 events in paragraphs 13 through 20."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-55/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
assert read(P/'935-part04-full-quotation-check.json')['count']==280
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-04';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json')
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
pending={(x['table'],x['id'],x['field']) for x in ledger if x['status']=='pending'}
changes={};unchanged=[]
def patch(table,rid,field,new,review):
 base=rows[table][rid];old=base[field]
 if old==new:unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,baseline=base,before={},after={},review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=new
profiles=read(P/'profiles-935-part04.json')['profiles']
quoteproof=read(P/'935-part04-profile-original-quotation-check.json');assert quoteproof['verified'] and quoteproof['count']==21
active={c['id']:c for c in read(P/'round-41/changes.json')['changes'] if c['table']=='fact_claim'}
support=[]
for item in quoteproof['items']:
 rid=item['person_id'];r=rows['person'][rid];assert r['name']==item['name']
 assert ('person',rid,'description') in pending
 c=rows['fact_claim'][item['claim_id']];assert c['subject_id']==rid and c['field_path']=='description'
 assert c['note'].split('；核对说明：',1)[0]=='原文：'+item['quotation']
 allowed=[c['note']]
 if c['id'] in active:allowed.append(active[c['id']]['after']['note'])
 support.append(dict(baseline=c,allowed_authorized_notes=allowed,source_url=item['source_url'],quotation=item['quotation'],source_sha256=item['source_sha256']))
 patch('person',rid,'description',profiles[r['name']],'根据原简介对应的既有引用及完整上下文展开人物身份、原有行动和具体年代；不依据当前批次覆盖原有经历，不更改姓名、别名、日期、家庭及状态字段。')
assert len(changes)==21
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-56';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='935年第29—37段涉及的21位人物原简介，依据各自早年既有引用与原文上下文白话改写，姓名、身份、家庭、年代与原文不变。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,supporting_claims=support,profile_quotation_proof_sha256=sha(P/'935-part04-profile-original-quotation-check.json'),full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
