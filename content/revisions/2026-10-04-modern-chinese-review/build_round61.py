# coding: utf-8
"""Review remaining profiles and claim notes for 935 paragraphs 21 through 28."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-60/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
assert read(P/'935-part03-full-quotation-check.json')['count']==134
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-03';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json')
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
pending={(x['table'],x['id'],x['field']) for x in ledger if x['status']=='pending'}
changes={};unchanged=[]
def patch(table,rid,field,new,review):
 base=rows[table][rid];old=base[field]
 if old==new:unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,baseline=base,before={},after={},review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=new
profiles=read(P/'profiles-935-part03.json')['profiles']
quoteproof=read(P/'935-part03-profile-original-quotation-check.json');assert quoteproof['verified'] and quoteproof['count']==3
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
notes={
'claim_zztj_279_0935_03_0007':'王继鹏向陈皇后请求得到李春燕；陈皇后随后转告王延钧。这里只说明请求和转告，不能把赐予宫人写成正式册立妃嫔。',
'claim_zztj_279_0935_03_0020':'《资治通鉴》记载，七月刘延皓由枢密使改任天雄节度使；本条没有单独记下任命日期。',
'claim_zztj_279_0935_03_0066':'徐知诰听到有人劝说后，对徐知谔更加优厚。劝说者的身份没有记载，这里不补出具体姓名。',
'claim_zztj_279_0935_03_0070':'九月丙申，吴国实行大赦，并将年号改为天祚；大赦与改元都记在同一日期下。'}
for key,new in notes.items():
 rid=ids[key];c=rows['fact_claim'][rid];assert ('fact_claim',rid,'note') in pending
 patch('fact_claim',rid,'note',c['note'].split('；核对说明：',1)[0]+'；核对说明：'+new,'结合连续原文写清人物指代、行动和时间；逐字引用不变。')
assert len(changes)==7
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-61';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='935年第21—28段剩余3条人物简介和4条事实核对说明；依据原引用与连续上下文白话改写，身份、日期与原文不变。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,supporting_claims=support,profile_quotation_proof_sha256=sha(P/'935-part03-profile-original-quotation-check.json'),full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
