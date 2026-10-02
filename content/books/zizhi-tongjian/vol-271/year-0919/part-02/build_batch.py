"""Curate consecutive Tongjian volume 271, year 919, paragraphs 5–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 9))
specs = [
    ('tongjian-271-919-autumn-winter', YEAR / 'part-01/sources/library/tongjian-271-919-autumn-winter', 'd78219e5', '司马光等'),
    ('jiuwudaishi-009-november-wangzan', P / 'sources/library/jiuwudaishi-009-november-wangzan', '99029069', '薛居正等'),
    ('jiuwudaishi-009-december-wangzan', P / 'sources/library/jiuwudaishi-009-december-wangzan', '99029069', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0919-p005-p008',
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
for n in range(5, 9):
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
        citation = f'卷271·贞明五年（919）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0919_02_{len(B["claims"])+1:04d}'
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
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','李紹榮':'元行钦','全师朗':'王宗朗'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271贞明五年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='919年本段条；确日未载', note='', year=919, place='吴'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0919_' + code
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
        edge = 'participation_zztj_271_0919_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('liu_xun_appointed_taining','梁任刘鄩为泰宁节度使、同平章事',5,
      '丁丑，以刘鄩为泰宁节度使、同平章事。',
      [('刘鄩','受任泰宁节度使、同平章事者')],when='919年十一月丁丑',place='泰宁',
      note='旧书另记兗州安抚制置使及赏平兗之功，主书任官从原句。')
claim('event','event_zztj_271_0919_liu_xun_appointed_taining','description',
      '《旧五代史》卷九同记十一月丁丑任刘鄩，并称“赏平兗之功”。',5,
      '十一月丁丑，以兗州安撫製置使、特進、檢校太傅、大彭郡開國公劉鄩為兗州節度使、開府儀同三司、檢校太尉、同平章事，賞平兗之功也。',
      '旧书作兗州节度使，主书作泰宁节度使；治所对应但保留两书官称原貌。',
      'jiuwudaishi-009-november-wangzan','adds')
event('wang_zan_fights_li_siyuan_qicheng','王瓒至戚城与李嗣源交战不利',5,
      '辛卯，王瓚引兵至戚城，与李嗣源战，不利。',
      [('王瓚','率兵至戚城与晋军交战的梁将'),('李嗣源','戚城交战的晋将')],
      when='919年十一月辛卯',place='戚城',note='旧书同日记王瓚遇晋军而退，未具称李嗣源。')
claim('event','event_zztj_271_0919_wang_zan_fights_li_siyuan_qicheng','description',
      '《旧五代史》卷九记王瓚至戚城遇晋军，“交綏而退”。',5,
      '辛卯，王瓚帥師至戚城，遇晉軍。交綏而退。',
      '旧书证戚城遭遇及退兵；是否为同一细部战况留待纸本校。',
      'jiuwudaishi-009-november-wangzan','corroborates')

event('liang_stores_grain_panzhang','梁军于潘张筑垒贮粮',6,
      '梁筑垒贮粮于潘张，距杨村五十里，',[],
      when='919年十二月前本段；确日未载',place='潘张、杨村',
      note='仅据主书保留距离与粮垒，不换算坐标。')
event('jin_intercepts_liang_supply_then_ambushed','晋王截梁饷而归，归途遭梁伏兵大败',6,
      '十二月，晋王自将骑兵自河南岸西上，邀其饷者，俘获而还；梁人伏兵于要路，晋兵大败。',
      [('晋王','亲率骑兵截梁饷后遭伏者')],when='919年十二月；确日未载',place='河南岸、要路',
      note='截饷得手与归途大败按原文先后同录，不写为持续胜利。')
event('li_shaorong_rescues_jin_king','李绍荣单骑击梁骑救晋王',6,
      '晋王以数骑走，梁数百骑围之，李绍荣识其旗，单骑奋击救之，仅免。',
      [('晋王','遭梁骑围而得救者'),('李绍荣','识晋王旗后单骑奋击救援者')],
      when='919年十二月截饷战后；确日未载',place='梁晋交战要路',
      note='李绍荣沿既有别名并入元行钦；原文称李绍荣。')
event('wang_zan_first_wins_captures_shi_junli','河南之战王瓒初胜，俘石君立等晋将',6,
      '戊戌，晋王复与王瓚战于河南，瓚先胜，获晋将石君立等；',
      [('晋王','戊戌河南交战的晋军统帅'),('王瓚','初胜并俘晋将的梁将'),('石君立','初战被俘的晋将')],
      when='919年十二月戊戌',place='河南',note='“先胜”只是本场第一阶段；旧书所记被俘将名有异文。')
claim('event','event_zztj_271_0919_wang_zan_first_wins_captures_shi_junli','description',
      '《旧五代史》卷九同记王瓚初获晋将，但被俘姓名作“石家才”。',6,
      '十二月戊戌，晉王領軍迫河南寨，王瓚率師禦之，獲晉將石家才。',
      '主书作石君立，旧书作石家才；不据音近或事件相同直接合并二名。',
      'jiuwudaishi-009-december-wangzan','conflicts')
event('wang_zan_defeated_retreats_north_city','王瓒继而大败，渡河退保北城',6,
      '既而大败，乘小舟渡河，走保北城，失亡万计。',
      [('王瓚','继初胜后大败并退保北城者')],when='919年十二月戊戌同场后段',place='河南、北城',
      note='“失亡万计”为主书量级措辞，不录作精确伤亡数。')
claim('event','event_zztj_271_0919_wang_zan_defeated_retreats_north_city','description',
      '《旧五代史》卷九记王瓚军不利后退保杨村寨。',6,
      '既而瓚軍不利，瓚退保楊村寨，晉人陷濮陽。',
      '两书同记王瓚败退；退保地名主书“北城”、旧书“杨村寨”，不擅作同地。',
      'jiuwudaishi-009-december-wangzan','conflicts')
event('shi_junli_rejects_liang_service','梁帝欲用石君立，石君立拒为梁效力',6,
      '帝闻石君立勇，欲将之，系于狱而厚饷之，使人诱之。君立曰：“我晋之败将，而为用于梁，虽竭诚效死，谁则信之！人各有君，何忍反为仇雠用哉！”帝犹惜之，尽杀所获晋将，独置君立。',
      [('石君立','被俘后拒为梁任用且独获留置的晋将')],
      when='919年十二月戊戌战后；确日未载',place='梁军',
      note='梁帝在本年系朱友贞；本句未说明石君立最后去向。')
event('jin_takes_puyang','晋王乘胜攻取濮阳',6,
      '晋王乘胜遂拔濮阳。',[('晋王','乘胜拔濮阳者')],
      when='919年十二月戊戌战后；确日未载',place='濮阳')
claim('event','event_zztj_271_0919_jin_takes_puyang','description',
      '《旧五代史》卷九同记晋军攻陷濮阳。',6,
      '晉人陷濮陽。','两书均记晋军取濮阳。',
      'jiuwudaishi-009-december-wangzan','corroborates')
event('dai_siyuan_replaces_wang_zan','梁召还王瓒，以戴思远代北面招讨使',6,
      '帝召王瓚还，以天平节度使戴思远代为北面招讨使，屯河上以拒晋人。',
      [('王瓚','被召还的原北面招讨使'),('戴思远','接任北面招讨使并屯河上者')],
      when='919年十二月濮阳失后；确日未载',place='河上',
      note='“代”明确职务交替，不据此推王瓚后续罪责。')

event('wang_zonglang_stripped_restores_quanshilang','蜀削王宗朗官爵，复姓名全师朗',7,
      '己酉，蜀雄武节度使兼中书令王宗朗有罪，削夺官爵，复其姓名曰全师朗，',
      [('王宗朗','被削官爵并恢复原姓名全师朗者')],
      when='919年十二月己酉',place='蜀',
      note='王宗朗与全师朗为同人；“有罪”未记具体罪名。')
event('sang_hongzhi_ordered_against_quanshilang','蜀命桑弘志讨全师朗',7,
      '命武定节度使兼中书令桑弘志讨之。',
      [('桑弘志','奉命讨全师朗的武定节度使'),('王宗朗','受讨命令针对者')],
      when='919年十二月己酉',place='蜀',
      note='这里只记讨伐命令，不推定已出兵或战果。')

event('wu_bans_private_weapons_banditry_rises','吴禁民私藏兵器，史载盗贼益繁',8,
      '吴禁民私畜兵器，盗贼益繁。',[],
      when='919年本段；确日未载',place='吴',
      note='原文把禁令与盗贼增多相连；不独立推算增幅。')
event('lu_shu_advocates_militia_wu_adopts','卢枢建议团结民兵，吴采纳',8,
      '御史台主簿京兆卢枢上言：“今四方分争，宜教民战。且善人畏法禁而奸民弄干戈，是欲偃武而反招盗也。宜团结民兵，使之习战，自卫乡里。”从之。',
      [('卢枢','上言教民战、团结民兵且建议获采纳的御史台主簿')],
      when='919年本段；确日未载',place='吴',
      note='“从之”证明采纳建议，不推出民兵编练规模或成效。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5, 9):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明五年第5—8段；刘鄩任官、王瓒戚城与河南战、蜀全师朗及吴民兵议。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=919,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(5, 9)], next_paragraph='zztj-v271-y0920-p001',
    coverage='卷271贞明五年第5—8段；刘鄩任官、梁晋河南之战、蜀将复姓名与吴民兵议。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[5]['id'],'note':'刘鄩职衔主书作泰宁节度使，旧书作兗州节度使；地名、职名原貌分别保留。'},
      {'paragraph_id':Q[6]['id'],'note':'石君立／石家才姓名异文、王瓒败退北城／杨村寨地名异文均保留，未自行合并；李绍荣匹配已证元行钦别名。'},
      {'paragraph_id':Q[7]['id'],'note':'王宗朗恢复全师朗本名，沿用既有UUID；讨伐命令不等于完成征伐。'},
      {'paragraph_id':Q[8]['id'],'note':'吴采纳卢枢民兵建议，未见实施范围及结果。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
