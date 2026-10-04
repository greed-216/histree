# -*- coding: utf-8 -*-
"""Read-only plan by default; guard each evidence-backed death-year patch."""
import argparse,hashlib,json,time,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists());BATCH=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-08'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
def request(path,data=None):
 key=env['SUPABASE_SERVICE_ROLE_KEY' if data is not None else 'SUPABASE_ANON_KEY']
 req=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+path,headers={'apikey':key,'Authorization':'Bearer '+key,'Content-Type':'application/json','Prefer':'return=representation'},data=json.dumps(data).encode() if data is not None else None,method='PATCH' if data is not None else 'GET')
 for attempt in range(3):
  try:
   with urllib.request.urlopen(req,timeout=40) as response:return json.load(response)
  except (urllib.error.URLError,TimeoutError):
   if attempt==2:raise
   time.sleep(1)
a=argparse.ArgumentParser();a.add_argument('--apply',action='store_true');args=a.parse_args()
b=read(BATCH/'content-batch.json');ids=read(BATCH/'sql/key-map.json');sha=hashlib.sha256((BATCH/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 audit=read(BATCH/f);assert audit['verified'] and audit['batch_sha256']==sha
updates=[]
for name,target in [('李从珂',936),('曹氏（李嗣源后）',936),('刘氏（李从珂后）',936),('李重美',936),('宋审虔',936),('耶律倍',936),('赵德钧',937)]:
 person=next(x for x in b['people'] if x['name']==name);pid=ids[person['key']]
 rows=request('person?id=eq.'+pid+'&select=id,name,death_year,status');assert len(rows)==1
 current=rows[0];assert current['name']==name and current['status']=='published' and current['death_year'] in [None,target]
 claims=[x for x in b['claims'] if x['subject_table']=='person' and x['subject_key']==person['key'] and x['field_path']=='death_year'];assert len(claims)==1
 c=claims[0];evidence=request('fact_claim?id=eq.'+ids[c['key']]+'&select=id,status,subject_id,source_id');assert len(evidence)==1 and evidence[0]['status']=='published' and evidence[0]['subject_id']==pid and evidence[0]['source_id']==ids[c['source_key']]
 updates.append(dict(id=pid,key=person['key'],name=name,field='death_year',before=current['death_year'],after=target,claim_id=ids[c['key']]))
plan_path=P/'fields.json'
if plan_path.exists():
 plan=read(plan_path);assert plan['batch_sha256']==sha
 assert [(x['id'],x['name'],x['after'],x['claim_id']) for x in plan['people']]==[(x['id'],x['name'],x['after'],x['claim_id']) for x in updates]
else:
 plan=dict(reason='本批明确李从珂、曹后、刘后、重美、宋审虔936自焚，倍936被害；赵德钧卒937据旧天福二年夏。仅补有公开事实支持的卒年，不改日期异说与旧批次。',batch=str(BATCH.relative_to(ROOT)),batch_sha256=sha,people=updates);write(plan_path,plan)
if not args.apply:
 print(dict(read_only=True,updates=[dict(name=x['name'],field=x['field'],before=x['before'],after=x['after']) for x in plan['people']]));raise SystemExit(0)
for row in plan['people']:
 target=row['after']
 current=request('person?id=eq.'+row['id']+'&select=id,name,death_year,status')[0];assert current['status']=='published' and current['name']==row['name'] and current['death_year'] in [row['before'],target]
 if current['death_year']!=target:
  guard='is.null' if row['before'] is None else 'eq.'+str(row['before'])
  result=request('person?id=eq.'+row['id']+'&status=eq.published&death_year='+guard,data=dict(death_year=target));assert len(result)==1 and result[0]['death_year']==target
 current=request('person?id=eq.'+row['id']+'&select=id,name,death_year,status')[0];assert current['id']==row['id'] and current['name']==row['name'] and current['death_year']==target and current['status']=='published'
write(P/'publication.json',dict(verified=True,revision_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),batch_sha256=sha,count=7,verified_at=datetime.now(timezone.utc).isoformat(),method='Published fact evidence, old-value guarded death_year-only patches, and independent anonymous readback'))
print(dict(verified=True,count=7,fields=['death_year']))
