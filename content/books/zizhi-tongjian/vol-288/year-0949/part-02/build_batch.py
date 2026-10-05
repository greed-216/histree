# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 949 paragraphs 12–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
COMMIT='69dcf8a2fbba2850268b5fe5a8e94410a672cacd'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-102-may-949','jiuwudaishi-110-guo-hezhong-949']:
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
main_sources = ['tongjian-288-949-zhao-surrender','tongjian-288-949-june-july']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0949-p012-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-288-949-zhao-surrender':'卷288·乾祐二年·赵思绾请降及追述','tongjian-288-949-june-july':'卷288·乾祐二年·六月至八月','jiuwudaishi-109-zhao-surrender-949':'卷109·赵思绾传·请降与被杀','jiuwudaishi-109-li-shouzhen-death':'卷109·李守贞传·河中陷落','jiuwudaishi-100-li-su-retirement':'卷100·高祖本纪·天福十二年八月李肃致仕','xinwudaishi-053-zhao-surrender':'卷53·赵思绾传·请降与被杀','songshi-249-wang-pu-hezhong':'卷249·王溥传·河中焚书'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(12, 17):
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
    labels={'tongjian-288-949-zhao-surrender':'卷288·乾祐二年·赵思绾请降及追述','tongjian-288-949-june-july':'卷288·乾祐二年·六月至八月','jiuwudaishi-109-zhao-surrender-949':'卷109·赵思绾传·请降与被杀','jiuwudaishi-109-li-shouzhen-death':'卷109·李守贞传·河中陷落','jiuwudaishi-100-li-su-retirement':'卷100·高祖本纪·天福十二年八月李肃致仕','xinwudaishi-053-zhao-surrender':'卷53·赵思绾传·请降与被杀','songshi-249-wang-pu-hezhong':'卷249·王溥传·河中焚书'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐二年（949年五月至七月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0949_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=949, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='949年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0949_' + code
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
        edge = 'participation_zztj_288_0949_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0949_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘承祐','唐主':'李璟','吴越王':'钱弘俶','弘亿':'钱弘亿','李肃':'李肃（晋昌节度副使）','王溥':'王溥（后周宋初）','靖\ue4c1余':'靖余'})
NEW_ALIASES={'张氏（李肃妻）':['张夫人','張氏（李肅妻）'],'程让能':['程讓能'],'钭滔':['鈄滔'],'李崇勋':['李崇勳'],'李崇玉':[],'靖余':[],'孙愿':['孫願'],'刘芮':['劉芮'],'王溥（后周宋初）':[]}
NEW_DESCRIPTIONS={
'张氏（李肃妻）':'张全义的女儿、李肃的妻子，个人名字与生卒年未载。《通鉴》记她劝李肃厚赠赵思绾，后来又劝丈夫让赵思绾归顺后汉。早期赠物的经过与《旧五代史》附注有所不同，分别保留。',
'程让能':'赵思绾的判官。949年与李肃劝赵思绾归顺后汉，《旧五代史》还记他起草章表。《新五代史》写陈让能，保留姓氏异说，未凭字形另建第二个人。生卒年未载。',
'钭滔':'吴越内牙都指挥使，史书记为胡进思的党羽。949年有人告发他谋叛，钱弘俶不愿深入追究，将他贬到处州。告发涉及钱弘亿，未据此认定两人确已谋反。生卒年未载。',
'李崇勋':'李守贞的儿子。《通鉴》记949年七月壬戌与父母等自焚。旧史附注另有李崇训的名字，尚待校核，不在本批直接合并。生年未载。',
'李崇玉':'李守贞的儿子。949年七月河中城陷时被郭威俘获，送到大梁处死。生年未载。',
'靖余':'李守贞任命的宰相。949年河中城陷时被俘，送到大梁处死。《通鉴》姓名中带有无法正常显示的字形，本批据《旧五代史》同一被俘、处死名单写作靖余，原文保留，纸本姓名待核。',
'孙愿':'李守贞任命的宰相。949年七月河中城陷时被俘，送到大梁处死。生年及此前经历未载。',
'刘芮':'李守贞任命的枢密使。949年七月河中城陷时被俘，送到大梁处死。生年及此前经历未载。',
'王溥（后周宋初）':'949年为秘书郎，在河中平定后劝郭威焚毁涉及朝臣、藩镇的往来书信，《宋史》王溥传也记此事。与901年条所载同名王溥分开建档。生卒年留待具体原文补录。'}
NEW_DEATH_YEARS={'李崇勋':949,'李崇玉':949,'靖余':949,'孙愿':949,'刘芮':949}
zhao='jiuwudaishi-109-zhao-surrender-949';li='jiuwudaishi-109-li-shouzhen-death';ls='jiuwudaishi-100-li-su-retirement';xin='xinwudaishi-053-zhao-surrender';wang='songshi-249-wang-pu-hezhong';may='jiuwudaishi-102-may-949';guo='jiuwudaishi-110-guo-hezhong-949'
add('zhao_cruelty_report','史书记赵思绾食人肝、以酒吞人胆',12,'赵思绾好食人肝，','则胆无敌矣。”',[('赵思绾','被史书记载有食人肝、吞人胆的行为')],year=None,when='史书概述赵思绾此前的行为，具体年月未载',place='具体地点未载',note='行为按史书记载；吞食千枚能无敌是赵思绾自称，不当作生理事实。')
add('zhao_siege_cannibalism','长安粮尽后，史书记赵思绾杀害妇女儿童充作军粮',12,'及长安城中食尽，','如羊豕法。',[('赵思绾','在长安粮尽后杀害妇女儿童充作军粮')],when='949年长安被围、赵思绾请降以前，具体日未载',place='长安',note='日计数和每次犒军数百为史书记载，不据此推算总死亡数。')
add('guo_invites_zhao_surrender','郭从义派人劝诱赵思绾投降',12,'思绾计穷，','使人诱之。',[('郭从义','派人劝诱赵思绾投降'),('赵思绾','因计穷而成为劝降对象')],when='949年五月受命为华州留后之前，具体日未载',place='长安')
add('li_su_refuses_zhao_servant_request','赵思绾年轻时请求做李肃的仆人，李肃拒绝',12,'初，思绾少时，','他日必为叛臣。”',[('赵思绾','年轻时请求做李肃的仆人'),('李肃','拒绝赵思绾的请求，并认为他日后可能叛乱')],year=None,when='赵思绾年轻时，具体年月未载',place='具体地点未载',note='李肃的说法属于当时的预测；请求被拒，不建立实际主仆关系。')
claim('person',people['李肃（晋昌节度副使）'],'description','李肃曾任晋昌军节度副使，947年八月获加左骁卫上将军致仕。',12,'前晉昌軍節度副使李肅加左驍衛上將軍致仕。','原文官职与《通鉴》所称退休将军一致，用于识别本批李肃；不与单州李肃直接合并。',source=ls)
add('zhang_gifts_zhao','李肃妻张氏劝丈夫厚赠赵思绾，以免结怨',12,'肃妻张氏，','厚以金帛遗之。',[('张氏（李肃妻）','劝李肃不要使赵思绾结怨'),('李肃','听妻子劝告后厚赠赵思绾'),('赵思绾','获得金帛赠物')],year=None,when='赵思绾年轻时的追述，具体年月未载',place='具体地点未载',note='乃厚以金帛遗之承接夫妻讨论，赠物主体按上下文理解为李肃一家；附注另记张夫人赠思绾妻，保留不同经过。')
relationship('张全义','张氏（李肃妻）','父亲',12,'肃妻张氏，全义之女也，','全义为张全义；女儿名字未载，用亲属身份限定，方向为张全义是张氏的父亲。')
relationship('李肃','张氏（李肃妻）','丈夫',12,'肃妻张氏，全义之女也，','李肃是张氏的丈夫，不另建反向妻子关系。')
add('zhao_visits_li_su','赵思绾占据长安后，多次拜访李肃',12,'及思绾据长安，','拜伏如故礼。',[('赵思绾','多次拜访李肃，仍按过去礼节拜伏'),('李肃','在长安闲居，接受赵思绾拜访')],year=None,when='赵思绾占据长安以后、请降以前，具体年月未载',place='长安',note='据城始于948年，本句反复拜访的具体日期未载，不能全部定在949年。')
add('zhang_stops_li_su_suicide_plan','李肃担心赵思绾连累自己，妻子劝他促成归顺',12,'肃曰：','曷若劝之归国！”',[('李肃','担心被赵思绾连累，想自杀'),('张氏（李肃妻）','劝丈夫让赵思绾归顺朝廷')],year=None,when='赵思绾反复拜访李肃后、请降前，具体年月未载',place='长安',note='欲自杀是念头，不写成李肃已经死亡；归国在此指归顺后汉。')
add('li_su_cheng_persuade_zhao','李肃与程让能劝赵思绾向后汉归顺',12,'会思绾问自全之计，','思绾从之，',[('赵思绾','询问自保之策，接受归顺建议'),('李肃','劝赵思绾趁朝廷三路用兵时归顺'),('程让能','以判官身份同李肃劝降')],when='949年五月乙丑任命前，具体日未载',place='长安',note='不失富贵是劝降时的判断，不是朝廷永久保证；与七月实际处死分开。')
sup('li_su_cheng_persuade_zhao',12,zhao,'時左驍衛上將軍致仕李肅寓居城中，因與判官程讓能同言於思綰曰：','《旧五代史》也记退休将军李肃与判官程让能共同劝赵思绾归顺。','同一官职、地点和劝降经过印证；不把书证重复当两次劝降。')
sup('li_su_cheng_persuade_zhao',12,xin,'其判官陳讓能謂思綰曰：','《新五代史》把劝降判官写作陈让能。','《通鉴》《旧五代史》作程让能；同一劝降经过下保留姓氏异说，姓名仍待纸本校核。',relation='conflicts')
add('zhao_requests_surrender','赵思绾派使者到后汉朝廷请降',12,'思绾从之，','诣阙请降。',[('赵思绾','接受劝告，派使者到朝廷请降')],when='949年五月乙丑任命前，具体派使日未载',place='长安至后汉朝廷')
sup('zhao_requests_surrender',12,zhao,'思綰然之，即令讓能為章表，遣牙將劉成琦入朝。','《旧五代史》记赵思绾让程让能起草章表，遣牙将刘成琦入朝。','同书本纪作刘成，未自行合并使者姓名或补出另一位人物。',relation='adds')
add('han_appoints_zhao_huazhou','后汉任命赵思绾为华州留后，命他前往任所',12,'乙丑，','令便道之官。',[('赵思绾','获任华州留后，奉命前往任所'),('刘承祐','在位朝廷任命赵思绾与常彦卿')],when='949年五月乙丑',place='后汉朝廷、华州',note='为任命，不等于赵思绾实际已到华州；郭从义七月奏报另有授命过程。')
sup('han_appoints_zhao_huazhou',12,may,'制授趙思綰華州節度留後、檢校太保，以永興城內都指揮使常彥卿為虢州刺史。','《旧五代史》本纪同记赵思绾任华州节度留后、检校太保。','本纪与主书同为五月乙丑；《新五代史》称镇国军留后，分别保留职称。')
sup('han_appoints_zhao_huazhou',12,xin,'拜思綰鎮國軍留後，趣使就鎮，','《新五代史》记赵思绾获任镇国军留后，并被催促到任。','镇国军与华州称谓对照，不据此另建一次同日任命；具体职称按各书保留。',relation='adds')
add('han_appoints_chang_guozhou','后汉任命常彦卿为虢州刺史',12,'乙丑，','令便道之官。',[('常彦卿','由都指挥使获任虢州刺史')],when='949年五月乙丑',place='后汉朝廷、虢州',note='任命不等于已经抵达虢州；七月仍见于长安。')
add('wu_yue_accuses_dou_tao','吴越有人告发钭滔谋叛，牵连钱弘亿',13,'吴越内牙都指挥使钭滔，','辞连丞相弘亿。',[('钭滔','遭到谋叛告发，史书记为胡进思党羽'),('胡进思','被史书列为钭滔所属派系人物'),('钱弘亿','受到告发牵连')],when='949年五月条后、六月条前，具体日未载',place='吴越',note='或告为有人告发；不写成已查明谋反，不据同句建立三人的盟友关系。')
add('qian_chu_demotes_dou_tao','钱弘俶不愿深入追究告发，将钭滔贬到处州',13,'吴越王弘亻叔',None,[('钱弘俶','不愿深究，将钭滔贬到处州'),('钭滔','被贬到处州')],when='949年五月条后、六月条前，具体日未载',place='吴越、处州',note='弘亻叔为底本钱弘俶字形，复用规范主体；未载钱弘亿同时被定罪。')
add('june_solar_eclipse','史书记六月初一发生日食',14,'六月，',None,[],when='949年六月癸酉朔',place='观测地点未载',note='朔为初一；仅录史书天象，不补食分、观测位置或灾变因果。')
add('zhao_receives_edict_returns_city','赵思绾出城接受诏命，郭从义守门并让他回城',15,'秋，七月，','复遣还城。',[('赵思绾','卸下甲胄出城接受诏命，随后回城'),('郭从义','派兵守南门，让赵思绾回城')],when='949年七月甲辰',place='长安城及南门',note='接受诏命不等于已前往华州。')
add('guo_returns_zhao_weapons','赵思绾索要牙兵与铠甲兵器，郭从义给还',15,'思绾求其牙兵','从义亦给之。',[('赵思绾','请求给还牙兵和铠甲兵器'),('郭从义','答应并给还')],when='949年七月甲辰受诏后、壬子被捕前，具体日未载',place='长安')
add('zhao_delays_departure','赵思绾收集财物，三次更改出发日期',15,'思绾迁延，','三改行期。',[('赵思绾','收集财物，拖延赴任并三次更改行期')],when='949年七月甲辰受诏后、壬子被捕前，具体日未载',place='长安')
add('guo_wei_allows_action_against_zhao','郭从义等怀疑赵思绾，秘密请示郭威后获准处置',15,'从义等疑之，','威许之。',[('郭从义','怀疑赵思绾，秘密请示郭威'),('郭威','同意郭从义等采取行动')],when='949年七月壬子以前，具体请示日未载',place='长安与河中行营',note='此句未直接列出具体处刑命令，图之按随后捕杀行动解释。')
add('guo_wang_capture_execute_zhao','郭从义与王峻诱捕赵思绾，连同常彦卿等处死',15,'壬子，',None,[('郭从义','入城以饮酒告别为由召来赵思绾，将他捕杀'),('王峻','以都监、南院宣徽使身份共同入城'),('赵思绾','被捕后在市中处死'),('常彦卿','与赵思绾及父兄部曲等一并处死')],when='949年七月壬子',place='长安府署、市场',note='《通鉴》记三百人，《旧五代史》记五百余人；不自行统一数字，也不从父兄两字补出具体姓名。')
sup('guo_wang_capture_execute_zhao',15,zhao,'是日，並部下叛黨新授虢州刺史常彥卿等五百餘人並誅之。','《旧五代史》记常彦卿等五百余人同日被处死。','《通鉴》同一处置记三百人，保留统计异说，不另建第二次处刑。',relation='conflicts')
sup('guo_wang_capture_execute_zhao',15,xin,'從義因入城召思綰，趣之上道，至則擒之。','《新五代史》也记郭从义入城召赵思绾，待他到来后擒获。','同一召见捕杀经过，不能据不同详略另算一次被俘。')
claim('person',people['赵思绾'],'death_year','赵思绾于949年七月壬子被处死。',15,span(15,'壬子，'),'更新事实引用，不覆盖已有发布人物档案字段。')
claim('person',people['常彦卿'],'death_year','常彦卿于949年七月与赵思绾等一并被处死。',15,span(15,'壬子，'),'原文同列处刑对象，不把父兄解释为已知姓名。')
add('guo_takes_hezhong_outer_city','郭威攻下河中外城，李守贞退守内城',16,'甲寅，','退保子城。',[('郭威','率军攻下河中外城'),('李守贞','收拢残军，退守内城')],when='949年七月甲寅',place='河中',note='外郭与子城区分，外城陷落不等于全城已被平定。')
sup('guo_takes_hezhong_outer_city',16,guo,'七月十三日，帝率三寨將士奪賊羅城。','《旧五代史》周太祖纪记七月十三日郭威率三寨将士攻下外城。','该篇帝为传主郭威，非后汉皇帝；日期保留原纪日。')
add('guo_declines_rushed_inner_city_attack','诸将请求急攻河中内城，郭威主张等待',16,'诸将请急攻之，','安用急为！”',[('郭威','认为对方困守仍会反击，拒绝立即急攻')],when='949年七月甲寅破外城后、壬戌城陷前',place='河中',note='涸水取鱼为军事比喻，不写作实际排水捕鱼。')
add('li_shouzhen_family_self_immolation','河中城陷时，李守贞与妻子、李崇勋等自焚',16,'壬戌，','等自焚，',[('李守贞','与妻子、儿子等自焚'),('李崇勋','与父母等自焚')],when='949年七月壬戌',place='河中',note='等未列完整名单，妻子姓名未载，不认为李守贞所有子女均死于火中。')
sup('li_shouzhen_family_self_immolation',16,li,'二年七月，城陷，舉家蹈火而死。','《旧五代史》也记乾祐二年七月城陷时李守贞一家自焚。','同篇后文仍记数子二女被俘，举家不能扩写为所有家属无一幸存。')
claim('person',people['李守贞'],'death_year','李守贞于949年七月河中城陷时自焚而死。',16,span(16,'壬戌，','等自焚，'),'原文自焚与后文被俘者区分；不覆盖旧主体未填的死亡字段。')
relationship('李守贞','李崇勋','父亲',16,'李守贞与妻及子崇勋等自焚，','子明确为李守贞之子；不未经校核把崇勋与崇训合并。')
add('guo_captures_li_son_officials','郭威进入河中，俘获李崇玉、靖余、孙愿等',16,'威入城，','国师总伦等，',[('郭威','进入城中并俘获李守贞的儿子和所任官员'),('李崇玉','作为李守贞的儿子被俘'),('靖余','作为李守贞任命的宰相被俘'),('孙愿','作为李守贞任命的宰相被俘'),('刘芮','作为李守贞任命的枢密使被俘'),('总伦','以国师身份被俘')],when='949年七月壬戌河中城陷时',place='河中',note='靖姓名中的特殊字形保留于摘录，规范名据旧史同一名单写靖余，纸本待核；所署宰相不指后汉朝廷宰相。')
claim('person',people['靖余'],'name','《旧五代史》同一河中被俘、处死名单写作靖余。',16,'僧總倫、靖余、張球、','与主书同场身份对应，仅据旧史选择可显示姓名；不擅自补造主书缺失字。',source=li)
relationship('李守贞','李崇玉','父亲',16,'获其子崇玉等','其指李守贞，李崇玉是被俘儿子，不能同李崇勋自焚混为一人。')
add('hezhong_captives_executed_daliang','李崇玉、靖余等被送往大梁，在市中处死',16,'威入城，','磔于市。',[('李崇玉','被送往大梁处死'),('靖余','被送往大梁处死'),('孙愿','被送往大梁处死'),('刘芮','被送往大梁处死'),('总伦','被送往大梁处死')],when='949年七月河中城陷后，具体处刑日未载',place='大梁',note='七月壬戌明确为城陷、自焚日，押送和处刑不强定同一天。')
sup('hezhong_captives_executed_daliang',16,li,'諸子並賊黨孫願、劉芮、張延嗣、劉仁裕、僧總倫、靖余、張球、王廷秀、焦文傑、安在欽等並磔於西市，','《旧五代史》还列出孙愿、刘芮、总伦、靖余等在西市被处死。','正文名单比主书详，补充西市定位，其他姓名保留在引用中，待后续具体身份补证。',relation='adds')
add('han_recruits_zhao_xiuji','后汉征召赵修己担任翰林天文',16,'征赵修己','为翰林天文。',[('赵修己','被征召担任翰林天文')],when='949年七月河中城陷后条下，具体日未载',place='后汉朝廷',note='仅记征召，不把主书此前天文预测转成科学事实。')
add('guo_finds_correspondence','郭威发现朝臣、藩镇与李守贞的书信，准备上报',16,'威阅守贞文书，','欲奏之。',[('郭威','查阅书信，认为有悖逆之意，准备向朝廷奏报')],when='949年七月河中城陷后，具体日未载',place='河中',note='欲奏是计划；未列具体通信者姓名，不推定某位已知朝臣参与谋反。')
add('wang_pu_advises_burning_letters','王溥劝郭威焚毁往来书信，郭威接受',16,'秘书郎榆次王溥',None,[('王溥','以秘书郎身份劝郭威焚毁书信，以安定人心'),('郭威','接受王溥焚毁书信的建议')],when='949年七月河中城陷后，具体日未载',place='河中',note='王溥对应《宋史》后周宋初宰相传，与901年同名人分开；原文魑魅为比喻，反仄字形保留，解释为不安之人。')
sup('wang_pu_advises_burning_letters',16,wang,'時李守貞據河中，趙思綰反京兆，王景崇反鳳翔，周祖將兵討之，辟溥為從事。','《宋史》记郭威讨三叛时征辟王溥为从事。','周祖指郭威；传主经历与本句秘书郎相合，不把从事写成朝廷另一位王溥。',relation='adds')
sup('wang_pu_advises_burning_letters',16,wang,'願一切焚之，以安反側。」周祖從之。','《宋史》也记王溥请求焚毁书信，郭威接受。','两书记载同一建议，不推定所有被提及官员都已被证明无罪。')
reviews={12:'分开早年追叙、劝降、请降和五月任命；拒绝仆人请求不建主仆关系。李肃以947年晋昌副使致仕记录辨认；程/陈、使者姓名及赠物经过异说保留。',13:'告发与定罪区分，钱弘亿只是受牵连；弘亻叔沿用钱弘俶，不建派系盟友推论。',14:'原纪年月初一保留，不换算公历或引入天象因果。',15:'受诏回城、给还兵甲、迟留、秘密请示、捕杀分开；三百与五百余并列，父兄姓名不补造。',16:'外城与内城区分，自焚与俘虏押送处死分开。李崇勋/崇训未合并，靖余据旧史名单显示、原缺字保留。王溥与901年同名人分开，欲奏不是已奏，焚书建议不推成无罪证明。'}
assert not (P/'publication.json').exists()
for n in range(12,17):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=949,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(12,17)],next_paragraph=Q[17]['id'],next_volume=288,next_year=949,supplements=supplements,excluded_non_body=[],coverage='卷288原90—94行连续五段，949年累计首16/37正文，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(12,17)],source_issues_review='程/陈让能、赵思绾处刑人数、赠物与请降使者异说保留。靖姓名缺字与崇勋/崇训尚待纸本校核，未补造缺字或强行合并。原纪日不自行换算；各书不同职称和详略分别定位。',plain_language_review='首次逐条检查标题、人物介绍、事件说明、参与角色、时间地点说明与事实解释。明确姓名主语，区分预测、计划、告发、任命和实际结果；早年追述用null。展示使用简体，逐字引用不改。复用主体保留旧档案字段，不安排固定发布后二次重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
