"""Curate consecutive Tongjian vol. 270, 917 paragraphs 13–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 21))
main = 'tongjian-270-917-year-end'
old13 = 'jiuwudaishi-013-liu-zhijun-death'
old09 = 'jiuwudaishi-009-liang-december'
old63 = 'jiuwudaishi-063-zhang-quanyi-name'
specs = [
    (main,P / 'sources/library' / main,'09262e73','司马光等'),
    (old13,P / 'sources/library' / old13,'09262e73','薛居正等'),
    (old09,P / 'sources/library' / old09,'09262e73','薛居正等'),
    (old63,P / 'sources/library' / old63,'28106b55','薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0917-p013-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
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
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/270.txt').read_text().splitlines()
for n in range(13, 21):
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
    for key in (main,):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明三年（917）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0917_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','蜀主':'王建','帝':'朱友贞','张宗奭':'张全义','闽王审知':'王审知','越主岩':'刘岩','延钧':'王延钧'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明三年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=917):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0917_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '917年本段条；确日未载', dynasty='五代十国',
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
          '只保留原纪年，不换算公历日；叙述性回顾不推成逐次日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0917_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p013: Shu commander Liu Zhijun, failure of command and December execution.
event('liu_zhijun_shu_command_fails','蜀将刘知俊任都招讨使而诸旧将多不奉令',13,
      '蜀主以刘知俊为都招讨使，诸将皆旧功臣，多不用其命，且疾之，故无成功。',
      [('蜀主','任刘知俊为都招讨使者'),('刘知俊','因旧将不奉令而未获战功的都招讨使')],
      when='917年十二月以前的军事局势；起日未载',place='蜀',
      note='“无成功”是主书对本次任用的评价，不概括刘知俊终生战绩。')
claim('event','event_zztj_270_0917_liu_zhijun_shu_command_fails','description',
      '《旧五代史》刘知俊传亦称蜀旧将违其节度、无功而还。',13,
      '時部將皆王建舊人，多違節度，不成功而還，蜀人因而毀之。',
      '旧书与主书叙事可能同源，保留其独立出处，不作完全独立确证。',old13,'corroborates')
event('liu_zhijun_executed_chengdu','蜀主以谋叛罪名捕斩刘知俊于炭市',13,
      '唐文扆数毁之，蜀主亦忌其才，尝谓所亲曰：“吾老矣，知俊非尔辈所能驭民。”十二月，辛亥，收知俊，称其谋叛，斩于炭市。',
      [('唐文扆','屡次毁谤刘知俊者'),('王建','下令捕斩刘知俊的蜀主'),('刘知俊','被以谋叛名义斩于炭市者')],
      when='917年十二月辛亥',place='炭市',
      note='原文是“称其谋叛”，只记蜀廷指控，不断言谋反已被证实。')
claim('event','event_zztj_270_0917_liu_zhijun_executed_chengdu','description',
      '《旧五代史》称王建十二月命捕刘知俊，在成都炭市斩之。',13,
      '偽蜀天漢元年冬十二月，建遣人捕知俊，斬於成都府之炭市。',
      '旧书称蜀天汉元年，与通鉴917年相应；确日仅主书给辛亥。',old13,'corroborates')

# p014–p016: edicts and appointments in chronological sequence.
event('shu_amnesty_guangtian_next_year','蜀大赦并预定次年改元光天',14,
      '癸丑，蜀大赦，改明年元曰光天。',[('王建','颁大赦并改次年年号的蜀主')],
      when='917年十二月癸丑；光天为次年年号',place='蜀',
      note='“改明年元”不等于在917年立即进入光天元年。')
event('zhang_quanyi_deputy_generalissimo','后梁任张宗奭为天下兵马副元帅',15,
      '壬戌，以张宗奭为天下兵马副元帅。',[('张宗奭','受任天下兵马副元帅者')],
      when='917年十二月壬戌',place='后梁',
      note='张宗奭即既有张全义，《旧五代史》明确记其在梁改名宗奭；复用主体。')
claim('person',people['张全义'],'description','《旧五代史》张全义传明言梁太祖为其改名宗奭。',15,
      '張全義，字國維，濮州臨濮人。初名居言，賜名全義，梁祖改為宗奭',
      '同人异名的直接书证；原文摘录保留繁体。',old63,'corroborates')
claim('event','event_zztj_270_0917_zhang_quanyi_deputy_generalissimo','description',
      '《旧五代史》末帝纪在壬戌记张宗奭授天下兵马副元帅。',15,
      '壬戌，以守太尉、兼中書令、河南尹、判六軍諸衛事、魏王張宗奭為天下兵馬副元帥。',
      '旧书详列原衔；不由官号推定实际统辖。',old09,'corroborates')
event('he_gui_xuanyi_commander','后梁因庆州功授贺瑰宣义节度使、同平章事',16,
      '帝论平庆州功，丁卯，以左龙虎统军贺瑰为宣义节度使、同平章事，寻以为北面行营招讨使。',
      [('帝','因庆州功授官的梁帝'),('贺瑰','受任宣义节度使、同平章事，后任北面行营招讨使者')],
      when='917年十二月丁卯；北面任命为“寻”后',place='后梁',
      note='第二项任命确日未载，保留“寻”而不同时定丁卯。')
claim('event','event_zztj_270_0917_he_gui_xuanyi_commander','description',
      '《旧五代史》末帝纪同记丁卯贺瑰授宣义节度使及同平章事。',16,
      '丁卯，以西面行營馬步都指揮使、左龍虎軍統軍賀瑰為檢校太傅、同中書門下平章事，充宣義軍節度使',
      '旧书加检校太傅；“寻以为北面”未在该引文中，仍据主书。',old09,'corroborates')

# p017: frozen-river crossing and Yangliu capture.
event('jin_crosses_frozen_river','晋王趁大寒河冰坚固，率步骑渡河',17,
      '戊辰，晋王畋于朝城。是日，大寒，晋王视河冰已坚，引步骑稍度。',
      [('晋王','检视河冰并率军渡河者')],when='917年十二月戊辰',place='朝城、河上',
      note='原文未具渡口名称；不推断全军即时过河。')
event('jin_captures_yangliu','晋军攻破杨刘城并俘守将安彦之',17,
      '梁甲士三千戍杨刘城，缘河数十里，列栅相望，晋王急攻，皆陷之。进攻杨刘城，使步卒斩其鹿角，负葭苇塞堑，四面进攻，即日拔之，获其守将安彦之。',
      [('晋王','攻破河岸营栅与杨刘城的晋军统帅'),('安彦之','被俘的梁杨刘城守将')],
      when='917年十二月戊辰',place='杨刘城',
      note='“三千”为主书梁守军数，不擅算伤亡或城池后续归属。')
claim('event','event_zztj_270_0917_jin_captures_yangliu','description',
      '《旧五代史》末帝纪亦记晋人十二月陷杨刘城，令梁帝停郊礼。',17,
      '是月，晉人陷楊劉城，帝聞之懼，遂停郊禮，車駕急歸東京。',
      '旧书只给十二月，与主书戊辰并列；其后郊礼另在下一段录。',old09,'corroborates')

# p018: proposed Liang ritual, objections, travel, then cancellation.
event('zhao_yan_proposes_liang_southern_sacrifice','赵岩建议梁帝赴西都行南郊礼',18,
      '先是，租庸使、户部尚书赵岩言于帝曰：“陛下践祚以来，尚未南郊，议者以为无异籓侯，为四方所轻。请幸西都行郊礼，遂谒宣陵。”',
      [('赵岩','建议行南郊礼者'),('朱友贞','受建议的梁帝')],
      when='梁帝赴洛阳前；确年月未载',place='西都、宣陵',year=None,
      note='“先是”属于前事；建议与实际出行分开。')
event('jing_xiang_opposes_liang_sacrifice','敬翔谏梁帝暂缓南郊',18,
      '敬翔谏曰：“自刘镠失利以来，公私困竭，人心惴恐；今展礼圜丘，必行赏赉，是慕虚名而受实弊也。且勍敌近在河上，乘舆岂宜轻动！俟北方既平，报本未晚。”',
      [('敬翔','主张先平北方、暂缓郊礼者'),('朱友贞','受谏未从的梁帝')],
      when='梁帝赴洛阳前；确年月未载',place='后梁',year=None,
      note='敬翔的财政与军事风险判断为其奏谏内容，不改写成已核实的国库金额。')
event('liang_emperor_abandons_sacrifice','梁帝赴洛阳后闻杨刘失守，罢郊祀返大梁',18,
      '帝不听，己巳，如洛阳，阅车服，饰宫阙，郊祀有日，闻杨刘失守，道路讹言晋军已入大梁，扼汜水矣，从官皆忧其家，相顾涕泣。帝惶骇失图，遂罢郊祀，奔归大梁。',
      [('朱友贞','赴洛阳筹郊礼后折返大梁的梁帝')],
      when='917年十二月己巳起；返京确日未载',place='洛阳、大梁',
      note='晋军入大梁、扼汜水是道路讹言，不录作真实战果；杨刘失守已有前段事件。')
claim('event','event_zztj_270_0917_liang_emperor_abandons_sacrifice','description',
      '《旧五代史》末帝纪也记梁帝幸洛阳拟南郊，闻杨刘失守而停礼返东京。',18,
      '己巳，帝幸洛陽，為來年有事於南郊也。遂幸伊闕，親拜宣陵。',
      '旧书明确拟于来年行礼；主书只说郊祀有日。',old09,'corroborates')

# p019–p020: Liang deputy and the Min–Yue marriage.
event('zhang_quanyi_western_capital_caretaker','梁任张宗奭为西都留守',19,
      '甲戌，以河南尹张宗奭为西都留守。',
      [('张宗奭','受任西都留守者')],when='917年十二月甲戌',place='西都洛阳',
      note='复用张全义主体；张宗奭为其梁时姓名。')
claim('event','event_zztj_270_0917_zhang_quanyi_western_capital_caretaker','description',
      '《旧五代史》末帝纪也记甲戌任张宗奭为西都留守。',19,
      '甲戌，以天下兵馬副元帥、太尉、兼中書令、河南尹、魏王張宗奭為西都留守。',
      '旧书详原官衔，不改变既有主体。',old09,'corroborates')
event('wang_yanjun_marries_liu_yan_daughter','闽王王审知为子王延钧娶越主刘岩之女',20,
      '是岁，闽王审知为其子牙内都指挥使延钧娶越主岩之女。',
      [('闽王审知','为子王延钧安排婚事的闽王'),('延钧','迎娶越主之女的牙内都指挥使'),('越主岩','嫁女与闽王之子的越主'),('刘岩之女（王延钧妻）','嫁于王延钧者')],
      when='917年是岁；具体月日未载',place='闽、越',
      note='女方原文未具名，采用带关系的消歧主体名，不推断其本名。')
for key,a,b,relation,value in [
    ('relationship_person_王审知_person_王延钧_父亲','闽王审知','延钧','父亲','王审知是王延钧的父亲。'),
    ('relationship_person_刘岩_person_刘岩之女（王延钧妻）_父亲','越主岩','刘岩之女（王延钧妻）','父亲','刘岩是王延钧妻的父亲。'),
    ('relationship_person_刘岩之女（王延钧妻）_person_王延钧_妻子','刘岩之女（王延钧妻）','延钧','妻子','刘岩之女是王延钧的妻子。')]:
    B['person_relationships'].append(dict(key=key,person_a_key=people[{'闽王审知':'王审知','越主岩':'刘岩','延钧':'王延钧'}.get(a,a)],person_b_key=people[{'闽王审知':'王审知','越主岩':'刘岩','延钧':'王延钧'}.get(b,b)],relation_type=relation,description=value,status='draft'))
    claim('person_relationship',key,'description',value,20,
          '闽王审知为其子牙内都指挥使延钧娶越主岩之女',
          '关系端点按原文“其子”“岩之女”“娶”确定；女性本名未载。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(13,21):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷270贞明三年第13—20段；刘知俊之死、梁晋任官及杨刘失守、闽越联姻。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=270,year=917,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(13,21)],
    next_paragraph='卷270贞明四年（918）第1段，需建立年账本',
    coverage='卷270贞明三年第13—20段，至917年卷末。',supplements=supplements,
    reviewed_questions=[
      {'paragraph_id':Q[13]['id'],'note':'刘知俊以“称其谋叛”被处死，不作谋叛定论。'},
      {'paragraph_id':Q[15]['id'],'note':'旧五代史明记张全义在梁改名宗奭，复用已有张全义主体。'},
      {'paragraph_id':Q[18]['id'],'note':'道路传晋军入大梁为讹言；南郊礼终未举行。'},
      {'paragraph_id':Q[20]['id'],'note':'刘岩女未具本名，以关系消歧主体记录；婚姻和亲子关系均据通鉴明文。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
