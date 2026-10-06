# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 293, year 956 paragraphs 41–48."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,58))
COMMIT='d1355da27db0b773c786b11815d5b346a3806769'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

for key in ['tongjian-293-956-hunan-yangzhou-withdrawal']:
 prior=next(x for f in (ROOT/'content').rglob('content-batch.json') for x in json.loads(f.read_text())['sources'] if x['key']==key)
 commit,relative=prior['url'].split('/blob/')[1].split('/',1)
 specs.append((key,(ROOT/relative).parent,commit,prior['author']))

# Reuse already published source identities, including the earlier Zhou Gui biography.
prior_source_registry={x['key']:x for f in sorted((ROOT/'content').rglob('content-batch.json')) if f.parent != P for x in json.loads(f.read_text())['sources']}
normalized=[]
for key,path,commit,author in specs:
 if key in prior_source_registry:
  archived=prior_source_registry[key]['url'].split('/blob/',1)[1];commit,relative=archived.split('/',1);old_path=(ROOT/relative).parent
  assert (old_path/'source.txt').read_bytes()==(path/'source.txt').read_bytes(),key
  path=old_path
 normalized.append((key,path,commit,author))
specs=normalized

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-293-956-hunan-yangzhou-withdrawal']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0956-p041-p048',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=record.get('edition_note','选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/293.txt').read_text().splitlines()
for n in range(41, 49):
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
for revision in sorted((ROOT/'content/revisions').glob('*/aliases.json')):
    if not (revision.parent/'publication.json').exists():continue
    for corrected in json.loads(revision.read_text()).get('people',[]):
        if corrected['name'] in registry:registry[corrected['name']]=dict(registry[corrected['name']],aliases=corrected['after'])
for name,extra in [('荝剌',['荝刺']),('耶律倍',['李赞华','李贊華'])]:
    if name in registry:registry[name]=dict(registry[name],aliases=list(dict.fromkeys(registry[name]['aliases']+extra)))
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if key in prior_source_registry}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    for a,b in [('主書','《资治通鉴》'),('補','补'),('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷293·显德三年（956年八月至十月及相关叙述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0956_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'马在贵':'南唐楚州将领。956年四月在湾头堰被韩令坤击败，《旧五代史》记其所领万余众，未记其本人最后结局。生卒年未载。',
'王环（后蜀凤州节度使）':'镇州真定人，早年以勇力为孟知祥御者，后掌后蜀宿卫。开运末秦凤等地入蜀后，孟昶任其为凤州节度使。955年十一月凤州陷落时被后周军俘获。与914—929年楚水军将领王环分别保存，无同人证据。生卒年未载。','王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
NEW_ALIASES={'王威（王处直之子）':['王威']}

ALIASES.update({'景通':'李璟','徐知诰':'李昪','徐诰':'李昪','元瓘':'钱传瓘','钱元瓘':'钱传瓘','闽主':'王继鹏','蜀主':'孟昶','汉主':'刘岩','梁均王':'朱友贞'})



ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

# Follow already verified merges so hidden legacy entities are never revived.
registry_by_key={r['key']:r for r in registry.values()}
for plan_file in sorted((ROOT/'content/revisions').glob('*/plan.json')):
 audit_file=plan_file.parent/'publication.json'
 if not audit_file.exists():continue
 plan=json.loads(plan_file.read_text());audit=json.loads(audit_file.read_text())
 if not (audit.get('verified') and audit.get('canonical_person_id') and audit.get('hidden_duplicate_person_id')):continue
 canonical=registry_by_key.get(plan.get('canonical_key'));duplicate=registry_by_key.get(plan.get('duplicate_key'))
 if canonical and duplicate:
  canonical=dict(canonical,aliases=list(dict.fromkeys(canonical.get('aliases',[])+plan.get('aliases_to_add',[]))))
  registry[canonical['name']]=canonical
  for alias in [duplicate['name']]+duplicate.get('aliases',[]):ALIASES[alias]=canonical['name']

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=globals().get("NEW_BIRTH_YEARS",{}).get(name),death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=956, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='956年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_293_0956_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=description or title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='采用史书记载的地点名称，地理坐标尚未核实。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按《资治通鉴》及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_293_0956_' + code + '_' + pk
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
    a=ALIASES.get(a,a); b=ALIASES.get(b,b)
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'史书记{a}是{b}的{kind}',quote,source=source)
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
        row=dict(key=f'relationship_zztj_293_0956_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 if kw.get('source'):
  t=(sources[kw['source']]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);quote=t[a:b]
 else:quote=span(n,start,end)
 E[code]=event(code,title,n,quote,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)











ALIASES.update({'上':'柴荣','帝':'柴荣','景达':'徐景达','唐主':'李璟'})
NEW_ALIASES={'王处讷':['王處訥'],'王彦升':['王彥升']}
NEW_DESCRIPTIONS={'王处讷':'后周司天少监。956年八月，《资治通鉴》记他与王朴编成《显德钦天历》并呈交朝廷，柴荣下令次年实行。生卒年未载，与邓处讷分别保存。','王彦升':'蜀人，后周铁骑都指挥使。956年十月李重进奏报他等人在盛唐击败南唐军。《资治通鉴》记斩首三千余级，《旧五代史》本纪记二千级，战果数量有异。生卒年本段未载。'}
aug='jiuwudaishi-116-august-956';sep='jiuwudaishi-116-september-956';oct='jiuwudaishi-116-october-956'
add('tang_rejects_interception','宋齐丘主张放周军撤退，南唐命各将守地而不擅出击',41,'唐诸将请据险','毋得擅出击周兵。',[('宋齐丘','反对据险截击，主张让周军离去以缓和战争')],when='956年七月周军撤离扬州以后，八月历法条以前，具体日未载',place='南唐军中',description='南唐诸将请求据险截击周军，宋齐丘认为这样会加深敌意，主张放其离去，以便缓和战争。南唐随后命各将各守驻地，不得擅自出击；这只是宋齐丘的判断，不能写成双方已经达成和议。')
add('jingda_hao_reinforcement','徐景达驻濠州声援寿州，陈觉掌军政而未决战',41,'由是寿春之围益急。',None,[('景达','以齐王身份率五万兵驻濠州，签署军中文书'),('陈觉','掌握援军军政')],when='956年寿春围攻期间，具体驻军日未载',place='濠州、寿州',description='《资治通鉴》认为停止出击使寿春围势更紧。齐王徐景达驻濠州，遥援寿州，拥兵五万；军政由陈觉决定，徐景达只在文书末尾签署。史书称其没有决战意图、将吏畏惧陈觉而不敢进言；这些评价保留出处，不外推所有人的内心。')
add('qintian_calendar_submitted','王朴、王处讷呈交《显德钦天历》，柴荣令次年实行',42,Q[42]['text'],None,[('王朴','以端明殿学士身份参与编历并呈交'),('王处讷','以司天少监身份参与编历并呈交'),('帝','下令从次年实行新历')],when='956年八月戊辰呈交；诏令规定次年实行',place='后周朝廷',note='呈交与计划实行分开；次年指957年，这里没有独立证明后来已实际全境执行。')
sup('qintian_calendar_submitted',42,aug,'戊辰，端明殿學士王樸撰成新歷上之，命曰《顯德欽天曆》，上親為制序，仍付司天監行用。','《旧五代史》也记八月戊辰王朴呈交新历，柴荣亲作序，并交司天监行用。','该句只列王朴，不据省略否定王处讷参与；没有次年字样，与《通鉴》规定次年实行分别保留。')
add('xiacai_fire_attack_fails','林仁肇试图烧毁下蔡浮桥，风向回转后退败',43,'殿前都指挥使','唐兵败退。',[('张永德','驻下蔡并迎战南唐援军'),('林仁肇','率水陆军援寿春，以载薪草船顺风纵火攻浮桥')],when='956年八月条所记，具体交战日未载',place='下蔡淮河浮桥',note='烧桥为意图，风回退败为结果，不写浮桥已经烧毁。')
sup('xiacai_fire_attack_fails',43,aug,'殿前都指揮使張永德奏，破淮賊於下蔡。先是，江南李景以王師猶在壽州，遣其將林仁肇、郭廷謂率水陸軍至下蔡，欲奪浮梁，以舟實薪芻，乘風縱火，永德禦之。有頃，風勢倒指，賊眾稍卻，因為官軍所敗。','《旧五代史》记张永德奏报下蔡获胜，并补列郭廷谓与林仁肇率水陆军援寿州。','奏报条在八月，先是说明战斗先前发生；李景沿既有李璟字形，不从排版紧接历法戊辰便断定战斗也在当日。')
add('xiacai_iron_barrier','张永德在浮桥外横设铁索与巨木，阻止南唐船靠近',43,'永德为铁绠',None,[('张永德','设置千余尺铁索，系巨木横阻淮河')],when='956年下蔡火攻失利以后，具体日未载',place='下蔡淮河浮桥外',description='张永德设置千余尺铁索，在离浮桥十余步处横截淮流，系以巨木，阻止南唐军靠近。长度和距离沿用史载单位，不未经证据换算成现代工程尺度。')
add('wangpu_deputy_commissioner','柴荣任王朴为户部侍郎、枢密副使',44,Q[44]['text'],None,[('帝','任命王朴'),('王朴','从端明殿学士等职获任户部侍郎、枢密副使')],when='956年九月丙午',place='后周朝廷')
sup('wangpu_deputy_commissioner',44,sep,'九月丙午，以端明殿學士、左散騎常侍、權知開封府事王樸為尚書戶部侍郎，充樞密副使；','《旧五代史》同记九月丙午任王朴为尚书户部侍郎、枢密副使。','两书所列旧职相同，王樸按简体规范与王朴同人。')
add('shengtang_victory_report','李重进奏报王彦升等击败进攻盛唐的南唐军',45,Q[45]['text'],None,[('李重进','奏报盛唐战果'),('王彦升','以铁骑都指挥使身份率军击败南唐进攻军')],when='956年十月癸酉奏报，具体交战日未载',place='盛唐',description='李重进于十月癸酉奏报南唐军进攻盛唐，王彦升等击败对方。《资治通鉴》记斩首三千余级，《旧五代史》本纪记二千级，数量有异。癸酉是奏报日，不能直接当作交战日。')
sup('shengtang_victory_report',45,oct,'癸酉，淮南招討使李重進奏，破淮賊於盛唐，斬二千級。','《旧五代史》记十月癸酉李重进奏报盛唐获胜，斩二千级。','《资治通鉴》三千余级与此数量有异，不能取较大数作为两书共同确定值。',relation='conflicts')
claim('person',people['王彦升'],'description','王彦升是蜀人；本段未记具体出生地或生卒年。',45,'彦升，蜀人也。','籍贯区域与出生地点不是同一概念，未给现代坐标。')
add('zhou_tax_collection_schedule','柴荣令夏税六月、秋税十月起征，避免提前征收',46,Q[46]['text'],None,[('帝','指出征收早于收获纺织的问题，命三司改起征时间')],when='956年十月丙子下诏；此后夏税六月、秋税十月起征',place='后周征税地区',description='柴荣指出近来谷帛征敛常在收获、纺织完成前就开始，命三司此后夏税从六月起征、秋税从十月起征。《通鉴》称民间因此便利。月份沿用历史纪月，不追溯为本年六月已执行，也不误写成全国税收取消。')
add('anshenqi_audience_promotion','安审琦入朝获加守太师，随后返回襄州',47,'山南东道节度使','遣还镇。',[('安审琦','镇襄州十余年后入朝，加守太师并返镇'),('帝','加安审琦官衔并遣回')],when='956年十月条所记；《旧五代史》记丙子加守太师',place='襄州至后周朝廷',note='十余年只作任期概述，不据模糊数量反推出准确上任年。')
sup('anshenqi_audience_promotion',47,oct,'丙子，襄州節度使、守太尉、兼中書令、陳王安審琦加守太師。審琦鎮漢上十餘年，至是來朝，故以命寵之。','《旧五代史》记十月丙子加安审琦守太师，解释为其长期镇汉上后入朝所获礼遇。','加衔的明确日可补充，不把遣返和送行也强定同日；汉上与襄州任职上下文相接。',relation='adds')
add('zhou_emperor_values_trust','柴荣询问安审琦送行情况，主张以诚信对待地方长官',47,'既行，',None,[('帝','向宰相说明君主守信可争取诸侯归心')],when='956年十月安审琦离京以后，具体日未载',place='后周朝廷',description='安审琦离京后，柴荣问宰相是否送行。宰相答送至城南，安审琦感念恩遇。柴荣认为近来朝廷不以诚信待诸侯，妨碍他们效忠，主张君主先守信。这里记录君臣对话，不把“诸侯归心”写成所有地方已经完全臣服。')
add('xiacai_swimmers_chain_ships','张永德奏报下蔡再胜：泳者夜潜锁船，周军进击',48,'壬午，','溺死者甚众。',[('张永德','夜遣善游者铁锁系住南唐船，发兵攻击并奏报战果')],when='956年十月壬午奏报，具体夜战日未载',place='下蔡水域',description='南唐水军再次进攻张永德。张永德夜令善游者潜入船下，以铁锁系船，再发兵进攻，南唐船不能进退，史书称溺死者很多。他于十月壬午奏报获胜。此战与先前火攻浮桥失败分开记录，未给死亡精确人数或泳者姓名。')
add('xiacai_swimmers_reward','张永德解下金带，奖赏锁船获胜的泳者',48,'永德解金带',None,[('张永德','以自己的金带赏赐善游者')],when='956年下蔡锁船战获胜后，具体赏赐日未载',place='下蔡军中',note='善游者未具名，不补虚构人物；金带价值未载。')
reviews={41:'截击提议、宋齐丘缓战判断、守地命令和军政控制区分。徐景达沿同人，不将史家对将吏评价作独立心理事实。',42:'呈交956八月戊辰与计划957行历分开；旧史补柴荣序、司天行用，未列王处讷不视为否定。',43:'火攻意图、风回失败及铁索木障依序。旧史郭廷谓为补充，八月奏报不等戊辰交战，尺度不换算。',44:'王朴任命九月丙午两书一致。',45:'十月癸酉奏报非战日，三千余与二千数量冲突并列，蜀人不定精确出生地。',46:'新起征月份沿古历，不追溯已经执行，不理解成免税；民便属于史家评价。',47:'加衔旧史记丙子，返镇送行不强同日。十余年不计算任始，匿名宰相不推具体名单，诚信论非天下已服事实。',48:'再次水战与八月火攻分开，壬午奏报不强战日，死亡甚众不编数，未具名泳者不造人。'}
assert not (P/'publication.json').exists()
for n in range(41,49):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(41,49)],next_paragraph=Q[49]['id'],next_volume=293,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原46—53行连续八段，后续未计。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(41,49)],source_issues_review='盛唐斩首数量两书有异；历法行用时间保留差别。王处讷王彦升检索既有姓名无同人，按明示官职与地域建档。原文原字保留，纸本及异文待核。',plain_language_review='首次逐条核对标题正文、人物与角色、事实说明和引用解释；均写明确主语动作，计划、奏报、战斗执行和史家评价分开，不使用内部来源简称，未知数量与姓名不补造。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
