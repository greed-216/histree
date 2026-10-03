# -*- coding: utf-8 -*-
"""Verify all 50 body paragraphs of 931 in volume 277 and their public evidence."""
import hashlib
import http.client
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'scripts/publish-book-batch.py').exists())
years=[HERE]
groups=[('sources','source'),('people','person'),('events','event'),('person_relationships','person_relationship'),('person_events','person_event'),('claims','fact_claim')]
ids_by_table={table:set() for _,table in groups}
sha_by_batch={};all_body=[];sources_by_id={};claims_source={};scope=[]
for year,vol,start,end in [(HERE,277,63,112)]:
 ledger=json.loads((year/'paragraphs.json').read_text())
 body=[r for r in ledger if r.get('kind') not in ('section_heading','separator')]
 raw_path=ROOT/f'resources/derived/tongjian/{vol}.txt'
 lines=raw_path.read_text().splitlines()
 boundaries=json.loads((year/'boundaries.json').read_text())
 assert hashlib.sha256(raw_path.read_bytes()).hexdigest()==boundaries['source_sha256']
 assert [r['source_line'] for r in body]==list(range(start,end+1))
 assert all(r['text']==lines[r['source_line']-1] for r in ledger)
 assert all(r['status']=='published_verified' for r in body)
 excluded=[r for r in ledger if r not in body]
 assert all(r['status']=='excluded_non_body_verified' and not r['event_keys'] for r in excluded)
 assert not excluded
 assert boundaries['body_paragraphs']==len(body)
 for item in boundaries['excluded_non_body']:
  assert item['text']==lines[item['source_line']-1]
 assert lines[61]=='长兴二年辛卯，公元九三一年' and lines[112]=='◎' and lines[113]=='长兴三年壬辰，公元九三二年'
 all_body+=body;covered=[];part_count=0
 for part in sorted(year.glob('part-*')):
  data_path=part/'content-batch.json';batch=json.loads(data_path.read_text());pub=json.loads((part/'publication.json').read_text())
  sha=hashlib.sha256(data_path.read_bytes()).hexdigest()
  assert pub['verified'] and pub['batch_sha256']==sha
  proof=json.loads((part/'readback-audit.json').read_text());assert proof['verified'] and proof['batch_sha256']==sha
  sha_by_batch[batch['batch_key']]=sha
  cov=json.loads((part/'coverage.json').read_text());covered+=cov['paragraphs'];part_count+=1
  assert {k for r in body if r['id'] in cov['paragraphs'] for k in r['event_keys']}=={r['key'] for r in batch['events']}
  assert all(next(r for r in body if r['id']==pid)['batch_key']==batch['batch_key'] for pid in cov['paragraphs'])
  mapping=json.loads((part/'sql/key-map.json').read_text())
  for group,table in groups:ids_by_table[table].update(mapping[r['key']] for r in batch[group])
  for r in batch['sources']:
   sid=mapping[r['key']]
   if sid in sources_by_id:assert sources_by_id[sid]==r['url']
   sources_by_id[sid]=r['url']
  for r in batch['claims']:claims_source[mapping[r['key']]]=mapping[r['source_key']]
  for snapshot in json.loads((part/'sources/manifest.json').read_text()):
   assert hashlib.sha256((part/'sources'/snapshot['file']).read_bytes()).hexdigest()==snapshot['sha256']
  for context in cov.get('source_contexts',[]):assert hashlib.sha256((part/'sources'/context['file']).read_bytes()).hexdigest()==context['sha256']
  snapshot_paths={r['key']:part/'sources'/r['file'] for r in json.loads((part/'sources/manifest.json').read_text())}
  for claim in batch['claims']:
   quote=claim['note'].removeprefix('原文：').split('；核对说明：',1)[0]
   assert quote and quote in snapshot_paths[claim['source_key']].read_text()
  main=set(cov['primary_source_keys'])
  assert {r['key'] for r in batch['claims'] if r['source_key'] not in main}=={r['claim_key'] for r in cov['supplements']}
 assert covered==[r['id'] for r in body]
 scope.append(dict(volume=vol,body_paragraphs=len(body),ledger_items=len(ledger),excluded_non_body=len(excluded),body_source_lines=[start,end],batches=part_count))
assert len(all_body)==50 and len(sha_by_batch)==5
next_year=HERE.parent/'year-0932'
next_ledger=json.loads((next_year/'paragraphs.json').read_text())
next_scope=[]
for dest,vol,start,end,header in [(next_year,277,115,137,114),(HERE.parent.parent/'vol-278/year-0932',278,6,33,5)]:
 ledger=json.loads((dest/'paragraphs.json').read_text());bd=json.loads((dest/'boundaries.json').read_text());raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in ledger]==list(range(start,end+1))
 assert all(r['status']=='pending' and not r['event_keys'] and r['text']==lines[r['source_line']-1] for r in ledger)
 assert lines[header-1]=='长兴三年壬辰，公元九三二年'
 if vol==278:assert lines[33]=='◎' and lines[34]=='长兴四年癸巳，公元九三三年'
 next_scope.append(dict(volume=vol,body_paragraphs=len(ledger),body_source_lines=[start,end],all_pending=True))
assert sum(r['body_paragraphs'] for r in next_scope)==51
assert next_ledger[0]['id']=='zztj-v277-y0932-p001'

env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
headers={'apikey':env['SUPABASE_ANON_KEY'],'Authorization':'Bearer '+env['SUPABASE_ANON_KEY']}
counts={}
for table,row_ids in ids_by_table.items():
 expected=sorted(row_ids);actual={}
 for offset in range(0,len(expected),80):
  chunk=expected[offset:offset+80];query='id=in.('+','.join(chunk)+')&select=id'
  if table!='source':query+=',status'
  if table=='source':query+=',url'
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
  if table=='source':assert all(r['url']==sources_by_id[r['id']] for r in rows)
  if table=='fact_claim':
   assert all(r['source_id']==claims_source[r['id']] and r['source'] and r['source']['id']==r['source_id'] and r['source']['url']==sources_by_id[r['source_id']] for r in rows)
  actual.update((r['id'],r) for r in rows)
 assert len(actual)==len(expected);counts[table]=len(actual)
 print({'table':table,'verified_rows':len(actual)},flush=True)
result=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),year=931,volumes=[277],body_paragraphs=50,ledger_items=50,excluded_ledger_non_body=0,excluded_boundary_structural_items=2,volume_scope=scope,year_complete=True,volume_complete=False,next_volume=277,next_year=932,next_paragraph=next_ledger[0]['id'],next_year_body_paragraphs=51,next_year_scope=next_scope,batch_sha256=sha_by_batch,unique_public_counts=counts,anonymous_readback_verified=True,source_snapshot_hashes_verified=True,source_context_hashes_verified=True,verbatim_claim_quotes_verified=True,source_urls_match_archives=True,scope='all 931 body paragraphs in volume 277, with retrospective and supplementary evidence')
(HERE/'year-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result)
