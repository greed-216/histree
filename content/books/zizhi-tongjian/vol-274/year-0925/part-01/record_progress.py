"""Record the verified continuous prefix; this is not a full-year audit."""
import hashlib
import json
from pathlib import Path

P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
YEAR=P.parent
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
ledger=read(YEAR/'paragraphs.json')
old=read(ROOT/'content/books/zizhi-tongjian/vol-273/year-0925/paragraphs.json')
assert len(old)==37 and all(x['status']=='published_verified' for x in old)
lines=(ROOT/'resources/derived/tongjian/274.txt').read_text().splitlines()
assert len(ledger)==30 and [x['source_line'] for x in ledger]==list(range(6,36))
assert all(x['text']==lines[x['source_line']-1] for x in ledger)
batch=read(P/'content-batch.json');pub=read(P/'publication.json');coverage=read(P/'coverage.json')
sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert pub['verified'] and pub['batch_sha256']==sha
assert coverage['paragraphs']==[x['id'] for x in ledger[:12]]
assert all(x['status']=='published_verified' and x['batch_key']==batch['batch_key'] for x in ledger[:12])
assert {k for x in ledger[:12] for k in x['event_keys']}=={x['key'] for x in batch['events']}
assert all(x['status']=='pending' for x in ledger[12:29])
assert ledger[29]['status']=='excluded_non_body_verified' and ledger[29]['kind']=='section_heading'
for x in read(P/'sources/manifest.json'):
 assert hashlib.sha256((P/'sources'/x['file']).read_bytes()).hexdigest()==x['sha256']
rel=str(P.relative_to(ROOT))
progress=read(ROOT/'content/yearly-progress.json')
cursor=progress['active_cursor']
assert cursor['next_paragraph'] in (ledger[0]['id'],ledger[12]['id'])
cursor.update(volume=274,year=925,last_reviewed_paragraph=ledger[11]['id'],last_published_paragraph=ledger[11]['id'],next_paragraph=ledger[12]['id'],next_paragraph_opening=ledger[12]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==925)
assert year['completed_volumes']==[273]
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',note='925年卷273全部37段与卷274前12段已连续发布并匿名读回；合计49/66正文段，卷274尚余17正文段。原账本第30项为926年章节标题，已核作结构项，不生成事件；全年未完成。')
followups=[
 ('surrender-locations',9,'升迁桥、两史升仙桥及新蜀世家七里亭分别保留；未证同一位置，不设现代坐标。'),
 ('surrender-dates-duration',9,'至城乙卯、出降丙辰、军入丁巳分录；新继岌传丙辰入成都及十月己酉绵州与主书十一月不同；七十/七十五日各书统计端点保留，待纸本。'),
 ('zongshou-prefectures',2,'主书遂合渝泸昌、旧史遂合渝泸忠，名单各五州，不能并成六州。'),
 ('palace-names',3,'主书大玄门、新史太玄门；迁宫主西宫、旧西宅、新天启宫；不自动纠字或认两次迁宫。'),
 ('lugantou-glyph',4,'主书句末鹿关头疑倒字，同段前文及两史鹿头关佐证，展示鹿头关，原字留存待纸本。'),
 ('wangkai-office',6,'王锴中书待郎疑侍郎，底本原字保留，不按繁简转换静默改官称。'),
 ('zongbi-kinsmen',12,'新史郭传称王衍弟宗弼，与既有宗弼出身、养子记法待核；未新建确定兄弟边。承涓与承班为主书不同人物，不自动并作异名。'),
]
for suffix,n,note in followups:
 key='925-v274-'+suffix
 if not any(x['key']==key for x in progress['editorial_followups']):
  progress['editorial_followups'].append(dict(key=key,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
index=read(ROOT/'content/books/zizhi-tongjian/index.json')
index.update(current_volume=274,current_year=925,current_volumes=[273,274],current_batch=rel,next_paragraph=ledger[12]['id'])
write(ROOT/'content/books/zizhi-tongjian/index.json',index)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=274,year=925,completed_paragraphs=12,volume_total_paragraphs=29,ledger_items=30,excluded_non_body=1,year_completed_paragraphs=49,year_total_paragraphs=66,next_paragraph=ledger[12]['id'],next_volume=274,continuous_prefix_verified=True,volume_complete=False,year_complete=False,batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)],batch_totals=dict(events=len(batch['events']),claims=len(batch['claims']))))
(YEAR/'README.md').write_text('# 《资治通鉴》卷274 · 925年\n\n本卷同光三年正文29段，来源文件第6—34行。账本保留30个稳定ID，第30项（原文件35行）为926年的章节标题，已标为结构项，不生成史事。前12段已连续录入、发布并匿名读回；下一段zztj-v274-y0925-p013，尚余17正文段。\n\n925年跨卷273、274，共66正文段，目前完成49段；须两卷正文全部发布并读回后才记全年完成。\n')
(P/'README.md').write_text('# 《资治通鉴》卷274 · 925年 · part-01\n\n连续处理p001—p012，已发布并匿名读回。43个事件、93条人物参与、242条事实引用；新增王承涓、李昊、郭廷诲3人，以及王宗弼—父亲→王承涓、郭崇韬—父亲→郭廷诲两条关系。王宗弼—父亲→王承班沿用既有关系。\n\n补证来自《旧五代史》卷33、57、74、136，《新五代史》卷14、24、44、63与《宋史》卷479。李昊字、出生地与翰林身份有补充出处；自言李绅后裔未当作已核定血亲。\n\n请降、正式出降、解缚释罪与军队入城分开；求官与表奏不混为正式诏任。昌/忠、宫门宫名、升迁桥/升仙桥/七里亭、绵州十月/十一月、七十/七十五日等异说并列。鹿关头按同段前文与两史显示鹿头关，逐字引用仍留原字；中书待郎待纸本校核。\n\n康延孝威胁斩董与郭崇韬反邪质问未录成已斩、已反。梁震预测和马殷愿退未当已发生结果。市场未改和新史兵不血刃评价未用于否定主书渡江损失。\n\n下一段zztj-v274-y0925-p013，925年完成49/66正文段，尚未完成。原账本第30项为926年章节标题，已校作非正文结构项。\n')
print(dict(next_paragraph=ledger[12]['id'],year_progress='49/66',verified=True))
