# -*- coding: utf-8 -*-
"""Advance only the exact publicly verified 929 continuous prefix."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==36
assert all(r['status']=='published_verified' for r in rows[:32])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[32:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(87,123))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
prev=read(P.parent.parent/'year-0928/year-audit.json');assert prev['verified'] and prev['year_complete'] and prev['body_paragraphs']==52
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P.parent/'part-04',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:32]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[27]['id'],rows[32]['id']]
progress['active_cursor'].update(volume=276,year=929,last_reviewed_paragraph=rows[31]['id'],last_published_paragraph=rows[31]['id'],next_paragraph=rows[32]['id'],next_paragraph_opening=rows[32]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==929)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='929年卷276共36正文段，首32段已连续发布并逐条匿名回查，余4段待处理；全年未完成。')
for key,n,note in [
 ('hancheng_kinship_and_rebel_names',28,'韩澄主与新康传为韩洙弟，新韩氏传为子；亲属有异不建确定父弟边。选定新卷40校勘注亦称子恐误，引新康及薛史弟说，已存编校上下文不算新独立正文。李匡宾/李从宾/李宾并列待纸核，不仅繁简、不增第二叛。韩洙卒依新韩氏929年补证，不倒赋丁酉。'),
 ('kangfu_appointment_and_glyph',28,'胡语便殿、安威胁、求外任背景null。请帅、授、哭辞、帝命更镇安拒、护送分，未实际换镇；牛卫共万人。卫原私用区字暂按同卷平行电子文本规范卫审𡷣，原文不改，纸核待，未混卫审符或審餘。'),
 ('baoning_and_sichuan_supplies',30,'辛亥阆果置保宁、壬子仁矩授，旧升阆及左卫大将军补称法。西川常供峡路请免拒催前事null，甲寅财乏为其理由，不奉诏不等已举兵。'),
 ('wu_xu_power_and_accusations',31,'徐旧职争权、钱龙凤赠、周计双告和除父丧背景null。人言七不臣与新知诰诬反都属指控非确反。十一月入朝留统军仍镇海、柯厚征兵、知诰专政分；兄弟对责归其说法，周遂斩不猜行刑者。'),
 ('wu_honorific_variant',32,'主睿圣文明光孝、新睿圣文明孝少光存异；改元大和本字，不太和、不重927即位。新同段中书令与主十二月纪时另留后批。')
]:
 full='929-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=929,current_volumes=[276],current_batch=rel,next_paragraph=rows[32]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=929,completed_paragraphs=32,volume_total_paragraphs=36,year_completed_paragraphs=32,year_total_paragraphs=36,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[32]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 929年 · part-05\n\n连续第28—32段（原114—118行）：39新增事件、68人物参与、184事实引用；19人物（5新增）；9来源（7新增、2复用），补证《旧五代史》《新五代史》。\n\n覆盖朔方请帅、康福任命与护送，保宁军设立和李仁矩任职，孟知祥拒峡路馈粮，以及吴徐争权、周廷望被斩、吴加号改元。新增韩澄、李匡宾、牛知柔、卫审𡷣、周廷望。\n\n韩洙卒依新韩氏传天成四年补纪年，确日未知。韩澄主与新康传为弟、新韩氏传为子，不建确定亲属边，所选卷40校勘注亦指出子恐误（保留为编校上下文）；李匡宾、新李从宾/李宾名异存，不直接合实名别名。康福善胡语不推民族，威胁不等已斩；请帅、授、辞、要求换镇、安拒、万人护送分。卫原私用区字经同卷平行电子文本暂规范卫审𡷣，原文不改，纸本待核，详sources字形记录。\n\n保宁主阆果与旧升阆详略保留；西川财乏为奏称理由，不奉诏不等已反。徐知询七不臣及新知诰诬反为指控，未作为确定谋反事实。钱龙凤赠非授帝位，周结交建议不等收买全部朝臣，徐争权背景不强全发生十一月；入朝、留统军仍领镇海、柯厚征兵、知诰专政、兄弟互责及斩周分录。\n\n主吴尊号有光，新少光，保留异文；改大和不改太和，加号不等第二次即位。新同段中书令概记与主十二月时点待后批补录。\n\n公开UUID、状态、逐字引用、来源SHA、source关联及固定GitHub链接均已回查。展示简体，引用保留底本；电子异文纸本待核。\n\n929年完成32/36段，下一段zztj-v276-y0929-p033，全年未完成；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 929年\n\n原文件87—122行，共36段正文；首32段五批已连续发布并匿名回查，余4段待处理。年界和卷末已核，下一卷277从930年开始。\n\n下一段zztj-v276-y0929-p033；连续覆盖和验证证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=32,total=36,next_paragraph=rows[32]['id'],year_complete=False))
