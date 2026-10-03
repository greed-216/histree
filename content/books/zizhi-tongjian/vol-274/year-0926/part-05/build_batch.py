# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 274, year 926, paragraphs 41–43."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 44))
PREV=YEAR/'part-04'
specs=[
 ('tongjian-274-926-march-and-wangyan',PREV/'sources/library/tongjian-274-926-march-and-wangyan','378d632d','司马光等'),
 ('tongjian-274-926-return-to-luoyang',P/'sources/library/tongjian-274-926-return-to-luoyang','572ee184','司马光等'),
 ('jiuwudaishi-051-926-congjing',PREV/'sources/library/jiuwudaishi-051-926-congjing','378d632d','薛居正等'),
 ('xinwudaishi-015-926-congjing-death',P/'sources/library/xinwudaishi-015-926-congjing-death','572ee184','欧阳修'),
 ('jiuwudaishi-034-926-retreat',P/'sources/library/jiuwudaishi-034-926-retreat','572ee184','薛居正等'),
 ('jiuwudaishi-035-926-crossing-and-yao',P/'sources/library/jiuwudaishi-035-926-crossing-and-yao','572ee184','薛居正等'),
 ('jiuwudaishi-094-926-liqiong',P/'sources/library/jiuwudaishi-094-926-liqiong','572ee184','薛居正等'),
 ('xinwudaishi-014-926-zhangrongge',P/'sources/library/xinwudaishi-014-926-zhangrongge','572ee184','欧阳修'),
 ('xinwudaishi-008-926-shi-advance',P/'sources/library/xinwudaishi-008-926-shi-advance','572ee184','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0926-p041-p043',
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
lines = (ROOT / 'resources/derived/tongjian/274.txt').read_text().splitlines()
for n in range(41, 44):
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
        citation = f'卷274·同光四年（926）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_274_0926_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'继岌':'李继岌','帝':'李存勖','上':'李存勖','嗣源':'李嗣源','李绍荣':'元行钦','李继璟':'李从璟','镠':'钱镠','传瓘':'钱传瓘','温':'徐温','徐知诰':'李昪','知诰':'李昪','敬瑭':'石敬瑭','习':'符习','循':'孔循','李绍虔':'杜晏球','李绍英':'房知温','西方鄴':'西方邺','李琼':'李琼（隐光）'}
NEW_ALIASES={'西方邺':['西方鄴'],'李琼（隐光）':['李瓊（隱光）'],'姚彦温':['姚彥溫'],'潘环':['潘環','潘瑰'],'张唐':['張唐','张塘','張塘'],'张容哥':['張容哥']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=926 if name=='张容哥' else None,description=f'《资治通鉴》卷274同光四年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='926年本段；确日未载', note='', year=926, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_274_0926_' + code
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
        edge = 'participation_zztj_274_0926_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_274_0926_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('cunxu_departs_luoyang_to_sishui','李存勖从洛阳东行，至汜水后遣元行钦率骑兵沿河东进',41,'乙亥','循河而东。',[('帝','东征者'),('李绍荣','奉遣率骑者')],when='926年三月乙亥发洛阳、丁丑至汜水、戊寅遣骑，据主书',place='洛阳、汜水及沿河东行路',note='主所列三日分阶段保留，不合并为同日；旧本纪乙丑出京、戊辰遣骑不同，独立补证。')
claim('event',E,'time_original','旧本纪记乙丑出京、戊辰遣元行钦骑军东向，与主书纪日不同。',41,'乙丑，車駕發京師。戊辰，遣元行欽將騎軍沿河東向。','仅记录书际异文，未核纸本，不改主日。',source='jiuwudaishi-034-926-retreat',relation='conflicts')
E=ev('congjing_remains_with_cunxu','李嗣源亲党多离去，李从璟拒绝自行脱身及再使父，愿留皇帝身边',41,'李嗣源亲党','以明赤诚。',[('李从璟','拒离及辞再遣者'),('帝','屡欲遣其使父者')],when='926年三月李存勖东征途中',place='李存勖东征军',note='亲党多亡不等全部离去；左右无名不补人名；自愿死于帝前是陈志，不是已经死。')
claim('event',E,'description','旧宗室传记其随庄宗赴汴，亲旧多逃而本人无脱身之意。',41,'從莊宗赴汴州，明宗之親舊多策馬而去，左右或勸從璟令自脫，終無行意，','庄宗赴汴为行动方向，不误写实际进入已被占的汴州。',source='jiuwudaishi-051-926-congjing',relation='corroborates')
E=ev('congjing_killed_by_yuan','李存勖强遣李从璟赴黎阳召父，李从璟途中被元行钦杀害',41,'帝闻嗣源','绍荣杀之。',[('帝','强遣使父者'),('李从璟','被杀使者'),('李绍荣','杀害者')],when='926年三月东征途中，确日未载',place='使赴黎阳途中，具体遇害地点未载',note='此次才为实杀，与前批卫州囚而获释分开；不凭黎阳召父把遇害地点确定为黎阳。')
claim('person',people['李从璟'],'death_year','李从璟于926年被元行钦杀害。',41,span(41,'帝闻嗣源'),'年月沿主本段，未补确日。')
claim('event',E,'description','新家人传记庄宗欲遣从璟通问，行钦认为不可而杀之。',41,'莊宗聞明宗已渡黎陽，復欲遣從璟通問。行欽以為不可，遂殺之。','与主已强遣、道遇不同的执行叙法并存；不当作两个死亡事件。',source='xinwudaishi-015-926-congjing-death',relation='conflicts')
E=ev('qianliu_ill_chuanguan_regent','钱镠患病赴衣锦军，命钱传瓘监国',42,'吴越王镠','传瓘监国。',[('镠','患病、命监国者'),('传瓘','镇海镇东留后、受命监国者')],when='926年三月主书此段，确日未载',place='衣锦军',note='监国不等继位；吴越书传瓘即既有钱传瓘，未据此改为新人物钱元瓘。')
E=ev('qianliu_receives_xuwen_envoy','徐温遣使问疾，钱镠认为意在窥察，仍强起接见',42,'吴徐温','强出见之。',[('温','遣问疾使者'),('镠','疑其窥察并接见者')],when='926年三月钱镠患病期间',place='衣锦军',note='阴狡及觇我是钱镠判断，保留言说归属；使者、左右无名不建实体。')
E=ev('xuwen_cancels_attack_after_recovery','徐温聚兵拟袭吴越，闻钱镠病愈而停止，钱镠随后返钱塘',42,'温果','镠寻还钱塘。',[('温','集兵拟袭后停止者'),('镠','病愈返钱塘者')],when='926年三月钱镠病愈后叙次，确日未载',place='吴、吴越与钱塘',note='聚兵欲袭不等已经发动攻击；本段各行动次序保留，不外推问疾是已证实间谍行为。')
E=ev('wu_advances_xuzhigao_yankeqiu','吴进徐知诰之位，严可求兼门下侍郎、同平章事',43,'吴以','同平章事。',[('徐知诰','右仆射同平章事、进位者'),('严可求','兼门下侍郎同平章事者')],when='926年三月主书本段叙次，确日未载',place='吴',note='徐知诰复用李昪；主待中疑侍中，原文待保留，在未获同事校证前不强改为确定官名。')
E=ev('cunxu_leaves_sishui','李存勖从汜水继续东行',43,'庚辰','帝发汜水。',[('帝','继续东行者')],when='926年三月庚辰据主书',place='汜水',note='与第41段首次至汜水及末段返汜水分开。')
E=ev('siyuan_takes_supply_silk_baigao','李嗣源在白皋取得山东上供绢船，用绢赏军',43,'辛已','取以赏军。',[('嗣源','取绢赏军者')],when='926年三月，主书记“辛已”，已疑巳待核',place='白皋',note='辛已原字保留，不把日干支字形错误当另一个日期；上供绢非自有库存。')
claim('event',E,'description','旧明宗纪亦记白皋驻军遇山东上供绢数船，取以赏军。',43,'帝乃趨白皋渡，駐軍於河上，會山東上供綱載絹數船適至，乃取以賞軍，軍士以之增氣。','同渡口同供绢同赏军印证，不凭增气扩写人数。',source='jiuwudaishi-035-926-crossing-and-yao',relation='corroborates')
E=ev('baigao_boat_dispute_execution','白皋争舟时，行营马步使斩安重诲从者示众，书称军中肃然',43,'安重诲','许州人也。',[('安重诲','被斩者所属者')],when='926年三月白皋渡河前',place='白皋渡',note='主陶后私用缺字未解，虽旧史见许州留后陶玘，同地籍不足证明同职同事，暂不建该执行者实体；不可把被斩从者写成安重诲本人。军中肃然是书载效果。')
E=ev('siyuan_crosses_river_and_gathers_fu_an','李嗣源渡河至滑州，招符习会于胙城，安审通也率兵来会',43,'嗣源济河','亦引兵来会。',[('嗣源','渡河、召集者'),('习','应召会兵者'),('安审通','率兵来会者')],when='926年三月白皋赏军之后、入梁之前',place='滑州、胙城',note='主滑洲疑州，依上下文州名规范展示滑州并留原引文；会军不补未载兵数。')
claim('event',E,'description','旧明宗纪补船少时得沿流木筏用于渡师。',43,'及將濟，以渡船甚少，帝方憂之。忽有木伐數隻，沿流而至，即用以濟師，故無留滯焉。','木伐是底本原字；补渡师方式，不推神迹或人为事先安排。',source='jiuwudaishi-035-926-crossing-and-yao',relation='adds')
E=ev('kongxun_offers_bian_to_first_arrival','孔循分别迎李存勖、向李嗣源密输款，称先到者得汴州',43,'知汴州','先至者得之。”',[('循','分别遣使、陈条件者'),('帝','西迎表对象'),('嗣源','北送密款对象')],when='926年三月李嗣源渡河后叙次',place='汴州与两军之间',note='先至者得之为孔循之言，未在此阶段当作占城结果；后面取城另记。')
E=ev('xifangye_sent_guard_bian','李存勖此前派骑将西方邺守汴州',43,'先是','守汴州；',[('帝','此前派遣者'),('西方鄴','满城籍骑将、守汴者')],year=None,when='926年三月取汴之前的追叙，派遣确年未载',place='汴州',note='先是为追叙，不强定派遣发生926年。西方为复姓，鄴展示邺。')
E=ev('liqiong_shi_take_bian','石敬瑭派李琼突入封丘门，随后自己从西门入据汴州，西方邺请降',43,'石敬瑭使裨将','西方鄴请降。',[('敬瑭','派裨将、入城占据者'),('李琼','攻封丘门的裨将'),('西方鄴','请降守将')],when='926年三月李嗣源入大梁前',place='汴州封丘门、西门',note='李琼据旧卷94同人同封丘门同石敬瑭辨为字隐光者；既有楚将李琼已908年卒，另建限定名，不能因同名复用。')
claim('person',people['李琼（隐光）'],'description','此李琼字隐光，沧州饶安人，与既有楚将李琼分为两个主体。',43,'李瓊，字隱光，滄州饒安人也。','由同一传随后同石敬瑭取封丘门的行动确认；不取传中947年死亡提前录入。',source='jiuwudaishi-094-926-liqiong',relation='adds')
claim('event',E,'description','旧李琼传同记西方邺守汴、李琼先突封丘门、石敬瑭随入及邺归命。',43,'時莊宗遣騎將西方鄴守其城，高祖憂之，使瓊以勁兵突封丘門而入，高祖踵之，鄴尋歸命，浚郊遂定。','高祖此处指晋高祖石敬瑭，非李存勖；同门、同先后及同守将对应。',source='jiuwudaishi-094-926-liqiong',relation='corroborates')
E=ev('siyuan_enters_daliang','石敬瑭催促李嗣源，李嗣源进入大梁',43,'敬瑭使人','嗣源入大梁。',[('敬瑭','催促者'),('嗣源','入梁者')],when='926年三月壬午据主书；旧明宗纪记二十六日',place='大梁',note='同占城后入城，壬午与二十六日各书分引，不自行历算同日。')
claim('event',E,'time_original','旧明宗纪记二十六日至汴州。',43,'二十六日至汴州，','旧本原纪时独立保留，不混旧庄宗壬申至荥泽与主壬午入梁。',source='jiuwudaishi-035-926-crossing-and-yao',relation='adds')
claim('event',E,'description','新晋本纪亦记石敬瑭率三百渡黎阳为前锋，明宗随后入汴，庄宗后到不得入。',43,'明宗然之，與之驍騎三百，渡黎陽為前鋒，明宗遂入汴。莊宗自洛後至，不得入，而兵皆潰去。','三百为石前锋，不是姚彦温兵数；莊宗不得入与后至为书说，不提前记遇弑。',source='xinwudaishi-008-926-shi-advance',relation='corroborates')
E=ev('yaoyanwen_sent_vanguard_defects','李存勖到荥泽东，厚赐姚彦温所部充前军；姚率众投李嗣源，遭斥并被夺兵',43,'是日，帝至荥泽东','即夺其兵。',[('帝','厚赐派前驱者'),('姚彦温','龙骧指挥使、率部投李者'),('嗣源','斥其不忠、夺兵者')],when='926年三月李嗣源入梁同日，主壬午叙次；旧庄宗纪壬申',place='荥泽东至大梁',note='主三千骑与旧两纪八百骑分别保留；姚事势已离是其陈述，不作独立全军状况统计。')
claim('event',E,'description','旧庄宗纪记壬申荥泽派姚彦温董八百骑，到中牟后奔汴州。',43,'壬申，帝至滎澤，以龍驤馬軍八百騎為前軍，遣姚彥溫董之。彥溫行至中牟，率所部奔於汴州。','主同日叙次、三千与旧壬申、八百有别，附中牟路径补证，不折算统一。',source='jiuwudaishi-034-926-retreat',relation='conflicts')
claim('event',E,'description','旧明宗纪亦记姚彦温率八百骑归李嗣源，受不忠之斥并被夺兵。',43,'是日，彥溫率部下八百騎歸於帝，具言：「主上為行欽所惑，事勢已離，難與共事。」帝曰：「卿自不忠，言何悖也！」乃奪其兵，','旧此帝为李嗣源，主为庄宗时区分；两旧纪为同书不可算两部独立确证。',source='jiuwudaishi-035-926-crossing-and-yao',relation='conflicts')
E=ev('panhuan_deserts_wangcun','守王村寨且有刍粟的潘环在皇帝遣骑查看时也奔大梁',43,'指挥使潘环','环亦奔大梁。',[('潘环','王村寨守将、奔梁者'),('帝','遣骑察寨者')],when='926年三月姚彦温投李后叙次',place='王村寨至大梁',note='旧潘瑰与主潘环据同王村寨同刍粟同奔汴辨同事同人，保留异名；主数万刍粟没有计量单位，不造石或斛。')
claim('event',E,'description','旧庄宗纪记名潘瑰、王村寨积粟数万，同样奔汴。',43,'時潘瑰守王村寨，有積粟數萬，亦奔汴州。','环、瑰字形非繁简转换，凭同职同寨同动作校同人，纸本字形待核。',source='jiuwudaishi-034-926-retreat',relation='conflicts')
E=ev('cunxu_turns_back_from_wansheng','李存勖到万胜镇闻李嗣源已据梁、诸军离叛，旋师夜返汜水',43,'帝至万胜镇','是夜复至汜水。',[('帝','下令旋师者')],when='926年三月，主壬午叙次及其当夜',place='万胜镇、汜水',note='吾不济矣为帝叹，不把绝对失败预言当后来结局已经发生；位置按主书保留。')
claim('event',E,'description','旧庄宗纪同记万胜镇旋师，夜次汜水，并补路旁荒冢置酒及愁台之名。',43,'帝聞諸軍離散，精神沮喪，至萬勝鎮即命旋師。登路旁荒塚，置酒視諸將流涕。俄有野人進雉，因問塚名，對曰：「里人相傳為愁台。」帝彌不悅，罷酒而去。是夜，次汜水。','愁台为里人相传地名，不写神兆或名不祥必致亡国；与甲申石桥誓死酒另事。',source='jiuwudaishi-034-926-retreat',relation='adds')
E=ev('cunxu_loses_escort_leaves_zhangtang','东征扈从二万五千返汜水已失万余，李存勖留张唐率三千守关',43,'帝之出关也','以步骑三千守关。',[('帝','留守部署者'),('张唐','秦州都指挥使、守关者')],when='926年三月返汜水时',place='汜水关',note='失万余是离散失众，不等阵亡万余；旧张塘据同秦州职同三千守关合同人，原字存。')
claim('event',E,'description','旧庄宗纪记二万五千出关、返后失万余骑，守关将名张塘。',43,'初，帝東出關，從駕兵二萬五千，及復至汜水，已失萬餘騎。乃留秦州都指揮使張塘以步騎三千守關。','主万余人、旧万余骑不同；张唐/张塘不是繁简形式，按同职同命同数量辨同人，待纸本。',source='jiuwudaishi-034-926-retreat',relation='conflicts')
E=ev('cunxu_promises_shu_gold_guards_reject','李存勖过罂子谷称魏王金银五十万到京将尽赐卫士，卫士回答已晚，帝泣',43,'癸未','帝流涕而已。',[('帝','声称将赐财并流涕者'),('继岌','所称报送金银的魏王')],when='926年三月癸未据主书',place='罂子谷',note='适报五十万为帝之说，尚未到京不当实际给付；金银没有计量单位不造钱数。卫士无名不建实体。')
claim('event',E,'description','新家人传亦记罂子谷承诺给蜀金银五十万，随从称太晚，帝泣。',43,'至罌子谷，道路隘狹，莊宗見從官執兵仗者，皆以好言勞之曰：「適報魏王平蜀，得蜀金銀五十萬，當悉給爾等。」對曰：「陛下與之太晚，得者亦不感恩。」莊宗泣下，','同地同数字同对答补证，得蜀金银与主又进说法有别；金银不是原确定五十万两。',source='xinwudaishi-014-926-zhangrongge',relation='corroborates')
E=ev('zhangrongge_pursued_over_treasury','李存勖索袍带赐从官，张容哥称已颁尽，卫士追杀张而他人救免',43,'又索袍带','或救之，获免。',[('帝','索赏赐者'),('张容哥','内库使、被追杀获救者')],when='926年三月癸未罂子谷叙次',place='罂子谷',note='称已尽是内库使回答，非独立库存核查；追杀时获免，与随后自尽分开。')
E=ev('zhangrongge_drowns_himself','张容哥向同类抱怨皇后吝财而宦者受罪，随后投河自尽',43,'容哥谓同类','因赴河死。',[('张容哥','陈述后投河者')],when='926年三月癸未罂子谷叙次',place='罂子谷途中河边，具体河段未载',note='吝财和归罪是张容哥之言，不推为全部军变唯一原因；因赴河死为实际死亡。')
claim('person',people['张容哥'],'death_year','张容哥于926年投河死亡。',43,span(43,'容哥谓同类','因赴河死。'),'沿本段年，不补确切河段。')
claim('event',E,'description','新家人传也记张容哥称皇后惜物、归罪于己，继而投水而死。',43,'容哥曰：「皇后惜物，不以給軍，而歸罪於我。事若不測，吾身萬段矣！」乃投水而死。','新称归罪于我、主于吾辈，分存原话；不把推测的不测之祸当已发生。',source='xinwudaishi-014-926-zhangrongge',relation='corroborates')
E=ev('cunxu_generals_cut_hair_at_shiqiao','李存勖在石桥西置酒悲问，元行钦等百余将截发誓死，众人号泣',43,'甲申','因相与号泣。',[('帝','置酒悲问者'),('李绍荣','参与诸将代表')],when='926年三月甲申据主书',place='石桥西',note='截发誓报为表达忠诚，不等之后均死战；百余为书载将数，不造所有姓名。')
E=ev('cunxu_reenters_luoyang','李存勖当晚返回洛阳城',43,'是日晚','入洛城。',[('帝','返洛者')],when='926年三月甲申晚据主书',place='洛阳',note='返京与石桥置酒分动作，不提前进入四月兵变。')
E=ev('shi_collects_stragglers_fu_fang_join','李嗣源派石敬瑭赴汜水收抚散兵，随后前行，杜晏球及房知温率军来会',43,'李嗣源命','李绍英引兵来会。',[('嗣源','遣前军并继进者'),('敬瑭','受命收抚散兵者'),('李绍虔','率兵来会者'),('李绍英','率兵来会者')],when='926年三月李存勖返洛之后叙次',place='大梁至汜水行军路',note='李绍虔复用杜晏球、李绍英复用房知温；赴汜水为受命方向，不直接把本句断为已到。')
claim('event',E,'description','旧明宗纪同记房知温、杜晏球自北面相继而至。',43,'既而房知溫、杜晏球自北面相繼而至。','主异名与旧原名同职同来会，复用既有主体。',source='jiuwudaishi-035-926-crossing-and-yao',relation='corroborates')
claim('event',E,'description','新晋本纪记庄宗西还后，明宗使石敬瑭前锋赴汜水收散卒。',43,'莊宗西還，明宗以敬瑭為前鋒趣汜水，且收其散卒。','只取遇弑之前句；后文庄宗遇弑待下一卷连续处理。',source='xinwudaishi-008-926-shi-advance',relation='corroborates')
E=ev('cunxu_plans_hold_sishui_reviews_cavalry','宰相枢密使请控汜水待魏王西军，李存勖接受、阅骑并命次晨东行',43,'丙戌',None,[('帝','采纳、阅骑及预令东行者'),('继岌','拟待西军的魏王')],when='926年三月丙戌据主书；诘旦东行为预令',place='洛阳上东门及所拟汜水控扼方向',note='主共奉疑共奏留原字；魏军将至为上奏预期，命诘旦出发不等已经执行，下卷即四月兵变另读。')

review='连续41—43段逐句核录，第43段跨两原文导出块分别引，不拼接。李从璟实际遇害与前获释分事，新传未遣即杀和主途中杀叙法各存。钱镠疾、监国、问疾、拟袭止兵及返塘不混继位或实战。徐知诰复用李昪，待中疑侍中留原文；辛已疑巳、滑洲疑州、共奉疑奏独立待校，不靠繁简转换掩饰。陶私用缺字未获同职同事原证，暂不建主体、不并陶玘；被斩安重诲从者不等斩安本人。西方为复姓，邺展示简体。李琼同封丘门行动由旧94明确字隐光，与908卒楚将分人。潘环/瑰和张唐/塘据同职同地同动作辨同人；姚三千/旧八百、诸纪出京遣骑到荥泽日、万余人/骑各存。魏金银五十万仅帝所称与承诺未当已赐，财尽是答话；张容哥追杀获救与投河死分阶段，吝财归罪为其言。石收散卒、两将会军、丙戌阅骑与次晨计划分实行动及预令；不提前记庄宗死、李嗣源登位。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,44):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(41,44)],next_paragraph='zztj-v275-y0926-p001',next_volume=275,supplements=supplements,excluded_non_body=[],coverage='卷274第41—43段，原文件78—80行；东征、李从璟遇害、吴越疾与监国、白皋渡河取绢、会军占梁、诸军离散及庄宗返洛。卷274连续43段处理，926年110段尚有卷275全部67段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(41,44)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
