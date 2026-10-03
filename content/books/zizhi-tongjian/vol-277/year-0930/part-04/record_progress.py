# -*- coding: utf-8 -*-
"""Record 35/55 only after two verified consecutive publication batches."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');bd=read(P.parent/'boundaries.json')
assert len(rows)==55 and all(r['status']=='published_verified' for r in rows[:35])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[35:])
raw=ROOT/'resources/derived/tongjian/277.txt';lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(6,61)) and all(r['text']==lines[r['source_line']-1] for r in rows)
assert lines[60]=='◎' and '九三一年' in lines[61]
previous=read(ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/year-audit.json')
assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==36
covered=[];proofs=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:35]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[29]['id'],rows[35]['id']]
progress['active_cursor'].update(volume=277,year=930,last_reviewed_paragraph=rows[34]['id'],last_published_paragraph=rows[34]['id'],next_paragraph=rows[35]['id'],next_paragraph_opening=rows[35]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==930)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原6—40行连续35段、4批已发布并匿名回查；全年55段，余20段待录入。61—62行年界结构不计正文。')
for key,n,note in [
 ('dongguangye_letter_reinforcement',30,'董书驻三千欲杀为其看法，再一骑是条件。旧九月癸未三州报告不是起反确日；旧董五月檄连叙差留。荀咸鹹同名身份，兵未至反补。'),
 ('four_thousand_task',31,'主侯弘实孟思恭四千会董攻阆，新侯四千助守东川，任务及名单异并列，不擅定不同阶段解释。'),
 ('an_retention_not_replacement',32,'请解求镇与帝怒听去皆未实际罢，甲申范真任而安如故；孟汉琼新同名不混其他孟。'),
 ('langzhou_capture_date',33,'主九月庚辰陷，新明纪十月乙巳直接系陷，旧同乙巳为张仁晖回奏，差分别留，不能抹为全同报告日。主重璋疑姓留底本，按董及新传识别。'),
 ('yaohong_execution_family',33,'梁旧部追叙null不作终身董部将；驻千人是状态。投书拒、俘责、斥、刑死和恤分，十人是执行壮士，二子未名不造。董旧李氏为姚话不当今时真实童仆活动。'),
 ('court_nominal_campaign_posts',35,'孟供馈为名义授命不证实际送粮，石权东非实际已克梓，王主右武卫旧右卫异职衔并列；孟思恭攻集败还免未独月日不强嵌两干支之间。')
]:
 full='930-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=930,current_volumes=[277],current_batch=rel,next_paragraph=rows[35]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=277,year=930,completed_paragraphs=35,volume_total_paragraphs=55,year_completed_paragraphs=35,year_total_paragraphs=55,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[35]['id'],batches=proofs))
bd['note']='930年卷277原6—60行55正文段；前35段、4批连续发布并匿名回查，余20段待处理。61—62行分隔及931标题不计正文。';write(P.parent/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 930年 · part-04

连续第30—35段（原35—40行）：44新增事件、85人物参与、223新增事实引用；24人物（7新增）、1新增父亲关系、12来源（9新增、3复用），补证《旧五代史》《新五代史》。新增董光业、李虔徽、荀咸乂、苏愿、孟思恭、孟汉琼、姚洪。

覆盖董光业止兵请求与董反、赵季良攻守计及两川分将出兵、安重诲请解职和中书争议、阆州陷落与李仁矩姚洪之死、范延光并任枢密、朝廷授将讨蜀及集州败将免官。董璋→董光业为父亲。

董书中的驻兵欲杀和再一骑则反归书信说法，条件不当已发生；九月癸未镇报不是起兵确日。三万、四千为原载兵数，四千是侯孟总兵，不各四千。新侯四千助守东川与主会攻阆任务差并列，未擅用阶段解释。

安求解、范辞代、冯赵议论均与后甲申实任分；范任而安如故，不能把怒听去写成正式罢安。主阆州九月庚辰陷，新明纪十月乙巳系陷，旧十月乙巳为张仁晖回奏，分别保留原叙与日期差。主重璋疑姓按董语境与新传识，不改原引，不造另人。

姚的梁旧部关系是追叙未知年，不建终身董部将边。驻兵、拒信、被擒责、斥董、受刑死与帝恤分别录；十人为行刑壮士，二子无名不造实名。新姚与主相近叙法不当两份独立目击口供。集州孟思恭败、被遣回、免职未独月日，免非死。孟供馈、石权东、王前锋均为任命，不证实际粮款到或攻克梓州；王主右武卫旧右卫职衔差原留。

全部快照SHA、逐字引句、公开UUID、source关联与固定GitHub链接回查。展示简体，原文保留繁简字形，电子本异文待纸本校核。

本年完成35/55段；下一段zztj-v277-y0930-p036。继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷277 · 930年

原6—60行55正文段。part-01—04连续第1—35段已发布并匿名回查；余20段待处理，未标全年完成。

第61—62行为年界分隔及931年标题，不计930正文；原文快照保持底本字形。下一段zztj-v277-y0930-p036。
''')
print(dict(completed=35,total=55,next_paragraph=rows[35]['id'],year_complete=False))
