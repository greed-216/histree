"""Prepare annual SQL without including reused records in publication/unpublication."""
import json,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[1]
subprocess.run([sys.executable,str(ROOT/'scripts/clean-public-copy.py'),'--batch',str(D/'content-batch.json')],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/prepare-content-import.py'),str(D/'content-batch.json'),str(D/'sql')],check=True)
b=json.loads((D/'content-batch.json').read_text());old=json.loads((D.parent/'later-liang-907-923/content-batch.json').read_text());ids=json.loads((D/'sql/key-map.json').read_text())
mapping={'people':'person','events':'event','person_events':'person_event','person_relationships':'person_relationship','claims':'fact_claim','topics':'topic'}
for name,status,groups in [('publish.sql','published',list(mapping)),('unpublish.sql','draft',list(reversed(mapping)))]:
 sql=['-- Only NEW records in year-0907-v1; reused published records are excluded.','BEGIN;']
 for group in groups:
  reused={r['key'] for r in old[group]};new=[ids[r['key']] for r in b[group] if r['key'] not in reused]
  if new:sql.append('UPDATE public.'+mapping[group]+" SET status='"+status+"' WHERE id IN ("+','.join("'"+i+"'" for i in new)+');')
 sql.append('COMMIT;');(D/'sql'/name).write_text('\n'.join(sql)+'\n')
