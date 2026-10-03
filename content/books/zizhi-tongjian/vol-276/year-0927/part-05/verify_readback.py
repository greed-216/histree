# -*- coding: utf-8 -*-
"""Verify this batch's exact public IDs and source URLs; never write the database."""
import hashlib
import http.client
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists())
def read(p):return json.loads(p.read_text())
batch=read(P/'content-batch.json');pub=read(P/'publication.json');ids=read(P/'sql/key-map.json')
sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert pub['verified'] and pub['batch_sha256']==sha
ledger=read(P.parent/'paragraphs.json');coverage=read(P/'coverage.json')
raw=ROOT/'resources/derived/tongjian/276.txt';lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==read(P.parent/'boundaries.json')['source_sha256']
assert coverage['paragraphs']==[r['id'] for r in ledger[18:25]]
assert [r['source_line'] for r in ledger[18:25]]==list(range(24,31))
assert all(r['text']==lines[r['source_line']-1] for r in ledger)
assert {k for r in ledger[18:25] for k in r['event_keys']}=={r['key'] for r in batch['events']}
assert all(r['status']=='published_verified' for r in read(ROOT/'content/books/zizhi-tongjian/vol-275/year-0927/paragraphs.json'))
assert len(ledger)==25
assert all(r['status']=='published_verified' for r in ledger[:18])
for s in read(P/'sources/manifest.json'):
 assert hashlib.sha256((P/'sources'/s['file']).read_bytes()).hexdigest()==s['sha256']
urls={ids[r['key']]:r['url'] for r in batch['sources']}
claim_sources={ids[r['key']]:ids[r['source_key']] for r in batch['claims']}
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
headers={'apikey':env['SUPABASE_ANON_KEY'],'Authorization':'Bearer '+env['SUPABASE_ANON_KEY']}
counts={}
for group,table in [('sources','source'),('people','person'),('events','event'),('person_relationships','person_relationship'),('person_events','person_event'),('claims','fact_claim')]:
 expected=sorted(ids[r['key']] for r in batch[group]);count=0
 for offset in range(0,len(expected),80):
  chunk=expected[offset:offset+80];query='id=in.('+','.join(chunk)+')&select=id'
  query+=',url' if table=='source' else ',status'
  if table=='fact_claim':query+=',source_id,source:source_id(id,url)'
  request=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+table+'?'+query,headers=headers)
  for attempt in range(3):
   try:
    with urllib.request.urlopen(request,timeout=40) as response:rows=json.load(response)
    break
   except (urllib.error.URLError,TimeoutError,http.client.RemoteDisconnected):
    if attempt==2:raise
    time.sleep(1)
  assert {r['id'] for r in rows}==set(chunk),table
  if table!='source':assert all(r['status']=='published' for r in rows),table
  if table=='source':assert all(r['url']==urls[r['id']] for r in rows)
  if table=='fact_claim':assert all(r['source_id']==claim_sources[r['id']] and r['source'] and r['source']['id']==r['source_id'] and r['source']['url']==urls[r['source_id']] for r in rows)
  count+=len(rows)
 assert count==len(expected);counts[table]=count
result=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),batch_sha256=sha,body_paragraphs=7,source_lines=[24,30],source_snapshot_hashes_verified=True,anonymous_readback_verified=True,source_urls_match_archives=True,public_counts=counts,year_complete=False,next_paragraph='zztj-v276-y0928-p001')
(P/'readback-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result)
