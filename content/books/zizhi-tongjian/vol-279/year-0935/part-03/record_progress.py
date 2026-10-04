# -*- coding: utf-8 -*-
"""Advance only the independently verified continuous published prefix."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==37 and [x['source_line'] for x in r]==list(range(85,122)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] for x in r)
assert all(x['status']=='published_verified' for x in r[:28]) and all(x['status']=='pending' and not x['event_keys'] for x in r[28:])
b=read(P/'content-batch.json');proofs=[]
for part,start,end in [(YEAR/'part-01',0,11),(YEAR/'part-02',11,20),(P,20,28)]:
 h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
 assert read(part/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
assert {k for x in r[20:28] for k in x['event_keys']}=={x['key'] for x in b['events']}
previous=YEAR.parent/'year-0934';prior=read(previous/'paragraphs.json');annual=read(previous/'progress-audit.json')
assert len(prior)==77 and all(x['status']=='published_verified' for x in prior) and annual['year_complete'] and annual['year_completed_paragraphs']==89
for proof in annual['batches']:
 part=ROOT/proof['batch'];h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest();assert h==proof['batch_sha256']
 for f in ['publication.json','readback-audit.json']:
  a=read(part/f);assert a['verified'] and a['batch_sha256']==h
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[20]['id'],r[28]['id']]
pr['active_cursor'].update(volume=279,year=935,last_reviewed_paragraph=r[27]['id'],last_published_paragraph=r[27]['id'],next_paragraph=r[28]['id'],next_paragraph_opening=r[28]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==935)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[279],completed_volumes=[],note='卷279本年37正文，前28段原85—112行连续公开并独立匿名核验。新增闽李春燕、军政任命、延英奏议、徐知谔、吴改元、枢密弊政和金州守战。第29段十月闽宫变待录，全年28/37未完成。')
for key,num,note in [('chunyan_request_roles',21,'主后白闽主而赐之有省主，新明确鏻与之；规范主体王延钧，原文春鷰与李春燕异体检索，赐宫人不立即当册妃或夫妻。'),('xu_zhie_advice_dates',25,'失务背景起年未载为null；当前责问厚待不强定七月独日。忠武王宠爱不凭此推父子，劝者匿名，知询往事及假设能治不当935实事。'),('shumi_patterns_years',27,'己酉任命与任官期间的常态叙述分；原已疑以保字，贿赂、睡议、专权及将帅怨均史述概括，不硬定全部己酉发生。'),('jinzhou_campaign_stages',28,'旧六月汉阴战、七月奏报与主九月水寨守城是阶段层次不同；崔处讷非陈知隐。以死继之不当马全节本战死亡；诏斩陈为命令，执行未知不填死年。')]:
 full='935-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[num-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=935,current_volumes=[279],current_batch=rel,next_paragraph=r[28]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=935,completed_paragraphs=28,volume_total_paragraphs=37,year_completed_paragraphs=28,year_total_paragraphs=37,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=False,year_complete=False,next_volume=279,next_year=935,next_paragraph=r[28]['id'],batches=proofs,year_scope=[dict(volume=279,body_paragraphs=37,published=28)]))
bd['note']='935年原85—121行37正文，前28段原85—112行公开核验，原113行第29段闽十月宫变待录。包括臣光曰评论段，不跳段；全年未完成。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 935年\n\n原85—121行37正文段，前28段已连续发布并独立匿名核验，全年28/37未完成。下一段 zztj-v279-y0935-p029（原113行），闽十月宫变。\n\n三批包括朝廷任官、吴蜀闽政事、延英奏议、边寇粮运、忻州和金州战事及军政弊政。其他书证保独立出处，简体展示、逐字引文保底本原字。原115行臣光曰仍在待录账本；原124行后晋纪为结构标题，后接卷280的936年。\n')
print(dict(year=935,completed=28,total=37,next_paragraph=r[28]['id'],year_complete=False))
