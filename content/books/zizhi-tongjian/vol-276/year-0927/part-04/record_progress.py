# -*- coding: utf-8 -*-
"""Record consecutive 927 coverage across both volumes after public verification."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
first=ROOT/'content/books/zizhi-tongjian/vol-275/year-0927';rows1=read(first/'paragraphs.json');rows=read(P.parent/'paragraphs.json')
assert len(rows1)==32 and len(rows)==25
assert all(r['status']=='published_verified' for r in rows1+rows[:18])
assert all(r['status']=='pending' for r in rows[18:])
for d,rs,begin,end in [(first,rows1,75,106),(P.parent,rows,6,30)]:
 bd=read(d/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
 assert hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
 assert [r['source_line'] for r in rs]==list(range(begin,end+1))
 assert all(r['text']==lines[r['source_line']-1] for r in rs)
parts=[first/f'part-{n:02d}' for n in range(1,7)]+[P.parent/'part-01',P.parent/'part-02',P.parent/'part-03',P];proofs=[];covered=[]
for part in parts:
 b=read(part/'content-batch.json');c=read(part/'coverage.json');sha=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
 for filename in ['publication.json','readback-audit.json']:
  proof=read(part/filename);assert proof['verified'] and proof['batch_sha256']==sha
 assert {k for r in rows1+rows if r['id'] in c['paragraphs'] for k in r['event_keys']}=={r['key'] for r in b['events']}
 covered+=c['paragraphs'];proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
assert covered==[r['id'] for r in rows1+rows[:18]]
rel=str(P.relative_to(ROOT));progress=read(ROOT/'content/yearly-progress.json')
assert progress['active_cursor']['next_paragraph'] in [rows[13]['id'],rows[18]['id']]
progress['active_cursor'].update(volume=276,year=927,last_reviewed_paragraph=rows[17]['id'],last_published_paragraph=rows[17]['id'],next_paragraph=rows[18]['id'],next_paragraph_opening=rows[18]['text'],batch=rel,status='in_progress')
y=next(x for x in progress['year_coverage'] if x['year']==927)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',completed_volumes=[275],note='927年两卷共57段，卷275全部32段与卷276前18段已发布并匿名回查，完成50段，余7段待录，全年未完成。')
for key,n,note in [
 ('wu-adoption-and-proposals',14,'徐父知询、养父李复用，旧掳育与先新杨转交说并列；兄长为养家非同血，陈家属未明妻母不建边。前事追叙、入朝计划和李草洪州未实行，接讯不强卒日。'),
 ('zhangjun-fuyanlin-inquiry',15,'主苻/旧符同副同案识人，不正式注册疑别字；疑死、诬谋反不当事实，主按无状/旧释不问存叙法，徙官不同928被拒回朝。'),
 ('wu-accession-amnesty-dates',17,'吴庚戌即位、甲子赦改元分日；新合项概叙未明同日不强判异日。新李太尉侍中、知询金陵尹补官不提前下一段丙子职位。')
]:
 full='927-v276-'+key
 if not any(x['key']==full for x in progress['editorial_followups']):progress['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=rows[n-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',progress)
idx=read(ROOT/'content/books/zizhi-tongjian/index.json');idx.update(current_volume=276,current_year=927,current_volumes=[275,276],current_batch=rel,next_paragraph=rows[18]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',idx)
write(P.parent/'progress-audit.json',dict(book='资治通鉴',volume=276,year=927,completed_paragraphs=18,volume_total_paragraphs=25,year_completed_paragraphs=50,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,year_complete=False,next_paragraph=rows[18]['id'],batches=proofs))
(P/'README.md').write_text("""# 《资治通鉴》卷276 · 927年 · part-04

连续第14—18段（原文件19—23行）已发布：27事件、41人物参与、3人物关系、125事实引用；2新增人物、13复用人物；6来源（5新增、1复用），补证《旧五代史》《新五代史》。

新增陈夫人〔徐温家属〕、符彦琳。徐温卒辛丑官衔保留；与知询父亲、与李昪养父复用旧key，补旧掳育与既有新杨行密转交养育经过异说。李与知询兄长注明养家非亲生。初追叙换政请求和计划年null，病中实际遣知询奉表与拟留代掌分开；李草求洪州未交未授，接讯日不强辛丑，知询急归、齐王忠武追赠分事。陈我家养之为话语，未明妻养母不建边。

张筠久疾、拒见、符副疑死奸谋、请交印、拘诬、朝召释、徙官分阶段；主苻/旧符同副同案识同人，苻疑字不正式别名。疑死非实死、谋反非定罪，主按无状/旧释不问不强统程序。旧補西京行京兆、诱离，未提前928到长安被拒回朝。石癸卯宣武亲军任命旧補六军副及州名，不重京水派军。

吴庚戌即位、追三先王帝号、新独补李太尉侍中和知询辅国金陵尹分别；补职确日未另载，不提前后丙子本段。安议攻、帝不从不造实际战争。甲子赦改元分事，新合即位事项概述不强定同庚戌或判异日；未补赦罪范围。

逐条原文、定位、源行及来源SHA、公开UUID、source关联和固定GitHub地址匿名回查通过。主书跨原始导出块，两块各保留快照，未拼接或标全部来源全文已处理。展示简体，原字保留，纸本及异文待核。

927年完成50/57段，下一段zztj-v276-y0927-p019；继续至936年后唐灭亡。
""")
(P.parent/'README.md').write_text("""# 《资治通鉴》卷276 · 927年

本卷25正文段（原文件6—30行），连续第1—18段四批已发布并匿名回查，余7段待录。927年另含卷275全部32段，共57段，当前完成50段，全年未完成。

下一段zztj-v276-y0927-p019。跨卷连续前缀和批次证明见progress-audit.json。
""")
print(dict(completed=50,total=57,next_paragraph=rows[18]['id'],year_complete=False))
