"""Curate consecutive Tongjian volume 271, year 920, paragraphs 1–4."""
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
    ('tongjian-271-920-jan-mar', P / 'sources/library/tongjian-271-920-jan-mar', '438b833a', '司马光等'),
    ('tongjian-271-920-april', P / 'sources/library/tongjian-271-920-april', '438b833a', '司马光等'),
    ('jiuwudaishi-065-li-jianji', P / 'sources/library/jiuwudaishi-065-li-jianji', '438b833a', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0920-p001-p004',
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
    ck = f'claim_zztj_271_0920_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'蜀主':'王宗衍','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
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

event('sang_hongzhi_takes_jinzhou_captures_quanshilang','桑弘志克金州，执全师朗献蜀主',1,
      '春，正月，戊辰，蜀桑弘志克金州，执全师朗，献于成都，',
      [('桑弘志','攻取金州并执全师朗者'),('全师朗','金州被俘后送往成都者')],
      when='920年正月戊辰',place='金州、成都',
      note='承919年蜀主命讨，全师朗沿王宗朗既有主体；不据此增造别一人物。')
event('shu_ruler_releases_quanshilang','蜀主释放全师朗',1,
      '蜀主释之。',[('蜀主','释放全师朗者'),('全师朗','被蜀主释放者')],
      when='920年正月戊辰金州事后本段',place='成都',
      note='“释之”仅指释放；未见恢复官爵的明文。')

event('zhang_chong_fails_anzhou_attack','吴张崇攻安州未克而还',2,
      '吴张崇攻安州，不克而还。',[('张崇','攻安州失败后撤回的吴将')],
      when='920年春本段；确日未载',place='安州',
      note='承919年十一月“寇安州”，本段明言未克，不误记占城。')
event('lujiang_accuses_magistrate_of_bribery','庐江民控告县令受赇',2,
      '庐江民讼县令受赇，',[],year=None,
      when='张崇在庐州任时；具体年月未载',place='庐江、庐州',
      note='该句是民间控告，不独立断言县令或张崇已被定罪。')
claim('person','person_张崇','description','《通鉴》称张崇在庐州贪暴不法。',2,
      '崇在庐州，贪暴不法。','主书叙述背景，始年未载；不据此推断具体贪赃案件已审结。')
event('yang_tingshi_proposes_investigating_zhang_chong','杨廷式主张追查张崇，徐知诰谢重之',2,
      '徐知诰遣侍御史知杂事杨廷式往按之，欲以威崇，廷式曰：“杂端推事，其体至重，职业不可不行。”知诰曰：“何如？”廷式曰：“械系张崇，使吏如升州，簿责都统。”知诰曰：“所按者县令耳，何至于是！”廷式曰：“县令微官，张崇使之取民财转献都统耳，岂可舍大而诘小乎！”知诰谢之曰：“固知小事不足相烦。”以是益重之。',
      [('徐知诰','遣杨廷式查事并在对答后更加器重他者'),('杨廷式','主张追查张崇的侍御史知杂事'),('张崇','杨廷式主张追查的庐州都统')],
      when='920年本段叙事；确日未载',place='庐州、升州',
      note='杨廷式提出械系与簿责，原文未说已经逮捕张崇；徐知诰沿李昪既有主体。')
claim('person','person_杨廷式','description','杨廷式，泉州人。',2,
      '廷式，泉州人也。','籍贯仅据主书；与任官事件同主体。')

event('li_jianji_commands_silver_spear_unit','晋王曾命李建及统银枪效节都',3,
      '晋王自得魏州，以李建及为魏博内外牙都将，将银枪效节都。',
      [('晋王','任命李建及统领魏博牙兵者'),('李建及','魏博内外牙都将、银枪效节都统领者')],
      when='晋王得魏州之后，三月罢军职之前；始年未定',year=None,place='魏州',
      note='“自得魏州”是背景追叙，不将任命硬定920年。')
claim('event','event_zztj_271_0920_li_jianji_commands_silver_spear_unit','description',
      '《旧五代史》卷六十五李建及传记其以胡柳之役功授魏博内外衙都将。',3,
      '以功授檢校司空、魏博內外衙都將。',
      '旧书传文说明任官所由，未单独证明银枪效节都任命月份；同一李建及主体。',
      'jiuwudaishi-065-li-jianji','adds')
event('wei_lingtu_accuses_li_jianji','韦令图谮李建及私财分军，晋王起疑',3,
      '建及为人忠壮，所得赏赐，悉分士卒，与同甘苦，故能得其死力，所向立功；同列疾之。宦者韦令图监建及军，谮于晋王曰：“建及以私财骤施，此其志不小，不可使将牙兵。”王疑之。建及知之，自恃无它，行之自若。',
      [('李建及','分赏士卒而受韦令图指摘者'),('韦令图','监军并向晋王谮李建及者'),('晋王','听韦令图言后起疑者')],
      when='920年三月罢职前；具体年月未载',year=None,place='魏州',
      note='将“建及有异志”记录为韦令图指控，不当作已证事实；其行为背景未定确年。')
event('li_jianji_removed_appointed_daizhou','晋王罢李建及军职，任代州刺史',3,
      '三月，王罢建及军职，以为代州刺史。',
      [('晋王','罢李建及军职并改授代州刺史者'),('李建及','被罢军职并任代州刺史者')],
      when='920年三月；确日未载',place='代州',
      note='任官变动有明示月份；主书未给正式罪名。')

event('yang_dongqian_proposes_schools_exams_selection','杨洞潜请汉设学校、贡举、铨选，汉主采纳',4,
      '汉杨洞潜请立学校，开贡举，设铨选；汉主岩从之。',
      [('杨洞潜','请立学校、开贡举、设铨选者'),('汉主岩','采纳杨洞潜建议的汉主')],
      when='920年三月后、夏四月前本段；确日未载',place='汉',
      note='“从之”证明采纳建议；不据此臆造学校数、考试批次或实施成效。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 5):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明六年第1—4段；金州、安州、庐州查事、李建及任官与汉政制议。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=920,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(1, 5)], next_paragraph=Q[5]['id'],
    coverage='卷271贞明六年第1—4段；蜀克金州、吴安州未克与庐州查事、李建及被罢、汉设贡举之议。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[1]['id'],'note':'全师朗与已录王宗朗同人；919年命讨与920年俘释分开记。'},
      {'paragraph_id':Q[2]['id'],'note':'庐江民控县令是指控；杨廷式主张械系张崇未见实际执行。徐知诰复用李昪。'},
      {'paragraph_id':Q[3]['id'],'note':'李建及最初统牙兵及受谮为追叙，始年未明；三月罢职才定920年。旧书传文独立补其任官。'},
      {'paragraph_id':Q[4]['id'],'note':'“从之”仅证汉主采纳杨洞潜学校、贡举、铨选建议，未记施行结果。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
