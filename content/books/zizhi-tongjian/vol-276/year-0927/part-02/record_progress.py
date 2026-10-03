# -*- coding: utf-8 -*-
"""Record consecutive 927 coverage across both volumes after public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
first=ROOT/'content/books/zizhi-tongjian/vol-275/year-0927';rows1=read(first/'paragraphs.json');rows=read(P.parent/'paragraphs.json')
assert len(rows1)==32 and len(rows)==25
assert all(r['status']=='published_verified' for r in rows1+rows[:10])
assert all(r['status']=='pending' for r in rows[10:])
for d,rs,begin,end in [(first,rows1,75,106),(P.parent,rows,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(begin,end+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[first/f'part-{n:02d}' for n in range(1,7)]+[P.parent/'part-01',P];proofs=[];covered=[]
for part in parts:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows1+rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows1+rows[:10]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[6]['id'],rows[10]['id']]
progress['active_cursor'].update(volume=276,year=927,last_reviewed_paragraph=rows[9]['id'],last_published_paragraph=rows[9]['id'],next_paragraph=rows[10]['id'],next_paragraph_opening=rows[10]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[275],note='927年两卷共57段，卷275全部32段与卷276前10段已发布并匿名回查，完成42段，余15段待录，全年未完成。')
for key,n,note in [
 ('chu-offices-name-taboo',7,'主拓跋恒/新拓拔常同职同册命识人，保留异名不正式别名；主殷父讯/新父元丰异文存说，不新建重复父亲。旧梁时文苑背景null不强927。'),
 ('fu-surname-and-khitan-envoys',8,'李彦超按既有别名沿符彦超，旧明父存审；复姓请求许分事，旧庚申后未具日不强命日；梅老同日来不扩为已签盟。')
]:
 full='927-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=rows[10]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=927,completed_paragraphs=10,volume_total_paragraphs=25,year_completed_paragraphs=42,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[10]['id'],batches=proofs))
(P/'README.md').write_text("""# 《资治通鉴》卷276 · 927年 · part-02

连续第7—10段（原文件12—15行）已发布：21事件、23人物参与、2人物关系、94事实引用；7新增人物、9复用人物；6来源（4新增、2复用），补证《旧五代史》《新五代史》。

新增李铎、崔颖、拓跋恒、张彦瑶、张迎、马讯、李序。楚册使到、唐遣李序竹册、宫殿百官及各授官分阶段；楚政权起源不改为927。机构三改名、两称谓、摄官与朗桂先除后请分别保留。旧梁时已有文苑学士为前事背景，年null；主拓跋恒/新拓拔常同职识同人，异名待校而不正式别名。避父讳原字和主讯/新元丰姓名差异并存，不自动校改或重复建父。张两人共职不造亲属边。

九月帝控从荣左右伪旨按话语记；拟斩非已杀，安请严戒非已许可。李彦超沿符彦超，复姓请求许可分事，旧明确父存审建父至子边，庚申后复姓句未另具日不硬定该日。孔兼东都不等罢枢密或抵达。契丹求好与唐回复分事，新同日梅老来补证，不强合旧同月贡使或宣布盟约。

逐条原文、定位、源行SHA及公开UUID、source关联和固定GitHub地址匿名回查通过。展示简体，引用保留原字，纸本及异名待核。

927年完成42/57段；下一段zztj-v276-y0927-p011，继续至936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷276 · 927年

本卷25正文段（原文件6—30行），连续第1—10段两批已发布并匿名回查，余15段待录。927年另含卷275全部32段，共57段，当前完成42段，全年未完成。

下一段zztj-v276-y0927-p011。跨卷连续前缀和批次证明见progress-audit.json。
""")
print(dict(completed=42,total=57,next_paragraph=rows[10]['id'],year_complete=False))
