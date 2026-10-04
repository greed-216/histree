# -*- coding: utf-8 -*-
"""Advance only the verified consecutive opening eight paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[:8]]
assert {k for x in r[:8] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[8:])
for x in r[:8]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[0]['id'],r[8]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[7]['id'],last_published_paragraph=r[7]['id'],next_paragraph=r[8]['id'],next_paragraph_opening=r[8]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—8段公开并独立匿名核验，8/70；下一段静江马希杲、楚汉边政。前段仍用后唐清泰三年。')
for key,n,note in [('khitan_peace_plan',5,'归俘、岁币为计划，新吕琦传补妻女方案；不是已归俘付钱或联姻。李赞华沿耶律倍、荝刺沿荝剌别名修订。'),('xue_office_date',6,'主935已称薛枢直，旧936正月官命补当前职，不覆盖旧记录或推首次任官。'),('min_era_compression',8,'主本年改通文，新将即位更名改元压缩；未名太后不造人。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[8]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=8,volume_total_paragraphs=70,year_completed_paragraphs=8,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[8]['id'],batches=[dict(batch=rel,batch_sha256=h,anonymous_readback_verified=True)]))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头8段公开核验，剩62段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—8段已公开并独立匿名核验，8/70；下一段 zztj-v280-y0936-p009，静江马希杲与楚汉边政。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡尚未完成录入。\n')
print(dict(completed=8,total=70,next=r[8]['id']))
