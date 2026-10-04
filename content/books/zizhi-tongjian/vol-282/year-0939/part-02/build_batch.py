# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 939 paragraphs 9–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,42))
specs=[(d.name,d,'00e77c12d50b6f8ea7c868872b15b90ddf01b8db','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-939-opening','jiuwudaishi-078-march']:
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
main_sources = ['tongjian-282-939-opening','tongjian-282-939-spring-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0939-p009-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-078-april':'卷78·晋高祖纪·天福四年四月','jiuwudaishi-078-may':'卷78·晋高祖纪·天福四年五月','xinwudaishi-068-min-superstition':'卷68·闽世家'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(9, 21):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-078-april':'卷78·晋高祖纪·天福四年四月','jiuwudaishi-078-may':'卷78·晋高祖纪·天福四年五月','xinwudaishi-068-min-superstition':'卷68·闽世家'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '三月条下' if n<=10 else '四月条下' if n<=14 else '夏季后续，主书未重列月份' if n<=19 else '六月条下'
        citation = f'卷282·后晋天福四年（939；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0939_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'王彦忠（怀远城戍将）':'939年据怀远城叛乱，接受后晋供奉官齐延祚招谕后投降，却被齐延祚擅自杀死。《旧五代史》记其为灵州戍将；《资治通鉴》电子本此处作寻州。生年未载。',
'齐延祚':'后晋供奉官。939年奉命招谕怀远城叛将王彦忠，招降后擅自将他杀死，被石敬瑭除名、杖打并流放。生卒年未载。',
'仁美（回鹘奉化可汗）':'回鹘可汗。939年三月被后晋册为奉化可汗。个人姓氏及生卒年本次未核。',
'颜衎':'后晋枢密直学士、工部郎中。939年废枢密院后，解除院内职务，保留本官。生卒年未载。',
'王延武':'曾任建州刺史。《资治通鉴》称他为王继鹏的叔父，《新五代史》记他为王审知之子。939年王继鹏听信林兴的谎言，命人将他杀死。生年未载。',
'王延望':'闽国户部尚书。《资治通鉴》称他为王继鹏的叔父，《新五代史》记他为王审知之子。939年王继鹏听信林兴的谎言，命人将他杀死。生年未载。',
'林兴（闽国巫者）':'闽国巫者，受王继鹏信任，假托宝皇之命参与政事。939年诬指王延武、王延望谋变，并奉命将二人及其五名子女杀死；同年因骗局败露被流放泉州。《新五代史》另记他后来被杀，具体时间未载。',
'王继镛':'王继鹏的弟弟。939年六月，王继严被解除兵权后，王继镛受命判六军，职名不再包含诸卫二字。生卒年未载。'}
NEW_ALIASES={'王彦忠（怀远城戍将）':['王彦忠','王彥忠'],'齐延祚':['齊延祚'],'仁美（回鹘奉化可汗）':['仁美（回鹘可汗）','奉化可汗'],'颜衎':['顏衎'],'王延武':[],'王延望':[],'林兴（闽国巫者）':['林兴','林興'],'王继镛':['王繼鏞']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=939 if name in ['王彦忠（怀远城戍将）','王延武','王延望'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=939, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='939年'+('三月' if n<=10 else '四月后续条下' if n<=14 else '夏季，六月条之前' if n<=19 else '六月')+'，具体日期未载'
    key = 'event_zztj_282_0939_' + code
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
        edge = 'participation_zztj_282_0939_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'与{a}存在原文明示的亲属关系',quote,source=source)
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
        row=dict(key=f'relationship_zztj_282_0939_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})




ALIASES.update({'唐主':'李昪','闽主':'王继鹏','楚王希范':'马希范','王彦忠':'王彦忠（怀远城戍将）','仁美':'仁美（回鹘奉化可汗）','林兴':'林兴（闽国巫者）','延武':'王延武','延望':'王延望','景遂':'徐景遂','景达':'徐景达','齐王璟':'李璟','继严':'王继严','继镛':'王继镛','让皇':'杨溥'})
mar='jiuwudaishi-078-march';apr='jiuwudaishi-078-april';may='jiuwudaishi-078-may';minbook='xinwudaishi-068-min-superstition'
add('wang_yanzhong_rebels','王彦忠据怀远城叛乱',9,'寻州','据怀远城叛，',[('王彦忠','以戍将身份据怀远城叛乱')],place='灵州、怀远城',description='戍将王彦忠据怀远城叛乱。《旧五代史》记为灵州戍将；《资治通鉴》所用电子本此处作“寻州”，地名字形差异保留。',note='展示地名依据旧史灵州，原文寻州戌将不改；未新增现代坐标或据怀远同名地名定现代位置。')
sup('wang_yanzhong_rebels',9,mar,'靈州戍將王彥忠據懷遠城作叛，','《旧五代史》也记王彦忠据怀远城叛乱，具体职地为灵州。','两书同名及同城叛乱行动相合，地名字形差异明确保留。',relation='conflicts')
add('qi_recruits_wang','石敬瑭派齐延祚招谕王彦忠，王彦忠投降',9,'上遣','彦忠降，',[('帝','派供奉官齐延祚招谕王彦忠'),('齐延祚','奉命招谕王彦忠'),('王彦忠','接受招谕并投降')],place='怀远城',note='招谕与投降确为发生，后面的杀降分别记录，未补出招谕时未载具体赦书条款。')
sup('qi_recruits_wang',9,mar,'帝遣供奉官齊延祚乘驛而往，彥忠率眾出降，','《旧五代史》补记齐延祚乘驿前往，王彦忠率众出城投降。','只补行程方式和率众出降，不编投降人数。')
add('qi_kills_surrendered_wang','齐延祚擅自杀死已投降的王彦忠',9,'延祚杀之。','延祚杀之。',[('齐延祚','擅自杀死已经投降的王彦忠'),('王彦忠','投降后被齐延祚杀死')],place='怀远城',note='上文投降、下文皇帝何得擅杀之明确杀降及越权，不写成奉石敬瑭命处决。')
sup('qi_kills_surrendered_wang',9,mar,'延祚矯制殺之。','《旧五代史》进一步写齐延祚假传诏令杀死王彦忠。','矫制为该书补充的越权方式，不据此补伪造诏书全文。')
add('shi_punishes_qi','石敬瑭因齐延祚擅杀降将，将其除名、杖打并流放',9,'上怒曰：','重杖配流，',[('帝','认为杀降违背诚信，责罚齐延祚'),('齐延祚','被除名、重杖并流放')],description='石敬瑭发怒，强调自己即位以来没有失信于人，王彦忠已经交出武器并出迎，齐延祚无权擅杀。石敬瑭将齐延祚除名、重杖并流放。',note='输仗按交出武器解释，除名非处死，流放地点未载；不推石敬瑭从未失信是网站独立历史结论。')
sup('shi_punishes_qi',9,mar,source_span(mar,'詔：「齊延祚','配流。'),'《旧五代史》也记皇帝以杀降损害诚信为由，下令将齐延祚除名、重杖、流放。','原敕文字保留，刑罚未记具体流放目的地。')
claim('person',people['王彦忠（怀远城戍将）'],'description','《旧五代史》还记王彦忠死后获赠官职并收葬。',9,'王彥忠贈官收葬。','这是身后处置；官职具体名称未载，不补姓名或官阶。',source=mar)
add('commentators_qi_death_penalty','史书记述有人认为齐延祚杀降不应免死',9,'议者犹',None,[],description='《资治通鉴》记，当时议论者仍认为齐延祚不应该免于死刑。',note='这是记载中的批评意见，未具名；不能据此写成实际执行死刑。')
add('renmei_fenghua','石敬瑭册回鹘可汗仁美为奉化可汗',10,'辛酉，',None,[('帝','册仁美为奉化可汗'),('仁美','以回鹘可汗身份获册奉化可汗')],when='939年三月辛酉',note='仁美仅按本句身份识别，不补未经校核的姓氏、世系或与仁裕等近名人物的关系。')
sup('renmei_fenghua',10,mar,'辛酉，封回鶻可汗仁美為奉化可汗。','《旧五代史》也记三月辛酉封回鹘可汗仁美为奉化可汗。','回鶻与回鹘为字形差异，原文保留，不另造族群实体。')
add('xu_zhizheng_surname_refused','李昪拒绝徐知证等改姓李的请求',11,'夏，四月，',None,[('徐知证','与江王宗室等请求一同改姓李，未获准'),('唐主','拒绝徐知证等改姓李的请求')],when='939年四月，具体日期未载',note='前批李昪本人恢复李姓已发生，此条是徐氏宗室请求；不把徐知证改名李知证。')
add('li_bian_south_suburb_rites','李昪在南郊举行祭祀',12,'辛巳，','唐主祀南郊；',[('唐主','在南郊举行祭祀')],when='939年四月辛巳',place='南郊',note='史书未列仪仗、祭品和具体地理坐标，不扩写。')
add('li_bian_april_amnesty','李昪下令大赦',12,'癸未，',None,[('唐主','下令大赦')],when='939年四月癸未',note='大赦与两日前郊祀分别记录，未列罪名豁免范围，不补法律细目。')
add('privy_historical_division','史书记述梁以来军国决策多由皇帝与崇政、枢密使商议',13,'梁太祖以来，','治文事而已。',[],year=None,when='梁太祖以来的制度追述，非939年单日事件',description='《资治通鉴》概述，梁太祖以来，军国大事多由皇帝与崇政使、枢密使商议；宰相接受决定，负责诏令、典故和文书事务。',note='这是对此前制度的概述，不改成每位皇帝和每件事务都没有例外。')
add('shi_initial_sang_privy','史书解释石敬瑭起初限制枢密使权力的原因',13,'帝惩','但命桑维翰兼枢密使。',[('帝','顾忌安重诲的旧事，即位初命桑维翰兼枢密使'),('桑维翰','在石敬瑭即位初兼任枢密使')],year=None,when='石敬瑭即位之初的追述，本句未列具体日期',description='《资治通鉴》解释，石敬瑭顾忌后唐明宗时期安重诲专横的旧事，因此即位初只让桑维翰兼任枢密使。',note='安重诲专横是本句史书对前朝的评价；追述不写成本年新任官，也不再造已公开任官事件的确定日期。')
add('liu_churang_mother_mourning','刘处让任枢密使后奏对不合旨意，随后因母丧服丧',13,'及刘处让','会处让遭母丧，',[('刘处让','任枢密使后多次奏对不合皇帝心意，随后遭母丧')],year=None,when='废枢密院之前的追述，母丧具体日期未载',description='刘处让接任枢密使后，奏对多次不合石敬瑭的心意，随后因母亲去世服丧。',note='母丧不是刘处让本人去世，母亲姓名未载；接任沿前批已公开记录，不另造第二次任命。')
add('shi_abolishes_privy','石敬瑭废枢密院，将印信和事务交中书、宰相分管',13,'甲申，','院事皆委宰相分判。',[('帝','废枢密院，将印信交中书，事务交宰相分管')],when='939年四月甲申',description='石敬瑭废除枢密院，将院印交给中书，原由枢密院处理的事务改由宰相分别管理。',note='废院与交印为具体制度调整，不推已经取消所有军事指挥权或全国军事机构。')
sup('shi_abolishes_privy',13,apr,'遂以密院印付中書，故密院廢焉。','《旧五代史》也记因刘处让母丧，将密院印交中书，废枢密院。','该书先是部分是背景追述，当前甲申官职调整有前文日期；不把母丧单独强定同日。')
add('zhang_congen_xuanhui','张从恩由枢密副使改任宣徽使',13,'以副使','为宣徽使，',[('张从恩','从枢密副使改任宣徽使')],when='939年四月甲申')
sup('zhang_congen_xuanhui',13,apr,'樞密副使張從恩改宣徽使：初廢樞密院故也。','《旧五代史》也记张从恩改宣徽使，并解释因枢密院被废。','职务变化与废院原因相合，不补此句未列的南院北院分工。')
add('situ_yan_lose_privy_posts','司徒诩和颜衎解除枢密院职务，保留本官',13,'直学士、','并罢守本官。',[('司徒诩','解除枢密直学士职务，保留仓部郎中本官'),('颜衎','解除枢密直学士职务，保留工部郎中本官')],when='939年四月甲申',note='罢守本官是解除院职、保留本官，不能写成二人完全罢官为民。')
sup('situ_yan_lose_privy_posts',13,apr,'樞密院學士、尚書倉部郎中司徒詡，樞密院學士、尚書工部郎中顏衎並落職守本官，','《旧五代史》也记司徒诩、颜衎落职守本官，并分别列仓部郎中和工部郎中职衔。','诩、詡为繁简，司徒为复姓；不拆成姓司、名徒诩的新人。')
add('privy_restoration_wishes','史书记述勋臣和近臣仍希望恢复枢密院',13,'然勋臣',None,[],year=None,when='废枢密院之后的持续追述，具体起止年月未载',description='《资治通鉴》评价部分勋臣和近臣不明大体、习惯旧制，仍经常希望恢复枢密院。',note='愿望与制度评价归史书，未说明这些人姓名或此时已经恢复机构。')
add('li_zhuanmei_restored','石敬瑭因前朝旧臣贫困，任李专美为赞善大夫',14,'帝以','赞善大夫，',[('帝','因前朝被除名旧臣生活贫困，任用李专美'),('李专美','重新获任赞善大夫')],description='石敬瑭看到两京被除名的后唐旧臣生活贫困憔悴，重新任李专美为赞善大夫。',note='本条在丙戌之前，主书未单列李专美任官日期；并致仕只随后三人任命，不扩大给李专美。')
add('han_ma_fang_retire','韩昭胤、马胤孙和房暠获授官职并退休',14,'丙戌，','并致仕。',[('帝','授予三位后唐旧臣官职并准退休'),('韩昭胤','以兵部尚书身份退休'),('马胤孙','以太子宾客身份退休'),('房暠','以右骁卫大将军身份退休')],when='939年四月丙戌',note='致仕是退休，不能把这三个官职都写成继续处理政务的实际任职。')
sup('han_ma_fang_retire',14,apr,source_span(apr,'丙戌，','皆唐末帝之舊臣也。'),'《旧五代史》也记四月丙戌韩昭裔、马裔孙、房暠分别获授相同官职并退休。','韩昭裔和韩昭胤、马裔孙和马胤孙沿既有别名，保留各书字形。')
add('lin_accuses_wang_uncles','林兴因与王延武有怨，假托神言诬指两位王氏宗室谋变',14,'闽主忌','延望将为变。”',[('闽主','忌惮两位叔父才名'),('林兴','因与王延武有怨，假托神言诬指两人谋变'),('延武','因才名受到猜忌，又被林兴诬指谋变'),('延望','因才名受到猜忌，被林兴诬指谋变')],place='闽国',description='王继鹏忌惮叔父王延武和王延望的才名。巫者林兴与王延武有怨，假托鬼神之言，声称王延武、王延望将谋变。',note='本书写为假托神言的指控，不改为二人确已叛乱；叔父称谓只依主书，不补具体兄弟排行。')
add('min_kills_uncles_children','王继鹏不加核查，命林兴杀死王延武、王延望及五名子女',14,'闽主不复诘，','并其五子。',[('闽主','未进一步核查，命林兴率壮士杀害宗室及其子女'),('林兴','奉命率壮士到住宅杀害王延武、王延望及五名子女'),('延武','在住宅被杀，其家子女也遭杀害'),('延望','在住宅被杀，其家子女也遭杀害')],place='闽国',description='王继鹏没有进一步核查林兴的指控，就命他率壮士到住宅，杀死王延武、王延望以及两人的五名子女。',note='两书均列子五人，不扩大为每家五人；子女性别和个人名字未单独说明，不造匿名人物节点。')
sup('min_kills_uncles_children',14,minbook,source_span(minbook,'三年夏，','及其子五人。'),'《新五代史》也记三年夏，林兴借宫中见虹宣称宗室将乱，奉命杀王审知之子延武、延望及其五名子女。','主书同事置939夏，新史三年夏沿通文纪年；虹兆是林兴的说法，不能写为真实神谕。')
relationship('延武','王继鹏','叔父',14,span(14,'闽主忌','才名，'),'原文明示王延武是王继鹏的叔父，方向为王延武指向王继鹏；不另推长幼排序。')
relationship('延望','王继鹏','叔父',14,span(14,'闽主忌','才名，'),'原文明示王延望是王继鹏的叔父，方向为王延望指向王继鹏。')
relationship('王审知','延武','父亲',14,'乃命興率壯士殺審知子延武、延望及其子五人。','新五代史明示王延武为王审知之子，父亲方向明确；复用王审知主体。',source=minbook)
relationship('王审知','延望','父亲',14,'乃命興率壯士殺審知子延武、延望及其子五人。','新五代史明示王延望为王审知之子，父亲方向明确。',source=minbook)
add('min_builds_sanqing','王继鹏听从陈守元建议，在宫中建三清殿并铸金神像',14,'闽主用陈守元言，','老君像，',[('闽主','采纳陈守元建议，建三清殿并用数千斤黄金铸神像'),('陈守元','提出建造三清殿、铸神像的建议')],place='闽国宫中',note='宝皇大帝、天尊和老君是所铸宗教形象，不新增为在世历史人物；数千斤不换算现代重量。')
sup('min_builds_sanqing',14,minbook,source_span(minbook,'守元教昶','太上老君像，'),'《新五代史》将建筑记为三层三清台，并同样记陈守元建议、以数千斤黄金铸神像。','主书三清殿、新史三清台三层分别保留，不据此把主书殿堂确定复原为同一三层建筑。')
add('min_rites_seeks_elixir','王继鹏昼夜作乐、焚香祷祀，求取神丹',14,'昼夜作乐，','求神丹。',[('闽主','昼夜作乐、焚香祷祀，意图求取神丹')],place='闽国宫中',note='求神丹是所求目标，不写成已经炼成神丹或获得长生。')
add('lin_controls_political_orders','闽国政事由林兴假托宝皇之命决定',14,'政无大小，',None,[('林兴','假托宝皇之命决定政事'),('闽主','让林兴传所谓宝皇之命处理政事')],description='《资治通鉴》记，闽国政事不论大小，都由林兴传达所谓宝皇之命来决定。',note='宗教言辞是操纵政事的方式，不认可为真实超自然指令。')
sup('lin_controls_political_orders',14,minbook,'事無大小，興輒以寶皇語命之而後行。','《新五代史》也记政事须先得到林兴所传宝皇之语，才付诸实行。','印证通过所谓神命处理政事，不推出每条实际命令内容。')
add('ma_tiance_rank','石敬瑭加马希范天策上将军，赐印并准开府置官',15,'戊申，',None,[('帝','加马希范天策上将军，赐印并准开府置官'),('楚王希范','获加天策上将军，得到开府置官许可')],when='939年夏戊申，主书未重列月份',note='听开府是许可，后面实际开天策府另有记载；此处不提前把全部官属视作已经任命。')
sup('ma_tiance_rank',15,may,'戊申，湖南節度使馬希範加天策上將軍。','《旧五代史》明确把马希范加天策上将军记在五月戊申。','主书四月之后未再标五月，依据该书补具体月份；不把后续所有日干支都盲目归四月。',field='time_original')
add('jing_sui_shouwang','徐景遂由吉王改封为寿王',16,'辛亥，','景遂为寿王，',[('唐主','将景遂由吉王改封为寿王'),('景遂','由吉王改封寿王')],when='939年夏辛亥，主书未重列月份',note='沿既有徐景遂稳定主体，原文只写景遂；不因父亲复姓李而新建第二个人物。')
add('jing_da_xuancheng','徐景达由寿阳公获封宣城王',16,'立寿阳公',None,[('唐主','封景达为宣城王'),('景达','由寿阳公获封宣城王')],when='939年夏辛亥，主书未重列月份',note='由公到王是封爵变化，不写为景达即位称帝。')
add('xu_zhie_dies','镇海节度使徐知谔去世',17,'乙卯，',None,[('徐知谔','以镇海节度使、兼中书令、梁怀王身份去世')],when='939年夏乙卯，主书未重列月份',note='梁怀王是本句所列封号，不与后梁皇帝混淆；月份不从前面的四月标题机械沿用。')
claim('person',people['徐知谔'],'death_year','《资治通鉴》在939年夏季后续条记徐知谔去世。',17,Q[17]['text'],'这里只补死亡出处，不重写早年已发布人物档案。')
add('wu_family_yongning','南唐迁杨溥的族人到泰州永宁宫，严加防卫',18,'唐人迁','防卫甚严。',[('让皇','族人被南唐迁往泰州永宁宫')],place='泰州、永宁宫',description='南唐将吴让皇杨溥的族人迁到泰州，住处称永宁宫，并严密防卫。',note='本句迁的是族人，杨溥本人已经在此前记录中去世；防卫严密不补守军人数和现代遗址位置。')
add('yang_gong_returns_yongning','杨珙称病，卸任后回到永宁宫',18,'康化节度使','罢归永宁宫。',[('杨珙','以康化节度使、兼中书令身份称病，卸任返回永宁宫')],place='永宁宫',note='称疾是称病的行动，不确诊病名，也未记此时死亡。')
add('yang_lian_kanghua_refused','李昪任杨琏为康化节度使，杨琏以服丧推辞获准',18,'乙丑，',None,[('唐主','任杨琏为康化节度使，准他辞任继续服丧'),('杨琏','被任为康化节度使，坚决推辞并请求服丧到底')],when='939年夏乙丑，主书未重列月份',description='李昪将平卢节度使、兼中书令杨琏任为康化节度使。杨琏坚决推辞，请求继续服丧到底，李昪允许了。',note='任命与实际未就任分开表述；终丧不是自杀殉葬，不凭此句猜服丧期精确结束日。')
add('li_jing_declines_heir','李璟坚辞李昪拟授的太子身份',19,'唐主将立','固辞；',[('唐主','打算立齐王李璟为太子'),('齐王璟','坚决推辞被立为太子')],note='将立为意图，固辞表示拒绝；本句不录为已经正式立太子。')
add('li_jing_high_offices','李璟受任大元帅、守太尉、录尚书事及升扬二州牧等职',19,'乃以为',None,[('唐主','改授李璟诸道兵马大元帅等职'),('齐王璟','受任诸道兵马大元帅、判六军诸卫、守太尉、录尚书事、升扬二州牧')],description='李璟推辞太子身份后，李昪授他诸道兵马大元帅、判六军诸卫、守太尉、录尚书事，以及升州、扬州二州牧等职。',note='本段任官是替代授职，未表示李璟已经继承帝位；保留正式官名，不猜每项实际权限。')
add('wang_jiyan_disarmed','王继鹏因猜忌，解除王继严兵权并将其改名继裕',20,'闽判六军','更名继裕；',[('闽主','因王继严获得军士支持而猜忌他，解除其兵权并改名'),('继严','被解除判六军诸卫兵权，改名继裕')],when='939年六月，具体日期未载',description='建王王继严任判六军诸卫，得到军士支持，王继鹏因此猜忌他。六月，王继鹏解除他的兵权，并将他改名为继裕。',note='改名沿王继严稳定主体，新增事实引用，不因名字不同造王继裕新人物。')
claim('person',people['王继严'],'aliases','939年六月，王继严被改名为王继裕。',20,span(20,'闽判六军','更名继裕；'),'保留既有稳定key；这是改名证据，未覆盖既有公开别名数组。')
add('wang_jiyong_commands','王继鹏命王继镛判六军，职名删去诸卫二字',20,'以弟继镛','去诸卫字。',[('闽主','命弟弟王继镛判六军，删去诸卫二字'),('继镛','受命判六军')],when='939年六月，具体日期未载',note='原文删职名诸卫二字，不据此推所有卫军机构均被撤销。')
relationship('继镛','王继鹏','弟弟',20,'以弟继镛判六军，去诸卫字。','主语沿闽主王继鹏，王继镛是他的弟弟，方向为弟弟指向兄长。')
add('lin_exiled_quanzhou','林兴骗局败露，被流放泉州',20,'林兴诈觉，','流泉州。',[('林兴','骗局败露后被流放泉州')],when='939年六月条下，具体日期未载',place='泉州',note='流泉州为流放，不写为本句已经被处死或自行移居。')
sup('lin_exiled_quanzhou',20,minbook,'後興事敗，亦被殺。','《新五代史》另记林兴后来事情败露，被杀。','主书此处记流放，新史记后来被杀而未列确日；两种处置分别保留，不能直接推定是在流放之前或之后，也不强定死亡年。',relation='adds')
add('min_moves_changchun','王继鹏听望气者称宫中有灾，迁居长春宫',20,'望气者',None,[('闽主','因望气者声称宫中有灾而迁居长春宫')],when='939年六月乙未',place='长春宫',description='望气者声称宫中将有灾祸。王继鹏在乙未迁居长春宫。',note='灾祸说法归望气者；这是闽国宫名，不与旧史四月撤同州长春宫使额混成同一宫殿。')
reviews={9:'主寻州戌将、旧灵州戍将字形差异保留，展示依据旧史；招谕投降、齐擅杀、石除名杖流及议者主张死刑分别录，不能把主张当执行。旧补矫制及赠官收葬。',10:'回鹘仁美册奉化可汗，主旧三月辛酉相合；不猜姓氏或近名关系。',11:'徐知证等请求随李昪改姓未获准，不能新增李知证身份。',12:'四月辛巳南郊祭祀和癸未大赦分日记，不补赦免细目。',13:'梁以来制度背景、桑维翰初兼任及刘母丧为追述；四月甲申废院交印委相与张改职、司徒颜落职守本官分录。愿复院不写已经恢复。旧史官命、原因补证。',14:'李专美恢复官职不并入后三人退休；韩昭胤马胤孙异字沿已核别名。林兴指控是假托，王延武延望及合计五名子女被杀，性别未明不补。主叔父与新父王审知关系各证、方向明确；殿与三层台异记分列，神命不认作真实。',15:'主未重列月份，旧史明确五月戊申；马希范获开府许可不等于已开府任官。',16:'景遂、景达复用既有主体；辛亥未重列月，按夏季记，不机械沿四月。',17:'徐知谔死在939夏乙卯条，未列月，不把梁怀王误为后梁君主。',18:'被迁是杨溥族人，本人已死；杨珙称病卸任，杨琏获命又辞任终丧分别录，未断言任命实际就任。',19:'李璟坚辞太子是拒绝拟授，另授大元帅等职非已经立太子或继位。',20:'六月王继严兵权解除改继裕、王继镛任判六军职名调整、林兴流泉州与乙未迁宫分别录。新史后被杀保留时间未知，不推本句已处死。'}
assert not (P/'publication.json').exists()
for n in range(9,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=939,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,21)],next_paragraph=Q[21]['id'],next_volume=282,next_year=939,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第9—20段，原14—25行，三月至六月；939年41段，后21段待录。',source_issues_review='主寻州、旧灵州保字；未重列五月的条目不沿四月，马希范旧史五月补证。王延武延望被杀及五子、三清殿与台、林兴流放与后来被杀差异分别保留；纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,21)],plain_language_review='首次逐条检查现代白话、主体身份、关系方向、时间和出处；追述与本年行动、指控与事实、意图许可与执行、意见与处置分开，引用保留原字。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
