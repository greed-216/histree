# -*- coding: utf-8 -*-
"""Advance verified volume-278 year-934 slice; the full year remains incomplete."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==12 and [x['source_line'] for x in r]==list(range(95,107)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] and x['status']=='published_verified' for x in r)
proofs=[]
for part,start,end in [(YEAR/'part-01',0,7),(P,7,12)]:
 b=read(part/'content-batch.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==sha
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 assert {k for x in r[start:end] for k in x['event_keys']}=={x['key'] for x in b['events']}
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
other=YEAR.parent.parent/'vol-279/year-0934';more=read(other/'paragraphs.json');assert len(more)==77 and all(x['status']=='pending' and not x['event_keys'] for x in more)
prior=YEAR.parent/'year-0933';annual=read(prior/'year-audit.json');assert annual['verified'] and annual['year_complete'] and annual['body_paragraphs']==56
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[7]['id'],more[0]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[-1]['id'],last_published_paragraph=r[-1]['id'],next_paragraph=more[0]['id'],next_paragraph_opening=more[0]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278原95—106行12正文段两批全部公开并独立匿名核验；卷279同年77段仍待录，全年当前12/89。建州战、薛文杰与符彦超遇害、册太后太妃及孟知祥称帝已录；符被害月份、任驾儿任货儿等异文并列。933年度审计保留，934全年未完成。')
for key,n,note in [('fu_month_variant',10,'符彦超遇害主承闰月，旧纪闰月奏此月七日夜，旧本传应顺元年正月；保月份差异，丁巳是奏日，己酉旦讨乱不反推杀日。'),('ren_name_variant',10,'同案王希全小字佛留；主任驾儿与旧任货儿同谋、杀符、李端平乱对应合为同人异名，纸本待核。'),('tang_rui_text_dependency',9,'主过疏与旧夹注迂疏异文；旧夹注明确引通鉴，不作独立动机证据。'),('min_sorcerer_identity',8,'主盛韬与新闽世家徐彦，主吴勖与新吴英仍待身份校核，不凭相似情节或简繁转换合并。')]:
 full='934-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=more[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=934,completed_paragraphs=12,volume_total_paragraphs=12,year_completed_paragraphs=12,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=True,year_complete=False,next_volume=279,next_year=934,next_paragraph=more[0]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=0)],previous_year_audit=str((prior/'year-audit.json').relative_to(ROOT))))
bd['note']='934年本卷原95—106行12正文段两批全部公开核验；原107—108行为空白边界。全年跨卷278的12段和279的77段，共89正文段，当前12/89；下一卷279第1段原6行，全年仍未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 934年\n\n原95—106行12正文段，两批已发布并独立匿名核验。934年跨卷278的12段、卷279的77段，共89正文段，当前12/89。下一段zztj-v279-y0934-p001（原6行），全年未完成。\n\n卷统年题清泰元年；正月与闰正月闵帝应顺的具体年号按事件原文保。符彦超遇害月份、任驾儿异名及主补书差异见批次校核说明。\n')
print(dict(year=934,completed=12,total=89,next_paragraph=more[0]['id'],year_complete=False))
