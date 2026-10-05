# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 16–22."""
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
COMMIT='278d73db50d6b6efe72681242684d9d42d0da2d4'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
specs.append(('tongjian-290-951-january-court',YEAR/'part-01/sources/library/tongjian-290-951-january-court',COMMIT,'司马光等'))
for key in ['jiuwudaishi-110-yedu-funeral','xinwudaishi-011-first-year-951']:
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
main_sources = ['tongjian-290-951-january-court']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p016-p022',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-110-tribute-food': '卷110·太祖本纪·停止贡食诏书', 'jiuwudaishi-110-advice': '卷110·太祖本纪·求言与将领任官', 'jiuwudaishi-111-jinzhou': '卷111·太祖本纪·澶州任官与晋州战报', 'jiuwudaishi-111-xizhou': '卷111·太祖本纪·隰州战报', 'jiuwudaishi-128-wangmin-career': '卷128·王敏传·杜重威幕府至澶州', 'jiuwudaishi-128-wangpu-career': '卷128·王朴传·校书郎与澶州记室', 'songshi-431-cuisong-family': '卷431·崔颂传·父亲与早年履历', 'songshi-431-cuisong-chanzhou': '卷431·崔颂传·澶州幕府', 'songshi-252-wangyan-jinzhou': '卷252·王晏传·晋州防御'}
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
for n in range(16, 23):
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
    labels={'jiuwudaishi-110-tribute-food': '卷110·太祖本纪·停止贡食诏书', 'jiuwudaishi-110-advice': '卷110·太祖本纪·求言与将领任官', 'jiuwudaishi-111-jinzhou': '卷111·太祖本纪·澶州任官与晋州战报', 'jiuwudaishi-111-xizhou': '卷111·太祖本纪·隰州战报', 'jiuwudaishi-128-wangmin-career': '卷128·王敏传·杜重威幕府至澶州', 'jiuwudaishi-128-wangpu-career': '卷128·王朴传·校书郎与澶州记室', 'songshi-431-cuisong-family': '卷431·崔颂传·父亲与早年履历', 'songshi-431-cuisong-chanzhou': '卷431·崔颂传·澶州幕府', 'songshi-252-wangyan-jinzhou': '卷252·王晏传·晋州防御'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年正月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_03_{len(B["claims"])+1:04d}'
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










ALIASES.update({'帝':'郭威','北汉主':'刘崇（刘知远弟）','刘崇':'刘崇（刘知远弟）','承钧':'刘承钧','潘聿撚':'潘聿捻','巩廷美':'巩延美','王敏':'王敏（杜重威判官）','荣':'柴荣','崇':'郭崇威','英':'曹威'})
NEW_ALIASES={'崔颂':['崔頌'],'王朴':['王樸'],'安元宝':['安元寶'],'许迁':['許遷'],'耿继业':['耿繼業'],'程筠':[]}
NEW_DESCRIPTIONS={'崔颂':'崔协之子，原任右补阙。951年任柴荣镇宁军观察判官。《宋史》记他字敦美、河南偃师人。生卒年尚未录入。','王朴':'东平人，原任校书郎。951年任柴荣镇宁军掌书记。《旧五代史》记他字文伯，在后汉乾祐年间中进士，后来进入澶州幕府。生卒年尚未录入。','安元宝':'北汉副兵马使。951年受命前去焚烧晋州西城，却向后周投降；史书未明言他是否完成焚烧。生卒年未载。','许迁':'郓州人，隰州刺史。951年派耿继业在长寿村迎击北汉军，随后守住隰州。生卒年未载。','耿继业':'隰州步军都指挥使。951年受许迁派遣，在长寿村迎击北汉军，俘获程筠等人后将其杀死。生卒年未载。','程筠':'北汉将领。951年在长寿村被耿继业俘获并杀死。出生年未载。'}
NEW_DEATH_YEARS={'程筠':951}
f='jiuwudaishi-110-yedu-funeral';food='jiuwudaishi-110-tribute-food';advice='jiuwudaishi-110-advice';jin='jiuwudaishi-111-jinzhou';xi='jiuwudaishi-111-xizhou';wm='jiuwudaishi-128-wangmin-career';wp='jiuwudaishi-128-wangpu-career';cf='songshi-431-cuisong-family';cc='songshi-431-cuisong-chanzhou';wy='songshi-252-wangyan-jinzhou';nw='xinwudaishi-011-first-year-951'
for code,name,office,start,end in [('feng_dao_chancellor','冯道','中书令','以太师冯道','为中书令，'),('dou_zhengu_shizhong','窦贞固','侍中','加窦贞固','侍中，'),('su_yugui_sikong','苏禹珪','司空','苏禹珪','司空。')]:
 add(code,'郭威任命'+name+'为'+office,16,start,end,[('帝','任命'+name+'为'+office),(name,'获任'+office)],when='951年正月己卯',place='后周朝廷',note='同日三项任命分别登记；没有把加官解释为另一次独立即位。')
sup('feng_dao_chancellor',16,f,'己卯，以前太師、齊國公馮道為中書令、宏文館大學士；','《旧五代史》还记冯道同时获任宏文馆大学士。','原字“宏文馆”保留，未据此改写《资治通鉴》的职名。',relation='adds')
sup('feng_dao_chancellor',16,nw,'己卯，馮道為中書令。','《新五代史》也记己卯冯道任中书令。','同一纪日与官职相符。',field='time_original')
sup('dou_zhengu_shizhong',16,f,'以司徒兼門下侍郎、同平章事、宏文館大學士竇貞固為侍中，監修國史；','《旧五代史》还记窦贞固监修国史。','补充同次任命中的职责，不推定已经完成国史编纂。',relation='adds')
sup('su_yugui_sikong',16,f,'以左僕射、平章事、集賢殿大學士蘇禹珪為守司空、平章事；','《旧五代史》记苏禹珪任守司空、平章事。','与《资治通鉴》的司空任命对应，保留“守”字和原有平章事衔的记载。',relation='adds')
add('wang_yanchao_xuzhou_edict','王彦超派使者持敕书到徐州，守将仍不肯开关',17,'王彦超奏','不肯启关，',[('王彦超','奏报已派使者持敕书去徐州'),('巩廷美','与其他守将犹豫，不肯开关')],when='951年正月己卯任官后条下，具体奏报日未载',place='徐州',note='原文明示王彦超奏报遣使与守将拒绝开关；未具名使者不建立人物。')
add('guo_orders_xuzhou_attack','郭威下诏进兵攻打徐州',17,'诏进兵','攻之。',[('帝','下诏攻打徐州'),('王彦超','奉诏率军进攻徐州')],when='951年正月，具体下诏日《资治通鉴》未另列',place='徐州',note='本段记录进攻命令，尚未记攻克徐州。')
sup('guo_orders_xuzhou_attack',17,f,'詔王彥超率兵攻徐州。','《旧五代史》也记郭威命王彦超率兵攻徐州。','《旧五代史》把诏令列在己卯任官之后、庚辰条之前；保留原叙述位置，不当另一道已证实的诏令。')
add('guo_requests_food_inventory','郭威向王峻表示不愿奢侈养身，命他列出各地贡食',18,'帝谓王峻曰：','命峻疏四方贡献珍美食物，',[('帝','自述早年艰苦，命王峻列出各地珍美贡食'),('王峻','奉命整理各地贡食清单')],when='951年正月庚辰停止贡食诏书以前，具体交谈日未载',place='后周朝廷',note='艰苦身世与不愿奢侈为郭威在谈话中的自述；清单本段未逐项列出。')
add('guo_stops_food_tribute','郭威于庚辰下诏停止各地珍美食物进贡',18,'庚辰，','甚为无用之物。”',[('帝','下诏停止供自己享用的珍美贡食')],when='951年正月庚辰',place='后周及各地贡食州府',note='停止范围是珍美食物贡奉，没有据此推定一切税赋或所有种类进贡都被取消。')
sup('guo_stops_food_tribute',18,food,'其兩浙進細酒、海味、姜瓜，湖南枕子茶、乳糖、白沙糖、橄欖子，','《旧五代史》诏书举例列出两浙细酒、海味、姜瓜和湖南茶、糖、橄榄等贡食。','这里只补充诏书中明确列出的部分食物；“枕子茶”等原字保留，没有猜测具体品种。',relation='adds')
sup('guo_stops_food_tribute',18,food,'今後並不須進奉。諸州府更有舊例所進食味，其未該者，宜奏取進止。','《旧五代史》记所列贡食以后不必再进奉，未列出的旧例贡食须另行奏请。','这条补充表明未列贡物有另行请示程序，不将诏书泛化为全国一切进贡立即废除。',relation='adds')
add('guo_invites_practical_advice','郭威要求文武官密奏利国利民办法，不必堆砌辞藻',18,'又诏曰：','勿事辞藻。”',[('帝','要求文武官直陈利国利民之策')],when='951年正月庚辰贡食诏书之后的另一诏令，具体日未另载',place='后周朝廷',note='两道诏令分开登记；封事指密封奏章，不能解释为公开网站投稿。')
sup('guo_invites_practical_advice',18,advice,'又詔在朝文武臣僚，各上封事，凡有益國利民之事，速具以聞。','《旧五代史》本纪正文也记求言诏，要求文武臣僚上封事。','只采用本纪正文；紧随其后的《通鉴》引文不另算独立书证。')
add('wang_jun_refuses_su_house','郭威把苏逢吉住宅赐给王峻，王峻推辞不住',18,'帝以苏逢吉',None,[('帝','将苏逢吉的住宅赐给王峻'),('王峻','认为该住宅与李崧被灭族有关，推辞不住'),('苏逢吉','其旧宅被赐给王峻'),('李崧','被王峻提及为该宅相关的灭族受害者')],when='951年正月条下，具体赐宅日未载',place='苏逢吉旧宅',note='李崧灭族为王峻提及的往事，没有再建立一次951年灭族事件，也不把推辞说成王峻入住后搬出。')
add('pan_follows_khitan_north','潘聿捻在契丹北归时放弃横海镇，随军北去',19,'初，契丹主北归，','弃镇随之，',[('潘聿撚','放弃横海节度使所镇地方，跟随契丹北归'),('耶律德光','此次北归时潘聿捻随行')],year=947,when='947年契丹自中原北归期间的追述，具体离镇日未载',place='横海军至契丹北归途中',note='“初”引出947年北归背景，此时契丹君主是耶律德光；951年后文出使联络的君主是耶律阮，二人分开。')
add('pan_southwest_commander','契丹任命潘聿捻为西南路招讨使',19,'契丹主以聿撚','为西南路招讨使。',[('潘聿撚','在契丹获任西南路招讨使')],year=None,when='潘聿捻随契丹北归之后的追述，具体任命年日未载',place='契丹',note='此处未明确任命年月；原文只称契丹君主，没有补出具体任命人的姓名。')
add('khitan_pan_letter','耶律阮在北汉建立后让潘聿捻给刘承钧写信',19,'及北汉主立，','遗刘承钧书。',[('耶律阮','派潘聿捻以书信联络刘承钧'),('潘聿撚','向刘承钧送书'),('承钧','收到契丹方面的书信联络')],when='951年正月北汉建立后，具体书信日期未载',place='契丹与北汉',note='仅登记书信联络，未将其当作援军已经抵达。')
add('northern_han_requests_khitan_aid','刘崇让刘承钧复信契丹，提出仿后晋求援',19,'北汉主使承钧','契丹主大喜。',[('北汉主','让刘承钧回信，提出向契丹求援'),('承钧','奉命复信，说明继承帝位与求援意愿'),('耶律阮','收到复信后喜悦')],when='951年正月与契丹互通书信时，具体日未载',place='北汉与契丹',note='信中只是提出仿照后晋先例，未明示已经割地、称臣或达成完整盟约，不建立这些关系。')
add('northern_han_garrisons','刘崇派兵驻扎阴地、黄泽、团柏',19,'北汉主发兵','屯阴地、黄泽、团柏。',[('北汉主','派兵屯驻三处')],when='951年正月北汉建立后、丁亥任招讨使以前',place='阴地、黄泽、团柏',note='三处驻兵地点依原文登记，没有补出兵数、路线或现代坐标。')
add('chengjun_jinzhou_expedition','刘承钧任招讨使，与白从晖、李存瑰率万人进攻晋州',19,'丁亥，','从晖，吐谷浑人也。',[('承钧','获任招讨使，与两名将领率步骑万人进攻晋州'),('白从晖','以副招讨使身份率军，史载为吐谷浑人'),('李存瑰','以都监身份参加进攻')],when='951年正月丁亥',place='北汉至晋州',note='白从晖沿既有稳定档案；与早年同名将领的完整履历仍待补证。此处进攻不与冬季第二次晋州战争混合。')
sup('chengjun_jinzhou_expedition',19,jin,'河東劉崇遣偽招討使劉鈞、副招討使白截海，率步騎萬餘人來攻州城，','《旧五代史》晋州战报称招讨使刘钧、副招讨使白截海率万余人来攻。','该战报的指挥官姓名与《资治通鉴》字形不同，分别保留；没有据“白截海”建立另一个参战人物，也未新增别名。',relation='conflicts')
for code,name,newname,start,end in [('guo_chong_rename','郭崇威','郭崇','郭崇威','更名崇，'),('cao_ying_rename','曹威','曹英','曹威','更名英。')]:
 add(code,name+'改名为'+newname,20,start,end,[(name,'改名为'+newname)],when='951年正月条下，具体改名日未载',place='后周',note='原文明示改名，继续使用同一个人物key和UUID，不新建改名后的重复主体。')
 claim('person',people[name],'name',name+'改名为'+newname+'。',20,span(20,start,end),'保存改名事实；已有主体的规范名与UUID保留，后续按同一人物查找。')
add('chai_rong_zhenning','郭威任命柴荣为镇宁节度使，选朝官辅佐',21,'二月，丁酉，','选朝士为之僚佐，',[('帝','任命皇子柴荣并选朝官辅佐'),('荣','从天雄牙内都指挥使获任镇宁节度使')],when='951年二月丁酉',place='镇宁军',note='皇子指已核为郭威养子的柴荣，复用既有档案，不由称皇子改变为生父子关系。')
sup('chai_rong_zhenning',21,jin,'丁酉，以皇子天雄軍牙內都指揮使、檢校右僕射、貴州刺史榮起復為澶州節度使、檢校太保，','《旧五代史》也记丁酉柴荣任澶州节度使、检校太保。','澶州与镇宁军是此处同次任官的两种称法，保留原书名称，不填写未经核对的坐标。',relation='adds')
for code,name,office,start,end in [('wang_min_chanzhou','王敏','节度判官','以侍御史王敏','为节度判官，'),('cui_song_chanzhou','崔颂','观察判官','右补阙崔颂','为观察判官，'),('wang_pu_chanzhou','王朴','掌书记','校书郎王朴','为掌书记。')]:
 add(code,'郭威任命'+ALIASES.get(name,name)+'为柴荣的'+office,21,start,end,[('帝','为柴荣任命'+office),(name,'进入柴荣幕府担任'+office)],when='951年二月丁酉柴荣任镇宁节度使时',place='镇宁军幕府',note='依同一任官段落识别职务；不把幕府任职建立为血亲或盟友关系。')
sup('wang_min_chanzhou',21,wm,'入朝，拜侍御史。世宗鎮澶淵，太祖以敏謹厚，遂命為澶州節度判官。','《旧五代史》王敏传明确记他先任侍御史，后进入柴荣澶州幕府任节度判官。','该传前文记他是金乡人、杜重威判官，足以连接已有947年主体与951年任官，没有新建同名王敏。')
sup('cui_song_chanzhou',21,cc,'世宗鎮澶淵，擇僚佐，頌與王朴、王敏中皆中其選，以頌為觀察判官，贈金紫。','《宋史》也记崔颂进入柴荣澶州幕府任观察判官，并获赐金紫。','同场幕僚中的王敏在此写作王敏中；《旧五代史》有王敏完整履历，字形差异单列保留，不凭一个“中”字另建人。',relation='adds')
sup('wang_pu_chanzhou',21,wp,'國初，世宗鎮澶淵，朝廷以朴為記室。','《旧五代史》也记后周初年王朴进入柴荣澶州幕府任记室。','与《资治通鉴》的掌书记任职对应，保留各书职名，不提前录入即位后的升迁。')
claim('person',people['王朴'],'description','王朴字文伯，东平人。',21,'王朴，字文伯，東平人也。','籍贯与《资治通鉴》相符，字文伯由《旧五代史》补充。',source=wp)
relationship('崔协','崔颂','父亲',21,'颂，协之子；','崔协是崔颂的父亲；关系方向从父亲指向儿子。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《宋史》也记崔颂的父亲是后唐宰相崔协。',21,'崔頌，字敦美，河南偃師人。父協，後唐門下侍郎、平章事。','父亲官职和姓名明确支持同一崔协；并补记崔颂字敦美、偃师籍贯。',source=cf,relation='corroborates')
add('jinzhou_five_prongs','北汉军五路攻晋州，王晏闭城设伏反击登城军',22,'戊戌，','千馀人。',[('承钧','误以为守军胆怯，率军攀城'),('王晏','闭城后以伏兵反击，造成北汉军伤亡')],when='951年二月戊戌',place='晋州',note='北汉军伤亡千余人为史载数，不能改成千余人全部战死；闭城先于伏兵反击。')
sup('jinzhou_five_prongs',22,jin,'以今月五日五道齊攻，率州兵拒之，賊軍傷死甚眾。','《旧五代史》二月丙午战报记北汉军于当月五日五路攻城，王晏率州兵抵御。','丙午是奏报所在纪日，不当作实际攻城日；该正文未给千余人的具体数目。')
sup('jinzhou_five_prongs',22,wy,'廣順元年，劉崇侵晉州，晏閉關不出，設伏城上。幷人以為怯，競攀堞而登，晏麾伏兵擊之，顛死者甚眾，','《宋史》王晏传也记他闭关设伏，北汉军误以为怯，攀城时被伏兵击退。','采用《宋史》独立传文；《旧五代史》后附的《宋史》引文不另算一份独立确证。')
add('an_yuanbao_defects','刘承钧派安元宝烧晋州西城，安元宝转而投降',22,'承钧遣副兵马使安元宝','元宝来降。',[('承钧','派安元宝焚烧晋州西城'),('安元宝','受命烧城后向后周投降')],when='951年二月晋州战败后，具体投降日未载',place='晋州西城',note='派遣焚城与投降分清，没有补写安元宝已经完成焚烧或猜测投降原因。')
add('chengjun_moves_xizhou','刘承钧从晋州转兵进攻隰州',22,'承钧乃','移军攻隰州。',[('承钧','转军攻打隰州')],when='951年二月晋州战败及安元宝投降后',place='晋州至隰州',note='转兵先后依本段，未补行军路线或日期。')
add('changshou_capture','许迁派耿继业在长寿村迎击北汉军，俘杀程筠等人',22,'癸卯，','杀之。',[('许迁','派耿继业迎击北汉军'),('耿继业','在长寿村俘获程筠等人并杀死'),('程筠','作为北汉将领被俘后被杀')],when='951年二月癸卯',place='长寿村',note='被俘杀的是将领程筠等人，不扩大为全体敌军；未具名其他被俘者不建立身份。')
add('xizhou_holds','北汉军攻隰州数日不克，伤亡后撤退',22,'未几，','迁，郓州人也。',[('许迁','守隰州，史载籍贯为郓州'),('承钧','此前带军转攻隰州，所部攻城失败后撤退')],when='951年二月癸卯长寿村战后不久，具体撤兵日未载',place='隰州',note='数日不是明确天数；承钧参与由同段转军指挥上下文支持，不能另造一个撤兵将领。')
sup('xizhou_holds',22,xi,'隰州刺史許遷奏，河東賊軍劉筠自晉州引兵來攻州城，尋以州兵拒之，賊軍傷死者五百人，信宿遁去。','《旧五代史》记许迁奏报敌军由晋州来攻，州兵抵御后敌军伤亡五百、两宿后退去。','敌军姓名原写刘筠，与《资治通鉴》的刘承钧不同，保留异文；信宿与数日、五百人与伤亡甚众各按原书登记，不混成同一精确数字。',relation='conflicts')
reviews={16:'三项同日任官拆开；《旧五代史》补充馆职和监修国史，《新五代史》印证冯道纪日。',17:'持敕劝降、拒不开关与攻城命令分开；没有提前记录三月攻克。',18:'谈话与贡物清单、庚辰诏令、另一求言诏及赐宅推辞分开。私用字按底本保留，没有猜字；旧本纪列物与未列须奏程序限定停贡范围。李崧灭族为已发生往事，不重复录为951年事件。',19:'947年德光北归与951年阮遣书区分；潘任招讨使年日未定用null。求援意愿不等于援军已到或割地盟约。白从晖沿已有主体，完整履历待补；旧战报白截海和刘钧保留异文，不据字形另建人物。',20:'两项明确改名分别登记，沿郭崇威、曹威稳定key，改名后不另建人。',21:'柴荣复用养子身份，不因皇子称呼改变关系。王敏传提供从杜重威至澶州完整履历，复用既有主体；宋王敏中字形待核。崔颂父崔协方向明确，宋传补身份；王朴东平人与记室一致。',22:'晋州戊戌攻城与旧丙午奏报日期分清；长寿村癸卯被俘杀与未几攻隰撤军分别登记。旧刘筠原字、信宿及伤亡五百保留为异说；不把安元宝奉命烧城当已完成焚烧。'}
assert not (P/'publication.json').exists()
for n in range(16,23):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(16,23)],next_paragraph=Q[23]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原21—27行连续七段；本年剩余段落仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(16,23)],source_issues_review='已核任官、书信、战役及改名的上下文；纸本未核。宋王敏中、旧白截海及刘筠等字形保留原书，未静默改名。旧二月本纪为长段阅读分块，已回看同一TXT原段；其附引他书不另算独立证据。白从晖早年履历连接仍待补证。',plain_language_review='逐条检查人物、事件、参与角色、关系、事实说明及核对说明。展示使用现代白话，引用保留原字；建议、命令、自述、行动与追述时间分别说明，不安排固定第二轮文案重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
