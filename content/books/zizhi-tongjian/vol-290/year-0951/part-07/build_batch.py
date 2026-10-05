# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 47–54."""
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
COMMIT='9e997db426b307c77960efec150970c3a7a81085'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-951-march-policies','xinwudaishi-070-zheng-gong','xinwudaishi-066-langzhou-flight']:
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
main_sources = ['tongjian-290-951-march-policies']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p047-p054',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-111-june-ministers':'卷111·太祖本纪二·广顺元年六月、七月','jiuwudaishi-111-august-transfers':'卷111·太祖本纪二·广顺元年八月','liaoshi-005-han-investiture':'卷5·世宗本纪·天禄五年六月','songshi-262-li-gu-hezhong':'卷262·列传二十一·李谷传·河中往事与拜相','songshi-482-wei-rong-early':'卷482·世家五·北汉刘氏·卫融早年'}
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
for n in range(47, 55):
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
    labels={'jiuwudaishi-111-june-ministers':'卷111·太祖本纪二·广顺元年六月、七月','jiuwudaishi-111-august-transfers':'卷111·太祖本纪二·广顺元年八月','liaoshi-005-han-investiture':'卷5·世宗本纪·天禄五年六月','songshi-262-li-gu-hezhong':'卷262·列传二十一·李谷传·河中往事与拜相','songshi-482-wei-rong-early':'卷482·世家五·北汉刘氏·卫融早年'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年六月至八月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_07_{len(B["claims"])+1:04d}'
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










ALIASES.update({'帝':'郭威','吴越王':'钱弘俶','弘亻叔':'钱弘俶','仁俊':'钱仁俊','北汉主':'刘崇（刘知远弟）','北汉王':'刘崇（刘知远弟）','契丹主':'耶律阮','翟光鄴':'翟光邺','于晏':'王晏','孙方谏':'孙方简','行友':'孙行友'})
NEW_ALIASES={'刘言':['劉言'],'卫融':['衛融']}
NEW_DESCRIPTIONS={'刘言':'吉州庐陵人，楚国辰州刺史。951年王逵、周行逢等欲迎他到朗州任副使，他单骑前往，众人废去马光惠后推他为权武平留后。生卒年尚未录入。','卫融':'北汉官员，青州博兴人，字明远。951年七月以翰林学士身份奉刘崇之命出使契丹，谢册礼并请求援兵。《宋史》记早年中进士，曾任南乐主簿、忠武军掌书记等职。生卒年尚未录入。'}
june='jiuwudaishi-111-june-ministers';aug='jiuwudaishi-111-august-transfers';li='songshi-262-li-gu-hezhong';wei='songshi-482-wei-rong-early';liao='liaoshi-005-han-investiture';nw='xinwudaishi-070-zheng-gong';chu='xinwudaishi-066-langzhou-flight'
add('wang_jun_left_pushe','郭威任命王峻为左仆射兼门下侍郎',47,'六月，辛亥，','为左仆射兼门下侍郎，',[('帝','任命王峻为左仆射兼门下侍郎'),('王峻','由枢密使、同平章事获任左仆射兼门下侍郎')],when='951年六月辛亥',place='后周朝廷')
sup('wang_jun_left_pushe',47,june,'辛亥，以樞密使王峻為尚書左僕射兼門下侍郎、同平章事、監修國史，充樞密使；','《旧五代史》补记王峻兼同平章事、监修国史，并继续充枢密使。','同日同人任职相合，补充兼职，不认定已辞去枢密使。',relation='adds')
add('fan_zhi_appointed','郭威任命范质为中书侍郎、同平章事',47,'枢密副使、兵部侍郎范质、','谷仍判三司。',[('帝','任命范质为中书侍郎、同平章事'),('范质','由枢密副使、兵部侍郎获任宰相')],when='951年六月辛亥',place='后周朝廷',note='并同平章事指范质与李谷，分别登记两人任职。')
sup('fan_zhi_appointed',47,june,'以樞密副使、尚書兵部侍郎範質為中書侍郎、同平章事，充集賢殿大學士；','《旧五代史》补记范质还充集贤殿大学士。','範質、范质沿已有字形别名复用，不新建实体。',relation='adds')
add('li_gu_appointed','郭威任命李谷为中书侍郎、同平章事，仍掌三司',47,'户部侍郎、判三司李谷','谷仍判三司。',[('帝','任命李谷为中书侍郎、同平章事'),('李谷','获任宰相，继续判三司')],when='951年六月辛亥',place='后周朝廷')
sup('li_gu_appointed',47,june,'以戶部侍郎、判三司李穀為中書侍郎、同平章事，判三司。','《旧五代史》也记李谷拜相后继续判三司。','李穀与李谷沿稳定主体复用。')
sup('li_gu_appointed',47,li,'廣順初，加戶部侍郎。未幾，拜中書侍郎、平章事，仍判三司。','《宋史》记李谷广顺初加户部侍郎，随后拜中书侍郎、平章事，仍判三司。','EPUB题名李濤傳，正文卷262开篇及连续上下文为李谷传，出处按正文标注，不照抄导航题名。')
add('dou_su_removed_chancellorship','郭威罢免窦贞固、苏禹珪的宰相职务，保留本官',47,'司徒兼侍中窦贞固、','并罢守本官。',[('帝','罢免两人的宰相职务'),('窦贞固','罢相后保留本官'),('苏禹珪','罢相后保留本官')],when='951年六月辛亥',place='后周朝廷',note='罢守本官不是剥夺全部官职，也不是两人死亡。')
sup('dou_su_removed_chancellorship',47,june,'司徒兼侍中、監修國史竇貞固，司空兼中書侍郎、同平章事、集賢殿大學士蘇禹珪，並罷相守本官。','《旧五代史》明确记两人罢相守本官，并列出此前兼职。','据明确罢相字样解释《资治通鉴》的罢守，不增补未载处罚理由。')
add('fan_zhi_shumi','郭威让范质参与掌管枢密院事务',47,'癸丑，','范质参知枢密院事。',[('帝','命范质参知枢密院事'),('范质','拜相后兼参与掌管枢密院事务')],when='951年六月癸丑',place='后周朝廷')
sup('fan_zhi_shumi',47,june,'癸丑，詔宰臣範質參知樞密院事。','《旧五代史》同日记宰臣范质参知枢密院事。','不把癸丑兼职混成辛亥拜相同一日期。')
add('zhai_shumi_deputy','郭威任命翟光邺兼枢密副使',47,'丁巳，',None,[('帝','任命翟光邺兼枢密副使'),('翟光鄴','以宣徽北院使身份兼枢密副使')],when='951年六月丁巳',place='后周朝廷')
sup('zhai_shumi_deputy',47,june,'以宣徽北院使翟光鄴兼樞密副使。','《旧五代史》同日记翟光邺兼枢密副使。','翟光鄴按已有翟光邺主体和别名复用。')
add('guo_li_hezhong_conversation','郭威讨河中时暗示李谷，李谷以尽节侍君回应',48,'初，帝讨河中，','帝以是贤之。',[('帝','讨河中时多次向李谷作暗示，并赞许其回应'),('李谷','任转运使时以臣子应尽节侍君回应郭威')],year=None,when='郭威讨河中时的追述，《宋史》系于后汉乾祐年间，未据本段另定具体日期',place='河中',note='微言讽之没有直引具体话语，不替郭威编造登基请求；人望所属是史家概述。')
sup('guo_li_hezhong_conversation',48,li,'初，漢乾祐中，周祖討河中，穀掌轉運，時周祖已有人望，屬漢政紊亂，潛貯異志，屢以諷穀，穀但對以人臣當盡節奉上而已。','《宋史》也记郭威讨河中时向掌转运的李谷作暗示，李谷只以臣子尽节侍君回应。','潜贮异志为该书对郭威意图的叙述，不扩写为已经公开发动夺位行动。')
used.setdefault(48,[]).append(E['li_gu_appointed'])
claim('event',E['li_gu_appointed'],'description','史书在回顾郭威与李谷的河中谈话后，记郭威即位后首先起用李谷为宰相。',48,'即位，首用为相。','这是对此后用人的回顾，不另建正月拜相事件；具体拜中书侍郎、同平章事已按六月辛亥登记。')
add('early_zhou_minister_assessment','史书评价王峻尽心军务、范质守法、李谷善于议政',48,'时国家新造，',None,[('王峻','被史书评价为日夜尽心、在军旅谋划上多有帮助'),('范质','被史书评价为明敏强记、谨守法度'),('李谷','被史书评价为沉毅有谋略，善于向郭威进言')],year=None,when='后周初立时期的概述，具体起止年月未载',place='后周朝廷',note='三名大臣的性格与贡献为史家评价，不据此编造某次战役或具体会议。')
add('ma_guanghui_assessment','史书记载马光惠嗜酒，不能使诸将服从',49,'武平节度使马光惠，','不能服诸将，',[('马光惠','被史书评价为愚懦嗜酒，不能使诸将服从')],when='951年六月被废以前的概述',place='朗州',note='不扩写为某个具名将领在具体一天拒令。')
add('langzhou_invites_liu_yan','王逵、周行逢、何敬真商议迎刘言为副使',49,'王逵、周行逢、何敬真谋','欲迎以为副使。',[('王逵','参与商议迎刘言为副使'),('周行逢','参与商议迎刘言为副使'),('何敬真','参与商议迎刘言为副使'),('刘言','以辰州刺史身份成为迎接任副使的对象')],when='951年六月条下，具体商议日未载',place='朗州与辰州',note='骁勇得蛮夷心是商议者看中刘言的理由；蛮夷为史书对当地族群的称谓，不补具体族名。邀请任副使与后来推为留后分开。')
add('liu_yan_arrives_langzhou','刘言担心拒绝会遭攻击，单骑前往朗州',49,'言知逵等难制，','乃单骑赴之。',[('刘言','因担心拒绝会遭攻击而单骑前往')],when='951年六月受邀之后，具体到达日未载',place='辰州至朗州',note='不往将攻我是刘言的判断，没有据此建立王逵已经攻辰州的事件。')
add('langzhou_removes_guanghui','朗州众人废去马光惠，并把他送往南唐',49,'既至，','送于唐，',[('马光惠','在刘言到达后被废并送往南唐')],when='951年六月刘言到朗州以后',place='朗州至南唐',note='众未列执行者姓名，不假定每名将领都亲自押送。')
sup('langzhou_removes_guanghui',49,chu,'進逵乃逐出留後馬光惠，迎言於辰州以為帥，進逵自為副。','《新五代史》也记逐出马光惠、迎刘言为主帅，并补记王进逵自为副使。','《新五代史》压缩叙事，把此事紧接修府出走后的战败追军；此处按《资治通鉴》六月条登记，不反推三月已经换刘言。',relation='adds')
add('liu_yan_wuping_acting','朗州众人推刘言为权武平留后',49,'推言','权武平留后，',[('刘言','被推举为权武平留后')],when='951年六月马光惠被废之后',place='朗州',note='权为暂代，不写成已获南唐正式节度使授命。')
add('langzhou_requests_tang_jiedushi','朗州向南唐请求节度使授命，南唐没有批准',49,'表求旄节于唐，','唐人未许。',[('刘言','作为新留后成为请求正式授节的对象')],when='951年六月推刘言为留后以后',place='朗州与南唐',note='旄节代表节度使正式授命；未许不等于南唐已发兵进攻，不补无载的使者姓名。')
add('langzhou_submits_zhou','刘言主持的朗州也向后周称藩',49,'亦称籓于周。',None,[('刘言','主持朗州后向后周称藩')],when='951年六月朗州换帅后',place='朗州至后周',note='称藩是政治表态，不推断后周已派官接管朗州。')
add('qian_renjun_restored','钱弘俶认定钱仁俊无罪，恢复他的官爵',50,'吴越王',None,[('吴越王','认定钱仁俊无罪并恢复其官爵'),('仁俊','获恢复此前官爵')],when='951年六月条下，具体恢复日未载',place='吴越',note='复其官爵没有列完整清单，不虚构所有兼职；前内外马步都统军使是原文标识。')
add('khitan_invests_liu_chong','契丹派燕王述轧等册封刘崇为大汉神武皇帝',51,'契丹遣燕王述轧等','大汉神武皇帝，',[('契丹主','派使者册封北汉君主'),('述轧','以燕王身份参与册封'),('北汉王','获大汉神武皇帝册号')],when='951年六月条下，具体册礼日未载',place='契丹与北汉')
sup('khitan_invests_liu_chong',51,nw,'兀欲遣燕王述軋、政事令高勳以冊尊旻為大漢神武皇帝，','《新五代史》补记与燕王述轧同赴册封的还有政事令高勋。','直接册封记载支持高勋同行；本文称旻是沿用后来的名字，不提前新建另一个北汉君主。',relation='adds')
pk=person('高勋',51,'以政事令身份与燕王述轧一同参与北汉册封','兀欲遣燕王述軋、政事令高勳以冊尊旻為大漢神武皇帝，',source=nw)
e='participation_zztj_290_0951_khitan_invests_liu_chong_'+pk
B['person_events'].append(dict(key=e,person_key=pk,event_key=E['khitan_invests_liu_chong'],role='以政事令身份与燕王述轧一同参与北汉册封',status='draft'))
claim('person_event',e,'role','高勋以政事令身份参与北汉册封。',51,'兀欲遣燕王述軋、政事令高勳以冊尊旻為大漢神武皇帝，','沿已有高勋及高勳字形主体复用。',source=nw)
sup('khitan_invests_liu_chong',51,liao,'六月辛卯朔，劉崇為周所攻，遣使稱，乞援，且求封冊。即遣燕王牒哷、樞密使高勛冊為大漢神武皇帝。','《辽史》把请援求册及派遣册封列在六月辛卯朔，册使称燕王牒哷、枢密使高勛。','《资治通鉴》燕王名为述轧，《辽史》写牒哷，高勋职衔也与《新五代史》不同；并列记载，不仅凭同为燕王就把牒哷加为述轧别名，也不以派遣日认定册礼同日已举行。',relation='conflicts')
add('khitan_invests_han_empress','契丹册命北汉君主的妃子为皇后',51,'妃为皇后。','妃为皇后。',[],when='951年六月北汉册封条下，具体册礼日未载',place='北汉',note='本句没有给妃子姓名，不猜测身份或生卒年。')
sup('khitan_invests_han_empress',51,nw,'并冊旻妻為皇后。','《新五代史》也记册封刘旻之妻为皇后。','妻与妃按各书用语保留，未据此新建无名人物。')
add('liu_chong_name_min','刘崇更名刘旻',51,'北汉主更名旻。',None,[('北汉主','更名旻')],when='951年六月册封条下，具体改名日未载',place='北汉',note='更名是同一君主的名字变化，沿刘崇稳定主体，不新建刘旻。')
claim('person',people['刘崇（刘知远弟）'],'name','刘崇在北汉册封条下更名刘旻。',51,'北汉主更名旻。','生平主体保持既有key；本句未提供更名原因。')
add('wei_rong_thanks_requests_troops','刘崇派卫融等赴契丹谢册礼并请求援兵',52,'秋，七月，',None,[('北汉主','派卫融等赴契丹谢册礼并请求援兵'),('卫融','以翰林学士身份出使契丹')],when='951年七月，具体派遣日未载',place='北汉至契丹',note='请求援兵与援军实际到达分开，不提前录入后续契丹出兵。')
claim('person',people['卫融'],'description','卫融字明远，是青州博兴人。',52,'衛融字明遠，青州博興人。','博兴籍贯与《资治通鉴》翰林学士卫融对应，连续北汉履历支持身份。',source=wei)
claim('person',people['卫融'],'description','《宋史》记卫融晋天福初中进士，历任南乐主簿、齐澶二州从事、忠武军掌书记。',52,'晉天福初舉進士，調南樂主簿，曆齊澶二州從事、忠武軍掌書記。','早年各职未给精确任职日，不强定为951年新任。',source=wei)
claim('person',people['卫融'],'description','《宋史》记卫融后汉初任太原观察支使，刘崇称帝后授中书侍郎、平章事。',52,'漢初，為太原觀察支使，劉崇稱帝，授中書侍郎、平章事。','《资治通鉴》出使时称翰林学士，《宋史》传记述宰相职衔；保留不同叙述，不据此覆盖本次出使职名或断言他只有一个官职。',source=wei)
add('han_yindi_burial','后汉隐帝刘承祐葬于颍陵',53,'八月，壬戌，',None,[('刘承祐','作为后汉隐帝葬于颍陵')],when='951年八月壬戌',place='颍陵',note='埋葬年份不等于去世年份，不把已死的刘承祐写成951年仍参与朝政。')
E['han_coffin_departure']=event('han_coffin_departure','后汉隐帝灵柩发引，郭威到太平宫祭奠',53,'八月辛卯，漢隱帝梓宮發引，帝詣太平宮臨奠，詔群臣出祖於西郊。',[('帝','到太平宫祭奠，并命群臣到西郊送葬')],source=aug,when='951年八月辛卯，《旧五代史》发引条',place='太平宫、西郊',note='发引是灵柩出发，壬戌是《资治通鉴》葬日，分录两项行动，不把不同日期当成同一葬日冲突。')
add('sun_fangjian_court_visit','孙方谏入朝',54,'义武节度使孙方谏入朝，','义武节度使孙方谏入朝，',[('孙方谏','以义武节度使身份入朝')],when='951年八月壬子调任以前，具体入朝日未载',place='后周朝廷')
add('sun_fangjian_zhen_guo','郭威把孙方谏调任镇国节度使',54,'壬子，','徙镇国节度使，',[('帝','调孙方谏任镇国节度使'),('孙方谏','由义武军调任镇国军')],when='951年八月壬子',place='镇国军')
sup('sun_fangjian_zhen_guo',54,aug,'定州孫方簡移鎮華州，','《旧五代史》也记孙方简从定州调镇华州。','孙方简、孙方谏为已核同人；华州为镇国军治所的记述，补书未沿用改名，不建立重复人物。')
add('sun_xingyou_yiwu_acting','郭威让易州刺史孙行友任义武留后',54,'以其弟易州刺史行友','为义武留后。',[('帝','任孙行友为义武留后'),('行友','由易州刺史任义武留后')],when='951年八月壬子条下',place='义武军')
sup('sun_xingyou_yiwu_acting',54,aug,'以易州刺史孫行友為定州留後。','《旧五代史》记易州刺史孙行友任定州留后。','定州与义武按两书军镇及州名用法对应，不把留后任命写成已授节度使。')
relationship('孙方简','孙行友','兄长',54,'以其弟易州刺史行友为义武留后。','《资治通鉴》明确称孙行友为孙方谏之弟。此前《宋史》本传所记叔侄关系存在异说，沿已有关系复用并保留冲突说明，不把所有书证改成兄弟。')
add('wang_yan_xuzhou','郭威把王晏从建雄军调镇徐州',54,'又徙建雄节度使于晏','镇徐州，',[('帝','调王晏镇徐州'),('于晏','由建雄节度使调任徐州')],when='951年八月壬子',place='徐州',note='于晏沿此前已核王晏主体；本次《旧五代史》同日晋州王晏移徐州继续印证，保留原文字形。')
sup('wang_yan_xuzhou',54,aug,'壬子，晉州王晏移鎮徐州，','《旧五代史》同日记晋州王晏移镇徐州。','同一原镇、目标镇及纪日印证于晏与王晏字形对应，不把于晏当独立新人物。')
add('wang_yanchao_jianxiong','郭威让王彦超接任建雄节度使',54,'以武宁节度使王彦超代之。',None,[('帝','让王彦超接替王晏的建雄军任职'),('王彦超','由武宁军调任建雄军')],when='951年八月壬子',place='建雄军',note='代之承王晏原职，不误读为王彦超再次接任刚离开的徐州。')
sup('wang_yanchao_jianxiong',54,aug,'徐州王彥超移鎮晉州。','《旧五代史》记王彦超从徐州调镇晋州。','对应武宁与建雄的州镇用法，未据州名另造第二次调任。')
reviews={47:'辛亥拜相与罢相、癸丑范质兼枢密、丁巳翟光邺兼副使分别录入。旧史同日印证并补王峻监修国史、范质集贤大学士；罢守不是剥夺全部官职。',48:'河中谈话为后汉时期追述，不强定951年；即位首用为相回指已录六月拜相，不另造正月授相。人物风格保留史家评价性质。宋262按正文确认李谷传，导航原题李濤傳不当传主。',49:'马光惠评价、迎刘言副使计划、刘言单骑到朗州、废光惠、推刘留后、向唐求节未许与向周称藩逐项录入。新书压缩时序不覆盖六月位置，不把担心遭攻击写成已攻辰州。',50:'钱仁俊官爵恢复沿已有主体，未补全无载兼职。',51:'册帝、册后与改名分录。新书补高勋；辽书燕王名牒哷、高勋称枢密使并列保留，不仅凭燕王职位强合别名；派遣日不等于册礼当日。妃无名不猜身份。',52:'卫融翰林学士出使谢册请兵，与实际出兵分开；宋482补字籍及早年任职，宰相职衔与主书翰林称谓分别保留。',53:'壬戌葬与旧史辛卯发引祭奠分开，葬年不当死亡年。',54:'入朝、孙方谏调镇、孙行友留后、王晏与王彦超互调分别录入；于晏王晏同日同镇印证。兄长关系按通鉴明确弟称，宋叔侄异说继续保留。'}
assert not (P/'publication.json').exists()
for n in range(47,55):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(47,55)],next_paragraph=Q[55]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原52—59行连续八段；本年后续正文仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(47,55)],source_issues_review='原文逐字导出，纸本未核。宋262传主李谷及宋482卫融附传已核正文。燕王牒哷与述轧名字、册使职衔、孙氏兄弟与叔侄异说并列保留，不强合；发引与葬日分开。',plain_language_review='首次录入已逐条检查展示标题、人物、事件、角色、关系、时间与引用说明；避免史料简称、含糊关系及无据主语，计划、评价、追述与实际行动分清。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
