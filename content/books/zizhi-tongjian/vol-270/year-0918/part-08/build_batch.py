"""Curate consecutive Tongjian volume 270, year 918, paragraphs 29–35."""
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
    ('xinwudaishi-061-liu-xin-qianzhou', P / 'sources/library/xinwudaishi-061-liu-xin-qianzhou', 'd87e4170', '欧阳修'),
    ('xinwudaishi-063-wang-jian-burial', P / 'sources/library/xinwudaishi-063-wang-jian-burial', 'd87e4170', '欧阳修'),
    ('xinwudaishi-065-han-renaming', P / 'sources/library/xinwudaishi-065-han-renaming', 'd87e4170', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p029-p035',
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
for n in range(29, 36):
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
    ck = f'claim_zztj_270_0918_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'蜀主':'王宗衍','越主岩':'刘岩','岩':'刘岩','龑':'刘岩',
            '吴越王镠':'钱镠','镠':'钱镠','知诰':'李昪','徐知诰':'李昪',
            '温':'徐温','晋王':'李存勖','吴王':'杨隆演','硃景瑜':'朱景瑜',
            '信':'刘信','英彦':'刘英彦','全播':'谭全播','知询':'徐知询'}.get(name, name)
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

event('song_guangsi_yields_six_armies', '宋光嗣九月让判六军于王宗弼，蜀主准许',29,
      '九月，壬午，蜀内枢密使宋光嗣以判六军让兼中书令王宗弼，蜀主许之。',
      [('宋光嗣','让判六军职权者'),('王宗弼','受让判六军职权者'),('蜀主','准许职权移交者')],
      when='918年九月壬午',place='蜀',
      note='“让”记军权移交，不误作宋光嗣退任内枢密使。')

event('liu_xin_qianzhou_failed_assault', '刘信昼夜攻虔州不克，转而劝谭全播纳赂',30,
      '吴刘信昼夜急攻虔州，斩首数千级，不能克；使人说谭全播，取质纳赂而还。',
      [('刘信','吴军攻城与派人说降的将领'),('谭全播','虔州守将、被劝纳赂者')],
      when='918年虔州围攻期间；确日未载',place='虔州',
      note='“斩首数千级”为史书数字；说降行为不等于城已陷。')
event('xu_wen_rebukes_liu_xin', '徐温杖刘信使者并遣刘英彦、朱景瑜率兵督攻虔州',30,
      '徐温大怒，杖信使者。信子英彦典亲兵，温授英彦兵三千，曰：“汝父居上游之地，将十倍之众，不能下一城，是反也！汝可以此兵往，与父同反！”又使升州牙内指挥使硃景瑜与之俱',
      [('徐温','杖使并遣刘英彦、朱景瑜者'),('刘英彦','受三千兵赴虔州者'),('硃景瑜','奉命与刘英彦同往者'),('刘信','被徐温责备者')],
      when='918年刘信攻虔州不克后；确日未载',place='吴、虔州',
      note='徐温说“是反也”为激将与斥责，不记为刘信确已谋反。硃景瑜规范名为朱景瑜，原字不改。')
claim('event','event_zztj_270_0918_xu_wen_rebukes_liu_xin','description',
      '《新五代史》卷六十一亦记徐温笞刘信使者并命济师。',30,
      '笞其使者而遣之，曰：「吾以笞信也。」因命濟師',
      '补书主干相合，但未列刘英彦、硃景瑜细节。',
      'xinwudaishi-061-liu-xin-qianzhou','corroborates')
father=person('刘信',30,'刘英彦之父','信子英彦典亲兵')
son=person('刘英彦',30,'刘信之子','信子英彦典亲兵')
rk='relationship_zztj_270_0918_liu_xin_father_of_yingyan'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=son,
    relation_type='父亲',description='刘信是刘英彦的父亲。',status='draft'))
claim('person_relationship',rk,'description','刘信是刘英彦的父亲。',30,
      '信子英彦典亲兵','“信子英彦”明示父子；按父亲方向记录。')

event('wang_jian_buried_yongling', '蜀十一月葬王建于永陵，庙号高祖',31,
      '冬，十一月，壬申，蜀葬神武圣文孝德明惠皇帝于永陵，庙号高祖。',
      [('王建','入葬永陵、庙号高祖者')],when='918年十一月壬申',place='永陵',
      note='神武圣文孝德明惠为主书谥号，王建本人此前六月已去世；葬礼另录。')
claim('event','event_zztj_270_0918_wang_jian_buried_yongling','description',
      '《新五代史》卷六十三亦记王建谥号、庙号高祖、陵名永陵。',31,
      '廟號高祖，陵曰永陵。',
      '新书与主书陵号庙号一致；未据此推定两书对皇后称号和死亡时间也一致。',
      'xinwudaishi-063-wang-jian-burial','corroborates')
claim('person',person('王建',31,'本段入葬永陵的前蜀高祖','蜀葬神武圣文孝德明惠皇帝于永陵'),
      'description','《新五代史》另称王建正室周氏号昭圣皇后，在王建后数日去世；与《通鉴》此前八月所记顺德皇后是否同人、日期如何对应，仍待校核。',31,
      '建正室周氏號昭聖皇后，後建數日而卒',
      '补书的“昭圣”与通鉴“顺德”称号不同，且死亡时序不同；仅并列记载，不合并皇后人物。',
      'xinwudaishi-063-wang-jian-burial','adds')

event('liu_yan_changes_state_name_han', '越主刘岩祀南郊大赦并改国号汉',32,
      '越主岩祀南郊，大赦，改国号曰汉。',
      [('越主岩','祀南郊、大赦并改国号汉者')],
      when='918年本段冬季条；确日未载',place='岭南',
      note='原文称“越主岩”，沿用已有刘岩主体；“汉”指其政权国号。')
claim('event','event_zztj_270_0918_liu_yan_changes_state_name_han','description',
      '《新五代史》卷六十五记二年祀天南郊、大赦、改国号汉。',32,
      '二年，祀天南郊，大赦境內，改國號漢。',
      '补书同记仪式与改号；该书人物别名刘龑需同主体处理，不改原文。',
      'xinwudaishi-065-han-renaming','corroborates')

event('liu_xin_takes_qianzhou', '刘信再攻虔州，谭全播奔雩都后被执',33,
      '刘信闻徐温之言，大惧，引兵还击虔州。先锋始至，虔兵皆溃，谭全播奔雩都，追执之。',
      [('刘信','率吴军再攻虔州者'),('谭全播','败走雩都而被执者')],
      when='918年刘信受徐温斥责后；确日未载',place='虔州、雩都',
      note='与第30段先攻不克和劝降分开；不将徐温斥“反”当作真实叛乱。')
claim('event','event_zztj_270_0918_liu_xin_takes_qianzhou','description',
      '《新五代史》卷六十一亦记刘信破虔州、执谭全播。',33,
      '遂破全播。',
      '补书叙述较简，主书另有雩都追执细节。',
      'xinwudaishi-061-liu-xin-qianzhou','corroborates')
event('tan_quanbo_given_wu_offices', '吴授谭全播右威卫将军、百胜节度使',33,
      '吴以全播为右威卫将军，领百胜节度使。',
      [('谭全播','被吴授右威卫将军并领百胜节度使者')],
      when='918年被吴军俘后；确日未载',place='吴',
      note='授官与被俘分录；不据此推断谭全播自愿归附。')

event('wuyue_tribute_uses_sea_route', '虔州陆路不通后吴越使者改由海路入贡梁',34,
      '先是，吴越王镠常自虔州入贡，至是道绝，始自海道出登、莱，抵大梁。',
      [('吴越王镠','改行海道入贡的吴越王')],
      when='918年虔州失守后；确日未载',place='登州、莱州、大梁',
      note='“先是”所述虔州旧陆路是背景；本段动作是道路断绝后开始走海路。')

event('xu_wen_proposes_wu_empire', '徐温劝吴王建国称帝，吴王未同意',35,
      '初，吴徐温自以权重而位卑，说吴王曰：“今大王与诸将皆为节度使，虽有都统之名，不足相临制；请建吴国，称帝而治。”王不许。',
      [('徐温','向吴王提出建国称帝者'),('吴王','未同意徐温建议者')],
      when='本段以“初”追叙；确年未载',year=None,place='吴',
      note='主书明确吴王不许，绝不可记成918年吴已称帝。')
event('xu_zhigao_moves_yan_keqiu_out', '徐知诰与骆知祥谋出严可求为楚州刺史',35,
      '严可求屡劝温以次子知询代徐知诰知吴政，知诰与骆知祥谋，出可求为楚州刺史。',
      [('严可求','屡劝改用徐知询且被外放楚州者'),('徐知询','严可求建议接掌吴政者'),
       ('徐知诰','与骆知祥谋出严可求者'),('骆知祥','与徐知诰共谋外放者')],
      when='本段“初”后追叙；确年未载',year=None,place='吴、楚州',
      note='建议徐知询代政未实施；外放楚州为一时任命，后被徐温留用。')
father=person('徐温',35,'徐知询之父','严可求屡劝温以次子知询代徐知诰知吴政')
son=person('徐知询',35,'徐温次子','严可求屡劝温以次子知询代徐知诰知吴政')
rk='relationship_zztj_270_0918_xu_wen_father_of_zhixun_younger'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=son,
    relation_type='父亲',description='徐温是徐知询的父亲。',status='draft'))
claim('person_relationship',rk,'description','徐温是徐知询的父亲。',35,
      '严可求屡劝温以次子知询代徐知诰知吴政',
      '本句称徐知询为徐温次子；按父亲方向记录，未把徐知诰视为此句“次子”。')
event('yan_keqiu_returned_by_xu_wen', '严可求向徐温主张建吴国后被留参庶政',35,
      '温大悦，复留可求参总庶政，使草具礼仪。',
      [('徐温','听严可求建议后留其参政者'),('严可求','获留并草拟礼仪者')],
      when='本段追叙；确年未载',year=None,place='金陵、吴',
      note='“草具礼仪”是准备，未表示建国称帝已发生。')
event('xu_zhigao_daughter_marries_yan_xu', '徐知诰以女嫁严可求之子严续',35,
      '知诰知可求不可去，乃以女妻其子续。',
      [('徐知诰','以女嫁严续者'),('严续','与徐知诰女成婚者')],
      when='本段追叙；确年未载',year=None,place='吴',
      note='女儿本段未具名；不据此建立徐知诰和严可求的直接姻亲边。')
event('li_cunxu_advances_against_liang_december', '晋王十二月庚子进兵距梁军十里驻营',35,
      '十二月，庚子朔，晋王进兵，距梁军十里而舍。',
      [('晋王','率晋军进兵并驻营者')],
      when='918年十二月庚子朔',place='梁军营前十里',
      note='“相持百馀日”为前期总述；只将庚子进兵精确系本日。')
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(29, 36):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明四年第29—35段；蜀军权移交、虔州陷落、王建葬礼、南汉国号和吴政议论。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=918,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(29, 36)], next_paragraph=Q[36]['id'],
    coverage='卷270贞明四年第29—35段；宋光嗣让军权、虔州战事、王建入永陵、刘岩改汉、吴徐温政治安排及晋梁对峙。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[30]['id'], 'note': '刘信说降未成、徐温杖使、再攻虔州分段记录；徐温斥“反”为威压话语，不当作已证实谋反。'},
      {'paragraph_id': Q[31]['id'], 'note': '新五代史卷63记王建庙号高祖、永陵，与通鉴相符；同段称其正室周氏为昭圣皇后且死于王建后数日，通鉴此前八月作顺德皇后殂，身份谥号及日期待校，不贸然并人。'},
      {'paragraph_id': Q[32]['id'], 'note': '主书称越主岩改国号汉，新五代史卷65称刘龑二年祀南郊改汉；两名复用已有刘岩主体。'},
      {'paragraph_id': Q[34]['id'], 'note': '吴越海路入贡是旧路断绝后的新路，不把“先是”旧陆路误记为本年新事件。'},
      {'paragraph_id': Q[35]['id'], 'note': '初字引政治背景，徐温劝称帝并未实现；十二月晋王进兵是本段明确日次，分录。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
