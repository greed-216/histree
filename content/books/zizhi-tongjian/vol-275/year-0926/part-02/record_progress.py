# -*- coding: utf-8 -*-
"""Record a continuous 55-paragraph prefix across volumes 274 and 275."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
previous=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926'
a=read(previous/'paragraphs.json');b=read(P.parent/'paragraphs.json')
assert len(a)==43 and len(b)==67
assert all(r['status']=='published_verified' for r in a+b[:12])
assert all(r['status']=='pending' for r in b[12:])
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
assert len(parts)==7 and covered==[r['id'] for r in a+b[:12]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[6]['id'],b[12]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=b[11]['id'],last_published_paragraph=b[11]['id'],next_paragraph=b[12]['id'],next_paragraph_opening=b[12]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段及卷275第1—12段共55段七批连续发布并匿名回查。卷275余55段待录，全年未完成。')
for key,n,note in [
 ('princely-deaths-and-missing',7,'主安霍秘密杀二王与监国后月余才知分时；刘后主监国遣杀、新入立后遣赐死分阶段异说。四幼子与存礼不知所终不填死年，四幼子生母未载不推刘后。'),
 ('sunguangxian-entry',8,'主梁震荐于高季昌掌书记与宋高从诲署从事的受荐者官称不同，时间未具，不合成926同次任命；攻楚为欲而止。'),
 ('dates-and-offices',9,'元主戊戌斩、旧财政后是日、新乙未后叙次不同。石陕主无确日旧己亥；李从珂主河中/旧河南府异说保留。孔三司判不提前成专职三司使，诸道诛宦只记教令不称全部已执行。'),
 ('shaohong-and-lichong',11,'主李强宏据新宣徽马绍宏曾赐李姓、前既有李绍宏同职校同人，只有请复无准文。华州李氵中合字冲独立于李再丰之子及温韬李绍冲；温段捕而欲杀后辛丑释归不提前后年死亡。'),
 ('shiy anrong'.replace(' ',''),12,'史彦镕与已存史敬镕、旧史敬熔同华州职但未得明说异名及同事件补证，相关事件保留主姓名，暂不新建或合主体，待纸本及同事校证。'),
 ('jiji-date-and-return',12,'主魏王死亡本段无确日，新明宗纪壬子薨置正式即位之后，不凭主段序定辛丑前死；李环奉魏王命缢、任代军与石慰抚分行动。张篯/籛繁简一人，不并张筠。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=926,completed_paragraphs=12,volume_total_paragraphs=67,year_completed_paragraphs=55,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[12]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=b[12]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
(P/'README.md').write_text('''# 《资治通鉴》卷275 · 926年 · part-02

连续第7—12段（原文件12—17行）已发布：37事件、83参与、237引用；新增9个人物及5条关系（庄宗与四幼子的父亲边，张延朗、安重诲的姻亲边）。

主线包含枢密任命、二王密杀及事后责安、刘后与李存渥奔晋阳及两王遇害、幼子不知所终、孙光宪荐任及谏止攻楚、元行钦实斩、陕州及河中留后、归田及姓氏、孔谦实斩与财政监军教令、魏王转东及自命李环缢杀、任圜代军、李冲华州擅杀、温段下狱后获释。其他史书补证来自《旧五代史》卷35、51、《新五代史》卷6、14、25、26、38、40及《宋史》卷483。

四幼子与存礼“不知所终”不填死亡年；父子名单依两史核，不推四人之母为刘后。安霍私杀二王、监国月余后责安与刘后被监国遣杀分事，不模糊责任。主元戊戌/两史叙次、李从珂河中/旧河南府、魏王无日/新壬子薨分别引证；孙主高季昌荐掌书/宋高从诲署从事不合成同次任命。宦官尽杀只记命令，未假定各地执行完成。

李强宏据同宣徽李赐姓马校李绍宏；李氵中展示李冲（华州都监），独立于李再丰子及温韬赐名李绍冲。篯/籛为繁简同人，张筠另人。史彦镕与史敬镕异名未获确证，事件保留主名，暂不新建或合人物；待考项登记于content/yearly-progress.json。温段被捕欲杀与辛丑释放分开，不提前后年死。

公开ID、引用source ID、快照哈希和固定GitHub URL已逐条匿名回查，见publication.json与readback-audit.json。926年连续完成55/110段，下一段zztj-v275-y0926-p013，本卷及全年未完成。
''')
(P.parent/'README.md').write_text('''# 《资治通鉴》卷275 · 926年

本卷67正文段（原文件6—72行），第1—12段两批已发布并匿名回查，余55段待录；连续前缀、源行、哈希及逐批回查证明见progress-audit.json。

926年含卷274的43段与本卷67段，合计110段，当前完成55段，全年未完成。下一段zztj-v275-y0926-p013。
''')
print(dict(completed=55,total=110,next_paragraph=b[12]['id'],volume_complete=False,year_complete=False))
