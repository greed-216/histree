# -*- coding: utf-8 -*-
"""Advance only the exact publicly verified 929 continuous prefix."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==36
assert all(r['status']=='published_verified' for r in rows[:16])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[16:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(87,123))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
prev=read(P.parent.parent/'year-0928/year-audit.json');assert prev['verified'] and prev['year_complete'] and prev['body_paragraphs']==52
proofs=[];covered=[]
for part in [P.parent/'part-01',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:16]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[8]['id'],rows[16]['id']]
progress['active_cursor'].update(volume=276,year=929,last_reviewed_paragraph=rows[15]['id'],last_published_paragraph=rows[15]['id'],next_paragraph=rows[16]['id'],next_paragraph_opening=rows[16]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==929)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='929年卷276共36正文段，首16段已连续发布并逐条匿名回查，余20段待处理；全年未完成。')
for key,n,note in [
 ('maxisheng_power_and_coin_variants',9,'马希声知政总军非继王位，927建国判军与929知政不强同次，次子明字若讷补。铁锡与旧铁鑞材字不同，鑞简镴不等锡，底本保留；铜一锡百是史载值不现代汇率。'),
 ('dangxiang_border_horse_policy',12,'初令本次新政策不当初追叙，先是旧贡酬馆赏及岁50余万年null，岁费非单匹价或本年独账；停直接赴阙不等全禁购马或党项所有朝贡；旧锡赉为赏赐词。'),
 ('congrong_office_year_and_khitan_envoy',13,'从荣河南六卫主旧929四月壬子、新列传长兴元年930纪年差保留，秦王后爵不提前。四月云寇不同五月再寇。旧癸丑捺括梅里等取秃馁骨并斩市，新同日撩括梅里求秃馁杀之省略对象，异目的及指代保留不造秃二次死。'),
 ('aidi_title_temple_proposal',16,'太常定谥景宗为五月奏内前案，原议年null；五月乙酉中书以别庙不应宗，朝去庙号不等废谥或毁庙。哀帝李祚复用，日疑曰原字留，不新建景宗人物。')
]:
 full='929-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=929,current_volumes=[276],current_batch=rel,next_paragraph=rows[16]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=929,completed_paragraphs=16,volume_total_paragraphs=36,year_completed_paragraphs=16,year_total_paragraphs=36,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[16]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 929年 · part-02\n\n连续第9—16段（原文件95—102行）：19事件、11人物参与、71事实引用；2新增人物、6复用人物；1条新增父亲关系；7来源（5新增、2复用），补证《旧五代史》《新五代史》。\n\n覆盖马殷命马希声知政、国政处理流程，铁锡钱禁令及湖南币值流通，楚王环石首败荆南，党项边境马市与旧贡马费制，两皇子军府官职，云州侵扰和契丹使事件，赵凤任相，唐哀帝谥与景宗庙号议。新增马希声、捺括梅里；马殷是马希声的父亲，不建反向重复。\n\n马希声知政不等继王位，旧建国判军背景与本次知政不强为同一次任命。旧铁鑞与主铁锡材字异文，鑞简镴不等锡；一铜值百锡为史载值不转现代汇率。王环为楚将沿既有，石首旧奏未独战日，不混前壬寅殿成。\n\n初令是本次新马市政策；先是贡马酬价、接待赏赐及岁50余万费为旧制追叙年null，不写单匹马价或本年独账。停止直赴阙方式不等停止所有买马或朝贡；锡赉为赏赐词。新从荣列传河南任职930与主旧929不同年并列；原秦王为后爵回称。从荣河南、从厚河东北都不交换写错。\n\n四月云寇与后五月再寇分。旧癸丑捺括梅里等取秃馁骸骨、使被斩为独立补证；新作撩括梅里、求秃馁杀之，目的与省略对象保留，不据此再造秃馁第二次死亡。赵相同日，新兼工部尚书补衔，不另建第二任相。\n\n太常定号为五月奏中前案，原议年null；中书奏、去景宗号本年乙酉有据。哀帝沿李祚，不新建景宗；去庙号非去谥号或毁别庙，日疑曰字原留。\n\n公开UUID、逐字摘录、SHA、source关联及固定GitHub出处已核验。展示简体，原文底本字形保留，纸本异文待核；快照中后续段未计完成。\n\n929年完成16/36段，下一段zztj-v276-y0929-p017；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 929年\n\n原文件87—122行，共36段正文；首16段两批已连续发布并匿名回查，余20段待处理。年界和卷末已核，下一卷277从930年开始。\n\n下一段zztj-v276-y0929-p017；连续覆盖和验证证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=16,total=36,next_paragraph=rows[16]['id'],year_complete=False))
