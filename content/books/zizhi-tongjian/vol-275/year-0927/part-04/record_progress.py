# -*- coding: utf-8 -*-
"""Record a verified consecutive eighteen-paragraph prefix; year 927 remains incomplete."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json'); second=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927';other=read(second/'paragraphs.json')
assert len(rows)==32 and len(other)==25
assert all(r['status']=='published_verified' for r in rows[:18])
assert all(r['status']=='pending' for r in rows[18:]+other)
for d,rs,first,last in [(P.parent,rows,75,106),(second,other,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[];covered=[];totals={'events':0,'claims':0}
for n in range(1,5):
 part=P.parent/f'part-{n:02d}';data=read(part/'content-batch.json');cov=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in cov['paragraphs'] for k in r['event_keys']}=={x['key'] for x in data['events']}
 covered+=cov['paragraphs'];parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert covered==[r['id'] for r in rows[:18]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[15]['id'],rows[18]['id']]
progress['active_cursor'].update(volume=275,year=927,last_reviewed_paragraph=rows[17]['id'],last_published_paragraph=rows[17]['id'],next_paragraph=rows[18]['id'],next_paragraph_opening=rows[18]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='927年两卷共57正文段，连续前18段四批已发布并逐条匿名回查，余39段待录，全年未完成。')
for key,note in [
 ('lutai-names','主宴安神博疑异文、旧震与房博于东寨，暂不新建疑名或确定并安；龙晊旧龙至同部同事校同人，原文不改。'),
 ('lutai-narrators-and-deaths','主房诱兵杀乌/旧房奏仅戍军乱后自己平各标叙述者；旧四月奏报前月21日不当乌卒在四月，逃免主一二旧二三概数不算精确死亡。'),
 ('gaoxiuxing-glyph','主高秀兴疑季兴据同役新世家及本卷后文沿高季昌，不注册正式别名或新疑名主体；纸本待校。')
]:
 full='927-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[15]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=rows[18]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=927,completed_paragraphs=18,volume_total_paragraphs=32,year_completed_paragraphs=18,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[18]['id'],batches=parts,batch_totals=totals))
(P/'README.md').write_text("""# 《资治通鉴》卷275 · 927年 · part-04

连续第16—18段（原文件90—92行）已发布：20事件（19新增、1复用）、36人物参与、106事实引用；新增龙晊、李仁矩2人，15复用人物；8来源（5新增、3复用），补证《旧五代史》《新五代史》。

分录秘密请移镇、刺史及节度任命、从荣镇邺护送、九部3500赴卢台、讹言与未交印、召宴、主房诱杀乌、安渡河骑军不动、房诈语脱身、合谋击乱、夜行追击、诘朝围击焚寨、范返邺防奔逸。魏兵克梁及亡庄宗为前史概述，不重复造事件；赵旧义成拒赴稳定事件与参与复用。

主宴安神博待校，不强并安审通或造疑名人；龙晊旧龙至同部同事识别。主房诱兵杀乌与房奏仅戍军乱后自己平分叙述者；四月辛巳报告前月21是奏日与发生日区分。逃免主十无一二/旧十无二三概数，不乘军额算确死。旧王都败后事和主后家属杀、加房侍中都待连续后录，未提前完成。

李仁矩三月甲戌到成都与派遣不同日，新送家属只补使事；主四月亲属到后段待录。刘到荆南、楚许德勋水军岳州、荆南坚壁求吴及吴水军援分别。高秀兴疑季兴按同役新世家及本卷后名沿高季昌，未注册正式别名。军额船数统帅未具不猜，受命不等全已执行。

每条引用公开source ID与固定GitHub地址、原文SHA及连续源行已匿名回查；简体展示，摘录原字不改，纸本及异文待核。927年完成18/57段，下一段zztj-v275-y0927-p019；目标仍为936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷275 · 927年

本卷32正文段（原文件75—106行），连续第1—18段四批已发布并匿名回查，余14段待录。927年另含卷276的25段，共57段，当前完成18段，全年未完成。

下一段zztj-v275-y0927-p019。连续前缀、源行哈希及批次证明见progress-audit.json。
""")
print(dict(completed=18,total=57,next_paragraph=rows[18]['id'],year_complete=False))
