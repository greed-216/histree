# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 293, year 957 paragraphs 1–6."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,48))
COMMIT='a3c2b1a6cf242bf4514a4d6934756f84abb3c1ce'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

for key in ['tongjian-293-956-year-end']:
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
main_sources = ['tongjian-293-956-year-end','tongjian-293-957-february-march']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0957-p001-p006',
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
lines = (ROOT / 'resources/derived/tongjian/293.txt').read_text().splitlines()
for n in range(1, 7):
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
        citation = f'卷293·显德四年（957年正月至二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0957_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'马在贵':'南唐楚州将领。956年四月在湾头堰被韩令坤击败，《旧五代史》记其所领万余众，未记其本人最后结局。生卒年未载。',
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

def event(code, title, n, quote, actors, when=None, note='', year=957, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='957年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_293_0957_' + code
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
        edge = 'participation_zztj_293_0957_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_293_0957_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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













ALIASES.update({'帝':'柴荣','上':'柴荣','北汉主':'刘承钧','景达':'徐景达','硃元':'舒元','朱元':'舒元','王环':'王环（后蜀凤州节度使）','许文縝':'许文稹'})
NEW_ALIASES={'段恒':[],'刘崇谏':['劉崇諫','崇谏'],'周廷构':['周廷構'],'刘仁赡妻（姓名未载）':[],'聂崇义':['聶崇義']}
NEW_DESCRIPTIONS={'段恒':'北汉内客省使。957年正月获任枢密使。姓名、职务与北汉年条核对，生卒年未载。','刘崇谏':'南唐寿州守将刘仁赡的幼子。《资治通鉴》记其夜渡淮北被捕，父亲命处以腰斩；《新五代史》记其趁父病谋与诸将出降。原书对前因记载不同，处刑具体日未载。','周廷构':'南唐寿州监军使。957年刘崇谏被父亲下令处死时，先哭求刘仁赡，又求其夫人相救，未获允许。生卒年未载。','刘仁赡妻（姓名未载）':'南唐刘仁赡的夫人，姓名未载。刘崇谏被下令处死时，周廷构向她求救，她认为军法名节不可徇私，催行处刑后才办理丧事。此条未明确其是否为崇谏生母，不建立母子关系。','聂崇义':'河南洛阳人，研习礼学，后汉乾祐年间任国子礼记博士。957年柴荣命其研究祭器祭玉制度、绘图呈报。《宋史》补载其在该年上图，朝廷另造祭器。生卒年未载。'}
jan='jiuwudaishi-117-january-957';feb='jiuwudaishi-117-february-957';new='xinwudaishi-32-liuchongjian';song='songshi-431-niechongyi-ritual';nh='xinwudaishi-70-tianhui-era'
add('northern_han_tianhui','北汉大赦并改元天会',1,'春，正月，','改元天会。',[('北汉主','在正月朔大赦并改元')],when='957年正月己丑朔',place='北汉')
sup('northern_han_tianhui',1,nh,'承鈞既立，始赦境內，改乾祐十年曰天會元年，','《新五代史》记刘承钧大赦，将乾祐十年改为天会元年。','该书用既立概述，没有正月己丑朔独立纪日；本条不将该段立七庙也提前定在同日。')
add('weirong_chancellor','刘承钧任卫融为中书侍郎、同平章事',1,'以翰林学士','同平章事，',[('北汉主','任命北汉宰相'),('卫融','从翰林学士获任中书侍郎、同平章事')],when='957年正月己丑朔条所记',place='北汉朝廷')
add('duanheng_privy','刘承钧任段恒为枢密使',1,'内客省使',None,[('北汉主','任命枢密使'),('段恒','从内客省使获任枢密使')],when='957年正月己丑朔条所记',place='北汉朝廷')
add('zhou_declines_prince_priority','柴荣认为功臣子弟尚未受恩，不宜先封幼子为王',2,Q[2]['text'],None,[('帝','回应宰相请求，认为不应先封幼子')],when='957年正月条所记，具体日未载',place='后周朝廷',note='未具名宰相不推范质等当场名单；拒先封的答语不等永不封王。')
add('shouchun_food_exhausted','寿春被围连年未下，城中粮食耗尽',3,'周兵围寿春，','城中食尽。',[],when='957年正月援军行动前的围城状态',place='寿春',note='连年概述956年以来围攻，不据此另造精确围城日数。')
add('zijin_tang_reinforcement','徐景达派许文稹、边镐、朱元援寿春，在紫金山设营',3,'齐王景达','晨夕相应，',[('景达','从濠州派援军'),('许文稹','以应援使、永安节度使身份领兵'),('边镐','以都军使身份领兵'),('硃元','以北面招讨使身份领兵')],when='957年正月丁未奏报前，具体进军日未载',place='濠州沿淮至紫金山',description='徐景达派许文稹、边镐、朱元率数万兵溯淮援寿春，在紫金山列十余寨，如连珠相接，与城内早晚用烽火呼应。数万、十余为史载概数，朱元复用此前改姓的舒元，许文稹与许文缜姓名异文沿既有记录。')
sup('zijin_tang_reinforcement',3,jan,'達留駐濠州，遣其將許文縝、邊鎬、朱元領兵數萬，溯淮而上，至紫金山，設十餘寨，與城內烽火相應。','《旧五代史》也记徐景达留濠州、遣三将率数万兵在紫金山设十余寨。','許文縝与已有许文稹沿同人异字，朱元沿舒元，不按繁简或姓名异字另建实体。')
add('shouchun_supply_corridor','南唐援军筑甬道，计划向寿春运粮',3,'又筑甬道','绵亘数十里。',[],when='957年正月李重进截击前，具体日未载',place='紫金山至寿春',note='欲运粮是目标，不记所有粮已顺利入城；数十里不转现代精确距离。')
sup('shouchun_supply_corridor',3,jan,'又築夾道數里，將抵壽春，為運糧之路，','《旧五代史》称运粮夹道长数里；《资治通鉴》称绵亘数十里。','长度口径不同并列保留，未强解释为同一测量点或取某数字定论。',relation='conflicts')
add('lichongjin_intercepts_aid','李重进截击寿春援军，夺两寨并奏报',3,'将及寿春，','重进以闻。',[('李重进','截击援军，夺取两寨，正月丁未奏报')],when='957年正月丁未奏报；具体战斗日未载',place='寿春附近',description='南唐援军将近寿春时被李重进截击。《资治通鉴》记大破援军、死亡五千人、夺两寨，李重进于丁未奏报。《旧五代史》记在寿州北破敌五千人，两书的死亡与破敌口径分别保留。')
sup('lichongjin_intercepts_aid',3,jan,'丁未，淮南道招討使李重進奏，破淮賊五千人於壽州北。','《旧五代史》记丁未李重进奏在寿州北破敌五千人。','破五千人与主书死五千人不是完全相同的统计口径；丁未是奏报日，交战未独立纪日。')
add('zhou_announces_return_huainan','柴荣诏告下月亲往淮上',3,'戊申，','诏以来月幸淮上。',[('帝','宣布次月前往淮上')],when='957年正月戊申下诏，计划二月出行',place='后周朝廷至淮上',note='来月幸是计划，本句不是当天已经抵达。')
sup('zhou_announces_return_huainan',3,jan,'戊申，詔取來月幸淮南。','《旧五代史》同记戊申宣布次月幸淮南。','诏令时点与后来实际出发分别录入。')
add('liurenshan_denied_sortie','刘仁赡请让边镐守城、自己出战，徐景达不准',3,'刘仁赡请','仁赡愤邑成疾。',[('刘仁赡','请求换人守城后率军决战，未获准而愤懑成病'),('边镐','被提议接守寿春，未记实际接守'),('景达','拒绝刘仁赡请求')],when='957年正月寿春援军阶段，具体日未载',place='寿春与南唐援军',note='计划让边镐守城不等已替换；病因愤懑为史书叙述，不作独立医学诊断。')
add('liuchongjian_captured','刘崇谏夜渡淮北被捕，刘仁赡命处以腰斩',3,'其幼子','左右莫敢救，',[('刘崇谏','夜渡淮北被小校捕获'),('刘仁赡','下令对幼子腰斩')],when='957年寿春守城条所记，具体夜间日期未载',place='寿春及淮河北岸',description='《资治通鉴》记刘仁赡幼子刘崇谏夜间乘船渡淮北，被小校捕获，刘仁赡命腰斩，左右不敢营救。该句没有明写已经投降后周；《新五代史》另记他趁父亲病重谋与诸将出降，前因分别保留。')
sup('liuchongjian_captured',3,new,'仁贍子崇諫幸其父病，謀與諸將出降，仁贍立命斬之，','《新五代史》称刘崇谏趁父病谋与诸将出降，刘仁赡立即命斩。','与《通鉴》夜渡淮北被捕的叙法不同，不能把两书拼成未载的完整阴谋。该传前文将亲征概写明年正月，与通鉴二三月行程不同，不据此给处刑定正月某日。',relation='conflicts')
relationship('刘仁赡','刘崇谏','父亲',3,'其幼子崇谏夜泛舟渡淮北，','其承上文刘仁赡，原文明确幼子；建立父亲方向，不另建反向儿子重复边。')
add('zhoutinggou_intercedes','周廷构哭求刘仁赡救刘崇谏，未获准',3,'监军使周廷构','仁赡不许。',[('周廷构','哭于中门请求免死'),('刘仁赡','拒绝监军救子请求')],when='957年刘崇谏处刑之前，具体日未载',place='寿春中门')
sup('zhoutinggou_intercedes',3,new,'監軍使周廷構哭于中門救之，不得，','《新五代史》也记周廷构哭求营救未成。','两书一致的是救援未成，不据该句补出匿名左右姓名。')
add('liurenshan_wife_refuses_pardon','刘仁赡夫人拒绝救子请求，催处刑后才办丧事',3,'廷构复使',None,[('周廷构','再次使人向刘仁赡夫人求救'),('刘仁赡妻（姓名未载）','认为军法与名节不可徇私，催促执行后办理丧事'),('刘崇谏','被执行处刑，随后办理丧事')],when='957年刘崇谏处刑时，具体日未载',place='寿春',description='周廷构又派人向刘仁赡夫人求救。她称并非不爱崇谏，但军法、名节不能徇私，否则刘氏将成为不忠之家，催促执行死刑，然后才办丧事。《通鉴》称将士感泣，这是史书记载的评价与反应，不编造在场全员名单。')
relationship('刘仁赡妻（姓名未载）','刘仁赡','妻子',3,span(3,'廷构复使','夫人曰：'),'夫人依守将上下文指刘仁赡妻，姓名未载；不能单凭对崇谏的爱推为生母。')
add('zhou_debates_ending_siege','有人以南唐援军仍强请求罢兵，柴荣犹疑',4,'议者','李谷寝疾在第。',[('帝','对撤军建议犹疑'),('李谷','当时患病在家')],when='957年二月丙寅问策前，具体日未载',place='后周朝廷及李谷家中',note='匿名议者不自动变成范质王溥本人；病名未载，不补病因。')
add('ligu_recommends_personal_campaign','柴荣派范质、王溥问计病中的李谷，李谷建议亲征',4,'二月，丙寅，',None,[('帝','派宰相询问，读到李谷奏疏后赞同'),('范质','奉命到李谷家中商议'),('王溥','奉命到李谷家中商议'),('李谷','上疏分析寿春将破，建议皇帝亲征')],when='957年二月丙寅',place='后周朝廷与李谷家中',description='柴荣派范质、王溥到病中的李谷家商议。李谷上疏认为寿春已危困，皇帝亲征可振奋将士、震慑援军，促城内认清败局，柴荣阅后欣悦。必可下是李谷预测，不把建议当成本日已经攻克寿春。')
add('niechongyi_ritual_diagrams','柴荣命聂崇义研究祭器、祭玉制度并绘图',5,Q[5]['text'],None,[('帝','下令重新制造祭器祭玉，命博士考制度绘图'),('聂崇义','受命研究礼器制度并绘图')],when='957年二月庚午',place='后周朝廷',note='更造为制造命令，本句未给每件器物完成日。')
sup('niechongyi_ritual_diagrams',5,song,'先是，世宗以郊廟祭器止由有司相承製造，年代浸久，無所規式，乃命崇義檢討摹畫以聞。四年，崇義上之，乃命有司別造焉。','《宋史》补记柴荣认为祭器缺乏规范，命聂崇义检讨绘图；显德四年上图后命另造。','任命与呈图是两个动作；宋传只给四年，不强定上图也在庚午。')
add('niechongyi_submits_diagrams','聂崇义于显德四年呈交祭器图，朝廷命另造祭器',5,'四年，崇義上之，','乃命有司別造焉。',[('聂崇义','呈交检讨绘制的祭器图'),('帝','收到图后命有司另造祭器')],source=song,when='《宋史》显德四年（957年），具体呈图日未载',place='后周朝廷',note='补书独立动作；此处不是后来建隆三年进《三礼图》的日期。')
claim('person',people['聂崇义'],'biography','《宋史》称聂崇义为河南洛阳人，少研三礼，后汉乾祐中任国子礼记博士并校定《公羊春秋》。',5,'聶崇義，河南洛陽人。少舉《三禮》，善《禮》學，通經旨。漢乾祐中，累官至國子《禮記》博士，校定《公羊春秋》，刊板於國學。','早年经历属追述，不当957年新任旧汉博士。',source=song)
add('wangpu_capital_regent','柴荣命王朴权东京留守、判开封府',6,'甲戌，','兼判开封府事，',[('帝','亲征前安排东京留守'),('王朴','权东京留守兼判开封府事')],when='957年二月甲戌',place='东京开封')
sup('wangpu_capital_regent',6,feb,'甲戌，以樞密副使王樸為權東京留守兼判開封府，','《旧五代史》同日记王朴权东京留守、判开封府。','这是此次亲征留守安排，不与前年的旧任重复当同一事件。')
add('zhangmei_palace_inspection','柴荣命张美为大内都巡检',6,'以三司使张美','为大内都巡检，',[('帝','安排大内巡检'),('张美','以三司使兼大内都巡检')],when='957年二月甲戌',place='东京大内')
sup('zhangmei_palace_inspection',6,feb,'以三司使張美為大內都巡檢。','《旧五代史》同记张美为大内都巡检。','同甲戌任命条，不混同韩通的京城内外都巡检。')
add('hantong_city_inspection','柴荣命韩通为京城内外都巡检',6,'以侍卫都虞候韩通','为京城内外都巡检。',[('帝','安排京城内外巡检'),('韩通','以侍卫都虞候兼京城内外都巡检')],when='957年二月甲戌',place='东京城内外')
add('zhou_departs_second_campaign','柴荣从大梁出发再次南征',6,'乙亥，','帝发大梁。',[('帝','从大梁出发')],when='957年二月乙亥',place='大梁向淮南')
sup('zhou_departs_second_campaign',6,feb,'乙亥，車駕發京師。','《旧五代史》同记二月乙亥柴荣发京师。','出发与后来到下蔡及渡淮分别录入。')
add('zhou_builds_fleet_background','柴荣返京后在汴水造数百战舰，弥补水军弱势',6,'先是周与唐战，','造战舰数百艘，',[('帝','因水军不如南唐而在京西汴水组织造舰')],year=None,when='956年寿春返京后至957年二月再次出征前，具体造舰起止日未载',place='大梁城西汴水',note='先是为上次返京后准备过程，不把数百舰全算乙亥当日造出；船数是概数。')
add('southern_soldiers_train_zhou_sailors','柴荣命南唐降卒教授北方士兵水战，数月后能力提高',6,'命唐降卒','殆胜唐兵。',[('帝','命南唐降卒传授水战技能')],year=None,when='956年返京后至957年二月再次出征前的数月训练',place='大梁汴水',description='柴荣命南唐降卒教北方士兵水战，数月后周军能纵横出没，史书称几乎胜过南唐水军。教官与学员未具名，比较为史家评价，不能造精确训练人数和每次演练成绩。')
add('wanghuan_leads_naval_force','王环率数千周军水师自闵河沿颍入淮',6,'至是命右骁卫',None,[('帝','命王环带水军进淮'),('王环','以右骁卫大将军身份率水军数千进淮')],when='957年二月再次亲征时，具体发船日未载',place='闵河沿颍水至淮河',note='复用955年被俘、956年获右骁卫职的后蜀王环，非早年楚水军王环。数千为概数，闵河底本地名不擅改。')
reviews={1:'北汉正月朔大赦改元与两任命分开，刘承钧沿核定别名；新史乾祐十年天会元年印证，但七庙留到后段。',2:'匿名宰相请求不造人物，未先封幼子不是永不封；功臣子未恩为答语。',3:'救援、营寨粮道、截击丁未奏、戊申次月计划分阶段。旧夹道数里与主数十里，破五千与死五千分口径。刘出战被拒，子渡北被捕与新谋出降分源，不拼造全部阴谋。妻明确未明母，不造母子；父亲方向确认。',4:'撤军议者匿名，李谷病居非亲征；丙寅派宰相问策、李疏预测与柴欣悦，不把预测写成此日克城。',5:'庚午命造器考图与宋显德四年上图另造区分，洛阳早年汉博士为追述，不与建隆三年进图混同。',6:'甲戌王朴留守张美大内韩通城内外职分清，乙亥出发不等到下蔡。汴水造舰及降卒训练为上次返京以来多月，年份留null；右骁王环沿956任命复用后蜀同人。'}
assert not (P/'publication.json').exists()
for n in range(1,7):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=957,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph=Q[7]['id'],next_volume=293,next_year=957,supplements=supplements,excluded_non_body=[],coverage='原65—70行首六段连续正文，后续未计。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,7)],source_issues_review='许文稹与許文縝沿既有异字同人，朱元舒元、右骁王环身份回查；刘崇谏前因两书叙法不同，数里数十里、死亡与破敌数字口径并列保留。闵河原名保留，纸本及异文待核。',plain_language_review='首次逐条核对人物、标题正文、角色关系和事实解释。预测和军令计划不当已成事实；史家评价明示来源；匿名夫人不造实名或母子，建造训练跨时追述不固定出发日，原文保留底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
