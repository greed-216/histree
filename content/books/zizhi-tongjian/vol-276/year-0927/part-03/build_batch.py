# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 927, paragraphs 11–13."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 26))
specs=[
 ('tongjian-276-july-opening',YEAR/'part-01/sources/library/tongjian-276-july-opening','e38f4580','司马光等'),
 ('jiuwudaishi-038-october-conflict',P/'sources/library/jiuwudaishi-038-october-conflict','fa886303','薛居正等'),
 ('jiuwudaishi-074-zhushouyin',P/'sources/library/jiuwudaishi-074-zhushouyin','fa886303','薛居正等'),
 ('jiuwudaishi-097-fanyanguang-march',P/'sources/library/jiuwudaishi-097-fanyanguang-march','fa886303','薛居正等'),
 ('jiuwudaishi-067-zhaofeng-protest',P/'sources/library/jiuwudaishi-067-zhaofeng-protest','fa886303','薛居正等'),
 ('jiuwudaishi-131-sunsheng-flight',P/'sources/library/jiuwudaishi-131-sunsheng-flight','fa886303','薛居正等'),
 ('xinwudaishi-033-sunsheng-name',P/'sources/library/xinwudaishi-033-sunsheng-name','fa886303','欧阳修'),
 ('xinwudaishi-033-sunsheng-flight',P/'sources/library/xinwudaishi-033-sunsheng-flight','fa886303','欧阳修'),
 ('xinwudaishi-006-927-opening',ROOT/'content/books/zizhi-tongjian/vol-275/year-0927/part-01/sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
 ('jiuwudaishi-067-renhuan-retirement',YEAR/'part-01/sources/library/jiuwudaishi-067-renhuan-retirement','e38f4580','薛居正等'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-july-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0927-p011-p013',
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
for n in range(11, 14):
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
        citation = f'卷276·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0927_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'孙晨':'孙晟','徐知诰':'李昪','硃守殷':'朱守殷','李彦超':'符彦超','李鐸':'李铎','楚王殷':'马殷','王晏球':'杜晏球','帝':'李嗣源','仁赞':'孟昶','琼华':'琼华长公主','李从严':'李继曮','楚王殷':'马殷','高季兴':'高季昌'}
NEW_ALIASES={'孙晟':['孫晟','孙凤','孫鳳','孙忌','孫忌'],'马彦超':['馬彥超'],'宋敬':[],'王仁镐':['王仁鎬'],'药纵之':['藥縱之']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成二年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='927年十月本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_276_0927_' + code
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
        edge = 'participation_zztj_276_0927_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0927_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
october='jiuwudaishi-038-october-conflict'; zhu='jiuwudaishi-074-zhushouyin';fan='jiuwudaishi-097-fanyanguang-march';sun='jiuwudaishi-131-sunsheng-flight'
E=ev('siyuan_leaves_luoyang_for_bian','李嗣源从洛阳出发，准备赴汴州',11,'冬，','将如汴州；',[('帝','出行者')],when='927年十月乙酉',place='洛阳至汴州')
claim('event',E,'description','旧明宗纪同记乙酉驾发西京，并留崔协奉祠祭。',11,'乙酉，駕發西京，詔留宰相崔協以奉祠祭。','西京洛阳同城称谓；出发不当已到汴。',source=october,relation='corroborates')
E=ev('siyuan_arrives_xingyang','李嗣源到荥阳',11,'丁亥','至荥阳。',[('帝','到荥阳者')],when='927年十月丁亥',place='荥阳')
claim('event',E,'description','旧明宗纪同记丁亥帝宿荥阳。',11,'丁亥，帝宿於滎陽。','补宿留与繁简地名；不造新的同日抵达事件。',source=october,relation='corroborates')
E=ev('rumors_wu_attack_eastern_lords','民间流传皇帝将亲击吴或处置东方诸侯的讹言',11,'民间讹言','东方诸侯。',[],place='后唐民间',note='明确讹言，不当已公布军事行动、实际进攻或皇帝真实目的。')
E=ev('sunsheng_urges_zhu_revolt','宣武判官孙晟劝朱守殷反',11,'宣武节度使','劝守殷反，',[('孙晨','判官、劝反者'),('硃守殷','听劝且疑惧者')],place='汴州',note='主孙晨与后段孙晟，旧同朱幕宾赞成其事、旧注高密及新判官同episode识同人；疑晨字不注册正式别名。')
claim('person',people['孙晟'],'aliases','孙晟初名凤，又名忌；主本段孙晨疑晟字异文，与同卷后段孙晟及两五代史同职同事对应。',11,'孫晟初名鳳，又名忌，密州人也。','初名凤又忌为新正文原证；密州与主高密地方层级称谓不当两个出生地冲突，孙晨待纸本核。',source='xinwudaishi-033-sunsheng-name',relation='adds')
claim('event',E,'description','旧江南传称朱守殷据夷门叛时孙晟为幕宾，赞成其事。',11,'天成初，朱守殷據夷門叛，時晟為幕賓，贊成其事。','旧正文补同职同事，不把校注引其他书当独立来源。',source=sun,relation='corroborates')
E=ev('zhu_holds_bian_city','朱守殷乘汴州城拒守',11,'守殷遂','乘城拒守。',[('硃守殷','据城拒守者')],place='汴州')
claim('event',E,'description','旧朱守殷传称其驱市人闭壁以叛。',11,'守殷驅市人閉壁以叛，','补动员市民关闭城壁，不造全体市民均自愿参加事实。',source=zhu,relation='adds')
E=event('zhu_kills_mayanchao_songjing','朱守殷杀都校马彦超、副使宋敬',11,'守殷乃生雲夢之疑，遂殺都校馬彥超、副使宋敬。',[('朱守殷','杀部将者'),('马彦超','都校、被杀者'),('宋敬','副使、被杀者')],source=zhu,place='汴州',when='927年十月拒城前后，确日未载',note='旧朱传正文独补两受害人；不把云梦之疑当实际皇帝设伏。')
claim('event',E,'description','旧明宗纪丁亥条记朱守殷奏称马彦超谋乱、已斩。',11,'汴州朱守殷奏，都指揮使馬彥超謀亂，已處斬訖。','谋乱是朱的奏称，非史料已证马叛；丁亥条奏报不强等实际杀日。',source=october,relation='conflicts')
claim('event',E,'description','新明宗纪乙酉条称朱守殷反，马步军都指挥使马彦超死之。',11,'宣武軍節度使朱守殷反，馬步軍都指揮使馬彥超死之。','死之与旧朱奏谋乱不同评价并存，军职详略原样；新在乙酉条不强回填杀日。',source='xinwudaishi-006-927-opening',relation='adds')
E=ev('fan_ordered_admonish_zhu','李嗣源遣宣徽使范延光往谕朱守殷',11,'帝遣','往谕之，',[('帝','派遣者'),('范延光','宣徽使、受命往谕者'),('硃守殷','被谕对象')],place='荥阳至汴州',note='遣谕不是已谈判成功；当事人动作与随后进攻分阶段。')
E=ev('fan_requests_five_hundred_cavalry','范延光请求五百骑同行，并主张尽早攻汴城',11,'延光曰','与俱。”',[('范延光','提出急攻及兵额请求者')],place='荥阳',note='五百为所请骑兵额，不当守军总数；不早则坚为其预测。')
claim('event',E,'description','旧范延光传亦记请骑兵五百先赴，并以人心必骇为理由。',11,'延光曰：「若不急攻，賊堅矣。請騎兵五百，臣先赴之，則人心必駭。」','战术理由为当事人话语，非已证所有人心反应。',source=fan,relation='corroborates')
E=ev('siyuan_accepts_fan_cavalry_request','李嗣源接受范延光的骑兵请求',11,'帝从之。','帝从之。',[('帝','准许者'),('范延光','请求获准者')],place='荥阳')
E=ev('fan_night_march_bian','范延光暮发，在天明前行二百里抵大梁城下',11,'延光暮发','抵大梁城下，',[('范延光','率先夜行者')],place='荥阳至大梁',note='主二百里、旧二百余里并存；古里不自行折现代公里，未具时速或路线。')
claim('event',E,'description','旧范传称自酉时至夜央驰二百余里至城下。',11,'延光自酉時至夜央，馳二百餘里，奄至城下，','时间及二百余里补证；主未明与旧夜央略异，不强统一为精确速度。',source=fan,relation='adds')
E=ev('fan_fights_bian_defenders','范延光在大梁城下与汴人交战，汴人大惊',11,'与汴人战','汴人大惊。',[('范延光','先至交战者')],place='大梁城下',note='大惊为史述，不等此役已破城，也未具死伤或人数。')
E=ev('siyuan_jingshui_dispatches_shi','李嗣源到京水，遣御营使石敬瑭率亲兵倍道跟进',11,'戊子','倍道继之。',[('帝','到京水、遣军者'),('石敬瑭','御营使、率亲兵跟进者')],when='927年十月戊子',place='京水至汴州',note='派遣跟进与以后抵城分开，未给亲兵规模，不照五百骑填石军人数。')
E=ev('anonymous_urges_removing_retired_officials','有人向安重诲建议，趁叛军未破除去失职在外者',11,'或谓','不如除之。”',[('安重诲','听建议者')],place='后唐行在',note='匿名说话者不建人物；或能为患是假设指控，不当在外官已参与朱叛。')
E=ev('anzhonghui_requests_renhuan_death','安重诲奏遣使赐任圜死',11,'重诲以为然','赐任圜死。',[('安重诲','奏遣使者'),('任圜','拟赐死对象')],place='后唐行在至磁州',note='按主奏遣为史书说法；旧传称称制、诬构另列，不提前当程序已证合法。')
claim('event',E,'description','旧任圜传称安重诲趁朱叛诬任圜与之勾结，立遣人称制害之。',11,'及朱守殷叛，重誨乘間誣其結構，立遣人稱製就害之，','主奏遣与旧称制、诬构的叙述差别存证；罪名不当事实。',source='jiuwudaishi-067-renhuan-retirement',relation='conflicts')
E=ev('zhaofeng_protests_renhuan_death','赵凤哭着质问安重诲，称任圜为义士并反对滥刑',11,'端明殿学士','何以赞国！”',[('赵凤','端明殿学士、抗议者'),('安重诲','被质问者'),('任圜','被辩护者')],place='后唐行在',note='主哭胃疑谓字，原文保留；义士与安肯逆是赵意见，非独立人格证明。')
claim('event',E,'description','旧赵凤传称其在任圜被赐自尽后哭谓安重诲，重诲笑而不责。',11,'既而鳳哭謂安重誨曰：「任圜，義士也，肯造逆謀以讎君父乎？如此濫刑，何以安國！」重誨笑而不責。','旧哭谓补疑字；主将抗议置使到前、旧既而死亡后叙，次序不强统一，笑不责不推认错或撤令。',source='jiuwudaishi-067-zhaofeng-protest',relation='adds')
E=ev('renhuan_drinks_with_clan_on_envoy_arrival','使者到磁州，任圜聚族酣饮',11,'使者至磁州','圜聚其族酣饮，',[('任圜','聚族饮酒者')],place='磁州',note='无亲属姓名，族聚饮不等所有亲属同被杀。')
E=ev('renhuan_death_cizhou','任圜在磁州接赐死命后死亡',11,'使者至磁州',None,[('任圜','被赐死者')],when='927年十月，主未具日；旧纪十二日，新纪乙未',place='磁州',note='主夹述未明具日，不强当戊子或在己丑前；神情不挠为史叙，不外推死法或全族同死。')
claim('event',E,'time_original','旧明宗纪丙申收到磁州报告，称供奉官王仁镐于本月十二日到达、称制杀任圜。',11,'丙申，磁州刺史藥縱之上言，今月十二日，供奉官王仁鎬至，稱製殺太子少保致仕任圜。','丙申是奏报记载日，十二日为报告的发生日，不能把死亡强定丙申。',source=october,relation='adds')
claim('event',E,'time_original','新明宗纪记十月乙未杀太子少保致仕任圜。',11,'乙未，殺太子少保致仕任圜。','新乙未与旧本月十二日各存，不自行换算消除异日；主未具日。',source='xinwudaishi-006-927-opening',relation='conflicts')
E=event('yaozongzhi_reports_renhuan_killing','磁州刺史药纵之奏报王仁镐称制杀任圜',11,'丙申，磁州刺史藥縱之上言，今月十二日，供奉官王仁鎬至，稱製殺太子少保致仕任圜。',[('药纵之','磁州刺史、奏报者'),('王仁镐','供奉官、报告所指称制执行者'),('任圜','报告所指被害者')],source=october,when='927年十月丙申奏报，所报发生日为本月十二日',place='磁州至后唐朝廷',note='报告与杀事两层，不造另一死亡；执行者按报告识别，不推药亲自执行。')
E=ev('siyuan_arrives_bian_assault','李嗣源到大梁，唐军四面进攻，众多吏民缒城出降',12,'己丑','甚众。',[('帝','到城督攻者')],when='927年十月己丑',place='大梁',note='甚众不量化降者，未具谁指挥每路；旧以戊子翌日叙同阶段，不重造到城。')
claim('event',E,'description','旧朱传亦记禁军长围夹攻，缒城出降甚众。',12,'長圍夾攻，縋城甚眾。','同阶段围城降者补证，无具体人数。',source=zhu,relation='corroborates')
E=ev('zhu_kills_family_orders_own_death','朱守殷尽杀其族，命左右斩杀自己',12,'守殷知事','斩之。',[('硃守殷','杀族及自请斩杀者')],when='927年十月己丑',place='大梁',note='族人未具姓名数量，不虚构全城死数；引颈命斩不等亲手自刎。')
claim('event',E,'description','旧朱传亦记朱力屈尽杀其族，引颈令左右尽其命。',12,'守殷力屈，盡殺其族，引頸令左右盡其命。','同死亡机制补证，与新自杀概称不硬改主具体动作。',source=zhu,relation='corroborates')
claim('event',E,'description','新明宗纪己丑条概称朱守殷自杀。',12,'己丑，守殷自殺。','自杀为概述，同日主命左右斩具体过程并列。',source='xinwudaishi-006-927-opening',relation='adds')
E=ev('bian_defenders_open_gates','汴城守军望见乘舆，相率开门投降',12,'乘城者','开门降。',[],when='927年十月己丑',place='大梁',note='未具指挥姓名，不概称全部守军提前投降。')
claim('event',E,'description','旧范传补范延光先入城巷战，至厚载门歼朱党。',12,'翌日，守陴者望見乘輿，乃相率開門，延光先入，與賊巷戰，至厚載門，盡殲其黨，','同役入城细节补证；旧翌日相对叙事不强填精确干支，歼党不当全城屠杀。',source=fan,relation='adds')
E=event('zhu_corpse_flogged_head_displayed','唐诏鞭朱守殷尸，悬首都市七日后送洛阳',12,'詔鞭守殷屍，梟首懸於都市，滿七日，傳送洛陽。',[('朱守殷','死后刑罚对象')],source=zhu,when='927年十月汴州平后，悬首七日，确日未载',place='汴州市区至洛阳',note='死后处理不当又一次死亡；七日展示非战役历时，尸首传送阶段按原文。')
E=ev('sunsheng_flees_wu','孙晟逃奔吴',12,'孙晟奔吴','孙晟奔吴，',[('孙晟','奔吴者')],when='927年十月汴州失守之后，确日未载',place='汴州至吴',note='主概叙终点，不强同己丑当天已到吴。')
claim('event',E,'description','新孙晟传称朱城陷后孙弃妻子，亡命陈宋之间；安重诲画其像购捕未得，遂族其家。',12,'晟乃棄其妻子，亡命陳、宋之間。安重誨惡晟，以謂教守殷反者晟也，畫其像購之，不可得，遂族其家。','补逃亡中间地及家属遇害；族孙家区别于朱自杀族，不注册匿名家属；时序在奔吴前后未强日。',source='xinwudaishi-033-sunsheng-flight',relation='adds')
claim('event',E,'description','旧江南传称孙晟匿迹更名，弃妻子，亡命陈宋间。',12,'城陷，朱氏被誅，晟乃匿跡更名，棄其妻子，亡命於陳、宋間。','旧正文补途中更名，未给改后名字不猜；注引欧阳史不算独立确认族家。',source=sun,relation='adds')
E=ev('li_bian_hosts_sunsheng','徐知诰将孙晟留为宾客',12,'徐知诰',None,[('徐知诰','接纳为客者'),('孙晟','被接纳宾客')],when='927年十月汴州失守后逃吴阶段，确日未载',place='吴',note='徐知诰沿李昪既有主体，宾客不强为已经任相或937称帝后。')
E=ev('waives_finance_arrears','后唐诏免三司逋负近二百万缗',13,'戊戌',None,[('帝','免欠诏所归者')],when='927年十月戊戌',place='后唐各道州府',note='近二百万为概数，不当精确2000000或现金已付；欠账免除不同财政收入到账。')
claim('event',E,'description','旧明宗纪同诏列免同光三年以前秋夏税租、务局课利缺额、沿河舟船折欠及天成元年残欠夏税。',13,'戊戌，詔曰：「諸道州府，自同光三年已前所欠秋夏稅租，並主持務局敗闕課利，並沿河舟船折欠，天成元年殘欠夏稅，並特與除放。','补欠项与年限，沿原诏措辞，不将所有债务或未来税赋一概永久取消。',source=october,relation='adds')
review='连续11—13段逐句校核。乙酉离洛、丁亥到荥、戊子京水遣石、己丑大梁攻降分阶段；吴东方讹言非实策，朱疑惧为史解释。主孙晨与后孙晟，旧正文朱幕宾赞成、新判官同事识同人，晨疑字不正式别名；新初凤又忌明录，旧注高密标注性质非另源。朱杀马宋由旧传独补，旧朱奏马谋乱是其说不当定罪、新死之别评价存证，不强奏报日=杀日。范遣谕、请500骑、帝准、暮发二百里、城下战分事，主200旧200余、未明旧夜央未精算速度，旧翌日入城巷战不强干支。匿名向安献除失职者策不建人，可能患非已逆。安主奏遣/旧乘间诬构称制并列；赵主哭胃疑谓、旧哭谓原证，主前置抗议/旧既而杀后次序不强统一，义士为赵意见，笑不责不当撤令。任聚族饮与死亡分，族未死数；主无死日不强戊子或己丑前，旧丙申奏报、本月十二日发生与新乙未分别，报告独事不重造死亡，王按报告执行药仅上报。朱杀族命左右斩、新自杀概称同日补，旧鞭尸悬首7日传洛不同第二死；吏民及守军降未量化或全城，厚载巷战不当屠全城。孙逃吴主概说，补途中陈宋更名无新名、弃家与安画购族家不混朱族，李昪接宾不提前帝位相位。三司近二百万概数、旧税课船欠年限保留，非现金到账非永久免全部税；旧末重海与任圜重复等讹缺保存未作为姓名新建或强动机推断。简体展示原字摘录，纸本及异日待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,14):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(11,14)],next_paragraph='zztj-v276-y0927-p014',next_volume=276,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷276连续11—13段、原文件16—18行；汴州拒守、任圜死亡、孙晟逃吴及免欠诏。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(11,14)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
