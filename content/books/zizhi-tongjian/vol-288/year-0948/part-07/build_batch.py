# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 43–50."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,70))
COMMIT='cfc4e70dd5b944e6aa97489ccdc694e25f795d09'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-948-august-september','jiuwudaishi-101-august-948','xinwudaishi-011-guo-rewards','xinwudaishi-064-zhang-ye-fall']:
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
main_sources = ['tongjian-288-948-august-september','tongjian-288-948-september-october']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p043-p050',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(43, 51):
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
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐元年（948年八月至九月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_07_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=948, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='948年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0948_' + code
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
        edge = 'participation_zztj_288_0948_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0948_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'南汉主':'刘弘熙','刘晟':'刘弘熙','蜀主':'孟昶','楚王':'马希广','希广':'马希广','希萼':'马希萼','仁矩':'侯仁矩','延广':'侯延广','欧弘练':'欧弘练（楚天策府内都押牙）'})
nurse='刘氏（侯延广乳母）';child='刘氏的孩子（侯延广乳母所生）'
NEW_ALIASES={'钟允章':['鍾允章'],'欧弘练（楚天策府内都押牙）':['歐弘練（楚天策府內都押牙）'],'张仲荀':['張仲荀'],'侯仁矩':[],'侯延广':['侯延廣'],nurse:['劉氏（侯延廣乳母）'],child:[],'王守筠':[]}
NEW_DESCRIPTIONS={
 '钟允章':'南汉知制诰。948年奉刘晟之命到楚国求婚，马希广拒绝；返回后向刘晟说明马氏兄弟正在相争。《新五代史》还记他的工部郎中职务。婚姻双方未具名，生卒年未据本次原文确定。',
 '欧弘练（楚天策府内都押牙）':'948年任楚国天策府内都押牙，与进奏官张仲荀建议马希广向后汉执政者送重礼，阻止马希萼单独朝贡求官。与943年所见客将区弘练存在姓字差异，是否同人，尚待校核；生卒年未载。',
 '张仲荀':'楚国进奏官。948年与天策府内都押牙欧弘练共同出谋，马希广据其建议向后汉执政者送重礼，使朝廷拒绝马希萼单独朝贡求官的请求。生卒年未据本段确定。',
 '侯仁矩':'侯益之子，曾任天平行军司马。王景崇杀侯益家属时，他先前已在外，因此幸免；948年九月庚申任隰州刺史。其子侯延广当时还在襁褓中，由乳母刘氏救出。生卒年未据本段确定。',
 '侯延广':'侯仁矩之子、侯益之孙。948年侯益家属遭王景崇杀害时尚在襁褓，乳母刘氏用自己的孩子替换他，抱他逃走，一路乞食到大梁，送回侯益家。具体出生年未据年龄反推，生卒年尚未录入。',
 nurse:'侯延广的乳母，只有刘姓而未记名字。侯益家属遭王景崇杀害时，她用自己的孩子替换侯延广，抱侯延广逃到大梁送回侯益家。《宋史》补记她的孩子代侯延广遇害。生卒年未载。',
 child:'侯延广乳母刘氏所生的孩子，姓名、年龄及性别未明确记载。刘氏在侯益家属遭杀时，用这个孩子替换侯延广；《宋史》明确记载其代侯延广遇害。',
 '王守筠':'侯益部下。948年九月戊申从凤翔逃来，报告侯益家属被王景崇杀害，《旧五代史》本纪记载这次报告。生卒年未载。'}
aug='jiuwudaishi-101-august-948';sep='jiuwudaishi-101-september-948';reward='xinwudaishi-011-guo-rewards';south='xinwudaishi-065-zhong-chu-marriage';chu='xinwudaishi-066-ma-separate-tribute';box='xinwudaishi-064-zhang-ye-fall';rescue='songshi-254-hou-yanguang-nurse';a='948年八月，具体日未载';s='948年九月，具体日未载'
add('li_shouzhen_expects_welcome','李守贞指望旧部因往日恩惠而迎接他',43,'始，','可坐而待之。',[('李守贞','以禁军旧部曾受恩为由，期待他们主动迎接')],year=None,when='郭威军抵河中前的追述，形成这一判断的具体年月未载',place='河中',description='李守贞认为禁军曾在自己麾下、受过恩惠，又不满后汉严法，因此指望他们到来时开城奉迎，自己可以坐等。',note='这是史书记载的李守贞判断，不当成士卒已经作出迎接承诺或城已打开。')
add('soldiers_respond_guo_rewards','士卒接受郭威赏赐，不再顾念李守贞的旧恩',43,'既而士卒','皆忘守贞旧恩。',[('郭威','向士卒给赏赐，赢得支持'),('李守贞','对旧部的影响被史书记为减弱')],when='948年八月抵河中城下前后，具体日未载',place='郭威军中',note='这是史书对士卒态度的概括，不推断所有人内心或新增具体叛降名单。')
add('guo_army_arrives_hezhong','郭威军抵达河中城下，鼓噪示威，李守贞失色',43,'己亥，',None,[('郭威','率军抵达河中城下'),('李守贞','见城下军队鼓噪而失色')],when='948年八月己亥；《旧五代史》奏报说二十三日抵城，日期差异保留',place='河中城下',note='到城下承前郭威所督军队，失色是史书描述；并未攻克河中。')
sup('guo_army_arrives_hezhong',43,aug,'癸卯，郭威奏，今月二十三日，大軍已抵河府賊城；','《旧五代史》记八月癸卯郭威奏报，大军在本月二十三日已抵河中城。','奏报日与抵城日分开；主书记己亥，独立日期表述并列保留，不以奏报日代替抵城日。',relation='conflicts',field='time_original')
add('bai_captures_west_gate','白文珂攻克河中西关城',44,'白文珂克','克西关城，',[('白文珂','攻克西关城')],when='948年八月抵城以后，具体日未载',place='河中西关城',note='西关城与河中主城分开，不写成已经全部平定李守贞。')
add('hezhong_camps_positions','白文珂、常思和郭威在河中周围设营',44,'白文珂克西关城，','威栅于城西。',[('白文珂','在河西设营'),('常思','在城南设营'),('郭威','按《资治通鉴》在城西设营')],when='948年八月抵城以后，具体日未载',place='河中周边、河西、城南、城西',note='第一栅的主语承接白文珂；主书郭威城西与新史城东不同，各书方位并列保留，未给现代坐标。')
sup('hezhong_camps_positions',44,reward,'威至河中，自柵其城東，思柵其南，文珂柵其西，','《新五代史》记郭威在城东、常思在城南、白文珂在城西设营。','郭威营地方向与主书城西不同；白文珂河西与城西的参照对象也不同，保留原记载，不强行绘成唯一方位。',relation='conflicts',field='location_name')
add('guo_sends_chang_si_home','郭威认为常思缺乏领军才能，将他遣回本镇',44,'未几，','先遣归镇。',[('郭威','因认为常思缺领军才能，将他遣归'),('常思','被先行遣回本镇')],when='948年八月设营后不久，具体日未载',place='河中至常思本镇',note='无将领才是郭威判断，不直接当本站人物评价；未几不换算具体天数。')
add('guo_rejects_immediate_assault','郭威反对立即强攻河中，提出先围困再进攻招降',44,'诸将欲急攻城，','不足虑也。”',[('郭威','否定急攻，主张围困断路、等兵粮耗尽后再攻招降'),('李守贞','成为围困策略的目标'),('赵思绾','按郭威方案先以分兵牵制'),('王景崇','按郭威方案先以分兵牵制')],when=a,place='河中军前',description='诸将想急攻河中，郭威认为李守贞善战、城防坚固，强攻会使士卒冒险，建议先围困断路，等城内粮食和财物耗尽，再用攻城器具和檄书逼降，另以分兵牵制长安、凤翔。',note='这是策略，不把预期的粮尽、父子不相保或三镇投降写成此时已发生。')
add('guo_builds_siege_works','郭威征发两万多民夫，修长壕和连城围困河中',44,'乃发诸州','列队伍而围之。',[('郭威','征发民夫修筑包围设施'),('白文珂','率领民夫开长壕、筑连城')],when=a,place='河中周边',note='民夫二万馀是原文数量，不改为准确20000；诸州未具名，不虚构征发名册。')
sup('guo_builds_siege_works',44,reward,'調五縣丁二萬人築連壘以護三柵。','《新五代史》也记征发两万丁民修连垒，写为五县，保护三处营寨。','主书诸州二万馀与新书五县二万分别保留，不将两数加总成四万人。',relation='adds')
add('guo_explains_quiet_pressure','郭威认为李守贞轻视太原将领，主张以静制敌',44,'威又谓','正宜静以制之。”',[('郭威','向诸将解释李守贞起兵原因，并主张静守制敌'),('李守贞','被郭威认为轻视新兴太原将领')],when=a,place='河中军前',note='曏畏高祖指刘知远；所述轻视及起兵原因是郭威判断，不当已证心理或另记刘知远此时在世。')
add('guo_sets_river_watch','郭威沿河设置火铺，轮换步卒守卫',44,'乃偃旗卧鼓，','番步卒以守之。',[('郭威','收起旗鼓，沿河设火铺并安排步卒轮守')],when=a,place='河中附近沿河数十里',note='偃旗卧鼓不是全军撤退；火铺是沿河守备设施，不自动解释为烧毁城池，长度只保留数十里。')
add('guo_navy_blocks_messengers','郭威部署水军沿岸停船，捕获秘密往来者',44,'遣水军',None,[('郭威','派水军停舟沿岸，封锁秘密往来')],when=a,place='河中附近河岸',note='史书如坐网中是围困形势的比喻，不写李守贞已被捕；秘密往来者未具名，不全部推为平民或谍员。')
add('wang_chuhui_retires','王处回请求退休，以太子太傅致仕',45,'蜀武德',None,[('王处回','以武德节度使兼中书令身份请老，获太子太傅致仕'),('孟昶','准许王处回致仕')],when='948年八月辛丑准许，提出请求日未载',place='后蜀朝廷',note='本次正式致仕与此前七月辞枢密职改任武德节度使分开，避免把外任和退休合为同一日。')
add('liu_sends_zhong_marriage','刘晟派钟允章向楚国求婚，马希广拒绝',46,'南汉主遣','楚王希广不许。',[('刘晟','派知制诰钟允章求婚'),('钟允章','奉南汉皇帝之命出使楚国求婚'),('马希广','拒绝婚姻请求')],when='948年八月条所载，具体日未载',place='南汉至楚国',note='刘晟沿已有刘弘熙主体，943年更名事实已发布；求婚男女未具名，不建立无证婚姻关系。')
sup('liu_sends_zhong_marriage',46,south,'六年，遣工部郎中、知制誥鍾允章聘楚以求婚，楚不許。','《新五代史》乾和六年也记钟允章奉命到楚求婚遭拒，补充其工部郎中职务。','乾和六年对应948年，原文没有给出八月或具体日，不把拒婚写成离婚。',relation='adds')
add('liu_zhong_discuss_chu_weakness','刘晟与钟允章议论楚国争斗，认为有机可乘',46,'南汉主怒。',None,[('刘晟','拒婚后发怒，并认为马希广懦弱吝啬、楚军久不作战，可乘机进取'),('钟允章','回答马氏兄弟正在内争，无力威胁南汉'),('马希广','成为刘晟负面评价和战略判断的对象')],when='948年八月条所载，拒婚以后，具体日未载',place='南汉朝廷',note='懦而吝啬、士卒忘战是刘晟判断，未作本站定评；此段没有实际出兵命令，不提前录后续攻楚。')
sup('liu_zhong_discuss_chu_weakness',46,south,'允章還，晟曰：「馬公復能經略南土乎？」是時，馬希廣新立，希萼起兵武陵，湖南大亂，允章具言楚可攻之狀。','《新五代史》也记钟允章返回后，向刘晟说明楚国可攻的形势。','该书后接实际攻贺桂诸州，但本批只补同次议论，不提前录后续战争，也不据传记合叙消除各段时间差。')
add('ma_xie_separate_tribute_request','马希萼请求独立朝贡，并求朝廷另授官爵',47,'武平节度使','求朝廷别加官爵，',[('马希萼','以武平节度使身份请求与马希广分别朝贡并另求官爵'),('马希广','成为请求分别朝贡所涉及的另一楚王')],when='948年九月壬子诏书以前，请求具体日未载',place='武平军至后汉朝廷',note='请求独立朝贡不等于已获独立楚王册封或此时已另建国家。')
sup('ma_xie_separate_tribute_request',47,chu,'希萼憤然而去，乃遣使詣京師求封爵，請置邸稱藩。漢隱帝不許，降璽書慰勞講解之。','《新五代史》也记马希萼遣使求封爵、设邸称藩，被刘承祐拒绝，并收到慰劳调解诏书。','传记把求封爵接在奔丧、返回武陵之后，未列948年九月壬子；作为同一往来补证，不新增一次确切日期的请求。',relation='adds')
add('ma_xiguang_bribes_to_block','马希广采纳欧弘练、张仲荀建议，贿赂后汉执政者阻止请求',47,'希广用','使拒其请。',[('马希广','采纳建议，向后汉执政者厚贿阻止马希萼请求'),('欧弘练','以天策府内都押牙身份出谋'),('张仲荀','以进奏官身份出谋'),('马希萼','独立朝贡求官请求遭阻止')],when='948年九月壬子诏书以前，具体日未载',place='楚国、后汉朝廷',note='执政者未具名，不无证列杨邠等具体收贿者；欧与943年区弘练的姓字差异尚未校定同人，暂以本职限定主体。')
add('han_edict_ma_tribute_via_xiguang','后汉诏令马氏兄弟和睦，马希萼朝贡须经马希广',47,'九月，','当附希广以闻。”',[('刘承祐','向马氏兄弟发诏调解并规定朝贡路径'),('马希萼','被要求经马希广向后汉朝贡'),('马希广','成为马希萼朝贡须经由的楚王')],when='948年九月壬子',place='后汉朝廷至楚国、武平军',note='诏令内容不等于兄弟已和好；朝贡路径不是新增父子血亲或自动军事上下级关系。')
add('ma_xie_refuses_edict','马希萼不接受后汉调解与朝贡安排',47,'希萼不从。',None,[('马希萼','不服从该诏令安排')],when='948年九月壬子诏书以后，具体回应日未载',place='武平军',note='只记录不从该安排，未扩成拒绝以后所有诏令。')
add('shu_relief_army_sanguan','后蜀军援助王景崇，驻扎散关',48,'蜀兵援','军于散关，',[('王景崇','获得后蜀军援助')],when=s,place='散关',note='军于指驻军，不补援军主将姓名或出兵人数。')
add('li_yancong_defeats_shu_relief','赵晖派李彦从突袭散关蜀军，蜀军败退',48,'赵晖遣',None,[('赵晖','派都监李彦从袭击蜀军'),('李彦从','率军袭击并击败蜀军')],when=s,place='散关',note='本句只明确李彦从为都监、执行袭击，不并入旧史另场法门寺袭王景崇之战；无证不添加三千或二千死伤。')
sup('li_yancong_defeats_shu_relief',48,sep,'戊辰，鳳翔都部署趙暉奏，大破川軍於大散關，殺三千餘人，其餘棄甲而遁。','《旧五代史》九月戊辰条记赵晖奏报在大散关击败川军，杀三千多人，其余弃甲退去。','地点和蜀军相合，作为相关战报补证；戊辰为奏报日，不直接当实际袭击日，该句没有写李彦从。',relation='adds')
add('meng_opens_petition_box','孟昶因政事被壅蔽，设置匦函接纳意见',49,'蜀主以','始置匦函，',[('孟昶','因张业、王处回执政时政事被遮蔽，设置匦函'),('张业','其执政被列为政事壅蔽背景'),('王处回','其执政被列为政事壅蔽背景')],when='948年九月己未',place='后蜀朝廷',note='以张业王处回执政为此前背景，不写成张业此时仍在世任相；匦函作为受理意见之箱，未造具体上书人。')
sup('meng_opens_petition_box',49,box,'昶始親政事，於朝堂置匭以通下情。','《新五代史》同记孟昶亲政后在朝堂设匦以了解下情。','传记无九月己未干支，只补设置位置和用途；不把该书所有亲政举措一并强定同一天。',relation='adds')
add('shu_petition_box_renamed','后蜀将匦函改称献纳函',49,'后改为',None,[],year=None,when='948年九月己未设置之后，改名具体年月未载',place='后蜀',note='后改没有具体日期，不把改名同样强定己未。')
add('wang_kills_hou_family','王景崇杀害侯益家属七十多人',50,'王景崇尽杀','七十馀人，',[('王景崇','杀害侯益家属'),('侯益','家属遭王景崇杀害')],when='948年九月条追述，实际发生日未载',place='凤翔',note='人数七十馀保留为约数；尽杀是主书概述，与仁矩和延广逃免应一起读，不写成侯益所有亲人无一存活。')
E['hou_family_murder_report']=event('hou_family_murder_report','王守筠从凤翔逃来，报告侯益家属遭杀',50,'九月戊申，侯益部曲王守筠自鳳翔來奔，言益家屬盡為王景崇所害。',[('王守筠','从凤翔逃来，报告杀害家属的消息'),('侯益','其部下报告家属被害'),('王景崇','被报告为杀害家属者')],when='948年九月戊申来奔奏报',place='凤翔至后汉朝廷',source=sep,note='另立消息到达事件；报告日期与杀害发生日期分开，不凭来奔确定王守筠原籍。')
sup('wang_kills_hou_family',50,sep,'言益家屬盡為王景崇所害。','《旧五代史》同记王守筠报告侯益家属被王景崇杀害。','该书这句没有人数，戊申是报告到达日，不据此确认杀人实际发生日。')
add('hou_renju_escapes_family_murder','侯仁矩因先已在外，逃过家属遭杀之难',50,'益子前天平','得免。',[('侯仁矩','原任天平行军司马，先已在外而幸免')],when='948年家属遭杀时，具体日未载',place='侯仁矩所在外地未载',note='在外地点未具名，不补在大梁或隰州；本事件免难与稍后官职分开。')
relationship('侯益','侯仁矩','父亲',50,'益子前天平行军司马仁矩先在外，得免。','益承接侯益；侯益是侯仁矩的父亲，不与后唐李仁矩混同。')
add('hou_renju_xizhou_governor','侯仁矩任隰州刺史',50,'庚申，','隰州刺史。',[('侯仁矩','任隰州刺史'),('刘承祐','任命侯仁矩为隰州刺史')],when='948年九月庚申',place='隰州',note='沿前句益子仁矩识别，未补现代坐标或在任期限。')
add('liu_nurse_rescues_hou_yanguang','乳母刘氏用自己的孩子替换侯延广，抱他逃走',50,'仁矩子延广，','抱延广而逃，',[('侯延广','尚在襁褓，被乳母用其孩子替换并救出'),(nurse,'用自己孩子替换侯延广，抱侯延广逃走'),(child,'被母亲用来替换侯延广')],when='948年侯益家属遭杀时，具体日未载',place='凤翔',note='没有补孩子姓名、性别或准确年龄，也不把替换过程写成自愿献身的心理判断。')
relationship('侯仁矩','侯延广','父亲',50,'仁矩子延广，尚在襁褓，','仁矩沿侯仁矩，侯仁矩是侯延广的父亲；尚在襁褓不反推准确出生年。')
relationship(nurse,'侯延广','乳母',50,'乳母刘氏以己子易之，抱延广而逃，','刘氏是侯延广的乳母，不是有证血亲母亲；A是B的乳母方向明确。')
relationship(nurse,child,'母亲',50,'乳母刘氏以己子易之，','己子指刘氏自己的孩子，母子血亲按明示记载；性别未明确，展示称孩子，不造儿子身份。')
E['nurse_child_dies_in_place']=event('nurse_child_dies_in_place','乳母刘氏的孩子代侯延广遇害',50,'乳母劉氏以己子代延廣死。',[(nurse,'用自己的孩子代替侯延广'),(child,'代侯延广遇害'),('侯延广','因乳母替换而免于死亡')],when='948年侯益家属遭杀时，具体日未载',place='凤翔',source=rescue,note='《宋史》明确说代延广死，主书仅说易之；按补证另记孩子死亡，不增具体杀人方式。')
add('liu_nurse_returns_hou_home','刘氏抱侯延广一路乞食，到大梁送回侯益家',50,'乞食至于',None,[(nurse,'抱侯延广一路乞食，到大梁送还'),('侯延广','被送回侯益家'),('侯益','接回孙子')],when='948年逃离凤翔之后，抵达大梁具体日未载',place='凤翔至大梁',note='乞食是沿途维生方式，没有给出行程时长、路线或侯益是否亲自接见。')
sup('liu_nurse_returns_hou_home',50,rescue,'劉氏行丐抱持延廣至京師還益。','《宋史》同记刘氏抱着侯延广行乞到京师，送还侯益。','京师在本事对应大梁；该段后接延广成年事迹，不强定都发生在948年。')
reviews={43:'李守贞期待旧部迎接为判断，郭威赏赐影响与己亥军抵城分录；旧史八月二十三抵城奏报另存，不用癸卯奏报日代替抵城日。',44:'西关城攻克不当河中全城已陷；三营部署、遣常归镇、围困策略、民夫修壕、静制判断、沿河火铺步卒和水军封锁分录。郭营城西与新史城东、民夫二万馀与五县二万差异保留。',45:'八月辛丑正式致仕与七月辞枢密外任分开。',46:'刘晟沿刘弘熙，更名已有逐字事实；求婚双方未具名不建夫妻。钟出使和返后战争机会判断分录，不提前后续实战。',47:'马希萼独立朝贡请求、马希广贿赂阻止、九月壬子诏令和不从分录。欧弘练与区弘练姓字差异未证同人，以本职限定待校；不推执政受贿者姓名。',48:'散关援军驻扎与李彦从袭击分录，旧史戊辰战报是相关补证，非把本次具体战日定戊辰；不混法门寺西二千战。',49:'己未始置匦函与后改名分录；张业王处回壅蔽为此前背景，改名年月未知。',50:'家属七十馀杀害与戊申消息到达分录；仁矩在外免难与庚申隰州任官分开。延广襁褓不反推生年，刘氏替换救人、宋明确孩子死亡、乞食归侯家分别录，父亲和乳母母亲关系方向核对。'}
assert not (P/'publication.json').exists()
for n in range(43,51):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(43,51)],next_paragraph=Q[51]['id'],next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷288原49—56行连续八段，本卷50/69；卷287已19段，全年69/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(43,51)],source_issues_review='郭威到河中日期、营地方位、民夫数各书差异分别保留。欧/区弘练待同人校核，按本职限定，不强合。侯益家属尽杀与两个免难者并读，旧史消息到达日不当实际被害日，宋明确乳母孩子代死单列。',plain_language_review='首次逐条核对人物、事件、时间、参与角色、关系方向和事实说明，明确主语；将判断、策略、诏令、实际行动和奏报区分。引用保持原字，未知年月为null，不造婚配人选、婴儿姓名性别或出生年。新数据完成首次自查，不追加固定的发布后二次全文重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
