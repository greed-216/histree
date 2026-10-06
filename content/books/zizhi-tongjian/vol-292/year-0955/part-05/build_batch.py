# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 32–39."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,40))
COMMIT='7a7159ae49017eccd2548c5c8143213ca3069a4e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-955-autumn-qinfeng']:
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
main_sources = ['tongjian-292-955-autumn-qinfeng','tongjian-292-955-winter-huainan']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0955-p032-p039',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
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
lines = (ROOT / 'resources/derived/tongjian/292.txt').read_text().splitlines()
for n in range(32, 40):
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
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷292·显德二年（955年十一月至十二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0955_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'王环（后蜀凤州节度使）':'镇州真定人，早年以勇力为孟知祥御者，后掌后蜀宿卫。开运末秦凤等地入蜀后，孟昶任其为凤州节度使。955年十一月凤州陷落时被后周军俘获。与914—929年楚水军将领王环分别保存，无同人证据。生卒年未载。','王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
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

def event(code, title, n, quote, actors, when=None, note='', year=955, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='955年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_292_0955_' + code
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
        edge = 'participation_zztj_292_0955_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0955_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 if kw.get('source'):
  t=(sources[kw['source']]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);quote=t[a:b]
 else:quote=span(n,start,end)
 E[code]=event(code,title,n,quote,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','王景':'王景（后晋耀州团练使）','吴越王':'钱弘俶','王环':'王环（后蜀凤州节度使）'})
NEW_ALIASES={'王环（后蜀凤州节度使）':[],'吴廷绍':['吳廷紹'],'韩令坤':['韓令坤'],'赵崇溥':['趙崇溥'],'殷崇义':['殷崇義'],'陈彦禧':['陳彥禧']}
NEW_DESCRIPTIONS={
'王环（后蜀凤州节度使）':'镇州真定人，早年以勇力为孟知祥御者，后掌后蜀宿卫。开运末秦凤等地入蜀后，孟昶任其为凤州节度使。955年十一月凤州陷落时被后周军俘获。与914—929年楚水军将领王环分别保存，无同人证据。生卒年未载。',
'吴廷绍':'南唐寿州监军。《通鉴》记其认为边境无事，冬季守淮浪费粮食物资，因此停止把浅防守；刘仁赡上表反对未获采纳。相关确切年份和生卒年未载。',
'韩令坤':'磁州武安人，后周侍卫马军都指挥使。955年十一月，奉柴荣命与其他十一名将领随李谷、王彦超出征南唐。生卒年未载。',
'赵崇溥':'后蜀凤州都监。955年十一月与威武节度使王环等被后周军俘获，随后因不进食而死，具体死亡时间未载。与后蜀客省使赵崇韬名字不同，未作合并。',
'殷崇义':'南唐官员。955年后周兵将至，李璟由翰林承旨、户部尚书任其为吏部尚书、知枢密院。生卒年及其他别名待对应史料补核。',
'陈彦禧':'吴越元帅府判官。955年受钱弘俶派遣入贡后周；柴荣随后下诏要求吴越出兵攻南唐。生卒年未载，未与其他书中仅有同名的作者强行合并。'
}
oc='jiuwudaishi-115-huainan-command';of='jiuwudaishi-115-fengzhou-report';od='jiuwudaishi-115-december-955';nw='xinwudaishi-62-huainan-war-start';ho='songshi-251-hanlingkun-origin'
lp=person('唐主',32,'是本段南唐君主，史书同时评价其性情与用人',span(32,'唐主性和柔，','政事日乱。'))
claim('person',lp,'evaluation','《通鉴》认为李璟性情温和、喜爱文章，却喜欢别人顺从自己，以致谄谀者得到任用、政事紊乱。',32,span(32,'唐主性和柔，','政事日乱。'),'这是史家对用人和政治的评价，不当作已量化验证的全部因果。')
claim('person',lp,'evaluation','《通鉴》称南唐攻取建州、击败湖南后，李璟更加骄傲，并有扩张天下的志向。',32,span(32,'既克建州，','有吞天下之志。'),'所述建州、湖南胜利为既往背景，未重建955年已发生的两场新战役；志向不等于实现。')
claim('person',lp,'biography','《通鉴》回述李璟曾为李守贞、慕容彦超的叛乱出兵，遥相声援。',32,span(32,'李守贞、','遥为声援。'),'两次旧事时间不由本955年条强定，保留回述事实；两名叛乱者与南唐君主并非同一人。')
claim('person',lp,'biography','《通鉴》回述南唐遣使从海路联络契丹和北汉，约定共同图谋中原。',32,span(32,'又遣使','未暇与之校。'),'中国在此指中原政权；原段未给各次使行日期，约定不当作同时已经联合出兵。')
add('tang_shallow_water_defense','南唐曾在冬季淮水变浅时派兵守河，称为把浅',32,'先是，','谓之“把浅”。',[],year=None,when='955年以前或南征前的历年冬季制度回述，起止年未载',place='淮水',note='每冬为长期惯例，不把全部历年戍守写成955年单次命令。')
add('wuting shao_ends_defense'.replace(' ',''),'吴廷绍停止冬季把浅防守',32,'寿州监军吴廷绍','悉罢之。',[('吴廷绍','认为边境无事、守兵耗粮，停止把浅')],year=None,when='955年南征以前，具体年份与月日未载',place='寿州及淮水防线',note='这是寿州监军对费用和边境的判断，不据此认定边境事实上毫无威胁。')
add('liurenshan_protests_defense','刘仁赡上表反对停止把浅，未能阻止',32,'清淮节度使刘仁赡','不能得。',[('刘仁赡','上表反对撤去冬季防守，未获采纳')],year=None,when='吴廷绍停止把浅时，具体年日未载',place='南唐寿州',note='不能得指反对意见未获采纳，不推定刘仁赡因此免官或被处罚。')
add('huainan_command_order','柴荣任李谷、王彦超统率淮南前军，命韩令坤等十二将随征',32,'十一月，','等十二将以伐唐。',[('帝','安排进攻南唐的淮南前军'),('李谷','任前军行营都部署并兼知庐寿等行府事'),('王彦超','任李谷副手'),('韩令坤','以侍卫马军都指挥使身份随前军出征')],when='955年十一月乙未朔',place='后周朝廷至淮南',note='李谷沿既有简体规范名，十二将含韩令坤，其余未列名不补造名单。')
sup('huainan_command_order',32,oc,'十一月乙未朔，以宰臣李穀為淮南道前軍行營都部署，知廬、壽等州行府事；以許州節度使王彥超為行營副部署；命侍衛馬軍都指揮使韓令坤等一十二將，各帶征行之號以從焉。','《旧五代史》同日记李谷、王彦超以及韩令坤等十二将的任命和随征安排。','许州节度与主书忠武节度为地方与军额称法，前军任命不等于后周君主当日已经亲征。')
sup('huainan_command_order',32,nw,'乃拜李穀為行營都部署，攻自壽州始。','《新五代史》南唐世家也记后周任李谷为行营都部署，从寿州开始进攻。','段首十三年十一月按南唐保大纪年上下文，同段后文混叙次年正阳战等，不将整段都算955年完成。')
claim('person',people['韩令坤'],'origin','韩令坤为磁州武安人。',32,'令坤，磁州武安人也。','籍贯保留古地名，现代坐标未核。')
claim('person',people['韩令坤'],'origin','《宋史》也记韩令坤为磁州武安人。',32,'韓令坤，磁州武安人。','只取籍贯，未据生平后文提前录入后续任职。',source=ho,relation='corroborates')

add('bian_channel_old_damage','《通鉴》回述汴水唐末溃决，埇桥东南成为积水之地',33,'汴水自唐末','悉为污泽。',[],year=None,when='唐末以来的河道背景，具体溃决年月未载',place='汴水、埇桥东南',note='史载污泽是积水荒地，不自动转换成现代环境污染指标。')
add('wuxingde_dredges_bian','柴荣命武行德征发民夫，循旧堤疏通汴水至泗上',33,'上谋击唐，','东至泗上。',[('上','为南征安排河道疏导'),('武行德','以武宁节度使身份征发民夫疏导河道')],year=None,when='955年南征准备期间或此前，具体施行年日未单列',place='汴水旧堤至泗上',note='先命表示南征前的准备顺序，本句未列明确年月；不把征发民夫命令当所有河段已经完工。')
add('chairong_defends_dredging','面对疏导河道的质疑，柴荣表示数年后必能获益',33,'议者皆以为难成，',None,[('上','认为河道工程将来会带来利益')],year=None,when='疏汴工程筹办时，具体年日未载',place='后周朝廷',note='数年之后是柴荣的预期，不自行写出确切竣工年和收益。')

add('chairong_discusses_punishment','柴荣与侍臣讨论刑赏，表示不因喜怒决定赏罚',34,'丁未，','因喜赏人。”',[('上','向侍臣说明刑赏原则')],when='955年十一月丁未',place='后周朝廷',note='这是治理原则的讲话，不等于已证明每次赏罚都符合此原则。')
add('daliang_streets_widened','柴荣整直拓宽大梁街道，宽处达到三十步',34,'先是，大梁','至三十步。',[('上','命整直并拓宽被民居侵占的道路')],when='955年扩城相关回述，具体实施日未载',place='大梁街道',description='《通鉴》记大梁居民占街建屋，大车能通行的道路很少。柴荣命令整直拓宽，宽处达到三十步。这是道路处理的回述，与此前扩外城规划分开，三十步不换算现代米数。')
add('daliang_graves_moved','大梁扩城时将坟墓迁到标志区域以外',34,'又迁坟墓','标外。',[('上','在扩城过程中安排迁坟')],when='955年扩城相关回述，具体迁移日未载',place='大梁扩城标志以外',note='该句明确迁坟，与此前今后新葬须标外七里的规定不同；本句未给迁移总数及新墓具体地点。')
add('chairong_accepts_city_criticism','柴荣承认扩城扰动居民与坟墓，表示愿承担批评',34,'上曰：“近广京城，',None,[('上','说明扩城扰动并表示承担怨谤')],when='955年十一月条中的扩城讲话，具体日未另列',place='大梁',description='柴荣承认扩城给生者和死者带来许多扰动，表示批评由自己承担，并认为将来会有利于百姓。这是柴荣对工程的说明，不抹去居民受到的实际影响。')

add('fengzhou_siege','王景等围攻凤州，韩通在城固镇阻断后蜀援军',35,'王景等围凤州，','以绝蜀之援兵。',[('王景','率军围凤州'),('韩通','分兵城固镇，截断后蜀援兵')],when='955年十一月戊申攻克以前，具体围城日未载',place='凤州及城固镇',note='城固镇沿古地名，不直接与现代城固县坐标绑定。')
add('fengzhou_captured','后周军攻克凤州，俘获王环、赵崇溥等将士五千人',35,'戊申，','等将士五千人。',[('王景','率后周军攻取凤州'),('王环','以威武节度使身份被俘'),('赵崇溥','以凤州都监身份被俘')],when='955年十一月戊申',place='凤州',note='五千为史载俘虏约述，不等同杀敌数；主书威武与旧本纪押送条凤翔称号差异保留。')
sup('fengzhou_captured',35,of,'癸丑，西南面行營都部署王景奏，收復鳳州，獲偽命節度使王環。','《旧五代史》记十一月癸丑王景奏报攻取凤州、俘获王环。','癸丑为奏报日，主书戊申为攻克日，分别保留，不仅据不同纪日就造两次凤州陷落。')
add('zhaochongpu_dies_captive','赵崇溥被俘后因不进食而死',35,'崇溥不食','而死。',[('赵崇溥','被俘后不进食，随后死亡')],year=None,when='955年十一月凤州被俘之后，具体死亡时间未载',place='俘后地点未载',note='死亡在被俘之后，但未列间隔，不强定戊申当日或一定955年内。')
claim('person',people['王环（后蜀凤州节度使）'],'origin','王环为真定人。',35,'环，真定人也。','对应同一后蜀威武节度使王环，籍贯不转为现代坐标。')
claim('person',people['王环（后蜀凤州节度使）'],'description','《新五代史》记凤州王环为镇州真定人，早年事孟知祥为御者，后获孟昶任命为凤州节度使。',35,'王環，鎮州真定人也。以勇力事孟知祥為御者，及知祥僭號于蜀，使典衞兵。晉開運之亂，秦、鳳、階、成入于蜀，孟昶以環為鳳州節度使。','这段明确后蜀履历；本站原裸名王环为楚水军将领，无同人证据，本次另建限定名，不覆盖原主体。',source='xinwudaishi-50-wanghuan-identity',relation='adds')
add('qinfeng_fourprefecture_amnesty','柴荣赦免秦、凤、阶、成四州境内罪人',35,'乙卯，','成境内，',[('帝','在新占四州实施区域赦免')],when='955年十一月乙卯',place='秦、凤、阶、成四州',note='曲赦是特定地区赦免，不译为全天下大赦。')
sup('qinfeng_fourprefecture_amnesty',35,of,'乙卯。曲赦秦、鳳、階、成等州管內罪人，自顯德二年十一月已前，凡有罪犯，無問輕重，一切釋放。','《旧五代史》同日记赦免四州管内显德二年十一月以前的罪人，无论轻重。','保存该书列明的区域和时间范围，不扩大为所有后蜀地区罪犯获赦。',relation='adds')
add('shu_captives_choose_stay_leave','柴荣允许被俘后蜀将士选择留周或返乡，并分别给付待遇',35,'所获蜀将士，','给资装而遣之。',[('帝','规定被俘后蜀将士去留待遇')],when='955年十一月乙卯处置',place='秦凤战区及后周',description='愿留下的后蜀被俘将士获得优厚俸赐，愿离去的获给路费行装后遣返。这里记录政策，不假定全部人都选择留下，也不添加未载姓名或待遇金额。')
add('fourprefecture_extra_levies_removed','柴荣保留两税，取消后蜀在四州增设的其他科徭',35,'诏曰：',None,[('帝','取消四州两税以外的后蜀科徭')],when='955年十一月乙卯诏令',place='秦、凤、阶、成四州',note='保留二税征科，不写成四州从此完全免税免役。')

add('liurenshan_organizes_defense','刘仁赡镇定安排寿州防守，使民众稍安',36,'唐人闻周兵','众情稍安。',[('刘仁赡','在闻周军将至后照常部署防守')],when='955年十一月后周军将至时，具体日未载',place='南唐寿州',note='众情稍安为史书概述，不用来推定全体民众不再恐惧。')
add('tang_huainan_reinforcements','李璟派刘彦贞赴寿州，皇甫晖、姚凤屯定远',36,'唐主以神武统军','将兵三万屯定远。',[('唐主','安排两路救援部署'),('刘彦贞','任北面行营都部署，率二万兵赴寿州'),('皇甫晖','任应援使，与姚凤率三万兵屯定远'),('姚凤','任应援都监，与皇甫晖率军屯定远')],when='955年十一月周军将至时，具体任命日未载',place='寿州及定远',note='二万与三万是两路史载兵数，不加给每人各三万；到寿州方向趣不等于已抵城。')
add('songqiqiu_recalled','李璟召宋齐丘回金陵商议应对国难',36,'召镇南','谋国难，',[('唐主','召宋齐丘商议战事'),('宋齐丘','以镇南节度使身份被召回金陵')],when='955年十一月南唐应对周军时，具体召还日未载',place='金陵')
sup('songqiqiu_recalled',36,nw,'是時，宋齊丘為洪州節度使，景召齊丘還金陵，','《新五代史》也记李璟召洪州节度使宋齐丘回金陵。','洪州与主书镇南为地名、军额称法分别保留。')
add('yinchongyi_privy_appointment','李璟任殷崇义为吏部尚书、知枢密院',36,'以翰林承旨、',None,[('唐主','任殷崇义掌枢密事务'),('殷崇义','由翰林承旨、户部尚书转任吏部尚书、知枢密院')],when='955年十一月南唐应对周军时，具体日未载',place='南唐朝廷')

add('ligu_crosses_huai','李谷等架设浮桥，从正阳渡淮',37,'李谷等为浮梁，','自正阳济淮。',[('李谷','组织建浮桥并渡过淮河')],when='955年十二月奏报寿州战果以前，具体渡河日未载',place='正阳淮河',note='浮梁为浮桥，不当江西浮梁地名。')
add('shouzhou_victory_report','李谷奏报王彦超在寿州城下击败二千余南唐兵',37,'十二月，','于寿州城下，',[('李谷','奏报寿州城下战果'),('王彦超','在寿州城下击败南唐军')],when='955年十二月甲戌奏报，交战具体日未载',place='寿州城下',note='败二千余是击败该规模兵力，不直接改写斩首二千余；甲戌是奏报日。')
sup('shouzhou_victory_report',37,od,'甲戌，李穀奏，破淮賊二千人於壽州城下。','《旧五代史》同日记李谷奏报在寿州城下击败二千人。','人数二千与主书二千余详略保留，旧本纪未点名王彦超，不替旧本补字。')
add('shankou_victory_report','李谷奏报白延遇在山口镇击败一千余南唐兵',37,'己卯，',None,[('李谷','奏报山口镇战果'),('白延遇','以先锋都指挥使身份在山口镇击败南唐军')],when='955年十二月己卯奏报，交战具体日未载',place='山口镇',note='击败人数不等于阵亡人数，未把十一月来远镇捷奏和本次山口镇混为一场。')
sup('shankou_victory_report',37,od,'己卯，李穀奏，破淮賊千餘人於山口鎮。','《旧五代史》同日记山口镇击败千余人。','沿奏报时点，不外推交战日或未载唐军将领。')

add('zhengrenhui_dies','枢密使郑仁诲去世',38,'丙戌，','郑仁诲卒。',[('郑仁诲','以枢密使兼侍中、韩忠正公身份去世')],when='955年十二月丙戌',place='后周，具体地点未载',note='韩忠正公是封爵谥称，非姓名韩忠正；郑仁诲沿旧主体。')
sup('zhengrenhui_dies',38,od,'丙戌，樞密使鄭仁誨卒。','《旧五代史》同日记郑仁诲去世。','确年纪日同主书，其他生平待对应段落，不在此重写档案。')
claim('person',people['郑仁诲'],'death_year','郑仁诲于955年十二月丙戌去世。',38,span(38,'丙戌，','郑仁诲卒。'),'保存可追溯死亡事实；旧人物其他字段不覆盖。')
add('chairong_mourns_zheng','柴荣不顾日时忌讳，亲往吊唁郑仁诲',38,'上临其丧，',None,[('上','认为君臣情义重要，亲往哭悼郑仁诲'),('郑仁诲','身后获柴荣亲自吊唁')],when='955年十二月郑仁诲去世后，吊唁具体日未单列',place='郑仁诲丧所',note='岁道非便是近臣提出的日时禁忌顾虑，不译成道路无法通行。')
add('wuyue_tribute_chen','钱弘俶派陈彦禧向后周入贡',39,'吴越王','陈彦禧入贡，',[('吴越王','遣元帅府判官入贡'),('陈彦禧','奉吴越王命向后周入贡')],when='955年十二月条所记，具体日未载',place='吴越至后周',note='弘亻叔为电子底本拆字，沿已核钱弘俶主体，未新造弘亻叔人物。')
add('wuyue_attack_tang_order','柴荣下诏要求钱弘俶出兵攻南唐',39,'帝以诏',None,[('帝','下诏要求吴越攻南唐'),('吴越王','收到出兵攻南唐的诏令')],when='955年十二月陈彦禧入贡后，具体日未载',place='后周至吴越',note='诏令不等于吴越当天已出兵，实际进军另按后续956年段落录入。')

reviews={32:'李璟性情志向为史家评价，建州湖南及声援旧事仅添背景引用，不造955年同名新战。海路外交及把浅无确年，停止与反对分开。十一月乙未朔四名将领部署，十二将未补名单；韩令坤籍贯双书核对。',33:'唐末河损与南征疏导及柴荣预期分开，具体施行年未明留null，不把疏导命令当竣工。',34:'丁未确定刑赏讲话，先是拓街与迁坟依扩城背景另列，宽三十步不换现代米数，迁坟执行不同于此前葬埋限制。',35:'围城截援、戊申陷城俘五千、赵崇溥俘后死亡、乙卯四州曲赦及俘虏去留、两税外科徭取消完整拆分。癸丑为旧史奏报非夺城日；赵崇溥死亡不强定955或同日。原裸名王环是楚水军将领，本次新建后蜀凤州王环，籍贯和御者至节度履历由新史补证，不复用原人。',36:'刘仁赡安众防守、两路二万和三万兵、宋齐丘召回、殷崇义任枢密分开。宋洪州与镇南称法同人，原文将兵不是所有部队必已抵达。',37:'浮梁指桥，甲戌己卯均奏报日期；二千余和千余为击败规模非杀敌数，山口与来远未混。',38:'韩忠正公是爵谥不是另一个人；丙戌死日与后续亲吊分开，日时顾虑不译成交通问题。',39:'钱弘俶拆字沿既有主体，陈彦禧不据书目同名合并；入贡与命攻唐分开，未来吴越行动未提前录。'}
assert not (P/'publication.json').exists()
for n in range(32,40):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=955,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(32,40)],next_paragraph='zztj-v292-y0956-p001',next_volume=292,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原64—71行最后八段全部处理；快照含956年后事但未计覆盖。下一年界为原72—73行。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(32,40)],source_issues_review='李谷穀、钱弘俶拆字按旧主体；后蜀王环与楚国王环分档，主书威武与旧押送条凤翔职称、十二月授官与次年主书记任差异保留至后续。攻城与奏报时点分开。新史混叙955—956年，只取本次对应事实。',plain_language_review='首次逐条核对所有标题、人物、角色、事件、地点、时间与事实说明；讲话和史家评价、追叙和当前事件、命令和执行、败兵和死伤、保留两税和免额外科徭分清。引用保持原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
