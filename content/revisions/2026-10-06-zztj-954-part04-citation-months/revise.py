# -*- coding: utf-8 -*-
"""Correct only the month label in citations for one immutable published batch."""
import sys,json,hashlib,importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists())
spec=importlib.util.spec_from_file_location('copyreview',ROOT/'scripts/review-public-history-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
client=m.Client();part=ROOT/'content/books/zizhi-tongjian/vol-291/year-0954/part-04';raw=(part/'content-batch.json').read_bytes();b=json.loads(raw);audit=m.read(part/'publication.json');assert audit['verified'] and audit['batch_sha256']==hashlib.sha256(raw).hexdigest()
ids=m.read(part/'sql/key-map.json');claims=[x for x in b['claims'] if x['source_key']=='tongjian-291-954-after-gaoping'];old='954年正月至三月及相关追述';new='954年三月至四月及相关追述'
assert claims and all(old in x['citation'] for x in claims)
mode=sys.argv[1];assert mode in ('preflight','apply')
planfile=P/'plan.json'
if mode=='preflight':
 rows={}
 for start in range(0,len(claims),40):
  keys=[ids[x['key']] for x in claims[start:start+40]]
  rows.update({x['id']:x for x in client.request('fact_claim',{'id':'in.('+','.join(keys)+')','select':'*','limit':1000})})
 changes=[]
 for x in claims:
  rid=ids[x['key']];r=rows[rid];assert r['status']=='published' and r['citation']==x['citation']
  assert r['claim_text']==x['claim_text'] and r['note']==x['note'] and r['source_id']==ids[x['source_key']]
  after=x['citation'].replace(old,new);assert after.split('·')[-2:]==x['citation'].split('·')[-2:]
  changes.append(dict(table='fact_claim',id=rid,key=x['key'],baseline=r,before={'citation':r['citation']},after={'citation':after},review='本批原105—112行覆盖954年三月战后至四月围晋阳，原月份模板仅至三月；只修正月份说明，书卷、段号、行号、来源UUID、逐字摘录和事实内容保留。'))
 m.write(planfile,dict(batch=str(part.relative_to(ROOT)),batch_sha256=audit['batch_sha256'],changes=changes))
else:
 plan=m.read(planfile);assert plan['batch_sha256']==audit['batch_sha256'];changes=plan['changes'];pre=m.read(P/'preflight.json');assert pre['read_only'] and pre['plan_sha256']==hashlib.sha256(planfile.read_bytes()).hexdigest()
for c in changes:
 assert set(c['after'])==set(c['before'])=={'citation'} and c['before']['citation'].replace(old,new)==c['after']['citation']
 assert c['baseline']['id']==c['id'] and c['baseline']['citation']==c['before']['citation']
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda c:m.apply_change(client,c,mode=='apply'),changes))
result=dict(verified=mode=='apply',read_only=mode=='preflight',plan_sha256=hashlib.sha256(planfile.read_bytes()).hexdigest(),count=len(results),anonymous_readback_verified=mode=='apply',protected_fields_unchanged=mode=='apply',results=results)
m.write(P/('publication.json' if mode=='apply' else 'preflight.json'),result);print(mode,len(results),'citation labels', 'verified' if mode=='apply' else 'checked')
