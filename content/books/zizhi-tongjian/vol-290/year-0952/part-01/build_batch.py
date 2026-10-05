# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 952 paragraphs 1–8."""
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
COMMIT='44575c9b45f3f29cba05ba49f0a7a9dc69fba5f3'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-951-final-appointments']:
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
main_sources = ['tongjian-290-951-final-appointments','tongjian-290-952-january-continuation']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0952-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-952-january-continuation':'卷290·广顺二年·正月起及相邻追述','jiuwudaishi-112-january-952':'卷112·太祖本纪三·广顺二年正月','xinwudaishi-011-second-year-952':'卷11·周本纪·广顺二年'}
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
for n in range(1, 9):
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
    labels={'tongjian-290-952-january-continuation':'卷290·广顺二年·正月起及相邻追述','jiuwudaishi-112-january-952':'卷112·太祖本纪三·广顺二年正月','xinwudaishi-011-second-year-952':'卷11·周本纪·广顺二年'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺二年（952年正月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0952_01_{len(B["claims"])+1:04d}'
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










ALIASES.update({'帝':'郭威','唐主':'李璟','乐元福':'药元福','史延超':'史延超（后周齐州防御使）'})
NEW_ALIASES={'曹英':[],'史延超（后周齐州防御使）':['史延超','史延韬','史延韜'],'张令彬':['張令彬'],'燕敬权':['燕敬權']}
NEW_DESCRIPTIONS={'曹英':'后周侍卫步军都指挥使、昭武节度使。952年正月任兖州行营都部署，率兵讨伐慕容彦超。生卒年未载。','史延超（后周齐州防御使）':'后周齐州防御使。952年正月与曹英等受命讨伐慕容彦超，任副部署。《旧五代史》同日同职写史延韬，按对应任命记录别名；与守晋州的史彦超分开。生卒年未载。','张令彬':'后周徐州巡检使，《旧五代史》称徐州巡检供给官。952年正月在沐阳击败南唐援军，并俘获燕敬权等。生卒年未载。','燕敬权':'南唐将领。952年正月南唐援慕容彦超的军队在沐阳被后周军击败时被俘。出生、死亡年份未载。'}
old='jiuwudaishi-112-january-952';nw='xinwudaishi-011-second-year-952'
add('sun_cao_failed_arson','孙朗、曹进夜间起事，潜烧府门未能点燃',1,'春，正月，','火不然。',[('孙朗','率部夜间起事，尝试焚烧府门'),('曹进','与孙朗率部尝试焚烧府门')],when='952年正月庚申夜',place='长沙',note='承前边镐治湖南的府门场景；火不然是没有燃起，不写成成功烧毁府门。')
add('bian_repels_mutiny','边镐发现起事后出兵交战，并命人鸣鼓角',1,'边镐觉之，','且命鸣鼓角，',[('边镐','发现起事，出兵交战并命人鸣鼓角')],when='952年正月庚申夜',place='长沙')
add('sun_cao_flee_langzhou','孙朗、曹进误以为天将亮，破关逃往朗州',1,'朗、进等以为将晓，','斩关奔朗州。',[('孙朗','误以为天将亮，破关逃往朗州'),('曹进','与孙朗破关逃往朗州')],when='952年正月庚申起事以后',place='长沙至朗州',note='以为将晓是判断，不据此认定鸣鼓角时实际已经天亮；斩关不补具名被杀守兵。')
add('wang_kui_consults_sun','王逵向孙朗询问用朗州兵夺回湖南是否可行',1,'王逵问朗曰：','可乎？”',[('王逵','询问以朗州军夺回湖南的可行性'),('孙朗','受王逵询问南唐军政情况')],when='952年正月孙朗到朗州之后',place='朗州',note='王逵所说此前与淮南交战多胜是其自述，不独立生成未具名战役或确定次数。')
add('sun_promises_hunan_vanguard','孙朗批评南唐军政，愿为王逵前驱，王逵厚待他',1,'朗曰：',None,[('孙朗','批评南唐军政，提出为夺湖南作前驱'),('王逵','听后欣喜并厚待孙朗')],when='952年正月王逵问策之后',place='朗州',note='朝无贤臣、取湖南如拾芥是孙朗的判断与夸言，不把未来夺地写成已经发生，也不视作南唐所有官员的客观评定。')
add('guo_repairs_daliang','后周征发开封府五万民夫修大梁城，十日左右后停止',2,'壬戌，',None,[('帝','征发开封府民夫修大梁城')],when='952年正月壬戌起役，旬日后停止',place='大梁城',note='初始日期与工期分清，不自行换算确切结束干支。')
sup('guo_repairs_daliang',2,old,'壬戌，修東京羅城，凡役丁夫五萬五千，兩旬而罷。','《旧五代史》同日记修东京罗城，征役五万五千人、两旬后停止。','与《资治通鉴》五万人、旬日不同，保留人数与工期异说，不用较详细数字覆盖主书。',relation='conflicts')
add('murong_prepares_yanzhou','慕容彦超征乡兵入城，引泗水入城壕备战',3,'慕容彦超发乡兵','为战守之备。',[('慕容彦超','征乡兵入城，引泗水入城壕备战')],when='952年正月甲子处置以前',place='兖州、泗水',note='引水备战不等于已经淹没邻州，不猜具体河道工程尺寸。')
add('murong_orders_border_plunder','慕容彦超向镇将发旗，令招募盗众抢掠邻境，地方上报其反叛',3,'又多以旗帜','所在奏其反状。',[('慕容彦超','命诸镇将招募群盗、抢掠邻境')],when='952年正月甲子讨伐任命以前',place='泰宁军及邻境',note='镇将与上报者未具名，不补名单或每次抢掠人数。')
add('yi_mi_detached_taining','郭威敕令沂州、密州不再隶属泰宁军',3,'甲子，','敕沂、密二州不复隶泰宁军。',[('帝','把沂州、密州从泰宁军管辖中划出')],when='952年正月甲子',place='沂州、密州、泰宁军',note='只是改隶，不推定两州此时已被慕容彦超攻占或废置。')
add('cao_ying_yanzhou_commander','郭威任命曹英为行营都部署，讨伐慕容彦超',3,'以侍卫步军都指挥使、','讨彦超，',[('帝','任曹英统率讨伐军'),('曹英','由侍卫步军都指挥使、昭武节度使受任都部署')],when='952年正月甲子',place='兖州行营')
sup('cao_ying_yanzhou_commander',3,old,'甲子，以侍衛步軍都指揮使曹英為兗州行營都部署，','《旧五代史》同日记曹英任兖州行营都部署。','明确行营与目标地区，未把任命当成已经攻破兖州。')
sup('cao_ying_yanzhou_commander',3,nw,'二年春正月甲子，侍衞步軍都指揮使曹英為兗州行營都部署。','《新五代史》也记广顺二年正月甲子曹英任兖州行营都部署。','仅引用正月任命，不提前录同段后面的五月城破与慕容之死。')
add('shi_yanchao_deputy','郭威任命齐州防御使史延超为副部署',3,'齐州防御使史延超','为副部署，',[('帝','任史延超为讨伐军副部署'),('史延超','以齐州防御使身份受任副部署')],when='952年正月甲子',place='兖州行营',note='史延超与之前晋州守将史彦超姓名职务不同，分别建主体。')
sup('shi_yanchao_deputy',3,old,'以齊州防禦使史延韜為副部署，','《旧五代史》同日同职写史延韬。','按齐州防御使、同日曹英副部署的组合对应史延超，记录异名，不只凭近似字形自动合并。',relation='adds')
add('xiang_xun_supervisor','郭威任命向训为讨伐军都监',3,'皇城使河内向训','为都监，',[('帝','任向训为讨伐军都监'),('向训','以皇城使身份受任都监')],when='952年正月甲子',place='兖州行营')
sup('xiang_xun_supervisor',3,old,'以皇城使向訓為兵馬都監，','《旧五代史》也记向训任兵马都监。','沿951年虒亭参战主体，官职改变不新建同名人。')
claim('person',people['向训'],'description','向训是河内人，此时为皇城使。',3,'皇城使河内向训为都监，','本段明确籍贯与原职；河内用史载名称，不强定现代出生坐标。')
add('yao_yuanfu_yanzhou_vanguard','郭威任命药元福为行营马步都虞候',3,'陈州防御使乐元福','为行营马步都虞候。',[('帝','任药元福为行营马步都虞候'),('乐元福','以陈州防御使身份受任马步都虞候')],when='952年正月甲子',place='兖州行营',note='底本本句作乐元福，后文作药元福；旧史同日同职写藥元福，按已核主体复用，摘录不改字。')
sup('yao_yuanfu_yanzhou_vanguard',3,old,'陳州防禦使藥元福為馬步都虞候，率兵討慕容彥超。','《旧五代史》记陈州防御使药元福任马步都虞候。','同日同职对应本段乐字写法，不另建乐元福。')
add('guo_honors_veteran_yao','郭威命曹英、向训以父辈礼遇药元福',3,'帝以元福宿将，',None,[('帝','要求曹英、向训不要按一般军礼对待宿将药元福'),('曹英','以父辈礼节尊敬药元福'),('向训','以父辈礼节尊敬药元福'),('药元福','作为宿将获特别礼遇')],when='952年正月甲子任命以后',place='后周讨伐军',note='父事为尊敬礼遇，不建立生父、养父或结义关系；旧书引隆平集是附注，未另算独立原书确证。')
add('tang_sends_murong_relief','李璟派五千兵驻下邳，援助慕容彦超',4,'唐主发兵五千，','以援彦超。',[('唐主','派五千兵援助慕容彦超'),('慕容彦超','成为南唐援助对象')],when='952年正月后周讨伐军行动期间',place='下邳',note='派兵驻援与此前951年求援分开，不另造受命主帅姓名。')
add('tang_army_retreats_muyang','南唐援军听说后周兵将到，退驻沐阳',4,'闻周兵将至，','退屯沐阳。',[],when='952年正月南唐军驻下邳以后',place='下邳至沐阳',note='驻地移动不等于此时已经投降。')
add('zhang_lingbin_muyang_victory','张令彬在沐阳击败南唐军，并俘获燕敬权',4,'徐州巡检使张令彬',None,[('张令彬','击败南唐援军'),('燕敬权','南唐军败后被俘')],when='952年正月，具体交战日未载；旧史丙寅记奏报',place='沐阳',description='张令彬在沐阳击败南唐援军，南唐军中被杀或溺死者合计千余人，燕敬权被俘。',note='杀、溺死者千余人为合计，未给分别数；被俘与未来获释分开，不提前录二月释使。')
sup('zhang_lingbin_muyang_victory',4,old,'丙寅，徐州巡檢供給官張令彬奏，破淮賊於沭陽，斬首千餘級，擒賊將燕敬權。','《旧五代史》丙寅记张令彬奏报在沭阳破军、斩首千余、俘燕敬权。','主书杀与溺死合计，此书记斩首，伤亡方式分别保留；沐阳与沭阳字形不同，奏报日不当交战日。',relation='conflicts')
add('murong_external_diversion_plan','慕容彦超谋划借外敌扰边牵制后周，乘机行动',5,'初，彦超以周室新造，','然后乘间而动。',[('慕容彦超','希望借北汉、契丹和南唐扰边牵制朝廷')],year=951,when='后周初立后的951年谋划，具体各次联络日未载',place='泰宁军及北汉、契丹、南唐',note='这是对已录私联北汉、求援南唐的策略补充，并提及契丹；不重复创建同一封私书，不推定各方进攻完全由他指挥。')
add('murong_external_support_weakens','北方围晋州的军队退去、南唐援军败后，慕容彦超势力受挫',5,'及北汉、契丹自晋州北走，',None,[('慕容彦超','外援退败后处境受挫')],when='952年正月沐阳战败以后',place='泰宁军',note='此前951年晋州撤军已有事件，只作为本次处境变化的背景，不重复录一次退军。')
add('li_hongxin_uneasy_han_kin','李洪信因自己与后汉皇室的亲缘而不安',6,'永兴节度使李洪信，','心不自安。',[('李洪信','以永兴节度使身份因后汉亲缘而不安')],year=None,when='郭威即位后至952年正月入朝以前的追述，具体起始日未载',place='永兴军、长安',note='本段未列具体亲属，不只据近亲二字新建一条不明血缘关系。')
add('wang_jun_levies_changan_troops','王峻以救晋州为由，从长安守军征调数百人',6,'城中兵不满千人，','发其数百。',[('王峻','在陕州时征调李洪信所部数百兵'),('李洪信','所管长安守军部分被征调')],year=951,when='951年王峻救晋州、驻陕州期间的追述',place='陕州与长安',note='以救晋州为名是史书用语，不据此断定救援是假的或郭威另有未载密令；数百不换算成精确数字。')
add('wang_jun_garrisons_changan','北汉退兵后，王峻派千余禁兵驻长安',6,'及北汉兵遁去，','戍长安。',[('王峻','在北汉退兵后派千余禁兵驻长安')],year=None,when='951年十二月晋州解围后至952年正月李洪信入朝以前，具体派兵日未载',place='长安',note='派遣主语承前王峻；不以驻兵结果自行推定诛杀李洪信的计划。')
add('li_hongxin_court_visit','李洪信惧怕长安驻军变化，前往后周朝廷',6,'洪信惧，',None,[('李洪信','因不安和驻军变化而入朝')],when='952年正月条下，具体入朝日未载',place='长安至后周朝廷',note='本句记录入朝，未说他已获罪、被囚或被杀。')
add('wang_jun_returns_audience','王峻从晋州返回，入见郭威',7,'壬申，',None,[('王峻','从晋州返回后入见郭威'),('帝','接受王峻入见')],when='952年正月壬申',place='后周朝廷')
add('cao_ying_yanzhou_encirclement','曹英等到兖州，设置包围工事',8,'曹英等至兗州，','设长围。',[('曹英','率讨伐军到兖州，设置包围工事')],when='952年正月，具体抵达日未载',place='兖州城外',note='长围为围城设施，不等于已攻破城池。')
add('yao_yuanfu_repels_murong_sorties','慕容彦超多次出战，都被药元福击败',8,'慕容彦超屡出战，','彦超不敢出。',[('慕容彦超','多次出城作战，败后不敢再出'),('药元福','击败慕容彦超的多次出击')],when='952年正月兖州被围以后',place='兖州城外',note='屡未给次数，不编各次单独日期与战死名单。')
add('zhou_completes_yanzhou_siegeworks','后周军十余日后合拢长围，继续攻城',8,'十馀日，',None,[('曹英','率军完成包围工事后继续攻城')],when='952年正月到兖州设围十余日以后，具体攻城日未载',place='兖州',note='长围合与攻城不等于城已陷；五月亲征和城破留在后续正文处理。')
reviews={1:'庚申夜实际起事与此前末年计划分开；火未燃、鸣鼓角、误判天明、逃朗州及问策逐项录。孙朗对南唐的批评为话语，不当已证军政全貌；未提前录王逵复取湖南。',2:'五万旬日与旧史五万五千两旬异说并列，同壬戌起役，未自动改主书。',3:'乡兵水壕、招盗抢掠、沂密改隶与四将任命、老将礼遇分开。史延超与旧史史延韬同日同齐州职对应，非史彦超。乐元福同役藥元福印证，父事不建父子。新周本纪只补甲子曹任，不提前其后五月。',4:'五千援军驻下邳、退沐阳及战敗俘将分开。旧史丙寅为奏报，斩首与主杀溺口径不同，沐沭字形保留。燕敬权被俘不提前未来归唐。',5:'反叛者借扰边牵制为951初谋划补充，已有私书与求唐援不重复。951晋州退军作背景，外援势沮在952沐阳败后，不断言他指挥外军。',6:'李洪信沿950李业兄与保义任职主体，本次永兴职变不另建。近亲不补不明血缘；951征兵、跨年驻兵与正月入朝分清，救名不当假命令。',7:'正月壬申王峻还朝入见，与951受命出征和入晋解围分开。',8:'到兖设围、药元福击败出战与十余日合围攻城分开，不提前五月城破；屡次数不编造。'}
assert not (P/'publication.json').exists()
for n in range(1,9):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=290,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷290原90—97行连续八段；952年跨卷290、291，后续仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],source_issues_review='逐字原文不改，纸本未核。原文块跨951与952，仅按对应账本取本批八段；修城人数工期、史延超史延韬、乐药元福、沐沭地名及斩首杀溺口径分别核记。外交军略不推永久盟约，父事不造血亲。',plain_language_review='首次逐条检查标题、人物、角色、时间、关系解释和事实说明；引用外用白话。判断、请求、计划、任命、具体行动与未发生结果区分，追述保留正确年份或跨年未定。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
