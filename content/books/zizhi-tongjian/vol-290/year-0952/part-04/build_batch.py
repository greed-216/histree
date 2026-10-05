# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 952 paragraphs 25–32."""
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
COMMIT='96fe3506d094c8545f18034b0950674072209b89'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-952-april-may']:
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
main_sources = ['tongjian-290-952-april-may','tongjian-290-952-june-july']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0952-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-952-june-july':'卷290·广顺二年·六月至八月及相邻追述','jiuwudaishi-112-june-952':'卷112·太祖本纪三·广顺二年六月','songshi-253-feng-jiye':'卷253·列传十二·冯继业传·父兄与继任','songshi-484-li-chongjin':'卷484·列传二百四十三·周三臣·李重进传'}
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
    labels={'tongjian-290-952-june-july':'卷290·广顺二年·六月至八月及相邻追述','jiuwudaishi-112-june-952':'卷112·太祖本纪三·广顺二年六月','songshi-253-feng-jiye':'卷253·列传十二·冯继业传·父兄与继任','songshi-484-li-chongjin':'卷484·列传二百四十三·周三臣·李重进传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺二年（952年六月至七月及相邻追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0952_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=952, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='952年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0952_' + code
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
        edge = 'participation_zztj_290_0952_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0952_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','吴氏':'吴氏（吴越顺德太夫人）','继业':'冯继业','继勋':'冯继勋','浣':'李澣','澣':'李澣','涛':'李涛','兀欲':'耶律阮'})
NEW_ALIASES={'孔仁玉':[],'颜涉':['顏涉'],'吴氏（吴越顺德太夫人）':[],'冯继业':['馮繼業'],'冯继勋':['馮繼勳'],'萧海真':['蕭海真','萧海贞','蕭海貞'],'田重霸':[],'李重进':['李重進'],'福庆长公主（郭威妹）':[]}
NEW_DESCRIPTIONS={'孔仁玉':'《旧五代史》称孔子第四十三代孙、前曲阜令、袭文宣公。952年郭威访孔颜后裔时，获赐绯服、任曲阜令。生卒年未载。','颜涉':'颜渊后裔，《旧五代史》称乡贡三礼。952年郭威访孔颜后裔时，获任曲阜主簿。未把后裔误作直接孙子，生卒年未载。','吴氏（吴越顺德太夫人）':'吴越顺德太夫人。952年六月乙未去世。本段未明示丈夫、子女，与已录钱传瓘妾、钱弘俶之母吴氏是否同一人，尚待封谥等补证，暂不合并。','冯继业':'大名人，字嗣宗，冯晖之子、冯继勋的弟弟。952年父亲去世前后杀兄，自掌朔方军府，六月获后周授朔方留后。《宋史》安排谋杀在父病时，时序独立保留。生卒年未录全。','冯继勋':'冯继业的兄长。952年朔方军继任过程中被冯继业杀害。出生年和此前官职未载。','萧海真':'契丹幽州节度使，耶律阮的妻弟，与李澣交好。952年答允李澣的内附劝说，《旧五代史》同日表述称萧海贞，按同官同使者对应。生卒年未载。','田重霸':'定州谍者。952年受李澣委托递交绢表，六月壬寅到大梁。生卒年未载。','李重进':'沧州人，福庆长公主之子，郭威的外甥，生于太原。郭威在藩镇时期的将佐，952年任恩州团练使，逐渐受重用。《宋史》还记当年内殿职务变化，具体任日未载。生卒年尚未录入。','福庆长公主（郭威妹）':'郭威的妹妹、李重进的母亲。福庆为封号，原文未给个人名字及生卒年。'}
NEW_DEATH_YEARS={'吴氏（吴越顺德太夫人）':952,'冯继勋':952}
old='jiuwudaishi-112-june-952';feng='songshi-253-feng-jiye';li='songshi-484-li-chongjin'
add('guo_worships_confucius','郭威到曲阜祭孔，认为孔子为帝王之师，行拜礼',25,'六月，乙酉朔，','遂拜之。',[('帝','到曲阜谒孔子祠，反对不拜建议并行拜礼')],when='952年六月乙酉朔',place='曲阜、孔子祠',note='陪臣与帝王师为礼制争论中的说法；底本既尊疑奠字，按祭祀语境解释，摘录不改。')
sup('guo_worships_confucius',25,old,'六月乙酉朔，帝幸曲阜縣，謁孔子祠。既奠，將致拜，','《旧五代史》同日记到曲阜谒祠，祭奠后欲行拜礼。','既奠与主书既尊字形差异保留，未悄改底本。')
sup('guo_worships_confucius',25,old,'其所奠酒器、銀爐並留於祠所。','《旧五代史》补记祭奠的酒器、银炉留在祠内。','为祭祀物品处置的补充，未编数量、价格。',relation='adds')
add('guo_repairs_confucius_shrine','郭威拜孔子墓，命修祠并禁止孔林砍柴采集',25,'又拜孔子墓，','禁孔林樵采。',[('帝','拜墓，命修葺祠宇、保护孔林')],when='952年六月乙酉朔',place='曲阜、孔林')
add('guo_appoints_confucian_descendants','郭威访孔子、颜渊后裔，任其为曲阜令、主簿',25,'访孔子、颜渊之后，','以为曲阜令及主簿。',[('帝','访后裔并授曲阜县官')],when='952年六月乙酉朔',place='曲阜',note='后裔跨多代，不等于孔子、颜渊的直接子孙；姓名由旧本纪补证。')
sup('guo_appoints_confucian_descendants',25,old,'前曲阜令、襲文宣公孔仁玉，是仲尼四十三代孫；有鄉貢《三禮》顏涉，是顏淵之後。','《旧五代史》补记两人为孔仁玉、颜涉，并说明世系与此前身份。','四十三代孙不写成直接孙子，未据世数倒推出生年。',relation='adds')
for name,role,quote in [('孔仁玉','获赐绯服、任曲阜令','仁玉賜緋，口授曲阜令，'),('颜涉','获任曲阜主簿并开始视事','顏涉授主簿，便令視事。')]:
 pk=person(name,25,role,quote,source=old);ek='participation_zztj_290_0952_confucian_descendants_'+pk
 B['person_events'].append(dict(key=ek,person_key=pk,event_key=E['guo_appoints_confucian_descendants'],role=role,status='draft'))
 claim('person_event',ek,'role',name+'：'+role+'。',25,quote,'姓名任职来自独立旧本纪，未补无证的现代墓址或祖先出生年。',source=old)
claim('person',people['孔仁玉'],'description','《旧五代史》记孔仁玉为孔子第四十三代孙，此前任曲阜令、袭文宣公。',25,'前曲阜令、襲文宣公孔仁玉，是仲尼四十三代孫；','世数按本书记载保留，不等同直接孙子，不由世数推具体出生年。',source=old)
claim('person',people['颜涉'],'description','《旧五代史》记颜涉为颜渊后裔、乡贡三礼。',25,'有鄉貢《三禮》顏涉，是顏淵之後。','后裔世数未载，乡贡三礼为当时应举身份，不改成未知的进士科。',source=old)
add('guo_leaves_yanzhou','郭威从兖州出发返京',25,'丙戌，',None,[('帝','从兖州出发返回京师')],when='952年六月丙戌',place='兖州至大梁')
sup('guo_leaves_yanzhou',25,old,'丙戌，車駕還京。','《旧五代史》同日也记郭威启程还京。','还京在此指启程，抵达日另记。')
add('wuyue_wu_lady_dies','吴越顺德太夫人吴氏去世',26,'乙未，',None,[('吴氏','以吴越顺德太夫人身份去世')],when='952年六月乙未',place='吴越',note='与此前已录钱弘俶母吴氏的封谥对应尚待补证，暂保留限定身份，不仅凭吴姓合并。')
add('chengdu_flood','成都遭大水冲淹，五千余人溺死、太庙四室损毁',27,'丁酉，','坏太庙四室。',[],when='952年六月丁酉',place='成都',description='大水进入成都，冲淹千余家，五千余人溺死，太庙四个庙室损毁。',note='户数、死亡数为史载概数；四室不是四座太庙，不补洪水实测流量与受灾坐标。')
add('shu_flood_pardon_relief','后蜀大赦并救济受灾之家',27,'戊戌，',None,[],when='952年六月戊戌',place='后蜀',note='赦罪与赈水灾两项同记，未给发放物资清单或所有受赦者名单。')
add('guo_returns_daliang','郭威抵达大梁',28,'己亥，',None,[('帝','返京抵达大梁')],when='952年六月己亥',place='大梁')
sup('guo_returns_daliang',28,old,'戊戌，車駕至自兗州。','《旧五代史》记六月戊戌自兖州返回。','主书己亥与旧书戊戌相差一日，保留纪日异说，不擅自改主书日期。',relation='conflicts')
add('feng_hui_dies','朔方节度使冯晖去世',29,'朔方节度使','冯晖卒，',[('冯晖','以朔方节度使兼中书令、陈留王身份去世')],when='952年六月；旧五代史记辛丑',place='朔方军',note='陈留王为封爵，不推死于陈留；具体死亡地未另考。')
sup('feng_hui_dies',29,old,'辛丑，以靈武節度使馮暉卒，輟視朝一日。','《旧五代史》六月辛丑记冯晖去世，郭威辍视朝一日。','灵武与朔方军镇名用法保留，辛丑为此书补充纪日。',relation='adds')
claim('person',people['冯晖'],'death_year','冯晖于952年六月去世。',29,'朔方节度使兼中书令陈留王冯晖卒，','沿已有冯晖主体补死亡事实，封爵与军镇不另建人。')
add('feng_jiye_kills_brother','冯继业杀兄冯继勋，自己主持朔方军府',29,'其子牙内都虞候继业',None,[('继业','以牙内都虞候身份杀兄并自掌军府'),('继勋','被弟弟冯继业杀害')],when='952年六月冯晖去世前后的军府继任，《宋史》时序另说明',place='朔方军',note='主书把杀兄写在父卒后，此书叙事先后与宋传父病时图杀不同，不合成确定同一天。')
relationship('冯晖','冯继业','父亲',29,'其子牙内都虞候继业杀其兄继勋，自知军府事。','其子承冯晖，明确父子方向；兄继勋冠同家族姓，未推未经明示的母亲身份。')
relationship('冯继勋','冯继业','兄长',29,'其子牙内都虞候继业杀其兄继勋，自知军府事。','其兄承冯继业，方向为冯继勋是冯继业的兄长，不误写父辈。')
sup('feng_jiye_kills_brother',29,feng,'周廣順初，暉疾，繼業圖殺其兄繼勳。暉卒，遂代其父為朔方軍留後。','《宋史》记冯晖患病时冯继业图杀兄，父卒后代为留后。','谋划与实际杀害以及父病父卒顺序分别保留，不能仅据此认定父卒前已经杀兄。',relation='adds')
claim('person',people['冯继业'],'description','冯继业字嗣宗，是大名人，早年随父任朔方及邠孟等处牙职。',29,'馮繼業，字嗣宗，大名人。父暉，朔方節度，封衛王。繼業幼敏慧，有度量，以父任補朔方軍節院使，隨父歷邠、孟，及再領朔方，皆補牙職。','引用独立传记早年履历，封卫王与主陈留王分别保留，未按年龄评价推生年。',source=feng)
add('li_huan_xiao_friendship','李澣在契丹任勤政殿学士，与幽州节度使萧海真交好',30,'太子宾客李涛之弟澣，','与幽州节度使萧海真善。',[('澣','在契丹任勤政殿学士，与萧海真交好'),('萧海真','任幽州节度使，与李澣交好')],year=None,when='李澣留契丹至952年六月表奏以前的一段时期，具体起止未载',place='契丹、幽州',note='善为交好，不推已经形成正式军事盟约。')
relationship('李涛','李澣','兄长',30,'太子宾客李涛之弟澣，在契丹为勤政殿学士，','之弟明示长幼，沿已有同一李澣、李涛主体，旧职改变不另建人。')
relationship('萧海真','耶律阮','妻弟',30,'海真，契丹主兀欲之妻弟也。','兀欲为已故耶律阮，方向表示萧海真是耶律阮的妻弟，不把当前耶律璟当此妻的丈夫。')
add('li_huan_persuades_xiao','李澣劝萧海真内附，萧海真答允',30,'浣说海南内附，','海真欣然许之。',[('澣','劝萧海真内附后周'),('萧海真','答允内附劝说')],when='952年六月壬寅田重霸到大梁以前',place='幽州',note='底本海南按上下文指海真，疑字保持原文，不误作海南地名；答允不等于幽州已交给后周。')
add('tian_chongba_carries_li_petition','李澣让田重霸递绢表，并写信向李涛说明契丹形势',30,'澣因定州谍者田重霸','二者皆利于速，度其情势，他日终不能力助河东者也。”',[('澣','托田重霸递表，写信建议后周用兵或及时议和'),('田重霸','作为定州谍者传递绢表'),('涛','成为李澣书信的收件人')],when='952年六月壬寅以前',place='契丹、定州至后周朝廷',note='童騃、无远志及不能助河东为李澣的判断，不能视为已证实的全部契丹国力；此处所说现君为耶律璟。')
add('tian_chongba_arrives_daliang','田重霸到大梁，朝廷因事务繁多没有采纳李澣方案',30,'壬寅，',None,[('田重霸','到大梁传递李澣建议')],when='952年六月壬寅',place='大梁',note='不果从是不采纳或未能实行，不写成已出兵契丹或已签和约。')
sup('tian_chongba_arrives_daliang',30,old,'壬寅，前翰林學士李澣自契丹中上表，陳奏機事，且言偽幽州節度使蕭海貞欲謀向化，帝甚嘉之。','《旧五代史》同日记李澣表奏，郭威嘉许萧海贞欲内附。','海真与海贞按同日李澣表、幽州节度使对应；附注所引宋传为间接引书，未另算独立宋史确证。',relation='adds')
add('feng_jiye_shuofang_acting','郭威任命冯继业为朔方留后',31,'辛亥，',None,[('帝','授冯继业朔方留后'),('继业','获朝廷朔方留后任命')],when='952年六月辛亥',place='朔方军',note='朝廷授任与之前自掌军府分开；留后不写成已经正式节度使。')
sup('feng_jiye_shuofang_acting',31,old,'辛亥，以朔方軍衙內都虞候馮繼業起復為朔方軍兵馬留後。','《旧五代史》同日记冯继业起复为朔方军兵马留后。','起复及此前衙内都虞候为补书内容，不推其确切服丧天数。',relation='adds')
add('wang_jun_guo_old_friendship','史书概述王峻倚仗功劳、对不获采纳的意见发怒，郭威以故旧功劳优容',32,'枢密使王峻，','峻以是益骄。',[('王峻','被史书评价为好权利、言事不允则怨'),('帝','因故旧及佐命功优容王峻，仍以兄礼称呼')],year=None,when='郭威即位后至952年七月的长期概述，具体各次谈话日未载',place='后周朝廷',note='性情与益骄为史家评价；年长及称兄不建立血缘或结义兄弟关系。')
relationship('王峻','郭威','故交',32,'帝以其故旧，且有佐命功，又素知其为人，每优容之。','原文明确故旧交往，但称兄仅为礼称，不构成兄长血缘关系。')
add('guo_promotes_trusted_officials','郭威逐渐进用郑仁诲、向训、李重进，王峻心生嫉妒',32,'副使郑仁诲、','峻心嫉之，',[('帝','逐渐重用旧日将佐'),('郑仁诲','作为副使受到重用'),('向训','作为皇城使受到重用'),('李重进','作为恩州团练使受到重用'),('王峻','对三人进用心生嫉妒')],year=None,when='郭威即位后至952年七月以前，具体各次进用日未载',place='后周朝廷',note='嫉妒为史书对王峻的心理描述，不据此说三人已结成同一派系。')
add('wang_jun_feigns_illness_resignation','王峻多次称病，请求解除枢密事务，以试探郭威意向',32,'累表称疾，','以诇帝意。',[('王峻','称病请求解任，史书记为试探君意')],when='952年七月戊子入朝以前',place='后周朝廷',note='称疾不确认具体疾病，试探是史家叙述，不作医学判断或宣布已经罢职。')
add('guo_repeatedly_reassures_wang','郭威多次派左右慰谕，王峻对使者态度强硬',32,'帝屡遣左右敦谕，','峻对使者辞气亢厉。',[('帝','多次派人慰谕王峻'),('王峻','对使者态度强硬')],when='952年七月戊子以前',place='后周朝廷与王峻府',note='使者未具名，不把后来的陈观当作这些每次使者。')
add('wang_jun_seeks_governor_guarantees','王峻致书诸道节度使求保证，诸道把信呈给郭威',32,'又遗诸道节度使书求保证，','帝惊骇久之，',[('王峻','向各道节度使求保证'),('帝','收到各道呈送的信件，感到惊骇')],when='952年七月戊子以前',place='后周各道与朝廷',note='保证的具体条文未载，不写成诸道已承诺起兵保他。')
add('guo_warns_visit_wang_house','郭威再劝王峻视事，表示若不来将亲赴其家，王峻仍不至',32,'复遣左右慰勉，','犹不至。',[('帝','劝王峻复办事务，表示可能亲去其家'),('王峻','仍未赴朝视事')],when='952年七月戊子以前',place='后周朝廷与王峻府',note='亲往为尚未执行的说法，不登记成郭威已到王府。')
add('chen_guan_counsels_guo','郭威派与王峻交好的陈观传旨，陈观建议摆出亲临府第的准备',32,'帝知枢密直学士陈观','从之。',[('帝','派陈观传旨，并采纳其建议'),('陈观','以枢密直学士身份建议声言临幸王府、备车驾相候')],when='952年七月戊子以前',place='后周朝廷',note='必不敢不来为陈观的判断；备驾并不等于已经临幸。')
add('wang_jun_returns_to_office','王峻入朝，郭威慰劳并令他视事',32,'秋，七月，戊子，','帝慰劳令视事。',[('王峻','入朝并受命继续视事'),('帝','慰劳王峻并让其办事')],when='952年七月戊子',place='后周朝廷',note='入朝节点与此前求解、拒来分开，未写成已遭罢免或被囚。')
relationship('福庆长公主（郭威妹）','李重进','母亲',32,'重进，沧州人，其母即帝妹福庆长公主也。','母子明确；同号公主不因封号相同而合并。')
relationship('郭威','福庆长公主（郭威妹）','兄长',32,'其母即帝妹福庆长公主也。','帝妹说明郭威为其兄长，长公主称号不代表她年长于郭威。')
relationship('郭威','李重进','舅父',32,'李重進，其先滄州人。周太祖之甥，福慶長公主之子也，生於太原。','宋史直接称周太祖之甥，与通鉴帝妹之子相合，方向为郭威是李重进的舅父。',source=li)
claim('person',people['李重进'],'description','《宋史》记李重进先世沧州、生于太原，晋天福中任殿直，后汉初随郭威征河中。',32,'李重進，其先滄州人。周太祖之甥，福慶長公主之子也，生於太原。晉天福中，仕為殿直。漢初，從周祖征河中。','沧州与生于太原分别为先世籍贯和出生地，不自动给生日；与主书母子及郭威将佐背景对应。',source=li)
claim('person',people['李重进'],'description','广顺二年李重进改大内都点检、权侍卫马步军都军头，领恩州团练使，后迁殿前都指挥使。',32,'二年，改大內都點檢、權侍衛馬步軍都軍頭，領恩州團練使，遷殿前都指揮使。','传记只给年度没有具体任日，作为履历保留，不把每个官职都当七月戊子同日升任。',source=li)
reviews={25:'乙酉祭孔、墓拜修祠护林与访后裔授县官、丙戌离兖分开。既尊疑奠字旧本纪印证不改源；孔仁玉四十三代与颜涉后裔不当直系孙子，旧书留祭器细节补证。',26:'吴越顺德吴氏死日明确，但未明亲属，与钱弘俶母吴氏封谥关系待证，不仅同姓强合。',27:'千余家五千死、四室损及戊戌赦赈分开，未改成四庙或现代实测洪水。',28:'主己亥与旧戊戌返京纪日不同保留。',29:'父晖死与继业杀兄自掌、宋父病谋杀与父卒代职顺序分清；父晖对继业、继勋兄对继业明确，不造未明母亲。宋传字籍早牙职与两种父封爵按书记录。',30:'澣浣已核同人，海南按前后海真指代待校不作地名；海真妻弟对已故阮，信中童主对现璟。劝内附答允、绢表兄书、壬寅田到未行方案分开，旧海贞同日同官对应，旧夹宋注不当独立宋来源。',31:'六月辛亥朝廷授留后与此前自掌军府分开，起复不推服丧日数。',32:'故交称兄不造血缘，嫉妒不造三人派系。称疾求解、慰谕不来、节镇求保证呈信、拟临府、陈策、七月戊子入朝分录。福母李及郭兄福明确，宋太祖甥印证舅父；沧先世太原生地分清。'}
assert not (P/'publication.json').exists()
for n in range(25,33):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],next_volume=290,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷290原114—121行连续八段；本年跨卷290、291，后续仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,33)],source_issues_review='引文逐字保底本，纸本未核。既尊既奠、海南海真海贞字形、郭返京纪日、冯父封爵及杀兄谋杀时序按各书保留；吴太夫人身份封谥未强合。外交称兄与血亲分开，旧史夹宋引不作独立宋正文。',plain_language_review='首次逐条核对标题、人物、角色、关系、时间及事实说明；白话明确主语，祖裔不误作直系孙子，礼称不造血缘，允诺与执行、判断与已证事实分开。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
