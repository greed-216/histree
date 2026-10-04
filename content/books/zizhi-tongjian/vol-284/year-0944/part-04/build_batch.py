# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 paragraphs 25–32."""
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
COMMIT='cfe7117a41b196f8984cd77f8ab5e4ebfe68ddf8'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-284-944-may-august','jiuwudaishi-082-944-june','xinwudaishi-009-944-january']:
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
main_sources = ['tongjian-284-944-may-august','tongjian-284-944-august-november']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0944-p025-p032',
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
for n in range(25, 33):
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
        month = '六月条下及追述' if n<=28 else '七月条下' if n<=30 else '八月条下及追述'
        citation = f'卷284·后晋天福九年、后称开运元年（944；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0944_04_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
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

ALIASES.update({'帝':'石重贵','高祖':'石敬瑭','汉主':'刘弘熙','唐主':'李璟','硃文进':'朱文进','杜威':'杜重威','杨光远':'杨檀','李浣':'李澣','折从阮':'折从远','岳':'刘岳'})
NEW_ALIASES={'折从远':['折從遠','折从阮','折從阮'],'折嗣伦':['折嗣倫'],'李慎仪':['李慎儀'],'刘温叟':['劉溫叟'],'徐台符':['徐臺符'],'范质':['范質','範質'],'田武':[]}
NEW_DESCRIPTIONS={
'折从远':'云州人，府州刺史。后晋割让北地后，府州归属契丹。他据险抵制契丹迁民，后奉石重贵命令攻入契丹境内、拔十余寨，944年六月戊午任府州团练使。《新五代史》明确其后因避汉高祖名改称折从阮，字可久。生卒年本次引文未载。',
'折嗣伦':'折从远之父，《新五代史》折从阮传记为麟州刺史。任官具体年月和生卒年未载。',
'李慎仪':'后晋右散骑常侍。944年六月戊辰任兵部侍郎、翰林学士承旨。生卒年本段未载。',
'刘温叟':'后晋都官郎中，944年六月戊辰任翰林学士。刘岳之子，《宋史》刘温叟传记其字永龄、河南洛阳人。生卒年本次引文未载。',
'徐台符':'武强人，后晋金部郎中、知制诰。944年六月戊辰任翰林学士。生卒年本段未载。',
'范质':'宗城人，后晋主客员外郎。944年六月戊辰任翰林学士。后续仕宦随编年主线补录。生卒年本次引文未载。',
'田武':'后晋前金州节度使。944年八月在北面行营任步军左厢排阵使，参与对契丹的军职部署。生卒年本段未载。'}
jun='jiuwudaishi-082-944-june';jul='jiuwudaishi-083-944-july';aug='jiuwudaishi-083-944-august';ann='xinwudaishi-009-944-january';sang='xinwudaishi-029-sang-restoration';zhe='xinwudaishi-050-zhe-congruan';feng='jiuwudaishi-125-feng-hui-reply';yang='songshi-269-yang-flood-advice';wen='songshi-262-liu-wensou-family'

# 25: the recommendation, separate institutional and personnel actions, and reported result.
add('recommend_sang_for_crisis','有人向石重贵建议，用桑维翰应对契丹与国内危局',25,'或谓帝曰：','不可。”',[('帝','听取任用桑维翰的建议'),('桑维翰','被不具名者推荐主持应对危局')],when='944年六月恢复枢密院之前，具体日未载',place='后晋朝廷',note='推荐者没有姓名，主书不猜其身份；新史称桑维翰暗中派人游说，作为独立原因说明保留。')
sup('recommend_sang_for_crisis',25,sang,'乃陰使人說帝曰：「制契丹而安天下，非用維翰不可。」','《新五代史》称桑维翰暗中派人向皇帝说，安定天下、应对契丹必须用桑维翰。','本传补游说由桑维翰安排，主书只写有人；不能反推出具体说客姓名。',relation='adds')
add('restore_privy_council','后晋恢复枢密院',25,'丙午，','复置枢密院，',[('帝','下令恢复枢密院')],when='944年六月丙午',place='后晋朝廷')
sup('restore_privy_council',25,jun,'丙午，詔復置樞密院。','《旧五代史》同样记六月丙午诏令恢复枢密院。','恢复机构的纪日与桑维翰任命纪日分别看，不能一律合成同一天。')
add('sang_chief_minister_privy','桑维翰任中书令兼枢密使，受托处理大小政务',25,'以维翰','悉以委之。',[('帝','任桑维翰为中书令兼枢密使，委托大小政务'),('桑维翰','任中书令兼枢密使，受托处理大小政务')],when='944年六月，《资治通鉴》丙午条下；旧史任命记丁未',place='后晋朝廷',note='恢复机构与任职日期有书间差别，独立引用，不静默对齐。')
sup('sang_chief_minister_privy',25,jun,'丁未，以侍中桑維翰為中書令，充樞密使。','《旧五代史》将桑维翰由侍中任中书令、枢密使记在六月丁未。','任命比丙午恢复机构晚一天，保留此书明确纪日。',relation='conflicts',field='time_original')
sup('sang_chief_minister_privy',25,sang,'拜維翰中書令，復為樞密使，封魏國公，事無巨細，一以委之。','《新五代史》也记任桑维翰为中书令、枢密使，补封魏国公。','封号按本传记载，不由受托政务推定他拥有皇帝全部权力。',relation='adds')
add('court_improves_after_sang','史书记桑维翰主持政务后，数月间朝廷治理有所改善',25,'数月之间，',None,[('桑维翰','主持政务后，被史书评价为改善朝廷治理')],when='944年六月任职之后数月，具体结束日未载',place='后晋朝廷',note='差治是治理渐有起色，不写成已消除全部危机；数月不自动换算成确定月份。')
sup('court_improves_after_sang',25,sang,'數月之間，百度寖理。','《新五代史》也记桑维翰任职后数月，各项政务渐有条理。','两书近似表述可能承袭，不作为完全独立的效果测量。')

# 26: flood, labor mobilization, completed closure, proposal and successful remonstrance.
add('huazhou_yellow_river_breach','黄河在滑州决口，淹及五州并绕梁山汇入汶水',26,'滑州河决，','合于汶。',[],when='944年六月，主书未列日；旧史记丙辰',place='滑州、汴州、曹州、单州、濮州、郓州、梁山、汶水',note='保留原文地名与范围，坐标未核；原文没有损失总额和死亡人数。')
sup('huazhou_yellow_river_breach',26,jun,'丙辰，滑州河決，漂註曹、單、濮、鄆等州之境，環梁山合於汶、濟。','《旧五代史》记六月丙辰滑州河决，水流绕梁山合入汶、济。','补丙辰纪日，汶济与主书只称汶的水系表述分别保存；漂註原字不改。',relation='adds',field='time_original')
add('flood_closure_labor_order','后晋征发多道民夫堵塞黄河决口',26,'诏大发','丁夫塞之。',[('帝','下诏征发多道民夫堵河')],when='944年六月决口之后，征发具体日未载',place='多道至滑州河口',note='丁夫为成年民夫，不补人数、各道名单或自愿参与结论。')
sup('flood_closure_labor_order',26,yang,'時河決數郡，大發丁夫，以本部帥董其役，既而塞之。','《宋史》记征发民夫，由当地军政长官督办堵河。','本传补工程督办方式，长官没有姓名，不为事件强配某个节度使。',relation='adds')
add('flood_breach_closed','后晋堵塞了黄河决口',26,'既塞，','既塞，',[],when='944年上述堵河之后，具体完成日未载',place='黄河决口处',note='既塞明确工程堵口完成，不只是命令；原文不保证所有受灾地区已恢复生活。')
add('emperor_plans_flood_monument','石重贵准备立碑记录堵河之事',26,'帝欲','纪其事。',[('帝','准备立碑记录堵河成果')],when='944年堵口完成之后',place='后晋朝廷',note='欲刻是计划，不登记碑已建成或存世位置。')
add('yang_advises_against_flood_boast','杨昭俭劝石重贵发布反省诏书，停止刻碑颂功',26,'中书舍人杨昭俭','罪己之文。”',[('杨昭俭','劝皇帝不要刻碑颂功，应发布反省诏书'),('帝','受到杨昭俭关于堵河刻碑的劝谏')],when='944年石重贵拟刻碑之后',place='后晋朝廷',note='劝降哀痛罪己诏不等于这些诏书已发布；不因染翰一词另造翰林书写事件。')
sup('yang_advises_against_flood_boast',26,yang,'昭儉表諫曰：「陛下刻石紀功，不若降哀痛之詔；摛翰頌美，不若頒罪己之文。」言甚切至，少主嗟賞之，卒罷其事。','《宋史》杨昭俭传也记同一劝谏，皇帝赞许后停止立碑。','染翰与摛翰按底本分别引用，核心劝谏一致；不把少主误作另一君主。')
add('emperor_cancels_flood_monument','石重贵接受杨昭俭劝谏，停止立碑',26,'帝善其言',None,[('帝','赞同杨昭俭劝谏，停止立碑计划')],when='944年上述劝谏之后',place='后晋朝廷',note='止指取消刻碑，不等于已发布罪己诏；原文没有退还工程款的记载。')

# 27: retrospective transfer and resistance, then current appointment.
add('fuzhou_subject_to_khitan','后晋割让北地后，府州与折从远归属契丹',27,'初，高祖割','亦北属。',[('高祖','割让北边土地给契丹'),('折从远','作为府州刺史随地区归属契丹')],year=None,when='936年后晋割让北地之后的追述；府州具体转属年月未载',place='府州',note='沿用已核936年割地背景，仅新录府州归属后果，不重建另一割让十六州事件。')
add('khitan_plans_hexi_population_move','契丹准备将河西居民迁往辽东，府州人惊恐',27,'契丹欲','州人大恐，',[],year=None,when='府州归属契丹之后、石重贵断绝关系之前的追述，确切年月未载',place='河西、府州、辽东',note='欲尽徙为迁民意图，不登记全部居民已迁抵辽东；河西不自动等同今日甘肃河西走廊。')
add('zhe_resists_population_move','折从远依托险要地形，抵制契丹迁民',27,'从远因','保险拒之。',[('折从远','据险抵制契丹迁民')],year=None,when='上述契丹拟迁民之后的追述，确切年月未载',place='府州',note='保险是保据险要，不是现代保险制度；不补具体山寨名称、兵数和战果。')
add('emperor_orders_zhe_attack','石重贵与契丹决裂后，派人命折从远进攻契丹',27,'及帝与契丹绝，','使攻契丹。',[('帝','派使者命折从远进攻契丹'),('折从远','接到石重贵进攻契丹的命令')],year=None,when='石重贵与契丹决裂之后、944年六月任官之前的追述，确切年月未载',place='后晋至府州',note='决裂发生于942年后，但此出使没有确年，不直接定942；使者未具名。')
add('zhe_takes_ten_khitan_forts','折从远深入契丹境内，攻取十余寨',27,'从远引兵','拔十馀寨。',[('折从远','率兵深入契丹境内，攻取十余寨')],year=None,when='上述奉命出兵之后、944年六月任官之前，确切年月未载',place='契丹境内，寨名与位置未载',note='十余按概数保留，不补精确寨数；深入行动与命令分开，不绘造路线。')
sup('zhe_takes_ten_khitan_forts',27,zhe,'晉出帝與契丹敗盟，從阮以兵攻契丹，取其城堡十餘，遷本州團練使，','《新五代史》也记折从阮在后晋与契丹关系破裂后攻取十余城堡，升本州团练使。','本传明确从阮初名从远，复用同一主体；后续兼朔州与振武官职按对应年月另录。')
add('zhe_fuzhou_training_commissioner','后晋任折从远为府州团练使',27,'戊午，','府州团练使。',[('帝','任折从远为府州团练使'),('折从远','由府州刺史升任本州团练使')],when='944年六月戊午',place='府州')
sup('zhe_fuzhou_training_commissioner',27,jun,'戊午，升府州為團練使額。','《旧五代史》同日记府州升为团练使级别。','本纪只写州级升格，主书明确任官者，分别支持机构与人物，不混作两次升迁。')
claim('person',people['折从远'],'name','《新五代史》明确折从阮初名折从远，后来因避汉高祖名改称从阮，字可久。',27,'折從阮字可久，初名從遠，避漢高祖名，改為阮，雲中人也。','名称对应由本传明载，合并为同一主体；不新建944年改名事件，也不提前改名的年月。',source=zhe,relation='adds')
claim('person',people['折从远'],'description','《资治通鉴》称折从远为云州人。',27,'从远，云州人也。','籍贯按主书，云中是新史原称，保存两书表述。')
relationship('折嗣伦','折从远','父亲',27,'折從阮字可久，初名從遠，避漢高祖名，改為阮，雲中人也。其父嗣倫，為麟州刺史。','父嗣伦承接折从阮，姓氏和关系由上下文明确；折嗣伦是折从远的父亲，任麟州刺史年月未载。',source=zhe)

# 28: institution restored, five appointments and an explicit paternal relation.
add('restore_hanlin_academicians','后晋恢复翰林学士职务',28,'甲子，','复置翰林学士。',[('帝','恢复翰林学士职务')],when='944年六月甲子',place='后晋朝廷')
sup('restore_hanlin_academicians',28,jun,'甲子，復置翰林學士。','《旧五代史》同样记六月甲子恢复翰林学士。','不把恢复职务与戊辰具体任命当成同一天。')
sup('restore_hanlin_academicians',28,sang,'及維翰為樞密使，復奏置學士，而悉用親舊為之。','《新五代史》记桑维翰任枢密使后奏请恢复学士，并任用亲旧。','本传给出奏请者与任人评价，不据其泛称给每位学士新建亲属或朋友关系。',relation='adds')
for code,title,start,end,name,role in [
('li_shenyi_hanlin_chief','李慎仪任兵部侍郎、翰林学士承旨','戊辰，','翰林学士承旨，','李慎仪','由右散骑常侍任兵部侍郎、翰林学士承旨'),
('liu_wensou_hanlin','刘温叟任翰林学士','戊辰，','皆为学士。','刘温叟','以都官郎中身份任翰林学士'),
('xu_taifu_hanlin','徐台符任翰林学士','戊辰，','皆为学士。','徐台符','以金部郎中、知制诰身份任翰林学士'),
('li_huan_hanlin','李澣任翰林学士','戊辰，','皆为学士。','李澣','以礼部郎中身份任翰林学士'),
('fan_zhi_hanlin','范质任翰林学士','戊辰，','皆为学士。','范质','以主客员外郎身份任翰林学士')]:
 add(code,title,28,start,end,[(name,role)],when='944年六月戊辰',place='后晋朝廷',note='戊辰任命与甲子恢复职务区分；籍贯武强属徐台符，宗城属范质，不把所有人都记为两地籍贯。')
sup('liu_wensou_hanlin',28,jun,'以刑部郎中劉溫叟改都官郎中，充翰林學士；','《旧五代史》记刘温叟由刑部郎中改都官郎中、任翰林学士。','补旧职与任职过程，不把温叟岳之子误作另一岳姓人物。',relation='adds')
sup('xu_taifu_hanlin',28,jun,'以金部郎中、知制誥徐臺符為翰林學士；','《旧五代史》同样记徐台符任翰林学士。','臺台繁简同人，底本原字不改。')
sup('li_huan_hanlin',28,jun,'以禮部郎中李浣本官知制誥，充翰林學士；','《旧五代史》用李浣之名，记本官知制诰、任翰林学士。','已录李澣包含李浣别名，复用既有主体；与李瀚等近字姓名不机械合并。',relation='adds')
sup('fan_zhi_hanlin',28,jun,'以主客員外郎範質充翰林學士；','《旧五代史》同样记范质任翰林学士。','范範字形按本书保留，本站同一主体。')
relationship('刘岳','刘温叟','父亲',28,'温叟，岳之子也。','上文温叟为刘温叟，岳为其父刘岳，宋史明确父岳后唐太常卿。方向为刘岳是刘温叟的父亲。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《宋史》明确刘温叟之父岳为后唐太常卿。',28,'父岳，後唐太常卿。','本传开头刘温叟为主语，父岳即刘岳；不根据太常卿另造同名人物。',source=wen,relation='corroborates')
claim('person',people['刘温叟'],'description','《宋史》记刘温叟字永龄、河南洛阳人。',28,'劉溫叟，字永齡，河南洛陽人。','正文传主刘温叟，电子章节题沿用李涛传；引用已按卷262刘温叟传标明，不照抄自动题名。',source=wen,relation='adds')

# 29–30: change of era, relief policy and a cabinet appointment.
add('kaiyun_general_amnesty','后晋在七月辛未朔实行大赦',29,'秋，七月，辛未朔，','大赦，',[('帝','颁布全国大赦')],when='944年七月辛未朔',place='后晋')
add('change_to_kaiyun_era','后晋将天福九年改为开运元年',29,'秋，七月，辛未朔，',None,[('帝','将天福九年改为开运元年')],when='944年七月辛未朔',place='后晋',description='石重贵在七月辛未朔改元，将944年的天福九年改称开运元年。年号改变不代表进入另一个公元年。')
sup('change_to_kaiyun_era',29,jul,'開運元年秋七月辛未朔，帝御崇元殿，大赦天下，改天福九年為開運元年。','《旧五代史》明确皇帝在崇元殿宣布大赦，将天福九年改为开运元年。','补新旧年号对应和仪式地点；同年上半年的原纪年保留，不改原文。',relation='adds')
extra('war_regions_autumn_tax_relief','后晋免除河北遭契丹侵扰地区当年秋税',29,jul,'河北諸州，曾經契丹蹂踐處，與免今年秋稅。',[('帝','免除河北受契丹侵扰地区当年秋税')],when='944年七月辛未朔赦令条下',place='河北受契丹侵扰的地区',note='范围仅受侵扰处，不扩大为全国所有税种；免税令与实际各户执行情况分开。')
extra('soldiers_graded_grants','后晋宣布按等级给军中将士优待',29,jul,'諸軍將士等第各賜優給。',[('帝','宣布按等级给各军将士优待')],when='944年七月辛未朔赦令条下',place='后晋诸军',note='没有具体钱粮数量，不补每人待遇。')
extra('stop_exaction_and_reward_contributors','后晋令停止征借钱帛，并优待已出钱者',29,jul,'諸州率借錢帛，赦書到日，畫時罷征，出一千貫已上者與免科徭，一萬貫已上者與授本州上佐雲。',[('帝','令各州收到赦书即停征，按已出钱数免徭或授州上佐')],when='944年七月辛未朔赦令，各州收到赦书时执行',place='后晋各州',note='一千贯以上免科徭、一万贯以上授州上佐，依两级条件保存；没有具名受益者，不虚构个人任命。')
extra('capital_thunderstorm_during_amnesty','京城宣布赦令时遭雷雨，史书记数百人被雷击死',29,jul,'是日宣赦未畢，會大雷雨，匆遽而罷。時都下震死者數百人，明德門內震落石龍之首，識者以為石乃國姓，蓋不祥之甚也。',[],when='944年七月辛未朔',place='京城、明德门',note='保留数百人概数和石龙损毁；石姓不祥是史书记录的解读，不写成本站对亡国的因果证明。')
add('liu_xu_returns_chancellorship','刘昫任司空兼门下侍郎、同平章事',30,'己丑，',None,[('刘昫','由太子太傅任司空兼门下侍郎、同平章事')],when='944年七月己丑',place='后晋朝廷')
sup('liu_xu_returns_chancellorship',30,jul,'太子太傅、譙國公劉句為守司空兼門下侍郎平章事、監修國史、判三司，','《旧五代史》作刘句，记相同任职并补监修国史、判三司。','该句同一己丑官职与主书刘昫对应，刘句字形待核，不另建人物，也不把句静默改为昫。',relation='adds')

# 31: command structure, memorial and reply, assessments, restricted authority and advice.
add('liu_zhi_yuan_northern_commander','后晋任刘知远为北面行营都统',31,'八月，辛丑朔，','为北面行营都统，',[('帝','任刘知远为北面行营都统'),('刘知远','以河东节度使身份受任北面行营都统')],when='944年八月辛丑朔',place='后晋北面行营')
add('du_northern_campaign_commander','后晋任杜重威为北面行营都招讨使',31,'顺国节度使杜威','以备契丹。',[('帝','任杜重威为都招讨使，部署防备契丹'),('杜威','以顺国节度使身份任都招讨使')],when='944年八月辛丑朔',place='后晋北面行营',note='杜威为已录杜重威同一人。主书督十三节度与旧纪总命十五将口径不同，包含统帅是否计入须区分，不径判兵数矛盾。')
sup('du_northern_campaign_commander',31,ann,'八月辛丑朔，劉知遠為北面行營都統，順德軍節度使杜威為都招討使。','《新五代史》同日记刘知远、杜威两项任命，杜威职衔写顺德军节度使。','顺德与通鉴顺国、旧纪镇州称谓保留异文，不另建军镇或主体。',relation='conflicts')
qaug=(sources[aug]/'source.txt').read_text();qaug=qaug[:qaug.index('壬寅，')]
extra('northern_fifteen_commanders','《旧五代史》记后晋部署十五名将领防御契丹',31,aug,qaug,
 [('帝','命十五名将领参与防备契丹'),('刘知远','任北面行营都统'),('杜威','任北面行营都招讨使'),('张从恩','任马步军都监'),('景延广','任马步军都排阵使'),('赵在礼','任马步军都虞候'),('安叔千','任马步军左厢排阵使'),('安审信','任马军右厢排阵使'),('安审琦','任马步军都指挥使'),('符彦卿','任马军左厢都指挥使'),('皇甫遇','任马步军右厢都指挥使'),('张彦泽','任马军排阵使'),('王廷胤','任马军左厢都指挥使'),('宋彦筠','任步军右厢都指挥使'),('田武','任步军左厢排阵使'),('潘环','任步军右厢排阵使')],
 when='944年八月辛丑',place='后晋北面行营',note='十五为将领部署名单，不是十五万兵。主书督十三节度与总名单口径分开。注文范质独草诏制来自东都事略，仅保留上下文，不作为本批独立正文事实。')
add('sang_commands_regional_governors','史书记桑维翰统一指挥十五位节度使，时人佩服其胆略',31,'桑维翰两秉朝政，','时人服其胆略。',[('桑维翰','统一指挥节度使，被史书称时人佩服其胆略')],when='944年八月部署时及此前两度执政的概述',place='后晋朝廷',note='出杨景是此前政治经历，不重建同一调任；节度使无敢违为史书评价，不凭泛称另建终身主臣关系。')
add('feng_hui_requests_assignment','冯晖上书称尚未年老，希望参与此次军事部署',31,'朔方节度使冯晖','而制书见遗。',[('冯晖','上书自称未老可用，对未被列入部署提出意见')],when='944年八月军事部署之后，具体日未载',place='朔方至后晋朝廷',note='尚未老是冯晖自陈，不能用来倒推出精确年龄或出生年。')
sup('feng_hui_requests_assignment',31,feng,'惟暉不預其數，乃上章自陳，且言未老可用，而制書見遺。','《旧五代史》冯晖传也记未被列入十五将部署后上书自陈未老可用。','朔方冯晖沿用已有主体，与后唐泸州刺史同名人物分开。')
add('sang_drafts_feng_hui_reply','桑维翰令值班学士起草答诏，称朔方重地离不开冯晖',31,'维翰诏禁直学士','受代亦须奇才。”',[('桑维翰','令值班学士起草答诏，说明冯晖留守朔方的理由'),('冯晖','答诏称其威望适合镇守朔方')],when='944年上述冯晖上书之后',place='后晋朝廷、朔方',note='非制书勿忘疑似转录字，原文保留，解释依旧史忽忘；学士未具名，不直接配范质或徐台符。')
sup('sang_drafts_feng_hui_reply',31,feng,'詔報云：「非制書忽忘，實以朔方重地，蕃部窺邊，非卿雄名，何以彈壓！比欲移卿內地，受代亦須奇才。」','《旧五代史》答诏称没有忘记冯晖，是朔方地位重要、需要其威望，替任亦须人才。','忽忘与主书勿忘并列留原字；后文移邠陕等属于另阶段，不在本段提前完成调任。',relation='adds')
add('feng_hui_pleased_reply','冯晖收到答诏后十分高兴',31,'晖得诏，','甚喜。',[('冯晖','收到答诏后十分高兴')],when='944年上述答诏送达后',place='朔方',note='情绪依史书记述，不补回信、献物或调任结果。')
add('sang_decides_many_affairs','史书记桑维翰迅速裁决纷繁政务，事后讨论仍难改易',31,'时军国多事，','亦终不能易也。',[('桑维翰','迅速裁决各方请示，史书称事后讨论也难改其方案')],when='944年桑维翰主持军国政务期间',place='后晋朝廷',note='辐氵奏为电子转录疑字，保留引用，解释只取各方请示纷至及裁决迅速的上下文；不改底本。')
add('criticism_sang_favor_grudges','史书记桑维翰为相重恩怨，也因此受到批评',31,'然为相颇任爱憎，','人亦以此少之。',[('桑维翰','被史书批评为执政时偏重个人恩怨')],when='944年执政表现的概述，具体评价日未载',place='后晋朝廷',note='这是史书评价，不虚构每一件报恩报怨事例或终身关系。')
add('liu_misses_two_rendezvous','契丹进攻时，刘知远两次未按期到山东会兵',31,'契丹之入寇也，','皆后期不至。',[('帝','两次命刘知远到山东会兵'),('刘知远','两次都未按期赶到会兵地点')],when='944年八月前契丹进攻期间的追述，两次具体日未载',place='山东，指太行山以东的战区',note='山东不直接限定为今日山东省；后期不至不推他最终完全没有发兵，也不拆出无日期的第三次违命。')
add('emperor_suspects_liu_ambition','石重贵向亲近者表示，怀疑刘知远另有图谋',31,'帝疑之，','何不速为之！”',[('帝','向亲近者表达对刘知远的怀疑'),('刘知远','因未按期会兵受到皇帝怀疑')],when='944年上述两次会兵延误之后、八月部署前后，具体日未载',place='后晋朝廷',note='异图是皇帝怀疑，不写成已经证实刘知远当时谋反；所亲未具名。')
add('liu_nominal_command_exclusion','刘知远虽任都统，却无实际统制权，未能参与重大密议',31,'至是虽为都统，','皆不得预。',[('刘知远','虽任都统，却没有实际统制权，也未能参与重大秘密议事')],when='944年八月任都统之后',place='后晋北面行营、朝廷',note='临制为实际统制，不能因为头衔便画出其实际指挥所有节度使的关系；秘密议题未载。')
add('liu_cautious_after_exclusion','刘知远知道自己被疏远，小心处事自守',31,'知远亦自知见疏，','但慎事自守而已。',[('刘知远','知道自己被疏远，谨慎处事自守')],when='944年上述受疏远期间',place='河东',note='自知与谨慎依史书记述，不补内心计划或已经建立新朝。')
add('guo_wei_advises_liu','郭威劝刘知远，河东险固且民风尚武，不必忧虑',31,'郭威见知远有忧色，',None,[('郭威','以河东地形、民风与军农条件劝慰刘知远'),('刘知远','听郭威劝慰')],when='944年上述刘知远受疏远期间，具体日未载',place='河东',note='霸王之资是郭威的判断，不写成刘知远此时已经称帝或公开举兵；士多战马原句疑有转录问题，解释不强定马匹数量。')

# 32: claim of authority, submission and an independent dated investiture.
add('zhu_claims_weiwu_regency','朱文进自称威武留后，暂掌闽国事务',32,'硃文进自称','权知闽国事，',[('硃文进','自称威武留后，暂掌闽国事务')],when='944年八月后晋授官前，具体自称日期未载',place='闽国',note='先自称与后晋正式任命分开；不重建三月已录自称闽主的相同登位事件。')
add('zhu_submits_to_jin','朱文进派人上表，向后晋称藩',32,'遣使奉表','称籓于晋。',[('硃文进','派使者向后晋上表称藩')],when='944年八月癸丑授官之前，具体出使日期未载',place='闽国至后晋',note='称藩是表文宣称的政治归属，不把朱与石血缘化，或断言后晋军队实际控制福建。')
add('jin_invests_zhu_min','后晋任朱文进为威武节度使，主管闽国事务',32,'癸丑，',None,[('帝','任朱文进为威武节度使，主管闽国事务'),('硃文进','获后晋任命为威武节度使，知闽国事')],when='944年八月癸丑',place='闽国、福州威武军')
sup('jin_invests_zhu_min',32,aug,'癸丑，以威武軍兵馬留後、權知閩國事朱文進為檢校太傅、福州威武軍節度使，知閩國事。','《旧五代史》同日记朱文进任福州威武军节度使、知闽国事，补检校太傅职衔。','同段八月壬寅才报王延羲遇害，属于传闻到达编年位置，不能据此把已录三月死亡改八月。',relation='adds')

reviews={25:'恢复机构丙午与桑任职旧史丁未分开。推荐与新史所称暗中安排游说并列，数月治理改善为史书评价。',26:'决口、征夫、堵塞完成、拟刻碑、劝谏与取消分别录。旧史丙辰补纪日，汶济与汶称谓并列；不把罪己诏建议写成已发布。',27:'追述与当前任命分开，府州转属依936年已核割地背景，其余追述无确年留null。契丹迁民是计划，抗拒和攻寨为已载行动。新史明载从阮初名从远，只建一人并补父嗣伦关系，后续兼官未提前。',28:'恢复甲子与任命戊辰分开，五人各有参与记录。李浣复用李澣，未与李瀚近字合并；刘岳父刘温叟方向明确。宋史电子题李涛不照抄，核正文卷262刘温叟传。',29:'同年天福九年改开运元年，不能当下一公元年。旧史补局部秋税、停征借令及奖励条件与雷雨，灾异不作天命事实。',30:'刘句与刘昫同日同官的异文保留不造新人，监修国史判三司独立书证。',31:'主书十三节度与旧纪十五将部署口径分别保留；都统头衔与刘知远缺实际权力分开。冯晖留朔方答诏不提前后续调镇，勿忘忽忘、辐氵奏疑字不改。个人评价、皇帝怀疑与郭威判断都有归属。',32:'朱自称、上表称藩、晋正式任命分开；旧史八月报告三月政变，不改先前死亡年月，未造血缘或实际军事控制关系。'}
assert not (P/'publication.json').exists()
for n in range(25,33):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=944,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],next_volume=284,next_year=944,supplements=supplements,excluded_non_body=[],coverage='卷284原30—37行连续第25—32段，六月至八月及追述；下接第33段澶州设置镇宁军，944全年尚未完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[1],'当前只引用第32段威武授官，九月至十一月其余段落尚未处理。'),(zhe,'只补初名、字、父亲和当前攻寨，不提前947年之后各镇任官。'),(feng,'只补八月部署与答诏，不提前后续移邠陕及再次回朔方。'),(sang,'只补本段任命、游说与学士恢复，早年废学士已在940年主线记录，不再次新建。'),(yang,'只补堵河与谏碑，不提前周世宗时期仕宦。'),(wen,'正文传主刘温叟，电子章节李涛传只是沿用题名；只取字、籍贯与父亲。'),(aug,'军职与朱任官用正文；东都事略注文不作独立来源，八月政变报告不用于更改三月死亡。')]],source_issues_review='桑任职丙午丁未、杜顺国顺德、刘昫刘句、勿忘忽忘及辐氵奏等分别保留。身份父亲关系与折改名有明确原文；未知年份追述、军职名义权力与政治怀疑均区分。电子文本纸本异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,33)],plain_language_review='首次逐项核对人物、事件、参与、关系、事实说明和时间解释，主语和动作明确。拟迁民、拟刻碑、任命、报告与史书评价分别处理；原文保持底本字形。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
