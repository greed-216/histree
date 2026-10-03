# -*- coding: utf-8 -*-
"""Advance the consecutive 928 prefix only after exact public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
rows=read(P.parent/'paragraphs.json');assert len(rows)==52
assert all(r['status']=='published_verified' for r in rows[:12])
assert all(r['status']=='pending' and not r['event_keys'] for r in rows[12:])
bd=read(P.parent/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert [r['source_line'] for r in rows]==list(range(33,85))
assert all(r['text']==lines[r['source_line']-1] for r in rows)
proofs=[];covered=[]
for part in [P.parent/'part-01',P.parent/'part-02',P]:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  proof=read(part/f);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows[:12]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json');assert progress['active_cursor']['next_paragraph'] in [rows[10]['id'],rows[12]['id']]
progress['active_cursor'].update(volume=276,year=928,last_reviewed_paragraph=rows[11]['id'],last_published_paragraph=rows[11]['id'],next_paragraph=rows[12]['id'],next_paragraph_opening=rows[12]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==928)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[],note='928年卷276共52正文段，首12段已连续发布并逐条匿名回查，余40段待处理；全年未完成。')
for key,n,note in [
 ('jingnan_peace_and_wanghuan',11,'新楚前明年正月是贡使被执时间，攻军未独给日，不强927攻；楚王环沿914同军主体，区别后蜀同名；俘斩合数非全亡、进逼未攻克；归史与和止分别据源，王泛述行事null。'),
 ('han_fengzhou_dayou_outcomes',11,'新四年承白龙，上下文单独快照；神弩/神弩军三千称谓保留，不硬当弩具等兵数；主败退解围/新尽杀叙法并列，未录全军死亡数；占筮仅史载非神示已证。'),
 ('congrong_taiyuan_timing',12,'主928四月河东北都具体官衔与旧927十二月庚辰移镇太原时间层次不同并列，未改主或强同日同次；其他四月月头任官未具日不强戊寅。'),
 ('wu_wangyanzhang_and_daorenji',12,'吴静江统军王彦章独立限定，区别梁将；楚潜伏角子湖、王三百舰杨浦截路与詹三百轻舟后袭是不同部队，舟数非人数。吴将会荆南只计划不虚构已到援将；主丁亥到达战与旧同日复州奏报分层，捕苗王非死不提前放还。')
]:
 full='928-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=928,current_volumes=[276],current_batch=rel,next_paragraph=rows[12]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=928,completed_paragraphs=12,volume_total_paragraphs=52,year_completed_paragraphs=12,year_total_paragraphs=52,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[12]['id'],batches=proofs))
(P/'README.md').write_text('# 《资治通鉴》卷276 · 928年 · part-03\n\n连续第11—12段（原文件43—44行）已发布：35事件、43人物参与、147事实引用；8新增人物、11复用人物；6来源（3新增、3复用），补证《旧五代史》《新五代史》，另存南汉白龙年号上下文。\n\n新增袁诠、马希瞻、苏章、苗璘、王彦章〔吴将〕、詹信、冯赟、杨思权。楚王环沿914楚军主体，区别后蜀同名；吴静江统军王彦章独立限定，区别梁将，避免同名误合并。\n\n楚荆南战分到岳、派军、迎战、夜伏、次晨横击、败与进逼、请和还史、军归责问及王环战略解释。俘斩以千是合计概数，进逼江陵不等攻克荆南。新楚前句明年正月记贡使被执，不直接赋后攻军927正月。王环每战身先、同甘苦、针药治伤与部下话语为行事泛述，年null，不推现代疗效和每役必胜。\n\n南汉封州战分先围及新贺江兵先败、占筮、大赦改元、苏援、铁絙巨轮堤伏、佯败诱追、锁船弩射、楚败退解围、苏团练。新四年承白龙，上下文原文定位独立保留，不把年号上下文本身另造928事件；主神弩三千与新神弩军三千、两索称法补充，不硬当三千弩具等人数。主大败退与新尽杀并列，不录全军阵亡统计，占筮不当神示证实。\n\n四月从荣河东北都具体官衔与旧前927十二月庚辰移太原的纪时层次并列，不改主或强同一次同日。冯太原、杨新平籍贯与官任分开，不虚构生年坐标。戊寅石邺天雄加使相、范成德与旧转运、新罢枢密同事；丙戌安兼河南并非三月拟外调兑现，从厚宣武仍判并非六军初授。\n\n吴万人至君山、楚许千舰迎御、许战前判断、角子湖伏与王三百舰杨浦截归、吴迟明荆江口拟会荆南、丁亥道人、詹三百轻舟绕后许前夹、败擒苗王归分事。吴将会荆南是计划，不推援军已到或主将；舟数不是人数，旧丁亥复州奏报不是二将捕获直接明证。被俘非战死，未提前后续放还。\n\n逐字摘录、源行与SHA、公开UUID、source关联和固定GitHub地址已匿名读回；上下文快照SHA也核验。所用主书快照跨尚未录入段落，未将整快照记完成。展示简体、原文保留底本，纸本异文待核。\n\n928年完成12/52段，下一段zztj-v276-y0928-p013；继续至936年后唐灭亡。\n')
(P.parent/'README.md').write_text('# 《资治通鉴》卷276 · 928年\n\n原文件33—84行，共52段正文；首12段三批已发布并匿名回查，余40段待连续处理。前后年界已核，卷277从930年开始。\n\n下一段zztj-v276-y0928-p013；连续前缀和批次证明见progress-audit.json。全年尚未完成。\n')
print(dict(completed=12,total=52,next_paragraph=rows[12]['id'],year_complete=False))
