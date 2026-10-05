# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 55–61."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='38a4f1055550253802e2379fcd8a0add8913c3da'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-xuzhou-march','jiuwudaishi-099-march-rising','xinwudaishi-010-accession','xinwudaishi-062-chen-jue-fuzhou','liaoshi-116-xiao-kinship']:
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
main_sources = ['tongjian-286-947-xuzhou-march']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p055-p061',
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
for n in range(55, 62):
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
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷286·天福十二年（947年三月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_11_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','契丹主':'耶律德光','周密':'周密（后晋节度使）','高彦询':'高彦珣','蜀主':'孟昶','汉韶':'孙汉韶','太后':'述律平','延鲁':'冯延鲁','李达':'李仁达','建封':'王建封','崇文':'王崇文','陈觉':'陈觉'})
NEW_ALIASES={'余安':[],'孟坚':['孟堅'],'刘洪进':['劉洪進']}
NEW_DEATH_YEARS={'孟坚':947}
NEW_DESCRIPTIONS={
'余安':'吴越将领。947年率水军从海道救援福州，三月己亥到白虾浦，与城内军队夹击南唐军，后领兵入福州，接管李仁达所部。生卒年未载。',
'孟坚':'南唐裨将。947年福州战事中，反对冯延鲁放吴越军登岸再围杀的计划，意见未被接受，随后战死。生年未载。',
'刘洪进':'福州战事中的南唐东南守将。947年听说吴越军可能撤离后，与其他将领建议王建封放其出城再取福州，未被采纳。生卒年未载。'}
j='jiuwudaishi-099-march-rising';nw='xinwudaishi-010-accession';nt='xinwudaishi-062-chen-jue-fuzhou';ls='liaoshi-004-march-deployment';kin='liaoshi-116-xiao-kinship'
t='947年三月，具体日未载'
add('liu_reassures_refugee_farmers','刘知远遣使持诏书，安抚聚居山谷躲避契丹的农民',55,'戊子，',None,[('帝','派使者持诏安抚避乱农民')],when='947年三月戊子',place='农民避乱聚居的山谷，具体地点未载',note='安集为安抚聚集安顿之意，未载实际返乡人数、所给钱粮或恢复耕作面积。')
add('gao_yunquan_submits_yanzhou','高允权上表归附刘知远',56,'辛卯，','奉表来降。',[('高允权','以延州暂任留后身份上表归附')],when='947年三月辛卯',place='延州至刘知远朝廷',note='此前获推留后与本次上表分别记录，不把二月城内变动强定为辛卯。')
sup('gao_yunquan_submits_yanzhou',56,j,'辛卯，權延州留後高允權遣判官李彬奏：本道節度使周密為三軍所逐，以允權知留後事，上表歸順。','《旧五代史》也在辛卯记高允权遣判官上表归顺，并说明周密被逐。','补书奏报说明的先前行动不能全部强定为同日，本批不另建重复城内起兵事件。')
add('liu_allows_zhou_mi_leave_yanzhou','刘知远命高允权允许周密到行在，周密放弃东城前来',56,'帝谕',None,[('帝','命高允权允许周密离城来行在'),('高允权','收到允许周密赴行在的命令'),('周密','放弃东城到刘知远行在')],when='947年三月辛卯条下，赴行在具体日未载',place='延州东城至刘知远行在',note='听为允许，不译作听取周密建议；命令与随后出行相接，但不硬定到达日。')
sup('liu_allows_zhou_mi_leave_yanzhou',56,j,'未幾，帝召密赴行在。','《旧五代史》也记不久后召周密到行在。','未几是相对次序，不给固定天数。',relation='adds')
add('gao_yanxun_submits_danzhou','高彦珣以丹州归附刘知远',57,'壬辰，',None,[('高彦询','以丹州归附刘知远')],when='947年三月壬辰',place='丹州至刘知远朝廷',note='本段原字彦询，复用前批高彦珣；杀刺史的行为已在前批录入，此处是正式归附。')
sup('gao_yanxun_submits_danzhou',57,nw,'壬辰，丹州指揮使高彥詢以其州來歸。','《新五代史》同记壬辰高彦询以丹州归附。','同职同事与主书一致，引用保持本书字形，不新建询、珣两个主体。')
add('li_hao_requests_fengzhou_attack','李昊向王处回分析固镇、兴州援秦路线，建议孙汉韶急攻凤州',58,'蜀翰林承旨','将兵急攻凤州。”',[('李昊','以翰林承旨身份建议急攻凤州'),('王处回','以枢密使身份听取建议'),('孙汉韶','被建议为出兵将领')],when='947年三月癸巳之前，具体日未载',place='后蜀朝廷；固镇、兴州、秦州及凤州（议论地点）',note='敌复据固镇、兴州道绝是李昊的形势分析，不据此另造一次未有叙述的夺镇战；建议不等于已经取凤州。')
add('meng_orders_sun_to_fengzhou','孟昶命孙汉韶赴凤州行营',58,'癸巳，',None,[('蜀主','命孙汉韶到凤州行营'),('孙汉韶','奉命前往凤州行营')],when='947年三月癸巳',place='后蜀至凤州行营',note='命诣行营为部署，不写成当日已经攻破凤州。山南西道官职见前句，沿原主体。')
add('khitan_announces_return_plan','耶律德光召晋百官，称天气将热，打算暂回契丹探望太后并留亲信镇守',59,'契丹主复召','为节度使。”',[('契丹主','宣布暂回契丹及留亲信镇守的计划')],when=t,place='大梁',note='天时向暑是本人提出的理由，宣布计划不表示已离开大梁；初段未点名留守者，不提前替换为萧翰。')
add('khitan_rejects_moving_mother','晋百官请迎述律太后到中原，耶律德光以其家族如古柏根难移为由拒绝',59,'百官请迎','不可移也。”',[('契丹主','拒绝迁太后来中原的建议')],when=t,place='大梁朝廷',note='古柏根是家族根基的譬喻，不转成真实地理树木；百官未名，不自动添加全部晋官。')
add('khitan_changes_mass_official_transfer','耶律德光原想带走全部晋百官，听取逐步迁移建议后，只命有职事者同行',59,'契丹主欲尽','馀留大梁。',[('契丹主','改变全部迁官计划，只令有职事者同行')],when=t,place='大梁至契丹（迁官计划）',note='或曰未名，不猜建议者。诏令不证明所有职事官都实际同行，也不补完整留京名单。')
add('khitan_restores_xuanwu_assigns_xiao','耶律德光恢复汴州宣武军名号，任萧翰为节度使',59,'复以汴州','以萧翰为节度使。', [('契丹主','恢复宣武军并任萧翰节度使'),('萧翰','获任宣武节度使')],when=t,place='汴州宣武军',note='授职的日期另据《辽史》补引，主书此句未标具体日；不将后文有争议的亲属说法当作授职的确定原因。')
sup('khitan_restores_xuanwu_assigns_xiao',59,ls,'三月丙戌朔，以蕭翰為宣武軍節度使','《辽史》在三月丙戌朔记任萧翰为宣武节度使。','主书三月条下没有独立标日，辽史明确朔日，各书定位分别保留，不推第二次任命。',relation='adds',field='time_original')
claim('person',people['萧翰'],'description','《通鉴》本段称萧翰为述律太后的兄子，其妹为契丹主皇后。',59,span(59,'翰，述律','契丹主后。'),'当前段与先前契丹主之舅的写法不同，辽史亦保存不同说法，亲属待核，不新增确定的姑侄或兄妹关系。')
claim('person',people['萧翰'],'description','《通鉴》记萧翰开始以萧为姓，并解释后族自此皆称萧氏。',59,span(59,'翰始以萧',None),'这是主书关于姓氏起源的说法，《辽史》对此提出异议，分别引用，不当已经解决的唯一族源结论。')
claim('person',people['萧翰'],'description','《辽史》质疑萧翰是述律皇后的侄子、萧翰之妹为皇后，并由此形成后族萧姓的说法，认为这与本纪不合。',59,'有謂述律皇后兄子名蕭翰者，為宣武軍節度使，其妹復為皇后，故后族皆以蕭為姓。其說與紀不合，故陳大任不取。','补书对同一亲属与族姓说法的明确质疑，保留待核；未据此猜定另一套亲属关系。',source=kin,relation='conflicts')
add('wuyue_sends_yu_an_navy','吴越再次派水军，由余安率领从海道救援福州',60,'吴越复发','自海道救福州。',[('余安','率吴越水军从海道救福州')],when='947年三月己亥之前，具体出发日未载',place='吴越海道至福州',note='没有写此行实际领兵人数，不将前书概述三万兵直接填成本次余安水军人数。')
add('yu_an_arrives_baixiapu_landing_blocked','余安水军到白虾浦，因岸边泥淖和南唐射击而无法铺竹箦登岸',60,'己亥，','箦不得施。',[('余安','水军抵白虾浦，登岸受阻')],when='947年三月己亥',place='福州白虾浦',note='竹箦为登岸所用竹铺具，泥淖与射击阻碍同时按原文记；城南南唐将领未在此句逐名，不补所有人参与。')
add('feng_plans_trap_onshore','冯延鲁主张放吴越军登岸再尽杀，认为可使福州不战而降',60,'冯延鲁曰：','城不攻自降矣。”',[('冯延鲁','提出放军登岸再围杀的计划')],when='947年三月己亥到白虾浦后，具体日未载',place='福州城南、白虾浦',note='尽杀、不攻自降为计划及预期，没有实际发生，不把福州已降写入本事件。')
add('meng_jian_warns_against_landing','孟坚反对放吴越军登岸，认为受困军队会拼死作战难以抵挡，冯延鲁不听',60,'裨将孟坚','吾自击之。”',[('孟坚','分析吴越军拼死作战风险，反对登岸计划'),('冯延鲁','拒绝孟坚建议，称自己来击敌')],when='947年三月己亥到白虾浦后，具体日未载',place='福州城南',note='求一战而死、锋不可当是孟坚判断，不当真实死亡统计；裨将身份按本句。')
add('wuyue_landing_routes_feng_meng_dies','吴越军登岸奋击，冯延鲁弃军逃走，孟坚战死',60,'吴越兵既登岸，','孟坚战死。',[('冯延鲁','无法抵挡登陆军，弃军逃走'),('孟坚','在登陆战中战死'),('余安','所率吴越军登岸奋击')],when='947年三月己亥到白虾浦后，具体战日未载',place='福州白虾浦、城南',note='兵既登岸表示实际登陆，与前面提出计划分开；余安为前文水军将领，不补其亲手击杀孟坚。')
add('fuzhou_garrison_joins_counterattack','吴越军乘胜推进，福州城内军队出击，夹攻南唐军，城南各军败退',60,'吴越兵乘胜','吴越兵追之。',[('余安','所率军与城内军夹击、追击南唐军')],when='947年三月白虾浦登陆战之后，具体日未载',place='福州城南',note='城内军队此句未点将名，不自动写为李仁达亲自领兵。')
sup('fuzhou_garrison_joins_counterattack',60,nt,'延魯與吳越兵先戰，大敗而走，諸軍皆潰歸。','《新五代史》也记冯延鲁先与吴越兵战、败走，各军溃归。','补书记述较简，不把其概括说法代替主书孟坚战死和王崇文阻追等具体次序。')
add('wang_chongwen_stops_pursuit','王崇文率三百牙兵抵御追兵，各军在其后列阵，吴越追兵退回',60,'王崇文',None,[('王崇文','以三百牙兵抵挡追兵、掩护各军列阵')],when='947年三月城南诸军败退之后，具体日未载',place='福州城南',note='三百为此时牙兵人数，不当南唐全军只余三百；追者乃还是追兵返回，不表示整个救援军撤出福州。')
add('liu_hongjin_proposes_enter_after_departure','有人传言吴越军要撤离，刘洪进等建议王建封放他们全出城后取城',61,'或言浙兵','而取其城。',[('刘洪进','据撤离传言提出趁出城取城建议'),('建封','收到取福州建议')],when='947年三月城南战败之后，具体日未载',place='福州东南',note='吴越欲拔李达军归钱唐是传言，不是已经执行的撤兵命令；白王建封为向其报告，不是报告给王崇文。')
add('wang_jianfeng_refuses_city_attack','王建封不满陈觉等专横，拒绝取城建议，称军队败了无法争城',61,'留从效不欲','安能与人争城！”',[('建封','拒绝趁对方出城取城的建议'),('留从效','被史书解释为不愿福州被平定'),('陈觉','被史书列为王建封不满的对象')],when='947年三月城南战败之后，具体日未载',place='福州围城营地',note='留从效意图与王建封不满是史家动机解释，不据此新建二人已经密谋的同盟关系；拒绝建议不等于吴越真已出城。')
add('nantang_burns_camps_collapses','南唐东南军当晚焚营逃走，城北军也相继溃散',61,'是夕，','相顾而溃。',[],when='947年三月拒绝取城建议当晚，具体干支日未载',place='福州东南及城北围城营地',note='本句未逐名各营将领，不把所有南唐主帅都连成亲手烧营者。是夕为相对时段，不硬定己亥当天。')
add('feng_attempts_self_stabbing_survives','冯延鲁持佩刀自刺，被亲近吏员救下，未死',61,'冯延鲁引','不死。',[('冯延鲁','以佩刀自刺，被救后未死')],when='947年三月南唐军溃散时，具体日未载',place='福州战场附近',note='引佩刀自刺不补伤口位置；救者未名，不猜身份，不能把孟坚战死与冯延鲁未死混淆。')
add('nantang_fuzhou_losses','史书记南唐军死二万余人、遗弃大量军资器械，府库因此耗竭',61,'唐兵死者','府库为之耗竭。',[],when='947年三月福州败退后的损失总述',place='福州战场及南唐府库',note='二万余人是史书记数，未作独立统计核实；器械数十万未给计量单位，不填金额、件数或折算币值。')
add('yu_an_enters_fuzhou_takes_troops','余安率军进入福州，李仁达将所部交给他',61,'余安引兵',None,[('余安','领军入福州并接收守军'),('李达','将所部交余安')],when='947年三月南唐围城军败退后，具体日未载',place='福州',note='李达沿已有李仁达主体；移交所部不自动写成吴越已经改设全部当地官制或李仁达立即赴钱唐。')
reviews={55:'戊子安抚避乱农民，未补实际返乡人数钱粮。',56:'辛卯上表与随后允许周密离东城赴行在分别记录，补书未几不换固定日。',57:'彦询复用前批彦珣，壬辰归附与前批杀刺史分开。',58:'李昊形势分析、建议与癸巳孙赴行营分记，不写成已取凤州。',59:'回国省太后意向、迁官方案及宣武任命分清，辽史另给朔日；萧翰亲属与姓氏起源保留主书和辽史质疑，不新建确定亲属。',60:'水军到达受阻、放行计划与反对、实际登岸、冯逃孟死、夹击与三百牙兵阻追连续记录，不把计划写成胜利。',61:'撤吴越传言、取城建议与拒绝、营溃、自刺未死、损失总述及移交守军分清；器械数字没有单位，不补金额。'}
assert not (P/'publication.json').exists()
for n in range(55,62):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(55,62)],next_paragraph=Q[62]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原60—66行连续七段，累计61/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(55,62)],source_issues_review='丹州字形同人复用；萧翰亲属与姓氏起源有异说，不建确定关系；辽史任宣武系朔日与主书条下位置分别保留；福州战损为史书记数，军资无单位。',plain_language_review='首次核对全部展示字段与事实引用，区分计划、假设、传言、观点与实际行动；福州战事按次序说明，原文保持底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
