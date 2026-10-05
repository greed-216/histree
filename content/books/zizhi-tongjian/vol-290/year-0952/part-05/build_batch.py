# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 952 paragraphs 33–37."""
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
COMMIT='b0deaf82eb531ea754c26437fed796ea476c451e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-952-june-july']:
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
main_sources = ['tongjian-290-952-june-july']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0952-p033-p037',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-112-august-952':'卷112·太祖本纪三·广顺二年八月'}
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
for n in range(33, 38):
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
    labels={'jiuwudaishi-112-august-952':'卷112·太祖本纪三·广顺二年八月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺二年（952年七月后卷末记事，月份承接另见校核说明）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0952_05_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=952, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='952年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0952_' + code
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
        edge = 'participation_zztj_290_0952_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0952_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','蜀主':'孟昶'})
NEW_ALIASES={'邵延钧':['邵延鈞'],'王承丕':[],'孙钦':['孫欽'],'赵季札':['趙季札']}
NEW_DESCRIPTIONS={'邵延钧':'后蜀工部尚书、判武德军。952年对监押王承丕不够礼敬，王承丕谋乱，命人杀邵延钧并屠其家。出生年未载，死亡年952年。','王承丕':'后蜀武德军监押。952年杀邵延钧，自称奉诏处置军府，开库赏兵、释放囚犯。孙钦发现他谋反后率兵捕杀，并将首级送往成都。出生年未载。','孙钦':'安次人，后蜀左奉圣都指挥使。952年原拟率部戍边，受王承丕邀入军府时不知道其谋乱。得知无诏后脱身，回营率兵捕杀王承丕。生卒年未载。','赵季札':'后蜀客省使。952年受孟昶之命赴梓州，慰抚吏民。生卒年未载。'}
NEW_DEATH_YEARS={'邵延钧':952,'王承丕':952}
old='jiuwudaishi-112-august-952'
add('li_gu_arm_injury_leave','李谷跌倒伤右臂，请假一个多月',33,'李谷足跌，','在告月馀。',[('李谷','跌倒伤右臂，因伤请假')],when='952年夏，旧五代史说明七月受伤，具体受伤日未载',place='后周',note='足跌指失足跌倒，受伤部位为右臂；主书请假月余，旧书记数旬。')
sup('li_gu_arm_injury_leave',33,old,'時穀以今年七月，因步履傷臂，請告數旬，','《旧五代史》说明李谷在当年七月跌倒伤臂、请假数旬。','此书把后续处置写于八月；主书本段承七月以后未另标八月，月序疑问保留。',relation='adds')
add('guo_calls_injured_li_gu','郭威因李谷事务繁重催其入朝，李谷表示还不能趋拜',33,'帝以谷职业繁剧，','辞以未任趋拜。',[('帝','催李谷入朝处理繁重事务'),('李谷','以尚不能趋拜为由辞行')],when='952年七月受伤一个多月以后，具体催召日未载',place='后周朝廷',note='职业在此为职务事务，不译成现代择业；未任趋拜不是已经辞官。')
add('guo_exempts_li_gu_audience','郭威免李谷朝参，仍让他办事',33,'癸巳，',None,[('帝','免除李谷朝参，但令其继续办事'),('李谷','获免朝参，继续视事')],when='952年癸巳，主书月序承接待核；旧五代史置八月',place='后周朝廷',note='免朝参不等于罢免职务；公元年明确，月份不凭原七月标题强定，保留补书记时。')
sup('guo_exempts_li_gu_audience',33,old,'詔穀扶持三司，刻名印署事，仍放朝參。','《旧五代史》记让李谷继续主持三司，刻姓名印章签署事务，免朝参。','印章用于签署公务，原文未列代签者。',relation='adds')
sup('guo_exempts_li_gu_audience',33,old,'賜宰臣李穀白藤肩輿。','《旧五代史》还记赐李谷白藤肩舆。','肩舆是人力抬行的乘坐工具。',relation='adds')
add('wang_chengpi_revolt_plan','王承丕因邵延钧不礼敬自己而谋乱',34,'蜀工部尚书、','承丕谋作乱。',[('邵延钧','被史书记为不礼敬监押王承丕'),('王承丕','谋划作乱')],when='952年辛丑军府事件以前，具体谋划日未载',place='武德军军府',note='不礼与谋乱关系是本书记载，未扩写具体羞辱言辞或长期党派。')
add('sun_qin_unaware_meeting','孙钦准备率部戍边，受王承丕邀同访邵延钧，尚不知道谋乱',34,'辛丑，','钦不知其谋，从之。',[('孙钦','赴王承丕处辞行，不知其谋而随同访府公'),('王承丕','邀请孙钦一同见府公')],when='952年辛丑，主书未另标本段月份，月序待核',place='武德军军府',note='孙钦原定戍边，不写成已到边地；府公承邵延钧，不另建一名府公人物。')
claim('person',people['孙钦'],'description','孙钦是安次人，任左奉圣都指挥使。',34,'左奉圣都指挥使安次孙钦当以部兵戍边，','籍贯与官职来自本句，未自行给现代坐标。')
add('wang_chengpi_kills_shao','王承丕命左右杀死邵延钧，并屠杀其家人',34,'承丕至，','屠其家，',[('王承丕','命左右杀邵延钧及其家人'),('邵延钧','在军府被杀')],when='952年辛丑',place='武德军军府',note='执行者和被害家属的姓名、人数未载。')
add('wang_claims_imperial_order','王承丕声称奉诏处置军府，开库赏兵、放囚犯并调动戍兵',34,'称奉诏处置军府，','发屯戍。',[('王承丕','声称奉诏，并开库赏兵、放囚、调动戍兵')],when='952年辛丑杀邵延钧以后',place='武德军军府',note='奉诏是王承丕的说法，后文不能出示诏书，不认定孟昶真的命其杀人。')
add('sun_qin_demands_edict','孙钦要求王承丕出示诏书，王承丕只许富贵、不答诏书',34,'将吏毕集，','勿问诏书。”',[('孙钦','要求出示诏书以示众'),('王承丕','许诺使孙钦富贵，拒绝说明诏书')],when='952年辛丑军府将吏聚集时',place='武德军军府',note='已伏辜为孙钦尚未识破时的讲话，不作本站对邵延钧有罪的认定。')
add('sun_qin_escapes_rebels','孙钦看出王承丕反叛，以巡察为由离府，拒绝其呼唤',34,'钦始知承丕反，','承丕连呼之，不止。',[('孙钦','识破后以巡察为由脱身'),('王承丕','呼唤孙钦，未能阻止他离开')],when='952年辛丑',place='武德军军府至军营',note='巡察是脱身说辞，不当作已经服从王承丕命令巡察城防。')
add('sun_qin_counterattacks','孙钦回营告知部众，率兵入府攻王承丕，使其左右弃械逃走',34,'钦至营，','皆弃兵走，',[('孙钦','告知部众，率兵反攻并喝止王承丕左右'),('王承丕','遭孙钦反攻')],when='952年辛丑',place='军营至武德军军府',note='原文未给部众人数，逃走者未具名。')
add('sun_qin_executes_wang','孙钦捕杀王承丕及其亲党，将首级送成都',34,'遂执承丕，',None,[('孙钦','捕杀王承丕并把首级送成都'),('王承丕','被捕后被斩')],when='952年辛丑军府反攻后，具体首级抵达日未载',place='武德军军府至成都',note='被诛亲属、党羽的姓名和人数未载。')
add('gao_xingzhou_dies','天平节度使高行周去世',35,'天平节度使、','高行周卒。',[('高行周','以天平节度使、守中书令身份去世')],when='952年，主书本句未列卒日；旧五代史记八月壬寅',place='天平军',note='爵职不是死亡地点的独立证据，原书未单列地点。')
sup('gao_xingzhou_dies',35,old,'壬寅，鄆州節度使高行周薨。','《旧五代史》八月壬寅记高行周去世。','郓州与天平军称谓分别保留，死亡年月日由独立补书记载。',relation='adds')
claim('person',people['高行周'],'death_year','高行周在952年去世，《旧五代史》记八月壬寅。',35,'天平节度使、守中书令高行周卒。','沿此前梁晋汉周同一高行周主体，不因军镇变动重建人物。')
add('gao_xingzhou_character_assessment','史书评价高行周勇而知义、有功不自夸，平时待宾僚和易',35,'行周有勇而知义，',None,[('高行周','被史书评价为有勇有义、临敌威严、平日和易')],year=None,when='高行周生前一段时期的综合评价，具体起止年月未载',place='高行周军镇与军中',note='战场形象与平居待客是史家概述，不编造952年死后他仍活动的事件。')
add('zhao_jizha_reassures_zizhou','孟昶派赵季札到梓州慰抚吏民',36,'癸卯，',None,[('蜀主','派客省使慰抚梓州吏民'),('赵季札','以客省使身份赴梓州慰抚')],when='952年癸卯，主书卷末未另标月份，月序待核',place='成都至梓州',note='与前文军府事件相邻，但本句未明示他参与捕王承丕，不添军事行动。')
add('han_private_salt_yeast_death_law','后汉旧法对私盐、酒曲犯罪不论数量都处死',37,'汉法，','无问多少抵死。',[],year=None,when='后汉时期旧法的追述，具体制定日未载',place='后汉',note='麹为酿酒用曲，不译成所有面粉或普通谷物；旧法与952年新诏分录。')
add('zhengzhou_salt_case','郑州百姓从官府所得盐被当私盐，遭处死，其妻申冤',37,'郑州民有','其妻讼冤。',[],when='952年癸丑新诏以前，具体案发与申冤日未载',place='郑州',description='郑州一名百姓以房屋相关收入折得官府给付的盐，经过州城时被官吏认作私盐并杀死，妻子为他申冤。',note='原文称以屋税受盐于官，房屋租税的具体制度未展开，未写成现代房产税；官盐来源与吏认为私盐分清，夫妻都未具名，不造姓名。')
add('guo_salt_yeast_penalties_by_weight','郭威按盐、酒曲的斤两分别规定刑罚',37,'癸丑，',None,[('帝','改按盐曲数量规定轻重不同刑罚')],when='952年癸丑；旧五代史置八月，主书月序承接待核',place='后周',note='本句没有列所有刑级，不编造少量必然无罪、具体徒刑年限。')
sup('guo_salt_yeast_penalties_by_weight',37,old,'癸丑，詔改鹽曲法，鹽曲犯五斤已上處死，煎鹼鹽者犯一斤已上處死。','《旧五代史》八月癸丑补记盐曲犯五斤以上处死、煎碱盐者犯一斤以上处死。','门槛按该书原文保留，麹与曲字形对应，未给本条未列的其他刑档补具体年限。',relation='adds')
reviews={33:'李谷七月伤臂旧书明确，免朝参而继续办事不当罢职。主癸巳月序未单列八月，旧在八月记署印与肩舆；月份疑问公开保留，不自行换公历。',34:'邵不礼与王谋、孙不知邀见、王杀邵家、自称诏赏库放囚、问诏、孙识破脱身回营反攻、捕斩送首逐项录。孙初未参与谋乱，伏辜是其当时话语，未当邵确犯罪；无名左右亲党家属不造名单。',35:'主高行周死未单列日，旧八月壬寅补；性格战勇与宴集为生前概述不系死年具体行为。',36:'癸卯赵慰抚梓州，未明参战不加武功；月序待核不强七月。',37:'旧汉盐曲法、官给盐被误处与妻申冤、癸丑斤量新法分开。屋税具体制度未明，展示只说明房屋收入折官盐，不改成现代房产税；旧八月及五斤一斤门槛独立补，原未给其他刑档不补。'}
assert not (P/'publication.json').exists()
for n in range(33,38):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,38)],next_paragraph='zztj-v291-y0952-p001',next_volume=291,next_year=952,supplements=supplements,excluded_non_body=[],coverage='卷290原122—126行连续五段；本卷952年正文结束，须继续卷291同年九月以后25段，本年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,38)],source_issues_review='逐字原文保持底本，纸本未核。主书秋七月后未单列八月，干支承接及旧八月条需另作版本校读，本批年明确而月份并列待核。屋税制度不擅改，武德军及监押等官称按原书；假称诏令与真实命令分清。',plain_language_review='首次检查标题、人物、事件、角色、日期和引用说明，引用外用白话。误认与真实来源、奉诏说法与不出诏、受邀无知与识破反攻、免朝与免职、旧法与新令分别表述。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
