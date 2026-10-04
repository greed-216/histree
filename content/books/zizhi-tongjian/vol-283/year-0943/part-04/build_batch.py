# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 943 paragraphs 25–33."""
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
COMMIT='7bc781abc574bfda6b3d4fe1b21ccaaaf8a0ef7e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-943-april-may','xinwudaishi-065-liu-sheng-accession','xinwudaishi-009-943-return','xinwudaishi-062-jing-brothers','xinwudaishi-029-jing-khitan']:
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
main_sources = ['tongjian-283-943-april-may','tongjian-283-943-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0943-p025-p033',
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
lines = (ROOT / 'resources/derived/tongjian/283.txt').read_text().splitlines()
for n in range(25, 34):
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
    for a,b in [('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        month = '八月至十一月条下及追述'
        citation = f'卷283·后晋天福八年（943；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0943_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=943, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='943年年初条下，具体日期未载'
    key = 'event_zztj_283_0943_' + code
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
        edge = 'participation_zztj_283_0943_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0943_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','汉主':'刘弘熙','景逷':'李景逷','宋太后':'宋氏（南唐李昪后）','种夫人':'种氏（李昪妃）','彝敏':'李彝敏','彝俊':'李彝俊','高祖':'石敬瑭','重胤':'石重胤','冯夫人':'冯氏（石重贵后）','冯后':'冯氏（石重贵后）','太后':'永宁公主（石敬瑭妻）','弘雅':'刘弘雅','镐':'边镐','契丹主':'耶律德光'})
NEW_ALIASES={'拓跋崇斌':['拓拔崇斌'],'李彝敏':['李彜敏'],'李彝俊':['李彜俊'],'乔荣':['喬榮','乔莹','喬瑩'],'石重胤':[],'冯濛':['馮濛'],'冯氏（石重贵后）':['吴国夫人冯氏','馮氏（石重贵后）'],'冯玉':['馮玉'],'严恩':['嚴恩','严思','嚴思'],'边镐':['邊鎬'],'白昌裕':[],'李台':[]}
NEW_DESCRIPTIONS={
'拓跋崇斌':'夏州牙内指挥使，943年谋作乱，李彝敏准备相助。《旧五代史》九月奏报称拓拔崇斌等五人已经被捕斩；拓跋、拓拔字形分别保留，处刑确切日未载。出生年未载。',
'李彝敏':'后晋绥州刺史。943年准备帮助拓跋崇斌作乱，事泄后与弟李彝俊等奔延州。九月，李彝殷奏报其事，朝廷下令送夏州处斩。两书此处主要记诏令，实际执行日尚未核，不据此补精确死亡日。',
'李彝俊':'李彝敏的弟弟。943年八月辛未随李彝敏等弃绥州奔延州。生卒年未载。',
'乔荣':'原河阳牙将，随赵延寿入契丹后任回图使，在后晋经商并在大梁设邸。943年遭囚禁和没收货物，获释后把景延广的外交言辞写下并报给耶律德光。《新五代史》相同场景作喬瑩，据行动、对话和纸上记录对应同人，姓名异文与纸本待核。生卒年未载。',
'石重胤':'石敬瑭称为少弟的人，又被石敬瑭收养为子。娶冯濛之女，早逝。《新五代史》明确说不知其与石敬瑭的血亲亲疏，故不强建唯一同父兄弟关系；养父关系明确。生卒具体年月尚未核。',
'冯濛':'安喜人，后晋冯皇后的父亲，曾任邺都副留守。《新五代史》还记他曾是定州进奏吏，居京师，受到安重诲赏识。生卒年未载。',
'冯氏（石重贵后）':'冯濛的女儿、冯玉的妹妹。先嫁石重胤，夫死后守寡；石敬瑭去世后被石重贵纳入宫中，943年十月戊申由吴国夫人立为皇后，随后参与政务。具体个人名字与生卒年未载。',
'冯玉':'冯皇后的兄长，后晋官员。《资治通鉴》记其由礼部郎中、盐铁判官被迅速擢为端明殿学士、户部侍郎；《旧五代史》另记知制诰、中书舍人、颍州团练使等任职。各书路径分别保留，生卒年本批未核。',
'严恩':'南唐洪州营屯都虞候。943年十月奉李璟命率兵讨张遇贤，与监军边镐共事。《新五代史》同一战役作嚴思，依据军职及边镐、张遇贤对应同人，保留姓名异文待纸本核。生卒年未载。',
'边镐':'金陵人，南唐通事舍人。943年十月任讨张遇贤军监军，用白昌裕为谋主，接连获胜；白昌裕建议开道绕到营后袭击，张遇贤随后逃走被捕。生卒年尚未核。',
'白昌裕':'南唐讨张遇贤军的谋主，由边镐任用，曾建议伐木开道绕到张遇贤营后袭击。《资治通鉴》籍贯写虞州，保留原地名待核，不自行改为虔州。生卒年未载。',
'李台':'张遇贤属下别将。943年十月张遇贤弃众投奔他，他认为神言无验，擒张遇贤投降，张遇贤后来在金陵市被斩。生卒年未载。'}
# 25–27: contemporary titles, planned rebellion, flight and family conduct.
add('jingti_baoning_wang','李璟立弟弟李景逷为保宁王',25,'八月，','为保宁王。',[('唐主','立弟弟景逷为保宁王'),('景逷','被立为保宁王')],when='943年八月乙卯',place='南唐')
add('jing_protects_jingti','宋太后因怨恨种氏，多次想害李景逷，李璟尽力保护他',25,'宋太后',None,[('宋太后','因怨恨种氏而多次想害景逷'),('景逷','受到李璟保护'),('唐主','尽力保护弟弟景逷')],year=None,when='李璟即位后相关记载，具体年月未载',place='南唐',note='屡欲为计划，未写太后已经杀死景逷；不补每次实施方法。')
sup('jingti_baoning_wang',25,'xinwudaishi-062-jing-brothers','景逷前未王，為保寧王。','《新五代史》也记此前未封王的景逷被封保宁王。','该句置于继位封王概述，没有乙卯日期，不说新史也明确同日。')
relationship('唐主','景逷','兄长',25,'唐主立弟景逷为保宁王。','原文明示李景逷为李璟弟弟，按兄长方向建立一条关系。')
add('tuoba_li_plan_rebellion','拓跋崇斌谋作乱，李彝敏准备相助，事情泄露',26,'夏州','事觉；',[('拓跋崇斌','任夏州牙内指挥使，谋作乱'),('彝敏','任绥州刺史，准备帮助拓跋崇斌')],when='943年八月辛未前，具体日期未载',place='夏州、绥州',note='将助为打算，主书此句不等于已攻城；旧纪后续奏报所述行动另引。')
add('li_yimin_flees_yanzhou','李彝敏与弟弟李彝俊等五人弃绥州，奔延州',26,'辛未，',None,[('彝敏','弃绥州，与弟等奔延州'),('彝俊','随兄长李彝敏奔延州')],when='943年八月辛未',place='自绥州赴延州',note='五人的具体名单未全载；旧纪二百七十口为骨肉人数，不混作五名起事者数量。')
ann='jiuwudaishi-082-943-september'
sup('li_yimin_flees_yanzhou',26,ann,'延州奏，綏州刺史李彜敏拋棄城郡，與弟彜俊等五人將骨肉二百七十口來投，','《旧五代史》还记他们带着亲属二百七十口来投延州。','九月延州奏报不是八月出发日；亲属数与五人群体分开。',relation='adds')
sup('tuoba_li_plan_rebellion',26,ann,'相次綏州刺史李彜敏擅將兵士，直抵城門，尋差人掩殺，','《旧五代史》引李彝殷奏报称李彝敏擅自率兵直抵城门，随后受到突袭。','这是奏报所述，不把主书准备相助改写为同日已到城门，也不补袭杀者未给姓名。',relation='adds')
E['tuoba_executed_before_report']=event('tuoba_executed_before_report','李彝殷奏报称拓跋崇斌等五人已经被捕斩',26,'衙內都指揮使拓拔崇斌等五人作亂，當時收擒處斬訖。',[('拓跋崇斌','据李彝殷奏报，已被捕斩')],year=943,when='943年九月甲午奏报前，实际处刑日未载',place='夏州',source=ann,note='当时收擒处斩讫支持执行已发生，甲午只作为奏报日。五人未全具名，不造其他死者。')
relationship('彝敏','彝俊','兄长',26,'彝敏弃州，与其弟彝俊等五人奔延州。','原文明示其弟，按李彝敏是李彝俊的兄长建立一条有向边。')
add('an_imperial_consort','石重贵尊生母安氏为皇太妃',27,'九月，','为皇太妃。',[('帝','尊母亲安氏为皇太妃'),('安氏（石重贵母）','由秦国夫人被尊为皇太妃')],when='943年九月，具体日期主书未载',place='后晋',note='复用既有安氏主体；皇太妃与石敬瑭妻永宁公主皇太后不同。')
sup('an_imperial_consort',27,ann,'九月戊寅，尊秦國夫人安氏為皇太妃，帝所生母也。','《旧五代史》记尊安氏为皇太妃在九月戊寅，并明确是石重贵生母。','主书只有月份，独立补证日，不覆盖原纪时。',relation='adds')
sup('an_imperial_consort',27,'xinwudaishi-009-943-return','九月戊寅，尊秦國夫人安氏為皇太妃。','《新五代史》也记九月戊寅尊安氏为皇太妃。','同人及封号。')
relationship('安氏（石重贵母）','帝','母亲',27,'尊帝母秦国夫人安氏为皇太妃。','主书明确母亲，旧纪明确所生母，复用安氏与石重贵，不混养母皇太后。')
add('shi_serves_family','史书记石重贵谨慎侍奉太后、太妃，与弟弟们友爱',27,'妃，代北人也。',None,[('帝','常在太后太妃宫中侍餐，对弟弟们友爱')],year=None,when='石重贵在位期间的概述，具体起止年月未载',place='后晋',note='甚谨、友爱是史书评价，未具名弟弟不自动添加所有宗室参与；安氏籍贯代北按史载。')
# 28: earlier trade, detention, September release and diplomatic statements.
add('qiao_follows_zhao','乔荣随赵延寿进入契丹',28,'初，','入契丹，',[('乔荣','原河阳牙将，随赵延寿进入契丹'),('赵延寿','乔荣随他进入契丹')],year=None,when='943年九月条下追述，随行年月未载',place='契丹',note='不以本年九月为进入契丹时间。')
add('qiao_trade_office','契丹任乔荣为回图使，他在晋经商并在大梁设邸',28,'契丹以为','置邸大梁。',[('乔荣','任回图使，往来后晋经商并在大梁设邸')],year=None,when='乔荣进入契丹之后，具体年月未载',place='大梁及晋契丹间',note='回图使为贸易相关职名，不改写为现代情报官；邸是商贸驻地，不推面积和货值。')
add('jing_proposes_qiao_detention','景延广劝石重贵囚禁乔荣，没收他在邸中的货物',28,'及契丹','悉取邸中之货。',[('景延广','劝石重贵囚禁乔荣并没收货物'),('帝','按此劝告囚禁乔荣'),('乔荣','被囚禁并失去邸中货物')],year=None,when='晋与契丹关系恶化之后，943年九月获释之前，具体年月未载',place='后晋',note='主书叙述囚荣与取货为已发生，但未给开始日；不据建议日期造独立确切处置日。')
add('khitan_traders_killed','史书记后晋杀死在境内经商的契丹人，夺其货物',28,'凡契丹之人','夺其货。',[],year=None,when='上述关系恶化与乔荣被囚期间，具体年月未载',place='后晋境内',note='未具名执行者、被杀者和人数，不把所有交易者具体列为名单，也不单据相邻句把唯一发令者推成景延广。')
add('ministers_oppose_breaking_pact','后晋大臣认为契丹助晋有功，不应背弃',28,'大臣皆言','不可负。',[],year=None,when='乔荣被囚后、获释前，具体日期未载',place='后晋',note='这是大臣意见；未具名发言者不自动加入桑维翰等后句人物。')
add('qiao_released','后晋释放乔荣，安慰赏赐后让他返回',28,'戊子，','慰赐而归之。',[('乔荣','获释，得到安慰和赏赐，返回契丹')],when='943年九月戊子',place='后晋',note='返回目的地结合前后契丹贸易与回报，赏赐金额未载。')
add('jing_tells_qiao_grandson_policy','景延广对乔荣重申称孙不称臣，并以十万横磨剑相威胁',28,'荣辞延广，','毋悔也！”',[('乔荣','辞别景延广，听到他的外交言辞'),('景延广','称孙不称臣，声称有十万横磨剑可迎战')],when='943年九月乔荣获释后，具体讲话日未载',place='后晋',note='十万横磨剑是景延广话语，不记为核实军械库存；翁孙是外交称谓，不建立血缘。')
add('qiao_requests_written_words','乔荣担心返国获罪，请求写下景延广的话',28,'荣自以','愿记之纸墨。”',[('乔荣','担心失货返国获罪，又想保留证据，请求将讲话写下')],when='943年九月上述辞别时',place='后晋',note='动机依主书叙述，未证明实际获罪。')
add('jing_orders_written_record','景延广命吏员把讲话写下，交给乔荣',28,'延广命吏','以授之，',[('景延广','命吏员记录其话语并交乔荣'),('乔荣','收到景延广讲话的书面记录')],when='943年九月上述辞别时',place='后晋',note='吏员未具名，不造记录者人物。')
add('qiao_reports_khitan','乔荣把景延广的话完整报告耶律德光',28,'荣具以','白契丹主。',[('乔荣','向耶律德光完整报告景延广的话'),('契丹主','收到乔荣报告')],when='943年乔荣返回契丹后，具体日期未载',place='契丹')
add('deguang_resolves_attack','耶律德光听到报告后愤怒，决定入侵后晋',28,'契丹主大怒，','入寇之志始决。',[('契丹主','听到报告后愤怒，决定入侵后晋')],when='943年上述报告后，具体日期未载',place='契丹',note='入寇之志是作出决定，不提前944年军队入境。')
add('jin_envoys_detained_youzhou','后晋派往契丹的使者被扣在幽州，不能见契丹君主',28,'晋使如契丹，','不得见。',[],when='943年上述交涉后，具体日期未载',place='幽州',note='使者未具名、不知道人数和拘禁期限，不自动将其他段落已具名使者套入。')
add('sang_requests_apology','桑维翰多次请求向契丹谦逊道歉，景延广阻止',28,'桑维翰屡请','每为延广所沮。',[('桑维翰','多次请求以谦逊言辞向契丹道歉'),('景延广','阻止桑维翰建议')],when='943年晋契丹交涉期间，具体日期未载',place='后晋',note='屡请不补次数；被阻止的建议不写成道歉已送达。')
add('shi_favors_jing','石重贵因拥立之功宠信景延广，他掌宿卫兵使大臣难以反对',28,'帝以延广','故大臣莫能与之争。',[('帝','因景延广有拥立之功而宠信他'),('景延广','受宠并掌宿卫兵，使大臣难以反对')],year=None,when='石重贵即位后的政务概述，具体起止年月未载',place='后晋',note='这是主书对权势原因的解释，不推所有大臣在所有议题均赞同。')
add('zhiyuan_recruits_prepares','刘知远担心景延广招致入侵，增加募兵并奏请设置兴捷、武节等军',28,'河东节度使',None,[('刘知远','担心景延广招致契丹入侵，增加募兵，并奏请设置十余军备战')],when='943年相关交涉后，具体日期未载',place='河东',note='奏置为请求设军，本段未明确批准情况，不补军额；兴捷武节为明确军名，十余是军数，不是人数。')
jing='xinwudaishi-029-jing-khitan'
sup('jing_tells_qiao_grandson_policy',28,jing,'延廣謂契丹使者喬瑩曰：','《新五代史》将这个外交场景中的乔荣写作契丹使者喬瑩。','从相同称孙不臣、十万剑、书纸和归报场景校核同人，姓名异文原字保留待纸本核；使者与主书商贸官身份并列。',relation='adds')
sup('jing_orders_written_record',28,jing,'因請載于紙，以備遺忘。延廣敕吏具載以授瑩，','《新五代史》也记喬瑩请求写下讲话，景延广命吏员记录交给他。','同一纸上记录与外交对话，不把本传初出帝立的背景全部定为942年。')
sup('qiao_reports_khitan',28,jing,'瑩藏其書衣領中以歸，具以延廣語告契丹，契丹益怒。','《新五代史》补充乔荣把书藏在衣领里带回，完整报告契丹。','仅补同一报告细节，契丹益怒为史书描述。',relation='adds')
claim('person',people['乔荣'],'name','《新五代史》同一外交记载作喬瑩，按行动及对话对应乔荣。',28,'喬瑩','异字不自动按繁简互换，具体书面记录、说话内容及归报相同，保留异文待纸本核。',source=jing,relation='adds')
# 29: reports and orders are distinguished from proven execution.
add('liyi_yin_reports_yimin','李彝殷向朝廷奏报李彝敏作乱',29,'甲午，','作乱之状，',[('李彝殷','以定难节度使身份奏报李彝敏作乱'),('彝敏','被李彝殷奏报作乱')],when='943年九月甲午',place='后晋',note='甲午是奏报日，不套作八月逃亡或处刑日。')
add('yimin_execution_order','后晋下诏逮捕李彝敏，送夏州处斩',29,'诏执',None,[('帝','下诏逮捕李彝敏，送夏州处斩'),('彝敏','被下诏逮捕送夏州处斩')],when='943年九月甲午奏报后',place='拟送夏州',note='主书诏及旧纪诏均主要记命令，本批不据此填确切执行日或确认死亡年份。')
sup('yimin_execution_order',29,ann,'送夏州處斬。','《旧五代史》也保存送夏州处斩的诏令。','引用是诏令，不冒充另一个已经执行的死亡证明。')
# 30: the October investiture and the earlier marriage history have different dates.
add('feng_empress_invested','石重贵立吴国夫人冯氏为皇后',30,'冬，','为皇后。',[('帝','立吴国夫人冯氏为皇后'),('冯夫人','由吴国夫人被立为皇后')],when='943年十月戊申',place='后晋')
sup('feng_empress_invested',30,'xinwudaishi-009-943-return','冬十月戊申，立馮氏為皇后。','《新五代史》本纪也记十月戊申立冯氏为皇后。','与家人传居丧时纳之为后的概述分清，正式册立日据本纪。')
add('chongyin_adopted','石敬瑭爱少弟石重胤，将他收养为子',30,'初，','养以为子；',[('高祖','将石重胤收养为子'),('重胤','被石敬瑭收养')],year=None,when='石敬瑭留守邺都前的追述，具体年月未载',place='后晋建立前',note='主书少弟与新史不知亲疏并列，只明确养父关系，不造同父血亲。')
add('chongyin_feng_marriage','石敬瑭为石重胤娶冯濛之女',30,'及留守','为其妇。',[('高祖','留守邺都时为石重胤娶冯濛之女'),('重胤','娶冯濛之女为妻'),('冯夫人','嫁给石重胤')],year=None,when='石敬瑭留守邺都时，具体年月未载',place='邺都',note='安喜为冯濛籍贯，不将它直接当婚礼地点；具体婚礼仪式未载。')
add('chongyin_dies_feng_widow','石重胤早逝，冯氏守寡',30,'重胤早卒，','冯夫人寡居，',[('重胤','早逝'),('冯夫人','夫亡后守寡')],year=None,when='石重贵纳冯氏之前，确切年月主书未载',place='地点未载',note='早卒不定943年；新史高祖反时死作独立年代背景，不补生日年龄。')
sup('chongyin_dies_feng_widow',30,'xinwudaishi-017-shi-chongyin','而敬威、敬德、重胤、重英，高祖反時死。','《新五代史》将石重胤之死放在石敬瑭起兵反唐时期。','独立纪年背景，不据相邻943年册后条下反推943年死亡；具体处刑者本句未载。',relation='adds')
add('shi_takes_feng_mourning','石敬瑭去世、尚未安葬时，石重贵纳冯氏入宫',30,'有美色，','帝遂纳之。',[('帝','见冯氏而喜爱，在石敬瑭死后未葬时纳她入宫'),('冯夫人','石敬瑭死后未葬时被石重贵纳入宫中')],year=942,when='942年石敬瑭去世后、安葬前，具体日期未载',place='后晋',note='高祖崩在前批942年明确，故此追述用942年，不能套943年十月；美色为史书描述。')
add('shi_claims_dowager_marriage_order','群臣道贺时，石重贵声称纳冯氏是皇太后的命令',30,'群臣皆贺，','不任大庆。”',[('帝','向冯道等声称此事是皇太后的命令'),('冯道','与群臣一同道贺并听到石重贵说法')],year=942,when='上述942年纳冯氏时，具体日期未载',place='后晋',note='声称是石重贵的话，不能当作太后确有此命；后文太后恚怒与其说法分开。')
add('shi_feng_drink_before_coffin','石重贵与冯氏饮酒，在石敬瑭灵柩前祝告并取笑',30,'群臣出，','夫人与左右皆大笑。',[('帝','与冯氏饮酒，经过灵柩时祝告，自称今日作新婿并笑'),('冯夫人','与石重贵饮酒，和身边人一起笑')],year=942,when='上述942年纳冯氏时，具体日期未载',place='石敬瑭灵柩前',note='醊为祭奠祝告，保留话语归属，不推亡者回应；左右未具名，不追加人物。')
add('dowager_angry_marriage','皇太后对石重贵纳冯氏生气，但无可奈何',30,'太后虽恚，','而无如之何。',[('太后','因石重贵纳冯氏而生气，但无可奈何')],year=942,when='上述942年纳冯氏时，具体日期未载',place='后晋',note='太后是石敬瑭妻永宁公主，不混成石重贵生母安氏；不能认定她已实际废婚或处分。')
add('feng_participates_government','冯氏被立为皇后后参与政务',30,'既正位','颇预政事。',[('冯夫人','正位皇后后参与政务')],when='943年十月册后之后，具体日期未载',place='后晋',note='颇预不写成掌握全部政权或临朝称制。')
add('feng_yu_promoted','石重贵迅速擢升冯玉为端明殿学士、户部侍郎，让他参与议政',30,'后兄玉，',None,[('帝','迅速擢升冯玉，邀其议政'),('冯玉','由礼部郎中、盐铁判官被擢升为端明殿学士、户部侍郎')],when='943年册后条下的任职概述，确切日期未载',place='后晋',note='两书此前职衔路径不完全相同，独立补证保留；不把后续樞密使等任职提前。')
feng='xinwudaishi-017-feng-empress'
sup('chongyin_feng_marriage',30,feng,'高祖留守鄴都，得濛驩甚，乃為重胤娶濛女，','《新五代史》也记石敬瑭留守邺都时，为石重胤娶冯濛之女。','高祖此处为石敬瑭，婚事主语明确。')
sup('shi_takes_feng_mourning',30,feng,'高祖崩，梓宮在殯，出帝居喪中，納之以為后。','《新五代史》家人传也记石重贵在居丧期间纳冯氏。','家人传纳之为后与本纪943年戊申册立区分，不据概述将正式册后改942年。')
sup('shi_claims_dowager_marriage_order',30,feng,'皇太后之命，與卿等不任大慶。','《新五代史》也记石重贵向群臣声称皇太后之命。','两书记相同言辞，仍只证明皇帝声称，非太后命令独立证据。')
sup('feng_yu_promoted',30,'jiuwudaishi-089-feng-yu','俄自知制誥、中書舍人出為潁州團練使，遷端明殿學士、戶部侍郎，','《旧五代史》记冯玉由知制诰、中书舍人出任颍州团练使，再任端明殿学士、户部侍郎。','正文与附引通鉴分清，任职路径独立保留，不覆盖主书礼部郎中盐铁判官表述。',relation='adds')
E['feng_yu_yingzhou']=event('feng_yu_yingzhou','石重贵任冯玉为检校尚书右仆射、颍州团练使',30,'丙子，以金部郎中、知制誥馮玉為檢校尚書右僕射，充潁州團練使。',[('帝','任冯玉为检校尚书右仆射、颍州团练使'),('冯玉','由金部郎中、知制诰获新任命')],when='943年九月丙子',place='后晋',source=ann,note='旧纪具体任官为独立补充，九月在十月册后前，不把传记概述顺序硬改成本次任官时间。')
relationship('高祖','重胤','养父',30,'高祖爱少弟重胤，养以为子；','养以为子明确收养；新史血亲亲疏不明，暂不另建唯一同父兄弟关系。')
relationship('冯濛','冯夫人','父亲',30,'娶副留守安喜冯濛女为其妇。','父女及父亲职务籍贯明确，不推冯濛与其他冯氏亲属关系。')
relationship('冯夫人','重胤','妻子',30,'娶副留守安喜冯濛女为其妇。','原文明确先嫁石重胤，未给婚期，后来改嫁事实分别引用。')
relationship('冯夫人','帝','妻子',30,'立吴国夫人冯氏为皇后。','册皇后与婚前旧配偶分别记录；不用反向丈夫边制造重复关系。')
relationship('冯玉','冯夫人','兄长',30,'后兄玉，时为礼部郎中、盐铁判官，','原文明示冯玉为冯皇后之兄，方向明确。')
# 31–33: retirement command and detailed campaign sequence.
add('hongya_retirement_order','刘弘熙命韶王刘弘雅退休',31,'汉主',None,[('汉主','命韶王弘雅退休'),('弘雅','被命令退休')],when='943年十月条下，具体日期未载',place='南汉',note='致仕是退出官职，不等于被杀或罢除王号。')
add('yan_en_campaign_order','李璟派严恩率兵讨张遇贤',32,'唐主遣','将兵讨张遇贤，',[('唐主','派严恩率兵讨张遇贤'),('严恩','以洪州营屯都虞候身份率兵讨伐')],when='943年十月条下，具体日期未载',place='虔州一带')
add('bian_hao_monitor','李璟任边镐为讨张遇贤军监军',32,'以通事舍人','为监军。',[('唐主','任边镐为监军'),('镐','由通事舍人出任讨伐军监军')],when='943年十月条下，具体日期未载',place='虔州一带')
add('bai_changyu_adviser','边镐以白昌裕为谋主',32,'镐用','为谋主，',[('镐','任用白昌裕为谋主'),('白昌裕','出任边镐的谋主')],when='943年十月讨张遇贤期间，具体日期未载',place='虔州一带',note='籍贯原文虞州保留待核，不强改虔州。')
add('bian_repeated_victories','边镐率军进攻张遇贤，接连获胜',32,'击张遇贤；','屡破之。',[('镐','率军进攻张遇贤，接连获胜'),('张遇贤','接连战败')],when='943年十月讨伐期间，具体日期未载',place='虔州一带',note='屡破只给多次胜利概述，不造没有日期、地点和战果的多条战役。')
add('zhang_oracle_silent','史书记张遇贤再求神言无回应，部众害怕',32,'遇贤祷于神，','其徒大惧。',[('张遇贤','史书记他求神而没有再获回应，部众因此害怕')],when='943年十月战败期间，具体日期未载',place='张遇贤军营',note='神不复言为史载传闻，不证明神灵存在或效果。')
add('bai_proposes_rear_attack','白昌裕建议伐木开道，绕到张遇贤军营后袭击',32,'昌裕劝','出其营后袭之，',[('白昌裕','建议伐木开道绕营后袭击'),('镐','收到白昌裕建议')],when='943年十月讨伐期间，具体日期未载',place='张遇贤军营周边',note='劝为建议，后句张遇贤弃众是结果，但此句未给伐木日期、道路长度或具体作战兵力。')
add('zhang_flees_to_li_tai','张遇贤丢下部众，投奔别将李台',32,'遇贤弃众','奔别将李台。',[('张遇贤','丢下部众，投奔李台'),('李台','张遇贤投奔的别将')],when='943年十月上述战败后，具体日期未载',place='李台驻地未载')
add('li_tai_surrenders_zhang','李台擒住张遇贤，向南唐投降',32,'台知','执遇贤以降，',[('李台','认为神言没有应验，擒张遇贤投降'),('张遇贤','被李台擒住交出')],when='943年十月上述逃亡后，具体日期未载',place='地点未载',note='知神无验是李台判断，投降对象结合南唐讨伐背景；不能推受降者一定是边镐本人。')
add('zhang_executed_jinling','张遇贤在金陵市被斩',32,'斩于',None,[('张遇贤','在金陵市被斩')],when='943年十月投降后，具体日期未载',place='金陵市',note='原文未列具体行刑者，不以相邻李台自动推李台亲自斩杀。')
zd='xinwudaishi-062-zhang-defeat'
sup('yan_en_campaign_order',32,zd,'景遣洪州營屯虞候嚴思、通事舍人邊鎬率兵攻之。','《新五代史》同一战役记洪州营屯虞候嚴思与边镐率兵攻张遇贤。','严恩与严思依据同战役同军职校核对应，原字保留待纸本，不另建重复严思。',relation='adds')
sup('bian_repeated_victories',32,zd,'冬十月，破虔州妖賊張遇賢。','《新五代史》明确此战在冬十月获胜。','妖贼为史书定性，展示只称张遇贤；不补确切日期。')
sup('li_tai_surrenders_zhang',32,zd,'遇賢問神，神不復語，羣盜皆懼，遂執遇賢以降。','《新五代史》也记部众因神言不再回应而害怕，擒张遇贤投降。','新史未具名李台，只支持被擒投降与传闻叙述，不补全部部众亲自擒获。')
claim('person',people['严恩'],'name','《新五代史》此战领兵者写作嚴思，主书作严恩。',32,'嚴思','同一洪州营屯军职、边镐及张遇贤战事对应同人，姓名异文待纸本校核。',source=zd,relation='adds')
claim('person',people['张遇贤'],'death_year','张遇贤于943年十月战败被擒后，在金陵市被斩。',32,'台知神无验，执遇贤以降，斩于金陵市。','原文死亡明确，复用已录主体，具体日期未载。')
add('sheng_southern_sacrifice','刘弘熙在南郊祭祀，实行大赦，改元乾和',33,'十一月，',None,[('汉主','在南郊祭祀，大赦并改元乾和')],when='943年十一月丁亥',place='南汉南郊',note='乾和与三月应乾分别记改元动作，不把一个国家复制成新朝。')
sup('sheng_southern_sacrifice',33,'xinwudaishi-065-liu-sheng-accession','冬，晟祀天南郊，改元曰乾和，','《新五代史》也记刘晟冬季祭天南郊，改元乾和。','只支持祭祀与改元，未给丁亥或大赦，支持范围分清。')
for x in B['people']:
 if x['name']=='拓跋崇斌':
  x['death_year']=943
  claim('person',x['key'],'death_year','据《旧五代史》九月甲午奏报，拓跋崇斌已经被捕斩。',26,'衙內都指揮使拓拔崇斌等五人作亂，當時收擒處斬訖。','死亡已在奏报前发生，实际处刑日未载，不把奏报日当死亡日。',source=ann,relation='adds')
for row in B['person_relationships']:
 if row['person_a_key']=='person_冯氏（石重贵后）' and row['person_b_key']=='person_石重胤':
  row['description']='冯氏先嫁石重胤为妻，石重胤早逝后守寡。'
  for c in B['claims']:
   if c['subject_table']=='person_relationship' and c['subject_key']==row['key']:c['claim_text']=row['description']
 if row['person_a_key']=='person_冯氏（石重贵后）' and row['person_b_key']=='person_石重贵':
  row['description']='冯氏在942年被石重贵纳入宫中，943年十月正式被立为皇后。'
  for c in B['claims']:
   if c['subject_table']=='person_relationship' and c['subject_key']==row['key']:c['claim_text']='943年十月冯氏被立为石重贵的皇后，配偶关系明确。'

reviews={25:'乙卯封保宁王与太后屡欲害、李璟保护概述分开，欲不等于已杀。',26:'拓跋谋乱李敏将助、事泄、八月辛未逃延分开。旧纪九月奏报带270亲属与作乱攻城、已捕斩独立补证，奏日不套事日。兄弟方向明确。',27:'九月尊安氏有新旧戊寅补，生母与太后永宁公主区分；谨事和友爱为在位概述不补所有弟弟参与。',28:'初随赵及回图贸易为追述，囚荣夺货和杀商不造明确发令者；戊子释放、称孙外交、军械声称、纸证、归报、契丹决入寇与扣使、谢议被沮、宿卫权势及刘备战逐项分开。乔荣喬瑩异文按特定场景校核，翁孙不造血缘，奏置不等于已经建军。',29:'甲午奏报与诏送夏斩分开，未独证执行不填确切死亡日。',30:'十月戊申册后与此前收养婚姻丧亡、942殡中纳后和皇帝声称太后命分开。新史亲疏不明，收养明确；母亲太后不混。冯玉任职路径分别引用，旧九月颖州任命独补不套十月。',31:'命致仕为退出官职，非已被杀或削王号。',32:'遣严恩、任边监、用白谋、屡胜、神言沉默、伐木绕后建议、弃众、李台擒降与金陵斩分开。严恩严思字形留待核，虞州不强改虔。',33:'十一丁亥南郊祭祀赦改乾和有新史冬祭改元补，不给新史未载大赦和精确日。'}
assert not (P/'publication.json').exists()
for n in range(25,34):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=283,year=943,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,34)],next_paragraph=Q[34]['id'],next_volume=283,next_year=943,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key='jiuwudaishi-089-feng-yu',note='只用于冯玉当前任职和亲属补证，后续军政与北迁不提前录入。')],coverage='连续第25—33段，原73—81行；八月至十一月及追述，后接第34段钱弘佐纳仰氏。',source_issues_review='乔荣喬瑩、严恩严思及李彝敏彜字等异文保留；石重胤亲疏未明不建唯一血亲，养父明确；虞州原地名、冯玉职衔路径分别保留待核，纸本未核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,34)],plain_language_review='首次检查标题正文、人物、角色、关系与事实说明。当前晋帝石重贵、唐主李璟、汉主刘弘熙身份明确；奏报诏令、计划执行和942年追述与943年册后分清，原文保留。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
