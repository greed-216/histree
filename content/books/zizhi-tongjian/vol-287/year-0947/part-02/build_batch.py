# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,76))
COMMIT='cb7c4e8e14cca0f06693158578b4b0287925c9b1'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-southern-march','jiuwudaishi-100-may-march','jiuwudaishi-051-li-congyi','songshi-261-li-wanchao']:
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
main_sources = ['tongjian-287-947-southern-march','tongjian-287-947-jinzhou-north-return']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p009-p016',
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
lines = (ROOT / 'resources/derived/tongjian/287.txt').read_text().splitlines()
for n in range(9, 17):
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
        citation = f'卷287·天福十二年（947年五月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_02_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_287_0947_' + code
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
        edge = 'participation_zztj_287_0947_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_287_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','兀欲':'耶律阮','麻荅':'麻答','拽剌':'拽剌（西奚王）','淑妃':'王淑妃','从益':'李从益','翟光鄴':'翟光邺','阿保机':'耶律阿保机'})
NEW_ALIASES={'翟令奇':[],'张环（晋宦官）':['張環（晉宦官）'],'王松':['王鬆'],'刘祚':['劉祚'],'刘审交':['劉審交'],'高奉明':[]}
NEW_DESCRIPTIONS={
'翟令奇':'947年担任泽州刺史，起初拒守，后接受李万超的劝说，向史弘肇投降。生卒年未载。',
'张环（晋宦官）':'晋朝宦官。947年拒绝将滋德宫宫人交给萧翰，遭萧翰拘押并用刑杀害。与渝州刺史张环分别建档。',
'王松':'947年原任礼部尚书，萧翰拥立李从益后，将王松任为宰相。《旧五代史》写作王鬆，并记为左丞相。生卒年未载。',
'刘祚':'947年任北来指挥使，萧翰拥立李从益后，任他暂掌侍卫亲军并兼在京巡检。生卒年未载。',
'刘审交':'字求益，幽州文安人。947年萧翰在汴州时重新任用他为三司使。萧翰北归后，他反对闭城拒守，主张听从王淑妃的迎接刘知远方案。生卒年尚未录入。',
'高奉明':'原任武州刺史。947年五月，耶律阮北归前任命他为安国节度使。生卒年未载。'}
NEW_DEATH_YEARS={'张环（晋宦官）':947}
j='jiuwudaishi-100-may-march';li='jiuwudaishi-051-li-congyi';song='songshi-261-li-wanchao';liu='jiuwudaishi-106-liu-shenjiao';t='947年五月，具体日未载'
add('shi_reports_zezhou_surrender','史弘肇报告泽州归降',9,'丁酉，','史弘肇奏克泽州。',[('史弘肇','向刘知远报告取得泽州')],when='947年五月丁酉（报告日）',place='泽州；刘知远行营',note='丁酉明确为奏报日，攻城、议撤与劝降实际发生日未分别明示。')
sup('shi_reports_zezhou_surrender',9,j,'丁酉，史宏肇奏，澤州刺史翟令奇以郡來降。','《旧五代史》同记丁酉史弘肇报告翟令奇以泽州归降。','两书奏报日相同，宏肇沿用史弘肇主体。')
add('zezhou_siege_recall_debate','刘知远因兵少拟召回史弘肇，苏逢吉、杨邠主张继续进军',9,'始，弘肇攻泽州，','使人谕指于弘肇。',[('史弘肇','率兵攻泽州，收到刘知远的撤回意向'),('翟令奇','坚守泽州'),('帝','因史弘肇兵少考虑召回，派人传达意向'),('苏逢吉','担心撤兵动摇河南归附，反对召回'),('杨邠','反对召回史弘肇')],when='947年五月丁酉奏报以前，具体日未载',place='泽州；刘知远行营',note='欲召还与未决说明尚未实际撤兵；敌将将逃及人心动摇是臣下判断。')
add('shi_advances_liu_accepts','史弘肇坚持继续进军，刘知远采纳意见',9,'弘肇曰：','帝乃从之。',[('史弘肇','认为军势已成，提出继续进军'),('帝','接受继续进军意见')],when='947年五月丁酉奏报以前，具体日未载',place='泽州；刘知远行营')
add('li_wanchao_persuades_zhai','李万超劝翟令奇投降，翟令奇接受',9,'弘肇遣部将','令奇乃降。',[('史弘肇','派李万超劝降'),('李万超','劝说翟令奇归降'),('翟令奇','接受劝说，交出泽州')],when='947年五月丁酉奏报以前，具体日未载',place='泽州')
sup('li_wanchao_persuades_zhai',9,song,'令奇乃開門迎納。弘肇即留萬超權州事','《宋史》记翟令奇开门迎纳，史弘肇留下李万超暂管州事。','使用直接导出的《宋史》正文，不将《旧五代史》夹注转引另算独立书证。')
add('li_wanchao_zezhou_acting','史弘肇令李万超暂管泽州事务',9,'弘肇以万超',None,[('史弘肇','安排李万超暂管泽州'),('李万超','暂管泽州事务')],when='947年五月泽州归降后，具体日未载',place='泽州',note='权知是暂管，不将随后正式任刺史的补书记载强定同日。')
add('zhang_yu_dies_heyang','张遇援救河阳，在南阪战败身亡',10,'崔廷勋、','败死。',[('崔廷勋','与耿崇美、拽剌合兵逼河阳'),('耿崇美','合兵逼河阳'),('拽剌','合兵逼河阳'),('张遇','率数千人援河阳，在南阪战败身亡')],when=t,place='河阳南阪',note='数千为约数；拽剌复用已识别的西奚王主体，身份待考事项保留。')
add('wu_xingde_defeated_closes_city','武行德出战失利，闭城守河阳',10,'武行德出战，','闭城自守。',[('武行德','出战失败后闭城自守')],when=t,place='河阳',note='区别此前乘虚取得河阳的行动，不把占城与反攻失利合成一次战果。')
add('cui_stops_assault_withdraws_huaizhou','崔廷勋劝止攻城，得知泽州失守后撤回怀州',10,'拽剌欲攻之，','还保怀州。',[('拽剌','提出攻河阳城'),('崔廷勋','认为北军已去，劝止攻城；闻泽州失守后退守怀州')],when=t,place='河阳至怀州',note='杀一夫可惜为崔廷勋发言，不据此推军队没有造成平民伤亡。')
add('cui_flees_loots_weizhou','崔廷勋等北逃，经过卫州时大肆劫掠',10,'弘肇将至，','大掠而去。',[('史弘肇','率兵将至怀州'),('崔廷勋','率众北逃，过卫州劫掠')],when=t,place='怀州至卫州',note='等未逐一列名，不补未明示的各人具体劫掠行为。')
add('shi_joins_wu_heyang','河南契丹军陆续北撤，史弘肇与武行德会合',10,'契丹在河南者','与武行德合。',[('史弘肇','引兵与武行德会合'),('武行德','与史弘肇会合')],when=t,place='河南、河阳')
add('shi_strict_discipline_evaluation','《资治通鉴》记史弘肇严行军法，并评价其南下军功',10,'弘肇为人，',None,[('史弘肇','以严酷军法约束将士，获史家军功评价'),('帝','史书记其因军功倚重史弘肇')],when='947年南下期间及其后总结，具体军法执行日未载',place='南下沿途',note='军法杀人是叙述事实；所向必克与皆其力是史家评价。刘知远入洛汴为总结性预述，不认定本段时已抵达两城。',description='《资治通鉴》记史弘肇对违令将校及侵扰民田、系马于树的士卒处以严酷惩罚，并将刘知远后来顺利进入洛阳、大梁归功于他。该结论是史家评价；入城的具体经过继续按后文录入。')
add('liu_arrives_huoyi','刘知远到霍邑，派使者告知赵匡赞其父被契丹拘押',11,'辛丑，',None,[('帝','到达霍邑，派使者向赵匡赞传话'),('赵匡赞','刘知远派使向他通报父亲被拘押的消息')],when='947年五月辛丑',place='霍邑；河中（通知目的地）',note='赵延寿被拘押已在前段录入，此处为传达消息，不重复建拘押事件。')
add('xiao_seizes_palace_women','萧翰强行夺走滋德宫五十多名宫人',12,'滋德宫有','夺宫人，',[('萧翰','破锁强夺宫人'),('张环（晋宦官）','拒绝交出滋德宫宫人')],when=t,place='滋德宫',note='五十多为原文约数；张环与渝州刺史同名，但职务及情境不同，分别建档。')
add('xiao_kills_eunuch_zhang','萧翰拘押宦官张环，用刑将他杀害',12,'执环，',None,[('萧翰','拘押并用刑杀害张环'),('张环（晋宦官）','被拘押并遭用刑杀害')],when=t,place='滋德宫')
add('xiao_forces_congyi_to_bian','萧翰假称契丹命令，派高谟翰迫使李从益与王淑妃到大梁',13,'初，翰闻','不得已而出。',[('萧翰','拟北归，假称契丹主命，派人迎李从益'),('高谟翰','奉派到洛阳迎李从益与王淑妃'),('从益','与王淑妃躲避迎接，后被迫离开'),('淑妃','与李从益躲在徽陵下宫，后被迫离开')],when='947年五月刘知远南下后，具体迎接日主书未载',place='洛阳徽陵下宫至大梁',note='恐乱阻归为史书记萧翰考虑；矫称表明该命令不可作为真实契丹诏令。王淑妃为养母，不能以母子一词推生母。')
sup('xiao_forces_congyi_to_bian',13,li,'乃詐稱契丹主命，遣人迎從益於洛陽，令知南朝軍國事。從益與王妃逃於徽陵以避之，使者至，不得已而赴焉。','《旧五代史》也记萧翰假称契丹命令，李从益与王淑妃躲避后被迫赴汴。','同一行动分别引用，养母身份依本传开篇，不补生母姓名。')
sup('xiao_forces_congyi_to_bian',13,j,'是日，契丹所署汴州節度使蕭翰迎郇國公李從益至東京，請從益知南朝軍國事。','《旧五代史》本纪将迎李从益至东京置于五月丁酉条下。','本纪补具体日期，主书初字叙述未明示当日；不强定全部任官都在丁酉。',relation='adds',field='time_original')
relationship('淑妃','从益','养母',13,'宮嬪所生。明宗命王淑妃母之','传主生母为未具名宫嫔，李嗣源令王淑妃作其母；复用已发布的养母关系，不建重复关系或生母关系。',source=li)
add('xiao_enthrones_congyi','萧翰在大梁拥立李从益，并率诸酋长向他行礼',13,'至大梁，','拜之，',[('萧翰','拥立李从益，率酋长行礼'),('从益','被萧翰拥立')],when=t,place='大梁')
add('congyi_court_appointments','王松、赵远等获任李从益政权官职',13,'以礼部尚书','充在京巡检。',[('王松','由礼部尚书获任宰相'),('赵远','由御史中丞获任宰相'),('翟光鄴','由前宣徽使获任枢密使'),('王景崇','由左金吾大将军获任宣徽使'),('刘祚','暂任侍卫亲军都指挥使，兼在京巡检')],when=t,place='大梁',note='主书接萧翰拥立叙任官，不自动认定李从益主动任命。《旧五代史》王鬆沿王松主体，赵上交沿赵远别名。')
sup('congyi_court_appointments',13,li,'乃偽署王鬆為左丞相，趙上交為右丞相。李式、翟光鄴為樞密使，王景崇為宣徽使','《旧五代史》记王松为左丞相、赵上交为右丞相，并在枢密使名单中另列李式。','官职名单并列保留；此补证不把未在本段主书出现的李式另立一次独立任官。',relation='adds')
claim('person','person_王松','description','《资治通鉴》记王松的父亲名徽，父亲主体身份暂待补证。',13,'松，徽之子也。','原文明示父名徽，但尚未获得能排除同名的补证，不直接与已有王徽主体建立父子关系。')
add('wang_feels_enthronement_peril','王淑妃向百官哭诉，认为拥立使母子陷入危险',13,'百官谒见','是祸吾家也！”',[('淑妃','向百官说明母子势弱，担忧被拥立的后果')],when=t,place='大梁',note='祸家是王淑妃当时的忧虑，此处不提前录入后文母子死亡。')
add('xiao_leaves_yan_guards','萧翰留下千名燕兵守城门，保卫李从益',13,'翰留燕兵','为从益宿卫。',[('萧翰','留下燕兵守门及宿卫'),('从益','由留驻燕兵宿卫')],when=t,place='大梁诸城门')
add('xiao_liu_xi_depart_bian','萧翰与刘晞离汴，李从益到北郊饯行',13,'壬寅，','从益饯于北郊。',[('萧翰','辞行北归'),('刘晞','与萧翰辞行'),('从益','到北郊饯行')],when='947年五月壬寅；《旧五代史》本纪记萧翰己亥离东京',place='大梁北郊',note='两书记萧翰离汴日不同，并列保留，不自行换算公历或抹平差异。')
sup('xiao_liu_xi_depart_bian',13,j,'己亥，蕭翰發離東京北去。','《旧五代史》本纪记五月己亥萧翰离东京北归。','与《资治通鉴》壬寅辞行存在纪日差异；本纪此句未提刘晞，不据此独立验证刘晞同日同行。',relation='conflicts',field='time_original')
add('congyi_summons_generals_no_arrival','李从益派人召高行周与武行德，两人均未到来',13,'遣使召','皆不至。',[('从益','派人召高行周、武行德'),('高行周','在宋州，未赴召'),('武行德','在河阳，未赴召')],when='947年五月萧翰辞行后，具体日未载',place='大梁、宋州、河阳',note='主书只说不至，不臆测未赴召动机；补书记委军事亦不能据此建立长期敌对关系。')
sup('congyi_summons_generals_no_arrival',13,liu,'李從益在汴州，召高行周、武行德將委以軍事，皆不受命。','《旧五代史》刘审交传记李从益欲委两将军事，两人皆未接受。','补书说明拟委军事，但不补两人拒命原因。',relation='adds')
add('wang_calls_welcome_liu','王淑妃建议百官迎接刘知远，反对据城争天下',13,'淑妃惧，','众犹欲拒守，',[('淑妃','说明被萧翰逼迫，建议迎接新主，反对闭城争天下')],when='947年五月召两将不至后，具体日未载',place='大梁',note='诸营五千、守一月可获北救是匿名臣下提议及预测，不记为已经围城一月或北军已经来援。',description='王淑妃说明母子是被萧翰逼迫而来，劝百官迎接刘知远、自求安定。有人提出集结城内军队等待北方援军，她反对为母子争天下而使全城遭祸。')
add('liu_shenjiao_opposes_siege','刘审交认为汴州民力已竭，主张听从王淑妃',13,'三司使文安','一从太妃处分。”',[('刘审交','以汴州经乱、民力枯竭为由反对闭城拒守'),('淑妃','其迎接刘知远的主张获刘审交支持')],when=t,place='大梁',note='无噍类是刘审交对再受围困后果的警告，不写成城中人口实际全部死亡。')
sup('liu_shenjiao_opposes_siege',13,liu,'此城經敵軍破除之後，民力空匱，餘眾幸存','《旧五代史》刘审交传也记他以城市受乱、民力空匮为由反对拒守。','与主书同一论议，不将两书记述累计为两次事件。')
claim('person','person_刘审交','description','刘审交字求益，籍贯为幽州文安。',13,'劉審交，字求益，幽州文安人也。','传主姓名与三司使、汴州议守情节吻合，录入字与籍贯，不将传内全部生平移到947年。',source=liu)
add('congyi_submits_to_liu','李从益改称梁王，向刘知远称臣迎接，并搬出宫中',13,'乃用赵远、',None,[('从益','改称梁王、知军国事，派使称臣迎刘知远，搬到私第'),('赵远','提出改称梁王、奉表迎接的方案'),('翟光鄴','提出改称梁王、奉表迎接的方案')],when=t,place='大梁',note='方案被实际采用；出居私第不写成此时被杀，死亡继续依后文录入。')
add('liu_arrives_jinzhou','刘知远到达晋州',14,'甲辰，',None,[('帝','到达晋州')],when='947年五月甲辰',place='晋州')
add('ruan_succession_anxiety','《资治通鉴》解释耶律阮对自行继位心有不安',15,'契丹主兀欲',None,[('兀欲','史书记其因自行继位而不安')],when=t,place='契丹朝廷',note='不安为史家解释；德光有子未具名，不据本句替未名人物建档；无太后命与此前宣诏声称获太后许可分别保留。',description='《资治通鉴》认为，耶律德光尚有儿子在契丹境内，耶律阮以侄辈身份继位，又未得到述律太后的命令，因此心有不安。此处是史家对其处境与心态的解释。')
# Reuse earlier historical actions without changing archived dates or descriptions.
for code,key,title,start,end,actors in [
 ('abaoji_death_recalled','event_zztj_275_0926_abaoji_dies_fuyu','耶律阿保机去世的追叙','初，契丹主阿保机','卒于勃海，',[]),
 ('shulu_executions_recalled','event_zztj_275_0926_shulu_executes_unruly_chiefs','述律平杀酋长诸将的追叙','述律太后杀','凡数百人。',[])]:
 E[code]=event(code,title,16,span(16,start,end),actors,stable_key=key,when='追叙耶律阿保机去世时的旧事；原事件发生年沿既有记录',note='复用已录入的旧事主体与日期，此处增加卷287追叙出处；数百为本段总述，不把新摘录强定947年。')
add('chiefs_support_ruan_return','契丹酋长诸将因担忧被杀，谋奉耶律阮率军北归',16,'契丹主德光复卒','勒兵北归。',[('兀欲','被酋长诸将谋奉为北归领军者')],when=t,place='恒州',note='惧死为史家动机说明；不虚构匿名酋长姓名。')
add('ruan_assigns_mada_gao','耶律阮任麻答为中京留守、高奉明为安国节度使',16,'契丹主以安国','为安国节度使。',[('兀欲','任命留守及节度使'),('麻荅','由安国节度使任中京留守'),('高奉明','由前武州刺史任安国节度使')],when='947年五月乙巳北归之前，具体任命日未载',place='恒州、中京留守府、安国军',note='原文中京沿恒州占领时期的称谓，不套用辽后期中京地理坐标。')
add('ruan_leaves_jin_officials','耶律阮留晋朝官军在恒州，带部分学士与宫廷人员北归',16,'晋文武官', '自随。',[('兀欲','留晋朝官军，带指定人员随行'),('徐台符','以翰林学士身份被带北归'),('李澣','以翰林学士身份被带北归')],when='947年五月乙巳北归之际',place='恒州',note='先总述留官军、后列随行例外，不解释为全部晋人无一随行；宫人、宦官、教坊人员未名，不另造姓名。')
add('ruan_departs_zhending','耶律阮从真定启程北归',16,'乙巳，',None,[('兀欲','从真定率军北归')],when='947年五月乙巳',place='真定')
sup('ruan_departs_zhending',16,j,'乙巳，契丹永康王烏裕自鎮州還蕃','《旧五代史》同记乙巳耶律阮从镇州北归。','烏裕沿既有耶律阮；真定与镇州按两书原称分别保留。')
reviews={9:'奏报日与攻城、撤回建议、劝降和暂管州事分别整理；直接《宋史》补证，不以夹注转引冒充独立原文。',10:'张遇战败死亡、武行德失利、劝止攻城、北逃劫掠与会合依序录入；军法事实与史家评价分清，入洛汴总结不提前定日。',11:'辛丑到霍邑及通报赵延寿被拘押，复用前段拘押主体，不重复事件。',12:'宦官张环与渝州刺史分别建档，仅用限定别名；强夺宫人与用刑杀人分录，人数保留约数。',13:'迫迎、拥立、任官、守门、离汴、召将、议守与称臣依序录入；王淑妃不推生母；王松父名徽主体待核；萧翰壬寅与己亥异说保留；拒守提议与实际投表分清。',14:'甲辰到晋州，区别前卷任命晋州官职。',15:'自行继位不安为史家解释；未名皇子不猜主体；太后授权异说保留。',16:'阿保机去世及述律平杀将为旧事，复用既有事件；北归动机、任官、人员留随与乙巳启程分录。'}
assert not (P/'publication.json').exists()
for n in range(9,17):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原14—21行连续八段，本卷累计16/75；947年跨卷尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],source_issues_review='保留萧翰离汴纪日差异、王松父亲身份待考；旧事日期沿既有事件；养母与同名宦官明确区分，未消除其他异文。',plain_language_review='首次逐项核对人物、事件、参与角色、时间地点、出处与事实说明；说明计划、预测、指控、史家评价和实际行动，展示字段用白话，逐字引用保持底本。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
