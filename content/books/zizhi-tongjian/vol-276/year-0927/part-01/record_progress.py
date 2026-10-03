# -*- coding: utf-8 -*-
"""Record consecutive 927 coverage across both volumes after public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
first=ROOT/'content/books/zizhi-tongjian/vol-275/year-0927';rows1=read(first/'paragraphs.json');rows=read(P.parent/'paragraphs.json')
assert len(rows1)==32 and len(rows)==25
assert all(r['status']=='published_verified' for r in rows1+rows[:6])
assert all(r['status']=='pending' for r in rows[6:])
for d,rs,begin,end in [(first,rows1,75,106),(P.parent,rows,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(begin,end+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[first/f'part-{n:02d}' for n in range(1,7)]+[P];proofs=[];covered=[]
for part in parts:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows1+rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows1+rows[:6]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[0]['id'],rows[6]['id']]
progress['active_cursor'].update(volume=276,year=927,last_reviewed_paragraph=rows[5]['id'],last_published_paragraph=rows[5]['id'],next_paragraph=rows[6]['id'],next_paragraph_opening=rows[6]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[275],note='927年两卷共57段，卷275全部32段与卷276前6段已发布并匿名回查，完成38段，余19段待录，全年未完成。')
for key,n,note in [
 ('douluge-weishuo-execution-days',3,'主新七月癸酉与旧壬申异日并存；陵合流地未强逐人配地，授州为朝廷所列罪名，骨肉放逐便不当全杀。'),
 ('wangyanqiu-restored-name',1,'据旧926恢复本姓记录，本段王晏球与旧杜晏球、李绍虔同一人，复用杜主体，未新建重复人物。'),
 ('exile-retirement-eclipse',4,'段辽温德刘濮主未具日，旧壬申是逐令非抵达；任请致仕与许可、旧传出居不同阶段，日食己卯朔未作现代天文校算。')
]:
 full='927-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=rows[6]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=927,completed_paragraphs=6,volume_total_paragraphs=25,year_completed_paragraphs=38,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[6]['id'],batches=proofs))
(P/'README.md').write_text("""# 《资治通鉴》卷276 · 927年 · part-01

连续第1—6段（原文件6—11行）已发布：10事件、9人物参与、49事实引用；8人物全部复用；6来源（3新增、3复用），补证《旧五代史》《新五代史》。

王晏球据旧明宗纪926恢复本姓记载识同既有杜晏球，不重复建人；旧补北面副招讨七月朔命。升夔宁江与西方邺节授分事，不重造三州收复。豆卢革韦说赐死主新癸酉、旧壬申并存；朝廷授州罪名不等校核其合理性，陵合流地未强逐人配地，骨肉放逐便不当全家处死。段凝辽州、温韬德州、刘训濮州分别，不当已经抵达；刘流不同六月刺史贬授。任致仕磁州请求与许可分事，旧甲戌寻医补记、旧传实际出居无到日，未提前十月死。日食主旧己卯朔，未自行换算公历、路径或政治因果。

来源SHA、连续源行、公开UUID、引用source关联及固定GitHub地址匿名回查通过。展示简体，原文保留字形，纸本及异日待核。

927年完成38/57段，下一段zztj-v276-y0927-p007。目标继续至936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷276 · 927年

本卷25正文段（原文件6—30行），连续第1—6段已发布并匿名回查，余19段待录。927年另含卷275全部32段，共57段，当前完成38段，全年未完成。

下一段zztj-v276-y0927-p007。跨卷连续前缀和批次证明见progress-audit.json。
""")
print(dict(completed=38,total=57,next_paragraph=rows[6]['id'],year_complete=False))
