# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 43–47."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,84))
COMMIT='16c0f5a86200a69c1b027a44e1cd6ceca86246f5'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-november-start','jiuwudaishi-103-november-950','jiuwudaishi-103-october-950']:
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
main_sources = ['tongjian-289-950-november-start','tongjian-289-950-ministers-conspiracy','tongjian-289-950-assassination-orders']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p043-p047',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
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
lines = (ROOT / 'resources/derived/tongjian/289.txt').read_text().splitlines()
for n in range(43, 48):
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
    labels={'jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十一月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_07_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=950, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='950年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_289_0950_' + code
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
        edge = 'participation_zztj_289_0950_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_289_0950_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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







ALIASES.update({'帝':'刘承祐','太后':'李氏（刘知远妻）','弘肇':'史弘肇','邠':'杨邠','章':'王章','业':'李业','文进':'聂文进','匡赞':'后匡赞','允明':'郭允明','王殷':'王殷（后汉后周将）','郭崇威':'郭崇威'})
NEW_ALIASES={'李业':['李業'],'聂文进':['聶文進'],'耿氏（刘承祐宠妃）':['耿夫人'],'孟业':['孟業'],'李洪义':['李洪義'],'曹威':[],'李洪建':[]}
NEW_DESCRIPTIONS={
'李业':'后汉李太后的弟弟，任武德使，刘知远时掌内库，刘承祐即位后受到宠信。950年与刘承祐等策划诛杀杨邠等大臣。出生与死亡年本批未录。',
'聂文进':'并州人，后汉枢密承旨，受到刘承祐宠信。950年参与诛杀大臣的谋划，在杨邠等被杀后召朝臣宣布其谋反。生卒年本批未录。',
'耿氏（刘承祐宠妃）':'受到后汉刘承祐宠爱的耿夫人。刘承祐想立她为皇后，杨邠认为过急；她死后，刘承祐想按皇后礼安葬，杨邠又反对。姓名、生卒年及正式册立结果未载。',
'孟业':'后汉供奉官。950年奉刘承祐命携带密诏前往澶州和邺都，传达杀王殷、郭威及王峻等人的命令。生卒年未载。',
'李洪义':'后汉李太后的弟弟，950年任镇宁节度使。刘承祐下密诏令他杀驻澶州的王殷，本段只记命令，未记他已经执行。生卒年未载。',
'曹威':'真定人，950年任邺都行营步军都指挥使。刘承祐密令他与郭崇威杀郭威及监军王峻，本段尚未记实际执行。生卒年未载。',
'李洪建':'李业的兄长，950年任侍卫马军都指挥使，后暂判侍卫司相关事务。收到杀王殷家属的命令后，只派人看守并继续供给饮食。生卒年未载。'}
finance='jiuwudaishi-107-wang-zhang-finance';oldchron='jiuwudaishi-103-november-950';newchron='xinwudaishi-010-han-court-killings'
def back(code,title,start,end,actors,note,description=None):
 return add(code,title,44,start,end,actors,year=None,when=('刘知远在世至刘承祐即位后的追述，具体任职年月未载' if code=='li_ye_manages_treasury' else '刘承祐即位后至950年十一月之前的追述，具体发生年月未载'),place='后汉',note=note,description=description)
add('wang_lingwen_tanzhou_plan','后汉拟派王令温救潭州，因内乱未能出兵',43,'朝廷议发兵',None,[('刘承祐','朝廷在其统治下筹议援楚'),('王令温','拟任援潭州军都部署')],when='950年十一月条下，诛杀大臣的内乱前后，具体议兵日未载',place='后汉朝廷、拟援潭州',note='以为都部署与救潭州计划关联，内难导致不果，不写成军队已抵潭州。')
sup('wang_lingwen_tanzhou_plan',43,'jiuwudaishi-103-october-950','時朝廷方議起軍，會內難，不果行。','《旧五代史》也记朝廷议兵援助湖南，遇内乱未成行。','在十月求援之后补述结果，没有王令温姓名；不能作为其任命的独立确证。')
back('four_ministers_duties','刘承祐即位后，杨邠、郭威、史弘肇和王章分掌要务','帝自即位以来，','王章掌财赋。',[('杨邠','以枢密使、右仆射、同平章事总掌机政'),('郭威','以枢密使兼侍中主掌征伐'),('史弘肇','以归德节度使等身份统率宿卫'),('王章','以三司使、同平章事掌管财赋')],'这是即位以来职掌概述，不造950年十一月四人同时初次任命。')
claim('person',people['杨邠'],'description','《资治通鉴》评价杨邠颇为公忠，记他不接待私下请托者，将馈赠余物献给朝廷。',44,span(44,'邠颇公忠，','有馀辄献之。'),'公忠为史书评价，不说从不收礼；原文明确虽不却四方馈遗。')
claim('person',people['史弘肇'],'description','《资治通鉴》以道不拾遗描述史弘肇督察京城后的秩序。',44,'弘肇督察京城，道不拾遗。','道不拾遗是史书的概括评价，不作为犯罪率为零的统计。')
back('wang_zhang_war_finance','王章节制开支、搜集财赋，维持三镇战争中的军需','是时承契丹','以是国家粗安。',[('王章','收聚财赋、节制出纳，供给长期驻军')],'三叛战争与战后积余属追述，不另造950年开始三叛；国家粗安为书中判断，不推民生全面改善。')
sup('wang_zhang_war_finance',44,finance,'軍旅所資，供饋無乏。及三叛平，賜與之外，國有餘積。','《旧五代史》也记西征军需不缺，三叛平定后赏赐之外仍有积余。','财政积余与后文过重征敛并列，不写成各阶层一致受益。')
back('wang_zhang_grain_surcharge','王章将每斛田税的附加耗粮从二升增至二斗','旧制，田税','谓之“省耗”；',[('王章','提高田税附加耗粮，称为省耗')],'原文给旧新单位，保留斛、升、斗，不换算现代重量或直接把附加粮当全部田税。')
sup('wang_zhang_grain_surcharge',44,finance,'乾祐中，輸一斛者，別令輸二斗，目之爲「省耗」。百姓苦之。','《旧五代史》将省耗措施记在乾祐年间，并说百姓受其困扰。','乾祐年间未定具体一年，不强系950年十一月。',relation='adds',field='time_original')
back('wang_zhang_cash_account','王章规定钱款收入八十为陌、支出七十七为陌','旧钱出入','谓之“省陌”；',[('王章','改变官府钱款支出的折算标准')],'台令保留原字，按本句主语王章解释；陌是计钱标准，不直接写成现代汇率或所有交易皆用此制。')
sup('wang_zhang_cash_account',44,finance,'至是民輸者如舊，官給者以七十七爲陌，遂爲常式。','《旧五代史》也记民众缴纳仍用旧标准，官府给付用七十七为陌。','正文措施与引《归田录》的后世市井情况分开，不将后世依除追溯为王章本段措施。')
back('wang_zhang_prohibition_penalty','史书记王章对盐、曲、酒曲禁令施用极刑','有犯盐、','由是百姓愁怨。',[('王章','对少量违禁也处以死罪')],'引文麹字和盐麹酒麹的列项原样保留，疑似转录重复待核；不据此构造具体被处死个案。')
sup('wang_zhang_prohibition_penalty',44,finance,'民有犯鹽礬酒曲之令，雖絲毫滴瀝，盡處極刑。','《旧五代史》写盐、矾、酒曲禁令，称少量违禁也用极刑。','《资治通鉴》电子本盐、麹、酒麹与此列项不同，可能涉及转录或异文，原字保留，纸本待核。',relation='conflicts')
back('wang_zhang_dislikes_scholars','王章轻视文臣的财计能力，讥讽其不会计算','章尤不喜文臣，','何益于用！”',[('王章','以不会计算为由讥讽文臣')],'是王章被记载的意见，不当作所有文臣实际无计算能力。')
back('wang_zhang_salary_valuation','王章以不能用于军需的物品发俸，并进一步提高估价','俸禄皆以','章更增之。',[('王章','使用闲置物品发俸，并提高所计价值')],'估价增加使实物给付价值与名义俸额不同，未提供具体幅度；不说俸禄完全停发。')
sup('wang_zhang_salary_valuation',44,finance,'郡官所請月俸，皆取不堪資軍者給之，謂之「閑雜物」，命所司高估其價，估定更添，謂之「擡估」，','《旧五代史》称此类发俸物品为闲杂物，提高估价为抬估。','补充称谓，未给准确实行日或涨价比例。',relation='adds')
back('ministers_restrain_favorites','杨邠等大臣多次抑制皇帝亲信与太后亲戚干政','帝左右嬖倖','邠等屡裁抑之。',[('杨邠','参与抑制亲信与外戚干预朝政')],'多人长期冲突概述，不造每一次具体奏议，也未把所有太后亲属归为同谋。')
back('shi_kills_lady_friend_son','史弘肇杀死求军职的太后故人之子','太后有故人子','弘肇怒而斩之。',[('太后','有故人之子求补军职'),('弘肇','因求军职之事发怒，杀死此人')],'故人之子没有姓名，不创建有名人物或虚构罪名；具体杀人年月未载。')
back('li_ye_manages_treasury','李业在刘知远时掌内库，后来受到刘承祐宠信','武德使李业，','尤蒙宠任。',[('李业','任武德使，曾奉刘知远命管理内库')],'高祖指刘知远，帝即位指刘承祐，前后时期分清；不是950年十一月初次任职。')
relationship('李氏（刘知远妻）','李业','姐姐',44,'武德使李业，太后之弟也，','太后之弟说明李氏是李业的姐姐，沿既有后汉李太后身份，不能混后晋李太后。')
back('li_ye_xuanhui_blocked','李业想任宣徽使，杨邠与史弘肇以迁补次序阻止','会宣徽使阙，','乃止。',[('李业','希望补宣徽使缺额'),('帝','与太后向执政者示意支持'),('太后','向执政者示意支持弟弟'),('杨邠','反对外戚越次补职'),('弘肇','与杨邠共同反对')],'请求与支持未获落实，不生成李业已任宣徽使的履历。')
back('yan_jinqing_waits_promotion','阎晋卿按次序应补宣徽使，却长期未获补授','内客省使阎晋卿','久而不补。',[('阎晋卿','按次序等待补授宣徽使')],'次当不等于已经任命，不补等待起止年月。')
back('favorites_resent_ministers','聂文进、后匡赞和郭允明因长期未迁官怨恨执政者','枢密承旨聂文进','文进，并州人也。',[('文进','任枢密承旨，受宠而未迁官'),('匡赞','任飞龙使，受宠而未迁官'),('允明','任翰林茶酒使，受宠而未迁官')],'并州籍贯单指聂文进，不推另两人籍贯；共同怨恨不当作本句已成立正式谋杀组织。')
back('liu_zhu_resent_ministers','刘铢罢青州归朝后未获新职，多次指骂执政者','刘铢罢青州归，','常戟手于执政。',[('刘铢','归朝后长期未除新官，对执政者不满')],'朝请是入朝活动，不说明失去一切待遇；戟手解释为指骂，不造武器攻击。')
back('emperor_rewards_performers','刘承祐结束三年丧期后听乐，赏伶人锦袍玉带','帝初除三年丧，','玉带。',[('帝','丧期结束后听乐并赏赐伶人')],'三年丧为礼制称谓，不机械换算满三十六个月；伶人未具名，不创建演员人物。')
back('shi_reclaims_performer_rewards','史弘肇斥责伶人无功受赏，收回锦袍玉带归官','伶人诣弘肇谢，','皆夺以还官。',[('弘肇','以边军未获赏赐为由，收回伶人的赏赐')],'史弘肇的话为其主张，未作为边军历来从未受赏的全称判断。')
back('geng_queen_proposal','刘承祐想立耿夫人为皇后，杨邠认为过急','帝欲立所幸耿夫人','邠以为太速。',[('帝','打算立宠爱的耿夫人为皇后'),('杨邠','认为册立太快'),('耿氏（刘承祐宠妃）','成为拟册立皇后的对象')],'欲立为计划，未认定已经正式册立皇后。')
back('geng_death_burial_dispute','耿夫人去世后，刘承祐拟用皇后葬礼，杨邠反对','夫人卒，','邠复以为不可。',[('耿氏（刘承祐宠妃）','去世，具体年份未载'),('帝','希望按皇后礼安葬'),('杨邠','反对使用皇后葬礼')],'死亡时间属于追述，未填950年死年；拟用后礼不等于实际按后礼下葬。')
back('emperor_yang_silence_dispute','刘承祐不满大臣控制，杨邠议政时让他不必发言','帝年益壮，','有臣等在。”',[('帝','对受大臣控制不满，议政时被要求禁声'),('杨邠','在皇帝前议事，回答让皇帝禁声'),('弘肇','与杨邠共同议事')],'记载对话与史书心理描述，未造具体议政议题或确日。')
claim('event',E['emperor_yang_silence_dispute'],'description','《资治通鉴》随后记刘承祐难以平息积怨。',44,'帝积不能平，','对应前面的禁声对话，分段快照跨界，另引下一处原文，不拼接伪造连续摘录。')
back('favorites_accuse_ministers','皇帝近侍称杨邠等将乱，刘承祐相信指控','左右因乘间','帝信之。',[('帝','相信近侍关于大臣将作乱的指控')],'近侍未在这句逐一具名，不能把将乱当独立确认事实。')
back('emperor_fears_forging_noise','刘承祐夜闻作坊锻造声，疑有急兵而整夜不眠','尝夜闻作坊','达旦不寐。',[('帝','因夜间锻造声疑虑兵变，整夜不眠')],'疑有急兵是恐惧，不等于作坊实际制造叛乱兵器；日期未知。')
back('su_stirs_li_ye','苏逢吉因与史弘肇有隙，多次用言语刺激李业等','司空、同平章事苏逢吉','屡以言激之。',[('苏逢吉','以言语激化李业等对史弘肇的不满'),('李业','被苏逢吉言语刺激')],'挑动矛盾不直接证明参与具体谋杀方案；后段明确苏逢吉不预其谋。')
add('emperor_plots_three_killings','刘承祐与李业等商定诛杀杨邠等大臣',44,'帝遂与业、','议既定，',[('帝','与亲信商定诛杀大臣'),('李业','参与商定诛杀计划'),('文进','参与谋划'),('匡赞','参与谋划'),('允明','参与谋划')],when='950年十一月乙亥告知阎晋卿之前，具体商定日未载',place='后汉宫廷',note='谋划与次日实际杀人分开，未在此处填死亡结果。')
add('han_lady_warns_plot','李太后要求与宰相商议，刘承祐与李业拒听劝告',44,'入白太后。','拂衣而出。',[('帝','把计划告知太后，听劝后发怒离开'),('太后','两次劝勿轻发，要求与宰相商议'),('李业','引述先帝说法，反对与文臣商议')],when='950年十一月，诛杀计划商定之后、乙亥告知阎晋卿之前',place='后汉宫廷',note='先帝所言是李业当时引述，不另造刘知远说过此话的有确日事件；太后劝止，不列为赞成诛杀者。')
add('yan_warns_shi_failed','阎晋卿获知计划后想向史弘肇告警，未能见到',44,'乙亥，',None,[('李业','等人把诛杀计划告诉阎晋卿'),('阎晋卿','担心计划不成，去史弘肇宅欲告警'),('弘肇','因别的事情辞谢不见')],when='950年十一月乙亥',place='史弘肇宅',note='欲告没有成功见面，不写史弘肇已知计划，也未补其辞见原因。')
add('three_ministers_killed','杨邠、史弘肇和王章入朝时被甲士杀死',45,'丙子旦，','杀邠、弘肇、章于东庑下。',[('杨邠','清晨入朝被甲士杀死'),('弘肇','清晨入朝被甲士杀死'),('王章','清晨入朝被甲士杀死')],when='950年十一月丙子清晨',place='宫中东庑下，甲士自广政殿出',note='甲士数十为书载概数，未具名，不补每人的亲手杀害者。')
sup('three_ministers_killed',45,oldchron,'丙子，誅樞密使楊邠、侍衛都指揮使史宏肇、三司使王章，夷其族。','《旧五代史》同日记诛杀杨邠、史宏肇、王章并灭族。','宏肇沿已有同人别字，不新建史宏肇；灭族结果另关联后续搜捕事件。')
sup('three_ministers_killed',45,newchron,'冬十一月丙子，殺楊邠及侍衞親軍都指揮使史弘肇、三司使王章，皆滅其族。','《新五代史》也记十一月丙子杀三臣并灭族。','此处只取对应句，后面的郭威起兵、刘承祐死亡尚未按游标读到，不提前录入。')
for name in ['杨邠','史弘肇','王章']:
 claim('person',people[name],'death_year',name+'于950年十一月丙子入朝时被杀。',45,span(45,'丙子旦，','杀邠、弘肇、章于东庑下。'),'补充死亡事实引用，复用主体与旧档案，不覆盖此前记录。')
add('nie_announces_treason','聂文进召朝臣，宣称三位大臣谋反已伏诛',45,'文进亟召','与卿等同庆！”',[('文进','在崇元殿向朝臣宣布三臣谋反被诛')],when='950年十一月丙子，三臣被杀之后',place='崇元殿',note='谋反是当时宣告的罪名，不因宣告认定三臣确实谋反。')
add('emperor_addresses_commanders','刘承祐召军将与旧任州镇官，宣称自己开始亲掌权力',45,'又召诸军将校','升殿谕之，',[('帝','向军将讲话，随后召旧任节度使、刺史宣谕')],when='950年十一月丙子',place='万岁殿庭及宫殿',note='军将拜谢是所载仪式，不推所有将领真心拥护；两次召见分对象保留，未具名者不补人名。')
add('ministers_families_killed','刘承祐遣使搜捕并杀死三臣亲属、党与和随从',45,'分遣使者',None,[('帝','分派骑兵使者搜捕诛杀关联人员'),('杨邠','亲属党与被搜捕杀害'),('弘肇','亲属党与被搜捕杀害'),('王章','亲属党与被搜捕杀害')],when='950年十一月丙子，三臣被杀之后',place='后汉京师，具体各处未载',note='尽杀为书载范围，不虚构人数或逐个未具名家属；傔从为随从。')
claim('person',people['史弘肇'],'description','《资治通鉴》记史弘肇平日对侍卫步军都指挥使王殷特别优厚。',46,'弘肇待侍卫步军都指挥使王殷尤厚，','优厚不自动推为血亲、结义或密谋同党；王殷复用后汉后周将。')
add('meng_ye_carries_orders','刘承祐派孟业持密诏赴澶州和邺都',46,'邠等死，','诣澶州及鄴都，',[('帝','派供奉官孟业传送密诏'),('孟业','携密诏前往澶州及邺都')],when='950年十一月丙子诛杀三臣之后，具体发遣时刻未载',place='京师至澶州、邺都',note='发遣不是已抵达，两地到达和如何处置在后段另录。')
add('order_kill_wang_yin','刘承祐密令李洪义杀驻澶州的王殷',46,'令镇宁节度使','杀殷，',[('帝','下达杀王殷的密令'),('李洪义','被命杀王殷'),('王殷','成为密令杀害的对象')],when='950年十一月丙子之后的密诏，具体时刻未载',place='澶州',note='只有命令，本段尚未执行，不填王殷死亡。')
relationship('李氏（刘知远妻）','李洪义','姐姐',46,'洪义，太后之弟也。','后汉李太后是李洪义姐姐；不与李业自动合并，原文分别具名。')
add('order_kill_guo_wang_jun','刘承祐密令郭崇威与曹威杀郭威、王峻',46,'又令鄴都行营','王峻。',[('帝','命郭崇威与曹威杀郭威及王峻'),('郭崇威','被密令杀郭威等'),('曹威','以真定籍步军都指挥使身份受密令'),('郭威','被列为密令目标'),('王峻','以监军、宣徽使身份被列为目标')],when='950年十一月丙子之后的密诏，具体时刻未载',place='邺都',note='曹威与郭威不同人；命令不等于执行成功，本段不填两人死亡。')
add('emperor_recalls_seven_governors','刘承祐急召高行周等七位州镇官入朝',46,'又急诏征','李谷入朝。',[('帝','急诏召七位州镇官入朝'),('高行周','以天平军节度使身份被召'),('符彦卿','以平卢节度使身份被召'),('郭从义','以永兴节度使身份被召'),('慕容彦超','以泰宁节度使身份被召'),('薛怀让','以匡国节度使身份被召'),('吴虔裕','以郑州防御使身份被召'),('李谷','以陈州刺史身份被召')],when='950年十一月丙子之后，具体诏下时刻未载',place='后汉各州镇至京师',note='召命不等于七人已同日抵京；各职名来自本句，不补行程。')
for code,name,title,start,end in [('su_temporary_privy','苏逢吉','暂管枢密院事务','以苏逢吉','权知枢密院事，'),('liu_zhu_kaifeng','刘铢','暂管开封府','前平卢节度使刘铢','权知开封府，'),('li_hongjian_guard','李洪建','暂判侍卫司事务','侍卫马军都指挥使李洪建','权判侍卫同事，'),('yan_temporary_cavalry','阎晋卿','暂任侍卫马军都指挥使','内侍省使阎晋卿','权侍卫马军都指挥使。')]:
 add(code,'刘承祐令'+name+title,46,start,end,[('帝','作出临时职务安排'),(name,title)],when='950年十一月丙子之后，具体任命时刻未载',place='后汉朝廷',note='权为临时代理，未改写成永久升任；原职名与电子本异字保留，官制细节待核。')
relationship('李洪建','李业','兄长',46,'洪建，业之兄也。','李洪建是李业的兄长，方向清楚，不据此推精确年龄差。')
sup('yan_temporary_cavalry',46,oldchron,'內客省使閻晉卿權侍衛馬軍都指揮使。','《旧五代史》也记阎晋卿暂任侍卫马军都指挥使，原职写内客省使。','《资治通鉴》此处写内侍省使，与其上文内客省使及旧本纪不同，原字保留，身份沿同一阎晋卿，原职异文待核。',relation='conflicts')
add('su_shocked_unconsulted','苏逢吉得知杀戮后惊愕，称皇帝若询问就不会如此',47,'时中外人情忧骇，','不至于此。”',[('苏逢吉','得知变故后惊愕，私下说未被问及')],when='950年十一月丙子诛杀三臣之后，具体发言时刻未载',place='后汉京师，私下发言处未载',note='《资治通鉴》明确他虽厌恶史弘肇而未参与李业等具体计划，与此前挑动矛盾分开；此处是史书叙述和私话，非司法认定。')
add('liu_zhu_kills_guo_wang_families','李业等命刘铢杀郭威、王峻家属，幼童亦未能幸免',47,'业等命刘铢','婴孺无免者。',[('李业','等人下令杀郭威、王峻家属'),('刘铢','执行命令，连幼童也杀害'),('郭威','家属成为杀戮对象'),('王峻','家属成为杀戮对象')],when='950年十一月，三臣被杀后的内乱中，具体执行日未载',place='后汉京师家属所在处，具体地址未载',note='本句未具名家属不补名单，未以极其惨毒一句猜测具体刑法或数字。')
add('li_hongjian_spares_wang_family','李洪建受命杀王殷家属，却只派人看守并供给饮食',47,'命李洪建',None,[('李洪建','没有按杀人命令执行，派人看守并供给饮食'),('王殷','家属被看守并获饮食')],when='950年十一月，三臣被杀后的内乱中，具体处置日未载',place='王殷家属所在处，具体地址未载',note='命令者承接李业等而未逐一列人；家属此时免杀，不推永久安全或后续所有人的结局。')
reviews={43:'筹援潭州而内乱未行，不将王令温拟任都部署写成已经出兵抵达。旧本纪补失败结果但不补姓名。',44:'即位以来职掌、财政制度、外戚亲信矛盾和耿夫人死葬等为追述，未知年用null。请求或拟册立不是已任命，指控不是事实；财计数字保留单位，盐麹酒麹与旧传盐矾酒曲异文待核。太后劝止、苏挑动与谋杀具体参与分清；乙亥告警未见，不写已成功通知。',45:'丙子诛杀三臣、宣称谋反、对军将宣谕、搜杀家属分开。谋反为宣告，不作独立确证；新旧本纪同日补证，数十甲士和关联家属不造名单。',46:'密诏发遣、杀人命令、召官与临时职掌分开，不提前录执行或抵京。郭崇威沿既有主体，后周王殷与晚唐同名分开；李洪义太后弟、李洪建李业兄关系有向。阎晋卿原职内侍省内客省异文保留。',47:'苏逢吉未参与李业具体谋划的主书叙述与此前挑动矛盾分清，未推无罪司法结论。刘铢杀家属和李洪建守视供食相反结果分开，未具名婴孺不造名单。'}
assert not (P/'publication.json').exists()
for n in range(43,48):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(43,48)],next_paragraph=Q[48]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原48—52行连续五段，其中原49行含君臣长期矛盾与财政追述；发布后首47/83正文已录，余36段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(43,48)],source_issues_review='长段按原始段落维持账本，库分段快照分三处逐字引用。财政禁令列项、阎晋卿原职异文保留；苏逢吉是否参与具体密谋以通鉴此段未预为本条说明，其他后续罪状记载不提前反写。纸本与转录异文待核。',plain_language_review='首次逐条自查现代白话、人物身份、关系方向、时间及原文；追述unknown年用null，指控、诏命、意图与实际结果明确分开。引用原字保留，不把工作简称写入展示字段。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
