"""Curate Tongjian 262, year 901, consecutive paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 56))
primary_prev = 'tongjian-262-901-spring'
primary = 'tongjian-262-901-feb-apr'
old_tang = 'jiutangshu-020-901-restoration'
old_five = 'jiuwudaishi-002-901-hezhong-taiyuan'
new_five = 'xinwudaishi-004-901-jin'

B = {'format_version': 1, 'batch_key': 'zztj-v262-y0901-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent / 'part-01/sources/library' / primary_prev, '7b68833', '司马光等'),
    (primary, P / 'sources/library' / primary, '0e8e093', '司马光等'),
    (old_tang, P.parent / 'part-01/sources/library' / old_tang, '7b68833', '刘昫等'),
    (old_five, P / 'sources/library' / old_five, '0e8e093', '薛居正等'),
    (new_five, P / 'sources/library' / new_five, '0e8e093', '欧阳修'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_prev, primary)}
for n in range(9, 17):
    assert Q[n]['text'] in ''.join(primary_texts.values()), (n, Q[n]['text'][:30])

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and Q[n]['text'] in data)

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0901_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·天复元年（901）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷262天复元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=901):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_262_0901_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '901年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '901年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role)
        edge = 'participation_zztj_262_0901_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0901_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 9: troops left at court. Cui's prediction and Han's warning remain attributed speech.
event('li_maozhen_returns_fengxiang', '李茂贞辞朝还镇', 9, '李茂贞辞还镇。',
      [('李茂贞', '辞朝还镇者')], when='901年正月后；确日未载', place='凤翔镇')
event('cui_requests_fengxiang_guards', '崔胤请留凤翔兵三千宿卫京师', 9,
      '讽茂贞留兵三千于京师，充宿卫，以茂贞假子继筠将之。',
      [('崔胤', '劝留兵者'), ('李茂贞', '被劝留兵者'), ('李继筠', '拟统留兵者')],
      when='901年李茂贞辞还镇时', place='京师',
      note='三千是崔胤所求驻兵；假子明确为李茂贞之假子，未据此推定正式收养仪式。')
event('han_wo_opposes_guards', '韩偓反对留凤翔兵，崔胤不从', 9,
      '偓曰：“留此兵则家国两危，不留则家国两安。”胤不从。',
      [('韩偓', '劝谏反对者'), ('崔胤', '未采纳者')], when='901年议京师宿卫时',
      note='两危两安为韩偓的判断，不作后来危机已发生的事实。')

# 10: campaign and the letters, recorded without adopting their accusations as fact.
event('zhu_plans_hezhong', '朱全忠议攻河中以制河东', 10,
      '硃全忠既服河北，欲先取河中以制河东。己亥，召诸将谓曰',
      [('朱温', '议攻河中者')], when='901年正月己亥', place='河中',
      note='“欲”与议兵为意图，不写己亥已占河中。')
event('zhang_crosses_river', '张存敬率三万兵渡河袭河中', 10,
      '庚子，遣张存敬将兵三万自汜水度河出舍山路以袭之，全忠以中军继其后。',
      [('张存敬', '前锋统兵者'), ('朱温', '中军继进者')], when='901年正月庚子', place='汜水、舍山路',
      note='三万仅指张存敬所将，不外推朱中军兵数。')
event('zhang_reaches_jiang', '张存敬到绛州', 10, '戊申，存敬至绛州。',
      [('张存敬', '到绛州者')], when='901年正月戊申', place='绛州')
event('tao_surrenders_jiang', '绛州刺史陶建钊降张存敬', 10, '庚戌，绛州刺史陶建钊降之；',
      [('陶建钊', '降者'), ('张存敬', '受降者')], when='901年正月庚戌', place='绛州',
      note='旧五代史作戊申攻下绛州，与主书庚戌陶降并列，不强合为同日。')
event('zhang_hanyu_surrenders_jin', '晋州刺史张汉瑜降张存敬', 10, '壬子，晋州刺史张汉瑜降之。',
      [('张汉瑜', '降者'), ('张存敬', '受降者')], when='901年正月壬子', place='晋州')
event('zhu_blocks_jin_jiang', '朱全忠以侯言何絪守晋绛扼河东援路', 10,
      '全忠遣其将侯言守晋州，何絪守绛州，屯兵二万以扼河东援兵之路。',
      [('朱温', '遣守军者'), ('侯言', '守晋州者'), ('何絪', '守绛州者')],
      when='901年晋绛降后', place='晋州、绛州', note='二万为两州扼援兵合叙，未分配到各将。')
event('court_mediates_zhu_refuses', '朝廷赐诏和解朱全忠，朱不从', 10,
      '朝廷恐全忠西入关，急赐诏和解之；全忠不从。',
      [('朱温', '拒和者'), ('李杰', '朝廷赐诏之君')], when='901年河中战事期间',
      note='朝廷所恐为原文所述原因；不写朱已西入关。')
event('wang_ke_asks_li_keyong', '王珂遣间使向李克用告急，援军不得进', 10,
      '珂遣间使告急于李克用，道路相继，克用以汴人先据晋、绛，兵不得进。',
      [('王珂', '求援者'), ('李克用', '未能进兵者')], when='901年晋绛被占后', place='河中、河东',
      note='求援与兵不得进分明，不写李克用不愿营救。')
event('wang_ke_wife_pleads', '王珂妻致书李克用求救，李劝举族归朝', 10,
      '珂妻遗克用书曰：“儿旦暮为俘虏，大人何忍不救！”克用报曰：“今贼兵塞晋、绛，众寡不敌，进则与汝两亡，不若与王郎举族归朝。”',
      [('王珂', '被劝归朝者'), ('李克用', '回书劝归朝者')], when='901年河中受攻时',
      note='妻氏未具名，不造人物；贼兵、众寡、两亡均属双方信中措辞。')
event('wang_ke_asks_li_maozhen', '王珂致书李茂贞求援并愿让河中，李不报', 10,
      '珂又遗李茂贞书，言：“天子新返正，诏籓镇无得相攻',
      [('王珂', '致书求援者'), ('李茂贞', '未回书者')], when='901年河中受攻时',
      note='河中请公有之是王珂书中的让地提议；未发生实际交割。')

# 11–12: February siege, capitulation, and later uncertain death.
event('li_sizhao_takes_zezhou', '李嗣昭攻取泽州', 11, '二月，甲寅朔，河东将李嗣昭攻泽州，拔之。',
      [('李嗣昭', '攻取泽州者')], when='901年二月甲寅朔', place='泽州')
event('zhang_marches_hezhong', '张存敬自晋州进围河中', 12,
      '乙卯，张存敬引兵发晋州；己未，至河中，遂围之。',
      [('张存敬', '围河中者')], when='901年二月乙卯出发、己未围城', place='河中')
event('wang_ke_flight_fails', '王珂欲率族渡河奔京师，因浮梁坏与守者不应未果', 12,
      '会浮梁坏，流澌塞河，舟行甚难，珂挈其族数百人欲夜登舟，亲谕守城者，皆不应。',
      [('王珂', '欲渡河奔京师者')], when='901年二月河中被围后', place='河中',
      note='数百人是王珂携族规模；奔京师属计划，未据此写实际逃出。')
event('liu_xun_advises_submission', '牙将刘训劝王珂先向张存敬送款', 12,
      '不若且送款存敬，徐图向背。”珂从之。',
      [('刘训', '劝送款者'), ('王珂', '从议者')], when='901年二月河中被围后', place='河中',
      note='保留刘训建议与王珂采纳，不把“徐图向背”当后续既定计划。')
event('wang_ke_offers_surrender', '王珂白幡牌印请降，要求待朱全忠至再交城', 12,
      '壬戌，珂植白幡于城隅，遣使以牌印请降于存敬。存敬请开城，珂曰：“吾于硃公有家世事分，请公退舍，俟硃公至，吾自以城授之。”存敬从之',
      [('王珂', '请降并求待朱至者'), ('张存敬', '受降并应允者')],
      when='901年二月壬戌', place='河中', note='请降先于朱到城，未写张存敬当日入城。')
event('zhu_arrives_luoyang', '朱全忠到洛阳闻河中请降', 12,
      '乙丑，全忠至洛阳，闻之喜，驰往赴之。',
      [('朱温', '闻降驰往者')], when='901年二月乙丑', place='洛阳')
event('zhu_mourns_wang_chongrong', '朱全忠至虞乡祭王重荣墓', 12,
      '戊辰，至虞乡，先哭于重荣之墓，尽哀；河中人皆悦。',
      [('朱温', '祭墓者'), ('王重荣', '墓主')], when='901年二月戊辰', place='虞乡',
      note='墓主王重荣为既有人物；旧五代史有庚午到河中、六月丁卯再拜墓之记，分事分日保留。')
event('zhu_accepts_hezhong', '朱全忠止王珂面缚之礼并同入河中', 12,
      '乃以常礼出迎，握手歔欷，联辔入城。',
      [('朱温', '受降入城者'), ('王珂', '以常礼迎者')], when='901年二月戊辰后；确日未另载', place='河中',
      note='王珂拟面缚牵羊而被朱阻止，实际以常礼迎接。')
event('zhang_huguo_and_wang_moved', '朱全忠表张存敬留后，迁王珂举族至大梁', 12,
      '全忠表张存敬为护国军留后，王珂举族迁于大梁。',
      [('朱温', '上表并迁王珂者'), ('张存敬', '被表护国军留后者'), ('王珂', '举族迁大梁者')],
      when='901年河中降后；确日未载', place='河中、大梁',
      note='上表任命与迁徙同句，未推上表当天已获朝廷批准。')
event('wang_ke_later_killed', '朱全忠后来遣人于华州杀王珂', 12,
      '其后全忠遣珂入朝，遣人杀之于华州。',
      [('朱温', '遣人杀王珂者'), ('王珂', '在华州被杀者')],
      when='其后；确年未载', place='华州', year=None,
      note='“其后”跨越本年条，不能定为901年；旧五代史本段未述死期。')
claim('person', people['王珂'], 'death_year', '王珂其后在华州被朱全忠遣人杀害，确年未载。', 12,
      '其后全忠遣珂入朝，遣人杀之于华州。', '死亡事实可据，死亡年份未知，不写901。')
event('zhu_returns_for_zhang_illness', '朱全忠闻张夫人病急自河中东归', 12,
      '全忠闻张夫人疾亟，遽自河中东归。', [('朱温', '东归者')],
      when='901年河中降后', place='河中至大梁', note='张夫人本段未具名，不引入未核身份。')
event('li_keyong_asks_peace_zhu_decides_attack', '李克用遣使请和，朱全忠回使后决意攻河东', 12,
      '李克用遣使以重币请修好于全忠；全忠虽遣使报之，而忿其书辞蹇傲，决欲攻之。',
      [('李克用', '遣使请和者'), ('朱温', '回使而决攻者')],
      when='901年河中降后', note='书辞蹇傲是朱全忠的评价；旧五代史补使者张特，主书未具名。')

# 13–15: appointments and remembrance.
event('wang_pu_chancellor', '王溥任中书侍郎同平章事', 13,
      '以翰林学士、户部侍郎王溥为中书侍郎、同平章事。',
      [('王溥', '受任者')], when='901年二月后；确日未载')
event('pei_shu_chancellor', '裴枢任户部侍郎同平章事', 13,
      '以吏部侍郎裴枢为户部侍郎、同平章事。',
      [('裴枢', '受任者')], when='901年二月后；确日未载')
event('cui_recommends_wang_pu', '崔胤引荐旧幕府王溥', 13,
      '溥，正雅之从孙也，常在崔胤幕府，故胤引之。',
      [('王溥', '受引荐者'), ('崔胤', '引荐者')], when='901年王溥入相时；确日未载',
      note='“从孙”仅保留文字说明，不换算为父子关系；在幕府任职不推政治盟约。')
event('li_yi_posthumous_title', '故睦王李倚追赠谥恭哀太子', 14,
      '赠谥故睦王倚曰恭哀太子。', [('李倚', '获追谥者')],
      when='901年二月后；确日未载', note='故表明已故；恭哀太子是追赠谥，不写重新立为在世太子。')
event('liu_rengong_shizhong', '刘仁恭加兼侍中', 15,
      '加幽州节度使刘仁恭、魏博节度使罗绍威并兼侍中。',
      [('刘仁恭', '加兼侍中者')], when='901年二月后；确日未载', place='幽州')
event('luo_shaowei_shizhong', '罗绍威加兼侍中', 15,
      '加幽州节度使刘仁恭、魏博节度使罗绍威并兼侍中。',
      [('罗绍威', '加兼侍中者')], when='901年二月后；确日未载', place='魏博')

# 16: six approach routes and dated falls, preserving March/April boundary.
event('zhu_returns_daliang_march', '朱全忠三月朔至大梁', 16,
      '三月，癸未朔，硃全忠至大梁。', [('朱温', '返回大梁者')],
      when='901年三月癸未朔', place='大梁')
routes = [
 ('shu_taixing','氏叔琮等领军由太行攻李克用','遣氏叔琮等将兵五万攻李克用，入自太行', [('朱温','遣兵者'),('氏叔琮','领军由太行入者'),('李克用','受攻方')], '太行'),
 ('zhang_xinkou','张文恭由磁州新口入','魏博都将张文恭入自磁州新口',[('张文恭','由磁州新口入者')],'磁州新口'),
 ('ge_tumen','葛从周会成德兵由土门入','葛从周以兗、郓兵会成德兵入自土门',[('葛从周','率兗郓兵由土门入者')],'土门'),
 ('zhang_maling','张归厚由马岭入','洺州刺史张归厚入自马岭',[('张归厚','由马岭入者')],'马岭'),
 ('wang_feihu','王处直由飞狐入','义武节度使王处直入自飞狐',[('王处直','由飞狐入者')],'飞狐'),
 ('hou_yindi','侯言由阴地入','权知晋州侯言以慈、隰、晋、绛兵入自阴地',[('侯言','率兵由阴地入者')],'阴地'),
]
for code,title,quote,actors,place in routes:
    event(code,title,16,quote,actors,when='901年三月癸卯出兵；各路到达日未载',place=place,
          note='原文六路依次分录；五万为氏叔琮等所将总述，不逐路分摊。')
event('shu_enters_tianjing', '氏叔琮入天井关进军昂车', 16,
      '叔琮入天井关，进军昂车。', [('氏叔琮','进军者')],
      when='901年三月癸卯后',place='天井关、昂车')
event('cai_xun_surrenders_qin', '沁州刺史蔡训以城降', 16,
      '辛亥，沁州刺史蔡训以城降。', [('蔡训','举城降者')],
      when='901年三月辛亥',place='沁州')
event('gai_zhang_surrenders_qin', '盖璋降侯言并权知沁州', 16,
      '河东都将盖璋诣侯言降，即令权知沁州。',
      [('盖璋','降侯言并权知沁州者'),('侯言','受降者')],
      when='901年三月辛亥后；确日未载',place='沁州')
event('shu_takes_zezhou', '氏叔琮拔泽州，李存璋弃城', 16,
      '壬子，叔琮拔泽州，刺史李存璋弃城走。',
      [('氏叔琮','攻取者'),('李存璋','弃城者')],when='901年三月壬子',place='泽州')
event('meng_qian_surrenders_luzhou', '氏叔琮攻潞州，孟迁降', 16,
      '叔琮进攻潞州，昭义节度使孟迁降之。',
      [('氏叔琮','攻潞州者'),('孟迁','降者')],when='901年三月壬子后',place='潞州')
event('li_shenjian_wang_zhou_surrender', '李审建王周率步骑降氏叔琮', 16,
      '河东屯将李审建、王周将步军一万、骑二千诣督琮降。',
      [('李审建','率军降者'),('王周','率军降者'),('氏叔琮','受降者')],
      when='901年三月潞州降后',place='潞州附近',
      note='底本文字“督琮”疑“叔琮”，保留原字并据同段前后主语识别；步一万骑二千为两将合叙。')
event('shu_advances_jinyang', '氏叔琮进趋晋阳', 16,
      '叔琮进趣晋阳。', [('氏叔琮','进军者')],when='901年三月潞州降后',place='晋阳')
event('shu_camps_dongwo', '氏叔琮四月出石会关营洞涡驿',16,
      '夏，四月，乙卯，叔琮出石会关，营于洞涡驿。',
      [('氏叔琮','出关设营者')],when='901年四月乙卯',place='石会关、洞涡驿')
event('zhang_e_surrenders_liaozhou', '张归厚至辽州，刺史张鄂降',16,
      '张归厚引兵至辽州，丁巳，辽州刺史张鄂降。',
      [('张归厚','率兵至辽州者'),('张鄂','降者')],when='901年四月丁巳',place='辽州')
event('bai_fengguo_takes_chengtian', '白奉国会成德兵取承天军',16,
      '别将白奉国会成德兵自井陉入，己未，拔承天军，与叔琮烽火相应。',
      [('白奉国','会师并攻取者'),('氏叔琮','烽火相应者')],
      when='901年四月己未',place='井陉、承天军')

# Supplement only the same subjects; preserve differences in readings.
extra(old_tang,'event','event_zztj_262_0901_zhang_crosses_river','description',
      '《旧唐书》本纪记朱全忠遣张存敬三万人攻河中。',
      '全忠令大將張存敬率兵三萬，由含山襲河中王珂',10,'corroborates','与主书兵数相合；旧唐本纪为节略记载。')
extra(old_five,'event','event_zztj_262_0901_tao_surrenders_jiang','time_original',
      '《旧五代史》记戊申攻下绛州；《通鉴》记戊申到绛州、庚戌陶建钊降。',
      '戊申，攻下絳州。',10,'conflicts','攻下与刺史降或为阶段不同，日期不同，不强并。')
extra(old_five,'event','event_zztj_262_0901_li_keyong_asks_peace_zhu_decides_attack','description',
      '《旧五代史》补请和使者为牙将张特。',
      '是月，李克用遣牙將張特來聘，請尋舊好',12,'adds','主书仅记遣使；旧五补姓名，暂不另建缺少主书身份核对的人物。')
extra(old_five,'event','event_zztj_262_0901_shu_taixing','description',
      '《旧五代史》并列贺德伦与氏叔琮领大军攻太原。',
      '遣大將賀德倫、氏叔琮領大軍以伐太原',16,'adds','主书称氏叔琮等，旧五补列贺德伦。')
extra(old_five,'event','event_zztj_262_0901_zhang_xinkou','description',
      '《旧五代史》同记张文恭由磁州新口入。',
      '魏博都將張文恭自磁州新口入',16,'corroborates','与主书路线同。')
extra(new_five,'event','event_zztj_262_0901_zhang_xinkou','description',
      '《新五代史》作张文敬入新口，主书及旧五作张文恭。',
      '張文敬入新口',16,'conflicts','姓名异文并列，不径作同人别名。')
extra(new_five,'event','event_zztj_262_0901_shu_taixing','time_original',
      '《新五代史》于四月叙多路入晋，主书三月癸卯遣兵、四月续进。',
      '四月，氏叔琮入天井',16,'conflicts','可能叙发兵与入境阶段有别，不把所有进军归一日。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9, 17):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='第9—16段连续校核：京师留兵、河中攻降、两相任用及三四月六路攻晋。书信为当事人主张；王珂“其后”被杀确年未定；旧五与新五攻绛日期、张文恭/文敬异文并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=262, year=901,
    primary_source_key=primary_prev, primary_source_keys=[primary_prev, primary],
    paragraphs=[Q[n]['id'] for n in range(9, 17)], next_paragraph=Q[17]['id'],
    coverage='天复元年55段中的第9—16段连续处理；本年尚未完成。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
