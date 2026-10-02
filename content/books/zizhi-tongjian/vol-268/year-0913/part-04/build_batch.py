"""Curate Tongjian 268, year 913, consecutive paragraphs 31-40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 50))
main3 = 'tongjian-268-913-midyear'
main4 = 'tongjian-268-913-autumn'
new_shu = 'xinwudaishi-063-wang-jian-yuanying'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0913-p031-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main3, P.parent / 'part-03/sources/library' / main3, '0c7bdab7', '司马光等'),
    (main4, P / 'sources/library' / main4, 'b8693d0e', '司马光等'),
    (new_shu, P / 'sources/library' / new_shu, 'b8693d0e', '欧阳修'),
]
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
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main3,main4)}
for n in range(31,41):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line']-1]
    assert any(row['text'] in text for text in primary_texts.values()),n

registry = {}
existing_relation_keys = set()
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    archived = json.loads(path.read_text())
    existing_relation_keys.update(row['key'] for row in archived['person_relationships'])
    for row in archived['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (path, row['name'])
        registry[row['name']] = row
aliases = {'吴越王镠':'钱镠','楚王殷':'马殷','蜀主':'王建',
           '王景仁':'王茂章','张宗奭':'张全义','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
aliases.update({'元膺':'王宗懿','蜀主':'王建','帝':'朱友贞','硃友谦':'朱友谦',
                '鄴王':'杨师厚','晋王':'李存勖','守光':'刘守光',
                '行珪':'高行珪','行周':'高行周','嗣源':'李嗣源',
                '存矩':'李存矩','传瓘':'钱传瓘','传璙':'钱传璙',
                '吴越王镠':'钱镠','从珂':'李从珂','魏氏':'魏氏（李从珂母）'})
aliases.update({'刘光浚':'刘光濬','光浚':'刘光濬','李存审':'符存审',
                '王德明':'张文礼','赵王':'王镕','传瓘':'钱传瓘',
                '师厚':'杨师厚','守奇':'刘守奇','万进':'张万进'})
aliases.update({'元膺':'王宗懿','太子':'王宗懿','蜀主':'王建',
                '道袭':'唐道袭','宗翰':'王宗翰','宗侃':'王宗侃',
                '宗贺':'王宗贺','宗黯':'王宗黯','赵王镕':'王镕',
                '晋王':'李存勖','高季兴':'高季昌'})
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main3,main4) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main3,main4):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化三年（913）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0913_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main3,main4):
        book = json.loads((source_dirs[source] / 'paragraph.json').read_text())['book']
        supplements.append(dict(claim_key=ck, source_book=book, primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=supplement_relation))
    return ck

def person(name, n, role, quote):
    name = aliases.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷268乾化三年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=913):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0913_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '913年本段条；确日未载', dynasty='五代十国',
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
          '段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_268_0913_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key,
                                       role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key

def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    if key in existing_relation_keys:
        reused.add(key)
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

event('liushouguang_offers_city', '刘守光向张承业请以幽州城降，遭拒绝', 31,
      '辛卯，燕主守光遣使诣张承业，请以城降。承业以其无信，不许。',
      [('刘守光','遣使请以幽州城投降的燕主'),('张承业','以刘守光无信为由拒绝的晋使')],
      when='913年六月辛卯',place='幽州',
      note='这是请降未被接受，不记幽州已易手。')
event('wang_jian_selects_attendants', '王建命杜光庭选人侍东宫，许寂、徐简夫获荐', 32,
      '蜀主命杜光庭选纯静有德者使侍东宫，光庭荐儒者许寂、徐简夫，太子未尝与之交言，日与乐工群小嬉戏无度，僚属莫敢谏。',
      [('王建','命杜光庭选太子近侍的蜀主'),('杜光庭','推荐许寂、徐简夫的道士'),('许寂','受荐侍东宫的儒者'),('徐简夫','受荐侍东宫的儒者'),('王宗懿','未与两名儒者交言的太子')],
      when='913年前背景追叙；确年未载',place='前蜀东宫',year=None,
      note='“豭喙龅齿”等外貌描写及“狷急猜忍”属史书评价，不建立医学或心理诊断事实；选侍与交往是可拆取的具体行为。')
claim('person',people['王宗懿'],'description',
      '《新五代史》卷六十三称元膺初名宗懿、后名宗坦，亦记杜光庭曾为其师。',32,
      '元膺，建次子也，初名宗懿，後更名宗坦，建得銅牌子于什仿，有文二十餘字，建以為符讖，因取之以名諸子，故又更曰元膺。',
      '新书作宗坦，本站已有通鉴线索作元坦；“宗坦／元坦”待纸本核，主体仍沿王宗懿稳定键。',new_shu,'adds')
event('prince_banquet_absences', '王宗懿七月设宴，王宗翰、潘峭、毛文锡未至', 33,
      '秋，七月，蜀主将以七夕出游。丙午，太子召诸王大臣宴饮，集王宗翰、内枢密使潘峭、翰林学士承旨高阳毛文锡不至，太子怒曰：“集王不来，必峭与文锡离间也。”',
      [('王宗懿','召诸王大臣宴饮并责怪未到者的太子'),('王宗翰','未出席宴会的集王'),('潘峭','未出席宴会的内枢密使'),('毛文锡','未出席宴会的翰林学士承旨')],
      when='913年七月丙午',place='前蜀',
      note='“必峭与文锡离间”是太子指控，不作为二人实际离间的事实。')
event('xu_chang_intimidate_tang', '徐瑶、常谦于宴中示意唐道袭，唐道袭恐惧离席', 33,
      '大昌军使徐瑶、常谦，素为太子所亲信，酒行，屡目少保唐道袭，道袭惧而起。',
      [('徐瑶','宴中屡次目视唐道袭的太子亲信'),('常谦','与徐瑶同在宴中的太子亲信'),('唐道袭','因宴中举动惧而离席的少保')],
      when='913年七月丙午',place='前蜀宴所',
      note='原文“屡目”不明言威胁方式；标题用“示意”概括，未将其解释为已策划刺杀。')
event('prince_accuses_pan_mao', '王宗懿控潘峭、毛文锡离间，王建令贬逐并任潘炕', 33,
      '丁未旦，太子入白蜀主曰：“潘峭、毛文锡离间兄弟。”蜀主怒，命贬逐峭、文锡，以前武泰节度使兼侍中潘炕为内枢密使。',
      [('王宗懿','向王建指控潘峭、毛文锡'),('王建','因太子控诉下令贬逐并任潘炕'),('潘峭','被贬逐的内枢密使'),('毛文锡','被贬逐的翰林学士'),('潘炕','受任内枢密使')],
      when='913年七月丁未晨',place='前蜀宫廷',
      note='“离间兄弟”为王宗懿陈述，史书未证明其真实；贬逐命令另作为王建实际行动。')
event('tang_daoxi_urges_guards', '唐道袭称太子谋乱，王建准召屯营兵宿卫', 33,
      '太子出，道袭入，蜀主以其事告之，道袭曰：“太子谋作乱，欲召诸将、诸王，以兵锢之，然后举事耳。”蜀主疑焉，遂不出；道袭请召屯营兵入宿卫，许之。内外戒严。',
      [('唐道袭','向王建指控太子谋乱并请求召兵'),('王建','生疑并准召屯营兵宿卫')],
      when='913年七月丁未',place='前蜀宫廷',
      note='“太子谋作乱”是唐道袭的指控；只能确定王建准召兵及戒严，不能以此证明先有叛乱计划。')
claim('event','event_zztj_268_0913_tang_daoxi_urges_guards','description',
      '《新五代史》卷六十三亦记唐袭向王建称太子将召兵作乱，随后请求营兵入卫。',33,
      '建以問之，襲曰：「太子謀作亂，欲召諸將、諸王以兵錮之，然後舉事爾！」建疑之，襲請召營兵入衞。',
      '新书作“唐袭”为唐道袭别称；与主书同为当事人指控，不是叛乱计划的独立证实。',new_shu,'corroborates')
event('prince_detains_pan_mao', '王宗懿召兵自卫，扣押潘峭、毛文锡及潘峤', 34,
      '太子初不为备，闻道袭召兵，乃以天武甲士自卫，捕潘峭、毛文锡至，楇之几死，囚诸东宫；又捕成都尹潘峤，囚诸得贤门。',
      [('王宗懿','闻召兵后自卫并拘押三人的太子'),('潘峭','被殴打近死并囚东宫'),('毛文锡','被殴打近死并囚东宫'),('潘峤','被拘囚于得贤门的成都尹')],
      when='913年七月丁未后、戊申前',place='前蜀东宫、得贤门',
      note='“楇之几死”说明殴打严重但三人此时未记死亡；潘峭与潘峤名字相近，分立实体。')
event('prince_forces_kill_tang', '徐瑶、常谦等奉太子攻唐道袭，唐道袭中箭被斩', 34,
      '戊申，徐瑶、常谦与怀胜军使严璘等各帅所部兵奉太子攻道袭。至清风楼，道袭引屯营兵出拒战；道袭中流矢，逐至城西，斩之。杀屯营兵甚众，中外惊扰。',
      [('徐瑶','率部奉太子攻唐道袭'),('常谦','率部奉太子攻唐道袭'),('严璘','率怀胜军参与攻唐道袭'),('王宗懿','为徐瑶等所奉的太子'),('唐道袭','率屯营兵拒战、中流矢并被斩')],
      when='913年七月戊申',place='清风楼、城西',
      note='唐道袭先中流矢后被追斩；原文“杀屯营兵甚众”未给具体人数。')
claim('event','event_zztj_268_0913_prince_forces_kill_tang','description',
      '《新五代史》卷六十三称唐袭与太子兵战于神武门，中流矢坠马而死。',34,
      '召大將徐瑤、常謙率兵出拒襲，與襲戰神武門，襲中流矢，墜馬死。',
      '新书作神武门、坠马死；主书作清风楼至城西、被斩。地点及死亡细节并列待核。',new_shu,'conflicts')
event('pan_kang_counsels_wang', '潘炕向王建称太子只与唐道袭争权', 35,
      '潘炕言于蜀主曰：“太子与唐道袭争权耳，无他志也。陛下宜面谕大臣以安社稷。”',
      [('潘炕','向王建解释太子与唐道袭争权并建议安抚'),('王建','听取潘炕陈述的蜀主')],
      when='913年七月戊申后',place='前蜀宫廷',
      note='“无他志”是潘炕判断，不能据此断定太子确无别的政治意图。')
event('wang_jian_sends_relief', '王建召王宗侃等讨徐瑶、常谦，王宗黯入宫交战', 35,
      '蜀主乃召兼中书令王宗侃、王宗贺、前利州团练使王宗鲁等，使发兵讨为乱者徐瑶、常谦等。宗侃等陈于西球场门，兼侍中王宗黯自大门安梯城而入，与瑶、谦战于会同殿前，杀数十人，馀众皆溃。',
      [('王建','下令讨徐瑶、常谦的蜀主'),('王宗侃','奉命列阵于西球场门'),('王宗贺','奉命参与讨徐瑶、常谦'),('王宗鲁','奉命参与讨徐瑶、常谦'),('王宗黯','自大门入与徐瑶常谦部交战'),('徐瑶','在会同殿前被王宗黯部交战的太子将领'),('常谦','同徐瑶率兵交战')],
      when='913年七月戊申后',place='西球场门、会同殿',
      note='“杀数十人”限于会同殿前交战，未推为整场死亡总数。')
event('xu_yao_dies_prince_flees', '徐瑶战死，常谦与王宗懿匿于龙跃池舰中', 35,
      '瑶死，谦与太子奔龙跃池，匿于舰中。及暮稍定。',
      [('徐瑶','在交战后死亡的太子将领'),('常谦','与太子逃往龙跃池的将领'),('王宗懿','与常谦匿于舰中的太子')],
      when='913年七月戊申暮前',place='龙跃池',
      note='徐瑶死因只据战事上下文，不添加具体杀者；“太子”沿王宗懿。')
event('prince_killed_by_guards', '王宗懿翌日求食后被卫士杀害，王宗翰到时已死', 35,
      '己酉旦，太子出就舟人丐食，舟人以告蜀主，遣集王宗翰往慰抚之；比至，太子已为卫士所杀。',
      [('王宗懿','求食后被卫士杀害的前蜀太子'),('王建','得知太子下落后遣王宗翰慰抚'),('王宗翰','受遣往慰抚，但到达前太子已死')],
      when='913年七月己酉晨',place='龙跃池',
      note='原文明记“卫士所杀”，未具名；王宗翰到时已死，不记其亲手杀太子。')
claim('event','event_zztj_268_0913_prince_killed_by_guards','description',
      '《新五代史》卷六十三亦记王宗翰未至，太子已为卫兵所杀。',35,
      '建遣宗翰招諭之，宗翰未至，為衞兵所殺。',
      '新书与主书都排除王宗翰到场杀太子的直接叙述；不推断卫兵受谁指使。',new_shu,'corroborates')
event('wang_jian_deposes_prince', '王建闻太子死后下诏废王宗懿为庶人并惩办近侍', 35,
      '蜀主疑宗翰杀之，大恸不已。左右恐事变，会张格呈慰谕军民榜，读至“不行斧钺之诛，将误社稷之计”，蜀主收涕曰：“朕何敢以私害公！”于是下诏废太子元膺为庶人。宗翰奏诛手刃太子者，元膺左右坐诛死者数十人，贬窜者甚众。',
      [('王建','怀疑王宗翰、后废太子为庶人并处罚近侍的蜀主'),('王宗翰','被王建怀疑但上奏诛杀行凶卫士的集王'),('张格','呈慰谕军民榜的官员'),('王宗懿','死后被废为庶人的前蜀太子')],
      when='913年七月己酉后',place='前蜀宫廷',
      note='王建“疑”宗翰杀太子只是怀疑；“手刃太子者”未具名；死者数十为元膺左右坐诛人数，不并入宫廷交战死亡。')
event('tang_posthumous_and_pan_restored', '王建追赠唐道袭太师、谥忠壮，潘峭复任枢密使', 36,
      '庚戌，赠唐道袭太师，谥忠壮；复以潘峭为枢密使。',
      [('唐道袭','死后获赠太师、谥忠壮'),('潘峭','复任枢密使'),('王建','作出追赠与复任的前蜀皇帝')],
      when='913年七月庚戌',place='前蜀')
event('li_xin_mozhou', '李信攻下莫州并擒毕元福', 37,
      '甲子，晋五院军使李信拔莫州，擒燕将毕元福。',
      [('李信','率晋军攻莫州并擒毕元福'),('毕元福','莫州失守时被俘的燕将')],
      when='913年七月甲子',place='莫州')
event('li_xin_yingzhou', '李信攻下燕瀛州', 37,
      '八月，乙亥，李信拔瀛州。',
      [('李信','率晋军攻下瀛州')],
      when='913年八月乙亥',place='瀛州')
event('gao_jichang_bohai_wang', '梁赐高季昌勃海王爵', 38,
      '赐高季昌爵勃海王。',
      [('高季昌','获赐勃海王爵的荆南将领')],
      when='913年八月；确日未载',place='后梁',
      note='“勃海”为原文字形，现代常见“渤海”；规范人物名仍用高季昌，亦见高季兴。')
event('jin_zhao_tianchang_meet', '晋王李存勖与赵王王镕会于天长', 39,
      '晋王与赵王镕会于天长。',
      [('李存勖','会赵王于天长的晋王'),('王镕','与晋王会于天长的赵王')],
      when='913年八月；确日未载',place='天长',
      note='只记录会面，不推定新盟约或具体军事决议。')
event('yao_yanzhang_ezhou', '楚将姚彦章水军侵吴鄂州，吕师造未至而楚军退', 40,
      '楚宁远节度使姚彦章将水军侵吴鄂州，吴以池州团练使吕师造为水陆行营应授使，未至，楚兵引去。',
      [('姚彦章','率楚水军侵吴鄂州的宁远节度使'),('吕师造','受吴任命赴援但尚未到达的池州团练使')],
      when='913年八月后、九月前；确日未载',place='鄂州',
      note='吕师造未至而楚兵已退，不能记作吕师造击退楚军；“应授使”为底本字形，官名待核。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(31,41):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化三年六月至九月前第31—40段连续处理；蜀太子案将指控、调兵、交战、死亡及追责拆分；繁简别名统一。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=913,
    primary_source_key=main3,primary_source_keys=[main3,main4],
    paragraphs=[Q[n]['id'] for n in range(31,41)],next_paragraph='zztj-v268-y0913-p041',
    coverage='卷268乾化三年六月至八月第31—40段，前蜀太子王宗懿之死、晋燕幽州攻守及楚吴鄂州边战。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[32]['id'],'note':'太子面貌与性情文字为史书评价；选侍记为事实但发生确年未载。新五代史作宗坦，既有通鉴线索作元坦，待核。'},
      {'paragraph_id':Q[33]['id'],'note':'太子与唐道袭相互指控的动机不作为既成事实；新五代史称唐袭，按同一职任及情节复用唐道袭。'},
      {'paragraph_id':Q[34]['id'],'note':'唐道袭死因：通鉴作清风楼出战、中流矢后城西被斩，新五代史作神武门中流矢坠马死。并列不强并。'},
      {'paragraph_id':Q[35]['id'],'note':'通鉴明称王宗翰未至而太子已被卫士杀；王建后来只是疑其杀人，二者不可倒置。'},
      {'paragraph_id':Q[40]['id'],'note':'吕师造未到鄂州时楚军已退；底本“应授使”官名待校。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
