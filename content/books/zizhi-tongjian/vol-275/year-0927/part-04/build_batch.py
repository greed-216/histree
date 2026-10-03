# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 16–18."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 33))
specs=[
 ('jiuwudaishi-038-lutai-report',P/'sources/library/jiuwudaishi-038-lutai-report','69768554','薛居正等'),
 ('jiuwudaishi-038-lutai-narrative',P/'sources/library/jiuwudaishi-038-lutai-narrative','69768554','薛居正等'),
 ('tongjian-275-lutai-aftermath',P/'sources/library/tongjian-275-lutai-aftermath','69768554','司马光等'),
 ('tongjian-275-chengdu-and-jingnan',P/'sources/library/tongjian-275-chengdu-and-jingnan','69768554','司马光等'),
 ('xinwudaishi-064-lirenju-mission',P/'sources/library/xinwudaishi-064-lirenju-mission','69768554','欧阳修'),
 ('tongjian-275-927-offices-and-khitan',YEAR/'part-02/sources/library/tongjian-275-927-offices-and-khitan','6ee141a6','司马光等'),
 ('xinwudaishi-006-927-opening',YEAR/'part-01/sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
 ('xinwudaishi-069-jingnan-conflict',YEAR/'part-03/sources/library/xinwudaishi-069-jingnan-conflict','c7025a3a','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-927-offices-and-khitan','tongjian-275-lutai-aftermath','tongjian-275-chengdu-and-jingnan']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0927-p016-p018',
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
for n in range(16, 19):
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
        citation = f'卷275·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_275_0927_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','庄宗':'李存勖','从荣':'李从荣','楚王殷':'马殷','高季兴':'高季昌'}
NEW_ALIASES={'龙晊':['龍至','龙至'],'李仁矩':[]}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷275天成二年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='927年正月本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_275_0927_' + code
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
        edge = 'participation_zztj_275_0927_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_275_0927_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
pk=person('皇甫晖',16,'史书追叙魏州牙兵克梁有功、后来皇甫晖张破败之乱导致庄宗亡','初，庄宗之克梁也，以魏州牙兵之力；及其亡也，皇甫晖、张破败之乱亦由之。')
claim('person',pk,'description','本段作者将魏州牙兵参与克梁与后来皇甫晖张破败之乱并置。',16,'初，庄宗之克梁也，以魏州牙兵之力；及其亡也，皇甫晖、张破败之乱亦由之。','克梁与庄宗亡是已录前事，不重复创建两次事件；因果为史书概述不等唯一原因。')
E=ev('zhaozaili_refused_huazhou_review','追叙赵在礼移滑州不赴任，史书记其受部下制约',16,'赵在礼之徙','其下所制。',[('赵在礼','已任而不赴镇者')],year=None,when='927卢台段追叙926年义成任命及拒赴镇',place='邺都与滑州',stable_key='event_zztj_275_0926_zhaozaili_yicheng_appointment_refused',note='复用926已发布同一任命拒赴事件；本引补受部下制约，不新造一次927拒赴滑州。')
E=ev('zhaozaili_secretly_requests_transfer','赵在礼为脱离祸患，暗遣腹心赴阙请求移镇',16,'在礼欲','求移镇，',[('赵在礼','秘密请移镇者')],year=None,when='927年三月调军前的请移镇前事，确日未载',place='邺都至后唐朝廷',note='腹心未名不造人物；旧请赴朝觐与主请移镇为不同措辞。')
claim('event',E,'description','旧明宗纪称在礼冀脱祸，潜奏愿赴朝觐。',16,'在禮冀脫其禍，潛奏願赴朝覲，','与主移镇动机相关而请求措辞不同，分别引用。',source='jiuwudaishi-038-lutai-narrative',relation='adds')
E=ev('huangfuhui_chenzhou_zhaojin_beizhou','朝廷任皇甫晖陈州刺史、赵进贝州刺史',16,'帝乃','贝州刺史，',[('帝','任命者'),('皇甫晖','陈州刺史'),('赵进','贝州刺史')],when='927年三月卢台乱前调军任命，确日未载',place='陈州、贝州及朝廷',note='陈不是辰；未给各人到任日期。')
E=ev('zhaozaili_henghai_congrong_yedu','赵在礼任横海节度使，李从荣镇邺都，范延光奉命领兵送并制置军事',16,'赵在礼为','制置鄴都军事。',[('赵在礼','横海获任者'),('从荣','皇子、镇邺者'),('范延光','宣徽北院使、护送及制置军事者')],when='927年三月卢台乱之前，确日未载',place='横海军、邺都',note='与926从荣天雄授职有新的实际镇邺护送阶段；命送不当当时已全部完成军务。')
E=ev('longzhi_nine_units_march_lutai','派奉节等九指挥三千五百人由龙晊领赴卢台备契丹，不给铠仗，只以长竿旗帜分队',16,'乃出奉节','俛首而去。',[('帝','调军安排所归朝廷'),('龙晊','军校、统领九指挥')],when='927年三月卢台乱前调军',place='邺都至卢台军',note='九指挥3500为此次调部，不等旧银枪8000全军；旧龙至同部同事与主龙晊沿同人，不凭字形再建军校。')
claim('event',E,'description','旧明宗纪称北御契丹时不支甲胄，仅长竿旗帜表队伍。',16,'是行也，不支甲胄，惟幟於長竿表隊伍而已，故俯首遄征。','与主同部旧叙；甲胄与兵仗各用书词，不虚构全员手中完全无任何武器。',source='jiuwudaishi-038-lutai-narrative',relation='corroborates')
E=ev('lutai_rumors_liyan_and_wuzhen','赴卢台军途中闻孟知祥杀李严，讹言出现；抵达后乌震获擢副招讨令讹言加剧',16,'中涂闻','讹言益甚。',[('孟知祥','已发生杀李严之讯所归主体'),('李严','死讯所涉者'),('乌震','擢任引发讹言所涉者')],when='927年三月部队赴卢台沿途及到后，确日未载',place='赴卢台道路及卢台军',note='复述死讯不重复李严死亡事件；朝延疑朝廷、不次为书评价，未给讹言具体内容不可猜。')
claim('event',E,'description','旧明宗纪称部队闻杀严，以为剑南阻绝，互相煽动；乌震代房又增浮说。',16,'在途聞李嚴為孟知祥所害，以為劍南阻絕，互相煽動。及屯於盧台，會烏震代房知溫為帥，轉增浮說。','剑南阻绝是军中猜测不作真实断路，独立书证但可能叙事相依。',source='jiuwudaishi-038-lutai-narrative',relation='adds')
E=ev('fang_resents_wuzhen_handover_pending','房知温怨乌震骤来代己，乌震到后尚未交印',16,'房知温怨','未交印。',[('房知温','史叙怨替代者'),('乌震','到任待交印者')],when='927年三月壬申之前、乌到后',place='卢台军',note='补明前批归兖是安排而未实交，不把怨情单独扩成终身敌对边。')
E=ev('wuzhen_east_camp_invitation','乌震召房知温及齐州防御使到东寨',16,'壬申','安神博于东寨，',[('乌震','东寨召见者'),('房知温','被召者')],when='927年三月壬申',place='卢台东寨',note='底本齐州防御使安神博疑异文，旧有震与房博于东寨；未确定身份，暂不注册安神博或强并安审通，不静默改原文。')
E=ev('fang_induces_wuzhen_killing','房知温诱龙晊所部在席上杀乌震，部众在营外鼓噪',16,'知温诱','营外，',[('房知温','主书所记诱兵杀震者'),('龙晊','涉乱所部军校，不当本人明确亲手行刺'),('乌震','席上遇杀者')],when='927年三月壬申',place='卢台东寨及营外',note='诱为主书所记，后房奏只称戍军乱；同一杀事保留不同叙述。')
claim('person',people['乌震'],'death_year','乌震于927年卢台兵变中被杀。',16,'知温诱龙晊所部兵杀震于席上，','主干支壬申；旧房奏前月二十一与奏日另存，不把奏日作死日。')
claim('event',E,'time_original','旧明宗纪四月辛巳朔房知温奏称前月二十一日戍军杀乌震。',16,'夏四月辛巳朔，房知溫奏：「前月二十一日，盧台戍軍亂，害副招討寧國軍節度使烏震，','房奏为三月事的报告，四月辛巳是报告日；未自行换算公历。',source='jiuwudaishi-038-lutai-report',relation='adds')
claim('event',E,'description','新明宗纪记三月卢台乱、杀将乌震。',16,'盧臺亂，殺其將烏震。','概叙同事件，不取后四月龙晊伏诛倒作此时已全剿。',source='xinwudaishi-006-927-opening',relation='corroborates')
E=ev('anshentong_escapes_holds_cavalry','安审通脱身夺舟渡河，统骑兵按甲不动',16,'安审通脱身','按甲不动。',[('安审通','渡河控制骑兵者')],when='927年三月壬申杀震后',place='卢台河西',note='此处原文明安审通，沿已存齐州主体；不因前疑名给他无证亲手杀震角色。')
E=ev('fang_deceives_soldiers_crosses_river','房知温欲出营被士卒拦辔，以收河西骑兵为说辞后登舟渡河',16,'知温恐','登舟济河，',[('房知温','受阻、以说辞离营渡河者')],when='927年三月壬申杀震后',place='卢台营门至河西',note='知温给之疑绐保留原字，话语所称收马兵不等真欲率乱兵成事。')
E=ev('fang_an_plan_attack_rebels','房知温与安审通合谋攻击乱兵，乱兵向南行',16,'与审通合谋','乱兵遂南行。',[('房知温','渡河合谋击乱者'),('安审通','与房谋击者')],when='927年三月壬申之后',place='卢台河西及南行路线',note='主乱兵自行南行/旧令卷甲南行为安排细节不同，各存。')
claim('event',E,'description','旧明宗纪称房安谋伺便攻之，并令乱兵卷甲南行。',16,'安審通戢騎軍不動，知溫與審通謀，伺便攻之，令亂兵卷甲南行。','旧令乱南行补充，与主自行语气不覆盖。',source='jiuwudaishi-038-lutai-narrative',relation='adds')
E=ev('cavalry_follows_night_march','骑兵整队缓随，乱兵失色、列炬夜行并疲于荒泽',16,'骑兵徐','疲于荒泽，',[('房知温','承前骑军合谋所归房'),('安审通','承前骑军合谋所归安')],when='927年三月壬申夜及其后追击',place='卢台南面荒泽',note='不自行添现代具体地名坐标或行军公里数。')
E=ev('dawn_attack_rebels_old_camp_burned','翌晨骑兵四合击乱军，余众返故寨而安审通已焚寨，乱军溃散',16,'诘朝','遂溃。',[('房知温','承前骑军参与镇压者'),('安审通','焚故寨、骑军参与者')],when='927年三月壬申夜行后诘朝，确日未另记',place='卢台南面及故寨',note='乱兵殆尽非精确全灭；焚寨先于余返，时间与执行骑兵分开。')
claim('event',E,'description','旧明宗纪称迟明房等击乱军，余众返寨已焚；翌日尽戮，草沟脱免十无二三。',16,'遲明，潛令外州軍別行，知溫等遂擊亂軍，橫屍於野，餘眾復趨舊寨，至則已焚之矣。翌日，盡戮之，脫於叢草溝塍者十無二三，','主一二/旧二三的脱免比例各存概数，未将旧王都败后的后事提前927。',source='jiuwudaishi-038-lutai-narrative',relation='adds')
claim('event',E,'description','主书称藏丛薄沟塍逃免者十无一二。',16,'其匿于丛薄沟塍得免者什无一二。','比例是概述，不凭3500乘比算确切死亡人数。')
claim('event',E,'description','房知温奏称与安审通已斩杀乱兵，朝廷为乌震废朝一日、赠太傅。',16,'尋與安審通斬殺亂兵訖。」帝聞之，廢朝一日，贈震太傅。','房奏只称平乱，主另述其诱杀；这是奏报与追赠补证，不把他自述当证明未参与起乱。',source='jiuwudaishi-038-lutai-report',relation='adds')
E=ev('fanyanguang_reinforces_yedu','范延光还到淇门闻卢台乱，发滑州兵返邺都以防逃逸乱兵',16,'范延光还',None,[('范延光','调滑州兵防奔逸者')],when='927年三月闻卢台乱之后',place='淇门、滑州至邺都',note='防奔逸不等已捕全部逃兵；鄴简化作邺，原文不改。')
E=ev('lirenju_mission_and_chengdu_arrival','李嗣源遣李仁矩传诏安谕孟知祥及吏民，甲戌到成都',17,'帝遣',None,[('帝','遣使者'),('李仁矩','客省使、传诏者'),('孟知祥','受安谕者')],when='927年三月甲戌抵成都，派遣日未载',place='后唐朝廷至成都',note='甲戌是到日不强当遣日，安谕不等已答允全部朝命。')
claim('event',E,'description','新蜀世家亦记明宗遣客省使李仁矩慰谕知祥，并送琼华公主及子昶等归蜀。',17,'乃遣客省使李仁矩慰諭知祥，并送瓊華公主及其子昶等歸之。','补同次使事，新送亲属不等在甲戌已全到；主后段四月丙申家属到尚待读，不提前处理。',source='xinwudaishi-064-lirenju-mission',relation='adds')
E=ev('liu_arrives_jingnan','刘训所部到荆南',18,'刘训兵','至荆南，',[('刘训','率军到荆南者')],when='927年三月甲戌之后本段，确日未载',place='荆南',note='到军不等攻克江陵。')
claim('event',E,'description','新荆南世家称明宗令襄州刘训为招讨使攻季兴。',18,'明宗乃以襄州劉訓為招討使，攻之，','补同一战役对象与军镇，不提前引后攻不克及西方三州战果。',source='xinwudaishi-069-jingnan-conflict',relation='corroborates')
E=ev('chu_water_army_yuezhou','马殷遣许德勋等率水军屯岳州',18,'楚王殷','屯岳州。',[('楚王殷','遣军楚王'),('许德勋','都指挥使、领水军者')],when='927年三月荆南役本段，确日未载',place='岳州',note='等未名不造其他统帅，不推水军已到江陵或船数兵额。')
E=ev('jingnan_holds_defenses_requests_wu','荆南坚壁不战，向吴求救',18,'高秀兴','求救于吴，',[('高季兴','荆南守方主体，底本高秀兴疑季')],when='927年三月荆南役，确日未载',place='荆南',note='高秀兴疑高季兴：同段承刘军所讨荆南、后文高季兴、独立新世家季兴受攻同役；沿高季昌，不注册高秀兴正式别名或新主体，纸本待校。')
E=ev('wu_sends_jingnan_water_relief','吴派水军援荆南',18,'吴人遣',None,[],when='927年三月荆南求救后，确日未载',place='吴至荆南方向',note='未载统帅名、船数兵额，不虚构徐温亲自统军或已击退刘训。')
review='连续16—18段逐句校核。魏兵克梁及后来亡庄宗是前史因果概述不重复建史事，赵旧义成拒赴滑州复用926稳定事件及参与。秘密请求主移镇/旧朝觐分说；皇甫陈赵进贝赵横海、从荣实际镇邺及范送制置、龙九指挥3500备契丹不支铠仗分事，九部与银枪8000历史军额不混。龙晊/旧龙至同部同役校同人。闻李严死讹言不造新死事件，剑南阻绝是军中猜测。房怨及未交印补明前归兖不是已完成。主宴安神博疑异文，旧震与房博于东寨，暂不注册疑名或强挂安审通宴席身份；后安原文明，沿现存齐州主体。主房诱兵杀乌/房奏仅戍军乱后自平分叙述，旧四月辛巳报告前月21不是杀震在四月；新三月概叙补。安渡河不动骑、房出门绐语渡、合谋乱南行、骑缓随夜行、诘朝围击焚寨、范防奔逸分事，不造精确死亡。主逃免十无一二/旧十无二三概数并存，旧王都败后事不提前。李传诏三月甲戌是到日，亲属回蜀新概述只补使事，主四月丙申家属到后段未读不标完。刘到军、楚许水军岳、荆南固守求吴援分录，主高秀兴疑季兴据同役新季兴受刘攻与主后同名沿高季昌不立疑名别名，援军无统帅兵额不猜。简体展示、摘录底本不改，纸本及异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(16,19):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(16,19)],next_paragraph='zztj-v275-y0927-p019',next_volume=275,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷275连续16—18段、原文件90—92行；卢台乱、成都使事及荆南楚吴水军。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(16,19)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
