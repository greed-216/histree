# coding: utf-8
"""Anonymous post-publication contract acceptance; no database or filesystem mutations beyond report."""
import concurrent.futures,hashlib,json,time,urllib.request,urllib.parse
from pathlib import Path
D=Path(__file__).resolve().parent;P=D/'plan.json';plan=json.loads(P.read_text());digest=hashlib.sha256(P.read_bytes()).hexdigest();receipt=json.loads((D/'publication-mysql.json').read_text());assert receipt['verified'] and receipt['plan_sha256']==digest
base='https://histree.wiki/api/v1'
def get(path):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(base+path,timeout=40) as response:return json.load(response)
  except Exception:
   if attempt==2:raise
   time.sleep(attempt+1)
byevent={}
for d in plan['event_dating']:byevent.setdefault(d['event_id'],[]).append(d)
def entry(pair):
 eid,expected=pair;row=get('/entry/'+eid);actual={d['id']:d for d in row['datings']}
 for d in expected:
  a=actual[d['id']]
  for k in ['event_id','earliest_year','latest_year','era_key','basis','claim_id','review_state']:assert a[k]==d[k],(eid,k)
  assert a['precision']==d['precision_kind']
 return eid
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:events=list(pool.map(entry,byevent.items()))
print('ENRICHED DATINGS VERIFIED',len(events),sum(map(len,byevent.values())),flush=True)
claims=plan['new_claims'];claim_count=relations=0
for start in range(0,len(claims),40):
 chunk=claims[start:start+40];q=urllib.parse.urlencode(dict(ids=','.join(c['id'] for c in chunk),limit=50));data=get('/catalog/fact_claim?'+q);assert not data['has_more'];rows={r['id']:r for r in data['items']};assert len(rows)==len(chunk)
 for c in chunk:
  e=rows[c['id']]['evidence'];assert e['origin']=='structured' and e['quote'] in c['note'] and e['review']==c['note'].split('；核对说明：',1)[1];assert e['location']['book_key']=='shiji';relations+=len(e['related_claims']);claim_count+=1
print('STRUCTURED CLAIMS VERIFIED',claim_count,'relation endpoints',relations,flush=True)
newsrc=[(pid,m) for pid,m in plan['source_metadata'].items() if m.get('new')]
def source(pair):
 pid,m=pair;body=get('/sources/'+m['id']+'/text');loc=get('/sources/'+m['id']+'/location')
 assert body['source_id']==m['id'] and body['archive_url']==m['url'];assert body['content_sha256']==m['sha256']==hashlib.sha256(body['content'].encode()).hexdigest();assert loc['paragraph_id']==pid and loc['book_key']=='shiji'
 return pid
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:sources=list(pool.map(source,newsrc))
print('ORIGINAL READER LINKS VERIFIED',len(sources),flush=True)
# Confirm exact-year visibility through the annual public query, across all pages.
years={}
for u in plan['updates']:
 if u['table']=='event' and 'start_year' in u['after']:years.setdefault(u['after']['start_year'],set()).add(u['id'])
for e in plan['new_events']:years.setdefault(e['start_year'],set()).add(e['id'])
def annual(pair):
 year,expected=pair;visible=set()
 for page in range(300):
  data=get('/timeline?year='+str(year)+'&page='+str(page));visible.update(r['id'] for r in data['items'])
  if not data['has_more']:break
 else:raise AssertionError('Annual pagination bound')
 assert expected<=visible,(year,expected-visible)
 return year
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:annual_years=list(pool.map(annual,years.items()))
print('ANNUAL TIMELINE VERIFIED',len(annual_years),'years',flush=True)
report=dict(verified=True,plan_sha256=digest,anonymous=True,dated_entries=len(events),dating_rows=sum(map(len,byevent.values())),structured_claims=claim_count,relation_endpoints=relations,new_original_sources=len(sources),annual_years=sorted(annual_years),annual_newly_dated_events=sum(map(len,years.values())))
(D/'public-contract-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PUBLIC ACCEPTANCE COMPLETE',flush=True)
