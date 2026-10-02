"""Curate consecutive Tongjian volume 270, year 919, paragraphs 1–5."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 24))
specs = [
    ('tongjian-270-918-to-919-boundary', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-10/sources/library/tongjian-270-918-to-919-boundary', 'fda1f808', '司马光等'),
    ('jiuwudaishi-009-desheng', P / 'sources/library/jiuwudaishi-009-desheng', '2605ed0c', '薛居正等'),
    ('xinwudaishi-063-shu-sacrifice', P / 'sources/library/xinwudaishi-063-shu-sacrifice', '2605ed0c', '欧阳修'),
    ('xinwudaishi-065-ma-empress', P / 'sources/library/xinwudaishi-065-ma-empress', '2605ed0c', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0919-p001-p005',
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
for n in range(1, 6):
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
        citation = f'卷270·贞明五年（919）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0919_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'蜀主':'王宗衍','晋王':'李存勖','汉主岩':'刘岩',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷270贞明五年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='919年本段条；确日未载', note='', year=919, place='吴'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0919_' + code
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
        edge = 'participation_zztj_270_0919_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('shu_southern_sacrifice_amnesty', '蜀主正月辛巳祀南郊并大赦',1,
      '春，正月，辛巳，蜀主祀南郊，大赦。',
      [('蜀主','祀南郊并颁大赦者')],when='919年正月辛巳',place='蜀南郊',
      note='918年底已宣布明年改元乾德，主书本段记录919年南郊祭祀与大赦。')
claim('event','event_zztj_270_0919_shu_southern_sacrifice_amnesty','description',
      '《新五代史》卷六十三亦记乾德元年正月祀南郊、大赦。',1,
      '乾德元年正月，祀天南郊，大赦',
      '补书明确乾德元年，与918年底“改明年元”的主书衔接。',
      'xinwudaishi-063-shu-sacrifice','corroborates')

event('li_cunshen_builds_desheng_twin_forts', '符存审在德胜夹河筑南北两城防守',2,
      '晋李存审于德胜南北夹河筑两城而守之。',
      [('李存审','在德胜南北夹河筑城防守者')],
      when='919年正月后本段；确日未载',place='德胜',
      note='李存审复用符存审主体；两城夹河，未核坐标。')
claim('event','event_zztj_270_0919_li_cunshen_builds_desheng_twin_forts','description',
      '《旧五代史》卷九记贞明五年正月晋人城德胜、夹河设栅。',2,
      '貞明五年春正月，晉人城德勝，夾河為柵。',
      '补书概述设栅，主书另明南北两城及李存审。',
      'jiuwudaishi-009-desheng','corroborates')
event('li_cunshen_replaces_zhou_dewei', '晋王以符存审代周德威任内外番汉马步总管',2,
      '晋王以存审代周德威为内外番汉马步总管。',
      [('晋王','任命符存审者'),('李存审','接替周德威任总管者'),('周德威','已阵亡的前总管')],
      when='919年本段；确日未载',place='晋',
      note='接任总管与在德胜筑城是不同动作；周德威上一年胡柳陂阵亡。')
event('li_sizhao_acting_youzhou', '晋王遣李嗣昭权知幽州军府事',2,
      '晋王还魏州，遣李嗣昭权知幽州军府事。',
      [('晋王','遣李嗣昭代管幽州者'),('李嗣昭','权知幽州军府事者')],
      when='919年本段；确日未载',place='魏州、幽州',
      note='“权知”为暂代，不写成已正式受卢龙节度使。')

event('liu_yan_makes_ma_empress', '汉主刘岩立越国夫人马氏为皇后',3,
      '汉主岩立越国夫人马氏为皇后，殷之女也。',
      [('汉主岩','册立越国夫人马氏为皇后者'),('越国夫人马氏','由越国夫人立为皇后者'),('马殷','皇后马氏之父')],
      when='919年本段；确日未载',place='汉',
      note='姓马、原封越国夫人、马殷之女均为主书明示；不猜个人名。')
claim('event','event_zztj_270_0919_liu_yan_makes_ma_empress','description',
      '《新五代史》卷六十五亦记三年册越国夫人马氏为皇后、为马殷女。',3,
      '三年，冊越國夫人馬氏為皇后。馬氏，楚王殷女也。',
      '补书记年号三年，和主书919年条对应；马氏保留称号识别，不并入其他同姓者。',
      'xinwudaishi-065-ma-empress','corroborates')
father=person('马殷',3,'越国夫人马氏之父','殷之女也。')
daughter=person('越国夫人马氏',3,'马殷之女、刘岩皇后','汉主岩立越国夫人马氏为皇后，殷之女也。')
rk='relationship_zztj_270_0919_ma_yin_father_of_empress_ma'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=daughter,
    relation_type='父亲',description='马殷是越国夫人马氏的父亲。',status='draft'))
claim('person_relationship',rk,'description','马殷是越国夫人马氏的父亲。',3,
      '汉主岩立越国夫人马氏为皇后，殷之女也。','“殷”承楚王马殷的既有主体；父亲方向明确。')
rk='relationship_zztj_270_0919_empress_ma_wife_of_liu_yan'
B['person_relationships'].append(dict(key=rk,person_a_key=daughter,person_b_key=person('刘岩',3,'立马氏为皇后的汉主','汉主岩立越国夫人马氏为皇后'),
    relation_type='妻子',description='越国夫人马氏是刘岩的妻子。',status='draft'))
claim('person_relationship',rk,'description','越国夫人马氏是刘岩的妻子。',3,
      '汉主岩立越国夫人马氏为皇后','皇后为汉主配偶；不据此推断婚期。')

event('shu_army_defeats_qi_meng_tieshan', '王宗播率蜀军出散关破岐将孟铁山，因大雨还师',4,
      '三月，丙戌，蜀北路行营都招讨、武德节度使王宗播等自散关击岐，渡渭水，破岐将孟铁山。会大雨而还，分兵戍兴元、凤州及威武城。',
      [('王宗播','率蜀军击岐并还师者'),('孟铁山','被蜀军击败的岐将')],
      when='919年三月丙戌起；还师确日未载',place='散关、渭水、兴元、凤州、威武城',
      note='王宗播复用许存主体；先破岐将、后遇雨还师并留戍，分阶段记录。')
event('wang_zongyu_fails_longzhou', '王宗昱三月戊子攻陇州不克',4,
      '戊子，天雄节度使、同平章事王宗昱攻陇州，不克。',
      [('王宗昱','攻陇州未克的蜀将')],when='919年三月戊子',place='陇州',
      note='“不克”明确未取城，不写成蜀占陇州。')
event('shu_ruler_lavish_outings', '蜀主与太后太妃频繁出游宴饮，耗费甚巨',4,
      '蜀主奢纵无度，日与太后、太妃游宴于贵臣之家，及游近郡名山，饮酒赋诗，所费不可胜纪。',
      [('蜀主','与太后太妃出游宴饮者'),('太后','与蜀主出游宴饮者'),('太妃','与蜀主出游宴饮者')],
      when='919年本段概述；起止日期未载',place='蜀',
      note='记录主书所述出游宴饮，不量化未给出的开支。')
event('yan_xu_coerces_women', '蜀仗内教坊使严旭强取民女入宫并受赂免放',4,
      '仗内教坊使严旭强取士民女子内宫中，或得厚赂而免之，以是累迁至蓬州刺史。',
      [('严旭','强取女子并受赂免放者')],
      when='919年本段追述；起止日期未载',year=None,place='蜀',
      note='长期行为未标始年；主书说因此累迁，不把每次升迁造为919年单日事件。')
event('shu_dowagers_sell_offices', '蜀太后与太妃出教令卖刺史等官',4,
      '太后、太妃各出教令卖刺史、令、录等官，每一官阙，数人争纳赂，赂多者得之。',
      [('太后','出教令卖官者'),('太妃','出教令卖官者')],
      when='919年本段概述；确日未载',place='蜀',
      note='两位沿用918年尊封的徐贤妃与徐淑妃主体；这是主书对制度性行为的概述。')

event('li_cunxu_takes_lulong_and_reassigns_youzhou', '晋王自领卢龙节度使，遣李绍宏提举幽州军府',5,
      '晋王自领卢龙节度使，以中门使李绍宏提举军府事，代李嗣昭。昭宏，宦者也，本姓马，晋王赐姓名',
      [('晋王','自领卢龙节度使并赐李绍宏姓名者'),('李绍宏','由中门使提举幽州军府者'),('李嗣昭','被李绍宏取代的权知军府者')],
      when='919年本段；确日未载',place='卢龙、幽州',
      note='李绍宏本姓马但旧名未载；不另建马姓人物。')
event('guo_chongtao_becomes_inner_gate_deputy', '孟知祥荐郭崇韬，晋王任其为中门副使',5,
      '孟知祥又荐教练使雁门郭崇韬能治剧，王以为中门副使。',
      [('孟知祥','推荐郭崇韬者'),('郭崇韬','被任中门副使者'),('晋王','作出任命者')],
      when='919年本段；确日未载',place='晋',
      note='任官与后来郭崇韬专典机密是前后关系，不强推具体日次。')
event('meng_zhixiang_resigns_inner_gate', '孟知祥称疾辞中门使，晋王改授河东马步都虞候',5,
      '及绍宏出幽州，知祥惧祸，称疾辞位，王乃以知祥为河东马步都虞候，自是崇韬专典机密。',
      [('孟知祥','称疾辞中门使、改任河东马步都虞候者'),('郭崇韬','此后专典机密者'),('晋王','改授孟知祥官职者')],
      when='919年李绍宏出幽州后；确日未载',place='晋、河东',
      note='“先是”吴珪、张虔厚获罪为背景，不把二人获罪强定919年。')
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 6):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明五年第1—5段；蜀南郊大赦、晋德胜布防、汉立马后、蜀岐战事和晋中门任官。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(1, 6)], next_paragraph=Q[6]['id'],
    coverage='卷270贞明五年第1—5段；蜀祀南郊、晋筑德胜、汉立马后、蜀对岐战事与晋王中门人事。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[2]['id'], 'note': '旧五代史卷9同记正月晋筑德胜夹河栅；继周德威总管职与幽州军府代管分录。'},
      {'paragraph_id': Q[3]['id'], 'note': '越国夫人马氏以刘岩皇后身份单列，马殷之女有主书和新五代史卷65明证。'},
      {'paragraph_id': Q[4]['id'], 'note': '宗播复用许存主体；太后太妃用918年继位段的既有身份，官员贪暴为主书概括评价，不擅定每人罪行。'},
      {'paragraph_id': Q[5]['id'], 'note': '李绍宏本姓马、获晋王赐名；未有明确旧名，不另建马姓主体。孟知祥称疾辞位与郭崇韬专机密分录。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
