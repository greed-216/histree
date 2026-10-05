# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 952 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
COMMIT='1fbdfd3758d9dbd47716e033cd59ac5314255f5a'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-952-january-continuation','jiuwudaishi-112-january-952','xinwudaishi-011-second-year-952']:
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
main_sources = ['tongjian-290-952-january-continuation']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0952-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-053-cui-yan-case':'卷53·杂传四十一·慕容彦超传·崔周度阎弘鲁案','jiuwudaishi-112-february-952':'卷112·太祖本纪三·广顺二年二月','jiuwudaishi-112-march-952':'卷112·太祖本纪三·广顺二年三月','songshi-478-pan-you':'卷478·世家一·南唐李氏·潘佑附传'}
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
for n in range(9, 17):
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
    labels={'xinwudaishi-053-cui-yan-case':'卷53·杂传四十一·慕容彦超传·崔周度阎弘鲁案','jiuwudaishi-112-february-952':'卷112·太祖本纪三·广顺二年二月','jiuwudaishi-112-march-952':'卷112·太祖本纪三·广顺二年三月','songshi-478-pan-you':'卷478·世家一·南唐李氏·潘佑附传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺二年（952年正月至三月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0952_02_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_290_0952_' + code
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
        edge = 'participation_zztj_290_0952_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0952_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','冯延己':'冯延巳','延鲁':'冯延鲁','潘佐':'潘佑','张纬':'张纬（李金全推官）','郑仁诲':'郑仁诲'})
NEW_ALIASES={'崔周度':[],'阎弘鲁':['閻弘魯'],'潘佑':['潘佐'],'王克贞':['王克貞'],'郑仁诲':['鄭仁誨'],'徐景运':['徐景運']}
NEW_DESCRIPTIONS={'崔周度':'慕容彦超的判官。曾劝慕容彦超不要反叛，后受命搜查阎弘鲁家财，为其说明财物已尽，最终被认为庇护阎弘鲁，在市中被斩。生年未载，死亡年为952年。','阎弘鲁':'阎宝之子，前陕州司马。952年兖州被围时因惧慕容彦超，倾家献财，仍被认为藏有财物，与妻子被拘押、拷打致死。生年未载。','潘佑':'南唐文臣。《资治通鉴》电子底本本段先写潘佐，后简称佑；结合《宋史》韩熙载、徐铉荐其入李璟朝的文学履历，按潘佑记录，原字保留、纸本异文待核。《宋史》记其善论议、入秘书省及崇文馆。生卒年未据本次原文定年。','王克贞':'庐陵人。952年南唐初设贡举时，成为三名进士及第者之一。本段未列另外两人姓名，生卒年未载。','郑仁诲':'晋阳人，后周内客省使、恩州团练使。952年三月任枢密副使，新旧五代史同日记载。生卒年尚未录入。','徐景运':'南唐前镇海节度使。952年任中书侍郎、同平章事，与冯延巳、孙晟同为宰相。未与徐景迁、徐景通混同，生卒年未载。'}
NEW_DEATH_YEARS={'崔周度':952,'阎弘鲁':952}
case='xinwudaishi-053-cui-yan-case';feb='jiuwudaishi-112-february-952';mar='jiuwudaishi-112-march-952';old='jiuwudaishi-112-january-952';nw='xinwudaishi-011-second-year-952';pan='songshi-478-pan-you'
add('cui_zhoudu_advises_murong','崔周度劝慕容彦超撤防归诚，不要因疑惧反叛',9,'初，彦超将反，','彦超怒。',[('崔周度','以判官身份劝止慕容彦超反叛'),('慕容彦超','听到劝谏后发怒')],year=None,when='951年末至952年兖州被围以前的追述，具体劝谏日未载',place='兖州',note='伯禽与三位反叛者是劝谏中的历史举例，不新建他们在952年参与本次谈话的事件。')
sup('cui_zhoudu_advises_murong',9,case,'初，彥超之反也，判官崔周度諫曰：','《新五代史》也记崔周度在慕容彦超反叛之初劝谏。','两书劝辞有差别，不能把不同引语拼成同一逐字讲话。')
add('murong_confiscates_city_wealth','兖州被围后，慕容彦超征取城中财产供军，许多人因被指藏财而死',9,'及官军围城，','坐匿财死者甚众。',[('慕容彦超','征取士民财产供军，并处死被认为藏财者')],when='952年兖州被围以后，具体日期未载',place='兖州',note='匿财是其追究的名目，未给每人的实际藏财证据；甚众不编数量。')
add('yan_honglu_offers_property','阎弘鲁惧怕慕容彦超，倾家献财',9,'前陕州司马阎弘鲁，','倾家为献。',[('阎弘鲁','以前陕州司马身份倾家献财')],when='952年兖州被围、征财期间',place='兖州')
relationship('阎宝','阎弘鲁','父亲',9,'前陕州司马阎弘鲁，宝之子也，','原文明确父子关系，宝承阎姓沿已有阎宝主体，方向为阎宝是阎弘鲁的父亲。')
add('cui_searches_yan_house','慕容彦超仍怀疑阎弘鲁藏财，命崔周度搜其家',9,'彦超犹以为有所匿，','宜无所爱。”',[('慕容彦超','怀疑仍有财物，命人搜家'),('崔周度','受命搜查，劝阎弘鲁不要保留财物'),('阎弘鲁','受到继续追索财物的威胁')],when='952年阎弘鲁献财以后',place='兖州',note='怀疑不等于证明确实藏财；崔周度说死生系财是警告，不当本站对量刑制度的结论。')
sup('cui_searches_yan_house',9,case,'弘魯遣家僮與周度斸掘搜索無所得。彥超又遣鄭麟持刃迫之，','《新五代史》补记家僮与崔周度挖掘搜索未得财物，慕容彦超又派郑麟持刀逼迫。','独立补充搜家和威胁细节，郑麟沿已录都押牙主体，不把威胁写成他亲手杀阎弘鲁。',relation='adds')
add('yan_family_says_property_exhausted','阎弘鲁哭求妻妾交出全部财物，妻妾说已交尽',9,'弘鲁泣拜其妻妾曰：','皆曰：“竭矣！”',[('阎弘鲁','请求妻妾交出全部所有以救命')],when='952年搜家期间',place='兖州',note='妻妾无名，不猜人数与身份；竭矣为她们回答，不能由后来找到一件物品就认定所有人故意隐瞒。')
add('yan_couple_imprisoned','崔周度向慕容彦超说明财物已尽，慕容彦超不信，将阎弘鲁夫妻下狱',9,'周度以白彦超，','收弘鲁夫妻系狱。',[('崔周度','报告阎家的回答'),('慕容彦超','不信报告，将阎弘鲁夫妻拘押'),('阎弘鲁','与妻子被拘押')],when='952年搜家之后',place='兖州',note='妻子未具名，不与其他同姓女子自动合并。')
sup('yan_couple_imprisoned',9,case,'下弘魯及周度于獄。','《新五代史》写阎弘鲁与崔周度被下狱。','《资治通鉴》此句为阎弘鲁夫妻下狱，拘押对象叙述不同，并列保留。',relation='conflicts')
add('wet_nurse_offers_gold','乳母在泥中找到金缠臂，献给慕容彦超，希望赎出主人',9,'有乳母于泥中','冀以赎其主。',[],when='952年阎家被拘押后',place='兖州',note='赎其主是她的目的，不写成成功赎出；乳母未具名，不虚构姓名。')
add('yan_couple_tortured_to_death','慕容彦超仍认定阎家藏财，将阎弘鲁夫妻拷打致死',9,'彦超曰：“果然，','肉溃而死。',[('慕容彦超','以藏财怀疑继续拷打阎弘鲁夫妻'),('阎弘鲁','与妻子被拷打致死')],when='952年兖州被围、征财期间，具体死日未载',place='兖州',note='所匿必犹多为慕容彦超的推断，不认定阎家仍藏很多财产。')
sup('yan_couple_tortured_to_death',9,case,'遣軍校笞弘魯夫婦肉爛而死，','《新五代史》也记慕容彦超派军校把阎弘鲁夫妻拷打致死。','具体执行军校未具名，不推为郑麟本人。')
add('cui_zhoudu_executed','慕容彦超以庇护阎弘鲁为由，在市中斩杀崔周度',9,'以周度为阿庇，',None,[('慕容彦超','以庇护为由杀害崔周度'),('崔周度','被指庇护阎弘鲁，在市中被斩')],when='952年阎弘鲁夫妻死后，具体日期未载',place='兖州市中',note='阿庇是慕容彦超所加理由，不作为本站独立认定崔周度犯罪。')
sup('cui_zhoudu_executed',9,case,'遂斬周度于市。','《新五代史》也记崔周度在市中被斩。','不提前引用同传五月慕容死与朝廷追赠。')
add('zhe_defeats_northern_han_fuzhou','折德扆在府州击败北汉进攻，杀二千余人',10,'北汉遣兵','杀二千馀人。',[('折德扆','以府州防御使身份击败北汉进攻')],when='952年二月攻拔岢岚军以前，具体交战日未载',place='府州',note='没有具名北汉领军者，不猜刘崇亲临。')
sup('zhe_defeats_northern_han_fuzhou',10,feb,'二月庚寅，府州防卸使折德扆奏，河東賊軍寇境，率州兵破之，斬首二千級。','《旧五代史》二月庚寅记折德扆奏报破军、斩首二千。','主书二千余人与此书二千概数保留；庚寅为奏报，不能直接当战日，防卸底本字形不改。',relation='adds')
add('zhe_takes_kelan','折德扆奏报攻取北汉岢岚军，并派兵驻守',10,'二月，庚子，',None,[('折德扆','奏报攻取岢岚军并驻兵')],when='952年二月庚子奏报，具体攻取日未另载',place='岢岚军')
sup('zhe_takes_kelan',10,feb,'庚子，府州防卸使折德扆奏，收河東界岢嵐軍。','《旧五代史》同日记折德扆奏报收取岢岚军。','与主书奏报日期一致，未编造攻城具体过程。')
add('guo_releases_yan_jingquan','郭威释放燕敬权等，让他们返回南唐并转告反对助叛的意思',11,'甲辰，帝释燕敬权','得无非计乎！”',[('帝','释放南唐被俘将领并让其转告对助叛的不满'),('燕敬权','获释放，奉命返回南唐转告郭威的话')],when='952年二月甲辰',place='后周至南唐',note='转告是命令，不能认定释放当天已经见到李璟。')
sup('guo_releases_yan_jingquan',11,old,'戊寅，徐州部送沭陽所獲賊將燕敬權等四人至闕下，詔賜衣服金帛，放歸本土，','《旧五代史》在正月戊寅记四名被俘将领被送到朝廷，获衣服金帛后放归。','与主书二月甲辰释放条的月日不同，保留两书记时与四人数，不把它们拼成两次已确定释放同一人。',relation='conflicts')
add('li_jing_returns_zhou_people','李璟惭愧，把此前所得中原人礼送归还',11,'唐主大惭，','皆礼而归之。',[('唐主','礼送此前所得中原人归还')],when='952年郭威释放燕敬权、传话以后',place='南唐至中原',note='中国人在此为中原方面的人，不译成现代国籍；名单和总数未载，未提前用旧史路昌祚故事替代全部对象。')
add('han_xizai_opposes_northern_war','韩熙载认为后周治理已稳固，反对南唐轻率进攻中原',11,'唐之言事者','必有害无益。”',[('韩熙载','以中书舍人身份反对轻率对后周用兵')],when='952年南唐礼送中原人归还前后',place='南唐朝廷',note='为治已固、有害无益是韩熙载对形势的判断，不扩大为各国皆认可的事实。')
add('tang_khitan_maritime_diplomacy','南唐自李昪以来常泛海通契丹，互赠财物并约为兄弟',12,'唐自烈祖以来，','约为兄弟。',[],year=None,when='李昪在位至李璟时期的长期追述，具体各次出使年月未载',place='南唐与契丹间海路',note='兄弟为外交约定，不建血缘或具体君主之间的永久结义关系；更相馈遗不补金额。')
add('tang_khitan_diplomatic_assessment','史书评价契丹只图南唐财物，没有真正为南唐出力',12,'然契丹利其货，',None,[],year=None,when='南唐与契丹交往的一段时期评价，具体起止年份未载',place='南唐、契丹',note='这是史家的外交评价，不当作每名使者的已证实动机。')
add('li_jing_promotes_literati','李璟喜爱文学，韩熙载等文臣因此获高官',13,'唐主好文学，','之徒皆至美官。',[('唐主','重视文学，使多名文臣获高官'),('韩熙载','以文学获美官'),('冯延己','以文学获美官'),('延鲁','以文学获美官'),('江文蔚','以文学获美官'),('潘佐','以文学获美官'),('徐铉','以文学获美官')],year=None,when='李璟在位时期的概述，具体各人升官日未载',place='南唐',note='底本潘佐后接佑字，结合《宋史》潘佑被韩熙载徐铉荐入李璟朝的文学履历，按潘佑记录；原字保持，纸本异文待核，未据本句补每人官号。')
claim('person',people['潘佑'],'description','《宋史》记潘佑善于文章论议，经陈乔、韩熙载、徐铉推荐入李璟朝，任秘书省正字、直崇文馆。',13,'及長，善屬文，尤長於論議。陳喬、韓熙載、徐鉉等共薦於景，為秘書省正字、直崇文館。','与主书文学入官场景对应，用于潘佐接佑的疑字校核，不提前录李煜时期迁任及死亡。',source=pan)
claim('person',people['潘佑'],'description','本段称佑为幽州人。',13,'佑，幽州人也。','接本段潘佐姓名疑字，按同段佑及宋史荐官履历作潘佑记录；纸本未核，字形疑问保留。')
add('jiang_wenwei_runs_first_exam','李璟命江文蔚主持南唐贡举，王克贞等三人进士及第',13,'当时唐之文雅','等三人及第。',[('唐主','命江文蔚主持贡举'),('江文蔚','以翰林学士身份主持贡举'),('王克贞','作为庐陵进士及第')],when='952年二月条下，具体开科日未载',place='南唐',note='底本韩林疑翰林字形，原引文不改；未尝设科举为对南唐此前的概述，不代表吴唐所有朝代都没有考试。')
add('jiang_claims_impartial_examination','江文蔚答李璟询问，称前朝公举私谒相半、自己全凭公正取士',13,'唐主问文蔚：','唐主悦。',[('唐主','询问本次取士与前朝相比如何，听后欣喜'),('江文蔚','称自己全凭公正取士')],when='952年南唐本次贡举之后',place='南唐朝廷',note='前朝公举私谒相半是江文蔚自评与批评，不量化为已证实五成舞弊；聊取士疑卿字，原引文保留。')
add('tang_abandons_examinations','张纬不满江文蔚说法，执政者共同阻挠，南唐停办贡举',13,'中书舍人张纬，',None,[('张纬','以前朝进士、中书舍人身份不满江文蔚说法')],when='952年本次贡举之后，具体停止日未载',place='南唐',note='张纬沿940年受李金全派向南唐递降表的既有主体，后来南唐文官职变不另建人。执政未逐一具名，不推每名宰相都亲自反对。')
add('zheng_renhui_shumi_deputy','郭威任郑仁诲为枢密副使',14,'三月，戊辰，',None,[('帝','任郑仁诲为枢密副使'),('郑仁诲','由内客省使、恩州团练使获任枢密副使')],when='952年三月戊辰',place='后周朝廷')
sup('zheng_renhui_shumi_deputy',14,mar,'以內客省使、恩州團練使鄭仁誨為樞密副使。','《旧五代史》同日也记郑仁诲任枢密副使。','仁诲仁誨为繁简对应，原文官职与主体一致。')
sup('zheng_renhui_shumi_deputy',14,nw,'戊辰，內客省使鄭仁誨為樞密副使，翟光鄴罷。','《新五代史》同日记郑仁诲任副使，并补翟光邺罢职。','只补同日交替背景，不提前录五月亲征任职。',relation='adds')
E['zhai_removed']=event('zhai_removed','翟光邺罢枢密副使',14,'戊辰，內客省使鄭仁誨為樞密副使，翟光鄴罷。',[('翟光邺','在郑仁诲任职时被罢枢密副使')],source=nw,when='952年三月戊辰',place='后周朝廷',note='源于新周本纪同日条，枢密副使此前951年任职已录，未补无载罢免理由。')
add('weisheng_renamed_wusheng','后周把威胜军更名为武胜军',15,'甲戌，',None,[],when='952年三月甲戌',place='威胜军、武胜军',note='军镇更名，不另建一支同名新军队；主书此句未提供军镇治所，不补未经核实的现代位置。')
add('feng_xu_sun_chancellors','李璟任冯延巳、徐景运、孙晟为宰相',16,'唐主以太弟太保、','皆同平章事。',[('唐主','任命三人同平章事'),('冯延己','由太弟太保、昭义节度使任左仆射、同平章事'),('徐景运','由前镇海节度使任中书侍郎、同平章事'),('孙晟','以右仆射身份兼同平章事')],when='952年三月条下，具体宣制日未载',place='南唐朝廷',note='并相同平章事是一组任命，官衔各有不同，不把孙晟再造为孙忌另一人。')
add('chang_mengxi_criticizes_appointment','常梦锡在任命宣读后公开称白麻不如江文蔚奏疏',16,'既宣制，','但不及江文蔚疏耳！”',[('常梦锡','以户部尚书身份公开批评宰相任命')],when='952年三月宰相任命宣读后',place='南唐朝廷',note='他的比较是讥讽任命，不把白麻误认为一件普通纺织品。')
add('sun_sheng_disparages_feng','孙晟以金杯玉碗盛污物之喻讥讽冯延巳',16,'晟素轻延己，','乃贮狗矢乎！”',[('孙晟','轻视冯延巳，用比喻讥讽其任相'),('冯延己','成为孙晟讥讽的对象')],when='952年三月任相前后的概述，具体说话日未载',place='南唐',note='狗矢为人物比喻，展示说明解释其意，不当成真实盛物行为。')
add('feng_requests_governing_authority','冯延巳称君主事事亲为限制宰相才干，要求李璟放手政务',16,'延己言于唐主曰：','此治道所以未成也。”',[('冯延己','提出宰相才干受君主亲自处理政务所限'),('唐主','听取放手政务的建议')],when='952年三月任相以后',place='南唐朝廷',note='治道未成的原因是冯延巳自己的说法，不当唯一客观因果。')
add('li_jing_delegates_to_feng','李璟把政务交给冯延巳，主要只批可',16,'唐主乃悉以政事委之，','奏可而已。',[('唐主','把政务交给冯延巳'),('冯延己','获委掌政务')],when='952年任相后，具体开始日未载',place='南唐朝廷')
add('feng_relies_on_subordinates','史书记载冯延巳不勤于政务，文书依赖胥吏、军事交给边将',16,'既而延己不能勤事，','军旅则委之边将。',[('冯延己','被史书记载为依赖胥吏处理文书、委边将处理军事')],year=None,when='952年获委政务以后的一段时期，具体起止年月未载',place='南唐',note='史家评价与处理分工不扩大为所有胥吏都腐败或每次军事失利都由此造成。')
add('li_jing_resumes_affairs','政务渐乱后，李璟重新亲自处理',16,'顷之，',None,[('唐主','在政务更加混乱后重新亲自处理')],year=None,when='委政冯延巳后一段时间，具体年月未载',place='南唐朝廷',note='顷之没有准确时长，不自定为三月同日收回或某个完整月。')
reviews={9:'反叛前劝谏与被围征财分开，藏财都是慕容彦超怀疑。妻妾乳母无名不补身份。新书补家僮搜财郑麟持刃，并对下狱对象有异说；父阎宝方向明确，阎夫妻与崔死于952，被围内具体日不明。',10:'府州战与庚子攻岢岚奏报分开；旧书庚寅为战胜奏，人数概数与防卸字形保留，不套确切战日。',11:'主二月甲辰与旧正月戊寅释放纪日异说保留。郭威话语、李璟礼还中原人和韩熙载劝止分别录；不提前旧书路昌祚后续全事。',12:'海上交往为李昪以来长期概述，兄弟外交不建血缘；契丹图财不出力为史家评价。',13:'文学任官为长期概述。潘佐接佑结合宋潘传同场文学荐官校为潘佑，保原字待纸本核。初贡举王克贞三人、江自称至公、张及执政阻贡举分录；韩林聊取士疑字保留。张纬沿940向南唐递降表主体，不以职变重建。',14:'戊辰任郑仁诲旧新本纪印证，新书补翟罢。籍晋阳，不补生日；不提前五月亲征职务。',15:'甲戌威胜改武胜为军镇名变化，不虚构改隶治所或新军。',16:'三宰任职、常批白麻、孙比喻、冯求委政、李委政、下属分工与李复亲理分开。长期顷之不强系三月日，人物观点和史家评价不当已证事实或因果。'}
assert not (P/'publication.json').exists()
for n in range(9,17):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=290,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷290原98—105行连续八段；952年跨卷290、291，后续仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],source_issues_review='逐字摘录保留底本，纸本未核。崔阎拘押对象、燕释放纪日分别保留；潘佐接佑经宋同场履历作姓名校核，韩林聊取士疑字不改原文。文臣任职与长期评价追述不强定日，旧书引文附注不算独立原书确证。',plain_language_review='首次检查所有展示字段和事实说明，主语动作关系清楚，引用外用白话；怀疑与证实、比喻与实际行为、意见与史家评价、委政与后续收回分清。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
