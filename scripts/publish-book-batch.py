"""Publish an audited book-led batch. Default is read-only preflight; --apply writes.
Existing entities are never overwritten. REST stages are resumable, not transactional.
"""
import argparse,hashlib,json,subprocess,sys,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from history_identity import merged_identity_target
from history_cross_supplements import validate_cross_supplement
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('batch');ap.add_argument('--apply',action='store_true');args=ap.parse_args()
P=Path(args.batch).resolve().parent
subprocess.run([sys.executable,str(ROOT/'scripts/validate-content-batch.py'),str(P/'content-batch.json')],check=True,stdout=subprocess.DEVNULL)
batch=json.loads((P/'content-batch.json').read_text());coverage=json.loads((P/'coverage.json').read_text())
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
env=dict(l.strip().split('=',1) for l in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
headers={'apikey':env['SUPABASE_SERVICE_ROLE_KEY'],'Authorization':'Bearer '+env['SUPABASE_SERVICE_ROLE_KEY'],'Content-Type':'application/json','Prefer':'return=representation'}
def req(table,q='',method='GET',body=None):
 r=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+table+'?'+q,headers=headers,method=method,data=None if body is None else json.dumps(body,ensure_ascii=False).encode())
 for attempt in range(3):
  try:
   with urllib.request.urlopen(r,timeout=40) as f:return json.load(f)
  except urllib.error.HTTPError:raise
  except (urllib.error.URLError,TimeoutError):
   if method!='GET' or attempt==2:raise
   time.sleep(1)
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
sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest();auditpath=P/'publication.json'
audit=json.loads(auditpath.read_text()) if auditpath.exists() else {'batch_sha256':sha,'stages':[]}
assert audit['batch_sha256']==sha,'Batch changed after publication started'
def save(stage):
 audit['stages'].append({'stage':stage,'at':datetime.now(timezone.utc).isoformat()});auditpath.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
def query(table):return 'id=in.('+','.join(r['id'] for r in rows[table])+')'
existing={}
for _,table in groups:
 if not rows[table]:existing[table]={};continue
 existing[table]={r['id']:r for r in req(table,query(table))}
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
print(json.dumps(summary,ensure_ascii=False),flush=True)
if not args.apply:raise SystemExit(0)
audit.setdefault('initial_counts',summary);save('preflight_checked')
for _,table in groups:
 missing=[r for r in rows[table] if r['id'] not in existing[table]]
 if missing:req(table,method='POST',body=missing)
 if rows[table]:
  actual={r['id']:r for r in req(table,query(table))};assert len(actual)==len(rows[table])
  for r in rows[table]:
   if r['id'] not in reused:assert all(actual[r['id']].get(k)==v for k,v in r.items() if k!='status'),table
 save('drafts_verified_'+table)
for _,table in groups:
 selected=[r['id'] for r in rows[table] if r['id'] not in reused]
 if table!='source' and selected:
  result=req(table,'id=in.('+','.join(selected)+')','PATCH',{'status':'published'});assert len(result)==len(selected)
 save('published_'+table)
headers['apikey']=env['SUPABASE_ANON_KEY'];headers['Authorization']='Bearer '+env['SUPABASE_ANON_KEY']
counts={}
for _,table in groups:
 if not rows[table]:counts[table]=0;continue
 actual=req(table,query(table)+('&select=*,source:source_id(*)' if table=='fact_claim' else ''))
 assert len(actual)==len(rows[table]),table
 if table!='source':assert all(r['status']=='published' for r in actual)
 if table=='fact_claim':assert all(r['source'] and r['source']['url'].startswith('https://github.com/greed-216/histree/blob/') for r in actual)
 counts[table]=len(actual)
audit['public_counts']=counts;audit['verified']=True;save('anonymous_readback_verified');print('Public readback verified',counts)
