# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 86–92."""
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
COMMIT='7ec68fbe613fa4f3a671f8b2f4b2181d1c6ec040'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['jiuwudaishi-099-heyang-april']:
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
main_sources = ['tongjian-286-947-liao-succession-april']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p086-p092',
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
for n in range(86, 93):
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
        citation = f'卷286·天福十二年（947年四月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_15_{len(B["claims"])+1:04d}'
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
def existing(code,key,n,quote,text,note):
 matches=[x for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for x in json.loads(f.read_text())['events'] if x['key']==key]
 assert matches,key
 B['events'].append(dict(matches[0],status='draft'));reused.add(key);used.setdefault(n,[]).append(key);E[code]=key
 claim('event',key,'description',text,n,quote,note)
ALIASES.update({'帝':'刘知远','契丹主':'耶律德光','兀欲':'耶律阮','太后':'述律平','张廷翰':'张廷翰（冀州）'})
NEW_ALIASES={'叶仁鲁':['葉仁魯'],'何行通':[],'张廷翰（冀州）':['張廷翰（冀州）']}
NEW_DEATH_YEARS={'何行通':947}
NEW_DESCRIPTIONS={
'叶仁鲁':'刘知远的亲将。947年率三千步骑救援承天军，在契丹兵外出劫掠时将其击败，四月丁丑收复承天军。生卒年尚未录入。',
'何行通':'契丹所任冀州刺史。947年被杀，《资治通鉴》《宋史》记冀州人杀他，《旧五代史》后文写张廷翰杀他，杀人主体存在不同记载。生年未载。',
'张廷翰（冀州）':'冀州信都人，任冀州牢城指挥使。947年何行通被杀后，被推知州事；《资治通鉴》称他为符习之甥。与《宋史》另一位泽州陵川人张廷翰分别识别，生卒年尚未录入。'}
j='jiuwudaishi-099-heyang-april';ls='liaoshi-004-taizong-death';ss='songshi-271-zhang-tinghan-jizhou';old='jiuwudaishi-101-zhang-tinghan-appointment';t='947年四月，具体日未载'
add('khitan_falls_ill_returning','耶律德光北归到临城患病，至栾城病情加重，用冰降热',86,'契丹主至临城，','且啖之。',[('契丹主','北归患病加重，用冰敷身并食冰')],when='947年四月丙子之前，具体起病日未载',place='临城至栾城',note='苦热与用冰按史书记述，不推现代疾病诊断，也不把病症直接当已核实死亡原因。')
sup('khitan_falls_ill_returning',86,ls,'戊辰，次高邑，不豫。','《辽史》记四月戊辰到高邑时身体不适，与主书临城起病的地点写法不同。','不豫为生病，不据地名异说强排同日两个地点。',relation='conflicts')
add('khitan_taizong_dies','耶律德光到杀胡林后去世',86,'丙子，','至杀胡林而卒。',[('契丹主','北归途中到杀胡林去世')],when='947年四月丙子；《辽史》作丁丑',place='杀胡林（栾城附近）',note='主书丙子与辽史丁丑并列，未自行换算公历或择一消除异说。栾城位置沿本段连续记述。')
sup('khitan_taizong_dies',86,j,'丙子，契丹主耶律德光卒於鎮之欒城。','《旧五代史》同记四月丙子耶律德光在栾城去世。','栾城与杀胡林为两书地名层级写法，未据此认定两次死亡。')
sup('khitan_taizong_dies',86,ls,'丁丑，崩于欒城，年四十六。','《辽史》记耶律德光在四月丁丑于栾城去世，年四十六。','与主书及旧五代史丙子不同；年龄只按本书记数，不反算确定出生年。',relation='conflicts')
add('khitan_preserves_body_transports_north','契丹人用盐处理耶律德光遗体后北运，晋人称其为帝羓',86,'国人剖其腹，',None,[],when='947年四月去世后，具体处理与启运日未载',place='杀胡林至契丹方向',note='帝羓是晋人的称呼；盐数斗为史书记数，不折算现代重量。')
add('zhao_refuses_return_enters_hengzhou','赵延寿怨耶律德光失约，表示不再北归，率兵先入恒州',87,'赵延寿恨','即日，先引兵入恒州，',[('赵延寿','表示不再北归并先领兵入恒州')],when='947年四月耶律德光死后，具体日未载',place='契丹北归军中至恒州',note='龙沙指北方故地，非当前新建坐标；即日相对本段事件，不另猜具体干支。')
add('zhao_admits_yelu_ruan_forces','耶律阮及契丹南北二王率部入恒州，赵延寿担心失去援兵而接纳',87,'契丹永康王',None,[('兀欲','与南北二王各率部入恒州'),('赵延寿','原想拒入，因恐失援而接纳')],when=t,place='恒州',note='南北二王未名，不把后续同名官号猜为某两个已知人物；欲拒与实际接纳分清。')
add('khitan_generals_support_ruan','契丹诸将密议拥立耶律阮，他登鼓角楼受叔兄拜礼',88,'时契丹诸将','受叔兄拜。',[('兀欲','获诸将密议支持，在鼓角楼受拜')],when='947年四月进入恒州前后，具体日未载',place='恒州鼓角楼',note='叔兄未列姓名，不据此新建任意亲属边；此段受拜与后续正式即位仪式分开。')
add('zhao_claims_southern_authority','赵延寿自称获契丹皇帝遗诏，暂掌南朝军国事务并通告诸道',88,'而延寿不之知，','仍下教布告诸道，',[('赵延寿','自称受遗诏，权知南朝军国事并通告诸道')],when=t,place='恒州至诸道',note='自称受遗诏是赵延寿的声称，不能当作遗诏确已存在；他不知诸将密议支持耶律阮。')
sup('zhao_claims_southern_authority',88,j,'趙延壽於鎮州自稱權知國事。','《旧五代史》同记赵延寿在镇州自称权知国事。','恒州、镇州沿史书当时同城称呼，主书南朝军国事与补书省称分别保留。')
add('ruan_resents_equal_supply','赵延寿将耶律阮与其他将领同等供给，耶律阮对此不满',88,'所以供给','兀欲衔之。',[('赵延寿','将耶律阮与诸将同等供给'),('兀欲','对同等供给心怀不满')],when=t,place='恒州',note='衔之为史书动机解释，不推具体粮额或本人未载的公开争吵。')
add('ruan_controls_hengzhou_keys_stores','耶律阮自行控制恒州城门钥匙和仓库出纳，拒绝赵延寿索取',88,'恒州诸门',None,[('兀欲','控制城门和仓库，拒交赵延寿'),('赵延寿','派人索取控制权未获准')],when=t,place='恒州',note='管钥与出纳是城门、仓库控制，不等同于已经正式统治全部中原。')
add('shulv_postpones_burial','耶律德光灵柩到契丹，述律太后称待各部安定后再安葬',89,'契丹主丧至国，',None,[('太后','未哭，表示待各部安定才安葬儿子')],when='947年耶律德光灵柩回国时，具体到达日未载',place='契丹，具体地点未载',note='发言表明延后安葬意向，不据此写成永久未葬或推测未哭的心理诊断。')
existing('liu_chengtian_garrison_review','event_zztj_286_0947_liu_leaves_chengtian_garrison_returns',90,span(90,'帝之自寿阳还也，','留兵千人戍承天军。'),'刘知远从寿阳返回时，留一千兵守承天军。','复用前批二月出行后留兵返回事件，这里补人数；追叙不重建第二次出行或四月留兵。')
add('khitan_raids_chengtian','承天军守兵闻契丹北归未作防备，遭袭溃散，契丹焚毁市邑',90,'戍兵闻契丹北还，','一日狼烟百馀举。',[],when='947年四月丁丑收复之前，具体袭击日未载',place='承天军',note='一日狼烟百余举为史书景象记数，不转成百余村被烧或百余次战斗。')
add('liu_sends_ye_relief_chengtian','刘知远判断契丹以袭击张虚势，派叶仁鲁率三千步骑救援',90,'帝曰：','将步骑三千赴之。',[('帝','判断契丹将逃，派三千步骑救援'),('叶仁鲁','受命率三千步骑赴承天军')],when='947年四月袭击之后、丁丑收复之前，具体遣兵日未载',place='后汉军中至承天军',note='虏将遁张虚势是刘知远判断，实际遣援另明；三千是本次救援规模。')
add('ye_recovers_chengtian','叶仁鲁趁契丹外出劫掠击败守军，丁丑收复承天军',90,'会契丹出剽掠，',None,[('叶仁鲁','乘虚破敌并收复承天军')],when='947年四月丁丑（收复日），前期战斗具体日未载',place='承天军',note='丁丑明确复取，乘虚作战可在此之前，不把整个过程压成同一时刻。')
add('jizhou_kills_he_xingtong','冀州人杀死契丹所任刺史何行通',91,'冀州人','杀契丹刺史何行通，',[('何行通','以契丹刺史身份被冀州人杀害')],when=t,place='冀州',note='杀人主体主书记州人，新旧史有差异，本条不强写张廷翰亲自动手。')
sup('jizhou_kills_he_xingtong',91,ss,'契丹入中原，署其黨何行通為刺史，契丹主道殂，州人共殺行通','《宋史》同记何行通为契丹所任刺史，契丹主途中去世后被州人共杀。','该书与主书州人说相近，不认为相同表述已经构成独立事实确证。')
sup('jizhou_kills_he_xingtong',91,old,'時廷翰殺本州刺史何行通，自知州事','《旧五代史》948年六月任官条回顾何行通被张廷翰所杀，张自行知州事。','回顾语不能强定杀人发生在948年六月；杀人主体与主書州人说并列，不消除差异。',relation='conflicts')
add('zhang_tinghan_chosen_jizhou','冀州人推张廷翰暂掌州事',91,'推牢城指挥使',None,[('张廷翰','以牢城指挥使身份获推知州事')],when=t,place='冀州',note='主书称冀州人及符习之甥，暂任知州事与后续正式拜刺史分开；不与泽州陵川同名宋将合并。')
sup('zhang_tinghan_chosen_jizhou',91,ss,'推廷翰知州事','《宋史》也记冀州人推张廷翰知州事。','只补此处推举，传中后续杀参与者、官任和战功未全部提前录在947年。')
claim('person',people['张廷翰（冀州）'],'description','此处张廷翰是冀州信都人。',91,'張廷翰，冀州信都人。','宋史同名另传为泽州陵川人，本主体按冀州牢城及州事行动区别，未合并两人。',source=ss)
relationship('张廷翰','符习','甥',91,span(91,'廷翰，',None),'方向表示张廷翰是符习的甥；保留史书亲属称谓，原文没有交代中间母系人物，不补母亲姓名。')
add('zhao_warned_of_khitan_plot','有人劝赵延寿先动手应对契丹诸大人密谋，赵延寿犹豫未决',92,'或说赵延寿','犹豫不决。',[('赵延寿','获劝先采取行动，仍犹豫不决')],when='947年四月壬午之前，具体日未载',place='恒州',note='说者未名，必有变、汉兵不减万人是劝说者判断和兵数估计，不据此新建已发生政变或核定万人兵数。')
add('zhao_plans_ritual_may_first','赵延寿下令次月朔日在待贤馆受百官贺，规定各官拜礼位置',92,'壬午，','节度使以下拜于阶下。',[('赵延寿','计划五月朔日上事受贺并规定拜礼位置')],when='947年四月壬午（下令）；拟五月朔日行礼',place='恒州待贤馆',note='次月朔日是计划日期，本段后文明确停止，不建立实际完成登位仪式。')
add('li_song_stops_zhao_ritual','李崧以契丹态度不一、事势难测劝阻，赵延寿停止受贺计划',92,'李崧',None,[('李崧','力劝暂不举行受贺礼'),('赵延寿','停止受贺计划')],when='947年四月壬午计划下达后，具体日未载',place='恒州',note='乃止为实际停止这项礼仪计划，不意味着赵延寿已经撤去此前全部自称官号。')
reviews={86:'病症不用现代诊断；丙子与辽丁丑死亡纪日、临城与高邑起病地点分别保留；帝羓为晋人称呼。',87:'赵言不归、先入恒州、纳阮军分录，南北二王未名不猜主体。',88:'诸将密议受拜、赵自称遗诏、同供给不满与城门仓库争夺分录，自称不证遗诏存在。',89:'太后不哭及待宁再葬是原文言行，未推心理诊断或永久不葬。',90:'寿阳留一千兵复用前批既有事件，避免重复；袭焚、三千援兵、丁丑复取分录，狼烟约数不转村数。',91:'冀州张区别陵川同名；州人、张杀何的书证异说并列；甥保留原称不补母系，948授官回顾不强定杀人日。',92:'未名劝者判断、壬午计划及李劝乃止分开，不将五月朔日计划写成实际举行。'}
assert not (P/'publication.json').exists()
for n in range(86,93):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(86,93)],next_paragraph='zztj-v287-y0947-p001',next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原91—97行连续七段，本卷累计92/92；947年五月以后在卷287，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(86,93)],source_issues_review='辽太宗死亡日期与起病地点异说；赵延寿自称遗诏不当确证；冀州何行通被杀主体异说；张同名分开，甥保留称谓。',plain_language_review='首次逐项阅读新增人物、事件、角色、关系、日期地点、出处及事实说明，明确行动主体、判断、自称和计划；留兵旧事复用既有key，原文摘录保持底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
