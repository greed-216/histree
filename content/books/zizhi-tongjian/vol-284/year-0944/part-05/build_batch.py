# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 paragraphs 33–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,45))
COMMIT='efabcfd3ab189a0761611575565bd16b0de54ae2'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-284-944-august-november','jiuwudaishi-083-944-august','xinwudaishi-068-zhu-wenjin','xinwudaishi-065-hongchang-death','xinwudaishi-009-944-january','tongjian-265-905-autumn']:
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
main_sources = ['tongjian-284-944-august-november']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0944-p033-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/284.txt').read_text().splitlines()
for n in range(33, 41):
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
    for a,b in [('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '八月条下及追述' if n<=34 else '九月条下' if n<=36 else '十月至十一月条下' if n<=38 else '十二月条下及追述'
        citation = f'卷284·后晋天福九年、后称开运元年（944；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0944_05_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=944, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='944年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_284_0944_' + code
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
        edge = 'participation_zztj_284_0944_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_284_0944_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
def extra(code,title,n,source,quote,actors,**kw):
 E[code]=event(code,title,n,quote,actors,source=source,**kw);return E[code]

ALIASES.update({'帝':'石重贵','唐烈祖':'李昪','唐主':'李璟','汉主':'刘弘熙','殷主':'王延政','硃文进':'朱文进','弘泽':'刘弘泽','杨光远':'杨檀','杨承勋':'杨承贵','杨承勳':'杨承贵','承勋':'杨承贵','承祚':'杨承祚','承信':'杨承信','杨麟':'杨麟（杨光远判官）'})
NEW_ALIASES={'姚景':[],'刘彦贞':['劉彥貞'],'康彦进':['康彥進'],'陈敬佺':['陳敬佺'],'卢进':['盧進'],'留从效':['留從效','留從効'],'王忠顺':['王忠順'],'董思安':[],'张汉思':['張漢思'],'王继勋':['王繼勳'],'陈洪进':['陳洪進'],'程谟':['程謨'],'王继成':['王繼成'],'丘涛':['丘濤','邱涛','邱濤'],'杜延寿':['杜延壽'],'杨瞻':['楊瞻'],'白延祚':[],'王德柔':[],'杨麟（杨光远判官）':['楊麟（楊光遠判官）'],'白文珂':[],'苏光诲':['蘇光誨']}
NEW_DESCRIPTIONS={
'姚景':'南唐清淮节度使。944年条下追述其去世后，刘崇俊求兼寿州。具体生卒年月未载，不将死亡定为944年。',
'刘彦贞':'刘信之子，南唐楚州刺史。944年条下追述他改任濠州观察使，迅速前往替代刘崇俊。具体任职年月与生卒年未载。',
'康彦进':'后晋深州刺史。944年九月丙子击退侵入遂城、乐寿的契丹军。生卒年本段未载。',
'陈敬佺':'殷国将领。944年王延政派他率三千兵驻尤溪、古田。生卒年本段未载。',
'卢进':'殷国将领。944年王延政派他率两千兵驻长溪。没有证据将其与下一段的杜进直接合并。生卒年本段未载。',
'留从效':'泉州散员指挥使，主书称桃林人，《宋史》记泉州永春人。944年参与杀黄绍颇、迎王继勋，并任都指挥使。新史写留從効，沿用同一主体。生卒年本次引文未载。',
'王忠顺':'泉州军中将领。944年与留从效、董思安、张汉思议反朱文进政权，参与泉州政变后被王延政任为都指挥使。生卒年本段未载。',
'董思安':'泉州军中将领。944年参与反朱文进的谋议和泉州政变，后被王延政任为都指挥使。生卒年本段未载。',
'张汉思':'泉州军中将领。944年与留从效等谋议反对朱文进。《宋史》对应谋议另记苏光诲，各书名单分别保留，不以名单不同将两人合并。生卒年本次引文未载。',
'王继勋':'王延政的从子，王氏宗族成员。944年留从效杀黄绍颇后请他主持泉州军府，王延政随后任他为侍中、泉州刺史。具体亲生父姓名本段未载。',
'陈洪进':'泉州副兵马使，主书称临淮，《宋史》记泉州仙游人，地名表述对应关系待核。944年将黄绍颇首级送建州，以说辞突破尤溪阻兵，获王延政任官。生卒年本次引文未载。',
'程谟':'漳州将领。944年闻泉州政变后杀刺史程文纬，立王继成暂掌漳州。与程文纬及新史作程贇的漳州守将分开。生卒年本段未载。',
'王继成':'王延政的从子，王氏宗族成员。944年程谟杀漳州刺史后立他暂掌漳州。亲生父姓名本段未载。',
'丘涛':'杨光远的节度判官，曾劝其叛乱。944年杨承勋决定开城投降时被杀。旧史作邱濤，对应职务和同一被杀场景，保留姓名异文。出生年未载。',
'杜延寿':'杨光远的亲将。944年杨承勋决定投降时与丘涛、杨瞻、白延祚等被杀。姓名来自新旧五代史，不因同音与其他杜延姓将领合并。出生年未载。',
'杨瞻':'杨光远的亲将。944年杨承勋决定投降时被杀。新旧传记作楊瞻，旧本纪同列人物作楊贍，姓名字形待核，不直接写成已证别名。出生年未载。',
'白延祚':'杨光远的亲将。944年杨承勋决定投降时与其他亲将被杀。出生年未载。',
'王德柔':'即墨县令。944年青州开城归降后，奉杨承勋等之命向后晋递交请罪表。生卒年本段未载。',
'杨麟（杨光远判官）':'杨光远的节度判官。944年青州归降时奉杨光远命向后晋递交请死表。与903年已录同名人缺少连续身份依据，暂分档保留待核。生卒年本段未载。',
'白文珂':'后晋代州刺史。944年九月在七里烽击败契丹；新史记丙子，旧史壬辰记录太原奏报。生卒年本次引文未载。',
'苏光诲':'《宋史》留从效传所记留从效亲近之人，参与944年泉州恢复王氏的谋议。该书名单与通鉴不同，不等同张汉思。生卒年本段未载。'}
NEW_DEATH_YEARS={'丘涛':944,'杜延寿':944,'杨瞻':944,'白延祚':944}
aug='jiuwudaishi-083-944-august';sep='jiuwudaishi-083-944-september';dec='jiuwudaishi-083-944-december';ys='jiuwudaishi-097-yang-siege';yc='jiuwudaishi-097-yang-chengxun-name';yn='xinwudaishi-051-yang-surrender';minz='xinwudaishi-068-zhu-wenjin';han='xinwudaishi-065-hongchang-death';ann='xinwudaishi-009-944-january';lc='songshi-483-liu-congxiao-origins';qc='songshi-483-quanzhou-coup';hc='songshi-483-chen-hongjin-origins';hm='songshi-483-chen-hongjin-mission';old905='tongjian-265-905-autumn'

# 33–34: territorial administration and retrospective succession; reuse 905 events.
add('chanzhou_zhenning_army','后晋在澶州设镇宁军，并将濮州划归其管辖',33,'癸亥，',None,[('帝','设澶州镇宁军，并将濮州划归其管辖')],when='944年八月癸亥',place='澶州、濮州')
sup('chanzhou_zhenning_army',33,aug,'癸亥，升澶州為節鎮，以鎮寧為軍額，割濮州為屬郡。','《旧五代史》也记澶州升为节镇，以镇宁为军号，濮州划为属郡。','军额是军镇名称，不是军队人数；原文没有说明有多少兵。')
add('liu_jin_dies_recalled','史书追述濠州刘金去世',34,'初，吴濠州刺史','刘金卒，',[('刘金','被追述已去世')],stable_key='event_zztj_265_0905_liu_jin_dies',when='905年九月后条；确日未载',place='濠州',note='复用卷265已经校核并发布的905年死亡事件，当前追述不新造死亡，不误系944年；职衔刺史与早条团练使各按底本保留。')
sup('liu_jin_dies_recalled',34,old905,'濠州团练使刘金卒，杨行密以金子仁规知濠州。','卷265的905年正文已记刘金去世、杨行密命刘仁规知濠州。','对当前追述回查905年条，沿用同一事件与日期，旧档案不改。',field='time_original')
add('liu_rengui_succeeds_recalled','史书追述刘仁规接任濠州',34,'子仁规','代之；',[('刘仁规','接替父亲刘金主持濠州')],stable_key='event_zztj_265_0905_liu_rengui_oversees_haozhou',when='刘金去世后；确日未载',place='濠州',note='复用905年已经发布的知濠州任命，当前只是补充继任追述，不另生成同人同事。')
relationship('刘金','刘仁规','父亲',34,'吴濠州刺史刘金卒，子仁规代之；','刘金是刘仁规的父亲，与905年所记金子仁规一致，复用旧关系。')
add('liu_rengui_death_recalled','史书追述刘仁规去世',34,'仁规卒，','仁规卒，',[('刘仁规','被追述已去世')],year=None,when='刘金去世之后、刘崇俊接任濠州之前，确切年月未载',place='濠州',note='初追述，不将刘仁规死亡定为944年。')
claim('person',people['刘仁规'],'death_year','刘仁规在刘崇俊接任濠州之前去世，确切年份本段未载。',34,'仁规卒，子崇俊代之。','仅记录死亡事实，不据当前编年位置补年。')
add('liu_chongjun_succeeds_haozhou','刘崇俊接替父亲刘仁规主持濠州',34,'仁规卒，','子崇俊代之。',[('刘崇俊','接替已去世的父亲刘仁规主持濠州')],year=None,when='南唐建立前的追述，确切继任年月未载',place='濠州',note='929年已有刘崇俊三世据濠的记载，本句是继任追述，不写成944年首次任官。')
relationship('刘仁规','刘崇俊','父亲',34,'仁规卒，子崇俊代之。','上文仁规是刘金之子刘仁规，刘仁规是刘崇俊的父亲，不建与父亲无关的同名人物。')
add('tang_creates_dingyuan_army','李昪在濠州设置定远军，任刘崇俊为节度使',34,'唐烈祖','为节度使。',[('唐烈祖','在濠州设置定远军，任刘崇俊为节度使'),('刘崇俊','获任定远军节度使')],year=None,when='李昪在位时期的追述，具体年月未载',place='濠州',note='定远军是军镇名称，不据此强填今日定远县坐标；未将追述直接定为944年。')
add('yao_jing_death_recalled','清淮节度使姚景去世',34,'会清淮节度使','姚景卒，',[('姚景','以清淮节度使身份被记为去世')],year=None,when='刘崇俊求兼寿州之前，确切年月未载',place='清淮军',note='会承接追述，死亡未确年，不机械认作944年。')
claim('person',people['姚景'],'death_year','清淮节度使姚景在刘崇俊求兼寿州之前去世，年份未载。',34,'会清淮节度使姚景卒，','未据卒字推死因，死亡年份留空。')
add('liu_chongjun_bribes_for_shouzhou','刘崇俊厚贿权要，请求兼管寿州',34,'崇俊厚赂权要，','求兼领寿州。',[('刘崇俊','贿赂权势人物，请求兼管寿州')],year=None,when='姚景去世之后的追述，具体年月未载',place='濠州、寿州',note='权要未具名，不给既有宰相强加受贿参与；求兼是请求。')
add('tang_moves_chongjun_qinghuai','李璟调刘崇俊为清淮节度使',34,'唐主阳为不知其意，','为清淮节度使，',[('唐主','表面不理会兼领请求，改调刘崇俊为清淮节度使'),('刘崇俊','从濠州被调至清淮')],year=None,when='李璟在位时期，主书944年条下的追述，确切任命年未载',place='寿州清淮军',note='不是准其同时控制两州，而是调离原镇；阳为不知是史书对皇帝表现的描述。')
add('liu_yanzhen_haozhou_appointment','李璟任刘彦贞为濠州观察使，命他迅速前往接替',34,'以楚州刺史','驰往代之；',[('唐主','任刘彦贞为濠州观察使，命其迅速前往'),('刘彦贞','由楚州刺史改任濠州观察使，迅速前往接替刘崇俊')],year=None,when='上述刘崇俊调任清淮时，具体年月未载',place='楚州、濠州')
add('liu_chongjun_regrets_request','刘崇俊后悔此前求兼寿州',34,'崇俊悔之。','崇俊悔之。',[('刘崇俊','被调离濠州后，后悔此前求兼寿州')],year=None,when='上述濠州换任之后，具体年月未载',place='清淮军',note='情绪依据史书记述，不补上奏辞职或重新夺回濠州。')
relationship('刘信','刘彦贞','父亲',34,'彦贞，信之子也。','彦贞承接刘彦贞，信为既有吴将刘信；刘信是刘彦贞的父亲，不混同其他刘姓将领。')

# 35–37: eclipse, distinct frontier battles, and a dated poisoning.
add('september_solar_eclipse','史书记后晋九月庚午朔发生日食',35,'九月，',None,[],when='944年九月庚午朔',place='史书未列观测地点',note='不把太阳食记录当作亡国天命，未提供天文学计算或精确可见范围。')
sup('september_solar_eclipse',35,sep,'九月庚午朔，日有蝕之。','《旧五代史》同样记九月庚午朔日食。','两书纪日一致，仍不推精确时刻及各地观测状况。')
add('khitan_raids_sui_leshou','契丹进攻遂城、乐寿',36,'丙子，','遂城、乐寿，',[],when='944年九月丙子',place='遂城、乐寿',note='原文为寇，记进攻，不能推两地都已被攻克。')
add('kang_yanjin_repels_khitan','康彦进击退进攻遂城、乐寿的契丹军',36,'丙子，',None,[('康彦进','以深州刺史身份击退契丹军')],when='944年九月丙子',place='遂城、乐寿方向，具体交战处未载',note='深州是康彦进职务所在地，不直接作为本次战场坐标。')
sup('khitan_raids_sui_leshou',36,ann,'九月丙子，契丹寇遂城、樂壽，','《新五代史》同样记九月丙子契丹侵入遂城、乐寿。','该书此句没有康彦进姓名，不单独用于证明反击领将。')
extra('bai_wenke_qilifeng_victory','白文珂在七里烽击败契丹',36,ann,'九月丙子，契丹寇遂城、樂壽，代州刺史白文珂及契丹戰于七里烽，敗之。',[('白文珂','以代州刺史身份在七里烽击败契丹')],when='944年九月，《新五代史》记在丙子条下',place='七里烽',note='是代州方面的另一场战事，不与康彦进遂乐反击强合为同一战场；没有白文珂已参深州的结论。')
sup('bai_wenke_qilifeng_victory',36,sep,'壬辰，太原奏，代州刺史白文珂破契丹於七里烽，斬首千餘級，生擒將校七十餘人。','《旧五代史》九月壬辰记录太原奏报，称白文珂击败契丹，斩首千余、生擒将校七十余。','壬辰是奏报日，与新史丙子条下战事分清；战果作为奏报数字保留，不填成独立核实总数。',relation='adds')
add('han_poisons_hongze','刘弘熙在邕州毒杀镇王刘弘泽',37,'冬，十月，',None,[('汉主','在邕州毒杀刘弘泽'),('弘泽','在邕州被毒杀')],when='944年十月丙午',place='邕州')
sup('han_poisons_hongze',37,han,'鎮王洪澤居邕州，有善政，是歲鳳皇見邕州，晟怒，使人酖殺之。','《新五代史》记刘洪泽居邕州、被评价有善政，刘晟因该地报凤凰而发怒，派人毒杀。','是岁承乾和二年944年；善政与凤凰之说按该书记述，不能把凤凰实际存在写成已证事实。',relation='adds')
claim('person',people['刘弘泽'],'death_year','刘弘泽在944年十月丙午被刘弘熙派人毒杀于邕州。',37,'冬，十月，丙午，汉主毒杀镇王弘泽于邕州。','弘泽洪泽与汉主晟弘熙沿用已核主体；补死亡事实，不改早期人物档案。')

# 38: deploy, organize, overthrow, carry a trophy, accept appointments and change allegiance.
add('chen_jingquan_garrison','王延政派陈敬佺率三千兵驻尤溪、古田',38,'殷主延政遣','屯尤溪及古田，',[('殷主','派陈敬佺率三千兵驻尤溪、古田'),('陈敬佺','率三千兵驻尤溪和古田')],when='944年十一月泉州政变之前，确切部署日未载',place='尤溪、古田',note='三千为两地部署合计，不给每地各三千。')
add('lu_jin_garrison_changxi','王延政派卢进率两千兵驻长溪',38,'卢进以兵','屯长溪。',[('殷主','派卢进率两千兵驻长溪'),('卢进','率两千兵驻长溪')],when='944年十一月泉州政变之前，确切日未载',place='长溪')
add('liu_group_plans_min_restoration','留从效与王忠顺、董思安、张汉思谋议反对朱文进',38,'泉州散员指挥使','众以为然。',[('留从效','说服同列反对朱文进、恢复王氏'),('王忠顺','赞同留从效提出的谋议'),('董思安','赞同留从效提出的谋议'),('张汉思','赞同留从效提出的谋议')],when='944年十一月政变前，具体日未载',place='泉州',note='吾属世受恩、事贼及死有余愧为留从效的动员说辞，不直接建每个人与每位王氏的终身关系。')
sup('liu_group_plans_min_restoration',38,qc,'時從效為泉州散指揮使，與其黨王忠順、董思安及所親蘇光誨相與圖議，興復王氏。','《宋史》同样记留从效、王忠顺、董思安谋议恢复王氏，另列苏光诲。','主书列张汉思，宋史列苏光诲，名单分别保存，不能认两名为同一人或主书漏名已证。',relation='adds')
extra('su_guanghui_coup_planning','《宋史》记苏光诲参与泉州恢复王氏的谋议',38,qc,'時從效為泉州散指揮使，與其黨王忠順、董思安及所親蘇光誨相與圖議，興復王氏。',[('苏光诲','作为留从效亲近之人参与恢复王氏的谋议')],when='944年泉州政变之前，具体日未载',place='泉州',note='仅补该书具名参与者，不因所亲一词认作有具体血缘的亲属。')
claim('person',people['留从效'],'description','《宋史》记留从效为泉州永春人，年幼失父，侍奉母亲和兄长。',38,'漳泉留從效，泉州永春人。幼孤，事母兄以孝悌聞。','桃林为主书原称，永春为宋史籍贯，古地对应尚未核；未具名母兄不造亲属节点。',source=lc,relation='adds')
add('liu_recruits_night_drinkers','留从效等召集亲近军士，在家中夜饮',38,'十一月，从效等','夜饮于从效之家，',[('留从效','召集亲近军士在家夜饮')],when='944年十一月，具体日未载',place='泉州留从效家',note='各引军中所善壮士并未逐个具名，不自动把后续所有任官者都作为酒宴参加者。')
add('liu_false_fuzhou_message','留从效向军士称福州已被攻下，借密令说法鼓动杀黄绍颇',38,'从效给之曰：','众皆踊跃，',[('留从效','声称富沙王已平福州并有密令，鼓动军士动手')],when='944年十一月夜饮时',place='泉州',note='福州已平是动员说辞，当时朱文进仍在，不能新建王延政已经攻下福州事件。给之底本原字保留，不译成已发军饷。')
sup('liu_false_fuzhou_message',38,minz,'泉州軍將留從効詐其州人曰：「富沙王兵收福州矣，吾屬世為王氏臣，安能交臂而事賊乎？」','《新五代史》明确称留从效用福州已收的说法欺骗州人，动员他们反朱。','明确言辞性质为欺骗，保留与主书夜宴对象不同的叙事范围。',relation='adds')
add('quanzhou_kills_huang','泉州军士越墙擒获并杀死黄绍颇',38,'操白梃，','斩之。',[('黄绍颇','被越墙进入的泉州军士擒获并杀死')],when='944年十一月上述动员后，具体日未载',place='泉州',note='白梃为棍棒，具体行刑者未具名，不将留从效写成确定亲手行刑者。')
sup('quanzhou_kills_huang',38,qc,'於是忠順、思安置酒從效家，募敢死士，得陳洪進等五十二人，夜持白梃逾城而入，劫庫兵，擒紹頗斬之。','《宋史》补王忠顺、董思安置酒，召得陈洪进等五十二人，夜间越城取库兵，杀黄绍颇。','人数、组织者与取库兵由该书独立补，不反过来改主书未列人数的记载。',relation='adds')
claim('person',people['黄绍颇'],'death_year','黄绍颇在944年十一月泉州政变中被杀。',38,'众皆踊跃，操白梃，逾垣而入，执绍颇，斩之。','斩之指黄绍颇，死亡明确，具体日未载。')
add('liu_invites_wang_jixun','留从效持泉州印到王继勋家，请他主持军府',38,'从效持州印','请主军府。',[('留从效','持州印请王继勋主持泉州军府'),('王继勋','受到留从效主持军府的邀请')],when='944年十一月黄绍颇被杀之后',place='泉州王继勋家',note='请主是邀请，与王延政后来任命泉州刺史分开。')
sup('liu_invites_wang_jixun',38,minz,'州人共殺紹頗，迎王繼勳為刺史，','《新五代史》记州人杀黄绍颇后迎王继勋为刺史。','本书概述职位结果，主书先请主军府后由王延政任官，保持两个阶段。')
add('liu_claims_coup_command','留从效自称平贼统军使',38,'从效自称','平贼统军使，',[('留从效','自称平贼统军使')],when='944年十一月泉州政变后',place='泉州',note='自称不等于王延政已颁该职，后续都指挥使任命另录。')
add('chen_carries_huang_head','留从效派陈洪进将黄绍颇首级送往建州',38,'函绍颇首，','赍诣建州。',[('留从效','派陈洪进将黄绍颇首级送建州'),('陈洪进','以副兵马使身份携首级赴建州')],when='944年十一月泉州政变后',place='泉州至建州')
sup('chen_carries_huang_head',38,hm,'從留從效殺黃紹頗，將以紹頗首送建州，請出兵為援，群下以道阻賊盛，憚其行。洪進慮事久生變，獨請往，','《宋史》补陈洪进主动请行，送首级到建州并请求援兵。','补请行和任务目的，未把尚在途中写成已获援兵。',relation='adds')
claim('person',people['陈洪进'],'description','《宋史》记陈洪进为泉州仙游人，少时习书与兵法，入军籍后攻汀州先登，被任副兵马使。',38,'陳洪進，泉州仙遊人。幼有壯節，頗讀書，習兵法。及長，以材勇聞。隸兵籍，從攻汀州，先登，補副兵馬使。','主书称临淮，是否籍贯与郡望表述不同尚待核；前次攻汀州没有确年，不在本批新建944年先登事件。',source=hc,relation='adds')
add('chen_blocked_at_youxi','陈洪进到尤溪，被数千福州戍兵拦住',38,'洪进至尤溪，','数千遮道。',[('陈洪进','赴建州途中在尤溪遭数千福州戍兵拦路')],when='944年十一月赴建州途中',place='尤溪',note='数千为概数，不能与此前陈敬佺三千殷兵视为同一部队。')
add('chen_false_zhu_death_story','陈洪进声称朱文进已被杀，并出示黄绍颇首级',38,'洪进绐之曰：','以绍颇首示之，',[('陈洪进','声称义师已杀朱文进，出示黄绍颇首级动摇守军')],when='944年十一月尤溪受阻时',place='尤溪',note='朱福州是朱文进，绐为欺骗，不能把这句话写成朱文进此时已死。倍道嗣君原字保留，解释不补护送君主已返。')
add('youxi_garrison_scattered','尤溪守军听陈洪进说辞后溃散，几名将领随他赴建州',38,'众遂溃，','诣建州。',[('陈洪进','使阻兵溃散，带几名将领赴建州')],when='944年上述说辞之后',place='尤溪至建州',note='大将数人未具名，不补人数或血缘；不将溃散写成全体被杀。')
sup('youxi_garrison_scattered',38,hm,'賊遂潰，渠帥數人皆聽命。洪進至建州，延政大悅，以為本州馬步行軍都校。','《宋史》也记阻兵溃散、几名首领听命，陈洪进到建州后获任本州马步行军都校。','任官名称与主书都指挥使分别保留，不据日期自行排出两个确定升迁日。',relation='adds')
add('wang_jixun_quanzhou_investiture','王延政任王继勋为侍中、泉州刺史',38,'延政以继勋','泉州刺史，',[('殷主','任王继勋为侍中、泉州刺史'),('王继勋','受任侍中、泉州刺史')],when='944年十一月泉州政变与赴建州之后',place='泉州、建州')
for code,name in [('liu_congxiao','留从效'),('wang_zhongshun','王忠顺'),('dong_sian','董思安'),('chen_hongjin','陈洪进')]:
 add(code+'_duzhihui','王延政任'+name+'为都指挥使',38,'从效、忠顺、','皆为都指挥使。',[('殷主','任命'+name+'为都指挥使'),(name,'获王延政任命为都指挥使')],when='944年十一月上述泉州归附后',place='殷国、泉州',note='本句四人各有任职，分别记录；未补统辖兵额与具体军营。')
sup('chen_hongjin_duzhihui',38,hm,'洪進至建州，延政大悅，以為本州馬步行軍都校。','《宋史》将陈洪进到建州后的任职记为本州马步行军都校。','主书都指挥使和宋史都校职称并列，未认作同一职名或两次已确定先后任命。',relation='conflicts')
add('cheng_mo_kills_zhangzhou_prefect','程谟得知泉州政变后，杀漳州刺史程文纬',38,'漳州将程谟','立杀刺史程文纬，',[('程谟','得知泉州消息后立即杀程文纬'),('程文纬','在漳州被程谟杀死')],when='944年十一月泉州消息传至漳州后',place='漳州',note='立杀表示立即杀，不能误当立程文纬为刺史；新史守将作程贇的身份异名仍待核。')
sup('cheng_mo_kills_zhangzhou_prefect',38,minz,'漳州聞之，亦殺贇，迎王繼成為刺史，','《新五代史》记漳州也杀守将程贇，迎王继成为刺史。','通鉴程文纬与新史程贇并列，暂不直接补同人别名或新增一个确定同事死者。',relation='conflicts')
claim('person',people['程文纬'],'death_year','漳州刺史程文纬在944年十一月被程谟杀死。',38,'漳州将程谟闻之，立杀刺史程文纬，','主书姓名和行动明确；新史程贇是否同人继续待核，不凭此把另外一个人也记死亡。')
add('cheng_mo_installs_wang_jicheng','程谟立王继成暂掌漳州事务',38,'立王继成','权州事。',[('程谟','推王继成暂掌漳州事务'),('王继成','被推暂掌漳州事务')],when='944年十一月程文纬被杀之后',place='漳州',note='权州事为暂掌，不直接当主书已任正式刺史；新史刺史称号作独立补证。')
sup('cheng_mo_installs_wang_jicheng',38,hm,'自是漳州殺程贇，迎延政從子繼成為刺史。','《宋史》也记漳州杀程贇，迎王延政从子王继成为刺史。','姓名差异与正式刺史说法独立保留，未强改主书暂掌。',relation='adds')
relationship('王继勋','王延政','族侄',38,'继勋、继成，皆延政之从子也，','原文称王继勋为王延政的从子，此处记录族中侄辈方向；亲生父和具体亲支未载，不建父子关系。')
relationship('王继成','王延政','族侄',38,'继勋、继成，皆延政之从子也，','王继成是王延政的族侄，原文从子支持侄辈，未强定其父姓名或叔伯长幼。')
claim('person',people['王继勋'],'description','王继勋、王继成因与福州核心宗支关系较远，在朱文进杀王氏宗族时得以保全。',38,'硃文进之灭王氏，二人以疏远获全。','疏远为二人得以幸存的书内解释，不能因王氏被杀便把两人提前记为已死。')
claim('person',people['王继成'],'description','王继成与王继勋在朱文进屠杀福州王氏时因关系疏远而幸存。',38,'硃文进之灭王氏，二人以疏远获全。','原文二人承上文继勋继成，不把王氏之灭解成全族灭绝。')
add('xu_wenzhen_requests_yin_submission','汀州刺史许文稹上表，请求归附殷国',38,'汀州刺史',None,[('许文稹','向王延政上表请求归附殷国'),('殷主','成为许文稹请求归附的君主')],when='944年十一月漳泉变化之后，具体日未载',place='汀州至建州',note='奉表请降与三月先投朱文进是不同阶段，不覆盖早期归属。')
sup('xu_wenzhen_requests_yin_submission',38,minz,'文縝懼，以汀州降于延政。','《新五代史》记许文缜因惧而率汀州投降王延政。','主书明写请降，此书写归降结果，分别保留并复用许文稹主体。',relation='adds')

# 39–40: Jin recognition, a prolonged siege, rejected advice and an enforced surrender.
add('jin_invests_zhu_min_king','后晋授朱文进同平章事，封闽国王',39,'十二月，',None,[('帝','授朱文进同平章事，封闽国王'),('硃文进','获后晋授同平章事并封闽国王')],when='944年十二月癸丑',place='闽国、后晋朝廷')
sup('jin_invests_zhu_min_king',39,dec,'癸丑，福州節度使朱文進加同平章事，封閩國王。','《旧五代史》同样记十二月癸丑授朱文进同平章事、封闽国王。','是八月威武任命之后另一授号，不与自称闽主混成一个首次即位。')
add('qingzhou_prolonged_siege','李守贞长期围困青州，城中粮尽、大量人饿死',40,'李守贞围青州经时，','饿死者太半。',[('李守贞','长期围困青州')],when='944年十二月归降前的围城过程，开始与持续日数本句未列',place='青州',note='太半为史书对饥饿死亡的描述，不补城中原人口或精确死者人数。')
sup('qingzhou_prolonged_siege',40,yn,'光遠嬰城固守，自夏至冬，城中人相食幾盡。','《新五代史》记杨光远自夏至冬固守，城中出现人相食。','人相食是该书独立细节，与主书粮尽饿死并列，不增造确定死者总数。',relation='adds')
add('yang_blames_khitan_absent_relief','契丹援兵未到，杨光远向北叩头，责其误己',40,'契丹援兵不至，','误光远矣！”',[('杨光远','因契丹援兵未至向北叩头，称被契丹皇帝耽误')],when='944年十二月开城前，具体日未载',place='青州',note='这是杨光远责怪盟方的言辞，不写成契丹已接到现场责问或其亲到契丹国。')
add('yang_sons_urge_surrender','杨承勋、杨承祚、杨承信劝父亲投降，盼保全家族',40,'其子承勋、','冀全其族。',[('承勋','劝父亲杨光远投降，盼保全家族'),('承祚','劝父亲杨光远投降，盼保全家族'),('承信','劝父亲杨光远投降，盼保全家族'),('杨光远','受到三个儿子投降的劝说')],when='944年开城前；主书十二月条下，旧传写冬十一月',place='青州',note='承勋复用杨承贵，新名有本传明证；盼保全不等于家族后来全部得免。')
sup('yang_sons_urge_surrender',40,ys,'冬十一月，承勛與弟承信、承祚見城中人民相食將盡，知事不濟，勸光遠乞降，冀免於赤族。','《旧五代史》杨光远传将诸子劝降记在冬十一月，并记与弟承信承祚同议。','主书十二月条下、旧传十一月分别保存；可能劝议早于丁巳实际开城，不强改成唯一日期。',relation='adds',field='time_original')
claim('person',people['杨承贵'],'aliases','杨承勋原名杨承贵，因避后晋少帝石重贵的名字而改名；本站复用原杨承贵主体。',40,'承勛，光遠之長子也。始名承貴，避少帝名改焉。','本传明文支持初名和后名为同一人，补杨承勋、楊承勛、楊承勳的检索别名；不是仅凭同名合并。',source=yc,relation='adds')
for son in ['承勋','承祚','承信']:
 relationship('杨光远',son,'父亲',40,'其子承勋、承祚、承信劝光远降，冀全其族。','原文明列三个儿子；杨光远规范主体为杨檀，承勋规范主体为杨承贵，复用已录父亲关系。')
relationship('承勋','承信','兄长',40,'冬十一月，承勛與弟承信、承祚見城中人民相食將盡，','承信被称为承勋的弟弟，杨承贵是杨承信的兄长；同一主体初名后名已明文确认。',source=ys)
relationship('承勋','承祚','兄长',40,'冬十一月，承勛與弟承信、承祚見城中人民相食將盡，','承祚被称为承勋的弟弟，杨承贵是杨承祚的兄长；不据本句强定两名弟弟彼此长幼。',source=ys)
add('yang_refuses_surrender_prophecy','杨光远拒绝投降，援引早年祭天池的吉兆说法',40,'光远不许，','姑待之。”',[('杨光远','拒绝投降，称早年祭天池的说法预示自己可当皇帝')],when='944年诸子劝降时；所引代北祭天池发生年月未载',place='青州',note='祭天池与人言当天子是当事人自述和吉兆说法，不新建事实确定的即位或神异事件。')
add('yang_chengxun_kills_qiu','杨承勋杀死劝父叛乱的丘涛等人',40,'丁巳，','节度判官丘涛等，',[('承勋','杀死丘涛等劝父叛乱者'),('丘涛','以节度判官身份被杀')],when='944年十二月丁巳；旧传将相关过程记在十一月',place='青州',note='原文等还有未具名人，新旧史具名者另作独立补；丘邱字形同场同官保留。')
sup('yang_chengxun_kills_qiu',40,dec,'丁巳，青州楊光遠降。光遠子承勛等斬觀察判官邱濤、牙將白延祚、楊贍、杜延壽等首級，送於招討使李守貞，','《旧五代史》本纪也记丁巳杨承勋等杀邱涛及白延祚、杨贍、杜延寿等。','丘涛职衔主书节度判官、旧纪观察判官分别保留；杨贍与传记杨瞻姓名差异待核，不直接补别名。',relation='adds')
for code,name in [('du_yanshou','杜延寿'),('yang_zhan','杨瞻'),('bai_yanzuo','白延祚')]:
 extra('chengxun_kills_'+code,'杨承勋等杀死亲将'+name,40,yn,'承勳知不可，乃殺節度判官丘濤、親將杜延壽、楊瞻、白延祚等，劫光遠幽之，遣人奉表待罪。',[('承勋','与弟等决定归降，杀死亲将'+name),(name,'以杨光远亲将身份被杀')],when='944年青州开城之前，具体日此传未列',place='青州',note='新史具名亲将补证，不能单靠此传无日条证明每人都在丁巳同一时刻被杀；旧传与旧本纪日期另保留。')
for name in ['丘涛','杜延寿','杨瞻','白延祚']:
 quote='丁巳，承勋斩劝光远反者节度判官丘涛等，' if name=='丘涛' else '乃殺節度判官丘濤、親將杜延壽、楊瞻、白延祚等，'
 claim('person',people[name],'death_year',name+'于944年杨承勋决定开城归降前被杀。',40,quote,'死亡年份依同年围城开降，确日与不同记载分开；不推同名者其他生卒。',source=None if name=='丘涛' else yn,relation='adds')
add('chengxun_sends_heads_to_li','杨承勋将被杀者首级送给李守贞',40,'送其首','于守贞，',[('承勋','将被杀者首级送给李守贞'),('李守贞','收到归降方送来的首级')],when='944年十二月丁巳',place='青州城内至围城军营',note='主书不写递送者，新旧传记所补承祚送首按独立引用保存。')
sup('chengxun_sends_heads_to_li',40,ys,'梟其首，乃遣承祚送於守貞。','《旧五代史》杨光远传明确由杨承祚将首级送给李守贞。','补递送者，不将其误作所有被杀者的亲自行刑者。',relation='adds')
add('chengxun_fires_detains_father','杨承勋纵火喧闹，将父亲杨光远强行移入私宅',40,'纵火大噪，','出居私第，',[('承勋','纵火喧闹，强行将父亲移入私宅'),('杨光远','被儿子强行移入私宅')],when='944年十二月丁巳',place='青州、杨光远私宅',note='劫为强制，不能写成杨光远自愿接受投降建议或当场被儿子杀死。')
add('chengxun_submits_surrender_petition','杨承勋向后晋上表请罪',40,'上表待罪，','上表待罪，',[('承勋','上表请求朝廷处置其罪')],when='944年十二月丁巳',place='青州至后晋朝廷',note='待罪是请罪表述，不写成皇帝已批准免死。')
extra('wang_derou_delivers_surrender_petition','王德柔向后晋递交青州请罪表',40,dec,'遣即墨縣令王德柔貢表待罪。',[('王德柔','以即墨县令身份递交青州请罪表')],when='944年十二月丁巳归降条下',place='青州至后晋朝廷',note='补递送使者，不补其到京确日和途中路线。')
extra('yanglin_delivers_death_petition','杨光远派判官杨麟向后晋递交请死表',40,dec,'楊光遠亦遣節度判官楊麟奉表請死。',[('杨光远','派杨麟递交请死表'),('杨麟','以节度判官身份递交请死表')],when='944年十二月青州归降时，具体日未另列',place='青州至后晋朝廷',note='杨麟与903年同名人尚无同人证据，暂分档；请死不等于已经处决。')
add('qingzhou_opens_to_jin','杨承勋打开青州城门，接纳后晋军',40,'开城','纳官军。',[('承勋','打开青州城门，接纳后晋军'),('李守贞','其所领后晋军进入青州')],when='944年十二月丁巳',place='青州',note='开城为实际发生，杨光远后来被杀随第42段继续，不在本段写成已死。')

reviews={33:'军镇设立与濮州划属，军额不解兵额，八月癸亥与旧本纪一致。',34:'刘金905年死亡与刘仁规接任复用既有事件和参与；仁规死亡、崇俊继任、定远建镇和后续调任追述未确年留null。三条父亲关系据明确子字，刘彦贞父信复用吴将刘信，官任与求兼分开。',35:'日食纪日原保留，不补天文范围或天命结论。',36:'遂乐进攻与康反击、代州白文珂七里烽战事分别录；丙子战事与壬辰奏报日期分清，奏报伤俘数字有归属。',37:'弘泽十月丙午毒杀与新史是岁、凤凰动机并列；凤凰是史书所述传言，不当现实独立事实。',38:'部署人数、动员谎言、夜袭、请主军府、自称、使行受阻和正式任命分别记录。宋史补人数、苏光诲、陈籍贯及都校，新史补泉漳汀归附，亲支和程姓名未硬合。朱已死、福州已收是欺骗说辞，不提前真实死亡。',39:'十二月后晋授朱同平章事封闽国王，不混三月自立或八月威武任命。',40:'围城、诸子劝降、父拒、诛党、首级递送、囚父、递表、开城分开。承勋初名承贵有本传明证，复用稳定主体并补aliases事实；旧传十一月与主书本纪十二月保留。杨瞻杨贍、丘邱及判官职衔原字差异保留，杨麟同名暂分。'}
assert not (P/'publication.json').exists()
for n in range(33,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=944,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph=Q[41]['id'],next_volume=284,next_year=944,supplements=supplements,excluded_non_body=[],coverage='卷284原38—45行连续第33—40段，八月至十二月及追述；下接第41段闽殷及南唐战事，944全年尚未完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'当前只处理第33—40段，快照内后续泉州反击和南唐战事留下一段。'),(minz,'只补泉漳汀归属，段尾朱连死亡另据主线后段录，不提前。'),(han,'本段只补弘泽遇害，前次弘昌死亡已发布，不重建。'),(ys,'只补围城与劝降，后文杀光远及后汉追赠未提前。'),(yc,'只补长子、初名和改名证据，947年契丹处死留后续。'),(yn,'只补当前围城、劝降与杀亲将，光远被杀的具名何延祚暂留第42段。'),(hm,'只补当前赴建州和任职，后续朱连死及南唐降建和留陈晚年未提前。'),(old905,'回查并复用刘金死亡、刘仁规继任旧事件，当前追述不新造死亡。')]],source_issues_review='旧传十一月与主书十二月劝降开城时序、杨瞻杨贍与丘邱姓名、陈洪进临淮仙游地名、陈都指挥使都校、程文纬程贇及宋史谋议名单分别保留。杨承勋初名承贵明确，不重复建档；未知年追述和谎言不硬作944年事实。纸本异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,41)],plain_language_review='首次逐项核对标题、人物、事件、参与、关系、事实说明与时间解释，主体明确；命令、继任追述、谎言、使行、计划与结果分别处理。原文保持底本字形。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
