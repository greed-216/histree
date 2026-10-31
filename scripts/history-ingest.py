"""Resumable book publication: ready (read-only DB), publish --apply, accept.

Curators author facts once. This command never infers identities or dates.
Source archival stays explicit via archive-history-sources.py. Progress moves
only after publisher, sidecars, anonymous annual/reader checks and real UI proof.
"""
import argparse, concurrent.futures, hashlib, importlib.util, json, os, sys, urllib.parse, urllib.request, uuid
from pathlib import Path
from datetime import datetime, timezone
from history_ingest_preflight import StageRunner, _write_json, timing_summary
TOOL_ROOT=Path(__file__).resolve().parents[1]
NS=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sid=lambda k:str(uuid.uuid5(NS,k))
FROZEN=['packet.json','curation.json','sources/manifest.json','content-batch.json','coverage.json','paragraphs.json','reused-keys.json','time-review.json','sql/key-map.json','workbench-validation.json']
def binding(batch):
 names=FROZEN+(['table-review.json','.workflow/table-review-validation.json'] if any('\t' in p['text'] for p in load(batch/'packet.json')['paragraphs']) else [])+[str(p.relative_to(batch)) for p in (batch/'sources').rglob('*') if p.is_file() and p.name in ('source.txt','paragraph.json')]
 assert all(batch.resolve() in (batch/n).resolve().parents for n in names),'Frozen path escaped batch'
 return {n:sha(batch/n) for n in names}
def script(name):return TOOL_ROOT/'scripts'/name
def engines():return [script(n) for n in ['history-ingest.py','history_ingest_preflight.py','history-batch-workbench.py','history_sidecars.py','history-table-review.py','mysql_connection.py','history_identity.py','history_cross_supplements.py','reuse-history-sources.py','archive-history-sources.py','publish-book-batch.py','mysql_content_store.py','source_texts.py','validate-content-batch.py','validate-history-time.py','prepare-book-import.py','prepare-content-import.py','project-review-coverage.py','upgrade-content-structure.mjs','mysql-publication-target.mjs']]
def get(base,path):
 with urllib.request.urlopen(base.rstrip('/')+path,timeout=40) as r:return json.load(r)
def run(args,batch,name,command,inputs=(),outputs=(),kind='mechanical'):
 receipt=StageRunner(batch/'.workflow/stages').run(name,[str(x) for x in command],inputs=inputs,outputs=outputs,engines=engines(),category='publication',kind=kind,allow_apply=args.apply,cwd=args.root)
 print(name,receipt['status'],round(receipt['elapsed_seconds'],3),flush=True)
 return receipt

def ready(args,batch):
 assert not (batch/'publication-mysql.json').exists(),'Started publications cannot be rebuilt'
 source_verification(batch)
 # Local archive reuse is guarded and cannot rewrite prior publications.
 run(args,batch,'source-reuse',[sys.executable,script('reuse-history-sources.py'),batch,'--root',args.root,'--apply-local'],inputs=[batch/'sources/manifest.json',batch/'packet.json'],kind='fresh_acceptance')
 source_verification(batch)
 if any('\t' in p['text'] for p in load(batch/'packet.json')['paragraphs']):
  run(args,batch,'table-review',[sys.executable,script('history-table-review.py'),'check',batch,'--require-publishable','--review',batch/'table-review.json','--output',batch/'.workflow/table-review-validation.json'],inputs=[batch/'packet.json',batch/'curation.json',batch/'table-review.json',batch/'sources'],outputs=[batch/'.workflow/table-review-validation.json'])
 run(args,batch,'editorial',[sys.executable,script('history_ingest_preflight.py'),batch,'--scroll',TOOL_ROOT/'apps/web/src/data/history-scroll.json','--output',batch/'.workflow/editorial-report.json','--fail-on-open'],inputs=[batch/'curation.json',batch/'packet.json',TOOL_ROOT/'apps/web/src/data/history-scroll.json'],outputs=[batch/'.workflow/editorial-report.json'])
 # Registry changes invalidate compilation cache; never cache from directory mtime alone.
 registry=[p for p in (args.root/'content').rglob('content-batch.json') if p.parent!=batch]
 registry+=list((args.root/'content/revisions').glob('*/plan.json'))+list((args.root/'content/revisions').glob('*/publication*.json'))
 source_files=[p for p in (batch/'sources').rglob('*') if p.is_file()]
 run(args,batch,'build',[sys.executable,script('history-batch-workbench.py'),'--root',args.root,'build',batch],inputs=[batch/'curation.json',batch/'packet.json',*source_files,*registry],outputs=[batch/n for n in ['content-batch.json','coverage.json','paragraphs.json','reused-keys.json','workbench-validation.json']])
 run(args,batch,'time-review',[sys.executable,script('validate-history-time.py'),batch/'content-batch.json','--from-curation',batch/'curation.json'],inputs=[batch/'content-batch.json',batch/'curation.json',*source_files],outputs=[batch/'time-review.json'])
 run(args,batch,'volume-audit',[sys.executable,script('history-batch-workbench.py'),'--root',args.root,'audit',batch.parent],inputs=[batch/'packet.json',batch/'curation.json',batch/'content-batch.json',*source_files],outputs=[batch.parent/'volume-audit.json'])
 whole_volume(batch)
 run(args,batch,'prepare-import',[sys.executable,script('prepare-book-import.py'),batch/'content-batch.json'],inputs=[batch/'content-batch.json',batch/'reused-keys.json'],outputs=[batch/'sql/key-map.json'])
 online_check(args,batch)
 run(args,batch,'mysql-preflight',publisher(args,batch),kind='fresh_acceptance')
 make_samples(batch)
 f=dict(format_version=1,target_fingerprint=load(batch/'.workflow/online-check.json')['target_fingerprint'],public_api_url=args.api.rstrip('/'),scroll_sha256=sha(TOOL_ROOT/'apps/web/src/data/history-scroll.json'),files=binding(batch),engines={str(p.relative_to(TOOL_ROOT)):sha(p) for p in engines()},source_verification_sha256=sha(batch/'.workflow/source-url-verification.json'),editorial_sha256=sha(batch/'.workflow/editorial-report.json'),online_check_sha256=sha(batch/'.workflow/online-check.json'),volume_audit_sha256=sha(batch.parent/'volume-audit.json'),web_samples_sha256=sha(batch/'.workflow/web-samples.json'))
 _write_json(batch/'.workflow/freeze.json',f)
 print('READY',sha(batch/'.workflow/freeze.json'))

def source_verification(batch):
    proof=load(batch/'.workflow/source-url-verification.json');assert proof['verified'] is True
    manifest=load(batch/'sources/manifest.json');checks=proof['sources']
    assert len(checks)==len(manifest) and len({c['key'] for c in checks})==len(checks)
    actual={c['key']:c for c in checks}
    for m in manifest:
        c=actual[m['key']];assert c.get('verified') is True and (c['url'],c['sha256'])==(m['url'],m['sha256']),'Source proof differs from manifest'
        path=(batch/'sources'/m['file']).resolve();assert batch.resolve() in path.parents and sha(path)==m['sha256']
    archive=load(batch/'.workflow/source-archive.json')
    assert archive['pushed'] and archive['anonymous_verified']
    assert archive['plan_sha256']==proof['plan_sha256']==sha(batch/'.workflow/source-upload-plan.json')
    assert archive['manifest_after_sha256']==sha(batch/'sources/manifest.json')

def online_check(args,batch):
 from history_identity import audited_hidden_edge
 from mysql_content_store import MysqlContentStore
 import pymysql
 curated=load(batch/'curation.json');reused=set(curated['reused_keys']);issues=[];seen=[]
 store=MysqlContentStore(args.mysql_env)
 try:
  store.connection.rollback()
  with store.connection.cursor() as cursor:cursor.execute('SET TRANSACTION READ ONLY')
  store.connection.begin()
  for group,table in [('people','person'),('events','event'),('person_events','person_event'),('person_relationships','person_relationship')]:
   rows=[i['row'] for i in curated['items'] if i['group']==group];byid={sid(r['key']):r for r in rows};ids=list(byid)
   for start in range(0,len(ids),100):
    live=store.request(table,'id=in.('+','.join(ids[start:start+100])+')')
    for old in live:
     r=byid[old['id']];seen.append(dict(table=table,key=r['key'],row=old))
     if old['status']!='published' or r['key'] not in reused:issues.append(dict(code='existing_key_needs_explicit_reuse',table=table,key=r['key'],live=old))
   fields,local=(['person_id','event_id','role'],['person_key','event_key','role']) if group=='person_events' else (['person_a','person_b','relation_type'],['person_a_key','person_b_key','relation_type']) if group=='person_relationships' else ([],[])
   if not fields:continue
   for start in range(0,len(rows),75):
    chunk=rows[start:start+75];pairs=[[(sid(r[k]) if k.endswith('_key') else r[k]) for k in local] for r in chunk]
    sql='SELECT * FROM `'+table+'` WHERE '+' OR '.join('('+' AND '.join('`'+f+'`=%s' for f in fields)+')' for _ in chunk)
    with store.connection.cursor(pymysql.cursors.DictCursor) as cursor:cursor.execute(sql,[v for pair in pairs for v in pair]);oldrows=[store.normalize(table,r) for r in cursor.fetchall()]
    for r,values in zip(chunk,pairs):
     for old in oldrows:
      if old['id']!=sid(r['key']) and all(old[f]==v for f,v in zip(fields,values)) and not audited_hidden_edge(args.root,store,table,old,sid(r['key'])):issues.append(dict(code='duplicate_edge_endpoints',table=table,key=r['key'],live=old))
  result=dict(ready_to_freeze=not issues,read_only=True,target_fingerprint=store.target_fingerprint,curation_sha256=sha(batch/'curation.json'),issues=issues,matched_canonical_rows=seen)
  _write_json(batch/'.workflow/online-check.json',result)
  assert not issues,'Resolve online-check.json before freezing; no automatic identity merge'
  return result
 finally:store.connection.rollback();store.connection.close()


def whole_volume(batch):
 p=load(batch/'packet.json');audit=load(batch.parent/'volume-audit.json')
 assert audit['full_volume_source_coverage'] and (audit['book_key'],audit['volume'],audit['source_version'])==(p['book_key'],p['volume'],p['source_version'])
 assert audit['paragraphs']==len(p['paragraphs']) and audit['next_paragraph']==p['next_paragraph'],'Pipeline requires one complete-volume batch'
 assert len(audit['batches'])==1,'Multiple batches require aggregate acceptance; this pipeline supports one complete-volume batch'
 item=audit['batches'][0]
 assert item['path']==str(batch.relative_to(batch.parent)) and item['batch_sha256']==sha(batch/'content-batch.json')
 assert item['paragraphs']==[r['id'] for r in p['paragraphs']],'Incomplete volume packet'
 return audit

def publisher(args,batch):return [sys.executable,script('publish-book-batch.py'),batch/'content-batch.json','--source-root',args.root,'--mysql-env',args.mysql_env,'--public-api-url',args.api,'--expected-target-fingerprint',load(batch/'.workflow/online-check.json')['target_fingerprint']]
def frozen(args,batch):
 p=batch/'.workflow/freeze.json';f=load(p)
 assert args.expected_freeze_sha256==sha(p),'Exact reviewed freeze SHA required'
 assert f['public_api_url']==args.api.rstrip('/'),'Frozen public API changed'
 assert f['scroll_sha256']==sha(TOOL_ROOT/'apps/web/src/data/history-scroll.json'),'Frozen period data changed'
 from mysql_content_store import MysqlContentStore
 store=MysqlContentStore(args.mysql_env)
 try:assert store.target_fingerprint==f['target_fingerprint'],'Frozen target database changed'
 finally:store.connection.rollback();store.connection.close()
 assert f['files']==binding(batch),'Frozen batch changed'
 assert all(sha(TOOL_ROOT/n)==h for n,h in f['engines'].items()),'Tool changed after freeze'
 assert f['online_check_sha256']==sha(batch/'.workflow/online-check.json')
 assert f['volume_audit_sha256']==sha(batch.parent/'volume-audit.json') and f['web_samples_sha256']==sha(batch/'.workflow/web-samples.json')
 assert f['source_verification_sha256']==sha(batch/'.workflow/source-url-verification.json') and f['editorial_sha256']==sha(batch/'.workflow/editorial-report.json')
 if f.get('tools_review_file'):
  review=(batch/f['tools_review_file']).resolve();assert batch in review.parents and sha(review)==f['tools_review_sha256']
  evidence=(batch/f['tools_revalidation_file']).resolve();assert batch in evidence.parents and sha(evidence)==f['tools_revalidation_sha256']
 return f


def refresh_tools(args,batch):
 """Revalidate changed tools after verified publication, without rebuilding or importing facts."""
 assert not args.apply and args.tool_review,'Tool refresh is read-only against MySQL and needs an explicit reviewed change list'
 path=batch/'.workflow/freeze.json';oldraw=path.read_bytes();old=load(path)
 assert args.expected_freeze_sha256==sha(path),'Exact prior freeze SHA required'
 assert old['files']==binding(batch),'Published batch or source bytes changed'
 assert old['public_api_url']==args.api.rstrip('/') and old['scroll_sha256']==sha(TOOL_ROOT/'apps/web/src/data/history-scroll.json')
 for field,name in [('source_verification_sha256','.workflow/source-url-verification.json'),('editorial_sha256','.workflow/editorial-report.json'),('online_check_sha256','.workflow/online-check.json'),('web_samples_sha256','.workflow/web-samples.json')]:assert old[field]==sha(batch/name),'Prior acceptance input changed'
 assert old['volume_audit_sha256']==sha(batch.parent/'volume-audit.json');whole_volume(batch);source_verification(batch)
 reviewpath=args.tool_review.resolve();assert batch in reviewpath.parents
 review=load(reviewpath);assert review['previous_freeze_sha256']==args.expected_freeze_sha256 and review['ci_verified'] is True
 current={str(p.relative_to(TOOL_ROOT)):sha(p) for p in engines()}
 assert set(old['engines'])<=set(current),'Tool refresh cannot remove previously protected engines'
 changes={n:(old['engines'].get(n),current.get(n)) for n in set(old['engines'])|set(current) if old['engines'].get(n)!=current.get(n)}
 declared={r['path']:(r['before_sha256'],r['after_sha256']) for r in review['changes']}
 assert changes and declared==changes and len(declared)==len(review['changes']) and all(r['reason'].strip() for r in review['changes']),'Unreviewed tool change'
 sidepaths=[batch/'.workflow'/name for name in ['sidecars-plan.json','sidecars-receipt.json','public-acceptance.json']]
 core_only=not any(p.exists() or p.is_symlink() for p in sidepaths)
 for name in (['publication-mysql.json'] if core_only else ['publication-mysql.json','.workflow/sidecars-receipt.json','.workflow/public-acceptance.json']):
  proof=load(batch/name);assert proof['verified'] and proof['batch_sha256']==sha(batch/'content-batch.json') and proof['target_fingerprint']==old['target_fingerprint'],'Publication is not fully verified'
 b=load(batch/'content-batch.json');published=load(batch/'publication-mysql.json')
 for group,table in [('people','person'),('events','event'),('person_events','person_event'),('person_relationships','person_relationship'),('sources','source'),('claims','fact_claim')]:assert published['public_counts'].get(table)==len(b[group]),'Incomplete anonymous publication counts'
 if not core_only:assert load(batch/'.workflow/public-acceptance.json')['public_api_url']==args.api.rstrip('/')
 from mysql_content_store import MysqlContentStore
 store=MysqlContentStore(args.mysql_env)
 try:assert store.target_fingerprint==old['target_fingerprint'],'Tool refresh cannot change database target'
 finally:store.connection.rollback();store.connection.close()
 run(args,batch,'tools-refresh-mysql-preflight',publisher(args,batch),kind='fresh_acceptance')
 proofpath=batch/'publication-mysql.json';core_sha=sha(proofpath)
 prepared=batch/'.workflow/tools-refresh-sidecars-plan.json'
 sideargs=['--plan',prepared] if core_only else ['--verify-public','--expected-plan-sha256',sha(batch/'.workflow/sidecars-plan.json')]
 run(args,batch,'tools-refresh-sidecars',[sys.executable,script('history_sidecars.py'),batch,'--root',args.root,'--mysql-env',args.mysql_env,'--public-api-url',args.api,*sideargs,'--expected-target-fingerprint',old['target_fingerprint']],kind='fresh_acceptance')
 prepared_sha=sha(prepared) if core_only else None
 evidence=dict(verified=True,read_only=True,previous_freeze_sha256=args.expected_freeze_sha256,batch_sha256=sha(batch/'content-batch.json'),target_fingerprint=old['target_fingerprint'],review_sha256=sha(reviewpath),engines=current,publication_verified=not core_only,core_verified_sidecars_prepared=core_only,sidecar_prepare_sha256=prepared_sha,facts_rebuilt=False,progress_advanced=False)
 record=batch/'.workflow'/('tools-revalidation-'+args.expected_freeze_sha256+'.json');_write_json(record,evidence)
 archive=batch/'.workflow/freezes'/(args.expected_freeze_sha256+'.json');archive.parent.mkdir(exist_ok=True)
 if archive.exists():assert archive.read_bytes()==oldraw
 else:archive.write_bytes(oldraw)
 updated=dict(old,engines=current,previous_freeze_sha256=args.expected_freeze_sha256,tools_review_file=str(reviewpath.relative_to(batch)),tools_review_sha256=sha(reviewpath),tools_revalidation_file=str(record.relative_to(batch)),tools_revalidation_sha256=sha(record))
 assert path.read_bytes()==oldraw and old['files']==binding(batch),'Published input changed during tool revalidation'
 assert current=={str(p.relative_to(TOOL_ROOT)):sha(p) for p in engines()} and sha(reviewpath)==updated['tools_review_sha256'],'Tools or review changed during revalidation'
 if core_only:assert not any(p.exists() or p.is_symlink() for p in sidepaths) and sha(prepared)==prepared_sha and sha(proofpath)==core_sha,'Partial publication changed during read-only revalidation'
 _write_json(path,updated);print('TOOLS REVALIDATED',sha(path))

def publish(args,batch):
 assert args.apply,'publish needs --apply; ready is read-only against MySQL';frozen(args,batch)
 receipt=batch/'publication-mysql.json'
 if not (receipt.exists() and load(receipt).get('verified')):run(args,batch,'mysql-publish',publisher(args,batch)+['--apply'],kind='apply')
 assert load(receipt)['verified'] and load(receipt)['batch_sha256']==sha(batch/'content-batch.json')
 side=batch/'.workflow/sidecars-receipt.json'
 if not (side.exists() and load(side).get('verified')):
  plan=batch/'.workflow/sidecars-plan.json'
  if not plan.exists():run(args,batch,'sidecars-plan',[sys.executable,script('history_sidecars.py'),batch,'--root',args.root,'--mysql-env',args.mysql_env,'--public-api-url',args.api,'--expected-target-fingerprint',load(batch/'.workflow/freeze.json')['target_fingerprint']],kind='fresh_acceptance')
  if side.exists() and load(side).get('committed'):command=['--verify-public']
  else:command=['--apply','--expected-plan-sha256',sha(plan)]
  run(args,batch,'sidecars-apply',[sys.executable,script('history_sidecars.py'),batch,'--root',args.root,'--mysql-env',args.mysql_env,'--public-api-url',args.api,'--expected-target-fingerprint',load(batch/'.workflow/freeze.json')['target_fingerprint'],*command],kind='apply' if '--apply' in command else 'fresh_acceptance')
 anonymous(args,batch)


def make_samples(batch):
 b=load(batch/'content-batch.json');reused=set(load(batch/'reused-keys.json'));rows=[r for r in b['events']+b['people'] if r['key'] not in reused] or b['events']+b['people'];chosen=[]
 if rows:
  for i in [0,len(rows)//2,len(rows)-1]:
   r=rows[i]
   if r['key'] in {x['key'] for x in chosen}:continue
   chosen.append(dict(key=r['key'],id=sid(r['key']),label=r.get('title',r.get('name')),path=('/events/' if 'title' in r else '/people/')+sid(r['key'])))
 if not rows:
  packet=load(batch/'packet.json');ps=packet['paragraphs']
  for i in sorted(set([0,len(ps)//2,len(ps)-1])):
   p=ps[i];chosen.append(dict(key=p['id'],id=p['id'],label=p['section_title'],path='/library/'+packet['book_key']+'/'+p['section_id']+'?paragraph='+p['id']))
 _write_json(batch/'.workflow/web-samples.json',dict(batch_sha256=sha(batch/'content-batch.json'),samples=chosen,reader_only=not bool(rows)))


def anonymous(args,batch):
 frozen(args,batch)
 b=load(batch/'content-batch.json');a=load(batch/'publication-mysql.json');assert a['verified'] and a['batch_sha256']==sha(batch/'content-batch.json')
 assert load(batch/'.workflow/sidecars-receipt.json')['verified'];ids=load(batch/'sql/key-map.json');reused=set(load(batch/'reused-keys.json'));expected={}
 for e in b['events']:
  if e['key'] in reused or e.get('start_year') is None:continue
  for y in {e['start_year'],e.get('end_year') or e['start_year']}:expected.setdefault(y,set()).add(ids[e['key']])
 def check(pair):
  y,want=pair;found=set()
  for page in range(500):
   d=get(args.api,'/timeline?'+urllib.parse.urlencode(dict(year=y,page=page)));found.update(e['id'] for e in d['items'])
   if not d['has_more']:break
  else:raise ValueError('Annual pagination exceeded bound')
  assert want<=found,(y,want-found)
  return dict(year=y,expected=len(want))
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:years=list(pool.map(check,expected.items()))
 packet=load(batch/'packet.json');primary={p['id']:p for p in packet['paragraphs']};manifest={m['key']:m for m in load(batch/'sources/manifest.json')};reader=[]
 candidates=[c for c in b['claims'] if manifest[c['source_key']]['paragraph_id'] in primary]
 if candidates:
  c=candidates[0];pid=manifest[c['source_key']]['paragraph_id'];sec=primary[pid]['section_id'];loc=get(args.api,'/sources/'+ids[c['source_key']]+'/location');assert loc==dict(book_key=packet['book_key'],section_id=sec,paragraph_id=pid)
  found=set()
  for page in range(100):
   d=get(args.api,'/library/'+packet['book_key']+'/sections/'+sec+'/links?'+urllib.parse.urlencode(dict(paragraph=pid,page=page)));found.update(x['claim_id'] for x in d['items'])
   if not d['has_more']:break
  else:raise ValueError('Reader pagination exceeded bound')
  assert ids[c['key']] in found;reader.append(dict(paragraph_id=pid,reverse_claims=len(found)))
 _write_json(batch/'.workflow/public-acceptance.json',dict(verified=True,public_api_url=args.api.rstrip('/'),target_fingerprint=a['target_fingerprint'],batch_sha256=a['batch_sha256'],annual_years=years,new_dated_events=len({x for s in expected.values() for x in s}),reader=reader,checked_at=datetime.now(timezone.utc).isoformat()))
 print('ANONYMOUS ACCEPTED',len(years),'years',flush=True)


def accept(args,batch):
 assert args.apply and args.progress and args.web_proof,'accept needs --apply, explicit --progress and actual --web-proof'
 frozen(args,batch);p=load(batch/'packet.json');a=load(batch/'publication-mysql.json');q=load(batch/'.workflow/public-acceptance.json');side=load(batch/'.workflow/sidecars-receipt.json');ui=load(args.web_proof);samples=load(batch/'.workflow/web-samples.json')
 assert a['target_fingerprint']==q['target_fingerprint']==load(batch/'.workflow/freeze.json')['target_fingerprint']
 assert q['public_api_url']==args.api.rstrip('/'),'Anonymous verification belongs to another API'
 assert all(x.get('verified') for x in [a,q,side,ui]);assert all(x['batch_sha256']==sha(batch/'content-batch.json') for x in [a,q,side,ui,samples]);assert ui.get('quote_expansion_verified') or samples['reader_only'] and ui.get('original_text_visible')
 assert {r['id'] for r in samples['samples']}=={r['id'] for r in ui['observations']},'UI proof sample mismatch'
 assert (ui['book_key'],ui['volume'])==(p['book_key'],p['volume']),'UI proof book/volume mismatch'
 sample_byid={r['id']:r for r in samples['samples']}
 assert len(ui['observations'])==len(sample_byid)
 assert all((r['book_key'],r['volume'],r['path'])==(p['book_key'],p['volume'],sample_byid[r['id']]['path']) for r in ui['observations']),'UI proof path/book/volume mismatch'
 assert all(r['observation'].strip() for r in ui['observations'])
 b=load(batch/'content-batch.json')
 for group,table in [('people','person'),('events','event'),('person_events','person_event'),('person_relationships','person_relationship'),('sources','source'),('claims','fact_claim')]:
  assert a['public_counts'].get(table)==len(b[group]),'Incomplete anonymous publication counts: '+table
 assert side['plan_sha256']==sha(batch/'.workflow/sidecars-plan.json') and side['target_fingerprint']==a['target_fingerprint']
 audit=whole_volume(batch)
 progress_path=args.progress.resolve();assert args.root in progress_path.parents;old=progress_path.read_bytes();progress=json.loads(old)
 assert progress['book_key']==p['book_key'],'Progress belongs to another book'
 if progress['active_cursor']['volume']==p['volume']+1:
  assert progress['active_cursor']['next_paragraph']==p['next_paragraph'] and p['volume'] in progress['completed_volumes']
  assert load(batch.parent/'completion-audit.json')['batch_sha256']==a['batch_sha256'];print('ALREADY ACCEPTED');return
 assert progress['book_key']==p['book_key'] and progress['active_cursor']==dict(volume=p['volume'],next_paragraph=p['paragraphs'][0]['id'])
 ledger=load(batch/'paragraphs.json');pending=[]
 for row in ledger:
  row['editorial_status']=row['status'];row['publication_status']='published_fact_subset_verified' if row['claim_keys'] else 'reviewed_deferred_no_fact_published' if row['status']=='pending_textual_review' else 'reviewed_no_structured_fact_verified';row['status']=row['publication_status'];row['publication_verified']=bool(row['claim_keys']);row['source_archive_verified']=True
  if row['editorial_status']=='pending_textual_review':pending.append(row)
 status='published_fact_subset_verified_with_deferred_material';relative=str(batch.relative_to(args.root));completion=dict(audit,status=status,published=True,publication_verified=True,batch=relative,batch_sha256=a['batch_sha256'],public_counts=a['public_counts'],web_ui_verified=True,source_archive_verified=True,paragraph_ledger=str((batch.parent/'published-paragraphs.json').relative_to(args.root)))
 cp=batch.parent/'completion-audit.json'
 if cp.exists():assert load(cp)==completion,'Existing completion differs'
 else:_write_json(cp,completion)
 _write_json(batch.parent/'published-paragraphs.json',dict(volume=p['volume'],paragraphs=ledger,status=status));_write_json(batch.parent/'deferred-items.json',dict(items=pending))
 coverage(args,batch,completion)
 # Preserve all old book claims; only append this hash-verified batch.
 indexpath=progress_path.parent/'source-index.json';index=load(indexpath);known={r['claim_key']:r for r in index['claims']}
 for c in load(batch/'content-batch.json')['claims']:
  row=dict(claim_key=c['key'],source_key=c['source_key'],subject_table=c['subject_table'],subject_key=c['subject_key'],citation=c['citation'],batch_files=[relative+'/content-batch.json'])
  if c['key'] in known:assert known[c['key']]==row
  known[c['key']]=row
 index['claims']=list(known.values());_write_json(indexpath,index)
 bookindex=progress_path.parent/'index.json';idx=load(bookindex);idx.update(last_reviewed_volume=p['volume'],next_volume=p['volume']+1,next_paragraph=p['next_paragraph'],status='in_progress');_write_json(bookindex,idx)
 progress.update(last_reviewed_volume=p['volume'],last_published_volume=p['volume'],last_reviewed_paragraph=p['paragraphs'][-1]['id'],last_published_paragraph=next((r['paragraph_id'] for r in reversed(ledger) if r['claim_keys']),progress.get('last_published_paragraph')),active_cursor=dict(volume=p['volume']+1,next_paragraph=p['next_paragraph']),completed_volumes=sorted(set(progress['completed_volumes']+[p['volume']])))
 seen={(r['volume'],r['paragraph_id']) for r in progress.get('pending_items',[])};progress.setdefault('pending_items',[]).extend(dict(volume=p['volume'],paragraph_id=r['paragraph_id'],items=r['observations']) for r in pending if (p['volume'],r['paragraph_id']) not in seen)
 assert progress_path.read_bytes()==old,'Book progress changed concurrently';_write_json(progress_path,progress)
 print('ACCEPTED',p['volume'],progress['active_cursor'])


def coverage(args,batch,completion):
 p=load(batch/'packet.json');out=batch/'.workflow';plan=out/'coverage.json';structure=out/'coverage-structure-plan.json'
 run(args,batch,'coverage-project',[sys.executable,script('project-review-coverage.py'),'--source-root',args.root,'--book',p['book_key'],'--volume',p['volume'],'--output',plan],kind='fresh_acceptance')
 rows=load(plan);assert len(rows['coverage'])==1 and rows['coverage'][0]['volume']==p['volume'] and rows['coverage'][0]['book_key']==p['book_key'] and not rows['skipped']
 run(args,batch,'coverage-plan',['node',script('upgrade-content-structure.mjs'),'--mysql-env',args.mysql_env,'--source-root',args.root,'--after','ffffffff-ffff-ffff-ffff-ffffffffffff','--limit','1','--coverage-plan',plan,'--output',structure],kind='fresh_acceptance')
 proposed=load(structure);assert proposed.get('publication_target_fingerprint')==load(batch/'.workflow/freeze.json')['target_fingerprint']
 assert not proposed['claim_structure'] and not proposed['event_dating'] and not proposed['claim_relations'] and proposed['coverage']==rows['coverage']
 run(args,batch,'coverage-apply',['node',script('upgrade-content-structure.mjs'),'--mysql-env',args.mysql_env,'--source-root',args.root,'--apply','--plan',structure,'--expected-sha256',sha(structure)],kind='apply')
 actual=get(args.api,'/library/'+p['book_key']);row=next(r for r in actual['coverage'] if r['volume']==p['volume']);assert all(row[k]==v for k,v in rows['coverage'][0].items())
 _write_json(out/'coverage-receipt.json',dict(verified=True,batch_sha256=completion['batch_sha256'],plan_sha256=sha(structure),reader_reviewed=len(rows['paragraphs'])))


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['ready','publish','verify','accept','refresh-tools','timings','online-check']);ap.add_argument('batch',type=Path);ap.add_argument('--root',type=Path,default=TOOL_ROOT);ap.add_argument('--mysql-env',type=Path);ap.add_argument('--api',default='https://histree.wiki/api/v1');ap.add_argument('--apply',action='store_true');ap.add_argument('--expected-freeze-sha256');ap.add_argument('--progress',type=Path);ap.add_argument('--web-proof',type=Path);ap.add_argument('--tool-review',type=Path);args=ap.parse_args();args.root=args.root.resolve();batch=args.batch.resolve();assert args.root in batch.parents;args.mysql_env=args.mysql_env or args.root/'.env.migration.local'
 if args.command=='ready':ready(args,batch)
 elif args.command=='publish':publish(args,batch)
 elif args.command=='verify':anonymous(args,batch)
 elif args.command=='accept':accept(args,batch)
 elif args.command=='refresh-tools':refresh_tools(args,batch)
 elif args.command=='online-check':online_check(args,batch)
 else:
  rows=[]
  for p in (batch/'.workflow/stages').glob('*/history.jsonl'):rows.extend(json.loads(line) for line in p.read_text().splitlines())
  print(json.dumps(timing_summary(rows),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
