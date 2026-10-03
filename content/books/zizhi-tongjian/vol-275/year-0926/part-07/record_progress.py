# -*- coding: utf-8 -*-
"""Record a verified continuous 103-paragraph prefix of year 926."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
previous=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926'
a=read(previous/'paragraphs.json');b=read(P.parent/'paragraphs.json')
assert len(a)==43 and len(b)==67
assert all(r['status']=='published_verified' for r in a+b[:60])
assert all(r['status']=='pending' for r in b[60:])
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
assert len(parts)==12 and covered==[r['id'] for r in a+b[:60]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[54]['id'],b[60]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=b[59]['id'],last_published_paragraph=b[59]['id'],next_paragraph=b[60]['id'],next_paragraph_opening=b[60]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段及卷275第1—60段共103段十二批连续发布并匿名回查。卷275余7段待录，全年未完成。')
for key,n,note in [
 ('deguang-succession-chronology',55,'主926年九月条/辽天显二年927冬十一月即帝与十二月尊后不同；辽倍请立/主倍欲奔不同，年界上下文逐字保存。'),
 ('xiaowen-kinship-and-marriage-stages',55,'主述后侄辈皇后据辽太宗妃及后弟室鲁女识别萧温；妻与姑母方向明确，辽大元帅纳妃/即位立后不等主本年首次婚。'),
 ('hanyanhui-and-yaokun-stages',55,'主韩任政事令与辽太祖前已有同职各引，未认首次；姚主继统后听归/旧先归后继统/新同西楼回程存先后异说，告哀日不是阿保机死日。'),
 ('lijiyan-rename-days-and-private-glyph',56,'主九月壬午/旧辛巳赐从字日异，拆字沿已有凤翔曮主体不并客省使李严，制书猶子不造真实收养。'),
 ('yanhan-zhaowu-glyph-and-king-title',58,'主昭武节度疑威武沿旧主体原字留；称大闽国王非唐册王，新仍稟唐正朔；赦不推所有罪免，追尊父不改925卒。'),
 ('maozhang-transfer-origin',59,'主静难旧邠州到昭义/新传华州到昭义同边蔚拒命说谕事留出发地异，李副使旧泾州与毛邠州留异，不造第二调任或已叛乱，久之接受不强壬辰同日。'),
 ('luwenjin-return-chronology-and-numbers',60,'主卢文时疑文进同段同旧帝纪校同人；主旧纪926/旧本传即位明年927异记保留，同事件不复制。主十余万人八千车/旧表十五万七八千车/新数万分说，不当战兵总数；奏表十月10决计11离14至属自述。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=926,completed_paragraphs=60,volume_total_paragraphs=67,year_completed_paragraphs=103,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[60]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=b[60]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)



(P/'README.md').write_text("""# 《资治通鉴》卷275 · 926年 · part-07

连续第55—60段（原文件60—65行）已发布：23事件、42参与、136事实引用；新增萧温、阿思没骨馁、边蔚3个人物；新增3条关系并复用王审知父亲至王延翰1条；19来源，补证《旧五代史》《新五代史》《辽史》。

依次处理契丹继统拥立、倍未遂奔唐、尊母立后与母子姑侄婚姻、德侍母概述、韩政事令、姚坤还唐和没骨馁告哀、李继曮赐名、百官赐衣、王延翰称王及官制赦令追尊、毛璋调任受代、卢文进杀戍归附。

主契丹继位编926年，辽正式帝位天显二年927十一月、十二月尊母册后各存；辽年界标题和相邻明年秋已逐字导出并校哈希。倍未遂奔唐不提前930实奔。萧温据辽同太宗配偶及述后弟女识别，妻子和姑母方向明确；元帅纳妃与即位立后有不同阶段，不强认926才首次成婚。德孝谨侍母属史书概述；韩在太祖先有政事令不认本段为首次任相；姚归与德立在主旧的先后差异保留，告哀来朝日与阿保机卒日分开。

李继拆字沿既有曮及从曮，不并客省使李严，主壬午与旧辛巳存日异。主王昭武节度疑威武原字保留，建国称王仍奉唐正朔，未说唐已册此号；百官、境内赦不外推精确人数和刑种。毛静难邠州与新华州出发镇、李副使旧泾州名称异说保留；欲拒诏与久之受代不是当天已经举兵叛乱。

卢文时据同段文进及旧纪同职同事件校疑字，不新建重复人物。旧本传明宗即位明年与主旧纪926不同，作为同事件日期异说；十余万人八千车、旧表十五万七八千车、新数万各存，自述人数不当实测战兵总额。旧奏10日决计、11离州、14至幽属卢上表所称，丁未队伍约七十里不换算现代精确里程。

来源、原文及年界上下文哈希、公开ID和逐条引用source ID与固定GitHub URL均匿名回查，见publication.json与readback-audit.json。926年连续完成103/110段，下一段zztj-v275-y0926-p061，全年未完成；目标仍为录至936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷275 · 926年

本卷67正文段（原文件6—72行），第1—60段七批已发布并匿名回查，余7段待录；源行和哈希、连续前缀及逐批回查证明见progress-audit.json。

926年含卷274的43段与本卷67段，共110段，目前完成103段，全年未完成。下一段zztj-v275-y0926-p061。
""")
print(dict(completed=103,total=110,next_paragraph=b[60]['id'],volume_complete=False,year_complete=False))
