# -*- coding: utf-8 -*-
"""Advance 933 only through all verified consecutive body paragraphs 1–49."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());END=49
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==57 and [x['source_line'] for x in r]==list(range(36,93))
assert all(x['text']==lines[x['source_line']-1] for x in r) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['status']=='published_verified' for x in r[:END]) and all(x['status']=='pending' and not x['event_keys'] for x in r[END:56])
assert r[56]['kind']=='section_heading' and r[56]['status']=='excluded_non_body_verified' and not r[56]['event_keys']
assert bd['body_paragraphs']==56 and bd['body_source_lines']==[36,91]
proof=[]
for part,start,end in [('part-01',0,10),('part-02',10,20),('part-03',20,30),('part-04',30,39),('part-05',39,42),('part-06',42,49)]:
 p=YEAR/part;b=read(p/'content-batch.json');sha=hashlib.sha256((p/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(p/f);assert a['verified'] and a['batch_sha256']==sha
 assert read(p/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 assert {k for x in r[start:end] for k in x['event_keys']}=={x['key'] for x in b['events']}
 proof.append(dict(batch=str(p.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[42]['id'],r[END]['id']]
pr['active_cursor'].update(volume=278,year=933,last_reviewed_paragraph=r[END-1]['id'],last_published_paragraph=r[END-1]['id'],next_paragraph=r[END]['id'],next_paragraph_opening=r[END]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==933)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278],completed_volumes=[],note='卷278原36—84行连续前49正文段公开核验，全年56正文段，当前49/56，后7待录；第57记录潞王上为下一节标题排除。第四批含昭信遥领、元帅班位、吴遣妓焚器、闽继图案、马政与三司、枢密换任及康王背景、夏州正授、陈劝与慎洮置军；第六批完成第43—49段官属处分、赵谏、明宗崩及宋王即位，下一段宫人案待录，全年及全卷未完成。')
for key,note,n in [('qin_entourage_lists','主八流七列，旧另列李蕘石州；主勒归六人列李瀚江文蔚，旧具六人而无李瀚有李潮，异名单保，不补改主原文。',43),('zhao_yuan_identity_place','宋卷262赵上交传明确本名远字上交后避汉祖讳；主幽州宋涿州范阳并存，EPUB题李濤傳沿另传主，当前引用正文赵传。',44),('jiang_yanhui_glyph','主将延徽与同卷934同军蒋延徽识同一吴攻建州将，规范蒋，原字及后文检索证保；不提前完成934段。',48)]:
 full='933-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))

write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=278,current_year=933,current_volumes=[278],current_batch=rel,next_paragraph=r[END]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=933,completed_paragraphs=END,volume_total_paragraphs=56,year_completed_paragraphs=END,year_total_paragraphs=56,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=r[END]['id'],batches=proof,previous_year_audit=str((YEAR.parent/'year-0932/year-audit.json').relative_to(ROOT))))
bd['note']='原36—91行56个连续正文段；前49已发布公开核验，余7待录；92潞王上为结构标题保留ID，下一段原85行司衣王氏案。全年未完成；93分隔94年标题另列。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 933年\n\n原35行年标题、36—91行56个连续正文段。前49段已公开匿名核验，后7段待录；92行潞王上为下一节标题保留ID而不计正文，下一段zztj-v278-y0933-p050（原85行）。93分隔及94行934标题另列。全年未完成。\n')
print(dict(year=933,completed=END,total=56,next_paragraph=r[END]['id'],year_complete=False))
