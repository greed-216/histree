# -*- coding: utf-8 -*-
"""Record a verified consecutive 10/50 prefix, keeping the rest of 931 pending."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==50 and all(x['status']=='published_verified' for x in rows[:10]);assert all(x['status']=='pending' and not x['event_keys'] for x in rows[10:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(63,113));assert all(x['text']==lines[x['source_line']-1] for x in rows)
assert lines[61]=='长兴二年辛卯，公元九三一年' and lines[112]=='◎' and lines[113]=='长兴三年壬辰，公元九三二年'
b=read(P/'content-batch.json');c=read(P/'coverage.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest();assert c['paragraphs']==[x['id'] for x in rows[:10]]
assert {k for x in rows[:10] for k in x['event_keys']}=={x['key'] for x in b['events']}
for f in ['publication.json','readback-audit.json']:
 d=read(P/f);assert d['verified'] and d['batch_sha256']==sha
previous=read(YEAR.parent/'year-0930/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==55
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[0]['id'],rows[10]['id']]
progress['active_cursor'].update(volume=277,year=931,last_reviewed_paragraph=rows[9]['id'],last_published_paragraph=rows[9]['id'],next_paragraph=rows[10]['id'],next_paragraph_opening=rows[10]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==931)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原63—72行连续10段已公开并匿名回查；全年50段，余40段待处理。113—114行分隔及932年标题不计正文。')
for n,key in [(2,'suizhou_capture_dates'),(6,'an_accusations_retrospective'),(9,'liyanqi_liyan_ke_and_dong_plot')]:
 full='931-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=931,current_volumes=[277],current_batch=rel,next_paragraph=rows[10]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=931,completed_paragraphs=10,volume_total_paragraphs=50,year_completed_paragraphs=10,year_total_paragraphs=50,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[10]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)]))
bd['note']='931年原63—112行50正文段，前10段已公开匿名核验，余40段待录；113—114行年界不计正文。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 931年 · part-01

连续第1—10段，原63—72行：33事件、58人物参与、148事实引用，12人物（李彦琦新增，其余复用），8来源（3新增、5复用）。补证旧、新五代史。

孟表谢、遂陷夏自杀、石再到剑州战退、夏首展示及二子请葬收葬、高加衔、合州归武信、安途中款待受谗召归、石烧营北归、三泉得诏凤翔拒入、利州弃城入城及赵密图董被拒、李仁罕峡路任命，连续分录。

新董传930九月陷遂与主、新孟931正月不同，保留同书内部时差。夏自杀与死后示首、收葬不混；二子无名不造，石必葬为预测，孟果葬为行动。石正月再战退剑门与二月烧营北归分别，新示首接班师为简叙不抹主再战过程。

初朱得镇、凤翔首次途经的款待与泣诉、朱报与书未独年按追叙留空。主硃弘昭与新朱弘昭沿稳定主体。朱指夺兵、石恐军变、孟奏过恶均保留说话者，不虚造安真实谋反或已夺兵。来回两次凤翔分别，一次馆舍一次拒纳。孟匿退报问渐进为试问，不生成虚假的新进军。

新利州李彦珂与主昭武李彦琦按同地同弃城识别，珂/琦不作繁简自动替换。未据九国志转述擅加李茂贞养父关系。赵图董只是建议被拒，董宿营后去；多诈未来祸为赵评价，不生成谋杀已执行。李任东略不提前夔州取城。

显示简体，引用与TXT快照保留原字；SHA、固定提交链接、匿名公开UUID和source引用关联已核。全年完成10/50，下一段zztj-v277-y0931-p011；继续至936年后唐灭亡。
''')
(YEAR/'README.md').write_text('''# 《资治通鉴》卷277 · 931年

原63—112行50正文段。part-01第1—10段已公开并匿名核验，余40段待录，未标全年完成。

113—114行分隔及932标题不计正文。下一段zztj-v277-y0931-p011。
''')
print(dict(year=931,completed=10,total=50,next_paragraph=rows[10]['id'],year_complete=False))
