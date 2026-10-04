# coding: utf-8
"""Review exact, already readable note sentences without database writes.

Only note fields are reviewed. Claims, identities and historic conclusions are not
approved by this language review. Anonymous readback must match the full baseline.
"""
import argparse,gzip,json,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
D=P/'round-09';PLAN=D/'review-plan.jsonl.gz'
PATTERNS={
 '按本段原文整理，不补写未载的月日、地点或人物完整生平。':'这句话说明整理范围及不补写未知信息，语义完整，使用现代书面汉语，无人物代称或史书工作简称；保留原值。',
 '参与身份依据本段措辞，不因同场出现推定额外关系。':'这句话明确参与角色取自原文，并避免仅凭同场出现新增关系，现代汉语含义清楚；保留原值。',
 '参与身份依据本段措辞，不因同场出现推定其他关系。':'这句话明确参与角色取自原文，并避免仅凭同场出现新增关系，现代汉语含义清楚；保留原值。',
}
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ledger():
 with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:return [json.loads(line) for line in f]
def build():
 assert not (D/'readback-audit.json').exists(),'Keep verified review plans immutable'
 snap_path=Path('/private/tmp/histree-public-prose-20261004.json');snap=read(snap_path)
 assert sha(snap_path)==read(P/'progress.json')['inventory_sha256']
 rows={r['id']:r for r in snap['tables']['fact_claim']};sources={r['id']:r for r in snap['tables']['source']}
 overlays=[]
 for path in sorted(P.glob('round-*/changes.json')):
  proof=path.with_name('readback-audit.json')
  if not proof.exists():continue
  assert read(proof)['verified'] and read(proof)['plan_sha256']==sha(path)
  overlays.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
  for change in read(path)['changes']:
   if change['table']=='fact_claim':rows[change['id']].update(change['after'])
 pending={x['id'] for x in ledger() if x['table']=='fact_claim' and x['field']=='note' and x['status']=='pending'}
 selected=[]
 for rid in sorted(pending):
  row=rows[rid];note=row['note']
  if not note or not note.startswith('原文：') or '；核对说明：' not in note:continue
  explanation=note.split('；核对说明：',1)[1]
  if explanation in PATTERNS:selected.append(dict(id=rid,baseline=row,source_url=sources[row['source_id']]['url'],explanation=explanation,review=PATTERNS[explanation]))
 meta=dict(format_version=1,at=datetime.now(timezone.utc).isoformat(),read_only=True,scope='仅审阅三个已经清楚的完整核对句式，逐条验证引用和公开行；其他字段仍按各自待审状态处理。',patterns=PATTERNS,records=len(selected),by_pattern=dict(Counter(x['explanation'] for x in selected)),inventory_sha256=sha(snap_path),verified_overlays=overlays,full_goal_complete=False)
 D.mkdir(parents=True,exist_ok=True)
 with gzip.open(PLAN,'wt',encoding='utf-8') as f:
  f.write(json.dumps(dict(meta=meta),ensure_ascii=False,separators=(',',':'))+'\n')
  for x in selected:f.write(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n')
 write(D/'review-summary.json',meta);print(meta['by_pattern'],flush=True)
def verify():
 spec=importlib.util.spec_from_file_location('copy_review',ROOT/'scripts/review-public-history-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);client=m.Client()
 with gzip.open(PLAN,'rt',encoding='utf-8') as f:
  meta=json.loads(next(f))['meta'];expected={r['id']:r for r in map(json.loads,f)}
 assert meta['records']==len(expected) and meta['read_only']
 for item in expected.values():assert item['explanation'] in PATTERNS and item['baseline']['note'].split('；核对说明：',1)[1]==item['explanation']
 ids=list(expected);chunks=[ids[i:i+80] for i in range(0,len(ids),80)]
 def check(chunk):
  rows=client.request('fact_claim',{'id':'in.('+','.join(chunk)+')','select':'id,subject_table,subject_id,field_path,claim_text,source_id,citation,note,status,source:source_id(id,url)'})
  assert {r['id'] for r in rows}==set(chunk),'Missing or inaccessible public record'
  results=[]
  for row in rows:
   item=expected[row['id']];base=item['baseline']
   assert all(row[k]==v for k,v in base.items()),(row['id'],'current row differs; leave pending for separate review')
   assert row['source'] and row['source']['id']==base['source_id'] and row['source']['url']==item['source_url']
   assert m.quote(row['note'])==m.quote(base['note'])
   results.append(dict(id=row['id'],note_sha256=digest(row['note']),quote_sha256=digest(m.quote(row['note'])),source_id=row['source_id'],source_url_sha256=digest(row['source']['url'])))
  return results
 results=[];errors=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  jobs={pool.submit(check,c):c for c in chunks}
  for job in as_completed(jobs):
   try:results.extend(job.result())
   except Exception as error:errors.append(dict(ids=jobs[job],error=str(error)))
   write(D/'running-readback.json',dict(read_only=True,plan_sha256=sha(PLAN),checked=len(results),errors=errors))
   if len(results)%800==0:print('Read back',len(results),'of',len(ids),flush=True)
 assert not errors,errors
 assert {r['id'] for r in results}==set(expected)
 results.sort(key=lambda x:x['id'])
 proof=dict(verified=True,read_only=True,at=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(PLAN),count=len(results),exact_notes_unchanged=True,verbatim_quotes_unchanged=True,source_urls_and_all_baseline_fields_unchanged=True,reviewed_field='fact_claim.note',database_writes=0,full_goal_complete=False,results=results)
 write(D/'readback-audit.json',proof)
 fields=ledger();seen=set()
 for field in fields:
  if field['table']=='fact_claim' and field['field']=='note' and field['id'] in expected:
   assert field['status']=='pending' or field.get('round')=='round-09'
   field['status']='reviewed_verified';field['round']='round-09';seen.add(field['id'])
 assert seen==set(expected)
 with gzip.open(P/'review-ledger.jsonl.gz','wt',encoding='utf-8') as f:
  for field in fields:f.write(json.dumps(field,ensure_ascii=False,separators=(',',':'))+'\n')
 progress=read(P/'progress.json');assert not any(x['path']=='round-09' for x in progress['rounds'])
 progress['field_counts']=dict(Counter(x['status'] for x in fields));progress['rounds'].append(dict(path='round-09',status='reviewed_verified_read_only',changes=0,reviewed_fields=len(expected),readback_audit_sha256=sha(D/'readback-audit.json')));assert progress['complete'] is False;write(P/'progress.json',progress)
 print('Verified unchanged note fields:',len(expected),'Full-site review remains active.',flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['build','verify']);args=a.parse_args()
 (build if args.mode=='build' else verify)()
