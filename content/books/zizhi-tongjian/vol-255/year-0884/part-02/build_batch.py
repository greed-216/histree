"""Curate the final eleven consecutive paragraphs in Tongjian volume 255, year 884."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=next(x for x in P.parents if (x/'scripts/validate-content-batch.py').exists())
YEAR_DIR=P.parent
B={'format_version':1,'batch_key':'zztj-v255-y0884-p008-p018',**{k:[] for k in ['people','events','person_events','person_relationships','sources','claims','topics']}}
source='tongjian-255-late-tang'
legacy=[ROOT/'content'/x/'content-batch.json' for x in ['later-liang-907-923','year-0907','late-tang-zhu-wen-early']]
prior=YEAR_DIR/'part-01/content-batch.json'
registry={}
for f in legacy+[prior]:
 for row in json.loads(f.read_text())['people']:
  registry[row['name']]=row
src=next(x for x in json.loads(prior.read_text())['sources'] if x['key']==source)
B['sources']=[src]
raw=(ROOT/'resources/derived/tongjian/255.txt').read_bytes()
(P/'sources'/f'{source}.txt').write_bytes(raw)
(P/'sources/manifest.json').write_text(json.dumps([dict(key=source,file=f'{source}.txt',sha256=hashlib.sha256(raw).hexdigest(),url=src['url'],upstream='resources/derived/tongjian/255.txt',transformation='none')],ensure_ascii=False,indent=2)+'\n')
paras=json.loads((YEAR_DIR/'paragraphs.json').read_text());Q={int(r['id'][-3:]):r for r in paras};used={};people={};reused={source}
def excerpt(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);return t[a:a+len(start)] if end is None else t[a:t.index(end,a)+len(end)]
def claim(table,key,field,text,n,q=None,note=None):
 assert 8<=n<=18
 q=q or Q[n]['text'];assert q in Q[n]['text']
 B['claims'].append(dict(key=f'claim_zztj_255_0884_02_{len(B["claims"])+1:04d}',subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=source,citation=f'卷255·中和四年（884）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',note=f'原文：{q}；核对说明：{note or "按此段原文整理；所述范围限于本段与引文，不扩充人物完整生平或精确月日。"}',status='draft'))
def person(name,n,role,aliases=None):
 if name in people:return people[name]
 if name in registry:
  row=dict(registry[name],status='draft');reused.add(row['key'])
 else:
  row=dict(key='person_'+name,name=name,aliases=aliases or [],era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷255中和四年条记载的{name}，在此段中为{role}。',biography=None,status='draft')
 B['people'].append(row);people[name]=row['key'];claim('person',row['key'],'biography',f'中和四年条所见：{name}为{role}。',n)
 return row['key']
def event(code,title,n,time,place,desc,actors,quote=None,year=884,note=None):
 key='event_zztj_255_0884_'+code
 B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=time,dynasty='唐',description=desc,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名，坐标未核。' if place else '原文未确定单一地点。',status='draft'))
 used.setdefault(n,[]).append(key)
 q=quote or Q[n]['text'];claim('event',key,'description',desc,n,q,note);claim('event',key,'time_original',time,n,q,note or ('此段为追叙或含“久之”等非精确时间，未强定发生年份。' if year is None else '由该年条定位；干支日未换算成公历日。'))
 for name,role in actors:
  pk=person(name,n,role);edge='participation_'+code+'_'+pk
  B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
  claim('person_event',edge,'role',f'{name}：{role}。',n,q)
 return key
def relation(a,b,n,kind,desc,q=None):
 ak=people[a];bk=people[b];key=f'relationship_{ak}_{bk}_{kind}'
 B['person_relationships'].append(dict(key=key,person_a_key=ak,person_b_key=bk,relation_type=kind,description=desc,status='draft'))
 claim('person_relationship',key,'description',desc,n,q)
 return key
# p008: multiple time layers, so later 舒州/庐州 incidents retain unknown year.
event('gao_accuses_lv','高澞向高骈呈吕用之罪状',8,'中和四年春条，具体月日未载',None,'高澞向高骈呈吕用之罪状；高骈没有采纳，次日又将文书示吕用之。',[('高澞','呈文者'),('高骈','受呈者'),('吕用之','被指控者')],excerpt(8,'高骈从子左骁卫大将军澞','命扶出。'))
event('gao_shuzhou','高澞知舒州事',8,'前事后月余；确年待考','舒州','高骈在高澞进言后一个多月，命高澞知舒州事。',[('高骈','任命者'),('高澞','知舒州事')],excerpt(8,'骈甚惭','以澞知舒州事。'),None)
event('li_shenfu_relief','李神福以旗帜疑兵解舒州之围',8,'高澞到舒州之后；确年待考','舒州','陈儒攻舒州，高澞向庐州求援。杨行愍兵力不足，李神福以多面旗帜营造援兵到来的声势，攻城者夜遁。',[('陈儒','攻舒州者'),('高澞','求援者'),('杨行愍','被求援者'),('李神福','用疑兵解围者')],excerpt(8,'群盗陈儒攻舒州','贼惧，宵遁。'),None)
event('gao_shuzhou_fall','吴迥、李本再攻舒州，高澞弃城后被杀',8,'前事久之；确年待考','舒州','吴迥、李本再攻舒州；高澞弃城，高骈派人杀高澞。',[('吴迥','攻舒州者'),('李本','攻舒州者'),('高澞','弃城及被杀者'),('高骈','遣人杀高澞者')],excerpt(8,'久之，群盗吴迥','骈使人就杀之。'),None)
event('yang_defeats_wu_li','杨行愍部擒斩吴迥、李本',8,'舒州再攻之后；确年待考','舒州','杨行愍遣陶雅、张训等攻吴迥、李本，擒斩二人；以陶雅摄舒州刺史。',[('杨行愍','遣兵者'),('陶雅','领兵及摄刺史'),('张训','领兵者'),('吴迥','被擒斩者'),('李本','被擒斩者')],excerpt(8,'杨行愍遣其将合肥陶雅','以雅摄州刺史。'),None)
event('tian_jun_luzhou','田頵击退攻庐州的秦宗权部',8,'舒州事后续叙；确年待考','庐州、舒城','秦宗权遣其弟领兵攻庐州、据舒城；杨行愍遣田頵击退。原文未记秦宗权之弟姓名。',[('秦宗权','遣兵者'),('杨行愍','遣田頵出战者'),('田頵','击退进攻者')],excerpt(8,'秦宗权遣其弟将兵寇庐州','遣其将合肥田頵击走之。'),None)
claim('person',people['李神福'],'biography','李神福为洺州人。',8,'神福，洺州人也。')
# p009: separate locations and actions.
event('lu_ezhou','路审中募兵据鄂州',9,'中和四年春条，具体月日未载','鄂州','前杭州刺史路审中在黄州得知鄂州刺史崔绍去世后，募兵三千人进入并占据鄂州。',[('路审中','据鄂州者'),('崔绍','原鄂州刺史，已去世')])
event('du_yuezhou','杜洪逐岳州刺史',9,'中和四年春条，具体月日未载','岳州','武昌牙将杜洪逐走岳州刺史，自行取代。原文未记被逐刺史姓名。',[('杜洪','逐刺史并取代者')])
# p010: April and lifting of the siege; do not move the long siege's start into 884.
event('taikang_xihua','李克用与诸军攻太康、西华',10,'中和四年夏四月癸巳起','太康、西华','李克用会合许、汴、徐、兗之军，四月癸巳拔太康；又攻西华，黄思鄴逃走。',[('李克用','会诸军进攻者'),('尚让','屯太康者'),('黄思邺','屯西华后逃走者')],excerpt(10,'李克用会许、汴','思鄴走。'))
event('chenzhou_lifted','黄巢撤出，陈州之围解除',10,'中和四年夏四月太康、西华战后','陈州','黄巢听闻诸军攻取太康、西华后退至故阳里，陈州之围解除。围陈州几三百日是截至此时的累计时长，不把围城起始记作884年。',[('黄巢','撤围者'),('赵犨','陈州守将'),('李克用','援军统领之一')],excerpt(10,'黄巢围陈州几三百日','陈州围始解。'),note='围城开始早于本年，事件仅记884年解围；不将近三百日误作自本年起。')
# p011: multiple May actions and separate named defections.
event('huang_to_bian','黄巢军趋汴州并掠尉氏',11,'中和四年五月癸亥起','尉氏、汴州方向','五月癸亥大雨，黄巢军营受水淹，黄巢又得知李克用到来，遂向汴州方向移动，攻掠尉氏。',[('黄巢','率军转向者'),('李克用','黄巢闻其将到者')],excerpt(11,'硃全忠闻黄巢将至','屠尉氏。'))
event('fan_tai','尚让逼大梁，朱珍与庞师古击退',11,'中和四年五月条，王满渡之战前','繁台','尚让领骑五千进逼大梁至繁台，宣武将朱珍、庞师古将其击退。',[('尚让','进逼者'),('朱珍','击退者'),('庞师古','击退者')],excerpt(11,'尚让以骁骑五千进逼大梁','击却之。'))
event('wangmandu','李克用在王满渡击败黄巢军',11,'中和四年五月戊辰','王满渡','朱全忠向李克用告急；五月戊辰，李克用与田从异追黄巢至王满渡，乘其军半渡而击，大败之。',[('朱温','向李克用告急'),('李克用','领兵击败黄巢军'),('田从异','同领兵追击者'),('黄巢','败军统领')],excerpt(11,'全忠复告急于李克用。','贼遂溃。'))
event('huang_generals_defect','尚让等分别归降时溥、朱全忠',11,'中和四年五月王满渡战后','汴州附近','王满渡败后，尚让率众降时溥；李谠、霍存、葛从周、张归霸及从弟张归厚等降朱全忠。',[('尚让','降时溥者'),('时溥','受降者'),('朱温','以朱全忠名义受降者'),('李谠','降朱全忠者'),('霍存','降朱全忠者'),('葛从周','降朱全忠者'),('张归霸','降朱全忠者'),('张归厚','降朱全忠者')],excerpt(11,'尚让帅其众降时溥','帅其众降硃全忠。'))
event('huang_pursued','李克用追黄巢至冤句后还汴',11,'中和四年五月己巳至辛未','封丘、冤句','李克用先在封丘再败黄巢，追至冤句；因兵马疲乏、粮尽，返回汴州。黄巢向东逃走。',[('李克用','追击者'),('黄巢','撤退者')],excerpt(11,'巢逾汴而北，己巳','乃还汴州，'),note='本段列己巳、庚午、辛未次序；不换算公历日期。原文“东奔充州”疑为兗州等转录讹误，暂不据此定位。')
# p012, p013: the inn incident.
event('lutou_garrison','高仁厚屯德阳，杨师立部据鹿头关',12,'中和四年五月癸酉','德阳、鹿头关','高仁厚屯德阳；杨师立遣郑君雄、张士安据鹿头关抵御。',[('高仁厚','屯德阳者'),('杨师立','遣兵者'),('郑君雄','守鹿头关者'),('张士安','守鹿头关者')])
event('shangyuan_attack','朱全忠部围攻上源驿，李克用脱险',13,'中和四年五月甲戌夜','汴州上源驿','李克用甲戌到汴州，朱全忠邀其入城住上源驿。宴后，杨彦洪与朱全忠谋围攻驿馆；李克用在薛志勤、史敬思等护卫下突围，史敬思战死。',[('李克用','被围攻及脱险者'),('朱温','以朱全忠名义设宴及参与围驿'),('杨彦洪','同谋并领兵围驿'),('薛志勤','护卫突围者'),('史敬思','殿后战死者'),('郭景铢','协助李克用脱险者')],excerpt(13,'甲戌，李克用至汴州','史敬思为后拒，战死。'))
event('yang_yanhong_dead','上源驿当夜朱全忠射杀杨彦洪',13,'中和四年五月甲戌夜','汴州','上源驿事变当夜，杨彦洪骑马行于朱全忠前，朱全忠射杀杨彦洪。',[('杨彦洪','被射杀者'),('朱温','射杀者')],excerpt(13,'杨彦洪谓全忠曰','全忠射之，殪。'))
event('liu_advises','刘氏劝李克用向朝廷申诉',14,'上源驿事变次晨，五月条','汴州','李克用妻刘氏劝阻其立即攻打朱全忠，建议向朝廷申诉；李克用听从并率军离去。',[('刘氏（李克用妻）','劝阻者'),('李克用','听从劝告者'),('朱温','被指控一方')],excerpt(14,'比明，克用至','克用从之，引兵去，'))
event('li_zhu_letters','李克用与朱全忠互致书信争论事变',14,'上源驿事变次日或稍后，具体日期未载',None,'李克用书信责朱全忠。朱全忠回信声称自己不知前夜事变，称由朝廷使者与杨彦洪谋划；这是其自辩之辞，不能直接当作事实。',[('李克用','致书责问者'),('朱温','回书自辩者')],excerpt(14,'但移书责全忠。','惟公谅察。'),note='朱全忠关于“不知”及“朝廷使者”的说法是书信中的单方辩解，与本卷围驿叙述并列保留。')
# p015: adoption is background; no fabricated 884 adoption date.
for child,alias in [('李嗣源','邈佶烈'),('李存信',None),('李存进',None),('李存贤',None),('李存孝','安敬思')]:
 person(child,15,'李克用养子',[alias] if alias else None)
person('李克用',15,'养父')
for child in ['李嗣源','李存信','李存进','李存贤','李存孝']:
 relation('李克用',child,15,'养父',f'《通鉴》卷255记李克用收{child}为养子；收养发生年未据此段确定。',excerpt(15,'克用养子嗣源','皆冒姓李氏。'))
claim('person',people['李嗣源'],'aliases','李嗣源原名邈佶烈。',15,'嗣源本胡人，名邈佶烈，无姓。')
claim('person',people['李存孝'],'aliases','李存孝原名安敬思。',15,'安敬思曰存孝')
event('li_returns_jinyang','李克用求粮不获后返回晋阳',15,'中和四年五月丙子以后','许州、晋阳','李克用五月丙子到许州故寨，向周岌求粮未得，于是经陕渡河回晋阳。',[('李克用','回晋阳者'),('周岌','以粮缺为由拒绝者')],excerpt(15,'丙子，克用至许州故寨','乃自陕济河还晋阳。'))
# p016-018: 鹿头关 campaign and separate execution of Yang Maoyan.
event('gao_lutou_night','高仁厚在鹿头关夜袭中击退东川军',16,'中和四年五月丁丑夜','鹿头关','郑君雄、张士安夜袭高仁厚营寨，杨茂言等弃寨；高仁厚设伏击退东川军。',[('郑君雄','夜袭者'),('张士安','夜袭者'),('高仁厚','设伏击退者'),('杨茂言','弃寨者')],excerpt(16,'郑君雄、张士安坚壁不出','斩获甚众而还。'))
event('yang_maoyan_exec','高仁厚处决杨茂言',16,'中和四年五月丁丑夜后翌晨','鹿头关','高仁厚以弃寨逃走、其后欺瞒为由处决行军副使杨茂言；其余逃散士卒获召回。',[('高仁厚','处决者'),('杨茂言','被处决者'),('张韶','奉命召回逃卒者')],excerpt(16,'仁厚念诸弃寨走者','命左右扶下，斩之，'))
event('shi_pu_pursuit','时溥遣李师悦追黄巢',17,'中和四年五月庚辰',None,'时溥遣李师悦领兵万人追击黄巢。',[('时溥','遣兵者'),('李师悦','领兵追击者'),('黄巢','被追击者')])
event('lutou_victory','高仁厚击败郑君雄并进围梓州',18,'中和四年五月癸未','鹿头关、梓州','高仁厚在鹿头关佯败诱敌、设伏击败郑君雄等；敌军当夜退回梓州。陈敬瑄增兵三千，进围梓州。',[('高仁厚','伏击者'),('郑君雄','战败者'),('陈敬瑄','增兵者')],Q[18]['text'])
# Preserve original passage order, including events whose year remains uncertain.
for n in range(8,19):
 paras[n-1]['status']='reviewed';paras[n-1]['event_keys']=used.get(n,[]);paras[n-1]['batch_key']=B['batch_key']
 assert used.get(n),f'Unprocessed paragraph {n}'
paras[7]['review']='首事归年条；“后月馀”“久之”及后续舒、庐事未强定884年。陈儒为舒州攻城者。'
paras[10]['review']='五月雨、繁台、王满渡、归降及追击拆分；“充州”疑为转录讹误，不据此定位。'
paras[12]['review']='围驿与杨彦洪被射杀分别记录；官军死者人数保留原文，不强迫并为一事。'
paras[13]['review']='朱全忠回信是单方辩解，不能覆盖前段围驿史事。'
paras[14]['review']='养子关系为追叙，发生年份不明；仅李克用返回晋阳据五月丙子定位。'
paras[15]['review']='鹿头关夜袭与高仁厚翌晨处决杨茂言分开。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8,19):paras[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR_DIR/'paragraphs.json').write_text(json.dumps(paras,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps({'book':'资治通鉴','volume':255,'year':884,'primary_source_key':source,'paragraphs':[Q[n]['id'] for n in range(8,19)],'next_paragraph':'zztj-v256-y0884-p001','coverage':'卷255的884年剩余十一段；年条继续于卷256。','supplements':[],'status':status},ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
