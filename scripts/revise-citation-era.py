"""Guarded correction of one known citation-label error. Default is read-only."""
import argparse,hashlib,json,os,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('plan',type=Path);a.add_argument('--apply',action='store_true');a.add_argument('--mysql-env',default=str(ROOT/'.env.migration.local'));a.add_argument('--public-api-url',default='https://123.56.189.146/api/v1');args=a.parse_args()
plan=json.loads(args.plan.read_text());changes=plan['changes']
from public_content_client import PublicContentClient
client=PublicContentClient(args.public_api_url,args.mysql_env,args.apply)
def request(query,body=None):return client.request('fact_claim',query,body)
for c in changes:
 assert c['table']=='fact_claim' and set(c['before'])==set(c['after'])=={'citation'}
 assert c['after']['citation']==c['before']['citation'].replace('显德五年（959','显德六年（959') and c['before']!=c['after']
 assert c['baseline']['id']==c['id'] and c['baseline']['citation']==c['before']['citation']
assert len({c['id'] for c in changes})==len(changes)
ids=list(c['id'] for c in changes);live={}
for offset in range(0,len(ids),100):
 rows=request({'id':'in.('+','.join(ids[offset:offset+100])+')','select':'id,citation,source_id,subject_table,subject_id,note,status'})
 live.update({r['id']:r for r in rows})
assert set(live)==set(ids)
for c in changes:
 current=live[c['id']];assert current['citation'] in [c['before']['citation'],c['after']['citation']]
 assert all(current[k]==v for k,v in c['baseline'].items() if k!='citation'), 'Concurrent non-citation change'
digest=hashlib.sha256(args.plan.read_bytes()).hexdigest()
if not args.apply:
 args.plan.with_name('preflight.json').write_text(json.dumps({'read_only':True,'plan_sha256':digest,'verified_rows':len(changes)},indent=2)+'\n');print('Read-only preflight verified:',len(changes));raise SystemExit(0)
preflight=json.loads(args.plan.with_name('preflight.json').read_text());assert preflight['read_only'] and preflight['plan_sha256']==digest
groups={}
for c in changes:
 if live[c['id']]['citation']==c['after']['citation']:continue
 groups.setdefault((c['before']['citation'],c['after']['citation']),[]).append(c['id'])
for i,((before,after),group) in enumerate(groups.items()):
 for offset in range(0,len(group),100):
  chunk=group[offset:offset+100]
  rows=request({'id':'in.('+','.join(chunk)+')','citation':'eq.'+before,'select':'id,citation,source_id,subject_table,subject_id,note,status'},{'citation':after})
  assert {r['id'] for r in rows}==set(chunk), 'Concurrent citation change; stop and inspect'
  for row in rows:
   baseline=live[row['id']];assert row=={**baseline,'citation':after}
 print('Corrected citation group',i+1,'/',len(groups),flush=True)
verified={}
for offset in range(0,len(ids),100):
 verified.update({r['id']:r for r in request({'id':'in.('+','.join(ids[offset:offset+100])+')','select':'id,citation,source_id,subject_table,subject_id,note,status'})})
for c in changes:assert verified[c['id']]=={**c['baseline'],**c['after']}
args.plan.with_name('publication-mysql.json').write_text(json.dumps({'status':'applied_anonymous_readback_verified','plan_sha256':digest,'corrected_rows':len(changes),'preserved_fields':['note','source_id','subject_table','subject_id','status']},ensure_ascii=False,indent=2)+'\n')
print('Applied and anonymously verified:',len(changes))
