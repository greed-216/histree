"""Anonymous byte-for-byte verification; does not save remote media files."""
import concurrent.futures,hashlib,json,urllib.request,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/stories-fifty-20261115'
expected=json.loads((OUT/'upload/assets.json').read_text())
uploaded={x['file']:x for x in json.loads((OUT/'oss-uploads.json').read_text())}
assert len(uploaded)==len(expected)==236
def verify(item):
    prior=uploaded[item['file']]
    assert prior['sha256']==item['sha256'] and prior['bytes']==item['bytes']
    url='https://histree.wiki/api/v1/media/images/'+item['file']
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url,timeout=90) as response:
                h=hashlib.sha256();size=0
                while True:
                    block=response.read(65536)
                    if not block:break
                    h.update(block);size+=len(block)
                content_type=response.headers['Content-Type'].split(';')[0]
                assert response.status==200 and size==item['bytes'] and h.hexdigest()==item['sha256']
                assert content_type==prior['contentType']
                return dict(file=item['file'],bytes=size,sha256=h.hexdigest(),contentType=content_type,cacheControl=response.headers['Cache-Control'])
        except Exception:
            if attempt==2:raise
            time.sleep(1)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    result=list(pool.map(verify,expected))
(OUT/'public-assets-readback.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(result),'public images,',sum(x['bytes'] for x in result),'bytes, all SHA256/MIME/size match')
