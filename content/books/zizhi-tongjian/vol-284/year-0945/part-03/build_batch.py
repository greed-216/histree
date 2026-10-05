# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 year 945 paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,36))
COMMIT='74486f99392b820f87f1b0c58501ef7c8c04d896'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-284-945-february-march','jiuwudaishi-083-945-march','xinwudaishi-009-945','liaoshi-004-945-march']:
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
main_sources = ['tongjian-284-945-february-march','tongjian-284-945-yangcheng-april']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0945-p017-p024',
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    for a,b in [('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        citation = f'卷284·后晋开运二年（945年三月至四月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0945_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=945, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='945年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_284_0945_' + code
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
        edge = 'participation_zztj_284_0945_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_284_0945_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
def extra(code,title,n,source,quote,actors,**kw):
 E[code]=event(code,title,n,quote,actors,source=source,**kw);return E[code]
ALIASES.update({'帝':'石重贵','契丹主':'耶律德光','杜威':'杜重威','闽主':'王延政','曦':'王延羲','硃文进':'朱文进','岩明':'卓岩明','继昌':'王继昌','李彦韬':'李彦韬（后晋宣徽使）'})
NEW_ALIASES={'李仁达':['李仁達'],'陈继珣':['陳繼珣'],'卓岩明':['卓巖明','卓俨明','卓儼明'],'萧处钧':['蕭處鈞'],'晋廷谦':['晉廷謙','晋庭谦','晉庭謙'],'没剌':['沒剌'],'药元福':['藥元福']}
NEW_DESCRIPTIONS={
 '李仁达':'光州人，曾任闽元从指挥使，多次在建州、福州之间投奔不同执政者。945年与陈继珣、黄仁讽发动福州政变，杀王继昌和吴成义，拥立僧卓岩明。后来又杀黄仁讽、陈继珣，将福州兵权集中到自己手中。生卒年本次引文未载。',
 '陈继珣':'浦城人，曾离王延政投奔王延羲，因献攻建州方案任著作郎。945年与李仁达、黄仁讽发动福州政变，后受李仁达任命驻北门，又被李仁达以谋反告发而杀。出生年未载。',
 '卓岩明':'雪峰寺僧，945年三月己亥被李仁达等拥立为帝，仍称天福十年并向后晋称臣。主书写卓岩明，新五代史对应同寺、同场立帝写卓俨明，作为姓名异文保留。生卒年本段未载。',
 '萧处钧':'后晋供奉官。945年三月乙巳诸军会定州时受命暂知祁州事。生卒年本段未载。',
 '晋廷谦':'契丹控制下的泰州刺史。945年三月庚戌向后晋军举州投降。旧五代史同次降城写晋庭谦，对应同州同日事件，保留姓名异文。生卒年本段未载。',
 '没剌':'945年后晋攻取满城时被俘的契丹首领。主书称酋长，旧本纪称相公。生卒年与是否还存在其他姓名写法本段未载，不因音近合并其他契丹首领。',
 '药元福':'并州晋阳人，早年侍奉王檀及后唐，曾任深州刺史。945年任后晋马军右厢副排阵使，在白团卫村被围时主张逆风急击，与符彦卿、张彦泽、皇甫遇领骑兵出战。《宋史》还记他战后任威州刺史。生卒年本次引文未载。'}
NEW_DEATH_YEARS={'陈继珣':945}
old='jiuwudaishi-083-945-march';oc='jiuwudaishi-083-945-march-continuation';apr='jiuwudaishi-083-945-april';ny='xinwudaishi-009-945';liao='liaoshi-004-945-march';zm='xinwudaishi-052-zhang-yangcheng';minbook='xinwudaishi-068-li-ren-da';yo='songshi-254-yao-origins';yb='songshi-254-yao-yangcheng';fb='songshi-251-fu-yangcheng'
# 17: earlier defections, a coup and the enthronement of a monk.
add('li_renda_early_min_service','李仁达在闽任元从指挥使，十五年未升职',17,'初，','不迁职。',[('李仁达','在闽任元从指挥使，十五年未升职')],when='追述早年，起止年月未载',year=None,place='闽国',note='光州籍贯据同句；十五年不倒推任官开始年，不能写945年才任此职。')
add('li_renda_defects_jianzhou','李仁达在王延羲执政时离闽投建州，被王延政任为将领',17,'闽主曦之世，','为将。',[('李仁达','离开王延羲投奔建州，被王延政任为将领'),('闽主','接纳李仁达，任他为将领')],when='王延羲执政时期的追述，具体年月未载',year=None,place='福州至建州',note='曦识别王延羲，不与前任王继鹏混淆；叛奔以政治投奔行为记录。')
add('li_renda_offers_zhu_jianzhou_plan','朱文进杀王延羲后，李仁达又投福州，献攻建州方案',17,'及硃文进弑曦，','之策。',[('李仁达','在朱文进夺权后投福州，献攻建州方案'),('硃文进','得到李仁达攻建州方案')],when='944年朱文进杀王延羲之后，具体月日未载',year=944,place='建州至福州',note='杀王延羲已在944年录入，不另建重复死事；李献策只是方案，未证明其率兵已攻克建州。')
add('zhu_banishes_li_fuqing','朱文进因不信任李仁达的反复，将他贬居福清',17,'文进恶','福清。',[('硃文进','因李仁达反复投奔而将其贬居福清'),('李仁达','被朱文进贬居福清')],when='944年献攻建州方案后、朱文进被杀前，具体日未载',year=944,place='福清')
add('chen_jixun_defects_and_appointed','陈继珣离王延政投福州，为王延羲献策并任著作郎',17,'［先是］','著作郎。',[('陈继珣','从王延政处投福州，为王延羲献攻建州方案并任著作郎'),('曦','接纳陈继珣的攻建州方案，任他为著作郎')],when='追述王延羲执政时期，具体年月未载',year=None,place='建州至福州',note='陈继珣籍贯浦城，原文先是标记保留；不把攻建州方案写成实际城已陷。')
add('li_chen_feel_insecure_yanzheng_rule','王延政得福州后，李仁达、陈继珣都感到不安',17,'及延政得福州，','不自安。',[('李仁达','因曾背离王延政，在其取得福州后不安'),('陈继珣','因曾背离王延政，在其取得福州后不安')],when='945年福州归王延政之后、政变前',place='福州',note='不安为史书记述的情绪，未补已经接到处死诏书。')
add('wang_jichang_alienates_soldiers','王继昌嗜酒、不关心将士，将士对他多有怨恨',17,'王继昌暗弱','多怨。',[('继昌','因嗜酒、不关心将士而受到怨恨')],when='945年任守福州后、政变前',place='福州',note='暗弱为史书评价，不补医疗或智力诊断；没有具名怨恨者，不虚构名单。')
add('li_chen_persuade_huang_coup','李仁达潜入福州，与陈继珣说服黄仁讽发动夺权',17,'仁达潜入福州，','仁讽然之。',[('李仁达','潜入福州，与陈继珣劝黄仁讽趁建州危急夺权'),('陈继珣','与李仁达说服黄仁讽夺权'),('黄仁讽','接受李仁达、陈继珣的夺权建议')],when='945年三月福州政变前，具体日未载',place='福州',note='援引王潮兄弟起家为说辞，不重建过去王潮取闽事件；富沙不能保城为劝说判断，不当建州此时已陷。')
add('li_faction_kills_jichang','李仁达等当晚率甲士闯入府署，杀王继昌',17,'是夕，','杀继昌及吴成义。',[('李仁达','与同谋率甲士突入府署，杀王继昌'),('陈继珣','参与当晚突入府署夺权'),('黄仁讽','加入夺权行动，王继昌被杀'),('继昌','在福州政变中被杀')],when='945年三月，劝黄仁讽的当晚；己亥立帝之前',place='福州府署',note='等承接李、陈、黄同谋，但亲自行刑者没有逐名分派，不写每人都亲手斩同一人。')
sup('li_faction_kills_jichang',17,minbook,'福州將李仁達謂其徒曰：「唐兵攻建州，富沙王不能自保，其能有此土也？」乃擒繼昌殺之。','《新五代史》也记李仁达以建州危急为说辞，擒杀王继昌。','此书明确李仁达，但未列全部同谋，不因省略推其他人没有参与。')
add('li_faction_kills_wu_chengyi','李仁达等闯入府署时也杀死吴成义',17,'是夕，','杀继昌及吴成义。',[('李仁达','与同谋率甲士突入府署，杀吴成义'),('吴成义','在福州政变中被杀')],when='945年三月劝黄仁讽的当晚，己亥立帝之前',place='福州府署')
add('li_renda_uses_monk_claim','李仁达怕人心不服，借卓岩明特殊相貌宣称他是真天子',17,'仁达欲自立，','相与迎之。',[('李仁达','因怕人心不服，宣称僧卓岩明有天子相并迎接他'),('岩明','因受众人尊重，被李仁达等用来争取拥护')],when='945年三月王继昌、吴成义被杀后',place='福州、雪峰寺',note='重瞳、垂手及真天子为李仁达的说辞和史书记述，不作神异确证；李仁达欲自立不是此时已经称帝。')
add('zhuo_yanming_enthroned','李仁达等于己亥拥立卓岩明为帝，换服并率将吏称臣',17,'己亥，','拜之。',[('李仁达','参与拥立卓岩明，并率将吏北面称臣'),('岩明','被拥立为帝，换衮冕受将吏朝拜')],when='945年三月己亥',place='福州',note='拥立的是僧卓岩明，不把李仁达写成当日皇帝。')
sup('zhuo_yanming_enthroned',17,minbook,'以雪峯寺僧卓儼明示眾曰：「此非常人也。」被以衮冕，率諸將吏北面而臣之。','《新五代史》同一雪峰寺僧被李仁达披衮冕、率将吏称臣的场景写卓俨明。','同寺同人同一立帝过程对应，姓名岩、儼异文作为检索别名保留，正字仍待纸本校核；后文再杀未提前。',relation='adds')
claim('person',people['卓岩明'],'aliases','卓岩明在《新五代史》对应雪峰寺僧被立为帝的段落中写作卓俨明。',17,'以雪峯寺僧卓儼明示眾曰：「此非常人也。」被以衮冕，率諸將吏北面而臣之。','同场立帝对应，保留姓名異文；并未据音近把另一名僧人合并。'.replace('異','异'),source=minbook)
add('zhuo_uses_jin_year_submits','卓岩明政权仍用天福十年纪年，并遣使向后晋称臣',17,'然犹称', '于晋。',[('岩明','其政权用天福十年纪年，并向后晋称臣')],when='945年三月己亥被立之后；政权称天福十年',place='福州至后晋朝廷',note='后晋本年通行开运二年，而福州仍称天福十年，保留双方年号，不改成另外一个公元年或已受后晋册封。')
add('yanzheng_kills_huang_family','王延政得知福州政变后，杀黄仁讽家属',17,'延政闻之，','仁讽家，',[('闽主','得知福州政变后诛杀黄仁讽家属'),('黄仁讽','其家属被王延政诛杀')],when='945年福州政变之后，具体日未载',place='建州、黄仁讽家属所在',note='家属未具名与人数未列，不虚构姓名；黄仁讽本人仍在福州，不写当时本人也死。')
add('zhang_hanzhen_fleet_fuzhou','王延政派张汉真率五千水军，会漳、泉兵讨卓岩明',17,'命统军使张汉真',None,[('闽主','派张汉真率水军会漳、泉兵讨卓岩明'),('张汉真','率水军五千会合漳、泉兵讨卓岩明'),('岩明','其福州政权成为王延政出兵目标')],when='945年福州政变之后',place='建州、漳州、泉州至福州',note='五千只明确水军，漳泉兵另未列数，不能称整支联军总计恰五千。')
# 18: successive operations with differences between narrative dates and memorial dates.
add('jin_armies_gather_dingzhou','杜重威等后晋诸军会合定州',18,'乙巳，','定州，',[('杜威','与诸军在定州会合')],when='945年三月乙巳',place='定州')
sup('jin_armies_gather_dingzhou',18,old,'乙巳，左補闕袁範先陷契丹，自賊中逃歸。杜威奏，與李守貞、馬全節、安審琦、皇甫遇部領大軍赴定州。','《旧五代史》补记杜重威在乙巳条下奏报，与李守贞、马全节、安审琦、皇甫遇率大军赴定州。','杜奏为奏报，各军赴与主书会合不是精确同一动作；原句前袁范逃归未重复录成本次会军人物。',relation='adds')
add('xiao_chujun_qizhou_deputy','后晋命萧处钧暂掌祁州事务',18,'以供奉官萧处钧','祁州事。',[('萧处钧','以供奉官身份暂知祁州事')],when='945年三月乙巳条下',place='祁州',note='权知为暂代，不直接称已正式授祁州刺史。')
add('jin_tingqian_surrenders_taizhou','后晋军进攻泰州，晋廷谦举州投降',18,'庚戌，','举州降。',[('晋廷谦','以泰州刺史身份举州投降后晋军')],when='945年三月庚戌',place='泰州',note='举州为率城归降，未补其亲自到后晋朝廷日期。')
sup('jin_tingqian_surrenders_taizhou',18,old,'庚戌，王師攻泰州，刺史晉庭謙以城降。','《旧五代史》同日同城归降写晋庭谦。','同为庚戌泰州刺史降城，姓名廷庭对应保留别名，未据字形另建同人。',relation='adds')
sup('jin_tingqian_surrenders_taizhou',18,liao,'庚子，杜重威、李守貞攻泰州。','《辽史》记杜重威、李守贞攻泰州的日期为庚子。','与主书、旧纪庚戌不同；辽句只明进攻不明晋氏归降，不推全部行动同日。',relation='conflicts',field='time_original')
add('jin_takes_mancheng','后晋军攻取满城，俘没剌及两千兵',18,'甲寅，','兵二千人。',[('没剌','作为契丹首领，在满城被后晋军俘获'),('杜威','其所领晋军攻取满城，俘没剌及兵')],when='945年三月甲寅',place='满城',note='俘获二千为本段数字，没有另补总守城人数或俘后处死。')
sup('jin_takes_mancheng',18,old,'甲寅，杜威奏，收復滿城，獲契丹首領沒剌相公，並蕃漢兵士二千人。','《旧五代史》记甲寅杜重威奏报收复满城，获没剌相公与蕃汉兵士二千。','主书取城条日、旧纪奏报日分别保存；酋长与相公为不同职衔表述，不外推官爵。',relation='adds')
add('jin_takes_suicheng','后晋军攻取遂城',18,'乙卯，','取遂城。',[('杜威','其所领后晋军攻取遂城')],when='945年三月乙卯',place='遂城')
sup('jin_takes_suicheng',18,old,'乙卯，杜威奏，收復遂城。','《旧五代史》记乙卯杜重威奏报收复遂城。','奏报日与实际占领日不强定相同。')
add('surrenderer_warns_khitan_returns','赵延寿部下的降者报告契丹主将率约八万余骑回军',18,'赵延寿部曲','宜速为备。”',[('杜威','收到降者关于契丹回军的消息'),('契丹主','被降者报告已再次率军南下')],when='945年三月丙辰退军前',place='后晋军营、虎北口',note='约八万余和次日将到都是降者报告，不能当已精确清点事实；虎北口保留原地名。')
sup('surrenderer_warns_khitan_returns',18,old,'時賊將趙延壽部曲來降，言：「契丹主昨至古北口，幽州走報，漢軍大下，收卻泰州。尋下令諸部，令輜重入塞，輕騎卻回。戎王率五萬餘騎，來勢極盛，明日前鋒必至，請為之備。」','《旧五代史》同类降者报告写古北口、五万余骑，并记遣辎重入塞、轻骑回军。','古北与虎北、五万余与八万余分书保留；均是报告言辞，未裁成确定兵数。',relation='conflicts')
add('du_retreats_to_taizhou','杜重威等惧契丹回军，于丙辰退保泰州',18,'杜威等惧，','退保泰州。',[('杜威','收到回军消息后率诸军退保泰州')],when='945年三月丙辰；旧纪丙辰退至满城、丁巳到泰州',place='遂城方向至泰州',note='主书概括丙辰退保，旧纪列中间满城与丁巳抵泰州，分别保留，不造两支重复撤退军。')
sup('du_retreats_to_taizhou',18,old,'是日，還滿城。丁巳，至泰州。','《旧五代史》写丙辰回满城、丁巳到泰州。','是日承丙辰，保留中间阶段及到达日。',relation='adds',field='time_original')
add('khitan_arrives_taizhou','契丹军到泰州',18,'戊午，','至泰州。',[],when='945年三月戊午；辽史戊子记前锋逼泰城',place='泰州')
sup('khitan_arrives_taizhou',18,liao,'戊子，趙延壽率前鋒薄泰城。','《辽史》将赵延寿前锋逼泰城记为戊子。','与主书戊午及旧纪前锋戊午不同，原纪日保留；薄是逼近，不直接写已经入城。',relation='conflicts',field='time_original')
add('jin_southward_khitan_pursues','后晋军于己未南撤，契丹紧随其后',18,'己未，','契丹踵之。',[('杜威','率后晋军南撤')],when='945年三月己未',place='泰州至阳城')
add('yangcheng_first_battle','后晋军在阳城击退契丹，追击十余里至白沟',18,'晋军至阳城，',None,[('杜威','其所领晋军在阳城击退契丹，并追至白沟')],when='945年三月庚申，晋军先已到阳城',place='阳城至白沟',note='本次庚申初战与癸亥围寨、次晨决战分阶段，不把所有阳城战事压成一个瞬间。')
sup('yangcheng_first_battle',18,old,'庚申，敵騎如墻而來，我步軍為方陣以禦之。選勁騎擊賊，鬥二十餘合，南行十餘里，賊勢稍卻，渡白溝而去。','《旧五代史》补方阵御敌、选择劲骑攻击和二十余合交战。','主书逐北十余里与旧纪南行十余里分别保留，不能当精确相同路线。',relation='adds')
sup('yangcheng_first_battle',18,liao,'己未，重威、守貞引兵南遁，追至陽城，大敗之。','《辽史》在己未记追到阳城并大败后晋军。','该书初战结果与主书庚申晋胜不同，保留日期及战果叙述，不用后续辽军败绩删除本句。',relation='conflicts')
# 19–20: a harried retreat, encirclement, tactical arguments and breakout.
add('jin_forms_southward_array','后晋军于壬戌结阵南行，被契丹骑兵包围交战',19,'壬戌，','拒之。',[('杜威','所率诸军结阵南行，抵御四面围来的契丹骑兵')],when='945年三月壬戌',place='阳城方向南行途中')
add('jin_army_hungry_slow','后晋军壬戌仅行十余里，人马饥饿疲乏',19,'是日，',None,[],when='945年三月壬戌',place='阳城方向南行途中',note='十余里为概数，不自行换算精确公里或增加伤亡数。')
add('jin_camps_baituan','后晋军到白团卫村，以鹿角构筑行寨',20,'癸亥，','行寨。',[('杜威','其所领晋军在白团卫村以鹿角设行寨')],when='945年三月癸亥',place='白团卫村',note='鹿角是防御障碍物，不理解成野生动物数量。')
add('khitan_cuts_supply_baituan','契丹重重包围晋军，并派奇兵绕后截断粮道',20,'契丹围之','断粮道。',[('契丹主','其所领军队包围晋军，派奇兵截断粮道')],when='945年三月癸亥',place='白团卫村',note='具体奇兵将领未列，不从后期另一次断粮战事借名。')
sup('khitan_cuts_supply_baituan',20,yb,'契丹以奇兵出陣後，斷糧道，','《宋史》药元福传也记契丹奇兵绕到晋军阵后断粮道。','旧本纪注中所引同传不算另一个独立目击证据。')
add('jin_thirst_wells_collapse','东北大风中晋军掘井坍塌，士卒绞泥水饮用，人马口渴',20,'是夕，','人马俱渴。',[],when='945年三月癸亥当晚',place='白团卫村',note='士卒取泥绞饮是极端缺水的具体记载，不据此添病名或精确伤亡人数。')
sup('jin_thirst_wells_collapse',20,fb,'軍中乏水，鑿井輒壞，爭絞泥吮之，人馬多渴死，','《宋史》符彦卿传进一步记人马多人渴死。','多渴死为该传补充，未列人数，不将主书人马俱渴直接翻成全部死亡。',relation='adds')
add('yelu_plans_capture_then_daliang','耶律德光宣称要尽俘晋军，再南取大梁',20,'至曙，','南取大梁！”',[('契丹主','天明大风中宣称要尽俘晋军，随后南取大梁')],when='945年三月癸亥次晨，原文未单列干支',place='白团卫村',note='尽擒南取为其计划和号令，晋军随后突围，不写当日大梁已经失守。')
add('khitan_dismounts_breaks_defenses','耶律德光命铁鹞下马拔鹿角，以短兵及顺风火尘攻击',20,'命铁鹞','助其势。',[('契丹主','命铁鹞下马毁晋军障碍，配合火焰尘土进攻')],when='945年三月癸亥次晨',place='白团卫村',note='铁鹞为军中称呼，不写为独立将领或鸟类；号令和实际拔障进攻属于同一攻营过程。')
sup('khitan_dismounts_breaks_defenses',20,liao,'至曙，命鐵鷂軍下馬，拔其鹿角，奮短兵入擊。順風縱火揚塵，以助其勢。','《辽史》也记天明命铁鹞下马毁鹿角，以短兵、火尘进攻。','表述与通鉴近似，可能有史源依赖，不当两份独立现场记录。')
add('jin_soldiers_demand_battle','晋军士兵愤怒呼喊要求出战，诸将向杜重威请战',20,'军士皆愤怒，','诸将请出战，',[('杜威','受到诸将及士兵要求立即出战的催请')],when='945年三月癸亥次晨',place='白团卫村晋营',note='诸将此句未具名，不能为每一名在场人另造个人奏请事实。')
add('du_delays_for_wind','杜重威要求等风减弱，再决定是否出战',20,'杜威曰：','可否。”',[('杜威','要求待风减弱后再观察是否出战')],when='945年三月癸亥次晨',place='白团卫村晋营')
add('li_shouzhen_urges_immediate_attack','李守贞认为风沙使敌难辨兵数，主张立即决战',20,'马步都监李守贞','无类矣。”',[('李守贞','认为风沙可以掩盖兵力，主张不要等风停而立即力战')],when='945年三月癸亥次晨',place='白团卫村晋营',note='风助我为将领战术判断，不当自然现象专为晋军而发生。')
add('li_orders_joint_attack_and_roles','李守贞号召诸军齐击，令杜重威守营，自率中军决战',20,'即呼曰：','决死矣！”',[('李守贞','号召诸军攻击，自称率中军决战'),('杜威','被李守贞要求负责守营')],when='945年三月癸亥次晨',place='白团卫村晋营',note='话中分工不等于杜重威完全没有任何后续出击命令；后文他仍遣精骑追击。')
add('zhang_consults_wait_wind','张彦泽召诸将问计，起初也同意等风向改变',20,'马军左厢都排陈使张彦泽','以为然。',[('张彦泽','问计诸将后，起初同意等风向改变再战')],when='945年三月癸亥次晨',place='白团卫村晋营')
sup('zhang_consults_wait_wind',20,zm,'彥澤以問諸將，諸將皆曰：「今虜乘上風，而吾居其下，宜待風回乃可戰。」彥澤以為然。','《新五代史》也记张彦泽起初接受等风回的建议。','后来接受急攻意见为另一个阶段，不因后来的勇战倒写他从未犹豫。')
add('yao_yuanfu_urges_reverse_wind','药元福独留劝张彦泽，应趁敌不备逆风急击',20,'诸将退，','诡道也。”',[('药元福','指出人马饥渴，劝张彦泽不要等风回，逆风出其不意'),('张彦泽','听取药元福逆风急击建议')],when='945年三月癸亥次晨',place='白团卫村晋营')
sup('yao_yuanfu_urges_reverse_wind',20,yb,'守貞與元福謀曰：「軍中饑渴已甚，若俟風反出戰，吾屬為虜矣！彼謂我不能逆風以戰，宜出其不意以擊之，此兵家之奇也。」','《宋史》药元福传将逆风急攻的商议记为李守贞与药元福共同提出。','主书写药单独劝张、李另发言，双方具体谈话对象不同，各书独立保留，不拼成确定同一场会议。',relation='adds')
claim('person',people['药元福'],'description','药元福为并州晋阳人，早年侍奉王檀，后来任后唐军职，晋天福时任深州刺史。',20,'藥元福，幷州晉陽人。幼有膽氣，善騎射。初事邢帥王檀為廳頭軍使，以勇敢聞。事後唐，為拱衛、威和親從馬鬥軍都校，天平軍內外馬軍都指揮使。晉天福中，為深州刺史。','籍贯与主书太原相合，具体早年任命年日未列；只补人物履历，不把前事硬定为945年。',source=yo)
add('fu_proposes_fight_for_country','符彦卿提出与其被俘，不如以身报国出战',20,'马步左右厢都排陈使符彦卿','徇国！”',[('符彦卿','主张出战，不愿束手被俘')],when='945年三月癸亥次晨',place='白团卫村晋营')
add('four_generals_break_west_gate','符彦卿、张彦泽、药元福、皇甫遇率精骑出西门，诸将跟进',20,'乃与彦泽、','契丹却数百步。',[('符彦卿','与张彦泽、药元福、皇甫遇率精骑出西门攻击'),('张彦泽','与符彦卿等率精骑出西门攻击'),('药元福','与符彦卿等率精骑出西门攻击'),('皇甫遇','与符彦卿等率精骑出西门攻击')],when='945年三月癸亥次晨',place='白团卫村晋营西门',note='西门是行寨出口，不自动认成阳城县城西门；初击退敌数百步是战术阶段。')
sup('four_generals_break_west_gate',20,zm,'彥澤即拔拒馬力戰，契丹奔北二十餘里，','《新五代史》张彦泽传以张彦泽拔拒马出战概括这一反击。','主书四将出西门的具体过程与传记重在张的叙述并列，不因主角不同剔除其他将领。',relation='adds')
sup('four_generals_break_west_gate',20,fb,'遂潛兵尾其後，順風擊之，契丹大敗，','《宋史》符彦卿传写潜兵跟到敌后，顺风攻击。','与药元福传逆风出其不意及主书正面破寨的叙述不同，独立保留战术异说，不将两说拼成完整无疑的绕后方案。',relation='conflicts')
add('li_calls_long_advance','符彦卿等请问攻击方式，李守贞命直接长驱取胜',20,'彦卿等谓守贞','取胜耳！”',[('符彦卿','就队列往返还是直进询问李守贞'),('李守贞','要求直接长驱奋击取胜')],when='945年三月癸亥次晨，初击后',place='白团卫村附近')
add('fu_cavalry_smashes_khitan','符彦卿等拥万余骑横击，契丹大败逃走',20,'彦卿等跃马','势如崩山。',[('符彦卿','率万余骑横击契丹军'),('张彦泽','随符彦卿等以骑兵猛攻'),('药元福','随符彦卿等骑兵攻击'),('皇甫遇','随符彦卿等骑兵攻击')],when='945年三月癸亥次晨决战',place='白团卫村附近',note='万余为该攻击群概数，不分每将各万余；风昏晦如夜为天气描写，不当夜间作战。')
sup('fu_cavalry_smashes_khitan',20,liao,'符彥卿以萬騎橫擊遼軍，率步卒並進，遼軍不利。','《辽史》也记符彦卿以万骑横击并与步兵并进，辽军失利。','万骑与主书万余分别保存，辽文与主书近似不作为完全独立确证。')
add('li_infantry_breaks_defenses_pursues','李守贞命步兵拔鹿角出战，步骑并进追敌二十余里',20,'李守贞亦令','二十馀里。',[('李守贞','命步兵拔去鹿角出营，与骑兵并进追击')],when='945年三月癸亥次晨决战后',place='白团卫村至追击途中',note='二十余里为追击概数，不给未核现代里程和终点坐标。')
sup('li_infantry_breaks_defenses_pursues',20,oc,'時步騎齊進，追襲二十餘里。','《旧五代史》同记步骑齐进，追袭二十余里。','此续段承接前段战事，段首引用宋史的文字不当旧史独立自叙。')
add('khitan_dismounted_abandons_gear','下马的契丹铁鹞来不及上马，丢弃大量马匹铠甲',20,'铁鹞既下马，','蔽地。',[],when='945年三月癸亥次晨败退时',place='白团卫村附近',note='委弃没有精确数量，不能补全军所有马匹都被俘。')
sup('khitan_dismounted_abandons_gear',20,fb,'獲其器甲、旗仗數萬以歸。','《宋史》符彦卿传记晋军带回器甲、旗仗数万。','该传战利品数量独立保存，不将器甲旗仗数万改成人员斩首数万。',relation='adds')
add('du_orders_attack_regrouping','契丹败兵在阳城东南水边重整，杜重威派精骑再击，使其渡水退走',20,'契丹散卒','皆渡水去。',[('杜威','阻止败军重整，派精骑再击使其渡水退走')],when='945年三月癸亥次晨决战后',place='阳城东南水边',note='水名未明确，不自动套白沟；这道实际攻击命令与之前待风的意见分别保留。')
sup('du_orders_attack_regrouping',20,oc,'至陽城東，賊軍稍稍成列，我騎復擊之，乃渡河而去。','《旧五代史》同记阳城东契丹军再列阵，晋骑再击，契丹渡河退去。','东与东南、水与河分别保留地理表达，不补确定现代河名。')
add('yelu_switches_camel_escape','耶律德光乘奚车逃十余里，追兵逼近后换乘骆驼逃走',20,'契丹主乘奚车','乘之而走。',[('契丹主','先乘奚车逃走，追兵迫近时换乘得到的骆驼')],when='945年三月癸亥次晨战败后',place='阳城方向逃军途中',note='获一橐驼为逃方得到一匹骆驼，不误写晋军俘虏契丹主；未列最终单程距离。')
sup('yelu_switches_camel_escape',20,liao,'上乘奚車退十餘里，晉追兵急，獲一橐駝乘之乃歸。','《辽史》也记契丹主从奚车改乘骆驼退走。','上指辽太宗耶律德光，先核传主，不能指晋帝。')
add('generals_request_urgent_pursuit','诸将请求继续急追契丹败军，杜重威反对',20,'诸将请急','衣囊邪？”',[('杜威','以幸免死为由，反对诸将请求继续急追')],when='945年三月癸亥次晨战败后',place='阳城附近晋军')
add('li_opposes_further_pursuit','李守贞认为人马饮水后沉重难行，主张保全军队返回',20,'李守贞曰：','全军而还。”',[('李守贞','以人马渴乏、饮水后难行解释，主张全军返回')],when='945年三月癸亥次晨战后',place='阳城附近晋军',note='皆足重是将领对疲乏的解释，不当医学诊断；不追为当时决策，不建李与杜永久盟友。')
sup('li_opposes_further_pursuit',20,oc,'兩日以來，人馬渴乏，今吃水之後，腳重難行，速宜收軍定州，保全而還，上策也。','《旧五代史》也记李守贞以两日渴乏、饮水后脚重为由，主张回定州。','发言者由前句守贞曰确认，不把理由当对每名兵士的实测医学状态。')
add('jin_returns_dingzhou_after_victory','后晋军在阳城获胜后退保定州',20,'乃退保','定州。',[('杜威','率晋军回定州'),('李守贞','建议保全军队，晋军退回定州')],when='945年三月阳城决战后',place='阳城至定州')
add('yelu_punishes_commanders_except_zhao','耶律德光回幽州集兵，因败战杖罚诸首领，赵延寿免罚',20,'契丹主至幽州，',None,[('契丹主','回幽州集兵后杖罚诸首领，唯不罚赵延寿'),('赵延寿','在败军处罚中得免杖罚')],when='945年三月败军回幽州后',place='幽州',note='各数百为书内笞杖数字，未具名首领和存亡不补；唯赵免不证明他没有参战。')
extra('yao_yuanfu_weizhou','后晋在阳城战后任药元福为威州刺史',20,yb,'以元福為威州刺史。',[('药元福','阳城战后获任威州刺史')],when='945年阳城战后，宋史未列具体日',place='威州',note='威州不同于魏州；早年深州、原州与当前授威州不混，944年澶州功事未在本段展开。')
# 21–23: withdrawal, imperial return and the restoration of a military district.
add('jin_armies_leave_dingzhou','后晋诸军于乙丑离定州返回',21,'乙丑，','引归。',[('杜威','与诸军从定州返回')],when='945年三月乙丑',place='定州向南')
sup('jin_armies_leave_dingzhou',21,oc,'乙丑，杜威等大軍自定州班師入恒州。','《旧五代史》明确乙丑班师进入恒州。','主书引归未写此中间地点，旧纪补恒州，不把所有军都已到大梁。',relation='adds')
add('taizhou_attached_dingzhou','后晋诏将泰州归定州管辖',21,'诏以',None,[],when='945年三月乙丑条下',place='泰州、定州',note='州军管辖变化不等同迁走全部居民。')
add('shi_leaves_chanzhou_return','石重贵从澶州出发还京',22,'夏，四月，','发澶州，',[('帝','从澶州出发还京')],when='945年四月辛巳',place='澶州至大梁')
sup('shi_leaves_chanzhou_return',22,apr,'辛巳，駕發澶州。','《旧五代史》同记辛巳离澶州。','离开与到达分阶段。')
add('shi_returns_daliang','石重贵返回大梁',22,'甲申，',None,[('帝','返回大梁')],when='945年四月甲申',place='大梁')
sup('shi_returns_daliang',22,apr,'甲申，至京師，曲赦在京禁囚。','《旧五代史》同记甲申回京，并补赦京城囚犯。','回京与赦囚分别录，不把曲赦概括为天下皆赦。',relation='adds')
extra('jin_pardons_capital_prisoners','石重贵还京后赦免京城囚犯',22,apr,'甲申，至京師，曲赦在京禁囚。',[('帝','回京后赦免京城囚犯')],when='945年四月甲申',place='大梁',note='曲赦仅限所明京城禁囚，不解为全国大赦。')
add('yedu_restored_tianxiong','后晋将邺都恢复为天雄军',23,'己丑，',None,[],when='945年四月己丑；旧本纪己亥',place='邺都',note='这是军镇制度恢复，不能据名军将邺都当作地理消失；纪日异文保留。')
sup('yedu_restored_tianxiong',23,apr,'己亥，詔鄴都依舊為天雄軍。','《旧五代史》记恢复天雄军诏令的日期为己亥。','主书己丑与旧本纪己亥不同，待核纸本，不强认两次恢复军镇。',relation='conflicts',field='time_original')
# Related reward dispositions in the same imperial return entry.
for code,name,title,quote,role,place in [
 ('liu_beiping','刘知远','后晋封刘知远为北平王','庚寅，河東節度使劉知遠封北平王；','获封北平王','河东'),
 ('du_grand_preceptor','杜威','后晋加杜重威守太傅','恒州節度使杜威加守太傅；','以恒州节度使身份加守太傅','恒州'),
 ('zhao_yanzhou','赵在礼','后晋移赵在礼镇兖州','徐州趙在禮移鎮兗州；','由徐州移镇兖州','徐州至兖州'),
 ('gao_yunzhou','高行周','后晋移高行周镇郓州，仍领侍卫','宋州節度使兼侍衛親軍馬步都指揮使高行周移鎮鄆州，侍衛如故；','由宋州移镇郓州，保留侍卫亲军统领职','宋州至郓州'),
 ('ma_tianxiong','马全节','后晋任马全节为天雄军节度使','鄴都留守馬全節改天雄軍節度使；','由邺都留守改任天雄军节度使','天雄军'),
 ('li_songzhou','李守贞','后晋移李守贞镇宋州，加侍卫亲军副指挥使','兗州節度使兼侍衛都虞候李守貞移鎮宋州，加檢校太師兼侍衛親軍副指揮使；','移镇宋州，加检校太师和侍卫亲军副指挥使','兖州至宋州'),
 ('an_xuzhou','安审琦','后晋授安审琦侍中，移镇许州','河中節度使安審琦加兼侍中，移鎮許州；','加兼侍中，由河中移镇许州','河中至许州'),
 ('fu_xuzhou','符彦卿','后晋授符彦卿同平章事，移镇徐州','許州節度使符彥卿加同平章事，移鎮徐州；','加同平章事，由许州移镇徐州','许州至徐州'),
 ('huangfu_title','皇甫遇','后晋加皇甫遇同平章事','滑州節度使皇甫遇加同平章事。','以滑州节度使身份加同平章事','滑州')]:
 extra('post_yangcheng_'+code,title,23,apr,quote,[(name,role)],when='945年四月庚寅',place=place,note='同本纪庚寅任官条下所列战后处置，与恢复天雄军诏令为不同阶段；不因早有同类加号便删本次明确再加记载。')
sup('post_yangcheng_fu_xuzhou',23,fb,'少帝嘉之，改武寧軍節度、同平章事。','《宋史》符彦卿传也记阳城战后改武宁军节度、加同平章事。','武宁对应徐州军镇，传记未列日，具体庚寅来自旧本纪。')
# 24: the Fuzhou counterattack, rituals, remorse and further executions.
add('zhang_hanzhen_attacks_east_gate','张汉真到福州，攻城东关',24,'闽张汉真','东关。',[('张汉真','率闽军到福州攻东关')],when='945年四月条下，具体日未载',place='福州东关')
add('huang_breaks_yanzheng_attack','黄仁讽得知家属被杀，开门出战，大败来攻闽军',24,'黄仁讽闻','大破闽兵，',[('黄仁讽','获知家属被杀后，开门出战击败闽軍'.replace('軍','军'))],when='945年四月条下',place='福州城外',note='家属被杀已在第17段录，获知是本段行动缘由，不造第二次家属遭杀。')
add('huang_captures_zhang_hanzhen','黄仁讽俘获张汉真，押入福州城',24,'执汉真，','入城，',[('黄仁讽','俘张汉真，带入城中'),('张汉真','被黄仁讽俘获并带入福州')],when='945年四月福州交战后',place='福州')
add('huang_executes_zhang_hanzhen','黄仁讽将俘获的张汉真斩杀',24,'斩之。','斩之。',[('黄仁讽','在福州城中斩杀张汉真'),('张汉真','被俘后在福州城中斩杀')],when='945年四月福州交战后',place='福州')
add('zhuo_rituals_in_palace','卓岩明在殿上喷水散豆、举行法事，未见其他治军方略',24,'卓岩明無'.replace('無','无'),'而已。',[('岩明','在殿上喷水散豆、举行各种法事')],when='945年四月条下的政权情形',place='福州宫殿',note='无它方略是史書评价，法事为行为记载，不录成有超自然效力或真实御敌效果。'.replace('書','书'))
add('zhuo_honors_unnamed_father','卓岩明遣使从莆田迎父，尊为太上皇',24,'又遣使迎其父','太上皇。',[('岩明','遣使从莆田迎接父亲，尊父亲为太上皇')],when='945年四月条下，具体日未载',place='莆田至福州',note='父亲未具名，不虚构名字或建立带占位姓名的人物；遣使迎父不单独补到达日。')
add('li_renda_controls_six_armies','李仁达拥立卓岩明后，自掌六军诸卫事务',24,'李仁达既立岩明，','诸卫事，',[('李仁达','拥立卓岩明后自行掌管六军诸卫事务')],when='945年卓岩明被立之后，具体日未载',place='福州',note='既立追述拥立后的掌兵，不再建第二次立帝事件。')
add('li_assigns_huang_west_gate','李仁达命黄仁讽守西门',24,'使黄仁讽','屯西门，',[('李仁达','派黄仁讽守福州西门'),('黄仁讽','受命屯兵西门')],when='945年李仁达掌兵时，具体日未載'.replace('載','载'),place='福州西门')
add('li_assigns_chen_north_gate','李仁达命陈继珣守北门',24,'陈继珣','屯北门。',[('李仁达','派陈继珣守福州北门'),('陈继珣','受命屯兵北门')],when='945年李仁达掌兵时，具体日未载',place='福州北门')
add('huang_regrets_betrayal','黄仁讽向陈继珣痛陈背主、杀继昌与弃家之愧，抚胸哭泣',24,'仁讽从容','恸哭。',[('黄仁讽','向陈继珣反省背叛王延政、杀受托王继昌、杀同乡及家属被害'),('陈继珣','听黄仁讽陈述自责')],when='945年四月条下',place='福州',note='伦理评价与十沉九浮为黄仁讽自述，不换成确实溺水次数；亡家自责不补所有家人姓名。')
add('chen_dismisses_huang_remorse','陈继珣劝黄仁讽追求功名，停止自责以免招祸',24,'继珣曰：','取祸。”',[('陈继珣','劝黄仁讽勿顾家属、勿再谈自责，以免招祸'),('黄仁讽','受到陈继珣劝止')],when='945年四月条下',place='福州')
add('li_accuses_huang_chen_treason','李仁达听到两人谈话后，派人告黄仁讽、陈继珣谋反',24,'仁达闻之，','谋反，',[('李仁达','派人告黄仁讽、陈继珣谋反'),('黄仁讽','被李仁达派人告谋反'),('陈继珣','被李仁达派人告谋反')],when='945年四月条下',place='福州',note='告谋反是指控，前段只是自责谈话，不据此认定二人已计划或实行反叛。')
add('li_kills_huang_renfeng','李仁达在谋反指控后杀黄仁讽',24,'仁达闻之，','皆杀之。',[('李仁达','派人告谋反后杀黄仁讽'),('黄仁讽','在谋反指控后被李仁达杀死')],when='945年四月条下',place='福州')
add('li_kills_chen_jixun','李仁达在谋反指控后杀陈继珣',24,'仁达闻之，','皆杀之。',[('李仁达','派人告谋反后杀陈继珣'),('陈继珣','在谋反指控后被李仁达杀死')],when='945年四月条下',place='福州')
add('li_renda_concentrates_army_power','黄仁讽、陈继珣死后，福州兵权全部归李仁达',24,'由是兵权',None,[('李仁达','在杀黄仁讽、陈继珣后掌握全部福州兵权')],when='945年四月条下两人被杀之后',place='福州',note='兵权集中不等同李仁达此时已称皇帝；卓岩明仍为所立政权君主。')
for name,n,quote in [('王继昌',17,'是夕，仁达等引甲士突入府舍，杀继昌及吴成义。'),('吴成义',17,'是夕，仁达等引甲士突入府舍，杀继昌及吴成义。'),('张汉真',24,'执汉真，入城，斩之。'),('黄仁讽',24,'仁达闻之，使人告仁讽、继珣谋反，皆杀之。'),('陈继珣',24,'仁达闻之，使人告仁讽、继珣谋反，皆杀之。')]:
 claim('person',people[name],'death_year',name+'于945年福州政变及相关交战中被杀。',n,quote,'原文在945年连续记事中明确被杀；具体纪日按各事件保留，不补年龄或未知家属姓名。')
sup('jin_takes_mancheng',18,ny,'甲寅，杜威克滿城。乙卯，克遂城。','《新五代史》本纪同记甲寅杜重威克满城、乙卯克遂城。','同日行动按两城阶段记录，不把后一乙卯套给前城。')
reviews={17:'李早年十五年任职及陈先是均不倒推年月；李在朱夺权后投福、被黜属于944。谋议、杀两将、拥僧及称晋藩分开，天福十年是福州所用年号而非改主书纪年；卓岩儼姓名同场对应保留，神异相貌是李说辞。',18:'主书行动日与旧纪奏报日分清；晋廷庭同日同州人名异文，没剌不与音近人合并。降者五八万、古虎北口、庚子庚戌攻泰及戊子戊午逼城日期并列，丙辰至满城丁巳至泰补中间行程，阳城初战与后续决战分阶段。',19:'壬戌结阵抵御与饥乏慢行分录，未列具体杀伤不补数字。',20:'围寨断粮、缺水掘井、大风攻营、待风与急攻意见、四将出西门、万骑横击、步骑并进及再次击败重整军分开。宋符顺风跟后与宋药逆风急攻为不同叙述，未拼成确定战术；战略目标南取大梁不是实际已陷，驼为契丹主逃骑不是被晋俘。',21:'乙丑离定州与泰隶定州行政变化分开，旧纪补班师入恒州中间地。',22:'辛巳离澶、甲申到梁及曲赦京囚分别记，未概括全国大赦。',23:'天雄恢复己丑己亥异文并列；战后庚寅加号移镇与军额恢复分开，许徐、河中宋郓等地不混。',24:'张攻黄破、俘张后斩、卓法事及迎父、李自掌兵及派两门驻军、黄自责与陈劝、李指控和分杀两人后集兵权分开。指控不认确实谋反，家属已前段遇害不重建；卓父未具名不虚构主体，未提前卓被杀。'}
assert not (P/'publication.json').exists()
for n in range(17,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=945,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=284,next_year=945,supplements=supplements,excluded_non_body=[],coverage='卷284原68—75行连续第17—24段，三月至四月及追述。下一段五月大赦，945年全年未完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'只处理福州初次政变、军会定州至阳城初战及壬戌退军，前段已发表不重复。'),(main_sources[1],'只处理第20—24段，长段全部行动拆分，未取之后五月。'),(minbook,'只补王继昌被杀、僧卓儼明被立；后文僧被杀、李称留后及弘义改名留对应下段，不提前；该书结尾保大四年不能强套前部每事。'),(old,'只补本次三月进军与决战叙述，开头祁州已上一批处理。'),(oc,'旧纪三月续段段首承接宋史引文，已核不是独立的第二份宋证；正文追击、返定及班师入恒分录。'),(apr,'补帝回京赦囚、军额恢复异日及庚寅战后任官，未取其他日景侯王加号。'),(yo,'只补药籍贯及早年履历，不把追述系945。'),(yb,'补当前药出击与授威，后文灵州等事留以后；此前开运初澶州功事未在本段重写。')]],source_issues_review='新旧史与辽史进军干支、初战胜败、降者报告五八万及古虎北口、宋符顺风跟后与宋药逆风出击、恢复天雄己丑己亥分别保留。卓岩儼、晋廷庭同一场景姓名异文留检索别名，仍待纸本核正字。小说式神异描述、指控谋反和未执行计划有明确归属，不作新事实定案。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],plain_language_review='首次逐条核对所有标题、人物、事件、参与、关系、时间与事实说明，主语明确，简体白话。长战事按行动与谈话过程分录，所言兵数、计划、军议、被俘、斩杀、假指控和实际结果分清。原文保持底本字形。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
