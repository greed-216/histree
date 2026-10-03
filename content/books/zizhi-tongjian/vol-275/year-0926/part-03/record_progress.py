# -*- coding: utf-8 -*-
"""Record a verified continuous 67-paragraph prefix of year 926."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
previous=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926'
a=read(previous/'paragraphs.json');b=read(P.parent/'paragraphs.json')
assert len(a)==43 and len(b)==67
assert all(r['status']=='published_verified' for r in a+b[:24])
assert all(r['status']=='pending' for r in b[24:])
parts=[];covered=[];totals={'events':0,'claims':0}
for directory,rows,first,last in [(previous,a,38,80),(P.parent,b,6,72)]:
 raw=ROOT/read(directory/'boundaries.json')['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==read(directory/'boundaries.json')['source_sha256']
 assert [r['source_line'] for r in rows]==list(range(first,last+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rows)
 for part in sorted(directory.glob('part-*')):
  data=read(part/'content-batch.json');pub=read(part/'publication.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
  assert pub['verified'] and pub['batch_sha256']==sha
  proof=read(part/'readback-audit.json');assert proof['verified'] and proof['batch_sha256']==sha
  ids=read(part/'coverage.json')['paragraphs'];covered+=ids
  assert {k for r in rows if r['id'] in ids for k in r['event_keys']}=={r['key'] for r in data['events']}
  parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
  for k in totals:totals[k]+=len(data[k])
assert len(parts)==8 and covered==[r['id'] for r in a+b[:24]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[12]['id'],b[24]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=b[23]['id'],last_published_paragraph=b[23]['id'],next_paragraph=b[24]['id'],next_paragraph_opening=b[24]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段及卷275第1—24段共67段八批连续发布并匿名回查。卷275余43段待录，全年未完成。')
for key,n,note in [
 ('accession-and-coffin-ritual',14,'同家、视犹子及嗣子礼不直接建收养或血缘，霍孔改号提议未采；甲午监国与丙午柩前即位分事。'),
 ('zhangxian-execution-critique',16,'主庚戌赐死、旧是月失守赐死及欧阳修不然史论并列，委城为弹劾，不把史论改写成确定替代死因。'),
 ('returning-army-numbers',17,'主与旧二万六千、新魏王传二万；主未具确日、旧壬子入见，各引不静默统一。'),
 ('finance-summary-and-restored-names',19,'任圜期年政绩与安忌为任职期间概述，确年未定；六将复名，杜晏球复王姓用同一稳定key；选入、剌吏电子疑字和郑玨/珏待纸本校。'),
 ('audience-glyph-and-eunuchs',20,'主丁已/旧丁巳并列；主诏诛宦官与旧都亭驿已执行分证，不把日序误当全部同日。'),
 ('congwen-and-provincial-offices',21,'李从温侄子方向从温至嗣源，不推叔伯长幼；赵主义成/旧滑州、符主建雄/旧晋州各存，赵军情为辞与请幸未实分开。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=926,completed_paragraphs=24,volume_total_paragraphs=67,year_completed_paragraphs=67,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[24]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=b[24]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
(P/'README.md').write_text('''# 《资治通鉴》卷275 · 926年 · part-03

连续第13—24段（原文件18—29行）已发布：30事件、51参与、168引用；新增苌从简、米君立、李从温3个人物，以及李从温是李嗣源侄子1条关系。

主线包含孔循任枢密使、保唐议礼与李嗣源丙午正式即位及受册、禁献鹰犬奇玩、张宪赐死、任圜返军、天成改元与初政、郑珏任圜任相、六将复名、五日内殿起居、北都诛宦、安金全赵在礼符彦超方镇任职。补证来自《旧五代史》卷35、36及《新五代史》卷6、14、15、28、46、47，14个独立来源记录及28条补充书证。

主旧返军二万六千与新二万不统一；主张宪庚戌赐死与旧是月、欧阳修怀疑旧记载史论分别保留。任圜期年政绩与安忌为任职期间概述，不记作五月朔日全部完成。朝政令与执行结果分证，诏诛宦官的实杀地点都亭驿据旧明确补充。丁已/旧丁巳及选入、剌吏疑字原文不改。杜晏球本段复王姓仍使用既有主体，杜养家无名不补养父母；从温侄子至嗣源方向，不猜叔伯长幼。

快照先归档于固定GitHub提交，public ID、每条引用source ID和URL、快照SHA均已匿名回查，见publication.json和readback-audit.json。926年连续完成67/110段，下一段zztj-v275-y0926-p025，全年未完成；目标仍是录入至936年后唐灭亡。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷275 · 926年

本卷67正文段（原文件6—72行），第1—24段三批已发布并匿名回查，余43段待录；连续前缀、源行、哈希及逐批回查证明见progress-audit.json。

926年含卷274的43段与本卷67段，合计110段，当前完成67段，全年未完成。下一段zztj-v275-y0926-p025。
''')
print(dict(completed=67,total=110,next_paragraph=b[24]['id'],volume_complete=False,year_complete=False))
