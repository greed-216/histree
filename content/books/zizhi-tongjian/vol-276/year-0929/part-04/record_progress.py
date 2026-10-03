# -*- coding: utf-8 -*-
"""Advance only the exact publicly verified 929 continuous prefix."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==36
assert all(r['status']=='published_verified' for r in rows[:27])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[27:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(87,123))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
prev=read(P.parent.parent/'year-0928/year-audit.json');assert prev['verified'] and prev['year_complete'] and prev['body_paragraphs']==52
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:27]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[22]['id'],rows[27]['id']]
progress['active_cursor'].update(volume=276,year=929,last_reviewed_paragraph=rows[26]['id'],last_published_paragraph=rows[26]['id'],next_paragraph=rows[27]['id'],next_paragraph_opening=rows[27]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==929)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='929年卷276共36正文段，首27段已连续发布并逐条匿名回查，余9段待处理；全年未完成。')
for key,n,note in [
 ('gaoyu_allegations_and_attribution',23,'高季兴已死928，不赋929离间。初追叙年null，谋主任用及923入贡复用；马殷拒请诛，希声矫命杀郁与榜告诬叛分。旧希范传与主新希声归责不同，保留异说；愿兄弟对象未直具不建结义，杨妻族不猜亲缘。'),
 ('fengdao_farming_poem_variant',24,'井陉出使为旧事例证，不新录929出使。旧他日不强同场；聂为被引作者非在场，主新谷/旧秋谷非繁简，原摘录保留；四人疑字待核。'),
 ('fuzhou_and_zizhou_tax_official',26,'鄜兵赢老疑羸留原，展示老弱不猜人数。资州税官是孟容弟非孟知祥弟，虽吾弟为假设，抵死不猜已执行；冯璩王处回请免不等批准。'),
 ('wuzhaoyu_hanmei_and_qianliu',27,'称臣私告为韩指控，新返谮旧后使辩保留；旧刘玫/主新韩玫名异不强合别名或另造确定告发者。安奏与新癸巳杀分，旧赐尽新坐死方式差不定斩刑。钱太师仍在，拘治命令非全已拘，旧乙未后令不强同日；表冤非已复爵。')
]:
 full='929-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=929,current_volumes=[276],current_batch=rel,next_paragraph=rows[27]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=929,completed_paragraphs=27,volume_total_paragraphs=36,year_completed_paragraphs=27,year_total_paragraphs=36,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[27]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 929年 · part-04\n\n连续第23—27段（原109—113行）：34事件（2复用）、63人物参与、167事实引用；20人物（7新增）、1复用父亲关系、9来源（6新增）。补证《旧五代史》《新五代史》。\n\n覆盖高郁案、冯道谈农事、鄜州戍东川兵归道、资州税官论死及吴越使者案。新增杨昭遂、聂夷中、孟容、冯璩、王处回、乌昭遇、韩玫。\n\n高郁案按初追叙，确年未载用null，高季兴已卒928。原任谋主及923入贡复用稳定事件。流言、指控、请诛、拒绝、罢兵柄、矫命杀人与榜告诬叛分；不将马殷记为杀人发令者。新楚世家归希声，旧希范传归希范，保留异说，未另造第二次死亡。雾与冤死为马殷解释，不当超自然事实。\n\n冯道井陉出使为旧事例证；两问不强同日。聂夷中为被引作者，未记在场。主新谷/旧秋谷为词异文，原摘录保持。鄜州兵选赢老疑羸，展示老弱，未具人数。税官是孟容之弟，非孟知祥之弟，虽吾弟是举例；抵死与实际执行分，不猜姓名、金额。\n\n乌昭遇称臣、拜舞、私告都是韩玫指控。新返谮、旧后使辩其被诬并列；旧刘玫/主新韩玫待校，不自动合实名别名或另建确定告发者。安奏与新九月癸巳记杀分，旧赐尽与新坐死御史狱方式并存。钱镠太师致仕仍有太师，削爵不等失吴越实控，拘治是命令；旧乙未诏可能后令。钱诸子表冤不省，不前移以后复爵。\n\n公开UUID、来源SHA、逐字摘录、source关联及固定GitHub链接已回查。展示简体，原文保留底本，纸本异文待核。\n\n929年完成27/36段，下一段zztj-v276-y0929-p028；全年未完成，继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 929年\n\n原文件87—122行，共36段正文；首27段四批已连续发布并匿名回查，余9段待处理。年界和卷末已核，下一卷277从930年开始。\n\n下一段zztj-v276-y0929-p028；连续覆盖和验证证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=27,total=36,next_paragraph=rows[27]['id'],year_complete=False))
