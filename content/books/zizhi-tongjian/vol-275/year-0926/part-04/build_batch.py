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
 ('tongjian-275-926-bian-mutiny',P/'sources/library/tongjian-275-926-bian-mutiny','e466a47f','司马光等'),
 ('jiuwudaishi-036-926-enduan-restore',P/'sources/library/jiuwudaishi-036-926-enduan-restore','e466a47f','薛居正等'),
 ('jiuwudaishi-036-926-an-declines',P/'sources/library/jiuwudaishi-036-926-an-declines','e466a47f','薛居正等'),
 ('jiuwudaishi-036-926-bian-and-taboo',P/'sources/library/jiuwudaishi-036-926-bian-and-taboo','e466a47f','薛居正等'),
 ('jiuwudaishi-036-926-executions-and-jingnan',P/'sources/library/jiuwudaishi-036-926-executions-and-jingnan','e466a47f','薛居正等'),
 ('xinwudaishi-025-926-fuyanrao',P/'sources/library/xinwudaishi-025-926-fuyanrao','e466a47f','欧阳修'),
 ('xinwudaishi-040-926-chai-executed',P/'sources/library/xinwudaishi-040-926-chai-executed','e466a47f','欧阳修'),
 ('xinwudaishi-024-926-mayan',P/'sources/library/xinwudaishi-024-926-mayan','e466a47f','欧阳修'),
 ('tongjian-275-926-accession',YEAR/'part-03/sources/library/tongjian-275-926-accession','5c38857d','司马光等'),
 ('jiuwudaishi-036-926-may-army',YEAR/'part-03/sources/library/jiuwudaishi-036-926-may-army','5c38857d','薛居正等'),
 ('xinwudaishi-006-926-may-offices',YEAR/'part-03/sources/library/xinwudaishi-006-926-may-offices','5c38857d','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-926-bian-mutiny','tongjian-275-926-accession']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p025-p036',
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
for n in range(25, 37):
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
    ck = f'claim_zztj_275_0926_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','明宗':'李嗣源','李彦饶':'符彦饶','彦饶':'符彦饶','彦超':'符彦超','李继严':'李继曮','从曮':'李继曮','高季兴':'高季昌','重诲':'安重诲'}
NEW_ALIASES={'高逖':[],'符彦饶':['符彥饒','李彦饶','李彥饒'],'张审琼':['張審瓊'],'韦俨':['韋儼'],'于可洪':['於可洪'],'马延':['馬延']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷275同光四年条所见人物：{name}，{role}。',biography=None,status='draft')
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
E=ev('wangyanhan_chancellor_honor','王延翰加同平章事',25,'甲戌',None,[('王延翰','加同平章事者'),('帝','加衔者')],when='926年五月甲戌',place='福州及后唐朝廷',note='加衔不等王延翰入洛常驻中央执政。')
claim('event',E,'description','旧史记福州节度使王延翰加检校太尉、同平章事。',25,'甲戌，福州節度使、檢校太傅王延翰加檢校太尉、同平章事。','原职及兼衔据旧补，日一致。',source='jiuwudaishi-036-926-may-army',relation='adds')
E=ev('an_requests_literary_advisers','史书记李嗣源令安重诲读奏章，安自陈古事非所及，请选文学之臣备应对',26,'帝目不知书','以备应对。”',[('帝','令读奏章者'),('重诲','读章及请文学臣者')],when='926年五月设置端明殿学士前，确日未载',place='后唐朝廷',note='目不知书为底本表述，展示解释为书所述识读问题；安自陈不尽通不能等同终生所有文书不懂。仿前朝是建议，不另外建立已设侍讲等机构事实。')
E=ev('enduan_academicians_created','朝廷设置端明殿学士，任冯道、赵凤为之',26,'乃置端明',None,[('帝','设职及任命者'),('冯道','翰林学士、任端明殿学士'),('赵凤','翰林学士、任端明殿学士')],when='926年五月乙亥',place='后唐朝廷端明殿',note='此为新职设置，前后任职不混成冯赵首次仕官。')
claim('event',E,'description','旧史记冯道、赵凤俱以本官充端明殿学士，此职自此始。',26,'乙亥，翰林學士、戶部侍郎、知制誥馮道，翰林學士、中書舍人趙鳳，俱以本官充端明殿學士。端明之職，自此始也。','补本官兼衔；不以夹注五代会要孔循献议替换主安重诲奏请或作新增独立来源。',source='jiuwudaishi-036-926-enduan-restore',relation='adds')
E=ev('guochongtao_burial_authorized','朝廷准郭崇韬归葬',27,'丙子','归葬，',[('郭崇韬','准归葬的已故人'),('帝','归葬准许者')],when='926年五月丙子',place='后唐朝廷及归葬之处，主未具墓地',note='听归葬是准许，不据此证明迁葬已实施；死年沿前批不改。')
E=ev('zhuyouqian_rank_restored','朝廷恢复朱友谦官爵',27,'复硃友谦','宫爵；',[('朱友谦','官爵获恢复的已故人'),('帝','恢复官爵发令者')],when='926年五月丙子',place='后唐朝廷',note='主宫爵疑官爵，原文不改，官名据旧补；朱/硃同人复用，不为死者写成复活任职。')
claim('event',E,'description','旧史列朱友谦恢复护国军节度使、太师、尚书令、河中尹、西平王。',27,'故萬州司戶朱友謙可復護國軍節度使、守太師、兼尚書令、河中尹、西平王，','原列兼衔据旧，不声称本人返镇履职。',source='jiuwudaishi-036-926-enduan-restore',relation='adds')
E=ev('guo_zhu_property_return_order','朝廷命返还郭崇韬、朱友谦两家此前籍没的货财田宅',27,'两家货财',None,[('郭崇韬','家财田宅返还对象'),('朱友谦','家财田宅返还对象'),('帝','返还发令者')],when='926年五月丙子',place='两家财产所在地，具体未载',note='归之按诏令返还处理，未推各宅田已完成移交或受领子女姓名。')
claim('event',E,'description','旧史记郭崇韬世业田宅还与骨肉。',27,'郭崇韜宜許歸葬，其世業田宅並還與骨肉。','受领者只是骨肉未名，不补幸存亲人名单。',source='jiuwudaishi-036-926-enduan-restore',relation='corroborates')
E=ev('an_south_east_command_declined','安重诲获兼领山南东道节度使，以襄阳要地应有帅为由固辞，朝廷准辞',28,'戊寅',None,[('帝','任命及准辞者'),('重诲','受任后固辞者')],when='926年五月戊寅',place='山南东道、襄阳及朝廷',note='任命后获辞，不写成实际赴镇长期担任；理由为辞职所称。')
claim('event',E,'description','旧史记安重诲兼领襄州，辞退理由先由其党提出。',28,'戊寅，以樞密使安重誨兼領襄州節度使。製下，重誨之黨謂重誨曰：「襄州地控要津，不可乏帥，無宜兼領。」重誨即自陳退，許之。','主直接载重诲理由，旧补其党建议，未具党人姓名不造人；山南东道与襄州职称分存。',source='jiuwudaishi-036-926-an-declines',relation='adds')
E=ev('bian_troops_ordered_waqiao','朝廷诏发张谏等汴州控鹤兵三千戍瓦桥',29,'诏发汴州','戍瓦桥。',[('帝','戍守调发令者'),('张谏','控鹤指挥使、被调者')],when='926年五月末至六月丁酉出城前，诏日未载',place='汴州至瓦桥',note='诏戍不等已经到瓦桥，丁酉只出汴城而回。')
E=ev('zhangjian_bian_military_mutiny','张谏等出城后返回汴州反叛，焚掠坊市并杀权知州推官高逖',29,'六月，丁酉','杀权知州、推官高逖。',[('张谏','叛军指挥使'),('高逖','被杀权知州、推官')],when='926年六月丁酉',place='汴州坊市',note='高逖为权知州且推官，不将顿号生成两个死者；张谏此前调发与本次叛分阶段。')
claim('person',people['高逖'],'death_year','高逖于926年汴州兵变中被杀。',29,span(29,'六月，丁酉','杀权知州、推官高逖。'),'实际被杀不仅发令；原未载亲手行刑者。')
claim('event',E,'description','新明宗纪同记六月丁酉控鹤军乱，张谏杀权知州高逖。',29,'六月丁酉，汴州控鶴軍亂，指揮使張諫殺其權知州事高逖。','同事同日补证，不外推其党所有军士均亲杀。',source='xinwudaishi-006-926-may-offices',relation='corroborates')
E=ev('yanrao_forced_leader_orders_stop_pillage','汴州叛军逼符彦饶为帅，符以止焚掠、听其命为条件，众从之',29,'逼马步都指挥使','众从之。',[('李彦饶','被逼为帅、要求停止焚掠者')],when='926年六月丁酉兵变后叙次',place='汴州',note='李彦饶据新符传同汴州职同张谏事校符彦饶；被逼不直接建叛军盟友或永久反叛标签。')
claim('person',people['符彦饶'],'description','新符存审传分述次子彦饶，记其为汴州马步军都指挥使。',29,'次子彥饒，為汴州馬步軍都指揮使。','结合该段张谏高逖韦俨同事校主李彦饶为符彦饶；主曹州刺史与新其后历曹州时序差不提前统一。',source='xinwudaishi-025-926-fuyanrao',relation='adds')
E=ev('yanrao_ambush_executes_zhangjian','符彦饶伏甲于室，在诸将入贺时执张谏等四人斩之',29,'己亥旦','斩之。',[('李彦饶','设伏执行者'),('张谏','被执斩者')],when='926年六月己亥旦',place='汴州府室',note='前日唱乱数人是符话语，不推只有四人参加兵变；四人是本阶段被执者，不与随后四百合并。')
claim('person',people['张谏'],'death_year','张谏于926年六月己亥被符彦饶设伏处决。',29,span(29,'己亥旦','斩之。'),'主具体处置日；旧概记谋叛伏诛并列，不据其段庚子移改。')
claim('event',E,'description','新符传补符彦饶与拱衙指挥使庞起共同伏甲于衙内。',29,'乃陰與拱衙指揮使龐起伏甲于衙內。','庞起仅作为补充原文中的同谋者，主无名不把全部主参与关系写成有庞。新明日与主丁酉至己亥间隔各存，未自行协调日期。',source='xinwudaishi-025-926-fuyanrao',relation='adds')
claim('event',E,'description','旧明宗纪概记张谏等谋叛伏诛。',29,'汴州屯駐控鶴指揮使張諫等謀叛伏誅，','旧概记置庚子条附近，不凭概记替换主己亥。',source='jiuwudaishi-036-926-bian-and-taboo',relation='corroborates')
E=ev('yanrao_crushes_zhangshenqiong_followers','张审琼率党众喧哗建国门，符彦饶出兵尽诛其众四百，军州始定',29,'其党张审琼','军、州始定。',[('张审琼','率党众者'),('李彦饶','勒兵平乱者')],when='926年六月己亥张谏被斩之后',place='汴州建国门',note='主四百/新四百余各引，不与三千调兵或三千家混成一个死亡总数；其众被诛不单凭此断张审琼个人明确死亡。')
claim('event',E,'description','新符传记设伏平乱后杀四百余人。',29,'明日，諫等皆集，伏兵發，誅諫等，殺四百餘人，','新合叙设伏和平乱且记余，主拆张谏四人及张审琼四百，叙法与计数各存。',source='xinwudaishi-025-926-fuyanrao',relation='adds')
E=ev('yanrao_hands_bian_to_weiyan','符彦饶即日牒军州事给节度推官韦俨权知，并上报朝廷',29,'即日','具以状闻。',[('李彦饶','移交并上报者'),('韦俨','节度推官、权知军州受领者')],when='926年六月己亥平乱当日',place='汴州',note='军州始定仅本事阶段，不推从此永久无乱。权知与正式节度使分开。')
claim('event',E,'description','新符传也记即日牒州事与推官韦俨。',29,'即日牒州事與推官韋儼。','韋儼/韦俨繁简同名，职事相同补证。',source='xinwudaishi-025-926-fuyanrao',relation='corroborates')
E=ev('kongxun_bian_prefect','朝廷诏枢密使孔循知汴州',29,'庚子','知汴州，',[('帝','任命者'),('孔循','受命知汴州者')],when='926年六月庚子',place='汴州',note='沿已有枢密使主体，知汴州不另建人与后期节度使混名。')
claim('event',E,'description','旧史记孔循权知汴州军州事。',29,'以樞密使孔循權知汴州軍州事。','补权知职称，非任枢密使的新一次事件。',source='jiuwudaishi-036-926-bian-and-taboo',relation='adds')
E=ev('kongxun_executes_mutineers_families','孔循收捕为乱者三千家，悉诛之',29,'收为乱者','悉诛之。',[('孔循','知汴州后的收捕诛族者')],when='926年六月庚子任知汴州后叙次；执行日主未另载',place='汴州',note='三千家是家数，不写为全部三千人或自行推亲属人口。旧奏三千人并族诛的数字单位另引，不静默统一。')
claim('event',E,'description','旧史记孔循奏召集赵虔以下三千人，并族诛讫。',29,'汴州知州孔循奏，召集謀亂指揮使趙虔已下三千人並族誅訖。','主三千家、旧三千人并族诛，计数单位不同；旧奏在壬子条后叙，不能认庚子即全部完成。赵虔仅旧载首领不合张谏。',source='jiuwudaishi-036-926-executions-and-jingnan',relation='adds')
relationship('彦饶','彦超','弟弟',29,'彦饶，彦超之弟也。','符彦饶是符彦超的弟弟，主明示长幼，方向弟至兄；未另建反向哥哥重复边。')
E=ev('former_shu_officials_arrive','前蜀百官到达洛阳',30,'蜀百官','至洛阳，',[],when='926年六月汴州兵变后叙次，确日未载',place='洛阳',note='百官是群体概称，本段未列完整名单，不生成一百个无名人物。')
E=ev('maquan_refuses_food_dies','主书记前蜀永平节度使兼侍中马全因亡国之叹不食而卒',30,'永平节度使','不食而卒。',[],when='926年前蜀官员至洛阳后；本段六月叙次，确日未载',place='洛阳',note='本段马全身份及字形尚缺两史同事补证，不并后晋马全节或楚马賨，也不猜合王宗俦。原姓名保留事件及摘录，暂不创建人物主体，登记待考；动机仅本书所引自述。')
E=ev('shu_officials_assigned_posts','朝廷任王锴等前蜀官员为诸州府刺史、少尹、判官、司马，另有人归蜀',30,'以平章事王锴',None,[('王锴','前蜀平章事、分授官群体中的具名人'),('帝','授职者')],when='926年六月蜀百官至洛阳后叙次',place='后唐诸州府、蜀',note='原未分别列王锴获哪一职及哪一州，不任选刺史，也不指定王锴就是归蜀者。')
E=ev('yukehong_huazhou_mutiny','滑州都指挥使于可洪等纵火反叛，攻击并逐出魏博戍兵三指挥',31,'辛丑',None,[('于可洪','滑州都指挥使、叛乱者')],when='926年六月辛丑',place='滑州',note='三个指挥是军队编制数，不推兵员人数；后段校验奏诉与七月处死留下一批，不提前写死年。')
E=ev('siyuan_relaxes_name_taboo','李嗣源敕自己的二名只要不连称就无需避讳',32,'乙巳',None,[('帝','名讳敕令者')],when='926年六月乙巳据主书；旧条日字作己巳',place='后唐文书与臣下名讳',note='二名是姓名中嗣源二字，不等存在两个不同姓名；不是准许连称不避。')
claim('event',E,'description','旧史敕文规定文书二字不连称不得回避，臣下可自行改与君亲同字之名。',32,'應文書內所有二字，但不連稱，不得回避。如是臣下之名，不欲與君親同字者，任自改更。','旧全文补适用范围；其前己巳与主乙巳字形异样并记，不暗改主日期。',source='jiuwudaishi-036-926-bian-and-taboo',relation='adds')
E=ev('mengzhixiang_shizhong_honor','西川节度使孟知祥加兼侍中',33,'戊申',None,[('孟知祥','加兼侍中者'),('帝','加衔者')],when='926年六月戊申',place='西川与后唐朝廷',note='只是加衔，孟先前已任西川节度使，不当首次赴成都。')
claim('event',E,'description','旧史载孟知祥为剑南西川节度副大使知节度使事，加检校太傅兼侍中。',33,'劍南西川節度副大使、知節度使事孟知祥加檢校太傅、兼侍中，','补兼衔及完整旧职，不另生成两次任命。',source='jiuwudaishi-036-926-executions-and-jingnan',relation='adds')
E=ev('lijiyan_returns_fengxiang','李继曮到华州，闻洛阳之乱后返回凤翔',34,'李继严至','复归凤翔；',[('李继严','到华州、闻乱返镇者')],when='926年洛阳内难后追叙；本段置六月，行动确日未载',place='华州至凤翔',note='继严为底本拆字，沿既有李继曮主体；新从曮同凤翔柴重厚事补证。段序不证明出华州发生在六月戊申后。')
claim('event',E,'description','新传记柴重厚拒纳后李从曮东到华州，闻庄宗之难西归。',34,'監軍使柴重厚拒而不納，從曮遂東至華州，聞莊宗之難乃西歸。','新从曮即既有李继曮异名；只补转向背景，不重新录上批已写拒纳。',source='xinwudaishi-040-926-chai-executed',relation='adds')
E=ev('siyuan_executes_chai','李嗣源为李继曮事诛杀柴重厚',34,'帝为之',None,[('帝','遣诛决定者'),('柴重厚','被诛者'),('李继严','处置缘由所涉者')],when='926年明宗入立后；主六月段叙，确日未载',place='凤翔及后唐朝廷，执行地点未明',note='原未列亲手执行人；诛宦总令与此具名案件分录。')
claim('person',people['柴重厚'],'death_year','柴重厚于926年被明宗遣人诛杀。',34,'帝为之诛柴重厚。','此前拒纳与此实诛分阶段。')
claim('event',E,'description','新传明确明宗入立，闻柴重厚曾拒李从曮，遣人诛之。',34,'明宗入立，聞重厚嘗拒從曮，遣人誅之。','明宗是决定者，未造执行人姓名或斩首方式。',source='xinwudaishi-040-926-chai-executed',relation='corroborates')
claim('event',E,'description','新传另记李从曮上书为柴重厚求宽免，朝廷不许。',34,'從曮上書，言重厚守鳳翔，軍民無所擾，願貸其過。雖不許，士人以此多之。','求贷与军民无扰是李的陈述，不造李本人要求杀柴；士人赞许为史评。',source='xinwudaishi-040-926-chai-executed',relation='adds')
E=ev('gaojixing_requests_three_prefectures','高季昌请求夔、忠、万三州为属郡，朝廷诏准',35,'高季兴',None,[('高季兴','荆南请属郡者'),('帝','准许者')],when='926年六月孟知祥加衔后主书叙次，确日未载',place='荆南与夔州、忠州、万州',note='表求与诏准不等三州全部已交接、降伏或荆南军已经占领；后续争执留待逐段。')
claim('event',E,'description','旧史载高季兴称三州原属本道后被西川侵据，诏准，并令夔州恢复除刺史。',35,'荊南節度使高季興上言「夔、忠、萬三州，舊是當道屬郡，先被西川侵據，今乞卻割隸本管。」詔可之。其夔州，偽蜀先曾建節，宜依舊除刺史。','旧属郡及被侵为高奏自述，不将其产权主张当无争议事实；不引用后夹注十国纪年作本批新来源。',source='jiuwudaishi-036-926-executions-and-jingnan',relation='adds')
E=ev('an_executes_mayan_before_retinue','殿直马延误冲安重诲前导，被安斩于马前',36,'安重诲恃恩','斩之于马前，',[('重诲','斩人者'),('马延','误冲前导被斩的殿直')],when='926年本段置六月末至七月间；主未载斩日，新明宗纪记七月庚申',place='主只马前；新记御史台门',note='恃恩骄横为作者评价，不独立建性格事实；误冲不等谋反。原主语安承前，非李嗣源亲手斩。')
claim('person',people['马延'],'death_year','殿直马延于926年被安重诲杀害。',36,span(36,'安重诲恃恩','斩之于马前，'),'仅此具名殿直，不混名相近马殷。')
claim('event',E,'description','新安传载安重诲过御史台门，马延误冲前导，安怒斩后奏。',36,'重誨嘗出，過御史臺門，殿直馬延悞衝其前導，重誨怒，即臺門斬延而後奏。','补地点与先杀后奏顺序，悞/误字形保留；不把同快照桑弘迁安虔另案提前扩入主线。',source='xinwudaishi-024-926-mayan',relation='adds')
claim('event',E,'time_original','新明宗纪记七月庚申安重诲杀马延于御史台门。',36,'秋七月庚申，安重誨殺殿直馬延于御史臺門。','主先杀后秋七月奏敕的叙法与新纪杀日不同，日期独立保留，不强定主未具日。',source='xinwudaishi-006-926-may-offices',relation='adds')
E=ev('liqi_reports_mayan_execution','御史大夫李琪向朝廷报告马延被杀之事',36,'御史大夫李琪','以闻。',[('李琪','御史大夫、奏报者')],when='926年马延被杀后，奏报确日未载',place='后唐朝廷',note='以闻只报事，不擅称明宗已经治安重诲罪。')
E=ev('an_requests_edict_after_mayan_death','安重诲奏请皇帝下诏，称马延陵突重臣，戒谕中外',36,'秋，七月',None,[('重诲','奏敕者'),('帝','下诏者'),('马延','诏中被指陵突者')],when='926年秋七月，确日未载',place='后唐朝廷及中外',note='陵突重臣为诏指控，未将马延误冲定成实际蓄意犯上。原未载明宗亲自到场斩人。')
claim('event',E,'description','新安传称安为斩马延请敕处分，明宗不得已从之。',36,'重誨以斬延，乃請降敕處分，明宗不得已從之，','不得已是新史因果判断，单引不变成独立心理确证；后无敢言为史概述不生成所有谏官皆沉默事实。',source='xinwudaishi-024-926-mayan',relation='adds')

review='连续25—36段逐句回查。王延翰同平章为加衔不推常驻执政。端明设职、冯赵以本官充任按主安奏及旧正文，夹注五代会要不新增独立来源。郭归葬与朱恢复官爵、两家财产返还为准许及命令，不推迁葬交割全实施；宫爵疑官爵与硃字存原。安兼山南东道固辞不写已赴镇，旧其党建议与主本人理由各存。汴州调三千戍瓦桥、丁酉返城焚掠杀高逖、逼彦饶、己亥伏甲斩张谏四人、建国门诛众四百、韦权知、庚子孔知州与后收三千家诛分阶段。主李彦饶以新符同汴州职高逖张谏韦俨事校符彦饶，主曹州刺史/新后迁时序留异；弟至符彦超方向，不反向重复。新明日伏甲与主己亥、新四百余与主四百、旧三千人并族诛与主三千家各引，禁加成总死亡数字。张审琼所众死不推本人明死；庞起赵虔仅补证具名不强塞主参与或合张谏。前蜀马全暂缺同事异名补证，事件保留不建或并马全节马賨王宗俦主体；王锴原无各别新职不任选刺史。于可洪滑州本段反叛，未提前下一段实诛。嗣源二名指嗣源二字不连称无需避，主乙巳/旧己巳各存。孟加衔不当首次任西川。李继私字沿既有曮与新从曮同华州凤翔柴事校，听乱西归追叙不强六月戊申后，柴实诛责任帝遣人与新李请贷不许并存。高三州诏准未推已占或接管，其旧属是自称。马延误冲安杀、李琪奏、安奏诏分动作，主未杀日/新七月庚申保留，陵突为诏指控。展示简体，原文快照不改字，纸本未核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(25,37)],next_paragraph=Q[37]['id'],next_volume=275,supplements=supplements,excluded_non_body=[],coverage='卷275第25—36段，原文件30—41行；端明学士设置、郭朱复典、安辞方镇、汴州兵变平乱及诛族、蜀官到洛、滑州兵乱、名讳敕、孟加衔、柴实诛、荆南三州、马延案。926年110正文段累计79，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(25,37)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
