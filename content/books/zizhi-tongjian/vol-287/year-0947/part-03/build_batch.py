# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,76))
COMMIT='727493791cbf73933108431c692275b3b8c9af2b'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-jinzhou-north-return','jiuwudaishi-100-may-march','jiuwudaishi-051-li-congyi']:
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
main_sources = ['tongjian-287-947-jinzhou-north-return']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p017-p024',
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
lines = (ROOT / 'resources/derived/tongjian/287.txt').read_text().splitlines()
for n in range(17, 25):
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
        citation = f'卷287·天福十二年（947年五月至六月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_03_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_287_0947_' + code
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
        edge = 'participation_zztj_287_0947_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_287_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','麻荅':'麻答','砺':'张砺','弘佐':'钱弘佐','弘倧':'钱弘倧','淑妃':'王淑妃','从益':'李从益'})
NEW_ALIASES={'李从朗':['李從朗'],'成霸卿':[],'薛琼':['薛瓊'],'郭从义':['郭從義'],'魏仁浦':['魏仁溥']}
NEW_DESCRIPTIONS={
'李从朗':'947年担任绛州刺史，起初与契丹将成霸卿等拒绝归附刘知远，五月戊申举城投降。生卒年未载。',
'成霸卿':'契丹将领。947年被派驻绛州，与刺史李从朗等拒绝归附刘知远，后绛州归降。生卒年未载。',
'薛琼':'947年以偏将身份，在绛州归降后获任防御使。生卒年未载。',
'郭从义':'947年任郑州防御使。六月刘知远令他先入大梁清理宫禁，并秘密命令他杀李从益与王淑妃。生卒年尚未录入。',
'魏仁浦':'字道济，卫州汲人。后晋末任枢密院小吏，随众被迁往契丹后逃归。947年在巩县迎见刘知远，因熟知军队人数与旧制受到郭威信任。生卒年尚未录入。'}
j='jiuwudaishi-100-may-march';june='jiuwudaishi-100-june-arrivals';li='jiuwudaishi-051-li-congyi';liao='liaoshi-076-zhang-li';zuo='xinwudaishi-067-qian-zuo-death';zong='xinwudaishi-067-qian-zong-succession';wei='songshi-249-wei-renpu-return';troops='songshi-249-wei-renpu-troops'
add('jiangzhou_resists_liu','李从朗、成霸卿等拒绝归附，白文珂攻绛州未克',17,'帝之即位也，','未下。',[('李从朗','以绛州刺史身份拒绝归附刘知远'),('成霸卿','与李从朗等守城拒命'),('帝','派白文珂进攻绛州'),('白文珂','以西南面招讨使、护国节度使身份进攻，尚未攻克')],when='947年刘知远即位后、五月戊申之前，具体攻城日未载',place='绛州',note='即位时拒命为回顾，此前攻城与后续刘知远亲至、戊申降城分开。')
sup('jiangzhou_resists_liu',17,j,'初，契丹遣偏校成霸卿、曹可璠等守其郡，帝建義之始，不時歸命','《旧五代史》也记契丹派成霸卿等守绛州，刘知远起兵后未及时归附。','补书记另名曹可璠，但本段主书未列其具体行动，暂保留在出处说明，不扩展未核身份。',relation='adds')
add('liu_orders_jiangzhou_surround','刘知远命军队围而不攻，向绛州守军说明利害',17,'帝至城下，','以利害谕之。',[('帝','到绛州城下，命部队分布围城，禁止攻打并劝降')],when='947年五月戊申归降之前，具体日未载',place='绛州城下')
add('li_conglang_surrenders','李从朗举绛州投降',17,'戊申，','从朗举城降。',[('李从朗','举城归降刘知远')],when='947年五月戊申',place='绛州')
sup('li_conglang_surrenders',17,j,'戊申，車駕至絳州，本州刺史李從朗以郡降','《旧五代史》同记五月戊申刘知远至绛州、李从朗以郡投降。','两书归降纪日一致，补书把至城置戊申，不将此前所有攻城行动也定为该日。')
add('liu_guards_jiangzhou_gates','刘知远派亲将守绛州城门，禁止士卒入城',17,'帝命亲将','士卒一人毋得入。',[('帝','派亲将分守城门，禁止士卒入城')],when='947年五月戊申归降后',place='绛州诸城门',note='记禁止入城的军令，不无证外推为全程没有任何侵扰。')
add('xue_qiong_jiangzhou_defense','薛琼获任绛州防御使',17,'以偏将',None,[('薛琼','由偏将获任防御使')],when='947年五月戊申归降后，具体任命日未另载',place='绛州')
add('liu_arrives_shanzhou','刘知远到陕州，赵晖亲自为他驾马入城',18,'辛亥，','赵晖自御帝马而入。',[('帝','到达陕州'),('赵晖','亲自为刘知远驾马入城')],when='947年五月辛亥',place='陕州',note='自御帝马按亲自驾御记，不将赵晖推为固定御马官。')
add('liu_arrives_shihao','刘知远到石壕，汴州有人前来迎接',18,'壬子，','汴人有来迎者。',[('帝','到石壕，受到汴州来人的迎接')],when='947年五月壬子',place='石壕',note='有来迎者未具名，不能写成全体汴州居民或百官都已迎接。')
add('xiao_mada_surrounds_zhang','萧翰到恒州，与麻答率铁骑包围张砺住宅',18,'六月，甲寅朔，','砺方卧病，出见之，',[('萧翰','到恒州，与麻答包围张砺住宅'),('麻荅','与萧翰率骑兵围张砺住宅'),('砺','患病卧床，起身见萧翰等')],when='947年六月甲寅朔',place='恒州，张砺住宅')
sup('xiao_mada_surrounds_zhang',18,liao,'時礪在恒州，蕭翰與麻答以兵圍其第。礪方臥病，出見之。','《辽史》张砺传也记萧翰与麻答围其宅、张砺卧病出见。','补书未给围宅干支日，不据此独立确认甲寅。')
add('xiao_accuses_shackles_zhang','萧翰指责张砺反对其任职及入宫，威胁杀他并命人拘锁',18,'翰数之曰：','命锁之。',[('萧翰','历数对张砺的指责，威胁杀他并命令拘锁'),('砺','被指反对契丹人任节度使、萧翰居宫及其掠夺行为')],when='947年六月甲寅朔',place='恒州，张砺住宅',note='所列各项按萧翰的指责登记，不把指控自动当独立确证；国舅是萧翰自述称谓，不据此新增未核亲属关系。',description='萧翰指责张砺曾反对契丹人担任节度使、反对萧翰居于汴州宫中，并向耶律德光反映萧翰与解里劫掠财物、子女的行为。他威胁杀张砺，命人将张砺拘锁。上述指责按萧翰发言记载，不作为逐项独立确证。')
add('zhang_defends_advice_mada_stops','张砺坚持其建议关乎国家，麻答劝阻萧翰杀他',18,'砺抗声曰：','翰乃释之。',[('砺','表示所言是国家大事，反对被拘锁'),('麻荅','以不能擅杀大臣为由力救'),('萧翰','接受劝阻，释放张砺')],when='947年六月甲寅朔',place='恒州，张砺住宅')
sup('zhang_defends_advice_mada_stops',18,liao,'麻答以礪大臣，不可專殺，乃救止之。','《辽史》同记麻答以张砺为大臣、不可擅杀而阻止萧翰。','记当场救止，未推长期盟友关系。')
add('zhang_li_dies','张砺在受萧翰逼迫后去世',18,'是夕，',None,[('砺','当晚去世，史书记其愤恚')],when='947年六月甲寅当晚；《旧五代史》记乙卯',place='恒州',note='《资治通鉴》以是夕承甲寅，《旧五代史》置乙卯；愤恚为史书记述，不据此作医学死因判断。')
sup('zhang_li_dies',18,liao,'是夕，礪恚憤卒。','《辽史》也记张砺在受逼迫当晚愤恚去世。','补书没有干支日期，不消除主书与旧史的纪日差异。')
sup('zhang_li_dies',18,june,'是日，契丹右僕射兼中書侍郎、平章事張礪卒於鎮州。','《旧五代史》六月乙卯条记张砺在镇州去世。','与《资治通鉴》六月甲寅当晚不同，各自保留；镇州与恒州沿两书原称。',relation='conflicts',field='time_original')
add('cui_submits_mada_wine','崔廷勋向麻答行礼献酒',19,'崔廷勋',None,[('崔廷勋','趋行拜见，跪着向麻答献酒'),('麻荅','踞坐接受崔廷勋献酒')],when='947年六月，具体日未载',place='恒州',note='按行动记礼仪，不外推崔廷勋终身主从关系或心理。')
add('liu_arrives_xinan','刘知远到新安，西京留司官员前来迎接',20,'乙卯，',None,[('帝','到达新安，受西京留司官员迎接')],when='947年六月乙卯',place='新安')
add('qian_hongzuo_dies','吴越王钱弘佐去世',21,'吴越忠献王','弘佐卒。',[('弘佐','去世，史书称忠献王')],when='947年六月，具体日此段未另载',place='吴越',note='虽接乙卯条后，本段未明示同日；不把承叙位置直接当精确日。')
sup('qian_hongzuo_dies',21,zuo,'開運四年，佐卒，年二十，謚曰忠獻。','《新五代史》记钱佐在开运四年去世，年二十，谥忠献。','钱佐按吴越王身份与既有钱弘佐匹配，原文省略弘字保留；不将传统记龄倒推确定出生年。',relation='adds')
add('qian_hongzuo_will_names_hongzong','钱弘佐遗命由钱弘倧掌镇海、镇东两军',21,'遗令以',None,[('弘佐','遗命指定钱弘倧任两军节度使兼侍中'),('弘倧','被遗命指定继掌两军')],when='947年六月钱弘佐去世之际，具体遗命日未载',place='吴越镇海、镇东军',note='遗令与实际袭位区别，实际袭位继续按后文丙寅条录入；本段丞相是原任官职。')
sup('qian_hongzuo_will_names_hongzong',21,zong,'佐卒，弟倧以次立。','《新五代史》明确钱佐死后，弟弟钱倧依次继位。','前一段弟俶立是简略继承叙述，下一段补明倧先立、被废后迎俶；本条不提前录年末废立。',relation='adds')
relationship('弘佐','弘倧','兄长',21,'佐卒，弟倧以次立。','《新五代史》明确倧是佐的弟弟，方向表示钱弘佐是钱弘倧的兄长；不由此推生母相同。',source=zong)
add('liu_arrives_luoyang','刘知远进入洛阳宫中，汴州百官奉表迎接',22,'丙辰，','汴州百官奉表来迎。',[('帝','到洛阳，入居宫中，接受汴州百官迎表')],when='947年六月丙辰',place='洛阳宫中')
sup('liu_arrives_luoyang',22,june,'丙辰，車駕至洛，兩京文武百僚自新安相次奉迎。','《旧五代史》同记丙辰刘知远到洛阳，两京官员自新安陆续迎接。','两书到洛纪日相同，补书迎接范围更广，各自保留，不虚构具名官员。',relation='adds')
add('liu_reassures_khitan_appointees','刘知远安抚受契丹任命的官员，焚毁其告牒',22,'诏谕以','聚其告牒而焚之。',[('帝','下诏安抚受契丹任命者，收集并焚毁告牒')],when='947年六月丙辰条下，具体执行日未另载',place='洛阳',note='下诏勿自疑与焚告牒为主书记载，不推以后所有官员都永久不受追究。')
add('zhao_yuan_changes_name','赵远改名赵上交',22,'赵远更名','上交。',[('赵远','改名上交')],when='947年六月丙辰条下',place='洛阳',note='复用已有主体赵远及赵上交别名，不新建第二人物。')
add('liu_secret_order_kill_congyi','刘知远令郭从义先入大梁，并秘密命令杀李从益、王淑妃',22,'命郑州防御使','及王淑妃。',[('帝','令郭从义先入大梁清宫，密令杀母子'),('郭从义','受命先入大梁清宫，并收到秘密杀人命令')],when='947年六月丙辰条下（命令），具体执行日另考',place='洛阳至大梁',note='本事件为下令，参与角色说明收到命令，不把命令日自动当死亡日。',description='刘知远命郑州防御使郭从义先进入大梁清理宫禁，并秘密下令杀李从益与王淑妃。命令与母子实际被杀分别记载。')
add('congyi_wang_killed','李从益与王淑妃在大梁被杀',22,'命郑州防御使','闻者泣下。',[('从益','被刘知远下令杀害'),('淑妃','被杀，临死为李从益申辩')],when='947年六月；《旧五代史》记于丙辰条下',place='大梁',note='主书且死及旧史皆赐死支持执行事实；主书命令所在日与精确行刑日不直接等同。')
sup('congyi_wang_killed',22,june,'郇國公李從益、唐明宗淑妃王氏皆賜死於東京。','《旧五代史》本纪明确记李从益与王淑妃在东京被赐死。','独立补充已执行层，未把命令仅当计划，也不将旧史条目日强定为主书实际执行日。')
sup('congyi_wang_killed',22,li,'從益與王妃俱賜死於私第，時年十七；時人哀之。','《旧五代史》李从益传记母子被赐死于私第，李从益时年十七。','本传补地点形态与传统记龄，不倒推精确出生年；夹注《五代史阙文》仍只作为本来源中的转引。',relation='adds')
add('wang_last_plea_for_congyi','王淑妃临死质问为何杀李从益，希望留下他祭明宗陵',22,'淑妃且死，',None,[('淑妃','临死为李从益申辩，提出留其祭陵的愿望')],when='947年六月母子被杀之际，具体日未载',place='大梁',note='此愿望未被实现；每年寒食祭陵是请求，不建成后续实际祭祀事件。')
add('liu_departs_luoyang','刘知远离开洛阳',23,'戊午，','帝发洛阳。',[('帝','离开洛阳继续向大梁行进')],when='947年六月戊午',place='洛阳')
add('wei_returns_meets_liu','魏仁浦从契丹逃归，在巩迎见刘知远',23,'枢密院吏','见于巩。',[('魏仁浦','从契丹逃归，在巩迎见刘知远'),('帝','在巩见魏仁浦')],when='947年六月戊午离洛之后在巩迎见；逃归具体日未载',place='契丹至巩',note='戊午是刘知远发洛日期，不能据此推魏仁浦逃归当天。')
sup('wei_returns_meets_liu',23,wei,'漢祖起太原，次鞏縣，仁浦迎謁道左，即補舊職。','《宋史》同记魏仁浦在巩县迎见刘知远，并获补旧职。','迎见地与主书一致，补旧职只按补书记；未直接当此时获得高级官职。',relation='adds')
claim('person','person_魏仁浦','description','魏仁浦字道济，籍贯为卫州汲。',23,'魏仁浦，字道濟，衛州汲人。','传主及迎见刘知远情节与主书匹配；字与籍贯按直接传文补证。',source=wei)
add('guo_questions_trusts_wei','郭威询问兵数和旧制，因魏仁浦熟知而信任任用他',23,'郭威问以','威由是亲任之。',[('郭威','询问兵数与旧制，随后亲近并任用魏仁浦'),('魏仁浦','能熟记军务与旧制，获郭威信任')],when='947年六月巩县迎见之后，具体问答日未另载',place='巩及刘知远行营',note='强记精敏为史家评价；未推特定未载任官日期。')
sup('guo_questions_trusts_wei',23,troops,'時周祖掌樞密，召仁浦問闕下兵數，仁浦悉能記之，手疏六萬人。','《宋史》记郭威问京城兵数，魏仁浦手写六万人。','周祖指郭威；补书置其掌枢密时，未给具体年日，不强定主书巩县会面当天；六万为回答内容，不作独立军籍实测。',relation='adds')
add('officials_welcome_liu_xingyang','窦贞固等汴州百官在荥阳迎接刘知远',24,'辛酉，','迎于荥阳。',[('窦贞固','与汴州百官在荥阳迎接刘知远'),('帝','受汴州百官迎接')],when='947年六月辛酉',place='荥阳')
add('liu_arrives_daliang','刘知远到达大梁',24,'甲子，','帝至大梁，',[('帝','到达大梁')],when='947年六月甲子',place='大梁')
sup('liu_arrives_daliang',24,june,'甲子，車駕至東京。','《旧五代史》同记甲子刘知远到东京。','大梁、东京分别保留两书称谓，不建两次到达。')
add('jin_governors_submit_liu','晋朝藩镇陆续归附刘知远',24,'晋之籓镇',None,[('帝','获得晋朝藩镇陆续归附')],when='947年刘知远入大梁前后，具体各藩镇归降日未载',place='晋朝诸藩镇',note='相继概述不等于所有藩镇都在甲子同日归附；各地具名行动继续按后文逐段录入。')
reviews={17:'即位后拒命和白文珂攻城为回顾，围而不攻、戊申投降、禁兵入城及薛琼任官分录；初始攻城日不强定戊申。',18:'辛亥陕州与壬子石壕属五月，甲寅围张砺属六月；萧翰指责与医学死因不作确证，麻答救止、释放、死亡分录；旧史乙卯死亡异说保留。',19:'行礼献酒仅记实际举动，不推终身主从关系。',20:'乙卯新安迎接，匿名官员不猜姓名。',21:'钱弘佐死亡与遗命分录，原文未另明示死亡日；新史简写弟俶立须合下一段倧先立后废，不提前导入年末政变；兄长关系依据弟倧明文。',22:'到洛、安抚焚牒、更名、清宫密令、母子被杀与临终请求分录；命令与执行分清，旧史明确已执行，行刑日不随命令硬定；赵远复用已有别名。',23:'戊午为发洛日，魏逃归与会面不强定同日；宋史补字道济、卫州汲与补旧职；问六万兵置郭威掌枢密时，未强定巩县当日。',24:'辛酉荥阳迎接、甲子入大梁及各藩镇相继归附分开，概述不强定所有地方同日归附。'}
assert not (P/'publication.json').exists()
for n in range(17,25):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原22—29行连续八段，本卷累计24/75；947年跨卷尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],source_issues_review='张砺去世甲寅与乙卯分别引用；吴越简叙俶继位与下段倧先立层次分清；郭威问兵补书记于掌枢密时，确日待考；匿名人物及执行日不外推。',plain_language_review='首次逐项核对标题、人物说明、事件正文、角色、关系、时间地点、出处与事实说明；区分命令、实际执行、指控、愿望和史家评价，引用保持原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
