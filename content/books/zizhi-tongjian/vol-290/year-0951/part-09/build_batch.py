# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 63–70."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,83))
COMMIT='b5396b868c179978bf5637eb7c5dc784ba41bd1d'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in []:
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
main_sources = ['tongjian-290-951-october-november']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p063-p070',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-october-november':'卷290·广顺元年·十月至十一月入楚与晋州战事','jiuwudaishi-112-october-relief':'卷112·太祖本纪三·广顺元年十月','songshi-261-siting-battle':'卷261·列传二十·陈思让传·虒亭战事','xinwudaishi-032-liu-renshan':'卷32·死节传·刘仁赡早年','xinwudaishi-062-chu-conquest':'卷62·南唐世家·保大九年入楚'}
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
lines = (ROOT / 'resources/derived/tongjian/290.txt').read_text().splitlines()
for n in range(63, 71):
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
    labels={'tongjian-290-951-october-november':'卷290·广顺元年·十月至十一月入楚与晋州战事','jiuwudaishi-112-october-relief':'卷112·太祖本纪三·广顺元年十月','songshi-261-siting-battle':'卷261·列传二十·陈思让传·虒亭战事','xinwudaishi-032-liu-renshan':'卷32·死节传·刘仁赡早年','xinwudaishi-062-chu-conquest':'卷62·南唐世家·保大九年入楚'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年十月至十一月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_09_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=951, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='951年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0951_' + code
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
        edge = 'participation_zztj_290_0951_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0951_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','北汉主':'刘崇（刘知远弟）','楚王':'马希崇','希崇':'马希崇','史彦超':'史彦超（后周将领）'})
NEW_ALIASES={'向训':['向訓'],'张仁谦':['張仁謙'],'王璠':[],'曹海金':[],'萧禹厥':['蕭禹厥'],'史彦超（后周将领）':['史彦超','史彥超'],'何徽':[],'刘仁赡':['劉仁贍'],'高远（南唐起居郎）':[],'申师厚':['申師厚'],'折逋嘉施':[]}
NEW_DESCRIPTIONS={'向训':'后周军官。951年与陈思让参与虒亭战事，《旧五代史》称监军，《宋史》称都监。生卒年及后续改名尚未据本次引文录入。','张仁谦':'后周军官。《宋史》陈思让传记他于951年与陈思让、向训等率军在虒亭西迎战北汉。生卒年未载。','王璠':'北汉偏将。《宋史》记951年虒亭交战中被陈思让等俘获。出生、死亡年份未载。','曹海金':'北汉偏将。《宋史》记951年虒亭交战中被陈思让等俘获。出生、死亡年份未载。','萧禹厥':'契丹彰国节度使。951年奉命率奚、契丹五万军队与北汉会合进攻后周。其他同音姓名对应及生卒年待核。','史彦超（后周将领）':'云州人，后周龙捷都指挥使。951年与王万敢、何徽防守晋州，抵抗北汉、契丹军。尚不与其他政权的同名将领合并，生卒年未录全。','何徽':'后周虎捷指挥使。951年与王万敢、史彦超共同抵御北汉、契丹对晋州的进攻。生卒年未载。','刘仁赡':'南唐将领，刘金之子，字守惠、彭城人。951年以武昌节度使身份率二百艘战舰攻取岳州。《新五代史》还记他早年任左监门卫将军、黄袁二州刺史，后掌亲军。生卒年尚未录入。','高远（南唐起居郎）':'幽州人，南唐起居郎。951年百官庆贺取湖南时，他认为取楚容易、守楚困难。未与其他年代同名人物合并，生卒年未载。','申师厚':'王峻的故交，曾为兖州牙将，失去职务后生活困顿。951年经王峻推荐任河西节度使，《旧五代史》还记任职前先授左卫将军。生卒年未载。','折逋嘉施':'凉州留后。951年向后周朝廷上表请求派来统帅，后周随后任命申师厚为河西节度使。生卒年未载。'}
old='jiuwudaishi-112-october-relief';song='songshi-261-siting-battle';liu='xinwudaishi-032-liu-renshan';nt='xinwudaishi-062-chu-conquest'
def attach(code,name,n,source,quote,role):
 pk=person(name,n,role,quote,source=source);ek='participation_zztj_290_0951_'+code+'_'+pk
 assert not any(x['key']==ek for x in B['person_events'])
 B['person_events'].append(dict(key=ek,person_key=pk,event_key=E[code],role=role,status='draft'))
 claim('person_event',ek,'role',f'{name}：{role}。',n,quote,'参与者来自同一战事的独立记载；纪时差异保留，不推定其他行动。',source=source)
add('chen_siting_victory','陈思让在虒亭击败北汉军',63,'冬，十月，',None,[('陈思让','以潞州巡检身份击败北汉军')],when='951年十月辛卯',place='虒亭')
sup('chen_siting_victory',63,old,'壬辰，潞州奏，巡檢使陳思讓、監軍向訓破河東賊軍於虒亭。','《旧五代史》十月壬辰记潞州奏报陈思让、向训在虒亭获胜。','《资治通鉴》辛卯为战事日期，此书壬辰为奏报，不把奏报日直接认作交战日。',relation='adds')
sup('chen_siting_victory',63,song,'廣順元年九月，劉崇遣大將李瑰領馬步軍各五都，鄉兵十都，自團柏軍於窯子店。思讓與都監向訓、張仁謙等率龍捷、吐渾軍，至虒亭西，與瑰軍遇，','《宋史》记陈思让与向训、张仁谦等率龙捷、吐浑军，在虒亭西遇李瑰军。','该传置于广顺元年九月，与《资治通鉴》十月辛卯不同。李瑰沿已核李存瑰别名，但战时月份按各书保留；都、军名不换算未经说明的人数。',relation='conflicts')
attach('chen_siting_victory','向训',63,old,'巡檢使陳思讓、監軍向訓破河東賊軍於虒亭。','以监军身份与陈思让共同击败北汉军')
attach('chen_siting_victory','张仁谦',63,song,'思讓與都監向訓、張仁謙等率龍捷、吐渾軍，至虒亭西，與瑰軍遇，','与陈思让、向训一起率军在虒亭西迎战')
E['siting_captures']=event('siting_captures','陈思让等在虒亭战事中俘获王璠、曹海金',63,'殺三百餘人，生禽百人，獲崇偏將王璠、曹海金，馬五十匹。',[('陈思让','与部将取得杀敌、俘虏及获马战果'),('王璠','以北汉偏将身份被俘'),('曹海金','以北汉偏将身份被俘')],source=song,when='951年虒亭战事，《宋史》置于九月，《资治通鉴》同战事记十月辛卯',place='虒亭西',description='《宋史》记陈思让等杀敌三百余人、生俘百人，俘获北汉偏将王璠、曹海金及马五十匹。',note='战果数字为《宋史》补充，生禽百人与两位偏将是否重复计数未明，不自行把总数加成一百零二人。')
add('bian_enters_liling','边镐率军进入醴陵',64,'唐边镐','引兵入醴陵。',[('边镐','率南唐军进入醴陵')],when='951年十月癸巳以前，具体进入日未载',place='醴陵')
add('ma_xichong_rewards_tang_army','马希崇派使者犒劳边镐军队',64,'癸巳，','遣使犒军。',[('楚王','派使者犒劳南唐军'),('边镐','所率部队获楚国使者犒劳')],when='951年十月癸巳',place='醴陵方向',note='原文未提供犒劳品类、数量或使者姓名。')
add('tuoba_heng_submission_letter','马希崇派拓跋恒向边镐递交降书',64,'壬寅，','乃为小儿送降状！”',[('楚王','派天策府学士递交降书'),('拓跋恒','向边镐递交请降文书并感叹自身处境'),('边镐','成为降书递交对象')],when='951年十月壬寅',place='楚国至南唐军',note='拓跋恒的感叹是人物话语，不作为本站对马希崇的称呼，也不推拓跋恒已死。')
add('ma_xichong_meets_bian','马希崇率弟侄迎接边镐，边镐传诏慰劳',64,'癸卯，','称诏劳之。',[('希崇','率弟侄迎接边镐并拜见'),('边镐','下马传达诏命，慰劳马希崇等')],when='951年十月癸卯',place='长沙方向',note='弟侄未具名，不猜每名宗族成员都到场。')
add('bian_enters_changsha','马希崇等随边镐进入长沙，边镐驻浏阳门楼',64,'甲辰，','镐舍于浏阳门楼，',[('希崇','随边镐进入长沙'),('边镐','入城并驻浏阳门楼')],when='951年十月甲辰',place='长沙、浏阳门楼')
sup('bian_enters_changsha',64,nt,'景遣信州刺史邊鎬攻楚，破潭州，','《新五代史》记李璟派信州刺史边镐攻楚、取潭州。','该书概述攻楚结果，《资治通鉴》详记递降书与迎接入城，不据“破”字虚构另一次强攻或战斗。')
add('bian_rewards_hunan_officials','湖南将吏向边镐祝贺，边镐厚赐他们',64,'湖南将吏毕贺，','镐皆厚赐之。',[('边镐','厚赐前来祝贺的湖南将吏')],when='951年十月甲辰入城后',place='长沙',note='将吏未逐一具名，不推他们全都正式授新职。')
add('bian_opens_grain_stores','边镐打开马氏粮仓赈济湖南饥民',64,'时湖南饥馑，',None,[('边镐','打开马氏仓粮赈济饥民')],when='951年十月入长沙以后',place='湖南',description='湖南正逢饥荒，边镐大量发放马氏粮仓的粮食赈济，史书记载楚人因此欢喜。',note='没有给出粮食总量或受助人数，不凭大悦推断长期支持南唐统治。')
add('xiao_yujue_joint_army','契丹派萧禹厥率奚、契丹五万军与北汉会合进攻',65,'契丹遣彰国节度使','会北汉兵入寇。',[('萧禹厥','以彰国节度使身份率奚、契丹五万军会合北汉军')],when='951年十月，具体派遣与会合日未载',place='北汉、后周边境',note='原文将五万作为奚契丹军合计，不写成两部各五万；本段未列派遣者姓名，不补其现场指挥。')
add('liu_chong_yindi_jinzhou','刘崇亲率两万兵从阴地关进攻晋州',65,'北汉主自将兵二万','寇晋州，',[('北汉主','亲自率两万兵从阴地关进攻晋州')],when='951年十月丁未设营以前',place='阴地关至晋州')
add('jinzhou_siege','刘崇军在晋州城北设营，三面立寨昼夜攻城，游兵至绛州',65,'丁未，','游兵至绛州。',[('北汉主','率军围攻晋州')],when='951年十月丁未开始设营，后续攻击具体起止日未载',place='晋州、绛州',note='三面立寨不等于四面完全合围；游兵到绛州不等于已攻占绛州。')
sup('jinzhou_siege',65,old,'丙午，晉州巡檢王萬敢奏，河東劉崇入寇，營於州北。','《旧五代史》记十月丙午王万敢奏报刘崇进攻、设营州北。','奏报记在丙午，《资治通鉴》丁未记设营，日期或叙事环节不同，保留两书，不改主书日期。',relation='conflicts')
add('jinzhou_defense','王万敢暂掌晋州，与史彦超、何徽共同守城',65,'时王晏已离镇，','共拒之。',[('王万敢','在旧帅已离、新帅未到时暂掌晋州并守城'),('史彦超','以龙捷都指挥使身份共同守城'),('何徽','以虎捷指挥使身份共同守城')],when='951年十月晋州被围期间',place='晋州',note='王晏与王彦超调任已录，本句作为守城人员安排背景，不再新建同一次调镇。')
claim('person',people['史彦超（后周将领）'],'description','史彦超是云州人。',65,'史彦超，云州人也。','限定本次后周守晋州将领，未与其他政权同名者合并。')
add('liu_renshan_takes_yuezhou','刘仁赡率二百艘战舰攻取岳州',66,'癸丑，','帅战舰二百取岳州，',[('刘仁赡','以南唐武昌节度使身份率二百艘战舰攻取岳州')],when='951年十月癸丑',place='岳州')
sup('liu_renshan_takes_yuezhou',66,old,'乙卯，荊南奏，淮南遣鄂州節度使劉仁贍，以戰船二百艘於今月二十五日入岳州。','《旧五代史》乙卯记荆南奏报刘仁赡于本月二十五日率二百艘战船入岳州。','《资治通鉴》癸丑为当月二十五日，乙卯是后来的奏报日；两书分别称武昌军与鄂州，不据此新建同名将领。')
add('liu_renshan_accepts_surrender','刘仁赡安抚接纳岳州归降者',66,'抚纳降附，','人忘其亡。',[('刘仁赡','安抚接纳归降者')],when='951年十月攻取岳州以后',place='岳州',note='人忘其亡为史家的赞许，不夸大为每个居民都接受新政权或没有损失。')
relationship('刘金','刘仁赡','父亲',66,'仁赡，金之子也。','本句明确父亲名金；《新五代史》进一步说明父金事杨行密，与已有吴将刘金沿同一淮南背景复用。')
claim('person',people['刘仁赡'],'description','刘仁赡字守惠，是彭城人，其父刘金曾侍奉杨行密、任濠滁二州刺史。',66,'仁贍字守惠，彭城人也。父金事楊行密，為濠、滁二州刺史，以驍勇知名。','父子身份及籍贯来自该书，不把其父任职记成951年新任。',source=liu)
claim('person',people['刘仁赡'],'description','刘仁赡早年任左监门卫将军、黄袁二州刺史，后来受李璟命掌亲军、任武昌军节度使。',66,'事南唐，為左監門衞將軍、黃袁二州刺史，所至稱治。李景使掌親軍，以為武昌軍節度使。','只补本段以前的履历，不提前录入后文周师攻淮、守寿州及家属事件。',source=liu)
add('tang_conquest_celebrations','南唐百官庆贺攻取湖南，高远担心容易攻取却难以守住',67,'唐百官共贺湖南平，','远，幽州人也。',[('高远（南唐起居郎）','在庆贺取湖南时表达守楚困难的担忧')],when='951年十月攻取湖南以后，具体庆贺日未载',place='南唐朝廷',note='高远的担忧不是已经失守湖南的事实；起居郎及幽州籍明确，不与其他同名者合并。')
add('li_jianxun_warns_conquest','李建勋担心攻取湖南成为祸患的开始',67,'司徒致仕李建勋曰：','祸其始此乎！”',[('李建勋','以致仕司徒身份表达对取楚后果的担忧')],when='951年十月取楚以后，具体谈话日未载',place='南唐',note='这是预测与担忧，不登记成祸患已经发生。')
add('li_jing_delays_rituals','李璟面对亲祭郊庙的请求，表示天下统一后再告谢',67,'唐主自即位以来，','然后告谢。”',[('唐主','此前未亲祭郊庙，回应礼官请求称统一后再告谢')],year=None,when='李璟即位后至取楚时期的追述，具体请求日未载',place='南唐朝廷',note='未尝亲祠不等于南唐没有任何祭祀；统一后告谢是其承诺，不记为后来已经实现。')
add('li_jing_easy_conquest_belief','李璟取楚后认为其他诸国也可迅速平定',67,'及一举取楚，','谓诸国指麾可定。',[('唐主','因取楚而认为诸国可迅速平定')],when='951年十月取楚之后',place='南唐',note='这是史书记载的判断，不视为其他各国已经投降。')
add('wei_cen_requests_weibo','魏岑请求将来任魏博节度使，李璟答允，魏岑拜谢',67,'魏岑侍宴言：',None,[('魏岑','请求待平定中原后任魏博节度使，并拜谢答允'),('唐主','答允魏岑未来任魏博节度使的请求')],when='951年取楚后的宴会，具体日期未载',place='南唐朝廷',note='这是附条件的请求与允诺，不登记成魏岑已获魏博任职；主骄臣佞保留为史家评价。')
add('ma_xie_hopes_tan_command','马希萼希望南唐任命他掌管潭州',68,'马希萼望唐人','立己为潭帅，',[('马希萼','希望南唐任命自己为潭州统帅')],when='951年十月南唐取楚后',place='衡山、潭州',note='望为期待，不写成已被任命。')
add('tanzhou_requests_bian','潭州人不愿由马希萼掌镇，请求边镐为统帅',68,'而潭人恶希萼，','共请边镐为帅，',[('边镐','成为潭州人请求留任的统帅对象')],when='951年十月南唐取楚后',place='潭州',note='潭人恶希萼为史书群体叙述，未列投票或每户民意，不虚构请求者姓名。')
add('bian_wuan_jiedushi','李璟任命边镐为武安节度使',68,'唐主乃以镐',None,[('唐主','任命边镐掌武安军'),('边镐','获任武安节度使')],when='951年十月潭州请求之后，具体授任日未载',place='武安军、潭州')
sup('bian_wuan_jiedushi',68,nt,'以邊鎬為湖南節度使。','《新五代史》记边镐任湖南节度使。','与《资治通鉴》武安节度使称谓分别保留，不把不同名称写成两次独立任职。')
add('shen_shihou_road_meeting','申师厚失职饥寒，在路上向故交王峻拜谒',69,'王峻有故人曰申师厚，','拜谒于道。',[('申师厚','失去职务后生活困顿，在路上拜谒王峻'),('王峻','遇到前来拜谒的故交申师厚')],year=None,when='951年十月申师厚任河西节度使以前的追述，具体见面日未载',place='后周道路',note='尝为兖州牙将是早年职位，不误写成当天仍任牙将。')
relationship('王峻','申师厚','故交',69,'王峻有故人曰申师厚，','故人表示原有交往关系，此处明确两人为故交；不是王峻与一切被推荐者都默认有此关系。')
add('liangzhou_requests_commander','凉州留后折逋嘉施上表请求朝廷派统帅',69,'会凉州留后','上表请帅于朝廷，',[('折逋嘉施','以凉州留后身份上表请求派统帅')],when='951年十月申师厚任职以前，具体上表日未载',place='凉州至后周朝廷')
add('guo_recruits_liangzhou_official','郭威招募愿去凉州的率府供奉官，一个多月无人应募',69,'帝以绝域非人所欲，','无人应募，',[('帝','招募自愿前往凉州的率府供奉官')],year=None,when='951年十月任命以前，招募持续一个多月，起始日未载',place='后周朝廷至凉州',note='一个多月可能跨月，不硬指定招募全在十月；无人应募不等于无人可任职。')
add('wang_recommends_shen','王峻向郭威推荐申师厚赴凉州任职',69,'峻荐师厚于帝。','峻荐师厚于帝。',[('王峻','推荐故交申师厚'),('帝','收到王峻对申师厚的推荐'),('申师厚','获王峻推荐')],when='951年十月丁巳以前',place='后周朝廷')
add('shen_hexi_jiedushi','郭威任命申师厚为河西节度使',69,'丁巳，','以师厚为河西节度使。',[('帝','任命申师厚为河西节度使'),('申师厚','获任河西节度使')],when='951年十月丁巳',place='河西军、凉州')
sup('shen_hexi_jiedushi',69,old,'丁巳，以左衛將軍申師厚為河西軍節度使、檢校太保。','《旧五代史》同日记申师厚由左卫将军任河西军节度使、检校太保。','补充此前官职和检校衔，不把兖州牙将当成此刻旧职。',relation='adds')
sup('shen_hexi_jiedushi',69,old,'師厚亦欣然求往，尋自前鎮將授左衛將軍、檢校工部尚書。翌日，乃有涼州之命，賜旌節、駝馬、繒帛以遣之。','《旧五代史》补记申师厚愿去，先授左卫将军、检校工部尚书，翌日得凉州之命，并获旌节、驼马、缯帛送行。','此前一天任职与随后正式命凉州分开理解，不据赠物推实际已经到任。',relation='adds')
add('bian_demands_ma_family_court','边镐催马希崇率宗族入朝南唐',69,'唐边镐趣','帅其族入朝，',[('边镐','催促马希崇率宗族入朝'),('希崇','被要求率宗族入朝')],when='951年十月入楚后、十一月辛酉登舟以前',place='长沙至南唐',note='趣为催促，不翻成边镐本人带全部宗族已经到金陵。')
add('ma_family_wants_to_stay','马氏宗族聚集哭泣，想重赂边镐，奏请留在长沙',69,'马氏聚族相泣，','奏乞留居长沙。',[],when='951年十一月辛酉登舟以前',place='长沙',note='欲重赂是意图，不写成已经交付贿赂；请留不等于南唐已答允。')
add('bian_rejects_ma_delay','边镐警告马希崇不可再反复，马希崇无言应对',69,'镐微晒曰：','希崇无以应，',[('边镐','以两家敌对及马氏内斗警告不得反复'),('希崇','对边镐的警告无以回应')],when='951年十一月辛酉登舟以前',place='长沙',note='殆六十年、未尝敢窥等为边镐的讲话，不用它独立证明两政权全部交往历史。')
add('ma_family_boards_boats','马希崇与宗族、将佐千余人哭着登舟离开',69,'十一月，辛酉，',None,[('希崇','与宗族及将佐千余人登舟离开长沙')],when='951年十一月辛酉',place='长沙至南唐',note='千余人为总人数；此处登舟不提前写成同日已经抵达金陵。')
sup('ma_family_boards_boats',69,nt,'盡遷馬氏之族于金陵。','《新五代史》概述马氏宗族被迁往金陵。','这是整个迁徙结果的概述，《资治通鉴》当前具体记登舟出发，区分出发日与抵达日，未提前录入马希萼洪州、马希崇舒州后续授任。')
add('wang_jun_relief_commander','郭威任王峻为行营都部署，率兵救晋州',70,'帝以北汉、契丹之兵','将兵救之。',[('帝','任王峻为行营都部署，命其救援晋州'),('王峻','受命率兵救晋州')],when='951年十一月甲子',place='后周朝廷至晋州')
sup('wang_jun_relief_commander',70,old,'丙辰，詔樞密使王峻率兵援晉州。','《旧五代史》在十月丙辰记命王峻率军援晋州。','与《资治通鉴》十一月甲子受命的月份、干支不同，并列保留，不自行把两次记日解释成已证实的两道不同命令。',relation='conflicts')
add('wang_jun_campaign_authority','郭威令各军听王峻指挥，准其便宜处置、自选将吏',70,'诏诸军皆受', '得自选择将吏。',[('帝','授王峻统一指挥、便宜处置及自选将吏权限'),('王峻','获得救援行动的指挥与选将权限')],when='951年十一月甲子',place='晋州救援军',note='这是授权，不虚构他已经选定哪些将吏。')
add('wang_jun_departs','王峻出发救晋州，郭威亲到城西饯行',70,'乙丑，',None,[('王峻','率救援军出发'),('帝','亲到城西为王峻饯行')],when='951年十一月乙丑',place='后周都城西侧',note='出发与甲子受命分别登记，不写成已解除晋州之围。')
reviews={63:'主书十月辛卯战，旧史壬辰奏，宋传置九月分别保留；向训、张仁谦及王璠曹海金来自同战场明确记载，宋杀俘获马数不重复相加，后续追击不提前录。',64:'醴陵入军、癸巳犒军、壬寅请降、癸卯迎军、甲辰入城、厚赐与开仓赈济连续分录。新书破潭州为概述，不虚构额外强攻；降书感叹是拓跋恒话语。',65:'五万奚契丹与两万北汉分清；三面围攻、游兵至绛州不等于攻占。旧史丙午奏报与主丁未设营并列；守城三将与已录调镇背景分开，史彦超限定后周将。',66:'主癸丑取岳、旧乙卯奏报本月二十五日分别理解；二百战船数量相合。刘金父亲方向明确，新书补字籍和父事杨行密，不提前寿州后事。',67:'庆贺、忧守、忧祸、郊庙追述、李璟判断和魏岑附条件求职分清；全部政治话语和史家评价不当确定结果，魏岑未实际任魏博。',68:'希萼盼任、潭人请帅与李璟正式任边镐分开；武安与新书湖南节度称谓保留不重复任职。',69:'故交拜谒、凉州请帅、跨月招募无人、推荐、丁巳授河西及马氏入朝过程分开。旧史先授左卫将军与次日河西命补证。重赂只是意图，十一辛酉登舟未当抵达日。',70:'主十一甲子授都部署、乙丑出发饯行与旧史十月丙辰救援诏异说保留；授权不代表已经选将，出发不等于解围。'}
assert not (P/'publication.json').exists()
for n in range(63,71):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(63,71)],next_paragraph=Q[71]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原68—75行连续八段；本年后续正文仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(63,71)],source_issues_review='逐字引文保持底本，纸本未核。虒亭战月与奏日、晋州设营和救援诏记日按各书分别保留；宋261按陈思让传正文，新32按刘仁赡正文核标签。刘金父子、王峻申师厚故交有明确引文；不提前录未来寿州、秦凤等行动。',plain_language_review='首次检查全部展示标题、人物、角色、关系、时间和引用说明。请求、期待、评价、允诺、授职、出发与实际结果分开；引用外使用白话，不补无证据的主语和细节。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
