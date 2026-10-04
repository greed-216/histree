# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 43–50."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,60))
specs=[(d.name,d,'3b828265cfbd6215bd5d3b5d884bc8b47edf4616','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-july-aftermath','jiuwudaishi-076-li-xia-background','xinwudaishi-008-lu-date','jiuwudaishi-095-zhou-gui']:
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
main_sources = ['tongjian-281-937-july-aftermath']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p043-p050',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-097-li-jinquan-anzhou':'卷97·李金全传','jiuwudaishi-076-937-september':'卷76·晋高祖纪·天福二年九月','jiuwudaishi-010-zhu-head-burial':'卷10·梁末帝纪','xinwudaishi-062-yang-meng-death':'卷62·南唐世家','xinwudaishi-013-guo-biography':'卷13·梁家人传·末帝次妃郭氏','xinwudaishi-013-zhu-head-burial':'卷13·梁家人传·末帝次妃郭氏'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/281.txt').read_text().splitlines()
for n in range(43, 51):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-097-li-jinquan-anzhou':'卷97·李金全传','jiuwudaishi-076-937-september':'卷76·晋高祖纪·天福二年九月','jiuwudaishi-010-zhu-head-burial':'卷10·梁末帝纪','xinwudaishi-062-yang-meng-death':'卷62·南唐世家','xinwudaishi-013-guo-biography':'卷13·梁家人传·末帝次妃郭氏','xinwudaishi-013-zhu-head-burial':'卷13·梁家人传·末帝次妃郭氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '七月条下' if n==43 else '七月至八月跨月条' if n==44 else '八月至九月跨月条' if n==48 else '八月条下' if n<48 else '九月条下'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'张朏':'后晋山南东道行军司马。937年奉安从进命率军与复州兵会合，在重要道路阻截安州叛将王晖。',
'胡进':'安州将领，王晖的部将。937年在王晖准备逃往吴国时将他杀死。',
'武彦和':'后晋安州指挥使。937年参与安州军乱后，因携带大量财物被李金全设伏捕杀。他临死时质问为何首恶获赦而胁从被杀。',
'王氏（守卫军使王宏之子）':'吴国守卫军使王宏的儿子，姓名未记。937年父亲被杨濛杀死后，他率兵进攻杨濛，被杨濛射杀。',
'郭悰':'吴国侍卫军使。937年在和州杀死杨濛的妻子儿女，随后被徐诰归责，贬往池州。',
'郭氏（朱友贞妃）':'后梁末帝朱友贞的妃子。937年与安崇阮被命收葬朱友贞首级。《新五代史》记她的父亲郭归厚曾任登州刺史，她在梁亡后出家，法名誓正，居洛阳。',
'郭归厚':'后梁官员，曾任登州刺史，是末帝次妃郭氏的父亲。具体生卒年份尚未记明。'}
NEW_ALIASES={n:[] for n in NEW_DESCRIPTIONS}
NEW_ALIASES.update({'张朏':['張朏'],'胡进':['胡進'],'武彦和':['武彥和'],'郭悰':[],'郭氏（朱友贞妃）':['誓正'],'郭归厚':['郭歸厚']})
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=937 if name in ['武彦和','王氏（守卫军使王宏之子）'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=937, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when=('937年七月' if n==43 else '937年八月' if n<49 else '937年九月')+'，具体日期未记载'
    key = 'event_zztj_281_0937_' + code
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
        edge = 'participation_zztj_281_0937_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'与{a}存在原文明示的亲属关系',quote,source=source)
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
        row=dict(key=f'relationship_zztj_281_0937_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})
ALIASES.update({'徐浩':'李昪','徐诰':'李昪','唐主':'李昪','吴主':'杨溥','濛':'杨濛','弘祚':'周弘祚','王宏子':'王氏（守卫军使王宏之子）','王晖':'王晖（安州威和指挥使）','郭氏':'郭氏（朱友贞妃）','梁均王':'朱友贞'})
# 43: request to receive abdication and refusal, not an accession.
add('wang_lingmou_first_urges_abdication','王令谋赴金陵劝徐诰接受禅位，徐诰辞让',43,'吴同平章事',None,[('王令谋','以吴同平章事身份赴金陵劝徐诰接受禅位'),('徐浩','辞让接受禅位')],place='金陵',note='电子本“徐浩”与同句“诰”及前后徐诰上下文对照，识别为徐诰即李昪，不另建徐浩人物；原字保留。劝受与实际即位分开。')
# 44: actions before August report, subsequent suppression, and independent conflict.
add('an_blocks_wang_hui_route','安从进命张朏会合复州兵，阻截王晖逃往吴国',44,'山南东道节度使','于要路邀之。',[('安从进','担心王晖逃吴，命军队在要路拦截'),('张朏','率军会合复州兵在要路拦截'),('王晖','阻截对象')],when='937年八月癸巳奏报之前，具体行动日未记载',place='安州至吴国的要路',note='邀在军事语境为阻截，不是邀请；没有写成已经生擒王晖。')
sup('an_blocks_wang_hui_route',44,'jiuwudaishi-095-zhou-gui','既而襄陽安從進遣行軍司馬張朏，會復州兵於要路以僥之，','《旧五代史》周瑰传也记安从进派张朏会合复州兵在要路阻截。','僥与《资治通鉴》邀的用字差异保留，动作按上下文理解为拦截，不改摘录。')
add('wang_hui_loots_prepares_escape','王晖劫掠安州，准备逃往吴国',44,'晖大掠安州，','将奔吴，',[('王晖','劫掠安州，准备逃往吴国')],when='937年八月癸巳奏报之前，具体日期未记载',place='安州',note='劫掠已发生，逃吴为准备，没有写成已经抵达。')
add('hu_jin_kills_wang_hui','胡进杀死准备逃吴的王晖',44,'晖大掠安州，','部将胡进杀之。',[('胡进','以王晖部将身份杀死王晖'),('王晖','准备逃吴时被部将胡进杀死')],when='937年八月癸巳奏报之前，具体被杀日未记载',place='安州',note='被杀日期与奏报日期分开，不直接用癸巳作死日。')
sup('hu_jin_kills_wang_hui',44,'jiuwudaishi-097-li-jinquan-anzhou','未及境，而暉為部下所殺。','《旧五代史》李金全传记王晖在李金全尚未进入安州境内时被部下杀死。','补先后关系；该句未具名胡进，《资治通鉴》给出名字，各自证据分别保留。',relation='adds')
add('wang_hui_death_report','朝廷收到王晖被杀的奏报',44,'八月，癸巳，','以状闻。',[('帝','收到王晖被杀的奏报')],when='937年八月癸巳奏报',note='奏报人本句未具名，不把前述安从进或张朏未经证据认作奏报主体。')
add('li_jinquan_sends_rebels_capital','李金全到安州，劝说数百乱军赴朝廷',44,'李金全至安州，','悉遣诣阙；',[('李金全','到安州劝说参与军乱者，并把数百人送往朝廷')],place='安州至朝廷',note='赴阙不等于已安全抵达或已经获赦；数百没有精确人数。')
event('li_jinquan_old_massacre','《旧五代史》记李金全设伏杀死被遣赴朝廷的数百乱军',44,source_span('jiuwudaishi-097-li-jinquan-anzhou','金全至，亂軍數百人','又擒其軍校武彥和等數十人，斬之。'),[('李金全','按《旧五代史》记载，设伏杀死被遣赴朝廷的数百乱军')],source='jiuwudaishi-097-li-jinquan-anzhou',place='安州附近野外',description='《旧五代史》记李金全劝数百乱军赴朝廷，随后设伏于野外将他们全部杀死，又捕杀武彦和等数十人。这与《资治通鉴》只明确数十人被设伏捕杀的经过不同。',note='独立记录另一书明确的执行，不能因《资治通鉴》只明数十人而漏录《旧五代史》数百人；两组人数不作未经证实的合计。')
sup('li_jinquan_sends_rebels_capital',44,'jiuwudaishi-097-li-jinquan-anzhou','金全至，亂軍數百人皆不安，金全說遣赴闕，密伏兵於野，盡殺之，','《旧五代史》还说李金全把数百人遣赴朝廷后设伏将其全部杀死。','与《资治通鉴》此处只记数百人被遣赴阙保留叙事差异，《旧五代史》执行另建独立事件，不直接改《资治通鉴》事实。',relation='adds')
add('li_jinquan_executes_wu_yanhe','李金全因武彦和等持有大量财物，设伏捕杀数十人',44,'既而闻指挥使','执而斩之。',[('李金全','得知武彦和等携有大量财物，设伏捕杀'),('武彦和','与数十名同伙被设伏捕杀')],place='安州附近野外',note='“贿”在这里指财物，不误译成给李金全的贿赂；数十为被捕杀群体，不补具体人数。')
sup('li_jinquan_executes_wu_yanhe',44,'jiuwudaishi-097-li-jinquan-anzhou','及金全至，聞彥和等當為亂之日，劫掠郡城，所獲財貨，悉在其第，遂殺而奪之。','《旧五代史》补记李金全因得知武彦和等家中存有劫掠财物，杀人后夺取财物。','劫掠财物存家与《资治通鉴》携有财物分别引用，夺财是《旧五代史》明确的行动，不仅按《资治通鉴》时间先后猜贪财动机。',relation='adds')
add('wu_yanhe_protests_execution','武彦和临死质问为何首恶获赦而胁从被杀',44,'彦和且死，','何罪乎！”',[('武彦和','临死称自己等属胁从，质问处刑理由')],place='安州附近',note='首恶、胁从和无罪为武彦和临死的辩解，不直接认定每人全无责任。')
add('shi_ignores_li_jinquan_killings','石敬瑭知道李金全的行径，却未追究',44,'帝虽知金全',None,[('帝','知道李金全的行径，却未追究'),('李金全','其行径未被皇帝追究')],note='《资治通鉴》明确掩而不问，不解释为不知道或正式判无罪。')
sup('shi_ignores_li_jinquan_killings',44,'jiuwudaishi-097-li-jinquan-anzhou','高祖聞之，以姑息金全故，不究其事，尋授以旄節。','《旧五代史》也说石敬瑭因姑息李金全而不追究，后来授给节度使旄节。','姑息原因归书中说明；后续任节度使另与九月甲寅记录对应，不倒写为杀人当日已升官。',relation='adds')
# 45: ordered detention, attempted asylum, rejection and killings.
add('yang_meng_kills_wang_hong','杨濛杀死看守自己的守卫军使王宏',45,'吴历阳公','杀守卫军使王宏。',[('濛','意识到吴将亡，杀看守自己的王宏'),('王宏','以守卫军使身份被杨濛杀死')],when='937年八月甲午',place='历阳',note='杨濛沿用旧主体；王宏是已录看守杨濛的吴控鹤军使，不与王弘贽等合并。')
add('yang_meng_kills_wang_son','王宏之子率兵攻杨濛，被杨濛射杀',45,'宏子勒兵','濛射杀之。',[('王宏子','父亲被杀后率兵攻击杨濛，被射杀'),('濛','射杀率兵来攻的王宏之子')],when='937年八月甲午杀王宏之后，具体时刻未记载',place='历阳',note='儿子姓名未载，用限定主体，不能把父子两次死亡合成王宏死两次。')
relationship('王宏','王宏子','父亲',45,'宏子勒兵攻濛，濛射杀之。','本句宏子与前句王宏相接，父亲方向明确；没有补出未记姓名。')
add('yang_meng_seeks_zhou_asylum','杨濛带两名骑兵赴庐州，想依附周本',45,'以德胜节度使','欲依之。',[('濛','带两名骑兵赴庐州，想依附周本'),('周本','吴国旧臣，杨濛拟依附的对象')],place='历阳至庐州',note='二骑指随行骑兵人数，不把本人算入二骑、不添总人数；依附为意图，未获接纳。')
add('zhou_ben_wants_receive_yang','周本想见杨濛，周弘祚劝他不要接纳',45,'本闻濛至，','何为不使我见！”',[('周本','想见杨濛，并反对儿子阻拦'),('弘祚','劝父亲不要接纳杨濛'),('濛','到来后周本想见的吴宗室')],place='庐州',description='周本得知杨濛到来，想见他。周弘祚极力劝阻，周本发怒，认为故主家郎君既来，自己应当相见。',note='郎君称呼为故主家子弟，不建杨濛与周本的血亲关系。')
relationship('周本','弘祚','父亲',45,'本闻濛至，将见之，其子弘祚固谏，','主文明示其子，复用已有同向父亲关系。')
add('zhou_hongzuo_sends_yang_jiangdu','周弘祚关门阻止周本出见，捕杨濛送江都',45,'弘祚合扉','送江都。',[('弘祚','关门阻止父亲出见，派人捕杨濛送江都'),('周本','被儿子关门阻止出见'),('濛','在门外被捕，送江都')],place='庐州至江都')
sup('zhou_hongzuo_sends_yang_jiangdu',45,'xinwudaishi-062-yang-meng-death','祚閉門遮本不得出，縛濛送金陵，見殺。','《新五代史》记周弘祚阻父出门，绑杨濛送金陵，被杀。','与《资治通鉴》送江都、后在采石被杀不同，分别保留行程和地点，不强合成同一段送达地点。',relation='conflicts')
add('li_bian_has_yang_meng_killed','徐诰派使者称诏杀杨濛于采石',45,'徐诰遣使','杀濛于采石，',[('徐诰','派使者称奉诏命，将杨濛杀于采石'),('濛','在采石被使者杀害')],place='采石',note='称诏只表示使者以诏命名义行事，未有吴主独立签发证据，不直接记杨溥亲自下令。')
add('yang_meng_posthumous_degradation','杨濛被追废为庶人，剔除宗室名籍',45,'追废为','绝属籍。',[('濛','被追废为庶人并剔除宗室名籍')],note='“悖逆”是处分时的官方称号，不作为网站自行对人物道德定论；追废是死后处分。')
add('guo_cong_kills_yang_family','郭悰在和州杀死杨濛的妻子儿女',45,'侍卫军使郭悰','杀濛妻子于和州，',[('郭悰','以侍卫军使身份杀死杨濛妻子儿女'),('濛','其妻子儿女在他死后被杀')],place='和州',note='妻子在此为妻与子女，不只指妻；姓名、人数未记，不捏造亲属主体。')
add('li_bian_demotes_guo_cong','徐诰将杀害杨濛家人的责任归给郭悰，贬他去池州',45,'诰归罪于悰，',None,[('徐诰','把杀杨濛家人责任归给郭悰并贬他'),('郭悰','被归责后贬往池州')],place='池州',note='归罪不等于已证明徐诰完全不知情；《资治通鉴》未具体说明贬后的官衔，不补为池州刺史。')
# 46–47: amnesty and redemption policy, not proof all people arrived home.
add('shi_amnesty_three_rebel_groups','石敬瑭赦免张从宾、符彦饶、王晖未被处死的同党',46,'乙巳，',None,[('帝','赦免三起军乱中尚未被处死的同党'),('张从宾','其未被处死同党在赦令范围内'),('符彦饶','其未被处死同党在赦令范围内'),('王晖','其未被处死同党在赦令范围内')],when='937年八月乙巳',note='三人本人均已死，作为赦令涉及的旧军乱对象参与，不写成三人获赦复生。')
sup('shi_amnesty_three_rebel_groups',46,'jiuwudaishi-076-li-xia-background',source_span('jiuwudaishi-076-li-xia-background','應自張從賓作亂以來，','一切不問。'),'《旧五代史》赦令也列张从宾及张延播的胁从者、符彦饶随身军将、安州王晖同党，已诛者以外全部释放。','使用八月乙巳诏正文，不把仅涉这三起军乱的赦令扩成所有重大犯罪均无条件获赦。')
sup('shi_amnesty_three_rebel_groups',46,'xinwudaishi-008-lu-date',source_span('xinwudaishi-008-lu-date','乙巳，赦非死罪囚','王暉餘黨。'),'《新五代史》也记八月乙巳赦免张从宾、符彦饶、王晖余党。','独立本纪确认赦令；非死罪囚为同时另列范围，不混入余党是否已被处死的界限。')
add('shi_redeems_people_from_khitan','石敬瑭派使者赎回梁唐以来流落契丹的士民',47,'梁、唐以来，',None,[('帝','派使者赎回出使或被掳而滞留契丹的士民')],description='对后梁、后唐以来因出使或被掳而滞留契丹的士民，石敬瑭派使者赎回，让他们回到各自家庭。',place='契丹至中原',note='梁唐以来限定待赎人员的经历，不将赎回行动定到梁唐。未列具体回归名单，不断言每人已经回到家。')
sup('shi_redeems_people_from_khitan',47,'jiuwudaishi-076-li-xia-background','應自梁朝、後唐以來，前後奉使及北京沿邊管界擄掠往向北人口，宜令官給錢物，差使賫持，往彼收贖，放歸本家','《旧五代史》乙巳诏要求官府提供钱物，派使者北上赎人并放归本家。','补赎回的制度安排；《资治通鉴》概述派使，《旧五代史》明为诏令，不能仅凭此证明所有赎回已完成。',relation='adds')
# 48: refusal to retire, final exhortation, August abdication decree, September death.
add('wang_lingmou_refuses_retirement','王令谋虽年老有病，仍不肯在齐王大事完成前退休',48,'吴司徒','吾何敢自安！”',[('王令谋','年老有病，拒绝退休建议')],year=None,when='齐王受禅筹备期间，劝退具体日期未记载',description='王令谋年老有病，牙齿已脱落。有人劝他退休，他表示齐王的大事还未完成，自己不敢先求安逸。',note='列举官衔为人物当时身份，不据此新增所有官职都在本日任命；匿名劝退者不造姓名。')
add('wang_lingmou_dying_urges_abdication','王令谋病重时仍极力劝徐诰接受禅位',48,'疾亟，','力劝徐诰受禅。',[('王令谋','病重时极力劝徐诰接受禅位'),('徐诰','受到王令谋劝进')],when='937年八月受禅诏之前，具体劝进日未记载',note='与七月到金陵劝进为后续病重阶段，不重复同一次行程。')
add('wu_decrees_abdication_qi','杨溥下诏将帝位禅让给齐国',48,'是月，','禅位于齐。',[('吴主','下诏将帝位禅让给齐国'),('徐诰','齐国统治者，禅位对象')],when='937年八月，原文是月',note='是月承接八月，下诏禅位与十月徐诰正式即位分开，不把诏令写成当月已经完成全部受禅礼。')
add('li_decheng_officials_urge_qi','李德诚再赴金陵，率百官劝徐诰即位',48,'李德诚等复诣','百官劝进，',[('李德诚','再次赴金陵，率百官劝进'),('徐诰','接受劝进的齐国统治者')],when='937年八月禅位诏之后',place='金陵',note='复表示再次，不把此前同类劝进删掉或合为一次。')
add('song_qiqiu_declines_petition_signature','宋齐丘没有在劝进表上署名',48,'宋齐丘不署表。','宋齐丘不署表。',[('宋齐丘','没有在劝进表上署名')],when='937年八月劝进期间',note='只明确未署表，不推断宋齐丘与所有官员断绝私人关系。')
add('wang_lingmou_dies','王令谋去世',48,'九月，癸丑，',None,[('王令谋','去世')],when='937年九月癸丑',note='九月癸丑明确死亡日期，不因本段前半八月事而错定为八月。')
# 49–50: appointment and the change of burial agents.
add('li_jinquan_anyuan_appointment','李金全被任命为安远节度使',49,'甲寅，',None,[('李金全','被任命为安远节度使')],when='937年九月甲寅',place='安州、安远军')
sup('li_jinquan_anyuan_appointment',49,'jiuwudaishi-076-937-september','以右領軍衛上將軍、權知安州軍州事李金全為安遠軍節度使。','《旧五代史》在九月甲寅条下也记李金全由权知安州军州事被任命为安远军节度使。','独立确认正式任命，与七月赴安州巡检、八月杀乱军区别。')
add('shi_reassigns_zhu_head_burial','石敬瑭改命安崇阮与郭氏收葬朱友贞首级',50,'娄继英',None,[('帝','在娄继英未及完成安葬便被处死后，另命安崇阮与郭氏办理'),('娄继英','原拟收葬，但未及完成便被处死'),('安崇阮','以右卫上将军身份被命收葬朱友贞'),('郭氏','以朱友贞故妃身份被命参与收葬'),('梁均王','已死，其首级被重新安排收葬')],description='娄继英先前请求收葬朱友贞首级，却在完成安葬前被处死。石敬瑭随后命后梁旧臣安崇阮和朱友贞的故妃郭氏办理收葬。',note='这段澄清五月请首而葬的后续尚未完成；当前另派办理，不等于新的下葬日已确认。郭氏参与收葬，不从同葬一词推出她在此刻已经去世。')
sup('shi_reassigns_zhu_head_burial',50,'jiuwudaishi-010-zhu-head-burial','時右衛上將軍婁繼英請之，會繼英得罪，乃詔左衛上將軍安崇阮收葬焉。','《旧五代史》也记娄继英请收首级，得罪后改诏安崇阮收葬，官衔写左卫上将军。','与《资治通鉴》右卫上将军的官衔不同，保留差异，不改原字。')
sup('shi_reassigns_zhu_head_burial',50,'xinwudaishi-013-zhu-head-burial',source_span('xinwudaishi-013-zhu-head-burial','晉天福三年，','與妃同葬之。'),'《新五代史》记天福三年准亲属收葬首级，并命安崇阮与郭氏同葬朱友贞首级。','《新五代史》记天福三年，《资治通鉴》本年为天福二年，年份异说分别保留；同葬之指两人共同办理，后句另说妃卒洛阳而未列年，不推出郭氏当年死。',relation='conflicts',field='time_original')
relationship('郭氏','梁均王','妃嫔',50,Q[50]['text'],'王故妃郭氏明确是朱友贞的妃子。方向为郭氏是朱友贞的妃嫔，不因妃称谓强写成正妻或皇后。')
relationship('郭归厚','郭氏','父亲',50,'次妃郭氏，父歸厚，事梁為登州刺史。','父归厚结合郭氏姓氏识别郭归厚，不与其他郭氏父亲合并；方向为郭归厚是郭氏的父亲。',source='xinwudaishi-013-guo-biography')
claim('person',people['郭氏（朱友贞妃）'],'description','《新五代史》记郭氏为朱友贞的次妃，父郭归厚曾任登州刺史；郭氏梁亡后出家，法名誓正，居洛阳。',50,source_span('xinwudaishi-013-guo-biography','次妃郭氏，','居于洛陽。'),'《新五代史》补父职、梁亡后出家法名和居所；937收葬角色另由本批《资治通鉴》引用证明，不把后来未定死亡提早。',source='xinwudaishi-013-guo-biography')
claim('person',people['郭归厚'],'description',NEW_DESCRIPTIONS['郭归厚'],50,'次妃郭氏，父歸厚，事梁為登州刺史。','明确父职，具体任职年月、生卒未知，不推为937仍任登州。',source='xinwudaishi-013-guo-biography')
# Attach the later evidence to the original May request without replacing its archive.
old_key='event_zztj_281_0937_lou_buries_zhu_head'
old_event=next(r for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for r in json.loads(f.read_text())['events'] if r['key']==old_key)
B['events'].append(dict(old_event,status='draft'));reused.add(old_key);used.setdefault(50,[]).append(old_key)
claim('event',old_key,'description','《资治通鉴》九月条说明娄继英在完成收葬前已被处死，五月的请求没有由他完成。',50,'娄继英未及葬梁均王而诛死，','这是对五月请首而葬的后续澄清，原档案保持，公开展示中的完成表述另作守卫勘误。')
profiles={
'张朏':(44,'山南东道节度使','于要路邀之。'),
'胡进':(44,'晖大掠安州，','部将胡进杀之。'),
'武彦和':(44,'既而闻指挥使','何罪乎！”'),
'王氏（守卫军使王宏之子）':(45,'宏子勒兵','濛射杀之。'),
'郭悰':(45,'侍卫军使郭悰',None)}
for name,(n,start,end) in profiles.items():claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'简介只据明确的身份与行动，未记生卒与家世不补。')
for raw,n,quote in [('王晖',44,'晖大掠安州，将奔吴，部将胡进杀之。'),('武彦和',44,'既而闻指挥使武彦和等数十人挟贿甚多，伏兵于野，执而斩之。'),('王宏',45,'吴历阳公濛知吴将亡，甲午，杀守卫军使王宏。'),('王宏子',45,'宏子勒兵攻濛，濛射杀之。'),('杨濛',45,'徐诰遣使称诏杀濛于采石，'),('王令谋',48,'九月，癸丑，令谋卒。')]:
 name=ALIASES.get(raw,raw);claim('person',people[name],'death_year',f'{name}于937年死亡。',n,quote,'《资治通鉴》明示本年死亡，具体日期未记者不以奏报日或相邻纪日替代；旧人物档案不覆写，另补死年事实。')
reviews={43:'徐浩疑徐诰用字，结合同句诰及上下文复用李昪，不造同名人；劝受和辞让不是已即位。',44:'安从进预拦截、王掠逃准备、胡杀及八月癸巳奏报分开。主遣数百赴阙、伏杀数十与旧数百伏杀另数十冲突保留；贿是财物，临死胁从为武辩解。旧明杀夺财，不能仅录建议漏实际；皇帝知道不问。',45:'杨杀王宏、宏子攻而射死、二骑庐州求依、周欲接被子关门、捕送江都与新金陵异说分别录。称诏不造吴主亲令，采石死与新概述被杀保留；悖逆处分不作道德断语。郭杀妻儿后归责贬池州，不填官衔。',46:'乙巳赦未诛同党，三首领已死不作本人获赦。旧诏正文独立确认。',47:'梁唐是被赎者旧经历，非赎回日期；派使赎与全部抵家区别，旧给钱物诏补安排。',48:'劝退不从在受禅前具体日期未知；八月病重劝诰、吴诏禅齐、李率官再劝、宋不署表分开。九月癸丑王死明确跨月；官衔是身份不是本段全部新授。',49:'九月甲寅李金全正式节度任命，旧本纪同日核；与此前巡检和杀乱军分开。',50:'主明确娄未及葬便诛，改命安郭办理；早五月并安葬表述需窄幅勘误，不重写整批。旧安左卫/主右卫异，新天福三年/主二年异保留。郭共同办理，不推出此日合葬郭尸或郭死亡。妃嫔方向明确，父归厚独立新传证。'}
assert not (P/'publication.json').exists()
for n in range(43,51):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(43,51)],next_paragraph=Q[51]['id'],next_volume=281,next_year=937,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第43—50段，原第48—55行，王令谋劝受、安州善后、杨濛遇害、赦乱党及赎契丹士民、八月禅位诏、九月王令谋卒与李金全任官、朱友贞收葬改派。937年尚未完成。',source_issues_review='原文逐行回查。徐浩与诰同句及上下文核为李昪；张朏、郭悰、武彦和原名保留；新旧死亡地点、人数、收葬年份和官衔异说独立引用。新卷13末帝次妃郭氏、卷62南唐世家以及旧卷97李金全传传主已核，旧李传旁注引用通鉴不当独立证据。新资料快照覆盖后续仅作来源，不计新增范围。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(43,51)],plain_language_review='首次整理逐条自查新增标题、简介、角色、事件、关系及事实解释，明确主语、计划/命令/执行和原话评价；引用保持原字。不做935年前的全面文案复写，已发现葬未完成的具体事实表述单独勘误。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
