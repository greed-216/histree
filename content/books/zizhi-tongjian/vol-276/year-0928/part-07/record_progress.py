# -*- coding: utf-8 -*-
"""Advance the consecutive 928 prefix only after exact public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:40])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[40:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P.parent/'part-04',P.parent/'part-05',P.parent/'part-06',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:40]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[32]['id'],rows[40]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[39]['id'],last_published_paragraph=rows[39]['id'],next_paragraph=rows[40]['id'],next_paragraph_opening=rows[40]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首40段已连续发布并逐条匿名回查，余12段待处理；全年未完成。')
for key,n,note in [
 ('zhangxichong_return_offices',33,'初接任谋归杀将攻营追叙年null；主卢龙守平州新平州节度不同称法，归众二万余口不是士兵。旧闰月上表、十月八十余入见、十一月壬午汝刺与列传防御使并列，不强整段同月；杀后投坑与旧投坑中毙不猜现代死因。'),
 ('wu_dowager_baitian',35,'吴太后沿927王太妃，不混明宗王德妃。白田新乾贞二年由既存前段改元定位，三十四将吏不等全部军人数；李被送吴非自愿新任，不推高亲临统军。'),
 ('wentao_duanning_death_edict',36,'令赐死只是命令，不独证当天执行；盗陵反覆为往事理由非928新案。旧同诏陶石聂及各任所补，不能说主载五人。'),
 ('qingzhou_refusal_campaign',38,'九月辛丑金州任命非实际赴任，十月据庆拒命不同动作；旧课利不集背景不精算盐额，新简反段序不强八月确日，不提前十二月族诛。'),
 ('licongmin_title_kinship',39,'从子未明父名伯叔长幼，不造亲父或确定叔父边；主副讨旧招讨职称并列，十月李敬周命讨不等已平城。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[40]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=40,volume_total_paragraphs=52,year_completed_paragraphs=40,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[40]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 928年 · part-07\n\n连续第33—40段（原文件65—72行）：22事件、25人物参与、104事实引用；8新增人物、7复用人物；1条新增父亲关系；10来源（7新增、3复用），补证《旧五代史》《新五代史》，乾贞改元上下文复用927快照。\n\n覆盖张希崇南归、入朝和汝州授官，吴太后薨，白田楚军败及李廷规被擒，温韬段凝等赐死令，房知温荆南军命与襄阳动员，窦廷琬金州调任拒命，李从敏北面军衔、李敬周讨庆诏。新增张希崇、张行简、李廷规、陶玘、石知讷、聂屿、窦廷琬、李从敏。\n\n张谋归各步骤初追叙年null，没于契丹为被俘非死；二万余口是人口，不是二万兵。旧闰月上表、十月八十余入见、十一月壬午汝刺分定位，列传防御使补衔并列，不强整段同在闰八月；未提前屯田、后官及卒。张父行简方向明确，李从敏从子不猜伯叔及父。\n\n吴王氏沿927太妃，不混李嗣源王德妃。新白田乾贞二年由前段改元确认，三十四将吏非总军数，李送吴非已任吴官。乙未敕所在赐死为命令，不直接写当天执行；主盗陵反覆为理由不建本年新案。旧独补陶石聂各职及温段流所，不说主载五人。\n\n武宁徐州、静难邠州同军治州；发兵襄阳不等江陵克。金州调令与庆拒不同，旧课利不足背景不精算，主副招讨与旧招讨异称并列。未提前十二月窦族诛。\n\n来源原TXT、逐字引文及定位保留底本；展示简体。结构校验、来源及上下文SHA、公开UUID、引用关联和固定GitHub链接已核验，纸本异文待考。快照中未读其他段不算完成。\n\n928年完成40/52段，下一段zztj-v276-y0928-p041；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 928年\n\n原文件33—84行，共52段正文；首40段七批已发布并匿名回查，余12段待连续处理。前后年界已核，卷277从930年开始。\n\n下一段zztj-v276-y0928-p041；连续前缀及证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=40,total=52,next_paragraph=rows[40]['id'],year_complete=False))
