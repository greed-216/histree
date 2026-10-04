# -*- coding: utf-8 -*-
"""Verify all 935 published paragraphs before advancing into volume 280."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==37 and [x['source_line'] for x in r]==list(range(85,122)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] and x['status']=='published_verified' for x in r)
proofs=[]
for part,start,end in [(YEAR/'part-01',0,11),(YEAR/'part-02',11,20),(YEAR/'part-03',20,28),(P,28,37)]:
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 assert {k for x in r[start:end] for k in x['event_keys']}=={x['key'] for x in read(part/'content-batch.json')['events']}
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
previous=YEAR.parent/'year-0934';prior=read(previous/'paragraphs.json');annual=read(previous/'progress-audit.json')
assert len(prior)==77 and all(x['status']=='published_verified' for x in prior) and annual['year_complete'] and annual['year_completed_paragraphs']==89
for proof in annual['batches']:
 part=ROOT/proof['batch'];h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert h==proof['batch_sha256']
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
assert lines[123]=='后晋纪' and lines[121:123]==['','']
nextpath=ROOT/'resources/derived/tongjian/280.txt';nl=nextpath.read_text().splitlines();assert len(nl)==77 and nl[4]=='天福元年丙申，公元九三六年' and all(nl[5:75]) and nl[75:]==['','']
ny=ROOT/'content/books/zizhi-tongjian/vol-280/year-0936';ny.mkdir(parents=True,exist_ok=True)
rows=[dict(id=f'zztj-v280-y0936-p{j:03d}',source_line=i,text=nl[i-1],status='pending',event_keys=[],book='资治通鉴',volume=280,year=936) for j,i in enumerate(range(6,76),1)]
if (ny/'paragraphs.json').exists():assert read(ny/'paragraphs.json')==rows
else:write(ny/'paragraphs.json',rows)
write(ny/'boundaries.json',dict(book='资治通鉴',volume=280,year=936,source_file=str(nextpath.relative_to(ROOT)),source_sha256=hashlib.sha256(nextpath.read_bytes()).hexdigest(),year_header_line=5,body_source_lines=[6,75],body_paragraphs=70,ledger_source_lines=[6,75],ledger_records=70,excluded_non_body=[dict(source_line=i,text=nl[i-1],reason='本卷标题、范围或年界结构项') for i in range(1,6)],next_volume=281,next_year=937,next_body_source_line=6,note='卷280天福元年原6—75行70正文均待录；该标题采用后晋改元纪年，其中前半仍属后唐清泰三年，事件纪年按原文分别核。包含史评与年末总述，不跳段。'))
(ny/'README.md').write_text('# 《资治通鉴》卷280 · 936年\n\n原6—75行70正文均待录，游标第1段。沿连续段落推进至后唐灭亡及本卷年末，当前0/70。卷首标题天福元年为后晋纪年，前半后唐清泰三年未据卷题提前改朝；史评与追叙保类型及不确定年。\n')
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[28]['id'],rows[0]['id']]
pr['active_cursor'].update(volume=280,year=936,last_reviewed_paragraph=r[-1]['id'],last_published_paragraph=r[-1]['id'],next_paragraph=rows[0]['id'],next_paragraph_opening=rows[0]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==935)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',volumes=[279],completed_volumes=[279],note='卷279本年37正文四批全部连续公开并独立匿名核验；原113—121行最后9段含闽政变、荆南史评、齐封国、闽叶翘、唐年末任官与陈天师。主新闽谥庙号、主旧冯任司空日异保留，未定年追叙不强定935。')
if not any(x['year']==936 for x in pr['year_coverage']):pr['year_coverage'].append(dict(year=936,status='in_progress',volumes=[280],batches=[],completed_volumes=[],note='卷280原6—75行70正文已核年界并建待录账本，0/70。下一段正月吴大元帅府。'))
for key,num,note in [('min_posthumous_titles',29,'主齐肃明孝皇帝惠宗、新惠皇帝太宗，谥庙号异说保原字待纸本，不擅覆盖。李仿/倣/亻放同官同事；王昶稳定别名，清远沿917汉主刘岩女婚事。'),('jingnan_comment_and_background',31,'以兄事非亲兄弟，郎君非儿子，臣光曰是宋史评非935人物在场言论；久、它日和退休后常态确年不具为null。'),('qi_grant_vs_foundation',32,'主十月授衔封齐国，新九月接封爵、三年建齐国属压缩层次；吴内封国不当南唐937已经建立。'),('ye_qiao_retirement_and_death',33,'叶福王友为往事，未几退归及寿终年未载，不填935卒年。元妃李敏女与贤妃李春燕分，甥历史称谓不造未名中间亲属。'),('feng_dao_sikong_date',36,'主十二月乙酉旧己丑冯任司空同命日異，军号匡国地名同州同；卢方案与冯答、卢止分，不称祭祀扫除已执行。')]:
 full='935-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[num-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=280,current_year=936,current_volumes=[280],current_batch=rel,next_paragraph=rows[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=935,completed_paragraphs=37,volume_total_paragraphs=37,year_completed_paragraphs=37,year_total_paragraphs=37,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=True,year_complete=True,next_volume=280,next_year=936,next_paragraph=rows[0]['id'],batches=proofs,year_scope=[dict(volume=279,body_paragraphs=37,published=37)]))
bd['note']='935年原85—121行37正文全部连续公开核验，原124行后晋纪结构标题不生成事实；包含臣光曰评论。已核936卷280年界，下一段原6行，全年尚待录。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 935年\n\n原85—121行37正文已分四批全部连续发布并独立匿名核验，全年37/37完成。下一段 zztj-v280-y0936-p001，936年正月吴徐知诰建大元帅府。\n\n保留完整史评、追叙和年末概述；简体展示，原文及异体保底本。闽谥庙号、冯道任司空日异并列，叶翘寿终与未明始年常态不硬定935。原124行后晋纪为结构标题，后接卷280天福元年，前段仍属后唐清泰三年。\n')
print(dict(year=935,completed=37,total=37,next_paragraph=rows[0]['id'],year_complete=True,next_year_pending=70))
