# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,45))
COMMIT='2a028697786379c39fe2e5fec2c736c49f846f9f'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['xinwudaishi-009-944-january']:
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
main_sources = ['tongjian-284-944-february-march']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0944-p001-p008',
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
lines = (ROOT / 'resources/derived/tongjian/284.txt').read_text().splitlines()
for n in range(1, 9):
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
        month = '二月至三月条下及追述'
        citation = f'卷284·后晋天福九年、后称开运元年（944；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0944_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=944, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='944年二月至三月条下，具体日期未载'
    key = 'event_zztj_284_0944_' + code
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
        edge = 'participation_zztj_284_0944_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_284_0944_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','契丹主':'耶律德光','杜威':'杜重威','周儒':'周儒（后晋博州刺史）','李琼':'李琼（后晋将领）'})
NEW_ALIASES={'石赟':['石贇'],'白再荣':['白再榮'],'麻答':[],'梁汉璋':['梁漢璋'],'薛怀让':['薛懷讓'],'石公霸':[],'李琼（后晋将领）':['李瓊（后晋将领）'],'王君怀':['王君懷'],'李守超':[],'安重怀':['安重懷'],'乌韩七':['烏韓七'],'何彦超':['何彥超']}
NEW_DESCRIPTIONS={
'石赟':'后晋前保义节度使。944年二月甲辰朔奉命驻守麻家口，戊午又奉诏分兵驻郓州。《辽史》同场部署写石斌，姓名异文尚待校核，未据此另作同人合并。生卒年未载。',
'白再荣':'后晋护圣都指挥使。944年二月甲辰朔奉命驻守马家口。原地名与石赟所守麻家口分别保留，不自动混写。生卒年本批未核。',
'麻答':'契丹将领，《资治通鉴》称为耶律德光的从弟。944年二月由周儒引导从马家口渡河，攻郓州北津，以接应杨光远。个人其他名字及生卒年本批未核。',
'梁汉璋':'应州人，后晋陈州防御使。944年二月乙巳与李守贞、皇甫遇、薛怀让等率合计一万军队沿河水陆进兵。生卒年本批未核。',
'薛怀让':'太原人，后晋怀州刺史。944年二月乙巳与李守贞、皇甫遇、梁汉璋等率合计一万军队沿河水陆进兵。生卒年本批未核。',
'石公霸':'后晋先锋指挥使。944年二月丙午在戚城与高行周、符彦卿一起遭契丹围攻，石重贵亲自率军救援后解围。生卒年未载。',
'李琼（后晋将领）':'后晋将领，沧州饶安人，曾与石敬瑭在李嗣源部下效力。出帝时任棣州刺史，拒绝杨光远招降；944年二月击退杨光远围城。《旧五代史》此役作冀州，与主书棣州并列待核。与马殷部下李琼分别建档。',
'王君怀':'后晋阶州、成州义军指挥使。944年二月率部千余人投降后蜀，请求作向导攻取阶州、成州。生卒年未载。',
'李守超':'《旧五代史》记944年三月澶州交战中率数百骑兵攻击契丹、使其稍退的晋方将领。姓名原文保留，纸本及是否有异名尚待校核，未直接并入李守贞。生卒年未载。',
'安重怀':'后晋护圣第二军都指挥使。《旧五代史》记944年三月交战中因被指临阵怯战、丢失兵器，与乌韩七、何彦超被斩。生卒具体月日本批未核。',
'乌韩七':'后晋护圣军指挥使。《旧五代史》记944年三月交战中因被指临阵怯战、丢失兵器，与安重怀、何彦超被斩。姓名字形与纸本待核。',
'何彦超':'后晋监军。《旧五代史》记944年三月交战中因被指临阵怯战、丢失兵器，与安重怀、乌韩七被斩。生卒具体日期未载。'}
feb='jiuwudaishi-082-944-february';mar='jiuwudaishi-082-944-march';liao='liaoshi-004-944-february'
# 1: guard orders, another account of the river crossing, joint expedition.
for code,title,start,end,name,role,place in [
('shi_yun_majia_guard','后晋命石赟驻守麻家口','二月，','守麻家口，','石赟','以原保义节度使身份受命驻守麻家口','麻家口'),
('he_yangliu_guard','后晋命何重建驻守杨刘镇','前威胜','守杨刘镇，','何重建','以原威胜节度使身份受命驻守杨刘镇','杨刘镇'),
('bai_majia_guard','后晋命白再荣驻守马家口','护圣都指挥使','守马家口，','白再荣','以护圣都指挥使身份受命驻守马家口','马家口'),
('an_heyang_guard','后晋命安彦威驻守河阳','西京留守','守河阳。','安彦威','以西京留守身份受命驻守河阳','河阳')]:
 add(code,title,1,start,end,[('帝','命将领驻守河防要地'),(name,role)],when='944年二月甲辰朔',place=place,note='命令与已抵达驻地分清；麻家口和马家口按底本分别保留，不自动合并。')
sup('he_yangliu_guard',1,feb,'何建守楊劉鎮，','《旧五代史》同场部署的杨刘守将写为何建。','主书何重建与旧史何建姓名异文保留，未用本句把全站其他何建主体自动合并。',relation='conflicts')
sup('shi_yun_majia_guard',1,liao,'晉將景延廣命石斌守麻家口，','《辽史》此场部署写景延广命石斌守麻家口。','与主书朝廷命石赟有姓名及发令者差别；文本可能承袭通鉴，不视为独立身份确证。',relation='conflicts')
add('mada_crosses_river','《资治通鉴》记周儒引麻答从马家口渡河，攻郓州北津',1,'未几，','以应杨光远。',[('周儒','引麻答从马家口渡河'),('麻答','在河东扎营并攻郓州北津，意在接应杨光远')],when='944年二月甲辰后未几，具体日未载',place='马家口、郓州北津',note='卷283末颜衎的渡河奏报已录，本段补具名麻答、扎营与攻击细节；两段纪时并列，可能记同次渡河，衔接待核，暂不推为两次不同渡河。')
sup('mada_crosses_river',1,liao,'未幾，周儒引遼軍麻答營于河東，攻鄆州北津，以應光遠。','《辽史》也写周儒引麻答在河东扎营，攻郓州北津，接应杨光远。','可能承袭主书的平行记载，不据文字相近另推一支军队或另一次渡河。')
claim('event',E['mada_crosses_river'],'description','此前颜衎奏报已提周儒引契丹渡河、蔡行遇被擒，本段补麻答在东岸扎营和攻北津。',1,'未几，周儒引契丹将麻答自马家口济河，营于东岸，攻郓州北津以应杨光远。','关联既有 event_zztj_283_0944_zhou_ru_guides_river_crossing 所载报告，两段可能记同次渡河，具体时序待核；不据本条另建蔡行遇第二次被俘。')
relationship('契丹主','麻答','从兄',1,'麻答，契丹主之从弟也。','原文从弟指同宗旁系中较年幼的同辈男性亲属，反向用从兄；不写成同父亲弟弟，不补两人父亲身份。')
add('li_joint_river_expedition','后晋派李守贞、皇甫遇、梁汉璋、薛怀让率一万兵沿河水陆进军',1,'乙巳，','水陆俱进。',[('帝','派四将率军沿河水陆进军'),('李守贞','与三将率合计一万人沿河进军'),('皇甫遇','与三将率合计一万人沿河进军'),('梁汉璋','以陈州防御使身份共同率军'),('薛怀让','以怀州刺史身份共同率军')],when='944年二月乙巳',place='沿河',note='万人是四将所率合计兵力，不各写一万；未名分军不造单独兵数。')
for name,quote,value in [('李守贞','守贞，河阳；','李守贞籍贯河阳。'),('梁汉璋','汉璋，应州；','梁汉璋籍贯应州。'),('薛怀让','怀让，太原人也。','薛怀让籍贯太原。')]:
 claim('person',people[name],'description',value,1,quote,'这是籍贯，不作为当日驻地或出生坐标。')
# 2: previous prohibition, surrounding army, urgent requests, rescue and complaints.
add('jing_prohibits_mutual_rescue','景延广先令各将分地防守，不许互相救援',2,'先是景延广','无得相救。',[('景延广','令各将分地守备，不准互相援救')],when='944年二月丙午戚城被围前的部署，具体日期未载',place='晋军',note='先是只明确前后关系，不按丙午确定禁令当天发布。')
add('qicheng_encirclement','契丹在戚城包围高行周、符彦卿和石公霸',2,'丙午，','于戚城。',[('高行周','在戚城遭契丹包围'),('符彦卿','在戚城遭契丹包围'),('石公霸','以先锋指挥使身份遭包围')],when='944年二月丙午',place='戚城')
sup('qicheng_encirclement',2,feb,'丙午，先鋒指揮使石公霸與契丹遇於戚城之北，為契丹所圍。','《旧五代史》补充石公霸先在戚城北遇敌被围，高行周、符彦卿随后督军进入战场。','该书展开三将受围的先后，不写三将开战前一直在同一地点。',relation='adds')
add('qicheng_urgent_request','高行周等告急，景延广迟缓地向石重贵报告',2,'行周等告急，','延广徐白帝，',[('高行周','与受围将领派人告急'),('景延广','迟缓地向石重贵报告'),('帝','收到景延广报告')],when='944年二月丙午受围期间',place='戚城、晋军行营',note='徐为迟缓，不凭此量化拖延时长。')
add('shi_rescues_qicheng','石重贵亲自率军救援，契丹解围离去',2,'帝自将救之。','契丹解去，',[('帝','亲自率军救援受围将领')],when='944年二月丙午',place='戚城')
add('qicheng_generals_complain','戚城三将哭诉援兵迟缓，险些无法脱身',2,'三将泣诉',None,[('高行周','与其他受围将领哭诉救援迟缓'),('符彦卿','与其他受围将领哭诉救援迟缓'),('石公霸','与其他受围将领哭诉救援迟缓')],when='944年二月丙午解围后',place='戚城',note='几不免为危急经历，不把三将记为阵亡。')
E['shi_rewards_qicheng']=event('shi_rewards_qicheng','石重贵在戚城古台置酒慰劳三将，三将指责景延广未及时援救',2,'登戚城古臺，置酒以勞三將，鹹咎延廣不遣兵赴難，相對泣下。',[('帝','在戚城古台置酒慰劳三将'),('高行周','与另外两将指责救援迟缓'),('符彦卿','与另外两将指责救援迟缓'),('石公霸','与另外两将指责救援迟缓')],source=feb,when='944年二月丙午解围后，置酒时刻未载',place='戚城古台',note='登台主语结合皇帝亲自救援上下文，鹹底本疑字原样保留，展示为三将皆指责。')
# 3: positions, attack, losses, supplies and appointment.
add('li_arrives_majia','李守贞等到达马家口',3,'戊申，','至马家口。',[('李守贞','与此前同军将领到达马家口')],when='944年二月戊申',place='马家口')
add('khitan_fortifies_majia','契丹派一万步兵筑垒，骑兵在外防护，其余数万兵留河西并渡兵',3,'契丹遣步卒','未已，',[],when='944年二月戊申交战前',place='马家口东岸及河西',note='主书骑兵数量未明；数十艘船渡兵与其余河西兵数分开，不将船数乘兵额。')
sup('khitan_fortifies_majia',3,liao,'麻答遣步卒萬人築營壘，騎兵萬人守于外，餘兵屯河西。','《辽史》将筑垒的发令者写为麻答，并记外守骑兵一万人。','主书未具名发令者、未列骑兵一万，独立保留该书记数；文本可能依通鉴，不算独立兵数确证。',relation='adds')
add('jin_takes_majia_fort','晋军逼近后契丹骑兵退走，晋军攻下马家口营垒',3,'晋兵薄之，','拔之。',[('李守贞','率军攻取马家口契丹营垒')],when='944年二月戊申',place='马家口',note='守贞领军由前段将领及旧纪明文补证，不为未具名士兵造主体。')
sup('jin_takes_majia_fort',3,feb,'李守貞以師搏之，遂破其眾。','《旧五代史》明确进攻主将为李守贞。','只支持攻营主将，不从等字强造其他将领个人斩杀战果。')
sup('jin_takes_majia_fort',3,'xinwudaishi-009-944-january','二月戊申，前軍都虞候李守貞及契丹戰于馬家渡，敗之。','《新五代史》也记二月戊申李守贞在马家渡击败契丹。','马家渡马家口作为各书记载名称保留，不据同战役补未经核验坐标。')
add('khitan_majia_losses','契丹在马家口战败，数千人投河淹死，另有数千被俘或被斩',3,'契丹大败，','亦数千人。',[],when='944年二月戊申',place='马家口河岸',note='俘斩为混合记数，不记成数千俘虏全部已被杀；不相加为伪精确人数。')
add('khitan_west_bank_withdraws','河西契丹兵哭号撤走，此后不敢再向东进军',3,'河西之兵','复东。',[],when='944年二月戊申战败之后',place='马家口河西',note='史书对此支军队的后续概述，不扩大为所有契丹部队从此永不渡河。')
E['majia_captures_executed']=event('majia_captures_executed','《旧五代史》记马家口晋军获马八百，俘将七十八人、部众五百人，送行营后皆被斩',3,'獲馬八百匹，生擒賊將七十八人，部眾五百人，送行在，悉斬之。',[],source=feb,when='944年二月戊申交战后，具体处刑日未载',place='马家口、晋军行营',note='数字按旧纪分类保留，不强造明确亲自下令或行刑者；与主书俘斩数千是不同范围记数。')
add('li_yiyin_border_report','李彝殷奏报率四万兵从麟州渡河，侵入契丹境内',3,'辛亥，','契丹之境。',[('李彝殷','奏报率四万兵从麟州渡河侵契丹境')],when='944年二月辛亥，奏报日',place='麟州至契丹境内',note='辛亥是奏报日期，不强作全部四万兵同日出发、渡河、完成侵入。')
sup('li_yiyin_border_report',3,feb,'辛亥，夏州節度使李彜殷合蕃漢之兵四萬抵麟州，濟河，侵契丹之境，以牽脅之。','《旧五代史》明确四万兵为蕃汉合兵，行动意在牵制契丹。','本书明列合兵类别和目的，原字彜殷保留，不按现代族群给每支军队补比例。',relation='adds')
add('li_yiyin_southwest_commander','后晋任李彝殷为契丹西南面招讨使',3,'壬子，','招讨使。',[('帝','任李彝殷为契丹西南面招讨使'),('李彝殷','受任为契丹西南面招讨使')],when='944年二月壬子',place='后晋',note='契丹西南面为后晋讨契丹的行营职掌，不解释为契丹政权任命。')
add('khitan_pacifies_captured_cities','契丹取得贝州、博州后曾安抚居民，有时授官赐服',3,'初，契丹主','赐服章。',[('契丹主','在取得两州后安抚居民，或授官赐服')],when='944年两州被契丹取得后的追述，具体日期未载',place='贝州、博州',note='抚尉保留安抚意；不推所有居民都受官，不把本条概述当新一次攻陷。')
add('khitan_kills_captives_after_defeat','契丹在戚城、马家口战败后杀害被俘百姓，并焚烧军士',3,'及败于戚城','燔炙之。',[('契丹主','史书记其战败愤怒后所属军队杀害被俘者')],when='944年二月戚城、马家口交战后，具体日未载',place='契丹军所过之处未逐一列出',note='军中集体暴力不写为皇帝亲手杀尽所有人，未具体记数不补杀害总额。')
add('jin_reacts_to_captive_killings','史书记晋人因契丹杀害俘虏而愤怒，协力抗敌',3,'由是晋人',None,[],when='944年上述杀害记载之后，具体日期未载',place='后晋',note='这是史书记载的集体反应，不强造全体晋人每人同样想法或具名指挥者。')
# 4: intended alliance, two imperial orders and no advance.
add('yang_plans_westward_join','杨光远率青州兵，打算向西与契丹会合',4,'杨光远','西会契丹。',[('杨光远','率青州兵打算向西与契丹会合')],when='944年二月条下，具体日期未载',place='青州',note='欲会合是计划，不将其写为已成功会师。')
add('shi_yun_yunzhou_order','后晋命石赟分兵驻郓州，防备杨光远',4,'戊午，','以备之。',[('帝','命石赟分兵驻郓州'),('石赟','奉诏分兵驻郓州防杨光远')],when='944年二月戊午',place='郓州')
add('liu_order_attack_hengzhou','后晋命刘知远从土门出恒州，进攻契丹',4,'诏刘知远','击契丹，',[('帝','命刘知远从土门出恒州攻契丹'),('刘知远','受到出兵进攻契丹的命令')],when='944年二月条下，具体日期未载',place='土门、恒州',note='只记命令，后句驻乐平不进另列，不说刘已从土门进入恒州。')
add('liu_order_rendezvous_xingzhou','后晋又命刘知远在邢州与杜重威、马全节会合',4,'又诏','于邢州。',[('帝','命刘知远与杜重威、马全节会合'),('刘知远','受到会合命令'),('杜威','被指定为会合对象'),('马全节','被指定为会合对象')],when='944年二月条下，具体日期未载',place='邢州',note='命令未证明三人已在邢州齐集。')
add('liu_stops_leping','刘知远率兵驻乐平，没有继续进军',4,'知远引兵',None,[('刘知远','驻兵乐平，没有继续进军')],when='944年二月上述诏令后，具体日期未载',place='乐平',note='不进为行动状态，不从本句自行补谋反动机。')
# 5: mourning and music, a retrospective practice followed by a dated refusal.
add('shi_music_after_mourning','石重贵居丧满一年后，让女乐工在宫中轻声奏乐',5,'帝居丧期年，','细声女乐。',[('帝','居丧满一年后让女乐工在宫中奏乐')],year=None,when='石敬瑭去世居丧满一年后，开始演奏的具体年月本句未载',place='后晋宫中',note='期年为一年期限，开始时点为追述，不硬套944年二月或据时长造精确日。')
add('shi_campaign_music','石重贵出征后常令身边人奏乐歌舞，声称这不算音乐',5,'及出师，','此非乐也。”',[('帝','在出征中常令身边人奏乐歌舞，并声称不算音乐')],when='944年本次出征期间的行为概述，具体日期未载',place='晋军行营',note='此非乐也为皇帝说法，与实际奏乐动作并列，不能当音乐学判断。')
add('shi_rejects_official_music','百官上表请求正式听乐，石重贵下诏不许',5,'庚申，',None,[('帝','拒绝百官上表请求听乐')],when='944年二月庚申',place='晋军行营')
sup('shi_rejects_official_music',5,feb,'庚申，宰臣馮道等再上表請聽樂，皆不允。','《旧五代史》具名请求者为冯道等宰臣，并写再次请求。','再表示此前也有请求但日期未给，不补另一次日期和全文。',relation='adds')
pk=person('冯道',5,'与宰臣上表请求听乐','庚申，宰臣馮道等再上表請聽樂，皆不允。',source=feb)
edge='participation_zztj_284_0944_shi_rejects_official_music_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['shi_rejects_official_music'],role='与宰臣再次上表请求听乐，由《旧五代史》具名',status='draft'))
claim('person_event',edge,'role','冯道与宰臣再次上表请求听乐。',5,'庚申，宰臣馮道等再上表請聽樂，皆不允。','身份具名由旧纪补证。',source=feb)
# 6–7: city name discrepancy, appointment, desertion and request for a guide role.
add('yang_attacks_di','杨光远围棣州，被刺史李琼击败后焚营退回青州',6,'壬戌，','走还青州。',[('杨光远','围棣州失利，烧营退回青州'),('李琼','以州兵击败围城的杨光远')],when='944年二月壬戌',place='棣州至青州',note='李琼依据新史棣州任职建立后晋将领主体，不与896年马殷部下混同；地名异文独立保留。')
sup('yang_attacks_di',6,feb,'壬戌，楊光遠率兵圍冀州，刺史李瓊以州兵擊之，棄營而遁。','《旧五代史》将同日被围州写为冀州，记李琼击败杨光远、杨弃营退去。','与主书棣州地名不同，保留异说不静默改字；旧纪未写杨本人焚营或已到青州。',relation='conflicts')
claim('person',people['李琼（后晋将领）'],'description','《新五代史》记出帝时李琼任棣州刺史，拒绝杨光远书信招降。',6,'出帝時，為棣州刺史。楊光遠反，以書招瓊，瓊拒而不納。','本传承接李琼与石敬瑭在明宗军中旧事，区别马殷部下同名将；主书同一出帝与杨叛时段据此识别。',source='xinwudaishi-047-li-qiong',relation='adds')
for code,title,start,end,name,role in [
('he_east_commander','后晋任何重建为东面马步都部署','癸亥，','马步都部署，','何重建','受任东面马步都部署'),
('he_garrisons_yunzhou','何重建率兵驻郓州','将兵',None,'何重建','率兵驻郓州')]:
 add(code,title,6,start,end,[(name,role)],when='944年二月癸亥条下，率军到达日未单列' if code.endswith('yunzhou') else '944年二月癸亥',place='郓州')
sup('he_east_commander',6,feb,'癸亥，以前鄧州節度使何建為東南面馬步軍都部署，率師屯汶陽。','《旧五代史》写前邓州节度使何建任东南面马步军都部署，驻汶阳。','姓名、此前职衔、东面或东南面及驻地均与主书不完全相同，作为对应场景异说保留，未自动合并何建主体。',relation='conflicts')
add('wang_junhuai_surrenders_shu','王君怀率阶成义军千余人投降后蜀',7,'阶、成义军','叛降蜀，',[('王君怀','率部千余人投降后蜀')],when='944年二月甲子前，具体日期未载',place='阶州、成州一带',note='义军为原军职名称，不因名称推民兵所有成员政治倾向。')
add('wang_requests_guide_role','王君怀请求作向导，协助后蜀攻取阶州、成州',7,'请为','阶、成。',[('王君怀','请求为后蜀作向导攻取两州')],when='944年二月投降后，具体日期未载',place='阶州、成州',note='请求不等于已获批准、已带路或两州已被攻取。')
add('shu_attacks_jiezhou','后蜀军进攻阶州',7,'甲子，',None,[],when='944年二月甲子',place='阶州',note='原文仅攻，尚未记陷城；未明领军者，不自动补孟昶亲征或王君怀亲带路。')
sup('shu_attacks_jiezhou',7,feb,'甲子，蜀人寇我階州。','《旧五代史》也记甲子蜀军进攻阶州。','我为晋本纪立场，本站展示不使用我方他方。')
# 8: ruse, reports, rain delay, proposed attack, battle phases and a deserter's message.
add('khitan_feigns_withdrawal','契丹假装离开元城，在古顿丘城埋伏精骑，等待晋军会合后袭击',8,'契丹伪弃','而击之。',[],when='944年三月癸酉前的部署，具体设伏日期未载',place='元城、古顿丘城',note='等待晋军会合是战术计划，不写伏击已经成功。')
add('zhang_reports_retreat','张从恩多次奏报契丹已经撤退',8,'鄴都留守','遁去；',[('张从恩','多次奏报契丹已经撤退')],when='944年三月癸酉前，具体各次奏报日未载',place='邺都',note='这是张从恩报告内容，前句主书明确是契丹诈退，不能把报告当真实撤军结论。')
add('jin_rain_halts_pursuit','晋军打算追击契丹，因连日下雨停止前进',8,'大军欲进','而止。',[],when='944年三月癸酉前，具体日期未载',place='元城附近晋军',note='欲追未执行到底，不造晋军已冲入契丹伏击圈。')
add('khitan_ambush_hunger','契丹伏兵等待十天，人马疲乏饥饿',8,'契丹设伏','人马饥疲。',[],when='944年三月癸酉前的设伏期间',place='古顿丘城',note='旬日表示十天时长，不据此造确定公历开始日。')
add('zhao_proposes_bridge_attack','赵延寿建议围攻晋军城下、夺浮桥，声称可定天下，耶律德光采用',8,'赵延寿曰：','契丹主从之，',[('赵延寿','提出围攻城下、夺浮桥的建议'),('契丹主','采纳赵延寿建议')],when='944年三月癸酉前，具体日期未载',place='契丹军营',note='天下定是建议者的预测，不写后晋已因这次建议灭亡。')
add('khitan_deploys_chanzhou','耶律德光率十余万兵列阵澶州城北',8,'三月，','不见其际。',[('契丹主','率十余万兵列阵澶州城北')],when='944年三月癸酉朔',place='澶州城北',note='城上望不见尽头为原文军势描述，不换算阵线精确公里数。')
add('gao_qicheng_south_battle','高行周前军在戚城南与契丹作战，自中午至傍晚互有胜负',8,'高行周前军','互有胜负。',[('高行周','率前军在戚城南与契丹交战')],when='944年三月癸酉朔，自午至晡',place='戚城南',note='互有胜负不写成单方面全胜；晡为下午晚段，不自行折算精确钟点。')
sup('gao_qicheng_south_battle',8,mar,'賊將趙延壽、趙延昭以數萬騎出王師之西，契丹主自擁精騎出王師之東，兩軍接戰，交相勝負。','《旧五代史》补充赵延寿、赵延昭骑兵在晋军西侧，耶律德光精骑在东侧。','只补布阵与交战概述，赵延昭沿用既有赵延照主体，不增加另一支同名军。',relation='adds')
add('shi_faces_khitan_main_force','耶律德光率精兵向晋中军来，石重贵列阵迎战',8,'契丹主以精兵','出陈以待之。',[('契丹主','率精兵向晋中军进攻'),('帝','列阵准备迎战')],when='944年三月癸酉朔',place='澶州战场')
add('khitan_questions_yang_claim','耶律德光看到晋军人数众多，质疑杨光远称其半已饿死的说法',8,'契丹主望见','今何其多也！”',[('契丹主','见晋军众多，质疑杨光远提供的说法')],when='944年三月癸酉朔',place='澶州战场',note='杨光远此前声称晋兵半已饿死，仅从转述保留，不变成真实军队死亡比例。')
add('jin_crossbows_resist','契丹骑兵从两侧冲击，晋军坚守不动，以齐射弩箭使敌稍退',8,'以精骑左右','契丹稍却；',[('契丹主','令精骑从两侧冲击晋阵')],when='944年三月癸酉朔',place='澶州战场',note='万弩齐发为史书记数，不据此反推出全部晋军每人持弩或具体装备库存。')
add('khitan_attacks_east_flank','《资治通鉴》记契丹再攻晋阵东侧，未能取胜',8,'又攻晋陈','不克。',[],when='944年三月癸酉朔',place='晋阵东侧')
sup('khitan_attacks_east_flank',8,mar,'契丹乃率精騎以攻東邊，王師敗走，敵騎追之。','《旧五代史》记东侧交战中晋军败退，契丹骑兵追击。','与主书东偏不克展开结果不同，分别保留；旧纪此处为一个战场阶段，不直接改写整场为晋军全败。',relation='conflicts')
E['jin_dike_troops_deter']=event('jin_dike_troops_deter','契丹追兵看到堤间晋军旗帜，以为伏兵而停止追击',8,'時有夾馬軍士千餘人在堤間治水寨，旗幟之末出於堰埭，敵望見之，以為伏兵所起，追騎乃止。',[],source=mar,when='944年三月癸酉东侧交战中，具体时刻未载',place='晋阵东侧河堤',note='以为伏兵是契丹判断，原文说晋兵正在修水寨，不另造晋军已安排伏击。')
E['li_shouchao_counterattack']=event('li_shouchao_counterattack','《旧五代史》记李守超率数百骑反击，使契丹稍退',8,'久之復戰，王師又退，李守超以數百騎短兵直起擊之，敵稍卻。',[('李守超','率数百骑近战反击契丹')],source=mar,when='944年三月癸酉交战期间，具体时刻未载',place='澶州战场',note='李守超姓名原字保留，尚未证其与李守贞同人，不静默改字；稍退不等全军溃败。')
add('chanzhou_battle_losses','两军苦战至暮，史书记死者无法计数',8,'苦战至暮，','不可胜数。',[],when='944年三月癸酉朔，至暮',place='澶州战场',note='不可胜数不给伪精确伤亡总数，也不将两军合计全部算作晋军阵亡。')
add('khitan_night_withdrawal','天黑后契丹撤离战场，在三十里外扎营',8,'昏后，','之外。',[],when='944年三月癸酉朔夜间',place='澶州战场三十里外，方位未载',note='三十里保留原单位，不换算现代距离或补方向。')
E['jin_executes_fearful_officers']=event('jin_executes_fearful_officers','《旧五代史》记安重怀、乌韩七、何彦超因被指临阵怯战而被斩',8,'護聖第二軍都指揮使安重懷、指揮使烏韓七、監軍何彥超等臨陣畏怯，手失兵仗，悉斬之。',[('安重怀','因被指临阵怯战、丢失兵器而被斩'),('乌韩七','因被指临阵怯战、丢失兵器而被斩'),('何彦超','因被指临阵怯战、丢失兵器而被斩')],source=mar,when='944年三月癸酉交战条下，确切处刑时刻未载',place='晋军行营',note='等字不补未具名被斩者；理由为本纪所载，不虚构审判过程或皇帝亲自执行。')
for name in ['安重怀','乌韩七','何彦超']:
 for x in B['people']:
  if x['name']==name:x['death_year']=944
 claim('person',people[name],'death_year',name+'据《旧五代史》于944年三月交战条下被斩。',8,'護聖第二軍都指揮使安重懷、指揮使烏韓七、監軍何彥超等臨陣畏怯，手失兵仗，悉斬之。','悉斩明确死亡，确切日未单列，不把叙述位置当作精确行刑时刻。',source=mar,relation='adds')
add('khitan_deserter_reports_retreat','契丹小校偷马投晋，声称契丹已传木书、收军北去',8,'乙亥，','收军北去。',[],when='944年三月乙亥',place='晋军行营',note='小校未具名，不造人物；北去是其报告，后续实际撤军沿下一段正文继续核。')
add('jing_refuses_pursuit','景延广怀疑契丹小校消息有诈，闭营不追',8,'景延广疑',None,[('景延广','怀疑消息有诈，闭营不追')],when='944年三月乙亥消息到后',place='晋军行营',note='疑有诈是景延广判断，不确认小校确是间谍。')
reviews={1:'四守口命令、周引麻答渡河扎营攻北津与乙巳万人进兵分开。上卷颜衎奏报已录，两处可能同事，具体时序待核，不另造第二次蔡俘；辽文本可能承袭。石斌石赟、何建何重建分别留异，麻马家地名不合。麻答从弟转从兄不写亲兄弟。',2:'先禁互援、丙午受围告急、迟报、皇帝救援与三将哭诉分录。旧纪先石公北遇敌、高符后进及古台置酒独补，时间不造钟点。',3:'到口、筑垒渡兵、攻拔、俘斩与溺死、河西退出分开。78将500兵及800马独补，不与数千混成总数；投井渡河俘虏处斩执行明确。李彝殷辛亥奏、壬子任分开；契丹抚慰与败后杀害独录，未具名百姓不造主体。',4:'欲会只是计划，戊午分兵与刘两道诏令、驻乐平不进分开。不据此补刘谋反动机。',5:'居丧期年演奏为追述未知年，出征奏乐概述与庚申请求拒绝分开。冯道由旧纪具名补，非乐为皇帝说法。',6:'棣州冀州地名异说并列，李琼按新史出帝棣州职务与旧明宗石敬瑭关系区分马殷部下。何建重建任官方向及驻地分别留异。',7:'降蜀、请作向导与甲子攻阶分开，请不等已获准带路，攻不等陷。',8:'诈退设伏、张多次报、雨止、十天饥疲、赵建议与三月攻阵分开。东侧新旧战果阶段不同并列；堤兵被误认伏军、李守超反击、三具名军官被斩独补。军械及两军伤亡不伪精确。乙亥小校报告与景疑闭营分开，实际北归待下一段。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=944,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=284,next_year=944,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key='xinwudaishi-009-944-january',note='全年本纪快照，本批仅引用二月戊申马家口战事。'),dict(source_key=mar,note='仅补当前澶州交战、反击与军官处刑；后续北归、泰州、征乡兵与太常丞王绪条另随主线处理。'),dict(source_key=liao,note='与通鉴字句接近，可能据主书编纂，不当独立确定兵数或身份的第三书证。')],coverage='卷284原6—13行连续8正文，二月至三月开篇；下接第9段南汉刘弘昌遇害，944全年尚未完成。',source_issues_review='石斌石赟、何建重建、棣州冀州、马家口马家渡地名异文与东侧战果不同保留。李守超字形原样，未并李守贞；李琼后晋主体与楚将分档。纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],plain_language_review='首次逐项检查标题、人物、角色、关系及事实说明，用完整主语和动作。计划、奏报、命令与执行分开，居丧时长与伤亡数字不强推，原文字形保留。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
