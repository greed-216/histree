# -*- coding: utf-8 -*-
"""Advance exactly five verified body paragraphs; leave all later body paragraphs pending."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==77 and [x['source_line'] for x in r]==list(range(6,83)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:23]) and all(x['status']=='pending' and not x['event_keys'] for x in r[23:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[18:23]]
assert {k for x in r[18:23] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
for first,start,end in [(YEAR/'part-01',0,4),(YEAR/'part-02',4,8),(YEAR/'part-03',8,13),(YEAR/'part-04',13,18)]:
 firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
 assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[18]['id'],r[23]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[22]['id'],last_published_paragraph=r[22]['id'],next_paragraph=r[23]['id'],next_paragraph_opening=r[23]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前23段连续公开并独立匿名核验，全年35/89。卷279原24—28行两镇降蜀、潞王入洛及废立、赏军筹资、闵帝孔氏遇害和宋令询自缢已录；第24段石敬瑭入朝待录，全年未完成。')
for key,n,note in [('conghou_death_method',23,'主拒饮毒酒后被王峦缢杀，旧闵纪遇鸩崩、新王弘贽传酒家日献后饮鸩不疑崩；各方法保来源，不编统一过程。'),('accession_deposition_dates',21,'主与旧末帝纪癸酉四日废、乙亥六日即位，新乙亥同主；旧闵纪五日即位七日废，日期顺序均异待纸核。'),('song_lingxun_ci_character',23,'主旧职磁州，新废帝纪慈州；原字保。宋死亡主无独日、旧辛巳邢州报死，奏报非死亡日，新戊寅条死之保书内位置。'),('two_towns_surrender_month',19,'主在四月条下记张孙以两镇降蜀未独日，新孟知祥世家三月兵溃后附蜀；六月成都见孟为后事勿前移。'),('kong_four_sons_identity',23,'孔氏与四子王峦回后被杀，回日未独载，勿强定四月戊寅。四子无逐名，此句不凭皇孙旧称猜名单；新补病后子幼不能从。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[23]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=23,volume_total_paragraphs=77,year_completed_paragraphs=35,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[23]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=23)]))
bd['note']='934年本卷原6—82行77正文段；前23段原6—28行公开核验，原29行第24段石敬瑭入朝仍待录。全年跨卷278的12段和279的77段共89正文，当前35/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前23已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前35/89。下一段 zztj-v279-y0934-p024（原29行），卷与全年未完成。\n\n两镇降蜀、入洛和正式废立、许赏与筹资、闵帝孔氏遇害及宋令询自缢已按行动分录。旧、新史废立日期与死亡方法分歧保独立引用，五个月房租预借按时长释读。\n')
print(dict(year=934,completed=35,total=89,next_paragraph=r[23]['id'],year_complete=False))
