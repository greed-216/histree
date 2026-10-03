# -*- coding: utf-8 -*-
"""Advance only after both consecutive 931 batches have public proof."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==50 and all(x['status']=='published_verified' for x in rows[:20]);assert all(x['status']=='pending' and not x['event_keys'] for x in rows[20:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(63,113));assert all(x['text']==lines[x['source_line']-1] for x in rows)
assert lines[61]=='长兴二年辛卯，公元九三一年' and lines[112]=='◎' and lines[113]=='长兴三年壬辰，公元九三二年'
covered=[];proofs=[]
for part in [YEAR/'part-01',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(part/f);assert d['verified'] and d['batch_sha256']==sha
 assert {k for x in rows if x['id'] in c['paragraphs'] for k in x['event_keys']}=={x['key'] for x in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[x['id'] for x in rows[:20]]
previous=read(YEAR.parent/'year-0930/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==55
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[10]['id'],rows[20]['id']]
progress['active_cursor'].update(volume=277,year=931,last_reviewed_paragraph=rows[19]['id'],last_published_paragraph=rows[19]['id'],next_paragraph=rows[20]['id'],next_paragraph_opening=rows[20]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==931)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原63—82行连续20段、2批已公开匿名回查；全年50段，余30段待处理。113—114行年界不计正文。')
for n,key in [(13,'song_office_succession'),(15,'dongdan_names_and_captive_tiyin'),(19,'qian_restoration_sequence')]:
 full='931-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=931,current_volumes=[277],current_batch=rel,next_paragraph=rows[20]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=931,completed_paragraphs=20,volume_total_paragraphs=50,year_completed_paragraphs=20,year_total_paragraphs=50,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[20]['id'],batches=proofs))
bd['note']='931年原63—112行50正文段，前20段两批已公开匿名核验，余30段待录；113—114行年界不计正文。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷277 · 931年 · part-02

连续第11—20段，原73—82行：26事件、42人物参与、127事实引用；20人物（仅安崇阮新增）、1父亲关系复用，8来源（6新增、2复用）。补证旧、新五代史及辽史。

安重诲出镇、赵凤申辩与帝不悦、两川撤军留戍、李仁罕忠万云安夔进军、宋齐丘入山劝召还朝致仕及寺更名、突欲与惕隐赐名、李从珂复见授左卫、孔循卒、钱镠复爵及张篯谕旨、李愚拜相，按连续动作分录。

安出镇不等死亡，赵不叛受谗为赵观点，帝朋党为帝判断。五千利州和三千果阆各为共留兵，不按各将各州重复计数。宋欲相为意图，请归葬父不直接证明葬已完成；主本次右仆射致仕与新吴大和三年皆平章事并列，不压成同日实拜相。景通沿李璟，父李昪关系复用。

突欲沿耶律倍，东丹慕华同主体，辽后李赞华未提前。主瑞慎、旧瑞镇、辽瑞慎字差留；惕隐为官名，按928救定州被俘赫邈及旧先定州擒将范围识别，狄怀惠赐名以引用连同主体，不合所有惕隐。未扩造旧纪快照内主未名诸俘将。安崇阮旧929黔转夔身份佐核，不混安重诲；杨汉宾沿930黔弃到忠，逃归朝廷非降孟。

从珂为养子不建生父边。横海/沧州军治所称法同孔卒。主三月钱复爵、新安死后复爵时序差保留；矫制为本次谕旨归责，不重写全部旧削爵史。张篯沿926张籛，非兄张筠。李愚旧补集贤殿大学士同任不另造。

展示简体，TXT与引句保留原字。SHA、公开UUID、固定来源及引用关联匿名核验通过。931年连续完成20/50段，下一段zztj-v277-y0931-p021，继续至936年后唐灭亡。
''')
(YEAR/'README.md').write_text('''# 《资治通鉴》卷277 · 931年

原63—112行50正文段。part-01—02连续第1—20段已公开匿名核验，余30段待录，全年未完成。

113—114行分隔及932标题不计正文。下一段zztj-v277-y0931-p021。
''')
print(dict(year=931,completed=20,total=50,next_paragraph=rows[20]['id'],year_complete=False))
