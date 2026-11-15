"""Package reviewed originals and shared-script WebP outputs, with exact hashes."""
import hashlib,json,shutil,tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OUT=ROOT/'artifacts/stories-fifty-20261115'
TARGET=OUT/'upload'
TARGET.mkdir(parents=True,exist_ok=True)
stories=json.loads((BASE/'catalog-draft-with-images.json').read_text())['stories']
reviews=json.loads((BASE/'image-reviews.json').read_text())
assets=[]
for s in stories:
    file=BASE/s['slug']/reviews[s['slug']].get('file','atlas-v1.png')
    assert hashlib.sha256(file.read_bytes()).hexdigest()==s['image']['sha256']
    shutil.copy2(file,TARGET/(s['image']['sha256']+'.png'))
for f in (OUT/'web-images').glob('*.webp'):shutil.copy2(f,TARGET/f.name)
for f in sorted(TARGET.iterdir()):
    if f.suffix not in ['.png','.webp']:continue
    sha=hashlib.sha256(f.read_bytes()).hexdigest();assert sha==f.stem
    assets.append(dict(file=f.name,sha256=sha,bytes=f.stat().st_size))
expected={s['image']['url'].split('/')[-1] for s in stories}
expected|={p['image']['url'].split('/')[-1] for s in stories for p in s['panels']}
expected|={s['cover']['url'].split('/')[-1] for s in stories}
assert expected=={a['file'] for a in assets}
(TARGET/'assets.json').write_text(json.dumps(assets,indent=2)+'\n')
shutil.copy2(BASE/'upload.cjs',TARGET/'upload.cjs')
archive=OUT/'histree-fifty-upload-20261115.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in TARGET.iterdir():tar.add(p,arcname='histree-fifty-assets/'+p.name)
print(len(assets),'assets;',archive.stat().st_size,'archive bytes')
