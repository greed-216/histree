# -*- coding: utf-8 -*-
"""Advance the continuous cursor only after public verification of all five parts."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');bd=read(P.parent/'boundaries.json');raw=ROOT/'resources/derived/tongjian/277.txt';lines=raw.read_text().splitlines()
assert len(rows)==55 and all(r['status']=='published_verified' for r in rows[:45])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[45:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(6,61)) and all(r['text']==lines[r['source_line']-1] for r in rows)
assert lines[60]=='◎' and '九三一年' in lines[61]
prior=read(ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/year-audit.json');assert prior['verified'] and prior['year_complete'] and prior['body_paragraphs']==36
covered=[];proofs=[]
for part in [P.parent/f'part-{n:02d}' for n in range(1,6)]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:45]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[35]['id'],rows[45]['id']]
progress['active_cursor'].update(volume=277,year=930,last_reviewed_paragraph=rows[44]['id'],last_published_paragraph=rows[44]['id'],next_paragraph=rows[45]['id'],next_paragraph_opening=rows[45]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==930)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原6—50行连续45段、5批已发布并匿名回查；全年55段，余10段待录入。61—62行年界结构不计正文。')
for n,key in [(36,'jiaozhou_identity_variants'),(39,'peiyu_return_time'),(40,'fengyun_office_time'),(43,'five_prefectures_glyph'),(44,'jing_alias_future_posts')]:
 full='930-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=930,current_volumes=[277],current_batch=rel,next_paragraph=rows[45]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=277,year=930,completed_paragraphs=45,volume_total_paragraphs=55,year_completed_paragraphs=45,year_total_paragraphs=55,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[45]['id'],batches=proofs))
bd['note']='930年卷277原6—60行55正文段；前45段、5批连续发布并匿名回查，余10段待处理。61—62行分隔及931标题不计正文。';write(P.parent/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 930年 · part-05

连续第36—45段（原41—50行）：30事件、50人物参与、154事实引用；24人物（7新增）、3父亲关系（1新增、2复用）、12来源（7新增、5复用）。补证《旧五代史》《新五代史》。

覆盖南汉攻交州与占城、遂州围城与康文通降、董璋退阆与剑门援军提议、钱镠表与裴羽返使、冯赟北都任命、董光业族诛、马殷请传马希声、峡路水军与五州陷落、严可求卒和徐景通参政。

曲承美复用911静海节度使曲美主体；据旧传全名、梁授旄与新传曲氏父子校核。新李守鄘与主李守鄜同役识别，旧李知顺另叙不擅合并。刘龑沿刘岩，徐知诰沿李昪，徐景通沿李璟。曲颢→曲美新增父亲关系；马殷→马希声、李昪→李璟复用。

裴羽旧传安死后返与主930返使时间差保留。冯赟主十月北院左卫、旧七月甲子南院右卫任北留职衔时间差并列。五州的征字疑讹保留未改渠、未补坐标。三千欲遣是计划；马殷疑死不是真实死亡；徐将出镇未当已经到任；新张武病卒与夏鲁奇自刎属于后续未提前。

展示简体，原文快照和摘录保留底本字形。来源固定GitHub提交，SHA、匿名公开UUID与source关联已核；电子本异文仍待纸本校核。

本年完成45/55段，下一段zztj-v277-y0930-p046。继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷277 · 930年

原6—60行55正文段。part-01—05连续第1—45段已发布并匿名回查；余10段待处理，未标全年完成。

第61—62行为年界分隔及931年标题，不计930正文；原文快照保持底本字形。下一段zztj-v277-y0930-p046。
''')
print(dict(completed=45,total=55,next_paragraph=rows[45]['id'],year_complete=False))
