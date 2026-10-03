# -*- coding: utf-8 -*-
"""Finish 933 only after its full public audit, then advance to pending 934."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
a=read(YEAR/'year-audit.json');r=read(YEAR/'paragraphs.json');assert a['verified'] and a['year_complete'] and a['body_paragraphs']==56 and a['next_year_body_paragraphs']==89
assert all(x['status']=='published_verified' for x in r[:56]) and r[56]['status']=='excluded_non_body_verified' and not r[56]['event_keys']
proof=[]
for part in sorted(YEAR.glob('part-*')):
 b=read(part/'content-batch.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert a['batch_sha256'][b['batch_key']]==sha
 for f in ['publication.json','readback-audit.json']:
  audit=read(part/f);assert audit['verified'] and audit['batch_sha256']==sha
 proof.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert len(proof)==7
next_year=YEAR.parent/'year-0934';rows=read(next_year/'paragraphs.json');assert len(rows)==12 and all(x['status']=='pending' and not x['event_keys'] for x in rows)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[49]['id'],rows[0]['id']]
pr['active_cursor'].update(volume=278,year=934,last_reviewed_paragraph=r[55]['id'],last_published_paragraph=r[55]['id'],next_paragraph=rows[0]['id'],next_paragraph_opening=rows[0]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==933)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',volumes=[278],completed_volumes=[278],note='卷278原36—91行56正文段全经七批发布及全年匿名精确核验；原92潞王上标题保留ID并排除事实。含同书异版校读及新旧五代史、辽史、宋史补证，异文与追叙年月未明项保持说明；下一年934跨卷278的12段和279的77段，全89段待录。')
if not any(x['year']==934 for x in pr['year_coverage']):pr['year_coverage'].append(dict(year=934,status='pending',volumes=[278,279],batches=[],completed_volumes=[],note='年界已回查，卷278原95—106行12段、卷279原6—82行77段，共89正文段全待录；从zztj-v278-y0934-p001开始，不提前记年或卷完成。'))
for key,n,note in [('palace_wang_consort',50,'司衣乳母王氏与王淑妃两人，主朱康告言与新传叙述层并列；私通不当夫妻，辛亥死仅司衣。'),('qian_yuanxiang_identity',53,'主钱元珦沿旧钱传珦，吴越传改元避讳名模式核同主体；确切转名及完整职任沿革仍待纸本补证，原元字保留。'),('wang_renda_death_chronology',55,'主933条族诛王仁达，新闽世家相近杀事置龙启三年改永和段，年代编排异说保，不硬同步死亡年。'),('ma_xiwang_glyph_and_retrospective',56,'主两处希旦、同书固定校版均希旺，规范同一母弟而保原字；全初段出生与死亡年未定，新希振弃官为道士非希旺请不许。')]:
 full='933-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=278,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=rows[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=933,completed_paragraphs=56,volume_total_paragraphs=56,year_completed_paragraphs=56,year_total_paragraphs=56,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=True,year_complete=True,excluded_ledger_non_body=1,next_volume=278,next_year=934,next_paragraph=rows[0]['id'],batches=proof,year_audit='year-audit.json',previous_year_audit=str((YEAR.parent/'year-0932/year-audit.json').relative_to(ROOT))))
bd=read(YEAR/'boundaries.json');bd['note']='933年原36—91行56正文段经七批及全年匿名公开核验。原92潞王上为下一节标题，保留ID排除；93分隔94标题另列。934年本卷95—106行12段全待录，下一卷279同年77段待录。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 933年\n\n原36—91行56正文段经七批全部发布，并以audit_year.py按精确公开ID、出处关联、原文逐字摘录与固定Git哈希完成全年核验。原92行潞王上标题保留ID，排除正文；93分隔及94行934年题另列。\n\n追叙、异名及各书年代差异保留说明；身份与出处修订有独立档案。933年完成，卷278整体仍有934年12段待录。下一段zztj-v278-y0934-p001，934年跨卷278、279共89正文段全待录。\n')
(P/'README.md').write_text('# 《资治通鉴》卷278 · 933年 · 第七批\n\n连续第50—56正文段（原85—91行）：司衣王氏案、宋令询出镇、孟知祥评新廷、闵帝初政与明州钱元珦、福州改府、王仁达遇害、楚兄弟追叙。旧新五代史补证，固定音注版作同书校读。\n\n司衣王氏与王淑妃分人，乳母与养母分边；主两处希旦据同书校版校读希旺而保底本原字，不新增疑似异字人。新闽世家王仁达杀事的段落年代与主不同，保异说。初段出生、隔离与死亡年月未知，不硬挂933。\n\n本批公开核验后，全年56正文段均经独立year-audit.json核验；第57标题排除，933年完成。下一段zztj-v278-y0934-p001；后唐灭亡目标仍待推进至936。\n')
print(dict(year=933,complete=True,body_paragraphs=56,next_year=934,next_paragraph=rows[0]['id'],next_year_body_paragraphs=89))
