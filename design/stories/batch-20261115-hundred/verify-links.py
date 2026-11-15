"""Anonymous readback of the selected published people and primary passages."""
import concurrent.futures,json,urllib.request,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE.parents[2]/'artifacts/stories-hundred-20261115'
OUT.mkdir(parents=True,exist_ok=True)
stories=json.loads((BASE/'scripts.json').read_text())['stories']
identities=json.loads((BASE/'identities.json').read_text())
people={p['id']:p for s in identities for p in s['people']}
jobs=[('person',ident,'/api/v1/entry/'+ident) for ident in people]
for s in stories:
    p=s['sourceParagraphs'][0]
    jobs.append(('source',p['id'],f'/api/v1/library/shiji/sections/{p["section_id"]}?paragraph={p["id"]}'))
def get(job):
    kind,ident,path=job
    with urllib.request.urlopen('https://histree.wiki'+path,timeout=30) as r:
        raw=r.read();data=json.loads(raw)
    if kind=='person':
        assert data['id']==ident and data['type']=='person' and data['status']=='published',(ident,data)
        return dict(kind=kind,id=ident,name=data['name'],aliases=data['aliases'],description=data['description'])
    assert ident in raw.decode(),ident
    return dict(kind=kind,id=ident,url=path,sha256=hashlib.sha256(raw).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    results=list(pool.map(get,jobs))
(OUT/'source-person-readback.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('Verified',len(people),'published people and',len(stories),'source links')
