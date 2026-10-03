# -*- coding: utf-8 -*-
"""Advance a consecutive ten-paragraph prefix; retain both volumes of year 932."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==23 and all(x['status']=='published_verified' for x in rows[:10]) and all(x['status']=='pending' and not x['event_keys'] for x in rows[10:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(115,138));assert all(x['text']==lines[x['source_line']-1] for x in rows)
other=YEAR.parent.parent/'vol-278/year-0932';rr=read(other/'paragraphs.json');assert len(rr)==28 and all(x['status']=='pending' and not x['event_keys'] for x in rr)
b=read(P/'content-batch.json');c=read(P/'coverage.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 d=read(P/f);assert d['verified'] and d['batch_sha256']==sha
assert c['paragraphs']==[x['id'] for x in rows[:10]]
assert {k for x in rows[:10] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=read(YEAR.parent/'year-0931/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==50
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[0]['id'],rows[10]['id']]
progress['active_cursor'].update(volume=277,year=932,last_reviewed_paragraph=rows[9]['id'],last_published_paragraph=rows[9]['id'],next_paragraph=rows[10]['id'],next_paragraph_opening=rows[10]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==932)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[277,278],completed_volumes=[],note='卷277原115—124行连续10段已公开匿名核验；卷277本年余13段、卷278本年28段待录，全年共51段，目前10/51。未标全卷或全年完成。')
for n,key in [(2,'fuqing_death_date'),(6,'dangxiang_report_counts')]:
 full='932-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=932,current_volumes=[277,278],current_batch=rel,next_paragraph=rows[10]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=932,completed_paragraphs=10,volume_total_paragraphs=23,year_completed_paragraphs=10,year_total_paragraphs=51,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[10]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)],other_volume=dict(volume=278,body_paragraphs=28,completed_paragraphs=0)))
bd['note']='932年卷277原115—137行23正文段，前10段已匿名公开回查，余13待录；同年卷278另28段均待录，全年未完成。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷277 · 932年 · part-01\n\n连续第1—10段、原115—124行：15人物（高彦俦、陈觉2新增）、18事件、35人物参与、1妻子关系复用、98事实引用，10来源（6新增、4复用）。补证《旧五代史》《新五代史》。\n\n范请兵与二将七千遣、孟妻福庆卒、董塞绵路、孟赵拟峡江遣使及李昊阻议、反复邀董、壁州计划未行、九经校印令、战果奏报、高王爵、吴礼贤院谈议、李昊赴梓及闽王复位分录。\n\n福庆新明载由琼华改封，沿927人物key和妻子关系；主乙未、旧九月报今年正月十二日叙法差保留，九月不是卒月。康主前朔方与旧灵武衔差，七千为合军数。主十九族二千七百与旧阿埋十族、二千余等统计并列，不擅合或相加。\n\n峡江、攻壁、李昊直取梁洋反问均为未执行方案；三遣为重复协商合述，附当前再遣事件，不多造三次。董疑卖己、李昊窥西川是当事人判断。九经是开始校刻下令，旧仅正文石经印板获准补，不提前夹注953板成。勃海／渤海是爵，不是高据北方疆域。礼贤院不因功能相似与新他时延宾亭自动混同。孙晟沿已建孙凤孙忌，陈觉海陵籍明确。\n\n展示简体，原TXT与摘录不改底本。匿名核验公开UUID、出处URL、事实来源关联与SHA通过。932年跨卷277、278共51段，当前连续完成10段，下一段zztj-v277-y0932-p011；目标至936年后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷277 · 932年\n\n本卷原115—137行23正文段，part-01第1—10段已公开匿名核验，余13段待录。\n\n932年还含卷278原6—33行28段，全年共51段，目前10/51，全年及全卷未完成。下一段zztj-v277-y0932-p011。\n')
print(dict(year=932,completed=10,total=51,next_paragraph=rows[10]['id'],year_complete=False))
