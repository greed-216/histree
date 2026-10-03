# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 931, year 932 paragraphs 1–10."""
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
 specs.append((directory.name,directory,'585a188b','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
PREVIOUS=YEAR.parent/'year-0931'
specs += [('tongjian-277-931-october',PREVIOUS/'part-04/sources/library/tongjian-277-931-october','077b3114','司马光等'),('xinwudaishi-064-meng-dong-dissent',PREVIOUS/'part-05/sources/library/xinwudaishi-064-meng-dong-dissent','b9e535ed','欧阳修'),('xinwudaishi-064-meng-campaign',YEAR.parent/'year-0930/part-04/sources/library/xinwudaishi-064-meng-campaign','73f70bd8','欧阳修'),('xinwudaishi-068-baohuang',PREVIOUS/'part-04/sources/library/xinwudaishi-068-baohuang','077b3114','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-931-october','tongjian-277-932-february']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0932-p001-p010',
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
for n in range(1, 11):
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
    ck = f'claim_zztj_277_0932_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'知祥':'孟知祥','璋':'董璋','季良':'赵季良','昊':'李昊','福庆长公主':'琼华长公主','知诰':'李昪','延钧':'王延钧','彦稠':'药彦稠'}
NEW_ALIASES={'高彦俦':['高彥儔'],'陈觉':['陳覺']}

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
    if when is None:when='932年'+('正月' if n<=3 else '二月' if n<=8 else '三月' if n==10 else '二月至三月本段')+'；确日未独载'
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
# Consecutive ten paragraphs with independently located supplements.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
jan='jiuwudaishi-043-932-january';feb='jiuwudaishi-043-932-february';dx='jiuwudaishi-043-932-dangxiang';pr='jiuwudaishi-043-932-princess-report';gao='xinwudaishi-069-932-gao-title';meng='xinwudaishi-064-meng-dong-dissent';princess='xinwudaishi-064-meng-campaign';minbook='xinwudaishi-068-baohuang'
ev('fan_requests_dangxiang_campaign','范延光称灵州至方渠间使臣及入贡者多遭党项掠夺，请发兵',1,'春，正月，','请发兵击之。”',[('范延光','枢密使、以道路遭掠请兵者')],place='灵州至邠州方渠镇',note='多为所掠是范奏述，不猜各使团人数；请兵与帝遣兵分别。')
E=ev('yao_kang_sent_dangxiang','朝廷遣药彦稠、康福率步骑七千讨党项',1,'己丑，',None,[('彦稠','静难节度使、受遣率军者'),('康福','前朔方节度使、受遣率军者')],when='932年正月己丑',place='后唐至党项活动地',note='七千是合军数，不两将各七千；受遣不等已破十九族。')
claim('event',E,'description','旧明宗纪同己丑记药彦稠、康福率步骑七千往方渠讨党项。',1,'己丑，遣邠州節度使藥彥稠、靈武節度使康福率步騎七千往方渠討党項之叛者。','旧邠州与主静难为军治所称法；康旧灵武衔与主前朔方叙法保留，未据旧省前字回写现任身份。叛者为朝廷书法，七千合数。',source=jan,relation='corroborates')
E=ev('fuqing_princess_dies','孟知祥妻福庆长公主卒',2,'乙未，',None,[('福庆长公主','去世的孟知祥妻'),('知祥','丧妻的西川节度使')],when='932年正月乙未',place='西川，卒地未独载',note='福庆沿927已建琼华长公主主体，旧新改封核对同人，不重造福庆人物。')
claim('person',people['琼华长公主'],'name','新孟世家记明宗改封琼华公主为福庆长公主。',2,'明宗改封瓊華公主為福慶長公主，','同孟妻及新明载改封，沿原琼华key与UUID；仅补识别名号，不在932再建一次改封事件。',source=princess,relation='adds')
claim('event',E,'time_original','旧明宗纪九月载孟知祥奏福庆长公主今年正月十二日薨；主记正月乙未。',2,'奏福慶長公主以今年正月十二日薨。','九月为报告时，不将死亡改为九月。主干支与旧月日字面差并列，未校纸本或强换算合历，不静改任何摘录。',source=pr,relation='conflicts')
relationship('福庆长公主','知祥','妻子',2,'孟知祥妻福庆长公主卒。','琼华（今福庆）→孟知祥妻子，复用927同关系端点和方向，不反向另建。')
ev('dong_blocks_mianzhou_route','董璋封塞绵州道路，不准孟知祥遣使入朝谢',3,'孟知祥以朝廷','不听遣使入谢，',[('知祥','欲入谢而受阻者'),('璋','塞路不许遣使者')],place='绵州路',note='塞路是当前阻使，不依据此一句建立地理疆界或攻占新州。')
ev('meng_zhao_consider_xiajiang_memorial','孟知祥与赵季良等商议，拟自峡江遣使上表',3,'与节度副使','自峡江上表，',[('知祥','与僚佐议改道遣使者'),('季良','节度副使、参与谋议者')],place='西川，拟经峡江',note='欲发使为方案，不能录为已从峡江绕过东川到京。等未名参与者不扩名单。')
ev('lihao_warns_unilateral_envoy','李昊认为不与东川共议而独遣使，将使己方担负违约之责',3,'掌书记李昊曰：','负约之责在我矣。”',[('昊','掌书记、反对独遣使者'),('知祥','受劝者')],place='西川',note='异日责在我是李昊风险判断，不当孟已经被法院判定违约。')
negotiation=ev('meng_sends_envoy_again','孟知祥再遣使与董璋商议，董璋不从',3,'乃复遣使',None,[('知祥','再遣协商者'),('璋','拒协商者')],place='西川至东川',note='复为前931邀同谢后持续交涉，本次再遣；后段三遣是合述，不额外造本年另外三次。')
ev('zhao_proposes_bizhou_attack','赵季良与诸将议遣高彦俦攻壁州，以阻山南兵转入山后诸州',4,'二月，','入山后诸州者；',[('季良','参与提议攻壁州者'),('高彦俦','太原人、昭武都监、拟领兵者')],place='拟攻壁州',note='议遣是提议而未执行，高彦俦拟领兵不等本句已经出军；太原为籍贯，不是拟攻击地。')
claim('person',people['高彦俦'],'description','高彦俦为太原人，此时昭武都监。',4,'昭武都监太原高彦俦','籍贯与职务均当前主句明确，高不混高从诲、各朝同高姓将。')
ev('lihao_objects_bizhou_campaign','李昊以尚未向朝廷谢罪及家属坟墓风险劝阻进攻壁州',4,'孟知祥谋于僚佐，','安用壁州乎！”',[('知祥','征询攻壁方案者'),('昊','以朝廷与家属风险反对者'),('苏愿','被提及朝廷已遣返的进奏官')],place='西川',note='不若直取梁洋为条件警告和反问，不另录李昊正式建议已攻梁洋；风险为其论据，不当朝廷已经毁坟杀亲。')
ev('meng_stops_bizhou_plan','孟知祥停止攻壁州计划，赵季良由此厌恶李昊',4,'知祥乃止。',None,[('知祥','止拟议攻壁者'),('季良','因阻议而恶李昊者'),('昊','被赵厌恶者')],place='西川',note='止是计划未行，不造先取壁州再撤军；恶为本次分歧史述，不造双方永久仇敌关系边。')
E=ev('orders_nine_classics_print','朝廷初令国子监校定九经，雕印出售',5,'辛未，',None,[],when='932年二月辛未',place='后唐国子监',note='此为开始下令校刻，不等本日全九经印版已完成或已卖遍全国。')
claim('event',E,'description','旧纪同辛未记中书请依石经文字刻九经印板，获准。',5,'辛未，中書奏：「請依石經文字刻《九經》印板。」從之。','仅引旧纪正文；后夹注引五代会要、953板成等留作快照背景不作本批新增事件，未提前953成果。',source=feb,relation='adds')
E=ev('yao_reports_dangxiang_captures','药彦稠等奏报破党项十九族、俘二千七百人',6,'药彦稠',None,[('彦稠','奏报军功者'),('康福','同正月受遣讨党项的将领')],place='党项活动地，奏闻后唐',note='战果数按奏报归属；等以同役正月明名识康福，未为所有族逐人造主体。奏日与各族攻破具体日未载。')
claim('event',E,'description','旧纪另载药彦稠奏诛阿埋等十族，与康福入白鱼谷追袭，获首领六人、诸羌二千余人及牲畜数千。',6,'藥彥稠奏，誅党項阿埋等十族，與康福入白魚穀追襲叛黨，獲大首領六人、諸羌二千餘人、孳畜數千，','主十九族二千七百与旧十族及二千余统计不一致，阶段范围未独解释，不强判完全同一次统计，也不相加成二十九族或四千余。白鱼谷为旧追袭地，不伪装主原载地点。',source=dx,relation='conflicts')
E=ev('gao_conghui_bohai_king','高从诲获赐勃海王爵',7,'赐高从诲',None,[('高从诲','受勃海王爵的荆南节度使')],place='荆南',note='勃海为封爵，不等获得北方渤海国疆域或迁镇；主未独日，承二月不套上辛未。')
claim('event',E,'description','新南平世家记长兴三年封高从诲渤海王。',7,'三年，封從誨渤海王。','三年承长兴；主勃海与新渤海字形称法并列，王爵与实际辖地分。后应顺南平王不提前。',source=gao,relation='corroborates')
ev('xu_builds_lixian_library','徐知诰在府舍建礼贤院，聚图书、延请士大夫',8,'吴徐知诰','延士大夫，',[('知诰','建院聚书招士者')],place='吴府舍',note='原仅府舍，不指定现代遗址或精确坐标。礼贤院与新书他时延宾亭不是凭功能相同自动认同建筑，不强套补证。')
ev('xu_discusses_sun_chen','徐知诰与孙晟、海陵陈觉谈议时事',8,'与孙晟',None,[('知诰','谈议时事的吴辅政者'),('孙晟','参与谈议者'),('陈觉','海陵人、参与谈议者')],place='吴府舍',note='同座谈议不造结盟或君臣正式任命，孙晟沿既有孙凤孙忌主体；陈觉不混陈皋。')
claim('person',people['陈觉'],'description','陈觉为海陵人，参与徐知诰府舍时事谈议。',8,'海陵陈觉谈议时事。','身份按本句，后南唐官职未提前赋在932。')
used.setdefault(9,[]).append(negotiation)
claim('event',negotiation,'description','主书合述孟知祥三遣使说董璋，警告不奉表谢罪恐再受讨，董不从。',9,'孟知祥三遣使说董璋，以主上加礼于两川，苟不奉表谢罪，恐复致讨；璋不从。','连续交涉合述附于本批再遣事件，不把三遣解释成前再遣之后额外三次；恐讨是孟的风险劝说，朝廷未本句已再伐。')
E=ev('meng_sends_lihao_zi','孟知祥遣李昊赴梓州，极论利害；董璋诟怒拒绝',9,'三月，辛丑，','诟怒，不许。',[('知祥','派李昊劝董者'),('昊','奉遣至梓州论利害者'),('璋','见李而怒拒者')],when='932年三月辛丑派遣；见面确日未独载',place='西川至梓州',note='辛丑为遣日，行程到见未独日，不能硬标往返同一天。')
claim('event',E,'description','新孟世家亦记三遣使不获允，派观察判官李昊说董，董疑孟卖己而怒侵昊。',9,'知祥三遣使往見璋，璋不聽，乃遣觀察判官李昊說璋，璋益疑知祥賣己，因發怒，以語侵昊。','主掌书记与新观察判官各载衔保留，使命同。疑卖己为董判断，不把孟真的出卖或后来两川开战提前。',source=meng,relation='adds')
ev('lihao_reports_dong_threat','李昊返报孟知祥，称董璋不通谋议且欲窥西川，劝作准备',9,'昊还，',None,[('昊','返报及建议戒备者'),('知祥','受报者'),('璋','被判断有窥西川之志者')],place='西川',note='窥志是李昊当时判断，非本句董已经率军袭成都；新后汉州战待连续主段。')
E=ev('yanjun_resumes_position','闽王延钧复位',10,'甲辰，',None,[('延钧','931避位受箓后复位者')],when='932年三月甲辰',place='闽',note='复位与931丙子暂令子权府分，尚未933帝号或更名璘，不提前录。')
claim('event',E,'description','新闽世家记王暂避位后复位。',10,'既而復位，','新相对次序补，不单凭既而推甲辰；日期依据主，后问六十年及称帝未提前。',source=minbook,relation='corroborates')
reviews={1:'范道路遇掠奏请与己丑二将七千合军遣分，不各七千。旧方渠地补，康主前朔方旧灵武衔差留；叛者是朝廷书法不造现代民族战争。',2:'福庆与927琼华新明载改封同孟妻，沿旧key和妻关系；主乙未与旧九月奏今年正月十二日差保留，九月仅报告不移卒月，纸本未核。',3:'董塞绵路、孟赵拟峡江上表、李昊违约风险警告、复遣董不从分。方案未执行不生成经峡江到京；违约为预测不是法判。',4:'赵诸将议高攻壁未行，高昭武都监太原籍直接记，新人不混高从诲。李反问直取梁洋为警告不立已攻；孟止后赵恶为此时分歧，不建永久仇边。',5:'二月辛未国子监九经校印售下令，不提前板成。旧正文石经文字刻从补；夹注引后书及953板成非本批录入。',6:'药等奏十九族二千七百；旧阿埋十族白鱼谷、首领六二千余人统计不同，未知阶段口径不相加或改数。数字为奏报，奏日非每战确日。',7:'高勃海爵旧新渤字差同爵，非渤海国疆域，不套邻辛未确日或提前934南平王。',8:'徐礼贤院聚书延士与孙陈谈议分，地点原府舍未硬核今遗址；新延宾亭不同年层次不套为同建筑。孙既有孙凤孙忌同人、陈海陵主明确，后南唐官不提前，同谈不立盟友边。',9:'三遣为连续谈判合述附本批再遣，不多造三次。三月辛丑遣李、董见怒拒、李还风险报告分，见面往返未硬同日。新观察判官主掌书记留；疑卖己及窥西川为各人判断，新汉州战后主待录。',10:'三月甲辰王复位同去年避位衔接，新既而补相对顺序不独定日；未提前933称帝更名。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=932,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v277-y0932-p011',next_volume=277,next_year=932,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续932年第1—10段、原115—124行；党项奏请遣及战果、孟妻卒、两川交涉壁州计划未行、九经印令、高受爵、吴礼贤院谈议、李昊使梓及闽复位。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
