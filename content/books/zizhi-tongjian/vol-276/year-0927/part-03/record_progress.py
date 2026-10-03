# -*- coding: utf-8 -*-
"""Record consecutive 927 coverage across both volumes after public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
first=ROOT/'content/books/zizhi-tongjian/vol-275/year-0927';rows1=read(first/'paragraphs.json');rows=read(P.parent/'paragraphs.json')
assert len(rows1)==32 and len(rows)==25
assert all(r['status']=='published_verified' for r in rows1+rows[:13])
assert all(r['status']=='pending' for r in rows[13:])
for d,rs,begin,end in [(first,rows1,75,106),(P.parent,rows,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(begin,end+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[first/f'part-{n:02d}' for n in range(1,7)]+[P.parent/'part-01',P.parent/'part-02',P];proofs=[];covered=[]
for part in parts:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows1+rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows1+rows[:13]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[10]['id'],rows[13]['id']]
progress['active_cursor'].update(volume=276,year=927,last_reviewed_paragraph=rows[12]['id'],last_published_paragraph=rows[12]['id'],next_paragraph=rows[13]['id'],next_paragraph_opening=rows[13]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[275],note='927年两卷共57段，卷275全部32段与卷276前13段已发布并匿名回查，完成45段，余12段待录，全年未完成。')
for key,n,note in [
 ('sunsheng-name-and-zhaofeng-glyph',11,'孙晨疑晟与后孙晟，两史同职同事识同人；初凤又忌明录，晨不正式别名。主哭胃/旧哭谓原字不改；抗议叙序存异。'),
 ('renhuan-death-report-days',11,'主任死未具日不强戊子或己丑前，旧丙申奏报与本月十二日发生、新乙未不同纪时并列，王执行药仅报告。'),
 ('zhu-family-sun-flight-arrears',12,'主命左右斩与新自杀概称同事；朱自杀族不同安族孙家；孙逃吴途中陈宋不强己丑已抵。债近二百万概数，旧欠项年限不扩永久全税免。')
]:
 full='927-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=rows[13]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=927,completed_paragraphs=13,volume_total_paragraphs=25,year_completed_paragraphs=45,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[13]['id'],batches=proofs))
(P/'README.md').write_text("""# 《资治通鉴》卷276 · 927年 · part-03

连续第11—13段（原文件16—18行）已发布：25事件、36人物参与、119事实引用；5新增人物、8复用人物；10来源（7新增、3复用），补证《旧五代史》《新五代史》。

新增孙晟、马彦超、宋敬、王仁镐、药纵之。主孙晨疑晟与后孙晟按两史同朱幕宾判官与行动识同人，晨不正式别名，新初凤又忌原证。离洛、荥阳、京水遣石、大梁攻降分阶段，民吴东侯讹言不当实策。朱杀马宋旧独补，旧朱奏马谋乱是其说、新死之为不同评价，奏报不强杀日。范谕、500骑请准、夜行、交战分事，主200里/旧200余里未折公里时速，旧翌日巷战不强干支。

任遣死主奏遣与旧诬构称制存叙述差；赵主哭胃/旧哭谓原字保留，主抗议前置/旧既而杀后不强统一。任聚族饮与死亡分，不将族人一同判死。主无确死日，旧丙申奏报、本月十二日发生、新乙未分别，药报告与王执行明确，报告不造第二死亡。朱杀族命左右斩、新自杀概称同日并列；旧鞭尸悬首7日送洛为死后处理。孙途中陈宋更名、弃家及安画购族其家独立引用，不混朱族；李昪接宾不提前帝位相位。免欠近二百万概数，旧租税课利船欠年限保留，非现金入账非永久免全部税；旧重海、重复任圜等讹缺未强推姓名动机。

逐条摘录、源行与来源SHA、公开UUID、source关联和固定GitHub地址匿名回查通过。展示简体，底本原字保留，纸本及异日待核。

927年完成45/57段，下一段zztj-v276-y0927-p014；继续至936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷276 · 927年

本卷25正文段（原文件6—30行），连续第1—13段三批已发布并匿名回查，余12段待录。927年另含卷275全部32段，共57段，当前完成45段，全年未完成。

下一段zztj-v276-y0927-p014。跨卷连续前缀和批次证明见progress-audit.json。
""")
print(dict(completed=45,total=57,next_paragraph=rows[13]['id'],year_complete=False))
