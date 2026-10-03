# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 929, paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 37))
specs=[
 ('tongjian-276-year-end',YEAR.parent/'year-0928/part-08/sources/library/tongjian-276-year-end','38a68a4c','司马光等'),
 ('jiuwudaishi-040-929-january',P/'sources/library/jiuwudaishi-040-929-january','ea985438','薛居正等'),
 ('jiuwudaishi-040-929-february',P/'sources/library/jiuwudaishi-040-929-february','ea985438','薛居正等'),
 ('jiuwudaishi-040-929-march',P/'sources/library/jiuwudaishi-040-929-march','ea985438','薛居正等'),
 ('jiuwudaishi-054-wangdu-fall',P/'sources/library/jiuwudaishi-054-wangdu-fall','ea985438','薛居正等'),
 ('jiuwudaishi-064-wangyanqiu-soldiers',P/'sources/library/jiuwudaishi-064-wangyanqiu-soldiers','ea985438','薛居正等'),
 ('jiuwudaishi-058-cuixie-death',P/'sources/library/jiuwudaishi-058-cuixie-death','ea985438','薛居正等'),
 ('xinwudaishi-006-929',P/'sources/library/xinwudaishi-006-929','ea985438','欧阳修'),
 ('xinwudaishi-015-licongcan',P/'sources/library/xinwudaishi-015-licongcan','ea985438','欧阳修'),
 ('xinwudaishi-015-mingzong-nephews',ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/part-03/sources/library/xinwudaishi-015-mingzong-nephews','5c38857d','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0929-p001-p008',
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
lines = (ROOT / 'resources/derived/tongjian/276.txt').read_text().splitlines()
for n in range(1, 9):
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
        citation = f'卷276·天成四年（929）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0929_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','从荣':'李从荣','赟':'冯赟','都':'王都','晏球':'杜晏球','王晏球':'杜晏球','王宴球':'杜晏球','从璨':'李从璨','重诲':'安重诲'}
NEW_ALIASES={'马让能':['馬讓能'],'李从璨':['李從璨']}

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

def event(code, title, n, quote, actors, when=None, note='', year=929, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='929年'+('正月' if n==1 else '二月' if n<=6 else '三月')+'本段；确日未载'
    key = 'event_zztj_276_0929_' + code
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
        edge = 'participation_zztj_276_0929_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0929_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
j='jiuwudaishi-040-929-january';f='jiuwudaishi-040-929-february';m='jiuwudaishi-040-929-march';w='jiuwudaishi-054-wangdu-fall';army='jiuwudaishi-064-wangyanqiu-soldiers';c='jiuwudaishi-058-cuixie-death';ann='xinwudaishi-006-929';lc='xinwudaishi-015-licongcan';kin='xinwudaishi-015-mingzong-nephews'
E=ev('fengyun_enters_xuanhui','冯赟入朝为宣徽使',1,'春','宣徽使，',[('赟','由外入朝获任宣徽使者')],place='后唐朝廷',note='与928河东副留守及密奏杨思权案分时点，不凭入字猜具体抵京日。')
claim('event',E,'description','旧明宗纪正月记北京副留守冯赟为宣徽使、判三司。',1,'以北京副留守馮贇為宣徽使、判三司。','本句列壬辰段后、戊戌前，未独具日；判三司是补职，不造新同名冯。',source=j,relation='adds')
E=ev('fengyun_advises_senior_mentor_for_congrong','冯赟向执政称李从荣刚僻轻易，宜选有德望者辅佐',1,'谓执政',None,[('赟','向执政建议者'),('从荣','建议辅导对象')],place='后唐朝廷',note='刚僻轻易为冯评价；宜选是建议未具已任辅佐人，从荣未记在场，不据此造双方为敌边。')
E=ev('wangdu_tunei_failed_breakout','王都、秃馁欲突围逃走而未能出城',2,'王都','不得出。',[('都','欲突围而未出者'),('秃馁','欲突围而未出者')],when='929年正月至二月陷城前；确日未载',place='定州',note='未出为失败结果，不写已逃出城；主列二月纪时前，不能强赋同一陷城干支。')
E=ev('marangneng_opens_dingzhou','定州都指挥使马让能开门纳官军',2,'二月','开门纳官军，',[('马让能','定州都指挥使、开门纳军者')],when='929年二月癸丑（主书）；新纪另作癸卯',place='定州',note='马让能新主体不与宰相杜让能合并；主癸丑、新癸卯不同干支并列，不自行校改或换公历。')
claim('event',E,'time_original','新明宗纪记二月癸卯王晏球克定州。',2,'二月癸卯，王晏球克定州。','主二月癸丑与新癸卯异日，保留底本定位，不择日消除矛盾。',source=ann,relation='conflicts')
claim('event',E,'time_original','旧明宗纪记二月乙巳王晏球奏本月三日收复定州。',2,'二月乙巳，王晏球奏，此月三日收復定州，獲王都首級，生擒契丹托諾等二千餘人。','乙巳是奏报日，三日是其所报收复日，不直接把乙巳当攻城执行日；未用月朔算法强修主字。',source=f,relation='adds')
claim('event',E,'description','旧王都传称马让能降于曲阳门，王都巷战败后回府自焚。',2,'四年三月，晏球拔定州，時都校馬讓能降於曲陽門，都巷戰而敗，奔馬歸於府第，縱火焚之，','补门名与战后退府步骤；旧列传三月与主新及旧帝纪二月不同纪时，保留异说不强三个日期为三次陷城。',source=w,relation='adds')
E=ev('wangdu_family_self_immolation','王都与家族自焚',2,'都举族','自焚，',[('都','自焚者')],when='929年二月癸丑陷城条；旧列传另系三月',place='定州',note='举族不扩为每一亲属无一生还，旧帝纪另载四子一弟后来被处刑，与本句家族范围叙法并列。')
claim('event',E,'description','旧王都传记王都退府纵火，府库妻孥一夕俱烬。',2,'都巷戰而敗，奔馬歸於府第，縱火焚之，府庫妻孥，一夕俱燼，','妻孥俱烬是列传叙法；同书帝纪尚记四子一弟在俘献后被刑，不能概括成现代核实全家无幸存。',source=w,relation='corroborates')
E=ev('tunei_two_thousand_captured','秃馁及契丹二千人被擒',2,'擒秃馁','二千人。',[('秃馁','被擒契丹将')],when='929年二月癸丑陷城条',place='定州',note='主二千、旧二千余叙法照录，不捏造精确名单；托诺、托馁在旧同案叙写匹配秃馁，不推广所有相似姓名为正式别名。')
claim('event',E,'description','旧明宗纪本月乙巳奏报生擒契丹托诺等二千余人。',2,'生擒契丹托諾等二千餘人。','同定州陷落案识别契丹将秃馁，主二千与旧二千余并列；没有都指挥使马的正式别名补写。',source=f,relation='corroborates')
E=ev('wangyanqiu_tianping_jiedushi_shizhong','王晏球为天平节度使，加兼侍中',2,'辛亥','并加兼侍中。',[('晏球','天平节度、兼侍中获任者')],when='929年二月辛亥',place='天平、郓州',note='王晏球沿杜晏球，王宴球疑写不另建实体；与赵德钧并加衔不等两人均为天平节度。')
E=ev('zhaodejun_added_shizhong','赵德钧加兼侍中',2,'辛亥','并加兼侍中。',[('赵德钧','兼侍中获加者')],when='929年二月辛亥',place='幽州',note='并加只指兼侍中，赵原幽州任职由旧纪核，不移任天平。')
claim('event',E,'description','旧明宗纪同项记幽州节度使赵德钧加兼侍中。',2,'幽州節度使趙德鈞加兼侍中。','本句同辛亥授职组，主并加称法相合，不捏造新调镇。',source=f,relation='corroborates')
claim('event','event_zztj_276_0929_wangyanqiu_tianping_jiedushi_shizhong','description','旧明宗纪同日称王晏球由宋州为郓州节度使，加兼侍中。',2,'辛亥，以北面行營招討使、宋州節度使王晏球為鄆州節度使，加兼侍中；','郓州是天平治州，主军与旧州称法相合，不造第二次任命。',source=f,relation='corroborates')
E=ev('tunei_brought_to_daliang','秃馁被送至大梁',2,'秃馁至','大梁，',[('秃馁','被送行在的俘将')],when='929年二月被擒后、处刑前；抵达确日未载',place='定州至大梁',note='原至承被俘送达，不写自愿出使，也不猜押送将姓名。')
E=ev('tunei_executed_market','秃馁在大梁市中被处死',2,'秃馁至',None,[('秃馁','市场处刑对象')],when='929年二月送到大梁后；主未独记日，旧纪同月辛酉处刑条',place='大梁市',note='主斩、旧磔刑叙法不同，标题用处死兼容并在引用保留具体异刑，不自行选定现代执行机制。')
claim('event',E,'description','旧明宗纪辛酉受俘献首后，记王都四子一弟及秃馁父子二人并磔于市。',2,'辛酉，帝御咸安樓受定州俘馘，百官就列，宣露布於樓前，禮畢，以王都首級獻於太社。王都男四人、弟一人，禿餒父子二人，並磔於市。','补时间与处刑对象，主斩与旧磔并列；王亲属姓名未具不造匿名个人，举族自焚不能解为全家所有人都死于火。',source=f,relation='conflicts')
E=event('dingzhou_prisoner_head_presentation','旧明宗纪记李嗣源受定州俘馘、宣露布，王都首级献太社',2,'辛酉，帝御咸安樓受定州俘馘，百官就列，宣露布於樓前，禮畢，以王都首級獻於太社。',[('帝','受俘馘者'),('都','已死后首级被献者')],source=f,when='929年二月辛酉',place='大梁咸安楼、太社',note='王都为死后献首对象，未写本人活着出席；百官和宣读人本句未名不猜。')
E=ev('zhaojingyi_dies','枢密使赵敬怡去世',3,'枢密',None,[('赵敬怡','枢密使、去世者')],place='后唐',note='确日未独具，不能因新简纪挨辛酉献俘就强定同日。')
claim('event',E,'description','新明宗纪本年二月条亦记赵敬怡薨。',3,'趙敬怡薨。','主卒、新薨同人同年，不以不同措辞推两个死亡；仍无独立干支。',source=ann,relation='corroborates')
E=event('zhaojingyi_posthumous_taifu','旧明宗纪记赵敬怡获赠太傅',3,'樞密使趙敬怡卒，贈太傅。',[('赵敬怡','身后赠太傅者')],source=f,when='929年二月卒后；追赠确日未载',place='后唐朝廷',note='死后追赠不是任职在世授官，不用前辛酉献俘日强定。')
E=ev('emperor_leaves_daliang','李嗣源从大梁出发',4,'甲子',None,[('帝','自大梁启程者')],when='929年二月甲子',place='大梁至洛阳途中',note='主发与后至分，不提前本日已到洛阳。')
E=event('emperor_reaches_zhengzhou','旧明宗纪补李嗣源途中到郑州',4,'丙寅，至鄭州。',[('帝','赴洛途中到郑州者')],source=f,when='929年二月丙寅',place='郑州',note='旧途中位置独补，不推与主甲子同一天。')
E=ev('cuixie_dies_xushui','宰相崔协卒于须水',5,'丁卯',None,[('崔协','门下侍郎同平章事、去世者')],when='929年二月丁卯',place='须水',note='主须水与旧须水驿互补，不填现代坐标或将末段别人传中早年评价当确定死因。')
claim('event',E,'description','旧崔协传称天成四年春随驾自夷门还京，至须水驿，中风暴卒。',5,'四年春，駕自夷門還京，從至須水驛，中風暴卒。','中风为旧传病名记载，不补现代影像诊断；夷门汴州地名背景不把该传全部早年故事计新录入。',source=c,relation='adds')
claim('event',E,'time_original','新明宗纪亦记丁卯崔协薨。',5,'丁卯，崔協薨。','同本年二月丁卯互证，不自行公历换算。',source=ann,relation='corroborates')
E=event('cuixie_posthumous_pushe','崔协获追赠尚书仆射',5,'丁卯，宰相崔協卒，詔贈尚書右僕射。',[('崔协','身后赠尚书仆射者')],source=f,when='929年二月卒后追赠，确诏日未独具',place='后唐朝廷',note='旧帝纪右仆射、旧传左仆射为异衔，标题不强择左右，原文两种完整保留。')
claim('event',E,'description','旧崔传记追赠尚书左仆射，谥恭靖。',5,'詔贈尚書左僕射，諡曰恭靖。','同书帝纪右、列传左异称并列，恭靖身后谥不造在世封爵；纸本待核。',source=c,relation='conflicts')
E=ev('emperor_arrives_luoyang','李嗣源到洛阳',6,'庚午',None,[('帝','至洛阳者')],when='929年二月庚午',place='洛阳',note='与甲子发梁、旧丙寅郑州不同时间动作；不是返北都。')
claim('event',E,'time_original','新明宗纪庚午记从汴州返回。',6,'庚午，至自汴州。','至自汴承帝回洛，原不自行换地名字。',source=ann,relation='corroborates')
E=ev('wangyanqiu_rewards_soldiers_no_execution_siege','王晏球围定州期间每日以私财犒士，始攻至克城未戮一卒',7,'王宴球','未尝戮一卒。',[('晏球','以私财犒军、围城期间不戮士卒的主将')],year=None,when='定州始攻至929年陷城的围城期间；本段未独载始攻确日',place='定州城下',note='未戮指未由其刑杀一卒，不等没有士卒战死；私财犒军不算国家军粮总额，王宴球沿杜晏球同人。')
claim('event',E,'description','旧王晏球传记所得禄赐私财尽以飨士、与将校宴饮，初战至拔城不戮一士。',7,'晏球能與將士同其甘苦，所得祿賜私財，盡以饗士，日具飲饌，與將校筵宴，待軍士有禮，軍中無不敬伏。其年冬，平賊。自初戰至於城拔，不戮一士，','补犒士与不刑杀；旧其年冬平贼与主929二月不同纪时，不以此变更主克城日或推无战亡；叙评归于旧史。',source=army,relation='adds')
E=ev('wangyanqiu_march_audience','王晏球入朝',7,'三月','晏球入朝，',[('晏球','入朝者')],when='929年三月辛巳',place='后唐朝廷',note='入朝在克城、外任后，不提前到二月。')
E=ev('emperor_praises_wangyanqiu','李嗣源赞王晏球定州之功',7,'帝美','其功；',[('帝','赞功者'),('晏球','被赞功者')],when='929年三月辛巳',place='后唐朝廷',note='美其功为褒赞，不补具体黄金赏物。')
E=ev('wangyanqiu_apologizes_supply_burden','王晏球只谢久烦粮饷运输',7,'晏球谢',None,[('晏球','就长期馈运负担致谢者')],when='929年三月辛巳',place='后唐朝廷',note='谢久烦馈运是对后勤耗费表达歉意，不误成因克城赔款或说军粮运输从未中断。')
E=ev('licongcan_huangchengshi_prior_tour','李嗣源东巡时，以李从璨为皇城使',8,'帝东巡','皇城使。',[('帝','东巡时委皇城事务者'),('从璨','皇城使获任者')],year=None,when='李嗣源东巡时、929年三月赐死之前；任命确年日本段未独载',place='宫城',note='为本案前事背景，不把本次二月返洛再写为三月新东巡；亲属身份主旧皇子、新侄异说，不建确定父子边。')
claim('person',people['李从璨'],'description','主书记李从璨为皇子、右卫大将军，性刚而不向安重诲屈服。',8,'皇子右卫大将军从璨性刚，安重诲用事，从璨不为之屈。','本批新限定主体，与李从敏从荣等不合并；性刚史述不当现代人格诊断；皇子称法与新侄并列。')
claim('person',people['李从璨'],'description','新唐家人传将李从璨列为明宗四侄之一。',8,'明宗兄弟皆不見于世家，而有姪四人，曰：從璨、從璋、從溫、從敏。','复用既有新亲属出处；与主皇子、旧帝之诸子有分歧，父名及叔伯长幼未明，不建亲父或强定伯叔边。',source=kin,relation='conflicts')
E=ev('licongcan_drunk_mounts_throne','李从璨与客在会节园宴饮，醉后戏登御榻',8,'从璨与','戏登御榻，',[('从璨','宴饮醉登御榻者')],year=None,when='赐死前的会节园宴；确年日未独载',place='会节园',note='戏登不等正式称帝、举兵篡位，宾客未具名不造人物。')
claim('event',E,'description','新从璨传亦记会节园饮酒，醉后戏登御榻。',8,'嘗於會節園飲，酒酣，戲登御榻，','旧主新同案叙事互证，不证明三史彼此完全独立；未提前后来安重诲死后恢复官职。',source=lc,relation='corroborates')
E=ev('anzhonghui_reports_requests_congcan_execution','安重诲奏请诛李从璨',8,'重诲奏','诛之；',[('重诲','奏请诛者'),('从璨','被请诛对象')],year=None,when='李从璨登御榻后、三月丙戌赐死前；奏日未独载',place='后唐朝廷',note='奏请与赐死执行分，主不明帝实时在园场，不造皇帝亲眼见到。')
E=ev('licongcan_given_death','李从璨被赐死',8,'丙戌','赐从璨死。',[('从璨','赐死对象')],when='929年三月丙戌',place='后唐',note='本句赐死为史载结果，未推刀绞药等具体执行方式。')
claim('event',E,'description','旧明宗纪丙戌诏贬皇城使李从璨为房州司户参军，仍令尽命，称帝之诸子。',8,'丙戌，詔皇城使李從璨貶授房州司戶參軍，仍令盡命。從璨，帝之諸子也。','补诏贬职与尽命，令与主赐死叙法互照；不假定李已到房州，亲属仍与新侄异说并列。',source=m,relation='adds')
claim('event',E,'time_original','新明宗纪同记三月丙戌杀侄从璨。',8,'三月丙戌，殺姪從璨。','日与主旧相合，侄字与主皇子、旧诸子异说保留，不反写引用原字。',source=ann,relation='corroborates')
E=ev('hengshan_groups_attack_shaoxhou','横山蛮侵扰邵州',8,'横山',None,[],when='929年三月条，确日未独载',place='邵州',note='原史称横山蛮保留，未具部落将姓名，不推现代民族身份、侵扰兵数或同丙戌日。')
review='卷276连续929年第1—8段、原87—94行。冯正月入宣徽，旧判三司补；劝重德辅从荣为建议、刚僻其评非事实诊断。从荣辅对象非在场。王秃突破失败与二月陷城分；马让能新人与杜让能别，主癸丑新癸卯旧乙巳报三日旧王传三月多种纪时并列，不强一日或三克城。马曲阳门降、王巷败退府自焚补步骤，举族/妻孥不当所有亲属无幸存，旧帝纪四子一弟仍处刑明确留。秃二千/旧二千余分概数，同案托诺托馁辨认不作全正式别名；送梁、刑市分，斩/旧磔叙法并列；旧辛酉俘馘首献社补，王已死首级不在场。辛亥杜晏球天平郓与赵幽州兼侍中分，赵不误任天平。赵敬怡卒确日未知，新邻辛酉不强同日，旧赠太傅身后。甲子离梁、旧丙寅郑州、丁卯崔须水卒、庚午洛阳分，主旧新互核。旧崔中风为古病名不现代诊断，身后仆射旧帝纪右传左并列及恭靖谥，不猜纸本字。围城王每日私财飨士、未戮一卒不是无战死，期间年null本句未具始年日，旧其年冬平贼不同不改主。三月辛巳朝、美功、谢馈运分，赞非物赏，谢为久劳馈运。李从璨新人与其他从字分，主皇子旧诸子新姪四人分歧；不建确定亲父或叔伯边。东巡任皇城前事、宴醉登榻、安请诛确年日null，三月丙戌死有确年；戏登非已称帝或举兵，旧房司户贬不等实际赴任，新后来恢复赠官不提前。横山蛮邵扰独句不强丙戌、不推现代族属。展示简体、原TXT逐字定位保留，纸本异文待核；未读本快照中四月至年底不计完成。'
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=929,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph='zztj-v276-y0929-p009',next_volume=276,next_year=929,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续929年第1—8段、原87—94行；冯入朝、定州陷及俘处、赵崔卒、帝梁郑洛行程、王入朝与李从璨及邵州案。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,9)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
