# -*- coding: utf-8 -*-
"""Audit every 933 body paragraph and exact publicly visible evidence, including applied errata."""
import hashlib,http.client,json,subprocess,time,urllib.error,urllib.request
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'scripts/publish-book-batch.py').exists())
read=lambda p:json.loads(p.read_text())
ledger=read(HERE/'paragraphs.json');boundary=read(HERE/'boundaries.json');raw=ROOT/boundary['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==boundary['source_sha256']
assert len(ledger)==57 and [r['source_line'] for r in ledger]==list(range(36,93))
assert all(r['text']==lines[r['source_line']-1] for r in ledger)
body=[r for r in ledger if r.get('kind') not in ('section_heading','separator')];excluded=[r for r in ledger if r not in body]
assert len(body)==56 and [r['source_line'] for r in body]==list(range(36,92))
assert all(r['status']=='published_verified' for r in body)
assert len(excluded)==1 and excluded[0]['text']=='潞王上' and excluded[0]['status']=='excluded_non_body_verified' and not excluded[0]['event_keys']
assert boundary['body_paragraphs']==56 and boundary['body_source_lines']==[36,91]
assert lines[34]=='长兴四年癸巳，公元九三三年' and lines[91:94]==['潞王上','◎','清泰元年甲午，公元九三四年']
for item in boundary['excluded_non_body']:assert item['text']==lines[item['source_line']-1]
groups=[('sources','source'),('people','person'),('events','event'),('person_relationships','person_relationship'),('person_events','person_event'),('claims','fact_claim')]
expected={t:set() for _,t in groups};urls={};claims={};covered=[];batch_hashes={}
rev=ROOT/'content/revisions/2026-10-04-933-era-citation';patch=read(rev/'citations.json');proof=read(rev/'publication.json')
assert proof['verified'] and proof['revision_sha256']==hashlib.sha256((rev/'citations.json').read_bytes()).hexdigest()
corrections={r['id']:r['after'] for r in patch['claims']}
for part in sorted(HERE.glob('part-*')):
 b=read(part/'content-batch.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==sha
 batch_hashes[b['batch_key']]=sha;mapping=read(part/'sql/key-map.json');cov=read(part/'coverage.json');covered+=cov['paragraphs']
 selected=[r for r in body if r['id'] in cov['paragraphs']]
 assert {k for r in selected for k in r['event_keys']}=={r['key'] for r in b['events']}
 assert all(r['batch_key']==b['batch_key'] for r in selected)
 for group,table in groups:expected[table].update(mapping[r['key']] for r in b[group])
 snapshots={r['key']:r for r in read(part/'sources/manifest.json')}
 for s in b['sources']:
  sid=mapping[s['key']]
  assert sid not in urls or urls[sid]==s['url'];urls[sid]=s['url']
  snap=part/'sources'/snapshots[s['key']]['file'];snapsha=snapshots[s['key']]['sha256']
  assert hashlib.sha256(snap.read_bytes()).hexdigest()==snapsha
  commit,path=s['url'].split('/blob/',1)[1].split('/',1)
  assert hashlib.sha256(subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)).hexdigest()==snapsha
 for ctx in cov.get('source_contexts',[]):assert hashlib.sha256((part/'sources'/ctx['file']).read_bytes()).hexdigest()==ctx['sha256']
 main=set(cov['primary_source_keys']);assert {c['key'] for c in b['claims'] if c['source_key'] not in main}=={c['claim_key'] for c in cov['supplements']}
 for c in b['claims']:
  quote=c['note'].removeprefix('原文：').split('；核对说明：',1)[0]
  assert quote and quote in (part/'sources'/snapshots[c['source_key']]['file']).read_text()
  cid=mapping[c['key']];assert cid not in claims
  claims[cid]=(mapping[c['source_key']],corrections.get(cid,c['citation']))
assert len(batch_hashes)==7 and covered==[r['id'] for r in body]
next_scope=[]
for vol,start,end in [(278,95,106),(279,6,82)]:
 dest=HERE.parent.parent/f'vol-{vol}/year-0934';rows=read(dest/'paragraphs.json');bd=read(dest/'boundaries.json');rp=ROOT/bd['source_file'];rl=rp.read_text().splitlines()
 assert hashlib.sha256(rp.read_bytes()).hexdigest()==bd['source_sha256']
 assert bd['body_paragraphs']==end-start+1 and [r['source_line'] for r in rows]==list(range(start,end+1))
 assert all(r['status']=='pending' and not r['event_keys'] and r['text']==rl[r['source_line']-1] for r in rows)
 for item in bd['excluded_non_body']:assert item['text']==rl[item['source_line']-1]
 assert rl[bd['year_header_line']-1]=='清泰元年甲午，公元九三四年'
 next_scope.append(dict(volume=vol,body_paragraphs=len(rows),body_source_lines=[start,end],all_pending=True))
assert sum(r['body_paragraphs'] for r in next_scope)==89
# Only anonymous public reads: checks exact rows, status, source joins, URLs, and applied citation errata.
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
headers={'apikey':env['SUPABASE_ANON_KEY'],'Authorization':'Bearer '+env['SUPABASE_ANON_KEY']};counts={}
for table,ids in expected.items():
 ids=sorted(ids);count=0
 for offset in range(0,len(ids),80):
  chunk=ids[offset:offset+80];query='id=in.('+','.join(chunk)+')&select=id'
  query+=',url' if table=='source' else ',status'
  if table=='fact_claim':query+=',citation,source_id,source:source_id(id,url)'
  req=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+table+'?'+query,headers=headers)
  for attempt in range(3):
   try:
    with urllib.request.urlopen(req,timeout=40) as response:rows=json.load(response)
    break
   except (urllib.error.URLError,TimeoutError,http.client.RemoteDisconnected):
    if attempt==2:raise
    time.sleep(1)
  assert {r['id'] for r in rows}==set(chunk),table
  if table!='source':assert all(r['status']=='published' for r in rows),table
  if table=='source':assert all(r['url']==urls[r['id']] for r in rows)
  if table=='fact_claim':assert all((r['source_id'],r['citation'])==claims[r['id']] and r['source'] and r['source']['id']==r['source_id'] and r['source']['url']==urls[r['source_id']] for r in rows)
  count+=len(rows)
 assert count==len(ids);counts[table]=count;print({'table':table,'verified_rows':count},flush=True)
result=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),year=933,volumes=[278],body_paragraphs=56,ledger_items=57,excluded_ledger_non_body=1,excluded_boundary_structural_items=3,year_complete=True,volume_complete=False,volume_scope=[dict(volume=278,body_paragraphs=56,body_source_lines=[36,91],ledger_items=57,excluded_non_body=1,batches=7)],next_volume=278,next_year=934,next_paragraph='zztj-v278-y0934-p001',next_year_body_paragraphs=89,next_year_scope=next_scope,batch_sha256=batch_hashes,unique_public_counts=counts,anonymous_readback_verified=True,source_snapshot_hashes_verified=True,committed_source_blobs_verified=True,source_context_hashes_verified=True,verbatim_claim_quotes_verified=True,source_urls_match_archives=True,citation_errata_verified=True,scope='all 56 continuous 933 body paragraphs in volume 278, with one retained section heading excluded; pending 934 spans volumes 278 and 279')
(HERE/'year-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result)
