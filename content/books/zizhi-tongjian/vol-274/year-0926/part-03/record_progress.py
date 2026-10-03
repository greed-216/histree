# -*- coding: utf-8 -*-
"""Advance the chronological cursor only after the third batch is public."""
import hashlib
import json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
audit=read(P/'readback-audit.json');b=read(P/'content-batch.json')
assert audit['verified'] and audit['batch_sha256']==hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
ledger=read(P.parent/'paragraphs.json');other=read(ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/paragraphs.json')
assert len(ledger)==43 and len(other)==67
assert all(r['status']=='published_verified' for r in ledger[:36])
assert all(r['status']=='pending' for r in ledger[36:]+other)
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (ledger[24]['id'],ledger[36]['id'])
progress['active_cursor'].update(volume=274,year=926,last_reviewed_paragraph=ledger[35]['id'],last_published_paragraph=ledger[35]['id'],next_paragraph=ledger[36]['id'],next_paragraph_opening=ledger[36]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[],note='926年共110正文段；卷274第1—36段三批连续公开并匿名读回。卷274余7段、卷275全67段待处理，全年未完成。')
for key,n,note in [
 ('siyuan-date',25,'主甲寅与旧甲辰受命征邺日不同；到邺、攻城及兵变两史纪日均分别保存待纸本。'),
 ('liyanhou-identity',27,'主李延厚与第9段李廷厚同任骁锐指挥使但身份尚待核，事件保留原名可检索，未另造或合并人物。'),
 ('huoyanwei-entry',30,'新霍传称霍独不入城，主同李入城，出城时长亦有异，分立引证不强合。'),
 ('kang-escape-place',31,'主康败后奔绵竹、旧奔绵州异说保留；此段只被擒不先录处决。'),
 ('wangyanhan-glyph',29,'主王廷翰据旧同职同任王延翰校同人，原字不改；辛酉与辛亥任日异说保存。')]:
 full='926-v274-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=274,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=ledger[36]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
parts=[];covered=[];totals={'events':0,'claims':0}
for part in sorted(P.parent.glob('part-*')):
 data=read(part/'content-batch.json');pub=read(part/'publication.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 assert pub['verified'] and pub['batch_sha256']==sha
 proof=read(part/'readback-audit.json');assert proof['verified'] and proof['batch_sha256']==sha
 covered+=read(part/'coverage.json')['paragraphs']
 parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert covered==[r['id'] for r in ledger[:36]]
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=274,year=926,completed_paragraphs=36,volume_total_paragraphs=43,year_completed_paragraphs=36,year_total_paragraphs=110,continuous_prefix_verified=True,volume_complete=False,year_complete=False,next_paragraph=ledger[36]['id'],batches=parts,batch_totals=totals))
(P/'README.md').write_text('# 《资治通鉴》卷274 · 926年 · part-03\n\n连续第25—36段（原文件62—73行）已发布：36事件、72参与、197引用；新增11个人物，本批无新人物关系。\n\n补证来自旧史卷34、35、37、64、74及新史卷45、46。李嗣源受命、拒乱兵、被逼入城、出城收兵分阶段记录；新霍传称独不入城，与主同入及出城时长差异保留。各书受命、到鄴、兵变纪日分别留存，未硬改为同日。\n\n康延孝金雁桥败擒不等已经处决，主逃绵竹与旧逃绵州各存；孟知祥施政与任将、魏县会兵得马、地方诛监军、预借夏秋税及张全义卒按主书顺序分录。原书李延厚与既有李廷厚同职但身份未决，事件先保留原名，暂不新增或合并人物。王廷翰据两史同职同任校王延翰；疑字保持来源原字，展示简体。\n\n公开ID、引用出处ID和固定URL已逐条匿名回查，见publication.json与readback-audit.json。下一段zztj-v274-y0926-p037，926全年未完成。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷274 · 926年\n\n本卷43正文段（原文件38—80行），第1—36段三批连续发布并匿名读回，余7段待录。\n\n926年还包含卷275的67段，共110段，目前完成36段。下一段zztj-v274-y0926-p037。\n')
print(dict(completed=36,total=110,next_paragraph=ledger[36]['id'],year_complete=False))
