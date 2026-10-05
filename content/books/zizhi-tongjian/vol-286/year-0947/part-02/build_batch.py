# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 4–9."""
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
COMMIT='d4c559b31fae71400d51ba9fe66160d5967ce6ca'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-capital-entry','liaoshi-004-947-january','xinwudaishi-029-jing-capture']:
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
main_sources = ['tongjian-286-947-capital-entry']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p004-p009',
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
for n in range(4, 10):
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
        citation = f'卷286·天福十二年（947年正月）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_02_{len(B["claims"])+1:04d}'
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
ALIASES.update({'晋主':'石重贵','契丹主':'耶律德光','李太后':'永宁公主（石敬瑭妻）','太后':'永宁公主（石敬瑭妻）','杨承勋':'杨承贵','承信':'杨承信','杨光远':'杨檀','傅住兒':'傅住儿','道':'冯道','崧':'李崧','建瑭':'史建瑭'})
NEW_ALIASES={'崔廷勋':['崔廷勛'],'史匡威':[]}
NEW_DESCRIPTIONS={'崔廷勋':'河内人。947年正月《资治通鉴》称他为大同节度使兼侍中，耶律德光派他率兵看守迁到封禅寺的石重贵及家人。《旧五代史》称为蕃大将崔廷勋，未另建同名人；生卒年未载。','史匡威':'史建瑭的儿子。947年契丹进入大梁后，以彰义节度使身份据守泾州，拒绝服从契丹命令。生卒年未载。'}
t='947年正月';j='jiuwudaishi-085-947-january';ls='liaoshi-004-947-january';jg='xinwudaishi-029-jing-capture'
add('yang_chengxun_executed','杨承勋被带到大梁，耶律德光以杀父和背叛契丹为由命人杀死他',4,'戊子，','脔食之。',[('杨承勋','以郑州防御使身份被捕处死'),('契丹主','以杀父和叛契丹指责杨承勋，命人处死')],when=t+'戊子',place='大梁',note='杨承勋初名杨承贵已在944年传记校核，复用稳定主体。杀父是契丹主指责，不能覆盖944年李守贞命都将杀杨光远的记载。脔食是肢解并食肉，不扩写具体参与者姓名。')
sup('yang_chengxun_executed',4,j,'戊子，殺鄭州防禦使楊承勛，責以背父之罪，令左右臠割而死。','《旧五代史》同记戊子处死郑州防御使杨承勋，责他背父。','两书责辞和死状不完全相同，各按原文保留，不把责辞当唯一已证动机。')
sup('yang_chengxun_executed',4,ls,'殺秦繼旻、李彥紳及鄭州防禦使楊承勛','《辽史》戊子条也记录杀杨承勋。','此处仅补同一死亡，不提前录主书后段秦继旻李彦绅死亡。')
claim('person','person_杨承贵','death_year','杨承勋（原名杨承贵）在947年正月戊子被耶律德光命人杀死。',4,span(4,'戊子，','脔食之。'),'旧身份名沿用稳定主体，死亡年月依据本句，不更改既有档案。')
add('yang_chengxin_receives_pinglu','耶律德光不久任命杨承信为平卢节度使，把其父旧兵交给他',4,'未几，',None,[('契丹主','任杨承信为平卢节度使，交付杨光远旧兵'),('承信','由右羽林将军出任平卢节度使')],when=t+'戊子之后不久，具体日未载',place='平卢军',note='未几不与戊子处死日强合；悉为父亲旧兵而非全国军队，未给确切数目。')
relationship('杨承勋','承信','兄长',4,span(4,'未几，','平卢节度使，'),'原文明杨承信为杨承勋弟弟，方向是兄长指向弟弟；复用已校核杨承贵主体。')
add('gao_accuses_zhang_khitan_detains','高勋向耶律德光控告张彦泽杀其家人，张和傅住儿被一同锁押',5,'高勋诉','锁之。',[('高勋','控告张彦泽杀家人'),('契丹主','因杀害和劫掠问题锁押二人'),('张彦泽','被控告并遭锁押'),('傅住兒','一同被锁押')],when=t+'己丑处死前，具体日未载',place='大梁',note='杀家人为前批事件，不重复建事件；本句未具载傅的具体劫掠行为，不能推两人每罪均同。')
add('officials_people_seek_zhang_death','耶律德光向百官公布张彦泽罪状并问是否当死，官员赞同，百姓也递状控告',5,'以彦泽之罪','彦泽罪。',[('契丹主','公布罪状并询问是否当死'),('张彦泽','成为百官和民众控告对象')],when=t+'己丑前',place='大梁',note='官员和百姓集体未列名，不补每人的身份；死亡意见不是尚已执行。')
add('zhang_fu_executed_north_market','张彦泽、傅住儿在北市被处死，高勋奉命监刑',5,'己丑，','高勋监刑。',[('契丹主','下令处决并命高勋监刑'),('张彦泽','在北市被处死'),('傅住兒','在北市被处死'),('高勋','奉命监督行刑')],when=t+'己丑',place='大梁北市')
sup('zhang_fu_executed_north_market',5,j,'己丑，斬張彥澤於市，以其剽劫京城，恣行屠害也。','《旧五代史》同记己丑在市中斩张彦泽，以劫掠和肆意杀害为由。','该句未写傅住儿，不据省略否定主书所载二人同死。')
sup('zhang_fu_executed_north_market',5,ls,'己丑，以張彥澤擅徙重貴開封，殺桑維翰，縱兵大掠，不道，斬於市。','《辽史》另列擅迁皇帝、杀桑维翰和纵兵劫掠等处死理由。','保留各书列举，不把张的每项行为均归于傅住儿。',relation='adds')
for name in ['张彦泽','傅住儿']:
 claim('person','person_'+name,'death_year',name+'在947年正月己丑于大梁北市被处死。',5,span(5,'己丑，','高勋监刑。'),'本段死亡明确；已发布档案不由本批直接覆写。')
add('victims_families_strike_zhang','张彦泽此前所杀士大夫的子孙穿丧服持杖哭骂，跟随并击打他',5,'彦泽前所杀','扑之。',[('张彦泽','被受害者家属哭骂并以杖击打')],when=t+'己丑行刑时',place='大梁北市及赴刑路线',note='家属未列具体姓名，不补人物名单。绖杖为服丧，未推每人具体亲等。')
add('gao_crowd_mutilate_zhang','高勋命割腕出锁、剖心祭死者，市民又损毁张彦泽遗体并争食',5,'勋命',None,[('高勋','命割腕解锁、剖心祭死者'),('张彦泽','遗体受到报复性毁损')],when=t+'己丑处死前后条下',place='大梁北市',note='原文紧接行刑，割腕具体在断头前后未再定时。保留记载性质，不能认为全体市民都参与。')
add('jing_suicide_chenqiao','景延广被送往契丹，在陈桥住宿时趁看守松懈自杀',6,'契丹送',None,[('景延广','被押送，夜间趁守卫松懈自杀')],when=t+'庚寅夜',place='陈桥',note='扼吭是扼住喉颈致死，不写未经记载的器具；既有封丘锁押之后的独立死亡。')
sup('jing_suicide_chenqiao',6,j,'庚寅，洛京留守景延廣自扼吭而死。','《旧五代史》也记庚寅景延广自杀。','死亡日一致；洛京留守为当时官名，不另创任命事件。')
sup('jing_suicide_chenqiao',6,jg,'至陳橋，止民家。夜分，延廣伺守者殆，引手扼吭而死，時年五十六。','《新五代史》补充住在陈桥民家，夜半趁看守松懈自杀，时年五十六。','传记未给庚寅，以主书记日另列；年龄不反算出生年。',relation='adds')
claim('person','person_景延广','death_year','景延广在947年正月庚寅夜于陈桥自杀。',6,Q[6]['text'],'年份、日、地点按通鉴本句，原文保持。')
add('shi_reduced_fuyi_huanglong','契丹封石重贵为负义侯，命安置黄龙府',7,'辛卯，','即慕容氏和龙城也。',[('契丹主','降低石重贵地位，命安置黄龙府'),('晋主','被封负义侯并指定安置处')],when=t+'辛卯',place='大梁至黄龙府（指定安置地）',note='这是封号和安置决定，实际北迁在后段，不写辛卯已经抵达。黄龙府地理说明是史家说法，未经坐标验证。')
sup('shi_reduced_fuyi_huanglong',7,j,'辛卯，契丹制，降帝為光祿大夫、檢校太尉，封負義侯，黃龍府安置。','《旧五代史》补充降为光禄大夫、检校太尉，并同记负义侯和黄龙府安置。','旧光禄、辽崇禄字不同，各按来源记录，不强改原字。',relation='adds')
sup('shi_reduced_fuyi_huanglong',7,ls,'辛卯，降重貴為崇祿大夫、檢校太尉，封負義侯。','《辽史》记崇禄大夫、检校太尉及负义侯，官名与旧史光禄大夫不同。','官衔字形差异保留，未据自动繁简转换合并。',relation='conflicts')
add('li_taihou_insists_follow_son','耶律德光准许李太后自行选择去处，她表示愿随石重贵同行',7,'契丹主使谓','欲何所归！”',[('契丹主','让使者转告太后可另选去处'),('李太后','称石重贵侍奉谨慎，坚持随行'),('晋主','太后坚持同行的儿子')],when=t+'辛卯条下，具体日未载',place='大梁',note='不用母命是耶律德光传话，违先君志为太后解释，不当全部亡国因果已证。')
add('shi_family_moved_fengchan_guarded','石重贵及家人被迁到封禅寺，崔廷勋率兵看守',7,'癸巳，','以兵守之。',[('契丹主','命迁帝家并派兵看守'),('晋主','与家人被迁寺中'),('崔廷勋','以大同节度使兼侍中身份率兵看守')],when=t+'癸巳',place='封禅寺')
sup('shi_family_moved_fengchan_guarded',7,j,'癸巳，遷帝於封禪寺，遣蕃大將崔廷勛將兵守之。','《旧五代史》同记癸巳迁帝至封禅寺，崔廷勋率兵监守。','蕃大将与通鉴具体官衔并存，不另建同名将领。')
add('shi_family_fears_visits_hungry_cold','耶律德光多次派人慰问，石重贵全家忧惧；连日雨雪且无人供应，众人受冻挨饿',7,'契丹主数遣','上下冻馁。',[('契丹主','多次派使者慰问'),('晋主','全家恐惧使者到来并受冻挨饿')],when=t+'癸巳迁寺后，连旬雨雪',place='封禅寺',note='存问是问候，举家恐惧为史书所述反应，未补每次慰问的具体威胁；连旬不强定起日。')
add('li_taihou_requests_food_monks_refuse','李太后请求寺僧供食，僧人以不敢揣测契丹意图为由拒绝',7,'太后使人','不敢献食。”',[('李太后','向寺僧请求供食')],when=t+'迁寺受困时',place='封禅寺',note='曾饭僧数万是太后在请求中自述前事，不在947年重建一次饭僧事件。僧人未具名。')
add('shi_pleads_guard_gets_food','石重贵暗中请求看守者，才得到少量食物',7,'晋主阴祈',None,[('晋主','私下请求看守者以求食物')],when=t+'迁寺受困时',place='封禅寺',note='稍得食不推已经解除饥寒；守者未具名，不强指崔本人递食。')
add('khitan_reenters_palace_guards_gates','耶律德光从赤冈率兵再入宫，契丹士兵昼夜守卫都城和宫禁各门',8,'是日，','不释兵仗。',[('契丹主','率兵再入宫并部署守门')],when=t+'癸巳（承前段是日）',place='赤冈至大梁宫城',note='再入宫与朔日首次入京分开，不创建两次首次占领。')
add('khitan_ritual_dog_sheepskin','契丹方面在门前杀犬、庭中挂羊皮以举行厌胜仪式',8,'磔犬','为厌胜。',[],when=t+'癸巳条下',place='大梁宫门与庭院',note='原文未给行礼者名，不强加耶律德光本人操刀；厌胜为仪式用途，不认可其效力。')
add('khitan_promises_lower_burdens','耶律德光向晋臣宣称停止整备军械和买马、减轻赋役即可太平',8,'契丹主谓','天下太平矣。”',[('契丹主','向晋臣提出停止军备、减轻赋役的说法')],when=t+'癸巳条下',place='大梁宫廷',note='这是言论，不能当全国军备已经停止或天下已太平。')
add('kaifeng_downgraded_bianzhou','契丹取消东京之号，把开封府降为汴州，并把府尹改为防御使',8,'废东京，','防御使。',[],when=t+'癸巳条下',place='开封府（改为汴州）',note='只记制度地位变化，未指谁被任为防御使，不据此替刘密另造任命。')
add('khitan_changes_chinese_attire_rites','耶律德光改穿中原衣冠，百官朝见起居沿用旧制',8,'乙未，','旧制。',[('契丹主','改穿中原衣冠并沿旧朝仪')],when=t+'乙未',place='大梁宫廷',note='中国为原文地域礼制用语，展示使用中原，不推改变族属或所有制度。')
add('zhao_zhang_recommend_li_song','赵延寿、张砺一同向耶律德光推荐李崧的才能',8,'赵延寿、','之才。',[('赵延寿','推荐李崧'),('张砺','共同推荐李崧'),('李崧','受到推荐')],when=t+'乙未后条下，具体日未载',place='大梁朝廷')
add('feng_dao_arrives_respected','冯道从邓州入朝，耶律德光敬重冯道、李崧',8,'会威胜节度使','礼重之。',[('冯道','以威胜节度使身份从邓州入朝'),('契丹主','礼遇冯道和李崧'),('李崧','与冯道同受礼遇')],when=t+'具体日未载',place='邓州至大梁',note='会表示相逢时机，不把入朝强系乙未当日。')
add('li_song_feng_dao_appointed','李崧不久任太子太师、枢密使，冯道任太傅，在枢密院候命顾问',8,'未几，',None,[('契丹主','任用李崧和冯道'),('李崧','任太子太师并充枢密使'),('冯道','任太傅，留枢密院备咨询')],when=t+'二人受到礼遇后不久',place='大梁枢密院',note='祗候为候命，不写枢密使由冯道担任；未几没有具体日。')
sup('li_song_feng_dao_appointed',8,ls,'癸巳，以張礪為平章事，晉李崧為樞密使，馮道為太傅','《辽史》把李崧任枢密使、冯道任太傅系于癸巳，通鉴置于乙未之后未几。','保留任命时间差异，不将通鉴改为癸巳；此处未补主书未载的同日张砺任命。',relation='conflicts',field='time_original')
add('khitan_sends_edicts_governors_submit','耶律德光分派使者向后晋藩镇颁诏，多数藩镇上表称臣并赴召',9,'契丹主分遣','奔驰而至。',[('契丹主','分派使者颁诏召藩镇')],when=t+'入京之后，具体日未载',place='后晋各藩镇',note='原文概述后有史匡威何重建例外，不写全部藩镇毫无例外归服；未名藩镇不补主体名单。')
add('shi_kuangwei_refuses_khitan','史匡威据守泾州，拒绝契丹命令',9,'惟彰义','建瑭之子也。',[('史匡威','以彰义节度使身份据泾州拒绝命令')],when=t+'契丹颁诏后，具体日未载',place='泾州')
relationship('建瑭','史匡威','父亲',9,span(9,'匡威，','建瑭之子也。'),'明记史匡威为史建瑭之子，父亲方向由史建瑭指向史匡威。')
add('he_chongjian_kills_envoy_surrenders_shu','何重建杀契丹使者，把秦、成、阶三州归降后蜀',9,'雄武节度使',None,[('何重建','以雄武节度使身份杀使者，举三州降蜀')],when=t+'契丹颁诏后，具体日未载',place='秦州、成州、阶州',note='复用942年将领何重建，同名官职行动相连；蜀受降对象未在本句具名，不虚连孟昶为当场参与。')
reviews={4:'承勋复用已证杨承贵后名；杀父为契丹责辞与944年实际处置分存。处死戊子，弟受兵任官未几不强同日，明确长幼关系。',5:'控告、锁押、众议、处刑、受害者家属及尸体报复分记；不为百官民众补名，傅之具体罪未扩写。',6:'旧本纪同庚寅，新传补民家夜半年龄；未反算生年，死亡不是此前请死。',7:'负义侯及指定安置不作已抵黄龙；光禄崇禄异文保留。李太后选择同行、迁寺、守禁、冻饿求食分记，饭僧追述不造新事。',8:'是日承癸巳，再入宫与朔入城分开；仪式未名施者不猜。乙未更衣，举荐到朝和未几任官分时；辽癸巳任官不同并列。',9:'概述臣服与泾州拒命、三州降蜀例外分记；史父明确关系，何重建沿稳定主体，不补未名使者和各镇官员。'}
assert not (P/'publication.json').exists()
for n in range(4,10):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(4,10)],next_paragraph=Q[10]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原9—14行连续六段，累计9/92；不将本卷视为947全年。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(4,10)],source_issues_review='承勋初名按944年已核回查；光禄崇禄、李崧冯道任命癸巳与乙未后时间并列，史家转引辽史不算独立确证；其他无直接补证处继续保留单书依据。',plain_language_review='首次逐条检查主语、动作、身份时间、关系方向与原文，白话自查完成；计划、责辞、实际动作区分。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
