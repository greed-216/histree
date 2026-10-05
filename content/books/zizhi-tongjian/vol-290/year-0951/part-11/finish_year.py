# -*- coding: utf-8 -*-
"""Advance 951 only after every consecutive paragraph and publication is verified."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'scripts/publish-book-batch.py').exists())
YEAR=P.parent
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
groups={'source':'sources','person':'people','event':'events','person_relationship':'person_relationships','person_event':'person_events','fact_claim':'claims'}
q=load(YEAR/'paragraphs.json');bd=load(YEAR/'boundaries.json');d=load(ROOT/'content/yearly-progress.json');ix=load(ROOT/'content/books/zizhi-tongjian/index.json');c=load(P/'coverage.json');b=load(P/'content-batch.json');a=load(P/'publication.json')
assert d['active_cursor']['next_paragraph']==q[76]['id']
assert c['paragraphs']==[x['id'] for x in q[76:]] and c['next_paragraph']=='zztj-v290-y0952-p001'
assert len(q)==82 and all(x['status']=='published_verified' for x in q[:76]) and all(x['status']=='reviewed' for x in q[76:])
assert a['verified'] and a['batch_sha256']==sha(P/'content-batch.json') and a['public_counts']=={t:len(b[g]) for t,g in groups.items()}
raw=(ROOT/bd['source_file']).read_text().splitlines();assert sha(ROOT/bd['source_file'])==bd['source_sha256']
assert [x['source_line'] for x in q]==list(range(6,88)) and all(x['text']==raw[x['source_line']-1] for x in q)
assert raw[87]=='◎' and raw[88]=='广顺二年壬子，公元九五二年' and raw[89].startswith('春，正月，庚申，夜，孙朗、曹进')
assert all(x['text']==raw[x['source_line']-1] and x['status']=='excluded_non_body_verified' and not x['event_keys'] for x in bd['structural_items'])
y=next(x for x in d['year_coverage'] if x['year']==951);rel=str(P.relative_to(ROOT));assert rel not in y['batches']
paths=y['batches']+[rel];flat=[];checks=[];record_keys={k:set() for k in groups}
for path in paths:
 pp=ROOT/path;bb=load(pp/'content-batch.json');aa=load(pp/'publication.json');cc=load(pp/'coverage.json')
 assert aa['verified'] and aa['batch_sha256']==sha(pp/'content-batch.json')
 assert aa['public_counts']=={t:len(bb[g]) for t,g in groups.items()}
 assert any(s['stage']=='anonymous_readback_verified' for s in aa['stages'])
 for m in load(pp/'sources/manifest.json'):assert sha((pp/'sources'/m['file']).resolve())==m['sha256']
 flat.extend(cc['paragraphs']);checks.append(dict(path=path,batch_key=bb['batch_key'],batch_sha256=aa['batch_sha256'],public_counts=aa['public_counts'],paragraphs=cc['paragraphs'],source_snapshots_verified=True))
 for t,g in groups.items():record_keys[t].update(x['key'] for x in bb[g])
 for pid in cc['paragraphs']:
  row=next(x for x in q if x['id']==pid);assert row['batch_key']==bb['batch_key'] and row['event_keys']
  assert set(row['event_keys'])<={x['key'] for x in bb['events']}
assert flat==[x['id'] for x in q]
# Build pending ledgers for both parts of 952. Nothing here is marked read or published.
next_ledgers=[]
for v,start,stop in [(290,90,126),(291,6,30)]:
 pp=ROOT/f'content/books/zizhi-tongjian/vol-{v}/year-0952';assert not pp.exists();pp.mkdir(parents=True)
 rf=ROOT/f'resources/derived/tongjian/{v}.txt';rr=rf.read_text().splitlines()
 assert (v==290 and rr[88]=='广顺二年壬子，公元九五二年') or (v==291 and rr[4]=='广顺二年壬子，公元九五二年')
 if v==291:assert rr[30]=='◎' and rr[31]=='广顺三年癸丑，公元九五三年'
 rows=[dict(id=f'zztj-v{v}-y0952-p{i:03d}',source_line=line,text=rr[line-1],status='pending',event_keys=[]) for i,line in enumerate(range(start,stop+1),1)]
 assert all(x['text'] and x['text']!='◎' and '公元九五' not in x['text'] for x in rows)
 save(pp/'paragraphs.json',rows)
 structural_lines=[88,89,127,128] if v==290 else [1,2,3,4,5]
 structures=[dict(source_line=line,text=rr[line-1],kind='separator' if rr[line-1] in ('','◎') else 'year_heading' if '公元九五' in rr[line-1] else 'section_heading',status='excluded_non_body_verified',event_keys=[],reason='已核卷年结构或末尾空行，不生成史事') for line in structural_lines]
 boundary=dict(book='资治通鉴',volume=v,year=952,source_file=str(rf.relative_to(ROOT)),source_sha256=sha(rf),body_lines=[start,stop],body_count=len(rows),structural_items=structures,note='按明确年标题及相邻原文行建立待录账本；952年跨卷290、291，正文均未读录发布，不能将本卷当全年。')
 if v==290:boundary['continuation']=dict(volume=291,year=952,next_paragraph='zztj-v291-y0952-p001',first_body_line=6)
 else:boundary['next_year_boundary']=dict(volume=291,separator_line=31,year_heading_line=32,year_heading=rr[31],year=953)
 save(pp/'boundaries.json',boundary)
 (pp/'README.md').write_text(f'# 《资治通鉴》卷{v} · 952年\n\n原{start}—{stop}行{len(rows)}正文均为待录。仅核年界及建立连续账本，没有标为已读、已校或已发布。952年跨卷290、291，须全部正文发布验证后才能记年度完成。\n')
 next_ledgers.append(dict(volume=v,body_count=len(rows),first_paragraph=rows[0]['id'],last_paragraph=rows[-1]['id'],status='pending'))
for row in q[76:]:row['status']='published_verified'
save(YEAR/'paragraphs.json',q)
bd['note']='951年仅在卷290，原6—87行82正文分11批连续发布并匿名读回；88行分隔、89行952年标题不作951史事，90行开始952年实际起事。跨年追述及异说按各批校核说明保留。'
save(YEAR/'boundaries.json',bd)
y.update(status='complete_published_verified',batches=paths,completed_volumes=[290],note='卷290广顺元年82正文分11批连续发布并匿名读回，年度审计核对每批哈希、出处快照、段落覆盖与年界；跨年追述及异说保留。')
assert not any(x['year']==952 for x in d['year_coverage'])
d['year_coverage'].append(dict(year=952,status='pending',volumes=[290,291],batches=[],completed_volumes=[],note='跨卷290、291的62段连续正文账本已建立待录；没有正文标为已读或发布。'))
first=load(ROOT/'content/books/zizhi-tongjian/vol-290/year-0952/paragraphs.json')[0]
d['active_cursor'].update(volume=290,year=952,last_reviewed_paragraph=q[-1]['id'],last_published_paragraph=q[-1]['id'],next_paragraph=first['id'],next_paragraph_opening=first['text'],batch=rel,status='pending')
ix.update(current_year=952,current_volume=290,current_volumes=[290,291],current_batch=rel,next_paragraph=first['id'])
save(ROOT/'content/yearly-progress.json',d);save(ROOT/'content/books/zizhi-tongjian/index.json',ix)
audit=dict(book='资治通鉴',year=951,volumes=[290],verified=True,verified_at=datetime.now(timezone.utc).isoformat(),published_body_count=len(q),body_ids=flat,batches=checks,unique_record_counts={t:len(keys) for t,keys in record_keys.items()},boundary_checks=dict(source_sha256=bd['source_sha256'],body_lines=[6,87],structural_items_verified=5,next_year_separator_line=88,next_year_heading_line=89,next_body_line=90,next_year_ledgers=next_ledgers),scope='年度完成只指951年82段正文按连续顺序录入、逐批校核与发布读回；不代表纸本异文、所有史料争议或全站旧文案已全部解决。完整目标仍到通鉴卷294末959年正文。',next_paragraph=first['id'])
save(YEAR/'completion-audit.json',audit)
(P/'README.md').write_text('# 《资治通鉴》卷290 · 951年第77—82段\n\n原82—87行连续六段已发布并匿名读回。新增33个事件，另复用949年咸师朗降唐事件；9名新人物、155条事实引用。来源、身份疑问、官职异称及追述年月见 coverage.json，发布证据见 publication.json。\n\n951年82段正文已经年度覆盖审计，下一段 `zztj-v290-y0952-p001`。继续后汉后周至卷294末的目标尚未完成。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷290 · 951年\n\n原6—87行82段正文，分11批连续发布并匿名读回。年度审计见 completion-audit.json；每批哈希、出处快照、连续段落与年界均已核对。史料异说、身份疑问与纸本未核事项按各批说明保留。\n\n下一段 `zztj-v290-y0952-p001`。952年跨卷290、291，62段正文账本均为待录。完整目标后汉后周至卷294末959年尚未完成；旧内容集中校改停在935年。\n')
print('951 annual coverage verified',len(q),'batches',len(paths),'next',first['id'],'952 pending bodies',sum(x['body_count'] for x in next_ledgers))
