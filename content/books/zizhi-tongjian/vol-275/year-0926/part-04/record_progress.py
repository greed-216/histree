# -*- coding: utf-8 -*-
"""Record a verified continuous 79-paragraph prefix of year 926."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
previous=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926'
a=read(previous/'paragraphs.json');b=read(P.parent/'paragraphs.json')
assert len(a)==43 and len(b)==67
assert all(r['status']=='published_verified' for r in a+b[:36])
assert all(r['status']=='pending' for r in b[36:])
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
assert len(parts)==9 and covered==[r['id'] for r in a+b[:36]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[24]['id'],b[36]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=b[35]['id'],last_published_paragraph=b[35]['id'],next_paragraph=b[36]['id'],next_paragraph_opening=b[36]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段及卷275第1—36段共79段九批连续发布并匿名回查。卷275余31段待录，全年未完成。')
for key,n,note in [
 ('enduan-and-restoration',26,'主安奏设端明与旧正文新职两证，夹注五代会要暂不新增；朱宫爵疑官爵原字留，准归葬与财产返还不推已全部实施。'),
 ('bian-mutiny-identities',29,'李彦饶据新符同职同汴州高逖张谏韦俨事校符彦饶；主曹刺史/新后迁叙次保留；弟至彦超方向，主新伏甲日序不同。'),
 ('bian-mutiny-numbers',29,'主张谏四人、张审琼众四百、新四百余与孔三千家、旧三千人并族诛分阶段单位各存，不加成死亡总数；不以众死推审琼具名死亡。'),
 ('maquan-identity',30,'前蜀永平节度使兼侍中马全原文及不食卒事件保留，暂未获两史同事异名确证，不建或合人物，不并马全节马賨王宗俦。'),
 ('taboo-glyph-and-lijiyan',32,'主乙巳与旧条己巳分记；二名是嗣源二字不连称可不避。李继拆字沿既有曮及新从曮同华州凤翔柴事校，西归追叙不强六月日。'),
 ('mayan-execution-and-edict',36,'主安杀马延未具日、新七月庚申御史台门分引；李琪奏及安奏帝敕各事，陵突为诏指控不当误冲就是蓄意犯上。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=926,completed_paragraphs=36,volume_total_paragraphs=67,year_completed_paragraphs=79,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[36]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=b[36]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
(P/'README.md').write_text('''# 《资治通鉴》卷275 · 926年 · part-04

连续第25—36段（原文件30—41行）已发布：27事件、48参与、151引用；新增高逖、符彦饶、张审琼、韦俨、于可洪、马延6个人物，以及符彦饶是符彦超弟弟1条关系。

主线包含王延翰加衔、端明殿学士设置与冯道赵凤任职、郭归葬朱复爵及财产返还、安重诲辞方镇、汴州兵变至平乱与孔循诛族、蜀官到洛、滑州兵变、嗣源名讳敕、孟知祥加衔、李继曮归凤翔与柴重厚实诛、荆南三州诏准、马延被安杀及奏敕。补证来自《旧五代史》卷36及《新五代史》卷6、24、25、40；11个独立来源记录。

汴州调发三千兵、张谏等四人、张审琼众四百、新四百余、孔三千家与旧三千人并族诛分阶段及单位保留，禁止加成总死亡人数。主李彦饶据新符传同职同事校符彦饶，主曹州刺史与新其后历曹州叙次有别；关系弟至兄，不另建反向重复边。张审琼众死不推其本人明死。马全暂缺可靠异名补证，事件保留原名并登记待考，暂不新建或合人物。王锴等授官无个人分配不猜其新职。李继拆字复用既有曮与新从曮，听乱返镇追叙不强定六月戊申后；柴被遣诛与李请贷不许分证。朱宫爵、主乙巳/旧己巳、主马延未具杀日/新七月庚申等原文差异留存。高三州准属不等已占接管；陵突重臣为诏指控，不抹去误冲与安先杀后奏。

来源固定提交、公开ID、引用source ID和URL、快照SHA已逐条匿名回查，见publication.json及readback-audit.json。926年连续完成79/110段，下一段zztj-v275-y0926-p037，全年未完成；目标仍是录至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷275 · 926年

本卷67正文段（原文件6—72行），第1—36段四批已发布并匿名回查，余31段待录；连续前缀、源行、哈希及逐批回查证明见progress-audit.json。

926年含卷274的43段与本卷67段，合计110段，当前完成79段，全年未完成。下一段zztj-v275-y0926-p037。
''')
print(dict(completed=79,total=110,next_paragraph=b[36]['id'],volume_complete=False,year_complete=False))
