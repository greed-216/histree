# -*- coding: utf-8 -*-
"""Advance only the verified consecutive first forty-one paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[36:41]]
assert {k for x in r[36:41] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[41:])
assert all(x['status']=='published_verified' for x in r[:36])
proofs=[]
for part,start,end in [(Y/'part-01',0,8),(Y/'part-02',8,12),(Y/'part-03',12,20),(Y/'part-04',20,28),(Y/'part-05',28,36),(P,36,41)]:
 ph=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==ph
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=ph,anonymous_readback_verified=True))
revision=ROOT/'content/revisions/2026-10-04-936-zhang-lingzhao-death'
rp=read(revision/'publication.json');assert rp['verified'] and rp['batch_sha256']==hashlib.sha256((Y/'part-04/content-batch.json').read_bytes()).hexdigest() and rp['revision_sha256']==hashlib.sha256((revision/'fields.json').read_bytes()).hexdigest()
revision_proof=dict(path=str(revision.relative_to(ROOT)),revision_sha256=rp['revision_sha256'],anonymous_readback_verified=True)
for x in r[36:41]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[36]['id'],r[41]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[40]['id'],last_published_paragraph=r[40]['id'],next_paragraph=r[41]['id'],next_paragraph_opening=r[41]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—41段公开并独立匿名核验，41/70；下一段晋安寨粮竭、张敬达被杀与降军处置。前段仍用后唐清泰三年。')
for key,n,note in [('jin_accession_dates',37,'主己亥改元不当册日，辽十一月丁酉与旧唐闰月丁卯册异时序保；备坛辽十月丁卯另动作。'),('sixteen_prefectures',37,'936割让约定与辽会同年图籍交付分阶段，州辖区不重复累加，政治父子不作血亲。'),('zhao_secret_offer',38,'赵延寿献物诈称和议与父密约求帝分，兄弟之国政治条款不建亲属，德光欲许不当已成。'),('sang_persuasion',39,'帝为新晋石，军粮忠信与竭财为桑论据；新桑传和旧外国传正文补，旧桑夹引通鉴不独证。'),('long_plan_reuse',40,'主到同旧龙传议赵和千骑救寨，复用2事件5参与；国近亲未具具体谱系，主介休新平遥并列。'),('dan_militia_kang',41,'康承询非康承训，丹逐与延杀杨分；前奔鄜和旧闰壬戌停任配流邓分，原赴延州义军乱保叙法。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[41]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=41,volume_total_paragraphs=70,year_completed_paragraphs=41,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[41]['id'],batches=proofs,revisions=[revision_proof]))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头41段公开核验，剩29段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—41段已公开并独立匿名核验，41/70；下一段 zztj-v280-y0936-p042，晋安寨粮竭、张敬达被杀与降军处置。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡尚未完成录入。\n')
print(dict(completed=41,total=70,next=r[41]['id']))
