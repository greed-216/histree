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
 ('tongjian-275-926-regency',YEAR/'part-01/sources/library/tongjian-275-926-regency','60d249b7','司马光等'),
 ('tongjian-275-926-returning-army',P/'sources/library/tongjian-275-926-returning-army','0c93a613','司马光等'),
 ('jiuwudaishi-035-926-appointments-fiscal',P/'sources/library/jiuwudaishi-035-926-appointments-fiscal','0c93a613','薛居正等'),
 ('jiuwudaishi-035-926-fiscal-and-yuan',P/'sources/library/jiuwudaishi-035-926-fiscal-and-yuan','0c93a613','薛居正等'),
 ('xinwudaishi-014-926-two-princes',P/'sources/library/xinwudaishi-014-926-two-princes','0c93a613','欧阳修'),
 ('xinwudaishi-014-926-liu-flight',P/'sources/library/xinwudaishi-014-926-liu-flight','0c93a613','欧阳修'),
 ('xinwudaishi-014-926-cunmei',P/'sources/library/xinwudaishi-014-926-cunmei','0c93a613','欧阳修'),
 ('jiuwudaishi-051-926-young-princes',P/'sources/library/jiuwudaishi-051-926-young-princes','0c93a613','薛居正等'),
 ('xinwudaishi-014-cunxu-five-sons',P/'sources/library/xinwudaishi-014-cunxu-five-sons','0c93a613','欧阳修'),
 ('songshi-483-sunguangxian',P/'sources/library/songshi-483-sunguangxian','0c93a613','脱脱等'),
 ('xinwudaishi-025-926-yuan-executed',P/'sources/library/xinwudaishi-025-926-yuan-executed','0c93a613','欧阳修'),
 ('xinwudaishi-026-zhangyanlang',P/'sources/library/xinwudaishi-026-zhangyanlang','0c93a613','欧阳修'),
 ('xinwudaishi-026-three-commissions',P/'sources/library/xinwudaishi-026-three-commissions','0c93a613','欧阳修'),
 ('xinwudaishi-038-mashaohong',P/'sources/library/xinwudaishi-038-mashaohong','0c93a613','欧阳修'),
 ('xinwudaishi-014-926-jiji-death',P/'sources/library/xinwudaishi-014-926-jiji-death','0c93a613','欧阳修'),
 ('xinwudaishi-040-926-wentao-release',P/'sources/library/xinwudaishi-040-926-wentao-release','0c93a613','欧阳修'),
 ('jiuwudaishi-035-926-regency',YEAR/'part-01/sources/library/jiuwudaishi-035-926-regency','60d249b7','薛居正等'),
 ('xinwudaishi-006-926-regency',YEAR/'part-01/sources/library/xinwudaishi-006-926-regency','60d249b7','欧阳修'),
 ('xinwudaishi-038-926-zhangjuhan',ROOT/'content/books/zizhi-tongjian/vol-274/year-0926/part-04/sources/library/xinwudaishi-038-926-zhangjuhan','378d632d','欧阳修'),
 ('jiuwudaishi-051-926-cunwo',YEAR/'part-01/sources/library/jiuwudaishi-051-926-cunwo','0a0ea078','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p007-p012',
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
for n in range(7, 13):
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
    ck = f'claim_zztj_275_0926_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李存勖','庄宗':'李存勖','监国':'李嗣源','嗣源':'李嗣源','李绍荣':'元行钦','李绍真':'霍彦威','李绍钦':'段凝','李绍氵中':'温韬','继岌':'李继岌','存霸':'李存霸','存渥':'李存渥','存确':'李存确','存纪':'李存纪','存礼':'李存礼','存美':'李存美','刘皇后':'刘夫人（李存勖妻）','李彦超':'符彦超','徐温':'徐温','季兴':'高季昌','高季兴':'高季昌','温':'徐温','光宪':'孙光宪','循':'孔循','李强宏':'李绍宏','从袭':'李从袭','圜':'任圜','敬瑭':'石敬瑭','李氵中':'李冲（华州都监）','氵中':'李冲（华州都监）','继嵩':'李继嵩','继潼':'李继潼','继蟾':'李继蟾','继峣':'李继峣'}
NEW_ALIASES={'张延朗':['張延朗'],'李继嵩':['李繼嵩'],'李继潼':['李繼潼'],'李继蟾':['李繼蟾'],'李继峣':['李繼嶢'],'孙光宪':['孫光憲'],'张篯':['張籛','张籛'],'李冲（华州都监）':['李沖（華州都監）','李氵中（华州都监）'],'李存敬':[]}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=926 if name=='李存敬' else None,description=f'《资治通鉴》卷275同光四年条所见人物：{name}，{role}。',biography=None,status='draft')
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
E=ev('appoint_an_and_zhang_privy','监国任安重诲为枢密使、张延朗为枢密副使',7,'乙未','为副使。',[('监国','任命者'),('安重诲','中门使、受任枢密使'),('张延朗','镇州别驾、受任副使')],when='926年四月乙未据主书',place='洛阳',note='监国为李嗣源，此时未正式即位；副使是枢密副使，不造别的衙署职。')
claim('event',E,'description','旧明宗纪亦记安重诲、张延朗同任枢密正副使。',7,'以中門使安重誨為樞密使，以鎮州別駕張延朗為樞密副使，','只取正副任命，后同句范延光及冯赟尚非主本段，不另造主线事件。',source='jiuwudaishi-035-926-regency',relation='corroborates')
E=ev('zhangyanlang_background_and_marriage','张延朗出身开封租庸吏，其女嫁安重诲之子，书称因此被安引荐',7,'延朗，开封人','故重诲引之。',[('张延朗','租庸吏出身、女嫁安氏子者'),('安重诲','引荐亲家者')],year=None,when='926年四月任职段内的背景追叙；结婚确年未载',place='开封及任职交往地，婚姻地点未载',note='性纤巧善事权要为史作者评价，不生成道德事实；女与安子均未名不补名。故为本书因果判断。')
relationship('张延朗','安重诲','姻亲',7,'以女妻重诲之子，故重诲引之。','张延朗之女嫁安重诲之子，两人为姻亲；本关系对称，未为无名子女造姓名。')
claim('person',people['张延朗'],'description','新张延朗传记其为汴州开封人，事梁由租庸吏任郓州粮料使。',7,'張延朗，汴州開封人也。事梁，以租庸吏為鄆州糧料使。','用本籍与出身印证，不提前录新传后来的三司使任命。',source='xinwudaishi-026-zhangyanlang',relation='adds')
E=ev('siyuan_orders_find_princes','监国下令各地访求出逃诸王',7,'监国令','所在访求诸王。',[('监国','寻访发令者')],when='926年四月乙未任命后叙次，确日未载',place='洛阳发令、所在诸地',note='访求为命令，不等已经找到所有诸王或全部送京。')
E=ev('an_huo_secretly_kill_two_princes','李存确、李存纪匿民间被密告，安重诲与霍彦威谋议后秘密遣人到田舍杀害',7,'通王存确','乃密遣人就田舍杀之。',[('存确','匿民间被杀通王'),('存纪','匿民间被杀雅王'),('安重诲','获密告、参与谋杀及遣人者'),('李绍真','参与谋议者')],when='926年四月诸王寻访期间，确日未载',place='南山民间田舍',note='殿下性慈不可闻为谋议者陈述，不当此时监国已知并同意；原无执行人名不造具体杀手。南山据前段主原出奔对应。')
claim('event',E,'description','新家人传记安重诲向霍彦威询问二王，霍主张勿奏、密处，然后杀于民家。',7,'重誨謂霍彥威曰：「二王逃難，主上尋求，恐其失所。今上既監國典喪，此禮如何？」彥威曰：「上性仁慈，不可聞奏。宜密為之所，以安人情。」乃即民家殺之。','新详霍提议与主共同谋议不同，留话者分工，不推监国事先授意。',source='xinwudaishi-014-926-two-princes',relation='adds')
for name in ['李存确','李存纪']:claim('person',people[name],'death_year',f'{name}于926年被密遣之人杀于民间。',7,span(7,'通王存确','乃密遣人就田舍杀之。'),'此前逃南山与此实际遇害分录，未补确日。')
E=ev('siyuan_rebukes_an_after_princes_death','二王遇害一月有余后，监国得知，责安重诲并哀惜',7,'后月馀','伤惜久之。',[('监国','后来得知并责备者'),('安重诲','受责者')],when='二王遇害后一月有余，据926年本段追记，确日未载',place='后唐朝廷',note='不得硬写与乙未同日；此为主所述事后反应，不据此证明此前实际不知的心理事实。')
E=ev('liu_cunwo_flee_jinyang_affair_report','刘后与李存渥奔晋阳，主书记途中私通',7,'刘皇后与申王','在道与存渥私通。',[('刘皇后','奔晋阳及书载私通者'),('存渥','同奔及书载私通者')],when='926年四月洛阳兵变后出逃途中',place='洛阳至晋阳路',note='私通为史载指控式叙述，非现代可独立验证私生活；不建立夫妻或正式婚姻边。')
claim('event',E,'description','新家人传也记刘后与存渥在道奸、到太原为尼。',7,'在道與存渥姦，及至太原，乃削髮為尼。','同一书载叙述补证，不因两书相同就断为独立确证；为尼另录。',source='xinwudaishi-014-926-liu-flight',relation='corroborates')
E=ev('cunwo_refused_jinyang_killed_fenggu','李存渥至晋阳被符彦超拒纳，逃至凤谷，被部下杀害',7,'存渥至晋阳','为其下所杀。',[('存渥','被拒入城、逃后被杀者'),('李彦超','拒纳者')],when='926年四月刘后同奔之后叙次，确日未载',place='晋阳、凤谷',note='不把拒纳直接等同符彦超下令部下杀；其下按存渥部下理解，执行者未名。凤谷原名未核现代坐标。')
claim('person',people['李存渥'],'death_year','李存渥于926年出逃后被其部下杀害。',7,span(7,'存渥至晋阳','为其下所杀。'),'主明确此段实杀，不提前写成第一批出宫即死。')
claim('event',E,'description','旧宗室传也记申王庄宗败后与刘后奔太原，被部下所杀。',7,'莊宗敗，與劉皇后同奔太原，為部下所殺。','只取正文，不拿同快照通鉴注当独立书证。',source='jiuwudaishi-051-926-cunwo',relation='corroborates')
E=ev('cunba_seeks_monk_refuge_killed','李存霸到晋阳兵已散尽，剃发求为僧；符彦超欲奏请处置，军士不听杀于碑下',7,'明日，永王存霸','杀之于府门碑下。',[('存霸','求僧服庇护后被杀者'),('李彦超','拟请奏、未能阻军士者')],when='李存渥至晋阳之后次日，926年四月叙次',place='晋阳府门碑下',note='不得将符彦超说当奏改成本人下令诛；日承前存渥到晋阳，不凭前逃离河中段庚寅自行算日。')
claim('person',people['李存霸'],'death_year','李存霸于926年到晋阳后被军士杀害。',7,span(7,'明日，永王存霸','杀之于府门碑下。'),'未造具体军士姓名。')
E=ev('liu_becomes_nun_executed','刘后在晋阳为尼，监国遣人将她杀害',7,'刘皇后为尼','监国使人就杀之。',[('刘皇后','为尼后被杀者'),('监国','遣人执行者')],when='926年四月主书诸王出逃段叙次，确日未载；新置明宗入立后',place='晋阳',note='原明确监国遣人，保留责任主体；不可因上段二王案不知而推此案也由安擅杀。各书阶段差别分引。')
claim('person',people['刘夫人（李存勖妻）'],'death_year','刘皇后于926年为尼后被李嗣源遣人杀害。',7,span(7,'刘皇后为尼','监国使人就杀之。'),'主监国阶段与新入立叙法并存，不补确日。')
claim('event',E,'time_original','新家人传置刘后被赐死于明宗入立后。',7,'明宗入立，遣人賜后死。','入立与主监国阶段不同，不能静默当同日同称谓。',source='xinwudaishi-014-926-liu-flight',relation='conflicts')
E=ev('cunli_young_sons_missing','李存礼及庄宗四幼子在乱中不知所终',7,'薛王存礼','遭乱皆不知所终。',[('存礼','失去后续消息的薛王'),('继嵩','失去消息幼子'),('继潼','失去消息幼子'),('继蟾','失去消息幼子'),('继峣','失去消息幼子'),('庄宗','四幼子之父')],when='926年四月乱后主书追记，确日未载',place='后唐乱中，各人具体去向未载',note='不知所终绝非全部已经死亡，不填四幼子死亡年；主继蟾继峣无顿号据两史明确名单拆二人。')
for child in ['继嵩','继潼','继蟾','继峣']:relationship('庄宗',child,'父亲',7,'庄宗幼子继嵩、继潼、继蟾继峣','李存勖是该幼子的父亲，母亲主未载，新传明说四人母名不著，不能统一推刘后。')
claim('event',E,'description','旧宗室传列繼潼、繼嵩、繼蟾、繼嶢为庄宗子，败后不知所终。',7,'繼潼、繼嵩、繼蟾、繼嶢並莊宗子，同光三年拜光祿大夫、檢校司徒，未封。莊宗敗，並不知所終。','只取正文；原注清异录后续走蜀暂不在本阶段新增。嶢展示峣。',source='jiuwudaishi-051-926-young-princes',relation='corroborates')
claim('event',E,'description','新家人传列庄宗五子，继岌之外四人母名号皆不著。',7,'莊宗五子：長曰繼岌，其次繼潼、繼嵩、繼蟾、繼嶢。繼岌母曰劉皇后，其四皆不著其母名號。','补父子名单，不以长子母亲当四幼子母亲，也不强建四人的长幼边。',source='xinwudaishi-014-cunxu-five-sons',relation='adds')
E=ev('cunmei_survives_with_paralysis','李存美因病风偏枯得免，居晋阳',7,'惟邕王存美',None,[('存美','病中幸存的邕王')],when='926年四月乱后主书记述，确日未载',place='晋阳',note='病风偏枯保留历史症状，不作现代医学诊断；得免仅当前未遇害，不推长寿或最终死年。')
claim('event',E,'description','新家人传同记存美素病风、居太原，另称其最终不知所终。',7,'存美素病風，居太原，與存禮皆不知其所終。','新末去向不明与主当时得免可分时理解，不认作926必死。',source='xinwudaishi-014-926-cunmei',relation='adds')
E=ev('xu_gao_value_advisers_after_cunxu_death','徐温、高季昌闻庄宗遇害，更看重严可求、梁震',8,'徐温','益重严可求、梁震。',[('徐温','更重严可求者'),('高季兴','更重梁震者'),('严可求','吴受重顾问'),('梁震','荆南受重顾问')],when='926年四月庄宗遇害消息传到之后',place='吴、荆南',note='前主两地谏论上下文据各自主顾对应，不造徐温与梁震直接任用关系；益重为作者记，不补官职。')
E=ev('liang_recommends_sunguangxian','梁震向高季昌推荐孙光宪，孙获掌书记',8,'梁震荐','使掌书记。',[('梁震','推荐者'),('光宪','前陵州判官、贵平人、获职者'),('季兴','接纳任用者')],when='926年四月主书本段叙次，确日未载',place='荆南',note='主以高季昌为受荐者；宋传高从诲见重署从事另段，不硬合为同次任命。')
claim('person',people['孙光宪'],'description','宋史记孙光宪字孟文、陵州贵平人。',8,'孫光憲字孟文，陵州貴平人。','只取字、籍补证，不提前录宋传后来的纳土、黄州刺史及死亡。',source='songshi-483-sunguangxian',relation='adds')
claim('event',E,'description','宋本传另述游荆渚时高从诲见重、署为从事。',8,'遊荊渚，高從誨見而重之，署為從事。','与主梁震荐于高季昌任掌书记的受荐者、官称不同，时间未给，不合成926同次任命。',source='songshi-483-sunguangxian',relation='conflicts')
E=ev('sun_dissuades_gao_attack_chu','高季昌造战舰拟攻楚，孙光宪以民力与他国乘隙风险劝阻，高停止',8,'季兴大治',None,[('季兴','拟攻后听劝停止者'),('光宪','谏止者')],when='926年四月孙掌书记之后主书叙次',place='荆南、拟攻楚',note='欲攻不是实际出兵；他国乘弊是孙的风险预测，不造他国已入侵事件。')
E=ev('yuan_executed_and_original_name_restored','元行钦被送至洛阳，与监国对质后被斩，恢复原姓名',9,'戊戌',None,[('李绍荣','到洛对质、被斩及恢复姓名者'),('监国','责问、下令者')],when='926年四月戊戌据主书；他书纪日叙次有别',place='洛阳',note='吾儿指前批李从璟，但此段不给重复死亡事件；先帝何负是元回话而非客观责任判定。')
claim('person',people['元行钦'],'death_year','元行钦于926年被斩于洛阳。',9,Q[9]['text'],'前平陆被执与此实斩分开。')
claim('event',E,'description','新元传同记双方对答、洛阳市斩，补市人为之流涕。',9,'明宗見之，罵曰：「我兒何負於爾！」行欽瞋目直視曰：「先皇帝何負於爾！」乃斬于洛陽市，市人皆為之流涕。','市人皆流涕为新作者概括，不扩大成全民支持；原儿指李从璟，不生新关系。',source='xinwudaishi-025-926-yuan-executed',relation='adds')
claim('event',E,'time_original','旧明宗纪置元行钦伏诛于财政奏议之后的“是日”。',9,'是日，宋州節度使元行欽伏誅。','承前段庚子叙次但本句未单具干支，与主戊戌有别，未核纸本不强定同日。',source='jiuwudaishi-035-926-fiscal-and-yuan',relation='conflicts')
claim('event',E,'time_original','新明宗纪将杀元行钦与孔谦置乙未任安重诲之后同段。',9,'乙未，中門使安重誨為樞密使。殺元行欽及租庸使孔謙。','不把新省略日与主戊戌强统一；两史书事件排列差保留。',source='xinwudaishi-006-926-regency',relation='conflicts')
E=ev('shi_appointed_shanzhou_guard_returning_army','监国担心征蜀军返后生变，任石敬瑭为陕州留后',10,'监国恐','以石敬瑭为陕州留后；',[('监国','任命者'),('敬瑭','陕州留后受任者')],when='926年四月己亥前后主叙次；旧明宗纪记己亥',place='陕州',note='恐为监国忧虑，不当返师已叛；留后不等正式节度。')
claim('event',E,'time_original','旧明宗纪己亥任石敬瑭权知陕州兵马留后。',10,'己亥，命石敬瑭權知陝州兵馬留後，','旧补确日与权知称，主本前句无确日，不把主后句己亥无条件移给前句。',source='jiuwudaishi-035-926-appointments-fiscal',relation='adds')
E=ev('congke_appointed_hezhong','监国任李从珂为河中留后',10,'己亥',None,[('监国','任命者'),('李从珂','留后受任者')],when='926年四月己亥据主书',place='河中',note='旧明宗纪河南府兵马留后与主河中不同，独立异说，不悄改方镇。')
claim('event',E,'description','旧明宗纪记李从珂权知河南府兵马留后。',10,'皇子從珂權知河南府兵馬留後。','主河中/旧河南府异文并存；旧称皇子为本纪视角，不补此时已册皇子事实。',source='jiuwudaishi-035-926-appointments-fiscal',relation='conflicts')
E=ev('zhangjuhan_granted_retirement','张居翰请求归田，获准',11,'枢密使张居翰','许之。',[('张居翰','请求归田的枢密使'),('监国','准许者')],when='926年四月本段叙次，确日未载',place='洛阳朝廷',note='不提前录天成三年卒；归田不推所有宦官同时免诛。')
claim('event',E,'description','新张居翰传记庄宗遇害后于至德宫见明宗、求归田里。',11,'莊宗遇弒，居翰見明宗於至德宮，求歸田里。','补面见地点与动作，不取后928死亡提前纳本事件。',source='xinwudaishi-038-926-zhangjuhan',relation='adds')
E=ev('huyanwei_recommends_kong_privy','霍彦威荐孔循，孔获任枢密副使',11,'李绍真屡荐','以循为枢密副使。',[('李绍真','屡荐者'),('循','枢密副使受任者'),('监国','任命者')],when='926年四月庚子据主书',place='洛阳',note='副使与下段壬寅正使分开，未提前升正。')
claim('event',E,'description','旧明宗纪同记孔循由权知汴州任枢密副使。',11,'以權知汴州軍州事孔循為樞密副使，','本条承旧庚子叙次，单引实际官职不提前正使。',source='jiuwudaishi-035-926-appointments-fiscal',relation='corroborates')
E=ev('lishaohong_requests_ma_surname','李绍宏请求恢复马姓',11,'李强宏','李强宏请复姓马。',[('李强宏','请求复姓者')],when='926年四月本段叙次，确日未载',place='后唐朝廷',note='主强宏疑绍宏，依新宣徽使马绍宏曾赐李姓及前朝同职校复用李绍宏，不新建强宏；请复尚无准许文字，不写已允。')
claim('person',people['李绍宏'],'description','新宦者传明载宣徽使马绍宏曾被赐姓李。',11,'有宣徽使馬紹宏者，嘗賜姓李，頗見信用。','主强宏疑字，沿此前李绍宏稳定key，马绍宏只作历史名校证，不重复人物。',source='xinwudaishi-038-mashaohong',relation='adds')
E=ev('kongqian_executed_under_charges','监国列举孔谦侵刻军民等罪并处决他',11,'监国下教','之罪而斩之，',[('监国','宣罪及处决者'),('孔谦','租庸使、被斩者')],when='926年四月庚子段叙次；旧明宗纪庚子',place='后唐朝廷',note='奸佞侵刻为监国教令指控，不当现代法院独立判定；主实斩可确，旧特贷全家不扩为族诛。')
claim('person',people['孔谦'],'death_year','孔谦于926年被监国李嗣源处决。',11,span(11,'监国下教','之罪而斩之，'),'本段实斩，非此前请求查库。')
claim('event',E,'description','旧明宗纪孔谦敕记贷全家、籍没田宅，随后伏诛。',11,'雖犯眾怒，特貸全家，所有田宅，並從籍沒。」是日，謙伏誅。','补处置范围，不把贷全家误作全族被杀。',source='jiuwudaishi-035-926-appointments-fiscal',relation='adds')
E=ev('abolish_kongqian_levies_restore_three_commissions','监国废孔谦苛敛法、租庸使及内勾司，恢复盐铁户部度支，令一宰相专判',11,'凡谦所立','委宰相一人专判。',[('监国','制度与法令发令者'),('孔谦','被废征敛法的原立者')],when='926年四月孔谦处决之后主书叙次',place='后唐中央财政及诸道',note='宣布皆罢不证各地已全部执行；恢复三司不等即设置专职三司使，新传后任另时勿提前。')
claim('event',E,'description','旧明宗纪明确专判三司者为豆卢革。',11,'敕停租庸名額，依舊為鹽鐵、戶部、度支三司，委宰臣豆盧革專判。','主未名的宰相据旧补名；不改主对应具体表述。',source='jiuwudaishi-035-926-appointments-fiscal',relation='adds')
claim('event',E,'description','新三司叙述记明宗废租庸职，以大臣一人判三司。',11,'明宗入立，誅租庸使孔謙而廢其使職，以大臣一人判戶部、度支、鹽鐵，號曰判三司。','新入立概述与主监国阶段称不同，不提前取延朗其后专职三司使任命。',source='xinwudaishi-026-three-commissions',relation='adds')
E=ev('abolish_monitors_order_eunuchs_killed','监国废诸道监军使，并命各道诛杀宦官',11,'又罢诸道',None,[('监国','废监军、命诛发令者')],when='926年四月废租庸制度之后主书叙次',place='后唐诸道',note='庄宗由宦官亡国为本书所记决策理由，不当历史唯一因果；命尽杀是诏令，未视所有宦官已在本段被杀。')
E=ev('congxi_persuades_jiji_turn_east','李继岌退至武功，李从袭劝他东行救内难，魏王采纳',12,'魏王继岌','继岌从之。',[('继岌','退军、采劝者'),('从袭','劝东行者')],when='926年四月辛卯兴平退军之后叙次，确日未载',place='兴平至武功',note='退不如进为李判断，东行救难意图不等已解京城之围；与上批谋凤翔阶段接续。')
claim('event',E,'description','新魏王传同记至武功时李从袭劝驰京师救内难。',12,'至武功，李從襲勸繼岌馳趣京師，以救內難。','同人同地同转向补证，不另建同一次劝说。',source='xinwudaishi-014-926-jiji-death',relation='corroborates')
E=ev('zhangjian_cuts_bridge_jiji_to_weinan','张篯断渭水浮桥，魏王沿水浮渡至渭南，吕知柔等腹心已逃',12,'还，至渭水','皆已窜匿。',[('继岌','遭断桥、至渭南者'),('张篯','权西都留守、断桥者'),('吕知柔','已窜匿腹心')],when='926年四月东返武功后叙次，确日未载',place='渭水、渭南',note='篯/籛按繁简字形匹配同权西都留守，另于既有张筠，不因同官混人；原未载张断桥具体动机。')
claim('event',E,'description','新魏王传记西都留守名张籛，断桥后魏王循河东至渭南、左右潰。',12,'行至渭河，西都留守張籛斷浮橋，繼岌不得度，乃循河而東，至渭南，左右皆潰。','张籛/张篯同名繁简，主浮渡与新不得度循河的行军叙法有别，原文分存。',source='xinwudaishi-014-926-jiji-death',relation='adds')
E=ev('jiji_orders_lihuan_strangle_him','李从袭称时事已去，李继岌流泪伏床，命李环缢杀自己',12,'从袭谓继岌','命仆夫李环缢杀之。',[('继岌','命自杀并被缢者'),('从袭','劝其自图者'),('李环','奉命执行缢杀的仆夫')],when='926年四月主本段无确日；新明宗纪记壬子薨',place='渭南',note='具体缢杀由本人命仆执行，不简单改为李环擅害或李从袭直接亲杀；新纪时间独立。')
claim('person',people['李继岌'],'death_year','李继岌于926年在渭南命李环缢杀自己。',12,span(12,'从袭谓继岌','命仆夫李环缢杀之。'),'其从前魏王与当前死者复用稳定主体。')
claim('event',E,'description','新魏王传详李环迟疑、与乳母言说，魏王面榻而卧后被缢。',12,'環遲疑久之，謂繼岌乳母曰：「吾不忍見王，王若無路求生，當踣面以俟。」繼岌面榻而臥，環縊殺之。','乳母无名不补名；只补缢杀动作，不提前取新传后葬华州及任军到京。',source='xinwudaishi-014-926-jiji-death',relation='adds')
claim('event',E,'time_original','新明宗纪记壬子魏王继岌薨。',12,'壬子，魏王繼岌薨。','新置丙午即位以后，主本段无日，不能从主排列推出确定辛丑前死亡。',source='xinwudaishi-006-926-regency',relation='adds')
E=ev('renhuan_takes_army_east','任圜接掌征蜀军东行',12,'任圜代将','任圜代将其众而东。',[('圜','代掌东行军者')],when='926年四月魏王死后叙次，确日未载',place='征蜀军东归路',note='此句在前一导出块，独立引证；东行不等已经到洛阳。')
E=ev('shi_soothes_returning_army','监国命石敬瑭慰抚返军，书称军士无异言',12,'监国命石','军士皆无异言。',[('监国','命慰抚者'),('敬瑭','慰抚受令者')],when='926年四月魏王死、任圜代军后叙次，确日未载',place='征蜀军东归路，慰抚具体地点未载',note='本句在下一导出块，未拼原文；无异言为书载此时反应，不推军队永不叛。')
E=ev('lichong_assigned_huazhou_monitor','监国此前命亲近者李冲任华州都监，应接征蜀军',12,'先是，监国','应接西师。',[('监国','派任者'),('李氵中','受命华州都监')],when='926年四月接西师前追叙，确日未载',place='华州',note='氵中为冲字拆录，展示李冲（华州都监）；不并既有李再丰之子李冲，也不并温韬赐名李绍冲。')
E=ev('lichong_forces_hua_prefect_to_court','李冲擅迫华州节度使史彦镕入朝',12,'氵中擅逼','史彦镕入朝；',[('李氵中','擅逼入朝者')],when='926年四月任华州都监后叙次',place='华州至洛阳朝廷方向',note='史彦镕与既有史敬镕及旧史敬熔同华州职，但未获明确异名证，本事件保留主姓名，暂不新建或强合其主体。擅为主判断，不推监国授意。')
E=ev('lichong_kills_licunjing_family','同州节度使李存敬过华州，被李冲杀害并及其家',12,'同州节度使李存敬','并屠其家；',[('李存敬','过华州被杀者'),('李氵中','杀人及屠家者')],when='926年四月李冲华州处置期间，确日未载',place='华州',note='屠其家原范围无人数及名单，不造全族人口；与旧史其他存姓义子暂不添亲属。')
E=ev('lichong_kills_congxi','李冲又杀西川行营都监李从袭',12,'又杀西川行营','李从袭。',[('李氵中','杀害者'),('从袭','被杀行营都监')],when='926年四月魏王死后华州处置叙次，确日未载',place='华州',note='魏王死时李从袭尚活，此处才实杀，未把魏王与他同时死。')
claim('person',people['李从袭'],'death_year','李从袭于926年被李冲（华州都监）杀害。',12,span(12,'又杀西川行营','李从袭。'),'主实杀确立年，不补确日。')
E=ev('an_reinstates_hua_prefect_recalls_chong','史彦镕向安重诲哭诉，安遣其还镇、召李冲归朝',12,'彦镕泣诉','召氵中归朝。',[('安重诲','遣还节度使、召都监者'),('李氵中','被召者')],when='926年四月李冲擅处置后叙次',place='洛阳朝廷、华州',note='史彦镕身份疑点延续，事件中保留主名但不强并；召归不等在此被处死。')
E=ev('huyanwei_directs_business','主书记李嗣源入洛后内外机事皆决于霍彦威',12,'自监国入洛','皆决于李绍真。',[('监国','入洛的监国'),('李绍真','主所述机事决策者')],when='926年四月入洛以后的一段时期概述',place='洛阳朝廷',note='皆决为史作者概括，不补枢密使等正式新官职；霍即赐名李绍真。')
E=ev('huyanwei_imprisons_wen_duan','霍彦威擅捕段凝、温韬入狱，拟杀',12,'绍真擅收','下狱，欲杀之。',[('李绍真','擅捕拟杀者'),('李绍钦','威胜节度使、被拘者'),('李绍氵中','太子少保、被拘者')],when='926年四月监国入洛之后、辛丑教令之前',place='洛阳',note='主李绍氵中即赐名李绍冲的温韬，本段末明复姓名；此处欲杀不等已处死。')
E=ev('an_dissuades_huo_killing_wen_duan','安重诲劝霍彦威勿借梁朝旧罪报私仇，霍稍沮',12,'安重诲谓绍真','绍真由是稍沮。',[('安重诲','劝阻者'),('李绍真','受劝稍沮者')],when='926年四月温段下狱之后、辛丑之前',place='洛阳',note='温段罪恶及专报仇为安言，不当独立审判事实；稍沮不是已彻底解决，后教释放另记。')
E=ev('wen_duan_names_restored_released','监国教温韬、段凝恢复姓名并放归田里',12,'辛丑',None,[('监国','下教恢复姓名与释放者'),('李绍氵中','恢复温韬姓名、获释者'),('李绍钦','恢复段凝姓名、获释者')],when='926年四月辛丑据主书',place='洛阳朝廷至归田之处，具体乡里未载',note='两人复姓名为同人履历，不重复建人；后流放及死在后年留待编年主线。')
claim('event',E,'description','新温韬传同记明宗入洛后与段凝下狱，随后赦归田里。',12,'明宗入洛，與段凝俱收下獄，已而赦之，勒歸田里。','不提前取新后文明年流德州赐死；本句不具赦确日，主辛丑独立保留。',source='xinwudaishi-040-926-wentao-release',relation='corroborates')

review='连续7—12段逐句回查。张延朗女嫁安重诲子建姻亲，婚年未知；诸王寻访、安霍密杀二王、监国后月余责安分时，刘后处决主明确监国责任与新入立阶段各存。存渥被拒后由其下杀不推符彦超下令，存霸军士不听请奏而杀。四幼子与存礼不知所终不写已死，父亲四边以两史名单校，无母证不推刘后。宋孙字孟文贵平补证，主高季昌荐掌书与宋高从诲署从事不合成一次；攻楚为欲且止未造实战。元戊戌斩与旧是日承财政段及新乙未后叙次差各存。石陕主未具日/旧己亥，李从珂主河中/旧河南府保留异说。张归田、孔副使不提前正使；主李强宏据宣徽李赐姓马校复用李绍宏，只有请复不等已准。孔教罪是指控，实斩与贷其家另存；废苛敛三司、诸道尽杀均命令，不冒称各地执行完毕。魏王复东、张篯断桥、至渭南、李环受命缢、任代军及石抚分阶段，新壬子薨单引不由排列定主死日；篯/籛繁简一人不并张筠。李氵中规范冲字独立华州都监，不并既有李再丰子或温韬。史彦镕/史敬镕同华州职未明异名，相关事件存原名暂不建或合主体，留待纸本及同事补证。李存敬与李从袭此处实死，霍捕温段欲杀但后安阻与辛丑放归，不提前后年死。展示简体，原文、快照、疑字不改。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(7,13)],next_paragraph=Q[13]['id'],next_volume=275,supplements=supplements,excluded_non_body=[],coverage='卷275第7—12段，原文件12—17行；监国任命、诸王遇害或不知所终、荆南孙光宪、元实斩、初期财政监军教令、魏王死与返师、李冲擅杀及温段释归。926年110正文段累计55，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(7,13)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
