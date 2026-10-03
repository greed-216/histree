# -*- coding: utf-8 -*-
"""Advance only the exact consecutive prefix backed by publication and public audits."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==57 and [x['source_line'] for x in r]==list(range(36,93))
assert all(x['text']==lines[x['source_line']-1] for x in r) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['status']=='published_verified' for x in r[:30]) and all(x['status']=='pending' and not x['event_keys'] for x in r[30:])
proof=[]
for part,start,end in [('part-01',0,10),('part-02',10,20),('part-03',20,30)]:
 p=YEAR/part;b=read(p/'content-batch.json');sha=hashlib.sha256((p/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(p/f);assert a['verified'] and a['batch_sha256']==sha
 assert read(p/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 assert {k for x in r[start:end] for k in x['event_keys']}=={x['key'] for x in b['events']}
 proof.append(dict(batch=str(p.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[20]['id'],r[30]['id']]
pr['active_cursor'].update(volume=278,year=933,last_reviewed_paragraph=r[29]['id'],last_published_paragraph=r[29]['id'],next_paragraph=r[30]['id'],next_paragraph_opening=r[30]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==933)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278],completed_volumes=[],note='卷278原36—65行连续前30正文段公开核验，全年57段，当前30/57，后27待录。第三批含闽国计、蜀册礼、尊号军给、立储元帅、吴立后、枢密换任及唐使海难追叙；全年及全卷未完成。')
for n,key in [(22,'shu_ceremony_glyph'),(23,'mingzong_honor_variant'),(24,'prince_deliberation_day'),(28,'feng_name_and_appointment_date'),(30,'zhang_voyage_date_location')]:
 full='933-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=r[n-1]['review']))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=278,current_year=933,current_volumes=[278],current_batch=rel,next_paragraph=r[30]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=933,completed_paragraphs=30,volume_total_paragraphs=57,year_completed_paragraphs=30,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=r[30]['id'],batches=proof,previous_year_audit=str((YEAR.parent/'year-0932/year-audit.json').relative_to(ROOT))))
bd['note']='原36—92行57个连续正文段；前30已发布公开核验，余27待录，下一段原66行李赞化昭信节度使。全年未完成；93分隔94年标题另列。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 933年\n\n原35行年标题、36—92行57个连续正文段。前30段已公开匿名核验，后27段待录，下一段zztj-v278-y0933-p031（原66行）。93分隔及94行934标题另列。全年未完成。\n')
print(dict(year=933,completed=30,total=57,next_paragraph=r[30]['id'],year_complete=False))
