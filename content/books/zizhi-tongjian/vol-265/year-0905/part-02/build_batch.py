"""Curate Tongjian 265, year 905, consecutive paragraphs 7–11."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 61))
primary = 'tongjian-265-905-early'
old_feb = 'jiutangshu-020-905-february'
old_six = 'jiutangshu-175-princes'
new_nine = 'xinwudaishi-001-princes'
new_ezhou = 'xintangshu-190-ezhou'
old_march = 'jiutangshu-020-905-march'
old_names = 'jiutangshu-175-prince-names'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p007-p011',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-01/sources/library' / primary, 'aaf3df65', '司马光等'),
    (old_feb, P / 'sources/library' / old_feb, '91cdc112', '刘昫等'),
    (old_six, P / 'sources/library' / old_six, '91cdc112', '刘昫等'),
    (new_nine, P / 'sources/library' / new_nine, '91cdc112', '欧阳修等'),
    (new_ezhou, P / 'sources/library' / new_ezhou, '91cdc112', '欧阳修等'),
    (old_march, P / 'sources/library' / old_march, '91cdc112', '刘昫等'),
    (old_names, P / 'sources/library' / old_names, 'c13fd201', '刘昫等'),
]
source_dirs = {sk: d for sk, d, _, _ in source_specs}
manifest = []
for sk, d, commit, author in source_specs:
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file=os.path.relpath(d / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary,)}
for n in range(7, 12):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '全昱':'朱全昱', '裕':'李祐', '李裕':'李祐', '李祕':'李秘', '李禛':'李祯', '祕':'李秘', '禛':'李祯', '存':'刘存', '洪':'杜洪', '延祚':'曹延祚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐二年（905）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=905):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0905_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '905年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '905年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0905_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0905_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 7: Retirement and the previously known elder-brother relation are separate.
event('zhu_quanyu_retires', '唐廷以朱全昱为太师并令致仕', 7,
      '戊戌，以安南节度使、同平章事硃全昱为太师，致仕。',
      [('朱全昱','受太师衔并致仕者')], when='905年二月戊戌',
      note='“致仕”为退职；兄长关系已在旧批次登记，不新建重复关系。')
event('zhu_requests_brothers_retirement', '朱全忠曾请罢兄朱全昱所领安南', 7,
      '全昱，全忠之兄也，戆朴无能，先领安南，全忠自请罢之。',
      [('朱温','请罢者'),('朱全昱','被请罢者')],
      when='朱全昱致仕前；确年未载', year=None,
      note='“先领”与“自请”是追叙；“戆朴无能”为主书人物评价，不据此另建事实。')

# 8: Nine named sons in Tongjian; Old Tang biography reports six and a different sequence.
prince_quote = '全忠使蒋玄晖邀昭宗诸子：德王裕、棣王祤、虔王禊、沂王禋、遂王祎、景王祕、祁王祺、雅王禛、琼王祥，置酒九曲池，酒酣，悉缢杀之，投尸池中。'
princes = [('李祐','被害德王，原文称裕'),('李祤','被害棣王'),('李禊','被害虔王'),
           ('李禋','被害沂王'),('李祎','被害遂王'),('李秘','被害景王，原文作祕'),
           ('李祺','被害祁王'),('李祯','被害雅王，本段作禛'),('李祥','被害琼王')]
event('jiuquchi_princes_killed', '朱全忠使蒋玄晖于九曲池杀昭宗九子', 8,
      prince_quote, [('朱温','遣使者'),('蒋玄晖','设宴行杀者'),*princes],
      when='905年二月戊戌社日', place='九曲池',
      note='主书列九人；德王裕沿早年改名记录复用李祐，景王祕复用李秘；雅王禛与898年本地底本祯按同一雅王合并，但逐字字形并列。《旧唐书》列传作六王且置昭宗遇弑之日，不能消去异说。')

# The primary text explicitly calls the princes Zhaozong's sons.
father = person('李杰', 8, '昭宗、九王之父', '昭宗诸子')
son = people['李祐']
rel_key = 'relationship_zztj_265_0905_zhaozong_father_dewang'
B['person_relationships'].append(dict(key=rel_key, person_a_key=father,
    person_b_key=son, relation_type='父亲', description='唐昭宗李杰是德王李祐的父亲。', status='draft'))
claim('person_relationship', rel_key, 'description', '唐昭宗李杰是德王李祐的父亲。', 8,
      '昭宗诸子：德王裕', '德王裕为已录李祐的后用名；其余八王已有昭宗父子关系，不重复建边。')

# 9: Split troop movement, capture, execution and appointment.
event('zhu_sends_cao_ezhou', '朱全忠遣曹延祚率军与杜洪共守鄂州', 9,
      '硃全忠遣其将曹延祚将兵与杜洪共守鄂州',
      [('朱温','遣军者'),('曹延祚','率援兵者'),('杜洪','共守者')],
      when='905年二月庚子前；确日未载', place='鄂州',
      note='只记援守安排，不提前写成守城成功。')
event('liu_cun_takes_ezhou', '刘存庚子攻克鄂州', 9,
      '庚子，淮南将刘存攻拔之', [('刘存','攻拔者'),('杜洪','失城者'),('曹延祚','守城援将')],
      when='905年二月庚子', place='鄂州',
      note='“之”承鄂州；第9段后续另述被俘与处决。')
event('du_cao_executed', '刘存俘杜洪、曹延祚和汴兵千余送广陵处决', 9,
      '执洪、延祚及汴兵千余人送广陵，悉诛之。',
      [('刘存','俘送者'),('杜洪','被俘处决者'),('曹延祚','被俘处决者')],
      when='905年二月庚子后；确日未载', place='广陵',
      note='“千余”是主书记数；不把所有人处决的地点从广陵外推到鄂州。')
event('yang_appoints_liu_ezhou', '杨行密任刘存为鄂岳观察使', 9,
      '行密以存为鄂岳观察使。', [('杨行密','任命者'),('刘存','受任者')],
      when='鄂州攻克后；确日未载', place='鄂岳',
      note='《新唐书》只称刘存守鄂州，职名仍以主书为据。')

# 10–11: Burial and appointment carry precise but disputed annal dates.
event('zhaozong_buried_heling', '唐昭宗己酉葬于和陵，庙号昭宗', 10,
      '己酉，葬圣穆景文孝皇帝于和陵，庙号昭宗。',
      [('李杰','被葬者')], when='905年二月己酉', place='和陵',
      note='谥号与庙号按原文字句保留，不把己酉换算公历日期。')
event('wang_shifan_heyang', '唐廷任王师范为河阳节度使', 11,
      '三月，庚午，以王师范为河阳节度使。',
      [('王师范','受任者')], when='905年三月庚午', place='河阳',
      note='《旧唐书》卷二十下本纪系三月壬戌，干支异说并列。')

extra(old_feb, 'event', 'event_zztj_265_0905_jiuquchi_princes_killed', 'description',
      '《旧唐书》卷二十下记社日九王于九曲池被绞杀。',
      '是月社日，樞密使蔣玄暉宴德王裕已下九王于九曲池，既醉，皆絞殺之', 8, 'corroborates',
      '本纪为九王，仍未逐个列名；本书列传另记六王。')
extra(new_nine, 'event', 'event_zztj_265_0905_jiuquchi_princes_killed', 'time_original',
      '《新五代史》卷一将杀九王系于天祐二年二月。',
      '二年二月，遣蔣玄暉殺德王裕等九王于九曲池。', 8, 'corroborates',
      '只证二月与九王；不以此推定戊戌。')
extra(old_six, 'event', 'event_zztj_265_0905_jiuquchi_princes_killed', 'description',
      '《旧唐书》卷一百七十五列传作德王以下六王，并置昭宗遇弑之日。',
      '昭宗遇弒之日，蔣玄暉於西內置社筵；酒酣，德王已下六王皆為玄暉所殺，投屍九曲池。', 8, 'conflicts',
      '人数、时间与主书及本纪冲突；电子本照录，纸本待核。')
extra(old_names, 'person', people['李祯'], 'description',
      '《旧唐书》卷一百七十五称雅王禛，与本站898年条“祯”为同一雅王的异文候选。',
      '雅王禛、瓊王祥，並光化元年十一月九日封。', 8, 'adds',
      '本书封王名作禛，早年《通鉴》本地TXT作祯；同封号同年可合并主体，仍保留字形差异待纸本校。')
extra(new_ezhou, 'event', 'event_zztj_265_0905_zhu_sends_cao_ezhou', 'description',
      '《新唐书》卷一百九十记朱全忠遣曹延祚率兵援杜洪。',
      '全忠遣曹延祚合吳章兵萬三千救洪。', 9, 'corroborates',
      '新书另述援军合兵数，本批不据其扩写主书兵数。')
extra(new_ezhou, 'event', 'event_zztj_265_0905_du_cao_executed', 'description',
      '《新唐书》卷一百九十亦记杜洪与曹延祚在扬州市被斩。',
      '與延祚皆斬揚州市。', 9, 'corroborates',
      '主书作广陵，书证作扬州；两名称各依原文保留。')
extra(old_feb, 'event', 'event_zztj_265_0905_zhaozong_buried_heling', 'time_original',
      '《旧唐书》卷二十下亦记二月己酉昭宗葬和陵。',
      '己酉，葬昭宗皇帝于和陵。', 10, 'corroborates',
      '只据本句印证葬日与陵名。')
extra(old_march, 'event', 'event_zztj_265_0905_wang_shifan_heyang', 'time_original',
      '《旧唐书》卷二十下将王师范河阳任命系于三月壬戌，与《通鉴》庚午不同。',
      '壬戌，制以前平盧軍節度使、檢校太傅、同平章事、兼青州刺史、上柱國、琅邪郡公、食邑二千五百戶王師範為孟州刺史、河陽三城懷孟節度觀察等使，從全忠奏也。', 11, 'conflicts',
      '同段后文明确王师范为孟州刺史、河阳三城怀孟节度观察使；此摘录仅定位制书起日，详见来源快照。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7, 12):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='卷265天祐二年第7—11段连续处理；九王人数和时间异说并列，雅王祯/禛复用同一主体，鄂州胜败和昭宗葬日各据原文。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=905,
    primary_source_key=primary, primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(7, 12)], next_paragraph=Q[12]['id'],
    coverage='卷265天祐二年第7—11段连续处理；朱全昱致仕、九王被害、鄂州陷落、昭宗葬和陵与王师范转任。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
