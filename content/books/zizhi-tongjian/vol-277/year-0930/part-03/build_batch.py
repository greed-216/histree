# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 930, paragraphs 20–29."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 56))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 key=directory.name;author='薛居正等' if key.startswith('jiuwudaishi') else '欧阳修'
 specs.append((key,directory,'5ae2febe',author))
specs.append(('tongjian-277-930-summer',YEAR/'part-02/sources/library/tongjian-277-930-summer','d5eb21c8','司马光等'))

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0930-p020-p029',
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
for n in range(20, 30):
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
        citation = f'卷277·长兴元年（930）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0930_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','重诲':'安重诲','从荣':'李从荣','从厚':'李从厚','璋':'董璋','知祥':'孟知祥','知诰':'李昪','传拯':'王传拯','宣':'陈宣','岩':'王岩（吴海州将）','绾':'王绾','舆':'王舆（吴光州刺史）'}
NEW_ALIASES={'李行德':[],'张俭':['張儉'],'边彦温':['邊彥溫'],'安从进':['安從進'],'王传拯':['王傳拯'],'陈宣':['陳宣'],'王岩（吴海州将）':['王岩（吴）'],'王舆（吴光州刺史）':['王舆（吴）']}

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

def event(code, title, n, quote, actors, when=None, note='', year=930, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='930年'+('五月' if n<=21 else '六月' if n<=23 else '七月' if n==24 else '八月')+'本段；确日未载'
    key = 'event_zztj_277_0930_' + code
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
        edge = 'participation_zztj_277_0930_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0930_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive nine paragraphs, chronological facts and independently located supplements.
# -*- coding: utf-8 -*-
aug='jiuwudaishi-041-930-august';haizhou='jiuwudaishi-041-930-haizhou-princes';an='xinwudaishi-024-an-accusation';zhao='xinwudaishi-028-zhaofeng-defends-an';congjin='xinwudaishi-051-ancongjin';dong='xinwudaishi-051-lirenju-dongzhang'
E=ev('dong_musters_tattooed_militia','董璋阅集民兵，使其剪发黥面',20,'董璋阅集','皆剪发黥面，',[('璋','阅集民兵者')],note='皆指本句被阅集的民兵，非东川全体居民；黥面不是全部处死，不写现代兵役人数。')
E=event('dong_yongding_fort_record','董璋在剑门北增置永定关',20,'复于剑门北置永定关，',[('璋','增关行动的指挥者')],when='930年五月本段记增永定关；原事件所含守寨行动未独纪年',place='剑门北、永定关',stable_key='event_zztj_277_0930_liyanzhao_defends_jianmen_yongding',note='复用前批新董传合记李彦钊扼寨和增永定关的同一事件；此主句只补增关组成动作及五月语境，不把李扼七砦全赋五月，也不宣称李亲自施工。旧公开事件标题与未知年份保留，具体纪时由本事实引句补。')
E=ev('dong_deploys_beacons','董璋在剑门防线布列烽火',20,'复于剑门北',None,[('璋','布列烽火者')],place='剑门北防线',note='布列烽火是预警部署，不等战役已打响；未证具体现代遗迹位置。')
E=ev('meng_petitions_thirteen_salt_monitors','孟知祥屡次上表请求把云安等十三盐监划归西川，以盐价款赡宁江屯兵',21,'孟知祥累表','以盐直赡宁江屯兵，',[('知祥','申请盐监归属及赡军者')],when='930年五月辛卯准奏前，多次上表未具日',place='云安等盐监、西川、宁江',note='十三为盐监数非十三州；盐直为盐价款不是食盐重量，累表与实际批准分录，不猜全部盐监名字或现代税率。')
E=ev('court_grants_meng_salt_monitors','后唐准孟知祥划云安等十三盐监归西川的请求',21,'孟知祥累表',None,[('知祥','准奏盐监归属请求者')],when='930年五月辛卯',place='云安等十三盐监、西川',note='许为准奏，不等当日已完成所有盐务和军款拨付；未名承办官不造人物。此具体案二十四史未检得同案补句，主独证。')
E=ev('solar_eclipse_sixth_month','六月朔日发生日食',22,'六月，',None,[],when='930年六月，癸已朔（底本原字，干支疑字待核）',note='底本癸已之已非通常地支巳，疑转录字；原引不改，不自行把日换为公历或以现代历算当原史证。仅记史载日食，不加影响人物吉凶。')
E=ev('centralizes_provincial_office_appointments','后唐敕防御使、团练使、刺史、行军司马和节度副使均由朝廷任命，诸道不得奏荐',23,'辛亥，',None,[],when='930年六月辛亥',note='列举职位的任命和奏荐权，不等撤销全部军镇或罢尽原任官；自今为诏定规则，不用本句证明后来处处执行。')
E=ev('dong_raids_sui_lang_garrisons','董璋遣兵掠遂州、阆州镇戍',24,'董璋遣兵','掠遂、阆镇戍，',[('璋','遣兵掠镇戍者')],when='930年七月戊辰两川奏前；具体掠日未载',place='遂州、阆州镇戍',note='主列在七月奏之前，起年930当条，月份未强称七月或六月；掠镇戍不等两城已被完全攻陷。')
E=ev('two_sichuans_petition_troop_reinforcement','两川因朝廷续遣兵屯遂州、阆州，再作论奏',24,'秋，七月，','复有论奏，',[('璋','东川方面论奏者'),('知祥','西川方面论奏者')],when='930年七月戊辰',place='两川、遂州、阆州',note='两川沿既有董孟，不虚造其他联名官；主未引表文细目，不能强说已要求皇帝全部撤军。')
E=ev('trade_into_shu_declines','两川再奏后，东北商旅少敢入蜀',24,'自是',None,[],when='930年七月两川再奏之后；持续情形未具起止日',place='东北至蜀商旅道路',note='少敢是史述风险反应，非完全断绝贸易，也没有商户或财货数值；东北按当时叙法，不限定现代东北三省。')
E=ev('informers_accuse_an_private_campaign','李行德、张俭引边彦温告称安重诲发兵欲自行讨淮南，并求占问命',25,'八月，乙未，','又引占相者问命。”',[('李行德','捧圣军使、引告密者'),('张俭','十将、引告密者'),('边彦温','告称安私讨及问命者'),('重诲','被指控对象')],when='930年八月乙未',note='这是告言，后证诬陷，不能建立安已谋反或已讨灭吴的事实；占相者未名不造身份。边与四月被杀杨彦温、早年王彦温不同人。')
claim('event',E,'description','新安传记告言转引李虔徽之客边彦温，指安私募士卒、缮甲欲伐吴并私交谍者。',25,'已而捧聖都軍使李行德、十將張儉告變，言：「樞密承旨李虔徽語其客邊彥溫云：『重誨私募士卒，繕治甲器，欲自伐吳。又與諜者交私。』」','补书转述链及告言内容不同详略，保持告言身份，不把李虔徽直接写成实际造谣者；前玉带谍事属另段追叙未在此提前再录。',source=an,relation='adds')
E=ev('emperor_consults_ancongjin_yao','李嗣源就安重诲被告事询问安从进、药彦稠',25,'帝以问','药彦稠，',[('帝','问将者'),('安从进','受询的侍卫都指挥使'),('药彦稠','受询将领'),('重诲','被询议对象')],when='930年八月乙未',note='主职衔与旧六月护驾马、步分职的具体归属不以本段自动合一；药沿四月同人。')
claim('person',people['安从进'],'description','新安从进传记其从庄宗为护驾马军都指挥使，明宗时任节度职。',25,'從進初從莊宗於兵間，為護駕馬軍都指揮使，領貴州刺史。明宗時，為保義、彰武軍節度使，','以姓名时代职掌识别同一安从进，不与安从义安崇阮混；新传后续夏州和晋代襄州反叛不提前录入。',source=congjin,relation='adds')
E=ev('ancongjin_yao_vouch_for_an','安从进、药彦稠称告密者意在离间，请以宗族保安重诲',25,'二人曰：','臣等请以宗族保之。”',[('安从进','为安辩护并请宗族作保者'),('药彦稠','为安辩护并请宗族作保者'),('重诲','被作保者')],when='930年八月乙未',note='三十年是二将话中事主时长，不据此反推安始事精确900年；请宗族保非二将宗族被杀。幸贵何苦为其论辩非现代已检全案。')
E=ev('bianyanwen_executed','李嗣源斩告密人边彦温',25,'帝乃斩彦温','召重诲慰抚之，',[('帝','命斩者'),('边彦温','被斩告密人')],when='930年八月乙未',note='彦温承边，不混已死杨；主本句斩边未明族其家，李张族诛另见壬寅。')
claim('event',E,'description','新安传记廷诘边彦温，边承认告言是诈，继记三人皆族诛。',25,'因廷詰彥溫，具伏其詐，於是君臣相顧泣下。彥溫、行德、儉皆坐族誅。','新连叙未逐日、旧乙未合记三人族诛，主先斩边后壬寅族李张；分述不同纪时和刑罚范围，不替主边斩补成必然同日全族皆死。',source=an,relation='adds')
claim('event',E,'time_original','旧明宗纪乙未合记李行德、张俭、边彦温并族诛，缘诬告安私市兵仗。',25,'乙未，捧聖軍使李行德、十將張儉、告密人邊彥溫並族誅，以其誣告安重誨私市兵仗故也。','旧与主分日处置及告言内容有异，保留旧合记，不覆盖主壬寅后续。',source=aug,relation='conflicts')
E=ev('emperor_comforts_an_after_accusation','李嗣源召安重诲慰抚，君臣相泣',25,'召重诲慰抚之',None,[('帝','慰抚者'),('重诲','受召慰抚者')],when='930年八月乙未处斩边后',note='相泣为主记，不等安永久免于后来罢官；新传求解职与范延光事属于另连叙，无主当前逐日段未跳录。')
E=ev('zhangyanlang_appointed_sansishi','后唐以张延朗行工部尚书、充三司使',26,'以前忠武节度使','充三司使。',[('张延朗','前忠武节度使、任工部尚书三司使者')],when='930年八月乙未案后本段；确日未载',note='行工部为主原衔，旧兵部异文另记，不静默统一；以前忠武/旧许州是原职不同称法，不当本日都仍任节度。')
claim('event',E,'description','旧明宗纪记张延朗行兵部尚书、充三司使，并列宣徽使下。',26,'以前許州節度使張延朗為檢校太傅、行兵部尚書，充三司使。','主工部、旧兵部有官名差，保留两说供校，不凭字形自动当繁简差；旧同段乙未之后未独明确任官日。',source=aug,relation='conflicts')
claim('event',E,'description','旧明宗纪宣旨让张延朗专总会计，三司使班位在宣徽使下。',26,'張延朗可充三司使，班在宣徽使下。','补职位班次，不据此推所有时期三司使都同班位。',source=aug,relation='adds')
E=ev('sansishi_designation_established','主书记三司使之名自张延朗此次任命始',26,'三司使之名',None,[],note='主对使名起始的叙述，不把之前已有判三司、三部门制度否定；不声称历史所有文献此前绝未用三司使字。')
claim('event',E,'description','旧明宗纪亦记三司之有使额，自张延朗始。',26,'三司之有使額，自延朗始也。','旧强调使额与主使名同案互证；旧他年诏里已出现三司使用语，需区别正文制度概括、后编称呼与正式使额，不作绝对词语首次出现论。',source=aug,relation='corroborates')
# -*- coding: utf-8 -*-
E=ev('chenxuan_leaves_haizhou','海州团练使陈宣罢归',27,'值团练使','陈宣罢归，',[('宣','罢归的海州团练使')],when='海州兵变前；罢归本句未独纪年日',year=None,place='海州',note='前置背景罢归未独年月，不强赋己亥；主团练使与旧兵变奏中刺史职称异详保留同人。')
E=ev('xu_promises_wang_haizhou_command','徐知诰许以海州都指挥使王传拯代陈宣',27,'吴徐知诰','知诰许以传拯代之；',[('知诰','许代任者'),('传拯','有威名、得士心的都指挥使、被许代者')],when='930年海州兵变前；本句未独月日',place='吴、海州',note='许为承诺代任，未正式完成就任；威名得士心为主评价，不建所有军士关系。')
E=ev('xu_restores_chen_recalls_wang','徐知诰又遣陈宣还海州，征王传拯还江都',27,'既而复遣','征传拯还江都。',[('知诰','改用陈宣并召王者'),('宣','被遣返海州者'),('传拯','被征回江都者')],when='930年海州兵变前，许代之后；确日未载',place='海州、江都',note='征是召回令，不证王实际已经抵江都；原先承诺与后续改命分。')
E=ev('wang_blames_chen_slander','王传拯愤怒，认为陈宣毁谤自己',27,'传拯怒，','以为宣毁之，',[('传拯','愤怒、认为被毁者'),('宣','被王怀疑毁谤者')],when='930年召回江都令后、己亥兵变前',place='海州',note='以为归王想法，不独认定陈确实造谣；不造终身仇敌边。')
E=ev('wang_kills_chen_at_departure_visit','王传拯率麾下辞见陈宣时，斩杀陈宣',27,'己亥，','因斩宣，',[('传拯','率麾下辞见并杀陈者'),('宣','被斩的团练使')],when='930年八月己亥',place='海州',note='入辞是离任前辞见借机行杀，不等王已到江都面辞徐；己亥实际行动与旧戊申兖州奏报分。')
E=ev('wang_burns_plunders_haizhou','王传拯及其部众焚掠海州城郭',27,'因斩宣，','焚掠城郭，',[('传拯','焚掠城郭部众的将领')],when='930年八月己亥',place='海州',note='焚掠不推整座城全部毁灭或居民全死；未名麾下不造军官。')
E=ev('wang_flees_to_tang_with_five_thousand','王传拯率众五千来奔后唐',27,'帅其众五千','帅其众五千来奔。',[('传拯','率部众来奔者')],when='930年八月己亥兵变后；抵达确日未独载',place='海州至后唐',note='主来以唐史视角，目的后唐由旧至沂州归国奏佐核；五千是众，不直接全计战兵。')
claim('event',E,'description','旧明宗纪戊申记兖州奏王传拯杀陈宣、焚海州，带兵士及家口五千归国至沂州，帝遣使慰纳。',27,'戊申，兗州奏：「淮南海州都指揮使王傳拯殺本州刺史陳宣，焚燒州城，以所部兵士及家口五千人歸國，至沂州。」帝遣使慰納之。','旧五千含家口，主众五千不写成纯战兵；戊申为奏闻日，未覆盖主己亥杀焚。旧刺史与主团练使职称不同详略，同海州陈宣不新建另人。帝慰纳为旧补，未名使不造实名。',source=haizhou,relation='adds')
E=ev('xu_accepts_blame_spares_wang_family','徐知诰承认此事为己过，免王传拯妻子',27,'知诰曰：“是吾过也。”','免其妻子。',[('知诰','自责并免王家属者'),('传拯','家属被免的叛奔者')],when='930年八月王传拯兵变来奔后；确日未载',place='吴',note='妻子古义妻与子女、免为免其罪责处置，不当解除婚姻；未名家属不造人名，王非免刑在吴本人实际获释。')
E=ev('wangyan_takes_troops_into_haizhou','涟水制置使王岩率兵进入海州',27,'涟水制置使','王岩将兵入海州，',[('岩','涟水制置使、率兵入海州者')],when='930年八月海州兵变后；确日未载',place='涟水至海州',note='吴将王岩不与闽王延禀异名王岩混；仅据同案新建消歧人物，二十四史未检具体同案王岩补句。将兵入不等打败王传拯，王已奔唐。')
E=ev('wangyan_promoted_weiwei_haizhou','吴以王岩为威卫大将军、知海州',27,'以岩为','知海州。',[('岩','任威卫大将军、知海州者')],when='930年八月王岩入海州后；确日未载',place='吴、海州',note='知海州为主持州事，不自动改名任刺史或团练使；威卫原字不替换为未校的威武军。')
relationship('绾','传拯','父亲',27,'传拯，绾之子也，','王绾→王传拯为父亲。王绾复用899年淮海涟水及海州同一吴将身份，不因今只作父名另建。')
relationship('舆','传拯','叔父',27,'传拯，绾之子也，其季父舆为光州刺史。','王舆→王传拯为叔父，季父是父亲幼弟，不当祖父；不另造王舆姓名同人的余、與字别名。')
E=ev('wangchuanzheng_sends_secret_letter_uncle','王传拯遣间使持书赴光州王舆处',27,'传拯遣间使','持书至光州，',[('传拯','遣持书间使者'),('舆','光州刺史、书使目标')],when='930年八月来奔后相关连叙；确日未载',place='后唐来奔地至光州',note='信内容未载，不断言邀叔一并投唐；匿名间使不造名。')
E=ev('wangyu_arrests_messenger_reports_wu','王舆拘执王传拯的间使，上报吴',27,'舆执之','以闻，',[('舆','执使上闻者'),('传拯','被执使者的派遣人')],when='930年八月间使到光州后；确日未载',place='光州至吴朝廷',note='之承间使，非亲自把王传拯捕回吴；不写成烧信或杀使。')
E=ev('wangyu_requests_retirement','王舆因侄遣使事请求罢归',27,'因求','因求罢归；',[('舆','请求罢归者')],when='930年八月上闻间使后；确日未载',place='吴、光州',note='求是申请，下一仍受任，不证已彻底退休或自杀。')
E=ev('xu_appoints_wangyu_konghe','徐知诰以王舆为控鹤都虞候',27,'知诰以舆','以舆为控鹤都虞候。',[('知诰','选任宿卫将领者'),('舆','受任控鹤都虞候者')],when='930年八月王舆求罢归后；确日未载',place='吴宿卫',note='主重厚慎密为知诰取人评价，非现代人格定论；典兵宿卫难其人不等吴无人可用，控鹤职不当后唐同名武官。')
claim('event',E,'description','主书记徐知诰以王舆重厚慎密，故用之。',27,'知诰以舆重厚慎密，故用之。','把选任理由归知诰，不造全部吴朝宿卫机构正式改制。')
E=ev('zhaofeng_urges_finish_false_accusation_case','赵凤奏称奸人诬陷大臣、动摇国之柱石，处置未尽',28,'壬寅，','行之未尽。”',[('赵凤','请求彻底处置诬陷者的奏者')],when='930年八月壬寅',note='主其话不点安名，承上安案识别；未尽是赵评价，不推已经新发现别的反叛组织。')
claim('event',E,'description','新赵凤传记边彦温案后数日，赵以殿之栋梁柱石比大臣，谏帝勿以此为闲事。',28,'大臣，國之棟梁柱石也，且重誨起微賤，歷艱危，致陛下為中興主，安可使姦人動搖！','新承前边案、后数日，未独干支；用于赵谏辞补，不提前后续赵凤因护安罢官。',source=zhao,relation='adds')
E=ev('lixingde_zhangjian_clan_execution','李嗣源收捕李行德、张俭，并族诛',28,'帝乃收',None,[('帝','命收捕族诛者'),('李行德','被收捕族诛者'),('张俭','被收捕族诛者')],when='930年八月壬寅',note='主分于乙未斩边之后，族是株连宗族、未具范围人数，不造实名亲属。旧三人合乙未纪时差另存。')
claim('event',E,'time_original','旧明宗纪把李行德、张俭和边彦温族诛合记八月乙未。',28,'乙未，捧聖軍使李行德、十將張儉、告密人邊彥溫並族誅，以其誣告安重誨私市兵仗故也。','与主壬寅收族李张、乙未斩边纪时及范围不同；不据旧覆盖主两日叙法。',source=aug,relation='conflicts')
E=ev('licongrong_enfeoffed_qin','后唐立皇子李从荣为秦王',29,'立皇子','从荣为秦王；',[('从荣','受封秦王的皇子')],when='930年八月，本段丙辰之前；主从荣封王未独载日',note='主无从荣本条日，不把后一丙辰复制给前；旧壬寅另证。封王不等即帝或太子。')
claim('event',E,'time_original','旧明宗纪壬寅封河南尹李从荣为秦王，仍择日册命。',29,'壬寅，皇子河南尹、判六軍諸衛事從榮封秦王，仍令所司擇日冊命。','壬寅为旧封命日，后九月仪注属于后续册礼，不提前八月；主日未具不强抹。',source=haizhou,relation='adds')
E=ev('liconghou_enfeoffed_song','后唐立皇子李从厚为宋王',29,'丙辰，',None,[('从厚','受封宋王的皇子')],when='930年八月丙辰',note='宋王爵非宋朝建立，原从厚复用，不新帝号人物。')
claim('event',E,'description','旧明宗纪同丙辰封镇州节度使李从厚为宋王，仍择日册命。',29,'丙辰，皇子鎮州節度使從厚封宋王，仍令擇日冊命。','封命与择日册礼分；镇州为当时节度职，六月转镇未因本快照跳段单独新增。',source=haizhou,relation='corroborates')
# -*- coding: utf-8 -*-
reviews={
20:'董阅集民兵剪黥、永定关、布烽分。民兵皆非全部居民。增关复用part01新董合记扼寨与增关事件，此主句只补关动作五月语境，不把李彦钊扼寨全强赋五月；原公开年null保留，新事实明确组成动作日期，避免再建同一关事件。',
21:'累表与辛卯准分；十三盐监不是十三州，云安等未具其余名不猜，盐直为价款非盐重量，赡屯军非当日已付款。二十四史未检具体同案盐监句，主独证。',
22:'原癸已朔的已疑应巳但本底本不改，不据现代历算补公历；二十四史未检对应明确补句，主独证。日食为现象不推吉凶。',
23:'六月辛亥列五类地方职位中央除授、诸道无得奏荐是规则，不当撤尽旧官或证明后续普遍执行。',
24:'董掠镇戍未具月日，不等攻陷两城；七月戊辰两川再奏因续屯而发。少敢为商旅反应非断尽贸易，东北按当时方向非现代三省。不提前秋后实战。',
25:'李张引边告内容是告言，安未因这告言成为已谋反；边彦温不混杨或王。帝问二将、宗族保、斩边、慰安分；三十年为辩话不反算精确始事年。新转述李虔徽客链不当虔徽已证实际造谣；新具伏诈与三人连族、旧乙未合族，对主乙未斩边而后壬寅族李张差别并列。新后求解职与范任连叙留主后续，不提前。安从进据主职与新兵间履历建，不合安从义安崇阮。',
26:'主工部旧兵部兼官异文保留，许州与忠武为原职称。三司使使名/使额始于此次为书中概括，非三司组织才生或所有旧文本此前绝无字；旧 earlier诏已用词，区别正式使额。',
27:'陈罢归前置背景未知年，徐许王代未实际任，改令陈还王征不证王已返江都；王以为陈毁归怀疑。徐知诰沿李昪既有稳定身份，不因本时未恢复李姓再造人物。己亥辞见杀、焚、众五千奔分，旧戊申兖州奏至沂州为报告日，五千含兵与家口不当纯战兵。徐自责免妻子为妻与子女，未名不造。王岩吴将消歧，非闽王延禀异名；入州非击败已奔王，授威卫知海州不改军名。王绾沿899年淮海涟水海州同吴将；父亲王绾→传拯，季父王舆→传拯叔父。王舆执使不是捕本人，信内容未具不猜招降；求罢非已退，控鹤任与徐厚密评价分。此案吴内部细节二十四史未检同案，主独证、旧补杀焚奔。',
28:'赵壬寅奏未尽与族李张分；新赵殿栋梁比喻补，后数日不推公历，后护安罢官未提前。旧乙未合三族与主两次纪法并列，未具宗族人数姓名不造。',
29:'主从荣封秦未独日、丙辰只系从厚宋；旧从荣壬寅、从厚丙辰封并择日册命补，九月册注不提前，封宋非新宋朝或秦王即太子。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(20,30):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=930,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(20,30)],next_paragraph='zztj-v277-y0930-p030',next_volume=277,next_year=930,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续930年第20—29段、原25—34行；两川部署盐务、日食及任官诏、安重诲诬告案、三司使、吴海州兵变及秦宋王封命。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(20,30)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
