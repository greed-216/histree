# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 942 paragraphs 27–33."""
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
specs=[(d.name,d,'d0f7599ab625e6aecad46626068a963056a59c78','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-942-may','xinwudaishi-009-942-succession','xinwudaishi-065-liu-yan-death','xinwudaishi-068-min-li-empress']:
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
main_sources = ['tongjian-283-942-may','tongjian-283-942-autumn-winter']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0942-p027-p033',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-942-autumn-winter':'卷283·天福七年八月至年末','jiuwudaishi-081-942-xiangzhou':'卷81·晋少帝本纪·天福七年八月','xinwudaishi-065-zhang-yuxian-battle':'卷65·南汉世家·钱帛馆之战','xinwudaishi-068-yu-tingying':'卷68·闽世家·余廷英'}
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
for n in range(27, 34):
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
    labels={'tongjian-283-942-autumn-winter':'卷283·天福七年八月至年末','jiuwudaishi-081-942-xiangzhou':'卷81·晋少帝本纪·天福七年八月','xinwudaishi-065-zhang-yuxian-battle':'卷65·南汉世家·钱帛馆之战','xinwudaishi-068-yu-tingying':'卷68·闽世家·余廷英'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '七月至八月条下及追述'
        citation = f'卷283·后晋天福七年（942；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0942_04_{len(B["claims"])+1:04d}'
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

ALIASES.update({'汉主':'刘弘度','弘昌':'刘弘昌','弘杲':'刘弘杲','陈道痒':'陈道庠','唐主':'李昪','曦':'王延羲','延政':'王延政','继柔':'王继柔','李后':'李氏（王延羲后）'})
NEW_DESCRIPTIONS={
'张遇贤':'博罗县吏。942年循州起事者拥立他为领袖，他称中天八国王、改元永乐并置官。南汉派刘弘昌、刘弘杲征讨，二人在钱帛馆被围，后由将领救出。生卒年未载。',
'陈道庠':'南汉指挥使，端州人。942年钱帛馆之战中救出被围的刘弘昌、刘弘杲。主书前处写陈道痒，同段籍贯句及新五代史写陈道庠，姓名据此校读，原文不改。',
'万景忻':'南汉将领。《新五代史》记942年与陈道庠在钱帛馆奋战，帮助刘弘昌、刘弘杲突围。生卒年未载。',
'王清':'后晋奉国军都虞候，曲周人。942年襄州久围未克时劝高行周加紧进攻，并与刘词率军先登。生卒年未载。',
'刘词':'后晋奉国都指挥使，元城人。942年与王清率军先登襄州。生卒年未载。',
'安宏赞':'安从进的儿子。《旧五代史》942年八月甲子所列高行周奏报称他在襄州被俘后处死。出生年未载；不与之前被俘的安弘义或九月记载的安弘受直接合并。',
'王继柔':'闽国人物。942年王延羲宴群臣时逼他饮酒，他私下减少酒量，被王延羲与一名客将一同杀死。《通鉴》称他为王延羲从子，《新五代史》列为儿子，亲属异说保留。',
'余廷英':'闽国同平章事，后任泉州刺史。史书记他假称奉诏为后宫选女子而掳人，事发后到福州请罪，又向王延羲及皇后送钱而获准回泉州，后来再次被召为相。生卒年未载。'}
NEW_ALIASES={'张遇贤':['張遇賢'],'陈道庠':['陳道庠','陈道痒'],'万景忻':['萬景忻'],'王清':[],'刘词':['劉詞'],'安宏赞':['安宏贊'],'王继柔':['王繼柔'],'余廷英':[]}
ann='jiuwudaishi-081-942-xiangzhou';new='xinwudaishi-065-zhang-yuxian-battle';minsrc='xinwudaishi-068-yu-tingying';family='xinwudaishi-068-min-li-empress';south='xinwudaishi-065-liu-yan-death';jin='xinwudaishi-009-942-succession'
def participant(code,name,n,quote,role,source):
 pk=person(name,n,role,quote,source=source);key='participation_zztj_283_0942_'+code+'_'+pk
 assert not any(x['key']==key for x in B['person_events'])
 B['person_events'].append(dict(key=key,person_key=pk,event_key=E[code],role=role,status='draft'))
 claim('person_event',key,'role',name+'：'+role+'。',n,quote,'此人物姓名和行动来自独立原文，不依据主书等字自行推名单。',source=source)
add('boluo_spirit_reports','博罗出现民家有神传言，居民前往占问，张遇贤恭敬奉事',27,'有神降','县吏张遇贤事之甚谨。',[('张遇贤','以县吏身份奉事传闻中的神')],year=None,when='张遇贤起事以前，具体年月未载',place='博罗',description='《资治通鉴》记博罗县民家出现能说话但不见形体的神的传闻，居民前往占问吉凶，县吏张遇贤恭敬奉事。',note='多验是史载民间占问描述，不声称神或预言已得到客观验证。')
add('zhang_yuxian_proclaimed','循州起事者共同拥立张遇贤，他称中天八国王、改元永乐并置官',27,'时循州盗贼群起，','置百官，',[('张遇贤','被拥立后称王、改元并置官')],when='942年七月条下，具体起事日期未载',place='循州',description='循州各股起事者未有统一领袖，共同祷告后，传称神让张遇贤作首领，于是拥立张遇贤。他称中天八国王，改元永乐，设置官员。',note='神言是记载中的传闻及拥立叙事，不当作客观神命；原文盗贼称谓保留，说明使用起事者。')
add('zhang_raids_coastal_places','张遇贤部众攻掠海滨地区，由诸将指示进退',27,'攻掠海隅。','诸将但告进退而已。',[('张遇贤','率部攻掠，军事进退由诸将指示')],when='942年起事后，具体日期未载',place='岭南海滨',note='无他方略为史书评价，不补军事能力测试或各城陷落日期。')
add('liu_orders_suppression','刘弘度命刘弘昌为都统、刘弘杲为副将，征讨张遇贤',27,'汉主以','为副以讨之，',[('汉主','安排两王征讨张遇贤'),('弘昌','任都统出征'),('弘杲','任副将出征')],when='942年张遇贤起事后，具体日期未载',place='南汉',note='汉主为已即位的刘弘度，不是四月去世的刘岩。')
add('two_princes_surrounded','南汉军在钱帛馆作战不利，刘弘昌、刘弘杲被围',27,'战于钱帛馆。','二王皆为贼所围；',[('弘昌','钱帛馆作战不利后被围'),('弘杲','与刘弘昌一同被围'),('张遇贤','所率部众围困南汉两王')],when='942年征讨张遇贤期间，具体日期未载',place='钱帛馆')
add('chen_rescues_two_princes','陈道庠等奋战，救出被围的刘弘昌、刘弘杲',27,'指挥使','得免。',[('陈道痒','奋战救出两王'),('弘昌','被救出并脱险'),('弘杲','被救出并脱险')],when='942年钱帛馆交战中，具体日期未载',place='钱帛馆',note='陈道痒与同段道庠及新史陈道庠对照校读，原文原字保留。')
sup('chen_rescues_two_princes',27,new,'裨將萬景忻、陳道庠力戰，挾二王潰圍而走。','《新五代史》补明万景忻与陈道庠一同奋战，带两王突围逃出。','陈道庠姓名有同书内句及新史支持，万景忻为补充参与者，不把不同书称谓另建同人。',relation='adds')
participant('chen_rescues_two_princes','万景忻',27,'裨將萬景忻、陳道庠力戰，挾二王潰圍而走。','与陈道庠奋战，带两王突围',new)
claim('person',people['陈道庠'],'biography','陈道庠是端州人。',27,'道庠，端州人也。','同段后句为姓名及籍贯校读依据，不自行换算籍贯坐标。')
add('zhang_captures_eastern_counties','张遇贤部众攻陷岭东多处州县',27,'东方州县', '多为遇贤所陷。',[('张遇贤','所率部众占据东方多处州县')],when='942年起事后，具体日期未载',place='岭东',note='州县未列完整名单，本批不提前录入十月循州陷落和刘传死亡。')
claim('person',person('高行周',28,'围攻襄州久未攻克',span(28,'高行周围','城中食尽，')),'biography','《资治通鉴》记高行周围攻襄州跨年未克，城中粮食耗尽。',28,span(28,'高行周围','城中食尽，'),'逾年保留跨年时序，不直接换算为超过十二个月或补具体围城起日。')
add('wang_qing_urges_assault','王清劝高行周加紧攻襄州，认为敌城已危、军民疲困',28,'奉国军都虞候','尚何俟乎！”',[('王清','劝高行周尽快逼攻'),('高行周','收到王清的进攻建议')],when='942年八月襄州被克以前，具体日期未载',place='襄州',note='城危师老民困为王清的判断，建议与随后先登行动分录。')
add('wang_liu_scale_wall','王清与刘词率军先登襄州城',28,'与奉国', '帅众先登。',[('王清','与刘词率军先登'),('刘词','与王清率军先登')],when='942年八月襄州被克时，具体日期未载',place='襄州',note='刘词为奉国都指挥使、元城人；两人籍贯分别保留，不因先登推只有二人攻城。')
add('xiangzhou_taken','高行周军攻克襄州',28,'八月，','拔之。',[('高行周','所率官军攻克襄州')],when='942年八月，具体日期主书未载',place='襄州')
sup('xiangzhou_taken',28,jin,'八月戊午，高行周克襄州。','《新五代史》补记八月戊午高行周攻克襄州。','主书只列八月；旧纪甲子是奏报列日，不能直接把奏报日当攻克日。',relation='adds')
add('an_congjin_self_immolates','安从进在襄州被攻克时举族自焚',28,'安从进',None,[('安从进','举族自焚而死')],when='942年八月襄州被克时，具体日期主书未载',place='襄州',note='举族为原文概括，旧纪另记儿子被俘处死，不擅填所有亲属死法名单。')
sup('an_congjin_self_immolates',28,ann,'是日，襄州行營都部署高行周奏，收復襄州，安從進自焚而死，','《旧五代史》在八月甲子列高行周奏报收复襄州、安从进自焚死亡。','甲子是列奏报日，原文未另明自焚确切日，不强定死亡为甲子。')
E['an_hongzan_captured_killed']=event('an_hongzan_captured_killed','安宏赞在襄州被俘后遭斩首',28,'生擒男宏贊斬之。',[('安宏赞','作为安从进之子被俘后斩首')],when='942年八月甲子所列高行周奏报，实际捕杀日未载',place='襄州',source=ann,note='依原文宏贊和父子称谓显示安宏赞；不与安弘义或之后弘受直接合并。')
relationship('安从进','安宏赞','父亲',28,'是日，襄州行營都部署高行周奏，收復襄州，安從進自焚而死，生擒男宏贊斬之。','男宏赞承接安从进之子，父亲方向明确；姓名异字保留。',source=ann)
add('zhao_ying_zhongshuling','石重贵任赵莹为中书令',29,'甲子，','为中书令。',[('石重贵','任赵莹为中书令'),('赵莹','获任中书令')],when='942年八月甲子')
sup('zhao_ying_zhongshuling',29,ann,'甲子，宰臣馮道加守太尉，趙瑩加中書令，','《旧五代史》同记八月甲子赵莹加中书令。','只补证本段赵莹任命，其他加官不越主线挑段录入。')
add('wang_yanxi_seeks_peace','王延羲派使者携诏与财物求和，王延政拒绝',29,'闽主曦','延政不受。',[('曦','派使者携手诏财物请求和解'),('延政','拒绝和解请求')],when='942年八月甲子条下，具体遣使日期未载',place='闽国',description='王延羲派使者带手诏、金器九百、钱一万缗以及将吏敕告六百四十通，向王延政求和。王延政拒绝。',note='各单位按原文保留，敕告为文书数，不当成六百四十名已受官将吏。')
add('wang_forces_jirou_to_drink','王延羲在九龙殿宴群臣，强迫王继柔饮酒',29,'丙寅，','强之。',[('曦','宴群臣并强迫王继柔喝酒'),('继柔','不能饮酒而被强迫')],when='942年八月丙寅',place='九龙殿',note='从子为主书亲属称谓，与新史诸子有异，暂不建唯一父子或伯叔关系。')
add('wang_kills_jirou','王继柔私下减少酒量，王延羲发怒，把他与客将一同杀死',29,'继柔私减',None,[('继柔','因私减饮酒量被杀'),('曦','因私减酒量发怒而杀王继柔和客将')],when='942年八月丙寅',place='九龙殿',note='客将未具名，不补其与王继柔亲属或帮倒酒的具体动作。')
sup('wang_kills_jirou',29,family,'諸子繼柔棄酒，并殺其贊者一人。','《新五代史》称王继柔为王延羲之子，记他弃酒，连同帮助者一人被杀。','儿子与主书从子不同，贊者与客将的称谓也不同，分别引用，不擅改唯一亲属身份。',relation='conflicts')
add('min_casts_yonglong_iron_coin','闽国铸永隆通宝大铁钱，一枚当铅钱一百枚',30,'闽人',None,[],when='942年八月条下，具体铸造日期未载',place='闽国',note='兑换比例按原文保留，不补发行量、购买力或金属含量。')
add('liu_yan_buried_kangling','南汉把刘岩葬于康陵，庙号高祖',31,'汉葬',None,[('刘岩','死后葬于康陵，庙号高祖')],when='942年八月条下，具体葬日未载',place='康陵',note='天皇大帝为死后尊称，此时南汉主为刘弘度，不把刘岩写成重新在世。')
sup('liu_yan_buried_kangling',31,south,'謚天皇大帝，廟號高祖，陵曰康陵。','《新五代史》也记刘龑谥天皇大帝，庙号高祖，陵名康陵。','传记概括死后名号和陵名，没有给八月具体葬日，不将传记死亡月一并当葬月。')
claim('person',person('唐主',32,'曾任吴相，改变旧法',span(32,'唐主自为','变更旧法甚多。')),'biography','《资治通鉴》称李昪任吴国宰相时推行许多旧法改革。',32,span(32,'唐主自为','变更旧法甚多。'),'兴利除害为史书评价，前朝长期概述不当942年同日单一改革。')
add('li_bian_orders_legal_code','李昪即位后命法官及尚书删定升元条三十卷',32,'及即位，','三十卷；',[('唐主','命法官及尚书整理法律条文')],year=None,when='李昪即位以后，942年颁行以前，具体年月未载',place='南唐',note='卷数三十与法律条数不同，法官尚书未名，不补编纂官名单。')
add('shengyuan_code_enacted','南唐颁行升元条',32,'庚寅，',None,[('唐主','颁行升元条')],when='942年八月庚寅',place='南唐',note='行之为颁行，与此前删定编纂分开。')
add('yu_appointed_quanzhou','王延羲任余廷英为泉州刺史',33,'闽主曦','为泉州刺史。',[('曦','任余廷英为泉州刺史'),('余廷英','由同平章事出任泉州刺史')],when='942年八月条下，具体日期未载',place='泉州',note='候官为原文籍贯字形，尚未据此改底本或补现代坐标。')
add('yu_abducts_women','余廷英掳走女子，假称奉诏为后宫挑选',33,'廷英贪秽，','以备后宫。',[('余廷英','掳走女子并假称奉诏选后宫')],year=None,when='余廷英任泉州刺史期间，具体年月未载',place='泉州',note='诈称受诏不是确有选后宫诏令；受害者未具名，不补人数。')
sup('yu_abducts_women',33,minsrc,'泉州刺史余廷英嘗矯曦命掠取良家子，','《新五代史》也记余廷英假托王延羲命令掳取良家女子。','嘗为过往行为，独立补证但不给具体年月。')
add('wang_orders_yu_inquiry','王延羲派御史调查余廷英掳人',33,'事觉，','御史按之。',[('曦','派御史调查'),('余廷英','掳人事发后遭调查')],year=None,when='余廷英掳人事发后，具体年月未载',place='闽国',note='御史未具名，不认作后面其他事件的刘赞。')
add('yu_reports_to_fuzhou','余廷英害怕，到福州自归，王延羲责问并准备交官处理',33,'廷英惧，','将以属吏；',[('余廷英','到福州自归'),('曦','责问并准备将余廷英交官处理')],year=None,when='掳人调查发生后，具体年月未载',place='福州',note='将以属吏是准备处理，不写成已经完成审判。')
add('yu_pays_banquet_money','余廷英献买宴钱一万缗，王延羲高兴',33,'廷英退，','曦悦，',[('余廷英','献买宴钱一万缗'),('曦','收到钱后高兴')],year=None,when='王延羲责问以后，具体年月未载',place='福州',note='买宴钱是史载名目，不擅改现代刑法定性；金额与新史写法分别保留。')
sup('yu_pays_banquet_money',33,minsrc,'廷英進買宴錢千萬，','《新五代史》记余廷英进买宴钱千万。','主书以万缗计，新史写钱千万，保持各自记数单位，不擅自换算或相加。',relation='adds')
add('wang_requests_empress_gift','王延羲次日召余廷英，询问给皇后的贡物',33,'明日召见，','皇后贡物安在？”',[('曦','次日召见并索问皇后贡物'),('余廷英','被问及给皇后的贡物')],year=None,when='余廷英献买宴钱的次日，具体年月未载',place='福州',note='原问话明确索问皇后贡物，未给本次要求的具体金额。')
add('yu_pays_empress_returns','余廷英再向李皇后献钱，随后获准回泉州',33,'廷英复献钱','乃遣归泉州；',[('余廷英','再献钱后获准回泉州'),('李后','收到余廷英的钱'),('曦','准许余廷英回泉州')],year=None,when='询问皇后贡物以后，具体年月未载',place='福州至泉州',note='同次李皇后复用王延羲妻主体，不与别朝皇后合并；主书未载第二次献钱金额。')
sup('yu_pays_empress_returns',33,minsrc,'廷英又獻皇后錢千萬，乃得不劾。','《新五代史》补记余廷英又献皇后钱千万，随后得免弹劾。','第二笔千万为新史补充，不将主书未给金额补成同一无争议数字。',relation='adds')
add('min_provinces_separate_empress_tribute','闽国各州此后另向皇后进贡',33,'自是诸州','别贡皇后物。',[],year=None,when='余廷英献皇后钱事件以后，起止年月未载',place='闽国',note='诸州为史书概述，不补州别金额或永续年限。')
add('yu_recalled_as_chancellor','王延羲不久又召余廷英为宰相',33,'未几，',None,[('曦','再次召余廷英为相'),('余廷英','不久又被召回任相')],year=None,when='余廷英获准回泉州不久后，确切年月未载',place='闽国',note='未几不换算固定天数，也不强定为八月同日。')
for name,n,q in [('安从进',28,'安从进举族自焚。'),('安宏赞',28,'生擒男宏贊斬之。'),('王继柔',29,'继柔私减其酒，曦怒，并客将斩之。')]:
 claim('person',people[name],'death_year',name+'于942年死亡。',n,q,'死亡动作明确，月日说明分别见对应事件，不擅补出生年。',source=ann if name=='安宏赞' else None)
for row in B['people']:
 if row['name'] in ['安宏赞','王继柔']:row['death_year']=942
reviews={27:'博罗神降及神命为传闻叙事，不确证超自然；拥立称王改元置官、攻掠、南汉两王征讨、钱帛馆被围和救出及岭东陷县分开。陈道痒据同段道庠及新史校读，万景忻仅据新史补参与；循州十月陷落及刺史死暂不提前。',28:'围城逾年为跨年背景，不换超过12个月；王清劝攻与王刘先登、八月克城和安自焚分期。新史戊午克与旧甲子奏报区别；旧男宏赞捕杀独立事件与父亲关系，不与弘义弘受直接合并，举族与被俘儿死法不强统一。',29:'八月甲子赵莹任官、闽求和财物文书及延政拒绝、丙寅逼酒杀继柔分开；主从子与新诸子关系异说保留，不建唯一父子或伯叔边。',30:'永隆铁钱与铅钱兑换比按原文，未补发行量或购买力。',31:'南汉刘岩葬康陵与庙号高祖，主八月条下无确日；新史仅名号陵名补证，不改四月死亡日。',32:'吴相改革概述与即位后删定三十卷为旧事，八月庚寅颁行单录；卷数不当法律条数。',33:'余泉州任命、假诏掳人、派查、福州自归责问、买宴钱、次日问皇后、再献钱归泉、各州别贡与未几再相分期；长期过往和未几确年不明为空。主万缗与新钱千万保各单位，不擅换；候官原字保留，纸本待核。'}
assert not (P/'publication.json').exists()
for n in range(27,34):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=283,year=942,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(27,34)],next_paragraph=Q[34]['id'],supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第27—33段，原32—38行；七月至八月及过往追述。后接十月张遇贤陷循州第34段，全年尚未完成。',source_issues_review='神降按传闻，陈道痒与道庠校读、襄州战日与奏日、继柔父侄异说、余献钱单位、候官字形保原。旧纪安宏赞与后续弘受不直接合并；电子底本纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(27,34)],plain_language_review='首次逐项检查人物身份、标题、参与角色、时间及亲属方向，现代白话与逐字摘录分开；传闻、提议、诏令和实际动作有别，追述及未几的未知年月保留。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
