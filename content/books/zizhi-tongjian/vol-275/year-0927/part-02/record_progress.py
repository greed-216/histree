# -*- coding: utf-8 -*-
"""Advance the verified consecutive prefix of 927; do not claim year completion."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
b=read(P.parent/'paragraphs.json');second=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927';c=read(second/'paragraphs.json')
assert len(b)==32 and len(c)==25
assert all(r['status']=='published_verified' for r in b[:12])
assert all(r['status']=='pending' for r in b[12:]+c)
for directory,rows,first,last in [(P.parent,b,75,106),(second,c,6,30)]:
 boundary=read(directory/'boundaries.json');raw=ROOT/boundary['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==boundary['source_sha256']
 assert [r['source_line'] for r in rows]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rows)
sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest();pub=read(P/'publication.json');proof=read(P/'readback-audit.json');cov=read(P/'coverage.json');batch=read(P/'content-batch.json')
assert pub['verified'] and proof['verified'] and pub['batch_sha256']==proof['batch_sha256']==sha
assert cov['paragraphs']==[r['id'] for r in b[6:12]]
assert {k for r in b[6:12] for k in r['event_keys']}=={x['key'] for x in batch['events']}
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [b[6]['id'],b[12]['id']]
progress['active_cursor'].update(volume=275,year=927,last_reviewed_paragraph=b[11]['id'],last_published_paragraph=b[11]['id'],next_paragraph=b[12]['id'],next_paragraph_opening=b[12]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[],note='927年卷275共32段、卷276共25段，共57正文段；连续前12段已发布并逐条匿名回查，余45段待录，全年未完成。')
for key,n,note in [
 ('khitan-era-and-burial',10,'主927段改元/辽元年二月926，葬主正月段木叶/辽二年八月丁酉祖陵；上下文哈希回查，不合未核地名或强定同日。'),
 ('shulv-wrist-and-death-toll',10,'主一腕/辽右腕，赵问答与亲戚百官谏分存；以百数概数，幼弱无主为说辞，断腕前后各次未具日。'),
 ('wu-salary-request',9,'徐阳疑佯原字保留；固请一月俸为请求不称已执行，肃然为作者概述，柴不服不造实际罚。'),
 ('wuzhen-convoys-and-handover',11,'三将兵为三次运粮，前事确日未载null；领宁国旧宣州军州称谓并列，不当离屯赴任；房归叙不强已交印抵兖，后段待录。')
]:
 full='927-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=b[12]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
prev=P.parent/'part-01'
prevdata=read(prev/'content-batch.json');prevsha=hashlib.sha256((prev/'content-batch.json').read_bytes()).hexdigest()
assert read(prev/'publication.json')['batch_sha256']==read(prev/'readback-audit.json')['batch_sha256']==prevsha
assert read(prev/'readback-audit.json')['verified']
assert read(prev/'coverage.json')['paragraphs']+cov['paragraphs']==[r['id'] for r in b[:12]]
parts=[dict(batch=str(prev.relative_to(ROOT)),batch_sha256=prevsha,anonymous_readback_verified=True),dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)]
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=927,completed_paragraphs=12,volume_total_paragraphs=32,year_completed_paragraphs=12,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[12]['id'],batches=parts,batch_totals={k:len(batch[k])+len(prevdata[k]) for k in ['events','claims']}))
(P/'README.md').write_text("""# 《资治通鉴》卷275 · 927年 · part-02

连续第7—12段（原文件81—86行）已发布：18事件、28人物参与、2人物关系、90事实引用；2新增人物李从厚及赵思温，13复用人物，7来源，补证《旧五代史》《辽史》。

从厚任官、就职与从荣反应分事；父亲李嗣源至从厚、兄长从荣至从厚方向明确。安重诲孔循加衔各录。吴柴戎服弹劾不服、徐佯误礼自劾受优诏及请扣一月俸区分；请求不直接当执行。

契丹改元主927段与辽926二月异年并存，辽元年上下文逐字归档并验SHA；葬主木叶山正月段/辽祖陵八月丁酉，不擅合地点，葬与926卒分别。述左右以百数概数、赵拒行答话、后说辞及断腕分别，未具各日null；主一腕/辽右腕、赵问答/亲戚百官谏不同叙述独立引用。未提前后953卒。

乌三次运粮前事日未知，不当三位将军；二月戊子副招讨领宁国与旧宣州不同称谓独存。房归镇不强已交印抵兖；后文卢台乱尚待录。石兼副使补检校太傅，未提前帝号。正文规范简体，逐字引用不改原字，纸本待核。

公开实体ID、每条引用的source ID和固定GitHub URL、源行及来源与年界上下文SHA均已回查。927年连续完成12/57段，下一段zztj-v275-y0927-p013；目标仍为936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷275 · 927年

本卷32正文段（原文件75—106行），连续第1—12段两批已发布并匿名回查，余20段待录。927年另含卷276的25段，共57段，目前完成12段，全年未完成。

下一段zztj-v275-y0927-p013。源行、哈希、连续前缀及批次回查证明见progress-audit.json。
""")
print(dict(completed=12,total=57,next_paragraph=b[12]['id'],year_complete=False))
