# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 49–54."""
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
 ('tongjian-275-926-chancellors-and-khitan',YEAR/'part-05/sources/library/tongjian-275-926-chancellors-and-khitan','f5afcc0c','司马光等'),
 ('jiuwudaishi-036-926-an-declines',YEAR/'part-04/sources/library/jiuwudaishi-036-926-an-declines','e466a47f','薛居正等'),
 ('xinwudaishi-006-926-may-offices',YEAR/'part-03/sources/library/xinwudaishi-006-926-may-offices','5c38857d','欧阳修'),
 ('jiuwudaishi-037-926-wanggongyan',P/'sources/library/jiuwudaishi-037-926-wanggongyan','0da9df19','薛居正等'),
 ('jiuwudaishi-037-926-border-defence',P/'sources/library/jiuwudaishi-037-926-border-defence','0da9df19','薛居正等'),
 ('jiuwudaishi-037-926-chu-offices',P/'sources/library/jiuwudaishi-037-926-chu-offices','0da9df19','薛居正等'),
 ('jiuwudaishi-098-zhaoyanshou',P/'sources/library/jiuwudaishi-098-zhaoyanshou','0da9df19','薛居正等'),
 ('songshi-262-ligu-hanxizai',P/'sources/library/songshi-262-ligu-hanxizai','0da9df19','脱脱等'),
 ('xinwudaishi-026-fuxi-wanggongyan',P/'sources/library/xinwudaishi-026-fuxi-wanggongyan','0da9df19','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-926-chancellors-and-khitan']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p049-p054',
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
for n in range(49, 55):
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
    ck = f'claim_zztj_275_0926_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','殷':'马殷','习':'符习','公俨':'王公俨','彦威':'霍彦威','李绍斌':'赵德钧','德钧':'赵德钧','延寿':'赵延寿','熙载':'韩熙载','谷':'李谷'}
NEW_ALIASES={'韩叔嗣':['韓叔嗣'],'韩熙载':['韓熙載','熙载'],'李谷':['李穀'],'赵延寿':['趙延壽','延寿'],'兴平公主':['興平公主'],'刘邟':['劉邟','刘邧','劉邧']}
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
# 连续正文，不按人物挑段；军额各项目分别列证。
E=ev('chongtao_old_shu_cavalry_units','追叙郭崇韬将蜀骑兵编为左右骁卫等六营，共三千人',49,'初，郭崇韬','凡三千人；',[('郭崇韬','蜀骑兵编营者')],year=None,when='926年八月庚寅条追叙此前；具体编营日未载',place='蜀地',note='初明确追叙，此处未具郭编营确年，不直接填926；也不是本日新增三千骑兵。')
E=ev('chongtao_old_shu_infantry_units','追叙郭崇韬将蜀步兵编为左右宁远等二十营，共二万四千人',49,'步兵分','凡二万四千人。',[('郭崇韬','蜀步兵编营者')],year=None,when='926年八月庚寅条追叙此前；具体编营日未载',place='蜀地',note='句主承郭崇韬，旧步军与新增兵区分，不能据此强定全蜀即时总兵额。')
E=ev('meng_chongshan_six_units','孟知祥增置左右冲山等六营、六千人，驻罗城内外',49,'庚寅','营于罗城内外；',[('孟知祥','新增军营者')],when='926年八月庚寅',place='成都罗城内外',note='罗城与前批牙城不同，六营六千只本项目，不将前批十六牙兵营重复相加。')
E=ev('meng_yining_twenty_units','孟知祥置义宁等二十营、一万六千人，分戍州县就食',49,'又置义宁','分戍管内州县就食；',[('孟知祥','置军并安排分戍就食者')],when='926年八月庚寅条，具体另日未载',place='西川管内州县',note='义宁二十营与宁远旧二十营是不同项目，不能混为同一部队或用就食推出精确粮额。')
E=ev('meng_laocheng_four_units','孟知祥置左右牢城四营、四千人，分戍成都境内',49,'又置左、右牢城',None,[('孟知祥','新增牢城军营者')],when='926年八月庚寅条，具体另日未载',place='成都境内',note='只保留本项四营四千，不在来源未给总数时计算全蜀军力，也不推人员来源。')
E=ev('wang_prior_kills_yang_recalled','追叙王公俨已杀杨希望',50,'王公俨','既杀杨希望，',[('王公俨','杀杨希望者'),('杨希望','被杀监军')],when='926年八月条追叙此前青州事，沿用已发布原事件',place='青州',note='与卷274本年春已录同一件事，复用原事件和参与key，不新增重复杀人事件。',stable_key='event_zztj_274_0926_wanggongyan_kills_yangxiwang')
claim('event',E,'description','旧史记王公俨乘杨希望分兵后无备，围其第、擒杀之。',50,'公儼乘其無備，圍希望之第，擒而殺之。','只取旧正文，不将后夹注引通鉴当独立补证。',source='jiuwudaishi-037-926-wanggongyan',relation='adds')
E=ev('wang_blocks_fuxi_return','王公俨声称军府不愿符习返回，并拒绝到齐州的符习，符习仍继续前行',50,'欲邀节钺','习不改前。',[('王公俨','谋求节度、宣称军情并拒符者'),('符习','试图返镇、继续前进者')],when='926年王公俨之官前，具体日未载',place='青州军府及齐州',note='不愿符还为王扬言，不据此证全军民真实一致意愿；不改前为仍前行，未说已入青州城。')
E=ev('wang_petitions_for_command_gets_deng','王公俨令将士上表请其为帅，朝廷授其登州刺史',50,'公俨又令','诏除登州剌史。',[('王公俨','令部属请帅、获授登州刺史者'),('帝','授刺史者')],when='926年八月乙未赴任前，授官确日未载',place='青州军府、后唐朝廷及登州任职',note='请帅与实际获授刺史不同，不能写已授平卢节度；剌疑刺原字留。')
claim('event',E,'description','新符习传亦载公俨求节度使而获拜登州刺史。',50,'因自求為節度使。明宗乃以房知溫代習鎮平盧，[1]拜公儼登州刺史。','此传房知温代习与主及新明宗纪霍彦威不合，保留异说，不能用传叙覆盖实际主事件任命者。',source='xinwudaishi-026-fuxi-wanggongyan',relation='conflicts')
E=ev('huo_transferred_pinglu_assembles_zi','王公俨迟赴任、称军情留他，李嗣源调霍彦威为平卢节度使并聚兵淄州图攻取',50,'公俨不时','以图攻取，',[('王公俨','迟赴任及托称军情者'),('帝','调任并处置者'),('霍彦威','天平节度使移平卢、聚兵者')],when='926年八月乙未前',place='天平、平卢及淄州',note='图攻取是备战意图不认已经攻陷青州；新符传房知温异说另引，旧明宗正文同霍。')
claim('event',E,'description','旧明宗纪记霍彦威代符习，聚兵淄州图进取。',50,'公儼不時赴任，即以霍彥威代符習，聚兵淄州，以圖進取。','正文独立补证，不引用夹注通鉴作第二独立来源。',source='jiuwudaishi-037-926-wanggongyan',relation='corroborates')
E=ev('wang_goes_dengzhou_after_fear','王公俨惧霍彦威兵势，开始赴登州任',50,'公俨惧','始之官。',[('王公俨','赴登州任者')],when='926年八月乙未',place='青州至登州',note='始之官为开始赴任，未推乙未已抵登州；恐惧动机为本书叙述。')
claim('event',E,'description','旧明宗纪记诏使到青州告谕，王公俨即赴所任。',50,'彥威至淄州，會詔使至青州告諭，公儼即赴所任。','旧补告谕环节；不把未名诏使新增人物。',source='jiuwudaishi-037-926-wanggongyan',relation='adds')
E=ev('huo_executes_wang_clan_party','霍彦威至青州后追擒王公俨，斩其族党，北海支使韩叔嗣也在其中',50,'丁酉','韩叔嗣预焉。',[('霍彦威','追擒处斩者'),('王公俨','被捕杀者'),('韩叔嗣','被杀支使')],when='926年八月丁酉据主书；新明宗纪作丁未',place='青州；旧补北海县捕、州东处斩',note='主族党悉斩范围及人口未具，旧具同谋将校八人不同口径不合死亡总数。预焉依前斩句指韩叔嗣在被斩者之列，不推其具体参与谋乱动作。')
claim('person',people['王公俨'],'death_year','王公俨于926年被霍彦威处斩。',50,'丁酉，彦威至青州，追擒之，并其族党悉斩之，','此处追擒并斩主语对象王；死亡记实际行为不以拒命意图推死。')
claim('person',people['韩叔嗣'],'death_year','韩叔嗣于926年王公俨族党被斩时也被杀。',50,'并其族党悉斩之，支使北海韩叔嗣预焉。','预焉承斩事，未具另日。')
claim('event',E,'description','旧纪记霍彦威奏已斩王公俨及同谋指挥使李谨、王居厚等八人，又记北海县捕获、州东处斩。',50,'新授青州節度使霍彥威奏，處斬新登州刺史王公儼，及同謀拒命指揮使李謹、王居厚等八人訖。','只作奏报补证，八人究竟含王或仅同谋口径不强断；李谨等只在补证名单未另设主线实体。',source='jiuwudaishi-037-926-wanggongyan',relation='adds')
claim('event',E,'location_name','旧明宗纪记公俨被擒于北海县、与同党斩于州东。',50,'遣人擒公儼於北海縣，與同黨斬於州東。','不补现代坐标，旧所述捕杀地点分开。',source='jiuwudaishi-037-926-wanggongyan',relation='adds')
claim('event',E,'time_original','新明宗纪作丁未霍彦威杀登州刺史王公俨。',50,'丁未，平盧軍節度使霍彥威殺其登州刺史王公儼。','与主丁酉不同干支，保留电子本异文待纸本核，不自行选择一个真日。',source='xinwudaishi-006-926-may-offices',relation='conflicts')
claim('event',E,'description','新符习传称房知温擒杀王公俨。',50,'公儼不時承命，知溫擒而殺之。','传中知温与两书帝纪及主霍彦威矛盾，作为书证异说，不新建另一次杀公俨。',source='xinwudaishi-026-fuxi-wanggongyan',relation='conflicts')
E=ev('hanxizai_plans_wu_ligu_farewell','韩熙载将奔吴，密告李谷；李谷送至正阳，与他痛饮告别',50,'其子熙载','痛饮而别。',[('韩熙载','韩叔嗣之子、拟奔吴者'),('李谷','汝阴进士、送别友人')],when='926年八月韩叔嗣被杀条之后，具体日未载',place='正阳送别地',note='将奔是准备，送至正阳不等已抵吴都或已被任官；吴指当时吴政权，不提前叫南唐。')
relationship('韩叔嗣','韩熙载','父亲',50,'支使北海韩叔嗣预焉。其子熙载将奔吴，','其子承韩叔嗣，韩叔嗣是韩熙载父亲，方向由父至子。')
relationship('韩熙载','李谷','朋友',50,'其子熙载将奔吴，密告其友汝阴进士李谷，','主明确友但无长幼或结义，不造哥哥弟弟、盟友、师生边；仅一条朋友关系，不反向复制。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','宋李谷传称李谷与韩熙载交好。',50,'與韓熙載善，','同李谷韩熙载南渡对话校同人，书源独立；后果如其言是后世评价，不提前录本年征服江南。',source='songshi-262-ligu-hanxizai',relation='corroborates')
E=ev('han_ligu_conditional_speech','韩熙载与李谷送别时各称若被用为相，将平定对方地区',50,'熙载谓谷曰',None,[('韩熙载','提出若在吴为相则定中原者'),('李谷','回应若在中原为相则取吴者')],when='926年八月条送别时，确日未载',place='正阳',note='若当条件句为志向谈话，不写本年任宰相或已出兵平定；笑与夸喻保留话语性质。')
claim('event',E,'description','宋李谷传保存江东相我定中原、中原相我取江南的同类对话。',50,'熙載將南渡，密告穀曰：“若江東相我，我當長驅以定中原。”穀笑曰：“若中原相我，下江南探囊中物耳。”','宋叙密告与主送别场景关系各存，江南用语不替主吴政权；未引谷后果如其言作926成果。',source='songshi-262-ligu-hanxizai',relation='corroborates')
E=ev('youzhou_border_report_anshentong_order','幽州奏报契丹寇边，李嗣源命安审通率兵抵御',51,'庚子',None,[('帝','御边发令者'),('安审通','齐州防御使、受命率军者')],when='926年八月庚子据主书；旧纪置于己亥条下',place='幽州边境及齐州军出动',note='奏报与调兵，未具交战结果或契丹将名；不据命令推已胜敌。')
claim('event',E,'description','旧明宗纪也记幽州奏契丹寇边，诏齐州防御使安审通率师。',51,'幽州奏，契丹寇邊，詔齊州防禦使安審通率師禦之。','旧此事接己亥朝会条，未独立列日；主庚子与段序不一致，记异而不定旧必己亥。',source='jiuwudaishi-037-926-border-defence',relation='corroborates')
E=ev('meng_flying_boat_water_training','孟知祥置左右飞棹兵六营、六千人，分戍滨江诸州并习水战防备夔峡',52,'九月',None,[('孟知祥','置水军及训练部署者')],when='926年九月壬戌',place='西川滨江诸州；防备方向夔州、峡州',note='习战以备是部署和训练，未实际攻夔峡，不将六千与旧步骑等简单相加全蜀总兵力。')
E=ev('zhaodejun_restores_name','卢龙节度使李绍斌获准复姓赵，并赐名德钧',53,'癸酉','仍赐名德钧。',[('李绍斌','请复姓、获赐名者'),('帝','准姓赐名者')],when='926年九月癸酉据主书；旧纪五月甲申',place='幽州卢龙及后唐朝廷',note='复用既有赵德钧及李绍斌别名，不另建人；命名日与加衔旧差异各引。')
claim('event',E,'time_original','旧明宗纪五月甲申记李绍斌加检校太傅同平章事、复姓名赵德钧。',53,'甲申，幽州節度使、檢校太保李紹斌加檢校太傅、同平章事，復姓名為趙德鈞。','旧此快照五月背景、主九月癸酉不同，不能默认为两次复姓或只改干支字形。',source='jiuwudaishi-036-926-an-declines',relation='conflicts')
E=ev('zhaoyanshou_marriage_background','追叙赵德钧养子赵延寿娶李嗣源之女兴平公主，史书以此解释德钧受亲任',53,'德钧养子','故德钧成蒙亲任。',[('德钧','赵延寿养父、书称受亲任者'),('延寿','公主丈夫'),('兴平公主','李嗣源之女、赵延寿妻子'),('帝','公主父亲')],year=None,when='926年九月改名条背景追叙，婚姻确年未载',place='后唐婚姻及朝廷背景',note='婚年未具不强填926。成蒙疑承蒙底本原字留；亲任因果为史作者解释，不推出每项官职都只凭婚姻。')
claim('person',people['赵延寿'],'description','旧史记赵延寿本姓刘，父邧为蓚令，后由赵德钧收养，及长尚明宗女兴平公主。',53,'延壽，本姓劉氏。父曰邧，常山人也，嘗任蓚令。','与主刘邟同父同蓚令及下同收养婚姻校同人，邟/邧姓名异字并存，未知原名不填刘延寿。',source='jiuwudaishi-098-zhaoyanshou',relation='adds')
relationship('赵德钧','赵延寿','养父',53,'德钧养子延寿尚帝女兴平公主，','德钧是延寿养父，养父与生父分别，不生成逆向冗余边。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','旧赵延寿传记德钧获延寿及其母种氏后养之为子。',53,'時德鈞為偏將，獲延壽並其母種氏，遂養之為子。','旧本传收养确证；获其母不等已娶其母，不据此新增婚姻关系。',source='jiuwudaishi-098-zhaoyanshou',relation='corroborates')
relationship('李嗣源','兴平公主','父亲',53,'延寿尚帝女兴平公主，','帝为此年明宗李嗣源，帝女明确生父关系，不推母亲名。')
relationship('兴平公主','赵延寿','妻子',53,'延寿尚帝女兴平公主，','尚公主明确婚姻，公主是延寿妻子，仅建此方向，不另建丈夫逆边。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','旧史亦记延寿及长尚明宗女兴平公主。',53,'及長，尚明宗女興平公主。','婚年本传未具，故不自动视作926新婚。',source='jiuwudaishi-098-zhaoyanshou',relation='corroborates')
relationship('刘邟','赵延寿','父亲',53,'延寿本蓚令刘邟之子也。','刘邟生父、赵德钧养父各存；旧刘父邧同职同子同事校同人，别名保留而原引不改。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','旧史称赵延寿本姓刘，父邧、常山人、曾任蓚令。',53,'延壽，本姓劉氏。父曰邧，常山人也，嘗任蓚令。','生父身份补证，邟邧异字有同人完整事件链支持，并非单凭繁简转换合并；不新增父早年事件。',source='jiuwudaishi-098-zhaoyanshou',relation='corroborates')
E=ev('mayin_granted_shangshuling','楚王马殷加守尚书令',54,'加楚王',None,[('殷','获加守尚书令者'),('帝','加衔者')],when='926年九月条未具日；旧记癸酉',place='楚国及后唐朝廷',note='守尚书令为加官衔，未推实到洛阳主持尚书省。')
claim('event',E,'description','旧明宗纪癸酉记楚王马殷加检校太师、守尚书令。',54,'癸酉，天策上將軍、湖南節度使、開府儀同三司、守太師、兼尚書令、楚王馬殷加檢校太師、守尚書令。','旧具体列旧衔及新增衔，主只守尚书令；不把同日附近钱氏加封混入马殷。',source='jiuwudaishi-037-926-chu-offices',relation='adds')

review='连续49—54段逐句校核。郭旧骑六营三千/步二十营二万四千是初追叙，确年不明置null；孟庚寅新增冲山六营六千、义宁二十营一万六千、牢城四营四千与九月壬戌飞棹六营六千逐项分录，牙城罗城及州县不同，未求全蜀瞬时总兵额。王杀杨复用274已录事件和参与；王扬言军情非真实全民意愿、欲帅而授登刺、迟任托辞、霍聚兵图取非已攻克。旧正文霍任擒杀与新符传房知温矛盾各存；主王之官乙未、杀丁酉，新纪丁未日异不改；族党及旧同谋八人未合死亡总数，旧夹注通鉴不算独立确证。韩叔嗣预焉承斩句，韩熙载父明确；将奔吴未证明到国任官；李谷正阳送友及双向若为相话语是志向不提前战争成果，宋后果如其言不纳本年。幽州奏契丹寇及命安审通出兵主庚子/旧附己亥条无独立日，保留异，未造战胜。赵德钧既有李绍斌主体复用，主九月癸酉复姓/旧五月甲申异记不造两次；兴平公主婚与收养背景年月null，明宗父、公主妻、赵养父、刘生父方向明确，旧刘邧/主刘邟同子同职同养婚链校同人非繁简自动合。旧获延寿母种氏不是已娶种氏。成蒙疑承蒙原文留。马殷守尚书令保加衔不推实掌尚书省，旧补检校太师及癸酉。文字展示简体、原文快照原字逐字，电子本纸本异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(49,55):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(49,55)],next_paragraph=Q[55]['id'],next_volume=275,supplements=supplements,excluded_non_body=[],coverage='卷275第49—54段，原文件54—59行；蜀旧军及孟新增军、王公俨处置和韩李送别、幽州御边、飞棹军、赵姓名与家属、马殷加衔。926年110正文段累计97，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(49,55)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
