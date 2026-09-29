"""Editorial decisions for 907; regenerate the reviewable draft, never writes to DB."""
import json,hashlib,shutil
from pathlib import Path
D=Path(__file__).resolve().parent; ROOT=D.parents[1]
old=json.loads((D.parent/'later-liang-907-923/content-batch.json').read_text()); paragraphs=json.loads((D/'paragraphs.json').read_text()); P={i:r['text'] for i,r in enumerate(paragraphs)}
b={'format_version':1,'batch_key':'year-0907-v1',**{k:[] for k in ['people','events','person_events','person_relationships','sources','claims','topics']}}
existing_names={x['name']:x for x in old['people']}; people={}; evmap={}; decisions={}; source='tongjian-user-266-v1'
b['sources'].append(dict(key=source,title='资治通鉴·卷266（用户提供TXT）',source_type='digital',author='司马光等',edition='用户提供爱上阅读TXT，底本未注明；2026-09-29固定快照',url='https://www.isyd.net',note='网站网址仅为文件自称来源，不是已验证的逐卷阅读链接。引用按本批tj266-907-p编号定位；原文件及分卷哈希见resources/catalog。文本含疑似转录错误，未经纸本校勘。'))
serial=0
def claim(table,key,field,statement,ps,note='按指定电子文本逐段整理；907年条中的前事与泛论不据此强行断年；尚待人工审阅。'):
 global serial
 for n in ps:
  serial+=1;b['claims'].append(dict(key=f'claim_0907_{serial:04d}',subject_table=table,subject_key=key,field_path=field,claim_text=statement,source_key=source,citation=f'卷266·开平元年条·tj266-907-p{n:03d}',note='原文：'+P[n]+'；核对说明：'+note,status='draft'))
def person(name,n,role,event_title):
 if name in people:return people[name]
 if name in existing_names:row=dict(existing_names[name])
 else:row=dict(key='person_'+name,name=name,aliases=[],era='唐末五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》907年条所记人物。在“{event_title}”中为{role}。本批仅整理相关史事，生卒与完整履历待补。',biography=None,status='draft')
 people[name]=row['key'];b['people'].append(row)
 if name not in existing_names:claim('person',row['key'],'description',row['description'],[n])
 return row['key']
def event(code,title,ps,time,place,description,participants,year=907,existing=None):
 key=existing or 'event_0907_'+code
 if existing:row=dict(next(x for x in old['events'] if x['key']==existing))
 else:row=dict(key=key,title=title,start_year=year,end_year=year,time_original=time,dynasty='唐末五代十国',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='原文历史地名；未核定古城址、今地与坐标。' if place else '原文未直接确定单一地点，待核。',status='draft')
 b['events'].append(row);evmap[code]=key
 for n in ps:decisions.setdefault(n,[]).append(key)
 if not existing:
  claim('event',key,'description',description,ps)
  claim('event',key,'time_original',time,ps[:1])
  if year:claim('event',key,'start_year','据开平元年条的当年叙事定位为907年；保留原纪年，不换算公历月日。',[0])
  if place:claim('event',key,'location_name',place,ps[:1])
 for name,role,n in participants:
  pk=person(name,n,role,title)
  if existing=='event_liang_founded' and name=='朱温':continue # reuse the published ruler edge, do not duplicate
  rk='participation_0907_'+code+'_'+pk
  b['person_events'].append(dict(key=rk,person_key=pk,event_key=key,role=role,status='draft'));claim('person_event',rk,'role',f'{name}在“{title}”中的记录角色：{role}。',[n])
 return key
# Date precision deliberately stops at the month where the source has doubtful day characters.
event('beizhou','梁王在贝州休兵',[1],'唐天祐四年正月辛巳','贝州','《通鉴》记梁王在贝州休兵。',[('朱温','休兵者',1)])
event('huainan_coup','张颢、徐温发动兵谏，控制淮南军政',[4],'唐天祐四年正月（原文干支作丙戍，待校）',None,'张颢、徐温率牙兵进入杨渥治事之所，杀其亲信，并逐步控制军政。段首所述诛杀三将等前事另列待核，不全部断为当日。',[('杨渥','受制者',4),('张颢','事变组织者',4),('徐温','事变组织者',4)])
event('persuade','罗绍威劝梁王灭唐，薛贻矩往返传达禅位意向',[5],'唐天祐四年正月','魏、大梁','罗绍威劝梁王尽早灭唐；唐昭宣帝遣薛贻矩至大梁，薛归后报告梁王有受禅之意，唐帝随后提出禅位，梁王辞让。',[('朱温','受劝进者',5),('罗绍威','劝进者',5),('薛贻矩','使者',5),('唐昭宣帝','遣使者',5)])
event('jinzhou_defense','康怀贞奉命屯晋州防备河东军',[6],'唐天祐四年正月条，具体日未载','晋州','梁王命康怀贞征发京兆、同华之兵屯晋州，以防备欲进攻泽州的河东军。',[('朱温','发令者',6),('康怀贞','领兵者',6)])
event('abdication_petitions','唐廷与各镇相继向梁王劝进',[7,9,11],'唐天祐四年二月至三月','大梁','唐廷组织百官劝进，三月再遣使传达禅位之意，并安排册礼、传国宝与金宝的奉送人员。杨凝式劝父杨涉辞去送玺之事。',[('朱温','受禅对象',7),('唐昭宣帝','发诏者',9),('薛贻矩','奉使者',9),('苏循','奉使者',9),('张文蔚','册礼使',11),('杨涉','押传国宝使',11),('张策','押传国宝副使',11),('赵光逢','押金宝副使',11),('杨凝式','劝谏者',11)])
event('youzhou_campaign','李思安进攻幽州，被刘守光击退',[8,13],'唐天祐四年三月至四月己酉','幽州','李思安奉梁王命领兵进攻幽州。四月抵城时刘仁恭不在城中，刘守光入城拒守并击退李思安。',[('朱温','发令者',8),('李思安','进攻者',8),('刘守光','守城者',13),('刘仁恭','卢龙节度使',13)])
event('liuren_captured','刘守光夺取卢龙军权并囚禁刘仁恭',[13],'唐天祐四年四月条','幽州、大安山','刘守光击退李思安后自称节度使，遣李小喜、元行钦进攻大安山，擒获并囚禁父亲刘仁恭。',[('刘守光','夺权者',13),('刘仁恭','被囚者',13),('李小喜','进攻者',13),('元行钦','进攻者',13)])
event('youzhou_exiles','王思同、李承约等离开幽州投奔河东',[13],'唐天祐四年四月条，先后间隔未详','河东','刘守光夺权后，王思同、李承约率部投奔河东；刘守奇先奔契丹，后亦奔河东。李克用任命李承约与王思同。',[('王思同','归附者',13),('李承约','归附者',13),('刘守奇','归附者',13),('李克用','接纳者',13)])
event('wenzhou','钱氏军队攻取温州，卢佶被杀',[10,15],'唐天祐四年三月至四月戊午','温州、青澳、安固','钱镠遣钱传镣、钱传瓘讨卢佶。钱传瓘避开青澳守军，自安固取道袭温州，城破后卢佶被擒杀；吴璋受命处理温州事务，钱氏军队转攻处州。',[('钱镠','发令者',10),('钱传镣','出征者',10),('钱传瓘','出征者',10),('卢佶','守方首领',10),('吴璋','温州制置使',15)])
event('remove_tang_era','梁王受百官称臣，下令公文去唐年号',[14],'唐天祐四年四月庚戌、辛亥','金祥殿','梁王在金祥殿受百官称臣，随后令笺表簿籍去除唐年号，仅记月日。',[('朱温','发令者',14),('张文蔚','到达大梁的使者',14)])
event('rename_zhu','朱温在即位前更名晃',[16],'唐天祐四年四月壬戌',None,'梁王在即位前更名晃；原文并记其兄朱全昱对称帝提出质问。',[('朱温','更名者',16),('朱全昱','质问者',16)])
event('founded','朱温称帝，后梁建立',[17],'唐天祐四年／梁开平元年四月甲子、戊辰','大梁','复用首批已存在的后梁建立事件。',[('朱温','统治者',17),('张文蔚','奉册者',17),('苏循','奉册者',17),('杨涉','奉宝者',17),('张策','奉宝者',17),('薛贻矩','奉宝者',17),('赵光逢','奉宝者',17),('唐昭宣帝','被降为济阴王者',17),('朱全昱','宗室在场者',17),('张祎','在场称贺者',17)],existing='event_liang_founded')
event('ma_chu','后梁封马殷为楚王',[18],'梁开平元年四月辛未',None,'后梁以武安节度使马殷为楚王。封号不等于后梁实际直接控制其辖地。',[('朱温','封授者',18),('马殷','受封者',18)])
event('jingxiang','敬翔主持崇政院，枢密院职事并入',[19,34],'梁开平元年四月至五月甲午',None,'敬翔先知崇政院事，负责承宣旨意及顾问谋议；五月后梁废枢密院，职事并入崇政院，以敬翔为院使。',[('朱温','任命者',19),('敬翔','受命者',19)])
event('ancestors','朱温追尊先祖及父母',[20],'梁开平元年四月条，具体日未载',None,'朱温追尊高祖以来的先人，尊父朱诚为烈祖文穆皇帝，母王氏为文惠皇后。本事件是追尊行为，不据此新增先人的在世活动。',[('朱温','追尊者',20)])
event('youwen','朱友文出任开封尹并主持建昌院',[21,32],'梁开平元年四月至五月辛卯','开封','朱温以养子朱友文为开封尹、判建昌院事，掌财政事务。五月建昌院改为建昌宫，相关职名随之改为建昌宫使。',[('朱温','任命者',21),('朱友文','受命者',21)])
event('revoke_keyong','后梁削夺李克用官爵',[22],'梁开平元年四月乙亥',None,'后梁下制削夺李克用官爵。原文同时记河东等地仍用唐年号，显示各地对后梁正朔的接受并不一致。',[('朱温','发令者',22),('李克用','被削官爵者',22)])
event('shujin_letters','蜀王与晋王讨论讨梁及称帝',[22],'907年后梁建立后条，具体日期未载',None,'蜀王致书晋王，提出各帝一方、平梁后再立唐宗室；李克用回书不许。本事件只记录书信提议，不据此建立已成形的军事同盟。',[('王建','致书提议者',22),('李克用','回书拒绝者',22),('杨渥','参与移檄者',22)])
event('zhang_chengye','李克用复用张承业为监军',[23],'907年后梁建立后条，具体日期未载','河东','李克用重新任用张承业为监军。段首保护张承业之事属于唐末追叙，不定为907年新事件。',[('李克用','任用者',23),('张承业','受任者',23)])
event('qi_court','岐王在唐亡后开府置百官',[24],'907年闻唐亡后，具体日期未载',None,'岐王在唐亡后没有称帝，但开府置百官，多项礼仪仿照帝制。段首有关治军的轶事不强行断为本年。',[('李茂贞','开府者',24)])
event('luoyin','罗隐劝钱镠讨梁，钱镠未采纳',[25],'907年后梁建立后条，具体日期未载',None,'罗隐劝钱镠出兵讨梁；原文记钱镠未能采用该建议。',[('罗隐','劝谏者',25),('钱镠','受谏者',25)])
event('xue_pm','薛贻矩出任中书侍郎、同平章事',[26],'梁开平元年五月丁丑朔',None,'后梁以薛贻矩为中书侍郎、同平章事。',[('朱温','任命者',26),('薛贻矩','受任者',26)])
event('hebei_titles','后梁加授王镕、罗绍威、王处直官衔',[27],'梁开平元年五月条，具体日未载',None,'后梁加授王镕、罗绍威、王处直官衔。用户TXT中“王镕宁太师”有疑字，王镕具体官衔暂不订正。',[('朱温','加授者',27),('王镕','受授者',27),('罗绍威','受授者',27),('王处直','受授者',27)])
event('khitan_envoys','契丹与后梁互遣使者通好',[28],'梁开平元年五月条，具体日未载',None,'契丹遣袍笏梅老通好，后梁遣高颀回访。本段后续契丹沿革和会盟叙事另列待核，未并入此次使行。',[('袍笏梅老','契丹使者',28),('高颀','后梁使者',28),('朱温','遣返聘使者者',28)])
event('southern_titles','后梁加封钱镠、张全义、刘隐等',[29],'梁开平元年五月己卯',None,'后梁封张全义为魏王、钱镠为吴越王；加刘隐、王审知兼侍中，封刘隐为大彭王。',[('朱温','封授者',29),('张全义','受封者',29),('钱镠','受封者',29),('刘隐','受封者',29),('王审知','受授者',29)])
event('gao_jingnan','高季昌受命为荆南节度使',[30],'梁开平元年五月癸未','荆南、江陵','后梁以高季昌为荆南节度使；原文记其到任后安集流散人口。江陵恢复的过程不压缩为任命当天完成。',[('朱温','任命者',30),('高季昌','受任者',30)])
event('zhu_princes','后梁封朱全昱及诸子为王',[31],'梁开平元年五月乙酉',None,'后梁封朱全昱为广王，朱友文为博王、朱友珪为郢王、朱友璋为福王、朱友贞为均王、朱友雍为贺王、朱友徽为建王；朱友文的养子身份另据前文记录。',[(n,'受封者',31) for n in ['朱全昱','朱友文','朱友珪','朱友璋','朱友贞','朱友雍','朱友徽']]+[('朱温','封授者',31)])
event('luzhou_siege','梁军围攻潞州，晋军出兵救援',[33,39],'梁开平元年五月至六月条','潞州','康怀贞奉命攻潞州；李嗣昭、李嗣弼守城。梁军久攻不克，转为筑垒围困；李克用命周德威等救援。这是907年围城与救援，与既有908年解围事件分别记录。',[('朱温','发令者',33),('康怀贞','围城者',33),('李嗣昭','守城者',39),('李嗣弼','守城者',39),('李克用','救援发令者',39)]+[(n,'救援将领',39) for n in ['周德威','李嗣本','李存璋','史建瑭','安元信','李嗣源','安金全']])
event('su_retired','后梁勒令苏循、张祎等致仕',[35],'梁开平元年五月（干支原文作戊戍，待校）',None,'后梁勒令苏循、张祎等十五人致仕，将苏楷斥归田里；苏循父子后依朱友谦。',[('朱温','发令者',35),('苏循','被勒致仕者',35),('张祎','被勒致仕者',35),('苏楷','被斥归者',35),('敬翔','建言者',35),('李振','议论者',35),('朱友谦','接纳者',35)])
event('chuzhou_surrender','卢约以处州归降吴越',[36],'907年五月条，具体日未载','处州','卢约以处州归降吴越。',[('卢约','归降者',36),('钱镠','归降对象',36)])
event('chu_huainan','楚军击败刘存等淮南水军，攻取岳州',[37],'907年五月出兵、六月交战','越堤、浏阳口、岳州','杨渥遣刘存等攻楚；秦彦晖、黄璠合击淮南军，刘存、陈知新被俘后遭马殷处死，刘威退走。秦彦晖随后取岳州。兵力与伤亡数字暂不结构化。',[('杨渥','发令者',37),('刘存','淮南统帅',37),('陈知新','淮南将领',37),('刘威','淮南应援使',37),('许玄应','淮南监军',37),('马殷','楚方发令者',37),('秦彦晖','楚方统帅',37),('黄璠','楚方将领',37),('杨定真','建言者',37)])
event('xu_executed','张颢、徐温在败战后处死许玄应',[37],'907年六月败战后，具体日未载',None,'淮南军攻楚失败后，张颢、徐温收捕并处死弘农王腹心许玄应。与战场上处死刘存、陈知新分开记录。',[('张颢','下令者',37),('徐温','下令者',37),('许玄应','被杀者',37)])
event('hongzhou','楚军与彭玕进攻洪州未克',[38],'907年六月条，具体日未载','洪州','马殷遣军与吉州刺史彭玕会攻洪州，未能攻克。',[('马殷','遣军者',38),('彭玕','进攻者',38)])
event('zezhou','范居实奉命救援泽州',[40],'梁开平元年六月条，具体日未载','泽州','晋军攻泽州，后梁遣范居实领兵救援。',[('朱温','发令者',40),('范居实','救援者',40)])
event('hanjian','韩建出任司徒、同平章事',[41],'梁开平元年六月甲寅',None,'后梁以平卢节度使韩建守司徒、同平章事。',[('朱温','任命者',41),('韩建','受任者',41)])
event('jiangling','高季昌断粮击退雷彦恭与楚军',[42],'907年六月条，具体日未载','江陵、公安','雷彦恭与楚军进攻江陵，高季昌屯公安并切断对方粮道，雷彦恭败退，楚军亦退。',[('雷彦恭','进攻者',42),('高季昌','守方统帅',42)])
event('liushouguang_confirmed','后梁授刘守光卢龙节度使',[43],'梁开平元年七月甲午',None,'刘守光囚父、自称留后后向后梁请命，获授卢龙节度使、同平章事。',[('朱温','任命者',43),('刘守光','受任者',43)])
event('quhao','曲颢继曲裕为静海节度使',[44],'梁开平元年七月丙申','静海','曲裕死后，其子曲颢由权知留后受命为静海节度使。人名按本次所用《通鉴》文本保留，异名待查。',[('曲裕','前任节度使',44),('曲颢','继任者',44),('朱温','任命者',44)])
event('leiyuezhou','雷彦恭进攻岳州未克',[45],'907年七月条，具体日未载','岳州','雷彦恭进攻岳州，未能攻克。',[('雷彦恭','进攻者',45)])
event('zhang_rename','后梁赐张全义名宗奭',[46],'梁开平元年八月丙午',None,'后梁赐河南尹张全义名宗奭。',[('朱温','赐名者',46),('张全义','受赐名者',46)])
event('qian_ma_commissions','后梁令钱镠、马殷兼领淮南与武昌军职',[47],'梁开平元年八月辛亥',None,'后梁以钱镠兼淮南节度使、马殷兼武昌节度使，并授招讨制置职任。这里只记录授官，不表示二人已实际占有对应辖区。',[('朱温','任命者',47),('钱镠','受任者',47),('马殷','受任者',47)])
event('gaohe','周德威在高河击败秦武',[48],'907年八月条，具体日未载','高河','康怀贞遣秦武进攻屯高河的周德威，秦武战败。',[('周德威','晋方将领',48),('康怀贞','遣军者',48),('秦武','梁方将领',48)])
event('jiazai','李思安接掌潞州围军，修筑夹寨',[49],'梁开平元年八月（干支原文作丁已，待校）','潞州','李思安代康怀贞为潞州行营都统，修筑内外夹城及运粮甬道。周德威等反复袭扰，使梁军受困。',[('朱温','换将者',49),('李思安','新任统帅',49),('康怀贞','降职者',49),('周德威','袭扰者',49)])
event('lei_revoked','雷彦恭再攻荆南失利，被后梁削爵讨伐',[50],'梁开平元年九月丙申及此前','涔阳、公安','雷彦恭进攻涔阳、公安，被高季昌击退。后梁削其官爵，命高季昌与马殷讨伐。',[('雷彦恭','被讨伐者',50),('高季昌','击退与奉讨者',50),('马殷','奉讨者',50),('朱温','发令者',50)])
event('shu_founded','王建称帝，建立前蜀',[51],'907年九月己亥',None,'王建未采用冯涓建议称制的意见，采韦庄之谋称帝，国号大蜀；本项目用“前蜀”区分后来的后蜀。',[('王建','称帝者',51),('冯涓','献议者',51),('韦庄','谋议者',51)])
event('shu_officials','前蜀任命王宗佶、韦庄、唐道袭',[51],'907年九月辛丑',None,'王建称帝后任命王宗佶为中书令、韦庄判中书门下事、唐道袭为内枢密使；并封王宗懿为遂王，封王具体日未载。',[('王建','任命者',51),('王宗佶','受任者',51),('韦庄','受任者',51),('唐道袭','受任者',51),('王宗懿','受封者',51)])
event('langzhou','荆南、楚军攻朗州，许德勋击败淮南援军',[52],'907年十月','朗州、朗口、浏阳、长沙','高季昌遣倪可福会秦彦晖攻朗州。杨渥遣泠业、李饶救雷彦恭，马殷遣许德勋迎击；淮南援军战败，泠业、李饶被俘后在长沙处死。',[('高季昌','遣军者',52),('倪可福','进攻者',52),('秦彦晖','进攻者',52),('雷彦恭','求援者',52),('杨渥','援军发令者',52),('泠业','淮南援将',52),('李饶','淮南援将',52),('马殷','楚方遣军者',52),('许德勋','楚方统帅',52)])
event('jiangzhuling','尹皓攻取晋军江猪岭寨',[53],'梁开平元年十一月甲申','江猪岭寨','夹马指挥使尹皓攻取晋军江猪岭寨。',[('尹皓','进攻者',53)])
event('liu_brothers','刘守文起兵攻打刘守光',[54],'907年十一月条，具体日未载',None,'刘守文得知弟弟刘守光囚父后起兵进攻，双方互有胜负。',[('刘守文','进攻者',54),('刘守光','交战者',54)])
event('liushouwen_surrender','罗绍威劝刘守文归梁，刘延祐入质',[55],'梁开平元年十一月戊子',None,'罗绍威致书刘守文劝其归梁。刘守文遣使请降，送子刘延祐为质；后梁加授其中书令。',[('罗绍威','劝降者',55),('刘守文','归附者',55),('刘延祐','入质者',55),('朱温','接纳者',55)])
event('deserters_amnesty','后梁赦免逃亡军士，许文面者还乡',[56],'梁开平元年十一月壬寅',None,'后梁赦免逃亡军士，允许有军号刺字者还乡。此前跋队斩和刺字制度为段首追叙，不作为本年新设制度；盗贼减少比例不结构化。',[('朱温','发诏者',56)])
event('yingzhou','米志诚袭颍州，梁援军出动后退兵',[57,59],'907年十一月至十二月甲子','颍州','米志诚率淮南军攻取颍州外郭，张实守子城。后梁十二月发援军，米志诚等退兵。',[('米志诚','进攻者',57),('张实','守城者',57),('朱温','遣援者',59)])
event('jinzhou_attack','李存璋攻晋州，后梁令河中、陕州救援',[58],'907年十一月至十二月壬戌','晋州','李克用命李存璋攻晋州，以分散上党方面的梁军；后梁命河中、陕州出兵救援。',[('李克用','发令者',58),('李存璋','进攻者',58),('朱温','救援发令者',58)])
event('mingzhou','晋军进攻洺州',[60],'907年十二月丁卯','洺州','《通鉴》记晋军进攻洺州，未在此段指明具体领兵者。',[])
event('xinzhou','淮南军攻信州，危仔倡向吴越求援',[61],'907年十二月条，具体日未载','信州','淮南军进攻信州，刺史危仔倡向吴越求援。',[('危仔倡','求援者',61),('钱镠','求援对象',61)])
# Directly attested personal relationships; no inferred allies from shared participation.
def relation(a,c,typ,desc,n):
 ak=person(a,n,typ,'原文亲属或任职记载');ck=person(c,n,typ,'原文亲属或任职记载');key=f'relationship_{ak}_{ck}_{typ}'
 b['person_relationships'].append(dict(key=key,person_a_key=ak,person_b_key=ck,relation_type=typ,description=desc,status='draft'));claim('person_relationship',key,'description',desc,[n])
for a,c,n in [('钱镠','钱传镣',10),('钱镠','钱传瓘',10),('杨涉','杨凝式',11),('刘仁恭','刘守光',13),('苏循','苏楷',35),('曲裕','曲颢',44),('刘守文','刘延祐',55),('王建','王宗懿',51),('朱温','朱友璋',31),('朱温','朱友雍',31),('朱温','朱友徽',31)]:relation(a,c,'父亲',f'{a}为{c}之父。原文见907年条；不据此推导持续政治支持。',n)
relation('朱温','朱友文','养父', '朱温为朱友文养父；原文明确称养子，并说友文本康氏之子。907年受任及封王不改变养子属性。',21)
relation('朱全昱','朱温','兄长','朱全昱为朱温兄长；本批依据907年改名与封王记载。',16)
relation('刘守文','刘守光','兄长','刘守文为刘守光兄长。907年因刘守光囚父，兄弟之间发生战争；亲属关系与政治敌对分开理解。',54)
relation('刘守光','刘守奇','兄长','原文称刘守奇为刘守光之弟；刘守奇在907年离开幽州。',13)
relation('李克用','张承业','任用者','907年条记李克用复用张承业为监军；这里只表达该阶段的任用关系。',23)
relation('朱温','敬翔','任用者','907年敬翔受命主持崇政院，承宣旨意、顾问谋议；关系范围限于本批任职记载。',19)
relation('高季昌','倪可福','统属者','907年十月高季昌遣其将倪可福参与攻朗州；仅据此记录当次军事统属。',52)
relation('杨渥','许玄应','主君','原文明确称许玄应为弘农王腹心、常预政事；本批只记录907年前后的依附关系。',37)
# Preserve existing IDs, statements and evidence; import skips these rows without modifying them.
reused={r['key'] for r in b['people'] if r['name'] in existing_names}|{'event_liang_founded'}
oldclaims=[dict(x) for x in old['claims'] if x['subject_key'] in reused]
b['claims'].extend(oldclaims);oldsourcekeys={x['source_key'] for x in oldclaims}
for x in old['sources']:
 if x['key'] in oldsourcekeys:b['sources'].append(dict(x))
oldmanifest=json.loads((D.parent/'later-liang-907-923/sources/manifest.json').read_text());manifest=[]
for m in oldmanifest:
 if m['key'] in oldsourcekeys:
  shutil.copy2(D.parent/'later-liang-907-923/sources'/m['file'],D/'sources'/m['file']);manifest.append(m)
# Identity checks and an independent account of the Shu accession, using archived PDF text.
pdfrows=[json.loads(l) for l in (ROOT/'resources/derived/twenty-four-histories/19新五代史.jsonl').read_text().splitlines()]
checks=[(1344,'person','person_王建','description','本批“蜀王”对应前蜀王建；《新五代史》前蜀世家列其姓名。'),(1353,'event',evmap['shu_founded'],'description','《新五代史》亦记王建于九月己亥即皇帝位，与通鉴本段称帝日期相合。'),(1497,'person','person_高季昌','aliases','高季兴本名季昌，本批采用907年的名字高季昌；高季兴作为检索异名。')]
# Find the page that explicitly calls Li Maozhen King of Qi.
qipage=next(x for x in pdfrows if 722<=x['pdf_page']<=734 and '岐王' in x['text'])
checks.append((qipage['pdf_page'],'person','person_李茂贞','description','本批“岐王”对应李茂贞；《新五代史》李茂贞传记其受封岐王。'))
pdfkey='xinwudaishi-github-20260929';pp=D/'sources/xinwudaishi-identity-excerpts.txt';pp.write_text('\n\n'.join(f'PDF第{n}页\n'+pdfrows[n-1]['text'] for n in sorted({x[0] for x in checks})))
meta=json.loads((ROOT/'resources/catalog/twenty-four-histories.json').read_text());url=next(x['url'] for x in meta if x['title']=='新五代史')
b['sources'].append(dict(key=pdfkey,title='新五代史（GitHub电子排印本）',source_type='digital',author='欧阳修',edition='grimoire-kindle仓库固定提交cc24276；电子排印本，底本待考',url=url,note='按PDF实际页码定位，非古籍原叶码；完整文件哈希见resources/catalog。'))
for n,table,key,field,statement in checks:
 serial+=1;b['claims'].append(dict(key=f'claim_0907_{serial:04d}',subject_table=table,subject_key=key,field_path=field,claim_text=statement,source_key=pdfkey,citation=f'PDF第{n}页',note='原文：'+pdfrows[n-1]['text']+'；核对说明：按PDF文字层提取核对；版式断行保留，未作纸本校勘。',status='draft'))
next(x for x in b['people'] if x['name']=='高季昌')['aliases']=['高季兴']
for key,file in [(source,'tongjian-266-user.txt'),(pdfkey,pp.name)]:
 raw=(D/'sources'/file).read_bytes();manifest.append(dict(key=key,file=file,sha256=hashlib.sha256(raw).hexdigest(),accessed_at='2026-09-29',url=next(x['url'] for x in b['sources'] if x['key']==key)))
# Explicit paragraph coverage including deferred background; no silent omissions.
notes={0:'年次标题，用于当年叙事的年份依据。',2:'杨渥杀周隐：上下文可能追叙前事；需对读前卷及吴世家，暂不录为907年事件。',3:'吕师周奔湖南：缺少独立日期；待核后决定是否编入907年。',4:'兵谏主体已录；诛杀三将等前史、奢侈描写与动机判断暂不单独断年。',5:'只提取当年劝进与使行；段首此前战事不重定为907年。',12:'刘仁恭营建与钱茶政策为背景叙述，时间不明，暂不录为907年事件。',13:'囚父、将领出走与亲属关系已录；罗氏相关私事和难辨官名暂不结构化。',20:'追尊行为已录；未将追尊的先人误作当年在世人物。',22:'正朔差异保留叙述；政治提议不转成已成立的盟约。',23:'仅复任监军录为本年；此前藏匿监军为追叙。',24:'仅闻唐亡后的开府行为列本年；前半轶事时间待核。',27:'王镕官衔疑字未订正，保留待核。',28:'只录契丹梁使行；契丹制度沿革、阿保机会晋王及背盟另留待核，不能整段认作907年。',37:'大战与许玄应被杀分开；未采信伤亡数字为结构化数量。',39:'参战者已建；追叙李嗣弼父李克修、史建瑭父史敬思及李嗣本改姓线索保留候选，待人物本传核验。',49:'干支“丁已”待校，界面仅用年；不自动纠为丁巳。',51:'称帝与任命分别建事件；韦庄祖父关系、王宗仁生平留作待核线索。',56:'赦令为本年；跋队斩与刺字制度为追叙，不录作当年创立。'}
ledger=[]
for i,p in enumerate(paragraphs):ledger.append(dict(**p,event_keys=decisions.get(i,[]),disposition='已转换，附待核事项' if i in decisions and i in notes else '已转换' if i in decisions else '纪年依据' if i==0 else '待核暂缓',note=notes.get(i,'按原文提取事件与有名参与者；不虚构未具名人物。')))
b['topics']=[dict(key='topic_year_0907',slug='year-907',title='907年：唐亡后的各地政局',description='逐段整理通鉴907年条，涵盖后梁建立与同期河东、淮南、吴越、蜀等地史事。底稿待审阅。',sections=[dict(heading='按原文顺序阅读907年',body='条目按原文顺序整理；原纪年保留月与干支，网站年份精度为年。追叙、疑字和未定年的内容单列待核，不强行归入本年。',node_keys=[x['key'] for x in b['events']])],status='draft')]
(D/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(D/'content-batch.json').write_text(json.dumps(b,ensure_ascii=False,indent=2));(D/'paragraph-review.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2));(D/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2))
review=['# 907年逐段分析稿','','所有新增条目为草稿；引用核验不是版本校勘或史实无误保证。','', '## 数量','']+[f'- {k}: {len(b[k])}' for k in b if isinstance(b[k],list)]+['','## 逐段处理','']
for l in ledger:
 review += [f'### {l["id"]} · {l["disposition"]}', '', '> '+l['text'],'',l['note'],'']
 for key in l['event_keys']:
  e=next(x for x in b['events'] if x['key']==key);review += [f'**{e["title"]}** · {e["time_original"]}',e['description'],'']
review+=['## 人物关系','']+[f'- {x["description"]}' for x in b['person_relationships']]
(D/'review.md').write_text('\n'.join(review)+'\n')
print({k:len(v) for k,v in b.items() if isinstance(v,list)});print('Reused',len(reused),'Paragraphs',len(ledger))
