# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 944 paragraphs 1–11."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,12))
COMMIT='76880fa37d0bdb722c1238d971903f0fd476eb32'
specs=[('xinwudaishi-062-feng-name' if d.name=='xinwudaishi-062-jia-chong' else d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-943-min-liu-zan']:
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
main_sources = ['tongjian-283-943-min-liu-zan','tongjian-283-944-january-close']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0944-p001-p011',
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
lines = (ROOT / 'resources/derived/tongjian/283.txt').read_text().splitlines()
for n in range(1, 12):
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
        month = '正月条下及追述'
        citation = f'卷283·后晋天福九年、后称开运元年（944；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0944_01_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=944, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='944年正月条下，具体日期未载'
    key = 'event_zztj_283_0944_' + code
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
        edge = 'participation_zztj_283_0944_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0944_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','契丹主':'耶律德光','杜威':'杜重威','李景遂':'徐景遂','李景达':'徐景达','冯延己':'冯延巳','曦':'王延羲','闽主':'王延羲','殷主':'王延政','丘甫遇':'皇甫遇','周儒':'周儒（后晋博州刺史）','王班':'王班（后晋殿直）'})
NEW_ALIASES={'邵珂':[],'王令温':['王令溫'],'曹光裔':[],'贾崇':['賈崇'],'孟守忠':[],'窦仪':['竇儀'],'周儒（后晋博州刺史）':[],'伟王（契丹）':['偉王（契丹）'],'邵崇范':['邵崇範'],'王令崇':[],'王班（后晋殿直）':[]}
NEW_DESCRIPTIONS={
'邵珂':'后晋永清军军校、王令温牙将，被免职后秘密遣人入契丹，称贝州粮多兵弱。944年正月由吴峦委守南门，随后引契丹入城。生卒年未载。',
'王令温':'瀛州河间人，后晋永清军节度使。免除邵珂军职，入朝时将其子邵崇范带在身边作人质。贝州陷落后家属被契丹俘获，944年正月被调为邓州节度使。生卒年本批未录。',
'曹光裔':'后晋成德节度使杜重威的幕僚。944年正月前往青州劝说杨光远，又替杨光远入朝奏报并随使者返回慰谕。生卒年未载。',
'贾崇':'南唐侍卫都虞候。944年正月条下记其求见李璟，反对限制群臣奏事。自称事奉先帝三十年，此处不据时长倒推出任官年。生卒年未载。',
'孟守忠':'后晋译者、译诏官。944年正月奉石重贵命向耶律德光致书，求恢复两国旧好，返回时带回拒绝修好的答复。生卒年未载。',
'窦仪':'蓟州人，后晋天平军观察判官。944年正月奉颜衎命向朝廷奏报周儒降契丹、引兵渡河及蔡行遇被俘，并向景延广说明与杨光远会合的危险。生卒年本批未核。',
'周儒（后晋博州刺史）':'后晋博州刺史，944年正月投降契丹，并与杨光远通使。颜衎的奏报称其引契丹从马家口渡河，蔡行遇被擒。未证与888年魏博被俘将领周儒同人，分别建档。',
'伟王（契丹）':'契丹王爵称谓，个人姓名在本批史料中未明确。944年正月辛丑，太原奏报在秀容击败其军；《新五代史》记与其交战的晋方将领为刘知远。生卒年未载。',
'邵崇范':'邵珂的儿子。《新五代史》记王令温入朝时，因怀疑邵珂而将邵崇范带在身边作人质。确切年月与生卒年未载。',
'王令崇':'王令温的弟弟。《旧五代史》记944年正月戊子从契丹回来，向后晋朝廷说明家族陷在贝州的情况。生卒年未载。',
'王班（后晋殿直）':'后晋殿直，与909年被杀的襄州刺史王班分别建档。944年正月辛巳奉命出使契丹，到邺都无法前进而返回，姓名由《新五代史》补证。生卒年未载。'}
aold='jiuwudaishi-082-944-january';anew='xinwudaishi-009-944-january';wu='xinwudaishi-029-wu-luan-death';jia='xinwudaishi-062-feng-name'
# 1: frontier report, preceding preparations, betrayal, death and five appointments.
add('frontier_reports_beizhou','边地奏报赵延寿、赵延照率五万契丹兵逼近贝州',1,'春，正月，','逼贝州。”',[('赵延寿','被奏报为领兵逼近贝州的契丹前锋'),('赵延照','被奏报为领兵逼近贝州的契丹前锋')],when='944年正月乙亥，奏报日',place='贝州',note='乙亥是边地驰告日期，兵数为奏报内容；不把入境日直接认作奏报日。')
sup('frontier_reports_beizhou',1,aold,'乙亥，滄、恒、貝、鄴馳告，契丹前鋒趙延壽、趙延昭引五萬騎入寇，將及甘陵，青州楊光遠召之也。','《旧五代史》记沧、恒、贝、邺乙亥驰告，赵延寿与赵延昭率五万骑兵逼近甘陵。','延照与延昭沿用已核主体，甘陵贝州名称保留各书原字；杨光远召之为该书记载，不由此推精确密告日。',relation='adds')
relationship('赵思温','赵延照','父亲',1,'延照，思温之子也。','父子明确，沿用既有关系稳定key，不另建反向儿子边。')
add('jin_stockpiles_beizhou','后晋因贝州是水陆要冲，在当地储备军粮草料防契丹',1,'先是朝廷','以备契丹。',[],year=None,when='944年正月陷城前的追述，具体开始年月未载',place='贝州',note='为大军数年之储说明储备目的或规模，不倒推出储粮起始年份。')
add('wang_dismisses_shao','王令温免除军校邵珂职务',1,'军校邵珂，','王令温黜之。',[('王令温','免除邵珂军职'),('邵珂','被免职')],year=None,when='贝州陷落前的追述，确切年月未载',place='贝州')
add('shao_invites_khitan','邵珂秘密遣人入契丹，称贝州粮多兵弱、容易攻取',1,'珂怨望，','易取也。”',[('邵珂','派人向契丹提供贝州粮多兵弱的说法')],year=None,when='邵珂被免职后、贝州陷落前，确切年月未载',place='贝州、契丹',note='粮多兵弱和易取是邵珂向契丹传递的说法，不直接变成本站军事评估。')
add('wu_luan_beizhou_assignment','王令温入朝，后晋任吴峦暂时主持贝州事务',1,'会令温入朝，','权知州事。',[('王令温','离开贝州入朝'),('吴峦','由前复州防御使被任命主持贝州事务')],year=943,when='943年十一月戊戌，日期由《旧五代史》补证',place='贝州',note='主书会令温入朝是追述，旧纪明确前一年十一月戊戌，不能强定944正月。')
sup('wu_luan_beizhou_assignment',1,'jiuwudaishi-082-wu-luan-assignment','戊戌，遣前復州防禦使吳巒權知貝州軍事，詔節度使王令溫赴闕。','《旧五代史》943年十一月戊戌记派吴峦权知贝州军事，召王令温入朝。','据本段十一月年界与此前连续943年本纪校核年份；不把新年条内追述全套944年。',relation='adds',field='time_original')
add('wu_shao_gate_defense','吴峦接受邵珂守城请求，派他守南门，自己守东门',1,'峦至，','峦自守东门。',[('吴峦','抚慰将士，派邵珂守南门，自己守东门'),('邵珂','请求效力，受命守南门')],when='944年正月契丹攻贝州期间，具体日期未载',place='贝州东门、南门')
add('wu_burns_siege_equipment','耶律德光亲攻贝州，吴峦抵抗并烧毁多数攻城器具',1,'契丹主自攻','殆尽。',[('契丹主','亲自率兵攻贝州'),('吴峦','抵抗并烧毁契丹攻城器具')],place='贝州')
add('shao_opens_south_gate','邵珂引契丹兵从贝州南门入城',1,'己卯，','自南门入，',[('邵珂','引契丹兵从南门入城')],when='944年正月己卯',place='贝州南门')
add('wu_luan_dies','贝州失守时，吴峦投井身亡',1,'珂引契丹','峦赴井死。',[('吴峦','贝州被攻入时投井身亡')],when='944年正月己卯',place='贝州',note='自杀动作明确，既有主体保留；个人基线不覆盖，新增死亡事实引用。')
sup('wu_luan_dies',1,wu,'巒顧城中已亂，即投井死。','《新五代史》也记吴峦见城内已乱，投井身亡。','传末不足贵为作者评价，不将评价当作吴峦本人言论。')
claim('person',people['吴峦'],'death_year','吴峦在944年正月己卯贝州陷落时投井身亡。',1,'己卯，契丹复攻城，珂引契丹自南门入，峦赴井死。','死亡明确，沿用既有主体，不改写已发布人物档案。')
add('khitan_captures_beizhou','契丹攻陷贝州，史书记被杀者近万人',1,'契丹遂陷','且万人。',[],when='944年正月己卯',place='贝州',note='且万人保留近万人量级，不给伪精确人数或未载身份构成。')
sup('khitan_captures_beizhou',1,aold,'己卯，契丹陷貝州，知州吳巒死之。','《旧五代史》也记正月己卯贝州陷落、吴峦死亡。','本句未记近万人数字，只支持城陷与死亡日期。')
for code,title,start,end,name,role in [
('gao_north_commander','后晋任高行周为北面行营都部署','庚辰，','都部署，','高行周','由归德节度使任北面行营都部署'),
('fu_cavalry_left','后晋任符彦卿为马军左厢排陈使','以河阳节度使','左厢排陈使，','符彦卿','由河阳节度使任马军左厢排陈使'),
('huangfu_cavalry_right','后晋任皇甫遇为马军右厢排陈使','以右神武统军','右厢排陈使，','皇甫遇','由右神武统军任马军右厢排陈使'),
('wang_infantry_left','后晋任王周为步军左厢排陈使','以陕府节度使','步军左厢排陈使，','王周','由陕府节度使任步军左厢排陈使'),
('pan_infantry_right','后晋任潘环为步军右厢排陈使','以左羽林将军',None,'潘环','由左羽林将军任步军右厢排陈使')]:
 add(code,title,1,start,end,[('帝','任命行营将领'),(name,role)],when='944年正月庚辰',place='后晋',note='沿用已录将领。皇甫遇在底本作丘甫遇，以旧纪同日、同军职、同任官序列校核，原字不改。潘环旧纪作左羽林统军，分别保留。')
sup('huangfu_cavalry_right',1,aold,'以右神武統軍皇甫遇為馬軍右廂排陣使，','《旧五代史》同日记右神武统军皇甫遇任马军右厢排阵使。','据同日及军职序列将底本丘甫遇校为皇甫遇；不新建丘甫遇人物。',relation='adds')
claim('person',people['皇甫遇'],'name','本段丘甫遇据《旧五代史》同日、同职任官记载校为皇甫遇。',1,'丘甫遇','底本原字保留，展示用已录姓名皇甫遇，纸本待核。')
# Supplement distinct actions from the same siege narrative.
E['shao_son_hostage']=event('shao_son_hostage','王令温怀疑邵珂，入朝时带其子邵崇范作人质',1,'令溫以事朝京師，心頗疑珂，乃質其子崇範以自隨。',[('王令温','因怀疑邵珂，带其子作人质入朝'),('邵珂','儿子被王令温带走作人质'),('邵崇范','被带在王令温身边作人质')],source=wu,year=None,when='王令温入朝、贝州陷落之前，确切年月本句未载',place='贝州至后晋朝廷',note='其子结合令温疑珂质子与本传上下文指邵珂之子，不错接为王令温之子。')
relationship('邵珂','邵崇范','父亲',1,'令溫以事朝京師，心頗疑珂，乃質其子崇範以自隨。','其子为被怀疑者邵珂之子，姓名只见崇範，依明确父子展开邵姓；确切人质日期未载。',source=wu)
E['wu_clothes_soldiers']=event('wu_clothes_soldiers','吴峦在严寒中拆帷幄给士兵作衣物',1,'巒善撫士卒，會天大寒，裂其帷幄以衣士卒，士卒皆愛之。',[('吴峦','在严寒中拆帷幄给士兵作衣物')],source=wu,year=None,when='吴峦守贝州期间，943年十一月任命后、944年正月陷落前，具体日期未载',place='贝州',note='有明确上下限但不能择一强定为943或944年。')
E['wang_lingchong_returns']=event('wang_lingchong_returns','王令崇从契丹返回，报告王令温家族陷在贝州',1,'時令溫弟令崇自契丹至，訴以舉族陷於甘陵，',[('王令崇','从契丹返回，报告家族陷在贝州')],source=aold,when='944年正月戊子条下，返回确切日期未单列',place='后晋朝廷',note='甘陵沿用本纪原称；不把举族陷与所有人死亡混同。')
relationship('王令温','王令崇','兄长',1,'時令溫弟令崇自契丹至，','弟明确，王令温是王令崇的兄长。',source=aold)
E['wang_lingwen_dengzhou']=event('wang_lingwen_dengzhou','后晋调王令温为邓州节度使',1,'以貝州節度使王令溫為鄧州節度使，',[('帝','任王令温为邓州节度使'),('王令温','由贝州调为邓州节度使')],source=aold,when='944年正月戊子',place='邓州',note='旧纪日明确；新传武胜军名称作为他书独立职衔，不直接覆盖旧纪地名。')
sup('wang_lingwen_dengzhou',1,wu,'而令溫家屬為契丹所虜，出帝憫之，以令溫為武勝軍節度使，','《新五代史》另记王令温家属被俘，后晋任他为武胜军节度使。','新传未给戊子日期，武胜军与旧纪邓州分别保留，不能由此补家属具体人数或获释时间。',relation='adds')
# 2–4: northern alerts, deceptive diplomatic report and two Southern Tang transfers.
add('yanmen_invasion_report','太原奏报契丹进入雁门关',2,'太原奏','雁门关。',[],place='雁门关',note='原文是奏报，不补具体入关日。')
sup('yanmen_invasion_report',2,aold,'太原奏，契丹入雁門，圍忻、代二州。','《旧五代史》还记契丹围攻忻州、代州。','独立补充围攻地点，不从奏报自动补当日攻城战果。',relation='adds')
add('heng_xing_cang_alerts','恒州、邢州、沧州都奏报契丹入侵',2,'恒、',None,[],place='恒州、邢州、沧州')
add('cao_warns_yang','杜重威派曹光裔劝说杨光远，说明利害',3,'成德节度使','为陈祸福，',[('杜威','派曹光裔前往杨光远处说明利害'),('曹光裔','向杨光远说明利害'),('杨光远','听取曹光裔劝说')],place='青州')
add('yang_claims_mothers_illness','杨光远派曹光裔奏称杨承祚为母病逃归，并感谢朝廷宽宥',3,'光远遣光裔','阖族荷恩。”',[('杨光远','让曹光裔转述承祚为母病逃归等说法'),('曹光裔','向朝廷转奏杨光远的话')],place='后晋朝廷',note='母病是杨光远辩解，不另证明其母实际病情；未把承祚作为入奏现场参与者。')
add('jin_reassures_yang','后晋相信杨光远说法，派使者与曹光裔回去慰谕',3,'朝廷信',None,[('帝','派使者与曹光裔往青州慰谕'),('曹光裔','随使者返回慰谕杨光远'),('杨光远','受到朝廷慰谕')],place='青州',note='信其言不代表杨光远实际停止叛乱。')
add('zhou_zong_zhennan','李璟任周宗为镇南节度使',4,'唐以','镇南节度使，',[('唐主','任周宗为镇南节度使'),('周宗','由侍中出任镇南节度使')],place='镇南')
add('zhang_juyong_zhenhai','李璟任张居咏为镇海节度使',4,'左仆射',None,[('唐主','任张居咏为镇海节度使'),('张居咏','由左仆射兼门下侍郎、同平章事出任镇海节度使')],place='镇海')
# 5: succession intention and access restrictions; conflicting independent source kept.
add('jing_plans_brother_succession','李璟决意将来传位给李景遂、李景达',5,'唐主决欲','二王。',[('唐主','决意将来传位给弟弟'),('李景遂','被李璟列为拟传位对象'),('李景达','被李璟列为拟传位对象')],place='南唐',note='齐燕二王据前批943年封号识别，复用徐景遂徐景达稳定主体；决欲不等于已传位。')
add('feng_plans_restrict_access','冯延巳等打算隔绝皇帝与朝臣，借此专权',5,'翰林学士','以擅权。',[('冯延己','史书记他等人欲借限制奏事专权')],place='南唐',note='欲为意图，不把未具名等人全部配成五鬼成员在现场共同行动。')
add('jing_limits_audiences','李璟令李景遂参决政务，只许魏岑、查文徽奏事，其他官员须奉召',5,'辛巳，','不得见。”',[('唐主','颁敕限制奏事与召见'),('李景遂','受命参与决定政务'),('魏岑','被允许向李璟奏事'),('查文徽','被允许向李璟奏事')],when='944年正月辛巳',place='南唐')
sup('jing_limits_audiences',5,jia,'十二月，景下令中外庶政委齊王景遂參決，惟陳覺、查文徽得奏事，羣臣非召見者，不得入。','《新五代史》将限制奏事的敕令放在十二月，准许奏事者记为陈觉、查文徽。','与通鉴正月辛巳及魏岑、查文徽存在月份和人选差异，各自引用；不以任一说法覆盖另一书。',relation='conflicts')
add('xiao_petition_no_response','萧俨上疏强烈反对限制奏事，未获答复',5,'国人大骇。','不报。',[('萧俨','上疏反对限制群臣奏事，未获答复')],when='944年正月辛巳敕令后，具体日期未载',place='南唐')
add('jia_chong_petitions_access','贾崇求见李璟，哭谏不应隔绝朝臣',5,'侍卫都虞候','涕泗呜咽。',[('贾崇','求见并哭谏，反对李璟隔绝朝臣'),('唐主','听取贾崇劝谏')],when='944年正月限制奏事敕令后，具体日期未载',place='南唐',note='自称事先帝三十年为贾崇言辞，不据此倒算固定任官起年。')
add('jing_withdraws_access_edict','李璟受贾崇劝谏触动，撤回限制奏事敕令',5,'唐主感悟，','前敕。',[('唐主','撤回限制奏事敕令')],when='944年正月贾崇劝谏后，具体日期未载',place='南唐')
sup('jing_withdraws_access_edict',5,jia,'景為之動容，引與坐，賜食而慰之，遂寢所下令。','《新五代史》记李璟留贾崇坐下，赐食慰问，随后停止此前敕令。','此处支持撤令及赐食，月份分歧仍按两书并列，不声称新史也写正月。',relation='adds')
add('jing_builds_tower_xiao_remonstrates','李璟建宫中高楼，萧俨借景阳楼作讽谏',5,'唐主于宫中','景阳楼耳。”',[('唐主','建高楼、召臣观看并询问萧俨'),('萧俨','借景阳楼和井的典故讽谏')],year=None,when='李璟在位初期相关追述，确切年月未载',place='南唐宫中',note='原文相邻不等于高楼在辛巳当天建成；典故不新建陈后主参与边。')
add('xiao_demoted_shuzhou','李璟因萧俨讽谏而怒，将他贬到舒州',5,'唐主怒，','贬于舒州，',[('唐主','将萧俨贬到舒州'),('萧俨','因讽谏被贬舒州')],year=None,when='上述高楼讽谏后，确切年月未载',place='舒州')
add('sun_guards_xiao','孙晟派兵防范萧俨，萧俨申辩自己只是因劝谏获罪',5,'观察使孙晟','反见防邪！”',[('孙晟','派兵防范萧俨'),('萧俨','向孙晟申辩，并提到孙晟此前顾命时的行动')],year=None,when='萧俨被贬舒州期间，确切年月未载',place='舒州',note='君几危社稷为萧俨责问；此前继位行动已有943年独立记录，不在此另造一次顾命政变。')
add('sun_withdraws_guards','孙晟惭惧，撤除对萧俨的防范',5,'晟惭惧，',None,[('孙晟','撤除对萧俨的防范')],year=None,when='上述申辩之后，确切年月未载',place='舒州')
# 6: missions, marching orders, locations, commanders; distinction between report and action.
add('jin_mission_blocked','石重贵派使者致书契丹，使者因契丹已屯邺都而无法前进，返回',6,'帝遣使','而返。',[('帝','遣使致书契丹，使者无法前进而返回')],place='邺都',note='主书使者未具名，新史王班及日期作为独立补证。')
sup('jin_mission_blocked',6,anew,'辛巳，殿直王班使于契丹，至于鄴都，不得進而復。','《新五代史》记正月辛巳殿直王班出使，到邺都无法前进而返回。','同一到邺都未通而返场景补使者与日期，不把派遣与返回都强定一天。',relation='adds')
pk=person('王班',6,'出使契丹，到邺都不能前进而返回','辛巳，殿直王班使于契丹，至于鄴都，不得進而復。',source=anew)
edge='participation_zztj_283_0944_jin_mission_blocked_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['jin_mission_blocked'],role='出使契丹，到邺都不能前进而返回',status='draft'))
claim('person_event',edge,'role','王班奉命出使契丹，到邺都不能前进而返回。',6,'辛巳，殿直王班使于契丹，至于鄴都，不得進而復。','由新史补具名使者，不在主书摘录中虚构人名。',source=anew)
add('jing_yuying_commander','石重贵任景延广为御营使',6,'壬午，','为御营使，',[('帝','任景延广为御营使'),('景延广','由侍卫马步都指挥使任御营使')],when='944年正月壬午',place='后晋')
add('li_zhou_tokyo_regent','石重贵任李周留守东京',6,'前靖难','东京留守。',[('帝','任李周留守东京'),('李周','由前靖难节度使任东京留守')],when='944年正月壬午',place='东京')
sup('li_zhou_tokyo_regent',6,aold,'以前邠州節度使李周為權東京留守。','《旧五代史》记李周为权东京留守，此前职衔记作邠州节度使。','靖难邠州形式保留各书记载，权字为临时主持，不能据旧纪给他更高未载官职。',relation='adds')
add('gao_vanguard_departs','高行周率前军先出发',6,'是日，','前军先发。',[('高行周','率前军先行出发')],when='944年正月壬午',place='东京出发')
add('jing_controls_orders','晋军作战方略和号令由景延广决定，史书记他凌侮诸将，皇帝也难约束',6,'时用兵方略','亦不能制。',[('景延广','决定军中方略和号令，凌侮诸将'),('帝','史书记难以约束景延广')],place='晋军',note='这是此次用兵中的权力概述，不建立景延广实际篡位或所有宰相都任同一官职的事件。')
add('shi_departs_tokyo','石重贵从东京出发北征',6,'乙酉，','帝发东京。',[('帝','从东京出发北征')],when='944年正月乙酉',place='东京')
sup('shi_departs_tokyo',6,aold,'乙酉，車駕發東京。','《旧五代史》也记正月乙酉皇帝从东京出发。','出发日明确，不直接套用于此前先行的前军。')
add('huazhou_reports_liyang','滑州奏报契丹兵到黎阳',6,'丁亥，','至黎阳。',[],when='944年正月丁亥，奏报日',place='黎阳',note='奏报日与到达日不强同；新史丙戌寇黎阳为另书行动日期，保留差别。')
sup('huazhou_reports_liyang',6,anew,'丙戌，契丹寇黎陽。','《新五代史》记正月丙戌契丹进攻黎阳。','主书丁亥是滑州报告，不将动作日和奏报日作为必须相同的一日。',relation='adds')
add('shi_arrives_chanzhou','石重贵到达澶州',6,'戊子，','帝至澶州。',[('帝','到达澶州')],when='944年正月戊子',place='澶州')
add('khitan_stations_yuancheng','耶律德光驻元城，赵延寿驻南乐',6,'契丹主屯','屯南乐；',[('契丹主','驻军元城'),('赵延寿','驻军南乐')],place='元城、南乐')
add('zhao_weibo_weiwang','耶律德光任赵延寿为魏博节度使，封魏王',6,'以延寿','封魏王。',[('契丹主','任赵延寿为魏博节度使并封魏王'),('赵延寿','获魏博节度使及魏王封号')],place='魏博',note='此任命由契丹主作出，不写成后晋皇帝任命或赵已经即帝位。')
sup('zhao_weibo_weiwang',6,aold,'以趙延壽為魏博節度使，改封魏王，','《旧五代史》也记契丹任赵延寿为魏博节度使、改封魏王。','本句置于辛卯奏报帐驻元城条，奏日不直接作为契丹授官日。')
add('liu_bai_resist_taiyuan','刘知远与白承福合兵二万人，抵抗侵入太原的契丹兵',6,'契丹寇太原，','二万击之。',[('刘知远','与白承福合兵二万抵抗契丹'),('白承福','与刘知远合兵抵抗契丹')],place='太原',note='二万是联合兵力，不分别写两人各领二万。')
for code,title,start,end,name,role in [
('liu_youzhou_commander','石重贵任刘知远为幽州道行营招讨使','甲午，','行营招讨使，','刘知远','被任为幽州道行营招讨使'),
('du_deputy_commander','石重贵任杜重威为幽州道行营副使','杜威为','副使，','杜威','被任为行营副使'),
('ma_inspector','石重贵任马全节为幽州道行营都虞候','马全节为','都虞候。','马全节','被任为行营都虞候')]:
 add(code,title,6,start,end,[('帝','任命幽州道行营将领'),(name,role)],when='944年正月甲午',place='后晋')
sup('liu_youzhou_commander',6,aold,'甲午，以北京留守劉知遠為幽州道行營招討使，以恒州節度使杜威副之，定州節度使馬全節為都虞候，','《旧五代史》也记甲午任刘知远为招讨使、杜威为副、马全节为都虞候。','三职对应，幽州道为行营职掌，不将三人都定位为当日已进入幽州。')
add('zhang_defends_liyang','石重贵派张彦泽等率兵抵抗黎阳契丹军',6,'丙申，',None,[('帝','派张彦泽等率兵抵抗契丹'),('张彦泽','以右武卫上将军身份率兵抵抗契丹')],when='944年正月丙申',place='黎阳')
sup('zhang_defends_liyang',6,aold,'丙申，契丹攻黎陽。遣右武衛上將軍張彥澤等率勁騎三千以禦之。','《旧五代史》补充此次派遣劲骑三千人。','兵数只由旧纪补，不把等人未具名将领随意从别段搬入。',relation='adds')
# 7–11: Shu appointment policy, diplomatic failure, reported battle, money and letters.
add('shu_remote_commands_restored','孟昶恢复让将相遥领节度使的做法',7,'戊戌，',None,[('蜀主','恢复将相遥领节度使的做法')],when='944年正月戊戌',place='后蜀',note='未具名获任者不建立参与边；复表示恢复，不造新的蜀朝。')
add('meng_shouzhong_mission','石重贵派孟守忠致书契丹，请求恢复旧好',8,'帝复遣','求修旧好。',[('帝','派孟守忠请求恢复旧好'),('孟守忠','奉命向契丹致书')],when='944年正月己亥，日期由旧纪补证',place='后晋至契丹',note='请求修好不是两国已经恢复盟约。')
sup('meng_shouzhong_mission',8,aold,'己亥，遣譯詔官孟守忠致書於契丹主，求修舊好。','《旧五代史》明确孟守忠出使日在正月己亥。','己亥为派遣日，不强定其返回也在同日。',relation='adds',field='time_original')
add('khitan_refuses_peace','耶律德光回信表示局势已成，拒绝改变',8,'契丹主复书','不可改也。”',[('契丹主','回信拒绝恢复旧好')],when='944年正月孟守忠出使后，具体回信日期未载',place='契丹',note='已成之势是回信措辞，不将其直接作为后晋必败的事实判断。')
add('xiurong_victory_report','太原奏报在秀容击败契丹伟王，斩首三千，契丹军退入鸦鸣谷',8,'辛丑，',None,[('伟王（契丹）','其军被奏报在秀容战败')],when='944年正月辛丑，奏报日',place='秀容、鸦鸣谷',note='辛丑为太原奏报日；伟王个人姓名未证，不猜耶律氏哪一人。')
sup('xiurong_victory_report',8,aold,'辛丑，太原奏，與契丹戰於秀谷，斬首三千級，生擒五百人，獲敵將一十七人，賊軍散入鴉鳴谷，已進軍追襲。','《旧五代史》记战于秀谷，斩首三千，生擒五百、获敌将十七，并已进军追袭。','秀谷与通鉴秀容地名分别保留待核；生擒与获将数字范围不相加成伪精确总数。',relation='adds')
sup('xiurong_victory_report',8,anew,'辛丑，劉知遠及契丹偉王戰于秀容，敗之。','《新五代史》明确晋方交战将领为刘知远。','新史辛丑记战事，主书同干支记奏报，保留动作与报告的纪时差别。',relation='adds')
pk=person('刘知远',8,'在秀容击败契丹伟王','辛丑，劉知遠及契丹偉王戰于秀容，敗之。',source=anew)
edge='participation_zztj_283_0944_xiurong_victory_report_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['xiurong_victory_report'],role='在秀容击败契丹伟王，由《新五代史》补证',status='draft'))
claim('person_event',edge,'role','刘知远在秀容击败契丹伟王。',8,'辛丑，劉知遠及契丹偉王戰于秀容，敗之。','领军姓名由新史补证，不从主书未具名奏报强推。',source=anew)
add('yin_tiande_coins','殷国铸天德通宝大铁钱，一枚当百枚',9,'殷铸',None,[],place='殷国',note='名义币值一当百，不转换为现代购买力；未载具体铸钱官与铸地。')
add('jing_letters_min_yin','李璟致书王延羲、王延政，责备兄弟相争',10,'唐主遣使','兄弟寻戈。',[('唐主','致书责备闽殷两主兄弟相争'),('曦','收到李璟责备兄弟相争的书信'),('殷主','收到李璟责备兄弟相争的书信')],place='南唐、闽国、殷国')
add('min_justifies_brother_war','王延羲回信，用周公和唐太宗诛兄弟作类比',10,'曦复书，','元吉为比。',[('曦','回信以古代诛兄弟的事例辩解')],place='闽国',note='历史人物是信中类比，不创建周公、唐太宗等参与944年事件的边；不认可其政治辩解为唯一事实。')
add('yin_accuses_tang_usurpation','王延政回信，指责李璟夺杨氏国',10,'延政复书，','夺杨氏国。',[('殷主','回信指责李璟夺杨氏国'),('唐主','受到王延政的指责')],place='殷国、南唐',note='夺杨氏国是王延政的指责，既有937年吴唐禅代有独立史事记录，不据此改成944年才发生禅代。')
add('tang_cuts_yin_ties','李璟因王延政回信而怒，与殷国断交',10,'唐主怒，',None,[('唐主','因回信愤怒，断绝与殷往来'),('殷主','其政权与南唐断交')],place='南唐、殷国')
add('yan_sends_dou_report','颜衎派窦仪入奏周儒降契丹、引兵渡河及蔡行遇被俘',11,'天平节度副使','蔡行遇。”',[('颜衎','派窦仪向朝廷报告军情'),('窦仪','向朝廷转奏军情')],place='郓州至后晋朝廷',note='本条为奏报，所述降城、通使、渡河与被俘分别建事实并标明报告来源。')
add('zhou_ru_surrenders','颜衎奏报周儒以博州城投降契丹，并与杨光远通使',11,'博州刺史','通使往还，',[('周儒','被奏报以博州城投降契丹并与杨光远通使'),('杨光远','被奏报与周儒通使')],when='944年正月条下所奏前事，具体发生日期未载',place='博州、青州',note='博州周儒与888年魏军同名将领身份未证同一，分档；通使不是血缘或终身盟友关系。')
sup('zhou_ru_surrenders',11,anew,'博州刺史周儒叛降于契丹。','《新五代史》也记博州刺史周儒投降契丹。','只支持降契丹，不替未载通使或马家口路线作额外证明。')
add('zhou_ru_guides_river_crossing','颜衎奏报周儒引契丹从马家口渡河，蔡行遇被擒',11,'引契丹','蔡行遇。”',[('周儒','被奏报引契丹从马家口渡河'),('蔡行遇','被奏报遭契丹擒获')],when='944年正月条下奏报的前事，具体发生日期未载',place='马家口',note='擒者原文为契丹军，不自动改成周儒亲自擒蔡行遇；不补死亡。')
add('dou_warns_jing','窦仪警告景延广，契丹若渡河与杨光远会合，河南将有危险',11,'仪谓景延广','延广然之。',[('窦仪','向景延广说明契丹渡河会合的危险'),('景延广','认可窦仪警告')],place='后晋军中',note='若是条件判断，不把警告直接译为杨光远已和契丹在河南会师。')
claim('person',people['窦仪'],'description','窦仪为蓟州人。',11,'仪，蓟州人也。','史载籍贯，无另证不补出生村、年份或坐标。')
reviews={1:'乙亥边报与己卯陷城分开；先是储粮免邵、通契丹等追述分时，吴峦任贝州由旧纪943年十一月补。丘甫遇校皇甫遇，不改底本；吴峦投井、城陷杀近万独记。王令温入朝质邵子、家属被俘与调邓州独补，未用传末评价替代动作。',2:'两地组奏报无具体攻入日；旧紀围忻代补地点，未添战果。',3:'母疾与荷恩是杨光远辩解；使者劝说、转奏及朝廷慰谕分开，信言不等已止反。',4:'两任职主体明确，与此前周宋党争及镇海任职分期。',5:'传位为意图，限制召见、上疏不报、贾哭谏及撤令分开。两书月份及可奏者有异说；徐景遂徐景达复用。高楼讽谏和贬舒守备为未确年追述，井典故不造古人参与。',6:'使者未通由新史王班补；帝石重贵，授赵官契丹德光。壬午先军与乙酉帝行、丁亥报告与戊子至澶分开。联合二万不翻倍，幽州道是行营名。',7:'遥领恢复不虚构未具名将相参与。',8:'孟派己亥由旧纪补，拒和回信非同日硬系；辛丑主书奏报新史战事区别，秀谷秀容异文并列，伟王姓名未明。',9:'铁钱一当百为名义币值，不推购买力或铸地。',10:'兄弟相争信、两方答与断交分开，古人比喻不参与；夺国是王延政指责。',11:'奏报动作与报告前事分开；周儒另档避免跨56年同名强合；殿直王班与909年已死襄州刺史分档，擒蔡不记死亡；窦警条件非已会师。'}
assert not (P/'publication.json').exists()
for n in range(1,12):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=283,year=944,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,12)],next_paragraph='zztj-v284-y0944-p001',next_volume=284,next_year=944,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key=anew,note='快照含全年本纪，本批仅用于正月记载，后续主线尚未录。'),dict(source_key=jia,note='复用已发布快照，敕令月份和允许奏事者与通鉴不同，独立并列，不将五鬼前事再次建档。')],coverage='卷283原93—103行11正文全部连续处理，后接卷284原6行二月；944全年跨两卷55段，未完成。',source_issues_review='丘甫遇据同日同职校皇甫遇；南唐奏事敕令月份及人选异说，秀谷秀容地点异文、伟王身份待核。博州周儒与晚唐同名人未强合。王周沿用938—942年主体，早期901同名连接留待身份复核，未重做旧批。纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,12)],plain_language_review='首次检查人物、事件标题正文、参与角色、关系与事实说明，动作主语写明；报告日、行动日、建议、许诺、引用中的指责和追述分别标注，原文保持。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
