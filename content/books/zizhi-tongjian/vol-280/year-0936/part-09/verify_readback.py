# coding: utf-8
"""Verify every immutable 936 batch and its current public endpoints; read only."""
import hashlib,subprocess,json,time,urllib.request,urllib.error,http.client
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ledger=read(Y/'paragraphs.json');bd=read(Y/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(ledger)==70 and [r['source_line'] for r in ledger]==list(range(6,76))
assert sha(raw)==bd['source_sha256'] and all(r['text']==lines[r['source_line']-1] for r in ledger)
assert lines[4]=='天福元年丙申，公元九三六年' and lines[75:]==['','']
assert all(x['status']=='published_verified' for x in ledger[:53])
assert all(x['status'] in ['reviewed','published_verified'] for x in ledger[53:])
assert bd['body_paragraphs']==70 and bd['body_source_lines']==[6,75]
merge=ROOT/'content/revisions/2026-10-04-zhang-yanqi-name';mp=read(merge/'plan.json');ma=read(merge/'publication.json')
assert ma['verified'] and ma['anonymous_readback_verified'] and ma['revision_sha256']==sha(merge/'plan.json')
canonical={ma['hidden_duplicate_person_id']:ma['canonical_person_id']}
citation_corrections={};relation_corrections={}
for revision in sorted((ROOT/'content/revisions').iterdir()):
 if not (revision/'publication.json').exists():continue
 proof=read(revision/'publication.json')
 if not proof.get('verified'):continue
 if (revision/'citations.json').exists():
  for row in read(revision/'citations.json').get('claims',[]):citation_corrections[row['id']]=row['after']
 if (revision/'relations.json').exists():
  for row in read(revision/'relations.json').get('relations',[]):relation_corrections[row['key']]=row['after']
env=dict(s.split('=',1) for s in (ROOT/'apps/api/.env').read_text().splitlines() if '=' in s and not s.startswith('#'))
headers={'apikey':env['SUPABASE_ANON_KEY'],'Authorization':'Bearer '+env['SUPABASE_ANON_KEY']}
def public(table,query):
 req=urllib.request.Request(env['SUPABASE_URL']+'/rest/v1/'+table+'?'+query,headers=headers)
 for attempt in range(4):
  try:
   with urllib.request.urlopen(req,timeout=40) as res:return json.load(res)
  except (urllib.error.URLError,TimeoutError,http.client.RemoteDisconnected):
   if attempt==3:raise
   time.sleep(1)
seen_sources={};expected={x:{} for x in ['source','person','event','person_event','person_relationship','fact_claim']};proofs=[];all_paragraphs=[];archive_cache={}
for part in sorted(Y.glob('part-*')):
 b=read(part/'content-batch.json');ids=read(part/'sql/key-map.json');pub=read(part/'publication.json');coverage=read(part/'coverage.json');bh=sha(part/'content-batch.json')
 assert pub['verified'] and pub['batch_sha256']==bh
 if part!=P:
  audit=read(part/'readback-audit.json');assert audit['verified'] and audit['batch_sha256']==bh
 all_paragraphs+=coverage['paragraphs'];snaps={s['key']:part/'sources'/s['file'] for s in read(part/'sources/manifest.json')}
 assert {k for r in ledger if r['id'] in coverage['paragraphs'] for k in r['event_keys']}=={e['key'] for e in b['events']}
 assert set(snaps)=={s['key'] for s in b['sources']}
 for s in read(part/'sources/manifest.json'):
  assert sha(snaps[s['key']])==s['sha256']
  ref,path=s['url'].split('/blob/',1)[1].split('/',1);key=(ref,path)
  if key not in archive_cache:archive_cache[key]=hashlib.sha256(subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)).hexdigest()
  assert archive_cache[key]==s['sha256']
 for ctx in coverage.get('source_contexts',[]):
  assert sha(part/'sources'/ctx['file'])==ctx['sha256']
  ref,path=ctx['url'].split('/blob/',1)[1].split('/',1)
  assert hashlib.sha256(subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)).hexdigest()==ctx['sha256']
 for c in b['claims']:
  quote=c['note'].removeprefix('原文：').split('；核对说明：',1)[0];assert quote and quote in snaps[c['source_key']].read_text()
 assert {c['key'] for c in b['claims'] if c['source_key'] not in set(coverage['primary_source_keys'])}=={s['claim_key'] for s in coverage['supplements']}
 for group,table in [('sources','source'),('people','person'),('events','event'),('person_events','person_event'),('person_relationships','person_relationship'),('claims','fact_claim')]:
  for r in b[group]:
   rid=ids[r['key']];rid=canonical.get(rid,rid) if table=='person' else rid
   fields={}
   if table=='source':fields['url']=r['url'];seen_sources[rid]=r['url']
   if table=='person_event':fields=dict(person_id=canonical.get(ids[r['person_key']],ids[r['person_key']]),event_id=ids[r['event_key']])
   if table=='person_relationship':
    correction=relation_corrections.get(r['key'])
    fields=dict(person_a=canonical.get(ids[r['person_a_key']],ids[r['person_a_key']]),person_b=canonical.get(ids[r['person_b_key']],ids[r['person_b_key']]),relation_type=r['relation_type'])
    if correction:fields=dict(person_a=correction['person_a'],person_b=correction['person_b'],relation_type=correction['relation_type'])
   if table=='fact_claim':fields=dict(citation=citation_corrections.get(rid,r['citation']),source_id=ids[r['source_key']],subject_table=r['subject_table'],subject_id=canonical.get(ids[r['subject_key']],ids[r['subject_key']]) if r['subject_table']=='person' else ids[r['subject_key']])
   if rid in expected[table]:assert expected[table][rid]==fields,(table,rid)
   expected[table][rid]=fields
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=bh,paragraphs=len(coverage['paragraphs']),anonymous_readback_verified=True))
assert all_paragraphs==[r['id'] for r in ledger]
assert public('person','id=eq.'+ma['hidden_duplicate_person_id']+'&select=id')==[]
counts={};current_counts={}
for table,records in expected.items():
 ordered=sorted(records);count=0
 fields=['id']+(['url'] if table=='source' else ['status'])
 if table=='person_event':fields+=['person_id','event_id']
 if table=='person_relationship':fields+=['person_a','person_b','relation_type']
 if table=='fact_claim':fields+=['citation','source_id','subject_table','subject_id','source:source_id(id,url)']
 for offset in range(0,len(ordered),80):
  chunk=ordered[offset:offset+80];rows=public(table,'id=in.('+','.join(chunk)+')&select='+','.join(fields))
  assert {r['id'] for r in rows}==set(chunk),(table,offset,len(rows),len(chunk))
  for row in rows:
   if table!='source':assert row['status']=='published',(table,row['id'])
   for k,value in records[row['id']].items():assert row[k]==value,(table,row['id'],k)
   if table=='fact_claim':assert row['source'] and row['source']['id']==row['source_id'] and row['source']['url']==seen_sources[row['source_id']]
  count+=len(rows)
 counts[table]=count
 print(table,count,flush=True)
# Targeted editorial checks prevent role/identity mistakes that counts alone miss.
b=read(P/'content-batch.json');ids=read(P/'sql/key-map.json')
assert len([x for x in b['people'] if x['key'] not in set(read(P/'reused-keys.json'))])==9
for name in ['郑阮','胡章','冯知兆','杜重贵']:
 p=next(x for x in b['people'] if x['name']==name)
 assert public('person','id=eq.'+ids[p['key']]+'&select=name,death_year,status')[0]==dict(name=name,death_year=936,status='published')
for name in ['张延朗','刘延皓','刘延朗','杨汉宾','房知温']:
 p=next(x for x in b['people'] if x['name']==name);row=public('person','id=eq.'+ids[p['key']]+'&select=name,status')[0];assert row==dict(name=name,status='published')
assert next(x for x in b['people'] if x['name']=='王建（高丽）')['key']=='person_王建（高丽）'
assert 'person_董温琪' in [x['person_key'] for x in b['person_events'] if x['event_key']=='event_zztj_280_0936_dong_captured_with_zhao']
assert not any(c['subject_key']=='person_董温琪' and c['field_path']=='death_year' for c in b['claims'])
for group,table in [('sources','source'),('people','person'),('events','event'),('person_events','person_event'),('person_relationships','person_relationship'),('claims','fact_claim')]:current_counts[table]=len(b[group])
result=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),batch_sha256=sha(P/'content-batch.json'),body_paragraphs=17,source_lines=[59,75],source_snapshot_hashes_verified=True,committed_source_blobs_verified=True,source_context_hashes_verified=True,anonymous_readback_verified=True,subject_and_participation_endpoints_verified=True,identity_merge_verified=True,source_urls_match_archives=True,public_counts=current_counts,year_public_counts=counts,all_year_batches_verified=proofs,year_complete=True,year_body_paragraphs=70,continuous_paragraph_coverage_verified=True,next_paragraph='zztj-v281-y0937-p001',volume_year_complete=True)
(P/'readback-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Verified all 70 consecutive paragraphs and all 9 public batches.',flush=True)
