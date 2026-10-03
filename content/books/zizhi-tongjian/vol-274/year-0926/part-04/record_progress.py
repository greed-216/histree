# -*- coding: utf-8 -*-
"""Advance the chronological cursor only after the fourth batch is public."""
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
assert all(r['status']=='published_verified' for r in ledger[:40])
assert all(r['status']=='pending' for r in ledger[40:]+other)
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (ledger[36]['id'],ledger[40]['id'])
progress['active_cursor'].update(volume=274,year=926,last_reviewed_paragraph=ledger[39]['id'],last_published_paragraph=ledger[39]['id'],next_paragraph=ledger[40]['id'],next_paragraph_opening=ledger[40]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[],note='926年共110正文段；卷274第1—40段四批连续公开并匿名读回。卷274余3段、卷275全67段待处理，全年未完成。')
for key,n,note in [
 ('congjing-names',37,'主从审、旧从璟、赐继璟据两史同长子同职同事合同人；生父李嗣源、两史明说收为己子的养父李存勖分别建边。'),
 ('treasury-variants',37,'主三银盆与旧妆奁银盆各二不同，幼子三人不补姓名；主给财癸酉、旧癸亥，元返朝甲戌、旧甲子及鹞店耀店均保留待纸本。'),
 ('zhai-jian-glyph',39,'主翟建白据新本纪同年同博州守将校作翟建，白疑自。晖、汴原字保留，不擅校第一地。'),
 ('wangyan-execution-date',40,'主置三月条下无确日，新本纪三月甲子与新蜀世家四月不同，分立引证待核；新张传称驰诏魏王与主向延嗣赍敕不同，不强合。')]:
 full='926-v274-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=274,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=ledger[40]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
parts=[];covered=[];totals={'events':0,'claims':0}
for part in sorted(P.parent.glob('part-*')):
 data=read(part/'content-batch.json');pub=read(part/'publication.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 assert pub['verified'] and pub['batch_sha256']==sha
 proof=read(part/'readback-audit.json');assert proof['verified'] and proof['batch_sha256']==sha
 covered+=read(part/'coverage.json')['paragraphs']
 parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert covered==[r['id'] for r in ledger[:40]]
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=274,year=926,completed_paragraphs=40,volume_total_paragraphs=43,year_completed_paragraphs=40,year_total_paragraphs=110,continuous_prefix_verified=True,volume_complete=False,year_complete=False,next_paragraph=ledger[40]['id'],batches=parts,batch_totals=totals))
(P/'README.md').write_text('''# 《资治通鉴》卷274 · 926年 · part-04

连续第37—40段（原文件74—77行）已发布：28事件、56参与、152引用；新增9个人物及2条人物关系。

补证来自《旧五代史》卷34、51及《新五代史》卷5、15、27、38、63。李从审、李从璟、李继璟据同人同事合并；生父李嗣源与养父李存勖分别建有方向的关系。请出内库、遣使传父、移檄会兵、诸将行动、王宗衍遇害依主书顺序分录，建议与实际执行分开。

银盆数量、赏军及返京纪日、鹞店与耀店、王宗衍遇害月份和传诏方式的异文保留独立引用。翟建白据同年同博州守将校作翟建，疑字在原文中保留。军士怨言、谋反判断与临刑预言按言说记录；幼子不补姓名，未执行的售子不写成事实。展示用简体，来源快照与摘录保留底本繁简字形。

公开ID、引用出处ID和固定URL已逐条匿名回查，见publication.json与readback-audit.json。下一段zztj-v274-y0926-p041，926全年未完成。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷274 · 926年

本卷43正文段（原文件38—80行），第1—40段四批连续发布并匿名读回，余3段待录。

926年还包含卷275的67段，共110段，目前完成40段。下一段zztj-v274-y0926-p041；本卷与全年均未完成。
''')
print(dict(completed=40,total=110,next_paragraph=ledger[40]['id'],year_complete=False))
