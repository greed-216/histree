"""Curate consecutive Tongjian volume 271, year 920, paragraphs 5–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 27))
specs = [
    ('tongjian-271-920-april', YEAR / 'part-01/sources/library/tongjian-271-920-april', '438b833a', '司马光等'),
    ('jiuwudaishi-010-liqi-appointment', P / 'sources/library/jiuwudaishi-010-liqi-appointment', 'e9c4775b', '薛居正等'),
    ('jiuwudaishi-010-tongzhou', P / 'sources/library/jiuwudaishi-010-tongzhou', 'e9c4775b', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0920-p005-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
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
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(5, 9):
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
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷271·贞明六年（920）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0920_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'蜀主':'王宗衍','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271贞明六年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='920年本段条；确日未载', note='', year=920, place='五代十国'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0920_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_271_0920_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('li_qi_appointed_chancellor','梁任李琪为中书侍郎、同平章事',5,
      '夏，四月，乙亥，以尚书右丞李琪为中书侍郎、同平章事。',
      [('李琪','由尚书右丞任中书侍郎、同平章事者')],
      when='920年四月乙亥',place='梁',
      note='旧书卷十同记任命，但日次置于该卷条目中；主书日期按原文。')
claim('event','event_zztj_271_0920_li_qi_appointed_chancellor','description',
      '《旧五代史》卷十同记以李琪为中书侍郎、平章事。',5,
      '以尚書左丞李琪為中書侍郎、平章事。',
      '旧书作尚书左丞，主书作尚书右丞；保留原文职衔异文，任相事实相合。',
      'jiuwudaishi-010-liqi-appointment','conflicts')
brother=person('李珽',5,'李琪之兄','琪，珽之弟也，')
younger=person('李琪',5,'李珽之弟','琪，珽之弟也，')
rk='relationship_zztj_271_0920_li_ting_elder_of_li_qi'
B['person_relationships'].append(dict(key=rk,person_a_key=brother,person_b_key=younger,
    relation_type='兄长',description='李珽是李琪的兄长。',status='draft'))
claim('person_relationship',rk,'description','李珽是李琪的兄长。',5,
      '琪，珽之弟也，','由“李琪是李珽之弟”转写为有向兄长关系。')
event('li_qi_demoted_after_xiao_qing_memorial','萧顷奏李琪改摄为守，李琪被罢为太子少保',5,
      '萧顷与琪同为相，顷谨密而阴伺琪短。久之，有以摄官求仕者，琪辄改摄为守，顷奏之。帝大怒，欲流琪远方，赵、张左右之，止罢为太子少保。',
      [('李琪','被萧顷奏劾后罢相为太子少保者'),('萧顷','奏李琪改摄官为守官者'),
       ('赵岩','在梁帝欲流李琪时为之转圜者'),('张汉杰','在梁帝欲流李琪时为之转圜者')],
      when='李琪四月任相后“久之”；确年、月、日未载',year=None,place='梁',
      note='“久之”是追叙，未强定此事仍发生于920；“欲流”未实际流放。')
claim('person','person_李琪','description','主书称李琪挟赵岩、张汉杰之势，颇通贿赂。',5,
      '琪，珽之弟也，性疏俊，挟赵岩、张汉杰之势，颇通贿赂。',
      '主书的人物评价与行为叙述，始年未定；不从评价推具体贪赃数额。')

event('zhu_youqian_takes_tongzhou','朱友谦袭取同州，程全晖奔大梁',5,
      '河中节度使冀王友谦以兵袭取同州，逐忠武节度使程全晖，全晖奔大梁。',
      [('朱友谦','率兵袭取同州的河中节度使'),('程全晖','被逐后奔大梁的忠武节度使')],
      when='920年四月后本段；确日未载',place='同州、大梁',
      note='原文记袭取、被逐与逃奔，不推具体攻城经过。')
claim('event','event_zztj_271_0920_zhu_youqian_takes_tongzhou','description',
      '《旧五代史》卷十记朱友谦先袭陷同州、程全晖单骑奔京师。',5,
      '先是，河中朱友謙襲陷同州，節度使程全暉單騎奔京師。',
      '旧书“先是”说明其为六月讨伐前事；与主书袭取、逃奔互证，单骑为补充。',
      'jiuwudaishi-010-tongzhou','adds')
event('zhu_lingde_appointed_tongzhou_acting','朱友谦以子朱令德为忠武留后',5,
      '友谦以其子令德为忠武留后，',
      [('朱友谦','以子朱令德为忠武留后者'),('朱令德','被父任为忠武留后者')],
      when='920年朱友谦袭取同州后；确日未载',place='同州',
      note='“留后”与后晋王授正式节度使分期。')
father=person('朱友谦',5,'朱令德之父','友谦以其子令德为忠武留后，')
son=person('朱令德',5,'朱友谦之子','友谦以其子令德为忠武留后，')
rk='relationship_zztj_271_0920_zhu_youqian_father_of_zhu_lingde'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=son,
    relation_type='父亲',description='朱友谦是朱令德的父亲。',status='draft'))
claim('person_relationship',rk,'description','朱友谦是朱令德的父亲。',5,
      '友谦以其子令德为忠武留后，','“其子”明确父子；令德沿朱姓创建规范名。')
event('liang_first_refuses_then_grants_tongzhou','梁帝先拒朱友谦请节，后以其兼忠武节度使',5,
      '表求节钺，帝怒，不许。既而惧友谦怨望，己酉，以友谦兼忠武节度使。',
      [('朱友谦','请节初被拒而后获梁帝兼授者')],
      when='920年四月后己酉授节；初请确日未载',place='梁、同州',
      note='保留先拒后授的顺序，不将两道决定合并为一次批准。')
claim('event','event_zztj_271_0920_liang_first_refuses_then_grants_tongzhou','description',
      '《旧五代史》卷十记朱友谦表请节旄初不允，后兼同州节度使。',5,
      '友謙以其子令德為同州留後，表求節旄，不允；既而帝慮友謙怨望，遂命兼鎮同州，',
      '旧书将职衔称“兼镇同州”，与主书“兼忠武节度使”分别保存。',
      'jiuwudaishi-010-tongzhou','corroborates')
event('jin_grants_zhu_lingde_tongzhou_jiedushi','朱友谦转求晋王节钺，晋王任朱令德为忠武节度使',5,
      '制下，友谦已求节钺于晋王，晋王以墨制除令德忠武节度使。',
      [('朱友谦','梁制下前已向晋王求节者'),('晋王','以墨制任朱令德者'),
       ('朱令德','获晋王墨制授忠武节度使者')],
      when='920年梁己酉授节制下前后；晋墨制确日未载',place='同州、晋',
      note='主书说明梁制下时朱友谦已向晋求节；墨制任命对象是其子令德。')

event('yang_longyan_illness_after_wu_kingship','吴宣王杨隆演建国称制后寝疾',6,
      '吴宣王重厚恭恪，徐温父子专政，王未尝有不平之意形于言色，温以是安之。及建国称制，尤非所乐，多沉饮鲜食，遂成寝疾。',
      [('吴宣王','建国称制后寝疾的吴王'),('徐温','主书所称专政的吴执政者')],
      when='吴建国称制后至920年逝前；起病确年未载',year=None,place='吴',
      note='吴宣王沿杨隆演既有主体；“徐温父子”未点名子，不擅定徐知诰或徐知训。')

event('xu_wen_rejects_usurpation_counsel','徐温驳斥劝其自取吴国者',7,
      '五月，温自金陵入朝，议当为嗣者。或希温意言曰：“蜀先主谓武侯：‘嗣子不才，君宜自取。’”温正色曰：“吾果有意取之，当在诛张颢之初，岂至今日邪！使杨氏无男，有女亦当立之。敢妄言者斩！”',
      [('徐温','入朝议嗣并公开驳斥自取吴国建议者')],
      when='920年五月；确日未载',place='金陵、吴朝',
      note='这里只记录徐温答辞及当时议嗣，不把答辞当作其内心动机的独立证据。')
event('yang_pu_appointed_regent','吴迎杨溥监国',7,
      '乃以王命迎丹杨公溥监国，',
      [('杨溥','受吴王命迎为监国的丹杨公'),('徐温','议嗣后奉王命迎杨溥者')],
      when='920年五月；确日未载',place='吴',
      note='监国先于六月戊申即吴王位，分开记录。')
event('yang_meng_moved_to_shuzhou','吴徙杨濛为舒州团练使',7,
      '徙溥兄濛为舒州团练使。',
      [('杨濛','被徙为舒州团练使的杨溥之兄'),('杨溥','杨濛之弟')],
      when='920年五月；确日未载',place='舒州',
      note='“徙”是任官变动，不推囚禁或罪名。')
elder=person('杨濛',7,'杨溥之兄','徙溥兄濛为舒州团练使。')
younger=person('杨溥',7,'杨濛之弟','徙溥兄濛为舒州团练使。')
rk='relationship_zztj_271_0920_yang_meng_elder_of_yang_pu'
B['person_relationships'].append(dict(key=rk,person_a_key=elder,person_b_key=younger,
    relation_type='兄长',description='杨濛是杨溥的兄长。',status='draft'))
claim('person_relationship',rk,'description','杨濛是杨溥的兄长。',7,
      '徙溥兄濛为舒州团练使。','“溥兄濛”明示长幼；不由已知两人与杨隆演关系臆推次序。')

event('yang_longyan_dies','吴宣王杨隆演去世',8,
      '己丑，宣王殂。',[('吴宣王','于己丑去世的吴王')],
      when='920年五月己丑',place='吴',
      note='承上段“吴宣王”；主书使用殂，月承五月。')
event('yang_pu_succeeds_wu_king','杨溥即吴王位',8,
      '六月，戊申，溥即吴王位。',[('杨溥','继即吴王位者')],
      when='920年六月戊申',place='吴',
      note='与五月监国分开。')
event('yang_pu_mother_wang_named_taifei','杨溥尊母王氏为太妃',8,
      '尊母王氏曰太妃。',[('杨溥','尊母王氏为太妃者'),('王氏','获尊太妃的杨溥之母')],
      when='920年六月戊申即位后本段；确日未载',place='吴',
      note='王氏以杨溥母消歧，不与其他同姓王氏合并。')
mother=person('王氏',8,'杨溥之母','尊母王氏曰太妃。')
son=person('杨溥',8,'王氏之子','尊母王氏曰太妃。')
rk='relationship_zztj_271_0920_yang_pu_mother_wang'
B['person_relationships'].append(dict(key=rk,person_a_key=mother,person_b_key=son,
    relation_type='母亲',description='杨溥母王氏是杨溥的母亲。',status='draft'))
claim('person_relationship',rk,'description','杨溥母王氏是杨溥的母亲。',8,
      '尊母王氏曰太妃。','“母王氏”明确母子；不据此推与其他吴王母亲同人。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5, 9):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明六年第5—8段；李琪任罢、同州易手、吴王议嗣与杨溥继位。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=920,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(5, 9)], next_paragraph=Q[9]['id'],
    coverage='卷271贞明六年第5—8段；梁相李琪、朱友谦袭同州、吴杨隆演逝与杨溥继位。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[5]['id'],'note':'李琪任相主书作尚书右丞、旧书作左丞；职衔异文并列。其被罢前有“久之”，未硬定920。朱友谦为朱令德之父有明文。'},
      {'paragraph_id':Q[6]['id'],'note':'“徐温父子专政”未点名儿子，未据此建立特定父子参与关系；杨隆演寝疾始年不明。'},
      {'paragraph_id':Q[7]['id'],'note':'徐温反对自取吴国为史载言辞，不推内心动机；杨濛为杨溥兄有直接明文。'},
      {'paragraph_id':Q[8]['id'],'note':'吴宣王沿杨隆演既有主体；杨溥母王氏采用消歧规范名，不与其他王氏合并。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
