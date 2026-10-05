# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 17–25."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,26))
COMMIT='b013bdbee16ef533670c03ff4c90acd31095c6c8'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-291-952-october','jiuwudaishi-112-november-952-hunan','jiuwudaishi-112-december-952-hunan','jiuwudaishi-112-january-953-yeji']:
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
main_sources = ['tongjian-291-952-october']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0952-p017-p025',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-952-october':'卷291·广顺二年十月至十二月','xinwudaishi-65-haoshi-952':'卷65·南汉世家第五·乾和十年蚝石之战','songshi-272-yangye-father':'卷272·列传第三十一·杨业'}
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
lines = (ROOT / 'resources/derived/tongjian/291.txt').read_text().splitlines()
for n in range(17, 26):
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
    labels={'tongjian-291-952-october':'卷291·广顺二年十月至十二月','xinwudaishi-65-haoshi-952':'卷65·南汉世家第五·乾和十年蚝石之战','songshi-272-yangye-father':'卷272·列传第三十一·杨业'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺二年（952年十一月至十二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0952_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=952, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='952年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0952_' + code
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
        edge = 'participation_zztj_291_0952_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0952_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','折从阮':'折从远','杨信':'杨信（麟州刺史）','重训':'杨重训'})
NEW_ALIASES={'杨信（麟州刺史）':['楊信（麟州刺史）'],'杨重训':['楊重訓'],'杨业':['楊業']}
NEW_DESCRIPTIONS={'杨信（麟州刺史）':'麟州地方豪强，曾自行担任刺史并获后周任命。去世后其子杨重训继任。《宋史》杨业传记杨业之父杨信为汉麟州刺史，按同地身份补充父子关系；不与安州节度使等同名者混同。生卒年未确。','杨重训':'麟州杨信之子，父死后继任刺史，曾以麟州归附北汉。952年遭围攻后重新归附后周，并向夏州、府州求援。生卒年未载。','杨业':'《宋史》记其为并州太原人，父亲杨信任汉麟州刺史。年轻时以骑射和勇武见称，后事刘崇。此处只补充父子身份及有明确原文的早年背景，具体生卒与后续经历待逐段补录。'}
oldnov='jiuwudaishi-112-november-952-hunan';olddec='jiuwudaishi-112-december-952-hunan';oldjan='jiuwudaishi-112-january-953-yeji';newhan='xinwudaishi-65-haoshi-952';songyang='songshi-272-yangye-father'
add('zhe_moves_jingnan','郭威将折从阮从保义调任静难节度使，令其讨伐野鸡族',17,'十一月，辛未，',None,[('帝','调折从阮任静难节度使并令其讨伐'),('折从阮','由保义调任静难节度使，受命讨伐野鸡族')],when='952年十一月辛未',place='保义军、静难军、庆州',note='复用已有折从远主体及折从阮别名；此处仅记调任及任务，不推出已经战胜。')
sup('zhe_moves_jingnan',17,oldnov,'辛未，陜州折從阮移鎮邠州。','《旧五代史》也记十一月辛未折从阮由陕州移镇邠州。','陕州与邠州分别对应保义、静难治所，用于印证同一次移镇，不将两种名称当作两次任职。')
add('guo_reduces_cowhide_tax','郭威减少牛皮征收三分之二，每十顷田征一张，余皮准许自用和买卖',18,'癸酉，敕：','惟禁卖于敌国。”',[('帝','减少牛皮征收并准许余皮自用买卖，但禁止卖给敌国')],when='952年十一月癸酉，《通鉴》纪日',place='后周',note='三分减二为减少原征收额的三分之二，不误写成减至原来的三分之二；仍有按田征收。')
sup('guo_reduces_cowhide_tax',18,oldnov,'應天下所納牛皮，今將逐所納數，三分內減二分，其一分於人戶苗畝上配定。每秋夏苗共十頃納連角皮一張，其黃牛納幹筋四兩，水牛半斤，犢子皮不在納限。','《旧五代史》补充每十顷纳连角皮一张，另规定黄牛、水牛筋额，犊子皮不在征收范围。','与减二分的规定印证；具体筋额是旧史敕文另载，不能扩成每种牛皮一律同额。',relation='adds')
sup('guo_reduces_cowhide_tax',18,oldnov,'甲戌，詔曰：「累朝已來，用兵不息，','《旧五代史》将该牛皮新规诏令记在十一月甲戌。','甲戌与《通鉴》癸酉不同，可能是公布记录差异，保留各书纪日，不自行换算后覆盖。',relation='conflicts',field='time_original')
sup('guo_reduces_cowhide_tax',18,oldnov,'牛馬驢騾皮筋角，今後官中更不禁斷，只不得將出化外敵境。州縣先置巡檢牛皮節級並停。','《旧五代史》还记解除牛马驴骡皮筋角的禁制，仅禁止运往敌境，并撤去州县巡检牛皮人员。','作为敕令范围的独立补充，不将一切动物产品或一般对外贸易都认定为解禁。',relation='adds')
add('earlier_hide_monopoly','此前战争期间禁止民间买卖牛皮，要求送官并支付价款',18,'先是，兵兴以来，','悉令输官受直。',[],year=None,when='此前战争时期的制度回述，起始年未载',place='中原',note='受直是获得价款，与后续停止补偿的制度分开，不归作952年首次立法。')
add('later_tang_hide_salt_payment','唐明宗时官府对征收牛皮只以盐偿付',18,'唐明宗之世，','有司止偿以盐；',[],year=None,when='后唐明宗在位时期的回述，本段未给具体实施年',place='后唐',note='只以盐补偿是主书所记，不等同全额现金价款；不自行补交易数量。')
add('later_jin_hide_no_payment','后晋天福年间，征收牛皮连盐补偿也不再支付',18,'晋天福中，','并盐不给。',[],year=None,when='后晋天福年间的回述，具体实施年未载',place='后晋')
add('later_han_private_hide_penalty','后汉对违反牛皮禁令规定极重处罚，史书称一寸也可处死',18,'汉法，','然民间日用实不可无。',[],year=None,when='后汉时期制度的回述，具体实施年未载',place='后汉',note='犯私牛皮按上下文为违反牛皮私有买卖禁制；记法令之严，不据此虚构某个已执行死刑的案件。')
add('ligu_proposes_land_hide_tax','李谷建议把牛皮征收均摊到田亩，郭威采纳以改革旧弊',18,'帝素知其弊，',None,[('李谷','建议牛皮征收均摊到田亩'),('帝','知道旧制度弊端，采纳按田亩征收建议')],when='952年牛皮新规出台前后的政策说明，具体建议日未载',place='后周朝廷',note='公私便之为史书对改革的概述，不编为逐户调查得出的精确效果。')
add('yellow_river_breaks_zhenghua','黄河在郑州、滑州决口，郭威派使察看并修补堵塞',19,'十二月，丙戌，',None,[('帝','派使察看黄河决口并组织修塞')],when='952年十二月丙戌',place='郑州、滑州',note='原河按郑滑所在及黄河上下文理解，修塞为派使处理任务，不断言全部堤工已于当日竣工。')
add('hou_zhang_offers_banquet_payment','侯章献绢千匹、银五百两作为买宴礼物',20,'甲午，前静难节度使侯章','银五百两。',[('侯章','以前静难节度使身份献绢与银买宴')],when='952年十二月甲午',place='后周朝廷',note='买宴为藩镇入朝宴犒相关进奉，不解释为私人宴席消费。')
add('guo_rejects_banquet_payment','郭威拒收侯章买宴礼物，规定以后同类进奉都不收',20,'帝不受，',None,[('帝','拒收买宴礼物并禁止以后收取同类进奉'),('侯章','所献买宴礼物被拒收')],when='952年十二月甲午',place='后周朝廷')
sup('guo_rejects_banquet_payment',20,olddec,'甲午，詔今後諸侯入朝，不得進奉買宴。','《旧五代史》同记十二月甲午禁止诸侯入朝进奉买宴。','与主书拒收及后续禁令相合，旧书未列本次绢银数量。')
add('wang_attacks_chenzhou','王逵率军与溪洞部众共五万人进攻郴州',21,'王逵将兵及洞蛮五万','攻郴州，',[('王逵','率军与溪洞部众共五万人攻郴州')],when='952年十二月条下，具体出兵日未载',place='湖南至郴州',note='五万按原文为军队及洞蛮的总规模，不能写成五万正规军另加不明数量；洞蛮是原书群体称谓，不套现代族别。')
add('pan_reinforces_haoshi','潘崇彻援救郴州，在蚝石与湖南军相遇，判断对方疲惫不整',21,'南汉将潘崇彻救之，','疲而不整，可破也。”',[('潘崇彻','援救郴州并判断湖南军疲惫、阵列不整')],when='952年十二月湖南军攻郴州后',place='郴州、蚝石',note='可破为潘崇彻交战前的判断，地点暂无可靠现代坐标。')
add('pan_defeats_wang_haoshi','潘崇彻在蚝石大败王逵军，史书形容尸体绵延八十里',21,'纵击，',None,[('潘崇彻','发起攻击并击败湖南军'),('王逵','所率湖南军被南汉击败')],when='952年十二月蚝石相遇以后',place='蚝石',note='伏尸八十里为原书战后描述，不可转为死亡人数或精确测绘长度。')
sup('pan_defeats_wang_haoshi',21,newhan,'十年，湖南王進逵以兵五萬率谿洞蠻攻郴州，潘崇徹敗進逵於蠔石，斬首萬餘級。','《新五代史》南汉乾和十年记王进逵率五万人攻郴州，潘崇彻在蚝石击败他，斩首一万余级。','乾和十年与952年上下文相合；斩首万余与伏尸八十里是不同表述，分别保留，不能将八十里换算一万人。',relation='adds')
add('xu_taifu_seeks_execution','徐台符请求处死诬告李崧的葛延遇与李澄',22,'翰林学士徐台符','葛延遇及李澄，',[('徐台符','请求处死诬告者'),('葛延遇','被徐台符请求追究诬告责任'),('李澄','被徐台符请求追究诬告责任')],when='952年十二月，癸卯处决以前',place='后周朝廷',note='该事件只记录请求，实际执行另录；李澄为已录诬告案主体，不与同名其他人物混同。')
add('feng_dao_invokes_amnesties','冯道认为葛延遇等已多次遇赦，反对处死他们',22,'冯道以为屡更赦，','不许。',[('冯道','以多次赦免为由反对追究处死')],when='952年十二月徐台符提出请求后',place='后周朝廷')
add('wang_jun_supports_xu','王峻赞许徐台符为李崧伸冤的主张，向郭威报告',22,'王峻嘉台符之义，','白于帝，',[('王峻','支持徐台符的主张并报告郭威')],when='952年十二月葛延遇等被处决以前',place='后周朝廷',note='原义为史书对主张的评价，展示写实际支持与报告，不编王峻额外言辞。')
add('ge_li_arrested_executed','后周逮捕葛延遇与李澄，将两人处死',22,'癸卯，收延遇、澄，',None,[('葛延遇','被后周逮捕并处死'),('李澄','被后周逮捕并处死')],when='952年十二月癸卯',place='后周',note='执行句未具名承办人员，承接朝廷裁决；不编冯道亲自改令或徐台符亲自行刑。')
add('liuyan_requests_langzhou_seat','刘言称潭州残破，请将使府移至朗州，并按马氏旧例贡献、卖茶',23,'刘言表称潭州残破，','悉如马氏故事。',[('刘言','请求迁使府至朗州及沿用马氏贡献卖茶旧例')],when='952年十二月条下，具体上表日未载',place='潭州、朗州',note='贡献、卖茶为同时提出的请求，不等同已在本日完成全部搬迁或取得永久贸易垄断。')
add('zhou_approves_langzhou_requests','后周批准刘言迁使府及沿用贡献、卖茶旧例的请求',23,'刘言表称潭州残破，',None,[('刘言','迁使府及贡献、卖茶旧例请求获后周批准')],when='952年十二月条下，批准日未载',place='后周朝廷、朗州')
sup('zhou_approves_langzhou_requests',23,oldjan,'乙卯，武平軍兵馬留後劉言奏：「潭州干戈之後，焚燒殆盡，乞移使府於武陵。」從之。','《旧五代史》在953年正月乙卯记刘言请求移使府于武陵并获准。','与主书952年十二月记请移朗州的纪时不同，可能记录奏请与处理环节；朗州武陵按同一治所背景对应，仍并列各书记载日期。',relation='conflicts',field='time_original')
add('ma_xie_held_at_court','马希萼入朝南唐，李璟将他留在朝中',24,'唐江西观察使楚王马希萼','唐主留之，',[('马希萼','以江西观察使、楚王身份入朝后被留下'),('唐主','将马希萼留在朝中')],when='952年十二月条下，具体入朝日未载',place='南唐朝廷',note='留之不直接译为下狱；未将其入朝之前的驻地与留朝后的金陵混为一处。')
add('ma_xie_later_dies','马希萼入朝后数年在金陵去世，谥号恭孝',24,'后数年，',None,[('马希萼','数年后在金陵去世，获恭孝谥号')],year=None,when='952年入朝后的数年，具体死亡年本段未载',place='金陵',note='后数年明确不是本年当即去世，保留待核，不将人物death_year设置为952。')
add('yang_xin_linzou_authority','麟州豪强杨信自行担任刺史，后获后周任命',25,'初，麟州土豪杨信','受命于周。',[('杨信','自行担任麟州刺史，随后获得后周任命')],year=None,when='后周建立后至952年末以前的回述，具体任命日未载',place='麟州',note='受命于周为后周正式承认，初为回述，不能一律按952年首次自立。')
add('yang_xin_dies_son_succeeds','杨信去世后，儿子杨重训继任刺史，并以麟州归附北汉',25,'信卒，','以州降北汉。',[('杨信','在儿子继任以前去世'),('重训','父死后继任，并以麟州归附北汉')],year=None,when='杨信获后周任命后至952年末被围以前，具体年月未载',place='麟州',note='原文给出次序，未给杨信死亡年，不因所在年条强填952年。')
add('yang_chongxun_returns_zhou','杨重训遭当地羌人围攻后重新归附后周，向夏州、府州求援',25,'至是，为群羌所围，',None,[('重训','遭围攻后归附后周，向夏州府州求援')],when='952年十二月条下，具体被围与求援日未载',place='麟州、夏州、府州',note='群羌为原书称谓，不自动映射现代族别；求救不等于援军已到或围攻已解除。')
relationship('杨信','重训','父亲',25,'信卒，子重训嗣，以州降北汉。','原文明示子重训，方向为杨信是杨重训的父亲；关系起止年月未载。')
relationship('杨信','杨业','父亲',25,'楊業，并州太原人。父信，為漢麟州刺史。','依据《宋史》杨业传同姓同麟州刺史身份补充，不与安州等地杨信混同；汉为该传旧政权背景，未据此重写通鉴受命后周的说法。',source=songyang)
reviews={17:'折从阮复用折从远及既有别名，旧书陕州邠州印证同日调镇，任命与实际战果分开。',18:'减额与田亩征收、旧制度四阶段、李谷建议分录；旧史甲戌与主书癸酉并列，筋角及巡检补充保留独立引用，不把减二分写成减至二分。',19:'决口与派使察看修塞记录为处理任务，不伪称已完工。',20:'侯章礼物与郭威拒收、后续禁令分开，旧纪同日印证，不扩大为取消全部藩镇进奉。',21:'五万是军队与溪洞部众总数，援救判断与战斗结果分开；新史乾和十年蚝石与主书对应，斩首万余与伏尸八十里不作数值换算。',22:'请求、遇赦反对、王峻奏报及朝廷处决分录，复用已录诬告案葛延遇李澄主体。',23:'上表与准许分开，旧书953正月日期与主书952十二月并列，不宣称全部迁府当天完工。',24:'952入朝被留与数年后死亡分开，死亡年未知；谥号保留，未作951就已卒。',25:'自任受命、死后继任降北汉、被围归周求援分开，初与至是区分；杨信父子身份有主书和宋传独立支持，同名安州人不混同。'}
assert not (P/'publication.json').exists()
for n in range(17,26):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=952,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,26)],next_paragraph='zztj-v291-y0953-p001',next_volume=291,next_year=953,supplements=supplements,excluded_non_body=[],coverage='卷291原22—30行连续九段，为本卷952年末尾，须跨卷290与卷291审计后才标全年完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,26)],source_issues_review='牛皮诏令纪日及迁府奏请跨年异说保留。马希萼后数年与杨信前事不填本年死亡；民间名词、政权背景与现代族别不强等同。杨信按麟州身份识别而非仅凭同名，纸本异文待核。',plain_language_review='首次逐条检查人物、事件、角色、关系、日期地点及事实解释，用现代白话说明主语和行动，保留制度阶段、请求与执行、追述与当前年区别；摘录不改字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
