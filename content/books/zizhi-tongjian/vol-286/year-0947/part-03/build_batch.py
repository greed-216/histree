# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 10–13."""
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
COMMIT='4a7f7d906bca2ed23df36ebba9c517df6c6e2446'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['jiuwudaishi-085-947-january','liaoshi-004-947-january']:
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
main_sources = ['tongjian-286-947-jin-army']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p010-p013',
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
for n in range(10, 14):
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
    ck = f'claim_zztj_286_0947_03_{len(B["claims"])+1:04d}'
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
ALIASES.update({'晋主':'石重贵','契丹主':'耶律德光','杜重威':'杜重威','李太后':'永宁公主（石敬瑭妻）','太后':'永宁公主（石敬瑭妻）','安太妃':'安氏（石重贵母）','冯后':'冯氏（石重贵后）','睿':'石重睿','延煦':'石延煦','延宝':'石延宝','李彦韬':'李彦韬（后晋宣徽使）','兀欲':'耶律阮','东丹王':'耶律倍'})
NEW_ALIASES={'耶律阮':['耶律兀欲','兀欲','永康王']}
NEW_DESCRIPTIONS={'耶律阮':'小字兀欲，东丹王耶律倍之子。《资治通鉴》947年条下称永康王，记耶律德光将李彦绅、秦继旻的家属和财产交给他。《辽史》卷五明确名阮、小字兀欲，按同一主体建档；王号具体授封时间仍须另据后文校核，生卒年暂未录。'}
t='947年正月';j='jiuwudaishi-085-947-january';ls='liaoshi-004-947-january';lr='liaoshi-005-yelu-ruan';past='946年末至947年初晋军投降后（本段追述），具体日未载'
add('khitan_collects_jin_arms_horses','晋军投降后，契丹收取军械存于恒州，把战马赶回本国',10,'初，','归其国，',[('契丹主','收取晋军军械和战马'),('杜重威','其率降晋军的军械马匹被收取')],when=past,year=None,place='恒州及契丹',note='初追述跨年过程，不强定为947新发生。数百万铠仗、数万马为史书概数，不当已核库存精确值。')
add('du_leads_surrendered_troops_south','耶律德光让杜重威带原晋军随自己南下',10,'遣重威','而南。',[('契丹主','让杜重威率降军南下'),('杜重威','率领原晋军南下')],when=past,year=None,place='向南行军途中')
add('khitan_considers_drowning_surrendered_troops','契丹军到河边时，耶律德光担心降军生变，打算驱赶他们入河',10,'及河，','河流。',[('契丹主','担忧降军反抗，计划驱入河中')],when=past,year=None,place='行军至河边（本句未具河名）',note='欲为计划，未记实际集体溺杀；本句河名未具，未补明确渡口和坐标。')
add('unnamed_advice_spares_troops_chenqiao','有人劝耶律德光暂时安抚降军，他于是让杜重威带兵驻陈桥',10,'或谏曰：','屯陈桥。',[('契丹主','听从暂抚降军建议，改令驻陈桥'),('杜重威','受命率降军驻陈桥')],when=past,year=None,place='陈桥',note='劝者未具名，不强并赵延寿下一段建议。担心各地晋军拒降为建议推测，不当已发生。')
add('surrendered_troops_hungry_blame_du','陈桥降军遭连日雪天和断供，受冻挨饿，哭泣并怨恨杜重威，路人也责骂他',10,'会久雪，',None,[('杜重威','遭受降军怨恨和路人责骂')],when='946年末至947年初陈桥驻屯期间，具体日未载',year=None,place='陈桥',note='官无所给为供应状况，不补粮额；咸怨与道旁人皆骂为史书概述，不造具体全名单。')
add('khitan_still_plans_kill_surrendered_troops','耶律德光仍想杀死晋军降兵',11,'契丹主犹','诛晋兵。',[('契丹主','仍计划杀降军')],when=t+'陈桥降军驻屯时，具体日未载',place='大梁及陈桥',note='犹欲是持续意图，最终获免在段末另录，不提前写成已屠杀。')
add('zhao_questions_khitan_ownership','赵延寿询问耶律德光是否要自己占有晋地，耶律德光表示南征为自己取地',11,'赵延寿言','岂为他人乎！”',[('赵延寿','询问取晋地的目的'),('契丹主','称南征是为自己取晋地')],when=t+'讨论降军处置时',place='契丹主行营',note='五年不解甲是本人说辞，不作为连续每日着甲的事实，也不反算开战年份。')
add('zhao_proposes_southern_garrisons','赵延寿分析南唐、后蜀可能乘虚进攻，建议用陈桥降军驻守南部边境',11,'延寿曰：“晋国南','不能为患矣。”',[('赵延寿','建议让降军守南边，防范南唐后蜀'),('契丹主','询问应对方法')],when=t+'讨论降军处置时',place='契丹行营至南方边境（建议范围）',note='诸国攻入是赵的风险分析，不写已经发生；沂密秦凤范围为发言所举地域，不直接绘疆界。')
add('khitan_recalls_jin_grant_fears_rebellion','耶律德光称以前把唐军交给后晋导致后患，担心留下降兵再次反抗',11,'契丹主曰：“吾昔','后患乎？”',[('契丹主','引用此前授兵经历，表达杀降军的理由')],when=t+'讨论降军处置时',place='契丹行营',note='昔在上党授兵为言论追述，已有936建晋相关档案，不新造同一授兵事件；失败解释为本人判断。')
add('zhao_proposes_hostage_families_rotating_garrisons','赵延寿建议迁降军家属到恒、定、云、朔，以分番戍南边降低反抗风险',11,'延寿曰：“曏留','此上策也。”',[('赵延寿','提出迁家属并轮番驻防的方案')],when=t+'讨论降军处置时',place='恒州、定州、云州、朔州及南部边境（建议范围）',note='今若为方案，不写所有家属已迁。妻子为妻与子女，不译成只有配偶。')
add('khitan_accepts_zhao_spares_army','耶律德光采纳赵延寿的意见，陈桥降军得以免死，分遣返回军营',11,'契丹主悦曰：',None,[('契丹主','采纳意见，准降军免死'),('赵延寿','所提保留降军方案获采纳')],when=t+'讨论后，具体日未载',place='陈桥及各军营',note='段末明确免死及分遣还营；迁家属和年度轮番戍守未由本句证实全部实施。')
add('li_yanshen_qin_jimin_executed','耶律德光杀李彦绅、秦继旻，史书记原因为二人曾受李从珂之命杀东丹王',12,'契丹主杀','故也。',[('契丹主','因二人曾参与杀东丹王而处死'),('李彦绅','以右金吾卫大将军身份被处死'),('秦继旻','以宦者身份被处死')],when=t+'主书未标日，辽史系戊子',place='大梁',note='936年受命杀耶律倍为已录前事，不重复事件；主书在本段未给日，辽戊子独立补证。')
sup('li_yanshen_qin_jimin_executed',12,ls,'戊子，以樞密副使劉敏權知開封府，殺秦繼旻、李彥紳及鄭州防禦使楊承勛','《辽史》把处死秦继旻、李彦绅系于戊子。','主书未标具体日，记录另一书纪日作为补充，不改变段落顺序。',relation='adds',field='time_original')
for name in ['李彦绅','秦继旻']:
 claim('person','person_'+name,'death_year',name+'在947年正月被耶律德光命人杀死。',12,span(12,'契丹主杀','故也。'),'死亡年按本年记载，日由辽史补证另存。')
add('ruan_receives_executed_families_property','耶律德光将李彦绅、秦继旻的家属和财产交给东丹王之子耶律阮',12,'以其家族','兀欲。',[('契丹主','将被杀二人的家属财产交给耶律阮'),('兀欲','获得家属财产')],when=t+'二人被杀后，具体日未载',place='大梁',note='以其家族赀财赐同时涉及家属和财产，不只当纯财产赠与；不为未名家属建人物。兀欲名阮据辽史本纪独立补证。')
relationship('东丹王','兀欲','父亲',12,span(12,'东丹王之子','兀欲。'),'明记兀欲为东丹王之子，复用已核东丹王耶律倍；父亲方向由倍指向阮。')
claim('person','person_耶律阮','aliases','《辽史》记耶律阮的小字为兀欲。',12,'諱阮，小字兀欲。','卷五传主为世宗；只用于身份和异名，不提前把后续即位当此时已发生。',source=lr)
claim('person','person_耶律阮','description','《资治通鉴》记耶律阮一目失明、强健而乐于施予。',12,span(12,'兀欲眇一目',None),'眇一目为身体记载，雄健好施为史家评价，不补画像细节。')
add('shi_family_depart_north','石重贵、李太后、安太妃、冯皇后、石重睿及两子被押送北迁',13,'癸卯，','百馀人。',[('晋主','随家人北迁'),('李太后','随石重贵北迁'),('安太妃','随石重贵北迁'),('冯后','随石重贵北迁'),('睿','作为石重贵的弟弟同行'),('延煦','作为养子随行'),('延宝','作为养子随行')],when=t+'癸卯',place='大梁至契丹的北迁途中',note='三位女性主体分开复用，弟睿即已录石重睿；子沿已核养子，不改为血缘。百余随从是主书概数，与他书分项不强合总数。')
sup('shi_family_depart_north',13,ls,'癸卯，遣趙瑩、馮玉、李彥韜將三百騎送負義侯及其母李氏、太妃安氏、妻馮氏、弟重睿、子延煦、延寶等于黃龍府安置。','《辽史》也记癸卯押送石重贵全家北迁，弟弟全名重睿。','李氏是政治母亲身份，安氏为已有生母主体，不合并太后与太妃。')
add('zhao_feng_li_accompany_shi_north','契丹派三百骑护送，并让赵莹、冯玉、李彦韬随石重贵北行',13,'契丹遣三百','与之俱。',[('契丹主','派护送兵并令三臣同行'),('晋主','被三百骑护送'),('赵莹','以中书令身份同行'),('冯玉','以枢密使身份同行'),('李彦韬','以马军都指挥使身份同行')],when=t+'癸卯',place='北迁途中',note='援送是护送押送，未因此推三百骑以外绝无看守；李彦韬限定宣徽使主体与此前同人职迁相连，不误用温韬。')
add('shi_starves_on_north_journey','石重贵北迁时供给不继，有时与李太后都无食物，旧臣不敢前来见他',13,'晋主在涂，','进谒者。',[('晋主','在北迁路上缺食且无人敢见'),('太后','有时也无食物')],when='947年正月癸卯启程后的路途中，具体日未载',place='北迁途中',note='绝食是断粮无食，不写主动绝食抗议；不把供给失败限定只发生在某一天。')
add('li_gu_meets_shi_donates','李谷在路上迎见石重贵，两人相对哭泣，李谷尽力献出财物',13,'独磁州刺史','以献。',[('李谷','以磁州刺史身份迎见，献出财物'),('晋主','与李谷相见哭泣')],when='947年北迁途中，具体日未载',place='北迁途中（李谷迎见地未具体标）',note='磁州是李谷官地，不把迎见点强定磁州城内；倾赀为史书描述，未载确切金额。')
sup('li_gu_meets_shi_donates',13,j,'〈（《宋史·李穀傳》：少帝蒙塵而北，舊臣無敢候謁者，穀獨拜迎於路，君臣相對泣下。穀曰：「臣無狀，負陛下。」因傾囊以獻。）〉','《旧五代史》电子本夹注转引《宋史·李谷传》，也记路上迎见、哭泣和献财。','该句是夹注转引，不当旧史正文独立证据；直接宋史原段尚待补引。')
add('shi_cries_at_du_camp_zhongdu','石重贵到中度桥，看到杜重威军营旧址，责其毁了自己家国，哭着离去',13,'晋主至中度桥',None,[('晋主','见杜重威军营后哭泣离去'),('杜重威','成为石重贵当场责难对象')],when='947年北迁到中度桥时，具体日未载',place='中度桥',note='责难是石重贵表态，不当亡国唯一原因的分析；主中度、旧中渡字形分别保留。')
sup('shi_cries_at_du_camp_zhongdu',13,j,'帝過中渡橋，閱前杜威營寨之跡','《旧五代史》也记经过中渡桥看到杜重威军营遗迹。','桥名中度与中渡字形待校核，未补现代坐标。')
reviews={10:'初追述降军收械、马北运、南下与欲溺计划、陈桥驻屯冻饿；具体动作跨年不强定为947，未名劝者不并赵延寿。',11:'谋杀未执行，赵延寿风险判断及迁家属方案均为建议，段末实际免死还营单独记；五年为本人发言，昔授唐兵不重复前事。',12:'李秦死亡与家属财产交付分别，辽补戊子；父亲东丹王方向明确。兀欲为阮据辽身份段补证，不提前即位或虚造授封日期。',13:'太后太妃皇后三主体与养子弟弟分清，北迁癸卯不当抵达黄龙；供给短缺非主动绝食，李谷迎见未强定磁州；旧本夹注宋史为转引不作独立确证，中度渡异文保留。'}
assert not (P/'publication.json').exists()
for n in range(10,14):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(10,14)],next_paragraph=Q[14]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原15—18行连续四段，累计13/92，本年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(10,14)],source_issues_review='初追述跨年保留空年份；兀欲身份据辽阮小字补证，不提前授王即位；旧史夹注宋史不作独立确证，中度中渡字形保留。',plain_language_review='首次逐条检查白话主语和行动，身份时间、关系方向与引用一致；计划评价表态和实际动作分开。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
