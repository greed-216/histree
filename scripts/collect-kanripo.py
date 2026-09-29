"""Collect bounded historical text repositories, pinned to a commit, preserving page markers."""
import subprocess,concurrent.futures,hashlib,io,json,pathlib,time,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'resources'
BOOKS=[('KR2m0003','五代會要',30),('KR2i0021','十國春秋',114),('KR2i0019','吳越備史',4),('KR2i0016','蜀檮杌',2),('KR2i0017','馬氏南唐書',30),('KR2i0018','陸氏南唐書',18),('KR3l0023','北夢瑣言',20)]
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HistreeResearch'}),timeout=90).read()
def book(spec):
 key,title,expected=spec;folder=BASE/'originals/kanripo'/key;folder.mkdir(parents=True,exist_ok=True)
 try:
  commit=subprocess.check_output(['git','ls-remote',f'https://github.com/kanripo/{key}.git','HEAD'],text=True,timeout=60).split()[0]
  url=f'https://codeload.github.com/kanripo/{key}/zip/{commit}';payload=get(url);archive=folder/'source.zip';archive.write_bytes(payload);rows=[]
  with zipfile.ZipFile(io.BytesIO(payload)) as z:
   for info in z.infolist():
    rel=pathlib.PurePosixPath(info.filename).parts[1:]
    if info.is_dir() or not rel or '..' in rel:continue
    dest=folder.joinpath(*rel);dest.parent.mkdir(parents=True,exist_ok=True);b=z.read(info);dest.write_bytes(b)
    rows.append(dict(file=str(dest.relative_to(ROOT)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
  texts=[x for x in rows if x['file'].endswith('.txt')]
  result=dict(key=key,title=title,expected_main_volumes=expected,text_files=len(texts),repository=f'https://github.com/kanripo/{key}',commit=commit,archive_url=url,archive_file=str(archive.relative_to(ROOT)),archive_sha256=hashlib.sha256(payload).hexdigest(),accessed_at=time.strftime('%Y-%m-%d'),files=rows,status='downloaded',edition_status='版本声明见同目录Readme.org；保留原页码标记，未逐字校勘')
 except Exception as e:result=dict(key=key,title=title,status='failed',error=str(e))
 (BASE/'catalog'/f'{key}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(title,result.get('text_files'),result['status'],flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(book,BOOKS))
(BASE/'catalog/kanripo.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
