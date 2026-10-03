# -*- coding: utf-8 -*-
"""Record a verified consecutive twenty-four-paragraph prefix; year 927 remains incomplete."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json'); second=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927';other=read(second/'paragraphs.json')
assert len(rows)==32 and len(other)==25
assert all(r['status']=='published_verified' for r in rows[:24])
assert all(r['status']=='pending' for r in rows[24:]+other)
for d,rs,first,last in [(P.parent,rows,75,106),(second,other,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[];covered=[];totals={'events':0,'claims':0}
for n in range(1,6):
 part=P.parent/f'part-{n:02d}';data=read(part/'content-batch.json');cov=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in cov['paragraphs'] for k in r['event_keys']}=={x['key'] for x in data['events']}
 covered+=cov['paragraphs'];parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert covered==[r['id'] for r in rows[:24]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[18]['id'],rows[24]['id']]
progress['active_cursor'].update(volume=275,year=927,last_reviewed_paragraph=rows[23]['id'],last_published_paragraph=rows[23]['id'],next_paragraph=rows[24]['id'],next_paragraph_opening=rows[24]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='927年两卷共57正文段，连续前24段五批已发布并逐条匿名回查，余33段待录，全年未完成。')
for key,note in [
 ('mengchang-mother-and-name','主子仁赞、旧昶初名仁贊注与新送昶识同人；旧明确生母李氏随知祥妻琼华入蜀，不建琼生母边，初名来自旧注不另加专书source。'),
 ('lutai-families-units','主3500家万人余、旧诏3500人在营骨肉单位分存，命令与执行分别，未造准确死人数；赏房主安反侧/旧赏功动机分说。'),
 ('kongxun-april-and-min-title','主癸卯遣孔、旧辛丑后记遣位置不硬定同日；主威武琅邪王/旧福建琅琊郡王同任不同衔存原文。')
]:
 full='927-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[18]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=rows[24]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=927,completed_paragraphs=24,volume_total_paragraphs=32,year_completed_paragraphs=24,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[24]['id'],batches=parts,batch_totals=totals))
(P/'README.md').write_text("""# 《资治通鉴》卷275 · 927年 · part-05

连续第19—24段（原文件93—98行）已发布：18事件、32人物参与、3人物关系、99事实引用；3新增人物（孟昶、琼华长公主、李氏〔孟昶母〕）、14复用人物；7来源（3新增、4复用），补证《旧五代史》《新五代史》。

卢台家属处斩敕令和执行分事，主3500家万余人与旧诏3500人在营家口单位不同，未换算精确死数；渠赤为史叙。房兼侍中主知首乱安反侧与旧赏功动机分别，另补同日安检校太傅。

孟家迎、凤翔留奏、许归及四月丙申到成都分阶段，未套三月李使到日。拆字凤翔主沿李继曮不并李严。仁赞据旧初名注和新昶同程识孟昶，初名证标旧校注性质；琼华是孟妻，孟昶生母李氏与琼同行明别，不建琼生母关系。父孟至昶、母李至昶、妻琼至孟方向明确，不猜公主父族。

赵请留与丁酉朝命分事，李昊归授未强同丁酉。江陵雨粮疾疫不现代确诊；孔主癸卯遣/旧辛丑后记遣位置存异，到城另录。王延钧五月癸丑主威武琅邪王/旧福建琅琊郡王衔并存。孔攻城遣说、衣万袭、赐楚督粮未获及撤兵敕分别；万袭衣套非兵额，未获粮不等楚反，旧补令散掠回程不造人数。

来源SHA、连续源行、每条公开source ID和固定GitHub地址均匿名回查；简体展示，原字摘录不改，纸本及异文待核。927年完成24/57段，下一段zztj-v275-y0927-p025；目标仍为936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷275 · 927年

本卷32正文段（原文件75—106行），连续第1—24段五批已发布并匿名回查，余8段待录。927年另含卷276的25段，共57段，当前完成24段，全年未完成。

下一段zztj-v275-y0927-p025。连续前缀、源行哈希及批次证明见progress-audit.json。
""")
print(dict(completed=24,total=57,next_paragraph=rows[24]['id'],year_complete=False))
