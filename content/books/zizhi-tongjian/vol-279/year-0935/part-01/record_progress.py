# -*- coding: utf-8 -*-
"""Record eleven verified paragraphs without marking the remaining year complete."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==37 and [x['source_line'] for x in r]==list(range(85,122)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:11]) and all(x['status']=='pending' and not x['event_keys'] for x in r[11:])
b=read(P/'content-batch.json');sha=hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
for f in ['publication.json','readback-audit.json']:
 a=read(P/f);assert a['verified'] and a['batch_sha256']==sha
assert read(P/'coverage.json')['paragraphs']==[x['id'] for x in r[:11]]
assert {k for x in r[:11] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent/'year-0934';prior=read(previous/'paragraphs.json');annual=read(previous/'progress-audit.json')
assert len(prior)==77 and all(x['status']=='published_verified' for x in prior) and annual['year_complete'] and annual['year_completed_paragraphs']==89
for proof in annual['batches']:
 part=ROOT/proof['batch'];h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert h==proof['batch_sha256']
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[0]['id'],r[11]['id']]
pr['active_cursor'].update(volume=279,year=935,last_reviewed_paragraph=r[10]['id'],last_published_paragraph=r[10]['id'],next_paragraph=r[11]['id'],next_paragraph_opening=r[11]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==935)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[279],completed_volumes=[],note='卷279本年37正文段，原85—95行前11段连续公开并独立匿名核验。闽改元赦、蜀赦、唐任官、夏州继任、蜀李太后唐魏追尊、闽陈后、三月赵李安任官和吴越陈母赠号已录。原96行第12段史在德言事待录，全年11/37未完成。')
for key,num,note in [('yiyin_sibling_order',4,'主称彝殷为彝超兄，旧三月称兄彝超、新及宋称弟；保各原句，图谱暂对称兄弟，不造确定兄长方向。彝兴后避宋讳仅补检索别名，未与阿啰王擅合。'),('min_early_wife_names',7,'主两娶刘氏，新称前妻早卒、继室金氏，婚次与姓不同，不合并两刘或擅校金为刘，原文保留纸本待核。'),('min_chen_kin_office_dates',7,'陈后族人殿使在初句所附背景，起任年未明，事件年null；具体亲等未载，只存族亲。'),('qian_maternal_kin_scope',10,'主未尝迁官授以重任的否定范围按并列官职动作理解，底本逗号不误译为不迁官却授重任。长期待母族行为起年未明，不硬填935。'),('wei_title_vs_investiture',6,'旧己丑上尊谥获准并请择日册命，主追尊同日；正式册命典礼日尚未在本条具载，不将上谥、批准、执行合一。')]:
 full='935-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[num-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=935,current_volumes=[279],current_batch=rel,next_paragraph=r[11]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=935,completed_paragraphs=11,volume_total_paragraphs=37,year_completed_paragraphs=11,year_total_paragraphs=37,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=935,next_paragraph=r[11]['id'],batches=[dict(batch=rel,batch_sha256=sha,anonymous_readback_verified=True)],year_scope=[dict(volume=279,body_paragraphs=37,published=11)]))
bd['note']='935年原85—121行37正文，前11段原85—95行公开核验，原96行第12段史在德言事待录。包括臣光曰评论段，不跳段；全年未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 935年\n\n原85—121行37正文段，前11段已连续发布并独立匿名核验，全年11/37未完成。下一段 zztj-v279-y0935-p012（原96行），史在德上书言事。\n\n李彝殷兄弟长幼、闽前妻姓、陈后族人任职追叙、吴越母族官任措辞分别保原文及校核说明。原115行臣光曰属于作者评论，仍在待录账本；原124行后晋纪为结构标题，后接卷280的936年。\n')
print(dict(year=935,completed=11,total=37,next_paragraph=r[11]['id'],year_complete=False))
