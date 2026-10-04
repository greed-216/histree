# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 942 paragraphs 9–14."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,41))
specs=[(d.name,d,'38b9b714bc0e6ccbbdf52f39b27d882bbd9c97f2','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-942-spring']:
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
main_sources = ['tongjian-283-942-spring','tongjian-283-942-southern-succession','tongjian-283-942-may']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0942-p009-p014',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-942-southern-succession':'卷283·天福七年四月·南汉继承','tongjian-283-942-may':'卷283·天福七年五月及随后记载','jiuwudaishi-080-942-remonstrance':'卷80·晋高祖本纪·天福七年四月','jiuwudaishi-080-942-may':'卷80·晋高祖本纪·天福七年五月','jiuwudaishi-096-zheng-shouyi':'卷96·郑受益传','xinwudaishi-065-liu-yan-death':'卷65·南汉世家·刘龑去世','xinwudaishi-065-liu-bin-succession':'卷65·南汉世家·刘玢继位'}
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
lines = (ROOT / 'resources/derived/tongjian/283.txt').read_text().splitlines()
for n in range(9, 15):
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
    labels={'tongjian-283-942-southern-succession':'卷283·天福七年四月·南汉继承','tongjian-283-942-may':'卷283·天福七年五月及随后记载','jiuwudaishi-080-942-remonstrance':'卷80·晋高祖本纪·天福七年四月','jiuwudaishi-080-942-may':'卷80·晋高祖本纪·天福七年五月','jiuwudaishi-096-zheng-shouyi':'卷96·郑受益传','xinwudaishi-065-liu-yan-death':'卷65·南汉世家·刘龑去世','xinwudaishi-065-liu-bin-succession':'卷65·南汉世家·刘玢继位'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '四月至五月条下及追述'
        citation = f'卷283·后晋天福七年（942；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0942_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=942, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='942年年初条下，具体日期未载'
    key = 'event_zztj_283_0942_' + code
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
        edge = 'participation_zztj_283_0942_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0942_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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

ALIASES.update({'帝':'石敬瑭','李涛':'李涛（后晋宋初官员）','汉高祖':'刘岩','高祖':'刘岩','弘度':'刘弘度','玢':'刘弘度','弘熙':'刘弘熙','弘昌':'刘弘昌','从谠':'郑从谠','王翻':'王翷'})
NEW_DESCRIPTIONS={
'杨洪':'张彦泽部下将领，逃离后在陕州被抓。942年《资治通鉴》记张彦泽醉中截断其手足并斩首。出生年未载。',
'郑受益':'唐宰相郑从谠的侄子，郑处诲之子。后晋右谏议大夫。942年四月上疏请求追究张彦泽虐民杀人的罪责。生卒年及后续履历本批未补定。',
'郑处诲':'郑从谠的兄长，郑受益的父亲。《旧五代史》记他曾任汴州节度使。生卒年未载。',
'王翷':'南汉右仆射兼西御院使。刘岩病重时与他商议把刘弘度、刘弘熙调往外地，立刘弘昌；计划经萧益劝阻而停止。《新五代史》同次谋划写王翻，姓名异字保留。',
'赵氏（刘弘度母）':'南汉刘弘度的母亲，原为昭仪。942年刘弘度即位并改名玢，尊她为皇太妃。姓名及生卒年未载。',
'刘氏（石敬瑭太妃）':'后晋皇太妃。942年五月乙巳被尊为皇太后。《资治通鉴》称她是石敬瑭的庶母，《旧五代史》所引徐无党注称生母，关系异说保留。姓名及出生年未载。',
'张麟':'后晋刑部郎中。942年四月庚申与李涛、麻麟、王禧一起上疏请求追究张彦泽罪责。生卒年未载。',
'麻麟':'后晋员外郎。942年四月庚申与李涛、张麟、王禧一起上疏请求追究张彦泽罪责。生卒年未载。',
'王禧':'后晋员外郎。942年四月庚申与李涛、张麟、麻麟一起上疏请求追究张彦泽罪责。生卒年未载。'}
NEW_ALIASES={'杨洪':['楊洪'],'郑受益':['鄭受益'],'郑处诲':['鄭處誨'],'王翷':['王翻'],'赵氏（刘弘度母）':['赵昭仪','趙昭儀'],'刘氏（石敬瑭太妃）':[],'张麟':['張麟'],'麻麟':[],'王禧':[]}
ann='jiuwudaishi-080-942-remonstrance';bio='jiuwudaishi-096-zheng-shouyi';may='jiuwudaishi-080-942-may';new='xinwudaishi-065-liu-bin-succession';death='xinwudaishi-065-liu-yan-death'
# Additional actors known by name only in an independent source.
def participant(code,name,n,quote,role,source):
 pk=person(name,n,role,quote,source=source);key='participation_zztj_283_0942_'+code+'_'+pk
 assert not any(x['key']==key for x in B['person_events'])
 B['person_events'].append(dict(key=key,person_key=pk,event_key=E[code],role=role,status='draft'))
 claim('person_event',key,'role',name+'：'+role+'。',n,quote,'姓名和参与动作来自此独立原文，不以主书等字推定其他人的名单。',source=source)
add('zhang_unauthorized_attack','张彦泽在泾州擅自出兵攻打胡人，所派兵众败亡',9,'张彦泽在泾州，','兵皆败没，',[('张彦泽','擅自发兵攻打胡人，部队败亡')],year=None,when='张彦泽任泾州节度使期间，942年离任以前，具体年月未载',place='泾州',note='在镇往事不强定三月；胡人未具名，不补兵数或民族。')
add('zhang_requisitions_horses','张彦泽征调百姓马匹一千多匹，补充败亡后的军力',9,'调民马','以补之。',[('张彦泽','征调百姓马匹补充败亡损失')],year=None,when='张彦泽任泾州节度使期间，败亡后，具体年月未载',place='泾州',note='千余为原文马匹概数，不补马价或士卒数。')
add('zhang_kills_yang_hong','张彦泽返程到陕州，抓获杨洪，醉中断其手足并斩首',9,'还至陕，','而斩之。',[('张彦泽','抓获逃离的杨洪并杀害'),('杨洪','在陕州被抓并遭断手足斩首')],when='942年张彦泽离任返程中，具体日期未载',place='陕州',note='杨洪为亡将，不推杀害获得合法审判或其他同名身份。')
add('wang_zhou_reports_abuses','王周奏报张彦泽贪残违法二十六条，百姓逃散五千多户',9,'王周奏','五千馀户。',[('王周','向朝廷报告张彦泽违法行为'),('张彦泽','被王周奏报二十六条违法行为')],when='942年王周接任泾州以后，具体日期未载',place='泾州',note='二十六条和五千余户是奏报内容，不补逐条清单或把户数当人数。')
add('shi_spares_zhang_initially','石敬瑭因张彦泽有军功、与杨光远联姻，暂不追究罪责',9,'彦泽既至，',None,[('帝','以军功和联姻关系为由不追究'),('张彦泽','到朝廷后未受追究')],when='942年张彦泽抵朝廷后、四月谏争以前，具体日期未载',note='联姻双方及婚配人未载，不据此建立杨光远与张彦泽直接夫妻或血亲关系。')
add('zheng_shouyi_petition','郑受益上疏，要求依法追究张彦泽杀人罪责',10,'夏，四月，','以湔洗圣德。”',[('郑受益','上疏请求追究张彦泽罪责'),('帝','收到郑受益劝谏')],when='942年四月己未',description='郑受益上疏指出，把张式交回张彦泽，使张彦泽更加肆无忌惮。他转述朝野议论：皇帝收了张彦泽献上的一百匹马，才纵容其行为，并请求依法追究张彦泽的罪责。',note='收百匹马为郑受益转述中外议论，不当作已经独立证实的收受事实；去年张式事件不重造942年事件。')
sup('zheng_shouyi_petition',10,ann,'己未，右諫議大夫鄭受益兩疏論張彥澤在涇州之日，違法虐民，支解掌書記張式、部曲楊洪等，請下所司，明申其罪。','《旧五代史》记郑受益同日两次上疏，请求查明张彦泽虐民及杀张式、杨洪等罪责。','两疏来自本纪补充，主书摘出奏词；不当成两个已经核实相隔日期的奏疏。',relation='adds')
add('shi_retains_zheng_memorial','石敬瑭将郑受益奏疏留在宫中，没有交付处理',10,'疏奏，','留中。',[('帝','将奏疏留中'),('郑受益','奏疏未被交付处理')],when='942年四月己未奏疏提交后',note='留中不能解释为已批准请求。')
relationship('从谠','郑受益','叔父',10,'受益，从谠之兄子也。','郑受益是郑从谠兄长的儿子，所以郑从谠是郑受益的叔父。')
relationship('郑处诲','郑受益','父亲',10,'處誨生受益。','旧史明确郑处诲生郑受益，父亲方向明确。',source=bio)
relationship('郑处诲','从谠','兄长',10,'從讜兄處誨，為汴州節度使。','旧史明确郑处诲是郑从谠的兄长；从讜为姓名异字，对应主书从谠。',source=bio)
add('li_tao_first_protest','李涛等到阁门前上疏，强烈请求追究张彦泽罪责',10,'庚申，','语甚切至。',[('李涛','与其他朝臣在阁门前极论张彦泽罪责')],when='942年四月庚申',note='使用后晋宋初官员李涛主体，避免与早期同名唐军人物混淆。')
qann='庚申，刑部郎中李濤、張麟，員外郎麻麟、王禧，同詣閣門上疏，論張彥澤罪犯，詞甚懇切。'
sup('li_tao_first_protest',10,ann,qann,'《旧五代史》补明一同上疏的刑部郎中张麟、员外郎麻麟和王禧。','各人姓名和官职来自本纪原文，同场参与不推盟友关系。',relation='adds')
for name,role in [('张麟','以刑部郎中身份同赴阁门上疏'),('麻麟','以员外郎身份同赴阁门上疏'),('王禧','以员外郎身份同赴阁门上疏')]:participant('li_tao_first_protest',name,10,qann,role,ann)
add('zhang_rank_reduced','石敬瑭下敕削张彦泽一阶，降爵一级',10,'辛酉，','降爵一级。',[('帝','下敕削阶降爵'),('张彦泽','受到削阶降爵处罚')],when='942年四月辛酉',note='阶和爵按原文分别保留，不换算现代官级。')
add('zhang_family_compensation','石敬瑭下令给张式父亲及子弟授官，并减轻回乡泾州民户的徭赋',10,'张式父','减其徭赋。”',[('帝','下令对张式家属授官，对回乡民户减徭赋'),('张铎','作为张式父亲获授官命令')],when='942年四月辛酉',place='泾州',note='诏令与每项实际执行不同；本段子弟未名，不凭等字造人物。')
sup('zhang_family_compensation',10,ann,'仍於涇州賜錢十萬，差人津置張式靈柩並骨肉歸鄉，所有先收納卻張式家財物畜，並令卻還。','《旧五代史》补记赐钱十万、安排张式灵柩与家属归乡，并命退还先前收纳的张家财物牲畜。','这些是诏令补充，不证明款物已经全部交付；十万保留史载金额，不补币种换算。',relation='adds')
add('li_tao_second_protest','李涛与两省、御史台官员再次伏阁上奏，认为处罚过轻',10,'癸亥，','请论如法。',[('李涛','与两省及御史台官员要求依法处罚')],when='942年四月癸亥',note='第二次奏争与庚申奏疏分开，其他官员没有完整名单。')
add('shi_summons_li_tao','石敬瑭召见李涛解释，李涛持笏近殿阶激烈争辩',10,'帝召涛','论辨声色俱厉。',[('帝','召见并向李涛说明'),('李涛','持笏近殿阶激烈争辩')],when='942年四月癸亥奏疏后')
add('li_tao_refuses_to_withdraw','石敬瑭连续呵斥李涛，李涛没有退下',10,'帝怒，','涛不退。',[('帝','愤怒并连续呵斥'),('李涛','面对呵斥没有退下')],when='942年四月癸亥召见中')
add('li_tao_questions_promise','石敬瑭称已许张彦泽不死，李涛以范延光铁券反驳，皇帝拂衣离开',10,'帝曰：“朕已许', '入禁中。',[('帝','以此前免死承诺拒绝严惩，随后离开'),('李涛','以范延光铁券反驳免死承诺')],when='942年四月癸亥召见中',note='范延光是谈话中举出的先例，不列为本次现场参与者；不把提及铁券另造当年事件。')
add('zhang_longwu_general','石敬瑭任张彦泽为左龙武大将军',10,'丙寅，',None,[('帝','任命张彦泽为左龙武大将军'),('张彦泽','获任左龙武大将军')],when='942年四月丙寅')
sup('zhang_longwu_general',10,ann,'翌日，以前涇州節度使張彥澤為左龍武大將軍。','《旧五代史》把这次左龙武大将军任命记在辛酉诏令的翌日。','与通鉴丙寅的日期不同，分别保留，不因异记另造第二次同职任命。',relation='conflicts')
add('liu_yan_changes_succession_plan','刘岩病中与王翷商议外放刘弘度、刘弘熙，改立刘弘昌',11,'汉高祖寝疾，','而立弘昌。',[('汉高祖','计划改变继承人'),('王翷','与刘岩商议外放两子并立少子'),('弘度','被计划调往邕州'),('弘熙','被计划调往容州'),('弘昌','被计划立为继承人')],when='942年四月刘岩去世前，具体日期未载',place='南汉',note='是谋划而非已执行外放或已正式立太子；孝谨、骄恣为史书的人物判断。')
sup('liu_yan_changes_succession_plan',11,new,'翻為龑謀，出洪度以邕州，洪熙容州，然後立洪昌為太子。','《新五代史》同记外放洪度、洪熙后立洪昌为太子的方案，谋臣名写王翻。','王翷与王翻按同一右仆射及继承方案对应，保留姓名异字；洪与弘沿用既有人物别名。')
add('xiao_yi_stops_succession_change','萧益问疾时劝刘岩按嫡长继承，刘岩停止改立计划',11,'制命将行，','乃止。',[('萧益','问疾时反对改变继承顺序'),('汉高祖','征询意见后停止改立计划')],when='942年四月刘岩去世前，具体日期未载',place='南汉',note='必乱为萧益的警告，不当作已经发生的政变。')
add('liu_yan_dies','南汉刘岩去世',11,'丁丑，','高祖殂。',[('汉高祖','去世')],when='942年四月丁丑',place='南汉')
sup('liu_yan_dies',11,death,'十五年，龑卒，年五十四，','《新五代史》记大有十五年刘龑去世，享年五十四。','同一刘岩死亡补证，年龄不自行换算出生年；后列谥号庙号陵名属于后续叙事，本次不提前授定。')
claim('person',people['刘岩'],'biography','《资治通鉴》批评刘岩善察、多权谋、自大，称中原天子为洛州刺史，并记其宫殿装饰奢华。',11,span(11,'高祖为人辨察','为饰。'),'这是史书对长期性格和生活的描述，不造942年单日装饰宫殿或外交辱骂事件。')
claim('person',people['刘岩'],'biography','《资治通鉴》记刘岩使用多种酷刑，包括把罪人投入有毒蛇的水狱。',11,span(11,'用刑惨酷','谓之水狱。'),'长期刑罚做法按原文概述，具体受害者、案由和日期未载，不补个案。')
add('yang_dongqian_remonstrates','杨洞潜劝谏刘岩，刘岩没有接受',11,'同平章事杨洞潜','不听。',[('杨洞潜','向刘岩劝谏'),('汉高祖','不接受杨洞潜劝谏')],year=None,when='刘岩在位期间，具体年月未载',place='南汉',note='承接酷刑记载，具体奏词未载；不因编年位置确定为942年四月。')
claim('person',people['刘岩'],'biography','《资治通鉴》记刘岩晚年愈发猜忌，认为士人会为子孙谋划，因而专用宦者，使南汉宦者势力扩大。',11,'末年尤猜忌；以士人多为子孙计，故专任宦者，由是其国中宦者大盛。','这是晚年用人概述，不补所有宦者名单或因果之外的新理由。')
add('liu_hongdu_succeeds','秦王刘弘度即位，并改名为玢',12,'秦王弘度','更名玢。',[('弘度','即皇帝位并改名玢')],when='942年四月刘岩去世后，具体日期未载',place='南汉',note='复用已有刘弘度稳定主体，刘玢是同人新名字，本批以事实引用补充，暂不直接改旧人物字段。')
sup('liu_hongdu_succeeds',12,new,'由是洪度卒得立。更名玢，改元曰光天，','《新五代史》同记洪度即位，改名玢并改元光天。','卒得立表示最终获立，不是去世；名字变动不新建人物。')
add('liu_hongxi_regent','刘弘度让刘弘熙辅政，改元光天',12,'以弘熙辅政，','改元光天；',[('弘度','安排刘弘熙辅政并改元'),('弘熙','开始辅政')],when='942年刘弘度即位时，具体日期未载',place='南汉',note='辅政不等于刘弘熙本年即已夺位。')
add('zhao_empress_dowager','刘弘度尊母亲赵昭仪为皇太妃',12,'尊母',None,[('弘度','尊母亲为皇太妃'),('赵氏（刘弘度母）','由昭仪被尊为皇太妃')],when='942年刘弘度即位时，具体日期未载',place='南汉')
relationship('赵氏（刘弘度母）','弘度','母亲',12,'秦王弘度即皇帝位，更名玢。以弘熙辅政，改元光天；尊母赵昭仪曰皇太妃。','赵昭仪是刘弘度的母亲，皇太妃尊号来自同句。')
for name in ['弘度','弘熙','弘昌']:relationship('汉高祖',name,'父亲',11,span(11,'汉高祖寝疾','少子越王弘昌孝谨有智识，'),'刘岩为三个儿子的父亲明示；复用已有同向关系及稳定key，不造反向重复边。')
add('khitan_rebukes_jin_tuyuhun','契丹因后晋招纳吐谷浑，派使者责问',13,'契丹以晋','遣使来让。',[('帝','所在后晋受到契丹使者责问')],when='942年五月条下，具体使者到达日期未载',place='后晋',note='招纳与责问承接前事，不补使者姓名或另把所有先前招纳定为本年五月。')
add('shi_jingtang_ill','石敬瑭忧虑，五月己亥开始患病',13,'帝忧悒',None,[('帝','忧虑并在五月己亥开始患病')],when='942年五月己亥',description='《资治通鉴》记石敬瑭因契丹责问而忧虑，不知如何应对，五月己亥开始患病。',note='忧虑与患病是史书的叙述关系，不据此作医学诊断。')
sup('shi_jingtang_ill',13,may,'時帝不豫，難於視朝故也。','《旧五代史》五月记石敬瑭患病，难以处理朝会。','只引用本纪正文，不把其后引辽史和契丹国志的注合算为旧史独立确证。')
add('liu_taifei_empress_dowager','石敬瑭尊刘太妃为皇太后',14,'乙巳，','为皇太后。',[('帝','尊刘太妃为皇太后'),('刘氏（石敬瑭太妃）','由太妃被尊为皇太后')],when='942年五月乙巳')
sup('liu_taifei_empress_dowager',14,may,'乙巳，尊皇太妃劉氏為皇太后。','《旧五代史》同记五月乙巳尊刘氏为皇太后。','正文尊号与通鉴对应，母系身份另作引用说明。')
claim('person',people['刘氏（石敬瑭太妃）'],'biography','《资治通鉴》称刘太妃是石敬瑭的庶母。',14,'太后，帝之庶母也。','庶母与生母含义不能无条件等同；旧史所引注有另一说法，暂不建立确定生母关系。')
claim('person',people['刘氏（石敬瑭太妃）'],'biography','《旧五代史》在尊号记载后引徐无党《五代史记注》，称刘氏是石敬瑭的生母。',14,'〈（徐無黨《五代史記註》云：高祖所生母也。）〉','明确这是所引徐无党注，与通鉴庶母并列，不能当成旧史正文独立核实的生母事实。',source=may,relation='conflicts')
claim('person',people['杨洪'],'death_year','杨洪于942年在陕州被张彦泽杀死。',9,'还至陕，获亡将杨洪，乘醉断其手足而斩之。','返程杀害承接942年离任，出生年未载。')
for row in B['people']:
 if row['name']=='杨洪':row['death_year']=942
reviews={9:'在泾州擅出兵及征马为先前在任概述，年月为空；返至陕州杀杨洪与王周奏罪及帝初不追究分期。户、马、条数单位分别保留，联姻不造明确婚配。',10:'己未郑受益疏及留中、庚申李涛等疏、辛酉削阶降爵及家属补偿、癸亥再争召见和丙寅任官分期。收百匹马为疏中转述议论，范延光为先例非现场。旧史补同疏张麟麻麟王禧及诏令赐钱退还，不提前实际给付；翌日任命与通鉴丙寅异说保留。叔父父亲兄长关系方向清楚。',11:'刘岩继承方案、萧益劝阻与停止、四月丁丑死亡分录；王翷与新史王翻同职同谋对应，弘洪异名复用。性格奢华酷刑和晚年宦者概述保留人物引用，杨洞潜谏未知年月为空。',12:'刘弘度即位及改名玢沿用稳定主体，不复制人；弘熙辅政改元与赵昭仪尊号、母亲方向分清，不提前弘熙夺位。',13:'契丹责问具体日未载，石敬瑭五月己亥病有明确日；史载忧悒与病不作现代医学因果。旧纪患病正文与注文区分。',14:'五月乙巳尊刘太妃有旧纪正文补证；通鉴庶母与旧纪引徐无党注生母并列，不建确定生母边。'}
assert not (P/'publication.json').exists()
for n in range(9,15):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
ledger[10]['claim_keys']=[x['key'] for x in B['claims'] if Q[11]['id'] in x['citation']]
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=283,year=942,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,15)],next_paragraph=Q[15]['id'],supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第9—14段，原14—19行，四月至五月及相关追述；下接宋齐丘罢省后交涉第15段，全年未完成。',source_issues_review='左龙武大将军任命日、王翷王翻姓名、弘洪字形、刘太妃庶母与所引注生母异说保留。旧史引注不冒称正文独立确证；纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,15)],plain_language_review='首次逐项检查标题、人物介绍、参与动作、亲属方向、时间及出处说明，均以现代白话表达；计划、谏言、命令和执行区分，旧主体基础字段保留。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
