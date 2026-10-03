# -*- coding: utf-8 -*-
"""Advance the consecutive 928 prefix only after exact public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:32])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[32:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P.parent/'part-04',P.parent/'part-05',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:32]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[25]['id'],rows[32]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[31]['id'],last_published_paragraph=rows[31]['id'],next_paragraph=rows[32]['id'],next_paragraph_opening=rows[32]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首32段已连续发布并逐条匿名回查，余20段待处理；全年未完成。')
for key,n,note in [
 ('youzhou_captive_stages',26,'八月甲戌截击与旧壬午奏报分；数百、五十余、旬日七百余与末逃数十属于不同叙法阶段，不精算全军死亡。本次惕隐沿赫邈，武从谏未自动增补他事亲属。'),
 ('lijitao_false_prince',27,'获儿宫畜非亲子，得得别名据旧明称；段佪养父据养之为儿。王都庄宗子及太子帝位均宣称，不建真父子或皇帝位，不提前翌年死。'),
 ('qian_chuanguan_succession',30,'传璹字形待考，不接钱传璙或造潜在重复人；传璟父钱镠明确、与瓘长幼未明。钱传瓘旧元瓘同案，双镇任命非国王继位。'),
 ('hemiao_guard_chronology',31,'主旧闰八月戊申赦五十亲卫斩六百，与新四夷叙在定州陷、秃馁被擒后时序异说并列；契丹直只补称，不提前秃馁死亡。'),
 ('meilao_jisu_identity',32,'梅老季素未分名官，暂保留史载称不拆为两人、不按梅老自动合907袍笏梅老；旧同月贡献无名并看。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[32]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=32,volume_total_paragraphs=52,year_completed_paragraphs=32,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[32]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 928年 · part-06\n\n连续第26—32段（原文件58—64行）：25事件、34人物参与、114事实引用；4新增人物、10复用人物；3条关系（2新增、1复用）；8来源（3新增、5复用），补证《旧五代史》《新五代史》。\n\n覆盖契丹败军幽州截击、李继陶身世与王都利用、王建立请免判三司未准、吴赦、吴越继嗣与双镇授任、契丹献俘处理和贡使。新增武从谏、李继陶、段佪、钱传璟；段佪养父与钱镠父传璟新增，父传瓘复用。\n\n李继陶获儿宫养非庄宗亲生，王都皇子帝位宣称不建立真实父子或皇帝登基；旧交段佪养之为儿是养父证，不提前次年处死。钱传璹原字待考，不连接钱传璙或新增疑似重复实体；钱传瓘元瓘同案同人，双镇军职非国王继位。梅老季素名官连称未解，不拆或合907袍笏梅老。\n\n八月主甲戌截击与旧壬午奏报分，主数百、旧纪五十余、旧传旬日七百余分叙，不用七千减逃数十计算死亡。亲卫五十与其余六百斩分，帝纾患为判断。新四夷将处理合叙定州陷及秃馁被擒后，契丹直补称并保留时序异说，不把秃馁死提前928。\n\n来源原TXT与逐字引用保持底本，展示简体。结构校验、来源SHA、公开UUID、引用关联及固定GitHub地址已核验。纸本异文待考；未将整快照后续未读段落算完成。\n\n928年完成32/52段，下一段zztj-v276-y0928-p033；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 928年\n\n原文件33—84行，共52段正文；首32段六批已发布并匿名回查，余20段待连续处理。前后年界已核，卷277从930年开始。\n\n下一段zztj-v276-y0928-p033；连续前缀及证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=32,total=52,next_paragraph=rows[32]['id'],year_complete=False))
