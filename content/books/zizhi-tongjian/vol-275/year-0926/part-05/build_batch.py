# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 7–12."""
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
 ('jiuwudaishi-036-926-burial-and-demotions',P/'sources/library/jiuwudaishi-036-926-burial-and-demotions','f5afcc0c','薛居正等'),
 ('jiuwudaishi-036-926-exile-edicts',P/'sources/library/jiuwudaishi-036-926-exile-edicts','f5afcc0c','薛居正等'),
 ('jiuwudaishi-036-926-hua-executions',P/'sources/library/jiuwudaishi-036-926-hua-executions','f5afcc0c','薛居正等'),
 ('jiuwudaishi-137-926-yaokun',P/'sources/library/jiuwudaishi-137-926-yaokun','f5afcc0c','薛居正等'),
 ('liaoshi-002-926-abaoji-death',P/'sources/library/liaoshi-002-926-abaoji-death','f5afcc0c','脱脱等'),
 ('liaoshi-002-926-coffin-return',P/'sources/library/liaoshi-002-926-coffin-return','f5afcc0c','脱脱等'),
 ('liaoshi-002-926-dongdan',P/'sources/library/liaoshi-002-926-dongdan','f5afcc0c','脱脱等'),
 ('liaoshi-002-926-fuyu',P/'sources/library/liaoshi-002-926-fuyu','f5afcc0c','脱脱等'),
 ('liaoshi-002-926-yaokun',P/'sources/library/liaoshi-002-926-yaokun','f5afcc0c','脱脱等'),
 ('tongjian-275-926-chancellors-and-khitan',P/'sources/library/tongjian-275-926-chancellors-and-khitan','f5afcc0c','司马光等'),
 ('xinwudaishi-028-926-xixifu-accusations',P/'sources/library/xinwudaishi-028-926-xixifu-accusations','f5afcc0c','欧阳修'),
 ('xinwudaishi-072-926-anduanshaojun',P/'sources/library/xinwudaishi-072-926-anduanshaojun','f5afcc0c','欧阳修'),
 ('tongjian-275-926-bian-mutiny',YEAR/'part-04/sources/library/tongjian-275-926-bian-mutiny','e466a47f','司马光等'),
 ('xinwudaishi-006-926-may-offices',YEAR/'part-03/sources/library/xinwudaishi-006-926-may-offices','5c38857d','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-926-bian-mutiny','tongjian-275-926-chancellors-and-khitan']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p037-p048',
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
for n in range(37, 49):
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
    ck = f'claim_zztj_275_0926_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

identity_revision=json.loads((ROOT/'content/revisions/2026-10-02-aboji-duplicate/plan.json').read_text())
assert identity_revision['canonical_key']=='person_阿保机' and identity_revision['duplicate_key']=='person_耶律阿保机'
ALIASES={'帝':'李嗣源','契丹主':'阿保机','阿保机':'阿保机','突欲':'耶律倍','德光':'耶律德光','述律后':'述律平','庄宗':'李存勖','坤':'姚坤','革':'豆卢革','说':'韦说','希甫':'萧希甫'}
NEW_ALIASES={'耶律倍':['突欲','托云'],'耶律德光':['德光'],'姚坤':[],'刘殷肇':['劉殷肇'],'萧希甫':['蕭希甫'],'王傪':[]}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷275同光四年条所见人物：{name}，{role}。',biography=None,status='draft')
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
E=ev('hua_mutiny_accusations_investigated','于可洪与魏博戍将互奏对方作乱，朝廷遣使调查',37,'于可洪','按验得实，',[('于可洪','互奏一方'),('帝','遣使调查者')],when='926年七月辛酉处决前，调查日未载',place='滑州及后唐朝廷',note='互奏是相互指控；主按验得实为调查叙述，未载使者姓名，不造具名官员。')
E=ev('yukehong_executed','于可洪被斩于都市',37,'辛酉','斩可洪于都市，',[('于可洪','被斩者')],when='926年七月辛酉',place='后唐都市，主未具城市名',note='前批本段只兵变，此处才实际死亡；旧都校相次到阙补证，现代坐标不推。')
claim('person',people['于可洪'],'death_year','于可洪于926年滑州兵变调查后被斩。',37,'辛酉，斩可洪于都市，','原于/旧於姓名字形相通，同滑州职同事件校同人，不提前前批死亡。')
claim('event',E,'description','旧明宗纪记都校于可洪等相次到阙，斩于都市。',37,'其都校於可洪等相次到闕，亦斬於都市。','旧概记非辛酉确日，分存；只记录已处决，不猜具体刑场。',source='jiuwudaishi-036-926-hua-executions',relation='corroborates')
E=ev('hua_mutiny_units_family_executions','朝廷族诛滑州左崇牙全营及助乱的右崇牙、两长剑、建平将校百人',37,'其首谋滑州',None,[('帝','族诛决定所归朝廷皇帝')],when='926年七月辛酉处置条，各营执行日未另载',place='滑州军营及朝廷处置地',note='全营、百人是主不同群体计数，族诛所及亲属总人口不明，不能加成死亡总数；诸军名按主断句存，不生成同名人物。')
claim('event',E,'description','旧纪概记滑州左右崇牙及长剑军士数百人被诛并夷其族。',37,'誅滑州左右崇牙及長劍等軍士數百人，夷其族，作亂故也。','旧数百与主助乱将校百人及首谋全营口径不同，分别引；不是旧史证明只有百人死亡。',source='jiuwudaishi-036-926-hua-executions',relation='adds')
E=ev('officials_five_day_rotating_petitions','朝廷令百官每五日起居并轮流奏事',38,'壬申',None,[('帝','转对制度发令者')],when='926年七月壬申',place='后唐朝廷',note='此前五月五日起居已录，本段新增转对奏事，不当此前朝仪不存在。')
E=ev('abaoji_conquers_fuyu','耶律阿保机攻渤海并攻取夫余城',39,'契丹主攻','拔其夫馀城，',[('契丹主','攻渤海取城者')],when='926年主七月条追记；辽史记正月庚申拔扶余',place='渤海夫余城',note='原勃海/渤海、夫馀/扶余字形各存；不是据段序写为七月首次攻取。')
claim('event',E,'time_original','辽太祖纪记天显元年正月庚申拔扶余城。',39,'天顯元年春正月己未，白氣貫日。庚申，拔扶餘城，誅其守將。','用相邻年度标题明确926，白气只是此摘录定位内容，不录成可验证天象；原日不换公历。',source='liaoshi-002-926-fuyu',relation='adds')
E=ev('abaoji_establishes_dongdan','契丹改渤海国为东丹',39,'更命曰','东丹国。',[('契丹主','改国名者')],when='926年主七月条追记；辽史记二月丙午',place='原渤海国',note='主句在拔夫余后写更命曰东丹，辽明确为改国名，不把夫余城市名写为东丹国；未推所有渤海旧民均完全受控。')
claim('event',E,'description','辽史明确改渤海国为东丹、忽汗城为天福。',39,'丙午，改渤海國為東丹，忽汗城為天福。','国家与城市两个更名不混同，主未名忽汗所以只作此事地理补证。',source='liaoshi-002-926-dongdan',relation='adds')
E=ev('be i_installed_dongdan'.replace(' ',''),'耶律阿保机命长子耶律倍镇东丹，号人皇王',39,'命其长子','号人皇王，',[('契丹主','任命父亲'),('突欲','镇东丹、受号人皇王的长子')],when='926年东丹建立时；辽史记二月丙午',place='东丹',note='突欲与辽人皇王倍以同任同地同称号校同人；不因以后奔唐更名提前录930事件。')
claim('person',people['耶律倍'],'description','辽史称皇太子倍受册人皇王主东丹。',39,'冊皇太子倍為人皇王以主之。','同一人皇王任职校突欲即耶律倍；姓名异名保留，不另建突欲人物。',source='liaoshi-002-926-dongdan',relation='adds')
E=ev('deguang_guards_west_tower','耶律阿保机命次子德光守西楼，号元帅太子',39,'以次子德光','号元帅太子。',[('契丹主','任命父亲'),('德光','守西楼、受号者')],when='926年主七月条追记，任命确日未载',place='契丹西楼',note='元帅太子称号不能据此提前写德光已继契丹皇帝位。')
relationship('契丹主','突欲','父亲',39,'命其长子突欲镇东丹，号人皇王，','耶律阿保机是耶律倍之父，主明确长子。')
relationship('契丹主','德光','父亲',39,'以次子德光守西楼，号元帅太子。','耶律阿保机是耶律德光之父，主明确次子；不是庄宗与德光的父子。')
relationship('突欲','德光','兄长',39,'命其长子突欲镇东丹，号人皇王，以次子德光守西楼，号元帅太子。','同父长子与次子明示长幼，倍是德光兄长，未另建弟弟反向边。')
E=ev('yaokun_sent_mourning_envoy','李嗣源派供奉官姚坤向契丹告庄宗之哀',39,'帝遣供奉官','告哀于契丹。',[('帝','派遣者'),('姚坤','供奉官、告哀使者')],when='926年明宗入立后、阿保机死前；出发确日未载',place='后唐至契丹',note='使者告哀与对方后来死亡分事件，不把主排列定为七月才出发。')
claim('event',E,'description','旧契丹传记姚坤奉书经西楼、慎州见阿保机。',39,'明宗初纂嗣，遣供奉官姚坤奉書告哀，至西樓邑，屬阿保機在渤海，又徑至慎州，崎嶇萬里。','行程据旧独立补，不把崎岖万里换成精确公里。',source='jiuwudaishi-137-926-yaokun',relation='adds')
claim('event',E,'time_original','辽史六月丙午记次慎州，唐遣姚坤告国哀。',39,'六月丁酉，二府平。丙午，次慎州，唐遣姚坤以國哀來告。','补到访纪时而非出发确日；丁酉是前事不移作使者日。',source='liaoshi-002-926-yaokun',relation='adds')
E=ev('abaoji_mourns_cunxu_explains_aid','耶律阿保机闻庄宗遇害恸哭，并称因渤海未下未能往援',39,'契丹主闻庄宗','哭不已。',[('契丹主','闻讯哭泣及解释者'),('庄宗','被悼者'),('坤','告哀后交谈使者')],when='926年姚坤告哀会见期间',place='契丹姚坤会见处；旧慎州行程',note='吾方欲救之是阿保机自述意向，未造已经出兵洛阳的援军行动。朝定本书释朋友，不据吾儿生成庄宗亲子或收养边。')
claim('event',E,'description','旧契丹传也记阿保机称原欲救助，因渤海未下而未往。',39,'近聞漢地兵亂，點得甲馬五萬騎，比欲自往洛陽救助我兒，又緣渤海未下，我兒果致如此，冤哉！','旧五万骑为其自述已点兵数，不据此认精确实测军额；没有到洛阳救援。',source='jiuwudaishi-137-926-yaokun',relation='adds')
E=ev('yaokun_debates_succession_legitimacy','阿保机与耶律倍质问李嗣源为何自立，姚坤解释并回应牵牛蹊田之喻',39,'又谓坤曰','“理当然。”',[('契丹主','质问及回应者'),('突欲','在侧参与论辩者'),('坤','解释明宗即位者'),('帝','交谈所议即位者')],when='926年姚坤告哀会见期间',place='契丹会见处',note='中国无主不得已而立是使者外交陈述，不当独立判定即位合法性；话语主体逐句存。')
claim('event',E,'description','旧契丹传称在侧的阿保机之子为托云，也引牵牛蹊田之说。',39,'其子托雲在側，謂坤曰：「漢使勿多談。」因引左氏牽牛蹊田之說以折坤，','托云与主突欲同会见发言、同东丹王校异译；话语异文不强逐字一致。',source='jiuwudaishi-137-926-yaokun',relation='adds')
E=ev('abaoji_declares_moderation_after_cunxu','阿保机向姚坤批评庄宗声色游畋，称自己已断酒、散遣伶人、放鹰犬',39,'又曰：“闻吾儿','行自亡矣。”',[('契丹主','批评及自陈者'),('坤','受话使者'),('庄宗','受批评对象')],when='926年姚坤会见阿保机时述及之前行为',place='契丹会见处及其家中自述',note='批评和自述并非独立核实庄宗唯一亡国原因或阿保机全家已经永远禁酒；若亦效为警戒不是未来已亡。')
E=ev('abaoji_demands_north_hebei_detains_envoy','阿保机提出以大河以北换不南侵，姚坤称无权决定，遭拘禁',39,'又曰：“吾儿与我','囚之，',[('契丹主','提条件并拘禁者'),('坤','拒专决、被囚使者')],when='926年姚坤告哀会见期间',place='契丹会见处，所索为大河以北',note='外交索地条件未被同意，未造河以北实际割让。友旧与无怨为讲话，不建永久盟友边。')
E=ev('abaoji_demands_three_prefectures_han_saves_yao','姚坤被囚十余日后，阿保机再索镇定幽三州，逼写状不成欲杀，韩延徽劝阻，姚再被囚',39,'旬馀，复召之',None,[('契丹主','再索地、拟杀并再囚者'),('坤','拒写状被囚者'),('韩延徽','谏阻杀使者')],when='926年首次拘禁姚坤后十余日',place='契丹会见及囚禁处；索镇州定州幽州',note='欲杀不等姚坤已经死亡；旧契丹传只索幽州且以归报续盟叙法不同，分别引不拼一谈判定稿。')
claim('event',E,'description','旧契丹传另记索幽州并称将到幽镇以南面盟。',39,'爾先復命，我續將馬萬騎至幽、鎮以南，與爾家天子面為盟約，我要幽州，令漢兒把捉，更不復侵入漢界。','这是阿保机提出的条件及未来意图，旧未载本段囚使过程；主大河以北及三州与旧索幽州各存，不当割地已成。',source='jiuwudaishi-137-926-yaokun',relation='conflicts')
E=ev('cunxu_buried_yongling','李存勖以光圣神闵孝皇帝谥号葬雍陵，庙号庄宗',40,'丙子',None,[('庄宗','被葬皇帝')],when='926年七月丙子据主书；旧明宗纪作乙亥',place='雍陵',note='庙号及谥号与死亡区别，本段葬不作新的死亡年；旧葬日分引。')
claim('event',E,'time_original','旧纪记乙亥庄宗梓宫发引，当日葬雍陵。',40,'乙亥，莊宗皇帝梓宮發引，帝縗服臨送於樓前。是日，葬莊宗於雍陵。','旧乙亥与主丙子相邻日不一致，保留两书原字，不选择未经纸本核对的统一日。',source='jiuwudaishi-036-926-burial-and-demotions',relation='conflicts')
E=ev('wangjianli_reports_liu_capture','王建立奏称涿州刺史刘殷肇不受代、谋乱，已经讨擒',41,'丁丑',None,[('王建立','镇州留后、奏报者'),('刘殷肇','奏称拒代谋乱并被擒者')],when='926年七月丁丑奏报；捕获具体日主未具',place='涿州、镇州及朝廷',note='谋乱是王建立奏报，不将指控当独立裁判；已讨擒为奏述完成动作，未写已被处死。剌史疑刺史原字存。')
claim('event',E,'description','旧纪记王建立奏刘殷肇与其党十三人被擒，正在折足勘诘。',41,'鎮州留後王建立奏，涿州刺史劉殷肇不受代，謀叛，昨發兵收掩，擒劉殷肇及其黨一十三人，見折足勘詰。','旧昨及十三人据奏保留，不推主丁丑前一日确定；折足为旧审讯叙述，不推全部十三人已死。',source='jiuwudaishi-036-926-burial-and-demotions',relation='adds')
E=ev('yingzhou_zhangguo_command_created','后唐于应州置彰国军',42,'己卯',None,[('帝','设置军镇者')],when='926年七月己卯',place='应州',note='主义彰国、旧作彰德，名称异说不静默覆盖。军镇设置不是一次战役。')
claim('event',E,'description','旧史作升应州为彰德军节度，兴唐军改寰州隶属。',42,'升應州為彰德軍節度，仍以興唐軍為寰州，隸彰德軍。','旧彰德与主彰国有异，补附寰州内容仅旧证，不替换主名。',source='jiuwudaishi-036-926-burial-and-demotions',relation='conflicts')
E=ev('dou_wei_salary_and_court_criticism','史书记豆卢革韦说礼貌或不尽恭，豆卢父子俸钱独受实钱且追给到正月，引起议论',43,'门下侍郎','由是众论沸腾。',[('革','门下侍郎同平章事、被议论者'),('说','同平章事、书称奏事礼不尽恭者')],when='926年五月以来俸给背景，七月贬相前概述',place='后唐朝廷及俸钱发放',note='礼不恭和众论为史叙评价；俸钱折估、起给月份分别保留，不生成未名豆卢子；因果为作者所述。')
E=ev('weishuo_grandson_office_bribery_report','史书记韦说以孙为子奏官，并受选人王傪赂、为其除近官',43,'说以孙','除近官。',[('说','书载奏亲属官、受赂授官者'),('王傪','书载行赂选人')],when='926年七月贬相前背景，具体年月日未载',year=None,place='后唐官员铨选',note='原未具孙名及近官官名，不造无名孙子实体或任选职；受赂为本书叙述，现代独立司法证据未有。王傪不凭旧改王参字句合异名。')
E=ev('xiaoxifu_adviser_nomination_opposed','李嗣源以内旨拟任萧希甫谏议大夫，豆卢革韦说覆奏',43,'中旨以库部','革、说覆奏。',[('帝','内旨拟任者'),('希甫','库部郎中、拟受任谏议大夫'),('革','覆奏者'),('说','覆奏者')],when='926年七月贬相前追记，确日未载',place='后唐朝廷',note='覆奏在此语境反对核议，以新明确沮难补证；不与下庚辰升散骑混为一职。')
claim('event',E,'description','新萧传也记明宗欲任其谏议大夫，豆卢革韦说沮难。',43,'初，明宗欲以希甫為諫議大夫，豆盧革、韋說頗沮難之。','只补拟任受阻，同快照别的匭函赦令不提前扩入主线。',source='xinwudaishi-028-926-xixifu-accusations',relation='corroborates')
E=ev('xiaoxifu_accuses_dou_wei','萧希甫上疏指豆卢革韦说不忠阿庚，并诬奏夺田杀人、夺井取藏物等罪名',43,'希甫恨之','取宿藏物。”',[('希甫','上疏指控者'),('革','被指控者'),('说','被指控者')],when='926年七月贬相前，疏日未载',place='后唐朝廷',note='主明确因诬，罪名作为指控内容，绝不写成豆卢革确实杀民或韦说确获宝藏；阿庚疑阿谀原字保留不擅改。恨为史心理判断。')
claim('event',E,'description','新萧传同称希甫诬奏，记井中勘查只有破釜。',43,'希甫希旨，誣奏「革縱田客殺人，而說與隣人爭井，井有寶貨。」有司推劾，井中惟破釜而已，','新亦诬奏明确，井有宝货是指控而勘查仅破釜；不补未证夺井动机。',source='xinwudaishi-028-926-xixifu-accusations',relation='adds')
E=ev('dou_wei_demoted_prefects','豆卢革被贬辰州刺史，韦说被贬溆州刺史',43,'制贬革','说溆州剌史。',[('革','被贬辰州刺史者'),('说','被贬溆州刺史者'),('帝','贬职制令者')],when='926年七月庚辰赏萧以前；新明宗纪记己卯',place='辰州、溆州及朝廷',note='与后癸未司户、甲申流放分阶段；主未具本事确日，新纪补己卯。剌/刺字形保留。')
claim('event',E,'time_original','新明宗纪记己卯贬豆卢革辰州刺史、韦说叙州刺史。',43,'己卯，貶豆盧革為辰州刺史，韋說敍州刺史。','新敍州/主溆州/旧漵州名不同，保留电子本异文待核，不能静默一律溆州。',source='xinwudaishi-006-926-may-offices',relation='conflicts')
claim('event',E,'description','旧明宗纪称因萧希甫疏奏贬二相，并引制书列罪。',43,'宰相豆盧革貶辰州刺史，韋說貶漵州刺史，仍令所在馳驛發遣，為諫議大夫蕭希甫疏奏故也。','旧后引制书罪状为朝廷指控，不以官方制书反盖主新诬奏判断；两种史叙并存。',source='jiuwudaishi-036-926-burial-and-demotions',relation='corroborates')
E=ev('xiaoxifu_rewarded_promoted','萧希甫获赐金帛并升散骑常侍',43,'庚辰',None,[('希甫','获赏、擢散骑常侍者'),('帝','赏擢者')],when='926年七月庚辰',place='后唐朝廷',note='赏赐并不能证明疏中所有罪状属实；具体财物两书异记分引不合总量。')
claim('event',E,'description','旧史记赐萧希甫衣段二十匹、银器五十两。',43,'庚辰，賜蕭希甫衣段二十匹、銀器五十兩，賞疏革、說之罪也。','旧具体物数，与主金帛概述各存。',source='jiuwudaishi-036-926-burial-and-demotions',relation='adds')
claim('event',E,'description','新萧传记赐帛百匹、粟麦三百石并拜左散骑常侍。',43,'明宗賜希甫帛百匹、粟麥三百石，拜左散騎常侍。','新数量及种类与旧不同，主只金帛概述，不能合称同次总赏三百二十石或两份奖赏已证。',source='xinwudaishi-028-926-xixifu-accusations',relation='conflicts')
E=ev('abaoji_dies_fuyu','耶律阿保机卒于夫余城',44,'辛巳','卒于夫馀城，',[('阿保机','去世契丹主')],when='926年七月辛巳；旧契丹传记七月二十七日',place='夫余城',note='自然死亡叙述，不把史载黄龙大星等征兆当现代可验证天象或死因。')
claim('person',people['阿保机'],'death_year','耶律阿保机于926年在夫余城去世。',44,'辛巳，契丹主阿保机卒于夫馀城，','本段实际卒记与此前对庄宗欲救、自述分开。')
claim('event',E,'description','辽太祖纪记辛巳帝崩，年五十五。',44,'是日，上崩，年五十五。','本快照是日承辛巳，年龄据原虚实未辨，不倒推精确出生年。',source='liaoshi-002-926-abaoji-death',relation='adds')
claim('event',E,'time_original','旧契丹传记阿保机卒于扶余城，天成元年七月二十七日。',44,'俄而卒於扶餘城，時天成元年七月二十七日也。','补原纪年日期，不自行换算公历；扶余字形与主夫馀并列。',source='jiuwudaishi-137-926-yaokun',relation='adds')
E=ev('shulu_executes_unruly_chiefs','述律后召难制诸将酋长及其妻，称丈夫应往见先帝而将丈夫们杀害',44,'述律后召',None,[('述律后','召集及下令杀害者')],when='926年阿保机死后追记，具体各日未载',place='契丹诸将酋长聚集处',note='对话是史载诱杀叙述；受害者名数未列，未推妻们也被杀或所有契丹将领均死，不把各次杀害强同辛巳。')
claim('person',people['述律平'],'description','辽太祖纪记阿保机死次日壬午皇后称制、权决军国事。',44,'壬午，皇后稱制，權決軍國事。','仅补死后摄政阶段，辽此处未记主召妻诱杀细节，不视二事相互直接确证。',source='liaoshi-002-926-abaoji-death',relation='adds')
E=ev('dou_wei_again_demoted_low_offices','豆卢革再贬费州司户、韦说再贬夷州司户',45,'癸未','夷州司户。',[('革','再贬费州司户者'),('说','再贬夷州司户者'),('帝','再贬发令者')],when='926年七月癸未',place='费州、夷州及朝廷',note='两人职和州各配对，不与甲申流州混合。')
claim('event',E,'description','旧制书列二人为司户参军，员外置同正员并驿遣。',45,'癸未，詔辰州刺史豆盧革可責授費州司戶參軍，漵州刺史韋說可責授夷州司戶參軍，皆員外置同正員，仍令馳驛發遣。','补完整低职称与员外置，罪责制书后段仅指控不抹去主诬奏。',source='jiuwudaishi-036-926-exile-edicts',relation='corroborates')
E=ev('dou_wei_exiled_ling_he','豆卢革流放陵州，韦说流放合州',45,'甲申',None,[('革','被流陵州者'),('说','被流合州者'),('帝','流放决定者')],when='926年七月甲申',place='陵州、合州',note='流放不是本年已被杀，后年死留编年主线；不猜到达州日。')
claim('event',E,'description','旧制书将二人定长流百姓，并令长知所在。',45,'革可陵州長流百姓，說可合州長流百姓，仍委逐處長知所在。','处置身份由旧补；制书指贪饕受贿等不是所有指控经现代核实。',source='jiuwudaishi-036-926-exile-edicts',relation='adds')
E=ev('meng_inventory_and_sixteen_units','孟知祥检库得铠甲二十万，设左右牙等十六营共一万六千兵驻牙城内外',46,'孟知祥阴有',None,[('孟知祥','检库及置兵者')],when='926年七月末至八月前本段概述，确日未载',place='成都牙城内外',note='阴有据蜀志是史作者心理归因；不提前写此时已称帝。铠甲二十万与兵一万六千是不同对象，不倒推全部铠甲已发放或军额二十万。')
E=ev('solar_eclipse_august','史书记八月乙酉朔日食',47,'八月',None,[],when='926年八月乙酉朔',place='史书未具观测地点',note='记为史载天象，不自行给现代时刻、食分、覆盖地区或证明任何政治兆应。')
E=ev('shulu_assigns_anduanshaojun','史书记述律后令少子安端少君守东丹',48,'丁亥','守东丹，',[('述律后','守东丹派任者')],when='926年八月丁亥据主书',place='东丹',note='安端少君主与新俱作少子，尚未校清与辽宗室安端关系，保留全称不建或并人物，不据此建耶律安端为述律子；不能靠相近名字推李胡。')
claim('event',E,'description','新契丹传亦载述律遣幼子安端少君赴扶余代东丹王。',48,'其母述律遣其幼子安端少君之扶餘代之，將立以為嗣。','新独立原文保留相同全称；欲立为嗣是意图不当已经成为契丹帝，不提前取后德光实际立或930突欲奔唐。',source='xinwudaishi-072-926-anduanshaojun',relation='adds')
E=ev('shulu_be i_escort_coffin'.replace(' ',''),'述律后与长子耶律倍奉阿保机之丧，率众离开夫余城',48,'与长子突欲',None,[('述律后','奉丧率众者'),('突欲','奉父丧率众者'),('阿保机','所奉丧的已故主')],when='926年八月丁亥据主书；辽史记甲午皇后奉梓宫西还',place='夫余城出发',note='出发与抵皇都、安葬在后不提前；主与长子同行而辽人皇王后来继至的叙法独立保留。')
claim('event',E,'time_original','辽史八月甲午记皇后奉梓宫西还。',48,'甲午，皇后奉梓宮西還。','主丁亥与辽甲午不同，原日期分别引，不补现代路线坐标。',source='liaoshi-002-926-coffin-return',relation='conflicts')
claim('event',E,'description','辽史记八月乙巳人皇王倍继至。',48,'乙巳，人皇王倍繼至。','辽主后继至与主和后同出夫余叙法不一致，不能默认为同日同行；具体何段合流待核。',source='liaoshi-002-926-coffin-return',relation='conflicts')
relationship('述律后','突欲','母亲',48,'与长子突欲奉契丹主之丧，','语句承述律后与其长子，主明确母子；未为身份待考安端少君创建母子边。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新契丹传称东丹王突欲之母为述律。',48,'初，阿保機死，長子東丹王突欲當立，其母述律','母亲明确补证；长子当立仅史所述继统主张，未当已立。',source='xinwudaishi-072-926-anduanshaojun',relation='corroborates')

review='连续37—48段逐句回查。滑州互奏、按验、辛酉实斩与各营族诛分事，前批于可洪不提前死；主全营/百将校及旧数百军士、族诛人口未载不合死亡数。壬申五日起居新增转对，不重复前五月制度。渤海攻取夫余及东丹为七月条追叙，辽正月拔扶余与二月丙午改国/忽汗城天福及倍人皇王分时间，国名城名不混。突欲/托云/倍据同人皇王同访谈校同人，德光次子未提前继位；阿父倍德、倍兄德、述母倍按明文方向。姚告哀出发未知、辽六月丙午到慎州分纪；吾儿朝定是外交旧交称谓不建阿与庄宗亲父子。欲救未实施；即位论辩、批庄宗与自称断酒均讲话不是独立动机事实。索大河以北、囚使十余日、改索三州拒写欲杀韩谏再囚与旧只索幽续盟不同各引，未造割地已经同意或姚已死。主葬丙子旧乙亥，王奏刘拒代谋乱被擒主丁丑/旧前葬条及十三人、折足各据奏未造实死。彰国/旧彰德存异。豆卢礼及俸钱背景史述、韦孙为子无名不造人、王傪行赂是书载不擅合王参；主阿庚疑谀原字留。萧拟任受阻、疏指控且主新明确诬、二相贬、庚辰赏与升分事，不认夺井藏物已证。主溆州/旧漵/新敍州及赏金帛/旧衣段银/新帛粟麦各存。阿死辛巳与旧七月27并引不换公历，辽祥异不录实测。述后诱杀难制酋长只未名人数，具体年月不强辛巳，未推妻也死；辽壬午称制独立补充。豆韦癸未低职、甲申流放不提前次年死。孟铠甲二十万与十六营一万六千分对象，阴志史判断未称帝。日食保留史记不推食分时刻。安端少君身份主新未与辽同名安端校清，保全称事件不建或合主体或母子，未猜李胡。述倍护丧主丁亥同行/辽甲午西还倍乙巳继至各存。阿保机按2026-10-02同人修订复用person_阿保机，不再复用已隐藏重复key。展示简体，底本字形和快照逐字保留，纸本未核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(37,49):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(37,49)],next_paragraph=Q[49]['id'],next_volume=275,supplements=supplements,excluded_non_body=[],coverage='卷275第37—48段，原文件42—53行；滑州案处决、转对、东丹及姚坤告哀外交、庄宗葬与方镇、豆韦罢相流放、阿保机卒及述后、孟置牙兵、日食与奉丧。926年110正文段累计91，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(37,49)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
