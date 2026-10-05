# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 69–72."""
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
COMMIT='b7c52ba6cde22f73d5e0bc2ffea0ec77f628d107'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-regency-chu-defense','jiuwudaishi-103-succession-regency']:
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
main_sources = ['tongjian-289-950-regency-chu-defense']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p069-p072',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-103-december-expedition':'卷103·隐帝本纪·十二月北征与任命','xinwudaishi-066-peng-plan':'卷66·楚世家·彭师暠作战建议','liaoshi-005-neiqiu-invasion':'卷5·世宗本纪·天禄四年十月南伐'}
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
for n in range(69, 73):
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
    labels={'jiuwudaishi-103-december-expedition':'卷103·隐帝本纪·十二月北征与任命','xinwudaishi-066-peng-plan':'卷66·楚世家·彭师暠作战建议','liaoshi-005-neiqiu-invasion':'卷5·世宗本纪·天禄四年十月南伐'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十一月至十二月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_11_{len(B["claims"])+1:04d}'
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










ALIASES.update({'太后':'李氏（刘知远妻）','契丹主':'耶律阮','希广':'马希广','希萼':'马希萼','硃进忠':'朱进忠','师暠':'彭师暠','可琼':'许可琼','王殷':'王殷（后汉后周将）'})
NEW_ALIASES={}
old='jiuwudaishi-103-succession-regency';dec='jiuwudaishi-103-december-expedition';chu='xinwudaishi-066-peng-plan';liao='liaoshi-005-neiqiu-invasion'
add('neiqiu_siege_report','镇州、邢州奏报契丹军围攻内丘，五日未攻克',69,'镇州、刑州奏：','死伤其众。',[('契丹主','率数万骑围攻内丘，五日未克')],when='950年十一月临朝后收到奏报，围攻发生日未载',place='内丘',description='镇州、邢州奏报：契丹君主率数万骑入侵，围攻内丘五日未能攻克，契丹军有死伤。',note='刑州沿已有地名邢州规范；数万骑是奏报规模，未给具体人数。奏报时间与实际围攻时间区分。')
sup('neiqiu_siege_report',69,old,'鎮州、邢州馳奏，契丹寇洺州，陷內丘縣。時契丹永康王烏裕率部族兩道入邊，內丘城小而固，契丹攻之，五日不下，敵人傷者甚眾。','《旧五代史》也记契丹君主率部族入边，围攻内丘五日未下。','永康王乌裕按既有耶律阮身份识别；旧史补记两路入边、内丘城小而坚固，不从此推具体入侵日。')
add('neiqiu_garrison_defection','内丘五百戍兵倒向契丹，引军入城后城遭屠杀',69,'有戍兵五百','入城，屠之，',[('契丹主','所率军队因戍兵引入攻下内丘')],when='950年十一月奏报所述围攻之后，具体陷城日未载',place='内丘',description='奏报记内丘五百戍兵倒向契丹，引契丹军入城；城中随后遭到屠杀。',note='被杀人数及具体执行者未载，不凭数百戍兵推全城人口。')
sup('neiqiu_garrison_defection',69,old,'時有官軍五百，在城防戍，攻急，官軍降於敵，屠其城而去。','《旧五代史》也记五百守军在攻势紧迫时投降，契丹军屠城后离去。','投降引入与随后屠城有对应证据，未补死亡总数。')
sup('neiqiu_garrison_defection',69,liao,'冬十月，自將南伐，攻下安平、內丘、束鹿等城，大獲而還。','《辽史》将契丹君主攻下内丘等城的南伐记在天禄四年十月。','已核上文四年为天禄四年950年。《通鉴》十一月记录奏报，《辽史》十月叙南伐，不能将奏报月当作围攻月；辽史本条没有守军投降与屠城细节。',relation='adds',field='time_original')
add('raoyang_falls_after_neiqiu','契丹军攻下内丘后又攻陷饶阳',69,'又陷饶阳。','又陷饶阳。',[('契丹主','所率契丹军又攻陷饶阳')],when='950年十一月奏报所述，具体陷城日未载',place='饶阳',note='奏报顺序记又陷，不把辽史的安平、束鹿等名单与饶阳强行互换，也不推饶阳必被屠城。')
add('lady_orders_guo_north','李太后命郭威率大军北征契丹',69,'太后敕郭威','击之，',[('太后','命郭威率军抵抗契丹'),('郭威','奉命率大军北征')],when='950年十一月收到契丹入侵奏报后、十二月甲午出发前',place='后汉朝廷，拟北征',note='敕命与下一句实际出发分开，不写此时已经交战或击败契丹。')
add('north_campaign_court_delegation','郭威北征时，政务暂交窦贞固、苏禹珪和王峻',69,'国事权委','苏禹珪、王峻，',[('太后','安排北征期间的政务职掌'),('窦贞固','受托暂管政务'),('苏禹珪','受托暂管政务'),('王峻','受托暂管政务')],when='950年十一月北征敕命后、十二月甲午出发前',place='后汉朝廷',note='权委为临时委托，不写三人同时任皇帝或永久获得全部权力。')
add('north_campaign_military_delegation','郭威北征时，军事事务交由王殷负责',69,'军事委王殷。','军事委王殷。',[('太后','安排军事职掌'),('王殷','受托负责军事事务')],when='950年十一月北征安排时、十二月甲午出发前',place='后汉朝廷',note='沿用后汉后周将王殷主体；不将朝廷委托解释成取代郭威北征指挥。')
add('guo_leaves_daliang_north','郭威于十二月甲午朔率军离开大梁北征',69,'十二月，',None,[('郭威','率大军自大梁出发北征')],when='950年十二月甲午朔',place='大梁',note='朔为本月初一，原纪日保留，不自行换算公历月日。')
sup('guo_leaves_daliang_north',69,dec,'十二月甲午朔，郭威領大軍北征。','《旧五代史》也记十二月甲午朔郭威率军北征。','本纪正文同日相符，尚未到澶州或发生军变。',field='time_original')
add('fan_zhi_privy_deputy','范质于丁酉被任命为枢密副使',70,'丁酉，',None,[('范质','由翰林学士、户部侍郎任枢密副使')],when='950年十二月丁酉',place='后汉朝廷',note='本段未写任命者姓名，不自行补郭威亲授；范质与範質沿既有人物。')
sup('fan_zhi_privy_deputy',70,dec,'丁酉，以翰林學士、尚書戶部侍郎、知制誥範質為樞密副使。','《旧五代史》也记丁酉任范质为枢密副使，并列他原任知制诰。','本纪正文列户部侍郎，附引《东都事略》记兵部侍郎，两层文本不可混作同一记载；本批沿两书正文，保留附引官衔差异待核。')
add('peng_prior_surrender','彭师暠此前归降楚国',71,'初，','彭师暠降于楚，',[('彭师暠','此前归降楚国')],year=None,when='950年长沙围城叙事中的早年追述',note='本段初不提供新日期；与940年交印请降事件相接，复用该事件和既有参与关系，不另造950年归降。',stable_key='event_zztj_282_0940_peng_surrenders_seals')
add('peng_crossbow_appointment','马希广重用彭师暠，任其为强弩指挥使并领辰州刺史',71,'楚人恶其犷直。','师暠常欲为希广死。',[('希广','怜惜彭师暠并任命其掌强弩、领辰州刺史'),('彭师暠','受任后愿为马希广效死')],year=None,when='马希广在位、950年长沙围城以前，具体任命年日未载',place='楚国',description='史书记楚人不喜欢彭师暠的粗直性格，马希广却怜惜他，任他为强弩指挥使，兼领辰州刺史；彭师暠常愿为马希广效死。',note='性格与效死之心是史书的叙述；领刺史不推已赴辰州，任命不能强定为950年。')
add('zhu_troops_jiangxi','朱进忠与部族兵合计七千余人到长沙，驻湘江西岸',71,'及硃进忠','营于江西，',[('硃进忠','与部族兵合计七千余人至长沙驻军')],when='950年长沙围城期间，具体到达日未载',place='长沙湘江西岸',note='七千余是合计，不写各七千；江西按下文渡江岳麓水西解为湘江西岸，不套现代江西省。原文蛮为史书称呼。')
add('peng_proposes_crossriver_attack','彭师暠请求步兵三千，提议与许可琼水军夹攻敌军',71,'师暠登城望之，','希广将从之。',[('彭师暠','提议从巴溪渡江到岳麓后，与水军腹背夹击'),('希广','起初打算采纳方案'),('可琼','被方案安排以战舰渡江配合')],when='950年长沙围城期间，具体建议日未载',place='长沙、巴溪、岳麓、水西',description='彭师暠认为朱进忠所部骄纵，建议借步兵三千自巴溪渡江，绕到岳麓后至水西，让许可琼水军渡江配合夹攻。马希广起初打算采纳。',note='易破、必破是彭师暠判断，未发生夹攻，三千为请求兵数，不是实际已调拨人数。')
sup('peng_proposes_crossriver_attack',71,chu,'請令可瓊等陣山前，臣以步兵三千自巴溪渡江趨岳麓，候夜擊之。','《新五代史》也记彭师暠请求三千步兵由巴溪渡江到岳麓，提出夜袭方案。','《通鉴》强调许可琼战舰渡江腹背夹击，《新五代史》写可琼等列阵山前并等候夜袭；保留方案细节差异，不混成一项已执行作战。',relation='adds')
add('ma_xie_bribes_xu','马希萼派密使许诺厚利及分治湖南，争取许可琼',71,'时马希萼','可琼有贰心，',[('希萼','派密使以利益和分治湖南的承诺争取许可琼'),('可琼','受到争取，开始有背离马希广的想法')],when='950年长沙围城期间、许可琼阻止进攻方案前',place='长沙围城军中',note='许分湖南为承诺，不写已实现分治；密使未具名不建人物。')
add('xu_blocks_peng_plan','许可琼诋毁彭师暠不可信，马希广放弃夹攻方案',71,'乃谓希广曰：','希广乃止。',[('可琼','以彭师暠与梅山诸部同类为由反对方案，声称不会负马希广'),('希广','听信许可琼，放弃方案'),('彭师暠','所提方案被阻止')],when='950年长沙围城期间，彭师暠建议进攻后',place='长沙',note='族类说法是许可琼的指控，不据此建立彭与梅山各酋具体血亲关系；世为楚将为自述，不推历代名单。')
sup('xu_blocks_peng_plan',71,chu,'希廣以為可，而可瓊已陰送款於希萼，遂沮其議。','《新五代史》也记马希广赞同方案，许可琼已暗中联络马希萼并阻止执行。','送款解释为暗中联络投靠，不当现代汇款；此时仍与随后公开投降区分。')
add('ma_xie_fourhundred_ships','马希萼以四百余艘战舰停泊湘江西岸',71,'希萼寻','泊江西。',[('希萼','率四百余艘战舰停泊湘江西岸')],when='950年长沙围城期间、夹攻方案被放弃后',place='长沙湘江西岸',note='寻为随后，不给具体日；四百余战舰不同于守方前批五百舰。')
add('xu_controls_generals','马希广令诸将听许可琼指挥，每日赐银五百两',71,'希广命诸将','银五百两，',[('希广','命诸将听许可琼指挥，每日赐银五百两'),('可琼','获得诸将指挥权和每日赏赐')],when='950年长沙围城期间，具体命令日未载',place='长沙',note='日赐是每日，不是单次或总计；未经执行日数不能算累计银额。')
add('ma_guang_visits_xu_camp','马希广多次到许可琼营中议事，因其闭营而称赞',71,'希广屡造','吾何忧哉！”',[('希广','多次到营议事，称赞许可琼并表示放心'),('可琼','常闭营，不使士卒知道朗军进退')],when='950年长沙围城期间、许可琼掌诸将后',place='许可琼军营',description='马希广多次到许可琼营中商议军务。许可琼常闭营，使士卒不知道朗军进退；马希广却称他为真将军，认为无需担忧。',note='称赞为马希广判断，不当证明指挥确实有效；闭营与隐瞒敌情按原文，不补现代军令动机。')
add('xu_meets_ma_xie_secretly','许可琼夜乘小船秘密会马希萼，约定作内应',71,'可琼或夜','约为内应。',[('可琼','借巡江之名夜乘小船，约定作内应'),('希萼','在水西秘密与许可琼会面')],when='950年长沙围城期间，具体秘密会面日未载',place='水西',note='或夜为有一夜，不写每天；单舸是小船，未载随从人数；承诺内应与实际举军投降分开。')
add('peng_requests_xu_removal','彭师暠斥责许可琼，向马希广请求尽快除去他',71,'一旦，','无贻后患。”',[('彭师暠','当面斥责许可琼，并入见马希广请求除掉他'),('可琼','被指将背叛楚国'),('希广','收到除去许可琼的请求')],when='950年长沙围城期间，秘密联络之后，具体日未载',place='长沙',note='人皆知之为彭师暠发言，不推每个士兵皆知；本句为请求，未执行杀人。')
sup('peng_requests_xu_removal',71,chu,'明日，師暠詣可瓊計事，瞋目叱之曰：「視汝反文在面，豈欲投賊乎！」拂衣而出，急白希廣，請殺之，希廣不聽。','《新五代史》也记彭师暠当面斥责许可琼，急告马希广请求杀他，马希广不听。','《新五代史》说提出作战建议的明日，《通鉴》只说一旦；不得将明日换算为确定公历日期。',relation='adds')
add('ma_guang_refuses_peng_warning','马希广因许可琼是许德勋之子，不信其将背叛',71,'希广曰：“可琼，',None,[('希广','以许可琼出身许德勋之家为由不信其背叛'),('彭师暠','退下后认为马希广缺乏决断，预言将败亡'),('可琼','仍获马希广信任')],when='950年长沙围城期间，彭师暠请求除去许可琼后',place='长沙',description='马希广说许可琼是许德勋之子，不相信他会背叛。彭师暠退下后叹马希广仁慈却不果断，认为败亡已近。',note='败亡预言是彭师暠评价，不提前将长沙陷落记为本句执行结果。亲属已有关系，本批不重复新建。')
add('changsha_snow_delays_battle','潭州大雪，潭州与朗州两军长时间未能交战',72,'潭州大雪，','久不得战。',[],when='950年长沙围城期间、十二月甲辰交战以前，降雪日未载',place='潭州',description='潭州大雪，史书记平地积雪四尺，潭州与朗州两军长时间不能交战。',note='四尺保留古制，没有同时代尺度依据不换算厘米；久不改成确定天数，气象现象无需造人物参与。')
add('ma_guang_ritual_statues','马希广听信巫师和僧人，制作鬼神塑像以求阻止朗军',72,'希广信巫觋','怒目视之，',[('希广','听信巫师与僧人建议，制作江边及高楼塑像')],when='950年长沙围城大雪时期，具体施行日未载',place='长沙江边、高楼',description='马希广听信巫师和僧人的话，在江边塑造举手阻挡朗军的鬼神，又在高楼制大像，手指水西、怒目相视。',note='塑像形象及求阻敌是实际举措与意图，不写鬼神实际击退朗兵；工匠、巫师和僧人无姓名不建人物。')
add('ma_guang_buddhist_prayers','马希广命僧人昼夜诵经，自己穿僧服礼拜求福',72,'命众僧',None,[('希广','命僧人昼夜诵经，自己穿僧服礼拜求福')],when='950年长沙围城大雪时期，具体祈福日未载',place='长沙',note='求福是意图，未证明实际获得护佑，也不据僧服推正式出家。')
reviews={69:'奏报与实际入侵时间分开；围攻五日未克、戍兵倒向契丹屠城、饶阳陷落、北征敕命、临时政务军事安排、十二月甲午出发分别录。旧本纪补军情，辽史天禄四年十月叙南伐不直接替换通鉴奏报月。',70:'丁酉任枢密副使与旧本纪同日相符；原任户部侍郎沿正文，旧史附引东都事略兵部侍郎差异保留待核；範質沿范质。',71:'归降追述复用940交印事件；马希广任彭官时间未知年null。夹攻建议、厚利及分治承诺、阻止方案、战舰驻军、指挥与赏赐、闭营议事、夜约内应、除叛请求和拒绝分别记。方案未执行，亲属沿既有关系。新史作战部署和明日时序差异保留。',72:'雪四尺与久未战保留原制和不确定时长。塑像与诵经礼拜记实际行为，神力挡兵、护佑及正式出家不作已实现事实。'}
assert not (P/'publication.json').exists()
for n in range(69,73):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(69,73)],next_paragraph=Q[73]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原74—77行连续四段；发布后首72/83正文已录，余11段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(69,73)],source_issues_review='辽史南伐月与汉廷奏报月区别，旧本纪附引范质兵部与正文户部官衔待核。彭作战建议在新旧叙述细节不同并列；族类与忠诚指控保留话语层，未知年月不强系。纸本及转录异文待核。',plain_language_review='逐条检查标题、说明、参与动作和对应事实说明，均使用现代白话；引文保持原字。计划、许诺、评价、奏报与执行区分，引用与主体逐条回核，不增设发布后二次文案审阅。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
