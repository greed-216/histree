"""Archive Wikisource rendered volume text with revision IDs and raw API responses."""
import threading,concurrent.futures,hashlib,json,pathlib,re,time,urllib.parse,urllib.request
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]; BASE=ROOT/'resources'
BOOKS=[('wudai-huiyao','五代會要',30,'制度汇编'),('shiguo-chunqiu','十國春秋',114,'后世十国史汇编'),('wudai-shibu','五代史補 (四庫全書本)',5,'笔记补史'),('beimeng-suoyan','北夢瑣言 (四庫全書本)',20,'晚唐五代笔记'),('wuyue-beishi','吳越備史',4,'吴越地方史')]
STOP=threading.Event()
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,t,a):
        if t in ('script','style'):self.skip+=1
        if t in ('p','div','br','li','tr','h1','h2','h3','h4'):self.parts.append('\n')
        if t=='img':
            attrs=dict(a);self.parts.append('[图字:'+attrs.get('alt','待核')+']')
    def handle_endtag(self,t):
        if t in ('script','style'):self.skip=max(0,self.skip-1)
        if t in ('p','div','li','tr','h1','h2','h3','h4'):self.parts.append('\n')
    def handle_data(self,s):
        if not self.skip:self.parts.append(s)
    def result(self):return re.sub(r'\n[ \t]*\n+', '\n\n',''.join(self.parts)).strip()+'\n'
def fetch_page(slug,title):
    folder=BASE/'originals/supplements'/slug;folder.mkdir(parents=True,exist_ok=True)
    name=title.replace('/','__'); raw=folder/(name+'.json');txt=folder/(name+'.txt')
    url='https://zh.wikisource.org/w/api.php?'+urllib.parse.urlencode(dict(action='parse',page=title,prop='text|links|revid',format='json'))
    for attempt in range(3):
        if STOP.is_set() and not raw.exists():return dict(title=title,status="deferred_rate_limit"),[]
        try:
            payload=raw.read_bytes() if raw.exists() else urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HistreeResearch/0.1 (historical source archive)'}),timeout=45).read()
            data=json.loads(payload)
            if 'parse' not in data:raise ValueError(str(data)[:200])
            p=data['parse'];raw.write_bytes(payload);parser=Text();parser.feed(p['text']['*']);text=parser.result();txt.write_text(text)
            row=dict(title=title,file=str(txt.relative_to(ROOT)),raw_file=str(raw.relative_to(ROOT)),url='https://zh.wikisource.org/wiki/'+urllib.parse.quote(title),revision_id=p['revid'],permalink='https://zh.wikisource.org/w/index.php?oldid='+str(p['revid']),sha256=hashlib.sha256(txt.read_bytes()).hexdigest(),characters=len(text),accessed_at=time.strftime('%Y-%m-%d'),status='downloaded',edition_status='维基文库电子转录；未逐字校勘',license_note='保留页面来源与修订号；遵循来源页面署名及共享条款')
            return row,p.get('links',[])
        except Exception as e:
            if getattr(e,"code",None)==429:
                STOP.set();return dict(title=title,status="deferred_rate_limit",error=str(e)),[]
            if attempt==2:return dict(title=title,status='failed',error=str(e),url=url),[]
            time.sleep(2)
def book(spec):
    slug,title,expected,kind=spec
    index,links=fetch_page(slug,title)
    targets=sorted(set(x['*'] for x in links if x.get('ns')==0 and 'exists' in x and x['*'].startswith(title+'/')))
    rows=[index]
    for page in targets:
        if not STOP.is_set():time.sleep(3)
        row,_=fetch_page(slug,page);rows.append(row)
    result=dict(key=slug,title=title,kind=kind,expected_main_volumes=expected,linked_subpages=len(targets),downloaded_pages=sum(x['status']=='downloaded' for x in rows),pages=rows,completeness='待按卷次核验；目录链接存在不等于正文完整')
    (BASE/'catalog'/f'{slug}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(title,result['downloaded_pages'],'/',len(rows),flush=True)
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:results=list(pool.map(book,BOOKS))
(BASE/'catalog/supplements.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
