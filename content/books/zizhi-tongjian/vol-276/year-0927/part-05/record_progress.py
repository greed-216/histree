# -*- coding: utf-8 -*-
"""Advance to 928 only after exact public batch and full-year audits."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
first=ROOT/'content/books/zizhi-tongjian/vol-275/year-0927';rows1=read(first/'paragraphs.json');rows=read(P.parent/'paragraphs.json');nextdir=P.parent.parent/'year-0928';future=read(nextdir/'paragraphs.json')
assert len(rows1)==32 and len(rows)==25 and len(future)==52
assert all(r['status']=='published_verified' for r in rows1+rows)
assert all(r['status']=='pending' and not r['event_keys'] for r in future)
parts=[first/f'part-{n:02d}' for n in range(1,7)]+[P.parent/f'part-{n:02d}' for n in range(1,6)];proofs=[];covered=[]
yearproof=read(P.parent/'year-audit.json');assert yearproof['verified'] and yearproof['year_complete'] and yearproof['body_paragraphs']==57
for part in parts:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert yearproof['batch_sha256'][b['batch_key']]==sha
 assert {k for r in rows1+rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows1+rows]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[18]['id'],future[0]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[-1]['id'],last_published_paragraph=rows[-1]['id'],next_paragraph=future[0]['id'],next_paragraph_opening=future[0]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',completed_volumes=[275,276],note='927年卷275全部32段和卷276全部25段，共57正文段，11批已连续发布并逐条匿名回查；全年审计通过，928年52段尚待处理。',year_audit=str((P.parent/'year-audit.json').relative_to(ROOT)))
if not any(x['year']==928 for x in progress['year_coverage']):progress['year_coverage'].append(dict(year=928,status='in_progress',volumes=[276],batches=[],completed_volumes=[],note='928年卷276原文件33—84行共52正文段，年界已核，均待连续录入；卷277从930年开始。'))
for key,n,note in [
 ('wu_kinship',21,'王氏仅吴太妃不猜生母；珙为杨溥兄子只建叔父关系，不从相邻濛猜父亲。'),
 ('zhouxuanbao_retrospective',22,'初预言与即位后召见计划未明确年，保留null；新补易服和不复召，话语不作相术能力证明；就除致仕非入京履任。'),
 ('temple_and_border_prices',23,'主诸提案与最终应州令分阶段；旧新丙午仅实际追尊立庙；祖先列表考未具名不猜谱系。主年度蔚代粟价和旧周令武己卯奏山北价格地域叙法并存，不推全国富裕。')
]:
 full='927-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=future[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=927,completed_paragraphs=25,volume_total_paragraphs=25,year_completed_paragraphs=57,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=True,year_complete=True,year_audit=str((P.parent/'year-audit.json').relative_to(ROOT)),next_paragraph=future[0]['id'],batches=proofs))
(P/'README.md').write_text('''# 《资治通鉴》卷276 · 927年 · part-05

连续第19—25段（原文件24—30行）已发布：20事件、23人物参与、3人物关系（2新增、1复用）、86事实引用；5新增人物、9复用人物；4来源（2新增、2复用）。补证《旧五代史》卷38、《新五代史》卷6和28。

吴王氏尊太后及徐知询、徐知诰官衔分事；未明王氏生母身份不建母子边。成都二十万民丁修城是征发，未推兵力或竣工。三封王未具日，不强戊寅；濛兄溥复用，溥兄澈、叔父珙按方向建边；珙父未明，不推杨濛。

周玄豹初相术预言、即位后召见计划及赵凤进谏未明确年，年null；新补易服故事和不复召，均保留史书记载性质，不证明相术有效。就除光禄卿致仕、赐金帛不等入京履任。

马缟与群臣各提案、帝意向、援引前代先例、最终应州旧宅令及追尊分阶段；旧新补十二月丙午，只赋实际追尊立庙，不赋前面讨论。新补祖考谥号列表，考无名不猜造人物谱系。刘岩到康州不推征讨。蔚代缘边年度粮价与旧周令武己卯奏报山北雁门北价格分别留出处，未换算斗钱或扩大为全国及每户富裕。

批次哈希、逐字摘录、源行与来源SHA、公开UUID、source关联和固定GitHub地址已匿名读回。展示简体，原文保留底本，纸本及异文待核。

927年两卷57段、11批全部已发布，并经全年审计；下一段zztj-v276-y0928-p001，继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷276 · 927年

本卷25正文段（原文件6—30行），五批全部已发布并匿名回查。927年另含卷275全部32段，共57正文段、11批，全年审计通过。

全年正文、原文行、摘录、批次哈希、公开UUID和出处关联的独立读回见year-audit.json；连续覆盖证明见progress-audit.json。

下一段zztj-v276-y0928-p001。928年卷276共52正文段尚待录入。
''')
print(dict(completed=57,total=57,next_paragraph=future[0]['id'],year_complete=True))
