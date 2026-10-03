# -*- coding: utf-8 -*-
"""Advance only after three consecutive 931 batches have public proof."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==50 and all(x['status']=='published_verified' for x in rows[:30]);assert all(x['status']=='pending' and not x['event_keys'] for x in rows[30:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(63,113));assert all(x['text']==lines[x['source_line']-1] for x in rows)
assert lines[61]=='长兴二年辛卯，公元九三一年' and lines[112]=='◎' and lines[113]=='长兴三年壬辰，公元九三二年'
covered=[];proofs=[]
for part in [YEAR/'part-01',YEAR/'part-02',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(part/f);assert d['verified'] and d['batch_sha256']==sha
 assert {k for x in rows if x['id'] in c['paragraphs'] for k in x['event_keys']}=={x['key'] for x in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[x['id'] for x in rows[:30]]
previous=read(YEAR.parent/'year-0930/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==55
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[20]['id'],rows[30]['id']]
progress['active_cursor'].update(volume=277,year=931,last_reviewed_paragraph=rows[29]['id'],last_published_paragraph=rows[29]['id'],next_paragraph=rows[30]['id'],next_paragraph_opening=rows[30]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==931)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原63—92行连续30段、3批已公开匿名回查；全年50段，余20段待处理。113—114行年界不计正文。')
for n,key in [(22,'min_gate_and_kinship'),(28,'court_finance_text')]:
 full='931-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=931,current_volumes=[277],current_batch=rel,next_paragraph=rows[30]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=931,completed_paragraphs=30,volume_total_paragraphs=50,year_completed_paragraphs=30,year_total_paragraphs=50,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[30]['id'],batches=proofs))
bd['note']='931年原63—112行50正文段，前30段三批已公开匿名核验，余20段待录；113—114行年界不计正文。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷277 · 931年 · part-03\n\n连续第21—30段，原83—92行：18人物（4新增）、30事件、47人物参与、5有向亲属关系、148事实引用，6来源（5新增、1复用）。补证《旧五代史》《新五代史》。\n\n王妃进淑妃；闽建州攻福州、王仁达假降伏杀王继雄、王延禀兵败被擒、招抚使被杀及二子奔吴越、五月斩王延禀复原姓名、王延政赴建州；赵延寿、石敬瑭、朱弘昭及孟汉琼孟鹄官职迁转；酒曲税价政令；内廷财用及赵廷隐请兵未许，依连续原文分动作。\n\n主东门、新南门异文并列；新连叙遂杀不抹去主四月俘、五月斩的时序。王继升与新继昇由同留守、同父、同奔识别；王延禀与复原姓名周彦琛同一主体。仁达从子保留原词，不推未名生父或伯叔长幼。父亲、兄长箭头遵循A是B的关系；不从次子猜继雄长子。\n\n城中官造减半与乡村许私造分，罢麹钱不是全田税。安重诲限制宫索属无年追叙；孟汉琼原赵王奴作为身份事实，不建永久主奴边。原重悔、亦无语文书留字，展示说明归并身份与未有文书，不臆改底本。孟鹄传后期年发疾未提前；赵廷隐请攻兴元秦凤不等占领。\n\n展示简体，来源快照与引句保留原字。发布后以匿名身份核验UUID、出处关联、固定Git来源及快照SHA。931年连续完成30/50段，下一段zztj-v277-y0931-p031，全年仍未完成。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷277 · 931年\n\n原63—112行50正文段。part-01—03连续第1—30段已公开匿名核验，余20段待录，全年未完成。\n\n113—114行分隔及932标题不计正文。下一段zztj-v277-y0931-p031。\n')
print(dict(year=931,completed=30,total=50,next_paragraph=rows[30]['id'],year_complete=False))
