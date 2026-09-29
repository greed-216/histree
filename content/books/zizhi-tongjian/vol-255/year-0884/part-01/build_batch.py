"""Read seven consecutive Tongjian paragraphs; generate draft records and a coverage ledger."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(p for p in P.parents if (p/'scripts/validate-content-batch.py').exists())
B={'format_version':1,'batch_key':'zztj-v255-y0884-p001-p007',**{k:[] for k in ['people','events','person_events','person_relationships','sources','claims','topics']}}
source='tongjian-255-late-tang'
legacy=[ROOT/'content'/d/'content-batch.json' for d in ['later-liang-907-923','year-0907','late-tang-zhu-wen-early']]
registry={}
identity_batches=legacy+sorted(f for f in (ROOT/'content/books').rglob('content-batch.json') if f.parent!=P and (f.parent/'publication.json').exists() and json.loads((f.parent/'publication.json').read_text()).get('verified'))
for path in identity_batches:
 for row in json.loads(path.read_text())['people']:
  registry[row['name']]=row
src=next(x for x in json.loads(legacy[-1].read_text())['sources'] if x['key']==source)
B['sources']=[src]
raw=(ROOT/'resources/derived/tongjian/255.txt').read_bytes();(P/'sources'/f'{source}.txt').write_bytes(raw)
(P/'sources/manifest.json').write_text(json.dumps([{'key':source,'file':f'{source}.txt','sha256':hashlib.sha256(raw).hexdigest(),'url':src['url'],'upstream':'resources/derived/tongjian/255.txt','transformation':'none'}],ensure_ascii=False,indent=2)+'\n')
paras=[];year=False
for line_no,line in enumerate(raw.decode().splitlines(),1):
 if line=='中和四年甲辰，公元八八四年':year=True;continue
 if year and line.strip():paras.append({'id':f'zztj-v255-y0884-p{len(paras)+1:03d}','source_key':source,'source_line':line_no,'text':line})
Q={n:p for n,p in enumerate(paras,1)};used={};reused=[];people={}
def claim(table,key,field,text,n,quote=None,note=None):
 B['claims'].append(dict(key=f'claim_zztj_255_0884_01_{len(B["claims"])+1:04d}',subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=source,citation=f'卷255·中和四年（884）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',note='原文：'+(quote or Q[n]['text'])+'；核对说明：'+(note or '按该年条及段落顺序整理；未给出的月日不推定。引用只支持本条所述内容，不代表整个人物传记。'),status='draft'))
def person(name,n,role,aliases=None):
 if name in people:return people[name]
 if name in registry:
  row=dict(registry[name],status='draft');reused.append(row['key'])
 else:row=dict(key='person_'+name,name=name,aliases=aliases or [],era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷255中和四年记载的{name}：{role}。',biography=None,status='draft')
 B['people'].append(row);people[name]=row['key'];claim('person',row['key'],'biography',f'中和四年条中，{name}为{role}。',n)
 return row['key']
def event(slug,title,n,time,place,desc,actors,note=None):
 key='event_zztj_255_0884_'+slug
 B['events'].append(dict(key=key,title=title,start_year=884,end_year=884,time_original=time,dynasty='唐',description=desc,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='史载地名；未核定古城址与坐标。' if place else '未确定单一发生地。',status='draft'))
 used.setdefault(n,[]).append(key);claim('event',key,'description',desc,n,note=note);claim('event',key,'time_original',time,n,note=note)
 for name,role in actors:
  pk=person(name,n,role,['乐行达'] if name=='乐彦祯' else None);ek='participation_'+slug+'_'+pk
  B['person_events'].append(dict(key=ek,person_key=pk,event_key=key,role=role,status='draft'));claim('person_event',ek,'role',f'{name}在“{title}”中：{role}。',n)
 return key
event('lu_xingyuan','鹿晏弘获任兴元留后',1,'中和四年春正月','兴元','唐廷任鹿晏弘为兴元留后。',[('鹿晏弘','受任兴元留后')])
event('le_rename','乐行达获赐名彦祯',2,'中和四年正月条，具体日未载',None,'唐廷赐魏博节度使乐行达名彦祯；乐行达与乐彦祯为同一人。',[('乐彦祯','获赐名者')])
claim('person',people['乐彦祯'],'aliases','乐行达获赐名彦祯。',2)
event('yang_recalled','唐廷征杨师立为右仆射',3,'中和四年正月条，具体日未载',None,'杨师立不满陈敬瑄兄弟权势，以及陈敬瑄许诺以东川酬赏高仁厚之事。田令孜担心杨师立作乱，唐廷征杨师立为右仆射。',[('杨师立','被征为右仆射'),('田令孜','担忧杨师立作乱'),('陈敬瑄','此前许诺以东川酬赏高仁厚')],'陈敬瑄遣高仁厚讨韩秀升及许诺为追叙，未另定为884年新发生事件。电子本文“因其不发兵遏”疑有脱文，不据此扩写罪名。')
event('li_eastward','李克用应援出兵，受阻后改道东渡',4,'中和四年二月','天井关、万善、陕及河中','周岌、时溥、朱全忠难以抵挡黄巢，共向李克用求援。二月，李克用领蕃、汉兵五万出天井关；诸葛爽以河桥未修好为由屯万善拒之，李克用改从陕、河中渡河向东。',[('周岌','求援者'),('时溥','求援者'),('朱温','以朱全忠名义求援'),('李克用','领兵应援并改道'),('诸葛爽','屯兵阻拦'),('黄巢','求援诸军所对抗的势力首领')])
event('yang_revolt','杨师立拒绝受代，起兵并进攻绵州',5,'中和四年二月条，具体日未载','涪城、绵州','杨师立拒绝受代，杀官告使与监军使，以讨陈敬瑄为名起兵，进屯涪城；遣郝蠲袭绵州，未能攻克。',[('杨师立','起兵者'),('郝蠲','奉命袭绵州'),('陈敬瑄','杨师立声称讨伐的对象')])
event('chen_command','陈敬瑄获授三道统军职权',5,'中和四年二月丙午',None,'唐廷任陈敬瑄为西川、东川、山南西道都指挥、招讨、安抚、处置等使。',[('陈敬瑄','受任者')])
event('yang_proclamation','杨师立发布讨陈敬瑄檄文',5,'中和四年三月甲子',None,'杨师立向行在百官及诸道将吏士庶移檄，列陈敬瑄十罪，自称集将士与八州坛丁十五万人，将长驱问罪。十五万人为檄文自称数目。',[('杨师立','发檄者'),('陈敬瑄','被檄文指责者')])
event('gao_campaign','唐廷削杨师立官爵，命高仁厚率军讨伐',5,'中和四年三月甲子檄文之后，具体日未载','东川','唐廷削杨师立官爵，任眉州防御使高仁厚为东川留后，领兵五千讨伐，以杨茂言为行军副使。',[('杨师立','被削官爵及讨伐者'),('高仁厚','受任东川留后并领军'),('杨茂言','行军副使')])
event('wazi_capture','朱全忠攻取瓦子寨，李唐宾、王虔裕归降',6,'中和四年三月条，具体日未载','瓦子寨','朱全忠攻取黄巢瓦子寨；黄巢将领李唐宾、王虔裕归降朱全忠。',[('朱温','以朱全忠名义攻寨并受降'),('李唐宾','归降者'),('王虔裕','归降者')],'该段位于三月条下、四月记事前，未单独标注日。李唐宾为陕人，王虔裕为楚丘人。')
event('wang_zhen','王镇拘执婺州刺史黄碣，归降钱镠',7,'中和四年三月条，具体日未载','婺州','婺州人王镇拘执刺史黄碣，归降钱镠。',[('王镇','拘执刺史并归降'),('黄碣','被拘执的婺州刺史'),('钱镠','归降对象')])
event('lou_lai','刘汉宏遣娄赉杀王镇并取代其位',7,'中和四年三月条，具体日未载','婺州','刘汉宏遣将娄赉杀王镇并取代其位。',[('刘汉宏','派遣者'),('娄赉','杀王镇并取代其位'),('王镇','被杀者')])
event('wuzhou_attack','蒋环邀钱镠军攻婺州，擒娄赉',7,'中和四年三月条，具体日未载','婺州','浦阳镇将蒋环召钱镠军共同进攻婺州，擒获娄赉后返回。',[('蒋环','邀兵并共同进攻'),('钱镠','出兵一方，不据此断定亲自领兵'),('娄赉','被擒者')])
# Record source-bound details without expanding undated biographies.
for name,text,n,q in [('李唐宾','李唐宾为陕人。',6,'巢将陕人李唐宾'),('王虔裕','王虔裕为楚丘人。',6,'楚丘王虔裕'),('黄碣','黄碣为闽人。',7,'碣，闽人也。')]:claim('person',people[name],'biography',text,n,quote=q)
# Explicit, time-bounded command relations only. Merely co-occurring actors are not allies.
for a,c,n,typ,desc in [('杨师立','郝蠲',5,'派遣者','884年二月条，杨师立遣郝蠲袭绵州。'),('刘汉宏','娄赉',7,'派遣者','884年三月条，刘汉宏遣娄赉杀王镇；仅据本次派遣建立关系。')]:
 key=f'relationship_{people[a]}_{people[c]}_{typ}';B['person_relationships'].append(dict(key=key,person_a_key=people[a],person_b_key=people[c],relation_type=typ,description=desc,status='draft'));claim('person_relationship',key,'description',desc,n)
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
record_status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n,row in enumerate(paras,1):
 row.update(status=record_status if n<=7 else 'pending',event_keys=used.get(n,[]),batch_key=B['batch_key'] if n<=7 else None)
 if n==3:row['deferred']='前事：高仁厚讨韩秀升与陈敬瑄的许诺，不在884年新建事件；“不发兵遏”疑脱文待校。'
 if n==5:row['review']='段内跨二月与三月，拆为四个事件；檄文兵数保留自称属性。'
 if n==7:row['review']='拆为王镇拘刺史、娄赉杀王镇、蒋环邀攻三事。'
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(set(reused+[source])),ensure_ascii=False,indent=2)+'\n')
(P.parent/'paragraphs.json').write_text(json.dumps(paras,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps({'book':'资治通鉴','volume':255,'year':884,'primary_source_key':source,'paragraphs':[r['id'] for r in paras[:7]],'next_paragraph':paras[7]['id'],'coverage':'连续七段；本卷当年后续段落及卷256下半年尚未录入','supplements':[],'status':record_status},ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
