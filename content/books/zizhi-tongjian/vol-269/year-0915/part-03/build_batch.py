"""Curate consecutive Tongjian vol. 269, 915 paragraphs 8–11."""
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
main = 'tongjian-269-915-wei'
old_wei = 'jiuwudaishi-028-wei'
old_may = 'jiuwudaishi-008-may'
new_wei = 'xinwudaishi-005-jin-wei'
specs = [
    (main, P / 'sources/library' / main, '5b089ca3', '司马光等'),
    (old_wei, P / 'sources/library' / old_wei, '5b089ca3', '薛居正等'),
    (old_may, P / 'sources/library' / old_may, '5b089ca3', '薛居正等'),
    (new_wei, P / 'sources/library' / new_wei, '5b089ca3', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p008-p011',
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
for n in range(8, 12):
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
    ck = f'claim_zztj_269_0915_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'李存审': '符存审'}.get(name, name)
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


# p008: distinguish the relief movement, advice, execution, and incorporation.
event('jin_moves_linqing', '李存勖应贺德伦求援，遣符存审据临清并率军东下', 8,
      '晋王得贺德伦书，命马步副总管李存审自赵州引兵进据临清。五月，存审至临清，刘鄩屯洹水。贺德伦复遣使告急于晋，晋王引大军自黄泽岭东下，与存审会于临清，犹疑魏人之诈，按兵不进。',
      [('李存勖','接求援书后调军东下并暂驻临清的晋王'),('贺德伦','再度遣使向晋军告急者'),('符存审','以李存审之名率军从赵州进临清者'),('刘鄩','此时驻屯洹水的梁将')],
      when='915年四月至五月；符存审五月抵临清', place='赵州、临清、黄泽岭、洹水',
      note='李存审复用既有符存审主体；晋王最初按兵不进，未写作即刻入魏州。')
claim('event','event_zztj_269_0915_jin_moves_linqing','description',
      '《旧五代史》卷二十八亦记晋王遣李存审屯临清并自晋阳东下。',8,
      '帝命馬步副總管李存審自趙州帥師屯臨清，帝自晉陽東下，與存審會。',
      '旧书称其名李存审，与本站既有符存审同一主体；卷二十八后文转引《通鉴》部分不作独立补证。',old_wei,'corroborates')
event('sikong_ting_advises_jin', '司空颋奉贺德伦命劝晋王先除张彦', 8,
      '德伦遣判官司空颋犒军，密言于晋王曰：“除乱当除根。”因言张彦凶狡之状，劝晋王先除之，则无虞矣。王默然。',
      [('贺德伦','遣司空颋入晋营的魏州节度使'),('司空颋','密劝晋王先除张彦的判官'),('李存勖','听取建议但当时未答的晋王'),('张彦','被建议先行除去的魏州乱军首领')],
      when='915年五月晋王至临清后；确日未载', place='临清晋营',
      note='原文只记密劝与晋王沉默，不推定事先承诺杀张彦。')
claim('event','event_zztj_269_0915_sikong_ting_advises_jin','description',
      '《旧五代史》卷二十八记司空颋劝晋王剪除张彦。',8,
      '賀德倫遣從事司空頲至軍，密啟張彥狂勃之狀，且曰：「若不剪此亂階，恐貽後悔。」',
      '颋、頲为繁简字形；两书劝告措辞相近但不逐字同。',old_wei,'corroborates')
event('zhang_yan_executed', '李存勖于永济斩张彦及其党七人', 8,
      '晋王进屯永济，张彦选银枪效节五百人，皆执兵自卫，诣永济谒见，王登驿楼语之曰：“汝陵胁主帅，残虐百姓，数日中迎马诉冤者百馀辈。我今举兵而来，以安百姓，非贪人土地。汝虽有功于我，不得不诛以谢魏人。”遂斩彦及其党七人，馀众股栗。',
      [('李存勖','在永济下令斩张彦等八人的晋王'),('张彦','带银枪效节军五百人赴见并被斩者')],
      when='915年五月；确日未载', place='永济',
      note='被斩者为张彦及其党七人，合八人；五百人为随行兵，不推为被杀人数。')
claim('event','event_zztj_269_0915_zhang_yan_executed','description',
      '《旧五代史》卷二十八记晋王斩张彦及同恶七人。',8,
      '遽令斬彥及同惡者七人，軍士股栗，帝親加慰撫而退。',
      '与通鉴所记张彦及七人被斩相合；旧书此处按晋王方记载。',old_wei,'corroborates')
claim('event','event_zztj_269_0915_zhang_yan_executed','description',
      '《新五代史》卷五概记晋王在永济诛张彦。',8,
      '行至永濟，誅其亂首張彥', '新书本纪概述，不列七名同党。',new_wei,'corroborates')
event('jin_reforms_silver_spear_guard', '李存勖赦免余众并收编张彦银枪军为帐前银枪都', 8,
      '王召谕之曰：“罪止八人，馀无所问。自今当竭力为吾爪牙。”众皆拜伏，呼万岁。明日，王缓带轻裘而进，令张彦之卒擐甲执兵，翼马而从，仍以为帐前银枪都。众心由是大服。',
      [('李存勖','宣布仅罪及八人并收编银枪军的晋王')],
      when='915年斩张彦后次日；确日未载', place='永济至魏州',
      note='收编对象为张彦旧部；旧书和新书也称帐前银枪，未据此推定全部军额。')
claim('event','event_zztj_269_0915_jin_reforms_silver_spear_guard','description',
      '《新五代史》卷五记晋王以张彦兵五百自卫，号帐前银枪军。',8,
      '以其兵五百自衞，號帳前銀槍軍。',
      '新书概述五百人为此时接收兵数，不回填杨师厚生前全部银枪效节都规模。',new_wei,'corroborates')
# p009: opposing deployments on the Wei county river line.
event('liu_xun_moves_weixian', '刘鄩率万余梁兵自洹水趋魏县，晋军分屯临清与魏县', 9,
      '刘鄩闻晋军至，选兵万馀人，自洹水趣魏县。晋王留李存审屯临清，遣史建瑭屯魏县以拒之，王自引亲军至魏县，与鄩夹河为营。',
      [('刘鄩','率万余梁兵自洹水趋魏县者'),('李存勖','亲率晋军与刘鄩隔河扎营者'),('符存审','以李存审之名留守临清的晋将'),('史建瑭','奉命在魏县抵御梁军的晋将')],
      when='915年五月；确日未载', place='洹水、魏县、临清',
      note='万余为主书记数；夹河为营表示对峙，本段未记交战结果。')
claim('event','event_zztj_269_0915_liu_xun_moves_weixian','description',
      '《旧五代史》卷二十八记刘鄩率精兵万人至魏县，李存审与晋王分兵抵御。',9,
      '梁將鄩聞帝至，以精兵萬人自洹水趣魏縣，帝命李存審帥師禦之，帝率親軍於魏縣西北，夾河為柵。',
      '主书万余，旧书万人；人数与部署分别保留，旧书此句未写临清留守。',old_wei,'adds')
# p010: Liang response and succession after Niu Cunji's death.
event('liang_sends_niu_yangliu', '朱友贞闻魏博叛，遣牛存节驻杨刘声援刘鄩', 10,
      '帝闻魏博叛，大悔惧，遣天平节度使牛存节将兵屯杨刘，为鄩声援。',
      [('朱友贞','派牛存节援刘鄩的梁帝'),('牛存节','受命驻杨刘声援刘鄩的天平节度使'),('刘鄩','获牛存节军声援的梁将')],
      when='915年五月条；确日未载', place='杨刘',
      note='“悔惧”是通鉴所记梁帝心理，不另推定公开诏令措辞。')
event('niu_cunjie_dies_wang_tan_replaces', '牛存节病卒，朱友贞以王檀代之', 10,
      '会存节病卒，以匡国节度使王檀代之。',
      [('牛存节','任军中病卒的梁将'),('朱友贞','命王檀代牛存节的梁帝'),('王檀','从匡国节度使转代牛存节声援军务者')],
      when='915年五月条；确日未载',
      note='主书只称病卒和替任，未载病名；旧书卷八明确五月卒。')
claim('event','event_zztj_269_0915_niu_cunjie_dies_wang_tan_replaces','description',
      '《旧五代史》卷八称节度使牛存节五月薨。',10,
      '節度使牛存節薨。', '旧书记五月死亡；不提供死因。',old_may,'adds')
# p011: only the beginning of the siege belongs here; its later duration is a retrospective claim.
event('liu_zhijun_sieges_binzhou', '李茂贞遣刘知俊围邠州，霍彦威坚守', 11,
      '岐王遣彰义节度使刘知俊围邠州，霍彦威固守拒之。',
      [('李茂贞','遣刘知俊攻邠州的岐王'),('刘知俊','率岐军围邠州的彰义节度使'),('霍彦威','率守军抵御围城者')],
      when='915年五月条；围城起日未载', place='邠州',
      note='本段只记围攻开始与守御，未把后续围城结果定在此时。')
claim('event','event_zztj_269_0915_liu_zhijun_sieges_binzhou','description',
      '《旧五代史》卷八记李茂贞遣刘知俊围邠州，霍彦威守御；另追叙围城十四月。',11,
      '凡攻圍十四月，節度使霍彥威、諸軍都指揮使黃貴堅守捍寇',
      '十四月是旧书对整个围城的回顾，不能写成915年五月即告结束。',old_may,'adds')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8, 12):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第8—11段连续处理；晋援魏、张彦被斩、银枪军收编与梁岐两线军事行动分录，旧书围城十四月只作后续回顾。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(8, 12)], next_paragraph=Q[12]['id'],
    coverage='卷269贞明元年五月第8—11段；晋王入魏前的军事布置、张彦被斩与银枪军收编、刘鄩和牛存节、邠州围城。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[9]['id'],'note':'刘鄩兵力通鉴作万余，旧五代史卷28作万人；不合计或改成精确数。'},
      {'paragraph_id':Q[11]['id'],'note':'旧五代史卷8所记围城十四月是追叙，不能提前录作915年五月终局。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
