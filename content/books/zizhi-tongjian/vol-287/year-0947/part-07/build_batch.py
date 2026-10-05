# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 49–56."""
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
COMMIT='22f4519de0a37af02e4e5c96623c1efb65f06888'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-august-administration']:
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
main_sources = ['tongjian-287-947-august-administration','tongjian-287-947-september-siege']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p049-p056',
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
for n in range(49, 57):
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
        citation = f'卷287·天福十二年（947年八月至十月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_07_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'刘知远','唐主':'李璟','南汉主':'刘弘熙','从诲':'高从诲','季兴':'高季昌','涛':'李涛（后晋宋初官员）','李涛':'李涛（后晋宋初官员）','弘弼':'刘弘弼','弘道':'刘弘道','弘益':'刘弘益','弘济':'刘弘济','弘简':'刘弘简','弘建':'刘弘建','弘伟':'刘弘暐','弘照':'刘弘昭','行周':'高行周','彦超':'慕容彦超','重威':'杜重威','逢吉':'苏逢吉','贞固':'窦贞固','承训':'刘承训'})
NEW_ALIASES={'尹实':['尹實'],'刘承训':['劉承訓']}
NEW_DESCRIPTIONS={'刘承训':'刘知远的儿子。947年九月刘知远诏赴澶、魏劳军时，任命他为东京留守。生卒年尚未录入。','尹实':'后汉郢州刺史。947年高从诲攻郢州时将其击败。《旧五代史》高从诲传也记这场战事，写高从诲攻城旬日后败退。生卒年未载。'}
gao='jiuwudaishi-133-gao-conghui';rep='xinwudaishi-069-gao-reputation';princes='xinwudaishi-065-eight-princes';sep='jiuwudaishi-100-september-offices';october='jiuwudaishi-100-october-siege';tao='songshi-262-li-tao-expedition'
t='947年八月，具体日未载';s='947年九月甲戌';later='947年杜重威叛后、九月亲征前，具体日未载'
add('gao_attacks_xiangzhou','高从诲趁杜重威叛乱出兵襄州，被安审琦击退',49,'高从诲闻','安审琦击却之。',[('从诲','闻杜重威叛乱，率数千水军袭襄州'),('杜重威','其叛乱成为高从诲出兵背景'),('安审琦','以山南东道节度使身份击退来军')],when=t,place='襄州',note='数千为史载约数，不能据同时反叛推杜重威与高从诲已结盟。')
add('gao_attacks_yingzhou','高从诲又攻郢州，被刺史尹实大败',49,'又寇郢州，','刺史尹实大破之。',[('从诲','出兵攻郢州，被击败'),('尹实','以郢州刺史身份大败荆南军')],when=t,place='郢州')
sup('gao_attacks_yingzhou',49,gao,'從誨怒，率州兵攻郢州，旬日，為刺史尹實所敗，自是朝貢不至。','《旧五代史》记高从诲攻郢州旬日，被尹实击败，此后不再朝贡。','旬日为约十日的攻城时长，不反推出精确开战日期。',relation='adds')
E['gao_requests_yingzhou']=event('gao_requests_yingzhou','高从诲曾请求后汉将郢州划归荆南',49,'及契丹入汴，漢高祖起義於太原，間道遣使奉貢，密有祈請，言俟車駕定河、汴，願賜郢州為屬郡，漢祖依違之。',[('从诲','遣使进贡并请求赐郢州作属郡'),('帝','对请求未明确答应或拒绝')],when='947年刘知远在太原起兵时，入大梁之前，具体日未载',place='荆南至太原',source=gao,note='以旧五代史补同一攻郢州背景，依违不是已经承诺割让。')
E['gao_request_rejected']=event('gao_request_rejected','刘知远入大梁后拒绝高从诲索取郢州的请求',49,'及入汴，從誨致貢，求踐前言，漢高祖不從。',[('从诲','进贡并要求践前言，索取郢州'),('帝','拒绝请求')],when='947年六月刘知远入大梁后，具体日未载',place='大梁',source=gao,note='践前言是高从诲提出要求的说法，前句只记汉祖依违，不将其改写为确定承诺后食言。')
add('gao_breaks_han_aligns_tang_shu','高从诲断绝与后汉往来，转而依附南唐与后蜀',49,'乃绝汉，',None,[('从诲','断绝后汉往来，依附南唐与后蜀')],when=t,place='荆南、南唐、后蜀',note='唐蜀为政权关系，未有此句明确君主个人行动，不建三人永久盟约。')
sup('gao_breaks_han_aligns_tang_shu',49,gao,'從誨東通於吳，西通於蜀，皆利其供軍財貨而已。','《旧五代史》记高从诲东通吴、西通蜀，并将动机解释为获取供军财货。','这里的吴按当时承袭吴地的南唐叙述理解，保留原字；求财为该书史家评价，不作为外交文件中的明示条款。',relation='adds')
add('jingnan_seizes_tribute','《资治通鉴》回顾荆南截取过境贡物、受追责后归还的做法',50,'初，荆南介居','曾不为愧。',[('季兴','在其任内开始截取过境贡物')],year=None,when='高季兴掌荆南以来，具体各次年份未载',place='荆南',note='连续多次做法的史家概述，未知各次时间，不造单一947年劫贡案。')
sup('jingnan_seizes_tribute',50,rep,'季興、從誨常邀留其使者，掠取其物，而諸道以書責誚，或發兵加討，即復還之而無媿。','《新五代史》记高季兴、高从诲常扣留过境使者与贡物，受书信责问或出兵讨伐后归还。','该书把父子都列入长期做法；无具体各次纪年，不以此概述覆盖已录具年个案。',relation='adds')
add('gao_multiple_allegiances','高从诲向不同政权称臣求赐，被称“高无赖”',50,'及从诲立，',None,[('从诲','向多个政权称臣，史书记其意在获得赏赐')],year=None,when='高从诲继位后至947年前后的长期做法，各次年份未载',place='荆南及交往诸政权',note='所向称臣和求赐为长期概述，称号是他国贬称，不作为正式爵号或政治自称。')
sup('gao_multiple_allegiances',50,rep,'從誨所嚮稱臣，蓋利其賜予。','《新五代史》也记高从诲向各国称臣，以求赏赐。','两书对动机的史家判断相近，不当作独立查证全部外交行为。')
sup('gao_multiple_allegiances',50,rep,'故諸國皆目為「高賴子」。','《新五代史》将诸国对高从诲的贬称记为“高赖子”。','与通鉴高无赖称谓不同，保留书别；不将贬称加入人物正式姓名。',relation='adds')
add('song_qiqiu_zhennan','李璟任宋齐丘为镇南节度使',51,'唐主以',None,[('唐主','任命宋齐丘出镇'),('宋齐丘','以太傅兼中书令身份获任镇南节度使')],when=t,place='南唐镇南军')
brothers=['弘弼','弘道','弘益','弘济','弘简','弘建','弘伟','弘照']
add('liu_sheng_kills_eight_brothers','刘晟担忧弟弟们争位，杀害八位弟弟',52,'南汉主恐','宜王弘照，',[('南汉主','担忧诸弟与其子争国，杀害八弟')]+[(x,'被刘晟杀害') for x in brothers],when='947年，《通鉴》置于八月条；《新五代史》记乾和五年同日，具体月日未载',place='南汉',note='弘伟对应既有刘弘暐、弘照对应既有刘弘昭；同一八王名单与王号背景核对后复用，保留底本字形。恐争国是记载的杀人动机，不证明诸弟已实际谋反。')
sup('liu_sheng_kills_eight_brothers',52,princes,'五年，晟弟洪弼、洪道、洪益、洪濟、洪簡、洪建、洪暐、洪昭，同日皆見殺。','《新五代史》将刘晟八弟遇害记在乾和五年，称同日皆被杀。','回查前段乾和改元年序，五年对应947年；弘洪字形及弘伟洪暐、弘照洪昭并列保留，不将同日理解为已有具体月日。',relation='adds')
for name in brothers:
 relationship('南汉主',name,'兄长',52,span(52,'南汉主恐','宜王弘照，'),'诸弟明确刘晟为兄长，方向表示刘晟是该弟的兄长；同名及弘洪字形沿已有主体。')
add('liu_sheng_kills_nephews','刘晟杀害八位弟弟的儿子，并将其女纳入后宫',52,'尽杀其男，','纳其女充后宫。',[('南汉主','杀害弟弟们的儿子，将其女纳入后宫')],when='947年杀八弟之际，具体日未载',place='南汉',note='其指前句诸弟，男女分别指诸弟子女，不误写刘晟杀自己诸子；未载姓名与人数，不虚构具名主体。')
add('liu_sheng_palaces_punishments','《资治通鉴》记刘晟建离宫并设置多种酷刑',52,'作离宫千馀间，','号“生地狱”。',[('南汉主','建离宫千余间，并设置镬汤、铁床、刳剔等酷刑')],year=None,when='刘晟在位期间，具体建宫及设刑年份未载',place='南汉',note='在宗室杀戮后概述长期政事，未明确各项发生年；千余是房间约数，生地狱为记载的称号，不新建实地地理对象。')
add('liu_sheng_kills_musician','刘晟醉后以乐工颈上瓜试剑，砍断乐工头颅',52,'尝醉，','遂断其头。',[('南汉主','醉后以乐工颈上瓜试剑，杀害乐工')],year=None,when='刘晟在位期间，具体年份未载',place='南汉',note='尝醉为未具年往事，乐工匿名，不虚构姓名或把此日与八王被杀日合并。')
add('liu_intends_dou_chancellor','刘知远拟任窦贞固为相，向苏逢吉询问另一人选',52,'初，帝与','其次谁可相者？”',[('帝','与窦贞固旧相知重，拟任为相并询问另一人选'),('贞固','成为拟任宰相的人选'),('逢吉','受到刘知远询问')],when='947年刘知远即位后、九月授任之前，具体日未载',place='后汉朝廷',note='拟任和正式九月甲戌任命分别录，俱事晋高祖是旧经历，不新建947年效力石敬瑭的事件。')
add('su_recommends_li_tao','苏逢吉推荐李涛为相，提及其曾请求斩张彦泽',52,'逢吉与翰林','此可相也。”',[('逢吉','推荐交好的李涛为相'),('涛','任翰林学士，受到推荐')],when='947年九月授相之前，具体日未载',place='后汉朝廷',note='原文张彦译与此前李涛乞斩张彦泽记载对应，疑字保留；此处为回忆推荐理由，不重建当年已斩张彦泽的事件。李涛沿已核后晋宋初官员，与887年同名者区别。')
add('generals_disagree_siege','高行周主张缓攻邺都，慕容彦超坚持急攻',52,'会高行周、','行周欲缓之以待其弊。',[('行周','主张缓攻以待城中衰弱'),('彦超','主张急攻'),('重威','据邺都受围')],when=later,place='邺都')
add('murong_accuses_gao','慕容彦超指责高行周因女儿婚姻关系偏护杜重威',52,'行周女为','由是二将不协。',[('行周','女儿嫁杜重威之子，受偏护之指控'),('彦超','以联姻关系指责高行周不攻'),('重威','其子娶高行周之女')],when=later,place='邺都军营',note='女为子妇是婚姻事实，爱贼不攻为慕容彦超指控，不能据此认定高行周确有私通。未载子女姓名，不猜指某子。')
relationship('行周','重威','姻亲',52,span(52,'行周女为','重威子妇，'),'双方子女结婚明确姻亲；此关系不推军事结盟，也不猜未具名子女身份。')
add('liu_considers_personal_campaign','刘知远担忧两将失和，考虑亲征但尚未决定',52,'帝恐生他变，','意未决。',[('帝','担忧军中失和另生变故，考虑亲征')],when=later,place='后汉朝廷',note='意未决是尚未决定，不提前写成已亲到邺都。')
add('li_tao_petitions_campaign','李涛上疏请刘知远亲征，受到赞赏',52,'涛上疏','以涛有宰相器。',[('涛','上疏请求亲征'),('帝','赞赏奏疏，认为李涛可任宰辅')],when=later,place='后汉朝廷')
sup('li_tao_petitions_campaign',52,tao,'杜重威據鄴叛，高祖命高行周、慕容彥超討之，二帥不協。濤密疏請親征。高祖覽奏，以濤堪任宰輔，即拜中書侍郎兼戶部尚書、平章事。','《宋史》李涛传也记两帅不协、李涛密疏请亲征，刘知远因此认为他可任宰辅。','正文回查传主为李涛；该传同段前接洛阳迎对及翰林任命，识别后晋宋初官员，不复用晚唐李涛。',relation='adds')
add('four_chancellors_offices','苏逢吉、苏禹珪、窦贞固、李涛获授宰相职衔',52,'九月，甲戌，','并同平章事。',[('逢吉','加左仆射兼门下侍郎、同平章事'),('苏禹珪','加右仆射兼中书侍郎、同平章事'),('贞固','授司空兼门下侍郎、同平章事'),('涛','授户部尚书兼中书侍郎、同平章事')],when=s,place='后汉朝廷',note='四人此前身份不同，苏氏二人本已任相，不能写成四人都是首次成为宰相。',description='九月甲戌，苏逢吉加左仆射兼门下侍郎，苏禹珪加右仆射兼中书侍郎，窦贞固任司空兼门下侍郎，李涛任户部尚书兼中书侍郎，四人均带同平章事。')
sup('four_chancellors_offices',52,sep,'甲戌，宰臣蘇逢吉加左僕射、監修國史，蘇禹珪加右僕射、集賢殿大學士，以吏部尚書竇貞固為守司空兼門下侍郎、平章事、宏文館大學士，','《旧五代史》也记甲戌苏逢吉、苏禹珪加仆射，窦贞固任司空、门下侍郎、平章事，并补监修国史、集贤与宏文馆职。','独立本纪正文摘录只涉及三人，李涛另句；保留职名原文，不以夹注宋史内容当新独立史料。',relation='adds')
sup('four_chancellors_offices',52,sep,'以翰林學士、行中書舍人李濤為中書侍郎兼戶部尚書、平章事。','《旧五代史》本纪正文同记李涛任中书侍郎兼户部尚书、平章事。','本纪正文与夹注所引宋史有尚书侍郎差异；本批补证按选定正文，与另导出的宋史尚书相合。')
add('liu_orders_inspection_campaign','刘知远下诏赴澶、魏慰劳军队',52,'戊寅，','诏幸澶、魏劳军，',[('帝','下诏赴澶、魏劳军')],when='947年九月戊寅',place='澶州、魏州（诏定前往地）',note='这是诏令，实际九月庚辰出大梁另录，不当戊寅已到两州。')
sup('liu_orders_inspection_campaign',52,sep,'戊寅，詔以杜重威叛命，取今月二十九日暫幸澶、魏。','《旧五代史》也记戊寅诏赴澶、魏，并将计划启行日定为当月二十九日。','计划日与后句庚辰发京分别保留，不自行换算现代日期。',relation='adds')
add('liu_chengxun_tokyo_regent','刘承训受任东京留守，负责刘知远出征期间留守',52,'以皇子承训',None,[('承训','以皇子身份任东京留守')],when='947年九月戊寅',place='东京大梁',note='皇子明确父子身份，但已存在父亲关系，若本批复用仍按全站稳定关系。')
relationship('帝','承训','父亲',52,span(52,'以皇子承训',None),'皇子承训明确为刘知远之子，方向表示刘知远是刘承训的父亲。')
add('feng_li_he_return','冯道、李崧、和凝从镇州返回后汉',53,'冯道、','自镇州还。',[('冯道','从镇州返回'),('李崧','从镇州返回'),('和凝','从镇州返回')],when='947年九月，己卯授官之前，具体返回日未载',place='镇州至后汉朝廷',note='己卯为后句李和授官日，未明确返回日，不强设同日。')
add('li_he_prince_tutors','李崧任太子太傅，和凝任太子太保',53,'己卯，',None,[('李崧','获任太子太傅'),('和凝','获任太子太保')],when='947年九月己卯',place='后汉朝廷')
sup('li_he_prince_tutors',53,sep,'己卯，以前樞密使李崧為太子太傅，以前左僕射和凝為太子太保。','《旧五代史》同记己卯李崧、和凝分别任太子太傅、太子太保。','旧史并记其前职，不推此时已经册立具体太子或实际开始授课。')
add('liu_leaves_daliang','刘知远从大梁出发亲征',54,'庚辰，',None,[('帝','从大梁启行')],when='947年九月庚辰',place='大梁')
sup('liu_leaves_daliang',54,sep,'庚辰，車駕發京師。','《旧五代史》同记庚辰刘知远从京师出发。','京师为此时大梁，启行与十月抵邺分录。')
add('zhao_kuangzan_submits_shu','赵匡赞担忧不被后汉容纳，遣使归降后蜀并请求援兵',55,'晋昌节度使',None,[('赵匡赞','遣使归降后蜀，请其从终南山路出兵援助')],when='947年冬十月，具体日未载',place='晋昌军、终南山路（请求援军线路）',note='请求线路区别实际出兵、实际抵达，后蜀答应与出军后段再录；畏不容为史家对赵的心理叙述。')
add('liu_reaches_gao_camp','刘知远抵达邺都城下，驻高行周军营',56,'戊戌，','舍于高行周营。',[('帝','抵邺都并驻营'),('行周','军营成为刘知远驻处')],when='947年十月戊戌',place='邺都城下、高行周营',note='主书记戊戌；旧本纪把至邺城下接在丙申任官之后，不强行对齐日期。')
sup('liu_reaches_gao_camp',56,october,'丙申，以相州留後王繼宏為相州節度使，加檢校太傅。至鄴都城下。','《旧五代史》十月条将抵邺都城下接在丙申任王继宏之后。','与通鉴戊戌抵达纪时位置不同；只为抵达事件保留旧史原文定位，不将王继宏任官强并为刘知远抵达的动作。',relation='conflicts')
add('gao_advises_exhaust_food','高行周建议等城中断粮，刘知远同意缓攻',56,'行周言于帝曰：','帝然之。',[('行周','建议等敌军粮尽，不急攻以免伤兵'),('帝','同意缓攻建议')],when='947年十月抵邺都后，具体日未另载',place='邺都城下',note='食尽自溃是高行周预测与策略，不提前写成此时城中已经无粮、杜重威已降。')
add('murong_humiliates_gao','慕容彦超多次欺辱高行周，高行周哭诉并以粪土塞口',56,'慕容彦超数因事','掏粪壤实其口，',[('彦超','多次因事欺辱高行周'),('行周','向执政者哭诉，并以粪土塞口')],when='947年十月围邺期间，具体各次日未载',place='邺都军营',note='数为多次，掏粪壤实其口的主体依句法为高行周，不写成慕容彦超把粪塞入其口。')
add('su_yang_report_and_mediate','苏逢吉、杨邠密报两将争执，刘知远命其和解',56,'苏逢吉、杨邠','犹命二臣和解之。',[('逢吉','与杨邠密报，并奉命劝解'),('杨邠','密报争执并奉命劝解'),('帝','知慕容彦超理亏，命二臣调停')],when='947年十月围邺期间，具体日未载',place='邺都军营',note='曲为理亏，与已执行刑事定罪区别；和解命令不等于两将永久消除嫌隙。')
add('liu_rebukes_murong','刘知远召慕容彦超责备，令其向高行周道歉',56,'又召彦超',None,[('帝','召慕容彦超入帐责备，并命其道歉'),('彦超','受责备并奉命向高行周道歉'),('行周','成为奉命道歉的对象')],when='947年十月围邺期间，具体日未载',place='刘知远军帐',note='且使诣行周谢是命令，未据此追加道歉已经完成及两将关系永久修复。')
reviews={49:'襄州击退、郢州战败与断汉附唐蜀分录，旧高传补求郢州被拒，依违不当承诺，旬日不反推开战日。',50:'截取贡物、受责归还与多向称臣为跨年概述，年份null；贬称高无赖与高赖子并列，不当正式姓名。',51:'南唐主确认为李璟，宋齐丘任镇南节度使，未补独立无载纪日。',52:'南汉主刘晟与后汉帝刘知远区分；八弟同日死据新史，弘洪及伟暐照昭异文沿已有主体；尽杀其男指诸弟子女，酷刑与乐工旧事日期未知。推荐李涛沿已核后晋宋初身份，张彦译疑字保留不创同名。婚姻事实与慕容指控区别；拟相、亲征提议、诏令、正式任命与留守分录。',53:'返回镇州与己卯授官不同纪时，太子三师职不自动证明已立具体太子。',54:'庚辰发大梁与戊寅诏及十月到邺分别记录。',55:'归蜀请求及终南路援军请求不当已经出兵或到达。',56:'戊戌到邺与旧丙申后叙抵达位置保留异说；粮尽为建议预期，高塞粪主体明确；密报和解令、责彦超令谢分别区分执行与命令。'}
assert not (P/'publication.json').exists()
for n in range(49,57):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(49,57)],next_paragraph=Q[57]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原54—61行连续八段，本卷累计56/75；947年跨卷累计148/167，尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(49,57)],source_issues_review='南汉八王名单保留弘洪、伟暐、照昭及恩息宜宣王号异文；刘知远抵邺戊戌与旧本纪丙申后叙位置不同。张彦译与张彦泽为疑字不新建主体。',plain_language_review='首次检查展示文案及事实说明，主语明确；引用原字不改。跨年概述不造日期，预期、指控、建议、诏令与实际行动分清。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
