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
raw=ROOT/'resources/derived/tongjian/277.txt';lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==read(P.parent/'boundaries.json')['source_sha256']
assert coverage['paragraphs']==[r['id'] for r in ledger[15:21]]
assert [r['source_line'] for r in ledger[15:21]]==list(range(130,136))
assert all(r['text']==lines[r['source_line']-1] for r in ledger)
assert {k for r in ledger[15:21] for k in r['event_keys']}=={r['key'] for r in batch['events']}
assert len(ledger)==23 and all(r['status']=='excluded_non_body_verified' and r['kind']=='separator' and not r['text'].strip() and not r['event_keys'] for r in ledger[21:])
assert all(r['status']=='published_verified' for r in ledger[:15])
for name in ['part-01','part-02']:
 prior=P.parent/name
 prior_sha=hashlib.sha256((prior/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(prior/f);assert d['verified'] and d['batch_sha256']==prior_sha
assert [r['source_line'] for r in ledger[21:]]==[136,137]
assert coverage['excluded_non_body']==[dict(paragraph_id=r['id'],source_line=r['source_line'],text=r['text'],reason=r['review']) for r in ledger[21:]]
previous=read(P.parent.parent/'year-0931/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==50
next_volume=P.parent.parent.parent/'vol-278/year-0932'
next_rows=read(next_volume/'paragraphs.json');next_bd=read(next_volume/'boundaries.json');next_raw=ROOT/next_bd['source_file'];next_lines=next_raw.read_text().splitlines()
assert len(next_rows)==28 and all(r['status']=='pending' and not r['event_keys'] for r in next_rows)
assert hashlib.sha256(next_raw.read_bytes()).hexdigest()==next_bd['source_sha256']
assert [r['source_line'] for r in next_rows]==list(range(6,34))
assert all(r['text']==next_lines[r['source_line']-1] for r in next_rows)
assert lines[113]=='长兴三年壬辰，公元九三二年' and next_lines[4]=='长兴三年壬辰，公元九三二年' and next_lines[33]=='◎' and next_lines[34]=='长兴四年癸巳，公元九三三年'

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
result=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),batch_sha256=sha,body_paragraphs=6,source_lines=[130,135],source_snapshot_hashes_verified=True,source_context_hashes_verified=True,anonymous_readback_verified=True,source_urls_match_archives=True,public_counts=counts,year_complete=False,next_paragraph='zztj-v278-y0932-p001',excluded_non_body_verified=2,volume_year_complete=True)
(P/'readback-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result)
