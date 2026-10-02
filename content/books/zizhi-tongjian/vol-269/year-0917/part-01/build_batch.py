"""Curate consecutive Tongjian vol. 269, 916 paragraphs 1–3."""
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
main1 = 'tongjian-269-917-spring-start'
main2 = 'tongjian-269-917-spring-mutiny'
old28 = 'jiuwudaishi-028-newzhou'
old97 = 'jiuwudaishi-097-lu-wenjin'
new48 = 'xinwudaishi-048-lu-wenjin'
liao01 = 'liaoshi-001-newzhou'
specs = [(key,P / 'sources/library' / key,'f5788d38',author) for key,author in [
    (main1,'司马光等'),(main2,'司马光等'),(old28,'薛居正等'),
    (old97,'薛居正等'),(new48,'欧阳修'),(liao01,'脱脱等')]]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0917-p001-p003',
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
for n in range(1, 4):
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
    for key in (main1, main2):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source in (main1, main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明三年（917）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0917_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1, main2):
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','契丹主':'阿保机'}.get(name, name)
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

# p001: relief of the Wu siege begun in the preceding year.
event('yuan_xiangxian_relief_yingzhou','后梁命袁象先救颍州，吴军撤围',1,
      '春，正月，诏宣武节度使袁象先救颍州，既至，吴军引还。',
      [('袁象先','奉诏率军赴颍州救援的宣武节度使')],
      when='917年春正月；确日未载',place='颍州',
      note='接续916年吴军进围颍州；本段只记袁象先到达后吴军撤退，不推为俘斩或收复其他州。')

# p002: short failed assault at Liyang.
event('jin_attacks_liyang_fails','晋王攻黎阳数日，刘鄩拒守，晋军未克而退',2,
      '二月，甲申，晋王攻黎阳，刘鄩拒之，数日，不克而去。',
      [('李存勖','率军攻黎阳数日未克的晋王'),('刘鄩','拒守黎阳的后梁将领')],
      when='917年二月甲申起、数日；未换算公历日',place='黎阳',
      note='“不克而去”为晋军撤退；不把黎阳误标为晋占。')
claim('event','event_zztj_269_0917_jin_attacks_liyang_fails','description',
      '《旧五代史》卷二十八同记晋王天祐十四年二月攻刘鄩所守黎阳，不克而还。',2,
      '天祐十四年二月，帝聞劉鄩復收殘兵保守黎陽，遂率師以攻之，不克而還。',
      '旧书以晋沿用天祐纪年，同指917年；不将旧书未载甲申的时间补入其原文。',old28,'corroborates')

# p003: background, levies, the mutiny, Lu Wenjin's subsequent flight.
event('li_cunju_poor_governance_newzhou','李存矩治新州骄惰，侍婢干预政事',3,
      '晋王之弟威塞军防御使存矩在新州，骄惰不治，侍婢预政。',
      [('李存矩','在新州治政不善的晋王之弟')],
      when='新州兵变前；起始年未载',place='新州',year=None,
      note='“骄惰不治”是主书评价性叙述，作为兵变背景；不据此给侍婢补姓名。')
junior = person('李存矩',3,'晋王李存勖之弟','晋王之弟威塞军防御使存矩在新州')
senior = person('李存勖',3,'李存矩之兄','晋王之弟威塞军防御使存矩在新州')
rel = 'relationship_person_李存矩_person_li_cunxu_弟弟'
B['person_relationships'].append(dict(key=rel,person_a_key=junior,person_b_key=senior,
    relation_type='弟弟',description='李存矩是李存勖的弟弟。',status='draft'))
claim('person_relationship',rel,'description','李存矩是李存勖的弟弟。',3,
      '晋王之弟威塞军防御使存矩在新州','晋王即李存勖；本句直接标明李存矩为其弟。')
event('jin_northern_recruitment_horse_levy','晋王令李存矩征募山北兵并向民间征马',3,
      '晋王使募山北部落骁勇者及刘守光亡卒以益南讨之军。又率其民出马，民或鬻十牛易一战马，期会迫促，边人嗟怨。',
      [('李存勖','下令增募兵马的晋王'),('李存矩','受命在山北征募并征马者')],
      when='917年新州兵变前；确日未载',place='山北、新州',
      note='“十牛易一战马”为主书举例，不推为统一法定兑换率。')
claim('event','event_zztj_269_0917_jin_northern_recruitment_horse_levy','description',
      '《新五代史》卢文进传亦记募山后劲兵、课民出马，十牛易一马。',3,
      '存矩募山後勁兵數千人，課民出馬，民以十牛易一馬',
      '新书“数千人”与主书随后实得五百骑分属不同计数，不直接相加。',new48,'corroborates')
event('li_cunju_marches_five_hundred_cavalry','李存矩率五百骑南行，以卢文进为裨将',3,
      '存矩得五百骑，自部送之，以寿州刺史卢文进为裨将。',
      [('李存矩','统领五百骑南行者'),('卢文进','随行裨将、寿州刺史')],
      place='新州至祁沟关途中',
      note='五百为此行骑兵数，不等同前述全部募兵数。')
event('gong_yanzhang_mutiny_qigou','宫彦璋与兵士在祁沟关谋杀李存矩并据新州',3,
      '甲午，至祁沟关，小校宫彦璋与士卒谋曰：“闻晋王与梁人确斗，骑兵死伤不少。吾侪捐父母妻子，为人客战，千里送死，而使长复不矜恤，奈何？”众曰：“杀使长，拥卢将军还新州，据城自守，其如我何！”',
      [('宫彦璋','鼓动兵士在祁沟关谋变的小校'),('李存矩','叛军拟杀的统兵者')],
      when='917年二月甲午；未换算公历日',place='祁沟关',
      note='引文是士兵所述动机，不另推晋梁战损数量；此处仅记谋变，杀害另录。')
event('li_cunju_killed_by_mutineers','祁沟关叛军闯传舍杀李存矩',3,
      '因执兵大噪，趣传舍，诘朝，存矩寝未起，就杀之，文进不能制，抚膺哭其尸曰：“奴辈既害郎君，使我何面复见晋王！”',
      [('李存矩','在传舍遇害的晋王之弟'),('卢文进','主书称未能制止乱军并哭李存矩者')],
      when='917年二月甲午次晨；未换算公历日',place='祁沟关传舍',
      note='按《通鉴》将杀害主体记为叛军，未把卢文进写成直接杀人者；其他史书异说另引。')
claim('event','event_zztj_269_0917_li_cunju_killed_by_mutineers','description',
      '《旧五代史》卢文进传正文也记乱兵害存矩，文进哭其尸；所附案语引另一说。',3,
      '害存矩於榻下。文進撫膺曰：「奴輩累我矣。」因環屍而泣曰：「此輩既害郎君，我何面目見王！」',
      '旧书正文与通鉴相近，不能据附录案语覆盖正文。',old97,'corroborates')
claim('event','event_zztj_269_0917_li_cunju_killed_by_mutineers','description',
      '《新五代史》称李存矩取卢文进之女为侧室，卢文进因而与乱军杀存矩。',3,
      '存矩求之為側室，文進以其大將不敢拒，雖與，心常歉之也，因與亂軍殺存矩反。',
      '参与责任与通鉴、旧书正文不同；女儿未具名，动机亦只作为新书说法。',new48,'conflicts')
claim('event','event_zztj_269_0917_li_cunju_killed_by_mutineers','description',
      '《辽史》卷一也直书卢文进杀李存矩来降。',3,
      '晉新州裨將盧文進殺節度使李存矩來降。',
      '辽史简写将责任归卢文进，与通鉴叛军行凶的叙述不同；不因此推定其亲手杀人。',liao01,'conflicts')
event('yang_quanzhang_rejects_mutineers_newzhou','叛军拥卢文进返回新州，守将杨全章拒入',3,
      '因为众所拥，还新州，守将杨全章拒之。',
      [('卢文进','被叛军拥回新州者'),('杨全章','拒叛军入新州的守将')],place='新州',
      note='卢文进“为众所拥”为主书说法，不能据此断其自愿程度。')
event('li_sihong_defeats_mutineers_wuzhou','叛军转攻武州，李嗣肱击败之',3,
      '又攻武州，雁门以北都知防御兵马使李嗣肱击败之。',
      [('李嗣肱','击败攻武州叛军的晋将')],place='武州',
      note='主书未给武州攻守兵数。')
event('lu_wenjin_flees_to_khitan','周德威追讨后，卢文进率众奔契丹',3,
      '周德威亦遣兵追讨，文进帅其众奔契丹。',
      [('周德威','派兵追讨叛军的晋将'),('卢文进','率残众奔契丹者')],place='晋北边、契丹',
      note='与下一段契丹攻新州分开，不提前记契丹占城。')
event('jin_king_punishes_cunju_staff','晋王因李存矩失政致乱，处死侍婢及幕僚数人',3,
      '晋王闻存矩不道以致乱，杀侍婢及幕僚数人。',
      [('李存勖','闻兵变后处死侍婢与幕僚的晋王')],place='晋王军府',
      note='受刑者未具名，“数人”不换算确数；主书以存矩失政解释处分。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 4):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269贞明三年第1—3段；颍州解围、黎阳未克、新州征兵与祁沟关兵变；卢文进责任异说并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=917,
    primary_source_key=main1,primary_source_keys=[main1,main2],paragraphs=[Q[n]['id'] for n in range(1,4)],
    next_paragraph=Q[4]['id'],coverage='卷269贞明三年第1—3段；颍州、黎阳与新州祁沟关兵变。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[3]['id'],'note':'《通鉴》和旧五代史卢文进传正文称叛军杀李存矩、卢文进未能制止；新五代史与辽史将责任归卢文进。各书异说并列，不以一种说法覆盖其他。'},
      {'paragraph_id':Q[3]['id'],'note':'“十牛易一战马”为个案换马描述，不作统一币值；五百骑为李存矩此行人数。宫彦璋仅主书具名。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
