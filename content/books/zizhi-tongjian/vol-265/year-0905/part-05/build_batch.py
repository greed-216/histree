"""Curate Tongjian 265, year 905, consecutive paragraphs 28–34."""
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
primary_spring = 'tongjian-265-905-spring'
old_exec = 'jiutangshu-020-905-executions'
old_july = 'jiutangshu-020-905-july'
old_aug = 'jiutangshu-020-905-august'
old_sikong = 'jiutangshu-190-sikongtu'
old_campaign = 'jiuwudaishi-002-xiangyang-campaign'
new_wenzhou = 'xintangshu-010-wenzhou'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p028-p034',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_spring, P.parent / 'part-03/sources/library' / primary_spring, 'b7f25c78', '司马光等'),
    (old_exec, P.parent / 'part-04/sources/library' / old_exec, '8a4d4e60', '刘昫等'),
    (old_july, P / 'sources/library' / old_july, '49927098', '刘昫等'),
    (old_aug, P / 'sources/library' / old_aug, '49927098', '刘昫等'),
    (old_sikong, P / 'sources/library' / old_sikong, '49927098', '刘昫等'),
    (old_campaign, P / 'sources/library' / old_campaign, '49927098', '薛居正等'),
    (new_wenzhou, P / 'sources/library' / new_wenzhou, '49927098', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_spring,)}
for n in range(28, 35):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '佶':'卢佶', '图':'司空图', '匡凝':'赵匡凝', '镠':'钱镠', '绍威':'罗绍威'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_05_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_265_0905_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 28: Recall order, Li Yangu's circumstances, and subsequent demotion.
event('court_recalls_absent_officials', '唐廷壬辰敕督遣避乱未入朝官员', 28,
      '时士大夫避乱，多不入朝。壬辰，敕所在州县督遣，无得稽留。',
      when='905年六月壬辰',
      note='原文说地方州县督遣，并未列出每名受督官员。')
event('li_yangu_demoted', '唐廷戊申贬李延古为卫尉寺主簿', 28,
      '前司勋员外郎李延古，德裕之孙也，去官居平泉庄，诏下未至。戊申，责授卫尉寺主簿。',
      [('李延古','被责授卫尉寺主簿者')], when='905年六月戊申', place='平泉庄',
      note='平泉庄为李延古去官所居，非卫尉寺的地点；诏下未至未解释为抗命。')
li_deyu=person('李德裕',28,'李延古祖父','德裕之孙也')
li_yangu=people['李延古']
rel='relationship_zztj_265_0905_li_deyu_grandfather_li_yangu'
B['person_relationships'].append(dict(key=rel,person_a_key=li_deyu,person_b_key=li_yangu,
                                       relation_type='祖父',description='李德裕是李延古的祖父。',status='draft'))
claim('person_relationship',rel,'description','李德裕是李延古的祖父。',28,'李延古，德裕之孙也',
      '“德裕之孙”明示祖孙；李德裕同名身份按人物检索待继续校核。')

# 29: July demotion; Old Tang labels it a further demotion.
event('liu_xun_demoted', '唐廷七月癸亥贬柳逊为曹州司马', 29,
      '秋，七月，癸亥，太子宾客致仕柳逊贬曹州司马。',
      [('柳逊','贬曹州司马者')], when='905年七月癸亥',place='曹州',
      note='《旧唐书》同日作“再贬”，先前致仕处置见前一史段，主书本段不详其前次命令。')

# 30: Weizhou mutiny and separate Shu offensive, with August marker only for the latter.
event('li_gongquan_weizhou_mutiny', '李公佺与天雄牙军谋乱后焚府奔沧州', 30,
      '庚午夜，天雄牙将李公佺与牙军谋乱，罗绍威觉之；公佺焚府舍，剽掠，奔沧州。',
      [('李公佺','谋乱、焚府后逃沧州者'),('罗绍威','察觉谋乱者')],
      when='905年七月庚午夜',place='沧州',
      note='沧州是李公佺逃往地点；谋乱和焚府舍在天雄军府，未推断罗绍威后来如何处置。')
event('wang_jian_attacks_feng_xingxi', '王建遣王宗贺等攻冯行袭于金州', 30,
      '八月，王建遣前山南西道节度使王宗贺等将兵，击昭信节度使冯行袭于金州。',
      [('王建','遣军者'),('王宗贺','领兵进攻者'),('冯行袭','被攻者')],
      when='905年八月；确日未载',place='金州',
      note='只记进攻，不预写战果；前山南西道节度使是王宗贺旧衔。')

# 31: Zhu's stated reasons are assertions; campaign actions are recorded separately.
event('zhu_orders_yang_against_zhao', '朱全忠遣杨师厚讨赵匡凝', 31,
      '硃全忠以赵匡凝东与杨行密交通，西与王建结婚，乙未，遣武宁节度使杨师厚将兵击之',
      [('朱温','遣兵者'),('杨师厚','领兵者'),('赵匡凝','被攻者')],
      when='905年八月乙未',
      note='“交通”“结婚”为史书所述朱全忠用兵理由；未给婚姻双方姓名，不据此新建人物婚姻关系。')
event('zhu_follows_yang_army', '朱全忠己亥率大军继进', 31,
      '己亥，全忠以大军继之。', [('朱温','率大军继进者')],when='905年八月己亥',
      note='“继之”承杨师厚讨赵匡凝；《旧五代史》另记辛未南征，保留日分差异。')

# 32: Wenzhou capture and Zhang Hui's flight.
event('lu_ji_takes_wenzhou', '卢约遣弟卢佶攻陷温州', 32,
      '处州刺史卢约使其弟佶攻陷温州',
      [('卢约','遣军者'),('卢佶','攻陷温州者')],
      when='905年八月本段；确日未载',place='温州',
      note='《新唐书》卷十将卢约陷温州系于905年正月，与主书八月叙事位置不同；其用兵指挥者亦未在新书该句明载。')
rel='relationship_zztj_265_0905_lu_ji_younger_brother_lu_yue'
B['person_relationships'].append(dict(key=rel,person_a_key=people['卢佶'],person_b_key=people['卢约'],
                                       relation_type='弟弟',description='卢佶是卢约的弟弟。',status='draft'))
claim('person_relationship',rel,'description','卢佶是卢约的弟弟。',32,'卢约使其弟佶',
      '“其弟”明示卢佶相对于卢约的弟弟关系。')
event('zhang_hui_flees_fuzhou', '张惠失温州后奔福州', 32,
      '张惠奔福州。', [('张惠','逃往福州者')],
      when='卢佶陷温州后；确日未载',place='福州',
      note='前句记卢佶攻陷温州，此处仅记张惠奔福州，未写具体逃亡路线。')

# 33: Relief order without a recorded outcome.
event('qian_liu_sends_fang_to_wuzhou', '钱镠遣方永珍救婺州', 33,
      '钱镠遣方永珍救婺州。',
      [('钱镠','遣军者'),('方永珍','救援婺州者')],
      when='905年八月本段；确日未载',place='婺州',
      note='本段只有救援动作，无战果；不与前段钱镖救婺州合并为同一人。')

# 34: Retrospective seclusion, summons, deliberate impropriety and release.
event('sikong_tu_retires_wangguan', '司空图弃官居王官谷并屡拒昭宗征召', 34,
      '初，礼部员外郎知制诏司空图弃官居虞乡王官谷，昭宗屡征之，不起。',
      [('司空图','退居王官谷并屡不应征者')],
      when='昭宗在位期间追叙；确年未载',year=None,place='虞乡王官谷',
      note='“初”是追叙，昭宗多次征召未给具体年日，故不硬填905年。')
event('sikong_tu_summoned_and_released', '柳璨征司空图入洛后准其放还山', 34,
      '柳璨以诏书征之，图惧，诣洛阳入见，阳为衰野，坠笏失仪。璨乃复下诏，略曰：“既养高以傲代，类移山以钓名。”又曰：“匪夷匪惠，难居公正之朝。可放还山。”',
      [('柳璨','征召并下诏放还者'),('司空图','入见后获放还者')],
      when='905年八月本段；旧唐书系壬寅放还',place='洛阳',
      note='“阳为”意为佯作；《旧唐书》本纪八月壬寅放还中条山，传记记入见坠笏失仪。')

extra(old_exec,'event','event_zztj_265_0905_court_recalls_absent_officials','description',
      '《旧唐书》卷二十下亦记壬辰敕遣朝官赴阙。',
      '新除朝官、前資朝官，敕到後三日內發遣赴闕',28,'corroborates',
      '旧书限定新除和前资朝官，记敕到三日内；主书概述士大夫避乱。')
extra(old_exec,'event','event_zztj_265_0905_li_yangu_demoted','description',
      '《旧唐书》卷二十下戊申敕李延古责授卫尉寺主簿。',
      '戊申，敕前司勳員外郎、賜緋魚袋李延古責授衛尉寺主簿',28,'corroborates',
      '只证责授官职，祖孙和去官居平泉庄仍据《通鉴》。')
extra(old_july,'event','event_zztj_265_0905_liu_xun_demoted','description',
      '《旧唐书》卷二十下癸亥记柳逊再贬曹州司马。',
      '癸亥，再貶柳遜曹州司馬',29,'corroborates',
      '“再贬”提示此前已有处置；不凭此补造未录命令。')
extra(old_campaign,'event','event_zztj_265_0905_zhu_orders_yang_against_zhao','time_original',
      '《旧五代史》卷二记庚午杨师厚率前军攻赵匡凝；《通鉴》乙未。',
      '庚午，遣大將軍楊師厚率前軍討趙匡凝於襄州',31,'conflicts',
      '两书记日不同，未擅自换算或修正。')
extra(old_aug,'event','event_zztj_265_0905_zhu_orders_yang_against_zhao','description',
      '《旧唐书》卷二十下亦载乙未杨师厚讨赵匡凝。',
      '是月乙未，全忠遣大將楊師厚討匡凝',31,'corroborates',
      '该摘录承八月丁亥朔，不扩大为原书所有军事细节。')
extra(new_wenzhou,'event','event_zztj_265_0905_lu_ji_takes_wenzhou','time_original',
      '《新唐书》卷十记天祐二年正月卢约陷温州；《通鉴》置于八月叙事。',
      '二年正月，盧約陷溫州',32,'conflicts',
      '新书未写卢佶，也不证具体执行者；月份异说待核。')
extra(old_aug,'event','event_zztj_265_0905_sikong_tu_summoned_and_released','time_original',
      '《旧唐书》卷二十下系司空图放还于八月壬寅。',
      '壬寅，敕：「前太中大夫、尚書兵部侍郎、賜紫金魚袋司空圖',34,'adds',
      '其后敕文至“宜放還中條山”；摘录这里只证该敕壬寅起日。')
extra(old_sikong,'event','event_zztj_265_0905_sikong_tu_summoned_and_released','description',
      '《旧唐书》卷一百九十下记司空图入洛、坠笏失仪并被放还。',
      '圖懼見誅，力疾至洛陽，謁見之日，墮笏失儀',34,'corroborates',
      '传记支持入见细节，放还敕文另见同段后文。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(28,35):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐二年第28—34段连续处理；追叙时日未定，卢约取温州月份异说及朱全忠出兵日分并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=905,
    primary_source_key=primary_spring,primary_source_keys=[primary_spring],
    paragraphs=[Q[n]['id'] for n in range(28,35)],next_paragraph=Q[35]['id'],
    coverage='卷265天祐二年第28—34段连续处理；官员督遣与责贬、魏州兵变、蜀攻金州、襄阳战事发端、温婺州与司空图。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
