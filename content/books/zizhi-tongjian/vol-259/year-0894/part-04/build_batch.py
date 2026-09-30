"""Curate consecutive Tongjian volume 259, year 894 paragraphs 25–33."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 34))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0894-p025-p033', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-894'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259乾宁元年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/259.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/259.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0894_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·乾宁元年（894）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259乾宁元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=894,note=None,quote=None):
    key='event_zztj_259_0894_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0894_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

alias.update({'李溪':'李磎','李谿':'李磎','薛志诚':'薛志勤','李存审':'符存审','刘廉':'刘谦'})
event('liu_rengong_proposes_yanzhou','刘仁恭经盖寓献取幽州策，求万人',25,'刘仁恭归河东以后；数献策，起止未载','河东、幽州',
      '刘仁恭多次通过盖寓向李克用献计，愿得到一万军攻取幽州。',[('刘仁恭','献策求兵者'),('盖寓','转呈献策中介'),('李克用','受献策及求兵对象')],year=None,quote='刘仁恭数因盖寓献策于李克用，愿得兵万人取幽州。',note='愿得是请求，非实际获授万人；数次起止不详，不因在十一月条就把早先献策全记十一月。')
event('keyong_small_force_fails_install_liu','李克用围邢时分数千欲纳刘仁恭，未克',25,'李克用攻邢州时；早于本段十一月大举，确年未定','邢州、幽州',
      '李克用在攻邢州时分兵数千，想把刘仁恭送入幽州掌权，没有成功。',[('李克用','分兵助纳者'),('刘仁恭','拟入幽州者')],year=None,quote='克用方攻邢州，分兵数千，欲纳仁恭于幽州，不克。',note='邢州围跨893至894，未具日年不强定；欲纳未克不能写为刘已任幽州节度。')
event('li_kuangchou_repeated_border_raids','李匡筹多次侵河东边境',25,'此前多次；具体起止未载','河东边境',
      '李匡筹渐骄，多次侵扰河东边境。',[('李匡筹','数次侵境者')],year=None,quote='李匡筹益骄，数侵河东之境。',note='益骄为书评，数侵不造逐次战役或边境精确地段。')
event('keyong_november_wuzhou_xinzhou','李克用大举攻匡筹，取武州围新州',25,'894年十一月','武州、新州',
      '李克用因李匡筹侵境而怒，十一月大举发兵，攻取武州，进围新州。',[('李克用','大举攻围者'),('李匡筹','被攻一方')],quote='克用怒，十一月，大举兵攻匡筹，拨武州，进围新州。',note='怒与此前侵境为史书所叙；武攻取与新被围区别，未把新州降记在十一月。')
event('zhang_fan_zhangyi_official','张鐇正式任彰义节度使',26,'894年十一月条；具体日未载','泾原、彰义',
      '朝廷以泾原留后张鐇为彰义节度使。',[('张鐇','正式受任者')],note='本年二月兄张钧表其留后与本段正式授节度分开；泾原与彰义皆原职称不创建两位张鐇。')
event('zhang_jian_sizhou_surrenders','朱使凌慢张谏，张举泗州归杨',27,'894年十一月条；具体日未载','泗州',
      '朱全忠派使者到泗州，使者怠慢刺史张谏，张谏举州归降杨行密。',[('朱温','以朱全忠名遣使一方'),('张谏','受凌慢后举州降者'),('杨行密','接受归降一方')],note='使者未名不造人物，不把凌慢全部归为朱亲口言语或断定已有他种阴谋。')
event('tang_linghui_tea_mission_seized','杨遣唐令回运茶贸易，朱全忠扣人夺茶',27,'泗州归杨后；894年，具体日未载','汴、宋',
      '杨行密派押牙唐令回带一万余斤茶到汴宋贸易，朱全忠扣押唐令回，尽取其茶。',[('杨行密','遣贸易者'),('唐令回','押牙运茶而被执者'),('朱温','以朱全忠名扣人夺茶者')],note='万余斤为书载，不换算现代重量或茶价；执不作已杀或后来获释。')
claim('person',people['杨行密'],'biography','《通鉴》在泗州与扣茶事后评论扬州、汴州双方开始有隙。',27,quote='扬、汴始有隙。',note='为史书对关系变化的概括，未据此新增终身敌对或为每次后续战争建立因果边。')
event('duanzhuang_relief_defeated','李匡筹数万救新州，段庄被李克用大破',28,'894年十二月；具体日未载','段庄、新州',
      '李匡筹派大将率步骑数万救新州，李克用选精兵在段庄迎战，大败援军；书载斩首万余级、生擒将校三百人。',[('李匡筹','遣救者'),('李克用','选兵迎击者')],quote='十二月，李匡筹遣大将将步骑数万救新州，李克用选精兵逆战于段庄，大破之，斩首万馀级，生擒将校三百人',note='数万与斩首万余是原书记数，将校三百只作将校非全军俘总数；援将未名不造人。')
event('captives_shown_xinzhou_surrenders','新州城下示俘，当夕归降',28,'894年十二月；段庄战后当夕','新州',
      '李克用军把俘获将校带到城下示众，当晚新州归降。',[('李克用','军主、城下示俘一方')],quote='生擒将校三百人，以练纟斥之，徇于城下。是夕，新州降。',note='以练纟斥之有拆字或讹字，保留并只记有城下示俘，不猜所用刑具，更不写俘将全被处死。降为城方，不给未名守将姓名。')
event('keyong_attacks_guizhou','李克用进攻妫州',28,'894年十二月辛亥','妫州',
      '李克用军继续进攻妫州。',[('李克用','进攻军主')],quote='辛亥，进攻妫州。',note='进攻非已攻克，结果本句未载。')
event('juyong_two_sided_attack','居庸关外李存审绕后夹击幽州军',28,'894年十二月壬子','居庸关',
      '李匡筹再次发兵出居庸关；李克用用精骑正面应战使敌疲惫，并派步将李存审由另路出敌后夹击。幽州军大败，书载杀获以万计。',[('李匡筹','再遣出关兵者'),('李克用','令骑当敌并遣步将者'),('符存审','以李存审名率步兵绕后者')],quote='壬子，匡筹复发兵出居庸关，克用使精骑当其前以疲之，遣步将李存审自他道出其背夹击之，幽州兵大败，杀获万计。',note='杀获是合并概数，不当万名均死亡；他道无线路坐标，不自行绘制绕行路线；存审依据独立新史赐姓李氏对应符存审。')
next(r for r in B['people'] if r['key']==people['符存审'])['aliases']=['李存审','符存']
claim('person',people['符存审'],'biography','《通鉴》记李存审本姓苻、宛丘人，李克用养为子。',28,quote='存审本姓苻，宛丘人，克用养以为子。',note='底本苻姓与新旧史符存审之符姓异字保留；独立新史明载赐李姓名存审，稳定主体用符存审，不把收养首次发生强定894年。')
relation('李克用','符存审','养父',28,'李克用是符存审的养父，本段称克用养以为子。',quote='存审本姓苻，宛丘人，克用养以为子。')
event('li_kuangchou_flees_cangzhou','李匡筹带族奔沧州',28,'894年十二月甲寅','幽州、沧州方向',
      '李匡筹带家族逃向沧州。',[('李匡筹','挈族逃走者')],quote='甲寅，李匡筹挈其族奔沧州',note='奔沧州是目的方向，后在景城被攻，不写已安全抵达沧州；族人未名不批量建档。')
event('lu_yanwei_kills_li_jingcheng','卢彦威遣军景城杀李匡筹，俘其众',28,'894年十二月甲寅条；逃亡途中','景城',
      '义昌节度使卢彦威图取李匡筹的辎重与妓妾，在景城派兵攻击，杀李匡筹，俘获其部众。',[('卢彦威','图物遣攻者'),('李匡筹','被杀者')],quote='义昌节度使卢彦威利其辎重、妓妾，遣兵攻之于景城，杀之，尽俘其众。',note='图物为史书所叙动机，不补现场台词；尽俘是概述，未作所有族人都杀死。')
event('keyong_youzhou_generals_surrender','李克用进幽州，卢龙大将请降',28,'894年十二月丙辰','幽州',
      '李克用进入幽州，卢龙方面的大将请求归降。',[('李克用','进军受请降者')],quote='丙辰，克用进军幽州，其大将请降。',note='其大将承匡筹方面，不猜具名将领或提前记895年迎入幽府仪式。')
claim('person',person('李匡威',28,'李匡筹据府时早先讲话的兄长'),'biography','《通鉴》追叙李匡筹初据军府时，李匡威称弟得军府仍不出家门，但担心弟才短，能守两年就算幸运。',28,quote='匡筹素暗懦，初据军府，兄匡威闻之，谓诸将曰：“兄失弟得，不出吾家，亦复何恨！但惜匡筹才短，不能保守，得及二年，幸矣。”',note='初据府是893年旧事，李匡威已死，不作894年新讲话；暗懦才短为书评或兄言，不作研究者心理定论，既有兄长关系不重复新增。')
event('wang_xingyue_added_title','王行约加检校待中',29,'894年十二月条；具体日未载','匡国',
      '匡国节度使王行约加检校待中，底本官名如此。',[('王行约','受加官者')],note='待中疑侍中转录讹字，未取得独立官名原文前保留底本，检校加官非实任中枢。')
event('wu_tao_returns_seal_requests_replacement','吴讨畏杜洪，纳印向杨请代',30,'894年十二月条；具体日未载','黄州',
      '吴讨害怕杜洪逼迫，向杨行密交印请求替代自己的职任。',[('吴讨','纳印请代者'),('杨行密','受请者'),('杜洪','所畏进逼一方')],note='区别三月归杨及此前黄州攻救；纳印请代不作被处死或反叛。')
event('qu_zhang_acting_huangzhou','杨行密以瞿章权知黄州',30,'吴讨纳印请代后；确日未载','黄州',
      '杨行密任先锋指挥使瞿章暂管黄州。',[('杨行密','任摄官者'),('瞿章','先锋指挥使、权知黄州者')],quote='行密以先锋指挥使瞿章权知黄州。',note='权知是暂摄，不改成已诏任黄州刺史。')
event('huangliandong_sieges_tingzhou','黄连洞军二万围汀州',31,'894年；是岁，具体月日未载','汀州',
      '书载黄连洞方面两万人包围汀州。',[],quote='是岁，黄连洞蛮二万围汀州',note='原书蛮为当时称谓，不自动对应现代民族；二万书数，未名领袖不造人物。')
event('li_chengxun_relief_jiangshuikou','王潮遣李承勋万人救汀，追败于浆水口',31,'894年；具体月日未载','汀州、浆水口',
      '福建观察使王潮派李承勋率万人迎击；围军退去，李承勋追至浆水口，击败对方。',[('王潮','遣救者'),('李承勋','领万人击追者')],quote='福建观察使王潮遣其将李承勋将万人击之；蛮解去，承勋追击之，至浆水口，破之。',note='一万为所派军书数；解去与追败前后区分，未补斩俘数量或断定黄连洞全体居民被灭。')
event('wang_chao_fujian_administration','王潮闽地略定后巡州劝农定税交邻',31,'闽地略定后的政务总述；具体起止未载','闽地各州县',
      '闽地渐定，王潮派僚佐巡视州县、劝农桑、制定租税、与邻道交好并保境息民，书称闽人安之。',[('王潮','安排地方政务者')],year=None,quote='闽地略定。潮遣僚佐巡州县，劝农桑，定租税，交好邻道，保境息民，闽人安之。',note='段末制度与民心总述，不将每次巡视定同一894年日期；闽人安之为史评，未写税率或现代治理绩效。')
event('liu_qian_dies_yin_mourning','封州刺史刘谦卒，刘隐贺江居丧',32,'894年条末；卒与居丧确日未载','封州、贺江',
      '封州刺史刘谦去世，其子刘隐在贺江守丧。',[('刘谦','底本作刘廉的去世刺史'),('刘隐','其子、居丧者')],quote='封州刺史刘廉卒，子隐居丧于贺江',note='本年条末未明月日，不作十二月精确死亡；新史父谦、封州贺江与子隐相应，沿一主体存字形，不据父卒反算出生年。')
next(r for r in B['people'] if r['key']==people['刘谦'])['aliases']=['刘廉']
claim('person',people['刘谦'],'aliases','主书底本本段作刘廉，新五代史刘隐父、封州刺史段作谦。',32,quote='封州刺史刘廉卒，子隐居丧于贺江',note='别名字段用于保留底本检索字形，不断言确有正式改名；同官地与父子链的独立出处另附。')
relation('刘谦','刘隐','父亲',32,'刘谦是刘隐的父亲，底本作刘廉并称子隐。',quote='封州刺史刘廉卒，子隐居丧于贺江')
event('liu_yin_kills_suspected_rebels','刘隐一夕诛百余谋乱士民',32,'刘隐居丧时；具体日未载','贺江',
      '书载士民一百余人谋乱，刘隐一夜将他们尽诛。',[('刘隐','诛杀者')],quote='士民百馀人谋乱，隐一夕尽诛之。',note='谋乱归于史书记载，未具名不造被杀者；百余是概数，不取精确101人，也不推具体审判程序。')
event('liu_chonggui_assigns_yin_heyuan','刘崇龟召刘隐补右都押牙兼贺水镇使',32,'诛谋乱士民后；具体日未载','岭南、贺水',
      '岭南节度使刘崇龟召刘隐，补为右都押牙兼贺水镇使。',[('刘崇龟','召补者'),('刘隐','受补职者')],quote='岭南节度使刘崇龟召补右都押牙兼贺水镇使',note='贺江居丧与贺水镇使分别保留，不猜现代同点；刘崇龟与刘隐同姓不推家族关系。')
event('liu_yin_fengzhou_recommendation','刘崇龟未几表刘隐为封州刺史',32,'任押牙镇使后未几；确日未载','封州',
      '刘隐被召补后不久，刘崇龟上表请其为封州刺史。',[('刘崇龟','表请者'),('刘隐','表请受任对象')],quote='岭南节度使刘崇龟召补右都押牙兼贺水镇使；未几，表为封州刺史。',note='未几为相对时长，不反算日数；表请与最终正式诏任有别，未假定当天获准。')
event('dong_chang_extra_tax_tributes','董昌重敛常赋外数倍，输巨额贡献馈遗',33,'多年政务总述；具体起止未载','越州、义胜',
      '《通鉴》称董昌为政苛虐，在常赋外加敛数倍，供贡献与内外馈赠；每旬发一纲，书载金万两、银五千鋋、越绫一万五千匹，其他物资相当。',[('董昌','重敛并输贡献者')],year=None,quote='义胜节度使董昌为政苛虐，于常赋之外，加敛数倍，以充贡献及中外馈遗，每旬发一纲，金万两，银五千鋋，越绫万五千匹，他物称是',note='苛虐为史书评价；书数与银单位鋋照存，不换现代金额。此前威胜与此义胜职称异字不新增董昌；多年贡献背景不强定开始894年。')
event('dong_transport_delay_deaths','董昌每纲五百运卒，误期遭杀',33,'贡献运输的长期做法；起止未载','',
      '董昌每纲用五百运卒，遇雨雪风水延误规定时间者，书载皆死。',[('董昌','运输与逾程惩罚制度的一方')],year=None,quote='用卒五百人，或遇雨雪风水违程，则皆死。',note='五百是每纲所用卒数，不合为年总人数；书未给具体遇难批次或总死亡数，皆死不编具体处死方式。')
event('court_rewards_dong_loyalty','朝廷以贡献为忠，累加董昌官爵',33,'此前宠命相继；具体年月未载','朝廷',
      '书述董昌责奉为天下最，朝廷因而认为忠诚，多次加宠，官至司徒同平章事、爵陇西郡王。',[('董昌','因贡献获累加官爵者')],year=None,quote='责奉为天下最，由是朝廷以为忠，宠命相继，官至司徒、同平章事，爵陇西郡王。',note='责奉底本疑字保留；为忠是朝廷评价，不断言董真实忠于朝廷；相继任官不造全在894年同日任授。')
event('dong_living_shrine_forced_worship','董昌建越州生祠，禁止民祷禹庙',33,'称帝谋议前的生祠做法；确年未载','越州、禹庙、生祠',
      '董昌在越州建生祠，制度比照禹庙，命民间祷赛者不得去禹庙而应去生祠。',[('董昌','建祠与命民祷赛者')],year=None,quote='是建生祠于越州，制度悉如禹庙，命民间祷赛者，无得之禹庙，皆之生祠。',note='是建疑于是建脱字，保留底本；制度悉如非有现存建筑测绘，未猜面积样式坐标或每人实际是否遵从。')
event('dong_yue_king_denied_emperor_suggestion','董昌求越王未获准，有人劝越帝',33,'谋称帝前；具体日年未载','',
      '董昌请求成为越王，朝廷未准。董称自己多年贡献却得不到越王封号，认为朝廷负他；有人谄称与其为越王不如作越帝。',[('董昌','求封未准并不悦者')],year=None,quote='昌求为越王，朝廷未之许，昌不悦曰：“朝廷欲负我矣，我累年贡献无算而惜一越王邪！”有谄之者曰：“王为越王，曷若为越帝。”',note='负我是董的判断，不作本项目立场；进言者未名不造人，越帝为建议非已称帝。')
event('dong_crowd_requests_emperor_delays','民间传时变请董称帝，董称待时',33,'894年条的称帝筹划背景；具体日未载','董昌门前',
      '民间讹传时世将变，人群集董昌门前喧噪请其称帝。董大喜，派人谢称天时未到，待时到自行称帝。',[('董昌','受请求并称待时者')],note='讹言为书载传闻，不当已经发生新朝革命；群体请帝不等代表所有越州民意，未补人数。此时仍未称帝。')
event('wu_yao_li_changzhi_urge_dong','吴瑶李畅之等劝董昌称帝',33,'894年称帝筹划时；具体日未载','',
      '董昌僚佐吴瑶、都虞候李畅之等劝其成就称帝计划。',[('董昌','被劝称帝者'),('吴瑶','劝进僚佐'),('李畅之','劝进都虞候')],quote='其僚佐吴瑶、都虞候李畅之等皆劝成之',note='劝成是称帝筹划非此年实际即位；同场劝说未推三人血亲或结义。')
event('dong_rewards_omens_reduces_awards','董昌赏献谣谶符瑞者，渐减赏额',33,'894年称帝筹划时；先后确日未载','',
      '吏民献谣谶符瑞者很多，董昌最初赏数百缗，献者日增后逐渐减到五百、三百。',[('董昌','奖励并渐减金额者')],quote='吏民献谣谶符瑞者不可胜纪，其始赏之以钱数百缗，既而献者日多，稍减至五百、三百而已',note='符瑞是所献之说，不证真实超自然现象；原文数百缗至五百三百量级有疑，不修成未经来源支持的数千，也不补币值换算。')
event('dong_plans_emperor_next_rabbit_year','董昌解释兔子谶，预告明年卯日称帝',33,'894年；声称将在明年二月卯日卯时称帝','',
      '董昌说兔子上金床的谶指自己，称自己生于卯岁、明年又逢卯年，计划在明年二月卯日卯时称帝。',[('董昌','解释谶并预告者')],quote='昌曰：“谶云‘兔子上金床’，此谓我也。我生太岁在卯，明年复在卯，二月卯日卯时，吾称帝之秋也。”',note='本事件是894年作出的声称，895年真实称帝另年再录；不从其生肖话语反算出生年，不把预告时刻当实际即位时间。')

from urllib.parse import quote as urlquote
supplements=[]
for sk,title,page in [('xinwudaishi-025-894-cunshen-origin','新五代史·卷25·符存审传·旧名籍贯',414),('xinwudaishi-025-894-cunshen-renaming','新五代史·卷25·符存审传·赐姓与居庸关',415),('xinwudaishi-065-894-liu-qian','新五代史·卷65·南汉世家·刘隐父段',1401)]:
    path='resources/derived/twenty-four-histories/19新五代史.jsonl'
    raw=next(json.loads(x)['text'].encode() for x in (ROOT/path).read_text().splitlines() if json.loads(x)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author='欧阳修',edition='仓库PDF派生电子文本；逐字及换行保留，未核纸本。',url=url,note=f'原PDF第{page}页，只补本批人物身份与行动。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,text,n,sk,quote,citation,note,kind):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_259_0894_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=ck,source_book='新五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('person',people['符存审'],'aliases','《新五代史》记符存审陈州宛丘人，初名存；籍贯与主书李存审相应。',28,'xinwudaishi-025-894-cunshen-origin','符存审，字德详，陈州宛丘人\n也。初名存','卷25·唐臣传第十三·符存审传·原PDF第414页','符与主书苻异字并存，宛丘籍贯及赐姓段相应；初名存为本姓符的旧名，不抽录后代传记。','corroborates')
extra('person',people['符存审'],'aliases','《新五代史》明确符存审归晋后，晋王以为义儿军使，赐姓李氏、名存审，支持与主书李存审同一人。',28,'xinwudaishi-025-894-cunshen-renaming','其后事李罕之，从罕之归晋，晋\n王以为义兒军使，赐姓李氏，名存\n审。','卷25·唐臣传第十三·符存审传·原PDF第415页','赐姓名为旧事不定894首次，独立身份书证而非只凭同名；太祖等后称不倒写当年称帝。','corroborates')
extra('event','event_zztj_259_0894_juyong_two_sided_attack','description','《新五代史》亦记存审从晋王击李匡俦，为前锋破居庸关。',28,'xinwudaishi-025-894-cunshen-renaming','从晋王击李匡俦，为前锋，破居\n庸关。','卷25·唐臣传第十三·符存审传·原PDF第415页','匡俦与主书匡筹为姓名异字，不新建同一军主；传记未给本次干支，不替主书记日。','corroborates')
extra('person',people['刘谦'],'aliases','《新五代史》南汉世家称刘隐父谦为封州刺史、贺江镇遏使，并记谦卒后广州表隐代之；主书底本相应父名作刘廉。',32,'xinwudaishi-065-894-liu-qian','父\n谦，为广州牙将。唐乾符五年，黄巢\n攻破广州，去略湖、湘间，广州表谦\n封州刺史、贺江镇遏使，以御梧、桂\n以西。','卷65·南汉世家第五·刘隐父段·原PDF第1401页','依据同一刘隐父、封州贺江职地链对应；保留廉谦异字，不断言真实改名，未反向采纳该页乾符五年的职位初授进本批新事件。','adds')
extra('event','event_zztj_259_0894_liu_yin_fengzhou_recommendation','description','《新五代史》记谦卒后广州上表令刘隐代父任封州刺史；与主书刘崇龟召补押牙镇使、未几表任的叙次不同。',32,'xinwudaishi-065-894-liu-qian','谦卒，广州表隐代谦封州刺史。','卷65·南汉世家第五·原PDF第1401页','传记简述与编年细述各留出处，不合并为同日诏准，也不把官名继任等于爵位世袭。','adds')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={
    25: '献策万人为求兵、围邢分数千未克、数侵河东为旧背景留年空；十一月武拔新围单录，不提前记新降。',
    26: '张鐇正式彰义与二月表留后区别。',
    27: '泗州使凌慢举降与茶贸扣人夺茶分录；万余斤原数，执非杀；扬汴始隙为书评不永久敌对。',
    28: '十二月段庄援败斩俘、城下示俘夕降、辛亥攻妫、壬子居庸夹击、甲寅逃与景城被杀、丙辰幽州请降分录；练纟斥疑字不造刑具，杀获合计非均死；李存审据新书赐姓合符存审，主书苻异字保留，养父有据；匡威旧话不记894亡后新讲话。',
    29: '检校待中疑侍中保底本，不补中枢实任。',
    30: '吴纳印请代、瞿权知分录，权知非诏任刺史。',
    31: '年度二万围汀、王遣万追败分阶段；蛮为书称不配现代民族；巡劝税邻保民长期总述留年空。',
    32: '父卒贺江居丧、士民谋乱百余一夕诛、刘崇龟召补、未几表封刺分阶段；刘廉据新书父谦封州贺江链为刘谦，字形检索别名非真实改名，父亲关系有原子隐句，不把表请作诏准。',
    33: '多年重赋贡物与运卒逾程死、累计朝宠、生祠强祷、求越王劝帝为背景留年空；传言请帝、吴李劝进、瑞谣奖励渐減与明年称帝预告分录；银鋋、责奉、是建、数百至五百三百疑字数保留，不提前写895实际即位或反算生肖生年。',
}
for n in range(25,34):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,34):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=894,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(25,34)],next_paragraph='zztj-v260-y0895-p001',coverage='卷259乾宁元年第25—33段连续录入；全33段完成须四批发布与整年核验。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
