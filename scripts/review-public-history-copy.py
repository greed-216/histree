# coding: utf-8
"""Inventory public prose and apply individually reviewed, guarded copy revisions."""
import argparse,hashlib,json,time,urllib.request,urllib.parse,urllib.error
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
FIELDS={'person':['name','description','biography','historical_evaluation','family','social_relations'],'event':['title','description','time_original','location_note','phases'],'person_relationship':['description'],'person_event':['role'],'event_causality':['description'],'fact_claim':['claim_text','note'],'topic':['title','description','sections'],'source':['title','edition','note']}
EDITABLE={table:set(fields)-({'name'} if table=='person' else set()) for table,fields in FIELDS.items()}
def digest(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def quote(note):return note.split('；核对说明：',1)[0] if note and note.startswith('原文：') else note
class Client:
 def __init__(self):
  self.env=dict(line.split('=',1) for line in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
 def request(self,table,query,payload=None):
  key=self.env['SUPABASE_ANON_KEY' if payload is None else 'SUPABASE_SERVICE_ROLE_KEY']
  url=self.env['SUPABASE_URL']+'/rest/v1/'+table+'?'+urllib.parse.urlencode(query,safe=',().:*')
  headers={'apikey':key,'Authorization':'Bearer '+key,'Content-Type':'application/json','Prefer':'return=representation'}
  req=urllib.request.Request(url,headers=headers,method='GET' if payload is None else 'PATCH',data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode())
  # A failed write is inspected by its caller, never retried blindly.
  attempts=4 if payload is None else 1
  for attempt in range(attempts):
   try:
    with urllib.request.urlopen(req,timeout=45) as response:return json.load(response)
   except (urllib.error.URLError,TimeoutError):
    if attempt+1==attempts:raise
    time.sleep(1)
 def rows(self,table,rows=None,checkpoint=None):
  rows=list(rows or [])
  while True:
   selection='id,subject_table,subject_id,field_path,claim_text,source_id,citation,note,status' if table=='fact_claim' else '*'
   query={'select':selection,'order':'id','limit':1000}
   if rows:query['id']='gt.'+rows[-1]['id']
   chunk=self.request(table,query)
   rows+=chunk
   if checkpoint:checkpoint(rows)
   if table=='fact_claim':print(table,len(rows),flush=True)
   if len(chunk)<1000:return rows

def validate_changes(changes):
 seen=set()
 for c in changes:
  assert c['table'] in EDITABLE and c['id'] and set(c['before'])==set(c['after'])
  assert set(c['after'])<=EDITABLE[c['table']] and c['before']!=c['after']
  assert (c['table'],c['id']) not in seen;seen.add((c['table'],c['id']))
  assert c.get('review'), 'Each change requires its editorial rationale'
  assert c.get('baseline',{}).get('id')==c['id'], 'Authoritative row baseline required'
  assert all(c['baseline'][k]==v for k,v in c['before'].items()), 'Old fields must match the baseline'
  if c['table']=='fact_claim' and 'note' in c['after']:assert quote(c['before']['note'])==quote(c['after']['note']),'verbatim evidence changed'
  if c['table']=='event' and 'time_original' in c['after']:assert c.get('preserved_original_dates'),'Explain preserved chronological tokens'
 return seen

def apply_change(client,c,apply):
 table=c['table'];fields=list(c['after']);rid=c['id']
 rows=client.request(table,{'id':'eq.'+rid,'select':','.join(['id']+fields)})
 assert len(rows)==1,(table,rid,'public row missing')
 current={k:rows[0][k] for k in fields};assert current in [c['before'],c['after']],(table,rid,'concurrent change')
 if apply and current!=c['after']:
  query={'id':'eq.'+rid,'select':','.join(['id']+fields)}
  for k,value in current.items():query[k]='is.null' if value is None else 'eq.'+(json.dumps(value,ensure_ascii=False,separators=(',',':')) if isinstance(value,(list,dict)) else str(value))
  try:result=client.request(table,query,c['after'])
  except (urllib.error.URLError,TimeoutError):
   # An observation failure can follow a successful PATCH. Re-read instead of repeating it.
   rows=client.request(table,{'id':'eq.'+rid,'select':','.join(['id']+fields)})
   assert len(rows)==1 and {k:rows[0][k] for k in fields}==c['after'];result=rows
  assert len(result)==1 and {k:result[0][k] for k in fields}==c['after'],(table,rid,'guard rejected')
 if apply:
  rows=client.request(table,{'id':'eq.'+rid,'select':'*'});row=rows[0]
  assert len(rows)==1 and {k:row[k] for k in fields}==c['after']
  # Full authoritative baseline includes all non-editable IDs, dates, endpoints and source metadata.
  if 'baseline' in c:
   assert all(row[k]==v for k,v in c['baseline'].items() if k not in fields and k not in ['updated_at']), (table,rid,'protected field changed')
 return dict(table=table,id=rid,fields=fields,verified=apply)

def main():
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['snapshot','preflight','apply']);a.add_argument('path',type=Path);a.add_argument('--workers',type=int,default=4);args=a.parse_args();client=Client()
 if args.mode=='snapshot':
  state=read(args.path) if args.path.exists() else dict(at=datetime.now(timezone.utc).isoformat(),scope='Anonymous-visible records at inventory time; embedding vectors excluded',tables={},completed_tables=[])
  for table in FIELDS:
   if table in state['completed_tables']:continue
   def checkpoint(rows):
    state['tables'][table]=rows;write(args.path,state)
   rows=client.rows(table,state['tables'].get(table,[]),checkpoint)
   state['tables'][table]=rows;state['completed_tables'].append(table);write(args.path,state)
   print(table,len(rows),flush=True)
  return
 plan=read(args.path);changes=plan['changes'];validate_changes(changes)
 if args.mode=='apply':
  preflight=read(args.path.with_name('preflight.json'));assert preflight['read_only'] and preflight['plan_sha256']==hashlib.sha256(args.path.read_bytes()).hexdigest(), 'Preflight must match the reviewed plan'
 results=[];errors=[];jobs=iter(changes)
 with ThreadPoolExecutor(max_workers=max(1,min(args.workers,6))) as pool:
  active={}
  def submit():
   c=next(jobs,None)
   if c is not None:active[pool.submit(apply_change,client,c,args.mode=='apply')]=c
  for _ in range(max(1,min(args.workers,6))):submit()
  while active:
   done,_=wait(active,return_when=FIRST_COMPLETED)
   for future in done:
    c=active.pop(future)
    try:results.append(future.result())
    except Exception as error:errors.append(dict(table=c['table'],id=c['id'],error=str(error)))
    if not errors:submit()
   write(args.path.with_name('running-audit.json'),dict(mode=args.mode,plan_sha256=hashlib.sha256(args.path.read_bytes()).hexdigest(),completed=results,errors=errors))
   if len(results)%25==0:print('Checked',len(results),'of',len(changes),flush=True)
 assert not errors,errors
 results.sort(key=lambda r:(r['table'],r['id']))
 out=args.path.with_name('publication.json' if args.mode=='apply' else 'preflight.json')
 write(out,dict(verified=args.mode=='apply',read_only=args.mode!='apply',plan_sha256=hashlib.sha256(args.path.read_bytes()).hexdigest(),at=datetime.now(timezone.utc).isoformat(),count=len(results),anonymous_readback_verified=args.mode=='apply',protected_fields_unchanged=args.mode=='apply',results=results))
 print('Verified' if args.mode=='apply' else 'Read-only preflight passed',len(results),flush=True)
if __name__=='__main__':main()
