# -*- coding: utf-8 -*-
"""Finish volume-277/year-932 body and enter volume 278; year remains incomplete."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==23 and all(x['status']=='published_verified' for x in rows[:21])
assert all(x['status']=='excluded_non_body_verified' and x['kind']=='separator' and not x['text'].strip() and not x['event_keys'] for x in rows[21:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(115,138));assert all(x['text']==lines[x['source_line']-1] for x in rows)
other=YEAR.parent.parent/'vol-278/year-0932';rr=read(other/'paragraphs.json');obd=read(other/'boundaries.json');oraw=ROOT/obd['source_file'];olines=oraw.read_text().splitlines()
assert len(rr)==28 and all(x['status']=='pending' and not x['event_keys'] for x in rr)
assert [x['source_line'] for x in rr]==list(range(6,34)) and all(x['text']==olines[x['source_line']-1] for x in rr)
assert hashlib.sha256(oraw.read_bytes()).hexdigest()==obd['source_sha256']
proof=[]
for path,selection in [(YEAR/'part-01',rows[:10]),(YEAR/'part-02',rows[10:15]),(P,rows[15:21])]:
 b=read(path/'content-batch.json');c=read(path/'coverage.json');sha=hashlib.sha256((path/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(path/f);assert d['verified'] and d['batch_sha256']==sha
 assert c['paragraphs']==[x['id'] for x in selection]
 assert {k for x in selection for k in x['event_keys']}=={x['key'] for x in b['events']}
 proof.append(dict(batch=str(path.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
previous=read(YEAR.parent/'year-0931/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==50
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[15]['id'],rr[0]['id']]
progress['active_cursor'].update(volume=278,year=932,last_reviewed_paragraph=rows[20]['id'],last_published_paragraph=rows[20]['id'],next_paragraph=rr[0]['id'],next_paragraph_opening=rr[0]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==932)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[277,278],completed_volumes=[277],note='卷277本年21段正文全部公开匿名核验，原136—137两空行排除保留ID；卷278本年28段待录。全年正文应49段（旧51误含2空行），目前21/49；只完成卷277的本年段，不标932全年完成。')
for n,key in [(16,'li_tang_homonym_and_yuan_glyph'),(16,'dong_guangsi_death_order'),(19,'captive_return_variants'),(20,'li_cungui_identity'),(21,'min_petition_timing')]:
 full='932-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=278,current_year=932,current_volumes=[277,278],current_batch=rel,next_paragraph=rr[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
excluded=read(P/'coverage.json')['excluded_non_body']
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=932,completed_paragraphs=21,volume_total_paragraphs=21,ledger_records=23,excluded_non_body_verified=excluded,year_completed_paragraphs=21,year_total_paragraphs=49,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=True,year_complete=False,next_paragraph=rr[0]['id'],batches=proof,other_volume=dict(volume=278,body_paragraphs=28,completed_paragraphs=0),count_correction='旧51包含本卷尾2空行；正文21+28=49。旧发布档案保留。'))
bd.update(body_source_lines=[115,135],body_paragraphs=21,ledger_source_lines=[115,137],ledger_records=23,excluded_non_body=excluded,note='932年卷277原115—135行21正文段已全部公开匿名核验；原136—137两空行核结构保留ID。卷278同年28段待录，全年49正文段，未完成。');write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷277 · 932年 · part-03\n\n连续第16—21正文段、原130—135行：34人物（11新增）、55事件、135参与、4有向关系、299事实引用、10出处（4新增6复用）。补证《旧五代史》《新五代史》。原136—137行两个空行保留ID，核结构排除，不造事件与事实。\n\n补齐五月汉州战役和董璋败亡、孟与部将争任、康党项奏、部分俘将放归及其后合述、保宁与东川安排、唐密规进取转招抚、闽宗教预言谋帝与请封。\n\n每个战场动作和后续行政命令分录，诬通谋、军情报告、奏报数、反间解释、预言和计划皆注明归属，不写实际合谋、已实施密攻或已称帝。战死数、俘将及不同批降卒不擅合算；旧六月与九月奏闻不改五月战日。\n\n西川左冲山指挥使李瑭与901已斩的汾州刺史异人，限定新主体。主元璝被俘与元瑰降疑同人或异人未定，后事件保留原称而不另建重复元姓人物，待考。张公鐸展示铎，主定元职衔和鸡踪桥字形保留；新鸡距及旧正文弥牟位置各述，旧夹注九国志暂不新增基础事实。\n\n董光演、光嗣、先已死光业不并；主光嗣先死与新董先死后光嗣自缢次序差并列。潘稠执行斩董与旧王晖集体主导分层。董延浩从子不补父；李存瑰与新瓌旧瑰按同供奉任务及孟甥亲缘识，父亲、外甥有方向；李克宁已亡不造本年参与。\n\n荝骨舍利与旧则骨同案称名，不是未获返荝剌；旧既而四月段与主五月己亥叙法留。闽廷钧疑字沿王延钧，宝皇等神号不造真人。旧七月乙未请封补时，不把所有问卜也放同日；新其他军镇任与九月返表待后段。\n\n展示简体，TXT与逐字引文原字保留。固定Git出处、公开UUID、关联和SHA匿名回查通过。卷277的932正文21段完成，全年应49段（旧51误含2空行），21/49；下一卷278同年首段，目标仍到936后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷277 · 932年\n\n原115—135行21正文段已全部公开匿名核验；账本末第22、23项为原136—137行空行，保留ID与原字，已核结构排除。3个批次分别覆盖1—10、11—15、16—21正文段。\n\n932年卷278原6—33行另28段待录，全年正文总数应为49（旧51误含卷尾2空行），目前21/49。全年未完成；下一段zztj-v278-y0932-p001。\n')
print(dict(year=932,completed=21,total=49,next_paragraph=rr[0]['id'],volume_year_complete=True,year_complete=False))
