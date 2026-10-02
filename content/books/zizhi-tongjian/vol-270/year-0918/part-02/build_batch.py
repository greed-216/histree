"""Curate consecutive Tongjian vol. 270, 918 paragraphs 5–11."""
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
main1 = 'tongjian-270-917-year-end'
main2 = 'tongjian-270-918-spring'
old28 = 'jiuwudaishi-028-yangliu-river'
old09 = 'jiuwudaishi-009-april-appointments'
specs = [
    (main1,ROOT / 'content/books/zizhi-tongjian/vol-270/year-0917/part-04/sources/library' / main1,'09262e73','司马光等'),
    (main2,P / 'sources/library' / main2,'4138a6db','司马光等'),
    (old28,P / 'sources/library' / old28,'26b19a11','薛居正等'),
    (old09,P / 'sources/library' / old09,'26b19a11','薛居正等'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p005-p011',
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
for n in range(5, 12):
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
    for key in (main1,main2):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source in (main1,main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明四年（918）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0918_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,main2):
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','蜀主':'王建','吴越王镠':'钱镠','岐王':'李茂贞','帝':'朱友贞','宗平':'王宗平','宗特':'王宗特'}.get(name, name)
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
# p005: Liang counterattack at Yangliu and aftermath of An Yanzhi's capture.
event('xie_yanzhang_attacks_yangliu','谢彦章率梁军数万攻晋杨刘城',5,
      '河阳节度使、北面行营排陈使谢彦章将兵数万攻杨刘城。',
      [('谢彦章','率梁军攻杨刘城的河阳节度使')],when='918年二月后、三月前；确日未载',place='杨刘城',
      note='数万为主书概数；本段未说杨刘城被梁军夺回。')
claim('event','event_zztj_270_0918_xie_yanzhang_attacks_yangliu','description',
      '《旧五代史》庄宗纪将谢彦章围逼杨刘系于二月。',5,
      '二月，梁將謝彥章帥眾數萬來迫楊劉，築壘以自固',
      '旧书给二月，主书上下文与之相容；同一叙事不作独立人数确证。',old28,'corroborates')
event('xie_yanzhang_floods_yangliu_approach','谢彦章筑垒决河水阻晋军进援',5,
      '甲子，晋王自魏州轻骑诣河上。彦章筑垒自固，决河水，瀰浸数里，以限晋兵，晋兵不得进。',
      [('李存勖','自魏州轻骑至河上的晋王'),('谢彦章','筑垒决河以阻晋军者')],
      when='918年二月甲子；确公历日期未换算',place='杨刘附近河上',
      note='决河水阻军为本段结果，未提前写入旧书六月中流交战。')
claim('event','event_zztj_270_0918_xie_yanzhang_floods_yangliu_approach','description',
      '《旧五代史》亦载谢彦章决河水数里限制晋军。',5,
      '又決河水，彌漫數里，以限帝軍。',
      '“数里”是史书描述，不绘制洪水范围。',old28,'corroborates')
event('an_yanzhi_remnants_join_jin','安彦之散卒聚为群盗，多受晋王招募',5,
      '安彦之散卒多聚于兗、郓山谷为群盗，以观二国成败，晋王招募之，多降于晋。',
      [('安彦之','其散卒聚于兗郓山谷的被俘梁将'),('李存勖','招募安彦之旧部的晋王')],
      when='杨刘失守后；具体月日未载',place='兗州、郓州山谷',
      note='“多降”无人数，不把安彦之本人写成归晋。')
claim('person',people['谢彦章'],'description','《通鉴》称谢彦章许州人。',5,
      '彦章，许州人也。','籍贯按史载，不推断出生地或今坐标。')

# p006–p011: consecutive appointments, formal titles, diplomacy and succession.
event('wang_zongkan_shu_both_routes','蜀主任王宗侃为东西两路诸军都统',6,
      '己亥，蜀主以东面招讨使王宗侃为东、西两路诸军都统。',
      [('蜀主','任王宗侃统东西路的蜀主'),('王宗侃','受任东西两路诸军都统者')],
      when='918年二月至三月间己亥；原文未再标月',place='蜀',
      note='原文只给日干支，处于二月条与三月条之间，不私换算公历。')
event('qian_liu_establishes_generalissimo_office','钱镠在吴越始置元帅府及官属',7,
      '三月，吴越王镠初立元帅府，置官属。',
      [('吴越王镠','设立元帅府的吴越王')],when='918年三月；确日未载',place='吴越',
      note='机构设立与官属存在有据，具体人员名单本段未给。')
event('shu_princes_zongping_zongte_titles','蜀主封王宗平忠王、王宗特资王',8,
      '夏，四月，癸卯朔，蜀主立子宗平为忠王，宗特为资王。',
      [('蜀主','封两子为王的蜀主'),('宗平','受封忠王的王建之子'),('宗特','受封资王的王建之子')],
      when='918年四月癸卯朔',place='蜀',
      note='两人均复用既有人物主体和父子关系。')
for rel,description in [
    ('relationship_person_王建_person_王宗平_父亲','王建是王宗平的父亲。'),
    ('relationship_person_王建_person_王宗特_父亲','王建是王宗特的父亲。')]:
    child='王宗平' if '王宗平' in rel else '王宗特'
    B['person_relationships'].append(dict(key=rel,person_a_key=people['王建'],person_b_key=people[child],
        relation_type='父亲',description=description,status='draft'))
    reused.add(rel)
    claim('person_relationship',rel,'description',description,8,
          '蜀主立子宗平为忠王，宗特为资王',
          '本段明称“子”，复用既有父子关系键及方向。')
event('qi_seeks_peace_with_shu_again','岐王李茂贞再遣使向蜀求好',9,
      '岐王复遣使求好于蜀。',[('岐王','再遣使求好的岐王')],
      when='918年四月；本句无确日',place='岐、蜀',
      note='使者未具名；只记岐王求好，不推断蜀已接受或结盟。')
event('xiao_qing_liang_chancellor','梁授萧顷中书侍郎、同平章事',10,
      '己酉，以吏部侍郎萧顷为中书侍郎、同平章事。',
      [('萧顷','受任中书侍郎、同平章事者')],when='918年四月己酉',place='后梁',
      note='本段承四月条；官职依原文。')
claim('event','event_zztj_270_0918_xiao_qing_liang_chancellor','description',
      '《旧五代史》末帝纪亦记四月己酉萧顷任平章事。',10,
      '己酉，以銀青光祿大夫、行中書侍郎、同中書門下平章事、權判戶部鄭玨為金紫光祿大夫',
      '旧书同日另有郑珏加官，萧顷任命在该段后句；此引仅定位日期，不引其姓名。',old09,'adds')
claim('event','event_zztj_270_0918_xiao_qing_liang_chancellor','description',
      '旧书同段详记萧顷由吏部侍郎加同平章事。',10,
      '以金紫光祿大夫、行尚書吏部侍郎、上柱國、蘭陵縣開國男、食邑三百戶蕭頃為中書門下平章事',
      '对照主书“中书侍郎、同平章事”，官衔文字保留各书说法。',old09,'corroborates')
event('gao_wanjin_dies','保大节度使高万金去世',11,
      '保大节度使高万金卒。',[('高万金','去世的保大节度使')],
      when='918年四月癸亥前；确日未载',place='鄜州',
      note='“卒”在癸亥任命前，本段未明确死日。')
event('gao_wanxing_two_circuits','梁以高万兴兼保大节度使，镇鄜延两州',11,
      '癸亥，以忠义节度使高万兴兼保大节度使，并镇鄜、延。',
      [('高万兴','兼领保大并镇鄜延者')],when='918年四月癸亥',place='鄜州、延州',
      note='接高万金卒后的任命；不推断两州边界。')
claim('event','event_zztj_270_0918_gao_wanxing_two_circuits','description',
      '《旧五代史》记癸亥高万兴兼领鄜延两道。',11,
      '癸亥，以延州忠義軍節度使、太原西面招討應接使、檢校太師、兼中書令、渤海王高萬興兼鄜、延兩道都製置使',
      '旧书官号与主书“兼保大节度使”略有差别，分别保留。',old09,'corroborates')
rel='relationship_person_高万兴_person_高万金_兄长'
B['person_relationships'].append(dict(key=rel,person_a_key=people['高万兴'],person_b_key=people['高万金'],
    relation_type='兄长',description='高万兴是高万金的兄长。',status='draft'))
reused.add(rel)
claim('person_relationship',rel,'description','高万兴是高万金的兄长。',11,
      '時萬興弟鄜州節度使萬金卒，故有是命。',
      '旧书明确“万兴弟万金”，复用既有有向兄长关系。',old09,'corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5,12):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷270贞明四年第5—11段；杨刘城梁晋攻防、蜀吴越岐政事及后梁任官。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=270,year=918,
    primary_source_key=main1,primary_source_keys=[main1,main2],paragraphs=[Q[n]['id'] for n in range(5,12)],next_paragraph=Q[12]['id'],
    coverage='卷270贞明四年第5—11段；杨刘之围、吴越蜀岐任官外交及高氏兄弟。',supplements=supplements,
    reviewed_questions=[
      {'paragraph_id':Q[5]['id'],'note':'《旧五代史》将谢彦章逼杨刘系于二月，后段六月交战不得混入本段；安彦之本人不作归晋。'},
      {'paragraph_id':Q[6]['id'],'note':'己亥在本年二月与三月条之间，主书未再次标月；不反推公历日。'},
      {'paragraph_id':Q[9]['id'],'note':'岐求好只记使者来往，未推定蜀接受。'},
      {'paragraph_id':Q[11]['id'],'note':'高万金死日未明；《旧五代史》另记高万兴为其兄，关系复用。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
