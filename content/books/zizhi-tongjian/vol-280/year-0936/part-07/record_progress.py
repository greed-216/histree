# -*- coding: utf-8 -*-
"""Advance only the verified consecutive first forty-seven paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[41:47]]
assert {k for x in r[41:47] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[47:])
assert all(x['status']=='published_verified' for x in r[:41])
proofs=[]
for part,start,end in [(Y/'part-01',0,8),(Y/'part-02',8,12),(Y/'part-03',12,20),(Y/'part-04',20,28),(Y/'part-05',28,36),(Y/'part-06',36,41),(P,41,47)]:
 ph=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==ph
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=ph,anonymous_readback_verified=True))
revision=ROOT/'content/revisions/2026-10-04-936-zhang-lingzhao-death'
rp=read(revision/'publication.json');assert rp['verified'] and rp['batch_sha256']==hashlib.sha256((Y/'part-04/content-batch.json').read_bytes()).hexdigest() and rp['revision_sha256']==hashlib.sha256((revision/'fields.json').read_bytes()).hexdigest()
revision_proof=dict(path=str(revision.relative_to(ROOT)),revision_sha256=rp['revision_sha256'],anonymous_readback_verified=True)
extra=ROOT/'content/revisions/2026-10-04-936-jingda-kang-deaths'
xp=read(extra/'publication.json')
assert xp['verified'] and xp['batch_sha256']==h and xp['revision_sha256']==hashlib.sha256((extra/'fields.json').read_bytes()).hexdigest()
extra_proof=dict(path=str(extra.relative_to(ROOT)),revision_sha256=xp['revision_sha256'],anonymous_readback_verified=True)

for x in r[41:47]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[41]['id'],r[47]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[46]['id'],last_published_paragraph=r[46]['id'],next_paragraph=r[47]['id'],next_paragraph_opening=r[47]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—47段公开并独立匿名核验，47/70；下一段赵德钧见述律及晋、契丹告别南下。前段仍用后唐清泰三年。')
for key,n,note in [('jingda_killers',42,'主安未忍后杨斩，旧张传与辽合写杨安杀，各说保；甲子张死，康独卒日不明。'),('surrender_horses',42,'主旧五千马与甲仗取出塞，辽五千马赐晋异说，不强推两去向均完成。削A081保底本占位。'),('chonggui_family',43,'生父敬儒、养父石、母安氏各向明确，主兄子与父敬儒定敬儒兄长；幼年收养及父卒年不置936。'),('tuanbai_dates',43,'主丁卯战退与辽庚午奏追、辛未过谷不同阶段异日保，不把报日至此败日。'),('congke_report_return',44,'己巳回怀州知晋立、杨降是报告日；魏州众议未名，刺薛几欲未执行、南还采纳与壬申河阳到达分。'),('luzhou_surrender',47,'旧其部曲千余回指有歧不硬定时赛队数，高告无粮为其说；甲戌受降、西郊命杀银鞍三千、赵锁送分。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[47]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=47,volume_total_paragraphs=70,year_completed_paragraphs=47,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[47]['id'],batches=proofs,revisions=[revision_proof,extra_proof]))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头47段公开核验，剩23段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—47段已公开并独立匿名核验，47/70；下一段 zztj-v280-y0936-p048，赵德钧见述律及晋、契丹告别南下。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡尚未完成录入。\n')
print(dict(completed=47,total=70,next=r[47]['id']))
