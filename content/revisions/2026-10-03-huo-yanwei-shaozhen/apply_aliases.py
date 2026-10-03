"""Add attested Huo Yanwei names to the existing person; default is read-only."""
import argparse,json,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent
ROOT=next(p for p in P.parents if (p/'scripts/publish-book-batch.py').exists())
B=ROOT/'content/books/zizhi-tongjian/vol-273/year-0924/part-03'
args=argparse.ArgumentParser();args.add_argument('--apply',action='store_true');a=args.parse_args()
b=json.loads((B/'content-batch.json').read_text());ids=json.loads((B/'sql/key-map.json').read_text())
key='person_霍彦威';pid=ids[key]
claims=[c for c in b['claims'] if c['subject_key']==key and c['field_path']=='aliases']
assert len(claims)==1 and '李绍真' in claims[0]['claim_text']
claim_ids=[ids[c['key']] for c in claims]
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
base=env['SUPABASE_URL']+'/rest/v1/'
def req(table,params,anon=False,method='GET',body=None):
 token=env['SUPABASE_ANON_KEY' if anon else 'SUPABASE_SERVICE_ROLE_KEY']
 headers={'apikey':token,'Authorization':'Bearer '+token,'Content-Type':'application/json','Prefer':'return=representation'}
 r=urllib.request.Request(base+table+'?'+urllib.parse.urlencode(params),headers=headers,method=method,data=None if body is None else json.dumps(body,ensure_ascii=False).encode())
 with urllib.request.urlopen(r,timeout=40) as f:return json.load(f)
old=req('person',{'id':'eq.'+pid})[0];assert old['name']=='霍彦威' and old['status']=='published'
proof=req('fact_claim',{'id':'in.('+','.join(claim_ids)+')','select':'id,status,subject_id,source:source_id(id,url)'},anon=True)
assert len(proof)==len(claim_ids) and all(r['status']=='published' and r['subject_id']==pid and r['source'] for r in proof)
after=list(old['aliases'] or [])
for name in ['霍彥威','李绍真','李紹真']:
 if name not in after:after.append(name)
for offset in range(0,100000,1000):
 rows=req('person',{'select':'id,name,aliases','order':'id','offset':offset,'limit':1000})
 for r in rows:assert r['id']==pid or not set(after).intersection([r['name']]+(r['aliases'] or [])),'Alias collision'
 if len(rows)<1000:break
else:raise RuntimeError('Person pagination limit')
change=dict(reason='通鉴卷273同光二年四月庚辰及旧五代史卷31赐霍彦威李绍真姓名；补赐名与繁体检索字形，同UUID不分裂。',people=[dict(id=pid,name=old['name'],before=old['aliases'] or [],after=after,claim_ids=claim_ids)])
if not a.apply:
 print(change);raise SystemExit(0)
record=P/'aliases.json'
if record.exists():
 prior=json.loads(record.read_text());assert prior['people'][0]['after']==after;change=prior
else:record.write_text(json.dumps(change,ensure_ascii=False,indent=2)+'\n')
req('person',{'id':'eq.'+pid},method='PATCH',body={'aliases':after})
public=req('person',{'id':'eq.'+pid,'select':'id,name,aliases,status'},anon=True);assert len(public)==1 and public[0]['aliases']==after and public[0]['status']=='published'
(P/'publication.json').write_text(json.dumps(dict(verified=True,at=datetime.now(timezone.utc).isoformat(),anonymous_readback=public,claim_ids=claim_ids),ensure_ascii=False,indent=2)+'\n')
print('Huo Yanwei aliases added to original UUID and anonymous readback verified')
