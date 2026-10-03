# -*- coding: utf-8 -*-
"""Advance the consecutive 928 prefix only after exact public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:10])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[10:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
proofs=[];covered=[]
for part in [P.parent/'part-01',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:10]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[8]['id'],rows[10]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[9]['id'],last_published_paragraph=rows[9]['id'],next_paragraph=rows[10]['id'],next_paragraph_opening=rows[10]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首10段已连续发布并逐条匿名回查，余42段待处理；全年未完成。')
for key,n,note in [
 ('kong_marriage_approval',9,'孔循出镇前婚议追叙null；获准非完婚，新合妻与出镇概述不提前十一月婚礼，不建未完成夫妻边；王德妃限定李嗣源妃区别吴王氏。'),
 ('hua_retrospective_hypothetical',9,'华入朝留阙与岁馀后重镇议、数月不出均未明确年null，不倒算；帝安对话不是华已任枢密或安已免官，不提前华州实际任命。'),
 ('an_wang_accusations_actual_jobs',9,'安王互告是所奏，异志和安张结婚威福不直接作已证叛乱或造姻亲；旧传夹通鉴注非独立确证。辛亥拟调安张、王代枢密未兑现，后王癸亥实际相财官区别；明日辞归非已归镇。'),
 ('retirement_salt_revenue',10,'郑四章与挽留、新郑庄、旧食邑分别据源；两川屡争和董诱贩前背景未日null，孟设三场当前条928未日；岁得七万是制度后年度概述null非928固定实收，商旅不复不是全国贸易终止。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[10]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=10,volume_total_paragraphs=52,year_completed_paragraphs=10,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[10]['id'],batches=proofs))
(P/'README.md').write_text('''# 《资治通鉴》卷276 · 928年 · part-02

连续第9—10段（原文件41—42行）已发布：36事件、61人物参与、163事实引用；1新增人物王德妃〔李嗣源妃〕、12复用人物；10来源（6新增、4复用），补证《旧五代史》《新五代史》。

第9段包含多阶段追叙及三月史事。孔循受亲信、帝欲安女婚、孔劝安辞、匿名提醒、孔结王德妃、王请从厚、帝许分别记录，未明年保留null。婚议获准不提前后十一月纳妃，不造已婚边；新孔传妻与出镇概述保留叙法。王德妃限定李嗣源妃，区别吴太妃王氏。乙未孔忠武同平章兼东都为实际出镇，旧许州、新罢枢密同事职称不推所有官爵削尽。

华温琪入朝留阙、左骁月赐及岁馀后重镇议、安无阙、屡言、枢密可代对话、帝答与数月不出均未明确年null。未倒算入朝年或把对话当实际换枢密；旧怕权臣几致成疾不作现代诊断，后华州任命不提前。安王互告、召入朝与面奏分阶段，异志专权及安张结婚威福为所奏，不直接建反叛事实或姻亲边；旧王传虑陷补动机，其夹注引通鉴不算独立确证，后王都叛段不提前标已读。

辛亥拟调安张、王代枢密，安陈辩、帝告朱、朱谏、帝慰抚及明日王请归分阶段；无实际换枢密，天下无事仅安话。郑请求、四章与明宗挽留、己未左仆射致仕、旧开府食邑及新郑庄补证，后卒不提前。癸亥王右仆射中书侍郎同平章判三司是实际相财职，旧细判盐铁户部度支与集贤、新简衔并列，不称已新设三司使。

第10段两川屡争盐利、董诱商旅贩盐是未明年前背景；孟汉州设三场重征按当前928条，未具日、场名税率不编。岁得七万缗与商旅停止前往东川为制度后概述，年null，不作928全年实收或全国贸易终止。

逐字摘录、源行、SHA、公开UUID、source关联与固定GitHub链接均匿名读回。主书第9段跨原始检索分段，各块保留独立原文与定位；快照包含尚未处理段落，不将整快照记完成。展示简体、摘录保留底本原字，纸本及异文待核。

928年完成10/52段，下一段zztj-v276-y0928-p011；继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷276 · 928年

原文件33—84行，共52段正文；首10段两批已发布并匿名回查，余42段待连续处理。前后年界已核，卷277从930年开始。

下一段zztj-v276-y0928-p011；连续前缀和批次证明见progress-audit.json。全年尚未完成。
''')
print(dict(completed=10,total=52,next_paragraph=rows[10]['id'],year_complete=False))
