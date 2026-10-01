"""Curate consecutive Tongjian volume 261, year 897 paragraphs 13–24."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 51))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0897-p013-p024', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-897-p013-p024'
fixed_commit='154365a'
reused_source_keys=set()
source_specs=[(source,'资治通鉴·卷261·乾宁四年第13—24段','司马光等'),('xintangshu-188-897-jiaxing','新唐书·卷188·嘉兴之战','欧阳修、宋祁等'),('xintangshu-186-897-dongchuan','新唐书·卷186·李洵宣谕及东川战事','欧阳修、宋祁等'),('jiuwudaishi-019-897-qu-zhang','旧五代史·卷19·朱友恭黄州战事','薛居正等'),('jiuwudaishi-055-gai-yu','旧五代史·卷55·盖寓传','薛居正等')]
manifest=[]
for sk,title,author in source_specs:
    if sk==source:
        records=[json.loads((P/'sources/library'/part/'paragraph.json').read_text()) for part in ['tongjian-spring-a','tongjian-spring-b']];filename='tongjian-261-897-p013-p024.txt';citation='《资治通鉴》卷261乾宁四年；原TXT连续段落 '+ '、'.join(r['id'] for r in records)
    else:
        records=[json.loads((P/'sources/library'/sk/'paragraph.json').read_text())];filename='library/'+sk+'/source.txt';citation=records[0]['citation']
    snapshot=P/'sources'/filename;url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str(snapshot.relative_to(ROOT))
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=citation))
    manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),url=url,paragraph_ids=[r['id'] for r in records],upstream_locators=[r['locator'] for r in records],transformation='主书相邻两份导出TXT按原字节拼接；补书逐字导出，保留底本与定位。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in range(13,25):assert Q[n]['text'] in (P/'sources/tongjian-261-897-p013-p024.txt').read_text()
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, set(reused_source_keys)
alias.update({'王宗播':'许存','杜弘':'杜洪','嵩从周':'葛从周','硃瑾':'朱瑾','硃宣':'朱瑄','李继徽':'杨崇本','硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0897_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷261·乾宁四年（897）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷261乾宁四年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=897,note=None,quote=None):
    key='event_zztj_261_0897_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_261_0897_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None,year=897):
    return event(code,title,n,when or '897年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note,year=year)
e('li_jitang_kuangguo_governor','李继瑭任匡国节度使',13,'夏，四月，以同州防御使李继瑭为匡国节度使。继瑭，茂贞之养子也。',[('李继瑭','受节度使者')],when='897年四月；确日未载',place='同州、匡国军',note='防御使升节度有原句；养子另建方向，不补养父收养年份。')
e('li_xun_two_chuan_mediation','李洵受两川宣谕使命和解王建顾彦晖',14,'以右谏议大夫李洵为两川宣谕使，和解王建及顾彦晖。',[('李洵','受宣谕者'),('王建','被和解对象'),('顾彦晖','被和解对象')],when='897年四月；确日未载',place='两川',note='和解是使令目的，不作双方已停战；新唐书左谏议官称保异记。')
e('qian_sends_gu_three_thousand_sea','钱镠遣顾全武三千兵从海道救嘉兴',15,'辛亥，钱镠遣顾全武等将兵三千自海道救嘉兴',[('钱镠','遣援者'),('顾全武','领兵者')],when='897年四月辛亥',place='海道、嘉兴',note='三千保主书记数，不推船数或精确航线。')
e('gu_arrives_jiaxing_defeats_huainan','顾全武至嘉兴城下大破淮南兵',15,'己未，至城下，击淮南兵，大破之。',[('顾全武','援胜者')],when='897年四月己未',place='嘉兴城下')
e('du_hong_requests_zhu_aid','杜洪被杨行密攻，求救朱温',16,'杜洪为杨行密所攻，求救于硃全忠。',[('杜洪','求援者'),('杨行密','攻方主帅'),('朱温','被请求者')],when='897年四月；确日未载',place='武昌',note='求援不建永久联盟或后梁臣属。')
e('nie_jin_raids_sizhou','朱温遣聂金掠泗州',16,'全忠遣其将聂金掠泗州',[('朱温','遣将者'),('聂金','领掠者')],when='897年四月杜洪求援后；确日未载',place='泗州',note='掠不写州城陷落，不补伤亡。')
e('zhu_yougong_attacks_huangzhou','朱友恭奉命攻黄州',16,'硃友恭攻黄州。',[('朱温','遣攻者'),('朱友恭','攻将')],when='897年四月杜洪求援后；确日未载',place='黄州')
e('yang_sends_ma_xun_relief','杨行密遣马珣等救黄州',16,'行密遣右黑云都指挥使马珣等救黄州。',[('杨行密','遣援者'),('马珣','右黑云都指挥使')],when='897年四月；确日未载',place='黄州',note='马珣独立人物，不因马姓并入马殷或马道殷。')
e('qu_zhang_abandons_huang_wuchang','瞿章闻朱友恭来，弃黄州拥众保武昌寨',16,'黄州刺史瞿章闻友恭至，弃城，拥众南保武昌寨。',[('瞿章','退保者')],when='897年四月朱友恭进攻时；确日未载',place='黄州、武昌寨',note='武昌寨是退保寨，不当杜洪所治武昌军已陷；不補人数。')
e('gu_breaks_eighteen_camps_captures_wei','顾全武破十八营，俘魏约等三千',17,'癸亥，两浙将顾全武等破淮南十八营，虏淮南将士魏约等三千人。',[('顾全武','攻胜俘人者'),('魏约','被俘将')],when='897年四月癸亥',note='十八营、三千为主书计数；不把每营都换成现代固定编制。')
e('tian_station_yiting_zhe_pursuit','田頵屯驿亭埭，两浙军乘胜追逐',17,'淮南将田頵屯驿亭埭，两浙兵乘胜逐之。',[('田頵','屯驻被追者')],when='897年四月癸亥战后；确日未另载',place='驿亭埭',note='本句未明言追军具名将，不凭此前顾全武名字补全部参与。')
e('tian_leaves_huzhou_chased_losses','田頵由湖州奔还，追败部众死千余',17,'甲戌，頵自湖州奔还，两浙兵追败之，頵众死者千馀人。',[('田頵','奔还败者')],when='897年四月甲戌',place='湖州',note='千余是记数，未记田本人被杀或被俘。')
e('han_false_accuses_demotes_zhang_yi','韩建诬奏贬张祎等',18,'韩建恶刑部尚书张祎等数人，皆诬奏，贬之。',[('韩建','诬奏者'),('张祎','被贬者')],when='897年四月；确日未载',note='诬奏按主书归述，不建立张祎真实犯罪；贬后具体官地未载。')
e('cui_hong_added_pingzhang','崔洪加同平章事',19,'五月，加奉国节度使崔洪同平章事。',[('崔洪','受加官者')],when='897年五月；确日未载',place='奉国军')
e('yougong_bridge_fangang_attacks','朱友恭造樊港浮梁进攻武昌寨',20,'辛巳，硃友恭为浮梁于樊港，进攻武昌寨',[('朱友恭','造梁攻者')],when='897年五月辛巳',place='樊港、武昌寨')
e('yougong_takes_wuchang_captures_qu','朱友恭拔武昌寨，执瞿章',20,'壬午，拔之，执瞿章',[('朱友恭','拔寨者'),('瞿章','被执者')],when='897年五月壬午',place='武昌寨',note='拔之承武昌寨，不作武昌州城；旧五代史光化初获瞿章记法独立保留。')
e('yougong_takes_huangzhou','朱友恭继取黄州',20,'遂取黄州。',[('朱友恭','取州者')],when='897年五月壬午拔寨后；确日未另载',place='黄州')
e('ma_xun_defeated_flees','马珣等败走',20,'马珣等皆败走。',[('马珣','败走者')],when='897年五月取黄州时；确日未载',note='败走不写已被擒或死。')
e('zhang_lin_guards_chengdu','王建留张琳守成都',21,'丙戌，王建以节度副使张琳守成都',[('王建','留守安排者'),('张琳','守成都者')],when='897年五月丙戌',place='成都')
e('wang_jian_fifty_thousand_dongchuan','王建亲率五万攻东川',21,'自将兵五万攻东川。',[('王建','亲领攻者')],when='897年五月丙戌',place='东川',note='与二月遣华洪王宗祐的五万分别记原时点，不据人数相同断同一批兵或两批共十万。')
e('hua_hong_renamed_wang_zongdi','华洪更名王宗涤',21,'更华洪姓名曰王宗涤。',[('王建','改姓名者'),('华洪','被改姓名者')],when='897年五月丙戌条；确日未另载',note='既有华洪与王宗涤同一主体，附改名出处而不新建人。')
claim('person',people['王宗涤'],'aliases','华洪在本段被更姓名为王宗涤。',21,quote='更华洪姓名曰王宗涤。')
e('qian_yue_receives_zhendong_insignia','钱镠至越州受镇东节钺',22,'六月，己酉，钱镠如越州，受镇东节钺。',[('钱镠','受节钺者')],when='897年六月己酉',place='越州',note='本段是实际受节钺，与896年两军诏任区分；不写本年新设镇东军。')
e('mao_petitions_wang_disobedience','李茂贞上表指王建连兵不听诏',23,'李茂贞表：“王建攻东川，连兵累岁，不听诏命。”',[('李茂贞','表言者'),('王建','被表指者')],when='897年六月；甲寅前',note='连兵累岁不听诏为表陈词，不补精确开战日期。')
e('wang_jian_demoted_nanzhou','王建被贬南州刺史',23,'甲寅，贬建南州刺史。',[('王建','被贬者')],when='897年六月甲寅',place='南州',note='诏贬不作实际抵任南州或已失西川控制。')
e('mao_appointed_xichuan','李茂贞受西川节度使',23,'乙卯，加茂贞为西川节度使',[('李茂贞','受西川者')],when='897年六月乙卯',place='西川',note='名义授职，主书后称王仍作战，不写茂贞已进成都视事。')
e('qin_prince_fengxiang_governor','覃王李嗣周受凤翔节度使',23,'以覃王嗣周为凤翔节度使。',[('覃王嗣周','受凤翔者')],when='897年六月乙卯',place='凤翔',note='复用李嗣周；新唐书作嗣郯王戒丕，保人物异记，不合并李戒丕与李嗣周。')
e('wang_takes_zi_south_captures_jining','王建克梓州南寨执李继宁',23,'癸亥，王建克梓州南寨，执其将李继宁。',[('王建','克寨者'),('李继宁','被执将')],when='897年六月癸亥',place='梓州南寨',note='克南寨不等于已克梓州州城，执将不写已杀。')
e('li_xun_arrives_zizhou','李洵宣谕至梓州',23,'丙寅，宣谕使李洵至梓州',[('李洵','到使者')],when='897年六月丙寅',place='梓州')
e('li_xun_meets_wang_banner_statement','李洵见王建于张杷砦，王称战士情不可夺',23,'己巳，见建于张杷砦，建指执旗者曰：“战士之情，不可夺也。”',[('李洵','会见者'),('王建','指旗陈词者')],when='897年六月己巳',place='张杷砦',note='主书砦名字形保留，未核现代地理。战士不可夺是王建陈词，不作全军独立表态或已达停战。')
e('mao_refuses_prince_surrounds_fengtian','覃王赴凤翔，李茂贞拒代并围于奉天',24,'覃王赴镇，李茂贞不受代，围覃王于奉天。',[('覃王嗣周','赴镇被围者'),('李茂贞','拒代围者')],when='897年六月授职之后；确日未载',place='奉天',note='实际赴镇与诏命分录，拒代不写王已掌凤翔。')
e('ningyuan_established_rongzhou','容州置宁远军',24,'置宁远军于容州',when='897年六月条；确日未载',place='容州')
e('gai_yu_leads_ningyuan','盖寓领宁远节度使',24,'以李克用大将盖寓领节度使。',[('盖寓','受领者')],when='897年六月条；确日未载',place='宁远军、容州',note='领为名义军职，不补盖寓已离河东抵容州。')
person('李茂贞',13,'李继瑭养父');rk='relationship_person_李茂贞_person_李继瑭_养父'
B['person_relationships'].append(dict(key=rk,person_a_key=people['李茂贞'],person_b_key=people['李继瑭'],relation_type='养父',description='李茂贞是李继瑭的养父。',status='draft'));claim('person_relationship',rk,'description','李茂贞是李继瑭的养父。',13,quote='继瑭，茂贞之养子也。',note='方向按A是B养父，收养起年未载，不记本年新收养。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
    record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0897_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('xintangshu-188-897-jiaxing','event','event_zztj_261_0897_gu_breaks_eighteen_camps_captures_wei','description','《新唐书》记顾全武救嘉兴，执张宣魏约，逐田頵于驿亭埭。','田頵、魏約、張宣共圍嘉興，鏐大將顧全武救之，執宣、約，逐頵驛亭埭。',17,'未具本句月日，保补书更多将名不凭此补各人全部参战时段或另造同名人物。','adds')
extra('xintangshu-188-897-jiaxing','person',people['魏约'],'description','《新唐书》记魏约与田頵张宣围嘉兴，被顾全武所执。','田頵、魏約、張宣共圍嘉興，鏐大將顧全武救之，執宣、約',17,'对应同地同将被俘，保不同书原字与叙事时序，未核纸本。','corroborates')
extra('xintangshu-186-897-dongchuan','person',people['李洵'],'description','《新唐书》称李洵为左谏议大夫，通鉴本段作右谏议大夫。','帝仍遣左諫議大夫李洵諭止，建拒命。',14,'两书左右官称异记，保同使同名主体，不创建左右谏议两个李洵。','conflicts')
extra('xintangshu-186-897-dongchuan','event','event_zztj_261_0897_li_xun_meets_wang_banner_statement','description','《新唐书》记遣李洵谕止而王建拒命。','帝仍遣左諫議大夫李洵諭止，建拒命。',23,'补书总述未具会见日期地点，不能用拒命一句反推使者到达前后细节；保主书陈词。','adds')
extra('xintangshu-186-897-dongchuan','event','event_zztj_261_0897_qin_prince_fengxiang_governor','description','《新唐书》记嗣郯王戒丕镇凤翔、徙李茂贞代王建；主书作覃王嗣周。','帝以嗣郯王戒丕鎮鳳翔，徙茂貞代建，皆不奉詔。',23,'受任宗室封号、姓名与主书不同，独立保异记，不将两王合并或静改主书。','conflicts')
extra('jiuwudaishi-019-897-qu-zhang','event','event_zztj_261_0897_yougong_takes_wuchang_captures_qu','time_original','《旧五代史》朱友恭传在光化初援杜洪黄州战事下记获瞿章；主书记乾宁四年五月。','光化初，淮夷侵鄂渚，武昌帥杜洪來乞師，太祖遣友恭將兵萬餘，濟江應援，引兵至龍沙、九江而還，軍聲大振。時淮寇據黃州，友恭攻陷其壁，獲賊將瞿章',20,'与该段下文获瞿章连读，年代异记保留；光化初不算唯一月日，不据同名捕将另造第二次确定被俘。','conflicts')
extra('jiuwudaishi-019-897-qu-zhang','person',people['朱友恭'],'description','《旧五代史》记朱友恭寿春人，本姓李名彦威。','朱友恭，壽春人，本姓李，名彥威。',20,'保已有朱友恭/李彦威主体，出生地与姓名补证不改发生年；传中太祖收养时年未载。','adds')
extra('jiuwudaishi-055-gai-yu','person',people['盖寓'],'description','《旧五代史》记盖寓蔚州人。','蓋寓，蔚州人。',24,'籍贯补同一人，不添现代坐标或生年。','adds')
extra('jiuwudaishi-055-gai-yu','person',people['盖寓'],'description','《旧五代史》记盖寓随李克用镇太原，改左都押牙、检校左仆射，出征常随。','洎移鎮太原，改左都押牙、檢校左僕射。武皇與之決事，言無不從，凡出征伐，靡不衛從。',24,'背景职历未具本句年份，未据此填897授职；夹注通鉴内容不视独立原始确证。','adds')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(13,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十二段连续校核；嘉兴两战、黄州寨州之别、东川诏贬与实际拒代分录。李洵官称及凤翔宗室人选、瞿章战事年代异记附独立出处；既有同人改名与官职复用稳定主体。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=897,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(13,25)],next_paragraph=Q[25]['id'],coverage='本年50段中的第13—24段连续整理，本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
