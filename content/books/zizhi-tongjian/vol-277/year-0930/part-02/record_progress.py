# -*- coding: utf-8 -*-
"""Record 19/55 only after two verified consecutive publication batches."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');bd=read(P.parent/'boundaries.json')
assert len(rows)==55 and all(r['status']=='published_verified' for r in rows[:19])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[19:])
raw=ROOT/'resources/derived/tongjian/277.txt';lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(6,61)) and all(r['text']==lines[r['source_line']-1] for r in rows)
assert lines[60]=='◎' and '九三一年' in lines[61]
previous=read(ROOT/'content/books/zizhi-tongjian/vol-276/year-0929/year-audit.json')
assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==36
covered=[];proofs=[]
for part in [P.parent/'part-01',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:19]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[9]['id'],rows[19]['id']]
progress['active_cursor'].update(volume=277,year=930,last_reviewed_paragraph=rows[18]['id'],last_published_paragraph=rows[18]['id'],next_paragraph=rows[19]['id'],next_paragraph_opening=rows[19]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==930)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原6—24行连续19段、2批已发布并匿名回查；全年55段，余36段待录入。61—62行年界结构不计正文。')
for key,n,note in [
 ('cao_establishment_and_investiture',10,'三月庚寅制立与五月十四册命辑引分；新后传从即位概叙不倒赋926，宫中妹称不建姐妹，锦谏追叙null。曹氏沿明宗后，非庄宗母。'),
 ('meng_zhongshuling_time',14,'主四月戊戌、新孟二月南郊加官的时间差并列，主日期保留，纸本待核；不另造同一次授官。'),
 ('yangyanwen_hezhong',15,'主河东/新河中牙内不同字，展示按河中同案，原文不改；新戊戌逐、旧奏本月五日阅马与壬寅奏闻区分。杨奉宣和安否认归说者。'),
 ('yang_execution_and_report',17,'主辛亥拔斩、癸丑献，旧癸丑奏收斩献，报告日非死日；新灭口动机属补书归述。吕沿910少年身份，新职衔补不造当日授职。'),
 ('wangjianli_accusation',19,'摇众是安奏指控不视为证实谋反，主昭义魏州与旧潞州邺都职地称法并列；致仕非处死。')
]:
 full='930-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=930,current_volumes=[277],current_batch=rel,next_paragraph=rows[19]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=277,year=930,completed_paragraphs=19,volume_total_paragraphs=55,year_completed_paragraphs=19,year_total_paragraphs=55,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[19]['id'],batches=proofs))
bd['note']='930年卷277原6—60行55正文段；前19段、2批连续发布并匿名回查，余36段待处理。61—62行分隔及931标题不计正文。';write(P.parent/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 930年 · part-02

连续第10—19段（原15—24行）：44事件、98人物参与、233事实引用；21人物（4新增）、1新增妻子关系、16来源（13新增、3复用），补证《旧五代史》《新五代史》。新增曹氏（李嗣源后）、杨彦温、索自通、药彦稠。

覆盖曹氏立后及王氏宫中往事、高从诲谢绝吴与吴军未克、董璋囚武虔裕、符习致仕、孟夏加衔、河中杨彦温逐李从珂与讨伐、朝廷加罪之争、索任职籍甲仗、王护李与吕琦咨询奏请、帝加尊号及王建立致仕。

三月制立与后续择日册命分；旧曹传辑引五月十四册，与主三月立后不同环节。曹不是庄宗母，王沿已有德妃；妹称不证姐妹。锦谏、真定醉殴等追叙未知年。

主河东牙内与补书河中称法保留，按闭城地点及补书识别杨。杨奉宣、安否认、帝怀疑分别归说者。旧奏本月五日阅马与壬寅奏闻分；命生致与攻拔斩杀、献报分别录，主辛亥杀与癸丑献首不混。新灭口动机明确标补书归述，未伪造已经面讯的口供。

孟主四月戊戌、新二月南郊加中书令纪时差并列，不覆盖主日期。符、王被奏过失为指控，致仕不是处死。吕复用910少年同人，先咨不推全部代笔。李从珂父子话不建生物学父亲边。曹→李嗣源为妻子。

全部来源快照SHA、逐字引句、公开UUID、source关联及固定GitHub链接均回查。展示简体，原文保留繁简字形；电子本异文待纸本校核。

本年完成19/55段；下一段zztj-v277-y0930-p020。继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷277 · 930年

原6—60行55正文段。part-01—02连续第1—19段已发布并匿名回查；余36段待处理，未标全年完成。

第61—62行为年界分隔及931年标题，不计930正文；原文快照保持底本字形。下一段zztj-v277-y0930-p020。
''')
print(dict(completed=19,total=55,next_paragraph=rows[19]['id'],year_complete=False))
