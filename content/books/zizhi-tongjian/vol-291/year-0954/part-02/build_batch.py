# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 11–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,39))
COMMIT='073fb28ff5792b333432fe68e474ebdcc4b7db18'
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
main_sources = ['tongjian-291-954-february-march']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0954-p011-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
for n in range(11, 21):
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
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·显德元年（954年正月至三月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0954_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0954_' + code
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
        edge = 'participation_zztj_291_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'柴荣','世宗':'柴荣','蜀主':'孟昶','北汉主':'刘崇（刘知远弟）','刘崇':'刘崇（刘知远弟）','汉主':'刘弘熙','杨兗':'杨衮','李筠':'李筠（原名李荣）','王溥':'王溥（后周宋初）','史彦超':'史彦超（后周将领）'})
NEW_ALIASES={'吴昌岌':['吳昌岌'],'吴昌文':['吳昌文'],'安扆':[],'安嗣':[],'安裔':[],'王藻':[],'穆令均':[],'符彦能':['符彥能'],'赵晁':['趙晁']}
NEW_DESCRIPTIONS={'吴昌岌':'静海吴氏君主，吴权之子，吴昌文之兄。《通鉴》回述其继吴权之后去世，具体死亡年此段未载。《宋史》同记其弟昌文继位，但前任链条不同，保留各书记述。','吴昌文':'吴昌岌之弟。《通鉴》回述兄死后其继位，954年正月向南汉请命，获任静海节度使兼安南都护。具体生卒年未定，继位前事不强填954年。','安扆':'后蜀将安思谦之子。史书称其与两兄弟倚父势暴横，954年与父一同被孟昶杀死。生年未载。','安嗣':'后蜀将安思谦之子。史书称其与两兄弟倚父势暴横，954年与父一同被孟昶杀死。生年未载。','安裔':'后蜀将安思谦之子。史书称其与两兄弟倚父势暴横，954年与父一同被孟昶杀死。生年未载。','王藻':'后蜀翰林使。多次向孟昶指称安思谦怨望、将反，后因擅启边奏于954年被杀。《新五代史》补其延误边奏的叙述，生年未载。','穆令均':'昭义节度使李筠所属将领。954年率二千步骑迎战北汉军，被张元徽诱入伏击后杀死。生年未载。','符彦能':'前耀州团练使。954年三月随樊爱能、何徽等受命先赴泽州，为迎击北汉的军队成员。生卒年未载。','赵晁':'真定人，后周控鹤都指挥使。954年三月向郑好谦表示宜慎重进军，郑转告柴荣后，两人被拘于怀州狱。生卒年未载。'}
NEW_DEATH_YEARS={n:954 for n in ['安扆','安嗣','安裔','王藻','穆令均']}
oldfeb='jiuwudaishi-114-february-954';oldorders='jiuwudaishi-114-march-orders-954';oldcampaign='jiuwudaishi-114-campaign-march-954';newshu='xinwudaishi-64-ansiqian-killed';songwu='songshi-488-changji-changwen'
add('wu_quan_dies','静海节度使吴权此前去世',11,'初，静海节度使吴权卒，','初，静海节度使吴权卒，',[('吴权','以静海节度使身份去世')],year=None,when='954年正月请命以前的回述，具体死亡年本段未载',place='静海',note='初明确回述，不能把吴权死亡放在954年当月。')
add('wu_changji_succeeds','吴权去世后，儿子吴昌岌继位',11,'子昌岌立。','子昌岌立。',[('吴昌岌','父死后继位')],year=None,when='吴权死后、954年吴昌文请命以前的回述',place='静海')
sup('wu_changji_succeeds',11,songwu,'紹洪卒，州將吳昌岌遂居其位。','《宋史》交阯传同样记吴昌岌掌其地，但前任写作绍洪。','该书前任链条与主书吴权父子回述有别，不将绍洪自动认作吴权或改写主书父亲姓名。',relation='conflicts')
add('wu_changji_dies','吴昌岌此前去世',11,'昌岌卒，','昌岌卒，',[('吴昌岌','在弟弟继位以前去世')],year=None,when='954年吴昌文请命以前的回述，具体死亡年未载',place='静海')
add('wu_changwen_succeeds','吴昌岌死后，弟弟吴昌文继位',11,'弟昌文立。','弟昌文立。',[('吴昌文','在兄长去世后继位')],year=None,when='954年正月请命以前的回述，具体继位日未载',place='静海')
sup('wu_changwen_succeeds',11,songwu,'昌岌死，其弟昌文襲。','《宋史》也记昌岌死后弟昌文继位。','两书此层次相同，但都未在所引句给确年，不自行以现代通说填日期。')
add('wu_changwen_requests_han_titles','吴昌文向南汉请命，获任静海节度使兼安南都护',11,'是月，',None,[('吴昌文','向南汉请命并获两项职衔'),('汉主','以南汉君主身份授吴昌文职衔')],when='954年正月，具体请命及授职日未载',place='静海、安南、南汉',note='南汉授职与此前当地继位不同，未把请命写成领土已经被南汉直接接管。')
relationship('吴权','吴昌岌','父亲',11,'初，静海节度使吴权卒，子昌岌立。','子昌岌明示吴权是吴昌岌的父亲；不补母名。')
relationship('吴昌岌','吴昌文','兄长',11,'昌岌卒，弟昌文立。','弟昌文明示兄弟长幼，方向为吴昌岌是吴昌文的兄长。')
add('liuchong_requests_khitan_aid','刘崇得知郭威去世后计划大举南侵，派使向契丹请援兵',12,'北汉主闻太祖晏驾，','遣使请兵于契丹。',[('北汉主','因郭威去世而计划出兵，并向契丹求援')],when='954年正月郭威去世后至二月援兵到达前',place='北汉、契丹',note='甚喜为史书对反应的叙述；请援是行动，但计划与实际进军另分。')
add('yang_gun_arrives_jinyang','契丹派杨衮率一万余骑兵赴晋阳援北汉',12,'二月，契丹遣其武定节度使、政事令杨兗','如晋阳。',[('杨兗','以武定节度使、政事令身份率万余骑至晋阳')],when='954年二月',place='契丹至晋阳',note='主本杨兗与旧纪同役杨袞对应，复用已有杨衮；万余为史载兵数，不当精确点名册。')
sup('yang_gun_arrives_jinyang',12,oldfeb,'二月庚戌，潞州奏，河東劉崇與契丹大將軍楊袞，舉兵南指。','《旧五代史》同役记契丹大将军杨袞与刘崇举兵南下。','按同次援北汉、南指潞州行动核杨兗杨袞为异写，庚戌是潞州报告，不等于赴晋阳出发日。')
claim('person',people['杨衮'],'aliases','《通鉴》此役写杨兗，《旧五代史》作杨袞，结合同次援北汉行动保留异写。',12,'河東劉崇與契丹大將軍楊袞，舉兵南指。','沿用此前契丹将杨衮主体，不因字形多造一名将领。',source=oldfeb)
add('liuchong_and_khitan_march_south','刘崇率三万兵，任白从晖总部署、张元徽先锋，与契丹军从团柏南向潞州',12,'北汉主自将兵三万，',None,[('北汉主','自率三万兵南下'),('白从晖','任行军都部署'),('张元徽','任前锋都指挥使'),('杨兗','所率契丹军与北汉一同南下')],when='954年二月杨衮赴晋阳后',place='晋阳、团柏至潞州',note='主书三万为北汉兵，与契丹万余分列，不把全部北汉兵写作骑兵。')
# Existing 948 deaths and 948–949 relief campaigns receive source claims, not duplicate events.
pk=person('安思谦',13,'被追述曾谮杀张业、废赵廷隐',span(13,'蜀左匡圣','蜀人皆恶之。'))
claim('person',pk,'description','《通鉴》在此追述安思谦对张业被杀、赵廷隐去职的影响。',13,span(13,'蜀左匡圣','蜀人皆恶之。'),'对应此前948年已录处置，不重新造一次954年的张业死亡或赵廷隐去职。')
claim('person',pk,'description','安思谦此前应援王景崇没有立功，内心惭惧不安。',13,span(13,'蜀主使将兵救王景崇','不自安。'),'对应此前948—949年已有多阶段援军事件的概述，未把整段回述强定为954新战。')
add('an_siqian_fears_palace_guard','张业被杀后宫门加强守卫，安思谦认为孟昶怀疑自己，多有不逊言语',13,'自张业之诛，','言多不逊。',[('安思谦','因宫门加强警备而怀疑自己受猜忌')],year=None,when='948年张业被杀后至954年安思谦死前的概述',place='后蜀宫廷',note='以为疑己是安思谦所想，不把他自己的猜想当孟昶已公开指控。')
add('an_kills_soldiers_to_intimidate','安思谦主管宿卫时，多次杀士卒立威',13,'思谦典宿卫，','多杀士卒以立威。',[('安思谦','主管宿卫期间多杀士卒立威')],year=None,when='安思谦死前的宿卫任职期间，具体起止未载',place='后蜀宿卫')
add('an_kills_restored_guard','孟昶重新留用被安思谦排斥的壮年卫士，安思谦仍将他杀死，使孟昶不满',13,'蜀主阅卫士，','蜀主不能平。',[('蜀主','留用被安思谦排斥的卫士，后因其被杀不满'),('安思谦','杀死孟昶重新留用的卫士')],year=None,when='954年二月安思谦被杀前，卫士被杀日未载',place='后蜀宫廷',note='卫士未具名，不编名字与军职；孟昶不满不等于已于此刻公开处死安。')
add('an_three_sons_abuse_power','安思谦三子安扆、安嗣、安裔倚仗父亲势力横行，受到民众怨恨',13,'思谦三子，','为国人患。',[('安扆','被史书记为倚父势横行'),('安嗣','被史书记为倚父势横行'),('安裔','被史书记为倚父势横行')],year=None,when='954年三子被杀以前的一段时期概述',place='后蜀',note='为史書对三子行为评价，未给每个具体案件或民众调查数据。')
for son in ['安扆','安嗣','安裔']:relationship('安思谦',son,'父亲',13,'思谦三子，扆、嗣、裔，倚父势暴横，为国人患。','三子明示安思谦是'+son+'的父亲，未给三人长幼或同母关系。')
add('wang_zao_accuses_an','王藻多次指称安思谦怨望、将反',13,'翰林使王藻屡言','将反，',[('王藻','以翰林使身份多次指控安思谦'),('安思谦','被王藻指称将反')],when='954年二月丁巳安思谦被杀以前',place='后蜀宫廷',note='将反为王藻说法，未改为已发生叛乱。')
add('meng_kills_an_and_sons','孟昶在安思谦入朝时命壮士杀他，连同安扆、安嗣、安裔被杀',13,'丁巳，思谦入朝，','及其三子。',[('蜀主','命杀安思谦与三子'),('安思谦','入朝时被杀'),('安扆','与父亲一同被杀'),('安嗣','与父亲一同被杀'),('安裔','与父亲一同被杀')],when='954年二月丁巳',place='后蜀宫廷')
add('wang_zao_executed','王藻也因擅自拆看边疆奏报而被孟昶杀死',13,'藻亦坐擅启边奏，',None,[('王藻','因擅启边奏而被杀'),('蜀主','处死擅启边奏的王藻')],when='954年二月丁巳，与安思谦同次处置',place='后蜀宫廷')
sup('wang_zao_executed',13,newshu,'昶與翰林使王藻謀殺思謙，而邊吏有急奏，藻不以時聞，輒啟其封，昶怒之。其殺思謙也，藻方侍側，因并擒藻斬之。','《新五代史》补王藻延误边疆急奏、擅拆封，孟昶在杀安思谦时连他一并杀死。','该书保留事件因果却未单列日，丁巳来自主书；不把此前出兵应援之日挪到二人遇害时。',relation='adds')
add('north_han_camps_lianghou','北汉军驻梁侯驿',14,'北汉兵屯梁侯驿，','北汉兵屯梁侯驿，',[],when='954年二月南下潞州期间',place='梁侯驿')
add('li_jun_sends_mu_camps_taiping','李筠派穆令均率二千步骑迎敌，自己率大军在太平驿筑营',14,'昭义节度使李筠','壁于太平驿。',[('李筠','派穆令均迎战，自率主力驻太平驿'),('穆令均','率二千步骑迎战')],when='954年二月北汉军屯梁侯驿后',place='太平驿、潞州一带')
relationship('穆令均','李筠','部将',14,'昭义节度使李筠遣其将穆令均将步骑二千逆战，','其将明确穆令均是李筠的部将；限954年此次迎战记录，不推定终身所属。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='954年迎击北汉时，穆令均是李筠（原名李荣）的部将。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('zhang_lures_mu_into_ambush','张元徽诈败引穆令均追击，伏兵杀穆令均，俘杀千余士卒',14,'张元徽与令均战，','俘斩士卒千馀人。',[('张元徽','诈败引敌追击，由伏兵击杀穆令均'),('穆令均','追击时落入伏兵而被杀')],when='954年二月迎战北汉军期间',place='潞州一带',note='俘斩为被俘与被杀的合述数，不写成千余人全部阵亡。')
sup('zhang_lures_mu_into_ambush',14,oldorders,'三月丁丑，潞州奏，河東劉崇入寇，兵馬監押穆令均部下兵士為賊軍所襲，官軍不利。','《旧五代史》三月丁丑记潞州报告穆令均所部被袭、官军不利。','三月丁丑是奏报而非主书二月叙述中战斗的确定日，未将二月战事改作三月当天。',relation='adds')
add('li_jun_retreats_shangdang','李筠退回上党，守城自保',14,'筠遁归上党，','婴城自守。',[('李筠','退归上党并据城自守')],when='954年二月穆令均所部受挫后',place='上党')
claim('person',people['李筠（原名李荣）'],'aliases','李筠原名李荣，因避柴荣名讳改名。',14,'筠，即李荣也，避上名改焉。','复用此前太原控鹤指挥使李荣主体，与晚唐李筠、前蜀李筠及李昪父李荣分开；946同名控鹤档案后续还须专核。')
add('chairong_discusses_personal_campaign','柴荣欲亲率军迎战，群臣认为刘崇势弱且国丧未毕，劝派将领代征',15,'世宗闻北汉主入寇，','宜命将御之。”',[('世宗','提出亲自率军迎敌')],when='954年二月北汉入侵、三月发军以前',place='后周朝廷',note='群臣对敌情判断为其意见，不认定刘崇确实没有亲自出兵。')
add('chairong_insists_liuchong_coming','柴荣判断刘崇趁国丧、新君初立要吞并后周，认为必须亲征',15,'帝曰：“崇幸我大丧，','朕不可不往。”',[('帝','说明必须亲征的判断')],when='954年二月亲征讨论时',place='后周朝廷',note='刘崇吞天下为柴荣的对敌方意图判断，非独立军令文本。')
add('feng_dao_opposes_personal_campaign','冯道坚持反对柴荣亲征，对其比唐太宗及山压卵说法提出质疑',15,'冯道固争之，','帝不悦。',[('冯道','反对亲征并质疑柴荣的论据'),('帝','与冯道争辩并不悦')],when='954年二月亲征讨论时',place='后周朝廷')
sup('feng_dao_opposes_personal_campaign',15,oldfeb,'帝又曰：「劉崇烏合之眾，茍遇王師，必如山壓卵耳。」道曰：「不知陛下作得山否？」帝不悅而罷。','《旧五代史》也保存柴荣以山压卵比敌军、冯道质疑能否为山的对话。','传述语句稍有差别，保原字，不把一方修辞当实测军力比。')
add('wangpu_supports_campaign','王溥劝柴荣亲征，柴荣采纳',15,'惟王溥劝行，',None,[('王溥','支持亲征'),('帝','采纳王溥劝行')],when='954年二月亲征讨论后',place='后周朝廷',note='复用后周宋初王溥，不接晚唐同名人。')
add('sun_hanshao_relieved_command','孟昶加孙汉韶武信节度使、乐安郡王，解除其禁军职务',16,'三月，乙亥朔，','罢军职。',[('蜀主','给孙汉韶加官封爵并罢禁军职'),('孙汉韶','获加官封爵但解除军职')],when='954年三月乙亥朔',place='后蜀',note='加节度与罢军职同时发生，不误录为解除全部官爵。')
add('meng_distributes_guard_command','孟昶为防安思谦式跋扈，命李廷珪等十人分掌禁军',16,'蜀主惩安思谦之跋扈，',None,[('蜀主','将禁军统辖分给十人'),('李廷珪','以山南西道节度使身份参加分掌禁兵')],when='954年三月安思谦被杀后的禁军调整',place='后蜀',note='十人只明列李廷珪，不补其他九人姓名。')
add('north_han_press_luzhou','北汉乘胜继续逼近潞州',17,'北汉乘胜','进逼潞州。',[('北汉主','所部乘胜推进至潞州一带')],when='954年三月丁丑部署以前',place='潞州')
add('fu_guo_attack_enemy_rear','柴荣命符彦卿从磁州固镇出北汉军后，以郭崇为副将',17,'丁丑，诏天雄节度使符彦卿','以镇宁节度使郭崇副之；',[('帝','安排符彦卿部从敌后出击'),('符彦卿','率军从磁州固镇出北汉军后'),('郭崇','任符彦卿副将')],when='954年三月丁丑',place='磁州固镇、北汉军后',note='固镇按史载磁州地名，不直接套为现代同名县。')
relationship('郭崇','符彦卿','副将',17,span(17,'诏天雄节度使符彦卿','以镇宁节度使郭崇副之；'),'副之明确郭崇是此次出军中符彦卿的副将，限定本次954年部署。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='954年三月从磁州固镇出军时，郭崇是符彦卿的副将。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('wang_han_intercept_east_jinzhou','柴荣命王彦超自晋州东路拦击北汉，以韩通为副将',17,'又诏河中节度使王彦超','以保义节度使韩通副之；',[('帝','部署晋州东路拦击'),('王彦超','率军自晋州东路拦击北汉军'),('韩通','任王彦超副将')],when='954年三月丁丑',place='晋州东路',note='邀为拦击，不是邀请来宴。')
relationship('韩通','王彦超','副将',17,span(17,'又诏河中节度使王彦超','以保义节度使韩通副之；'),'副之明确韩通是此次拦击中王彦超的副将，限定本次954年部署。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='954年三月从晋州东路拦击北汉时，韩通是王彦超的副将。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('advance_force_to_zezhou','柴荣命樊爱能、何徽等五将先赴泽州，由向训监军',17,'又命马军都指挥使','宣微使向训监之。',[('帝','派先遣军赴泽州'),('樊爱能','任先遣领兵将领'),('何徽','任先遣领兵将领'),('白重赞','以义成节度使身份先赴泽州'),('史彦超','以郑州防御使身份先赴泽州'),('符彦能','以前耀州团练使身份先赴泽州'),('向训','受命监军')],when='954年三月丁丑',place='泽州',note='宣微疑为宣徽，展示按通行职名，原字不改；五将同行不自动建终身盟友。')
sup('advance_force_to_zezhou',17,oldorders,'命宣徽使向訓、馬軍都指揮使樊愛能、步軍都指揮使何徽、滑州節度使白重贊、鄭州防禦使史彥超、前耀州團練使符彥能等，領兵先赴澤州。','《旧五代史》同日也列向训与五将先赴泽州。','旧纪白重赞称滑州、主书称义成军，保留同一军镇两种称谓，不多建人物。')
claim('person',people['白重赞'],'description','白重赞籍贯宪州。',17,'重赞，宪州人也。','籍贯由原文明确给出，不将宪州写为义成军治所。')
add('chairong_march_amnesty','柴荣在出征前颁布大赦',18,'辛巳，',None,[('帝','颁布大赦')],when='954年三月辛巳',place='后周')
sup('chairong_march_amnesty',18,oldorders,'辛巳，制：「大赦天下，常赦所不原者，咸赦除之。','《旧五代史》同记辛巳大赦，通常不予赦免者也获赦除。','仅按该诏给出范围，未将全部后续案件终身豁免。',relation='adds')
add('feng_escorts_guowei_coffin','柴荣命冯道奉郭威灵柩赴山陵',19,'癸未，','奉梓宫赴山陵，',[('帝','命冯道护送郭威灵柩'),('冯道','奉命护送郭威灵柩至陵所')],when='954年三月癸未发令',place='大梁至山陵',note='奉命赴陵与四月实际下葬分开；未强写郭威在此已埋葬。')
add('zheng_stays_tokyo','柴荣任郑仁诲为东京留守',19,'以郑仁诲',None,[('郑仁诲','获任东京留守以留守大梁')],when='954年三月癸未，《通鉴》纪日',place='东京大梁')
sup('zheng_stays_tokyo',19,oldcampaign,'甲申，以樞密使鄭仁誨為東京留守。','《旧五代史》把郑仁诲任东京留守记在三月甲申。','癸未与甲申日差独立保留，不将主书日期无说明地覆盖。',relation='conflicts',field='time_original')
add('chairong_leaves_daliang','柴荣从大梁出发亲征北汉',20,'乙酉，','帝发大梁。',[('帝','离京亲征')],when='954年三月乙酉',place='大梁')
sup('chairong_leaves_daliang',20,oldcampaign,'乙酉，車駕發京師。','《旧五代史》同日记车驾发京师。','当前君主为柴荣，不混为郭威的西征。')
add('chairong_reaches_huaizhou','柴荣抵达怀州，希望加快行程',20,'庚寅，','帝欲兼行速进，',[('帝','到怀州后希望加速进军')],when='954年三月庚寅',place='怀州')
add('zhao_chao_advises_caution','赵晁私下向郑好谦认为敌势正盛，建议持重挫敌',20,'控鹤都指挥使真定赵晁','宜持重以挫之。”',[('赵晁','向郑好谦提出谨慎进军判断'),('郑好谦','听取赵晁的意见')],when='954年三月庚寅在怀州时',place='怀州',note='贼势方盛为赵晁的判断，不当精确军情测量。')
add('chairong_jails_zhao_zheng','郑好谦转奏慎重进军建议，柴荣追问来源，得知赵晁后将二人拘于州狱',20,'好谦言于帝，','帝命并晁械于州狱。',[('郑好谦','转奏后被追问并拘捕'),('赵晁','作为意见来源被拘捕'),('帝','追问意见来源并下令拘捕两人')],when='954年三月庚寅在怀州时',place='怀州州狱',note='言其人则生、不然必死为柴荣威胁，实际句只记下狱，不录二人已处死。')
add('chairong_passes_zezhou','柴荣经过泽州，宿营州城东北',20,'壬辰，',None,[('帝','过泽州后宿营城东北')],when='954年三月壬辰',place='泽州城东北')
sup('chairong_passes_zezhou',20,oldcampaign,'是月十八日至澤州，既晡，帝御戎服，觀兵於東北郊，距州十五里，夜宿於村舍。','《旧五代史》补记当月十八日至泽州，下午观兵于东北郊十五里外，夜宿村舍。','同一到达宿营补细节，里数为原书记述，不给现代村址；高平交战留下一段。',relation='adds')

reviews={11:'吴权死、岌继、岌死、文继为初回述，不强定954；正月请命授职单列。宋前任链绍洪差别保留，父兄关系限原文明示，不推两兄弟同母。',12:'刘崇复用北汉主体不接萧县同名人。请兵、杨万余骑赴晋阳、北汉三万合军南下分开；杨兗旧同役杨袞对应，庚戌是潞州奏报。',13:'张业与赵去职、安援景崇无功为既录前事补事实，不重建948死亡。宫门怀疑、杀卒、复籍卫士被害、三子横行、王藻指控及丁巳父子与王藻被杀分开；新书边奏细节补证。',14:'梁侯扎营、二千迎击与太平主力、诈退伏杀、李退上党分开；俘斩不全阵亡，旧三月丁丑为报告。李筠明确原荣，复用947主体，与其他同名分开。',15:'亲征提议与群臣意见、柴荣判断、冯道辩难及王溥支持分开，修辞不当实测军力。',16:'孙加官封爵与罢禁职同令，不写全部罢官；十人分典只列李廷珪，其余姓名不造。',17:'北汉推进与三路诏令分开，郭副符、韩副王两关系限定本次部署，五将同行不自动友谊；宣微宣徽字形原保。',18:'辛巳赦独立，新旧范围补充，不推以后全部免罪。',19:'奉棺赴陵为任务非已葬，郑东京留守癸未甲申日差保留。',20:'乙酉离京、庚寅怀州、赵意见郑转奏及两人下狱、壬辰泽州宿营分开；威胁不误作处死，旧十八日及东北十五里补而不造现代村址。'}
assert not (P/'publication.json').exists()
for n in range(11,21):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph=Q[21]['id'],next_volume=291,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷291原91—100行连续十段；954年跨两卷尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,21)],source_issues_review='吴氏前任链、杨兗杨袞、郑留守纪日、奏报与战斗日期分别说明；李筠同名按已核原名荣主体识别，946同职档案另待专项证据合并。纸本及异文待核。',plain_language_review='首次逐条检查展示标题、人物、角色、关系方向及事实说明；前事回述、谋划猜测、出军部署、实际伤亡和拘捕分别明示。部将副将关系注明适用战事，原文不改字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
