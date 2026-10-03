# -*- coding: utf-8 -*-
"""Advance the continuous cursor only after exact public readback."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');b=read(P/'content-batch.json');c=read(P/'coverage.json')
sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for file in ['publication.json','readback-audit.json']:
 proof=read(P/file);assert proof['verified'] and proof['batch_sha256']==sha
assert len(rows)==55 and all(r['status']=='published_verified' for r in rows[:9])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[9:])
assert c['paragraphs']==[r['id'] for r in rows[:9]]
assert {k for r in rows[:9] for k in r['event_keys']}=={r['key'] for r in b['events']}
raw=ROOT/'resources/derived/tongjian/277.txt';lines=raw.read_text().splitlines();bd=read(P.parent/'boundaries.json')
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(6,61))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
assert lines[60]=='◎' and '九三一年' in lines[61]
previous=read(ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/year-audit.json')
assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==36
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[0]['id'],rows[9]['id']]
progress['active_cursor'].update(volume=277,year=930,last_reviewed_paragraph=rows[8]['id'],last_published_paragraph=rows[8]['id'],next_paragraph=rows[9]['id'],next_paragraph_opening=rows[9]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==930)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原6—14行连续9段已发布并匿名回查；全年55段，余46段待录入。61—62行年界结构不计正文。')
for key,n,note in [
 ('sichuan_accusation',4,'尼告李仁罕张业谋害，孟诘无状，不确认为谋反；丁酉处刑都延昌王行本，戊戌赴宴。二十四史未检同案，主独证。'),
 ('name_variants',5,'李从曮及私用字形复用李继曮，朱弘照/旧朱宏昭复用朱弘昭，原字保留。李彦钊不与彦超合并。'),
 ('era_and_crown_prince',6,'二月乙卯实际改长兴，年标题不使正月自动变长兴；新吴二年承大和二年930，杨溥→杨琏父亲复用。'),
 ('kangfu_baojing',8,'康福奏克保静杀李匡宾，奏日未载；旧三月灵武杀蕃二千是不同记载，不作此案补证。')
]:
 full='930-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=930,current_volumes=[277],current_batch=rel,next_paragraph=rows[9]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=277,year=930,completed_paragraphs=9,volume_total_paragraphs=55,year_completed_paragraphs=9,year_total_paragraphs=55,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[9]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)]))
bd['note']='930年卷277原6—60行55正文段；前9段连续发布并匿名回查，余46段待处理。61—62行分隔及931标题不计正文。';write(P.parent/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 930年 · part-01

连续第1—9段（原6—14行）：26事件、42人物参与、120事实引用；17人物（4新增）、1复用父亲关系、6来源（5新增、1复用），补证《旧五代史》《新五代史》。新增郭在徽、都延昌、王行本、李彦钊。

覆盖剑门设寨、赵季良往返两川、郭在徽大钱提议与降官、杨澈改封、孟知祥处理谋害指控与赴宴、两川表忧、郊祀赦令改元、李继曮和朱弘昭任职、杨琏太子册立、康福保静奏报与昭义军复名。

郭奏是提议，不写成已经铸钱。李仁罕张业被告后原书记无状，不建立已谋反事实；被处刑的是都延昌王行本。赵对董璋的评价保持归属。新董传李彦钊守剑门、增永定关未独载年份，用未知年。两川表文自陈忧恐，慰诏不推撤兵。乙卯改长兴，不以全年标题倒赋正月。李继曮、朱弘昭按同职务同日期沿已有身份，摘录保留异字。新吴二年承大和纪年，杨溥→杨琏父亲复用。康保静奏报不与旧灵武杀蕃二千混为一案。

展示名称和说明用简体，原文及逐字引句保留底本繁简字形。来源SHA、公开UUID、source关联及固定GitHub链接均回查；电子本异文仍待纸本校核。

本年完成9/55段；下一段zztj-v277-y0930-p010。继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷277 · 930年

原6—60行55正文段。part-01连续第1—9段已发布并匿名回查；余46段待处理，未标全年完成。

第61—62行为年界分隔及931年标题，不计930正文；原文快照保持底本字形。下一段zztj-v277-y0930-p010。
''')
print(dict(completed=9,total=55,next_paragraph=rows[9]['id'],year_complete=False))
