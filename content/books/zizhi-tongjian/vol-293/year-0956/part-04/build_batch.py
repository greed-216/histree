# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 23–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,58))
COMMIT='b209265fbe734c2fa40aacb570f4fd3aa12504d1'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

for key in ['tongjian-293-956-april-yangzhou-liuhe','jiuwudaishi-116-april-yangzhou-liuhe']:
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
main_sources = ['tongjian-293-956-april-yangzhou-liuhe','tongjian-293-956-may-june']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0956-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
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
lines = (ROOT / 'resources/derived/tongjian/293.txt').read_text().splitlines()
for n in range(25, 33):
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
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷293·显德三年（956年四月至六月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0956_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'马在贵':'南唐楚州将领。956年四月在湾头堰被韩令坤击败，《旧五代史》记其所领万余众，未记其本人最后结局。生卒年未载。',
'王环（后蜀凤州节度使）':'镇州真定人，早年以勇力为孟知祥御者，后掌后蜀宿卫。开运末秦凤等地入蜀后，孟昶任其为凤州节度使。955年十一月凤州陷落时被后周军俘获。与914—929年楚水军将领王环分别保存，无同人证据。生卒年未载。','王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
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

def event(code, title, n, quote, actors, when=None, note='', year=956, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='956年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_293_0956_' + code
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
        edge = 'participation_zztj_293_0956_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_293_0956_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','太祖皇帝':'赵匡胤','刘崇':'刘崇（刘知远弟）','李继勋':'李继勋（后周宋初将领）'})
NEW_ALIASES={'马在贵':['馬在貴'],'秦进崇':['秦進崇'],'李继勋（后周宋初将领）':[]}
NEW_DESCRIPTIONS={
'马在贵':'南唐楚州将领。956年四月在湾头堰被韩令坤击败，《旧五代史》记其所领万余众，未记其本人最后结局。生卒年未载。',
'秦进崇':'南唐涟州刺史。956年四月韩令坤奏报在湾头堰击败楚州兵时，被俘获。生卒年未载。',
'李继勋（后周宋初将领）':'大名元城人，后周侍卫步军都指挥使、彰信节度使。956年六月驻寿州城南，被刘仁赡趁无备突击，南寨受损。《宋史》记其早年在郭威帐下任禁军官。与947年后蜀同名左千牛卫上将军缺少同人证据，分别保存。'}
old='jiuwudaishi-116-april-yangzhou-liuhe';may='jiuwudaishi-116-may-956';jun='jiuwudaishi-116-june-south-camp';li='songshi-254-lijixun-identity'
add('zhaokuangyin_marks_caps','赵匡胤在六合战中斫不尽力士卒的皮笠，次日查痕处死数十人',25,'是战也，','由是部兵莫敢不尽死，',[('太祖皇帝','以斫笠作记号，次日检笠后杀不尽力士卒')],when='956年四月六合交战及次日，具体日未载',place='六合周军',description='《通鉴》记赵匡胤假作督战，斫不尽力士卒的皮笠作记号，次日查验有刀痕者数十人并处死。随后部下不敢不拼力作战。不尽死在此为尽力效死，不是全军已经死亡。',note='底本有剑亦字形异常，按斫笠再检叙事解释为痕迹，原文保留；人员名单和精确人数未载。')
add('lijing_orders_yangzhou_recovery','李璟闻扬州失守，命周边各处发兵收复',25,'先是，','命四旁发兵取之。',[('唐主','命各处兵力重新争取扬州')],when='956年二月扬州失守之后的回述，具体发令日未载',place='南唐周边至扬州',note='复取命令不等于此时已经收复扬州，不把回述都定四月己卯。')
add('wantou_victory_report','韩令坤奏报湾头堰击败楚州兵万余，俘秦进崇',25,'己卯，','获涟州刺史秦进崇。',[('韩令坤','奏报湾头堰获胜'),('秦进崇','以涟州刺史身份被俘')],when='956年四月己卯奏报，交战日未单列',place='湾头堰',note='楚州是南唐辖州，非已灭湖南楚国复出军队；败万余不直接等同斩首数。')
sup('wantou_victory_report',25,old,'己卯，韓令坤奏，敗楚州賊將馬在貴萬餘眾於灣頭堰，獲漣州刺史秦進崇。','《旧五代史》同日记湾头堰捷报及秦进崇被俘。','沿同场同人，人数字面保留，不新增未载唐军主将。')
mp=person('马在贵',25,'率楚州军在湾头堰被韩令坤击败','己卯，韓令坤奏，敗楚州賊將馬在貴萬餘眾於灣頭堰，獲漣州刺史秦進崇。',source=old)
me=dict(key='participation_zztj_293_0956_wantou_mazaigui',person_key=mp,event_key=E['wantou_victory_report'],role='据《旧五代史》，领楚州军在湾头堰被击败',status='draft')
B['person_events'].append(me)
claim('person_event',me['key'],'role','马在贵率楚州军在湾头堰被韩令坤击败。',25,'己卯，韓令坤奏，敗楚州賊將馬在貴萬餘眾於灣頭堰，獲漣州刺史秦進崇。','主书未点名楚州将领，旧书补充其名；不把马在贵自动记作被俘或被杀。',source=old)
add('quxi_victory_report','张永德奏报在曲溪堰击败万余泗州兵',25,'张永德奏',None,[('张永德','奏报曲溪堰获胜')],when='956年四月己卯条所附奏报，独立交战日未载',place='曲溪堰',note='与韩令坤湾头堰是不同地点和统帅，不能合成一场；未列斩首人数。')
sup('quxi_victory_report',25,'songshi-255-zhangyongde-quxi','又敗泗州軍千餘於曲溪堰，','《宋史》张永德传也记曲溪堰获胜，但人数记千余。','主书万余与宋传千余数量差异保留；传记未列己卯日，不据详略改主文。',relation='conflicts')
add('xiangxun_huainan_command','柴荣任向训为淮南节度使兼沿江招讨使',26,'丙戌，','兼沿江招讨使。',[('帝','任向训掌淮南与沿江招讨'),('向训','由宣徽南院使获任淮南节度使兼招讨')],when='956年四月丙戌',place='淮南及沿江')
sup('xiangxun_huainan_command',26,old,'丙戌，以宣徽南院使向訓為權淮南節度使，充沿江招討使；','《旧五代史》同日记向训权任淮南节度使、充沿江招讨使。','主书省权字、旧史明记暂任，分别保存；同人不因职名详略再分档。')
add('wokou_bridge_completed','涡口奏报新建浮桥完成',26,'涡口奏','浮梁成。',[],when='956年四月丙戌条所记奏报，竣工日未另列',place='涡口',note='浮梁是浮桥，报告竣工与此前下蔡桥成地点不同。')
add('chairong_haozhou_to_wokou','柴荣由濠州到涡口',26,'丁亥，','如涡口。',[('帝','从濠州转往涡口')],when='956年四月丁亥',place='濠州至涡口')
add('fanzhi_stops_yangzhou_trip','柴荣想亲去扬州，范质等以兵疲粮少哭谏，柴荣止行',26,'帝锐于进取，','泣谏而止。',[('帝','欲继续亲去扬州，听谏后停止'),('范质','以兵疲粮少反对继续东行')],when='956年四月在涡口期间，具体谏止日未载',place='涡口',note='止行明确，不能把欲至扬州建成真正已到扬州事件；其他谏者未具名。')
sup('fanzhi_stops_yangzhou_trip',26,may,'天子駐於渦口，猶欲再幸揚州，宰相範質以師老泣諫，乃班師。','《旧五代史》所引马令《南唐书》也记范质以军队疲惫哭谏。','为旧史引书，非另查马令底本；该书五月返京条注回述，不把谏止强定为五月戊戌当天。')
add('chairong_intends_kill_douyi','柴荣曾因生气欲杀窦仪，范质赶来劝救',26,'帝尝怒翰林学士窦仪，','即起避之。',[('帝','因怒拟杀窦仪，见范质前来而回避'),('窦仪','面临君主拟杀'),('范质','前来劝救窦仪')],year=None,when='柴荣在位期间的回述，具体年日未载',place='后周朝廷，具体地点未载',note='尝为旧事未明时，不强定在956年四月；拟杀不等窦仪已经被处死。')
add('fanzhi_saves_douyi','范质伏地哭谏愿承担宰相责任，柴荣释窦仪',26,'质趋前伏地，',None,[('范质','伏地叩头并劝君主不要枉杀'),('帝','怒意缓解后释放窦仪'),('窦仪','因劝谏得以获释')],year=None,when='柴荣拟杀窦仪回述的同次劝谏，具体年日未载',place='后周朝廷，具体地点未载',note='仪罪不至死为范质谏言，不虚构具体指控罪名和刑律判文。')
relationship('范质','窦仪','救命恩人',26,span(26,'质趋前伏地，'),'范质在柴荣拟杀窦仪时劝止，使窦仪获释，是此次劝救的救命恩人。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='柴荣拟杀窦仪时，范质伏地哭谏使其获释，是窦仪此次脱险的救命恩人。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('liuchong_buried_jiaocheng','北汉将刘崇葬于交城北山，定庙号世祖',27,Q[27]['text'],None,[('刘崇','以北汉神武帝身份身后安葬')],when='956年四月条末所记，安葬具体日未载',place='交城北山',note='神武帝对应既有刘崇（刘知远弟），不是早年萧县同名人物。这里是葬及庙号，不改此前死亡年954955异说，也不推定具体陵址。')
add('zhenhuai_military_district','柴荣将涡口设为镇淮军',28,Q[28]['text'],None,[('帝','在涡口设置镇淮军军额')],when='956年五月壬辰朔',place='涡口')
sup('zhenhuai_military_district',28,may,'五月壬辰朔，以渦口為鎮淮軍。','《旧五代史》同日记涡口设镇淮军。','军额设置与此前新桥竣工为不同事项。')
add('chenhui_nantaijiang_victory','陈诲在南台江击败福州军，俘斩千余',29,'丙申，','俘斩千馀级。',[('陈诲','以南唐永安节度使身份在南台江获胜')],when='956年五月丙申',place='南台江',note='俘斩为俘虏与杀敌的合称，不把千余全写成阵亡；福州军未在此具名主将。')
add('yongan_renamed_zhongyi','李璟将永安军改名忠义军',29,'唐主更命','忠义军。',[('唐主','改军额名号'),('陈诲','所任永安军改称忠义')],when='956年五月南台江捷报后，具体改名日未单列',place='永安军',note='军额改名不自行推定新增州县或迁移驻地。')
relationship('陈诲','陈德诚','父亲',29,'诲，德诚之父也。','陈诲是陈德诚的父亲，后者沿近期募兵及泰州戍守记录同一人。')
add('chongjin_continues_siege','柴荣留李重进等继续围寿州，自涡口北返',30,'戊戌，','自涡口北归，',[('帝','留军围城后北返'),('李重进','以侍卫亲军都指挥使身份留围寿州')],when='956年五月戊戌',place='涡口北归、寿州围军',note='返京不等撤去所有寿州围军，仍围城未破。')
sup('chongjin_continues_siege',30,may,'戊戌，車駕還京，發渦口。','《旧五代史》同日记柴荣离涡口返京。','发为出发，不把返京起日等同抵京日。')
add('chairong_returns_daliang','柴荣由淮南返抵大梁',30,'乙卯，',None,[('帝','返抵大梁')],when='956年五月乙卯',place='大梁')
sup('chairong_returns_daliang',30,may,'乙卯，上至自淮南，','《旧五代史》同日记柴荣从淮南返回。','与戊戌离涡口分阶段，不把两日期互换。')
add('huainan_prisoner_pardon','柴荣赦淮南各州在押者',31,'六月，','赦淮南诸州系囚，',[('帝','赦淮南各州在押囚犯')],when='956年六月壬申',place='淮南诸州')
sup('huainan_prisoner_pardon',31,jun,'壬申，曲赦淮南道諸州見禁罪人，自今年六月十一日已前，凡有違犯，無問輕重，並不窮問。','《旧五代史》详列淮南在押者及本年六月十一日以前犯罪的赦免范围。','特定地区和时限不扩为天下永久免刑，不自行换公历。',relation='adds')
add('huainan_levies_removed','柴荣取消南唐不合理赋役，令地方长官报告不便民事项',31,'除李氏',None,[('帝','停不合理赋役并要求地方官报告')],when='956年六月壬申',place='淮南诸州',note='非理赋役与不便民事项不是全部正常税役都取消。')
sup('huainan_levies_removed',31,jun,'先屬江南之時，應有非理科徭，無名配率，一切停罷雲。','《旧五代史》同记取消江南旧治下不合理科徭、无名摊派。','保留限定词，不作全免税说明。')
add('shouzhou_south_camp_defeat','刘仁赡趁李继勋南营无备出击，杀数百周兵并焚攻具',32,Q[32]['text'],None,[('李继勋','驻寿州城南，营地受突击'),('刘仁赡','从城中出兵，袭击无备周营')],when='956年六月，主书未独立列交战日；《旧五代史》戊子奏报条下记当日攻营',place='寿州城南',description='后周侍卫步军都指挥使、彰信节度使李继勋驻寿州南，刘仁赡见其无备，出兵袭击，杀周兵数百并焚烧攻城器具。李继勋使用后周宋初将领限定名，与后蜀同名人物分开。')
sup('shouzhou_south_camp_defeat',32,jun,'戊子，升贍國軍為濱州。淮南道招討使李重進奏，壽州賊軍攻南寨，王師不利。','《旧五代史》记六月戊子李重进奏报南寨受攻、周军失利。','奏报者为李重进，驻将为李继勋，不合并；旧文随后说是日出城攻营，按本纪戊子记录保留，主书仍未独立列日。')
sup('shouzhou_south_camp_defeat',32,jun,'其攻城之具並為賊所焚，將士死者數百人。','《旧五代史》也记攻具被焚、将士死数百。','双方同类概数不加成两场独立伤亡，原文贼为后周视角称谓，展示明确为南唐军。')
claim('person',people['李继勋（后周宋初将领）'],'description','《宋史》记李继勋为大名元城人，早年在郭威帐下，后任禁军军官及侍卫步军都指挥使。',32,'李繼勳，大名元城人。周祖領鎮，選隸帳下。廣順初，補禁軍列校，累遷至虎捷左廂都指揮使、領永州防禦使。顯德初，遷侍衛步軍都指揮使、領昭武軍節度。歲餘，改領曹州。','以当时禁军军职及曹州彰信任职背景辨别本批人物；与后蜀李继勋缺少衔接证据，不强合。',source=li,relation='adds')

reviews={25:'六合斫笠及次日检痕处死、李璟旧召四方复扬、己卯湾头俘秦及曲溪报捷分开。剑私有字保留、数十不造精名册，尽死为效力非全军已死，楚州为州非湖南楚国。',26:'丙戌任向及涡口新桥成、丁亥移涡、范止扬州亲行、帝尝怒窦与范救两回述事件分开。拟殺与释明确，范救确年未载留null，救命方向有事实依据。',27:'北汉神武帝沿刘崇（刘知远弟），葬与庙号不改旧死年争议，不造刘承钧亲自主持或精陵址。',28:'五月壬辰朔涡口军额与新桥为两项，旧同日印证。',29:'丙申陈诲败福州与俘斩千余合称、后军额改忠义及父陈德诚关系分录，不以所有俘斩当阵亡。',30:'五月戊戌离涡留李军继续围城、乙卯到京分两阶段，北返不等完全撤围。',31:'六月壬申区域赦囚与六月十一日以前时限、取消不合理赋役及报告不便民分开，不扩大天下永久免刑或全部免税。',32:'后周禁军李继勋与蜀同名暂分，李重进是戊子奏报者不是受攻将。数百死与攻具毁坏旧主互证不相加，旧史戊子奏报附是日交战与主未列日并存。'}
assert not (P/'publication.json').exists()
for n in range(25,33):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],next_volume=293,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原30—37行连续八段，从六合战后至六月南营失利，后续未计覆盖。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,33)],source_issues_review='剑亦异字原保、范救窦无确年、北汉葬不改死亡年异说，李继勋后周蜀同名分档，书中奏报与战日区分，纸本及具体异文仍待核。',plain_language_review='首次逐条自查人物、动作、军职和日期说明，假督检痕、拟殺与获释、效死与已死、俘斩与单一阵亡、赋役限定及区域赦免范围分清，原文保持底本。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
