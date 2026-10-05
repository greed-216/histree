# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 paragraphs 41–44."""
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
COMMIT='b20c86dd55e2fffd503cfcda0a449be32dd9edc8'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-284-944-august-november','xinwudaishi-068-zhu-wenjin','xinwudaishi-051-yang-surrender','songshi-483-chen-hongjin-mission','xinwudaishi-009-944-january']:
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
main_sources = ['tongjian-284-944-august-november','tongjian-284-944-leap']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0944-p041-p044',
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
for n in range(41, 45):
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
        month = '十二月条下' if n==41 else '闰十二月条下'
        citation = f'卷284·后晋天福九年、后称开运元年（944；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0944_06_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','殷主':'王延政','硃文进':'朱文进','杨光远':'杨檀','杨承勋':'杨承贵','契丹主':'耶律德光','杜威':'杜重威','张从思':'张从恩','杨麟':'杨麟（杨光远判官）'})
NEW_ALIASES={'林守谅':['林守諒'],'李廷锷':['李廷鍔'],'杜进':['杜進'],'臧循':[],'张汉真':['張漢真'],'何延祚':[],'林仁翰':[],'任邈':[],'徐晏':[]}
NEW_DESCRIPTIONS={
 '林守谅':'朱文进的统军使。944年奉命与李廷锷率军攻泉州，被留从效击败后斩杀。出生年本段未载。',
 '李廷锷':'朱文进的内客省使。944年与林守谅率军攻泉州，战败后被留从效俘虏，之后结局本段未载。',
 '杜进':'殷国大将军。944年王延政派他率两万兵救泉州。与此前驻长溪的卢进名字不同，缺少同人证据，分别建档。生卒年本段未载。',
 '臧循':'南唐翰林待诏，与查文徽同乡，曾经商而熟悉福建山川。向查文徽提出攻建州方案，随后在邵武被殷军俘获，押至建州斩杀。早年经历具体年月未载。',
 '张汉真':'殷国将领。944年从镛州率八千兵将到建阳一带，查文徽获知后退回建阳。与泉州军将张汉思没有同人证据，不合并。生卒年本段未载。',
 '何延祚':'后晋客省副使。《新五代史》记李守贞派他到杨光远私宅，他命一名未具名都将杀杨光远。与此前被杀的白延祚分开。生卒年本次引文未载。',
 '林仁翰':'福州南廊承旨。944年闰十二月丁酉率部反对连重遇与朱文进，杀连重遇后号召众人杀朱文进。《新五代史》称他为裨将。生卒年本段未载。',
 '任邈':'青州掌书记。944年闰十二月乙酉因杨光远叛乱被判流放原州，诏令规定以后遇赦也不得放还。生卒年本次引文未载。',
 '徐晏':'青州支使。944年闰十二月乙酉因杨光远叛乱被判流放武州，诏令规定以后遇赦也不得放还。生卒年本次引文未载。'}
NEW_DEATH_YEARS={'林守谅':944,'臧循':944}
old='jiuwudaishi-083-944-leap';new='xinwudaishi-051-yang-surrender';minbook='xinwudaishi-068-zhu-wenjin';tang='xinwudaishi-062-min-campaign';song='songshi-483-chen-hongjin-mission';jn='xinwudaishi-009-944-january'
# 41: two opposing campaigns, a proposed operation and its first setbacks.
add('zhu_recruits_quanzhou_army','朱文进得知黄绍颇被杀，以重赏招募两万兵',41,'硃文进闻','募兵二万，',[('硃文进','因黄绍颇被杀而惧怕，招募两万兵')],when='944年十二月条下，泉州政变后',place='福州',note='两万是史书记载的募兵数，不写成实到战场人数；黄绍颇之死沿用已录事实。')
add('lin_li_attack_quanzhou','朱文进派林守谅、李廷锷率军攻泉州',41,'遣统军使林守谅、','五百里。',[('硃文进','派两名将领领兵攻泉州'),('林守谅','以统军使身份率军攻泉州'),('李廷锷','以内客省使身份率军攻泉州')],when='944年十二月条下',place='福州至泉州',note='钲鼓相闻五百里为书内声势描写，不据此画精确行军路线。')
add('du_jin_relief_quanzhou','王延政派杜进率两万兵救援泉州',41,'殷主延政遣大将军杜进','救泉州，',[('殷主','派杜进率两万兵救泉州'),('杜进','以大将军身份率两万兵赴泉州救援')],when='944年十二月条下',place='建州至泉州',note='杜进与卢进没有同人证据，分别记录；不将两军兵数相加称为同一阵营人数。')
add('liu_congxiao_defeats_fuzhou','留从效打开泉州城门出战，大败福州军',41,'留从效开门','大破之，',[('留从效','打开泉州城门，与福州军交战并将其击败')],when='944年十二月条下',place='泉州')
add('lin_shouliang_killed','林守谅在泉州军败后被斩杀',41,'斩守谅，','斩守谅，',[('林守谅','在泉州战败后被斩杀'),('留从效','斩杀来攻泉州的林守谅')],when='944年十二月条下',place='泉州')
add('li_tinge_captured','李廷锷在泉州军败后被俘',41,'执廷锷。','执廷锷。',[('李廷锷','在泉州军败后被俘'),('留从效','俘获李廷锷')],when='944年十二月条下',place='泉州',note='被俘不同于斩杀，不将李廷锷提前记为死亡。')
add('wu_chengyi_fleet_fuzhou','王延政派吴成义率千艘战舰攻福州',41,'延政遣统军使吴成义','攻福州，',[('殷主','派吴成义领战舰攻福州'),('吴成义','以统军使身份率千艘战舰攻福州')],when='944年十二月条下',place='福州',note='千艘为原书记载，未核实际可用舰数；此处是出兵，不提前写福州已经归降。')
add('zhu_sends_hostages_wuyue','朱文进将子弟送到吴越作人质，请求救援',41,'硃文进遣子弟','以求救。',[('硃文进','送子弟为人质，向吴越求援')],when='944年十二月条下',place='福州至吴越',note='子弟未具名，不虚构人物；请求救援不等于吴越已经出兵。')
add('zang_xun_proposes_jianzhou','臧循凭经商时的地理经验，向查文徽提出攻建州方案',41,'初，唐翰林待诏臧循，','之策。',[('臧循','凭熟悉福建山川的经历向查文徽提出攻建州方案'),('查文徽','得到同乡臧循提出的攻建州方案')],when='此前，具体年月未载',year=None,place='南唐',note='初字追述，昔为商人与同乡不写成血亲、正式盟友关系。')
add('cha_requests_attack_yin','查文徽上表请求攻王延政，多人认为不宜出兵',41,'文徽表请','不可。',[('查文徽','向李璟上表请求进攻王延政'),('殷主','成为查文徽请求进攻的对象')],when='944年十二月出兵前，具体日未载',place='南唐至殷国',note='国人多反对但没有具名，不补反对者名单。')
add('li_jing_orders_border_recon','李璟任查文徽为江西安抚使，命其巡视边境侦察',41,'唐主以文徽为江西安抚使，','可否；',[('唐主','任命查文徽并派他巡视边境，侦察攻殷是否可行'),('查文徽','任江西安抚使，巡视边境侦察')],when='944年十二月条下，正式出兵之前',place='江西与殷国边境')
add('cha_reports_can_capture','查文徽到信州后奏称攻殷必胜',41,'文徽至信州，','必克。',[('查文徽','在信州奏称进攻殷国必能取胜'),('唐主','收到查文徽的出兵建议')],when='944年十二月条下',place='信州',note='必克是查文徽的判断，不当成当时已经胜利。')
add('bian_gao_campaign_command','李璟任边镐为行营招讨诸军都虞候，随查文徽攻殷',41,'唐主以洪州营屯都虞候边镐','伐殷。',[('唐主','任命边镐并派其随查文徽进攻殷国'),('边镐','由洪州营屯都虞候任行营招讨诸军都虞候，率军随查文徽攻殷'),('查文徽','领军攻殷，边镐率兵跟随')],when='944年十二月条下',place='南唐至殷国')
sup('bian_gao_campaign_command',41,tang,'景因其亂遣查文徽及待詔臧循發兵攻建州。','《新五代史》也记李璟利用闽国内乱，派查文徽、待诏臧循领兵攻建州。','补具名臧循；本段先后和其他纪日不覆盖主书，建州后来陷落不提前录。',relation='adds')
add('cha_advances_gaizhu','查文徽从建阳进军，驻盖竹',41,'文徽自建阳','盖竹，',[('查文徽','从建阳进军盖竹并驻扎')],when='944年十二月条下',place='建阳至盖竹')
add('cha_hears_yin_reinforcements','查文徽获知三州归殷，张汉真率八千兵即将到来',41,'闻漳、泉、汀三州','将至，',[('查文徽','获知三州归殷和殷军援兵将到'),('张汉真','从镛州率八千兵将到')],when='944年十二月条下',place='盖竹、镛州',note='原文皆隆于殷疑为降的转录问题，原字保留；三州归附有前段与新史相应记载。张汉真与张汉思不合并，将至不改成已交战。')
sup('cha_hears_yin_reinforcements',41,minbook,'文縝懼，以汀州降于延政。延政已得三州，','《新五代史》记王延政已得泉、漳、汀三州，支持此处三州归附殷国的理解。','只补归附背景，不新建三州各自重复归降事件；不据此改写主书原字。')
add('cha_retreats_jianyang','查文徽因惧怕殷军退回建阳',41,'文徽惧，','建阳。',[('查文徽','获知殷军将到后退回建阳')],when='944年十二月条下',place='盖竹至建阳')
add('zang_xun_shaowu_captured','邵武居民引导殷军袭击臧循驻军，臧循被俘',41,'臧循屯邵武，','循军，执循',[('臧循','驻军邵武，部队被殷军袭破，自己被俘')],when='944年十二月条下',place='邵武',note='引路居民和殷军执行者未具名，不补其身份或军数。')
add('zang_xun_executed','臧循被押送建州斩杀',41,'执循送','斩之。',[('臧循','被殷军押至建州斩杀')],when='944年十二月条下，具体日未载',place='邵武至建州')
# 42: secret execution, a false report, and related pardons and dispositions.
add('jin_delegates_yang_execution','后晋朝廷命李守贞自行处置杨光远',42,'朝廷以','便宜从事。',[('帝','因杨光远诸子已投降，命李守贞自行处置杨光远'),('李守贞','获命自行处置杨光远'),('杨光远','成为朝廷命李守贞处置的对象')],when='944年闰十二月癸酉前，具体日未载',place='后晋朝廷至青州',note='便宜从事是授予处置权；不写成公开颁布斩首诏书。')
sup('jin_delegates_yang_execution',42,old,'帝以光遠頃歲太原歸命，欲曲全之，議者曰：「豈有反狀滔天而赦之也！」乃命守貞便宜處置。','《旧五代史》记石重贵因杨光远早年在太原归附而想保全他，但议者反对，最终命李守贞自行处置。','皇帝保护意图和议者反对分别有归属，不解释成所有官员都明确具名反对。',relation='adds')
extra('jin_promises_yang_survival','石重贵曾赐诏杨光远，承诺不杀他',42,new,'賜光遠詔書，許以不死，羣臣皆以為不可，乃敕李守貞便宜處置。',[('帝','曾以诏书承诺杨光远不死，后因群臣反对改变处置'),('杨光远','曾得到皇帝不杀的承诺')],when='944年青州归降后、被杀前，传记未列月日',place='后晋朝廷至青州',note='本事件记录先前承诺，随后被杀是另一阶段；不可把承诺写成最终免死结果。')
add('li_shouzhen_enters_qingzhou_leap','李守贞于闰月癸酉进入青州',42,'闰月，癸酉，','入青州，',[('李守贞','于闰月癸酉进入青州')],when='944年闰十二月癸酉',place='青州',note='此前开城纳军与本句李守贞入城分开；旧本纪癸酉为死亡奏报日，不强证同为入城日。')
add('yang_guangyuan_killed','李守贞派人到别宅杀死杨光远',42,'遣人拉杀','于别第，',[('李守贞','派人杀死杨光远'),('杨光远','在别宅被李守贞派人杀死')],when='944年闰十二月癸酉条下；《旧五代史》癸酉为奏报日',place='青州别宅',note='不把因掩饰而报病死写成自然死亡；主书记时与旧史奏报日分列。')
sup('yang_guangyuan_killed',42,old,'癸酉，李守貞奏，楊光遠卒。','《旧五代史》把癸酉记作李守贞奏报杨光远去世的日期。','奏报日不能自动等同实际杀害日。',relation='adds',field='time_original')
sup('yang_guangyuan_killed',42,new,'守貞遣客省副使何延祚殺之于其家。延祚至其第，光遠方閱馬于廐，延祚使一都將入','《新五代史》记李守贞派客省副使何延祚到杨光远宅中，由何延祚命一名都将入内执行。','补具名负责使者，实际都将未具名；与旧史所引欧阳史内容不能算成第二份独立证据。',relation='adds')
person('何延祚',42,'受李守贞派遣，到杨光远家中命一名都将执行杀害','守貞遣客省副使何延祚殺之于其家。延祚至其第，光遠方閱馬于廐，延祚使一都將入',source=new)
edge='participation_zztj_284_0944_yang_guangyuan_killed_person_何延祚';B['person_events'].append(dict(key=edge,person_key=people['何延祚'],event_key=E['yang_guangyuan_killed'],role='受李守贞派遣，命一名都将杀杨光远',status='draft'));claim('person_event',edge,'role','何延祚受李守贞派遣，命一名都将杀杨光远。',42,'守貞遣客省副使何延祚殺之于其家。延祚至其第，光遠方閱馬于廐，延祚使一都將入','新史具名使者的独立补充；未具名都将不另造姓名。',source=new)
add('li_falsely_reports_yang_illness','李守贞将杨光远被杀掩报为病死',42,'以病死闻。','以病死闻。',[('李守贞','向朝廷掩报杨光远死于疾病'),('杨光远','被杀后被掩报为病死')],when='944年闰十二月癸酉条下',place='青州至后晋朝廷',note='病死只是奏报说法，史书叙述实际为被杀。')
sup('li_falsely_reports_yang_illness',42,old,'守貞遣人拉殺之，以病卒聞。','《旧五代史》也记李守贞派人杀害杨光远，却上报为病死。','与真实死因分清。')
add('yang_chengxun_ruzhou','后晋起复杨承勋，任他为汝州防御使',42,'丙戌，','防御使。',[('帝','起复杨承勋，任他为汝州防御使'),('杨承勋','获起复，出任汝州防御使')],when='944年闰十二月丙戌',place='后晋朝廷、汝州',note='承勋是杨承贵的后名，复用同一稳定主体；起复保留制度名称，不补原文未列服丧起始日。')
sup('yang_chengxun_ruzhou',42,old,'丙戌，降青州為防禦使額，以萊州刺史楊承勛為汝州防禦使。','《旧五代史》同记丙戌由莱州刺史杨承勋任汝州防御使。','杨承勋初名已由前段本传证明；职务变更不另建同人。')
for code,name,office in [('chengxin','杨承信','右羽林将军'),('chengzuo','杨承祚','右骁骑卫将军')]:
 extra('jin_appoints_'+code,'后晋任'+name+'为'+office,42,old,'閏月庚午，以楊承信為右羽林將軍，承祚為右驍騎衛將軍。皆光遠之子，先詣闕請罪，故特授是官。',[(name,'因此前入朝请罪，获任'+office),('帝','因杨光远之子来朝请罪而任官')],when='944年闰十二月庚午',place='后晋朝廷',note='此前来朝请罪的具体日未载，此处只录庚午任命，不创造同时来朝日。')
extra('zhang_wandi_executed','后晋削夺张万迪官爵并处斩',42,old,'乙酉，前登州刺史張萬迪削奪官爵處斬，',[('张万迪','因参与杨光远叛乱被削夺官爵、处斩')],when='944年闰十二月乙酉',place='后晋',note='这一处罚原因由同段并以杨光远叛故支持；执行地点本句未载。')
for code,name,place,quote in [('yanglin','杨麟','威州','青州節度判官楊麟配流威州，'),('renmiao','任邈','原州','掌書記任邈配流原州，'),('xuyan','徐晏','武州','支使徐晏配流武州。')]:
 extra('jin_exiles_'+code,'后晋判'+name+'流放'+place,42,old,quote,[(name,'因杨光远叛乱被判流放'+place)],when='944年闰十二月乙酉',place=place,note='与同段处罚时间相连；判配流不自行补到达目的地日。杨麟复用身份限定主体。')
 sup('jin_exiles_'+code,42,old,'縱逢恩赦，不在放還之限，並以楊光遠叛故也。','这些被流放者因杨光远叛乱受罚，诏令规定即使以后遇赦也不得放还。','处罚原因与特别限制适用于同段被流放者，不能写成后续真的遇赦或返回。',relation='adds')
extra('jin_pardons_qingzhou','后晋赦青州辖区罪人，对被杨光远牵连的吏民不予追究',42,old,'曲赦青州管內罪人，立功將士各賜優給，青州吏民為楊光遠詿誤者，一切不問。',[('帝','赦免青州辖区罪人，赏立功将士，不追究被牵连吏民')],when='944年闰十二月乙酉相关处置条下，未逐项列日',place='青州',note='赦免普通辖区罪人与不予放还的具名叛党范围不同，不概括成所有人皆获赦。')
sup('jin_pardons_qingzhou',42,jn,'閏月乙酉，德音赦青州囚。','《新五代史》将赦青州囚明确记在闰月乙酉。','该书有具体赦囚纪日，不把所有赏官事件都套此日。',relation='adds',field='time_original')
extra('li_shouzhen_chancellor_title','后晋授李守贞同平章事',42,old,'青州行營招討使、兗州節度使兼侍衛都虞候李守貞加同平章事，',[('李守贞','平青州后获加同平章事')],when='944年闰十二月青州平定后的授官条下，确日未单列',place='后晋朝廷')
extra('fu_yanqing_xuzhou_command','后晋改任符彦卿为许州节度使',42,old,'副招討使、河陽節度使符彥卿改許州節度使。',[('符彦卿','由河阳节度使改任许州节度使')],when='944年闰十二月授官条下，确日未单列',place='河阳至许州',note='许州不同于徐州，不混淆地点。')
extra('qingzhou_defense_rank','后晋将青州降为防御使军额',42,old,'丙戌，降青州為防禦使額，',[],when='944年闰十二月丙戌',place='青州',note='军额变化不解释成驻军兵员减少的具体人数。')
extra('di_guangye_qingzhou','后晋任翟光邺为青州防御使',42,old,'以宣徽使翟光鄴為青州防禦使，',[('翟光邺','由宣徽使任青州防御使')],when='944年闰十二月癸巳',place='青州',note='时间依据同段癸巳任官句，不套前面的丙戌。')
# 43: the misleading message and two incompatible accounts of the coup.
add('wu_falsely_claims_tang_support','吴成义谎称南唐大军是来助殷国讨朱文进的',43,'殷吴成义闻','益惧。',[('吴成义','得知南唐军到来，谎称其协助殷国讨敌，使福州更恐惧')],when='944年闰十二月条下',place='福州',note='南唐实际攻殷，吴成义所说是欺骗消息，不建立南唐殷国军事同盟。')
sup('wu_falsely_claims_tang_support',43,tang,'延政聞唐且攻之，遣人紿福州曰：「唐兵助我討賊矣。」','《新五代史》将谎称南唐助讨的遣人者记为王延政。','主书写吴成义，本书写王延政，分别保留具体行动者，未据省略推断两人必共同策划。',relation='conflicts')
add('zhu_sends_state_seal_yin','朱文进派李光准等将国宝送给殷国',43,'乙未，','于殷。',[('硃文进','派李光准等向殷国送国宝'),('李光准','以同平章事身份奉国宝出使殷国')],when='944年闰十二月乙未',place='福州至建州',note='奉国宝是使者行动与归顺表示，不补朱文进本人到建州或王延政已接受的结论。')
add('lin_renhan_calls_followers','林仁翰以世代事王氏号召部属反对朱文进、连重遇',43,'丁酉，','何面见之！”',[('林仁翰','号召部属摆脱朱文进与连重遇，称世代事奉王氏')],when='944年闰十二月丁酉',place='福州',note='政治效忠话语不建林氏与王氏血亲关系。')
add('lin_renhan_attacks_lian_house','林仁翰率三十人到连重遇宅中，多名随从见防卫严密而逃',43,'帅其徒三十人','遁去。',[('林仁翰','率三十名披甲部属奔向连重遇宅中'),('连重遇','严密设兵自卫，使一些来攻者逃离')],when='944年闰十二月丁酉',place='福州连重遇宅',note='三十是起行人数，部分逃走后的实战人数未载，不写三十人全数战斗。')
add('lin_renhan_kills_lian','林仁翰持槊刺死连重遇，并斩首示众',43,'仁翰执槊','以示众曰：',[('林仁翰','持槊刺杀连重遇并斩首示众'),('连重遇','被林仁翰刺杀')],when='944年闰十二月丁酉',place='福州',note='这是主书先杀连重遇的顺序，另外两书记先杀朱文进，异说并列不强行调和。')
sup('lin_renhan_kills_lian',43,minbook,'重遇亦殺文進，傳首建州以自歸。福州裨將林仁翰又殺重遇，','《新五代史》记连重遇先杀朱文进、传首建州归降，林仁翰随后杀连重遇。','杀连重遇者林仁翰一致，但先后及朱文进行凶者与主书不同，保留异说。',relation='conflicts')
add('lin_renhan_urges_zhu_execution','林仁翰展示连重遇首级，号召众人杀朱文进赎罪',43,'“富沙王且至，','踊跃从之，',[('林仁翰','以王延政将至和赎罪为说辞，号召众人杀朱文进'),('硃文进','成为林仁翰号召众人杀害的目标')],when='944年闰十二月丁酉',place='福州',note='将至及族灭威胁属于动员言辞，不录成王延政本人已经到福州或全城随后被族灭。')
add('fuzhou_crowd_kills_zhu','福州众人响应林仁翰，杀死朱文进',43,'众踊跃从之，','遂斩文进，',[('硃文进','被响应林仁翰的众人杀死'),('林仁翰','号召众人后，众人杀死朱文进')],when='944年闰十二月丁酉',place='福州',note='主书没有明确说林仁翰亲自斩杀朱文进，不把号召者写成唯一执行者。')
sup('fuzhou_crowd_kills_zhu',43,minbook,'重遇亦殺文進，傳首建州以自歸。','《新五代史》记朱文进由连重遇杀害，并由连重遇送首建州归降。','这是另一个行凶者与先后顺序的版本，与主书并列，未建确定的第二次死亡事件。',relation='conflicts')
sup('fuzhou_crowd_kills_zhu',43,song,'連重遇殺朱文進，傳首建州，福人又殺重遇，','《宋史》陈洪进传也写连重遇先杀朱文进，福州人后杀连重遇。','该叙述与新史接近，可能有史源依赖，不能当作两份独立证据裁定主书错误。',relation='conflicts')
add('wu_chengyi_enters_fuzhou','福州人迎吴成义入城',43,'迎吴成义','入城，',[('吴成义','在朱文进、连重遇被杀后受到迎接，进入福州')],when='944年闰十二月丁酉条下',place='福州',note='进入的是吴成义，不把王延政写成亲到福州。')
add('zhu_lian_heads_sent_jianzhou','福州方面将朱文进、连重遇首级装匣送建州',43,'函二首','送建州。',[],when='944年闰十二月丁酉条下',place='福州至建州',note='递送者未具名，不补林仁翰本人赴建州；此前送国宝是另一使行。')
extra('lin_plans_yanzheng_fuzhou_capital','林仁翰等谋迎王延政以福州为都',43,minbook,'福州裨將林仁翰又殺重遇，謀迎延政都福州。',[('林仁翰','在杀连重遇后计划迎王延政以福州为都'),('殷主','成为林仁翰计划迎接的君主')],when='944年福州政变之后，传记未列日',place='福州',note='谋迎为计划，不将迎吴成义入城或之后迁都说成当日王延政实际到城。')
extra('chen_returns_quanzhou_after_coup','王延政在福州政变后派陈洪进返回泉州',43,song,'連重遇殺朱文進，傳首建州，福人又殺重遇，延政遂遣洪進歸泉州。',[('殷主','派陈洪进返回泉州'),('陈洪进','奉王延政之命返回泉州')],when='944年福州政变后，宋史未列月日',place='建州至泉州',note='宋史归泉州行动独立补充，之前泉州使行复用既有主体，不补确切到达日。')
# 44: renewed Khitan advance and a disordered Jin retreat.
add('zhao_yanshou_leads_advance','契丹再次大举南下，赵延寿率先领兵进攻',44,'契丹复大举','先进。',[('赵延寿','以卢龙节度使身份率兵先行进攻'),('契丹主','组织契丹再度大举进攻后晋')],when='944年闰十二月条下',place='契丹至后晋河北')
add('du_wei_requests_help_xingzhou','契丹前锋到邢州，杜重威遣使抄小路告急',44,'契丹前锋','告急。',[('杜威','契丹前锋到邢州后，派使者抄小路向朝廷告急')],when='944年闰十二月条下',place='邢州至后晋朝廷',note='主书避石重贵名写杜威，复用杜重威；不把间道解释成与敌方串通。')
add('shi_illness_blocks_personal_command','石重贵想亲自领军抵抗契丹，因患病未能成行',44,'帝欲自将','有疾，',[('帝','想亲领军抵抗契丹，但恰逢患病')],when='944年闰十二月条下',place='后晋朝廷',note='没有病名、治疗或精确病程，不补医疗诊断。')
add('jin_sends_three_commands_xingzhou','石重贵命张从恩、马全节、安审琦会兵驻邢州',44,'命天平节度使','屯邢州，',[('帝','命三名将领会合各道兵马屯驻邢州'),('张从思','以天平节度使身份受命会兵驻邢州'),('马全节','以邺都留守身份受命会兵驻邢州'),('安审琦','以护国节度使身份受命会兵驻邢州')],when='944年闰十二月条下',place='邢州',note='本句张从思与本段从恩不一致；旧本纪同次派军明写张从恩，与其既有天平节度使身份连续，沿用张从恩，不将疑字列为确定别名。')
sup('jin_sends_three_commands_xingzhou',44,old,'詔張從恩、馬全節、安審琦率師屯邢州，趙在禮屯鄴都。','《旧五代史》同次派军明确写张从恩、马全节、安审琦驻邢州。','旧本纪与主书后句从恩及此前任官相合，作为识别张从恩的书证；原文张从思保留，纸本字形待核。')
add('zhao_zaili_troops_yedu','石重贵命赵在礼驻军邺都',44,'武宁节度使赵在礼','屯鄴都。',[('帝','命赵在礼驻军邺都'),('赵在礼','以武宁节度使身份屯兵邺都')],when='944年闰十二月条下',place='邺都')
add('khitan_headquarters_yuanshi','耶律德光率大军随后到达，在元氏设军中驻地',44,'契丹主以大兵','于元氏。',[('契丹主','领大军跟进，在元氏设立军中指挥驻地')],when='944年闰十二月条下',place='元氏',note='建牙指设置军中驻地，不理解为另建一座政治都城。')
sup('khitan_headquarters_yuanshi',44,old,'是月，契丹耶律德光與趙延壽領全軍入寇，圍恒州，分兵陷鼓城、槁城、元氏、高邑、昭慶、寧晉、蒲澤、欒城、柏鄉等縣，前鋒至邢州，河北諸州告急。','《旧五代史》也记闰月耶律德光与赵延寿领军进攻，围恒州并分兵攻陷多县，前锋到邢州。','围城、县城陷落和元氏设牙是不同事实；县名槁城原字保留，坐标待核。',relation='adds')
extra('khitan_besieges_hengzhou_leap','契丹军在闰月围攻恒州',44,old,'契丹耶律德光與趙延壽領全軍入寇，圍恒州，',[('契丹主','与赵延寿率军围恒州'),('赵延寿','与耶律德光领军围恒州')],when='944年闰十二月，具体日未列',place='恒州',note='围城不自动写成恒州已经陷落。')
sup('khitan_besieges_hengzhou_leap',44,jn,'契丹寇恆州。','《新五代史》也在闰月条下记契丹进攻恒州。','寇不单独证明城已攻克。')
extra('khitan_takes_hebei_counties','契丹分兵攻陷鼓城、元氏等县',44,old,'分兵陷鼓城、槁城、元氏、高邑、昭慶、寧晉、蒲澤、欒城、柏鄉等縣，',[],when='944年闰十二月，具体日未列',place='鼓城、槁城、元氏、高邑、昭庆、宁晋、蒲泽、栾城、柏乡',note='九个具名县分别保留，等字不能推总数正好九县；槁城字形和蒲泽地名待核，未自动定位。')
add('jin_orders_partial_retreat','后晋朝廷畏惧契丹军势，命张从恩等稍退',44,'朝廷惮','稍却，',[('帝','因畏惧契丹军势，下诏让张从恩等稍向后撤'),('张从恩','收到稍退的诏令')],when='944年闰十二月条下',place='邢州方向至相州',note='稍却是退兵命令，不写成皇帝命令士兵焚掠百姓。')
add('jin_retreat_disorder_plunder','后晋军退向相州时惊慌溃乱，弃甲并沿途焚掠',44,'于是诸军','不复能整。',[('张从恩','其所领诸军退却后失去队列，至相州仍无法整顿')],when='944年闰十二月退兵时',place='退军沿途至相州',note='焚掠为军队行为，没有具名亲自焚掠者，不向马全节或安审琦虚构个人行凶事实；结局是不整顿，不是全军被契丹歼灭。')
for name,quote in [('林守谅','斩守谅，'),('臧循','执循送建州斩之。')]:
 claim('person',people[name],'death_year',name+'于944年被杀。',41,quote,'本段属于944年末连续叙事，死亡明载；没有确切日，不补公历日期。')
reviews={41:'区分泉州攻防、吴成义攻福州与南唐攻殷。求救、奏言必克、援兵将至不作已执行结果。初追述臧循早年留空年；卢进杜进、张汉思张汉真分别建档，隆字疑转录保留并用归附书证说明。',42:'处置授权、既有免死承诺、入城、杀害、假报病死、起复及平青州后任官处罚分开。主书癸酉条下与旧本纪奏报癸酉分别保留，何延祚由新史具名，都将匿名。杨承勋复用杨承贵主体。',43:'唐助我为吴成义欺骗消息，新史将遣人者写王延政；主书先杀连后杀朱，新史宋史反序及朱杀害者异说分别列出，不另造两次死亡。不把号召者推为唯一行刑者，不把谋迎王延政当实际入城。',44:'张从思疑字按同次旧本纪及后句从恩识别张从恩，原字保留不加确定别名。杜威复用杜重威；军队驻地、围城、县陷与稍退溃乱区分，弃甲焚掠不补个人凶手或全军歼灭。'}
assert not (P/'publication.json').exists()
for n in range(41,45):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=944,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(41,45)],next_paragraph='zztj-v284-y0945-p001',next_volume=284,next_year=945,supplements=supplements,excluded_non_body=[],coverage='卷284原46—49行连续末4段，十二月及闰十二月；本批验证发布后944年两卷55正文全部处理。卷284还包含945年，不标整卷完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'本次只处理第41段，前文已发布不重复建事件。'),(main_sources[1],'只录944年第42—44段；快照内945年首段留后续。'),(tang,'只补攻建州与诈称援军，后文945—946年福州和泉州变局留后续；保大二年二月杀王纪日异于主书，未覆盖已发表纪日。'),(new,'本次补光远被杀、免死承诺与具名使者，前次囚父与诛党不重建。'),(song,'只补当前福州政变异说与陈洪进返回，后文南唐取建州和泉州归附留后续。')]],source_issues_review='张从思与张从恩、皆隆于殷疑字原字保留；福州政变先后、朱文进行凶者及诈称唐援的遣人者存在异说。癸酉主书条下杀害与旧史奏报日期不强合。新史和宋史近似叙述不作为相互独立确证。纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(41,45)],plain_language_review='首次逐条阅读全部标题、人物说明、事件正文、参与角色、时间解释和事实引用；主语明确，命令计划、假消息、死亡及奏报分开。解释简体，逐字摘录保持底本。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
