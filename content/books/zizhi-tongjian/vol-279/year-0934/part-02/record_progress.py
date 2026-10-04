# -*- coding: utf-8 -*-
"""Advance exactly four verified body paragraphs; leave all later body paragraphs pending."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==77 and [x['source_line'] for x in r]==list(range(6,83)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:8]) and all(x['status']=='pending' and not x['event_keys'] for x in r[8:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[4:8]]
assert {k for x in r[4:8] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
first=YEAR/'part-01';firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[:4]]
proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[4]['id'],r[8]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[7]['id'],last_published_paragraph=r[7]['id'],next_paragraph=r[8]['id'],next_paragraph_opening=r[8]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前8段连续公开并独立匿名核验，全年20/89。卷279原10—13行凤翔拒命、劝谏与求援、辛卯与丁酉征军任命、重吉被拘及三月五节度合兵奏已录；第9段实际攻城待录，全年未完成。')
for key,n,note in [('ma_name_variant',5,'马胤孙与旧马裔孙字庆先、棣州商河籍及废帝履历相合保同人异名；主滴河字待校，不用自动繁简转换断避讳原因。'),('nanyi_identity_pending',5,'赧诩为主书推官使者，姓名暂无可靠独立补证，保原字、繁体赧詡及定位待纸本核；不臆改阮诩。'),('campaign_appointment_days',5,'主辛卯王思同任帅药彦稠副，丁酉加王同平章；旧闵帝纪将帅副任命并记丁酉，日期层次并列保留。'),('sun_hanshao_identity',8,'孙汉韶为李存进子，新义儿传明宗时复本姓；沿同一孙汉韶主体，不因父李姓另造李汉韶，复姓确年未载。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[8]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=8,volume_total_paragraphs=77,year_completed_paragraphs=20,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[8]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=8)]))
bd['note']='934年本卷原6—82行77正文段；前8段原6—13行公开核验，原14行第9段实际攻城仍待录。全年跨卷278的12段和279的77段共89正文，当前20/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前8已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前20/89。下一段zztj-v279-y0934-p009（原14行），卷与全年未完成。\n\n凤翔拒命、将佐劝谏、求援与朝廷征军任命按行动分录；檄中指控不作独立已核事实，派将、合兵奏与实际攻城区分。姓名与日期异文见批次校核说明。\n')
print(dict(year=934,completed=20,total=89,next_paragraph=r[8]['id'],year_complete=False))
