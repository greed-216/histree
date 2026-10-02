"""Curate Tongjian 267, year 910, consecutive paragraphs 18-27."""
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
main1 = 'tongjian-267-910-summer'
main2 = 'tongjian-267-910-autumn'
old_xia = 'jiuwudaishi-132-lirenfu'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0910-p018-p027',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-02/sources/library' / main1, 'c1049d99', '司马光等'),
    (main2, P / 'sources/library' / main2, 'e7ad69d9', '司马光等'),
    (old_xia, YEAR / 'part-01/sources/library' / old_xia, '8f8f3416', '薛居正等'),
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
primary_texts = {key: (source_dirs[key] / 'source.txt').read_text() for key in (main1, main2)}
for n in range(18, 28):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in primary_texts[main1 if n <= 23 else main2], n

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
aliases = {'韧城': '韦庄', '吴越王镠': '钱镠', '岐王': '李茂贞',
           '邠帅': '杨崇本', '李继徽': '杨崇本', '泾帅': '刘知俊',
           '晋王': '李存勖', '赵王镕': '王镕', '张宗奭': '张全义', '梁帝': '朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or (main1 if n <= 23 else main2)
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1, main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷267·开平四年（910）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_267_0910_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1, main2):
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

# The selected TXT has 韧城; the annotated Tongjian reads 韋莊. Preserve the raw quote.
event('wei_zhuang_death', '前蜀宰相韦庄去世', 18,
      '秋，七月，戊子朔，蜀门下侍郎兼吏部尚书、同平章事韧城卒。',
      [('韦庄', '前蜀门下侍郎、吏部尚书、同平章事，卒于此条')],
      when='910年七月戊子朔', place='蜀',
      note='选定电子底本作“韧城”，《资治通鉴》胡三省音注本卷267作“韋莊”；与本书908年韦庄任蜀相的记载合校，展示名作韦庄，纸本仍待核。')

event('qian_liu_eunuch_plea', '钱镠为周延诰等二十五名避难宦者请求宽赦', 19,
      '吴越王镠表“宦者周延诰等二十五人，唐末避祸至此，非刘、韩之党，乞原之。”',
      [('钱镠', '为避难宦者奏请宽赦的吴越王'), ('周延诰', '钱镠上表所称二十五名避难宦者之一')],
      when='910年七月条；确日未载', place='吴越、后梁朝廷',
      note='“非刘、韩之党”是钱镠上表的说法；不据奏词证明全部宦者的政治经历。')
event('liang_eunuch_reply', '朱温答复暂留避难宦者于吴越', 19,
      '上曰：“此属吾知其无罪，但今革弊之初，不欲置之禁掖，可且留于彼，谕以此意。”',
      [('朱温', '答复可让宦者暂留吴越、不置禁中的梁帝')],
      when='910年七月钱镠上表后；确日未载', place='后梁朝廷',
      note='梁帝表示知其无罪并许暂留吴越；未载这些人进入后梁宫禁。')

event('xiazhou_coalition_siege', '岐、邠、泾联合晋军围夏州，李仁福守城', 20,
      '岐王与邠、泾二帅各遣使告晋，请合兵攻定难节度使李仁福。晋王遣振武节度使周德威将兵会之，合五万众围夏州，仁福婴城拒守。',
      [('李茂贞', '向晋请求合兵攻夏州的岐王'),
       ('杨崇本', '参与请晋合兵的邠帅，时称李继徽'),
       ('刘知俊', '参与请晋合兵的泾帅'),
       ('李存勖', '遣周德威会兵的晋王'),
       ('周德威', '率晋兵会盟围夏州'),
       ('李仁福', '固守夏州的定难节度使')],
      when='910年七月后条；确日未载', place='夏州',
      note='邠、泾二帅身份据本书前文及胡三省音注核为李继徽（杨崇本）、刘知俊；五万为主书记载联军数，围城结局在第26段。')
claim('event', 'event_zztj_267_0910_xiazhou_coalition_siege', 'description',
      '《旧五代史》李仁福传也记周德威会兵围夏州、李仁福固守，并称守城月余。', 20,
      '後唐武皇遣大將周德威會邠、鳳之師五萬同攻夏州，仁福固守月餘',
      '旧书“武皇”指已故李克用，与《通鉴》此年晋王李存勖不合；仅补守城时长概数，领军身份异说待核。',
      old_xia, 'adds')

event('liu_shouguang_yichang', '刘守光兼领义昌节度使', 21,
      '八月，以刘守光兼义昌节度使。',
      [('刘守光', '兼领义昌节度使')],
      when='910年八月；确日未载', place='义昌军',
      note='本书五月已任刘继威义昌节度使；胡三省所引《考异》亦未确定如何安置继威，不推其免官。')

event('wang_rong_mother_death', '赵王王镕母何氏去世，后梁遣使吊丧', 22,
      '会赵王镕母何氏卒，庚申，遣使吊之，且授起复官。',
      [('王镕', '母何氏去世的赵王'), ('王镕母何氏', '赵王王镕之母，卒于此条'),
       ('朱温', '遣吊使并授起复官的梁帝')],
      when='910年八月庚申遣使；何氏卒日未载', place='镇州、后梁朝廷',
      note='史仅载母姓何，名未载；吊使抵达与何氏去世未必同日。')
relation('王镕母何氏', '王镕', '母亲', 22, '赵王镕母何氏卒',
         '原文明言母子；限定展示名避免与其他何氏合并。')
event('liang_envoy_reports_jin', '梁吊使见晋使后报告王镕或与晋往来', 22,
      '使者见晋使，归，言于帝曰：“镕潜与晋通，镇、定势强，终恐难制。”帝深然之。',
      [('王镕', '梁使怀疑与晋往来的赵王'), ('朱温', '采纳梁使怀疑的梁帝')],
      when='910年八月庚申吊使返梁后；确日未载', place='镇州、后梁朝廷',
      note='“潜与晋通”是使者推断并获梁帝认可，不能单凭见到晋使证明秘密盟约已经成立。')

event('li_renfu_emergency', '李仁福向后梁告急，请救夏州', 23,
      '壬戌，李仁福来告急。',
      [('李仁福', '夏州被围后向梁帝告急的定难节度使')],
      when='910年八月壬戌', place='夏州、后梁朝廷',
      note='“来告急”按主书编年，不据此推算使者出发日。')
event('zhang_quanyi_xijing', '朱温任张全义为西京留守', 23,
      '甲子，以河南尹兼中书令张宗奭为西京留守。',
      [('张宗奭', '时名宗奭，获任西京留守的张全义')],
      when='910年八月甲子', place='西京洛阳',
      note='张宗奭是张全义在梁时赐名；胡三省音注本正文作全义并列举宗奭异文，复用既有人物，不另建实体。')
event('li_sian_heyang', '朱温遣李思安率万人屯河阳防晋军袭西京', 23,
      '帝恐晋兵袭西京，以宣化留后李思安为东北面行营都指挥使，将兵万人屯河阳。',
      [('朱温', '因担忧晋军袭西京而部署河阳'), ('李思安', '受任东北面行营都指挥使，率万人屯河阳')],
      when='910年八月甲子后；确日未载', place='河阳',
      note='万人为主书所称李思安所率兵数；“恐袭”是梁帝判断，非晋军已袭西京。')
event('liang_emperor_shanzhou', '朱温自洛阳赴陕州督战', 23,
      '丙寅，帝发洛阳；己巳，至陕。',
      [('朱温', '从洛阳赴陕州的梁帝')],
      when='910年八月丙寅出发、己巳抵陕', place='洛阳、陕州',
      note='两个干支日保留；不换算公历日。')
event('yang_kang_sanyuan', '朱温以杨师厚为招讨使，与康怀贞屯三原', 23,
      '辛未，以镇国节度使杨师厚为西路行营招讨使，会感化节度使康怀贞将兵三万屯三原。',
      [('杨师厚', '受任西路行营招讨使'), ('康怀贞', '会兵三万屯三原的感化节度使'),
       ('朱温', '任命杨师厚并部署三原军队的梁帝')],
      when='910年八月辛未', place='三原',
      note='三万是会军部署的史载数，不拆为两人各三万人；仍沿《通鉴》康怀贞用字。')
event('li_yu_liu_wan_intercept', '朱温遣李遇、刘绾趋银夏，截岐晋兵归路', 23,
      '甲申，遣夹马指挥使李遇、刘绾自鄜、延趋银、夏，邀其归路。',
      [('朱温', '命军截击围夏州联军归路'), ('李遇', '受命自鄜延趋银夏的夹马指挥使'),
       ('刘绾', '与李遇一同受命的夹马指挥使')],
      when='910年八月甲申', place='鄜州、延州、银州、夏州',
      note='此段是命令与行军计划；实际到夏州、联军撤围在第26段。')

event('qian_liu_hai_tang', '钱镠修筑杭州捍海石塘并扩城', 24,
      '吴越王镠筑捍海石唐，广杭州城，大修台馆。由是钱唐富庶盛于东南。',
      [('钱镠', '修筑海塘、扩建杭州城及台馆的吴越王')],
      when='910年本段条；确日未载', place='杭州、钱唐',
      note='选定电子底本作“捍海石唐”，胡三省音注本作“捍海石塘”；标题用通行设施名，原引照录。富庶是史书因果判断，不据此测算财富。')
event('liang_emperor_return_ill', '朱温九月返洛阳，旧疾复发', 25,
      '九月，己丑，上发陕；甲午，至洛阳，疾复作。',
      [('朱温', '自陕返洛阳后旧疾复发的梁帝')],
      when='910年九月己丑出发、甲午抵洛阳', place='陕州、洛阳',
      note='原文未明疾病现代诊断，也未说明病情此后持续。')
event('xiazhou_siege_lifted', '李遇等抵夏州，岐晋联军撤围', 26,
      '李遇等至夏州，岐、晋兵皆解去。',
      [('李遇', '率梁军抵达夏州的将领'), ('李仁福', '夏州守军主帅，围城得解')],
      when='910年九月甲午后条；确日未载', place='夏州',
      note='“至夏州”“皆解去”按主书先后；未明每支联军撤退的具体日期及损失。')
event('liang_zezhou_garrison', '后梁遣杨师厚、李思安屯泽州，谋取上党', 27,
      '冬，十月，遣镇国节度杨师厚、相州刺史李思安将兵屯泽州以图上党。',
      [('杨师厚', '受命屯泽州谋上党'), ('李思安', '同受命屯泽州谋上党')],
      when='910年十月；确日未载', place='泽州、上党',
      note='“以图”仅为战略意图，此段不载攻取上党。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(18, 28):
    ledger[n - 1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                         review='卷267开平四年第18—27段连续处理；韦庄、张全义及石塘按音注本校识，底本原字保留。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=267, year=910,
    primary_source_key=main1, primary_source_keys=[main1, main2],
    paragraphs=[Q[n]['id'] for n in range(18, 28)],
    next_paragraph='zztj-v267-y0910-p028',
    coverage='卷267开平四年第18—27段，韦庄卒、夏州围救、镇定交恶伏线及钱镠海塘。',
    supplements=supplements, status=status,
    textual_reviews=[dict(paragraph_id=Q[n]['id'], review_url='https://zh.wikisource.org/zh-hant/資治通鑑_(胡三省音注)/卷267',
                          note=note) for n, note in ((18, '底本“韧城”校作韦庄'),
                                                       (20, '邠泾二帅身份据胡注'),
                                                       (23, '宗奭、全义为同一人'),
                                                       (24, '底本“石唐”校作石塘'))]),
    ensure_ascii=False, indent=2) + '\n')
print({key: len(value) for key, value in B.items() if isinstance(value, list)})
