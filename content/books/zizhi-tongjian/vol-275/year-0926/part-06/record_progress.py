# -*- coding: utf-8 -*-
"""Record a verified continuous 97-paragraph prefix of year 926."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
previous=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926'
a=read(previous/'paragraphs.json');b=read(P.parent/'paragraphs.json')
assert len(a)==43 and len(b)==67
assert all(r['status']=='published_verified' for r in a+b[:54])
assert all(r['status']=='pending' for r in b[54:])
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
assert len(parts)==11 and covered==[r['id'] for r in a+b[:54]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[48]['id'],b[54]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=b[53]['id'],last_published_paragraph=b[53]['id'],next_paragraph=b[54]['id'],next_paragraph_opening=b[54]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段及卷275第1—54段共97段十一批连续发布并匿名回查。卷275余13段待录，全年未完成。')
for key,n,note in [
 ('military-numbers-and-retrospection',49,'郭编蜀骑步两项初追叙未具确年不定926；孟冲山义宁牢城飞棹各营人数及牙罗城分项，不用异时旧新数算全蜀军额。'),
 ('wanggongyan-dates-and-actors',50,'王杀杨复用旧事件；主丁酉/新纪丁未及主旧霍彦威/新符传房知温异说均保留，旧夹注通鉴不作独立确证；族党与八人不合死亡总数。'),
 ('han-ligu-conditional-speech',50,'韩叔嗣是熙载父、韩李为友；将奔吴不等已到国，若用为相对话不等实际拜相或已征服，宋谷后果如言不纳本年。'),
 ('anshentong-border-dates',51,'主庚子与旧事附己亥条但无独立干支，分别定位，未认命御即已战胜。'),
 ('zhaodejun-name-and-yanshou-parentage',53,'主九月癸酉/旧五月甲申复姓日期不同，不造两次；赵养父刘生父公主父及妻分别，背景婚年未知；主刘邟/旧刘邧同子同职同养婚链校同人，原字保留。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=926,completed_paragraphs=54,volume_total_paragraphs=67,year_completed_paragraphs=97,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[54]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=b[54]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)


(P/'README.md').write_text("""# 《资治通鉴》卷275 · 926年 · part-06

连续第49—54段（原文件54—59行）已发布：17个新增事件、1个复用事件，33条人物参与、6条关系、110条事实引用；新增韩叔嗣、韩熙载、李谷、赵延寿、兴平公主、刘邟6个人物，9个来源记录。补证来自《旧五代史》《新五代史》《宋史》。

依次录入郭崇韬此前编蜀骑步军、孟知祥新增冲山义宁牢城和飞棹兵、王公俨求帅拒任至被杀及韩李送别、安审通奉命御契丹、赵德钧复姓名及赵延寿家属背景、马殷加官。王公俨此前杀杨希望复用卷274事件及参与，不复制主体。

旧军新军、营数兵数和牙城罗城州县驻地分项，不计算未经证明的全蜀即时总军额；追叙编营与婚姻确年未载记null。王扬言军情不认全军民真实意见，霍聚兵图取不推已攻克；主丁酉/新丁未、主旧霍彦威/新符传房知温的日期及行动者异说保留。族党与同谋八人的不同统计口径不合死亡总数。韩熙载将奔吴、韩李若为相的对话均保意图而非已到吴任相征服。

赵德钧复姓主九月癸酉/旧五月甲申异记存两证，不建第二人物或第二复姓。赵延寿生父刘邟/旧刘邧同职同子校同人，收养和婚姻分别建边；旧获其母种氏不推德钧已娶其母。各关系按A是B的该身份解释，朋友不凭空转换为兄弟或结义。

宋史电子章节题李濤傳与正文李谷传不符，公开出处标题及两条引用定位已单列content/revisions/2026-10-03-songshi-262-ligu-heading勘误，原批次与原文保持档案可回查。

原文、公开ID及引用source ID和固定GitHub URL已逐条匿名回查，见publication.json和readback-audit.json。926年连续完成97/110段，下一段zztj-v275-y0926-p055，全年未完成；目标仍是录至936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷275 · 926年

本卷67正文段（原文件6—72行），第1—54段六批已发布并匿名回查，余13段待录；连续前缀、源行及哈希、逐批回查证明见progress-audit.json。

926年含卷274的43段及本卷67段，共110段，当前完成97段，全年未完成。下一段zztj-v275-y0926-p055。
""")
print(dict(completed=97,total=110,next_paragraph=b[54]['id'],volume_complete=False,year_complete=False))
