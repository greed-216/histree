# -*- coding: utf-8 -*-
"""Verify consecutive first twenty paragraphs; advance year-932 prefix to 41/49."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists());YEAR=P.parent
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(rows)==28 and all(x['status']=='published_verified' for x in rows[:20]) and all(x['status']=='pending' and not x['event_keys'] for x in rows[20:])
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256'];assert [x['source_line'] for x in rows]==list(range(6,34));assert all(x['text']==lines[x['source_line']-1] for x in rows)
oldyear=YEAR.parent.parent/'vol-277/year-0932';oa=read(oldyear/'progress-audit.json');orows=read(oldyear/'paragraphs.json')
assert oa['volume_year_complete'] and oa['completed_paragraphs']==21 and oa['year_total_paragraphs']==49
assert all(x['status']=='published_verified' for x in orows[:21]) and all(x['status']=='excluded_non_body_verified' and not x['text'].strip() and not x['event_keys'] for x in orows[21:])
for item in oa['batches']:
 path=ROOT/item['batch'];sha=hashlib.sha256((path/'content-batch.json').read_bytes()).hexdigest();assert sha==item['batch_sha256']
 for f in ['publication.json','readback-audit.json']:
  a=read(path/f);assert a['verified'] and a['batch_sha256']==sha
proof=[]
for path,selection in [(YEAR/'part-01',rows[:10]),(P,rows[10:20])]:
 b=read(path/'content-batch.json');c=read(path/'coverage.json');sha=hashlib.sha256((path/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  d=read(path/f);assert d['verified'] and d['batch_sha256']==sha
 assert c['paragraphs']==[x['id'] for x in selection] and {k for x in selection for k in x['event_keys']}=={x['key'] for x in b['events']}
 proof.append(dict(batch=str(path.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[10]['id'],rows[20]['id']]
progress['active_cursor'].update(volume=278,year=932,last_reviewed_paragraph=rows[19]['id'],last_published_paragraph=rows[19]['id'],next_paragraph=rows[20]['id'],next_paragraph_opening=rows[20]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==932)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[277,278],completed_volumes=[277],note='卷277本年21正文完整公开核验，2空行结构排除；卷278前20段已核验，余8待录。全年49正文，当前41/49；未标全卷或全年完成。')
for n,key in [(12,'dejun_city_chronology'),(15,'li_cungui_second_mission_glyph'),(18,'li_jinquan_military_title'),(19,'congrong_family_and_initial_orders'),(20,'meng_hu_name_glyph')]:
 full='932-v278-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=rows[n-1]['review']))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=278,current_year=932,current_volumes=[277,278],current_batch=rel,next_paragraph=rows[20]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=932,completed_paragraphs=20,volume_total_paragraphs=28,year_completed_paragraphs=41,year_total_paragraphs=49,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=rows[20]['id'],batches=proof,previous_volume=dict(volume=277,body_paragraphs=21,completed_paragraphs=21,excluded_non_body_verified=2,audit=str((oldyear/'progress-audit.json').relative_to(ROOT)))))
bd['note']='932年卷278原6—33行28正文段，前20已公开匿名核验，余8待录；卷277同年21正文全核，2空行核排。全年49正文，当前41/49，全年未完成。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷278 · 932年 · part-02\n\n连续第11—20段、原16—25行：23人物（4新增）、29事件、58参与、3关系（1父亲复用、2新增）、160事实引用、11出处（8新增3复用）。补证《旧五代史》《新五代史》。\n\n吴扩城、幽州边堡、楚授官、孟子摄职、帝答两川任免及兵家属、秦诗幕及康疏、秦王宫廷争疑、河东出镇初议、孟冯任职逐动作分录。\n\n金陵周围二十里为城周不是面积。良乡潞县追叙年份null，三河本次932且九月奏毕明确；主旧阎沟新盐沟及方位各留，不借旧传运河二百里回写六月奏数。旧夹注辽史和未来936事不新增。\n\n孟仁赞沿孟昶及927父亲关系，摄与新概衔分。复遣李存瓘疑字按同供奉任务及前孟甥存瑰旧瑰识；此次祭赠及任免答与此前草请阶段分，差罢仍须奏，五将正授旧续处置未提前。拒送家属与不复征兵分别保留。\n\n秦诗幕素行null，旧紫府集名补而不造未见千余诗。康疏五六条政治论据不当实际殷晋灾异。秦安内臣宗室关系追叙与意见明确归属，不把安复生或风险当已被杀；王淑沿王德，不混曹徐。永宁公主限石妻主体，妻子与父亲有向，旧石氏为婚家称，不猜生母或同父异母手足长幼。\n\n河东初命、受诏再辞、朱暂知代康入阙与后11月终任、12月正朱任分。孟秸后鹄与旧同日孟鵠三司出许州识已有孟鹄，不因OCR字新建；刀笔同乡引擢概述null。前影义军名疑字不静改、不造影义地理实体。展示简体，TXT逐字不变。\n\n匿名公开UUID、出处关联及SHA回查通过。932年41/49，下一段zztj-v278-y0932-p021；目标继续至936后唐灭亡。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 932年\n\n原6—33行28正文段；part-01前10段及part-02第11—20段已公开匿名核验，余8待录。原34分隔、35下一年标题排除见boundaries。\n\n卷277同年21正文已核且2空行核排，全年49正文，目前41/49，未完成；下一段zztj-v278-y0932-p021。\n')
f=oldyear/'README.md';s=f.read_text();s=s.replace('前10段已公开核验，余18待录','前20段已公开核验，余8待录').replace('目前31/49','目前41/49').replace('zztj-v278-y0932-p011','zztj-v278-y0932-p021');f.write_text(s)
print(dict(year=932,completed=41,total=49,next_paragraph=rows[20]['id'],year_complete=False))
