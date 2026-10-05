# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 30–35."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='576d9a100a90791fb2103eff8dc0a2a9ed251986'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['jiuwudaishi-099-947-envoy']:
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
main_sources = ['tongjian-286-947-accession']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p030-p035',
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
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
    for a,b in [('主書','《资治通鉴》'),('補','补'),('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        citation = f'卷286·天福十二年（947年二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_07_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'蜀主':'孟昶','李继勋':'李继勋（后蜀将领）','刘景':'刘景（后蜀兴州刺史）','赵晖':'赵晖（后汉将领）','刘愿':'刘愿（947年契丹将）'})
NEW_ALIASES={'刘景（后蜀兴州刺史）':['劉景（後蜀興州刺史）'],'史弘肇':['史宏肇'],'张彦威':['張彥威'],'杨邠':['楊邠'],'刘愿（947年契丹将）':['劉願（947年契丹將）','劉愿（947年契丹將）'],'王晏':[],'赵晖（后汉将领）':['趙暉（後漢將領）'],'侯章':[]}
NEW_DESCRIPTIONS={
'刘景（后蜀兴州刺史）':'后蜀兴州刺史，947年二月与李继勋攻取固镇。生卒年未载；不与刘景岩等姓名相近的人物合并。',
'史弘肇':'荥泽人，947年二月任刘知远的武节都指挥使，奉命在球场集合各军，宣布出兵日期。《旧五代史》亦有史宏肇的字形。生卒年暂未录入。',
'张彦威':'潞城人，947年二月任河东行军司马，与其他将吏多次上书劝刘知远称帝。生卒年未载。',
'杨邠':'冠氏人，947年二月任河东都押牙，与郭威共同劝刘知远接受称帝建议。生卒年暂未录入。',
'刘愿（947年契丹将）':'契丹将领，被任命为保义节度副使。947年二月庚午，王晏等在陕州杀死他。《宋史》姓名写作劉愿，保留不同底本字形，不与其他同名作者合并。生年未载。',
'王晏':'徐州人，947年二月任奉国都头，与赵晖、侯章谋划杀死契丹将刘愿，率数名壮士夜入府署、取库中兵器。生卒年暂未录入。',
'赵晖（后汉将领）':'澶州人，947年二月在陕州与王晏、侯章谋划反抗契丹，刘愿被杀后获推为留后。与887年被部下杀死的上元赵晖不是同一人。生卒年暂未录入。',
'侯章':'太原人，947年二月任都头，在陕州与王晏、赵晖共同谋划反抗契丹。生卒年暂未录入。'}
j='jiuwudaishi-099-947-envoy';ji='jiuwudaishi-099-imperial-title';nw='xinwudaishi-010-accession';ss='songshi-252-wang-yan-revolt'
add('shu_takes_guzhen','李继勋、兴州刺史刘景攻取固镇',30,'壬戌，','拔之。',[('李继勋','与刘景共同攻取固镇'),('刘景','以兴州刺史身份攻取固镇')],when='947年二月壬戌',place='固镇',note='李继勋复用已限定为后蜀将领的主体；刘景不与刘景岩合并。原文只记攻取，未载伤亡人数。')
add('he_requests_shu_troops_for_fengzhou','何重建请求蜀军与阶州、成州兵共同扼守散关，以夺取凤州',30,'乙丑，','以取凤州，',[('何重建','请求联合出兵控制散关、攻取凤州')],when='947年二月乙丑',place='阶州、成州、散关至凤州（作战计划）',note='这是请求和作战目标，不能据此写为已经占领凤州。')
add('meng_sends_shannan_troops','孟昶派山南兵三千七百人响应何重建的请求',30,'丙寅，',None,[('蜀主','派出山南兵三千七百人'),('何重建','获得出兵响应')],when='947年二月丙寅',place='山南至散关方向',note='三千七百是本次派兵数，不推算后蜀总兵力，也不提前写凤州战果。')
add('liu_regrets_he_defection','刘知远听说何重建归蜀，感叹中原无主、藩镇外附，责怪自己未尽责任',31,'刘知远闻','良可愧也！”',[('刘知远','对何重建归蜀作出感叹')],when='947年二月丁卯前，具体日未载',place='河东',note='感叹是刘知远的说法，不将其自责转成已证实的失职结论。何重建归蜀本身已在前批录入。')
add('officers_urge_liu_first_refusal','河东将佐劝刘知远称帝以号令四方，刘知远拒绝',31,'于是将佐','知远不许。',[('刘知远','拒绝将佐的称帝建议')],when='947年二月丁卯前，具体日未载',place='河东',note='此处未列将佐姓名，不把后文劝进者自动全部列入本次参与者。')
add('liu_announces_rescue_plan','刘知远听说石重贵北迁，声称要从井陉出兵迎他回晋阳',31,'闻晋主','迎归晋阳。',[('刘知远','声称出兵迎回石重贵'),('石重贵','成为所称迎回行动的对象')],when='947年二月丁卯前，具体日未载',place='井陉至晋阳（所称路线）',note='声言是对外宣布的计划，不表示已经迎回石重贵。实际出行另在后续段落记录。')
add('shi_hongzhao_musters_armies','刘知远命史弘肇在球场集合各军，宣布出兵日期',31,'丁卯，','出师之期。',[('刘知远','下令集合各军'),('史弘肇','以武节都指挥使身份集合各军并宣布日期')],when='947年二月丁卯',place='河东球场',note='原文未载所宣布的出兵日期，不补具体日，也不据此断言军队已经出发。')
add('soldiers_urge_accession_liu_suppresses','军士要求刘知远先称帝再出兵，刘知远以契丹仍强为由制止呼喊',31,'军士皆曰：',None,[('刘知远','拒绝军士的称帝要求，命身边人制止呼喊')],when='947年二月丁卯',place='河东球场',note='军士的万岁呼声不是即位仪式；契丹仍强、军威未振是刘知远的理由。军士及左右没有姓名，不虚造参与者。')
add('zhang_yanwei_three_petitions','张彦威等三次上书劝刘知远称帝，刘知远仍犹豫',32,'己巳，','知远疑未决。',[('张彦威','以行军司马身份与将吏三次上书劝进'),('刘知远','对劝进仍未作决定')],when='947年二月己巳条下；三次上书各日未全部载明',place='河东',note='己巳是本段记事日，不把三次上书都硬定为同一天。')
sup('zhang_yanwei_three_petitions',32,j,'戊辰，河東行軍司馬張彥威與文武將吏等，以中原無主，帝威望日隆，群情所屬，上箋勸進，帝謙讓不允。自是群官三上箋','《旧五代史》从二月戊辰起记张彦威等上书，随后群官三次劝进。','《资治通鉴》己巳条记三次劝进与犹豫，《旧五代史》从戊辰记起，两书记日及叙述范围分别保存。',relation='adds',field='time_original')
sup('zhang_yanwei_three_petitions',32,nw,'二月戊辰，河東行軍司馬張彥威等上牋勸進。','《新五代史》也在二月戊辰记张彦威等上书劝进。','本条只给上书劝进起始日，不据此改写《通鉴》三次上书的记事日。',relation='adds',field='time_original')
add('guo_yang_persuade_liu','郭威、杨邠劝刘知远及时接受拥戴，刘知远同意称帝',32,'郭威与',None,[('郭威','与杨邠共同劝刘知远接受称帝建议'),('杨邠','以都押牙身份劝刘知远把握时机'),('刘知远','接受称帝建议')],when='947年二月己巳',place='河东',note='天意、人心可能转移是郭威和杨邠的劝说理由，不视为客观预言。刘知远同意劝进与辛未实际即位分别记录。')
add('khitan_appoints_liu_yuan','契丹任刘愿为保义节度副使，史书记陕州人苦于他的暴虐',33,'契丹以','苦其暴虐。',[('刘愿','被任命为保义节度副使')],when='947年二月庚午之前，具体日未载',place='陕州',note='任命未标日期，暴虐及百姓受苦为史书概述。刘愿按时代和职务限定，不与同名作者合并。')
add('wang_zhao_hou_plan_revolt','王晏、赵晖、侯章谋划杀刘愿、将陕州归附刘知远',33,'奉国都头','晖等然之。',[('王晏','提出杀刘愿、归附河东的计划'),('赵晖','赞同王晏的计划'),('侯章','参与谋议并赞同计划')],when='947年二月庚午前，具体日未载',place='陕州',note='刘知远威德远著、归附后易得富贵是王晏的说法，不能直接当作客观评价。赵晖与887年已死的上元同名人物分开。')
add('wang_enters_armory_at_night','王晏带数名壮士夜间越过牙城，进入府署取兵器分给众人',33,'晏与壮士','以给众。',[('王晏','率数名壮士夜入府署并分发库中兵器')],when='947年二月庚午前夜',place='陕州牙城与府署',note='壮士数人未给准确人数；不补姓名或推算部队规模。')
sup('wang_enters_armory_at_night',33,ss,'晏乃率敢死士數人夜踰城，入府署，劫庫兵給其徒，','《宋史》王晏传也记他率数人夜间越城入府署、取库兵。','此为王晏传的独立出处；《旧五代史》电子本也转引此传，不能把转引再计作另一份独立确证。')
add('wang_revolt_kills_liu_yuan','陕州反抗军杀死刘愿及契丹监军，将刘愿首级悬在府门',33,'庚午旦，','契丹监军，',[('王晏','参与杀刘愿的陕州反抗行动'),('赵晖','参与陕州反抗行动'),('侯章','参与陕州反抗行动'),('刘愿','被杀，首级悬于府门')],when='947年二月庚午清晨',place='陕州府门',note='《旧五代史》记赵晖、侯章、王晏参与杀监军与刘愿；《通鉴》本句没有点名行刑人，不指定谁亲手斩首。监军未名，不建立猜测身份。')
sup('wang_revolt_kills_liu_yuan',33,j,'庚午，陜府屯駐奉國指揮使趙暉、侯章、都頭王晏殺契丹監軍及副使劉願','《旧五代史》也在庚午记赵晖、侯章、王晏杀契丹监军及刘愿。','对应《通鉴》的庚午清晨；各书记官职称谓不同，分别保留，不改写为所有人均担任同一军职。')
sup('wang_revolt_kills_liu_yuan',33,ss,'遲明，斬愿首級府門外。','《宋史》王晏传也记天明前后斩刘愿首级于府门外。','原字愿与《通鉴》愿、《旧五代史》願属于不同底本字形；按相同事件识别同一人，引用保持原字。')
add('zhao_hui_chosen_liuhou','陕州反抗军推赵晖为留后',33,'奉晖','留后。',[('赵晖','获推为陕州留后')],when='947年二月庚午',place='陕州',note='留后是此时的推举结果，不提前写刘知远后来授予的节度使。王晏、赵晖、侯章籍贯分别为徐州、澶州、太原，依据段末记载。')
sup('zhao_hui_chosen_liuhou',33,j,'暉自稱留後','《旧五代史》记赵晖自称留后。','《通鉴》记奉为留后，《旧五代史》写自称，《宋史》记众请为帅，分别保留表述差异。',relation='adds')
# A supplemental action in the same revolt; its exact date is not established.
E['rebels_reject_khitan_commissions']=event('rebels_reject_khitan_commissions','契丹授赵晖、侯章、王晏军职，三人不接受',33,'契丹因授暉陜州兵馬留後，侯章為本州馬步軍都指揮使，王晏為副都指揮使，暉等不受命。',[('赵晖','拒绝契丹授陕州兵马留后'),('侯章','拒绝契丹授本州马步军都指挥使'),('王晏','拒绝契丹授副都指挥使')],when='947年二月陕州反抗后，具体日未载',place='陕州',source=j,note='此行动由《旧五代史》补充，契丹授职不表示三人已经接受。补书在同一主书段落下单独建事，不改变后续通鉴游标。')
add('liu_zhiyuan_accession','刘知远在太原即皇帝位',34,'辛未，','即皇帝位。',[('刘知远','正式即皇帝位')],when='947年二月辛未',place='太原',note='即位日依《通鉴》辛未，《旧五代史》补证太原宫受册。《新五代史》记此时尚未定汉国号，不提前将六月国号决定写入本日。')
sup('liu_zhiyuan_accession',34,ji,'辛未，帝於太原宮受冊，即皇帝位','《旧五代史》记辛未在太原宫受册即位。','本纪传主为刘知远，不将帝误认作石重贵。')
sup('liu_zhiyuan_accession',34,nw,'辛未，皇帝即位，稱天福十二年。','《新五代史》同记辛未即位、称天福十二年。','此条与主书即位日相符；六月国号改汉在后续编年中处理。')
add('liu_resumes_tianfu_era','刘知远不沿用开运纪年，改称天福十二年',34,'自言','天福十二年。',[('刘知远','改称天福十二年')],when='947年二月辛未',place='太原',note='不忍改晋国、厌恶开运之名是刘知远自述理由，不据此补出对石重贵的实际政治承诺。')
sup('liu_resumes_tianfu_era',34,ji,'制改晉開運四年為天福十二年。','《旧五代史》明确记把开运四年改为天福十二年。','保留原纪年，不自行换算公历月日。')
add('liu_stops_khitan_levies','刘知远下诏停止各地替契丹征钱征帛',34,'壬申，','皆罢之。',[('刘知远','命各地停止替契丹征钱征帛')],when='947年二月壬申',place='诏令所指各道',note='这是诏令内容，不断言所有地区已执行，也不推免除所有其他赋税。')
add('liu_exempts_coerced_jin_envoys','刘知远不追究被契丹胁迫出使的晋臣，命他们到行在',34,'其晋臣','令诣行在。',[('刘知远','免究被迫出使的晋臣，命其到行在')],when='947年二月壬申',place='各道至刘知远行在',note='免究对象限定为被迫出使的晋臣，不能扩成所有投降者；没有姓名，不自动关联全部晋臣。')
add('liu_orders_other_khitan_killed','刘知远下令各地杀死其余契丹人员',34,'自馀契丹，',None,[('刘知远','命各地诛杀其余契丹人员')],when='947年二月壬申',place='诏令所指各地',note='这是诏令中的命令，不据此推算实际被杀人数，也不把未载的具体杀戮写成已发生。')
add('cui_attacks_fengzhou_retreats','何重建派崔延琛攻凤州未克，崔延琛退守固镇',35,'何重建',None,[('何重建','派宫苑使崔延琛攻凤州'),('崔延琛','攻凤州失败后退守固镇')],when='947年二月辛未、壬申条之后，具体日未载',place='凤州至固镇',note='崔延琛沿用此前926年入蜀的同名中使记录，宫苑使官职与后蜀活动相接，长期仕历仍可补证。攻击未成功，不录凤州已经被占领。')
for who,place in [('王晏','徐州'),('赵晖（后汉将领）','澶州'),('侯章','太原')]:
 claim('person',people[who],'description',f'{who}是{place}人。',33,span(33,'晏，徐州；'), '籍贯按《资治通鉴》段末明确记载；保留历史地名，不自行换算现代行政区或坐标。')
reviews={30:'区分固镇已取、散关与凤州作战请求、实际派兵；刘景限定后蜀兴州刺史，李继勋复用后蜀将领。',31:'分清自责、将佐建议、迎回石重贵的声称计划、球场集军与军士劝进；不把计划写作已经出兵或称帝。',32:'己巳条记三次上书，旧、新五代史从戊辰记劝进；保留记日及叙述范围区别，郭威杨邠进说与正式即位分记。',33:'陕州计划、夜入取兵、杀刘愿监军、推留后及拒契丹授职分记；赵晖不同于887年已死者，刘愿不是同名作者。宋史补证不将旧史转引当另一份独立证据。',34:'即位、改称天福十二年与壬申三项诏令分记；不提前确定六月汉国号，诏令不等各地已经执行。',35:'凤州未克、退守固镇，不预写取城；崔延琛暂沿此前入蜀中使主体，长期仕历保留待补。'}
assert not (P/'publication.json').exists()
for n in range(30,36):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(30,36)],next_paragraph=Q[36]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原35—40行连续六段，累计35/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(30,36)],source_issues_review='劝进日期分别保留；赵晖与晚唐同名死者分开，史弘肇宏肇字形同人，刘景按后蜀职务限定；即位和汉国号决定不混用。',plain_language_review='首次核对全部展示字段的主语、动作、时间、参与角色及对应事实引用，分别表示计划、请求、诏令与实际结果。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
