# -*- coding: utf-8 -*-
"""Record the first 12 consecutive 926 paragraphs after exact public readback."""
import hashlib
import json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
audit=read(P/'readback-audit.json');b=read(P/'content-batch.json')
assert audit['verified'] and audit['batch_sha256']==hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
ledger=read(P.parent/'paragraphs.json');other=read(ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/paragraphs.json')
assert len(ledger)==43 and len(other)==67
assert all(r['status']=='published_verified' for r in ledger[:12])
assert all(r['status']=='pending' for r in ledger[12:]+other)
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (ledger[0]['id'],ledger[12]['id'])
progress['active_cursor'].update(volume=274,year=926,last_reviewed_paragraph=ledger[11]['id'],last_published_paragraph=ledger[11]['id'],next_paragraph=ledger[12]['id'],next_paragraph_opening=ledger[12]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[],note='926年共110正文段；卷274第1—12段已发布并逐ID匿名读回及固定URL核对。卷274余31段、卷275全67段待处理，全年未完成。')
for key,n,note in [
 ('private-glyphs',1,'李继拆字严为李继曮，李严另人；第3段张拆字厉据旧史滏阳、军书职与府第恸哭同事校张砺，底本字形保留。'),
 ('shiwu-office',8,'吏武据两史旧将七刺史校史武；成都节度使李嗣源据前后成德军职校为职名疑字。七将中其余六人先保存新本纪具名原文，白奉国与901主体是否同人须继续核，不贸然合并。'),
 ('khitan-envoy',6,'梅老鞋里断名未决，两书均无分隔，暂不建立人名实体；与梅老没古、梅老述骨关系后续核。'),
 ('dates-offices',12,'主癸巳入鄴与新本纪甲午叙陷都、主皇甫等马步都指挥使与旧都虞候斩斫使分别保留待纸本。李存乂主庚辰幽、寻杀与旧庚辰伏诛不强合确日。')]:
 full='926-v274-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=274,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=ledger[12]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=274,year=926,completed_paragraphs=12,volume_total_paragraphs=43,year_completed_paragraphs=12,year_total_paragraphs=110,continuous_prefix_verified=True,volume_complete=False,year_complete=False,next_paragraph=ledger[12]['id'],batches=[dict(batch=rel,batch_sha256=audit['batch_sha256'],anonymous_readback_verified=True)],batch_totals={k:len(b[k]) for k in ['events','claims']}))
(P/'README.md').write_text('# 《资治通鉴》卷274 · 926年 · part-01\n\n连续第1—12段（原文件38—49行）已发布：41事件、98参与、265引用；新增20人、6条关系，其余人物和关系复用。\n\n补证来自《旧五代史》卷34、98和《新五代史》卷5、14、45。郭朱谋反和刘后弑帝为告言、谗言或讹言，不作已证事实。皇后教令、继岌先拒后从、李环实际击杀、李崧事后伪敕分录；成都二子与洛阳三子分录。朱友谦被杀、诛子诏令、河中家属实际就刑区分。\n\n底本吏武据两史校史武、成都李嗣源职名有疑、张拆字厉据旧张砺传校名；原字保留，展示简体。梅老鞋里断名未定，暂不造人物；七将其余六名保留新史原文，身份核后再建主体。乐人数、李存乂幽杀叙日、鄴陷日期和皇甫官职异说分别可回查。第11段横跨两个阅读块，逐块引用，不拼造快照。\n\n验证见publication.json和readback-audit.json：批次哈希、连续源行、快照哈希、全部公开ID及具体出处ID/URL均已核。下一段zztj-v274-y0926-p013；926年共110正文段，全年未完成。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷274 · 926年\n\n本卷43正文段（原文件38—80行），第1—12段已发布并匿名读回；其余31段待录。\n\n926年还包含卷275的67段，共110段，目前完成12段。下一段zztj-v274-y0926-p013。\n')
print(dict(completed=12,total=110,next_paragraph=ledger[12]['id'],year_complete=False))
