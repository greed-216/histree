# -*- coding: utf-8 -*-
"""Advance only the verified consecutive first twenty-eight paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[20:28]]
assert {k for x in r[20:28] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[28:])
assert all(x['status']=='published_verified' for x in r[:20])
proofs=[]
for part,start,end in [(Y/'part-01',0,8),(Y/'part-02',8,12),(Y/'part-03',12,20),(P,20,28)]:
 ph=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==ph
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=ph,anonymous_readback_verified=True))
revision=ROOT/'content/revisions/2026-10-04-936-zhang-lingzhao-death'
rp=read(revision/'publication.json');assert rp['verified'] and rp['batch_sha256']==h and rp['revision_sha256']==hashlib.sha256((revision/'fields.json').read_bytes()).hexdigest()
revision_proof=dict(path=str(revision.relative_to(ROOT)),revision_sha256=rp['revision_sha256'],anonymous_readback_verified=True)
for x in r[20:28]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[20]['id'],r[28]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[27]['id'],last_published_paragraph=r[27]['id'],next_paragraph=r[28]['id'],next_paragraph_opening=r[28]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—28段公开并独立匿名核验，28/70；下一段李从珂欲亲征及朝臣劝议。前段仍用后唐清泰三年。')
for key,n,note in [('weizhou_final_dates',21,'主丁未拔斩、新戊申克壬子斩、旧戊申奏21日收城壬子献首并列，七指挥为军单位处置诏。'),('appeal_promise_vs_execution',23,'父礼称臣割地是约事捷条件，非血缘或已交16州。辽赵莹经卢、桑再告急、萧报期独立记，不指派主未名间使。'),('jinyang_battle_counts_dates',28,'主辛丑辽庚子战、甲辰奏战15日，主步兵近万辽数万级保约数与各书层次；主刘劝杀与旧汉高祖纪补实际尽杀分独立证据，不因主未记结果而否认旧执行记载。'),('jinyang_routes_and_siege',28,'主壬寅辽癸卯围、当夕旧塹围层次并列；悄孤飞狐、耀辉、赢涉晋陷疑字原保。的鲁此役战死新独补，未具独立日，三路援是诏非都到。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[28]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=28,volume_total_paragraphs=70,year_completed_paragraphs=28,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[28]['id'],batches=proofs,revisions=[revision_proof]))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头28段公开核验，剩42段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—28段已公开并独立匿名核验，28/70；下一段 zztj-v280-y0936-p029，李从珂欲亲征及朝臣劝议。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡尚未完成录入。\n')
print(dict(completed=28,total=70,next=r[28]['id']))
