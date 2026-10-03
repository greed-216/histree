# -*- coding: utf-8 -*-
"""Guarded citation correction, default read-only, exact anonymous readback."""
import argparse,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'apps/api/.env').exists())
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
f=P/'citations.json';rows=json.loads(f.read_text())['claims']
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
headers={'apikey':env['SUPABASE_SERVICE_ROLE_KEY'],'Authorization':'Bearer '+env['SUPABASE_SERVICE_ROLE_KEY'],'Content-Type':'application/json','Prefer':'return=representation'}
def req(query,method='GET',body=None):
 r=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/fact_claim?'+query,headers=headers,method=method,data=None if body is None else json.dumps(body,ensure_ascii=False).encode())
 with urllib.request.urlopen(r,timeout=40) as response:return json.load(response)
for offset in range(0,len(rows),80):
 chunk=rows[offset:offset+80];actual={r['id']:r for r in req('id=in.('+','.join(r['id'] for r in chunk)+')&select=id,citation,status')}
 assert set(actual)=={r['id'] for r in chunk}
 for r in chunk:assert actual[r['id']]['status']=='published' and actual[r['id']]['citation'] in [r['before'],r['after']]
print('Citation preflight verified:',len(rows),flush=True)
if args.apply:
 # Each paragraph uses one identical before/after locator, so patch those IDs together.
 groups={}
 for r in rows:groups.setdefault((r['before'],r['after']),[]).append(r['id'])
 for (before,after),ids in groups.items():
  changed=req('id=in.('+','.join(ids)+')&citation=eq.'+urllib.parse.quote(before),'PATCH',{'citation':after})
 headers['apikey']=env['SUPABASE_ANON_KEY'];headers['Authorization']='Bearer '+env['SUPABASE_ANON_KEY']
 for offset in range(0,len(rows),80):
  chunk=rows[offset:offset+80];actual={r['id']:r for r in req('id=in.('+','.join(r['id'] for r in chunk)+')&select=id,citation,status')}
  assert set(actual)=={r['id'] for r in chunk}
  for r in chunk:assert actual[r['id']]['status']=='published' and actual[r['id']]['citation']==r['after']
 (P/'publication.json').write_text(json.dumps(dict(verified=True,revision_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),count=len(rows),verified_at=datetime.now(timezone.utc).isoformat(),method='Guarded exact citation correction; anonymous exact-ID readback'),ensure_ascii=False,indent=2)+'\n')
 print('Citation anonymous readback verified:',len(rows))
