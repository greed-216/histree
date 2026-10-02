"""Curate consecutive Tongjian vol. 269, 916 paragraphs 4–6."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 10))
main = 'tongjian-269-917-northern-frontier'
old28 = 'jiuwudaishi-028-newzhou'
liao01 = 'liaoshi-001-newzhou'
liao71 = 'liaoshi-071-shulv-ping'
old32 = 'jiuwudaishi-032-ma-cun'
specs = [
    (main,P / 'sources/library' / main,'00253a75','司马光等'),
    (old28,ROOT / 'content/books/zizhi-tongjian/vol-269/year-0917/part-01/sources/library' / old28,'f5788d38','薛居正等'),
    (liao01,ROOT / 'content/books/zizhi-tongjian/vol-269/year-0917/part-01/sources/library' / liao01,'f5788d38','脱脱等'),
    (liao71,ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-08/sources/library' / liao71,'5d6a1646','脱脱等'),
    (old32,P / 'sources/library' / old32,'00253a75','薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0917-p004-p006',
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
lines = (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()
for n in range(4, 7):
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
        citation = f'卷269·贞明三年（917）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0917_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','契丹主':'阿保机','述律后':'述律平','吴王':'杨隆演','楚王殷':'马殷'}.get(name, name)
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
    key = 'event_zztj_269_0917_' + code
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
        edge = 'participation_zztj_269_0917_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p004: retrospective frontier geography and the defense system before 917.
event('yuguan_eight_garrisons','幽州北渝关至进牛口设八防御军',4,
      '初，幽州北七百里有渝关，下有渝水通海。自关东北循海有道，道狭处才数尺，旁皆乱山，高峻不可越。比至进牛口，旧置八防御军，募土兵守之。',
      [],when='幽州旧制；设防起始年未载',place='渝关、渝水、进牛口',year=None,
      note='“初”“旧置”均为追叙，未据此绘制现代坐标或915—917年的国界。')
event('youzhou_frontier_defense','幽州边军凭险清野、守隘抵御契丹',4,
      '每岁早获，清野坚壁以待契丹，契丹至，辄闭壁不战，俟其去，选骁勇据隘邀之，契丹常失利走。',
      [],when='旧防御制度；具体年份未载',place='幽州北边',year=None,
      note='这段是反复性的边防方式，不拆成每年都有一次的虚构战役。')
event('zhou_dewei_loses_yuguan_barrier','周德威任卢龙节度使后不修边备，渝关失险',4,
      '及周德威为卢龙节度使，恃勇不修边备，遂失渝关之险，契丹每刍牧于营、平之间。',
      [('周德威','被主书评为不修边备的卢龙节度使')],
      when='周德威任卢龙节度使期间；确年未载',place='渝关、营州、平州',year=None,
      note='“遂失渝关之险”系主书因果评价，先保留原文说法，不转成有确日的失关战役。')
claim('person',people['周德威'],'description',
      '《通鉴》并称周德威忌幽州旧将有名者，常杀之。',4,
      '德威又忌幽州旧将有名者，往往杀之。',
      '未具名、未给具体年月，不新建被杀人物或多起定年事件。')

# p005: diplomacy, rejected plan, Newzhou capture, Jin counterattack and Khitan relief.
event('wu_sends_naphtha_to_khitan','吴王遣使赠契丹猛火油',5,
      '吴王遣使遗契丹主以猛火油，曰：“攻城，以此油然火焚楼橹，敌以水沃之，火愈炽。”',
      [('吴王','遣使献猛火油的吴王'),('契丹主','受猛火油的契丹君主')],
      when='917年三月前；确日未载',place='吴、契丹',
      note='使者未具名；只记录史书对猛火油性质的叙述，不现代化推断配方。')
event('shulv_ping_stops_yuzhou_oil_assault','阿保机拟以三万骑攻幽州，述律后劝止',5,
      '契丹主大喜，即选骑三万欲攻幽州，述律后哂之曰：“岂有试油而攻一国乎！”',
      [('阿保机','拟选三万骑攻幽州的契丹主'),('述律后','反对以油试攻幽州的皇后')],
      when='917年三月前；确日未载',place='幽州',
      note='“欲攻”是计划，不当作此时三万骑已围城；三万为主书所载预选兵数。')
claim('event','event_zztj_269_0917_shulv_ping_stops_yuzhou_oil_assault','description',
      '《辽史》述律氏传亦记吴献猛火油、太祖拟出三万骑而后劝止。',5,
      '太祖選三萬騎以攻幽州，后曰：「豈有試油而攻人國者？」',
      '《辽史》将献油者称“呉主李掞”，主书仅称吴王；不据疑名更换已存吴王主体。',liao71,'corroborates')
event('lu_wenjin_khitan_takes_newzhou','卢文进引契丹急攻新州，安金全弃城',5,
      '三月，卢文进引契丹兵急攻新州，刺史安金全不能守，弃城走。',
      [('卢文进','引契丹兵攻新州者'),('安金全','不能守新州而弃城的晋刺史')],
      when='917年三月；确日未载',place='新州',
      note='承上段卢文进奔契丹；这是另一次引兵攻新州，不合并为祁沟关叛乱当日。')
claim('event','event_zztj_269_0917_lu_wenjin_khitan_takes_newzhou','description',
      '《辽史》卷一也记契丹攻新州、安金全遁。',5,
      '進攻其城，刺史安金全遁',
      '辽史将时间系神册二年春二月，与主书三月不同；并列保留。',liao01,'conflicts')
event('liu_yin_newzhou_prefect','卢文进任部将刘殷为新州刺史',5,
      '文进以其部将刘殷为刺史，使守之。',
      [('卢文进','任刘殷守新州的契丹依附将领'),('刘殷','被任为新州刺史的卢文进部将')],place='新州',
      note='主书说卢文进任其部将守城，不将此任命直接归给阿保机。')
event('zhou_dewei_counterattack_newzhou_fails','周德威合晋三镇军攻新州，旬日未克',5,
      '晋王使周德威合河东、镇、定之兵攻之，旬日不克。',
      [('李存勖','命周德威反攻新州的晋王'),('周德威','率河东镇定军攻新州未克者')],
      when='917年三月；围攻约旬日，确起讫未载',place='新州',
      note='“旬日不克”不等于城被晋军夺回。')
event('khitan_relief_defeats_zhou_dewei','阿保机率大军援新州，周德威败归',5,
      '契丹主帅众三十万救之，德威众寡不敌，大为契丹所败，奔归。',
      [('阿保机','率契丹军援新州的君主'),('周德威','败于契丹军而退的晋将')],place='新州',
      note='三十万为主书所载兵数，不当作核实规模；后续围幽州在下一段。')
claim('event','event_zztj_269_0917_khitan_relief_defeats_zhou_dewei','description',
      '《旧五代史》庄宗纪记周德威攻新州、契丹援军来后晋军败退。',5,
      '帝命周德威率兵三萬攻之，營於城東。俄而文進引契丹大至，德威拔營而歸，因為契丹追躡，師徒多喪。',
      '旧书所说晋军三万与主书契丹号三十万为不同方兵数；不互相替换。',old28,'corroborates')

# p006: Ma Cun is already a published person and the sibling relation already exists.
event('ma_cun_raid_shanggao','楚王马殷遣弟马存攻吴上高，掳获后返',6,
      '楚王殷遣其弟存攻吴上高，俘获而还。',
      [('马殷','遣弟攻吴上高的楚王'),('马存','率军攻吴上高并携俘返楚者')],place='上高',
      note='“俘获”不具数目，不推断已占领上高；马存复用既有人物主体。')
claim('person',people['马存'],'description','《旧五代史》卷三十二亦称马存为湖南马殷之弟。',6,
      '存，湖南馬殷之弟也。','补独立书证确认主书“殷弟存”之姓名。',old32,'corroborates')
rel='relationship_person_马殷_person_马存_兄长'
B['person_relationships'].append(dict(key=rel,person_a_key=people['马殷'],person_b_key=people['马存'],
    relation_type='兄长',description='马殷是马存的兄长。',status='draft'))
reused.add(rel)
claim('person_relationship',rel,'description','马殷是马存的兄长。',6,
      '楚王殷遣其弟存攻吴上高','本段明言马存为马殷弟；复用既有方向与关系键。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(4, 7):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269贞明三年第4—6段；旧幽州边防追叙、吴献油及契丹新州战事、马存攻上高。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=917,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(4,7)],
    next_paragraph=Q[7]['id'],coverage='卷269贞明三年第4—6段；幽州北边旧防、吴契丹往来、新州战事及楚吴上高之役。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[4]['id'],'note':'渝关八防御军及周德威失险是“初”起的追叙，不定在917年；地名不作无证坐标。'},
      {'paragraph_id':Q[5]['id'],'note':'献猛火油时太祖拟攻幽州仅是计划；辽史系契丹攻新州于二月，通鉴系三月，月份并列。三十万为记载兵数。'},
      {'paragraph_id':Q[6]['id'],'note':'马存为已存人物、马殷之弟，复用兄长关系；上高之役只记俘获而返，不记领土改变。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
