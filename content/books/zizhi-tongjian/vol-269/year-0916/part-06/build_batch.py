"""Curate consecutive Tongjian vol. 269, 916 paragraphs 28–33."""
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
main = 'tongjian-269-916-autumn'
new63 = 'xinwudaishi-063-shu-invasion'
new04 = 'xinwudaishi-004-zheng-jue'
old23 = 'jiuwudaishi-023-he-gui-qingzhou'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-04/sources/library' / main, '5e858107', '司马光等'),
    (new63, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-04/sources/library' / new63, '5e858107', '欧阳修'),
    (new04, P / 'sources/library' / new04, '628a20ca', '欧阳修'),
    (old23, P / 'sources/library' / old23, '628a20ca', '薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p028-p033',
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
for n in range(28, 34):
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
    for key in ([main]):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明二年（916）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0916_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'蜀主':'王建','晋王':'李存勖','李存审':'符存审','王宗播':'许存','契丹王阿保机':'阿保机','吴王':'杨隆演','蜀主':'王建','楚王殷':'马殷','硃瑾':'朱瑾','郑綮':'郑綮'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
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
          '只保留原纪年，不换算公历日；叙述性回顾不推成逐次日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0916_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p028: appointment and the explicit great-nephew relation.
event('zheng_jue_chancellor','后梁授郑珏中书侍郎、同平章事',28,
      '丁酉，以礼部侍郎郑珏为中书侍郎、同平章事。',
      [('郑珏','由礼部侍郎受中书侍郎、同平章事任命者')],
      when='916年冬十月丁酉；未换算公历日',place='后梁朝廷',
      note='按前段冬十月顺叙；新五代史卷四明确记十月丁酉。')
claim('event','event_zztj_269_0916_zheng_jue_chancellor','description',
      '《新五代史》卷四记冬十月丁酉郑珏同平章事。',28,
      '冬十月丁酉，中書侍郎鄭珏同中書門下平章事。',
      '新书保留繁体原字，与主书任命时序一致。',new04,'corroborates')
jue = person('郑珏',28,'郑綮之侄孙','珏，綮之侄孙也。')
qi = person('郑綮',28,'郑珏的祖辈亲属','珏，綮之侄孙也。')
rel = 'relationship_person_郑珏_person_郑綮_侄孙'
B['person_relationships'].append(dict(key=rel,person_a_key=jue,person_b_key=qi,
    relation_type='侄孙',description='郑珏是郑綮的侄孙。',status='draft'))
claim('person_relationship',rel,'description','郑珏是郑綮的侄孙。',28,
      '珏，綮之侄孙也。','原文明确郑珏相对于郑綮的方向，不推断具体父辈姓名。')

# p029: this amnesty is separate from December.
event('shu_amnesty_jihai','前蜀己亥大赦',29,
      '己亥，蜀大赦。',[],when='916年己亥；未换算公历日',place='前蜀',
      note='与第31段十二月戊申的大赦分为两次记录。')

# p030: embassy, joint campaign, and Wu march.
event('jin_invites_wu_joint_campaign','晋王遣使赴吴约合兵击梁',30,
      '晋王遣使如吴，会兵以击梁。',
      [('李存勖','遣使赴吴约合兵击梁的晋王')],place='晋、吴',
      note='来使未具名；“会兵”是意图，不当作此句已实际会师。')
event('xu_zhixun_wu_command','吴任徐知训为淮北行营都招讨使',30,
      '十一月，吴以行军副使徐知训为淮北行营都招讨使',
      [('徐知训','受淮北行营都招讨使任命的吴行军副使')],
      when='916年十一月；确日未载',place='吴、淮北')
event('wu_army_advances_song_bo','徐知训、朱瑾等率吴兵趋宋亳响应晋',30,
      '及硃瑾等将兵趣宋、亳与晋相应。',
      [('徐知训','吴军淮北行营都招讨使、统军响应晋'),('硃瑾','率吴兵趋宋亳以响应晋')],
      when='916年十一月；确日未载',place='宋州、亳州',
      note='“硃瑾”保留主书原字，人物规范名朱瑾；此句不推定已取宋亳。')
event('wu_crosses_huai_besieges_yingzhou','吴军渡淮移檄，进围颍州',30,
      '即渡淮，移檄州县，进围颍州。',[],when='916年十一月；确日未载',place='淮河、颍州',
      note='主书未写攻克颍州，记录为围城而非占领。')

# p031: December amnesty and a coming-year era change.
event('shu_amnesty_wushen','前蜀十二月戊申再大赦',31,
      '十二月，戊申，蜀大赦',[],when='916年十二月戊申；未换算公历日',place='前蜀',
      note='与此前己亥大赦分别记录；史载年内两次。')
event('shu_announces_tianhan_and_han','前蜀宣布次年改元天汉并改国号大汉',31,
      '改明年元曰天汉，国号大汉。',
      [('王建','宣布改次年年号及国号的前蜀君主')],
      when='916年十二月戊申宣布；次年使用天汉',place='前蜀朝廷',
      note='“改明年元”表示预告917年年号，不把天汉元年误记为916年。')
claim('event','event_zztj_269_0916_shu_announces_tianhan_and_han','description',
      '《新五代史》卷六十三记十月大赦、改明年天汉并改国号汉，与《通鉴》十二月有月份差异。',31,
      '十月，大赦。改明年元曰天漢，[1]國號漢。',
      '新书原文含编注[1]，逐字保留；月份、国号“大汉/汉”差异并列，待纸本与纪年考订。',new63,'conflicts')

# p032: reciprocal diplomacy after the Jin conquest of Hebei.
event('chu_sends_goodwill_to_jin','楚王马殷遣使向晋通好',32,
      '楚王殷闻晋王平河北，遣使通好。',
      [('马殷','闻晋平河北后遣使通好的楚王')],place='楚、晋',
      note='“殷”承楚王马殷之名；不补使者姓名或盟约内容。')
event('jin_replies_to_chu_goodwill','晋王遣使答复楚王',32,
      '晋王亦遣使报之。',
      [('李存勖','遣使回报楚王的晋王')],place='晋、楚',
      note='只据主书记双向遣使，不推为正式军事同盟。')

# p033: Qingzhou remains contested; the Old Five Dynasties History says it is only retaken in 917.
event('qingzhou_joins_qi','庆州叛梁附岐，李继陟据庆州',33,
      '是岁，庆州叛附于岐，岐将李继陟据之。',
      [('李继陟','据庆州的岐将')],when='916年是岁；确月日未载',place='庆州',
      note='叛附和据州发生在916年；不提前记庆州被梁收复。')
event('he_gui_qingzhou_command','后梁命贺瑰为西面行营马步都指挥使讨庆州',33,
      '诏以左龙虎统军贺瑰为西面行营马步都指挥使，将兵讨之',
      [('朱友贞','下诏命贺瑰讨庆州的后梁皇帝'),('贺瑰','受命率军讨庆州的左龙虎统军')],
      when='916年是岁；确月日未载',place='庆州',
      note='受命讨庆州不等于已收复庆州。')
claim('event','event_zztj_269_0916_he_gui_qingzhou_command','description',
      '《旧五代史》贺瑰传也记贞明二年庆州为李继陟据，贺瑰领西面行营军。',33,
      '貞明二年，慶州叛，為李繼陟所據，瑰以本官充西面行營馬步軍都指揮使兼諸軍都虞候',
      '旧书职衔多兼诸军都虞候；暂不补成主书未载的受任方式。',old23,'corroborates')
event('he_gui_takes_ning_yan','贺瑰击败岐兵并取宁、衍二州',33,
      '破岐兵，下宁、衍二州。',
      [('贺瑰','率后梁军击败岐兵并取宁衍二州')],
      when='916年是岁；确月日未载',place='宁州、衍州',
      note='主书仅明确宁、衍二州；庆州收复旧书系于贞明三年。')
claim('event','event_zztj_269_0916_he_gui_takes_ning_yan','description',
      '《旧五代史》贺瑰传记其与张筠破岐众后取宁、衍二州，庆州平在次年秋。',33,
      '與張筠破涇、鳳之眾三萬，下寧、衍二州。三年秋，慶州平。',
      '旧书补张筠参与、岐众来源和后续庆州时间；不将917年庆州平并入916年事件。',old23,'adds')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(28, 34):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269贞明二年第28—33段连续处理；郑珏任相、蜀赦与改号、晋吴合兵、楚晋通好、庆州叛附与宁衍战事。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=916,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(28,34)],
    next_paragraph=Q[34]['id'],coverage='卷269贞明二年第28—33段；官职、赦令、淮北行军、楚晋遣使与庆州战事。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[28]['id'],'note':'郑珏为郑綮侄孙，关系方向按原文建立；不推断中间一代身份。'},
      {'paragraph_id':Q[29]['id'],'note':'己亥大赦与十二月戊申大赦分录。'},
      {'paragraph_id':Q[30]['id'],'note':'硃瑾/朱瑾为同人，原文用硃字，规范人物名朱瑾；吴军进围颍州不等于攻克。'},
      {'paragraph_id':Q[31]['id'],'note':'改明年元天汉是916年宣布、917年使用；新五代史作十月且国号汉，通鉴作十二月大汉，异文并列。'},
      {'paragraph_id':Q[33]['id'],'note':'旧五代史补张筠参战，称庆州平于贞明三年秋；本批只记916年下宁、衍二州。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
