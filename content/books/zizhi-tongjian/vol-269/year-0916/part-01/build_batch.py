"""Curate consecutive Tongjian vol. 269, 916 paragraphs 1–4."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 39))
main = 'tongjian-269-915-winter'
main2 = 'tongjian-269-916-battle'
new54 = 'xinwudaishi-054-li-yu'
new61 = 'xinwudaishi-061-ma-qian'
old08 = 'jiuwudaishi-008-liu-xun-defeat'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-08/sources/library' / main, 'b1919250', '司马光等'),
    (main2, P / 'sources/library' / main2, '6d9827c7', '司马光等'),
    (new54, ROOT / 'content/books/zizhi-tongjian/vol-262/year-0900/part-04/sources/library' / new54, '7db9c9d', '欧阳修'),
    (new61, P / 'sources/library' / new61, '6d9827c7', '欧阳修'),
    (old08, P / 'sources/library' / old08, '6d9827c7', '薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p001-p004',
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
for n in range(1, 5):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
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

def choose_source(quote):
    for key in (main, main2):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source in (main, main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明二年（916）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0916_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main, main2):
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'全昱':'朱全昱','友谅':'朱友谅','硃瑾':'朱瑾','李存审':'符存审','晋王':'李存勖','吴王':'杨隆演','蜀主':'王建','帝':'朱友贞'}.get(name,name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=['馬謙'] if name=='马谦' else [], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明二年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=916):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0916_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '916年本段条；确日未载', dynasty='五代十国',
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
          '追叙确年不明。' if year is None else '按主书段落次序；干支未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0916_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p001: keep the retrospective "久之" separate from the January appointments.
event('zhu_quanyu_dies','宣武节度使朱全昱去世',1,
      '春，正月，宣武节度使、守中书令、广德靖王全昱卒。',
      [('朱全昱','正月去世的宣武节度使')],when='916年春正月；确日未载',place='后梁',
      note='原文省姓“全昱”，按既有朱全昱身份；不反推卒日。')
event('li_yu_appointed','后梁召李愚为左拾遗、崇政院直学士',1,
      '帝闻前河南府参军李愚学行，召为左拾遗，充崇政院直学士。',
      [('朱友贞','闻李愚学行并召任者'),('李愚','被召任左拾遗、崇政院直学士者')],
      when='916年春正月条；确日未载',place='后梁朝廷',
      note='“闻”只说明任命缘由是获知其学行，不单独创设荐举者。')
claim('event','event_zztj_269_0916_li_yu_appointed','description',
      '《新五代史》卷五十四称李愚由李延光屡荐而获召，后拜左拾遗、崇政院直学士。',1,
      '延光以經術事梁末帝為侍講，數稱薦愚，愚由此得召。久之，拜左拾遺、崇政院直學士。',
      '新书增加荐举背景；“久之”不拿来改写通鉴正月条任命日期。',new54,'adds')
event('li_yu_etiquette_dispute','李愚见衡王朱友谅仅行长揖，后梁帝责问',1,
      '衡王友谅贵重，李振等见，皆拜之愚独长揖，帝闻而让之',
      [('李愚','对衡王只行长揖并向皇帝解释者'),('朱友谅','受见礼的衡王'),('李振','拜见衡王者'),('朱友贞','责问李愚礼节的皇帝')],
      when='916年春正月条；确日未载',place='后梁朝廷',
      note='“李振等”只明确李振，未给其他拜者姓名；长揖与拜礼按原文区分。')
event('li_yu_later_dismissed','李愚后来因刚直罢为邓州观察判官',1,
      '久之，竟以抗直罢为邓州观察判官。',
      [('李愚','后因刚直被罢任邓州观察判官者')],
      when='见于916年正月条追叙“久之”；实际年未定',place='邓州',year=None,
      note='“久之”表示距前事一段时间，不能硬定于916年。')
# p002.
event('li_jichong_shu_offices','蜀主授李继崇武泰节度使、兼中书令、陇西王',2,
      '蜀主以李继崇为武泰节度使、兼中书令、陇西王。',
      [('王建','授予李继崇官爵的蜀主'),('李继崇','受授武泰节度使、兼中书令、陇西王者')],
      when='916年春正月条；确日未载',place='前蜀朝廷',
      note='只记录本段任命，不把915年秦州降蜀重录。')
# p003: the coup attempt, advice, and suppression are distinguishable acts.
event('wu_guards_seize_king','吴宿卫将马谦、李球劫吴王并取库兵讨徐知训',3,
      '二月，辛丑夜，吴宿卫将马谦、李球劫吴王登楼，发库兵讨徐知训。',
      [('马谦','劫吴王并发库兵的宿卫将'),('李球','劫吴王并发库兵的宿卫将'),('杨隆演','被劫登楼的吴王'),('徐知训','被讨伐目标')],
      when='916年二月辛丑夜；未换算公历日',place='吴国都城',
      note='吴王按当时杨隆演既有身份；“讨”是兵变方宣称的行动，不作合法性判断。')
claim('event','event_zztj_269_0916_wu_guards_seize_king','description',
      '《新五代史》卷六十一亦记李球、马谦挟杨隆演登楼并取库兵。',3,
      '宿衞將李球、馬謙挾隆演登樓，取庫兵以誅知訓',
      '新书作繁体“馬謙”，姓名归同一主体；“誅知訓”为兵变方目的，未遂。',new61,'corroborates')
claim('person',people['马谦'],'aliases','《新五代史》将马谦写作馬謙。',3,
      '宿衞將李球、馬謙挾隆演登樓',
      '繁简字形归入本批同一人物，原文保持馬字。',new61,'adds')
event('yan_kekiu_stabilizes_xu','严可求劝徐知训勿出走，随后安定府中',3,
      '知训将出走，严可求曰：“军城有变，公先弃众自去，众将何依！”知训乃止。众犹疑惧，可求阖户而寝，鼾息闻于外，府中稍安。',
      [('徐知训','欲出走后听劝留下者'),('严可求','劝留徐知训并镇定府中者')],
      when='916年二月辛丑夜至壬寅前',place='吴国都城',
      note='“府中稍安”是原文结果，不推成兵变已结束。')
event('zhu_jin_suppresses_coup','硃瑾率外众击溃兵变，马谦、李球被斩',3,
      '诸道副都统硃瑾自润州至，视之，曰：“不足畏也。”返顾外众，举手大呼，乱兵皆溃，擒谦、球，斩之。',
      [('朱瑾','原文作硃瑾，率外众击溃兵变者'),('马谦','兵败被擒斩者'),('李球','兵败被擒斩者')],
      when='916年二月壬寅；未换算公历日',place='吴国天兴门外',
      note='硃瑾与既有朱瑾同人；原文所见行动是其举手大呼、外众进击。')
claim('person',people['朱瑾'],'aliases','《资治通鉴》本段作硃瑾。',3,
      '诸道副都统硃瑾自润州至',
      '硃字为朱的异体写法，复用朱瑾UUID；别名待同步。')
claim('event','event_zztj_269_0916_zhu_jin_suppresses_coup','description',
      '《新五代史》卷六十一亦记朱瑾率外兵前视兵阵、兵变者被斩。',3,
      '朱瑾適自外來，以一騎前視其陣，曰：「此不足為也。」因反顧一麾，外兵爭進，遂斬球、謙，而亂兵皆潰。',
      '新书作朱瑾，和主书“硃瑾”按同人匹配；一骑前视为新书细节。',new61,'corroborates')
# p004: keep the maneuver, the vanguard defeat, the main battle, and escape distinct.
event('jin_feigns_retreat','晋王李存勖佯称归晋阳以诱刘鄩',4,
      '晋王乃留副总管李存审守营，自劳军于贝州，声言归晋阳。鄩闻之，奏请袭魏州。',
      [('李存勖','声称返回晋阳并留军守营的晋王'),('符存审','留守晋军营地的副总管'),('刘鄩','闻讯请求袭魏州的梁将')],
      when='916年二月后、三月前后；确日未载',place='贝州、魏州',
      note='“声言归晋阳”是佯示，未称晋王真返晋阳；旧五代史卷八记三月大战。')
claim('event','event_zztj_269_0916_jin_feigns_retreat','description',
      '《旧五代史》卷八亦记晋王诈称归太原，刘鄩信之。',4,
      '既而晉王詐言歸太原，劉鄩以為信。',
      '太原与通鉴晋阳为同一军事目标的不同地名表达；不把新书三月日期套给佯言当天。',old08,'corroborates')
event('yang_yanzhi_vanguard_defeated','杨延直率军赴魏州，夜间遭晋军突击溃败',4,
      '鄩令澶州刺史杨延直引兵万人会于魏州，延直夜半至城南，城中选壮士五百潜出击之，延直不为备，溃乱而走。',
      [('刘鄩','命杨延直会师者'),('杨延直','率梁军赴魏州并遭夜袭者')],
      when='916年故元城会战前夜；确日未载',place='魏州城南',
      note='万人、五百人为主书记数；未推定夜袭军具体统帅。')
event('liu_xun_defeated_at_yuancheng','刘鄩梁军在故元城西受晋军合围而大败',4,
      '李嗣源以城中兵出战，晋王亦自贝州至，与嗣源当其前。鄩见之，惊曰：“晋王邪！”引兵稍却，晋王蹑之，至故元城西，与李存审遇。晋王为方陈于西北，存审为方陈于东南，鄩为圆陈于其中间，四面受敌。合战良久，梁兵大败',
      [('刘鄩','梁军主将，败于故元城西'),('李存勖','从西北方围击梁军的晋王'),('符存审','从东南方围击梁军的晋将'),('李嗣源','率魏州城中兵出战的晋将')],
      when='916年故元城会战；《旧五代史》记三月，确日未载',place='故元城西',
      note='晋军形成夹击，主书称梁步卒七万，此处不将其作精确死者数。')
claim('event','event_zztj_269_0916_liu_xun_defeated_at_yuancheng','description',
      '《旧五代史》卷八记三月刘鄩与晋王大战于故元城而败。',4,
      '三月，劉鄩率師與晉王大戰於故元城，鄩軍敗績。',
      '旧书明确三月，主书该段承二月下而未在段首重写月，保留两种时间粒度。',old08,'corroborates')
event('liu_xun_escapes_to_huazhou','刘鄩率数十骑突围，经黎阳渡河退保滑州',4,
      '鄩引数十骑突围走。梁步卒凡七万，晋兵环而击之，败卒登木，木枝为之折，追至河上，杀溺殆尽。鄩收散卒自黎阳渡河，保滑州。',
      [('刘鄩','率残部突围后退保滑州的梁将')],
      when='916年故元城会战后；确日未载',place='故元城、黎阳、滑州',
      note='“梁步卒凡七万”是参战兵数记载，不等于死者七万；“杀溺殆尽”为史书叙述。')
claim('event','event_zztj_269_0916_liu_xun_escapes_to_huazhou','description',
      '《旧五代史》卷八亦记刘鄩从黎阳渡河奔滑州。',4,
      '鄩自黎陽濟河奔滑州。',
      '与主书退路相合；伤亡数不据旧书推算。',old08,'corroborates')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 5):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明二年第1—4段连续处理；李愚后罢官追叙未定年，马谦繁体归同人，故元城之战与旧五代史三月纪年并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=916,
    primary_source_key=main, primary_source_keys=[main,main2],
    paragraphs=[Q[n]['id'] for n in range(1, 5)], next_paragraph=Q[5]['id'],
    coverage='卷269贞明二年正月、二月至故元城会战第1—4段；任官、吴国兵变和梁晋战事。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[1]['id'],'note':'李愚因抗直“久之”被罢任的确年不明，事件年份为空；新五代史所记李延光荐举为补证。'},
      {'paragraph_id':Q[3]['id'],'note':'原文硃瑾与既有朱瑾同人；新五代史繁体馬謙按马谦别名，不另建人物。'},
      {'paragraph_id':Q[4]['id'],'note':'旧五代史卷八明记三月故元城战，通鉴该段未显写月；梁步卒七万非死亡人数。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
