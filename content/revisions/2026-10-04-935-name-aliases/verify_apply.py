# -*- coding: utf-8 -*-
"""Guarded aliases-only revision; default is read-only, --apply writes two alias arrays."""
import argparse,hashlib,json,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists())
BATCH=ROOT/'content/books/zizhi-tongjian/vol-279/year-0935/part-02'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
def request(path,service=False,data=None):
 key=env['SUPABASE_SERVICE_ROLE_KEY' if service else 'SUPABASE_ANON_KEY'];headers={'apikey':key,'Authorization':'Bearer '+key,'Content-Type':'application/json','Prefer':'return=representation'}
 req=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+path,headers=headers,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,method='PATCH' if data is not None else 'GET')
 for attempt in range(3):
  try:
   with urllib.request.urlopen(req,timeout=40) as response:return json.load(response)
  except (urllib.error.URLError,TimeoutError):
   if attempt==2:raise
   time.sleep(1)
a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args()
b=read(BATCH/'content-batch.json');ids=read(BATCH/'sql/key-map.json');sha=hashlib.sha256((BATCH/'content-batch.json').read_bytes()).hexdigest()
publication=read(BATCH/'publication.json');assert publication['verified'] and publication['batch_sha256']==sha
names=['杨檀','刘延朗'];desired={x['name']:x for x in b['people'] if x['name'] in names};assert set(desired)==set(names)
rows=[]
for name in names:
 person=desired[name];result=request('person?id=eq.'+ids[person['key']]+'&select=id,name,aliases,status');assert len(result)==1
 current=result[0];assert current['status']=='published' and current['name']==name
 claims=[x for x in b['claims'] if x['subject_table']=='person' and x['subject_key']==person['key'] and x['field_path']=='aliases'];assert claims
 for c in claims:
  q=request('fact_claim?id=eq.'+ids[c['key']]+'&select=id,status,subject_table,subject_id,source_id');assert len(q)==1 and q[0]['status']=='published' and q[0]['subject_id']==current['id'] and q[0]['source_id']==ids[c['source_key']]
 rows.append(dict(id=current['id'],key=person['key'],name=name,before=current['aliases'],after=list(dict.fromkeys(current['aliases']+person['aliases'])),claim_ids=[ids[c['key']] for c in claims]))
plan_path=P/'aliases.json'
if plan_path.exists():
 plan=read(plan_path)
 assert plan['batch_sha256']==sha
 for row in rows:
  old=next(x for x in plan['people'] if x['id']==row['id']);assert row['before'] in [old['before'],old['after']],('concurrent aliases changed',row['name'])
else:
 plan=dict(reason='935五月杨檀获赐名光远；刘延郎、刘延朗为同官命异写。只补别名，保规范名、UUID及全部旧引用。',batch=str(BATCH.relative_to(ROOT)),batch_sha256=sha,people=rows);write(plan_path,plan)
if not args.apply:
 print(dict(read_only=True,people=[dict(name=x['name'],before=x['before'],after=x['after']) for x in plan['people']]));raise SystemExit(0)
for row in plan['people']:
 current=request('person?id=eq.'+row['id']+'&select=id,aliases,status')[0];assert current['aliases'] in [row['before'],row['after']] and current['status']=='published'
 if current['aliases']!=row['after']:
  result=request('person?id=eq.'+row['id'],service=True,data=dict(aliases=row['after']));assert len(result)==1 and result[0]['aliases']==row['after']
for row in plan['people']:
 current=request('person?id=eq.'+row['id']+'&select=id,name,aliases,status')[0];assert current['name']==row['name'] and current['aliases']==row['after'] and current['status']=='published'
write(P/'publication.json',dict(verified=True,revision_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),batch_sha256=sha,count=len(plan['people']),verified_at=datetime.now(timezone.utc).isoformat(),method='Guarded aliases-only patch; public evidence claims and anonymous person readback verified'))
print(dict(verified=True,count=len(plan['people']),fields=['aliases']))
