"""Curate Tongjian 268, year 912, consecutive paragraphs 1-10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
main1 = 'tongjian-268-912-first'
main2 = 'tongjian-268-912-middle'
main3 = 'tongjian-268-912-next'
old_campaign = 'jiuwudaishi-028-912-campaign'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0912-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, P / 'sources/library' / main1, '425c28ca', '司马光等'),
    (main2, P / 'sources/library' / main2, '425c28ca', '司马光等'),
    (main3, P / 'sources/library' / main3, '425c28ca', '司马光等'),
    (old_campaign, P / 'sources/library' / old_campaign, '6276ece7', '薛居正等'),
]
source_dirs = {key: path for key, path, _, _ in specs}
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
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {key: (source_dirs[key] / 'source.txt').read_text() for key in (main1,main2,main3)}
for n in range(1, 11):
    row=Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line']-1]
    if n != 7:
        assert any(row['text'] in text for text in primary_texts.values()), n
    else:
        head = primary_texts[main1].splitlines()[-1]
        assert row['text'].startswith(head)
        assert primary_texts[main2].rstrip() == row['text'][len(head):]

registry = {}
existing_relation_keys = set()
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    archived = json.loads(path.read_text())
    existing_relation_keys.update(row['key'] for row in archived['person_relationships'])
    for row in archived['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (path, row['name'])
        registry[row['name']] = row
aliases = {'吴越王镠':'钱镠','楚王殷':'马殷','蜀主':'王建',
           '王景仁':'王茂章','张宗奭':'张全义','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,main2,main3) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,main2,main3):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化二年（912）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0912_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,main2,main3):
        book = json.loads((source_dirs[source] / 'paragraph.json').read_text())['book']
        supplements.append(dict(claim_key=ck, source_book=book, primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=supplement_relation))
    return ck

def person(name, n, role, quote):
    name = aliases.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷268乾化二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=912):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0912_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '912年本段条；确日未载', dynasty='五代十国',
               description=title + '。', phases=[], location_name=place,
               location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown',
               location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',
               status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote,
          note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', row['time_original'], n, quote,
          '段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_268_0912_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key,
                                       role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key

def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    if key in existing_relation_keys:
        reused.add(key)
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

event('three_commands_attack_yan', '周德威会赵、义武军攻燕，取祁沟关并围涿州', 1,
      '德威东出飞狐，与赵王将王德明、义武将程岩会于易水。丙戌，三镇兵进攻燕祁沟关，下之；戊子，围涿州。',
      [('周德威','率晋军出飞狐会盟并攻燕'),('王德明','代表赵王率军会师的张文礼'),('程岩','代表义武率军会师')],
      when='912年正月丙戌取祁沟关、戊子围涿州',place='易水、祁沟关、涿州',
      note='底本称王德明，沿既有人物张文礼（赵德明）归一；不因姓氏写法另立人物。')
event('liuzhiwen_surrenders', '刘守奇招降涿州刺史刘知温', 1,
      '刺史刘知温城守，刘守奇之客刘去非大呼于城下，谓知温曰：“河东小刘郎来为父讨贼，何豫汝事而坚守邪？”守奇免胄劳之，知温拜于城上，遂降。',
      [('刘知温','守涿州后向刘守奇投降'),('刘守奇','临城招降刘知温'),('刘去非','受刘守奇指使向城上喊话')],
      when='912年正月戊子后；确日未载',place='涿州',
      note='原文“为父讨贼”指刘守奇为父报仇，关系事实须核父名后再入关系库。')
event('liushouqi_to_liang', '周德威谮刘守奇，刘守奇与刘去非、赵凤奔梁', 1,
      '周德威疾守奇之功，谮诸晋王，王召之，守奇恐获罪，与去非及进士赵凤来奔，上以守奇为博州刺史。',
      [('周德威','向晋王谮刘守奇'),('刘守奇','因惧获罪与客人奔梁、获任博州刺史'),('刘去非','随刘守奇奔梁'),('赵凤','随刘守奇奔梁的进士'),('李存勖','召刘守奇的晋王'),('朱温','任刘守奇博州刺史的梁帝')],
      when='912年正月戊子后；确日未载',place='涿州、梁',
      note='“疾守奇之功”是史书所记动机；奔梁与任官分层，不认为晋王已经定罪。')
event('yan_embattled_and_liang_relief', '周德威至幽州，刘守光求救；朱温拟亲征镇、定', 1,
      '丁酉，德威至幽州城下，守光来求救。二月，帝疾小愈，议自将击镇、定以救之。',
      [('周德威','兵临幽州'),('刘守光','向梁求救的燕主'),('朱温','议亲征镇定救燕的梁帝')],
      when='912年正月丁酉至幽州；二月梁议亲征',place='幽州、镇州、定州',
      note='二月只有出征议定，实际行军见后段。')
event('liang_embassy_to_shu', '后梁遣卢玭使蜀，朱温致书称王建为兄', 2,
      '帝闻岐、蜀相攻，辛酉，遣光禄卿卢玭等使于蜀，遗蜀主书，呼之为兄。',
      [('朱温','遣使并致书蜀主的梁帝'),('卢玭','奉命出使前蜀的光禄卿'),('王建','受梁书信的蜀主')],
      when='912年二月辛酉',place='后梁、前蜀',
      note='“呼之为兄”是书信称谓，不据此建立血亲或结义关系。')
event('zhu_wen_kills_retinue', '朱温赴前线，因从官迟至扑杀孙骘、张衍、张俊', 3,
      '甲子，帝发洛阳。从官以帝诛戮无常，多惮行，帝闻之，益怒。是日，至白马顿，赐从官食，多未至，遣骑趣之于路。左散骑常侍孙骘、右谏议大夫张衍、后部郎中张俊最后至，帝命扑杀之。',
      [('朱温','下令扑杀三名迟到从官的梁帝'),('孙骘','被朱温下令扑杀的左散骑常侍'),('张衍','被朱温下令扑杀的右谏议大夫'),('张俊','被朱温下令扑杀的后部郎中')],
      when='912年二月甲子',place='洛阳、白马顿',
      note='“诛戮无常”为主书叙述；三人姓名官职逐一保留。')
event('li_sian_executed', '朱温因旧事贬逐并赐死李思安', 3,
      '丁卯，至获嘉，帝追思李思安去岁供馈有阙，贬柳州司户，告辞称明远之能曰：“观明远之忠勤如此，见思安之悖慢何如？”寻长流思安于崖州，赐死。明远后更名凝。',
      [('朱温','贬逐并赐死李思安的梁帝'),('李思安','被贬柳州、流崖州并赐死'),('段明远','供馈受朱温称许，后更名段凝')],
      when='912年二月丁卯及其后不久',place='获嘉、柳州、崖州',
      note='段凝即段明远，复用同一人物；“寻”不换算确日。')
event('liang_siege_orders', '朱温命杨师厚、李周彝围枣强，贺德伦、袁象先围蓚县', 3,
      '乙亥，帝至魏州，命都招讨使宣义节度使杨师厚，副使、前河阳节度使李周彝围枣强，招讨应接使、平卢节度使贺德伦，副使、天平留后袁象先围蓚脩县。',
      [('朱温','在魏州下令分兵攻城'),('杨师厚','率军围枣强的都招讨使'),('李周彝','围枣强的副使'),('贺德伦','围蓚县的招讨应接使'),('袁象先','围蓚县的副使')],
      when='912年二月乙亥',place='魏州、枣强、蓚县',
      note='蓚脩县保留底本写法，不自行断定现代地名。')
event('chenzhou_surrenders_chu', '宋鄴、昌师益率众降楚，马殷分别授辰州、溆州刺史', 4,
      '辰州蛮酋宋鄴、昌师益皆帅众降于楚，楚王殷以鄴为辰州刺史，师益为溆州刺史。',
      [('宋鄴','率众降楚并任辰州刺史的宋邺'),('昌师益','率众降楚并任溆州刺史'),('马殷','任命二人的楚王')],
      when='912年二月；确日未载',place='辰州、溆州、楚',
      note='宋鄴归入既有宋邺；“蛮酋”是原书称呼，不作本站身份标签。')
event('zhu_wen_panics_at_xiabo', '朱温至下博南，误闻晋兵大至而趋枣强', 5,
      '三月，辛巳，至下博南，登观津冢。赵将符习引数百骑巡逻，不知是帝，遽前逼之。或告曰：“晋兵大至矣！”帝弃行幄，亟引兵趣枣强，与杨师厚军合。',
      [('朱温','弃行幄并急趋枣强的梁帝'),('符习','率数百骑巡逻逼近梁帝的赵将'),('杨师厚','在枣强与朱温合兵')],
      when='912年三月辛巳',place='下博南、观津冢、枣强',
      note='符习不知所逼者是朱温；误报“大军”由不具名者喊出。')
event('zaoqiang_resists', '赵军坚守枣强，守卒诈降袭击李周彝', 6,
      '枣强城小而坚，赵人聚精兵数千守之。师厚急攻之，数日不下，城坏复修，死伤者以万数。城中矢石将竭，谋出降，有一卒奋曰：“贼自柏乡丧败已来，视我镇人裂眦，今往归之，如自投虎狼之口耳。因穷如此，何用身为！我请独往试之。”夜，缒城出，诣梁军诈降，李周彝召问城中之备，',
      [('杨师厚','急攻枣强的梁将'),('李周彝','询问赵军诈降守卒的梁将')],
      when='912年三月丙戌前数日',place='枣强',
      note='守卒未具姓名，不杜撰人名；死伤“以万数”为史书描述，未按军别细分。')
event('zaoqiang_massacre', '梁军丙戌拔枣强并屠城', 6,
      '帝闻之，愈怒，命师厚昼夜急攻，丙戌，拔之，无问老幼尽杀之，流血盈城。',
      [('朱温','下令昼夜攻枣强的梁帝'),('杨师厚','奉命攻下枣强的梁将')],
      when='912年三月丙戌',place='枣强',
      note='“无问老幼尽杀之”是主书原文，事件写屠城，不增估计死亡人数。')
claim('event','event_zztj_268_0912_zaoqiang_massacre','description',
      '《旧五代史》卷二十八也记梁攻下枣强并屠城，但系事日期与《通鉴》不同。',6,
      '三月壬午，梁祖自督軍攻棗強。甲申，城陷，屠之。',
      '旧书记甲申陷城，主书记丙戌；异日并列，不将二者强行换算为同一日。',old_campaign,'conflicts')
event('fucunshen_rejects_retreat', '符存审拒避土门，部署晋军救蓚县', 7,
      '晋忻州刺史李存审屯赵州，患兵少，裨将赵行实请入土门避之，存审不可。',
      [('李存审','拒绝退避土门的晋忻州刺史符存审'),('赵行实','建议避入土门的裨将')],
      when='912年三月；蓚县受攻前后',place='赵州、土门',
      note='李存审为符存审的养姓称名，复用既有人物。')
event('xiabo_bridge_ruse', '符存审扼下博桥，史建瑭等分道袭取梁军樵刍者', 7,
      '存审乃引兵扼下博桥，使建瑭、嗣肱分道擒生。建瑭分其麾下为五队，队各百人，一之衡水，一之南宫，一之信都，一之阜城，自将一队深入，与嗣肱遇梁军之樵刍者皆执之，获数百人。明日会于下博桥。皆杀之，留数人断臂纵去，曰：“为我语硃公：晋王大军至矣！”',
      [('李存审','布置下博桥佯动的符存审'),('史建瑭','分五队俘获梁军樵刍者'),('李嗣肱','参与分道擒生')],
      when='912年三月丁亥前；确日未载',place='下博桥、衡水、南宫、信都、阜城',
      note='此处明记杀数百樵刍者、断臂放归数人，录入不遮掩；“硃公”是原文字形，展示人物仍用朱温。')
event('xiuxian_night_raid', '史建瑭、李嗣肱冒梁军旗号夜袭贺德伦营', 7,
      '丁亥，始至县西，未及置营，建瑭、嗣肱各将三百骑，效梁军旗帜服色，与樵刍者杂行，日且暮，至德伦营门，杀门者，纵火大噪，弓矢乱发，左右驰突，既暝，各斩馘执俘而去。',
      [('史建瑭','率三百骑袭营'),('李嗣肱','率三百骑袭营'),('贺德伦','营垒遭夜袭的梁将')],
      when='912年三月丁亥',place='蓚县西、贺德伦营',
      note='每将三百骑，分别记录；片段在电子分段第二块内。')
event('zhu_wen_retreats_xiuxian', '朱温误认晋王大军至，烧营夜遁并病情加剧', 7,
      '帝大骇，烧营夜遁，迷失道，委曲行百五十里，戊子旦乃至冀州；蓚之耕者皆荷鉏奋梃逐之。委弃军资器械不可胜计。既而复遣骑觇之，曰：“晋军实未来，此乃史先锋游骑耳。”帝不胜惭愤，由是病增剧，不能乘肩舆。留贝州旬馀，诸军始集。',
      [('朱温','烧营退至冀州且病情加剧的梁帝')],
      when='912年三月丁亥夜至戊子晨',place='蓚县、冀州、贝州',
      note='主书明言晋王大军实未来；不把佯动写为晋王本人到场。')
claim('event','event_zztj_268_0912_xiuxian_night_raid','description',
      '《旧五代史》卷二十八亦记史建瑭等袭贺德伦营，兵数作每将百余骑。',7,
      '建瑭與李都督各領百餘騎，旗幟軍號類梁軍，與芻牧者雜行，暮及賀德倫營門，殺守門者，縱火大呼，俘斬而旋。',
      '旧书称“李都督”、每将百余骑；主书称李嗣肱、各三百骑，身份和兵数保留差异。',old_campaign,'conflicts')
event('zhang_wanjin_kills_liujiwei', '张万进因刘继威侵家杀之，自称义昌留后并向梁、晋求降', 8,
      '义昌节度使刘继威年少，淫虐类其父，淫于都指挥使张万进家，万进怒，杀之。诘旦，召大将周知裕，告其故。万进自称留后，以知裕为左都押牙。庚子，遣使奉表请降，亦遣使降于晋；晋王命周德威安抚之。',
      [('刘继威','被张万进所杀的义昌节度使'),('张万进','杀刘继威并自称留后、向梁晋两方求降'),('周知裕','获任左都押牙的沧州大将'),('李存勖','命周德威安抚张万进的晋王'),('周德威','奉晋王命安抚张万进')],
      when='912年三月庚子奏降；杀刘继威在此前',place='义昌军、沧州',
      note='旧五代史将张万进杀刘继威系于辛丑，主书系庚子前；原文异日并列。')
claim('event','event_zztj_268_0912_zhang_wanjin_kills_liujiwei','description',
      '《旧五代史》卷二十八记张万进辛丑杀刘继威并向梁、晋两方求降。',8,
      '辛丑，滄州都將張萬進殺留後劉繼威，自為滄帥，遣人送款於梁，亦乞降於帝。',
      '旧书系辛丑，主书庚子为遣使日期；杀人日期是否可据旧书直定，待校。',old_campaign,'adds')
event('zhou_zhiyu_to_liang', '周知裕不安而奔梁，朱温设归化军任其指挥使', 8,
      '知裕心不自安，求为景州刺史，遂来奔，帝为之置归化军，以知裕为指挥使，凡军士自河朔来者皆隶之。',
      [('周知裕','奔梁后任归化军指挥使'),('朱温','设归化军任周知裕的梁帝')],
      when='912年三月庚子后；确日未载',place='景州、后梁',
      note='周知裕先求景州刺史、后奔梁；求任不等于已经获任。')
event('zhang_wanjin_shunhua', '朱温任张万进义昌留后，改义昌为顺化并授节度使', 8,
      '辛丑，以万进为义昌留后。甲辰，改义昌为顺化军，以万进为节度使。',
      [('朱温','任命张万进并改义昌为顺化的梁帝'),('张万进','获任义昌留后、顺化节度使')],
      when='912年三月辛丑、甲辰',place='义昌军、顺化军',
      note='同人两次职任按时间先后展示；不另立顺化人物。')
event('zhu_wen_to_weizhou', '朱温离贝州至魏州', 9,
      '乙巳，帝发贝州；丁未，至魏州。',
      [('朱温','由贝州赴魏州的梁帝')],when='912年三月乙巳至丁未',place='贝州、魏州')
event('waqiao_pass_surrenders', '周德威遣李存晖攻瓦桥关，关吏及莫州刺史李严降', 10,
      '戊申，周德威遣裨将李存晖等攻瓦桥关，其将吏及莫州刺史李严皆降。',
      [('周德威','命部将攻瓦桥关'),('李存晖','率兵攻瓦桥关的晋裨将'),('李严','随关吏降晋的莫州刺史')],
      when='912年三月戊申',place='瓦桥关、莫州',
      note='“将吏”未具姓名；旧书称攻下瓦桥关，并不推为屠城。')
claim('event','event_zztj_268_0912_waqiao_pass_surrenders','description',
      '《旧五代史》卷二十八也记周德威遣李存晖攻下瓦桥关。',10,
      '戊申，周德威遣李存暉攻瓦橋關，下之。',
      '旧书“存暉”为传统字形，归一为李存晖；旧书只记关下，不补主书所列李严身份。',old_campaign,'corroborates')
event('meng_zhixiang_saves_liyan', '李严固辞晋王任命，孟知祥赤足谏止处斩', 10,
      '晋王使传其子继岌，严固辞。王怒，将斩之，教练使孟知祥徒跣入谏曰：“强敌未灭，大王岂宜以一怒戮向义之士乎！”乃免之。',
      [('李存勖','欲因李严拒任而斩之的晋王'),('李严','拒绝教导李继岌的降将'),('孟知祥','赤足进谏使李严免死的教练使'),('李继岌','晋王命李严教导的儿子')],
      when='912年三月戊申后；确日未载',place='晋王军中',
      note='“乃免之”明确李严未被斩；孟知祥此时官为教练使。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化二年开篇第1—10段连续处理；繁简及异名归一、原文原字保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=912,
    primary_source_key=main1,primary_source_keys=[main1,main2,main3],
    paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v268-y0912-p011',
    coverage='卷268乾化二年正月至三月第1—10段，晋攻燕、梁攻枣强与蓚县、义昌军易主。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[1]['id'],'note':'王德明与已录赵德明/张文礼核为同一赵王将领；旧五代史卷54、56同见王德明，保留原称。'},
      {'paragraph_id':Q[3]['id'],'note':'段明远后更名凝，归入已录段明远，原文不改。'},
      {'paragraph_id':Q[6]['id'],'note':'旧五代史卷28甲申陷枣强；通鉴丙戌，日期异说并列。'},
      {'paragraph_id':Q[7]['id'],'note':'电子分段跨两块；旧史作李都督、百余骑，通鉴作李嗣肱、三百骑；待纸本核。'},
      {'paragraph_id':Q[8]['id'],'note':'旧史系辛丑杀刘继威，通鉴庚子为遣使日期，未强并。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
