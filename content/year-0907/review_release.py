# -*- coding: utf-8 -*-
"""Apply the documented 907 source review after build_batch.py. Offline, deterministic."""
import json, hashlib
from pathlib import Path
D=Path(__file__).resolve().parent; R=D.parents[1]
b=json.loads((D/'content-batch.json').read_text()); manifest=json.loads((D/'sources/manifest.json').read_text())
assert not any(x['key']=='claim_0907_review_001' for x in b['claims']), 'Run build_batch.py first'
old=json.loads((D.parent/'later-liang-907-923/content-batch.json').read_text()); reused={x['key'] for x in old['claims']}
for c in b['claims']:
 if c['key'] not in reused:c['note']=c['note'].replace('尚待人工审阅。','2026-09-29由项目助手核读；单源内容按书中记载发布，不视为独立证实。')
meta=json.loads((R/'resources/catalog/twenty-four-histories.json').read_text())
texts={}; snippets={}; sources={x['key']:x for x in b['sources']}
for title,num,key in [('旧五代史','18','jiuwudaishi-github-20260929'),('新五代史','19','xinwudaishi-github-20260929')]:
 texts[key]={r['pdf_page']:r['text'] for r in map(json.loads,(R/f'resources/derived/twenty-four-histories/{num}{title}.jsonl').read_text().splitlines())}
 if key not in sources:
  s=dict(key=key,title=title+'（GitHub电子排印本）',source_type='digital',author='薛居正等；清代辑本',edition='grimoire-kindle固定提交cc24276；电子排印本，底本待考',url=next(x['url'] for x in meta if x['title']==title),note='引用按PDF实际页码。旧五代史现行辑本夹有他书引文；明确引自通鉴的段落不计作独立证据。')
  b['sources'].append(s);sources[key]=s
J='jiuwudaishi-github-20260929'; X='xinwudaishi-github-20260929'
serial=0
def add(table,key,field,statement,src,quote,cite,note='本项目核读电子文本；文字层不是原刻影印，未作纸本校勘。'):
 global serial
 serial+=1
 b['claims'].append(dict(key=f'claim_0907_review_{serial:03d}',subject_table=table,subject_key=key,field_path=field,claim_text=statement,source_key=src,citation=cite,note='原文：'+quote+'；核对说明：'+note,status='draft'))
 snippets.setdefault(src,[]).append(quote)
def pdf(code,src,page,statement,field='description',note=None,table='event'):
 add(table,'event_0907_'+code if table=='event' and code!='event_liang_founded' else code,field,statement,src,texts[src][page],f'太祖纪三·PDF第{page}页' if src==J else f'梁本纪第二·PDF第{page}页',**({'note':note} if note else {}))
def amend(code,field,value):
 k='event_0907_'+code;next(x for x in b['events'] if x['key']==k)[field]=value
 for c in b['claims']:
  if c['subject_key']==k and c['field_path']==field:c['claim_text']=value
for code,src,p,st in [('ma_chu',J,74,'《旧五代史》亦记辛未马殷进封楚王。'),('jingxiang',J,74,'《旧五代史》记敬翔知崇政院。'),('jingxiang',X,24,'《新五代史》记五月甲午改枢密院为崇政院，以敬翔为使。'),('youwen',J,75,'《旧五代史》记朱友文任开封尹、判建昌院事，并明确其为朱温养子。'),('xue_pm',J,77,'《旧五代史》记薛贻矩任中书侍郎、平章事。'),('southern_titles',J,77,'《旧五代史》记张全义进封魏王、钱镠进封吴越王；本条不用于证明刘隐、王审知的加授。'),('zhu_princes',X,24,'《新五代史》亦记封朱全昱及诸子为王，但所列名单与通鉴不同，未列友雍，另列三名侄辈；保留各书所载，不拼接成同一完整名单。'),('quhao',J,81,'《旧五代史》记曲裕卒，七月丙申曲颢起复安南都护、充节度使。'),('jiazai',J,82,'《旧五代史》将李思安接任潞州行营都统记于八月；此处不能独立证明夹寨所有细节。'),('deserters_amnesty',X,25,'《新五代史》亦记十一月壬寅赦亡命背军髡黥刑徒。')]:pdf(code,src,p,st)
for src,p in [(J,79),(X,24)]:pdf('hanjian',src,p,'韩建拜相月份有异：《旧五代史》列五月，《通鉴》《新五代史》列六月甲寅。本条日期从后二书，保留异文。','time_original')
amend('ancestors','time_original','907年（追尊及相关礼仪分阶段记载，各书系月有异）')
for src,p in [(J,74),(J,75),(J,82),(X,24)]:pdf('ancestors',src,p,'追尊日期不可压为单日：《旧五代史》四月载追号、七月载追尊皇妣皇太后；《新五代史》将祖考妣追尊集中列于七月。','time_original')
amend('khitan_envoys','time_original','907年后梁建立后（通鉴系五月条，新五代史系四月条）')
pdf('khitan_envoys',X,23,'袍笏梅老来使在《新五代史》列四月条，在《通鉴》列五月条。此页仅核来使，不能证明高颀回访的具体日期。','time_original')
for src,p in [(J,69),(X,23)]:pdf('event_liang_founded',src,p,'受禅日期记法有异：《旧五代史》此处作戊辰即位；《通鉴》《新五代史》作四月甲子即位、戊辰改元。现有条目沿用通鉴记法，引用并列供复核。','time_original')
rel=next(x for x in b['person_relationships'] if x['relation_type']=='养父');pdf(rel['key'],J,75,'朱友文本康氏子，由朱温收养；养父关系有《旧五代史》直接记载。',table='person_relationship')
# Regional accounts retain their textual variants and page markers.
km=json.loads((R/'resources/catalog/kanripo.json').read_text())
for repo,title,author,edition,file in [('KR2i0019','吴越备史','范坰、林禹','SBCK','002'),('KR2i0016','蜀梼杌','张唐英','WYG','001')]:
 m=next(x for x in km if x['key']==repo);key=repo+'-0907-review'
 url=f"https://github.com/kanripo/{repo}/blob/{m['commit']}/{repo}_{file}.txt"
 s=dict(key=key,title=title+'（Kanripo电子本）',source_type='digital',author=author,edition=edition+'；版本标识沿用来源，未逐叶影像核对',url=url,note='保留原文页标、异体字和缺字代码；缺字代码不自行释读。固定版本见URL。')
 b['sources'].append(s);sources[key]=s
 raw=(R/f'resources/originals/kanripo/{repo}/{repo}_{file}.txt').read_text()
 if repo=='KR2i0019':
  quote=raw[raw.index('<pb:KR2i0019_SBCK_002-2a>'):raw.index('<pb:KR2i0019_SBCK_002-2b>')]
  amend('wenzhou','time_original','907年正月至四月（吴越备史记正月出兵，通鉴记三月出兵；四月取温州）')
  add('event','event_0907_wenzhou','time_original','《吴越备史》记正月伐永嘉、四月斩卢佶而还，与通鉴出兵月份不同；不据此强定单一月份。',key,quote,'卷二·文穆王·002-2a')
 else:
  quote=raw[raw.index('<pb:KR2i0016_WYG_001-4a>'):raw.index('<pb:KR2i0016_WYG_001-4b>')]
  add('event','event_0907_shu_founded','description','《蜀梼杌》亦记九月王建称帝、号大蜀；其改元武成的系年与通鉴不同，本条仅用来核对称帝，不据此新增907年改元事件。',key,quote,'卷上·001-4a','原文年次及改元记法与通鉴存在差异，需后续专门校勘；祥瑞叙事未转为史实。')
  add('event','event_0907_shu_officials','description','《蜀梼杌》亦列王宗佶中书令、韦庄判中书门下事、唐道袭枢密使；此引文不能证明王宗懿受封日期。',key,quote,'卷上·001-4a')
# Add independent Old History material; source statements do not imply decrees were fully carried out.
def newevent(code,title,time,desc,pages,participants):
 key='event_0907_'+code; row=dict(next(x for x in b['events'] if x['key']=='event_0907_xue_pm'))
 row.update(key=key,title=title,time_original=time,description=desc);b['events'].append(row)
 quote='\n'.join(texts[J][p] for p in pages)
 for field,value in [('description',desc),('time_original',time),('start_year','据太祖纪三开平元年条定位907年。')]:add('event',key,field,value,J,quote,'太祖纪三·PDF第'+ '、'.join(map(str,pages))+'页')
 for name,role in participants:
  person=next(x for x in b['people'] if x['name']==name);rk='participation_0907_'+code+'_'+person['key']
  b['person_events'].append(dict(key=rk,person_key=person['key'],event_key=key,role=role,status='draft'))
  add('person_event',rk,'role',name+'在“'+title+'”中的角色：'+role+'。',J,quote,'太祖纪三·PDF第'+ '、'.join(map(str,pages))+'页')
 b['topics'][0]['sections'].append(dict(heading=title,body='补自《旧五代史》；请在条目出处中查看原文。',node_keys=[key]))
newevent('retain_chancellors','张文蔚、杨涉留任宰相','梁开平元年五月','后梁以唐朝宰臣张文蔚、杨涉为门下侍郎、平章事；这是政权更替后的官职延续。',[77],[('朱温','任命者'),('张文蔚','受任者'),('杨涉','受任者')])
newevent('restore_exiles','后梁诏复唐朝被贬官员官资','梁开平元年六月癸亥','后梁下诏登记唐朝被贬南方官员姓名，恢复官资并送赴京师；已死者准许归葬。这里记录诏令，不断言各地全部执行。',[80,81],[('朱温','发诏者')])
newevent('release_palace','后梁放出西京宫人','梁开平元年九月辛丑','《旧五代史》记西京大内放出两宫内人及前朝宫人，任其所适；不推算人数，也不扩写后续生活。',[83],[('朱温','在位君主')])
newevent('envoy_limits','后梁规定使臣停留期限','梁开平元年九月条，具体日未单列','后梁针对奉使官员长期滞留，按各地距离规定一月、二十日、十日或三五日等停留期限，旅途日行两驿；疾病、江河阻隔须奏报，由御史纠察。',[83,84],[('朱温','发敕者')])
b['topics'][0]['description']='以《资治通鉴》907年条为主线，参读新旧五代史、吴越备史、蜀梼杌。保留各书差异，提供逐条原文与出处；部分记载仍为单源。'
b['topics'][0]['sections'][0]['body']+=' 多源补核的差异在各条引用中列明；未定年的追叙继续暂缓。'
for key,qs in snippets.items():
 file='review-'+key+'.txt';path=D/'sources'/file
 # New History already has identity excerpts: keep both in a single manifest file.
 existing=next((x for x in manifest if x['key']==key),None)
 original=(D/'sources'/existing['file']).read_text() if existing else ''
 path.write_text(original+'\n\n'+'\n\n'.join(dict.fromkeys(qs)))
 item=dict(key=key,file=file,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),accessed_at='2026-09-29',url=sources[key]['url'])
 manifest=[x for x in manifest if x['key']!=key]+[item]
(D/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(D/'content-batch.json').write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
report={'reviewed_at':'2026-09-29','reviewer':'项目助手，受用户委托核读电子史料','added_claims':serial,'new_events':4,'counts':{k:len(v) for k,v in b.items() if isinstance(v,list)},'limits':['多源核对集中于开国、任官、追尊、使行、吴越和蜀；不是每条均有独立来源。','旧五代史内明确转引通鉴的段落不作为独立证据。','电子排印底本未考定，PDF页码非古籍叶码；未作影像校勘。','无确切年代的追叙仍暂缓；月份异文并列，不强行裁决。']}
(D/'release-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report)
