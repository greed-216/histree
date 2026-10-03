# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 11–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 58))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'0f922712','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))

PREV=YEAR/'part-01'
specs += [(key,PREV/'sources/library'/key,'871075e5',author) for key,author in [('tongjian-278-933-january-april','司马光等'),('jiuwudaishi-044-933-april','薛居正等')]]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-january-april','tongjian-278-933-may-july']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0933-p011-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书姓名校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(11, 21):
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
        # Preserve published payload for hash reproducibility; corrected live citation is in revisions/2026-10-04-933-era-citation. Future 933 batches must use 长兴四年.
        citation = f'卷278·长兴三年（933）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0933_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','从荣':'李从荣','瓚':'刘赞（秦王傅）','刘瓚':'刘赞（秦王傅）','刘瓒':'刘赞（秦王傅）','从珂':'李从珂','从益':'李从益','从温':'李从温','从璋':'李从璋','从敏':'李从敏','彝超':'李彝超','从进':'安从进','徐知诰':'李昪','知诰':'李昪','吴主':'杨溥','璘':'王延钧','闽主':'王延钧','继鹏':'王继鹏','审知':'王审知','钱元瓘':'钱传瓘','钱元璙':'钱传璙','元瓘':'钱传瓘','元璙':'钱传璙','阿啰王':'阿啰王（李彝超兄）'}
NEW_ALIASES={'刘赞（秦王傅）':['刘瓒（秦王傅）','劉讚（秦王傅）','劉贊（秦王傅）'],'王居敏':[],'鱼崇远':['魚崇遠'],'阿啰王（李彝超兄）':['阿啰王','阿囉王','阿罗王'],'李从益':['李從益'],'宋温':['宋溫']}

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

def event(code, title, n, quote, actors, when=None, note='', year=933, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='933年四月承前本段；确日未独载' if n<=12 else '933年五月承前本段；确日未独载' if n<=16 else '933年本段；确月日未独载' if n==17 else '933年七月承前本段；确日未独载'
    key = 'event_zztj_278_0933_' + code
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
        edge = 'participation_zztj_278_0933_' + code + '_' + pk
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
    corrections={}
    import uuid
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
    people_ids={str(uuid.uuid5(namespace,x['key'])):x['key'] for x in registry.values()}
    for revision in sorted((ROOT/'content/revisions').glob('*/relations.json')):
        if not (revision.parent/'publication.json').exists():continue
        for revision_row in json.loads(revision.read_text()).get('relations',[]):corrections[revision_row['key']]=revision_row['after']
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if x['key'] in corrections:
                c=corrections[x['key']];x=dict(x,person_a_key=people_ids[c['person_a']],person_b_key=people_ids[c['person_b']],relation_type=c['relation_type'])
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_278_0933_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive ten body paragraphs in the next volume of the same year.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
apr='jiuwudaishi-044-933-april';oldid='jiuwudaishi-068-liuzan-identity';oldtutor='jiuwudaishi-068-liuzan-tutor';newid='xinwudaishi-028-liuzan-identity';newtutor='xinwudaishi-028-liuzan-tutor';newex='xinwudaishi-028-liuzan-exclusion';princes='xinwudaishi-006-933-princes';may='jiuwudaishi-044-933-may';july='jiuwudaishi-044-933-july';oldsiege='jiuwudaishi-132-summer-siege';newsiege='xinwudaishi-040-yichao-siege';wu='xinwudaishi-061-taihe-jinling';qian='tongjian-278-933-qian-yuanliao-collation'
ev('prince_tutors_requested','言事者请置亲王师傅，宰相畏从荣而请其自行选择',11,'言事者请','请令王自择。',[('从荣','获准自择师傅的秦王')],place='后唐朝廷、秦王府',note='言事者及宰相本句未名，不凭官职套为冯道或李愚；畏是史叙，不推皆永久臣服。')
ev('wang_jumin_recommends_liuzan','王居敏荐刘赞为师傅，李从荣表请任用',11,'秦王府判官','从荣表请之。',[('王居敏','秦王府判官、太子詹事、荐人者'),('瓚','兵部侍郎、被荐者'),('从荣','表请所荐师傅者')],place='秦王府、后唐朝廷',note='主名瓚，旧讚新贊同秦王傅识同人；与已录923嘉州司马刘赞未有同人证据，限定刘赞（秦王傅）新主体，勿凭简体同名合并。')
E=ev('liuzan_qin_tutor','四月癸丑刘赞任秘书监、秦王傅',11,'癸丑，','秦王傅，',[('上','授官者'),('瓚','受秘书监兼王傅者')],when='933年四月癸丑',place='秦王府',note='主前兵部、旧刑部侍郎不同衔保留；不是王傅任于秦王后自称，授官与前表请求分。')
claim('event',E,'description','旧明宗纪同癸丑记刑部侍郎刘讚任秘书监、秦王傅。',11,'癸丑，以刑部侍郎劉讚為秘書監、秦王傅。','主前兵部与旧刑部异衔并列，源名瓚/讚不是自动繁简同字，通过职务同日同受任识别。',source=apr,relation='corroborates')
claim('person',people['刘赞（秦王傅）'],'description','旧传称秦王傅刘赞为魏州人。',11,'劉讚，魏州人也。','旧卷68履历与当前王傅相接，区别先前嘉州司马同名；父比及新玭异字暂不新增父亲主体，未核生日。',source=oldid,relation='adds')
claim('person',people['刘赞（秦王傅）'],'description','新传称刘赞魏州人，明宗时累迁中书舍人、御史中丞、刑部侍郎。',11,'明宗時，累遷中書舍人、御史中丞、刑部侍郎。','新主体承刘贊魏州身份，与旧讚相合；累迁是此前履历，不定每职均在933新授。',source=newid,relation='adds')
relationship('瓚','从荣','王傅',11,'以瓚为秘书监、秦王傅','刘赞（秦王傅）→李从荣王傅，方向为A是B的该身份，正式任自本次；不等二人亲属或从荣已接受全部谏言。')
ev('yu_chongyuan_secretary','四月癸丑鱼崇远任秦王府记室',11,'前襄州支使','为记室。',[('上','授官者'),('鱼崇远','前襄州支使、山阳人、任记室者')],when='933年四月癸丑同段；单独任日未独载',place='秦王府',note='山阳为籍称不推现代县唯一对应，记室不是太子傅。旧纪夹注五代会要不新增，主身份已明。')
E=ev('liuzan_laments_appointment','刘赞自认左迁，哭诉请求免任而未能免',11,'瓚自以左迁，','不得免。',[('瓚','自认左迁、请求免任者')],when='933年四月受王傅命后；确日未独载',place='后唐朝廷、秦王府',note='自以为其认知，不把品秩简单等同升降；不代录胡注对动机的推断。')
claim('event',E,'description','旧刘传记忽闻其命掩泣固辞，未能止任命。',11,'忽聞其命，掩泣固辭，竟不能止。','旧叙辞与主泣诉对应，不把旧夹注恐祸分析当本人口供。',source=oldtutor,relation='corroborates')
claim('event',E,'description','新刘传记受秦王傅命后哭称祸将至。',11,'贊泣曰：「禍將至矣！」','新引语与主自以左迁不同层次并列，担忧不是此时已经被杀或贬岚州。',source=newtutor,relation='adds')
E=ev('liuzan_advises_congrong','秦王府群僚轻脱谄谀，刘赞从容规讽，李从荣不悦',11,'王府参佐','从荣不悦。',[('瓚','独规讽的王傅'),('从荣','对规讽不悦者')],year=None,when='受王傅任后的日常概述；各次年月未独载',place='秦王府',note='轻脱谄谀为史论概述，未名群僚不能给全体已建幕僚贴永久标签。')
claim('event',E,'description','新刘传同记秦王群僚谄谀，刘赞独从容讽谏、引向正道。',11,'獨贊從容諷諫，率以正道。','对应主规讽，未编未见具体一次谏词。',source=newex,relation='corroborates')
E=ev('congrong_restricts_tutor_access','李从荣以僚属待刘赞，后令门者限制其入府，每月仅准一至',11,'瓚虽为傅，',None,[('从荣','不循师礼并限制入府者'),('瓚','受限制、或整日不获召见及饮食者')],year=None,when='任王傅后的持续待遇概述；起止年未独载',place='秦王府',note='主月听一至、新月一至相符；竟日有或字，不推每天断食或监禁。')
claim('event',E,'description','新刘传称秦王令刘赞来不得通，刘赞每月一至府、退而杜门。',11,'後戒左右贊來不得通，贊亦不往，月一至府而已，退則杜門不交人事。','主月听一至强调准入，新月一至及不交强调反应，均保；后秦死、流放、刘卒未来不提前本段。',source=newex,relation='adds')
ev('yichao_sends_aluowang','李彝超不奉调任诏，遣兄阿啰王守青岭门并集党项自救',12,'李彝超不奉诏，','以自救。',[('彝超','拒调任、调防并召部众者'),('阿啰王','被遣守青岭门的兄长')],place='青岭门、夏州境内',note='共兄字疑其兄，保留原字；兄明确，阿啰王为未明姓名称号，不猜等同后弟李彝兴或彝殷。遣守是命令，不外推已建何规模关寨。')
relationship('阿啰王','彝超','兄长',12,'遣共兄阿啰王守青岭门','阿啰王（李彝超兄）→李彝超兄长，按本书明文；未名个体不自动同后传弟彝兴，未据兄弟关系推同母。')
ev('yao_advances_luguan','药彦稠等进屯芦关',12,'药彦稠等','进屯芦关，',[('药彦稠','进军芦关者')],place='芦关',note='等字未名其余将领，不把安从进、宋温自动列为本句到芦关者。')
ev('yichao_raids_transport','李彝超遣党项抄掠官军粮运及攻城器具',12,'彝超遣党项','抄粮运及攻具，',[('彝超','遣部众袭粮及攻具者')],place='夏州进军路、粮运线',note='主未列袭夺数量，不推全部器械被毁。')
ev('army_falls_back_jinming','官军自芦关退保金明',12,'官军自芦关',None,[],place='芦关至金明',note='主退军未名统帅，不将等概指当确定某一人临阵逃跑；与七月全军撤回是两阶段。')
ev('jipeng_fuwang_palace','闽主封王继鹏为福王、宝皇宫使',13,'闽王璘','充宝皇宫使。',[('闽主','封子并授宫使者'),('继鹏','受福王与宝皇宫使者')],when='933年四月条后、五月条前；确日未独载',place='闽、宝皇宫',note='与正月右仆射中书侍郎同平章是加封任，未当已经继帝位。')
for name,title,start,end in [('从珂','潞王','五月，戊寅，','从珂为潞王，'),('从益','许王','从益为许王','从益为许王，'),('从温','兖王','从子天平节度使从温','从温为兗王，'),('从璋','洋王','护国节度使从璋','从璋为洋王，'),('从敏','泾王','成德节度使从敏',None)]:
 E=ev('prince_'+name,f'五月戊寅李{ name }封{title}',13,start,end,[('上','封王者'),(name,'获'+title+'爵者')],when='933年五月戊寅',place='后唐宗室',note='从珂虽称皇子但已知为养子，不新造生父关系；从温从璋从敏为从子，未明其父及长幼不猜叔伯。兗简体显示兖，军名与既有任不改。')
 if name=='从珂':claim('event',E,'description','旧明宗纪同戊寅记皇子凤翔节度使李从珂封潞王。',13,'戊寅，皇子鳳翔節度使從珂封潞王。','当前封王不复录932凤翔任命。',source=may,relation='corroborates')
 else:
  q={'从益':'皇子從益封許王，','从温':'鄆州節度使李從溫封兗王，','从璋':'河中節度使李從璋封洋王，','从敏':'鎮州節度使李從敏封涇王。'}[name]
  claim('event',E,'description','旧明宗纪五月同段记李'+name+'封'+title+'。',13,q,'旧鄆州/河中/镇州为主天平/护国/成德治名，同人爵封不造两任。',source=may,relation='corroborates')
claim('event',used[13][1],'description','新明宗纪同五月戊寅记从珂潞王、从益许王及三侄封王。',13,'夏五月戊寅，封子從珂為潞王，','取新同日佐主，新自注从珂非子指养子，不取消政治称子也不写生父。其他王爵可在同段回查。',source=princes,relation='corroborates')
relationship('上','从益','父亲',13,'立皇子从珂为潞王，从益为许王','李嗣源→李从益父亲，皇子从益明确，不因从珂养子而将从益也一概判养子；未知生母本段不猜。')
ev('min_earthquake','五月庚辰闽地震',14,'庚辰，','闽地震，',[],when='933年五月庚辰',place='闽',note='无震级、震中和损失数据，不套现代地震等级或绘具体断层。')
ev('min_ruler_retires_jipeng_acts','闽主因地震避位修道，命王继鹏权总万机',14,'闽主璘','权总万机。',[('闽主','避位修道、委权者'),('继鹏','福王、权总万机者')],when='933年五月庚辰地震同段；确起日未另载',place='闽',note='权总是暂代，不当即正式继位；此前陈守元预言而避位的新书泛叙不强并作同一原因。')
ev('min_palace_building_contrast','史述闽从王审知节俭府舍低陋转为大建宫殿',14,'初，闽王审知',None,[('审知','被回顾节俭、府舍低陋的旧主'),('闽主','当前大建宫殿的君主')],year=None,when='初与至是对照的建筑政策概述；各次确年未独载',place='闽',note='审知已925卒，本次是过去比较，不建933审知在世施工；大作未列工程日期或宫殿名，不强猜扩建地图。')
E=ev('emperor_sudden_wind_illness','五月甲申李嗣源突然得史称风疾',15,'甲申，','帝暴得风疾；',[('上','突然发病者')],when='通鉴933年五月甲申',place='后唐宫廷',note='风疾为史载病称，不据电子文诊断现代中风病种。')
claim('event',E,'description','旧明宗纪同甲申记帝九曲池避暑、登楼，风毒暴作而不豫。',15,'甲申，帝避暑於九曲池，既而登樓，風毒暴作，聖體不豫，','旧场所经过补，夹注北梦瑣言医学因果不新增。',source=may,relation='adds')
E=ev('emperor_recovers_audience','五月庚寅李嗣源病势稍缓，在文明殿见群臣',15,'庚寅，',None,[('上','小愈临殿者')],when='通鉴933年五月庚寅',place='文明殿',note='小愈不等病已永久痊愈。旧翌日而愈与主庚寅小愈阶段异说保，未静改主日。')
claim('event',E,'description','旧同甲申发病段记翌日而愈。',15,'翌日而愈。','旧翌日与主庚寅小愈日期和程度不一致，并列，后复不豫仍逐段录，不作现代病程诊断。',source=may,relation='adds')
ev('xia_signals_cavalry_rescue','壬辰夜夏州城上举火，天明有数千骑来救',16,'壬辰夜，','数千骑救之，',[],when='933年五月壬辰夜至次日天明，承前月条',place='夏州城及城外',note='数千概数，杂虏为原敌称，不作本站民族名；举火与援骑先后明，未猜具体援帅或远方联盟。')
ev('song_wen_repels_rescue','安从进遣先锋使宋温击退夏州援骑',16,'安从进遣',None,[('从进','派先锋击援者'),('宋温','先锋使、击退来援者')],when='933年五月壬辰夜后次日，承前本段',place='夏州城外',note='击走不等全歼，未见伤亡人数或宋温籍贯父母，不编。')
ev('song_qiqiu_proposes_capital','吴宋齐丘劝徐知诰迁吴主都金陵',17,'吴宋齐丘','徙吴主都金陵，',[('宋齐丘','劝迁都者'),('徐知诰','受劝者'),('吴主','拟迁都的吴君')],when='933年本段，列于五月与七月条间；确月日未独载',place='吴、拟金陵',note='劝徙为建议，不写吴主此时已搬迁；徐沿李昪，吴主杨溥沿既有key。')
E=ev('xu_builds_jinling_palace','徐知诰开始营建金陵宫城',17,'知诰乃',None,[('徐知诰','营宫城者')],when='933年本段，迁都建议后；确月日未独载',place='金陵',note='乃营为营建，不当已建成也不凭此写杨溥实际迁入；与932扩外城二十里不同工程。')
claim('event',E,'description','新吴世家太和五年概记建都于金陵。',17,'五年，建都於金陵。','太和五年对应933，主本段是营宫，主次年尚讨论迁入；新建都概述不替代主迁都进度或证明当年君已住金陵。',source=wu,relation='adds')
ev('capital_panics_absent_emperor','帝旬日不见群臣，京城人惊惧，部分避往山野或军营',18,'帝旬日不见群臣，','或寓止军营。',[],when='933年七月庚辰临殿前的旬日概述；精确起日未载',place='后唐都城、周边山野与军营',note='旬日为约十日叙时，不机械倒推公历起日；或为部分人，不写全城逃空。')
ev('emperor_guangshou_audience','七月庚辰李嗣源带病御广寿殿，京城人心稍安',18,'秋，七月，',None,[('上','力疾临广寿殿者')],when='933年七月庚辰',place='广寿殿',note='人情始安为史叙舆情，不量化全国支持率，带病不是已恢复健康。')
E=ev('xia_siege_logistics','安从进攻夏州未能破坚城，党项掠粮，关中运输困竭',19,'安从进攻夏州。','民间困竭不能供。',[('从进','攻城受补给困难的统帅')],when='至933年七月撤兵前的围城过程；起日未独载',place='夏州、关中输粮山路',note='赫连勃勃筑城是史称旧建造背景，不在933造其筑新城；党项万余为概数，城坚如铁石为描述不当金属材质检测。')
claim('event',E,'description','旧彝超传记五月安从进至城下围攻，七月粮运受党项万余骑袭而民困。',19,'五月，安從進領軍至城下，彜超不受代，從進駐軍以攻之。','旧补五月阶段；旧后七月述均见快照，不以此前芦关局部退保等同已全军返京。',source=oldsiege,relation='adds')
claim('event',E,'description','新李传记围城百余日不克，坚壁难凿，党项抄粮，民运斗粟束刍费数千。',19,'彝超果不受代，從進與彥稠以兵圍之，百餘日不克。','百余为新概述不推准确百日、兵数伤亡；故老传赫连蒸土为历史传闻不新建本年事实。',source=newsiege,relation='adds')
E=ev('yichao_brothers_request_compromise','李彝超兄弟登城请安从进表闻，求容自新并愿先行征伐',19,'李彝超兄弟登城','愿为众先。”',[('彝超','请求转奏自新者'),('从进','受登城说词的围城帅')],when='933年七月撤军前本段；确日未独载',place='夏州城',note='祖父世守、土贫无贡储为兄弟所言立场，未视为已审定地税数据。兄弟未逐名，不把前阿啰王必定此次登城。愿征伐是承诺，不当已出军替唐作战。')
claim('event',E,'description','旧彝超传七月同记兄弟登城请求改图。',19,'秋七月，彜超昆仲登城謂從進曰：','旧同七月兄弟集体归属，未补未名哥哥本名。',source=oldsiege,relation='corroborates')
E=ev('tang_orders_xia_withdrawal','七月壬午李嗣源命安从进撤回围夏州兵',19,'上闻之，壬午，','引兵还。',[('上','下撤兵命者'),('从进','奉撤兵令者')],when='933年七月壬午',place='夏州围城营、后唐朝廷',note='命撤与实际行程分，不写当日全军已到洛阳。')
claim('event',E,'description','旧明宗纪同壬午诏安从进班师，称攻夏州无功。',19,'壬午，詔安從進班師，時王師攻夏州無功故也。','同日诏命互核，不另造第二撤军令。',source=july,relation='corroborates')
ev('renfu_rumor_reassessed','其后有人称李仁福虚言契丹为援，实际未通，导致朝廷误征',19,'其后有知李仁福阴事者，','无功而还。”',[],year=None,when='其后，撤军后的解释性报告；确年未独载',place='后唐、夏州相关',note='有知者云为未名人士新说，不当已确独立查案结论；与此前诸镇潜通指控并列，阴事不是本站已定罪事实，仁福已死不复生通敌。')
ev('xia_links_rebels_retrospective','史述此后夏州轻朝廷，常与叛臣相联以邀馈赠',19,'自是夏州轻朝廷，','以邀赂遗。',[],year=None,when='自是，此后反复政策概述；起止年及各次未独载',place='夏州',note='概述不建每名未载叛臣或把全部此后联系压为933同日；赂遗保为馈赠关系史述，不猜金额。')
E=ev('army_extra_grants','七月乙酉李嗣源因病未平及征夏无功、军中流言，赐京军额外优给',19,'上疾久未平，',None,[('上','发额外优给者')],when='933年七月乙酉',place='后唐在京诸军',note='无名赏赉令兵益骄为史评价，未据此说每一军人都犯法；未见具体人均金额。')
claim('event',E,'description','旧明宗纪同乙酉记赐京军将校优给，称帝疾未痊、军士流言。',19,'詔賜在京諸軍將校優給有差。時帝疾未痊，軍士有流言故也。','同日互核，旧同日孟鹄死亡不提前从其他书插入本段主线；后主下一段另读。',source=july,relation='corroborates')
E=ev('qian_yuanguan_wuwang','七月丁亥朝廷封钱元瓘为吴王',20,'丁亥，','爵吴王。',[('上','授吴王爵者'),('钱元瓘','两浙君、获吴王爵者')],when='933年七月丁亥',place='两浙、后唐朝廷',note='钱元瓘沿既有钱传瓘改名主体；吴王爵不等杨吴国君，不能与吴主杨溥合并。')
claim('event',E,'description','旧明宗纪同丁亥记两浙节度使钱元瓘封吴王。',20,'丁亥，兩浙節度使、檢校太傅、守中書令錢元瓘封吳王。','同日同爵补官衔，旧钱传后改元的主体UUID沿用。',source=july,relation='corroborates')
# Selected TXT mistakenly repeats the younger brother's name at the elder brother's positions.
collated=(sources[qian]/'source.txt').read_text()
E=ev('qian_brother_visit','钱元璙从苏州入见钱元瓘，兄弟行家人礼、祝寿互陈忠让',20,'元瓘于兄弟甚厚，',None,[('钱元瓘','承位弟弟、以家礼奉觞者'),('钱元璙','从苏州来见的兄长、中吴建武节度使')],year=None,when='兄弟入见及对泣叙事，附七月封爵段；确月日未独载',place='苏州至两浙王府',note='主底本兄长及答话处误重复元瓘；固定音注版正文元璙、注即传璙识已有钱传璙。原文不改，入见未独日不套丁亥。对话为史述立场，不编具体转让印玺新仪式。')
claim('event',E,'description','通鉴固定音注校录正文称元璙从苏州入见、答称知忠顺，兄弟对泣。',20,'元璙自蘇州入見，','校录同书异版用于校兄名；旧TXT误重复仍留原摘，不当两人同名或同人自见。胡注为校字依据不算独立第二史书确证。',source=qian,relation='adds')
claim('person',people['钱传璙'],'aliases','钱传璙后称钱元璙，通鉴音注在此明确元璙即传璙。',20,'元璙卽傳璙。','已有902钱传璙及904底本传撩身份沿稳定key，后名仅补别名；不追溯说902即已称元璙。',source=qian,relation='adds')
relationship('钱元璙','钱元瓘','兄长',20,'其兄中吳、建武節度使元璙自蘇州入見','钱传璙（元璙）→钱传瓘（元瓘）兄长，主兄字及校录姓名明确；复用已有同向关系时保旧key，未知是否同母不猜。',source=qian)
reviews={11:'秦王请师、王居敏荐与表、癸丑正式授刘傅鱼记室、刘泣辞、日常谏与限门分。秦傅主瓚旧讚新贊按同职同日识别，与已录923嘉州司马刘赞未有同人证，限定新主体；旧魏州履历补。主兵部、旧刑部异职保，主自以左迁与新祸将至言并列，不推现代品级或当时已遭杀贬。旧父比新玭异字暂未建父。旧传夹注其他专书不新增。',12:'不奉诏、遣兄守及聚部、药屯芦关、抄粮具、局部退金明分。共兄疑其字保留，阿啰王称兄但未名，不猜等后弟彝兴或彝殷；有向兄长关系。部众未名不造民族统帅，局部退与七月全军撤分。',13:'闽福王宫使在五月条前，不套戊寅；五月戊寅五唐王逐人封，与旧同月同职军治名互核、新同日佐。主政治称从珂皇子仍是已知养子，不新生父边。李从益明确皇子父关系，三从子未明叔伯长幼不猜。',14:'五月庚辰地震及闽主避位暂委子分，权总不是正继帝位；未强同此前陈守元预言避位泛叙。节俭旧主审知与至是大建宫殿为对照概述yearnull，不把925死审知复生，没震级不编。',15:'五月甲申风疾及庚寅小愈临殿分，旧甲申九曲池登楼场所补；旧翌日愈与主小愈日异并列，不改主。风疾为史称不当现代中风诊断，夹注北梦不新增。',16:'五月壬辰夜举火、天明数千援骑与安遣宋击退分，概数不说全歼或确定民族首领；宋温新身份仅先锋使。',17:'宋劝迁吴主和徐营金陵宫分，提议营建非已迁吴主，徐沿李昪吴主杨溥。新太和五年建都概述补，未替代主次年尚迁都进度，不与932外城扩建混。',18:'旬日帝未见臣、都人或避与七月庚辰带病临广寿殿分，未精倒推十日公历起，不说全城逃尽或帝痊。',19:'夏城坚及粮困、李兄弟求改图、七月壬午撤令、后仁福未通新解释、此后夏州联叛概述、七月乙酉京军优给分。旧五月围城与七月供困层次补、新百余日概述不推精日，赫连旧筑为背景不造933工程。兄弟话贫无贡储及愿征为立场承诺，不当已查税或已从军；后未知知者云与此前潜通报告并列，yearnull。此前局部芦关退非此次全军撤，命回非当日抵京。旧同日孟鹄死不抢主未载段落，史兵骄论不当全体皆犯罪。',20:'七月丁亥钱吴王与旧同日互核，吴爵不等吴主。兄访礼与对泣未独年月yearnull，不强套封爵日。主兄名及答名误重复元瓘，固定音注同卷正文元璙、注即传璙核已有902传璙，原文不改。元瓘沿传瓘、元璙沿传璙稳定key并补后名检索；兄长有向，不猜同母，校录为同书异版非独立史书。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
context=P/'sources/context/qian-yuanliao-name/response.json'
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=933,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v278-y0933-p021',next_volume=278,next_year=933,supplements=supplements,source_contexts=[dict(file=os.path.relpath(context,P/'sources'),sha256=hashlib.sha256(context.read_bytes()).hexdigest(),note='通鉴音注固定修订2115814完整API响应；兄名原TXT误重复元瓘的同书校录核对。')],excluded_non_body=[],coverage='卷278连续933年第11—20段、原46—55行；秦王师傅、夏州进退、闽及唐王爵、地震权总、明宗病况与舆情、吴营宫、围夏困乏撤军及优给、钱王爵与兄弟礼。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,21)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
