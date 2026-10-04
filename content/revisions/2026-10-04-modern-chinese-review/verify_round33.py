# coding: utf-8
"""Independent anonymous verification after the guarded first copy revision."""
import importlib.util,json,hashlib,gzip
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'scripts/review-public-history-copy.py').exists())
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
plan_path=P/'round-33/changes.json';plan=read(plan_path);pub=read(P/'round-33/publication.json');assert pub['verified'] and pub['plan_sha256']==sha(plan_path)
spec=importlib.util.spec_from_file_location('copy_review',ROOT/'scripts/review-public-history-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);client=m.Client()
snap=read(Path('/private/tmp/histree-public-prose-20261004.json'));assert sha(Path('/private/tmp/histree-public-prose-20261004.json'))==plan['inventory_sha256']
sources={r['id']:r for r in snap['tables']['source']};groups={};counts={};quote_count=0
for item in plan['supporting_claims']:
 claim=item['baseline'];records=client.request('fact_claim',{'id':'eq.'+item['claim_id'],'select':'id,subject_table,subject_id,field_path,claim_text,source_id,citation,note,status,source:source_id(id,url)'})
 assert len(records)==1;record=records[0]
 assert all(record[k]==v for k,v in claim.items())
 assert record['source'] and record['source']['url']==sources[record['source_id']]['url']
 assert record['subject_id']==item['person_id'] and m.quote(record['note'])==m.quote(claim['note'])
print('Supporting introductory claims',len(plan['supporting_claims']),flush=True)

for change in plan['changes']:groups.setdefault(change['table'],[]).append(change)
for table,changes in groups.items():
 ids=[c['id'] for c in changes];expected={c['id']:c for c in changes};count=0
 for offset in range(0,len(ids),80):
  chunk=ids[offset:offset+80];selection='id,subject_table,subject_id,field_path,claim_text,source_id,citation,note,status,source:source_id(id,url)' if table=='fact_claim' else '*'
  rows=client.request(table,{'id':'in.('+','.join(chunk)+')','select':selection})
  assert {r['id'] for r in rows}==set(chunk),table
  for row in rows:
   c=expected[row['id']]
   assert all(row[k]==v for k,v in c['after'].items()),(table,row['id'],'public prose does not match')
   assert all(row[k]==v for k,v in c['baseline'].items() if k not in c['after'] and k!='updated_at'),(table,row['id'],'protected field changed')
   if table=='fact_claim':
    assert m.quote(row['note'])==m.quote(c['baseline']['note'])
    assert row['source'] and row['source']['id']==row['source_id'] and row['source']['url']==sources[row['source_id']]['url']
    quote_count+=1
  count+=len(rows)
 counts[table]=count;print(table,count,flush=True)
changes_by_id={(c['table'],c['id']):c for c in plan['changes']}
unchanged_groups={}
for c in plan['reviewed_unchanged']:unchanged_groups.setdefault(c['table'],{})[c['id']]=c['baseline']
for table,expected in unchanged_groups.items():
 ids=list(expected)
 for offset in range(0,len(ids),80):
  chunk=ids[offset:offset+80]
  selection='id,subject_table,subject_id,field_path,claim_text,source_id,citation,note,status' if table=='fact_claim' else '*'
  results=client.request(table,{'id':'in.('+','.join(chunk)+')','select':selection})
  assert {r['id'] for r in results}==set(chunk)
  for row in results:
   base=expected[row['id']];change=changes_by_id.get((table,row['id']),{})
   wanted=dict(base);wanted.update(change.get('after',{}))
   assert all(row[k]==v for k,v in wanted.items() if k!='updated_at'),(table,row['id'],'unchanged reviewed field or protected row changed')
for archive in plan['archives']:
 assert sha(ROOT/archive['batch']/'content-batch.json')==archive['batch_sha256']
 for source in archive['source_files']:assert sha(ROOT/source['path'])==source['sha256']
proof=dict(verified=True,at=datetime.now(timezone.utc).isoformat(),plan_sha256=sha(plan_path),public_counts=counts,exact_prose_verified=True,verbatim_quotes_unchanged=quote_count+len(plan['supporting_claims']),source_joins_and_urls_verified=True,identity_dates_states_and_endpoints_unchanged=True,published_archives_and_original_files_unchanged=True,unchanged_reviewed_fields_verified=sum(len(c['fields']) for c in plan['reviewed_unchanged']),full_goal_complete=False)
write(P/'round-33/readback-audit.json',proof)
with gzip.open(P/'review-ledger.jsonl.gz','rt',encoding='utf-8') as f:ledger=[json.loads(line) for line in f]
reviewed={(c['table'],c['id'],field) for c in plan['changes'] for field in c['after']}
reviewed.update((c['table'],c['id'],field) for c in plan['reviewed_unchanged'] for field in c['fields'])
found=set()
for field in ledger:
 key=(field['table'],field['id'],field['field'])
 if key in reviewed:
  assert field['status']=='pending' or field['round']=='round-33', key
  field['status']='reviewed_verified';field['round']='round-33';found.add(key)
assert found==reviewed, 'All reviewed fields must exist in the inventory ledger'
with gzip.open(P/'review-ledger.jsonl.gz','wt',encoding='utf-8') as f:
 for field in ledger:f.write(json.dumps(field,ensure_ascii=False,separators=(',',':'))+'\n')
from collections import Counter
progress=read(P/'progress.json');progress['field_counts']=dict(Counter(x['status'] for x in ledger));assert not any(r['path']=='round-33' for r in progress['rounds'])
progress['rounds'].append(dict(path='round-33',status='published_verified',changes=len(plan['changes']),readback_audit_sha256=sha(P/'round-33/readback-audit.json')));assert progress['complete'] is False;write(P/'progress.json',progress)
print('Thirty-third round verified; full-site review remains active.',flush=True)
