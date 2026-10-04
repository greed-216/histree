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
assert all(x['status']=='published_verified' for x in r[:4]) and all(x['status']=='pending' and not x['event_keys'] for x in r[4:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[:4]]
assert {k for x in r[:4] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[0]['id'],r[4]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[3]['id'],last_published_paragraph=r[3]['id'],next_paragraph=r[4]['id'],next_paragraph_opening=r[4]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279首4段连续公开并独立匿名核验，全年16/89。卷279原6—9行赵季良授职、吴迁都争议及禅代追叙、己卯三镇调令、金陵两次火及徐复府已录；卷279第5段凤翔拒命长段待录，全年未完成。')
for key,n,note in [('zhou_chizhou_office',2,'主池州副使、新南唐世家池州刺史官名并列；先是及久之所引谋禅、贬复职均未独年月，不硬定934二月。'),('jinling_fire_month',4,'主二月甲申乙酉两火，新吴世家大和六年闰正月金陵火罢建都；月份及罢都顺序异说并列，不强绑定某一次火。'),('three_town_orders',3,'三镇己卯调令与实际到任不同；主徙节度兼北都、旧权北京镇州邺都职名层次并列，皆宣无制与遣监送不等三人已经抵镇。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[4]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=4,volume_total_paragraphs=77,year_completed_paragraphs=16,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[4]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=4)]))
bd['note']='934年本卷原6—82行77正文段；前4段原6—9行公开核验，原10行第5段仍待录。全年跨卷278的12段和279的77段共89正文，当前16/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前4已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前16/89。下一段zztj-v279-y0934-p005（原10行），卷与全年未完成。\n\n迁都、禅代意向与实际行动分录；先是及久之未强定本年。周宗贬职官名、金陵火灾月份保留主补书异说。\n')
print(dict(year=934,completed=16,total=89,next_paragraph=r[4]['id'],year_complete=False))
