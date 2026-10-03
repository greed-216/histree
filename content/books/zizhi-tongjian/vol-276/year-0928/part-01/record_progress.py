# -*- coding: utf-8 -*-
"""Record only the verified continuous prefix; keep the remaining year pending."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:8])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[8:])
b=read(P/'content-batch.json');cov=read(P/'coverage.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 proof=read(P/f);assert proof['verified'] and proof['batch_sha256']==sha
assert cov['paragraphs']==[r['id'] for r in rows[:8]]
assert {k for r in rows[:8] for k in r['event_keys']}=={r['key'] for r in b['events']}
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
prior=read(P.parent.parent/'year-0927/year-audit.json');assert prior['verified'] and prior['year_complete'] and prior['body_paragraphs']==57
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[0]['id'],rows[8]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[7]['id'],last_published_paragraph=rows[7]['id'],next_paragraph=rows[8]['id'],next_paragraph_opening=rows[8]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首8段已连续发布并逐条匿名回查，余44段待处理，全年未完成。')
for key,n,note in [
 ('mao_glyph_and_early_actions',2,'主时报赭袍疑时服，原字与旧服赭黄并列，不靠繁简转换改讹字；征前行为确年未明null；旧后秋案与赐死不提前。'),
 ('yedu_cancel_wu_envoy',5,'将如邺与不果行分计划和停止，军属甫迁确年未明null。主拒使安重诲的抗礼窥觇判断、旧帝以荆吴相连决定并列，不把判断当间谍已证。'),
 ('zhangjun_guard_title',7,'主授左卫上将军与旧辛卯左骁卫上将军及原任衔不同，保留异文和具体来源，未改主或创造未经证明的二次转官。'),
 ('guizhou_action_reports',8,'主二月壬辰攻取归州与旧三月收复奏报/杀败数千、新三月克州不同纪法并列；未强同日，新未独具干支不强癸亥；荆南未几再取未具主将日。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[8]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=8,volume_total_paragraphs=52,year_completed_paragraphs=8,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[8]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)]))
(P/'README.md').write_text('''# 《资治通鉴》卷276 · 928年 · part-01

连续第1—8段（原文件33—40行）已发布：23事件、16人物参与、4父亲关系、94事实引用；3新增人物、9复用人物；7来源（5新增、2复用），补证《旧五代史》《新五代史》。

丁巳封杨琏、杨璘、杨璆及杨玢，前三为杨溥子，玢为宣帝杨隆演子；父亲方向明示，封国不当已赴治所。毛璋赭袍纵酒、剖心杀劝谏者是征前背景，确年null。主时报赭袍疑时服，旧服赭黄及王衍戏独补，保留原字待纸本核；不把王衍作为928现场人物。征金吾旧补辛酉，不提前传后秋案和赐死。契丹平州新补丁巳、旧方陷不强辛酉。日食与旧应亏云不见并列，不扩食分或全国可见。

巡邺计划、军属甫迁未定年、不悦流言和帝未成行分阶段，不造兵变或抵邺；旧停巡令与何泽劝谏获迁分事，不强任命丁丑。吴往来背景未定单年，不重造923灭梁；庚辰使到目的、安拒使判断、旧帝决定及荆吴相连理由、后断交分别引用，未作已证间谍或全贸易永久停止。

张筠到长安被拒、单骑朝洛及授官不同927授西都；主左卫/旧左骁卫、旧原山南西道衔的差异并列，未强造二次转官。归州主二月壬辰行动、旧三月奏报及数千概数、新三月克州并列纪法；未强赋新癸亥。荆南未几再取未具月日与将名。

逐条摘录、源行、SHA、公开UUID、source关联与固定GitHub地址已匿名读回。展示简体，底本原字保留；纸本及异文待核。

928年完成8/52段，下一段zztj-v276-y0928-p009。继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷276 · 928年

原文件33—84行，共52段正文；首8段已发布并匿名回查，余44段待连续处理。前后年界已核，卷277从930年开始。

下一段zztj-v276-y0928-p009；连续前缀和批次证明见progress-audit.json。全年尚未完成。
''')
print(dict(completed=8,total=52,next_paragraph=rows[8]['id'],year_complete=False))
