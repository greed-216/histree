# -*- coding: utf-8 -*-
"""Advance after all 110 body paragraphs pass the full-year public audit."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
audit=read(YEAR/'year-audit.json')
assert audit['verified'] and audit['year_complete'] and audit['year']==926 and audit['body_paragraphs']==110
assert audit['anonymous_readback_verified'] and audit['verbatim_claim_quotes_verified'] and len(audit['batch_sha256'])==13
other=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926';a=read(other/'paragraphs.json');b=read(YEAR/'paragraphs.json')
assert len(a)==43 and len(b)==67 and all(r['status']=='published_verified' for r in a+b)
parts=[];covered=[];totals={'events':0,'claims':0}
for folder in [other,YEAR]:
 for part in sorted(folder.glob('part-*')):
  batch=read(part/'content-batch.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();pub=read(part/'publication.json');proof=read(part/'readback-audit.json')
  assert audit['batch_sha256'][batch['batch_key']]==sha and pub['verified'] and pub['batch_sha256']==sha and proof['verified'] and proof['batch_sha256']==sha
  covered+=read(part/'coverage.json')['paragraphs'];parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
  for k in totals:totals[k]+=len(batch[k])
assert covered==[r['id'] for r in a+b] and len(parts)==13
next_year=YEAR.parent/'year-0927';next_rows=read(next_year/'paragraphs.json');second=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927';second_rows=read(second/'paragraphs.json')
assert len(next_rows)==32 and len(second_rows)==25 and all(r['status']=='pending' and not r['event_keys'] for r in next_rows+second_rows)
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[60]['id'],next_rows[0]['id'])
progress['active_cursor'].update(volume=275,year=927,last_reviewed_paragraph=b[66]['id'],last_published_paragraph=b[66]['id'],next_paragraph=next_rows[0]['id'],next_paragraph_opening=next_rows[0]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='complete_published_verified',completed_volumes=[274,275],note='926年卷274的43段和卷275的67段共110正文段、13批全部发布。全年联合审计复核连续源行、批次及快照哈希、逐字摘录、年界结构项与匿名可见实体、引用及固定URL。两书纪年人数异说及待纸本问题保留。')
if not any(x['year']==927 for x in progress['year_coverage']):progress['year_coverage'].append(dict(year=927,status='in_progress',volumes=[275,276],completed_volumes=[],batches=[],note='927年卷275正文32段、卷276正文25段共57段，年界和源行已核，正文全部待录。下一段卷275第1段。'))
for key,n,note in [
 ('shu-fiscal-units-and-report',61,'主魏郭五百万/新孟六百万与剩二百万分来源，金银缯帛充数不视全现金；十万兵为孟答话不当实测。主可库不许税/新拒诏口径各存。'),
 ('liyan-monitor-and-prophecy',61,'己酉任监不等已入川，李母警告非已死；实际927杀留下一年。朱硃同太原文思同东川校同人。'),
 ('certificates-retrospection',62,'甲戌刘奏与限定官告、后执政全体建议、长兴以后卒伍胥史岁万数分时；旧庄宗部分费用减免不是926前全员皆征。'),
 ('min-regicide-accusation',63,'延禀称延翰妻崔氏共弑先王是指控，不认实事；实际斩只延翰，未言妻同死。新崔病死年未载，不推此日活死。成南疑城南保字。'),
 ('chentao-homonym',63,'福州指挥使陈陶与既有陈敬瑄子雅州陈陶无同人证，以陈陶（福州指挥使）独立主体，不并旧父子。'),
 ('luwenjin-appointment-day',64,'主癸已疑巳/旧甲午任滑州义成同人同职而日异保留，未造第二任命。'),
 ('shu-transport-billion-unit',66,'金帛十亿未明单位，不添缗、银两或现代币；朝迁疑朝廷原字留，不据济用判断长期富。'),
 ('wuyue-era-later-omission',67,'本年宝正改元与其后复通讳称分时，后年未知null；本次二十四史未找到明确补证，不用范围外专书代替。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=next_rows[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
for folder,vol,rows in [(other,274,a),(YEAR,275,b)]:
 bounds=read(folder/'boundaries.json');bounds['note']='926年正文全部发布并通过两卷全年联合审计；原文、结构项及定位保持。';write(folder/'boundaries.json',bounds)
 old=read(folder/'progress-audit.json');old.update(completed_paragraphs=len(rows),volume_total_paragraphs=len(rows),year_completed_paragraphs=110,year_total_paragraphs=110,volume_complete=True,year_complete=True,next_paragraph=next_rows[0]['id'],next_volume=275,next_year=927,year_audit=str((YEAR/'year-audit.json').relative_to(ROOT)))
 if vol==275:old.update(batches=parts,batch_totals=totals)
 write(folder/'progress-audit.json',old)
 (folder/'README.md').write_text(f'# 《资治通鉴》卷{vol} · 926年\n\n本卷{len(rows)}正文段全部发布并匿名回查。926年两卷共110正文段、13个批次全部完成，全年源行、哈希、逐字摘录、公开引用和URL审计见卷275/year-0926/year-audit.json。\n\n下一段zztj-v275-y0927-p001。927年共57段，尚待录入；目标仍为936年后唐灭亡。\n')
(P/'README.md').write_text('''# 《资治通鉴》卷275 · 926年 · part-08

末7段（第61—67段，原文件66—72行）已发布：34事件、51参与、161事实引用，新增5人、4条关系；10个来源记录，补证《旧五代史》《新五代史》。新人物为朱弘昭、王延禀、陈陶（福州指挥使）、崔氏（王延翰妻）、李从荣。

按序处理蜀犒军及财赋转运、孟府库与州税答话、安两川疑制、李严请任和母言、朱任东川、告身制度及长兴以后延叙、闽采女谏隙至十二月内乱捕杀推立、卢文进及从荣任官、金帛到洛与吴越改宝正及后省称。

主五百万/新六百万及募集主体、两书余二百万分别保留，混合财物不算全现金军费。李母预言非已死，实际杀监留927；告身后时延叙不填926。闽弑父为延禀指控，妻名姓确认与罪行真实性分开，主未言妻同斩。福州军使陈陶不并既有雅州陈陶；兄长、养父、妻子、父亲关系各有明文且方向明确。卢主癸已疑巳/旧甲午存日异，金帛十亿单位不明不加缗，吴越后复通年未知不强本年。

批次原文与公开引用、固定GitHub URL匿名回查见publication.json、readback-audit.json。926年卷274的43段与卷275的67段共110正文段、13批完成全年联合审计，见上级year-audit.json。年界标题分隔不生史事，927年57段仍pending；下一段zztj-v275-y0927-p001，目标仍为录至936年后唐灭亡。
''')
print(dict(year_complete=926,body_paragraphs=110,batches=13,next_year=927,next_paragraph=next_rows[0]['id'],next_year_body_paragraphs=57))
