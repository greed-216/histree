# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 26–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 53))
specs=[
 ('tongjian-276-late-summer',YEAR/'part-05/sources/library/tongjian-276-late-summer','86b40c48','司马光等'),
 ('jiuwudaishi-039-august',P/'sources/library/jiuwudaishi-039-august','f88fd498','薛居正等'),
 ('jiuwudaishi-039-intercalary',P/'sources/library/jiuwudaishi-039-intercalary','f88fd498','薛居正等'),
 ('jiuwudaishi-054-lijitao',P/'sources/library/jiuwudaishi-054-lijitao','f88fd498','薛居正等'),
 ('jiuwudaishi-064-wangyanqiu-dingzhou',YEAR/'part-04/sources/library/jiuwudaishi-064-wangyanqiu-dingzhou','db4b82d4','薛居正等'),
 ('xinwudaishi-046-wangyanqiu-dingzhou',YEAR/'part-04/sources/library/xinwudaishi-046-wangyanqiu-dingzhou','db4b82d4','欧阳修'),
 ('xinwudaishi-072-hemiao',YEAR/'part-05/sources/library/xinwudaishi-072-hemiao','86b40c48','欧阳修'),
 ('xinwudaishi-006-928',YEAR/'part-01/sources/library/xinwudaishi-006-928','c991ab36','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-late-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p026-p032',
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
for n in range(26, 33):
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
        citation = f'卷276·天成三年（928）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0928_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','庄宗':'李存勖','晏球':'杜晏球','王晏球':'杜晏球','都':'王都','德钧':'赵德钧','惕隐':'赫邈','镠':'钱镠','传瓘':'钱传瓘','传璟':'钱传璟'}
NEW_ALIASES={'武从谏':['武從諫'],'李继陶':['李繼陶','得得'],'段佪':[],'钱传璟':['錢傳璟']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成三年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='928年'+('八月' if n<=30 else '闰八月')+'本段；确日未载'
    key = 'event_zztj_276_0928_' + code
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
        edge = 'participation_zztj_276_0928_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0928_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
aug='jiuwudaishi-039-august';inter='jiuwudaishi-039-intercalary';jitao='jiuwudaishi-054-lijitao';old='jiuwudaishi-064-wangyanqiu-dingzhou';new='xinwudaishi-046-wangyanqiu-dingzhou';he='xinwudaishi-072-hemiao';ann='xinwudaishi-006-928'
E=ev('khitan_retreat_muddy_starvation_youzhou','契丹败军北走，泥泞饥疲，入幽州境',26,'契丹北走','入幽州境。',[],when='928年七月易州战后、八月截击前，确日未载',place='北撤道路至幽州境',note='描述人马饥疲不推其所有成员饿死；北撤是前批唐河易州军后续，不重复建立前次会战。')
E=ev('wucongjian_zhaodejun_captures_hemiao','赵德钧遣武从谏率精骑邀击，分兵扼险，生擒惕隐等数百人',26,'八月','生擒惕隐等数百人；',[('德钧','遣骑分扼者'),('武从谏','牙将、精骑邀击统领'),('惕隐','被生擒本次援军酋长')],when='928年八月甲戌',place='幽州境及险要',note='数百为主概数；惕隐沿前批本次赫邈，非秃馁；武新人未因同幽州将把将来武贵妃亲属自动挂入。')
claim('event',E,'time_original','旧明宗纪在八月壬午记幽州赵德钧奏府西邀杀败军数千、生擒惕隐等五十余人。',26,'壬午，幽州趙德鈞奏，於府西邀殺契丹敗黨數千人，生擒首領惕隱等五十餘人。','壬午是奏报日，与主甲戌截击分别保留；数千邀杀与五十余被擒不是同类别，主数百与旧数不同不合并。',source=aug,relation='conflicts')
claim('event',E,'description','旧王传称赵德钧派武从谏截击，分扼要路，旬日内获惕隐以下酋长七百余。',26,'惕隱以餘眾北走幽州，趙德鈞令牙將武從諫以騎邀擊。德鈞分扼諸要路，旬日之內，盡獲惕隱已下酋長七百餘人，契丹遂弱。','旬日内累计、主截击数百、旧纪五十余分类阶段有异，七百余不等当天单战俘数；不当精确全部被俘名录。',source=old,relation='conflicts')
claim('event',E,'description','新明宗纪八月将被赵德钧擒的首领记作愓隐赫邈。',26,'八月，盧龍軍節度使趙德鈞執契丹首領愓隱赫邈。','愓/惕保留底本不同写法，只按同案赫邈确认人名，不将官称全部任者同人。',source=ann,relation='corroborates')
claim('event',E,'description','新王传称惕隐与数十骑逃至幽州西，被赵德钧擒送京师。',26,'惕隱與數十騎走至幽州西，為趙德鈞擒送京師。','数十骑为末段逃随而非所有被俘总数，与主数百分别保留。',source=new)
E=ev('villagers_attack_scattered_khitan_survivors','契丹余军散投村落，村民白梃击之，逃归者不过数十',26,'馀众散投','不过数十人。',[],place='幽州境村落及北归路',note='白梃为原述器物；不过数十为史载概数，不能用七千减数十算精确死者，多阶段俘获不等全亡。')
claim('event',E,'description','旧明宗纪同记秋雨泥泞饥乏、败军散入村落被白梃击杀，仅奇峰岭北有马者数十余逃脱。',26,'是時，官軍襲殺契丹，屬秋雨繼降，泥濘莫進，人饑馬乏，散投村落，所在村民持白梃毆殺之。德鈞出兵接於要路，惟奇峰嶺北有馬潛遁脫者數十餘，無噍類。','奇峰岭地名据补证不猜坐标，無噍類是叙述用语，兼存所述逃脱者，不另断绝对全歼。',source=aug)
E=ev('khitan_morale_after_youzhou_defeat','史书记此后契丹气沮，不敢轻易犯塞',26,'自是',None,[],year=None,when='八月幽州败后的一段时期，终止年未载',place='后唐北部边境',note='沮气、不敢轻犯为史家后续评价，非永久和平、无任何边境冲突，未具体断定有效截止年。')
E=ev('cunxu_captures_child_lijitao_hebei','李存勖早年徇河北获一小儿，养于宫中',27,'初','畜之宫中，',[('庄宗','获儿及宫中收养者'),('李继陶','当时未具姓名的所获小儿')],year=None,when='初追叙庄宗徇地河北，确年日未载',place='河北、庄宗宫中',note='畜宫不等亲生之子，不据王都后言造庄宗亲父边；李继陶后授名仅回识同一人。')
claim('person',people['李继陶'],'aliases','旧史记李继陶先被庄宗俘获收养，故名得得。',27,'李繼陶者，莊宗初略地河朔，俘而得之，收養於宮中，故名曰得得。','得得为书文明称登记别名，未推生父、生年、族属，非繁简近名自动猜合。',source=jitao)
E=ev('cunxu_names_lijitao_when_grown','小儿长成后，李存勖赐姓名李继陶',27,'及长','李继陶；',[('庄宗','赐姓名者'),('李继陶','受姓名者')],year=None,when='河北获儿宫养长成以后，确年日未载',place='庄宗宫中',note='李姓赐名不能推生物亲父关系，未把及长换算成年年龄。')
E=ev('siyuan_releases_lijitao_accession','李嗣源即位后放遣李继陶',27,'帝即位','纵遣之。',[('帝','即位后放遣者'),('李继陶','被放遣者')],year=None,when='明宗即位后的追叙，具体放遣日未载',place='后唐宫中',note='即位作相对定位，放遣不必恰即位当日；不强926具体月日，旧交养说另保留。')
E=event('anzhonghui_assigns_lijitao_to_duanhui','旧史补天成初安重诲把李继陶交段佪养作儿子',27,'天成初，安重誨知其本末，付段佪養之為兒；',[('安重诲','交付养育者'),('段佪','接养作儿子者'),('李继陶','被交养者')],source=jitao,year=None,when='旧史天成初，确年日未载',place='后唐，地点未具',note='旧补处置过程，不把主纵遣时点与交养硬等同；段佪依原字，未猜近形段凝同人。')
relationship('段佪','李继陶','养父',27,'天成初，安重誨知其本末，付段佪養之為兒；','按养之为儿建立段佪是李继陶养父；不据宫养字样另造李存勖亲父。',source=jitao)
E=event('duanhui_allows_lijitao_choose_departure','旧史补段佪因李继陶不称，许其自行去就',27,'佪知其不稱，許其就便。',[('段佪','许自行去就者'),('李继陶','获准去就者')],source=jitao,year=None,when='天成初交养之后，确年日未载',place='后唐，地点未具',note='不称原语含义保留，不推忤逆、不孝罪及具体处分日。')
E=ev('wangdu_obtains_lijitao','王都获得李继陶',27,'王都得','王都得之，',[('都','获取李继陶者'),('李继陶','被王都取归者')],year=None,when='定州叛乱前取得李继陶的追叙，确年日未载',place='王都所部',note='旧潜取以归及都叛分别叙，不能将取得本人强定928年；与城堞包装行动分录。')
E=ev('wangdu_yellow_robe_lijitao_false_imperial_claim','王都令李继陶穿黄袍坐城堞，宣称其为庄宗之子已即帝位',27,'使衣','曾不念乎！”',[('都','借李身份劝说者'),('李继陶','黄袍城堞被利用者'),('晏球','被劝说者')],when='928年定州围城本段，确日未载',place='定州城堞',note='庄宗之子及即帝位是王都宣称，不能录真实亲子关系或正式皇帝登基；衣黄袍不等本站承认正统。')
claim('event',E,'description','旧史称王都潜取李继陶归，呼作庄宗太子，叛后令着服装登城以惑军士，众知其伪而辱骂。',27,'王都素蓄異志，潛取以歸，呼為莊宗太子。及都叛，遂僭其服裝，時俾乘墉，欲惑軍士，人咸知其偽，競詬辱之。','太子/皇帝子为王都包装，新称身分不建真实父子或太子授命；人咸知为史家概述，不精确统计所有军民态度。',source=jitao)
E=ev('wangyanqiu_rejects_lijitao_scheme_demands_battle_surrender','王晏球斥王都伎俩，指出应全军决战或投降',27,'晏球曰',None,[('晏球','拒诱并提出两策者'),('都','被回应者')],place='定州围城',note='二策是劝告、逼降语言，不记王都此时已经出降；不提前翌年李继陶被擒处死。')
E=ev('wangjianli_requests_relief_three_commissions','王建立以不识文字请求免判三司',28,'王建立','请罢判三司，',[('王建立','申请免职者')],place='后唐朝廷',note='目不知书为自述理由，未推身体失明；请求罢不是已罢官，区别十一月正式外镇。')
E=ev('court_refuses_wangjianli_three_commissions_relief','朝廷不许王建立免判三司',28,'不许。',None,[('王建立','请罢未获准者')],place='后唐朝廷',note='不许明确结果，不推新授三司或科举资格。')
E=ev('wu_august_general_amnesty','吴大赦',29,'乙未',None,[],when='928年八月乙未',place='吴',note='未载赦免范围不猜具体罪名，不推所有政权同步大赦。')
E=ev('qianliu_selects_heir_by_achievement','钱镠欲立钱传瓘为嗣，令诸子自陈功绩择多者',30,'吴越王','吾择多者而立之。”',[('镠','选择继承者及提问者'),('传瓘','拟定继承对象')],when='928年闰八月授镇前的继嗣安排，确日未载',place='吴越',note='欲立及询功是安排过程，不等本年钱镠已死或传瓘已成为国王。')
E=ev('qian_sons_recommend_qianchuanguan','钱氏诸子推举钱传瓘为嗣',30,'传瓘兄','皆推传瓘，',[('传瓘','受推举者'),('传璟','推传瓘者')],when='928年继嗣安排、闰八月授镇前，确日未载',place='吴越',note='原列传璹、传瓘、传璟；传璹字未获他证，不接已有钱传璙也不造潜在重复实体。传瓘自身列于推举句按主原字保留，不擅改人物名单。')
claim('event',E,'description','主书名单原列传璹、传瓘、传璟皆推传瓘，其中传璹字形待考。',30,'传瓘兄传璹、传瓘、传璟皆推传瓘，','传璹仅作为原称待核，未假定其为钱传璙；未明传璟与传瓘长幼，不建哥哥或弟弟。')
relationship('镠','传瓘','父亲',30,span(30,'吴越王','皆推传瓘，'),'中子及诸子承钱镠，复用既有同向父亲关系，非别立元瓘同人。')
relationship('镠','传璟','父亲',30,span(30,'吴越王','皆推传瓘，'),'诸子承钱镠，传璟为其子；未猜生母、生年或排行。')
E=ev('qianliu_requests_two_commands_chuanguan','钱镠奏请把两镇授钱传瓘',30,'乃奏请','授传瓘。',[('镠','向朝廷奏请者'),('传瓘','两镇拟授者')],when='928年闰八月丁未授命前，确日未载',place='吴越至后唐朝廷',note='奏请与诏准分录，镇名依紧接诏镇海镇东，不添此前军镇边界地图。')
E=ev('qianchuanguan_zhenhai_zhendong_commissions','朝廷命钱传瓘为镇海、镇东节度使',30,'闰月',None,[('传瓘','镇海镇东获任者')],when='928年闰八月丁未',place='镇海、镇东',note='闰月承八月为闰八月，双镇任官非本年吴越国王继位。')
claim('event',E,'description','旧明宗纪同日记钱元瓘为杭州越州大都督府长史，充镇东镇海节度使，列原两浙留后等职。',30,'閏月丁未，兩浙節度觀察留後、清海軍節度使、檢校太師、兼中書令錢元瓘可杭州、越州大都督府長史，充鎮東、鎮海等軍節度使。','元瓘与主传瓘同案同日期两镇身份，沿既有钱传瓘，不按改名新建；依前官衔不是本日全新授。',source=inter,relation='corroborates')
E=ev('zhaodejun_presents_hemiao_captives','赵德钧向朝廷献惕隐等契丹俘虏',31,'戊申','献契丹俘惕隐等，',[('德钧','献俘者'),('惕隐','被献俘酋长')],when='928年闰八月戊申',place='幽州至后唐朝廷',note='献俘不同前八月生擒，不造重新被擒第二次。')
E=ev('generals_ask_execution_khitan_captives','诸将请求诛杀契丹俘虏',31,'诸将','皆请诛之，',[],when='928年闰八月戊申献俘时',place='后唐朝廷',note='诸将未具名，不猜王晏球亲自参与建议；请杀与实际分流处理分开。')
E=ev('siyuan_prefers_spare_chiefs_for_border_relief','李嗣源认为留契丹骁将可缓边患，不应尽杀',31,'帝曰','以纾边患。”',[('帝','论留俘安边策略者')],when='928年闰八月戊申献俘时',place='后唐朝廷',note='纾边患是帝判断与目的，不能凭此认定后来永久边患消失。')
E=ev('hemiao_fifty_chiefs_pardoned_personal_guard','惕隐等五十名酋长获赦，置于亲卫',31,'乃赦','置之亲卫，',[('惕隐','获赦并入亲卫酋长')],when='928年闰八月戊申',place='后唐朝廷亲卫',note='五十为主所记留者，非前所有被擒数；不造其自然长期忠诚，未与另六百混作同批全赦。')
claim('event',E,'description','旧明宗纪同日记惕隐等五十留亲卫，其余契丹六百斩。',31,'戊申，趙德鈞獻戎俘於闕下，其蕃將惕隱等五十人留於親衛，餘契丹六百人皆斬之。','同日留、斩分流，旧无帝论详细话语，不当引用直接印证其原话。',source=inter,relation='corroborates')
claim('event',E,'description','新四夷附录称赦赫邈，选壮健五十余人为契丹直。',31,'明宗斬禿餒等六百餘人，而赦赫邈，選其壯健者五十餘人為「契丹直」。','新将处理叙在定州陷擒秃馁之后且斩者列秃馁，与主本年献俘及次年定州陷时序不同；仅补赫邈名与契丹直称，不能将秃馁死亡提前本年。',source=he,relation='conflicts')
E=ev('six_hundred_khitan_captives_executed','其余六百名契丹俘虏被斩',31,'馀六百',None,[],when='928年闰八月戊申',place='后唐朝廷',note='六百为史载处理数，不凭新合叙把秃馁已被斩纳入本年；未名不编名单。')
claim('event',E,'description','旧明宗纪同日称其余契丹六百皆斩。',31,'戊申，趙德鈞獻戎俘於闕下，其蕃將惕隱等五十人留於親衛，餘契丹六百人皆斬之。','印证本次分流，不能将五十留者当已被斩。',source=inter,relation='corroborates')
E=ev('khitan_meilaojisu_tribute','契丹遣史载梅老季素等入贡',32,'契丹',None,[],place='契丹至后唐朝廷',note='梅老季素底本未分姓名官称，暂不拆成两人，也不将其按梅老二字合到907袍笏梅老主体，保留原称待考。')
claim('event',E,'description','旧明宗纪闰月亦记契丹遣使来贡献，未具使者名。',32,'契丹遣使來貢獻。','主具梅老季素称名，旧未具名；相邻同月贡使并看但未反推其姓名拆分。',source=inter,relation='corroborates')
review='卷276连续928年第26—32段逐句校核。七月易州后北撤饥疲、八月甲戌赵遣武精骑分扼擒惕隐、村击与数十逃、此后气沮评价分事；武新人不自动补后亲属，惕隐沿本次赫邈。旧八月壬午奏与主甲戌行动分，数百/五十余/旬日七百余分类阶段差异并列，不精确全军死亡。初李继陶河北获儿宫畜、长赐姓名、帝即位放遣追叙null；旧得得别名与天成初安交段佪养子、许就便补年null，段佪养父明示，庄宗宫养非亲生。王都取得李继陶追叙年null，与反后黄袍城堞包装分开；王都黄袍皇子帝位宣称不是事实亲子或正式皇帝位，旧太子包装及众辱印证性质，未提前翌年城陷李被杀。王建目不知书请罢、不许分，目不识非失明，请罢不是已罢；乙未吴赦不猜罪。钱镠欲立子询功、诸子名单推传瓘、奏两镇、闰八月丁未诏准分；传璹仅原称疑字未接钱传璙不造潜在重复人物；传璟新主体父钱镠明示，未明与瓘长幼。钱传瓘/元瓘同案同双镇同人不重建；双镇官命非钱镠死亡或传瓘国王即位。戊申献、诸将请杀、帝安边判断、五十赦亲卫、六百斩分；新四夷将此处理合叙定州城陷擒秃馁后，斩者禿餒时序与主本年异保留，绝不把秃馁死亡提前928。契丹直补称名五十余与主五十分别保留，不建未来永忠关系。梅老季素姓名官称连绵待考，不拆或接907袍笏梅老，旧同月贡使未名只能并看。繁简仅规范展示，原文定位保留，纸本异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(26,33):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(26,33)],next_paragraph='zztj-v276-y0928-p033',next_volume=276,next_year=928,supplements=supplements,excluded_non_body=[],coverage='卷276连续928年第26—32段、原文件58—64行；幽州败军截击、李继陶身世与王都利用、判三司请辞、吴赦、吴越继嗣双镇、契丹献俘与贡使。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(26,33)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
