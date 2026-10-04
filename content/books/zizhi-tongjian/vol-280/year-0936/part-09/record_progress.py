# coding: utf-8
"""Advance past 936 only after complete publication and independent annual readback."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;Y=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(Y/'paragraphs.json');b=read(P/'content-batch.json');h=sha(P/'content-batch.json')
assert len(r)==70 and all(x['status']=='published_verified' for x in r[:53])
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==h
annual=read(P/'readback-audit.json');assert annual['year_complete'] and annual['year_body_paragraphs']==70 and annual['continuous_paragraph_coverage_verified'] and len(annual['all_year_batches_verified'])==9
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[53:]]
revisions=[]
for slug,file in [('2026-10-04-936-zhang-lingzhao-death','fields.json'),('2026-10-04-936-jingda-kang-deaths','fields.json'),('2026-10-04-936-tang-fall-deaths','fields.json'),('2026-10-04-zhang-yanqi-name','plan.json'),('2026-10-04-936-year-end-deaths','fields.json')]:
 path=ROOT/'content/revisions'/slug;proof=read(path/'publication.json');assert proof['verified'] and proof['revision_sha256']==sha(path/file)
 revisions.append(dict(path=str(path.relative_to(ROOT)),revision_sha256=proof['revision_sha256'],anonymous_readback_verified=True))
for x in r[53:]:x['status']='published_verified'
write(Y/'paragraphs.json',r)
nextY=ROOT/'content/books/zizhi-tongjian/vol-281/year-0937';nextY.mkdir(parents=True,exist_ok=True)
raw=ROOT/'resources/derived/tongjian/281.txt';lines=raw.read_text().splitlines();assert lines[4]=='天福二年丁酉，公元九三七年' and lines[5]=='春，正月，乙卯，日有食之。' and lines[64]=='◎' and lines[65]=='天福三年戊戌，公元九三八年'
nextrows=[dict(id=f'zztj-v281-y0937-p{n:03d}',source_line=n+5,text=lines[n+4],status='pending',event_keys=[],book='资治通鉴',volume=281,year=937) for n in range(1,60)]
assert all(x['text'] for x in nextrows)
if (nextY/'paragraphs.json').exists():assert read(nextY/'paragraphs.json')==nextrows
else:write(nextY/'paragraphs.json',nextrows)
write(nextY/'boundaries.json',dict(book='资治通鉴',volume=281,year=937,source_file=str(raw.relative_to(ROOT)),source_sha256=sha(raw),year_header_line=5,body_source_lines=[6,64],body_paragraphs=59,ledger_source_lines=[6,64],ledger_records=59,excluded_non_body=[dict(source_line=n,text=lines[n-1],reason='本卷标题、范围或年界结构项') for n in range(1,6)],next_year_structure=[dict(source_line=n,text=lines[n-1],reason='下一年分隔符或938年题，不属于937正文') for n in [65,66]],next_volume=281,next_year=938,next_body_source_line=67,note='仅初始化连续原文账本，59段全待录；人工核开头与938年界，未录入任何937史事。'))
(nextY/'README.md').write_text('# 《资治通鉴》卷281 · 937年\n\n59段原文账本已初始化（原6—64行），全部待录。原65行分隔符及66行938年题不属于本年正文。下一段 zztj-v281-y0937-p001：春，正月，乙卯，日有食之。\n')
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[53]['id'],nextrows[0]['id']]
pr['active_cursor'].update(volume=281,year=937,last_reviewed_paragraph=r[-1]['id'],last_published_paragraph=r[-1]['id'],next_paragraph=nextrows[0]['id'],next_paragraph_opening=nextrows[0]['text'],batch=rel,status='pending')
y=next(x for x in pr['year_coverage'] if x['year']==936)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',volumes=[280],completed_volumes=[280],note='卷280原6—75行70正文全部连续公开；9批原文、引用、参与和关系端点独立匿名核验。后唐辛巳灭亡及晋入洛后年末事均完成；下一卷281年937第1段尚待录。')
if not any(x['year']==937 for x in pr['year_coverage']):pr['year_coverage'].append(dict(year=937,status='pending',volumes=[281],completed_volumes=[],batches=[],note='原6—64行59正文已初始化，全部待录；938年题不计入937。'))
for key,n,note in [('zheng_ruan_variant',59,'主旧郑阮、新郑玩同曹州刺史被石重立杀链核为异写，保别名，新补己丑。'),('zhou_gui_variant',66,'主周瑰、旧帝纪周环、旧传周瑰按晋阳出纳旧臣、三司任命辞职链核同人，不建重复主体。'),('fang_death_day',67,'主庚子条下闻卒与旧传辛巳卒日疑差并列，卒年同936；需核纸本及纪日。'),('lu_wenjin_date',69,'主936十二月辛丑、旧传936十二月、新传元年冬、新纪937正月癸亥互异，保各书来源与元年冬二年初边界待核。'),('li_decheng_jingnan',70,'主李德诚荆南职疑镇南，原字保留未定新任荆南；待纸本和吴任职链校核。'),('zhou_quanjin_date',70,'新周劝进叙于937受禅后压写，主936本次与937复劝区分，不硬当同日；新死不提前填936。'),('goryeo_summary',70,'主压记击破新罗百济及府郡数，未分具体日期，不自动认两国同936同日军事灭亡；保史载概数。')]:
 full='936-v280-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=281,current_year=937,current_volumes=[281],current_batch=rel,next_paragraph=nextrows[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(Y/'progress-audit.json',dict(book='资治通鉴',volume=280,year=936,completed_paragraphs=70,volume_total_paragraphs=70,year_completed_paragraphs=70,year_total_paragraphs=70,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=True,year_complete=True,next_volume=281,next_year=937,next_paragraph=nextrows[0]['id'],batches=annual['all_year_batches_verified'],year_public_counts=annual['year_public_counts'],all_year_anonymous_readback_verified=True,revisions=revisions))
bd=read(Y/'boundaries.json');bd['note']='936年原6—75行70正文全部连续公开核验；开头5结构项不计正文，卷末空行不计正文。下一卷281年937第1段待录。';write(Y/'boundaries.json',bd)
(Y/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n70/70连续正文全部公开，9批原文、参与、关系、事实出处及姓名修订独立匿名核验。原文6—75行，开头5结构行与末空行不算史事。后唐辛巳灭亡和晋入洛后的年末各地史事均完成。\n\n下一段：卷281，937年 zztj-v281-y0937-p001；仅初始化原文账本，尚未录入。纸本校核和纪日异说见各批 coverage 及年度勘校followups，保原文不消除冲突。\n')
print(dict(completed=70,total=70,next=nextrows[0]['id']))
