"""Curate Tongjian 263, year 903, consecutive paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 16))
primary = 'tongjian-263-902-yearend'
primary_middle = 'tongjian-263-903-wang-shifan'
primary_late = 'tongjian-263-903-fengxiang'
old_five = 'jiuwudaishi-002-903-fengxiang'



B = {'format_version': 1, 'batch_key': 'zztj-v263-y0903-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent.parent / 'year-0902/part-07/sources/library' / primary, '6cba60d', '司马光等'),
    (primary_middle, P / 'sources/library' / primary_middle, 'cb7f7d8', '司马光等'),
    (primary_late, P / 'sources/library' / primary_late, 'cb7f7d8', '司马光等'),
    (old_five, P / 'sources/library' / old_five, 'cb7f7d8', '薛居正等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, primary_middle, primary_late)}
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
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '李继诲':'周承诲', '李彦弼':'董彦弼', '硃友宁':'朱友宁', '侃':'宋侃', '何后':'何氏（唐昭宗皇后）', '景王秘':'李秘', '苏检女':'苏氏（苏检女、景王妃）'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0903_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷263·天复三年（903）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷263天复三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=903):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_263_0903_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '903年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '903年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_263_0903_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_263_0903_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1: first contacts with Zhu Quanzhong's camp.
event('court_sends_cui_guo', '昭宗遣崔构郭遵诲赴朱全忠营',1,
      '春，正月，甲辰，遣殿中侍御史崔构、供奉官郭遵诲诣硃全忠营。',
      [('李杰','遣使者'),('崔构','赴营使者'),('郭遵诲','赴营使者'),('朱温','受使者')],
      when='903年正月甲辰',place='凤翔汴营',
      note='两使赴营不等于和议已成。')
event('maozhen_sends_guo_qiqi', '李茂贞遣郭启期赴汴营议和',1,
      '丙午，李茂贞亦遣牙将郭启期往议和解。',
      [('李茂贞','遣使者'),('郭启期','议和使者'),('朱温','议和对象')],
      when='903年正月丙午',place='凤翔汴营',
      note='“议和解”为磋商，未记成约。')

# 2: Wang Shifan's rising and Liu Xun's seizure of Yanzhou.
event('wang_shifan_responds_to_edict', '王师范见救驾诏及张浚书后决定举兵',2,
      '韩全诲以诏书征籓镇兵入援乘舆，师范见之，泣下沾衿，曰：“吾属为帝室籓屏，岂得坐视天子困辱如此。各拥强兵，但自卫乎！”会张浚自长水亦遗之书，劝举义兵。师范曰：“张公言正会吾意，夫复何疑！',
      [('王师范','决定举兵者'),('韩全诲','发诏征兵者'),('张浚','致书劝兵者')],
      when='903年正月条前后；起意确日未载',place='青州',
      note='忠义等评价与人物引语保留为主书及当事人表述；发诏、致书为起意背景，具体发生日期未载。')
event('wang_shifan_plans_simultaneous_rising', '王师范遣诸将伪装贡使商贩分赴诸州拟同日起兵',2,
      '时关东兵多从全忠在凤翔，师范分遣诸将诈为贡献及商贩，包束兵仗，载以小车，入汴、徐、兗、郓、齐、沂、河南、孟、滑、河中、陕、虢、华等州，期以同日俱发，讨全忠。',
      [('王师范','策划与分遣者'),('朱温','讨伐对象')],
      when='903年正月条；确日未载',place='汴、徐、兗、郓、齐、沂、河南、孟、滑、河中、陕、虢、华',
      note='诸州是计划目标，不建成均已被攻取。')
event('wang_shifan_teams_exposed', '王师范分遣诸州队伍多败露被擒',2,
      '适诸州者多事泄被擒，独行军司马刘鄩取兗州。',
      [('王师范','分遣者'),('刘鄩','唯一成功攻取兗州者')],
      when='903年正月条；确日未载',place='诸州、兗州',
      note='“多”不换算具体人数；刘鄩取兗州另作具体事件。')
event('ge_congzhou_tuns_xingzhou', '葛从周率泰宁军屯邢州，刘鄩探得兗州虚实',2,
      '时泰宁节度使葛从周悉将其屯邢州，鄩先遣人为贩油者入城，诇其虚实及兵所从入。',
      [('葛从周','率军屯邢州者'),('刘鄩','遣人侦察者')],
      when='903年正月丙午前',place='邢州、兗州',
      note='葛从周当时不在兗州城内；侦察人员姓名未载。')
event('liu_xun_takes_yanzhou', '刘鄩丙午率五百精兵从水窦入兗州取军城',2,
      '丙午，鄩将精兵五百夜自水窦入，比明，军城悉定，市人皆不知。',
      [('刘鄩','夺城者')],
      when='903年正月丙午',place='兗州',
      note='葛从周当时率主力屯邢州，非说其本人在城中被俘。')
event('liu_xun_treats_ge_family', '刘鄩据兗州后礼待葛从周母及家属',2,
      '鄩据府舍，拜从周母，每旦省竭；待其妻子，甚有恩礼；子弟职掌、供亿如故。',
      [('刘鄩','礼待者'),('葛从周','家属受礼者')],
      when='903年正月丙午后',place='兗州',
      note='主书“省竭”疑为“省谒”转录问题；保留原字，不据疑字增补具体礼仪。')

# 3–4: Hua Prefecture attempt and the Liang response.
event('zhang_juhou_kills_lou', '张居厚伪装贡使袭华州东城并杀娄敬思',3,
      '是日，青州牙将张居厚帅壮士二百将小车至华州东城，知州事娄敬思疑其有异，剖视之。其徒大呼，杀敬思，攻西城。',
      [('张居厚','率兵袭城者'),('娄敬思','被杀守官')],
      when='903年正月丙午',place='华州东城',
      note='“是日”承上段丙午；旧五代史称牙将张厚，异名另注。')
event('cui_yin_flees_huazhou', '崔胤拒华州来袭军不克，走商州后被追回',3,
      '崔胤在华州，帅众拒之，不克，走至商州，追获之。',
      [('崔胤','拒战失利后被追回者')],
      when='903年正月丙午后',place='华州、商州',
      note='“追获之”宾语承崔胤，未据此记张居厚被捕；后续崔胤仍参与政务。')
event('pei_di_uncovers_wang_plot', '裴迪审问王师范使者获知东方举兵',4,
      '师范遣走卒赍书至大梁，迪问以东方事，走卒色动。迪察其有变，屏人问之，走卒具以实告。',
      [('王师范','遣使者'),('裴迪','审问者')],place='大梁',
      note='使者姓名未载，不建虚构人物。')
event('zhu_youning_eastward', '裴迪请朱友宁率万余人东巡兗郓，召葛从周合攻王师范',4,
      '迪不暇白全忠，亟请马步都指挥使硃友宁将兵万馀人东巡兗、郓。友宁召葛从周于邢州，共攻师范。',
      [('裴迪','请求出兵者'),('硃友宁','东进主将'),('葛从周','被召合攻者'),('王师范','交战对象')],
      place='兗州、郓州、邢州',
      note='裴迪先行部署，随后朱全忠得知并增兵。')
event('zhu_reinforces_eastern_front', '朱全忠闻王师范举兵后分兵先归交朱友宁统领',4,
      '全忠闻变，亦分兵先归，使友宁并将之。',
      [('朱温','分兵者'),('硃友宁','统领援军者')],place='凤翔、东方',
      note='“先归”相对凤翔战线，未推定具体军行路线。')

# 5: court executions and renewed messages to Zhu's camp.
event('maozhen_proposes_execution', '李茂贞戊申独见昭宗并请诛韩全诲等以求和',5,
      '戊申，李茂贞独见上，中尉韩全诲、张彦弘、枢密使袁易简、周敬容皆不得对。茂贞请诛全诲等，与硃全忠和解，奉车驾还京。',
      [('李茂贞','请诛与议和者'),('李杰','会见者'),('韩全诲','拟诛对象'),('张彦弘','未获见者'),('袁易简','未获见者'),('周敬容','未获见者')],
      when='903年正月戊申',place='凤翔',
      note='“请诛”先于执行；李茂贞所提奉车驾还京尚未发生。')
event('han_quanhui_executed', '昭宗命凤翔兵收斩韩全诲等',5,
      '上喜，即遣内养帅凤翔卒四十人收全诲等，斩之。',
      [('李杰','下令者'),('韩全诲','被杀者'),('李茂贞','此前提出诛杀者')],
      when='903年正月戊申',place='凤翔',
      note='四十为奉命收捕的兵数，并非被杀人数；具体被杀者以原文明确姓名为限。')
event('court_replaces_eunuch_posts', '朝廷以第五可范等四人补中尉枢密职',5,
      '以御食使弟五可范为左军中尉，宣徽南院使仇承坦为右军中尉，王知古为上院枢密使，杨虔朗为下院枢密使。',
      [('第五可范','左军中尉受任者'),('仇承坦','右军中尉受任者'),('王知古','上院枢密使受任者'),('杨虔朗','下院枢密使受任者')],
      when='903年正月戊申',place='凤翔',
      note='底本作“弟五可范”，结合复姓第五及旧五代史“第五可范”作规范名；逐字保留底本。')
event('second_fengxiang_executions', '凤翔当夜又斩李继筠等十六人',5,
      '是夕，又斩李继筠、李继诲、李彦弼及内诸司使韦处廷等十六人。',
      [('李继筠','被斩者'),('李继诲','被斩者'),('李彦弼','被斩者'),('韦处廷','被斩者')],
      when='903年正月戊申夜',place='凤翔',
      note='十六人是这一轮“等”人数，未将其与韩全诲等人数相加为精确总数；李继诲、李彦弼沿用既有受赐名稳定人物。')
event('court_sends_han_wo_and_heads', '昭宗遣韩偓赵国夫人及使者向朱全忠示韩全诲等首',5,
      '己酉，遣韩偓及赵国夫人诣全忠营，又遣使囊全诲等二十馀人首以示全忠',
      [('李杰','遣使者'),('韩偓','赴营者'),('赵国夫人','赴营者'),('朱温','受示者'),('韩全诲','被示首者')],
      when='903年正月己酉',place='凤翔汴营',
      note='二十余人为主书所称示首数；旧五代史称三千余，差异另列，不混算。')
event('li_zhen_receives_reply', '朱全忠遣李振辛亥奉表入谢',5,
      '辛亥，全忠遣观察判官李振奉表入谢。',
      [('朱温','遣使者'),('李振','奉表者')],when='903年正月辛亥',place='凤翔')

# 6: the siege remains and Cui Yin is repeatedly recalled.
event('zhu_maintains_siege', '韩全诲等被诛后朱全忠仍围凤翔',6,
      '全诲等已诛，而全忠围犹未解。',
      [('朱温','围城方'),('韩全诲','已诛者')],when='903年正月辛亥后',place='凤翔',
      note='不同于903年后续正式撤围。')
event('maozhen_recalls_cui_yin', '李茂贞请昭宗急召崔胤赴凤翔，崔胤称疾不至',6,
      '茂贞疑崔胤教全忠欲必取凤翔，白上急召胤，令帅百官赴行在。凡四降诏，三赐硃书御札，言甚切至，悉复故官爵，胤竟称疾不至。',
      [('李茂贞','请求急召者'),('李杰','降诏者'),('崔胤','先称疾未至者'),('朱温','受御札者')],
      when='903年正月辛亥后',place='凤翔',
      note='李茂贞之“疑”非崔胤确有密谋的证明；崔胤稍后始来。')
event('cui_yin_comes_after_letters', '李茂贞朱全忠分别致书后崔胤始赴凤翔',6,
      '茂贞惧，自致书于胤，辞甚卑逊。全忠亦以书召胤，且戏之曰：“吾未识天子，须公来辨其是非。”胤始来。',
      [('李茂贞','致书者'),('朱温','致书者'),('崔胤','赴凤翔者')],place='凤翔',
      note='朱全忠信中的戏语为引语，不当作鉴别天子身份的实际程序。')

# 7: Fengxiang gate and renewed confrontation.
event('fengxiang_gate_opens', '凤翔甲寅始开城门',7,'甲寅，凤翔始启城门。',
      [('李茂贞','城内主帅')],when='903年正月甲寅',place='凤翔',
      note='开门不等于昭宗当日出城，车驾出凤翔在后段。')
event('zhu_captures_li_jiqin', '朱全忠丙辰疑凤翔兵逼营，击之俘李继钦',7,
      '丙辰，全忠巡诸寨，至城北，有凤翔兵自北山下，全忠疑其逼己，遣兵击之，擒其将李继钦。',
      [('朱温','遣兵者'),('李继钦','被俘者')],when='903年正月丙辰',place='凤翔城北',
      note='“疑其逼己”为朱全忠判断，不推成凤翔军确已发动攻击。')
event('court_questions_zhu_attack', '昭宗遣赵国夫人冯翊夫人诘问朱全忠，蒋玄晖奉表答奏',7,
      '上遣赵国夫人、冯翊夫人诣全忠营诘其故，全忠遣亲吏蒋玄晖奉表入奏。',
      [('李杰','遣使者'),('赵国夫人','诘问使者'),('冯翊夫人','诘问使者'),('朱温','被诘问者'),('蒋玄晖','奉表者')],
      when='903年正月丙辰后',place='凤翔汴营',
      note='双方互送使者，不推断诘问结果。')

# 8: marriage negotiations and killings.
event('maozhen_proposes_marriages', '李茂贞请以子侃尚平原公主并以苏检女嫁景王',8,
      '李茂贞请以其子侃尚平原公主，又欲以苏检女为景王秘妃以自固。',
      [('李茂贞','提亲者'),('侃','拟尚公主者'),('平原公主','拟婚者'),('苏检','拟婚之女父'),('苏检女','拟嫁者'),('景王秘','拟娶者')],
      place='凤翔',
      note='“请”“欲”均为提议，婚姻实现另记；景王秘按既有李秘识别，需后续纸本核。')
event('empress_he_reluctantly_consents', '何后初难平原公主婚事，昭宗以出凤翔为先而促成',8,
      '平原公主，何后之女也，后意难之。上曰：“且令我得出，何忧尔女！”后乃从之。',
      [('平原公主','被议婚者'),('何后','先迟疑后同意者'),('李杰','劝说者')],place='凤翔',
      note='何后为既有何氏（唐昭宗皇后）；皇帝引语表示当时权衡，未推断公主个人意愿。')
event('song_kan_marries_princess', '宋侃壬戌娶平原公主，景王纳苏氏为妃',8,
      '壬戌，平原公主嫁宋侃。纳景王妃苏氏。',
      [('侃','娶公主者'),('平原公主','出嫁者'),('景王秘','纳妃者'),('苏检女','被纳妃者')],
      when='903年正月壬戌',place='凤翔',
      note='“侃”与同段宋侃为同一人；苏氏由上句苏检女承接，暂用消歧名称。')
event('fengxiang_eunuch_purge_tallies', '凤翔被诛宦官达七十二人，朱全忠又密令京兆杀九十人',8,
      '时凤翔所诛宦官已七十二人，硃全忠又密令京兆搜捕致仕不从行者，诛九十人。',
      [('朱温','密令京兆搜捕者')],when='903年正月壬戌前后',place='凤翔、京兆',
      note='七十二与九十为两地两项史载人数，不与旧五“首级三千余”混算。')

for rel,a,b,kind,n,quote,desc in [
    ('relationship_person_李茂贞_person_宋侃_父亲','李茂贞','宋侃','父亲',8,'李茂贞请以其子侃尚平原公主','李茂贞是宋侃的父亲。'),
    ('relationship_person_何氏（唐昭宗皇后）_person_平原公主_母亲','何氏（唐昭宗皇后）','平原公主','母亲',8,'平原公主，何后之女也','何氏（唐昭宗皇后）是平原公主的母亲。'),
    ('relationship_person_苏检_person_苏氏（苏检女、景王妃）_父亲','苏检','苏氏（苏检女、景王妃）','父亲',8,'苏检女为景王秘妃','苏检是苏氏（景王妃）的父亲。'),
    ('relationship_person_宋侃_person_平原公主_丈夫','宋侃','平原公主','丈夫',8,'平原公主嫁宋侃','宋侃是平原公主的丈夫。'),
]:
    B['person_relationships'].append(dict(key=rel,person_a_key=people[a],person_b_key=people[b],
        relation_type=kind,description=desc,status='draft'))
    claim('person_relationship',rel,'description',desc,n,quote,
          '原文明示亲属或婚姻，按“A是B的关系”单向记载；未外推政治同盟。')

extra(old_five,'event','event_zztj_263_0903_liu_xun_takes_yanzhou','description',
      '《旧五代史》亦记刘鄩袭取兗州。','是日，師範又遣其將劉鄩盜據兗州',2,
      'corroborates','旧五同记兗州得手；“是日”相对其段内丙辰，主书为丙午，具体日干支不强合。')
extra(old_five,'event','event_zztj_263_0903_zhang_juhou_kills_lou','description',
      '《旧五代史》记王师范牙将张厚伪贡袭华州，主书作张居厚。',
      '青州節度使王師範遣牙將張厚輦甲胄弓槊，詐言來獻，欲盜據州城',3,
      'adds','两书记同一华州小车伪贡事，但人名张厚/张居厚异文保留，旧五另称事觉已擒。')
extra(old_five,'event','event_zztj_263_0903_court_sends_han_wo_and_heads','description',
      '《旧五代史》称送韩全诲以下三千余人首级，主书称二十余人。',
      '昭宗遣中使押送軍容使韓全誨已下三千餘人首級以示帝',5,
      'conflicts','人数差距甚大，底本和统计口径待核；旧五此处记丁巳，主书记己酉。')
extra(old_five,'event','event_zztj_263_0903_fengxiang_gate_opens','description',
      '《旧五代史》亦记正月甲寅凤翔启壁。',
      '三年正月甲寅，岐人啟壁',7,
      'corroborates','岐人启壁与主书凤翔启城门相应。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复三年第1—8段：凤翔议和与王师范举兵并行，宦官诛杀及婚姻分录；旧五代史日期、人数、人名异文另注。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=903,
    primary_source_key=primary,primary_source_keys=[primary,primary_middle,primary_late],
    paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],
    coverage='卷263天复三年共15个非空段落中的第1—8段连续处理；本年续在卷263及卷264。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
