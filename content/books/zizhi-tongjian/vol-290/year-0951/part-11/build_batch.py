# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 77–82."""
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
COMMIT='05c8382e0d397e9dac6d60dfa83048d6aa2e8137'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-951-year-end','jiuwudaishi-112-december-expedition','xinwudaishi-062-chu-conquest','songshi-261-siting-battle']:
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
main_sources = ['tongjian-290-951-year-end','tongjian-290-951-final-appointments']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p077-p082',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-final-appointments':'卷290·广顺元年末至二年初·授任征赋与年界','xinwudaishi-065-chenzhou-campaign':'卷65·南汉世家·乾和九年冬取郴州','xinwudaishi-062-hunan-taxation':'卷62·南唐世家·保大十年湖南征敛','songshi-481-pan-chongche':'卷481·世家四·南汉刘氏·潘崇彻附传'}
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
for n in range(77, 83):
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
    labels={'tongjian-290-951-final-appointments':'卷290·广顺元年末至二年初·授任征赋与年界','xinwudaishi-065-chenzhou-campaign':'卷65·南汉世家·乾和九年冬取郴州','xinwudaishi-062-hunan-taxation':'卷62·南唐世家·保大十年湖南征敛','songshi-481-pan-chongche':'卷481·世家四·南汉刘氏·潘崇彻附传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年十一月至十二月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_11_{len(B["claims"])+1:04d}'
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










ALIASES.update({'帝':'郭威','唐主':'李璟','唐王':'李璟','北汉主':'刘崇（刘知远弟）','南汉主':'刘弘熙','王赟':'王赟（楚永州刺史）'})
NEW_ALIASES={'仇弘超':[],'康延沼':['康延昭'],'王赟（楚永州刺史）':[],'潘崇彻':['潘崇徹'],'谢贯':['謝貫'],'张峦':['張巒'],'杨继勋':['楊繼勳'],'孙朗':['孫朗'],'曹进':['曹進']}
NEW_DESCRIPTIONS={'仇弘超':'后周行营马军都指挥使。951年晋州解围后奉王峻之命，与药元福等率骑兵追击北汉军至霍邑。生卒年未载。','康延沼':'后周军官。951年奉王峻之命，与陈思让等率骑兵追击北汉军。《宋史》陈思让传同役记康延昭，与陈思让分任左右厢排阵使，按同场同职对应；未与康延泽合并。生卒年未载。','王赟（楚永州刺史）':'楚国永州刺史。951年南唐要求湖南刺史入朝，他较晚到达，被李璟毒杀。与已录岳州刺史王赟是否同人仍待补证，暂不合并。此前履历和出生年未载。','潘崇彻':'南汉内侍省丞。951年与谢贯率兵攻郴州，在义章击败南唐援军。《宋史》附传记为广州南海人，官称写内侍省局丞。生卒年尚未录入。','谢贯':'南汉将军。951年与潘崇彻受命率兵攻郴州。生卒年未载。','张峦':'南唐黑云指挥使。951年十二月任知全州，防备南汉。《新五代史》保大十年另记他出兵争桂管失败，时序另保留。生卒年未载。','杨继勋':'南唐都官郎中。南唐取湖南以后被派去征收湖南租赋，以供驻军；史书记载征收苛刻、湖南人失望。生卒年未载。','孙朗':'原随蒙城镇将咸师朗投降南唐的军人，后任奉节指挥使。南唐取湖南后因功赏和粮赐问题不满，与曹进商议杀王绍颜、边镐，夺取湖南归附中原。实际起事在952年另段，不提前录为951年既成事实。生卒年未载。','曹进':'南唐奉节指挥使，原随咸师朗降唐。因功赏、粮赐问题，与孙朗商议杀王绍颜和边镐、夺湖南归附中原。此处为计划，实际起事另见952年。生卒年未载。'}
NEW_DEATH_YEARS={'王赟（楚永州刺史）':951}
old='jiuwudaishi-112-december-expedition';song='songshi-261-siting-battle';nt='xinwudaishi-062-chu-conquest';tax='xinwudaishi-062-hunan-taxation';nh='xinwudaishi-065-chenzhou-campaign';pan='songshi-481-pan-chongche'
add('murong_requests_court_visit','慕容彦超请求入朝，郭威答允',77,'慕容彦超奏请入朝，','即许之。',[('慕容彦超','请求入朝'),('帝','认为请求有诈，仍答允')],when='951年十二月，具体奏请日未载',place='泰宁军与后周朝廷',note='郭威知其诈是史书对其判断的表述；答允不等于慕容彦超已入京。')
add('murong_cancels_court_visit','慕容彦超又以境内盗贼多为由，不肯离镇',77,'既而复称',None,[('慕容彦超','以境内多盗为由，表示未敢离镇')],when='951年十二月入朝请求获准以后',place='泰宁军',note='多盗是他所称理由，未另立已证实盗情事件。')
sup('murong_cancels_court_visit',77,old,'兗州慕容彥超上言，乞朝覲，詔允之，尋稱部內草寇起，不敢離鎮。','《旧五代史》同样记请求朝觐获准后，又称部内草寇起而不离镇。','两书都未在此句给实际朝觐日，不虚构一次已完成入朝。')
add('jinzhou_siege_food_shortage','北汉久攻晋州不克，大雪与百姓避寨使军粮不足',78,'北汉主攻晋州，','军乏食。',[('北汉主','所率军久攻晋州未克，面临缺粮')],when='951年十二月晋州解围以前',place='晋州及周边',note='百姓聚保山寨导致野无所掠，不扩大成全部居民死亡或全国饥荒。')
add('khitan_han_night_retreat','契丹军听说王峻到蒙坑，烧营夜退',78,'契丹思归，','烧营夜遁。',[],when='951年十二月王峻前锋过蒙坑以后、晋州解围时',place='晋州',note='思归为史书记载的军中意向，不给未具名士兵逐一建立心理记录。')
add('wang_jun_enters_jinzhou','王峻进入晋州，面对追击建议暂未决断',78,'峻入晋州，','峻犹豫未决。',[('王峻','进入晋州，对诸将立即追击的请求尚未决断')],when='951年十二月围军退走以后',place='晋州',note='进入城中与后续追击分开，不称他亲自率先锋先到蒙坑。')
sup('wang_jun_enters_jinzhou',78,old,'己酉，王峻奏，劉崇逃遁，王師已入晉州。','《旧五代史》十二月己酉记王峻奏报刘崇逃遁、王师已入晋州。','己酉为奏报日，不替代《资治通鉴》未单列的入城日期。',relation='adds')
add('wang_orders_cavalry_pursuit','王峻次日派仇弘超、药元福、陈思让、康延沼率骑兵追击',78,'明日，','将骑兵追之，',[('王峻','在入晋州次日派骑兵追击'),('仇弘超','以行营马军都指挥使身份率骑兵追击'),('药元福','以都排陈使身份率骑兵追击'),('陈思让','受命率骑兵追击'),('康延沼','受命率骑兵追击')],when='951年十二月王峻入晋州后的次日，具体干支未载',place='晋州至霍邑',note='底本陈思让职称写左厢排除使，字形及与康的官职分配待核；不把两人机械写为同一个左厢职。')
claim('person',people['康延沼'],'description','《宋史》记康延昭与陈思让分别任左右厢排阵使，奉命经乌岭路到绛州与救援军会合。',78,'以思讓與康延昭分為左右廂排陣使，令率軍自烏嶺路至絳州與大軍合。','同一晋州救援、与陈思让配任和追击背景支持康延昭与康延沼对应，不仅凭近音合并，未与康延泽混同；本句未明确两人左右对应，不额外指定。',source=song)
add('huoyi_pursuit_battle','后周骑兵追到霍邑进击，北汉军多人坠落崖谷死亡',78,'及于霍邑，','北汉兵坠崖谷死者甚众。',[('仇弘超','参与霍邑追击'),('药元福','参与霍邑追击'),('陈思让','参与霍邑追击'),('康延沼','参与霍邑追击')],when='951年十二月受命追击以后',place='霍邑',note='甚众未给伤亡总数，不编精确数字；名将参与来自前句明确追击名单。')
add('kang_slows_pursuit','康延沼在霍邑狭道未急追，北汉军得以通过',78,'霍邑道隘，','由是北汉兵得度。',[('康延沼','在狭道追击不急，北汉军得以通过')],when='951年十二月霍邑追击期间',place='霍邑',note='畏懦是史家评价，动作仅为未急追，不推定他故意通敌。')
add('yao_yuanfu_urges_pursuit','药元福认为应趁北汉疲惫继续追击，以免后患',78,'药元福曰：','必为后患。”',[('药元福','劝诸将趁敌军疲惫继续追击')],when='951年十二月霍邑追击期间',place='霍邑',note='他对刘崇目标、军力和未来后患的说法保留为人物判断，不直接证明后来灾祸。')
add('wang_jun_stops_pursuit','诸将不愿再进，王峻遣使止追，追兵返回',78,'诸将不欲进，','遂还。',[('王峻','派使者停止追击')],when='951年十二月霍邑追击以后',place='霍邑至后周军',note='不猜每名具名将领都反对追击，也不虚构止追原因。')
add('khitan_retreat_losses','契丹军到晋阳时，人员与马匹损失约十分之三四',78,'契丹比至晋阳，','士马什丧三四。',[],when='951年十二月北撤到晋阳时',place='晋阳',note='士马为人员与马匹的合称，比例按原文保留，不推算万人或匹数，也不把损失全算作战死。')
add('xiao_yujue_punishes_chief','萧禹厥因无功感到羞耻，把一名大酋长钉在市中，十余天后斩杀',78,'萧禹厥耻于无功，','旬馀而斩之。',[('萧禹厥','惩罚并杀害一名大酋长')],when='951年晋州撤军后，具体开始及杀害日未载',place='契丹军所到市镇，原文未具名',note='大酋长没有姓名，未新建具名人物；“钉”按底本保留，不补原文未载的刑具或程序。')
add('liu_chong_pauses_expansion','晋州失利后，刘崇暂息进取之意',78,'北汉主始息意于进取。','北汉主始息意于进取。',[('北汉主','暂息进取之意')],when='951年晋州失利以后',place='北汉',note='始息意不译成永久停止一切军事行动。')
add('northern_han_burdens_flight','史书概述北汉赋役沉重，许多百姓逃入后周境内',78,'北汉土瘠民贫，',None,[],year=None,when='北汉建立后的一段时期概述，具体起止年份未载',place='北汉至后周边境',note='土地民生与对契丹供奉为史家背景叙述，不虚构具体税率、人口总数和每次逃迁日。')
add('song_qiqiu_taifu','李璟任命宋齐丘为太傅',79,'唐主以镇南节度使兼中书令宋齐丘','为太傅，',[('唐主','任宋齐丘为太傅'),('宋齐丘','由镇南节度使兼中书令获任太傅')],when='951年十二月条下，具体授任日未载',place='南唐朝廷')
add('ma_xie_hongzhou_assignment','李璟任马希萼为江南西道观察使、守中书令，镇洪州，仍封楚王',79,'以马希萼','仍赐爵楚王。',[('唐主','任马希萼镇洪州，仍赐楚王爵'),('马希萼','获江南西道观察使、守中书令及洪州任所')],when='951年十二月马氏东迁以后，具体授任日未载',place='洪州',note='这是东迁后的授任，与此前三月封楚王分开，观察使不擅自改成节度使。')
sup('ma_xie_hongzhou_assignment',79,nt,'景以希萼為洪州節度使，','《新五代史》记李璟以马希萼为洪州节度使。','主书江南西道观察使与补书洪州节度使官称不同，分别保留，不用补書替换主书职衔。',relation='conflicts')
add('ma_xichong_shuzhou_assignment','李璟任马希崇为永泰节度使兼侍中，镇舒州',79,'以马希崇','镇舒州。',[('唐主','任马希崇镇舒州'),('马希崇','获永泰节度使兼侍中')],when='951年十二月马氏东迁以后，具体授任日未载',place='舒州')
sup('ma_xichong_shuzhou_assignment',79,nt,'希崇舒州節度使，','《新五代史》也记马希崇任舒州节度使。','永泰与舒州为两书军镇、州名用法，未新建两次不同授任。')
add('hunan_officials_assigned','南唐按原地位高低给湖南将吏授官',79,'湖南将吏，','卑者以次拜官。',[],when='951年十二月湖南将吏入南唐以后',place='南唐',note='未列全部授官者姓名，不补造任命名单。')
add('liao_peng_rewarded','李璟赞许廖偃、彭师暠，给两人授职并厚赏',79,'唐主嘉廖偃、彭师暠之忠，','赐予甚厚。',[('唐主','赞许两人并授职、厚赏'),('廖偃','获左殿直军使、莱州刺史'),('彭师暠','获殿直都虞候')],when='951年十二月马氏将佐入南唐以后',place='南唐朝廷',note='忠为李璟的评价；莱州刺史为授职称号，不推定廖偃实际占领或到任北方莱州。')
add('wang_yun_poisoned','永州刺史王赟迟到南唐朝廷，被李璟毒杀',79,'湖南刺史皆入朝于唐，',None,[('唐主','毒杀较晚到达的永州刺史王赟'),('王赟','以永州刺史身份较晚入朝，被毒杀')],when='951年十二月湖南刺史入朝条下，具体毒杀日未载',place='南唐朝廷',note='原文未明杀害原因；本段永州刺史与已有岳州刺史王赟是否同人，尚缺连续任职或家世补证，暂用限定主体，不只凭同名合并。')
add('pan_xie_chenzhou_attack','刘晟派潘崇彻、谢贯率兵进攻郴州',80,'南汉主遣','将兵攻郴州，',[('南汉主','派潘崇彻、谢贯进攻郴州'),('潘崇彻','以内侍省丞身份率兵攻郴州'),('谢贯','以将军身份率兵攻郴州')],when='951年十二月条下，具体出兵日未载',place='郴州')
claim('person',people['潘崇彻'],'description','潘崇彻是广州南海人。',80,'潘崇徹，廣州南海人。','本传南汉内侍及军事履历对应主书潘崇彻；下一句事主姓名为私用字，未猜字另建人，也不提前录其后桂州代任或宋初生涯。',source=pan)
add('bian_sends_chenzhou_relief','边镐派军援救郴州',80,'唐边镐发兵救之。','唐边镐发兵救之。',[('边镐','派兵救援郴州')],when='951年十二月南汉攻郴州之后',place='长沙至郴州方向',note='未列领军将领，不默认边镐本人已经到义章。')
add('pan_defeats_tang_at_yizhang','潘崇彻在义章击败南唐援军，攻取郴州',80,'崇彻败唐兵','遂取郴州。',[('潘崇彻','在义章击败南唐军并攻取郴州')],when='951年十二月，具体交战日未载',place='义章、郴州')
sup('pan_defeats_tang_at_yizhang',80,nh,'九年冬，又遣內侍潘崇徹攻郴州，李景兵亦在，與崇徹遇，戰，大敗景兵於宜章，遂取郴州。','《新五代史》南汉乾和九年冬也记潘崇彻在宜章大败李璟军，攻取郴州。','乾和九年为951年。主书义章与补书宜章字形不同，原文保留，不另建两场战役或未经核实的坐标。')
add('bian_requests_quan_dao_governors','边镐请求任命全州、道州刺史，防备南汉',80,'边镐请除全、道','以备南汉。',[('边镐','请求给全州、道州任命刺史')],when='951年十二月郴州失守后、丙辰任命以前',place='全州、道州',note='除在此为授职，不译成取消二州。')
add('liao_daozhou_governor','李璟任命廖偃为道州刺史',80,'丙辰，','以廖偃为道州刺史，',[('唐主','任廖偃为道州刺史'),('廖偃','获任道州刺史')],when='951年十二月丙辰',place='道州')
add('zhang_luan_quanzhou','李璟让黑云指挥使张峦知全州',80,'以黑云指挥使张峦','知全州。',[('唐主','派张峦主持全州事务'),('张峦','以黑云指挥使身份知全州')],when='951年十二月丙辰',place='全州',note='知全州为主持州务，不把黑云指挥使译成普通云州军将。')
claim('person',people['张峦'],'description','《新五代史》保大十年记李璟派将军张峦出兵争夺桂管而未成功。',80,'廣州劉晟乘楚之亂，取桂管，景遣將軍張巒出兵爭之，不克。','补书置保大十年即952年，主书本次951年只记知全州；作为连续军职背景保留独立出处，不把这次知全州写成已完成的争桂管战役。',source=tax)
add('wang_yanzheng_guangshan','李璟任王延政为山南西道节度使，改封光山王',81,'是岁，',None,[('唐主','任王延政山南西道节度使、改封光山王'),('王延政','由安化节度使、鄱阳王获新任及爵号')],when='951年，具体月日未载',place='南唐',note='山南西道与光山王为授任和封爵，不推定他已实际控制后周所辖全部山南西道。')
E['xian_surrenders']=event('xian_surrenders','蒙城镇将咸师朗率部投降南唐',82,'初，蒙城镇将咸师朗将部兵降唐，',[('咸师朗','率部投降南唐')],year=949,when='949年已录的降唐行动，本段追述未另纪日',place='蒙城',stable_key='event_zztj_288_0949_xian_shilang_surrenders_huangfu',note='本段回顾已有949年向皇甫晖投降事件，复用原key及参与，不重复新建一次降唐。')
add('fengjie_unit_formed','李璟把咸师朗所部编为奉节都，让他们随边镐平湖南',82,'唐主以其兵为奉节都，','从边镐平湖南。',[('唐主','把降军编为奉节都并用于湖南行动'),('咸师朗','所部被编为奉节都，随边镐平湖南')],year=None,when='949年降唐后至951年取湖南期间的追述，具体编制日未载',place='南唐至湖南',note='从军平湖南为此部队的行动，不把所有部兵都新建具名人物。')
add('tang_moves_hunan_resources','南唐把湖南钱粮、珍玩、舟舰等物资迁往金陵',82,'唐悉收湖南','皆徙于金陵，',[],year=None,when='南唐951年取湖南后至952年初奉节军起事以前的追述，具体各次转运日未载',place='湖南至金陵',note='悉收为史家概述，包含亭馆花果等，未考证搬运方式，不擅自补运输工具与数量。')
add('yang_jixun_collects_hunan_taxes','李璟派杨继勋等征收湖南租赋，供给驻军',82,'遣都官郎中杨继勋','以赡戍兵。',[('唐主','派官员征收湖南租赋供驻军'),('杨继勋','以都官郎中身份奉命征收租赋')],year=None,when='951年湖南被取后至952年初起事以前的追述，具体派遣日未载',place='湖南',note='派遣者据唐朝廷上下文明确；等字未列其他人，不补全部税官名单。')
add('hunan_taxation_discontent','史书记载杨继勋等征赋苛刻，湖南人失望',82,'继勋等务为苛刻，','湖南人失望。',[('杨继勋','被史书评价为征收苛刻')],year=None,when='南唐取湖南后的一段时期，具体年月未载',place='湖南',note='苛刻与民众失望为史书概述，不编具体税额或诉讼案件。')
sup('hunan_taxation_discontent',82,tax,'楚地新定，其府庫空虛，宰相馮延巳以克楚為功，不欲取費於國，乃重斂其民以給軍，楚人皆怨而叛，','《新五代史》记楚地新定、府库空虚，冯延巳不愿向本国取费，重敛楚民供军，民众怨而反叛。','该书将此叙述置保大十年；主书年末回顾征赋不满，时序分别保留。未提前录其后刘言攻逐边镐，也不把冯延巳参与强系为951年某日。',relation='adds')
add('wang_shaoyan_cuts_rations','王绍颜减少奉节等士卒的粮食赏赐',82,'行营粮料使王绍颜','减士卒粮赐，',[('王绍颜','以行营粮料使身份减少士卒粮赐')],year=None,when='取湖南后至952年初孙朗曹进起事以前，具体减赐日未载',place='湖南',note='原文未给减额或粮食数量，不虚构减半等比例。')
add('sun_cao_plot_hunan','孙朗、曹进因粮赐与功赏不满，商议杀王绍颜、边镐夺湖南',82,'奉节指挥使孙朗、曹进','富贵可图也！”',[('孙朗','因待遇不满，提出杀人夺地归附中原的计划'),('曹进','与孙朗商议杀人夺地归附中原')],year=None,when='951年取湖南后至952年正月庚申实际起事以前的谋划，具体谈话日未载',place='湖南',note='怒言与计划不等于已经杀死王绍颜、边镐；当前年末止于谋划，实际起事在下一年正文另录。')
reviews={77:'请求入朝、答允与后称多盗不离镇分录；多盗保留人物理由，旧史印证不虚构实际朝觐。',78:'久攻缺粮、夜退、入城、次日追击、霍邑交战、缓追、药元福建议与止追分别记录。康沼昭按同役左右厢职对应，未与延泽合并；排除疑官名字形不强释。契丹士马损耗不全当死亡，钉酋长及北汉赋役概述不编人数与税率。',79:'宋太傅、马氏两镇、湖南将吏官赏与廖彭授职分录，地方虚衔不当实控。新书希萼洪州节度与主观察使异称保留。永州王赟与岳州王赟待核，不仅同名强合。',80:'潘谢出兵、边镐援兵、义章胜与取郴、请求刺史、丙辰廖道张全分开；新南汉九年冬印证，义宜字形保留。宋潘附传只补籍贯，不猜私用字，也不提前后续接替吴怀恩。新书张争桂管系952，不当此次知全州同一事。',81:'是岁统记任官封爵，年明确月日不明；山南西道头衔不当实际控制整区域。',82:'咸降唐复用949事件，奉节编制与从征跨949至951不硬年。资源转运、苛征、减粮与孙曹计划是末年追述，起止未明保留跨951至952初范围；实际烧府门起事不提前到本年。新书重敛置保大十年并列，未提前刘言攻逐。'}
assert not (P/'publication.json').exists()
for n in range(77,83):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(77,83)],next_paragraph='zztj-v290-y0952-p001',next_volume=290,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷290原82—87行连续六段；完成本年正文后须另作年度发布与年界审计。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(77,83)],source_issues_review='逐字引文保留底本，纸本未核。排除官名疑字、康沼昭同场对应、义宜地名字形、永州与岳州王赟身份待核、希萼观察与节度官称分别记录。宋潘传私用字未猜，湖南征敛补书年份独立保留。自动原文块跨951与952年，原84—95行快照不改，本批只引用951年原84—87行，不把年界及下一年史事录入本年。',plain_language_review='首次检查展示标题、人物、角色、关系、时间和事实说明；命令、建议、预计、已执行和追述分清，引用外使用现代白话；不安排旧文案全面重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
