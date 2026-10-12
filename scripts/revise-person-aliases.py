"""Merge evidence-backed aliases, default read-only; preserve historical batches."""
import argparse,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('revision');ap.add_argument('--apply',action='store_true');ap.add_argument('--mysql-env',default=str(ROOT/'.env.migration.local'));ap.add_argument('--public-api-url',default='https://123.56.189.146/api/v1');args=ap.parse_args()
p=Path(args.revision).resolve();revision=json.loads(p.read_text())
from mysql_content_store import MysqlContentStore
store=MysqlContentStore(args.mysql_env,args.apply,args.public_api_url)
def request(table,query='',method='GET',body=None):return store.request(table,query,method,body)
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
  query='id=eq.'+row['id']+'&aliases=eq.'+urllib.parse.quote(json.dumps(row['before'],ensure_ascii=False))
  updated=request('person',query,'PATCH',body);assert len(updated)==1,row['name']
 store.public=True
 for row in revision['people']:
  actual=request('person','id=eq.'+row['id']);assert len(actual)==1 and actual[0]['aliases']==row['after']
 (p.parent/'publication-mysql.json').write_text(json.dumps({'verified':True,'revision_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'count':len(revision['people']),'verified_at':datetime.now(timezone.utc).isoformat(),'method':'Guarded alias merge; published claim checks; anonymous readback'},ensure_ascii=False,indent=2)+'\n')
 print('Alias anonymous readback verified')
