# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 13–21."""
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
COMMIT='20d7e6560e7ea1d32a1da921d2ba225e55b0e6ce'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-opening','jiuwudaishi-103-march-950']:
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
main_sources = ['tongjian-289-950-opening','tongjian-289-950-spring-government']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p013-p021',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-289-950-spring-government':'卷289·乾祐三年·四月、五月及追述','jiuwudaishi-103-april-950':'卷103·隐帝本纪·乾祐三年四月','xinwudaishi-012-chai-rong-early':'卷12·周世宗本纪·早年与贵州任职','jiuwudaishi-114-chai-rong-early':'卷114·周世宗本纪·早年与贵州任职','xinwudaishi-020-chai-empress':'卷20·周太祖圣穆皇后柴氏传','songshi-253-zhe-deyi-family':'卷253·折德扆传·父子身份','hanshu-001-changling-burial':'卷1下·高帝纪·葬长陵','houhanshu-002-yuanling-burial':'卷2·显宗孝明帝纪·光武帝葬原陵'}
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
for n in range(13, 22):
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
    labels={'tongjian-289-950-spring-government':'卷289·乾祐三年·四月、五月及追述','jiuwudaishi-103-april-950':'卷103·隐帝本纪·乾祐三年四月','xinwudaishi-012-chai-rong-early':'卷12·周世宗本纪·早年与贵州任职','jiuwudaishi-114-chai-rong-early':'卷114·周世宗本纪·早年与贵州任职','xinwudaishi-020-chai-empress':'卷20·周太祖圣穆皇后柴氏传','songshi-253-zhe-deyi-family':'卷253·折德扆传·父子身份','hanshu-001-changling-burial':'卷1下·高帝纪·葬长陵','houhanshu-002-yuanling-burial':'卷2·显宗孝明帝纪·光武帝葬原陵'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年三月、四月、五月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_03_{len(B["claims"])+1:04d}'
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



ALIASES.update({'帝':'刘承祐','折从阮':'折从远','杨信':'杨承信','郭荣':'柴荣','郭威妻':'柴氏（郭威妻）'})
NEW_ALIASES={'柴荣':['郭荣','柴榮','郭榮'],'柴守礼':['柴守禮'],'柴氏（郭威妻）':['圣穆皇后柴氏','聖穆皇后柴氏'],'折德扆':[]}
NEW_DESCRIPTIONS={
'柴荣':'本姓柴，950年《资治通鉴》以郭荣记名，任贵州刺史、天雄牙内都指挥使。父亲柴守礼是郭威妻子柴氏的兄长，郭威在尚无儿子时收养他。《新五代史》记他幼年跟随姑母在郭威家成长。《旧五代史》的任职纪年与通鉴不同，分别保留。',
'柴守礼':'柴荣的父亲，也是郭威妻子柴氏的兄长。《资治通鉴》和新旧五代史都记其父子身份；本段没有记其950年官职和生卒年。',
'柴氏（郭威妻）':'郭威的妻子，柴守礼的妹妹、柴荣的姑母。《新五代史》后妃传记她没有儿子，与郭威收养兄长之子柴荣，后称圣穆皇后。本段仅核亲属身份，不将后来皇后称号当作950年在位身份，生卒年尚未录入。',
'折德扆':'折从远（后名折从阮）之子，任府州蕃汉马步都指挥使。950年五月己亥获任府州团练使，《宋史》也明确记其父为从阮。生卒年未载。'}
april='jiuwudaishi-103-april-950';march='jiuwudaishi-103-march-950';newchai='xinwudaishi-012-chai-rong-early';oldchai='jiuwudaishi-114-chai-rong-early';empress='xinwudaishi-020-chai-empress';zhe='songshi-253-zhe-deyi-family';chang='hanshu-001-changling-burial';yuan='houhanshu-002-yuanling-burial'
add('han_orders_ancestral_temples','后汉下诏在汉高祖、汉光武帝陵墓营建寝庙',13,'甲寅，','以时致祭。',[('刘承祐','下诏在两汉帝陵营建寝庙，按时祭祀')],when='950年三月甲寅',place='汉高祖长陵、汉光武帝原陵',note='寝庙为陵墓祭祀建筑，所指两汉先帝，不能认作后汉刘知远陵墓。具体建筑规模和位置坐标未载。')
sup('han_orders_ancestral_temples',13,chang,'五月丙寅，葬長陵。','《汉书》高帝纪记高帝葬在长陵，可用于识别本段汉高祖陵名。','只校核陵名，不将汉初下葬日期搬为950年，也不新建汉初丧葬事件。',relation='adds',field='location_name')
sup('han_orders_ancestral_temples',13,yuan,'三月丁卯，葬光武皇帝於原陵。','《后汉书》记光武皇帝葬原陵，并奉庙号世祖，可用于识别本段世祖原陵。','只校核陵主，不把古代下葬日当后汉诏令日期；原文注文中的地点不直接转为现代坐标。',relation='adds',field='location_name')
add('officials_suspend_temple_project','主管官署认为费用过高，搁置帝陵寝庙计划',13,'有司以费多，','寝其事，',[],year=None,when='950年三月诏令之后，具体搁置日未载',place='后汉主管官署、长陵与原陵',note='寝其事解释为搁置计划，不写成已建成后停用；有司未具名。')
claim('event',E['officials_suspend_temple_project'],'description','《资治通鉴》追记直到后汉灭亡，两陵也没有得到一次祭奠。',13,'以至国亡，二陵竟不沾一奠。','这是跨时段结果概述，不能把后汉灭亡当作950年三月当天事件，未补后来全无祭祀的普遍结论。')
for code,name,title,quote,day,place in [('gao_tianping','高行周','高行周调任天平节度使','徙高行周为天平节度使，','壬戌','天平军'),('fu_pinglu','符彦卿','符彦卿调任平卢节度使','符彦卿为平卢节度使。','壬戌','平卢军'),('murong_taining','慕容彦超','慕容彦超调任泰宁节度使','甲子，徙慕容彦超为泰宁节度使。','甲子','泰宁军')]:
 event(code,title,14,quote,[(name,title[len(name):])],when='950年三月'+day,place=place,note='调任为正式命令，未给实际到任日，不补现代军镇疆界。');E[code]='event_zztj_289_0950_'+code
sup('gao_tianping',14,march,'壬戌，鄴都高行周移鎮鄆州，兗州符彥卿移鎮青州，並加邑封。','《旧五代史》同日记高行周移镇郓州、符彦卿移镇青州，并增加封邑。','主书军镇名与旧史州名分别保留，对应已有天平、平卢任职脉络；加邑封为旧史补充。',relation='adds')
sup('murong_taining',14,march,'鄆州慕容彥超移鎮兗州。','《旧五代史》甲子条也记慕容彦超由郓州移镇兖州。','与主书泰宁军任职对照，未造两次调任。')
add('zhe_family_audience','折从阮带家族入朝',15,'永安节度使',None,[('折从阮','以永安节度使身份带家族入朝')],when='950年三月条下，具体日未载',place='府州至后汉京师',note='折从阮即已更名的折从远，沿同一主体；举族不补每位家属名单。')
sup('zhe_family_audience',15,march,'府州折從阮皆自鎮來朝，嘉慶節故也。','《旧五代史》三月来朝名单也列府州折从阮，说明来朝为嘉庆节。','同月行动对照，但旧史不记举族及独立日，未强定为丙午来朝。')
for code,name,title,start,end,when,place in [
('xue_kuangguo','薛怀让','薛怀让调任匡国节度使','夏，四月，','为匡国节度使。','950年四月戊辰朔','匡国军'),
('zhe_wusheng','折从阮','折从阮调任武胜节度使','庚午，','为武胜节度使。','950年四月庚午','武胜军'),
('yang_baoda','杨信','杨信调任保大节度使','壬申，','为保大节度使，','950年四月壬申','保大军'),
('liu_ci_anguo','刘词','刘词由镇国调任安国节度使','徒镇国','为安国节度使，','950年四月壬申','安国军'),
('wang_lingwen_anyuan','王令温','王令温由永清调任安远节度使','永清节度使','为安远节度使。','950年四月壬申','安远军')]:
 add(code,title,16,start,end,[(name,title[len(name):])],when=when,place=place,note='按主书日序分录命令；徒是底本字形，此处按调任解释，原字不改。未给到任日。')
sup('xue_kuangguo',16,april,'邢州薛懷讓移鎮同州，','《旧五代史》同日记薛怀让从邢州移镇同州。','州名与主书匡国军分别保存，不把名义军镇和现代行政疆界混同。')
sup('zhe_wusheng',16,april,'庚午，府州折從阮移鎮鄧州。','《旧五代史》同日记折从阮从府州调镇邓州。','与武胜军任职对照，不因从远从阮更名新建人物。')
sup('yang_baoda',16,april,'安州楊信移鎮鄜州，','《旧五代史》壬申条记杨信由安州调镇鄜州。','杨信与杨承信身份已按任地及父光远校核；姓名写法保留，未另造改名日。')
sup('liu_ci_anguo',16,april,'壬申，華州劉詞移鎮邢州，','《旧五代史》同日记刘词由华州调镇邢州。','同一调任，军镇名、州名分别保存。')
sup('wang_lingwen_anyuan',16,april,'貝州王令溫移鎮安州，並加邑封。','《旧五代史》同日记王令温由贝州调镇安州，并增封邑。','加邑封为此书补充，不把旧任永清写作950年新获封。',relation='adds')
add('wang_rao_secret_communication','王饶在李守贞叛乱期间暗中与他联络',16,'李守贞之乱，','王饶潜与之通。',[('王饶','在李守贞叛乱时暗中与他联络'),('李守贞','叛乱期间与王饶有暗中联络')],year=None,when='李守贞叛乱期间的追述，具体联络年月未载',place='王饶与李守贞之间，具体地点未载',note='潜通为史书记载，没有书信细节；不把此事放在950年四月。')
add('wang_rao_courts_shi','王饶入朝后竭力结交史弘肇',16,'及入朝，','厚结史弘肇，',[('王饶','入朝后竭力结交史弘肇'),('史弘肇','成为王饶竭力结交的对象')],when='950年入朝后，具体结交日未载',place='后汉京师',note='厚结指极力结交，未列贿赂数额，也未明记史弘肇亲自推荐任命。')
add('wang_rao_huguo','王饶升任护国节度使，引起惊讶',16,'及入朝，',None,[('王饶','入朝结交史弘肇后升任护国节度使')],when='950年四月条下，主书未单列任命日',place='护国军',note='主书作护国，旧史同月作华州节度使，目的地差异待核；不将两者自动拆成两次实际调任。')
claim('event',E['wang_rao_huguo'],'description','李守贞被平定后，人们原以为王饶会被安排闲职，听到他获任节度使时感到惊讶。',16,span(16,'守贞平，'),'这是史书叙述的舆论反应，未列发言者；王饶暗通与任命之间未有证据证明全部幕后过程。')
sup('wang_rao_huguo',16,april,'以鄜州留後王饒為華州節度使，以其來朝故也。','《旧五代史》壬申条记鄜州留后王饶任华州节度使，理由写他来朝。','与主书护国节度使的军镇地点不同，日期和理由的详略也不同。分别保留，不据此抹去主书的结交与惊讶记载。',relation='conflicts',field='location_name')
add('yang_bin_requests_resignation','杨邠请求辞去枢密使',17,'杨邠求','枢密使，',[('杨邠','请求辞去枢密使')],when='950年四月辛巳之前，具体请求日未载',place='后汉朝廷',note='求解是请求辞任，未已免职。')
add('han_refuses_yang_resignation','刘承祐派宦官劝止杨邠辞任',17,'杨邠求','谕止之。',[('刘承祐','派宦官劝杨邠继续任职'),('杨邠','收到劝止辞任的传话')],when='950年四月辛巳之前，具体日未载',place='后汉朝廷、传话现场',note='中使未具名，不补使者身份，帝闻下文不是证明刘承祐亲自在场。')
add('wu_supports_yang_resignation','吴虔裕支持杨邠辞职，主张枢密使轮换',17,'宣徽北院使','相公辞之是也。”',[('吴虔裕','主张枢密职位不宜久任，支持杨邠辞职')],when='950年四月辛巳之前，传话现场，具体日未载',place='杨邠接见中使的现场',note='吴虔裕的主张不等于朝廷已实行轮换制度；旧史明记中使回报，不把谈话写成帝前面谏。')
add('wu_qianyu_zhengzhou','刘承祐听到吴虔裕的言论后不悦，任他为郑州防御使',17,'帝闻之，',None,[('刘承祐','听到吴虔裕言论后不悦，任命他到郑州'),('吴虔裕','获任郑州防御使')],when='950年四月辛巳',place='后汉朝廷、郑州',note='主书叙不悦与外任的先后，不补正式处分文书，也不写已被处死。')
sup('wu_qianyu_zhengzhou',17,april,'中使還具奏，帝不悅，故有是命。','《旧五代史》明确说宦官回报吴虔裕言论，皇帝不悦，因此任他为郑州防御使。','补明消息传递与史书所叙因果，具体情绪为书中记载，不扩成其他刑罚。',relation='adds')
add('court_plans_guo_yedu','后汉朝廷计划让郭威镇邺都，督率诸将防御契丹',18,'朝廷以契丹','以备契丹。',[('郭威','被提议到邺都督率诸将防御契丹')],when='950年四月壬午任命之前，具体议论日未载',place='后汉朝廷、邺都与河北',description='史书记契丹近期入侵河北，各藩镇只顾自守。后汉朝廷计划派郭威镇邺都，统一督率诸将防御。',note='这是计划背景，未列契丹本次所有路线日期和人数，不另造无明确纪日的完整战役。')
add('shi_su_dispute_guo_authority','史弘肇与苏逢吉争论郭威出镇后是否兼掌枢密',18,'史弘肇欲','今反以外制内，其可乎！”',[('史弘肇','主张郭威保留枢密使以便指挥军队'),('苏逢吉','认为外镇兼掌枢密没有先例，会形成外制内')],when='950年四月壬午任命之前',place='后汉朝廷',note='两人的制度理由与不满分别保留；未因对郭威方案有异议就建立个人敌对关系，故事无之为苏逢吉观点。')
add('guo_wei_yedu_appointment','刘承祐任郭威为邺都留守、天雄节度使，保留枢密使',18,'壬午，','枢密使如故。',[('刘承祐','采纳保留郭威枢密使的方案，下诏任命'),('郭威','获任邺都留守、天雄节度使，继续兼枢密使')],when='950年四月壬午',place='邺都、天雄军',note='正式命令与实际辞行、到任在后文分录；未把郭威此时职务写成已经称帝。')
sup('guo_wei_yedu_appointment',18,april,'壬午，以樞密使郭威鄴都留守，依前樞密使。','《旧五代史》同日也记郭威任邺都留守，仍为枢密使。','同一命令，旧史略写不等于否定主书天雄节度职。')
add('hebei_obeys_guo_supplies','后汉命河北诸州按郭威文书供应兵甲和钱粮',18,'仍诏河北，','立皆禀应。',[('刘承祐','下诏河北按郭威文书供应军需'),('郭威','其军需文书获得直接调度效力')],when='950年四月壬午任命条下',place='河北诸州',note='兵甲钱谷为兵器、钱粮等军需，未列具体征收或支出数，不能推成郭威取得全国财政权。')
sup('hebei_obeys_guo_supplies',18,april,'詔河北諸州，應兵甲、錢帛、糧草一稟郭威處分。','《旧五代史》也记河北兵甲、钱帛和粮草听郭威调度。','范围在河北，军需权限与全国宰相职权不混同。')
add('dou_house_banquet_dispute','朝贵在窦贞固家饮宴，史弘肇与文臣发生争执',18,'明日，',None,[('窦贞固','其宅第成为朝贵饮宴场所'),('史弘肇','向郭威敬酒并厉声批评廷议分歧、贬低文书作用'),('郭威','受到史弘肇敬酒'),('苏逢吉','与杨邠举杯，劝不必介意国事争论'),('杨邠','与苏逢吉劝不必介意国事争论'),('王章','反问没有文书如何取得财赋')],when='950年四月壬午任命的翌日，未自行换算公历日期',place='后汉京师窦贞固宅第',description='郭威获任的翌日，朝贵在窦贞固家会饮。史弘肇对廷议分歧不满，又贬低文书的作用；苏逢吉、杨邠劝解，王章反问没有文书如何取得财赋。史书记将相从此开始出现裂痕。',note='毛锥解释为毛笔、文书工作。弟为敬酒称呼，不建立史弘肇与郭威血亲；窦宅场所不证明所有宾客都由窦本人邀请。')
add('yongan_military_command_abolished','后汉撤销府州永安军军额',19,'癸未，',None,[('刘承祐','下诏撤销永安军军额')],when='950年四月癸未',place='府州永安军',note='军额是军镇名号，不等于摧毁府州城市或驱散所有驻军。')
sup('yongan_military_command_abolished',19,april,'癸未，府州永安軍額宜停，命降為團練州。','《旧五代史》同日明确记府州停止永安军军额，降为团练州。','补明地点与调整后的级别，不把后年重建永安军提前到本日。',relation='adds')
add('chai_rong_guizhou_appointment','后汉任命柴荣为贵州刺史、天雄牙内都指挥使',20,'壬辰，','天雄牙内都指挥使。',[('刘承祐','任命左监门卫将军郭荣为贵州刺史、天雄牙内都指挥使'),('郭荣','以左监门卫将军身份获任贵州刺史、天雄牙内都指挥使')],when='950年四月壬辰',place='天雄军；所领贵州史载地名',note='郭荣即本姓柴的柴荣，统一主体，不新建另一人。贵州为当时州名，不直接套现代贵州省位置；领刺史与牙内职不推实际赴贵州到任。')
sup('chai_rong_guizhou_appointment',20,newchai,'太祖鎮天雄，榮領貴州刺史、天雄軍牙內都指揮使。','《新五代史》也记郭威镇天雄时，柴荣领贵州刺史、天雄军牙内都指挥使。','任职内容相合，此句未列绝对纪年，不作为950年日期独立确证。')
sup('chai_rong_guizhou_appointment',20,oldchai,'二年，太祖鎮鄴，改天雄軍牙內都指揮使，領貴州刺史、檢校右僕射。','《旧五代史》周世宗本纪在汉乾祐二年记郭威镇邺、柴荣任天雄牙内都指挥使并领贵州刺史。','与通鉴乾祐三年条及旧史隐帝本纪郭威镇邺年不同，保存纪年冲突；不拆成无证据的两次任命。',relation='conflicts',field='time_original')
relationship('郭威','柴荣','养父',20,'威未有子时养以为子。','郭威是柴荣养父，收养为此前追述，具体年月未载。')
relationship('柴守礼','柴荣','父亲',20,'荣本姓柴，父守礼，郭威之妻兄也，','守礼为柴荣亲父，郭威妻兄所指守礼，不把郭威当柴荣生父。')
relationship('柴氏（郭威妻）','郭威','妻子',20,'柴氏女適太祖，是為聖穆皇后。',source=newchai,note='结合本传上句柴氏女适太祖，后为圣穆皇后核郭威妻身份；不把后追号当作950年在位皇后。')
relationship('柴守礼','柴氏（郭威妻）','兄长',20,'荣本姓柴，父守礼，郭威之妻兄也，','柴守礼是郭威妻子柴氏的兄长，方向由兄明确。')
relationship('柴氏（郭威妻）','柴荣','姑母',20,'后兄守禮子榮，幼從姑長太祖家，','柴氏是柴荣父亲的妹妹，姑母方向明确；新史父名与主书对应。',source=newchai)
claim('person',people['柴荣'],'description','《新五代史》记柴荣本姓柴，为邢州龙冈人。',20,'世宗睿武孝文皇帝，本姓柴氏，邢州龍岡人也。','只补本姓与籍贯，后来的世宗皇帝称号是传记标题，不作为950年已即位。',source=newchai)
claim('person',people['柴荣'],'birth_year','《旧五代史》记柴荣生于唐天祐十八年辛巳，即921年，出生地为邢州别墅。',20,'帝以唐天祐十八年，歲在辛巳，九月二十四日丙午，生於邢州之別墅。','本条原纪年与出生地保持，年换算为921；不把农历九月二十四日直接展示为公历月日。出生年份作为来源事实，不在本段另造950年出生。',source=oldchai)
claim('person',people['柴氏（郭威妻）'],'description','《新五代史》后妃传记郭威妻子柴氏没有儿子，收养兄长柴守礼的儿子，后来成为周世宗。',20,'周太祖聖穆皇后柴氏，無子，養后兄守禮之子以為子，是為世宗。','仅补亲属与收养关系，不把周太祖、皇后和世宗的后来称号提前作950年身份。',source=empress)
add('zhe_deyi_fuzhou_appointment','后汉任命折德扆为府州团练使',21,'五月，','本州团练使。',[('刘承祐','任命府州蕃汉马步都指挥使折德扆为本州团练使'),('折德扆','由府州蕃汉马步都指挥使获任府州团练使')],when='950年五月己亥',place='府州',note='本州指府州，与前段永安军撤额后团练州调整相接，不写成新建另一府州。')
relationship('折从阮','折德扆','父亲',21,'德扆，从阮之子也。','折从阮即折从远，是折德扆的父亲，沿既有改名主体。')
claim('person',people['折德扆'],'description','《宋史》折德扆传也明确说其父为折从阮，家族世居云中。',21,'折德扆，世居雲中，為大族。父從阮，','只核籍贯背景与父子身份，该段后年永安军建置纪年有待校核，不提前录后周任命。',source=zhe)
reviews={13:'两汉高祖长陵与光武世祖原陵通过汉书后汉书定位，未误认刘知远陵墓；诏令、官署搁置、到后汉亡仍无祭奠的追叙分别处理，结果不强记本月。',14:'三项调任分别按壬戌与甲子，军镇名和州名对照，未给实际到任日。',15:'折从阮沿折从远改名主体；举族未补成员，旧史同月嘉庆节来朝不套丙午。',16:'五项调任逐日分录，徒字保留；王饶暗通李守贞为追述，众人预期为意见，结交不是明载推荐。护国与旧史华州军镇不同保留异说，不造两次无证调任。',17:'辞职请求、派使劝止、吴虔裕支持及帝不悦外任分开，中使传话非帝亲自在场。轮换为吴意见不是已实施制度。',18:'契丹入寇背景不造完整战役。派郭镇邺计划、保留枢密争论、正式任命、军需权限及翌日宴争分开。毛锥解释文书，弟非血亲，制度观点非确定个人敌对。',19:'罢永安军按旧史府州军额降团练州解释，不等于城市或驻军被毁。',20:'郭荣本姓柴，与柴荣同主体；收养、亲父、妻兄、姑母均有方向。收养追述不系本月，未来帝后称号不提前。贵州不直接映现代省；旧史二年与主书三年任职冲突，出生年921来源事实独立保存，无伪公历月日。',21:'本州为府州，五月己亥任命与父子关系区分；宋史仅补家族身份，后年节镇建置未提前录。'}
assert not (P/'publication.json').exists()
for n in range(13,22):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(13,22)],next_paragraph=Q[22]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原18—26行连续九段；发布后首21/83正文已录，余62段待录。两段图书库快照覆盖更多后文不视为已录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(13,22)],source_issues_review='王饶主书护国与旧史华州地点异说保留；柴荣旧史乾祐二年与主书三年任职不强合。贵州史载州名不套现代省。折从阮沿既有折从远；杨信同杨承信此前已核。原陵长陵通过两汉书定位，电子本和纸本异文仍待核。',plain_language_review='首次逐条自查标题、人物介绍、角色、关系方向、时间地点与来源解释。明确请求、计划、正式命令、舆论和追述，毛锥解释为文书，未知起止保留null；生父养父区分、帝后追号不提前。原字引用不改，不另安排固定发布后二次改写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
