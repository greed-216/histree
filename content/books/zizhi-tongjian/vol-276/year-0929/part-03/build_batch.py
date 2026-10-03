# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 929, paragraphs 17–22."""
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
 ('tongjian-276-929-spring-summer',YEAR/'part-02/sources/library/tongjian-276-929-spring-summer','04953b74','司马光等'),
 ('xinwudaishi-051-lirenju-dongzhang',P/'sources/library/xinwudaishi-051-lirenju-dongzhang','0a803f54','欧阳修'),
 ('jiuwudaishi-040-929-june',P/'sources/library/jiuwudaishi-040-929-june','0a803f54','薛居正等'),
 ('jiuwudaishi-040-929-july',P/'sources/library/jiuwudaishi-040-929-july','0a803f54','薛居正等'),
 ('jiuwudaishi-040-929-may',YEAR/'part-02/sources/library/jiuwudaishi-040-929-may','04953b74','薛居正等'),
 ('xinwudaishi-069-gaoconghui-accession',YEAR.parent/'year-0928/part-09/sources/library/xinwudaishi-069-gaoconghui-accession','b2d57128','欧阳修'),
 ('xinwudaishi-061-wu-kingship',ROOT/'content/books/zizhi-tongjian/vol-270/year-0919/part-02/sources/library/xinwudaishi-061-wu-kingship','9e9d8b9a','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-929-spring-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0929-p017-p022',
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
for n in range(17, 23):
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
    ck = f'claim_zztj_276_0929_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','仁矩':'李仁矩','璋':'董璋','重诲':'安重诲','彦珣':'李彦珣','从诲':'高从诲','季兴':'高季昌','殷':'马殷','元信':'安元信','简':'李简','知询':'徐知询','知诰':'李昪','彦忠':'李彦忠'}
NEW_ALIASES={'李彦珣':['李彥珣'],'李彦忠':['李彥忠'],'刘崇俊':['劉崇俊']}

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
    if when is None:when='929年'+('五月' if n<=19 else '六月' if n<=21 else '八月')+'本段；确日未载'
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
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
d='xinwudaishi-051-lirenju-dongzhang';jun='jiuwudaishi-040-929-june';jul='jiuwudaishi-040-929-july';may='jiuwudaishi-040-929-may';gh='xinwudaishi-069-gaoconghui-accession';wu='xinwudaishi-061-wu-kingship'
E=ev('court_requests_sichuan_contributions','李嗣源筹备南郊祭祀，遣李仁矩传诏，要求西川献百万缗、东川五十万缗',17,'帝将','东川五十万缗；',[('帝','筹郊祀并遣诏使者'),('仁矩','客省使、传诏两川者')],place='后唐至两川',note='将祀是筹备不是已祭，今疑令字留原；要求与实际献额分，未把每川都实际献出足额。')
claim('event',E,'description','新董璋传天成四年记诏两川贡助南郊物五十万，李仁矩持安重诲书谕董璋，董只出十万。',17,'天成四年，明宗祀天南郊，詔兩川貢助南郊物五十萬，使李仁矩賫安重誨書往諭璋，璋訴不肯出，秖出十萬而已。','新叙祀南郊、物五十万与主将祀、西川百万东川五十万口径不同原存；新未独给缗单位，不强总额相等或本年已完成郊祭。',source=d,relation='conflicts')
E=ev('sichuan_pleads_military_shortage_pays_less','两川以军用不足辞，西川献五十万缗、东川献十万缗',17,'皆辞','东川献十万缗。',[],place='西川、东川',note='军用不足是两川所陈理由，非现代审计事实；两实际数非朝廷最初请求数。')
claim('person',people['李仁矩'],'description','李仁矩曾为李嗣源藩镇时客将，受安重诲厚待，主书记其恃恩骄慢。',17,span(17,'仁矩，帝','恃恩骄慢。'),'客将为旧生平背景未赋929新任；骄慢为史评，厚待不造永久盟友关系。')
E=ev('dongzhang_invites_lirenju_banquet','董璋在梓州置宴邀请李仁矩',17,'至梓州','置宴召之，',[('璋','设宴邀使者'),('仁矩','受邀者')],place='梓州',note='与后未赴宴分动作，不补宴席日期。')
E=ev('lirenju_ignores_banquet_drinks','李仁矩到中午未赴董璋宴，仍拥妓饮酒',17,'日中','方拥妓酣饮。',[('仁矩','未赴宴而饮者')],place='梓州',note='日中是当天时段，不换现代钟点；妓未名不造人物，不推谁招宴宾人数。')
E=ev('dongzhang_armed_confrontation_lirenju','董璋怒，率持兵部众入驿，责斥李仁矩，引用西川杀李客省事威胁',17,'璋怒','谓我独不能邪！”',[('璋','率兵入驿责使者'),('仁矩','阶下被责使者')],place='梓州驿',note='斩李客省是董话中引既往李严案，不新造929杀李严；本次威胁未等已杀李仁矩。')
E=ev('lirenju_pleads_escapes','李仁矩流泪拜请，得以脱免',17,'仁矩流','仅而得免；',[('仁矩','哭拜求免而获免者')],place='梓州驿',note='得免承董威胁，未死；不补具体交换条件或已正式赦罪。')
E=ev('dongzhang_bribes_lirenju_apology','董璋随后厚赂李仁矩致歉',17,'既而','以谢之。',[('璋','赂使致歉者'),('仁矩','收赂对象')],place='梓州',note='数额未具，不与东川十万贡额混为同一赂款。')
E=ev('lirenju_returns_accuses_dongzhang','李仁矩返回后称董璋不法',17,'仁矩还','言璋不法。',[('仁矩','回朝陈述不法者'),('璋','被指不法对象')],place='梓州至后唐朝廷',note='不法为使者报告，未推正式审判结果或当前已发生叛乱。')
claim('event',E,'description','新董璋传称董欲杀仁矩，仁矩涕泣获免，归称董璋必反。',17,'又因事欲殺仁矩，仁矩涕泣而免，歸言璋必反。','必反是李的预测报告，不当本年已经反；因事概叙与主宴冲突细节互补，未以新省略补造实际杀使。',source=d,relation='adds')
E=ev('liyanxun_sent_dongchuan','李仁矩归后不久，朝廷又遣退事舍人李彦珣赴东川',17,'未几','诣东川，',[('帝','再遣使者'),('彦珣','退事舍人、赴东川使者')],year=None,when='未几：李仁矩归后不久；确年日未独载',place='后唐至东川',note='未几为相对时距，不据此强五月或本年精日；李彦珣不与沙彦珣及李彦舜合并，退事舍人原衔待核。')
E=ev('dongzhang_detains_liyanxun_followers','李彦珣入境失小礼，董璋拘其随从',17,'入境','璋拘其从者，',[('彦珣','入境失礼的使者'),('璋','拘随从者')],year=None,when='李彦珣使东川途中，确年日未独载',place='东川境',note='被拘是从者非李本人，失小礼原语未具具体礼仪，不猜现代犯罪。')
E=ev('liyanxun_flees_back','李彦珣逃归',17,'彦珣奔',None,[('彦珣','奔还者')],year=None,when='从者被拘后，确年日未独载',place='东川至后唐',note='逃归不等被处死或带走全部从者。')
E=ev('gaoconghui_prior_admonishes_father','高季兴反叛时，高从诲多次劝谏而父不听',18,'高季兴','不听。',[('季兴','不听劝谏的父亲'),('从诲','劝谏者')],year=None,when='高季兴反叛时的追叙，具体劝谏年月未独具',place='荆南',note='节谏按反复进谏理解，不据叛背景把每次劝谏都固定928；父边已有，不另建。')
E=ev('gaoconghui_prefers_near_tang_to_far_wu','高从诲袭位后对僚佐称唐近吴远，舍近臣远失策',18,'从诲既','非计也。”',[('从诲','对僚佐评归属选择者')],when='928年袭位后至929年归附申请前；本句确日未载',year=None,place='荆南',note='是高的政治判断和提出方向，不当他说话当日已正式被后唐任职。')
E=ev('gaoconghui_through_mayin_apologizes_tang','高从诲借马殷向后唐谢罪',18,'乃因','谢罪于唐。',[('从诲','经楚谢罪者'),('殷','中介谢罪者')],place='荆南经楚至后唐',note='经楚中介不等荆南并入楚，也不推两个政权永久盟约。')
claim('event',E,'description','新荆南世家同记从诲因惧被唐讨，遣使聘楚，马殷为之向唐请命。',18,'從誨以父自絕于唐，懼復見討，乃遣使者聘于楚，楚王馬殷為之請命于唐，','动机据新传归于史述，未提前随后刘知谦奉表、930授职或后封王。',source=gh,relation='corroborates')
E=ev('gaoconghui_letter_anyuanxin_resume_tribute','高从诲致书安元信，求保奏恢复职贡',18,'又遗','复修职贡。',[('从诲','求保奏者'),('元信','山南东道节度使、受信者')],place='荆南至山南东道',note='求字是申请，不独立证明此前各项贡物都已送达。')
E=ev('anyuanxin_reports_gaoconghui_letter','安元信将高从诲书信上报',18,'丙申','以从诲书闻，',[('元信','保奏上报者'),('从诲','其归附信被上报者')],when='929年五月丙申',place='山南东道至后唐朝廷',note='与六月高自行上表、七月正式任命分时点。')
claim('event',E,'time_original','旧明宗纪同日记襄州奏荆南高从诲乞归顺。',18,'丙申，襄州奏，荊南高從誨乞歸順。','襄州为山南东道治州，主名安元信；旧奏地方称法不同，未另造第二同日保奏。',source=may,relation='corroborates')
E=ev('emperor_accepts_gaoconghui_return_request','李嗣源许可高从诲所请',18,'帝许之。',None,[('帝','许可归附请求者')],when='929年五月丙申',place='后唐朝廷',note='许可与后续官授不同，不能写本日已复全部官爵。')
E=ev('khitan_attacks_yunzhou_may','契丹再次侵扰云州',19,'契丹',None,[],place='云州',note='四月主第14段与本五月记分，不当单一事件被两次统计，也不推同将同军人数。')
E=ev('yedu_restored_weizhou_offices_removed','后唐复称邺都为魏州，停留守、皇城使',20,'六月',None,[],when='929年六月戊申',place='邺都、魏州',note='改名和停官制，不等摧毁全部城池或未给姓名的官员被杀。')
claim('event',E,'description','旧明宗纪六月戊申段后称诏邺都仍旧为魏府，并去魏府、汴州、益州宫殿鸱尾，赐节度使为衙署。',20,'詔鄴都仍舊為魏府。應魏府、汴州、益州宮殿悉去鴟尾，賜節度使為衙署。','魏府与主魏州称法保留；旧此句承戊申段未独日，日由主。宫殿改衙署是独立补说明，不等主记三个城市均废。',source=jun,relation='adds')
E=ev('gaoconghui_petitions_submission','高从诲自署前荆南行军司马、归州刺史，上表求内附',21,'庚申','求内附。',[('从诲','自署旧职、奉表申请者')],when='929年六月庚申',place='荆南至后唐',note='自称前职是请罪署衔，不与928吴授荆南节度冲突地再造自己罢吴官诏。')
claim('event',E,'description','旧明宗纪六月丙辰记高从诲上章首罪、求修职贡，进银三千两赎罪。',21,'丙辰，權知荊南軍府事高從誨上章首罪，乞修職貢，仍進銀三千兩贖罪。','主庚申与旧丙辰表章纪时不同或另奏未能确定，并列不强同日；银三千两不是主明载上表数，也非五月保奏书的原本金额。',source=jun,relation='adds')
E=ev('tang_appoints_gaoconghui_jingnan','后唐授高从诲荆南节度使兼侍中',21,'秋','节度使兼侍中。',[('从诲','后唐正式授军职者')],when='929年七月甲申',place='荆南',note='这是后唐授，别于928吴授同衔；新世家系长兴元年正月有纪年差，不消去。')
claim('event',E,'description','旧明宗纪同日记高从诲起复，授检校太傅兼侍中，充荆南节度使。',21,'甲申，以前荊南行軍司馬、檢校太傅高從誨起復，授檢校太傅、兼侍中，充荊南節度使。','同甲申补起复和检校衔，父丧背景不猜守丧精日；不另造第三同日节度任命。',source=jul,relation='corroborates')
claim('event',E,'time_original','新荆南世家将拜高从诲节度使系于长兴元年正月。',21,'長興元年正月，拜從誨節度使，','长兴元年为930，与主旧929七月不同，原记保留不另造确定二次任命；本句后追封高楚王等留待对应主年。',source=gh,relation='conflicts')
E=ev('jingnan_campaign_commander_office_abolished','朝廷罢荆南招讨使',21,'己丑',None,[],when='929年七月己丑',place='荆南军务',note='罢的是军职，未名具体被罢者不猜房知温被杀或解除全部镇职。')
E=ev('lijian_requests_return_jiangdu_ill','吴武昌节度使兼侍中李简因病请求返江都',22,'八月','求还江都，',[('简','患病请返江都者')],place='武昌至江都',note='沿919已录武昌节度使李简，不混王建将李简；请归非已经抵江都，后卒采石分。')
E=ev('lijian_dies_caishi','李简卒于采石',22,'癸丑','卒于采石。',[('简','于采石去世者')],when='929年八月癸丑',place='采石',note='不补现代诊断、兵败死因或归抵江都；电子本纸本待核。')
claim('person',people['李简'],'description','新吴世家此前记鄂州李简为镇西大将军。',22,'鄂州李簡鎮西大將軍，','复用919出处提供吴鄂州身份连续性，不当本年新增任镇西或与王建军同名合并；更早杨行密将限定名与本主体重叠待独立修订，不增第三实体。',source=wu)
relationship('知询','简','女婿',22,'徐知询，简婿也，','婿明方向徐知询→李简，徐是李的女婿；不凭婿字另造无名妻子实体或确婚年月。')
E=ev('xuzhixun_retains_lijian_two_thousand','徐知询擅留李简亲兵二千于金陵',22,'擅留','于金陵，',[('知询','擅留亲军者')],place='金陵',note='简前死语境，二千是亲兵不是全部武昌总兵数；未推这些兵亲属关系、具体编制或叛乱。')
E=ev('xuzhixun_recommends_liyanzhong','徐知询上表荐李彦忠代父镇鄂州',22,'表荐','代父镇鄂州，',[('知询','荐继军职者'),('彦忠','被荐替父者')],place='鄂州军职',note='表荐非任命已批准；新李彦忠不混后晋王彦忠。')
relationship('简','彦忠','父亲',22,'表荐简子彦忠代父镇鄂州，','原简子彦忠明父，李简→李彦忠为父亲；不建反向重复儿子边。')
E=ev('xuzhigao_appoints_chaizaiyong_wuchang','徐知诰以柴再用为武昌节度使',22,'徐知诰','武昌节度使；',[('知诰','任用武昌节度者'),('柴再用','龙武统军、武昌节度获任者')],place='武昌',note='徐知诰沿李昪同人，不能说彦忠最终已继职；当时吴官，未提前南唐帝位。')
E=ev('xuzhixun_objects_to_family_preference','徐知询怒，称刘崇俊为兄之亲、三世据濠州，质问为何己妻族李彦忠不可',22,'知询怒',None,[('知询','就亲属任职偏好发言者'),('刘崇俊','话中比较的濠州人物'),('彦忠','话中妻族比较对象')],place='吴、金陵',note='刘三世濠州及兄之亲为徐的指称，非独立族谱明父祖，不猜三任姓名；两比较对象无记在场，彦忠妻族不推出与徐妻具体兄弟长幼。')
review='卷276连续929年第17—22段、原103—108行。帝将郊祀请求西川百万東五十万与实际西50东10万缗分，请军用不足为两川说法；今疑令字原留。新董天成4祀天、两川物50万与主将祀口径差保留，不推本年已经郊祭或新物单位缗。李旧客将安宠为生平，不建永盟；董宴邀、李日中不赴饮、董武装入驿斥引西川杀李客省、李泣求免、董赂谢、李归报不法分，不新造929李严死亡；新归言必反是预测不是已叛。未几彦珣再使、失小礼拘从、彦珣奔还年null，拘者从属不是使本人，退事舍人原衔待核，不混沙彦珣。高父叛谏与袭位近唐远吴议前事年null，经马殷谢罪、致安元信书、五月丙申安奏与帝许分；许可不等本日已授官。五月云寇与四月分，六月戊申邺魏复称与停职，旧魏府和三州宫殿改衙署补不猜毁全城。六月庚申高前职自署内附表与旧丙辰罪表银3000两并列，未确认同一奏日差还是不同表，不转五月书金额。七月甲申后唐高任与928吴任分，旧同日起复检校衔补，新长兴元年正月930异年留，不另造确定二次任；己丑罢招讨不猜杀主将。八月李简疾请返、癸丑采石卒、徐擅留二千、荐李子彦忠非批准、徐知诰任柴、徐怒族比较分。李沿919武昌同人，不混王建军李；旧0891杨行密将限定实体疑与当前重叠待独立修订不第三造。徐女婿李、李父彦忠方向明确，无名妻未造；刘崇俊新为话中对象，三世濠州兄亲是徐说不猜父祖，妻族不推彦忠与徐妻长幼，非在场演员。原摘录定位保留底本，展示简体；纸本异文待核，高郁案下一段未读不计完。'
review=review.replace('東','东')
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,23):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=929,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(17,23)],next_paragraph='zztj-v276-y0929-p023',next_volume=276,next_year=929,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续929年第17—22段、原103—108行；两川贡与使冲突、荆南归唐、云寇邺制及吴武昌李徐柴案。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(17,23)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
