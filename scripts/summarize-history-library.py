"""Build and verify the local research-library catalog; never imports production content."""
import hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1];B=ROOT/'resources';C=B/'catalog'
def load(name):return json.loads((C/name).read_text())
def save(name,obj):(C/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
books=[];checks=[]
periods=['上古—西汉','西汉','东汉','三国','两晋十六国','南北朝','南北朝','南北朝','南北朝','南北朝','南北朝','南北朝','隋','南北朝','南北朝','唐','唐','五代十国','五代十国','宋','辽','金','元','明']
ins={x['file']:x for x in load('pdf-inspection.json')}
for i,x in enumerate(load('twenty-four-histories.json')):
 p=ROOT/x['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']; assert ins[x['file']]['status']=='parsed'
 books.append(dict(key='history-'+str(i+1).zfill(2),title=x['title'],periods=[periods[i]],format='PDF',file=x['file'],source_url=x['url'],sha256=x['sha256'],pages=ins[x['file']]['pages'],edition_status=ins[x['file']]['edition_status'],status='下载校验通过；版本待考'))
checks.append('24/24 PDF通过SHA-256复核、Git blob校验及PDF解析；未逐页校勘')
x=load('tongjian-user-file.json');assert hashlib.sha256((ROOT/x['file']).read_bytes()).hexdigest()==x['sha256'];books.append(dict(key='tongjian-user',title='资治通鉴',periods=['战国—五代'],format='TXT',file=x['file'],sha256=x['sha256'],edition_status=x['edition_status'],status='294卷标题已识别'))
vols=load('tongjian-volumes.json');assert len(vols)==294
for x in vols:assert hashlib.sha256((ROOT/x['file']).read_bytes()).hexdigest()==x['sha256']
assert [(x['volume'],x['heading']) for x in vols[265:272]]==[(266,'后梁纪一'),(267,'后梁纪二'),(268,'后梁纪三'),(269,'后梁纪四'),(270,'后梁纪五'),(271,'后梁纪六'),(272,'后唐纪一')]
checks.append('用户TXT原件哈希未变；294个分卷哈希通过；后梁卷266—271及后唐卷272标题对应正确')
for x in load('kanripo.json'):
 assert x['status']=='downloaded'
 for f in x['files']:assert hashlib.sha256((ROOT/f['file']).read_bytes()).hexdigest()==f['sha256']
 readme=(B/'originals/kanripo'/x['key']/'Readme.org').read_text(); targets=set(re.findall(r'\[\[file:([^\]:]+)',readme));assert all((B/'originals/kanripo'/x['key']/t).exists() for t in targets)
 edition=re.search(r'^#\+TITLE: .+ / (.+)$',readme,re.M).group(1)
 books.append(dict(key=x['key'],title=x['title'],periods=['晚唐—五代十国'],format='TXT',directory='resources/originals/kanripo/'+x['key'],source_url=x['repository'],commit=x['commit'],text_files=x['text_files'],edition_code=edition,edition_status='仓库标注版本：'+edition+'；非书页影像；未逐字校勘',status='固定提交已归档；目录链接文件齐全'))
checks.append('7个Kanripo仓库文件哈希及Readme目录引用文件均通过')
# Reconstruct the Wikisource partial inventory, including pages saved before rate-limit interruption.
wiki=[]
for raw in sorted((B/'originals/supplements').glob('*/*.json')):
 d=json.loads(raw.read_text()).get('parse');txt=raw.with_suffix('.txt')
 if d and txt.exists():wiki.append(dict(title=d['title'],file=str(txt.relative_to(ROOT)),raw_file=str(raw.relative_to(ROOT)),revision_id=d['revid'],permalink='https://zh.wikisource.org/w/index.php?oldid='+str(d['revid']),sha256=hashlib.sha256(txt.read_bytes()).hexdigest(),characters=len(txt.read_text())))
save('wikisource-downloaded-pages.json',wiki)
w=next(x for x in wiki if x['title']=='五代史補 (四庫全書本)/全覽');s=(ROOT/w['file']).read_text();assert all('卷'+n in s for n in ['一','二','三','四','五'])
books.append(dict(key='wudai-shibu',title='五代史补',periods=['五代'],format='TXT',file=w['file'],source_url=w['permalink'],sha256=w['sha256'],edition_status='四库全书本电子转录；未逐字校勘',status='已取得五卷合并页；分卷副本有缺口，使用合并页'))
pg=load('beimeng-gutenberg.json');assert hashlib.sha256((ROOT/pg['file']).read_bytes()).hexdigest()==pg['sha256'];checks.append('五代史补合并文本含五卷标题；北梦琐言另有Gutenberg副本')
for row in ins.values():
 if 'extracted_pages_file' in row:
  pages=[json.loads(l) for l in (ROOT/row['extracted_pages_file']).read_text().splitlines()];assert len(pages)==row['pages'];assert [p['pdf_page'] for p in pages]==list(range(1,row['pages']+1))
checks.append('旧五代史1667页、新五代史1627页已逐页提取，页码连续、数量匹配')
save('library.json',dict(collected_at='2026-09-29',unique_works=len(books),books=books,alternate_editions=[pg],validation=checks))
summary=['# 采集与质量报告','','日期：2026-09-29。已归档 **33种书**：二十四史24种、用户提供的资治通鉴1种、五代十国补充资料8种；不同网站或版本的副本不重复计数。','', '## 已取得资料','','| 类别 | 结果 |','| --- | --- |','| 二十四史PDF | 24/24，原PDF合计187,812,076字节，约188 MB |','| 资治通鉴TXT | 原件9,394,794字节；识别并拆分294个卷标题；底本未注明 |','| 五代会要 | 30卷及提要，31个文本文件，Kanripo WYG |','| 十国春秋 | 114卷及卷首，115个文本文件，Kanripo WYG |','| 吴越备史 | 4个文本文件，Kanripo SBCK |','| 蜀梼杌 | 上下卷、提要、后序，4个文本文件，Kanripo WYG |','| 马氏南唐书 | 30卷及卷首，31个文本文件，Kanripo SBCK |','| 陆氏南唐书 | 17个文本文件，内部含本纪3卷、列传15卷及序、音释；同号纪传合并在文件中，Kanripo SBCK |','| 北梦琐言 | 20卷及卷首，21个文件，Kanripo WYG；另存Gutenberg全文副本 |','| 五代史补 | 已取得含五卷的全览文本，维基文库四库全书本电子转录 |','','WYG、SBCK是来源仓库的版本声明，分别为文渊阁四库全书、四部丛刊。保留原文元数据与页码标记，但本轮没有对照相应底本书页校勘。','','## 核验结果','']+['- '+c for c in checks]+['','## 重要发现与限制','','- PDF抽查显示旧五代史为现代电子排印版，可提取文字；首尾抽查没有确认出版版本，不能标为古籍影印或某出版社点校本。','- 用户TXT正文存在明显疑似转录异常，例如部分卷首“起”作“赵”或“趣”；原件保留，作为待核问题，不自动订正。','- 294个卷标题仅证明结构检查通过，不能证明每卷无删节或错字；末卷含进书表等附文。','- 维基文库采集遇429限流后停止。已下载页面见catalog/wikisource-downloaded-pages.json；旧分卷采集记录中的失败项属于该来源的副本缺口，主资料已由Kanripo或合并文本补足。','- 十国春秋是后世汇编；五代史补、北梦琐言有笔记性质，后续逐条核对，不把重复转引视作独立证据。','- 已建立书籍级时代标签与后梁工作分期，尚未给所有正文段落精确断代，也未生成或发布新的人物、关系、事件。','','## 下一步','','从907—908年开始：通鉴卷266及267的908年段，配合新旧五代史对应本纪、列传。按PROCESSING.md生成原文对照稿和草稿JSON；审阅后走现有导入流程。']
(B/'COLLECTION_REPORT.md').write_text('\n'.join(summary)+'\n');print('Validated',len(books),'unique works;',len(wiki),'Wikisource snapshots')
