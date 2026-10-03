# -*- coding: utf-8 -*-
"""Advance ten paragraphs in volume 278; count both volumes in the same year."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==28 and all(x['status']=='published_verified' for x in rows[:10]) and all(x['status']=='pending' and not x['event_keys'] for x in rows[10:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(6,34));assert all(x['text']==lines[x['source_line']-1] for x in rows)
oldyear=YEAR.parent.parent/'vol-277/year-0932';orows=read(oldyear/'paragraphs.json');oa=read(oldyear/'progress-audit.json');assert oa['volume_year_complete'] and oa['completed_paragraphs']==21 and oa['year_total_paragraphs']==49
assert all(x['status']=='published_verified' for x in orows[:21]) and all(x['status']=='excluded_non_body_verified' and not x['text'].strip() and not x['event_keys'] for x in orows[21:])
for item in oa['batches']:
 path=ROOT/item['batch'];sha=hashlib.sha256((path/'content-batch.json').read_bytes()).hexdigest();assert sha==item['batch_sha256']
 for f in ['publication.json','readback-audit.json']:
  a=read(path/f);assert a['verified'] and a['batch_sha256']==sha
b=read(P/'content-batch.json');c=read(P/'coverage.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 d=read(P/f);assert d['verified'] and d['batch_sha256']==sha
assert c['paragraphs']==[x['id'] for x in rows[:10]] and {k for x in rows[:10] for k in x['event_keys']}=={x['key'] for x in b['events']}
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[0]['id'],rows[10]['id']]
progress['active_cursor'].update(volume=278,year=932,last_reviewed_paragraph=rows[9]['id'],last_published_paragraph=rows[9]['id'],next_paragraph=rows[10]['id'],next_paragraph_opening=rows[10]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==932)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[277,278],completed_volumes=[277],note='卷277本年21正文段完整公开核验，2空行结构排除；卷278前10段公开核验，余18段待录。全年49正文段，当前31/49；未标全卷或全年完成。')
for n,key in [(2,'qian_zhongshu_shangshu_variant'),(3,'meng_receives_edict_accounts'),(4,'chu_death_and_mourning'),(9,'meng_petition_authority'),(10,'east_troops_retrospective')]:
 full='932-v278-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=278,current_year=932,current_volumes=[277,278],current_batch=rel,next_paragraph=rows[10]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=932,completed_paragraphs=10,volume_total_paragraphs=28,year_completed_paragraphs=31,year_total_paragraphs=49,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[10]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)],previous_volume=dict(volume=277,body_paragraphs=21,completed_paragraphs=21,excluded_non_body_verified=2,audit=str((oldyear/'progress-audit.json').relative_to(ROOT)))))
bd['note']='932年卷278原6—33行28正文段，前10已公开匿名核验，余18待录；卷277同年21正文段全部完成，2空行结构核排。全年49正文，当前31/49，全年未完成。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷278 · 932年 · part-01\n\n连续第1—10段、原6—15行：16人物（潘约1新增）、19事件、31参与、1弟弟关系、102事实引用、8出处（5新增3复用）。补证《旧五代史》《新五代史》。\n\n七月党项奏、钱加衔、李存瑰至成都与回朝、湖南旱闭祠、马希声卒及迎马希范、从珂赵凤出镇、武兴军废、八月希范至长沙袭位、孟墨制表改稿、安重诲东兵布置追叙与兵家属请求分录。\n\n钱元瓘同钱传瓘，主加中书令、旧加守尚书令异官并列，旧元尞疑字保留。李使六月遣、七月到及还、旧九月回报分；主受诏拜泣与新见使倨慢各场景笔法留。主马七月辛卯卒、旧八月己亥废朝不混，迎朗州与八月正式袭位分。新希范弟希声方向明确，同日生不推同母双胞胎；字宝规补。\n\n党项数字为奏报来寇七百、俘五十口径不混，不推康实际领军。废军行政军州层次、安国邢州同治称法保留，不套前干支或确定疆界。五留后草表与李权柄风险、改孟自请各分，请未获准；旧九月回表不是八月草表日。\n\n初布兵及六镇东兵约三万为跨年追叙，已死安夏李只是过去参与，不重复建各镇旧任攻克；兵数不相加。请家属无独日期null，后朝廷不许待续段；新放在长兴四年封王后，层次差留不强改年。展示简体，TXT摘录原字。\n\n匿名公开UUID、出处关联与SHA核验通过。卷277同年21正文加卷278前10，全年31/49；下一段zztj-v278-y0932-p011。目标仍到936后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 932年\n\n原6—33行28正文段；part-01前10段已公开匿名核验，余18段待录。原34分隔、35下一年标题排除见boundaries，未当史事。\n\n卷277同年21正文全部核验且2空行结构排除，全年49正文，目前31/49，尚未完成。下一段zztj-v278-y0932-p011。\n')
print(dict(year=932,completed=31,total=49,next_paragraph=rows[10]['id'],year_complete=False))
