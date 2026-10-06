# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 7–14."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,29))
COMMIT='3cf04308010988e93f2be2b3123fa7653105db77'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-116-january-956','songshi-1-zhao-kuangyin-name','songshi-263-dou-yi-clemency']:
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
main_sources = ['tongjian-292-956-shouzhou-chuzhou']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0956-p007-p014',
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
lines = (ROOT / 'resources/derived/tongjian/292.txt').read_text().splitlines()
for n in range(7, 15):
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
        citation = f'卷292·显德三年（956年正月至二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0956_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
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
    key = 'event_zztj_292_0956_' + code
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
        edge = 'participation_zztj_292_0956_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0956_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','太祖皇帝':'赵匡胤','宣祖皇帝':'赵弘殷','马崇祚':'马崇祚（后周左金吾卫将军）'})
NEW_ALIASES={'何延锡':['何延錫'],'司超':[],'高弼':[],'赵弘殷':['趙弘殷'],'赵普':['趙普'],'马崇祚（后周左金吾卫将军）':[]}
NEW_DESCRIPTIONS={
'何延锡':'南唐都监。956年正月涡口水战中被赵匡胤所率后周军杀死。生年未载。',
'司超':'元城人，后周巡检使。956年二月奏报在盛唐击败南唐兵并俘高弼等。《通鉴》职名中庐、拜、光、黄的拜字可疑，《旧五代史》记庐寿巡检使，字形及职辖详略保留待核。',
'高弼':'南唐都监。956年二月在盛唐战败后被后周军俘获，《旧五代史》同时称其为吉州刺史。生卒年未载。',
'赵弘殷':'后周马军副都指挥使，赵匡胤的父亲，后来由宋朝追尊为宣祖。956年滁州战事后夜间来到城下，赵匡胤以城门属公务为由拒绝夜开，翌晨才准入。生卒年留待对应史料补录。',
'赵普':'蓟人，字则平。早年为刘词幕僚，获刘词遗表推荐；956年滁州攻取后，范质荐任军事判官。赵匡胤与其交谈后赏识他。面对百余名被捕者拟处死，赵普请求先审讯，再决定处罚，使多数人保全性命。',
'马崇祚（后周左金吾卫将军）':'后周左金吾卫将军。956年二月获命主管滁州事务。与946年契丹客省副使、暂掌恒州的同名主体缺少连贯履历证据，暂分档保存。生卒年未载。'}
NEW_DEATH_YEARS={'何延锡':956}
jan='jiuwudaishi-116-january-956';feb='jiuwudaishi-116-february-956';nw='xinwudaishi-49-huangfu-captured';name='songshi-1-zhao-kuangyin-name';son='songshi-1-zhao-father-son';zp='songshi-256-zhaopu-identity';zc='songshi-256-zhaopu-chuzhou';dou='songshi-263-dou-yi-clemency'
add('chairong_yongning_reassurance','柴荣到永宁镇，主张先安抚寿州周边农民，使其安心务业',7,'壬子，','各令安业。”',[('帝','担心军队再临使农民聚城受饥，提出先派人安抚')],when='956年正月壬子',place='永宁镇及寿州周边',note='农民将再入城、可能饥死是柴荣的担忧，主书本句未证明所有人已聚城饿死，也未逐项记使者完成任务。')
add('chongjin_replaces_ligu','柴荣到正阳后，以李重进代李谷统率淮南行营',7,'甲寅，','以谷判寿州行府事。',[('帝','更换行营统帅'),('李重进','任淮南道行营都招讨使'),('李谷','转判寿州行府事务')],when='956年正月甲寅',place='正阳')
sup('chongjin_replaces_ligu',7,jan,'甲寅，車駕至正陽。以侍衛都指揮使李重進為淮南道行營都招討使，命宰臣李穀判壽州行府事。','《旧五代史》同日记柴荣到正阳，以及李重进、李谷职务调整。','李谷不是在此被全部免官，沿主书判寿州行府职务。')
add('chairong_shouzhou_siege','柴荣在淝水北侧设营，命诸军围寿州并迁浮桥到下蔡',7,'丙辰，','徙正阳浮梁于下蔡镇。',[('帝','设营、下令围城及迁浮桥')],when='956年正月丙辰',place='寿州城下、淝水之阳、正阳至下蔡',description='柴荣到寿州城下，在淝水之阳设营，命诸军围城，并安排将正阳浮桥移到下蔡镇。阳为水之北侧，具体营址尚未核实。',note='阳沿史载方位为水之北岸，具体营址坐标未核；标题不另造现代营地。')
sup('chairong_shouzhou_siege',7,jan,'丙辰，至壽州城下，營於州西北淝水之陽，詔移正陽浮橋於下蔡。','《旧五代史》同日记柴荣驻寿州西北淝水之阳，诏移桥至下蔡。','下令迁桥与二月桥成分阶段保存；西北为相对州城方位，不直接标现代坐标。')
add('shouzhou_labor_levy','柴荣征发多州数十万丁夫，参与寿州攻城，昼夜不息',7,'丁巳，','昼夜不息。',[('帝','征发攻城丁夫')],when='956年正月丁巳',place='寿州城下；民夫来自宋、毫、陈、颍、徐、宿、许、蔡等州',note='底本毫疑亳，引用与所列地点原字保留待核；数十万为史载约数，不给各州分配虚构人数。')
add('tang_camps_tushan','南唐万余兵系船淮上，在涂山下设营',7,'唐兵万馀人','涂山之下。',[],when='956年正月涡口战事前，具体设营日未载',place='淮水及涂山下',note='未载此处所有主将姓名，不把何延锡自动写成全军唯一统帅。')
add('wokou_naval_victory','赵匡胤以诱敌伏击在涡口击败南唐兵，杀何延锡并夺船',7,'庚申，',None,[('帝','命赵匡胤进攻南唐军营'),('太祖皇帝','遣百余骑佯退诱敌，伏兵击败南唐军'),('何延锡','以南唐都监身份被杀')],when='956年正月庚申条所记命令及交战；旧史壬戌奏报',place='涡口',description='柴荣命赵匡胤攻击南唐军。赵匡胤派百余骑逼近营地后假装逃走，以伏兵拦击，南唐兵在涡口败退，都监何延锡等被杀，战舰五十余艘被夺。太祖皇帝是后来的宋朝称号，赵匡胤当时仍为后周将领。')
sup('wokou_naval_victory',7,jan,'壬戌，今上奏，破淮賊萬餘眾於渦口，斬偽兵馬都監何延錫等，獲戰船五十艘。','《旧五代史》记壬戌赵匡胤奏报涡口获胜、斩何延锡等、获五十艘船。','今上指该书编纂时宋太祖，壬戌是奏报日；五十与五十余、主书庚申条交战层次分别保留，不造两场涡口战役。')

add('wangkui_south_command','柴荣命王逵为南面行营都统，进攻南唐鄂州',8,'诏以','使攻唐之鄂州。',[('帝','安排湖南兵参与攻南唐'),('王逵','以武平节度使兼中书令身份获任南面行营都统')],when='956年正月条所记，具体诏日未载',place='湖南至鄂州',note='命攻与实际获胜分开；王逵沿既有王进逵同人主体。')
add('pan_hosts_wangkui','王逵率兵过岳州，潘叔嗣备宴犒劳',8,'逵引兵','奉事甚谨。',[('王逵','率兵过岳州'),('潘叔嗣','以岳州团练使身份厚备宴犒')],when='956年王逵进兵途中，具体日未载',place='岳州',note='宴犒是史载招待行动，不给未载金额和物资数量。')
add('wangkui_entourage_accuses_pan','王逵左右索求不满，指控潘叔嗣谋反，王逵发怒',8,'逵左右',None,[('王逵','听取谋反指控后显露怒意'),('潘叔嗣','被指控后惧怕不安')],when='956年王逵途经岳州时',place='岳州',description='《通鉴》记王逵左右索取无厌，未获满足者向王逵指控潘叔嗣谋反。王逵怒形于色，潘叔嗣因此惧怕不安。谋反在这里是指控，不写成已经核实的犯罪，也不提前录入后段潘叔嗣的行动。')
add('hejingzhu_defense_choice','何敬洙拒绝将民众迁入城内，整地备战，获李璟认可',9,Q[9]['text'],None,[('唐主','原命何敬洙迁民入城固守，后来认可其备战回应'),('何敬洙','不按迁民命令办，清地备战并表示与兵民共存亡')],when='956年正月湖南兵将至时，具体日未载',place='南唐武昌',note='俱死于此是何敬洙的决心表达，不是百姓士兵已全部死亡。')

add('xiacai_bridge_completed','下蔡浮桥建成，柴荣亲自察看',10,Q[10]['text'],None,[('上','亲自察看建成的浮桥')],when='956年二月丙寅',place='下蔡',note='与正月丙辰迁桥命令分开，本句才明确桥成。')
add('sheng tang_victory_report'.replace(' ',''),'司超奏报在盛唐击败三千余南唐兵，俘高弼并获船',11,'戊辰，','获战舰四十馀艘。',[('司超','以巡检使身份奏报盛唐获胜'),('高弼','以南唐都监身份被俘')],when='956年二月戊辰奏报，交战日未单列',place='盛唐',description='元城人司超奏报在盛唐击败南唐兵三千余人，俘都监高弼等，获战舰四十余艘。《通鉴》巡检辖区文字中的拜字可疑，《旧五代史》称庐寿巡检使，保留差异。')
sup('shengtang_victory_report',11,feb,'戊辰，廬壽巡檢使司超奏，破淮賊三千於盛唐，獲都監偽吉州刺史高弼以獻。詔釋之。','《旧五代史》同日记司超盛唐获胜，称高弼为都监、吉州刺史，并记柴荣释放高弼。','三千与三千余、巡检职辖详略保留；只说释放不推定高弼已获新官。',relation='adds')
add('gaobi_released','柴荣释放盛唐战中被俘的高弼',11,'獲都監偽吉州刺史高弼以獻。','詔釋之。',[('帝','释放被俘的高弼'),('高弼','被献俘后获释放')],source=feb,when='956年二月戊辰奏报条所附处置，具体释放日未另载',place='后周行在',note='独立保留旧史明确执行的释放，不把主书没写释放解释成仍在监禁。')
add('qingliu_attack','柴荣命赵匡胤急袭清流关，赵军从山后进击皇甫晖所部',11,'上命太祖皇帝','太祖皇帝引兵出山后；',[('上','命赵匡胤倍道袭清流关'),('太祖皇帝','从山后出兵'),('皇甫晖','列阵山下，与前锋交战')],when='956年二月戊辰奏报以后所叙，主书未单列战日；旧史壬申奏报',place='清流关',note='倍道为加快进军，不计算具体速度；戊辰是前场盛唐奏报日，不强定清流战同日。')
add('chuzhou_pursuit_capture','赵匡胤追入滁州，击伤并俘皇甫晖、姚凤，攻取城池',11,'晖等大惊，','遂克滁州。',[('太祖皇帝','涉水追击，冲阵伤皇甫晖并俘两将'),('皇甫晖','退入滁州后欲列阵交战，被击伤俘获'),('姚凤','在滁州被俘')],when='956年二月清流关失利之后，具体夺城日未单列',place='清流关至滁州',description='《通鉴》记皇甫晖等退入滁州，想断桥固守；赵匡胤率兵涉水追到城下，答应皇甫晖列阵请求，随后突入阵中击伤其头部，将皇甫晖、姚凤俘获并攻取滁州。伤者此时仍被生俘，未提前记为阵亡。')
sup('chuzhou_pursuit_capture',11,feb,'壬申，今上奏，破淮賊萬五千人於清流山，乘勝攻下滁州，擒偽命江州節度使、充行營應援使皇甫暉，常州團練使、充應援都監姚鳳以獻。','《旧五代史》记二月壬申赵匡胤奏报清流山获胜及夺取滁州、俘皇甫晖姚凤。','壬申为奏报日，主书未列夺城日；万五千为击败规模，不自动改为斩首数。')
sup('chuzhou_pursuit_capture',11,feb,'太祖以周師數千與暉遇於清流關隘路，周師大敗，暉整全師入憩滁州城下，會翊日再出。','旧史所引王铚《默记》另记赵匡胤军先在清流关失利，皇甫晖回滁州休整。','这与主书山后进击的叙次不同，标为引书异说，未把先败故事当作已由所有书共同确证。',relation='conflicts')
sup('chuzhou_pursuit_capture',11,feb,'夜從小徑行，三軍跨馬浮西澗以迫城，暉果不為備。奪門以入，','《默记》引文随后记周军由小径夜行、渡西涧迫城夺门。','不同取城过程分别保存，不把同场城池陷落重复建成第二次战役；该引文里的赵学究未直接等同赵普。',relation='conflicts')
sup('chuzhou_pursuit_capture',11,nw,'周師征淮，景以暉為北面行營應援使，屯清流關，為周師所敗，并其都監姚鳳皆被擒。','《新五代史》也记皇甫晖屯清流关，被周军击败，与姚凤一同被俘。','传记后文见柴荣与去世属后段，本次只覆盖败俘，不提前处理死亡。')
add('zhaohongyin_night_gate','赵弘殷夜抵滁州，赵匡胤以城门属公务拒绝夜开',11,'后数日，',None,[('宣祖皇帝','以马军副都指挥使身份夜抵滁州，请求开门'),('太祖皇帝','以城门属于公务为由不肯夜开，翌晨才准入')],when='956年二月滁州攻取后数日，具体日未载',place='滁州城门',note='宣祖是宋朝追尊的赵弘殷，太祖为赵匡胤；两人在当时均未以皇帝身份统治。')
claim('person',people['赵弘殷'],'description','《宋史》太祖本纪明确弘殷为后来追尊的宣祖。',11,'敬生弘殷，是為宣祖。','此句位于赵匡胤祖系同节，确认弘殷与宣祖称号，不把敬的父子关系错接到匡胤。',source=name,relation='corroborates')
relationship('赵弘殷','赵匡胤','父亲',11,'太祖，宣祖仲子也，','《宋史》同节先明弘殷为宣祖，再记太祖为宣祖次子，结合主书父子对话确认方向：赵弘殷是赵匡胤的父亲。',source=son)

add('douyi_registers_chuzhou_treasury','柴荣派窦仪登记滁州府库财物',12,'上遣翰林学士','籍滁州帑藏，',[('上','派窦仪登记府库'),('窦仪','以翰林学士身份登记滁州财物')],when='956年二月滁州攻取之后，具体日未载',place='滁州府库')
add('douyi_refuses_unauthorized_silk','窦仪拒绝赵匡胤属吏无诏取绢，赵匡胤因此尊重他',12,'太祖皇帝遣亲吏','太祖皇帝由是重仪。',[('太祖皇帝','派亲吏取库绢，后因窦仪坚持规定而敬重他'),('窦仪','认为已登记为公物须有诏才能取')],when='956年二月滁州府库登记之后',place='滁州府库',note='初克城时可给军是窦仪解释前后制度边界，不据此新增已经取空全库的事件。')
sup('douyi_refuses_unauthorized_silk',12,dou,'顯德中，太祖克滁州，世宗遣儀籍其府庫。太祖復令親吏取藏中絹給麾下，','《宋史》也记柴荣派窦仪登记滁州府库，赵匡胤又遣亲吏取绢给部下。','使用已发布的同一原文快照复用source，不另造重复出处。')
sup('douyi_refuses_unauthorized_silk',12,dou,'今既著籍，乃公帑物也，非詔不可取。','《宋史》窦仪传同记登记后属于公款财物，没有诏命不可擅取。','后文宋初相位、人际评价暂不录为956年已发生。')
add('machongzuo_chuzhou','柴荣任左金吾卫将军马崇祚主管滁州',12,'诏左金吾卫将军',None,[('上','命马崇祚主管滁州'),('马崇祚','以左金吾卫将军身份知滁州')],when='956年二月滁州攻取之后，具体诏日未载',place='滁州',note='与946年契丹客省副使同名者缺少连续履历证据，暂新增后周官职限定名，不按同名直接复用。')

add('liuci_recommends_zhaopu','刘词在遗表中推荐幕僚赵普',13,'初，永兴节度使刘词','赵普有才可用。',[('刘词','以遗表推荐幕僚'),('赵普','以刘词幕僚身份被推荐')],year=None,when='刘词去世前的遗表回述，具体作表年日未单列',place='永兴军至后周朝廷',note='本段初为旧事，不强定956年二月；刘词卒报在既有955年末旧本纪，但作表本身未列日。')
relationship('刘词','赵普','推荐人',13,span(13,'初，永兴节度使刘词','赵普有才可用。'),'此关系限定刘词遗表举荐赵普，不写终身政治盟友。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='刘词在遗表中举荐赵普时，是赵普的推荐人。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('fanzhi_recommends_zhaopu','滁州攻取后，范质荐赵普为军事判官',13,'会滁州平，','范质荐普为滁州军事判官，',[('范质','推荐赵普出任滁州军事判官'),('赵普','被荐任滁州军事判官')],when='956年二月滁州平定之后',place='滁州及后周朝廷')
relationship('范质','赵普','推荐人',13,span(13,'会滁州平，','范质荐普为滁州军事判官，'),'此关系限定956年滁州军事判官的荐任，不据此推为其他年份所有职务均由范质举荐。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='956年滁州军事判官荐任中，范质是赵普的推荐人。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
sup('fanzhi_recommends_zhaopu',13,zc,'周顯德初，永興軍節度劉詞辟為從事，詞卒，遺表薦普於朝。世宗用兵淮上，太祖拔滁州，宰相范質奏普為軍事判官。','《宋史》同记刘词遗表举荐，范质在滁州攻取后奏任赵普为军事判官。','两次推荐阶段分开，后文淮南平后调职未提前录。')
claim('person',people['赵普'],'origin','赵普为蓟人。',13,'蓟人赵普','依主书籍贯，不给现代出生地点坐标。')
claim('person',people['赵普'],'description','《宋史》记赵普字则平，为幽州蓟人。',13,'趙普，字則平，幽州薊人。','只取身份及籍贯；同段父亲迁徙、婚姻另待对应材料延伸，不造当前年事件。',source=zp,relation='corroborates')
add('zhaokuangyin_values_zhaopu','赵匡胤与赵普交谈后对他产生好感',13,'太祖皇帝与语，','悦之。',[('太祖皇帝','与赵普交谈后赏识他'),('赵普','与赵匡胤交谈')],when='956年二月滁州判官荐任之后，具体日未载',place='滁州',note='谈话认可不等于本段已发生后来的谋划拥立。')
add('zhaopu_requests_interrogation','赵普请求先审讯拟处死的百余被捕者，使多数人活命',13,'时获盗百馀人，',None,[('赵普','请求先讯问再决刑，保全多数人性命'),('太祖皇帝','因此更加赞赏赵普')],when='956年二月滁州平定之后，具体日未载',place='滁州',description='《通鉴》记百余名被捕为盗者原拟处死，赵普请求先审讯再决定刑罚，约七八成得以活命，赵匡胤更加赏识他。人数与比例都是史载约数，不换算成精确获救人数，也不把所有被捕者都写成已定罪。')
sup('zhaopu_requests_interrogation',13,zc,'時獲盜百餘，當棄市，普疑有無辜者，啟太祖訊鞫之，獲全活者眾。','《宋史》也记赵普怀疑其中有无辜者，请赵匡胤审讯，最终保全许多人。','宋传未给七八比例，两书人数和结果详略分别保留。')
add('zhaokuangyin_bright_armor_response','赵匡胤回应战场装束显眼的提醒，表示有意让敌人识认',14,Q[14]['text'],None,[('太祖皇帝','在有人指出装束易被敌人识认时，表示正希望如此')],year=None,when='赵匡胤从军期间的习惯及对话回述，具体年份和日期未载',place='战场，具体地点未载',description='《通鉴》概述赵匡胤威名渐盛，临阵时常以繁缨装饰马匹、穿戴鲜明铠甲。有人提醒容易被敌军识认，他回答自己正希望敌人认得。这是习惯和对话的概述，不强定为956年二月某次具体交战。')

reviews={7:'永宁讲话里的饿殍为忧虑，甲寅换帅、丙辰围城迁桥、丁巳征夫、涂山设营与涡口命击交战分别处理。淝水之阳按北侧，毫疑亳保留；庚申命战与壬戌奏报区分。',8:'湖南任统帅、岳州宴犒、左右索求及谋反指控分阶段；谋叛为谗言，不记作已确认叛乱，未来潘叔嗣行动不提前。',9:'李璟命迁民、何敬洙反对及备战表态、君主认可分别说明，俱死是决心非实际全体死亡。',10:'丙寅桥成及柴荣察看独立于此前迁桥命令。',11:'盛唐奏报、旧高弼获释、清流山后进兵、滁州追击伤俘与旧引默记先败后胜异说并列；壬申奏报非强定战日。宣祖赵弘殷由宋本纪祖系识别，宋父子记载与主对话明确方向；夜门后数日不推精确日。',12:'府库登记、拒绝无诏取绢及认可、命知滁州分开，旧宋同快照复用。马崇祚契丹与后周同名无连续履历，新增限定名待核。',13:'遗表荐、范质荐任、交谈认可、先审救活分开，父子与推荐关系各有引文，推荐阶段限定。赵普七八成不换精确人数，旧事无确日不强955956。',14:'临阵习惯与回应为无确时概述，留year null，不创建虚构某日披甲战役。'}
assert not (P/'publication.json').exists()
for n in range(7,15):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(7,15)],next_paragraph=Q[15]['id'],next_volume=292,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原80—87行连续八段，从寿州围攻至赵匡胤装束对话；未来献皇甫晖等段未计覆盖。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(7,15)],source_issues_review='庚申命战与壬戌涡口奏报、清流戊辰后叙与壬申奏报分清；旧引默记先败后胜异说保留。庐拜职辖及毫字保留待核。马崇祚分档，宋宣祖身份及父子方向由同节祖系回查。',plain_language_review='首次逐条自查主语、称号、角色、事件和时间解释，父亲与推荐方向明示；无确年旧事留null，诏令与桥成、伤俘与死亡、谗言与事实、人数约数与精数分清，原文不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
