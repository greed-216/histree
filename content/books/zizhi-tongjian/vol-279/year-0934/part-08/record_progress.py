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
assert all(x['status']=='published_verified' for x in r[:58]) and all(x['status']=='pending' and not x['event_keys'] for x in r[58:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[46:58]]
assert {k for x in r[46:58] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
for first,start,end in [(YEAR/'part-01',0,4),(YEAR/'part-02',4,8),(YEAR/'part-03',8,13),(YEAR/'part-04',13,18),(YEAR/'part-05',18,23),(YEAR/'part-06',23,34),(YEAR/'part-07',34,46)]:
 firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
 assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[46]['id'],r[58]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[57]['id'],last_published_paragraph=r[57]['id'],next_paragraph=r[58]['id'],next_paragraph_opening=r[58]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前58段连续公开并独立匿名核验，全年70/89。卷279原52—63行重美授职、文附蜀、吴降濛监守、后唐争相择卢立后、护贡令宋退居、二王宴与蜀授职、孟知祥死及孟昶改名即位已录；第59段刘昫税逋核免待录，全年未完成。')
for key,n,note in [('liu_xu_gou_character',50,'主蚼上下文刘昫、旧刘煦同李愚争执，沿已核昫主体；原疑字保源，不靠繁简转换。'),('lottery_jin_zhu_character',50,'主筋挟、新卢传筯挟，展示筷校读但主引文不改；夹取为史叙，不当神意证据或姚已七月任相。'),('liu_empress_identity',52,'末帝沛国刘后新旧一致，区别庄宗刘玉娘及其他刘氏。新明重美等不知生母，不自动设刘后母；父茂威有新传明文。'),('niu_escort_hou_character',53,'主禁后卫疑字保原，只录诏牛兵护贡及会邠州兵讨，未证已执行胜；929牛护康是另事。'),('song_right_pushe_character',54,'主右仆谢为疑写，沿既有宋右仆射身份；保源。新吴同年司空仅补衔，未查到独立南园同事，不混后九华隐。'),('shu_renhan_shi_character',57,'主教见李什罕，前后李仁罕、仁罕第对应沿同人；底字保原。设备不猜已兵变，赵强将警言非诸将确实叛。'),('meng_death_compacted_month',57,'主七月甲子夜殂、旧辑补孟传七月卒；新世家六月宴劳后连记病立储死亡未独列确日，不套全段六月或改主日期。旧大典原阙册府辑补层如实标，不作完整原薛史。'),('shu_regency_yi_character',57,'主受遣诏辅政，遣疑遗，保底字只录召受诏辅政；无独立别书六人召命不伪造多书证。'),('meng_secret_crying_scope',57,'主王处回泣、新相对泣范围不同，各引独立原句；王处回、赵季良立后发丧新补，不强定所有阶段同甲子。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[58]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=58,volume_total_paragraphs=77,year_completed_paragraphs=70,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[58]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=58)]))
bd['note']='934年本卷原6—82行77正文段；前58段原6—63行公开核验，原64行第59段刘昫税逋核免待录。全年跨卷278的12段和279的77段共89正文，当前70/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前58已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前70/89。下一段 zztj-v279-y0934-p059（原64行），卷与全年未完成。\n\n后唐择相立后与吴降濛监守、宋退居、蜀任官及孟知祥去世、孟昶改名即位分录；指控、意向及诏令不当已完成行动。繁简展示与疑字校读分别说明，孟病逝压缩叙事和旧传辑补层保可追溯定位。\n')
print(dict(year=934,completed=70,total=89,next_paragraph=r[58]['id'],year_complete=False))
