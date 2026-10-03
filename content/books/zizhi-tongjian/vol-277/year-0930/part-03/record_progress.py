# -*- coding: utf-8 -*-
"""Record 29/55 only after two verified consecutive publication batches."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');bd=read(P.parent/'boundaries.json')
assert len(rows)==55 and all(r['status']=='published_verified' for r in rows[:29])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[29:])
raw=ROOT/'resources/derived/tongjian/277.txt';lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(6,61)) and all(r['text']==lines[r['source_line']-1] for r in rows)
assert lines[60]=='◎' and '九三一年' in lines[61]
previous=read(ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/year-audit.json')
assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==36
covered=[];proofs=[]
for part in [P.parent/'part-01',P.parent/'part-02',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:29]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[19]['id'],rows[29]['id']]
progress['active_cursor'].update(volume=277,year=930,last_reviewed_paragraph=rows[28]['id'],last_published_paragraph=rows[28]['id'],next_paragraph=rows[29]['id'],next_paragraph_opening=rows[29]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==930)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原6—34行连续29段、3批已发布并匿名回查；全年55段，余26段待录入。61—62行年界结构不计正文。')
for key,n,note in [
 ('yongding_reused_component',20,'前批新董守寨增关合记事件复用，此主句只证永定关组成动作五月，不把李扼寨全定五月，公开主年未知保留。'),
 ('solar_eclipse_glyph',22,'原癸已朔的已疑地支巳，底本不改，未用现代历算代替史证或猜公历。'),
 ('an_informers_dates',25,'主乙未斩边、壬寅族李张；旧乙未三人并族、新连叙族，有日和范围差并列。告言不等安已反，边不混杨彦温。'),
 ('zhang_sansishi_office',26,'主工部旧兵部官名异文，正式三司使使额概括不等三司组织才生或此前文本绝无三司使字。'),
 ('haizhou_numbers_kinship',27,'主众五千、旧兵士家口五千，非五千纯战兵；己亥行杀与戊申奏闻分。王绾沿899吴将身份，季父王舆→传拯叔父。王岩吴将消歧非闽王。')
]:
 full='930-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=930,current_volumes=[277],current_batch=rel,next_paragraph=rows[29]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=277,year=930,completed_paragraphs=29,volume_total_paragraphs=55,year_completed_paragraphs=29,year_total_paragraphs=55,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[29]['id'],batches=proofs))
bd['note']='930年卷277原6—60行55正文段；前29段、3批连续发布并匿名回查，余26段待处理。61—62行分隔及931标题不计正文。';write(P.parent/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 930年 · part-03

连续第20—29段（原25—34行）：35事件（34新增、1复用）、53人物参与（52新增、1复用）、157新增事实引用；19人物（8新增）、2新增关系、6来源（5新增、1复用），补证《旧五代史》《新五代史》。

新增李行德、张俭、边彦温、安从进、王传拯、陈宣、王岩（吴海州将）、王舆（吴光州刺史）。徐知诰沿李昪既有主体，王绾沿899年同吴将身份。父亲王绾→王传拯，叔父王舆→王传拯；季父不当祖父。

覆盖两川部署、盐监划拨、日食、地方任官诏、安重诲被诬案、张延朗三司使、吴海州兵变及秦宋王封命。永定关复用前批合记事件，此主句只补增关的五月语境，守七砦动作未独纪时，不把原事件全部强赋五月。

六月癸已朔疑字保留，未换公历。主乙未斩边、壬寅族李张，旧乙未三人并族、新连叙三族，保留不同纪时和刑罚范围；告言不当安已反。主张延朗工部、旧兵部不同原职衔并列，三司使使额始于此次不当此前毫无三司组织。

海州己亥杀陈焚掠与旧戊申兖州奏闻分；旧明确五千含兵与家口，不当纯战兵。王以为陈毁是怀疑；徐许代是承诺非已经任职，王舆求罢是请求，执使非抓王本人，免妻子是免妻与子女之罪责。吴内部细节主独证，旧补杀焚与来奔。

全部来源SHA、逐字引句、公开UUID、source关联及固定GitHub链接均回查。展示简体，原文保留繁简字形，电子本异文待纸本校核。

本年完成29/55段；下一段zztj-v277-y0930-p030。继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷277 · 930年

原6—60行55正文段。part-01—03连续第1—29段已发布并匿名回查；余26段待处理，未标全年完成。

第61—62行为年界分隔及931年标题，不计930正文；原文快照保持底本字形。下一段zztj-v277-y0930-p030。
''')
print(dict(completed=29,total=55,next_paragraph=rows[29]['id'],year_complete=False))
