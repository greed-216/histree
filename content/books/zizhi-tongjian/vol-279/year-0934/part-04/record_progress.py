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
assert all(x['status']=='published_verified' for x in r[:18]) and all(x['status']=='pending' and not x['event_keys'] for x in r[18:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[13:18]]
assert {k for x in r[13:18] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
for first,start,end in [(YEAR/'part-01',0,4),(YEAR/'part-02',4,8),(YEAR/'part-03',8,13)]:
 firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
 assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[13]['id'],r[18]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[17]['id'],last_published_paragraph=r[17]['id'],next_paragraph=r[18]['id'],next_paragraph_opening=r[18]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前18段连续公开并独立匿名核验，全年30/89。卷279原19—23行西军进陕、康请降暂宥、闵帝出奔及洛阳请令争议、卫州驿变与孟汉琼被斩已录；第19段两镇降蜀待录，全年未完成。')
for key,n,note in [('chen_hui_identity_pending',17,'934石敬瑭亲将陈晖与909梁军马步都指挥使同名未证同人，先建陈晖（石敬瑭亲将）消歧；勿将其驿变死亡回填到909主体，后有证再合并。'),('weizhou_month_boundary',17,'主四月庚午朔未明遇石、旧三月二十九日夜；时界与随骑人数差分别保，不换公历调平。主刘知远引兵杀、旧新石敬瑭归责为不同层次。'),('ben_hongjin_variant',17,'主旧奔洪进，新王弘贽传奔弘进，同驿变与自刎对应同人异名；无证不改贲姓。'),('an_patrol_day_variant',14,'主丙寅安从进京城巡检，旧乙亥条下同诏，历日或电子编次疑点并列待纸核，不自动更改底字。'),('zhu_feng_death_days',15,'主旧戊辰朱井死、安杀冯，新闵纪丁卯早一日；己巳群臣获讯不是死亡日。'),('meng_execution_days',18,'主孟渑池西被斩在四月初字附记，独日未载；旧三月二十八日、新己巳记杀，保各书位置不强定主庚午死日。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[18]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=18,volume_total_paragraphs=77,year_completed_paragraphs=30,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[18]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=18)]))
bd['note']='934年本卷原6—82行77正文段；前18段原6—23行公开核验，原24行第19段两镇降蜀仍待录。全年跨卷278的12段和279的77段共89正文，当前30/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前18已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前30/89。下一段zztj-v279-y0934-p019（原24行），卷与全年未完成。\n\n西军进陕、洛阳出奔与朝臣请令、卫州驿变、孟汉琼被斩按行动分录；传闻、意向和执行区别。主旧新的日期、人数、责任叙述差异并列，934石亲将陈晖与909梁将暂不强并。\n')
print(dict(year=934,completed=30,total=89,next_paragraph=r[18]['id'],year_complete=False))
