# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 31–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,47))
COMMIT='cfe4b4148ad7d1e2ee8fc2e5d5c0cfad4d17a33c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-291-953-june-december']:
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
main_sources = ['tongjian-291-953-june-december']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0953-p031-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-953-june-december':'卷291·广顺三年六月至十二月','jiuwudaishi-113-august-953':'卷113·太祖本纪四·广顺三年八月','jiuwudaishi-113-september-953':'卷113·太祖本纪四·广顺三年九月','jiuwudaishi-113-october-953':'卷113·太祖本纪四·广顺三年十月','jiuwudaishi-113-december-953':'卷113·太祖本纪四·广顺三年十二月','xinwudaishi-65-liusheng-name':'卷65·南汉世家第五·刘晟旧名','xinwudaishi-65-five-princes':'卷65·南汉世家第五·乾和十一年五子册封','xinwudaishi-65-liuchang-name':'卷65·南汉世家第五·刘鋹初名'}
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
lines = (ROOT / 'resources/derived/tongjian/291.txt').read_text().splitlines()
for n in range(31, 41):
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
    labels={'tongjian-291-953-june-december':'卷291·广顺三年六月至十二月','jiuwudaishi-113-august-953':'卷113·太祖本纪四·广顺三年八月','jiuwudaishi-113-september-953':'卷113·太祖本纪四·广顺三年九月','jiuwudaishi-113-october-953':'卷113·太祖本纪四·广顺三年十月','jiuwudaishi-113-december-953':'卷113·太祖本纪四·广顺三年十二月','xinwudaishi-65-liusheng-name':'卷65·南汉世家第五·刘晟旧名','xinwudaishi-65-five-princes':'卷65·南汉世家第五·乾和十一年五子册封','xinwudaishi-65-liuchang-name':'卷65·南汉世家第五·刘鋹初名'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺三年（953年七月至十二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0953_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=953, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='953年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0953_' + code
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
        edge = 'participation_zztj_291_0953_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0953_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','荣':'柴荣','汉主':'刘弘熙','刘晟':'刘弘熙','王殷':'王殷（后汉后周将）'})
NEW_ALIASES={'白重赞':['白重贊'],'刘彦章':['劉彥章'],'杜延熙':[],'刘继兴':['劉繼興','刘鋹','劉鋹'],'刘璇兴':['劉璇興'],'刘庆兴':['劉慶興'],'刘保兴':['劉保興'],'刘崇兴':['劉崇興'],'张万友':['張萬友'],'马谔':['馬諤'],'乔赟':['喬贇'],'翟光裔':[]}
NEW_DESCRIPTIONS={'白重赞':'后周武成节度使。953年九月己亥奏报已堵塞决口的黄河。生卒年未载。','刘彦章':'齐州驻乐寿的保宁军都头。953年杀死兵马都监杜延熙，企图响应契丹，未成而被捕处死。生年未载。','杜延熙':'乐寿县兵马都监。953年九月被齐州保宁驻军都头刘彦章等杀死。生年未载。','刘继兴':'南汉刘晟之子，953年封卫王。《新五代史》明确记刘鋹初名继兴，保留同人别名；当时尚未即位，生卒年暂未核定。','刘璇兴':'南汉刘晟之子，953年封桂王。生卒年未载。','刘庆兴':'南汉刘晟之子，953年封荆王。生卒年未载。','刘保兴':'南汉刘晟之子。953年封王，《通鉴》电子本作祯王、《新五代史》作祥王，保留王号异读。生卒年未载。','刘崇兴':'南汉刘晟之子，953年封梅王。生卒年未载。','张万友':'后周郑州开道指挥使。953年驻乐寿，没有参加刘彦章叛乱，与马谔捕获刘彦章等并处死。生卒年未载。','马谔':'后周供奉官。953年奉朝廷命赴乐寿调查，与张万友捕获并处死刘彦章等十三人。生卒年未载。','乔赟':'北汉将领。953年十二月进犯府州，被折德扆击退。生卒年未载。'}
NEW_DESCRIPTIONS['翟光裔']='后周通事舍人。953年八月奉命赴湖南宣抚，朝廷同时准许王逵迁使府。未与不同职衔、已去世的翟光邺合并，生卒年未载。'
NEW_DEATH_YEARS={'刘彦章':953,'杜延熙':953}
oldaug='jiuwudaishi-113-august-953';oldsep='jiuwudaishi-113-september-953';oldoct='jiuwudaishi-113-october-953';olddec='jiuwudaishi-113-december-953';newname='xinwudaishi-65-liusheng-name';newsons='xinwudaishi-65-five-princes';newchang='xinwudaishi-65-liuchang-name'
add('southern_tang_drought','南唐严重干旱，井泉干涸，淮河水浅到可涉渡',31,'唐大旱，','淮水可涉，',[],when='953年七月条下至八月限制运粮前，旱灾具体起止未载',place='南唐、淮河流域',note='可涉反映史书所记低水位，不提供现代流量或降水量。')
add('hungry_people_cross_huai','饥民北渡淮河，濠州与寿州出兵阻拦，饥民与军队冲突后向北逃来',31,'饥民度淮而北者','民与兵斗而北来。',[],when='953年南唐旱灾期间',place='濠州、寿州至淮河北岸',note='军队未具名统帅，不自动指定当地某名节度使；不编冲突死伤数。')
add('guo_allows_grain_for_tang_people','郭威称两国百姓应同等看待，准许南唐百姓买米运过淮河',31,'帝闻之曰：','听籴米过淮。”',[('帝','允许南唐百姓购粮过淮')],when='953年七月至八月己未以前，具体许可日未载',place='后周、淮河',note='听籴米是准许买粮，不说全部粮食免费发放。')
add('tang_builds_grain_stores','南唐人随之建仓大量购粮，供给军队',31,'唐人遂筑仓，','多籴以供军。',[],when='953年郭威允许购粮之后、八月己未限制以前',place='南唐、淮河一带',note='供军为主书所述用途，不凭唐人概称补具名经办官。')
add('guo_restricts_bulk_grain_transport','郭威准许南唐百姓以人力或牲畜携米，禁止以船车运粮',31,'八月，己未，',None,[('帝','允许少量负载购粮，限制船车运输')],when='953年八月己未',place='后周、淮河',note='原文按运输方式限制，未给固定重量，不写成完全关闭粮食交易。')
add('wang_accuses_liuyan_in_memorial','王逵上表诬称刘言欲降南唐、攻潭州，已被军众废囚，自己已安抚朗州',32,'王逵遣使上表，','军府讫。”',[('王逵','派使上表，以虚假指控解释刘言被囚'),('刘言','被王逵上表指控欲降南唐并攻潭州')],when='953年八月，甲戌处理以前',place='湖南至后周朝廷',note='诬是主书明说；奏表中的刘言谋反与军众废囚不当真实行动。')
sup('wang_accuses_liuyan_in_memorial',32,oldaug,'甲戌，潭州王進逵奏：「朗州劉言與淮賊通連，差指揮使鄭交部領兵士，欲並當道。鄭交為軍眾所執，奔入武陵，劉言尋為諸軍所廢，臣已至朗州安撫訖。」','《旧五代史》八月甲戌保存王进逵另一奏报，说刘言与南唐勾连、军众将其废黜。','这是奏报内容，不当独立确证；奏报所称郑交与主书此前郑珓是否同人仍待核，不直接加别名或再造同案人物。',relation='adds')
add('wang_requests_seat_tanzhou','王逵请求将使府重新移回潭州',32,'且请复移', '使府治潭州。',[('王逵','请求把使府迁回潭州')],when='953年八月，甲戌以前',place='朗州、潭州')
add('di_guangyi_pacifies_hunan','后周派翟光裔赴湖南宣抚，批准王逵迁使府请求',32,'甲戌，','从其所请。',[('翟光裔','以通事舍人身份奉命到湖南宣抚'),('王逵','迁使府请求获准')],when='953年八月甲戌',place='后周朝廷至湖南',note='宣抚为朝廷派使处置，不擅自补使者已逐州访谈的细节。')
add('zhou_takes_langzhou','王逵返回长沙，安排周行逢掌管朗州',32,'逵还长沙，','以周行逢知朗州事，',[('王逵','回长沙并安排周行逢掌朗州'),('周行逢','受命掌管朗州事务')],when='953年八月朝廷处理湖南以后',place='长沙、朗州')
add('pan_kills_liuyan','王逵派潘叔嗣在朗州杀死刘言',32,'又遣潘叔嗣',None,[('王逵','派潘叔嗣杀刘言'),('潘叔嗣','奉派在朗州杀刘言'),('刘言','被潘叔嗣杀死')],when='953年八月，刘言被囚与迁府处理以后',place='朗州',note='接续六月被囚事件，死亡不提前放在六月；不将朝廷批准迁府等同明确授权杀人。')
sup('pan_kills_liuyan',32,oldaug,'詔劉言勒歸私第，委王進逵取便安置。','《旧五代史》奏报后记朝廷要求刘言归私第，交王进逵安排。','该诏仅记安置，没有明说朝廷诏令处死；主书实际遇害另有明确叙述，两层保留。',relation='adds')
add('bai_reports_river_repaired','白重赞奏报已堵塞黄河决口',33,'九月，己亥，',None,[('白重赞','以武成节度使身份奏报决口已堵塞')],when='953年九月己亥奏报',place='黄河决口地区',note='奏报为完成情况，未给准确修工完成日或段口坐标。')
add('khitan_attacks_leshou','契丹进犯乐寿',34,'契丹寇乐寿，','契丹寇乐寿，',[],when='953年九月条下，具体入侵日未载',place='乐寿')
add('liuyanzhang_kills_du','刘彦章等杀死乐寿都监杜延熙，企图响应契丹',34,'齐州戍兵右保宁都头刘彦章','谋应契丹，',[('刘彦章','杀都监并谋响应契丹'),('杜延熙','被驻军都头杀死')],when='953年九月乐寿被寇期间',place='乐寿',note='谋应为计划，未写成已经与契丹正式合兵。')
sup('liuyanzhang_kills_du',34,oldsep,'丁酉，深州上言：「樂壽縣兵馬都監杜延熙為戍兵所害。」','《旧五代史》九月丁酉记深州奏报杜延熙被戍兵杀害。','丁酉为报告日，不强定实际被杀日。',relation='adds',field='time_original')
add('liuyanzhang_party_executed','刘彦章响应契丹未成，与同党被处死',34,'不克，',None,[('刘彦章','谋应契丹未成，被处死')],when='953年九月乐寿叛乱后，处决日未载',place='乐寿')
sup('liuyanzhang_party_executed',34,oldsep,'朝廷急遣供奉官馬諤省其事，諤乃與萬友擒彥章等十三人斬之，餘眾奔齊州。','《旧五代史》明确记马谔与张万友捕获刘彦章等十三人，处死后其余军众逃回齐州。','十三人为被捕处死人数，不能把全部余众都记为处死；两将行动来自独立旧纪。',relation='adds')
for name,role in [('马谔','奉朝廷命调查并与张万友捕杀叛军'),('张万友','未参与叛乱，与马谔捕杀刘彦章等')]:
 quote='諤乃與萬友擒彥章等十三人斬之，餘眾奔齊州。';pk=person(name,34,role,quote,source=oldsep)
 edge='participation_zztj_291_0953_liuyanzhang_party_executed_'+pk;B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['liuyanzhang_party_executed'],role=role,status='draft'));claim('person_event',edge,'role',name+'：'+role+'。',34,quote,'职衔和未参与叛乱背景见同一旧纪前文，未把朝廷调查写为马谔独自斩杀全部余众。',source=oldsep)
# The following five investitures explicitly name the Southern Han ruler's sons.
father=person('刘晟',35,'以南汉君主身份册封五子',Q[35]['text'])
claim('person',father,'aliases','《新五代史》记南汉刘晟初名洪熙；弘熙与洪熙两种写法保留为同人的旧名。',35,'晟，初名洪熙，封晉王。','既有弘熙与洪熙别名保留，晟为新史明确记载的后名，不因更名另造人物。',source=newname)
for name,rank,start,end in [('刘继兴','卫王','继兴','为卫王，'),('刘璇兴','桂王','璇兴','为桂王，'),('刘庆兴','荆王','庆兴','为荆王，'),('刘保兴','祯王','保兴','为祯王，'),('刘崇兴','梅王','崇兴','为梅王。')]:
 code='southern_han_invests_'+name
 add(code,'刘晟册封'+name+'为'+rank,35,start,end,[('刘晟','册封儿子为'+rank),(name,'获封'+rank)],when='953年九月条下，具体封王日未载',place='南汉',note='南汉主刘晟为既有刘弘熙的后名，两种名字按同人识别；王号保留主书写法，祥祯差异另附。')
 relationship('刘晟',name,'父亲',35,Q[35]['text'],'立其子明示父子，方向为刘晟（旧名刘弘熙）是'+name+'的父亲；不推定五子同母。')
 sup(code,35,newsons,'十一年，晟病甚，封其子繼興衞王，璇興桂王，慶興荊王，保興祥王，崇興梅王。','《新五代史》乾和十一年也记五子封王，并称刘晟病重。','乾和十一年对应953年；保兴王号该书为祥王，主本为祯王，其余名单对应，原字分别保存。',relation='conflicts' if name=='刘保兴' else 'corroborates')
claim('person',people['刘继兴'],'aliases','《新五代史》明确记刘鋹初名继兴，保留同一人的两个名字。',35,'鋹，初名繼興，封衞王。','本次只核同人别名，不提前建立其继位或后世事件。',source=newchang)
add('wide_floods_953','青徐至安复、丹慈至贝镇的广大地区发生洪灾',36,'东自青、徐，',None,[],when='953年九月条下，洪灾具体起止未载',place='青州、徐州、安州、复州、丹州、慈州、贝州、镇州一带',note='为原书灾区范围概述，不将各州直接连成准确洪水边界或给未载水深。')
sup('wide_floods_953',36,oldaug,'是月所在州郡奏，霖雨連綿，漂沒田稼，損壞城郭廬舍。','《旧五代史》八月末概述连雨淹没庄稼、损坏城郭房屋。','两书灾情时间范围不同，可能为持续连雨，分别保留，未认定所有州同日受灾。',relation='adds')
add('guowei_autumn_illness','郭威入秋后患风痹，影响进食与行走；术士建议散财禳灾',37,'帝自入秋得风痹疾，','术者言宜散财以禳之。',[('帝','入秋后患病，进食行走受影响')],when='953年入秋以后，具体起病日未载',place='后周宫廷',note='风痹保留古病名，不推现代医学确诊；散财禳灾是术士建议，不写成有效治疗结论。')
add('guo_discusses_capital_rites','郭威想祀南郊，但因以往多在洛阳而犹豫，执政认为可在都城祭祀',37,'帝欲祀南郊，','何必洛阳！”',[('帝','因旧制地点疑虑而讨论郊祀安排')],when='953年秋筹备郊祀时',place='大梁、洛阳',note='执政未具名，不自动写成范质或李谷亲口回答。')
add('daliang_builds_ritual_sites','后周开始在大梁建圜丘、社稷坛和太庙',37,'于是，始筑圜丘、社稷坛，','作太庙于大梁。',[],when='953年秋郊祀地点议定以后',place='大梁',note='始筑为开始建造，不说全部工程已在某天完工。')
add('feng_collects_spirit_tablets','郭威派冯道到洛阳迎接太庙、社稷神主',37,'癸亥，',None,[('冯道','奉命赴洛阳迎接太庙社稷神主'),('帝','派冯道迎神主')],when='953年九月条下癸亥，《通鉴》记日',place='洛阳至大梁')
sup('feng_collects_spirit_tablets',37,oldoct,'詔中書令馮道赴西京迎奉太廟神主。','《旧五代史》十月条记冯道赴西京迎太庙神主。','主书九月条癸亥与旧书十月无单独纪日不同，保留发令与行程记载差异，未强改主日。',relation='adds',field='time_original')
add('southern_han_general_amnesty','南汉颁布大赦',38,'南汉大赦。','南汉大赦。',[('刘晟','以南汉君主身份颁布大赦')],when='953年九月后至十一月前条下，具体大赦日未载',place='南汉')
add('four_suburban_altars_approved','太常请求参照洛阳建四郊祭坛，郭威批准',38,'冬，十一月，己丑，','从之。',[('帝','批准太常参照洛阳营建四郊坛的请求')],when='953年十一月己丑',place='大梁',note='太常为官署，未具名请求者，不编田敏亲自此日上奏。')
add('tablets_arrive_daliang','神主抵达大梁，郭威到西郊迎接，将其祔享太庙',38,'十二月，丁未朔，',None,[('帝','到西郊迎接并将神主安置太庙祭享')],when='953年十二月丁未朔，《通鉴》纪日',place='大梁西郊、太庙')
sup('tablets_arrive_daliang',38,olddec,'十二月戊申，雨木冰。是日，四廟神主至西郊，帝郊迎奠饗，奉神主入於太廟，設奠安神而退。','《旧五代史》记十二月戊申四庙神主至西郊，郭威迎接、安置太庙。','丁未朔与戊申纪日不同，保存两读，不自行换算后判定；四庙神主范围与主书前称太庙社稷分别保留。',relation='conflicts',field='time_original')
add('wangyin_usurps_orders_extracts_money','王殷以私帖处理本应奉敕的河北驻军事务，还大量搜刮民财',39,'鄴都留守、天雄节度使','又多掊敛民财。',[('王殷','以私帖代敕处理驻军事务并搜刮财物')],year=None,when='953年十二月入朝以前一段时期的概述，具体起始未载',place='邺都、河北',note='恃功专横为史書评价，实际行为分明；帖子不是现代网络发帖。')
add('guo_warns_wangyin_money','郭威派人告诉王殷国库富足，需用可取，不必搜刮',39,'帝闻之不悦，','何患无财！”',[('帝','派人规劝王殷用国库财物而非搜刮'),('王殷','收到郭威规劝')],when='953年王殷被疑前，具体传谕日未载',place='后周朝廷、邺都')
add('he_fujin_secretly_accuses_wangyin','何福进入朝，秘密报告王殷隐情，郭威因此起疑',39,'成德节度使何福进','帝由是疑之。',[('何福进','在入朝时密报王殷隐情'),('帝','因报告而更加怀疑王殷')],when='953年十二月甲子',place='后周朝廷',note='素恶为史書描述何福进此前不喜欢王殷，阴事内容未载，不编具体阴谋细节。')
sup('he_fujin_secretly_accuses_wangyin',39,olddec,'甲子，鎮州節度使何福進來朝。','《旧五代史》同记十二月甲子何福进入朝。','该书只载来朝，不凭省略认为密报绝无发生，也不当独立密报内容证明。')
add('wangyin_held_as_capital_patrol','王殷入朝，郭威留他任京城内外巡检',39,'乙丑，',None,[('王殷','入朝后留任京城内外巡检'),('帝','留王殷在京任巡检')],when='953年十二月乙丑',place='后周京城')
sup('wangyin_held_as_capital_patrol',39,olddec,'乙丑，鄴都留守王殷來朝。','《旧五代史》同日记王殷来朝。','旧纪未列巡检任职，作为来朝日期的印证。')
add('zhe_deyi_repels_qiao','折德扆奏报击退北汉将乔赟对府州的进犯',40,'戊辰，',None,[('折德扆','以府州防御使身份奏报击退来敌'),('乔赟','进犯府州后被击退')],when='953年十二月戊辰奏报',place='府州',note='报告日与实际交战日分开，未编双方兵数、伤亡及追击距离。')

reviews={31:'旱灾、饥民被阻、郭威准买米、南唐备军粮与八月限制运输分录；允许买卖不写成免费赈粮，运输方式不换固定斤数。',32:'王逵诬表、迁府请求与批准、周掌朗州、潘杀刘分开；旧纪奏报当王逵说法，安置诏不写成授权处死，郑交姓名未强合前段郑珓。',33:'奏塞是报告已完成，不给精确工期或坐标。',34:'契丹入寇、刘杀杜谋应与失败处决分开，旧纪补马谔张万友、十三人及余众奔齐；丁酉为报告。',35:'五子逐一册封并补父子关系；刘晟复用旧弘熙，继兴与鋹明文同人。保兴祯祥王号异读，乾和十一年同953但具体日未知。',36:'原书区域性洪水概述保范围，不绘假疆界；旧八月霖雨与主九月可为连灾但未硬定同一天。',37:'郭威古病名及术士建议、郊祀地点议论、始筑坛庙与冯道迎神分录；诊断不现代化，旧十月记行与主九月癸亥并列。',38:'南汉赦、十一月太常请建四坛与十二月神主抵达分开；丁未戊申与神主范围差异保存。',39:'王殷专横行为、郭威规劝、何福进甲子密报及王乙丑来朝留任分别记，不补阴事内容。',40:'戊辰为折德扆奏报，不硬定战斗发生日，乔赟未被误写为阵亡。'}
assert not (P/'publication.json').exists()
for n in range(31,41):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=953,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(31,41)],next_paragraph=Q[41]['id'],next_volume=291,next_year=953,supplements=supplements,excluded_non_body=[],coverage='卷291原63—72行连续十段；953年末六段尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(31,41)],source_issues_review='刘晟旧名与继兴后名明确证据单列，五子王号祯祥异读、神主丁未戊申及迎奉发令时间分别保留；古病名无现代诊断，纸本异文待核。',plain_language_review='首次逐条检查新标题、人物介绍、角色、关系方向及事实解释，赈济与购粮、奏表与事实、任命与执行、奏报日与战斗日分清；正文使用现代白话，逐字引用保底本。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
