# -*- coding: utf-8 -*-
"""Record a verified consecutive thirty-two-paragraph prefix; year 927 remains incomplete."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json'); second=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927';other=read(second/'paragraphs.json')
assert len(rows)==32 and len(other)==25
assert all(r['status']=='published_verified' for r in rows[:32])
assert all(r['status']=='pending' for r in other)
for d,rs,first,last in [(P.parent,rows,75,106),(second,other,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[];covered=[];totals={'events':0,'claims':0}
for n in range(1,7):
 part=P.parent/f'part-{n:02d}';data=read(part/'content-batch.json');cov=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in cov['paragraphs'] for k in r['event_keys']}=={x['key'] for x in data['events']}
 covered+=cov['paragraphs'];parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert covered==[r['id'] for r in rows[:32]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[24]['id'],other[0]['id']]
progress['active_cursor'].update(volume=276,year=927,last_reviewed_paragraph=rows[31]['id'],last_published_paragraph=rows[31]['id'],next_paragraph=other[0]['id'],next_paragraph_opening=other[0]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[275],note='927年两卷共57正文段，连续前32段六批已发布并逐条匿名回查，余25段待录，全年未完成。')
for key,paragraph_number,note in [
 ('renhuan-finance-and-chancellorship',26,'五月辞三司与六月丙戌罢相不同；旧任传食券正文补证，校注引通鉴不独立；七月致仕、十月杀待录。'),
 ('liuxun-tan-chan-glyph',30,'主檀州与旧澶州均保留，暂不校地名或给坐标；不提前七月流濮州。'),
 ('three-prefectures-battle-report-day',32,'主六月段后记收州未具日，旧七月甲子段奏报、新同日取州，报告日不当战日；旧夔刺史与新随刺史异文待核。')
]:
 full='927-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[paragraph_number-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=other[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=927,completed_paragraphs=32,volume_total_paragraphs=32,year_completed_paragraphs=32,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=True,year_complete=False,next_paragraph=other[0]['id'],batches=parts,batch_totals=totals))
(P/'README.md').write_text("""# 《资治通鉴》卷275 · 927年 · part-06

连续第25—32段（原文件99—106行）已发布：17事件、26人物参与、82事实引用；3新增人物（史光宪、孟鹄、温辇）、9复用人物；6来源（3新增、3复用），补证《旧五代史》《新五代史》。

楚使入贡、赏赐、江陵扣使夺物、请附吴与吴拒臣分录；徐温救援困难之说为政策理由，不当实际战争。馆券争执、宫人评论、采安议、五月任辞三司和孟权判分录，六月任罢相另事，未提前致仕或死亡。温辇请立太子仅是提议。张己丑与旧丁亥后记载位置不强统；刘檀州/澶州异文并存。楚王进楚国王不当新建国家。西方邺三州收复主六月后无日、旧七月甲子段奏报、新七月甲子取州，报告不当战日，夔/随刺史职衔原样并列。

逐字摘录及源行SHA核对，公开ID、引用source关联及固定GitHub地址匿名读回通过。展示简体，原文保留底本字形，纸本及异文待核。

本卷927年32段全部处理；927年跨两卷57段，完成32段，全年未完成。下一段zztj-v276-y0927-p001，目标仍为936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷275 · 927年

本卷32正文段（原文件75—106行）六批均已发布并匿名回查，卷内处理完成。927年另含卷276的25段，共57段，当前完成32段，全年未完成。

下一段zztj-v276-y0927-p001。连续前缀、源行哈希及批次证明见progress-audit.json。
""")
print(dict(completed=32,total=57,next_paragraph=other[0]['id'],year_complete=False))
