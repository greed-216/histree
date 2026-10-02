"""Curate consecutive Tongjian volume 270, year 918, paragraphs 19–22."""
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
    ('tongjian-270-918-xu-zhigao-tax', P / 'sources/library/tongjian-270-918-xu-zhigao-tax', '66164588', '司马光等'),
    ('tongjian-270-918-summer-autumn', P / 'sources/library/tongjian-270-918-summer-autumn', '66164588', '司马光等'),
    ('xinwudaishi-061-xu-zhixun-chronology', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-04/sources/library/xinwudaishi-061-xu-zhixun-chronology', 'b2190309', '欧阳修'),
    ('xinwudaishi-063-zongding', P / 'sources/library/xinwudaishi-063-zongding', '66164588', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p019-p022',
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
for n in (19, 20, 21, 22):
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
    ck = f'claim_zztj_270_0918_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'知诰':'李昪', '徐知诰':'李昪', '瑾':'朱瑾', '硃瑾':'朱瑾',
            '温':'徐温', '吴王':'杨隆演', '晋王':'李存勖', '蜀主':'王宗衍',
            '传球':'钱传球', '李存审':'符存审', '宗鼎':'王宗鼎'}.get(name, name)
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

event('xu_wen_reconsiders_purge', '徐温听徐知诰、严可求陈述后收敛对吴将的大规模诛戮',19,
      '吴徐温入朝于广陵，疑诸将皆预硃瑾之谋，欲大行诛戮。徐知诰、严可求具陈徐知训过恶，所以致祸之由，温怒稍解',
      [('徐温','原拟大行诛戮、听陈述后怒稍解者'),('徐知诰','陈述徐知训过恶者'),('严可求','陈述徐知训过恶者')],
      when='918年七月前后；确日未载',place='广陵',
      note='这是徐温意图与情绪改变，不能记为已发生大规模诛戮。')
event('xu_wen_reburies_zhu_jin', '徐温命自雷塘捞出朱瑾遗骨安葬',19,
      '乃命网瑾骨于雷塘而葬之',
      [('徐温','下令网骨安葬者'),('朱瑾','遗骨被捞起安葬者')],
      when='918年七月前后；确日未载',place='雷塘',
      note='接续前段徐温沉朱瑾尸于雷塘；先后处置分开记载。')
event('xu_zhigao_appointed_wu_deputy', '吴任徐知诰为淮南节度行军副使等职',19,
      '戊戌，以知诰为淮南节度行军副使、内外马步都军副使、通判府事，兼江州团练使。以徐知谏权润州团练事。',
      [('徐知诰','戊戌受任淮南行军副使等职者'),('徐知谏','权润州团练事者')],
      when='918年七月戊戌；上承七月条',place='吴',
      note='徐知诰沿用既有李昪主体；徐知谏任官同段未另载干支。')
event('xu_zhigao_remits_wu_arrears', '徐知诰奉吴王命免天祐十三年以前逋税',19,
      '以吴王之命，悉蠲天祐十三年以前逋税，馀俟丰年乃输之。',
      [('徐知诰','奉吴王命推行蠲税者'),('吴王','颁蠲税命令者')],
      when='918年徐知诰执吴政后；确日未载',place='吴',
      note='只免天祐十三年以前的逋税，其余待丰年缴纳；不是取消全部税。')
event('song_qiqiu_reforms_wu_tax', '宋齐丘建议免丁口钱并改征谷帛，徐知诰采纳',19,
      '齐丘曰：“安有民富而国家贫者邪！”知诰从之。',
      [('宋齐丘','提出税制改议者'),('徐知诰','采纳宋齐丘建议者')],
      when='918年徐知诰执吴政后；确日未载',place='吴',
      note='上文建议蠲丁口钱、余税输谷帛；“由是国富强”为长期史家评价，不即时记为当年成果。')
claim('event','event_zztj_270_0918_song_qiqiu_reforms_wu_tax','description',
      '宋齐丘建议蠲丁口钱，其余税改输谷帛。',19,
      '请蠲丁口钱；自馀税悉输谷帛',
      '底本同句有私用字，摘录避开该字但源快照原样保留。')
event('xu_wen_limits_song_qiqiu_office', '徐温不愿进用宋齐丘，授其殿直、军判官',19,
      '知诰欲进用齐丘而徐温恶之，以为殿直、军判官。',
      [('徐温','不愿进用宋齐丘而授低职者'),('宋齐丘','任殿直、军判官者')],
      when='918年本段追叙；确日未载',place='吴',
      note='徐温对宋齐丘的态度见主书；不将二人密谈推成具体阴谋。')

event('liu_xin_replaces_wang_qi', '虔州围攻中王祺病，吴以刘信代掌行营',20,
      '虔州险固，吴军攻之，久不下，军中大疫，王祺病，吴以镇南节度使刘信为虔州行营招讨使，未几，祺卒。',
      [('王祺','病倒后不久去世的前行营主帅'),('刘信','接任虔州行营招讨使者')],
      when='918年虔州围攻期间；确日未载',place='虔州',
      note='王祺病、刘信代将、王祺卒是依次发生；不把军疫断为其唯一病因。')
claim('event','event_zztj_270_0918_liu_xin_replaces_wang_qi','description',
      '《新五代史》卷六十一记王祺久攻虔、韶不克，病后由刘信接替。',20,
      '祺病，以劉信代之。',
      '补书简记与主书换将相符；不据此推出确切卒日。',
      'xinwudaishi-061-xu-zhixun-chronology','corroborates')
event('tan_quanbo_requests_relief', '谭全播向吴越、闽、楚求援虔州',20,
      '谭全播求救于吴越、闽、楚。',
      [('谭全播','向三方求援者')],
      when='918年虔州受围期间；确日未载',place='虔州',
      note='求援与各方后来实际出兵分录。')
event('wuyue_chu_min_relieve_qianzhou', '吴越、楚、闽分别出兵策应虔州',20,
      '吴越王镠以统军使传球为西南面行营应援使，将兵二万攻信州；楚将张可求将万人屯古亭，闽兵屯雩都以救之。',
      [('钱镠','任命钱传球出兵者'),('传球','率吴越兵攻信州者'),('张可求','率楚兵屯古亭者')],
      when='918年虔州受围期间；确日未载',place='信州、古亭、雩都',
      note='兵数为史书记载；闽军主帅此句未具名，不补造人物。')
event('zhou_ben_breaks_wuyue_siege', '周本以城楼宴饮疑兵使吴越军夜撤信州之围',20,
      '刺史周本，启关张虚幕于门内，召僚佐登城楼作乐宴饮，飞矢雨集，安坐不动；吴越疑有伏兵，中夜，解围去。',
      [('周本','以虚幕、宴饮示无惧的信州刺史')],
      when='918年虔州受围期间；确日未载',place='信州',
      note='主书称吴越疑有伏兵；未写成周本实际设置伏兵。')
claim('event','event_zztj_270_0918_zhou_ben_breaks_wuyue_siege','description',
      '周本启关张虚幕，并在箭雨中登楼宴饮。',20,
      '刺史周本，启关张虚幕于门内，召僚佐登城楼作乐宴饮',
      '这是史书记载的疑兵动作，不推断吴越军撤退唯一原因。')
event('chen_zhang_wu_counterraid', '吴派陈璋领兵侵苏、湖，钱传球南屯汀州',20,
      '吴以前舒州刺史陈璋为东南面应援招讨使，将兵侵苏、湖，钱传球自信州南屯汀州。',
      [('陈璋','受任东南面应援招讨使并侵苏湖者'),('钱传球','自信州南屯汀州者')],
      when='918年虔州受围期间；确日未载',place='苏州、湖州、汀州',
      note='分录吴军反向侵袭和吴越军南屯，不写成占领苏湖。')

event('jin_mobilizes_for_invasion', '晋王调集周德威、符存审、李嗣源等军准备入寇梁',21,
      '晋王谋大举入寇，周德威将幽州步骑三万，李存审将沧景步骑万人，李嗣源将邢洺步骑万人，王处直遣将将易定步骑万人',
      [('晋王','谋大举入寇并集军者'),('周德威','率幽州步骑者'),('李存审','率沧景步骑者'),
       ('李嗣源','率邢洺步骑者'),('王处直','派将率易定步骑者')],
      when='918年八月大阅前；确日未载',place='魏州及诸镇',
      note='李存审复用符存审主体；兵数为各军原书数字，未简单相加作实际总数。')
event('jin_army_review_wei_zhou', '晋王八月在魏州大会阅兵',21,
      '八月，并河东、魏博之兵，大阅于魏州。',
      [('晋王','组织魏州大阅者')],when='918年八月；确日未载',place='魏州',
      note='主书明确八月大阅；前句谋战与各军会合的确日未载。')

event('wang_zongding_refuses_army_office', '蜀彭王王宗鼎辞领军使，蜀主准许',22,
      '蜀诸王皆领军使，彭王宗鼎谓其昆弟曰：“亲王典兵，祸乱之本。今主少臣强，谗间将兴，缮甲训士，非吾辈所宜为也。”因固辞军使，蜀主许之，但营书舍、植松竹自娱而已。',
      [('王宗鼎','坚辞军使者'),('蜀主','准许辞任者')],
      when='918年本段条；确日未载',place='蜀',
      note='主书称彭王；拒任是本段动作，前述诸王皆领军使是背景。')
claim('person',person('王宗鼎',22,'本段称彭王并辞军使者','彭王宗鼎谓其昆弟曰'),
      'description','《新五代史》卷六十三曾列王宗鼎为鲁王；与本段彭王称号可能分属不同时间。',22,
      '魯王宗鼎，興王宗澤',
      '书中列王建诸子封号，未说明与918年本段同日；不直接判作矛盾。',
      'xinwudaishi-063-zongding','adds')
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in (19, 20, 21, 22):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明四年第19—22段；徐温与徐知诰治吴、虔州攻守、晋军集结及王宗鼎辞军。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=918,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in (19, 20, 21, 22)], next_paragraph=Q[23]['id'],
    coverage='卷270贞明四年第19—22段；徐知诰治吴与税制、虔州攻守、晋军集结及蜀王宗鼎辞军。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[19]['id'], 'note': '本段承接前段朱瑾灭族，但徐温又命捞骨安葬；不把前后不同处置合为同一时刻。为底本私用字，未擅改。'},
      {'paragraph_id': Q[20]['id'], 'note': '王祺病逝、刘信代将与吴越楚闽应援分录；新五代史卷61有王祺病代的简记。'},
      {'paragraph_id': Q[21]['id'], 'note': '李存审复用既有符存审主体；兵数为主书所记，不加总推定实际总兵力。'},
      {'paragraph_id': Q[22]['id'], 'note': '主书作彭王宗鼎，新五代史卷63作鲁王宗鼎，可能为异期封号，未贸然判为同一时间的文字冲突。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
