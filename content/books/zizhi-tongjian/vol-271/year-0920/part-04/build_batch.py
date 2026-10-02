"""Curate consecutive Tongjian volume 271, year 920, paragraphs 14–18."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 27))
specs = [
    ('tongjian-271-920-april', YEAR / 'part-01/sources/library/tongjian-271-920-april', '438b833a', '司马光等'),
    ('tongjian-271-920-winter', P / 'sources/library/tongjian-271-920-winter', '9edfda98', '司马光等'),
    ('jiuwudaishi-010-tongzhou-defeat', P / 'sources/library/jiuwudaishi-010-tongzhou-defeat', '9edfda98', '薛居正等'),
    ('jiuwudaishi-056-fu-cunshen-tongzhou', P / 'sources/library/jiuwudaishi-056-fu-cunshen-tongzhou', '9edfda98', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0920-p014-p018',
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
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(14, 19):
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
        citation = f'卷271·贞明六年（920）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0920_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','蜀主':'王宗衍','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'窦维':['竇維'],'华温琪':['華溫琪']}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271贞明六年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='920年本段条；确日未载', note='', year=920, place='五代十国'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0920_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_271_0920_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('fu_cunshen_reaches_hezhong_crosses_river','符存审等到河中，当日渡河',14,
      '李存审等至河中，即日济河。',
      [('李存审','率晋援军到河中并渡河者')],
      when='920年晋援同州期间；主书确月、日未载',place='河中',
      note='李存审复用符存审；旧书传记另将到河中系于九月，不改写主书纪时。')
claim('event','event_zztj_271_0920_fu_cunshen_reaches_hezhong_crosses_river','time_original',
      '《旧五代史》符存审传记九月到河中、进营朝邑。',14,
      '九月，次河中，進營朝邑。',
      '主书本段未记确月；补书记为九月，两者分别保留，不把七月遣军当作到达日期。',
      'jiuwudaishi-056-fu-cunshen-tongzhou','adds')
event('fu_cunshen_probes_liu_xun_camp','符存审以二百精甲杂河中军逼刘鄩垒',14,
      '梁人素轻河中兵，每战必穷追不置。存审选精甲二百，杂河中兵，直压刘鄩垒，鄩出千骑逐之；知晋人已至，大惊，自是不敢轻出。',
      [('李存审','选二百精甲杂河中兵逼梁垒者'),('刘鄩','出千骑追逐、得知晋援至后不敢轻出者')],
      when='920年晋援至河中后；确日未载',place='同州梁军营垒',
      note='二百精甲与梁出千骑为主书兵数，不推造成多少伤亡。')
event('jin_camps_at_chaoyi','晋军屯营朝邑',14,
      '晋人军于朝邑。',[],
      when='920年晋援同州期间；确日未载',place='朝邑',
      note='“军于”只录驻军地点，未核其现代坐标。')

event('zhu_youqian_rejects_return_to_liang','朱友谦拒诸子劝归梁，坚持晋盟',15,
      '河中事梁久，将士皆持两端。诸军大集，刍粟踊贵，友谦诸子说友谦且归款于梁，以退其师，友谦曰：“昔晋王亲赴吾急，秉烛夜战。今方与梁相拒，又命将星行，分我资粮，岂可负邪！”',
      [('朱友谦','拒诸子劝归梁并申说晋王旧援之恩者')],
      when='920年同州攻援期间；确日未载',place='河中',
      note='诸子未点名，不由已录朱令德猜代发言者；“昔”援战为回顾，未另造920年旧战。')

event('jin_attacks_huazhou_outer_wall','晋军分兵攻华州，毁其外城',16,
      '晋人分兵攻华州，坏其外城。',[],
      when='920年同州攻援期间；确日未载',place='华州',
      note='坏外城与占领华州不同阶段；此句只证外城被毁。')
event('liu_xun_defeated_retreats_luowen','符存审等逼梁营，刘鄩败退罗文寨',16,
      '李存审等按兵累旬，乃进逼刘鄩营，鄩等悉众出战，大败，收馀众退保罗文寨。',
      [('李存审','按兵累旬后进逼梁营并获胜者'),('刘鄩','悉众出战败后退保罗文寨者')],
      when='920年同州攻援期间，晋军按兵累旬后；确日未载',place='同州梁营、罗文寨',
      note='按兵累旬是等待时长，不擅换算起止公历日。')
claim('event','event_zztj_271_0920_liu_xun_defeated_retreats_luowen','description',
      '《旧五代史》卷十记晋将救同州，梁军败退华州罗文寨。',16,
      '晉王遣都將李嗣昭、李存審、王建及率師來援同州，戰於城下。我師敗績，諸將以餘眾退保華州羅文寨。',
      '旧书梁本纪“我师”指梁军，不能按引用视角误记晋败；同书王建及依赐姓名证据按李建及同人。',
      'jiuwudaishi-010-tongzhou-defeat','corroborates')
event('fu_cunshen_opens_liang_retreat_route','符存审议开梁军走路，派人在沙苑牧马',16,
      '又旬馀，存审谓李嗣昭曰：“兽穷则搏，不如开其走路，然后击之。”乃遣人牧马于沙苑。',
      [('李存审','与李嗣昭议开梁军退路并遣牧马者'),('李嗣昭','听符存审议战术的晋将')],
      when='920年罗文寨败退后又旬馀；确日未载',place='沙苑',
      note='主书未点名牧马者；旧书传记指定王建及，作为独立补充参加记录。')
# This actor is named only by the supplementary book, so every added field cites it.
name='李建及'
pk=registry[name]['key']
if name not in people:
    B['people'].append(dict(registry[name],status='draft'))
    people[name]=pk
    reused.add(pk)
    claim('person',pk,'description','旧书本段王建及依赐姓名证据对应李建及。',16,
          '乃令王建及牧馬於沙苑，',
          '《旧五代史》卷六十五李建及传已证本姓王、后赐姓名；不因旧书仍称王建及再建人物。',
          'jiuwudaishi-056-fu-cunshen-tongzhou','adds')
ek='event_zztj_271_0920_fu_cunshen_opens_liang_retreat_route'
edge='participation_zztj_271_0920_supplement_li_jianji_grazes_shayuan'
B['person_events'].append(dict(key=edge,person_key=pk,event_key=ek,
    role='旧书所记奉命在沙苑牧马者',status='draft'))
claim('person_event',edge,'role','李建及（旧书作王建及）奉命在沙苑牧马。',16,
      '乃令王建及牧馬於沙苑，',
      '主书只称遣人，具体人名从旧书补充；未将传记内《欧阳史》注文视作旧书独立本体。',
      'jiuwudaishi-056-fu-cunshen-tongzhou','adds')
event('jin_pursues_liang_at_wei_river','梁军夜遁，晋军追至渭水再破之',16,
      '鄩等宵遁，追击至渭水，又破之，杀获甚众，',
      [('刘鄩','夜遁后被晋军追至渭水再败的梁将'),('李存审','承主书统军上下文追击梁军者')],
      when='920年沙苑牧马部署后；确日未载',place='渭水',
      note='“杀获甚众”不转为精确伤亡数；此为罗文寨初败后的追击阶段。')
event('jin_advances_xiagui_visits_tang_tombs','符存审等告谕关右、略地下邽，谒唐陵后还师',16,
      '存审等移檄告谕关右，引兵略地至下邽，谒唐帝陵，哭之而还。',
      [('李存审','率军略地至下邽、谒唐陵后还师者')],
      when='920年渭水追击后；确日未载',place='关右、下邽、唐帝陵',
      note='下邽是兵略所至，未推整个关右均被占领。')
claim('event','event_zztj_271_0920_jin_advances_xiagui_visits_tang_tombs','description',
      '《旧五代史》符存审传记其略地至奉先，谒帝陵后班师。',16,
      '存審略地至奉先，謁諸帝陵，乃班師。',
      '主书作下邽，补书作奉先，行军所至地名异文分别保存，不擅合为同一地。',
      'jiuwudaishi-056-fu-cunshen-tongzhou','conflicts')

event('hezhong_attacks_chongzhou','河中军攻崇州，温韬惧',17,
      '河中兵进攻崇州，静胜节度使温昭图甚惧。',
      [('温昭图','因河中军攻崇州而忧惧的静胜节度使')],
      when='920年同州战后本段；确日未载',place='崇州',
      note='温昭图复用已发布温韬身份勘误；攻崇州不等于已取崇州。')
event('dou_wei_advises_wen_tao_transfer','窦维劝温韬表请移镇',17,
      '帝使供奉官窦维说之曰：“公所有者华原、美原两县耳，虽名节度使，实一镇将，比之雄籓，岂可同日语也，公有意欲之乎？”昭图曰：“然。”维曰：“当为公图之。”即教昭图表求移镇，',
      [('窦维','奉梁帝命劝温昭图请移镇的供奉官'),('温昭图','接受劝说并表请移镇者')],
      when='920年河中攻崇州后本段；确日未载',place='华原、美原',
      note='窦维关于两县及雄藩的话是劝说辞；本段未记温韬新任何镇，正式调镇留待后文。')
event('hua_wenqi_acts_jingsheng_liuhou','梁命华温琪权知静胜留后',17,
      '帝以汝州防御使华温琪权知静胜留后。',
      [('华温琪','由汝州防御使权知静胜留后者')],
      when='920年温昭图请移镇后本段；确日未载',place='静胜、汝州',
      note='“权知”保留临时主持身份，未写为正式节度使。')

event('shu_king_visits_wuding_returns_anyuan','蜀主至武定军，数日后还安远',18,
      '冬，十月，辛酉，蜀主如武定军，数日，复还安远。',
      [('蜀主','自安远至武定军数日后返回者')],
      when='920年十月辛酉出行，数日后返回；还日未载',place='武定军、安远',
      note='数日不是固定天数，未计算返程日期。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(14, 19):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明六年第14—18段；晋援同州诸阶段、华温琪权知静胜及蜀武定行还。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=920,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(14, 19)], next_paragraph=Q[19]['id'],
    coverage='卷271贞明六年第14—18段；同州攻援、罗文寨与渭水追击、静胜换守、蜀武定行还。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[14]['id'],'note':'主书援军到达未记确月，旧书传记另记九月，保留各书纪时。'},
      {'paragraph_id':Q[15]['id'],'note':'劝归梁诸子未点名；朱友谦追述旧援，不造本年回顾战争。'},
      {'paragraph_id':Q[16]['id'],'note':'罗文寨败退与渭水追击分阶段；旧书沙苑牧马者王建及按本姓王后赐姓名证据复用李建及。下邽／奉先行军地名异说并列，旧书内欧阳史注文不作独立旧史本体。'},
      {'paragraph_id':Q[17]['id'],'note':'温昭图复用温韬；窦维教请移镇及华温琪权知留后有别，未提前记温韬正式新镇。'},
      {'paragraph_id':Q[18]['id'],'note':'辛酉出行与数日后返回保留原相对日期，未臆定还日。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
