"""Curate consecutive Tongjian volume 271, year 920, paragraphs 19–21."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 27))
specs = [
    ('tongjian-271-920-winter', YEAR / 'part-04/sources/library/tongjian-271-920-winter', '9edfda98', '司马光等'),
    ('jiuwudaishi-054-wang-rong-conflict', P / 'sources/library/jiuwudaishi-054-wang-rong-conflict', '2f1e57ed', '薛居正等'),
    ('jiuwudaishi-062-zhang-wenli-adoption', P / 'sources/library/jiuwudaishi-062-zhang-wenli-adoption', '2f1e57ed', '薛居正等'),
    ('jiuwudaishi-062-zhang-wenli-command', P / 'sources/library/jiuwudaishi-062-zhang-wenli-command', 'a545c342', '薛居正等'),
    ('xinwudaishi-039-zhang-wenli-name', ROOT / 'content/revisions/2026-10-03-zhang-wenli-wang-deming/sources/library/xinwudaishi-039-zhang-wenli-name', '0f528112', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0920-p019-p021',
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
for n in range(19, 22):
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
people, used, reused, supplements = {}, {}, set(), []

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
        citation = f'卷271·贞明六年（920）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0920_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','蜀主':'王宗衍','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
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
                   aliases={'李蔼':['李霭','李藹','李靄'],'李弘规':['李宏规','李弘規','李宏規'],'陈彦威':['陳彥威'],'苏汉衡':['蘇漢衡']}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271贞明六年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='920年本段条；确日未载', note='', year=920, place='五代十国'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0920_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_271_0920_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('wang_zongchou_and_three_deputies_appointed','蜀命王宗俦统西北招讨、王宗昱等三将为副',19,
      '十一月，戊子朔，蜀主以兼侍中王宗俦为山南节度使、西北面都招讨、行营安抚使，天雄节度使、同平章事王宗昱、永宁军使王宗晏、左神勇军使王宗信为三招讨以副之，',
      [('王宗俦','受任山南节度使、西北面都招讨、行营安抚使者'),('王宗昱','为副的天雄节度使'),
       ('王宗晏','为副的永宁军使'),('王宗信','为副的左神勇军使')],
      when='920年十一月戊子朔',place='山南、蜀',note='主书明确一主三副；同授职不推彼此亲属关系。')
event('shu_army_invades_qi_via_guguan','蜀军伐岐，出故关、屯咸宜、入良原',19,
      '将兵伐岐，出故关，壁于咸宜，入良原。',
      [('王宗俦','承上文统军伐岐者')],when='920年十一月戊子朔授将后本段',place='故关、咸宜、良原',
      note='“壁于”是驻垒；入良原未说明全域控制。')
event('wang_zongchou_attacks_longzhou_qi_defends','王宗俦攻陇州，岐王率军屯汧阳',19,
      '丁酉，王宗俦攻陇州，岐王自将万五千人屯汧阳。',
      [('王宗俦','攻陇州的蜀将'),('岐王','率一万五千人屯汧阳的李茂贞')],
      when='920年十一月丁酉',place='陇州、汧阳',note='攻陇州未说明已经攻克；兵数据主书。')
event('chen_yanwei_defeats_qi_jiankualing','陈彦威出散关，在箭筈岭败岐军',19,
      '癸卯，蜀将陈彦威出散关，败岐兵于箭筈岭，',
      [('陈彦威','出散关、败岐兵的蜀将')],when='920年十一月癸卯',place='散关、箭筈岭')
event('shu_army_returns_for_lack_of_food','蜀军粮尽而还',19,
      '蜀兵食尽，引还。',[],when='920年十一月癸卯战后本段',place='蜀岐战场',
      note='只记粮尽及撤回；不把一次击败岐兵写成完整征服岐国。')
event('shu_generals_garrison_qin_shanggui_weiwu','蜀将分屯秦州、上邽及威武城',19,
      '宗昱屯秦州，宗俦屯上邽，宗晏、宗信屯威武城。',
      [('王宗昱','屯秦州者'),('王宗俦','屯上邽者'),('王宗晏','屯威武城者'),('王宗信','屯威武城者')],
      when='920年十一月撤军后本段',place='秦州、上邽、威武城')
event('shu_king_departs_anyuan','蜀主发安远城',19,
      '庚戌，蜀主发安远城。',[('蜀主','从安远城启行者')],when='920年十一月庚戌',place='安远城')
event('shu_king_reaches_lizhou_lin_sie_invites','蜀主至利州，允林思谔请幸阆州',19,
      '十二月，庚申，至利州，阆州团练使林思谔来朝，请幸所治，从之。',
      [('蜀主','至利州并允林思谔请幸其治所者'),('林思谔','来朝请幸阆州的团练使')],
      when='920年十二月庚申',place='利州、阆州',note='主语承蜀主；“从之”是准请，实际到阆州在后面壬申。')
event('shu_king_sails_downriver_local_supply','蜀主泛江而下，州县供办',19,
      '癸亥，泛江而下，龙舟画舸，辉映江渚，州县供办，民始愁怨。',
      [('蜀主','泛江南下并由州县供办者')],when='920年十二月癸亥',place='利州至阆州江路',
      note='民愁怨为史书叙述；未计算供办费用或沿江各州具体负担。')
event('shu_king_takes_he_kang_daughter','蜀主至阆州，取将嫁的何康女，其夫悲恸而卒',19,
      '壬申，至阆州，州民何康女色美，将嫁，蜀主取之，赐其夫家帛百匹，夫一恸而卒。',
      [('蜀主','取何康女并赐其夫家帛者'),('何康女','将嫁而被蜀主取走的阆州女子')],
      when='920年十二月壬申',place='阆州',
      note='何康女姓名未载；“将嫁”与“夫”并见，未据此另建已成婚的丈夫关系。夫之死仅按主书叙述。')
father=person('何康',19,'本段女子之父、阆州州民','州民何康女色美，将嫁，')
daughter=person('何康女',19,'何康之女','州民何康女色美，将嫁，')
rk='relationship_zztj_271_0920_he_kang_father_of_daughter'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=daughter,
    relation_type='父亲',description='何康是何康女的父亲。',status='draft'))
claim('person_relationship',rk,'description','何康是何康女的父亲。',19,
      '州民何康女色美，将嫁，','“何康女”明示父女；女以父名消歧，未杜撰个人姓名。')
event('shu_king_reaches_zizhou','蜀主至梓州',19,
      '癸未，至梓州。',[('蜀主','至梓州者')],when='920年十二月癸未',place='梓州',note='主语承本段蜀主巡行。')

event('wang_rong_delegates_government_to_favorites','王镕嬉游、政事仰成僚佐，李蔼等用事',20,
      '赵王镕自恃累世镇成德，得赵人心，生长富贵，雍容自逸，治府第园沼，极一时之盛，多事嬉游，不亲政事，事皆仰成于僚佐，深居府第，权移左右，行军司马李蔼、宦者李弘规用事于中外，宦者石希蒙尤以谄谀得幸。',
      [('赵王镕','委政于僚佐的成德赵王'),('李蔼','用事于中外的行军司马'),
       ('李弘规','用事于中外的宦者'),('石希蒙','得王镕宠幸的宦者')],
      when='王镕晚年政事背景；起始年未载',year=None,place='成德',
      note='本段为多年政事背景与史书评价，未强定这些动作始于920。李蔼、下段李霭为同场同职用字异文。')

event('zhang_wenli_sent_with_liu_shouwen','刘仁恭命张文礼随刘守文镇沧州',21,
      '初，刘仁恭使牙将张文礼从其子守文镇沧州，',
      [('刘仁恭','遣牙将张文礼随子镇沧州者'),('张文礼','随刘守文镇沧州的牙将'),('守文','镇沧州的刘仁恭之子')],
      when='追叙刘仁恭主幽州时期；确年未载',year=None,place='沧州',note='“初”追叙，未定920年。')
event('zhang_wenli_rebels_cangzhou_flees_zhenzhou','张文礼乘刘守文省父据城作乱，败后奔镇州',21,
      '守文诣幽州省其父，文礼于后据城作乱，沧人讨之，奔镇州。',
      [('刘守文','赴幽州省父期间城中生乱的沧州主将'),('张文礼','据城作乱后遭讨、奔镇州者')],
      when='追叙刘守文镇沧州时期；确年未载',year=None,place='幽州、沧州、镇州')
event('wang_rong_adopts_zhang_wenli_names_deming','王镕收张文礼为养子，更名德明并委军务',21,
      '文礼好夸诞，自言知兵，越王镕奇之，养以为子，更名德明，悉以军事委之。',
      [('张文礼','为王镕养子、更名德明并获委军事者'),('王镕','收养张文礼并委军事者')],
      when='张文礼奔镇州后追叙；确年未载',year=None,place='镇州',
      note='本段“越王镕”与前段“赵王镕”称号异字保留，按同一王镕；更名德明与下文王德明沿已核同人。')
rk='relationship_person_王镕_person_张文礼_养父'
relation=json.loads((ROOT/'content/books/zizhi-tongjian/vol-267/year-0911/part-01/content-batch.json').read_text())
r=next(r for r in relation['person_relationships'] if r['key']==rk)
B['person_relationships'].append(dict(r,status='draft'));reused.add(rk)
claim('person_relationship',rk,'description','王镕是张文礼的养父。',21,
      '养以为子，更名德明，','复用已发布养父关系的原key和UUID，不新建同端点关系。')
claim('person','person_张文礼','aliases','张文礼受王镕收养后号王德明。',21,
      '張文禮者，狡獪人也，鎔惑愛之，以為子，號王德明。',
      '《新五代史》明确全名王德明，配合卷72韩延徽寄住记录已修正916年重复主体；原档案保留。',
      'xinwudaishi-039-zhang-wenli-name','corroborates')
claim('event','event_zztj_271_0920_wang_rong_adopts_zhang_wenli_names_deming','description',
      '《旧五代史》张文礼传亦记其为王镕义男、赐姓更名德明。',21,
      '鎔賞其言，給遺甚厚，因錄為義男，賜姓，名德明，由是每令將兵。',
      '义男与主书养子对应；本句未记收养确年。',
      'jiuwudaishi-062-zhang-wenli-adoption','corroborates')
event('fu_xi_replaces_zhang_wenli_field_command','王镕以符习代张文礼行营，召张文礼为防城使',21,
      '德明将行营兵从晋王，镕欲寄以腹心，使都指挥使符习代还，以为防城使。',
      [('张文礼','由从晋行营召还任防城使者'),('符习','替代张文礼领行营兵者'),('王镕','调整行营与防城人选者')],
      when='王镕晚年追叙；确年未载',year=None,place='晋行营、镇州',
      note='主书代还的省略主语以旧书明确“符习代其行营，以文礼为防城使”校核，未把符习写为防城使。')
claim('event','event_zztj_271_0920_fu_xi_replaces_zhang_wenli_field_command','description',
      '《旧五代史》明确以符习代张文礼行营、以张文礼为防城使。',21,
      '乃以符習代其行營，以文禮為防城使，',
      '补书明确两项职务的对象，帮助校核主书省略主语。',
      'jiuwudaishi-062-zhang-wenli-command','adds')
event('wang_rong_western_mountain_religious_tours','王镕晚年事佛求仙，往游西山',21,
      '镕晚年好事佛及求仙，专讲佛经，受符箓，广斋醮，合炼仙丹，盛饰馆宇于西山，每往游之，登山临水，数月方归，将佐士卒陪从者常不下万人，往来供顿，军民皆苦之。',
      [('王镕','晚年讲经求仙、游西山且众从者')],
      when='王镕晚年持续背景；起始年未载',year=None,place='西山',
      note='史书概述多次游行，未拆成各次虚构日期；万人为原文量级。')
event('wang_rong_returns_from_west_mountain_to_huying','王镕由西山还、宿鹘营庄，石希蒙劝他继续游',21,
      '是月，自西山还，宿鹘营庄，石希蒙劝王复之它所。',
      [('王镕','自西山还宿鹘营庄者'),('石希蒙','劝王镕转游它所者')],
      when='920年十二月（主书是月承上）；确日未载',place='西山、鹘营庄',
      note='主书记本年十二月；旧书王镕传起此事作“天祐八年冬十二月”，纪年疑讹单独保留。')
claim('event','event_zztj_271_0920_wang_rong_returns_from_west_mountain_to_huying','time_original',
      '《旧五代史》王镕传本段起事纪年作天祐八年冬十二月。',21,
      '天祐八年冬十二月，鎔自西山回，宿於鶻營莊，將歸府第，希蒙勸之佗所。',
      '与主书920年十二月及随后王镕被杀的次年记录存在纪年差异，疑漏“十”或记事错置，纸本未核，不自行改字。',
      'jiuwudaishi-054-wang-rong-conflict','conflicts')
event('li_honggui_urges_return_shi_ximeng_slanders','李弘规劝王镕归府，石希蒙反谮使其留宿',21,
      '李弘规言于王曰：“晋王夹河血战，栉风沐雨，亲冒矢石，而王专以供军之资奉不急之费，且时方艰难，人心难测，王久虚府第，远出游从，万一有奸人为变，闭关相距，将若之何？”王将归，希蒙密言于王曰：“弘规妄生猜间，出不逊语以劫胁王，专欲夸大于外，长威福耳。”王遂留，信宿无归志。',
      [('李弘规','劝王镕归府防变的宦者'),('石希蒙','反谮李弘规以阻归府者'),('王镕','初将归后听石希蒙言而留宿者')],
      when='920年十二月鹘营庄事；确日未载',place='鹘营庄',
      note='石希蒙指控李弘规劫胁为当事人言辞，不当作已证案情；信宿保留相对时间。')
event('su_hanheng_armed_petition_li_honggui_accuses_shi','苏汉衡率亲军请王镕归，李弘规请诛石希蒙',21,
      '弘规乃教内牙都将苏汉衡帅亲军，擐甲拔刃，诣帐前白王曰：“士卒暴露已久，愿从王归！”弘规因进言曰：“石希蒙劝王游从不已，且闻欲阴谋为逆，请诛之以谢众。”王不听，',
      [('李弘规','命苏汉衡率亲军请归并请诛石希蒙者'),('苏汉衡','率披甲持刃亲军请归的内牙都将'),
       ('王镕','不听诛石希蒙之请者'),('石希蒙','被李弘规指控阴谋为逆者')],
      when='920年十二月鹘营庄事；确日未载',place='王镕行帐',
      note='“且闻欲阴谋”为指控，未证石希蒙已有谋反；王不听仍与随后牙兵擅杀分开。')
event('guards_kill_shi_ximeng_wang_rong_returns','牙兵杀石希蒙，王镕惧而归府',21,
      '牙兵遂大噪，斩希蒙首，诉于前。王怒且惧，亟归府。',
      [('石希蒙','被牙兵斩首者'),('王镕','怒惧而急归府者')],
      when='920年十二月鹘营庄事当日；确日未载',place='王镕行帐、镇州府第',
      note='主书牙兵斩首未点名执刀者，不推苏汉衡亲手斩首。')
event('wang_rong_orders_li_honggui_li_ai_families_killed','王镕命王昭祚、张文礼围李弘规及李蔼宅并族诛',21,
      '是夕，遣其长子副大使昭祚与王德明将兵围弘规及李霭之第，族诛之，连坐者数十家。',
      [('王镕','当晚下令围宅族诛者'),('王昭祚','奉父命围宅的长子副大使'),('王德明','同王昭祚领军围宅的张文礼'),
       ('李弘规','被围宅族诛者'),('李霭','被围宅族诛的行军司马李蔼')],
      when='920年十二月杀石希蒙归府之夕；确日未载',place='镇州李弘规、李蔼宅',
      note='李霭与上段李蔼同人，由旧书李藹同职同事补证；数十家保留原文量级，未补名单。')
claim('event','event_zztj_271_0920_wang_rong_orders_li_honggui_li_ai_families_killed','description',
      '《旧五代史》同记王昭祚、张文礼围李宏规及行军司马李藹宅并族诛。',21,
      '是日，令其子昭祚與張文禮以兵圍李宏規及行軍司馬李藹宅，並族誅之，詿誤者凡數十家。',
      '补书宦者名作李宏规、主书作李弘规；同职同事对应同人，原名写法与纪年差异分开保存。',
      'jiuwudaishi-054-wang-rong-conflict','corroborates')
rk='relationship_person_王镕_person_王昭祚_父亲'
relation=json.loads((ROOT/'content/books/zizhi-tongjian/vol-262/year-0900/part-03/content-batch.json').read_text())
r=next(r for r in relation['person_relationships'] if r['key']==rk)
B['person_relationships'].append(dict(r,status='draft'));reused.add(rk)
claim('person_relationship',rk,'description','王镕是王昭祚的父亲，王昭祚为其长子。',21,
      '是夕，遣其长子副大使昭祚与王德明将兵围弘规及李霭之第，',
      '复用原父亲关系key和UUID；本段进一步明示长子。')
event('wang_rong_kills_su_hanheng_investigates_guards','王镕杀苏汉衡并收治其党，亲军大恐',21,
      '又杀苏汉衡，收其党与，穷治反状，亲军大恐。',
      [('王镕','杀苏汉衡并收治党与者'),('苏汉衡','被王镕杀的内牙都将')],
      when='920年十二月族诛李弘规等后；确日未载',place='镇州',
      note='“穷治反状”是追查动作，未由此确认被治诸人均实际谋反。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19, 22):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明六年第19—21段；蜀伐岐巡行、赵王政事与亲军冲突，异名与追叙分录。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=920,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(19, 22)], next_paragraph=Q[22]['id'],
    coverage='卷271贞明六年第19—21段；蜀伐岐与巡行、王镕委政、张文礼养子及赵亲军冲突。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[19]['id'],'note':'蜀授将、伐岐、缺粮还屯及主巡行分阶段；何康女姓名未载，将嫁与夫并见，不臆造完成婚姻关系。'},
      {'paragraph_id':Q[20]['id'],'note':'晚年政事背景起始年不明；主书李蔼／下段李霭与补书李藹同职同事按同人处理。'},
      {'paragraph_id':Q[21]['id'],'note':'越王镕／赵王镕字样原样保留；张文礼／王德明经通鉴与新五代史直接名号、韩延徽寄住证据合并，见2026-10-03-zhang-wenli-wang-deming勘误。养父及王昭祚父亲关系复用旧UUID。'},
      {'paragraph_id':Q[21]['id'],'note':'符习代行营、张文礼任防城使以旧书明文校核；旧书李宏规对应主书李弘规，天祐八年冬十二月与主書920年纪年有疑讹，未改底本。互相谋反指控均保留为当事人言辞。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
