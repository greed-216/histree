"""Curate consecutive Tongjian volume 270, year 919, paragraphs 6–8."""
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
    ('tongjian-270-919-lanshan', P / 'sources/library/tongjian-270-919-lanshan', '9e9d8b9a', '司马光等'),
    ('xinwudaishi-061-wu-kingship', P / 'sources/library/xinwudaishi-061-wu-kingship', '9e9d8b9a', '欧阳修'),
    ('jiuwudaishi-134-wu-kingship', P / 'sources/library/jiuwudaishi-134-wu-kingship', '9e9d8b9a', '薛居正等'),
    ('jiuwudaishi-133-langshan-variant', P / 'sources/library/jiuwudaishi-133-langshan-variant', 'c4b7d130', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0919-p006-p008',
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
for n in range(6, 9):
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
    ck = f'claim_zztj_270_0919_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'蜀主':'王宗衍','晋王':'李存勖','汉主岩':'刘岩',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
            '徐知诰':'李昪','徐知誥':'李昪'}.get(name, name)
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
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0919_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('qian_liu_sends_fleet_against_wu','钱镠命钱传瓘率五百战舰自东洲攻吴',6,
      '诏吴越王镠大举讨淮南。镠以节度副大使传瓘为诸军都指挥使，帅战舰五百艘，自东洲击吴。',
      [('吴越王镠','奉诏出兵、任钱传瓘为都指挥使者'),('传瓘','率吴越战舰从东洲攻吴者')],
      place='东洲、淮南',note='主书未明诏命发出日；五百艘为原书数字，不核作实际存量。')
event('wu_orders_peng_and_chen_to_resist','吴命彭彦章与陈汾抵御吴越水师',6,
      '吴遣舒州刺史彭彦章及裨将陈汾拒之。',
      [('彭彦章','奉吴命抵御吴越的舒州刺史'),('陈汾','奉吴命抵御吴越的裨将')],
      place='吴、东洲',note='彭彦章复用909年袁州被执主体；十年间任职迁移尚待其他书证，不据同名再建一人。')

event('xu_wen_petitions_wu_emperor','徐温率将吏请吴王称帝，吴王不许',7,
      '吴徐温帅将吏籓镇请吴王称帝，吴王不许。',
      [('徐温','率将吏请称帝者'),('吴王','拒绝称帝者')],
      when='919年四月前；主书确日未载',place='吴',
      note='主书只记请称帝而被拒；新五代史写春二月，作为独立出处，不覆盖主书。')
claim('event','event_zztj_270_0919_xu_wen_petitions_wu_emperor','description',
      '《新五代史》记天祐十六年春二月徐温请杨隆演即天子位，未获准。',7,
      '十六年，春二月，溫率將吏請隆演即天子位，不許。',
      '补书明指杨隆演及春二月；主书无月，留作补充纪时。',
      'xinwudaishi-061-wu-kingship','adds')
event('yang_longyan_takes_wu_kingship','杨隆演四月戊戌即吴国王位并改元武义',7,
      '夏，四月，戊戌朔，即吴国王位。大赦，改元武义。建宗庙社稷，置百官，宫殿文物皆用天子礼。以金继土，腊用丑。',
      [('吴王','即吴国王位、大赦改元者')],
      when='919年四月戊戌朔',place='吴',
      note='称“吴国王”并用天子礼，不写主书认定其即皇帝位。')
claim('event','event_zztj_270_0919_yang_longyan_takes_wu_kingship','description',
      '《新五代史》记徐温奉册宝尊杨隆演为吴王，改天祐十六年为武义元年。',7,
      '夏四月，溫奉玉冊、寶綬尊隆演即吳王位。建宗廟、社稷，設百官如天子之制，改天祐十六年為武義元年，大赦境內',
      '补书明确杨隆演人名与改元，书中文字保留繁体。',
      'xinwudaishi-061-wu-kingship','corroborates')
claim('event','event_zztj_270_0919_yang_longyan_takes_wu_kingship','description',
      '《旧五代史》卷一百三十四作“温乃册渭为天子”，又记武义元年。',7,
      '溫乃冊渭為天子，國號大吳，改唐天祐十六年為武義元年。',
      '旧书“渭”和“天子”与主书“吴国王位”及新书“隆演”有字词差异；保留异文，纸本待核，不据此新建杨渭主体。',
      'jiuwudaishi-134-wu-kingship','conflicts')
event('wu_posthumous_honors','吴改谥前王、尊母太妃',7,
      '改谥武忠王曰孝武王，庙号太祖，威王曰景王，尊母为太妃；',
      [('杨行密','被改谥孝武王、上庙号太祖者'),('杨渥','被改谥景王者')],
      when='919年四月即位后本段；确日未载',place='吴',
      note='武忠王为杨行密、威王为杨渥，依据前文已识别主体；“母”本段无名，不新建人物。')
claim('event','event_zztj_270_0919_wu_posthumous_honors','description',
      '《新五代史》亦记追尊杨行密孝武王、庙号太祖及杨渥景王。',7,
      '追尊行密孝武王，廟號太祖，渥景王，廟號烈祖。',
      '新书另载杨渥庙号烈祖，主书本段未明，此项只作补书附见。',
      'xinwudaishi-061-wu-kingship','adds')
event('wu_high_office_appointments','吴王就位后任徐温等人中枢官职',7,
      '以徐温为大丞相、都督中外诸军事、诸道都统、镇海、宁国节度使、守太尉兼中书令、东海郡王，以徐知诰为左仆射、参政事兼知内外诸军事，仍领江州团练使，以扬府左司马王令谋为内枢密使，营田副使严可求为门下侍郎，盐铁判官骆知祥为中书侍郎，前中书舍人卢择为吏部尚书兼太常卿，掌书记殷文圭为翰林学士，馆驿巡宫游恭为知制诰，前驾部员外郎杨迢为给事中。',
      [('徐温','受大丞相、东海郡王等职爵者'),('徐知诰','受左仆射、参政事等职者'),
       ('王令谋','受内枢密使者'),('严可求','受门下侍郎者'),('骆知祥','受中书侍郎者'),
       ('卢择','受吏部尚书兼太常卿者'),('殷文圭','受翰林学士者'),
       ('游恭','受知制诰者'),('杨迢','受给事中者')],
      when='919年四月即位后本段；确日未载',place='吴',
      note='职位逐人按主书对应；徐知诰复用李昪主体，新书异名“徐知誥”只用于匹配。')
event('langshan_river_wu_yue_victory','钱传瓘乙巳在狼山江败吴水军',8,
      '钱传瓘与彭彦章遇；传瓘命每船皆载灰、豆及沙，乙巳，战于狼山江。吴船乘风而进，传瓘引舟避之，既过，自后随之。吴回船与战，传瓘使顺风扬灰，吴人不能开目；及船舷相接，传瓘使散沙于己船而散豆于吴船，豆为战血所渍，吴人践之皆僵仆。传瓘因纵火焚吴船，吴兵大败。',
      [('钱传瓘','在狼山江指挥吴越水师者'),('彭彦章','率吴水师迎战者')],
      when='919年四月乙巳',place='狼山江',
      note='主书记录灰、豆、沙及火攻战术；战斗结果另以原文记载，不换算公历日。')
claim('event','event_zztj_270_0919_langshan_river_wu_yue_victory','description',
      '钱传瓘以扬灰、撒沙豆、纵火焚船之法击败吴水师。',8,
      '传瓘因纵火焚吴船，吴兵大败。',
      '主书概括战果；战术细节仍在本段原文快照，可逐字回查。')
claim('event','event_zztj_270_0919_langshan_river_wu_yue_victory','description',
      '通鉴记吴越俘吴裨将七十人，斩首千馀级，焚战舰四百艘。',8,
      '传瓘俘吴裨将七十人，斩首千馀级，焚战舰四百艘。',
      '史载战果数字照录，未以其他史料交叉核实，不作为现代统计。')
claim('event','event_zztj_270_0919_langshan_river_wu_yue_victory','description',
      '《旧五代史》钱元瓘传亦载东洲水战及火筏扬灰，但系于贞明四年，称俘彭彦章。',8,
      '梁貞明四年夏，镠大舉伐吳，以元瓘為水戰諸軍都指揮使。戰棹抵東洲，吳人以舟師拒戰，元瓘為火筏順風揚灰以岔之，白晝如霧，吳師迷方，遂敗之，擒軍使彭彥章並軍校七十餘人，得戰艦四百隻。',
      '旧书元瓘为钱传瓘后名；记年918与通鉴919不同，称俘彭彦章与通鉴自杀不同。保留并列，不将异文改作主书事实，纸本待核。',
      'jiuwudaishi-133-langshan-variant','conflicts')
event('peng_yanzhang_suicide_chen_fen_holds_back','彭彦章战败自杀，陈汾按兵不救',8,
      '彦章战甚力，兵尽，继之以木，身被数十创，陈汾按兵不救；彦章知不免，遂自杀。',
      [('彭彦章','战败后自杀的吴将'),('陈汾','按兵不救的吴裨将')],
      when='919年狼山江战中；确日未另载',place='狼山江',
      note='复用909年被执彭彦章主体，主书叙事连续到本次自杀；909—919间仕履待核。')
event('wu_executes_chen_fen_supports_peng_family','吴诛陈汾并拨其家产抚恤彭彦章家属',8,
      '吴人诛汾，籍没家赀，以其半赐彦章家，禀其妻子终身。',
      [('陈汾','被吴诛杀及籍没者'),('彭彦章','家属获抚恤的阵亡将领')],
      when='919年狼山江战后；确日未载',place='吴',
      note='“妻子”指其家属，不从中推定未具名妻儿人数。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(6, 9):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明五年第6—8段；吴越攻吴、杨隆演即吴王位及狼山江战。旧书“渭”“天子”异文并存，纸本待核。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(6, 9)], next_paragraph=Q[9]['id'],
    coverage='卷270贞明五年第6—8段；吴越进攻吴、杨隆演即吴王位及狼山江之战。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[7]['id'],'note':'新五代史作杨隆演即吴王；旧五代史作“渭”“天子”，保留异文不改主书，也不据电子本将杨渭立为新主体。'},
      {'paragraph_id':Q[8]['id'],'note':'彭彦章与909年被吴执的袁州刺史同名，暂复用既有主体；其间仕履未核。旧五代史卷133钱元瓘传系战于918年并称俘彭彦章，与通鉴919年自杀相抵牾，纸本待核。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
