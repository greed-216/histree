# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 954 paragraphs 6–13."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,26))
COMMIT='b8cc8594d63007caf3bc997ace00c8ade1071c2e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-954-may-siege','xinwudaishi-70-sang-gui-zheng','jiuwudaishi-114-siege-labor-954','xinwudaishi-12-chairong-accession']:
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
main_sources = ['tongjian-292-954-may-siege','tongjian-292-954-summer-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0954-p006-p013',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
for n in range(6, 14):
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
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷292·显德元年（954年围晋阳至八月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0954_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_292_0954_' + code
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
        edge = 'participation_zztj_292_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'柴荣','北汉主':'刘崇（刘知远弟）','承钧':'刘承钧','钱弘亻叔':'钱弘俶'})
NEW_ALIASES={'高锡':['高錫'],'景范':['景範'],'李彦崇':['李彥崇']}
NEW_DESCRIPTIONS={'高锡':'河中人，后周河南府推官。954年柴荣围晋阳返朝后，上书劝他选择适任官员、让宰相和地方官分掌事务，不要事事亲决，柴荣未采纳。生卒年未载。','景范':'长山人，后周枢密直学士、工部侍郎。954年七月癸巳获任中书侍郎、同平章事并判三司。《旧五代史》同记任命，名字作景範。生卒年未载。','李彦崇':'前泽州刺史。954年高平之战时奉命守江猪岭，截断北汉退路，却在听闻周军南逃后退兵，使刘崇得以经该路逃归。八月己酉因失职降任率府副率。生卒年未载。'}
old='jiuwudaishi-114-siege-labor-954';july='jiuwudaishi-114-july-954';aug='jiuwudaishi-114-august-li-yanchong';new='xinwudaishi-12-chairong-accession';sang='xinwudaishi-70-sang-gui-zheng';yao='songshi-254-yao-yuanfu-retreat'
add('wang_dezhong_stays_daizhou','王得中从契丹返回，遇周军围晋阳，留在代州',6,'初，王得中返自契丹，','留止代州。',[('王得中','从契丹返回后留在代州')],when='954年周军围晋阳期间、桑珪杀郑处谦以前',place='代州',note='初回述先前行程，未把返回直接定在末句甲辰处死当天。')
add('sang_detains_wang_dezhong','桑珪杀郑处谦后，拘捕王得中并送到周军',6,'及桑珪杀郑处谦，','送于周军。',[('桑珪','拘捕王得中并送交周军'),('王得中','被捕后送往周军')],when='954年五月代州杀郑处谦之后',place='代州至周军')
sup('sang_detains_wang_dezhong',6,sang,'代州將桑珪殺防禦使鄭處謙，以城降周，并送得中于周。','《新五代史》也记桑珪杀郑处谦后送王得中到周军。','杀郑事件已在上一批录入，本条只补王得中遭拘送的后续，不重复建立杀郑事件。')
add('chairong_questions_wang_relief','柴荣释放王得中并赐带马，询问契丹援兵到达时间',6,'帝释之，','虏兵何时当至？”',[('帝','释放赐物后询问援军'),('王得中','获释和赐物，受到询问')],when='954年围晋阳时王得中被送至周军后',place='晋阳城下周军')
add('wang_dezhong_denies_other_mission','王得中回答只奉命送杨衮，没有其他请求',6,'得中曰：“臣受命','他无所求。”',[('王得中','对柴荣隐瞒求援任务')],when='954年围晋阳期间受问时',place='周军',note='回答不代表确未求援，主书此前已录向契丹求援与承诺，此处是当事人回答。')
add('wang_dezhong_explains_silence','王得中说明母亲困在晋阳，不愿透露援军使家国两亡',6,'或谓得中曰：','所得多矣！”',[('王得中','解释宁愿被杀也不透露契丹援军')],when='954年被俘询问后、甲辰被杀以前',place='周军',note='周人必据险、家国两亡为王得中的预判，不作为已经发生的结果；老母未具姓名，不造人物。')
add('chairong_hangs_wang_dezhong','柴荣以王得中欺骗为由，将他缢杀',6,'甲辰，',None,[('帝','以欺罔为由处死王得中'),('王得中','被缢杀')],when='954年甲辰，围晋阳末期、撤军前；原文此处未重标月份',place='晋阳城下周军')
sup('chairong_hangs_wang_dezhong',6,sang,'已而契丹敗符彥卿於忻口，得中遂見殺。','《新五代史》也记符彦卿忻口失利后，王得中被杀。','保留先忻口失利后王被杀的次序，未补新史未载的行刑日。')
claim('person',people['王得中'],'death_year','王得中于954年被柴荣以欺罔为由缢杀。',6,'甲辰，帝以得中欺罔，缢杀之。','死亡年据显德元年连续正文；既有主体死亡字段不无守卫覆盖。')
add('chairong_withdraws_jinyang','柴荣离开晋阳，撤回后周',7,'乙巳，','帝发晋阳。',[('帝','率军撤离晋阳')],when='954年乙巳撤离晋阳，《通鉴》原干支；旧史在六月记撤军',place='晋阳')
sup('chairong_withdraws_jinyang',7,old,'六月癸卯朔，詔班師，車駕發離太原。','《旧五代史》记六月癸卯朔诏班师并离开太原。','旧史癸卯朔与主书乙巳离晋阳不同，分别保留，不统一为同日。',relation='conflicts',field='time_original')
sup('chairong_withdraws_jinyang',7,new,'六月乙巳，班師。','《新五代史》也记六月乙巳班师。','为主书乙巳提供六月上下文，旧史不同日期另列。')
add('yao_organizes_rearguard','药元福提醒退军难，柴荣交他统筹，药元福列队殿后',7,'匡国节度使药元福','勒兵成列而殿。',[('药元福','提醒退军风险，编军列队殿后'),('帝','将撤军安排交给药元福')],when='954年六月乙巳撤军时',place='晋阳撤退路')
sup('yao_organizes_rearguard',7,yao,'元福上言曰：「進軍甚易，退軍甚難。」世宗曰：「一以委卿。」遂部分卒伍為方陣而南，元福以麾下為後殿，','《宋史》补记药元福将军队编成方阵向南，以麾下殿后。','退军部署为实际安排，不把提醒写成未执行的建议。',relation='adds')
add('yao_repels_han_pursuit','北汉军追击撤退周军，药元福击退追兵',7,'北汉果出兵追蹑，','元福击走之。',[('药元福','击退追来的北汉军'),('北汉主','所部追击周军而被击退')],when='954年六月撤军途中',place='晋阳以南撤退路')
sup('yao_repels_han_pursuit',7,yao,'崇果出兵來追，元福擊走之。','《宋史》也记刘崇派兵追击、药元福击退追军。','印证殿后行动，不据此说撤军没有其他损失。')
add('zhou_burns_abandoned_stores','周军仓促撤走，焚毁城下数十万粮草',7,'然军还匆遽，','悉焚弃之。',[('帝','周军撤退时焚弃军粮草料')],when='954年六月撤军时',place='晋阳城下',note='原文数十万未列计量单位，不补斛、担或人数。')
sup('zhou_burns_abandoned_stores',7,old,'賊城之下，糧草數十萬，悉焚棄之。','《旧五代史》同记城下数十万粮草被焚弃。','两书都未在此给出明确计量，不生成精确重量。')
add('zhou_retreat_disorder','周军受谣言惊扰，互相抢掠，军需损失严重',7,'军中讹言相惊，','军须失亡不可胜计。',[('帝','撤退军队发生惊扰和物资损失')],when='954年六月撤军期间',place='周军撤退路',note='失亡不可胜计为概述，不编造伤亡人数或军需数量。')
add('zhou_officials_abandon_han_cities','后周安置在北汉州县的刺史等官员弃城逃走',7,'所得北汉州县，','皆弃城走，',[('帝','所任北汉州县官员随撤军弃城')],when='954年六月周军撤退后',place='此前归降后周的北汉州县')
add('sang_city_falls_to_han','桑珪不敢投周，闭城自守，北汉军攻陷代州',7,'惟代州桑珪',None,[('桑珪','既叛北汉又不敢归周，守城而被攻破'),('北汉主','派军攻陷代州')],when='954年六月周军撤退后的记载，具体攻陷日未载',place='代州',note='本段说攻拔城池，未说桑珪此时被杀，不补死亡。')
for code,title,start,end,when,place in [
 ('chairong_return_luzhou','柴荣返程到达潞州','乙酉，','帝至潞州。','954年六月乙酉，《通鉴》纪日','潞州'),
 ('chairong_return_zhengzhou','柴荣返程到达郑州','甲子，','至郑州。','954年六月甲子','郑州'),
 ('chairong_visits_songling','柴荣拜谒郭威嵩陵','丙寅，','谒嵩陵。','954年六月丙寅','嵩陵'),
 ('chairong_return_daliang','柴荣回到大梁','庚午，','至大梁。','954年六月庚午','大梁')]:
 add(code,title,8,start,end,[('帝','返程'+title[2:])],when=when,place=place)
sup('chairong_return_luzhou',8,old,'乙巳，車駕至潞州。','《旧五代史》把车驾至潞州记在六月乙巳。','主书乙巳离晋阳、乙酉到潞州；旧史乙巳已到潞州，日差分别保留。',relation='conflicts',field='time_original')
sup('chairong_visits_songling',8,old,'丙寅，帝親拜嵩陵，祭奠而退。','《旧五代史》同记六月丙寅柴荣亲拜嵩陵并祭奠。','葬郭威与柴荣后来谒陵是不同事件。')
sup('chairong_return_daliang',8,old,'庚午，帝至自河東。','《旧五代史》同记六月庚午从河东回朝。','旧史此句未再写大梁地名，与主书京师返程相对应。')
add('chairong_personally_decides_business','柴荣高平获胜后开始大小政务亲决，百官承受指令',8,'帝违众议破北汉，','百官受成于上而已。',[('帝','开始亲自决定大小政务')],when='954年高平战后至返朝后的政务概述',place='后周朝廷',note='破北汉在此指击败北汉军，不是已经灭亡北汉国；不把自是概述硬定成六月庚午单日政策。')
add('gaoxi_petitions_delegation','高锡上书劝柴荣择人分职，按功过赏罚，不要代行所有臣职',8,'河南府推官高锡上书谏，','无乃失为政之本乎！”',[('高锡','劝柴荣任用合适官员、分职而治'),('帝','收到高锡的劝谏')],when='954年返朝后所记，具体上书日未载',place='后周朝廷',note='不信群臣、褊迫疑忌是高锡奏疏批评，不转为本站对柴荣心理的确定诊断。')
add('chairong_rejects_gaoxi','柴荣未采纳高锡劝分职治理的奏疏',8,'帝不从。','帝不从。',[('帝','未采纳高锡意见'),('高锡','上书未被采纳')],when='954年高锡上书后，具体日未载',place='后周朝廷')
claim('person',people['高锡'],'description','高锡时任河南府推官。',8,'河南府推官高锡上书谏，','职务由这句明确给出；籍贯由同段末句另引，不把河南府任职地当出生地。')
claim('person',people['高锡'],'description','高锡是河中人。',8,'锡，河中人也。','籍贯按原文，未补现代县名。')
add('liuchong_ill_entrusts_chengjun','刘崇忧愤患病，把国事交给儿子刘承钧',9,'北汉主忧愤成疾，',None,[('北汉主','患病后委国事于儿子'),('承钧','以侍卫都指挥使身份承办国事')],when='954年晋阳围城解除后、七月段落以前，具体日未载',place='北汉晋阳',note='委国事不等于刘崇已去世或刘承钧已即帝位，后续监国继位另见后段。')
relationship('刘崇（刘知远弟）','刘承钧','父亲',9,Q[9]['text'],'主书明确其子承钧，复用北汉既有父子主体与方向，不与萧县同名刘崇关联。')
add('shen_shihou_leaves_without_edict','申师厚未等诏命便擅离河西军，赴朝廷',10,'河西节度使申师厚','擅弃镇入朝，',[('申师厚','未经诏命离开河西军入朝')],when='954年七月癸酉朔处分以前',place='河西军凉州至后周朝廷')
sup('shen_shihou_leaves_without_edict',10,july,'師厚在涼州歲餘，以所部艱食，蕃情反覆，奏乞入朝，','《旧五代史》记申师厚在凉州一年多，因辖区食物困难、部族局势反复而奏请入朝。','保存史书陈述的离镇背景与先奏请过程；奏请不等于已获准，未按背景时长反推准确到任日。',relation='adds')
add('shen_installs_unnamed_son','申师厚离镇时自行任儿子为河西留后',10,'署其子','为留后。',[('申师厚','自行任儿子留守河西军')],when='954年七月处分以前离镇时',place='河西军凉州',note='儿子没有姓名，不建立具名人物，也不据署留后反推朝廷认可。')
add('shen_demoted_for_departure','后周把申师厚降为率府副率',10,'秋，七月，',None,[('申师厚','因擅离河西被降职'),('帝','处分擅离任所的申师厚')],when='954年七月癸酉朔',place='后周朝廷')
sup('shen_demoted_for_departure',10,july,'秋七月癸酉朔，前河西軍節度使申師厚責授右監門衛率府副率。','《旧五代史》同日记申师厚责授右监门卫率府副率。','补具体官职，与主书率府副率简称对应；未把降职写成处死。',relation='adds')
add('qianchu_grand_marshal','柴荣加钱弘俶天下兵马都元帅',11,'丁丑，',None,[('钱弘亻叔','获加天下兵马都元帅'),('帝','加授吴越王元帅号')],when='954年七月丁丑',place='后周朝廷、吴越',note='钱弘亻叔为电子底本拆分字形，复用钱弘俶并保留原引字，不新建同名王。')
sup('qianchu_grand_marshal',11,july,'丁丑，天下兵馬元帥、吳越國王錢俶加天下兵馬都元帥；','《旧五代史》同记钱俶由天下兵马元帅加为天下兵马都元帅。','补原先官号与加授差别，钱俶、弘俶同一已核主体。',relation='adds')
add('fanzhi_situ','柴荣加范质守司徒',12,'癸巳，','范质守司徒，',[('范质','在门下侍郎、同平章事上加守司徒'),('帝','加授范质守司徒')],when='954年七月癸巳',place='后周朝廷')
sup('fanzhi_situ',12,july,'以左僕射兼門下侍郎、平章事、監修國史範質為守司徒兼門下侍郎、平章事、宏文館大學士；','《旧五代史》补列范质加守司徒后兼门下侍郎、平章事及宏文馆大学士。','範与范为字形对应，保留各书记述的完整职务，不新造人物。',relation='adds')
add('jingfan_chancellor_finance','景范任中书侍郎、同平章事并判三司',12,'以枢密直学士、','判三司。',[('景范','由枢密直学士、工部侍郎转任宰相并掌三司')],when='954年七月癸巳',place='后周朝廷')
sup('jingfan_chancellor_finance',12,july,'以樞密院學士、工部侍郎景範為中書侍郎、平章事，判三司；','《旧五代史》同记景范的宰相与三司任命。','主书范、新旧本字形範相对应；枢密学士职名前缀详略保留。')
claim('person',people['景范'],'description','景范是长山人。',12,'长山景范','籍贯由主书明确给出，未用人物姓氏代替地名。')
add('zheng_renhui_shizhong','柴荣加郑仁诲兼侍中',12,'加枢密使、', '兼侍中。',[('郑仁诲','以枢密使、同平章事加兼侍中')],when='954年七月癸巳',place='后周朝廷')
sup('zheng_renhui_shizhong',12,july,'樞密使、檢校太保、同平章事鄭仁誨加兼侍中；','《旧五代史》同记郑仁诲加兼侍中，另列检校太保。','保留旧本纪所补职衔，不改变主体姓名。')
add('wei_renpu_chief_privy','柴荣任魏仁浦为枢密使',12,'乙未，','魏仁浦为枢密使。',[('魏仁浦','由枢密副使升任枢密使'),('帝','任命魏仁浦掌枢密院')],when='954年七月乙未',place='后周朝廷')
sup('wei_renpu_chief_privy',12,july,'乙未，以樞密副使、右監門衛大將軍魏仁浦為樞密使、檢校太保。','《旧五代史》同日记魏仁浦任枢密使，并加检校太保。','具体官号补证，未把职务晋升写成首次入仕。',relation='adds')
add('dou_zhengu_returns_luoyang','范质任司徒后，原司徒窦贞固回洛阳',12,'范质既为司徒，','司徒窦贞固归洛阳，',[('窦贞固','回洛阳'),('范质','此时已加守司徒')],when='954年七月范质任司徒之后',place='洛阳',note='未据此补正式罢官诏令或自称已全无旧职。')
add('dou_zhengu_assessed_levies','洛阳府县把窦贞固按普通百姓对待，照常征课役',12,'府县以民视之，','课役皆不免。',[('窦贞固','被府县照常征收课役')],when='954年回洛阳后',place='洛阳',note='只记原文待遇，不在没有具体法令证据时判定府县执法违法或司徒必获豁免。')
add('dou_appeals_xiang_xun','窦贞固向留守向训投诉被征课役，向训不理会',12,'贞固诉于留守向训，',None,[('窦贞固','向向训投诉课役待遇'),('向训','不接受窦贞固投诉')],when='954年窦贞固回洛阳受课役后',place='洛阳')
add('li_yanchong_guards_escape_route','高平之战时，柴荣命李彦崇守江猪岭截断刘崇退路',13,'初，帝与北汉主','遏北汉主归路。',[('帝','命李彦崇截守北汉退路'),('李彦崇','受命守江猪岭')],when='954年三月高平之战时的追述',place='江猪岭',note='初回述战前命令，不把守岭行动定在八月降职日。')
add('li_yanchong_retreat_allows_escape','李彦崇听到樊爱能等南逃便撤兵，刘崇经该路逃走',13,'彦崇闻樊爱能等','自其路遁去。',[('李彦崇','听闻南逃后撤守'),('北汉主','经李彦崇撤守的道路逃走')],when='954年三月高平战败逃归期间的追述',place='江猪岭',note='不把追述重新做成八月北汉第二次逃归；仅补守路失职经过。')
add('li_yanchong_demoted','柴荣因李彦崇高平撤守失职，将其贬为率府副率',13,'八月，',None,[('李彦崇','因高平撤守被降职'),('帝','处分李彦崇失职')],when='954年八月己酉',place='后周朝廷')
sup('li_yanchong_demoted',13,aug,'己酉，前澤州刺史李彥崇責授右司禦副率。高平之役，帝與賊軍相遇，即令彥崇領兵守江豬嶺，以遏寇之歸路，彥崇初見王師已卻，即時而退，及劉崇兵敗，果由茲嶺而遁，故有是責。','《旧五代史》也记李彦崇因撤离江猪岭，致刘崇从此逃归，在八月己酉降职。','主书只写率府副率，旧史补右司御；事因与处分的不同月份分开。')
reviews={6:'被俘、赐物询问、隐瞒与解释、被杀分开。王得中对家国结果的判断不是既成事实，老母匿名不造主体；死亡留甲辰原纪时，不换算公历。',7:'实际撤军主书乙巳与旧史六月癸卯朔并列，新史六月乙巳补上下文。药元福方阵殿后据宋史补证；焚粮不造单位，代州城陷不补桑珪已死。',8:'返程各站和谒陵分录；乙酉与旧史乙巳到潞州差异保存。破北汉指胜军非灭国，亲决概述不当单日诏令；高锡奏疏批评保留来源身份。',9:'刘崇病中委国事不等于死亡或儿子即位，父子关系复用已核北汉主体。',10:'申师厚奏请、擅离、署匿名儿子及七月处分分开；旧史困难原因保存为记述，不写成已获准离镇。',11:'钱弘亻叔拆字对应钱弘俶、钱俶，保原字并复用身份；加都元帅与原元帅区分。',12:'四项任命分别记录，景范长山籍贯明确；窦归洛阳、受课役、投诉与未受理分开，不补豁免法令或全部免官结论。',13:'三月守岭、撤守与刘崇逃路为追述，八月己酉处分为当前行动；旧史完整因果与具体官职分别补证。'}
assert not (P/'publication.json').exists()
for n in range(6,14):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(6,14)],next_paragraph=Q[14]['id'],next_volume=292,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷292原11—18行连续八段，从围晋阳末期至八月处分；各原文快照所含其余段落未计本批覆盖。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(6,14)],source_issues_review='撤军与到潞州纪日差异并列，钱弘俶拆分字形保留，景範与景范按同人同职对应；匿名儿子和老母不造姓名。纸本及异文待核。',plain_language_review='首次逐条检查人物、事件、角色、关系、日期、政务意见及事实说明。上书批评和当事人预判均注明性质；请求、擅离、授职、处分和死亡逐项区分，摘录保持底本原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
