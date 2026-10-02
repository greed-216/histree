"""Curate consecutive Tongjian volume 270, year 918, paragraphs 36–38."""
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
    ('tongjian-270-918-autumn', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-07/sources/library/tongjian-270-918-autumn', '011a5623', '司马光等'),
    ('tongjian-270-918-year-end', P / 'sources/library/tongjian-270-918-year-end', '652cec40', '司马光等'),
    ('jiuwudaishi-028-huliupo', P / 'sources/library/jiuwudaishi-028-huliupo', '652cec40', '薛居正等'),
    ('xinwudaishi-063-qiande', P / 'sources/library/xinwudaishi-063-qiande', '652cec40', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p036-p038',
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
for n in range(36, 39):
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
    ck = f'claim_zztj_270_0918_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'晋王':'李存勖','蜀主':'王宗衍','硃珪':'朱珪',
            '彦章':'谢彦章','瑰':'贺瑰'}.get(name, name)
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

event('he_gui_kills_xie_yanzhang', '贺瑰与朱珪伏甲杀谢彦章等三名梁将',36,
      '瑰益疑之，密谮之于帝，与行营马步都虞候曹州刺史硃珪谋，因享士，伏甲，杀彦章及濮州刺史孟审澄、别将侯温裕，以谋叛闻。',
      [('贺瑰','疑忌谢彦章、密奏并谋杀者'),('硃珪','与贺瑰共谋杀害者'),
       ('谢彦章','被杀梁骑将'),('孟审澄','被杀濮州刺史'),('侯温裕','被杀别将')],
      when='918年十二月丁未前；确日未载',place='梁军行营',
      note='“通晋”是贺瑰怀疑，“谋叛”是上报说辞，不视为谢彦章等已证实叛乱。')
claim('event','event_zztj_270_0918_he_gui_kills_xie_yanzhang','description',
      '《旧五代史》卷二十八也记贺瑰在军中杀谢彦章。',36,
      '時梁將賀瑰殺騎將謝彥章於軍',
      '补书记杀谢彦章主干，未在此段列孟审澄、侯温裕。',
      'jiuwudaishi-028-huliupo','corroborates')
event('zhu_gui_promoted_after_killings', '梁先后任朱珪为匡国留后、平卢节度使',36,
      '丁未，以硃珪为匡国留后，癸丑，又以为平卢节度使兼行营马步副指挥使以赏之。',
      [('硃珪','因贺瑰杀将事获两次赏任者')],
      when='918年十二月丁未、癸丑',place='梁',
      note='两次任命相隔数日，按主书原字硃珪定位，显示沿用朱珪规范名。')

event('li_cunxu_rejects_zhou_dewei_advice', '晋王欲趋大梁，周德威劝慎行而未获采纳',37,
      '王欲自将万骑直趣大梁，周德威曰：“梁人虽屠上将，其军尚全，轻行徼利，未见其福。”不从。',
      [('晋王','欲率万骑趋大梁并未采劝者'),('周德威','劝其勿轻行者')],
      when='918年十二月谢彦章死后；确日未载',place='晋军营、赴大梁方向',
      note='周德威警告梁军尚全，不把晋王的进攻愿望记为已攻抵大梁。')
event('li_cunxu_sends_noncombatants_back', '晋王十二月戊午令军中老弱归魏州',37,
      '戊午，下令军中老弱悉归魏州',
      [('晋王','下令遣返军中老弱者')],
      when='918年十二月戊午',place='魏州',
      note='老弱归魏州是军队整备动作，不将“众号十万”视为精确人数。')
event('li_cunxu_breaks_camp_advances', '晋王十二月庚申毁营趋汴',37,
      '庚申，毁营而进，众号十万。',
      [('晋王','率晋军毁营进兵者')],
      when='918年十二月庚申',place='趋汴州方向',
      note='“众号十万”是史书称号数，不与其他诸军数字机械相加。')
claim('event','event_zztj_270_0918_li_cunxu_breaks_camp_advances','description',
      '《旧五代史》卷二十八亦记戊午遣老幼、庚申毁营进军。',37,
      '戊午，下令軍中老幼，令歸魏州，悉兵以趣汴。庚申，大軍毀營而進。',
      '补书记两个干支动作；主书作老弱，旧书作老幼，保留原字。',
      'jiuwudaishi-028-huliupo','corroborates')

event('shu_announces_qiande_era', '蜀十二月辛酉宣布明年改元乾德',38,
      '辛酉，蜀改明年元曰乾德。',
      [('蜀主','在位期间颁布明年乾德年号者')],
      when='918年十二月辛酉宣布；919年起用乾德',place='蜀',
      note='主书“明年”明确指919年，本事件是918年的改元宣布。')
claim('event','event_zztj_270_0918_shu_announces_qiande_era','description',
      '《新五代史》卷六十三记王宗衍即位次年改元乾德。',38,
      '衍立之明年，改元乾德。',
      '918年继位、次年919年乾德元年，和主书“明年”相合。',
      'xinwudaishi-063-qiande','corroborates')
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(36, 39):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明四年第36—38段；贺瑰杀谢彦章、晋王十二月进兵和蜀改明年元。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=918,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(36, 39)], next_paragraph=Q[39]['id'],
    coverage='卷270贞明四年第36—38段；贺瑰杀谢彦章等骑将、晋王决定进兵、蜀宣布来年乾德元号。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[36]['id'], 'note': '贺瑰疑谢彦章通晋是其猜疑和密奏，不记为查实叛谋；杀三将与朱珪赏任分录。'},
      {'paragraph_id': Q[37]['id'], 'note': '晋王未采周德威谨慎建议，戊午遣老弱归魏州、庚申毁营进兵分开。'},
      {'paragraph_id': Q[38]['id'], 'note': '辛酉宣布“明年”改元乾德，对应919年，不将乾德元年误写为918年。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
