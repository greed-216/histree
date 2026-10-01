"""Curate Tongjian 262, year 901, consecutive paragraphs 33–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 54))
primary_prev = 'tongjian-262-901-aug-oct'
primary = 'tongjian-262-901-oct-transition'
primary_nov = 'tongjian-262-901-nov'

old_tang_oct = 'jiutangshu-020-901-oct'
old_tang_nov = 'jiutangshu-020-901-nov'


B = {'format_version': 1, 'batch_key': 'zztj-v262-y0901-p033-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent / 'part-04/sources/library' / primary_prev, 'ea829ed', '司马光等'),
    (primary, P / 'sources/library' / primary, '207dc44', '司马光等'),
    (primary_nov, P / 'sources/library' / primary_nov, '207dc44', '司马光等'),
    (old_tang_oct, P / 'sources/library' / old_tang_oct, '207dc44', '刘昫等'),
    (old_tang_nov, P / 'sources/library' / old_tang_nov, '207dc44', '刘昫等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_prev, primary, primary_nov)}
for n in range(33, 41):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/262.txt').read_text().splitlines()[Q[n]['source_line']-1], n

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
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_262_0901_05_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷262·天复元年（901）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷262天复元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
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
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_262_0901_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_262_0901_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 33: September deliberation. A damaged phrase separates two recorded speeches.
event('emperor_requests_joint_action', '昭宗九月召韩偓，请崔胤促朱全忠李茂贞协同行动',33,
      '九月，癸丑，上急召韩偓，谓曰：“闻全忠欲来除君侧之恶，大是尽忠，然须令与茂贞共其功。若两帅交争，则事危矣。卿为我语崔胤，速飞书两镇，使相与合谋，则善矣。',
      [('李杰','召韩偓并提出协同行动者'),('韩偓','受命传话者'),('崔胤','拟被传话者'),('朱温','昭宗所述欲来者'),('李茂贞','昭宗拟协同者')],
      when='901年九月癸丑',
      note='“闻全忠欲来”“大是尽忠”为昭宗所闻和判断；协同是请求，未写两镇已经合作。引文之后底本有疑损字。')
event('emperor_complains_guard_commanders', '昭宗向韩偓抱怨李继诲李彦弼等禁中骄横',33,
      '上又谓偓曰：“继诲、彦弼辈骄横益甚，累日前与继筠同入，辄于殿东令小儿歌以侑酒，令人惊骇。”',
      [('李杰','抱怨者'),('韩偓','听闻者'),('周承诲','昭宗指称骄横者'),('董彦弼','昭宗指称骄横者'),('李继筠','被昭宗说同入者')],
      when='901年九月癸丑对话时',place='宫中殿东',
      note='李继诲=周承诲、李彦弼=董彦弼；行为是昭宗口述，不把具体发生日定为癸丑。')
event('han_warns_guard_eunuch_union', '韩偓警告宦官与宿卫兵相结将使汴岐兵相斗',33,
      '崔胤本留卫兵，欲以制敕使也，今敕使、卫兵相与为一，将若之何！汴兵若来，必与岐兵斗于阙下，臣窃寒心。',
      [('韩偓','警告者'),('李杰','听谏者'),('崔胤','先前留卫兵者')],when='901年九月癸丑',
      note='汴岐兵将斗是韩偓预测，不写此时已在阙下交战。')

# 34–35: October march and the Hangzhou battle.
event('zhu_marches_daliang_oct', '朱全忠十月戊戌率大军离大梁',34,
      '冬，十月，戊戌，硃全忠大举兵发大梁。',
      [('朱温','率军出发者')],when='901年十月戊戌',place='大梁')
event('li_shenfu_feigns_retreat', '李神福佯退杭州战线并设青山伏兵',35,
      '神福谓诸将曰：“杭兵尚强，我师且当夜还。”杭俘走告全武，神福命勿追，暮遣羸兵先行，神福为殿，使行营都尉吕师造伏兵青山下。',
      [('李神福','设计佯退者'),('吕师造','设伏者'),('顾全武','获佯退消息者')],
      when='901年十月杭州战事期间',place='杭州青山附近',
      note='段首“神福?窈挤枿使出入卧内”疑损，不解释；退军系诱敌谋划，不写淮南军当时已撤。')
event('li_shenfu_captures_gu', '李神福吕师造夹击顾全武并生擒之',35,
      '全武素轻神福，出兵追之。神福、师造夹击，大破之，斩首五千级，生擒全武。',
      [('李神福','夹击者'),('吕师造','夹击者'),('顾全武','被击败生擒者')],
      when='901年十月杭州战事期间',place='青山附近',
      note='斩首五千是主书数字，非现代独立统计；顾全武被生擒未被杀。')
event('qian_liu_laments_gu_capture', '钱镠闻顾全武被俘而悲叹',35,
      '钱镠闻之，惊泣曰：“丧我良将！”',
      [('钱镠','闻讯悲叹者'),('顾全武','被指良将者')],
      when='901年顾全武被俘后',
      note='“丧我良将”为钱镠叹语，顾全武原文为生擒而非死亡。')
event('qin_chang_surrenders_linan', '李神福进攻临安，秦昶率三千人降',35,
      '神福进攻临安，两浙将秦昶帅众三千降之。',
      [('李神福','进攻者'),('秦昶','率众降者')],
      when='901年顾全武被俘后',place='临安',
      note='三千为秦昶率领之众；不写已攻下临安城。')

# 36: October court coercion, dated measures, and Zhu's eastern-capital petition.
event('han_orders_emperor_to_fengxiang', '韩全诲丁酉令李继诲李彦弼勒兵逼昭宗幸凤翔',36,
      '韩全诲闻硃全忠将至，丁酉，令李继诲、李彦弼等勒兵劫上，请幸凤翔，宫禁诸门皆增兵防守，人及文书出入搜阅甚严。',
      [('韩全诲','令勒兵者'),('周承诲','奉令勒兵者'),('董彦弼','奉令勒兵者'),('李杰','受胁者')],
      when='901年十月丁酉',place='京师宫禁',
      note='此时勒兵并请西幸，尚未记实际出京；赐名将领复用既有主体。')
event('emperor_secret_letter_to_cui', '昭宗密赐崔胤御札称势须西行',36,
      '上遣人密赐崔胤御札，言皆凄怆，末云：“我为宗社大计，势须西行，卿等但东行也。惆怅！惆怅！”',
      [('李杰','密札者'),('崔胤','受札者')],when='901年十月丁酉后',
      note='“势须西行”是昭宗札中表达，不写他已离京。')
event('zhao_guofuren_conveys_emperor', '赵国夫人转昭宗话称李彦弼无礼且君后涕泣',36,
      '戊戌，上遣赵国夫人出语韩偓：“朝来彦弼辈无礼极甚，欲召卿对，其势未可。”且言：“上与皇后但涕泣相同。”',
      [('李杰','遣传话者'),('赵国夫人','转述者'),('韩偓','受话者'),('董彦弼','被指无礼者'),('何氏（唐昭宗皇后）','被述与帝涕泣者')],
      when='901年十月戊戌',
      note='赵国夫人仅有封号，未据此补姓名；无礼是所转昭宗话。')
event('han_quanhui_revokes_january_edict', '韩全诲等癸卯迫昭宗寝正月敕，并侍侧议政',36,
      '癸卯，全诲等令上入阁召百官，迫寝正月丙午敕书，悉如咸通以来近例。是日，开延英，全诲等即侍侧，同议政事。',
      [('韩全诲','迫寝敕并侍议者'),('李杰','被迫寝敕者')],when='901年十月癸卯',place='延英殿',
      note='正月丙午敕是前批限制宦官侍侧奏事的敕，不将其误作当日新诏。')
event('li_jiyun_loots_treasury', '李继筠丁未遣部兵掠内库',36,
      '丁未，神策都指挥使李继筠遣部兵掠内库宝货、帷帐、法物',
      [('李继筠','遣兵掠内库者')],when='901年十月丁未',place='京师内库')
event('han_sends_royals_ahead', '韩全诲密送诸王宫人先赴凤翔',36,
      '韩全诲遣人密送诸王、宫人先之凤翔。',
      [('韩全诲','密遣者')],when='901年十月丁未后',place='凤翔',
      note='诸王宫人未逐名；先行与昭宗本人出京不同。')
event('zhu_reaches_hezhong_petitions_luoyang', '朱全忠戊申至河中表请昭宗幸东都',36,
      '戊申，硃全忠至河中，表请车驾幸东都，京城大骇，士民亡窜山谷。',
      [('朱温','到河中并表请者'),('李杰','被请迁都者')],
      when='901年十月戊申',place='河中',
      note='表请幸东都不等于昭宗已答允；百姓避乱是主书所记反应。')

# 37: November encirclement and surrender at Tongzhou.
event('li_jiyun_blocks_palace', '李继筠十一月朔勒兵阙下禁人出入',37,
      '十一月，己酉朔，李继筠等勒兵阙下，禁人出入，诸军大掠。',
      [('李继筠','勒兵者')],when='901年十一月己酉朔',place='京师阙下',
      note='诸军大掠不全归李继筠一部；街民衣纸布襦反映乱状。')
event('han_jian_names_sima_ye', '韩建令司马鄴知匡国留后',37,
      '韩建以幕僚司马鄴知匡国留后。',
      [('韩建','委任者'),('司马鄴','知留后者')],when='901年十一月己酉朔条',place='匡国军')
event('sima_ye_surrenders_tongzhou', '朱全忠以四镇兵七万趋同州，司马鄴迎降',37,
      '硃全忠引四镇兵七万趣同州，鄴迎降。',
      [('朱温','率兵七万者'),('司马鄴','迎降者')],when='901年十一月己酉朔后',place='同州',
      note='七万系主书所记四镇兵数；旧唐本纪记同州壬子陷、司马鄴被执，叙法不同。')

# 38: the forced westward move. Represent accusations as claims of speakers.
event('han_blocks_sun_from_emperor', '韩全诲因孙德昭不从而阻其见昭宗',38,
      '韩全诲等以李继昭不与之同，遏绝不令见上。',
      [('韩全诲','阻见者'),('孙德昭','被阻见者'),('李杰','被阻其见者')],
      when='901年十一月己酉后',
      note='李继昭是孙德昭；此句明确不与韩同，勿误列劫驾同谋。')
event('sun_guards_cui_residence', '孙德昭率六十余人及关东驻京兵守崔胤宅',38,
      '继昭帅所部六十馀人及关东诸道兵在京师者共守卫之。百官及士民避乱者，皆往依之。',
      [('孙德昭','守卫者'),('崔胤','受守卫者')],
      when='901年十一月京师乱时',place='开化坊',
      note='六十余仅是孙所部人数，关东诸道兵另列，不合计推总数。')
event('court_officials_refuse_summons', '昭宗庚戌召百官，崔胤等表辞不至',38,
      '庚戌，上遣供奉官张绍孙召百官，崔胤等皆表辞不至。',
      [('李杰','遣召者'),('张绍孙','传召者'),('崔胤','表辞者')],
      when='901年十一月庚戌',place='京师')
event('han_claims_zhu_wants_usurpation', '韩全诲壬子陈兵并称朱全忠欲劫昭宗赴洛传禅',38,
      '壬子，韩全诲等陈兵殿前，言于上曰：“全忠以大兵逼京师，欲劫天子幸洛阳，求传禅。',
      [('韩全诲','陈兵并指称者'),('李杰','受胁听闻者'),('朱温','被指称者')],
      when='901年十一月壬子',place='京师殿前',
      note='劫往洛阳求传禅是韩全诲的指控，不作朱当时已实施传禅的事实。')
event('han_forces_emperor_down_tower', '昭宗拒幸凤翔登乞巧楼，韩全诲等迫其下楼',38,
      '上不许，杖剑登乞巧楼。全诲等逼上下楼',
      [('李杰','拒请而登楼者'),('韩全诲','逼下楼者')],
      when='901年十一月壬子',place='乞巧楼')
event('dong_yanbi_fires_palace', '董彦弼于御院纵火',38,
      '上行才及寿春殿，李彦弼已于御院纵火。',
      [('董彦弼','纵火者'),('李杰','离院者')],
      when='901年十一月壬子',place='御院',
      note='李彦弼=董彦弼；纵火发生于昭宗到寿春殿时。')
event('emperor_forced_to_hu', '昭宗携后妃诸王被迫出京，当夕宿鄠县',38,
      '不得已，与皇后、妃嫔、诸王百馀人皆上马，恸哭声不绝，出门，回顾禁中，火已赫然。是夕，宿鄠县。',
      [('李杰','被迫西行者'),('何氏（唐昭宗皇后）','随行皇后')],
      when='901年十一月壬子；是夕宿鄠县',place='京师至鄠县',
      note='百余人为后妃诸王等合叙，未逐名；“不得已”表被迫，非昭宗自愿巡幸。')

# 39–40: western movement and Han Jian's surrender.
event('zhu_threatens_han_jian', '朱全忠遣司马鄴入华州责韩建',39,
      '硃全忠遣司马鄴入华州，谓韩建曰：“公不早知过自归，又烦此军少留城下矣。”',
      [('朱温','遣责者'),('司马鄴','传话者'),('韩建','受责者')],
      when='901年十一月壬子后',place='华州',
      note='传话是施压，未记华州已被攻陷。')
event('han_jian_surrenders_gifts_silver', '韩建遣李巨川请降并献银三万两',39,
      '韩建遣节度副使李巨川请降，献银三万两助军，全忠乃西南趣赤水。',
      [('韩建','请降献银者'),('李巨川','奉命请降者'),('朱温','受降者')],
      when='901年十一月壬子后',place='华州、赤水',
      note='银三万两为主书所记献军数量；旧唐本纪也记李巨川送款。')
event('li_maozhen_meets_emperor', '李茂贞癸丑于田家硙迎昭宗',40,
      '癸丑，李茂贞迎车驾于田家硙，上下马慰接之。',
      [('李茂贞','迎驾者'),('李杰','受迎者')],
      when='901年十一月癸丑',place='田家硙')
event('emperor_reaches_zhouzhi', '昭宗甲寅至盩厔并乙卯留一日',40,
      '甲寅，车驾至盩厔；乙卯，留一日。',
      [('李杰','车驾西行者')],
      when='901年十一月甲寅至、乙卯留',place='盩厔',
      note='两日顺序明确，未写此时已至凤翔。')

extra(old_tang_oct,'event','event_zztj_262_0901_zhu_marches_daliang_oct','description',
      '《旧唐书》本纪亦记十月戊戌朱全忠引四镇兵出动，另记七万兵。',
      '戊戌，全忠引四鎮之師七萬赴河中',34,'adds',
      '印证日次；七万是旧唐此处兵数，主书第34段未载兵数。')
extra(old_tang_nov,'event','event_zztj_262_0901_sima_ye_surrenders_tongzhou','description',
      '《旧唐书》作十一月壬子汴军陷同州并执司马鄴；《通鉴》记司马鄴迎降。',
      '是日，汴軍陷同州，執州將司馬鄴',37,'conflicts',
      '陷城被执与迎降叙法有异，保持两书说法；不可静改为同一种归降方式。')
extra(old_tang_nov,'event','event_zztj_262_0901_han_jian_surrenders_gifts_silver','description',
      '《旧唐书》本纪记韩建遣李巨川送款，与主书请降相应。',
      '華州節度使韓建遣判官李巨川送款',39,'corroborates',
      '旧唐未在此句列银三万两，不拿它印证银数。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,41):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='第33—40段连续校核：昭宗与韩偓对话、朱十月发兵、杭州伏击、京师兵逼与西幸、韩建请降及李茂贞迎驾。疑损字不释；朱求传禅为韩全诲指控；李继昭=孙德昭且不从；旧唐司马鄴被执与主书迎降异说并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=262,year=901,
    primary_source_key=primary_prev,primary_source_keys=[primary_prev,primary,primary_nov],
    paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph=Q[41]['id'],
    coverage='天复元年53段中的第33—40段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
