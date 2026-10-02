"""Curate consecutive Tongjian volume 270, year 918, paragraphs 23–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 45))
specs = [
    ('tongjian-270-918-summer-autumn', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-06/sources/library/tongjian-270-918-summer-autumn', '66164588', '司马光等'),
    ('tongjian-270-918-autumn', P / 'sources/library/tongjian-270-918-autumn', '011a5623', '司马光等'),
    ('jiuwudaishi-028-autumn', P / 'sources/library/jiuwudaishi-028-autumn', '011a5623', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p023-p028',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
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
for n in range(23, 29):
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
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明四年（918）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0918_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'晋王':'李存勖','赵王镕':'王镕','李存审':'符存审','李绍荣':'元行钦',
            '谢彦章':'谢彦章','光葆':'宋光葆','晃':'欧阳晃'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷270贞明四年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='918年本段条；确日未载', note='', year=918, place='吴'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0918_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '主书本段未明标月日；他书记载作独立引文，不覆盖主书。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0918_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('zhang_wanjin_joins_jin', '张万进八月己酉遣使附晋并求援',23,
      '万进闻晋兵将出，己酉，遣使附于晋，且求援。',
      [('张万进','遣使附晋并求援者')],when='918年八月己酉；上承八月条',place='兖州、晋',
      note='“轻险好乱”与嬖幸求赂为史书评价和背景，不记作确定的单一叛变动机。')
claim('event','event_zztj_270_0918_zhang_wanjin_joins_jin','time_original',
      '《旧五代史》卷二十八亦记己酉张万进遣使归晋。',23,
      '己酉，梁兗州節度使張萬進遣使歸款。',
      '补书记日次与主书相合；旧书保留繁体“兗”。',
      'jiuwudaishi-028-autumn','corroborates')
event('liu_xun_sent_against_zhang_wanjin', '梁任刘鄩为兖州安抚制置使讨张万进',23,
      '以亳州团练使刘鄩为兗州安抚制置使，将兵讨之。',
      [('刘鄩','受梁命率兵讨张万进者'),('张万进','被讨伐者')],
      when='918年八月己酉后；确日未载',place='兗州',
      note='任命与讨伐是主书记载；不提前写后续胜败。')

event('shu_shunde_empress_dies', '蜀顺德皇后八月甲子去世',24,
      '甲子，蜀顺德皇后殂。',
      [('蜀顺德皇后','去世的蜀后')],when='918年八月甲子；上承八月条',place='蜀',
      note='主书本段仅提供谥号称谓；姓名、亲属身份待其他书证核对。')
claim('person',person('蜀顺德皇后',24,'本段称蜀顺德皇后；姓名未载','甲子，蜀顺德皇后殂。'),
      'death_year','918年去世。',24,'甲子，蜀顺德皇后殂。',
      '按本年编年条记死亡年，不凭称号与其他周氏合并。')
next(row for row in B['people'] if row['key']=='person_蜀顺德皇后')['death_year']=918

event('shu_eunuchs_given_military_posts', '蜀主乙丑授王廷绍等六人将军、军使职',25,
      '乙丑，蜀主以内给事王廷绍、欧阳晃、李周辂、宋光葆、宋承蕴、田鲁俦等为将军及军使',
      [('王廷绍','受任将军或军使者'),('欧阳晃','受任将军或军使者'),('李周辂','受任将军或军使者'),
       ('宋光葆','受任将军或军使者'),('宋承蕴','受任将军或军使者'),('田鲁俦','受任将军或军使者')],
      when='918年八月乙丑',place='蜀',
      note='原书“将军及军使”未逐人对应具体职名，角色不擅配官。')
event('zhou_xiang_admonishes_shu', '周庠谏蜀主任用内给事，蜀主不听',25,
      '皆干预政事，骄纵贪暴，大为蜀患，周庠切谏，不听。',
      [('周庠','切谏者')],when='918年八月乙丑后；确日未载',place='蜀',
      note='“骄纵贪暴”是主书整体评价，未分配到每人的具体罪行。')
event('ouyang_huang_sets_fire', '欧阳晃纵火焚邻近军营以扩住宅，蜀主未问',25,
      '晃患所居之隘，夜，因风纵火，焚西邻军营数百间，明旦，召匠广其居；蜀主亦不之问。',
      [('欧阳晃','因扩住宅而纵火者')],
      when='918年本段记事；确日未载',place='蜀军营',
      note='军营数百间为史书规模描述；未推算死伤。')
pa=person('宋光葆',25,'宋光嗣的从弟','光葆，光嗣之从弟也。')
pb=person('宋光嗣',25,'宋光葆的从兄','光葆，光嗣之从弟也。')
rk='relationship_zztj_270_0918_song_guangbao_younger_cousin'
B['person_relationships'].append(dict(key=rk,person_a_key=pa,person_b_key=pb,
    relation_type='从弟',description='宋光葆是宋光嗣的从弟。',status='draft'))
claim('person_relationship',rk,'description','宋光葆是宋光嗣的从弟。',25,
      '光葆，光嗣之从弟也。','按 A→B 表示 A 是 B 的从弟；不用宽泛“兄弟”替代。')

event('jin_liang_faceoff_majia', '晋军屯麻家渡，梁贺瑰、谢彦章屯行台村对峙',26,
      '晋王自魏州如杨刘，引兵略郓、濮而还，循河而上，军于麻家渡。贺瑰、谢彦章将梁兵屯濮州北行台村，相持不战。',
      [('晋王','率晋军屯麻家渡者'),('贺瑰','梁军行台村主将之一'),('谢彦章','梁军行台村主将之一')],
      when='918年八月前后；确日未载',place='麻家渡、濮州北行台村',
      note='史载两军驻地；不自行比附现代坐标。')
claim('event','event_zztj_270_0918_jin_liang_faceoff_majia','description',
      '《旧五代史》卷二十八亦记晋军营麻家渡、梁军屯行台村。',26,
      '遂營於麻家渡，諸陣列營十數。梁將賀瑰、謝彥章以軍屯濮州行台村',
      '两军对峙位置与主书相符，旧书称相持百余日属后续总述。',
      'jiuwudaishi-028-autumn','corroborates')
event('li_cunxu_ambushed_at_dike', '晋王李存勖轻骑近梁营遭谢彦章伏兵，符存审救出',26,
      '谢彦章伏精甲五千于堤下；王引十馀骑度堤，伏兵发，围王数十重，王力战于中，后骑继之者攻之于外，仅得出。会李存审救至，梁兵乃退',
      [('谢彦章','梁军设伏者'),('晋王','遭伏击并脱身者'),('李存审','率军救援晋王者')],
      when='918年八月后本段叙事；确日未载',place='濮州北行台村附近河堤',
      note='李存审复用符存审主体；五千、十余骑为史书所述规模。')
claim('event','event_zztj_270_0918_li_cunxu_ambushed_at_dike','description',
      '《旧五代史》卷二十八也记谢彦章伏兵堤下、晋王过堤受围。',26,
      '謝彥章率精兵五千伏於堤下，帝以十餘騎登堤，伏兵發，圍帝十數重。',
      '补书详略与主书不同，但可互核伏击主干。',
      'jiuwudaishi-028-autumn','corroborates')

event('zhang_xuan_raids_chu_guting', '吴将张宣夜袭古亭楚军并取胜',27,
      '吴刘信遣其将张宣等夜将兵三千袭楚将张可求于古亭，破之',
      [('刘信','遣张宣出兵者'),('张宣','率三千兵夜袭者'),('张可求','古亭被袭的楚将')],
      when='918年八月后本段叙事；确日未载',place='古亭',
      note='张宣等夜袭破楚军；人数为原文数字，不据此推算实际伤亡。')
event('wuyue_min_withdraw_from_qianzhou_relief', '吴越、闽援兵闻楚军败而撤回',27,
      '又遣梁诠等将兵击吴越及闽兵，二国闻楚兵败，俱引归。',
      [('梁诠','受刘信派遣攻吴越及闽援兵者')],
      when='918年古亭夜袭后；确日未载',place='虔州外围',
      note='主书说两国闻楚兵败后撤回，未说吴军已在正面歼灭两军。')

event('meishan_raid_shaozhou', '梅山蛮攻邵州，楚将樊须击退',28,
      '梅山蛮寇邵州，楚将樊须击走之。',
      [('樊须','率楚军击退来犯者')],
      when='918年八月后本段条；确日未载',place='邵州',
      note='“梅山蛮”为史书所用集体称谓，不建单一人物；后续地理待核。')
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(23, 29):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明四年第23—28段；张万进附晋、蜀宫政事、麻家渡对峙与吴军援虔。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=918,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(23, 29)], next_paragraph=Q[29]['id'],
    coverage='卷270贞明四年第23—28段；张万进附晋、蜀顺德皇后去世与宫臣、麻家渡对峙、吴军古亭夜袭。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[23]['id'], 'note': '张万进附晋与刘鄩奉梁命讨伐分录；旧五代史卷28也记己酉归款。'},
      {'paragraph_id': Q[24]['id'], 'note': '主书仅称蜀顺德皇后，个人名及与其他周氏的同一性未有本段证据，暂以称号建主体。'},
      {'paragraph_id': Q[25]['id'], 'note': '宋光葆为宋光嗣从弟有原文明证，按前者指向后者建立“从弟”关系。'},
      {'paragraph_id': Q[26]['id'], 'note': '晋王多次轻骑挑战为背景，谢彦章伏兵和李存审救援为本段具体经过；旧五代史卷28有同事补证。'},
      {'paragraph_id': Q[27]['id'], 'note': '吴将张宣夜袭破楚军后，吴越与闽军闻败引归；不记为同时被吴军正面击败。'},
      {'paragraph_id': Q[28]['id'], 'note': '梅山蛮是史书集体称谓，不据此建单一人物。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
