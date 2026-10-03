# -*- coding: utf-8 -*-
"""Record a verified consecutive fifteen-paragraph prefix; year 927 remains incomplete."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json'); second=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927';other=read(second/'paragraphs.json')
assert len(rows)==32 and len(other)==25
assert all(r['status']=='published_verified' for r in rows[:15])
assert all(r['status']=='pending' for r in rows[15:]+other)
for d,rs,first,last in [(P.parent,rows,75,106),(second,other,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[];covered=[];totals={'events':0,'claims':0}
for n in range(1,4):
 part=P.parent/f'part-{n:02d}';data=read(part/'content-batch.json');cov=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in cov['paragraphs'] for k in r['event_keys']}=={x['key'] for x in data['events']}
 covered+=cov['paragraphs'];parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert covered==[r['id'] for r in rows[:15]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[12]['id'],rows[15]['id']]
progress['active_cursor'].update(volume=275,year=927,last_reviewed_paragraph=rows[14]['id'],last_published_paragraph=rows[14]['id'],next_paragraph=rows[15]['id'],next_paragraph_opening=rows[15]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='927年两卷共57正文段，连续前15段三批已发布并逐条匿名回查，余42段待录，全年未完成。')
for key,note in [
 ('shu-goods-retrospection','魏王遣韩运蜀物及高杀韩是讨伐前旧事，主未具日null，新联系庄宗之难；四十万/四十余万未给单位，十余人只是新人数。'),
 ('jingnan-campaign-days','主旧二月壬寅削官部署/新二月戊戌刘招讨存异；四万仅刘夏一路，东南面原名保留，三面计划不是已取胜。'),
 ('guocongqian-appointment-execution','郭景州任命丙申，族诛到任后具体日未载，未具族人数，不强当同日或景等荆。')]:
 full='927-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[12]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=rows[15]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=927,completed_paragraphs=15,volume_total_paragraphs=32,year_completed_paragraphs=15,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[15]['id'],batches=parts,batch_totals=totals))
(P/'README.md').write_text('''# 《资治通鉴》卷275 · 927年 · part-03

连续第13—15段（原文件87—89行）已发布：13事件、28人物参与、78事实引用；新增韩珙1人，复用12人；6来源（3新增、3复用），补证《旧五代史》《新五代史》。

郭从谦景州任命及既至族诛、高请求子弟任刺史不许、潘炕罢后夺夔州杀戍兵、拒西方邺及袭涪未克、魏王遣韩押蜀货、峡口截杀、朝诘水神答、削高爵、刘夏四万与董西方楚军三面部署分别。另录三月李敬周武信朝命与监牧，旧补任圜倡议及马殷参与同部署。

韩押货与死为讨伐前旧事，主未具日null，新庄宗难背景并列，未把已卒继岌写927发令。主金帛四十万/新四十余万，单位未具不擅换钱缗银两；新韩等十余是人数不混财物量。水神覆溺为高答推托，不称实际溺亡。主旧壬寅/新戊戌讨伐日期不同；四万仅刘夏一路，其他军数未具不造总额，三面是部署非战果。郭族诛人数未具，诛日不套任日，景与荆不同；潘罢不是潘死，子弟不猜从诲。正月孟先任李敬周与三月朝廷任命不同阶段。

公开ID、每条引用source ID与固定GitHub链接、原文快照SHA和连续源行已匿名回查。简体展示，底本逐字不改，纸本及异文待核。927年完成15/57段，下一段zztj-v275-y0927-p016，目标仍是936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷275 · 927年

本卷32正文段（原文件75—106行），连续第1—15段三批已发布并匿名回查，余17段待录。927年另含卷276的25段，共57段，当前完成15段，全年未完成。

下一段zztj-v275-y0927-p016。连续前缀、源行哈希及批次证明见progress-audit.json。
''')
print(dict(completed=15,total=57,next_paragraph=rows[15]['id'],year_complete=False))
