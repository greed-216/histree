# -*- coding: utf-8 -*-
"""Record a continuous 49-paragraph prefix across volumes 274 and 275."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
previous=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926'
a=read(previous/'paragraphs.json');b=read(P.parent/'paragraphs.json')
assert len(a)==43 and len(b)==67
assert all(r['status']=='published_verified' for r in a+b[:6])
assert all(r['status']=='pending' for r in b[6:])
parts=[];covered=[];totals={'events':0,'claims':0}
for directory,rows,first,last in [(previous,a,38,80),(P.parent,b,6,72)]:
 raw=ROOT/read(directory/'boundaries.json')['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==read(directory/'boundaries.json')['source_sha256']
 assert [r['source_line'] for r in rows]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rows)
 for part in sorted(directory.glob('part-*')):
  data=read(part/'content-batch.json');pub=read(part/'publication.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
  assert pub['verified'] and pub['batch_sha256']==sha
  proof=read(part/'readback-audit.json');assert proof['verified'] and proof['batch_sha256']==sha
  ids=read(part/'coverage.json')['paragraphs'];covered+=ids
  assert {k for r in rows if r['id'] in ids for k in r['event_keys']}=={r['key'] for r in data['events']}
  parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
  for k in totals:totals[k]+=len(data[k])
assert len(parts)==6 and covered==[r['id'] for r in a+b[:6]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[0]['id'],b[6]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=b[5]['id'],last_published_paragraph=b[5]['id'],next_paragraph=b[6]['id'],next_paragraph_opening=b[6]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段及卷275第1—6段共49段六批连续发布并匿名回查。卷275余61段待录，全年未完成。')
for key,n,note in [
 ('palace-mutiny-and-date',1,'主黄甲同攻、新与黄甲相射；主丁亥朔、旧庄宗丁丑朔及旧明宗丁亥朔各存，原文不改；未推郭亲射或进酪毒杀。'),
 ('fu-siblings-and-cunwo',1,'李彦卿据同父与宋同宫城王全斌守卫校符彦卿；李彦超据新同北京巡检及旧本人还符姓校符彦超。申王存屋据旧同申王刘后逃太原校李存渥。'),
 ('arrival-glyph',1,'主乙丑入洛与前戊子后庚寅不顺，旧明宗及新明宗记己丑；主乙保留，异文单独引用。'),
 ('shanyou-and-consorts',1,'善友只名未具姓不并振武石善友；韩淑妃复用既有韩夫人、伊德妃独立于梁张德妃及蜀徐淑妃。'),
 ('jinyang-and-zhangxian',5,'吕郑内养只有姓、具体各人监兵监库未载，不并吕知柔；李存沼近属不推具体家属。张昭远据宋本名校五代宋初张昭；主忻州/新沂州及存霸到晋阳时序保留，张宪之死留待主后段。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=926,completed_paragraphs=6,volume_total_paragraphs=67,year_completed_paragraphs=49,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[6]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=b[6]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
(P/'README.md').write_text('''# 《资治通鉴》卷275 · 926年 · part-01

连续第1—6段（原文件6—11行）已发布：29事件、68参与、182引用；新增11个人物、2条有方向的人物关系。

以主书四月兴教门兵变、庄宗遇害、诸王出逃、李嗣源入洛、元行钦被执、魏王退军、凤翔康延孝实诛、晋阳事变与监国释宫人为连续主线。补证来自《旧五代史》卷34、35、38、51、74、《新五代史》卷6、14、25、28、37及《宋史》卷255、263。

李彦卿/符彦卿、李彦超/符彦超依同父同职同事校同人；符存审是符彦卿的父亲，符彦超是其兄长，按方向建边。善友只名未载姓，不并早年振武将石善友；申王存屋据旧宗室同申王同刘后出奔校李存渥。淑妃韩氏复用韩夫人，德妃伊氏不并梁张氏或蜀徐氏。吕郑两内养只据姓与晋阳内养分人，未擅配具体分工；张昭远据宋本名合为五代宋初张昭。

主丁亥朔与旧庄宗丁丑朔、主乙丑入洛与两史己丑、黄甲同攻与新相射、张宪忻州/新沂州及存霸时序各存原字及独立引用。未知射手、进酪不推亲射或毒杀；元行钦被执未提前录死，魏王谋凤翔未当已占，晋阳密谋与军士实际诛杀分开。监国与正式即位分阶段。来源快照、引文保留原字，展示与身份匹配用简体。

publication.json及readback-audit.json确认公开ID、对应source ID、原文快照哈希和固定URL逐条可回查。926年已连续完成49/110段，下一段zztj-v275-y0926-p007；全年及本卷未完成。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷275 · 926年

本卷67正文段（原文件6—72行），第1—6段一批已发布并匿名回查，余61段待录；连续前缀、源行、哈希及逐批回查证明见progress-audit.json。

926年含卷274的43段与本卷67段，合计110段，当前完成49段，全年未完成。下一段zztj-v275-y0926-p007。
''')
(previous/'README.md').write_text('''# 《资治通鉴》卷274 · 926年

本卷43正文段（原文件38—80行）五批全部发布并匿名读回；连续覆盖、原文源行、哈希、结构行及逐批发布证明见progress-audit.json。

926年另含卷275的67段，全年共110段。主线已进入卷275，当前完成范围与下一段以content/yearly-progress.json为准。
''')
print(dict(completed=49,total=110,next_paragraph=b[6]['id'],volume_complete=False,year_complete=False))
