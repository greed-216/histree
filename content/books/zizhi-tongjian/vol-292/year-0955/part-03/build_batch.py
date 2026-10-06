# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,40))
COMMIT='8741b9b4a20fa26f3204e3b49150ae61ad62ec9b'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-955-qinfeng-first-order']:
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
main_sources = ['tongjian-292-955-qinfeng-first-order']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0955-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
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
lines = (ROOT / 'resources/derived/tongjian/292.txt').read_text().splitlines()
for n in range(17, 25):
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
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷292·显德二年（955年五月至七月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0955_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=955, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='955年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_292_0955_' + code
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
        edge = 'participation_zztj_292_0955_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0955_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 if kw.get('source'):
  t=(sources[kw['source']]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);quote=t[a:b]
 else:quote=span(n,start,end)
 E[code]=event(code,title,n,quote,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','蜀主':'孟昶','北汉主':'刘承钧','太祖':'郭威','太祖皇帝':'赵匡胤','南汉主':'刘弘熙','王景':'王景（后晋耀州团练使）'})
NEW_ALIASES={'吕彦珂':['呂彥珂'],'赵崇韬':['趙崇韜'],'马遇':['馬遇'],'胡立':[],'张美':['張美']}
NEW_DESCRIPTIONS={
'吕彦珂':'后蜀武宁节度使。955年五月，孟昶安排他作为高彦俦的副手参加北路行营，抵御后周军。生卒年未载。',
'赵崇韬':'后蜀客省使。955年五月，孟昶任命他为北路行营都监，参与抵御后周军的部署。生卒年未载。',
'马遇':'汝州民众。955年六月柴荣亲审囚犯时，查明马遇父亲和弟弟被官吏冤枉致死的情况。《通鉴》未记其家人姓名和后续处理细节。',
'胡立':'后周濮州刺史，955年六月西征时任排陈使，在威武城东与后蜀军交战失利后被俘。生卒年未载。',
'张美':'清河人，后周枢密院承旨。《通鉴》记955年六月任右领军大将军、权点检三司事，《旧五代史》记八月任权判三司，任职月与称号差异分别保留。早年管理澶州隶属三司的财物，曾应柴荣私人所求而供给，郭威得知后将他调到濮州。'
}
td='jiuwudaishi-115-temple-edict-date';tr='jiuwudaishi-115-temple-rationale';rules='jiuwudaishi-115-temple-regulations';reg='jiuwudaishi-115-monk-registers';tot='jiuwudaishi-115-temple-year-totals';jun='jiuwudaishi-115-june-955';jul='jiuwudaishi-115-july-commanders';aug='jiuwudaishi-115-zhangmei-eight-month';nz='xinwudaishi-64-zhao-jizha-return';nh='xinwudaishi-65-liuhongzheng-killed'

add('temple_consolidation','柴荣下令停废没有敕额的寺院',17,'敕天下寺院，','非敕额者悉废之。',[('帝','下令整顿寺院')],when='955年五月，具体日据《旧五代史》记为甲戌',place='后周辖区',description='柴荣下令停废没有朝廷敕赐名额的寺院。《旧五代史》所载诏令还规定，将佛像和僧尼迁入保留的寺院；无敕额寺院的县城、军镇等另有留设例外，不能理解为所有寺院一律拆毁。',note='停废是行政处置，不直接等于所有建筑均已拆毁；详细例外由独立诏令引用说明。')
sup('temple_consolidation',17,td,'甲戌，詔曰：','《旧五代史》将整顿寺院诏令系于五月甲戌。','月份根据同段开头五月辛未核对，甲戌是诏令日，不是全年清点统计日。',field='time_original')
sup('temple_consolidation',17,tr,'將隆教法，須辨否臧，宜舉舊章，用革前弊。','诏令以整顿僧尼违法和寺院管理为理由，宣称目的是维护教法。','这是诏令对政策目的的陈述，不据此认定所有停废寺院都有犯罪。',relation='adds')
sup('temple_consolidation',17,rules,'其無敕額者，並仰停廢，所有功德佛像及僧尼，並騰並於合留寺院內安置。','《旧五代史》记停废寺院的佛像及僧尼须迁入保留寺院安置。','区分寺院停废、人员迁并和建筑拆毁，未记所有僧尼一律还俗。',relation='adds')
sup('temple_consolidation',17,rules,'天下諸縣城郭內，若無敕額寺院，只於合停廢寺院內，選功德屋宇最多者，或寺院僧尼各留一所，若無尼住，只留僧寺院一所。諸軍鎮坊郭及二百戶已上者，亦依諸縣例指揮。如邊遠州郡無敕額寺院處，於停廢寺院內僧尼各留兩所。','无敕额寺院的县城可在原定停废寺院中按条件留设僧寺、尼寺；军镇坊郭和二百户以上聚落按同类规则办理，边远州郡另有各留两所的规定。','保留诏令例外与数量，不把主书简述解释为毫无例外的建筑清零。',relation='adds')
sup('temple_consolidation',17,rules,'今後並不得創造寺院蘭若。王公戚裏諸道節刺已下，今後不得奏請創造寺院及請開置戒壇。','诏令还禁止新建寺院，并禁止王公、外戚及地方长官申请新建寺院和开置戒坛。','新建禁令与既有寺院停废分别说明。',relation='adds')
add('ordination_rules','柴荣禁止私度僧尼，并规定出家须获家人许可',17,'禁私度僧尼，','伯叔之命。',[('帝','规定出家许可条件并禁止私自剃度')],when='955年五月寺院整顿诏令',place='后周辖区',description='柴荣禁止未经许可剃度僧尼，要求有意出家者先取得家人同意。《旧五代史》详记按父母祖父母、已孤者同居伯叔兄等情况处理，并设年龄、经文考核和奉养家人等条件。')
sup('ordination_rules',17,rules,'男子女子如有誌願出家者，並取父母、祖父母處分，已孤者取同居伯叔兄處分，候聽許方得出家。','《旧五代史》详记家庭许可条件：须获父母、祖父母同意，已孤者取同居伯叔兄许可。','按家庭情形分列，不译为所有亲属同时同意。',relation='adds')
sup('ordination_rules',17,rules,'男年十五已上，念得經文一百紙，或讀得經文五百紙，女年十三已上，念得經文七十紙，或讀得經文三百紙者，經本府陳狀乞剃頭，委錄事參軍本判官試驗經文。','诏令规定男性十五岁以上、女性十三岁以上，并须通过经文考核和官府申请程序。','纸为底本经文计量，不换算成现代页数；考核背诵和阅读标准分别保留。',relation='adds')
sup('ordination_rules',17,rules,'應男女有父母、祖父母在，別無兒息侍養，不聽出家。','家中有父母祖父母在世而无其他子女侍养者，不准出家。','体现赡养条件，不据诏令推定每一僧尼的具体家庭情况。',relation='adds')
add('ordination_platforms','柴荣限定两京等地可以设置戒坛',17,'惟两京、','听设戒坛。',[('帝','限定受戒地点')],when='955年五月寺院整顿诏令',place='两京、大名府、京兆府、青州',note='两京沿史载名称，不给未经核实的现代坐标。')
sup('ordination_platforms',17,rules,'兩京、大名府、京兆府、青州各處置戒壇，候受戒時，兩京委祠部差官引試，其大名府等三處，只委本判官錄事參軍引試。','《旧五代史》同时说明两京由祠部差官引试，其他三处由当地判官、录事参军考核。','这是受戒管理规则，不虚构各地实际受戒人数。',relation='adds')
add('ban_body_harm_rituals','柴荣禁止以毁伤身体等方式聚众惑众',17,'禁僧俗舍身、','幻惑流俗者。',[('帝','禁止以自伤等行为聚众惑众')],when='955年五月寺院整顿诏令',place='后周辖区',description='柴荣禁止僧俗以舍身、断手足、炼指、挂灯、带钳等方式聚众惑众。这里记录诏令及其对这些行为的判断，未据此认定所有宗教活动都属欺骗。')
sup('ban_body_harm_rituals',17,reg,'今後一切止絕。如有此色人，仰所在嚴斷，遞配邊遠，仍勒歸俗，其所犯罪重者，準格律處分。','《旧五代史》所载诏令还规定相关处罚，包括发配边远、勒令还俗，罪重者依律处置。','这是处罚规定，不当作已有全部施行的具名案件。',relation='adds')
add('annual_monk_registers','柴荣要求每年编造僧尼名册，及时登记死亡和还俗',17,'令两京及诸州','皆随时开落。',[('帝','要求建立并更新僧尼名册')],when='955年五月诏令规定此后每年办理',place='两京及后周诸州',note='每岁是制度周期，不能把未来各年编册当作955年已逐次完成。')
sup('annual_monk_registers',17,reg,'每年造僧帳兩本，其一本奏聞，一本申祠部，逐年四月十五日後，勒諸縣取索管界寺院僧尼數目申州，州司攢帳，至五月終已前文帳到京，僧尼籍帳內無名者，並勒還俗。','名册每年造两份，一份奏报，一份送祠部；县自四月十五日后上报，州汇总后须在五月底前送京，未列名者勒令还俗。','这是按年执行的规定，不将首次诏令前的四月十五日当作当年已执行的确日。',relation='adds')
add('temple_annual_totals','《通鉴》统计955年保留和停废寺院及登记僧尼人数',17,'是岁，',None,[],when='955年全年汇总，统计截止日未载',place='后周辖区',description='《通鉴》记955年保留寺院2694所，停废30336所，登记僧人42444名、尼僧18756名。《旧五代史》记寺院两项数量相同，僧尼登记合计61200人。这些是史书记载的当年汇总，不是五月诏令颁布当天的实测数字。')
sup('temple_annual_totals',17,tot,'是歲，諸道供到帳籍，所存寺院凡二千六百九十四所，廢寺院凡三萬三百三十六，僧尼系籍者六萬一千二百人。','《旧五代史》按各道送交账籍汇总，保留寺院2694所、停废30336所、登记僧尼61200人，与主书僧尼两项相加相符。','42444加18756为61200；保存各书统计口径，不写成中国所有地区寺院和僧尼的普查。')

add('wangjing_captures_eight_forts','王景攻取黄牛等八座寨堡',18,'王景拔','八寨。',[('王景','率后周军攻取八座寨堡')],when='955年五月戊寅部署之前，具体日未载',place='黄牛等八寨',note='只载一处寨名，不虚构其余七寨名称或坐标。')
add('shu_northern_commanders','孟昶任李廷珪等四人统率北路行营',18,'戊寅，',None,[('蜀主','任命北路行营将领'),('李廷珪','任北路行营都统'),('高彦俦','任招讨使'),('吕彦珂','任高彦俦副手'),('赵崇韬','任都监')],when='955年五月戊寅',place='后蜀北路行营',description='孟昶任捧圣控鹤都指挥使、保宁节度使李廷珪为北路行营都统，左卫圣步军都指挥使高彦俦为招讨使，武宁节度使吕彦珂为副手，客省使赵崇韬为都监。')
add('zhaojizha_turns_back','赵季札到德阳后畏惧周军，请求解除边任并安排家属财物西归',19,'蜀赵季札','及妓妾西归。',[('赵季札','未赴边任，求解职回奏并先遣辎重及妓妾西归')],when='955年五月丁亥回成都之前',place='德阳',description='赵季札到德阳，听说后周军入境后不敢继续前行。他上书请求解除边任、回朝奏事，并先送辎重及妓妾向西返回。此处没有记载赵季札曾抵达秦州。')
sup('zhaojizha_turns_back',19,nz,'季札行至德陽，聞周兵至，遽馳還奏事。','《新五代史》也记赵季札到德阳，闻周军到来后赶回奏事。','前次受命为监军不等于实际到达秦州；本条才记回返行动。')
add('zhaojizha_return_panic','赵季札独自骑马回成都，民众误以为军队战败而惊恐',19,'丁亥，','莫不震恐。',[('赵季札','单骑驰入成都，引起战败误解')],when='955年五月丁亥',place='成都',note='众以为奔败是民众的误解，本条不证明当日后蜀军已经战败。')
add('zhaojizha_imprisoned','孟昶问赵季札军情，因他不能回答而将其拘押',19,'蜀主问以机事，','系之御史台，',[('蜀主','询问军情后命拘押赵季札'),('赵季札','不能回答军情，被拘押在御史台')],when='955年五月丁亥回成都之后、甲午处死之前',place='成都御史台')
add('zhaojizha_executed','孟昶在崇礼门处死赵季札',19,'甲午，',None,[('蜀主','命处死赵季札'),('赵季札','在崇礼门被处死')],when='955年五月甲午',place='成都崇礼门')
sup('zhaojizha_executed',19,nz,'昶問之，季札惶懼不能道一言，昶怒殺之，','《新五代史》也记孟昶因赵季札无法回答而将他杀死。','新史没有单列甲午纪日，不能凭此抹去主书明确的拘押、处死两阶段。')
claim('person',people['赵季札'],'death_year','赵季札于955年五月甲午在成都被处死。',19,span(19,'甲午，'),'保存有出处的死年事实；复用人物档案的其他字段不在本次覆盖。')
add('chairong_reviews_prisoners','柴荣在内苑亲自审查囚犯',20,'六月，','内苑。',[('上','在内苑亲审囚犯')],when='955年六月庚子',place='后周内苑')
add('mayu_wrongful_deaths','柴荣审查马遇一案，查明其父亲和弟弟被官吏冤枉致死',20,'有汝州民马遇，','始得其实，',[('上','亲问后查明冤情'),('马遇','父亲和弟弟被冤枉致死，多次复查仍未能申冤')],when='955年六月庚子查明；此前冤死和复查的具体时间未载',place='后周内苑，案涉汝州',description='汝州民众马遇的父亲和弟弟被官吏冤枉致死，多次复查仍未能申冤。柴荣亲自询问才查明情况。史书未记涉案官吏、亲属姓名和后续赔偿处罚细节。',note='庚子用于查明案件，不把更早的冤死也强定为同一天；不根据未载姓名建立虚构人物。')
add('officials_personal_case_reviews','《通鉴》记马遇案后，各地方长官亲自察看诉讼',20,'人以为神。',None,[('上','亲审查明冤情受到称赞')],when='955年六月庚子马遇案之后，具体日未载',place='后周地方官府',description='《通鉴》记柴荣查明马遇案后，人们赞叹其判断，各地长官也因此亲自察看诉讼。这里保留史书对影响的概述，不推成所有案件此后都已无冤错。')

add('weiwu_east_defeat','后周军在威武城东失利，胡立等人被后蜀军俘获',21,'壬寅，','为蜀所擒。',[('李廷珪','率后蜀军与周军交战'),('胡立','以排陈使、濮州刺史身份参战，被俘')],when='955年六月壬寅',place='威武城东',note='主书未逐一点名现场周军主将及其余被俘者，不仅据此前部署将所有统帅加为直接交战者。')
add('shu_seeks_coalition','孟昶派秘密使者联络北汉和南唐，提议共同出兵牵制后周',21,'丁未，','俱出兵以制周，',[('蜀主','秘密派使联络两国共同出兵')],when='955年六月丁未派使',place='后蜀至北汉、南唐',note='间使是秘密使者，不擅自译成已有具体间谍组织；使者姓名未载。')
add('northern_han_tang_agree','刘承钧和李璟同意孟昶提出的联合出兵计划',21,'蜀主遣间使',None,[('蜀主','提出联合出兵牵制后周'),('北汉主','同意联合出兵提议'),('唐主','同意联合出兵提议')],when='955年六月丁未派使之后，答复具体日未载',place='北汉和南唐朝廷',description='孟昶遣使邀请北汉、南唐共同出兵制约后周，刘承钧、李璟都答应。这是接受计划的记载，本段没有证明两国已经在丁未当天出兵。',note='主书当时北汉主按前段继位为刘承钧，沿既有主体；各国后续实际出兵另按后文录入。')
add('hantong_southwest_inspector','柴荣任韩通为西南行营马步军都虞候',22,Q[22]['text'],None,[('帝','任命韩通承担西南行营职务'),('韩通','由彰信节度使充西南行营马步军都虞候')],when='955年六月己酉',place='后周西南行营')
sup('hantong_southwest_inspector',22,jun,'六月己酉，以曹州節度使韓通充西南面行營都虞候。','《旧五代史》也记六月己酉任韩通为西南面行营都虞候，任前称曹州节度使。','彰信军与曹州称法及行营职名详略分别保留，不据称法不同另建韩通人物。')
add('liuhongzheng_killed','刘弘熙杀死通王刘弘政',23,'戊午，',None,[('南汉主','杀死通王刘弘政'),('刘弘政','以祯州节度使、通王身份被杀')],when='955年六月戊午',place='南汉',description='南汉君主刘弘熙杀死祯州节度使、通王刘弘政。《通鉴》随后概述刘岩的其他儿子至此均已被杀；这句话不表示正在位的刘弘熙本人也已去世。',note='君主沿刘弘熙既有主体，别名刘晟已另有核定记录；高祖指刘岩，概述有在位者语境，不新造刘弘熙死亡事件。')
sup('liuhongzheng_killed',23,nh,'十三年，又殺其弟洪政，於是龑之諸子盡矣！','《新五代史》记乾和十三年杀弟洪政，并有刘龑诸子尽的同类概述。','十三年置于该传乾和纪年上下文；洪政与主书弘政沿既有刘弘政主体，不能把兄弟关系概述理解为刘晟已死亡。')
claim('person',people['刘弘政'],'death_year','刘弘政于955年六月戊午被刘弘熙杀死。',23,Q[23]['text'],'死亡事实有主书明确纪日，不覆盖旧档案的其他生平字段。')

add('zhangmei_finance_appointment','柴荣任张美为右领军大将军，暂掌三司事务',24,'壬戌，','权点检三司事。',[('帝','任张美掌财务事务'),('张美','由枢密院承旨获任右领军大将军、权点检三司事')],when='《通鉴》记955年六月壬戌；《旧五代史》记八月丁未权判三司',place='后周朝廷',note='主书记权点检三司事，旧史记权判三司且月日不同，分别保存，不强行归为同日或断定一定是两次任命。')
sup('zhangmei_finance_appointment',24,aug,'丁未，中書侍郎、平章事、判三司景範罷判三司，加銀青光祿大夫，依前中書侍郎、平章事，進封開國伯；以樞密院承旨張美權判三司。','《旧五代史》记八月丁未景范罢判三司、张美权判三司。','段首八月癸卯明确月份；任职时点和称号与主书有差异，本次并列同主体出处，不先行录入未来景范的独立八月事件。',relation='conflicts')
add('zhangmei_private_supplies','张美在澶州管理财物时，曾应柴荣私人所求供给',24,'初，帝在澶州，','美曲为供副。',[('帝','在澶州时曾向张美私下求取财物'),('张美','管理隶三司的州财物，并应柴荣私人所求供给')],year=None,when='柴荣在澶州期间的追述，具体年份和日期未载',place='澶州',note='柴荣在澶州的早年经历，不套用955年；原文未记具体金额，不添加贪污数额。')
add('zhangmei_transferred_puzhou','郭威得知张美向柴荣私人供给后，将张美调到濮州',24,'太祖闻之怒，','为濮州马步都虞候。',[('太祖','得知财物供给后生气，将张美调走'),('张美','被调任濮州马步都虞候')],year=None,when='郭威在位期间、张美澶州供给之后，具体年日未载',place='澶州至濮州',description='郭威得知张美为柴荣私人供给财物后发怒，但顾虑伤及柴荣的心意，只将张美调为濮州马步都虞候。这里的太祖是后周郭威，不能与同段后文所称宋太祖赵匡胤混同。')
claim('person',people['张美'],'evaluation','《通鉴》称张美理财精敏，帮助柴荣征伐时保障费用，但柴荣因澶州旧事始终不以公忠相待。',24,span(24,'美治财精敏，','终不以公忠待之。'),'保存史书对能力和君臣信任的评价；征伐四方为概述，不把今后各场战事都记录为955年已发生。')
add('qinfeng_commanders_july','柴荣任王景为西南行营都招讨使、向训为兵马都监',24,'秋，七月，','兼行营兵马都监。',[('帝','调整西征行营指挥职务'),('王景','兼西南行营都招讨使'),('向训','兼行营兵马都监')],when='955年七月丁卯朔',place='后周西南行营')
sup('qinfeng_commanders_july',24,jul,'秋七月丁卯朔，以鳳翔節度使王景兼西南面行營都招討使，以宣徽南院使、鎮安軍節度使向訓兼西南面行營都監。','《旧五代史》同日记王景、向训两项行营任命。','向训职名有兵马都监和行营都监的详略差别，沿同一人物与同一次任命。')
add('ministers_propose_withdrawal','宰相因秦凤战事久无功、粮运不继，请求撤兵',24,'宰相以景等久无功。','固请罢兵。',[],when='955年七月行营任命以后，具体日未载',place='后周朝廷',note='宰相未逐一具名，不仅因现职名单就建所有宰相直接参与；请求撤军与最终决策分开。')
add('zhaokuangyin_qinfeng_inspection','柴荣派赵匡胤察看秦凤战局，听取可继续进取的报告',24,'帝命太祖皇帝',None,[('帝','命赵匡胤往察战局并采纳其报告'),('太祖皇帝','察看后返回，报告秦凤可以攻取')],when='955年七月撤兵讨论之后，具体往返日未载',place='后周朝廷至秦凤军前',description='柴荣派赵匡胤到秦凤军前察看战局。赵匡胤回来后报告秦、凤可以攻取，柴荣听从其意见，继续推进战事。此处太祖皇帝是史书对后来宋太祖的称呼，赵匡胤当时尚未称帝。',note='可取是勘察后的判断，不在本段提前记录秦凤已全部攻下。')

reviews={
17:'寺院停废诏令与例外、家庭许可、年龄考核、戒坛、自伤禁令、年度名册及全年统计分别处理；全年僧尼数字相加与旧史61200相符，未当五月当天统计。',
18:'八寨只有黄牛具名；四将同一次五月戊寅任命，李廷珪高彦俦复用、吕彦珂赵崇韬新增。',
19:'德阳畏敌请求返回、丁亥单骑回成都、拘押和甲午处死分别处理，新史补证没有单列纪日；此前任命不等到任。',
20:'六月庚子只用于柴荣亲审查明冤案，不给父弟冤死同日。马遇家人与官吏姓名未载，不虚构；神判和各长官察狱是史书评价及影响概述。',
21:'威武城东失利和胡立被俘、丁未秘密联络、两国接受计划分开，未记同日实际出兵。北汉主沿主书前段刘承钧继位主体。',
22:'韩通沿同人，彰信曹州与都虞候称法详略并列。',
23:'南汉主沿刘弘熙即刘晟，弘政洪政沿旧主体；诸子尽的概述不包含仍在位的杀人者本人死亡。',
24:'张美六月与旧史八月任三司的时点异说保留。澶州供给、郭威调职为旧事year null；同段太祖郭威、太祖皇帝赵匡胤明确区分。七月两将任命、宰相撤军请求、赵匡胤勘察与采纳分开，秦凤可取不是已平。'}
assert not (P/'publication.json').exists()
for n in range(17,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=955,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=292,next_year=955,supplements=supplements,excluded_non_body=[],coverage='原49—56行连续八段，从寺院整顿至七月秦凤战事讨论；含追述但不将以后攻取结果提前录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],source_issues_review='张美六月与八月掌三司并列；诏令日期核五月甲戌，统计保留全年范围；新史赵季札叙次和弘洪字形保留。所有原文快照保留底本，纸本待核。',plain_language_review='首次逐条检查人物、事件标题、说明、参与角色、时间和事实引用的解释均使用明确主语与现代白话。太祖指代、计划与执行、制度与全年统计分别说明，原文保持原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
