"""Download the user-selected 24 histories at the recorded Git commit; verify Git blob hashes."""
import concurrent.futures, hashlib, json, pathlib, time, urllib.parse, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'resources'
tree=json.loads((BASE/'catalog/github-tree.json').read_text())
items=[x for x in tree['tree'] if x['path'].startswith('kindle_free_books/二十四史/PDF/') and x['path'].endswith('.pdf')]
def fetch(x):
    dest=BASE/'originals/twenty-four-histories/backup'/pathlib.Path(x['path']).name
    dest.parent.mkdir(parents=True,exist_ok=True)
    url='https://raw.githubusercontent.com/LeungGeorge/grimoire-kindle/'+tree['sha']+'/'+urllib.parse.quote(x['path'])
    for attempt in range(3):
        try:
            data=dest.read_bytes() if dest.exists() else urllib.request.urlopen(url,timeout=120).read()
            assert len(data)==x['size'] and data.startswith(b'%PDF-')
            assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==x['sha']
            dest.write_bytes(data)
            print('OK',dest.name,len(data),flush=True)
            return dict(title=dest.stem[2:],file=str(dest.relative_to(ROOT)),url=url,repository_commit=tree['sha'],git_blob_sha1=x['sha'],sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),accessed_at=time.strftime('%Y-%m-%d'),status='download_verified',edition_status='待检查版本页；不得视为古籍影印原本')
        except Exception as e:
            if attempt==2:return dict(title=dest.stem,file=str(dest.relative_to(ROOT)),url=url,status='failed',error=str(e))
            time.sleep(2)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(fetch,items))
(BASE/'catalog/twenty-four-histories.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('Downloaded',sum(x['status']=='download_verified' for x in results),'/',len(items),flush=True)
