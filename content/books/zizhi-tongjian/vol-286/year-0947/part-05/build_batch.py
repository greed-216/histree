# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 20–23."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='ce294d52ced25002a7ab63dd3c7dc2190f538b72'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-officials-looting']:
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
main_sources = ['tongjian-286-947-officials-looting','tongjian-286-947-zhang-nantang']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p020-p023',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
for n in range(20, 24):
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
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷286·天福十二年（947年正月）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_05_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
def existing(key,n,quote,text,note):
 row=next(x for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for x in json.loads(f.read_text())['events'] if x['key']==key)
 B['events'].append(dict(row,status='draft'));reused.add(key);used.setdefault(n,[]).append(key)
 claim('event',key,'description',text,n,quote,note)
 return key
ALIASES.update({'契丹主':'耶律德光','晋主':'石重贵','知远':'刘知远','刘九':'刘九（947年契丹将）'})
NEW_ALIASES={'王峻':[],'刘九（947年契丹将）':['劉九（947年契丹將）'],'高防':[],'王守恩':[],'赵行迁':['趙行遷']}
NEW_DESCRIPTIONS={'王峻':'安阳人，刘知远的客将。947年奉三表赴契丹，报告贺入大梁、暂不离太原及贡路受阻。《旧五代史》称牙将王峻，记二月出使和携杖回太原。生卒年本段未核。','刘九（947年契丹将）':'契丹将。947年刘知远的表章称他率一军从土门向西进入南川，引起太原城中忧惧。原书仅给名刘九，使用职务年代限定，不补真实姓名与生卒年。','高防':'昭义节度判官。947年张从恩拟往契丹朝见时，他以晋室亲属应守臣节为由劝谏，未被听从；张离镇后留下他协助赵行迁、王守恩。生卒年未载。','王守恩':'王建立的儿子，与张从恩是姻亲。947年在上党，以左骁卫大将军身份被张从恩暂派为巡检使，协助赵行迁。姻亲具体双方未明，不补具体婚配，生卒年未载。','赵行迁':'昭义节度副使。947年张从恩赴契丹朝见前，让他主持留后事务，并由王守恩、高防协助。生卒年未载。'}
t='947年初，具体月日未载';j='jiuwudaishi-089-liu-xu-office';jh='jiuwudaishi-099-947-envoy';sn='songshi-254-zhang-congen'
add('khitan_orders_liu_finance_reward','耶律德光以赏赐三十万名将士为由，命刘昫筹措钱帛',20,'契丹主谓','速宜营办。”',[('契丹主','声称三十万军队应得赏赐，命筹办'),('刘昫','以判三司身份被要求筹款')],when=t,place='大梁',note='三十万为耶律德光发言中的兵数，不当已核兵额。底本姓名有私用缺字，依据判三司及契丹入京职务与旧史刘昫传对应，不改原文。')
claim('person','person_刘昫','description','《旧五代史》记刘昫开运初复判三司，契丹入京后仍留原职。',20,'開運初，授司空、平章事，監修國史，復判三司。契丹主至，不改其職。','官职、时间及此前全站主体对应，用于主书缺字姓名识别；传末休致死亡是后续，不在本批提前录入。',source=j)
add('liu_requests_compulsory_city_loans','府库已空，刘昫请求向都城居民强制征借钱帛，将相也不能免除',20,'时府库空竭，','皆不免。',[('刘昫','因府库空竭请求向都城士民征借')],when=t,place='大梁',note='请为提出办法，将相以下不能免为叙述所记范围；不补每户额度、利息及还款承诺。')
add('khitan_envoys_force_provincial_loans','契丹分派数十名使者到各州征借钱帛，以重刑逼迫民众',20,'又分遣','人不聊生。',[('契丹主','派使者到各州强制征借')],when=t,place='各州',note='使者未具名不造名单，严诛是逼迫手段，不从此生成所有人已被杀的数量。')
add('khitan_retains_money_plans_north_transport','史书记征得钱帛没有赏军，而是存入内库，准备运回契丹',20,'其实无所','其国。',[('契丹主','将钱帛留内库，计划运回本国')],when=t,place='大梁内库至契丹（计划去向）',note='欲辇归为计划，不写已经运回；没有颁给按本段范围，不断言所有时代所有赏赐均未发生。')
add('exactions_create_resentment','史书记强制征敛使内外怨愤，人们开始希望驱逐契丹',20,'于是内外',None,[],when=t,place='大梁及各州',note='这是史家概述社会反应，不猜所有人的个人态度和政治组织。')
add('shi_liu_mistrust_background','史书记石重贵与刘知远彼此猜忌，刘知远虽有统帅名号，却不能参与诸军行动决定',21,'初，','不得预闻。',[('晋主','与刘知远相互猜忌'),('知远','虽有北面统帅名号，未获实际决策权')],when='944年任北面行营都统之后至契丹入大梁前（947年条下追述）',year=None,place='后晋朝廷与河东',note='任北面统帅已在944年记录，本事件记录主书追述的权力限制评价，不重复创建任命。相猜忌不做永久敌对关系。')
existing('event_zztj_284_0944_liu_zhi_yuan_northern_commander',21,span(21,'虽以为北面','不得预闻。'),'《资治通鉴》947年追述刘知远的北面行营都统名号，称他没有实际参与诸军行动决定。','复用944年已发布任命事件，只追加追述引用及实际权限说明，日期仍沿原档案，不新建同一任命。')
add('liu_expands_hedong_recruitment','刘知远因未获军队实际决策权，在河东广募士兵',21,'知远因之','士卒。',[('知远','在河东扩大募兵')],when='契丹入大梁之前（947年条下追述），具体起止日未载',year=None,place='河东',note='因之为史家联系前述权限问题，不把募兵开始强定为947或某一日。')
add('yangcheng_soldiers_join_hedong','阳城战役后，数千名离散士兵转投刘知远',21,'阳城之战，','数千人，',[('知远','接纳阳城战役后离散士兵')],when='945年阳城战役后至947年初（本段追述），具体归附日未载',year=None,place='河东',note='战役已在945年录入，此处记离散军人归附；数千是概数，归附日期不强定战役同日。')
existing('event_zztj_285_0946_liu_confiscates_bai_wealth',21,span(21,'又得吐谷浑','财畜，'),'《资治通鉴》947年追述刘知远取得吐谷浑财畜，作为河东富强的背景。','复用946年已录没收吐谷浑家产事件，不另建一次夺财；主书本段仅概述取得财畜，不重复杀戮。')
add('hedong_strength_assessed','史书记河东因吸收兵员和财畜而富强，步骑达到五万人',21,'由是河东',None,[('知远','治下河东被记为诸镇中富强突出')],when='至947年初的河东状况（本段追述）',year=None,place='河东',note='五万为史书记述兵数，富强冠诸镇为比较评价，不作为已核财政排行榜。')
add('liu_avoids_advice_and_relief_background','史书记刘知远预料晋契丹失和有危险，却未劝谏，也没有拦截契丹或援京的意图',22,'晋主与契丹','入援之志。',[('知远','未劝谏晋主，也未计划截击或援京')],when='契丹入大梁之前（947年条下追述），具体月日未载',year=None,place='河东与后晋朝廷',note='知其必危及无援意为史家判断，不补其私人内心原话或未知秘密计划。')
add('liu_guards_hedong_borders','刘知远得知契丹进入大梁后，分兵守河东四境防备侵袭',22,'及闻契丹','以防侵轶。',[('知远','分兵防守河东边境')],when=t+'，得知契丹入京后',place='河东四境',note='不补每路防区、兵数和现代边界。')
add('wang_jun_delivers_three_memorials','刘知远派王峻奉三表赴契丹：祝贺入京、解释暂不离镇，并请求撤军以便贡路通行',22,'遣客将安阳王峻','可以入贡。',[('知远','派王峻递交三份表章'),('王峻','以客将身份出使递交三表'),('契丹主','收到三份表章')],when='947年初，通鉴正月条下未标日，旧本纪系二月',place='太原至大梁',note='夷夏杂居与城中忧惧是表中所陈理由，贡路需待撤军为提出的条件，不写已撤回或贡物已运到。')
sup('wang_jun_delivers_three_memorials',22,jh,'是月，帝遣牙將王峻奉表於契丹','《旧五代史》汉高祖纪在二月条下记刘知远派牙将王峻奉表。','帝在该纪指刘知远；不同书记月分别存，不把主书正月条下排列当确定出使月。',relation='adds',field='time_original')
add('liu_jiu_deployment_in_memorial','刘知远在表中称契丹将刘九从土门进入南川，太原城中忧惧，要求召还其军',22,'值契丹将刘九','可以入贡。',[('知远','在表中陈述契丹军威胁并请求撤军'),('刘九','在表中被记为率军屯南川')],when='947年初，刘知远派王峻奉表时',place='土门至南川',note='所陈部署是表中信息，未由独立军事报告确证；未载召军结果，不新增已撤兵事件。')
add('khitan_honors_liu_with_child_address_staff','耶律德光褒奖刘知远，在姓名前加儿字，并赐木拐作为礼遇',22,'契丹主赐诏','仍赐以木柺。',[('契丹主','褒奖、加儿称并赐木拐'),('知远','获得契丹礼遇')],when='947年初，王峻出使时',place='契丹朝廷至太原',note='儿字是政治礼辞，不建立亲生父子或收养关系。木拐为优礼大臣的器物，主书以伟王得杖作礼制比较，不据此另录一次未知年月赐杖。')
sup('khitan_honors_liu_with_child_address_staff',22,jh,'契丹主賜詔褒美，呼帝為兒，又賜木拐一。','《旧五代史》也记呼刘知远为儿、赐木拐一件。','贺表和礼遇同属出使过程，旧纪以二月记，不造真实父子。')
sup('khitan_honors_liu_with_child_address_staff',22,jh,'王峻持持而歸，契丹望之皆避路。','《旧五代史》还称王峻携杖返回，契丹人见到便避路。','底本持持疑有重复字，原字不改；这是同次使程补充，未据此推所有道路均由契丹控制。',relation='adds')
add('bai_wenke_delivers_gifts','刘知远又派北都副留守白文珂献上丝织品和名马',22,'知远又遣','名马，',[('知远','派白文珂献礼'),('白文珂','以北都副留守身份出使献礼'),('契丹主','收到礼物')],when=t+'，王峻出使后条下',place='太原至大梁',note='奇缯名马未列数量，不补贡物价格，白文珂沿已有代州刺史主体按仕历复用。')
add('khitan_questions_liu_waiting','白文珂回太原时，耶律德光让他传话，责问刘知远为何不事南北两朝、仍观望',22,'契丹主知','所俟邪？”',[('契丹主','通过使者责问刘知远观望'),('白文珂','返程时被要求传话'),('知远','成为责问对象')],when=t+'，白文珂返程时',place='大梁至太原',note='南北不事为耶律德光指责，与已奉表献礼并列，不当刘知远完全没有外交联系。')
add('guo_warns_liu_khitan_resentment','郭威向刘知远报告契丹怨恨，并转述王峻认为契丹失民心、无法久占中原',22,'蕃汉孔目官郭威','中国。”',[('郭威','以蕃汉孔目官身份提出警告'),('知远','听取警告'),('王峻','其判断被郭威转述')],when=t+'，使者返回后',place='太原',note='必不能久有为王峻判断的转述，不当客观定时预测；不写王峻当场与郭刘同时在场。')
add('liu_waits_for_khitan_retreat','有人劝刘知远出兵，他认为契丹新收晋军、占据京城，应等其取财北归再行动',22,'或劝知远',None,[('知远','拒绝轻动，决定等待契丹退兵机会')],when=t+'，各方劝进军时',place='太原',note='数目十万、货财足将北去和冰雪消难久留为刘的分析，不能写已经退兵或此时已发起进军。劝者未名。')
add('zhang_congen_consults_liu_about_khitan_visit','张从恩因昭义接近怀州、洛阳，准备赴契丹朝见，先向刘知远询问',23,'昭义节度使','谋于知远。',[('张从恩','准备赴契丹朝见并遣使询问'),('知远','收到询问')],when=t,place='昭义军、河东至大梁（计划行程）',note='地迫为地理形势，欲为计划；未到段末遂行前不写已经出发。')
add('liu_encourages_zhang_go_first','刘知远劝张从恩先赴契丹，称自己将随后去，张从恩相信了',23,'知远曰：','以为然。',[('知远','劝张先行并表示会随后去'),('张从恩','接受建议')],when=t+'，收到回话时',place='河东至昭义军',note='刘此表态与此前观望并列，未写他实际履行随后朝见，也未断言此句必是设计陷害。')
add('gao_fang_advises_loyalty_ignored','高防以张从恩是晋室亲属为由劝他守臣节，张没有听从',23,'判官高防','从恩不从。',[('高防','以昭义判官身份劝守晋臣之节'),('张从恩','不接受劝谏')],when=t,place='昭义军',note='晋室懿亲是高防陈述的身份，具体与皇室亲等未载，不创建血缘端点。')
sup('gao_fang_advises_loyalty_ignored',23,sn,'及契丹入汴，從恩欲降，從事高防諫曰：「公晉室之親，宜盡臣節。」從恩不聽，乃棄城而去。','《宋史》也记高防劝张从恩守晋臣之节，未被采纳，张弃城而去。','宋史以欲降描述意图，主书欲入朝；两种叙述并列，未提前录该传后续王守恩夺财和归汉。')
add('zhang_leaves_zhao_wang_gao_in_charge','张从恩令赵行迁主持留后事务，让王守恩暂任巡检使、高防协助，随后出发',23,'左骁卫大将军','遂行。',[('张从恩','安排留守后出发'),('赵行迁','以副使身份主持留后事务'),('王守恩','以左骁卫大将军身份暂代巡检'),('高防','留军中协助')],when=t,place='上党至大梁',note='留下协助和暂派职务不当永久任官；时在上党不是所有人籍贯，不补确切抵京日。')
relationship('王建立','王守恩','父亲',23,span(23,'守恩，',None),'原文明确王守恩为王建立之子，父亲方向由建立指向守恩。')
relationship('王守恩','张从恩','姻亲',23,span(23,'左骁卫大将军','与从恩姻家，'),'姻家只证姻亲，具体双方、性别配偶和亲等未知，保留对称关系，不擅转父婿或姐夫。')
reviews={20:'缺字刘由旧刘昫传开运判三司、契丹不改职对应；原字保留，不添加缺字为检索别名。三十万本人说辞、征借范围及未赏军蓄库、欲北运与民怨分记。',21:'初追述相猜与实际权力、募兵、阳城散卒归、河东兵力状况；北面任命和吐谷浑夺财复用原事件追加证据，避免重复。未知动作年留空，五万不当已核兵籍。',22:'此前无谏援是史家评述；守境、王使三表及刘九部署、礼遇、白献与传责、郭转王评、刘等待分记。旧本纪王使系二月，主书正月条下未标日期，时间并列；儿不作血缘，预判不作已退兵。',23:'刘回话未当已赴契丹；高谏未名皇亲亲等；留后巡检协助与出行分别，父子明文及姻亲对称不猜婚配。宋仅补高谏张离，后续夺财归汉不提前。'}
assert not (P/'publication.json').exists()
for n in range(20,24):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(20,24)],next_paragraph=Q[24]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原25—28行连续四段，累计23/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(20,24)],source_issues_review='缺字刘昫按官职同书外证识别，原TXT不改；王峻使程月序主正月条下与旧二月并列，持持疑重复字保留；直接宋补高防劝谏，未来史事留后段。',plain_language_review='首次逐条检查白话、身份时间、关系方向、原文及引用；未把请求承诺分析当实际执行，旧事件复用不重建。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
