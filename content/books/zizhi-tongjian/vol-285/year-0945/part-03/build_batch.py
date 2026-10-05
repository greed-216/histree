# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 945 paragraphs 19–23."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,24))
COMMIT='cb9d5570b796ecf7a4a202bff72b905f6cd3ff0c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-945-november-december','xinwudaishi-009-945','xinwudaishi-029-sang-feng-strife']:
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
main_sources = ['tongjian-285-945-november-december']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0945-p019-p023',
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
lines = (ROOT / 'resources/derived/tongjian/285.txt').read_text().splitlines()
for n in range(19, 24):
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
    for a,b in [('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        citation = f'卷285·后晋开运二年（945年十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0945_03_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_285_0945_' + code
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
        edge = 'participation_zztj_285_0945_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_285_0945_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','汉主':'刘弘熙','刘晟':'刘弘熙','景达':'徐景达','李景达':'徐景达','弘佐':'钱弘佐','李彦韬':'李彦韬（后晋宣徽使）','胡思进':'胡进思'})
NEW_ALIASES={'殷鹏':['殷鵬'],'戴偃':['玄黄子','玄黃子'],'丁思瑾':[],'谢仲宣':['謝仲宣']}
NEW_DESCRIPTIONS={'殷鹏':'大名人，字大举。《旧五代史》记他进士出身，曾为后唐闵帝幕僚，天福年间任中书舍人，与冯玉共事并替他草拟诏令。945年十二月任给事中、枢密直学士，参与冯玉的任官商议；《资治通鉴》记有人因此向他请托、送礼。生卒年本批未核。','戴偃':'《旧五代史》记为金陵人，自称玄黄子，擅长以诗讽谏，唐末避乱到湖南。《资治通鉴》945年条称他为湘阴处士，因诗讽刺而被马希范囚禁；《旧五代史》另记马希范命他迁居碧湘湖，并禁止他人与其来往。两书处置细节分别保留，生卒年未核。','丁思瑾':'楚天策副都军使。945年十二月条下记他为戴偃受囚上书直谏，马希范削去他的官爵。生卒年未载；不与同年《旧五代史》所记晋左羽林统军丁审琪混同。','谢仲宣':'南唐齐王徐景达的府属。945年十二月条下，他向徐景达提出宋齐丘是先帝旧交、不应弃置；徐景达转向李璟进言，随后受命去青阳召宋齐丘。生卒年未载。'}
os='jiuwudaishi-084-945-december';yp='jiuwudaishi-089-yin-peng';sg='jiuwudaishi-089-sang-dismissal';dy='jiuwudaishi-133-dai-yan';ny='xinwudaishi-009-945';ns='xinwudaishi-029-sang-feng-strife'
dec='945年十二月条下，具体日未载';old='945年桑维翰罢政之前的追述，具体月日待核'
add('qian_southeast_marshal','后晋授钱弘佐东南面兵马都元帅',19,'十二月，',None,[('弘佐','获授东南面兵马都元帅')],when='945年十二月乙丑',place='吴越',note='授予军职，不据此推断东南诸国实际均受其指挥。')
sup('qian_southeast_marshal',19,os,'十二月乙丑，以兩浙節度使、吳越國王錢宏佐兼東南面兵馬都元帥。','《旧五代史》同记十二月乙丑钱弘佐兼东南面兵马都元帅。','两书姓名弘佐宏佐为底本字形差异，沿用钱弘佐主体，原文保留宏字。')
# Independent evidence for previous paragraph's death; do not create a contradictory appointment as a settled fact.
prior_kan=next(x for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for x in json.loads(f.read_text())['events'] if x['key']=='event_zztj_285_0945_qian_kills_kan_fan')
B['events'].append(dict(prior_kan,status='draft'));reused.add(prior_kan['key']);used.setdefault(19,[]).append(prior_kan['key'])
claim('event','event_zztj_285_0945_qian_kills_kan_fan','description','《旧五代史》945年十二月丙寅仍记阚璠遥领宁国军节度使、仍典军；与《资治通鉴》十一月被杀的先后顺序冲突，待核。',19,'以吳越國金馬右廂都指揮使、明州刺史闞璠遙領宣州寧國軍節度使，並典軍如故。','补登记原书异说；未认作追赠、诏令延迟或另一个阚璠，这些解释本段均无证据。',source=os,relation='conflicts')
event('hu_zhaoxin_appointment','《旧五代史》记胡进思遥领昭信军节度使',19,'丙寅，以吳越國金馬左廂都指揮使、湖州刺史胡思進遙領虔州昭信軍節度使，',[('胡思进','在《旧五代史》记为遥领虔州昭信军节度使')],source=os,when='《旧五代史》记945年十二月丙寅',place='吴越；遥领虔州',note='原书胡思进与《资治通鉴》湖州刺史胡进思职地对应，暂复用同人并保留倒置字形待核；遥领不等于离开吴越到虔州就任。')
claim('person',people['胡进思'],'aliases','《旧五代史》此处将湖州刺史胡进思写作胡思进。',19,'湖州刺史胡思進','职地与身份对应作同人引用，姓名字序仍待纸本核，不改已有别名字段。',source=os)
add('yin_appointed','殷鹏任给事中、枢密直学士',20,'辛未，','直学士。',[('殷鹏','由前中书舍人任给事中、枢密直学士')],when='945年十二月辛未',place='后晋朝廷')
sup('yin_appointed',20,os,'以前中書舍人殷鵬為給事中，充樞密直學士；','《旧五代史》同记殷鹏由前中书舍人任给事中，充枢密直学士。','辛未纪日见同段开头，两书职名一致。')
claim('person',people['殷鹏'],'description','殷鹏字大举，大名人；《旧五代史》记其年少中进士，曾为后唐闵帝幕僚。',20,'殷鵬，字大舉，大名人也。以雋秀為鄉曲所稱，弱冠擢進士第。唐閔帝之鎮魏州，聞其名，辟為從事。','说明姓名字籍贯与前职，不将传记早年经历定在945年。',source=yp)
add('feng_yin_appointments','冯玉在任官时与殷鹏商议',20,'鹏，','议之。',[('冯玉','与殷鹏商议朝廷人事任命'),('殷鹏','作为冯玉同党参与任官商议')],when=dec,place='后晋朝廷',note='党是史书对政治依附的描述，不新增亲属或正式组织关系。')
sup('feng_yin_appointments',20,yp,'及玉為樞密使，擢為本院學士，每有庶僚秉鞹謁玉，故事，宰臣以履見之，鵬多在玉所，見客亦然。','《旧五代史》记冯玉任枢密使后，殷鹏任本院学士，经常在冯玉处以宰臣接客方式见来访官员。','补充两人的共事与接客情况，不把来访者一概认作行贿。',relation='adds')
add('yin_receives_petitions_gifts','向殷鹏请托、送礼的人很多',20,'由是',None,[('殷鹏','因参与任官商议而受到大量请托和送礼')],when=dec,place='后晋',note='充满其门为史书概述，未补人数或金额；本段其门承接殷鹏，不外推每次任命均为受贿结果。')
# 21: retrospective setting and allegations are separate from dismissal.
add('sang_sends_servant','桑维翰派女仆入宫问候太后',21,'初，','太后，',[('桑维翰','在石重贵病未好、适逢正旦时派女仆入宫问候太后'),('帝','病尚未好，适逢正旦')],when=old,year=None,place='后晋宫廷',note='初字引入追述，不能定为十二月正旦；未具名女仆不新建人物。')
add('sang_asks_chongrui_study','桑维翰询问石重睿最近是否读书',21,'因问：','读书否？”',[('桑维翰','通过女仆询问皇弟石重睿最近读书情况'),('石重睿','成为询问读书情况的对象')],when=old,year=None,place='后晋宫廷')
sup('sang_asks_chongrui_study',21,sg,'後因少帝微有不豫，維翰曾密遣中使達意於太后，請為皇弟重睿擇師傅以教道之，少帝以此疑其有他。','《旧五代史》记桑维翰派中使向太后请求，为石重睿选择师傅，石重贵因此怀疑他别有企图。','《资治通鉴》女仆问读书与该书中使请择师傅的细节不同，分别保留，不合并成同一使者的确定言辞。',relation='conflicts')
sup('sang_asks_chongrui_study',21,ns,'帝飲酒過度得疾，維翰遣人陰白太后，請為皇弟重睿置師傅。','《新五代史》记石重贵饮酒过度生病，桑维翰暗中派人向太后请求为石重睿设师傅。','该书使者未具名；饮酒得病为该书补充，不能据此补确切正旦年。',relation='adds')
add('shi_reports_to_feng','石重贵把桑维翰询问石重睿的事告诉冯玉',21,'帝闻之，','冯玉，',[('帝','得知询问后告诉冯玉'),('冯玉','从石重贵处得知桑维翰的询问')],when=old,year=None,place='后晋')
add('feng_accuses_sang','冯玉诬告桑维翰有废立皇帝的企图',21,'玉因','之志。',[('冯玉','诬告桑维翰有废立之志'),('桑维翰','受到冯玉关于废立企图的诬告')],when=old,year=None,place='后晋',note='谮是诬告，不把废立企图当作已证实的桑维翰计划。')
add('shi_suspects_sang','石重贵对桑维翰产生怀疑',21,'帝疑之。','帝疑之。',[('帝','因诬告怀疑桑维翰'),('桑维翰','受到石重贵怀疑')],when=old,year=None,place='后晋')
add('feng_li_exclude_sang','冯玉、李彦韬与李守贞合谋排挤桑维翰',21,'李守贞','排之，',[('李守贞','原本厌恶桑维翰，与冯玉、李彦韬合谋排挤'),('冯玉','参与排挤桑维翰'),('李彦韬','参与排挤桑维翰'),('桑维翰','受到合谋排挤')],when='945年桑维翰罢政之前，具体日未载',place='后晋',note='李彦韬复用后晋宣徽使，不误合902年温韬别名主体。')
add('recommend_zhao_replace_sang','冯玉等认为赵莹容易控制，共同推荐他替代桑维翰',21,'以中书令','维翰。',[('赵莹','被认为柔弱易控制，获共同推荐'),('冯玉','参与推荐赵莹'),('李彦韬','参与推荐赵莹'),('李守贞','参与推荐赵莹')],when='945年桑维翰罢政之前，具体日未载',place='后晋',note='柔而易制为史书所述推荐者的考量，不当作客观人格鉴定。')
add('sang_dismissed_kaifeng','桑维翰被罢政，改任开封尹',21,'丁亥，','开封尹。',[('桑维翰','被罢去政务职权，改任开封尹')],when='945年十二月丁亥',place='开封')
sup('sang_dismissed_kaifeng',21,os,'丁亥，以樞密使、中書令桑維翰為開封尹；','《旧五代史》同记十二月丁亥桑维翰由枢密使、中书令改任开封尹。','原职与新职分别保留，不把开封尹视作流放。')
sup('sang_dismissed_kaifeng',21,ny,'丁亥，桑維翰罷。','《新五代史》同记十二月丁亥桑维翰罢政。','两本纪纪日一致。')
sup('sang_dismissed_kaifeng',21,sg,'玉遂以詞激少帝，尋出維翰為開封府尹。','《旧五代史》列传记冯玉用言辞激石重贵，随后桑维翰改任开封府尹。','补充处置前因；该传未在此给独立确切日，纪日据本纪与主书。',relation='adds')
add('zhao_chief_secretary','赵莹任中书令',21,'以莹为','中书令，',[('赵莹','获任中书令')],when='945年十二月丁亥',place='后晋朝廷')
sup('zhao_chief_secretary',21,os,'以開封尹趙瑩為中書令、宏文館大學士；','《旧五代史》记赵莹由开封尹任中书令、宏文馆大学士。','大学士职为该书补证，保留宏文馆原字，不自行改为弘文馆。',relation='adds')
add('li_song_privy_council','李崧任枢密使、守侍中',21,'李崧为','守侍中。',[('李崧','获任枢密使、守侍中')],when='945年十二月丁亥',place='后晋朝廷')
sup('li_song_privy_council',21,os,'以左僕射、門下侍郎、平章事李崧為守侍中，充樞密使；','《旧五代史》同记李崧由左仆射、门下侍郎、平章事改任守侍中、枢密使。','守侍中是完整官职表达，不拆作地理驻守。')
sup('li_song_privy_council',21,ny,'開封尹趙瑩為中書令，李崧守侍中、樞密使。','《新五代史》同记赵莹任中书令、李崧守侍中兼枢密使。','独立保留本纪引用。')
add('sang_withdraws_visits','桑维翰称脚病，减少朝见并拒绝宾客',21,'维翰遂','宾客。',[('桑维翰','改任开封尹后称脚病，减少朝见，拒绝宾客')],when='945年十二月罢政之后，具体日未载',place='开封',note='称足疾是其所称病情，不诊断是否装病。')
sup('sang_withdraws_visits',21,sg,'維翰稱足疾，罕預朝謁，不接賓客。','《旧五代史》同记桑维翰称脚病，少朝见、不接宾客。','行为记载一致，不把罕预朝谒改成从未朝见。')
sup('sang_withdraws_visits',21,ns,'維翰遂稱足疾，稀復朝見。','《新五代史》也记桑维翰称脚病，减少朝见。','未据称疾断定疾病真伪。')
add('question_sang_treatment','有人质问冯玉，为何让元老桑维翰处理开封琐务',21,'或谓','乎？”',[('冯玉','受到质问，为何未给桑维翰大藩而让他任开封尹')],when='945年十二月罢政后，具体日未载',place='后晋',note='说话者未名，不造人物；提议优以大藩未执行，不建授藩事实。')
add('feng_fears_sang_rebellion','冯玉称害怕桑维翰造反，或教别人造反',21,'玉曰：“恐其反耳。”',None,[('冯玉','以担心桑维翰自己或教人造反解释处置'),('桑维翰','被冯玉指称可能造反或教人造反')],when='945年十二月罢政后，具体日未载',place='后晋',note='冯玉的担心与辩解不等于桑维翰实际造反。')
# 22–23.
add('ma_imprisons_dai','马希范因戴偃诗中讽刺而囚禁他',22,'楚湘阴','囚之。',[('戴偃','因诗中多有讽刺而被囚禁'),('马希范','囚禁戴偃')],when=dec,place='楚，具体拘禁地点未载',note='湘阴为处士所在，不据此把拘禁地定为湘阴；与旧书金陵出身不矛盾。')
sup('ma_imprisons_dai',22,dy,'即日使遷居湖上，乃潛戒公私不得與之往還。自是偃窮餓日至，無以為計，','《旧五代史》记马希范命戴偃迁居碧湘湖，并暗中禁止公私与其来往，戴偃因而日益贫困饥饿。','该书记迁湖隔绝往来，与《资治通鉴》囚禁的处置细节分别列出；该段没有明确年日，不将所有过程强定十二月。',relation='adds')
claim('person',people['戴偃'],'description','《旧五代史》记戴偃是金陵人，善于以诗规讽，自称玄黄子，作《渔父诗》百篇讽谏马希范奢侈营建。',22,(sources[dy]/'source.txt').read_text().split('故其句有：')[0].strip(),'自称与诗名据本传，原文规讽对象为马氏文昭王；未将本传后来携女出逃、马氏去世提前录在945年。',source=dy)
add('ding_remonstrates','丁思瑾为戴偃受囚上书直谏',22,'天策','切谏，',[('丁思瑾','以天策副都军使身份上书直谏马希范'),('马希范','受到丁思瑾上书直谏')],when=dec,place='楚')
add('ma_strips_ding','马希范削去丁思瑾的官爵',22,'希范削',None,[('马希范','因直谏削丁思瑾官爵'),('丁思瑾','上书后被削去官爵')],when=dec,place='楚',note='削官爵非杀死，不补具体新职或流放地。')
add('xie_asks_recall_song','谢仲宣劝徐景达为宋齐丘回朝进言',23,'唐齐王','众心。”',[('谢仲宣','向齐王徐景达指出弃置先帝旧交宋齐丘不合人心'),('景达','听取府属谢仲宣的进言'),('宋齐丘','成为回朝建议所涉及的人物')],when=dec,place='南唐',note='不厌众心是谢仲宣的判断，不等同于全民反对调查。')
add('jingda_pleads_song','徐景达向李璟请求不要弃置宋齐丘',23,'景达为之','为名！”',[('景达','向李璟为宋齐丘进言'),('唐主','听取徐景达请求'),('宋齐丘','由徐景达请求不要弃置')],when=dec,place='南唐',note='景达沿用徐景达主体，未因已更姓李另建重复人。勿用可也为论辩，不认作已决定终身不用。')
add('li_sends_jingda_qingyang','李璟派徐景达亲赴青阳召宋齐丘',23,'唐主乃',None,[('唐主','派徐景达去青阳召宋齐丘'),('景达','受命亲往青阳召宋齐丘'),('宋齐丘','获召回朝')],when=dec,place='青阳',note='这里只记录派人召回，任太傅中书令在下一年，不提前录入。')
reviews={19:'吴越授元帅同日补证；阚璠十二月任官与十一月被杀冲突独立登记，不覆盖死亡。胡进思思进按湖州刺史对应保留倒字待核，遥领非到任。',20:'殷鹏大名即广晋地域身份对应，字大举前职独立来源。任职、任官商议、请托送礼分开，不把全部来访当作行贿。',21:'初字正旦为追叙未定年，太后女仆未造名。两史中使请师傅与通鉴女仆问读书不同并列。诬告与疑惧不是实际废立；李彦韬后晋主体单独复用。三项官命丁亥，足疾朝见频率按文。匿名质问与冯玉害怕造反不写成已反。',22:'戴偃湘阴居处与金陵籍贯分清，囚禁与迁湖隔绝往来细节各录，旧传全程未套945十二月。丁思瑾直谏削官非死，不混丁审琪。',23:'谢府属、齐王进言与受命往青阳分开，评价人心不当客观统计；李景达复用徐主体，下一年授宋职尚未录。'}
assert not (P/'publication.json').exists()
for n in range(19,24):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=945,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(19,24)],next_paragraph='zztj-v285-y0946-p001',next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285第24—28行，945年第19—23段连续五段；须待本批发布及年度审计后才确认945年58段完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(19,24)],source_contexts=[dict(source_key=main_sources[0],note='只录945年最后五段；946年正月在同一来源快照中，仅留上下文不提前录。')],source_issues_review='阚璠任官纪日与死亡矛盾保留待核；胡思进字序待纸本核。桑维翰遣女仆或中使、询问读书或置师傅并列原文。戴偃隔绝往来本传未明确年日。电子底本纸本未核不视作独立确证。',plain_language_review='首次逐条阅读人物、事件、参与及事实说明，写明确主体与动作；诬告、猜测、请求和实际处置分开。补证追述不强定当前年，引用原字与快照一致。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
