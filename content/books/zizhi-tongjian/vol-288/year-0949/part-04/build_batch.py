# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 949 paragraphs 23–26."""
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
COMMIT='20d5546bb3510d89dd7f3f66087f55d50b7752ed'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-949-june-july','jiuwudaishi-125-wang-shouen-luoyang']:
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
main_sources = ['tongjian-288-949-june-july','tongjian-288-949-august-december']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0949-p023-p026',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-288-949-august-december':'卷288·乾祐二年·八月至十二月','xinwudaishi-046-ouyang-commentary':'卷46·王建立传附王守恩·欧阳修论','xinwudaishi-066-pushezhou':'卷66·楚世家·仆射洲之战及后续','jiuwudaishi-102-september-949':'卷102·隐帝本纪·乾祐二年九月','jiuwudaishi-110-return-court-949':'卷110·周太祖纪·乾祐二年八月返京'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(23, 27):
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
    labels={'tongjian-288-949-august-december':'卷288·乾祐二年·八月至十二月','xinwudaishi-046-ouyang-commentary':'卷46·王建立传附王守恩·欧阳修论','xinwudaishi-066-pushezhou':'卷66·楚世家·仆射洲之战及后续','jiuwudaishi-102-september-949':'卷102·隐帝本纪·乾祐二年九月','jiuwudaishi-110-return-court-949':'卷110·周太祖纪·乾祐二年八月返京'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐二年（949年八月至九月及史论）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0949_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=949, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='949年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0949_' + code
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
        edge = 'participation_zztj_288_0949_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0949_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘承祐','希广':'马希广','希萼':'马希萼','王赟':'王赟（楚岳州刺史）','苑氏':'苑氏（马希萼妻）'})
NEW_ALIASES={'王赟（楚岳州刺史）':['王赟','王贇'],'苑氏（马希萼妻）':['苑氏']}
NEW_DESCRIPTIONS={
'王赟（楚岳州刺史）':'王环的儿子，楚国岳州刺史。949年受马希广任命为都部署战棹指挥使，在仆射洲击败马希萼，追击时奉马希广命令撤回。生卒年尚未录入。',
'苑氏（马希萼妻）':'马希萼的妻子，个人名字与生年未载。949年劝丈夫不要与兄弟交战，未被听从；马希萼战败归来后，投井而死。未因同姓与苑玫等人建立亲属关系。'}
NEW_DEATH_YEARS={'苑氏（马希萼妻）':949}
comment='xinwudaishi-046-ouyang-commentary';chu='xinwudaishi-066-pushezhou';sept='jiuwudaishi-102-september-949';guo='jiuwudaishi-110-return-court-949';wang='jiuwudaishi-125-wang-shouen-luoyang'
# Attach commentary to the historical event already published; do not invent a 949 event involving Ouyang Xiu.
ck='event_zztj_288_0949_guo_orders_bai_replace_wang'
old=[e for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for e in json.loads(f.read_text())['events'] if e['key']==ck]
assert old and len({json.dumps(e,sort_keys=True,ensure_ascii=False) for e in old})==1
B['events'].append(dict(old[0],status='draft'));reused.add(ck);used[23]=[ck];E['commentary']=ck
claim('event',ck,'historical_commentary','欧阳修认为，郭威以枢密使文书随意撤换留守、朝廷也不追问，反映出当时法制纲纪已经败坏；他提醒治国者重视细小变化，防止逐渐失序。',23,Q[23]['text'],'此段是后世史家对已录949年事件的评论，关联原事件而不创建949年欧阳修参加朝政的事件。未有无君之志是欧阳修对郭威当时动机的判断，不当作已证明的内心事实。')
sup('commentary',23,comment,'而周太祖以一樞密使頭子易置之，如更戍卒。','《新五代史》也载欧阳修以枢密使文书撤换留守的事例，批评法制纲纪败坏。','《通鉴》节引同一史论，两处是同一作者论述的传承，不作为两个独立来源证明郭威的政治动机。',relation='adds',field='historical_commentary')
add('wang_shouen_bribes_in_capital','王守恩到大梁后担心获罪，献物并重贿权贵',24,'守恩至大梁，','重赂权贵。',[('王守恩','担心获罪，在大梁献物并重贿权贵')],when='949年八月被撤换留守后，具体到京日未载',place='大梁',note='未载受贿者具体姓名、金额或逐次交易，不把所有权臣都认定为收贿者。')
add('han_spares_wang_shouen','后汉朝廷念王守恩曾率潞州归附，免其罪',24,'朝廷亦以','故宥之，',[('王守恩','因早先率潞州归附后汉而获朝廷宽宥'),('刘承祐','在位朝廷宽宥王守恩')],when='949年王守恩到大梁后，具体日未载',place='后汉朝廷',note='主书记宽宥原因有首举潞州归汉，不把前句重赂直接写成获赦唯一原因。')
add('han_executes_wang_aides','后汉处死王守恩手下数名办事者',24,'但诛其用事者',None,[('王守恩','手下数名办事者被朝廷处死')],when='949年王守恩获宽宥时，具体日未载',place='后汉，具体行刑地点未载',note='用事者姓名、人数和具体罪名未列，不能补成全体属吏或家属都被杀。')
event('wang_shouen_returns_property','王守恩被撤换后，向追讨财物的洛阳人逐一偿还',24,'而洛人有曾為守恩非理割剝者，皆就其第征其舊物，守恩一一償之。',[('王守恩','向到府追讨财物的受害者逐一偿还')],when='949年被撤换西京留守后，具体日未载',place='洛阳',source=wang,note='这是《旧五代史》对撤换后情况的补充；不据一一偿之推断所有受害者都已获得全部赔偿。')
add('ma_xie_mobilizes_builds_fleet','马希萼征调朗州壮丁，号静江军，造七百艘战船',25,'马希萼悉调','将攻潭州，',[('马希萼','征调朗州壮丁为乡兵，号静江军，造船准备攻潭州')],when='949年八月仆射洲之战前，具体征调日未载',place='朗州',note='郎州为底本字形，按同段朗州、武陵语境显示朗州；乡兵号静江军不与桂州静江节度军自动合并。七百为史载船数，准备进攻不等于当时已占潭州。')
add('yuan_warns_ma_xie','苑氏劝马希萼不要与兄弟交战，马希萼未听从',25,'其妻苑氏谏曰：','引兵趣长沙。',[('苑氏','劝马希萼不要与兄弟交战'),('马希萼','没有听劝，率兵前往长沙')],when='949年八月仆射洲之战前，具体日未载',place='朗州至长沙方向',note='胜负皆为人笑是苑氏劝说的理由，不作为社会调查结论。')
relationship('马希萼','苑氏','丈夫',25,'其妻苑氏谏曰：','其承接马希萼；方向为马希萼是苑氏的丈夫，名字未载。')
add('ma_xiguang_proposes_yielding','马希广听闻兄长来攻，表示愿让出楚国',25,'马希广闻之曰：','当以国让之而已。”',[('马希广','表示不愿与兄长争斗，愿将楚国让给他'),('马希萼','成为马希广拟让位的对象')],when='949年八月仆射洲之战前，具体日未载',place='长沙',note='这是让位的提议，不写成已经让出统治权。')
relationship('马希萼','马希广','兄长',25,'朗州，吾兄也，不可与争，','复用947年已发布的兄长关系，郎/朗字形不新建亲属或城市主体。')
add('liu_li_oppose_yielding','刘彦瑫、李弘皋等坚决反对马希广让位',25,'刘彦瑫、','固争以为不可，',[('刘彦瑫','坚决反对马希广让出楚国'),('李弘皋','坚决反对马希广让出楚国')],when='949年八月仆射洲之战前，具体日未载',place='长沙',note='等没有列更多人，不补完整反对者名单。')
add('ma_xiguang_assigns_wang_liu','马希广命王赟指挥水军，刘彦瑫监军',25,'乃以岳州刺史','以彦瑫监其军。',[('马希广','任命王赟与刘彦瑫组织水军抵御兄长'),('王赟','由岳州刺史任都部署战棹指挥使'),('刘彦瑫','负责监督王赟所统军队')],when='949年八月仆射洲之战前，具体日未载',place='楚国水军、岳州至长沙附近',note='战棹指挥使为水军职务；监其军未载另有独立官号，不擅补正式监军使任命。')
add('wang_liu_defeat_ma_pushezhou','王赟所部在仆射洲击败马希萼，获战船三百艘',25,'己丑，','获其战舰三百艘。',[('王赟','指挥军队在仆射洲击败马希萼'),('刘彦瑫','监军，在新史中也被记为取胜将领'),('马希萼','在仆射洲战败，损失战船三百艘')],when='949年八月己丑',place='仆射洲',note='主书承接王赟、刘彦瑫部署记胜；三百是获船，不当死亡或俘虏人数。')
sup('wang_liu_defeat_ma_pushezhou',25,chu,'彥瑫敗希萼於僕射洲。','《新五代史》也记刘彦瑫在仆射洲击败马希萼。','同地、同对手对应同一战事，叙述重点在刘彦瑫，不推定王赟没有参战。')
sup('wang_liu_defeat_ma_pushezhou',25,sept,'湖南馬希廣奏，於八月十八日大破朗州馬希萼之眾。','《旧五代史》九月条载马希广奏报，称八月十八日击败朗州马希萼军。','八月十八日为奏报所称交战日，不把九月奏报日当交战日；原纪月日保留，不自行换算公历。',field='time_original')
add('ma_xiguang_recalls_pursuit','王赟追击马希萼，马希广命他撤回，以免伤兄',25,'赟追希萼，','赟引兵还。',[('王赟','追击马希萼，奉命后撤回'),('马希广','派使者召回王赟，要求不要伤害兄长'),('马希萼','被追击，随后对方奉命撤回')],when='949年八月己丑仆射洲之战后，具体召回时刻未载',place='仆射洲至马希萼撤退途中',note='将及之为即将追上，不写成已擒获马希萼后又释放。')
relationship('王环','王赟','父亲',25,'赟，环之子也。','按楚国王环及王赟父子身份复用王环主体，不与后汉刘赟合并。')
add('ma_xie_returns_from_red_sand_lake','马希萼从赤沙湖乘小船逃回朗州',25,'希萼自赤沙湖','乘轻舟遁归，',[('马希萼','战败后从赤沙湖乘小船逃回')],when='949年八月己丑仆射洲之战后，具体归期未载',place='赤沙湖至朗州方向',note='归承接此前从朗州出兵，未载完整行军路线和渡口；不补现代湖泊坐标。')
add('yuan_dies_in_well','马希萼战败归来后，苑氏担忧灾祸，投井而死',25,'苑氏泣曰：',None,[('苑氏','担忧灾祸，不愿目睹，投井而死')],when='949年八月马希萼战败归来后，具体日未载',place='马希萼归处，具体井址未载',note='祸将至为苑氏的判断，不写成预言必然应验；死法按原文，不擅加他人强迫。')
add('guo_wei_returns_receives_rewards','郭威到大梁觐见刘承祐，获赐金帛等',26,'戊戌，','鞍马，',[('郭威','回到大梁入见，获赐金帛、衣服、玉带、鞍马'),('刘承祐','慰劳郭威并赐物')],when='949年八月戊戌',place='大梁',note='本段九月标题在后，戊戌承接八月；赐物未列各类数量和价值。')
sup('guo_wei_returns_receives_rewards',26,guo,'其月二十七日入朝。漢帝命升階撫勞，酌禦酒以賜之，錫賫優厚。','《旧五代史》周太祖纪记郭威八月二十七日入朝，后汉皇帝慰劳并赐酒、赏物。','该篇帝为郭威、汉帝为刘承祐；原文纪日保留，不自行换算公历。',field='time_original')
add('guo_requests_shared_rewards','郭威辞谢独享赏赐，请一并赏赐留京大臣',26,'辞曰：“臣受命期年，','请遍赏之。”',[('郭威','认为留京大臣保障京师与军需有功，请一并赏赐')],when='949年八月戊戌入见时',place='大梁',note='仅克一城是郭威自谦的说辞，不作为史书记全年仅一城被平定的结论。辞谢与随后实际受赏分别记录。')
sup('guo_requests_shared_rewards',26,sept,'此皆居中大臣鎮撫謀畫之功也，臣安敢獨擅其美乎！」帝然之，','《旧五代史》也记郭威将安定京师、保障军需的功劳归于留京大臣，刘承祐赞同。','同一返京论功过程，不把本纪九月叙述中的回顾强定为另一次奏议。')
add('guo_declines_regional_command','郭威拒绝兼领方镇，提出杨邠位在自己之上',26,'又议加领方镇，','不可以弘肇为比。”',[('郭威','拒绝兼领方镇，提到杨邠尚无封土'),('杨邠','被郭威举为位在自己之上的大臣'),('史弘肇','被郭威作为不同职掌的比较对象')],when='949年八月郭威返京论赏期间，具体议赏日未载',place='后汉朝廷',note='杨邠与史弘肇为郭威发言中提及的人，不写成两人亲自出席反对；未有茅土为其说辞，不扩写为杨邠没有任何财产。')
sup('guo_declines_regional_command',26,guo,'翌日，漢帝議賞勛，欲兼方鎮，帝辭之，乃止。','《旧五代史》记入朝次日后汉皇帝欲让郭威兼领方镇，郭威辞谢，议赏停止。','传主帝为郭威；主书未列翌日，作为补充原纪时，不补所议具体藩镇名。',relation='adds',field='time_original')
add('han_rewards_nine_ministers','后汉向九位宰辅和有关使职赐物，待遇与郭威相同',26,'九月，','与威如一。',[('刘承祐','在位朝廷向九位宰辅和使职赐物'),('郭威','成为九位大臣赏赐待遇的比较对象')],when='949年九月壬寅',place='后汉朝廷',note='九人按原文职类合计，不凭后段任官名单补齐九人的身份；与威如一指这次赏赐，不推成全部官阶待遇相同。')
add('guo_refuses_special_reward','刘承祐想特别赏赐郭威，郭威再次辞谢',26,'帝欲特赏威，',None,[('刘承祐','想特别赏赐郭威'),('郭威','认为谋划、粮运和战斗之功属于各方，辞谢独受赏赐')],when='949年九月壬寅遍赏后条下，具体再次辞谢日未载',place='后汉朝廷',note='欲特赏为意向，不生成已经额外发出的赏物数量；辞谢不推出郭威此前完全没接受任何赐物。')
reviews={23:'完整史论关联已发布的郭威撤换留守事件，保留郭威、白文珂、王守恩既有事件。没有新建949年欧阳修活动，也没有用史论补造日期。新史为同作者原论补证，不算独立确证。',24:'献物、贿赂、因早期归附而获宽宥、用事者被杀分开；未列受贿人和被杀者姓名。旧史追讨财物补记原地洛阳，不当全体受害者获完全赔偿。',25:'备战、苑氏劝阻、马希广拟让位、反对、任命、交战、追击、召回、逃归与苑氏死亡分开。郎州原字保留，显示朗州，静江军乡兵不与桂州节镇合并。获船与伤亡不混，王赟与刘赟分开，王环和兄长关系沿用既有主体。',26:'八月返京、辞谢独赏、拒兼方镇、九月遍赏、再次辞特赏分开。期年和仅克一城为郭威说辞，提及杨邠、史弘肇不等于二人亲自出席；九位受赏者不补完整名单。旧史二十七日、翌日另保留原纪时。'}
assert not (P/'publication.json').exists()
for n in range(23,27):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=949,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(23,27)],next_paragraph=Q[27]['id'],next_volume=288,next_year=949,supplements=supplements,excluded_non_body=[],coverage='卷288原101—104行连续四段，含史论一段，949年累计首26/37段；未将史论新建为949年事件，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(23,27)],source_issues_review='欧阳修论与新史原论为同一论述的传承，政治动机属史家解释。楚战新史重刘彦瑫、主书承王赟部署，按同场补证；旧史九月奏报明称八月十八日，不混奏报与交战日。旧史现有楚传有缺佚，不虚构书证。郎/朗州及战船数字按底本保留；地理坐标、纸本与异文待核。',plain_language_review='首次逐条核对标题、人物介绍、事件正文、参与角色、时间地点与事实说明；明确主语，区分史论、建议、任命、实际战果和事后处置。未知日不补公历，未知地不补坐标。原文不改字，复用主体、关系及史论所关联事件保留旧档案，不安排固定发布后二次重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
