# -*- coding: utf-8 -*-
"""Advance 933 only through all verified consecutive body paragraphs 1–39."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());END=39
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==57 and [x['source_line'] for x in r]==list(range(36,93))
assert all(x['text']==lines[x['source_line']-1] for x in r) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['status']=='published_verified' for x in r[:END]) and all(x['status']=='pending' and not x['event_keys'] for x in r[END:])
proof=[]
for part,start,end in [('part-01',0,10),('part-02',10,20),('part-03',20,30),('part-04',30,39)]:
 p=YEAR/part;b=read(p/'content-batch.json');sha=hashlib.sha256((p/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(p/f);assert a['verified'] and a['batch_sha256']==sha
 assert read(p/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 assert {k for x in r[start:end] for k in x['event_keys']}=={x['key'] for x in b['events']}
 proof.append(dict(batch=str(p.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[30]['id'],r[END]['id']]
pr['active_cursor'].update(volume=278,year=933,last_reviewed_paragraph=r[END-1]['id'],last_published_paragraph=r[END-1]['id'],next_paragraph=r[END]['id'],next_paragraph_opening=r[END]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==933)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278],completed_volumes=[],note='卷278原36—74行连续前39正文段公开核验，全年57段，当前39/57，后18待录。第四批含昭信遥领、元帅班位、吴遣妓焚器、闽继图案、马政与三司、枢密换任及康王背景、夏州正授、陈劝与慎洮置军；第40段兵变长叙尚待录，全年及全卷未完成。')
for n,key in [(31,'bei_zhaoxin_nominal'),(34,'min_jitu_kinship'),(35,'horse_cost_and_sun_prior_office'),(37,'yichao_jiedushi_glyph'),(38,'fan_inner_outer_advisers'),(39,'shenzhou_rename_gap')]:
 full='933-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=r[n-1]['review']))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=278,current_year=933,current_volumes=[278],current_batch=rel,next_paragraph=r[END]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=933,completed_paragraphs=END,volume_total_paragraphs=57,year_completed_paragraphs=END,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=r[END]['id'],batches=proof,previous_year_audit=str((YEAR.parent/'year-0932/year-audit.json').relative_to(ROOT))))
bd['note']='原36—92行57个连续正文段；前39已发布公开核验，余18待录，下一段原75行明宗疾作及秦王兵变长叙。全年未完成；93分隔94年标题另列。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 933年\n\n原35行年标题、36—92行57个连续正文段。前39段已公开匿名核验，后18段待录，下一段zztj-v278-y0933-p040（原75行）。93分隔及94行934标题另列。全年未完成。\n')
print(dict(year=933,completed=END,total=57,next_paragraph=r[END]['id'],year_complete=False))
