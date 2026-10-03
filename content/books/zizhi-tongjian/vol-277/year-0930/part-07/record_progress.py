# -*- coding: utf-8 -*-
"""Close 930 only after a full anonymous year audit, then move to pending 931."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');proof=read(YEAR/'year-audit.json');nxt=YEAR.parent/'year-0931';nr=read(nxt/'paragraphs.json')
assert proof['verified'] and proof['year_complete'] and proof['body_paragraphs']==55 and proof['next_paragraph']==nr[0]['id']
assert len(rows)==55 and all(x['status']=='published_verified' for x in rows)
assert len(nr)==50 and all(x['status']=='pending' and not x['event_keys'] for x in nr)
assert len(proof['batch_sha256'])==7
for part in sorted(YEAR.glob('part-*')):
 b=read(part/'content-batch.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert proof['batch_sha256'][b['batch_key']]==sha
 for name in ['publication.json','readback-audit.json']:
  d=read(part/name);assert d['verified'] and d['batch_sha256']==sha
progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[48]['id'],nr[0]['id']];rel=str(P.relative_to(ROOT))
y=next(x for x in progress['year_coverage'] if x['year']==930)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',completed_volumes=[277],note='卷277长兴元年原6—60行55正文段、7批连续发布；全年逐字来源、固定链接、公开UUID及引用关系匿名读回通过。追叙与异说保留原时，卷277后续931/932尚待，非全卷读完。')
if not any(x['year']==931 for x in progress['year_coverage']):progress['year_coverage'].append(dict(year=931,status='in_progress',volumes=[277],batches=[],completed_volumes=[],note='卷277原63—112行50正文段已建待录入账本；尚无本年已发布批次。'))
progress['active_cursor'].update(volume=277,year=931,last_reviewed_paragraph=rows[-1]['id'],last_published_paragraph=rows[-1]['id'],next_paragraph=nr[0]['id'],next_paragraph_opening=nr[0]['text'],batch=rel,status='in_progress')
for n,key in [(50,'bei_reporting_and_retrospective'),(51,'jianzhou_battle_scope'),(54,'an_departure_date')]:
 full='930-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=931,current_volumes=[277],current_batch=rel,next_paragraph=nr[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=930,completed_paragraphs=55,volume_total_paragraphs=55,year_completed_paragraphs=55,year_total_paragraphs=55,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=True,year_complete=True,next_paragraph=nr[0]['id'],next_volume=277,next_year=931,year_audit='year-audit.json',batch_sha256=proof['batch_sha256'],anonymous_readback_verified=True))
bd=read(YEAR/'boundaries.json');bd['note']='930年原6—60行55正文段、7批连续公开并完成全年匿名证据核验；61—62行年界不计正文。931/932全卷后段未完成。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 930年 · part-07

连续第49—55段，原54—60行：20事件、29人物参与、86事实引用，8人物全部复用；8来源（6新增、2复用）。补证旧、新五代史及辽史。

马希声袭位撤国制、东丹王渡海、十二月石抵关与剑州山桥战、夔州报复开、马加衔、安重诲赴督战及夔州戍兵纵归，依序分录。突欲沿耶律倍，辽倍传密召刻诗携书为未独年的补证，年字段留空；辽十一月戊寅是东丹奏报，不作登州或洛阳到达日。旧青州转登奏与辽东丹奏视角分别保留。

五百善射分队、百余俘斩合数不可加倍。新概剑门与主详剑州山桥同战层次差；王晖沿前陵州主体。癸卯开州为奏闻日。安主壬子请、癸丑行，旧甲寅遣且翌日行日期差保留。运输石斗比不作财政精确常数，人畜死亡无确数。帝拟自行非已亲征、颇然非已诏全撤，新三泉召还后段未提前。纵归一千五百不等全部三万戍蜀军。

原文快照保留底本字形，展示简体。匿名公开UUID、source关联、逐字引用与固定链接核验通过。930年55/55段及七批全年证据审计完成，卷277其后年度尚待。

下一段zztj-v277-y0931-p001；目标继续至936年后唐灭亡。
''')
(YEAR/'README.md').write_text('''# 《资治通鉴》卷277 · 930年

长兴元年原6—60行55正文段，七批均已公开并通过全年匿名证据核验。史料异文、身份待考与未知年份追叙分别保留。

61—62行分隔及931标题不计930正文。全年完成不等卷277全卷读完；下一段zztj-v277-y0931-p001，931年首段孟知祥奉表谢。
''')
print(dict(year=930,complete=True,paragraphs=55,next_year=931,next_paragraph=nr[0]['id']))
