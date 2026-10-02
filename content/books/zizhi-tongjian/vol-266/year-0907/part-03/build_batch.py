"""Curate Tongjian 266, year 907, consecutive paragraphs 16–22."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 62))
primary = 'tongjian-266-907-spring-later'
accession = 'tongjian-266-907-accession'
early_liang = 'tongjian-266-907-early-liang'
old_edict = 'jiuwudaishi-003-accession-edict'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0907-p016-p022',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-02/sources/library' / primary, '81ed5300', '司马光等'),
    (accession, P / 'sources/library' / accession, '04d95f09', '司马光等'),
    (early_liang, P / 'sources/library' / early_liang, '04d95f09', '司马光等'),
    (old_edict, P / 'sources/library' / old_edict, 'd9a65808', '薛居正等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, accession, early_liang)}
for n in range(16, 23):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '梁王':'朱温', '王景仁':'王茂章'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/year-0907/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0907_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷266·开平元年（907）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷266开平元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=907, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_266_0907_' + code)
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
                                time_original=when or '907年本段条；确日未载', dynasty='唐', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '907年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_266_0907_' + code + '_' + pk
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
    ck = f'claim_zztj_266_0907_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 16: Name change and the elder brother's objection precede the accession.
event('zhu_renames','梁王朱温更名晃',16,
      '壬戌，梁王更名晃。',
      when='907年四月壬戌',
      note='朱温、朱晃为同一人，复用旧907更名事件及既有人物，不另立人物。',
      reuse_key='event_0907_rename_zhu')
claim('event','event_0907_rename_zhu','description',
      '朱全昱在朱温即位前质问其称帝。',16,
      '王兄全昱闻王将即帝位，谓王曰：“硃三，尔可作天子乎！”',
      '朱全昱的话是其反对称帝的言辞；“王兄”明示长幼。')
for name in ('朱全昱','朱温'):
    person(name,16,'兄弟关系与朱温更名记载中的人物','王兄全昱闻王将即帝位')
relation('relationship_person_朱全昱_person_zhu_wen_兄长',16,
         '王兄全昱闻王将即帝位','原文“王兄”明示朱全昱为朱温兄长；复用已有方向。')

# 17: The enthronement and subsequent edicts have distinct dates.
event('liang_accession','朱温即皇帝位',17,
      '甲子，张文蔚、杨涉乘辂自上源驿从册宝，诸司各备仪卫卤簿前导，百官从其后，至金祥殿前陈之。王被兗冕，即皇帝位。',
      when='907年四月甲子即帝位；戊辰改元国号',place='大梁金祥殿',
      note='“兗冕”为本电子底本文字，旧书作“袞冕”，不静默改字；复用后梁建立事件。',
      reuse_key='event_liang_founded')
claim('event','event_liang_founded','description',
      '戊辰大赦、改元开平，定国号大梁。',17,
      '戊辰，大赦，改元，国号大梁。',
      '即位与改元相隔数日；不将戊辰写作即位日。')
claim('event','event_liang_founded','description',
      '奉唐昭宣帝为济阴王。',17,
      '奉唐昭宣帝为济阴王，皆如前代故事，唐中外旧臣官爵并如故。',
      '唐昭宣帝封济阴王；迁曹州及守卫见本段后句。')
event('former_tang_emperor_confined','后梁将济阴王迁往曹州并派兵看守',17,
      '迁济阴王于曹州，栫之以棘，使甲士守之。',
      [('唐昭宣帝','被迁并受看守者')],
      when='907年四月戊辰后；确日未载',place='曹州',
      note='此人即退位后封济阴王的唐昭宣帝；本句没有记其死亡。')
event('liang_capital_command_changes','后梁改汴州为开封府并调整京府军名',17,
      '以汴州为开封府，命曰东都；以故东都为西都；废故西京，以京兆府为大安府，置佑国军于大安府，更名魏博曰天雄军。',
      [('朱温','改制的后梁皇帝')],
      when='907年四月戊辰后诏令；确日未载',place='汴州、京兆府、魏博',
      note='按主书记录制度与名号改变；不据名称直接绘制疆域边界。')
extra(old_edict,'event','event_liang_founded','description',
      '《旧五代史》卷三保存诏文，直书改天祐四年为开平元年、国号大梁。',
      '可改唐天祐四年為開平元年，國號大樑。',17,'corroborates',
      '诏文是政权自述的文书证据；只独立证明诏令内容，不证明“受命于天”等修辞。')
extra(old_edict,'event','event_zztj_266_0907_liang_capital_command_changes','description',
      '《旧五代史》卷三诏文记升汴州为开封府并建名东都。',
      '宜升汴州為開封府，建名東都。',17,'corroborates',
      '诏文未涵盖主书本事件其余所有京府、军名变更；只印证开封府与东都两项。')

# 18-21: Appointments and ancestral honors are not military annexations.
event('ma_yin_chu_title','后梁封马殷为楚王',18,
      '辛未，以武安节度使马殷为楚王。',
      when='907年四月辛未',place='武安军',
      note='封王是名号授予，不据此推定后梁直接控制湖南。',
      reuse_key='event_0907_ma_chu')
event('jing_xiang_heads_chongzheng','敬翔知崇政院事',19,
      '以宣武掌书记、太府卿敬翔知崇政院事，以备顾问，参谋议，于禁中承上旨，宣于宰相而行之。',
      when='907年四月辛未后；确日未载',
      note='本段记“知崇政院事”；枢密院职事并入发生在后续五月段落，不倒填。',
      reuse_key='event_0907_jingxiang')
claim('event','event_0907_jingxiang','description',
      '主书称敬翔参与军谋、民政，并在禅代之际有较多谋划。',19,
      '翔为人沉深，有智略，在幕府三十馀年，军谋、民政，帝一以委之。',
      '“三十余年”为主书概数，且是回顾性评述，不推成907年新任职年限。')
event('zhu_ancestors_honored','朱温追尊先祖及父母',20,
      '追尊皇高祖考、妣以来皆为帝、后，皇考诚为烈祖文穆皇帝。妣王氏为文惠皇后。',
      when='907年即位后条；确日未载',
      note='“追尊”是身后尊号，不推成朱诚或王氏在907年仍在世。',
      reuse_key='event_0907_ancestors')
for name in ('朱诚','王氏（朱温母）','朱温'):
    person(name,20,'朱温家族追尊记载中的人物','皇考诚为烈祖文穆皇帝。妣王氏为文惠皇后。')
relation('rel_early_朱诚_朱温_父亲',20,
         '皇考诚为烈祖文穆皇帝','“皇考诚”指朱温父亲朱诚；复用既有父亲关系。')
relation('rel_early_王氏（朱温母）_朱温_母亲',20,
         '妣王氏为文惠皇后','“妣王氏”指朱温母亲；未将同姓王氏泛化合并。')
event('zhu_youwen_takes_kaifeng_finances','朱友文任开封尹并判建昌院',21,
      '至是，以养子宣武节度副使友文为开封尹、判院事，掌凡国之金谷。友文本康氏之子也。',
      when='907年即位后条；确日未载',place='开封府',
      note='“初”所述建昌院原设时间未定，本段只确认友文此次授职；旧907任用事件复用。',
      reuse_key='event_0907_youwen')
for name in ('朱温','朱友文'):
    person(name,21,'养父子授职记载中的人物','以养子宣武节度副使友文为开封尹')
relation('relationship_person_zhu_wen_person_朱友文_养父',21,
         '以养子宣武节度副使友文为开封尹','“养子”明示收养关系，友文本康氏之子；复用既有养父关系。')

# 22: The Shu-Jin letter exchange records proposed, rejected cooperation.
event('li_keyong_titles_revoked','后梁削夺李克用官爵',22,
      '乙亥，下制削夺李克用官爵。',
      when='907年四月乙亥',
      note='削官为后梁诏令，不意味着河东承认后梁统治。',
      reuse_key='event_0907_revoke_keyong')
claim('event','event_0907_revoke_keyong','description',
      '主书记河东、凤翔、淮南仍称天祐，西川仍称天复。',22,
      '是时，惟河东、凤翔、淮南称“天祐”，西川称“天复”年号。',
      '本句呈现史书所见年号使用，不据此描绘确切边界或推定所有属州一致。')
event('shu_jin_letters','蜀王致晋王议各帝一方，晋王回书不许',22,
      '又遗晋王书云：“请各帝一方，俟硃温既平，乃访唐宗室立之，退归籓服。”晋王复书不许，曰：“誓于此生靡敢失节。”',
      when='907年唐亡后；确日未载',
      note='“请各帝一方”为蜀王建议，晋王明确拒绝；不建已结成军事同盟关系。',
      reuse_key='event_0907_shujin_letters')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(16,23):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平元年第16—22段连续处理；即位与改元分日，旧907事件及家族关系复用，诏文证据独立标注。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=907,
    primary_source_key=primary,primary_source_keys=[primary,accession,early_liang],
    paragraphs=[Q[n]['id'] for n in range(16,23)],next_paragraph=Q[23]['id'],
    coverage='卷266开平元年第16—22段连续处理；朱温改名、即位、改元、制度设置、家族追尊和反梁书信。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
