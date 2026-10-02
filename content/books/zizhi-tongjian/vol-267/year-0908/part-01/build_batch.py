"""Curate Tongjian 267, year 908, consecutive paragraphs 1–17."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 18))
main1 = 'tongjian-267-908-aug-nov'
main2 = 'tongjian-267-908-yearend'
new_wang = 'xinwudaishi-023-wang-jingren'
new_chu = 'xinwudaishi-066-chu-south'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0908-p001-p017',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (main1, P / 'sources/library' / main1, '6e5fe218', '司马光等'),
    (main2, P / 'sources/library' / main2, '6e5fe218', '司马光等'),
    (new_wang, P / 'sources/library' / new_wang, '6e5fe218', '欧阳修等'),
    (new_chu, P / 'sources/library' / new_chu, '6e5fe218', '欧阳修等'),
]
source_dirs = {sk: d for sk, d, _, _ in source_specs}
manifest = []
for sk, d, commit, author in source_specs:
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file=os.path.relpath(d / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (main1, main2)}
for n in range(1, 18):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'李继徽':'杨崇本', '王景仁':'王茂章', '硃景':'朱景', '硃全忠':'朱温', '蜀主':'王建', '吴越王镠':'钱镠', '晋王克用':'李克用', '晋王存勖':'李存勖', '济阴王':'唐昭宣帝', '唐哀皇帝':'唐昭宣帝', '存勗':'李存勖', '克寧':'李克宁'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/later-liang-907-923/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json',
                'content/later-liang-907-923/content-batch.json',
                'content/books/zizhi-tongjian/vol-263/year-0902/part-02/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_267_0908_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷267·开平二年（908）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='五代十国', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷267开平二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=908, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_267_0908_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        if key not in {row['key'] for row in B['events']}:
            row = dict(legacy_events[reuse_key], status='draft')
            B['events'].append(row)
        reused.add(key)
        desc = title + '。'
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '908年本段条；确日未载', dynasty='五代十国', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '908年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_267_0908_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def relation(key, n, quote, note):
    assert quote in Q[n]['text']
    row = legacy_relations[key]
    if key not in {item['key'] for item in B['person_relationships']}:
        B['person_relationships'].append(dict(row, status='draft'))
        reused.add(key)
    claim('person_relationship',key,'description',row['description'],n,quote,note)

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_267_0908_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1–3: Wuyue diplomacy and the fighting over Suzhou and Dongzhou.
event('wang_jingren_mission','钱镠遣王茂章（改名景仁）赴梁陈述取淮南之策',1,
      '八月，吴越王镠遣宁国节度使王景仁奉表诣大梁，陈取淮南之策。景仁即茂章也，避梁讳改焉。',
      [('钱镠','遣使赴后梁的吴越王'),('王景仁','原名王茂章，奉表陈策的宁国节度使')],
      when='908年八月',place='大梁',
      note='王景仁与王茂章为同一人，复用已勘误的王茂章稳定key；陈策不等于已出兵取淮南。')
extra(new_wang,'event','event_zztj_267_0908_wang_jingren_mission','description',
      '《新五代史》卷二十三亦记王景仁初名茂章。',
      '王景仁，廬州合淝人也。初名茂章',1,'corroborates',
      '传记确证姓名同一；繁体原字保留，展示仍复用王茂章。')
event('huainan_suzhou_siege','淮南周本、吕师造率军攻吴越并围苏州',2,
      '淮南遣步军都指挥使周本、南面统军使吕师造击吴越，九月，围苏州。',
      [('周本','淮南步军都指挥使，参与围苏州'),('吕师造','淮南南面统军使，参与围苏州')],
      when='908年九月围苏州；出兵稍早',place='苏州',
      note='“淮南兵死者万馀人”属于同段东洲战事叙述，未作为此次围苏州的精确兵损。')
event('dongzhou_capture','吴越张仁保攻取常州东洲',2,
      '吴越将张仁保攻常州之东洲，拔之。',
      [('张仁保','攻取东洲的吴越将领')],when='908年九月条；确日未载',place='常州东洲',
      note='“拔之”只指东洲，不指常州全境。')
event('dongzhou_recovery','淮南陈璋、柴再用在鱼荡败张仁保并复东洲',2,
      '淮南以池州团练使陈璋为水陆行营都招讨使，帅柴再用等诸将救东洲，大破仁保于鱼荡，复取东洲。',
      [('陈璋','受任水陆行营招讨使并救东洲'),('柴再用','随军救东洲的淮南将领'),('张仁保','在鱼荡被击败的吴越将领')],
      when='908年九月后条；确日未载',place='鱼荡、东洲',
      note='先受任再救援、交战并收复东洲；“万馀”兵损为主书概数，未强加到单次交战。')
claim('event','event_zztj_267_0908_dongzhou_recovery','description',
      '柴再用战时舟坏，以长槊浮渡脱险，随后用家中备给僧人的食物犒军。',2,
      '柴再用方战舟坏，长槊浮之，仅而得济。家人为之饭僧千人，再用悉取其食以犒部兵',
      '仅据主书记录，饭僧千人是原计划人数，不写成已施行。')
event('shu_empress_zhou','前蜀立周氏为皇后',3,
      '丙子，蜀立皇后周氏。后，许州人也。',
      [('前蜀皇后周氏','被立为前蜀皇后')],when='908年丙子',place='蜀',
      note='周氏为姓氏称谓，无确切名，避免与其他周氏人物合并；许州为籍贯。')

# 4: several theaters in a single long chronological paragraph.
event('jin_attacks_jinzhou','周德威、李嗣昭攻晋州；朱温赴陕州救援，晋军退隰州',4,
      '晋周德威、李嗣昭将兵三万出阴地关，攻晋州，刺史徐怀玉拒守。帝自将救之，丁丑，发大梁，乙酉，至陕州。',
      [('周德威','率晋兵攻晋州'),('李嗣昭','率晋兵攻晋州'),('徐怀玉','守晋州的刺史'),('朱温','自大梁出发救援晋州')],
      when='908年九月丁丑梁帝出发、乙酉至陕州；攻晋州确日未载',place='晋州、陕州',
      note='下文乙未晋军退隰州单列事实；梁帝到陕州不代表已经抵晋州。')
claim('event','event_zztj_267_0908_jin_attacks_jinzhou','description',
      '周德威等听闻梁帝将至，于乙未退保隰州。',4,
      '周德威等闻帝将至，乙未，退保隰州',
      '退兵是已发生的结果，梁帝亲至晋州不是本段事实。')
event('hujingzhang_shangpingguan','胡敬璋攻上平关，刘知俊击破',4,
      '戊子，岐王所署延州节度使胡敬璋寇上平关，刘知俊击破之。',
      [('胡敬璋','率岐军进攻上平关'),('刘知俊','击败胡敬璋')],
      when='908年九月戊子',place='上平关',
      note='岐王所署官职保留原说，和晋州、荆南战线分开。')
event('chu_jingnan_hankou','高季昌断楚朝贡路，许德勋至沙头后高季昌请和',4,
      '荆南节度使高季昌遣兵屯汉口，绝楚朝贡之路。楚王殷遣其将许德勋将水军击之，至沙头，季昌惧而请和。',
      [('高季昌','遣兵阻断楚朝贡路并请和'),('马殷','遣许德勋出兵的楚王'),('许德勋','率楚水军至沙头')],
      when='908年九月后条；确日未载',place='汉口、沙头',
      note='请和是主书所述结果，未推断双方正式盟约及持续时限。')
extra(new_chu,'event','event_zztj_267_0908_chu_jingnan_hankou','description',
      '《新五代史》卷六十六亦记高季昌阻汉口、许德勋攻沙头及高季昌求和。',
      '殷遣許德勳攻其沙頭，季昌求和，乃止',4,'corroborates',
      '新史说“乃止”指此役止兵，不推为长期和平。')
event('chu_lingnan_six_prefectures','吕师周率楚军攻岭南，取昭、贺、梧、蒙、龚、富六州',4,
      '殷又遣步军都指挥使吕师周将兵击岭南，与清海节度使刘隐十馀战，取昭、贺、梧、蒙、龚、富六州。',
      [('马殷','命吕师周攻岭南的楚王'),('吕师周','率楚军攻岭南并取六州'),('刘隐','与楚军交战的清海节度使')],
      when='908年九月后条；十余战跨度未载',place='岭南六州',
      note='六州名单依主书；“十馀战”为史书概述，不能定每战日期或绘精确疆界。')
extra(new_chu,'event','event_zztj_267_0908_chu_lingnan_six_prefectures','description',
      '《新五代史》卷六十六亦记吕师周率楚军取昭、贺、梧、蒙、龚、富诸州。',
      '以為馬步軍都指揮使，率兵攻嶺南，取昭、賀、梧、蒙、龔、富等州',4,'corroborates',
      '新史在吕师周来奔楚的叙事后概述南征，未给本年精确战日。')

# 5–10: Shu court, tomb robbery, titles and Liang Zhen's residence in Jingnan.
event('shu_consorts_oct','王建立张氏为贵妃、徐氏姐妹为贤妃和德妃',5,
      '冬，十月，蜀主立后宫张氏为贵妃，徐氏为贤妃，其妹为德妃。',
      [('王建','任命后宫封号的蜀主')],when='908年十月',place='蜀',
      note='两徐仅以氏族和姐妹关系见载，具体名字未明，不以通称建可混同的人物节点。')
claim('event','event_zztj_267_0908_shu_consorts_oct','description',
      '贵妃张氏为王宗懿之母；徐氏姐妹为徐耕之女。',5,
      '张氏，郪人，宗懿之母也。二徐，耕之女也',
      '姓氏称谓及亲属关系按原文展示；未得具体名，不创建泛称人物关系节点。')
event('wen_tao_tang_tombs','温韬聚众嵯峨山并盗掘多处唐帝陵',6,
      '华原贼帅温韬聚众嵯峨山，暴掠雍州诸县，唐帝诸陵发之殆遍。',
      [('温韬','聚众劫掠并盗掘唐帝陵')],when='908年十月条；持续时间未载',place='嵯峨山、雍州诸县',
      note='“殆遍”为概述，不推出具体被盗陵墓完整名单或时间。')
event('shu_xingxiu_review','王建在星宿山讲武',7,
      '庚戌，蜀主讲武于星宿山，步骑三十万。',
      [('王建','在星宿山讲武的蜀主')],when='908年庚戌',place='星宿山',
      note='“步骑三十万”沿主书记数，不作为现代清点兵力。')
event('liang_emperor_returns_daliang','朱温返回大梁',8,
      '丁巳，帝还大梁。',
      [('朱温','返回大梁的后梁皇帝')],when='908年丁巳',place='大梁',
      note='与第4段至陕州相接，不据此推定中途具体路线。')
event('liu_yin_commission','后梁任刘隐清海、静海节度使，刘隐留下两名官告使',9,
      '辛酉，以刘隐为清海、静海节度使，以膳部郎中赵光裔、右补阙李殷衡充官告使，隐皆留之。',
      [('刘隐','受任两道节度使并留下官告使'),('赵光裔','受派的官告使，后被刘隐留下'),('李殷衡','受派的官告使，后被刘隐留下')],
      when='908年辛酉',place='岭南',
      note='授官与官告使留任据主书；刘隐实际控制范围及二人后续职掌未扩写。')
claim('event','event_zztj_267_0908_liu_yin_commission','description',
      '赵光裔是赵光逢之弟，李殷衡是李德裕之孙。',9,
      '光裔，光逢之弟；殷衡，德裕之孙也',
      '亲属关系明载，称谓规范化；不因同姓推测其他亲属。')
person('赵光逢',9,'赵光裔之兄','光裔，光逢之弟')
B['person_relationships'].append(dict(key='relationship_person_赵光逢_person_赵光裔_兄长',
    person_a_key=people['赵光逢'],person_b_key=people['赵光裔'],relation_type='兄长',
    description='赵光逢是赵光裔的兄长。',status='draft'))
claim('person_relationship','relationship_person_赵光逢_person_赵光裔_兄长','description',
      '赵光逢是赵光裔的兄长。',9,'光裔，光逢之弟',
      '“之弟”明确长幼；赵光逢已见旧批次，沿用其稳定key。')
event('liang_zhen_jingnan','梁震途经江陵受高季昌礼遇，以白衣身份留为谋主',10,
      '过江陵，高季昌爱其才识，留之，欲奏为判官。震耻之，欲去，恐及祸',
      [('梁震','途经江陵，被高季昌挽留'),('高季昌','挽留梁震并欲奏为判官')],
      when='908年本段“至是”后起；长期居留未定年',place='江陵',
      note='梁震原欲入蜀，途经江陵被挽留；“欲奏为判官”未成，后以白衣参与谋议。')
claim('event','event_zztj_267_0908_liang_zhen_jingnan','description',
      '梁震以白衣参谋，不受高氏辟署；高季昌称其“先辈”。',10,
      '震终身止称前进士，不受高氏辟署。季昌甚重之，以为谋主，呼曰先辈。',
      '这句是梁震要求；“终身止称前进士，不受高氏辟署”为后见概述，后续未全发生于908年。')

# 11–17: Liang's Huainan raid, western succession, Youzhou fighting, and court changes.
event('kou_yanqing_huoqiu','寇彦卿袭霍丘，被土豪朱景击败',11,
      '十一月，彦卿帅众二千袭霍丘，为土豪硃景所败',
      [('寇彦卿','奉后梁命进击淮南，袭霍丘失败'),('朱景','在霍丘击败寇彦卿的土豪')],
      when='908年十一月',place='霍丘',
      note='原文作“硃景”，展示转简为朱景；与既有朱姓人物需凭事迹区分。“二千”依主书记数。')
claim('event','event_zztj_267_0908_kou_yanqing_huoqiu','description',
      '寇彦卿由朱温依钱镠请求任为东南面行营都指挥使，进击淮南。',11,
      '帝从吴越王镠之请，以亳州团练使寇彦卿为东南面行营都指挥使，击淮南',
      '后梁任命已发生，但与吴越协同的具体兵力和指挥关系不扩写。')
event('kou_yanqing_retreat','寇彦卿攻庐、寿州均未胜，受史俨抵御后撤回',11,
      '又攻庐、寿二州，皆不胜。淮南遣滁州刺史史俨拒之，彦卿引归。',
      [('寇彦卿','攻庐寿不克而撤回'),('史俨','奉淮南命抵御梁军')],
      when='908年十一月霍丘战后；确日未载',place='庐州、寿州',
      note='“皆不胜”不写成梁军占领两州；与霍丘袭击分开。')
event('li_sijian_dies','定难节度使李思谏去世，其子李彝昌自为留后',12,
      '定难节度使李思谏卒；甲戌，其子彝昌自为留后。',
      [('李思谏','去世的定难节度使'),('李彝昌','在父亲去世后自任留后')],
      when='908年甲戌李彝昌自为留后；李思谏卒日未载',place='定难',
      note='“自为留后”是李彝昌自行承位，不写成当日朝廷正式任命。')
B['person_relationships'].append(dict(key='relationship_person_李思谏_person_李彝昌_父亲',
    person_a_key=people['李思谏'],person_b_key=people['李彝昌'],relation_type='父亲',
    description='李思谏是李彝昌的父亲。',status='draft'))
claim('person_relationship','relationship_person_李思谏_person_李彝昌_父亲','description',
      '李思谏是李彝昌的父亲。',12,'其子彝昌自为留后',
      '本段“其子”承李思谏，父子方向明确。')
event('liu_shouwen_youzhou','刘守文攻幽州，刘守光得晋援后于卢台、玉田两败刘守文',13,
      '刘守文举沧德兵攻幽州，刘守光求救于晋，晋王遣兵五千助之。丁亥，守文兵至卢台军，为守光所败；又战玉田，亦败。守文乃还。',
      [('刘守文','率沧德兵攻幽州，连败后撤军'),('刘守光','向晋求援并击败刘守文'),('李存勖','派晋兵支援刘守光的晋王')],
      when='908年丁亥卢台战、其后玉田战',place='卢台军、玉田',
      note='“五千”按主书记数；刘守文、刘守光的兄弟关系已存，不在同场叙述里另建关系。')
event('liang_chancellors_nov','张策致仕，杨涉复任同平章事',14,
      '癸巳，中书侍郎、同平章事张策以刑部尚书致仕；以左仆射杨涉同平章事。',
      [('张策','以刑部尚书致仕'),('杨涉','受任同平章事')],
      when='908年癸巳',place='后梁朝廷',
      note='两项任免同日条，未定公历日。')
event('hu_jingzhang_dies','胡敬璋去世，李继徽以刘万子代镇延州',15,
      '保塞节度使胡敬璋卒，静难节度使李继徽以其将刘万子代镇延州。',
      [('胡敬璋','去世的保塞节度使'),('李继徽','遣将刘万子代镇延州'),('刘万子','被派代镇延州的将领')],
      when='908年岁末条；确日未载',place='延州',
      note='李继徽为杨崇本受岐王赐名后的称谓，沿用已发布的杨崇本稳定key；胡敬璋卒与刘万子代镇相连，但不推断朝廷正式授节度使。')
event('yang_longyan_announces_succession','杨隆演遣万全感间道告晋、岐其继位',16,
      '是岁，弘农王遣军将万全感赍书间道诣晋及岐，告以嗣位。',
      [('杨隆演','遣将通报继位的弘农王'),('万全感','携书间道出使晋与岐')],
      when='908年是岁；确月日未载',place='晋、岐',
      note='这里只确认派使通报，不将晋、岐回应或结盟倒填到908年。')
event('liang_luoyang_plan','朱温拟迁都洛阳',17,
      '帝将迁都洛阳。',
      [('朱温','筹划迁都洛阳的后梁皇帝')],
      when='908年岁末；迁都为计划',place='洛阳',
      note='“将”表示计划，未在908年完成迁都；执行过程见下一年。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,18):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷267开平二年第1—17段连续处理；围苏州与东洲战分开，多处战线分录，人物繁简及改名沿既有身份。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=267,year=908,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(1,18)],next_paragraph='zztj-v267-y0909-p001',
    coverage='卷267开平二年17段连续处理；苏州东洲战、晋州战、楚岭南战、朝廷人事与年末迁都计划。卷266与卷267合成908年完整主线。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
