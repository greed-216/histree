# -*- coding: utf-8 -*-
"""Correct uncertain retrospective dates, preserving published archives and verbatim excerpts."""
import argparse,hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
plan=json.loads((P/'plan.json').read_text());ids=json.loads((ROOT/plan['batch']/'sql/key-map.json').read_text())
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
def request(table,uid,method='GET',body=None,anon=False):
 token=env['SUPABASE_ANON_KEY'] if anon else env['SUPABASE_SERVICE_ROLE_KEY']
 req=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+table+'?id=eq.'+uid,method=method,headers={'apikey':token,'Authorization':'Bearer '+token,'Content-Type':'application/json','Prefer':'return=representation'},data=None if body is None else json.dumps(body,ensure_ascii=False).encode())
 with urllib.request.urlopen(req,timeout=40) as f:return json.load(f)
checked=[]
for item in plan['entries']:
 uid=ids[item['key']];rows=request(item['table'],uid);assert len(rows)==1
 if item['table']=='fact_claim':assert rows[0]['status']=='published'
 for k in item['old']:assert rows[0][k] in (item['old'][k],item['new'][k]),(item['key'],k)
 checked.append((item,uid,rows[0]))
if args.apply:
 for item,uid,before in checked:
  row=request(item['table'],uid)[0]
  if any(row[k]!=v for k,v in item['new'].items()):
   result=request(item['table'],uid,'PATCH',item['new']);assert len(result)==1
  rows=request(item['table'],uid,anon=True);assert len(rows)==1 and all(rows[0][k]==v for k,v in item['new'].items())
  assert all(rows[0][k]==v for k,v in before.items() if k not in item['new'] and k!='updated_at'),('unrelated field changed',item['key'])
 (P/'publication.json').write_text(json.dumps(dict(verified=True,anonymous_readback_verified=True,unrelated_fields_preserved=True,plan_sha256=hashlib.sha256((P/'plan.json').read_bytes()).hexdigest(),count=len(checked),entries=[dict(table=i['table'],id=u,fields=i['new']) for i,u,before in checked],at=datetime.now(timezone.utc).isoformat()),ensure_ascii=False,indent=2)+'\n')
print(dict(mode='apply' if args.apply else 'preflight',entries=len(checked)))
