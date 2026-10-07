"""Read-only anonymous verification of generated guide entities and references."""
import argparse,json,urllib.parse,urllib.request,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--env',type=Path,default=ROOT/'apps/web/.env.local');args=a.parse_args()
env=dict(l.split('=',1) for l in args.env.read_text().splitlines() if '=' in l and not l.startswith('#'))
url=env['VITE_SUPABASE_URL'].strip('"\'');key=env['VITE_SUPABASE_ANON_KEY'].strip('"\'')
def rows(table,ids):
 result={}
 for offset in range(0,len(ids),100):
  query=urllib.parse.urlencode({'id':'in.('+','.join(ids[offset:offset+100])+')','select':'*'})
  req=urllib.request.Request(url+'/rest/v1/'+table+'?'+query,headers={'apikey':key,'Authorization':'Bearer '+key})
  with urllib.request.urlopen(req,timeout=35) as f:result.update({r['id']:r for r in json.load(f)})
 assert set(result)==set(ids),(table,'Missing anonymous-visible rows')
 return result
path=ROOT/'apps/web/src/data/history-guides.json';data=json.loads(path.read_text())
events={e['id']:e for p in data['overview']['stages']+data['zhou']['chapters'] for e in p['events']}
people={p['id']:p for c in data['zhou']['chapters'] for p in c['people']}
refs={r['id']:dict(r,eventId=e['id']) for e in events.values() for r in e['evidence']}
for table,records in [('event',events),('person',people)]:
 live=rows(table,list(records))
 for rid,r in records.items():
  assert live[rid]['status']=='published'
  field='title' if table=='event' else 'name';assert live[rid][field]==r[field]
  if table=='event':assert live[rid]['start_year']==r['year']
live=rows('fact_claim',list(refs))
for rid,r in refs.items():
 row=live[rid];assert row['status']=='published' and row['source_id']==r['sourceId'] and row['subject_id']==r['eventId']
 assert row['citation']==r['citation']
 assert row['note'].split('原文：',1)[-1].split('；核对说明：',1)[0]==r['quote']
sourceids=list({r['sourceId'] for r in refs.values()});live=rows('source',sourceids)
for r in refs.values():assert live[r['sourceId']]['url']==r['url']
counts={}
for table in ['person_event','person_relationship']:
 selected={e['id']:e for c in data['zhou']['chapters'] for e in c['graph']['edges'] if e['subject_table']==table};counts[table]=len(selected)
 if not selected:continue
 live=rows(table,list(selected))
 for rid,e in selected.items():
  r=live[rid];assert r['status']=='published'
  if table=='person_event':assert (r['person_id'],r['event_id'],r['role'])==(e['source'],e['target'],e['type'])
  else:assert (r['person_a'],r['person_b'],r['relation_type'])==(e['source'],e['target'],e['type'])
audit=dict(status='anonymous_readback_verified',generated_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),events=len(events),people=len(people),claims=len(refs),sources=len(sourceids),graph_relations=counts,citation_corrections_verified=json.loads((ROOT/'content/revisions/2026-10-07-959-citation-era/publication.json').read_text())['corrected_rows'])
(ROOT/'content/guides/public-readback.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps(audit,ensure_ascii=False))
