# -*- coding: utf-8 -*-
"""Record publication of the 24-paragraph prefix, keeping year 925 incomplete."""
import hashlib
import json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(p for p in P.parents if (p/'content/yearly-progress.json').exists())
YEAR=P.parent
def read(p):return json.loads(p.read_text())
def write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
ledger=read(YEAR/'paragraphs.json')
raw=(ROOT/'resources/derived/tongjian/274.txt').read_text().splitlines()
assert len(ledger)==30 and all(x['text']==raw[x['source_line']-1] for x in ledger)
assert all(x['status']=='published_verified' for x in ledger[:24])
assert all(x['status']=='pending' for x in ledger[24:29])
assert ledger[29]['status']=='excluded_non_body_verified'
old=read(ROOT/'content/books/zizhi-tongjian/vol-273/year-0925/paragraphs.json')
assert len(old)==37 and all(x['status']=='published_verified' for x in old)
parts=[];covered=[];totals={'events':0,'claims':0}
for part in [YEAR/'part-01',P]:
 batch=read(part/'content-batch.json');pub=read(part/'publication.json');cov=read(part/'coverage.json')
 sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 assert pub['verified'] and pub['batch_sha256']==sha
 covered+=cov['paragraphs']
 assert {k for x in ledger if x['id'] in cov['paragraphs'] for k in x['event_keys']}=={x['key'] for x in batch['events']}
 for x in read(part/'sources/manifest.json'):
  assert hashlib.sha256((part/'sources'/x['file']).read_bytes()).hexdigest()==x['sha256']
 parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(batch[k])
assert covered==[x['id'] for x in ledger[:24]]
rel=str(P.relative_to(ROOT));next_row=ledger[24]
progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (ledger[12]['id'],next_row['id'])
progress['active_cursor'].update(volume=274,year=925,last_reviewed_paragraph=ledger[23]['id'],last_published_paragraph=ledger[23]['id'],next_paragraph=next_row['id'],next_paragraph_opening=next_row['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==925)
assert year['completed_volumes']==[273]
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',note='925年卷273全部37段与卷274前24段已连续发布并匿名读回，共61/66正文段；卷274尚余5正文段，第30项为已核结构标题，全年未完成。')
followups=[
 ('zongbi-clan-execution',13,'主书十二月己巳族诛宗弼宗勋宗渥，新本纪承十一月叙次且宗训字异；独立保存两书日期与人名字形。新郭传弟称法未当确定血亲。'),
 ('zengcheng-marriage',18,'主书925年汉主以女增城公主妻之，新史七年叙次、隐女增城县主妻旻；婚配郑旻明确，不误配郑昭淳，未确定父女边；父系、爵号和年份待纸本。'),
 ('famine-glyphs',17,'租唐使/吏座/恿悍为底本疑字，旧史租庸使及吏士可补核；原字留存，不把疑字当正常繁简对应。'),
 ('gaowanxing-office',23,'高万兴兼史书令疑中书令，保留原字待校；高允韬留后与926正授分开。'),
 ('shenzhi-posthumous-glyph',14,'新史謚日忠懿之日疑曰，原文保留，谥号用两书相应记载，卒日不是授谥日。'),
]
for suffix,n,note in followups:
 key='925-v274-'+suffix
 if not any(x['key']==key for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=key,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=274,current_year=925,current_volumes=[273,274],current_batch=rel,next_paragraph=next_row['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=274,year=925,completed_paragraphs=24,volume_total_paragraphs=29,ledger_items=30,excluded_non_body=1,year_completed_paragraphs=61,year_total_paragraphs=66,next_paragraph=next_row['id'],next_volume=274,continuous_prefix_verified=True,volume_complete=False,year_complete=False,batches=parts,batch_totals=totals))
(YEAR/'README.md').write_text('# 《资治通鉴》卷274 · 925年\n\n本卷同光三年正文29段（原文件6—34行），前24段已连续发布并匿名读回。账本第30项为926年的章节标题，保留稳定ID，已核为非正文结构项。\n\n925年跨卷273、274，共66正文段，目前完成61段；下一段zztj-v274-y0925-p025，尚余5正文段，全年未完成。\n')
(P/'README.md').write_text('# 《资治通鉴》卷274 · 925年 · part-02\n\n连续处理p013—p024，已发布并匿名读回。41个事件（其中银枪军收编复用915年旧事件）、71条参与、216条事实引用；新增7人及增城公主—妻子→郑旻、高万兴—父亲→高允韬两条关系。王审知—父亲→王延翰复用。\n\n补证《旧五代史》卷33、34、57，《新五代史》卷5、24、65、68。宗弼族诛月份与宗训/宗勋字异各存；承休受诘死万人是问讯结论，不从撤军人数差值独立确证。史彦琼为伶官，未按监军惯例误判宦官。\n\n增城婚配主句省对象，新史明确郑旻，并记刘隐女、增城县主、七年叙次；婚配对象明确但未建立确定父女边，年份爵号异说保留。主书记925年末；不将郑昭淳使者误作夫君。\n\n银枪军近八千为追叙收编补证，未另造925年收编；军荒年概述、等漕粮、冬猎扰民与财政议论分开。租唐使、吏座、恿悍、史书令等底本字保留待核。李琪改革敕令不等已经落实，赴汴只是拟议并因谏停止。\n\n下一段zztj-v274-y0925-p025，925年完成61/66正文段。\n')
print(dict(next_paragraph=next_row['id'],year_progress='61/66',verified=True))
