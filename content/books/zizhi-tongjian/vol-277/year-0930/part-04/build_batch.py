# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 930, paragraphs 30–35."""
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
 key=directory.name;author='司马光等' if key.startswith('tongjian') else '薛居正等' if key.startswith('jiuwudaishi') else '欧阳修'
 specs.append((key,directory,'73f70bd8',author))
specs.append(('jiuwudaishi-062-dongzhang-imprisons-wu',YEAR/'part-02/sources/library/jiuwudaishi-062-dongzhang-imprisons-wu','d5eb21c8','薛居正等'))
specs.append(('xinwudaishi-006-930',YEAR/'part-01/sources/library/xinwudaishi-006-930','238471e3','欧阳修'))
specs.append(('xinwudaishi-024-an-accusation',YEAR/'part-03/sources/library/xinwudaishi-024-an-accusation','5ae2febe','欧阳修'))

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-rebellion','tongjian-277-930-autumn-winter']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0930-p030-p035',
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
for n in range(30, 36):
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
    ck = f'claim_zztj_277_0930_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','重诲':'安重诲','璋':'董璋','光业':'董光业','知祥':'孟知祥','季良':'赵季良','仁罕':'李仁罕','仁矩':'李仁矩','业':'张业','德妃':'王德妃（李嗣源妃）','延光':'范延光','洪':'姚洪','思恭':'孟思恭'}
NEW_ALIASES={'董光业':['董光業'],'李虔徽':[],'荀咸乂':['荀鹹乂'],'苏愿':['蘇願'],'孟思恭':[],'孟汉琼':['孟漢瓊'],'姚洪':[]}

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
    if when is None:when='930年本段；主句未独纪月日' if n==30 else '930年九月本段；确日未载'
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
# -*- coding: utf-8 -*-
sept='jiuwudaishi-041-930-september';october='jiuwudaishi-041-930-october';letter='xinwudaishi-026-lirenju-letter';fall='xinwudaishi-026-lirenju-fall';yaolife='xinwudaishi-033-yaohong-identity';yaodeath='xinwudaishi-033-yaohong-death';meng='xinwudaishi-064-meng-campaign';dong='jiuwudaishi-062-dongzhang-imprisons-wu';ann='xinwudaishi-006-930';an='xinwudaishi-024-an-accusation'
E=ev('dong_letter_threatens_rebellion','董璋致在洛阳的宫苑使董光业书，称朝廷削地屯兵欲杀己，若再发兵入斜谷则必反',30,'董璋之子','与汝诀矣。”',[('璋','致书、以再发兵为反叛条件者'),('光业','在洛阳任宫苑使、受父书者')],place='东川至洛阳、斜谷',note='三千驻兵和欲杀为董书说法，一骑为假设触发条件，非本句已发一骑；与汝诀是决绝书语非儿子已死。')
claim('event',E,'description','新李仁矩传亦载董告子光业：再一骑入斜谷必反。',30,'若唐復遣一騎入斜谷，吾反必矣！與汝自此而決。','同案书信印证，仍作条件威胁，不倒成当时既定实战；新称节髦原字不替主节镇。',source=letter,relation='corroborates')
relationship('璋','光业','父亲',30,'董璋之子光业为宫苑使，在洛阳，','董璋→董光业为父亲，子明示；不因称光业无姓另造人。')
E=ev('dongguangye_shows_letter_liqianhui','董光业将董璋书信示枢密承旨李虔徽',30,'光业以书示','枢密承旨李虔徽。',[('光业','示书求通报者'),('李虔徽','枢密承旨、看书者')],place='洛阳',note='示书不等李已经同意止兵；虔徽与虔徵等未核近字不自动混。')
claim('event',E,'description','旧董传同记光业将书呈李虔徽。',30,'光業以書呈樞密承旨李虔徽。','旧同身份佐核，虔徽沿原名，不新增未名其他枢要。',source=dong,relation='corroborates')
E=ev('xunxianyi_sent_langzhou','朝廷又遣荀咸乂率兵戍阆州',30,'未几，','将兵戍阆州，',[('荀咸乂','率增戍兵赴阆州者')],when='930年董璋书后未几；确月日未载',place='后唐至阆州',note='遣往是派兵行动，不证此刻已入阆；主别将、旧中使称法不同，咸/鹹为展示简体和原字差。')
claim('event',E,'description','新李仁矩传记安重诲遣荀咸乂益戍阆州，兵未到而董已反。',30,'重誨又遣荀咸乂將兵益戍閬州，光業亟言以為不可，重誨不聽。咸乂未至，璋已反，','补派兵决策者和未至时序，原段未独日，不另填荀率三千或一千。',source=fall,relation='adds')
E=ev('guangye_requests_stop_xun','董光业向李虔徽陈述兵至前父必反，请止荀咸乂之兵',30,'光业谓虔徽曰：','吾父保无他。”',[('光业','请求止兵、担保父无他者'),('李虔徽','受陈请者'),('璋','被儿子预测将反者')],place='洛阳',note='父必反及保无他是光业判断和承诺，不是已经证实可避免战争；不敢自爱非自杀。')
E=ev('an_refuses_guangye_stop_request','李虔徽将董光业之请告安重诲，安不从',30,'虔徽以告','重诲不从。',[('李虔徽','转告止兵请求者'),('重诲','拒绝止兵者')],place='后唐朝廷',note='不从针对停增戍，非本句已下令诛董光业；旧囚武等另有年代，不把整连叙都提前。')
E=ev('dong_rebels_after_reinforcement_news','董璋闻朝廷未止增戍，遂起兵反叛',30,'璋闻之','遂反。',[('璋','起兵反叛者')],note='主起兵未独载月日；此前郭等指控和五月部署不倒写当时已反，当前遂反为主明确断事。')
E=ev('three_garrisons_report_dong_muster','利、阆、遂三镇上报董璋反，并称已聚兵将攻三镇',30,'利、阆、遂三镇','将攻三镇。',[('璋','三镇报告中的聚兵欲攻者')],place='利州、阆州、遂州至后唐朝廷',note='已聚兵欲攻是镇报，非三城已陷；报者无实名，不新增已任此三州所有长官作联名者。')
claim('event',E,'time_original','旧明宗纪九月癸未记三州奏董谋叛、结连孟知祥。',30,'癸未，利、閬、遂三州奏，東川節度使董璋謀叛，結連西川孟知祥。','旧为报告日期和谋叛说法，不能反赋主未具日的起兵确日为癸未；结连为镇报，孟实际约举见下一主段。',source=sept,relation='adds')
E=ev('an_emperor_respond_to_dong_rebellion','安重诲称早知董会反，李嗣源表示被负即讨',30,'重诲曰：',None,[('重诲','将责任归帝含容的发言者'),('帝','表示被负则讨者')],note='早知与含容为安话、我不负人为帝自述，不作独立史实定罪或已经发兵日期。')
E=ev('suyuan_reports_plan_attack_sichuans','西川进奏官苏愿告孟知祥朝廷欲大发兵讨两川',31,'九月，癸亥，','朝廷欲大发兵讨两川。”',[('苏愿','进奏官、报告朝廷意向者'),('知祥','受报者')],when='930年九月癸亥',place='后唐朝廷消息至西川',note='朝廷欲发为消息和计划，不等唐军已到成都；苏愿不与苏颋苏检混。')
E=ev('zhaojiliang_proposes_take_sui_lang','赵季良建议先取遂、阆再并兵守剑门，以免内顾',31,'知祥谋于副使','吾无内顾之忧矣。',[('季良','副使、提出攻守方案者'),('知祥','向副使问计者')],when='930年九月癸亥消息后',place='西川、遂州、阆州、剑门计划',note='主建议东川兵先取，属计划，未当已取两城；大军虽来是条件，不能证已经交战。')
E=ev('meng_invites_dong_joint_rebellion','孟知祥采赵季良计，遣使约董璋同举兵',31,'知祥从之','约董璋同举兵。',[('知祥','采计并邀同举者'),('璋','被邀同举者')],when='930年九月癸亥消息后、庚午派将前',place='西川至东川',note='邀约与前董遂反有先后，不替换为两个同时同日宣布反；未名使不建人。')
E=ev('dong_sends_accusatory_notices_attacks_lang','董璋移文利、阆、遂三镇，指责其离间朝廷，并引兵击阆州',31,'璋移缴','引兵击阆州。',[('璋','发檄指责三镇并攻阆者')],when='930年九月约同举后；确日未载',place='东川至利、阆、遂；阆州',note='主移缴原字疑文书称法不改为现存正式檄原件；离间归董指责，兵击不等此刻城陷。')
claim('event',E,'description','旧明宗纪记利阆进董檄，说将兵击利阆，责其间谍朝廷。',31,'利州、閬州進納東川檄書，言將兵擊利、閬，責以間諜朝廷為名。','旧称檄书和间谍，与主离间不同字，均是董责言；旧段甲申之后未强赋所有董出军甲申。',source=sept,relation='adds')
E=ev('lirenhan_appointed_campaign_commander','孟知祥以李仁罕为行营都部署',31,'庚午，','李仁罕为行营都部署，',[('知祥','任行营统帅者'),('仁罕','都指挥使、受任行营都部署者')],when='930年九月庚午',note='本段正式任战役职，不与旧三月宴案人格指控混。')
E=ev('zhaotingyin_appointed_campaign_deputy','孟知祥令赵廷隐协助李仁罕统兵',31,'庚午，','汉州刺史赵廷隐副之，',[('知祥','任副手者'),('赵廷隐','汉州刺史、行营副手')],when='930年九月庚午',note='副之承李行营都部署，展示副手不造原未载全套官品；汉州职沿已有同人。')
E=ev('zhangye_appointed_vanguard','孟知祥以张业为先锋指挥使',31,'庚午，','简州刺史张业为先锋指挥使，',[('知祥','任先锋者'),('业','简州刺史、任先锋指挥使者')],when='930年九月庚午',note='张业沿既有同人，不据官职另建张知业。')
E=ev('meng_sends_thirty_thousand_suizhou','孟知祥遣李仁罕、赵廷隐、张业将兵三万攻遂州',31,'庚午，','将兵三万攻遂州；',[('知祥','派兵攻遂者'),('仁罕','行营统帅'),('赵廷隐','统军副手'),('业','先锋将领')],when='930年九月庚午',place='西川至遂州',note='三万为史载军数，未现代独立核实；派军攻不提前写成攻陷、夏鲁奇死，后续围城另录。')
claim('event',E,'description','新孟世家亦记三将率三万人攻遂州。',31,'知祥遣李仁罕、張業、趙廷隱將兵三萬人會璋攻遂州，','新会璋文字与主董攻阆布置不同详略，保留新说，不因此把董本人置于遂州同场。',source=meng,relation='corroborates')
E=ev('hou_mengsends_four_thousand_lang','孟知祥遣侯弘实、孟思恭将四千兵，会董璋攻阆州',31,'别将牙内都指挥使',None,[('知祥','另派四千援军者'),('侯弘实','牙内都指挥使、领援军者'),('思恭','先登指挥使、领援军者'),('璋','被会同攻阆的东川主将')],when='930年九月庚午分兵',place='西川至阆州',note='四千是两将所率总数，不各四千；侯沿已有主体，孟不与拓跋思恭赵思恭混。')
claim('event',E,'description','新孟世家则说另遣侯弘实将四千助董守东川。',31,'別遣侯弘實將四千人助璋守東川，','新无孟思恭且任务为守东川，主两将会攻阆有任务差，可能阶段不同但未擅解为已证阶段，保留并列。',source=meng,relation='conflicts')
# -*- coding: utf-8 -*-
E=ev('wang_menghanqiong_disparage_an','王德妃、武德使孟汉琼渐用事，多次向李嗣源短毁安重诲',32,'王德妃及','数短重诲于上。',[('德妃','渐用事、短毁安者'),('孟汉琼','武德使、短毁安者'),('重诲','被短毁对象'),('帝','听取短言的皇帝')],when='930年九月甲戌请辞前一时期；未独起日',note='数为多次，渐用事为主归述，不证二人全部指控为真；王沿已有德妃，孟新姓名不混孟知祥或孟思恭。')
claim('person',people['安重诲'],'description','主记安重诲久专大权，中外恶之者众。',32,'安重诲久专大权，中外恶之者众；','这是主书对当时权势与反感的概括，无名单人数，不作民意统计或起年。')
E=ev('an_requests_relief_emperor_reassures','安重诲因忧惧上表请解机务，李嗣源表示无嫌并提诬告者已诛',32,'重诲内忧惧','卿何为尔？”',[('重诲','上表请解机务者'),('帝','拒其忧疑、慰言者')],when='930年九月甲戌面奏前',note='表解为请辞未获准；帝称诬者已诛承前案，不再造一次斩告者。')
E=ev('an_repeatedly_requests_regional_post','安重诲面奏屡请一镇以全余生，李嗣源先拒后怒称听去',32,'甲戌，','朕不患无人！”',[('重诲','面奏屡请出镇者'),('帝','先拒后怒言听去者')],when='930年九月甲戌',note='臣无种是假设若无帝明将灭族，不当安族已经尽死；听去是怒言，主之后安如故，不能写成当日已罢枢密使赴镇。')
E=ev('fan_urges_keep_an_declines_replacement','范延光劝留安重诲，李嗣源询其可否代任，范以资浅才不及辞',32,'前成德节度使','何敢当此？”',[('延光','前成德节度使、劝留并辞代者'),('帝','询范能否代者'),('重诲','被劝留对象')],when='930年九月甲戌请辞时',note='辞代为本次应对，不否定后甲申实受任；前成德主衔、旧在镇州同军职称法，无需新同名人物。')
E=ev('emperor_sends_meng_to_discuss_an_office','李嗣源遣孟汉琼到中书议安重诲之事',32,'上遣孟汉琼','诣中书议重诲事，',[('帝','遣议者'),('孟汉琼','赴中书议事者'),('重诲','被议任职对象')],when='930年九月甲戌请辞后相关连叙',place='后唐宫中至中书',note='议事不等立即下诏罢职；只据武德使本衔，不提前以未来宣徽使重建人。')
E=ev('feng_zhao_disagree_an_resignation','冯道主张为爱安重诲宜解其枢务，赵凤反对、奏大臣不可轻动',32,'冯道曰：',None,[('冯道','建议解安枢务者'),('赵凤','反对轻动大臣者'),('重诲','被议对象')],when='930年九月甲戌请辞后中书议事',note='解枢务为建议，赵批公失言为意见冲突，不造永久敌人或正式罢官事实。')
claim('event',E,'description','新安传亦记孟汉琼赴中书，冯道认为罢去可纾其祸，赵凤以大臣不可轻动相反。',32,'馮道曰：「諸公苟惜安公，使得罷去，是紓其禍也。」趙鳳以為大臣不可輕動。','新连前告变后叙无独九月干支，不据其段位自动倒赋乙未全案；建议后范任安如故见独立主段。',source=an,relation='corroborates')
E=ev('lang_generals_advise_entrenchment','东川兵到阆州，诸将建议李仁矩深沟高垒守待援兵',33,'东川兵至','贼自走矣。”',[('仁矩','听取守策的阆州主将'),('璋','诸将评价中的东川统帅')],when='930年九月庚辰陷城前',place='阆州',note='原重璋疑姓字按董璋语境及新传核，原文不改，不建重璋新人物；反谋、金帛、旬日援至是诸将判断，非已证唐大军十日实际抵达。诸将未名不把姚洪当实际发言人。')
claim('event',E,'description','新李仁矩传也记将校认为兵未可用、应坚壁待援。',33,'皆曰：「璋有二心久矣，常以利啖吾兵，兵未可用，而賊鋒方銳，宜堅壁以挫之。守旬日，大軍必至，賊當自退。」','主说啖其士卒、新说啖吾兵有受利对象差，保留两书原语，不用引句证明军众实际受贿名单。',source=fall,relation='adds')
E=ev('lirenju_sallies_routs_before_contact','李仁矩轻视蜀兵，出战后兵未交即溃归',33,'李仁矩曰：','兵未交而溃归。',[('仁矩','拒守策、率军出战溃归者')],when='930年九月庚辰城陷前',place='阆州城外',note='蜀懦为李评，不作客观民族性格；未交而溃非已统计战死人数。')
claim('event',E,'description','新李仁矩传同记李驱兵出战，未交即潰。',33,'即驅之出戰，兵未交而潰，','同案行动印证，尚未到被擒死亡，不合为出战当刻李已死。',source=fall,relation='corroborates')
E=ev('dong_captures_langzhou','董璋昼夜攻阆州，庚辰城陷',33,'董璋昼夜','庚辰，城陷，',[('璋','连续攻城并攻陷者')],when='930年九月庚辰',place='阆州',note='主城陷日明确，旧十月乙巳为奏报、新纪直接乙巳系陷有时差，分别记，不用报告日覆盖主实际日。')
claim('event',E,'time_original','新明宗纪将董陷阆州、杀李仁矩和姚洪之死系于十月乙巳。',33,'乙巳，董璋陷閬州，殺節度使李仁矩，指揮使姚洪死之。','新本句十月承纪明确，与主九月庚辰城陷有纪时差；旧同乙巳是供奉官回奏，不能因此断新只是报告日，更不能抹平主日。电子本纸本待核。',source=ann,relation='conflicts')
claim('event',E,'time_original','旧明宗纪十月乙巳记张仁晖自利州回，奏董已陷阆州、李仁矩举家遇害。',33,'乙巳，供奉官張仁暉自利州回，奏董璋攻陷閬州，節度使李仁矩舉家遇害。','旧为回奏日，非已明确城陷发生乙巳；未读后续董光业丁未处刑不提前录此批。张仁晖只引句中的报告人，不凭快照全文新增其另事。',source=october,relation='adds')
E=ev('dong_kills_lirenju_family','董璋攻陷阆州后杀李仁矩，并灭其族',33,'庚辰，城陷，','灭其族。',[('璋','下杀令者'),('仁矩','城陷后被杀者')],when='930年九月庚辰城陷后；杀确日未独载',place='阆州',note='族未具姓名数，不新建虚构亲属；原主杀与旧举家、新家属皆见杀范围字异并列，不写成全阆州百姓被杀。')
claim('event',E,'description','新李仁矩传记李被擒，家属一同被杀。',33,'仁矩被擒，并其家屬皆見殺。','补被擒及家属范围，主族与新家属原分别留，不替换为族数或处刑方式。',source=fall,relation='corroborates')
E=ev('yaohong_former_dong_subordinate','追叙姚洪曾在董璋为梁将时隶其麾下',33,'初，璋为梁将，','姚洪尝隶麾下，',[('璋','后梁时期姚的原上级'),('洪','曾隶董麾下者')],year=None,when='后梁时期旧部往事；具体年未载',note='初追叙不用930作始年，不建跨终身当前统属，姚后拒董已不同阵营。')
claim('person',people['姚洪'],'description','新姚洪传称姚原为梁小校，曾事董，后事唐任指挥使。',33,'姚洪，本梁之小校也。自董璋為梁將，洪嘗事璋，後事唐為指揮使。','说明同一姚由梁至唐身份，不与姚洎姚顗混，未据此补确出生死亡月日。',source=yaolife,relation='adds')
E=ev('yaohong_garrisons_langzhou_thousand','姚洪率兵千人戍阆州',33,'至是，','将兵千人戍阆州；',[('洪','指挥使、率千人守阆者')],when='930年阆州城陷前的驻戍状态；始戍年日未独载',place='阆州',note='至是为城陷前已有驻军，不另定930本日首次派戍；千为史载兵数，新长兴中概叙但不补其独日。')
claim('event',E,'description','新姚传记长兴中遣姚将千人戍阆州。',33,'長興中，遣洪將千人戍閬州。','长兴中为补书宽纪时，不据此改主未具始戍日；与旧929保宁部署可有层次，不伪造具体续派令。',source=yaodeath,relation='corroborates')
E=ev('yaohong_rejects_dong_letter','董璋密书诱姚洪，姚将信投厕',33,'璋密以书诱之','洪投诸厕。',[('璋','密书诱旧部者'),('洪','投弃书信拒从者')],when='930年阆州陷落前；确日未载',place='阆州',note='原未说明所有许官许财，不造信全文或姚秘密已降又反；投诸厕动作按两书。')
claim('event',E,'description','新姚传亦记董以书招姚，姚得书投厕。',33,'董璋反，遣人以書招洪，洪得璋書，輒投厠中。','同案拒信，匿名使不新建人。',source=yaodeath,relation='corroborates')
E=ev('dong_captures_reproaches_yaohong','董璋城陷后执姚洪，责其负昔日奖拔',33,'城陷，璋执洪','今日何相负？”',[('璋','执旧部、责相负者'),('洪','被擒责者')],when='930年九月阆州陷后；确日未独载',place='阆州',note='奖拔恩为董自述，不独确认姚因其奖拔欠永久效忠；未受俘对话不写成朝廷审讯记录。')
E=ev('yaohong_denounces_dong_refuses_submission','姚洪斥董璋负天子，表明宁为天子死、不与董并生',33,'洪曰：','岂忍为汝所为乎！吾宁为天子死，不能与人奴并生！”',[('洪','被俘后拒从并责反者'),('璋','被斥负天子者')],when='930年阆州陷后受俘时',place='阆州',note='董李氏奴、拾粪恩都是姚话，不能另造本年童仆经历；李氏由新李七郎补语可识早年但不自动当李克用或李嗣源。宁死为誓语，死亡另录。')
E=ev('dong_executes_yaohong','董璋令壮士对姚洪施酷刑，姚至死仍骂',33,'璋怒，','洪至死骂不绝声。',[('璋','命处刑者'),('洪','受酷刑而死者')],when='930年九月阆州陷后；受刑确日未独载',place='阆州',note='十人是壮士执行者数，不是姚十子；自啖承壮士，不解作姚自己食肉，然镬原字不改，摘要不臆断现代刑法罪名。')
claim('event',E,'description','新姚传同记董命十壮士刲肉而食、姚至死大骂。',33,'璋怒，然鑊于前，令壯士十人刲其肉而食，洪至死大罵。','新与主同酷刑记述，承于城陷不独日；两书依存可能不当两份完全独立证言。',source=yaodeath,relation='corroborates')
E=ev('emperor_supports_yaohong_family','李嗣源置姚洪二子于近卫，厚给姚家',33,'帝置洪二子',None,[('帝','优抚遗属者'),('洪','死后遗属受优抚者')],when='930年闻阆州姚死后；确日未载',note='二子未名，不造姓名或分别建虚构儿子一二；录置近卫不等本人重新活任。')
claim('event',E,'description','新姚传记明宗闻姚死泣下、录其二子，厚恤其家。',33,'明宗聞之泣下，錄其二子，而厚卹其家。','补帝反应与恤家，未同日具体任官，不用无名子建亲属边。',source=yaodeath,relation='adds')
E=ev('fan_appointed_shumishi_an_stays','后唐以范延光为枢密使，安重诲仍任原职',34,'甲申，',None,[('延光','新任枢密使者'),('重诲','仍任枢密职者')],when='930年九月甲申',note='新增范而安如故，并非取代安离职；p32辞代与这里实任不同阶段。')
claim('event',E,'description','旧明宗纪同甲申记镇州节度使范延光授枢密使，兼检校太傅、守刑部尚书。',34,'甲申，以鎮州節度使範延光為檢校太傅、守刑部尚書，充樞密使。','镇州与主前成德衔为军镇名详略，范/範原字保留；兼衔不等本人已经专任刑部部务。',source=sept,relation='corroborates')
# -*- coding: utf-8 -*-
E=ev('court_strips_dong_orders_campaign','后唐下制削董璋官爵，兴兵讨伐',35,'丙戌，','兴兵讨之。',[('璋','被削官爵、受讨对象')],when='930年九月丙戌',note='制削与遣将是朝廷措施，不是本日已收复东川；前书董条件威胁不代替此时叛后的处分。')
claim('event',E,'description','旧明宗纪同丙戌记削董在身官爵、征兵进讨。',35,'丙戌，詔東川節度使董璋可削奪在身官爵，仍征兵進討。','同日制处分印证，未把官爵具体项目补成原未载清单。',source=sept,relation='corroborates')
E=ev('meng_appointed_southwest_supply','朝廷以孟知祥兼西南面供馈使',35,'丁亥，','以孟知祥兼西南面供馈使。',[('知祥','被命兼西南面供馈使者')],when='930年九月丁亥',note='供馈为供给职，不强解为本人已效忠送粮；孟此前实际与董举兵与朝廷名义授职可并列，不提前十一月削孟。')
claim('event',E,'description','旧明宗纪同丁亥任孟知祥西南面供馈使。',35,'丁亥，以西川節度使孟知祥兼西南面供饋使，','供饋/供馈繁简原字各留，授命不证明供馈实际已完成。',source=sept,relation='corroborates')
E=ev('shijingtang_appointed_dongchuan_commander','石敬瑭受任东川行营都招讨使',35,'以天雄节度','为东川行营都招讨使，',[('石敬瑭','天雄节度使、任东川行营都招讨使者')],when='930年九月丁亥',note='任命不是同日唐军已进剑门，保留此前天雄本职沿已有主体。')
claim('event',E,'description','旧明宗纪同丁亥任天雄石敬瑭东川行营都招讨使。',35,'天雄軍節度使石敬瑭兼東川行營都招討使，','任战役职与后续行军、权知分录。',source=sept,relation='corroborates')
E=ev('xialuqi_appointed_dongchuan_deputy','夏鲁奇受任东川行营招讨副使',35,'以天雄节度','以夏鲁奇为之副。',[('夏鲁奇','招讨副使、协同石敬瑭者')],when='930年九月丁亥',note='之副承招讨主将，由旧明示正式副职，不把夏在遂州守城当已随石北军同出。')
claim('event',E,'description','旧明宗纪记遂州节度使夏鲁奇兼东川行营招讨副使。',35,'以遂州節度使夏魯奇兼東川行營招討副使。','补正式副衔与本职，未来围城死亡不提前。',source=sept,relation='corroborates')
E=ev('mengsigong_fails_jizhou_attack','董璋使孟思恭分兵攻集州，孟轻进而败归',35,'璋使孟思恭','败归；',[('璋','派分兵者'),('思恭','分兵攻集、败归者')],when='930年集州分兵战事；主本段未独月日',place='集州',note='轻进为主归述，败归未具兵损数，不写成孟已战死；集州不误换为合州或后文遂州。')
E=ev('dong_sends_mengsigong_back','董璋因孟思恭败归而怒，遣还成都',35,'璋怒，','遣还成都，',[('璋','遣还败将者'),('思恭','被遣还成都者')],when='930年集州败归后；确月日未载',place='东川至成都',note='还成都非擅派人灭孟家，怒与遣为主明言。')
E=ev('meng_removes_mengsigong_office','孟知祥免孟思恭官',35,'知祥免其官','知祥免其官。',[('知祥','免官者'),('思恭','被免官者')],when='930年孟思恭遣还成都后；确月日未载',place='成都',note='其承孟思恭，未具免何具体职不强定所有爵禄；免非处死。集州败免案二十四史未检具体同案补句，主独证。')
E=ev('shijingtang_acting_dongchuan','朝廷以石敬瑭权知东川事',35,'戊子，','以石敬瑭权知东川事。',[('石敬瑭','被命权知东川者')],when='930年九月戊子',place='东川名义军政职',note='权知为暂摄任命，不等已攻克梓州实际接管。')
E=ev('wangsitong_appointed_western_vanguard','朝廷以王思同为西都留守兼行营马步都虞候，充伐蜀前锋',35,'庚寅，',None,[('王思同','受任西都留守、行营马步都虞候及伐蜀前锋者')],when='930年九月庚寅',place='西都、伐蜀前锋职',note='主右武卫上将军、旧右卫上将军衔异保留，西都与旧西京京兆称法佐核，不据任命补行军到达日。')
claim('event',E,'description','旧明宗纪同庚寅以右卫上将军王思同为京兆尹、西京留守兼西南行营马步都虞候。',35,'庚寅，以右衛上將軍王思同為京兆尹，充西京留守兼西南行營馬步都虞候。','主右武卫与旧右卫名差，并列不静默改职衔；旧京兆尹、西京及西南行营细节补，未核现代坐标。',source=sept,relation='adds')
reviews={
30:'董书欲杀三千及再一骑则反归董说、威胁非当刻已反。父亲董璋→董光业，光业宫苑在洛阳。示书李虔徽、派荀咸乂、光请止、李转安拒、董闻反、三镇奏、安帝话分。荀咸/鹹规范简体、主别将旧中使异详留；新兵未至已反补，报九月癸未不是主起反确日，旧此前五月传檄连叙与主九月差留，不把书里诀当光已死。',
31:'苏愿癸亥传朝廷欲讨为消息计划；赵副使攻守计未实际拿两城，孟邀董与先董反分。董移缴原字留，责离间归檄言。庚午李统、赵副、张先锋与三万攻遂分；四千是侯孟总军非各四千，侯沿已有身份。新侯四千助守东川 vs 主侯孟会攻阆任务异，不擅阶段解释；新会璋攻遂也不强把董当日置遂。',
32:'久专权中外恶众为史述无人数名单，王孟渐用事、短安是朝议不是全部罪已证。安表求解与甲戌求一镇、帝怒听去皆尚未实际罢；无种是假设免遭灭族非已全族死。范辞代不否定后甲申真任。帝遣孟议、冯宜罢、赵不可轻动分，新连乙未案后的求解概叙不倒赋乙未所有事。孟汉琼不混孟知祥思恭。',
33:'主重璋疑姓据董语境和新传识，不改原字不造重璋。诸将啖兵、新其受利我兵有说法差，旬日援是预测；李轻敌出未交溃为实际。主九月庚辰城陷，新明纪十月乙巳直接系陷为差；旧同乙巳张仁晖回奏为报告日，不能据旧就强说新也仅报道。杀李灭族人数未具；姚梁旧属追叙null，不造永久董部将边。姚千人驻态不定本日新派，书投厕、被擒责、姚斥、刑死、帝恤分。姚对董李氏奴是话，新李七郎不把李氏混李克用；十人执行壮士、自啖不是姚自己食，二子无名不造虚实名。新姚同书依存不当两独立口供。光业后十月被诛留主第41段，不提前。',
34:'九月甲申范任枢密安如故为并任，非替换；旧前镇州成德和兼刑部衔补，范/範原字留。',
35:'丙戌削董兴师、丁亥孟供馈石主夏副、戊子石权东、庚寅王前锋分。授孟供馈是名义授职不证实际送粮或已放弃与董举；石权东非已克梓。集州孟思恭分攻败、董遣回、孟免官未独月日不强嵌丁亥戊子间，更非杀。主王右武卫旧右卫衔差留；西都旧京兆西京不同称法。第36段交州及以后尚待，全年未完成。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(30,36):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=930,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(30,36)],next_paragraph='zztj-v277-y0930-p036',next_volume=277,next_year=930,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续930年第30—35段、原35—40行；董光业止兵书、两川举兵分将、安重诲请解职、阆州陷落姚洪之死及朝廷任将讨蜀。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(30,36)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
