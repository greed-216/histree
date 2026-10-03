# -*- coding: utf-8 -*-
"""Advance the consecutive 928 prefix only after exact public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:17])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[17:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:17]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[12]['id'],rows[17]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[16]['id'],last_published_paragraph=rows[16]['id'],next_paragraph=rows[17]['id'],next_paragraph_opening=rows[17]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首17段已连续发布并逐条匿名回查，余35段待处理；全年未完成。')
for key,n,note in [
 ('wangdu_contacts',13,'初追叙各事年null；怕迁未有调镇诏，求婚不等姻亲，王建立阳许密奏不等共同反叛；主五镇益与新岐异说并列，未猜五帅。'),
 ('dingzhou_relief_strength',15,'主新万骑与旧千余骑初援不同保留，旧幽州奏二千与败返二千不同统计阶段；两外关非主城，未猜供税三州。新郑杜迎军二千独立，仅杜明确被杀，不扩大郑也死。'),
 ('zhaojingyi_identity',16,'赵敬怡新主体与赵敬贻不同；主旧天雄副、新右卫上将军原衔分别保留。'),
 ('quyang_timing_generals',17,'主乙丑丙寅丁卯行动与旧丁卯奏十八新乐、壬申奏二十一曲阳区分；旧嘉山高行周与新曲阳高行珪不合并。五千与总万余不相加，过半不精算，回顾斩是军令，可擒是判断，王秃仍逃，殆无非确全歼。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[17]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=17,volume_total_paragraphs=52,year_completed_paragraphs=17,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[17]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 928年 · part-04\n\n连续第13—17段（原文件45—49行）：41事件、61人物参与、181事实引用；4新增人物、12复用人物；8来源（5新增、3复用），补证《旧五代史》《新五代史》。\n\n覆盖王都联络与反状奏报、杨濛改封临川、定州初战、赵敬怡任枢密使、新乐与曲阳战事。新增朱建丰、赵敬怡、郑季璘、杜弘寿。王晏球沿已校正杜晏球主体。\n\n初追叙不强赋928年；求婚、结兄弟拟议不建已成关系，王建立阳许密奏不记真共谋。主益与新岐五镇异说、各阶段不同兵数保留；定州北西关城不等主城克复。新迎军郑杜二千人与秃馁返二千骑分开，仅杜明确被杀。赵敬怡与赵敬贻、高行珪与高行周不按近名合并。\n\n行动日与奏报日分别保留。去弓短兵、回顾者斩是军令，不推实际处决；可擒是判断，王都与秃馁逃脱。契丹五千是万余合军一部，死过半不精算，北逃殆无不记确定全歼。旧传夹引通鉴注不作独立确证。\n\n来源TXT、逐字引用和定位保留底本字形，名称及说明用简体。纸本异文待核；结构校验、源SHA、公开UUID、引用关联与固定GitHub URL均已核验。快照包括后续未读段落，未将全快照算完成。\n\n928年完成17/52段，下一段zztj-v276-y0928-p018；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 928年\n\n原文件33—84行，共52段正文；首17段四批已发布并匿名回查，余35段待连续处理。前后年界已核，卷277从930年开始。\n\n下一段zztj-v276-y0928-p018；连续前缀和批次证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=17,total=52,next_paragraph=rows[17]['id'],year_complete=False))
