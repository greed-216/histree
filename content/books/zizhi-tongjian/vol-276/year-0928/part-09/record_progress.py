# -*- coding: utf-8 -*-
"""Advance the cursor only after exact batch and complete 928 year audits."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');future=read(P.parent.parent/'year-0929/paragraphs.json')
assert len(rows)==52 and len(future)==36
assert all(r['status']=='published_verified' for r in rows)
assert all(r['status']=='pending' and not r['event_keys'] for r in future)
yearproof=read(P.parent/'year-audit.json');assert yearproof['verified'] and yearproof['year_complete'] and yearproof['body_paragraphs']==52
proofs=[];covered=[]
for part in [P.parent/f'part-{n:02d}' for n in range(1,10)]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert yearproof['batch_sha256'][b['batch_key']]==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[47]['id'],future[0]['id']]
progress['active_cursor'].update(volume=276,year=929,last_reviewed_paragraph=rows[-1]['id'],last_published_paragraph=rows[-1]['id'],next_paragraph=future[0]['id'],next_paragraph_opening=future[0]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',completed_volumes=[276],note='928年卷276全部52正文段、9批已连续发布并逐条匿名回查；全年重新核验公开UUID、出处关联和原文快照通过。929年36段尚待处理。',year_audit=str((P.parent/'year-audit.json').relative_to(ROOT)))
if not any(x['year']==929 for x in progress['year_coverage']):progress['year_coverage'].append(dict(year=929,status='in_progress',volumes=[276],batches=[],completed_volumes=[],note='929年卷276原文件87—122行共36正文段，年界卷末已核，均待连续录入；卷277从930年开始。'))
for key,n,note in [
 ('qingzhou_capture_clan_execution',48,'甲辰为李敬周奏报克庆与窦族诛时点，实际攻克执行确日不独具，族诛范围人数未明，不写九族精数。'),
 ('gaojixing_death_calendar',49,'主十二月丙辰卒，旧帝纪十一月壬午已奏卒产生时间倒置，明确异说保留，不能以奏报日与卒日一般间隔解释。旧新冬年相合；脚气古病名不现代足癣诊断，71龄不倒生年，吴任从诲与后唐后续授分；不提前归唐及后封。'),
 ('zhangzhao_princely_education',50,'张昭远与张昭同人，宋史避汉祖讳为后期姓名原因非928改名；先朝游乐为其奏言评语，建储不敢轻议不等已请立具体太子，择师及礼遇建议未实行。'),
 ('yanjun_ordains_congrong_yang_feng',51,'闽二万度僧主独证，未找到二十四史同案补证，人数照录不扩现代核实。李从荣忧废是主观疑虑，杨劝募甲为建议非已备反；匿名左右不造姓名，河南相公从厚只比较非在场，兄长边复用927。新喜儒诗为生平补述不定本月。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=929,current_volumes=[276],current_batch=rel,next_paragraph=future[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=52,volume_total_paragraphs=52,year_completed_paragraphs=52,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=True,year_complete=True,year_audit=str((P.parent/'year-audit.json').relative_to(ROOT)),next_paragraph=future[0]['id'],batches=proofs))
(P/'README.md').write_text('''# 《资治通鉴》卷276 · 928年 · part-09

连续第48—52段（原文件80—84行）：20事件、30人物参与、94事实引用；12人物均复用；2条亲属关系均复用；8来源（5新增、3复用），补证《旧五代史》《新五代史》《宋史》。

覆盖庆州克与窦廷琬族诛，高季兴病中委子权军府、卒与吴授高从诲官，张昭远皇子教育与礼遇建议，闽王王延钧度二万民为僧，李从荣忧废及杨思权劝募兵、冯赟密奏、召杨不罪。

甲辰记奏报，不强定执行日；族诛不猜九族人数。高卒主十二月丙辰、旧帝纪十一月壬午已奏卒有矛盾，并列留出处待核，不掩为普通奏报时间差。旧新冬与卒年互证；脚气古病名不诊断现代足癣，71龄不倒生年。吴任官不等后唐后来授职，不提前929—930归唐任命或封王。

张昭远沿张昭（五代宋初），宋史名字原因只作同人补证，改名不写为928事件。张建议未用，不等已建太子或已实行教育制度。闽度僧人数照录，仅主书记载同案，未查得独立补证。李从荣疑废为当事人担忧，杨劝增募修甲为建议，未推已经兵变；从厚只在比较中提及，未写在场。兄长关系和高氏父亲关系复用已发布对象。

来源SHA、逐字摘录、公开UUID、source关联及固定GitHub链接已匿名回查；展示简体，原文保留底本，纸本异文待考。

928年全部52正文段、9批完成，经全年重新公开核验。下一段zztj-v276-y0929-p001；继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷276 · 928年

原文件33—84行，共52正文段、9批，全部发布并匿名回查。全年重新核验全部公开UUID、逐字摘录、原文SHA、source关联与固定GitHub出处，详见year-audit.json；连续覆盖证明见progress-audit.json。

年度覆盖完成不等纸本异文已经全部定论，疑字、纪时差异和史料分歧见各批coverage及editorial_followups。

下一段zztj-v276-y0929-p001。929年原文件87—122行共36正文段，尚待连续录入；卷277从930年开始。
''')
print(dict(completed=52,total=52,next_paragraph=future[0]['id'],year_complete=True))
