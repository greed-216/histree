"""Curate Tongjian 266, year 907, consecutive paragraphs 23–30."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 62))
primary = 'tongjian-266-907-early-liang'
khitan = 'tongjian-266-907-khitan'
may = 'tongjian-266-907-may'
new_zhang = 'xinwudaishi-038-zhangchengye'
new_khitan = 'xinwudaishi-072-khitan-treaty'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0907-p023-p030',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-03/sources/library' / primary, '04d95f09', '司马光等'),
    (khitan, P / 'sources/library' / khitan, '8077dd4f', '司马光等'),
    (may, P / 'sources/library' / may, '8077dd4f', '司马光等'),
    (new_zhang, P / 'sources/library' / new_zhang, '8077dd4f', '欧阳修等'),
    (new_khitan, P / 'sources/library' / new_khitan, 'aad58198', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, khitan, may)}
for n in range(23, 31):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '梁王':'朱温', '晋王':'李克用', '吴王镠':'钱镠', '阿保機':'阿保机', '張承業':'张承业'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/year-0907/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0907_04_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷266·开平元年（907）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷266开平元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=907, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_266_0907_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        if key not in {row['key'] for row in B['events']}:
            row = dict(legacy_events[reuse_key], status='draft')
            B['events'].append(row)
        reused.add(key)
        desc = title + '。'
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '907年本段条；确日未载', dynasty='唐', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '907年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_266_0907_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def relation(key, n, quote, note):
    assert quote in Q[n]['text']
    row = legacy_relations[key]
    if key not in {item['key'] for item in B['person_relationships']}:
        B['person_relationships'].append(dict(row, status='draft'))
        reused.add(key)
    claim('person_relationship',key,'description',row['description'],n,quote,note)

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_266_0907_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 23: The sheltering is retrospective; the restored appointment is the current notice.
event('zhang_chengye_restored','晋王复任张承业为监军',23,
      '至是，复以为监军，待之加厚，承业亦为之竭力。',
      when='907年本段条；确日未载',
      note='前句斛律寺匿人属于唐末追叙；本句为复任。',reuse_key='event_0907_zhang_chengye')
claim('event','event_0907_zhang_chengye','description','唐末李克用将张承业藏于斛律寺，以免被诛。',23,
      '晋王匿监军张承业于斛律寺，斩罪人以应诏。',
      '追叙发生时间未在此段确载；不作为907年新事。')
extra(new_zhang,'event','event_0907_zhang_chengye','description',
      '《新五代史》卷三十八亦记李克用藏张承业于斛律寺，后复用为监军。',
      '晉王憐承業，不忍殺，匿之斛律寺。昭宗崩，乃出承業，復為監軍。',23,'corroborates',
      '新史将复任系于昭宗死后；与主书“至是”的叙述时间不同，保留两书写法。')

# 24: Separate the undated camp anecdote from the post-Tang political choice.
event('qi_fu_zhao_anecdote','岐王亲往苻昭家应对告反',24,
      '有告部将苻昭反者，岐王直诣其家，悉去左右，熟寝经宿而还；由是众心悦服。',
      [('李茂贞','被告反后亲赴苻昭家的岐王'),('苻昭','被人告发谋反的部将')],
      when='唐末追叙；确年未载',year=None,
      note='此为治军轶事，无明确年份；不将“告反”确认为苻昭真的谋反。')
event('qi_court','岐王在唐亡后开王府置百官而未称帝',24,
      '及闻唐亡，以兵羸地蹙，不敢称帝，但开岐王府，置百官，名其所居为宫殿，妻称皇后，将吏上书称笺表，鞭、扇、号令多拟帝者。',
      when='907年唐亡后；确日未载',
      note='开府和拟帝仪制不等于正式称帝；原文明确“不敢称帝”。',reuse_key='event_0907_qi_court')

# 25-27: Advice and court appointments.
event('luoyin_advises_qian','罗隐劝钱镠兴兵讨梁，钱镠未采纳',25,
      '镇海节度判官罗隐说吴王镠兴兵讨梁',
      when='907年唐亡后；确日未载',
      note='“虽不能用”明确是未采纳；不推定钱镠实际出兵。',reuse_key='event_0907_luoyin')
claim('event','event_0907_luoyin','description','钱镠虽未采用罗隐建议，仍赞许其态度。',25,
      '虽不能用，心甚义之。','仅记录主书对钱镠态度的叙述。')
event('xue_appointment','薛贻矩任中书侍郎、同平章事',26,
      '五月，丁丑朔，以御史大夫薛贻矩为中书侍郎、同平章事。',
      when='907年五月丁丑朔',
      note='按主书干支纪日，不自行换算公历。',reuse_key='event_0907_xue_pm')
event('hebei_titles','后梁加授王镕、罗绍威、王处直官衔',27,
      '加武顺军节度使赵王王镕宁太师，天雄节度使鄴王罗绍威守太傅，义武节度使王处直兼侍中。',
      when='907年五月丁丑朔后；确日未载',
      note='电子底本“王镕宁太师”疑有讹字，原文照录；不确认具体官衔。',reuse_key='event_0907_hebei_titles')

# 28: Distinguish retrospective Khitan expansion, diplomatic exchange, and the broken pledge.
event('khitan_tribes_consolidated','阿保机逐渐兼并契丹诸部并向外扩张',28,
      '其后阿保机稍以兵击灭七部，复并为一国。又北侵室韦、女真，西取突阙故地，击奚，灭之，复立奚王而使契丹监其兵，东北诸夷皆畏服之。',
      [('阿保机','契丹诸部兼并与扩张的主导者')],
      when='907年以前的追叙；确年未载',year=None,
      note='“其后”“稍”表示持续过程；不把所有征服定于907年。')
event('khitan_embassy','契丹袍笏梅老使梁，梁遣高颀报聘',28,
      '契丹遣其臣袍笏梅老来通好，帝遣太府少卿高颀报之。',
      when='907年五月条；确日未载',
      note='高颀为《通鉴》底本字形；《新五代史》作高頃，未经进一步校勘不据字形另立或合并人物。',
      reuse_key='event_0907_khitan_envoys')
event('jin_khitan_oath','阿保机与晋王李克用在云州东城会盟',28,
      '是岁，阿保机帅众三十万寇云州，晋王与之连和，面会东城，约为兄弟，延之帐中，纵酒，握手尽欢，约以今冬共击梁。',
      [('阿保机','与晋王会面并约共击梁'),('李克用','与阿保机会面并约共击梁')],
      when='907年；约当年冬共击梁',place='云州东城',
      note='“约为兄弟”是本次会盟誓约，后文记背盟；不建永久人物兄弟关系。')
claim('event','event_zztj_266_0907_jin_khitan_oath','description',
      '《通鉴》记阿保机留马三千匹酬晋王赠金缯。',28,
      '阿保机留马三千匹，杂畜万计以酬之。',
      '三千匹为《通鉴》底本数量；《新五代史》作千匹，二说并存。')
event('khitan_breaks_jin_oath','阿保机归后背弃晋王之盟而附梁',28,
      '阿保机既归而背盟，更附于梁，晋王由是而恨之。',
      [('阿保机','背弃会盟而附梁'),('李克用','会盟破裂后的晋王')],
      when='907年会盟后；确日未载',
      note='主书记归后背盟；未给具体日月，不将先前誓约作为持久关系。')
extra(new_khitan,'event','event_zztj_266_0907_jin_khitan_oath','description',
      '《新五代史》亦记阿保机与李克用在云州东城握手约为兄弟、共击梁。',
      '阿保機以兵三十萬會克用於雲州東城。置酒，酒酣，握手約為兄弟。',28,'corroborates',
      '“三十万”为两书所记军数，未据此作现代统计确数。')
extra(new_khitan,'event','event_zztj_266_0907_jin_khitan_oath','description',
      '《新五代史》记阿保机遗晋马千匹，与《通鉴》三千匹不同。',
      '阿保機遺晉馬千匹。',28,'conflicts',
      '数量异文并列保留；不自动折衷。')
extra(new_khitan,'event','event_0907_khitan_envoys','description',
      '《新五代史》记梁遣高頃等报聘，《通鉴》作高颀。',
      '梁遣太府卿高頃、軍將郎公遠等報聘。',28,'conflicts',
      '使臣字形和官衔均有异文；未据自动繁简转换确定同一姓名。')
extra(new_khitan,'event','event_zztj_266_0907_khitan_breaks_jin_oath','description',
      '《新五代史》亦记阿保机归后背约，转遣使聘梁。',
      '既歸而背約，遣使者袍笏梅老聘梁。',28,'corroborates',
      '只印证背约及遣使，不以新史后续“逾年”叙事倒填为907年。')

# 29-30: Southern honors and Jingnan appointment/recovery.
event('southern_titles','后梁授张全义、钱镠、刘隐、王审知封爵官衔',29,
      '己卯，以河南尹兼河阳节度使张全义为魏王；镇海、镇东节度使吴王钱镠为吴越王；加清海节度使刘隐、威武节度使王审知兼侍中，乃以隐为大彭王。',
      when='907年五月己卯',
      note='封爵与加官不直接证明后梁对各节度使辖地的实际控制。',reuse_key='event_0907_southern_titles')
event('gao_jingnan','后梁以高季昌为荆南节度使',30,
      '癸未，以权知荆南留后高季昌为节度使。',
      when='907年五月癸未',
      note='授职的日次明确；后续安集流散人口是逐步过程。',reuse_key='event_0907_gao_jingnan')
claim('event','event_0907_gao_jingnan','description',
      '高季昌到任后安集流散人口，史书记百姓复业。',30,
      '季昌安集流散，民皆复业。',
      '“到官”以后历时未详；不把所有恢复归于五月癸未当日。')
claim('event','event_0907_gao_jingnan','description',
      '《通鉴》记荆南旧统八州，此时仅余江陵。',30,
      '荆南旧统八州，乾符以来，寇乱相继，诸州皆为邻道所据，独馀江陵。',
      '此为领地变迁的概述；未据此推绘精确边界。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(23,31):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平元年第23—30段连续处理；追叙与本年事件分开，契丹马数和使臣姓名异文并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=907,
    primary_source_key=primary,primary_source_keys=[primary,khitan,may],
    paragraphs=[Q[n]['id'] for n in range(23,31)],next_paragraph=Q[31]['id'],
    coverage='卷266开平元年第23—30段连续处理；晋监军、岐府、梁廷任命、契丹会盟与荆南。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
