"""Curate consecutive Tongjian vol. 269, 915 paragraphs 22–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 34))
main = 'tongjian-269-915-august'
new_66 = 'xinwudaishi-066-ma-yin-brothers'
new_65 = 'xinwudaishi-065-ma-consort'
new_61 = 'xinwudaishi-061-xu-wen-915'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-06/sources/library' / main, '5f494c20', '司马光等'),
    (new_66, P / 'sources/library' / new_66, '4c3a46f3', '欧阳修'),
    (new_65, P / 'sources/library' / new_65, '4c3a46f3', '欧阳修'),
    (new_61, P / 'sources/library' / new_61, '4c3a46f3', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p022-p024',
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
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
for n in range(22, 25):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in (source_dirs[main] / 'source.txt').read_text(), n
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

def claim(table, key, field, value, n, quote, note, source=main, relation='adds'):
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明元年（915）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0915_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'王宗播': '许存'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
    if name == '杨延直':
        row['aliases'] = ['楊延直']
    if name == '夏鲁奇':
        row['aliases'] = ['李绍奇']
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '姓名按既有主体规范；原文和摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=915):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0915_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '915年本段条；确日未载', dynasty='五代十国',
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
          '段内追叙，确年待考。' if year is None else '按主书段落次序；未把干支换算成公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0915_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key




# p022: marriage link between Liu Yan and the Chu court.
event('liu_yan_seeks_chu_bride', '刘岩向楚迎娶妻室，马殷遣马存送嫁', 22,
      '刘岩逆妇于楚，楚王殷遣永顺节度使存送之。',
      [('刘岩','向楚迎娶妻室的岭南势力首领'),('马殷','派永顺节度使马存送嫁的楚王'),('马存','以永顺节度使身份奉命送嫁的楚将')],
      when='915年莘县对峙后所记；确月日未载', place='楚、岭南',
      note='主书只写“存”；据楚王马殷之弟马存既有人物与《新五代史》马存、马賨为不同兄弟的记载识别，未把“存”误合并到马賨。妻室在主书未具名，暂不新建泛名人物。')
claim('person',people['马存'],'description',
      '《新五代史》卷六十六区分马殷之弟马賨与马存，两人为不同人。',22,
      '殷以其弟賨為左相，存為右相',
      '旧书未在此句说明915年永顺节度使是谁，仅用于区分“存”和“賨”；主书官号与911年马賨任永顺节度使之间是否有交替待核。',new_66,'adds')
claim('event','event_zztj_269_0915_liu_yan_seeks_chu_bride','description',
      '《新五代史》后记刘岩皇后马氏是楚王马殷之女。',22,
      '馬氏，楚王殷女也。',
      '此为后来的皇后身份与父系补证；915年主书仅记迎妇，未言当时册后或给出个人名。',new_65,'adds')
# p023: Later Shu ruler Wang Jian orders two parallel campaigns.
event('shu_orders_qinzhou_attack', '王建任王宗绾、王宗播率北路军攻秦州', 23,
      '乙未，蜀主以兼中书令王宗绾为北路行营都制置使，兼中书令王宗播为招讨使，攻秦州；',
      [('王建','任命北路行营将领并命攻秦州的蜀主'),('王宗绾','获任北路行营都制置使的蜀将'),('王宗播','获任招讨使的蜀将')],
      when='915年乙未；所属月从本年段落顺序，未换算公历日', place='秦州',
      note='“攻秦州”为任命和出兵目标，不预记攻下秦州。王宗播是已发布人物许存的赐名，沿用既有UUID与线上别名修订。')
event('shu_orders_fengzhou_attack', '王建任王宗瑶、王宗翰率东北军攻凤州', 23,
      '兼中书令王宗瑶为东北面招讨使，同平章事王宗翰为副使，攻凤州。',
      [('王建','任命东北面行营将领并命攻凤州的蜀主'),('王宗瑶','获任东北面招讨使的蜀将'),('王宗翰','获任副使的蜀将')],
      when='915年乙未；所属月从本年段落顺序，未换算公历日', place='凤州',
      note='与攻秦州并行记录，不推定两军同日到达或夺城。')
# p024: Xu Wen remains effective controller while Xu Zhixun governs in Guangling.
event('wu_promotes_xu_wen', '吴加徐温军职、齐国公及两浙都招讨使，镇润州', 24,
      '庚戌，吴以镇海节度使徐温为管内水陆马步诸军都指挥使、两浙都招讨使、守侍中、齐国公，镇润州，以升、润、常、宣、歙、池六州为巡属，军国庶务参决如故；',
      [('徐温','获加军职、齐国公并移镇润州的吴国执政者')],
      when='915年庚戌；未换算公历日', place='润州；巡属升、润、常、宣、歙、池六州',
      note='主书为多项官爵与驻镇同条记述；六州是巡属，不据此绘制疆域边界。')
claim('event','event_zztj_269_0915_wu_promotes_xu_wen','description',
      '《新五代史》卷六十一也记徐温于吴天祐十二年获封齐国公、两浙都招讨使并始镇润州。',24,
      '十二年封徐溫齊國公、兩浙都招討使，始鎮潤州。',
      '新书简记主要官爵；“十二年”是吴沿用唐天祐年号，不误作后梁纪年。',new_61,'corroborates')
claim('person',people['徐温'],'aliases','徐温在《新五代史》原文写作徐溫。',24,
      '十二年封徐溫齊國公',
      '繁简字形为同一既有人物，后续对线上别名作有证据修订。',new_61,'corroborates')
event('xu_zhixun_governs_guangling', '徐知训留广陵主持政事，徐温在润州遥决大事', 24,
      '军国庶务参决如故；留徐知训居广陵秉政。',
      [('徐温','移镇润州而继续参决军国事务的吴国执政者'),('徐知训','留在广陵主持政事的吴国官员')],
      when='915年徐温镇润州后；确日未载', place='广陵、润州',
      note='既有徐温为徐知训父亲的关系不重复建边；主书只明言留广陵秉政。')
claim('event','event_zztj_269_0915_xu_zhixun_governs_guangling','description',
      '《新五代史》卷六十一记徐知训留任行军副使主持政务，大事由徐温遥决。',24,
      '留其子知訓為行軍副使，秉政，而大事溫遙決之。',
      '旧书补行军副使官名；父子关系已有既存记录，此处不新建重复关系。',new_61,'adds')
claim('person',people['徐知训'],'aliases','徐知训在《新五代史》原文写作徐知訓。',24,
      '留其子知訓為行軍副使',
      '繁简字形为同一既有人物，后续对线上别名作有证据修订。',new_61,'corroborates')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(22, 25):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第22—24段连续处理；楚婚、蜀秦凤两路任命与吴徐温移镇分别记录，繁简名不新建人物。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(22, 25)], next_paragraph=Q[25]['id'],
    coverage='卷269贞明元年第22—24段；刘岩迎楚妇、蜀出兵秦凤、吴徐温移镇。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[22]['id'],'note':'主书仅称永顺节度使“存”；马存与马賨是不同的楚王弟，911年马賨受永顺节度使官，此时是否转由马存须纸本及官历核。'},
      {'paragraph_id':Q[22]['id'],'note':'新五代史后记马氏为楚王女、刘岩皇后，只用于婚姻对象身份补充，不提前写为915年已册后。'},
      {'paragraph_id':Q[23]['id'],'note':'蜀两路攻秦州和凤州为任命及军事目标；攻城结果未在此段明言。'},
      {'paragraph_id':Q[24]['id'],'note':'徐温、徐知训在新五代史作繁体“徐溫”“徐知訓”，既有人物别名已修订并匿名读回，见content/revisions/2026-10-02-xu-wen-zhixun-traditional。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
