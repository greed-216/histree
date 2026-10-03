# -*- coding: utf-8 -*-
"""Record a verified continuous 91-paragraph prefix of year 926."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
previous=ROOT/'content/books/zizhi-tongjian/vol-274/year-0926'
a=read(previous/'paragraphs.json');b=read(P.parent/'paragraphs.json')
assert len(a)==43 and len(b)==67
assert all(r['status']=='published_verified' for r in a+b[:48])
assert all(r['status']=='pending' for r in b[48:])
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
assert len(parts)==10 and covered==[r['id'] for r in a+b[:48]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in (b[36]['id'],b[48]['id'])
progress['active_cursor'].update(volume=275,year=926,last_reviewed_paragraph=b[47]['id'],last_published_paragraph=b[47]['id'],next_paragraph=b[48]['id'],next_paragraph_opening=b[48]['text'],batch=rel,status='in_progress')
year=next(x for x in progress['year_coverage'] if x['year']==926)
if rel not in year['batches']:year['batches'].append(rel)
year.update(status='in_progress',completed_volumes=[274],note='926年共110正文段；卷274全部43段及卷275第1—48段共91段十批连续发布并匿名回查。卷275余19段待录，全年未完成。')
for key,n,note in [
 ('hua-punishment-and-totals',37,'主全营族诛与助乱将校百人、旧数百军士各口径分证，家属人口未名不合死亡总数；于可洪此处实斩不提前前批。'),
 ('dongdan-and-yaokun',39,'渤海攻取与建东丹属年内追叙，辽正月拔扶余二月改国及倍册号；突欲托云倍校同人，外交吾儿非庄宗亲子。主索河北三州并囚使与旧只索幽州各存未造割地。'),
 ('burial-and-zhangguo-glyphs',40,'主庄宗葬丙子/旧乙亥，主彰国/旧彰德并存；刘殷肇谋乱为王奏，已擒不推已处死。'),
 ('chancellor-accusations-and-rewards',43,'主新明确萧诬奏，官方制书罪状作为指控不抹去诬；阿庚疑谀原字留，主溆/旧漵/新敍州、赏金帛/旧衣段银/新帛粟麦各存不合总量。王傪不以旧王参字句强并。'),
 ('abaoji-shulu-and-coffin',44,'阿保机辛巳卒与旧七月27并引，辽异象不当实测；述后诱杀只未名酋长不推妻们也死。主丁亥同行/辽甲午西还及倍乙巳继至保留。'),
 ('anduanshaojun-identity',48,'主新皆少幼子安端少君，与辽同名宗室安端关系尚未校清，保全称事件不建或并人物、不建母子，不猜李胡。')]:
 full='926-v275-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=b[n-1]['id'],required_action=note))
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=275,year=926,completed_paragraphs=48,volume_total_paragraphs=67,year_completed_paragraphs=91,year_total_paragraphs=110,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=b[48]['id'],batches=parts,batch_totals=totals))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=275,current_year=926,current_volumes=[274,275],current_batch=rel,next_paragraph=b[48]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)

(P/'README.md').write_text("""# 《资治通鉴》卷275 · 926年 · part-05

连续第37—48段（原文件42—53行）已发布：31事件、61参与、173事实引用；新增耶律倍、耶律德光、姚坤、刘殷肇、萧希甫、王傪6个人物，4条明确亲属关系；14个独立来源记录，补证来自《旧五代史》《新五代史》《辽史》。

主线包括滑州乱兵处决、百官起居转对、契丹建东丹与册立两子、姚坤告哀及外交交涉、庄宗归葬、刘殷肇被擒、应州置军、豆卢革韦说贬谪及萧希甫诬奏、阿保机去世与述律后杀酋长、孟知祥扩军、日食及契丹奉丧西返。

渤海攻取和册封属年内追叙，不全部定为七月。外交言辞、领土索求和拟议联盟分别记录，不视作实际割让；外交称庄宗为吾儿不建亲子关系。阿保机复用已应用同人合并修订的canonical_key person_阿保机，不恢复隐藏的重复主体。刘殷肇谋乱保留为王建立奏称，已擒不推已处死。萧希甫所奏田地、杀人、邻井等明确为诬告，制书罪状保留指控属性。

葬日丙子/乙亥、军名彰国/彰德、韦说贬地溆/漵/敍州、萧希甫赏赐种类数量和姚坤受囚交涉异说分来源保留。死亡数字不合并不同阶段、单位及家属未知数。安端少君身份待考，暂不创建人物、不并同名宗室、不推母子关系；主丁亥同返与辽后甲午西还、倍乙巳继至的行程差异保留。

原文快照及逐字摘录保留底本繁简字形，展示与实体匹配使用规范简体。来源固定提交、公开ID、引用source ID和URL、快照SHA已逐条匿名回查，见publication.json及readback-audit.json。926年连续完成91/110段，下一段zztj-v275-y0926-p049，全年未完成；目标仍是录至936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷275 · 926年

本卷67正文段（原文件6—72行），第1—48段五批已发布并匿名回查，余19段待录；连续前缀、源行、哈希及逐批回查证明见progress-audit.json。

926年含卷274的43段与本卷67段，合计110段，当前完成91段，全年未完成。下一段zztj-v275-y0926-p049。
""")
print(dict(completed=91,total=110,next_paragraph=b[48]['id'],volume_complete=False,year_complete=False))
