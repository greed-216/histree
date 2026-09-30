"""Merge evidence-backed aliases, default read-only; preserve historical batches."""
import argparse,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('revision');ap.add_argument('--apply',action='store_true');args=ap.parse_args()
p=Path(args.revision).resolve();revision=json.loads(p.read_text())
env=dict(l.strip().split('=',1) for l in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
headers={'apikey':env['SUPABASE_SERVICE_ROLE_KEY'],'Authorization':'Bearer '+env['SUPABASE_SERVICE_ROLE_KEY'],'Content-Type':'application/json','Prefer':'return=representation'}
def request(table,query='',method='GET',body=None):
 r=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+table+'?'+query,headers=headers,method=method,data=None if body is None else json.dumps(body,ensure_ascii=False).encode())
 with urllib.request.urlopen(r,timeout=40) as f:return json.load(f)
for row in revision['people']:
 old=request('person','id=eq.'+row['id']);assert len(old)==1 and old[0]['status']=='published'
 assert old[0]['name']==row['name'] and old[0]['aliases'] in [row['before'],row['after']],row['name']
 assert set(row['before']).issubset(row['after'])
 for cid in row['claim_ids']:
  c=request('fact_claim','id=eq.'+cid);assert len(c)==1 and c[0]['status']=='published' and c[0]['subject_id']==row['id'] and c[0]['field_path']=='aliases'
print('Alias preflight verified:',len(revision['people']),flush=True)
if args.apply:
 for row in revision['people']:
  old=request('person','id=eq.'+row['id'])[0]
  if old['aliases']==row['after']:continue
  assert old['aliases']==row['before']
  body={'aliases':row['after']}
  query='id=eq.'+row['id']+'&aliases=eq.'+urllib.parse.quote('{'+','.join(row['before'])+'}')
  updated=request('person',query,'PATCH',body);assert len(updated)==1,row['name']
 headers['apikey']=env['SUPABASE_ANON_KEY'];headers['Authorization']='Bearer '+env['SUPABASE_ANON_KEY']
 for row in revision['people']:
  actual=request('person','id=eq.'+row['id']);assert len(actual)==1 and actual[0]['aliases']==row['after']
 (p.parent/'publication.json').write_text(json.dumps({'verified':True,'revision_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'count':len(revision['people']),'verified_at':datetime.now(timezone.utc).isoformat(),'method':'Guarded alias merge; published claim checks; anonymous readback'},ensure_ascii=False,indent=2)+'\n')
 print('Alias anonymous readback verified')
