"""Curate Tongjian 262, year 901, consecutive paragraphs 25–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 56))
primary_prev = 'tongjian-262-901-may-june'
primary = 'tongjian-262-901-aug-oct'

old_tang_spring = 'jiutangshu-020-901-spring'
old_tang_summer = 'jiutangshu-020-901-may-june'


B = {'format_version': 1, 'batch_key': 'zztj-v262-y0901-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent / 'part-03/sources/library' / primary_prev, '8f5b1e1', '司马光等'),
    (primary, P / 'sources/library' / primary, 'ea829ed', '司马光等'),
    (old_tang_spring, P / 'sources/library' / old_tang_spring, 'ea829ed', '刘昫等'),
    (old_tang_summer, P / 'sources/library' / old_tang_summer, 'ea829ed', '刘昫等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_prev, primary)}
for n in range(25, 33):
    assert Q[n]['text'] in ''.join(primary_texts.values()), (n, Q[n]['text'][:30])

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'孙德昭', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and Q[n]['text'] in data)

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0901_04_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·天复元年（901）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷262天复元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=901):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_262_0901_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '901年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '901年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role)
        edge = 'participation_zztj_262_0901_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0901_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 25: restored courtiers and Han Wo's advice, with the damaged tail excluded from inference.
event('linghu_han_promoted', '令狐涣韩偓因参与返正任翰林学士',25,
      '中书舍人令狐涣、给事中韩偓皆预其谋，故擢为翰林学士，数召对，访以机密。',
      [('令狐涣','参与返正并受擢者'),('韩偓','参与返正并受擢者'),('李杰','召对者')],
      when='901年返正后；确日未载',place='京师')
father=person('令狐綯',25,'令狐涣之父')
son=people['令狐涣']
rel='relationship_person_令狐綯_person_令狐涣_父亲'
B['person_relationships'].append(dict(key=rel,person_a_key=father,person_b_key=son,
    relation_type='父亲',description='《资治通鉴》901年条称令狐涣为令狐綯之子。',status='draft'))
claim('person_relationship',rel,'description','令狐綯是令狐涣的父亲。',25,
      '涣，綯之子也。','主书明示父子；按A是B的父亲建立方向。')
event('emperor_relies_on_cui', '昭宗将军国事委崔胤',25,
      '时上悉以军国事委崔胤，每奏事，上与之从容，或至然烛。',
      [('李杰','委事者'),('崔胤','受委奏事者')],when='901年返正后',
      note='“悉以军国事委”是主书概括；不意味着其他官员无权限。')
event('cui_consulted_by_eunuchs', '宦官事无大小先咨崔胤',25,
      '宦官畏之侧目，事无大小，皆咨胤而后行。',
      [('崔胤','被咨者')],when='901年返正后',
      note='不逐名生成宦官；畏之是原书叙述。')
event('han_warns_cui_against_total_purge', '韩偓屡谏崔胤勿尽除宦官，崔不从',25,
      '胤志欲尽除之，韩偓屡谏曰：“事禁太甚。此辈亦不可全无，恐其党迫切，更生他变。”胤不从。',
      [('崔胤','谋尽除且不从者'),('韩偓','劝谏者')],when='901年返正后多次',
      note='“更生他变”为韩偓风险判断，不作后事发生证据。')
event('emperor_asks_han_about_eunuchs', '昭宗丁卯召韩偓问处置宦官',25,
      '丁卯，上独召偓，问曰：“敕使中为恶者如林，何以处之？”',
      [('李杰','发问者'),('韩偓','受问者')],when='901年六月丁卯',
      note='“为恶者如林”是昭宗发问措辞，不逐名或计数。')
event('han_advises_keep_amnesty', '韩偓劝昭宗守返正赦令，择少数恶者依法处置',25,
      '夫人主所重，莫大于信，既下此诏，则守之宜坚。若复戮一人，则人人惧死矣。',
      [('韩偓','进谏者'),('李杰','听谏者')],when='901年六月丁卯',
      note='续文建议明罪处罚少数、安抚余众；这是政策建议，不写朝廷已照办。')
event('emperor_entrusts_han', '昭宗称宦官处置终属韩偓',25,
      '曰：“此事终以属卿。”',
      [('李杰','表示委托者'),('韩偓','受委托者')],when='901年六月丁卯',
      note='原文此句前含疑似转录错乱“?鄙仙钜晕滑”，主语据同段对话承昭宗，需纸本核；不解读乱码。')

# 26–28: river-east counteroffensive, appointments and Sichuan rebellion.
event('li_keyong_sends_yindi', '李克用遣李嗣昭周德威出阴地关',26,
      '李克用遣其将李嗣昭、周德威将兵出阴地关',
      [('李克用','遣兵者'),('李嗣昭','领兵者'),('周德威','领兵者')],
      when='901年六月后；确日未载',place='阴地关')
event('tang_li_surrenders_xi', '李嗣昭周德威攻隰州，刺史唐礼降',26,
      '攻隰州，刺史唐礼降之。',
      [('李嗣昭','攻者'),('周德威','攻者'),('唐礼','降者')],
      when='901年出阴地关后',place='隰州')
event('zhang_gui_surrenders_ci', '河东军进攻慈州，刺史张瑰降',26,
      '进攻慈州，刺史张瑰降之。',
      [('李嗣昭','进攻者'),('周德威','进攻者'),('张瑰','降者')],
      when='901年隰州降后',place='慈州')
event('ding_hui_zhaoyi', '闰月丁会任昭义节度',27,
      '闰月，以河阳节度使丁会为昭义节度使',
      [('丁会','任昭义节度者')],when='901年闰月；主书未明闰几月',place='昭义军',
      note='主书只作闰月；旧唐书明记闰六月，作为独立补证保留。')
event('meng_qian_heyang', '闰月孟迁任河阳节度',27,
      '孟迁为河阳节度使，从硃全忠之请也。',
      [('孟迁','任河阳节度者'),('朱温','奏请者')],
      when='901年闰月；主书未明闰几月',place='河阳')
event('du_congfa_rebellion', '道士杜从法诱三州民作乱',28,
      '道士杜从法以妖妄妄诱昌、普、合三州民作乱',
      [('杜从法','发动者')],when='901年闰月后；确日未载',place='昌州、普州、合州',
      note='“妖妄妄诱”为主书评价，不据此推具体教义。')
event('wang_jian_sends_zongan', '王建遣王宗黯率三万会东川武信兵讨杜从法',28,
      '王建遣行营兵马使王宗黯将兵三万会东川、武信兵讨之。',
      [('王建','遣兵者'),('王宗黯','领兵者'),('杜从法','被讨者')],
      when='901年杜从法作乱后',place='东川、武信',
      note='三万仅指王宗黯所将，不外推会师总兵数。')
claim('person',people['王宗黯'],'aliases','王宗黯即吉谏，为同一人。',28,
      '宗黯，即吉谏也。','主书明示异名，复用既有王宗黯，不新建吉谏。')

# 29: court conflict and the armed appeal to Zhu.
event('cui_requests_eunuch_purge', '崔胤请昭宗尽诛宦官，改用宫人掌内司',29,
      '崔胤请上尽诛宦官，但以宫人掌内诸司事。',
      [('崔胤','请奏者'),('李杰','受请者')],when='901年闰月后；确日未载',
      note='仅为崔胤请求，未写昭宗当即尽诛。')
event('eunuchs_appeal_emperor', '韩全诲等闻谋求哀，昭宗令崔胤改封疏上奏',29,
      '韩全诲等涕泣求哀于上，上乃令胤：“有事封疏以闻，勿口奏。”',
      [('韩全诲','求哀者'),('李杰','令改奏法者'),('崔胤','被令封疏者')],
      when='901年崔胤请诛宦官后',
      note='封疏与口奏程序改变，不等于崔胤被免相。')
event('eunuchs_plant_spies', '宦官以内宫识字女子窃得崔胤密谋',29,
      '宦官求美女知书者数人，内之宫中，阴令诇察其事，尽得胤密谋，上不之觉也。',
      [('崔胤','密谋被探得者'),('李杰','未觉察者')],
      when='901年崔胤改封疏后',place='宫中',
      note='女子未具名，不造人物；主书说昭宗不觉。')
event('eunuchs_plan_remove_cui', '韩全诲等惧而谋去崔胤',29,
      '全诲等大惧，每宴聚，流涕相诀别，日夜谋所以去胤之术。',
      [('韩全诲','谋去崔胤者'),('崔胤','被谋去者')],when='901年密谋泄露后',
      note='谋划不等于已经除去崔胤。')
event('cui_loses_salt_iron_office', '禁军诉冬衣减损，昭宗解崔胤盐铁使',29,
      '全诲等教禁军对上喧噪，诉胤减损冬衣。上不得已，解胤盐铁使。',
      [('韩全诲','教禁军申诉者'),('崔胤','失盐铁使者'),('李杰','解除职务者')],
      when='901年宦官谋去崔胤期间',
      note='冬衣减损是禁军受教所诉，是否实减未据此证实。')
event('zhu_maozhen_compete_emperor', '朱全忠欲昭宗幸东都，李茂贞欲幸凤翔',29,
      '全忠欲上幸东都，茂贞欲上幸凤翔。',
      [('朱温','欲昭宗东迁者'),('李茂贞','欲昭宗赴凤翔者'),('李杰','两方争取之君')],
      when='901年秋前；确日未载',
      note='“欲”是两方意图，未写昭宗已经迁驾。')
event('cui_sends_letter_to_zhu', '崔胤致朱全忠书称奉密诏请兵迎驾',29,
      '遗硃全忠书，称被密诏，令全忠以兵迎车驾',
      [('崔胤','致书自称奉诏者'),('朱温','受书者')],
      when='901年七月甲寅前',
      note='“称被密诏”为崔胤书中说法，不能据此认定真有密诏。')
event('zhu_returns_to_raise_troops', '朱全忠七月甲寅归大梁发兵',29,
      '全忠得书，秋，七月，甲寅，遽归大梁发兵。',
      [('朱温','归大梁发兵者')],when='901年七月甲寅',place='大梁',
      note='此句只写发兵，不预写后来抵京结果。')

# 30–32: Sichuan victory, the August debates and the first Hangzhou movement.
event('wang_zongkan_suppresses_du', '王宗侃等平杜从法之乱',30,
      '西川龙台镇使王宗侃等讨杜从法，平之。',
      [('王宗侃','讨平者'),('杜从法','被平定者')],
      when='901年七月后八月前；确日未载',place='西川',
      note='“等”所指未逐名，不造其他将领。')
event('han_defends_lu_yi', '韩偓向昭宗解释陆扆返正日易服外逃，昭宗止疑',31,
      '至于不乐返正，恐出于谗人之口，愿陛下察之。”上乃止。',
      [('韩偓','为陆扆解释者'),('李杰','停止追问者'),('陆扆','被怀疑者')],
      when='901年八月甲申',
      note='陆扆易服外逃为昭宗听闻与韩偓推测，未据此句定为已证事实；不乐返正被韩偓质疑。')
event('han_quanhui_recruits_commanders', '韩全诲等欲以兵制昭宗，结李继诲李彦弼李继筠',31,
      '韩全诲等惧诛，谋以兵制上，乃与李继昭、李继诲、李彦弼、李继筠深相结，继昭独不肯从。',
      [('韩全诲','谋结兵者'),('孙德昭','被结而不从者'),('周承诲','被结者'),('董彦弼','被结者'),('李继筠','被结者'),('李杰','被谋制者')],
      when='901年八月甲申后',
      note='赐名李继昭=孙德昭，李继诲=周承诲，李彦弼=董彦弼；孙明确不从，不写为共谋。')
event('emperor_asks_han_about_unrest', '昭宗问韩偓外间传闻及内殿和解之议',31,
      '令狐涣欲令朕召崔胤及全诲等于内殿，置酒和解之，何如？',
      [('李杰','问策者'),('韩偓','受问者'),('令狐涣','建议设宴者')],
      when='901年八月甲申后某日',
      note='设宴是令狐涣建议，未写已举行；前述外间传闻仍以韩偓转述。')
event('han_advises_selective_exile', '韩偓建议显罪数人速逐，其余许自新',31,
      '独有显罪数人，速加窜逐，馀者许其自新，庶几可息。',
      [('韩偓','建议者'),('李杰','称善者')],when='901年八月问策时',
      note='建议与昭宗称善不等于已经实施窜逐。')
event('eunuchs_ignore_edicts', '宦官倚党援不遵出监军或守陵敕',31,
      '上或出之使监军，或黜守诸陵，皆不行，上无如之何。',
      [('李杰','下敕却未获执行者')],when='901年八月后',
      note='宦官未逐名，不造受命者；不将未执行的任命写成到任。')
event('rumor_qian_liu_dead', '有人向杨行密报告钱镠被盗杀的传闻',32,
      '或告杨行密云，钱镠为盗所杀。',
      [('杨行密','听闻者'),('钱镠','传闻被杀者')],when='901年八月后；确日未载',
      note='“或告”是传闻，不写钱镠实际死亡。')
event('yang_sends_li_shenfu_hangzhou', '杨行密遣李神福攻取杭州，顾全武列八寨拒敌',32,
      '行密遣步军都指挥使李神福等将兵取杭州，两浙将顾全武等列八寨以拒之。',
      [('杨行密','遣兵者'),('李神福','领兵者'),('顾全武','列寨拒敌者')],
      when='901年获钱镠死讯传闻后',place='杭州',
      note='本段仅记进军和列寨；攻陷杭州、钱镠之死均未发生。')

extra(old_tang_spring,'event','event_zztj_262_0901_cui_sends_letter_to_zhu','description',
      '《旧唐书》本纪概述崔胤与朱全忠相善、双方争取迁驾。',
      '宰相崔胤與朱全忠相善，四人各為表裏',29,'corroborates',
      '只印证政局相近；旧唐此段不载密诏书信，不能为密诏真实性作证。')
extra(old_tang_summer,'event','event_zztj_262_0901_ding_hui_zhaoyi','time_original',
      '《旧唐书》明确任丁会昭义在闰六月辛巳朔；主书只作闰月。',
      '閏六月辛巳朔，制以河陽節度丁會',27,'adds',
      '保留旧唐月日作为补证，不把通鉴原字静改。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,33):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='第25—32段连续校核：韩偓劝谏、隰慈州降、闰月任命、杜从法之乱、崔胤宦官争执与八月京师、杭州传闻。乱码不推事实；李继昭为孙德昭且独不从；钱镠死讯仅是传闻；旧唐赦令日期异记待补前批。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=262,year=901,
    primary_source_key=primary_prev,primary_source_keys=[primary_prev,primary],
    paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],
    coverage='天复元年55段中的第25—32段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
