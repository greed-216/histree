"""Prepare a book-led batch and remove reused rows from status-change SQL."""
import json,re,subprocess,sys,uuid
from pathlib import Path
p=Path(sys.argv[1]).resolve();out=p.parent/'sql'
# Published batches are immutable archives. Check prospective imports against
# reviewed corrections before generating any SQL from their reused rows.
if not (p.parent/'publication.json').exists():
 batch=json.loads(p.read_text())
 revisions={}
 root=Path(__file__).resolve().parents[1]
 for revision in sorted((root/'content/revisions').glob('*/relations.json')):
  for row in json.loads(revision.read_text()).get('relations',[]):
   revisions[row['key']]=row['after']
 reused=set(json.loads((p.parent/'reused-keys.json').read_text()))
 for row in batch['person_relationships']:
  if row['key'] not in reused:
   assert row['relation_type'] not in ['父子','母子','统属'], f"{row['key']}: 请填写 A 相对于 B 的具体身份"
  if row['key'] in revisions:
   namespace=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
   actual={'person_a':str(uuid.uuid5(namespace,row['person_a_key'])), 'person_b':str(uuid.uuid5(namespace,row['person_b_key'])), 'relation_type':row['relation_type']}
   assert actual==revisions[row['key']], f"{row['key']}: 与已校核关系方向不一致，请按 content/revisions 修正后复用"
subprocess.run([sys.executable,str(Path(__file__).with_name('prepare-content-import.py')),str(p),str(out)],check=True)
ids=json.loads((out/'key-map.json').read_text());reused=json.loads((p.parent/'reused-keys.json').read_text())
excluded={ids[k] for k in reused}
for name in ['publish.sql','unpublish.sql']:
 lines=[]
 for line in (out/name).read_text().splitlines():
  if line.startswith('UPDATE '):
   keys=[v for v in re.findall(r"'([0-9a-f-]{36})'",line) if v not in excluded]
   if not keys:continue
   line=re.sub(r'IN \(.*\)',"IN ("+','.join("'"+v+"'" for v in keys)+')',line)
  lines.append(line)
 (out/name).write_text('\n'.join(lines)+'\n')
