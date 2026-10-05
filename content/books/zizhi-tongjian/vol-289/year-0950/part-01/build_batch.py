# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 1–7."""
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
COMMIT='aecd425b6a5c2b61245e92470190e94829f2d494'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-103-january-950-reports','jiuwudaishi-101-december-948']:
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
main_sources = ['tongjian-289-950-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p001-p007',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-289-950-opening':'卷289·乾祐三年·正月、二月及追述','songshi-261-guo-qiong-origin':'卷261·郭琼传·籍贯与早年','songshi-261-guo-qiong-han':'卷261·郭琼传·后汉任职'}
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
    labels={'tongjian-289-950-opening':'卷289·乾祐三年·正月、二月及追述','songshi-261-guo-qiong-origin':'卷261·郭琼传·籍贯与早年','songshi-261-guo-qiong-han':'卷261·郭琼传·后汉任职'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年正月、二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_01_{len(B["claims"])+1:04d}'
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

ALIASES.update({'帝':'刘承祐','唐主':'李璟','弘冀':'李弘冀'})
NEW_ALIASES={'郭琼':['郭瓊']}
NEW_DESCRIPTIONS={'郭琼':'后汉将领，曾任沂州刺史。950年正月奉命担任东路行营都部署，率禁军和齐州兵支援王万敢。《宋史》郭琼传记其为平州卢龙人，但对密州战事的叙述与通鉴不同，分别保留。生卒年尚未核。'}
jan='jiuwudaishi-103-january-950-reports'; birthday='jiuwudaishi-101-december-948'; origin='songshi-261-guo-qiong-origin'; guohan='songshi-261-guo-qiong-han'
add('zhao_hui_shizhong','后汉给凤翔节度使赵晖加兼侍中',1,'春，正月，',None,[('赵晖','以凤翔节度使身份加兼侍中')],when='950年正月丁未',place='后汉朝廷、凤翔',note='加兼侍中为官衔，不写成赵晖已离开凤翔、入朝担任实际宰相。')
sup('zhao_hui_shizhong',1,jan,'丁未，鳳翔節度使、充西南行營都部署趙暉加兼侍中。','《旧五代史》同样记正月丁未赵晖加兼侍中，并列西南行营都部署身份。','同一纪日和任命，补充官职称谓，不拆成两次加官。')
add('wang_wangan_requests_reinforcement','王万敢请求增兵攻打南唐',2,'密州刺史王万敢','以攻唐。',[('王万敢','请求增兵攻打南唐')],when='950年正月，主书未单列纪日',place='密州及后汉朝廷',note='请求增兵不等于增兵已经到达，也不预定攻击结果。')
sup('wang_wangan_requests_reinforcement',2,jan,'戊申，密州刺史王萬敢奏，奉詔領兵入海州界，至荻水鎮，俘掠焚蕩，更請益兵。','《旧五代史》把王万敢请求增兵的奏报记在正月戊申，奏报还提到海州荻水镇的俘掠与焚烧。','戊申是奏报日期，不能当作此前攻击荻水镇的确切日期；主书949年获水镇攻击是否同次仍待核。',relation='adds',field='time_original')
add('guo_qiong_deployment','后汉命郭琼率禁军与齐州兵支援王万敢',2,'诏以',None,[('刘承祐','下诏任郭琼为东路行营都部署'),('郭琼','奉命率禁军和齐州兵支援王万敢'),('王万敢','将获得郭琼所率部队支援')],when='950年正月，王万敢请求增兵后',place='后汉朝廷、齐州及海州方向',note='帅为率领，部署指统军职务。诏命与实际行军、到达和战果区分。')
sup('guo_qiong_deployment',2,jan,'詔前沂州刺史郭瓊率禁軍赴之。','《旧五代史》也记后汉命前沂州刺史郭琼率禁军前往。','姓名繁简统一，主书另列齐州兵及都部署职务，不凭略写认定书证互相否定。')
sup('guo_qiong_deployment',2,jan,'前沂州刺史郭瓊奏，部署兵士，深入海州賊界。','《旧五代史》同月另记郭琼奏报已率部深入海州境内。','这是同月的执行补充，原文未单列奏报纪日，不强系丙寅，也不提前合并二月回军的记载。',relation='adds')
sup('guo_qiong_deployment',2,guohan,'漢乾祐中，淮人攻密州，以為行營都部署，未至，淮人解去。','《宋史》郭琼传记乾祐年间南唐军攻密州，郭琼任行营都部署；他尚未到达，南唐军已撤走。','该传概述未列年份，攻守方向、到达情况与通鉴及旧史正月叙述有差别，尚未认定就是同次行动。不得据此抹去旧史深入海州的奏报。',relation='conflicts')
claim('person',people['郭琼'],'description','《宋史》郭琼传记郭琼是平州卢龙人。',2,'郭瓊，平州盧龍人。','回查卷261传主和上下文；只补籍贯身份，不把其早年仕契丹和归唐经历放在950年。',source=origin)
add('guo_wei_requests_border_march','郭威请求率兵到契丹边境',3,'郭威请','契丹之境，',[('郭威','请求率兵到契丹边境')],when='950年正月，具体日未载',place='后汉与契丹边境',note='请求临边不等于已经越境开战，不把后文二月巡边返回提前当本句的执行结果。')
add('han_stops_guo_border_march','后汉朝廷制止郭威此次率兵临边的请求',3,'郭威请',None,[('郭威','率兵临边的请求被制止'),('刘承祐','下诏制止郭威此次请求')],when='950年正月，具体日未载',place='后汉朝廷',note='诏止只对应此次请求，不扩大成郭威此后被禁止所有巡边活动。')
add('han_collects_war_remains','后汉派使者收葬河中、凤翔的战死者和饿死者遗骸',4,'丙寅，','遗骸，',[('刘承祐','派使者赴河中、凤翔收葬遗骸')],when='950年正月丙寅',place='河中、凤翔',note='收瘗指收葬遗骸，未列使者姓名和实际完成数；死者包括战死与饿死者。')
sup('han_collects_war_remains',4,jan,'丙寅，分命使臣赴永興、鳳翔、河中，收葬用兵已來所在骸骨。','《旧五代史》同日记收葬，并把永兴也列入使者前往地点。','保留两书记载的范围差异，永兴为该书补充，不改写通鉴原地点。',relation='adds',field='location_name')
add('monks_collect_remains','史书记僧人已收集大量遗骸',4,'时有僧',None,[],year=None,when='950年正月丙寅收葬诏令时，已完成收集；起始时间未载',place='河中、凤翔战区，具体收集地点未载',note='二十万为史书所记数量，主书未交代统计方法或每具归属；不当作单场战役死亡人数，也不凭时有认定僧人当天才开始收集。')
sup('monks_collect_remains',4,jan,'時已有僧聚髑髏二十萬矣。','《旧五代史》具体写僧人已收集二十万头骨。','髑髏为头骨，通鉴写遗骸；两书表述保留，未经统计校核，不展示为已独立确证的总死亡人数。',relation='adds')
add('li_jinquan_command_removed','李璟得知后汉平定三镇叛乱后，撤销李金全的北面招讨职务',5,'唐主闻',None,[('李璟','得知后汉平定三镇后，撤销李金全招讨职务'),('李金全','不再担任北面行营招讨使')],when='950年正月条下，具体日未载',place='南唐朝廷',note='三叛对应此前李守贞、赵思绾、王景崇三镇，罢只指本句所列职务，不写成李金全所有官职都被撤销。')
add('liu_yanzhen_extortion_bribery','史书记刘彦贞搜敛民财，贿赂权贵',6,'唐清淮','以赂权贵，',[('刘彦贞','任清淮节度使期间搜敛民财，贿赂权贵')],year=None,when='刘彦贞长期任职寿州期间的追述，具体起止未载',place='寿州及南唐权贵所在',note='多敛与贿赂为史书指述，未列数额、受贿者名单或每次行为日期，不一律认定发生在950年二月。')
add('powerful_praise_liu_yanzhen','史书记受贿权贵争相称赞刘彦贞',6,'唐清淮','权贵争誉之。',[('刘彦贞','因贿赂权贵而被他们争相称赞')],year=None,when='刘彦贞长期任职寿州期间的追述，具体起止未载',place='南唐',note='权贵未具名，不补宋齐丘等人的参与，史书所叙关联不外推其他人的动机。')
add('liu_yanzhen_false_alarm','刘彦贞担心被调任，虚报后汉将大举南征',6,'在寿州积年，','南伐。',[('刘彦贞','为保住职务，虚报后汉将大举南征')],year=None,when='950年二月南唐人事调整前，具体奏报年月未载',place='寿州、南唐朝廷',note='妄奏为史书对奏报的判断，不把所报后汉大举南征写成已发生的军事行动。')
add('li_hongji_runxuan_command','李璟任命李弘冀为润、宣二州大都督，驻润州',6,'二月，','镇润州，',[('李璟','任命李弘冀为润、宣二州大都督'),('李弘冀','以燕王、东都留守身份改任润、宣二州大都督，驻润州')],when='950年二月，具体日未载',place='润州、宣州',note='弘冀沿已有李弘冀主体，原文没有再次册封燕王，不另造本月封王事件。')
add('zhou_zong_eastern_capital','李璟任命周宗为东都留守',6,'二月，',None,[('李璟','任命周宗为东都留守'),('周宗','以宁国节度使身份改任东都留守')],when='950年二月，具体日未载',place='南唐东都',note='保留东都史载名称，不把本句未写的实际到任日或现代地址补入。')
add('han_allows_birthday_audience','后汉准许藩镇将领入朝为嘉庆节祝寿',7,'朝廷欲',None,[('刘承祐','准许请求入朝祝寿的藩镇将领来朝')],when='950年二月条下，具体日未载',place='后汉朝廷及各藩镇',note='朝廷欲移易藩镇为调整意图，许之是准许入朝；具体来朝名单与实际调任在后文录入，不提前写成全部将领已到京师。')
claim('event',E['han_allows_birthday_audience'],'description','后汉朝廷打算调整藩镇任职，借将领请求入朝祝寿的机会准许来朝。',7,Q[7]['text'],'移易为任职调整意图，不是疆域改变；本段尚未列已执行的调任。')
claim('event',E['han_allows_birthday_audience'],'time_original','嘉庆节是后汉为皇帝生日设立的节日，《旧五代史》记其为三月九日。',7,'辛卯，群臣上表，請以三月九日誕聖日為嘉慶節。從之。','该句来自948年设节记载，仅用于解释嘉庆节；950年二月允准与三月实际庆贺分别录，不把948年辛卯改为950年纪日。',source=birthday)
reviews={1:'加兼侍中保存官衔，不推任实际宰相或离镇；旧史同日印证。',2:'请求、诏命和旧史同月执行奏报区分；戊申是王万敢奏报日，不定此前海州行动日。郭琼姓名、旧任、宋史籍贯核对；宋史密州攻守及到达概述不同，独立保留未强认同役，后年青州活动未提前录。',3:'郭威请求与诏令制止分开；不推已越境开战或终身禁巡边，后文返回另录。',4:'收葬诏令与已有僧收集遗骸分开，僧人收集起始不明；二十万是史书记数，不当成单战精确死亡统计。旧史增永兴与髑髅表述保留。',5:'撤销李金全北面招讨职务，不推所有官职皆罢；三叛仅解释此前三镇。',6:'刘彦贞积年搜敛、贿赂与虚报为追述，不强系本月；权贵未具名。李弘冀、周宗二月任命分录，原衔不写成本月新增册封。',7:'后汉意图调整任职与允许入朝分开；未提前写成三月已来朝或全部调任完成。旧史948年嘉庆节设立仅补节日解释，不移其年份。'}
assert not (P/'publication.json').exists()
for n in range(1,8):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,8)],next_paragraph=Q[8]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原6—12行连续七段，从950年正月加赵晖侍中至二月准藩镇来朝。后续76正文仍待录；来源快照含后文只用于原文定位，不表示其余段已录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,8)],source_issues_review='宋史郭琼传乾祐密州战事与通鉴及旧史正月海州叙述有差别，未强认同役。主书获水与旧史荻水待核，奏报日不是行动日。二十万遗骸、髑髅为史书记数，未有独立统计；旧史多列永兴。新五代史检索到刘彦贞后周征淮记载，但时段在后年，未作950年独立证据。纸本及转录异文待核。',plain_language_review='首次逐条检查标题、人物介绍、角色、时间地点与事实解释。明确朝廷所指及人名，区分奏请、诏命、实施、追述、虚报和史家数字。展示简体，原字不改；未知年份保留null，复用主体保持原档案。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
