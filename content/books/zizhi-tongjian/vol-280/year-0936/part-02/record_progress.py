# -*- coding: utf-8 -*-
"""Advance only the verified consecutive first twelve paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[8:12]]
assert {k for x in r[8:12] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[12:])
assert all(x['status']=='published_verified' for x in r[:8])
proofs=[]
for part,start,end in [(Y/'part-01',0,8),(P,8,12)]:
 ph=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==ph
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=ph,anonymous_readback_verified=True))
for x in r[8:12]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[8]['id'],r[12]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[11]['id'],last_published_paragraph=r[11]['id'],next_paragraph=r[12]['id'],next_paragraph_opening=r[12]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—12段公开并独立匿名核验，12/70；下一段昭义奏石敬瑭反及后唐讨河东部署。前段仍用后唐清泰三年。')
for key,n,note in [('divination_year',12,'主术者今年、旧有人明年并列，记作占验话语，不强定追叙年。'),('chu_background_and_names',9,'马希杲与希萼分人；裴指称、华夫人请赎、王巡视解释各归说话者。夜庭、赢疾底本疑字留原。'),('transfer_vs_execution',12,'庚寅夜草制、辛卯任命、甲午催行与幕僚决议分，不以任命推已经赴镇；杨彦询获保护不当已被杀。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[12]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=12,volume_total_paragraphs=70,year_completed_paragraphs=12,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[12]['id'],batches=proofs))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头12段公开核验，剩58段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—12段已公开并独立匿名核验，12/70；下一段 zztj-v280-y0936-p013，昭义奏石敬瑭反及后唐讨河东部署。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡尚未完成录入。\n')
print(dict(completed=12,total=70,next=r[12]['id']))
