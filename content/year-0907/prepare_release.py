"""Build guarded updates from the originally imported draft to the reviewed release.
Usage: python3 prepare_release.py original-draft.json
The before image is retained for auditing. Refuses concurrent editorial changes.
"""
import json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
before=json.loads(Path(sys.argv[1]).read_text());after=json.loads((D/'content-batch.json').read_text());ids=json.loads((D/'sql/key-map.json').read_text())
old=json.loads((D.parent/'later-liang-907-923/content-batch.json').read_text())
tables={'people':'person','events':'event','person_events':'person_event','person_relationships':'person_relationship','claims':'fact_claim','sources':'source','topics':'topic'}
def lit(x):return "'"+x.replace("'","''")+"'"
def converted(r):
 r=dict(r);r.pop('key')
 for a,z in {'person_key':'person_id','event_key':'event_id','person_a_key':'person_a','person_b_key':'person_b','subject_key':'subject_id','source_key':'source_id'}.items():
  if a in r:r[z]=ids[r.pop(a)]
 if 'sections' in r:r['sections']=[dict(heading=s['heading'],body=s['body'],node_ids=[ids[k] for k in s['node_keys']]) for s in r['sections']]
 return r
sql=['BEGIN;','SET LOCAL standard_conforming_strings = on;'];audit=[]
for g,t in tables.items():
 prior={r['key']:r for r in before[g]};reused={r['key'] for r in old[g]}
 for r in after[g]:
  k=r['key']
  if k not in prior or r==prior[k]:continue
  assert k not in reused, f'Refusing to modify reused record {k}'
  a,z=converted(prior[k]),converted(r)
  payload=lit(json.dumps(z,ensure_ascii=False));expected=lit(json.dumps(a,ensure_ascii=False));key=lit(ids[k]);cols=[x for x in z if z[x]!=a.get(x)]
  sql.append(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM public.{t} t WHERE id={key} AND to_jsonb(t) @> {expected}::jsonb) THEN RAISE EXCEPTION 'Concurrent change or missing draft: {ids[k]}'; END IF; END $$;")
  sql.append(f"UPDATE public.{t} SET "+','.join(f'{c}=v.{c}' for c in cols)+f' FROM jsonb_populate_record(NULL::public.{t}, {payload}::jsonb) v WHERE {t}.id={key};')
  audit.append(dict(table=t,key=k,id=ids[k],before=a,after=z))
# Combine inserts, corrections, publication into a SINGLE transaction.
insert=(D/'sql/import-draft.sql').read_text().replace('BEGIN;','',1).rsplit('COMMIT;',1)[0]
publish=(D/'sql/publish.sql').read_text().replace('BEGIN;','',1).rsplit('COMMIT;',1)[0]
sql += [insert,publish,'COMMIT;']
(D/'sql/release.sql').write_text('\n'.join(sql)+'\n');(D/'release-changes.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print('Guarded corrections:',len(audit))
