# -*- coding: utf-8 -*-
"""Advance exactly five verified body paragraphs; leave all later body paragraphs pending."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==77 and [x['source_line'] for x in r]==list(range(6,83)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:13]) and all(x['status']=='pending' and not x['event_keys'] for x in r[13:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[8:13]]
assert {k for x in r[8:13] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for part in previous.glob('part-*'):
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
for first,start,end in [(YEAR/'part-01',0,4),(YEAR/'part-02',4,8)]:
 firstsha=hashlib.sha256((first/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(first/f);assert a['verified'] and a['batch_sha256']==firstsha
 assert read(first/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(first.relative_to(ROOT)),batch_sha256=firstsha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));proofs.append(dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True))
pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[8]['id'],r[13]['id']]
pr['active_cursor'].update(volume=279,year=934,last_reviewed_paragraph=r[12]['id'],last_published_paragraph=r[12]['id'],next_paragraph=r[13]['id'],next_paragraph_opening=r[13]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278,279],completed_volumes=[278],note='934年卷278的12段及卷279前13段连续公开并独立匿名核验，全年25/89。卷279原14—18行凤翔攻城倒戈、李从珂东进、闵帝召兵赏军、重吉惠明遇害、朱洪实被斩与王思同遇害已录；第14段西军进陕及康义诚降待录，全年未完成。')
for key,n,note in [('wang_sitong_death_accounts',13,'主、旧本传说王醉时不待报擅杀，醒后怒刘嗟惜；新传直接从珂乃杀。旧帝纪二十三日灵口诛、旧本传二十二昭应问答与主分日分地并列，杀日主未独干支。'),('hongshi_zongshi_word',12,'主初段宗史疑字原字保，不由同姓或电子字形建立宗兄血亲；933讨秦已有记录不重建同一事件。'),('chongji_youcheng_deaths',11,'楚宋州拷索杀重吉与旧前拘幽不同；尼惠明沿李幼澄同女，本句不明楚亲杀尼，也不把后举哀日当死亡日。'),('nanyi_haoxu_comparison',13,'新王思同传使推官郝诩被拘，与卷279第5段主赧诩同使者案形成疑字对照；先不新造郝重复人物，保主字待纸本及同书异版校核。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=934,current_volumes=[278,279],current_batch=rel,next_paragraph=r[13]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=13,volume_total_paragraphs=77,year_completed_paragraphs=25,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=934,next_paragraph=r[13]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=13)]))
bd['note']='934年本卷原6—82行77正文段；前13段原6—18行公开核验，原19行第14段西军进陕及康义诚降仍待录。全年跨卷278的12段和279的77段共89正文，当前25/89，卷与全年均未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n原6—82行77正文段，前13已发布并独立匿名核验；全年跨卷278的12段及本卷77段，当前25/89。下一段zztj-v279-y0934-p014（原19行），卷与全年未完成。\n\n凤翔军变、东进和朝廷赏军、子女被杀及两将处决按动作分录；意图、言辞、赏诺与完成区分。王思同遇害的主旧新责任与日期异说并列，姓名疑字保回查。\n')
print(dict(year=934,completed=25,total=89,next_paragraph=r[13]['id'],year_complete=False))
