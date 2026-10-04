# -*- coding: utf-8 -*-
"""Advance exactly ten verified body paragraphs; leave all later body paragraphs pending."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==77 and [x['source_line'] for x in r]==list(range(6,83)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:68]) and all(x['status']=='pending' and not x['event_keys'] for x in r[68:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[58:68]]
assert {k for x in r[58:68] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
for first,start,end in [(YEAR/'part-01',0,4),(YEAR/'part-02',4,8),(YEAR/'part-03',8,13),(YEAR/'part-04',13,18),(YEAR/'part-05',18,23),(YEAR/'part-06',23,34),(YEAR/'part-07',34,46),(YEAR/'part-08',46,58)]:
 firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
 assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[58]['id'],r[68]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[67]['id'],last_published_paragraph=r[67]['id'],next_paragraph=r[68]['id'],next_paragraph_opening=r[68]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前68段连续公开并独立匿名核验，全年80/89。卷279原64—73行刘昫核账免税、姚命相索自通死赵任、凤翔备蜀、李判六军与边奏、李肇迟朝、后唐两相罢、蜀李仁罕被谗杀族与李肇致仕、吴加荣辞受已录；第69段文州攻守待录，全年未完成。')
for key,n,note in [('appointment_draft_subject',63,'主又至学士院侦草麻省略到院主语，可能承李仁罕或宋从会；保动作与引用，不强定到院人物和参与边，待更明确版本或旁证。'),('tax_amount_unit_scope',59,'主338万未列单位，不补贯缗石；主长兴以前压缩，旧长兴4年12月以前明确，分列范围，不把主解929前。'),('suo_death_day',61,'主八月戊子退朝投洛水卒，旧八月丁亥卒；日异说保，同年同官同人不造两次死。'),('zhao_feng_appointment_day',61,'主八月丙申赵太保，旧乙未；前安国与邢州军号地名同，不因异日造二命。'),('liu_dismiss_clerks_character',66,'主皆相驾疑贺，新刘传闻罢欢呼相贺，展示校读摘录保原；新月华门提印引语独补，主无人从归不是新也具。'),('renhan_accusation_xiong_character',67,'主素凶疑字保，不据此造暴力；共谮有异志为指控非已证反叛，死诏是政治立场。'),('renhan_death_versus_edict',67,'因入朝命武士执杀在主癸未罪诏前无独日，不能将捕杀都定癸未；子宋等死属此条未各具执行日。'),('renhan_family_scope',67,'主子继宏与宋等数人伏诛、新并族其家范围不同，各保原句，不编未名家属或自认主列全族名单。'),('khitan_report_event_dates',64,'己未云奏、辛酉石奏为报告日，不自动当战日；主百井屯报与旧十月代州部署是阶段区别，不互改地点。'),('xu_honours_declined',68,'主当年吴加荣位九锡后辞不受；旧935以后封齐加锡属于后阶段，不当前已接受或受禅。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[68]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=68,volume_total_paragraphs=77,year_completed_paragraphs=80,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[68]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=68)]))
bd['note']='934年本卷原6—82行77正文段；前68段原6—73行公开核验，原74行第69段文州攻守待录。全年跨卷278的12段和279的77段共89正文，当前80/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前68已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前80/89。下一段 zztj-v279-y0934-p069（原74行），卷与全年未完成。\n\n核旧税与免征、奏报战况、任免与迟朝、指控谋处置及罪诏执行、吴辞受分录；338万无单位、索与赵日期异说、三司吏疑字与李仁罕家族范围均保独立原文。\n')
print(dict(year=934,completed=80,total=89,next_paragraph=r[68]['id'],year_complete=False))
