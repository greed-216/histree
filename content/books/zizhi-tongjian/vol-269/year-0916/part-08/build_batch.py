"""Curate consecutive Tongjian vol. 269, 916 paragraphs 37–38."""
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
main = 'tongjian-269-916-yearend'
liao01 = 'liaoshi-001-shence'
liao71 = 'liaoshi-071-shulv-ping'
liao74a = 'liaoshi-074-han-yanhui-early'
liao74b = 'liaoshi-074-han-yanhui-return'
new72 = 'xinwudaishi-072-han-yanhui'
specs = [(main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-07/sources/library' / main, 'ff79148c', '司马光等')]
for key, author in [(liao01,'脱脱等'),(liao71,'脱脱等'),(liao74a,'脱脱等'),(liao74b,'脱脱等'),(new72,'欧阳修')]:
    specs.append((key, P / 'sources/library' / key, '5d6a1646', author))
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p037-p038',
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
for n in range(37, 39):
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
    ck = f'claim_zztj_269_0916_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'蜀主':'王建','晋王':'李存勖','述律后':'述律平','述律氏':'述律平','契丹主':'阿保机','李存审':'符存审','王宗播':'许存','契丹王阿保机':'阿保机','晋王':'李存勖','述律后':'述律平','述律氏':'述律平','契丹主':'阿保机'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=['述律氏','述律后','述律皇后'] if name == '述律平' else [],
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

# p037 is mostly retrospective. Date only the 916 imperial titles and Shence era.
event('yan_soldiers_flee_to_khitan','燕军士因刘守光残虐多归契丹',37,
      '初，燕人苦刘守光残虐，军士多归于契丹。',
      [('刘守光','燕军士因其残虐而离开的燕主')],
      when='刘守光治燕期间；确年未载',place='燕、契丹',year=None,
      note='“初”标示追叙，不当作916年新发生的逃亡。')
event('khitan_raids_yan_during_siege','刘守光被围幽州时，契丹掠其北边士民',37,
      '及守光被围于幽州，其北边士民多为契丹所掠，契丹日益强大。',
      [('刘守光','幽州被围时的燕主')],
      when='刘守光被围幽州期间；非916年当年叙事',place='幽州北边',year=None,
      note='承“初”追叙；被掠人数与范围未载。')
event('abaoji_takes_imperial_title','阿保机称帝，述律氏受后号并置百官',37,
      '契丹王阿保机自称皇帝，国人谓之天皇王，以妻述律氏为皇后，置百官。',
      [('阿保机','称帝并立述律氏为后的契丹王'),('述律氏','受皇后称号的阿保机之妻')],
      when='916年神册元年；《辽史》纪春二月丙申受尊号',place='契丹',
      note='主书记自称皇帝、天皇王及置百官；《辽史》记916年二月受尊号，称号文字不同。')
claim('event','event_zztj_269_0916_abaoji_takes_imperial_title','time_original',
      '《辽史》卷一记神册元年春二月丙申上尊号，后受应天大明地皇后号。',37,
      '丙申，群臣及諸屬國築壇州東，上尊號曰大聖大明天皇帝，后曰應天大明地皇后。',
      '《辽史》具体日按其原纪年引用，不换算公历；尊号与通鉴“天皇王”异文并列。',liao01,'adds')
claim('person',person('述律平',37,'阿保机之妻、契丹皇后','以妻述律氏为皇后'),'description',
      '《辽史》述律氏传明记其名平、小字月理朵。',37,
      '太祖淳欽皇后述律氏，諱平，小字月理朶。',
      '将《通鉴》述律氏/述律后与《辽史》述律平归一；史料原字保留。',liao71,'adds')
rel = 'relationship_person_阿保机_person_述律平_丈夫'
B['person_relationships'].append(dict(key=rel,person_a_key=person('阿保机',37,'契丹王、述律氏之夫','以妻述律氏为皇后'),
    person_b_key=people['述律平'],relation_type='丈夫',description='阿保机是述律平的丈夫。',status='draft'))
claim('person_relationship',rel,'description','阿保机是述律平的丈夫。',37,
      '以妻述律氏为皇后','主书明称述律氏为阿保机妻，关系方向从丈夫指向妻子。')
event('khitan_shence_era_begins','契丹改元神册',37,
      '至是，改元神册。',
      [('阿保机','神册改元时的契丹皇帝')],
      when='916年神册元年；《辽史》纪春二月丙申',place='契丹',
      note='“至是”将前述追叙接回916年；未把更早的事一律定在神册元年。')
claim('event','event_zztj_269_0916_khitan_shence_era_begins','description',
      '《辽史》卷一记受尊号、大赦并建元神册。',37,
      '大赦，建元神冊。',
      '大赦为辽史补充，主书只明确改元。',liao01,'corroborates')
event('shulv_ping_repels_shiwei','述律平守营击败黄头、臭泊室韦',37,
      '阿保机尝度碛击党项，留述律后守其帐，黄头、臭泊二室韦乘虚合兵掠之。述律后知之，勒兵以待其至，奋击，大破之，由是名震诸夷。',
      [('阿保机','度碛攻击党项而留述律后守营者'),('述律后','守营并击败室韦的契丹皇后')],
      when='阿保机攻党项期间；确年未载',place='碛、契丹营帐',year=None,
      note='“尝”是未定年回顾，不标成916年战事；二室韦名称按原文。')
claim('event','event_zztj_269_0916_shulv_ping_repels_shiwei','description',
      '《辽史》述律氏传亦记其击败黄头、臭泊室韦。',37,
      '黃頭、臭泊二室韋乘虚襲之；后知，勒兵以待，奮撃，大破之',
      '辽史同事，但可能与通鉴共享前人材料；不以两书作完全独立确证。',liao71,'corroborates')
claim('person',people['述律平'],'description',
      '《通鉴》记述律后称只拜天、不拜人，展现其仪礼态度。',37,
      '吾惟拜天，不拜人也。',
      '这是一则未定年的传记轶事，不在916年时间线上另建事件。')
event('jin_king_treats_khitan_couple_as_elders','晋王以叔父、叔母之礼事阿保机及述律后',37,
      '晋王方经营河北，欲结契丹为援，常以叔父事阿保机，以叔母事述律后。',
      [('李存勖','以叔父叔母之礼结契丹为援的晋王'),('阿保机','受晋王叔父之礼的契丹王'),('述律后','受晋王叔母之礼的契丹皇后')],
      when='晋王经营河北期间；确年未载',place='晋、契丹',year=None,
      note='这是外交礼称，不能建为真实叔侄血缘关系。')

# p038 is a career retrospective from Liu Shouguang's late rule through Jin and Khitan.
event('liu_shouguang_sends_han_to_khitan','刘守光遣韩延徽赴契丹求援',38,
      '刘守光末年衰困，遣参军韩延徽求援于契丹。',
      [('刘守光','遣参军向契丹求援的燕主'),('韩延徽','奉命赴契丹的燕参军')],
      when='刘守光末年；确年未载',place='幽州、契丹',year=None,
      note='“末年”明确为916年之前追叙；不把求援记成916年。')
claim('event','event_zztj_269_0916_liu_shouguang_sends_han_to_khitan','description',
      '《新五代史》卷七十二亦记韩延徽为刘守光参军并受派赴契丹。',38,
      '為劉守光參軍，守光遣延徽聘于契丹。',
      '新书用“聘”字，主书作求援；两者目的表述不完全相同。',new72,'corroborates')
event('abaoji_detains_han_for_no_bow','韩延徽不拜阿保机，被留牧马',38,
      '契丹主怒其不拜，留之，使牧马于野。',
      [('阿保机','因韩延徽不拜而将其留在契丹的君主'),('韩延徽','不拜而被留牧马的燕使')],
      when='韩延徽初使契丹时；确年未载',place='契丹',year=None)
event('shulv_ping_recommends_han','述律后劝阿保机礼遇韩延徽，韩延徽成为谋主',38,
      '述律后言于契丹主曰：“延徽能守节不屈，此今之贤者，奈何辱以牧圉！宜礼而用之。”契丹主召延徽与语，悦之，遂以为谋主，举动访焉。',
      [('述律后','劝契丹主礼用韩延徽者'),('阿保机','召韩延徽交谈并任为谋主者'),('韩延徽','获礼用并任谋主者')],
      when='韩延徽初留契丹后；确年未载',place='契丹',year=None)
claim('event','event_zztj_269_0916_shulv_ping_recommends_han','description',
      '《辽史》韩延徽传也记述律后劝用延徽，太祖与其交谈后任参军事。',38,
      '述律后諫曰：「彼秉節弗撓，賢者也，奈何困辱之？」太祖召與語，合上意，立命參軍事。',
      '辽史明确述律后作用；与新五代史省略该细节不同，未据此推翻主书。',liao74a,'corroborates')
event('han_yanhui_sets_up_khitan_settlements','韩延徽建议建城、市里、婚配与耕作安置汉人',38,
      '延徽始教契丹建牙开府，筑城郭，立市里，以处汉人，使各有配偶，垦艺荒田。由是汉人各安生业，逃亡者益少。',
      [('韩延徽','建议契丹建政设城安置汉人者')],
      when='韩延徽在契丹任谋主期间；确年未载',place='契丹',year=None,
      note='主书把多项措施合叙且未给实施地点、逐年顺序，不拆成虚构日期。')
claim('event','event_zztj_269_0916_han_yanhui_sets_up_khitan_settlements','description',
      '《辽史》韩延徽传同记建城、市里、配偶和垦艺。',38,
      '乃請樹城郭，分市裏，以居漢人之降者。又為定配偶，教墾藝，以生養之。',
      '辽史称“汉人之降者”，主书泛称汉人；只承认记载相近。',liao74a,'corroborates')
event('han_yanhui_flees_to_jinyang','韩延徽逃往晋阳，晋王拟置幕府',38,
      '顷之，延徽逃奔晋阳。晋王欲置之幕府，掌书记王缄疾之。',
      [('韩延徽','从契丹逃至晋阳者'),('李存勖','欲将韩延徽置于幕府的晋王'),('王缄','嫉韩延徽的晋王掌书记')],
      when='韩延徽在契丹任谋主后；确年未载',place='晋阳',year=None,
      note='“顷之”相对前事，无足够证据将抵晋阳定在916年。')
event('han_yanhui_visits_mother_and_wang_deming','韩延徽离晋省母，途中寄住王德明家',38,
      '延徽不自安，求东归省母，过真定，止于乡人王德明家',
      [('韩延徽','离晋赴东省母并住王德明家的燕人'),('王德明','留韩延徽寄住的同乡')],
      when='韩延徽逃至晋阳后；确年未载',place='晋阳、真定、幽州',year=None,
      note='省母地点承后文“既省母”与幽州背景；未按现代地名定位。')
event('han_yanhui_returns_to_khitan','韩延徽省母后重返契丹，阿保机厚待之',38,
      '既省母，遂复入契丹。契丹主闻其至，大喜，如自天而下',
      [('韩延徽','省母后返回契丹者'),('阿保机','闻韩延徽归来而欣喜的契丹主')],
      when='韩延徽省母后；确年未载',place='契丹',year=None)
claim('event','event_zztj_269_0916_han_yanhui_returns_to_khitan','description',
      '《辽史》记韩延徽再至契丹，太祖欢喜并赐名“匣列”。',38,
      '上大悅，賜名曰匣列。「匣列」，遼言復來也。',
      '赐名是辽史补充；未在本站另建同名人物。',liao74b,'adds')
event('han_yanhui_khitan_chancellor','阿保机称帝后任韩延徽为相',38,
      '及称帝，以延徽为相，累迁至中书令。',
      [('阿保机','称帝后任韩延徽为相的契丹君主'),('韩延徽','任相并后迁中书令者')],
      when='阿保机称帝后；晋升中书令时间未载',place='契丹',year=None,
      note='本句把任相与“累迁”合叙，不能都定在916年；《辽史》另载返契丹后授守政事令。')
claim('event','event_zztj_269_0916_han_yanhui_khitan_chancellor','description',
      '《辽史》韩延徽传作其返契丹后任守政事令、崇文馆大学士。',38,
      '即命為守政事令、崇文館大學士，中外事悉令參決。',
      '职官名称和任命节点与通鉴概述不同，未直接等同“中书令”。',liao74b,'adds')
event('han_yanhui_letter_to_jin','韩延徽致晋王书，解释北去并托养母',38,
      '晋王遣使至契丹，延徽寓书于晋王，叙所以北去之意，且曰：“非不恋英主，非不思故乡，所以不留，正惧王缄之谗耳。”因以老母为托',
      [('韩延徽','致书晋王说明北去并托养母者'),('李存勖','收到韩延徽书信的晋王'),('王缄','被韩延徽书中指责进谗者')],
      when='韩延徽复入契丹后；确年未载',place='契丹、晋',year=None,
      note='韩延徽的“惧王缄之谗”是其自述，不据此断言王缄曾提出具体谗言。')
claim('person',person('韩延徽',38,'由燕使转任契丹谋主','延徽，幽州人，有智略，颇知属文。'),'description',
      '《通鉴》称韩延徽主张有己在契丹便不南牧，并称同光年间契丹未深入为寇。',38,
      '延徽在此，契丹必不南牧。',
      '引文是韩延徽自述；“终同光之世”是后见总结，不作为916年已发生的事实。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(37, 39):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269贞明二年第37—38段；神册改元定916年，燕末与韩延徽经历多属追叙，未知确年不强行定年。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=916,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(37,39)],
    next_paragraph=None,coverage='卷269贞明二年末两段；契丹神册改元、述律后及韩延徽生平追叙。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[37]['id'],'note':'《辽史》卷一系神册元年春二月受尊号、改元；《通鉴》“初”以下燕民迁逃、室韦战、结援等追叙未给确年。述律后据辽史名平，叔父叔母仅外交礼称。'},
      {'paragraph_id':Q[38]['id'],'note':'韩延徽使契丹、归晋、复入契丹各事按相对先后记录，具体年份未定；相官与后迁中书令不一律归到916。同光之世结论仅作追叙声明。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
