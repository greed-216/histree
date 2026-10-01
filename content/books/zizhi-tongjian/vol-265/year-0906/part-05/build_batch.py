"""Curate Tongjian 265, year 906, consecutive paragraphs 33–42."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 43))
primary = 'tongjian-265-906-autumn'
primary_leap = 'tongjian-265-906-leap-month'
old_cangzhou = 'jiuwudaishi-002-cangzhou'
old_ding = 'jiuwudaishi-059-dinghui'
new_kang = 'xinwudaishi-022-kanghuaiying'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0906-p033-p042',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-04/sources/library' / primary, '10d699bc', '司马光等'),
    (primary_leap, P / 'sources/library' / primary_leap, 'e67128a6', '司马光等'),
    (old_cangzhou, P.parent / 'part-04/sources/library' / old_cangzhou, '10d699bc', '薛居正等'),
    (old_ding, P / 'sources/library' / old_ding, 'ce105e4d', '薛居正等'),
    (new_kang, P / 'sources/library' / new_kang, 'e67128a6', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, primary_leap)}
for n in range(33, 43):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '裴':'秦裴', '渥':'杨渥', '仁恭':'刘仁恭', '守文':'刘守文', '克用':'李克用', '存勖':'李存勖', '知俊':'刘知俊', '崇本':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0906_05_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐三年（906）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=906, time_quote=None):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0906_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '906年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '906年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0906_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0906_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 33: The two Kang names are kept as separate existing entities pending a source check.
event('liu_kang_capture_five_western_prefectures', '刘知俊与康怀贞攻下鄜延等五州', 33,
      '十一月，刘知俊、康怀贞乘胜攻鄜、延等五州，下之。',
      [('刘知俊','攻取五州者'),('康怀贞','与刘知俊合兵者')],
      when='906年十一月；确日未载',place='鄜州、延州等五州',
      note='原文只点名鄜、延，其余三州不自行补定。前段作康怀英，本段作康怀贞；先依字面复用既有两实体，异同待核。')
event('liu_kang_promoted_after_western_campaign', '刘知俊加同平章事、康怀贞任保义节度使', 33,
      '加知俊同平章事，以怀贞为保义节度使。',
      [('刘知俊','获加同平章事者'),('康怀贞','获任保义节度使者')],
      when='906年十一月攻取鄜延后；确日未载',
      note='授职与战果分录；不将“西军自是不振”量化。')

# 34: Record the explicit father-son relation and succession.
event('gao_yan_dies_gao_li_succeeds', '湖州刺史高彦卒，其子高澧继任', 34,
      '湖州刺史高彦卒，子澧代之。',
      [('高彦','卒去的湖州刺史'),('高澧','继任湖州刺史者')],
      when='906年十一月后条；确日未载',place='湖州',
      note='“子澧”承接高彦，显示父子关系；高澧以本段首次建档。')
rel='relationship_person_高彦_person_高澧_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['高彦'],person_b_key=people['高澧'],
                                      relation_type='父亲',description='高彦是高澧的父亲。',status='draft'))
claim('person_relationship',rel,'description','高彦是高澧的父亲。',34,'湖州刺史高彦卒，子澧代之。',
      '“子澧”以高彦为父；关系方向为父亲指向儿子。')

event('qian_liu_recommends_wang_jingren', '钱镠荐王景仁，诏令领宁国节度使', 35,
      '十二月，乙酉，钱镠表荐行军司马王景仁，诏以景仁领宁国节度使。',
      [('钱镠','表荐者'),('王景仁','获诏领宁国节度使者')],
      when='906年十二月乙酉',
      note='区分钱镠表荐与朝廷下诏；本段未载王景仁实际到任。')
event('zhu_sends_li_zhouyi_to_luzhou', '朱全忠遣李周彝自河阳救潞州', 36,
      '硃全忠分步骑数万，遣行军司马李周彝将之，自河阳救潞州。',
      [('朱温','派援军者'),('李周彝','率步骑援潞州者')],
      when='906年十二月条；确日未载',place='河阳、潞州',
      note='“救潞州”是遣军目的；下段潞州降于河东，不倒填救援结果。')

# 37: Administrative reorganization, without drawing a boundary.
event('huazhou_commandery_reorganization', '废镇国军兴德府，华州及金商州改隶', 37,
      '闰月，乙丑，废镇国军兴德府复为华州，隶匡国节度，割金、商州隶佑国军。',
      [],when='906年闰月乙丑',place='华州、金州、商州',
      note='行政隶属变化不等于已核地理疆界；不自行换算闰月为公历月。')

# 38: Mourning is a retrospective statement; surrender follows the attack.
event('ding_hui_mourns_emperor_zhaozong', '丁会闻昭宗死讯后率将士缟素哀悼', 38,
      '初，昭宗凶讣至潞州，昭义节度使丁会帅将士缟素流涕久之。',
      [('丁会','率将士哀悼者')],when='昭宗死讯传至潞州后；确日未载',place='潞州',year=None,
      note='“初”表示追叙，不能当作906年闰月发生。')
event('ding_hui_surrenders_luzhou_to_jin', '丁会举潞州军降河东', 38,
      '及李嗣昭攻潞州，会举军降于河东。',
      [('李嗣昭','进攻潞州者'),('丁会','举军归降者')],
      when='906年闰月条；确日未载',place='潞州',
      note='“及”承前述进攻；《旧五代史》卷五十九作十二月，纪时不强合。')
event('li_keyong_appoints_li_sizhao_zhaoyi', '李克用任李嗣昭为昭义留后', 38,
      '李克用以嗣昭为昭义留后。',
      [('李克用','任命者'),('李嗣昭','获任昭义留后者')],
      when='丁会举军降河东后；确日未载',place='潞州',
      note='此为任命记载，不补写正式节度使授职。')
event('ding_hui_explains_surrender', '丁会向李克用解释归降原因并受厚待', 38,
      '会见克用，泣曰：“会非力不能守也。梁王陵虐唐室，会虽受其举拔之恩，诚不忍其所为，故来归命耳。”克用厚待之，位于诸将之上。',
      [('丁会','解释归降者'),('李克用','接纳并厚待者')],
      when='丁会归降后；确日未载',
      note='“陵虐唐室”是丁会当面陈述的理由，不作为未经核准的旁观叙述。')

# 39-41: The Cangzhou withdrawal, provisions and Zezhou failure are distinct.
event('zhu_orders_cangzhou_assault_preparations', '朱全忠己巳命军中准备攻沧州', 39,
      '己巳，硃全忠命诸军治攻具，将攻沧州。',
      [('朱温','命制攻具者')],when='906年闰月己巳',place='沧州',
      note='“将攻”是准备行为，不写成沧州已受强攻或陷落。')
event('zhu_withdraws_from_cangzhou_after_luzhou_news', '朱全忠闻潞州不守后撤离沧州', 39,
      '壬申，闻潞州不守，甲戌，引兵还。',
      [('朱温','率军撤退者')],when='906年闰月壬申闻讯，甲戌引兵还',place='沧州',
      note='壬申与甲戌为两日；仅据主书记录闻讯后撤军，不推定唯一原因。')
event('zhu_destroys_cangzhou_army_supplies', '朱全忠撤军时命焚沉军粮', 40,
      '全忠将还，命悉焚之，烟炎数里，在舟中者凿而沉之。',
      [('朱温','下令焚沉粮食者')],when='906年自沧州撤军时；确日未载',place='沧州',
      note='前句追述河南北调运的刍粮；“数里”是主书对烟势的约数。')
event('liu_shouwen_requests_surplus_supplies', '刘守文致书请求将余粮留给沧州城民', 40,
      '刘守文使遗全忠书曰：“王以百姓之故，赦仆之罪，解围而去，王之惠也。城中数万口，不食数月矣。与其焚之为烟，沉之为泥，愿乞其馀以救之。”',
      [('刘守文','致书请求者'),('朱温','受书者')],
      when='朱全忠撤军并焚粮时；确日未载',place='沧州',
      note='“数万口、不食数月”为刘守文信中所述；不换算具体人口和围困天数。')
event('zhu_leaves_grain_for_cangzhou', '朱全忠留下数囷粮食济沧州人', 40,
      '全忠为之留数囷以遗之，沧人赖以济。',
      [('朱温','留粮者')],when='刘守文致书后；确日未载',place='沧州',
      note='“数囷”保留主书原量词，不推算重量。')
event('jin_army_fails_at_zezhou', '河东军进攻泽州未克而退', 41,
      '河东兵进攻泽州，不克而退。',
      [],when='906年闰月末条；确日未载',place='泽州',
      note='主书未指明具体将领，不从相邻段落推定。')

# 42: The last segment of the year includes a retrospective biography clause.
event('peng_gan_requests_hunan_surrender', '吉州刺史彭玕遣使请降湖南', 42,
      '吉州刺史彭玕遣使请降于湖南',
      [('彭玕','遣使请降者')],when='906年卷末条；确日未载',place='吉州、湖南',
      note='“请降”是提出归附，本段未写湖南是否接受。')
event('zhong_chuan_appoints_peng_gan_jizhou', '钟传曾任彭玕为吉州刺史', 42,
      '玕本赤石洞蛮酋，钟传用为吉州刺史。',
      [('钟传','曾任命者'),('彭玕','曾获任吉州刺史者')],
      when='彭玕请降湖南之前；确年日未载',place='吉州',year=None,
      note='“本”提示追叙，年份不定；“蛮酋”为史书用语，本站概述不沿用该族群称谓。')

extra(old_cangzhou,'event','event_zztj_265_0906_liu_kang_capture_five_western_prefectures','description',
      '《旧五代史》卷二记康怀英十一月庚戌乘胜收鄜州，主书本段作康怀贞攻鄜、延等五州。',
      '十一月庚戌，懷英乘勝進軍，遂收鄜州',33,'conflicts',
      '同一西线战事的将名存在怀英/怀贞差异；现阶段不合并站内两人物实体，也不把庚戌强配五州全数。')
extra(old_ding,'event','event_zztj_265_0906_ding_hui_surrenders_luzhou_to_jin','time_original',
      '《旧五代史》卷五十九丁会传记三年十二月举潞州归河东，与主书闰月条纪时不同。',
      '三年十二月，王師攻會，居旬日，會以潞州歸於武皇',38,'conflicts',
      '不同纪时并列保留；“王师”是旧书立场用语，未据此推算确日。')
extra(new_kang,'event','event_zztj_265_0906_ding_hui_surrenders_luzhou_to_jin','description',
      '《新五代史》卷二十二亦记丁会以潞州归晋，后叙康怀英围潞州。',
      '丁會以潞州叛梁降晉，太祖命懷英為招討使',38,'corroborates',
      '新书后续围潞州属另一阶段，不倒填本段。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,43):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐三年第33—42段连续处理；西线人名异说、丁会归降纪时、卷末追叙分开校核。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=906,
    primary_source_key=primary,primary_source_keys=[primary,primary_leap],
    paragraphs=[Q[n]['id'] for n in range(33,43)],next_paragraph=None,
    coverage='卷265天祐三年第33—42段连续处理；西线收州、潞州归晋、沧州撤军、泽州战事及彭玕请降。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
