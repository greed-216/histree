# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 23–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,58))
COMMIT='ea70f60f767f3688984c5ec3aa3a578a6a95317a'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

for key in ['tongjian-293-956-may-june']:
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
main_sources = ['tongjian-293-956-may-june','tongjian-293-956-hunan-yangzhou-withdrawal']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0956-p033-p040',
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
for n in range(33, 41):
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
        citation = f'卷293·显德三年（956年六月至七月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0956_05_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=956, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='956年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_293_0956_' + code
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
        edge = 'participation_zztj_293_0956_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_293_0956_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','硃元':'舒元','朱元':'舒元','李平':'杨讷','符氏':'符氏（柴荣宣懿皇后）'})
NEW_ALIASES={'刘光委':['劉光委'],'邓氏（周行逢妻）':['鄧氏（周行逢妻）'],'唐德':[],'仁及':[]}
NEW_DESCRIPTIONS={
'刘光委':'湖南邵州刺史。《通鉴》记周行逢派人探察诸州，收到他多宴饮的报告后怀疑谋害自己，将刘召回杀死。是否确有谋反没有证据，死亡具体年日未载。',
'邓氏（周行逢妻）':'周行逢的妻子，封郧国夫人，姓名未载。《通鉴》称其刚决、善理家产，劝丈夫减少严刑，后来居村墅不回府，并亲自输税，要求节度使率先守例。与其他邓氏分档。',
'唐德':'周行逢的女婿。曾请求补吏，周认为其不适任而不予官职，给耕牛、农具让其务农。生卒年与此事确切年份未载。',
'仁及':'受周行逢信任的僧人，参与军府事务并获加检校司空。《通鉴》还记其娶数妻、出入导从如王公。具体任用年日、生卒年及各妻姓名未载。'}
ap='songshi-483-zhouxingfeng-appointment';gov='songshi-483-zhouxingfeng-governance';old='jiuwudaishi-116-july-956'
add('zhuyuan_jiangbei_command','李璟听朱元论用兵后，命其领军收复江北诸州',33,Q[33]['text'],None,[('唐主','认为朱元有用兵能力，命领军'),('硃元','以驾部员外郎身份奏论并获军令')],when='956年六月寿州南寨失利之后、七月条以前，具体日未载',place='南唐朝廷至江北',note='朱元沿既有舒元改姓记录，命复江北不是当时已全部收复。')
add('zhou_hunan_official_appointment','柴荣正式任周行逢为武平节度使，制置武安、静江军务',34,'秋，七月，','制置武安、静江等军事。',[('帝','正式授周行逢节度与制置职务'),('周行逢','获任武平节度使，兼制两地军务')],when='956年七月辛卯朔',place='武平、武安、静江',note='这是朝廷正式任命，与此前入朗州自称两军留后不同。')
sup('zhou_hunan_official_appointment',34,ap,'世宗乃授行逢郎州大都督、武平軍節度、製置武安靜江等州軍事兼侍中，','《宋史》也记柴荣授周行逢武平节度、制置武安静江并兼侍中。','郎字原保，主书朗州与原电子异字不另建地点；宋传未独立列辛卯朔。')
add('zhou_reforms_hunan_tax_officials','周行逢接管湖湘后，去除马氏横赋并选廉平官员',34,'行逢既兼总湖、湘，','为刺史、县令。',[('周行逢','整顿赋税、去除为害官民，选廉平刺史县令')],year=None,when='956年兼总湖湘之后的治理概述，具体各项实施年日未载',place='湖南',note='横赋是额外不当征敛，不表示一切正常税收全免；皆去之不都解释成全部处死。')
sup('zhou_reforms_hunan_tax_officials',34,gov,'行逢在鎮，盡心為治，辟署官屬，必取廉介之士。','《宋史》也评价周行逢治理时选用廉介官员。','在镇为整个任期概述，不把任用全强定956七月辛卯。')
add('zhou_strict_military_discipline','周行逢严惩骄横旧部，将士怨惧',34,'朗州民、夷杂居，','众怨怼且惧。',[('周行逢','以严法约束刘言王逵旧部')],year=None,when='周行逢统治湖南期间的概述，具体起止年未载',place='朗州及湖南',note='民夷为史载群体称谓，不据此定现代族群；将士怨惧为史家概述，不作每人心理普查。')
add('zhou_kills_plotting_officers','周行逢在诸将宴会上拘捕谋乱者，斥责后当场杀死',34,'有大将与其党十馀人','乐饮而罢。',[('周行逢','宴会上拘谋乱者并当场杖杀，随后安抚其余将领')],year=None,when='周行逢在湖南任职期间，具体年日未载',place='诸将宴席，具体地点未载',description='《通鉴》记一名大将与同党十余人谋乱，周行逢得知后在宴席拘捕，斥责自己节用实库是为将士，当场打死他们。其余将领震惧，他又说其他人无罪，继续宴饮。姓名与精确总人数未载，不扩大为全部将领。')
claim('person',people['周行逢'],'evaluation','《通鉴》称周行逢善察隐事，常预先查获部下谋乱叛逃，部众因此凛惧，但也多疑残忍。',34,span(34,'行逢多计数，','常散遣人密诇诸州事，'),'这是史家对多次行为的概述，不造每次未具名谋乱案件或保证侦察全无误报。')
add('zhou_spies_on_prefectures','周行逢常派人秘密探察诸州事务',34,'然性猜忍，','常散遣人密诇诸州事，',[('周行逢','派人秘密探察地方事务')],year=None,when='周行逢任内习惯，具体年日未载',place='湖南诸州',note='密探未具名，不编造情报机构组织和具体名单。')
add('liuguangwei_killed_on_suspicion','周行逢因刘光委多宴饮而疑其谋害，召回并杀死',34,'其之邵州者，','即召还，杀之。',[('周行逢','据宴饮报告起疑，召杀邵州刺史'),('刘光委','因多宴饮被怀疑而遭杀')],year=None,when='周行逢任内，具体死亡年日未载',place='邵州至召还处',note='多宴饮是报告，欲谋我是周行逢推断，不记成谋反已经查实。')
add('zhangwenbiao_returns_hengzhou','张文表怕获罪，请回衡州，厚献馈物并谨事左右',34,'亲卫指挥使、','由是得免。',[('张文表','请返任所并通过厚献等求免祸'),('周行逢','准张文表回治所')],year=None,when='周行逢统湖南期间，具体年日未载',place='衡州及湖南军府',note='得免是在当时免遭其猜忌，不表示张文表后来终身安全或永不获罪。')
dp=person('邓氏（周行逢妻）',34,'周行逢妻、郧国夫人，史书称其刚决善理家产',span(34,'行逢妻郧国夫人邓氏，','善治生，'))
claim('person',dp,'evaluation','《通鉴》形容邓氏外貌不美，却性情果断、善于管理家产。',34,'陋而刚决，善治生，','这属于史家对外貌和能力的评价，展示明确来源，不据外貌判断其行动价值。')
relationship('邓氏（周行逢妻）','周行逢','妻子',34,span(34,'行逢妻郧国夫人邓氏，','善治生，'),'原文明记妻，按方向邓氏是周行逢的妻子；郧国夫人为封号，不推作籍贯。')
add('deng_criticizes_harsh_law','邓氏劝周行逢法太严会疏远人心，周不听',34,'尝谏行逢','汝妇人何知！”',[('邓氏（周行逢妻）','劝丈夫减少严刑'),('周行逢','以轻蔑回答拒绝意见')],year=None,when='周行逢任内旧事，具体年日未载',place='湖南府中')
add('deng_moves_to_country_estate','邓氏不悦，往村墅看田后不回府，屡拒周行逢迎请',34,'邓氏不悦，','不至。',[('邓氏（周行逢妻）','到村墅后不再回府'),('周行逢','屡遣人迎请未成')],year=None,when='劝谏争执之后，具体年日未载',place='湖南府舍至村墅',note='去村不等离婚或亡故，不补具体庄园坐标。')
add('deng_pays_tax_and_refuses_return','邓氏亲输税，要求节度使先守法率下，并因担忧滥杀拒回府',34,'一旦，自帅僮仆',None,[('邓氏（周行逢妻）','率僮仆输税，要求丈夫率先遵守并拒绝回府'),('周行逢','劝妻回府，被其拒绝')],year=None,when='邓氏住村墅以后，具体输税年日未载',place='湖南税所及村墅',description='邓氏亲率僮仆输税，说明税属官府，节度使家须先守例才可率下。她提醒周行逢过去任里正曾代人缴税避罚，并因担忧滥杀会引变乱、村居便于避难而拒回府；僚属认为其言直，劝周采纳。旧里正经历是她回忆，叛乱风险是她判断，不作当前已经发生的事实。')
add('zhou_rejects_tangde_office','周行逢拒女婿唐德求官，给耕牛农具让其务农',35,Q[35]['text'],None,[('唐德','以女婿身份求补吏'),('周行逢','认为唐不适任，给农具耕牛而不任官')],year=None,when='周行逢在镇期间旧事，具体年日未载',place='湖南')
relationship('周行逢','唐德','岳父',35,'行逢婿唐德求补吏，','原称婿在此指女婿，因此周行逢是唐德岳父；妻女姓名不明，未补匿名姓名。')
sup('zhou_rejects_tangde_office',35,gov,'有女婿求補吏，不許，返給以耒耜，','《宋史》也记拒绝女婿求官、给农具归农。','宋传未写唐德名，不擅补到摘录；此事未明确定956年当天。')
claim('person',people['周行逢'],'biography','《通鉴》回述周行逢年轻时犯法受黥，服役辰州铜坑。',36,'行逢少时尝坐事黥，隶辰州铜坑，','少时为旧事，具体年月未载，不能当956年新受刑。')
add('zhou_refuses_remove_tattoo','有人建议周行逢除去面上刑痕，他举黥布为例而不羞',36,'或说行逢：',None,[('周行逢','拒把旧刑痕视为耻辱')],year=None,when='周行逢为地方长官后，具体年日未载',place='湖南',note='汉黥布是历史类比，没有参与这次对话；药灭只是匿名建议，不当作已实际治疗。')
add('hunan_honorary_titles_proliferate','《通鉴》概述刘言、王逵以来湖南因战功授检校三公者众多',37,'自刘言、','检校官至三公者以千数。',[],year=None,when='刘言王逵至周行逢时期的累积概述，具体授号批次未载',place='湖南',note='以千数为史载数量概述，三公为检校加衔，不等同全国实任三公同时数千人。')
claim('person',person('徐仲雅',37,'前天策府学士，自马希广被废后不再任职',span(37,'前天策府学士徐仲雅，','杜门不仕，')),'biography','徐仲雅在马希广被废后闭门不仕。',37,span(37,'前天策府学士徐仲雅，','杜门不仕，'),'马希广之废为旧事起点，不把退隐开始硬定956年。')
add('zhou_forces_xuzhongya_post','周行逢慕徐仲雅，署节度判官，徐屡辞，周强召仍不接受',37,'行逢慕之，','终辞不取，',[('周行逢','署任判官并强迫其接受文牒'),('徐仲雅','认为不应成为昔日下属的幕吏，拒绝赴职受牒')],year=None,when='周行逢统湖南时期，具体年日未载',place='湖南军府',note='署任与真正接受职务分开，不写徐已经就任判官；辞疾不证明实患病。')
add('xuzhongya_exiled_recalled','周行逢因拒任放徐仲雅到邵州，随后召回',37,'行逢怒，','既而召还。',[('周行逢','放徐到邵州又召回'),('徐仲雅','遭放逐后被召回')],year=None,when='拒受判官文牒之后，具体年日未载',place='湖南军府至邵州')
add('xuzhongya_mocks_inflated_titles','周行逢生日夸威望，徐仲雅用遍地太保司空讥讽，再被放邵州',37,'会行逢生日，','竟不能屈。',[('周行逢','夸兼镇三府威望，因讥讽再放逐徐'),('徐仲雅','借检校虚衔遍布讥讽周而不屈')],year=None,when='周行逢在任某次生日，具体年份和月日未载',place='湖南军府至邵州',note='生日未写日期，不推生年月日；四邻畏我是周的自问，遍地司空为讽语而非精确统计。')
add('renji_privileges','周行逢信任僧仁及，使其参与军府并加检校司空',37,'有僧仁及，',None,[('周行逢','信任仁及并给予军府职权加衔'),('仁及','参与军府事务、获检校司空，史书记其数妻及王公般导从')],year=None,when='周行逢任内概述，具体年日未载',place='湖南军府',note='数妻未具名，不创建虚构妻子名单；僧人加检校司空与国家实任司空不同。')
add('fu_empress_dies','柴荣宣懿皇后符氏去世',38,Q[38]['text'],None,[('符氏','以后周宣懿皇后身份去世')],when='956年七月辛亥',place='后周，具体地点未载',note='沿954年初立皇后同人，与后来继立的另一符氏区分。')
sup('fu_empress_dies',38,old,'辛亥，皇后符氏薨。','《旧五代史》同日记符皇后去世。','同段七月标题核定月份，不新增一名裸符氏人物。')
claim('person',people['符氏（柴荣宣懿皇后）'],'death_year','柴荣宣懿皇后符氏于956年七月辛亥去世。',38,Q[38]['text'],'死亡年日作为有出处事实，不覆盖旧档案其他身世字段。')
add('zhuyuan_takes_shuzhou','朱元攻取舒州，郭令图弃城逃走',39,'唐将硃元取舒州，','弃城走。',[('硃元','攻取舒州'),('郭令图','弃守舒州逃走')],when='956年七月条所记，具体夺城日未载',place='舒州',note='朱元复用舒元，与前周军初取和夜复城是不同阶段。')
add('liping_takes_qizhou','李平攻取蕲州',39,'李平取蕲州。','李平取蕲州。',[('李平','攻取蕲州')],when='956年七月条所记，具体日未载',place='蕲州',note='李平沿已录杨讷改名记录，不与此前杀知州的李福合并。')
add('tang_appoints_zhu_li','李璟任朱元为舒州团练使、李平为蕲州刺史',39,'唐主以元','蕲州刺史。',[('唐主','任命两名复城将领'),('硃元','任舒州团练使'),('李平','任蕲州刺史')],when='956年七月两州恢复之后，具体任命日未载',place='舒州、蕲州')
add('zhuyuan_takes_hezhou','朱元随后攻取和州',39,'元又取和州。',None,[('硃元','取得和州')],when='956年七月舒州任命前后，具体日未载',place='和州',note='又表后续动作，不把舒和蕲三个州战役全定同日。')

add('tang_coercive_fiscal_background','《通鉴》回述南唐以茶盐强征粟帛及淮南营田使民困苦',40,'初，唐人','民甚苦之。',[],year=None,when='后周南征前的南唐制度背景，具体起止年未载',place='南唐淮南',description='《通鉴》称南唐把茶盐强加给百姓，征取粟帛，称为博征，又在淮南兴营田，使民众困苦。这里保留史书记载的财政方式，不误译为自愿市场交换，也不编造每户摊派金额。')
add('huainan_people_form_white_armor','周军侵掠使迎劳民众失望，人们筑堡自守，称白甲军',40,'及周师至，','多复为唐有。',[],when='956年淮南战事期间的概述，具体各次行动日未载',place='淮南山泽与各州',description='《通鉴》记淮南民众初以牛酒欢迎周军，周将帅却侵掠，使民失望。民众聚集山泽、建堡自守，持农具、用纸为甲，被称白甲军；周兵多次讨伐失利，先取诸州许多又归南唐。群体与战果都是概述，未补领导人名单，也不把白甲军直接等同南唐正规军。')
add('tang_camps_zijin','南唐援兵驻紫金山，与寿春城内烽火相应',40,'唐之援兵','烽火相应。',[],when='956年寿春围攻时，具体设营日未载',place='紫金山与寿春',note='此处主书未具名所有援军统帅，不从后段名单补成当前当场参与者。')
add('xiangxun_requests_concentration','向训请集中广陵军攻寿春，柴荣批准',40,'淮南节度使向训','诏许之。',[('向训','请求先并力取寿春，再图进取'),('帝','批准集中兵力方案')],when='956年七月弃扬州回寿春之前，具体奏日未载',place='扬州至后周朝廷',note='俟克城是未来计划，本段寿春并未攻下。')
add('xiangxun_withdraws_yangzhou_orderly','向训封府库移交扬州，安排地方牙将巡城后撤军，民众送行',40,'训封府库','负糗Я以送之。',[('向训','封库移交、令牙将分区巡城后撤军')],when='956年七月回军寿春时，具体撤军日未载',place='扬州至寿春',note='糗Я字形异常保留引用，按送行粮食理解，不猜完整字或实际总量；秋毫不犯是史书对这次撤军纪律的评价，不抹去此前侵掠记载。')
sup('xiangxun_withdraws_yangzhou_orderly',40,old,'淮南節度使向訓自揚州班師，回駐壽春。','《旧五代史》同记向训放弃扬州并回驻寿春。','该书叙经年未下为围攻久的概述，不因此把整个条目硬改次年。')
sup('xiangxun_withdraws_yangzhou_orderly',40,old,'向訓請棄揚州，並力以攻壽春，乃封府庫付主者，遣淮南舊將按巡城中，秋毫不犯而去。','旧史所引马令《南唐书》也记封库移交和巡城保民再撤。','明确为引书依赖，非另得马令底本；参与旧将名字未载。')
add('chuzhou_garrison_withdraws','滁州守将也弃城，军队合赴寿春',40,'滁州守将亦',None,[],when='956年七月并军寿春时，具体日未载',place='滁州至寿春',note='守将未具名，不自动写此前任知州的马崇祚亲自主持弃城。')

reviews={33:'硃元沿舒元同人，谈策与受命复江北不等完成。',34:'辛卯朔仅用于正式授职，随后除横赋、任廉吏、军纪、宴擒杀、密察与疑杀刘、张回衡、邓谏去村输税全部拆分，具体年不明留null。嫌谋是猜测，郧国封号非籍贯，邓拒归非离婚。',35:'唐德女婿关系与求官被拒、赠农具分开，职位不给不等亲族关系断绝；宋未具名只印同事，不把唐妻母推为邓。',36:'少时黥铜坑为旧经历，药除建议与拒耻态度不造真实治疗；黥布是引用历史人物非在场。',37:'检校三公以千为累计荣衔非国家实任，徐马希广废后退隐、署而拒、两次放逐及讽生日分开，不反推周生日。仁及信任、军府参与和妻导从概述不造匿名妻谱。',38:'七月辛亥宣懿符后死沿既有长姐主体，不和继立另一符后合，旧同日核。',39:'朱与李改姓名沿既有舒元杨讷，舒取郭走、蕲取、两任、和取分阶段，不强都同日。',40:'唐财政旧制year null，初迎劳与周侵掠、白甲自固、州多复唐、紫金烽火、向奏许可、封库巡城撤扬、民送与滁撤完整处理。糗异常不改原，不把当次好军纪当此前全部不侵掠；先克寿春是计划。'}
assert not (P/'publication.json').exists()
for n in range(33,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph=Q[41]['id'],next_volume=293,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原38—45行连续八段，含湖南任内概述与旧事；以主年条处理但不把全部概述定在本年，后续未计。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,41)],source_issues_review='糗Я异常字原保；大量任内概述无独立年月留null。朱元李平按改姓名记录复用，不另建；僧及女子未知实名用称谓，虚衔实职和婚姻方向分清，纸本待核。',plain_language_review='首次逐条检查人物事件角色与解释，作者评价、猜疑和讽语不当已证事实；治理和滥杀并列保留。血缘婚姻只建明示，乡村输税和未知年月、军事计划和撤军执行区分，原文不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
