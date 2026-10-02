"""Curate Tongjian 268, year 913, consecutive paragraphs 11-20."""
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
main2 = 'tongjian-268-913-coup'
old_annals = 'jiuwudaishi-028-jin-yansiege'
old_gao = 'jiuwudaishi-065-gao-xinggui'
old_li = 'jiuwudaishi-035-li-siyuan'
new_yuan = 'xinwudaishi-025-yuan-xingqin'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0913-p011-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main2, P.parent / 'part-01/sources/library' / main2, 'be135c91', '司马光等'),
    (old_annals, P / 'sources/library' / old_annals, '01699c4a', '薛居正等'),
    (old_gao, P / 'sources/library' / old_gao, '01699c4a', '薛居正等'),
    (old_li, P / 'sources/library' / old_li, '01699c4a', '薛居正等'),
    (new_yuan, P / 'sources/library' / new_yuan, '01699c4a', '欧阳修'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main2,)}
for n in range(11,21):
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
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or main2
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source == main2:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化三年（913）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0913_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main2:
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

event('tang_daoxi_returns', '唐道袭复任前蜀枢密使，王宗懿上疏反对', 11,
      '蜀唐道袭自兴元罢归，复为枢密使。太子元膺延疏道袭过恶，以为不应复典机要，蜀主不悦。',
      [('唐道袭','自兴元归来复任枢密使'),('王宗懿','以元膺之名上疏唐道袭过恶的前蜀太子'),('王建','对太子上疏不悦的前蜀皇帝')],
      when='913年二月庚子前；确日未载',place='前蜀',
      note='“元膺”为王宗懿当时名字；“延疏”疑有讹字，保留底本原文；“过恶”为太子指控，不作为已证实事实。')
event('tang_daoxi_taizi_shaobao', '王建授唐道袭太子少保', 11,
      '庚子，以道袭为太子少保。',
      [('唐道袭','受任太子少保'),('王建','任命唐道袭的前蜀皇帝')],
      when='913年二月庚子；月份承前文，未换算公历',place='前蜀',
      note='本段未明言免枢密使，不能据太子少保任命推定两职互斥。')
event('zhou_dewei_takes_lutai', '周德威攻下燕卢台军', 12,
      '三月，甲辰朔，晋周德威拔燕卢台军。',
      [('周德威','率晋军攻下燕卢台军')],when='913年三月甲辰朔',place='卢台军')
claim('event','event_zztj_268_0913_zhou_dewei_takes_lutai','description',
      '《旧五代史》卷二十八亦记晋军三月甲辰收卢台军。',12,
      '三月甲辰朔，收盧台軍。','旧书本纪与通鉴月日一致；旧书未在本句单列周德威。',old_annals,'corroborates')
event('youzhen_renamed_huang', '朱友贞改名锽', 13,
      '丁未，帝更名锽；久之，又名瑱。',
      [('朱友贞','在丁未改名锽的梁帝')],when='913年三月丁未',place='后梁',
      note='“久之，又名瑱”只记后来的异名，原文未给年份，不录作913年另一次改名。')
claim('person',people['朱友贞'],'aliases','朱友贞曾改名锽，后来又名瑱；瑱的确年未载。',13,
      '帝更名锽；久之，又名瑱。','帝承接朱友贞；两次改名时间不同，后一次不可标为913年。')
event('yang_shihou_ye_wang', '朱友贞加杨师厚中书令、封邺王并委政', 14,
      '庚戌，加杨师厚兼中书令，赐爵鄴王，赐语不名，事无巨细必咨而后行。',
      [('杨师厚','获兼中书令、邺王爵并受梁帝倚重'),('朱友贞','授杨师厚官爵的梁帝')],
      when='913年三月庚戌',place='后梁',
      note='底本“鄴”为邺的异体字，规范展示作邺；不推定杨师厚实际独揽全部政务。')
event('zhu_youqian_returns_liang', '朱友谦受梁招抚后复称藩并奉梁年号', 14,
      '帝遣使招抚硃友谦；友谦复称籓，奉梁年号。',
      [('朱友贞','遣使招抚朱友谦的梁帝'),('朱友谦','复称藩并奉梁年号的河中将领')],
      when='913年三月庚戌后；确日未载',place='河中',
      note='“硃”“籓”为底本字形；使者未具名，不另建。')
event('zhu_youjing_kang_wang', '朱友贞封皇弟朱友敬为康王', 15,
      '丙辰，立皇弟友敬为康王。',
      [('朱友贞','册立皇弟的梁帝'),('朱友敬','被封康王的皇弟')],
      when='913年三月丙辰',place='后梁')
relation('朱友贞','朱友敬','兄长',15,'立皇弟友敬为康王。','“皇弟”明确友贞年长；关系方向为朱友贞是朱友敬的兄长。')
event('liu_guangjun_gubeikou', '刘光濬攻下古北口，胡令圭等奔晋', 16,
      '乙丑，晋将刘光濬克古北口，燕居庸关使胡令圭等奔晋。',
      [('刘光濬','率晋军攻下古北口'),('胡令圭','与其他燕将奔晋的居庸关使')],
      when='913年三月乙丑',place='古北口、居庸关',
      note='古北口被攻下与胡令圭等奔晋为同段连续结果；“等”未具名者不另建。')
claim('event','event_zztj_268_0913_liu_guangjun_gubeikou','description',
      '《旧五代史》卷二十八记乙丑收古北口，胡令珪等挈族来奔。',16,
      '乙丑，收古北口。時居庸關使胡令珪等與諸戍將相繼挈族來奔。',
      '旧书“胡令珪”与主书“胡令圭”字形不同，按职务、地点和同日情节视作同一人但保留异文待纸本核。',old_annals,'corroborates')
event('dai_siyuan_baoyi_jiedushi', '戴思远任保义节度使镇邢州', 17,
      '戊辰，以保义留后戴思远为节度使，镇邢州。',
      [('戴思远','由保义留后升节度使并镇邢州')],
      when='913年三月戊辰',place='邢州')

event('liu_shouguang_yuan_xingqin_north', '刘守光遣元行钦率七千骑赴山北募兵', 18,
      '燕主守光命大将元行钦将骑七千，牧马于山北，募北山兵以应契丹；',
      [('刘守光','命元行钦率骑兵山北募兵的燕主'),('元行钦','率七千骑牧马并募兵的燕将')],
      when='913年三月后；确日未载',place='山北',
      note='七千为原文所记骑兵数；“以应契丹”是募兵目的，不记作契丹实际出兵。')
event('gao_xinggui_wuzhou', '刘守光授高行珪武州刺史为外援', 18,
      '又以骑将高行珪为武州刺史，以为外援。',
      [('刘守光','任命高行珪的燕主'),('高行珪','获任武州刺史的燕骑将')],
      when='913年三月后；确日未载',place='武州')
event('li_siyuan_shanhou_eight', '李嗣源取山后八军，李存矩获任新州刺史', 18,
      '晋李嗣源分兵徇山后八军，皆下之；晋王以其弟存矩为新州刺史总之。',
      [('李嗣源','分兵攻取山后八军的晋将'),('李存勖','任命弟李存矩总管的晋王'),('李存矩','获任新州刺史统辖山后八军')],
      when='913年三月后；确日未载',place='山后八军、新州',
      note='“其弟”承晋王李存勖；八军是原文行政军镇数，不折算为兵员。')
event('lu_wenjin_deputy', '晋王以卢文进为裨将', 18,
      '以燕纳降军使卢文进为裨将。',
      [('卢文进','由燕纳降军使获任晋军裨将')],
      when='913年三月后；确日未载',place='山后',
      note='原文省主语，承晋王任命语境；不推定卢文进此前已长期效忠晋。')
event('gao_xinggui_surrenders_wuzhou', '李嗣源进攻武州，高行珪以城降晋', 18,
      '李嗣源进攻武州，高行珪以城降。',
      [('李嗣源','率晋军进攻武州'),('高行珪','以武州城向晋军投降')],
      when='913年三月后；确日未载',place='武州')
claim('event','event_zztj_268_0913_gao_xinggui_surrenders_wuzhou','description',
      '《旧五代史》卷六十五记高行珪降李嗣源。',18,
      '明宗諭以逆順之理，行珪乃降。',
      '旧书后称明宗，所指为此时李嗣源；列传侧重劝降，主书记攻城。',old_gao,'adds')
event('yuan_xingqin_sieges_wuzhou', '元行钦围攻归晋的高行珪，高行周赴晋求援', 18,
      '元行钦闻之，引兵攻行珪，行珪使其弟行周质于晋军以求救，李嗣源引兵救之，行钦解围去。',
      [('元行钦','闻高行珪降晋后围攻武州'),('高行珪','遣弟行周赴晋求援'),('高行周','作为高行珪之弟赴晋军为质求援'),('李嗣源','率晋军救武州迫元行钦解围')],
      when='913年三月后；确日未载',place='武州',
      note='旧五代史卷28作“行温”，卷65作“行周”；两者不直接合并为同一名字，人物按主书及列传暂记高行周，列异文待核。')
relation('高行珪','高行周','兄长',18,'行珪使其弟行周质于晋军以求救，',
         '主书明称行周是行珪之弟；旧书本纪“行温”异文需另核。')
claim('event','event_zztj_268_0913_yuan_xingqin_sieges_wuzhou','description',
      '《旧五代史》卷二十八记高行珪遣弟“行溫”为质；与主书“行周”不同。',18,
      '行珪遣其弟行溫為質，且乞應援。',
      '本纪作行溫；卷六十五列传作行周。保留异文，不另建行温实体，也不以字形转换抹平。',old_annals,'conflicts')
claim('event','event_zztj_268_0913_yuan_xingqin_sieges_wuzhou','description',
      '《旧五代史》卷六十五记高行珪遣弟行周告急，周德威命军援救。',18,
      '行珪遣弟行周告急於周德威，德威命明宗、李嗣本、安金全將兵援之。',
      '列传与主书人名一致；补出周德威下令及李嗣本、安金全参战，未因此增主书人物参与边。',old_gao,'adds')
event('yuan_xingqin_surrenders', '李嗣源与高行周追至广边军，八战后元行钦降晋', 18,
      '嗣源与行周追至广边军，凡八战，行钦力屈而降；嗣源爱其骁勇，养以为子。',
      [('李嗣源','与高行周追击并收元行钦为养子'),('高行周','与李嗣源追击元行钦'),('元行钦','经八战力屈降晋并成为李嗣源养子')],
      when='913年三月后；确日未载',place='广边军',
      note='八战是主书所载，未给具体各战日；养子关系发生在降后。')
relation('李嗣源','元行钦','养父',18,'嗣源爱其骁勇，养以为子。',
         '明确收为养子；关系方向为李嗣源是元行钦的养父。')
claim('event','event_zztj_268_0913_yuan_xingqin_surrenders','description',
      '《新五代史》卷二十五详记八战、双方中箭、元行钦投降并被李嗣源收养。',18,
      '凡八戰，明宗七射中行欽，行欽拔矢而戰，亦射明宗中股。行欽屢敗，乃降。明宗撫其背而飲以酒曰：「壯士也！」因養以為子。',
      '新书为后见叙述；射中次数未入主事件标题，仅在书证补充。',new_yuan,'adds')
claim('event','event_zztj_268_0913_yuan_xingqin_surrenders','description',
      '《旧五代史》卷三十五亦记八战、李嗣源中股和收元行钦。',18,
      '凡八戰，帝控弦發矢七中。行欽酣戰不解，矢亦中帝股，拔矢復戰。行欽窮蹙，面縛乞降，帝酌酒飲之，拊其背曰：「吾子，壯士也！」因厚遇之。',
      '旧书后称帝指李嗣源；与新书相关叙事未计为独立多方确认。',old_li,'corroborates')
event('ruzhou_taken_gao_dai', '李嗣源攻下儒州并任高行珪代州刺史', 18,
      '嗣源进攻儒州，拔之，以行珪为代州刺史。',
      [('李嗣源','率军攻下儒州'),('高行珪','获任代州刺史')],
      when='913年三月后；确日未载',place='儒州、代州',
      note='《旧五代史》卷65作高行珪后任朔州刺史，非代州；各书异文并列，暂不改主书。')
claim('event','event_zztj_268_0913_ruzhou_taken_gao_dai','description',
      '《旧五代史》卷六十五作高行珪“朔州刺史”，与主书“代州刺史”不同。',18,
      '尋以行珪為朔州刺史，','任职州名异文；旧书“寻”表示后续，不保证与通鉴为同一任命。',old_gao,'conflicts')
event('li_xingzhou_and_congke_retinue', '高行周与李从珂分领李嗣源牙兵', 18,
      '行周留事嗣源，常与嗣源假子从珂分将牙兵以从。',
      [('高行周','留事李嗣源并分领牙兵'),('李嗣源','率部出征的晋将'),('李从珂','李嗣源假子并分领牙兵')],
      when='913年前后追叙；具体起讫待考',place='晋军',
      note='“常”是持续状态，不误写成913年某日单次行动。',year=None)
event('li_congke_parentage', '李从珂为魏氏与前夫王氏之子，后来随母入李嗣源家', 18,
      '从珂母魏氏，镇州人，先适王氏，生从珂，嗣源从晋王克用战河北，得魏氏，以为妾，故从珂为嗣源子，及长，以勇健善战知名，嗣源爱之。',
      [('李从珂','魏氏与王氏之子，后随母入李嗣源家'),('魏氏（李从珂母）','镇州人，李从珂生母'),('李嗣源','魏氏后来的夫家，抚养李从珂')],
      when='913年前生平追叙；确年待考',place='镇州、河北',
      note='原文“王氏”未给名，不建单名人物；李嗣源与魏氏结合时间未载，不能定913年。',year=None)
relation('魏氏（李从珂母）','李从珂','母亲',18,'从珂母魏氏，镇州人，先适王氏，生从珂，',
         '明确生母关系；“王氏”是其前夫，未具名。')
relation('李嗣源','李从珂','继父',18,'故从珂为嗣源子，',
         '李从珂先为魏氏与王氏所生，魏氏后为李嗣源妾，因此为继父关系。')

event('wu_attacks_yijin', '吴将李涛率二万兵出千秋岭攻吴越衣锦军', 19,
      '吴行营招讨使李涛帅众二万出千秋岭，攻吴越衣锦军。',
      [('李涛','吴行营招讨使，率军攻衣锦军')],
      when='913年三月后至四月前；确日未载',place='千秋岭、衣锦军',
      note='二万为主书所载兵力，未记战果；与887年杨行密麾下李涛同名且同在吴方，暂沿既有主体，待传记核实。')
event('qian_chuanguan_relief', '钱镠遣钱传瓘援衣锦军，钱传璙水军攻东洲', 19,
      '吴越王镠以其子湖州刺史传瓘为北面应援都指挥使以救之，睦州刺史传璙为招讨收复都指挥使，将水军攻吴东洲以分其兵势。',
      [('钱镠','任命二子分路应对吴军的吴越王'),('钱传瓘','由湖州刺史任北面应援都指挥使援衣锦军'),('钱传璙','由睦州刺史任招讨收复都指挥使率水军攻东洲')],
      when='913年三月后至四月前；确日未载',place='衣锦军、东洲',
      note='传瓘与传璙均为钱镠之子；两路行动目的不同，原文未给胜负。')
relation('钱镠','钱传璙','父亲',19,'吴越王镠以其子湖州刺史传瓘为北面应援都指挥使以救之，睦州刺史传璙为招讨收复都指挥使，',
         '“其子”统领二人，钱镠为钱传璙之父；若既有同向关系则复用。')
event('yuan_xiangxian_zhennan', '袁象先领镇南节度使、同平章事', 20,
      '夏，四月，癸未，以袁象先领镇南节度使、同平章事。',
      [('袁象先','受领镇南节度使及同平章事')],
      when='913年四月癸未',place='镇南')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,21):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化三年三月至四月第11—20段连续处理；繁简规范化，原文不改；行周／行温及代／朔州异文并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=913,
    primary_source_key=main2,primary_source_keys=[main2],
    paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v268-y0913-p021',
    coverage='卷268乾化三年三月至四月第11—20段，前蜀内廷、梁朝任命、晋燕山后攻守与吴越战事。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[11]['id'],'note':'“元膺”是前蜀太子王宗懿之名；“延疏”保留TXT字形，疑讹待纸本校勘。'},
      {'paragraph_id':Q[13]['id'],'note':'朱友贞三月丁未更名锽；“久之，又名瑱”不当作同日或本年改名。'},
      {'paragraph_id':Q[16]['id'],'note':'《旧五代史》卷28作胡令珪，主书作胡令圭，按官职与同日事迹暂对为一人并记异文。'},
      {'paragraph_id':Q[18]['id'],'note':'《旧五代史》卷28作高行温，卷65及主书作高行周；卷65又作高行珪任朔州刺史，主书作代州。异文待核，不自动改字。李从珂身世为追叙，年份留空。'},
      {'paragraph_id':Q[19]['id'],'note':'李涛与887年吴方同名人物暂复用，身份跨26年仍需传记进一步核实。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
