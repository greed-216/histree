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
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert len(ledger)==28 and [r['source_line'] for r in ledger]==list(range(6,34))
assert all(r['text']==lines[r['source_line']-1] for r in ledger)
assert coverage['paragraphs']==[r['id'] for r in ledger[20:28]]
assert {k for r in ledger[20:28] for k in r['event_keys']}=={r['key'] for r in batch['events']}
assert all(r['status'] in ['reviewed','published_verified'] for r in ledger[20:])
assert lines[4]=='长兴三年壬辰，公元九三二年' and lines[33]=='◎' and lines[34]=='长兴四年癸巳，公元九三三年'
assert all(r['status']=='published_verified' for r in ledger[:20])
for name in ['part-01','part-02']:
 prior_batch=P.parent/name
 prior_hash=hashlib.sha256((prior_batch/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  prior=read(prior_batch/f);assert prior['verified'] and prior['batch_sha256']==prior_hash
previous_year=P.parent.parent.parent/'vol-277/year-0932'
pr=read(previous_year/'paragraphs.json');pb=read(previous_year/'boundaries.json');pf=ROOT/pb['source_file'];pl=pf.read_text().splitlines()
assert len(pr)==23 and pb['body_paragraphs']==21 and all(r['status']=='published_verified' for r in pr[:21])
assert all(r['status']=='excluded_non_body_verified' and not r['text'].strip() and not r['event_keys'] for r in pr[21:])
assert [r['source_line'] for r in pr]==list(range(115,138)) and all(r['text']==pl[r['source_line']-1] for r in pr)
assert hashlib.sha256(pf.read_bytes()).hexdigest()==pb['source_sha256']
for name in ['part-01','part-02','part-03']:
 prior=previous_year/name;prior_sha=hashlib.sha256((prior/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(prior/f);assert d['verified'] and d['batch_sha256']==prior_sha
pa=read(previous_year/'progress-audit.json');assert pa['continuous_prefix_verified'] and pa['volume_year_complete'] and pa['year_total_paragraphs']==49
for s in read(P/'sources/manifest.json'):
 assert hashlib.sha256((P/'sources'/s['file']).read_bytes()).hexdigest()==s['sha256']
for context in coverage.get('source_contexts',[]):
 assert hashlib.sha256((P/'sources'/context['file']).read_bytes()).hexdigest()==context['sha256']
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
result=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),batch_sha256=sha,body_paragraphs=8,source_lines=[26,33],source_snapshot_hashes_verified=True,source_context_hashes_verified=True,anonymous_readback_verified=True,source_urls_match_archives=True,public_counts=counts,year_complete=False,next_paragraph='zztj-v278-y0933-p001',excluded_non_body_verified=0,volume_year_complete=True)
(P/'readback-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result)
