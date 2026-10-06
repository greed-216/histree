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
COMMIT='716a3d9ea101493ffb96bbdc98041c65d71f2fd6'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

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
main_sources = ['tongjian-293-956-march-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0956-p001-p008',
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
        citation = f'卷293·显德三年（956年三月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0956_01_{len(B["claims"])+1:04d}'
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','太祖皇帝':'赵匡胤','南汉主':'刘弘熙','冯延己':'冯延巳','何超':'何超（后周光州招安巡检使）','李福':'李福（南唐蕲州将）'})
NEW_ALIASES={'张琼':['張瓊'],'王崇质':['王崇質'],'龚澄枢':['龔澄樞'],'何超（后周光州招安巡检使）':[],'张绍':['張紹'],'张承翰':['張承翰'],'郭令图':['郭令圖'],'李福（南唐蕲州将）':[],'王承巂':[],'李彦頵':['李彥頵'],'王审琦':['王審琦']}
NEW_DESCRIPTIONS={
'张琼':'馆陶人，赵匡胤麾下牙将。956年攻寿春时，赵匡胤乘皮船入壕遭弩射，张琼以身体遮护，被射中腿部，重伤后恢复。《宋史》也记大名馆陶籍贯及护救经过，未把死而复苏当作当年永久死亡。',
'王崇质':'南唐礼部尚书。956年三月奉李璟命与司空孙晟一起向后周奉表求和。生卒年未载。',
'龚澄枢':'番禺人，南汉内给事。956年林延遇病重时推荐其代任，刘弘熙随后任其知承宣院及内侍省。生卒年及后续权势经历待按年代补录。',
'何超（后周光州招安巡检使）':'后周光、舒、黄招安巡检使、行光州刺史。956年三月率安随申蔡兵攻光州，奏报张承翰带城归降。与943年后晋左飞龙使、暂掌单州的同名何超暂无完整连续履历证据，暂分档保存。',
'张绍':'南唐光州刺史。956年三月周军来攻时放弃城池逃走。生卒年未载。',
'张承翰':'南唐光州都监。956年三月带光州归降后周，《旧五代史》还记随后授集州刺史。生卒年未载。',
'郭令图':'后周行舒州刺史。956年三月攻取舒州后，被舒州人驱逐；王审琦夜袭恢复后，郭令图得回城。生卒年未载。',
'李福（南唐蕲州将）':'南唐蕲州将领。956年三月杀死知州王承巂，带州归降后周。与904年条所见同名李福暂无同人证据，暂分档保存。',
'王承巂':'南唐蕲州知州。956年三月被当地将领李福杀死，随后蕲州归降后周。生年未载。',
'李彦頵':'后周彰武军留后。956年其治下民众及羌胡因其侵刻起事，柴荣召其回朝；《旧五代史》称延州留后，补记其与都监阎绾镇压，并杀酋帅十人。生卒年未载。',
'王审琦':'洛阳人，后周铁骑都指挥使，字仲宝。956年舒州人逐郭令图后，选轻骑夜袭恢复舒州。《宋史》记其先世辽西、后迁洛阳及早年在郭威军中履历，生卒年待后续补录。'}
NEW_DEATH_YEARS={'王承巂':956}
old='jiuwudaishi-116-march-956';zi='songshi-259-zhangqiong-identity';zs='songshi-259-zhangqiong-shield';wi='songshi-250-wangshenqi-identity';ws='songshi-250-wangshenqi-shuzhou'
add('chairong_carries_siege_stone','柴荣察看水寨，在淝桥取石运往寨中，命随从各携一石',1,Q[1]['text'],None,[('上','亲自携石并要求随从协助运石')],when='956年三月甲午朔',place='淝桥至寿州水寨',note='砲在此为攻城投石器，不写成近代火炮；取一石是石块，不换成粮食石或固定重量。')
add('zhaokuangyin_boat_under_fire','赵匡胤乘皮船进入寿春壕中，遭城上连弩射击',2,'太祖皇帝乘皮船','矢大如屋椽。',[('太祖皇帝','乘皮船入壕受到城上弩射')],when='956年三月寿春围攻期间，具体日未载',place='寿春城壕',note='矢如屋椽为史载形容，不据此制作未经考证的精确武器尺寸。')
add('zhangqiong_shields_zhao','张琼以身护赵匡胤，被弩箭射中腿部，重伤后苏醒',2,'牙将馆陶张琼','死而复苏。',[('张琼','以身体遮护赵匡胤，腿部中箭后苏醒'),('太祖皇帝','获张琼身体遮护')],when='956年三月寿春壕中受射时，具体日未载',place='寿春城壕',note='死而复苏作为重伤后恢复的叙述保存，不填写张琼死亡年956；两书后续仍有其活动。')
sup('zhangqiong_shields_zhao',2,zs,'瓊亟以身蔽太祖，矢中瓊股，死而復蘇。','《宋史》同记张琼遮护赵匡胤、腿部中箭后苏醒。','股髀为相近腿部称谓，摘录保留底本，不当作史书确认永久死亡又复活。')
add('zhangqiong_arrow_removed','张琼饮酒后让人破骨取出箭镞，史书称其镇定',2,'镞着骨',None,[('张琼','箭镞卡骨，饮酒后让人取出')],when='956年寿春受伤之后，具体处置日未载',place='寿春战场附近，具体地点未载',description='《通鉴》记箭镞卡在骨中不能拔出，张琼饮酒后让人破骨取出，流血数升而神色自若。这是史书中的治疗经过及勇毅描写，原书的计量和效果不当作现代医学测量。')
sup('zhangqiong_arrow_removed',2,zs,'鏃著髀骨，堅不可拔。瓊索杯酒滿飲，破骨出之，血流數升，神色自若。太祖壯之。','《宋史》同记饮酒取箭及流血镇定，并记赵匡胤赞赏其勇。','后文宋初任职不提前归入956年，具体酒量、失血量不换现代单位。')
claim('person',people['张琼'],'origin','《宋史》记张琼为大名馆陶人，早年善射且在赵匡胤帐下。',2,'張瓊，大名館陶人。世為牙中軍。瓊少有勇力，善射，隸太祖帳下。','只取籍贯和当时所属，传记前后其他战役及宋初经历待对应年段。',source=zi,relation='adds')

add('sunsheng_wangchongzhi_mission','李璟升孙晟为司空，派他与王崇质奉表求和并献财物',3,'唐主复以','罗绮二千匹。',[('唐主','升孙晟并派两使奉表'),('孙晟','由右仆射转司空，奉表出使'),('王崇质','以礼部尚书身份共同出使')],when='956年三月奉表出使，具体派遣日未单列',place='南唐至后周行在',description='李璟任孙晟为司空，与礼部尚书王崇质共同奉表，表示愿仿效吴越、湖南奉后周正朔、守土为外臣，请求停止征伐；献金千两、银十万两、罗绮二千匹。奉表表达臣服愿望，不是双方已经缔结和约。')
sup('sunsheng_wangchongzhi_mission',3,old,'丙午，江南國主李景遣其臣偽司空孫晟、偽禮部尚書王崇質等奉表來上，仍進金一千兩、銀十萬兩、羅綺二千匹，','《旧五代史》记三月丙午孙晟、王崇质奉表来上，并列相同礼物数量。','丙午是到行在的记录，主书该段先说派遣、后第9段才列丙午到达，不能把派遣日强定为到达日。')
add('sunsheng_declares_duty','孙晟对冯延巳说出使本当由左相承担，但自己不能负先帝',3,'晟谓冯延己','则负先帝。”',[('孙晟','向冯延巳表达出使责任'),('冯延巳','听取孙晟关于职责的说法')],when='956年三月孙晟出使之前，具体日未载',place='南唐朝廷',note='冯延己沿既有冯延巳同人，负先帝为孙晟的忠诚表态，不据此确认冯延巳已正式被任命使者。')
add('sunsheng_warns_wangchongzhi','孙晟途中对王崇质说自己决不负永陵，并劝其自谋',3,'既行，',None,[('孙晟','途中夜间表达忠于先帝的决意'),('王崇质','听取孙晟关于自身处境的提醒')],when='956年三月出使途中，具体夜晚未载',place='出使途中，具体地点未载',note='知不免是孙晟对命运的预感，不在此提前导入本年后来的死亡；百口为形容家口众多，不建立精确家族人口。')

claim('person',person('林延遇',4,'南汉甘泉宫使，本段述其受君主倚信及谋害诸王',span(4,'南汉甘泉宫使林延遇','皆延遇之谋也。')),'evaluation','《通鉴》称林延遇阴险多谋，受刘弘熙倚信，并参与谋害南汉诸王。',4,span(4,'南汉甘泉宫使林延遇','皆延遇之谋也。'),'沿935年入南汉、950掌政及954赐毒等已发布主体；诸弟被害为旧事及史家概述，不造本年重复杀王事件。')
add('linyanyu_dies','林延遇去世，史书记南汉民众相贺',4,'乙未卒，','国人相贺。',[('林延遇','以甘泉宫使身份去世')],when='956年三月乙未',place='南汉',note='国人相贺为史家的群体反应概述，不当作每名居民都被逐一调查。')
claim('person',people['林延遇'],'death_year','林延遇于956年三月乙未去世。',4,'乙未卒，国人相贺。','年月按本段接三月甲午朔的编年上下文，身份承接林延遇。')
add('lin_recommends_gong','林延遇病重时推荐龚澄枢接替自己',4,'延遇病甚，','荐内给事龚澄枢自代，',[('林延遇','病重时举荐接替人选'),('龚澄枢','以内给事身份被推荐')],when='956年三月乙未林延遇死前，具体推荐日未载',place='南汉宫廷')
relationship('林延遇','龚澄枢','推荐人',4,span(4,'延遇病甚，','荐内给事龚澄枢自代，'),'此关系限定林延遇病重时推荐龚澄枢接替事务。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='林延遇病重时推荐龚澄枢接替自己，是此次任用的推荐人。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('gong_privy_appointment','刘弘熙在推荐当天任龚澄枢掌承宣院及内侍省',4,'南汉主即日','及内侍省。',[('南汉主','采纳推荐，任龚澄枢掌两处宫内事务'),('龚澄枢','获任知承宣院及内侍省')],when='956年三月林延遇举荐当日，具体日未单列',place='南汉宫廷',note='即日承接推荐，不自动套乙未死日；当前南汉君主沿刘弘熙即刘晟，不另建人物。')
claim('person',people['龚澄枢'],'origin','龚澄枢为番禺人。',4,'澄枢，番禺人也。','史载籍贯保留，不赋出生坐标。')

add('hechao_guangzhou_campaign','何超率安、随、申、蔡四州数万兵攻光州',5,'光、舒、黄','四州兵数万攻光州。',[('何超','以招安巡检使、行光州刺史身份攻城')],when='956年三月丙申奏报以前，实际进兵日未载',place='安、随、申、蔡至光州',note='后周巡检何超与943同名官暂无连续履历证据，暂分限定名；数万为四州合计，不分成每州数万。')
add('guangzhou_surrender_report','何超奏报张绍弃城、张承翰带光州归降',5,'丙申，',None,[('何超','奏报光州归降'),('张绍','以南唐刺史身份弃城走'),('张承翰','以都监身份带城归降')],when='956年三月丙申奏报，弃城归降日未另列',place='光州',note='此光州不是广州；主书刺史弃城与都监降城为不同人的动作。')
sup('guangzhou_surrender_report',5,old,'三月丙申，行光州刺史何超奏，光州偽命都監張承翰以城歸順，尋授承翰集州刺史。','《旧五代史》同日记光州归顺，并补记张承翰随后授集州刺史。','寻授没有独立日，不能强定丙申同日已经到集州。',relation='adds')
add('zhangchenghan_jizhou_appointment','张承翰归降后获任集州刺史',5,'尋授承翰','集州刺史。',[('张承翰','归降后获授集州刺史')],source=old,when='956年三月光州归降之后不久，具体日未载',place='后周朝廷及集州',note='只录授职，史书未说已抵任；未给现代集州位置。')

add('guol ingtu_captures_shuzhou'.replace(' ',''),'郭令图攻取舒州',6,'丁酉，','郭令图拔舒州。',[('郭令图','以行舒州刺史身份攻取城池')],when='956年三月丁酉',place='舒州')
sup('guolingtu_captures_shuzhou',6,ws,'詔以郭令圖領刺史，命審琦及司超以精騎攻其城，一夕拔之，擒其刺史，獲鎧仗軍儲數十萬計。','《宋史》王审琦传补记任郭令图为刺史，并命王审琦、司超率精骑攻城，夜间取城。','这是一场第一次夺城的补证，随后郭被逐、王复城为另一阶段；器储数十万为原文概数，不造单位。',relation='adds')
add('lifu_kills_wangchengxi','李福杀蕲州知州王承巂，带州归降后周',6,'唐蕲州将李福','举州来降。',[('李福','杀知州并带蕲州归降'),('王承巂','以蕲州知州身份被杀')],when='956年三月丁酉条所附，独立杀降日未载',place='蕲州',note='李福与904年裸名人物无同人证据，暂分档；巂字保留，不靠繁简转换猜替名。')
add('qicangzhen_huangzhou_order','柴荣派齐藏珍进攻黄州',6,'遣六宅使','攻黄州。',[('上','派出攻黄州部队'),('齐藏珍','以六宅使身份受命进攻')],when='956年三月丁酉条所附，具体出军日未载',place='黄州',note='派遣不等于本段已经攻下黄州。')
add('liyanjun_revolt_recall','李彦頵治下民众及羌胡起事攻击，柴荣召他回朝',6,'彰武留后',None,[('李彦頵','因治下起事遭攻击，被召回朝'),('上','召李彦頵回朝')],when='956年三月条所记，起事和召还具体日未载',place='彰武军延州至后周朝廷',description='《通鉴》称彰武留后李彦頵贪虐，治下民众及羌胡起事攻击他，柴荣将他召还。旧史称延州留后，记民众怨其侵刻，又补镇压经过；当地冲突与朝廷召还不能写成同日全部完成。')
sup('liyanjun_revolt_recall',6,old,'延州留後李彥頵奏，蕃眾與部民為亂，尋與兵司都監閻綰掩殺，獲其酋帥高鬧兒等十人，磔於市。','《旧五代史》还记李彦頵奏报起事，并与都监阎绾镇压，俘获高闹儿等十名首领后处死。','延州与彰武为地名军额称法；旧史在庚戌条后附记奏报，未独立列镇压日，不能把主书起事或召还全定庚戌。',relation='adds')

add('shu_captives_enrolled','秦凤平定后，柴荣赦免被俘蜀兵，编入军籍参加淮南征战',7,'秦、凤之平也，','从征淮南，',[('上','赦俘后编军并使从征')],year=None,when='955年秦凤平定之后至956年淮南征战期间的回述，具体编入日未载',place='秦凤至淮南',note='与955年允许俘虏自选去留待遇分开，这里明确部分已被编军；不补未载姓名和编军总数。')
add('former_shu_soldiers_flee_tang','编入后周军的原后蜀俘兵逃往南唐',7,'复亡降于唐。',None,[],when='956年三月癸卯送回之前，具体逃离日未载',place='淮南战区至南唐',note='复亡降指离开周军投南唐，原句不是士兵死亡；最后送回150人不等原编军全体数。')
add('lijing_returns_150_soldiers','李璟将一百五十名逃来的原蜀兵送回后周',7,'癸卯，','唐主表献百五十人；',[('唐主','以表将一百五十人送回')],when='956年三月癸卯',place='南唐至后周行在')
sup('lijing_returns_150_soldiers',7,old,'江南國主李景表送先隔過朝廷兵士一百五十人至行在。其軍即蜀軍也，','《旧五代史》也记李璟送一百五十人到行在，明确他们原为蜀兵。','来源身份印证，不把所有南唐俘虏或全体蜀兵扩大为这一百五十人。')
add('chairong_executes_returned_soldiers','柴荣下令处死被送回的一百五十名原蜀兵',7,'上悉命斩之。',None,[('上','命处死送回者')],when='956年三月癸卯送回之后，具体执行日未另列',place='后周行在',note='主书命令与旧史尽戮执行独立补证，未从命斩推给未载的行刑将领。')
sup('chairong_executes_returned_soldiers',7,old,'帝怒其奔竄，盡戮之。','《旧五代史》明确记柴荣因士兵逃走而发怒，将送回者全部杀死。','原文帝是世宗柴荣，执行已明；不把主书没写现场细节误作未执行。',relation='adds')

add('shuzhou_people_exp el_guo'.replace(' ',''),'舒州人驱逐郭令图',8,'舒州人逐','郭令图，',[('郭令图','在舒州任职时被当地人逐出')],when='956年三月第一次攻取舒州以后，具体日未载',place='舒州')
add('wangshenqi_recovers_shuzhou','王审琦率轻骑夜袭舒州，再次取城，使郭令图得以返回',8,'铁骑都指挥使',None,[('王审琦','选轻骑夜袭并恢复舒州'),('郭令图','舒州恢复后得以返回')],when='956年三月郭令图被逐之后，具体夜袭日未载',place='舒州',note='王审琦为洛阳人，首次夺城与被逐后的恢复分别保存，不合成同一夜。')
sup('wangshenqi_recovers_shuzhou',8,ws,'令圖既入城，審琦等遂救黃州，數日，令圖為舒人所逐。審琦選輕騎銜枚夜發，信宿至城下，大敗舒人，令圖得復還治所。','《宋史》补记王审琦等先援黄州，得知郭令图被逐后轻骑夜行，再恢复城池和任所。','数日与信宿沿原叙事相对时间，不换算确切日期；大败舒人不虚增未载斩首数。',relation='adds')
claim('person',people['王审琦'],'origin','《宋史》记王审琦字仲宝，先世辽西，后迁居洛阳。',8,'王審琦，字仲寶，其先遼西人，後徙家洛陽。','主书记洛阳与祖籍迁居叙述不冲突，不将祖籍当确切出生地点。',source=wi,relation='adds')

reviews={1:'三月甲午朔视寨取石为实际携石，砲为投石器，石块不作粮食量。',2:'皮船受弩、张琼护救腿伤恢复及饮酒取镞分开，死而复苏不登记永久死亡，血升和矢如椽为史载描写。宋身份、籍贯与动作独立出处，不提前宋初任职。',3:'孙晟升司空与两使奉表、献财、对冯延巳职责表态和途中对王崇质决意分开。丙午在后第9段到达，不能作最初派遣日；知不免为预感不提前死。',4:'林延遇过往谋王为评价追述，乙未死亡、病重推荐与当日龚任职分开，推荐即日非强乙未，南汉主沿刘弘熙。',5:'何超身份与943同名未证连贯分档。四州兵数万合计；丙申为奏报，张绍走与张承翰降分开，旧后授集州未给到任日。',6:'丁酉郭拔舒、李福杀蕲知州并降、齐藏珍攻黄令、延州起事与李彦頵召还分开。李福早年同名不合；旧镇压与杀十首领保留，附奏报与执行日不合。宋首次攻舒补证不混后恢复。',7:'原蜀俘赦编、从征逃唐、癸卯送回150及命斩和旧尽戮执行完整处理；不把复亡译死亡，不扩大为全部蜀兵，年月相对范围保留。',8:'舒人逐郭与王夜袭复城分开，宋先援黄州再复城及相对时长保留。王审琦新建身份、字和籍贯双来源，未知战果人数不补。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=293,next_year=956,supplements=supplements,excluded_non_body=[],coverage='卷293原6—13行连续八段，接卷292同年；检索快照卷号题名年首为结构，不计史事。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],source_issues_review='何超、李福同名待核限定分档；巂頵等字保留。宋第一次攻舒与夜复城分开，旧附延州起事和俘兵送回没有独立日不强套。死而复苏和复亡降各按上下文，不造死亡。',plain_language_review='首次逐条自查主语、角色和动作，称臣请求与已成约、推荐当日与死日、派遣与到达、拟死预感与真实死亡、命斩与旧执行、祖籍迁居与出生地分清，原引用保持字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
