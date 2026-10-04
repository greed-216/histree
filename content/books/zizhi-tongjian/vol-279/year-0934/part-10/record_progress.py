# -*- coding: utf-8 -*-
"""Close 934 only after all 89 body paragraphs and batch hashes are verified."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;YEAR=P.parent;ROOT=next(x for x in P.parents if (x/'content/yearly-progress.json').exists())
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
r=read(YEAR/'paragraphs.json');bd=read(YEAR/'boundaries.json');raw=ROOT/bd['source_file'];lines=raw.read_text().splitlines()
assert len(r)==77 and [x['source_line'] for x in r]==list(range(6,83)) and hashlib.sha256(raw.read_bytes()).hexdigest()==bd['source_sha256']
assert all(x['text']==lines[x['source_line']-1] and x['status']=='published_verified' for x in r)
previous=YEAR.parent.parent/'vol-278/year-0934';prior=read(previous/'paragraphs.json');assert len(prior)==12 and all(x['status']=='published_verified' for x in prior)
proofs=[]
for scope,ledger in [(previous,prior),(YEAR,r)]:
 boundary=read(scope/'boundaries.json');source=ROOT/boundary['source_file'];source_lines=source.read_text().splitlines()
 assert hashlib.sha256(source.read_bytes()).hexdigest()==boundary['source_sha256']
 assert all(row['text']==source_lines[row['source_line']-1] for row in ledger if row.get('kind','body')=='body')
 covered=[]
 for part in sorted(scope.glob('part-*')):
  h=hashlib.sha256((part/'content-batch.json').read_bytes()).hexdigest()
  for f in ['publication.json','readback-audit.json']:
   a=read(part/f);assert a['verified'] and a['batch_sha256']==h
  covered.extend(read(part/'coverage.json')['paragraphs'])
  proofs.append(dict(batch=str(part.relative_to(ROOT)),batch_sha256=h,anonymous_readback_verified=True))
 assert covered==[x['id'] for x in ledger]
nextyear=YEAR.parent/'year-0935';n=read(nextyear/'paragraphs.json');assert len(n)==37 and [x['source_line'] for x in n]==list(range(85,122))
assert all(x['status']=='pending' and not x['event_keys'] and x['text']==lines[x['source_line']-1] for x in n)
assert lines[83]=='清泰二年乙未，公元九三五年' and lines[123]=='后晋纪'
assert (ROOT/'resources/derived/tongjian/280.txt').read_text().splitlines()[4]=='天福元年丙申，公元九三六年'
rel=str(P.relative_to(ROOT));pr=read(ROOT/'content/yearly-progress.json');assert pr['active_cursor']['next_paragraph'] in [r[68]['id'],n[0]['id']]
pr['active_cursor'].update(volume=279,year=935,last_reviewed_paragraph=r[-1]['id'],last_published_paragraph=r[-1]['id'],next_paragraph=n[0]['id'],next_paragraph_opening=n[0]['text'],batch=rel,status='in_progress')
y=next(x for x in pr['year_coverage'] if x['year']==934)
if rel not in y['batches']:y['batches'].append(rel)
y.update(status='complete_published_verified',volumes=[278,279],completed_volumes=[278,279],note='934年跨卷278的12段及卷279的77段，共89正文段全部连续公开，并以匿名读回、出处及批次哈希独立核验。标题与分隔符未录成史事；下一年935年卷279原85行起共37段尚待录入。')
if not any(x['year']==935 for x in pr['year_coverage']):pr['year_coverage'].append(dict(year=935,status='in_progress',volumes=[279],completed_volumes=[],batches=[],note='卷279原85—121行共37连续正文段，包括臣光曰作者评论；原124行后晋纪标题排除。全部待录，后接卷280的936年。'))
for key,num,note in [('zhang_yanlang_name',69,'主张延郎、延朗同职同事，旧同任官写张延朗；沿已核主体，保原字，不将异写当繁简。'),('jingqian_office_chronology',70,'主934十一月景迁左仆射参政事、935三月加同平章事；新吴世家压在六年条称太保平章事。不同官衔及时间并列，待纸本核，不能前移后命。'),('e_wang_burial_identity',75,'主鄂王李从厚十二月乙酉葬，身份据已发布第21段废少帝为鄂王；旧十二月庚午诏葬庶人从荣有异文，不能直接等同对象或改字。命葬与执行亦非同日。'),('yang_han_character',77,'主汉曰政乱如此中的汉字、说话主语有疑，未强定杨或刘发言；原字保留，待更明确版本校核。'),('yang_death_year',77,'杨洞潜谢病归第后久之不召遂卒，死年不明确，事件年null；不将年末追叙硬设934死亡。')]:
 full='934-v279-'+key
 if not any(x['key']==full for x in pr['editorial_followups']):pr['editorial_followups'].append(dict(key=full,status='published_with_textual_review_pending_paper',primary_batch=rel,primary_paragraph=r[num-1]['id'],required_action=note))
write(ROOT/'content/yearly-progress.json',pr)
i=read(ROOT/'content/books/zizhi-tongjian/index.json');i.update(current_volume=279,current_year=935,current_volumes=[279],current_batch=rel,next_paragraph=n[0]['id']);write(ROOT/'content/books/zizhi-tongjian/index.json',i)
write(YEAR/'progress-audit.json',dict(book='资治通鉴',volume=279,year=934,completed_paragraphs=77,volume_total_paragraphs=77,year_completed_paragraphs=89,year_total_paragraphs=89,continuous_prefix_verified=True,source_hash_and_lines_verified=True,volume_year_complete=True,year_complete=True,next_volume=279,next_year=935,next_paragraph=n[0]['id'],batches=proofs,year_scope=[dict(volume=278,body_paragraphs=12,published=12),dict(volume=279,body_paragraphs=77,published=77)]))
bd['note']='934年本卷原6—82行共77正文段全部公开核验；跨卷278的12段，全年89/89完成。卷279的935年原85行起37正文均未录入。';write(YEAR/'boundaries.json',bd)
(YEAR/'README.md').write_text('# 《资治通鉴》卷279 · 934年\n\n本卷原6—82行77正文段全部发布并独立匿名核验。全年跨卷278的12段和本卷77段，共89/89连续正文全部完成。下一年从 zztj-v279-y0935-p001（原85行）开始，935年37段全部待录。\n\n人名、官职、死日、葬礼、指控和执行分别核对；旧从荣与主鄂王李从厚葬礼异文、景迁官职压缩时序、杨洞潜疑字及不明死年均保独立出处和待考说明。\n')
print(dict(year=934,completed=89,total=89,next_paragraph=n[0]['id'],year_complete=True))
