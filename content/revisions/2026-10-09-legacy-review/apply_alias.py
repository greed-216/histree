"""Publish dedicated alias evidence, then guard the canonical alias array; default read-only."""
import argparse, hashlib, json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone
P=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--env-file',type=Path,required=True);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
env={}
for line in args.env_file.read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1)
  if k in ('SUPABASE_URL','SUPABASE_ANON_KEY','SUPABASE_SERVICE_ROLE_KEY'):env[k]=v
plan=json.loads((P/'alias-plan.json').read_text());baseline=plan['person_baseline'];wanted=dict(plan['alias_claim'],status='published')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,obj):(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def request(table,query,method='GET',body=None,service=False):
 key=env['SUPABASE_SERVICE_ROLE_KEY' if service else 'SUPABASE_ANON_KEY']
 url=env['SUPABASE_URL']+'/rest/v1/'+table+'?'+urllib.parse.urlencode(query,safe=',().:*')
 req=urllib.request.Request(url,headers={'apikey':key,'Authorization':'Bearer '+key,'Content-Type':'application/json','Prefer':'return=representation'},method=method,data=None if body is None else json.dumps(body,ensure_ascii=False).encode())
 # Never retry uncertain writes; read the exact ID before deciding what remains.
 for attempt in range(4 if method=='GET' else 1):
  try:
   with urllib.request.urlopen(req,timeout=45) as response:return json.load(response)
  except (urllib.error.URLError,TimeoutError):
   if method!='GET' or attempt==3:raise
   time.sleep(1)
def get(table,rid,service=False):
 rows=request(table,{'id':'eq.'+rid,'select':'*'},service=service);assert len(rows)<=1;return rows[0] if rows else None
def check_claim(row):
 assert row and all(row[k]==v for k,v in wanted.items() if k!='status') and row['status'] in ('draft','published'),'Conflicting alias claim'
def inspect():
 current=get('person',baseline['id']);assert current and current['status']=='published' and current['aliases'] in (plan['before'],plan['after'])
 assert all(current[k]==v for k,v in baseline.items() if k not in ('aliases','updated_at')),'Protected person field changed'
 support=get('fact_claim',plan['support_claim_id']);assert support and support['status']=='published' and support['source_id']==wanted['source_id']
 assert support['note'].split('；核对说明：',1)[0]==wanted['note'].split('；核对说明：',1)[0]
 source=get('source',wanted['source_id']);assert source and source['url']==plan['support_source_url']
 collision=request('person',{'or':'(name.in.(钱元瓘,錢元瓘),aliases.ov.{钱元瓘,錢元瓘})','select':'id,name,aliases','limit':1000})
 assert all(x['id']==baseline['id'] for x in collision),'Alias matches another person'
 claim=get('fact_claim',wanted['id'],True)
 if claim:check_claim(claim)
 return current,claim
current,claim=inspect();plan_sha=digest(P/'alias-plan.json')
if not args.apply:
 write('alias-preflight.json',{'read_only':True,'plan_sha256':plan_sha,'old_aliases_matched':True,'dedicated_claim_exists':bool(claim),'existing_source_verified':True,'no_alias_collision':True,'online_writes':0});print('Read-only alias preflight passed');raise SystemExit(0)
pre=json.loads((P/'alias-preflight.json').read_text());assert pre['read_only'] and pre['plan_sha256']==plan_sha
stages=[]
def stage(name):
 stages.append(name);write('alias-running-audit.json',{'plan_sha256':plan_sha,'stages':stages})
if not claim:
 try:request('fact_claim',{},'POST',[plan['alias_claim']],True)
 except (urllib.error.URLError,TimeoutError):pass
 claim=get('fact_claim',wanted['id'],True);check_claim(claim)
stage('dedicated_claim_present')
if claim['status']=='draft':
 try:request('fact_claim',{'id':'eq.'+wanted['id'],'status':'eq.draft'},'PATCH',{'status':'published'},True)
 except (urllib.error.URLError,TimeoutError):pass
claim=get('fact_claim',wanted['id']);check_claim(claim);assert claim['status']=='published';stage('dedicated_claim_publicly_verified')
current,_=inspect()
if current['aliases']!=plan['after']:
 array='{'+','.join(plan['before'])+'}'
 try:request('person',{'id':'eq.'+baseline['id'],'name':'eq.'+baseline['name'],'status':'eq.published','aliases':'eq.'+array},'PATCH',{'aliases':plan['after']},True)
 except (urllib.error.URLError,TimeoutError):pass
current,_=inspect();assert current['aliases']==plan['after'];stage('aliases_publicly_verified')
write('alias-publication.json',{'verified':True,'at':datetime.now(timezone.utc).isoformat(),'plan_sha256':plan_sha,'additional_claims_sha256':digest(P/'additional-claims.json'),'person_id':baseline['id'],'claim_id':wanted['id'],'protected_person_fields_unchanged':True,'source_url_and_verbatim_quote_unchanged':True,'anonymous_readback_verified':True,'stages':stages})
print('Verified dedicated alias claim and canonical aliases; original identity and source retained')
