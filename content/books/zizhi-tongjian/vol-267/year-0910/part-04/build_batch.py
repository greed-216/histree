"""Curate Tongjian 267, year 910, consecutive paragraphs 28-34."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 44))
main1 = 'tongjian-267-910-autumn'
main2 = 'tongjian-267-910-winter'
main3 = 'tongjian-267-910-zhao-jin'
old_army = 'jiuwudaishi-006-northern-army'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0910-p028-p034',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-03/sources/library' / main1, 'e7ad69d9', '司马光等'),
    (main2, P / 'sources/library' / main2, '9708b0c5', '司马光等'),
    (main3, P / 'sources/library' / main3, 'f121af82', '司马光等'),
    (old_army, P / 'sources/library' / old_army, '9708b0c5', '薛居正等'),
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
primary_texts = {key: (source_dirs[key] / 'source.txt').read_text() for key in (main1, main2, main3)}
for n in range(28, 35):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[row['source_line'] - 1]
    if n == 33:
        assert row['text'] in (primary_texts[main1] + primary_texts[main3]).replace('\n', ''), n
    else:
        assert row['text'] in primary_texts[main1 if n <= 32 else main2], n

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
           '王景仁':'王茂章','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1, main3, main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1, main2, main3):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷267·开平四年（910）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_267_0910_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1, main2, main3):
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
                   description=f'《资治通鉴》卷267开平四年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=910):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_267_0910_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '910年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_267_0910_' + code + '_' + pk
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

event('shen_xingsi_kills_chen', '沈行思因湖州任用争执杀陈瑰，欲刺盛师友', 28,
      '行思取锻槌击瑰，杀之，因诣镠，与师友论功，夺左右槊，欲刺师友，众执之。',
      [('沈行思', '杀陈瑰、欲刺盛师友后被拘'), ('陈瑰', '被沈行思杀害的吴越将吏'),
       ('盛师友', '沈行思意欲刺杀的湖州将领')],
      when='910年十月前后条；确日未载', place='吴越',
      note='“欲刺”是未遂，盛师友未在本段被杀；胡三省音注本作陈瓌，底本瑰照录。')
event('shen_xingsi_executed', '钱镠斩沈行思，任盛师友为婺州刺史', 28,
      '镠斩行思，以师友为婺州刺史。',
      [('钱镠', '处死沈行思并任命盛师友的吴越王'),
       ('沈行思', '被钱镠斩杀'), ('盛师友', '获任婺州刺史')],
      when='910年十月前后条；沈行思被拘后', place='吴越、婺州',
      note='与第5段湖州事件相接，但本段叙述有追叙，不将全部前事强置十月。')

event('wang_jingren_command', '后梁任王茂章（王景仁）为北面招讨使', 29,
      '十一月，己丑，以宁国节度使、同平章事王景仁充北面行营都指挥招讨使，潞州副招讨使韩勍副之，以李思安为先锋将，趣上党。',
      [('王景仁', '时名王景仁，受任北面行营都招讨使'),
       ('韩勍', '受任副招讨使'), ('李思安', '担任先锋将')],
      when='910年十一月己丑', place='后梁朝廷、上党方向',
      note='王景仁与王茂章为同一人，依已核修订复用UUID；“趣上党”为当时部署，后文改屯魏州。')
claim('event', 'event_zztj_267_0910_wang_jingren_command', 'description',
      '《旧五代史》卷六也记王景仁为北面都招讨使、韩勍为副、李思安为先锋。', 29,
      '以甯國軍節度使王景仁充北面行營都招討使，潞州副招討使韓勍為副，相州刺史李思安為先鋒使',
      '旧书紧接以镇定叛连晋为背景概述，不将其全部倒填为己丑当天已成。', old_army)
event('wang_jingren_weizhou', '后梁改令王景仁等屯魏州，杨师厚返陕州', 29,
      '寻遣景仁等屯魏州，杨师厚还陕。',
      [('王景仁', '转屯魏州的梁将'), ('杨师厚', '返陕州的梁将')],
      when='910年十一月己丑后不久；确日未载', place='魏州、陕州',
      note='“寻”不换算为确日；此为上党计划之后的实际调动。')

event('shu_heir_renamed', '王建将太子王宗懿改名元坦', 30,
      '蜀主更太子宗懿名曰元坦。',
      [('王建', '为太子改名的蜀主'), ('王宗懿', '获改名元坦的前蜀太子')],
      when='910年十一月条；确日未载', place='蜀',
      note='元坦与王宗懿为同一人；本批保留原文异名，不另建人物。')
fake_quote = '庚戌，立假子宗裕为通王，宗范为夔王，宗钅岁为昌王，宗寿为嘉王，宗翰为集王'
fake_children = [('王宗裕','通王'),('王宗范','夔王'),('王宗鐬','昌王'),('王宗寿','嘉王'),('王宗翰','集王')]
event('shu_adopted_kings', '王建封五位假子为通、夔、昌、嘉、集王', 30, fake_quote,
      [('王建', '封五位假子为王的蜀主')] + [(name, f'受封{title}的王建假子') for name,title in fake_children],
      when='910年十一月庚戌', place='蜀',
      note='“假子”为收养或政治性拟亲，绝不写成生父子；底本宗钅岁为拆字，胡本作宗鐬。')
next(row for row in B['people'] if row['key']==people['王宗鐬'])['aliases']=['王宗钅岁','王宗鐬']
for name,_ in fake_children:
    relation('王建', name, '假父', 30, fake_quote,
             '前半句明称“假子”，只记拟制父子；不得推为王建亲生子。')
real_quote = '立其子宗仁为普王，宗辂为雅王，宗纪为褒王，宗智为荣王，宗泽为兴王，宗鼎为彭王，宗杰为信王，宗衍为郑王。'
real_children = [('王宗仁','普王'),('王宗辂','雅王'),('王宗纪','褒王'),('王宗智','荣王'),
                 ('王宗泽','兴王'),('王宗鼎','彭王'),('王宗杰','信王'),('王宗衍','郑王')]
event('shu_natural_kings', '王建封八位亲生子为王', 30, real_quote,
      [('王建', '封八位亲生子为王的蜀主')] + [(name, f'受封{title}的王建之子') for name,title in real_children],
      when='910年十一月庚戌', place='蜀',
      note='原文“其子”与下文“宗懿等九人……真其子”互校；太子宗懿为第九位。')
for name,_ in real_children:
    relation('王建',name,'父亲',30,real_quote,'原文明称“其子”，与假子封王名单分开。')
person('王宗特',30,'王建亲生子','惟宗懿等九人及宗特、宗平真其子')
person('王宗平',30,'王建亲生子','惟宗懿等九人及宗特、宗平真其子')
for name in ('王宗特','王宗平'):
    relation('王建',name,'父亲',30,'惟宗懿等九人及宗特、宗平真其子',
             '此句明确二人是王建亲生子，不属于前列假子。')
person('王宗范母周氏',30,'王宗范之母、王建之妾','宗范姓张，其母周氏为蜀主妾')
relation('王宗范母周氏','王宗范','母亲',30,'宗范姓张，其母周氏为蜀主妾',
         '只确认其母周姓及王建妾身份；不据此推断王建是宗范生父。')
relation('王建','王宗翰','舅父',30,'宗翰姓孟，蜀主之姊子',
         '原文明称宗翰是王建姐姐之子；舅甥与假父关系并存，不当生父子。')

event('liang_emperor_hunt', '朱温病情稍缓，在伊洛之间校猎', 31,
      '上疾小愈，辛亥，校猎于伊、洛之间。',
      [('朱温', '病情稍缓后校猎的梁帝')],
      when='910年十一月辛亥', place='伊水、洛水之间',
      note='“小愈”仅为当时稍缓，不推断病已根治。')

event('liang_suspects_zhao_ding', '朱温疑镇定附晋，拟趁罗绍威亡后处置两镇', 32,
      '上疑赵王镕贰于晋，且欲因鄴王绍威卒除移镇、定。',
      [('朱温', '怀疑王镕并欲处置镇定的梁帝'), ('王镕', '被梁帝怀疑的赵王')],
      when='910年十一月辛亥后条；确日未载', place='镇州、定州',
      note='此为梁帝意图及怀疑，不把镇定实际叛梁定在此句。')
event('liang_deep_ji_deployment', '朱温遣杜廷隐、丁延徽率魏博兵分屯深冀', 32,
      '上遣供奉官杜廷隐、丁延徽临魏博兵三千分屯深、冀，声言恐燕兵南寇，助赵守御。又云分兵就食。',
      [('朱温', '遣军进入深冀的梁帝'), ('杜廷隐', '率魏博兵屯深冀'),
       ('丁延徽', '与杜廷隐同赴深冀')],
      when='910年十一月辛亥后；确日未载', place='深州、冀州',
      note='三千为两将所率魏博兵总数；“恐燕兵南寇”“分兵就食”为梁方公开理由。')
event('shi_gongli_warning', '石公立劝王镕拒梁军入深州，王镕未纳', 32,
      '赵将石公立戍深州，白赵王镕，请拒之。镕遽命开门，移公立于外以避之。',
      [('石公立', '劝拒梁军入深州的赵将'), ('王镕', '令开城门、调石公立离开的赵王')],
      when='910年梁军抵深州时；确日未载', place='深州',
      note='石公立后引语为警告，不当成其预言结果已经发生。')

event('wang_rong_petitions_liang', '王镕得知梁军意图，遣使请其撤离深冀', 33,
      '梁人有亡奔真定，以其谋告镕者，镕大惧，又不敢先自绝；但遣使诣洛阳，诉称“燕兵已还，与定州讲和如故，深、冀民见魏博兵入，奔走惊骇，乞召兵还。”',
      [('王镕', '得梁亡人告警后遣使请撤兵的赵王')],
      when='910年梁军入深冀后；确日未载', place='真定、洛阳',
      note='使者陈述是王镕对梁的申诉；“不敢先自绝”说明此时尚未公开断绝关系。')
event('liang_kills_zhao_garrison', '杜廷隐等在深冀杀赵守军并据城', 33,
      '未几，廷隐等闭门尽杀赵戍兵，乘城拒守。',
      [('杜廷隐', '闭门杀赵戍兵并据城的梁使')],
      when='910年王镕遣使申诉后不久；确日未载', place='深州、冀州',
      note='“尽杀”按主书记载赵戍兵结局，人数未载；“廷隐等”所指各人的具体执行行为未分。')
event('zhao_seeks_jin_yan', '王镕攻深冀不克，向晋、燕求援', 33,
      '镕始命石公立攻之，不克，乃遣使求援于燕、晋。',
      [('王镕', '命石公立攻城并向晋燕求援'), ('石公立', '率赵军攻城未克')],
      when='910年深冀守军被杀后；确日未载', place='深州、冀州、晋、燕',
      note='攻城未克与遣使求援是前后动作，不假设燕已应援。')
event('jin_accepts_zhao_alliance', '李存勖决定援赵，遣周德威出井陉屯赵州', 33,
      '我若疑而不救，正堕硃氏计中。宜趣发兵赴之，晋、赵叶力，破梁必矣。”乃发兵，遣周德威将之，出井陉，屯赵州。',
      [('李存勖', '决定出兵援赵的晋王'), ('周德威', '受命率晋军出井陉屯赵州')],
      when='910年赵王求援后；确日未载', place='井陉、赵州',
      note='引语表达晋王战策；“破梁必矣”是其预期，不是此时已破梁。')
event('liu_shouguang_refuses_zhao', '刘守光拒赵求援，燕军未出兵', 33,
      '守光曰：“王镕数负约，今使之与梁自相弊，吾可以坐承其利，又何救焉！”赵使者交错于路，守光竟不为出兵。',
      [('刘守光', '拒绝救赵的燕王'), ('王镕', '遣使往燕求援的赵王')],
      when='910年赵王求援后；确日未载', place='燕、赵',
      note='孙鹤曾劝燕王出兵，但未改变刘守光的决定；不把燕列入实际联军。')
event('zhao_ding_tianyou', '镇定复称唐天祐年号，武顺复称成德军', 33,
      '自是镇、定复称唐天祐年号，复以武顺为成德军。',
      [('王镕', '镇州方面转用唐天祐年号的赵王'), ('王处直', '定州方面与赵同转唐天祐年号')],
      when='910年赵晋联盟后；确日未载', place='镇州、定州',
      note='年号恢复发生在梁赵冲突与晋援之后；不要倒置于梁军入城前。')

event('liang_army_recalled', '司天言月食不利出兵，朱温召王景仁等返洛阳', 34,
      '司天言：“来月太阴亏，不利宿兵于外。”上召王景仁等还洛阳。',
      [('朱温', '听司天意见召回北军的梁帝'), ('王景仁', '奉召返回洛阳的北军主帅')],
      when='910年十二月己未前；确日未载', place='洛阳',
      note='月食不利出兵为司天奏说，不作为客观军事因果定律。')
event('liang_army_xingming', '朱温命王景仁等攻赵晋，梁军会罗周翰兵屯邢洺', 34,
      '十二月，己未，上闻赵与晋合，晋兵已屯赵州，乃命王景仁等将兵击之。庚申，景仁等自河阳渡河，会罗周翰兵，合四万，军于邢、洺。',
      [('朱温', '闻赵晋结盟后命北军出击'), ('王景仁', '率梁军北进并与罗周翰会兵'),
       ('罗周翰', '率魏博兵与王景仁会合')],
      when='910年十二月己未命出兵、庚申会军', place='河阳、邢州、洺州',
      note='四万为会合后总兵数；此时仅屯邢洺，柏乡交战属后续段落及翌年。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(28, 35):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷267开平四年第28—34段连续处理；前蜀亲子/假子分开，赵晋燕梁互动按先后分录。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=267, year=910,
    primary_source_key=main1, primary_source_keys=[main1,main2,main3],
    paragraphs=[Q[n]['id'] for n in range(28,35)],next_paragraph='zztj-v267-y0910-p035',
    coverage='卷267开平四年第28—34段，湖州后续、前蜀诸王、梁赵晋燕决裂及北军动员。',
    supplements=supplements,status=status,
    textual_reviews=[{'paragraph_id':Q[30]['id'],
                      'review_url':'https://zh.wikisource.org/zh-hant/資治通鑑_(胡三省音注)/卷267',
                      'note':'电子底本宗钅岁为拆字；音注本作宗鐬。亲生子与假子按原文分开。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({key:len(value) for key,value in B.items() if isinstance(value,list)})
