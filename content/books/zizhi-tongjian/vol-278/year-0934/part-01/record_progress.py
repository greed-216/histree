# -*- coding: utf-8 -*-
"""Advance only the seven verified 934 paragraphs; preserve all pending continuation."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==12 and [x['source_line'] for x in r]==list(range(95,107)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r) and all(x['status']=='published_verified' for x in r[:7])
assert all(x['status']=='pending' and not x['event_keys'] for x in r[7:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[:7]]
assert {k for x in r[:7] for k in x['event_keys']}=={x['key'] for x in b['events']}
other=YEAR.parent.parent/'vol-279/year-0934';more=read(other/'paragraphs.json');assert len(more)==77 and all(x['status']=='pending' and not x['event_keys'] for x in more)
prior=YEAR.parent/'year-0933';annual=read(prior/'year-audit.json');assert annual['verified'] and annual['year_complete'] and annual['body_paragraphs']==56
for part in prior.glob('part-*'):assert hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()==annual['batch_sha256'][read(part/'content-batch.json')['batch_key']]
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[0]['id'],r[7]['id']]
pr['active_cursor'].update(volume=278,year=934,last_reviewed_paragraph=r[6]['id'],last_published_paragraph=r[6]['id'],next_paragraph=r[7]['id'],next_paragraph_opening=r[7]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[],note='934年首批卷278原95—101行7正文段公开匿名精确核验；本卷12段、卷279同年77段，全年89段，当前7/89。改应顺、换将、兼衔封王、迁居待吴与子女处置已录，第8段建州长叙待录。933年年度审计保留完成，934年和卷均未完成。')
for key,n,note in [('feng_zhongshuling_offer',3,'戊子冯被诏加中书令、坚辞不受、己丑改兼侍中分，不当实际就任中书令。'),('youcheng_huiming_identity',7,'主女惠明与旧皇长女尼惠明大师幼澄同人；新规范李幼澄保惠明等检索别名，旧后文举哀只作核身份不提前死亡年或日。'),('934_year_heading',1,'卷年题清泰是整年统题，当前正月闵帝改应顺，不当此时潞王已称帝。')]:
 full='934-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=278,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[7]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=934,completed_paragraphs=7,volume_total_paragraphs=12,year_completed_paragraphs=7,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_volume=278,next_year=934,next_paragraph=r[7]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)],year_scope=[dict(volume=278,body_paragraphs=12,published=7),dict(volume=279,body_paragraphs=77,published=0)],previous_year_audit=str((prior/'year-audit.json').relative_to(ROOT))))
bd['note']='934年本卷原95—106行12正文段，前7段公开核验，后5待录，下一段原102行建州长叙。全年跨卷278的12段和279的77段，共89正文段，当前7/89；卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 934年\n\n原95—106行12正文段，前7已发布并独立匿名核验，后5待录。934年跨卷278的12段、卷279的77段，共89正文段，当前7/89。下一段zztj-v278-y0934-p008（原102行），卷及全年未完成。\n\n卷统年题清泰元年；正月闵帝改应顺的具体年号按事件原文保，不提前记潞王即位。结构项另列、不计正文。\n')
print(dict(year=934,completed=7,total=89,volume_completed=7,volume_total=12,next_paragraph=r[7]['id'],year_complete=False))
