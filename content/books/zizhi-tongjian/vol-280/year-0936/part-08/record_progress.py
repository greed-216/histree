# -*- coding: utf-8 -*-
"""Advance only the verified consecutive first fifty-three paragraphs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
assert len(r)==70
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[47:53]]
assert {k for x in r[47:53] for k in x['event_keys']}=={x['key'] for x in b['events']}
assert all(x['status']=='pending' and not x['event_keys'] for x in r[53:])
assert all(x['status']=='published_verified' for x in r[:47])
proofs=[]
for part,start,end in [(Y/'part-01',0,8),(Y/'part-02',8,12),(Y/'part-03',12,20),(Y/'part-04',20,28),(Y/'part-05',28,36),(Y/'part-06',36,41),(Y/'part-07',41,47),(P,47,53)]:
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
assert xp['verified'] and xp['batch_sha256']==hashlib.sha256((Y/'part-07/content-batch.json').read_bytes()).hexdigest() and xp['revision_sha256']==hashlib.sha256((extra/'fields.json').read_bytes()).hexdigest()
extra_proof=dict(path=str(extra.relative_to(ROOT)),revision_sha256=xp['revision_sha256'],anonymous_readback_verified=True)

current_revision=ROOT/'content/revisions/2026-10-04-936-tang-fall-deaths'
cp=read(current_revision/'publication.json');assert cp['verified'] and cp['batch_sha256']==h and cp['revision_sha256']==hashlib.sha256((current_revision/'fields.json').read_bytes()).hexdigest()
current_proof=dict(path=str(current_revision.relative_to(ROOT)),revision_sha256=cp['revision_sha256'],anonymous_readback_verified=True)
merge=ROOT/'content/revisions/2026-10-04-zhang-yanqi-name'
mp=read(merge/'publication.json');assert mp['verified'] and mp['anonymous_readback_verified'] and mp['revision_sha256']==hashlib.sha256((merge/'plan.json').read_bytes()).hexdigest()
merge_proof=dict(path=str(merge.relative_to(ROOT)),revision_sha256=mp['revision_sha256'],anonymous_readback_verified=True)

for x in r[47:53]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[47]['id'],r[53]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[52]['id'],last_published_paragraph=r[52]['id'],next_paragraph=r[53]['id'],next_paragraph_opening=r[53]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[280],completed_volumes=[],note='卷280连续第1—53段公开并独立匿名核验，53/70；下一段旧朝重臣处分与晋朝收尾。前段仍用后唐清泰三年。')
for key,n,note in [('dejun_shulv_variant',48,'主太原可救与旧夹引不可救依赖校异非独证；赵卒937据旧天福二夏，幽州仅田宅所在非会见地点。'),('xiang_wen_identity',49,'主太相温旧大相温同五千护石核异写，不合辽迪离毕；至河梁与送洛叙法保。'),('gao_tian_rank',50,'主田建雄节度与旧节度副不同职保，原澤筠疑漢筠；见石主途中、旧入洛后飞诏召另时序。'),('zhang_yanqi_merge',51,'同连续军职和符彦饶回河阳链，张彦琪/琦已合到较早UUID，原参与及人物引用迁移，隐藏空重复主体，旧批不改。'),('bei_death_dates',51,'主丁丑条下杀倍、辽辛巳召同死拒后害连记日异；秦李为受遣，不把倍或二人并自焚死者。'),('heyang_dates',52,'主旧晋己卯河阳、旧唐庚辰、辽辛巳原日并存，待纸本；守南城、彰圣捕刘、释复位分。'),('tang_fall_order',53,'止焚全部宫与王曹避匿话在自焚之前插叙，新传清楚；明确同焚5人、倍另杀、石晚入旧第和次甲申入宫分。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=r[53]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=53,volume_total_paragraphs=70,year_completed_paragraphs=53,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_paragraph=r[53]['id'],batches=proofs,revisions=[revision_proof,extra_proof,current_proof,merge_proof]))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文，开头53段公开核验，剩17段待录；卷题天福元年，前段仍后唐清泰三年。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n连续第1—53段已公开并独立匿名核验，53/70；下一段 zztj-v280-y0936-p054，旧朝重臣处分与晋朝收尾。原文与繁体出处保底本，展示及匹配用简体；后唐灭亡核心段落已录，936年度尚未完成。\n')
print(dict(completed=53,total=70,next=r[53]['id']))
