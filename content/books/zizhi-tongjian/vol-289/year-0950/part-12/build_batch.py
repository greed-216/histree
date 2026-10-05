# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 73–76."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,84))
COMMIT='4036ee803f0476e08112a5a3782bf4ceb782f41e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-103-december-expedition','xinwudaishi-066-peng-plan']:
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
main_sources = ['tongjian-289-950-changsha-falls','tongjian-289-950-chu-yun-north']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p073-p076',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-289-950-changsha-falls':'卷289·乾祐三年·长沙陷落','tongjian-289-950-chu-yun-north':'卷289·乾祐三年·楚王更替与迎嗣','xinwudaishi-018-xuzhou-garrison':'卷18·刘赟传·留守徐州','xinwudaishi-066-ma-xiguang-death':'卷66·楚世家·马希广被杀'}
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
lines = (ROOT / 'resources/derived/tongjian/289.txt').read_text().splitlines()
for n in range(73, 77):
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
    labels={'tongjian-289-950-changsha-falls':'卷289·乾祐三年·长沙陷落','tongjian-289-950-chu-yun-north':'卷289·乾祐三年·楚王更替与迎嗣','xinwudaishi-018-xuzhou-garrison':'卷18·刘赟传·留守徐州','xinwudaishi-066-ma-xiguang-death':'卷66·楚世家·马希广被杀'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十一月至十二月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_12_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=950, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='950年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_289_0950_' + code
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
        edge = 'participation_zztj_289_0950_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_289_0950_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'太后':'李氏（刘知远妻）','希广':'马希广','希萼':'马希萼','希崇':'马希崇','硃进忠':'朱进忠','张晖':'张晖（马希广将）','赟':'刘赟','光赞':'马光赞'})
NEW_ALIASES={'何敬真':[],'雷晖':['雷暉'],'吴宏':['吳宏'],'李弘节':['李弘節'],'唐昭胤':[],'刘宾':['劉賓'],'巩延美':['鞏延美','巩庭美','鞏庭美','巩廷美','鞏廷美'],'杨温':['楊溫']}
NEW_DESCRIPTIONS={
'何敬真':'武陵人，朗州步军指挥使。950年率部族兵攻破韩礼在杨柳桥的防线；马希萼入长沙后任他为朗州牙内都指挥使，率兵戍守。生卒年未载。',
'雷晖':'朗州人。950年穿潭州士兵衣服潜入韩礼营寨，挥剑攻击未中，却引起军中骚乱，何敬真乘乱进攻。生卒年未载。',
'吴宏':'楚国步军指挥使。950年长沙被围时出清泰门作战，城陷后向马希萼表示愿死，马希萼没有杀他。生卒年未载。',
'李弘节':'楚国掌书记李弘皋的弟弟。950年长沙陷落后被马希萼一方捕获囚禁，随后与李弘皋等遭残酷杀害。生年未载。',
'唐昭胤':'楚国都军判官。950年长沙陷落后被马希萼一方捕获囚禁，随后与李弘皋等遭残酷杀害。生年未载。',
'刘宾':'楚国内外巡检侍卫指挥使。950年十二月丙午，奉马希萼命禁止长沙的焚烧与劫掠。与同名人物尚无同人证据，生卒年未载。',
'巩延美':'刘赟的右都押牙。950年刘赟离开徐州西行迎立时，与杨温留守徐州。《新五代史》刘赟传写作巩庭美，同职同伴及同一留守场景对应；生卒年本批未录。',
'杨温':'刘赟的元从都教练使。950年刘赟离开徐州西行迎立时，与巩延美留守徐州。生卒年本批未录。'}
NEW_DEATH_YEARS={'李弘节':950,'唐昭胤':950}
chu='xinwudaishi-066-peng-plan';death='xinwudaishi-066-ma-xiguang-death';xuzhou='xinwudaishi-018-xuzhou-garrison';dec='jiuwudaishi-103-december-expedition'
add('he_jingzhen_yangliu_deployment','何敬真率三千部族兵在杨柳桥列阵',73,'甲辰，','陈于杨柳桥，',[('何敬真','以朗州步军指挥使身份率三千部族兵列阵')],when='950年十二月甲辰',place='杨柳桥',note='武陵为籍贯、杨柳桥为阵地；原文蛮为史书称呼，展示采用部族兵，不补具体族属。')
add('he_observes_han_disorder','何敬真看到韩礼营中旌旗混乱，认为容易击败',73,'敬真望','击之易破也。”',[('何敬真','观察旗帜混乱并认为对方已恐惧'),('韩礼','营寨旗帜混乱，受到敌军观察')],when='950年十二月甲辰',place='杨柳桥韩礼营寨',note='恐惧与易破是何敬真的判断，不当已经完成战果；韩礼沿前批主体。')
add('lei_hui_infiltrates_han','雷晖伪装潭州士兵潜入韩礼营寨，袭击未中',73,'朗人雷晖','军中惊扰。',[('雷晖','穿潭州士兵衣服潜入，挥剑攻击韩礼未中'),('韩礼','遇袭未中，所部惊乱')],when='950年十二月甲辰',place='韩礼营寨',note='手剑解释持剑攻击，不写空手；此次不中与随后韩礼受伤死亡分开，不能写雷晖当场杀韩礼。')
add('han_li_defeat_death','何敬真乘乱击溃韩礼所部，韩礼伤后回家去世',73,'敬真等乘其乱','至家而卒。',[('何敬真','乘营中骚乱进攻，击溃韩礼所部'),('韩礼','受伤逃离，回家后去世')],when='950年十二月甲辰交战，韩礼回家去世确日未单列',place='杨柳桥及韩礼家中',note='受伤逃回家后死，不推在战场当场战死；原文等不补其他将领姓名。')
claim('person',people['韩礼'],'death_year','韩礼于950年杨柳桥兵败受伤，回家后去世。',73,'礼被创走，至家而卒。','战斗日甲辰与实际去世日可能有间隔，不强定同日。')
add('changsha_water_land_attack','朗州军从水陆两路急攻长沙',73,'于是朗兵水陆','急攻长沙，',[],when='950年十二月甲辰韩礼败后',place='长沙',note='军队行动尚未点出本次总指挥，未把所有作战均写马希萼亲自冲锋；水陆不补路线坐标。')
add('wu_hong_qingtai_sortie','吴宏表示愿以死报国，率兵出清泰门作战失利',73,'步军指挥使吴宏','战不利。',[('吴宏','表示愿以死报国，率兵出清泰门，作战失利'),('杨涤','与吴宏互相表示愿以死报国，并各自出兵')],when='950年十二月甲辰',place='清泰门',note='两将对话共同引用；此事件主记吴宏一路，不把失利当战死，杨涤另路另记。')
add('yang_di_changle_fighting','杨涤出长乐门作战，敌军稍退而友军未救援',73,'涤出长乐，','退就食。',[('杨涤','出长乐门自辰至午作战，疲饿后退下吃饭'),('许可琼','按兵不救杨涤'),('刘彦瑫','按兵不救杨涤')],when='950年十二月甲辰，自辰至午作战',place='长乐门',description='杨涤出长乐门，自辰时战至午时，朗州兵稍退。许可琼、刘彦瑫按兵不救；杨涤所部疲饿，退下吃饭。',note='少却为稍退，不写已完全击溃；古时段保留，不换算分钟。按兵不救不等于本句二人都已公开投降。')
sup('yang_di_changle_fighting',73,chu,'希萼攻長樂門，牙將吳宏、楊滌戰于門中，希萼少衄，已而許可瓊奔于希萼，宏、滌聞之皆潰。','《新五代史》将吴宏、杨涤合记为长乐门抵抗者，马希萼稍受挫后许可琼投向他，两将所部溃败。','《通鉴》分吴宏出清泰门、杨涤出长乐，并记杨先退就食；两书作战地点和败退细节分别保留，不混改吴宏地点。',relation='conflicts')
add('peng_northeast_fighting','彭师暠在长沙城东北角迎战',73,'彭师暠战','城东北隅。',[('彭师暠','在城东北角作战')],when='950年十二月甲辰',place='长沙城东北角',note='未载兵数、敌军将领及本路胜败，不从此前三千请求套兵数。')
add('xu_surrenders_changsha_falls','长沙城东起火，许可琼举军投降马希萼，长沙陷落',73,'蛮兵自城东纵火，','长沙遂陷。',[('许可琼','受求援后举全军投降马希萼'),('希萼','接受许可琼投降，所部攻陷长沙')],when='950年十二月甲辰',place='长沙',description='部族兵从城东放火，城上守军请求许可琼救城；许可琼却率全军投降马希萼，长沙随即陷落。',note='求援与投降是实际行动，内应承诺另有前批事件。原文未给投降兵数，不套战舰数量作人数。')
add('changsha_three_day_plunder','长沙陷落后，朗州军与部族兵劫掠杀人焚屋三日',73,'朗兵及蛮兵大掠','皆入蛮落。',[],when='950年十二月甲辰陷城后持续三日',place='长沙',description='长沙陷落后，朗州军与部族兵劫掠三日，杀害官吏和平民、焚烧房舍；马殷以来建造的宫室被烧毁，积存宝物被带入部族聚落。',note='武穆王指马殷，原文皆是叙述概括，不计算毁屋和遇难人数；三日不自行反算结束公历日。')
add('li_yanwen_rescue_flight','李彦温救城未成，与刘彦瑫率兵经袁州逃往南唐',73,'李彦温望见','遂奔唐。',[('李彦温','从驼口救长沙，攻清泰门未成，率千余人护送马希广诸子等逃往南唐'),('刘彦瑫','率千余人与李彦温护送马希广诸子等逃往南唐')],when='950年十二月甲辰陷城后的救援与逃亡，抵南唐日未载',place='驼口、长沙清泰门、袁州、南唐',description='李彦温见城中起火，自驼口率兵救援，攻清泰门不成。李彦温、刘彦瑫各率千余人，护送马希广诸子等经袁州逃往南唐。',note='奉文昭王通常关联已故马希范，本句未说明所奉具体对象，保留原文待核，不写马希范活着同行。各千余不是合计千余，袁州与最终投唐分开。')
add('zhang_hui_surrenders_ma_xie','张晖投降马希萼',73,'张晖降于希萼。','张晖降于希萼。',[('张晖','长沙陷后投降马希萼'),('希萼','接受张晖投降')],when='950年十二月长沙陷落后，具体日未载',place='长沙',note='复用马希广将张晖，未与博州守将或后晋使者合并；不据投降造正式新任官职。')
add('ma_xichong_urges_xie_rule','马希崇率将吏向马希萼劝进',73,'左司马希崇','劝进。',[('希崇','以左司马身份率将吏劝进'),('希萼','受到将吏劝进')],when='950年十二月长沙陷落后',place='长沙',note='劝进为请求接受统治地位，丁未自称楚王另录，不写此次已经正式获后汉册封。')
add('ma_xie_spares_wu_peng','吴宏和彭师暠请死，马希萼没有杀他们',73,'吴宏战，',None,[('吴宏','战后表示死而无愧先王'),('彭师暠','投下长矛，大声请死'),('希萼','感叹二人坚毅，没有杀他们')],when='950年十二月长沙陷落后',place='长沙',description='吴宏作战后衣袖染血，向马希萼表示被许可琼所误，虽死无愧先王；彭师暠投下长矛大声请死。马希萼感叹二人坚毅，没有杀他们。',note='不杀对象是本句吴宏彭师暠，不推所有俘虏免死；所误为吴宏话语，不作全部败因的独立证明。')
add('ma_xie_enters_government','马希崇于乙巳迎马希萼入府处理政务',74,'乙巳，','入府视事，',[('希崇','迎马希萼进入府中'),('希萼','入府处理政务')],when='950年十二月乙巳',place='长沙府',note='视事是开始处理事务，不是观光查看；闭城与捕获另录。')
add('ma_xie_captures_opponents','马希萼一方关闭城门，捕获马希广及李弘皋等',74,'闭城，','皆获之。',[('希萼','一方闭城抓捕马希广及旧部'),('希广','被捕获'),('李弘皋','以掌书记身份被捕获'),('李弘节','与兄李弘皋一同被捕'),('唐昭胤','以都军判官身份被捕获'),('邓懿文','被捕获'),('杨涤','被捕获')],when='950年十二月乙巳',place='长沙',note='分捕为分派抓捕，不写马希萼本人亲手抓每人；李弘节为李弘皋弟。')
relationship('李弘皋','李弘节','兄长',74,'掌书记李弘皋、弟弘节','李弘皋是李弘节兄长，端点按本站A是B的关系约定；不据此补父母。')
add('ma_brothers_dispute_imprisonment','马希萼质问继位长幼，马希广答被拥立，随后被囚',74,'希萼谓希广曰：','希萼皆囚之。',[('希萼','以父兄遗业和长幼顺序质问，囚禁马希广及被捕者'),('希广','回答自己被将吏拥立、朝廷任命')],when='950年十二月乙巳',place='长沙',note='回答是马希广申辩，囚禁不是已处死；父兄身份不据此次话语重复建关系。')
sup('ma_xie_captures_opponents',74,death,'希廣率妻子匿于慈堂。明日擒之。','《新五代史》补记马希广携妻子藏于慈堂，次日被捕。','妻子在此可含妻与子女，原文未具名不造配偶；明日为相对日，与通鉴乙巳捕获的顺序相接，不编造公历日。',relation='adds')
add('liu_bin_forbids_arson','马希萼于丙午命刘宾禁止焚烧和劫掠',74,'丙午，','禁止焚掠。',[('希萼','命刘宾禁止焚烧和劫掠'),('刘宾','以内外巡检侍卫指挥使身份受命止焚掠')],when='950年十二月丙午',place='长沙',note='命令不等于即时完全停止，本句未给实施效果；不把刘宾的联合职称拆成两位人。')
add('ma_xie_claims_titles','马希萼于丁未自称楚王及天策上将军等职',74,'丁未，','节度使、楚王。',[('希萼','自称楚王、天策上将军及四军节度使')],when='950年十二月丁未',place='长沙',description='马希萼自称天策上将军、武安、武平、静江、宁远等军节度使和楚王。',note='自称与中央册封区分，不写全部所称辖地已实际控制；未把楚王写成皇帝。')
add('ma_xichong_deputy_appointment','马希萼任马希崇为节度副使并负责府中事务',74,'以希崇','判官府事，',[('希萼','任命马希崇为节度副使、判官府事'),('希崇','受任节度副使并负责府中事务')],when='950年十二月丁未自称楚王后条下',place='长沙',note='判官府事按负责府务解释，不改为近现代司法判官，未给另行任命日。')
add('ma_xie_installs_lang_officials','马希萼将湖南重要职务交给朗州人',74,'湖南要职，','悉以朗人为之。',[('希萼','将湖南重要职务交给朗州人')],when='950年十二月丁未后的官职安排',place='湖南',note='未具名名单不虚构具体官职任命；悉为史书概括，不变成现代人事统计。')
add('ma_xie_kills_li_yang_tang','李弘皋、李弘节、唐昭胤、杨涤遭肢解杀害，邓懿文被斩首',74,'脔食李弘皋','于市。',[('希萼','一方杀害被捕的马希广旧部'),('李弘皋','遭肢解杀害'),('李弘节','遭肢解杀害'),('唐昭胤','遭肢解杀害'),('杨涤','遭肢解杀害'),('邓懿文','在市中被斩首')],when='950年十二月丁未自称楚王及任职条下，具体处决日未单列',place='长沙',description='马希萼一方肢解杀害李弘皋、李弘节、唐昭胤、杨涤，史书还记有食肉行为；邓懿文在市中被斩首。',note='脔食的杀害与食肉含义保留，没有执行者姓名不补；不扩写血腥细节，不把相邻丁未强作每人确切死日。')
for name in ['李弘皋','李弘节','唐昭胤','杨涤','邓懿文']:
 claim('person',people[name],'death_year',name+'于950年长沙陷落后被马希萼一方杀害。',74,'脔食李弘皋、弘节、唐昭胤、杨涤，斩邓懿文于市。','年份据十二月连续叙事，执行方式各异，确日未单列；复用人物不覆盖旧介绍。')
add('ma_xie_considers_sparing_guang','马希萼于戊申问能否留马希广性命，朱进忠反对',74,'戊申，希萼谓将吏曰：','他日必悔之。”',[('希萼','认为马希广受左右影响，问能否让他活着'),('希广','成为讨论是否留命的对象'),('硃进忠','以一国不容二主为由反对留命')],when='950年十二月戊申',place='长沙',note='三年血战是朱进忠发言，不据此新建三年连续战事；尝为希广所答原文答疑有转录问题，未在展示中猜成确定鞭打经历，留待版本核对。')
sup('ma_xie_considers_sparing_guang',74,death,'希萼見之惻然曰：「此鈍夫也，豈能為惡？左右惑之爾。」顧其下曰：「吾欲活之，如何？」其下皆不對，遂縊死之。','《新五代史》也记马希萼认为马希广受左右影响，询问是否留他活命，部下不答，随后将他绞死。','新史未写朱进忠此处反对，也未列戊申；补记死亡方式，不把反对话语强加进新史。',relation='adds')
add('ma_guang_ordered_death','马希萼于戊申命令处死马希广，马希广临刑仍诵佛经',74,'戊申，赐希广死。','犹诵佛书，',[('希萼','命令处死马希广'),('希广','被命令处死，临刑仍诵佛经')],when='950年十二月戊申',place='长沙',note='通鉴赐死未给方式；新史绞死在独立补证中，不改主书引文。')
claim('person',people['马希广'],'death_year','马希广于950年十二月戊申被马希萼命令处死。',74,'戊申，赐希广死。','新史补绞死，主书纪日原样保留，不换算公历月日。')
add('peng_buries_ma_guang','彭师暠将马希广葬于浏阳门外',74,'彭师暠葬之',None,[('彭师暠','将马希广安葬于浏阳门外'),('希广','死后被葬于浏阳门外')],when='950年十二月戊申马希广死后，具体葬日未单列',place='长沙浏阳门外',note='葬地沿原名，不推现代墓址；彭未随马处死，与前段马希萼不杀彭相符。')
add('yun_leaves_xuzhou_garrison','刘赟留巩延美、杨温守徐州，随冯道等西行',75,'武宁节度使赟','与冯道等西来，',[('赟','留二将守徐州，随迎接使者西行'),('巩延美','以右都押牙身份留守徐州'),('杨温','以元从都教练使身份留守徐州'),('冯道','随刘赟西行奉迎')],when='950年奉迎诰下后、十二月抵宋州前，离开徐州日未载',place='徐州至西行途中',note='离开徐州与下一段至宋州分开，仍未实际到京即位。')
sup('yun_leaves_xuzhou_garrison',75,xuzhou,'初，贇自徐州入也，以都押牙鞏庭美、教練使楊溫守徐州。','《新五代史》也记刘赟离开徐州时，留巩庭美、杨温守城。','通鉴巩延美、新史巩庭美同职同伴同一留守场景对应，复用同一新主体并保留两种字形。此段后文951年城陷及被杀未提前纳入950事件。')
add('yun_royal_guard_on_road','刘赟西行时使用王者仪仗，随从呼万岁',75,'在道仗卫，','左右呼万岁。',[('赟','西行途中使用王者仪仗，受随从呼万岁')],when='950年刘赟赴京途中，具体日未载',place='徐州向京师途中',note='礼仪待遇与真正登基区分，左右未具名不建人物。')
add('guo_sliding_yun_comfort','郭威在滑州停留数日，刘赟派人慰劳军队',75,'郭威至滑州。','赟遣使慰劳。',[('郭威','到滑州停留数日'),('赟','派使者慰劳郭威军队')],when='950年十二月甲午北征出发后至己酉离滑州前',place='滑州',note='数日不具体化，慰劳不是刘赟亲自来营；使者无姓名不补。')
add('guo_generals_reject_yun','郭威诸将不向刘赟使者行礼，私下担忧刘氏复立报复',75,'诸将受命之际，','尚有种乎！”',[],when='950年十二月滑州慰劳时',place='滑州郭威军中',description='郭威诸将收到刘赟慰劳之命时互相看着，不肯行拜礼，私下说曾攻破劫掠京城，担心刘氏再立后自己和后代不能保全。',note='诸将无名单，不把每名已有将领都设参与；担心灭族是其话语，不写刘赟已下报复令。')
add('guo_leaves_hua_chan','郭威于己酉听到将领议论，离滑州赶往澶州',75,'己酉，','趣澶州。',[('郭威','听到将领议论后率军赶往澶州')],when='950年十二月己酉',place='滑州至澶州',note='趣为赶往，壬子抵达另段，不写己酉已到澶州。')
add('su_yugui_sent_song','苏禹珪于辛亥被派往宋州迎接刘赟',75,'辛亥，',None,[('苏禹珪','被派到宋州迎接嗣君刘赟'),('赟','成为宋州迎接对象')],when='950年十二月辛亥',place='宋州',note='本句省略派遣者，不指定郭威亲发命令；如宋州为前往，不写已经迎回。')
sup('su_yugui_sent_song',75,dec,'辛亥，遣宰相蘇禹珪及朝臣十員，往宋州迎奉嗣君。','《旧五代史》也记辛亥派苏禹珪与十名朝臣到宋州迎嗣君。','同日同事，旧本纪补十名朝臣，无具名名单不建十位人物。')
add('ma_guangzan_wuping_deputy','马希萼任儿子马光赞为武平留后',76,'楚王希萼','为武平留后，',[('希萼','任儿子马光赞为武平留后'),('光赞','受任武平留后')],when='950年十二月马希萼称楚王后，具体任命日未载',place='武平',note='复用前批父子关系与已留守朗州的儿子，不据新职创另人；留后是代理节度职务。')
add('he_jingzhen_lang_guard','马希萼任命何敬真为朗州牙内都指挥使，派兵戍守',76,'以何敬真','将兵戍之。',[('希萼','任命何敬真并令率兵守朗州'),('何敬真','受任朗州牙内都指挥使，率兵戍守')],when='950年十二月马希萼称楚王后，具体任命日未载',place='朗州',note='之指朗州语境，牙内职掌不译现代军衔，兵数未载。')
add('tuoba_heng_refuses_ma_xie','马希萼想任用拓跋恒，拓跋恒称病不肯起身',76,'希萼召拓跋恒',None,[('希萼','召拓跋恒，想任用他'),('拓跋恒','称病不肯起身接受任用')],when='950年十二月马希萼称楚王后，具体召见日未载',place='楚国',note='称疾不诊断实际疾病；欲用没有明确拟官，不写已经正式任命。')
reviews={73:'甲辰杨柳桥列阵、观察、雷袭未中、韩败伤归死、各路出战与友军未救、许可琼降与陷城、劫掠三日、救城失败逃唐、张晖降、希崇劝进、吴彭不杀分录。吴宏清泰门与新史长乐门异说保留。奉文昭王具体对象待核，不把已故马希范当活人同行。',74:'乙巳入府捕囚、丙午止焚命令、丁未自称及任职、诸臣遭害、戊申留命讨论与赐死、葬地分录。杀害方式忠于原文不扩写细节；朱此前所答疑转录字不猜鞭打，三年血战保留其发言。李弘皋兄长有弟明确证据。',75:'留二将徐州、西行仪仗、滑州慰劳、诸将不拜及恐惧、己酉往澶、辛亥派苏迎嗣分别记；未即位。巩延美与新庭美同场人物对应、别名保留，951年结局未提前纳入。',76:'马光赞武平留后、何敬真朗州牙内及戍守、拓跋恒称病拒用分录。沿稳定父子主体，不填未载任用职务与具体病因。'}
assert not (P/'publication.json').exists()
for n in range(73,77):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(73,77)],next_paragraph=Q[77]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原78—81行连续四段；发布后首76/83正文已录，余7段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(73,77)],source_issues_review='吴宏战斗城门主新不同并列，文昭王所奉对象及朱进忠此前所答字形待核；不生成无证据身份或经历。新史补马希广藏慈堂及绞死，巩姓名对应保留原字，未知日期不强套。旧史卷133马希广希萼传标全篇佚，其附引五代史补不作为独立正文确证。纸本及转录异文待核。',plain_language_review='首次逐条核对标题、正文、角色、关系与事实说明的白话和主体；杀害、计划、命令、评价、仪仗与即位各自区分。原文原字保留，未解问题明示，不安排固定二次文案审阅。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
