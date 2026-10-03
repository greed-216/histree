# -*- coding: utf-8 -*-
"""Advance the consecutive 933 prefix only after independent public readback."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==57 and [x['source_line'] for x in r]==list(range(36,93))
assert all(x['text']==lines[x['source_line']-1] for x in r) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['status']=='published_verified' for x in r[:10]) and all(x['status']=='pending' and not x['event_keys'] for x in r[10:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
c=read(P/'coverage.json');assert c['paragraphs']==[x['id'] for x in r[:10]]
assert {k for x in r[:10] for k in x['event_keys']}=={x['key'] for x in b['events']}
prev=read(YEAR.parent/'year-0932/year-audit.json');assert prev['verified'] and prev['year_complete'] and prev['body_paragraphs']==49
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[0]['id'],r[10]['id']]
pr['active_cursor'].update(volume=278,year=933,last_reviewed_paragraph=r[9]['id'],last_published_paragraph=r[9]['id'],next_paragraph=r[10]['id'],next_paragraph_opening=r[10]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==933)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278],completed_volumes=[],note='卷278原36—45行连续首10正文段公开核验，全年57段，当前10/57，后47待录。正月闽与朝廷、二月蜀凉楚夏、三月移镇下制敕及四月催任按原段顺序；全年及全卷未完成。')
for n,key in [(1,'liuxu_glyph'),(2,'min_name_and_limin_identity'),(6,'renfu_death_month'),(8,'dingnan_transfer_dates_monitor'),(10,'imperial_examples_courier')]:
 full='933-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=r[n-1]['review']))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=278,current_year=933,current_volumes=[278],current_batch=rel,next_paragraph=r[10]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=933,completed_paragraphs=10,volume_total_paragraphs=57,year_completed_paragraphs=10,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=r[10]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)],previous_year_audit=str((YEAR.parent/'year-0932/year-audit.json').relative_to(ROOT))))
bd['note']='原36—92行57个连续正文段；前10已发布公开核验，余47待录，下一段原46行亲王师傅安排。全年未完成；93分隔94年标题另列。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷278 · 933年 · part-01\n\n连续首10段、原36—45行：24人物（10新增14复用）、30事件、56参与、2关系（1新增父亲1复用）、167事实引用、13出处（12新增1复用）。补证《旧五代史》《新五代史》；安从进来源沿930固定引用。\n\n秦与刘昫加任、闽龙传言改宅名及宝皇受册称帝、国号赦改元改名祖庙、两相枢密与唐使去留、孟地方五镇墨制、凉州请命与补书批准、楚加官、夏州父卒子立、孟封王、河西报告及朝廷移镇军令、五镇朝廷制授、三月敕四州与四月催任逐动作分录。\n\n闽臣李敏与昭宗旧名李敏不同，使用限定主体；刘昫与旧刘煦同日同职任相识同人，原字保留不当繁简字。王延钧主璘、新鏻称名各留，不重复造君；父亲关系检查已应用方向修正再复用。姓名检索修正见content/revisions/2026-10-04-wang-yanjun-lin。\n\n龙见为有言传闻，不当已证自然事实，宝皇为宗教受册叙事，不造神人亲属。追祖谥为身后礼，不把925已死审知复生。旧清泰元年遇弒与后续主935记事不同不提前当年死。凉州请授与旧新批准分，二千五百为唐旧戍回顾非933现有军数；使团杨通信补，主发言者未名，新归承谦单列，黄巢阻隔与唐亡层次各保。\n\n孟二月墨制与三月朝廷正式下制分，五军前留后与治州名由旧补，张知业沿张业，检校衔不当实际三公。仁福主二月戊午卒、旧传三月卒与旧三月奏闻分层；父亲李仁福→李彝超，旧次子补，生年未知。河西潜通契丹仅为报告，朝廷恐联兵侵略为担忧，不写已发生，起年null。三月移镇主癸未旧戊子异日并列、军名治名同任；主五万为军令数不是实到数；安重益主旧纪一致、旧传从益留异字。\n\n三月丁亥敕与四月李上言催任分，受命未到不写已到任；年少不能御是帝诏理由，不推生年。李从缺字严沿既有李继曮旧李从严身份例，王都李匡宾为过去敕例不重建当年覆族。使者旧苏继颜与传苏继彦疑字，不造双使。\n\n本批逐字摘录、快照哈希、匿名公开UUID及事实出处关联校验通过。933年10/57，下一段zztj-v278-y0933-p011，全年未完成；目标继续至936后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 933年\n\n原35行年标题、36—92行57个连续正文段。首10段已公开匿名核验，后47段待录，下一段zztj-v278-y0933-p011（原46行）。93分隔及94行934标题另列。全年未完成。\n')
print(dict(year=933,completed=10,total=57,next_paragraph=r[10]['id'],year_complete=False))
