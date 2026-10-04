# -*- coding: utf-8 -*-
"""Advance only the verified consecutive first twenty paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[12:20]]
assert {k for x in r[12:20] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[20:])
assert all(x['status']=='published_verified' for x in r[:12])
proofs=[]
for part,start,end in [(Y/'part-01',0,8),(Y/'part-02',8,12),(P,12,20)]:
 ph=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==ph
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=ph,anonymous_readback_verified=True))
for x in r[12:20]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[12]['id'],r[20]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[19]['id'],last_published_paragraph=r[19]['id'],next_paragraph=r[20]['id'],next_paragraph_opening=r[20]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—20段公开并独立匿名核验，20/70；下一段范延光拔魏州、诛张令昭及党部。前段仍用后唐清泰三年。')
for key,n,note in [('army_dates',13,'主乙巳排陈丙午部署、旧乙卯部署丙辰杨副命并列，官衔层次不偷换。'),('an_background_terms',14,'后三万待卫疑字、代州伏州异地保；弟子古义不擅建师徒叔侄。安重荣步骑与旧骑、补己酉奏日分别。'),('weibo_dates',15,'主癸丑旧新壬子逐刘、主六月庚申旧辛酉削官异日并列，逃相州与至洛阳分阶段。'),('shi_family_names_dates',18,'重殷沿同官同井同重裔之旧重英；主戊子旧己丑诛二子，敬德死狱与旧沂州奏诛异表述保。石重裔不擅并新重胤，从弟用从兄保亲属范围。'),('yunzhou_glyph_and_days',20,'沙名私用字沿旧沙彥珣，丁酉是奏表、实际二夜三日分。桑奏尹逐沙与沙奏桑反并列为各自说法；擒送与行刑日不强同日。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[20]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=20,volume_total_paragraphs=70,year_completed_paragraphs=20,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[20]['id'],batches=proofs))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头20段公开核验，剩50段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—20段已公开并独立匿名核验，20/70；下一段 zztj-v280-y0936-p021，范延光拔魏州、诛张令昭及党部。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡尚未完成录入。\n')
print(dict(completed=20,total=70,next=r[20]['id']))
