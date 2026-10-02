"""Curate consecutive Tongjian volume 270, year 918, paragraphs 16–18."""
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
    ('tongjian-270-918-xu-zhixun-end', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-04/sources/library/tongjian-270-918-xu-zhixun-end', 'b2190309', '司马光等'),
    ('jiuwudaishi-028-yangliu-river', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-02/sources/library/jiuwudaishi-028-yangliu-river', '26b19a11', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p016-p018',
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
for n in (16, 17, 18):
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
    ck = f'claim_zztj_270_0918_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'晋王':'李存勖', '蜀主':'王宗衍', '宗弼':'王宗弼', '宗瑶':'王宗瑶',
            '宗绾':'王宗绾', '宗播':'许存', '王宗播':'许存', '宗裔':'王宗裔',
            '宗夔':'王宗夔', '宗黯':'王宗黯'}.get(name, name)
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

event('li_cunxu_surveys_yangliu_river', '晋王李存勖六月壬戌到杨刘察河水', 16,
      '壬戌，晋王自魏州劳军于杨刘，自泛舟测河水，其深没枪。',
      [('晋王','自魏州到杨刘并测河者')], when='918年六月壬戌', place='杨刘',
      note='月份由《旧五代史》卷28对应壬戌条核对；主书上承六月。')
claim('event','event_zztj_270_0918_li_cunxu_surveys_yangliu_river','time_original',
      '《旧五代史》卷二十八记六月壬戌晋王自魏州复至杨刘。',16,
      '六月壬戌，帝自魏州復至楊劉。',
      '明确六月；与二月谢彦章筑垒决水不是同一次行动。',
      'jiuwudaishi-028-yangliu-river','corroborates')
event('li_cunxu_crosses_yangliu', '晋王李存勖六月甲子率军涉水攻梁阵', 16,
      '甲子，王引亲军先涉，诸军随之，褰甲横枪，结陈而进。',
      [('晋王','率亲军先涉河者')], when='918年六月甲子',place='杨刘河上',
      note='涉水进攻与先前二月围城分开。')
event('liang_defeated_yangliu', '杨刘河中交战梁军败，谢彦章脱身，晋取滨河四寨', 16,
      '晋兵因而乘之，梁兵大败，死伤不可胜纪，河水为之赤，彦章仅以身免。是日，晋人遂陷滨河四寨。',
      [('谢彦章','梁军临岸迎战并败退脱身者'),('晋王','晋军主帅')],
      when='918年六月甲子',place='杨刘河上及滨河四寨',
      note='只录主书明确的梁军败退、谢彦章脱身和四寨失守；伤亡数不可量化。')
claim('event','event_zztj_270_0918_liang_defeated_yangliu','description',
      '《旧五代史》卷二十八记梁军中流大败、谢彦章仅免。',16,
      '交鬥於中流，梁軍大敗，殺傷甚眾，河水如絳，謝彥章僅得免去。',
      '补书记载与主书相近，均不提供确切伤亡人数。',
      'jiuwudaishi-028-yangliu-river','corroborates')

event('zhang_ge_first_demoted', '蜀贬张格为茂州刺史，并贬杨玢等人',17,
      '庚午，贬格为茂州刺史，玢为荣经尉。吏部侍郎许寂、户部侍郎潘峤皆坐格党贬官。',
      [('张格','由宰相贬为茂州刺史者'),('杨玢','贬为荣经尉者'),
       ('许寂','因张格党贬官者'),('潘峤','因张格党贬官者')],
      when='918年六月庚午；上承六月条',place='蜀',
      note='初贬与后来的维州司户、合水镇调徙分开。')
event('zhang_ge_further_demoted', '张格再贬维州司户，庾凝绩奏徙合水镇',17,
      '格寻再贬维州司户，庾凝绩又奏徙格于合水镇，令茂州刺史顾承郾伺格阴事。',
      [('张格','再贬并被奏徙者'),('庾凝绩','奏徙张格并令顾承郾伺察者'),('顾承郾','被令伺察张格者')],
      when='918年庚午后；确日未载',place='维州、合水镇、茂州',
      note='奏徙与伺察不等于张格已被杀；顾承郾后因公事获罪。')
claim('event','event_zztj_270_0918_zhang_ge_further_demoted','description',
      '王宗侃妻劝顾承郾母阻止儿子为人报仇，承郾听从，庾凝绩后因公事抵承郾罪。',17,
      '承郾从之。凝绩怒，因公事抵承郾罪。',
      '不把王宗侃妻的行为误记为已救张格出狱，也不将抵罪解释为处死。')

event('shu_princes_created_july', '蜀主七月封王宗弼等人为王',18,
      '秋，七月，壬申朔，蜀主以兼中书令王宗弼为巨鹿王，宗瑶为临淄王，宗绾为临洮王，宗播为临颍王，宗裔、宗夔及兼侍中宗黯皆为琅邪郡王。甲戌，以王宗侃为乐安王。',
      [('蜀主','颁封王诏者'),('王宗弼','封巨鹿王者'),('宗瑶','封临淄王者'),
       ('宗绾','封临洮王者'),('宗播','封临颍王者'),('宗裔','封琅邪郡王者'),
       ('宗夔','封琅邪郡王者'),('宗黯','封琅邪郡王者'),('王宗侃','甲戌封乐安王者')],
      when='918年七月壬申朔及甲戌',place='蜀',
      note='壬申与甲戌是两次封王日次；逐人角色注明，不将全部封王压在同一天。')
event('yu_chuansu_appointed_shu_chancellor', '蜀七月丙子任庾传素为同平章事',18,
      '丙子，以兵部尚书庾传素为太子少保兼中书侍郎、同平章事。',
      [('庾传素','由兵部尚书任太子少保兼中书侍郎同平章事者')],
      when='918年七月丙子',place='蜀',
      note='按本句列出官职，不将人名庾传素与庾凝绩混同。')
claim('person',person('王宗弼',18,'七月后主导蜀廷任免者','蜀主不亲政事，内外迁除皆出于王宗弼。'),
      'description','《资治通鉴》称蜀主不亲政事、王宗弼主导内外迁除，并评其纳贿多私。',18,
      '宗弼纳贿多私，上下咨怨。',
      '这是主书对其执政的评价，未具体指认某一次收贿。')
claim('person',person('宋光嗣',18,'受蜀主宠任者','宋光嗣通敏善希合，蜀主宠任之，蜀由是遂衰。'),
      'description','《资治通鉴》记蜀主宠任宋光嗣，并以此解释蜀政衰落。',18,
      '宋光嗣通敏善希合，蜀主宠任之，蜀由是遂衰。',
      '“由是遂衰”是史家因果评断，不误作可逐日定位的事件。')
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in (16, 17, 18):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明四年第16—18段；杨刘渡河交战、蜀臣贬官及七月封王任官。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=918,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in (16, 17, 18)], next_paragraph=Q[19]['id'],
    coverage='卷270贞明四年第16—18段；杨刘渡河战、蜀廷张格贬谪与七月封王任官。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[16]['id'], 'note': '旧五代史卷28将杨刘渡河交战系六月，与此前二月筑垒决河分开。'},
      {'paragraph_id': Q[17]['id'], 'note': '张格贬官多次分录；顾承郾伺察、庾凝绩后抵罪不推断已杀张格。'},
      {'paragraph_id': Q[18]['id'], 'note': '宗播复用既有许存主体和王宗播别名；诸王封号依原文逐人关联。纳贿及蜀衰为史书评价，非具体收赃案。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
