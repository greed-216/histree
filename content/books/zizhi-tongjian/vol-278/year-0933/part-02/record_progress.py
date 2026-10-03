# -*- coding: utf-8 -*-
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==57 and [x['source_line'] for x in r]==list(range(36,93))
assert all(x['text']==lines[x['source_line']-1] for x in r) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['status']=='published_verified' for x in r[:20]) and all(x['status']=='pending' and not x['event_keys'] for x in r[20:])
proof=[]
for part,start,end in [('part-01',0,10),('part-02',10,20)]:
 p=YEAR/part;b=read(p/'content-batch.json');sha=hashlib.sha256((p/'content-batch.json').read_bytes()).hexdigest()
 for f in ['publication.json','readback-audit.json']:
  a=read(p/f);assert a['verified'] and a['batch_sha256']==sha
 assert read(p/'coverage.json')['paragraphs']==[x['id'] for x in r[start:end]]
 assert {k for x in r[start:end] for k in x['event_keys']}=={x['key'] for x in b['events']}
 proof.append(dict(batch=str(p.relative_to(ROOT)),batch_sha256=sha,anonymous_readback_verified=True))
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[10]['id'],r[20]['id']]
pr['active_cursor'].update(volume=278,year=933,last_reviewed_paragraph=r[19]['id'],last_published_paragraph=r[19]['id'],next_paragraph=r[20]['id'],next_paragraph_opening=r[20]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==933)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='in_progress',volumes=[278],completed_volumes=[],note='卷278原36—55行连续前20正文段公开核验，全年57段，当前20/57，后37待录。第二批含亲王师傅、夏州攻防、皇子封王、闽政、明宗疾病、吴宫城与钱氏兄弟；全年及全卷未完成。')
for n,key in [(11,'liuzan_identity_and_office'),(12,'aluo_brother_identity'),(20,'qian_yuanliao_name')]:
 full='933-v278-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[n-1]['id'],required_action=r[n-1]['review']))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=278,current_year=933,current_volumes=[278],current_batch=rel,next_paragraph=r[20]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=278,year=933,completed_paragraphs=20,volume_total_paragraphs=57,year_completed_paragraphs=20,year_total_paragraphs=57,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_complete=False,volume_year_complete=False,year_complete=False,next_paragraph=r[20]['id'],batches=proof,previous_year_audit=str((YEAR.parent/'year-0932/year-audit.json').relative_to(ROOT))))
bd['note']='原36—92行57个连续正文段；前20已发布公开核验，余37待录，下一段原56行闽主复位。全年未完成；93分隔94年标题另列。';write(YEAR/'boundaries.json',bd)
(P/'README.md').write_text('# 《资治通鉴》卷278 · 933年 · part-02\n\n连续第11—20段，原46—55行。23人物（6新增17复用）、36事件、52参与、4关系、175事实引用、15出处（13新增2复用）。以《通鉴》为主，《旧五代史》《新五代史》补证；另存同书固定修订音注本用于钱元璙姓名校读，不能算独立第二史书。\n\n秦王师傅任命、劝谏与入府频次、夏州守青岭与粮道战事、皇子封王、闽地震避位及政事、明宗疾病与朝见、迁都建议和吴宫营建、夏州撤军及钱氏兄弟礼仪分录。提议与实施、传闻与定论、确日与追叙分开。钱氏入见未独载年月，不套七月封爵丁亥日；帝患风疾沿古籍表述，不推现代病名。\n\n刘赞（秦王傅）与此前923年嘉州司马刘赞证据不足以识同人，使用限定主体。主刘瓚、旧刘讚、新刘贊通过同日同职识同一秦王傅；主兵部与旧刑部侍郎留异文，父比或玭未能确定不立亲属边。阿啰王仅明确为李彝超兄，未认作其弟李彝兴，也不猜姓名。李从珂养亲与诸从子辈分不新造生父或伯叔边。\n\n主TXT在钱氏兄弟处重写元瓘；固定通鉴音注版正文元璙、注元璙即传璙，沿已有钱传璙主体补后名和兄长关系，原TXT及逐字引文保留。别名合并见content/revisions/2026-10-04-qian-chuanliao-yuanliao。两批引用定位中的长兴三年（933）笔误已按年标题校为长兴四年（933），保留原始发布批次与独立勘误记录content/revisions/2026-10-04-933-era-citation。\n\n公开精确UUID、出处关联、逐字引文、快照及上下文哈希核验通过。933年前20/57段已发布，下一段zztj-v278-y0933-p021；全年未完成。\n')
(YEAR/'README.md').write_text('# 《资治通鉴》卷278 · 933年\n\n原35行年标题、36—92行57个连续正文段。前20段已公开匿名核验，后37段待录，下一段zztj-v278-y0933-p021（原56行）。93分隔及94行934标题另列。全年未完成。\n')
print(dict(year=933,completed=20,total=57,next_paragraph=r[20]['id'],year_complete=False))
