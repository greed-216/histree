"""Curate Tongjian 263, year 902, consecutive paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 60))
primary = 'tongjian-263-902-opening'



old_tang = 'jiutangshu-020-902-opening'
old_five = 'jiuwudaishi-002-902-campaign'


B = {'format_version': 1, 'batch_key': 'zztj-v263-y0902-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, '2a58915', '司马光等'),
    (old_tang, P / 'sources/library' / old_tang, '2a58915', '刘昫等'),
    (old_five, P / 'sources/library' / old_five, '2a58915', '薛居正等'),
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
for n in range(1, 9):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'孙德昭', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0902_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷263·天复二年（902）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷263天复二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=902):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_263_0902_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '902年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '902年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_263_0902_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_263_0902_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1–3: fighting draws Zhu away from Fengxiang; court appointments and attempted mediation.
event('zhu_moves_wugong', '朱全忠正月复屯三原并移军武功',1,
      '春，正月，癸丑，硃全忠复屯三原，又移军武功。',
      [('朱温','移军者')],when='902年正月癸丑',place='三原、武功')
event('li_zhou_attack_ci_xi', '李嗣昭周德威攻慈隰以分朱全忠兵势',1,
      '河东将李嗣昭、周德威攻慈、隰，以分全忠兵势。',
      [('李嗣昭','攻慈隰者'),('周德威','攻慈隰者'),('朱温','兵势被牵制者')],
      when='902年正月癸丑条',place='慈州、隰州',
      note='此句只记进攻及目的，攻取两州见第4段，不前置结果。')
event('wei_yifan_chancellor', '韦贻范丁卯任工部侍郎同平章事',2,
      '丁卯，以给事中韦贻范为工部侍郎、同平章事。',
      [('韦贻范','受任者')],when='902年正月丁卯')
event('yan_gui_mediator_and_zhu_surname', '严龟充岐汴和协使并赐朱全忠李姓',3,
      '丙子，以给事中严龟充岐、汴和协使，赐硃全忠姓李，与李茂贞为兄弟，全忠不从。',
      [('严龟','受命和协者'),('朱温','被赐姓而不从者'),('李茂贞','拟结兄弟者')],
      when='902年正月丙子',
      note='朝廷拟赐姓并结兄弟，但朱不从；不改朱温稳定姓名或造已成立的兄弟关系。')
event('maozhen_does_not_fight', '李茂贞此时不出战',3,
      '时茂贞不出战。',
      [('李茂贞','不出战者')],when='902年正月丙子前后',place='凤翔',
      note='限本段阶段，不写全年度未出战。')
event('zhu_returns_hezhong_feb', '朱全忠闻河东兵起二月戊寅回军河中',3,
      '全忠闻有河东兵，二月，戊寅朔，旋军河中。',
      [('朱温','回军者')],when='902年二月戊寅朔',place='河中')

# 4–6: the Puxian campaign, Jianling tomb, and the move at Lizhou.
event('li_sizhao_takes_ci_xi', '李嗣昭等取慈隰并逼晋绛',4,
      '李嗣昭等攻慈、隰，下之，进逼晋、绛。',
      [('李嗣昭','取州并进兵者')],when='902年二月；确日未载',place='慈州、隰州、晋州、绛州',
      note='“等”所指周德威可承前段，但本句不逐列其余将领。')
event('zhu_sends_youning_join_shu', '朱全忠遣侄朱友宁会氏叔琮攻河东军',4,
      '己丑，全忠遣兄子友宁将兵会晋州刺史氏叔琮击之。',
      [('朱温','遣兵者'),('朱友宁','率兵者'),('氏叔琮','会兵者')],
      when='902年二月己丑',place='晋州',
      note='“兄子”明确朱友宁为朱全忠侄；本批先据事件说明，不造不明父名。')
event('jiang_changes_hands', '李嗣昭袭取绛州，康怀英复取',4,
      '李嗣昭袭取绛州，汴将康怀英复取之。',
      [('李嗣昭','先袭取者'),('康怀英','复取者')],
      when='902年二月己丑后',place='绛州',
      note='绛州先归河东后为汴军复取，不能只记一次控制变更。')
event('hedong_camps_puxian', '李嗣昭等屯蒲县',4,
      '嗣昭等屯蒲县。',
      [('李嗣昭','屯军者')],when='902年二月绛州复失后',place='蒲县')
event('shu_breaks_hedong_puxian', '氏叔琮蒲南断归路破河东军',4,
      '乙未，汴军十万营于蒲南，叔琮夜帅众断其归路而攻其垒，破之，杀获万馀人。',
      [('氏叔琮','夜袭破营者')],when='902年二月乙未',place='蒲县南',
      note='十万为主书记汴军营兵数，万余是主书杀获合述，不当作独立核算。')
event('zhu_reaches_jinzhou', '朱全忠己亥自河中赴军并乙巳至晋州',4,
      '己亥，全忠自河中赴之，乙巳，至晋州。',
      [('朱温','赴晋州者')],when='902年二月己亥出发、乙巳到',place='河中、晋州')
event('jianling_tomb_robbed', '简陵被盗掘',5,
      '盗发简陵。',when='902年二月条；确日未载',place='简陵',
      note='盗者未具名，不推具体责任人或被盗物。')
event('li_jizhong_abandons_lizhou', '西川兵至利州，李继忠弃镇奔凤翔',6,
      '西川兵至利州，昭武节度使李继忠弃镇奔凤翔。',
      [('李继忠','弃镇者')],when='902年二月条；确日未载',place='利州、凤翔')
event('wang_jian_appoints_zongwei', '王建以王宗伟为利州制置使',6,
      '王建以剑州刺史王宗伟为利州制置使。',
      [('王建','任命者'),('王宗伟','受任者')],when='902年李继忠弃镇后',place='利州')

# 7–8: the emperor rebukes Wei and the defeat of Hedong troops.
event('emperor_questions_wei_yifan', '昭宗三月宴中质问韦贻范西幸缘由',7,
      '三月，庚戌，上与李茂贞及宰相、学士、中尉、枢密宴，酒酣，茂贞及韩全诲亡去。上问韦贻范：“朕何以巡幸至此？”',
      [('李杰','质问者'),('韦贻范','被问者'),('李茂贞','席间离去者'),('韩全诲','席间离去者')],
      when='902年三月庚戌',place='凤翔',
      note='李茂贞韩全诲离席先于昭宗质问；不推二人因此被定罪。')
event('emperor_rebukes_wei_yifan', '昭宗斥韦贻范答不知，并批其取相非道',7,
      '上曰：“卿何得于朕前妄语云不知？”又曰：“卿既以非道取宰相，当于公事如法，若有不可，必准故事。”',
      [('李杰','斥责者'),('韦贻范','被斥者')],when='902年三月庚戌',
      note='“非道取宰相”为昭宗当面斥语，不作未经复核的独立结论。')
event('wei_yifan_offers_wine', '韦贻范屡以大杯献昭宗并举杯及颐',7,
      '贻范屡以大杯献上，上不即持，贻范举杯直及上颐。',
      [('韦贻范','献杯者'),('李杰','受献者')],when='902年三月庚戌宴',place='凤翔')
event('shu_youning_attack_hedong_camp', '氏叔琮朱友宁戊午进攻河东营',8,
      '戊午，氏叔琮、硃友宁进攻李嗣昭、周德威营。',
      [('氏叔琮','进攻者'),('朱友宁','进攻者'),('李嗣昭','守营者'),('周德威','守营者')],
      when='902年三月戊午',place='河东营')
event('zhou_dewei_retreats', '周德威败后令李嗣昭先退，自率骑兵继退',8,
      '德威出战而败，密令嗣昭以后军先去，德威寻引骑兵亦退。',
      [('周德威','出战失利并掩退者'),('李嗣昭','奉令率后军先退者')],
      when='902年三月戊午',
      note='退军有先后，不写二将同时弃营。')
event('li_tingluan_captured', '汴军追击河东溃军并俘李克用子廷鸾',8,
      '叔琮、友宁长驱乘之，河东军惊溃，禽克用子廷鸾，兵仗辎重委弃略尽。',
      [('氏叔琮','追击者'),('朱友宁','追击者'),('李廷鸾','被俘者'),('李克用','被俘者之父')],
      when='902年三月戊午',
      note='原文仅名廷鸾，李姓由“克用子”明确；被俘不等于被杀。')
rel='relationship_person_li_keyong_person_李廷鸾_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=people['李克用'],person_b_key=people['李廷鸾'],
    relation_type='父亲',description='《资治通鉴》902年条称廷鸾为李克用之子。',status='draft'))
claim('person_relationship',rel,'description','李克用是李廷鸾的父亲。',8,
      '禽克用子廷鸾','主书明示父子，李克用与廷鸾复用同一姓氏。')
event('zhu_orders_attack_hedong', '朱全忠命氏叔琮朱友宁乘胜攻河东',8,
      '硃全忠令叔琮、友宁乘胜遂攻河东。',
      [('朱温','下令者'),('氏叔琮','奉命者'),('朱友宁','奉命者')],
      when='902年三月戊午战后',
      note='本句为命令，太原是否攻下需后段核实。')

extra(old_tang,'event','event_zztj_263_0902_li_zhou_attack_ci_xi','description',
      '《旧唐书》本纪记李克用遣周德威攻慈隰晋。',
      '李克用遣大將周德威攻慈、隰、晉等州',1,'adds',
      '主书首段列李嗣昭周德威、旧唐本纪强调周德威并扩及晋州。')
extra(old_five,'event','event_zztj_263_0902_zhu_returns_hezhong_feb','description',
      '《旧五代史》记朱全忠二月闻晋军南下，遣朱友宁会氏叔琮御之。',
      '二月，聞晉軍大舉南下，聲言來援鳳翔，帝遣硃友甯帥師會晉州刺史氏叔琮以禦之',3,'adds',
      '补出旧五的晋军声言来援凤翔；不据此决定晋军真实动机。')
extra(old_five,'event','event_zztj_263_0902_li_tingluan_captured','description',
      '《旧五代史》亦记三月败晋军、生擒李克用男廷鸾。',
      '三月，友甯、叔琮與晉軍戰于晉州之北，大敗之，生擒克用男廷鸞',8,'corroborates',
      '印证被俘与父子；旧五地作晋州之北，主书本段未列此战地点。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复二年第1—8段：三原武功与河东攻慈隰、韦贻范入相、严龟和协未成、蒲县战事、简陵被盗、利州与三月凤翔宴、李克用子廷鸾被俘。赐朱李姓不从；旧五晋军援凤翔为其声言。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=902,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],
    coverage='天复二年卷263共59个非空段落中的第1—8段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
