"""Curate the first ten consecutive paragraphs of Tongjian 267, year 910."""
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
main = 'tongjian-267-910-summer'
old_luo = 'jiuwudaishi-005-luoshaowei'
old_li = 'jiuwudaishi-024-liting'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0910-p011-p017',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main, P / 'sources/library' / main, 'c1049d99', '司马光等'),
    (old_luo, P / 'sources/library' / old_luo, 'c1049d99', '薛居正等'),
    (old_li, P / 'sources/library' / old_li, 'c1049d99', '薛居正等'),
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
main_text = (source_dirs[main] / 'source.txt').read_text()
for n in range(11, 18):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in main_text, n

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
aliases = {'吕兗': '吕兖', '蜀主': '王建', '吴越王镠': '钱镠', '晋王': '李存勖',
           '岐王': '李茂贞', '吴王': '杨隆演', '梁帝': '朱温', '宗懿': '王宗懿'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=main, supplement_relation='adds'):
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷267·开平四年（910）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_267_0910_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
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

# 徐温丧母、赈施衣物及随后起复；母亲仅见周姓，单列为有范围的名称。
event('xu_wen_mother_death', '徐温母周氏于五月去世', 11,
      '五月，吴徐温母周氏卒',
      [('徐温', '母周氏去世的吴将'), ('徐温母周氏', '徐温之母，五月去世')],
      when='910年五月；确日未载', place='吴',
      note='史载其姓周，名未载；“徐温母周氏”是限定性展示名。')
relation('徐温母周氏', '徐温', '母亲', 11, '吴徐温母周氏卒',
         '仅据“徐温母周氏”确认母子；不与其他周氏合并。')
event('xu_wen_funerary_clothes', '徐温命将祭祀偶人衣物解予贫者', 11,
      '将吏致祭，为偶人，高数尺，衣以罗锦，温曰：“此皆出民力，奈何施于此而焚之，宜解以衣贫者。”',
      [('徐温', '主张将祭祀衣物分给贫者')],
      when='910年五月周氏丧祭时', place='吴',
      note='徐温的处置意见由引语记载；不推算衣物数量和受赠人数。')
event('xu_wen_reinstated', '徐温起复为内外马步军都军使并领润州观察使', 11,
      '未几，起复为内外马步军都军使，领润州观察使。',
      [('徐温', '起复掌内外军并领润州观察使')],
      when='910年五月后不久；确日未载', place='润州',
      note='“未几”为相对时间，不换算具体天数。')

event('shu_refuses_ba_jian', '王建拒向岐王割让巴剑二州，以财货相赠', 12,
      '又求巴、剑二州，蜀主曰：“吾奉茂贞，勤亦至矣；若与之地，是弃民也，宁多与之货。”乃复以丝、茶、布、帛七万遗之。',
      [('李茂贞', '向前蜀索要巴、剑二州的岐王'), ('王建', '拒绝割地、改以财货相赠的蜀主')],
      when='910年五月后条；确日未载', place='巴州、剑州、蜀、岐',
      note='“七万”原文未明单位，不写成七万匹；巴剑二州并未据此移交。')

event('liu_jiwei_yichang', '刘继威获任义昌节度使', 13,
      '己亥，以刘继威为义昌节度使。',
      [('刘继威', '获任义昌节度使')],
      when='910年五月己亥', place='义昌军',
      note='与第1段“辅之镇沧州”前后相承，不另造同名人物。')

event('luo_shaowei_death', '罗绍威去世，梁以罗周翰为天雄留后', 14,
      '癸丑，天雄节度使兼中书令鄴贞庄王罗绍威卒。诏以其子周翰为天雄留后。',
      [('罗绍威', '去世的天雄节度使'), ('罗周翰', '罗绍威之子，获任天雄留后')],
      when='910年五月癸丑', place='魏博',
      note='父子关系已在909年批次建档；本段复用人物，不重建关系。')
claim('event', 'event_zztj_267_0910_luo_shaowei_death', 'description',
      '《旧五代史》卷五记魏博节度使罗绍威去世，梁帝悲悼并赠尚书令。', 14,
      '魏博節度使、守太師、兼中書令、鄴王羅紹威薨',
      '旧书另记追赠尚书令；此处不混入《通鉴》主体事件日期。', old_luo)

# 冯行袭病重后，许州军府过渡按动作拆开。
event('feng_xingxi_illness', '冯行袭病重请代，朱温忧许州牙兵生变', 15,
      '匡国节度使长乐忠敬王冯行袭疾笃，表请代者。许州牙兵二千，皆秦宗权馀党，帝深以为忧。',
      [('冯行袭', '病重并上表请派继任者'), ('朱温', '担忧许州牙兵生变的梁帝')],
      when='910年六月庚戌前；确日未载', place='许州',
      note='牙兵二千及其来历按主书记载；不能据“馀党”推定每人当下叛乱。')
event('li_ting_xuzhou_mission', '朱温遣李珽赴许州，李珽安抚将吏', 15,
      '六月，庚戌，命崇政院直学士李珽驰往视行袭病，曰：“善谕朕意，勿使乱我近镇。”珽至许州，谓将吏曰',
      [('朱温', '遣李珽赴许州的梁帝'), ('李珽', '奉命探视冯行袭并安抚许州将吏')],
      when='910年六月庚戌遣使；至许州日未载', place='许州',
      note='李珽对将吏的威劝见后文；不把梁帝所说百万兵视为实际驻兵数。')
event('li_ting_takes_seals', '冯行袭交两使印于李珽，由李珽代掌军府', 15,
      '乃即卧内宣诏，谓行袭曰：“公善自辅养，勿视事，此子孙之福也。”行袭泣谢，遂解两使印授珽，使代掌军府。',
      [('冯行袭', '交出两使印的许州节度使'), ('李珽', '宣诏后受印并代掌军府')],
      when='910年六月李珽至许州后；确日未载', place='许州',
      note='交印和代掌已发生；此时冯行袭尚未去世。')
claim('event', 'event_zztj_267_0910_li_ting_takes_seals', 'description',
      '《旧五代史》李珽传亦记其在卧内宣诏，冯行袭交印使其代掌军府。', 15,
      '行襲泣謝，遂解二印以授珽，代掌軍府事',
      '旧书“二印”与《通鉴》“两使印”互见，不据此补出具体两个官署名称。', old_li)
event('feng_xingxi_death_li_ting', '冯行袭去世，后梁任李珽权知匡国留后', 15,
      '庚辰，行袭卒。甲申，以李珽权知匡国留后，悉以行袭兵分隶诸校，冒冯姓者皆还宗。',
      [('冯行袭', '庚辰去世的匡国节度使'), ('李珽', '甲申权知匡国留后并整编旧部')],
      when='910年六月庚辰卒、甲申任李珽', place='许州',
      note='死亡与任命分隔干支日，合为军府接续事件但保留时间先后。')
claim('event', 'event_zztj_267_0910_feng_xingxi_death_li_ting', 'description',
      '《旧五代史》李珽传称其获任匡国军留后。', 15,
      '乃以珽為匡國軍留後',
      '传文不明确冯行袭确切卒日，日期仍以主书为准。', old_li)

event('ma_yin_tiance', '后梁加马殷天策上将军，楚开天策府', 16,
      '楚王殷求为天策上将，诏加天策上将军。殷始开天策府，以弟宾为左相，存为右相。',
      [('马殷', '获加天策上将军并开天策府'), ('马宾', '马殷之弟，任天策府左相'),
       ('马存', '马殷之弟，任天策府右相')],
      when='910年六月后条；确日未载', place='楚',
      note='原文仅称“宾”“存”，以主语马殷及“弟”承接姓名；马存复用908年实体。')
relation('马殷', '马宾', '兄长', 16, '以弟宾为左相', '原文称马宾为马殷之弟。')
relation('马殷', '马存', '兄长', 16, '存为右相',
         '“弟宾……存”并列，结合上句同指马殷之弟；与908年马存身份一致。')
event('chu_jingnan_defeat', '楚军侵荆南至油口，高季昌击败并追至白田', 16,
      '殷遣将侵荆南，军于油口。高季昌击破之，斩首五千级，逐北至白田而还。',
      [('马殷', '遣将侵荆南的楚王'), ('高季昌', '率荆南军击败楚军并追至白田')],
      when='910年六月后条；确日未载', place='油口、白田',
      note='“斩首五千级”为主书记载，未经独立核数；楚将未具名。')

event('aopian_chishi_defeat', '敖骈围彭瑊于赤石，楚兵救援并俘敖骈', 17,
      '吴水军指挥使敖骈围吉州刺史彭玕弟瑊于赤石，楚兵救瑊，虏骈以归。',
      [('敖骈', '率吴水军围赤石，后被楚军俘获'),
       ('彭瑊', '彭玕之弟，受围后获楚军救援'),
       ('彭玕', '吉州刺史，彭瑊之兄')],
      when='910年六月后条；确日未载', place='赤石',
      note='楚救兵将领未具名；不将楚军说成彭玕直接指挥。')
relation('彭玕', '彭瑊', '兄长', 17, '彭玕弟瑊', '原文明言彭瑊是彭玕之弟。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11, 18):
    ledger[n - 1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                         review='卷267开平四年第11—17段连续处理；许州交印与继任、楚荆南战事按原文时序分录。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=267, year=910,
    primary_source_key=main, paragraphs=[Q[n]['id'] for n in range(11, 18)],
    next_paragraph='zztj-v267-y0910-p018',
    coverage='卷267开平四年第11—17段，吴徐温、岐蜀交涉、魏博与许州继任、楚荆南战事。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({key: len(value) for key, value in B.items() if isinstance(value, list)})
