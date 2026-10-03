# -*- coding: utf-8 -*-
"""Advance to volume 275 only after the entire volume-274 year slice is verified."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
ledger=read(P.parent/'paragraphs.json');other=read(ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/paragraphs.json')
assert len(ledger)==43 and len(other)==67
assert all(r['status']=='published_verified' for r in ledger)
assert all(r['status']=='pending' for r in other)
raw=ROOT/'resources/derived/tongjian/274.txt';lines=raw.read_text().splitlines();bounds=read(P.parent/'boundaries.json')
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bounds['source_sha256']
assert [r['source_line'] for r in ledger]==list(range(38,81))
assert all(r['text']==lines[r['source_line']-1] for r in ledger)
assert all(lines[r['source_line']-1]==r['text'] for r in bounds['excluded_non_body'])
assert other[0]['source_line']==bounds['next_body_source_line']==6 and bounds['next_volume']==275
next_raw=ROOT/'resources/derived/tongjian/275.txt';next_lines=next_raw.read_text().splitlines()
next_bounds=read(ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/boundaries.json')
assert hashlib.sha256(next_raw.read_bytes()).hexdigest()==next_bounds['source_sha256']
assert [r['source_line'] for r in other]==list(range(6,73))
assert all(r['text']==next_lines[r['source_line']-1] for r in other)
assert '九二六年' in next_lines[next_bounds['year_header_line']-1]
parts=[];covered=[];totals={'events':0,'claims':0}
for part in sorted(P.parent.glob('part-*')):
 data=read(part/'content-batch.json');pub=read(part/'publication.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 assert pub['verified'] and pub['batch_sha256']==sha
 proof=read(part/'readback-audit.json');assert proof['verified'] and proof['batch_sha256']==sha
 ids=read(part/'coverage.json')['paragraphs'];covered+=ids
 assert {k for r in ledger if r['id'] in ids for k in r['event_keys']}=={r['key'] for r in data['events']}
 parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert len(parts)==5 and covered==[r['id'] for r in ledger]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (ledger[40]['id'],other[0]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=ledger[-1]['id'],last_published_paragraph=ledger[-1]['id'],next_paragraph=other[0]['id'],next_paragraph_opening=other[0]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段五批连续发布并匿名回查、卷年连续覆盖审计通过。卷275全67段待处理，全年未完成。')
for key,n,note in [
 ('congjing-death',41,'主已遣使道遇杀与新家人欲遣、行钦以不可而杀的执行叙法不同，保留一死亡主体及独立引证待核。'),
 ('closing-text-glyphs',43,'待中疑侍中、辛已疑巳、滑洲疑州、共奉疑奏保留底本；行营马步使陶后私用字未获同职同事证据，暂不并许州留后陶玘、不建执行者主体。'),
 ('liqiong-disambiguation',43,'主攻封丘门李琼据旧94同事明确字隐光，独立主体李琼（隐光），不并908卒楚将。'),
 ('closing-names-and-numbers',43,'潘环/潘瑰、张唐/张塘据同地职事合同人但字形待核；姚三千/旧两纪八百、万余人/骑及出京遣骑至荥泽各纪日独立保留。')]:
 full='926-v274-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=274,year=926,completed_paragraphs=43,volume_total_paragraphs=43,year_completed_paragraphs=43,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,structural_lines_verified=True,volume_complete=True,year_complete=False,next_paragraph=other[0]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=other[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
(P/'README.md').write_text('''# 《资治通鉴》卷274 · 926年 · part-05

连续第41—43段（原文件78—80行）已发布：26事件、53参与、148引用；新增6个人物，无新增人物关系。

补证来自《旧五代史》卷34、35、51、94及《新五代史》卷8、14、15。李从璟遇害与前批获释分开；钱镠患病监国、问疾、拟袭停止与返塘逐动作录。白皋取供绢、渡师、会兵、取汴、姚彦温叛归与夺兵、王村奔梁、庄宗旋师返洛、张容哥获救后自尽均沿主书次序处理。丙戌翌晨东行仍是预令，未提前录下卷庄宗遇害。

取汴的李琼据旧94字隐光、同封丘门同石敬瑭之事，另建李琼（隐光），与908年去世楚将分人。西方为复姓，邺用简体。潘环/潘瑰、张唐/张塘依同职同地同动作辨同人，字形待核；姚三千/旧八百、万余人/骑、两纪出京遣骑到荥泽纪日保留异说。待中、辛已、滑洲、共奉疑字原文不改；陶后私用缺字暂不建主体、不强并陶玘。

公开ID、引用出处ID、固定URL和原文哈希已逐条匿名核对，见publication.json、readback-audit.json。卷274的926年43段五批全部完成，全年仍有卷275的67段待录。下一段zztj-v275-y0926-p001。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷274 · 926年

本卷43正文段（原文件38—80行）五批全部发布并匿名读回；连续覆盖、原文源行、哈希、结构行及逐批发布证明见progress-audit.json。

926年还包含卷275的67段，全年110段目前完成43段，全年未完成。下一段zztj-v275-y0926-p001。
''')
print(dict(completed=43,total=110,next_paragraph=other[0]['id'],volume_complete=True,year_complete=False))
