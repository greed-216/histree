# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 14–19."""
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
COMMIT='3c44c1173db8c2bfe524e8a0bfd15e49f18b53b9'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-jin-army']:
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
main_sources = ['tongjian-286-947-jin-army','tongjian-286-947-officials-looting']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p014-p019',
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
for n in range(14, 20):
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
    ck = f'claim_zztj_286_0947_04_{len(B["claims"])+1:04d}'
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
ALIASES.update({'契丹主':'耶律德光','蜀主':'孟昶','兀欲':'耶律阮','匡赞':'赵匡赞','潘聿撚':'潘聿捻','李继勋':'李继勋（后蜀将领）','李肃':'李肃（晋昌节度副使）','拽刺':'拽剌（西奚王）'})
NEW_ALIASES={'李继勋（后蜀将领）':['李繼勳（後蜀將領）'],'刘晞':['劉晞'],'留珪':[],'郎五':[],'潘聿捻':['潘聿撚'],'赵匡赞':['趙匡贊'],'史佺':[],'刘晏僧':['劉晏僧'],'李肃（晋昌节度副使）':['李肅（晉昌節度副使）'],'述轧':['述軋']}
NEW_DESCRIPTIONS={'李继勋（后蜀将领）':'后蜀左千牛卫上将军。947年正月癸丑，孟昶任命他为秦州宣慰使。使用国别限定身份，暂未与后周宋初同名将领合并，生卒年未载。','刘晞':'涿州人，在契丹曾任枢密使、同平章事及燕京留守。947年任西京留守，到洛阳后责斥奚王慢待赵在礼。与后晋官员刘昫字形、职务不同，暂不合并；生卒年未载。','留珪':'耶律阮（兀欲）的弟弟。947年正月耶律德光任命他为义成节度使。原书仅给名留珪，不自行补姓及后世异名，生卒年未载。','郎五':'947年正月耶律德光任命他为镇宁节度使。《资治通鉴》称其为族人，具体亲等未说明，不建立具体血缘关系；生卒年未载。','潘聿捻':'耶律阮的姐夫。947年正月被任命为横海节度使，原文字形为潘聿撚，展示采用捻并保留原字别名。生卒年未载。','赵匡赞':'赵延寿的儿子。947年正月受耶律德光任命为护国节度使。生卒年未载。','史佺':'947年正月受耶律德光任命为彰义节度使，但史匡威拒绝交出该镇。本段未载史佺实际到任，生卒年未载。','刘晏僧':'契丹客省副使。947年正月被任命为忠武节度使，姓名中的僧字不作为宗教身份依据。生卒年未载。','李肃（晋昌节度副使）':'947年赵在礼入朝后，留在长安的部将作乱，他以晋昌节度副使身份平定叛乱。原文籍贯写建人，疑有缺字，未补成具体地名；暂未与936年单州刺史同名人合并，生卒年未载。','述轧':'契丹将领。947年耶律德光派他与奚王拽刺、高谟翰驻守洛阳。生卒年、具体家族未载。'}
t='947年正月';j='jiuwudaishi-090-zhao-death';jl='jiuwudaishi-096-liu-detained';nw='xinwudaishi-046-zhao-death'
add('li_jixun_shu_qinzhou_commission','孟昶任命后蜀将领李继勋为秦州宣慰使',14,'癸丑，',None,[('蜀主','任命秦州宣慰使'),('李继勋','以左千牛卫上将军身份获任')],when=t+'癸丑',place='后蜀朝廷至秦州',note='宣慰使是任命，未以本句断言已抵秦州；用国别限定以免与后周宋初同名将领自动混合。')
# The list records commissions, not proof that every appointee took possession.
appointments=[('liu_xi_xijing','刘晞','以前燕京留守刘晞为西京留守','契丹主以前燕京留守刘晞','西京留守，','由燕京留守获任西京留守','洛阳'),('liu_gui_yicheng','留珪','以留珪为义成节度使','永康王兀欲之弟','义成节度使，','获任义成节度使','义成军'),('lang_wu_zhenning','郎五','以郎五为镇宁节度使','族人郎五','镇宁节度使，','获任镇宁节度使','镇宁军'),('pan_henghai','潘聿撚','以潘聿捻为横海节度使','兀欲姊婿','横海节度使，','获任横海节度使','横海军'),('zhao_kuangzan_huguo','匡赞','以赵匡赞为护国节度使','赵延寿之子','护国节度使，','获任护国节度使','护国军'),('zhang_yanchao_xiongwu','张彦超','以张彦超为雄武节度使','汉将张彦超','雄武节度使，','以汉将身份获任雄武节度使','雄武军'),('shi_quan_zhangyi','史佺','以史佺为彰义节度使','史佺为','彰义节度使，','获任彰义节度使','彰义军'),('liu_yanseng_zhongwu','刘晏僧','以刘晏僧为忠武节度使','客省副使刘晏僧','忠武节度使，','以客省副使身份获任忠武节度使','忠武军'),('hou_yi_fengxiang','侯益','以侯益为凤翔节度使','前护国节度使侯益','凤翔节度使，','由原护国节度使获任凤翔节度使','凤翔军'),('jiao_jixun_baoda','焦继勋','以焦继勋为保大节度使','权知凤翔府事焦继勋','保大节度使。','由暂管凤翔府获任保大节度使','保大军')]
for code,name,verb,start,end,role,place in appointments:
 add(code,'耶律德光'+verb,15,start,end,[('契丹主','任命地方长官'),(name,role)],when=t+'具体日未载',place=place,note='名录对应受命，不据官镇所在地填已抵任或坐标；原官职与新官职分别。')
relationship('兀欲','留珪','兄长',15,span(15,'永康王兀欲之弟','义成节度使，'),'明确记留珪为耶律阮之弟，兄长方向由阮指向留珪，不自动补姓。')
relationship('潘聿撚','兀欲','姐夫',15,span(15,'兀欲姊婿','横海节度使，'),'姊婿为姐姐的丈夫，潘聿捻是耶律阮的姐夫，未名姐姐不造具名实体。')
relationship('赵延寿','匡赞','父亲',15,span(15,'赵延寿之子','护国节度使，'),'明确匡赞为赵延寿之子，父亲指向儿子。')
claim('person','person_刘晞','description','刘晞是涿州人。',15,span(15,'晞，','人也。'),'原文字形晞保留，不因与昫相似合并为中央官员刘昫。')
add('he_shi_refuse_weaken_khitan','何重建已归附后蜀，史匡威拒绝让位，史书记契丹势力因此受挫',15,'既而',None,[('何重建','归附后蜀使新任官受阻'),('史匡威','拒绝被替代'),('史佺','所获彰义任命遭现任拒绝')],when=t+'任命之后，具体日未载',place='雄武军、彰义军',note='何附蜀行动已在第9段录入，此处记任命受阻的后续影响；不重复三州降蜀事件。势稍沮为史家概述。')
add('zhao_leaves_changan_officers_rebel','赵在礼入朝，留在长安的部将作乱',16,'晋昌节度使','作乱，',[('赵在礼','以晋昌节度使身份入朝，留守部将作乱')],when=t+'具体日未载',place='长安至大梁（入朝行程）',note='部将未具名，未把赵在礼认定为下令叛乱者。')
add('li_su_quells_changan_revolt','晋昌节度副使李肃讨伐作乱部将，长安军府恢复稳定',16,'节度副使',None,[('李肃','讨平叛乱，安定军府')],when=t+'赵在礼离镇后，具体日未载',place='长安',note='建人疑有缺字，原字保留且不补籍贯；与936单州刺史同名人暂分，不宣称已证异人。')
add('liu_jixun_admits_earlier_diplomacy_role','史书记石重贵与契丹断交时，刘继勋任宣徽北院使，曾参与谋议',17,'晋主之绝','预其谋。',[('刘继勋','在断交时曾参与谋议')],when='石重贵与契丹断交时（947年条下追述），具体日未载',year=None,place='后晋朝廷',note='匡国节度使为947所见职称，宣徽北院使为此前；不把断交作947新事件，也不由本句定为唯一谋主。')
add('khitan_questions_liu_jixun_blames_feng','刘继勋入朝被耶律德光责问，急指冯道、景延广为谋议主导，称自己未发言',17,'契丹主入汴，','何敢发言！”',[('刘继勋','被责问后推责于冯道景延广'),('契丹主','责问断交谋议'),('冯道','在殿上被刘继勋指称')],when=t+'耶律德光入京后，具体日未载',place='大梁宫廷',note='刘的否认参与是本人辩解，与史家颇预其谋并列；景延广只被提及，不造在场参与。')
sup('khitan_questions_liu_jixun_blames_feng',17,jl,'少帝在鄴，道為首相，與景延廣謀議，遂致南北失歡。臣位至卑，未嘗措言，今請問道，道細知之。','《旧五代史》也记刘继勋把失和归于冯道、景延广，自称没有发言。','辩解与该传亦预其谋不同，分别保留，不据话语裁定冯道确为谋主。')
add('khitan_defends_feng_detains_liu','耶律德光拒绝刘继勋牵连冯道，命锁押刘继勋，准备送往黄龙府',17,'契丹主曰：','黄龙府。',[('契丹主','拒绝牵连冯道，锁刘准备北送'),('冯道','得到耶律德光的辩护'),('刘继勋','被锁押，拟送黄龙府')],when=t+'刘继勋受责问后',place='大梁至黄龙府（拟送地）',note='将送是计划，后有获释，不能写已抵黄龙。')
sup('khitan_defends_feng_detains_liu',17,jl,'繼勛時有疾，契丹主因令人候其疾狀，雲有風痹，契丹主曰：「北方地涼，居之此疾可愈。」乃命鎖繼勛。','《旧五代史》还记刘继勋有风痹，耶律德光以北方凉可治病为说辞命锁。','这是补充传记说辞，不肯定北方气候能治病，也不代替主书处罚叙述。',relation='adds')
add('zhao_worries_luoyang','赵在礼到洛阳后，因耶律德光曾责他导致庄宗时的乱局而忧虑行程',17,'赵在礼至洛阳，','良可忧。”',[('赵在礼','在洛阳表达此行的忧虑')],when=t+'乙卯之前',place='洛阳',note='庄宗之乱由我致为转述耶律德光指责，不当唯一已证因果或947新乱。')
add('khitan_stations_three_luoyang_commanders','耶律德光派述轧、奚王拽刺、高谟翰驻守洛阳',17,'契丹主遣','戍洛阳，',[('契丹主','派三将驻洛阳'),('述轧','以契丹将身份驻守'),('拽刺','以奚王身份驻守'),('高谟翰','以渤海将身份驻守')],when=t+'赵在礼到洛阳前后，具体日未载',place='洛阳',note='奚王姓名通鉴拽刺、新史同一场景拽剌，沿已有西奚王主体暂复用，不合并941同名使者；既有西奚王是否确为本次人仍列待核。')
add('zhao_humiliated_by_luoyang_commanders','赵在礼拜见洛阳驻军将领，拽刺等坐着受礼，怠慢他',17,'在礼入谒，','受之。',[('赵在礼','在庭下拜见'),('拽刺','坐受赵在礼的拜礼')],when=t+'乙卯之前',place='洛阳',note='等未逐名具载哪两将如何行礼，不把述轧高谟翰全连入怠慢行为。')
sup('zhao_humiliated_by_luoyang_commanders',17,nw,'遇契丹拽剌等，拜於馬首，拽剌等兵共侵辱之，誅責貨財','《新五代史》称拽剌等及其士兵凌辱赵在礼，并索取财物。','姓名刺剌及拜礼位置庭下马首各按来源保留，士兵名单未知。',relation='adds')
sup('zhao_humiliated_by_luoyang_commanders',17,j,'契丹首領、奚王伊喇等在洛下，在禮望塵致敬，首領等倨受其禮，加之淩辱，邀索貨財','《旧五代史》称洛阳奚王为伊喇，也记凌辱和索财。','同一赵在礼赴洛场景下姓名另说，保留名异，不据此另造一次受辱或断言三个名字均已证同人。',relation='conflicts')
add('zhao_zaili_suicide_zhengzhou','赵在礼到郑州，听说刘继勋被锁押，当夜在马厩间自缢',17,'乙卯，','马枥间。',[('赵在礼','因得知刘继勋被锁而惊惧，夜间自缢')],when=t+'乙卯夜',place='郑州',note='惧与闻讯为史书顺叙，不把其全部动机限为这一件；自经用自缢，不补未载器具。')
sup('zhao_zaili_suicide_zhengzhou',17,j,'丁未歲正月二十五日夜，以衣帶就馬櫪自絞而卒，年六十六。','《旧五代史》明确正月二十五日夜，以衣带在马厩自缢，时年六十六。','原纪日与干支并存，不自行换算公历；年龄不反算生年。',relation='adds')
sup('zhao_zaili_suicide_zhengzhou',17,nw,'中夜惶惑，解衣帶就馬櫪自經而卒，年六十二。','《新五代史》也记衣带自缢，但记年龄六十二，与旧史六十六不同。','年龄异说不择一补出生年。',relation='conflicts')
claim('person','person_赵在礼','death_year','赵在礼在947年正月于郑州自缢，通鉴记乙卯夜，旧史记二十五日夜。',17,span(17,'乙卯，','马枥间。'),'死亡年明确；干支与月日分别保留，不直接改既有档案。')
add('liu_released_after_zhao_death','耶律德光听说赵在礼死亡，释放刘继勋',17,'契丹主闻','释继勋，',[('契丹主','闻赵死后释放刘继勋'),('刘继勋','获释')],when=t+'乙卯之后，具体日未载',place='大梁',note='乃释直接叙述先后，不增加具体密议原因。')
add('liu_jixun_dies_after_release','刘继勋获释后去世，通鉴称他忧愤而死',17,'继勋忧愤','而卒。',[('刘继勋','获释后死亡')],when='947年刘继勋获释后，具体月日未载',place='居所（主书未具体标）',note='忧愤为通鉴归因，旧传病亡说另列，未当已证临床死因。')
sup('liu_jixun_dies_after_release',17,jl,'尋解之，以疾終於家。','《旧五代史》称不久解锁，因病死在家中。','旧传正文病亡与通鉴忧愤分别保留，夹注通鉴不再作为独立确证。',relation='conflicts')
claim('person','person_刘继勋','death_year','刘继勋在947年获释后去世，确切月日未载。',17,span(17,'继勋忧愤','而卒。'),'按947年条下随后死亡记载，未将其强定乙卯同日。')
add('liu_xi_rebukes_xi_king','刘晞到洛阳，责斥奚王怠慢赵在礼，站在庭下压住其气焰，洛阳民众稍感安心',17,'刘晞在契丹',None,[('刘晞','到洛阳后责斥奚王并压住其气焰'),('拽刺','受到责斥')],when=t+'到洛阳后，具体日未载',place='洛阳',note='行文置赵死之后，实际到洛及责斥日未标；枢密使同平章事为在契丹旧职，未作947新任命。')
add('khitan_receives_tributes_boasts','耶律德光广收各地贡献，纵酒作乐，向晋臣声称自己了解中原而晋臣不懂契丹',18,'契丹主广受',None,[('契丹主','收贡献、饮酒作乐并发表言论')],when=t+'具体日未载',place='大梁',note='声称了解不等于知识全知；四方贡献未名贡者不补名单金额。')
add('zhao_requests_supplies_khitan_refuses','赵延寿请求供给契丹军粮，耶律德光以本国没有此惯例为由拒绝',19,'赵延寿请','吾国无此法。”',[('赵延寿','请求给军队粮食'),('契丹主','以无此惯例拒绝')],when=t+'具体日未载',place='大梁',note='无此法为本人说辞，不泛化成契丹所有时代无后勤制度。')
add('khitan_rotates_looting_grass_grain','契丹骑兵以牧马为名轮番外出劫掠，称为打草谷',19,'乃纵胡骑','打草谷”。',[('契丹主','纵容契丹骑兵外出劫掠')],when=t+'拒供粮之后，具体日未载',place='大梁周边及各地',note='牧马是名目，与实际劫掠分清；不把所有契丹居民当劫掠者。')
add('looting_devastates_capital_surroundings','史书记京畿和郑滑曹濮一带民众被杀、财物牲畜几乎耗尽',19,'丁壮毙',None,[],when='947年契丹劫掠期间，具体日未载',place='京畿一带及郑州、滑州、曹州、濮州',note='数百里及殆尽是史书概述，不转换为精准疆界、人口和损失数；遇害民众未具名，不虚造人物。')
reviews={14:'后蜀李继勋使用国别限定，任宣慰使不写已抵秦州。',15:'十项地方任命分别录入，不将任命等同占有辖地；兄长、姐夫、父亲三关系方向明确，郎五族人亲等不猜。何附蜀和史拒代记任命受阻，不重复降蜀原事。',16:'留长安部将未具名，李肃籍贯建人疑缺字不补，936同名官员暂分。',17:'刘断交谋议为追述，推责为辩解，北送为计划而最终释放。奚王刺剌伊喇各书异名并列，暂复用西奚王主体但保待核、不并941使者。赵死干支与旧二十五日、年龄66/62并列；刘病亡与忧愤并列。刘晞旧职不造新任命。',18:'自夸言论不当全知事实，未补未名贡者。',19:'请求粮食、拒绝、劫掠名目与民众损失分别；不补精确损失与全体参与者。'}
assert not (P/'publication.json').exists()
for n in range(14,20):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(14,20)],next_paragraph=Q[20]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原19—24行连续六段，累计19/92，本年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(14,20)],source_issues_review='新旧五代史赵死亡年龄及奚王名字不同；刘继勋死因和疾病补证分别；李肃身份及籍贯缺字、李继勋同名分档、奚王与既有主体对应仍待核。导出片段中的下一段私用字不在本批覆盖，未提前处理。',plain_language_review='首次逐条自查身份时间、白话主语行动、关系方向及引用，计划任命和实到、指责言论和事实区分；不扩大旧内容润色。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
