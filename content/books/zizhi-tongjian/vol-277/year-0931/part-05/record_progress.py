# -*- coding: utf-8 -*-
"""Close 931 only after whole-year anonymous evidence verification; advance to pending 932."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');proof=read(YEAR/'year-audit.json');nxt=YEAR.parent/'year-0932';nr=read(nxt/'paragraphs.json')
assert proof['verified'] and proof['year_complete'] and proof['body_paragraphs']==50 and proof['next_paragraph']==nr[0]['id']
assert len(rows)==50 and all(x['status']=='published_verified' for x in rows)
assert len(proof['batch_sha256'])==5
assert proof['next_year_body_paragraphs']==51
for target,size in [(nxt,23),(YEAR.parent.parent/'vol-278/year-0932',28)]:
 rr=read(target/'paragraphs.json');assert len(rr)==size and all(x['status']=='pending' and not x['event_keys'] for x in rr)
for part in sorted(YEAR.glob('part-*')):
 b=read(part/'content-batch.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert proof['batch_sha256'][b['batch_key']]==sha
 for name in ['publication.json','readback-audit.json']:
  d=read(part/name);assert d['verified'] and d['batch_sha256']==sha
progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[40]['id'],nr[0]['id']];rel=str(P.relative_to(ROOT))
y=next(x for x in progress['year_coverage'] if x['year']==931)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',completed_volumes=[277],note='卷277长兴二年原63—112行50正文段、5批连续发布；全年逐字原文、固定出处URL、公开UUID与事实出处关联匿名回查通过。卷277后续932及卷278同年尚待，全年完成不等全卷已读完。')
if not any(x['year']==932 for x in progress['year_coverage']):progress['year_coverage'].append(dict(year=932,status='in_progress',volumes=[277,278],batches=[],completed_volumes=[],note='全年度跨卷277原115—137行23段与卷278原6—33行28段，共51正文段均待录，尚无本年已发布批次。'))
progress['active_cursor'].update(volume=277,year=932,last_reviewed_paragraph=rows[-1]['id'],last_published_paragraph=rows[-1]['id'],next_paragraph=nr[0]['id'],next_paragraph_opening=nr[0]['text'],batch=rel,status='in_progress')
for n,key in [(44,'wanglingmou_left_right'),(46,'ma_funeral_and_pan_title'),(50,'jiaozhou_year_and_viewpoint')]:
 full='931-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=932,current_volumes=[277,278],current_batch=rel,next_paragraph=nr[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=931,completed_paragraphs=50,volume_total_paragraphs=50,year_completed_paragraphs=50,year_total_paragraphs=50,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=True,year_complete=True,next_paragraph=nr[0]['id'],next_volume=277,next_year=932,year_audit='year-audit.json',batch_sha256=proof['batch_sha256'],anonymous_readback_verified=True))
bd=read(YEAR/'boundaries.json');bd['note']='931年原63—112行50正文段、5批连续公开并通过全年匿名原文证据回查；113—114行年界不计正文，932年度两卷仍待录入。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷277 · 931年 · part-05\n\n连续第41—50段，原103—112行：24人物（4新增）、33事件、60人物参与、2父亲关系（1新增、1复用）、168事实引用，8来源（5新增、3复用）。补证《旧五代史》《新五代史》。\n\n日食、苏愿到成都及孟董邀谢再怨、李仁罕归军、吴国辅政父子分工与王宋任相、张崇爵、铁器政令、马殷葬及潘起讥语、徐到金陵、赵让昭武李代、闽预言避位及杨廷艺交州战事逐动作整理。\n\n董族灭与疑刘不闻为董说辞，未独证朝廷隐瞒。新王令谋左仆射、主右仆射官衔差留；宋十一月平章与三月致仕分。张二十余年长期弊政、马日食鸡习惯、杨养假子及李受贿背景未独年，不倒推年份。铁器每二亩三钱与旧每亩一钱五分合，夏秋未解释为全年固定额。\n\n马葬主衡阳、新上潢称法待核；潘主前吏部、新礼部异文留。底本鸡字部件问题保留，展示概括鸡食，未猜菜名；阮籍是讥语典故，不造931古人活动。昭武延隐疑字沿赵廷隐，顷剑州同功仅让任背景。神命六十年是陈守元预言；王继鹏暂掌不当继王已帝，玄锡是王延钧道名。\n\n交州是岁汇记不硬定十二月，养子群体不造3000实体。杨廷艺不混920杨廷式；李进沿930交州守将，不混李进唐。救城、援未至陷城、李逃被杀、程转围、杨出战宝死分阶段；新叛是南汉视角。主证李死、新仅逃，未视沉默为反证。\n\n展示简体，逐字TXT引用保留原字。五批及931年50/50段全年公开UUID、固定出处及引用关系匿名核验通过；卷277后续932尚待。下一段zztj-v277-y0932-p001，932跨277、278两卷51段；目标继续至936年后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷277 · 931年\n\n原63—112行50正文段，part-01—05五批全部发布并通过全年匿名原文证据核验。异文与追叙时间分别保留。\n\n113—114行分隔及932标题不计931正文。全年完成不等卷277全卷已读完；下一段zztj-v277-y0932-p001。932年跨卷277、278，共51段仍待录。\n')
print(dict(year=931,complete=True,paragraphs=50,next_year=932,next_paragraph=nr[0]['id']))
