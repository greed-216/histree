# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 1–7."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,83))
COMMIT='7f523fc68334366ce90d3a6e1465b179c9c38000'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='tongjian-290-951-january-court']
for key in []:
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
main_sources = ['tongjian-290-951-accession-policy']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p001-p007',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-accession-policy':'卷290·广顺元年·即位与正月政策','jiuwudaishi-110-accession-edict':'卷110·太祖本纪·汉太后授符诰','jiuwudaishi-110-pardon-posthumous':'卷110·太祖本纪·改元赦令及追赠','jiuwudaishi-110-grain-surcharge':'卷110·太祖本纪·停斗余秤耗','jiuwudaishi-110-criminal-law':'卷110·太祖本纪·刑法与连坐限制','jiuwudaishi-110-staff-tombs':'卷110·太祖本纪·罢补将与守陵','jiuwudaishi-131-liu-hao-career':'卷131·刘皞传·历官至卫尉卿','songshi-257-li-chongju-property':'卷257·李崇矩传·交还史氏家产','xinwudaishi-011-first-year-951':'卷11·周本纪·广顺元年'}
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
lines = (ROOT / 'resources/derived/tongjian/290.txt').read_text().splitlines()
for n in range(1, 8):
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

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
    labels={'tongjian-290-951-accession-policy':'卷290·广顺元年·即位与正月政策','jiuwudaishi-110-accession-edict':'卷110·太祖本纪·汉太后授符诰','jiuwudaishi-110-pardon-posthumous':'卷110·太祖本纪·改元赦令及追赠','jiuwudaishi-110-grain-surcharge':'卷110·太祖本纪·停斗余秤耗','jiuwudaishi-110-criminal-law':'卷110·太祖本纪·刑法与连坐限制','jiuwudaishi-110-staff-tombs':'卷110·太祖本纪·罢补将与守陵','jiuwudaishi-131-liu-hao-career':'卷131·刘皞传·历官至卫尉卿','songshi-257-li-chongju-property':'卷257·李崇矩传·交还史氏家产','xinwudaishi-011-first-year-951':'卷11·周本纪·广顺元年'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年正月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={'王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
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

def event(code, title, n, quote, actors, when=None, note='', year=951, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='951年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0951_' + code
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
        edge = 'participation_zztj_290_0951_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0951_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=event(code,title,n,span(n,start,end),actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)










ALIASES.update({'帝':'郭威','汉太后':'李氏（刘知远妻）','汉李太后':'李氏（刘知远妻）','唐庄宗':'李存勖','明宗':'李嗣源','晋高祖':'石敬瑭','汉高祖':'刘知远','荣':'柴荣','刘勋':'刘承勋','刘皞':'刘皞（后晋编敕官）'})
NEW_ALIASES={'李崇矩':[],'史弘福':['史福']}
NEW_DESCRIPTIONS={'李崇矩':'上党人，史弘肇的亲吏，曾掌其家产账册。951年郭威命他寻找史弘肇亲属，他找到史弘福并将所掌家产全部交还；郭威赞赏他，令他转隶柴荣帐下。生卒年未载。','史弘福':'史弘肇的弟弟。951年李崇矩向郭威报告他仍在世，并将掌握的史氏家产全部交给他。《宋史》李崇矩传写史弘肇母弟福。生卒年未载。'}
old='jiuwudaishi-110-accession-edict';pardon='jiuwudaishi-110-pardon-posthumous';grain='jiuwudaishi-110-grain-surcharge';law='jiuwudaishi-110-criminal-law';staff='jiuwudaishi-110-staff-tombs';career='jiuwudaishi-131-liu-hao-career';song='songshi-257-li-chongju-property';new='xinwudaishi-011-first-year-951'
add('lady_hands_guo_seals','李太后于丁卯授郭威符宝，下诰令他即位',1,'春，正月，','即皇帝位。',[('汉太后','授监国郭威符宝，下诰令即位'),('郭威','获得符宝与即位诰令')],when='951年正月丁卯',place='大梁朝廷',note='授符宝诰与实际从皋门入宫登基分录；符宝指君主凭信与印宝，不作虚构器物图。')
sup('lady_hands_guo_seals',1,old,'今奉符寶授監國，可即皇帝位。','《旧五代史》丁卯太后诰也记将符宝授郭威，允许即位。','诰令中的天命、人心、六师推戴是诰令说法，不将政治宣示当现代调查结论。')
add('guo_accession_chongyuan','郭威自皋门入宫，在崇元殿正式即位',1,'监国自皋门','即位于崇元殿，',[('郭威','自皋门入宫，在崇元殿正式即位')],when='951年正月丁卯',place='大梁崇元殿',note='与950年军中拥立及监国分开，此处有正式入宫登基记载。')
sup('guo_accession_chongyuan',1,old,'是日，帝自臯門入大內，禦崇元殿，即皇帝位。','《旧五代史》也记丁卯郭威从皋门入宫，在崇元殿即位。','臯与皋字形统一展示，摘录原字保留。')
add('guo_zhou_dynasty_name','郭威称自己是周室后裔，定国号为周',1,'制曰：“朕周室','国号宜曰周。”',[('郭威','以周室、虢叔后裔的自述解释国号周')],when='951年正月丁卯',place='大梁朝廷',note='周室虢叔后裔是诏制自述，不因此建立无证据的跨千年血缘链。')
sup('guo_zhou_dynasty_name',1,pardon,'朕本姬室之遠裔，虢叔之後昆，積慶累功，格天光表，盛德既延於百世，大命復集於眇躬，今建國宜以大周為號，','《旧五代史》即位制也用周室后裔说法说明国号大周。','国号有制度决定证据，家系远祖宣示未独立谱牒校核。')
add('guo_guangshun_pardon','郭威改元广顺并实行大赦',1,'改元，大赦。','改元，大赦。',[('郭威','改元广顺，实行大赦')],when='951年正月丁卯',place='后周',note='广顺元年据年题及新旧本纪，不给实际所有罪人释放完成日。')
sup('guo_guangshun_pardon',1,new,'廣順元年春正月丁卯，皇帝即位，大赦，改元，國號周。','《新五代史》也记丁卯即位、大赦、改元及国号周。','几项同日措施分开记录，不与950年监国混为一日。')
sup('guo_guangshun_pardon',1,pardon,'可改漢乾祐四年為廣順元年。自正月五日昧爽已前，應天下罪人，常赦所不原者，咸赦除之。','《旧五代史》制补记将乾祐四年改为广顺元年，大赦以正月五日天明以前为界。','制文列赦令适用截止时点，未写每个受刑者实际释放；不自行换算公历。',relation='adds')
add('guo_posthumous_three_ministers','郭威追赠杨邠、史弘肇、王章，官府负责收殓安葬',1,'杨邠、史弘肇、王章等','官为敛葬，',[('郭威','追赠被害大臣，令官府办理收殓安葬'),('杨邠','死后获追赠与官府办理葬事'),('史弘肇','死后获追赠与官府办理葬事'),('王章','死后获追赠与官府办理葬事')],when='951年正月丁卯即位诏制',place='后周朝廷',note='等未给全部名单，本事件列三名有姓名者；葬事安排不强定已同日完成下葬。')
sup('guo_posthumous_three_ministers',1,pardon,'並可加等追贈，備禮歸葬，葬事官給，仍訪子孫敘用。','《旧五代史》制也命追赠、按礼归葬，葬费官给，访求子孙任用。','已读上文三臣名单，宏肇底本字形沿既有弘肇主体；命令与完成分开。')
add('guo_seeks_minister_descendants','郭威命访求杨邠、史弘肇、王章等子孙任用',1,'仍访其子孙','叙用之。',[('郭威','命访求被害大臣子孙并任用'),('杨邠','其子孙成为访求任用对象'),('史弘肇','其子孙成为访求任用对象'),('王章','其子孙成为访求任用对象')],when='951年正月丁卯即位诏制',place='后周',note='子孙未列姓名，不造无证据谱系，也不把访求令当全部找到并授官。')
add('guo_stops_grain_surcharge','郭威禁止仓库收纳官吏额外收取斗余、称耗',1,'凡仓场、库务','称耗。',[('郭威','禁止仓场库务收纳官吏额外收取斗余和称耗')],when='951年正月丁卯即位诏制',place='后周各仓场、库务',description='郭威规定仓场、库务负责收纳的官吏不得额外收取斗余和称耗，限制借量斗、称量损耗之名加收财物。',note='保留制度专名并说明动作，不根据诏令声称全国加收立即完全消失。')
sup('guo_stops_grain_surcharge',1,grain,'掌納官吏一依省條指揮，不得別納鬥餘、秤耗，','《旧五代史》也命收纳官吏遵守规定，不得另收斗余、秤耗。','称耗与秤耗为两书字形，保留原引文；不把正常税额也当全部免除。')
add('guo_stops_surplus_offerings','郭威停止旧例进献的额外盈余财物',1,'旧所羡馀物，','悉罢之。',[('郭威','停止旧例进献的额外盈余财物')],when='951年正月丁卯即位诏制',place='后周仓场、库务',note='羡余为旧例所进盈余，未写取消一切财政收入，金额未载。')
sup('guo_stops_surplus_offerings',1,grain,'舊來所進羨余物色，今後一切停罷。','《旧五代史》也命停止旧例进献的羡余财物。','对应进献旧例，不能扩成全部库存物资销毁。')
add('guo_restores_theft_adultery_law','郭威命盗窃、奸罪按晋天福元年以前规定处罚',1,'犯窃盗及奸者，','刑名，',[('郭威','规定盗窃与奸罪采用晋天福元年以前刑罚条制')],when='951年正月丁卯即位诏制',place='后周',note='刑名为刑罚规定，不补各罪全部量刑表；主书奸的范围与旧制和奸表述区别保留。')
sup('guo_restores_theft_adultery_law',1,law,'今後應犯竊盜賊贓及和奸者，並依晉天福元年已前條制施行。','《旧五代史》制明确说盗窃赃物及双方自愿的奸罪，依晋天福元年以前条制施行。','旧制限定和奸，通鉴概称奸；不从概述推强迫性犯罪的全部量刑被减免。',relation='adds')
add('guo_limits_family_punishment','郭威规定除反逆罪外，不得牵连杀亲属或没收家产',1,'罪人非反逆，','籍没家赀。',[('郭威','限制除反逆罪外的杀害亲属、没收家产')],when='951年正月丁卯即位诏制',place='后周',note='保留反逆例外，不能写彻底废除全部连坐；没收家产不等于免个人合法刑罚。')
sup('guo_limits_family_punishment',1,law,'應諸犯罪人等，除反逆罪外，其罪並不得籍沒家產、誅及骨肉，一依格令處分。','《旧五代史》也记除反逆外，不得没收家产或诛杀亲属，按法规处理。','同例外同限制，未补现代司法制度。')
for code,name,start,end in [('zhuang_tomb_households','唐庄宗','唐庄宗、明宗、晋高祖','各置守陵十房，'),('ming_tomb_households','明宗','唐庄宗、明宗、晋高祖','各置守陵十房，'),('jin_tomb_households','晋高祖','唐庄宗、明宗、晋高祖','各置守陵十房，')]:
 add(code,'郭威为'+ALIASES[name]+'陵墓设置十户守陵人家',1,start,end,[('郭威','为前代君主陵墓设置守陵户'),(name,'其陵墓获置十户守陵人家')],when='951年正月丁卯即位诏制',place='前代君主陵墓',note='十房指守陵人户，旧制十户印证；各陵各十，不作总计十。陵址坐标未核。')
sup('zhuang_tomb_households',1,staff,'唐莊宗、明宗、晉高祖，各置守陵十戶，以近陵人戶充。','《旧五代史》也规定三位前代君主各置十户守陵，以陵墓附近人户充任。','十户印证通鉴十房，补近陵人家范围；不推永久免税。',relation='adds')
add('guo_preserves_han_tomb_services','郭威保留刘知远陵墓人员、祭祀与守陵户',1,'汉高祖陵职员、宫人，','并如故。',[('郭威','保留汉高祖陵墓原有人员、祭祀与守陵户'),('汉高祖','陵墓服务制度获保留')],when='951年正月丁卯即位诏制',place='汉高祖陵',note='如故为沿旧制，未给具体人数及每次祭祀费用，不自行补。')
sup('guo_preserves_han_tomb_services',1,staff,'漢高祖皇帝陵署職員及守宮人，時日薦饗，並守陵人戶等，一切如故。','《旧五代史》也保留汉高祖陵署人员、祭祀和守陵户。','守宫人按陵署服务者解释，不混作新后宫任职。')
add('late_tang_theft_death_rule','晚唐严法规定盗赃三匹者处死',1,'初，唐衰，','窃盗赃三匹者死。',[],year=None,when='晚唐时期的刑法追述，具体颁行年未载',place='唐朝',description='史书追述，晚唐盗贼增多后不按通常律文处理，另定严法，盗窃赃物达到三匹者处死。',note='三匹保留古代赃物计价单位，不换成三件现代衣物；未给颁行帝和年，年置null。')
add('jin_theft_five_pi_rule','晋天福年间将盗窃死刑赃额提高到五匹',1,'晋天福中，','加至五匹。',[],year=None,when='晋天福年间的刑法追述，具体改变年日未载',place='后晋',note='承前盗窃赃额三匹，五匹为死刑标准提高，不写951年新颁；天福范围可知不擅选其中一年。')
add('jin_adultery_death_rule','晋天福年间旧法对已婚妇女相关奸罪判男女死刑',1,'奸有夫妇人，','男女并死。',[],year=None,when='晋天福时期旧法追述，具体颁行日未载',place='后晋',description='史书追述，对于与有夫之妇发生性关系的案件，不论强迫还是自愿，男女都判死刑。',note='该句接晋天福刑法背景；原文明说无问强和男女并死，不将受害者受罚改写为现代规范，也不自行认定此案全部责任。')
add('han_one_coin_theft_death','后汉旧法规定盗窃一钱以上者处死',1,'汉法，','一钱以上皆死。',[],year=None,when='后汉时期刑法追述，具体颁行年日未载',place='后汉',note='一钱是书载赃额，未换现代货币；不把此旧法写成郭威951年新法。')
add('han_family_punishment_abuse','后汉旧时非反逆案件也常杀亲属、没收家产',1,'又罪非反逆，','故帝即位，首革其弊。',[],year=None,when='郭威即位以前的后汉刑罚概述',place='后汉',description='史书追述，后汉旧时即使不是反逆罪，也常诛杀亲属、没收家产，因而郭威即位后首先改变这些做法。',note='往往为概述，不造未具名案件清单；与951年实际限制令分开。')
add('yang_bin_places_local_staff','杨邠此前从三司军将中选人补地方幕职',2,'初，杨邠','补都押牙、孔目官、内知客，',[('杨邠','认为功臣国戚方镇多不熟政务，从三司军将中选补地方幕职')],year=None,when='后汉杨邠主政期间的追述，具体开始年日未载',place='后汉各方镇',note='不闲为不熟悉，推断出自杨邠判断；不写所有节度使确实无能力。')
add('guo_abolishes_central_staff','郭威罢撤朝廷派到方镇的军将幕职',2,'其人自恃敕补，','至是悉罢之。',[('郭威','罢撤此前朝廷派往方镇的军将幕职')],when='951年正月即位初，具体执行日未单列',place='后周各方镇',description='史书说这些军将仗着朝廷任命而专横，节度使不能约束。郭威即位时罢撤了这些中央选派的幕职安排。',note='专横和不能约束为史书概述；罢撤指定军将选补，不说废掉所有都押牙等官职。')
sup('guo_abolishes_central_staff',2,staff,'其先於在京諸司差軍將充諸州郡元從都押衙、孔目官、內知客等，並可停廢，仍勒卻還舊處職役。','《旧五代史》也命停止从京城诸司派军将充任地方幕职，并令他们返回原处任职。','补返回原处安排，不推所有地方官都罢免。',relation='adds')
add('guo_li_seeks_shi_family','郭威命李崇矩寻找史弘肇亲属，得知史弘福在世',2,'帝命史弘肇','弘福今存。”',[('郭威','命史弘肇旧亲吏李崇矩访亲属'),('李崇矩','向郭威报告史弘福仍在世'),('史弘福','被寻访确认在世'),('史弘肇','其亲属成为郭威访求对象')],when='951年正月即位初，具体寻访日未载',place='后周',note='上党为李崇矩籍贯，不当史弘福此时所在地；亲吏不是血亲关系。')
sup('guo_li_seeks_shi_family',2,song,'汝史氏家故吏也，為我求其近屬，吾將恤之。','《宋史》也记郭威请李崇矩寻找史弘肇近亲，表示要抚恤。','周祖指郭威，史氏家故吏说明履历，不据此造养子或亲属关系。')
relationship('史弘肇','史弘福','兄长',2,'弘肇弟弘福今存。','史弘肇是史弘福兄长，主书明弟；宋传母弟福作独立补证，具体父母不另推。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《宋史》记史弘福是史弘肇的同母弟弟。',2,'崇矩上其母弟福。','其母弟指史弘肇的弟弟福，不是李崇矩的弟弟；与通鉴弘肇弟弘福相互校核。',source=song)
add('li_chongju_prior_property_books','史弘肇此前让李崇矩掌管家产账册',2,'初，弘肇','家赀之籍，',[('史弘肇','让李崇矩掌家产账册'),('李崇矩','负责史弘肇家产账册')],year=None,when='史弘肇在世时的追述，具体委任年日未载',place='史弘肇家',note='账籍职务不推所有财产原本属于李崇矩；不强定951年已故者新委任。')
add('li_returns_shi_property','李崇矩将掌握的史弘肇家产全部交给史弘福',2,'由是尽得其产，','皆以授弘福。',[('李崇矩','将因掌账掌握的史氏家产全交给史弘福'),('史弘福','收到李崇矩交还的家产'),('史弘肇','其留下的家产被交给弟弟')],when='951年正月寻得史弘福后，具体交产日未载',place='后周',note='尽得其产可含控制掌握，不无证据定为已侵吞再返还；财产数量未载。')
sup('li_returns_shi_property',2,song,'崇矩素主其家，盡籍財產以付福，','《宋史》也记李崇矩原来管史家，将财产全部登记交给史弘福。','记录财产转交，不自行评定旧时占有的法律性质。')
add('guo_li_assigned_chai_rong','郭威赞赏李崇矩，令他转隶柴荣帐下',2,'帝贤之，',None,[('郭威','赞赏李崇矩，命其隶柴荣帐下'),('李崇矩','转隶柴荣帐下'),('荣','接收李崇矩任职')],when='951年正月交还史氏家产后，具体命令日未载',place='柴荣帐下',note='皇子荣沿既有柴荣、郭荣主体；未给任职名，不提前补显德年供奉官。')
sup('guo_li_assigned_chai_rong',2,song,'周祖嘉之，以崇矩隸世宗帳下。','《宋史》也记郭威赞赏李崇矩，令其隶世宗帐下。','世宗是对柴荣的后世称号，不说951年柴荣已是皇帝；后文显德供奉官不提前录。')
add('wang_yanchao_wuning_acting','郭威于戊辰命王彦超暂任武宁节度使',3,'戊辰，',None,[('郭威','任前复州防御使王彦超暂管武宁'),('王彦超','暂任武宁节度使')],when='951年正月戊辰',place='武宁',note='权为临时职掌，不写已永久正式授节度使；尚未攻下徐州。')
add('lady_li_moves_west_palace','后汉李太后迁居西宫',4,'汉李太后','迁居西宫，',[('汉李太后','迁居西宫')],when='951年正月己巳上尊号之前条下，具体迁居日未单列',place='西宫',note='迁居与上尊号同段但迁居未独给日，不强套己巳；不推西宫现代地址。')
add('lady_li_zhaosheng_title','郭威于己巳给李太后上昭圣皇太后尊号',4,'己巳，',None,[('郭威','给后汉李太后上昭圣皇太后尊号'),('汉李太后','获昭圣皇太后尊号')],when='951年正月己巳',place='后周朝廷',note='上尊号承前帝郭威，太后主体沿刘知远妻，不与后晋李氏皇后混用。')
sup('lady_li_zhaosheng_title',4,new,'己巳，上漢太后尊號曰昭聖皇太后。','《新五代史》也记己巳上汉太后尊号昭圣皇太后。','同日相符，名称展示简体、摘录保留繁体。',field='time_original')
add('liu_chengxun_dies','开封尹兼中书令刘承勋去世',5,'开封尹',None,[('刘勋','以开封尹兼中书令身份去世')],when='951年正月己巳尊号与癸酉加衔之间条下，具体死日未载',place='后周',note='刘勋沿950年开封尹刘承勋简称，不与刘承训或其他同名合并；该句未给死因，不以此前久病强作此句病死断言。')
claim('person',people['刘承勋'],'death_year','刘承勋于951年正月去世。',5,Q[5]['text'],'同职与950年刘承勋开封尹、兼中书令连贯；只将死亡年作为新引用，不覆盖旧档案。')
add('wang_jun_pingzhang','郭威于癸酉给王峻加同平章事衔',6,'癸酉，',None,[('郭威','给王峻加同平章事衔'),('王峻','获加同平章事')],when='951年正月癸酉',place='后周朝廷',note='加衔不写王峻此时离任枢密使；不混成六月范质李谷拜相。')
add('liu_hao_han_funeral','卫尉卿刘皞受命主持刘承祐丧事',7,'以卫尉卿',None,[('郭威','安排卫尉卿刘皞主持汉隐帝丧事'),('刘皞','以卫尉卿身份主持刘承祐丧事'),('刘承祐','丧事由刘皞主持')],when='951年正月癸酉加王峻官后条下，具体命令日未载',place='后周朝廷、汉隐帝丧事',note='主为主持，不能原字直接写主丧让读者猜；不同于950年郭命有司迁梓宫，尚未实际八月葬陵。')
claim('person',people['刘皞（后晋编敕官）'],'description','《旧五代史》记刘皞历任驾部员外郎兼侍御史、太府卿、宗正卿，周初转卫尉卿。',7,'清泰初，入為起居郎，改駕部員外郎，兼侍御史知雜事，移河南少尹、兵部郎中，轉太府卿。漢祖受命，用為宗正卿。周初，改衛尉卿。','同传连续历官衔接938年编敕官与951年卫尉卿，复用同一稳定主体；传首兄名句疑转录字保留，本批不新增兄弟关系。',source=career)
reviews={1:'授符诰、正式登基、国号自述、改元大赦、追赠葬事和访子孙、停附加收取与羡余、刑罚复旧和非反逆连坐限制、各陵守户分别录。晚唐、晋天福及后汉旧法追述年null，未混成951新法。周室后裔是诏制自述，不造远祖关系；旧制和奸范围与主概述区分。',2:'杨邠补军将幕职为此前追述，郭罢中央选补不是废全部同名地方职。访史亲、确认史福、兄长关系、原掌账、实际交家产和转隶柴荣分开；不把尽得其产断为侵吞，宋同母弟福校核。',3:'戊辰王彦超权武宁临时职掌，不写徐州已克或正式永久授职。',4:'迁西宫实际日未独列，己巳尊号主新同日；太后沿后汉刘知远妻。',5:'刘勋沿同官950刘承勋稳定主体，不并刘承训。死亡年951，未强套癸酉或据久病自行定病死。',6:'癸酉王峻加同平章事，未更改既有枢密使履历和强定实际独揽宰相权。',7:'卫尉卿刘皞与旧131历官链衔接938编敕官，复用人物；主持隐帝丧事不等于八月已下葬。传首句字疑不造新兄弟关系。'}
for row in B['events']:
 if row['key'].endswith('late_tang_theft_death_rule'):row['dynasty']='唐'
 elif row['key'].endswith(('jin_theft_five_pi_rule','jin_adultery_death_rule')):row['dynasty']='后晋'
 elif row['key'].endswith(('han_one_coin_theft_death','han_family_punishment_abuse','yang_bin_places_local_staff')):row['dynasty']='后汉'
assert not (P/'publication.json').exists()
for n in range(1,8):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,8)],next_paragraph=Q[8]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原6—12行连续七段；发布后首7/82正文完成，余75段待录，951年尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,8)],source_issues_review='晚唐、晋、汉刑法背景未给具体颁年，保留年null；主奸与旧制和奸范围区别明示。刘皞传官历支撑身份衔接，传首句兄名异字待核不据其造关系；宋传母弟福指史弘肇弟，周世宗为后世称号。已读原文、卷题及相邻段，纸本和转录异文待核。',plain_language_review='首次核对标题、正文、人物介绍、参与动作、亲属方向及对应事实说明，全部使用现代白话，引用原字保留。诏令和执行、政治谱系自述、追赠与死亡、追述旧法与951新措施分开；不安排固定发布后二次文案审阅。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
