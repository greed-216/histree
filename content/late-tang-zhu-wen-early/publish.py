"""Guarded, resumable REST publication. Dry-run unless --apply; credentials stay in env file.
REST operations are not a SQL transaction. New records are inserted as drafts, checked,
then published in dependency order. The audit records every completed stage.
"""
import argparse,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
env=dict(l.strip().split('=',1) for l in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
headers={'apikey':env['SUPABASE_SERVICE_ROLE_KEY'],'Authorization':'Bearer '+env['SUPABASE_SERVICE_ROLE_KEY'],'Content-Type':'application/json'}
def req(table,query='',method='GET',body=None):
 r=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+table+'?'+query,headers={**headers,'Prefer':'return=representation'},method=method,data=None if body is None else json.dumps(body,ensure_ascii=False).encode())
 with urllib.request.urlopen(r,timeout=45) as f:return json.load(f)
batch=json.loads((P/'content-batch.json').read_text());ids=json.loads((P/'sql/key-map.json').read_text())
reused={ids['person_zhu_wen'],ids['person_朱全昱'],ids['relationship_person_朱全昱_person_zhu_wen_兄长']}
groups=[('sources','source'),('people','person'),('events','event'),('person_relationships','person_relationship'),('person_events','person_event'),('claims','fact_claim')]
rows={}
for group,table in groups:
 rows[table]=[]
 for original in batch[group]:
  r=dict(original);r['id']=ids[r.pop('key')]
  for a,b in {'person_key':'person_id','event_key':'event_id','person_a_key':'person_a','person_b_key':'person_b','subject_key':'subject_id','source_key':'source_id'}.items():
   if a in r:r[b]=ids[r.pop(a)]
  rows[table].append(r)
audit_path=P/'publication.json'
audit=json.loads(audit_path.read_text()) if audit_path.exists() else {'batch_sha256':hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest(),'stages':[]}
assert audit['batch_sha256']==hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest(),'Batch changed after audit started'
def save(stage):
 audit['stages'].append(stage);audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
existing={}
for _,table in groups:
 query='id=in.('+','.join(r['id'] for r in rows[table])+')'
 existing[table]={r['id']:r for r in req(table,query)}
 if table=='person':
  allpeople=req('person','select=id,name')
  for r in rows[table]:
   assert not any(p['name']==r['name'] and p['id']!=r['id'] for p in allpeople), 'Name collision: '+r['name']
 if table=='person_relationship':
  relationships=req(table,'select=id,person_a,person_b,relation_type')
  for r in rows[table]:
   assert not any(all(x[k]==r[k] for k in ['person_a','person_b','relation_type']) and x['id']!=r['id'] for x in relationships),'Duplicate relationship endpoints'
 for r in rows[table]:
  old=existing[table].get(r['id'])
  if old and r['id'] not in reused and table!='source':
   assert all(old.get(k)==v for k,v in r.items() if k!='status'),f'Conflicting existing row {table}/{r["id"]}'
zhu=existing['person'][ids['person_zhu_wen']]
patch={k:rows['person'][0][k] for k in ['birth_year','description','biography','era']}
if all(zhu[k]==v for k,v in patch.items()):audit.setdefault('zhu_patch',patch)
else:
 assert zhu['birth_year'] is None and zhu['biography']=='后梁建立者。907年在大梁称帝，912年在宫廷政变中被杀。','Zhu biography changed; review before publishing'
 audit['zhu_before']={k:zhu[k] for k in patch};audit['zhu_patch']=patch
summary={t:{'new':sum(r['id'] not in existing[t] for r in rs),'existing':sum(r['id'] in existing[t] for r in rs)} for t,rs in rows.items()}
print(json.dumps(summary,ensure_ascii=False))
if not args.apply:
 print('Dry run passed; no database writes.');raise SystemExit(0)
save('preflight_checked')
for _,table in groups:
 missing=[r for r in rows[table] if r['id'] not in existing[table]]
 if missing:req(table,'','POST',missing)
 save('drafts_checked_'+table)
# Verify every staged record before publishing. Existing source metadata is preserved.
for _,table in groups:
 actual={r['id']:r for r in req(table,'id=in.('+','.join(r['id'] for r in rows[table])+')')}
 assert len(actual)==len(rows[table])
 for r in rows[table]:
  if table=='source' and r['id'] in existing[table] or r['id'] in reused:continue
  assert all(actual[r['id']].get(k)==v for k,v in r.items() if k!='status'),table
for _,table in groups:
 if table=='source':continue
 selected=[r['id'] for r in rows[table] if r['id'] not in reused]
 if selected:
  changed=req(table,'id=in.('+','.join(selected)+')','PATCH',{'status':'published'});assert len(changed)==len(selected)
 save('published_'+table)
if not all(zhu[k]==v for k,v in patch.items()):
 query='id=eq.'+zhu['id']
 for k in patch:
  query+='&'+k+('=is.null' if zhu[k] is None else '=eq.'+urllib.parse.quote(str(zhu[k]),safe=''))
 changed=req('person',query,'PATCH',patch);assert len(changed)==1,'Concurrent biography update; published new records remain intact'
save('zhu_biography_updated')
# Read as anonymous visitor, including citation joins, to check actual public access.
headers['apikey']=env['SUPABASE_ANON_KEY'];headers['Authorization']='Bearer '+env['SUPABASE_ANON_KEY']
counts={}
for _,table in groups:
 actual=req(table,'id=in.('+','.join(r['id'] for r in rows[table])+')')
 assert len(actual)==len(rows[table]),table
 if table!='source':assert all(r['status']=='published' for r in actual)
 counts[table]=len(actual)
public_zhu=req('person','id=eq.'+zhu['id'])[0]
assert all(public_zhu[k]==v for k,v in patch.items())
claims=req('fact_claim','id=in.('+','.join(r['id'] for r in rows['fact_claim'])+')&select=*,source:source_id(*)')
assert all(c['source'] and c['source']['url'].startswith('https://github.com/') for c in claims)
audit['public_counts']=counts;audit['verified']=True;save('anonymous_readback_verified');print('Published and anonymous readback verified',counts)
