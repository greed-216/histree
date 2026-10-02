"""Curate consecutive Tongjian vol. 270, 918 paragraphs 1–4."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 45))
main = 'tongjian-270-917-year-end'
old18 = 'jiuwudaishi-018-jing-xiang-memorial'
new63 = 'xinwudaishi-063-wang-zongjie-heirs'
specs = [
    (main,ROOT / 'content/books/zizhi-tongjian/vol-270/year-0917/part-04/sources/library' / main,'09262e73','司马光等'),
    (old18,P / 'sources/library' / old18,'dc0e63b6','薛居正等'),
    (new63,P / 'sources/library' / new63,'dc0e63b6','欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p001-p004',
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
lines = (ROOT / 'resources/derived/tongjian/270.txt').read_text().splitlines()
for n in range(1, 5):
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
    for key in (main,):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明四年（918）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0918_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'蜀主':'王建','帝':'朱友贞','李亚子':'李存勖','太子衍':'王宗衍','信王宗杰':'王宗杰'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷270贞明四年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=918):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0918_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '918年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_270_0918_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key
# p001: first action in Zhengming 4 (918).
event('shu_restores_shu_name','前蜀大赦并恢复国号蜀',1,
      '春，正月，乙亥朔，蜀大赦，复国号曰蜀。',
      [('蜀主','大赦并恢复国号的蜀主')],when='918年正月乙亥朔',place='蜀',
      note='与917年末预定次年改元光天相衔接；国号与年号分开。')

# p002: Liang retreat and Jing Xiang's memorial after Yangliu fell.
event('jin_raids_yun_pu_then_returns','晋军侵掠郓州、濮州附近后撤回',2,
      '帝至大梁，晋兵侵掠至郓、濮而还。',
      [('帝','返回大梁的梁帝')],when='918年春正月后；确日未载',place='大梁、郓州、濮州',
      note='晋军未据此句占领郓、濮；“侵掠至”与“而还”连读。')
event('jing_xiang_memorial_after_yangliu','敬翔上疏批评梁廷对晋战事失策',2,
      '敬翔上疏曰：“国家连年丧师，疆土日蹙。陛下居深宫之中，所与计事者皆左右近习，岂能量敌国之胜负乎！',
      [('敬翔','上疏建言的后梁重臣'),('朱友贞','收受上疏的梁帝')],
      when='918年春正月后；确日未载',place='大梁',
      note='敬翔对损失、近习的判断是奏疏内容，未据此生成额外战役或实测疆域。')
claim('event','event_zztj_270_0918_jing_xiang_memorial_after_yangliu','description',
      '敬翔主张访求其他对晋方略，并请赴边陲效力；赵岩、张宗奭等人称其怨望，梁帝未采纳。',2,
      '陛下宜询访黎老，别求异策。不然，忧未艾也。臣虽驽怯，受国重恩，陛下必若乏才，乞于边垂自效。”疏奏，赵、张之徒言翔怨望，帝遂不用。',
      '赵、张依前后文识别为赵岩、张宗奭一派；这里不据简称新建参与边。')
claim('event','event_zztj_270_0918_jing_xiang_memorial_after_yangliu','description',
      '《旧五代史》敬翔传也保留其对杨刘失守后梁廷失策的奏言。',2,
      '及劉鄩失河朔，安彥之喪楊劉，翔奏曰：「國家連年遣將出征，封疆日削',
      '两书引奏可能有文本源流关联，不视作完全独立确证；卷十八记有更详语句。',old18,'corroborates')

# p003: WU's Qiánzhou campaign, before the city is captured.
event('wu_wang_qi_campaign_qianzhou','吴任王祺领军攻虔州谭全播',3,
      '吴以右都押牙王祺为虔州行营都指挥使，将洪、抚、袁、吉之兵击谭全播。',
      [('王祺','领吴军攻虔州的右都押牙'),('谭全播','虔州被攻方')],
      when='918年春；本段未给确日',place='虔州',
      note='本段是出兵及抵城，不提前记录虔州陷落。')
event('yan_keqiu_recruits_gan_boatmen','严可求以厚利招赣石水工助吴军抵虔州',3,
      '严可求以厚利募赣石水工，故吴兵奄至虔州城下，虔人始知之。',
      [('严可求','招募赣石水工者')],when='918年春；本段未给确日',place='赣石、虔州',
      note='水工姓名及人数未载，不推断具体航线或行军天数。')

# p004: Shu heir politics and death of Prince Zongjie.
event('shu_heir_concerns','蜀主王建忧太子王宗衍耽于游乐',4,
      '蜀太子衍好酒色，乐游戏。蜀主尝自夹城过，闻太子与诸王斗鸡击球喧呼之声，叹曰：“吾百战以立基业，此辈其能守之乎！”',
      [('太子衍','被评为耽于游乐的蜀太子'),('蜀主','忧太子能否守成的蜀主')],
      when='918年二月癸亥前；确日未载',place='蜀宫',
      note='太子“衍”复用既有王宗衍；史书品评按记述，不扩大到其全部行为。')
event('wang_jian_considers_zongjie_heir','王建曾有改立信王王宗杰之意',4,
      '信王宗杰有才略，屡陈时政，蜀主贤之，有废立意。',
      [('信王宗杰','被蜀主考虑改立的信王'),('蜀主','有废立太子想法者')],
      when='918年二月癸亥之前；确日未载',place='蜀',
      note='“有废立意”只表示意向，未发生实际废太子或改立。')
claim('event','event_zztj_270_0918_wang_jian_considers_zongjie_heir','description',
      '《新五代史》称王建曾觉得王宗杰材贤，考虑与王宗辂择一为嗣，徐妃等支持王宗衍。',4,
      '建以豳王宗輅貌類己，而信王宗傑於諸子最材賢，欲於兩人擇立之。',
      '该传追叙更早立储过程，不能据此判定918年又已举行正式选择。',new63,'adds')
event('wang_zongjie_sudden_death','蜀信王王宗杰二月癸亥暴卒',4,
      '二月，癸亥，宗杰暴卒，蜀主深疑之。',
      [('王宗杰','二月癸亥暴卒的信王'),('王建','对其暴卒起疑的蜀主')],
      when='918年二月癸亥',place='蜀',
      note='“深疑”未指明确凶手或死因，不建谋杀事件。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,5):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷270贞明四年第1—4段；蜀复国号、梁敬翔上疏、吴攻虔州、蜀储位疑虑。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=270,year=918,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(1,5)],next_paragraph=Q[5]['id'],
    coverage='卷270贞明四年第1—4段；蜀大赦、梁廷奏疏、吴攻虔州与蜀宗杰之死。',supplements=supplements,
    reviewed_questions=[
      {'paragraph_id':Q[2]['id'],'note':'敬翔奏疏中损地、兵事评价与后梁朝臣“怨望”指控保留归属，不直接断言。'},
      {'paragraph_id':Q[3]['id'],'note':'吴兵至虔州城下，不把下一阶段攻陷虔州提前。'},
      {'paragraph_id':Q[4]['id'],'note':'王宗杰暴卒与蜀主深疑不能推出凶手；新五代史立储记事属于追叙。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
