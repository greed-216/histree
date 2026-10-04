# coding: utf-8
"""Curated evidence notes, dates and locations for 936 paragraphs 13 through 20."""
import json,gzip,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-32/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:dict(r) for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-03';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');profiles=read(P/'profiles-936-part03.json')
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
pending={(x['table'],x['id'],x['field']) for x in ledger if x['status']=='pending'}
changes=[];unchanged=[];support=[]
for original in batch['people']:
 rid=ids[original['key']];base=rows['person'][rid]
 if ('person',rid,'description') not in pending:continue
 name=base['name'];old=base['description'];new=profiles[name]
 assert ('person',rid,'description') in pending
 changes.append(dict(table='person',id=rid,baseline=base,before=dict(description=old),after=dict(description=new),review='对照原简介对应的人物事实引用，去掉“本批所见人物”等录入模板并展开动作、姓名和职务；不补写完整生平，不改变人物姓名、身份、日期或家庭关系字段。'))
 candidates=[c for c in snap['tables']['fact_claim'] if c['subject_table']=='person' and c['subject_id']==rid and c['field_path']=='description']
 if '本批' in old:
  role=old.rsplit('，',1)[1][:-1];candidates=[c for c in candidates if c['claim_text'].endswith('：'+role+'。')]
 elif '907年' in old:
  candidates=[c for c in candidates if c['claim_text']==old]
 else:
  match=re.search(r'卷(\d+)(.+?)条',old);assert match
  candidates=[c for c in candidates if '卷'+match[1] in c['citation'] and match[2] in c['citation']]
 assert candidates,(name,'Existing introductory evidence missing')
 claim=rows['fact_claim'][candidates[0]['id']]
 support.append(dict(person_id=rid,claim_id=claim['id'],baseline=claim,review='原简介的既有事实引用，已核读所述姓名、行动及上下文；作为白话改写依据，不增加史实判断。'))
assert len(changes)==len(profiles)==len(support)==20
for original in batch['sources']:
 rid=ids[original['key']];base=rows['source'][rid]
 if ('source',rid,'title') in pending:
  unchanged.append(dict(table='source',id=rid,fields=['title'],baseline=base,review='书名、卷次、纪传及片段标题是出处定位，已经清楚；保留原值，不改来源链接。'))
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-33';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第13—20段涉及的20位人物既有简介改为白话，姓名保持原值；依据各自原简介的既有引用，不扩写完整生平。',inventory_sha256=sha(snap_path),archives=archives,changes=changes,reviewed_unchanged=unchanged,supporting_claims=support,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes)),changed_fields=sum(len(c['after']) for c in changes),unchanged_fields=len(unchanged)))
