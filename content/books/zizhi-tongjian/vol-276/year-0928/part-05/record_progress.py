# -*- coding: utf-8 -*-
"""Advance the consecutive 928 prefix only after exact public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:25])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[25:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P.parent/'part-04',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:25]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[17]['id'],rows[25]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[24]['id'],last_published_paragraph=rows[24]['id'],next_paragraph=rows[25]['id'],next_paragraph_opening=rows[25]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首25段已连续发布并逐条匿名回查，余27段待处理；全年未完成。')
for key,n,note in [
 ('chu_wu_shatou',18,'吴两俘将返归，许众驹争是判断非本年内战；马殷父希范关系复用，从嗣为季兴从子不补父名伯叔长幼。廖赣人不推坐标。'),
 ('forced_assault_losses',19,'畏怯为朱张宣言，主杀伤三千与旧伤者三千原分类并列；旧七月甲寅奏六月二十二行动，不把奏报日当攻城日。'),
 ('mao_garrison_chronology',20,'先是及后续撤戍追叙年null，新是岁承三年另存上下文；新将撤戍叙在高季兴死及从诲请命后，与主六月附近排列差异并列，不提前高死。'),
 ('wangyan_burial_year',21,'王衍沿王宗衍，主旧帝纪天成三年与新世家天成二年并列；诏许诸侯礼与实际葬日分层，十八丧三赵村补不强同日。'),
 ('yeast_tax_scope',23,'每亩五钱非商品曲价；食货原官曲酒户按上年官曲钱十取二非营业额20%，其他家用禁私卖及坊村例外原范围保留，非全国售酒免税。'),
 ('hemiao_relief_numbers',24,'本次惕隐据新四夷记名赫邈，不将官称所有任者合并。主新七千旧传五千并列；奏日与行军日分，满城斩二千马千与易州俘二千不同统计，不提前八月擒。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[25]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=25,volume_total_paragraphs=52,year_completed_paragraphs=25,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[25]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 928年 · part-05\n\n连续第18—25段（原文件50—57行）：36事件、52人物参与、170事实引用；4新增人物、16复用人物；1条父亲关系复用；9来源（6新增、3复用），补证《旧五代史》《新五代史》，另保留孟蜀世家纪年上下文。\n\n覆盖楚吴议和及两将返归、沙头楚荆南战、定州被迫攻城、毛重威夔州戍兵逃归、王衍追封葬礼、安审通去世、酒曲禁制与税法改革、契丹第二批援军唐河易州战、王延钧闽王爵。新增高从嗣、廖匡齐、毛重威、赫邈；惕隐是本次赫邈官称，不将历任同官自动合并。\n\n马希范之父是马殷，父亲边复用；高从嗣从子不补父亲或伯叔长幼。吴王彦章区别梁将。许德勋众驹争是预判，畏怯是朱张宣言；三千杀伤不改阵亡。毛先是及顷之追叙年null，新高季兴死后撤戍次序异说保留。王衍沿王宗衍；主旧天成三年与新二年并列，准诸侯礼不强实际下葬日，十八丧及三赵村补不推新死者名单。\n\n酒曲每亩五钱非商品价，原官曲户上年官曲钱十取二非营业收入20%，家用自造、商业售酒、坊村例外范围分别保留。主新七千援与旧王传五千不同兵数并列，唐河、满城、易州分事，二千级、千马、二千俘不同类别不相加作总死亡；未提前八月惕隐被擒。奏报日与所报行动日分别保留，旧夹通鉴注不算独立确证。\n\n来源原TXT与逐字摘录保持底本，展示简体。结构校验、源及上下文SHA、公开UUID、引用关联与固定GitHub链接已核验；纸本异文待考。未将跨未读段落的整个快照记完成。\n\n928年已连续完成25/52段，下一段zztj-v276-y0928-p026；目标继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 928年\n\n原文件33—84行，共52段正文；首25段五批已发布并匿名回查，余27段待连续处理。前后年界已核，卷277从930年开始。\n\n下一段zztj-v276-y0928-p026；连续前缀及证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=25,total=52,next_paragraph=rows[25]['id'],year_complete=False))
