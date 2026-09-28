#!/usr/bin/env python3
"""Compile a validated editorial batch into reviewable, transactional SQL; never connects to a DB."""
import json
import subprocess
import sys
import uuid
from pathlib import Path

batch_path = Path(sys.argv[1])
out = Path(sys.argv[2])
subprocess.run([sys.executable, str(Path(__file__).with_name('validate-content-batch.py')), str(batch_path)], check=True)
batch = json.loads(batch_path.read_text())
namespace = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/greed-216/histree/content')
ids = {row['key']: str(uuid.uuid5(namespace, row['key']))
       for group in batch.values() if isinstance(group, list) for row in group}
groups = [('sources','source'),('people','person'),('events','event'),
          ('person_relationships','person_relationship'),('person_events','person_event'),
          ('claims','fact_claim'),('topics','topic')]
# Identifiers come from this whitelist, never from free-form batch data.
columns = {
 'source': 'id title source_type author edition url note',
 'person': 'id name aliases era birth_year death_year description biography status',
 'event': 'id title start_year end_year time_original dynasty description phases location_name location_modern_name location_lat location_lng location_precision location_note status',
 'person_relationship': 'id person_a person_b relation_type description status',
 'person_event': 'id person_id event_id role status',
 'fact_claim': 'id subject_table subject_id field_path claim_text source_id citation note status',
 'topic': 'id slug title description sections status',
}
def literal(value):
 return "'" + value.replace("'", "''") + "'"

sql = ['BEGIN;', "SET LOCAL standard_conforming_strings = on;"]
publish, unpublish = ['BEGIN;'], ['BEGIN;']
for group, table in groups:
 rows = []
 for original in batch[group]:
  row = dict(original)
  row['id'] = ids[row.pop('key')]
  for src, dst in {'person_key':'person_id','event_key':'event_id','person_a_key':'person_a',
                   'person_b_key':'person_b','subject_key':'subject_id','source_key':'source_id'}.items():
   if src in row: row[dst] = ids[row.pop(src)]
  if table == 'topic':
   row['sections'] = [dict(heading=s['heading'],body=s['body'],node_ids=[ids[k] for k in s['node_keys']]) for s in row['sections']]
  allowed = columns[table].split()
  if set(row) - set(allowed): raise ValueError(f'Unsupported columns for {table}')
  rows.append(row)
 if not rows: continue
 cols = ', '.join(columns[table].split())
 payload = literal(json.dumps(rows,ensure_ascii=False))
 sql.append(f'INSERT INTO public.{table} ({cols})\nSELECT {cols} FROM jsonb_populate_recordset(NULL::public.{table}, {payload}::jsonb)\nON CONFLICT (id) DO NOTHING;')
 # Re-running a batch must never silently overwrite subsequent editor changes.
 if table != 'source':
  selected = ','.join(literal(r['id']) for r in rows)
  publish.append(f"UPDATE public.{table} SET status='published' WHERE id IN ({selected});")
  unpublish.insert(1, f"UPDATE public.{table} SET status='draft' WHERE id IN ({selected});")
for statements in (sql,publish,unpublish): statements.append('COMMIT;')
out.mkdir(parents=True,exist_ok=True)
for name, statements in [('import-draft.sql',sql),('publish.sql',publish),('unpublish.sql',unpublish)]:
 (out/name).write_text('\n\n'.join(statements)+'\n')
(out/'key-map.json').write_text(json.dumps(ids,ensure_ascii=False,indent=2)+'\n')
print(f'Prepared {len(ids)} records in {out}; no database writes performed.')
