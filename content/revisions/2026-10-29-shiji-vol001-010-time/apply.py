# coding: utf-8
"""Bounded exact-plan transaction; default checks old values and performs no writes."""
import json,sys,hashlib,re,urllib.request
from pathlib import Path
import pymysql
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'scripts'))
from mysql_content_store import MysqlContentStore
sha=lambda b:hashlib.sha256(b).hexdigest();P=D/'plan.json';raw=P.read_bytes();plan=json.loads(raw);digest=sha(raw);apply='--apply' in sys.argv
assert plan['kind']=='source_scoped_time_revision' and len(plan['reviews'])==247
if apply:assert '--expected-sha256' in sys.argv and sys.argv[sys.argv.index('--expected-sha256')+1]==digest,'Exact reviewed plan hash required'
for p,h in plan['protected_paths'].items():assert sha((R/p).read_bytes())==h,('Published archive changed',p)
updates=plan['updates'];assert len({(u['table'],u['id']) for u in updates})==len(updates)
allowed_updates={'event':{'start_year','end_year','time_original','description'},'person':{'death_year'}}
for u in updates:
 assert set(u['after'])==set(u['before']) and set(u['after'])<=allowed_updates[u['table']]
 if u['table']=='event' and 'start_year' in u['after']:assert u['before']['start_year'] is None
 if u['table']=='person':assert u['before']['death_year'] is None
for d in plan['event_dating']:
 assert d['review_state']=='reviewed' and d['precision_kind'] in ['year','range','relative','era','unknown']
 lo,hi=d['earliest_year'],d['latest_year'];assert all(y is None or type(y) is int and y!=0 and abs(y)<=10000 for y in [lo,hi])
 assert lo is None or hi is None or lo<=hi
 if d['precision_kind'] in ['year','range']:assert lo is not None and hi is not None
 if d['precision_kind']=='year':assert lo==hi
for source in plan['sources']:assert source['source_type'] in ['primary','reference','scholarship','digital','media'], 'Unsupported source type'
claims={c['id']:c for c in plan['new_claims']};assert len(claims)==len(plan['new_claims'])
meta=plan['source_metadata'];srcbyid={m['id']:m for m in meta.values()};texts=[];links=[];structures=[]
for cid,c in claims.items():
 m=srcbyid[c['source_id']];quote=c['note'][3:c['note'].index('；核对说明：')];b=(R/m['raw_path']).read_bytes();assert sha(b)==m['sha256'] and quote in b.decode('utf-8-sig')
 structures.append(dict(claim_id=cid,note_sha256=sha(c['note'].encode()),quote_text=quote,review_note=c['note'].split('；核对说明：',1)[1],review_state='deferred' if any(w in c['note'] for w in ['待考','异说','差异']) else 'recorded'))
for pid,m in meta.items():
 if m['id'] not in plan['used_source_ids']:continue
 b=(R/m['raw_path']).read_bytes();assert sha(b)==m['sha256'];commit=re.search(r'/blob/([0-9a-f]{40})/',m['url']).group(1);ah=sha(m['url'].encode())
 texts.append(dict(source_id=m['id'],archive_url_sha256=ah,archive_url=m['url'],content=b.decode('utf-8'),content_sha256=sha(b),archive_blob_sha256=sha(b),archive_commit=commit))
 links.append(dict(source_id=m['id'],archive_url_sha256=ah,snapshot_sha256=sha(b),paragraph_id=pid))
def fp(c):
 vals=[c[k] for k in ['subject_table','subject_id','claim_text','source_id','citation','note']]+[srcbyid[c['source_id']]['url']]
 return sha('|'.join(str(v or '').encode().hex().upper() for v in vals).encode())
for d in plan['event_dating']:assert d['claim_sha256']==fp(claims[d['claim_id']]) and claims[d['claim_id']]['subject_id']==d['event_id']
for d in plan['claim_relations']:assert d['claim_sha256']==fp(claims[d['claim_id']]) and d['related_sha256']==fp(claims[d['related_claim_id']])
inserts=[('source',plan['sources'],['id']),('event',plan['new_events'],['id']),('person_event',plan['new_person_events'],['id']),('source_text',texts,['source_id','archive_url_sha256']),('library_source_link',links,['source_id','archive_url_sha256']),('fact_claim',plan['new_claims'],['id']),('claim_structure',structures,['claim_id']),('event_dating',plan['event_dating'],['id']),('claim_relation',plan['claim_relations'],['id'])]
s=MysqlContentStore(R/'.env.migration.local',writable=apply,public_url='https://histree.wiki/api/v1');assert s.target_fingerprint==plan['target_fingerprint'];A=D/'publication-mysql.json';prior=json.loads(A.read_text()) if A.exists() else None
if prior:assert prior['plan_sha256']==digest
read=lambda c,t,identity: (c.execute('SELECT * FROM `'+t+'` WHERE '+' AND '.join(s.column(t,k)+'=%s' for k in identity)+' FOR UPDATE',list(identity.values())),c.fetchone())[1]
def norm(t,r):return s.normalize(t,r) if r else None
try:
 s.connection.begin()
 with s.connection.cursor(pymysql.cursors.DictCursor) as c:
  for u in updates:
   old=norm(u['table'],read(c,u['table'],dict(id=u['id'])));assert old is not None
   expected=dict(u['full_before'],**u['after'])
   assert all(old[k]==u['full_before'][k] for k in u['full_before'] if k!='updated_at') or prior and all(old[k]==expected[k] for k in expected if k!='updated_at'),('Old-value guard failed',u['key'])
  for old in plan['protected_events']:
   live=norm('event',read(c,'event',dict(id=old['id'])));assert live==old,('Old dated canonical event changed',old['id'])
  for table,rows,ids in inserts:
   assert table in s.columns
   for row in rows:
    assert set(row)<=s.columns[table],('Unexpected columns',table,set(row)-s.columns[table]);old=norm(table,read(c,table,{k:row[k] for k in ids}))
    if old:assert all(old[k]==v for k,v in row.items()),('Insert identity conflict',table,row.get('id',row.get('source_id')))
  if not apply:s.connection.rollback();print('READONLY VERIFIED',len(updates),'bounded updates;',sum(len(rs) for _,rs,_ in inserts),'inserts, source bytes and canonical dates checked; plan',digest);raise SystemExit(0)
  audit=dict(plan_sha256=digest,target_fingerprint=s.target_fingerprint,status='applying',verified=False,updates=len(updates),inserts={t:len(rs) for t,rs,_ in inserts});A.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
  for table,rows,ids in inserts:
   for row in rows:
    if read(c,table,{k:row[k] for k in ids}):continue
    cols=list(row);c.execute('INSERT INTO `'+table+'` ('+','.join(s.column(table,k) for k in cols)+') VALUES ('+','.join('%s' for _ in cols)+')',[s.value(table,k,row[k]) for k in cols])
  for u in updates:
   old=norm(u['table'],read(c,u['table'],dict(id=u['id'])))
   if all(old[k]==v for k,v in u['after'].items()):continue
   cols=list(u['after']);guards=list(u['before']);c.execute('UPDATE `'+u['table']+'` SET '+','.join(s.column(u['table'],k)+'=%s' for k in cols)+' WHERE id=%s AND '+' AND '.join(s.column(u['table'],k)+' <=> %s' for k in guards),[*[s.value(u['table'],k,u['after'][k]) for k in cols],u['id'],*[s.value(u['table'],k,u['before'][k]) for k in guards]]);assert c.rowcount==1
  for u in updates:
   actual=norm(u['table'],read(c,u['table'],dict(id=u['id'])));expected=dict(u['full_before'],**u['after']);assert all(actual[k]==v for k,v in expected.items() if k!='updated_at'),('Unplanned field change',u['key'])
  for old in plan['protected_events']:assert norm('event',read(c,'event',dict(id=old['id'])))==old
 s.connection.commit()
except BaseException:s.connection.rollback();raise
finally:s.connection.close()
# Anonymous verification is a separate resumable phase; publication is not accepted until it passes.
s=MysqlContentStore(R/'.env.migration.local',public_url='https://histree.wiki/api/v1');s.public=True
for table,ids in [('event',[u['id'] for u in updates if u['table']=='event']+[r['id'] for r in plan['new_events']]),('person',[u['id'] for u in updates if u['table']=='person']),('fact_claim',list(claims))]:
 out={}
 for i in range(0,len(ids),40):out.update({r['id']:r for r in s.request(table,'id=in.('+','.join(ids[i:i+40])+')&limit=1000')})
 assert len(out)==len(ids),(table,'anonymous visibility mismatch')
 for u in updates:
  if u['table']==table:assert all(out[u['id']][k]==v for k,v in u['after'].items())
 if table=='fact_claim':
  for cid,row in claims.items():assert all(out[cid][k]==v for k,v in row.items() if k in out[cid])
for p,h in plan['protected_paths'].items():assert sha((R/p).read_bytes())==h
A_data=json.loads(A.read_text());A_data.update(status='complete',verified=True,anonymous_readback_verified=True,protected_canonical_events_unchanged=True,original_batch_hashes_unchanged=True);A.write_text(json.dumps(A_data,ensure_ascii=False,indent=2)+'\n');s.connection.close();print('MYSQL REVISION ACCEPTED',len(updates),'updates,',len(plan['new_events']),'new stages,',len(claims),'new claims')
