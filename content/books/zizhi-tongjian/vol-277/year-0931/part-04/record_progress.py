# -*- coding: utf-8 -*-
"""Advance only after four consecutive 931 batches have public proof."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==50 and all(x['status']=='published_verified' for x in rows[:40]);assert all(x['status']=='pending' and not x['event_keys'] for x in rows[40:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(63,113));assert all(x['text']==lines[x['source_line']-1] for x in rows)
assert lines[61]=='长兴二年辛卯，公元九三一年' and lines[112]=='◎' and lines[113]=='长兴三年壬辰，公元九三二年'
covered=[];proofs=[]
for part in [YEAR/'part-01',YEAR/'part-02',YEAR/'part-03',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(part/f);assert d['verified'] and d['batch_sha256']==sha
 assert {k for x in rows if x['id'] in c['paragraphs'] for k in x['event_keys']}=={x['key'] for x in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[x['id'] for x in rows[:40]]
previous=read(YEAR.parent/'year-0930/year-audit.json');assert previous['verified'] and previous['year_complete'] and previous['body_paragraphs']==55
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[30]['id'],rows[40]['id']]
progress['active_cursor'].update(volume=277,year=931,last_reviewed_paragraph=rows[39]['id'],last_published_paragraph=rows[39]['id'],next_paragraph=rows[40]['id'],next_paragraph_opening=rows[40]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==931)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='卷277原63—102行连续40段、4批已公开匿名回查；全年50段，余10段待处理。113—114行年界不计正文。')
for n,key in [(31,'an_execution_and_accusations'),(35,'baohuang_chronology'),(36,'dongfan_name_glyph')]:
 full='931-v277-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=931,current_volumes=[277],current_batch=rel,next_paragraph=rows[40]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=277,year=931,completed_paragraphs=40,volume_total_paragraphs=50,year_completed_paragraphs=40,year_total_paragraphs=50,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[40]['id'],batches=proofs))
bd['note']='931年原63—112行50正文段，前40段四批已公开匿名核验，余10段待录；113—114行年界不计正文。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷277 · 931年 · part-04\n\n连续第31—40段，原93—102行：27人物（9新增）、32事件（31新增、1复用）、67人物参与、4有向亲属关系、180事实引用，8来源（7新增、1复用）。补证《旧五代史》《新五代史》。\n\n安重诲请致仕、二子逃奔、李从璋移镇、药彦稠派兵、父拘送二子、陕州系狱、翟察条件诛令、围宅拜礼及夫妻挝杀、奏至列罪和二子被诛分动作。己亥为奏至诏日，不直接赋给夫妻遇害时刻。旧丁酉奏已拘送补相对时序，主先杀后奏与旧赐死诏叙法并列。主又诬为史书对指控的评判，引用显示谁提出什么，未造确证安谋反。新其余子孙免不扩大为灭族。\n\n安崇赞／崇讚／崇贊及翟光邺／翟光鄴／翟光業按同案身份核对；妻张氏以配偶消歧。苏愿刘澄奉遣不同后来抵达。从珂西都留守、诸道均税命令、闽建宝皇宫任宫主、耶律倍更赐李赞华、徐知谏卒及徐知询继镇南、范延光加相、五坊放鹰隼禁进、李进唐拔通州及王延政刺史按编年主段顺录。\n\n宝皇宫新世家后连叙的时间不强改主年；后逊位称帝预言待主段。东凡慕华疑字由旧同日东丹同赐名核，原字保留。徐知谏参与召徐知询为追叙，补入929年已有入朝事件与参与边，未新造931再召。徐知询称弟直接支持兄长方向。李嗣源回忆随武皇狩猎只作为当前解释引语，李克用为被提及者，未造931同行事件。通州不武断套今日北京，未核坐标。\n\n展示简体，TXT与摘录保留底本字形。发布后匿名核验UUID、事实出处关联、固定Git URL与快照SHA。931年连续完成40/50段，下一段zztj-v277-y0931-p041，全年未完成；目标继续到936年后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷277 · 931年\n\n原63—112行50正文段。part-01—04连续第1—40段已公开匿名核验，余10段待录，全年未完成。\n\n113—114行分隔及932标题不计正文。下一段zztj-v277-y0931-p041。\n')
print(dict(year=931,completed=40,total=50,next_paragraph=rows[40]['id'],year_complete=False))
