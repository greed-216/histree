"""Curate consecutive Tongjian volume 271, year 921, paragraphs 19–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 25))
specs = [
 ('tongjian-271-921-zhen-ding',YEAR/'part-03/sources/library/tongjian-271-921-zhen-ding','57d33707','司马光等'),
 ('tongjian-271-921-yearend',P/'sources/library/tongjian-271-921-yearend','4fea316c','司马光等'),
 ('new-wudaishi-61-yang-pu',YEAR/'part-01/sources/library/new-wudaishi-61-yang-pu','668adafc','欧阳修'),
 ('xinwudaishi-065-dayue-founding',ROOT/'content/books/zizhi-tongjian/vol-270/year-0917/part-01/sources/library/xinwudaishi-065-dayue-founding','8cdf5b01','欧阳修'),
 ('jiuwudaishi-029-han-zhengshi',P/'sources/library/jiuwudaishi-029-han-zhengshi','4fea316c','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0921-p019-p024',
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
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(19, 25):
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
people, used, reused, supplements = {}, {}, {'tongjian-271-921-zhen-ding','new-wudaishi-61-yang-pu','xinwudaishi-065-dayue-founding'}, []

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
        citation = f'卷271·龙德元年（921）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0921_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','高祖':'王建','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271龙德元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='921年本段；确日未载', note='', year=921, place='五代十国', source=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0921_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_271_0921_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
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
        row=dict(key=f'relationship_zztj_271_0921_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)
event('xu_wen_urges_wu_southern_sacrifice','徐温劝吴王郊祀，主张事天贵诚、不必多费',19,
 '吴徐温劝吴王祀南郊，',[('徐温','劝吴王祀南郊者'),('吴王','受劝郊祀的杨溥')],
 when='921年冬本段郊祀前；确日未载',place='吴',note='礼乐费用争论是当事人意见，不把唐灌枢脂百斛说法转成本次实际支出。')
claim('event',used[19][-1],'description','徐温主张事天贵诚，批评唐季奢费，不赞成照搬。',19,
 '吾闻事天贵诚，多费何为！','观点归属徐温，未视为已证的财政统计。')
event('yang_pu_sacrifices_south','吴王杨溥祀南郊，配太祖',19,
 '甲子，吴王祀南郊，配以太祖。',[('吴王','举行南郊祭祀者')],
 when='921年冬甲子；通鉴置十月后、十一月条前，新史记十一月',place='吴南郊',
 note='太祖为吴杨行密；本句未重列月份，不消除与新五代史十一月的编年差别。')
claim('event',used[19][-1],'time_original','《新五代史》记杨溥冬十一月祀天南郊、御天兴楼大赦。',19,
 '冬十一月，祀天於南郊。御天興樓，大赦。','明确记十一月，通鉴此段接十月而未重列月；两书位置与纪时并列，纸本考异待核。',source='new-wudaishi-61-yang-pu',relation='conflicts')
event('wu_amnesty_and_li_bian_promotion','吴乙丑大赦，徐知诰加同平章事、领江州观察使',19,
 '乙丑，大赦；加徐知诰同平章事，领江州观察使。',[('徐知诰','加同平章事、领江州观察使的李昪')],
 when='921年冬乙丑；甲子郊祀翌日',place='吴、江州',note='徐知诰沿用李昪主体，此时史载名保留；未把领职写为迁离广陵实驻江州。')
event('jiangzhou_fenghua_army_li_bian','吴以江州为奉化军，徐知诰领节度使',19,
 '寻以江州为奉化军，以知诰领节度使。',[('知诰','领奉化节度使者')],when='921年冬加官后之寻；确日未载',place='江州、奉化军')
event('xu_wen_recalls_cui_taichu','徐温欲征崔太初，徐知诰劝先使入朝留之',19,
 '徐温闻寿州团练使崔太初苛察失民心，欲征之，徐知诰曰：“寿州边隅大镇，征之恐为变，不若使其入朝，因留之。”',
 [('徐温','闻崔失民心而欲征者'),('崔太初','被拟征的寿州团练使'),('徐知诰','建议先令入朝而留之者')],
 when='921年冬本段；确日未载',place='寿州、吴',note='恐为变是徐知诰预测，未记寿州已经兵变。苛察失民心是本段叙述。')
event('cui_taichu_reappointed_general','徐温征崔太初为右雄武大将军',19,
 '温怒曰：“一崔太初不能制，如他人何！”征为右雄武大将军。',[('徐温','坚持征调者'),('崔太初','改任右雄武大将军者')],
 when='921年冬本段；确日未载',place='寿州、吴')
event('jin_attacks_zhenzhou_personally','李存勖令符存审、李嗣源守德胜，自攻镇州',20,
 '十一月，晋王使李存审、李嗣源守德胜，自将兵攻镇州。',
 [('晋王','亲自攻镇州者'),('李存审','守德胜的符存审'),('李嗣源','守德胜者')],when='921年十一月',place='德胜、镇州')
event('chujin_sends_chuqi_qijian_submission','张处瑾遣张处琪、齐俭谢罪请服，晋王不许',20,
 '张处瑾遣其弟处琪、幕僚齐俭谢罪请服，晋王不许，尽锐攻之，旬日不克。',
 [('张处瑾','遣弟幕僚请服者'),('处琪','奉遣谢罪请服的弟弟'),('齐俭','奉遣谢罪请服的幕僚'),('晋王','拒请服、攻城旬日未克者')],
 when='921年十一月',place='镇州',note='旬日是攻城时长，不换算具体止日；未因请服记城已降。')
relationship('处瑾','处琪','兄长',20,'张处瑾遣其弟处琪','其弟明确长幼，方向为张处瑾是张处琪的兄长。')
claim('event',used[20][-1],'description','《旧五代史》亦记张处琪、齐俭乞降，言犹不逊，被晋囚禁；双方筑土山攻守。',20,
 '張處瑾遣弟處琪、幕客齊儉等候帝乞降，言猶不遜，帝命囚之。時王師築土山以攻其壘，城中亦起土山以拒之，','补囚使、筑土山；通鉴称谢罪请服、旧史评言犹不逊，言辞评价分别保留，不假定使者已获释。',source='jiuwudaishi-029-han-zhengshi')
event('han_zhengshi_breaks_out_for_dingzhou','韩正时率千骑突围趋定州，欲求王处直援',20,
 '处瑾使韩正时将千骑突围出，趣定州，欲求救于王处直。',[('处瑾','遣千骑求救者'),('韩正时','率千骑突围求救者')],
 when='921年十一月',place='镇州、定州',note='欲求援不等于已会王处直；前文已记处直被幽，不删改此叙述。')
event('han_zhengshi_killed_after_pursuit','韩正时突围后被追击而死',20,
 '晋兵追至行唐，斩之。',[('韩正时','被追击而死者')],when='921年十一月',place='行唐',
 note='通鉴概述晋兵追斩；旧史另记残众保衡唐、彭赟斩韩正时以降，具体行凶者及地名另有说明。')
claim('event',used[20][-1],'description','《旧五代史》记追击后余众保衡唐，彭赟斩韩正时以降。',20,
 '餘眾保衡唐，賊將彭贇斬正時以降。','对通鉴晋兵追斩补具体过程；行唐与衡唐地名并列待核，不依异文填坐标。',source='jiuwudaishi-029-han-zhengshi',relation='conflicts')
pk=person('彭赟',20,'旧史记斩韩正时以降者','賊將彭贇斬正時以降。',source='jiuwudaishi-029-han-zhengshi')
ek='participation_zztj_271_0921_peng_yun_kills_han'
B['person_events'].append(dict(key=ek,person_key=pk,event_key=used[20][-1],role='旧史所记斩韩正时以降者',status='draft'))
claim('person_event',ek,'role','彭赟为旧史所记斩韩正时以降者。',20,
 '賊將彭贇斬正時以降。','并列具体参与，不把他凭空称晋军将领；贇规范为赟，原引不改。',source='jiuwudaishi-029-han-zhengshi')
claim('person',people['韩正时'],'death_year','韩正时于921年十一月突围后被杀。',20,'晋兵追至行唐，斩之。','主书本年十一月条；异书记行凶者另有说明。')
event('wang_yu_promises_khitan_riches','王郁以镇州美女金帛劝契丹主出兵',21,
 '契丹主既许卢文进出兵，王郁又说之曰：“镇州美女如云，金帛如山，天皇王速往，则皆己物也，不然，为晋王所有矣。”',
 [('卢文进','已获契丹主许出兵者'),('王郁','以镇州财色劝出兵者'),('契丹主','受劝的耶律阿保机')],
 when='921年契丹十二月攻幽前',place='契丹、镇州',note='美女金帛如云如山及可归己是王郁游说，不作为财物数量清单。')
event('shulu_remonstrates_khitan_southward','述律后谏南征，契丹主不听',21,
 '述律后谏曰：',[('述律后','谏阻南征的述律平'),('契丹主','不听谏而出兵者')],
 when='921年契丹十二月攻幽前',place='契丹',note='西楼羊马及晋王不可敌是述律后意见；未把远山疑似远出类转录问题静默改字。')
claim('event',used[21][-1],'description','述律后以西楼羊马富足、晋王善兵及可能危败劝阻，契丹主不听。',21,
 '吾闻晋王用兵，天下莫敌，脱有危败，悔之何及！”契丹主不听，','观点和风险预测归属述律后，不说本年已出现她所预测的战败。')
event('khitan_attacks_youzhou','契丹主攻幽州，李绍宏守城',21,
 '十二月，辛未，攻幽州，李绍宏婴城自守。',[('契丹主','率军攻幽州者'),('李绍宏','婴城自守者')],when='921年十二月辛未',place='幽州')
event('khitan_takes_zhuozhou','契丹围涿州旬日拔城，俘李嗣弼',21,
 '契丹长驱而南，围涿州，旬日拔之，擒刺史李嗣弼。',[('契丹主','南下攻涿州者'),('李嗣弼','被俘的涿州刺史')],
 when='921年十二月攻幽后；围涿旬日，确日未载',place='涿州',note='旬日是围城时长，不把拔城也填辛未。被擒不直接写成被杀。')
event('jin_rescues_dingzhou','契丹攻定州，王都告急，李存勖率五千亲军救援',21,
 '进攻定州，王都告急于晋，晋王自镇州将亲军五千救之，',[('契丹主','进攻定州者'),('王都','向晋告急者'),('晋王','率亲军五千自镇州援定者')],
 when='921年十二月契丹南下本段；确日未载',place='定州、镇州',note='五千是所将亲军史载数，未与翌年不同战斗重复合计。')
event('wang_sitong_guards_langshan','李存勖遣王思同戍狼山南拒契丹',21,
 '遣神武都指挥使王思同将兵戍狼山之南以拒之。',[('晋王','遣戍狼山南者'),('王思同','戍狼山南的神武都指挥使')],
 when='921年十二月救定州时',place='狼山之南',note='地名未配现代坐标，不凭狼山同名匹配现代山体。')
event('ni_kefu_repairs_jiangling_outer_wall','高季昌遣倪可福率万人修江陵外郭',22,
 '高季昌遣都指挥使倪可福以卒万人修江陵外郭，',[('高季昌','遣修外郭者'),('倪可福','率万人修外郭的都指挥使')],
 when='921年年末本段；确月日未载',place='江陵',note='外郭修筑不扩为全部城墙重建或新首都；人数按史载。')
event('gao_ji_chang_beats_ni_kefu','高季昌视工，因进度慢杖倪可福',22,
 '季昌行视，责功程之慢，杖之。',[('季昌','视察杖责者'),('倪可福','被杖责者')],when='921年江陵外郭工程中',place='江陵')
relationship('高季昌','高季昌女','父亲',22,'季昌女为可福子知进妇','高季昌之女明确；女子未载姓名，限定为倪知进妻。')
relationship('倪可福','知进','父亲',22,'季昌女为可福子知进妇','可福子知进明确，规范名倪知进。')
relationship('高季昌女','知进','妻子',22,'季昌女为可福子知进妇','妇为儿子之妻，已婚背景关系；未据所在921条反推成婚年份。')
event('gao_gives_silver_after_beating_ni','高季昌托女解释杖责是威众办事，赐倪可福白金',22,
 '季昌谓其女曰：“归语汝舅：吾欲威众办事耳。”以白金数百两遗之。',
 [('季昌','托女释杖责并赐白金者'),('高季昌女','受托告公公者'),('倪可福','被告知并受赐者')],
 when='921年杖倪可福后',place='江陵',note='舅在妻妇语境指公公，非女方娘家舅父；威众为高季昌自述，白金原称保留未换算现代货币。')
event('ni_shu_made_chancellor','汉以尚书左丞倪曙同平章事',23,Q[23]['text'],[('倪曙','尚书左丞、获同平章事者')],when='921年是岁；月日未载',place='汉',note='不把是岁任官等同年末某日；无官龄出生信息。')
claim('person',people['倪曙'],'description','《新五代史》另记贞明三年刘龑建国时倪曙工部侍郎、平章事。',23,
 '置百官，以楊洞潛為兵部侍郎，李衡禮部侍郎，倪曙工部侍郎，趙光胤兵部尚書，皆平章事。','新史前句贞明三年、下句皆平章事；为917年的既有职任补证，通鉴921尚书左丞不同阶段并列，不改本条为917。',source='xinwudaishi-065-dayue-founding')
event('chen_xu_groups_invade_chu','辰、溆地方武装侵楚',24,
 '辰、溆蛮侵楚，',[],when='921年本段；月日未载',place='辰、溆、楚',note='原书称蛮为古代作者用语，展示用地方武装；未据此强配现代民族或建未名首领。')
event('yao_yanzhang_suppresses_chen_xu','楚宁远节度副使姚彦章讨平辰、溆之侵',24,
 '楚宁远节度副使姚彦章讨平之。',[('姚彦章','奉讨平侵楚者')],when='921年本段；月日未载',place='辰、溆、楚')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19,25):
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
  review='921年末六段连续校核；吴郊祀纪月、韩正时死者归属保留书证差异；契丹南下、江陵修城、汉任相及楚地方战事分录。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=271,year=921,
 primary_source_key=main_sources[0],primary_source_keys=main_sources,
 paragraphs=[Q[n]['id'] for n in range(19,25)],next_paragraph='zztj-v271-y0922-p001',supplements=supplements,
 coverage='卷271龙德元年第19—24正文段，原文件61—66行；年末六段全覆盖，分隔符第67行不生成史事。',
 reviewed_questions=[
 {'paragraph_id':Q[19]['id'],'note':'吴主杨溥、徐知诰复用李昪；郊祀通鉴甲子置十月后十一月条前，新史明记十一月，月份并列待核；领江州不当迁镇。'},
 {'paragraph_id':Q[20]['id'],'note':'张处瑾是张处琪兄长。旧史补囚请降使者及双方土山；通鉴晋兵追斩韩正时，旧史追军败残众后彭赟斩之以降，归属与行唐衡唐地名保留差异。'},
 {'paragraph_id':Q[21]['id'],'note':'契丹主复用2026-10-02修订后person_阿保机，耶律阿保机旧重复主体不重新发布。王郁财色劝说及述律后预测是言论；十二月辛未指幽州攻击，涿州旬日后陷及定州援未附同日；李嗣弼被俘不当死亡。'},
 {'paragraph_id':Q[22]['id'],'note':'倪知进及高季昌女既婚背景不推成婚年；汝舅在妇嫁语境为公公，未建娘家舅父关系；白金保留原称。'},
 {'paragraph_id':Q[23]['id'],'note':'新史贞明三年倪曙工部平章是先前阶段，与主书本年尚书左丞平章并列；未改主书年条。'},
 {'paragraph_id':Q[24]['id'],'note':'地方武装用语与原书蛮称分开，未推现代民族或虚构首领。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
