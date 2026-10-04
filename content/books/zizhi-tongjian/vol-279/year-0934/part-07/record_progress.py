# -*- coding: utf-8 -*-
"""Advance exactly twelve verified body paragraphs; leave all later body paragraphs pending."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==77 and [x['source_line'] for x in r]==list(range(6,83)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:46]) and all(x['status']=='pending' and not x['event_keys'] for x in r[46:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[34:46]]
assert {k for x in r[34:46] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
for first,start,end in [(YEAR/'part-01',0,4),(YEAR/'part-02',4,8),(YEAR/'part-03',8,13),(YEAR/'part-04',13,18),(YEAR/'part-05',18,23),(YEAR/'part-06',23,34)]:
 firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
 assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[34]['id'],r[46]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[45]['id'],last_published_paragraph=r[45]['id'],next_paragraph=r[46]['id'],next_paragraph_opening=r[46]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前46段连续公开并独立匿名核验，全年58/89。卷279原40—51行明宗葬、石敬瑭请归河东复任、五月诸任官、张孙迁成都、李从曮复镇、房知温入朝与徐知询卒、蜀取成州已录；第47段六月重美授职待录，全年未完成。')
for key,n,note in [('han_zhaoyun_alias',36,'主及新韩昭胤，旧同丙午端明学士转枢密作昭允；同职同日识别既有韩主体，原字待纸本，不靠繁简转换。'),('fang_gao_ji_character',36,'主权知枢密院记、旧权知枢密事，事记疑字保底本，任北院一致；不自动改源。'),('xiangli_jin_day_order',37,'戊午在丁未前，旧同戊午；正文次序不倒排，陕州保义州与军号。'),('li_congyan_private_glyph',43,'主李从私用字严、新从曮同拦马复镇、旧从严同任，沿既有李继曮主体别名；摘录保缺字不覆底本。'),('fang_royal_enfeoffment_order',44,'旧房传称末帝先封王宁其心再入朝、新房传记入朝慰劳返镇封东平王；同人优礼一致，封与朝先后不同保各来源，无证不给主壬戌封爵日。'),('li_chong_pinglu_identity',44,'平卢房知温司马李冲（新李沖）消歧单列；不并李再丰子与华州都监，生卒籍贯未知。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[46]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=46,volume_total_paragraphs=77,year_completed_paragraphs=58,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[46]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=46)]))
bd['note']='934年本卷原6—82行77正文段；前46段原6—51行公开核验，原52行第47段六月重美授职待录。全年跨卷278的12段和279的77段共89正文，当前58/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前46已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前58/89。下一段 zztj-v279-y0934-p047（原52行），卷与全年未完成。\n\n明宗葬与护送、石敬瑭请归意见与复任、诸任官、迁家与抵达、请许与李从曮复镇、房知温察形势与入朝、徐知询卒及蜀取成州分录；繁简只用于展示和实体匹配，韩异写、房前职疑字及李缺字保原文校核。\n')
print(dict(year=934,completed=58,total=89,next_paragraph=r[46]['id'],year_complete=False))
