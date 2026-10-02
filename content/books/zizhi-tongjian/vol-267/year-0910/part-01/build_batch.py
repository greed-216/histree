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
main = 'tongjian-267-909-yearend'  # The exact exported paragraph crosses the 909/910 boundary and ends at 910 p010.
old_cang = 'xinwudaishi-039-cangzhou'
old_xia = 'jiuwudaishi-132-lirenfu'
old_cui = 'jiuwudaishi-068-cuiyi'
new_kou = 'xinwudaishi-021-kouyanqing'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0910-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main, YEAR.parent / 'year-0909/part-03/sources/library' / main, '0d6451a5', '司马光等'),
    (old_cang, YEAR.parent / 'year-0909/part-03/sources/library' / old_cang, '0d6451a5', '欧阳修等'),
    (old_xia, P / 'sources/library' / old_xia, '8f8f3416', '薛居正等'),
    (old_cui, P / 'sources/library' / old_cui, '8f8f3416', '薛居正等'),
    (new_kou, P / 'sources/library' / new_kou, '8f8f3416', '欧阳修等'),
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
for n in range(1, 11):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in main_text, n

registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
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
    ck = f'claim_zztj_267_0910_01_{len(B["claims"])+1:04d}'
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
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

# 沧州降服与随后处置；吕琦后任代州判官的日期未由本段确定。
event('cangzhou_surrender', '刘延祚力竭，出降刘守光', 1, '春，正月，乙未，刘延祚力尽出降。',
      [('刘延祚', '沧州守方，力尽出降'), ('刘守光', '受降并控制沧州的燕主')],
      when='910年正月乙未', place='沧州')
event('cangzhou_new_command', '刘守光遣张万进、周知裕辅刘继威镇守沧州', 1,
      '守光使大将张万进、周知裕辅之镇沧州，以延祚及其将佐归幽州',
      [('刘守光', '派军将辅其子镇沧州'), ('刘继威', '受辅镇沧州的幼子'),
       ('张万进', '受命辅刘继威镇沧州'), ('周知裕', '受命辅刘继威镇沧州'),
       ('刘延祚', '被押送幽州的前沧州守方')],
      when='910年正月乙未降后', place='沧州、幽州',
      note='刘继威当时年幼；不推定两名辅佐将领的后续任期。')
event('lu_yan_execution', '刘守光族吕兖而释放孙鹤', 1, '族吕兗而释孙鹤。',
      [('刘守光', '下令诛吕兖家族、释放孙鹤'), ('吕兖', '遭族诛的沧州旧臣'),
       ('孙鹤', '被释放的沧州旧臣')], when='910年沧州出降后', place='幽州',
      note='“族吕兗”照主书记载；吕琦获救见下句，不能据此断言家族无一生还。')
event('lu_qi_rescue', '赵玉冒称吕琦为弟并负其逃脱', 1,
      '门下客赵玉绐监刑者曰：“此吾弟也，勿妄杀。”监刑者信之，遂挈以逃。琦足痛不能行，玉负之，变姓名，乞食于路，仅而得免。',
      [('赵玉', '冒称吕琦为弟并负其逃生的门客'), ('吕琦', '吕兖之子，获赵玉救出的少年')],
      when='910年吕兖被族诛时', place='幽州逃亡路上',
      note='“此吾弟”是赵玉欺骗监刑者的说法，不建立兄弟关系。')
relation('吕兖', '吕琦', '父亲', 1, '兗子琦，年十五', '“兗子琦”确认父子，兗仅在展示名规范为兖。')
event('lu_qi_daizhou', '晋王闻吕琦之名，任其为代州判官', 1,
      '晋王闻其名，署代州判官。', [('李存勖', '听闻吕琦并予任命的晋王'),
                                    ('吕琦', '后被任为代州判官')],
      when='吕琦逃脱后；确年未载', place='代州', year=None,
      note='本句承接逃亡经历，但任命日期不明，不强置于910年。')
claim('event', 'event_zztj_267_0910_cangzhou_surrender', 'description',
      '《新五代史》卷三十九亦记刘延祚力穷后降，印证沧州降服结局。', 1,
      '久之，延祚力窮，遂降', '仅印证降服，不借其“久之”倒推确切开围日。', old_cang)

event('lu_guangchou_appointment', '后梁任卢光稠为镇南留后', 2,
      '辛丑，以卢光稠为镇南留后。', [('卢光稠', '获任镇南留后')],
      when='910年正月辛丑', place='镇南军')
event('liu_rengong_retirement', '刘守光为父刘仁恭请致仕，后梁授其太师致仕', 3,
      '刘守光为其父仁恭请致仕，丙午，以仁恭为太师，致仕。',
      [('刘守光', '为父请致仕'), ('刘仁恭', '受太师衔致仕')],
      when='910年正月丙午', place='幽州',
      note='致仕为名义安排；不推定刘仁恭当时人身自由。')
event('liu_shouwen_murder', '刘守光暗杀兄刘守文，并归罪执行者', 3,
      '守光寻使人潜杀其兄守文，归罪于杀者而诛之。',
      [('刘守光', '使人潜杀刘守文并诛杀执行者'), ('刘守文', '被兄弟刘守光暗杀')],
      when='910年正月丙午后；确日未载', place='幽州',
      note='暗杀与诛执行者均按主书叙述；未载执行者姓名。')

event('wu_title_amnesty', '岐王加杨隆演兼中书令、嗣吴王，吴境大赦', 4,
      '万全感自岐归广陵，岐王承制加弘农王兼中书令，嗣吴王，于是吴王赦其境内。',
      [('万全感', '从岐地返回广陵'), ('李茂贞', '承制加授吴王名号的岐王'),
       ('杨隆演', '受加兼中书令、嗣吴王并赦境内的弘农王')],
      when='910年二月；确日未载', place='岐、广陵、吴境',
      note='“嗣吴王”按原文保留；不把岐王承制写成梁廷直接任命。')
event('gao_li_flees_wu', '高澧求吴援未得入湖州，率五千人奔吴', 5,
      '高澧求救于吴，吴常州刺史李简等将兵应之，湖州将盛师友、沈行思闭城不内；澧帅麾下五千人奔吴。',
      [('高澧', '求援后率部奔吴'), ('李简', '率吴兵应援'),
       ('盛师友', '闭湖州城拒高澧入内'), ('沈行思', '闭湖州城拒高澧入内')],
      when='910年三月癸巳前；确日未载', place='湖州、吴',
      note='五千为主书记载高澧麾下人数；未明言李简所率兵数。')
event('qian_biao_huzhou', '钱镠巡湖州，任钱镖为刺史', 5,
      '三月，癸巳，吴越王镠巡湖州，以钱镖为刺史。',
      [('钱镠', '巡视湖州并任命刺史'), ('钱镖', '获任湖州刺史')],
      when='910年三月癸巳', place='湖州')

event('shu_heir_daoxi_split', '蜀太子王宗懿与唐道袭交恶，王建外任道袭', 6,
      '太子屡谑之于朝，由是有隙，互相诉于蜀主。蜀主恐其交恶，以道袭为山南西道节度使、同平章事。',
      [('王宗懿', '与唐道袭交恶的蜀太子'), ('唐道袭', '被外任山南西道节度使'),
       ('王建', '为免二人交恶而外任唐道袭的蜀主')],
      when='910年三月后条；确日未载', place='蜀、山南西道',
      note='“恐其交恶”为蜀主担忧，不替二人判定事件责任。')
event('zheng_xu_appointment', '唐道袭荐郑顼继任蜀内枢密使', 6,
      '道袭荐宣徽北院使郑顼为内枢密使',
      [('唐道袭', '荐举郑顼'), ('郑顼', '受荐任内枢密使')],
      when='910年唐道袭外任后；确日未载', place='蜀')
event('zheng_xu_dismissal', '郑顼欲查唐道袭兄弟库帛，王建出郑顼并任潘炕', 6,
      '顼受命之日，即欲按道袭昆弟盗用内库金帛。道袭惧，奏项褊急，不可大任，丙午，出顼为果州刺史，以宣徽南院使潘炕为内枢密使。',
      [('郑顼', '拟查内库盗用，被出为果州刺史'), ('唐道袭', '奏称郑顼不宜重任'),
       ('王建', '决定改任郑顼及潘炕的蜀主'), ('潘炕', '继任内枢密使')],
      when='910年三月丙午', place='蜀、果州',
      note='盗用内库仍是拟查之事，不能写成已证实；底本“奏项褊急”疑“顼”讹，原字保留。')

event('xia_military_mutiny', '高宗益作乱杀李彝昌，夏州将吏诛高宗益', 7,
      '夏州都指挥使高宗益作乱，杀节度使李彝昌。将吏共诛宗益',
      [('高宗益', '发动兵变并杀李彝昌，后被诛'), ('李彝昌', '夏州节度使，被高宗益杀害')],
      when='910年春；四月前', place='夏州',
      note='《旧五代史》李仁福传记作开平三年春，与本书编于开平四年相异，保留待考。')
event('li_renfu_commission', '夏州将吏推李仁福为帅，后梁授定难节度使', 7,
      '推彝昌族父蕃汉都指挥使李仁福为帅，癸丑，仁福以闻。夏，四月，甲子，以仁福为定难节度使。',
      [('李仁福', '被夏州将吏推举，后受定难节度使')],
      when='910年春癸丑上报；四月甲子获授', place='夏州',
      note='“族父”仅指同族父辈，不自动建生父或伯父关系。')
claim('event', 'event_zztj_267_0910_xia_military_mutiny', 'description',
      '《旧五代史》卷一百三十二亦记高宗益兵变、李彝昌遇害及李仁福获推，但将事系于开平三年春。', 7,
      '三年春，牙將高宗益等作亂，彜昌遇害',
      '与《通鉴》开平四年条存在一年差异；该传所引后续周德威围夏州不可倒置到本段。', old_xia, 'conflicts')
claim('event', 'event_zztj_267_0910_li_renfu_commission', 'description',
      '《旧五代史》卷一百三十二也载夏州军吏推李仁福，梁帝四月授其定难节度使。', 7,
      '本州軍吏迎立仁福為帥。其年四月，梁祖降制授仁福檢校司空，充定難軍節度使',
      '该传前称“三年春”，故只作身份与授职补证，纪年异说保留。', old_xia)

event('auspicious_wheat_rejected', '朱友谅献瑞麦，朱温以宋州水灾诘责之', 8,
      '丁卯，宋州节度使衡王友谅献瑞麦，一茎三穗，帝曰：“丰年为上瑞。今宋州大水，安用此为！”诏除本县令名，遣使诘责友谅',
      [('朱友谅', '献瑞麦而遭梁帝诘责'), ('朱温', '因宋州水灾拒其瑞麦奏报')],
      when='910年四月丁卯', place='宋州',
      note='瑞麦和水灾按主书记载；不推定宋州全年收成。')
event('zhu_youneng_songzhou', '朱温以朱友能代朱友谅为宋州留后', 8,
      '以兗海留后惠王友能代为宋州留后。友谅、友能，皆全昱子也。',
      [('朱温', '决定更换宋州留后的梁帝'), ('朱友谅', '被替换的宋州节度使'),
       ('朱友能', '受命代任宋州留后')],
      when='910年四月丁卯后', place='宋州',
      note='兗字及官号依电子底本保留，人物展示采用站内规范字形。')
person('朱全昱', 8, '朱友谅、朱友能之父', '友谅、友能，皆全昱子也。')
relation('朱全昱', '朱友谅', '父亲', 8, '友谅、友能，皆全昱子也。', '主书明言二人均朱全昱之子。')
relation('朱全昱', '朱友能', '父亲', 8, '友谅、友能，皆全昱子也。', '主书明言二人均朱全昱之子。')

event('dingchang_command', '后梁以晋绛沁设定昌军，任华温琪为节度使', 9,
      '帝以晋州刺史下邑华温琪拒晋兵有功，欲赏之，会护国节度使冀王友谦上言晋、绛边河东，乞别建节镇，壬申，以晋、绛、沁三州为定昌军，以温琪为节度使。',
      [('朱友谦', '建言另设节镇'), ('朱温', '采纳建节镇并任命华温琪'),
       ('华温琪', '因守晋州功获任定昌节度使')],
      when='910年四月壬申', place='晋州、绛州、沁州',
      note='守晋功见本段前句；新军辖三州仅按主书记载。')

event('tianjin_bridge_death', '寇彦卿前导在天津桥将未避道者投出栏外致死', 10,
      '左金吾大将军寇彦卿入朝，至天津桥，有民不避道，投诸栏外而死。',
      [('寇彦卿', '前导致民死亡的左金吾大将军')],
      when='910年四月辛巳前；确日未载', place='天津桥',
      note='主书未录死者名；《旧五代史》《新五代史》均记为梁现。')
event('cui_yi_impeaches_kou', '崔沂弹劾寇彦卿杀人，梁帝责授寇彦卿', 10,
      '御史司宪崔沂劾奏“彦卿杀人阙下，请论如法。”',
      [('崔沂', '坚持依法弹劾寇彦卿'), ('寇彦卿', '被弹劾的金吾将军')],
      when='910年四月辛巳前；确日未载', place='后梁朝廷',
      note='此处为崔沂奏词；寇彦卿称“不意误死”与之并列，不当作定论。')
claim('event', 'event_zztj_267_0910_cui_yi_impeaches_kou', 'description',
      '崔沂按律反驳将责任归给从者及定为过失的说法。', 10,
      '在法，以势使令为首，下手为从，不得归罪从者',
      '为崔沂援法奏说；不据此推断最终司法判决。')
event('kou_yanqing_demotion', '后梁责授寇彦卿游击将军、左卫中郎将', 10,
      '辛巳，责授彦卿游击将军、左卫中郎将。',
      [('寇彦卿', '因天津桥案受到责授')],
      when='910年四月辛巳', place='后梁朝廷')
event('kou_threat_cui', '寇彦卿扬言悬赏崔沂首，朱温警告不得伤崔沂', 10,
      '彦卿扬言：“有得崔沂首者，赏钱万缗。”沂以白帝，帝使人谓彦卿：“崔沂有毫发伤，我当族汝！”',
      [('寇彦卿', '扬言悬赏崔沂首级'), ('崔沂', '向梁帝报告威胁'),
       ('朱温', '警告寇彦卿不得伤害崔沂')],
      when='910年四月辛巳后；确日未载', place='后梁朝廷',
      note='悬赏为寇彦卿扬言，不表示实际支付或崔沂遇害。')
claim('event', 'event_zztj_267_0910_tianjin_bridge_death', 'description',
      '《旧五代史》崔沂传记死者为市民梁现，并称前导伍伯将其掷栏致死。', 10,
      '市民梁現者不時回避，前導伍伯捽之，投石欄以致斃',
      '补死者名及直接执行者；主书仅写“有民”，未另建同名事件。', old_cui)
claim('event', 'event_zztj_267_0910_tianjin_bridge_death', 'description',
      '《新五代史》寇彦卿传亦记死者梁现和前驱致死。', 10,
      '民梁現不避道，前驅捽現投橋上石欄以死',
      '与旧书互见，但两书可能相互依赖，不当作完全独立确证。', new_kou)

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 11):
    ledger[n - 1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                         review='卷267开平四年第1—10段连续处理；夏州兵变纪年异说及天津桥死者姓名保留分书出处。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=267, year=910,
    primary_source_key=main, paragraphs=[Q[n]['id'] for n in range(1, 11)],
    next_paragraph='zztj-v267-y0910-p011',
    coverage='卷267开平四年第1—10段，沧州降服与处置、吴越湖州、蜀内任免、夏州兵变、天津桥案。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({key: len(value) for key, value in B.items() if isinstance(value, list)})
