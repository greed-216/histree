# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 931, paragraphs 31–40."""
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
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'077b3114','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
specs.append(('tongjian-277-931-may',YEAR/'part-03/sources/library/tongjian-277-931-may','52e45d2f','司马光等'))

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-931-may','tongjian-277-931-october']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0931-p031-p040',
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
lines = (ROOT / 'resources/derived/tongjian/277.txt').read_text().splitlines()
for n in range(31, 41):
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
        citation = f'卷277·长兴二年（931）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0931_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','重诲':'安重诲','崇赞':'安崇赞','崇绪':'安崇绪','张氏':'张氏（安重诲妻）','光鄴':'翟光邺','延钧':'王延钧','延政':'王延政','知诰':'李昪','知询':'徐知询','知谏':'徐知谏','武皇':'李克用','突欲':'耶律倍','东丹慕华':'耶律倍','守元':'陈守元'}
NEW_ALIASES={'安崇赞':['安崇贊','安崇讚'],'安崇绪':['安崇緒'],'张氏（安重诲妻）':['阿張（安重誨妻）'],'翟光邺':['翟光鄴','翟光業','翟光业'],'刘澄':['劉澄'],'陈守元':['陳守元'],'徐彦':['徐彥'],'兴盛韬':['興盛韜'],'李进唐':['李進唐']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=931, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='931年'+('闰五月' if n<=32 else '六月' if n<=34 else '本段，月未独载' if n==35 else '九月' if n<=38 else '十月')+'；确日未独载'
    key = 'event_zztj_277_0931_' + code
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
        edge = 'participation_zztj_277_0931_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0931_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive nine paragraphs, chronological facts and independently located supplements.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
leap='jiuwudaishi-042-931-intercalary';jun='jiuwudaishi-042-931-june';sep='jiuwudaishi-042-931-september';oldan='jiuwudaishi-066-an-killed';newan='xinwudaishi-024-an-killed';temple='xinwudaishi-068-baohuang'
ev('an_requests_retirement','安重诲心不自安，上表请致仕',31,'护国节度使','表请致仕；',[('重诲','护国节度使兼中书令、请致仕者')],when='931年闰五月制前；上表确日未载',place='河中',note='心不自安为史述状态，请致仕与制准分，不直接证明反叛。')
E=ev('an_retires_taizi_taishi','后唐制安重诲以太子太师致仕',31,'闰月，庚寅，','制以太子太师致仕。',[('重诲','获准以太子太师致仕者')],when='931年闰五月庚寅',place='后唐、河中')
claim('event',E,'description','旧明宗纪同闰月庚寅制安重诲以太子太师致仕。',31,'閏月庚寅，製河中節度使、檢校太師、兼中書令安重誨可太子太師致仕。','承五月后闰月为闰五月，旧主同日；出镇、致仕与死亡分开。',source=leap,relation='corroborates')
E=ev('an_sons_flee_hezong','安崇赞、安崇绪于父获致仕制当日逃奔河中',31,'是日，','逃奔河中。',[('崇赞','逃奔河中的安重诲之子'),('崇绪','逃奔河中的安重诲之子'),('重诲','二子所奔的父亲')],when='931年闰五月庚寅',place='京师至河中')
claim('event',E,'description','新安传记二子在京宿卫，闻制当日奔父。',31,'重誨子崇緒、崇贊，宿衞京師，聞制下，即日奔其父，','补京师宿卫身份，崇贊与旧崇讚同人，不因赞繁异字拆分。',source=newan,relation='adds')
relationship('重诲','崇赞','父亲',31,'其子崇赞、崇绪逃奔河中。','安重诲→安崇赞父亲；未记两子长幼，不编兄长边。')
relationship('重诲','崇绪','父亲',31,'其子崇赞、崇绪逃奔河中。','安重诲→安崇绪父亲；不混安崇阮，不建逆向重复。')
E=ev('licongzhang_huguo','保义节度使李从璋移任护国节度使',31,'壬辰，','为护国节度使；',[('李从璋','由保义转护国节度使者')],when='931年闰五月壬辰',place='陕州至河中')
claim('event',E,'description','旧明宗纪同壬辰记陕州节度使李从璋移镇河中。',31,'壬辰，陝州節度使李從璋移鎮河中。','保义治陕州、护国治河中为军与州称法；李从璋不混李从珂、李从厚。',source=leap,relation='corroborates')
ev('yao_yanchou_sends_hezong','朝廷遣步军指挥使药彦稠率兵赴河中',31,'甲午，','将兵趣河中。',[('药彦稠','步军指挥使、领兵赴河中者'),('重诲','受朝廷防范的河中致仕者')],when='931年闰五月甲午',place='后唐至河中',note='遣将赴是派兵，不当已围安宅；后围宅由李从璋主记。')
ev('an_reacts_sons','安重诲见二子到河中，认为他们受人指使，称将以死徇国',31,'安崇赞等至河中，','夫复何言！”',[('重诲','惊见二子、作出判断者'),('崇赞','到父处者'),('崇绪','到父处者')],place='河中',note='为人所使是安判断，未具幕后人，不凭此建某人已唆使的事实。')
E=ev('an_arrests_sends_sons','安重诲拘执二子，上表送赴京师',31,'乃执二子','表送诣阙。',[('重诲','拘执并上表送二子者'),('崇赞','被父拘送者'),('崇绪','被父拘送者')],place='河中至京师',note='不把拘执送子等同已经到京或父当场杀子。')
claim('event',E,'description','旧纪闰月丁酉载安重诲奏已拘送崇赞、崇绪赴阙。',31,'丁酉，安重誨奏：「男崇讚、崇緒等到州，臣已拘送赴闕。」','旧丁酉是上奏记日；主拘送本句未独日，不强定父拘执恰在丁酉。',source=leap,relation='adds')
ev('envoy_warns_an','中使次日见安重诲恸哭，称有人指其有异志、朝廷已派药彦稠兵',31,'明日，有中使至，','将兵至矣。”',[('重诲','接受中使消息者'),('药彦稠','被中使提及已派兵的将领')],when='931年闰五月二子到后次日；确日未载',place='河中',note='中使未名不造人物；异志为人言，兵至矣在说话中不独证明已完成到达。')
ev('an_denies_rebellion','安重诲向中使否认异志，称劳国家发兵更增己罪',31,'重诲曰：“吾受国怨，','罪益重矣。”',[('重诲','向中使否认异志者')],place='河中',note='保留当事人自辩出处，不当独立判定全部相关指控真伪的司法结论。')
ev('an_sons_jailed_shan','安崇赞等行至陕州，被诏系狱',31,'崇赞等至陕，','有诏系狱。',[('崇赞','行至陕州被系者'),('崇绪','同拘送途中被系者')],place='陕州',note='前乃执二子承主语；未已经到京再关河中，新传行至陕州下狱同证。')
E=ev('di_inspects_an_conditional_order','李嗣源遣皇城使翟光邺赴河中察安重诲，命若有异志则诛',31,'皇城使翟光鄴','则诛之。”',[('光鄴','受遣察安的皇城使'),('帝','下有条件诛杀命令者'),('重诲','受察者')],place='后唐至河中',note='素恶为主史述旧情不编确年；果有异志则诛为条件命令，不当已证谋反。')
claim('event',E,'description','新安传作翟光业，受命视安去就，有异志则与从璋图之。',31,'明宗又遣翟光業至河中，視重誨去就，戒曰：「有異志，則與從璋圖之。」','光業与主光鄴同使职、同使命、同从璋处置识别同人；显示翟光邺，原文不改。',source=newan,relation='corroborates')
E=ev('licongzhang_surrounds_an','翟光邺至河中后，李从璋以甲士围安重诲宅第',31,'光鄴至河中，','围其第，',[('光鄴','已抵河中的察使'),('李从璋','率甲士围宅者'),('重诲','被围宅者')],place='河中安重诲第',note='翟到与李率兵围为主动作，不指定药兵实际参与围宅。')
claim('event',E,'description','旧安传亦记翟到、李从璋率甲士围安宅。',31,'既至，李從璋自率甲士圍其第，','旧传承翟使河中，与主对应，不再创建第二场围宅。',source=oldan,relation='corroborates')
ev('licongzhang_bows_an_returns','李从璋入宅庭下拜安重诲，安降阶答拜',31,'自入见重诲，','降阶答拜，',[('李从璋','入庭拜者'),('重诲','下阶答拜者')],place='河中安重诲第',note='仪礼动作与随即杀人分，不把拜仪当真实政治和解。')
E=ev('licongzhang_kills_an','李从璋奋挝击安重诲头部，将其杀死',31,'从璋奋挝','击其首；',[('李从璋','挥挝击首杀人者'),('重诲','被击首杀死者')],when='931年闰五月；己亥奏诏之前，确日未载',place='河中安重诲第',note='己亥是奏至后诏记日，不将此句确日自动定己亥；原未将药彦稠设行刑人。')
claim('event',E,'description','新安传记李从璋乘安重诲答拜时击其首，夫妻皆死。',31,'重誨降而答拜，從璋以檛擊其首，','主挝、新檛、旧楇原字保留，不武断换为剑刺。',source=newan,relation='corroborates')
E=ev('licongzhang_kills_an_wife','安重诲妻张氏惊救，亦被李从璋挝杀',31,'妻张氏惊救，','亦挝杀之。',[('张氏','救夫时被杀者'),('李从璋','杀张氏者'),('重诲','张氏救护的被杀丈夫')],when='931年闰五月；安被击时，确日未载',place='河中安重诲第',note='张氏用丈夫消歧，不混其他张氏；原救动作与遭杀承接。')
claim('event',E,'description','新安传记妻走抱安而呼，亦被击首，夫妻皆死。',31,'重誨妻走抱之而呼曰：「令公死未晚，何遽如此！」又擊其首，夫妻皆死，','妻相救及死亡补证；阿张名形由旧纪另一条事实引用，不凭姓猜具体名。',source=newan,relation='corroborates')
claim('person',people['张氏（安重诲妻）'],'description','旧明宗纪诏列安重诲妻阿张及二子赐死。',31,'並妻阿張、男崇讚崇緒等並賜死，其餘親不問。','阿张为旧称，主张氏同夫、同案、同死亡匹配；诏在己亥不掩去主先杀后奏时序。',source=leap,relation='adds')
relationship('张氏','重诲','妻子',31,'妻张氏惊救，亦挝杀之。','张氏→安重诲妻子，明确方向；不建反向重复丈夫边。')
E=ev('an_posthumous_accusation','安遇害奏至，朝廷己亥诏列罪，并称其欲击淮南图兵柄、遣人携二子归镇',31,'奏至，己亥，','遣元随窃二子归本道；',[('重诲','被诏列罪者'),('孟知祥','诏中被称受离间者'),('董璋','诏中被称受离间者'),('钱镠','诏中被称受离间者'),('崇赞','诏中所称窃归之子'),('崇绪','诏中所称窃归之子')],when='931年闰五月己亥',place='后唐',note='列罪、又诬为主书对诏的叙述；不把指控直接立为安确谋反、私募兵或指使子逃的实体事件。诏书所言与安前自辩并存。')
claim('event',E,'description','旧明宗纪作已亥诏削安官爵，令夫妻及二子赐死，其余亲不问。',31,'已亥，詔安重誨宜削奪在身官爵，','已/己原字保留，主己亥作日读；旧诏令赐死与主夫妻先被杀后奏叙法区别，不改底本。',source=leap,relation='adds')
E=ev('an_sons_executed','朝廷诛安崇赞、安崇绪',31,'并二子诛之。',None,[('崇赞','被诛的安重诲之子'),('崇绪','被诛的安重诲之子')],when='931年闰五月己亥诏后；行刑确日未独载',place='后唐',note='二子在陕系狱后诛；原未载处死地点，不将陕州推定为刑场，亦不说被父杀。')
claim('event',E,'description','新安传亦记并杀二子，其余子孙皆免。',31,'并殺其二子，其餘子孫皆免。','明确二子与其他子孙处置不同，不渲染全族尽杀。',source=newan,relation='adds')
ev('envoys_return_two_chuan','李嗣源遣西川进奏官苏愿、东川军将刘澄还本道，谕安重诲专命兴兵已伏辜',32,'丙午，',None,[('帝','遣使归本道传谕者'),('苏愿','西川进奏官、奉遣归者'),('刘澄','东川军将、奉遣归者'),('重诲','被谕旨归责的已死者')],when='931年闰五月丙午',place='后唐至西川、东川',note='谕旨归责安专命，不把此前伐川全部命令独证为伪造；奉遣与后来成都抵达分。刘澄不混同姓柳或吴将刘彦。')
E=ev('licongke_xidu_liushou','李从珂复同平章事，任西都留守',33,'六月，',None,[('李从珂','复同平章事、任西都留守者')],when='931年六月乙丑',place='西都')
claim('event',E,'description','旧明宗纪同乙丑记李从珂加同平章事，行京兆尹、充西都留守，依前检校太傅。',33,'乙丑，以皇子左衛大將軍從珂依前檢校太傅，加同平章事、行京兆尹，充西都留守。','加与主复为同任叙法，兼京兆尹补；前左卫在三月已录不重复。',source=jun,relation='adds')
E=ev('equalize_land_tax','朝廷命诸道均民田税',34,'丙子，',None,[],when='931年六月丙子',place='后唐诸道',note='均税是诏令，不是已全国丈量完成或税率完全一致。')
claim('event',E,'description','旧诏要求观察使以有力户出剩田亩补贫下不迨顷亩，排改检括，自今年起为定额。',34,'丙子，詔諸道觀察使均補苗稅，將有力人戶出剩田畝，補貧下不迨頃畝，有嗣者排改檢括，自今年起為定額。','旧诏具体措辞补，保留有嗣者原字不猜改；这是调整田税编额，不直接证明重新分田或现代累进税。',source=jun,relation='adds')
E=ev('min_builds_baohuang_palace','陈守元、徐彦、兴盛韬诱王延钧建宝皇宫，土木极盛',35,'闽王延钧', '极土木之盛，',[('延钧','好神仙之术、建宫的闽王'),('陈守元','道士、劝建宫者'),('徐彦','巫者、劝建宫者'),('兴盛韬','巫者、劝建宫者')],place='闽',note='神仙术为信仰及诱导叙述，不当神谕真实；本段年内未独月，造宫费用未具数字。')
claim('event',E,'description','新闽世家亦记陈守元以左道见信，建宝皇宫以居。',35,'鏻好鬼神、道家之說，道士陳守元以左道見信，建寶皇宮以居之。','新在长兴三年后连叙，不将宫建设确日强改931或932；当前补同宫与道士身份，后逊位称帝、六十年预言待连续主段不提前。',source=temple,relation='corroborates')
ev('chenshouyuan_palace_head','王延钧以陈守元为宝皇宫宫主',35,'以守元',None,[('延钧','任命宫主者'),('守元','获任宝皇宫宫主者')],place='闽宝皇宫',note='宫主为宗教宫观职，不混宫廷内侍或另立一国。')
E=ev('bei_named_lizanhua','东丹慕华获更赐姓名李赞华',36,'秋，九月，',None,[('东丹慕华','更赐李赞华姓名者')],when='931年九月己亥',place='后唐',note='原东凡慕华疑字依前文同赐名东丹及旧同日对应识耶律倍；保留原东凡，不造东凡人物。')
claim('event',E,'description','旧明宗纪同己亥记怀化军节度使东丹慕华更赐李讚华，改封陇西县开国公。',36,'己亥，懷化軍節度使東丹慕華賜姓名李讚華，改封隴西縣開國公。','赞/讚统一展示而原文保留；旧补封爵，耶律倍稳定主体，无新李赞华重复人物。',source=sep,relation='adds')
claim('person',people['耶律倍'],'name','耶律倍在后唐先称东丹慕华，本次更赐李赞华。',36,'更赐东凡慕华姓名曰李赞华。','同人名号历史作为引用记录；东凡疑字由旧东丹同日同姓名核对，不改TXT。')
ev('xuzhijian_dies','吴镇南节度使、同平章事徐知谏卒',37,'吴镇南节度使、','徐知谏卒；',[('知谏','去世的镇南节度使同平章事')],place='吴镇南',note='本句无独干支，九月承上，不按后句辛丑给死亡定日。')
ev('xuzhixun_takes_zhennan','吴以徐知询代徐知谏任镇南节度使，赐东海郡王爵',37,'以诸道副都统、','东海郡王。',[('知询','诸道副都统镇海节度使、代镇南并获爵者'),('知谏','被继任的已故节度使')],place='吴镇南',note='守中收令原疑字留，展示中书令不新增孤官；代之据前镇南任，不将原镇海同时判废除。')
E=ev('xuzhijian_helped_summon_xun','徐知诰召徐知询入朝时，徐知谏参与其谋',37,'徐知诰之召','知谏豫其谋。',[('知诰','原召入朝者'),('知询','原被召入朝者'),('知谏','参与召询谋者')],when='追叙929年已录徐知询入吴朝；本句未独年',year=None,stable_key='event_zztj_276_0929_xuzhixun_enters_wu_court',note='与929入朝稳定事件补连，原事件年份保留929；知谏参与为当前追叙新证，不新造931又召一场。')
ev('xuzhixun_mourns_jian','徐知询途中遇徐知谏丧，抚棺哭诉弟用心如此，何面见先王',37,'知询遇其丧于涂，','于地下乎！”',[('知询','途中遇丧抚棺泣语者'),('知谏','丧棺被遇、受泣语的弟弟')],place='吴、途中未详',note='用心如此是徐知询哭诉回应旧谋，不当客观已证明弟害兄；先王本句未名不新建匿名王。')
relationship('知询','知谏','兄长',37,'弟用心如此，我亦无憾，然何面见先王于地下乎！','由徐知询对徐知谏称弟辨长幼，徐知询→徐知谏兄长；不从同徐姓猜共父。')
E=ev('fanyanguang_pingzhang','枢密使范延光加同平章事',37,'辛丑，',None,[('范延光','枢密使、加同平章事者')],when='931年九月辛丑',place='后唐')
claim('event',E,'description','旧纪同辛丑记范延光加同平章事，使如故。',37,'辛丑，樞密使、檢校太傅、刑部尚書範延光加同平章事，使如故。','旧兼检校太傅刑部尚书补；使如故即仍枢密使，不当罢使改纯宰相。',source=sep,relation='corroborates')
E=ev('releases_five_fang_birds','李嗣源敕释放五坊鹰隼，禁内外再进献',38,'辛亥，','内外无得更进。',[('上','敕释鹰隼禁进者')],when='931年九月辛亥',place='后唐五坊',note='放生与禁进为当日敕，不等后世永久禁止全国一切猎事。')
claim('event',E,'description','旧明宗纪同辛亥诏五坊现有鹰隼放归山林，今后不许进献。',38,'辛亥，詔五坊見在鷹隼之類，並可就山林解放，今後不許進獻。','同日敕内容对应，补放归山林；无鸟数不造数字。',source=sep,relation='corroborates')
ev('fengdao_emperor_discuss_hunting','冯道称释放鹰隼为仁及禽兽，李嗣源说明因狩猎损害庄稼而不为',38,'冯道曰：',None,[('冯道','以仁及禽兽称赞者'),('上','以毁稼说明戒猎理由者'),('武皇','被追叙曾随从狩猎的李克用')],place='后唐',note='朕昔猎为无年回忆，作为当次解释引用，不新编931李克用仍在世同行；随武皇狩猎无具体年与地点，不另造年代或作未核产量。')
ev('lijintang_takes_tongzhou','洋州指挥使李进唐攻拔通州',39,'冬，十月，',None,[('李进唐','洋州指挥使、攻通州者')],when='931年十月丁卯',place='通州',note='洋州为其官隶、通州为攻取地点，不混洋州自身被攻陷；不推今日北京通州，坐标未核。')
ev('yanzheng_jianzhou_cishi','王延政任建州刺史',40,'壬午，',None,[('延政','受任建州刺史者')],when='931年十月壬午',place='建州',note='五月遣抚与十月任刺史分；未提前后建殷称帝。')
reviews={31:'请致仕、庚寅制、二子当日奔、壬辰从璋移镇、甲午药遣兵、安惊见判断执送、中使次日传人言、安否认、陕系、翟条件察令、围第拜礼夫妻挝杀、己亥奏诏列罪及二子被诛分别。旧丁酉奏拘送不强设拘执日；主先殺后奏与旧己亥赐死诏并列。主又诬保留指控归属，不当安已独证谋反。安赞讚贊、翟邺鄴業辨同案同人；妻张氏消歧，其他子孙非全族尽诛。',32:'丙午苏刘奉遣归本道，未当已成都东川抵达；专命为谕旨归责不改全伐川命令性质。',33:'六月乙丑从珂复相留守，旧兼京兆尹补，沿养子主体不混从璋。',34:'丙子均税命令，旧均补苗税及田亩编额补，未当已完成重分土地；有嗣者疑字留。',35:'王神仙术、陈徐兴诱建宝皇宫及宫主任命，未当神谕真实；新同宫补但承932后连叙不独定建宫日，后逊位称帝不提前。',36:'九月己亥东凡疑字由旧东丹同授李讚華核耶律倍，原字留；赐李赞华事实与春东丹慕华沿同一主体，旧封爵补。',37:'徐知谏卒、询继镇南赐爵、途中抚棺哭分别，无独卒日不套后辛丑。召询豫谋追叙接929入朝旧事件及参与边，不重造931召。称弟直接支持询兄谏；守中收令疑字留。辛丑范加相使如故仍枢密。',38:'辛亥放五坊鹰隼及禁进，旧山林补；冯仁赞与帝损稼说明为当次对话。昔随武皇为无年回忆，只参与角色注明被谈及，未新建931李克用同行狩猎。',39:'十月丁卯洋州指挥使李进唐拔通州，军隶与攻击地分，历史通州非武断北京通州。',40:'十月壬午延政建州刺史，五月遣抚不同动作，未提前殷政权。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(31,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=931,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(31,41)],next_paragraph='zztj-v277-y0931-p041',next_volume=277,next_year=931,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续931年第31—40段、原93—102行；安致仕二子奔被系夫妻遇害及诏、苏刘遣归、从珂留守、均税、闽宝皇宫、倍更赐名、吴徐兄弟丧、范加相、禁进鹰隼及通州建州政事。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(31,41)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
