"""Curate consecutive Tongjian volume 260, year 896 paragraphs 22–30."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p022-p030', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-896'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁三年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/260.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/260.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'落落':'落落','通王滋':'李滋','嗣延王戒丕':'李戒丕','戒丕':'李戒丕','嗣贾王嗣周':'李嗣周','嗣周':'李嗣周','韩建之子从允':'韩从允','硃朴':'朱朴','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0896_09_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=896,note=None,quote=None):
    key='event_zztj_260_0896_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0896_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def e(code,title,n,q,actors=(),when=None,place=None,year=896,note=None,description=None):
    return event(code,title,n,when or '896年卷260本段条；确日未载',place,description or title+'。',actors,year=year,quote=q,note=note)

e('gu_attacks_yue_outer_city','顾全武夜攻越州，翌晨克外郭',22,'甲午，夜，顾全武急攻越州，乙未旦，克其外郭，董昌犹据牙城拒之。',[('顾全武','攻克外郭者'),('董昌','据牙城抵抗者')],when='896年五月甲午夜至乙未旦',place='越州',note='外郭已克，牙城仍拒；不提前记董已降。')
e('luo_tuan_deceives_dong_retirement','钱镠遣骆团诈称奉诏，劝董昌归临安',22,'戊戌，镠遣昌故将骆团绐昌云：“奉诏，令大王致仕归临安。”',[('钱镠','遣说者'),('骆团','诈称诏命者'),('董昌','受骗者')],when='896年五月戊戌',note='绐明确为骗，奉诏不作为真实朝廷诏书；故将不推出终身臣属关系。')
e('dong_delivers_seals_leaves_qingdao','董昌交出牌印，出居清道坊',22,'昌乃送牌印，出居清道坊。',[('董昌','交牌印出居者')],when='896年五月戊戌被骗以后',place='清道坊')
e('wu_zhang_takes_dong_executes_xiaojiangnan','吴璋舟载董昌往杭州，至小江南斩之',22,'己亥，全武遣武勇都监使吴璋以舟载昌如杭州，至小江南，斩之',[('顾全武','遣送者'),('吴璋','载送行刑者'),('董昌','被斩者')],when='896年五月己亥',place='小江南',note='如杭州为目的地，行刑地小江南；未配现代地点，不作已到杭城。')
e('dong_family_officials_killed','董昌家属三百余及李邈蒋瑰以下百余人被杀',22,'并其家三百馀人，宰相李邈、蒋瑰以下百馀人。',[('李邈','被杀宰相'),('蒋瑰','被杀宰相')],when='896年五月董昌被斩条内',note='人数为主书记载，补书十余人异记另附；未为无名家属造人物，也未补个体行刑地点。')
e('dong_levies_reduces_rations','董昌围城中征钱帛，削减战士粮食',22,'昌在围城中，贪吝益甚，口率民间钱帛，减战士粮。',[('董昌','征敛减粮者')],when='896年越州围城期间',place='越州',note='口率保原摘录，按征敛释读；贪吝归于主书评价，不推现代税率。')
e('qian_sends_head_rewards_relief','钱镠传董昌首至京师，赏军并开仓赈贫',22,'及城破，库有金帛杂货五百间，仓有粮三百万斛。钱镠传昌首于京师，散金帛以赏将士，开仓以振贫乏。',[('钱镠','传首赏军赈贫者')],when='896年五月越州城破后',place='越州',note='五百间、三百万斛为史书库存称数，不换现代重量；传首京师不等于钱亲赴京。',description='主书记越州城破后库有金帛杂货五百间、粮三百万斛。钱镠传董昌首于京师，散金帛赏军，开仓赈贫。')

e('li_keyong_raids_weibo_six_prefectures','李克用攻魏博，侵掠遍六州',23,'李克用攻魏博，侵掠遍六州。',[('李克用','攻掠者')],when='896年六月战前条；起讫未载',place='魏博',note='六州不补未列地名，也不记已占领六州。')
e('zhu_sends_ge_huanshui_leaves_pang_yun','朱温调葛从周援魏，留庞师古攻郓',23,'硃全忠召葛从周于郓州，使将兵营洹水以救魏博，留庞师古攻郓州',[('朱温','调军者'),('葛从周','营洹水援魏者'),('庞师古','留攻郓者')],when='896年六月战前；确日未载',place='洹水、郓州')
e('luoluo_captured_at_huanshui','洹水交战，落落马踬被汴军生擒',23,'六月，克用引兵击从周，汴人多凿坎于陈前，战方酣，克用之子铁林指挥使落落马遇坎而踬，汴人生擒之',[('李克用','引兵交战者'),('葛从周','受攻将'),('落落','马踬被擒者')],when='896年六月',place='洹水',note='朱军凿坎与被擒按主书；补书不同篇月份异记保留。落落不自行补正式名李落落。')
e('li_keyong_rescues_luoluo_escapes','李克用救落落亦马踬，射杀汴将得免',23,'克用自往救之。马亦踬，几为汴人所获；克用顾射汴将一人，毙之，乃得免。',[('李克用','救子射将逃免者')],when='896年六月交战时',place='洹水',note='几被获不是已经被擒；汴将一人未名不补姓名。')
e('zhu_refuses_ransom_luo_kills_luoluo','朱温拒赎落落，交罗弘信使杀之',23,'克用请修好以赎落落，全忠不许，以与罗弘信，使杀之。',[('李克用','请修好赎子者'),('朱温','拒赎交人者'),('罗弘信','受人处杀者'),('落落','被杀者')],when='896年六月战后条；确日未载',note='请修好未作已经结盟；不合并被擒与处杀同一时点。')
e('li_keyong_withdraws_after_son_killed','李克用在落落被杀后引军还',23,'克用引军还。',[('李克用','撤军者')],when='896年落落被杀后条；确日未载')
e('ge_crosses_river_yangliu_attacks_yun','葛从周渡河屯杨刘，再攻郓州',23,'葛从周自洹水引兵济河，屯于杨刘，复击郓',[('葛从周','渡河屯营攻郓者')],when='896年李克用撤军后条；确日未载',place='杨刘、郓州',note='杨刘保主书，旧五代史阳留字形差异另附。')
e('ge_wins_guleting_takes_subordinate_cities','葛从周破三镇军于故乐亭，汴军据兖郓属城',23,'及兗、郓、河东之兵战于故乐亭，破之，兗、郓属城皆为汴人所据',[('葛从周','破军者')],when='896年再攻郓州后条；确日未载',place='故乐亭',note='属城皆据不表示兖郓两州主城已陷，未载三军将姓名不补朱瑄朱瑾亲率。')
e('luo_blocks_li_reinforcements_yan_yun','兖郓屡求李克用援，罗弘信拒其援军',23,'屡求救于李克用，克用发兵赴之，为罗弘信所拒，不得前，兗、郓由是不振。',[('李克用','发援军者'),('罗弘信','拒援军者')],when='896年兖郓属城被据后；起讫未载',note='兖郓不振为主书总结，未添降服或灭亡日期。')
ka,kb=people['李克用'],people['落落'];rk=f'relationship_{ka}_{kb}_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=ka,person_b_key=kb,relation_type='父亲',description='主书记落落为李克用之子。',status='draft'))
claim('person_relationship',rk,'description','李克用是落落的父亲。',23,quote='克用之子铁林指挥使落落',note='A是B父亲的方向明确；只录一条，不造反向重复。')

e('li_tun_weibei_towns_respect_court','李克用屯渭北时，李茂贞韩建恭事朝廷',24,'初，李克用屯渭北，李茂贞、韩建惮之，事朝廷礼甚恭。',[('李克用','屯驻者'),('李茂贞','礼恭者'),('韩建','礼恭者')],when='初所追叙屯渭北期间；确年未载',place='渭北',year=None,note='初为追叙；惮之为史书所述，不全定896。')
e('towns_reduce_tribute_after_li_leaves','李克用离去后，两镇贡奉渐疏表章骄慢',24,'克用去，二镇贡献渐疏，表章骄慢',[('李茂贞','两镇之一'),('韩建','两镇之一')],when='李克用离渭北后的渐变背景；起讫未载',year=None,note='渐疏及骄慢归于主书概述，不补精确开始日。')
e('emperor_adds_armies_princes_recruit','唐昭宗还石门后置诸军，诸王领军并募兵',24,'上自石门还，于神策两军之外，更置军圣、捧宸、保宁、宣化等军，选补数万人，使诸王将之；嗣延王戒丕、嗣贾王嗣周又自募麾下数千人。',[('唐昭宗','置军者'),('李戒丕','自募将'),('李嗣周','自募将')],when='自石门还后的增军背景；具体起讫未载',year=None,note='数万数千为书中概数；军圣及嗣贾王为底本字形，嗣周复用已知李嗣周，不另建贾王同名人。')
e('mao_claims_court_plans_attack_prepares_entry','李茂贞疑朝廷欲讨己，勒兵扬言入阙诉冤',24,'茂贞以为欲讨己；语多怨望，嫌隙日构。茂贞亦勒兵扬言欲诣阙讼冤；京师士民争亡匿山谷。',[('李茂贞','疑忌勒兵者')],when='896年京畿战事之前背景；确日未载',note='欲讨己为茂贞判断；扬言欲诣不是已和平入朝。士民逃匿未载人数。')
e('emperor_sends_princes_guard_near_capital','唐昭宗命通延覃诸王卫近畿，戒丕屯三桥',24,'上命通王滋及嗣周、戒丕分将诸军以卫近畿，戒丕屯三桥。',[('唐昭宗','分将命令者'),('李滋','分将者'),('李嗣周','分将者'),('李戒丕','分将屯三桥者')],when='896年六月京畿战前条；确日未载',place='三桥、近畿')
e('mao_petitions_accuses_prince_emperor_calls_hedong','李茂贞表称延王讨己，唐昭宗急告河东',24,'茂贞遂表言“延王无故称兵讨臣，臣今勒兵入朝请罪。”上遽遣使告急于河东。',[('李茂贞','上表声称者'),('唐昭宗','遣使告急者')],when='896年六月逼京畿前条；确日未载',note='延王无故讨臣及入朝请罪为茂贞表辞，不作为无争议事由。')
e('mao_defeats_prince_louguan','李茂贞逼京畿，覃王战娄馆败',24,'丙寅，茂贞引兵逼京畿，覃王与战于娄馆，官军败绩。',[('李茂贞','逼近交战者'),('李嗣周','战败覃王')],when='896年六月丙寅',place='娄馆',note='覃王按已知嗣周爵号复用，官军败未补伤亡数。')
e('mao_approaches_capital_jiepi_proposes_taiyuan','李茂贞逼京师，李戒丕请唐昭宗幸太原',24,'秋，七月，茂贞进逼京师。延王戒丕曰：“今关中籓镇无可依者，不若自鄜州济河，幸太原，臣请先往告之。”',[('李茂贞','逼京师者'),('李戒丕','提出太原路线者')],when='896年七月',place='京师',note='路线为戒丕建议，不作为已经到太原，也不把无可依者作为全面客观评价。')
e('emperor_orders_fuzhou_leaves_weibei','唐昭宗诏幸鄜州，出至渭北',24,'辛卯，诏幸鄜州；壬辰，上出至渭北',[('唐昭宗','诏幸并出行者')],when='896年七月辛卯诏、壬辰出',place='渭北',note='鄜州为诏定目的，不作已抵鄜州。')
e('han_congyun_requests_huazhou_han_appointed','韩建遣子从允请幸华州，唐昭宗初拒并授韩职',24,'韩建遣其子从允奉表请幸华州，上不许，以建为亦畿都指挥、安抚制置及开通四面道路、催促诸道纲运等使。',[('韩建','遣子受职者'),('韩从允','奉表者'),('唐昭宗','拒请授职者')],when='896年七月壬辰出渭北后条',note='从允按韩建之子补姓消歧；亦畿保底本，正文不发挥具体行政权限。',description='韩建遣其子韩从允奉表请唐昭宗幸华州，帝初不许，授韩建京畿相关指挥、安抚制置、通道路及催纲运等职，底本作亦畿。')
e('emperor_fuping_calls_han_yuan_envoy','唐昭宗至富平，遣元公讯召韩建议去留',24,'而建奉表相继，上及从官亦惮远去，癸己，至富平，遣宣徽使元公讯召建，面议去留。',[('唐昭宗','召议者'),('元公讯','宣徽使奉召者'),('韩建','被召者')],when='896年七月底本癸己',place='富平',note='癸己为底本疑干支，未静改癸巳；元公讯保原姓名未并元公询。惮远去是主书叙述。')
e('han_meets_emperor_persuades_huazhou','韩建见帝富平，劝幸华州获从',24,'甲午，建诣富平见上，顿首涕泣言：“方今籓臣跋扈者，非止茂贞。陛下若去宗庙园陵，远巡边鄙，臣恐车驾济河，无复还期。今华州兵力虽微，控带关辅，亦足自固。臣积聚训厉，十五年矣，西距长安不远，愿陛下临之，以图兴复。”上乃从之。',[('韩建','劝幸者'),('唐昭宗','听从者')],when='896年七月甲午',place='富平',note='十五年为韩建陈词称数，不由此推确切筹备始年；无复还期为担忧，不是已实现后果。')
e('emperor_reaches_huazhou_palace_office','唐昭宗宿下邽至华州，以韩建府署为行宫',24,'乙未，宿下邽；丙申，至华州，以府署为行宫；建视事于龙兴寺。',[('唐昭宗','驻行宫者'),('韩建','移龙兴寺视事者')],when='896年七月乙未宿、丙申至',place='下邽、华州')
e('mao_enters_changan_burns_buildings','李茂贞入长安，烧毁重葺宫室市肆',24,'茂贞遂入长安，自中和以来所葺宫室、市肆，燔烧俱尽。',[('李茂贞','入城烧毁者')],when='896年七月帝至华州后条；确日未另载',place='长安',note='中和以来是重建建筑背景，焚烧按896入城后，不造逐栋财产数量。')
ka,kb=people['韩建'],people['韩从允'];rk=f'relationship_{ka}_{kb}_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=ka,person_b_key=kb,relation_type='父亲',description='韩从允为韩建之子，本段奉父表请幸华州。',status='draft'))
claim('person_relationship',rk,'description','韩建是韩从允的父亲。',24,quote='韩建遣其子从允奉表请幸华州',note='只录父亲方向，不补生母或出生年。')

e('cui_yin_sent_wuan_for_zhaowei_party','崔胤出任武安，帝以其为崔昭纬党',25,'乙己，以中书侍郎、同平章事崔胤同平章事，充武安节弃使。上以胤，崔昭纬之党也，故出之。',[('崔胤','出任者'),('唐昭宗','外任命令者')],when='896年七月条底本乙己',note='乙己与节弃使均保底本疑字；官称按节度使释读，具体公历日未推，党身份归于帝判断。',description='崔胤以同平章事出任武安节度使，底本作节弃使；唐昭宗认为他属崔昭纬党，因此令出。')
e('lu_yi_appointed_chancellor','陆扆为户部侍郎同平章事',26,'丙午，以翰林学士承旨、尚书左丞陆扆为户部侍郎、同平章事。扆，陕人也。',[('陆扆','受相职者')],when='896年七月丙午',note='陕人作为本段籍贯事实，不据此补具体出生城市坐标。',description='翰林学士承旨、尚书左丞陆扆被任为户部侍郎、同平章事。主书称其陕人。')
claim('person',people['陆扆'],'description','陆扆为陕人。',26,quote='扆，陕人也。',note='陕为史载籍贯，未推生年。')
e('he_ying_recommends_zhu_pu','何迎表荐襄阳博士朱朴，称才如谢安',27,'水部郎中何迎表荐国子《毛诗》博士襄阳硃朴，才如谢安',[('何迎','表荐者'),('朱朴','被荐博士')],when='896年七月条；确日未载',note='才如谢安为推荐评价，不创建谢安参与本次事件。')
e('xu_yanshi_recommends_zhu_pu','许岩士荐朱朴有经济才',27,'道士许岩士亦荐朴有经济才。',[('许岩士','荐举道士'),('朱朴','被荐者')],when='896年七月条；确日未载',note='经济才为治理能力的推荐评价，不改现代经济学专家。')
e('emperor_interviews_rewards_zhu_he','唐昭宗连日召朱朴，赏朱朴何迎金帛',27,'上连日召对，朴有口辩，上悦之，曰：“朕虽非太宗，得卿如魏征矣。”赐以金帛，并赐何迎。',[('唐昭宗','召对赐赏者'),('朱朴','受召受赏者'),('何迎','受赏者')],when='896年七月条连日召对；确日未载',note='太宗魏征是帝比喻，不建参与边；金帛未载数。',description='唐昭宗连日召朱朴对答，喜其口辩，以魏征比拟朱朴，赐金帛，并赏何迎。')
e('xu_yanruo_daming_palace_guard','徐彦若为大明宫留守兼京畿安抚制置等使',28,'以徐彦若为大明宫留守，兼京畿安抚制置等使。',[('徐彦若','受留守等职者')],when='896年七月条；确日未载',place='大明宫')
e('yang_petitions_move_capital_jianghuai','杨行密表请唐昭宗迁都江淮',29,'杨行密表请上迁都江淮',[('杨行密','请迁都者')],when='896年七月条；确日未载',note='请不作迁都已实现，江淮为建议范围，不选定具体都城。')
e('wang_petitions_emperor_chengdu','王建请唐昭宗幸成都',29,'王建请上幸成都。',[('王建','请幸者')],when='896年七月条；确日未载',note='不作唐昭宗已幸成都。')
e('han_declines_participating_court_decisions','诏韩建参与议政，韩建固辞而止',30,'宰相畏韩建，不敢专决政事。八月，丙辰，诏建关议朝政；建上表固辞，乃止。',[('韩建','受诏固辞者'),('唐昭宗','下诏者')],when='896年八月丙辰',note='宰相畏为书中背景，未名单个宰相不补；固辞而止不作实际获全面执政权。')
e('han_calls_routes_supply_emperor','韩建檄诸道输资粮至行在',30,'韩建移檄诸道，令共输资粮诣行在。',[('韩建','移檄令输者')],when='896年八月条；确日未另载',note='令输资粮不作各道实际已全部交付。')
e('li_keyong_criticises_han_predicts_capture','李克用批韩建弱帝，预言遭茂贞或朱温擒',30,'李克用闻之，叹曰：“去岁从余言，岂有今日之患！”又曰：“韩建天下痴物，为贼臣弱帝室，是不为李茂贞所擒，则为硃全忠所虏耳！”',[('李克用','评议者')],when='896年八月闻韩建檄令后',note='痴物、贼臣等为李的陈词；被擒是预测，不补为896已被擒，去岁语未另建重复895事件。')
e('li_keyong_petitions_joint_aid_emperor','李克用奏拟与邻道发兵援帝',30,'因奏将与邻道发兵入援。',[('李克用','奏拟入援者')],when='896年八月闻檄评议后条；确日未载',note='将为拟议，不作援军已经发出或抵华州。')

supplements=[]
prior=json.loads((YEAR/'part-05/content-batch.json').read_text());sk='wuyuebeishi-001-896-yue-siege'
B['sources'].append(next(dict(r) for r in prior['sources'] if r['key']==sk));reused.add(sk)
raw=(ROOT/'resources/originals/kanripo/KR2i0019/KR2i0019_001.txt').read_bytes();(P/'sources'/(sk+'.txt')).write_bytes(raw)
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(next(dict(r) for r in json.loads((YEAR/'part-05/sources/manifest.json').read_text()) if r['key']==sk));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(sk,raw,code,n,text,q,citation,note,kind='adds'):
    assert q in raw;ck=f'claim_zztj_260_0896_09_{len(B["claims"])+1:04d}';key='event_zztj_260_0896_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation=citation,note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='吴越备史' if sk.startswith('wuyue') else '旧五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra(sk,raw.decode(),'dong_family_officials_killed',22,'《吴越备史》记斩李邈、蒋瑰等十余人，胁从皆赦；主书记宰相以下百余人及董家三百余人。','又斬偽宰相李邈蔣瓌等十餘人以下¶\n<pb:KR2i0019_SBCK_001-21b>¶\n脅從者悉宥之','卷1·乾宁三年五月·KR2i0019_SBCK_001-21a末—21b','十余与百余及家属详略并列，未推同一统计范围或覆盖主书；蒋瓌对应主书蒋瑰，不造新人。','conflicts')
extra(sk,raw.decode(),'wu_zhang_takes_dong_executes_xiaojiangnan',22,'《吴越备史》同记吴璋执董昌至而斩，但未具主书己亥、小江南细节。','頋全武遣上武勇都監使¶\n吳璋執昌至而斬之','卷1·乾宁三年五月·KR2i0019_SBCK_001-21a','与主书有详略，不把补书乙未段头扩为本句确日，也未倒灌主书细节到补书。','corroborates')
from urllib.parse import quote as urlquote
def oldsource(sk,page,title):
    path='resources/derived/twenty-four-histories/18旧五代史.jsonl';raw=next(json.loads(l)['text'] for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==page);url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_text(raw);B['sources'].append(dict(key=sk,title=title,source_type='primary',author='薛居正等',edition='仓库PDF提取电子文本；未核纸本。',url=url,note=f'原PDF第{page}页；异记独立引用。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw.encode()).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n');return raw
sk='jiuwudaishi-taizu-896-luoluo';raw=oldsource(sk,28,'旧五代史·梁太祖纪·乾宁三年洹水战')
extra(sk,raw,'luoluo_captured_at_huanshui',23,'《旧五代史》太祖纪记六月落落率三千骑，被葛从周击败擒献。','六月，李克用帅蕃汉\n诸军营于斥丘，遣其男落落将铁林小\n兒三千骑薄于洹水，从周与战，大败\n之，生擒落落以献。','梁太祖纪·乾宁三年六月·原PDF第28页','三千骑是补书详数，主书未载不覆盖；落落之子身份主书已有，不再反向建重复关系。','adds')
extra(sk,raw,'zhu_refuses_ransom_luo_kills_luoluo',23,'《旧五代史》同记朱温拒赎，送落落于罗宏信而斩。','克用悲骇，请修\n旧好以赎其子，帝不许，遂执落落送\n于罗宏信，斩之。','梁太祖纪·乾宁三年六月条·原PDF第28页','罗宏信是旧书字形，主线复用罗弘信；帝为梁纪追称朱温，不推当年已帝。','corroborates')
sk='jiuwudaishi-wuhuang-896-luoluo';raw=oldsource(sk,602,'旧五代史·唐武皇纪·乾宁三年落落被擒')
extra(sk,raw,'luoluo_captured_at_huanshui',23,'《旧五代史》武皇纪在七月车驾幸华州后记是月落落被擒；主书和梁太祖纪作六月。','六月，李茂贞举兵犯京师。七\n月，车驾幸华州。是月，武皇与汴军\n战于洹水之上，铁林指挥使落落被\n擒。落落，武皇之长子也。','唐武皇纪·乾宁三年七月条·原PDF第602页','被擒月份异记并列，不改主书六月；长子为补书说法，未凭此补其生母。','conflicts')
sk='jiuwudaishi-hanjian-896-huazhou';raw=oldsource(sk,332,'旧五代史·韩建传·迎昭宗幸华州')
extra(sk,raw,'mao_defeats_prince_louguan',24,'《旧五代史》韩建传记乾宁三年四月延王通王讨李茂贞败，主书本段六月覃王娄馆战；记载人物与时间不同。','三年四月，昭宗遣延王、通王\n率禁兵讨李茂贞，为茂贞所败','韩建传·乾宁三年条·原PDF第332页','可能不同概括或异说，未认必为同一细节，原书四月和延通两王保留，不覆盖主书六月覃王。','conflicts')
extra(sk,raw,'emperor_reaches_huazhou_palace_office',24,'《旧五代史》韩建传记七月十五日昭宗至华下，并称百官士庶继至。','七月十五日，昭宗至华\n下，百官士庶相继而至。','韩建传·乾宁三年七月·原PDF第332页','十五日是该书纪日，与主书丙申各自保留，不自行换算公历以强认同一天。','adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(22,31):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='连续段动作、表辞、追叙与未执行请求分录；原字疑文保留，落落及韩从允父子明确方向；吴越和旧五代史的数字、日期、人物异记各附独立出处。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(22,31)],next_paragraph=Q[31]['id'],coverage='第22—30段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
