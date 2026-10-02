"""Curate consecutive Tongjian vol. 269, 915 paragraphs 5–7."""
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
main = 'tongjian-269-914-year-end'
old_mutiny = 'jiuwudaishi-008-wei-mutiny'
old_zhang = 'jiuwudaishi-008-zhang-yan'
old_baoheng = 'jiuwudaishi-008-li-baoheng'
new_baoheng = 'xinwudaishi-040-li-baoheng'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0914/part-03/sources/library' / main, 'cc69bae0', '司马光等'),
    (old_mutiny, P / 'sources/library' / old_mutiny, 'ed9f98aa', '薛居正等'),
    (old_zhang, P / 'sources/library' / old_zhang, 'ed9f98aa', '薛居正等'),
    (old_baoheng, P / 'sources/library' / old_baoheng, 'ed9f98aa', '薛居正等'),
    (new_baoheng, P / 'sources/library' / new_baoheng, 'ed9f98aa', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p005-p007',
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
for n in range(5, 8):
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
    ck = f'claim_zztj_269_0915_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
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


def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

# p005: failed transfer, mutiny, negotiation, and the appeal to Jin.
event('wei_troops_resist_split', '魏州军士因分镇迁徙而不满', 5,
      '魏兵皆父子相承数百年，族姻磐结，不愿分徙。德伦屡趣之，应行者皆嗟怨，连营聚哭。',
      [('贺德伦','督促魏州将士迁往新镇的节度使')],
      when='915年魏博分镇后；确日未载', place='魏州',
      note='“父子相承数百年”为军府传承描述，不指具体人物连续任职数百年。')
event('wang_yanzhang_jinbo', '刘鄩屯南乐，王彦章领龙骧骑入魏州金波亭', 5,
      '己丑，刘鄩屯南乐，先遣澶州刺史王彦章将龙骧五百骑入魏州，屯金波亭。',
      [('刘鄩','驻屯南乐并先遣王彦章入魏州的梁将'),('王彦章','领龙骧五百骑驻金波亭者')],
      when='915年己丑；本段承三月，确月待校', place='南乐、魏州金波亭',
      note='五百骑为主书记数；未换算干支公历日期。')
event('wei_troops_mutiny', '魏州兵变焚掠、王彦章撤出，贺德伦亲兵被杀', 5,
      '是夕，军乱，纵火大掠，围金波亭，王彦章斩关而走。诘旦，乱兵入牙城，杀贺德伦之亲兵五百人，劫德伦置楼上。',
      [('王彦章','被围金波亭后破关撤出的梁将'),('贺德伦','被兵变军士劫持的天雄节度使')],
      when='915年己丑当夜及次晨', place='魏州金波亭、牙城',
      note='亲兵五百人为主书记数；旧五代史卷八作五百余人，并称三月二十九日夜。')
claim('event','event_zztj_269_0915_wei_troops_mutiny','description',
      '《旧五代史》卷八记三月二十九日夜魏州军乱、王彦章逃出、贺德伦被囚。',5,
      '三月二十九日夜，魏軍乃作亂，放火大掠，首攻龍驤軍，王彥章斬關而遁。',
      '旧书明确月日；与主书干支待历日核算，未直接改写主书时间。',old_mutiny,'adds')
claim('event','event_zztj_269_0915_wei_troops_mutiny','description',
      '《旧五代史》卷八记贺德伦亲军被杀五百余人。',5,
      '殺德倫親軍五百餘人於牙城，執德倫置之樓上。',
      '主书作五百人，旧书作五百余人；不合并成精确人数。',old_mutiny,'adds')
event('zhang_yan_stops_looting', '银枪效节军校张彦率党止兵变军士剽掠', 5,
      '有效节军校张彦者，自帅其党，拔白刃，止剽掠。',
      [('张彦','率其党持刀止剽掠的效节军校')],
      when='915年魏州兵变次晨；确日未换算', place='魏州',
      note='止剽掠不等于结束兵变；旧书另记其党数百人，未纳作主书数字。')
event('hu_yi_negotiation', '朱友贞遣扈异抚谕魏军，张彦请复相澶卫三州未获准', 5,
      '夏，四月，帝遣供奉官扈异抚谕魏军，许张彦以刺史。彦请复相、澶、卫三州如旧制。异还，言张彦易与，但遣刘鄩加兵，立当传首。帝由是不许，但以优诏答之。',
      [('朱友贞','遣使抚谕但不许恢复原镇的梁帝'),('扈异','奉命抚谕魏州军的供奉官'),('张彦','请恢复相澶卫归旧镇的军校'),('刘鄩','被扈异建议用兵的梁将')],
      when='915年四月', place='魏州、梁朝廷',
      note='扈异主张加兵是建议，梁帝未在此处据此实际发动进攻。')
claim('event','event_zztj_269_0915_hu_yi_negotiation','description',
      '《旧五代史》卷八记梁帝遣使安抚，张彦等要求恢复相、卫并撤刘鄩军。',5,
      '因迫德倫飛奏，請卻復相、衛，抽退劉鄩軍。',
      '旧书此处只明言相、卫，主书另列澶；各依原书措辞。',old_zhang,'adds')
event('zhang_yan_forces_appeal_jin', '张彦撕毁梁诏，逼贺德伦致书求援晋王', 5,
      '使者再返，彦裂诏书抵于地，戟手南向诟朝廷，谓德伦曰：“天子愚暗，听人穿鼻。今我兵甲虽强，苟无处援，不能独立，宜投款于晋。”遂逼德伦以书求援于晋。',
      [('张彦','撕毁诏书并逼贺德伦求援于晋者'),('贺德伦','被迫致书向晋王求援的节度使')],
      when='915年四月；确日未载', place='魏州',
      note='原文明确“逼”贺德伦；其个人意愿不可据致书推断。')
claim('event','event_zztj_269_0915_zhang_yan_forces_appeal_jin','description',
      '《旧五代史》卷八记张彦逼贺德伦遣牙将曹廷隐致书晋王。',5,
      '德倫不得已而從之，乃遣牙將曹廷隱奉書求援於太原。',
      '旧书补致书使者姓名；主书只记致书动作。',old_zhang,'adds')
# p006: retained identity across the 914–915 boundary, and explicit adoption.
event('li_baoheng_kills_yanlu', '李保衡杀李彦鲁并自称静难留后', 6,
      '李继徽假子保衡杀李彦鲁，自称静难留后，',
      [('李保衡','杨崇本养子，杀李彦鲁并自任静难留后者'),('彦鲁（杨崇本子）','以李彦鲁之名被李保衡杀害者'),('杨崇本','以李继徽之名被称作李保衡养父者')],
      when='915年四月条；确日未载', place='静难、邠州',
      note='李继徽即已录杨崇本；本段明确“李彦鲁”，复用914年其子彦鲁主体，不因添姓新建。')
relation('杨崇本','李保衡','养父',6,'李继徽假子保衡',
         '李继徽已据旧五代史卷十三确认为杨崇本；“假子”指养子，关系方向为杨崇本是李保衡养父。')
claim('person',people['彦鲁（杨崇本子）'],'aliases',
      '914年仅称彦鲁者，在915年《通鉴》被称李彦鲁。',6,
      '保衡杀李彦鲁', '与前段同为李继徽之子且死于继位争夺；先合并稳定主体，规范显示名后续改为李彦鲁。')
claim('event','event_zztj_269_0915_li_baoheng_kills_yanlu','description',
      '《新五代史》卷四十记杨崇本养子李保衡杀彦鲁以降梁。',6,
      '崇本養子李保衡，殺彥魯以降梁。',
      '新书明确养父身份与杀彦鲁，称彦鲁未冠姓。',new_baoheng,'corroborates')
claim('event','event_zztj_269_0915_li_baoheng_kills_yanlu','description',
      '《旧五代史》卷八记李保衡为杨崇本养子，彦鲁领州事五十余日后被杀。',6,
      '彥魯領知州事五十餘日，保衡殺彥魯送款於帝',
      '“五十余日”为旧书记数；与914年死亡时间参照，不据此换算确日。',old_baoheng,'adds')
event('li_baoheng_defects_liang', '李保衡以邠、宁二州归附后梁', 6,
      '举邠、宁二州来附。', [('李保衡','举邠宁二州归附后梁者')],
      when='915年四月条；确日未载', place='邠州、宁州',
      note='“来附”承后梁编年视角，地点只记州名，不推定边界。')
event('li_baoheng_huo_appointments', '梁任李保衡为感化节度使、霍彦威为静难节度使', 6,
      '诏以保衡为感化节度使，以河阳留后霍彦威为静难节度使。',
      [('朱友贞','下诏任命两镇节度使的梁帝'),('李保衡','受任感化节度使'),('霍彦威','由河阳留后改任静难节度使')],
      when='915年四月条；确日未载', place='感化、静难',
      note='旧五代史卷八作李保衡为华州节度使，官镇称谓关系待考；不以异称覆盖主书。')
claim('event','event_zztj_269_0915_li_baoheng_huo_appointments','description',
      '《旧五代史》卷八称李保衡获华州节度使、霍彦威获邠州节度使。',6,
      '即以保衡為華州節度使，以河陽留後霍彥威為邠州節度使。',
      '旧书用治所名，主书用军额；待核是否指同一官镇，不自断为职位冲突。',old_baoheng,'adds')
# p007: explicit Xu family relation and promotion.
event('xu_zhixun_promoted', '徐温任其子徐知训为淮南行军副使、诸军副使', 7,
      '吴徐温以其子牙内都指挥使知训为淮南行军副使、内外马步诸军副使。',
      [('徐温','任命其子知训的吴国执政者'),('徐知训','由牙内都指挥使升任淮南行军副使及诸军副使')],
      when='915年四月条后；确日未载', place='淮南',
      note='本段只记任命，不推定徐知训此时已独揽吴政。')
relation('徐温','徐知训','父亲',7,'徐温以其子牙内都指挥使知训',
         '原文“其子”明确父子；父亲关系方向为徐温→徐知训。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5, 8):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第5—7段连续处理；魏州兵变与求晋援分录，李彦鲁复用前段彦鲁主体，养父及徐温父子关系按明确原文录入。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(5, 8)], next_paragraph=Q[8]['id'],
    coverage='卷269贞明元年三月末至四月第5—7段；魏州兵变、邠宁归梁与徐知训任职。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[5]['id'],'note':'旧五代史明记三月二十九日夜兵变，通鉴用己丑；历日待校。'},
      {'paragraph_id':Q[6]['id'],'note':'李彦鲁与914年仅称彦鲁者为同一主体，线上规范显示名待改；旧书华州与通鉴感化官镇称谓待校。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
