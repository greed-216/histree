"""Curate Tongjian 269, year 914, consecutive paragraphs 11-16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 17))
main1 = 'tongjian-269-914-spring'
main2 = 'tongjian-269-914-year-end'
old_jin = 'jiuwudaishi-028-jin-autumn'
old_yanlu = 'jiuwudaishi-008-yang-yanlu'
old_date = 'jiuwudaishi-013-yang-date'
new_yanlu = 'xinwudaishi-040-yang-yanlu'
new_shu = 'xinwudaishi-063-gao-jichang'
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0914-p011-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, P.parent / 'part-01/sources/library' / main1, '98ce861b', '司马光等'),
    (main2, P / 'sources/library' / main2, 'cc69bae0', '司马光等'),
    (old_jin, P / 'sources/library' / old_jin, 'cc69bae0', '薛居正等'),
    (old_yanlu, P / 'sources/library' / old_yanlu, 'cc69bae0', '薛居正等'),
    (old_date, P / 'sources/library' / old_date, 'cc69bae0', '薛居正等'),
    (new_yanlu, P / 'sources/library' / new_yanlu, 'cc69bae0', '欧阳修'),
    (new_shu, P.parent / 'part-01/sources/library' / new_shu, '98ce861b', '欧阳修'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main1,main2)}
for n in range(11,17):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line']-1]
    assert any(row['text'] in text for text in primary_texts.values()),n

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
           '王景仁':'王茂章','张宗奭':'张全义','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
aliases.update({'元膺':'王宗懿','蜀主':'王建','帝':'朱友贞','硃友谦':'朱友谦',
                '鄴王':'杨师厚','晋王':'李存勖','守光':'刘守光',
                '行珪':'高行珪','行周':'高行周','嗣源':'李嗣源',
                '存矩':'李存矩','传瓘':'钱传瓘','传璙':'钱传璙',
                '吴越王镠':'钱镠','从珂':'李从珂','魏氏':'魏氏（李从珂母）'})
aliases.update({'刘光浚':'刘光濬','光浚':'刘光濬','李存审':'符存审',
                '王德明':'张文礼','赵王':'王镕','传瓘':'钱传瓘',
                '师厚':'杨师厚','守奇':'刘守奇','万进':'张万进'})
aliases.update({'元膺':'王宗懿','太子':'王宗懿','蜀主':'王建',
                '道袭':'唐道袭','宗翰':'王宗翰','宗侃':'王宗侃',
                '宗贺':'王宗贺','宗黯':'王宗黯','赵王镕':'王镕',
                '晋王':'李存勖','高季兴':'高季昌'})
aliases.update({'吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘',
                '传璙':'钱传璙','传瑛':'钱传瑛','蜀主':'王建',
                '宗衍':'王宗衍','宗辂':'王宗辂','宗杰':'王宗杰',
                '宗侃':'王宗侃','晋王':'李存勖','守光':'刘守光',
                '朱温':'朱温','王景仁':'王茂章'})
aliases.update({'硃瑾':'朱瑾','硃景浮':'朱景浮','王景仁':'王茂章',
                '景仁':'王茂章','守光':'刘守光','晋王':'李存勖',
                '越王镕':'王镕','赵王镕':'王镕','仁恭':'刘仁恭'})
aliases.update({'镕':'王镕','晋王':'李存勖','守光':'刘守光',
                '仁恭':'刘仁恭','小喜':'李小喜','蜀主':'王建',
                '太子':'王宗衍','宗寿':'王宗寿','季昌':'高季昌',
                '成先':'王成先','张武':'张武'})
aliases.update({'康怀英':'康怀贞','怀英':'康怀贞','怀贞':'康怀贞',
                '帝':'朱友贞','蜀主':'王建','马鄴':'马邺',
                '崇景':'刘崇景','威':'刘威','洙':'韩洙'})
aliases.update({'晋王':'李存勖','赵王镕':'王镕','蜀主':'王建',
                '宗寿':'王宗寿','宗范':'王宗范','宗播':'许存',
                '王宗播':'许存','王宗鐸':'王宗铎','宗鐸':'王宗铎',
                '宗俨':'王宗俨','硃瑾':'朱瑾','友璋':'朱友璋',
                '存节':'牛存节','彦鲁':'彦鲁（杨崇本子）',
                '李继徽':'杨崇本','杨崇本':'杨崇本'})
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·乾化四年（914）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_269_0914_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,main2):
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
                   description=f'《资治通鉴》卷269乾化四年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=914):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0914_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '914年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_269_0914_' + code + '_' + pk
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

event('jin_zhao_meet_xingzhou', '晋王会王镕、周德威，李嗣昭合兵南向邢州', 11,
      '晋王既克幽州，乃谋入寇。秋，七月，会赵王镕及周德威于赵州，南寇邢州，李嗣昭引昭义兵会之。',
      [('李存勖','会赵王与周德威并率晋军南向邢州'),('王镕','在赵州与晋王会军的赵王'),('周德威','与晋王会于赵州的晋将'),('李嗣昭','率昭义兵会晋王军')],
      when='914年七月',place='赵州、邢州',
      note='“乃谋入寇”是晋王计划；本段随后明记南向邢州，尚未记邢州被攻下。')
event('yang_shihou_xingzhou_relief', '杨师厚率梁军救邢州，曹进金投梁后晋军退', 11,
      '杨师厚引兵救邢州，军于漳水之东。晋军至张公桥，裨将曹进金来奔。晋军退，诸镇兵皆引归。八月，晋王还晋阳。',
      [('杨师厚','率梁军驻漳水东救邢州'),('曹进金','自晋军投梁的裨将'),('李存勖','晋军撤后于八月还晋阳')],
      when='914年七月至八月',place='漳水之东、张公桥、晋阳',
      note='“来奔”承梁方叙事指曹进金归梁；原文只记晋军退，未明确一次会战败绩。')
claim('event','event_zztj_269_0914_yang_shihou_xingzhou_relief','description',
      '《旧五代史》卷二十八亦记曹进金奔梁、晋军不利而退。',11,
      '梁將楊師厚軍於漳東，帝軍次張公橋，既而裨將曹進金奔於梁，帝軍不利而退。八月，還晉陽。',
      '旧书概括“军不利”，主书只记投奔与退兵；两书不用于推定未写出的具体战斗。',old_jin,'adds')
event('wang_zongxun_killed', '王宗训擅归成都并多所邀求，王建命卫士殴杀', 12,
      '蜀武泰节度使王宗训镇黔州，贪暴不法，擅还成都。庚辰，见蜀主，多所邀求，言辞狂悖。蜀主怒，命卫士殴杀之。',
      [('王宗训','自黔州擅归成都并被卫士殴杀的武泰节度使'),('王建','命卫士殴杀王宗训的前蜀皇帝')],
      when='914年八月庚辰',place='黔州、成都',
      note='“贪暴不法”“狂悖”是主书评价和王建处置语境；只将擅归、觐见、殴杀作为具体行动。')
claim('event','event_zztj_269_0914_wang_zongxun_killed','description',
      '《新五代史》卷六十三概记八月王建杀黔南节度使王宗训。',12,
      '八月，殺黔南節度使王宗訓。',
      '新书作黔南节度使，主书作武泰节度使镇黔州；官号用法保留。',new_shu,'adds')
event('pan_qiao_wutai_mao_miji', '王建以潘峭镇武泰，毛文锡判枢密院', 12,
      '戊子，以内枢密使潘峭为武泰节度使、同平章事，翰林学士承旨毛文锡为礼部尚书，判枢密院。',
      [('潘峭','由内枢密使任武泰节度使、同平章事'),('毛文锡','由翰林学士承旨任礼部尚书、判枢密院'),('王建','作出任命的前蜀皇帝')],
      when='914年八月戊子',place='前蜀')
event('mao_wenxi_blocks_flood_plan', '毛文锡反对决堰灌江陵，王建停止计划', 12,
      '峡上有堰，或劝蜀主乘夏秋江涨，决之以灌江陵。毛文锡谏曰：“高季昌不服，其民何罪！陛下方以德怀天下，忍以邻国之民为鱼鳖食乎！”蜀主乃止。',
      [('毛文锡','以江陵民众受害为由反对决堰的蜀臣'),('王建','听谏后不实行决堰计划的蜀主'),('高季昌','毛文锡进谏中所称不服的荆南主将')],
      when='914年八月戊子后；确日未载',place='峡上、江陵',
      note='原文“或劝”未具名；这是未实施的水攻提议，不能录为江陵发生水灾。')
event('zhu_youzhen_appoints_youzhang', '朱友贞任福王朱友璋为武宁节度使', 13,
      '帝以福王友璋为武宁节度使。',
      [('朱友贞','任命福王朱友璋的梁帝'),('朱友璋','受任武宁节度使的福王')],
      when='914年八月后、九月前；确日未载',place='武宁')
event('wang_yin_defects_wu', '王殷不受朱友璋接替，叛梁附吴', 13,
      '前节度使王殷，友珪所置也，惧，不受代，叛附于吴。',
      [('王殷','不受代并叛梁附吴的前武宁节度使')],
      when='914年九月前；确日未载',place='徐州、武宁',
      note='原文“惧”是对王殷心理的叙述，未推定其他动机；“友珪所置”指朱友珪此前任命。')
event('liang_reconquers_wuning', '梁遣牛存节、刘鄩讨王殷，十月军宿州', 13,
      '九月，命淮南西北面招讨应接使牛存节及开封尹刘鄩将兵讨之。冬，十月，存节等军于宿州。',
      [('朱友贞','命牛存节、刘鄩出兵的梁帝'),('牛存节','奉命讨王殷并军宿州'),('刘鄩','与牛存节同出兵讨王殷')],
      when='914年九月命将、十月军宿州',place='宿州、徐州',
      note='“讨之”指讨王殷，此时未记徐州已被梁夺回。')
event('zhu_jin_xuzhou_relief', '朱瑾率吴军救徐州，被牛存节等击退', 13,
      '吴平卢节度使硃瑾等将兵救徐州，存节等逆击，破之，吴兵引归。',
      [('朱瑾','率吴军救徐州的平卢节度使'),('牛存节','与梁军迎击并击退吴军')],
      when='914年十月；确日未载',place='徐州',
      note='“等”代表未具名同行者；本段只记救援吴兵退，未记王殷结局。')
event('nanzhao_invades_lizhou', '南诏军攻黎州，王建命王宗范、许存、王宗寿为三招讨迎击', 14,
      '十一月，乙巳，南诏寇黎州，蜀主以夔王宗范、兼中书令宗播、嘉王宗寿为三招讨以击之。',
      [('王建','命三招讨反击南诏军的前蜀皇帝'),('王宗范','受命为三招讨之一的夔王'),('许存','以王宗播之名受命为三招讨之一'),('王宗寿','受命为三招讨之一的嘉王')],
      when='914年十一月乙巳',place='黎州',
      note='原文“宗播”沿既有许存主体；“三招讨”为三名任命者，不推定三路行军细节。')
event('nanzhao_pancangzhang', '前蜀军丙辰败南诏军于潘仓嶂，赵嵯政等被斩', 14,
      '丙辰，败之于潘仓嶂，斩其酋长赵嵯政等。',
      [('王宗范','此前受命为三招讨之一；此战个人行动未详'),('许存','以王宗播之名受命为三招讨之一；此战个人行动未详'),('王宗寿','此前受命为三招讨之一；此战个人行动未详'),('赵嵯政','在潘仓嶂之战被斩的南诏酋长')],
      when='914年十一月丙辰',place='潘仓嶂',
      note='“等”未具名者不另建；主书未给参与各将个人战功。')
event('nanzhao_shankoucheng', '前蜀军壬戌再败南诏军于山口城', 14,
      '壬戌，又败之于山口城。',
      [('王宗范','三招讨之一'),('许存','以王宗播之名为三招讨之一'),('王宗寿','三招讨之一')],
      when='914年十一月壬戌',place='山口城',
      note='只记“又败之”，未给具体斩获。')
event('nanzhao_wuhouling', '前蜀军十二月破武侯岭十三寨', 14,
      '十二月，乙亥，破其武侯岭十三寨。',
      [('王宗范','三招讨之一'),('许存','以王宗播之名为三招讨之一'),('王宗寿','三招讨之一')],
      when='914年十二月乙亥',place='武侯岭',
      note='“十三寨”为史书记数，不折算兵力或人口。')
event('nanzhao_daduhu', '前蜀军辛巳败南诏军于大度河，桥绝多人溺死', 14,
      '辛巳，又败之于大度河，浮斩数万级，蛮争走度水，桥绝，溺死者数万人。',
      [('王宗范','三招讨之一'),('许存','以王宗播之名为三招讨之一'),('王宗寿','三招讨之一')],
      when='914年十二月辛巳',place='大度河',
      note='“浮斩数万级”“溺死数万人”均为主书数量记载，未交叉核验且可能涉及不同计数口径；不合计成总死亡数。')
claim('event','event_zztj_269_0914_nanzhao_daduhu','description',
      '《新五代史》卷六十三概记王建遣王宗范在大渡河击败南蛮。',14,
      '冬，南蠻攻掠界上，建遣夔王宗範擊敗之于大渡河。',
      '新书作大渡河，主书作大度河，水名字形与战事地点待核；新书不提供主书的伤亡数字。',new_shu,'corroborates')
event('wang_jian_recalls_zongfan', '王建召回拟筑浮桥渡大度河继续进攻的王宗范等', 14,
      '宗范等将作浮梁济大渡河攻之，蜀主召之令还。',
      [('王宗范','拟筑浮桥继续进军而被召还的三招讨'),('王建','下令召回远征军的蜀主')],
      when='914年十二月辛巳后；确日未载',place='大渡河',
      note='拟作浮梁而未记实际架成，也未记继续深入南诏。')
event('wang_zongduo_jiezhou', '王宗铎攻岐阶州及固镇，破十一寨', 15,
      '癸未，蜀兴州刺史兼北路制置指挥使王宗鐸攻岐阶州及固镇，破细砂等十一寨，斩首四千级。',
      [('王宗铎','以底本王宗鐸字形率蜀军攻阶州固镇的兴州刺史')],
      when='914年十二月癸未',place='阶州、固镇、细砂',
      note='繁体“鐸”规范作“铎”，未因此另建人物；四千级为主书斩首数，待其他书证。')
event('wang_zongyan_changchengguan', '王宗俨攻岐长城关等四寨', 15,
      '甲申，指挥使王宗俨破岐长城关等四寨，斩首二千级。',
      [('王宗俨','率蜀军攻长城关等四寨的指挥使')],
      when='914年十二月甲申',place='长城关',
      note='四寨与斩首二千为主书记载，不与前一日王宗铎战果混算。')
event('yang_chongben_poisoned_by_son', '杨崇本以李继徽之名被其子彦鲁毒杀，彦鲁自任留后', 16,
      '岐静难节度使李继徽为其子彦鲁所毒而死，彦鲁自为留后。',
      [('杨崇本','以李继徽之名任岐静难节度使、被其子毒杀'),('彦鲁（杨崇本子）','毒杀父亲后自任留后者')],
      when='914年年末；确日未载',place='静难、邠州',
      note='主书仅称“彦鲁”无姓，暂用附父身份限定名；“李继徽”经旧五代史卷13明示为杨崇本曾用名。')
relation('杨崇本','彦鲁（杨崇本子）','父亲',16,'李继徽为其子彦鲁所毒而死，',
         '李继徽即杨崇本，原文称彦鲁为其子；不自造彦鲁姓氏。')
claim('person',people['杨崇本'],'aliases','杨崇本曾因李茂贞养子身份冒姓李，名继徽。',16,
      '楊崇本，不知何許人，幼為李茂貞之假子，因冒姓李氏，名繼徽。',
      '旧书卷十三明示姓名变迁；本站沿既有杨崇本稳定主体。',old_date,'adds')
claim('event','event_zztj_269_0914_yang_chongben_poisoned_by_son','description',
      '《新五代史》卷四十作乾化四年彦鲁弑杨崇本。',16,
      '乾化四年，為其子彥魯所弒。',
      '与通鉴将事件置914年相合；新书只概述，不补具体日期。',new_yanlu,'corroborates')
claim('event','event_zztj_269_0914_yang_chongben_poisoned_by_son','time_original',
      '《旧五代史》卷十三却作乾化元年冬（911）彦鲁毒杀杨崇本。',16,
      '乾化元年冬，為其子彥魯所毒而死。',
      '旧书卷十三与通鉴及新书卷四十年份不合，异文保留；旧书卷八又说“去岁”支持914，但其纪年上下文待纸本核。',old_date,'conflicts')
claim('event','event_zztj_269_0914_yang_chongben_poisoned_by_son','description',
      '《旧五代史》卷八称杨崇本“去岁”为彦鲁毒杀。',16,
      '崇本乃李茂貞養子，任邠州二十餘年，去歲為其子彥魯所毒。',
      '卷八所在编年承次年邠州归梁，依其上下文“去岁”较合914；不拿它覆盖卷十三“乾化元年冬”的明确异文。',old_yanlu,'adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,17):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269乾化四年七月至岁末第11—16段连续处理；前蜀诸战不混算伤亡，杨崇本异名及彦鲁弑父年异说留审。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=914,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(11,17)],next_paragraph='zztj-v269-y0915-p001',
    coverage='卷269乾化四年七月至十二月第11—16段，晋梁邢州军情、前蜀黔州与南诏边战、吴梁徐州争夺、杨崇本被杀。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[12]['id'],'note':'王宗训“不法”是史书评价，事实层分别记录擅回成都、王建命卫士殴杀及随后人事任命；灌江陵只为未实施提案。'},
      {'paragraph_id':Q[14]['id'],'note':'潘仓嶂、山口城、武侯岭和大度河各战按原文次序分开；伤亡数量是主书口径，未合计。新五代史作大渡河。'},
      {'paragraph_id':Q[15]['id'],'note':'王宗鐸繁体名规范作王宗铎，原文原字保留。'},
      {'paragraph_id':Q[16]['id'],'note':'李继徽＝杨崇本有旧五代史卷13明文；其子仅称彦鲁，暂不自造姓。通鉴、新五代史置914年，旧五代史卷13作911年，卷8“去岁”可与914年合。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
