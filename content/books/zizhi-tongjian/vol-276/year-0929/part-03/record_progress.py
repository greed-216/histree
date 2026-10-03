# -*- coding: utf-8 -*-
"""Advance only the exact publicly verified 929 continuous prefix."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==36
assert all(r['status']=='published_verified' for r in rows[:22])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[22:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(87,123))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
prev=read(P.parent.parent/'year-0928/year-audit.json');assert prev['verified'] and prev['year_complete'] and prev['body_paragraphs']==52
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:22]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[16]['id'],rows[22]['id']]
progress['active_cursor'].update(volume=276,year=929,last_reviewed_paragraph=rows[21]['id'],last_published_paragraph=rows[21]['id'],next_paragraph=rows[22]['id'],next_paragraph_opening=rows[22]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==929)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='929年卷276共36正文段，首22段已连续发布并逐条匿名回查，余14段待处理；全年未完成。')
for key,n,note in [
 ('sichuan_money_and_envoys',17,'主请求西百万东50万与实献西50东10万分，军用不足为其说法，今疑令原留。新物50万口径不同、祀天概叙不定本年已郊祭。李归言不法/新必反是报告非已反；彦珣未几使拘从奔还年null，不混沙彦珣，拘从不是李本人，退事舍人原衔待核。'),
 ('gaoconghui_return_steps',18,'高叛劝父和袭位近唐远吴评前事年null，借楚谢罪、致安函、五月丙申保奏帝许不同正式授官。六月庚申表与旧丙辰罪表银3000两未能确定同表或另奏，年月异说留，不转为五月信金额；主旧七月甲申授与新930正月差，不造确定二次任。'),
 ('yedu_and_wuchang_offices',20,'主复魏州停留守皇城，旧魏府及宫去鸱尾改衙署补，不等全毁都城。徐留李亲兵二千非全部武昌军；李彦忠推荐非获任，柴再用才实际获任；徐之刘三世濠兄亲是其话，不猜父祖。'),
 ('lijian_identity_and_inlaws',22,'本次复用919已录武昌李简，不混王建将李；更早杨行密将限定实体疑与当前同人重叠待独立修订，不造第三人。徐知询是李简女婿，李简是李彦忠父亲，方向明确；妻族不推李彦忠与徐妻长幼，无名妻不造。')
]:
 full='929-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=929,current_volumes=[276],current_batch=rel,next_paragraph=rows[22]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=929,completed_paragraphs=22,volume_total_paragraphs=36,year_completed_paragraphs=22,year_total_paragraphs=36,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[22]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 929年 · part-03\n\n连续第17—22段（原文件103—108行）：28事件、39人物参与、121事实引用；3新增人物、11复用人物；2条新增关系；7来源（3新增、4复用），补证《旧五代史》《新五代史》。\n\n覆盖两川助郊祀钱及董璋与李仁矩冲突、李彦珣使行，高从诲归唐申请与正式授职，五月云州侵扰、邺都复魏制，以及李简卒与吴武昌任命之争。新增李彦珣、李彦忠、刘崇俊。\n\n请求钱额与实际献额分，军用不足为两川陈述；今疑令留原，新贡助物口径及祀天概叙不同，不强本年已完成郊祭。董威胁引用旧李严案不新造李严死亡，李回报必反为预测；彦珣未几使拘从奔还年null，退事舍人原衔待核，从者被拘非李本人被拘。\n\n高劝父及近唐远吴评为前事年null，借马殷、安元信保奏帝许，与六月自行上章、七月正式唐授分。旧丙辰表银三千两与主庚申表保留，未定同一或不同表；新长兴元年正月授与主旧929七月不同，不能另造已确定二次任。吴928任与唐929任不同政权。魏州/魏府称法与去鸱尾改衙署补保留，不毁城。\n\n李简沿919武昌同人，不混王建军同名；更早杨行密将限定实体疑重复留待独立修订。李请返江都与采石卒分。徐留二千亲兵不是全部武昌军，荐李彦忠不是任命获准，徐知诰沿李昪、柴再用实际获任。徐称刘三世濠州兄亲仅话中说法，不猜祖父父亲和具体亲缘，比较对象不当在场。\n\n徐知询是李简的女婿，李简是李彦忠的父亲，两边方向明确，不造无名妻或妻族的具体长幼。公开UUID、逐字摘录、来源SHA、source关联及固定GitHub链接已核验；展示简体，原文保留底本，纸本异文待核。\n\n929年完成22/36段，下一段zztj-v276-y0929-p023高郁案；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 929年\n\n原文件87—122行，共36段正文；首22段三批已连续发布并匿名回查，余14段待处理。年界和卷末已核，下一卷277从930年开始。\n\n下一段zztj-v276-y0929-p023；连续覆盖和验证证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=22,total=36,next_paragraph=rows[22]['id'],year_complete=False))
