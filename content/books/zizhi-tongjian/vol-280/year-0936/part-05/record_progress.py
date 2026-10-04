# -*- coding: utf-8 -*-
"""Advance only the verified consecutive first thirty-six paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[28:36]]
assert {k for x in r[28:36] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[36:])
assert all(x['status']=='published_verified' for x in r[:28])
proofs=[]
for part,start,end in [(Y/'part-01',0,8),(Y/'part-02',8,12),(Y/'part-03',12,20),(Y/'part-04',20,28),(P,28,36)]:
 ph=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==ph
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=ph,anonymous_readback_verified=True))
revision=ROOT/'content/revisions/2026-10-04-936-zhang-lingzhao-death'
rp=read(revision/'publication.json');assert rp['verified'] and rp['batch_sha256']==hashlib.sha256((Y/'part-04/content-batch.json').read_bytes()).hexdigest() and rp['revision_sha256']==hashlib.sha256((revision/'fields.json').read_bytes()).hexdigest()
revision_proof=dict(path=str(revision.relative_to(ROOT)),revision_sha256=rp['revision_sha256'],anonymous_readback_verified=True)
for x in r[28:36]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[28]['id'],r[36]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[35]['id'],last_published_paragraph=r[35]['id'],next_paragraph=r[36]['id'],next_paragraph_opening=r[36]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—36段公开并独立匿名核验，36/70；下一段石敬瑭即位、割十六州及赵德钧求镇州。前段仍用后唐清泰三年。')
for key,n,note in [('northern_campaign_glyphs',29,'雍正重美沿封雍李重美，目疾为原话不诊断；刘延皓与刘延朗分，戊申发京、己酉后援命分。'),('long_min_plans',30,'立李赞华主明确议不决、旧不能用；千骑入寨为旧传另一未实行方案，夹引通鉴胡注不当独立确证。'),('conscription_standard',31,'主七户、新刘景岩传七户、旧正文十户并列；征命、未来限期、教战与统计评价分。'),('zhao_army_routes',32,'原九月飞狐后袭命与准改土门分，银鞍契丹直是赵军；刘先戍始年空、当前并军936行程分，三地职戍籍不合。'),('southern_han_liu_jun_identity',33,'主刘浚与新劉濬同南汉同父刘崇望识别，避乱背景未知年不造新确年事件。'),('liujingyan_variants',36,'主刘景岩旧景严新景巖同杨兵变同地官合人，主旧前坊新前丹差异保，高万金非郎万金。丁酉奏授不当杨死日；杨卒年936明确。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[36]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=36,volume_total_paragraphs=70,year_completed_paragraphs=36,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[36]['id'],batches=proofs,revisions=[revision_proof]))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头36段公开核验，剩34段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—36段已公开并独立匿名核验，36/70；下一段 zztj-v280-y0936-p037，石敬瑭即位、割十六州及赵德钧求镇州。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡尚未完成录入。\n')
print(dict(completed=36,total=70,next=r[36]['id']))
