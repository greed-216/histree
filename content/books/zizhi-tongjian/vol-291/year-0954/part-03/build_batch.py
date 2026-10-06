# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 954 paragraphs 21–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,39))
COMMIT='2a8781f0b81874ff142e6f29547499414becd367'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-114-campaign-march-954','xinwudaishi-12-chairong-accession']:
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
main_sources = ['tongjian-291-954-gaoping']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0954-p021-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
for n in range(21, 25):
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
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·显德元年（954年正月至三月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0954_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0954_' + code
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
        edge = 'participation_zztj_291_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'柴荣','北汉主':'刘崇（刘知远弟）','杨兗':'杨衮','史彦超':'史彦超（后周将领）','太祖皇帝':'赵匡胤','唐景思':'唐景思（后周效顺指挥）','李义':'李义（北汉司天监）'})
NEW_ALIASES={'赵匡胤':['趙匡胤'],'马仁瑀':['馬仁瑀'],'王延嗣':[],'李义（北汉司天监）':['李义','李義'],'唐景思（后周效顺指挥）':[]}
NEW_DESCRIPTIONS={'赵匡胤':'后周宿卫将领，后来成为宋太祖。954年高平之战右军溃逃后，与张永德分率两翼反击北汉军。《宋史》本纪印证其率同列冲锋的记载。生卒年留待相应史料补录。','马仁瑀':'夏津人，后周内殿直。954年高平之战中骑马射敌，鼓舞士气；《宋史》马仁瑀传也记这次行动。生卒年本段未载。','王延嗣':'北汉副枢密使。954年高平之战前让司天监李义建议开战，当晚在后周军再次击败北汉时被杀。生年未载。','李义（北汉司天监）':'北汉司天监。954年高平之战前经王延嗣向刘崇表示可以开战，王得中反对这一建议。生卒年未载；不与其他朝代同名人物合并。','唐景思（后周效顺指挥）':'后周前武胜行军司马。954年高平之战后奉命统领由数千北汉降卒组成的效顺指挥，戍守淮上。与925年前蜀故镇屯驻指挥使唐景思是否同人，缺少明确履历证据，暂作独立主体。'}
NEW_DEATH_YEARS={'王延嗣':954}
old='jiuwudaishi-114-campaign-march-954';new='xinwudaishi-12-chairong-accession';song='songshi-1-gaoping-counterattack';ma='songshi-273-ma-renyu-gaoping'
day='954年三月癸巳，高平之战当天'
add('han_camps_south_gaoping','刘崇经过潞州未攻城，南下驻军高平以南',21,'北汉主不知帝至，','军于高平之南。',[('北汉主','率军越过潞州南下驻营')],when='954年三月壬辰晚，高平交战前夕',place='潞州至高平以南',note='是夕承接前段壬辰；不知柴荣已到是史书的叙述。')
add('gaoping_vanguard_clash','后周前锋击退北汉兵，柴荣催各军加速前进',21,'癸巳，','趣诸军亟进。',[('帝','担心北汉退走，催各军前进'),('北汉主','所部前锋受挫')],when=day,place='高平以南')
sup('gaoping_vanguard_clash',21,old,'十九日，先鋒與賊軍相遇，賊陣於高平縣南之高原。','《旧五代史》记三月十九日前锋相遇，北汉在高平县南高原布阵。','保留原书记载的月日及地点，不自行换算公历。')
add('han_gaoping_deployment','刘崇居中军，张元徽居东，杨衮居西布阵',21,'北汉主以中军','众颇严整。',[('北汉主','在巴公原布中军'),('张元徽','在东侧布军'),('杨兗','在西侧布军')],when=day,place='巴公原')
add('zhou_gaoping_deployment','柴荣部署高平阵势，亲自披甲临阵督战',21,'时河阳节度使刘词','帝介马自临陈督战。',[('刘词','率后军尚未到达'),('白重赞','与李重进领左军居西'),('李重进','与白重赞领左军居西'),('樊爱能','与何徽领右军居东'),('何徽','与樊爱能领右军居东'),('向训','与史彦超率精骑居中'),('史彦超','与向训率精骑居中'),('张永德','以禁军护卫柴荣'),('帝','部署诸军并亲临战阵')],when=day,place='高平以南')
sup('zhou_gaoping_deployment',21,old,'乃令侍衛馬步軍都虞候李重進、滑州節度使白重贊將左，居陣之西廂；侍衛馬軍都指揮使樊愛能、步軍都指揮使何徽將右，居陣之東廂；宣徽使向訓、鄭州防禦使史彥超，以精騎當其中；殿前都指揮使張永德以禁兵衛蹕。帝介馬觀戰。','《旧五代史》也列后周左、中、右军及护卫禁兵的安排。','李重进与白重赞共同领左军，不据排列顺序编造正副关系。')
add('liuchong_rejects_yang_warning','刘崇认为可以独胜后周，拒绝杨衮谨慎进兵的建议',21,'北汉主见周军少，','兗默然不悦。',[('北汉主','认为无需契丹助战，拒绝缓进'),('杨兗','观察后认为周军强劲，劝勿轻进')],when=day,place='巴公原',note='关于胜负的言论是双方判断，不录为已验证的兵力优劣。')
add('li_yi_advises_attack','风转为南风后，王延嗣让李义建议刘崇开战，刘崇同意',21,'时东北风方盛，','北汉主从之。',[('王延嗣','让李义向刘崇报告可战'),('李义','判断可以开战'),('北汉主','接受开战建议')],when=day,place='高平战场',note='风向变化按史载保留，不把司天判断当作胜败的科学定论。')
add('wang_dezhong_opposes_attack','王得中反对开战建议，刘崇拒绝并威胁杀他',21,'枢密直学士王得中','且斩汝！”',[('王得中','劝刘崇不要采信李义'),('北汉主','坚持已作出的决定并威胁王得中')],when=day,place='巴公原',note='此处只记威胁，不记王得中已经被杀。')
add('zhang_attacks_zhou_right','刘崇命东军先攻，张元徽率千骑冲击后周右军',21,'麾东军先进，',None,[('北汉主','命东军先行攻击'),('张元徽','率千骑冲击后周右军')],when=day,place='高平战场东侧')
add('fan_he_flee_gaoping','樊爱能、何徽先率骑兵逃走，后周右军溃散',22,'合战未几，','右军溃。',[('樊爱能','率骑兵逃离战场'),('何徽','与樊爱能一同逃走')],when=day,place='高平战场右军')
sup('fan_he_flee_gaoping',22,old,'何徽以徒兵陣於後，為奔騎所突，即時潰亂，二將南走。','《旧五代史》补记何徽步军在后，被逃跑骑兵冲乱后，两将南逃。','两书记述的领兵细节并列保留，不把何徽的步军改成全体骑兵。',relation='adds')
add('zhou_infantry_surrenders','后周千余步兵解甲投降北汉',22,'步兵千馀人','降于北汉。',[('北汉主','接受后周步兵投降')],when=day,place='高平战场',note='此处是后周士兵降北汉，与战后北汉降卒分开。')
add('chairong_under_fire_gaoping','柴荣见战局危急，亲率卫兵冒箭石督战',22,'帝见军势危，','自引亲兵犯矢石督战。',[('帝','亲率卫兵冒箭石临阵督战')],when=day,place='高平战场')
add('zhao_zhang_two_wings','赵匡胤劝张永德分率两翼反击，两人各领二千人进战',22,'太祖皇帝时为宿卫将，','各将二千人进战。',[('太祖皇帝','鼓励同列并提出分翼反击，领右翼'),('张永德','接受建议，乘高向西领左翼进攻')],when=day,place='高平战场',note='太祖皇帝在这段指宋太祖赵匡胤，不是已故周太祖郭威；此时赵匡胤仍为后周将领。')
claim('person',people['赵匡胤'],'description','《宋史》本纪所称太祖为赵匡胤。',22,'太祖啟運立極英武睿文神德聖功至明大孝皇帝諱匡胤，姓趙氏，涿郡人也。','结合宋太祖本纪的姓名和同书高平行动，确定《通鉴》此段的身份；此时尚未建立宋朝。',source='songshi-1-zhao-kuangyin-name')
add('zhao_counterattack_gaoping','赵匡胤身先士卒，后周兵奋战击退北汉',22,'太祖皇帝身先士卒，','北汉兵披靡。',[('太祖皇帝','率先冲击北汉阵锋'),('北汉主','所部在反击中退却')],when=day,place='高平战场',note='一当百是史书对奋战的赞述，不按一人确实杀百人生成伤亡统计。')
sup('zhao_counterattack_gaoping',22,song,'將合，指揮樊愛能等先遁，軍危。太祖麾同列馳馬衝其鋒，漢兵大潰。','《宋史》宋太祖本纪也记樊爱能等逃走后，赵匡胤率同列冲锋，北汉军溃败。','本纪后续太原攻城及任职另属后续进程，这里只补高平反击。')
add('ma_renyu_rallies_gaoping','马仁瑀跃马射敌，鼓舞后周士气',22,'内殿直夏津马仁瑀','士气益振。',[('马仁瑀','鼓舞军士后骑马射敌')],when=day,place='高平战场',description='后周内殿直马仁瑀呼吁众人保护柴荣，跃马引弓射击敌军。史书称他连续射杀数十人，后周士气因而振作。',note='数十人为史载估数，不细化成精确人数。')
sup('ma_renyu_rallies_gaoping',22,ma,'仁瑀謂眾曰：「主辱臣死，安用我輩！」乃控弦躍馬，挺身出陣射賊，斃者數十人，士氣益振，大軍乘之，崇遂敗績。','《宋史》马仁瑀传也记其高平挺身射敌、鼓舞士气。','两书保存的激励言辞有别，保留原字；《旧五代史》夹注也引用此类传记，不能将转引算成独立证据。')
add('ma_quanyi_charges_gaoping','马全乂劝柴荣稳住坐骑，率数百骑冲入敌阵',22,'殿前右番行首马全乂',None,[('马全乂','劝柴荣观战，率数百骑冲阵'),('帝','受到马全乂稳住坐骑的劝告')],when=day,place='高平战场',note='贼势已尽是马全乂的战场判断，不保证已擒北汉君主。')
add('liuchong_orders_zhang_pursuit','刘崇得知柴荣亲临，奖励张元徽并催他乘胜进兵',23,'北汉主知帝自临陈，','趣使乘胜进兵。',[('北汉主','奖励并催促张元徽进攻'),('张元徽','受到奖励和继续进攻命令')],when=day,place='高平战场')
add('zhang_yuanhui_killed','张元徽进至阵前，马倒后被周兵杀死',23,'元徽前略陈，','北军由是夺气。',[('张元徽','进攻时马倒，被后周兵杀死')],when=day,place='高平战场',description='北汉将张元徽到阵前进攻时坐骑倒下，被后周士兵杀死。史书称他是北汉骁将，他的死亡使北汉军士气受挫。',note='不把马倒的原因补成受箭或落入陷阱。')
sup('zhang_yuanhui_killed',23,old,'臨陣斬賊大將張暉及偽樞密使王延嗣。','《旧五代史》在傍晚再战记北汉大将张暉与王延嗣被杀。','《通鉴》把张元徽马倒被杀放在前一阶段，《旧五代史》作张暉且同列晚战死亡；保留姓名与先后差别，尚不把张暉作为张元徽的确定别名。',relation='conflicts')
claim('person',people['张元徽'],'death_year','《资治通鉴》记张元徽于954年高平之战中被杀。',23,'元徽前略陈，马倒，为周兵所杀。','死亡年依据显德元年连续正文；既有主体死亡字段不在本批无守卫地覆盖。')
add('liuchong_fails_rally','北汉军败退，刘崇亲举红旗也未能止住溃兵',23,'时南风益盛，','不能止。',[('北汉主','举红旗试图收拢军队，未能制止溃退')],when=day,place='高平战场')
add('yang_gun_withdraws_gaoping','杨衮未援北汉，率契丹军全军退走',23,'杨兗畏周兵之强，',None,[('杨兗','未救北汉，率本部退走')],when=day,place='高平战场',note='畏惧周军与怨恨刘崇言语是史书所述动机；全军而退不外推为绝无伤亡。')
add('fan_he_loot_baggage','樊爱能、何徽率数千骑南逃并抢掠辎重，役徒惊散',24,'樊爱能、何徽引数千骑南走，','失亡甚多。',[('樊爱能','率骑南逃，所部抢掠辎重'),('何徽','一同南逃，所部抢掠辎重')],when=day,place='高平以南撤退路',note='失亡未给数目，不将运输人员的逃散与损失全写成阵亡。')
add('fugitives_ignore_messengers','柴荣派人阻止溃兵，军士拒命，有人杀死使者并散布败讯',24,'帝遣近臣及亲军校','馀众已降虏矣。”',[('帝','派近臣与亲军军官追赶劝止')],when=day,place='高平以南撤退路',note='契丹大至、官军已败是溃兵扬言，不当作实际战局；只记部分使者被杀。')
add('liuci_rejects_fan','刘词遇逃兵受阻劝，仍率后军北进',24,'刘词遇爱能等于涂，','引兵而北。',[('刘词','拒绝樊爱能等阻止，坚持北进'),('樊爱能','试图阻止刘词前进')],when='954年三月癸巳，傍晚增援前',place='高平以南进军路')
add('liuci_evening_victory','刘词傍晚到达，与诸军再败据涧北汉军，王延嗣被杀',24,'时北汉主尚有馀众万馀人，','追至高平，',[('北汉主','率万余残部据涧布阵'),('刘词','到达后与诸军攻击北汉残部'),('王延嗣','在再战中被后周军杀死')],when='954年三月癸巳傍晚',place='高平附近涧谷至高平')
sup('liuci_evening_victory',24,old,'日暮，賊萬餘人阻澗而陣，會劉詞領兵至，與大軍迫之，賊軍又潰，','《旧五代史》也记日暮刘词到达，再击据涧万余北汉军。','与白天反击区分，为同一天第二次击败；张暉死亡的差异另行登记。')
sup('liuci_evening_victory',24,new,'癸巳，及劉旻戰于高原，敗之，〈與其不屈于周，不與其稱帝，故書姓名。〉追及于高平，又敗之。','《新五代史》记癸巳高原战胜后，追至高平再次击败刘旻。','刘旻为既有刘崇主体的别名；夹注是史家书法说明，不录为战场行为。')
add('zhou_captures_gaoping_spoils','后周追击至高平，缴获北汉御用器物、大量辎重和牲畜',24,'僵尸满山谷，','杂畜不可胜纪。',[('北汉主','所部遗弃御用器物与军需')],when='954年三月癸巳晚再战后',place='高平附近山谷',note='御特字形按底本保留，结合旧史偽乘輿器服解释为君主御用物；不可胜纪不转换成精确数量。')
sup('zhou_captures_gaoping_spoils',24,old,'所獲輜重、兵器、駝馬、偽乘輿器服等不可勝紀。','《旧五代史》列缴获辎重、兵器、骆驼与马、刘崇的乘舆器服。','补充物资类别，不将御特直接当作某种现代车辆。',relation='adds')
add('chairong_executes_defectors','柴荣夜宿野外，将被重新抓获的投敌周兵处死',24,'是夕，帝宿于野次，','皆杀之。',[('帝','处死被重新抓获的投敌步兵')],when='954年三月癸巳夜',place='高平野营',note='对象是后周此前降北汉的步兵，原文不列此次抓获人数；与北汉降兵分开。')
sup('chairong_executes_defectors',24,old,'其夕，殺降軍二千餘人，我軍之降敵者亦皆就戮。','《旧五代史》另记当夜杀降军二千余人，并处死后周投敌者。','前项降军与后项我军投敌者在该句中分列，《通鉴》此处只记后者；保留额外杀降记载及对象差异，不合并成同一批或推定全部降兵都被杀。',relation='adds')
add('fugitives_return_after_victory','樊爱能等闻后周获胜后陆续返回，有人到天明仍未归',24,'樊爱能等闻周兵大捷，','有达曙不至者。',[('樊爱能','得知获胜后与军士逐渐返回')],when='954年三月癸巳夜至甲午早',place='高平附近',note='未按所有人都已返回处理，后续问罪另见下一段。')
add('chairong_rests_gaoping','柴荣在高平休整军队',24,'甲午，','休兵于高平，',[('帝','在高平休兵')],when='954年三月甲午',place='高平')
add('tang_leads_surrendered_han','柴荣选数千北汉降卒编为效顺指挥，命唐景思率领戍守淮上',24,'选北汉降卒数千人','使戍淮上，',[('帝','选编北汉降卒并安排戍守淮上'),('唐景思','奉命统领效顺指挥')],when='954年三月甲午',place='高平至淮上',note='唐景思仅按前武胜行军司马与本次效顺军职识别；925年前蜀同名人的同人关系待证，不直接复用。')
add('release_han_prisoners','柴荣给其余二千余北汉降卒资装，让他们离去',24,'馀二千馀人','赐资装纵遣之。',[('帝','给其余降卒资装并放行')],when='954年三月甲午',place='高平')
sup('release_han_prisoners',24,old,'詔賜河東降軍二千餘人各絹二匹，並給其衣裝，鄉兵各給絹一匹，放還本部。','《旧五代史》补记二千余河东降兵每人获绢二匹及衣装，乡兵每人绢一匹，放还本部。','释放对象与前夜处死记录分开；两书记载不可压成全部降军同样处置。',relation='adds')
add('ligu_hides_after_rout','李谷被乱兵逼迫，藏入山谷，数日后才出来',24,'李谷为乱兵所迫，','数日乃出。',[('李谷','受乱兵逼迫后在山谷躲藏数日')],when='954年三月高平战事期间及随后数日',place='高平附近山谷',note='未把数日之后的行动固定在癸巳当天，也不据此推定他已被俘。')
add('chairong_arrives_luzhou_after_gaoping','柴荣战后到达潞州',24,'丁酉，',None,[('帝','获胜后到潞州')],when='954年三月丁酉，《资治通鉴》纪日',place='潞州')
sup('chairong_arrives_luzhou_after_gaoping',24,new,'丁酉，幸潞州。','《新五代史》也将柴荣至潞州记在三月丁酉。','新史与主书纪日相同，旧史另记戊戌，分别保留。')
sup('chairong_arrives_luzhou_after_gaoping',24,old,'戊戌，車駕至潞州。','《旧五代史》把柴荣到潞州记在三月戊戌。','与《资治通鉴》《新五代史》的丁酉相差一天，未擅自统一。',relation='conflicts',field='time_original')
reviews={21:'逐项整理双方阵势和战前争议。杨兗复用杨衮，刘崇复用北汉主体。王得中受死亡威胁不等于被杀，风向及司天意见不当作胜败定论。',22:'宋太祖本纪姓名与高平行动印证赵匡胤身份，此时只是周将。分翼领兵、马仁瑀与马全乂行动各自列明，一当百不转成伤亡数字。何徽步军受奔骑冲乱的旧史细节另存。',23:'张元徽马倒被杀与旧史张暉在晚战被杀的姓名及次序差别并列，未建立确定别名。杨衮全军退不等于无伤亡，刘崇举旗未能收兵。',24:'白昼与傍晚两次胜利、溃兵行动、周投敌兵及北汉降卒分别记录。旧史另记杀降军二千余人，保留对象差别；释放资装数量按旧史补充。唐景思同名未证，另建限定主体。到潞州丁酉与戊戌并列。'}
assert not (P/'publication.json').exists()
for n in range(21,25):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(21,25)],next_paragraph=Q[25]['id'],next_volume=291,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷291原101—104行连续四段高平之战正文；954年跨两卷尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,25)],source_issues_review='张元徽与张暉、降兵处置对象及到潞州日期的异说独立保留。唐景思与925年同名人的身份关系待核。纸本及异文尚待校核。',plain_language_review='首次逐条检查标题、人物介绍、事件说明、参与角色、事实与校核说明；计划、评价、威胁及实际结果分开。新增关系不由共同作战推断，原文保留字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
