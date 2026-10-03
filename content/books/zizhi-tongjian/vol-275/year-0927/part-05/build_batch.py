# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 19–24."""
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
 ('jiuwudaishi-038-jingnan-april',P/'sources/library/jiuwudaishi-038-jingnan-april','4b8f7b80','薛居正等'),
 ('jiuwudaishi-038-min-withdrawal',P/'sources/library/jiuwudaishi-038-min-withdrawal','4b8f7b80','薛居正等'),
 ('jiuwudaishi-136-mengchang-parentage',P/'sources/library/jiuwudaishi-136-mengchang-parentage','4b8f7b80','薛居正等'),
 ('tongjian-275-chengdu-and-jingnan',YEAR/'part-04/sources/library/tongjian-275-chengdu-and-jingnan','69768554','司马光等'),
 ('jiuwudaishi-038-lutai-narrative',YEAR/'part-04/sources/library/jiuwudaishi-038-lutai-narrative','69768554','薛居正等'),
 ('xinwudaishi-064-lirenju-mission',YEAR/'part-04/sources/library/xinwudaishi-064-lirenju-mission','69768554','欧阳修'),
 ('xinwudaishi-069-jingnan-conflict',YEAR/'part-03/sources/library/xinwudaishi-069-jingnan-conflict','c7025a3a','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-chengdu-and-jingnan']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0927-p019-p024',
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
for n in range(19, 25):
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
    ck = f'claim_zztj_275_0927_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','仁赞':'孟昶','琼华':'琼华长公主','李从严':'李继曮','楚王殷':'马殷','高季兴':'高季昌'}
NEW_ALIASES={'孟昶':['孟仁赞','孟仁贊'],'琼华长公主':['瓊華長公主'],'李氏（孟昶母）':[]}
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
E=ev('lutai_families_execution_edict','朝廷敕令卢台乱兵在营家属全门处斩',19,'夏，','全门处斩。',[('帝','下敕所归者')],when='927年四月庚寅',place='后唐朝廷至邺都',note='此为命令，实际执行另录；未具亲属姓名不虚构受害者。')
claim('event',E,'description','旧明宗纪诏称龙至所部九指挥三千五百人在营家口骨肉可全家处斩。',19,'詔：「盧台亂軍龍至所部鄴都奉節等九指揮三千五百人在營家口骨肉，並可全家處斬。」','3500旧此句为军人编部，主3500家为家户，不互换单位；旧龙至沿已识龙晊。',source='jiuwudaishi-038-lutai-narrative',relation='corroborates')
E=ev('lutai_families_killed_in_lime_kiln','敕到邺都，九指挥闭门，将三千五百家万余人驱至石灰窑全部斩杀',19,'敕至','悉斩之，',[],when='927年四月庚寅敕至邺都之后，执行确日未另记',place='邺都石灰窑',note='主家户3500、人数万余是作者记数；万余概数不写10000精确，不具窑坐标和执行者名。')
claim('event',E,'description','主书称杀后永济渠变赤。',19,'永济渠为之变赤。','史料所述后果保留归书，未把文学性叙述换算水量或血量。')
E=ev('fang_rewarded_shizhong','朝廷加房知温兼侍中，史书称虽知其首乱仍欲安定反侧者',19,'朝廷虽知',None,[('帝','加官所归朝廷'),('房知温','兼侍中获授者')],when='927年四月癸巳',place='后唐朝廷',note='任命为史事，朝廷知首乱及安反侧为主书动机解释，不作读心独立证据。')
claim('event',E,'description','旧明宗纪同日称房知温加侍中、安审通加检校太傅，并以卢台之功奖赏。',19,'癸巳，兗州節度使房知溫加侍中，齊州防禦使安審通加檢校太傅，並賞盧台之功也。','补安授衔及旧以功叙述，与主知首乱安反侧不同解释各标出处。',source='jiuwudaishi-038-lutai-narrative',relation='adds')
E=event('anshentong_taifu_reward','安审通加检校太傅，旧书记以卢台之功奖赏',19,'癸巳，兗州節度使房知溫加侍中，齊州防禦使安審通加檢校太傅，並賞盧台之功也。',[('安审通','齐州防御使、获加检校太傅')],when='927年四月癸巳',place='后唐朝廷',source='jiuwudaishi-038-lutai-narrative',note='同日不同获授者独录，不等认可其无起乱责任。')
E=ev('wuzhang_fetches_meng_family','孟知祥遣武漳到晋阳迎妻琼华长公主及子仁赞',20,'先是','于晋阳，',[('孟知祥','遣迎者'),('武漳','文水人、牙内指挥使、迎家者'),('琼华','孟妻、被迎者'),('仁赞','孟子、被迎者')],year=None,when='927年四月入成都前的先是追叙，派遣日未载',place='晋阳至蜀',note='先是前事不强归四月；仁赞按旧初名证识孟昶，未提前当927已帝。')
claim('person',people['孟昶'],'aliases','孟昶初名仁赞；主书本段仁赞与新蜀世家送昶记载同一归蜀家属。',20,'昶，知祥之第三子也。〈（《宋朝事實》云：昶，初名仁贊。','初名证来自旧五代史所载校注，注明性质，不另注册范围外宋朝事实独立source。',source='jiuwudaishi-136-mengchang-parentage',relation='adds')
relationship('孟知祥','仁赞','父亲',20,'孟知祥遣牙内指挥使文水武漳迎其妻琼华长公主及子仁赞于晋阳，','其子明确父孟知祥，不猜排行。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','旧僭伪列传明称昶为知祥第三子。',20,'昶，知祥之第三子也。','补子次不改父子方向。',source='jiuwudaishi-136-mengchang-parentage',relation='corroborates')
relationship('琼华','孟知祥','妻子',20,'孟知祥遣牙内指挥使文水武漳迎其妻琼华长公主及子仁赞于晋阳，','妻子至丈夫，妻与子并列不推出妻为此子生母。')
E=ev('fengxiang_holds_meng_family','李继曮闻孟知祥杀李严，家属到凤翔时将其留住并奏报',20,'及凤翔','以闻，',[('李从严','凤翔节度使、留家属奏报者'),('孟知祥','消息所涉者'),('李严','死亡消息所涉者')],year=None,when='李严被杀之后至927年四月家属到成都前，确日未载',place='凤翔',note='底本拆字名沿既有凤翔李继曮及赐从曮，不并监军李严，不复制李严死亡。')
claim('event',E,'description','新蜀世家称凤翔李从曮闻杀严，以为孟反而留家属。',20,'行至鳳翔，鳳翔節度使李從曮聞知祥殺李嚴，以為知祥反矣，遂留之。','以为反为李的判断，不据此宣布孟此日已公开独立。',source='xinwudaishi-064-lirenju-mission',relation='adds')
E=ev('siyuan_allows_meng_family_to_shu','李嗣源允许孟知祥家属归蜀',20,'帝听','其归蜀；',[('帝','允许者')],year=None,when='凤翔奏报之后、927年四月丙申到成都前，许归日未载',place='后唐朝廷至凤翔、蜀')
E=ev('meng_family_chengdu_arrival','琼华长公主及孟仁赞一行到成都',20,'丙申',None,[('琼华','到成都者'),('仁赞','到成都者')],when='927年四月丙申',place='成都',note='到日明记，不把三月李仁矩到日甲戌误当家属到日。')
claim('event',E,'description','旧僭伪列传称孟昶与生母李氏随孟妻琼华长公主同入蜀。',20,'及知祥鎮蜀，昶與其母從知祥妻瓊華長公主同入於蜀。','补同程生母，明确妻与母不是同一人；旧此句未具到日，不将旧同光二年丙戌疑错年句套主到日。',source='jiuwudaishi-136-mengchang-parentage',relation='adds')
relationship('李氏（孟昶母）','仁赞','母亲',20,'母李氏，本莊宗之嬪御，以賜知祥。','旧前句传主昶明确母李氏，限定传主区分同姓；不能建琼华生母边。',source='jiuwudaishi-136-mengchang-parentage')
E=ev('meng_requests_zhaojiliang_deputy','孟知祥因与盐铁判官赵季良有旧，奏留为副使',21,'盐铁判官','为副使。',[('孟知祥','奏留者'),('赵季良','盐铁判官、拟留副使')],year=None,when='927年四月丁酉朝命之前奏请，确日未载',place='成都奏后唐朝廷',note='有旧不强建亲属师徒盟友；奏请与获任分事。')
E=ev('zhaojiliang_xichuan_deputy','赵季良获任西川节度副使',21,'朝廷不得已','西川节度副使。',[('帝','任命所归朝廷'),('赵季良','获任副使')],when='927年四月丁酉',place='西川、成都',note='不得已是主书解释，不外推失去所有控制权。')
E=ev('lihao_returns_shu_observer','李昊归蜀，孟知祥任其观察推官',21,'李昊归蜀',None,[('李昊','归蜀、获任者'),('孟知祥','授推官者')],when='927年四月丁酉段之后本段概叙，确日未载',place='蜀、成都',note='不把归日授日强套丁酉，不提前后观察判官或翰林学士任命。')
E=ev('jingnan_rain_supply_disease','江陵久雨且粮道不继，军中疾疫，刘训卧病',22,'江陵卑湿','亦寝疾；',[('刘训','卧病招讨使')],when='927年四月癸卯遣使之前',place='江陵',note='气候粮道和疾疫为史叙关联，不给现代病原诊断、死亡数或温雨量。')
E=ev('kongxun_dispatched_inspect_campaign','李嗣源遣孔循往荆南探视并审察攻战是否适宜',22,'癸卯',None,[('帝','遣使者'),('孔循','枢密使、探视审战者')],when='927年四月癸卯据主，旧辛丑后记遣',place='后唐朝廷至江陵行营',note='派遣不等本日已抵江陵。')
claim('event',E,'description','旧明宗纪在辛丑事项后记遣孔循赴荆南城下，因刘训有疾。',22,'遣樞密使孔循赴荊南城下，時招討使劉訓有疾故也。','旧前辛丑与主癸卯篇内定位分存；未武断旧明确本句另有干支，单记录前后位置。',source='jiuwudaishi-038-jingnan-april',relation='adds')
E=ev('yanjun_weiwu_and_langya','王延钧获任威武节度使、守中书令、琅邪王',23,'五月',None,[('帝','任命所归者'),('王延钧','留后转正及获封者')],when='927年五月癸丑',place='闽、威武军',note='本道承威武不写突然建新国；琅邪原字与旧琅琊郡王称谓并列。')
claim('event',E,'description','旧明宗纪同日称王延钧任福建节度使，检校太师、守中书令、琅琊郡王。',23,'五月癸丑，以福建留後、檢校太傅、舒州刺史王延鈞為檢校太師、守中書令，充福建節度使、琅琊郡王；','福建军州名与主威武、王与郡王衔保留不同文字，不造两次冊命。',source='jiuwudaishi-038-min-withdrawal',relation='adds')
E=ev('kongxun_arrives_unsuccessful_assault','孔循到江陵，攻城未克并遣人入城劝高季兴，高不逊',24,'孔循至','季兴不逊。',[('孔循','到江陵督视、遣说者'),('高季兴','拒说不逊者')],when='927年五月本段，丙寅赐衣前，确日未载',place='江陵',note='未具谁亲自临阵，不把孔本人行杀攻细节补成实证；不逊是书评价，书未录劝辞。')
claim('event',E,'description','新荆南世家亦称刘训奉招讨攻高季兴而不克。',24,'明宗乃以襄州劉訓為招討使，攻之，不克，','同役刘军失败补证，不重复创建另一攻城。',source='xinwudaishi-069-jingnan-conflict',relation='corroborates')
E=ev('hunan_camp_summer_clothes','朝廷遣使赐湖南行营夏衣万袭',24,'丙寅','万袭；',[('帝','赐衣所归者')],when='927年五月丙寅',place='湖南行营',note='万袭为衣套不当战兵总数；赐令未具每个营实际领到数。')
E=ev('ma_yin_gifts_food_request_unmet','朝廷赐马殷鞍马玉带并督馈粮，最终未获粮',24,'丁卯','竟不能得。',[('帝','赐物督粮者'),('楚王殷','受赐及被督馈粮者')],when='927年五月丁卯赐物督粮，未获粮为其后结果',place='楚及荆南行营',note='并未说明楚私藏粮或故意毁粮，不把未获馈粮推为已正式叛唐。')
E=ev('jingnan_withdrawal_order','后唐诏刘训等引兵还',24,'庚午',None,[('帝','撤军敕命者'),('刘训','受命引兵还者')],when='927年五月庚午',place='荆南行营返程',note='诏还不凭此句称所有部队已抵本镇。')
claim('event',E,'description','旧明宗纪记庚午罢荆南师，随后令军士散掠居民而回。',24,'庚午，詔罷荊南之師，既而令軍士散掠居民而回。','旧独补掠居民命令与回程，不造精确受害人数财物数量。',source='jiuwudaishi-038-min-withdrawal',relation='adds')
review='连续19—24段逐句校核。庚寅家属全门杀令与敕到执行分事，主3500家/旧3500军人在营家口不同计量，万余概数不当10000精准，渠变赤史叙不算血水量。主房首乱而欲安反侧与旧赏功不同动机标出处，癸巳加房和旧补安检校不同获授人。孟家迎先是前日不强四月，武沿已有人。主仁赞据旧初名注及新昶同归识孟昶；初名来自旧所载校注，不新增专书source。琼华孟妻不是昶生母，旧母李氏与琼同行明别，限定李氏孟昶母另建；父、妻、母方向明确，不猜公主父族或亲生关系。凤翔拆字沿既有李继曮赐从曮不并监军李严，以为反是留人者判断。派遣许归日未知null，丙申到成都明确，不混三月李使甲戌。旧尾同光二年丙戌疑错年未使用，后帝位与死不提前本批。赵奏留副使前事/丁酉朝任分开，有旧不建亲属；李昊归授不强丁酉，不提前后来判官翰林。江陵雨粮疾病不做现代病名确诊，癸卯遣孔与旧前辛丑后叙位置差异保留、不硬说旧本句明确辛丑派；派日到日分。五月王同日主威武琅邪王/旧福建琅琊郡王衔名各存，留后转正非重复新建国。孔到攻不克遣说、不逊评价、丙寅衣万袭为衣套非兵数、丁卯赐楚督粮未获不推楚已叛，庚午撤令不强全部抵镇，旧回程散掠命令补证无具人数。简体展示、原字摘录保持，纸本及异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(19,25)],next_paragraph='zztj-v275-y0927-p025',next_volume=275,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷275连续19—24段、原文件93—98行；卢台家属、孟家归蜀、赵李任官、荆南战事及闽册命。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(19,25)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
