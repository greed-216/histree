# coding: utf-8
"""Review date explanations, relationship descriptions and source titles for 936 paragraphs 1 through 8."""
import json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path);assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
assert read(P/'round-42/readback-audit.json')['verified'],'Verify preceding updates before constructing fresh baselines'
assert read(P/'part01-full-quotation-check.json')['count']==151
rows={t:{r['id']:r for r in records} for t,records in snap['tables'].items()}
for old_plan in sorted(P.glob('round-*/changes.json')):
 proof=old_plan.with_name('readback-audit.json')
 if not proof.exists():continue
 assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(old_plan)
 for c in read(old_plan)['changes']:rows[c['table']][c['id']].update(c['after'])
part=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-01';batch=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');curated=read(P/'curated-936-part01.json')
events={ids[e['key']]:e['key'].removeprefix('event_zztj_280_0936_') for e in batch['events'] if e['key'].removeprefix('event_zztj_280_0936_') in curated};assert len(events)==len(curated)==30
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
pending={(x['table'],x['id'],x['field']) for x in ledger if x['status']=='pending'}
changes={};unchanged=[]
def patch(table,rid,field,new,review):
 base=rows[table][rid];old=base[field]
 if old==new:unchanged.append(dict(table=table,id=rid,fields=[field],baseline=base,review=review));return
 key=(table,rid)
 if key not in changes:changes[key]=dict(table=table,id=rid,baseline=base,before={},after={},review=review)
 c=changes[key];c['before'][field]=old;c['after'][field]=new
dates={
'前述方案之后久之；确日未载':'提出上述方案一段时间后；具体日期未载',
'936年三月条下；确日未独载':'记在936年三月条下；未单独记载具体日期',
'936年正月条下；确日未独载':'记在936年正月条下；未单独记载具体日期',
'后楼召对及其后；确日未载':'在后楼被召见时及其后；具体日期未载',
'前述夜间问计之后；确日未载':'上述夜间询问对策之后；具体日期未载',
'936年正月癸丑言论之后；闻讯日未载':'936年正月癸丑的谈话之后；石敬瑭听到消息的日期未载',
'936年正月癸卯；补三月官命的前职任命':'936年正月癸卯；这项任命说明了吕琦三月改任官职之前的职务',
'前述变意后一日；确日未载':'李从珂改变主意后的某一天；具体日期未载，“一日”不表示紧接着的第二天',
'936年正月癸丑千春节宴':'936年正月癸丑的千春节宴席',
'任中书期间常态；各次及起止年月未载':'担任中书官职期间的表现；各次行动及任职起止年月未载',
'936年三月条下某夜；确日未载':'记在936年三月条下的某个夜晚；具体日期未载',
'936年三月条下另一夜；确日未载':'记在936年三月条下的另一个夜晚；具体日期未载',
'936年三月条下讨论；所述求和属此前背景':'讨论记在936年三月条下；谈话中提到的求和发生在此前，具体年份未明',
'后楼召对时；确日未载':'在后楼被召见时；具体日期未载',
'936年正月癸卯条下；补当前和议对话职衔':'记在936年正月癸卯条下；这项任命说明了薛文遇在和议谈话中的官职'
}
for original in batch['events']:
 rid=ids[original['key']];base=rows['event'][rid];old=base['time_original']
 if ('event',rid,'time_original') not in pending:continue
 if old in dates:new=dates[old]
 else:
  assert old in ['936年正月丁未','936年正月癸丑','936年三月丁巳','936年三月丙午'],old
  new=old
 patch('event',rid,'time_original',new,'对照本批逐字引用，展开时间说明；保留原年、月及干支日期和未知日期。“一日”指某日，不强定为次日；此前背景仍不指定发生年。')
 if new!=old:changes[('event',rid)]['preserved_original_dates']='原936年、正月、三月及丁未、癸丑、癸卯、丁巳、丙午均原样保留；未载日期仍未知，未换算公历日期；“一日”按原文解释为某一天。'
for original in batch['person_relationships']:
 rid=ids[original['key']];r=rows['person_relationship'][rid]
 if ('person_relationship',rid,'description') not in pending:continue
 assert r['relation_type']=='父亲'
 assert r['description']==rows['person'][r['person_a']]['name']+'是'+rows['person'][r['person_b']]['name']+'的父亲。'
 patch('person_relationship',rid,'description',r['description'],'核读原文明示的子关系，现有说明已完整写明双方姓名与父亲方向；保持现有文案、端点和关系类型。')
for original in batch['sources']:
 rid=ids[original['key']];r=rows['source'][rid]
 if ('source',rid,'title') not in pending:continue
 assert any(r['title'].startswith(book+'·') for book in ['资治通鉴','旧五代史','新五代史'])
 patch('source',rid,'title',r['title'],'出处标题为完整史书名、卷次及篇章或主题定位，含义清楚；保留书目专名，不更改出处URL和底本信息。')
archives=[dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha(part/'content-batch.json'),source_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in sorted((part/'sources').rglob('source.txt'))])]
D=P/'round-43';assert not (D/'publication.json').exists();D.mkdir(parents=True,exist_ok=True)
plan=dict(created_at=datetime.now(timezone.utc).isoformat(),scope='936年第1—8段的时间说明、两条父亲关系说明及出处标题；人物介绍及事实字段另行审阅。',inventory_sha256=sha(snap_path),archives=archives,changes=list(changes.values()),reviewed_unchanged=unchanged,full_goal_complete=False)
(D/'changes.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(changes=len(changes),by_table=dict(Counter(c['table'] for c in changes.values())),changed_fields=sum(len(c['after']) for c in changes.values()),unchanged_fields=len(unchanged)))
