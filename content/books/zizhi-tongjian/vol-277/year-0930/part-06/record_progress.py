# -*- coding: utf-8 -*-
"""Advance the continuous cursor only after public verification of all six parts."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');bd=read(P.parent/'boundaries.json');raw=ROOT/'resources/derived/tongjian/277.txt';lines=raw.read_text().splitlines()
assert len(rows)==55 and all(r['status']=='published_verified' for r in rows[:48])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[48:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(6,61)) and all(r['text']==lines[r['source_line']-1] for r in rows)
assert lines[60]=='◎' and '九三一年' in lines[61]
prior=read(ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/year-audit.json');assert prior['verified'] and prior['year_complete'] and prior['body_paragraphs']==36
covered=[];proofs=[]
for part in [P.parent/f'part-{n:02d}' for n in range(1,7)]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:48]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[45]['id'],rows[48]['id']]
progress['active_cursor'].update(volume=277,year=930,last_reviewed_paragraph=rows[47]['id'],last_published_paragraph=rows[47]['id'],next_paragraph=rows[48]['id'],next_paragraph_opening=rows[48]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==930)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原6—53行连续48段、6批已发布并匿名回查；全年55段，余7段待录入。61—62行年界结构不计正文。')
for n,key in [(47,'mayin_death_year'),(48,'jianmen_identity_timing')]:
 full='930-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=930,current_volumes=[277],current_batch=rel,next_paragraph=rows[48]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=277,year=930,completed_paragraphs=48,volume_total_paragraphs=55,year_completed_paragraphs=48,year_total_paragraphs=55,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[48]['id'],batches=proofs))
bd['note']='930年卷277原6—60行55正文段；前48段、6批连续发布并匿名回查，余7段待处理。61—62行分隔及931标题不计正文。';write(P.parent/'boundaries.json',bd)
(P/'README.md').write_text("""# 《资治通鉴》卷277 · 930年 · part-06

连续第46—48段（原51—53行），剑门长段全段处理：31事件、59人物参与、158事实引用；24人物（14新增）、9来源（7新增、2复用）。补证旧、新五代史。

张武至渝州受降、取泸遣朱分兵；马殷去世、遗命与边备讨论；唐军绕袭剑门、破焚剑州、两川告急援军、庞谢夜袭、潘沙败敌、张武死及袁代将、黔涪进军和分屯南山，逐动作分录。假设进梓、欲先据、未独日的调兵不写为已证全过程同日。

马卒主930十一己巳、新93079岁、旧931十一十日78岁并列；新年谱辨旧为编者校考，非另原书已核独证。王经/弘/宏同阶州同役校为王弘贽，原引不改。冯晖（后唐泸州刺史）魏州身份与新传、旧纪校核；902弘铎部下同名缺衔接，不自动合，留待身份校考。李筠（前蜀永平节度使）与897被诛唐都头分开。李肇沿926汝阴孟部主体。

旧辛巳收到十三日战报，奏闻与作战日分；剑门三千/三千余数差留。杨汉宾/旧汉章、主朱进军/旧董攻叙法差留。王晖以前陵州消歧，不混冯晖和旧云州叛将。追至丰都不等捕杨。来源快照保留底本字形，公开引用与SHA已核，电子异文待纸本。

本年完成48/55段，下一段zztj-v277-y0930-p049。目标继续至936年后唐灭亡。
""")
(P.parent/'README.md').write_text('''# 《资治通鉴》卷277 · 930年

原6—60行55正文段。part-01—06连续第1—48段已发布并匿名回查；余7段待处理，未标全年完成。

第61—62行为年界分隔及931年标题，不计930正文；原文快照保持底本字形。下一段zztj-v277-y0930-p049。
''')
print(dict(completed=48,total=55,next_paragraph=rows[48]['id'],year_complete=False))
