# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 932 paragraphs 11–15."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 24))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'e9aa70e4','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))
specs += [('tongjian-277-932-february',YEAR/'part-01/sources/library/tongjian-277-932-february','585a188b','司马光等'),('xinwudaishi-067-qian-restoration',YEAR.parent/'year-0931/part-02/sources/library/xinwudaishi-067-qian-restoration','1066c58f','欧阳修'),('liaoshi-072-bei-tang-names',YEAR.parent/'year-0931/part-02/sources/library/liaoshi-072-bei-tang-names','1066c58f','脱脱等'),('xinwudaishi-072-hemiao',ROOT/'content/books/zizhi-tongjian/vol-276/year-0928/part-05/sources/library/xinwudaishi-072-hemiao','86b40c48','欧阳修'),('xinwudaishi-064-meng-dong-dissent',YEAR.parent/'year-0931/part-05/sources/library/xinwudaishi-064-meng-dong-dissent','b9e535ed','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-932-february','tongjian-277-932-april']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0932-p011-p015',
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
for n in range(11, 16):
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
        citation = f'卷277·长兴三年（932）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0932_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','镠':'钱镠','传瓘':'钱传瓘','元瓘':'钱传瓘','仁章':'陆仁章','击仁章':'陆仁章','仁俊':'钱仁俊','刘仁'+chr(0xe3ab)+'巳':'刘仁𣏌','仁'+chr(0xe3ab)+'巳':'刘仁𣏌','赞华':'耶律倍','夏氏':'夏氏（李存勖后宫）','惕隐':'赫邈','檀':'杨檀','德钧':'赵德钧','从厚':'李从厚','璋':'董璋','知祥':'孟知祥','季良':'赵季良','廷隐':'赵廷隐'}
NEW_ALIASES={'王晖':['王暉'],'刘仁𣏌':['劉仁𣏌'],'钱仁俊':['錢仁俊'],'曹仲达':['曹仲達'],'沈崧':[],'荝剌':['萴剌','則剌','则剌','原知感'],'杨檀':['楊檀'],'夏氏（李存勖后宫）':['夏氏（莊宗後宮）'],'武弘礼':['武弘禮']}

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

def event(code, title, n, quote, actors, when=None, note='', year=932, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='932年'+('三月本段' if n==11 else '四月本段')+'；确日未独载'
    key = 'event_zztj_277_0932_' + code
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
        edge = 'participation_zztj_277_0932_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0932_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive five dense paragraphs with independently located supplements.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
old='jiuwudaishi-043-932-april'; report='jiuwudaishi-043-932-qian-report';succ='xinwudaishi-067-qian-succession';institute='xinwudaishi-067-zengneng-institute';names='xinwudaishi-072-captive-names';requests='xinwudaishi-072-captive-requests';hemiao='xinwudaishi-072-hemiao';liao='liaoshi-072-bei-character';liaonames='liaoshi-072-bei-tang-names';rest='xinwudaishi-067-qian-restoration';meng='xinwudaishi-064-meng-dong-dissent'
E=ev('qian_asks_successor','钱镠病重，询问将吏何人可以接掌',11,'吴越武肃王钱镠疾，','谁可为帅者？”',[('镠','病重询问后继者')],place='吴越')
ev('qian_officers_recommend','将吏推举钱传瓘，以其仁孝有功为由',11,'众泣曰：','孰不爱戴！”',[('传瓘','被将吏推举者'),('镠','听取推举者')],place='吴越',note='将吏评价归当事人，不视为全国民意。两镇令公沿既有钱传瓘主体。')
E=ev('qian_hands_seals','钱镠交印钥给钱传瓘，嘱善守并令子孙善事中国',11,'镠乃悉出印钥','勿以易姓废事大之礼。”',[('镠','交印钥留训者'),('传瓘','受印钥及遗训者')],place='吴越',note='善事中国为临终训示，不把后代所有朝贡自动当成已履行。')
claim('event',E,'description','新吴越世家同记将领推举元瓘、钱镠交筦钥。',11,'鏐乃出筦鑰數篋，召元瓘與之曰：「諸將許爾矣。」','主悉出印钥与新筦钥数箧各自书法保留。元瓘是改名前钱传瓘同人。',source=succ,relation='corroborates')
E=ev('qian_liu_dies','吴越武肃王钱镠卒，史载年八十一',11,'庚戌卒，','年八十一。',[('镠','去世者')],when='932年三月庚戌',place='吴越，卒地未独载',note='史载八十一不据此推算周岁或出生年份。')
claim('event',E,'description','新吴越世家记长兴三年钱镠卒，年八十一，谥武肃，子元瓘立。',11,'長興三年，鏐卒，年八十一，謚曰武肅。子元瓘立。','复用已归档出处；新可补年龄及谥号，不独提供庚戌日。',source=rest,relation='corroborates')
claim('event',E,'time_original','旧纪在七月辛巳朔记因钱镠薨而废朝三日；主卒日为三月庚戌。',11,'秋七月辛巳朔，以天下兵馬元帥、尚父、吳越國王錢鏐薨，廢朝三日。','旧朝廷纪废朝时间不等卒日，未据七月改死亡月；本批仅作为死亡通报补证，不提前新建七月废朝事件。',source=report,relation='adds')
ev('qian_brothers_shared_mourning','钱传瓘与兄弟同幄行丧',11,'传瓘与兄弟','同幄行丧，',[('传瓘','与诸兄弟同幄行丧者')],place='吴越',note='诸兄弟未具名，不凭同幄造名单或排行。')
ev('lu_separates_successor_tent','陆仁章另设一幄安置钱传瓘，限制诸公子从者入内并昼夜警卫',11,'内牙指挥使击仁章曰：','未尝休息。',[('仁章','内牙指挥使、另幄及警卫安排者'),('传瓘','被另幄安置的继业者')],place='吴越',note='本段后明载陆仁章，同职同行可识；前击仁章疑字保留不造击姓人物。禁从者妄入不是禁所有兄弟往来。')
ev('lu_opposed_qian_before_succession','史书追述钱镠末年陆仁章屡以事触犯钱传瓘',11,'镠末年左右','数以事犯之。',[('仁章','追述屡触犯传瓘者'),('传瓘','被触犯者')],year=None,when='追叙钱镠末年；确年未载',place='吴越',note='末年不硬定932；左右附与陆犯是史书叙述，不建立永久敌对关系。')
ev('qian_rewards_lu_loyalty','钱传瓘慰劳陆仁章，陆以尽节事先王回应',11,'至是，传瓘劳之，','传瓘嘉叹久之。',[('传瓘','慰劳并嘉叹者'),('仁章','以服务在位主君解释行为者')],place='吴越')
E=ev('qian_successor_changes_names','钱传瓘袭位改名元瓘，兄弟名中传字皆改为元',11,'传瓘既袭位，','皆更为“元”。',[('传瓘','袭位改名的吴越继承者')],place='吴越',note='复用钱传瓘key；元瓘作为同人改名补证，不重造第二人；未明名兄弟不逐个补名。')
claim('event',E,'description','新吴越世家记元瓘立、袭封吴越国王，玉册金印如钱镠故事。',11,'鏐卒，元瓘立，襲封吳越國王，玉冊、金印，皆如鏐故事。','新概叙袭封礼制，与主遗命去国仪层次不同；未据一句认定所有仪制已永久废尽，也未用新书否定主遗命。',source=succ,relation='adds')
ev('qian_drops_royal_ceremonies','钱传瓘依遗命去国仪，采用藩镇制度',11,'以遗命去国仪，','用籓镇法；',[('传瓘','依遗命调整仪制者')],place='吴越',note='不外推吴越国号消失或所有旧仪永久废除。')
ev('qian_remits_abandoned_land_tax','钱传瓘免除民田荒绝者的租税',11,'除民田荒绝者','租税。',[('传瓘','免荒田租税者')],place='吴越',note='免荒绝田，不泛化全部民田免税。')
ev('cao_zhongda_acting_government','钱传瓘命处州刺史曹仲达权知政事',11,'命处州刺史','权知政事。',[('传瓘','任命者'),('曹仲达','处州刺史、权知政事者')],place='吴越',note='权知政事沿原衔，不自动等同后唐宰相。')
E=ev('qian_creates_zengneng','吴越置择能院掌选举殿最，浙西营田副使沈崧领院',11,'置择能院，','以浙西营田副使沈崧领之。',[('传瓘','置院任职的吴越主'),('沈崧','浙西营田副使、领择能院者')],place='吴越')
claim('event',E,'description','新吴越世家记元瓘令国相沈崧置择能院，选吴中文士录用。',11,'使其國相沈崧置擇能院，選吳中文士錄用之。','主营田副使和新国相职称、主殿最和新文士选录范围分别保留，不将新概传在后期叙述位置硬推为另年另设同院。',source=institute,relation='adds')
luo=span(11,'内牙指挥使富阳','皆为众所恶。')
liuname='刘仁𣏌';person(liuname,11,'富阳人、久事吴越的内牙指挥使',luo)
claim('person',people[liuname],'name','展示名刘仁𣏌；底本姓名含私用区部件，暂据同卷字形对照识读。',11,luo,'富阳内牙指挥使、同陆仁章久事及后任湖州识同人；固定维基文库同卷对照见sources/glyph-comparison，不用搜索摘要作史事出处，不擅改成刘仁杞。纸本待核。')
ev('lu_liu_disliked','史书述陆仁章性刚、刘仁𣏌好毁短人，皆为众所恶',11,'内牙指挥使富阳','皆为众所恶。',[('仁章','被史述性刚者'),(liuname,'被史述好毁短人者')],year=None,when='追述二将久事及素行；确年未载',place='吴越',note='品性与众恶归史书描述，不作为现代诊断或永久敌对边。')
ev('officers_demand_lu_liu_execution','诸将赴府门请求诛陆仁章与刘仁𣏌',11,'一日，诸将','请诛之；',[('仁章','被诸将请求诛杀者'),(liuname,'被诸将请求诛杀者')],year=None,when='钱传瓘袭位后，一日；确年、月日未独载',place='吴越府门',note='一日为继位后相对时序，未确认同月；请诛不等实际处死。')
ev('qian_rejects_officers_demand','钱传瓘遣从子钱仁俊告谕诸将，拒绝以私憾诛旧将',11,'元瓘使从子仁俊','吾当归临安以避贤路！”',[('传瓘','拒请诛并条件称将归临安者'),('仁俊','从子、受遣告谕者'),('仁章','被保全旧将'),(liuname,'被保全旧将')],year=None,when='袭位后诸将请诛时；确年、月日未独载',place='吴越府门',note='条件归临安是劝威辞，不是已回临安或退位。钱仁俊从子不推具体父亲。')
relationship('仁俊','传瓘','从子',11,'元瓘使从子仁俊谕之','A→B即钱仁俊是钱传瓘的从子，不擅转亲侄、兄弟之子或补父。')
ev('officers_withdraw_request','诸将听告谕后惧而退',11,'众惧而退。','众惧而退。',[],year=None,when='袭位后告谕诸将后；确年、月日未独载',place='吴越府门')
ev('lu_quzhou_appointment','钱传瓘任陆仁章为衢州刺史',11,'乃以仁章为衢州刺史，','仁章为衢州刺史，',[('传瓘','任命者'),('仁章','被任衢州刺史者')],year=None,when='诸将退后；确年、月日未独载',place='衢州')
ev('liu_huzhou_appointment','钱传瓘任刘仁𣏌为湖州刺史',11,'仁'+chr(0xe3ab)+'巳为湖州刺史。',None,[('传瓘','任命者'),(liuname,'被任湖州刺史者')],year=None,when='诸将退后，与陆任衢州同段；确年、月日未独载',place='湖州')
ev('qian_ignores_denunciations','钱传瓘对告讦上书置而不问，史书述将吏因而和睦',11,'中外有上书',None,[('传瓘','不问告讦上书者')],year=None,when='袭位后施政概述；确年、月日未独载',place='吴越',note='由是辑睦为史叙归因，不保证此后绝无冲突。')
# Captures belong to earlier campaigns. This batch adds identity/corroboration, not another capture.
cap=span(12,'初，','契丹屡遣使请之。')
for name in ['荝剌','惕隐']:person(name,12,'前已被留在后唐，契丹屡请归的将领',cap)
claim('person',people['荝剌'],'description','通鉴追叙荝剌与惕隐皆为赵德钧所擒；新契丹附录分记萴剌由王晏球擒。',12,'晏球攻破定州，擒禿餒、萴剌，皆送京師。','主皆赵所擒与新分记萴剌王擒有差，并列保留不回写已发布俘获事件；主荝剌、新萴剌、旧则剌按同援王都及求归情节识，不与另则骨舍利混同。',source=hemiao,relation='conflicts')
claim('person',people['荝剌'],'name','新契丹附录记俘将萴剌获赐姓名原知感。',12,'萴剌曰原知感，','只是补同人别名，不在932重建赐名事件；萴剌、则剌等字形差留原，舍利为原叙身份不随官名合并其他人。',source=names,relation='adds')
E=ev('khitan_requests_captives','契丹屡遣使请求遣返荝剌与赫邈等俘将',12,'初，','契丹屡遣使请之。',[('荝剌','被请求遣返者'),('惕隐','被请求遣返者')],year=None,when='初，追叙俘获后的屡次求归；各次年份未载',place='契丹至后唐',note='不把初的俘获放到932，也不造不具名每位使臣。')
claim('event',E,'description','新契丹附录记契丹厚币遣使，求归赫邈、萴剌等。',12,'由是卑辭厚幣數遣使聘中國，因求歸赫邈、萴剌等，','新多次请求概述补，不同于新每次斩使叙法自动逐次造事件；确次、确日不明。',source=requests,relation='corroborates')
E=ev('zhao_opposes_captive_return','李嗣源征询群臣，赵德钧等认为放俘将将再生边患',12,'上谋于群臣，','纵之则边患复生。”',[('上','征询意见者'),('德钧','等主张留俘并陈述风险者')],year=None,when='主置初追叙未独年；旧纪列932年四月',place='后唐朝廷',note='数年不犯边及以俘将牵制为赵等判断，不把其因果解释作已证明事实；主初未硬猜年。')
claim('event',E,'time_original','旧明宗纪于长兴三年四月记赵德钧奏请不允遣返。',12,'契丹累遣使求歸則剌、惕隱等，幽州趙德鈞奏請不俞允。','当前求议旧有四月定位，主初追叙未独纪时并列；不将此前俘获追叙一并硬归四月。',source=old,relation='adds')
E=ev('yang_warns_captive_release','李嗣源问杨檀；杨认为荝剌熟悉中国虚实，归后将为深患',12,'上以问冀州刺史杨檀，','恐悔之无及。”',[('上','询问杨者'),('檀','冀州刺史、反对遣归者'),('荝剌','被杨判断放归将再南攻者')],year=None,when='主初追叙未独年；旧纪列932年四月',place='后唐朝廷',note='南向发矢、如丧手足为杨判断，不等放归已射箭，未创实际边战。')
claim('event',E,'description','旧明宗纪记杨檀罢郡至阙后受问，陈述宽赦来援王都者而不宜放还。',12,'會冀州刺史楊檀罷郡至闕，帝問其事，','旧罢郡至阙与主冀州刺史为称衔叙法差，保留，不据主略语自动认仍在郡办公。',source=old,relation='adds')
claim('person',people['杨檀'],'description','杨檀为沙陀人。',12,'檀，沙陀人也。','主明确族属，不按杨姓猜汉族或自动并其他杨檀。')
ev('emperor_stops_captive_return','李嗣源听杨檀意见，停止放归荝剌等的打算',12,'上乃止。','上乃止。',[('上','止拟放俘者'),('荝剌','本次未被放归的求归对象'),('惕隐','同求归对象')],year=None,when='主初追叙未独年；旧纪列932年四月',place='后唐',note='止为本次方案不行；旧既而另遣则骨在主后段待录，不能宣称此后一俘不放。')
ev('emperor_plans_bei_post','李嗣源欲授耶律倍河南藩镇，群臣反对；帝以与其父约为昆弟等理由坚持',13,'上欲授李赞华','其可致乎！”',[('上','拟授藩镇并解释理由者'),('赞华','拟受职的来归者')],year=None,when='四月癸亥任命前的拟议；确年、月日未独载',place='后唐朝廷',note='父约昆弟为帝引述前约，不在932重新造结义；拟议不等当前已授职。')
E=ev('bei_yicheng_appointment','四月癸亥耶律倍任义成节度使，朝廷选朝士为僚属辅之',13,'夏，四月，癸亥，','为选朝士为僚属辅之。',[('赞华','以李赞华名受义成节度使者'),('上','任命及选辅佐者')],when='932年四月癸亥',place='义成军')
claim('event',E,'description','旧明宗纪同癸亥记李赞华由怀化军任滑州节度使。',13,'癸亥，以懷化軍節度使李讚華為滑州節度使。','义成军以滑州为治的军州称法，对应同日同人任命，不建另一次任职；先前李赞华沿耶律倍稳定主体。',source=old,relation='corroborates')
claim('event',E,'description','新契丹附录记长兴三年以赞华为义成军节度使。',13,'三年，以贊華為義成軍節度使。','同前文长兴纪年，新不独载干支。',source=names,relation='corroborates')
ev('bei_does_not_manage_affairs','史书述耶律倍优游自奉、不参与政事，李嗣源嘉之且不问其不法',13,'赞华但优游自奉，','以庄宗后宫夏氏妻之。',[('赞华','被述自奉不豫政者'),('上','被述嘉之且宽容者')],year=None,when='义成受职后概述；确年及各行为日期未独载',place='后唐',note='截句兼含婚事用于明确主语；婚事另录。主不法未具体逐条定罪，不能说每次行为皆已帝批准。')
E=ev('bei_xia_marriage','李嗣源将李存勖后宫夏氏嫁给耶律倍',13,'以庄宗后宫夏氏妻之。','以庄宗后宫夏氏妻之。',[('上','安排婚配者'),('赞华','与夏氏婚配者'),('夏氏','被嫁给耶律倍的庄宗后宫女子')],year=None,when='主受职后概述；辽书置赐名之前；婚年未确',place='后唐',note='夏氏按李存勖后宫识，不擅据辽庄宗后称皇后，也不等刘皇后。主叙职后、辽叙赐名先前位置差留，未硬定932婚日。')
claim('event',E,'description','辽义宗传同记明宗以庄宗后夏氏妻倍。',13,'明宗以莊宗后夏氏妻之，','辽先婚再赐东丹慕华等与主职后叙顺序不同，日期空缺；仅据婚配同主体印证，不据辽后字重写为皇后。',source=liaonames,relation='corroborates')
relationship('夏氏','赞华','妻子',13,'以庄宗后宫夏氏妻之。','夏氏→耶律倍为妻子；关系只指此婚姻阶段，求离婚后仍未据本句明确准奏，不标终身。')
E=ev('bei_abuses_household','通鉴述耶律倍嗜饮人血，虐待姬妾及婢仆',13,'赞华好饮人血，','或刀刲火灼；',[('赞华','被史书记载残酷对待家内女子及仆役者')],year=None,when='传记性素行概述；各次年份未载',place='后唐，具体宅地未载',note='归属通鉴叙述，未据此断现代医学诊断；受害者未名不虚造人物。')
claim('event',E,'description','辽义宗传亦述倍性刻急好杀，婢妾微过常加刲灼。',13,'然性刻急好殺，婢妾微過，常加刲灼。','辽亦归史书品行描述，不独确月日；主另述饮血，而辽本段并未饮血，不混作共同原文。',source=liao,relation='adds')
E=ev('xia_requests_divorce_nun','夏氏不忍耶律倍之残酷，奏请离婚为尼',13,'夏氏不忍其残，',None,[('夏氏','提出离婚及为尼请求者'),('赞华','被夏氏请求离婚的丈夫')],year=None,when='婚后素行概述之末；确年、月日未载',place='后唐',note='奏是请求，未明写准奏或已经削发，不建已离婚完成或出家完成事件。')
claim('event',E,'description','辽义宗传记夏氏惧而求削发为尼。',13,'夏氏懼而求削髮為尼。','辽求与主奏共同支持请求，不能替代批准或已剃发。主不忍与辽惧各述动机，未将两书合成她的原话。',source=liao,relation='corroborates')
E=ev('conghou_zhongshuling','乙丑宋王李从厚加兼中书令',14,'乙丑，',None,[('从厚','宋王、加兼中书令者')],when='932年四月乙丑',place='后唐')
claim('event',E,'description','旧明宗纪同乙丑记天雄军节度使宋王从厚兼中书令。',14,'乙丑，以天雄軍節度使、宋王從厚兼中書令。','天雄军为旧补当前衔；加兼不改既有李从厚主体或套正式主理中书省。',source=old,relation='corroborates')
ev('dong_plans_chengdu_attack','董璋与诸将谋袭成都，诸将皆称必克',15,'东川节度使董璋','皆曰必克；',[('璋','谋袭成都的东川节度使')],place='东川，拟袭成都',note='诸将必克为预测，不等已克成都。')
ev('wang_hui_objects_dong_campaign','前陵州刺史王晖以盛夏出师无名等理由反对袭成都，董璋不从',15,'前陵州刺史王晖','璋不从。',[('王晖','前陵州刺史、反对出师者'),('璋','未采纳反对者')],place='东川',note='剑南万里为王谏辞，不计算辖区面积；必无成功为预测。')
ev('meng_sends_pan_hanzhou','孟知祥闻董欲袭，遣潘仁嗣率三千人赴汉州侦察',15,'孟知祥闻之，','诣汉州诇之。',[('知祥','遣侦军者'),('潘仁嗣','马军都指挥使、率三千赴汉州侦察者')],place='西川至汉州',note='诇是侦察，不把本句当潘已击败董军。')
ev('dong_takes_baiyanglin','董璋入西川境，破白杨林镇、俘戍将武弘礼，孟知祥忧之',15,'璋入境，','知祥忧之。',[('璋','入境破镇并俘将者'),('武弘礼','被俘白杨林戍将'),('知祥','对董声势担忧者')],place='白杨林镇',note='破镇不等已到成都；被俘不等被处死。未核今址不填坐标。')
E=ev('zhao_jiliang_field_strategy','赵季良建议以弱兵诱董、劲兵待之，并劝孟知祥亲出坚定众心',15,'赵季良曰：','以强众心。”',[('季良','提出诱敌野战与主帅亲出建议者'),('知祥','受建议者'),('璋','被分析军心及部署者')],place='西川',note='董无恩士不附为赵判断；始小衄后大捷为预测，不能提前记本段已先败后胜。计划诱兵不是已实施阵型。')
ev('zhao_tingyin_agrees_strategy','赵廷隐赞同季良，判断董璋轻而无谋且将败',15,'赵廷隐以季良言','当为公擒之。”',[('廷隐','赞同且预测可擒董者'),('季良','获赞同的策略提出者'),('璋','被预测将败者')],place='西川',note='预测不当已被孟擒。')
E=ev('zhao_tingyin_appointed_campaign','辛巳孟知祥以赵廷隐为行营马步军都部署，率三万人拒董',15,'辛巳，',None,[('知祥','任命并遣军者'),('廷隐','行营马步军都部署、率三万人拒董者')],when='932年四月辛巳',place='西川拒董前线，具体行程未载',note='受命率拒为当前动作，后日汉州胜败待下一连续段，三万人不把潘三千再另加为33000。')
claim('event',E,'description','新孟世家亦记知祥遣赵廷隐率兵三万拒董。',15,'知祥遣趙廷隱率兵三萬，','新概传把此接董破汉州后、主当前破白杨林后先遣；同三万遣军补证，保留叙述先后差，不提前下段汉州战果、孟亲将或桥战。',source=meng,relation='adds')

reviews={11:'病问帅、推举、交印训、三月庚戌卒八十一、同幄陆另设警卫、慰劳、袭位改名、仪制税免曹权政择能、旧将争执告谕及外任逐动作分录。旧七月废朝为奏闻不能改卒日；新玉册金印与主去国仪层次异留。钱元瓘沿钱传瓘稳定主体；钱仁俊只从子不补父。陆前击字不造新姓；刘名私用区部件同卷固定文本对照刘仁𣏌，不改成杞，原文保留。末年素行及一日之后具体年未明用null，归临安为条件威辞。',12:'初俘获只补人物识别不重复建过去俘获。荝主新萴旧则及原知感别名按同案识，非则骨舍利。主皆赵擒与新萴由晏球擒并列。屡求未具次年份null；当次群臣、杨谏、帝止主初无独年，旧四月单独补时不倒推俘获年。边患解释与南射是意见预测，不建已行战争；杨罢郡与主官衔称法差留。',13:'拟授意见与四月癸亥授义成分，旧滑州军治称法同任。素行婚配及求离婚未独日期null。辽婚在赐名之前主职后概叙，留相对叙差；夏以庄宗后宫限名，不误作刘皇后或确定皇后。虐待是史述不猜诊断，不造未名受害者；奏与求只请求，不写已离婚已剃发。',14:'四月乙丑从厚加兼中书令，旧补天雄军衔；不当改名或实际主理省政新权。',15:'董谋袭、王反对、潘三千侦、董破白杨林俘武、季良建议、廷赞及辛巳任遣三万分录。预测与战略未提前变成战果，不预录后段汉州交战，也不相加潘军到33000；新孟三万遣军同事补，破汉州后叙与主白杨林后叙位置差保留不引其后已胜。'}
# Minimal archived glyph comparison is auxiliary, not another foundational corpus.
contexts=[]
for f in ['paragraph.html','paragraph.txt','review.json']:
 path=P/'sources/glyph-comparison'/f
 contexts.append(dict(file='glyph-comparison/'+f,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),purpose='刘仁𣏌姓名私用区字形核对；史事引用仍为选定原TXT',url='https://github.com/greed-216/histree/blob/e9aa70e4/'+str(path.relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,16):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=932,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(11,16)],next_paragraph='zztj-v277-y0932-p016',next_volume=277,next_year=932,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷277连续932年第11—15段、原125—129行；吴越钱镠身后继承及施政、求归契丹俘将争议、李赞华授职婚配史述及夏氏求离、从厚加衔、两川开战前侦察与拒敌部署。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,16)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
