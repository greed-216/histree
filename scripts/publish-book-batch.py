"""Publish an audited book-led batch. Default is read-only preflight; --apply writes.
Existing entities are never overwritten. MySQL chunks are transactional; full batch publication is staged and resumable.
"""
import argparse,concurrent.futures,hashlib,json,subprocess,sys,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from history_identity import merged_identity_target
from history_cross_supplements import validate_cross_supplement
ROOT=Path(__file__).resolve().parents[1];TOOL_ROOT=ROOT
ap=argparse.ArgumentParser();ap.add_argument('batch');ap.add_argument('--source-root',type=Path);ap.add_argument('--apply',action='store_true');ap.add_argument('--expected-target-fingerprint');ap.add_argument('--source-only-evidence',action='store_true');ap.add_argument('--mysql-env',default=str(ROOT/'.env.migration.local'));ap.add_argument('--public-api-url',default='https://123.56.189.146/api/v1');args=ap.parse_args()
if args.source_root:ROOT=args.source_root.resolve()
P=Path(args.batch).resolve().parent
subprocess.run([sys.executable,str(TOOL_ROOT/'scripts/validate-content-batch.py'),str(P/'content-batch.json')],check=True,stdout=subprocess.DEVNULL)
batch=json.loads((P/'content-batch.json').read_text());coverage=json.loads((P/'coverage.json').read_text())
time_review=P/'time-review.json'
prior_paths=[P/'publication-mysql.json',P/'publication.json']
legacy_verified=any(p.exists() and json.loads(p.read_text()).get('verified') and json.loads(p.read_text()).get('batch_sha256')==hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest() for p in prior_paths)
if time_review.exists() or not legacy_verified:
 subprocess.run([sys.executable,str(TOOL_ROOT/'scripts/validate-history-time.py'),str(P/'content-batch.json')],check=True)
if args.source_only_evidence:assert batch['sources'] and not any(batch[k] for k in ('people','events','person_events','person_relationships','claims','topics')), 'Source-only evidence cannot contain fact rows'
assert not batch['topics'], 'Book publisher does not yet publish topics'
source_keys={r['key'] for r in batch['sources']}
primary_keys=set(coverage.get('primary_source_keys',[coverage['primary_source_key']]))
assert coverage['paragraphs'] and primary_keys and coverage['primary_source_key'] in primary_keys
assert primary_keys <= source_keys, 'Missing primary source'
supplements={x['claim_key']:x for x in coverage['supplements']}
assert len(supplements)==len(coverage['supplements']), 'Duplicate supplement mapping'
for c in batch['claims']:
 if c['source_key'] not in primary_keys:
  extra=supplements[c['key']]
  assert extra['subject_key']==c['subject_key']
  if extra['primary_paragraph_id'] not in coverage['paragraphs']:
   validate_cross_supplement(ROOT,extra['primary_paragraph_id'],extra['subject_key'],coverage.get('cross_volume_supplements',[]))
  assert extra['source_book'] and extra['relation'] in ['corroborates','adds','conflicts']
assert set(supplements)=={c['key'] for c in batch['claims'] if c['source_key'] not in primary_keys}, 'Unmatched supplement mapping'
ids=json.loads((P/'sql/key-map.json').read_text());reused={ids[k] for k in json.loads((P/'reused-keys.json').read_text())}
from mysql_content_store import MysqlContentStore,visible
store=MysqlContentStore(args.mysql_env,args.apply,args.public_api_url)
assert not args.expected_target_fingerprint or store.target_fingerprint==args.expected_target_fingerprint, 'Target differs from frozen review'
def req(table,q='',method='GET',body=None):return store.request(table,q,method,body)
def allrows(table,select):
 result=[]
 for offset in range(0,100000,1000):
  page=req(table,f'select={select}&order=id&limit=1000&offset={offset}');result.extend(page)
  if len(page)<1000:return result
 raise RuntimeError('Preflight pagination limit exceeded')
groups=[('sources','source'),('people','person'),('events','event'),('person_relationships','person_relationship'),('person_events','person_event'),('claims','fact_claim')]
rows={}
for group,table in groups:
 rows[table]=[]
 for original in batch[group]:
  r=dict(original);r['id']=ids[r.pop('key')]
  for a,b in {'person_key':'person_id','event_key':'event_id','person_a_key':'person_a','person_b_key':'person_b','subject_key':'subject_id','source_key':'source_id'}.items():
   if a in r:r[b]=ids[r.pop(a)]
  rows[table].append(r)
# Audit must match precisely the reviewed bytes.
sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest();auditpath=P/'publication-mysql.json'
audit=json.loads(auditpath.read_text()) if auditpath.exists() else {'batch_sha256':sha,'stages':[],'source_only_evidence':args.source_only_evidence}
assert bool(audit.get('source_only_evidence'))==args.source_only_evidence,'Source publication mode changed after publication started'
assert audit['batch_sha256']==sha,'Batch changed after publication started'
assert audit.get('target_fingerprint',store.target_fingerprint)==store.target_fingerprint,'Publication target changed'
audit['target_fingerprint']=store.target_fingerprint
audit['backend']='mysql'
def save(stage):
 audit['stages'].append({'stage':stage,'at':datetime.now(timezone.utc).isoformat()});auditpath.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
def selected_rows(table,selected,suffix='',method='GET',body=None):
 result=[]
 for offset in range(0,len(selected),100):
  chunk=selected[offset:offset+100]
  result.extend(req(table,'id=in.('+','.join(chunk)+')'+suffix,method,body))
 return result
def table_rows(table,suffix=''):
 return selected_rows(table,[r['id'] for r in rows[table]],suffix)
existing={}
for _,table in groups:
 if not rows[table]:existing[table]={};continue
 existing[table]={r['id']:r for r in table_rows(table)}
 for r in rows[table]:
  old=existing[table].get(r['id'])
  if r['id'] in reused:assert old and (table=='source' or old['status']=='published'),'Missing/unpublished reused row'
  elif old:assert all(old.get(k)==v for k,v in r.items() if k!='status'),f'Conflicting row: {table}/{r["id"]}'
# Names and aliases flag identity collisions before insertion; endpoints flag duplicate edges.
def norm(s):return s.replace('硃','朱')
# A completed identity merge keeps a hidden historical row. Exempt only its
# audited redirect to the current canonical row; ordinary drafts still collide.
people={x['id']:x for x in allrows('person','id,name,aliases,status')}
redirects={}
current_person_ids={x['id'] for x in rows['person']}
for audit_file in sorted((ROOT/'content/revisions').glob('*/publication.json')):
 merge_audit=json.loads(audit_file.read_text());plan_file=audit_file.parent/'plan.json'
 if merge_audit.get('canonical_person_id') not in current_person_ids or not merge_audit.get('hidden_duplicate_person_id') or not plan_file.exists():continue
 merge_plan=json.loads(plan_file.read_text())
 if merge_audit.get('revision_sha256'):assert merge_audit['revision_sha256']==hashlib.sha256(plan_file.read_bytes()).hexdigest(),'Merge plan changed after verification'
 target=merged_identity_target(merge_plan,merge_audit,people)
 if target:
  duplicate,canonical=target
  assert not req('person_event','person_id=eq.'+duplicate+'&select=id'),'Merged duplicate still has participants'
  assert not req('fact_claim','subject_table=eq.person&subject_id=eq.'+duplicate+'&select=id'),'Merged duplicate still has person claims'
  assert not req('person_relationship','or=(person_a.eq.'+duplicate+',person_b.eq.'+duplicate+')&select=id'),'Merged duplicate still has relations'
  redirects[duplicate]=canonical
for old in people.values():
 oldnames={norm(x) for x in [old['name']]+(old['aliases'] or [])}
 for row in rows['person']:
  assert old['id']==row['id'] or redirects.get(old['id'])==row['id'] or not oldnames.intersection(norm(x) for x in [row['name']]+row.get('aliases',[])), 'Person identity collision: '+row['name']
for table,fields in [('person_relationship',['person_a','person_b','relation_type']),('person_event',['person_id','event_id','role'])]:
 if not rows[table]:continue
 for old in allrows(table,'id,'+','.join(fields)):
  for row in rows[table]:assert old['id']==row['id'] or not all(old[k]==row[k] for k in fields), 'Duplicate edge endpoints'
summary={t:{'new':sum(r['id'] not in existing[t] for r in rs),'reused':sum(r['id'] in reused for r in rs)} for t,rs in rows.items()}
import source_texts
source_text_rows=source_texts.batch_texts(batch,ids,source_only_evidence=args.source_only_evidence)
summary['source_text']=source_texts.preflight(store.connection,source_text_rows,{r['id']:r['url'] for r in rows['source']})
print(json.dumps(summary,ensure_ascii=False),flush=True)
if not args.apply:raise SystemExit(0)
assert summary['source_text']['table_exists'], 'Apply the source_text migration before publishing; no data written'
audit.setdefault('initial_counts',summary);save('preflight_checked')
for _,table in groups:
 missing=[r for r in rows[table] if r['id'] not in existing[table]]
 for offset in range(0,len(missing),100):req(table,method='POST',body=missing[offset:offset+100])
 if rows[table]:
  actual={r['id']:r for r in table_rows(table)};assert len(actual)==len(rows[table])
  for r in rows[table]:
   if r['id'] not in reused:assert all(actual[r['id']].get(k)==v for k,v in r.items() if k!='status'),table
 save('drafts_verified_'+table)
try:
 source_texts.insert_texts(store.connection,source_text_rows)
 source_texts.verify_texts(store.connection,source_text_rows)
 store.connection.commit()
except Exception:
 store.connection.rollback();raise
save('source_texts_verified')
for _,table in groups:
 selected=[r['id'] for r in rows[table] if r['id'] not in reused]
 if table!='source' and selected:
  result=selected_rows(table,selected,method='PATCH',body={'status':'published'});assert len(result)==len(selected)
 save('published_'+table)
source_visibility={}
if args.source_only_evidence:
 for row in source_text_rows:
  source_visibility[row['source_id']]=bool(store.read('fact_claim','r.source_id=%s AND '+visible('fact_claim'),[row['source_id']],'id','r.id',1,0))
store.public=True
counts={}
for _,table in groups:
 if not rows[table]:counts[table]=0;continue
 actual=table_rows(table,'&select=*,source:source_id(*)' if table=='fact_claim' else '')
 assert len(actual)==len(rows[table]),table
 if table!='source':assert all(r['status']=='published' for r in actual)
 if table=='fact_claim':assert all(r['source'] and r['source']['url'].startswith('https://github.com/greed-216/histree/blob/') for r in actual)
 counts[table]=len(actual)
def verify_source_text(row):
 with urllib.request.urlopen(args.public_api_url.rstrip('/')+'/sources/'+row['source_id']+'/text',timeout=40) as response:
  raw=response.read()
  empty_unclaimed=args.source_only_evidence and not source_visibility.get(row['source_id'],True) and not raw and response.headers.get('Content-Length')=='0' and response.headers.get('Content-Type') is None
  assert response.status==200 and (response.headers.get_content_type()=='application/json' or empty_unclaimed),'Unexpected source text HTTP response'
  public_text=json.loads(raw) if raw else None
 state=source_texts.verify_public_text(row,public_text,args.source_only_evidence,source_visibility.get(row['source_id'],True))
 return row['source_id'],state
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: text_results=dict(pool.map(verify_source_text,source_text_rows))
assert set(text_results)=={r['source_id'] for r in source_text_rows}
audit['source_text_visibility']=text_results
audit['public_counts']=counts;audit['verified']=True;save('source_archive_verified' if args.source_only_evidence else 'anonymous_readback_verified');print('Source archive verified' if args.source_only_evidence else 'Public readback verified',counts)
