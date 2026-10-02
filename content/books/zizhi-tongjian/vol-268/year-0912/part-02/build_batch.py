"""Curate Tongjian 268, year 912, consecutive paragraphs 11-20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
main1 = 'tongjian-268-912-next'
new_liyu = 'xinwudaishi-061-liyu'
old_xue = 'jiuwudaishi-007-xue'
new_xue = 'xinwudaishi-002-xue'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0912-p011-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-01/sources/library' / main1, '425c28ca', '司马光等'),
    (new_liyu, P / 'sources/library' / new_liyu, '3d980bc5', '欧阳修'),
    (old_xue, P / 'sources/library' / old_xue, '3d980bc5', '薛居正等'),
    (new_xue, P / 'sources/library' / new_xue, '3d980bc5', '欧阳修'),
]
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
primary_texts = {main1: (source_dirs[main1] / 'source.txt').read_text()}
for n in range(11, 21):
    row=Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line']-1]
    assert row['text'] in primary_texts[main1],n

registry = {}
existing_relation_keys = set()
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    archived = json.loads(path.read_text())
    existing_relation_keys.update(row['key'] for row in archived['person_relationships'])
    for row in archived['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (path, row['name'])
        registry[row['name']] = row
aliases = {'吴越王镠':'钱镠','楚王殷':'马殷','蜀主':'王建',
           '王景仁':'王茂章','张宗奭':'张全义','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化二年（912）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0912_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,):
        book = json.loads((source_dirs[source] / 'paragraph.json').read_text())['book']
        supplements.append(dict(claim_key=ck, source_book=book, primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=supplement_relation))
    return ck

def person(name, n, role, quote):
    name = aliases.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷268乾化二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=912):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0912_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '912年本段条；确日未载', dynasty='五代十国',
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
          '段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_268_0912_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key,
                                       role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key

def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    if key in existing_relation_keys:
        reused.add(key)
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

event('wu_old_generals_discontent', '刘威、陶雅、李遇、李简不满徐温执政', 11,
      '吴镇南节度使刘威，歙州观察使陶雅，宣州观察使李遇，常州刺史李简，皆武忠王旧将，有大功，以徐温自牙将秉政，内不能平；李遇尤甚，常言：“徐温何人，吾未尝识面，一旦乃当国邪！”',
      [('刘威','对徐温执政不满的吴旧将'),('陶雅','对徐温执政不满的吴旧将'),('李遇','公开不满徐温执政的宣州将领'),('李简','对徐温执政不满的吴旧将'),('徐温','受吴旧将不满的执政者')],
      when='912年宣州围城前；确日未载',place='吴、宣州',
      note='“武忠王旧将”是原文群体身份，不由此推出四人结盟或共同叛乱。')
event('xu_jie_persuades_liyu', '徐玠途经宣州，劝李遇入见新王，言辞引发争执', 11,
      '馆驿使徐玠使于吴越，道过宣州，温使玠说遇入见新王，遇初许之；玠曰：“公不尔，人谓公反。”遇怒曰：“君言遇反，杀侍中者非反邪！”',
      [('徐玠','奉徐温命劝李遇入见新王的馆驿使'),('徐温','命徐玠说服李遇的吴执政者'),('李遇','先许入见而后与徐玠争执的宣州将领')],
      when='912年宣州围城前；确日未载',place='宣州',
      note='“侍中”原文释为威王；李遇的反问是其指责，不能据此直接立徐温杀威王的事实。')
event('xu_wen_sends_chai_to_xuanzhou', '徐温任王檀宣州制置使，遣柴再用、徐知诰率军赴宣州', 11,
      '温怒，以淮南节度副使王檀为宣州制置使，数遇不入朝之罪，遣都指挥使柴再用帅升、润、池、歙兵纳檀于宣州，升州副使徐知浩为之副。',
      [('徐温','命军纳王檀于宣州的吴执政者'),('王檀','获任宣州制置使的淮南节度副使'),('李遇','被数不入朝之罪的宣州将领'),('柴再用','率诸州兵赴宣州的都指挥使'),('徐知浩','随柴再用为副的升州副使徐知诰、李昪')],
      when='912年四月前后；确日未载',place='宣州、升州、润州、池州、歙州',
      note='底本“徐知浩”与《通鉴》卷268另一版本“徐知诰”及本卷后文“知诰”对校，归入已有李昪；原文不改。')
event('liyu_resists_siege', '李遇拒绝王檀接任，柴再用围攻宣州逾日未克', 11,
      '遇不受代，再用攻宣州，逾日不克。',
      [('李遇','拒绝交接宣州的原任将领'),('柴再用','围攻宣州逾日未克的吴将')],
      when='912年四月前后；确日未载',place='宣州',
      note='本段只到围攻未克，李遇出城与被杀见后续第23段，不能提前并入。')
claim('event','event_zztj_268_0912_liyu_resists_siege','description',
      '《新五代史》卷六十一亦记李遇拒受王壇代任、柴再用围宣州。',11,
      '溫聞之，怒，遣柴再用以兵送王壇代遇，且召之。遇疑不受命，再用圍之，',
      '新史“王壇”与主书“王檀”异字；职位与情境相合，但不据字形直接复用另一个王坛人物。该段还概述后续李遇被杀，暂留待通鉴后段录入。',new_liyu,'corroborates')

event('ma_yin_four_commands', '后梁加马殷四镇节度使及洪鄂行营都统', 12,
      '夏，四日，癸丑，以楚王殷为武安、武昌、静江、宁远节度使，洪、鄂四面行营都统。',
      [('马殷','获梁授四镇节度使及行营都统的楚王')],
      when='912年夏、癸丑；底本“四日”，异本作“四月”',place='武安、武昌、静江、宁远、洪州、鄂州',
      note='底本“四日”疑“四月”误字；《通鉴》卷268另一电子版本作“四月”，展示时间保留待核，不把“四日”当月中四日。')

event('zhu_youwen_asks_return', '朱友文朝见朱温，请其返回东都', 13,
      '乙卯，博王友文来朝，请帝还东都。',
      [('朱友文','来朝并请梁帝还东都的博王'),('朱温','接见朱友文的梁帝')],
      when='912年四月乙卯',place='魏州',
      note='乙卯属第12段所引四月后连续纪日，但底本“四日”误字尚待纸本核。')
event('zhu_wen_travel_weizhou_huazhou', '朱温离魏州，经黎阳久留，抵滑州', 13,
      '丁巳，发魏州；己未，至黎阳，以疾淹留；乙丑，至滑州。',
      [('朱温','因病在黎阳滞留后抵滑州的梁帝')],
      when='912年四月丁巳至乙丑',place='魏州、黎阳、滑州',
      note='“以疾淹留”只说明行程延误，不推具体病种。')

event('dong_zhuo_rebellion_suppressed', '董琢在维州起事，王建遣赵绰讨平', 14,
      '维州羌胡董琢反，蜀主遣保鸾军使赵绰讨平之。',
      [('董琢','在维州起事的羌胡首领'),('王建','遣军讨平维州起事的蜀主'),('赵绰','受命讨平董琢的保鸾军使')],
      when='912年四月；确日未载',place='维州',
      note='“羌胡”沿原文说明，不据此推现代民族身份；未见独立二十四史补证。')

event('zhu_wen_to_daliang', '朱温抵达大梁', 15,
      '己巳，帝至大梁。', [('朱温','于己巳抵达大梁的梁帝')],
      when='912年四月己巳',place='大梁')

event('liang_embassy_to_chu_lingnan', '朱温遣韦戬等赴潭州、广州调停楚与岭南冲突', 16,
      '帝闻岭南与楚相攻，甲戌，以右散骑常侍韦戬等为潭、广和叶使，往解之。',
      [('朱温','遣和叶使往调停楚与岭南冲突的梁帝'),('韦戬','奉命出使潭州与广州的右散骑常侍')],
      when='912年四月甲戌',place='潭州、广州',
      note='“和叶使”是原书使名；只录遣使，不推调停结果。')

event('zhu_wen_leaves_daliang', '朱温戊寅离开大梁', 17,
      '戊寅，帝发大梁。', [('朱温','于戊寅离开大梁的梁帝')],
      when='912年四月戊寅',place='大梁')

event('jin_reinforces_zhou_dewei', '李存勖遣符存审率吐谷浑、契苾骑兵会周德威', 18,
      '周德威白晋王，以兵少不足攻城，晋王遣李存审将吐谷浑、契苾骑兵会之。',
      [('周德威','向晋王报告兵力不足以攻城'),('李存勖','派符存审率骑兵增援的晋王'),('李存审','率吐谷浑、契苾骑兵会周德威的符存审')],
      when='912年四月；确日未载',place='幽州军前',
      note='“李存审”仍归入已有符存审；吐谷浑、契苾指兵员来源，不建虚构将领。')
event('li_siyuan_yingzhou', '李嗣源攻瀛州，刺史赵敬降晋', 18,
      '李嗣源攻瀛州，刺史赵敬降。',
      [('李嗣源','率晋军攻瀛州'),('赵敬','向晋军投降的瀛州刺史')],
      when='912年四月；确日未载',place='瀛州',
      note='赵敬与后史所见赵敬怡字形相近，暂无同一身份证据，不自动归并。')

event('zhu_wen_returns_luoyang_ill', '朱温五月甲申抵洛阳，病势加重', 19,
      '五月，甲申，帝至洛阳，疾甚。',
      [('朱温','到洛阳后病势加重的梁帝')],
      when='912年五月甲申',place='洛阳',
      note='病种与后续死亡时间不在本段推定。')

event('xue_yiju_dies', '梁相薛贻矩卒', 20,
      '司空、门下侍郎、同平章事薛贻矩卒。',
      [('薛贻矩','于912年五月去世的梁司空、宰相')],
      when='912年五月；确日未载',place='洛阳',
      note='《通鉴》本段仅系五月，未给确日；旧五代史另叙梁帝吊祭，不据此推确日。')
claim('event','event_zztj_268_0912_xue_yiju_dies','description',
      '《新五代史》卷二亦记薛贻矩于五月去世。',20,
      '是月，薛貽矩薨。',
      '“是月”承五月；新史没有记具体死亡干支。',new_xue,'corroborates')
claim('event','event_zztj_268_0912_xue_yiju_dies','description',
      '《旧五代史》卷七记薛贻矩患病后去世，梁帝吊祭。',20,
      '宰臣薛貽矩抱恙在假，不克扈從，宣問旁午，仍命且駐東京以俟良愈。及薨，帝震悼頗久，命雒苑使曹守璫往弔祭之',
      '旧书给出患病、吊祭细节；不把梁帝悲伤程度当可量化事实。',old_xue,'adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,21):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化二年第11—20段连续处理；徐知浩、四日等字形问题保留底本并注明异本。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=912,
    primary_source_key=main1,primary_source_keys=[main1],
    paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v268-y0912-p021',
    coverage='卷268乾化二年四月至五月第11—20段，吴宣州变局、梁帝病中行程、晋攻燕及薛贻矩卒。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[11]['id'],'note':'底本“徐知浩”，《通鉴》卷268另一版本作“徐知誥”，本卷第23段与新五代史卷62均见徐知誥；归入既有李昪。底本王檀、新史王壇；不与旧孙儒将王坛误并。李遇死亡在第23段才录。'},
      {'paragraph_id':Q[12]['id'],'note':'底本“夏，四日，癸丑”疑“四月”误字；《通鉴》另一电子版本作“四月”，原文仍逐字留存，纸本待核。'},
      {'paragraph_id':Q[18]['id'],'note':'底本李存审归入符存审；瀛州赵敬不与后史赵敬怡仅据字形合并。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
