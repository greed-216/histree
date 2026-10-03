# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 13–17."""
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
 ('tongjian-276-salt-wars',YEAR/'part-02/sources/library/tongjian-276-salt-wars','f890926e','司马光等'),
 ('tongjian-276-dingzhou-start',P/'sources/library/tongjian-276-dingzhou-start','db4b82d4','司马光等'),
 ('jiuwudaishi-064-wangyanqiu-dingzhou',P/'sources/library/jiuwudaishi-064-wangyanqiu-dingzhou','db4b82d4','薛居正等'),
 ('xinwudaishi-046-wangyanqiu-dingzhou',P/'sources/library/xinwudaishi-046-wangyanqiu-dingzhou','db4b82d4','欧阳修'),
 ('xinwudaishi-039-wangdu-dingzhou',P/'sources/library/xinwudaishi-039-wangdu-dingzhou','db4b82d4','欧阳修'),
 ('jiuwudaishi-039-may',P/'sources/library/jiuwudaishi-039-may','db4b82d4','薛居正等'),
 ('jiuwudaishi-039-april',YEAR/'part-03/sources/library/jiuwudaishi-039-april','b559f13a','薛居正等'),
 ('xinwudaishi-006-928',YEAR/'part-01/sources/library/xinwudaishi-006-928','c991ab36','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-salt-wars','tongjian-276-dingzhou-start']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p013-p017',
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
for n in range(13, 18):
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
    ck = f'claim_zztj_276_0928_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','都':'王都','重诲':'安重诲','建立':'王建立','晏球':'杜晏球','王晏球':'杜晏球','濛':'杨濛','德钧':'赵德钧','硃建丰':'朱建丰','建丰':'朱建丰','馁':'秃馁'}
NEW_ALIASES={'朱建丰':['硃建丰','朱建豐'],'赵敬怡':['趙敬怡'],'郑季璘':['鄭季璘'],'杜弘寿':['杜弘壽']}
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

def event(code, title, n, quote, actors, when='928年五月本段；确日未载', note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
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
old='jiuwudaishi-064-wangyanqiu-dingzhou';new='xinwudaishi-046-wangyanqiu-dingzhou';du='xinwudaishi-039-wangdu-dingzhou';may='jiuwudaishi-039-may';apr='jiuwudaishi-039-april';ann='xinwudaishi-006-928'
E=ev('wangdu_autonomous_offices_taxes','史书追叙王都镇易定，自授刺史以下官、租赋用于本军',13,'初','租赋皆赡本军。',[('都','义武节度使兼中书令、自治官赋所归者')],year=None,when='初追叙镇易定期间，具体起年未载',place='易州、定州',note='十馀年是原述，不据此倒推初任年份；与已录921夺位并看，计年范围待核，不重造父位事件。')
E=ev('anzhonghui_restricts_wangdu_by_law','安重诲掌政后逐步用法制约束王都',13,'及安重诲','稍以法制裁之；',[('重诲','制约者'),('都','受制约者')],year=None,when='安重诲用事后的追叙，确年日未载',place='后唐朝廷与义武',note='稍是逐渐，不虚构具体法条、诏令颁日与税率。')
claim('event',E,'description','新王氏传同述安重诲每以法约束王都，王都开始有异志。',13,'及明宗立，頗惡都為人，而安重誨每以法繩之，都始有異志。','新所述动机与评价保留叙述性质，不当正式法案或已成立司法谋反判决。',source=du,relation='corroborates')
E=ev('siyuan_dislikes_wangdu_usurpation','李嗣源因王都篡父位而厌恶之',13,'帝亦','恶之。',[('帝','厌恶所归者'),('都','所针对者')],year=None,when='初追叙，确年日未载',place='后唐朝廷',note='厌恶为史载态度，父位是已有921前事背景，不新造生父或把养父改为亲父。')
E=ev('border_garrisons_wangdu_suspicion','契丹多次侵边，朝廷屯兵幽易，王都暗中防备往来大将，猜疑渐深',13,'时契丹','浸成猜阻。',[('都','防备朝廷往来军将者')],year=None,when='王都起叛前的边防背景，确年日未载',place='幽州、易州',note='数犯、多屯、浸为背景叙述，不虚构每次侵边或指定未具名诸将；防备不等已经开战。')
claim('event',E,'description','新王氏传记唐军多次往来定州，王都供饷不足，因此更不自安。',13,'是時，唐兵擊契丹，數往來定州，都供饋多闕，益不自安。','补新所述供饷问题与动机，不以此给原主未具的欠饷金额。',source=du)
E=ev('hezhaoxun_advises_wangdu_self_preservation','王都怕被调往他镇，和昭训劝其谋自全',13,'都恐','为自全之计，',[('都','担忧被迁镇者'),('和昭训','腹心、提出自全之计者')],year=None,when='起叛前追叙，确年日未载',place='义武',note='恐迁是担忧，未当已有调镇诏；腹心不等亲属，劝计不造具体已成组织。')
claim('event',E,'description','新王氏传补和昭训以天子新立、四方未附为由劝王都谋自安。',13,'和昭訓為都謀曰：「天子新立，四方未附，其勢易離，可為自安之計。」','四方未附与易离为和的判断，不作全国政治忠诚客观统计。',source=du)
E=ev('wangdu_seeks_zhaodejun_marriage','王都向卢龙节度使赵德钧求婚',13,'都乃','卢龙节度使赵德钧。',[('都','求婚联亲者'),('德钧','卢龙节度使、所求联亲对象')],year=None,when='王都叛前联络，确年日未载',place='义武至卢龙',note='未明双方拟嫁娶的人名与是否获准，不造二人自己结婚或已形成姻亲边。')
E=ev('wangdu_contacts_wangjianli','王都因王建立与安重诲有隙，遣使结兄弟，并谋恢复河北旧例',13,'又知成德','阴与之谋复河北故事，',[('都','遣使联络者'),('建立','成德节度使、被联络者')],year=None,when='起叛前追叙，确年日未载',place='义武与成德',note='主后文明王阳许密奏，不将此拟议结兄弟当真实共同反唐或建立永恒结盟边。')
E=ev('wangjianli_feigns_agrees_reports','王建立表面应允王都，暗中奏报朝廷',13,'建立阳许','密奏之。',[('建立','表面许而密报者')],year=None,when='上述联络之后，确年日未载',place='成德至后唐朝廷',note='阳许非真实共谋已实施；与上批安告建立有异志不同，不因前告发直接认定其反叛。')
E=ev('wangdu_wax_letters_five_commands','王都以蜡书联络青徐潞益梓五镇，意图离间',13,'都又以','离间之。',[('都','送蜡书联络者')],year=None,when='起叛前联络，确年日未载',place='义武至青、徐、潞、益、梓',note='主列地名不具五帅姓名，不能按后职位猜演员；书信联络不等五镇均已加入反叛。')
claim('event',E,'description','新王氏传将五镇列作青徐岐潞梓，称约同举兵而五镇不应。',13,'遣人以蠟書招青、徐、岐、潞、梓五鎮，約皆舉兵，而五鎮不應。','主益、新岐有地点差异并列，未改原字；不应是新补结果，不能据此造五军已出兵。',source=du,relation='conflicts')
E=ev('wangdu_tries_recruit_wangyanqiu','王都遣人游说北面副招讨使王晏球，遭拒绝',13,'又遣人说','晏球不从；',[('都','遣游说者'),('晏球','归德节度使北面副招讨使、拒从者')],year=None,when='四月癸巳奏报之前，确年日未载',place='义武与北面军',note='王晏球沿已校杜晏球同人key，李绍虔为旧赐名；拒从不造新的父母或长幼关系。')
E=ev('wangdu_bribes_retinue_failed_plot','王都赠金王晏球帐下，图谋王晏球而未成',13,'乃以金','不克；',[('都','贿金图谋者'),('晏球','图谋所针对者')],year=None,when='四月癸巳奏报前，确年日未载',place='北面军帐下',note='使图之及不克为谋未成，不建已遇刺身亡；帐下未具名不虚构刺客及金数。')
E=ev('wangyanqiu_reports_wangdu_rebellion','王晏球奏报王都反状',13,'癸巳','反状闻，',[('晏球','奏报者'),('都','反状所涉者')],when='928年四月癸巳',place='北面军至后唐朝廷',note='癸巳回到当前年四月；奏报内容与叛乱具体每一步日期区别。')
claim('event',E,'description','旧明宗纪同记北面副招讨、宋州节度使王晏球上报王都反状。',13,'北面副招討、宋州節度使王晏球以定州節度使王都反狀聞。','宋州归德、定州义武治州军名不同叙法相合；旧此句在癸巳项内不另具日，主干支据主。',source=apr,relation='corroborates')
E=ev('court_orders_campaign_discussion','朝廷命张延朗与北面诸将议讨王都',13,'诏宣徽使',None,[('张延朗','宣徽使、奉命议讨者')],when='928年四月癸巳王都反状奏报后',place='北面军、后唐朝廷',note='议讨为军事决策阶段，不与壬寅实际授讨使和攻城合并；诸将未具名不猜补名单。')
E=ev('yangmeng_linchuan_title','吴改封常山王杨濛为临川王',14,'戊戌',None,[('濛','由常山王改封临川王者')],when='928年四月戊戌',place='吴',note='同人既有杨濛key，常山前号和临川新号不造两人；未直接指本人已赴临川。')
E=ev('wangdu_stripped_offices_titles','朝廷削夺王都官爵',15,'庚子','王都官爵。',[('都','被削官爵者')],when='928年四月庚子',place='后唐朝廷、义武',note='削官爵为诏令，不等已俘王都或城已陷。')
claim('event',E,'description','旧明宗纪同日记削夺王都在身官爵，列义武节度使、太原王等原衔。',15,'庚子，製義武軍節度使、檢校太尉、兼中書令、太原王王都削奪官爵。','原衔概录不单独造原官爵授予日期；太原王爵号不是本次占领太原。',source=apr,relation='corroborates')
E=ev('wangyanqiu_northern_commander_dingzhou','王晏球任北面招讨使，权知定州军州事',15,'壬寅','权知定州行州事，',[('晏球','北面招讨使权知定州事务获任者')],when='928年四月壬寅',place='北面行营、定州',note='主北面讨使、行州事疑脱字，展示参旧招讨使、军州事称法，原字保留；权知不等定州已攻克。')
claim('event',E,'description','旧明宗纪同日记王晏球为北面行营招讨使，知定州军州事。',15,'壬寅，以王晏球為北面行營招討使，知定州行軍州事；','主行州事/旧行军州事及讨使/招讨称法并列，不能靠繁简转换改底本脱字。',source=apr,relation='corroborates')
claim('event',E,'description','新明宗纪同日称归德军节度使王晏球为北面行营招讨使。',15,'壬寅，歸德軍節度使王晏球為北面行營招討使。','同人既存宋州归德两名，维持杜晏球key。',source=ann,relation='corroborates')
E=ev('anshentong_deputy_campaign','横海节度使安审通任副招讨使',15,'以横海','为副招讨使，',[('安审通','副招讨使获任者')],when='928年四月壬寅',place='北面行营',note='沿926已有主体，不提前后七月卒于师。')
claim('event',E,'description','旧明宗纪补安审通兼诸道马军都指挥使。',15,'以滄州節度使兼北面行營馬軍都指揮使安審通為副招討使兼諸道馬軍都指揮使；','沧州横海治州军号相合，补军衔不当另一次新任。',source=apr)
E=ev('zhangqianzhao_campaign_supervisor','郑州防御使张虔钊任都监',15,'以郑州','为都监，',[('张虔钊','都监获任者')],when='928年四月壬寅',place='定州行营',note='都监为军职，不推个人已出战或后续促攻本日完成。')
E=ev('court_gathers_armies_dingzhou','朝廷发诸道兵会讨定州',15,'发诸道','会讨定州。',[],when='928年四月壬寅',place='诸道至定州',note='未具兵数与军将名单，不能推所有全国军队齐到。')
E=ev('wangyanqiu_takes_north_gate','王晏球同日攻定州，取北关城',15,'是日','拔其北关城。',[('晏球','攻取北关城者')],when='928年四月壬寅',place='定州北关城',note='北关城是外关，不能作定州主城已经陷落。')
E=ev('wangdu_bribes_tunei_for_aid','王都用重赂向奚酋秃馁求救',15,'都以重赂','奚酋秃馁，',[('都','贿金求援者'),('馁','主书所称奚酋、被求援者')],when='928年四月攻定州后、五月援至前，确日未载',place='定州至奚、契丹援军',note='主奚酋与下契丹军性质并列，不猜现代族籍；此后呼为诺王等未在主本句明示，不提前造称王登位。')
E=ev('tunei_enters_dingzhou_ten_thousand','秃馁以万骑突入定州',15,'五月','突入定州，',[('馁','援定州骑军统领')],when='928年五月，确日未载',place='定州',note='主万骑是本次初援记载；其他书不同数并列，不按所有援军批次合算。')
claim('event',E,'description','旧王晏球传称契丹遣秃馁领千余骑援王都，突入定州。',15,'契丹遣禿餒率騎千餘來援都，突入定州，','主万骑、旧千馀初援数量不同保留；传前是岁承天成二年叙序亦较简，主本行动928据主，不强各阶段同年同日。',source=old,relation='conflicts')
claim('event',E,'description','新王晏球传称契丹遣秃馁领万骑救王都。',15,'都遣人北招契丹，契丹遣禿餒將萬騎救都。','印证主初援万骑，不能将其后七千另一援军提前当本次万骑组成。',source=new,relation='corroborates')
claim('event',E,'description','新明宗纪在五月记契丹秃馁入定州。',15,'五月，契丹禿餒入于定州。','补五月同一行动，未给具体日。',source=ann,relation='corroborates')
E=ev('wangyanqiu_retires_quyang','王晏球退保曲阳',15,'晏球退保','晏球退保曲阳，',[('晏球','退保者')],place='曲阳',note='退保是实际军动，不等战败溃军全灭。')
E=ev('wangdu_tunei_attack_quyang','王都与秃馁追攻曲阳的王晏球军',15,'都与秃馁','就攻之。',[('都','进攻者'),('馁','同攻者')],place='曲阳',note='都与秃馁当次军事协同，未造结拜或夫妻关系。')
E=ev('jiashan_victory_tunei_returns','王晏球在嘉山下大败王都与秃馁，秃馁以二千骑退回定州',15,'晏球与战','奔还定州。',[('晏球','嘉山胜军统领'),('馁','以二千骑奔还者')],place='嘉山、定州',note='二千是败后所率返回，区别初援万骑，不能当单凭数字已核八千死者。')
claim('event',E,'description','旧王晏球传记用短兵击王都与契丹军，在嘉山下大败敌军、追至城门。',15,'晏球督厲軍士，令短兵擊賊，戒之曰：「回首者死。」符彥卿以龍武左軍攻軍其左，高行周以龍武右軍攻其右，奮劍揮楇，應手首落，賊軍大敗於嘉山之下，追襲至於城門。','旧将短兵会战概叙于嘉山，主嘉山及后曲阳分别叙；右军旧高行周与新高行珪不同人名保留，不将两将自动合并或强定都在同战。',source=old)
E=ev('wangyanqiu_takes_west_gate','王晏球追至定州城门，攻得西关城',15,'晏球追至','得其西关城。',[('晏球','追击及攻取西关城者')],place='定州西关城',note='西关城不是定州主城，未提前929全城克复。')
claim('event',E,'description','旧明宗纪五月记王晏球奏已收定州北西二关城。',15,'王晏球上言，收奪得定州北西二關城。','奏报将两阶段成果合记，旧未为此句独具干支，不能强辛亥即两关攻取日。',source=may,relation='corroborates')
E=ev('wangyanqiu_builds_west_gate_base_siege','因定州城坚难攻，王晏球增修西关城为行府，以三州民税供军而围守',15,'定州城坚',None,[('晏球','修行府、组织军食及围守者')],place='定州西关城、三州范围未具',note='三州未具名不猜地理边界；供军税未列税率，围守不等已克城。')
E=event('zhengjilin_duhongshou_intercepted','新史记王都遣郑季璘、杜弘寿二千人迎契丹，遭王晏球击败并被擒',15,'都遣指揮使鄭季璘、龍泉鎮將杜弘壽以二千人迎契丹，為晏球所敗。季璘、弘壽被執，',[('郑季璘','指挥使、领迎军后被擒者'),('杜弘寿','龙泉镇将、迎军后被擒者'),('晏球','新传所记击败迎军者')],source=du,when='928年定州役援军联络阶段，新传未具确月日',place='定州与契丹迎军途中',note='新独补迎军，并非主秃馁败后返回二千骑同一群体；被擒两将不等二将均已处决。')
E=event('duhongshou_declares_loyalty_executed','新史记杜弘寿自述受恩中山两世不敢二心，随后被杀',15,'晏球責曰：「吾嘗使人招汝，何故不降？」弘壽對曰：「受恩中山兩世矣，不敢有二心。」遂見殺，弘壽臨刑，神色自若。',[('晏球','质问为何不降者'),('杜弘寿','被质问、自述忠心及被杀者')],source=du,when='定州役迎军被擒后，新传未具月日',year=None,place='军前，地点本句未明',note='受恩两世为杜陈述，不造其与王氏亲属；遂见杀主语接杜，不扩大郑季璘也必同死，神色自若是史家叙述。')
E=event('youzhou_reports_tunei_two_thousand','旧史记幽州奏秃馁领二千骑向西南趋定州',15,'己未，幽州奏，契丹禿餒領二千騎西南趨定州。',[('馁','幽州所报领骑者')],source=may,when='928年五月己未奏报，所报出动确日未载',place='幽州至定州方向',note='二千是此奏报阶段，不强当主初援万骑或败后返城二千完全同一统计样本。')
E=ev('zhaojingyi_shumishi','天雄节度副使赵敬怡任枢密使',16,'辛酉',None,[('赵敬怡','天雄节度副使、枢密使获任者')],when='928年五月辛酉',place='后唐朝廷',note='新主体逐字赵敬怡，未按相似名合到赵敬贻；不提前929卒。')
claim('event',E,'description','旧明宗纪同日补赵敬怡原判兴唐府事。',16,'辛酉，以天雄軍節度副使、判興唐府事趙敬怡為樞密使。','补原兼职，未造兴唐府新任另一次事件。',source=may)
claim('event',E,'description','新明宗纪同日记右卫上将军赵敬怡任枢密使。',16,'辛酉，右衞上將軍趙敬怡為樞密使。','新原衔右卫与主旧天雄副不同叙法并列，不能据此认为两个同名人或所有兼职都互斥。',source=ann)
E=ev('wangyanqiu_moves_wangdu_relief_approach','王晏球闻契丹发兵救定州，率大军趋望都',17,'王晏球闻','将大军趣望都，',[('晏球','率军趋望都者')],place='望都',note='将大军为带军行动，非将要的计划；契丹另次救兵未直接等五月初援同一批。')
E=ev('zhangyanlang_travels_zhending_leaves_zhujianfeng','王晏球命张延朗分兵退保新乐，张转往真定，留朱建丰修新乐城',17,'遣张延朗','将兵修新乐城。',[('晏球','命退保者'),('张延朗','转真定、留修城军者'),('建丰','赵州刺史、领军修新乐城者')],place='新乐、真定',note='主命退保与张实际转真定是不同动作同段组合；朱硃已有字形常用，姓名新限定不是朱友丰。')
E=ev('wangdu_khitan_night_take_xinle_kill_zhu','契丹循他路入定州，与王都夜破新乐，杀朱建丰',17,'契丹已','杀建丰。',[('都','夜袭者'),('建丰','被杀赵州刺史')],place='定州至新乐',note='死亡只朱建丰，不能录张延朗亦死；契丹主将本句未名不强全由秃馁独指。')
claim('event',E,'description','新王传称契丹入定州后与王都突袭张延朗军，张大败后收余兵会王晏球趋曲阳。',17,'而契丹從他道入定州，與都出不意擊延朗軍，延朗大敗，收餘兵會晏球趨曲陽，都乘勝追之。','新未具朱建丰死亡姓名，补张败后存活收军，不以此引用直接印证朱被杀。',source=new)
claim('event',E,'time_original','旧明宗纪在五月丁卯记镇州奏五月十八日官军不利于新乐。',17,'丁卯，鎮州奏，今月十八日，王師不利於新樂。','丁卯为奏报日、十八为所报发生日，原样并记不自动换算公历；主夜袭未具日，不强丁卯即夜袭。',source=may)
E=ev('wangyanqiu_zhangyanlang_meet_xingtang','王晏球与张延朗会于行唐',17,'乙丑','会于行唐，',[('晏球','会军者'),('张延朗','会军者')],when='928年五月乙丑',place='行唐',note='实际会军不等前张仍屯新乐，也不是其死亡后再现。')
E=ev('wangyanqiu_zhangyanlang_arrive_quyang','王晏球、张延朗到曲阳',17,'丙寅','至曲阳。',[('晏球','率军到达者'),('张延朗','同到曲阳者')],when='928年五月丙寅',place='曲阳',note='承前同军主体，不补舟或人数。')
E=ev('wangdu_khitan_intercept_quyang','王都集合本部与契丹五千骑，合万余人，在曲阳拦截唐军',17,'王都乘胜','邀晏球等于曲阳，',[('都','拦截合军者'),('晏球','被拦截唐军统领')],place='曲阳',note='五千骑是本次合军一部、万余为总数概录，不将所有数相加成确定十五千。')
E=ev('quyang_battle_order_close_combat','曲阳城南交战，王晏球令去弓矢用短兵，回顾者斩',17,'丁卯','回顾者斩！”',[('晏球','集将下令者')],when='928年五月丁卯',place='曲阳城南',note='王都轻骄、一战擒是晏球判断，不等王都此战已被擒；军令威慑不等实际斩了回顾者。')
E=ev('tang_cavalry_charge_quyang_victory','唐骑先冲入敌阵，大败王都与契丹军',17,'于是骑兵','大破之，',[('晏球','骑军胜战统领')],when='928年五月丁卯',place='曲阳城南',note='主奋，楇挥剑有标点及字形疑，原字保留，只概录骑军先冲不改原句；不凭主未名骑军自动猜具体左右将。')
claim('event',E,'description','新王传补符彦卿左军、高行珪右军及中军骑士抱马项冲敌，敌大败。',17,'晏球立高岡，號令諸將皆橐弓矢、用短兵，回顧者斬。符彥卿以左軍攻其左，高行珪以右軍攻其右，[2]中軍騎士抱馬項馳入都軍，都遂大敗，','新高行珪与旧嘉山概叙高行周不同人名保留，未合并或硬推同役同人；底本[2]注标原样保留，动作是史载不编现代兵种战法细节。',source=new)
claim('event',E,'time_original','旧明宗纪五月壬申记王晏球奏五月二十一日于曲阳大败定州军及契丹，斩获数千。',17,'壬申，王晏球奏，今月二十一日，大破定州賊軍及契丹於曲陽，斬獲數千人，','壬申为奏报日、二十一为所报行动日，与主丁卯分别保留原纪日，不自动换算干支或把奏报日等行动日。',source=may)
E=ev('quyang_losses_flight_wangdu_tunei_escape','曲阳败军尸遍野，契丹死者过半，王都秃馁以数骑逃脱',17,'僵尸蔽野','仅免。',[('都','以数骑逃脱者'),('馁','同逃者')],when='928年五月丁卯交战后',place='曲阳及北逃路线',note='主过半为概述，不用前五千计算确定死者人数；数骑为逃随人数，不等只存这几人；王都未被擒。')
claim('event',E,'description','新王氏传同记曲阳大败后王都与秃馁以数骑逃走，闭城不出。',17,'與都及契丹戰，大敗之曲陽，都及禿餒得數騎遯去，閉城不復出。','补回城闭守结果，未提前翌年自焚与秃馁被俘。',source=du,relation='corroborates')
claim('event',E,'description','新王传形容曲阳至定州横尸弃甲六十余里，王都与秃馁入城不再出战。',17,'都遂大敗，自曲陽至定州，橫尸棄甲六十餘里。都與禿餒入城，不敢復出。','六十余里为史载败军场面概数，不精确配地图尸体分布；闭守非定州已被唐军占领。',source=new)
E=ev('zhaodejun_intercepts_fleeing_khitan','赵德钧邀击契丹北逃军，史书记几无幸免',17,'卢龙节度使',None,[('德钧','卢龙节度使、邀击者')],when='928年五月曲阳败军北走后，确日未载',place='北走路线、卢龙范围',note='殆无是近乎无人幸免的叙述，不能写确定全部歼灭或混后七月惕隐援军被截事件。')
review='连续13—17段逐句校核。初王自治官赋、十馀年原述不倒算起任、安渐法裁、帝恶篡父、边屯防备、和劝自全、王求赵婚、联王建兄弟河北旧议、王阳许密奏、蜡书五镇、说晏拒、贿帐图未成皆追叙null；怕迁非已有诏，拟婚不猜两方子女，阳许不当真反叛或永久结义边。主益新岐五镇差异并列，未具五帅不按官职猜人，新不应不造五军出兵。癸巳奏反、议讨后戊戌杨濛临川、庚子削王、壬寅王讨权定安副张都监诸军及北关分事，讨/招讨和行州/军州疑脱原字保留，不繁简补底本。宋归德、沧横海名沿同人。五月秃万骑主、新万旧千馀不同，旧五月己未二千是报告阶段，不强初援或败返同一样本；奚酋与契丹军原性质保留。曲阳退、王秃攻、嘉山胜、二千返、追西关、修关税三州围守分事；两外关非全定州，三州未名不猜。新独补郑季璘杜弘寿二千迎军败擒与杜自述两世忠及见杀；迎军二千非秃返二千，只有杜接被杀，不扩大郑也死，杜杀确年未明null。辛酉赵敬怡枢密旧补判兴唐、新右卫原衔并列不误赵敬贻。后王趋望都、张被命新乐实至真定留朱建丰修城、契丹他路入与王夜破朱死、新张败收余、会行唐乙丑到曲阳丙寅、王合部契五千总万馀邀截、丁卯短兵军令与冲胜、过半概死及数骑两首逃、赵北截分别。旧丁卯奏报本月十八新乐、壬申奏报二十一曲阳与主原纪日并列不换公历或当报告日=行动；旧嘉山与新曲阳短兵阵容高行周/珪不同人名不合并、不硬推两人同仗实参加，旧夹通鉴注非独立印证。主奋，楇标点字疑原字保留，回顾斩只军令非已斩，王轻可擒是判断非已擒，五千/总万馀不相加和死过半不精算。新六十里弃甲原场面非地图精确分布，殆无北逃不确定全歼或提前惕隐后援。晏球沿校后杜key，其他复用已有主体；新朱建丰赵敬怡郑季璘杜弘寿，繁简匹配原文不改，纸本异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(13,18):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,18)],next_paragraph='zztj-v276-y0928-p018',next_volume=276,next_year=928,supplements=supplements,excluded_non_body=[],coverage='卷276连续928年第13—17段、原文件45—49行；王都联络与讨定州初期、杨濛改封、赵枢密、新乐曲阳战。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(13,18)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
