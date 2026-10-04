# -*- coding: utf-8 -*-
"""Read-only by default; guarded patch of one published person's death_year."""
import argparse,hashlib,json,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists());BATCH=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-04'
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
b=read(BATCH/'content-batch.json');ids=read(BATCH/'sql/key-map.json');sha=hashlib.sha256((BATCH/'content-batch.json').read_bytes()).hexdigest();pub=read(BATCH/'publication.json');assert pub['verified'] and pub['batch_sha256']==sha
person=next(x for x in b['people'] if x['name']=='张令昭');pid=ids[person['key']]
rows=request('person?id=eq.'+pid+'&select=id,name,death_year,status');assert len(rows)==1;current=rows[0];assert current['name']=='张令昭' and current['status']=='published' and current['death_year'] in [None,936]
claims=[x for x in b['claims'] if x['subject_table']=='person' and x['subject_key']==person['key'] and x['field_path']=='death_year'];assert len(claims)==1
c=claims[0];evidence=request('fact_claim?id=eq.'+ids[c['key']]+'&select=id,status,subject_id,source_id');assert len(evidence)==1 and evidence[0]['status']=='published' and evidence[0]['subject_id']==pid and evidence[0]['source_id']==ids[c['source_key']]
plan_path=P/'fields.json'
if plan_path.exists():
 plan=read(plan_path);assert plan['batch_sha256']==sha and current['death_year'] in [plan['person']['before'],plan['person']['after']]
else:
 plan=dict(reason='连续第21段与新旧五代史明确张令昭本年被斩，补卒年，保各书行刑日异文。',batch=str(BATCH.relative_to(ROOT)),batch_sha256=sha,person=dict(id=pid,key=person['key'],name='张令昭',field='death_year',before=current['death_year'],after=936,claim_id=ids[c['key']]));write(plan_path,plan)
if not args.apply:
 print(dict(read_only=True,name='张令昭',field='death_year',before=plan['person']['before'],after=936));raise SystemExit(0)
current=request('person?id=eq.'+pid+'&select=id,death_year,status')[0];assert current['status']=='published' and current['death_year'] in [plan['person']['before'],936]
if current['death_year']!=936:
 result=request('person?id=eq.'+pid,data=dict(death_year=936));assert len(result)==1 and result[0]['death_year']==936
current=request('person?id=eq.'+pid+'&select=id,name,death_year,status')[0];assert current['id']==pid and current['name']=='张令昭' and current['death_year']==936 and current['status']=='published'
write(P/'publication.json',dict(verified=True,revision_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),batch_sha256=sha,count=1,verified_at=datetime.now(timezone.utc).isoformat(),method='Guarded death_year-only patch with published fact evidence and anonymous person readback'))
print(dict(verified=True,count=1,fields=['death_year']))
