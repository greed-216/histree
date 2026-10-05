# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 33–40."""
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
COMMIT='8636c7baf7b9441624e26d44023cae263c6bd03f'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-june-july-governors']:
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
main_sources = ['tongjian-287-947-june-july-governors','tongjian-287-947-hengzhou-uprising']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p033-p040',
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
for n in range(33, 41):
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
        citation = f'卷287·天福十二年（947年七月至八月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_05_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'刘知远','兀欲':'耶律阮','麻荅':'麻答','李达':'李仁达','孺赟':'李仁达','弘倧':'钱弘倧','通':'李通（李仁达弟）','弘璲':'杜弘璲','张琏':'张琏（幽州军指挥使）','李荣':'李筠（原名李荣）','刘鐸':'刘铎','邪律忠':'郎五'})
NEW_ALIASES={'李通（李仁达弟）':['李通（李仁達弟）'],'杜弘璲':[],'张琏（幽州军指挥使）':['張璉（幽州軍指揮使）'],'杨衮':['楊袞'],'杨安':['楊安'],'李筠（原名李荣）':['李榮（控鶴指揮使）','李荣（控鹤指挥使）'],'李彦从':['李彥從']}
NEW_DESCRIPTIONS={'李通（李仁达弟）':'李仁达的弟弟。947年李仁达赴钱唐见吴越王钱弘倧时，令他在福州代理留后事务。生卒年未载。','杜弘璲':'杜重威之子。947年杜重威拒绝调镇，送他到麻答处作人质以求援兵。生卒年未载。','张琏（幽州军指挥使）':'947年率领赵延寿留在恒州的幽州亲兵，杜重威请求借其军守魏州。是否与895年所见同名人物有关，未得确证，分别建档。生卒年未载。','杨衮':'契丹将领。947年麻答派他率契丹及幽州兵援杜重威；他出兵后，恒州留守军减少，为当地起兵提供时机。生卒年未载。','杨安':'契丹将领。947年受麻答派遣，与李殷率千骑进攻洺州，在邢、洺两州境内劫掠。生卒年未载。','李筠（原名李荣）':'并州太原人，初名荣，后来因避周世宗讳改名筠。947年任控鹤指挥使，与何福进筹划恒州起兵，先夺甲库并组织官兵与居民作战。与李昪的父亲李荣、晚唐同名李筠分别建档。生卒年尚未录入。','李彦从':'947年任左飞龙使，恒州驱逐契丹驻军后，奉刘知远命率军前往增援。生卒年未载。'}
j='jiuwudaishi-100-intercalary-july';aug='jiuwudaishi-100-august-hengzhou';bai='jiuwudaishi-106-bai-zairong';origin='songshi-484-li-yun-origin';name='songshi-484-li-yun-name';t='947年闰七月，具体日未载';u='947年闰七月辛巳';v='947年八月壬午朔'
add('li_da_leaves_brother_fuzhou','李仁达令弟弟李通暂掌福州，自己赴钱唐见钱弘倧',33,'李达以','见吴越王弘倧，',[('李达','令弟弟代理福州留后事务，自己赴钱唐'),('通','暂掌福州留后事务'),('弘倧','受李仁达前来拜见')],when='947年七月，具体日未载',place='福州至钱唐',note='李达沿已有李仁达及多次更名的主体；弟通明确姓氏，但未知生卒年。')
relationship('李达','通','兄长',33,span(33,'李达以','见吴越王弘倧，'),'其弟通明确长幼，方向表示李仁达是李通的兄长。')
add('qian_renames_li_rugun','钱弘倧加李仁达兼侍中，并改其名为孺赟',33,'弘倧承制','更其名曰孺赟。',[('弘倧','承制加李仁达兼侍中，并为他改名'),('李达','获加兼侍中，改名孺赟')],when='947年七月钱唐会见之际，具体日未载',place='钱唐',note='更名沿同一主体，新增事实说明此时孺赟为李仁达，不新建更名人物。')
add('li_bribes_hu_for_return','李仁达以金笋和杂宝贿赂胡进思，请求回福州',33,'既而孺赟','求归福州。',[('孺赟','以金笋二十株及杂宝贿赂胡进思求归'),('胡进思','收到求归福州的贿赂')],when='947年七月受加官、更名后，具体日未载',place='钱唐',note='悔惧为史家心态描述，金笋形态不推重量或币值。')
add('hu_petitions_li_return','胡进思代李仁达请求返回福州，钱弘倧同意',33,'进思为之请，',None,[('胡进思','向钱弘倧代为请求'),('弘倧','同意请求'),('李达','求归福州获同意')],when='947年七月，具体批准日未载',place='钱唐至福州（获准返回地）',note='同意回归与实际到达福州日期区别，后文到镇另录。')
add('du_refuses_transfer_hostage','杜重威拒绝调镇，送儿子杜弘璲到麻答处求援',34,'杜重威自以','质于麻荅以求援。',[('杜重威','拒绝移镇，送儿子作人质以求援'),('弘璲','被送到麻答处作人质'),('麻荅','成为杜重威求援及质子的对象')],when='947年七月丙申调任后、闰七月庚午之前',place='邺都至恒州',note='疑惧为史家描述，负中国为史家评价；拒命区别上批收到调任命令，不写成已赴归德。')
relationship('杜重威','弘璲','父亲',34,span(34,'杜重威自以','质于麻荅以求援。'),'其子弘璲明确父子，方向表示杜重威是杜弘璲的父亲。')
add('du_requests_youzhou_troops','杜重威请求赵延寿留在恒州的幽州亲兵守魏州',34,'赵延寿有','重威请以守魏。',[('赵延寿','其原有幽州亲兵留在恒州'),('张琏','率幽州亲兵'),('杜重威','请求以幽州兵守魏州')],when='947年七月丙申调任后、闰七月庚午之前',place='恒州至魏州（请求驻守地）',note='二千为史载兵数，张琏与895年同名者尚未证明同人，限定职务建档。')
add('mada_sends_yang_gun','麻答派杨衮率契丹及幽州兵援杜重威',34,'麻荅遣其将','幽州兵赴之。',[('麻荅','派杨衮率援军赴魏州'),('杨衮','率契丹一千五百人与幽州兵赴援')],when='947年七月至闰七月，具体派军日未载',place='恒州至魏州',note='契丹一千五百、幽州二千为不同部队，不误将一千五百作为援军总数。')
add('liu_strips_du_orders_campaign','刘知远削夺杜重威官爵，派高行周、慕容彦超讨伐',34,'闰月，庚午，',None,[('帝','削夺杜重威官爵，组织讨伐'),('杜重威','被削夺官爵并受讨'),('高行周','任招讨使率军讨伐'),('慕容彦超','以镇宁节度使身份任副使')],when='947年闰七月庚午',place='后汉朝廷至邺都')
sup('liu_strips_du_orders_campaign',34,j,'詔削奪重威官爵，貶為庶人。以高行周為行營都部署，率兵進討。','《旧五代史》也记削夺杜重威官爵、贬为庶人，并以高行周率军讨伐。','该书主帅职名作行营都部署，通鉴作招讨使，分别保留；补句没有慕容彦超，不据此确认其副职。',relation='adds')
add('yang_guo_wang_formal_offices','杨邠、郭威、王章分别获正式枢密、财政职任',35,'辛未，','皆为正使。',[('杨邠','由权枢密使正式任枢密使'),('郭威','由权副枢密使正式任副枢密使'),('王章','由权三司使正式任三司使')],when='947年闰七月辛未',place='后汉朝廷',note='正使指由暂代变正式职任，郭威仍为副枢密使，不因正使二字误建成枢密使正职。')
sup('yang_guo_wang_formal_offices',35,j,'辛未，以權樞密使楊邠為樞密使，加檢校太傅；以權樞密副使郭威為副樞密使，加檢校太保；以權三司使王章為三司使，加檢校太傅。','《旧五代史》明确同日杨邠、郭威、王章各由暂代转为正式原职，并加检校官。','补书逐人职名澄清正使不是三人都任同一正职。',relation='adds')
add('wang_zhang_cuts_costs','王章建议停止不急事务、节省开支，以保障扩编军队用度',35,'时兵荒之馀，',None,[('王章','提出削减非急事务与无益支出，以供军用'),('帝','收到王章财政建议')],when='947年闰七月，具体建议日未另载',place='后汉朝廷',note='兵数顿增数倍为史家概数；用度克赡记方案效果，不臆造预算金额或具体项目。')
add('liu_builds_six_temples','刘知远下令建立六庙，尊奉汉代两帝并追尊四代先人',36,'庚辰，',None,[('帝','建立六庙，以两汉帝庙为百世不迁，并立四亲庙追尊')],when='947年闰七月庚辰',place='后汉宗庙',note='宗庙政治奉祀不能作为刘知远与两汉皇室有真实血缘的证据，不建无证家谱连接。')
sup('liu_builds_six_temples',36,j,'庚辰，追尊六廟，以太祖高皇帝、世祖光武皇帝為不祧之廟，高曾已下四朝，追尊謚號','《旧五代史》同记庚辰六庙及两汉帝庙不祧、四代先人追尊。','六庙数量与结构相合，不凭奉祀关系推血缘祖先。')
add('mada_seizes_abuses_civilians','《资治通鉴》记麻答夺取财物妇女，并诬村民为盗、用刑杀害',37,'麻荅贪猾残忍，','语笑自若。',[('麻荅','夺取民间财物妇女，诬捕并用刑杀村民')],when='947年麻答留守恒州期间，具体各案日未载',place='恒州及附近村落',note='贪猾残忍为史家评价，诬盗与杀人按记载整理；匿名被害者不虚构姓名或人数。')
add('mada_uses_imperial_regalia','麻答穿黄衣、用帝王车服，并称契丹无此禁忌',37,'出入或被黄衣，','吾国无忌也。”',[('麻荅','使用帝王车服，声称契丹无此禁忌')],when='947年恒州留守期间，具体日未载',place='恒州',note='吾国无忌为麻答自述，不认定契丹制度完全不存在等级限制。')
add('mada_assigns_four_ministers','麻答派冯道等四人分别主管馆院及中书事务',37,'又以宰相员不足，','其僭妄如此。',[('麻荅','发牒安排四人职掌'),('冯道','判弘文馆'),('李崧','判史馆'),('和凝','判集贤'),('刘昫','判中书')],when='947年恒州留守期间，具体日未载',place='恒州',note='判为主持事务；僭妄为史家评价，不将四人同职建成统一枢密任命。')
add('mada_punishes_crimes_controls_exit','麻答严惩契丹犯法者，又令守门人杀窥门汉人以阻止逃离',37,'然契丹或犯法，',None,[('麻荅','严惩契丹犯法者，并向守门人下达杀窥门者的命令')],when='947年恒州留守期间，具体日未载',place='恒州城门、市场',note='杀窥门人是命令，此段未明载具体执行个案；市肆不扰是史家对执法结果的描述，不能消除前文麻答侵夺民间的记载。')
add('xue_kills_supply_envoy_submits','薛怀让杀麻答催粮使者，举洺州归降刘知远',38,'麻荅遣使','举州降。',[('麻荅','遣使催运洺州粮饷'),('薛怀让','闻刘知远入大梁后杀使者，举州归降')],when='947年六月刘知远入大梁后、闰七月恒州起兵前，具体日未载',place='洺州')
sup('xue_kills_supply_envoy_submits',38,aug,'初，懷讓為洺州防禦使，契丹麻答發健步督洺州糧運，懷讓殺之以聞。','《旧五代史》同记麻答派人督洺州粮运，薛怀让杀使者并奏报。','此为八月条内追叙，不将杀使者日直接定为八月奏报邢州之日。')
add('guo_xue_attack_xingzhou_fails','郭从义与薛怀让攻邢州刘铎，未能攻克',38,'帝遣郭从义','不克，',[('帝','派郭从义率一万兵会同薛怀让攻邢州'),('郭从义','率军进攻邢州'),('薛怀让','会军攻邢州'),('刘鐸','据邢州未被攻克')],when='947年洺州归降后、恒州起兵前，具体日未载',place='邢州')
add('mada_sends_yang_an_li_yin','刘铎向麻答求援，杨安、李殷率千骑攻洺州',38,'鐸请兵于麻荅，','攻怀让于洺州。',[('刘鐸','向麻答请求援军'),('麻荅','派杨安与李殷率千骑援攻'),('杨安','与李殷率骑兵攻洺州'),('李殷','以原义武节度使身份率骑兵攻洺州')],when='947年恒州起兵前，具体日未载',place='邢州、恒州至洺州')
add('xue_defends_yang_loots','薛怀让守洺州，杨安等军劫掠邢、洺两州边境',38,'怀让婴城自守，','邢、洺之境。',[('薛怀让','闭城自守'),('杨安','纵军劫掠邢州、洺州境内')],when='947年恒州起兵前，具体日未载',place='洺州、邢州境内',note='安等未逐一列全，不将未明示的每人都加为具体劫掠参与者。')
add('mada_embezzles_rations','麻答按一万四千人领粮供不足二千驻军，将余粮据为己有',38,'契丹所留兵','收其馀以自入。',[('麻荅','令按虚增人数给粮，将差额据为己有')],when='947年恒州留守期间，具体日未载',place='恒州',note='不足二千与一万四千按史载数量分别保留，不倒算确定贪污金额。')
add('mada_cuts_han_army_rations','麻答削减汉兵及其粮食，军中怨愤并想南归',38,'麻荅常疑汉兵，','皆有南归之志。',[('麻荅','逐步削减汉兵，并将其粮食分给契丹军')],when='947年恒州起兵之前，具体日未载',place='恒州',note='疑汉兵、众心怨愤和南归之志为史家动机描述，不以皆字证明每一名军士的心理。')
add('he_li_plan_uprising','何福进、李筠秘密联络壮士，筹划攻契丹驻军',38,'前颍州防御使','犹豫未发。',[('何福进','与控鹤指挥使秘密联络数十壮士，暂未发动'),('李荣','与何福进谋攻驻军，因其尚强而犹豫')],when='947年闰七月辛巳起兵之前，具体日未载',place='恒州',note='李荣按宋史明示初名荣、后改筠识别为李筠（原名李荣）；与晚唐李筠及李昪父李荣分别建档。数十为约数，谋划与实际发动分开。')
claim('person','person_李筠（原名李荣）','description','李筠是并州太原人，曾任控鹤指挥使。',38,'李筠，并州太原人。','传首籍贯与主书太原相合，本传随后明确迁控鹤指挥使；核对传主及职务后匹配，非晚唐同名者。',source=origin)
claim('person','person_李筠（原名李荣）','description','李筠初名荣，因避周世宗讳而改名筠。',38,'初名榮，避周世宗諱，將改之，或令名“筠”','直接传文确认旧名与改名原因；此为后来的更名说明，不把更名行为定到947年。',source=name)
add('he_li_choose_bell_signal','何福进、李筠趁契丹军外出，约定以寺钟为起兵信号',38,'会杨衮、',None,[('何福进','趁驻军减至八百，决定起兵并约定寺钟信号'),('李荣','参与决定起兵及约定信号')],when='947年闰七月辛巳起兵前',place='恒州佛寺及军营',note='前不足二千、此留八百为不同军队部署阶段，不能直接混作同一时点人数；杨衮杨安出军在前段分别录入。')
add('ruan_summons_ministers_funeral','耶律阮派骑兵召冯道、李崧、和凝赴耶律德光葬礼',39,'辛巳，','会葬契丹主德光于木叶山。',[('兀欲','派骑兵召晋朝官员参加耶律德光葬礼'),('冯道','被召赴葬礼'),('李崧','被召赴葬礼'),('和凝','被召赴葬礼')],when=u,place='恒州至木叶山（拟赴葬礼地点）',note='官员未出发即起兵，不能将召赴写成已经参加葬礼；辽史葬礼月份地名需另校核。')
add('hengzhou_bell_attack','寺钟响起后，汉兵夺守门武器、突入军府',39,'道等未行，','因突入府中。',[],when=u,place='恒州城门、军府',note='兵民未名，按集体行动录入，杀十余为史载约数，不虚构具名斩杀者。')
add('li_yun_takes_arsenal','李筠夺取甲库，给汉兵居民装备并与契丹军交战',39,'李荣先据甲库，','与契丹战。',[('李荣','夺甲库，发装备给军民并焚牙门交战')],when=u,place='恒州甲库、牙门')
add('bai_forced_to_join','白再荣犹豫躲避，被军吏强行拉出参战',39,'荣召诸将并力，','再荣不得已而行。',[('李荣','召诸将一起作战'),('白再荣','起初躲避，后被军吏迫使参战')],when=u,place='恒州军营')
sup('bai_forced_to_join',39,bai,'再榮端坐本營，遲疑久之。為軍吏所迫，乃行。','《旧五代史》白再荣传也记他迟疑不出，后受军吏逼迫才参战。','同一犹豫与受迫行动，不因本纪白再荣等逐麻答的概述反推他首先发动。')
add('mada_retreats_north_city','麻答等携家属财物退守北城，起兵队伍出现劫掠与逃散',39,'诸将继至，','懦者窜匿。',[('麻荅','惊慌后载财物家属退守北城')],when=u,place='恒州北城',note='军民缺统一及部分人劫掠、逃散按史述整理，不把所有参战军民都记为劫掠者。')
add('khitan_counterattack_casualties','契丹军从北门反攻，史书记汉民死者二千余',39,'八月，壬午朔，','汉民死者二千馀人。',[],when=v,place='恒州北门及城内',note='二千余是此阶段主书叙述，与后段李谷讲话中的近三千可能范围不同，不能相加或当精确单日清点。')
add('li_gu_requests_ministers_rally','李谷请冯道、李崧、和凝到战场鼓励士卒',39,'前磁州刺史李谷','争自奋。',[('李谷','担忧战事失败，请三位官员赴战场'),('冯道','到战场安慰鼓励士卒'),('李崧','到战场安慰鼓励士卒'),('和凝','到战场安慰鼓励士卒')],when=v,place='恒州战场')
add('mada_flees_dingzhou','城外村民鼓噪后，麻答、刘晞、崔廷勋北逃定州',39,'会日暮，',None,[('麻荅','与刘晞、崔廷勋携众逃定州'),('刘晞','逃往定州'),('崔廷勋','逃往定州'),('邪律忠','在定州与逃军会合')],when='947年八月壬午日暮',place='恒州至定州',note='村民欲夺财物妇女为其行动意图，不虚构已全部夺得；忠即郎五明确同人，沿已核郎五，底本邪字保留。')
sup('mada_flees_dingzhou',39,aug,'麻答與河陽節度使崔廷勛、洛京留守劉晞，並奔定州。','《旧五代史》八月壬午同记麻答、崔廷勋、刘晞逃定州。','本纪以白再荣等概述逐军，不消除主书李筠等发动、白再荣受迫及集体作战细节。')
add('feng_declines_command','冯道安抚兵民，被推为节度使但辞让，请选武将暂领',40,'冯道等四出','宜择诸将为留后。”',[('冯道','安抚兵民，辞让节度使推举，建议选择武将留后')],when='947年八月驱逐契丹驻军后，具体日未载',place='恒州',note='被推与真正接受任命区别，冯道拒绝，不能建为他已任节度使。')
add('bai_acts_regent_requests_aid','白再荣因资位较高暂掌留后，向刘知远报告并请援',40,'时李荣功最多，','且请援兵。',[('李荣','史家记其军功最多，但未被推任留后'),('白再荣','因资位较高获推暂掌留后，并请援')],when='947年八月驱逐契丹驻军后，具体日未载',place='恒州',note='军功评价与资位选择分别记，地方权知留后区别后来朝廷正式授任乙未。')
sup('bai_acts_regent_requests_aid',40,bai,'諸軍以再榮名次在諸校之右，乃請權知留後事。','《旧五代史》也记诸军因白再荣资位在诸校之上，请他暂掌留后事务。','只录地方推举，与该书本纪八月乙未正式授任区别，不提前合并。')
add('liu_sends_li_yancong','刘知远派李彦从率兵援恒州',40,'帝遣左飞龙使','将兵赴之。',[('帝','派军增援恒州'),('李彦从','以左飞龙使身份率军前往')],when='947年八月恒州请援后，具体日未载',place='大梁至恒州')
add('wang_rao_defends_gate','王饶担忧被白再荣吞并，称病守东门自卫',40,'白再荣贪昧，','严兵自卫。',[('白再荣','猜忌诸将，造成王饶担忧'),('王饶','担忧遭吞并，诈称足疾，率兵守东门楼')],when='947年八月驱逐契丹军后，具体日未载',place='恒州东门楼',note='贪昧猜忌及恐为所并为史家记述，不推双方已正式开战。')
add('zhao_yanyi_mediates','赵延乂在白再荣与王饶之间往来劝解',40,'司天监赵延乂','始得解。',[('赵延乂','与两人交好，往来劝解'),('白再荣','与王饶之间的戒备获劝解'),('王饶','经劝解与白再荣缓和')],when='947年八月，具体日未载',place='恒州')
sup('zhao_yanyi_mediates',40,bai,'司天監趙延乂俱與之善，乃來往解釋，遂無相忌之意。','《旧五代史》同记赵延乂往来劝解白再荣与王饶。','交好不额外创建终身盟友关系。')
add('bai_extorts_ministers','白再荣派军围李崧、和凝住宅索赏，两人拿家财给军士',40,'再荣以李崧、','各以家财与之，',[('白再荣','以两人曾任宰相且家富为由，派军围宅索赏'),('李崧','交出家财给军士'),('和凝','交出家财给军士')],when='947年八月，具体日未载',place='恒州李崧、和凝住宅')
add('li_gu_stops_murder','李谷责问白再荣，阻止其杀李崧、和凝灭口',40,'又欲杀崧、','再荣惧而止。',[('白再荣','计划杀两人灭口，受李谷责问后停止'),('李谷','以军民共同出力及朝廷追责为由劝阻'),('李崧','被计划杀害，因劝阻获免'),('和凝','被计划杀害，因劝阻获免')],when='947年八月，具体日未载',place='恒州',note='杀人计划被阻止，不建成实际死亡；近三千是李谷讲话中的概数，不与上一段二千余累加。')
sup('li_gu_stops_murder',40,bai,'再榮欲害崧以利其財','《旧五代史》白再荣传记其欲杀李崧以利其财，随后李谷劝阻。','补书此处只明言欲害李崧且动机写利财，主书并言崧凝灭口；受害范围及动机分别保留。',relation='adds')
add('li_gu_stops_levy','李谷阻止白再荣征取居民财物供军',40,'又欲率民财','乃止。',[('白再荣','欲征居民财供军，后停止'),('李谷','力争阻止征财')],when='947年八月，具体日未载',place='恒州',note='欲率被阻止，不建为全城已完成征收。')
add('bai_detains_former_mada_staff','白再荣拘押曾为麻答办事的汉人以取财，被称白麻答',40,'汉人尝事麻荅者，',None,[('白再荣','拘押麻答旧属以取财，因贪虐被居民称白麻答')],when='947年八月，具体日未载',place='恒州',note='白麻答是居民对贪虐的称呼，不是另一个契丹将领或白再荣正式改名。')
sup('bai_detains_former_mada_staff',40,bai,'其漢人曾事滿達勒者盡拘之，以取其財。','《旧五代史》同记拘押曾为契丹留守办事者以取财。','补书满达勒与本文麻答译名及传内床答勒、杀北帅等表述存在问题，原文保留，未据译名推新主体死亡。')
reviews={33:'李达孺赟沿李仁达主体，弟通另建限定身份；暂掌福州、赴钱唐、加官更名、贿赂求归、同意归程分录。',34:'拒调镇与先前收到任命区别，质子父子关系明确；幽州兵与契丹援兵数量分清，张琏未强合895年同名者；剥爵讨伐按闰七月庚午。',35:'正使为由暂代转正式，郭威仍副枢密使，旧史逐人职名补明；财政建议与扩兵后的用度评价不推金额。',36:'六庙及四亲庙政治奉祀不证明两汉血缘，不造无证祖系。',37:'侵夺、诬捕杀人、帝王车服声称、馆院职掌和严刑门禁分别整理，史家评价不冒充逐案调查，杀窥门者是命令。',38:'杀催粮使、攻邢州未克、洺州守战、侵吞差额、削汉兵粮、密谋与寺钟约信分录；李荣据宋史初名证识别新李筠，与晚唐同名和李昪父分档。',39:'辛巳召赴葬礼未成行、起兵夺库、白再荣受迫、北城退守与八月壬午反攻、鼓舞、北逃分录；两千余为阶段叙述，不与后段近三千相加；邪律忠即郎五沿既有主体。',40:'冯道辞推与白再荣地方暂掌、李彦从援军、王饶自卫和赵调停、围宅取财、杀人及征财计划被阻、拘旧属取财分录；未将被阻杀人写成已死，旧传受害范围和译名问题保留。'}
assert not (P/'publication.json').exists()
for n in range(33,41):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph=Q[41]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原38—45行连续八段，本卷累计40/75；947年跨卷尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,41)],source_issues_review='张琏身份待考；李筠原名李荣据宋史确证，限定别名避免早期同名；麻答满达勒床答勒与旧传杀逐异叙待核，死亡人数引用不累加；礼庙不推血统，命令与执行分清。',plain_language_review='首次逐项核对人物、事件、参与角色、关系方向、时间地点、出处及事实说明，明确计划、被阻行动、约数、史家评价和实际结果；所有逐字摘录保留底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
