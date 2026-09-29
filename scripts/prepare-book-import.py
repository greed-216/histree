"""Prepare a book-led batch and remove reused rows from status-change SQL."""
import json,re,subprocess,sys
from pathlib import Path
p=Path(sys.argv[1]).resolve();out=p.parent/'sql'
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
