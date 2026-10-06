# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 21–30."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,47))
COMMIT='a03e158968cf63490b7ea1d52bdaea928e33b44d'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-291-953-february-march','xinwudaishi-66-he-zhu-killed']:
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
main_sources = ['tongjian-291-953-february-march','tongjian-291-953-june-december']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0953-p021-p030',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-953-february-march':'卷291·广顺三年二月至五月','tongjian-291-953-june-december':'卷291·广顺三年六月至十二月','jiuwudaishi-113-may-953':'卷113·太祖本纪四·广顺三年五月','jiuwudaishi-113-june-953':'卷113·太祖本纪四·广顺三年六月','jiuwudaishi-113-july-953':'卷113·太祖本纪四·广顺三年七月','songshi-249-weirenpu-yuanzhao':'卷249·魏仁浦传','songshi-271-zhangcangying':'卷271·张藏英传','xinwudaishi-66-he-zhu-killed':'卷66·楚世家第六·刘言'}
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
lines = (ROOT / 'resources/derived/tongjian/291.txt').read_text().splitlines()
for n in range(21, 31):
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
    labels={'tongjian-291-953-february-march':'卷291·广顺三年二月至五月','tongjian-291-953-june-december':'卷291·广顺三年六月至十二月','jiuwudaishi-113-may-953':'卷113·太祖本纪四·广顺三年五月','jiuwudaishi-113-june-953':'卷113·太祖本纪四·广顺三年六月','jiuwudaishi-113-july-953':'卷113·太祖本纪四·广顺三年七月','songshi-249-weirenpu-yuanzhao':'卷249·魏仁浦传','songshi-271-zhangcangying':'卷271·张藏英传','xinwudaishi-66-he-zhu-killed':'卷66·楚世家第六·刘言'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺三年（953年三月至七月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0953_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=953, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='953年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0953_' + code
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
        edge = 'participation_zztj_291_0953_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0953_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','蜀主':'孟昶','冯延己':'冯延巳','张仿':'张亻放（楚军指挥使）','王殷':'王殷（后汉后周将）'})
NEW_ALIASES={'郭元昭':[],'李温玉':['李溫玉'],'魏仁涤':['魏仁滌'],'张藏英':['張藏英'],'郑珓':['鄭珓']}
NEW_DESCRIPTIONS={'郭元昭':'浚仪人，曾任解州刺史。此前因与榷盐使李温玉不和而诬报其叛乱，牵连魏仁浦。953年返京后由魏仁浦奏请任庆州刺史。《宋史》同案写郑元昭且纪时有别，保存异说，不直接改姓或另造同案人物。生卒年未载。','李温玉':'榷盐使，魏仁浦的岳父。后汉乾祐年间因儿子在李守贞据守的河中而遭郭元昭诬报、拘禁，郭威知道冤情后予以释放。《宋史》补称其管理安邑、解县两池，生卒年未载。','魏仁涤':'魏仁浦之弟。953年郭元昭返京途中在洛阳向他诉说恐惧，他认为其兄不会以私人恩怨损害公事。《宋史》同案也记这番回应，生卒年未载。','张藏英':'涿州范阳人，契丹军使，兼任榷盐制置等职。953年率军士、亲属、盐户等归附后周。《通鉴》电子本户台与旧史卢台、宋传盧䑓写法有别，按同人同役保留校核说明。生卒年留待后续逐段补录。','郑珓':'湖南指挥使。953年王逵攻入朗州时被杀。生年未载。'}
NEW_DEATH_YEARS={'郑珓':953}
oldmay='jiuwudaishi-113-may-953';oldjune='jiuwudaishi-113-june-953';oldjuly='jiuwudaishi-113-july-953';songwei='songshi-249-weirenpu-yuanzhao';songzhang='songshi-271-zhangcangying';newliu='xinwudaishi-66-he-zhu-killed'
add('shaniu_welcomes_army','杀牛族因与野鸡族不和，向讨伐野鸡族的官军送粮迎接',21,'初，杀牛族','馈饷迎奉，',[],year=None,when='952—953年讨伐野鸡族战事的回述，具体馈粮日未载',place='庆州一带',note='部族名保持史载称谓，不推定现代族属；馈饷不等于已达正式长期军事联盟。')
add('army_plunders_shaniu','官军贪图杀牛族财物和牲畜，反而抢掠他们',21,'官军利其财畜','而掠之；',[],year=None,when='讨伐野鸡族期间杀牛族迎军后的回述，具体日未载',place='庆州一带')
add('shaniu_yeji_defeat_zhang','杀牛族起兵与野鸡族合兵，在包山击败张建武',21,'杀牛族反，','于包山。',[('张建武','在包山被杀牛族与野鸡族合兵击败')],year=None,when='952—953年相关战事回述，具体败战日未载',place='包山',note='原初追述，不能按三月条自动强定败战日；合为本次反击，非终身族群关系。')
sup('shaniu_yeji_defeat_zhang',21,oldmay,'官軍不利，為蕃人迫逐，投崖墜澗而死者數百人。從阮等以兵自保，不相救應。','《旧五代史》五月条回述官军被迫逐，数百人投崖坠涧而死，折从阮等自保未救援。','五月是该条记述位置，不认定战败当日在五月；死亡数为原书记载，未把未救援改为折从阮亲自杀官军。',relation='adds')
add('guo_yanqin_removed_after_raid','郭威因郭彦钦侵扰部众引发反抗，将他免职归家',21,'帝以郭彦钦',None,[('帝','因郭彦钦侵扰导致反抗而免职'),('郭彦钦','被免职归家')],when='953年三月条下记处分，具体首次免职日未载',place='后周、庆州',note='处分阶段与战事回述分开，具体首次免职日未载；旧纪五月有归私第处理记录。')
sup('guo_yanqin_removed_after_raid',21,oldmay,'辛巳，前慶州刺史郭彥欽勒歸私第。','《旧五代史》五月辛巳记前庆州刺史郭彦钦被令回私人住所。','前刺史表明先已离任，可能为后续处置；不将此日强当主书首次免职日。',relation='adds',field='time_original')
sup('guo_yanqin_removed_after_raid',21,oldmay,'帝怒彥欽及建武，俱罷其任，','《旧五代史》还记郭彦钦与张建武因相关战事一同被罢免。','这是旧书记载的两人处分，主书此处仅具郭彦钦；不据其省略判断张建武一定未受罚。',relation='adds')
add('guo_yuanzhao_false_accusation','郭元昭因与李温玉不和、怀疑魏仁浦包庇，借李守贞反叛之机拘禁李温玉并诬报，牵连魏仁浦',22,'初，解州刺史浚仪郭元昭','事连仁浦。',[('郭元昭','以李温玉之子在河中为由拘禁并诬报'),('李温玉','被拘禁并被奏报叛乱'),('魏仁浦','被指涉嫌包庇岳父而受牵连')],year=None,when='后汉李守贞河中反叛期间的回述，具体拘禁日未载',place='解州、河中',note='元昭疑仁浦庇之为其怀疑，不认定魏仁浦确有包庇；儿子未具名不编姓名。')
sup('guo_yuanzhao_false_accusation',22,songwei,'元昭意仁浦必庇溫玉，會李守貞以河中叛，溫玉子在城中，元昭即繫溫玉以變聞。','《宋史》同案也记因李温玉之子在河中而拘禁、奏报的经过。','该传将元昭写作郑元昭，与主书郭姓不同；按同一盐务纠纷与魏氏关系说明异读，不用新姓覆盖主书。')
claim('person',people['郭元昭'],'description','《宋史》同一李温玉盐务纠纷中写郑元昭，并称其开封浚仪人；与《通鉴》郭元昭存在姓氏异读。',22,'有鄭元昭者，開封浚儀人，為安邑、解縣兩池榷鹽使，遷解州刺史。','同一籍贯、解州盐务职位及李温玉魏仁浦案件对应，保留异说；姓氏未核纸本，不自动添加郑姓别名。',source=songwei,relation='conflicts')
add('guowei_releases_wenyu','郭威当时任枢密使，知道李温玉被诬，释放并不予追究',22,'帝时为枢密使，','释不问。',[('帝','以当时枢密使身份识破诬告并释放'),('李温玉','获释且不受追究')],year=None,when='后汉河中反叛期间、郭威为枢密使时的回述',place='后汉朝廷',note='帝是后来的郭威，当时仍是后汉枢密使，不提前写成已经称帝。')
add('yuanzhao_fears_weipu_revenge','郭元昭卸任返京时害怕魏仁浦报复，在洛阳向魏仁涤诉说，魏仁涤劝他宽心',22,'至是，仁浦为枢密承旨，','况肯以私害公乎！”',[('郭元昭','卸任返京途中因旧怨担忧，向魏仁涤诉说'),('魏仁涤','认为兄长不会以私怨损害公事')],when='953年三月郭元昭到朝廷以前',place='洛阳',note='魏仁涤的劝慰为其判断，不能编此前已有魏仁浦报复命令。')
add('weipu_recommends_yuanzhao','魏仁浦奏请郭威任郭元昭为庆州刺史',22,'既至，丁亥，','以元昭为庆州刺史。',[('魏仁浦','奏请任命曾诬告自己的人'),('郭元昭','获任庆州刺史'),('帝','任郭元昭为庆州刺史')],when='953年三月丁亥',place='后周朝廷、庆州')
sup('weipu_recommends_yuanzhao',22,songwei,'顯德中，仁浦為樞密使，元昭不自安。','《宋史》将元昭返京担忧的背景放在显德中、魏仁浦任枢密使时。','与《通鉴》953年广顺三年、魏仁浦为枢密承旨的记载不同；宋传后文又说白周祖任命，纪时须继续校核，不将主线改到显德年间。',relation='conflicts',field='time_original')
sup('weipu_recommends_yuanzhao',22,songwei,'元昭至京師，仁浦果不介意，白周祖授元昭慶州刺史。','《宋史》同案也记魏仁浦不计旧怨，奏请授元昭庆州刺史。','同一任命结果印证，姓名、纪年及枢密职衔的差异仍独立保留。')
relationship('李温玉','魏仁浦','岳父',22,'温玉婿魏仁浦为枢密主事，元昭疑仁浦庇之。','温玉婿明示李温玉是魏仁浦的岳父；妻子未具名，不编妻名。')
relationship('魏仁浦','魏仁涤','兄长',22,'以告仁浦弟仁涤，','仁浦弟仁涤明示长幼，方向为魏仁浦是魏仁涤的兄长。')
add('wang_rengao_xuanhui','郭威任王仁镐为宣徽北院使兼枢密副使',22,'己丑，',None,[('王仁镐','由棣州团练使获任宣徽北院使兼枢密副使')],when='953年三月己丑',place='后周朝廷',note='太原为籍贯，不误为此前棣州团练使治所。')
add('feng_yansi_restored_chancellor','李璟再次让左仆射冯延巳兼同平章事',23,'唐主复以',None,[('唐主','恢复冯延巳同平章事职'),('冯延己','获恢复宰相职务')],when='953年三月条下，具体复任日未载',place='南唐朝廷',note='同平章事为宰相职衔，复为恢复，不新建同名冯延己人物。')
add('zhou_warns_wang_about_zhang','周行逢对王逵说何敬真与张仿有亲戚关系，临刑托付后事，劝王逵提防张仿',24,'周行逢恶武平节度副使张仿，','公宜备之。”',[('周行逢','因厌恶张仿而向王逵提出警告'),('王逵','听取对张仿的警告'),('张仿','被周行逢指称可能因何敬真之死而构成威胁')],when='953年四月庚申张仿被杀以前',place='湖南',note='亲戚及托付是周行逢所述，具体亲等未明，未据这番敌对指控直接新建确定血缘关系。')
add('wang_kills_zhang_fang','王逵召张仿饮酒，趁他醉后杀死他',24,'夏，四月，庚申，',None,[('王逵','召饮后趁醉杀死张仿'),('张仿','醉酒后被王逵杀死')],when='953年四月庚申',place='湖南',note='张仿复用已核张亻放主体，不因明确字形另造人物。')
add('chang_si_visits_court','归德节度使常思入朝',25,'丙寅，','常思入朝，',[('常思','以归德节度使兼侍中身份入朝')],when='953年四月丙寅',place='宋州至后周朝廷')
add('chang_si_moves_pinglu','郭威调常思为平卢节度使',25,'戊辰，','徙平卢节度使。',[('常思','调任平卢节度使')],when='953年四月戊辰',place='平卢军')
add('chang_si_offers_silk_debts','常思离任前奏称此前在宋州向民间放贷四万余两丝，愿进献朝廷，请官府征收',25,'将行，奏曰：','帝颔之。',[('常思','以民间所欠丝债进献，请官府征收'),('帝','当时点头答应')],when='953年四月常思将赴平卢时',place='宋州、后周朝廷',note='举丝是放贷形成债权，不解释为税粮或官府原有财政收入；帝颔之为当时回应。')
add('guo_cancels_chang_silk_debts','郭威公告免除宋州百姓所欠常思的丝债，已缴者退还',25,'五月，丁亥，',None,[('帝','取消丝债征收并退还已缴部分'),('常思','丝债被取消后仍无羞愧表示')],when='953年五月丁亥',place='宋州',note='常思无怍色为史书评价；退还是已输者，不编实际逐户退还完成名单。')
sup('guo_cancels_chang_silk_debts',25,oldmay,'丁亥，新授青州節度使常思在宋州日出放得絲四萬一千四百兩，請征入官。詔宋州給還人戶契券，其絲不征。','《旧五代史》同日记丝债四万一千四百两，令退还人户契券、不予征收。','比主书四万余更细，独立保留计量；青州为平卢治所，不当第二次不同调任。',relation='adds')
add('shu_schools_previous_decline','史书概述唐末以来各地学校废弃，作为蜀地兴学的背景',26,'自唐末以来，','所在学校废绝，',[],year=None,when='唐末以来至蜀地兴学以前的历史概述',place='各地',note='为史书的背景概述，未据此绘出所有学校逐一停办清单。')
add('wu_zhaoyi_funds_schools','毋昭裔以巨额私财营建学校，请求刻印《九经》，孟昶同意',26,'蜀毋昭裔出私财百万','蜀主从之。',[('毋昭裔','出私财建学馆并请求刻印九经'),('蜀主','批准刻印九经的请求')],year=None,when='953年五月条下回述蜀地兴学，起止年未载',place='后蜀',note='原书私财百万未明币种，展示用巨额私财，不改成银百万两；不自动将全项工程开工定为953年。')
add('shu_learning_revives','史书记蜀地兴学与刻经以后，文学教育重新兴盛',26,'由是蜀中文学复盛。',None,[],year=None,when='蜀地建学馆、刻经以后的概述，起止未载',place='后蜀',note='文学依当时学术教育语境，不缩成现代小说出版量；为主书的效果概述。')
add('zhang_cangying_surrenders','沧州奏报契丹军使张藏英归附后周',27,'六月，壬子，',None,[('张藏英','由契丹军使率众归附后周')],when='953年六月壬子奏报',place='契丹卢台至沧州',note='主本户台与旧纪卢台、宋传盧䑓字形不同，按同人同次归附校读地点展示；壬子为沧州报告，不强定全部渡海过程当天完成。')
sup('zhang_cangying_surrenders',27,oldjune,'契丹幽州榷鹽制置使兼防州刺史、知盧臺軍事張藏英，以本軍兵士及職員戶人孳畜七千頭口歸化。','《旧五代史》补载张藏英兼榷盐制置、刺史等职，并带兵士、职员、户人及牲畜合计七千头口归附。','头口是混合计数，不全部写为七千名士兵；防州与宋传坊州写法另待核，不据疑字定位坐标。',relation='adds')
sup('zhang_cangying_surrenders',27,songzhang,'周廣順三年，率內外親屬並所部兵千餘人，及煮鹽戶長幼七千餘口，牛馬萬計，舟數百艘，航海歸周。','《宋史》细分为亲属及兵千余人、盐户七千余口、牛马万计、船数百艘，并记航海归周。','与旧纪混合七千头口的计数范围和规模不同，各书分列，不相加成一个精确总数。',relation='adds')
E['zhang_cangying_received']=event('zhang_cangying_received','郭威起初疑虑张藏英归附，将他安置封禅寺，后赐衣带、钱帛等',27,'周祖頗疑之，令館於封禪寺，俄賜襲衣、銀帶、錢十萬、絹百匹、銀器、鞍勒馬。',[('张藏英','初被安置封禅寺，随后获得赏赐'),('帝','对归附者起初疑虑，后赐衣带钱帛等')],year=None,when='953年归周后至954年世宗即位以前，具体赏赐日未载',place='封禅寺、后周',source=songzhang,note='宋传俄为相对时间，未把接待与赏赐全压到六月壬子；不提前录后续世宗朝官职与战事。')
relationship_quote='初，唐明宗之世，宰相冯道、李愚请令判国子监田敏校正《九经》，刻板印卖，朝廷从之。'
add('feng_li_request_classics','冯道与李愚此前请求由田敏校正《九经》，刻板印卖',28,'初，唐明宗之世，','刻板印卖，',[('冯道','在唐明宗时期请求国子监校经刻印'),('李愚','在唐明宗时期与冯道共同请求'),('田敏','被提议负责九经校正')],year=932,when='后唐明宗时的回述；已录932年二月辛未准刻经',place='后唐国子监',note='与953年板成分开；此处主段未给申请日，932年为已有主线对应同一准刻事件，不把进献完成当开工。')
E['classics_previous_order']=event('classics_previous_order','朝廷此前批准校刻《九经》',28,relationship_quote,[],when='后唐明宗时期回述，具体准刻日见已录932年二月辛未',year=932,place='后唐国子监',stable_key='event_zztj_277_0932_orders_nine_classics_print',note='复用932年已发布的准刻事件，当前只是新出处，保持原实体档案，不重写旧文案。')
add('classics_blocks_completed','《九经》印板完成并进献朝廷',28,'丁巳，','板成，献之。',[('田敏','此前负责校经的九经印板完成并进献')],when='953年六月丁巳',place='后周朝廷、国子监',note='国子监校经依据前句同一项目，未说田敏亲手雕完全部印板。')
add('classics_spread_in_wartime','史书记《九经》刻印完成后，乱世中经书仍得到广泛传播',28,'由是，虽乱世，',None,[],when='953年印板完成后传播效果的概述，具体统计期未载',place='中原',note='传布甚广为史书效果描述，不补发行册数或识字率。')
add('zhou_governs_tanzhou_for_wang','王逵让周行逢掌管潭州，自己率军进攻朗州',29,'王逵以周行逢知潭州，','克之，',[('王逵','安排周行逢掌潭州，自率军攻取朗州'),('周行逢','替王逵掌管潭州')],when='953年六月条下，七月以前',place='潭州至朗州',note='知潭州为掌管事务，不擅自补另一份节度册授。')
add('zheng_jiao_killed','王逵攻下朗州后杀死指挥使郑珓',29,'杀指挥使郑珓，','杀指挥使郑珓，',[('王逵','攻入朗州后杀指挥使郑珓'),('郑珓','在朗州被杀')],when='953年六月条下，朗州被攻下时',place='朗州')
add('liuyan_captured_confined','王逵俘获刘言，将他关在别馆',29,'执武安节度使、同平章事刘言，',None,[('王逵','俘获刘言并将其关在别馆'),('刘言','被王逵俘获并拘禁')],when='953年六月条下，王逵攻下朗州后',place='朗州',note='武安节度使为此处主书称谓，与先前武平授职有差别，记录原职称异读；拘禁与后续被杀分开，不提前录死亡。')
sup('liuyan_captured_confined',29,newliu,'乃舉兵襲武陵，執言殺之，','《新五代史》将袭武陵、俘获并杀刘言合叙。','主书先写六月被囚、后八月另记遇害；此处保留新书概述，未把刘言死亡提前定为六月。',relation='adds')
add('wang_yin_seeks_court','王殷三次上表请求入朝',30,'秋，七月，','王殷三表请入朝，',[('王殷','三次上表请求入朝')],when='953年七月，具体三次上表日主书未载',place='邺都至后周朝廷')
add('guo_stops_wang_yin_visit','郭威怀疑王殷不诚，派使阻止他入朝',30,'帝疑其不诚，',None,[('帝','因疑虑王殷而派使阻止入朝'),('王殷','入朝行程被阻止')],when='953年七月王殷三次请求以后',place='后周朝廷、邺都',note='不诚为郭威的怀疑，不自动当王殷已有具体谋反行为。')
sup('guo_stops_wang_yin_visit',30,oldjuly,'甲申，鄴都王殷奏乞朝覲，凡三上章，允之。尋以北邊奏契丹事機，詔止其行。','《旧五代史》七月甲申条记王殷三次请求，起初获准，随后因北边报告契丹动向而被止行。','补充先准后止的过程及朝廷所述边防理由，与主书疑其不诚的动机解释并列；不擅断哪一解释完全正确。',relation='adds')

reviews={21:'初引出此前馈粮、劫掠及包山败战，具体日期未知，不强定三月。郭处分与旧五月前刺史勒归区别，旧纪补官兵伤亡及张建武也被罢。',22:'后汉旧案与953返京授职分开；魏仁涤劝慰是判断。李温玉岳父、魏兄弟方向明确；宋传郑元昭与主郭元昭、显德与广顺纪时差异独立保存。',23:'冯延己复用冯延巳，复任不当首次任相。',24:'亲戚与临刑托付来自周行逢指控，不直接建确定亲等关系；庚申醉杀独立事件，张仿保原UUID。',25:'四月入朝调镇及丝债进献请求、五月蠲债退款分开。旧纪精确丝额与契券退还作补充，放贷不是田税。',26:'唐末学校废弃背景、毋私财兴学刻经与后续文学复盛分开，起止未知；百万未标币种，展示不写银百万两。',27:'归周奏报与宋传接待赏赐分开；户台、卢台字形和防州坊州差异保存，兵户牲畜各书计数不相加，后世任职未提前。',28:'932请校刻、复用旧准刻事件、953丁巳板成进献与传播效果分开，不新造同一准刻实体；旧档案原值保留。',29:'委周掌潭、攻朗州、杀郑及囚刘分录；新书记杀的概述不把主书后八月死亡提前，武安与武平职衔异读保留。',30:'王殷请求与郭威阻止分开；旧纪先允后止、边防理由和主书疑诚解释并列。'}
assert not (P/'publication.json').exists()
for n in range(21,31):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=953,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(21,31)],next_paragraph=Q[31]['id'],next_volume=291,next_year=953,supplements=supplements,excluded_non_body=[],coverage='卷291原53—62行连续十段；953年尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,31)],source_issues_review='郭郑元昭、显德与广顺、张藏英地名职称字形及计数差异分别保留。旧准刻事件复用原档案，所有新说明使用白话，纸本异文未核。',plain_language_review='首次逐条检查新标题、说明、参与角色、关系方向和事实解释；追述、推测、指控、请求与执行分开。复用已发布实体保留原档案，未重写早期文案。引用原字不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
