"""Curate Tongjian 267, year 910, consecutive paragraphs 35-43."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 44))
main1 = 'tongjian-267-910-winter'
main2 = 'tongjian-267-910-yearend'
old_lu = 'jiuwudaishi-006-luyanchang'
new_baixiang = 'xinwudaishi-025-baxiang'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0910-p035-p043',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-04/sources/library' / main1, '9708b0c5', '司马光等'),
    (main2, P / 'sources/library' / main2, '7674c2cb', '司马光等'),
    (old_lu, P / 'sources/library' / old_lu, '7674c2cb', '薛居正等'),
    (new_baixiang, P / 'sources/library' / new_baixiang, '7674c2cb', '欧阳修'),
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
primary_texts = {key: (source_dirs[key] / 'source.txt').read_text() for key in (main1, main2)}
for n in range(35, 44):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in primary_texts[main1 if n <= 41 else main2], n

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
           '王景仁':'王茂章','李存审':'符存审','宋鄴':'宋邺','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1, main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1, main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷267·开平四年（910）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_267_0910_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1, main2):
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
                   description=f'《资治通鉴》卷267开平四年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=910):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_267_0910_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '910年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_267_0910_' + code + '_' + pk
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

event('lu_guangchou_succession', '卢光稠病逝，谭全播奉立卢延昌', 35,
      '虔州刺史卢光稠疾病，欲以位授谭全播，全播不受。光稠卒，其子韶州刺史延昌来奔丧，全播立而事之。',
      [('卢光稠','病逝的虔州刺史'),('谭全播','辞让并奉立卢延昌'),('卢延昌','回虔州奔丧并承位')],
      when='910年本段条；确日未载',place='虔州',note='卢延昌在已发布段落中为卢光稠之子；原文以“延昌”省姓。')
event('lu_yanchang_wu_liang', '卢延昌接受吴官并经马殷向梁密表', 35,
      '吴遣使拜延昌虔州刺史，延昌受之，亦因楚王殷通密表于梁，曰：“我受淮南官，以缓其谋耳，必为朝廷经略江西。”',
      [('卢延昌','接受吴官并向梁密表'),('马殷','传递卢延昌给梁的密表')],
      when='910年卢光稠卒后；确日未载',place='虔州、楚、梁',note='密表内容是卢延昌向梁自陈意图，不将其视为已执行的江西攻略。')
event('lu_yanchang_liang_appointment', '后梁授卢延昌镇南留后', 35,
      '丙寅，以延昌为镇南留后。', [('卢延昌','获后梁授镇南留后')],
      when='910年丙寅',place='镇南',note='《旧五代史》卷六于翌年二月附近追述相关表奏与任命，日期并列待考。')
event('liao_shuang_shaozhou', '卢延昌奏廖爽为韶州刺史', 35,
      '延昌表其将廖爽为韶州刺史，爽，赣人也。',
      [('卢延昌','奏请任命其将廖爽'),('廖爽','获奏为韶州刺史')],
      when='910年丙寅后；确日未载',place='韶州',note='只记“表”为奏请，不推成已经到任。')
event('yan_keqiu_xingan', '严可求在新淦置制置使并渐增戍兵以图虔州', 35,
      '吴淮南节度判官严可求请置制置使于新淦县，遣兵戍之，以图虔州。每更代，辄潜益其兵，虔人不之觉也。',
      [('严可求','请置制置使并增驻军的吴官')],
      when='910年本段条；持续增兵，起止未详',place='新淦县',note='“以图虔州”为吴方计划；本段未记吴军已取得虔州。')
claim('event','event_zztj_267_0910_lu_yanchang_liang_appointment','description',
      '《旧五代史》卷六追述卢延昌经马殷上表、梁帝授镇南留后。',35,
      '尋兼授鎮南將軍節度使觀察留後，命使慰勞。',
      '此为旧史翌年二月附近的追叙，不能直接改写《通鉴》丙寅日期。',old_lu,'adds')

event('shu_chancellors', '王建授周庠、庾传素同平章事', 36,
      '庚午，蜀主以御史中丞周庠、户部侍郎判度支庾传素并为中书侍郎、同平章事。',
      [('王建','任命两位宰相的蜀主'),('周庠','获任中书侍郎、同平章事'),('庾传素','获任中书侍郎、同平章事')],
      when='910年庚午',place='前蜀')
event('liang_law_code', '李燕等刊定《梁律令格式》并施行', 37,
      '太常卿李燕等刊定《梁律令格式》，癸酉，行之。',
      [('李燕','参与刊定梁律令格式的太常卿')],when='910年癸酉施行',place='后梁',
      note='“等”表示另有未列名参与者；不补造姓名。')
event('liang_baixiang_advance', '王茂章（王景仁）等率梁军进柏乡', 38,
      '丁丑，王景仁等进军柏乡。', [('王景仁','率梁军进柏乡的将领')],
      when='910年丁丑',place='柏乡',note='王景仁与王茂章复用同一已校人物；此时尚未发生柏乡决战。')
event('shu_yongping_decree', '前蜀大赦并宣布翌年改元永平', 39,
      '辛巳，蜀大赦，改明年元曰永平。',
      [('王建','前蜀君主；本段记大赦及翌年改元')],
      when='910年辛巳；改元自翌年起',place='前蜀',note='永平是翌年元号，不将910年标为永平元年。')

event('jin_king_comes_to_zhao', '王镕再求晋援，李存勖由赞皇东下并会周德威', 40,
      '赵王镕复告急于晋，晋王以蕃汉副总管李存审守晋阳，自将兵自赞皇东下，王处直遣将将兵五千以从。辛巳，晋王至赵州，与周德威合',
      [('王镕','再次向晋告急的赵王'),('李存勖','率晋军自赞皇东下的晋王'),('李存审','留守晋阳的蕃汉副总管'),('王处直','遣五千兵随晋军'),('周德威','在赵州与晋王会合')],
      when='910年辛巳到赵州；此前东下',place='晋阳、赞皇、赵州',
      note='李存审据旧五代史其子请复符姓记载，与既有人物符存审同人；五千为王处直所遣兵数。')
event('jin_captures_liang_foragers', '晋军俘梁刍荛者二百并送赵', 40,
      '获梁刍荛者二百人，问之曰：“初发洛阳，梁主有何号令？”对曰：“梁主戒上将云：‘镇州反覆，终为子孙之患。今悉以精兵付汝，镇州虽以铁为城，必为我取之。’”晋王命送于赵。',
      [('李存勖','讯问并将被俘梁人送往赵')],when='910年辛巳',place='赵州',
      note='所谓梁主命令出于被俘刍荛者答语，标为俘虏证言，不直接当作梁廷诏令。')
event('jin_challenges_liang', '晋军在柏乡附近两次挑战梁军', 40,
      '壬午，晋王进军，距柏乡三十里，遣周德威等以胡骑迫梁营挑战，梁兵不出。癸未，复进，距柏乡五里，营于野河之北，又遣胡骑迫梁营驰射，且诟之。',
      [('李存勖','率军进至柏乡附近'),('周德威','率胡骑挑战梁营')],
      when='910年壬午、癸未',place='柏乡、野河以北',note='先距柏乡三十里，次日进至五里；不把两次挑战合并成同日决战。')
event('zhou_dewei_flank_skirmish', '韩勍率梁兵追击，周德威袭两翼俘百余人', 40,
      '梁将韩勍等将步骑三万，分三道追之，铠胄皆被缯绮，镂金银，光彩炫耀，晋人望之夺气。周德威谓李存璋曰：“梁人志不在战，徒欲曜兵耳。不挫其锐，则吾军不振。”',
      [('韩勍','率梁步骑三万追击的将领'),('周德威','判断梁军耀兵并决定反击'),('李存璋','听周德威陈述的晋将')],
      when='910年癸未',place='野河附近',note='三万为梁军步骑规模；“志不在战”是周德威判断。')
claim('event','event_zztj_267_0910_zhou_dewei_flank_skirmish','description',
      '周德威以精骑袭梁军两端，俘百余人后双方退兵。',40,
      '德威自帅精骑千馀击其两端，左驰右突，出入数四，俘获百馀人，且战且却，距野河而止。梁兵亦退。',
      '此为当日接战，不提前录入翌年柏乡决战结果。')
claim('event','event_zztj_267_0910_jin_challenges_liang','description',
      '《新五代史》卷二十五亦述晋王出赞皇、进距柏乡五里、营野河北。',40,
      '莊宗自將出贊皇，會德威于石橋，進距柏鄉五里，營于野河北。',
      '新史记会师地点为石桥，主书记赵州；视为地点描述差异，不强定同处。',new_baixiang,'corroborates')

event('zhou_dewei_advises_retreat', '周德威劝李存勖缓战，转请张承业进言', 41,
      '德威言于晋王曰：“贼势甚盛，宜按兵以待其衰。”王曰：“吾孤军远来，救人之急，三镇乌合，利于速战，公乃欲按兵持重，何也？”',
      [('周德威','劝晋王缓战'),('李存勖','初主张速战的晋王')],
      when='910年癸未后；确日未载',place='野河附近',note='双方争论为战策，不把“速战”当作已实行。')
claim('event','event_zztj_267_0910_zhou_dewei_advises_retreat','description',
      '周德威进一步劝张承业进言，拟退高邑诱梁军离营。',41,
      '不若退军高邑，诱贼离营，彼出则归，彼归则出，别以轻骑掠其馈饷，不过逾月，破之必矣。',
      '“破之必矣”为周德威的预期而非当日战果。')
event('jin_retires_gaoyi', '晋王听周德威之议，撤营退保高邑', 41,
      '时梁兵闭垒不出，有降者，诘之，曰：“景仁方多造浮桥。”王谓德威曰：“果如公言。”是日，拔营，退保高邑。',
      [('李存勖','同意撤营退保高邑'),('周德威','主张退保高邑的晋将')],
      when='910年癸未后当日；确日未载',place='野河、高邑',
      note='造浮桥出自降者口供；主书载晋军据此撤退，未断言桥已建成。')
claim('event','event_zztj_267_0910_jin_retires_gaoyi','description',
      '《新五代史》卷二十五也记经张承业劝说后晋军退鄗邑。',41,
      '乃退軍鄗邑。',
      '新史用鄗邑，主书用高邑；保留史载地名差异，未核现代地理。',new_baixiang,'corroborates')

event('chu_southwest_raids', '宋邺、潘金盛分别寇湘乡、武冈', 42,
      '至是，鄴寇湘乡，金盛寇武冈',
      [('宋鄴','寇湘乡的辰州酋长'),('潘金盛','寇武冈的溆州酋长')],
      when='910年本段条；确日未载',place='湘乡、武冈',note='宋鄴规范简体名为宋邺，原文保留鄴；未断言二人同地合兵。')
event('ma_yin_sends_lu_shizhou', '马殷遣吕师周率衡山兵五千讨宋邺、潘金盛', 42,
      '楚王殷遣昭州刺史吕师周将衡山兵五千讨之。',
      [('马殷','遣将讨伐的楚王'),('吕师周','率衡山兵五千出讨的昭州刺史')],
      when='910年本段条；确日未载',place='衡山、湘乡、武冈',note='只记发兵，不提前记翌年讨平结果。')

# 第43段先叙黄巢时期与刘隐据岭南以来的背景，均不得误定为910年。
event('pang_liu_tang_background', '庞巨昭、刘昌鲁在黄巢南侵时守容州、高州', 43,
      '黄巢之寇岭南也，巨昭为容管观察使，昌鲁为高州刺史，帅群蛮据险以拒之，巢众不敢入境。',
      [('庞巨昭','黄巢南侵时守容州'),('刘昌鲁','黄巢南侵时守高州')],
      when='黄巢南侵岭南时；确年本段未载',place='容州、高州',year=None,
      note='追叙唐代旧事，不能直接标成910年。')
event('tang_ningyuan_command', '唐廷在容州置宁远军并任庞巨昭、刘昌鲁', 43,
      '唐嘉其功，置宁远军于容州，以巨昭为节度使，以昌鲁为高州防御使。',
      [('庞巨昭','获任宁远节度使'),('刘昌鲁','获任高州防御使')],
      when='唐廷嘉奖拒黄巢之后；确年未载',place='容州、高州',year=None)
event('liu_yin_southern_failed_attacks', '刘隐据岭南后，其弟刘岩攻高州、容州未克', 43,
      '及刘隐据岭南，二州不从；隐遣弟岩攻高州，昌鲁大破之，又攻容州，亦不克。',
      [('刘隐','据岭南并遣弟攻两州'),('刘岩','攻高州与容州的刘隐之弟'),('刘昌鲁','击败刘岩攻高州之兵'),('庞巨昭','守容州未被攻克')],
      when='刘隐据岭南后、910年归楚之前；确年未载',place='高州、容州',year=None,
      note='追叙背景未标确年；不能因其在910段落出现而强定910年。')
event('liu_changlu_seeks_chu', '刘昌鲁致书归楚，马殷遣姚彦章迎接', 43,
      '昌鲁自度终非隐敌，是岁，致书请自归于楚。楚王殷大喜，遣横州刺史姚彦章将兵迎之。',
      [('刘昌鲁','致书请求归楚'),('马殷','派姚彦章迎接刘昌鲁'),('姚彦章','率兵赴容州、高州迎接')],
      when='910年是岁；确日未载',place='高州、楚',note='“是岁”明指本年，此后动作按叙事次序录入。')
event('mo_yanzhao_plot_executed', '莫彦昭建议伏击楚军，庞巨昭拒绝并杀莫彦昭', 43,
      '裨将莫彦昭说巨昭曰：“湖南兵远来疲乏，宜撤储偫，弃城，潜于山谷以待之。彼必入城，我以全军掩之，彼外无继援，可擒也。”巨昭曰：“马氏方兴，今虽胜之，后将何如！不若具牛酒迎之。”彦昭不从，巨昭杀之，举州迎降。',
      [('庞巨昭','拒伏击方案、杀莫彦昭并率州降楚'),('莫彦昭','提出伏击方案、被庞巨昭杀')],
      when='910年姚彦章至容州时；确日未载',place='容州',
      note='计策未被执行；不将楚军记为遭伏击。')
event('chu_south_generals_return', '姚彦章至高州并护送庞、刘族属及兵士归长沙', 43,
      '彦章进至高州，以兵援送巨昭、昌鲁之族及士卒千馀人归长沙。',
      [('姚彦章','率楚军护送人员'),('庞巨昭','其族属随楚军返长沙'),('刘昌鲁','其族属随楚军返长沙')],
      when='910年容州归楚后；确日未载',place='高州、长沙',note='千余为士卒数，未加计族属人数。')
event('chu_southern_appointments', '马殷任姚彦章知容州、刘昌鲁永顺军副使', 43,
      '楚王殷以彦章知容州事，以昌鲁为永顺节度副使。',
      [('马殷','授姚彦章、刘昌鲁职任'),('姚彦章','获命知容州事'),('刘昌鲁','获命永顺节度副使')],
      when='910年容州归楚后；确日未载',place='容州、楚',
      note='只记所授职任，不推定刘昌鲁已转赴永顺治所。')
# 明示的亲属关系均指向同一稳定人物。
person('卢光稠',35,'卢延昌之父','光稠卒，其子韶州刺史延昌来奔丧')
person('卢延昌',35,'卢光稠之子','光稠卒，其子韶州刺史延昌来奔丧')
if 'relationship_person_卢光稠_person_卢延昌_父亲' not in existing_relation_keys:
    relation('卢光稠','卢延昌','父亲',35,'光稠卒，其子韶州刺史延昌来奔丧','原文其子明指卢延昌。')
relation('刘隐','刘岩','兄长',43,'隐遣弟岩攻高州','原文“弟岩”明示刘隐为刘岩之兄。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(35, 44):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷267开平四年第35—43段连续处理；910年事与唐代追叙分开，柏乡战果不前置。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=267, year=910,
    primary_source_key=main1, primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(35,44)],next_paragraph='zztj-v267-y0911-p001',
    coverage='卷267开平四年第35—43段，虔州、前蜀任命、柏乡前哨、楚西南及容高归楚。',
    supplements=supplements,status=status,
    textual_reviews=[{'paragraph_id':Q[35]['id'],'note':'旧五代史卷六在翌年二月附近回溯卢延昌表奏与梁任命；主书丙寅时间保留，确切互校待纸本。'},
                     {'paragraph_id':Q[40]['id'],'note':'李存审与既有符存审按旧五代史卷三十八其子请复符姓之记复用；新五代史卷二十五会师石桥，主书作赵州。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({key:len(value) for key,value in B.items() if isinstance(value,list)})
