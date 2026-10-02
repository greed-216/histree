"""Curate Tongjian 268, year 912, consecutive paragraphs 21-30."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
main1 = 'tongjian-268-912-next'
main2 = 'tongjian-268-912-liyu-continuation'
main3 = 'tongjian-268-912-zhu-death'
new_liyu = 'xinwudaishi-061-liyu'
old_yangtou = 'jiuwudaishi-028-yangtou'
old_longtou = 'jiuwudaishi-056-longtou'
new_longtou = 'xinwudaishi-025-longtou'
old_death = 'jiuwudaishi-007-zhu-death'
new_death = 'xinwudaishi-013-zhu-death'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0912-p021-p030',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-01/sources/library' / main1, '425c28ca', '司马光等'),
    (main2, P / 'sources/library' / main2, '99be897d', '司马光等'),
    (main3, P / 'sources/library' / main3, '99be897d', '司马光等'),
    (new_liyu, YEAR / 'part-02/sources/library' / new_liyu, '3d980bc5', '欧阳修'),
    (old_yangtou, P / 'sources/library' / old_yangtou, '99be897d', '薛居正等'),
    (old_longtou, P / 'sources/library' / old_longtou, '99be897d', '薛居正等'),
    (new_longtou, P / 'sources/library' / new_longtou, '99be897d', '欧阳修'),
    (old_death, P / 'sources/library' / old_death, '99be897d', '薛居正等'),
    (new_death, P / 'sources/library' / new_death, '99be897d', '欧阳修'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main1,main2,main3)}
for n in range(21,31):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line']-1]
    if n != 23:
        assert any(row['text'] in text for text in primary_texts.values()),n
    else:
        head=primary_texts[main1].splitlines()[-1]
        assert row['text']==head+primary_texts[main2].rstrip()

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
           '王景仁':'王茂章','张宗奭':'张全义','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,main2,main3) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,main2,main3):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化二年（912）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0912_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,main2,main3):
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
                   description=f'《资治通鉴》卷268乾化二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=912):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0912_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '912年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_268_0912_' + code + '_' + pk
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

event('longtougang_zhou_captures_shan', '周德威龙头冈生擒单廷珪、击败燕军', 21,
      '燕主守光遣其将单廷珪将精兵万人出战，与周德威遇于龙头冈。',
      [('刘守光','遣单廷珪率燕军出战的燕主'),('单廷珪','率燕军与周德威交战'),('周德威','率晋军迎战单廷珪')],
      when='912年五月；确日未载',place='龙头冈',
      note='主书后文记周德威生擒单廷珪、斩首三千；旧五代史卷28作羊头冈、斩首五千余，卷56与主书近，异说并列。')
event('longtougang_zhou_captures_shan_result', '周德威侧身避枪击落单廷珪，燕军溃败', 21,
      '既战，见德威于陈，援枪单骑逐之，枪及德威背，德威侧身避之，奋楇反击廷珪坠马，生擒，置于军门。燕兵退走，德威引骑乘之，燕兵大败，斩首三千级。',
      [('周德威','避枪反击、生擒单廷珪并追击燕军'),('单廷珪','被周德威击落马后生擒的燕将')],
      when='912年五月；确日未载',place='龙头冈',
      note='斩首三千是《通鉴》所记战果，不把旧史卷28五千余改写为同数。')
claim('event','event_zztj_268_0912_longtougang_zhou_captures_shan_result','description',
      '《旧五代史》卷五十六记龙头岗之战，单廷珪被生擒、斩首三千级。',21,
      '五月七日，劉守光令驍將單廷珪督精甲萬人出戰，德威遇於龍頭崗。初，廷珪謂左右曰：「今日擒周陽五。」既臨陣，見德威，廷珪單騎持槍躬追德威，垂及，德威側身避之，廷珪少退，德威奮楇南墜其馬，生獲廷珪，賊黨大敗，斬首三千級',
      '卷56给出五月七日；同书卷28却作五月乙卯朔、羊头冈、斩首五千余，暂不择一。',old_longtou,'corroborates')
claim('event','event_zztj_268_0912_longtougang_zhou_captures_shan_result','description',
      '《旧五代史》卷二十八另记周德威在羊头冈擒单廷珪，斩首五千余级。',21,
      '五月乙卯朔，周德威大破燕軍於羊頭岡，擒大將單廷珪，斬首五千餘級。',
      '同书卷28与卷56及《通鉴》的战场地名、斩首数和日期不一致，保留为异说。',old_yangtou,'conflicts')
claim('event','event_zztj_268_0912_longtougang_zhou_captures_shan_result','description',
      '《新五代史》卷二十五亦记周德威击落并生擒单廷珪。',21,
      '德威佯走，度廷珪垂及，側身少却，廷珪馬方馳，不可止，縱其少過，奮檛擊之，廷珪墜馬，遂見擒。',
      '新史补充“佯走”等动作，不据以覆盖主书措辞。',new_longtou,'adds')

event('shu_pardon_jichou', '前蜀己丑大赦', 22,
      '己丑，蜀大赦。',
      when='912年五月己丑',place='前蜀',
      note='主书仅记蜀大赦，未说明具体赦令范围。')

event('xu_wen_hostage_liyu_son', '徐温挟李遇幼子至宣州城下劝降', 23,
      '李遇少子为淮南牙将，遇最爱之，徐温执之，至宣州城下示之，其子啼号求生，遇由是不忍战。温使典客何荛入城，以吴王命说之曰：“公本志果反，请斩荛以徇；不然，随荛纳款。”',
      [('李遇','因幼子被挟持而不忍作战的宣州将领'),('徐温','扣押李遇幼子并遣何荛劝降'),('何荛','奉吴王名义入宣州劝李遇投降')],
      when='912年五月；确日未载',place='宣州',
      note='李遇幼子未具姓名，不编造姓名；这一事件的原文跨两个电子分段，本摘录在第一块。')
event('liyu_surrenders_executed', '李遇开门降，徐温命柴再用杀李遇并夷族', 23,
      '遇乃开门请降，温使柴再用斩之，夷其族。于是诸将始畏温，莫敢违其命。',
      [('李遇','开门请降后被斩并夷族'),('徐温','命柴再用杀李遇的吴执政者'),('柴再用','奉徐温命斩李遇')],
      when='912年五月；确日未载',place='宣州',
      note='这是第11段围城的结局；“诸将始畏”是主书叙述，不具体推定个人心态。')
claim('event','event_zztj_268_0912_liyu_surrenders_executed','description',
      '《新五代史》卷六十一也记李遇出城后被杀、家族被诛。',23,
      '溫諷再用伺其出，殺之，并族其家。',
      '新史说温暗示再用伺机杀李遇，主书说直接命令；行动一致而命令形式异。',new_liyu,'corroborates')
event('xu_zhigao_shengzhou', '徐知诰以宣州之功迁升州刺史', 23,
      '徐知诰以功迁升州刺史。知诰事温甚谨，安于劳辱，或通夕不解带，温以是特爱之，',
      [('徐知诰','因宣州事获升州刺史的李昪'),('徐温','任用并赏识徐知诰的吴执政者')],
      when='912年五月；确日未载',place='升州',
      note='本段明确徐知诰，与第11段底本“徐知浩”对校，沿既有李昪稳定实体。')
event('xu_zhigao_recruits_staff', '徐知诰治理升州并征辟宋齐丘等幕僚', 23,
      '知诰在升州，独选用廉吏，修明政教，招延四方士大夫，倾家赀无所爱。洪州进士宋齐丘，好纵横之术，谒知诰，知诰奇之，辟为推官，与判官王令谋、参军王翃专主谋议，以牙吏马仁裕、周宗、曹悰为腹心。',
      [('徐知诰','治理升州、征辟宋齐丘等人的李昪'),('宋齐丘','受辟为推官的洪州进士'),('王令谋','徐知诰幕下判官'),('王翃','徐知诰幕下参军'),('马仁裕','徐知诰腹心牙吏'),('周宗','徐知诰腹心牙吏'),('曹悰','徐知诰腹心牙吏')],
      when='912年五月后；持续治理，确始日未载',place='升州',
      note='“独选廉吏”等带有史家评述，按原文归属；幕僚只按本段明示职位，不推政治结盟。')

event('zhu_wen_near_death', '朱温闰月病危，向近臣忧其子难敌晋王', 24,
      '闰月，壬戌，帝疾增甚，谓近臣曰：“我经营天下三十年，不意太原馀孽更昌炽如此！吾观其志不小，天复夺我年，我死，诸儿非彼敌也，吾无葬地矣！”因哽咽，绝而复苏。',
      [('朱温','闰月壬戌病危并忧梁继承局势的梁帝')],
      when='912年闰月壬戌；底本未注明闰几月',place='洛阳',
      note='“太原馀孽”等是朱温引语，不作为本站评价；“绝而复苏”不是本次死亡。')

event('gao_jichang_fortifies_jiangling', '高季昌扩筑江陵外郭', 25,
      '高季昌潜有据荆南之志，乃奏筑江陵外郭，增广之。',
      [('高季昌','奏请扩大江陵外郭的荆南将领')],
      when='912年闰月前后；确日未载',place='江陵',
      note='“潜有据荆南之志”是主书对意图的记载，实际筑城范围及结果未详。')

event('wang_kai_minister_reassignment', '王锴罢相，改任蜀兵部尚书', 26,
      '丙寅，蜀门下侍郎、同平章事王锴罢为兵部尚书。',
      [('王锴','由前蜀宰相改任兵部尚书')],
      when='912年闰月丙寅',place='前蜀',
      note='“罢”指罢同平章事职，原文未记罪由。')

event('zhu_wen_succession_family', '朱温诸子及养子友文的身份、职任', 27,
      '帝长子郴王友裕早卒。次假子博王友文，帝特爱之，常留守东都，兼建昌宫使。次郢王友珪，其母亳州营倡也，为左右控鹤都指挥使，无宠。次均王友贞，为东都马步都挥指使。',
      [('朱温','诸子及养子友文的梁帝'),('朱友裕','早卒的长子郴王'),('朱友文','受宠的养子博王、东都留守'),('朱友珪','不受宠的郢王、控鹤都指挥使'),('朱友贞','为东都马步都挥指使的均王')],
      when='912年六月前追叙；各职任确始年不定',place='东都、亳州',
      note='本段以“长子”“次假子”等追叙身份，不把诸人出生、封王、友裕死亡定为912年。')

event('zhu_wen_favors_youwen', '朱温欲将后事托朱友文，朱友珪因而不安', 28,
      '友文妇王氏色美，帝尤宠之，虽未以友文为太子，帝意常属之。友珪心不平。友珪尝有过，帝挞之，友珪益不自安。帝疾甚，命王氏召友文于东都，欲与之诀，且付以后事。',
      [('朱温','命王氏召朱友文并欲托付后事的梁帝'),('朱友文','被朱温拟托后事的博王'),('朱友珪','因继承局势不安的郢王'),('王氏（朱友文妻）','受朱温命召夫朱友文的博王妃')],
      when='912年六月事变前；确日未载',place='洛阳、东都',
      note='“意常属之”是史书所记倾向，但尚未正式立朱友文为太子；王氏仅有姓，使用语境限定实体。')
event('zhang_shi_warns_yougui', '张氏告朱友珪传宝之事，二人谋求自保', 28,
      '友珪妇张氏亦朝夕侍帝侧，知之，密告友珪曰：“大家以传国宝付王氏，怀往东都，吾属死无日矣！”夫妇相泣。',
      [('张氏（朱友珪妻）','将宫中消息告朱友珪的郢王妃'),('朱友珪','听妻张氏告知传国宝之事')],
      when='912年六月事变前；确日未载',place='洛阳宫中',
      note='张氏所说“吾属死无日”是其恐惧判断，不写作梁帝已有杀令。')
relation('朱友文','王氏（朱友文妻）','丈夫',28,'友文妇王氏色美',
         '主书明言友文妇王氏，按“朱友文是王氏的丈夫”的方向录入；王氏没有名字，实体名加丈夫限定以免与其他王氏混同。')
relation('朱友珪','张氏（朱友珪妻）','丈夫',28,'友珪妇张氏亦朝夕侍帝侧',
         '主书明言友珪妇张氏，按“朱友珪是张氏的丈夫”的方向录入；张氏没有名字，实体名加丈夫限定。')
event('yougui_laizhou_order', '朱温拟出朱友珪为莱州刺史，朱友珪惧被追赐死', 28,
      '六月，丁丑朔，帝使敬翔出友珪为莱州刺史，即令之官。已宣旨，未行敕。时左迁者多追赐死，友珪益恐。',
      [('朱温','宣旨外放朱友珪为莱州刺史的梁帝'),('敬翔','奉命传达朱友珪外任的梁臣'),('朱友珪','因外放命令与先例而恐惧的郢王')],
      when='912年六月丁丑朔',place='洛阳、莱州',
      note='只宣旨、未行敕；未将朱友珪当作已到任刺史，也无实际赐死令。')
event('yougui_han_qing_coup', '朱友珪与韩勍合谋，率五百牙兵夜入宫', 28,
      '戊寅，友珪易服微行入左龙虎军。见统军韩珪，以情告之。勍亦见功臣宿将多以小过被诛，惧不自保，遂相与合谋。勍以牙兵五百人从友珪杂控鹤士入，伏于禁中，中夜斩关入，至寝殿，侍疾者皆散走。',
      [('朱友珪','改装入左龙虎军并与韩勍合谋的郢王'),('韩珪','率五百牙兵助朱友珪入宫的统军韩勍')],
      when='912年六月戊寅夜',place='洛阳宫中、左龙虎军',
      note='底本先作“韩珪”后作“勍”，《旧五代史》卷七、《新五代史》卷十三均作韩勍；归一已有人物韩勍，保留底本异字。')
event('feng_tinge_kills_zhu_wen', '冯廷谔刺杀朱温，朱友珪秘不发丧', 28,
      '友珪仆夫冯廷谔刺帝腹，刃出于背。友珪自以败氈裹之，瘗于寝殿，秘不发丧。',
      [('冯廷谔','亲手刺杀朱温的朱友珪仆夫'),('朱温','在寝殿被冯廷谔刺杀的梁帝'),('朱友珪','裹尸埋于寝殿并秘丧的主谋')],
      when='912年六月戊寅夜',place='洛阳宫中寝殿',
      note='按主书区分主谋朱友珪与执行刺杀的冯廷谔；不把朱友珪写成亲手持剑者。')
claim('event','event_zztj_268_0912_feng_tinge_kills_zhu_wen','description',
      '《新五代史》卷十三亦记冯廷谔持剑杀朱温，叙述为追刺腹部。',28,
      '友珪親吏馮廷諤以劍犯太祖，太祖旋柱而走，劍擊柱者三，太祖憊，仆于牀，廷諤以劍中之，洞其腹，腸胃皆流。',
      '新史对过程有更多描写；只以共同点支持死亡及执行者，不将细节混合成单一确定场景。',new_death,'adds')
claim('event','event_zztj_268_0912_feng_tinge_kills_zhu_wen','description',
      '《旧五代史》卷七亦记冯廷谔刺朱温、朱友珪匿丧。',28,
      '友珪僕夫馮廷諤刺帝腹，刃出於背。友珪自以敗氈裹之，瘞於寢殿，秘不發喪。',
      '旧史卷七与主书措辞近同，可能共用材料，不作为独立数量证据。',old_death,'corroborates')
event('ding_zhaopu_order_kill_youwen', '朱友珪遣丁昭溥赴东都，命朱友贞杀朱友文', 28,
      '遣供奉官丁昭溥驰诣东都，命均王友贞杀友文。',
      [('朱友珪','遣使下杀朱友文命令的郢王'),('丁昭溥','赴东都传令的供奉官'),('朱友贞','接获杀朱友文命令的均王'),('朱友文','成为朱友珪杀令目标的博王')],
      when='912年六月戊寅后；确时未载',place='洛阳、东都',
      note='本段是杀令，第30段才载友文已死；不提前定执行结果。')

event('yougui_forged_edict', '朱友珪矫诏诬朱友文谋逆并暂掌军国', 29,
      '己卯，矫诏称：“博王友文谋逆，遣兵突入殿中，赖郢王友珪忠孝，将兵诛之，保全朕躬。然疾因震惊，弥致危殆，宜令友珪权主军国之务。”',
      [('朱友珪','矫诏诬朱友文并取得暂掌军国名义'),('朱友文','被伪诏指控谋逆的博王')],
      when='912年六月己卯',place='洛阳',
      note='“友文谋逆”是伪诏内容，不能录为真实谋逆事件或事实。')
event('han_qing_rewards_troops', '韩勍为朱友珪谋，散府库金帛赐军臣', 29,
      '韩勍为友珪谋，多出府库金帛赐诸军及百官以取悦。',
      [('韩勍','建议散赏军臣的朱友珪同谋'),('朱友珪','借赏赐稳定局势的临时执政者')],
      when='912年六月己卯后；确日未载',place='洛阳',
      note='原文“以取悦”是意图记述，不据此推得军臣全部支持。')

event('yougui_accession', '丁昭溥返报朱友文已死，朱友珪发丧即位', 30,
      '辛巳，丁昭溥还，闻友文已死，乃发丧，宣遗制，友珪即皇帝位。',
      [('丁昭溥','返洛阳并传回朱友文死讯的供奉官'),('朱友文','已遇害的博王'),('朱友珪','公开朱温死讯并即位的郢王')],
      when='912年六月辛巳',place='洛阳、东都',
      note='“闻友文已死”只确认此时接获死讯；主书未在此段交代执行者与确切被杀日。')
event('han_jian_killed_xuzhou', '许州张厚兵变杀韩建，朱友珪授张厚陈州刺史', 30,
      '许州军士更相告变，匡国节度使韩建皆不之省，亦不为备。丙申，马步都指挥使张厚作乱，杀建，友珪不敢诘。甲辰，以厚为陈州刺史。',
      [('韩建','在许州兵变中被杀的匡国节度使'),('张厚','兵变杀韩建后获陈州刺史'),('朱友珪','未追究张厚而任其陈州刺史的梁帝')],
      when='912年六月丙申兵变、甲辰任官',place='许州、陈州',
      note='“不敢诘”为主书判断；任官与兵变按先后区分，不推正式赦免文书。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,31):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化二年第21—30段连续处理；龙头冈异说及朱温遇弑不同叙述分源保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=912,
    primary_source_key=main1,primary_source_keys=[main1,main2,main3],
    paragraphs=[Q[n]['id'] for n in range(21,31)],next_paragraph='zztj-v268-y0912-p031',
    coverage='卷268乾化二年五月至六月第21—30段，龙头冈战、宣州李遇之死、朱温遇弑与朱友珪即位。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[21]['id'],'note':'旧五代史卷28作羊头冈、斩首五千余、五月乙卯朔；卷56与通鉴作龙头冈、三千，卷56系五月七日。并列不同卷记载，纸本待核。'},
      {'paragraph_id':Q[23]['id'],'note':'整段跨通鉴电子分段p003186/003187；徐知诰归既有李昪。新五代史对徐温下令杀李遇的方式有不同措辞。'},
      {'paragraph_id':Q[28]['id'],'note':'底本先作韩珪后作勍，与旧新五代史韩勍互校，归入既有韩勍；旧史与通鉴遇弑文字近同，新史另记追刺细节。朱友文被杀待第30段消息。'},
      {'paragraph_id':Q[30]['id'],'note':'本段只明确丁昭溥返报友文已死，未给执行者与确切死日；不得从矫诏“友文谋逆”推出真实谋逆。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
