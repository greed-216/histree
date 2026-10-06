# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 1–6."""
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
COMMIT='5a3b20b2409dbdd33b6e5de146408af9c01bd45c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-955-winter-huainan','jiuwudaishi-115-december-955','xinwudaishi-62-huainan-war-start']:
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
main_sources = ['tongjian-292-955-winter-huainan']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0956-p001-p006',
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
for n in range(1, 7):
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
        citation = f'卷292·显德三年（956年正月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0956_01_{len(B["claims"])+1:04d}'
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','王环':'王环（后蜀凤州节度使）','王绍颜':'王绍颜（南唐滁州刺史）'})
NEW_ALIASES={'张全约':['張全約'],'王绍颜（南唐滁州刺史）':[]}
NEW_DESCRIPTIONS={
'张全约':'南唐池州刺史。956年正月与刘仁赡劝阻刘彦贞急追周军，未获听从。正阳战败后收拢余众退到寿州，刘仁赡上表任其为马步左厢都指挥使。生卒年未载。',
'王绍颜（南唐滁州刺史）':'南唐滁州刺史。956年正阳之战后放弃城池逃走。是否与941年向李昪上书的同名内侍为同一人，尚无完整履历证据，暂分档保留。生卒年未载。'}
old='jiuwudaishi-116-january-956';last='jiuwudaishi-115-december-955';nw='xinwudaishi-62-huainan-war-start'
add('wanghuan_reward','柴荣任后蜀旧将王环为右骁卫大将军，奖励其此前守城不降',1,Q[1]['text'],None,[('帝','任王环为右骁卫大将军'),('王环','因此前守凤州不降而获任')],when='956年正月丙午',place='后周朝廷',note='复用955年新建后蜀王环，不与楚水军王环合并；奖励不降指被俘前尽忠所事，不译成王环正在拒绝任命。')
sup('wanghuan_reward',1,last,'辛卯，西南面行營都部署王景，差人部送所獲偽鳳翔節度使王環至闕。詔釋之，仍賜鞍馬衣服，尋授右驍衛〈（按：原本闕一字。）〉大將軍。','《旧五代史》在955年十二月押送到京、释放后接记王环获授右骁卫大将军。','主书将任命单列956年正月丙午，旧史在此前押送条后说寻授且官名缺字，两种纪时保留，不强定为两次不同任命。',relation='conflicts')
add('shangyao_report','李谷奏报在上窑击败一千余南唐兵',2,Q[2]['text'],None,[('李谷','奏报上窑获胜')],when='956年正月丁酉奏报，交战日未单列',place='上窑',note='败千余记击败规模，不直接等同斩首或阵亡人数。')
sup('shangyao_report',2,old,'丁酉，李穀奏，破淮賊於上窯。','《旧五代史》同日记李谷奏报上窑获胜，但未列人数。','两书详略分别保留，不将主书人数擅补进旧书摘录。')
add('daliang_outerwall_labor','柴荣征发开封等地十余万民众修筑大梁外城',3,Q[3]['text'],None,[('帝','征发多地民众修筑外城')],when='956年正月戊戌',place='大梁外城，民夫来自开封府、曹州、滑州、郑州',note='此为实际征发修筑，与955年扩城规划诏令分开；民众总数不重复分配到每州。')
sup('daliang_outerwall_labor',3,old,'戊戌，發丁夫十萬城京師羅城。','《旧五代史》同日记征发十万丁夫筑京师罗城。','主书十余万与旧史十万为约述差异，保留而不计算成精确人数。',relation='conflicts')
add('chairong_huainan_personal_order','柴荣下诏亲征淮南',4,'庚子，','下诏亲征淮南，',[('帝','下诏安排亲征')],when='956年正月庚子',place='后周朝廷',note='诏令和壬寅实际离京分开。')
sup('chairong_huainan_personal_order',4,old,'庚子，詔取此月八日幸淮南。','《旧五代史》同日记诏定本月八日出行淮南。','保留原历日期，与下文壬寅离京配合，不自行换算公历。')
add('dongjing_defense_arrangement','柴荣安排向训、王朴留守东京，韩通掌京城侍卫巡检',4,'以宣徽南院使、','在京内外都巡检。',[('帝','安排离京期间京城军政'),('向训','暂任东京留守'),('王朴','任向训副手'),('韩通','暂掌侍卫司及京城内外巡检')],when='《通鉴》接正月庚子诏令记部署；《旧五代史》向训王朴任命单列辛丑',place='东京大梁',description='柴荣亲征前，以宣徽南院使、镇安节度使向训暂任东京留守，端明殿学士王朴为副；彰信节度使韩通暂掌侍卫司和京城内外巡检。权表示暂任，未记三人永久离开原职。')
sup('dongjing_defense_arrangement',4,old,'辛丑，以宣徽南院使向訓為權東京留守，以端明殿學士王樸為副留守。','《旧五代史》把向训、王朴留守任命记在辛丑。','主书在庚子诏令同段附录任命，纪日详略分别保留，不替韩通添加旧史该句没有的任命。',relation='conflicts')
add('li_chongjin_baichongzan_advance','柴荣命李重进先赴正阳、白重赞率三千亲兵屯颍上',4,'命侍卫都指挥使、','屯颍上。',[('帝','安排先遣军和颍上兵力'),('李重进','奉命领兵先赴正阳'),('白重赞','以河阳节度使身份率三千亲兵屯颍上')],when='956年正月庚子诏令所附部署，具体到达日未载',place='正阳、颍上',note='三千只属于白重赞部，李重进所领人数未载。')
add('chairong_departs_daliang','柴荣离开大梁亲征',4,'壬寅，','帝发大梁。',[('帝','从大梁出发')],when='956年正月壬寅',place='大梁')
sup('chairong_departs_daliang',4,old,'壬寅，車駕發京師，','《旧五代史》同日记柴荣离京。','车驾指当时后周君主柴荣，不是尚未称帝的赵匡胤。')
add('liuyan zhen_relief'.replace(' ',''),'刘彦贞率兵赴来远镇，并以战舰威胁正阳浮桥',4,'李谷攻寿州，','为攻浮梁之势。',[('李谷','久攻寿州未下'),('刘彦贞','率援军至来远镇并安排战舰趋正阳')],when='956年正月李谷退兵之前，具体日未载',place='寿州、来远镇、正阳',description='李谷久攻寿州未克，刘彦贞率援军到来远镇，史书记其距寿州二百里；又派数百艘战舰趋正阳，形成威胁浮桥的态势。浮梁在此为浮桥，未记南唐已经把桥攻断。')
add('ligu_proposes_bridge_retreat','李谷因担心水战和浮桥被截，提议退守正阳待柴荣到来',4,'李谷畏之，','以待车驾。”',[('李谷','召将佐商议退守浮桥')],when='956年正月寿州围攻期间，具体提议日未载',place='寿州军前',note='这是李谷对风险的判断和建议，不把腹背受敌、皆不归写成已经发生的损失。')
add('chairong_tries_stop_retreat','柴荣在圉镇得知退兵计划，急派中使制止',4,'上至圉镇，','乘驿止之。',[('上','急派使者阻止退兵')],when='956年正月壬寅离京以后、丁未到陈州以前',place='圉镇至寿州军前',note='使者到达结果在后句，不能因发出命令就记李谷已经遵从。')
add('ligu_burns_supplies_retreats','使者到达时，李谷已烧掉粮草并退守正阳',4,'比至，','退保正阳。',[('李谷','焚毁粮草后退保正阳')],when='956年正月，具体退兵日未单列；旧史丁未奏报退守',place='寿州至正阳')
sup('ligu_burns_supplies_retreats',4,old,'丁未，李穀奏，自壽州引軍退守正陽。','《旧五代史》记丁未李谷奏报从寿州退守正阳。','丁未是奏报日期，不强改成实际退兵发生日。',field='time_original')
sup('ligu_burns_supplies_retreats',4,old,'軍回之際無復嚴整，公私之間頗多亡失，淮北役夫亦有陷於賊境者。','《旧五代史》还记撤退秩序失整，公私财物多有亡失，部分淮北役夫陷在对方境内。','亡失与陷境不能全译为死亡；人数、个人身份和最终结局未载。',relation='adds')
sup('ligu_burns_supplies_retreats',4,nw,'乃焚其芻糧，退屯正陽。','《新五代史》也记李谷烧粮退到正阳。','该段跨955与956叙事，本句按当前主書时序为956，不误系为段首南征的955年十一月。')
add('chairong_arrives_chen','柴荣到陈州，急遣李重进进兵淮上',4,'丁未，',None,[('帝','到陈州后急派李重进赴淮'),('李重进','奉命迅速引兵至淮上')],when='956年正月丁未',place='陈州至淮上')

add('ligu_requests_emperor_wait','李谷奏请柴荣暂留陈颍，待解决水军和浮桥风险',5,Q[5]['text'],None,[('李谷','奏陈水军和粮道风险，请柴荣暂驻陈颍'),('帝','阅读奏章后不悦')],when='956年正月辛亥奏报',place='正阳军前至柴荣行在',description='李谷认为南唐战舰从河中推进、弩炮不能及，且淮水上涨，浮桥和粮道可能被截，因此请柴荣暂驻陈州、颍州，等李重进到后共商御舰保桥，并主张通过长期备战耗敌。柴荣看后不悦。这些风险和长期策略属于李谷的判断，不是粮道此时已被截断的事实。')
for st,en,text in [('贼舰中淮而进，','其危不测。','李谷声称战舰推进、河水上涨，担心浮桥粮道中断会危及军队和柴荣。'),('愿陛下且驻跸陈、颍，','立具奏闻。','李谷请柴荣先驻陈颍，待李重进到后判断如何御舰保桥，再立刻奏报。'),('但若厉兵秣马，','取之未晚。','李谷认为跨春冬长期备战可以使南唐疲弊，不必急取。')]:
 claim('event',E['ligu_requests_emperor_wait'],'description',text,5,span(5,st,en),'这是奏章中的建议与预判，不把尚未发生的风险、未来军队疲弊或取胜当作既成结果。')

p=person('刘彦贞',6,'是此次南唐援军主将，史书对其此前能力和行为有负面评价',span(6,'刘彦贞素','故周师至，唐主首用之。'))
claim('person',p,'evaluation','《通鉴》认为刘彦贞骄贵、缺少军事才略，历任藩镇时贪暴，积财并贿赂权要。',6,span(6,'刘彦贞素','以赂权要，'),'这是史书评价和行为概述，巨亿不转换成可验证的现代财产金额，也不点名未载受贿者。')
add('weicen_praises_liuyanzhen','魏岑等称赞刘彦贞的治民和用兵能力',6,'由是魏岑等','唐主首用之。',[('魏岑','与其他人夸赞刘彦贞'),('刘彦贞','受到魏岑等称赞而获李璟优先任用'),('唐主','面对周军来攻时优先任用刘彦贞')],year=None,when='南征前旧事及任用背景，具体称赞年日未载',place='南唐朝廷',description='《通鉴》记魏岑等把刘彦贞的治民和用兵比作古代名臣名将，因此李璟在周军到来时首先任用他。这是他人赞辞与史家的任用解释，不是本站对刘彦贞能力的肯定。',note='未说魏岑本人收受某笔财物，不从上下句推定具体受贿名单；不另建龚黄韩彭参与此事。')
add('liuyanzhen_chases_zhou','刘彦贞、咸师朗等闻周军撤退后率军急追正阳',6,'其裨将咸师朗','旌旗辎重数百里，',[('刘彦贞','率军追击退走的周军'),('咸师朗','与其他裨将认为周军撤退可趁，参与追击')],when='956年正月李谷退守之后、正阳之战之前',place='至正阳',note='勇而无谋为史家评价，数百里为叙述军队辎重延展的概数，不当实测战线。')
add('liurenshan_zhangquanyue_warn','刘仁赡、张全约劝阻刘彦贞急追，刘彦贞不听',6,'刘仁赡及池州刺史','彦贞不从。',[('刘仁赡','劝刘彦贞不要急战'),('张全约','与刘仁赡共同劝阻'),('刘彦贞','拒绝劝阻')],when='956年正月正阳之战以前',place='南唐寿州援军',description='刘仁赡和池州刺史张全约劝刘彦贞不要急追。刘仁赡说未交战而敌人先退，可能是畏其声威，急战一旦失利将危及大局。刘彦贞不听。这是劝告的理由，不证明周军撤退真的出于畏惧他。')
sup('liurenshan_zhangquanyue_warn',6,old,'前軍張全約亦曰：「不可追。」','《旧五代史》所引马令《南唐书》也记张全约反对追击。','明确标为旧史所引另一书的补充，不能当作独立查得另一份马令底本。')
add('liurenshan_strengthens_shouzhou','刘仁赡预言刘彦贞遇敌必败，加兵守寿州城',6,'既行，仁赡曰：','乃益兵乘城为备。',[('刘仁赡','在劝阻失败后加兵守城')],when='956年正月刘彦贞出发以后',place='寿州',note='果遇必败是其当时预言，守城行动明确，不用结果倒推预言是战后发言。')
add('zhengyang_battle','李重进渡淮，在正阳东击败刘彦贞，杀死刘彦贞并俘咸师朗等',6,'李重进度淮，','收军资器械三十馀万。',[('李重进','渡淮迎战并击败南唐军'),('刘彦贞','在正阳战败被杀'),('咸师朗','与其他南唐将领被生俘')],when='956年正月，主书本段未独立列战日；《旧五代史》辛亥奏报',place='正阳东',description='李重进渡过淮河，在正阳东迎击南唐军并获胜。刘彦贞被杀，咸师朗等被俘。《通鉴》记斩首万余级、尸体延展三十里、收得军资器械三十余万；《旧五代史》奏报记斩首二万余级，戎甲三十万副、马五百匹。人数和物资统计口径分别保留，不相加为总数。')
sup('zhengyang_battle',6,old,'辛亥，李重進奏，大破淮賊於正陽，斬首二萬餘級，伏屍三十里，臨陣斬賊大將劉彥貞，生擒偏將鹹師朗已下，獲戎甲三十萬副、馬五百匹。','《旧五代史》记正月辛亥李重进奏报正阳获胜，杀刘彦贞、俘咸师朗等，斩首二万余级并获戎甲三十万副及五百马。','辛亥用于奏报，不强定为交战日；斩首万余与二万余、军资器械与戎甲计量差别并列，鹹师朗沿原咸师朗主体，不改摘录。',relation='conflicts')
sup('zhengyang_battle',6,nw,'比及正陽，而重進先至，軍未及食而戰，彥貞等遂敗。','《新五代史》也记李重进先至正阳，刘彦贞军未及进食交战而败。','补书没有明确战日，不以同段开头十三年十一月强定此战发生于955。')
claim('person',people['刘彦贞'],'death_year','刘彦贞于956年正阳之战被杀。',6,span(6,'李重进度淮，','生擒咸师朗等，'),'死亡年按主书显德三年正月上下文，日期未另列，旧史同年奏报印证。')
add('zhaochao_kills_surrendered','《旧五代史》记赵晁杀害正阳战后三千余降兵',6,'殺獲之外，','皆為我將趙晁所殺。',[('赵晁','杀害已经投降的南唐兵')],source=old,when='956年正月正阳之战后，具体日未载',place='正阳战后地点未载',note='降者三千余与战阵斩首的统计范围不同，单独保存杀降事件，不把降兵仍记作交战阵亡；旧书明确为已执行。')
add('zhangquanyue_returns_shouzhou','张全约收拢残兵退回寿州，刘仁赡上表任其为左厢都指挥使',6,'是时江、淮','为马步左厢都指挥使。',[('张全约','收拢余众退到寿州，并获表任'),('刘仁赡','上表任张全约为马步左厢都指挥使')],when='956年正月正阳失利以后',place='寿州',description='《通鉴》记江淮长期安定、民众不惯战争，刘彦贞战败使南唐人恐惧。张全约收余众退到寿州，刘仁赡上表任他为马步左厢都指挥使。背景评价与退兵、任职分别说明，未写成已有全体民众测量结果。')
add('huangfu_yao_retreat_qingliu','皇甫晖、姚凤退守清流关',6,'皇甫晖、','退保清流关。',[('皇甫晖','退守清流关'),('姚凤','与皇甫晖退守清流关')],when='956年正月正阳之战后',place='清流关',note='与此前955年屯定远分阶段保存；本段未记两人已被俘。')
add('wangshaoyan_leaves_chuzhou','滁州刺史王绍颜放弃城池逃走',6,'滁州刺史王绍颜',None,[('王绍颜','放弃滁州逃走')],when='956年正月正阳之战后',place='滁州',note='暂无与941年内侍同人的连续履历证据，暂建限定名，不覆盖原人；未记周军同日已正式占城。')

reviews={1:'后蜀王环复用955新建限定名，与楚将分开；主书956正月丙午与旧史955十二月条后寻授、缺字并列，守城不降指俘前尽忠。',2:'丁酉为奏报；千余败兵非千余死亡，旧未列人数。',3:'戊戌征发为执行阶段，与955规划分开，十万及十余万分别保留。',4:'庚子诏亲征、京城留守安排、两路先遣、壬寅离京、刘彦贞救援、水军威胁、李谷议退、柴荣使止、已烧粮撤退、丁未陈州调兵完整处理。旧辛丑留守纪日与主附庚子并列；撤退役夫陷境不作死亡。',5:'辛亥奏章分风险、暂驻请求与长期备战策略，奏称风险不当已断粮，柴荣不悦只是反应。',6:'负面评价、魏岑赞辞和任用解释、追击、两将劝阻、守城准备、正阳战俘杀、旧史明确杀降三千余、收残军表任、清流退兵、滁州弃城全部处理。斩首万余与二万余不相加，辛亥为奏报；咸鹹字形保留，王绍颜同名待核分档。'}
assert not (P/'publication.json').exists()
for n in range(1,7):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph=Q[7]['id'],next_volume=292,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原74—79行六个连续正文长短段，从王环任命至正阳战后；全年的后续和下一卷未计完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,7)],source_issues_review='王环授官时点及缺字、留守任命庚子辛丑、役夫十万十余万、斩首万余二万余与物资口径并列。王绍颜滁州刺史与941同名内侍未强合。新史一段跨955956不套段首年代，旧史引马令注明依赖。',plain_language_review='首次逐条检查标题、人物、角色、时间、正文及事实解释为现代白话，保留明确主语；风险与事实、建议与执行、奏报与交战、阵亡与杀降分清，摘录保持原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
