# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 945 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,57))
COMMIT='b581496bddc409a2722727b001b6e1fbe269b9b0'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-946-february-june','jiuwudaishi-084-946-june']:
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
main_sources = ['tongjian-285-946-february-june','tongjian-285-946-july-august']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p009-p016',
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
for n in range(9, 17):
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
        citation = f'卷285·后晋开运二年（946年六月至八月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=946, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='946年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_285_0946_' + code
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
        edge = 'participation_zztj_285_0946_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_285_0946_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','李弘义':'李仁达','杜威':'杜重威','李彦韬':'李彦韬（后晋宣徽使）','解里':'解里（946年契丹将）'})
NEW_ALIASES={'李殷':[],'王彦超':['王彥超'],'白延遇':[],'解里（946年契丹将）':['解里','解裏'],'白可久':[],'白铁匮':['白鐵匱'],'赫连海龙':['赫連海龍'],'王义宗':['王義宗']}
NEW_DESCRIPTIONS={'李殷':'蓟人，后晋义武节度使。946年六月受任北面行营步军都指挥使兼都排阵使。生卒年未载；与后周王殷分为不同主体。','王彦超':'临清人，后晋护圣指挥使。946年六月受命与白延遇带所属十营兵赴邢州。生卒年未载。','白延遇':'太原人，后晋护圣指挥使。946年六月受命与王彦超带所属十营兵赴邢州。生卒年未载；不与皇甫遇等姓名相近将领混同。','解里（946年契丹将）':'946年八月，李守贞报告在长城以北与契丹军交战，并斩杀酋帅解里。《旧五代史》写作解里相公。与945年狼山战记的谐里是否同一人尚未核实，暂按本次身份记录，不因近似译名合并。出生年未载。','白可久':'吐谷浑部落首领，史书记其地位次于白承福。带所属部众先逃往契丹，受任云州观察使；契丹试图借他招引白承福。具体逃归年月与生卒年未载。','白铁匮':'《旧五代史》晋少帝本纪记为吐谷浑大首领，刘知远在946年八月奏报与白承福、赫连海龙等一起被杀，其族亦遭杀害。处置与奏报日期须区分，生年未载。','赫连海龙':'《旧五代史》晋少帝本纪记为吐谷浑大首领，946年八月刘知远奏报其与白承福、白铁匮等被杀并夷族。不同史书对这一处置的纪月有异说，生年未载。','王义宗':'《旧五代史》汉高祖本纪记为吐谷浑别部首领，刘知远杀白承福等五族之后，命他统领其余部众。该书记在946年五月，其他史书把诛杀放在八月；不同纪月分别保留。生卒、所属别部具体名称未载。'}
NEW_DEATH_YEARS={'白铁匮':946,'赫连海龙':946,'解里（946年契丹将）':946}
june='946年六月条下，具体日未载';july='946年七月条下，具体日未载';aug='946年八月条下，具体日未载';past='946年相应记事以前的追述，具体年月未载'
feng='xinwudaishi-049-feng-hui-horses';oj='jiuwudaishi-084-946-june';oy='jiuwudaishi-084-946-july';oa='jiuwudaishi-084-946-august';oz='jiuwudaishi-084-946-zhao-correspondence';cj='xinwudaishi-062-chen-jue-fuzhou';nh='xinwudaishi-010-bai-chengfu-death';oh='jiuwudaishi-099-bai-chengfu-death'
# 9: retrospective offices versus dated return.
add('feng_hui_buys_horses','冯晖在灵武赢得羌胡信任，一年买马达五千匹',9,'初，','五千匹，',[('冯晖','镇灵武时赢得羌胡信任，并在一年内买到五千匹马')],when=past,year=None,place='灵武',note='期年表示一年时长，不据此反推具体开始年。')
sup('feng_hui_buys_horses',9,feng,'彥超既留，而諸部族爭以羊馬為市易，期年有馬五千匹。','《新五代史》记拓跋彦超被留后，诸部族争着用羊马交易，一年取得五千匹马。','補交易背景，不重复前批留拓跋事件，也不把交易量改为战斗所得。',relation='adds')
add('jin_suspects_feng','后晋朝廷猜忌冯晖，把他调到邠州、陕州',9,'朝廷忌之，','陕州，',[('冯晖','因朝廷猜忌，先后调任邠州、陕州')],when=past,year=None,place='灵武至邠州、陕州',note='两处调任的独立年月未在本句给出，不凑成同一天两职。')
sup('jin_suspects_feng',9,feng,'晉見暉馬多而得夷心，反以為患，徙鎮靜難，又徙保義。','《新五代史》记后晋因冯晖马多且获部众归心而猜忌，先后调他到静难、保义。','静难对应邠州、保义对应陕州，作为军镇与州名的同事补证，不造新的两次不同调任。')
add('feng_enters_guard_command','冯晖入朝任侍卫步军都指挥使，并领河阳节度使',9,'入为','河阳节度使。',[('冯晖','入朝掌侍卫步军，兼领河阳节度使')],when=past,year=None,place='后晋朝廷；领河阳',note='领节度使不等于已亲赴河阳坐镇，原文入为与领分别表达。')
sup('feng_enters_guard_command',9,feng,'歲中，召為侍衞步軍都指揮使，領河陽節度使，暉於是始覺晉有患己意。','《新五代史》同记冯晖被召为侍卫步军都指挥使、领河阳，并察觉朝廷猜忌。','岁中没有独立年号，时间保持未定，不直接套946任命日。')
add('feng_seeks_return','冯晖后悔离开灵武，厚事冯玉、李彦韬，请求回镇灵州',9,'晖知','灵州。',[('冯晖','后悔离灵武，向冯玉、李彦韬求复镇'),('冯玉','受到冯晖厚事并被请求协助复镇'),('李彦韬','受到冯晖厚事并被请求协助复镇')],when='946年六月复任以前，具体年月未载',year=None,place='后晋朝廷',note='厚事不擅补行贿金额，李彦韬复用后晋主体，不误合温韬。')
add('feng_reappointed_shuofang','朝廷因羌胡侵扰，再任冯晖为朔方节度使，令他率关西兵迎击',9,'朝廷亦','羌、胡；',[('冯晖','再次获任朔方节度使，率关西兵应对羌胡侵扰')],when='946年六月丙寅',place='关西至朔方',note='复任与已打胜仗有别，本段只有任命和率兵任务；不提前下文辉德战事。')
sup('feng_reappointed_shuofang',9,oj,'丙寅，以前昭義軍節度使李從敏為河陽節度使，以河陽節度使兼侍衛步軍都指揮使馮暉為靈州節度使。','《旧五代史》同记六月丙寅冯晖由河阳兼侍卫步军改任灵州节度使。','灵州与朔方军镇对应，冯晖原职和纪日一致；李从敏任河阳只作上下文，不提前构造不相关官命。')
add('yao_campaign_commander','药元福以威州刺史身份任行营马步军都指挥使',9,'以威州',None,[('药元福','由威州刺史受任行营马步军都指挥使')],when='946年六月丙寅条下',place='威州至朔方行营',note='未把新军职改成已获胜战功。')
# 10.
add('dingzhou_reports_khitan','定州奏报契丹集兵压境',10,'乙丑，','压境。',[],when='946年六月乙丑',place='定州至后晋朝廷',note='是地方奏报，实际集结开始日未载。')
for code,title,start,end,actors in [
 ('li_shouzhen_north_command','李守贞任北面行营都部署','诏以','都部署，',[('李守贞','以天平节度使、侍卫马步都指挥使身份任北面行营都部署')]),
 ('huangfu_north_deputy','皇甫遇任北面行营副都部署','义成节度','副之；',[('皇甫遇','以义成节度使身份任北面行营副职')]),
 ('zhang_north_cavalry','张彦泽任行营马军都指挥使兼都虞候','彰德节度','都虞候，',[('张彦泽','以彰德节度使身份掌行营马军兼都虞候')]),
 ('li_yin_north_infantry','李殷任行营步军都指挥使兼都排阵使','义武节度','排阵使；',[('李殷','以义武节度使身份掌行营步军兼都排阵使')])]:
 add(code,title,10,start,end,actors,when='946年六月定州奏报后，诏令独立日未载',place='后晋北面行营')
old_q='定州奏，蕃寇壓境。詔李守貞為北面行營都部署，滑州皇甫遇為副，相州張彥澤充馬軍都指揮使，定州李殷充步軍都指揮使。'
for code in ['li_shouzhen_north_command','huangfu_north_deputy','zhang_north_cavalry','li_yin_north_infantry']:
 sup(code,10,oj,old_q,'《旧五代史》六月也记定州告警后，由李守贞、皇甫遇、张彦泽、李殷分别任北面部署、副职、马军和步军指挥。','该本纪此句承壬午附近叙述而未单给乙丑，主书乙丑保留为定州奏报日，不将两书强合为同日任命。')
add('wang_bai_ten_camps','王彦超、白延遇率所属十营兵赴邢州',10,'遣护圣','邢州。',[('王彦超','率部兵与白延遇赴邢州'),('白延遇','率部兵与王彦超赴邢州')],when=june,place='赴邢州',note='十营为二人所带部兵总叙，不乘成每人十营或换为确切人数。')
add('li_yantao_monitors_shouzhen','李彦韬轻视李守贞，并掌握他在外的大小事务',10,'时马军','知之，',[('李彦韬','以马军都指挥使、镇安节度使身份用事，轻视并掌握李守贞外任事务'),('李守贞','在外大小事务均被李彦韬知晓')],when='946年六月条附叙两人关系，具体起止未载',place='后晋朝廷及行营',note='监知为史文所述权势状态，不造具体谍报机关或监控技术。')
add('shouzhen_conceals_resentment','李守贞表面敬奉李彦韬，内心怨恨他',10,'守贞外',None,[('李守贞','表面敬奉、内心怨恨李彦韬'),('李彦韬','受到李守贞表面敬奉而内心怨恨')],when='946年六月条附叙，具体起止未载',place='后晋',note='史书叙述人物态度，不建长期敌对关系替代具体叙事。')
# 11: diplomacy failed; subsequent forged command belongs to paragraph 18.
add('li_rejects_fuzhou_attack','南唐将领想乘破建州之胜攻福州，李璟不允许',11,'初，','不许。',[('唐主','不许南唐乘胜攻福州')],when='南唐攻克建州后、946年七月以前的追述，具体日未载',year=None,place='南唐至福州',note='欲取是不被批准的建议，不能录成已攻福州。')
add('chen_offers_persuasion','陈觉自请到福州说服李仁达入朝',11,'枢密使','入朝。',[('陈觉','以枢密使身份自请说服李仁达入朝'),('李弘义','成为陈觉拟劝说入朝的对象')],when='陈觉赴福州以前，具体年月未载',year=None,place='南唐至福州')
sup('chen_offers_persuasion',11,cj,'陳覺自言可不用尺兵致仁達等。','《新五代史》也记陈觉自称不必用兵便可使李仁达等入朝。','自信说辞不等于已经成功；该书前文克闽州郡的压缩顺序与主书分别保留。')
add('song_recommends_chen','宋齐丘推荐陈觉，称他可凭才辩使李仁达入朝',11,'宋齐丘','弘义。',[('宋齐丘','向李璟推荐陈觉才辩'),('陈觉','被宋齐丘推荐以外交劝服李仁达')],when='陈觉赴福州以前，具体年月未载',year=None,place='南唐',note='不烦寸刃为推荐者的预期，未写成真实无战征服。')
add('li_honors_family','李璟封李仁达的母亲、妻子为国夫人，并迁升他的四个弟弟',11,'唐主乃','迁官，',[('唐主','封李仁达母妻、升其四弟官职'),('李弘义','母妻与四弟获得南唐封赏')],when='陈觉赴福州宣谕时，具体年月未载',year=None,place='南唐至福州',note='母妻未名、四弟官名未载；已知李弘通虽属弟但本句未逐名，不替四人造身份或官命。')
add('chen_fuzhou_envoy','李璟任陈觉为福州宣谕使，厚赐李仁达金帛',11,'以觉为','金帛。',[('唐主','任陈觉宣谕，给李仁达金帛'),('陈觉','任福州宣谕使'),('李弘义','获李璟厚赐金帛')],when='南唐攻克建州后、946年七月以前，具体日未载',year=None,place='福州',note='原书未给金额，不把赐帛写成李仁达已答应入朝。')
sup('chen_fuzhou_envoy',11,cj,'景以覺為宣諭使，召仁達朝金陵，仁達不從。','《新五代史》记李璟任陈觉宣谕使，召李仁达朝金陵，李仁达不从。','该书写召而不从，主书记陈觉不敢开口；差异分别保留，不断言口头召命已送达且正式被拒。',relation='conflicts')
add('li_treats_chen_coldly','李仁达知道陈觉的意图，以傲慢言辞和冷淡礼遇接待',11,'弘义知','疏薄。',[('李弘义','知道入朝劝说意图，对陈觉态度倨傲、礼遇疏薄'),('陈觉','受到李仁达冷淡接待')],when='陈觉抵福州时，具体年月未载',year=None,place='福州')
add('chen_returns_without_invitation','陈觉不敢向李仁达提出入朝，返回南唐',11,'觉不敢',None,[('陈觉','未敢提入朝要求便返回')],when='陈觉赴福州宣谕之后，具体年月未载',year=None,place='福州至南唐',note='此处主书行动主体陈觉明确，未与下文疑误陈诲文字混同。')
# 12–14.
add('yellow_river_yangliu_breach','黄河在杨刘决口，水向西进入莘县，宽四十里，再从朝城向北流',12,'秋，',None,[],when=july,place='杨刘、莘县、朝城',note='史载水宽四十里，未换算现代洪水面积或给坐标。')
sup('yellow_river_yangliu_breach',12,oy,'楊劉口河決西岸，水闊四十里。','《旧五代史》同记七月杨刘口黄河西岸决口、水宽四十里。','主書另列莘县朝城路径，补证不据省略否认路径。')
add('messenger_claims_zhao_return','从幽州来的人声称赵延寿有意归后晋',13,'有自','归国。',[('赵延寿','被来人声称有意归后晋')],when=july,place='幽州至后晋',note='来人未名，自报意图不是已验证真心归国。')
add('li_feng_order_du_letter','李崧、冯玉相信消息，命杜重威向赵延寿写信并许以厚利',13,'枢密使','厚利，',[('李崧','相信消息、与冯玉命杜重威写信'),('冯玉','相信消息并参与书信招引'),('杜威','受命致书赵延寿、陈述朝旨与厚利'),('赵延寿','收到后晋书信招引')],when='946年；《旧五代史》记三月发信，《资治通鉴》在七月条记此事',place='天雄军至幽州',note='《资治通鉴》在七月条记送信，《旧五代史》明确回述三月发信；原文顺序与实际发信月分别呈现。')
sup('li_feng_order_du_letter',13,oz,'是歲三月，復遣鄴都杜威致書於延壽，且述朝旨，啖以厚利，','《旧五代史》记946年三月再命杜重威致书赵延寿，陈述朝旨、许以厚利。','主书此段位于七月条，未单给首次送信月；以该书补三月发信，事件显示原主书语境而非定同日。',relation='adds',field='time_original')
add('zhao_xingshi_delivers_letter','赵行实因曾事赵延寿，奉命秘密送信给他',13,'洛州军将','遗之。',[('赵行实','因曾事赵延寿而被派秘密送信'),('赵延寿','由旧属赵行实送信')],when='946年赵延寿书信往来期间，首次送信日未载',place='后晋至幽州',note='沿用早期同名军将key，不补未经证实的亲属关系。')
sup('zhao_xingshi_delivers_letter',13,oz,'仍遣洺州軍將趙行實賫書而往，潛申款密。行實曾事延壽，故遣之。','《旧五代史》记赵行实为洺州军将，曾事赵延寿，奉命携信秘密前往。','主书洛州与该书洺州职地不同，保留异说，不能靠繁简转换当作同一州。',relation='conflicts')
add('zhao_requests_army_reception','赵延寿回信称思归中原，请后晋发大军接应他南返',13,'延寿复书','恳密。',[('赵延寿','回信自称思归，并请求大军接应')],when='946年七月条下书信往来，具体回信日未载',place='幽州至后晋',note='回信承诺尚未兑现，不作赵延寿已经叛逃事实。')
sup('zhao_requests_army_reception',13,oz,'七月，行實自燕回，得延壽書，且言：「久陷邊庭，願歸中國，乞發大軍應接，即拔身南去。」','《旧五代史》记七月赵行实从燕地带回赵延寿请求发军接应的书信。','将书信返回月与首次三月送信分别说明，未把后来的设诱真相提前当成当前朝廷已知。',relation='adds')
add('court_sends_zhao_again','后晋朝廷欣然再派赵行实与赵延寿约定接应日期',13,'朝廷欣然，',None,[('赵行实','再赴赵延寿处约定接应日期'),('赵延寿','与后晋派使约定接应')],when=july,place='后晋至幽州',note='约期不等同实际发军或入京归国，未补具体所约日期。')
sup('court_sends_zhao_again',13,oz,'時朝廷欣然從之，復遣趙行實計會延壽大軍應接之所。','《旧五代史》记朝廷再派赵行实安排大军接应之地。','主书约期与旧书接应地点均为筹划层，未当作已会师。',relation='adds')
add('li_reports_changcheng_victory','李守贞报告在长城北与契丹千余骑交战四十里，斩解里并使余众落水',14,'八月，','甚众。”',[('李守贞','奏报长城北战胜契丹并斩解里'),('解里','被李守贞奏报斩杀')],when='946年八月奏报，战斗具体日未载',place='长城北',note='战绩与兵数为奏报，奏报日未单给；解里近名谐里未合并。')
sup('li_reports_changcheng_victory',14,oa,'李守貞奏，大軍至望都縣，相次至長城北，遇敵千餘騎，轉鬥四十里，斬蕃將解裏相公。','《旧五代史》同记李守贞奏报军经望都至长城北、遇契丹千余骑、转斗四十里、斩解里相公。','同一报捷与姓名译字对应，原文解裏保留；此前癸亥另记张煦任青州，不将其日套报捷。')
claim('person',people['解里（946年契丹将）'],'death_year','李守贞在946年八月奏报斩杀契丹将解里。',14,'斩其酋帅解里，','死亡来源为战报，具体战斗日未给；暂不与其他近名契丹将领合并。')
add('li_returns_chanzhou','朝廷命李守贞撤回澶州驻军',14,'丁卯，',None,[('李守贞','受命还屯澶州')],when='946年八月丁卯',place='北面行营至澶州')
sup('li_returns_chanzhou',14,oa,'丁卯，詔班師。','《旧五代史》同记丁卯诏令班师。','班师补撤回任务，澶州去向据主书，不凭旧书省略否定驻地。')
# 15: background before mass killing.
add('shi_hosts_bai_chengfu','石重贵与契丹断交后，多次召白承福入朝，厚加宴赏',15,'帝既','甚厚。',[('帝','多次召白承福并厚赏'),('白承福','入朝受宴赏')],when='后晋与契丹断交后、白承福被杀以前，具体年月未载',year=None,place='后晋朝廷',note='原已录断交事件，本段只录其后礼遇，不重新造一次断交。')
add('bai_fights_chanzhou','白承福跟随石重贵在澶州与契丹作战',15,'承福从帝','澶州，',[('白承福','跟随石重贵在澶州对契丹作战'),('帝','与白承福共同作战')],when='白承福被杀以前的澶州战事，具体日未载',year=None,place='澶州',note='未凭回顾文字将此定为946年新战。')
add('bai_garrisons_huazhou','白承福与张从恩驻守滑州',15,'又与','滑州。',[('白承福','与张从恩戍滑州'),('张从恩','与白承福驻滑州')],when='白承福被杀以前，具体年月未载',year=None,place='滑州')
add('bai_group_returns_taiyuan','因天气炎热，白承福部落被遣回太原，在岚石一带放牧',15,'属岁','之境。',[('白承福','部落被遣回太原、牧于岚石之境')],when='白承福被杀之前一个炎热年份，具体年月未载',year=None,place='太原、岚州和石州一带',note='主语遣部落为承前朝廷安排但执行者未名，未造具名押送使；岁大热不强定本年夏。')
add('liu_punishes_bai_group','白承福部落多有违法者，刘知远不予宽纵',15,'部落多犯法，','纵舍。',[('刘知远','对部落违法不加宽纵'),('白承福','其部落有违法情况')],when='部落回太原后、诛杀前，具体年月未载',year=None,place='太原、岚石一带',note='既未列具体罪项，也不能把后来诬告谋反解释为已证实犯罪。')
add('bai_group_plans_return','吐谷浑部众因朝廷衰弱、畏刘知远严厉，打算回原居地',15,'部落知','故地。',[('白承福','所属部众谋回故地')],when='白可久率部先逃之前，具体年月未载',year=None,place='太原及部落牧地',note='是部众计划，不把白承福本人已逃归契丹写成事实。')
add('bai_kejiu_defects','白可久率所属部众先逃往契丹',15,'有白可久者，','契丹，',[('白可久','地位次于白承福，率所属部众先逃契丹')],when='白承福被杀以前，具体年月未载',year=None,place='太原牧地至契丹')
add('khitan_appoints_bai_kejiu','契丹任白可久为云州观察使，借他招引白承福',15,'契丹用',None,[('白可久','被任为云州观察使，用来招引白承福'),('白承福','成为契丹拟招引的对象')],when='白可久逃归之后、白承福被杀之前，具体年月未载',year=None,place='云州',note='以诱承福是契丹的目的，不写白承福已经归附。')
# 16: plans, forced migration, fabricated accusation, execution and inventory separated.
add('liu_guo_discuss_removal','刘知远向郭威提出，留吐谷浑部众在太原是心腹之患，应将他们除去',16,'知远与','去之。”',[('刘知远','向郭威提出应除去太原吐谷浑部众'),('郭威','参与刘知远关于处置吐谷浑的谋议')],when='白承福被杀之前，具体月日未载',year=None,place='太原',note='腹心之疾为刘知远的判断，不当作全族客观罪名。')
add('historian_notes_bai_wealth','史书记白承福家富，用银槽喂马',16,'承福家','银槽。',[('白承福','被史书记为家富、用银槽喂马')],when='白承福被杀前的家资介绍，具体年月未载',year=None,place='白承福居处，具体位置未载')
add('guo_urges_kill_for_wealth','郭威劝刘知远杀白承福，没收家产供军',16,'威劝','赡军。',[('郭威','劝杀白承福并没收财物供军'),('刘知远','听取杀人夺财建议'),('白承福','成为杀人夺财建议的对象')],when='白承福被杀之前，具体月日未载',year=None,place='太原',note='先录建议，实际杀人没收分别另录，不能以建议替代执行证据。')
add('liu_requests_bai_migration','刘知远密奏称吐谷浑反复难保，请将部众迁往内地',16,'知远密表：','内地。”',[('刘知远','密奏请求迁部众，称其反复难保')],when='白承福被杀之前，具体月日未载',year=None,place='太原至后晋朝廷',note='反复难保是密奏的理由，不认作史料已证实全体将叛。')
add('shi_moves_bai_people','石重贵派使者调迁吐谷浑部众一千九百人，分置河阳等州',16,'帝遣使','诸州。',[('帝','派使者迁部众至河阳和其他州'),('白承福','所属部众受到调迁安排')],when='946年白承福诛杀前，迁移具体日未载',year=None,place='太原牧地至河阳及诸州',note='实际分置与请求分开，一千九百人是史载数，不补未列州名；此段可能五月或八月前，各书月份不一致。')
add('guo_lures_bai_into_taiyuan','刘知远派郭威诱白承福等入太原城居住',16,'知远遣威','城中，',[('刘知远','派郭威诱部落首领入城'),('郭威','诱白承福等入住太原城'),('白承福','被诱进入太原城')],when='946年白承福等被杀之前，具体月日未载',place='太原城')
add('liu_fabricates_rebellion','刘知远诬告白承福等五族谋叛',16,'因诬','谋叛，',[('刘知远','诬告白承福等五族谋叛'),('白承福','与其他族众被诬告谋叛')],when='946年诛杀之前，具体月日未载',place='太原',note='原文诬字明确，不把五族谋叛写成实际反叛。')
add('liu_kills_bai_families','刘知远派兵围杀白承福等五族，共四百口',16,'知远遣威','四百口，',[('刘知远','派兵围杀白承福等五族'),('郭威','奉命诱首领入城，为随后围杀作准备'),('白承福','与五族四百口一起遇害')],when='946年八月条下；《旧五代史》汉高祖纪另记五月，处置纪月待核',place='太原城',note='合四百口是全部五族总数，不拆成每族四百；不把郭威写成有证据直接挥刀杀人。')
sup('liu_kills_bai_families',16,oa,'癸酉，河東節度使劉知遠奏，誅吐渾大首領白承福、白鐵匱、赫連海龍等，並夷其族凡四百口，蓋利其孳畜財寶也，人皆冤之。','《旧五代史》晋少帝纪记八月癸酉刘知远奏报诛白承福、白铁匮、赫连海龙等，夷族四百口，并称其为夺财、人皆以为冤。','癸酉为奏报日，不能直接当所有死亡日；该书补两名首领与评价，不补未名的其他两族。',relation='adds')
sup('liu_kills_bai_families',16,nh,'八月，殺吐渾白承福等族，取其貲鉅萬，良馬數千。','《新五代史》汉高祖纪也记八月杀白承福等族，并取财物巨万、良马数千。','明确此纪帝为刘知远而非石重贵；数千概数不合并为主书买马五千的同一批马。')
sup('liu_kills_bai_families',16,oh,'三年五月，加守太尉。是月，帝誅吐渾白承福等五族凡四百人，','《旧五代史》汉高祖纪把刘知远诛白承福等五族四百人记在开运三年五月。','此纪帝为刘知远，主书八月条与新史八月、旧晋纪八月奏报不同，处置与奏报可能不同但不能据此猜定唯一五月日期。',relation='conflicts',field='time_original')
for name in ['白铁匮','赫连海龙']:
 quote='誅吐渾大首領白承福、白鐵匱、赫連海龍等，並夷其族凡四百口，'
 pk=person(name,16,'在刘知远八月奏报中记为遇害吐谷浑首领',quote,source=oa)
 edge='participation_zztj_285_0946_liu_kills_bai_families_'+pk
 B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['liu_kills_bai_families'],role='被《旧五代史》列为遇害吐谷浑首领',status='draft'))
 claim('person_event',edge,'role',name+'被《旧五代史》列为白承福诛杀事件中的遇害首领。',16,quote,'同一处置新增该书具名的参与主体，不另造一场诛杀，原文保留。',source=oa,relation='adds')
 claim('person',pk,'death_year',name+'于946年被刘知远杀死，八月癸酉奏报。',16,quote,'纪年一致、执行月份异说与奏报日区别，不改成每人癸酉死亡。',source=oa,relation='adds')
claim('person',people['白承福'],'death_year','白承福于946年被刘知远杀死；新史记八月，旧汉纪记五月，旧晋纪八月奏报。',16,'以兵围而杀之，合四百口，','同一年三种纪月层次分别列出处，人物死亡年为946，具体月日保持待核。')
add('liu_confiscates_bai_wealth','刘知远没收白承福等人的家产',16,'籍没','家赀。',[('刘知远','没收遇害者家产'),('白承福','家产遭没收')],when='946年白承福等被杀时，纪月有异说',place='太原')
sup('liu_confiscates_bai_wealth',16,nh,'取其貲鉅萬，良馬數千。','《新五代史》补记取得财物巨万、良马数千。','数量为史书概数，不构现代币值或精确资产清单。',relation='adds')
add('jin_rewards_bai_killing','后晋朝廷下诏褒赏对白承福等部众的处置',16,'诏褒','赏之，',[('刘知远','处置白承福等之后获得朝廷褒赏')],when='946年处置之后，具体月日未载',place='后晋朝廷至太原',note='主语朝廷诏令，未具名获赏名单与金额，不补郭威具体加官。')
add('historian_notes_tuyuhun_decline','史书记这次杀戮使吐谷浑部众衰弱',16,'吐谷浑',None,[],when='946年处置后的影响，具体起止未载',place='吐谷浑部众',note='遂微是史书对影响的概述，不等同吐谷浑所有族群彻底灭绝。')
# Independent continuation within the same killing account, not an invented fifth family.
event('wang_yizong_leads_survivors','《旧五代史》记刘知远命王义宗统领剩余吐谷浑部众',16,'是月，帝誅吐渾白承福等五族凡四百人，以別部王義宗統其餘眾。',[('刘知远','命别部王义宗统领余众'),('王义宗','受命统领诛杀后的剩余部众')],source=oh,when='《旧五代史》汉高祖纪记946年五月',place='太原及吐谷浑部众',note='该书五月纪月独立保留，未依据名字推王义宗与白承福的血缘关系。')
reviews={9:'初字市马与调邠陕入卫为追述；静难保义对应军镇州名不造重复迁转。丙寅才复任，率关西任务非已胜。厚事不猜金额。',10:'乙丑为定州奏报，诸任命未独立给日，旧六月段保留，不套壬午。十营不乘二。李彦韬后晋主体与温韬不混；监知与内恨不造笼统敌对关系。',11:'初字外交为建州后追述，欲取未准非已战；陈自请和宋推荐是预期，母妻未名四弟官名不造。主陈不敢言与新召而不从细节不同并列；矫诏兵事留后段。',12:'杨刘西岸决口与莘县朝城水道分开地名，四十里史载水宽，不换面积或坐标。',13:'消息和回书非真实归附。旧三月发信七月归书补时序；洛洺州职地异说。赵行实复用早期同名军将，未添亲属；约日期与接应地计划未已会师。',14:'八月奏报非明确战斗日，丁卯撤回独立日；解里暂不同945谐里合，死年据本年奏报。',15:'宴赏战澶戍滑热遣返牧皆追述不强946，旧族犯事不等后诬反确罪。白可久早逃与云州诱福是计划，承福未逃。',16:'刘郭谋议杀夺计划、帝迁部众、郭诱入城、诬反、实际围杀、没财褒赏影响分别。五族共四百口不每族400，1900迁众非400死同额。旧晋纪八月癸酉奏报补白铁匮赫连海龙；旧汉纪五月与新八月并列，帝为刘非石。王义宗统余众独立五月原书，不造未名两族。'}
assert not (P/'publication.json').exists()
for n in range(9,17):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285原39—46行连续八段，946年共56段，本批发布后累计16段，仍40段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],source_contexts=[dict(source_key=main_sources[0],note='只录第9—10段；前2—8段已发布不重复。'),dict(source_key=main_sources[1],note='只录第11—16段；末第17—18段慕容彦超与陈觉矫诏福州战事留下一批。'),dict(source_key=oz,note='只补三月送信、七月返回与再约接应；九月瀛州诈降和其他官命未提前。'),dict(source_key=cj,note='只补陈觉自请宣谕、召入朝不从的说法；矫诏兵事、围城失败、监军与后世被流不提前。'),dict(source_key=oh,note='只补五月诛杀纪月及王义宗统余众；九月战事与十二月后晋投降未提前。')],source_issues_review='白承福处置主八月条及新八月、旧汉纪五月、旧晋纪八月癸酉奏报分层保留。洛州洺州职地异说，陈觉不敢言与召而不从差异保留。解里谐里近译未强合。电子本纸本未核不当独立确证。',plain_language_review='首次逐项阅读所有展示字段与事实说明，简体白话，主语明确。建议、密奏理由、诬告、书信承诺、战报与实际处置分开，未知时间和未名角色不猜补；逐字原文保持底本。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
