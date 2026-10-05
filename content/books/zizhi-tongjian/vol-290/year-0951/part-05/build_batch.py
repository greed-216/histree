# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 31–38."""
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
COMMIT='4ae3eabc78dcb3f9ddd203076e0412b51fdf8d20'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-951-february-diplomacy','xinwudaishi-011-first-year-951']:
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
main_sources = ['tongjian-290-951-february-diplomacy','tongjian-290-951-march-policies']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p031-p038',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-february-diplomacy':'卷290·广顺元年·二三月外交与楚国册封','tongjian-290-951-march-policies':'卷290·广顺元年·三月徐州战果与沿淮政策','jiuwudaishi-111-march-policy':'卷111·太祖本纪二·广顺元年三月','songshi-483-zhou-background':'卷483·世家六·湖南周氏·周行逢早年','xinwudaishi-066-langzhou-flight':'卷66·楚世家·王进逵修府出走','xinwudaishi-066-wang-background':'卷66·楚世家·刘言与王进逵早年'}
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
for n in range(31, 39):
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
    labels={'tongjian-290-951-february-diplomacy':'卷290·广顺元年·二三月外交与楚国册封','tongjian-290-951-march-policies':'卷290·广顺元年·三月徐州战果与沿淮政策','jiuwudaishi-111-march-policy':'卷111·太祖本纪二·广顺元年三月','songshi-483-zhou-background':'卷483·世家六·湖南周氏·周行逢早年','xinwudaishi-066-langzhou-flight':'卷66·楚世家·王进逵修府出走','xinwudaishi-066-wang-background':'卷66·楚世家·刘言与王进逵早年'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年二三月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_05_{len(B["claims"])+1:04d}'
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










ALIASES.update({'巩廷美':'巩延美','帝':'郭威','楚王':'马希萼','唐主':'李璟','北汉主':'刘崇（刘知远弟）','契丹主':'耶律阮','张亻放':'张亻放（楚军指挥使）'})
NEW_ALIASES={'谢彦颙':['謝彥顒'],'王逵':['王进逵','王進逵'],'周行逢':[],'唐师翥':['唐師翥','唐翥'],'马光惠':['馬光惠'],'马希振':['馬希振'],'张亻放（楚军指挥使）':[],'拽剌梅里（951年契丹使者）':['拽剌梅里']}
NEW_DESCRIPTIONS={
'谢彦颙':'马希萼原来的家奴，担任小门使。《资治通鉴》记他受宠后专横，与马希崇产生嫌隙，并获准参加府宴。生卒年未载。',
'王逵':'楚国朗州静江军指挥使。《新五代史》称王进逵，记为武陵人，早年是静江军士卒。951年与周行逢率修府士兵逃回朗州，参与当地军府事务。生卒年尚未录入。',
'周行逢':'楚国朗州静江军副使。951年与王逵率修府士兵逃回朗州。《宋史》记为朗州武陵人，早年因犯法被编入军队，凭骁勇升任军官。生卒年尚未录入。',
'唐师翥':'楚国湖南指挥使。951年奉马希萼命令追赶王逵等，在朗州遭伏击，败后逃回。《新五代史》同一追击记载称唐翥。生卒年未载。',
'马光惠':'马希振之子、马希萼的侄子。951年王逵等罢免马光赞后，让他主持朗州事务，随后拥立他为节度使。生卒年未载。',
'马希振':'马光惠的父亲。《资治通鉴》在951年朗州政局记载中明确说明这项亲属关系，未提供其生卒年。',
'张亻放（楚军指挥使）':'楚国诸军指挥使。951年与王逵、周行逢、何敬真共同处理朗州军府事务。电子底本姓名末字写作“亻放”，字形待核，暂不与其他记载中的张仿合并。生卒年未载。',
'拽剌梅里（951年契丹使者）':'951年耶律阮派遣的使者，负责答复北汉来使李巩言。姓名及梅里称谓仍待校核，暂不与其他年代的同称使臣合并。生卒年未载。'}
old='jiuwudaishi-111-march-policy';nw='xinwudaishi-011-first-year-951';wang='xinwudaishi-066-wang-background';flight='xinwudaishi-066-langzhou-flight';zhou='songshi-483-zhou-background'
ret='马希萼攻占长沙以后至951年三月的概述，具体发生时间未载'
add('ma_xie_old_grievances','史书记载马希萼得势后报复旧怨、纵酒荒淫',31,'楚王希萼既得志，','昼夜纵酒荒淫，',[('楚王','被史书评价为得势后杀戮无度、纵酒荒淫')],year=None,when=ret,place='楚国',note='这是史家对一段时期的概述，没有列出具体被杀者，不据此新增具名杀人事件。')
add('ma_xie_delegates_xichong','马希萼把军府事务交给马希崇',31,'悉以军府事','委马希崇。',[('楚王','把军府事务交给马希崇'),('马希崇','接受军府事务的委托')],year=None,when=ret,place='楚国')
add('ma_xichong_disorder','史书记载马希崇徇私，政务与刑罚陷入混乱',31,'希崇复多私曲，','政刑紊乱。',[('马希崇','被史书记载为徇私并导致政刑混乱')],year=None,when=ret,place='楚国',note='保留史家的评价性质，原文没有列出具体案由。')
add('chu_seizes_property_for_rewards','楚国府库空虚后征取民财赏兵，士卒仍抱怨分配不均',31,'府库既尽于乱兵，',None,[],year=None,when=ret,place='楚国',description='乱兵耗尽府库后，楚国征取百姓财物赏赐士卒，有时封住居民家门取财。士卒仍抱怨分配不均，随马希萼而来的朗州旧将佐也产生离心。',note='原文未具名取财执行者；群体怨望不外推为每个具名将领的心理。')
add('li_jing_treats_liu','李璟厚待入贡使者刘光辅',32,'刘光辅之入贡于唐也，','唐主待之厚，',[('唐主','厚待楚国入贡使者'),('刘光辅','出使南唐时受到厚待')],when='951年二月刘光辅入贡期间的追述，具体接待日未载',place='南唐',note='入贡出发此前已经登记，此处只新增接待行为。')
add('liu_advises_take_hunan','刘光辅秘密向李璟建议攻取湖南',32,'光辅密言：','可取也。”',[('刘光辅','秘密提出湖南可取的判断'),('唐主','听取刘光辅的建议')],when='951年二月入贡期间，具体谈话日未载',place='南唐',note='民疲主骄是刘光辅的判断，不视为已独立证明的全部民情。')
add('bian_hao_xinzhou','李璟任命边镐为信州刺史',32,'唐主乃以','为信州刺史，',[('唐主','任命边镐为信州刺史'),('边镐','由营屯都虞候获任信州刺史')],when='951年刘光辅入贡劝取湖南之后，具体任命日未载',place='信州')
add('bian_hao_yuanzhou','边镐率军驻袁州，南唐暗中筹划进取湖南',32,'将兵屯袁州，',None,[('边镐','率军驻袁州'),('唐主','暗中筹划进取湖南')],when='951年刘光辅劝取湖南之后，具体驻军日未载',place='袁州',note='潜图进取是筹划，不提前写成已攻克长沙。')
add('xie_yanyong_favored','谢彦颙从马希萼家奴成为受宠的小门使',33,'小门使谢彦颙，','恃恩专横。',[('谢彦颙','原为家奴，担任小门使并受宠'),('楚王','宠信小门使谢彦颙')],year=None,when='谢彦颙早年身份及受宠情形的概述，具体年份未载',place='楚国',note='首面按容貌理解；与妻妾杂坐不推定为性关系，受宠也不新建无明文的亲属关系。')
add('xie_ma_xichong_resentment','谢彦颙与马希崇并肩而行、拍背，马希崇对此怀恨',33,'常肩随希崇，','希崇衔之。',[('谢彦颙','常与马希崇并肩而行，有时拍他的背'),('马希崇','对谢彦颙的举动怀恨')],year=None,when='951年三月前后所追述的长期举动，起止时间未载',place='楚国')
add('chu_gate_officer_custom','楚国府宴旧例要求小门使持兵在门外守候',33,'故事，','小门使执兵在门外。',[],year=None,when='楚国府宴旧例，具体建立年份未载',place='楚国军府')
add('xie_banquet_seating','马希萼让谢彦颙参加府宴，有时坐在诸将之上',33,'希萼使彦颙预坐，',None,[('楚王','准许谢彦颙入席，有时安排在诸将之上'),('谢彦颙','参加府宴并获优先席位')],year=None,when=ret,place='楚国军府',description='马希萼让谢彦颙参加府宴，有时坐在诸将之上。史书记载诸将因此感到受辱。',note='没有具名的诸将心理不外推给王逵、周行逢等每个人。')
add('chu_palace_repair','马希萼命王逵、周行逢率千余士兵修复府舍',34,'希萼以府舍焚荡，','帅所部兵千馀人治之，',[('楚王','命静江军士兵修复被烧毁的府舍'),('王逵','以静江指挥使身份率兵修府'),('周行逢','以副使身份率兵修府')],year=None,when='长沙府舍被焚以后、951年三月壬申出走以前，开工时间未载',place='长沙')
claim('person',people['王逵'],'description','王逵在《新五代史》中称王进逵，为武陵人，早年是静江军士卒，后来担任马希萼的指挥使。',34,'王進逵，武陵人也。', '同书下一段同样记修府、逃回武陵和唐翥追击，据连续履历对应王逵，未仅凭同姓合并。',source=wang)
claim('person',people['王逵'],'description','王进逵早年是静江军士卒，后来担任马希萼的指挥使。',34,'進逵少為靜江軍卒，事希萼為指揮使。','仅补充早年履历，不提前录入后续攻逐边镐等行动。',source=wang)
claim('person',people['周行逢'],'description','周行逢是朗州武陵人，早年因犯法被编入军队，凭骁勇逐步升任军官。',34,'湖南周行逢，朗州武陵人。少無賴，不事產業。嘗犯法配隸鎮兵，以驍勇累遷裨校。','只采用籍贯与早年任职；少无赖是不另扩写的史家评价，后文宋初及后续湖南政局未在此提前录入。',source=zhou)
sup('chu_palace_repair',34,flight,'長沙遭亂殘毀，希萼使進逵以靜江兵營緝之，兵皆愁怨，','《新五代史》也记马希萼命王进逵率静江军修复长沙，士兵因此愁怨。','同一军职、修府和逃归场景支持王进逵与王逵为同人。')
add('repair_soldiers_complain','修府士兵因劳苦、没有犒赏而抱怨如同囚犯服役',34,'执役甚劳，','岂知我辈之劳苦乎！”',[],year=None,when='951年三月出走以前的修府期间，具体日期未载',place='长沙',note='士兵的比喻与抱怨不是司法判决，不能据此说修府士兵已被定罪。')
add('wang_zhou_plan_escape','王逵与周行逢因军中怨气商议及早自保',34,'逵、行逢闻多，','祸及吾曹。”',[('王逵','听到军中怨言，与周行逢商议自保'),('周行逢','与王逵商议避免祸及自身')],when='951年三月壬申出走以前，具体商议日未载',place='长沙')
add('wang_zhou_escape_langzhou','王逵与周行逢率修府士兵逃回朗州',34,'壬申旦，','逃归朗州。',[('王逵','率士兵带长柄斧和白梃逃回朗州'),('周行逢','与王逵一起率兵逃回朗州')],when='951年三月壬申早晨',place='长沙至朗州')
sup('wang_zhou_escape_langzhou',34,flight,'進逵因擁之，夜以長柯巨斧斫關，奔歸武陵。','《新五代史》记王进逵夜间率兵用长柄大斧砍关，逃回武陵。','《资治通鉴》记壬申早晨，《新五代史》记夜间；时段差异并列保留，不用补书覆盖主书纪时。',relation='conflicts')
add('ma_xie_late_report','马希萼醉酒未醒，左右到次日才报告士兵出走',34,'时希萼醉未醒，','始白之。',[('楚王','醉酒未醒，直到次日才获知士兵出走')],when='951年三月壬申至癸酉',place='长沙',note='报告延误是原文记载，不猜测左右的具体姓名。')
add('tang_shizhu_pursuit','马希萼派唐师翥率千余人追击，追军抵达朗州',34,'希萼遣湖南指挥使','直抵朗州。',[('楚王','派唐师翥率军追赶出走士兵'),('唐师翥','率千余人追赶，未在途中追及，直抵朗州')],when='951年三月癸酉报告以后，具体抵达日未载',place='长沙至朗州')
sup('tang_shizhu_pursuit',34,flight,'明日遣將唐翥追之，及于武陵，','《新五代史》称追击将领为唐翥，记他于次日受命追赶，抵达武陵。','同一派遣者、追击对象和战败场景对应唐师翥；“及于武陵”不据以否定《资治通鉴》的途中不及。')
add('langzhou_ambush','王逵等伏击疲惫追军，唐师翥败后逃回',34,'逵等乘其疲乏，','师翥脱归。',[('王逵','趁追军疲惫发动伏击'),('唐师翥','所部伤亡惨重，自己逃回')],when='951年三月追军到朗州以后，具体交战日未载',place='朗州',note='原文死伤殆尽不翻成全军死亡，未据“等”外推每名将领都亲自伏击。')
sup('langzhou_ambush',34,flight,'翥戰大敗而還。','《新五代史》也记唐翥大败后返回。','两书同场败归支持姓名对应，没有补出具体伤亡数字。')
add('langzhou_deposes_guangzan','王逵等罢免朗州留后马光赞',34,'逵等黜留后马光赞，','逵等黜留后马光赞，',[('王逵','参与罢免马光赞'),('马光赞','被罢免朗州留后')],when='951年三月朗州击败追军后，具体日未载',place='朗州')
add('ma_guanghui_governs','王逵等让马光惠主持朗州事务',34,'更以希萼兄子光惠','希振之子也。',[('王逵','参与推举马光惠主持朗州事务'),('马光惠','接替主持朗州事务')],when='951年三月马光赞被罢以后，具体日未载',place='朗州')
relationship('马希振','马光惠','父亲',34,'光惠，希振之子也。','原文明确父子身份；方向表示马希振是马光惠的父亲。')
add('ma_guanghui_jiedushi','王逵等随后拥立马光惠为节度使',34,'寻奉光惠为节度使，','寻奉光惠为节度使，',[('王逵','参与拥立马光惠为节度使'),('马光惠','被拥立为节度使')],when='951年主持朗州事务后不久，具体月日未载',place='朗州',note='奉为不等于已获南唐或后周正式授命，不新造册封使。')
add('langzhou_joint_affairs','王逵、周行逢、何敬真与张亻放共同处理朗州军府事务',34,'逵等与何敬真','参决军府事。',[('王逵','参与决定朗州军府事务'),('周行逢','参与决定朗州军府事务'),('何敬真','参与决定朗州军府事务'),('张亻放','以诸军指挥使身份参与决定军府事务')],when='951年马光惠被拥立后，具体月日未载',place='朗州',note='周行逢按本段前文逵、行逢对应“逵等”；张姓名末字底本写亻放，未凭字形合并张仿。共同议事不自动建立盟友关系。')
add('ma_xie_informs_tang','马希萼向南唐报告朗州事变',34,'希萼具以状言于唐，','希萼具以状言于唐，',[('楚王','向南唐报告朗州事变')],when='951年朗州事变之后，具体月日未载',place='楚国至南唐')
add('li_jing_recruits_langzhou','李璟派使者以厚赏招谕王逵等',34,'唐主遣使','以厚赏招谕之。',[('唐主','派使者用厚赏招谕王逵等'),('王逵','成为招谕对象')],when='951年收到马希萼报告以后，具体月日未载',place='南唐至朗州')
add('langzhou_no_reply','王逵等收下南唐赏赐、放走使者，却不答复诏书',34,'逵等纳其赏，',None,[('王逵','收下赏赐、放走使者，却不答复南唐诏书')],when='951年南唐使者招谕以后，具体月日未载',place='朗州',description='王逵等收下赏赐，放走南唐使者，却不答复诏书。史书记载南唐也不敢追问。',note='收赏不等于已服从南唐，唐不敢诘保留史书的判断性质。')
sup('langzhou_deposes_guangzan',34,flight,'進逵乃逐出留後馬光惠，迎言於辰州以為帥，進逵自為副。','《新五代史》在败军返回后直接叙述王进逵逐出马光惠、迎刘言为主帅。','《资治通鉴》此处是罢马光赞、立马光惠，逐马光惠迎刘言另见后续六月条；两书记事压缩与顺序不同，不能把迎刘言提前至本次罢光赞。',relation='conflicts')
add('wang_yanchao_takes_xuzhou','王彦超奏报攻克徐州',35,'王彦超奏克徐州，','王彦超奏克徐州，',[('王彦超','奏报攻克徐州')],when='951年三月；《新五代史》记甲戌',place='徐州')
sup('wang_yanchao_takes_xuzhou',35,nw,'三月甲戌，武寧軍節度使王彥超克徐州。','《新五代史》记三月甲戌，武宁军节度使王彦超攻克徐州。','《资治通鉴》本句未单列日期，以独立出处保留补书记日。',field='time_original',relation='adds')
sup('wang_yanchao_takes_xuzhou',35,old,'徐州行營都部署王彥超馳奏，收復徐州。','《旧五代史》也记王彦超驰奏收复徐州，称其为徐州行营都部署。','不同书采用不同职务称谓，不据此另建王彦超。')
add('gong_killed_xuzhou','徐州被攻克后，巩廷美等被杀',35,'杀巩廷美等。',None,[('巩廷美','徐州被攻克后被杀')],when='951年三月徐州被攻克后',place='徐州',note='巩廷美沿用已有巩延美主体及别名；原文未明执行处决者，不强称王彦超亲自处斩。')
claim('person',people[ALIASES.get('巩廷美','巩廷美')] if '巩廷美' in people else next(x['key'] for x in B['people'] if '巩廷美' in x['aliases']),'death_year','巩廷美在951年三月徐州被攻克后被杀。',35,'王彦超奏克徐州，杀巩廷美等。','以本次战果明确死亡年份；沿既有主体，不改写旧档案中的未知字段。')
E['yang_execution']=event('yang_execution','徐州被攻克后，杨温及亲近徒党被处斩',35,'城內逆首楊溫及親近徒黨並處斬。',[('杨温','徐州被攻克后被处斩')],source=old,when='951年三月徐州被攻克后',place='徐州',note='独立采用《旧五代史》处斩诏文，逆首是诏书用语，不作为本站额外评价。')
E['xuzhou_release']=event('xuzhou_release','后周释放徐州被胁迫参与守城的军民',35,'其餘無名目人及本城軍都將校、職掌吏民等，雖被脅從，本非同惡，並釋放。',[],source=old,when='951年三月徐州被攻克后',place='徐州',note='诏书区分被胁迫者与处斩对象，不写成所有守军被杀。')
E['xuzhou_return_farming']=event('xuzhou_return_farming','郭威准许被招入徐州守城的草贼归农，并要求安抚',35,'其招入城草賊，並放歸農，仍倍加安撫。',[],source=old,when='951年三月徐州被攻克后',place='徐州',note='具体政策来自郭威诏文；草贼为当时称谓，不推断每人的身份与籍贯。')
E['xuzhou_family_protection']=event('xuzhou_family_protection','郭威命人安抚守护刘赟在徐州的妻子与家属',35,'湘陰公夫人並骨肉在彼，仰差人安撫守護，勿令驚恐。',[],source=old,when='951年三月徐州被攻克后',place='徐州',note='湘阴公依已录后汉宗室刘赟对应；这项命令未提供执行者姓名或证实所有家属随后命运。')
add('li_gongyan_arrives','北汉使者李巩言抵达契丹',36,'北汉李巩言','至契丹，',[('李巩言','作为北汉使者抵达契丹')],when='951年三月条下，具体抵达日未载',place='契丹',note='出发求兵此前已录，本次只新增抵达，不将后周田敏混为同一使者。')
add('khitan_reply_northern_han','耶律阮派拽剌梅里答复北汉来使',36,'契丹主使',None,[('契丹主','派使者答复北汉'),('拽剌梅里（951年契丹使者）','受命答复李巩言的来使请求')],when='951年三月条下，具体派遣日未载',place='契丹与北汉',note='派遣命令不等于使者已经到北汉；梅里或为称谓，暂不与其他同称使臣合并。')
add('zhou_no_border_raids','郭威命沿淮军镇守境，禁止擅入南唐',37,'丙子，敕：','擅入唐境。',[('帝','禁止沿淮军镇纵容兵民擅入南唐')],when='951年三月丙子',place='沿淮军镇',note='朝廷与唐本无仇怨是郭威诏书的政治说法，不改成历史上从无冲突的事实。')
sup('zhou_no_border_raids',37,old,'詔沿淮州縣軍鎮，今後自守疆土，不得縱一人一騎擅入淮南地分。','《旧五代史》也记沿淮州县军镇不得纵一人一骑擅入淮南。','印证守境禁越政策，未据淮南一词绘制具体边界。')
add('zhou_tang_trade','郭威命令不得阻止与南唐之间的商旅往来',37,'商旅往来，',None,[('帝','要求不得禁止与南唐之间的商旅往来')],when='951年三月丙子',place='后周与南唐边境',note='商旅政策不等于两国结盟，也没有宣布取消所有税费。')
add('luzhou_sends_captives','潞州把涉县俘获的二百六十余名北汉将卒送往朝廷',38,'己卯，','人，',[],when='951年三月己卯',place='涉县、潞州至后周朝廷',note='原文未明这批俘虏全部来自此前长寿村一役，不合并为同一批战俘。')
sup('luzhou_sends_captives',38,old,'己卯，潞州奏，涉縣所擒河東將士二百餘人，部送赴闕。','《旧五代史》同日记潞州将涉县俘获的河东将士二百余人送往朝廷。','《资治通鉴》为二百六十余人，《旧五代史》为二百余人，保留各书概数，不据较粗数量否定较细数量。',relation='adds')
add('zhou_returns_captives','后周赐衣履给涉县所获北汉将卒，并把他们释放回去',38,'各赐衫袴巾履遣还。',None,[],when='951年三月己卯',place='后周朝廷至北汉',note='只记这批送来的将卒获赐衣履并遣还，不说双方进行了对等换俘。')
sup('zhou_returns_captives',38,old,'詔給衫袴巾屨，放歸本土。','《旧五代史》也记给俘虏衣物鞋履，并放回本土。','与送俘条相连，不新建其他批次的释放。')
reviews={31:'马希萼得势后的概述可能跨950至951，未强定起点。委政、徇私评价、征财赏兵及群体怨望分别保留。',32:'接待、秘密建议、边镐任职与驻袁州分开；入贡出发不重复，进取是计划。',33:'家奴、小门使与受宠概述不强定年；首面按容貌解释，杂坐不外推性关系，宴例与破例分开。',34:'修府、抱怨、商议、逃兵、延报、追击、伏击和朗州政局连续分录；王逵与王进逵、唐师翥与唐翥按同场履历对应。张亻放字形待核不强合张仿；新书夜逃与主书晨逃、罢免对象与迎刘言叙述顺序差异并列，未提前录入六月废光惠。马希振父亲方向明确。',35:'克徐州、巩廷美被杀分别录入；巩复用巩延美。新书补甲戌，旧书补杨温处斩、释放胁从、归农及保护家属诏令。',36:'抵达与回使任命分录；李巩言沿已有北汉使者，拽剌梅里暂独立，不猜测同称使臣身份。',37:'守境禁越与商旅不禁分别登记；无仇怨保留诏书说法性质。',38:'送俘与赐遣分开，二百六十余和二百余按各书精度保留，不推为此前战斗同批俘虏。'}
assert not (P/'publication.json').exists()
for n in range(31,39):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(31,39)],next_paragraph=Q[39]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原36—43行连续八段；本年后续正文仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(31,39)],source_issues_review='原文逐字导出不改字，纸本未核。王进逵及唐翥按同场履历对应。张亻放姓名字形待核；拽剌梅里不与其他同称使臣合并。晨逃与夜逃、朗州换帅叙述次序及俘虏概数按各书保留。',plain_language_review='已逐条检查标题、人物介绍、事件说明、参与角色、亲属方向、时间解释及事实说明；明确区分评价、建议、命令与实际行动，引用外使用白话，未为流畅补出无证据的执行者。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
