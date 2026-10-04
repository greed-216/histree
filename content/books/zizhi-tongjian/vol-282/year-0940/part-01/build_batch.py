# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 940 paragraphs 1–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,36))
specs=[(d.name,d,'c30e8592e48c53567d2d07454baccf80e3e0ec55','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-939-autumn','jiuwudaishi-133-ma-xifan']:
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
main_sources = ['tongjian-282-939-autumn','tongjian-282-940-spring']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0940-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-079-february':'卷79·晋高祖纪·天福五年二月','jiuwudaishi-079-march':'卷79·晋高祖纪·天福五年三月','jiuwudaishi-079-april':'卷79·晋高祖纪·天福五年四月','xinwudaishi-066-chu-surrender':'卷66·楚世家·彭士愁归降与铜柱','xinwudaishi-068-min-conflict':'卷68·闽世家·王延政','tongjian-282-940-spring':'卷282·天福五年春夏'}
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
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(1, 11):
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
    labels={'jiuwudaishi-079-february':'卷79·晋高祖纪·天福五年二月','jiuwudaishi-079-march':'卷79·晋高祖纪·天福五年三月','jiuwudaishi-079-april':'卷79·晋高祖纪·天福五年四月','xinwudaishi-066-chu-surrender':'卷66·楚世家·彭士愁归降与铜柱','xinwudaishi-068-min-conflict':'卷68·闽世家·王延政','tongjian-282-940-spring':'卷282·天福五年春夏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月条下' if n<=2 else '二月条下' if n<=5 else '二月至三月' if n==6 else '三月条下' if n<=8 else '四月条下'
        citation = f'卷282·后晋天福五年（940；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0940_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=940, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='940年'+('正月' if n<=2 else '二月' if n<=6 else '三月' if n<=8 else '四月')+'条下，具体日期未载'
    key = 'event_zztj_282_0940_' + code
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
        edge = 'participation_zztj_282_0940_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0940_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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




ALIASES.update({'唐主':'李昪','曦':'王延羲','闽王':'王延羲','延政':'王延政','元瓘':'钱传瓘','师暠':'彭师暠','业翘':'业翘（闽监军）','李德充':'李德珫'})
NEW_DESCRIPTIONS={
'彭师暠':'彭士愁的儿子。940年受父亲派遣，率诸酋长向楚交出溪、锦、奖三州官印，请求归降。生卒年未载。',
'业翘（闽监军）':'王延羲派往建州监督军队的亲吏，与王延政发生争执后逃往南镇，后来与杜汉崇逃往福州。姓名沿《资治通鉴》业翘，不与叶翘自动合并。生卒年未载。',
'杜汉崇':'闽国教练使，受王延羲派遣监督南镇军，与业翘一起向王延羲报告王延政的隐事，随后逃往福州。《新五代史》相关故事中的监军名为杜建崇，姓名差异待核。生卒年未载。',
'潘师逵':'闽国统军使。940年与吴行真率军进攻王延政，驻建州城西；三月遭王延政夜袭，被陈诲杀死。出生年未载。',
'吴行真':'闽国统军使。940年与潘师逵率军进攻王延政，驻建州城南；三月在王延政军队渡水进攻以前弃营逃走。生卒年未载。',
'薛万忠':'吴越内都监使。940年与仰仁诠受钱传瓘派遣，率军救援建州的王延政。生卒年未载。',
'蔡弘裔':'闽国都军使。940年三月受潘师逵派遣，带三千兵出战，被王延政派出的林汉彻等在茶山击败。生卒年未载。',
'林汉彻':'王延政麾下将领。940年三月与其他将领在茶山击败蔡弘裔所率军队。生卒年未载。',
'李德珫':'后晋建雄节度使。940年三月调任北都留守。《旧五代史》同次从晋州到北京的调任写作李德充，按任职与行动对应识别为同一人，保留原文字形说明。生卒年未载。',
'王令谦':'安从进的元随都押牙，因劝谏安从进被杀。史书未在此处明确劝谏与遇害的具体年份。',
'潘知麟':'安从进麾下押牙，因劝谏安从进被杀。史书未在此处明确劝谏与遇害的具体年份。',
'陈诲':'建安人，王延政麾下战棹都头。940年三月在夜袭中杀死潘师逵。生卒年未载。'}
NEW_ALIASES={'彭师暠':['彭師暠'],'业翘（闽监军）':['业翘','業翹'],'杜汉崇':['杜漢崇'],'潘师逵':['潘師逵'],'吴行真':['吳行真'],'薛万忠':['薛萬忠'],'蔡弘裔':[],'林汉彻':['林漢徹'],'李德珫':['李德充'],'王令谦':['王令謙'],'潘知麟':[],'陈诲':['陳誨']}
feb='jiuwudaishi-079-february';mar='jiuwudaishi-079-march';apr='jiuwudaishi-079-april';chu='xinwudaishi-066-chu-surrender';minbook='xinwudaishi-068-min-conflict';oldchu='jiuwudaishi-133-ma-xifan'
add('shi_receives_min_envoys','石敬瑭接见此前被拘的闽国使者郑元弼等',1,'春，正月，','郑元弼等。',[('帝','接见闽国使者'),('郑元弼','以闽国使者身份受接见')],note='衔接939年使者被拘的记载；王继鹏已死，此处仍是处理此前出使事务。')
add('zheng_requests_punishment','郑元弼为王继鹏的失礼辩解，并请求以死赎罪',1,'元弼曰：','以赎昶罪。”',[('郑元弼','辩解并请求以死赎罪'),('帝','听取郑元弼的辩解')],description='郑元弼说，王继鹏不懂礼义，皇帝不必因他的言语喜怒；自己出使失职，愿接受处死以赎王继鹏之罪。',note='不将使者的贬称当作网站的民族判断；请求处死不等于被实际处死。')
add('shi_releases_min_envoys','石敬瑭下诏释放郑元弼等闽国使者',1,'帝怜之，',None,[('帝','怜悯郑元弼并下诏释放使者'),('郑元弼','获诏释放')],when='940年正月辛未')
add('liu_burns_peng_camp','刘勍等借大风用火箭焚寨，进攻彭士愁',2,'楚刘勍等','而攻之，',[('刘勍','与其他楚军将领用火箭攻寨'),('彭士愁','所据营寨受到楚军火攻')],place='彭士愁营寨')
add('peng_flees_mountains','彭士愁率部逃入奖州、锦州深山',2,'士愁帅','深山，',[('彭士愁','率部逃入深山')],place='奖州、锦州深山')
add('peng_surrenders_seals','彭士愁派彭师暠交出三州官印，请求归降楚国',2,'乙未，',None,[('彭士愁','派遣儿子请求归降'),('彭师暠','率诸酋长交出溪、锦、奖三州官印')],when='940年正月乙未',description='彭士愁派儿子彭师暠率诸酋长，向楚交出溪、锦、奖三州官印，请求归降。',note='本句是请求归降，后续安置在下一段；人数未载，三州官印不与其他书的五州求盟强行统一。')
relationship('彭士愁','彭师暠','父亲',2,'遣其子师暠帅诸酋长','其子明确对应彭士愁；记录彭士愁是彭师暠的父亲。')
sup('peng_surrenders_seals',2,chu,'遣其子師暠率諸蠻酋降于勍。','《新五代史》也记彭士愁派儿子师暠率诸酋长向刘勍归降。','传记没有明确月日，用于人物与归降行动的补证，不据其后叙事提前录入各地归附。')
sup('peng_surrenders_seals',2,oldchu,'士愁以五州乞盟，乃銘於銅柱。','《旧五代史》记彭士愁以五州求盟；《资治通鉴》记交出三州官印。','两书所述州数与行为范围不同，是否指相同范围尚未裁定，分别保留。',relation='conflicts')
add('an_audience','安彦威入朝，石敬瑭赞许他对契丹谦让',3,'二月，','深称朕意。”',[('安彦威','入朝并得到皇帝赞许'),('帝','将与契丹的交往解释为守信报义')],when='940年二月庚戌',description='北都留守安彦威入朝。石敬瑭说，契丹曾援救自己，现在应以信义相报，并赞许安彦威在契丹不断索求时仍能谦让。',note='信义是皇帝解释外交政策的言论，不作为网站对契丹索求的独立评价。')
sup('an_audience',3,feb,'庚戌，北京留守安彥威來朝，帝慰接甚厚，賜上樽酒。','《旧五代史》也记二月庚戌安彦威入朝，并补记皇帝厚待、赐酒。','纪日相合，北京与北都为本次任职的两种表述。')
add('an_replies','安彦威回应，皇帝为百姓尚且谦让，自己更应如此',3,'对曰：','上悦。',[('安彦威','以皇帝为百姓谦让为由作答'),('帝','听到答复后高兴')],when='940年二月庚戌',description='安彦威回应说，皇帝为百姓尚且以谦辞和厚礼侍奉契丹，自己谦让又有什么可说。石敬瑭听后高兴。',note='为百姓属于安彦威给出的理由，不据此确定政策实际效果。')
add('liu_returns_changsha','刘勍率军返回长沙',3,'刘勍引兵','长沙。',[('刘勍','率军返回长沙')],place='长沙')
add('ma_resettles_xizhou','马希范迁溪州治所，并奏请彭士愁担任溪州刺史',3,'楚王希范徙','溪州刺史，',[('马希范','迁移溪州并奏请任官'),('彭士愁','被奏请担任溪州刺史')],place='溪州',description='马希范把溪州迁到较便利的地方，并上表请求让彭士愁担任溪州刺史。',note='便地未明具体地点，表是上表奏请，不补后晋已经批准的任命。')
add('liu_jinzhou','马希范任刘勍为锦州刺史，此后当地部众服从楚国',3,'以刘勍','服于楚。',[('马希范','任刘勍为锦州刺史'),('刘勍','获任锦州刺史')],place='锦州',description='马希范任刘勍为锦州刺史。《资治通鉴》随后记当地部众归服楚国。',note='归服按史书范围记，不扩成现代民族或所有西南地区统一归附。')
add('ma_copper_pillar','马希范在溪州铸立铜柱，刻上盟誓',3,'希范自谓',None,[('马希范','自称伏波将军后裔，铸立刻有盟誓的铜柱')],place='溪州',description='马希范自称伏波将军的后裔，用五千斤铜铸柱，柱高一丈二尺，入地六尺，在柱上刻下盟誓并立在溪州。',note='斤、丈、尺沿原单位，不换算现代尺寸；自称祖系不建立确定的远祖血缘关系。')
sup('ma_copper_pillar',3,chu,'希範乃立銅柱以為表，命學士李臯銘之。','《新五代史》也记马希范立铜柱，并补记由学士李皋撰铭。','李皋沿本书原字展示；与已录李弘皋是否同人尚无充分证据，不作合并。',relation='adds')
sup('ma_copper_pillar',3,oldchu,'希範自言漢伏波將軍援之後，故鑄銅柱以繼之。','《旧五代史》明确指出马希范自称汉代伏波将军马援的后裔，铸柱以继其事。','两书均属马希范自称，不升级为已考定祖系。',relation='adds')
add('yang_lian_dies','杨琏祭谒平陵归来后，在船上醉后去世',4,'唐康化', '卒于舟中，',[('杨琏','祭谒平陵归来后，在船上醉后去世')],place='归途船中',description='康化节度使兼中书令杨琏祭谒平陵归来，一天夜里大醉，随后在船中去世。',note='记载未明具体日子或医学死因，不把大醉直接判定为酒精中毒。')
add('yang_lian_posthumous','李昪追封杨琏为弘农靖王',4,'唐主',None,[('唐主','追封杨琏并定谥'),('杨琏','死后被追封为弘农靖王')],note='封号与谥号合写为弘农靖王；南唐皇帝为李昪，不套用后唐君主。')
background=dict(year=None,when='940年二月进攻建州以前的背景，具体日期未载')
add('min_suspicion','史书记王延羲即位后苛虐，并猜忌宗族、追究旧怨',5,'闽王曦既立，','多寻旧怨。',[('曦','被史书评价为骄淫苛虐并猜忌宗族')],description='《资治通鉴》评价王延羲即位后的作风为骄纵、淫乱、苛刻残暴，并记他猜忌宗族，常追究旧怨。',note='作风评价明确归史书；跨越即位后的持续经历不硬定在940年。',**background)
add('min_letters','王延政多次写信劝谏，王延羲回信责骂',5,'其弟','复书骂之；',[('延政','多次写信劝谏兄长'),('曦','因弟弟劝谏而发怒，并回信责骂')],**background)
relationship('王延政','王延羲','弟弟',5,'其弟建州刺史延政','其弟所指为王延羲之弟，按有方向的弟弟关系记录。')
sup('min_letters',5,minbook,'曦立，為淫虐，延政數貽書諫之。','《新五代史》也记王延政多次写信劝谏王延羲。','相近记载作为补证；该段结尾建国称殷属于后续经历，不提前放入940年。')
relationship('王审知','王延政','父亲',5,'延政，審知子也。','《新五代史》明确王延政是王审知之子；引用独立出处，复用父亲主体。',source=minbook)
add('min_monitors','王延羲派业翘监督建州军、杜汉崇监督南镇军',5,'遣亲吏','监南镇军，',[('曦','派遣亲吏和教练使监督两支军队'),('业翘','受派监督建州军'),('杜汉崇','受派监督南镇军')],note='业翘沿本段身份新建，不与叶翘自动合并；杜汉崇与他书杜建崇的姓名差异保留待核。',**background)
sup('min_monitors',5,minbook,'曦怒，遣杜建崇監其軍，延政逐之，','《新五代史》在相关故事中写监军为杜建崇，《资治通鉴》写杜汉崇，并另列业翘。','人名及监军叙述有差异，未将杜建崇直接登记为已核别名，也未删除主书的另一名监军。',relation='conflicts')
add('min_reports','业翘与杜汉崇向王延羲报告王延政隐事，兄弟猜忌加深',5,'二人争','积相猜恨。',[('业翘','搜集并报告王延政的隐事'),('杜汉崇','搜集并报告王延政的隐事'),('曦','收到监军报告'),('延政','与兄长的猜忌加深')],**background)
add('ye_quarrel','业翘质问王延政是否反叛，王延政欲杀他，业翘逃走',5,'一日，','翘奔南镇，',[('业翘','因议事不合质问王延政，随后逃往南镇'),('延政','受质问后想杀业翘')],place='建州、南镇',note='是否反叛是业翘的质问；欲斩是王延政的意图，未记业翘被杀。',**background)
add('yan_attacks_nanzhen','王延政攻败南镇戍兵，业翘与杜汉崇逃往福州',5,'延政发兵',None,[('延政','出兵攻败南镇戍兵'),('业翘','逃往福州'),('杜汉崇','逃往福州')],place='南镇、福州',description='王延政出兵攻打南镇，击败驻军。业翘与杜汉崇逃往福州，西部边地的戍兵也溃散。',note='此段作为二月进攻前的起因叙述，未给明确年份，不将未载姓名的西部守将补成新人物。',**background)
add('min_invades_jianzhou','王延羲派潘师逵、吴行真率四万兵进攻王延政',6,'二月，','击延政。',[('曦','派遣军队进攻王延政'),('潘师逵','与吴行真共同率军进攻'),('吴行真','与潘师逵共同率军进攻'),('延政','遭兄长派兵进攻')],when='940年二月，具体日期未载',place='建州',note='四万人是两将统率的合计，不各记四万。')
add('min_camps_burns','潘师逵、吴行真隔水设营，烧毁建州城外房屋',6,'师逵军于','焚城外庐舍。',[('潘师逵','驻城西，与吴行真隔水设营、烧毁民居'),('吴行真','驻城南，与潘师逵隔水设营、烧毁民居')],place='建州城西、城南',when='940年二月，具体日期未载')
add('yan_asks_wuyue','王延政向吴越求援',6,'延政求救','吴越，',[('延政','向吴越请求救援')],when='940年二月，吴越出兵以前')
add('qian_sends_relief','钱传瓘派仰仁诠、薛万忠率四万兵救援建州',6,'壬戌，','将兵四万救之，',[('元瓘','派遣四万兵救援王延政'),('仰仁诠','受命率军救援'),('薛万忠','受命率军救援')],when='940年二月壬戌',place='吴越、建州',note='此时记派兵，不提前记作已经到达；四万是两将合计。')
add('lin_remonstrates','林鼎反对吴越出兵，钱传瓘没有采纳',6,'丞相林鼎','不听。',[('林鼎','就出兵救援提出劝谏'),('元瓘','没有采纳林鼎劝谏')],when='940年二月出兵救援时，具体日期未载',note='原文未列林鼎劝谏的具体理由，不编写判断或对话。')
add('cai_chashan_defeat','蔡弘裔率三千兵出战，被林汉彻等击败于茶山',6,'三月，',None,[('潘师逵','派蔡弘裔率三千兵出战'),('蔡弘裔','率军出战并战败'),('延政','派林汉彻等迎战'),('林汉彻','与其他将领在茶山击败敌军')],when='940年三月戊辰',place='茶山',description='潘师逵分出三千兵，派蔡弘裔出战。王延政派林汉彻等在茶山击败这支军队，史书记斩首一千余级。',note='千余保留为一千多，不精确成一千；没有证据表明蔡弘裔本人在此战死亡。')
add('retirement_denied','安彦威、王建立请求退休，石敬瑭没有批准',7,'安彦威','不许。',[('安彦威','请求退休'),('王建立','请求退休'),('帝','拒绝两人的退休请求')])
add('liu_yedu','石敬瑭任刘知远为邺都留守',7,'辛未，','为鄴都留守，',[('帝','任命刘知远'),('刘知远','由归德节度使等职任邺都留守')],when='940年三月辛未',place='邺都')
sup('liu_yedu',7,mar,'辛未，宋州歸德軍節度使、侍衛親軍馬步軍都指揮使劉知遠加特進，改鄴都留守、廣晉尹，典軍如故。','《旧五代史》补记刘知远加特进、任广晋尹，并继续掌军。','三月辛未与主书相合；继续掌军不误写为被解除军职。',relation='adds')
add('an_guide','石敬瑭调安彦威为归德节度使、兼侍中',7,'徙彦威','加兼侍中。',[('帝','调任安彦威并加兼侍中'),('安彦威','由北都留守调任归德节度使')],when='940年三月辛未',place='归德')
sup('an_guide',7,mar,'以北京留守安彥威為宋州節度使。','《旧五代史》也记安彦威从北京留守调任宋州节度使。','宋州为归德军所在州，此处用同次任命对照，不补现代坐标。')
add('wang_zhaoyi','石敬瑭调王建立为昭义节度使，并封韩王',7,'癸酉，','进爵韩王；',[('帝','调王建立并进封韩王'),('王建立','调任昭义节度使，封韩王')],when='940年三月癸酉',place='昭义')
sup('wang_zhaoyi',7,mar,'癸酉，以青州節度使王建立為昭義軍節度使，進封韓王，','《旧五代史》也记三月癸酉王建立由青州调任昭义、进封韩王。','日期与任官一致。')
add('liao_qin_transfer','后晋因王建立出身辽州，将辽、沁二州划入昭义',7,'以建立','隶昭义。',[('帝','将两州划归昭义'),('王建立','其出身成为划州的史载理由')],when='940年三月癸酉',place='辽州、沁州、昭义',note='籍贯是主书所述划州理由；未补未载的疆域边界和坐标。')
sup('liao_qin_transfer',7,mar,'仍割遼、沁二州為昭義屬郡，以建立本遼州人，用成其衣錦之美也。','《旧五代史》也记将辽、沁二州划入昭义，并解释为使王建立衣锦还乡。','衣锦还乡属于史书解释，不补未载的个人请求。')
add('li_beidu','石敬瑭调李德珫为北都留守',7,'徙建雄','为北都留守。',[('帝','调任李德珫'),('李德珫','由建雄节度使调任北都留守')],when='940年三月癸酉；日期据《旧五代史》同次调任条',place='北都',note='主书在癸酉条后接记；旧史同次从晋州调北京写李德充，按职务及动作对应识别同人，保留异字说明。')
sup('li_beidu',7,mar,'以晉州節度使李德充為北京留守，','《旧五代史》在三月癸酉条下记李德充从晋州调任北京留守；《资治通鉴》写李德珫。','同次任官与前后职务对应，姓名字形仍待版本校核；未改写原文。',relation='adds')
E['huangfu_jinzhou']=event('huangfu_jinzhou','石敬瑭调皇甫遇为晋州节度使',7,'以潞州節度使皇甫遇為晉州節度使。',[('帝','调任皇甫遇'),('皇甫遇','由潞州调任晋州节度使')],source=mar,when='940年三月癸酉条下',place='晋州',description='《旧五代史》在李德珫调离晋州的同一条记，皇甫遇从潞州调任晋州节度使。',note='由独立出处补充此次军镇交接；不将此句冒作通鉴原文。')
add('an_congjins_preparations','安从进截取湖南贡物，招人增兵，暗中谋划异动',7,'山南东道','增广甲卒；',[('安从进','截取贡物、招纳亡命者并扩充兵员')],year=None,when='940年三月拟调青州以前的持续动向，具体起止日期未载',description='《资治通鉴》记，安从进凭借险固地势，暗中谋划异动，擅自截取湖南贡物、招纳亡命者并扩充兵员。',note='谋划与扩军不等于已经公开起兵；未给定具体年份。')
add('an_kills_remonstrators','安从进杀死劝谏他的王令谦、潘知麟',7,'元随都押牙','皆杀之。',[('安从进','杀死两名劝谏者'),('王令谦','因劝谏被杀'),('潘知麟','因劝谏被杀')],year=None,when='940年三月拟调青州以前的追述，遇害具体年份未载')
add('shi_proposes_qingzhou','石敬瑭询问安从进是否愿调青州，安从进以讥讽回答拒绝',7,'及王建立',None,[('帝','派人征询安从进调任青州的意愿，未追究其答复'),('安从进','以搬青州到汉南的说法回应调任建议')],description='王建立调到潞州后，石敬瑭派人询问安从进是否愿意调任空出的青州，表示若愿意才下诏。安从进回答，若把青州搬到汉南，自己才赴任。皇帝没有追究。',note='只是征询意愿，没有已下诏或已赴任的证据；汉南沿史载名称，不补地理边界。')
add('yan_night_attack','王延政募千余敢死士，夜渡水放火袭击潘师逵营寨',8,'丁丑，','以应之，',[('延政','募集敢死士并发动夜袭'),('潘师逵','营寨遭渡水火攻')],when='940年三月丁丑',place='建州城外潘师逵营寨',description='王延政募集一千多名敢死士，夜间渡水潜入潘师逵营寨，借风纵火，建州城上的军队击鼓呐喊响应。')
add('chen_kills_pan','陈诲杀死潘师逵，潘师逵部众溃散',8,'战棹都头','其众皆溃。',[('陈诲','杀死潘师逵'),('潘师逵','在夜袭中被杀')],when='940年三月丁丑',place='潘师逵营寨',note='战棹都头、建安籍贯沿原文；明确死亡只用于潘师逵，部众溃散不等于全部死亡。')
add('wu_abandons_camp','王延政军尚未渡水，吴行真已弃营逃走，死者万人',8,'戊寅，','死者万人。',[('延政','准备进攻吴行真营寨'),('吴行真','在对方渡水以前率将士弃营逃走')],when='940年三月戊寅',place='吴行真营寨',description='王延政引兵准备进攻吴行真营寨，建州军还未渡水，吴行真及其将士已经弃营逃走。《资治通鉴》记死者万人，未说明具体死亡方式。',note='未渡水不能改写为已渡河攻破敌营；万人死亡不说成万人全部被斩，也不推吴行真本人死于此次逃跑。')
add('yan_takes_two_cities','王延政乘胜夺取永平、顺昌，建州军势增强',8,'延政乘胜',None,[('延政','乘胜夺取两城，其军队开始强盛')],place='永平、顺昌',description='王延政乘胜夺取永平、顺昌两城。《资治通鉴》认为，从此建州军队开始强盛。',note='自是是史书对局势变化的概述，不新增一天可定位的军队整编。')
sup('yan_takes_two_cities',8,minbook,'曦乃舉兵攻延政，為延政所敗。','《新五代史》也记王延羲派兵攻王延政，结果被击败。','补证整体战事，不将传记未分述的细节补成新的确切日战斗。')
add('zhao_proposes_three_finances','赵季良请求与毋昭裔、张业分管三司',9,'夏，四月，','分判三司，',[('赵季良','请求与另两位宰相分管财政三司'),('毋昭裔','被提出共同分管三司'),('张业','被提出共同分管三司')],note='请求与下一句实际命令分录；此处三司为财政事务，不当尚书六部整体重组。')
add('meng_assigns_three_finances','孟昶命赵季良管户部、毋昭裔管盐铁、张业管度支',9,'癸卯，',None,[('蜀主','命三位宰相分别主管财政事务'),('赵季良','主管户部事务'),('毋昭裔','主管盐铁事务'),('张业','主管度支事务')],when='940年四月癸卯',description='孟昶命赵季良主管户部事务、毋昭裔主管盐铁事务、张业主管度支事务。')
add('ma_anyuan','石敬瑭任马全节为安远节度使',10,'庚戌，',None,[('帝','任命马全节'),('马全节','由前横海节度使任安远节度使')],when='940年四月庚戌',place='安远')
sup('ma_anyuan',10,apr,'庚戌，以滄州節度使馬全節為安州節度使。','《旧五代史》也记四月庚戌将马全节从沧州调任安州。','通鉴用横海与安远军号，旧史用州名；主书前横海官衔与旧史现职措辞分别保留，不补未载任职间隙。')
for name in ['杨琏','潘师逵']:
 row=next(x for x in B['people'] if x['name']==name)
 if row['key'] not in reused:row['death_year']=940
 quote='卒于舟中' if name=='杨琏' else '陈诲杀师逵'
 claim('person',row['key'],'death_year',f'{name}在940年去世。',4 if name=='杨琏' else 8,quote,'年份据当前编年上下文，未补具体公历日期；复用人物原档案不改写。')
reviews={
1:'郑元弼等获释衔接此前出使被拘；王继鹏已死，不误作在位新派使。请死与实际释放分别录。',
2:'火攻、逃山与正月乙未交印请降分别录；师暠为彭士愁之子。主书三州官印与旧史五州求盟范围不同，未强合。',
3:'安彦威入朝庚戌与后续楚地安置各有时间范围；言论归当事人。彭士愁任刺史为奏请。铜柱尺寸沿原单位，马援后裔是自称，不建确定远祖关系。',
4:'杨琏祭谒归来、船中醉后死亡及追封分录；未诊断死因或补日。',
5:'持续背景与二月当前战事区分，前述未确年份保留为空。业翘不自动合并叶翘，杜汉崇与杜建崇保留差异；欲斩不写成已斩。王延政父亲由新史明确补证。',
6:'两次四万兵各为合计；吴越下令出兵不等于已抵达。林鼎反对原因未知。三月戊辰茶山三千兵败、千余首级不补将领死亡。',
7:'退休申请未准、辛未及癸酉军镇任命分录。李德珫与李德充按同次职务动作对应识别，字形待核；皇甫遇交接来自旧史。安从进筹备不是已起兵，杀谏者确年未载；青州只是拟议调任。',
8:'丁丑夜袭、陈诲杀潘师逵，戊寅吴行真未待对方渡水已弃营，万人死亡原因未载；永平顺昌归建州后军势增强属史书概述。',
9:'赵季良奏请与孟昶癸卯实际分管命令分别录，三位职责明列。',
10:'主书安远军号与旧史安州任命、四月庚戌对应；前横海与旧史现职措辞差异保留。'}
assert not (P/'publication.json').exists()
for n in range(1,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=940,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph=Q[11]['id'],next_volume=282,next_year=940,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第1—10段，原49—58行；正月至四月记载。全年35段，剩余25段待录。',source_issues_review='三州官印与五州求盟、杜汉崇与杜建崇、李德珫与李德充等异说或字形保留。李皋未自动合并李弘皋。后续称殷及吴越援军抵达不提前录入。电子本纸本与异文仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)],plain_language_review='首次检查展示字段、身份、时间、关系方向与引用；追述不强定年、请求与命令区分、欲杀不写成已杀、未渡水不写成已经攻破，史书与当事人评价注明归属；原文摘录保留底本字形。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
