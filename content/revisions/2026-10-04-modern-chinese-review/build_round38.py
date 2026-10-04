# coding: utf-8
"""Curated participation wording for 936 paragraphs 13 through 20."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-37/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-02';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');curated=read(P/'roles-936-part02.json')
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
manual_facts={}
roles={};role_evidence=[]
for original in batch['person_events']:
 rid=ids[original['key']];base=rows['person_event'][rid];new=curated[original['key']];roles[rid]=new
 if ('person_event',rid,'role') in pending:patch('person_event',rid,'role',new,'逐项核读参与引用，写清行动与涉及人物，区分请求、方案、意见和实际行动；人物和事件ID保持原值。')
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if c['subject_table']=='person_event' and c['subject_id'] in roles and c['field_path']=='role':
  participation=rows['person_event'][c['subject_id']];name=rows['person'][participation['person_id']]['name'];role_evidence.append((c,participation,name,roles[c['subject_id']]))
  if ('fact_claim',rid,'claim_text') in pending:patch('fact_claim',rid,'claim_text',name+'：'+roles[c['subject_id']]+'。','对应参与事实展开为该引用所支持的动作；逐字引用、校核说明和出处保持不变。')
for original in batch['claims']:
 rid=ids[original['key']];c=rows['fact_claim'][rid]
 if c['subject_table']=='person' and c['field_path']=='description' and ('fact_claim',rid,'claim_text') in pending:
  if rid in manual_facts:
   patch('fact_claim',rid,'claim_text',manual_facts[rid],'明确书名、人名及原文“弟子”的歧义，不推定为师徒或叔侄关系。')
   continue
  candidates=[x for x in role_evidence if x[1]['person_id']==c['subject_id'] and x[0]['source_id']==c['source_id'] and x[0]['note'].split('；核对说明：',1)[0]==c['note'].split('；核对说明：',1)[0]]
  assert candidates,(c['id'],'Match the same person and exact quotation before expanding a person fact')
  wanted={x[2]+'：'+x[3]+'。' for x in candidates};assert len(wanted)==1
  patch('fact_claim',rid,'claim_text',next(iter(wanted)),'人物事实与参与引用逐字一致并对应同一主体，按该条动作展开；不扩写人物完整生平，不改变引用、身份或关系。')
for original in batch['person_relationships']:
 rid=ids[original['key']];r=rows['person_relationship'][rid]
 a=rows['person'][r['person_a']]['name'];b=rows['person'][r['person_b']]['name']
 new=r['description']
 if r['relation_type']=='从兄':new='按原文“从弟”的记载，石敬瑭是石敬威的同宗兄辈，具体亲属范围仍待核实。'
 else:assert new==a+'是'+b+'的'+r['relation_type']+'。'
 if ('person_relationship',rid,'description') in pending:patch('person_relationship',rid,'description',new,'逐条核读亲属引用，明确双方姓名和关系方向；从兄保留古称范围，解释同宗长幼，不擅定父亲或共同祖先。端点和类型不变。')
 for claim_original in batch['claims']:
  c=rows['fact_claim'][ids[claim_original['key']]]
  if c['subject_table']=='person_relationship' and c['subject_id']==rid and ('fact_claim',c['id'],'claim_text') in pending:
   claim_new=new
   if c['id']==ids['claim_zztj_280_0936_02_0022']:claim_new='《新五代史》记载，马希广是马希范的同母弟弟。'
   else:assert c['claim_text']==r['description']
   patch('fact_claim',c['id'],'claim_text',claim_new,'对应同条亲属引用展开关系说明，保留端点、方向和原文，未载的生母或共同祖先不补出。')
assert len(roles)==len(curated)==51
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-38';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第9—12段待审参与角色、逐字对应人物事实和两条亲属关系说明；逐条核读角色及对应引用，计划、指控与已发生行动分别说明，引用和端点不变。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
