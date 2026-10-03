# -*- coding: utf-8 -*-
"""Advance to 930 only after six batch audits and a fresh full-year public audit."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');future=read(ROOT/'content/books/zizhi-tongjian/vol-277/year-0930/paragraphs.json')
assert len(rows)==36 and len(future)==55
assert all(r['status']=='published_verified' for r in rows)
assert all(r['status']=='pending' and not r['event_keys'] for r in future)
yearproof=read(P.parent/'year-audit.json');assert yearproof['verified'] and yearproof['year_complete'] and yearproof['body_paragraphs']==36
proofs=[];covered=[]
for part in [P.parent/f'part-{n:02d}' for n in range(1,7)]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert yearproof['batch_sha256'][b['batch_key']]==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[32]['id'],future[0]['id']]
progress['active_cursor'].update(volume=277,year=930,last_reviewed_paragraph=rows[-1]['id'],last_published_paragraph=rows[-1]['id'],next_paragraph=future[0]['id'],next_paragraph_opening=future[0]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==929)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',completed_volumes=[276],note='929年卷276全部36正文段、6批连续发布并逐条匿名回查；全年重新核验全部公开UUID、出处关联和原文快照通过。930年55段尚待处理。',year_audit=str((P.parent/'year-audit.json').relative_to(ROOT)))
if not any(x['year']==930 for x in progress['year_coverage']):progress['year_coverage'].append(dict(year=930,status='in_progress',volumes=[277],batches=[],completed_volumes=[],note='930年卷277原6—60行共55正文段，年界回查，均待连续录入；第61—62行为分隔及931标题，不计930正文。'))
for key,n,note in [
 ('kangfu_battle_report_variants',33,'主青刚峡数千帐/旧丁酉奏方渠三百余帐有地数差，不用奏报日解释全部；牛羊三万非人，杀获非全杀，丁酉为奏日，卫规范字沿前批，受代非改朝。'),
 ('xu_wine_shenjiangao',34,'知询疑毒不是现代确认下毒者；拒酒、申合饮、密药、脑溃卒分，脑字原存不改肠或现代诊断。申案二十四史未检同案，主独证。主十二月加中书令、新十一月概叙差保留。'),
 ('wangyanbing_jixiong_identity',35,'廷禀沿已有王延禀，同建州及同子继雄对照，廷延原字并列；后新931战死只补身份不提前事件。称疾为本人陈述，父请任与庚子诏刺史分，父亲边方向明确。'),
 ('sichuan_marriage_and_surveillance',36,'既以仁矩镇承十月，不重授；武故吏外兄/新表兄方向武→安，不猜父母线。诇反目标、仁矩增饰非已确反，城隍是城防壕，绵龙划镇为传言。求婚只许未礼成，不造未名子女或姻亲边；谋拒非930已反，新孟赵问劝补，随后共同表与主930二月需后续对读。')
]:
 full='929-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=277,current_year=930,current_volumes=[277],current_batch=rel,next_paragraph=future[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=929,completed_paragraphs=36,volume_total_paragraphs=36,year_completed_paragraphs=36,year_total_paragraphs=36,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=True,year_complete=True,year_audit=str((P.parent/'year-audit.json').relative_to(ROOT)),next_paragraph=future[0]['id'],batches=proofs))
bd=read(P.parent/'boundaries.json');bd['note']='929年全文在卷276原87—122行，36正文段全部连续发布并通过全年匿名公开审计；卷尾123—124空行。卷277从930年开始，下一正文第6行。';write(P.parent/'boundaries.json',bd)
(P/'README.md').write_text('''# 《资治通鉴》卷276 · 929年 · part-06

连续第33—36段（原119—122行）：22新增事件、36人物参与、103事实引用；14人物（3新增）、2新增关系、6来源（3新增、3复用），补证《旧五代史》《新五代史》。新增申渐高、王继雄、武虔裕。

覆盖康福到灵州、朔方受代，徐氏酒宴及申渐高之死，建州父子任职，安重诲监查董璋及两川求婚联合。

康福方渠邀击与青刚峡突袭分；数千帐不是人数，杀获不是全杀。旧十二月丁酉奏两族于方渠三百余帐、牛羊三万，与主峡数千帐有地数差并列，奏日不倒赋战日。卫规范字沿前批，原私用字保留。受代是朝廷派代，不是改朝换代。

吴加徐知诰中书令、宁国主十二月，新概叙十一月，保留纪时差。酒宴先记疑毒，不直接确认徐知诰下毒；拒酒、申诙谐合饮、密药、脑溃卒分，脑字原留，不推现代毒物或自杀。此案二十四史未检得同案补证，主独证。

王廷禀按建州身份沿王延禀稳定人物，廷延异名并列；后新闽同子继雄只作身份与父子补证，931战死不提前。父请任与庚子诏刺史分。王延禀→王继雄为父亲。武虔裕主外兄、新表兄，武→安重诲为表兄，不猜具体父母线。

反状为侦查目标，仁矩增饰奏不等当时董已反；城隍是防城壕，道路绵龙划镇是传言。求婚主许未礼成，不造未名子女或婚姻边。谋联合不提前930实际起兵；新孟赵季良问劝补，其后共表慰诏留930主段对读。

来源SHA、逐字引用、公开UUID、source关联及固定GitHub链接均已回查。929年全部36段、6批完成，全年重新公开审计通过。纸本异文仍待校。

下一段zztj-v277-y0930-p001；继续至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷276 · 929年

原文件87—122行，共36正文段、6批，全部连续发布并匿名回查。全年重新核验全部公开UUID、原文SHA、逐字引用、source关联与固定出处通过，详见year-audit.json。

年度连续覆盖完成不等纸本异文已全部定论；待考问题见各批coverage与editorial_followups。

下一段zztj-v277-y0930-p001。930年卷277原6—60行共55段，均待处理；第61—62行为年界分隔和931标题。
''')
print(dict(completed=36,total=36,next_paragraph=future[0]['id'],year_complete=True))
