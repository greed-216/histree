"""Curate Tongjian 265, year 905, consecutive paragraphs 53–60."""
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
primary_winter = 'tongjian-265-905-winter'
primary_transition = 'tongjian-265-905-yearend-transition'
primary_yearend = 'tongjian-265-905-yearend'
old_november = 'jiutangshu-020-905-november'
old_dec_early = 'jiutangshu-020-905-december-early'
old_dec_late = 'jiutangshu-020-905-december-late'
new_tang_succession = 'xintangshu-010-yangxingmi-succession'
new_five_yearend = 'xinwudaishi-001-905-yearend'
new_yangwo = 'xinwudaishi-061-yangwo-succession'
new_kong_dispute = 'xinwudaishi-043-kongxun-dispute'
new_wang_dispute = 'xinwudaishi-043-wangyin-dispute'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p053-p060',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_winter, P.parent / 'part-07/sources/library' / primary_winter, '9d94d70f', '司马光等'),
    (primary_transition, P / 'sources/library' / primary_transition, '0ca5e91a', '司马光等'),
    (primary_yearend, P / 'sources/library' / primary_yearend, '49e7efb9', '司马光等'),
    (old_november, P.parent / 'part-08/sources/library' / old_november, '4525bafe', '刘昫等'),
    (old_dec_early, P / 'sources/library' / old_dec_early, '49e7efb9', '刘昫等'),
    (old_dec_late, P / 'sources/library' / old_dec_late, '49e7efb9', '刘昫等'),
    (new_tang_succession, P / 'sources/library' / new_tang_succession, '49e7efb9', '欧阳修等'),
    (new_five_yearend, P / 'sources/library' / new_five_yearend, '49e7efb9', '欧阳修等'),
    (new_yangwo, P.parent / 'part-07/sources/library' / new_yangwo, '9d94d70f', '欧阳修等'),
    (new_kong_dispute, P.parent / 'part-08/sources/library' / new_kong_dispute, '4525bafe', '欧阳修等'),
    (new_wang_dispute, P.parent / 'part-08/sources/library' / new_wang_dispute, '4525bafe', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_winter, primary_transition, primary_yearend)}
for n in range(53, 61):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '殷衡':'孔循', '赵殷衡':'孔循', '玄晖':'蒋玄晖', '璨':'柳璨', '渥':'杨渥', '行密':'杨行密', '何太后':'何氏（唐昭宗皇后）', '太后':'何氏（唐昭宗皇后）', '后':'何氏（唐昭宗皇后）', '行袭':'冯行袭', '硃建武':'朱建武'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_09_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐二年（905）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   aliases=['硃建武'] if canonical == '朱建武' else [], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=905, time_quote=None):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0905_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '905年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '905年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0905_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0905_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 53: Death and succession petition are separate actions.
event('yang_xingmi_dies', '吴武忠王杨行密庚辰去世', 53,
      '庚辰，吴武忠王杨行密薨', [('杨行密', '去世者')],
      when='905年十一月庚辰', place='淮南',
      note='杨行密卒日见主书；不把杨渥授任或即位并入死亡事件。')
event('generals_request_yang_wo_titles', '淮南将佐请李俨承制授杨渥节度使等职', 53,
      '将佐共请宣谕使李俨承制授杨渥淮南节度使、东南诸道行营都统，兼侍中、弘农郡王。',
      [('李俨', '被请求承制授职的宣谕使'), ('杨渥', '拟受诸职者')],
      when='905年十一月庚辰杨行密薨后', place='淮南',
      note='原文是将佐共请李俨承制授职；不把“请”直接写成已完成正式任命。')

# 54: Proposed rites, decrees, refusals, denunciations, and killings have distinct agency.
event('liu_jiang_discuss_nine_bestowals', '柳璨与蒋玄晖再议加朱全忠九锡', 54,
      '柳璨、蒋玄晖等议加硃全忠九锡',
      [('柳璨', '议加九锡者'), ('蒋玄晖', '议加九锡者'), ('朱温', '拟受九锡者')],
      when='905年十一月辛巳前；确日未载',
      note='此处为继续议礼，与前批追叙方案相关，不等于九锡已经受领。')
event('su_xun_urges_abdication', '苏循公开主张朝廷向朱全忠禅让', 54,
      '礼部尚书苏循独扬言曰：“梁王功业显大，历数有归，朝廷速宜揖让。”朝士无敢违者。',
      [('苏循', '公开主张禅让者'), ('朱温', '苏循所称梁王')],
      when='905年十一月辛巳前；确日未载',
      note='“历数有归”是苏循言论，不是可独立证实的天命；朝士态度按主书保留。')
event('zhu_named_wei_king_nine_bestowals', '唐廷辛巳进封朱全忠魏王并加九锡', 54,
      '以宣武、宣义、天平、护国、天雄、武顺、佑国、河阳、义武、昭义、保义、戎昭、武定、泰宁、平庐、忠武、匡国、镇国、武宁、忠义、荆南等二十一道为魏国，进封魏王，仍加九锡。',
      [('朱温', '受魏王九锡诏者')],
      when='905年十一月辛巳', place='魏国（诏定二十一道）',
      note='这是朝廷诏命，后句朱全忠让而不受；不写成已受领。二十一道名单与《旧唐书》《新五代史》有异，逐书保留。',
      time_quote='辛巳，以全忠为相国，总百揆。')
event('zhu_refuses_wei_title', '朱全忠对魏王九锡诏命让而不受', 54,
      '全忠怒其稽缓，让不受。', [('朱温', '辞让诏命者')],
      when='905年十一月辛巳诏后；确日未载',
      note='辞让与朝廷进封分录；动机“怒其稽缓”为主书叙述。')
event('jiang_delivers_hand_edict', '唐廷戊子令蒋玄晖持手诏往见朱全忠', 54,
      '十二月，戊子，命枢密使蒋玄晖赍手诏诣全忠谕指。',
      [('蒋玄晖', '持手诏赴朱全忠处者'), ('朱温', '受谕对象')],
      when='905年十二月戊子',
      note='《旧唐书》同记戊子送手诏；手诏具体措辞不能由主书补写。')
event('jiang_reports_zhu_anger', '蒋玄晖癸巳自大梁回报朱全忠怒未解', 54,
      '癸巳，玄晖自大梁还，言全忠怒不解。',
      [('蒋玄晖', '从大梁回报者'), ('朱温', '被转述为怒未解者')],
      when='905年十二月癸巳', place='大梁至唐廷',
      note='只记蒋玄晖所报告的朱全忠态度；不把两人的交涉内容自行补齐。')
event('liu_can_proposes_cession', '柳璨甲午奏请唐帝传禅并赴大梁传意', 54,
      '甲午，柳璨奏称：“人望归梁王，陛下释重负，今其时也。”即日遣璨诣大梁达传禅之意，全忠拒之。',
      [('柳璨', '奏请并赴大梁传意者'), ('朱温', '拒绝传禅提议者')],
      when='905年十二月甲午', place='大梁',
      note='“人望归梁王”是柳璨奏辞；主书说朱全忠拒之，不写成传禅已完成。')
event('queen_asks_jiang_for_survival', '何太后托宫人向蒋玄晖求传禅后保全母子', 54,
      '何太后泣遣宫人阿秋、阿虔达意玄晖，语以他日传禅之后，求子母生全。',
      [('何太后', '托人求保全母子者'), ('阿秋', '传达何太后意思者'),
       ('阿虔', '传达何太后意思者'), ('蒋玄晖', '受托对象')],
      when='本段追叙；确年日未载', year=None,
      note='“他日传禅之后”是假设将来情形；不能写成传禅已发生。')
event('wang_kong_second_accusation', '王殷与赵殷衡指控蒋玄晖等谋复唐', 54,
      '王殷、赵殷衡谮玄晖，云“与柳璨、张廷范于积善宫夜宴，对太后焚香为誓，期兴复唐祚。”',
      [('王殷', '提出指控者'), ('孔循', '以赵殷衡名提出指控者'),
       ('蒋玄晖', '被指控者'), ('柳璨', '被指控者'), ('张廷范', '被指控者'),
       ('何太后', '被指称参与盟誓者')],
      when='905年十二月乙未前；确日未载',
      note='夜宴、盟誓、复唐均是王殷与孔循的谮言，不当作已证实活动。')
event('jiang_ying_zhu_arrested', '朱全忠乙未捕蒋玄晖、应顼、朱建武', 54,
      '乙未，收玄晖及丰德库使应顼、御厨使硃建武系河南狱；以王殷权知枢密，赵殷衡权判宣徽院事。',
      [('朱温', '下令收捕者'), ('蒋玄晖', '被收捕者'), ('应顼', '被收捕者'),
       ('朱建武', '被收捕者'), ('王殷', '暂掌枢密者'), ('孔循', '以赵殷衡名暂判宣徽院者')],
      when='905年十二月乙未', place='河南狱',
      note='拘押与新任命同日见于主书，死亡另见丁酉，不提前记为乙未处死。')
event('zhu_petitions_refusal', '朱全忠三表辞魏王九锡', 54,
      '全忠三表辞魏王、九锡之命。', [('朱温', '三次上表辞命者')],
      when='905年十一月辛巳后、十二月丁酉前；确日未载',
      note='只记三次辞命，不推定各表日期或真实意图。')
event('zhu_named_all_armies_commander', '唐廷丁酉准辞魏王九锡，改授天下兵马元帅', 54,
      '丁酉，诏许之，更以为天下兵马元帅',
      [('朱温', '受改授天下兵马元帅者')],
      when='905年十二月丁酉',
      note='与本年十月“诸道兵马元帅”称号不同；《旧唐书》亦称由诸道改为天下。')
event('jiang_ying_zhu_killed', '蒋玄晖、应顼、朱建武丁酉被杀', 54,
      '是日，斩蒋玄晖，杖杀应顼、硃建武。',
      [('蒋玄晖', '被斩者'), ('应顼', '被杖杀者'), ('朱建武', '被杖杀者')],
      when='905年十二月丁酉', place='河南',
      note='“是日”承丁酉；旧唐书乙未诏语称送河南府处决，执行日据主书。')
event('court_restructures_palace_offices', '唐廷庚子省枢密使及宣徽南院使', 54,
      '庚子，省枢密使及宣徽南院使，独置宣徽使一员，以王殷为之，赵殷衡为副使。',
      [('王殷', '任宣徽使者'), ('孔循', '以赵殷衡名任副使者')],
      when='905年十二月庚子',
      note='省官署与任职见同句，勿与乙未“权知”“权判”混同。')
event('court_bars_palace_women_from_orders', '唐廷辛丑罢宫人传诏与参随视朝', 54,
      '辛丑，敕罢宫人宣传诏命及参随视朝。',
      when='905年十二月辛丑',
      note='只录制度命令，不推断实际执行范围与持续时间。')
event('jiang_posthumously_disgraced', '唐廷追削蒋玄晖并命焚尸', 54,
      '追削蒋玄晖为凶逆百姓，令河南揭尸于都门外，聚众焚之。',
      [('蒋玄晖', '被追削并命示众焚尸者')],
      when='905年十二月辛丑后条；确日未载', place='河南都门',
      note='诏令记为命令；不凭本句推定尸体已实际焚毁。')

# 55–56: Keep allegations separate from the killing and the dated court orders.
event('wang_kong_accuse_jiang_again', '王殷、赵殷衡再诬蒋玄晖私侍何太后', 55,
      '玄晖既死，王殷、赵殷衡又诬玄晖私侍何太后，令阿秋、阿虔通导往来。',
      [('王殷', '再提指控者'), ('孔循', '以赵殷衡名再提指控者'),
       ('蒋玄晖', '死后被指控者'), ('何太后', '被指控涉及者'),
       ('阿秋', '被指为通导者'), ('阿虔', '被指为通导者')],
      when='蒋玄晖死后、己酉前；确日未载',
      note='主书明确称“诬”，私侍和通导均不录为真实发生。')
event('queen_and_attendants_killed', '何太后与宫人阿秋、阿虔遇害', 55,
      '己酉，全忠密令殷、殷衡害太后于积善宫，敕追废太后为庶人，阿秋、阿虔皆于殿前扑杀。',
      [('朱温', '密令杀害者'), ('王殷', '受命执行者'), ('孔循', '以赵殷衡名受命执行者'),
       ('何太后', '被害者'), ('阿秋', '被扑杀者'), ('阿虔', '被扑杀者')],
      when='《资治通鉴》905年十二月己酉；《旧唐书》作戊申', place='积善宫、殿前',
      note='何太后遇害日两书记载不同，保留异日；追废为诏令，另有执行问题不外推。')
event('court_mourns_queen', '唐廷庚戌因太后丧废朝三日', 55,
      '庚戌，以皇太后丧，废朝三日。',
      when='《资治通鉴》905年十二月庚戌；《旧唐书》作己酉',
      note='两书干支相差一日，不自行订正；三日为停朝期限。')
event('court_cancels_suburban_rite', '唐廷辛亥取消来年正月郊庙礼', 56,
      '辛亥，敕以宫禁内乱，罢来年正月上辛谒郊庙礼。',
      when='《资治通鉴》905年十二月辛亥；《旧唐书》作庚戌',
      note='诏称“宫禁内乱”是官方理由；主书与旧书又差一日，不当作另一场郊礼。')

# 57–60: Court executions, regional military changes, and retrospective grievance.
event('liu_can_zhang_tingfan_demoted', '柳璨与张廷范癸丑被贬', 57,
      '癸丑，守司空兼门下侍郎、同平章事柳璨贬登州刺史，太常卿张廷范贬莱州司户。',
      [('柳璨', '贬登州刺史者'), ('张廷范', '贬莱州司户者')],
      when='905年十二月癸丑', place='登州、莱州',
      note='本句是贬官诏命，非已赴任；与次日处决分录。')
event('liu_can_zhang_tingfan_executed', '柳璨、张廷范甲寅被处死', 57,
      '甲寅，斩璨于上东门外，车裂廷范于都市。',
      [('柳璨', '被斩者'), ('张廷范', '被车裂者')],
      when='905年十二月甲寅', place='上东门外、都市',
      note='柳璨临刑语为主书引述，不用它推定其真实罪责。')
event('wang_zonglang_flees_jinzhou', '王宗朗焚金州城邑后奔成都', 57,
      '西川将王宗朗不能守金州，焚其城邑，奔成都。',
      [('王宗朗', '失守后焚城并奔成都者')],
      when='905年十二月甲寅后条；确日未载', place='金州、成都',
      note='主书说不能守，不写成某军当日攻破金州。')
event('feng_xingxi_recovers_jinzhou', '冯行袭复取金州并请徙理均州', 57,
      '戎昭节度使冯行袭复取金州，奏称“金州荒残，乞徙理均州，”从之。更以行袭领武安军。',
      [('冯行袭', '复取金州并请迁治、兼领武安者')],
      when='905年十二月甲寅后条；确日未载', place='金州、均州',
      note='荒残是冯行袭奏称；旧唐书记迁治、改武定军，主书作“更以行袭领武安军”，军名异文待核。')
event('chen_xun_flees_muzhou', '陈询失守睦州奔广陵，陶雅入据', 58,
      '陈询不能守睦州，奔于广陵，淮南招讨使陶雅入据其城。',
      [('陈询', '弃睦州奔广陵者'), ('陶雅', '入据睦州者')],
      when='905年年末条；确日未载', place='睦州、广陵',
      note='只录失守与入据，不推定双方交战过程。')
event('yang_wo_departure_grievance', '杨渥离宣州时欲携幄幕亲兵，王茂章拒绝', 59,
      '杨渥之去宣州也，欲取其幄幕及亲兵以行，观察使王茂章不与，渥怒。',
      [('杨渥', '要求携幄幕亲兵而受拒者'), ('王茂章', '拒绝交付者')],
      when='杨渥离宣州时的追叙；确日未载', year=None, place='宣州',
      note='“之去宣州也”追叙此前离任时的争执，不确定为第59段当日。')
event('yang_wo_orders_attack_wang_maozhang', '杨渥袭位后派李简等兵袭王茂章', 59,
      '既袭位，遣马步都指挥使李简等将兵袭之。',
      [('杨渥', '派兵者'), ('李简', '领兵袭击者'), ('王茂章', '被袭击对象')],
      when='905年杨渥袭位后；确日未载', place='宣州',
      note='“之”承王茂章；主书本段未载战果，不提前写败亡或去向。')
event('yang_biao_repels_hunan_troops', '杨彪击退侵淮南的湖南兵', 60,
      '湖南兵寇淮南，淮南牙内指挥使杨彪击却之。',
      [('杨彪', '率军击退者')], when='905年年末条；确日未载', place='淮南',
      note='主书未给来兵将领、规模与具体地点，不推断攻方主帅。')

extra(new_tang_succession, 'event', 'event_zztj_265_0905_yang_xingmi_dies', 'time_original',
      '《新唐书》卷十同记杨行密庚辰卒。',
      '庚辰，淮南節度使楊行密卒', 53, 'corroborates',
      '该书称淮南节度使，主书称吴武忠王；两书称谓各保留。')
extra(new_tang_succession, 'event', 'event_zztj_265_0905_generals_request_yang_wo_titles', 'description',
      '《新唐书》卷十记杨渥获淮南节度副大使及东面诸道行营都统，职名与主书将佐请求有所不同。',
      '以其子渥為淮南節度副大使、東面諸道行營都統', 53, 'conflicts',
      '主书称将佐请李俨承制授节度使、东南诸道行营都统等；新书称副大使、东面诸道都统，不能无说明地合并职名。')
extra(old_november, 'event', 'event_zztj_265_0905_zhu_named_wei_king_nine_bestowals', 'description',
      '《旧唐书》卷二十下载辛巳诏命和二十一道名单。',
      '辛巳，制：「回天再造竭忠守正功臣', 54, 'adds',
      '旧书二十一道与主书名单有次序及名称差异，不以其名单覆盖《通鉴》。')
extra(new_five_yearend, 'event', 'event_zztj_265_0905_zhu_named_wei_king_nine_bestowals', 'time_original',
      '《新五代史》卷一同记十一月辛巳封魏王、相国、备九锡。',
      '十一月辛巳，天子封王為魏王、相國，總百揆', 54, 'corroborates',
      '该书二十一军清单与主书、旧唐书不同，未在本条强行统合。')
extra(old_dec_early, 'event', 'event_zztj_265_0905_jiang_delivers_hand_edict', 'time_original',
      '《旧唐书》卷二十下同记十二月戊子蒋玄晖赍手诏往魏国。',
      '戊子，詔蔣玄暉齎手詔赴魏國', 54, 'corroborates',
      '旧书另说不许陈让锡命，作为该书所载诏意。')
extra(old_dec_early, 'event', 'event_zztj_265_0905_liu_can_proposes_cession', 'description',
      '《旧唐书》卷二十下保存甲午柳璨奏议与唐帝令其亲赴大梁传意。',
      '甲午，上召三宰相議其事，柳璨曰：「人望歸元帥，陛下揖讓釋負，今其時也。」',
      54, 'corroborates', '奏辞为柳璨主张，不能把“人望归”当独立民意调查。')
extra(old_dec_early, 'event', 'event_zztj_265_0905_jiang_ying_zhu_arrested', 'description',
      '《旧唐书》卷二十下乙未诏蒋玄晖、应顼、朱建武送河南府处决。',
      '乙未，敕：樞密使蔣玄暉宜削在身官爵，送河南府處斬。豐德庫使應頊、尚食使硃建武送河南府決殺',
      54, 'adds', '主书乙未记收系、丁酉记执行；旧书乙未是处决诏令，不作已经处决之日。')
extra(old_dec_early, 'event', 'event_zztj_265_0905_court_restructures_palace_offices', 'description',
      '《旧唐书》卷二十下庚子诏停枢密及两院，王殷权知枢密；与主书“独置宣徽使一员”不同。',
      '庚子，敕：樞密使及宣徽南院北院並停', 54, 'conflicts',
      '两书官署叙述不能强并；主书王殷任宣徽使、新书王殷权知枢密并列。')
extra(new_wang_dispute, 'event', 'event_zztj_265_0905_queen_asks_jiang_for_survival', 'description',
      '《新五代史》王殷传称何太后求蒋玄晖保全母子。',
      '梁王禪位後，願全唐家子母', 54, 'corroborates',
      '仍是对将来禅位的请求，不证明已经禅让。')
extra(old_dec_late, 'event', 'event_zztj_265_0905_queen_and_attendants_killed', 'time_original',
      '《旧唐书》卷二十下记何太后戊申被害、己酉废朝，与《通鉴》己酉/庚戌差一日。',
      '戊申，全忠令知樞密王殷害皇太后何氏于積善宮，又殺宮人阿秋、阿虔',
      55, 'conflicts', '保留干支日差异，待历日及纸本校勘；不把两日理解为两次杀害。')
extra(new_kong_dispute, 'event', 'event_zztj_265_0905_queen_and_attendants_killed', 'description',
      '《新五代史》孔循传记朱全忠遣孔循、王殷弑何皇后。',
      '太祖遣循與王殷弒何皇后', 55, 'corroborates',
      '该书没有阿秋、阿虔的处决细节；孔循即主书赵殷衡。')
extra(old_dec_late, 'event', 'event_zztj_265_0905_court_cancels_suburban_rite', 'time_original',
      '《旧唐书》卷二十下庚戌诏停次年正月上辛郊庙，与主书辛亥相差一日。',
      '庚戌，敕：「朕以謬荷丕圖', 56, 'conflicts',
      '同一取消郊礼诏书的干支异记，不记为两道不同决定。')
extra(old_dec_late, 'event', 'event_zztj_265_0905_liu_can_zhang_tingfan_demoted', 'time_original',
      '《旧唐书》卷二十下同记癸丑柳璨贬登州、张廷范贬莱州。',
      '癸丑，敕光祿大夫、守司空', 57, 'corroborates',
      '旧书保留更长诏文，官衔摘录非完整全文。')
extra(old_dec_late, 'event', 'event_zztj_265_0905_liu_can_zhang_tingfan_executed', 'time_original',
      '《旧唐书》卷二十下同记甲寅柳璨被斩、张廷范车裂。',
      '甲寅，敕：「責授登州刺史柳璨', 57, 'corroborates',
      '诏书含定罪措辞，不自动视为已证实罪责；下文载“是日斬於上東門外”。')
extra(old_dec_late, 'event', 'event_zztj_265_0905_feng_xingxi_recovers_jinzhou', 'description',
      '《旧唐书》卷二十下记收复金州、请徙理均州，并称改武定军。',
      '戎昭軍奏收復金州，兵火之後，井邑殘破，請移理所於均州，從之。仍改為武定軍',
      57, 'conflicts', '主书说“更以行袭领武安军”；旧书记军额改武定，军名异文待核。')
extra(new_yangwo, 'event', 'event_zztj_265_0905_yang_wo_departure_grievance', 'description',
      '《新五代史》卷六十一同记杨行密卒、杨渥继立及王茂章任宣州观察使，但未记幄幕亲兵争执。',
      '行密卒，渥嗣立', 59, 'adds',
      '该书不能独立证实争执；仅为继任前后次序的补充。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(53, 61):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='卷265天祐二年第53—60段连续处理；异日与军名异文并列，指控、追叙和诏命不混作已发生事实。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=905,
    primary_source_key=primary_winter, primary_source_keys=[primary_winter, primary_transition, primary_yearend],
    paragraphs=[Q[n]['id'] for n in range(53, 61)], next_paragraph=None,
    coverage='卷265天祐二年第53—60段连续处理；杨行密去世、魏王九锡与传禅争议、何太后遇害、郊礼取消、年底州镇事。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
