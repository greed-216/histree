# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 22–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,84))
COMMIT='6cb30a738bec3fb5634ff2481280a4833869f788'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-spring-government','songshi-261-guo-qiong-han']:
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
main_sources = ['tongjian-289-950-spring-government','tongjian-289-950-intercalary-month']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p022-p028',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-289-950-intercalary-month':'卷289·乾祐三年·闰月与六月等','jiuwudaishi-103-may-950':'卷103·隐帝本纪·乾祐三年五月','jiuwudaishi-103-intercalary-950':'卷103·隐帝本纪·乾祐三年闰月','jiuwudaishi-103-june-950':'卷103·隐帝本纪·乾祐三年六月','jiuwudaishi-103-hidden-emperor-commentary':'卷103·隐帝本纪·史家论述中的修德问答','jiuwudaishi-107-liu-zhu':'卷107·刘铢传·青州征召','xinwudaishi-030-shi-banquets':'卷30·史弘肇传·将相宴会冲突'}
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
lines = (ROOT / 'resources/derived/tongjian/289.txt').read_text().splitlines()
for n in range(22, 29):
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
    labels={'tongjian-289-950-intercalary-month':'卷289·乾祐三年·闰月与六月等','jiuwudaishi-103-may-950':'卷103·隐帝本纪·乾祐三年五月','jiuwudaishi-103-intercalary-950':'卷103·隐帝本纪·乾祐三年闰月','jiuwudaishi-103-june-950':'卷103·隐帝本纪·乾祐三年六月','jiuwudaishi-103-hidden-emperor-commentary':'卷103·隐帝本纪·史家论述中的修德问答','jiuwudaishi-107-liu-zhu':'卷107·刘铢传·青州征召','xinwudaishi-030-shi-banquets':'卷30·史弘肇传·将相宴会冲突'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年五月、闰月、六月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=950, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='950年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_289_0950_' + code
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
        edge = 'participation_zztj_289_0950_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_289_0950_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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




ALIASES.update({'帝':'刘承祐','太后':'李氏（刘知远妻）','承勋':'刘承勋','史弘肇妻':'阎氏（史弘肇妻）'})
NEW_ALIASES={'刘承勋':['劉承勛','劉承勳'],'阎氏（史弘肇妻）':['閻氏（史弘肇妻）'],'郭超':[]}
NEW_DESCRIPTIONS={
'刘承勋':'刘承祐的弟弟。950年五月以山南西道节度使身份被任命为开封尹，加兼中书令；《资治通鉴》同时说明他实际尚未出阁。与947年已去世的刘承训分开，生卒年未载。',
'阎氏（史弘肇妻）':'史弘肇的妻子。史书记她曾是酒家倡，即在酒家表演的歌伎。950年王章宴会上，史弘肇把苏逢吉关于阎姓的玩笑理解为讥讽妻子的出身。她是否出席宴会未载，名字和生卒年未载。',
'郭超':'卫州刺史。《宋史》郭琼传记他与郭琼奉命率部屯青州，涉及后汉征召刘铢。该传没有单列行动纪日，《资治通鉴》相应段只列郭琼；生卒年未载。'}
may='jiuwudaishi-103-may-950';leap='jiuwudaishi-103-intercalary-950';june='jiuwudaishi-103-june-950';commentary='jiuwudaishi-103-hidden-emperor-commentary';liuzhu='jiuwudaishi-107-liu-zhu';shi='xinwudaishi-030-shi-banquets';guohan='songshi-261-guo-qiong-han'
add('guo_wei_departure_advice','郭威辞行，劝刘承祐听取太后教导并信任旧臣',22,'庚子，','帝敛容谢之。',[('郭威','辞行时劝皇帝听取太后教导、亲近忠直、信任旧臣，并承诺守边'),('刘承祐','听取郭威辞行劝告，郑重致谢')],when='950年五月庚子',place='后汉朝廷',description='郭威辞行时劝刘承祐听取李太后的教导，亲近忠直、远离谗邪，信任苏逢吉、杨邠、史弘肇等旧臣，并表示愿尽力守边。刘承祐郑重致谢。',note='必无败失是郭威对旧臣的信任与劝告，不当后续不会失败的事实；太后被提到不证明她出席辞行。')
add('guo_wei_yedu_defensive_orders','郭威到邺都后，命边将严守边境、不得出境侵掠',22,'威至鄴都，',None,[('郭威','到邺都后要求边将严守边境，不得出境侵掠')],when='950年五月辞行到邺都后，具体到任日未载',place='邺都、河北边境',description='郭威到邺都后，因河北困弊，要求边将严加防备、不得出境侵掠。契丹若入侵，就守坚固城寨，清空城外可被敌军利用的粮草等物资，等待对方。',note='坚壁清野为备敌指令，不写成本段已经全线实施清野或打退新一次入侵。')
add('regional_reporting_order','后汉规定防御使、团练使非军务须先经观察使奏报',23,'辛丑，',None,[('刘承祐','下敕规定防御使、团练使的奏报程序')],when='950年五月辛丑',place='后汉各州与朝廷',description='后汉规定，防御使、团练使除军事事项外，不得自行直接奏报，应先报观察使，由其斟酌后上报朝廷。',note='军期按军事事项理解，保留例外，不写成任何情况都禁止直接奏报。')
add('liu_chengxun_kaifeng_appointment','刘承勋获任开封尹，加兼中书令',24,'丙午，',None,[('刘承祐','任命弟弟刘承勋为开封尹，加兼中书令'),('承勋','以山南西道节度使身份获任开封尹，加兼中书令')],when='950年五月丙午',place='后汉朝廷、开封',note='未出阁表示尚未出阁任事，不据此补年龄或已经实掌开封政务。承勋与承训字不同，后者947年已去世，不合并。')
sup('liu_chengxun_kaifeng_appointment',24,may,'丙午，以皇弟興元節度承使勛為開封尹，加兼中書令，未出閣。','《旧五代史》同日也记皇弟承勋任开封尹、兼中书令，并说明未出阁。','兴元、山南西道职称对照；旧史电子本节度承使勋有转录字序问题，摘录原样保留，不据此另建承使勋人物。')
relationship('刘承祐','刘承勋','兄长',24,'以皇弟山南西道节度使承勋','皇弟明确刘承勋是刘承祐的弟弟，因此刘承祐是其兄长；未据本句推同母。')
add('guo_qiong_qingzhou_deployment','后汉担心刘铢拒召，派郭琼率兵屯青州',25,'平卢节度使','将兵屯青州。',[('刘铢','朝廷想征召他，担心他拒命'),('郭琼','奉命率兵屯青州，配合征召刘铢'),('刘承祐','朝廷借沂密对南唐用兵的机会安排郭琼屯青州')],when='950年五月刘铢庚戌入朝之前，具体部署日未载',place='青州、平卢军',note='贪虐恣横为史书对刘铢的评价，借沂密用兵不另造本月新的完整对唐战役。部署与后续实际入朝分开。')
sup('guo_qiong_qingzhou_deployment',25,guohan,'先遣瓊與衛州刺史郭超以所部兵屯青州。','《宋史》郭琼传还记郭琼与卫州刺史郭超一起率部屯青州。','郭超为补书具名参与者，通鉴略去不等于不存在；该传未单列日，不补为庚戌部署。',relation='adds')
pk=person('郭超',25,'与郭琼奉命率部屯青州','先遣瓊與衛州刺史郭超以所部兵屯青州。',source=guohan)
ek='participation_zztj_289_0950_guo_qiong_qingzhou_deployment_'+pk
B['person_events'].append(dict(key=ek,person_key=pk,event_key=E['guo_qiong_qingzhou_deployment'],role='《宋史》记他与郭琼率部屯青州',status='draft'))
claim('person_event',ek,'role','《宋史》记郭超以卫州刺史身份，与郭琼率部屯青州。',25,'先遣瓊與衛州刺史郭超以所部兵屯青州。','此参与来自宋史补证，未认定他在通鉴未记的其他场合也出席。',source=guohan)
sup('guo_qiong_qingzhou_deployment',25,liuzhu,'因前浙州刺史郭瓊自海州用兵還，過青州，遂留之，','《旧五代史》刘铢传记郭琼从海州返回、经过青州后被留在当地。','与主书五月主动派兵的叙述方式不同。前浙州为该电子本原字，另据同书本纪为前沂州，字形问题保留；不强定两次驻屯或重排行军日。',relation='conflicts')
add('liu_zhu_plans_banquet_attack','刘铢设宴召郭琼，埋伏兵士准备杀他',25,'铢不自安，','欲害之。',[('刘铢','不安，设宴召郭琼并埋伏兵士准备杀他'),('郭琼','成为刘铢设宴召来、准备袭击的对象')],when='950年五月刘铢入朝前，具体宴会日未载',place='青州刘铢宴会场所',note='伏兵为实际布置，欲害是意图；后文未敢发动，不能写成郭琼已被杀伤。')
add('guo_qiong_attends_liu_banquet','郭琼知道设伏，仍屏退随从从容赴宴',25,'琼知其谋，','铢不敢发。',[('郭琼','知道刘铢谋划，屏退随从从容赴宴'),('刘铢','见郭琼从容无惧，没有发动伏兵')],when='950年五月刘铢入朝前',place='青州刘铢宴会场所',note='未列郭琼如何得知、伏兵人数和是否被解除，不造反击或缴械结果。')
sup('guo_qiong_attends_liu_banquet',25,guohan,'瓊知其謀，屏去從者，從容就席，略無懼色，銖不敢發。','《宋史》也记郭琼屏退随从从容入席，刘铢没有发动伏兵。','同一经过印证，姓名和动作对照，未把新旧传记重复录成两次宴会。')
add('guo_qiong_persuades_liu_depart','郭琼向刘铢陈说利害，刘铢接诏后动身',25,'琼因谕','诏至即行。',[('郭琼','向刘铢说明去留的利害'),('刘铢','听取劝告，诏令到达后动身')],when='950年五月庚戌入朝前，具体动身日未载',place='青州至后汉京师',note='即行是接诏后动身，庚戌才记入朝，不把两者都定为庚戌。')
sup('guo_qiong_persuades_liu_depart',25,guohan,'瓊因為陳禍福，銖感其言，遂治裝。俄詔至，即日上道。','《宋史》也记郭琼陈说利害、刘铢准备行装，接诏后当天动身。','即日对应接诏之日，原传未列绝对纪日，不自行填庚戌。')
add('liu_zhu_audience','刘铢入朝',25,'庚戌，','铢入朝。',[('刘铢','由青州入朝')],when='950年五月庚戌',place='后汉京师',note='入朝不等于当日已被囚禁或处死，后续职务另按后文录。')
add('guo_qiong_yingzhou','后汉任命郭琼为颍州团练使',25,'辛亥，',None,[('郭琼','获任颍州团练使'),('刘承祐','任命郭琼为颍州团练使')],when='950年五月辛亥',place='颍州',note='主书电子本颖州与补书潁州字形不同，规范名称用颍州，原文保持颖；不把宋史随后加防御使强定为辛亥。')
sup('guo_qiong_yingzhou',25,guohan,'瓊改潁州團練使，又加防禦使。','《宋史》也记郭琼改颍州团练使，随后又加防御使。','传记未列后加防御使日期，只作为职务补充，不把两次职变压为本日。',relation='adds')
add('wang_zhang_banquet_hand_game','王章宴请朝贵，阎晋卿教史弘肇行酒令',26,'癸丑，','屡教之。',[('王章','设宴招待朝贵，席间行手势酒令'),('史弘肇','不熟悉手势酒令，由阎晋卿指教'),('阎晋卿','坐在史弘肇旁边，多次教他行酒令')],when='950年五月癸丑',place='王章宴会场所',note='手势令为宴饮酒令，不笼统当作今日某套固定划拳规则；未列所有与会者。')
add('su_joke_shi_insults','苏逢吉开阎姓玩笑，史弘肇认为受讥而辱骂他',26,'苏逢吉戏','逢吉不应。',[('苏逢吉','就阎姓开玩笑，被辱骂后不回应'),('史弘肇','认为玩笑讥讽妻子出身，愤怒辱骂苏逢吉')],when='950年五月癸丑宴会上',place='王章宴会场所',note='意是史弘肇的理解，不能断言苏逢吉明确承认讥讽妻子。阎氏为妻子背景，不证明她出席。')
relationship('阎氏（史弘肇妻）','史弘肇','妻子',26,'弘肇妻阎氏，本酒家倡也，','妻子方向明确，未因与阎晋卿同姓推亲属关系。')
claim('person',people['阎氏（史弘肇妻）'],'description','史书记史弘肇妻子阎氏曾是酒家倡，即在酒家表演的歌伎。',26,'弘肇妻阎氏，本酒家倡也，','本为背景追述，具体经历时间未载，不扩为950年在宴会中表演或与阎晋卿同族。')
sup('su_joke_shi_insults',26,shi,'弘肇妻閻氏，酒家倡，以為譏己，大怒，以醜語詬逢吉，逢吉不校。','《新五代史》也记史弘肇把玩笑理解为讥讽，于是辱骂苏逢吉，苏没有争辩。','两书同样通过史弘肇的理解说明冲突，未证苏的内心用意。')
add('shi_threatens_su_su_leaves','史弘肇想殴打苏逢吉，苏逢吉起身离席',26,'弘肇欲殴','逢吉起去。',[('史弘肇','想殴打苏逢吉'),('苏逢吉','起身离开宴席')],when='950年五月癸丑宴会上',place='王章宴会场所',note='欲殴是意图，未明记已经打中、造成伤势。')
add('yang_stops_shi_sword_pursuit','史弘肇索剑欲追苏逢吉，杨邠哭着劝止',26,'弘肇索剑','愿孰思之！”',[('史弘肇','索剑准备追苏逢吉'),('杨邠','哭着劝阻，提醒杀宰相将使皇帝难处')],when='950年五月癸丑宴会后段',place='王章宴会场所',note='索剑欲追不写成已刺杀或追上苏逢吉，愿孰思之底本字形不改。')
add('yang_escorts_shi_home','史弘肇骑马离开，杨邠并骑送他回家',26,'弘肇即上马','送至其第而还。',[('史弘肇','骑马离开宴会'),('杨邠','与史弘肇并骑，将他送回家后返回')],when='950年五月癸丑宴会之后',place='王章宴会场所至史弘肇宅第',note='联镳解释为并骑同行，不补路线、随从名单或事后和解。')
add('wang_jun_mediation_fails','刘承祐命王峻设宴调解将相冲突，但没有成功',26,'于是将相','不能得。',[('刘承祐','命王峻设宴调解将相冲突'),('王峻','设宴调解，但未成功')],when='950年五月癸丑宴会冲突后，具体调解日未载',place='后汉京师，主书未列场所',note='将相如水火为史家形容冲突加深，不据此造所有将军与所有文臣全面敌对关系。')
sup('wang_jun_mediation_fails',26,shi,'隱帝遣王峻置酒公子亭和解之。','《新五代史》具体记王峻的调解宴设在公子亭。','地点为补书增加，句末只叙和解安排，没有明确成功，不覆盖主书未能成功。',relation='adds',field='location_name')
add('su_abandons_external_post','苏逢吉想外任避开史弘肇，后来放弃',26,'逢吉欲求','吾齑粉矣！”',[('苏逢吉','考虑外任避开史弘肇，又因担心后果而放弃')],when='950年五月将相冲突之后，具体日未载',place='后汉朝廷',note='欲求出镇是考虑，未有正式任命或已到外镇。吾齑粉为其担忧，不作为他当时已被杀事实。')
add('yang_shi_stop_wang_external_post','王章想求外官，杨邠与史弘肇坚持劝止',26,'王章亦忽忽',None,[('王章','不乐，想求外官'),('杨邠','坚持劝止王章外任'),('史弘肇','坚持劝止王章外任')],when='950年五月将相冲突之后，具体日未载',place='后汉朝廷',note='固止为坚持劝止，不写成王章已被外放或离开三司职位。')
add('palace_anomaly_record','史书记录后汉宫中多次出现怪异现象',27,'闰月，','宫中数有怪。',[],when='950年五月之后的闰月，具体各次日期未载',place='后汉宫中',note='有怪为史书记载，性质未说明，不作现代验证过的鬼怪事实。旧史描写也保留为来源说法。')
sup('palace_anomaly_record',27,leap,'是月，宮中有怪物，投瓦石，擊窗撼扉，人不能制。','《旧五代史》把同月宫中异象写作有不明怪物投瓦石、击窗摇门。','这是电子底本中的叙述，未经现代证实，不据此建立真实超自然生物主体或把它确定为人为袭击。',relation='adds')
add('capital_storm_flood','后汉京师遭大风雨、雷击和积水',27,'癸巳，','水深平地尺馀。',[],when='950年五月之后的闰月癸巳',place='后汉京师、郑门',description='史书记大风雨掀毁屋舍、拔树，郑门门扇被吹起，落在十多步外。雷击死亡六七人，平地积水一尺多。',note='数字与长度沿史书概数，不换算现代测量。发屋为屋舍受风损坏，未造现代气象风速或灾区全貌。')
sup('capital_storm_flood',27,leap,'閏月癸巳，京師大風雨，壞營舍，吹鄭門扉起，十數步而墮，拔大木數十，震死者六七人，水平地尺餘，池隍皆溢。','《旧五代史》同日也记京师风雨、雷击死亡与积水，并补营舍损毁、沟渠皆溢。','主书数字与补书概数对应，仍为史书记数，不当独立现代统计。',relation='adds')
add('zhao_yanyi_recommends_virtue','刘承祐询问消灾祈祷方法，赵延乂建议修德',27,'帝召司天监','莫如修德。”',[('刘承祐','召赵延乂询问消灾祈祷方法'),('赵延乂','说明专长在天文历日，不熟祈祷术，建议皇帝修德')],when='950年闰月风雨之后，具体问答日未载',place='后汉朝廷',note='禳祈为当时消灾祈祷观念，建议修德是政治劝告，不宣称能以道德改变天气。')
sup('zhao_yanyi_recommends_virtue',27,commentary,'召司天監趙延乂訊其休咎，延乂對以修德即無患，','《旧五代史》史家论述中也记刘承祐询问赵延乂，赵建议修德。','此段未单列问答年月，只印证人物与对答，不作为精确日期独立确证。')
add('zhao_yanyi_zhenguan_zhengyao','刘承祐追问如何修德，赵延乂建议学习《贞观政要》',27,'延乂归，',None,[('刘承祐','赵延乂离开后，派宦官追问如何修德'),('赵延乂','建议读《贞观政要》并效法其中做法')],when='950年闰月赵延乂初次答问之后，具体日未载',place='赵延乂返回后的传话现场',note='这是建议，未记皇帝实际读完或依书改政；中使未具名，不写赵当面再次进奏。')
sup('zhao_yanyi_zhenguan_zhengyao',27,commentary,'既退，遣中使就問延乂曰：「何者為德？」延乂勸讀《貞觀政要》。','《旧五代史》也记皇帝在赵延乂退出后派宦官追问，赵劝读《贞观政要》。','次序与对象相合，后文史家批评皇帝的因果判断未当成本日实际政策变化。')
add('zhengzhou_river_breach','河水在郑州境内决口',28,'六月，',None,[],when='950年六月，具体日未载',place='郑州境内',note='主书仅列决口地点，未补死伤或面积；旧史进一步列原武县界，不自行换算现代河道坐标。')
sup('zhengzhou_river_breach',28,june,'鄭州奏，河決原武縣界。','《旧五代史》同月记郑州奏报河水在原武县界决口。','奏报在癸卯条下未独立列日，不能把癸卯直接确定为决口发生日。',relation='adds',field='location_name')
reviews={22:'辞行日期庚子、到任日未知；听太后教导与信旧臣是郭威劝告，太后未认定在场，保证不败不是事实。边防指令与实际新战役区分，坚壁清野解释物资防敌，不造执行结果。',23:'防御团练使奏报程序有军务例外，不扩大成一律禁止直奏。',24:'刘承勋与已死刘承训分开，皇弟只证兄弟方向，不推同母；未出阁不补年龄或实际掌京府。旧史节度承使勋原字保留。',25:'征召计划、屯军、设宴伏兵、郭屏从赴宴、未敢发、谕去留、接诏动身、庚戌入朝、辛亥任颍州分开。郭超从宋史补参与；旧刘传郭自海州返经过留镇叙次与主部署不同不强造两次，旧前浙州与主前沂州待核。后加防御职无日，不提前套辛亥。',26:'酒令与阎教为已发生，苏玩笑目的未明，史认为受讥与欲殴索剑不是已伤杀。妻阎氏只背景、同姓不推亲。杨劝送、王峻调解未成功、苏拟外镇后止、王章欲外官被止分开，不造已外任。新史公子亭只补调解地点，妻倡为原称及解释不补经历年月。',27:'宫怪为史书报告不确证超自然，风雨雷击数字长度沿概数未换现代统计。初召答修德与退出后宦官追问荐书分开，建议不当真实改变天气或帝已读书。闰月依五月后六月前年界，不补公历月日。',28:'决口按六月，旧史原武县界补地点；奏报附日不当实际灾害日，未补死伤面积。'}
assert not (P/'publication.json').exists()
for n in range(22,29):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(22,29)],next_paragraph=Q[29]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原27—33行连续七段；发布后首28/83正文已录，余55段待录。快照更多后文仍未处理。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(22,29)],source_issues_review='刘铢征召部署在旧传与主书的叙次不同，前浙州疑字保留；颍颖统一展示原字不改。承勋承训不同人。宫中异象为来源叙述，不现代证实；风雨数字、决口奏报日与发生日严格区分。纸本及电子转录异文待核。',plain_language_review='首次逐条检查人物、标题正文、参与角色、关系方向、日期地点和来源解释。明确计划与结果、主观讥讽理解、劝告、祈祷观念与史书记数；未补伤害或外任结果，不定未知日期，旧主体档案保持，原引用不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
