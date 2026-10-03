# -*- coding: utf-8 -*-
"""Advance the chronological cursor only after the second batch is public."""
import hashlib
import json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
audit=read(P/'readback-audit.json');b=read(P/'content-batch.json')
assert audit['verified'] and audit['batch_sha256']==hashlib.sha256((P/'content-batch.json').read_bytes()).hexdigest()
ledger=read(P.parent/'paragraphs.json');other=read(ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/paragraphs.json')
assert len(ledger)==43 and len(other)==67
assert all(r['status']=='published_verified' for r in ledger[:24])
assert all(r['status']=='pending' for r in ledger[24:]+other)
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (ledger[12]['id'],ledger[24]['id'])
progress['active_cursor'].update(volume=274,year=926,last_reviewed_paragraph=ledger[23]['id'],last_published_paragraph=ledger[23]['id'],next_paragraph=ledger[24]['id'],next_paragraph_opening=ledger[24]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[],note='926年共110正文段；卷274第1—24段两批连续公开并匿名读回。卷274余19段、卷275全67段待处理，全年未完成。')
for key,n,note in [
 ('wangwen-date',22,'王温乱主甲辰夜、旧本纪甲午夜不同，主擒斩与旧磔本军门不同，分别留存待纸本。郭称帝未来坑军为其传言，不当真实帝诏。'),
 ('monitor-name',18,'主李延安按旧康传同职同队李廷安匹配，底本原名保留；主七千步骑与旧七千骑为兵种异说。'),
 ('adoptive-ties',22,'新伶官传称郭从谦因同姓拜郭崇韬为叔，非血缘；李存乂是其养父，未作生父。亲军建制与得胜战功追叙未强926。'),
 ('chengdu-command-claim',16,'康延孝奉诏代孟为其檄称，非真任官；康与焦武将及我为忧惧推断，未当朝廷已颁诛康令。桔柏津主遣人断、旧密报断桥令分别。'),
 ('yedu-glyphs',21,'主胃其众疑谓、勿遣噍类疑遗，原字不改；赦免承诺不等已赦，帝勿留活口为命令非既成屠杀。第24段戊申先于丁未叙次保留。')]:
 full='926-v274-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=ledger[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=274,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=ledger[24]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
parts=[];covered=[];totals={'events':0,'claims':0}
for part in sorted(P.parent.glob('part-*')):
 data=read(part/'content-batch.json');pub=read(part/'publication.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 assert pub['verified'] and pub['batch_sha256']==sha
 proof=read(part/'readback-audit.json');assert proof['verified'] and proof['batch_sha256']==sha
 covered+=read(part/'coverage.json')['paragraphs']
 parts.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
 for k in totals:totals[k]+=len(data[k])
assert covered==[r['id'] for r in ledger[:24]]
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=274,year=926,completed_paragraphs=24,volume_total_paragraphs=43,year_completed_paragraphs=24,year_total_paragraphs=110,continuous_prefix_verified=True,volume_complete=False,year_complete=False,next_paragraph=ledger[24]['id'],batches=parts,batch_totals=totals))
(P/'README.md').write_text('# 《资治通鉴》卷274 · 926年 · part-02\n\n连续第13—24段（原文件50—61行）已发布：31事件、62参与、174引用；新增8人及李存乂为郭从谦养父的1条关系。补证来自旧史卷34、74及新史卷37、44。\n\n鄴乱后招抚与攻城、康延孝返蜀、任圜追讨、郭从谦与亲军危机背景、王衍止长安及皇弟赴镇按主书连续顺序整理。康奉诏代孟为檄说，元行钦必赦为其承诺，皇帝攻破后勿留活口为命令，各自不混为既成事实。\n\n王温主甲辰与旧甲午、主斩与旧磔分别留存；主李延安据旧同职同队李廷安核为同人，原字不改；主七千步骑与旧七千骑不同。郭门高是优名，认叔非血亲，养父关系不作生父；得胜战功及亲军建制追叙未强定926。\n\n全部公开ID和出处ID/固定URL经匿名读回验证，见publication.json与readback-audit.json。下一段zztj-v274-y0926-p025，926全年未完成。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷274 · 926年\n\n本卷43正文段（原文件38—80行），第1—24段两批连续发布并匿名读回，余19段待录。\n\n926年还包含卷275的67段，共110段，目前完成24段。下一段zztj-v274-y0926-p025。\n')
print(dict(completed=24,total=110,next_paragraph=ledger[24]['id'],year_complete=False))
