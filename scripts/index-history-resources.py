"""Index supplied Tongjian without rewriting it; inspect PDFs and extract the two Five Dynasties histories."""
import hashlib,json,pathlib,re
from pypdf import PdfReader
ROOT=pathlib.Path(__file__).resolve().parents[1]; BASE=ROOT/'resources'
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
p=next(BASE.glob('*资治通鉴*.txt')); raw=p.read_bytes();text=raw.decode('utf-8-sig').replace('\r\n','\n'); starts=list(re.finditer(r'^([一二三四五六七八九十百]+)\n',text,re.M));assert len(starts)==294
body_start=text.index('========正文========')+len('========正文========'); groups=list(re.finditer(r'^([^\n]{1,6}纪)\n一\n',text,re.M))
nums={'零':'0','〇':'0','一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9'}
records=[]
for i,m in enumerate(starts):
 end=starts[i+1].start() if i+1<len(starts) else len(text)
 dyn=next((g.group(1) for g in reversed(groups) if g.start()<m.start()),None)
 chunk=text[m.start():end]; years=[]
 for ym in re.finditer(r'公元(前?)([零〇一二三四五六七八九]+)年',chunk):
  n=int(''.join(nums[c] for c in ym.group(2)));years.append(-n if ym.group(1) else n)
 # Preserve exact normalized-source offsets; boundaries may include the next dynasty heading.
 out=BASE/'derived/tongjian'/f'{i+1:03d}.txt';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(chunk)
 records.append(dict(volume=i+1,heading=dyn+m.group(1),file=str(out.relative_to(ROOT)),source_file=str(p.relative_to(ROOT)),normalized_start=m.start(),normalized_end=end,year_start=min(years) if years else None,year_end=max(years) if years else None,year_basis='电子文本内公元纪年标记；未校勘',sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
save(BASE/'catalog/tongjian-volumes.json',records)
save(BASE/'catalog/tongjian-user-file.json',dict(title='资治通鉴',file=str(p.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),encoding='UTF-8',recognized_volume_headings=len(starts),source='用户提供；文件自称爱上阅读www.isyd.net',edition_status='底本未注明；识别出294卷标题不等于无缺字错字',accessed_at='2026-09-29',notes=['原文件未修改','分卷按标题顺序编号；保留原文本字符，卷界可能附带下一纪标题','末卷含进书表等附文；后续正文分析需分开']))
results=[]
for p in sorted((BASE/'originals/twenty-four-histories').glob('*.pdf')):
 try:
  reader=PdfReader(p);first=reader.pages[0].extract_text() or '';last=reader.pages[-1].extract_text() or ''
  row=dict(file=str(p.relative_to(ROOT)),title=p.stem[2:],pages=len(reader.pages),first_page_sample=first[:700],last_page_sample=last[-350:],status='parsed',edition_status='电子PDF；底本与转录质量未校勘')
  if '五代史' in p.name:
   out=BASE/'derived/twenty-four-histories'/p.with_suffix('.jsonl').name;out.parent.mkdir(parents=True,exist_ok=True)
   with out.open('w') as f:
    for n,page in enumerate(reader.pages,1):f.write(json.dumps(dict(pdf_page=n,text=page.extract_text() or ''),ensure_ascii=False)+'\n')
   row['extracted_pages_file']=str(out.relative_to(ROOT));row['edition_status']='已抽查为电子排印本；无已确认刊本版本信息'
  results.append(row);print('PDF',p.name,len(reader.pages),flush=True)
 except Exception as e:results.append(dict(file=str(p.relative_to(ROOT)),status='failed',error=str(e)))
save(BASE/'catalog/pdf-inspection.json',results)
print('Tongjian volumes',len(records),'PDFs',len(results),flush=True)
