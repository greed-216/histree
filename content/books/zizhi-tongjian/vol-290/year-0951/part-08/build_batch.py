# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 55–62."""
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
COMMIT='de96122983ba5859ae5249fe97bf6072d2a7e372'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['xinwudaishi-066-chu-investiture','jiuwudaishi-111-august-transfers']:
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
main_sources = ['tongjian-290-951-september-coups']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p055-p062',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-september-coups':'卷290·广顺元年·八九月与契丹楚国政变','liaoshi-005-shizong-death':'卷5·世宗本纪·天禄五年九月遇弑','liaoshi-006-muzong-accession':'卷6·穆宗本纪·应历元年即位','jiuwudaishi-111-september-report':'卷111·太祖本纪二·九月定州奏报'}
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
for n in range(55, 63):
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
    labels={'tongjian-290-951-september-coups':'卷290·广顺元年·八九月与契丹楚国政变','liaoshi-005-shizong-death':'卷5·世宗本纪·天禄五年九月遇弑','liaoshi-006-muzong-accession':'卷6·穆宗本纪·应历元年即位','jiuwudaishi-111-september-report':'卷111·太祖本纪二·九月定州奏报'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年八月至九月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_08_{len(B["claims"])+1:04d}'
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










ALIASES.update({'帝':'郭威','柴氏':'柴氏（郭威妻）','北汉主':'刘崇（刘知远弟）','契丹主':'耶律阮','齐王述律':'耶律璟','楚王':'马希萼','希崇':'马希崇','唐主':'李璟','蜀主':'孟昶','沤僧':'沤僧（契丹太宁王）','李翊':'李翊（前辰阳县令）','匡凝':'廖匡凝','帅暠':'彭师暠'})
NEW_ALIASES={'沤僧（契丹太宁王）':['沤僧'],'王得中':[],'范仁恕':[],'徐威':[],'陈敬迁':['陳敬遷'],'鲁公馆':['魯公館'],'陆孟俊':['陸孟俊'],'李观象':['李觀象'],'杨仲敏':['楊仲敏'],'魏师进':['魏師進'],'黄勍':['黃勍'],'李翊（前辰阳县令）':[],'廖偃':[],'廖匡凝':[],'刘虚己':['劉虛己'],'范守牧':[]}
NEW_DESCRIPTIONS={
'沤僧（契丹太宁王）':'《资治通鉴》称太宁王、伟王之子。951年九月与述轧作乱，杀害耶律阮，随后被拥立耶律璟的部众杀死。《辽史》本纪此役记察割作乱，具体姓名对应待核，未直接合并。',
'王得中':'上党人，北汉枢密直学士。951年九月受刘崇派遣出使契丹，祝贺新君即位，并请求援兵进攻晋州。生卒年未载。',
'范仁恕':'后蜀吏部尚书、御史中丞。951年九月任中书侍郎兼吏部尚书、同平章事。生卒年未载。',
'徐威':'楚国马步都指挥使。951年奉马希萼之命率兵防备朗州军，随后参与政变，囚禁马希萼、拥立马希崇。生卒年尚未录入。',
'陈敬迁':'楚国左右军马步使。951年与徐威等奉命在长沙城西北立寨防备朗州军，并参与政变。生卒年未载。',
'鲁公馆':'楚国水军都指挥使。951年与徐威等奉命设寨防备朗州军，并参与政变。《新五代史》同场记鲁绾，姓名是否对应待核，未直接合并。生卒年未载。',
'陆孟俊':'楚国牙内侍卫指挥使。951年与徐威等设寨防备朗州军，并参与囚禁马希萼、拥立马希崇的政变。生卒年未载。',
'李观象':'桂林人，刘言的掌书记。951年劝刘言先要求马希崇杀死马希萼旧将佐，再谋取湖南。生卒年未载。',
'杨仲敏':'楚国都军判官。951年马希崇因畏惧刘言，下令杀死杨仲敏等人，并把首级送往朗州。生卒年此前未载，死亡年为951年。',
'魏师进':'楚国牙内指挥使。951年马希崇下令杀死魏师进等人，并把首级送往朗州。此前履历及出生年未载。',
'黄勍':'楚国都押牙。951年马希崇下令杀死黄勍等人，并把首级送往朗州。此前履历及出生年未载。',
'李翊（前辰阳县令）':'楚国前辰阳县令。951年受马希崇之命把被杀将佐的首级送往朗州，遭刘言等指责后惶恐自杀。未与其他时期同名人物合并。',
'廖偃':'廖匡图之子，楚国衡山指挥使。951年与叔父廖匡凝商议扶助被废的马希萼，率庄户和乡人，与彭师暠共同拥立马希萼为衡山王。生卒年未载。',
'廖匡凝':'廖偃的叔父，楚国节度巡官。951年与廖偃商议扶助马希萼，参与在衡山拥立及组织乡兵。生卒年未载。',
'刘虚己':'马希萼在衡山的判官。951年受派遣向南唐请求援助。生卒年未载。',
'范守牧':'马希崇的客将。951年奉表向南唐请求援兵。生卒年未载。'}
NEW_DEATH_YEARS={'沤僧（契丹太宁王）':951,'杨仲敏':951,'魏师进':951,'黄勍':951,'李翊（前辰阳县令）':951}
oldaug='jiuwudaishi-111-august-transfers';oldsep='jiuwudaishi-111-september-report';ls='liaoshi-005-shizong-death';lm='liaoshi-006-muzong-accession';chu='xinwudaishi-066-chu-investiture'
add('chai_posthumous_empress','郭威追立已故妻子柴氏为皇后',55,'戊午，',None,[('帝','追立已故妻子为皇后'),('柴氏','去世后获追立皇后')],when='951年八月戊午',place='后周朝廷',note='追立说明柴氏已去世，不把951年追封当作死亡年。')
sup('chai_posthumous_empress',55,oldaug,'戊午，故夫人柴氏追立為皇后，仍令所司定謚，備禮冊命。','《旧五代史》同日记追立柴氏，并命有关部门议定谥号、准备册命礼仪。','本句尚未给定谥，不用后来谥号代替当天流程。',relation='adds')
add('li_cungui_tuanbai_attack','刘崇派李存瑰率兵从团柏进攻后周',56,'九月，','自团柏入寇。',[('北汉主','派招讨使李存瑰率兵进攻'),('李存瑰','以招讨使身份从团柏进军')],when='951年九月，具体出兵日未载',place='团柏',note='沿本年已有北汉代州防御使及攻晋州参与档案，不因职名变化新建人物。入寇是史书措辞，展示明确进攻后周。')
add('khitan_nine_springs_council','耶律阮在九十九泉与酋长商议南下，强令反对的诸部出兵',56,'契丹欲引兵会之，','契丹主强之。',[('契丹主','计划会合北汉军，强令诸部南下')],when='951年九月癸亥以前，具体议兵日未载',place='九十九泉',note='诸部不愿南下是群体记载，不推定每个具名宗王都持同样态度；计划会师不写成已经会合。')
add('shizong_killed_revolt','述轧、沤僧在火神淀作乱，杀害耶律阮',56,'癸亥，','弑契丹主而立述轧。',[('述轧','与沤僧参与政变'),('沤僧','以太宁王身份参与政变'),('契丹主','在政变中被杀害')],when='951年九月癸亥',place='新州以西火神淀',note='主书写述轧、沤僧作乱；辽本纪写察割反，分别引用，不强合人名，也不据杀害概述猜具体挥刀者。')
sup('shizong_killed_revolt',56,ls,'癸亥，祭讓國皇帝於行宮。群臣皆醉，察割反，帝遇弒，年三十四。','《辽史》同日记祭让国皇帝后群臣皆醉、察割反，世宗遇弑，年三十四。','作乱者姓名与《资治通鉴》不同，祭祀背景及年龄也为该书独立补充；未由年龄倒推生年，未把察割直接作为沤僧别名。',relation='conflicts')
sup('shizong_killed_revolt',56,oldsep,'癸亥，定州奏，契丹永康王烏裕為部下所殺。','《旧五代史》九月癸亥记定州奏报契丹永康王乌裕被部下杀害。','这是后周收到的奏报条，未列作乱者名字，不以报告日证明传递必在事件当天完成。')
claim('person',people['耶律阮'],'death_year','耶律阮于951年九月癸亥在契丹政变中被杀。',56,'癸亥，行至新州之西火神淀，燕王述轧及伟王之子太宁王沤僧作乱，弑契丹主而立述轧。','沿现有耶律阮主体补死亡事实，不改写已发布档案。')
add('revolt_installs_shuzha','作乱者杀害耶律阮后拥立述轧',56,'燕王述轧及','而立述轧。',[('述轧','政变后被拥立'),('沤僧','参与拥立述轧')],when='951年九月癸亥政变之后',place='火神淀',note='这是《资治通鉴》叙事，不把短暂拥立写成稳定在位或列出新年号。')
add('jing_escapes_south_mountain','齐王述律逃入南山',56,'契丹主德光之子齐王述律','逃入南山，',[('齐王述律','政变后逃入南山')],when='951年九月癸亥政变之后，具体逃离时刻未载',place='南山',note='述律是耶律德光之子，沿已核耶律璟主体；与太后述律氏区分。')
add('jing_defeats_rebels','拥立齐王述律的诸部攻击并杀死述轧、沤僧及其族党',56,'诸部奉述律以攻','并其族党。',[('齐王述律','被诸部拥立，对抗作乱者'),('述轧','在诸部攻击中被杀'),('沤僧','在诸部攻击中被杀')],when='951年九月契丹政变之后',place='火神淀周边',note='族党未具名，不补造亲属死亡名单。')
sup('jing_defeats_rebels',56,lm,'逆臣察割等伏誅。','《辽史》记察割等被诛。','反叛者姓名继续按各书记载保留，不能仅凭伏诛场景把所有名字视为同人。',relation='conflicts')
claim('person',people['述轧'],'death_year','述轧于951年九月政变后的反击中被杀。',56,'诸部奉述律以攻述轧、沤僧，杀之，并其族党。','沿此前燕王及册使述轧主体，死亡是《资治通鉴》的记载；姓名对照疑问保留。')
add('jing_enthroned_yingli','诸部立耶律璟为帝，改元应历',56,'立述律为帝，','改元应历。',[('齐王述律','被立为契丹皇帝，改元应历')],when='951年九月政变之后；《辽史》记丁卯即位',place='契丹',note='主书未另列即位日，辽书丁卯作为独立补证，不写成癸亥当日正式即位。')
sup('jing_enthroned_yingli',56,lm,'丁卯，即皇帝位，群臣上尊號曰天順皇帝，改元應歷。','《辽史》记丁卯即位、群臣上尊号天顺皇帝、改元应历。','正文所属穆宗本纪已核，对应耶律璟；尊号和即位日为此书补充。',relation='adds')
add('jing_enters_youzhou','耶律璟从火神淀进入幽州，派使者通知北汉',56,'自火神淀入幽州，','遣使告于北汉，',[('齐王述律','进入幽州，并派使者通知北汉')],when='951年九月即位之后',place='火神淀至幽州、北汉',note='幽州为史载名称，不用现代行政边界替代路线。')
sup('jing_enters_youzhou',56,lm,'戊辰，如南京。是月，遣劉承訓告哀於漢。','《辽史》记戊辰赴南京，并于当月派刘承训向汉告哀。','《资治通鉴》写入幽州、遣使告北汉；《辽史》具体记告哀，消息内容按两书保留。本次未给刘承训新增无明日期的主书参与。',relation='adds')
add('wang_dezhong_congratulates','刘崇派王得中祝贺契丹新君即位',56,'北汉主遣枢密直学士','贺即位，',[('北汉主','派王得中祝贺契丹新君'),('王得中','以枢密直学士身份赴契丹祝贺')],when='951年九月接到契丹使者通知以后',place='北汉至契丹')
add('han_requests_jinzhou_troops','刘崇继续以叔父称契丹新君，请援兵进攻晋州',56,'复以叔父事之，',None,[('北汉主','继续以叔父称契丹新君，请求援兵进攻晋州'),('王得中','出使贺即位，并递交援兵请求')],when='951年九月王得中出使条下',place='北汉与契丹',note='叔父是外交称谓，不建立血缘关系；请兵不是已经获得援兵。')
# The following paragraph describes the newly enthroned ruler, not the killed Yelü Ruan.
ALIASES['契丹主']='耶律璟'
add('jing_sleeping_king','史书记载耶律璟酣饮晚起，国人称他为睡王',57,'契丹主年少，','国人谓之睡王。',[('契丹主','被史书评价为好游戏、不理国事、酣饮晚起')],year=None,when='耶律璟即位后的长期概述，具体起止年份未载',place='契丹',note='每夜达旦是史家概述，不当成951年九月某一夜的精确作息记录；新君与此前被杀的耶律阮区分。')
claim('person',people['耶律璟'],'description','史书记载耶律璟酣饮、天亮入睡，中午才起，被称睡王。',57,'每夜酣饮，达旦乃寐，日中方起，国人谓之睡王。','史家概述与称号保留，不外推医学诊断或全部治理情况。')
add('jing_later_name_ming','史书记载耶律璟后来更名为明',57,'后更名明。',None,[('契丹主','据史书记载后来更名明')],year=None,when='耶律璟即位以后，改名具体年份未载',place='契丹',note='“后”未给具体年，不强系951；沿耶律璟稳定主体，保留该名字记载待进一步版本校核。')
add('fan_renshu_chancellor','孟昶任范仁恕为中书侍郎兼吏部尚书、同平章事',58,'壬申，',None,[('蜀主','任范仁恕为宰相并兼吏部尚书'),('范仁恕','由吏部尚书、御史中丞获任中书侍郎兼吏部尚书、同平章事')],when='951年九月壬申',place='后蜀')
add('xu_keqiong_mengzhou','马希萼疑许可琼怀怨，把他调任蒙州刺史',59,'楚王希萼既克长沙，','出为蒙州刺史。',[('楚王','克长沙后不赏许可琼，疑其怀怨而调出'),('许可琼','由楚国军职调任蒙州刺史')],year=None,when='950年长沙被攻克至951年九月政变以前的追述，具体任命日未载',place='蒙州',note='怨望是马希萼的怀疑，不写成已证实许可琼怀怨或已参与反叛。')
add('chu_northwest_camp','马希萼派徐威等率兵在长沙西北立寨，防备朗州军',59,'遣马步都指挥使徐威、','以备朗兵。',[('楚王','派军将在长沙城西北设寨'),('徐威','以马步都指挥使身份率兵设寨'),('陈敬迁','以左右军马步使身份率兵设寨'),('鲁公馆','以水军都指挥使身份率兵设寨'),('陆孟俊','以牙内侍卫指挥使身份率兵设寨')],when='951年九月政变以前，具体设寨日未载',place='长沙城西北隅')
add('xu_group_plans_revolt','徐威等因士卒不获安抚而怨怒，谋划作乱，马希崇知情',59,'不存抚役者，','希崇知其谋，',[('徐威','与所部将卒谋划作乱'),('陈敬迁','参与设寨将领的作乱谋划'),('鲁公馆','参与设寨将领的作乱谋划'),('陆孟俊','参与设寨将领的作乱谋划'),('希崇','知道作乱计划')],when='951年九月戊寅以前',place='长沙',note='希崇知情不等于原文此句已明确他指挥全部政变；将卒怨怒是群体记载。')
add('ma_xie_banquet_absences','马希萼宴请将吏，徐威等未参加，马希崇称病不到',59,'戊寅，','希崇亦辞疾不至。',[('楚王','宴请将吏'),('徐威','与同行将领未参加宴会'),('希崇','称病不参加宴会')],when='951年九月戊寅',place='长沙军府',note='辞疾是称病，不确认马希崇确有疾病。')
add('xu_revolt_seizes_ma_xie','徐威等以抓马为名闯入宴席袭击众人，抓住逃走的马希萼',59,'威等使人先驱','威等执囚之。',[('徐威','率部以抓马为名袭击宴席、囚禁马希萼'),('楚王','翻墙逃走，随后被抓住')],when='951年九月戊寅',place='长沙军府',description='徐威等先派人把十余匹踢咬人的马赶入府中，随后率持斧和白梃的部众以抓马为名突入宴席，击打在场众人。马希萼翻墙逃走，被他们抓住囚禁。',note='希萼逾垣后被抓，不写成成功逃脱。')
sup('xu_revolt_seizes_ma_xie',59,chu,'希崇與楚舊將徐威、陸孟俊、魯綰等謀作亂。','《新五代史》记马希崇与徐威、陆孟俊、鲁绾等共同谋划作乱。','比《资治通鉴》“希崇知其谋”更明确描述参与谋划；鲁绾与鲁公馆是否同人待核，不直接加入别名。',relation='adds')
sup('xu_revolt_seizes_ma_xie',59,chu,'希萼置酒端陽門，希崇辭以疾，威等縱惡馬十餘匹，以壯士執檛隨之，突入其府，劫庫兵，縛希萼，迎希崇以立。','《新五代史》也记用恶马掩护突入，并补记宴席在端阳门、夺取库兵和捆绑马希萼。','端阳门与夺库为该书独立细节，不把希崇称病认定为患病。',relation='adds')
add('xie_yanyong_killed','徐威等抓住谢彦颙并将他碎尸杀害',59,'执谢彦颙，','自顶及踵剉之。',[('谢彦颙','政变中被抓住并被碎尸杀害')],when='951年九月戊寅政变期间',place='长沙',note='剉之为分割身体的杀害描述，不添加原文没有的刑具与现场细节；执行者为前句威等，不指定某人亲手。')
claim('person',people['谢彦颙'],'death_year','谢彦颙在951年九月楚国政变中被杀。',59,'执谢彦颙，自顶及踵剉之。','承本段戊寅政变叙事，沿已有人物补死亡引用。')
add('ma_xichong_wuan_acting','政变者立马希崇为武安留后，纵兵抢掠',59,'立希崇','纵兵大掠。',[('希崇','被拥立为武安留后')],when='951年九月戊寅政变之后',place='长沙',note='留后是实际拥立身份，不写成获南唐或后周正式节度使任命；抢掠部众未具名，不外推被抢家庭数量。')
add('ma_xie_confined_hengshan','马希萼被囚禁于衡山县',59,'幽希萼于衡山县。',None,[('楚王','政变后被囚禁于衡山县')],when='951年九月戊寅政变之后，具体到达日见后续丙戌条',place='衡山县',note='本段概述与后文押送丙戌抵达为同一囚禁过程，不另造第二次被废。')
add('liu_yan_sends_tanzhou_army','刘言听闻马希崇被立，派兵趋向潭州',60,'刘言闻希崇立，','声言讨其篡夺之罪。',[('刘言','派兵趋向潭州，宣称讨伐马希崇篡夺')],when='951年九月马希崇被立以后',place='朗州至潭州',note='篡夺之罪是刘言出兵的公开理由，不替历史人物作司法裁决。')
add('langzhou_army_yiyang','刘言派出的军队驻扎益阳以西',60,'壬午，','军于益阳之西。',[],when='951年九月壬午',place='益阳以西',note='原文未列驻军将领，不能据派遣者就认定刘言亲自在军中。')
add('ma_xichong_sends_defenders','马希崇派两千士兵抵御刘言的军队',60,'希崇惧，癸未，','发兵二千拒之，',[('希崇','派两千士兵抵御进军')],when='951年九月癸未',place='楚国',note='只记发兵数量与目的，未提供实际交战结果。')
add('ma_xichong_langzhou_peace','马希崇向朗州求和，请求成为相邻藩镇',60,'又遣使如朗州求和，','请为邻籓。',[('希崇','遣使向刘言求和，请为邻藩'),('刘言','成为求和对象')],when='951年九月癸未条下',place='长沙至朗州',note='请为邻藩为求和条件，不推为刘言已正式接受。')
add('li_guanxiang_strategy','李观象建议刘言先让马希崇杀旧将，再图取湖南，刘言采纳',60,'掌书记桂林李观象','言从之。',[('李观象','劝刘言先要求马希崇交出旧将首级，再图湖南'),('刘言','采纳李观象的计策')],when='951年九月马希崇求和后',place='朗州',note='可兼有为李观象对计划成功的判断，不写成刘言已经占领全湖南。')
add('ma_xichong_kills_officials','马希崇因畏惧刘言，杀死杨仲敏、刘光辅等十余人',60,'希崇畏言，','等十馀人首，',[('希崇','下令斩杀旧将佐以满足刘言的要求'),('杨仲敏','以都军判官身份被杀'),('刘光辅','以掌书记身份被杀'),('魏师进','以牙内指挥使身份被杀'),('黄勍','以都押牙身份被杀')],when='951年九月求和及计策条后，具体杀害日未载',place='长沙',note='十余人为包括原文所列四人在内的总数，不分别计算四人之外再加十余人。')
claim('person',people['刘光辅'],'death_year','刘光辅在951年九月被马希崇杀害。',60,'希崇畏言，即断都军判官杨仲敏、掌书记刘光辅、牙内指挥使魏师进、都押牙黄勍等十馀人首，','沿二月入贡南唐的掌书记主体，当前身份与旧将佐背景相连，不另建同名人。')
add('li_yi_carries_heads','马希崇派前辰阳县令李翊把首级送往朗州',60,'遣前辰阳县令李翊','赍送朗州。',[('希崇','派李翊把首级送往朗州'),('李翊','以前辰阳县令身份送首级')],when='951年九月斩杀旧将佐以后',place='长沙至朗州')
add('liu_wang_doubt_heads','首级送到朗州时腐败，刘言、王逵等怀疑身份并责骂李翊',60,'至则腐败，','怒责翊，',[('刘言','怀疑腐败首级的身份，责骂使者'),('王逵','参与怀疑身份、责骂使者'),('李翊','送到首级后受到责骂')],when='951年九月李翊到朗州以后',place='朗州',note='以为非是他们的怀疑，不据此认定马希崇送的是假首级。')
add('li_yi_suicide','李翊遭责骂后惶恐自杀',60,'翊惶恐自杀。',None,[('李翊','遭刘言等责骂后惶恐自杀')],when='951年九月李翊送首级到朗州以后',place='朗州')
add('ma_xichong_governance_assessment','史书评价马希崇纵酒、为政不公，国人不支持他',61,'希崇既袭位，','国人不附。',[('希崇','被史书评价为纵酒荒淫、为政不公、言语多虚妄')],when='951年马希崇被拥立之后的概述，具体起止日未载',place='楚国',note='国人不附为史家概述，不推定每一个具名人物都拒绝支持。')
add('peng_punished_after_changsha','马希萼攻入长沙后，彭师暠虽免死，仍被杖打贬为平民',61,'初，马希萼入长沙，','犹杖背黜为民。',[('楚王','对彭师暠免死，但处以杖打并贬为平民'),('彭师暠','免死后仍遭杖打、贬为平民')],year=950,when='950年马希萼攻入长沙以后的追述，具体处分日未载',place='长沙',note='处分承此前950年攻入长沙，不系951年新发生；免死不是未受处罚。')
add('peng_escorts_ma_xie','马希崇派彭师暠押送马希萼，暗中希望他杀害马希萼',61,'希崇以为师暠必怨之，','实欲师暠杀之。',[('希崇','派彭师暠押送马希萼，并暗中希望他杀人'),('彭师暠','受命押送马希萼到衡山'),('楚王','被押送到衡山')],when='951年九月马希崇被立以后，丙戌抵达以前',place='长沙至衡山县',note='必怨之是马希崇的推测；希望杀人不是彭师暠已杀人。')
add('peng_refuses_murder','彭师暠不愿成为弑君者，反而更谨慎地侍奉马希萼',61,'师暠曰：','奉事逾谨。',[('彭师暠','拒绝成为弑君者，更谨慎地侍奉马希萼'),('楚王','受到彭师暠谨慎侍奉')],when='951年九月押送衡山期间',place='长沙至衡山',note='原文为其话语与行动，不据此建立无条件永久效忠关系。')
add('ma_xie_arrives_hengshan','马希萼在彭师暠押送下抵达衡山',61,'丙戌，','至衡山。',[('楚王','在押送途中抵达衡山'),('彭师暠','押送马希萼抵达衡山')],when='951年九月丙戌',place='衡山县',note='对应前段被幽衡山县，同一过程的抵达节点，不新增一次囚禁。')
add('liao_family_support_plan','廖偃与叔父廖匡凝商议扶助被废的马希萼',61,'衡山指挥使廖偃，','盍相与辅之！”',[('廖偃','与叔父商议扶助马希萼'),('匡凝','与侄子商议扶助马希萼')],when='951年九月马希萼抵达衡山以后',place='衡山县',note='世受马氏恩为商议者表述的理由，不补出每一代受恩细节。')
relationship('廖匡图','廖偃','父亲',61,'衡山指挥使廖偃，匡图之子也，','原文明确父子关系，方向为廖匡图是廖偃的父亲。')
relationship('廖匡凝','廖偃','叔父',61,'与其季父节度巡官匡凝谋曰：','季父为父辈的幼弟，关系方向为廖匡凝是廖偃的叔父，不误写为廖匡图的叔父。')
add('hengshan_raises_local_troops','廖偃等组织庄户和乡人为兵',61,'于是帅庄户及乡人','悉为兵，',[('廖偃','组织庄户和乡人为兵'),('匡凝','参与组织乡兵')],when='951年九月衡山扶助商议以后',place='衡山县',note='悉为兵描述被组织的人群，不夸张为全县所有居民。')
add('ma_xie_hengshan_king','廖偃等与彭师暠共同拥立马希萼为衡山王',61,'与帅暠共立希萼','为衡山王，',[('廖偃','参与拥立马希萼'),('匡凝','参与拥立马希萼'),('彭师暠','参与拥立马希萼'),('楚王','被拥立为衡山王')],when='951年九月马希萼抵达衡山后',place='衡山县',note='底本“帅暠”沿本段彭师暠对应，保留原字不另建人；地方拥立不等于已获南唐册封。')
sup('ma_xie_hengshan_king',61,chu,'希崇遣彭師暠、廖偃囚希萼於衡山，師暠奉希萼為衡山王，臣於李景。','《新五代史》也记马希萼在衡山被拥立，并向李璟称臣。','此书称廖偃与彭师暠参与囚送；《资治通鉴》明确押送者彭师暠、抵达后廖氏扶助。叙述角色及向唐称臣细节分别保留，不推一切已受唐任命。',relation='adds')
add('hengshan_defenses','衡山拥立者以县为行府，拦江设栅、编竹造战舰',61,'以县为行府，','编竹为战舰，',[],when='951年九月拥立衡山王以后',place='衡山县、江面',note='断江为栅为设置江面障碍，不画出未经考证的具体位置或战舰尺寸。')
add('peng_wuqing_jiedushi','彭师暠在衡山政权中获任武清节度使',61,'以师暠','为武清节度使，',[('彭师暠','获任武清节度使')],when='951年九月衡山拥立以后',place='衡山县',note='本地政权授职，原文未明确具名授任执行者；不称已获后周或南唐正式确认。')
add('hengshan_recruits_thousands','衡山政权募兵数日达万余人，多处州县响应',61,'召募徒众，','州县多应之。',[],when='951年九月衡山拥立后数日',place='衡山及响应州县',note='原文不给各州县名称，不虚构完整控制区域。')
add('liu_xuji_requests_tang_aid','马希萼派判官刘虚己向南唐求援',61,'遣判官刘虚己',None,[('楚王','派判官向南唐求援'),('刘虚己','作为判官出使南唐请求援助')],when='951年九月衡山立府、募兵以后',place='衡山至南唐',note='求援与援军是否到达分开。')
add('xu_group_plans_kill_xichong','徐威等担心朗州、衡山逼迫，计划杀马希崇以自解',62,'徐威等见希崇所为，','欲杀希崇以自解。',[('徐威','与同党谋划杀马希崇以求自保'),('希崇','成为杀害计划的目标')],when='951年九月朗州、衡山局势发展后',place='长沙',note='欲杀为计划，不写成马希崇已经被杀；恐祸是谋划者的判断。')
add('fan_shoumu_tang_aid','马希崇察觉危险，秘密派范守牧向南唐请求援兵',62,'希崇微觉之，','奉表请兵于唐，',[('希崇','秘密派范守牧奉表求援'),('范守牧','以客将身份奉表向南唐求兵')],when='951年九月察觉徐威等谋划以后',place='长沙至南唐')
add('bian_hao_marches_changsha','李璟命边镐率万人从袁州向长沙进军',62,'唐主命边镐',None,[('唐主','命边镐率军前往长沙'),('边镐','受命率万人从袁州向长沙进军')],when='951年九月收到马希崇求援以后',place='袁州至长沙',note='此处是命令与进军方向，未提前写成已经进占长沙或迁走马氏。')
reviews={55:'追立为死后封号，不强定柴氏死年；旧史同日印证。',56:'出兵、议兵、政变、拥立述轧、述律逃走、反击、正式即位、入幽州、告北汉及王得中贺请兵分录。新君沿已核耶律璟主体；辽书察割姓名异说不强合沤僧或述轧，丁卯即位与癸亥遇弑分清。',57:'契丹主已换为耶律璟，睡王为史家长期概述，不套当夜；后更明未给年，保留原书待核名字。',58:'壬申任相，不把吏部尚书与御史中丞旧职当多名人物。',59:'许可琼调蒙追述跨950至951，不新造夺长沙。设寨四将、谋划知情、宴缺席、恶马掩护袭击、杀谢彦颙、拥立与抢掠、幽衡山分别记录。新书鲁绾与鲁公馆不强合。',60:'讨篡夺为声言，求和条件未等于达成；李观象计策是计划，四名旧将被杀合计十余人。腐败首级遭疑不证明是假的，李翊限定前辰阳县令。',61:'希崇治理评价与950年彭师暠处分分开。杀人意图未实现，押送丙戌抵达承前幽衡山同过程。廖氏父子及叔侄方向明确；原帅暠对应彭师暠。地方拥立、建防、授职、募兵及求唐援逐项登记，不推正式册授。',62:'徐威杀希崇为计划，范守牧求援与李璟命边镐进军分开，不提前录入攻占结果。'}
assert not (P/'publication.json').exists()
for n in range(55,63):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(55,63)],next_paragraph=Q[63]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原60—67行连续八段；本年后续正文仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(55,63)],source_issues_review='原文保持底本字形，纸本未核。辽书察割与通鉴述轧沤僧政变姓名不同，未强合；辽书丁卯正式即位另作补证。鲁公馆与新书鲁绾、帅暠字形及耶律璟后更明分别说明。楚国计划与实际政变、怀疑与证实区分。',plain_language_review='首次录入逐条检查标题、人物、事件说明、角色、时间、关系与引用解释。明确国君更替及称谓指向，所有引用之外使用白话；不为句子流畅补出无载的人名、动机或结果。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
