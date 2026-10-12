"""Run the unchanged book publisher with bounded waiting on its normal lock."""
import sys,json,hashlib,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from publication_wait import install
batch=Path(sys.argv[1]);proof=json.loads(batch.with_name('preflight.json').read_text())
assert proof['read_only'] and proof['batch_sha256']==hashlib.sha256(batch.read_bytes()).hexdigest(),'Reviewed preflight differs'
install(proof['target_fingerprint'])
runpy.run_path(str(ROOT/'scripts/publish-book-batch.py'),run_name='__main__')
