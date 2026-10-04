# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 938 paragraphs 30–35."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,43))
specs=[(d.name,d,'ffeb58e6e0fe058df2623e62372c88eca7addd8c','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修、宋祁' if d.name.startswith('xintangshu') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-938-surrender-and-capital','jiuwudaishi-077-october']:
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
main_sources = ['tongjian-281-938-surrender-and-capital','tongjian-281-938-late-year']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0938-p030-p035',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-077-october':'卷77·晋高祖纪·天福三年十月','jiuwudaishi-077-november':'卷77·晋高祖纪·天福三年十一月','xinwudaishi-065-bach-dang':'卷65·南汉世家','xintangshu-101-xiao-fang':'卷101·萧仿附传'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/281.txt').read_text().splitlines()
for n in range(30, 36):
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
    labels={'jiuwudaishi-077-october':'卷77·晋高祖纪·天福三年十月','jiuwudaishi-077-november':'卷77·晋高祖纪·天福三年十一月','xinwudaishi-065-bach-dang':'卷65·南汉世家','xintangshu-101-xiao-fang':'卷101·萧仿附传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '十月条下，含追述' if n<34 else '十一月条下'
        citation = f'卷281·后晋天福三年（938；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0938_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'吴权':'杨廷艺的旧将。938年从爱州起兵进攻皎公羡，取得交州，并在白藤江利用铁桩和潮汐击败南汉水军。生卒年本段未载。',
'萧益':'南汉崇文使，萧仿的孙子。938年南汉出兵交州时，建议谨慎进军、选用熟悉地形的向导；刘岩没有听从。生卒年未载。',
'萧仿':'萧益的祖父。《新唐书》记他字思道，为萧悟之子，在唐代大和年间考中进士，后来担任给事中。生卒年本次未核。',
'侯融':'南汉著作佐郎。曾劝刘岩停止用兵、休养民力；交州战败后，刘岩追究他的责任，打开棺木暴露遗体。劝谏和死亡的具体年月未载。',
'彭氏（楚顺贤夫人）':'楚顺贤夫人。938年去世。《资治通鉴》记她治家有法，马希范对她有所畏惧；个人名字和出生年未载。',
'卢损（后晋册礼使）':'后晋左散骑常侍。938年十一月受命为册礼使，参与后晋封王继鹏为闽国王的安排。生卒年未载。',
'林恩（闽进奏官）':'闽国进奏官。938年十一月受王继鹏派遣，向后晋执政官转达拒绝册命和使者的意见。生卒年未载。',
'黄讽（闽谏议大夫）':'闽国谏议大夫。938年十一月与家人告别后进谏，拒绝受杖打，被王继鹏贬为平民。生卒年未载。'}
NEW_ALIASES={'吴权':['吳權'],'萧益':['蕭益'],'萧仿':['蕭仿'],'侯融':[],'彭氏（楚顺贤夫人）':['顺贤夫人彭氏','順賢夫人彭氏'],'卢损（后晋册礼使）':['卢损','盧損'],'林恩（闽进奏官）':['林恩'],'黄讽（闽谏议大夫）':['黄讽','黃諷']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name in ['杨嗣复','萧仿'] else '五代十国',birth_year=None,death_year=938 if name=='彭氏（楚顺贤夫人）' else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=938, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='938年十月条下，具体日期未载' if n<34 else '938年十一月条下，具体日期未载'
    key = 'event_zztj_281_0938_' + code
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
        edge = 'participation_zztj_281_0938_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_281_0938_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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




ALIASES.update({'唐主':'李昪','汉主':'刘岩','弘操':'刘弘操','杨延艺':'杨廷艺','楚王希范':'马希范','彭氏':'彭氏（楚顺贤夫人）','卢损':'卢损（后晋册礼使）','林恩':'林恩（闽进奏官）','黄讽':'黄讽（闽谏议大夫）'})
new='xinwudaishi-065-bach-dang';nov='jiuwudaishi-077-november'
add('shi_october_general_amnesty','石敬瑭下令大赦',30,'戊戌，',None,[('帝','下令大赦')],when='938年十月戊戌',note='此条简记大赦，不自动补出此前广晋赦令以外所有具体法律条款。')
sup('shi_october_general_amnesty',30,'jiuwudaishi-077-october','戊戌，大赦天下，以魏府初平故也。','《旧五代史》也记十月戊戌大赦，并说明因为魏府刚刚平定。','原因来自该书独立补充，不替主书简条补出具体赦免条件。')
add('ngo_quyen_marches_jiaozhou','吴权从爱州起兵进攻交州的皎公羡',31,'杨延艺故将','于交州，',[('吴权','以杨廷艺旧将身份，从爱州起兵进攻交州'),('皎公羡','受到吴权进攻')],place='爱州、交州',note='杨延艺复用937年杨廷艺主体；旧将身份不是杨廷艺仍在世领兵，不重复录937年遇害。')
relationship('吴权','杨廷艺','旧部',31,span(31,'杨延艺故将','于交州，'),'故将明确吴权是杨廷艺的旧部，属于既有从属经历，不推永久联盟。')
add('kieu_requests_southern_han_aid','皎公羡派使者向南汉求援并送礼',31,'公羡遣使','于汉。',[('皎公羡','派使者送礼求南汉救援'),('汉主','收到皎公羡求援')],place='交州、南汉',note='以赂求救按送礼求援表述，匿名使者不补姓名。')
add('liu_appoints_hongcao_jiaowang','刘岩任刘弘操为静海节度使，改封交王并命其救援',31,'汉主欲乘其乱','将兵救公羡，',[('汉主','意图借乱夺取交州，任刘弘操为静海节度使、改封交王并派军救援'),('弘操','由万王改封交王，任静海节度使并带兵救援')],place='静海军、交州',note='欲乘乱取交州是刘岩的意图，不能写成已占领；任官、改封和出兵均见本句。')
relationship('汉主','弘操','父亲',31,span(31,'汉主欲乘其乱','将兵救公羡，'),'其子明确刘岩是刘弘操的父亲，复用既有主体及关系。')
sup('liu_appoints_hongcao_jiaowang',31,new,'龑封洪操交王，出兵白藤以攻之。','《新五代史》也记刘龑封洪操为交王，并出兵白藤。','刘龑沿用刘岩主体，洪操沿用刘弘操主体；字形别名有既有登记，原文各自保留。')
add('liu_stationed_haimen','刘岩亲自率军驻海门，为刘弘操声援',31,'汉主自将','为之声援。',[('汉主','亲率军驻海门为刘弘操声援')],place='海门',note='驻海门声援不误写为刘岩本人率舰在白藤江交战。')
sup('liu_stationed_haimen',31,new,'龑以兵駐海門，','《新五代史》也记刘龑率军驻海门。','只印证驻军地点，不补无记载的海门现代坐标。')
add('xiao_yi_advises_caution','萧益建议南汉谨慎进军、多用向导，刘岩没有听从',31,'汉主问策于崇文使萧益，','不听。',[('汉主','向萧益问策，但未听从谨慎进军的建议'),('萧益','指出久雨和海道风险，建议谨慎行军、多用向导')],description='萧益指出连日下雨、海道险远，认为吴权不能轻视，建议大军谨慎行军，多用熟悉地形的向导。刘岩没有听从。',note='吴权桀黠是萧益在建议中的评价，不作网站独立人格定论；霖雨积旬不换算确定起止日。')
add('hongcao_sails_bach_dang','刘岩命刘弘操率战舰从白藤江前往交州',31,'命弘操','趣交州。',[('汉主','命刘弘操率战舰由白藤江进军'),('弘操','率战舰从白藤江前往交州')],place='白藤江、交州',note='趣为前往，不译为兴趣；行军命令与后续追击分别记录。')
add('ngo_quyen_kills_kieu','吴权已经杀死皎公羡并据有交州',31,'权已杀公羡，','据交州，',[('吴权','杀死皎公羡并占据交州'),('皎公羡','被吴权杀死')],when='938年迎战南汉水军之前，具体日期未载',place='交州',note='已表示迎战之前完成，不按后段潮落战斗日认定皎公羡死亡日期。')
sup('ngo_quyen_kills_kieu',31,new,'權已殺公羨，逆戰海口，','《新五代史》也记吴权已杀皎公羡，随后在海口迎战。','书内十年条与主书938年位置不同；行动先后可相互参照，纪年差异另保留，不强行当同年独立确证。')
add('ngo_quyen_plants_iron_stakes','吴权在海口埋设顶端包铁的尖木桩',31,'引兵逆战，','冒之以铁，',[('吴权','准备迎战，在海口埋设尖木桩，顶端包铁')],place='白藤江海口',note='大后私用字在摘录保留，后文铁杙及新史铁橛支持展示木桩；不猜原字替换原文快照。')
sup('ngo_quyen_plants_iron_stakes',31,new,'植鐵橛海中，','《新五代史》也记吴权在海中设置铁桩。','海中与主书海口分别保留，不推未经核实的布桩坐标、数量或长度。')
add('ngo_baits_hongcao_at_tide','吴权用轻舟乘潮挑战并佯退，引刘弘操追击',31,'遣轻舟','弘操逐之，',[('吴权','派轻舟乘潮挑战后佯退'),('弘操','追击吴权的轻舟')],place='白藤江海口',note='伪遁为佯退，不是吴权已经败逃；潮汐战术不补现代精确时刻。')
add('bach_dang_han_fleet_defeat','潮退后南汉战舰被铁桩阻碍，水军大败',31,'须臾潮落，','太半；',[('吴权','以铁桩和潮汐击败南汉水军'),('弘操','率领的水军战舰受阻，大败')],place='白藤江海口',description='潮水退去后，南汉战舰被铁桩阻碍，无法返回，水军大败。史书称溺亡者超过半数。',note='太半沿史书概述，不编具体伤亡数字；无法返回不扩写为每条战船都被击沉。')
sup('bach_dang_han_fleet_defeat',31,new,'權兵乘潮而進，洪操逐之，潮退舟還，轢橛者皆覆，','《新五代史》也记吴权部队借潮水行动，洪操追击，潮退后触桩的船只覆没。','两书战术细节分别保留；该书只说触桩者皆覆，不推全部舰只覆没。')
sup('bach_dang_han_fleet_defeat',31,new,source_span(new,'十年，','龑收餘眾而還。'),'《新五代史》将皎公羡杀杨廷艺、吴权攻交州及南汉白藤战败合记在大有十年条下。','主书937年记皎公羡杀杨廷艺、938年记白藤战事，另一书的合记和纪年差异保留，不覆盖主书日期。',relation='conflicts',field='time_original')
add('hongcao_dies_in_battle','刘弘操在白藤江战败中死亡',31,'弘操死，','弘操死，',[('弘操','在白藤江水军战败中死亡')],place='白藤江',note='死见主书，新史补战死；两书纪年有差异，主书年度保留938，具体日期未载。')
sup('hongcao_dies_in_battle',31,new,'洪操戰死，','《新五代史》明确写洪操战死。','死因来自战事上下文，不补为某个具名敌将亲手杀死。')
claim('person',people['刘弘操'],'death_year','《资治通鉴》在938年条记刘弘操战败死亡；《新五代史》合记于大有十年，存在纪年差异。',31,'弘操死，','这是主书年度归属及异说说明，不据此改写早期已发布人物档案。')
add('liu_grieves_and_withdraws','刘岩因刘弘操死亡痛哭，收拢余部撤回',31,'汉主恸哭，','收馀众而还。',[('汉主','因儿子死亡痛哭，收拢余部撤回')],place='海门、南汉',note='撤回方向只有还，不补确定路线和到达时间。')
sup('liu_grieves_and_withdraws',31,new,'龑收餘眾而還。','《新五代史》也记刘龑收拢余部撤回。','只印证撤军，不把该书未写的痛哭作为独立补证。')
add('hou_rong_advises_peace','侯融此前建议刘岩停止用兵、休养民力',31,'先是，','弭兵息民，',[('侯融','以著作佐郎身份建议停止用兵、休养民力'),('汉主','收到侯融的劝谏')],year=None,when='交州战败之前，具体年月未载',note='先是为追述，不按白藤战败当日认定进谏。')
add('liu_exposes_hou_corpse','刘岩战败后追究侯融，打开棺木暴露遗体',31,'至是以兵不振，','暴其尸。',[('汉主','因战败追究侯融，命人打开棺木暴露遗体'),('侯融','死后被打开棺木暴露遗体')],note='打开棺木说明侯融此前已死，但死亡日期和死因未载，人物死亡年留空；不误作战败后才杀死侯融。')
relationship('萧仿','萧益','祖父',31,'益，仿之孙也。','末句承接萧益，仿为其祖父；同卷新唐书萧氏家传识别萧仿，不凭孙关系猜萧益父亲。')
claim('person',people['萧仿'],'description',NEW_DESCRIPTIONS['萧仿'],31,'仿，字思道，悟子。大和中，擢進士第。除累給事中。','《新唐书》卷101萧氏家传中萧仿附传，姓氏依前文家传和小节上下文核对；不把唐代任官当938年事件。',source='xintangshu-101-xiao-fang')
add('peng_shunxian_dies','楚顺贤夫人彭氏去世',32,'楚顺贤夫人','彭氏卒。',[('彭氏','去世')],when='938年十月条下，具体日期未载',note='此年主书记死亡，生年和个人名字未载，不猜补彭氏名字。')
add('peng_household_discipline','史书记述彭夫人治家有法，马希范对她有所畏惧',32,'彭夫人貌陋','楚王希范惮之；',[('彭氏','被史书评价治家有法'),('楚王希范','对彭夫人有所畏惧')],year=None,when='彭夫人生前的追述，具体年月未载',description='《资治通鉴》评价彭夫人治家有法，记马希范对她有所畏惧。原文同时评论她的容貌；这些是史书的评价。',note='评价有来源归属，不将容貌判断作为网站的客观结论；此句不补未载婚期。')
add('ma_xifan_indulgence_after_peng','彭夫人去世后，马希范沉溺声色、彻夜饮酒',32,'既卒，','内外无别。',[('楚王希范','在彭夫人去世后沉溺声色、彻夜饮酒')],year=None,when='彭夫人去世之后，具体起止年月未载',note='既卒后持续行为不当死亡当日单次宴会；内外无别按缺少内外礼制区分理解，不猜个别人参与。')
add('ma_xifan_kills_merchant','马希范杀死一名商人并强夺其妻，女子自缢',32,'有商人妻美，',None,[('楚王希范','杀死商人并强夺其妻')],year=None,when='彭夫人去世后的记载，具体年月未载',description='马希范看中一名商人的妻子，杀死商人并强夺她。女子发誓不受侮辱，随后自缢。',note='夫妻姓名未载，保留匿名受害者说明，不编姓名或进一步推家族身份。')
add('yunzhou_yellow_river_breach','黄河在郓州决口',33,'河决郓州。',None,[],place='郓州',note='河为本卷黄河水系背景；此句只记决口，不编灾民数、淹没面积或确切决口坐标。')
add('fan_visits_court_from_yunzhou','范延光从郓州入朝',34,'十一月，',None,[('范延光','从郓州前往朝廷')],when='938年十一月，主书未单列具体日期',place='郓州、朝廷')
sup('fan_visits_court_from_yunzhou',34,nov,'乙巳，鄆州範延光來朝。','《旧五代史》补充范延光十一月乙巳来朝。','来朝日为独立补证，不改主书未列日的说明。',field='time_original')
add('jin_confers_min_king','石敬瑭封王继鹏为闽国王，命卢损为册礼使并赐赭袍',35,'丙午，','赐昶赭袍。',[('帝','封王继鹏为闽国王，任册礼使并赐赭袍'),('闽主','收到后晋封闽国王的安排'),('卢损','以左散骑常侍身份被任命为册礼使')],when='938年十一月丙午',note='王继鹏本已称帝，此为后晋给的册命，不改作闽国内首次称王；任使与实际获接纳分开。')
sup('jin_confers_min_king',35,nov,'丙午，封閩王昶為閩國王，加食邑一萬五千戶。','《旧五代史》也记十一月丙午封王昶为闽国王，并补加食邑一万五千户。','王昶沿用王继鹏主体；食邑为名义封授单位，不换算实际人口或固定财政收入。')
add('wang_jigong_linhai','石敬瑭封王继恭为临海郡王',35,'戊申，','临海郡王。',[('帝','封王继恭为临海郡王'),('王继恭','以威武节度使身份获封临海郡王')],when='938年十一月戊申',note='王继恭沿用937年主体，原有弟弟/儿子异说不在此段强行定论。')
sup('wang_jigong_linhai',35,nov,'以威武軍節度、福建管內觀察處置等使王繼恭為特進、檢校太傅，仍封臨海郡王。','《旧五代史》也记王继恭封临海郡王，并补特进、检校太傅职衔。','本句接戊申条，任官日期与主书相合；亲属身份不是本句内容，不据此解决既有异说。')
add('min_rejects_jin_investiture','王继鹏派林恩向后晋表示拒绝册命和使者',35,'闽主闻之，','及使者。',[('闽主','以已经称帝为由，派林恩转达拒绝册命和使者'),('林恩','向后晋执政官转达拒绝的意见')],description='王继鹏得知册命安排后，以自己已经采用皇帝称号为由，派进奏官林恩向后晋执政官表示拒绝册命和使者。',note='辞使者是拒绝接纳使者，不推已经拘押、杀害或驱逐一个具名使者。')
add('huang_feng_remonstrates','黄讽与家人告别后进谏王继鹏',35,'闽谏议大夫黄讽','入谏，',[('黄讽','以谏议大夫身份，与家人告别后进谏'),('闽主','受到黄讽进谏')],description='黄讽因王继鹏的纵欲和暴虐，与妻子、子女告别后入朝进谏。',note='淫暴是进谏的背景评价；妻子中的子指子女，姓名和人数未载，不造家人节点。')
add('huang_feng_refuses_flogging','王继鹏想杖打黄讽，黄讽拒绝因直谏受杖',35,'闽主欲杖之，','臣不受也。”',[('闽主','想杖打黄讽'),('黄讽','表示愿为不忠受罚，拒绝因直谏被杖打')],note='欲杖是意图，黄讽拒绝后原文未记已实际受杖，不录为已经杖伤。')
add('huang_feng_demoted_commoner','王继鹏发怒，将黄讽贬为平民',35,'闽主怒，',None,[('闽主','发怒，将黄讽贬为平民'),('黄讽','被贬为平民')],note='黜为民为身份处分，不误作当场处死或流放某地。')
reviews={30:'十月戊戌大赦，旧史补魏府初平原因；不扩写具体条款。',31:'吴权故将身份、皎求援、刘弘操任官改封出兵、海门声援、萧益建议、铁桩潮汐战败与撤军分录。新史大有十年合记与主937杀杨/938战事有差异，分别引用。弘操死亡不猜凶手，侯融此前劝谏及死后开棺分开，不造死亡年。私用字木桩有后文铁杙、新史铁橛佐证，原文不改。萧仿祖父方向明确，新唐书证明唐人身份，未补萧益父亲。',32:'彭氏去世为938本年记载；治家评价与马希范后续行为、商人夫妻受害分开，追述年月留空。彭氏个人名、匿名夫妻姓名不猜补，容貌评价归史书。',33:'郓州河决只记史载地区，不补坐标和灾情数字。',34:'十一月范延光郓州入朝，旧史补乙巳日，两书各自保持纪时精度。',35:'丙午封闽国王、卢损任使赭袍、戊申封王继恭与拒册分别记录。黄讽辞家进谏、杖打意图及拒受、贬民分开；未记实际受杖，妻子指妻及子女不作两个妻子。王继恭既有亲属异说不借新任官改定。'}
assert not (P/'publication.json').exists()
for n in range(30,36):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=938,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(30,36)],next_paragraph=Q[36]['id'],next_volume=281,next_year=938,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第30—35段，原96—101行；大赦、白藤江战事、楚彭夫人及马希范行为、郓州河决、范延光入朝、闽册命及黄讽进谏。938年未完成。',source_issues_review='新五代史卷65南汉世家与主书纪年差异保留，木桩私用字保留原文；旧五代史卷77补纪日任官，新唐书卷101萧氏家传核萧仿身份，未延展唐代任官事件。纸本及异文仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(30,36)],plain_language_review='首次逐条检查标题、人物简介、事件、参与和出处解释，主语与关系方向明确；意图、建议、行动、追述和评价分开，引文保留原字。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
