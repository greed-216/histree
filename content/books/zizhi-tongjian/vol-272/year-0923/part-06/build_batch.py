# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 25–29."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 77))
specs = [
 ('tongjian-272-923-august',YEAR/'part-05/sources/library/tongjian-272-923-august','d77c4a74','司马光等'),
 ('tongjian-272-923-autumn-plan',P/'sources/library/tongjian-272-923-autumn-plan','460d5032','司马光等'),
 ('jiuwudaishi-029-923-autumn-plan',P/'sources/library/jiuwudaishi-029-923-autumn-plan','460d5032','薛居正等'),
 ('jiuwudaishi-030-923-zhongdu',P/'sources/library/jiuwudaishi-030-923-zhongdu','460d5032','薛居正等'),
 ('xinwudaishi-063-shu-remonstrance',P/'sources/library/xinwudaishi-063-shu-remonstrance','460d5032','欧阳修'),
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p025-p029',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/272.txt').read_text().splitlines()
for n in range(25, 30):
    assert Q[n]['text'] == lines[Q[n]['source_line'] - 1]
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
people, used, reused, supplements = {}, {}, {'tongjian-272-923-august','xinwudaishi-005-923-founding'}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷272·同光元年（923）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_272_0923_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'曹氏（李存勖母）','太妃':'刘氏（李克用妻）',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦','曹氏':'曹氏（李存勖母）','刘氏':'刘氏（李克用妻）','武皇':'李克用','考晋王':'李克用','上':'李存勖','帝':'李存勖','执宜':'执宜（李存勖曾祖）','国昌':'李国昌','继岌':'李继岌','硃守殷':'朱守殷','硃安殷':'朱守殷','守殷':'朱守殷','王铁枪':'王彦章','彦章':'王彦章','翔':'敬翔','顺密':'卢顺密','嗣源':'李嗣源','遂严':'刘遂严','颙':'燕颙','梁末帝':'朱友贞','崇韬':'郭崇韬','延孝':'康延孝','延光':'范延光','宗侃':'王宗侃','赵':'赵岩','张':'张汉杰','任团':'任团','圜':'任圜','团':'任团','绍斌':'赵德钧','李绍斌':'赵德钧','凝':'段凝','在珣':'顾在珣','彦朗':'顾彦朗','嘉王宗寿':'王宗寿','魏国夫人刘氏':'刘夫人（李存勖妻）','李绍奇':'夏鲁奇','廷隐':'赵廷隐','嗣彬':'刘嗣彬','知俊':'刘知俊','振':'李振','张宗奭':'张全义'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷272同光元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='923年本段；确日未载', note='', year=923, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_272_0923_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_272_0923_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。',source=source)
    return key

def relationship(a,b,kind,n,quote,note,source=None):
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
    a=next(x['name'] for x in B['people'] if x['key']==pa); b=next(x['name'] for x in B['people'] if x['key']==pb)
    matches={}
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_272_0923_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)

# Paragraph 25: Shu court, remonstrance and the ninth-day banquet.
E=event('shu_court_companions','王宗衍以韩昭、潘在迎、顾在珣为狎客，侍游宴',25,'蜀主以文思殿大学士韩昭、内皇城使潘在迎、武勇军使顾在珣为狎客，陪侍游宴，',[('蜀主','以三人为狎客的王宗衍'),('韩昭','文思殿大学士、狎客'),('潘在迎','内皇城使、狎客'),('顾在珣','武勇军使、狎客')],when='主书923年九月前背景；狎客起始确年未载',year=None,place='前蜀宫廷',note='侍宴为持续行为，未将背景习惯全部定九月某日；狎客为史书称谓，官职不是本段皆新任。')
claim('event',E,'description','《新五代史》同列韩昭潘在迎顾在珣等狎客，另有严旭。',25,'以韓昭、潘在迎、顧在珣、嚴旭等為狎客；','范围稍异，主书三人、新史含严旭独立保存，不改三人名单为全部。',source='xinwudaishi-063-shu-remonstrance',relation='adds')
relationship('顾彦朗','顾在珣','父亲',25,'在珣，彦朗之子也。','彦朗按前文东川顾彦朗，同姓在珣承上；父亲方向明确，不混弟顾彦晖。')
event('shu_governance_narrative','主书述宋光嗣等专断，王锴庾传素未规正',25,'时枢密使宋光嗣等专断国家，恣为威虐，务徇蜀主之欲以盗其权。宰相王锴、庾传素等各保宠禄，无敢规正。',[('宋光嗣','被述专断的枢密使'),('王锴','被述未规正的宰相'),('庾传素','被述未规正的宰相')],when='923年本段所述形势；起始年未载',place='前蜀',note='威虐盗权保宠为作者政治评价，归属主书，不当已独立核实动机或新任官事件。')
event('pan_urges_punish_remonstrators','主书记潘在迎屡劝蜀主诛谏者',25,'潘在迎每劝蜀主诛谏者，无使谤国。',[('潘在迎','被记每劝者'),('蜀主','受劝者')],when='本段背景持续言论；确年未载',year=None,place='前蜀',note='每劝不等实际诛杀，未指具体死者，不虚建。')
event('liu_zan_satirical_drawing','嘉州司马刘赞献陈后主三阁图及讽歌',25,'嘉州司马刘赞献陈后主三阁图，并作歌以讽；',[('刘赞','献图歌讽谏者'),('蜀主','受讽对象')],when='923年主书九月前本段；确日未载',place='嘉州、蜀廷',note='陈后主图是讽谏材料，不在923年建立陈后主新任或宴游事件。')
event('pu_yuqing_forthright_answer','蒲禹卿对策切直，王宗衍未用其言',25,'贤良方正蒲禹卿对策语极切直；蜀主虽不罪，亦不能用也。',[('蒲禹卿','对策者'),('蜀主','未罪也未用者')],when='923年主书九月前本段；确日未载',place='前蜀',note='贤良方正按原书称谓，未据此赋具体中第日期；不能用为主书评价及结果，不构造实际惩罚。')
E=event('shu_double_ninth_remonstrance','重阳宣华苑宴，王宗寿谏社稷危，韩昭潘在迎笑为酒悲',25,'九月，庚戌，蜀主以重阳宴近臣于宣华宛，酒酣，嘉王宗寿乘间极言社稷将危，流涕不已。韩昭、潘在迎曰：“嘉王好酒悲。”因谐笑而罢。',[('蜀主','重阳宴近臣者'),('嘉王宗寿','哭谏者'),('韩昭','称酒悲而谐笑者'),('潘在迎','称酒悲而谐笑者')],when='923年九月庚戌；主书重阳纪时',place='宣华苑',note='主书宣华宛疑苑异字，展示苑由新史明确；好酒悲是讥语而非医学判断，未改原字。')
claim('event',E,'description','《新五代史》同记九日宣华苑宴，宗寿以社稷言泣，狎客讥为酒悲。',25,'嘗以九日宴宣華苑，嘉王宗壽以社稷為言，言發泣涕。韓昭等曰：「嘉王酒悲爾！」','新史尝未给该年干支，主书923庚戌作为主线，不能宣称两书均记庚戌。',source='xinwudaishi-063-shu-remonstrance',relation='corroborates')
# Paragraph 26: crisis and competing proposals.
E=event('tang_autumn_supply_crisis','主书记唐军刍粮损失、孔谦急敛、民流亡，库存不足半年',26,'自德胜失利以来，丧刍粮数百万，租庸副使孔谦暴敛以供军，民多流亡，租税益少，仓廪之积不支半岁。',[('孔谦','被记暴敛供军的租庸副使')],when='923年德胜失利以来至九月朝城会议',place='后唐军民',note='数百万未载单位，不填石数；暴敛与民亡为史书述因果，带来源，不作现代财政统计。')
claim('event',E,'description','《旧五代史》同记编户流亡、军赋不支半年。',26,'編戶流亡，計其軍賦，不支半年。','同阶段库存忧困互证，未补数百万具体单位。',source='jiuwudaishi-029-923-autumn-plan',relation='corroborates')
event('duan_raids_chansouth','段凝进临河南，澶西相南有寇掠',26,'帝在朝城，梁段凝进至临河之南，澶西、相南，日有寇掠。',[('段凝','推进临河南的梁将'),('帝','驻朝城的李存勖')],when='923年九月朝城会议前',place='朝城、临河之南、澶西、相南',note='日有为形势，不虚构每天独立战斗或具名受害村。')
event('lu_wang_guide_khitan_south','卢文进、王郁引契丹屡过瀛涿之南',26,'卢文进、王郁引契丹屡过瀛、涿之南，传闻俟草枯冰合，深入为寇。',[('卢文进','引契丹者'),('王郁','引契丹者')],when='923年九月所述持续侵入；确日未载',place='瀛州、涿州之南',note='实际屡过和传闻待冰合深入分开，未把传闻冬季行动当已执行，不默认阿保机亲领。')
E=event('shaohong_proposes_territory_exchange','李绍宏等建议以郓换卫州黎阳、画河休兵，李存勖不悦',26,'宣徽使李绍宏等皆以为郓州城门之外皆为寇境，孤远难守，有之不如无之，请以易卫州及黎阳于梁，与之约和，以河为境，休兵息民，俟财力稍集，更图后举。',[('李绍宏','建议交换议和者'),('帝','不悦而未采方案者')],when='923年九月朝城会议',place='朝城、郓州、卫州、黎阳',note='是建议，未形成换地条约或实际交割；皆为寇境属于会议判断。')
claim('event',E,'description','《旧五代史》同载换卫州黎阳及郓、指河休兵方案，未具名献者。',26,'今若馳檄告諭梁人，卻衛州、黎陽以易鄆州，指河為界，約且休兵。','该书或曰而未李绍宏名，人物归属以主书为据。',source='jiuwudaishi-029-923-autumn-plan',relation='corroborates')
E=event('chongtao_advocates_attack_bian','郭崇韬独答李存勖，主张留守魏杨刘、合郓兵直取大梁',26,'陛下若留兵守魏，固保杨刘，自以精兵与郓州合势，长驱入汴，彼城中既空虚，必望风自溃。',[('郭崇韬','主张直接进汴者')],when='923年九月朝城会议',place='朝城、魏州、杨刘、郓州、大梁',note='郭崇韬判断梁城空虚、兵将能力为其策略陈说，不当已核实独立普查；留守和行军是建议非本段已完成。')
claim('event',E,'description','郭崇韬称详询康延孝，认为成败机在今岁。',26,'臣尝细询康延孝以河南之事，度已料彼，日夜思之，成败之机决在今岁。','显示情报来源，不能把复述康说当第三份完全独立确证。')
claim('event',E,'description','《旧五代史》同记郭崇韬劝亲御直趋汴州。',26,'時郭崇韜勸帝親禦六軍，直趨汴州，半月之間，天下可定。','半月为献策预估，未将实际灭梁期硬设半月。',source='jiuwudaishi-029-923-autumn-plan',relation='corroborates')
event('cunxu_decides_despite_astrology','李存勖决意进军，不听司天不利之奏',26,'帝曰：“此正合朕志。丈夫得则为王，失则为虏，吾行决矣！”司天奏：“今岁天道不利，深入必无功。”帝不听。',[('帝','决志并不听占候者')],when='923年九月朝城议策后',place='朝城',note='天命及天道言论保留为历史行动中的信念，不作现代因果；司天未名不造术者姓名。')
# Paragraph 27: Dingfang encounter and the order to send families home.
E=event('dingfang_frontline_defeat','李嗣源遣李从珂逆战，在递坊败王彦章前锋',27,'王彦章引兵逾汶水，将攻郓州，李嗣源遣李从珂将骑兵逆战，败其前锋于递坊镇，获将士三百人，斩首二百级，彦章退保中都。',[('王彦章','渡汶拟攻郓的梁主将'),('李嗣源','遣逆战者'),('李从珂','逆战败前锋者')],when='923年九月戊辰捷奏前；战日主书未单列',place='汶水、递坊镇、中都',note='主书戊辰明确捷奏至，不直接断同日开战；俘三百、斩二百口径不同，不重复相加成阵亡五百。')
claim('event',E,'description','《旧五代史》记戊辰至汶、递公镇交战，嗣源以精骑败梁，俘任钊田章等三百。',27,'戊辰，梁將王彥章率眾至汶河，李嗣源遣騎軍偵視，至遞公鎮，梁軍來挑戰，嗣源以精騎擊而敗之，生擒梁將任釗、田章等三百人，俘斬二百級，彥章引眾保於中都。','递坊/递公地名异字并存；主书李从珂率，旧史归嗣源统军，不改两者为互斥将领；旧史俘斩/主书斩首口径分别存。',source='jiuwudaishi-029-923-autumn-plan',relation='adds')
for name in ['任钊','田章']:
 qt='生擒梁將任釗、田章等三百人，';pk=person(name,27,'递公之战被俘梁将',qt,source='jiuwudaishi-029-923-autumn-plan');ek='participation_zztj_272_0923_dingfang_captive_'+pk
 B['person_events'].append(dict(key=ek,person_key=pk,event_key=E,role='递公之战被俘梁将',status='draft'));claim('person_event',ek,'role',name+'是旧史明示的被俘梁将。',27,qt,'同事补名，不虚定死者，后续生卒待考。',source='jiuwudaishi-029-923-autumn-plan')
event('dingfang_victory_report','递坊捷奏至朝城，李存勖大喜',27,'戊辰，捷奏至朝城，帝大喜，谓郭崇韬曰：“郓州告捷，足壮吾气！”',[('帝','受捷奏者'),('郭崇韬','听帝告语者')],when='923年九月戊辰',place='朝城',note='这是捷奏日，独立于交战具体日判断；大喜为主书叙述。')
E=event('army_families_sent_home','李存勖命军中将士家属归兴唐',27,'己巳，命将士悉遣其家归兴唐。',[('帝','遣家属归兴唐令者')],when='923年九月己巳',place='唐军、兴唐府',note='命令不等每名家属均当天已到家；另十月刘夫人继岌归属于具体皇室安排。')
claim('event',E,'description','《旧五代史》同记己巳军中家属归邺。',27,'己巳，下令軍中將士家屬並令歸鄴。','邺兴唐同段异名；令与实际抵达分明。',source='jiuwudaishi-029-923-autumn-plan',relation='corroborates')
# Paragraph 28: chronicle astronomical record.
E=event('solar_eclipse_october','史书记十月辛未朔日食',28,'冬，十月，辛未朔，日有食之。',[],when='923年十月辛未朔',place='史书未载具体观测地点',note='按史载天象，不强换公历、现代轨迹或食分；不是以日食解释梁亡。')
claim('event',E,'description','《旧五代史》同记同光元年十月辛未朔日食。',28,'同光元年冬十月辛未朔，日有食之。','同日天象记录互证，未完成现代天文回算。',source='jiuwudaishi-030-923-zhongdu',relation='corroborates')
# Paragraph 29: the Zhongdu operation, not yet Liang's fall.
E=event('imperial_family_returns_xingtang','李存勖遣刘夫人、李继岌归兴唐，作出决战安排',29,'帝遣魏国夫人刘氏、皇子继岌归兴唐，与之诀曰：',[('帝','遣妻子与皇子者'),('魏国夫人刘氏','归兴唐的刘夫人'),('继岌','归兴唐的皇子')],when='923年十月壬申出兵前；主书确日未列',place='兴唐府',note='刘夫人是妻，不能沿用p7李克用妻刘太妃；旧史同句称皇后为后来称谓，不提前制造923册后事件。')
claim('event',E,'description','《旧五代史》记辛未当日刘氏继岌归邺。',29,'是日，皇后劉氏、皇子繼岌歸鄴宮，帝送於離亭，歔欷而別。','是日承辛未朔，为旧史补时间；皇后是该史称谓，主书本时魏国夫人独立保留。',source='jiuwudaishi-030-923-zhongdu',relation='adds')
claim('event',E,'description','李存勖称若失败则聚家魏宫而焚，表达决战命令。',29,'若其不济，当聚吾家于魏宫而焚之！','若为失败条件下的指令，本段未发生焚宫杀家，不建立执行事件。')
E=event('tokyo_defence_four_officials','豆卢革、李绍宏、张宪、王正言奉命同守东京',29,'仍命豆卢革、李绍宏、张宪、王正言同守东京。',[('帝','留守命令者'),('豆卢革','奉命同守者'),('李绍宏','奉命同守者'),('张宪','奉命同守者'),('王正言','奉命同守者')],when='923年十月壬申进军前',place='东京、兴唐府',note='东京仍指魏兴唐，不是后来洛阳或现代东京；军职据任务，未推所有人正式同任留守官。')
claim('event',E,'description','《旧五代史》同列四人守邺城。',29,'詔宣徽使李紹宏、宰相豆盧革、租庸使張憲、興唐尹王正言同守鄴城。','四人各原职明确，不改成新官名。',source='jiuwudaishi-030-923-zhongdu',relation='corroborates')
E=event('cunxu_crosses_yangliu_to_yun','李存勖军自杨刘渡河，翌日至郓州',29,'壬申，帝以大军自杨刘济河，癸酉，至郓州，',[('帝','渡河进郓主将')],when='923年十月壬申渡河，癸酉至郓',place='杨刘、郓州',note='两日步骤留原干支，未给公历或现代线路。')
claim('event',E,'description','《旧五代史》同记壬申渡、癸酉郓州。',29,'壬申，帝御大軍自楊劉濟河。癸酉，至鄆州。','同日同路线互证。',source='jiuwudaishi-030-923-zhongdu',relation='corroborates')
event('tang_night_crosses_wen','唐军夜越汶水，以李嗣源前锋进中都',29,'中夜，进军逾汶，以李嗣源为前锋，',[('帝','率军越汶者'),('李嗣源','前锋将')],when='923年十月癸酉夜',place='汶水、中都途中',note='承癸酉夜，旧史夜三鼓补夜次；不直接作现代时间1时。')
E=event('zhongdu_liang_defeat','唐军败梁追中都，围城后再破溃围兵',29,'甲戌旦，遇梁兵，一战败之，追至中都，围其城。城无守备，少顷，梁兵溃围出，追击，破之。',[('帝','率唐军破梁者'),('李嗣源','唐前锋')],when='923年十月甲戌旦',place='中都',note='无守备为史书记形势，并非该城历史从无城墙；两步追击分述，不当两场同名年度事件。')
claim('event',E,'description','《旧五代史》同记甲戌攻中都梁自溃。',29,'甲戌，帝攻之，中都素無城守，師既雲合，梁眾自潰。','同役补证；旧史素无城守不是现代考古定论。',source='jiuwudaishi-030-923-zhongdu',relation='corroborates')
E=event('xia_luqi_captures_yanzhang','李绍奇刺伤并擒王彦章',29,'王彦章以数十骑走，龙武大将军李绍奇单骑追之，识其声，曰：“王铁枪也！”拔槊刺之，彦章重伤，马踬，遂擒之，',[('王彦章','逃走重伤被俘者'),('李绍奇','追刺擒敌的夏鲁奇')],when='923年十月甲戌中都败后',place='中都附近',note='李绍奇复用有别名的夏鲁奇；伤重被俘不当此刻阵亡，乙亥处斩为后段。')
E=event('zhongdu_officers_captured','中都役俘张汉杰、李知节、赵廷隐、刘嗣彬等',29,'并擒都监张汉杰、曹州刺史李知节、裨将赵廷隐、刘嗣彬等二百馀人，斩首数千级。',[('张汉杰','被俘都监'),('李知节','被俘曹州刺史'),('赵廷隐','被俘裨将'),('刘嗣彬','被俘裨将')],when='923年十月甲戌中都之战',place='中都',note='二百余俘与斩首数千口径分开；被俘不推全部死刑或立即归降。')
claim('event',E,'description','《旧五代史》补被俘康文通、王山兴，战果称斩馘二万、马千匹。',29,'是日，擒梁將王彥章及都監張漢傑、趙廷隱、劉嗣彬、李知節、康文通、王山興等將吏二百餘人，斬馘二萬，奪馬千匹。','主书数千与旧史二万兵杀数显异，不择大数；补名单保留出处，未据此推个别人物生卒。',source='jiuwudaishi-030-923-zhongdu',relation='conflicts')
claim('person',people['赵廷隐'],'description','主书记赵廷隐为开封人。',29,'廷隐，开封人；','籍贯原地名，不推现代户籍地址。')
relationship('刘嗣彬','刘知俊','族子',29,'嗣彬，知俊之族子也。','原称族子，A嗣彬是B知俊的族子；不自行改亲儿子或推具体侄父，已明确方向。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,30):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='连续前蜀九月记事与唐军决策、中都战；重复习惯未强定日期、宣华宛疑字保留、九月戊辰是捷奏主书记、朝候不作因果、妻刘氏与嫡母分人、李绍奇夏鲁奇同人、伤俘非处斩、斩数千/二万异文并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(25,30)],next_paragraph=Q[30]['id'],supplements=supplements,coverage='卷272正文第25—29段，原文件30—34行；p25复用上一批主书快照，p26—29完整原TXT分段覆盖。',reviewed_questions=[
 {'paragraph_id':Q[25]['id'],'note':'狎客起始和每劝等持续行为年null；政治评价带作者归属；顾彦朗父顾在珣明确；九月庚戌宣华宛/新史苑保留原字，九日同事补书不伪称同给干支。'},
 {'paragraph_id':Q[26]['id'],'note':'数百万粮损单位未知不填石；冬侵传闻不提前成事；换郓卫黎阳为未采建议；郭询康情报不是独立确证第三来源；天命天道归当事言论。'},
 {'paragraph_id':Q[27]['id'],'note':'主书戊辰明确捷奏、旧史战同日；递坊/递公地名保留；李嗣源统军与李从珂率逆战不互斥；任钊田章旧史补被俘，不虚造死亡。'},
 {'paragraph_id':Q[28]['id'],'note':'日食只据史载，未现代回算食分和公历；不关联梁亡的超自然因果。'},
 {'paragraph_id':Q[29]['id'],'note':'魏国夫人妻刘氏不同李克用刘妻，旧史称皇后是称谓回用未提前册后；东京兴唐不是洛阳；夏鲁奇别名李绍奇复用，俘彦章未死；二百俘、斩数千与二万分层；刘嗣彬族子不推具体父母或亲子。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
