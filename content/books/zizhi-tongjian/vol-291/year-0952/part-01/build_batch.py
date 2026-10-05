# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 1–7."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,26))
COMMIT='0b5d180c84d59cd6b51901d4787f2720c08451e0'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
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
main_sources = ['tongjian-291-952-september']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0952-p001-p007',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-952-september':'卷291·广顺二年·九月至十月及卷首年界','jiuwudaishi-112-september-952':'卷112·太祖本纪三·广顺二年九月'}
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
    labels={'tongjian-291-952-september':'卷291·广顺二年·九月至十月及卷首年界','jiuwudaishi-112-september-952':'卷112·太祖本纪三·广顺二年九月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺二年（952年九月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0952_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=952, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='952年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0952_' + code
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
        edge = 'participation_zztj_291_0952_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0952_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','蜀主':'孟昶','赵进':'赵进（后蜀将领）','张仿':'张亻放（楚军指挥使）'})
NEW_ALIASES={'裴坚':['裴堅'],'吴延福':['吳延福'],'刘诚诲':['劉誠誨','刘诲','劉誨'],'何继筠':['何繼筠'],'赵进（后蜀将领）':[],'欧阳广':['歐陽廣'],'蒲公益':[],'朱全琇':['硃全琇'],'宇文琼':['宇文瓊'],'彭万和':['彭萬和'],'潘叔嗣':[],'张文表':['張文表'],'刘瑫（楚蛮酋）':[]}
NEW_DESCRIPTIONS={'裴坚':'吴越丞相。952年九月甲寅朔去世。此前履历和生年未载。','吴延福':'吴越台州刺史。952年九月裴坚去世后任同参相府事。生卒年未载。','刘诚诲':'后周龙捷都指挥使。952年受成德节度使何福进派遣驻贝州抵御契丹。《旧五代史》同场写刘诲，按同一军职及行动对应，原字保留。生卒年未载。','何继筠':'后周牙内都指挥使。《旧五代史》记952年九月与刘诲等率兵抵御契丹。生卒年未载。','赵进（后蜀将领）':'后蜀奉銮肃卫都虞候。952年率兵向利州，得知后周在关中集兵是为了防备北汉后返回。缺少与已录后唐贝州刺史赵进的连续履历证据，暂分人物。生卒年未载。','欧阳广':'吉水人。952年上书警告边镐不适合统帅湖南，建议另择将帅、增兵，未获回复。生卒年未载。','蒲公益':'朗州牙将。952年与王逵等受刘言任命为指挥使。后文同一行动写薄公益，字形对应待同场回查，未据姓字另造人物。生卒年未载。','朱全琇':'朗州牙将。952年与王逵等受刘言任命为指挥使，姓名底本写硃全琇。生卒年未载。','宇文琼':'朗州牙将。952年与王逵等受刘言任命为指挥使。生卒年未载。','彭万和':'朗州牙将。952年与王逵等受刘言任命为指挥使。生卒年未载。','潘叔嗣':'朗州人、刘言麾下牙将。952年任指挥使。史书称其果敢，与周行逢、张文表交好、共同成事。生卒年未载。','张文表':'朗州人、刘言麾下牙将。952年任指挥使。史书称其善战，与周行逢、潘叔嗣交好、共同成事。生卒年未载。','刘瑫（楚蛮酋）':'楚地地方首领，任土团都指挥使。952年被任为西境镇遏使，防备苻彦通。原书未明具体族属，不与后周文官刘涛混同，生卒年未载。'}
NEW_DEATH_YEARS={'裴坚':952}
old='jiuwudaishi-112-september-952'
add('pei_jian_dies','吴越丞相裴坚去世',1,'九月，甲寅朔，','吴越丞相裴坚卒。',[('裴坚','以吴越丞相身份去世')],when='952年九月甲寅朔',place='吴越')
add('wu_yanfu_prime_minister','钱弘俶让台州刺史吴延福同参相府事',1,'以台州刺史吴延福',None,[('吴延福','由台州刺史获任同参相府事')],when='952年九月甲寅朔',place='吴越',note='任职承吴越政局，未列搬迁日期；并参相府事不改成独任最高丞相。')
add('guo_forbids_northern_raids','郭威禁止北边吏民进入契丹境内俘掠',2,'庚午，',None,[('帝','敕北边吏民不得跨境俘掠')],when='952年九月庚午',place='后周、契丹边境',note='禁俘掠不是禁止所有商旅往来。')
sup('guo_forbids_northern_raids',2,old,'詔北面沿邊州鎮，自守疆埸，不得入北界俘掠。','《旧五代史》同日也记沿边州镇守境、不得入北界俘掠。','北界按当时契丹边界理解，没有给现代边界线或疆域多边形。')
add('gao_mohan_crosses_hulu','高谟翰用芦苇筏渡胡卢河，率契丹军进至冀州',3,'契丹将高谟翰','至冀州，',[('高谟翰','以苇筏渡河并进军冀州')],when='952年九月，具体渡河日未载',place='胡卢河至冀州',note='苇筏为渡河工具，未给筏数、军队总量。')
add('he_fujin_sends_liuchenghui','何福进派刘诚诲等驻贝州抵御契丹',3,'成德节度使何福进','屯贝州以拒之。',[('何福进','派龙捷军将领驻贝州'),('刘诚诲','以龙捷都指挥使身份驻贝州迎敌')],when='952年九月高谟翰入境以后',place='成德军、贝州')
sup('he_fujin_sends_liuchenghui',3,old,'乙亥，鎮州奏，契丹寇深、冀州，遣龍捷都指揮使劉誨、牙內都指揮使何繼筠等率兵拒之而退。','《旧五代史》乙亥记镇州奏报契丹寇深冀，派刘诲、何继筠等率兵抵御。','刘诲与刘诚诲按同一龙捷职衔和同役对应；乙亥为奏报，未把它认定为每一步进退都发生当日。',relation='adds')
claim('person',people['刘诚诲'],'aliases','《旧五代史》同役称刘诚诲为刘诲。',3,'遣龍捷都指揮使劉誨、牙內都指揮使何繼筠等率兵拒之而退。','同职同一深冀入侵对应，保留简名异说，没有只凭刘姓合并。',source=old)
pk=person('何继筠',3,'以牙内都指挥使身份率兵抵御契丹','遣龍捷都指揮使劉誨、牙內都指揮使何繼筠等率兵拒之而退。',source=old)
ek='participation_zztj_291_0952_he_fujin_sends_liuchenghui_'+pk
B['person_events'].append(dict(key=ek,person_key=pk,event_key=E['he_fujin_sends_liuchenghui'],role='以牙内都指挥使身份率兵抵御契丹',status='draft'))
claim('person_event',ek,'role','何继筠以牙内都指挥使身份率兵抵御契丹。',3,'遣龍捷都指揮使劉誨、牙內都指揮使何繼筠等率兵拒之而退。','同行将领来自独立旧本纪，未推其与何福进的血缘关系。',source=old)
add('khitan_retires_north','契丹听说后周军前来，迅速撤军北渡',3,'契丹闻之，','遽引兵北渡。',[],when='952年九月后周军赴贝州后',place='冀州北撤',note='北渡未再指定河名，未把退军写成所有被掳者都已获救。')
add('captives_resist_killed','被掳的冀州丁壮见后周军后呼喊并准备反抗，官军未响应，契丹杀死他们',3,'所掠冀州丁壮',None,[],when='952年九月契丹北撤途中',place='冀州北撤路上',note='数百人为被掳群体规模；官军不敢应是史书所记，不给未具名将领补出拒援言辞或动机。')
sup('captives_resist_killed',3,old,'冀部被擄者望見官軍，鼓噪不已，官軍不敢進，其丁壯盡為蕃軍所殺而去。','《旧五代史》也记被掳丁壮见官军鼓噪，官军不敢进，丁壮尽被杀。','两书应与进用字分别保留，不把军队未进改成将领已经下令处决被掳者。')
add('li_tinggui_requests_reinforcements','李廷珪奏报后周集兵关中，请求增兵防备',4,'蜀山南西道节度使李廷珪','请益兵为备。',[('李廷珪','奏请增兵防备关中集兵')],when='952年九月，具体奏请日未载',place='后蜀山南西道、关中',note='后周集兵目的后来说明是防北汉，最初请求只反映后蜀的防备判断。')
add('zhao_jin_heads_lizhou','孟昶派赵进率兵前往利州',4,'蜀主遣奉銮肃卫都虞候赵进','将兵趣利州，',[('蜀主','派赵进率兵赴利州'),('赵进','以奉銮肃卫都虞候身份率兵向利州')],when='952年九月李廷珪请兵后',place='后蜀至利州',note='赵进限定本次后蜀将领，缺与后唐贝州刺史连续履历，不只凭同名合并。')
add('shu_reinforcements_return','后蜀得知后周集兵防北汉，增援军队返回',4,'既而闻周人',None,[('赵进','所率增援军在得知后周集兵目的后返回')],when='952年九月向利州行军后',place='利州方向至后蜀',note='引还为撤回军队，不补已经与后周交战。')
add('bian_hao_hunan_assessment','史书评价边镐在湖南管理混乱、不得人心',5,'唐武安节度使边镐，','不合众心。',[('边镐','被史书评价为昏庸懦弱、缺乏决断，政务由多方掌控')],year=None,when='951年取湖南后至952年秋的一段时期概述，具体起止未载',place='湖南',note='政出多门为管理多头，未给每个具体机关或全部民意调查。')
add('ouyang_guang_warns_hunan','欧阳广上书警告边镐不宜统湖南，建议另择将帅增兵，未获回复',5,'吉水人欧阳广',None,[('欧阳广','上书建议换统帅、增兵救湖南')],when='952年九月条下，具体上书日未载',place='南唐',note='必丧湖南是欧阳广的预测，不提前写成这一天已失湖南；不报为未回复，不等于具体处分。')
add('li_jing_orders_langzhou','李璟让边镐经略朗州',6,'唐主使镐','经略朗州，',[('唐主','让边镐处理进取朗州事务'),('边镐','受命经略朗州')],when='952年九月湖南反攻以前',place='湖南、朗州',note='经略是部署任务，不等于朗州已被攻取。')
add('bian_neglects_defense','边镐听到从朗州来者称刘言忠顺，因此未备战',6,'有自朗州来者，','镐由是不为备。',[('边镐','因听到刘言忠顺的说法而不设防')],when='952年朗州反攻以前',place='湖南',note='忠顺是来者所言，不当作已确定刘言以后不会反攻。')
add('liu_yan_refuses_court','李璟召刘言入朝，刘言没有前往',6,'唐主召刘言入朝，','言不行，',[('唐主','召刘言入朝'),('刘言','没有应召前往')],when='952年九月朗州部署反攻以前',place='南唐与朗州')
add('wang_zhou_advise_attack_bian','刘言担心南唐讨伐，王逵认为可击边镐，周行逢劝尽速行动',6,'谓王逵曰：','不可图也。”',[('刘言','向王逵问南唐可能讨伐时的应对'),('王逵','认为朗州有险有兵、边镐不得人心，可出击'),('周行逢','劝立即行动，避免对方作准备')],when='952年九月刘言不赴南唐后',place='朗州',note='唐必伐我、可一战擒是人物判断；本段止于谋划，未提前录十月实际反攻。')
add('liu_yan_ten_commanders','刘言任王逵等十人为指挥使，分派出兵',6,'言乃以逵、行逢','部分发兵。',[('刘言','任十名部将为指挥使、分派出兵'),('王逵','受任指挥使'),('周行逢','受任指挥使'),('何敬真','受任指挥使'),('张仿','受任指挥使'),('蒲公益','受任指挥使'),('朱全琇','受任指挥使'),('宇文琼','受任指挥使'),('彭万和','受任指挥使'),('潘叔嗣','受任指挥使'),('张文表','受任指挥使')],when='952年九月反攻湖南部署期间',place='朗州',note='张仿与951年同朗州军府、同王周何议事的张亻放按连续职务和部件字形校核同人，复用原key；未提前录所有人后来战果。')
claim('person',people['张亻放（楚军指挥使）'],'aliases','张仿为951年电子底本拆字写作张亻放的朗州指挥使，按连续军府履历复用同一主体。',6,'言乃以逵、行逢及牙将何敬真、张仿、蒲公益、硃全琇、宇文琼、彭万和、潘叔嗣、张文表十人皆为指挥使，部分发兵。','与951年朗州共同议军府的同组职务、人名和亻放构件对应，保存本年明确张仿写法；既有key和旧档案不改，别名另用守卫更新。')
add('zhou_zhang_pan_cooperation','史书记载周行逢善于谋划、张文表善于作战、潘叔嗣果敢，三人交好并合作',6,'叔嗣、文表，',None,[('周行逢','被史书称能谋，与两将交好合作'),('张文表','被史书称善战，与两将交好合作'),('潘叔嗣','被史书称果敢，与两将交好合作')],year=None,when='三名朗州将领一段时期的综合描述，具体起止年月未载',place='朗州',note='相须成功、情款亲昵为长期概述，未把每次合作都强定952年同一天。')
q=span(6,'叔嗣、文表，')
for a,b in [('周行逢','张文表'),('周行逢','潘叔嗣'),('张文表','潘叔嗣')]:relationship(a,b,'朋友',6,q,'原文明示三人情款亲昵、相互合作，为该时期交好；具体起止年月未载。')
add('zhou_rejects_fu_aid','诸将欲请苻彦通援助，周行逢以此前焚掠为由反对，最终停止邀请',7,'诸将欲召溆州酋长苻彦通','乃止。',[('周行逢','以此前焚掠百姓为由反对召苻彦通助战')],when='952年九月朗州反攻谋划时',place='朗州、溆州',note='对族群的贪而无义等说法为周行逢的历史话语，展示只记录拒绝援军的行动与理由；未默认支持此概括。')
add('liu_tao_western_commander','朗州任刘瑫为西境镇遏使，防备苻彦通',7,'然亦畏彦通为后患，',None,[('刘瑫（楚蛮酋）','以土团都指挥使身份获补西境镇遏使')],when='952年九月决定不请苻彦通后',place='朗州西境',note='具体授令者未具名；群蛮为原书概括，未给现代族别，未将镇遏职改成正式节度使。')
# Append the newly available seniority variant to the exact previously ingested paragraph.
qold='故第四姊追封福慶長公主。'
pk=person('福庆长公主（郭威妹）',1,'《旧五代史》称其为郭威已故的第四位姐姐，与《资治通鉴》称妹妹的记载存在分歧',qold,source=old)
start=len(supplements)-1
claim('person',pk,'description','《旧五代史》九月条称福庆长公主为郭威的已故第四姊；《资治通鉴》卷290前段称帝妹，长幼存在异说。',1,qold,'同封号及郭威姊妹背景作为独立补证，主书与旧书长幼说法并列，不只凭一书记载重写旧人物及关系。',source=old,relation='conflicts')
rel=next(x for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for x in json.loads(f.read_text())['person_relationships'] if x['person_a_key']=='person_郭威' and x['person_b_key']==pk and x['relation_type']=='兄长')
B['person_relationships'].append(dict(rel,status='draft'));reused.add(rel['key'])
# The prior relation's other endpoint needs an unchanged person record and its own evidence.
person('郭威',1,'为旧史所记追封福庆长公主的君主',qold,source=old)
claim('person_relationship',rel['key'],'description','郭威与福庆长公主为手足；《资治通鉴》称妹、《旧五代史》称第四姊，长幼有异说。',1,qold,'本次补充旧书与原兄长标签相冲突的证据，保留原主书关系记录；后续需校核长幼，未另建一条相反关系。',source=old,relation='conflicts')
for row in supplements[start:]:row['primary_paragraph_id']='zztj-v290-y0952-p032'
reviews={1:'甲寅裴卒、吴延福参府分录，任职承吴越政局。',2:'庚午禁边界俘掠与旧同日诏印证，不扩商旅禁止。',3:'苇筏渡河、何遣贝州、契丹北渡与冀人鼓噪被杀分开。旧补刘诲、何继筠，刘名按同职同役对应；乙亥为奏报，未给某将拒援动机。',4:'后蜀疑关中兵而请增、赵进趋利、知备北汉引还分开；赵进与早先后唐同名人暂不合。',5:'边治多头为史评，欧阳广上书预判不当已亡湖南，未回复不编处分。',6:'经略朗州、来言忠顺不备、召刘不赴、王周劝策、十将分派及三人友情分别记，未来十月战果未提前。张仿复用951张亻放主体，新别名有当前明确写法与同组履历。',7:'拒召苻为援与以刘瑫防后患分开；周的族群评价保为历史话语，不改为本站断言，土团名不换现代族名。'}
assert not (P/'publication.json').exists()
for n in range(1,8):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,8)],next_paragraph=Q[8]['id'],next_volume=291,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷291原6—12行连续七段；十月长篇战事从下一段继续，952年尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,8)],source_issues_review='原文块含卷首结构，当前只引用正文6—12行，原字与纸本未核说明保留。张仿与951拆字名按同军府同组履历校核；赵进不强合后唐同名者。旧书第四姊与主书帝妹异说另外回指已录卷290段32，不伪放入当前主段；关系旧值保留、相反证据新增。',cross_volume_supplements=[dict(primary_paragraph_id='zztj-v290-y0952-p032',subject_key=k,issue='福庆长公主长幼异说，新增旧五代史证据，原人物及关系档案保留') for k in [pk,rel['key']]],plain_language_review='首次逐条检查展示标题、人物、角色、日期、关系及事实说明。声音与行动、预测与结果、知情与误判、历史话语与本站判断分清；引文原字不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
