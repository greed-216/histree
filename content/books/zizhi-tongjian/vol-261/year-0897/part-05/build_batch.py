"""Curate consecutive Tongjian volume 261, year 897 paragraphs 37–48."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 51))
B = {'format_version': 1, 'batch_key': 'zztj-v261-y0897-p037-p048', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-261-897-autumn'
fixed_commit='eddb060'
source_specs=[]
source_titles = {
    'tongjian-261-897-september-close': '资治通鉴·卷261·乾宁四年第37段',
    'tongjian-261-897-autumn-end': '资治通鉴·卷261·乾宁四年第38—45段',
    'tongjian-261-897-year-end': '资治通鉴·卷261·乾宁四年第46—48段',
    'xintangshu-010-897-october': '新唐书·卷10·乾宁四年十月',
    'xintangshu-186-897-gu-death': '新唐书·卷186·顾彦晖之死',
    'jiuwudaishi-022-897-niu-retreat': '旧五代史·卷22·牛存节掩护撤退',
    'jiuwudaishi-055-897-li-chengsi': '旧五代史·卷55·李承嗣与清口战',
    'jiuwudaishi-134-897-wang-chao': '旧五代史·卷134·王潮继承安排',
    'jiutangshu-020-898-context': '旧唐书·卷20上·光化元年年首',
    'jiutangshu-020-898-he-queen': '旧唐书·卷20上·何氏宜册为后',
    'jiutangshu-020-hui-prince-identity': '旧唐书·卷20下·哀帝与辉王祚身份',
    'xinwudaishi-068-897-wang-succession': '新五代史·卷68·王审知继立',
}
for d in sorted((P/'sources/library').iterdir()):
 r=json.loads((d/'paragraph.json').read_text());source_specs.append((d.name,source_titles[d.name],{'资治通鉴':'司马光等','旧五代史':'薛居正等','新五代史':'欧阳修','新唐书':'欧阳修、宋祁等','旧唐书':'刘昫等'}[r['book']]))
reused_source_keys=set()
manifest=[]
for sk,title,author in source_specs:
 d=P/'sources/library'/sk;r=json.loads((d/'paragraph.json').read_text());filename='library/'+sk+'/source.txt';url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((d/'source.txt').relative_to(ROOT))
 B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=r['citation']))
 manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256((d/'source.txt').read_bytes()).hexdigest(),url=url,paragraph_id=r['id'],upstream_locator=r['locator'],transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def primary(n):return 'tongjian-261-897-september-close' if n==37 else 'tongjian-261-897-autumn-end' if n<=45 else 'tongjian-261-897-year-end'
for n in range(37,49):assert Q[n]['text'] in (P/'sources/library'/primary(n)/'source.txt').read_text()
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
alias.update({'祕':'李秘','祚':'唐昭宣帝','祺':'李祺','何氏':'何氏（唐昭宗皇后）','德王':'李祐','辉王':'唐昭宣帝','侯瓚':'侯瓒','瑶':'瑶（顾彦晖假子）','审知':'王审知','审邽':'王审邽','李彦徽':'李彦徽（湖州）','延王戒丕':'李戒丕','王宗播':'许存','杜弘':'杜洪','嵩从周':'葛从周','硃瑾':'朱瑾','硃宣':'朱瑄','李继徽':'杨崇本','硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_261_0897_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=primary(n), citation=f'卷261·乾宁四年（897）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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
e('zhang_lian_campaign_mao','张琏任凤翔西北行营招讨使',37,Q[37]['text'],[('张琏','受招讨任命者'),('李茂贞','拟讨对象')],when='897年九月条；确日未载',place='凤翔',note='任招讨使不等于已攻克凤翔。')
e('wang_jian_xichuan_restored','王建复任西川节度使并同平章事',38,'复以王建为西川节度使、同平章事。',[('王建','复授者')],when='897年九月条；确日未载',place='西川')
e('wang_gao_added_pingzhang','王郜加同平章事',38,'加义武节度使王郜同平章事。',[('王郜','受加者')],when='897年九月条；确日未载',place='义武军')
e('mao_deprived_restored_song_name','李茂贞官爵被削夺，复姓名宋文通',38,'削夺新西川节度使李茂贞官爵，复姓名宋文通。',[('李茂贞','削夺者')],when='897年九月条；确日未载',note='记录朝廷处分，不表示实际控制区同时被夺。')
e('zhu_campaign_qingkou_an-feng','朱全忠遣庞师古葛从周南征，亲顿宿州',39,Q[39]['text'],[('朱温','遣军亲将者'),('庞师古','清口军主将'),('葛从周','安丰军主将'),('杨行密','被进攻对象')],when='897年九月条所述南征筹划；确日未载',place='清口、安丰、宿州',description='朱全忠既得兖郓，大举攻杨行密；遣庞师古率徐宿宋滑兵七万营清口，拟趋扬州，葛从周率兖郓曹濮兵营安丰，拟趋寿州，朱全忠自将顿宿州。',note='七万只属庞军，不作两军合计；拟趋不写已取扬州寿州。')
e('li_jitang_flees_fengxiang','李继瑭因讨茂贞及韩建动摇而奔凤翔',40,'匡国节度使李继瑭闻朝廷讨李茂贞而惧，韩建复从而摇之，继瑭奔凤翔。',[('李继瑭','出奔者'),('韩建','从而摇之者')],when='897年九月至十月任韩建前；确日未载',place='凤翔',note='复用此前明记茂贞养子，不认李继徽或李继溥。')
e('han_jian_two_armies_appointed','韩建任镇国匡国两军节度使',40,'冬，十月，以建为镇国、匡国两军节度使。',[('韩建','兼领两军者')],when='897年十月；确日未载',place='镇国军、匡国军')
e('hou_shao_surrenders_wang','侯绍率二万人降王建',41,'壬子，知遂州侯绍帅众二万，乙卯，知合州王仁威帅众千人，戊午，凤翔将李继溥以援兵二千，皆降于王建。',[('侯绍','率众降者'),('王建','受降者')],when='897年十月壬子',place='遂州',description='知遂州侯绍率众二万人降王建。',note='降由句末皆降统摄，不改为已任正式刺史。',)
e('wang_renwei_surrenders','王仁威率千人降王建',41,'壬子，知遂州侯绍帅众二万，乙卯，知合州王仁威帅众千人，戊午，凤翔将李继溥以援兵二千，皆降于王建。',[('王仁威','率众降者'),('王建','受降者')],when='897年十月乙卯',place='合州',description='知合州王仁威率众千人降王建。',note='降由句末皆降统摄；千人为原数，不补现代估算。')
e('li_jipu_surrenders','李继溥率凤翔援兵二千降王建',41,'戊午，凤翔将李继溥以援兵二千，皆降于王建。',[('李继溥','率援兵降者'),('王建','受降者')],when='897年十月戊午',description='凤翔将李继溥率援兵二千降于王建。',note='溥不并继瑭、继密；援兵归降不推全凤翔军归降。')
e('gu_sends_zongbi_return_wang','顾彦晖围急，遣王宗弼归王建',41,'建攻梓州益急。庚申，顾彦晖聚其宗族及假子共饮，遣王宗弼自归于建。',[('顾彦晖','遣归者'),('王宗弼','归王建者'),('王建','受归者')],when='897年十月庚申',place='梓州',note='王宗弼沿旧魏弘夫主体；聚饮不逐猜匿名宗族姓名。')
e('gu_yao_kills_gu_and_self','顾彦晖命假子瑶杀己同饮者，瑶随后自杀',41,'酒酣，命其假子瑶杀己及同饮者，然后自杀。',[('顾彦晖','命假子杀己者'),('瑶','杀顾及同饮者后自杀者')],when='897年十月庚申',place='梓州',note='瑶按顾假子建立瑶（顾彦晖假子），不并王瑶、吴瑶或王宗瑶；主书未写本人姓，显示名按主书仅载瑶加养家消歧，不补姓。主书主语承瑶，另书顾自刎并列。')
for name in ['顾彦晖','瑶（顾彦晖假子）']:claim('person',people[name],'death_year','主书记乾宁四年（897）梓州围急之际死亡。',41,quote='酒酣，命其假子瑶杀己及同饮者，然后自杀。',note='保存主书叙事，死法与补书异说并列；瑶姓未明载。')
e('wang_enters_zi_sends_zongwan','王建入梓州，遣王宗绾徇昌普等州',41,'建入梓州，城中兵尚七万人，建命王宗绾分兵徇昌、普等州',[('王建','入城遣将者'),('王宗绾','分兵徇地者')],when='897年十月庚申以后；确日未另载',place='梓州、昌州、普州',description='王建入梓州，城中兵尚七万人；命王宗绾分兵徇昌、普等州。',note='七万为入城时兵数，与新唐书相应；徇不补每州具体受降日。')
e('wang_zongdi_dongchuan_deputy','王宗涤任东川留后',41,'以王宗涤为东川留后。',[('王宗涤','受任留后者'),('王建','署置者')],when='897年十月王建入梓后；确日未另载',place='东川',note='复用华洪，留后不改正式节度使。')
e('liu_requests_command_against_li_denied','刘仁恭奏请自为统帅讨李克用，诏不许',42,'刘仁恭奏称：“李克用无故称兵见讨，本道大破其党于木瓜涧，请自为统帅以讨克用。”诏不许。',[('刘仁恭','奏请者'),('李克用','拟讨对象')],when='897年十月条木瓜战后；确日未载',description='刘仁恭奏称李克用无故见讨、己军木瓜大破，请统帅讨克用，朝廷不许。',note='无故为刘奏中立场，不录成已核事实；未实际奉诏统帅。')
e('zhu_recommends_liu_pingzhang','朱全忠奏加刘仁恭同平章事，朝廷从之',42,'又遗硃全忠书。全忠奏加仁恭同平章事，朝廷从之。',[('刘仁恭','致书受加者'),('朱温','奏荐者')],when='897年十月条；确日未载',note='致书与推荐明载，不由此补终身盟友关系。')
e('liu_apologizes_li_reproaches','刘仁恭遣使谢李克用，李回书责其失信',42,'仁恭又遣使谢克用，陈去就不自安之意。克用复书略曰：',[('刘仁恭','遣使谢者'),('李克用','复书者')],when='897年十月条木瓜战后；确日未载',description='刘仁恭遣使谢李克用，陈去就不自安；李克用回书以用人报德、盟誓失信责之。',note='回信骨肉猜防等为李的警告修辞，不作刘家庭真实发生之事；仗钅戊部件字保快照不猜武器。')
for code,title,name in [('mi_jing_prince','皇子祕封景王','祕'),('zuo_hui_prince','皇子祚封辉王','祚'),('qi_qi_prince','皇子祺封祁王','祺')]:
 e(code,title,43,Q[43]['text'],[(name,'受封皇子'),('唐昭宗','封皇子者')],when='897年十月甲子',note='以祕对应简体秘，皇子承昭宗上下文。祚为本年名，不无据改名柷；后续改名另附出处。')
e('zhang_lian_added_pingzhang','张琏加同平章事',44,Q[44]['text'],[('张琏','受加者')],when='897年十月条；确日未载',place='彰义军')
e('yang_zhu_jin_chuzhou_front','杨行密朱瑾率三万拒汴，张训任前锋',45,'杨行密与硃瑾将兵三万拒汴军于楚州，别将张训自涟水引兵会之，行密以为前锋。',[('杨行密','领军任前锋者'),('硃瑾','领军者'),('张训','涟水援军前锋')],when='897年清口战前筹备；确月日未载',place='楚州、涟水',note='三万属杨朱主军，不与先段庞军七万混作同军。')
e('pang_keeps_low_camp','庞师古不听迁离清口低洼营地之议',45,'庞师古营于清口，或曰：“营地汙下，不可久处。”不听。师古恃众轻敌，居常弈棋。',[('庞师古','不纳建议者')],when='897年清口战前；确月日未载',place='清口',note='轻敌为主书记述，建议者匿名；不得因弈棋推人格诊断。')
e('zhu_jin_dams_pang_kills_warning','朱瑾壅淮上流，庞师古斩来告者',45,'硃瑾壅淮上流，欲灌之。或以告师古，师古以为惑众，斩之。',[('硃瑾','壅水者'),('庞师古','斩告者')],when='897年清口战前；确月日未载',place='淮水上流、清口',note='壅水与后来洪水保持段内先后；匿名告者不猜名。')
e('qingkou_surprise_and_flood','朱瑾侯瓒潜渡袭汴营，张训逾栅，水至军乱',45,'十一月，癸酉，瑾与淮南将侯瓚将五千骑潜渡淮，用汴人旗帜，自北来趣其中军，张训逾栅而入。士卒苍黄拒战，淮水大至，汴军骇乱。',[('硃瑾','潜渡袭营者'),('侯瓚','率骑潜渡者'),('张训','逾栅者'),('庞师古','受袭汴军主将')],when='897年十一月癸酉',place='淮水、清口',note='主书五千骑原数照录，不借用夹注五十骑替换。')
e('qingkou_pang_defeated_killed','杨行密渡淮夹攻，庞师古败死',45,'行密引大军济淮，与瑾等夹攻之，汴军大败。斩师古及将士首万馀级，馀众皆溃。',[('杨行密','渡淮夹攻者'),('硃瑾','夹攻者'),('庞师古','败死主将')],when='897年十一月癸酉',place='清口',note='万余级为主书记载斩首数，不作所有参战者精确总损失；旧五代史生获另列。')
claim('person',people['庞师古'],'death_year','乾宁四年（897）清口之战庞师古败死。',45,quote='斩师古及将士首万馀级，馀众皆溃。')
e('zhu_yanshou_defeats_ge_shou','朱延寿击破葛从周，葛退濠州闻败北还',45,'葛从周屯于寿州西北，寿州团练使硃延寿击破之，退屯濠州，闻师古败，奔还。',[('葛从周','被击退走者'),('朱延寿','击破者')],when='897年十一月清口战前后；确日未载',place='寿州西北、濠州',note='先被击退后闻败奔还，不把每个动作强定癸酉日。')
e('pi_water_ge_half_cross_attacked','杨行密朱瑾朱延寿追击，葛从周淠水半济大败',45,'行密、瑾、延寿乘胜追之，及于淠水。从周半济，淮南兵击之，杀溺殆尽，从周走免。',[('杨行密','追击者'),('硃瑾','追击者'),('朱延寿','追击者'),('葛从周','半济被击逃免者')],when='897年十一月清口战后追击；确日未载',place='淠水',note='杀溺殆尽不推葛本人死亡，也不换确切人数。')
e('niu_rearguard_retreat_snow','牛存节弃马步战掩护，汴军饥雪北归损失',45,'遏后都指挥使牛存节弃马步斗，诸军稍得济淮，凡四日不食，会大雪，汴卒缘道冻馁死，还者不满千人。',[('牛存节','步战掩护者')],when='897年十一月败军撤退；四日不食而遇雪',place='淮水及北归路',note='不满千人为主书归还者范围，旧五代史收合八千余可能阶段不同，不算减法战损。')
e('zhu_returns_yang_challenge_letter','朱全忠闻败还，杨行密致书约淮上决战',45,'全忠闻败，亦奔还。行密遗全忠书曰：“庞师古、葛从周，非敌也，公宜来淮上决战。”',[('朱温','闻败还者及受书者'),('杨行密','约战致书者')],when='897年十一月清口战后；确日未载',note='约决战非双方后来已应约交战。')
e('li_chengsi_qingkou_priority_recalled','杨行密战后确认李承嗣先攻清口之策',45,'行密大会诸将，谓行军副使李承嗣曰：“始吾欲先趣寿州，副使云不如先向清口。师古败，从周自走，今果如所料。”',[('杨行密','战后论功者'),('李承嗣','先清口建策者')],when='897年十一月战后大会；策略为战前追述',note='建策时间只保战前，不将战后话倒作当日现场命令。')
e('li_chengsi_reward_zhenhai','杨行密赏李承嗣万缗并表领镇海节度',45,'赏之钱万缗，表承嗣领镇海节度使。',[('杨行密','赏赐上表者'),('李承嗣','受赏表领者')],when='897年十一月战后；确日未载',note='表领不等于已实据钱镠镇海辖地；不把挂名任命写成杭州易主。')
person('史俨',45,'与李承嗣获杨行密优待，长期效力者')
for name in ['李承嗣','史俨']:
 claim('person',people[name],'description','主书总述杨行密厚待李承嗣、史俨，以第舍姬妾优赐，二人为其尽力屡立功，终卒淮南。',45,quote='行密待承嗣及史俨甚厚，第舍、姬妾，咸选其尤者赐之，故二人为行密尽力，屡立功，竟卒于淮南。',note='跨年总述；不将其后死亡定897，也不猜未具名家人或每场战功。')
claim('event','event_zztj_261_0897_qingkou_pang_defeated_killed','description','主书总评杨行密由清口胜利保据江淮，朱全忠不能与争。',45,quote='行密由是遂保据江、淮之间，全忠不能与之争。',note='主书对战后局势的总述，不推从此双方永久无交战。')
e('he_consort_queen','昭宗立淑妃何氏为皇后',46,'戊寅，立淑妃何氏为皇后。',[('唐昭宗','立后者'),('何氏','受立皇后者')],when='897年十一月戊寅',note='十一月由前段月标继承；旧唐书光化元年四月制册日期不同，分列不覆盖。')
person('德王',46,'何皇后所生德王；沿已有李祐主体')
claim('person',people['何氏（唐昭宗皇后）'],'description','何皇后为东川人，生德王、辉王。',46,quote='后，东川人，生德王、辉王。',note='德王沿已有李祐封号，辉王为上段皇子祚；不将东川籍贯写成任地。')
person('王潮',47,'威武节度使，病中安排继承后去世');person('审知',47,'王潮弟，观察副使，受命知军府事')
claim('person',people['王审知'],'description','主书追述王审知为观察副使，有过王潮仍捶挞，审知无怨色。',47,quote='威武节度使王潮弟审知，为观察副使，有过，潮犹加捶挞，审知无怨色。',note='惯常背景不另造897年某日惩罚案或心理诊断。')
e('wang_chao_assigns_shenzhi','王潮病，舍四子命王审知知军府事',47,'潮寝疾，舍其子延兴、延虹、延丰、延休，命审知知军府事。',[('王潮','安排继承者'),('审知','受命知事者'),('王延兴','未被选择的儿子'),('王延虹','未被选择的儿子'),('王延丰','未被选择的儿子'),('王延休','未被选择的儿子')],when='897年十二月王潮去世前；确日未载',place='福建',note='舍子不等于杀子或四子夺位；各王姓沿父子上下文，不猜生卒。')
e('wang_chao_dies','王潮去世',47,'十二月，丁未，潮薨。',[('王潮','去世者')],when='897年十二月丁未',place='福建')
claim('person',people['王潮'],'death_year','乾宁四年（897）十二月丁未，王潮去世。',47,quote='十二月，丁未，潮薨。')
e('shenzhi_offers_shengui_declines','王审知让位王审邽，审邽辞不受',47,'审知以让其兄泉州刺史审邽，审邽以审知有功，辞不受。',[('审知','让位者'),('审邽','辞受者')],when='897年十二月王潮死后；确日未载',place='福建、泉州',note='辞受不建王审邽继任福建事件。')
e('shenzhi_self_deputy_reports','王审知自称福建留后并表朝廷',47,'审知自称福建留后，表于朝廷。',[('审知','自称上表者')],when='897年十二月王潮死后；确日未载',place='福建',note='自称不是朝廷正式除授；后年威武留后任命留后批。')
e('wang_jian_returns_zi_chengdu','王建自梓州还成都',48,'壬戌，王建自梓州还。戊辰，至成都。',[('王建','还镇者')],when='897年十二月壬戌启程、戊辰至成都',place='梓州、成都')
e('nanzhao_zhongxing_sends_letters','南诏骠信舜化有上书，王建谏朝廷不以诏答',48,'是岁，南诏骠信舜化有上皇帝书函及督爽牒中书木夹，年号中兴。朝廷欲以诏书报之。王建上言：“南诏小夷，不足辱诏书。臣在西南，彼必不敢犯塞。”从之。',[('舜化（南诏骠信）','上书政权之主'),('王建','谏不辱诏者')],when='897年是岁；确月日未载',description='南诏骠信舜化有上皇帝书函及督爽牒中书木夹，年号中兴；朝廷拟以诏答，王建谏不以诏书报之，朝廷采纳。',note='有上为谓词，名字舜化按南诏语境识别，不命名舜化有；骠信督爽为官号。彼必不犯是王判断，非已经核实永不犯塞；不把是岁定十二月壬戌。')

# 新的有向家属关系；复用已有王潮—王审知兄长关系。
def relation(a,b,typ,n,q,description=None,reuse=False):
 ak=people[alias.get(a,a)];bk=people[alias.get(b,b)];key=f'relationship_{ak}_{bk}_{typ}'
 text=description or f'{alias.get(a,a)}是{alias.get(b,b)}的{typ}。'
 B['person_relationships'].append(dict(key=key,person_a_key=ak,person_b_key=bk,relation_type=typ,description=text,status='draft'))
 if reuse:reused.add(key)
 claim('person_relationship',key,'description',text,n,quote=q,note='方向为A是B的该身份；本段记身份而非本年关系始建，不补生育、收养确日。')
relation('顾彦晖','瑶','养父',41,'命其假子瑶杀己及同饮者',description='顾彦晖是瑶的养父；本批以瑶（顾彦晖假子）识别该未明载姓的假子。')
for child in ['祕','祚','祺']:relation('唐昭宗',child,'父亲',43,Q[43]['text'])
relation('唐昭宗','何氏','丈夫',46,'戊寅，立淑妃何氏为皇后。')
for child in ['德王','辉王']:relation('何氏',child,'母亲',46,'后，东川人，生德王、辉王。')
relation('王潮','审知','兄长',47,'威武节度使王潮弟审知',description='《通鉴》称王审知为王潮之弟；王潮是王审知的兄长。',reuse=True)
for child in ['王延兴','王延虹','王延丰','王延休']:relation('王潮',child,'父亲',47,'潮寝疾，舍其子延兴、延虹、延丰、延休，命审知知军府事。')
relation('审邽','审知','兄长',47,'审知以让其兄泉州刺史审邽')

supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
 record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_261_0897_05_{len(B["claims"])+1:04d}'
 B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
 supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('xintangshu-010-897-october','event','event_zztj_261_0897_hou_shao_surrenders_wang','description','《新唐书》十月壬子记遂州刺史侯绍叛附王建。','十月壬子，遂州刺史侯紹叛附于王建。',41,'同人同日，主书称知遂州、降；补书官称叛附词分保，不改主书中性受降叙述。','corroborates')
extra('xintangshu-010-897-october','event','event_zztj_261_0897_wang_renwei_surrenders','time_original','《新唐书》记乙卯合州刺史王仁威叛附王建。','乙卯，合州刺史王仁威叛附于建。',41,'承前十月，官称与知合州分列。','corroborates')
extra('xintangshu-010-897-october','event','event_zztj_261_0897_gu_yao_kills_gu_and_self','time_original','《新唐书》本纪记十月庚申梓州陷，顾彦晖死。','庚申，建陷梓州，劍南東川節度使顧彥暉死之。',41,'同日印证死亡，但不支持主书具体执行者。','corroborates')
extra('xintangshu-186-897-gu-death','event','event_zztj_261_0897_gu_yao_kills_gu_and_self','description','《新唐书》传记写顾彦晖手杀妻子后自刎，主书写命假子瑶杀己及同饮者后自杀。','彥暉手殺妻子，乃自刎，宗族諸將皆死，麾下兵猶七萬。',41,'死法和杀人主语不同，保留异说；不据此覆盖主书，瑶的死亡仍只凭主书。','conflicts')
extra('xintangshu-186-897-gu-death','event','event_zztj_261_0897_wang_enters_zi_sends_zongwan','description','《新唐书》顾传亦记围急后麾下兵犹七万。','麾下兵猶七萬。',41,'同规模记载，不把两书当完全独立统计或精确验算。','corroborates')
extra('xintangshu-010-897-october','event','event_zztj_261_0897_zuo_hui_prince','description','《新唐书》本纪记甲子封子祕景王、祚辉王、祺祁王。','甲子，封子祕為景王，祚輝王，祺祁王。',43,'同日与同名封号，祚未来改名另核；这里只挂三王共同授封上下文。','corroborates')
extra('jiutangshu-020-hui-prince-identity','person',people['唐昭宣帝'],'description','本段辉王祚与既有唐昭宣帝（哀帝柷）为同一人，是昭宗第九子，母何氏。','哀皇帝諱柷，昭宗第九子，母曰積善太后何氏。景福元年九月三日，生於大內。乾寧四年二月，封輝王，名祚。',43,'本引用于同人识别，不将哀帝称号倒填897；授封日期差异另列，不因日期异记拆成两人。','corroborates')
extra('jiutangshu-020-hui-prince-identity','event','event_zztj_261_0897_zuo_hui_prince','time_original','《旧唐书》哀帝本纪记乾宁四年二月封辉王名祚；主书及新唐书本纪记十月甲子封辉王。','乾寧四年二月，封輝王，名祚。',43,'同人识别成立，封王月日仍有异记；保两书日期，不推出二次确定授封。','conflicts')
extra('jiuwudaishi-022-897-niu-retreat','event','event_zztj_261_0897_niu_rearguard_retreat_snow','description','《旧五代史》牛存节传记收合所部及败兵八千余，四日不食而得旋师。','存節遏其後，諸將釋騎步鬥，諸軍稍得濟，收合所部並敗兵共八千餘人，至於淮涘，時不食已四日矣。',45,'主书还者不满千人与补书收合八千余的时间、统计范围可能不同，并列不强算战损；其年由前段乾宁四年及后五年核。','adds')
extra('jiuwudaishi-055-897-li-chengsi','event','event_zztj_261_0897_qingkou_pang_defeated_killed','description','《旧五代史》李承嗣传记朱瑾率三万与承嗣伏清口、大败汴人并生获庞师古。','朱瑾率淮南軍三萬，與承嗣設伏於清口，大敗汴人，生獲龐師古。',45,'生获与主书斩首叙述不同，可能先获后杀但未证实，不编造确定执行链。传以其年九月出师统叙，不倒改主书十一月战日。','conflicts')
extra('jiuwudaishi-055-897-li-chengsi','event','event_zztj_261_0897_li_chengsi_reward_zhenhai','description','《旧五代史》记行密留李承嗣不遣，奏授检校太尉、领镇海节度使。','行密嘉其雄才，留而不遣，仍奏授檢校太尉，領鎮海軍節度使。',45,'检校太尉为补官称，奏授不推实际占领两浙；夹注十国春秋不作本次新增来源。','adds')
extra('jiutangshu-020-898-he-queen','event','event_zztj_261_0897_he_consort_queen','time_original','《旧唐书》记光化元年（898）四月庚子制淑妃何氏宜册皇后；主书记897年十一月戊寅立后。','四月庚子，制淑妃何氏宜冊為皇后。',46,'上一段光化元年春正月头已导出归档（p003254），本段承898年；制宜册与实际立可能阶段不同，未核前保日期差异。','conflicts')
extra('jiutangshu-020-898-context','event','event_zztj_261_0897_he_consort_queen','time_original','《旧唐书》何氏宜册条所承年首为光化元年。','光化元年春正月辛未朔，車駕在華州。',46,'本引只证相邻四月条年首位置，并非正月立后；相邻完整快照保存。','adds')
extra('jiuwudaishi-134-897-wang-chao','event','event_zztj_261_0897_wang_chao_assigns_shenzhi','description','《旧五代史》亦记王潮病中舍延兴延虹延丰延休，命王审知知军府事。','潮寢疾，舍其子延興、延虹、延豐、延休，命審知知軍府事。',47,'同安排，后续正式节度任命不提前置本年。','corroborates')
extra('jiuwudaishi-134-897-wang-chao','event','event_zztj_261_0897_shenzhi_offers_shengui_declines','description','《旧五代史》亦记潮十二月丁未死，审知让兄审邽而兄辞。','十二月丁未，潮薨，審知以讓其兄審邽，審邽以審知有功，辭不受。',47,'同日与让位过程；王审邽兄长方向正确。','corroborates')
extra('xinwudaishi-068-897-wang-succession','event','event_zztj_261_0897_shenzhi_self_deputy_reports','description','《新五代史》王氏世家记乾宁四年王潮卒、王审知代立。','乾寧四年，潮卒，審知代立。',47,'只取本年继承一句；后文拜节度封王跨年，不能全定897。','corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(37,49):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十二段连续校核；三路南征与清口、寿州、淠水追击分录，战后总述不混当年死亡。顾死法、何后册立纪年、败兵收合人数与归还范围、庞生获与斩首异记各保。家属方向明示，福建自称留后不写已正式除授；南诏是岁不定十二月。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=261,year=897,primary_source_key=primary(38),primary_source_keys=[primary(37),primary(38),primary(46)],paragraphs=[Q[n]['id'] for n in range(37,49)],next_paragraph=Q[49]['id'],coverage='本年50段中的第37—48段连续整理，本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
