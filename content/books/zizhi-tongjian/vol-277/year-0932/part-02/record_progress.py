# -*- coding: utf-8 -*-
"""Advance verified year-932 continuous prefix to paragraph 15; preserve next volume."""
import json, hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==23 and all(x['status']=='published_verified' for x in rows[:15]) and all(x['status']=='pending' and not x['event_keys'] for x in rows[15:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(115,138));assert all(x['text']==lines[x['source_line']-1] for x in rows)
other=YEAR.parent.parent/'vol-278/year-0932';rr=read(other/'paragraphs.json');assert len(rr)==28 and all(x['status']=='pending' and not x['event_keys'] for x in rr)
proof=[]
for path,selection in [(YEAR/'part-01',rows[:10]),(P,rows[10:15])]:
 b=read(path/'content-batch.json');c=read(path/'coverage.json');sha=hashlib.sha256((path/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(path/f);assert d['verified'] and d['batch_sha256']==sha
 assert c['paragraphs']==[x['id'] for x in selection]
 assert {k for x in selection for k in x['event_keys']}=={x['key'] for x in b['events']}
 proof.append(dict(batch=str(path.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
previous=read(YEAR.parent/'year-0931/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==50
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[10]['id'],rows[15]['id']]
progress['active_cursor'].update(volume=277,year=932,last_reviewed_paragraph=rows[14]['id'],last_published_paragraph=rows[14]['id'],next_paragraph=rows[15]['id'],next_paragraph_opening=rows[15]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==932)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[277,278],completed_volumes=[],note='卷277原115—129行连续15段已公开匿名核验；卷277本年余8段、卷278本年28段待录，全年共51段，目前15/51。未标全卷或全年完成。')
for n,key in [(11,'qian_successor_glyph_and_ceremonies'),(12,'captive_identity_and_time'),(13,'bei_marriage_and_requests'),(15,'meng_campaign_order')]:
 full='932-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=932,current_volumes=[277,278],current_batch=rel,next_paragraph=rows[15]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=932,completed_paragraphs=15,volume_total_paragraphs=23,year_completed_paragraphs=15,year_total_paragraphs=51,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[15]['id'],batches=proof,other_volume=dict(volume=278,body_paragraphs=28,completed_paragraphs=0)))
bd['note']='932年卷277原115—137行23正文段，前15段已匿名公开回查，余8待录；同年卷278另28段均待录，全年未完成。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷277 · 932年 · part-02\n\n连续第11—15段、原125—129行。22人物（9新增）、38事件、72参与、2有向关系、191事实引用、13出处（8新增、5复用）；补证《旧五代史》《新五代史》《辽史》。\n\n内容：钱镠临终传位及去世、钱传瓘继业和施政、陆仁章及刘仁𣏌相关争执、契丹俘将求归争议、李赞华授义成及婚配与夏氏请求、宋王加衔、董璋袭西川前期及孟军部署。\n\n钱传瓘与改名元瓘沿同一主体；钱仁俊只录从子。钱卒三月庚戌，旧七月废朝是朝廷通报与哀悼记载，不改死亡月。新袭封玉册金印与主去国仪分层留说。\n\n刘名底本私用区部件按固定同卷文本核字为𣏌；辅助对照在sources/glyph-comparison，史事仍引选定TXT，原文不改，纸本待核。陆前击仁章同段后陆仁章识；荝剌与新萴剌、旧则剌及别赐原知感同案识，不与则骨舍利混。主皆赵擒与新萴王晏球擒差并列；过去俘获不重复建事件。\n\n主初追叙与旧四月定位分别留说；素行、婚配、各次请求及一日等未确年用null。辽婚在赐名之前与主职后叙述顺序差保留。夏氏按庄宗后宫限名，不据辽后字定皇后；奏离婚和求削发仅为请求，未写已批准。条件退归、战略和胜败预测均未写成实际行动。新孟遣三万叙在破汉州后、主在白杨林后，保留相对次序差不提前汉州战果。\n\n展示简体，TXT摘录保持底本；逐条出处固定Git提交。公开UUID、出处关联及SHA匿名核验通过。932年15/51，下一段zztj-v277-y0932-p016；目标仍至936后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷277 · 932年\n\n本卷原115—137行23正文段，part-01第1—10段及part-02第11—15段已公开匿名核验，余8段待录。\n\n932年还含卷278原6—33行28段，全年共51段，目前15/51，全年及全卷未完成。下一段zztj-v277-y0932-p016。\n')
print(dict(year=932,completed=15,total=51,next_paragraph=rows[15]['id'],year_complete=False))
