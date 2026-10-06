# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 954 paragraphs 21–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,25))
COMMIT='cd645e3efcb32aa415b690b609c4d750baa3dbf6'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-954-summer-autumn']:
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
main_sources = ['tongjian-292-954-summer-autumn','tongjian-292-954-hunan-yearend']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0954-p021-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
for n in range(21, 25):
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
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷292·显德元年（954年年末及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0954_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_292_0954_' + code
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
        edge = 'participation_zztj_292_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'柴荣','北汉主':'刘崇（刘知远弟）','承钧':'刘承钧','契丹主':'耶律璟','刘承训':'刘承训（契丹册命使）','刘瑫':'刘瑫（楚蛮酋）'})
NEW_ALIASES={'刘承训（契丹册命使）':[],'苻彦通':[],'王虔朗':[]}
NEW_DESCRIPTIONS={'刘承训（契丹册命使）':'契丹骠骑大将军、知内侍省事。《通鉴》显德元年末记他奉契丹命册立刘承钧为北汉皇帝。与刘知远的同名儿子分开；生卒年未载，册命年另有史书异说。','苻彦通':'溆州地方部族首领。马希萼攻破长沙时掠得府库财物，后来在溪洞地区称王。王虔朗劝说后，他去王号、献铜鼓，获王逵承制任为黔中节度使。生卒年未载，自称苻秦后裔不当已证族谱。','王虔朗':'桂州人，王逵部将。《通鉴》954年末记其自请出使苻彦通，劝其去王号归附，获任都指挥使并参与府政。生卒年未载。'}
ld='liaoshi-6-liuchong-death-succession';lh='liaoshi-6-yingli5-heading';nd='xinwudaishi-70-liuchong-death';nz='xinwudaishi-66-zhou-xingfeng-954';oz='jiuwudaishi-114-zhou-xingfeng-september'
add('chengjun_regency','刘崇病重，命刘承钧监国',21,'北汉主疾病，','命其子承钧监国，',[('北汉主','病重时命儿子监国'),('承钧','受命监国')],when='954年末《通鉴》本条所记，具体日未载',place='晋阳',note='监国与后续受册为帝分开；此前委国事不是此次正式继位。')
add('liuchong_dies','《资治通鉴》记刘崇病逝',21,'北汉主疾病，','寻殂。',[('北汉主','病重后去世')],when='954年末《通鉴》本条；新五代史、辽史另记955年十一月',place='晋阳',description='《资治通鉴》在显德元年末记刘崇命儿子监国后不久去世。《新五代史》及《辽史》另有翌年十一月记法，死亡纪年存在差异。',note='寻表示此后不久，不计精确天数。索引按主书954年保留，异年并列待考。')
sup('liuchong_dies',21,nd,'旻自敗於高平，已而被圍，以憂得疾，明年十一月卒，年六十，子承鈞立。','《新五代史》说刘旻高平战败后忧病，明年十一月去世，享年六十，刘承钧继位。','高平之战在954年，此书明年指955年，与主书年条差异保留；享年不推精确生年。',relation='conflicts',field='time_original')
sup('liuchong_dies',21,ld,'十一月乙未朔，漢主崇殂，子承鈞遣使來告，且求嗣立。','《辽史》应历五年十一月条记刘崇去世，刘承钧遣使告哀并求嗣立。','应历五年为955年；乙未朔后接死亡和使行，不能把全部行动强定同日。',relation='conflicts',field='time_original')
sup('liuchong_dies',21,lh,'應歷五年','《辽史》死亡段落的年标题为应历五年。','卷六同第5节，年标题原1317行，死亡段原1329行。标题只校核纪年，不作为史事；应历元年951，五年955。',relation='conflicts',field='time_original')
claim('person',people['刘崇（刘知远弟）'],'death_year','《通鉴》把刘崇死亡列在954年条，新五代史与辽史另记955年，死亡年有异说。',21,span(21,'北汉主疾病，','寻殂。'),'只补各书记载的死亡事实，不覆盖既有death_year或抹去异年。')
add('report_liuchong_death','北汉向契丹派使报告刘崇去世',21,'遣使告哀','于契丹。',[('承钧','北汉向契丹派使告哀'),('契丹主','收到北汉死讯')],when='刘崇死亡之后；主书列954年末，另书纪年有异说',place='北汉至契丹',note='使者未具名，告哀日不当死亡日。')
add('khitan_confirms_chengjun','契丹派刘承训册命刘承钧为北汉皇帝',21,'契丹遣骠骑大将军、','册命承钧为帝，',[('契丹主','派册命使确认继位'),('刘承训','以契丹骠骑大将军、知内侍省事身份执行册命'),('承钧','获册命为帝')],when='刘崇死亡后，主书954年末条，册命年有异说',place='北汉晋阳',note='契丹使者不是刘知远同名儿子，册命是政治承认，不等于血缘认养。')
sup('khitan_confirms_chengjun',21,ld,'遣使吊祭，遂封冊之。','《辽史》应历五年条也记遣使吊祭、封册刘承钧。','另书记在955年，本句未具使者姓名；保留年份与细节差别。',relation='conflicts')
add('chengjun_becomes_jun','刘承钧改名刘钧',21,'更名钧。','更名钧。',[('承钧','改名为钧')],when='主书954年末受册记载后，具体日未载',place='北汉',note='保持同一主体稳定key，不因更名新建人物。')
claim('person',people['刘承钧'],'aliases','刘承钧受册后改名刘钧，繁体作劉鈞。',21,span(21,'契丹遣骠骑大将军、','更名钧。'),'同句明确承钧改名钧，字形转换仅用于别名检索。')
claim('person',people['刘承钧'],'evaluation','《通鉴》称刘承钧孝谨、勤政，爱民礼士，境内大体安定。',21,'北汉孝和帝性孝谨，既嗣位，勤于为政，爱民礼士，境内粗安。','这是继位后的评价，不把整个在位期结果限定为954年末。')
add('chengjun_khitan_protocol','刘承钧对契丹上表称儿子，契丹君主诏称他儿皇帝',21,'每上表于契丹主称男，',None,[('承钧','上表以男自称'),('契丹主','以儿皇帝称北汉君主')],year=None,when='刘承钧继位以后的外交称谓，具体起讫年未载',place='北汉与契丹',note='每上表是反复外交礼称，不是某日血缘认养。')
relationship('耶律璟','刘承钧','政治父亲',21,span(21,'每上表于契丹主称男，'),'父子外交称谓只建政治关系，不替代刘崇血缘父亲关系。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='刘承钧继位后，耶律璟在两国文书的父子礼称中居政治父亲地位；这是政治关系，原文未记两人有血缘。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('fu_loots_changsha','马希萼攻破长沙时，苻彦通掠走府库积蓄',22,'马希萼之帅群蛮破长沙也，','皆为溆州蛮酋苻彦通所掠，',[('马希萼','攻破长沙时发生掠库'),('苻彦通','掠得府库积蓄')],year=950,when='950年马希萼攻破长沙时的回述，具体日此段未载',place='长沙',note='回查已录950年末楚内战背景，只补具名掠库者，不重建长沙城陷或放在954年。')
add('fu_claims_kingship','苻彦通凭掠得财富壮大，在溪洞地区称王',22,'彦通由是富强，','称王于溪洞间。',[('苻彦通','在溪洞地区称王')],year=None,when='950年长沙城破以后、王虔朗出使以前，具体年未载',place='溪洞地区',note='自称王不等于朝廷已封王。')
add('wangkui_seeks_envoy','王逵掌握湖南后，希望派使安抚苻彦通并招募人选',22,'王逵既得湖南，','募能往者，',[('王逵','计划派使并招募人选')],when='954年末条所载，具体月日未载',place='湖南')
add('qianlang_volunteers','王虔朗自请出使苻彦通',22,'其将王虔朗请行。','其将王虔朗请行。',[('王虔朗','自请出使'),('王逵','收到部将请行')],when='954年末条所载使行前',place='湖南')
relationship('王虔朗','王逵','部将',22,'其将王虔朗请行。','原文明称其将，王虔朗是王逵的部将，限定此湖南使行时段。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='954年记述的湖南使行时，王虔朗是王逵的部将。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('qianlang_meets_fu','王虔朗到苻彦通处，苻彦通列众多侍卫接见，态度倨傲',22,'既至，','礼貌甚倨。',[('王虔朗','出使会见苻彦通'),('苻彦通','列侍卫接见使者')],when='954年末条所载会见时',place='苻彦通驻地，具体地点未载',note='态度是史书描述，未造侍卫人数。')
add('qianlang_rebukes_fu','王虔朗斥责苻彦通未求盟且轻慢使者，提及其自称苻秦后裔',22,'虔朗厉声责之曰：','异日得无悔乎！”',[('王虔朗','斥责苻彦通接待与政治态度'),('苻彦通','受到斥责')],when='954年末条所载会见时',place='苻彦通驻地',note='苻秦血统只是自称，不能建已证族谱；苒裔疑为苗裔，引用不改字，解释用后裔。先祖事马氏也保留为使者话语。')
add('fu_apologizes','苻彦通惭惧，握王虔朗的手致歉',22,'彦通惭惧，','执虔朗手谢之。',[('苻彦通','向使者致歉'),('王虔朗','得到致歉')],when='954年末条所载会见时',place='苻彦通驻地')
add('qianlang_proposes_submission','王虔朗劝苻彦通去王号归王逵，提出可获节度使任命',22,'虔朗知其可动，','岂不尊荣哉！”',[('王虔朗','劝去王号归附'),('苻彦通','听取劝说')],when='954年末条所载劝说时',place='苻彦通驻地',note='隋唐州县与官号尊荣为使者论证，不逐一确认为已核地图边界或实授官职。')
add('fu_abandons_kingship','苻彦通听从劝说，当日去除王号',22,'彦通大喜，','即日去王号，',[('苻彦通','去掉王号')],when='劝说当日，主书列954年末，未具月日',place='溪洞地区')
add('fu_presents_drums','苻彦通经王虔朗向王逵献铜鼓数枚',22,'因虔朗','献铜鼓数枚于王逵。',[('苻彦通','献铜鼓'),('王虔朗','转献铜鼓'),('王逵','接受铜鼓')],when='954年末条所载去王号后',place='溪洞地区至王逵军府',note='数枚不造确数，不补器物年代。')
add('wangkui_praises_qianlang','王逵赞王虔朗一言胜数万兵，称为国士',22,'逵曰：','真国士也！”',[('王逵','赞赏使行成果'),('王虔朗','获王逵赞赏')],when='954年末条所载使行后',place='王逵军府',note='数万兵是赞语，不是实际兵力节省统计。')
add('fu_appointed_qianzhong','王逵承制任苻彦通为黔中节度使',22,'承制以彦通','为黔中节度使，',[('王逵','承制授官'),('苻彦通','获任黔中节度使')],when='954年末条所载使行后',place='黔中',note='保持承制任命，不另造后周皇帝同日册任诏令。')
add('qianlang_promoted','王逵任王虔朗为都指挥使，准其参与府政',22,'以虔朗','预闻府政。',[('王逵','任王虔朗参与府政'),('王虔朗','获任都指挥使并参与府政')],when='954年末条所载使行后',place='王逵军府')
claim('person',people['王虔朗'],'description','王虔朗是桂州人。',22,'虔朗，桂州人也。','史载籍贯，不补现代出生地址。')
add('wangkui_recommends_liutao','王逵担忧西界边患，上表荐刘瑫为镇南节度副使兼西界都招讨使',23,Q[23]['text'],None,[('王逵','上表荐任刘瑫以安西界'),('刘瑫','被荐为镇南节度副使兼西界都招讨使')],when='954年末条所载，具体月日未载',place='锦州及西界',note='表为是上表推荐，不等于已获朝廷批准；边患是王逵担忧，不写成刘瑫已反。')
add('hunan_famine','湖南饥荒，百姓采食草木果实',24,'是岁，','民食草木实。',[],when='954年全年概述，具体月份未载',place='湖南',note='草木实是植物果实，不替换为树皮，不造饥民和死亡精确人数。')
add('zhou_grain_relief','周行逢开仓赈济湖南饥民，救活很多人',24,'武清节度使、','全活甚众。',[('周行逢','以知潭州事身份开仓赈灾')],when='954年湖南饥荒期间，具体月日未载',place='潭州、湖南',note='甚众不补人数或赈粮量。')
sup('zhou_grain_relief',24,nz,'顯德元年，拜行逢武清軍節度使，權知潭州軍府事。','《新五代史》记显德元年周行逢任武清军节度使、权知潭州军府事。','只补当时身份，不直接印证赈灾细节；后文潘叔嗣杀王逵属未来段落，不提前录入。',relation='adds')
sup('zhou_grain_relief',24,oz,'甲戌，以武安軍節度副使、知潭州軍府事周行逢為鄂州節度使，知潭州軍府事，加檢校太尉。','《旧五代史》记九月甲戌周行逢任鄂州节度使，仍知潭州事，加检校太尉。','保存职务称谓，不把赈灾日期强定为九月甲戌任命日。',relation='adds')
claim('person',people['周行逢'],'evaluation','《通鉴》称周行逢了解民间疾苦，认真治政、严格无私，选廉正僚属，规章简明，吏民觉得方便。',24,span(24,'行逢起于微贱，','吏民便之，'),'是施政概述，未造每次选任日期及未具名僚属。')
claim('person',people['周行逢'],'evaluation','《通鉴》称周行逢自奉节俭。',24,'其自奉甚薄；','保留作者评价，不补具体俸禄。')
add('zhou_defends_frugality','周行逢以马氏奢侈后衰败回应过俭的批评',24,'或讥其太俭，',None,[('周行逢','说明不愿效法马氏奢侈')],year=None,when='周行逢治潭州时期的概述，具体发言年未载',place='潭州',note='马氏子孙乞食是周行逢说法，不给全部后裔新建954年乞食事件。')
reviews={21:'死亡年主书954与新史、辽史955并列待考；辽史应历五年标题独立回查，死讯与告哀不强定同日。刘承训分同名，政治父子不作血亲，更名仍用同一主体。',22:'掠库为950年旧事，后续称王年未定。使行、去王号、赠铜鼓、授官分录，苻秦世系是自称，苒裔原字保留，赞语不当战果。',23:'担忧与荐任分别说明，不造刘瑫已反或朝廷批准。',24:'全年饥荒与赈灾分开，副书只补任职，不当印证赈粮数；施政评价与未具年的言辞保留来源。'}
assert not (P/'publication.json').exists()
for n in range(21,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(21,25)],next_paragraph='zztj-v292-y0955-p001',next_volume=292,next_year=955,supplements=supplements,excluded_non_body=[],coverage='原26—29行最后四段正文；原30行帝号题名为结构项，之后为955年。快照内的955年段落尚未处理。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,25)],source_issues_review='刘崇死亡年通鉴954与新五代史、辽史955并列待考，辽应历五年已核年标题。契丹刘承训与后汉皇子分开，苻秦世系不证，苒裔疑字保留。纸本待核。',plain_language_review='首次逐条检查标题、人物、角色、时间、关系及事实说明。外交父子非血亲，自称非已证世系，上表不当批准，未知日期和匿名人物不伪造。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
