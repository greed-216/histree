# -*- coding: utf-8 -*-
"""Verify this batch's exact public IDs and source URLs; never write the database."""
import hashlib
import subprocess
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
assert len(ledger)==12 and [r['source_line'] for r in ledger]==list(range(95,107))
assert all(r['text']==lines[r['source_line']-1] for r in ledger)
assert coverage['paragraphs']==[r['id'] for r in ledger[7:]]
assert {k for r in ledger[7:] for k in r['event_keys']}=={r['key'] for r in batch['events']}
assert all(r['status'] in ['reviewed','published_verified'] for r in ledger[7:])
assert all(r['status']=='published_verified' for r in ledger[:7])
first=P.parent/'part-01';firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
assert lines[91:94]==['潞王上','◎','清泰元年甲午，公元九三四年'] and lines[106:108]==['','']
assert bd['body_paragraphs']==12 and bd['body_source_lines']==[95,106]
previous=P.parent.parent/'year-0933';annual=read(previous/'year-audit.json')
assert annual['verified'] and annual['year_complete'] and annual['body_paragraphs']==56
old_ledger=read(previous/'paragraphs.json');assert all(r['status']=='published_verified' for r in old_ledger[:56]) and old_ledger[56]['status']=='excluded_non_body_verified'
for part in previous.glob('part-*'):
 sha_prior=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 assert annual['batch_sha256'][read(part/'content-batch.json')['batch_key']]==sha_prior
 for f in ['publication.json','readback-audit.json']:
  d=read(part/f);assert d['verified'] and d['batch_sha256']==sha_prior
other=P.parent.parent.parent/'vol-279/year-0934';other_ledger=read(other/'paragraphs.json');other_bd=read(other/'boundaries.json');other_raw=ROOT/other_bd['source_file'];other_lines=other_raw.read_text().splitlines()
assert len(other_ledger)==77 and [r['source_line'] for r in other_ledger]==list(range(6,83))
assert all(r['status']=='pending' and not r['event_keys'] and r['text']==other_lines[r['source_line']-1] for r in other_ledger)
assert hashlib.sha256(other_raw.read_bytes()).hexdigest()==other_bd['source_sha256']
assert len(ledger)+len(other_ledger)==89
snapshots={r['key']:P/'sources'/r['file'] for r in read(P/'sources/manifest.json')}
for c in batch['claims']:
 quote=c['note'].removeprefix('原文：').split('；核对说明：',1)[0];assert quote and quote in snapshots[c['source_key']].read_text()
main=set(coverage['primary_source_keys'])
assert {c['key'] for c in batch['claims'] if c['source_key'] not in main}=={c['claim_key'] for c in coverage['supplements']}
for s in read(P/'sources/manifest.json'):
 assert hashlib.sha256((P/'sources'/s['file']).read_bytes()).hexdigest()==s['sha256']
for source in batch['sources']:
 archive=source['url'].split('/blob/',1)[1];commit,path=archive.split('/',1)
 archived_bytes=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
 assert hashlib.sha256(archived_bytes).hexdigest()==next(x['sha256'] for x in read(P/'sources/manifest.json') if x['key']==source['key'])
for context in coverage.get('source_contexts',[]):
 assert hashlib.sha256((P/'sources'/context['file']).read_bytes()).hexdigest()==context['sha256']
urls={ids[r['key']]:r['url'] for r in batch['sources']}
claim_sources={ids[r['key']]:ids[r['source_key']] for r in batch['claims']}
revision=ROOT/'content/revisions/2026-10-04-933-era-citation'
rev=read(revision/'citations.json');rp=read(revision/'publication.json')
assert rp['verified'] and rp['revision_sha256']==hashlib.sha256((revision/'citations.json').read_bytes()).hexdigest()
corrections={r['id']:r['after'] for r in rev['claims']}
claim_citations={ids[r['key']]:corrections.get(ids[r['key']],r['citation']) for r in batch['claims']}
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
headers={'apikey':env['SUPABASE_ANON_KEY'],'Authorization':'Bearer '+env['SUPABASE_ANON_KEY']}
counts={}
for group,table in [('sources','source'),('people','person'),('events','event'),('person_relationships','person_relationship'),('person_events','person_event'),('claims','fact_claim')]:
 expected=sorted(ids[r['key']] for r in batch[group]);count=0
 for offset in range(0,len(expected),80):
  chunk=expected[offset:offset+80];query='id=in.('+','.join(chunk)+')&select=id'
  query+=',url' if table=='source' else ',status'
  if table=='fact_claim':query+=',citation,source_id,source:source_id(id,url)'
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
  if table=='fact_claim':assert all(r['citation']==claim_citations[r['id']] and r['source_id']==claim_sources[r['id']] and r['source'] and r['source']['id']==r['source_id'] and r['source']['url']==urls[r['source_id']] for r in rows)
  count+=len(rows)
 assert count==len(expected);counts[table]=count
result=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),batch_sha256=sha,body_paragraphs=5,source_lines=[102,106],source_snapshot_hashes_verified=True,committed_source_blobs_verified=True,source_context_hashes_verified=True,anonymous_readback_verified=True,source_urls_match_archives=True,citation_revision_verified=True,public_counts=counts,year_complete=False,next_paragraph='zztj-v279-y0934-p001',excluded_non_body_verified=0,volume_year_complete=True)
(P/'readback-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result)
