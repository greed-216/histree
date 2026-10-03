# -*- coding: utf-8 -*-
"""Advance only after the complete 925 audit verifies all seven batches."""
import hashlib
import json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(p for p in P.parents if (p/'content/yearly-progress.json').exists())
YEAR=P.parent
def read(p):return json.loads(p.read_text())
def write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
ledger=read(YEAR/'paragraphs.json');audit=read(YEAR/'year-audit.json')
assert audit['verified'] and audit['year_complete'] and audit['body_paragraphs']==66
assert all(r['status']=='published_verified' for r in ledger[:29])
assert ledger[29]['status']=='excluded_non_body_verified'
for key,sha in audit['batch_sha256'].items():
 matches=[p for p in (ROOT/'content/books/zizhi-tongjian').glob('vol-*/year-0925/part-*/content-batch.json') if read(p)['batch_key']==key]
 assert len(matches)==1 and hashlib.sha256(matches[0].read_bytes()).hexdigest()==sha
next_year=YEAR.parent/'year-0926';next_ledger=read(next_year/'paragraphs.json')
other=ROOT/'content/books/zizhi-tongjian/vol-275/year-0926';other_ledger=read(other/'paragraphs.json')
assert len(next_ledger)==43 and len(other_ledger)==67
assert all(r['status']=='pending' for r in next_ledger+other_ledger)
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (ledger[24]['id'],next_ledger[0]['id'])
progress['active_cursor'].update(volume=274,year=926,last_reviewed_paragraph=ledger[29]['id'],last_published_paragraph=ledger[28]['id'],next_paragraph=next_ledger[0]['id'],next_paragraph_opening=next_ledger[0]['text'],batch=rel,status='in_progress')
year=next(r for r in progress['year_coverage'] if r['year']==925)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='complete_published_verified',completed_volumes=[273,274],note='925年卷273的37段与卷274的29正文段共66段、七批全部发布；全年审计复核连续源行、批次哈希、快照及匿名可见引用和固定URL。原账本第67项为926帝纪标题，已核结构项保留，不生史事。')
if not any(r['year']==926 for r in progress['year_coverage']):progress['year_coverage'].append(dict(year=926,status='in_progress',volumes=[274,275],completed_volumes=[],batches=[],note='926年卷274正文43段、卷275正文67段，共110段；年界与原文连续账本已核，尚待录入，下一段卷274第1段。'))
for key,n,note in [
 ('prince-cunyi',25,'主书存又据同日同睦王两史校为李存乂；旧本纪未列薛王，旧宗室传同年封存礼补，不是更名或存礼未封。'),
 ('guo-report-quantities',26,'向延嗣报告郭父子金银钱马及妓乐数皆转述，未当独立核定赃物；新郭传蜀簿兵三十万、粮二百五十三万与旧本纪三万、三百五十三万差异保留。'),
 ('guo-orders',27,'帝令孟诛后允先察，遣马附条件，拒贸杀而刘后自为教；新郭传写矫诏，性质分别保留。实际杀郭留926正月，不移至925。'),
 ('chu-trade-text',28,'辐氵奏底本拆字保留待校；不征商旅、茶算与铅铁钱、帛税为不同叙述税目，初追叙未强年，不将零商旅税等同全部零税。')]:
 full='925-v274-'+key
 if not any(r['key']==full for r in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=274,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=next_ledger[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
parts=[];totals={'events':0,'claims':0}
for part in sorted(YEAR.glob('part-*')):
 b=read(part/'content-batch.json');p=read(part/'publication.json');parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=p['batch_sha256'],anonymous_readback_verified=p['verified']))
 for k in totals:totals[k]+=len(b[k])
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=274,year=925,completed_paragraphs=29,volume_total_paragraphs=29,ledger_items=30,excluded_non_body=1,year_completed_paragraphs=66,year_total_paragraphs=66,next_paragraph=next_ledger[0]['id'],next_volume=274,next_year=926,continuous_prefix_verified=True,volume_complete=True,year_complete=True,year_audit='year-audit.json',batches=parts,batch_totals=totals))
(YEAR/'README.md').write_text('# 《资治通鉴》卷274 · 925年\n\n本卷29正文段（原文件6—34行）三批全部发布并匿名读回。账本第30项为926帝纪标题，稳定ID及原字保留，已核为非正文结构项。\n\n925年两卷共66正文段、七批全部完成，全年原文、哈希、快照、公开记录及引用固定URL审计见year-audit.json。下一段zztj-v274-y0926-p001。\n')
(ROOT/'content/books/zizhi-tongjian/vol-273/year-0925/README.md').write_text('# 《资治通鉴》卷273 · 925年\n\n本卷37正文段（原文件84—120行）四批全部公开并匿名读回，卷审计见volume-audit.json。\n\n925年续卷274的29正文段亦完成；两卷全年66段的联合审计见卷274/year-0925/year-audit.json。原账本另有926章节标题一项，不计正文。下一段zztj-v274-y0926-p001。\n')
(P/'README.md').write_text('# 《资治通鉴》卷274 · 925年 · part-03\n\n第25—29正文段已发布并匿名读回：22事件、56参与、146引用；新增7人、5条李存勖为皇弟兄长的关系，另两条兄长关系复用。第30项为已核的926章节标题，不生史事。\n\n补证来自旧史卷33、51、57与新史卷5、14、24、66。存又按两史同日同睦王校作存乂，薛王封爵有旧列传补证。郭氏反志及财货为内官指控，不当核定事实；楚财政属初起追叙，未强年。皇帝条件处理、允许先察、拒贸杀与刘后自教分开；实际杀郭留926。\n\n第26段跨两个导出阅读块，分别保存定位与引用，不拼造底本。新郭传蜀簿兵粮与旧本纪不同，报告财货清单未混加。楚商税与茶算税目各存，底本辐氵奏保留待纸本。吴越告号、吴拒函退使禁通商不等已开战。\n\n全年两卷66正文段完成公开联合审计，下一段zztj-v274-y0926-p001。\n')
(next_year/'README.md').write_text('# 《资治通鉴》卷274 · 926年\n\n本卷正文43段，原文件38—80行，均待录入。年首的帝纪标题、分隔符及纪年行排除在正文外。\n\n926年还须卷275正文67段，共110段；不能完成本卷后就标全年完成。下一段zztj-v274-y0926-p001。\n')
(other/'README.md').write_text('# 《资治通鉴》卷275 · 926年\n\n本卷正文67段，原文件6—72行，均待录入。原文件73行分隔符及74行927年标题不算正文。\n\n926年须先处理卷274的43段，再接本卷67段，共110正文段。\n')
print(dict(year_complete=925,next_paragraph=next_ledger[0]['id'],next_year_body_paragraphs=110))
