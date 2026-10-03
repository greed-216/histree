# -*- coding: utf-8 -*-
"""Advance the verified consecutive prefix of 927; do not claim year completion."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
b=read(P.parent/'paragraphs.json');second=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927';c=read(second/'paragraphs.json')
assert len(b)==32 and len(c)==25
assert all(r['status']=='published_verified' for r in b[:6])
assert all(r['status']=='pending' for r in b[6:]+c)
for directory,rows,first,last in [(P.parent,b,75,106),(second,c,6,30)]:
 boundary=read(directory/'boundaries.json');raw=ROOT/boundary['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==boundary['source_sha256']
 assert [r['source_line'] for r in rows]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rows)
sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest();pub=read(P/'publication.json');proof=read(P/'readback-audit.json');cov=read(P/'coverage.json');batch=read(P/'content-batch.json')
assert pub['verified'] and proof['verified'] and pub['batch_sha256']==proof['batch_sha256']==sha
assert cov['paragraphs']==[r['id'] for r in b[:6]]
assert {k for r in b[:6] for k in r['event_keys']}=={x['key'] for x in batch['events']}
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [b[0]['id'],b[6]['id']]
progress['active_cursor'].update(volume=275,year=927,last_reviewed_paragraph=b[5]['id'],last_published_paragraph=b[5]['id'],next_paragraph=b[6]['id'],next_paragraph_opening=b[6]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[],note='927年卷275共32段、卷276共25段，共57正文段；连续前6段已发布并逐条匿名回查，余51段待录，全年未完成。')
for key,n,note in [
 ('liyan-death-month',6,'主正月段、新明宗纪二月、新蜀世家正月互异；新纪壬午朔为来使日不直接当杀日。'),
 ('chancellor-office-glyph',3,'主中书议郎疑侍郎，旧新皆中书侍郎；议事背景不全强归癸亥，崔协暴死是假设、李琪不廉是孔循评价。'),
 ('prisoner-review-proposal-date',5,'旧李同请旬问记在戊辰事项之后，主庚午颁令；建议与敕令阶段分开，不武断同日。'),
 ('liyan-report-and-zhuhongzhao-glyph',6,'孟诬奏之诈口敕优赏仅指控；丁受瘗令不强已葬；硃朱异体同人，弘照疑昭保持原文。')]:
 full='927-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=b[6]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=927,completed_paragraphs=6,volume_total_paragraphs=32,year_completed_paragraphs=6,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[6]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)],batch_totals={k:len(batch[k]) for k in ['events','claims']}))
(P/'README.md').write_text('''# 《资治通鉴》卷275 · 927年 · part-01

连续第1—6段（原文件75—80行）已发布：20事件、50人物参与、126事实引用；6新增人物、14复用人物，7来源（4新增、3复用），补证《旧五代史》《新五代史》。

依次覆盖明宗更名亶、孟知祥迎监军与地方先任李敬周、置相争议及冯道崔协拜相、王延禀返建警告、每旬亲问囚犯、孟杀李严与事后上奏及两位朝使离蜀。李同和王彦铢的补证参与挂接同一事件。

追叙与未定日不强套本日。密诏只是孟自言，李琪不廉与崔协识字少是人物评价，暴死是假设，诬奏中的诈诏不是已核史实。主中书议郎疑侍郎与旧新官名差异、李严主及新世家正月与新纪二月差异并列。新壬午朔不直接作为杀严确日。瘗尸受命不强称已葬。繁简仅用于展示与身份匹配，原文快照不改。

来源快照哈希、公开ID及逐条引用的source ID和固定GitHub URL已匿名回查，见publication.json、readback-audit.json；纸本及异文仍待核。927年完成6/57正文段，下一段zztj-v275-y0927-p007，目标仍为录至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷275 · 927年

本卷32正文段（原文件75—106行），连续第1—6段已发布并匿名回查，余26段待录。927年另含卷276的25段，共57段，目前完成6段，全年未完成。

下一段zztj-v275-y0927-p007。源行、哈希、连续前缀及批次回查证明见progress-audit.json。
''')
print(dict(completed=6,total=57,next_paragraph=b[6]['id'],year_complete=False))
