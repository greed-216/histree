# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 1–6."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 68))
specs=[
 ('tongjian-275-926-palace-and-taiyuan',P/'sources/library/tongjian-275-926-palace-and-taiyuan','60d249b7','司马光等'),
 ('tongjian-275-926-regency',P/'sources/library/tongjian-275-926-regency','60d249b7','司马光等'),
 ('jiuwudaishi-034-926-cunxu-death',P/'sources/library/jiuwudaishi-034-926-cunxu-death','60d249b7','薛居正等'),
 ('jiuwudaishi-035-926-arrival',P/'sources/library/jiuwudaishi-035-926-arrival','60d249b7','薛居正等'),
 ('jiuwudaishi-035-926-regency',P/'sources/library/jiuwudaishi-035-926-regency','60d249b7','薛居正等'),
 ('xinwudaishi-006-926-regency',P/'sources/library/xinwudaishi-006-926-regency','60d249b7','欧阳修'),
 ('xinwudaishi-037-926-palace-mutiny',P/'sources/library/xinwudaishi-037-926-palace-mutiny','60d249b7','欧阳修'),
 ('xinwudaishi-028-926-zhangxian',P/'sources/library/xinwudaishi-028-926-zhangxian','60d249b7','欧阳修'),
 ('songshi-255-926-wangquanbin',P/'sources/library/songshi-255-926-wangquanbin','60d249b7','脱脱等'),
 ('songshi-263-926-zhangzhao-name',P/'sources/library/songshi-263-926-zhangzhao-name','60d249b7','脱脱等'),
 ('songshi-263-926-zhangzhao-petition',P/'sources/library/songshi-263-926-zhangzhao-petition','60d249b7','脱脱等'),
 ('xinwudaishi-014-924-consort-titles',P/'sources/library/xinwudaishi-014-924-consort-titles','60d249b7','欧阳修'),
 ('jiuwudaishi-038-928-fuyanchao-surname',P/'sources/library/jiuwudaishi-038-928-fuyanchao-surname','60d249b7','薛居正等'),
 ('jiuwudaishi-051-926-cunwo',P/'sources/library/jiuwudaishi-051-926-cunwo','0a0ea078','薛居正等'),
 ('xinwudaishi-025-cunshen-final',ROOT/'content/books/zizhi-tongjian/vol-273/year-0924/part-04/sources/library/xinwudaishi-025-cunshen-final','4ab203a5','欧阳修'),
 ('jiuwudaishi-074-926-kang-capture',ROOT/'content/books/zizhi-tongjian/vol-274/year-0926/part-03/sources/library/jiuwudaishi-074-926-kang-capture','8ecc7ee3','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p001-p006',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
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
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/275.txt').read_text().splitlines()
for n in range(1, 7):
    assert Q[n]['text'] == lines[Q[n]['source_line'] - 1]
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷275·同光四年（926）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_275_0926_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李存勖','上':'李存勖','庄宗':'李存勖','嗣源':'李嗣源','李绍荣':'元行钦','李绍琛':'康延孝','继岌':'李继岌','存霸':'李存霸','存屋':'李存渥','存确':'李存确','存纪':'李存纪','存乂':'李存乂','刘后':'刘夫人（李存勖妻）','硃守殷':'朱守殷','李彦卿':'符彦卿','李彦超':'符彦超','存审':'符存审','善友':'善友（庄宗鹰坊人）','张昭远':'张昭（五代宋初）','淑妃':'韩夫人（李存勖正妃）','德妃':'伊氏（李存勖德妃）'}
NEW_ALIASES={'符彦卿':['符彥卿','李彦卿','李彥卿'],'符彦超':['符彥超','李彦超','李彥超'],'何福进':['何福進'],'王全斌':[],'善友（庄宗鹰坊人）':['善友（莊宗鷹坊人）'],'侯益':[],'伊氏（李存勖德妃）':['伊德妃'],'张昭（五代宋初）':['张昭远','張昭遠'],'李存沼':[],'吕内养（晋阳）':['呂內養（晉陽）'],'郑内养（晋阳）':['鄭內養（晉陽）']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=926 if name in ['李存沼','吕内养（晋阳）','郑内养（晋阳）'] else None,description=f'《资治通鉴》卷275同光四年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='926年本段；确日未载', note='', year=926, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_275_0926_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_275_0926_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{next(x["name"] for x in B["people"] if x["key"]==pk)}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。',source=source)
    return key

def relationship(a,b,kind,n,quote,note,source=None):
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
    a=next(x['name'] for x in B['people'] if x['key']==pa); b=next(x['name'] for x in B['people'] if x['key']==pb)
    matches={}
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_275_0926_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('cunxu_prepares_departure_and_guo_revolts','庄宗准备东行，郭从谦率部与黄甲两军攻兴教门',1,'夏，四月','攻兴教门。',[('帝','严办将发的皇帝'),('郭从谦','从马直指挥使、率部作乱者'),('存乂','郭不知已死、拟拥立的睦王')],when='926年夏四月丁亥朔据主书',place='洛阳宣仁门、五凤门、兴教门',note='不知睦王已死、欲奉为郭的认知与意图，非存乂复生或实际即位；此处帝准备发，未已出城。')
claim('event',E,'description','新郭从谦传记从谦攻兴教门，与黄甲军相射；与主同攻的叙法不同。',1,'莊宗入食內殿，從謙自營中露刃注矢，馳攻興教門，與黃甲軍相射。','不把新相射静默改为联合作乱，分别保留双方关系叙法。',source='xinwudaishi-037-926-palace-mutiny',relation='conflicts')
E=ev('cunxu_repels_first_palace_attack','庄宗率诸王和近卫骑兵击退乱兵，召朱守殷助击但朱未至',1,'帝方食','茂林之下。',[('帝','率近卫击乱、急召援军者'),('硃守殷','将骑在外、未赴召而驻北邙者')],when='926年四月丁亥朔初攻兴教门时',place='洛阳宫门、北邙',note='主不至并驻北邙，不外推秘密参与郭叛；中使无名不补姓名。')
E=ev('palace_gate_burned_guards_fight','乱兵焚门登城，近臣宿将多遁，符彦卿、何福进、王全斌等十余人力战',1,'乱兵焚兴教门','十馀人力战。',[('李彦卿','散员都指挥使、力战者'),('何福进','宿卫军校、力战者'),('王全斌','宿卫军校、力战者')],when='926年四月丁亥朔乱兵再攻时',place='洛阳兴教门及宫城',note='主李彦卿按父符存审与宋同宫变同王全斌校符彦卿，不因李/符异姓新建重复人；皆释甲为书载概括，与明确留战者并录。')
claim('event',E,'description','宋王全斌传同记近臣宿将弃甲，王全斌与符彦卿等十数人拒战。',1,'同光末，國有內難，兵入宮城，近臣宿將皆棄甲遁去，惟全斌與符彥卿等十數人居中拒戰。','同宫城事件、同参与者辨主李彦卿为符彦卿；宋未提何福进不据此否定。',source='songshi-255-926-wangquanbin',relation='corroborates')
relationship('存审','李彦卿','父亲',1,'彦卿，存审之子；','存审即符存审，是符彦卿生父；原主李彦卿名与新列子、宋同守卫补证合核。')
claim('person',people['符彦卿'],'description','新符存审传列其子彦超、彦饶、彦卿。',1,'存審三子：彥超、彥饒、彥卿。','这里只取姓名亲属匹配；三子为本传所列，不扩写成全部仅有三子。',source='xinwudaishi-025-cunshen-final',relation='adds')
E=ev('cunxu_wounded_and_dies','庄宗中流矢，善友扶至绛霄庑下，刘后遣人进酪，庄宗随后死亡',1,'俄而帝','须臾，帝殂。',[('帝','中箭后死亡者'),('善友','鹰坊人、扶帝者'),('刘后','未亲临、遣人进酪者')],when='926年四月丁亥朔据主书；旧庄宗纪丁丑朔、亭午',place='洛阳宫城绛霄庑下',note='主流矢不擅定射手、进酪不推毒杀；善友只名未载姓，不与早年振武戍将石善友合并。')
claim('person',people['李存勖'],'death_year','李存勖于926年宫城兵变中中箭后死亡。',1,span(1,'俄而帝','须臾，帝殂。'),'主月日与旧异文并存，不因死后本纪谥号改变既有人物。')
claim('event',E,'time_original','旧庄宗纪置四月丁丑朔，记亭午崩；新郭传与主记丁亥朔。',1,'四月丁丑朔，以永王存霸為北都留守，申王存渥為河中節度使。','旧同段是日承此朔日，丁丑/丁亥异文保留未核纸本；此引文仅定位，不新录两留守任命。',source='jiuwudaishi-034-926-cunxu-death',relation='conflicts')
claim('event',E,'description','旧庄宗纪记中流矢、亭午崩于绛霄殿廡下，年四十三。',1,'俄而帝為流矢所中，亭午，崩於絳霄殿之廡下，時年四十三。','原年龄为书说，不据虚实岁自行倒推出生年。',source='jiuwudaishi-034-926-cunxu-death',relation='adds')
claim('event',E,'description','新郭传记乱兵从楼上射帝、伤重踣绛霄廊下、午时崩。',1,'亂兵從樓上射帝，帝傷重，踣于絳霄殿廊下，自皇后、諸王左右皆奔走。至午時，帝崩，','此书补射箭方位与伤重，主未具射手，仍不指定郭亲射。',source='xinwudaishi-037-926-palace-mutiny',relation='adds')
E=ev('shanyou_cremates_cunxu_with_instruments','庄宗死后近侍散去，善友收乐器覆盖尸体焚烧',1,'李彦卿等恸哭','覆帝尸而焚之。',[('李彦卿','恸哭离去者'),('善友','收乐器焚尸者'),('帝','被焚遗体之人')],when='926年四月丁亥朔庄宗死后',place='绛霄庑下',note='焚尸与庄宗中矢死分动作；不推善友是杀帝者或宗教火葬礼主持。')
claim('event',E,'description','旧庄宗纪也记五坊人善友以乐器簇尸焚之，明宗入洛仅得燼骨。',1,'是時，帝之左右例皆奔散，唯五坊人善友斂廓下樂器簇於帝屍之上，發火焚之。及明宗入洛，止得其燼骨而已。','五坊与鹰坊为各书职称，不为此补姓；后得骨用于同事件补证。',source='jiuwudaishi-034-926-cunxu-death',relation='corroborates')
E=ev('liu_cunwo_yuan_flee_palace','刘后携金宝与李存渥、元行钦率七百骑焚喜庆殿，经师子门出逃',1,'刘后囊金宝','自师子门出走。',[('刘后','携财出逃者'),('存屋','申王、同逃者'),('李绍荣','同逃将领')],when='926年四月丁亥朔宫乱后',place='洛阳喜庆殿、师子门',note='主存屋据同申王与旧宗室传同刘后奔太原校李存渥，原屋保留；七百为书载同逃骑兵，不造个人财额。')
claim('person',people['李存渥'],'description','旧宗室传记申王名存渥，校主存屋字形。',1,'申王存渥，莊宗第四弟，','同申王、同庄宗败后刘后出奔辨同人；第四弟为书说，未另建长幼关系。',source='jiuwudaishi-051-926-cunwo',relation='adds')
claim('event',E,'description','旧宗室传记申王存渥在庄宗败后与刘皇后同奔太原。',1,'莊宗敗，與劉皇后同奔太原','只取共同出逃以核同人，后文被杀待主后段处理，不写为本次出宫已死。',source='jiuwudaishi-051-926-cunwo',relation='corroborates')
E=ev('cunque_cunji_flee_south_mountain','李存确、李存纪逃往南山',1,'通王存确','雅王存纪奔南山。',[('存确','通王、出逃者'),('存纪','雅王、出逃者')],when='926年四月丁亥朔宫乱后',place='洛阳南山',note='此时只逃未死，下文后段谋杀不得提前写。')
E=ev('zhushouyin_takes_palace_women_city_plundered','宫人逃散，朱守殷入宫选三十余宫人携乐器珍玩归家，诸军大掠都城',1,'宫人多逃散','于是诸军大掠都城。',[('硃守殷','入宫取宫人珍玩者')],when='926年四月丁亥朔宫乱后',place='洛阳宫城、朱守殷家及都城',note='明确取人财与全城军掠分别按主书句序录，不扩写其亲自指挥全部抢掠；宫人无名不造实体。')
E=ev('siyuan_hears_cunxu_death_at_yingzigu','李嗣源在罂子谷得庄宗死讯而恸哭，向诸将陈述忧虑',1,'是日，李嗣源','今吾将安归乎！”',[('嗣源','闻讯、陈述者'),('帝','所闻死亡者')],when='926年四月丁亥朔据主书',place='罂子谷',note='素得士心、群小蔽惑为嗣源所言，并非已独立证明的全部死因。')
claim('event',E,'description','旧明宗纪也记丁亥朔至罂子谷闻庄宗晏驾，恸哭。',1,'四月丁亥朔，至罌子穀，聞蕭牆釁作，莊宗晏駕，帝慟哭不自勝。','同书明宗纪与庄宗纪丁丑存在内部分歧，不用多数票覆盖底本。',source='jiuwudaishi-035-926-arrival',relation='corroborates')
E=ev('zhushouyin_calls_siyuan_restore_order','朱守殷遣使催李嗣源入京救止焚掠',1,'戊子','愿亟来救之！”',[('硃守殷','遣急报者'),('嗣源','催赴对象')],when='926年四月戊子据主书',place='洛阳至李嗣源军',note='京城大乱为朱报告，此段发报不等李已经抵京。')
E=ev('siyuan_enters_luoyang_buries_remains','李嗣源入洛止私第，禁焚掠，收庄宗燼骨殡敛',1,'乙丑','而殡之。',[('嗣源','入洛、禁掠、殡骨者'),('帝','所殡骨之人')],when='926年四月主记“乙丑”，旧明宗纪与新明宗纪记己丑',place='洛阳',note='乙丑与前戊子、后庚寅序不合疑己丑，但底本与引用原乙保留，另录两史纪日，未静默改字；殡未等雍陵正式葬。')
claim('event',E,'time_original','旧明宗纪记己丑至洛阳止旧宅并分诸将止焚掠。',1,'己丑，帝至洛陽，止於舊宅，分命諸將止其焚掠。','独立日期引证，不自行合成通鉴己丑文本。',source='jiuwudaishi-035-926-arrival',relation='conflicts')
claim('event',E,'time_original','新明宗纪同记己丑入洛。',1,'己丑，入洛陽。','新旧两部同日为校证，仍保留主疑字。',source='xinwudaishi-006-926-regency',relation='conflicts')
E=ev('houyi_leaves_ye_returns_cunxu','李嗣源入鄴时，侯益脱身归洛，庄宗流涕相抚',1,'嗣源之入鄴也','庄宗抚之流涕。',[('侯益','平遥前直指挥使、脱身返洛者'),('帝','相抚者')],when='926年三月李嗣源入鄴期间的追叙，确日未载',place='鄴至洛阳',note='追叙可由前卷同年鄴乱定位三月，不写成庄宗死后的相抚。')
E=ev('siyuan_restores_houyi','侯益自缚请罪，李嗣源认为其为臣尽节，令复原职',1,'至是，益','使复其职。',[('侯益','自缚请罪者'),('嗣源','赦责复职者')],when='926年四月李嗣源入洛时',place='洛阳',note='乐为臣疑字保留；不因请罪假定侯益已犯罪，不造新增官职。')
E=ev('siyuan_instructs_patrol_consorts','李嗣源令朱守殷巡徼待魏王、丰备淑德二妃供给，称葬毕归藩',1,'嗣源谓硃守殷','国家扞御北方耳。”',[('嗣源','下令并表达归藩意者'),('硃守殷','巡徼供给受令者'),('继岌','所待魏王'),('淑妃','在宫供给对象'),('德妃','在宫供给对象')],when='926年四月李嗣源入洛时',place='洛阳宫廷',note='归藩为其声明，不等真实已经归藩；淑妃依新家人韩氏、德妃伊氏核名，德妃不并梁末帝张氏。')
claim('person',people['伊氏（李存勖德妃）'],'description','新家人传明说韩氏封淑妃、伊氏封德妃，核本段二妃身份。',1,'乃封韓氏為淑妃，伊氏為德妃。','封妃为同光二年（924）追溯书证，本批只作姓名官称校核，不新建926封妃事件。',source='xinwudaishi-014-924-consort-titles',relation='adds')
claim('event',E,'description','旧明宗纪同记令朱巡抚待魏王，称山陵礼毕归藩。',1,'時魏王繼岌征蜀未還，帝謂朱守殷曰：「公善巡撫，以待魏王。吾當奉大行梓宮山陵禮畢，即歸藩矣。」','旧所载言论与主同，未视归藩已经执行。',source='jiuwudaishi-035-926-arrival',relation='corroborates')
E=ev('officials_urge_siyuan_accession_refused','豆卢革率百官上笺劝进，李嗣源解释行军原委并拒绝',1,'是日，豆卢革',None,[('豆卢革','率百官劝进者'),('嗣源','拒劝进并陈述者')],when='926年四月李嗣源入洛当日，主乙丑疑己丑',place='洛阳',note='自称本无他心等为本人解释，不当已证内心；劝进不等已经登基，下段监国另录。')
claim('event',E,'description','旧明宗纪同记入洛当日群臣劝进，帝面谕止之。',1,'是日，群臣諸將上箋勸進，帝面諭止之。','帝在旧明纪指李嗣源，未据本纪称帝把此时身份改成正式皇帝。',source='jiuwudaishi-035-926-arrival',relation='corroborates')
E=ev('yuan_captured_pinglu','元行钦拟投河中李存霸，兵散后在平陆被执、折足送洛阳',2,'李绍荣欲','折足送洛阳。',[('李绍荣','拟赴河中、被执者'),('存霸','拟投对象')],when='926年四月庚寅至平陆据主书',place='洛阳外逃路、平陆至洛阳',note='欲奔河中不等见到李存霸；被执不是此时已斩，捕者未名不造。')
E=ev('cunba_abandons_post_to_jinyang','李存霸率千人弃镇奔晋阳',2,'存霸亦',None,[('存霸','弃镇率部逃奔者')],when='926年四月宫乱后叙次，确日未载',place='河中至晋阳方向',note='奔晋阳为目的与行动，不提前纳入第7段到晋阳及被杀。')
E=ev('jiji_retreats_xingping_toward_fengxiang','李继岌至兴平闻洛阳乱，引军西返，拟保凤翔',3,'辛卯',None,[('继岌','闻乱退军、拟保凤翔者')],when='926年四月辛卯据主书',place='兴平至凤翔方向',note='谋保据凤翔不等已占据，下一步东返与死亡尚待后段。')
E=ev('xiang_executes_kang_fengxiang','向延嗣到凤翔，奉庄宗原命处决康延孝',4,'向延嗣',None,[('向延嗣','奉原诏行刑者'),('李绍琛','被处决者'),('帝','原命发令者')],when='926年四月本段叙次，确日未载',place='凤翔',note='李绍琛复用康延孝；前批金雁桥被擒未死，此次始录实诛。庄宗之命为此前诏令，不当死后新发。')
claim('person',people['康延孝'],'death_year','康延孝于926年在凤翔被向延嗣奉诏处决。',4,Q[4]['text'],'前擒后诛按主连续区分。')
claim('event',E,'description','旧康传同记班师到凤翔、向延嗣赍诏至遂诛。',4,'及圜班師，行次鳳翔，中使向延嗣齎詔至，遂誅之。','此处圜任圜；同人同地同向诏补证，后葬与天成初迁首不提前扩成主本段行动。',source='jiuwudaishi-074-926-kang-capture',relation='corroborates')
E=ev('cunxu_assigns_two_monitors_jinyang','庄宗此前派吕、郑二内养至晋阳，分别监兵、监仓库',5,'初，庄宗','皆承应不暇。',[('帝','此前派遣者'),('吕内养（晋阳）','两内养之一'),('郑内养（晋阳）','两内养之一'),('张宪','留守、应承者')],year=None,when='926年四月晋阳事变前追叙，派遣确年未载',place='晋阳',note='原无具体各人分工，不指定吕监兵或郑监库；仅据姓及职辨主体，不并吕知柔或其他郑氏内官。')
E=ev('fuyanchao_becomes_northern_inspector','鄴变后庄宗任符彦超为北都巡检，书明其为符彦卿兄',5,'及鄴都有变','彦卿之兄也。',[('帝','任命者'),('李彦超','汾州刺史、北都巡检'),('李彦卿','被明言为其弟者')],when='926年三月鄴乱后、庄宗死前追叙',place='晋阳北都',note='主李彦超据新张宪同北京巡检及旧本人还符姓校符彦超；三月鄴变由前卷定位，不把任命写成庄宗死后。')
relationship('李彦超','李彦卿','兄长',5,'彦超，彦卿之兄也。','符彦超是符彦卿的兄长，单边按方向约定，不新增重复弟弟反边。')
claim('person',people['符彦超'],'description','旧明宗纪记北京留守李彦超奏父存审原姓符，请还本姓。',5,'北京留守李彥超上言：「先父存審，本姓符氏，蒙武皇賜姓，乞卻還本姓。」從之。','这是后来天成三年姓名校证，不新增926已还本姓之事；实体用通行符姓，原引文李保留。',source='jiuwudaishi-038-928-fuyanchao-surname',relation='adds')
E=ev('zhangzhao_urges_zhangxian_petition_refused','庄宗死后张昭远劝张宪奉表劝进，张宪因先帝恩拒绝，张昭远流泪赞其志',5,'庄宗既殂','忠义不朽矣。”',[('张昭远','河间推官、劝表并赞志者'),('张宪','拒表者')],when='926年四月庄宗死后',place='晋阳',note='张昭远据宋本名昭远校张昭（五代宋初）；与三国张昭及他同名者区分。忠义不朽为张评语，不生成客观等级。')
claim('person',people['张昭（五代宋初）'],'description','宋史记张昭字潜夫，本名昭远，避汉祖讳改称昭。',5,'張昭，字潛夫，本名昭遠，避漢祖諱，止稱昭。','后世改名用于匹配，不生成926改名事件；主河间与宋世居濮州不是同一含义，未强改籍贯。',source='songshi-263-926-zhangzhao-name',relation='adds')
claim('event',E,'description','宋张昭传同记其劝张宪奉表自安、张宪拒绝，二人相泣。',5,'昭謂憲曰：「得無奉表勸進為自安之計乎？」憲曰：「我本書生，見知主上，位至保𨤲，乃布衣之極。苟靦顏求生，何面目見主於地下？」昭曰：「此古人之志也，公能行之，死且不朽矣。」相泣而去，','只取劝表及言论，不把宋末憲遂死提前录入此拒表事件。',source='songshi-263-926-zhangzhao-petition',relation='corroborates')
claim('event',E,'description','新张宪传也记张昭远教其奉表，张宪涕泣拒绝。',5,'憲從事張昭遠教憲奉表明宗以勸進，憲涕泣拒之。','新叙存霸到晋阳在前、主到晋阳在后段；相同拒表事补证，事件次序差别保留。',source='xinwudaishi-028-926-zhangxian',relation='corroborates')
E=ev('cunzhao_forges_order_plots_taiyuan','李存沼奔晋阳假传庄宗命，与吕郑内养谋杀张宪、符彦超据城',5,'有李存沼者','据晋阳拒守。',[('李存沼','庄宗近属、矫诏及密谋者'),('吕内养（晋阳）','参与密谋内养'),('郑内养（晋阳）','参与密谋内养'),('张宪','拟杀对象'),('李彦超','拟杀对象')],when='926年四月庄宗死后叙次，确日未载',place='洛阳至晋阳、晋阳',note='主仅近属，不补确切兄弟父子；谋杀是计划尚未杀成功，不将两拟杀者写成此时死亡。')
E=ev('fuyanchao_warns_zhangxian','符彦超知密谋告张宪，拟先图之；张宪以先帝恩不忍',5,'彦超知之','乃天也。”',[('李彦超','知谋、密告、拟先制者'),('张宪','拒先制者')],when='926年四月李存沼矫诏之后、壬辰军变之前',place='晋阳',note='天是张宪信念，非超自然判断；彦超欲先图尚未等其亲自处决。')
E=ev('jinyang_soldiers_kill_monitors_cunzhao','壬辰夜晋阳军士杀吕郑内养与李存沼，并掠城至天明',5,'彦超谋未决','因大掠达旦。',[('吕内养（晋阳）','被杀内养'),('郑内养（晋阳）','被杀内养'),('李存沼','被杀者')],when='926年四月壬辰夜据主书',place='晋阳牙城及城中',note='军士共杀未指明由符彦超下令，不能将先拟图推作实际主使；达旦为延续时段。')
E=ev('zhangxian_flees_xinzhou','张宪闻晋阳兵变，逃往忻州',5,'宪闻变','出奔忻州。',[('张宪','闻变出奔者')],when='926年四月壬辰夜军变后叙次',place='晋阳至忻州',note='主忻州与新沂州不同，且新置存霸杀后，分别引用；不在此录张宪死。')
claim('event',E,'description','新张宪传记其出奔沂州，与主忻州地名有别。',5,'憲出奔沂州，亦見殺。','整句逐字保留，死亡是新后续叙事，仅用于来源差异说明，本事件只录出奔；待主后续段处理死亡。',source='xinwudaishi-028-926-zhangxian',relation='conflicts')
E=ev('fuyanchao_restores_taiyuan_order','李嗣源书至，符彦超号令军士安定城中，权知太原军府',5,'会嗣源移书至',None,[('嗣源','移书者'),('李彦超','号令安城、权知军府者')],when='926年四月晋阳军变后叙次',place='太原晋阳',note='权知为暂掌，未任正式节度；主城中始安为书载效果。')
E=ev('siyuan_accepts_regency_enters_xingsheng','百官三笺请监国，李嗣源接受，甲午居兴圣宫受朝，下令称教、百官称殿下',6,'百官三笺','百官称之曰殿下。',[('嗣源','受请监国、受百官班见者')],when='926年四月接受三笺在前，甲午入宫受见据主书',place='洛阳兴圣宫',note='接受监国与正式即位分开，未提前把此日写成称帝。')
claim('event',E,'time_original','旧明宗纪记壬辰三拜笺请监国、甲午幸兴圣宫受班见。',6,'壬辰，文武百僚三拜箋，請行監國之儀，以安宗社，答旨從之。既而有司上監國儀注。甲午，幸大內興聖宮，始受百僚班見之儀。','主三笺无确日，旧补壬辰，甲午两书同，不视改国号讨论已实施。',source='jiuwudaishi-035-926-regency',relation='adds')
claim('event',E,'description','新明宗纪记甲午监国、于兴圣宫朝群臣。',6,'甲午，監國，朝羣臣于興聖宮。','只取监国朝群臣，不提前录同段丙午即位及诛元孔。',source='xinwudaishi-006-926-regency',relation='corroborates')
E=ev('siyuan_releases_young_palace_women','宣徽使献数百年轻宫人，李嗣源拒绝，改用熟悉旧事的宫人，年轻者归亲或自择去处，蜀宫人同例',6,'庄宗后宫',None,[('嗣源','拒献、安排宫职与放归者')],when='926年四月监国受见后叙次',place='洛阳宫中',note='主后宫余千余、献数百均书载概数；老旧是原有熟习者，少年不补现代年龄范围；无亲者任适不擅说一律强嫁。')

review='连续卷275第1—6段逐句回查。原源首块含帝纪标题，仅引用对应正文不生成标题史事。郭攻门主黄甲同攻、新相射分别保留；庄宗中箭进酪不推亲射或毒杀，主丁亥/旧庄宗丁丑/旧明宗丁亥各存。李彦卿据同父及宋同王全斌守卫校符彦卿，李彦超据新同北京巡检及旧本人还符姓辨符彦超；父亲、兄长两边按方向约定。善友仅名不并石善友；申王存屋校李存渥、乙丑入洛疑己丑保留主字与两史引证。韩淑、伊德据新册妃对应，不并蜀徐淑或梁张德。侯益脱鄴为三月追叙，与入洛后复职分开；李嗣源归藩仅其说，劝進/监国/正式即位分阶段。元在平陆被执未死、存霸奔晋阳未到、魏王谋凤翔未占不提早结局；康前被擒到本段凤翔向诏实诛。吕郑两内养名未载且分工未配各人，不并吕知柔；李存沼近属不补具体亲属。张昭远据宋本名合为五代宋初张昭，主河间/宋世居濮不混籍义。张宪拒表相同，主奔忻州与新沂州、存霸时序有差；新死亡引文只作来源说明，未提前录死亡。壬辰军士杀监不推符彦超主使；甲午监国不等即位、年轻宫人归亲/任适不推统一强嫁。展示简体，原文摘录与快照保留底本繁简及疑字。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,7):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph=Q[7]['id'],next_volume=275,supplements=supplements,excluded_non_body=[],coverage='卷275第1—6段，原文件6—11行；兴教门兵变与庄宗死、诸王出奔、李嗣源入洛、元被执、魏王退军、康延孝实诛、晋阳军变及监国释宫人。926年110正文段累计49，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,7)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
