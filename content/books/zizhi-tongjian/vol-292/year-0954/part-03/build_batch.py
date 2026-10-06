# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 954 paragraphs 14–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,25))
COMMIT='f810d30ec35101c5176a9eb422396fe0a243cd24'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-954-summer-autumn','jiuwudaishi-114-august-li-yanchong','xinwudaishi-12-chairong-accession']:
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
main_sources = ['tongjian-292-954-summer-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0954-p014-p020',
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
for n in range(14, 21):
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
        citation = f'卷292·显德元年（954年八月至十一月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0954_03_{len(B["claims"])+1:04d}'
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










ALIASES.update({'帝':'柴荣','上':'柴荣','太祖':'郭威','太祖皇帝':'赵匡胤'})
NEW_ALIASES={'孟汉卿':['孟漢卿']}
NEW_DESCRIPTIONS={'孟汉卿':'后周左羽林大将军。954年十月甲辰因监督收纳草税时场官扰民、多取耗余，被柴荣赐死。有司认为罪不至死，柴荣表示是为了警戒众人。《旧五代史》同记其监纳多取耗余获罪，生年未载。'}
NEW_DEATH_YEARS={'孟汉卿':954}
aug='jiuwudaishi-114-august-li-yanchong';october='jiuwudaishi-114-october-reform';nov='jiuwudaishi-114-november-riverwork';new='xinwudaishi-12-chairong-accession'
add('zhenguo_military_district_removed','柴荣撤销镇国军建制',14,'己巳，',None,[('帝','撤销镇国军建制')],when='954年八月己巳',place='镇国军华州',note='撤销军额不等于毁掉城池或杀尽军人；旧本纪补依旧为郡。')
sup('zhenguo_military_district_removed',14,aug,'己巳，宜停華州鎮國軍，依舊為郡。','《旧五代史》同记八月己巳停华州镇国军、依旧为郡。','补所在地与撤销军额后的行政表述，不推全城废弃。',relation='adds')
add('wangyan_wuning_background','郭威因王晏守晋州有功，把他调到乡里附近的武宁军',15,'初，太祖以建雄节度使王晏','徙晏为武宁节度使。',[('太祖','因王晏拒北汉有功而调镇徐州'),('王晏','从建雄军调往徐州武宁军')],year=951,when='951年八月壬子，复用此前已录调镇事件，954年本条补记理由',place='建雄军至徐州',stable_key='event_zztj_290_0951_wang_yan_xuzhou',note='初追述对应已发布951年调镇事件，不另建954年调任；现在补功劳与乡里理由。')
claim('person',people['王晏'],'description','《通鉴》把王晏乡里与滕县相联系，并记他年轻时曾参与盗匪活动。',15,span(15,'其乡里有滕县，','晏少时尝为群盗，'),'底本写其乡里有滕县，字句疑有转录问题；保留与滕县的联系，出生地点未作精确判定。早年经历不定在954年。')
add('wangyan_gifts_former_companions','王晏到徐州后召集旧日同伙，赠金帛鞍马',15,'至镇，','赠之金帛、鞍马，',[('王晏','召集早年同伙并赠财物')],year=None,when='951年调镇徐州以后、954年九月立碑请求以前，具体日未载',place='徐州',note='召集及赠物是到镇后旧事，不强定为954年九月。')
add('wangyan_warns_against_banditry','王晏要求旧同伙劝止乡里盗匪，以族诛威胁再犯者',15,'谓曰：“吾乡素名多盗，','为者吾必族之。”',[('王晏','要求旧同伙劝止盗匪，并威胁族诛再犯者')],year=None,when='王晏到徐州召集故党时，具体年份未载',place='徐州、滕县一带',note='族诛在此是王晏的威胁，原文未列实际被族诛的人，不新造处刑事件。')
claim('event',E['wangyan_warns_against_banditry'],'description','《通鉴》说王晏劝止盗匪后，境内变得清肃。',15,'于是一境清肃。','这是史书对施政效果的概述，不外推徐州以后再无犯罪。')
add('xuzhou_requests_honor_stele','徐州人请为王晏立衣锦碑，朝廷准许',15,'九月，',None,[('王晏','徐州人请求为其立碑，得到许可'),('帝','准许徐州人立碑请求')],when='954年九月',place='徐州',note='请立与获准明确，主书未说碑已建成，不录竣工。')
add('meng_hanqing_sentenced_to_death','孟汉卿因场官多收草税耗余、扰民被赐死',16,'冬，十月，','赐死。',[('孟汉卿','因草税收纳失当被赐死'),('帝','赐死孟汉卿')],when='954年十月甲辰',place='后周',note='监纳责任与场官具体扰民行为分开，不补孟汉卿亲自侵吞多少税粮。')
sup('meng_hanqing_sentenced_to_death',16,october,'冬十月甲辰，左羽林大將軍孟漢卿賜死，坐監納厚取耗餘也。','《旧五代史》同日记孟汉卿因监督收纳时多取耗余被赐死。','只印证罪由与赐死，未给财物数量或具体执行方式。')
sup('meng_hanqing_sentenced_to_death',16,new,'冬十月甲辰，殺左羽林大將軍孟漢卿。','《新五代史》同记十月甲辰杀孟汉卿。','本纪简文未解释罪由，不据省略认为他无罪。')
add('officials_object_meng_penalty','有司奏称孟汉卿罪不至死，柴荣表示要警戒众人',16,'有司奏汉卿罪不至死。',None,[('帝','承认处罚意在惩戒众人'),('孟汉卿','有司认为其罪不应处死')],when='954年十月甲辰孟汉卿赐死记载后',place='后周朝廷',note='保留有司量刑意见与柴荣回答，不自行判定适用律条；主书先述赐死后述奏答，不擅改为已获改判。')
add('anyuan_yongqing_removed','柴荣撤销安远、永清二军建制',17,'己酉，',None,[('帝','撤销安远和永清军额')],when='954年十月己酉',place='安远军、永清军')
sup('anyuan_yongqing_removed',17,october,'詔安、貝二州依舊為防禦州，其軍額並停。','《旧五代史》补记安州、贝州依旧为防御州，两州军额停止。','旧文把军额停置接在己酉之后，未将防御州调整写成撤除州城。',relation='adds')
claim('person',people['柴荣'],'evaluation','《通鉴》认为历朝姑息宿卫、不愿检阅，导致老弱居多、临敌逃降；柴荣在高平之战后看到这些弊病。',18,span(18,'初，宿卫之士，','始知其弊。'),'这是主书对制度积弊及其影响的概述，不把所有宿卫一概标成逃兵或把历朝失国写成单一原因。')
add('chairong_advocates_quality_army','柴荣提出兵贵精不贵多，批评养无用兵耗费民力',18,'癸亥，','且健懦不分，众何所劝！”',[('帝','阐述精兵与军费主张')],when='954年十月癸亥',place='后周朝廷',note='百名农夫难养一甲士是柴荣论述的负担说法，不当作全社会已统计的精确供养比例。')
add('chairong_orders_troop_selection','柴荣下令大规模检选军队，精锐升上军，弱者淘汰',18,'乃命大简诸军，','羸者斥去之。',[('帝','下令检选并调整军队')],when='954年十月癸亥言论后',place='后周诸军',note='淘汰老弱不是处死老弱军人，原文未给被淘汰人数。')
sup('chairong_orders_troop_selection',18,october,'己未，供奉官郝光庭棄市，坐在葉縣巡檢日，挾私斷殺平人也。是日大閱，帝親臨之。','《旧五代史》把柴荣亲临大阅记在十月己未。','旧本纪己未大阅与主书癸亥整训论说的纪日不同，保留不同阶段和日期；郝光庭案为日期上下文，不把它作为主书整训原因。',relation='conflicts',field='time_original')
sup('chairong_orders_troop_selection',18,october,'復命總戎者，自龍捷、虎捷以降，一一選之，老弱羸小者去之，諸軍士伍，無不精當。','《旧五代史》同记各军自龙捷、虎捷起逐一选择，去除老弱羸小。','保留实际选择规则，不补逐军具体名额。')
add('chairong_recruits_brave_men','柴荣诏募天下壮士入京，争取原被藩镇收用的勇士',18,'又以骁勇之士多为诸籓镇所蓄，','咸遣诣阙，',[('帝','诏募各地勇士前来京师')],when='954年十月整训期间',place='各地至后周京师',note='多为藩镇所蓄是主书所述背景，不指所有藩镇都已全部交出勇士。')
add('zhao_selects_palace_units','柴荣命赵匡胤选优秀壮士组成殿前诸班',18,'命太祖皇帝选其尤者','为殿前诸班，',[('帝','委赵匡胤选择殿前诸班'),('太祖皇帝','挑选优秀壮士进入殿前诸班')],when='954年十月整训期间',place='后周京师',note='太祖皇帝在本句是宋太祖赵匡胤，不是已经去世的后周郭威；殿前诸班的名称沿史载，不改成近代军种。')
sup('zhao_selects_palace_units',18,october,'至是命今上一概簡閱，選武藝超絕者，署為殿前諸班，因是有散員、散指揮使、內殿直、散都頭、鐵騎、控鶴之號。','《旧五代史》也记赵匡胤简阅武艺出众者、署为殿前诸班，并列有关军职与班直名称。','宋代修史所称今上指赵匡胤，结合主书同役确认；原文列的是多种名称，不全解释成独立人数相同的军队。',relation='adds')
add('commanders_select_cavalry_infantry','柴荣命各军将帅检选骑兵、步兵',18,'其骑步诸军，','各命将帅选之。',[('帝','命各军将帅选择骑步军士')],when='954年十月整训期间',place='后周各军')
claim('event',E['chairong_orders_troop_selection'],'description','《通鉴》认为整训使士卒强健，并把后续对外获胜归功于选练。',18,'由是士卒精强，近代无比，征伐四方，所向皆捷，选练之力也。','这是作者回顾后续结果的评价，不把所有后续战役获胜都定在954年十月。')
add('chairong_proposes_local_policing','柴荣提出召回中央巡检使，让节镇、州县负责治盗',19,'戊辰，',None,[('帝','提出召回巡检使并责成地方治盗')],when='954年十月戊辰',place='后周朝廷及地方节镇州县',note='引文是柴荣对侍臣提出的安排，主书此处未另列各使实际返京的执行记录，不写成所有巡检使已返京。')
add('river_breaks_eastward','黄河在杨刘至博州一带连年向东决口，汇成大片水泽',20,'河自杨刘','弥漫数百里。',[],year=None,when='954年十一月修堤以前持续数年的河患，起始年未载',place='杨刘至博州一带',note='百二十里、数百里为史载长度和范围，不转换成核定现代淹没边界。')
add('river_inundates_qi_di_zi','黄河冲破东北古堤，淹齐棣淄等州，毁田宅并使流民捕鱼采草籽求生',20,'又东北坏古堤而出，','捕鱼以给食，',[],year=None,when='954年十一月治河以前的连年水患，具体年未载',place='齐、棣、淄诸州至海滨',note='不可胜计未给灾损总数；菰稗指原文记载的采食对象，不简化成所有人只吃树皮。')
add('earlier_river_repairs_fail','朝廷此前屡派使者堵河，未能成功',20,'朝廷屡遣使者','不能塞。',[],year=None,when='954年十一月李谷治河以前，具体次数和年份未载',place='黄河决口一带',note='史书没有逐次使者名单，不新造姓名，也不把此概述的全程都设为柴荣本人执政期间。')
add('ligu_inspects_river_dikes','柴荣派李谷赴澶郓齐察看堤防与堵口工程',20,'十一月，戊戌，','按视堤塞，',[('帝','派李谷查办河堤'),('李谷','到澶郓齐察看堤防及堵口')],when='954年十一月戊戌',place='澶、郓、齐',note='遣与按视是任命任务及工程巡视，不把此句当作同日已经完成全部修堤。')
sup('ligu_inspects_river_dikes',20,nov,'戊戌，詔宰臣李穀監築河堤。先是，鄆州界河決，數州之地洪流為患，故命穀治之。','《旧五代史》同记十一月戊戌诏李谷监筑河堤，并说明郓州河决引发数州水患。','具体任命与背景同史对照，不把先是河决硬定为戊戌当天。')
add('ligu_completes_riverwork','李谷治河征发六万人，三十日后完成',20,'役徒六万，',None,[('李谷','监督六万人修堤，三十日完成')],when='954年十一月戊戌派遣后，原文记三十日完成，可能跨月',place='黄河决口堤防',note='持续三十日不等于十一月戊戌当天完成，不自行计算公历完工日。')
sup('ligu_completes_riverwork',20,nov,'役丁夫六萬人，三十日而罷。','《旧五代史》同记征发丁夫六万人，三十日后结束役作。','原书毕与罢的表述差别分别保留，不补工程技术细节或堤长。')
reviews={14:'军额撤销与州城废弃区分，旧本纪补华州依旧为郡。',15:'调镇复用951年已有事件，初回述不造954年调任。赠旧党与威胁止盗用未知年，族诛仅是话语威胁；九月请碑获准不等于已经建成。',16:'孟汉卿草税监纳责任与场官扰民分开；有司量刑意见、柴荣惩众答语分别保存，不补收受财物数量或行刑方式。',17:'安远永清军额停撤，与安贝二州仍为防御州的旧史记述对应，未说州城被废。',18:'整训背景是回顾评价，百农夫养一兵是皇帝说法，非统计比率。具体淘汰、招募、赵匡胤择殿班与各帅检选分录，原癸亥与旧己未不同日期并列。',19:'召回巡检是对侍臣提出的治理安排，未造所有使臣返京的实际执行记录。',20:'连年河患、民田受灾及先前堵口失败是旧事概述，起始年未载；李谷戊戌任命与六万人三十日完工分开，未强改为同日完成。'}
assert not (P/'publication.json').exists()
for n in range(14,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(14,21)],next_paragraph=Q[21]['id'],next_volume=292,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷292原19—25行连续七段；原30行帝号题名另在结构纠正记录中保留，不计本年正文。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(14,21)],source_issues_review='军队整训纪日癸亥与旧本纪己未并列；旧史今上与主书太祖皇帝均按同役识别为赵匡胤。王晏调镇复用旧事件，旧河患起始年不明。结构题名纠正不改原文。纸本待核。',plain_language_review='首次逐条检查标题、人物、角色、时间及事实说明；帝郭威与帝柴荣、宋太祖赵匡胤按各句身份明确。威胁、量刑意见、提议、任命及实际完工分开，原文保持字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
