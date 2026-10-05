# -*- coding: utf-8 -*-
"""Audit only volume 290's 952 coverage; the same year continues in volume 291."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists())
YEAR=P.parent
load=lambda f:json.loads(f.read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
groups={'source':'sources','person':'people','event':'events','person_relationship':'person_relationships','person_event':'person_events','fact_claim':'claims'}
q=load(YEAR/'paragraphs.json');bd=load(YEAR/'boundaries.json');d=load(ROOT/'content/yearly-progress.json');ix=load(ROOT/'content/books/zizhi-tongjian/index.json');c=load(P/'coverage.json');b=load(P/'content-batch.json');a=load(P/'publication.json')
assert d['active_cursor']['next_paragraph']==q[32]['id'] and len(q)==37
assert all(x['status']=='published_verified' for x in q[:32]) and all(x['status']=='reviewed' for x in q[32:])
assert c['paragraphs']==[x['id'] for x in q[32:]] and c['next_paragraph']=='zztj-v291-y0952-p001' and c['next_year']==952 and c['next_volume']==291
assert a['verified'] and a['batch_sha256']==sha(P/'content-batch.json') and a['public_counts']=={t:len(b[g]) for t,g in groups.items()}
raw=(ROOT/bd['source_file']).read_text().splitlines();assert sha(ROOT/bd['source_file'])==bd['source_sha256']
assert [x['source_line'] for x in q]==list(range(90,127)) and all(x['text']==raw[x['source_line']-1] for x in q)
assert raw[88]=='广顺二年壬子，公元九五二年' and raw[126:]==['','']
for x in bd['structural_items']:assert x['text']==raw[x['source_line']-1] and x['status']=='excluded_non_body_verified' and not x['event_keys']
y=next(x for x in d['year_coverage'] if x['year']==952);rel=str(P.relative_to(ROOT));assert rel not in y['batches'] and y['volumes']==[290,291]
paths=y['batches']+[rel];flat=[];checks=[]
for path in paths:
 pp=ROOT/path;bb=load(pp/'content-batch.json');aa=load(pp/'publication.json');cc=load(pp/'coverage.json')
 assert cc['volume']==290 and cc['year']==952
 assert aa['verified'] and aa['batch_sha256']==sha(pp/'content-batch.json') and aa['public_counts']=={t:len(bb[g]) for t,g in groups.items()}
 assert any(x['stage']=='anonymous_readback_verified' for x in aa['stages'])
 for m in load(pp/'sources/manifest.json'):assert sha((pp/'sources'/m['file']).resolve())==m['sha256']
 for pid in cc['paragraphs']:
  row=next(x for x in q if x['id']==pid);assert row['batch_key']==bb['batch_key'] and row['event_keys'] and set(row['event_keys'])<={x['key'] for x in bb['events']}
 flat.extend(cc['paragraphs']);checks.append(dict(path=path,batch_key=bb['batch_key'],batch_sha256=aa['batch_sha256'],paragraphs=cc['paragraphs'],public_counts=aa['public_counts'],source_snapshots_verified=True))
assert flat==[x['id'] for x in q]
nextdir=ROOT/'content/books/zizhi-tongjian/vol-291/year-0952';qq=load(nextdir/'paragraphs.json');bbd=load(nextdir/'boundaries.json');rr=(ROOT/bbd['source_file']).read_text().splitlines()
assert len(qq)==25 and all(x['status']=='pending' and not x['event_keys'] for x in qq)
assert sha(ROOT/bbd['source_file'])==bbd['source_sha256'] and [x['source_line'] for x in qq]==list(range(6,31)) and all(x['text']==rr[x['source_line']-1] for x in qq)
assert rr[4]=='广顺二年壬子，公元九五二年' and qq[0]['text'].startswith('九月，甲寅朔，') and rr[30]=='◎' and rr[31]=='广顺三年癸丑，公元九五三年'
for row in q[32:]:row['status']='published_verified'
save(YEAR/'paragraphs.json',q)
bd['note']='卷290广顺二年原90—126行37段，分5批连续发布并匿名读回；卷末127—128行为空行。月份承接疑问见各批校核说明。仍须继续卷291同年九月至年末25段，不能记本年完成。'
save(YEAR/'boundaries.json',bd)
y.update(status='partial_published_verified',batches=paths,completed_volumes=[290],note='952年跨卷290、291共62正文。卷290的37段已连续发布并通过本卷覆盖审计；卷291九月以后25段仍待录，全年尚未完成。')
d['active_cursor'].update(volume=291,year=952,last_reviewed_paragraph=q[-1]['id'],last_published_paragraph=q[-1]['id'],next_paragraph=qq[0]['id'],next_paragraph_opening=qq[0]['text'],batch=rel,status='pending')
ix.update(current_year=952,current_volume=291,current_volumes=[290,291],current_batch=rel,next_paragraph=qq[0]['id'])
save(ROOT/'content/yearly-progress.json',d);save(ROOT/'content/books/zizhi-tongjian/index.json',ix)
audit=dict(book='资治通鉴',volume=290,year=952,verified=True,verified_at=datetime.now(timezone.utc).isoformat(),published_body_count=37,body_ids=flat,batches=checks,boundary_checks=dict(source_sha256=bd['source_sha256'],body_lines=[90,126],trailing_empty_lines=[127,128],continuation_volume=291,continuation_year=952,next_body_line=6,pending_continuation_count=len(qq)),scope='只核本卷37段连续录入和逐批发布读回，未解决的月序及异文仍保留。952年在卷291尚有25段待录，完整目标至卷294末959年也未完成。',next_paragraph=qq[0]['id'])
save(YEAR/'volume-completion-audit.json',audit)
(P/'README.md').write_text('# 《资治通鉴》卷290 · 952年第33—37段\n\n原122—126行五段已发布并匿名读回，新增17事件、4人物、74事实引用。身份、月序和原文解释见 coverage.json，发布证据见 publication.json。\n\n卷290本年37段正文已完成连续覆盖审计；下一段 `zztj-v291-y0952-p001`。全年62段还剩卷291的25段，目标至通鉴末尚未完成。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷290 · 952年\n\n原90—126行37正文分5批连续发布并匿名读回，本卷覆盖审计见 volume-completion-audit.json。月序等资料疑问按各批说明保留。\n\n952年跨卷290、291共62正文，现37段完成，卷291九月以后25段待录。下一段 `zztj-v291-y0952-p001`。旧内容集中校改停在935年；完整目标至卷294末959年尚未完成。\n')
print('verified volume 290 952 37/37; yearly 37/62; next',qq[0]['id'])
