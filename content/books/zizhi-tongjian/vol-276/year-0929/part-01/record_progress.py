# -*- coding: utf-8 -*-
"""Advance only the exact publicly verified 929 continuous prefix."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==36
assert all(r['status']=='published_verified' for r in rows[:8])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[8:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(87,123))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
prev=read(P.parent.parent/'year-0928/year-audit.json');assert prev['verified'] and prev['year_complete'] and prev['body_paragraphs']==52
b=read(P/'content-batch.json');c=read(P/'coverage.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 proof=read(P/f);assert proof['verified'] and proof['batch_sha256']==sha
assert c['paragraphs']==[r['id'] for r in rows[:8]]
assert {k for r in rows[:8] for k in r['event_keys']}=={r['key'] for r in b['events']}
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[0]['id'],rows[8]['id']]
progress['active_cursor'].update(volume=276,year=929,last_reviewed_paragraph=rows[7]['id'],last_published_paragraph=rows[7]['id'],next_paragraph=rows[8]['id'],next_paragraph_opening=rows[8]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==929)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='929年卷276共36正文段，首8段已连续发布并逐条匿名回查，余28段待处理；全年未完成。')
for key,n,note in [
 ('dingzhou_dates_family_fates',2,'主二月癸丑、新癸卯、旧乙巳报三日、旧王传三月不同纪时并列。王举族自焚与旧妻孥俱烬不推全家无幸存；旧帝纪四子一弟在辛酉被刑。秃主斩旧磔并列，二千与二千余概数不精算，王宴球沿杜晏球不加疑字别名。'),
 ('cuixie_posthumous_rank',5,'旧帝纪赠右仆射、旧传左仆射异衔并列；中风古病名不现代诊断，确卒日主新丁卯。赵卒未独干支，不能据挨辛酉而强同日。'),
 ('wangyanqiu_siege_soldiers',7,'围城未戮一士是未刑杀，不能等无战亡；主始攻至克城未独始年日，期间null，旧其年冬平贼不同不改主。私财犒军不是国家总军费，帝美功不补物赏。'),
 ('licongcan_kinship_execution',8,'主皇子旧帝之诸子、新明宗侄不同说法保留，不建确定生父或叔伯边。东巡授皇城、会节宴、安奏均前事年null，三月丙戌赐死确记；旧贬房司户不等已赴任，后恢复官赠太保不提前。横山邵扰不强同日或推现代族属。')
]:
 full='929-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=929,current_volumes=[276],current_batch=rel,next_paragraph=rows[8]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=929,completed_paragraphs=8,volume_total_paragraphs=36,year_completed_paragraphs=8,year_total_paragraphs=36,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[8]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)]))
(P/'README.md').write_text('''# 《资治通鉴》卷276 · 929年 · part-01

连续第1—8段（原文件87—94行）：27事件、32人物参与、118事实引用；2新增人物、10复用人物；10来源（8新增、2复用），补证《旧五代史》《新五代史》。

覆盖冯赟入宣徽及劝辅从荣、定州陷落与王都自焚、秃馁俘送处刑、王晏球与赵德钧军衔，赵敬怡及崔协卒、帝梁郑洛行程、围城犒士和王晏球入朝、李从璨案及横山蛮扰邵州。新增马让能、李从璨，不新增亲属边。

定州日期主癸丑、新癸卯、旧帝纪乙巳报本月三日、旧王传三月分存。王举族自焚不能扩为全家无幸存，旧纪尚载四子一弟处刑。秃馁主斩与旧磔并列，俘数二千与二千余照录。王宴球疑写沿杜晏球同人；天平与郓州同军治州，赵只加侍中不误移天平。

赵敬怡卒日未独具，旧赠太傅身后；崔协丁卯须水卒，古病名中风照录不现代诊断，旧仆射左右异衔并列。甲子发梁、旧丙寅郑州、庚午洛阳分阶段。王未戮一卒指未刑杀，不等无战亡；私财犒士不是国家军粮总额，旧其年冬平贼不同纪时注明；三月辛巳入朝、褒功、谢馈运分。

李从璨主皇子旧诸子、新侄说并列，暂不建确定父子或叔伯边。东巡授皇城、会节宴和安奏为前事，确年null；三月丙戌死确记。戏登御榻不等已称帝或举兵；旧贬房州司户不推到任，新后来复官赠太保不提前录。横山邵州案无实名不猜，月内确日未具。

逐字摘录、来源SHA、公开UUID、source关联及固定GitHub链接已核验；展示简体，原文保留底本，纸本异文待考。快照中后续四月和未来年代未计已处理。

929年完成8/36段，下一段zztj-v276-y0929-p009；继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷276 · 929年

原文件87—122行，共36段正文；首8段已连续发布并匿名回查，余28段待处理。年界和卷末已核，下一卷277从930年开始。

下一段zztj-v276-y0929-p009；连续覆盖和验证证明见progress-audit.json。全年尚未完成。
''')
print(dict(completed=8,total=36,next_paragraph=rows[8]['id'],year_complete=False))
