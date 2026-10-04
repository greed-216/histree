# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 941 paragraphs 22–29."""
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
specs=[(d.name,d,'179342146c1d78cfe3d5641c28e7db199f4e8b59','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

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
main_sources = ['tongjian-282-941-autumn-winter']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0941-p022-p029',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-282-941-autumn-winter':'卷282·天福六年九月至十二月','xinwudaishi-051-an-congjin-orders':'卷51·安从进传·预备空名宣敕','xinwudaishi-051-an-congjin-retreat':'卷51·安从进传·出兵与败退','jiuwudaishi-080-an-congjin-battle':'卷80·晋高祖纪·天福六年十二月奏十一月战事','jiuwudaishi-098-an-congjin-orders':'卷98·安从进传·预备空名宣敕'}
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
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(22, 30):
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
    labels={'tongjian-282-941-autumn-winter':'卷282·天福六年九月至十二月','xinwudaishi-051-an-congjin-orders':'卷51·安从进传·预备空名宣敕','xinwudaishi-051-an-congjin-retreat':'卷51·安从进传·出兵与败退','jiuwudaishi-080-an-congjin-battle':'卷80·晋高祖纪·天福六年十二月奏十一月战事','jiuwudaishi-098-an-congjin-orders':'卷98·安从进传·预备空名宣敕'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '九月条下' if n<=24 else '九月至十月' if n==25 else '十月条下' if n==26 else '八月北行追述' if n==27 else '十一月条下'
        citation = f'卷282·后晋天福六年（941；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0941_05_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=941, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='941年'+('九月' if n<=24 else '十月' if n<=26 else '八月北行追述' if n==27 else '十一月')+'条下，具体日期未载'
    key = 'event_zztj_282_0941_' + code
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
        edge = 'participation_zztj_282_0941_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0941_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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






ALIASES.update({'唐主':'李昪','曦':'王延羲','延政':'王延政','亚澄':'王亚澄','郑王':'石重贵','李敏':'李敏（闽国宰相）','弘义':'安弘义'})
NEW_DESCRIPTIONS={
'李敏（闽国宰相）':'闽国同平章事。资治通鉴941年十月条下记他去世。与早已去世、曾名李敏的唐昭宗分开建档；是否与早期闽国尚书、李春燕之父李敏为同一人，另待史料校核。出生年未载。',
'武延翰':'后晋唐州刺史。941年十一月向朝廷奏报安从进举兵攻邓州。生卒年未载。',
'焦继勋':'后晋武德使。941年十一月受石重贵派遣，与张从恩、郭金海、陈思让领大梁兵讨伐安从进；旧史奏报中也列其参与唐州以南战役。生卒年未据本段确定。',
'郭金海':'后晋护圣都指挥使，原属突厥。941年十一月受石重贵派遣讨伐安从进，丁丑获任先锋使。生卒年未载。',
'陈思让':'后晋作坊使，幽州人。941年十一月受石重贵派遣讨伐安从进，丁丑获任先锋军监军。生卒年未据本段确定。',
'李建崇':'后晋申州刺史。941年十一月所率军队为石重贵遣兵赴叶县会合讨伐安从进的对象。新五代史记他与郭金海等受空名敕出讨，在湖阳遇安从进军。生卒年未载。',
'宋彦筠':'后晋前同州节度使，滑州人。941年十一月丁丑受任高行周的副将，参与南面军前讨伐安从进的部署。生卒年未载。',
'安弘义':'安从进的儿子，牙内都指挥使。941年十一月癸未花山战役中被张从恩军俘获。旧史对应奏报写安宏義，姓名字形作为同次战役的异写保留。生卒年未载。'}
NEW_ALIASES={'李敏（闽国宰相）':[],'武延翰':[],'焦继勋':['焦繼勛'],'郭金海':[],'陈思让':['陳思讓'],'李建崇':[],'宋彦筠':['宋彥筠'],'安弘义':['安弘義','安宏义','安宏義']}
old='jiuwudaishi-080-an-congjin-battle';orders='xinwudaishi-051-an-congjin-orders';retreat='xinwudaishi-051-an-congjin-retreat';oldorders='jiuwudaishi-098-an-congjin-orders'
add('huazhou_reports_breach','滑州奏报黄河决口',22,'辛酉，',None,[],when='941年九月辛酉，奏报日期',place='滑州',note='言是地方奏报，决口实际发生日期未载，不能把奏报日直接当决口日；未给灾情范围或伤亡。')
add('shi_sends_yang_yanxun','石敬瑭派杨彦询出使契丹，担忧安重荣杀使引起边境战争',23,'帝以安重荣','使于契丹。',[('帝','因担忧契丹进犯而派使交涉'),('杨彦询','以安国节度使身份出使契丹')],when='941年九月乙亥',note='乙亥为遣使日，抵达契丹具体日期未载；恐其犯塞是皇帝担忧，未写成契丹已入侵。')
add('khitan_rebukes_yang','耶律德光向杨彦询责问契丹使者被杀的经过',23,'彦询至其帐，','契丹主责以使者死状，',[('杨彦询','抵达契丹主帐中，受到责问'),('耶律德光','责问使者死亡情况')],when='941年九月乙亥遣使后，具体日期未载',place='契丹主帐中')
add('yang_explains_an','杨彦询以父母无法管住恶子的比喻解释安重荣行为，耶律德光怒气缓解',23,'彦询曰：',None,[('杨彦询','以恶子难制的比喻解释安重荣行为'),('耶律德光','听解释后怒气缓解')],when='941年杨彦询抵达契丹帐中后，具体日期未载',description='杨彦询把安重荣比作父母也管不住的恶子，问这种情况该怎么办。耶律德光的怒气因此缓解。',note='恶子为外交比喻，不建立安重荣与皇帝的血缘父子关系，也不补未载的赔偿协议。')
add('xi_promotes_yacheng_again','王延羲任王亚澄为威武节度使、兼中书令，改封长乐王',24,'闽主曦',None,[('曦','任命儿子并改封王号'),('亚澄','获任威武节度使、兼中书令并改封长乐王')],place='闽国',note='与此前同平章事、判六军诸卫的任命分期；父子关系已录，不重复新建。')
add('guo_wei_persuades_bai','刘知远派郭威奉诏劝白承福离开安重荣，许以节度使职位',25,'刘知远遣','许以节钺。',[('刘知远','派亲将奉诏劝降并许授节度使'),('郭威','奉诏向白承福提出归附与授官条件'),('白承福','收到离开安重荣归朝廷的劝说')],when='941年十月白承福归附以前，具体日期未载',note='许以节钺是承诺，不写成当时已授节度使。')
add('guo_wei_advises_gifts','郭威回报刘知远，建议以厚礼招来白承福',25,'威还，','知远从之，',[('郭威','回报并建议用厚礼招来白承福'),('刘知远','接受厚礼招抚建议')],when='941年十月白承福归附以前，具体日期未载',description='郭威回报，认为安重荣只用袍裤赠给部众，若要招来白承福，应给更多财物。刘知远接受建议。',note='惟利是嗜是郭威对部众的评价，不作为本站对整个族群的判断；厚礼种类及价值未载。')
add('liu_warns_bai','刘知远派人警告白承福，要求停止支持安重荣并归朝廷',25,'且使谓承福曰：','悔无及矣。”',[('刘知远','派人警告白承福应尽早归朝廷'),('白承福','收到朝廷可能用兵的警告')],when='941年十月白承福归附以前，具体日期未载',description='刘知远派人告诉白承福，朝廷此前已将他们划归契丹，南来助安重荣会陷入叛逆；安重荣即将败亡，应尽早归朝廷，以免被用兵后南北无所归。',note='安重荣即将败亡是劝说中的判断，不记成已败；本条不是朝廷已出兵攻击白承福。')
add('bai_submits_to_liu','白承福害怕，率部归附刘知远',25,'承福惧，','帅其众归于知远。',[('白承福','因警告害怕，率部归附'),('刘知远','接受白承福部众归附')],when='941年冬十月，具体日期未载')
add('liu_settles_tuyuhun','刘知远将白承福部众安置在太原东山及岚州、石州之间',25,'知远处之','及岚、石之间，',[('刘知远','安置白承福部众'),('白承福','所率部众被安置在河东')],when='941年十月归附以后，具体日期未载',place='太原东山、岚州与石州之间',note='史载地理范围保留，不补聚落坐标。')
add('liu_recommends_bai_office','刘知远上表请求白承福领大同节度使',25,'表承福','领大同节度使，',[('刘知远','上表推荐白承福领大同节度使'),('白承福','被推荐领大同节度使')],when='941年十月归附以后，具体日期未载',note='表为上表请求，原文没有另记朝廷批准日期，不把表荐当作已完成授官。')
add('liu_takes_tuyuhun_cavalry','刘知远收白承福部中精锐骑兵归自己指挥',25,'收其精骑','以隶麾下。',[('刘知远','收编精锐骑兵'),('白承福','所率部众中的精骑被收编')],when='941年十月归附以后，具体日期未载',note='骑兵人数未载，不把安重荣此前奏表十万众套给此次收编。')
add('an_claims_tribal_support','安重荣此前檄告各道，声称将与吐谷浑、达靼、契苾一同起兵',25,'始，安重荣','同起兵，',[('安重荣','檄告各道并声称获得诸部共同起兵支持')],year=None,when='白承福归附刘知远以前，具体年月未载',note='始引出前事，云为檄文声称，不确认各部已同意或一同起兵。')
add('an_loses_expected_support','白承福归刘知远，达靼、契苾也未赴援，安重荣势力大减',25,'既而承福',None,[('安重荣','失去预期的部众支持，势力受挫'),('白承福','归附刘知远使安重荣失去其支持')],when='941年十月白承福归附后，具体日期未载',note='未赴是缺乏实际支援，不据此建各部此前已结盟或背叛的关系。')
add('xi_ascends_emperor','王延羲正式即闽国皇帝位',26,'闽主曦','即皇帝位。',[('曦','即皇帝位')],place='闽国',note='与此前自称大闽皇的称号记录分期，依据本段正式即位动作。')
add('yan_claims_marshal','王延政自称兵马元帅',26,'王延政','自称兵马元帅。',[('延政','自行称兵马元帅')],place='建州',note='自称不当作王延羲授官。')
add('li_min_dies','闽国同平章事李敏去世',26,'闽同平章事',None,[('李敏','以闽国同平章事身份去世')],place='闽国',note='与唐昭宗旧名李敏分开识别，不能按字面别名合并。')
add('he_ning_proposes_blank_orders','和凝在石敬瑭北行时建议留下空名宣敕，应对安从进反叛',27,'帝之发大梁也，','遣击之；',[('和凝','建议预留空名宣敕给留守'),('帝','听取预防安从进反叛的建议'),('郑王','被建议持敕应变，及时命将讨伐')],when='941年八月石敬瑭离开大梁时',description='和凝担忧石敬瑭北行后安从进反叛，建议秘密留下十几通未填将领姓名的宣敕，交给留守石重贵；发生变乱后即可填入将领姓名，派兵讨伐。',note='这是八月北行时的追述，不强定十一月；空名指预留将领姓名，不是一般空白文书。')
sup('he_ning_proposes_blank_orders',27,orders,'願為空名宣敕十數通授鄭王，有急則命將以往。','《新五代史》同记和凝建议预备十几通空名宣敕，交石重贵以便紧急命将。','同记应变办法及数量措辞；未把预备诏令当作叛乱已经发生。')
sup('he_ning_proposes_blank_orders',27,oldorders,'願陛下為空名宣敕十通授鄭王，有急則命將往。','《旧五代史》安从进传记空名宣敕十通。','主书与新史十数通，旧史十通，数量详略作为异说保留。',relation='conflicts')
add('shi_accepts_blank_orders','石敬瑭接受和凝预留宣敕的建议',27,'帝从之。','帝从之。',[('帝','接受预留空名宣敕建议')],when='941年八月石敬瑭离开大梁时',note='本条为接受建议，石重贵实际动用宣敕在随后讨伐记载补充。')
add('an_attacks_dengzhou','安从进举兵进攻邓州',28,'十一月，','攻邓州，',[('安从进','举兵进攻邓州')],when='941年十一月，具体日期未载',place='邓州',note='此处才是实际举兵，与此前筹谋和求援分期。')
add('wu_reports_an_attack','唐州刺史武延翰奏报安从进攻邓州',28,'唐州刺史','以闻。',[('武延翰','向朝廷奏报安从进举兵进攻')],place='唐州',note='奏报日期未载，不当作同日开始进攻。')
add('chonggui_sends_campaign_army','石重贵派张从恩等率大梁兵，赴叶县会合李建崇军讨安从进',28,'郑王遣','以讨之。',[('郑王','派遣讨伐军'),('张从恩','以宣徽南院使身份率兵讨伐'),('焦继勋','以武德使身份率兵讨伐'),('郭金海','以护圣都指挥使身份率兵讨伐'),('陈思让','以作坊使身份率兵讨伐'),('李建崇','所率军队成为大梁兵奉命赴叶县会合的对象')],place='叶县',note='就兵为赴军队处会合，不写成李建崇由南唐张建崇改名或将申州搬到叶县。')
sup('chonggui_sends_campaign_army',28,retreat,'鄭王以空名敕授李建崇、郭金海等討之，','《新五代史》明确记石重贵使用空名敕，命李建崇、郭金海等讨伐安从进。','实际动用预备敕令的补证，连接八月预备与十一月出兵，不把两段当不同讨伐。',relation='adds')
claim('person','person_郭金海','biography','郭金海原属突厥。',28,'金海，本突厥；','按主书明载族属，不凭姓名推定汉族或现代民族分类。')
claim('person','person_陈思让','biography','陈思让是幽州人。',28,'思让，幽州人也。','史载籍贯，不补现代出生地坐标。')
add('gao_campaign_commander','石敬瑭任高行周为南面军前都部署，宋彦筠为副，张从恩监军',28,'丁丑，','张从恩监焉；',[('帝','任命讨伐安从进的统帅与副将、监军'),('高行周','获任南面军前都部署'),('宋彦筠','获任高行周副将'),('张从恩','受命监军')],when='941年十一月丁丑',note='任官与已经会战分开；宋彦筠本段为前同州节度使。')
add('guo_chen_vanguard','石敬瑭任郭金海为先锋使，陈思让为先锋监军',28,'又以郭金海','陈思让监焉。',[('帝','任命先锋及先锋监军'),('郭金海','获任先锋使'),('陈思让','受命监先锋军')],when='941年十一月丁丑',note='又承接丁丑任命，不补两人统率兵数。')
claim('person','person_宋彦筠','biography','宋彦筠是滑州人。',28,'彦筠，滑州人也。','籍贯按原文保留。')
add('li_dechong_acts_tokyo','石敬瑭命李德珫暂任东京留守，召石重贵赴邺都',29,'庚辰，','如鄴都。',[('帝','调整留守并召石重贵'),('李德珫','由邺都留守暂任东京留守'),('郑王','被召赴邺都')],when='941年十一月庚辰',place='东京、邺都',note='权是临时担任；本条召赴不等于当天抵达邺都，与十二月正式留守任命分期。')
add('an_shenhui_defends_dengzhou','安从进攻邓州，安审晖据牙城抵抗，使其败退',29,'安从进攻邓州，','不能克而退。',[('安从进','进攻邓州未能攻克而退'),('安审晖','据牙城抵御安从进')],when='941年十一月花山战以前，具体日期未载',place='邓州',note='同次邓州进攻的守御与退却阶段，牙城为城内主将驻守的内城，不补现代城址。')
add('an_defeated_huashan','安从进在花山遇张从恩军，交战大败',29,'癸未，','合战，大败，',[('安从进','意外遇讨伐军，交战大败'),('张从恩','所率部队击败安从进')],when='941年十一月癸未',place='花山',note='未料到军队来得快是史书叙述，不补行军时速。')
sup('an_defeated_huashan',29,retreat,'進至湖陽，遇建崇等，大駭，以為神速，復為野火所燒，遂大敗。','《新五代史》记安从进进至湖阳，遇李建崇等，又遭野火，随后大败。','主书花山与新史湖阳地点表述不同，参战将领侧重也不同；保留同次败退的独立出处，未裁为两场战役或强改主书地名。',relation='conflicts')
sup('an_defeated_huashan',29,old,'南面軍前奏，十一月二十七日，武德使焦繼勛、先鋒都指揮使郭金海等於唐州南遇安從進賊軍一萬餘人，大破之，','《旧五代史》十二月纪载奏报，称十一月二十七日焦继勋、郭金海等在唐州南击败安从进一万多人的军队。','十一月二十七日为所报战日，十二月为奏报所列月份，不混为十二月交战；兵数为奏报声称，未自行换算或覆盖癸未。',relation='adds')
add('an_hongyi_captured','张从恩军俘获安从进之子安弘义',29,'从恩获其子','弘义，',[('张从恩','所率军队俘获安弘义'),('弘义','以牙内都指挥使身份被俘')],when='941年十一月癸未',place='花山')
sup('an_hongyi_captured',29,old,'生擒衙內都指揮使安宏義，獲山南東道之印，','《旧五代史》奏报同记擒获牙内都指挥使安宏义，并缴获山南东道印。','同次战役、同官职被俘者与主书安弘义对应，宏与弘作为姓名异写保留，不与传记次年所记安弘受合并。',relation='adds')
relationship('安从进','弘义','父亲',29,'从恩获其子牙内都指挥使弘义，','其子承接安从进，父亲方向明确；旧史全名安宏义用于核实姓氏及同次被俘身份。')
add('an_retreats_xiangzhou','安从进率数十骑逃回襄州，闭城自守',29,'从进以数十骑',None,[('安从进','战败后率数十骑逃回襄州，闭城自守')],when='941年十一月癸未战败后',place='襄州',note='婴城为闭城守御，不提前记为次年已经自焚。')
sup('an_retreats_xiangzhou',29,old,'其安從進單騎奔逸。','《旧五代史》奏报写安从进单骑逃走。','主书及新史数十骑，旧史奏报单骑，保留逃走人数的异说，未据此拆成两次不同逃亡。',relation='conflicts')
for row in B['people']:
 if row['name']=='李敏（闽国宰相）':
  row['death_year']=941
  claim('person',row['key'],'death_year','闽国宰相李敏于941年十月条下去世。',26,'闽同平章事李敏卒。','年代与职务符合闽国宰相，不能与唐昭宗旧名对应主体相合。')
reviews={22:'九月辛酉为滑州奏报日，河决发生日期未载。',23:'九月乙亥为遣杨彦询日，抵帐及应答未明日期；恶子是外交比喻，不建立血缘关系。',24:'王亚澄升威武节度使兼中书令与改封长乐王分于此前任官，父子关系不重复。',25:'郭威奉诏劝白承福、厚礼建议、威胁性劝说与十月实际归附、安置、表荐及收编分开。表领节度使不当明确已授；安重荣此前檄文云各部共同起兵保留声称，各部后来未赴援不自动推已结盟或背叛。',26:'王延羲即皇帝、王延政自称元帅与李敏去世分录。李敏为闽宰相，与唐昭宗旧名消歧；是否与早期闽尚书及李春燕父亲同人另待核。',27:'八月北行预备宣敕追述不套十一月；十数通与旧史十通差异保留，接受建议与实际动用敕令分期。',28:'十一月攻邓、武延翰奏报、石重贵遣军会合及丁丑统帅先锋任官分录；郭金海族属、陈思让及宋彦筠籍贯直接引用。',29:'十一月庚辰临时留守与十二月正式调任有别；邓州守御败退、癸未花山遇敌、俘安弘义及襄州自守分开。主书花山与新史湖阳、将领及火攻不同，旧史战日奏报十一月二十七和一万余人的兵数、单骑与数十骑分别保留，未提前记自焚。'}
assert not (P/'publication.json').exists()
for n in range(22,30):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=941,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(22,30)],next_paragraph=Q[30]['id'],next_volume=282,next_year=941,supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第22—29段，原107—114行；九月至十一月及八月追述。全年38段，累计29段，剩余9段待录。',source_issues_review='李敏闽国宰相与唐昭宗旧名及早期闽尚书身份需分别处理；花山与湖阳、空名宣敕十与十数、逃走单骑与数十骑等异说保留。旧史十二月记奏十一月战事，奏报月与战日严格区分。纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(22,30)],plain_language_review='首次检查新增人物介绍、事件说明、参与角色、关系方向、时间及事实引用；外交比喻、檄文声称、授官承诺、实际归附、上表、奏报与战斗日期分别说明，原文保留，旧主体字段不扩大改写。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
