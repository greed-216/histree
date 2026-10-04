# -*- coding: utf-8 -*-
"""Advance the verified continuous prefix from eleven to twenty paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==37 and [x['source_line'] for x in r]==list(range(85,122)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:20]) and all(x['status']=='pending' and not x['event_keys'] for x in r[20:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
proofs=[]
for part,start,end in [(YEAR/'part-01',0,11),(P,11,20)]:
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
assert {k for x in r[11:20] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent/'year-0934';prior=read(previous/'paragraphs.json');annual=read(previous/'progress-audit.json')
assert len(prior)==77 and all(x['status']=='published_verified' for x in prior) and annual['year_complete'] and annual['year_completed_paragraphs']==89
for proof in annual['batches']:
 part=ROOT/proof['batch'];h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert h==proof['batch_sha256']
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[11]['id'],r[20]['id']]
pr['active_cursor'].update(volume=279,year=935,last_reviewed_paragraph=r[19]['id'],last_published_paragraph=r[19]['id'],next_paragraph=r[20]['id'],next_paragraph_opening=r[20]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==935)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[279],completed_volumes=[],note='卷279本年37正文，前20段原85—104行连续公开并独立匿名核验。新增史在德言事、吴景迁加职陈辅、唐蜀任官、杨檀赐名、柴死问功、应州寇、河东粮运与忻州处死军士、严刑诏。第21段闽李春燕待录，全年20/37未完成。')
for key,num,note in [('liu_yanhao_appointment_month',14,'主旧四月辛卯刘延皓任枢密，新五月辛卯，同人同职保月异说，不造两任、不自动校新月份。'),('liu_yanlang_appointment_order',14,'主癸巳刘延郎任官，旧同官命置辛卯条后未另列日；保编次。延郎与延朗同人，不因同姓推皇后弟；刘后姐姐仅明确延皓。'),('yang_tan_office_before_name',16,'旧同年二月庚午杨檀由振武移定州，旧五月称定州，主五月仍称振武；补任官前文并保主衔。赐名光远同稳定主体。'),('xinzhou_execution_report_dates',19,'主六月叙事处死李晖等36，旧七月丙申奏斩；奏日和执行日层次不同，原说并列。谋乱为奏报理由非独证；旧附契丹国志同文有依赖，不算新独证或新增专书。'),('li_hui_distinct_identity',19,'935挟马都将李晖与902同名人物尚无同人证明，单建限定主体，避免误合或将旧人物死年覆为935。'),('shi_background_and_spies',19,'既还镇自全、常议夜谈、贿曹左右、宾前自称属未具始年的背景，年null；两子内使未具名，不猜名字；曹不自动当收贿亲探者。'),('grain_counts_and_region',19,'五万单位绢匹、1500单位车乘，命令不等于全部已运到；主镇冀、旧镇州及山东/河北地域层次分别保，山东非现代省。')]:
 full='935-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[num-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=935,current_volumes=[279],current_batch=rel,next_paragraph=r[20]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=935,completed_paragraphs=20,volume_total_paragraphs=37,year_completed_paragraphs=20,year_total_paragraphs=37,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=935,next_paragraph=r[20]['id'],batches=proofs,year_scope=[dict(volume=279,body_paragraphs=37,published=20)]))
bd['note']='935年原85—121行37正文，前20段原85—104行公开核验，原105行第21段闽李春燕待录。包括臣光曰评论段，不跳段；全年未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 935年\n\n原85—121行37正文段，前20段已连续发布并独立匿名核验，全年20/37未完成。下一段 zztj-v279-y0935-p021（原105行），闽福王与李春燕。\n\n两批涵盖闽改元、夏州继任、尊号与唐蜀任官、言事开放、景迁辅政、改名及边寇、粮运和忻州军士处死。异名、同名和年月异说分别保原文；两子内使未具名、背景始年未明项均保不确定。原115行臣光曰仍在待录账本；原124行后晋纪为结构标题，后接卷280的936年。\n')
print(dict(year=935,completed=20,total=37,next_paragraph=r[20]['id'],year_complete=False))
