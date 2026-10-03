# -*- coding: utf-8 -*-
"""Advance only after all 49 body paragraphs of 932 pass annual public audit."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
read=lambda p:json.loads(p.read_text())
def write(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
a=read(YEAR/'year-audit.json');assert a['verified'] and a['year_complete'] and a['body_paragraphs']==49 and a['excluded_ledger_non_body']==2
r=read(YEAR/'paragraphs.json');assert len(r)==28 and all(x['status']=='published_verified' for x in r)
proof=[]
for part in sorted(YEAR.glob('part-*')):
 b=read(part/'content-batch.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert a['batch_sha256'][b['batch_key']]==sha
 for f in ['publication.json','readback-audit.json']:
  c=read(part/f);assert c['verified'] and c['batch_sha256']==sha
 proof.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
next_year=YEAR.parent/'year-0933';nr=read(next_year/'paragraphs.json');assert len(nr)==57 and all(x['status']=='pending' and not x['event_keys'] for x in nr)
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [r[20]['id'],nr[0]['id']]
progress['active_cursor'].update(volume=278,year=933,last_reviewed_paragraph=r[-1]['id'],last_published_paragraph=r[-1]['id'],next_paragraph=nr[0]['id'],next_paragraph_opening=nr[0]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==932)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',volumes=[277,278],completed_volumes=[277,278],note='卷277本年21正文、卷278本年28正文，共49段六批连续公开核验；2空行结构排除。全年逐字摘录、固定出处链接、公开UUID与事实出处关联匿名回查通过。932完成不等卷278后续933、934已完成。')
if not any(x['year']==933 for x in progress['year_coverage']):progress['year_coverage'].append(dict(year=933,status='in_progress',volumes=[278],batches=[],completed_volumes=[],note='卷278原36—92行57个连续正文段，全部待录；下一段zztj-v278-y0933-p001，不跳段。'))
for n,key in [(23,'xu_titles_action_glyph'),(24,'jingda_annal_biography_chronology'),(28,'liuhan_prince_titles')]:
 full='932-v278-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=r[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_year=933,current_volume=278,current_volumes=[278],current_batch=rel,next_paragraph=nr[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
oldyear=YEAR.parent.parent/'vol-277/year-0932'
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=932,completed_paragraphs=28,volume_total_paragraphs=28,year_completed_paragraphs=49,year_total_paragraphs=49,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=True,year_complete=True,next_paragraph=nr[0]['id'],batches=proof,annual_audit=str((YEAR/'year-audit.json').relative_to(ROOT)),previous_volume=dict(volume=277,body_paragraphs=21,completed_paragraphs=21,excluded_non_body_verified=2,audit=str((oldyear/'progress-audit.json').relative_to(ROOT)))))
bd=read(YEAR/'boundaries.json');bd['note']='932年原6—33行28正文段全部发布核验；连同卷277本年21正文，全年49段六批完成，2空行排除。卷278后续933、934未完成；下一段933年原36行。';write(YEAR/'boundaries.json',bd)
# Preserve the prior-volume local cursor as its handoff; attach the complete annual proof.
oa=read(oldyear/'progress-audit.json');oa.update(year_completed_paragraphs=49,year_complete=True,annual_audit=str((YEAR/'year-audit.json').relative_to(ROOT)));write(oldyear/'progress-audit.json',oa)
(P/'README.md').write_text('# 《资治通鉴》卷278 · 932年 · part-03\n\n连续第21—28段、原26—33行：32人物（22新增）、31事件、65参与、20关系、213事实引用、10出处（8新增2复用）。补证《旧五代史》《新五代史》。\n\n河东最后议定与正式授任、赵延寿加官、吴授徐官、防边与蔚州投附、晋阳军财任事、十二月康朱正式任、南汉十九子封王逐动作分录。\n\n北京为后唐北都，不是现代北京。范曾荐石与本次欲用康、李崧坚持及群议归石分别留。朱暂知与十二月正节区别。张敬达主932大同任、旧本纪930由应州移云州与旧传三年应州四年云州的纪传差异并列，不强定每次防边年；补字志通、小字生铁。张彦超沙陀及明宗养子明确，李嗣源→张彦超养父，不猜收养年或生父。投蔚州与契丹授大同分别，不能当已夺张敬达全部军境。\n\n南汉十九子逐人封爵、父亲边有向；弘／洪及各爵名并列，缺字据新洪暐补而原文不改。耀枢主雍正新邕王、弘度主宾后秦新五年直秦、弘暐思／息、弘济辩／辨、弘昭宜／宣留校核。未几改秦年份null。大有928改元见已发布卷276年928part-03事件event_zztj_276_0928_liuyan_changes_era_dayou，新五年与主932对读；纪年上下文另存。吴知诰矢字不靠繁简转换作辞或受，暂不建肯定受辞事件。\n\n简体展示、底本摘录原字，疑字另核。刘岩沿已存UUID，姓名引用支持补齐检索别名字形；修正审计在content/revisions/2026-10-04-liu-yan-name。\n\n本批与全年匿名公开UUID、事实出处关联和快照SHA回查通过。932全年49正文、六批完成，2卷尾空行结构排除。下一段zztj-v278-y0933-p001；933的57连续正文段已建账本且全部待录。目标继续至936后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 932年\n\n原6—33行28正文段，三批全部公开核验；34分隔、35下一年标题排除。卷277同年21正文及2空行已核，932全年49正文、六批完成。全年审计见year-audit.json，全部引用逐字及匿名出处关联核对。\n\n下一段zztj-v278-y0933-p001，933年原36—92行57正文段全部待录。932完成不等卷278后续年份已完成。\n')
(oldyear/'README.md').write_text('# 《资治通鉴》卷277 · 932年\n\n原115—135行21正文段、三批全部公开核验；136、137行卷尾空行保留既有ID，结构排除。卷278同年28正文也全部核验，932全年49正文、六批完成。全年审计见[year-audit.json](../../vol-278/year-0932/year-audit.json)。\n\n下一段zztj-v278-y0933-p001；未将卷278后续年份标为完成。\n')
print(dict(year=932,completed=49,total=49,next_paragraph=nr[0]['id'],year_complete=True))
