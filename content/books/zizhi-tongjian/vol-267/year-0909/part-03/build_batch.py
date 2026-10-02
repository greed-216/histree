"""Curate Tongjian 267, year 909, consecutive paragraphs 41–60."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 61))
main1 = 'tongjian-267-909-summer-battles'
main2 = 'tongjian-267-909-autumn'
main3 = 'tongjian-267-909-yearend'
old_jin = 'jiuwudaishi-027-jinzhou'
new_jin = 'xinwudaishi-005-jinzhou'
old_wang = 'jiuwudaishi-021-wangtieqiang'
new_cang = 'xinwudaishi-039-cangzhou'
new_liu = 'xinwudaishi-044-liuzhijun-flight'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0909-p041-p060',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (main1, P.parent / 'part-02/sources/library' / main1, 'f23ed514', '司马光等'),
    (main2, P / 'sources/library' / main2, '0d6451a5', '司马光等'),
    (main3, P / 'sources/library' / main3, '0d6451a5', '司马光等'),
    (old_jin, P / 'sources/library' / old_jin, '0d6451a5', '薛居正等'),
    (new_jin, P / 'sources/library' / new_jin, '0d6451a5', '欧阳修等'),
    (old_wang, P / 'sources/library' / old_wang, '0d6451a5', '薛居正等'),
    (new_cang, P / 'sources/library' / new_cang, '0d6451a5', '欧阳修等'),
    (new_liu, P.parent / 'part-02/sources/library' / new_liu, '528dc5cd', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (main1, main2, main3)}
for n in range(41, 61):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'徐知诰':'李昪', '吕兗':'吕兖', '李继徽':'杨崇本', '王景仁':'王茂章', '硃景':'朱景', '硃全忠':'朱温', '蜀主':'王建', '吴越王镠':'钱镠', '晋王克用':'李克用', '晋王存勖':'李存勖', '济阴王':'唐昭宣帝', '唐哀皇帝':'唐昭宣帝', '存勗':'李存勖', '克寧':'李克宁'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/later-liang-907-923/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json',
                'content/later-liang-907-923/content-batch.json',
                'content/books/zizhi-tongjian/vol-260/year-0895/part-04/content-batch.json',
                'content/books/zizhi-tongjian/vol-263/year-0902/part-02/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_267_0909_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷267·开平三年（909）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷267开平三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=909, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_267_0909_' + code)
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
                                time_original=when or '909年本段条；确日未载', dynasty='五代十国', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '909年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_267_0909_' + code + '_' + pk
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
    ck = f'claim_zztj_267_0909_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 41–44: court and command appointments after the summer campaigns.
event('liang_emperor_recovers','朱温病情稍缓并恢复视朝',41,
      '甲寅，上疾小瘳，始复视朝。',
      [('朱温','病情稍缓后恢复视朝的梁帝')],when='909年八月甲寅',place='洛阳',
      note='“小瘳”仅为稍愈，不推定病已根治。')
event('kanghuaizhen_commission','康怀贞受任西路行营副招讨使',42,
      '以镇国节度使康怀贞为西路行营副招讨使。',
      [('康怀贞','受任西路行营副招讨使')],when='909年八月条；确日未载',
      note='沿《通鉴》康怀贞用字；旧新史有关战役或作康怀英，既有人物身份未强并。')
event('shu_heir_six_armies','蜀太子王宗懿判六军并开永和府',43,
      '蜀主命太子宗懿判六军，开永和府，妙选朝士为僚属。',
      [('王建','命太子判六军的蜀主'),('王宗懿','判六军、开永和府的太子')],
      when='909年八月条；确日未载',place='蜀',
      note='朝士名单未载，不补造府僚。')
event('fangzhou_report','均州张敬方奏克房州',44,
      '辛酉，均州刺史张敬方奏克房州。',
      [('张敬方','奏报攻取房州的均州刺史')],when='909年八月辛酉',place='房州',
      note='“奏克”为其上报；与第39段杨虔以房州附蜀相接，未据此推定所有守将结局。')

# 45–49: Jinzhou and Xiangzhou theaters, with conflicting accounts of Mengkeng.
event('jinzhou_siege_relief','晋周德威等围晋州，杨师厚救援后晋军撤围',45,
      '晋王引兵南下，先遣周德威等将兵出阴地关攻晋州，刺史边继威悉力固守。晋兵穿地道，陷城二十馀步，城中血战拒之，一夕城复成。',
      [('李存勖','引晋兵南下的晋王'),('周德威','率军围晋州'),('边继威','固守晋州的刺史')],
      when='909年八月后条；确日未载',place='晋州',
      note='本段岐王欲令刘知俊攻灵夏和约晋出兵为计划；晋州围攻实际发生，不将灵夏计划记为此时已成。')
claim('event','event_zztj_267_0909_jinzhou_siege_relief','description',
      '杨师厚奉诏救晋州，在蒙坑击破周德威骑兵，晋军解围退去。',45,
      '师厚击破之，进抵晋州，晋兵解围遁去',
      '《通鉴》如此记；《新五代史》庄宗纪则称晋军在蒙坑败梁军，异说并列。')
extra(new_jin,'event','event_zztj_267_0909_jinzhou_siege_relief','description',
      '《新五代史》卷五作晋军于蒙坑败梁军，与《通鉴》杨师厚击破周德威相反。',
      '遣周德威攻晉州，敗梁軍于蒙阬',45,'conflicts',
      '新史未给本段详细战日；不强行把双方胜负写为同一版本。')
extra(old_jin,'event','event_zztj_267_0909_jinzhou_siege_relief','description',
      '《旧五代史》卷二十七主文记杨师厚赴援后周德威撤围，支持撤围结局；其注文另录晋方败梁说。',
      '梁祖遣楊師厚領兵赴援，德威乃收軍而退',45,'corroborates',
      '主文仅明晋军撤围，未独立确认蒙坑交战谁胜；旧书注文中的相反说法不算本条主文确证。')
event('li_hong_jingnan_raid','李洪攻荆南被倪可福击败，梁命陈晖会兵讨伐',46,
      '李洪寇荆南，高季昌遣其将倪可福击败之。诏马步都指挥使陈晖将兵会荆南兵讨洪。',
      [('李洪','攻荆南而败的襄州叛将'),('高季昌','遣倪可福出战的荆南节度使'),('倪可福','击败李洪'),('陈晖','奉梁命赴荆南会兵')],
      when='909年八月后条；确日未载',place='荆南',
      note='陈晖受命会兵已发生，攻拔襄州要到第48段。')
event('wang_kai_chancellor','王建任王锴为前蜀宰相',47,
      '蜀主以御史中丞王锴为中书侍郎、同平章事。',
      [('王建','任命王锴的蜀主'),('王锴','受任中书侍郎、同平章事')],
      when='909年八月后条；确日未载',place='蜀',
      note='主书未载此处确日，不借邻段九月丁酉定日。')
event('xiangzhou_recovered','陈晖军克襄州，李洪、杨虔等被送洛阳处死',48,
      '陈晖军至襄州，李洪逆战，大败，王求死。九月，丁酉，拔其城，斩叛兵千人，执李洪、杨虔等送洛阳，斩之。',
      [('陈晖','率梁军击败李洪并夺襄州'),('李洪','战败被俘后送洛阳处死'),('杨虔','被俘送洛阳处死'),('王求','此役身亡的乱将')],
      when='909年九月丁酉拔襄州；李洪等处斩随后',place='襄州、洛阳',
      note='“千人”为主书记载的斩叛兵数，不等于此役全部死伤；李洪、杨虔与叛兵处置分开。')
event('wang_tan_luzhou','后梁任王檀为潞州东面行营招讨使',49,
      '丁未，以保义节度使王檀为潞州东面行营招讨使。',
      [('王檀','受任潞州东面行营招讨使')],when='909年九月丁未',place='潞州',
      note='授职不等于本段已攻下潞州。')

# 50: Liu Shouguang's son receives Yichang command.
event('liu_jiwei_yichang','刘守光遣子刘继威安抚沧州，梁任刘继威义昌留后',50,
      '刘守光奏遣其子中军兵马使继威安抚沧州吏民。戊申，以继威为义昌留后。',
      [('刘守光','遣子安抚沧州并奏请的燕王'),('刘继威','获任义昌留后')],
      when='909年九月戊申授留后；遣使稍早',place='沧州',
      note='安抚为刘守光奏称，城内刘延祚军仍在抵抗，不写成沧州已完全受其控制。')
B['person_relationships'].append(dict(key='relationship_person_刘守光_person_刘继威_父亲',
    person_a_key=people['刘守光'],person_b_key=people['刘继威'],relation_type='父亲',
    description='刘守光是刘继威的父亲。',status='draft'))
claim('person_relationship','relationship_person_刘守光_person_刘继威_父亲','description',
      '刘守光是刘继威的父亲。',50,'刘守光奏遣其子中军兵马使继威',
      '“其子”明载父子；不把刘继威与李继威等异人混同。')

# 51–56: court, Fujian ties, calendar, Huzhou killings, and Wei succession.
event('liang_chancellors_sep','后梁罢韩建、杨涉相位，任赵光逢、杜晓同平章事',51,
      '辛亥，侍中韩建罢守太保，左仆射、同平章事杨涉罢守本官。以太常卿赵光逢为中书侍郎，翰林奉旨工部侍郎杜晓为户部侍郎，并同平章事。',
      [('韩建','罢侍中改守太保'),('杨涉','罢同平章事、守原官'),('赵光逢','受任中书侍郎、同平章事'),('杜晓','受任户部侍郎、同平章事')],
      when='909年九月辛亥',place='后梁朝廷',
      note='四项任免为同日朝廷政事；杜晓是杜让能之子见下句。')
person('杜让能',51,'杜晓之父','晓，让能之子也')
B['person_relationships'].append(dict(key='relationship_person_杜让能_person_杜晓_父亲',
    person_a_key=people['杜让能'],person_b_key=people['杜晓'],relation_type='父亲',
    description='杜让能是杜晓的父亲。',status='draft'))
claim('person_relationship','relationship_person_杜让能_person_杜晓_父亲','description',
      '杜让能是杜晓的父亲。',51,'晓，让能之子也',
      '本段“晓”指杜晓，父亲杜让能沿用旧实体。')
event('fujian_huainan_break','闽王王审知斩淮南使张知远，上表后与淮南断交',52,
      '淮南遣使者张知远修好于福建，知远倨慢，闽王审知斩之，表上其书，始与淮南绝。',
      [('张知远','奉淮南命赴福建修好而被处死'),('王审知','斩使并向后梁上表的闽王')],
      when='909年九月后条；确日未载',place='福建',
      note='“倨慢”是史书对使者行为的叙述；断交是本段结局，不推断双方长期所有往来断绝。')
event('wang_shenzhi_rule_summary','史书概述王审知在闽节俭、宽刑薄赋及海道入贡',52,
      '审知性俭约，常蹑麻屦，府舍卑陋，未尝营葺。宽刑薄赋，公私富实，境内以安。岁自海道登、莱入贡，没溺者什四五。',
      [('王审知','史书所述在闽施政与海道贡使相关的闽王')],
      when='王审知治闽期间；本段总述，确年未载',place='福建、登州、莱州',year=None,
      note='“岁自海道”及损失比例为史书跨年概述，不全定在909年；“什四五”不当作现代精确死亡率。')
event('yongchang_calendar','前蜀采行胡秀林所献《永昌历》',53,
      '冬，十月，甲子，蜀司天监胡秀林献《永昌历》，行之。',
      [('胡秀林','献《永昌历》的蜀司天监')],
      when='909年十月甲子',place='蜀',
      note='原文明确“行之”，与仅提出建议不同；不推算历法具体规则。')
event('gao_li_huzhou_killings','高澧于湖州诱杀民兵并大规模搜杀',54,
      '澧悉集民兵于开元寺，绐云犒享，入则杀之，死者逾半；在外者觉之，纵火作乱。澧闭城大索，凡杀三千人。',
      [('高澧','诱杀湖州民兵并搜杀城内者的刺史')],
      when='909年十月戊辰前；确日未载',place='湖州开元寺',
      note='“逾半”和“三千人”均为主书记述，不能据此推出被召民兵总人数；其所谓欲尽杀百姓是发言，不是先已施行。')
event('gao_li_defects','高澧叛吴越附淮南、焚镇，钱镠遣钱镖讨之',54,
      '吴越王镠欲诛之，戊辰，澧以州叛附于淮南，举兵焚义和临平镇，镠命指挥使钱镖讨之。',
      [('高澧','以湖州附淮南并焚镇'),('钱镠','命讨高澧的吴越王'),('钱镖','奉命讨高澧的指挥使')],
      when='909年十月戊辰叛附；讨伐命令随后',place='湖州、义和临平镇',
      note='钱镠“欲诛”是意向，实际命钱镖讨伐已载；不把此段写成高澧已被擒。')
event('liang_nov_rites','朱温十一月行圜丘礼并大赦',55,
      '十一月，甲午，帝告谢于圜丘；戊戌，大赦。',
      [('朱温','行圜丘礼并发布大赦的梁帝')],
      when='909年十一月甲午礼圜丘、戊戌大赦',place='洛阳',
      note='两次朝廷行为分隔干支日，保留原时序。')
event('luo_shaowei_ill','罗绍威患风痹并上表求退',56,
      '鄴王罗绍威得风痹病，上表称：“魏故大镇，多外兵，愿得有功重臣镇之，臣乞骸骨归第。”',
      [('罗绍威','患病并上表求退的魏博节度使')],
      when='909年十一月己亥前；确日未载',place='魏博',
      note='“风痹”为主书病名，未按现代医学重新诊断；请求卸职未在本段得到准许。')
event('luo_zhouhan_appointment','朱温任罗周翰为天雄节度副使、知府事',56,
      '己亥，以其子周翰为天雄节度副使，知府事。',
      [('罗周翰','罗绍威之子，获任天雄节度副使')],
      when='909年十一月己亥',place='魏博',
      note='任副使不等于罗绍威当时已去世；朱温随后劝罗绍威强食，仍盼其康复。')
B['person_relationships'].append(dict(key='relationship_person_罗绍威_person_罗周翰_父亲',
    person_a_key=people['罗绍威'],person_b_key=people['罗周翰'],relation_type='父亲',
    description='罗绍威是罗周翰的父亲。',status='draft'))
claim('person_relationship','relationship_person_罗绍威_person_罗周翰_父亲','description',
      '罗绍威是罗周翰的父亲。',56,'以其子周翰为天雄节度副使',
      '“其子”承罗绍威；仅确认父子，不从后见官号倒推继位。')

# 57: Lingzhou relief, the ambush at Shengping, and Liu Zhijun's new command.
event('lingzhou_siege','岐王遣刘知俊围灵州，韩逊向后梁求援',57,
      '岐王欲取灵州以处刘知俊，且以为牧马之地，使知俊自将兵攻之。朔方节度使韩逊遣使告急；',
      [('刘知俊','奉岐王命攻灵州'),('韩逊','朔方节度使，向梁廷求援')],
      when='909年十一月至十二月前；确日未载',place='灵州',
      note='岐王欲以灵州安置刘知俊是计划；刘知俊实际围城及韩逊告急有后文印证。')
event('liang_bin_ning_relief','朱温遣康怀贞、寇彦卿攻邠宁以牵制刘知俊',57,
      '诏镇国节度使康怀贞、感化节度使寇彦卿将兵攻邠宁以救之。怀贞等所向皆捷，克宁、衍二州，拔庆州南城，刺史李彦广出降。',
      [('朱温','下诏救灵州的梁帝'),('康怀贞','率梁军攻邠宁'),('寇彦卿','与康怀贞并军'),('李彦广','庆州南城被攻后出降的刺史')],
      when='909年十一月至十二月己丑前',place='邠宁、宁州、衍州、庆州南城',
      note='主书详列梁军攻取地点，不推成完整取得庆州；康怀贞与他书康怀英名称不自动合并。')
event('liu_lifts_lingzhou','刘知俊于十二月己丑解灵州围并撤军',57,
      '刘知俊闻之，十二月，己丑，解灵州围，引兵还。',
      [('刘知俊','因梁军攻邠宁而解灵州围')],
      when='909年十二月己丑',place='灵州',
      note='围城已解除，不能写成岐军占领灵州。')
extra(new_liu,'event','event_zztj_267_0909_liu_lifts_lingzhou','description',
      '《新五代史》卷四十四亦记韩逊求援及梁军攻邠宁牵制刘知俊。',
      '韓遜告急，太祖遣康懷英、寇彥卿等攻邠寧以牽之',57,'adds',
      '新史将主书康怀贞写作康怀英；沿已存异名争议并列，不据繁简转换合并人物。')
event('wang_yanzhang_sanshui','刘知俊于三水截击梁军，王彦章力战使康怀贞军得过',57,
      '怀贞等还，至三水，知俊遣兵据险邀之，左龙骧军使寿张王彦章力战，怀贞等乃得过。',
      [('刘知俊','在三水设伏截击梁军'),('王彦章','力战掩护梁军过险'),('康怀贞','率梁军从三水脱险')],
      when='909年十二月己丑后；确日未载',place='三水',
      note='三水脱险不等于整个梁军此后安全返营，升平另遭伏击。')
event('shengping_ambush','刘知俊于升平山口伏击康怀贞军，梁军大败',57,
      '至升平，刘知俊伏兵山口，怀贞大败，仅以身免，德遇等军皆没。',
      [('刘知俊','伏击梁军的岐将'),('康怀贞','升平战败而逃生的梁将'),('李德遇','梁军裨将，所部覆没')],
      when='909年十二月三水战后；确日未载',place='升平',
      note='主书“德遇等军皆没”指部队损失，未明言李德遇、许从实、王审权个人结局。')
extra(new_liu,'event','event_zztj_267_0909_shengping_ambush','description',
      '《新五代史》卷四十四记刘知俊于升平大败梁将康怀英，并记许从实被杀。',
      '知俊大敗懷英於昇平，殺梁將許從實',57,'adds',
      '主书称康怀贞、许从实所部分道皆没；新史给许从实本人结局及不同将名，不以主书军事损失推定其死亡。')
event('liu_zhijun_jingzhou','岐王授刘知俊彰义节度使，镇泾州',57,
      '岐王以知俊为彰义节度使，镇泾州。',
      [('刘知俊','受岐王授彰义节度使并镇泾州')],
      when='909年十二月升平战后；确日未载',place='泾州',
      note='与出奔岐后仅获厚俸无镇的第29段形成时序变化。')

# 58–60: retrospective portrait, Shu retirement, and the Cangzhou famine.
event('wang_yanzhang_iron_spears','王彦章以双铁枪闻名，时人称“王铁枪”',58,
      '王彦章骁勇绝伦，每战用二铁枪，皆重百斤，一置鞍中，一在手，所向无前，时人谓之“王铁枪”。',
      [('王彦章','史书概述其惯用双铁枪并有“王铁枪”称号')],
      when='王彦章从军期间；本段人物追叙，确年未载',year=None,
      note='“每战”和铁枪重量是主书概述，不定为909年单次战斗，也不转算现代重量。')
extra(old_wang,'event','event_zztj_267_0909_wang_yanzhang_iron_spears','description',
      '《旧五代史》卷二十一亦记王彦章从军时常持铁枪冲阵。',
      '常持鐵槍衝堅陷陣',58,'corroborates',
      '旧书不在此段确认“每枪百斤”或两枪细节，只印证铁枪作战形象。')
event('wang_zongbian_retirement','蜀州刺史王宗弁称疾归成都，拒受检校太保',59,
      '蜀蜀州刺史王宗弁称疾，罢归成都，杜门不出。蜀主疑其矜功怨望，加检校太保，固辞不受',
      [('王宗弁','称疾退居成都并拒绝加官的前蜀将领'),('王建','疑王宗弁怨望而加官的蜀主')],
      when='909年十二月后条；确日未载',place='蜀州、成都',
      note='底本“蜀蜀州”疑重复字，保留原文；王建的疑虑不作为王宗弁确有怨望的事实。')
claim('event','event_zztj_267_0909_wang_zongbian_retirement','description',
      '王建最终认可王宗弁退居，并加赐给。',59,
      '蜀主嘉其志而许之，赐与有加',
      '其“廉者足而不忧”是王宗弁自述，不作为客观财产判断。')
event('cangzhou_starvation','刘守光长期围沧州，城内粮尽并发生食人惨况',60,
      '刘守光围沧州久不下，执刘守文至城下示之，犹固守。城中食尽，民食堇泥，军士食人',
      [('刘守光','围沧州并押刘守文示城的燕王'),('刘守文','被押到城下示众的沧州旧帅')],
      when='909年岁末，围城持续数月；确日未载',place='沧州',
      note='源文后有私用损字“”，不据疑字补定牲畜身体部位；本段未记沧州陷落。')
extra(new_cang,'event','event_zztj_267_0909_cangzhou_starvation','description',
      '《新五代史》卷三十九也记刘守光围沧州、城内粮尽，并称围城百余日。',
      '守光圍之百餘日，城中食盡',60,'adds',
      '新史“百余日”为概数，主书“久不下”，不据此逆推出精确开围日期。')
event('lu_yan_slaughter','吕兖设“宰杀务”，杀害羸弱者以供沧州守军',60,
      '吕兗选男女羸弱者，饲以麹面而烹之，以给军食，谓之宰杀务。',
      [('吕兗','在沧州围困时主持“宰杀务”的节度判官')],
      when='909年沧州围城期间；确日未载',place='沧州',
      note='“吕兗”展示规范作吕兖，来源仍照原字；此为史书所记极端暴行，不淡化为普通军粮征集。')
extra(new_cang,'event','event_zztj_267_0909_lu_yan_slaughter','description',
      '《新五代史》卷三十九亦记吕兖等将饥民供军食，称“宰务”。',
      '兗等率城中饑民食以麴，號「宰務」',60,'corroborates',
      '两书称谓“宰杀务/宰务”不同，保留原字；细节仅按各自原文陈列。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,61):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷267开平三年第41—60段连续处理；晋州蒙坑异说、升平分阶段战事及沧州困守按证据保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=267,year=909,
    primary_source_key=main1,primary_source_keys=[main1,main2,main3],
    paragraphs=[Q[n]['id'] for n in range(41,61)],next_paragraph='zztj-v267-y0910-p001',
    coverage='卷267开平三年第41—60段连续处理；晋州、襄州、灵州升平、闽吴断交、湖州屠杀、沧州饥荒。与前两批合为909年完整主线。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
