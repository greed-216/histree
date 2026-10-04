# -*- coding: utf-8 -*-
"""Advance exactly eleven verified body paragraphs; leave all later body paragraphs pending."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==77 and [x['source_line'] for x in r]==list(range(6,83)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:34]) and all(x['status']=='pending' and not x['event_keys'] for x in r[34:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[23:34]]
assert {k for x in r[23:34] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
for first,start,end in [(YEAR/'part-01',0,4),(YEAR/'part-02',4,8),(YEAR/'part-03',8,13),(YEAR/'part-04',13,18),(YEAR/'part-05',18,23)]:
 firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
 assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[23]['id'],r[34]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[33]['id'],last_published_paragraph=r[33]['id'],next_paragraph=r[34]['id'],next_paragraph_opening=r[34]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前34段连续公开并独立匿名核验，全年46/89。卷279原29—39行入朝判三司、蜀明德、刘遂清撤戍归朝赦、蜀入两州、改元赦与授职、康药被杀及王苌释放、征财进言和三档诏赏已录；第35段明宗葬待录，全年未完成。')
for key,n,note in [('shu_zaishe_character',26,'底本蜀在赦疑字保原，明确改元明德已录；新世家只记四月改元，赦令性质范围尚待纸本核，不无证改大。'),('hao_qiong_south_north_office',30,'主丁亥以南院使郝权判枢密，旧同日北院改南院权判；同人权判一致，原职职序不同分列。'),('yao_execution_days',32,'主康戊子药己丑，新废帝纪戊子康药一并杀，旧戊子削夺诏不是每人已行刑证明；保诏与实际行动。'),('chang_congjian_chang_character',33,'主庚寅释条作苌长简，前同案从简、新苌传兵溃被执获释可匹配已有从简；从长非繁简转字，底字保原待纸。'),('liu_suiqing_dependent_note',27,'旧刘遂清传谱系、字及籍贯为正文补证，其撤戍与赦免段明确附引通鉴，标依赖不作独立确认。父琪消歧为刘琪（刘遂清父），不补退休年。'),('reward_dependent_number_note',34,'旧末帝纪正文壬辰诏赏不同额可印证，具体二马驼七十等在附引通鉴注中，不能作独立数字验证。征财六万、总集二十万与三档诏赏分层，均给原则不是同额。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[34]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=34,volume_total_paragraphs=77,year_completed_paragraphs=46,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[34]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=34)]))
bd['note']='934年本卷原6—82行77正文段；前34段原6—39行公开核验，原40行第35段明宗葬仍待录。全年跨卷278的12段和279的77段共89正文，当前46/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前34已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前46/89。下一段 zztj-v279-y0934-p035（原40行），卷与全年未完成。\n\n撤戍弃地、归朝赦、改元任官、康药死亡与王苌释放、征财及三档赏诏分录。赦字和人物异写保原文，药死亡日期并列；明确旧传附引通鉴的依赖关系，避免重复计为独立补证。\n')
print(dict(year=934,completed=46,total=89,next_paragraph=r[34]['id'],year_complete=False))
