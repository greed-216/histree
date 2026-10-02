"""Curate consecutive Tongjian volume 270, year 918, paragraphs 14–15."""
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
    ('tongjian-270-918-spring', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-02/sources/library/tongjian-270-918-spring', '4138a6db', '司马光等'),
    ('tongjian-270-918-xu-zhixun-middle', P / 'sources/library/tongjian-270-918-xu-zhixun-middle', 'b2190309', '司马光等'),
    ('tongjian-270-918-xu-zhixun-end', P / 'sources/library/tongjian-270-918-xu-zhixun-end', 'b2190309', '司马光等'),
    ('xinwudaishi-061-xu-zhixun-chronology', P / 'sources/library/xinwudaishi-061-xu-zhixun-chronology', 'b2190309', '欧阳修'),
    ('xinwudaishi-042-zhu-jin-killing', P / 'sources/library/xinwudaishi-042-zhu-jin-killing', 'b2190309', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p014-p015',
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
for n in (14, 15):
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
    ck = f'claim_zztj_270_0918_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'硃瑾':'朱瑾', '瑾':'朱瑾', '吴王':'杨隆演', '隆演':'杨隆演', '温':'徐温',
            '知训':'徐知训', '知诰':'李昪', '徐知诰':'李昪', '志诚':'米志诚'}.get(name, name)
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

# The first episodes in paragraph 14 are retrospective, with no stated date.
event('xu_zhixun_threatens_li_decheng', '徐知训向使者扬言杀李德诚', 14,
      '知训怒，谓使者曰：“会当杀德诚，并其妻取之！”',
      [('徐知训','向使者扬言杀李德诚者'),('李德诚','被威胁者')],
      when='918年本段追叙；确年未载', year=None,
      note='扬言杀害不等于已经杀害；发生年未载。')
event('xu_zhixun_humiliates_wu_king', '徐知训多次凌侮吴王杨隆演', 14,
      '知训狎侮吴王，无复君臣之礼。',
      [('徐知训','凌侮吴王者'),('吴王','受凌侮的吴王')],
      when='918年本段追叙；确年未载', year=None,
      note='本段接举多次旧事，不强定都发生于918年。')
event('xu_zhixun_plots_against_xu_zhigao', '徐知训伏甲欲杀徐知诰，刁彦能放其离去', 14,
      '又尝与知诰饮，伏甲欲杀之，知谏蹑知诰足，知诰阳起如厕，遁去，知训以剑授左右刁彦能使追杀之。彦能驰骑及于中涂，举剑示知诰而还，以不及告。',
      [('徐知训','授剑命追杀者'),('徐知诰','得以脱身者'),('刁彦能','追及却放其离去者')],
      when='918年本段追叙；确年未载', year=None,
      note='原文指伏甲与追杀未遂；不记为已杀徐知诰。')
event('xu_zhixun_moves_zhu_jin', '徐知训置静淮军并出朱瑾任节度使', 14,
      '知训恶瑾位加己上，置静淮军于泗州，出瑾为静淮节度使，瑾益恨之',
      [('徐知训','置静淮军并出朱瑾者'),('瑾','出任静淮节度使者')],
      when='918年本段追叙；确月日未载',
      note='“瑾”指本段前文“硃瑾”；规范主体沿用朱瑾，原文保留异体。')
event('zhu_jin_kills_xu_zhixun', '朱瑾设伏杀徐知训', 14,
      '知训答拜，瑾以笏自后击之踣地，呼壮士出斩之。',
      [('朱瑾','设伏并杀徐知训者'),('徐知训','被杀者')],
      when='918年本段条；确月日有异说',
      note='主书本段未注明月份，新五代史卷61作吴天祐十五年四月；不能仅据段落位置判定两书日期相冲突。')
claim('event', 'event_zztj_270_0918_zhu_jin_kills_xu_zhixun', 'time_original',
      '《新五代史》卷六十一将朱瑾杀徐知训记在吴天祐十五年四月。', 14,
      '四月，副都統朱瑾殺徐知訓，瑾自殺。',
      '主书本段没有明标月份；排列在六月叙事后不构成确定的日期冲突。',
      'xinwudaishi-061-xu-zhixun-chronology', 'adds')
claim('event', 'event_zztj_270_0918_zhu_jin_kills_xu_zhixun', 'description',
      '《新五代史》卷四十二亦记朱瑾设伏以笏击徐知训、伏兵杀之。', 14,
      '知訓方拜，瑾以笏擊踣之，伏兵自戶突出，殺之。',
      '该书独立记载杀害动作；原文繁体不改。',
      'xinwudaishi-042-zhu-jin-killing', 'corroborates')
event('zhu_jin_suicide', '朱瑾向吴王示徐知训首级后自刭', 14,
      '乃自后逾城，坠而折足，顾追者曰：“吾为万人除害，以一身任患。”遂自刭。',
      [('朱瑾','逾城折足后自刭者')],
      when='918年本段条；确月日有异说',
      note='《新五代史》卷61记四月；此处不将吴王不知情解释为事前同谋。')
claim('event', 'event_zztj_270_0918_zhu_jin_suicide', 'description',
      '《新五代史》卷四十二也记朱瑾逾垣折足后自刎。', 14,
      '因踰垣，折其足。瑾顧路窮',
      '该书下文紧接“遂自刎”；摘录与快照可回查。',
      'xinwudaishi-042-zhu-jin-killing', 'corroborates')

event('xu_zhigao_takes_wu_government', '徐知诰从润州渡江并接掌吴政', 15,
      '徐知诰在润州闻难，用宋齐丘策，即日引兵济江。瑾已死，因抚定军府。时徐温诸子皆弱，温乃以知诰代知训执吴政',
      [('徐知诰','自润州引兵渡江并接掌吴政者'),('宋齐丘','提出渡江建议者'),('徐温','令徐知诰代徐知训者')],
      when='918年朱瑾杀徐知训后；确日未载',
      note='徐知诰所接的是徐知训吴政职位；与徐温收养关系待单独证据。')
claim('event', 'event_zztj_270_0918_xu_zhigao_takes_wu_government', 'description',
      '《新五代史》卷六十一记徐知诰从润州率兵入，遂秉政。', 15,
      '潤州徐知誥聞亂，率兵入',
      '补书将“遂秉政”接于此句，和主书吴政接管相合。',
      'xinwudaishi-061-xu-zhixun-chronology', 'corroborates')
event('xu_wen_punishes_zhu_jin_family', '徐温沉朱瑾尸于雷塘并灭其族', 15,
      '沉硃瑾尸于雷塘而灭其族。',
      [('徐温','下令沉尸并灭朱瑾家族者'),('硃瑾','死后尸体遭沉雷塘者')],
      when='918年徐知训被杀后；确日未载', place='雷塘',
      note='本句主语承接“温乃”，不写为徐知诰所为；硃与朱同一主体。')
event('xu_wen_kills_li_yan', '徐温疑李俨与朱瑾通谋而杀之', 15,
      '宣谕使李俨贫困，寓居海陵。温疑其与瑾通谋，皆杀之。',
      [('徐温','因怀疑通谋而杀李俨者'),('李俨','遭杀的宣谕使')],
      when='918年朱瑾杀徐知训后；确日未载',place='海陵、吴',
      note='“通谋”是徐温的怀疑，不写为已证实的共谋。')
event('yan_keqiu_traps_mi_zhicheng', '严可求诈称袁州胜楚，伏兵擒斩米志诚及其子', 15,
      '严可求恐志诚不受命，诈称袁州大破楚兵，将吏皆入贺，伏壮士于戟门，擒志诚，斩之，并其诸子。',
      [('严可求','设计伏兵者'),('米志诚','被擒斩者')],
      when='918年朱瑾杀徐知训后；确日未载',
      note='“袁州大破楚兵”是严可求用于诱捕的假消息，不建成胜楚事件。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in (14, 15):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明四年第14—15段；徐知训之死及徐知诰接掌吴政，繁简异体合并；新史四月说并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=918,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in (14, 15)], next_paragraph=Q[16]['id'],
    coverage='卷270贞明四年第14—15段；徐知训凌侮吴王之追叙、朱瑾杀知训与自杀、徐知诰接掌吴政。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[14]['id'], 'note': '硃瑾与既有朱瑾同一主体；徐知诰复用既有李昪主体及其徐知诰别名，原文字形保留。前半诸旧事无确年。'},
      {'paragraph_id': Q[14]['id'], 'note': '新五代史卷61称吴天祐十五年四月杀徐知训；通鉴本段排于六月王建去世之后但没有明标月，不能仅据段落位置断言矛盾。'},
      {'paragraph_id': Q[15]['id'], 'note': '徐温疑米志诚、李俨通谋，不录为已证实事实；袁州胜楚是严可求诈称。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
