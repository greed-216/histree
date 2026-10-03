# -*- coding: utf-8 -*-
"""Advance the consecutive 928 prefix only after exact public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:47])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[47:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P.parent/'part-04',P.parent/'part-05',P.parent/'part-06',P.parent/'part-07',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:47]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[40]['id'],rows[47]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[46]['id'],last_published_paragraph=rows[46]['id'],next_paragraph=rows[47]['id'],next_paragraph_opening=rows[47]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首47段已连续发布并逐条匿名回查，余5段待处理；全年未完成。')
for key,n,note in [
 ('dingzhou_waiting_aidi_temple',41,'王宴球疑写沿杜晏球，诸将翻城未成，内溃为建议预期非928已陷；三州税未具州名。哀帝位庙疑字原留，诏曹州立庙非已建成。'),
 ('huoyanwei_death_kinship',43,'主十一卒与旧冬定位，讣到不是卒日，57龄不倒生年；晋忠武公后称，册赠无独年月，旁注929葬敕不强定追赠日。父承训、兄彦珂方向明确。'),
 ('kong_daughter_marriage_party',45,'庚寅实际纳孔女非此前议准，孔女以限定名识别；厚结主语孔循，得之大梁疑字不改；王德妃为明宗妃。促孔归镇非已经到达，新婚罢压缩叙次不强十一月婚触发早二月罢，宋王为后爵回称。'),
 ('wangjianli_titling_iron_question',46,'权知青军州与甲午正式平卢分，主中书侍郎旧左仆射衔异留；仍同平章不写全罢。铁券让三疑字旧三人补，李继麟朱友谦同人，郭朱回忆非在场，族灭非928新死，赵存信为意见非废制。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[47]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=47,volume_total_paragraphs=52,year_completed_paragraphs=47,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[47]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 928年 · part-08\n\n连续第41—47段（原文件73—79行）：22事件、26人物参与、98事实引用；4新增人物、12复用人物；4条新增人物关系；7来源（3新增、4复用），补证《旧五代史》《新五代史》。\n\n覆盖定州围城待变、曹州唐哀帝庙诏、霍彦威卒与悼念追赠、王雅取归州、李从厚纳孔女及孔循求留、王建立暂掌及正式任青州、铁券问答。新增霍承训、霍彦珂、王雅、孔氏（李从厚妃）。\n\n霍彦威是霍承训的父亲、霍彦珂的兄长，孔循是孔氏的父亲、李从厚是孔氏的丈夫，均按A是B的关系方向，不建反向重复。霍追赠年null，57龄不倒生年。庚寅是实际成婚，区别此前议婚许可；厚结主语孔循。郭崇韬、朱友谦只在帝回忆中提及，未写928在场或新死亡。\n\n本批出处与逐字摘录保留原字，展示简体。全文疑字王宴球、位庙、得之大梁、让三人原样保留，异文说明见coverage；底本纸本校核仍待考。旧新异衔与压缩纪时分别引用，不覆盖主书。\n\n结构校验、来源SHA、公开UUID、引用关联和固定GitHub链接已核验；来源快照内其他年代段落未计完成。928年完成47/52段，下一段zztj-v276-y0928-p048；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 928年\n\n原文件33—84行，共52段正文；首47段八批已发布并匿名回查，余5段待连续处理。前后年界已核，卷277从930年开始。\n\n下一段zztj-v276-y0928-p048；连续前缀及证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=47,total=52,next_paragraph=rows[47]['id'],year_complete=False))
