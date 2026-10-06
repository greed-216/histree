# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 954 paragraphs 25–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,39))
COMMIT='6e8f22e0feef7c5c3f1d27117d6777d1c8c5b7e7'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-114-campaign-march-954','xinwudaishi-12-chairong-accession','songshi-1-gaoping-counterattack']:
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
main_sources = ['tongjian-291-954-after-gaoping']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0954-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
for n in range(25, 33):
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
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·显德元年（954年正月至三月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0954_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0954_' + code
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
        edge = 'participation_zztj_291_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'柴荣','北汉主':'刘崇（刘知远弟）','北汉王':'刘崇（刘知远弟）','契丹主':'耶律璟','杨兗':'杨衮','史彦超':'史彦超（后周将领）','太祖皇帝':'赵匡胤','南汉主':'刘弘熙','弘邈':'刘弘邈','汉昭圣皇太后李氏':'李氏（刘知远妻）'})
NEW_ALIASES={'董希颜':['董希顏'],'田琼':['田瓊'],'李谦溥':['李謙溥'],'张汉超':['張漢超']}
NEW_DESCRIPTIONS={'董希颜':'北汉汾州防御使。954年四月王彦超进攻汾州时，董希颜以城向后周投降。《旧五代史》本纪及《新五代史》也记此事。生卒年未载。','田琼':'后周密州防御使。954年四月奉柴荣之命进攻北汉沁州，未能攻下。此处沿用《通鉴》姓名；《旧五代史》此前密州防御使作田中，两名是否同人尚待校核。生卒年未载。','李谦溥':'太原人，后周供备库副使。954年四月独自骑马说服辽州刺史投降后周。《宋史》也记同一职务与劝降行动，但把刺史姓名写作张乙，与《通鉴》张汉超不同。生卒年未载。','张汉超':'北汉辽州刺史。954年四月接受后周供备库副使李谦溥的劝说，以城投降。《新五代史》《旧五代史》也记张汉超归顺，《宋史》同役写作张乙，暂不作为确定别名。生卒年未载。'}
old='jiuwudaishi-114-campaign-march-954';awards='jiuwudaishi-114-awards-northward-954';april='jiuwudaishi-114-april-supply-954';new='xinwudaishi-12-chairong-accession';newhan='xinwudaishi-65-hongmiao-killed';song='songshi-273-li-qianpu-liaozhou'
add('liuchong_flees_by_diaoke','刘崇穿粗衣戴斗笠，率百余骑由雕窠岭逃走',25,'北汉主自高平被褐戴笠，','由雕窠岭遁归，',[('北汉主','乘契丹赠马，率百余骑逃离高平')],when='954年三月高平战败后',place='高平至雕窠岭',note='只记录逃走时所率百余骑，不把此数作为北汉全部残军人数。')
add('liuchong_kills_guide','刘崇夜间迷路，强迫村民带路，发现走向晋州后杀死向导',25,'宵迷，','杀导者。',[('北汉主','强迫村民带路，发现走错方向后杀人')],when='954年三月战败逃归途中',place='雕窠岭至晋州方向',note='原文只说向导误领，不把它写成村民有意诱骗的定论。')
add('liuchong_returns_exhausted','刘崇昼夜逃赶，听到周兵将至便离去，筋疲力尽回到晋阳',25,'昼夜北走，',None,[('北汉主','仓促北逃，体力衰竭后回到晋阳')],when='954年三月高平战败后',place='北逃路线至晋阳',note='传周兵至是途中传言，不把每次追兵都当作已经赶到。')
add('chairong_consults_zhang_military_law','柴荣犹豫是否处死逃将，张永德劝他严格军法',26,'帝欲诛樊爱能等','帝掷枕于地，大呼称善。',[('帝','向张永德询问处分逃将的意见'),('张永德','认为逃将应死，劝柴荣确立军法')],when='954年三月己亥',place='后周行宫',note='军事力量百万等为张永德论说中的假设，不填实际兵力数。')
add('chairong_executes_fan_he','柴荣处死樊爱能、何徽及其所属军使以上七十余人',26,'即收爱能、徽','悉斩之。',[('帝','拘捕并处死逃将及军官'),('樊爱能','因高平逃阵被处死'),('何徽','因高平逃阵被处死')],when='954年三月己亥',place='潞州行宫',note='卖与刘崇是柴荣的指责，不另录已证实投敌密谋；数量按原文七十余，不细分各人精确人数。')
sup('chairong_executes_fan_he',26,old,'己亥，侍衛馬軍都指揮使、夔州節度使樊愛能，侍衛步軍都指揮使、壽州節度使何徽等並諸將校七十餘人，並伏誅。','《旧五代史》也记己亥处死樊爱能、何徽等七十余将校。','两书所列樊爱能与何徽的军镇称号不同，各保留原名，不改变稳定人物身份。')
sup('chairong_executes_fan_he',26,new,'己亥，侍衞馬軍都指揮使樊愛能、步軍都指揮使何徽伏誅。','《新五代史》也记己亥樊爱能、何徽被处死。','只印证点名与纪日，未以本纪简文推断全部军官人数。')
for name in ['樊爱能','何徽']:
 claim('person',people[name],'death_year',f'{name}在954年三月己亥因高平逃阵被柴荣处死。',26,span(26,'即收爱能、徽','悉斩之。'),'死亡年依据本年正文及新旧五代史；对既有主体以事实引用补充，不无守卫地覆盖人物字段。')
add('chairong_gives_he_coffin','柴荣曾因何徽守晋州有功想赦他，最终仍按军法杀死，给棺归葬',26,'帝以何徽先守晋州有功，','给槥归葬。',[('帝','放弃赦免何徽，给棺让其归葬'),('何徽','旧功未能免死，获给棺归葬')],when='954年三月己亥处分逃将时',place='潞州',note='与前项同一次处决，单列赦免讨论及归葬安排，不另计一次死亡。')
sup('chairong_gives_he_coffin',26,old,'帝以何徽有平陽守禦之功，欲貸其罪，竟不可，與愛能俱殺之，皆給槥車歸葬。','《旧五代史》也记何徽旧守平阳有功，但未免死，并记两将均给棺车归葬。','主书点何徽给槥，旧史用皆补及樊爱能，分别保留叙述范围。',relation='adds')
claim('event',E['chairong_executes_fan_he'],'description','史书认为这次处决使骄将惰卒开始畏惧，朝廷不再姑息。',26,'自是骄将惰卒始知所惧，不行姑息之政矣。','这是《通鉴》对军纪效果的总结，不扩大为以后军队再无逃亡。')
for code,title,start,end,actors in [
 ('li_chongjin_zhongwu','柴荣因高平战功任李重进兼忠武节度使','庚子，赏高平之功，','以李重进兼忠武节度使，',[('帝','奖赏高平战功'),('李重进','兼任忠武节度使')]),
 ('xiang_xun_yicheng','向训因高平战功兼任义成节度使','向训兼义成节度使，','向训兼义成节度使，',[('向训','因战功兼任义成节度使')]),
 ('zhang_yongde_wuxin','张永德因高平战功兼任武信节度使','张永德兼武信节度使，','张永德兼武信节度使，',[('张永德','因战功兼任武信节度使')]),
 ('shi_yanchao_zhenguo','史彦超因高平战功任镇国节度使','史彦超为镇国節度使。'.replace('節','节'),'史彦超为镇国节度使。',[('史彦超','因战功任镇国节度使')])]:
 add(code,title,26,start,end,actors,when='954年三月庚子',place='后周')
sup('li_chongjin_zhongwu',26,awards,'庚子，以侍衛馬步都虞候李重進為許州節度使，以宣徽南院使向訓為滑州節度使，以殿前都指揮使張永德為武信軍節度使，職並如故。','《旧五代史》同日列李重进许州、向训滑州及张永德武信军节度任命，并记原职保留。','忠武与许州、义成与滑州对应军镇称谓，按同人同役补证，不分别造两个官员。')
sup('shi_yanchao_zhenguo',26,awards,'以鄭州防禦使史彥超為華州節度使，賞高平之功也。','《旧五代史》同记史彦超因高平战功任华州节度使。','镇国军与华州按同一军镇官职称谓保留，不改变人名限定。')
add('zhao_promoted_by_zhang','张永德盛赞赵匡胤，柴荣任赵匡胤为殿前都虞候、领严州刺史',26,'张永德盛称太祖皇帝之智勇，','领严州刺史，',[('张永德','向柴荣称赞赵匡胤的智勇'),('帝','提升赵匡胤的官职'),('太祖皇帝','获任殿前都虞候、领严州刺史')],when='954年三月庚子，《通鉴》接续赏功所记',place='后周',note='宋太祖赵匡胤此时未称帝；与郭威的后周太祖庙号区分。')
sup('zhao_promoted_by_zhang',26,'songshi-1-gaoping-counterattack','還，拜殿前都虞候，領嚴州刺史。','《宋史》也记赵匡胤任殿前都虞候、领严州刺史，但把它接在攻河东城后返还的叙述中。','职务相同，叙述先后不同；宋史此句无日，不强认其任命也在庚子。',relation='conflicts')
sup('zhao_promoted_by_zhang',26,awards,'以散員都指揮使李繼勛為殿前都虞候，','《旧五代史》庚子赏功名单列李继勋任殿前都虞候。','与《通鉴》接续记赵匡胤同职的叙述并列；两人不合并，任职先后及本纪名单完整性待核。',relation='conflicts')
add('ma_renyu_promoted_after_gaoping','柴荣任马仁瑀为控鹤弓箭直指挥使',26,'以马仁瑀为','控鹤弓箭直指挥使，',[('马仁瑀','获任控鹤弓箭直指挥使')],when='954年三月庚子赏功记载',place='后周')
add('ma_quanyi_promoted_after_gaoping','柴荣任马全乂为散员指挥使',26,'马全乂为','散员指挥使。',[('马全乂','获任散员指挥使')],when='954年三月庚子赏功记载',place='后周')
add('other_soldiers_promoted_gaoping','后周因高平战功迁升数十位将校，部分士卒被提拔领军',26,'自馀将校迁拜者','主军厢者。',[('帝','因战功迁升其他将校和士卒')],when='954年三月庚子赏功记载',place='后周',note='数十人按概数保留，不编造未明列的全部名单。')
add('zhao_chao_released','柴荣释放此前因建议持重而被囚的赵晁',26,'释赵晁之囚。',None,[('帝','释放赵晁'),('赵晁','获释')],when='954年三月庚子赏功记载末',place='后周',note='这里只明说赵晁获释，不据此写郑好谦也同日获释。')
add('han_repairs_jinyang_defenses','刘崇收拢逃散士卒，修整武器和城防，准备抵御后周',27,'北汉主收散卒，','以备周。',[('北汉主','收兵、修甲兵和城壕备战')],when='954年三月高平战败退归后',place='晋阳')
add('yang_gun_camps_daizhou','杨衮率契丹军北驻代州',27,'杨兗将其众','北屯代州，',[('杨兗','率军北驻代州')],when='954年三月高平战败后',place='代州')
add('wang_dezhong_requests_jinyang_rescue','刘崇遣王得中送杨衮并求援，耶律璟答应救晋阳',27,'北汉王遣王得中送兗，','许发兵救晋阳。',[('北汉王','派王得中送杨衮并向契丹求救'),('王得中','送杨衮后向契丹求援，奉回报'),('杨兗','由王得中护送'),('契丹主','答应出兵救晋阳')],when='954年三月高平战败后',place='代州及契丹',note='承诺发兵与援兵已经到达分开，未在此段录作完成救援。')
add('fu_army_advances_from_luzhou','柴荣任符彦卿统率河东行营，郭崇等分掌军职，率二万步骑从潞州出发',27,'壬寅，以符彦卿','将步骑二万发潞州。',[('帝','设置河东行营并命军队北进'),('符彦卿','任都部署兼知太原行府事，统军'),('郭崇','任符彦卿副将'),('向训','任都监'),('李重进','任马步都虞候'),('史彦超','任先锋都指挥使')],when='954年三月壬寅',place='潞州至河东')
sup('fu_army_advances_from_luzhou',27,awards,'壬寅，以天雄軍節度使、衛王符彥卿為河東行營都部署，知太原行府事；以澶州節度使郭崇為行營副部署；以宣徽南院使向訓為行營兵馬都監；以侍衛都虞候李重進為行營都虞候。以華州節度使史彥超為先鋒都指揮使，領步騎二萬，進討河東。','《旧五代史》同记河东行营五人分职、步骑二万进讨河东。','各职按原文分工保留，不把都监和先锋都当作副部署。')
relationship('郭崇','符彦卿','副将',27,span(27,'壬寅，以符彦卿','以郭崇副之，'),'三月壬寅河东行营郭崇是符彦卿的副将；复用此前已存在的同向关系，只补本次任职出处。')
add('wang_han_enter_yindiguan','柴荣命王彦超、韩通经阴地关入河东，与符彦卿合军',27,'仍诏王彦超、韩通','合军而进，',[('帝','命两将会合北进'),('王彦超','率军经阴地关与符彦卿会合'),('韩通','同经阴地关会师'),('符彦卿','受命与两将合军前进')],when='954年三月壬寅部署',place='阴地关至河东')
add('liuci_bai_escort_command','柴荣任刘词为随驾部署，白重赞为副将',27,'又以刘词',None,[('帝','任命随驾军的主副将'),('刘词','任随驾部署'),('白重赞','任随驾副将')],when='954年三月壬寅部署',place='后周随驾军')
relationship('白重赞','刘词','副将',27,span(27,'又以刘词'),'白重赞在954年三月壬寅所定随驾部署中是刘词的副将，限定本次军职。')
if B['person_relationships'][-1]['key'] not in reused:
 B['person_relationships'][-1]['description']='954年三月壬寅设置随驾军职时，白重赞是刘词的副将。';B['claims'][-1]['claim_text']=B['person_relationships'][-1]['description']
add('han_empress_li_dies','后汉昭圣皇太后李氏在西宫去世',28,'汉昭圣皇太后李氏殂于西宫。',None,[('汉昭圣皇太后李氏','在西宫去世')],when='954年三月壬寅部署之后、四月以前，具体日未载',place='西宫',note='复用刘知远妻、刘承祐母的李氏；后汉国亡后仍保留太后尊号，不误认后周新立皇后。')
claim('person',people['李氏（刘知远妻）'],'death_year','后汉昭圣皇太后李氏于954年在西宫去世。',28,Q[28]['text'],'正文在显德元年三月与四月之间；不自行补具体死亡日或改写已发布人物行。')
add('yuxian_submits_zhou','北汉盂县向后周投降',29,'夏，四月，','北汉盂县降。',[('帝','后周受降盂县')],when='954年四月',place='盂县')
add('fu_camps_jinyang','符彦卿率军驻晋阳城下',29,'符彦卿军晋阳城下，','符彦卿军晋阳城下，',[('符彦卿','驻军晋阳城下')],when='954年四月',place='晋阳城下')
add('dong_xiyan_surrenders_fenzhou','王彦超进攻汾州，董希颜向后周投降',29,'王彦超攻汾州，','北汉防御使董希颜降。',[('王彦超','进攻汾州'),('董希颜','向后周投降')],when='954年四月',place='汾州')
sup('dong_xiyan_surrenders_fenzhou',29,april,'河中節度使王彥超奏，偽汾州防禦使董希顏以城歸順。','《旧五代史》记王彦超奏报董希颜以汾州归顺，接在乙卯葬太祖之后。','奏报日期与实际归降日期不直接等同。')
sup('dong_xiyan_surrenders_fenzhou',29,new,'汾州防禦使董希顏叛于漢來附。','《新五代史》也记汾州防御使董希颜归附后周。','叛于汉是该书对转属的表述，与前文后汉李太后身份无关，这里指北汉。')
add('kang_tian_attacks_fail','柴荣派康延沼攻辽州、田琼攻沁州，两路均未攻下',29,'帝遣莱州防御使康延沼','皆不下。',[('帝','命两将分别攻城'),('康延沼','攻辽州未下'),('田琼','攻沁州未下')],when='954年四月',place='辽州、沁州',note='此时未下不等于以后两城也始终未降；田琼与旧本纪田中是否同人待核。')
add('li_qianpu_persuades_zhang','李谦溥单骑劝说辽州刺史张汉超，张汉超以城投降',29,'供备库副使太原李谦溥',None,[('李谦溥','独自骑马劝辽州刺史归降'),('张汉超','接受劝说，向后周投降')],when='954年四月',place='辽州')
sup('li_qianpu_persuades_zhang',29,april,'丙辰，偽遼州刺史張漢超以城歸順。','《旧五代史》把张汉超以辽州归顺记在四月丙辰。','主书此段只给四月，补证保留旧史明确纪日，不将劝说行动也全压成丙辰当天。',relation='adds')
sup('li_qianpu_persuades_zhang',29,song,'世宗征劉崇，遼州刺史張乙堅壁不下，遣謙溥單騎說之，乙以城降，以功改閑廄使。','《宋史》也记李谦溥单骑劝降辽州刺史，并记因功改任闲厩使；刺史姓名写作张乙。','主书与新旧五代史写张汉超，此传作张乙；保存姓名异说，不把张乙加入确定别名，也不把后续任职强定为四月某日。',relation='conflicts')
add('guowei_buried_songling','郭威在嵩陵下葬，庙号太祖',30,'乙卯，',None,[('郭威','以已故后周君主身份葬入嵩陵')],when='954年四月乙卯',place='嵩陵',note='本段周太祖为郭威，与前段宋太祖赵匡胤不同；三月奉棺赴陵的命令与此处实际下葬分开。')
sup('guowei_buried_songling',30,april,'夏四月乙巳，太祖靈駕發東京。乙卯，葬於嵩陵。','《旧五代史》同记四月乙卯葬郭威于嵩陵，另记乙巳灵驾从东京出发。','保留先出发后下葬的安排，不把乙巳当下葬日。')
add('hongmiao_assigned_yongzhou','刘弘熙任高王刘弘邈为雄武节度使，镇守邕州',31,'南汉主以高王弘邈','镇邕州。',[('南汉主','命刘弘邈镇邕州'),('弘邈','获任雄武节度使')],when='954年四月戊午被杀以前',place='邕州')
add('hongmiao_requests_guard_duty','刘弘邈担忧齐王、镇王先前死于邕州，拒赴任并求宿卫，未获准',31,'弘邈以齐、镇二王','求宿卫，不许。',[('弘邈','拒赴邕州，申请留在宫廷宿卫'),('南汉主','不许刘弘邈改任宿卫')],when='954年四月任镇邕州时',place='南汉朝廷',note='二王先前死亡在旧批次已有记载，不重建为954年死亡；求职遭拒与实际赴镇分开。')
add('hongmiao_delegates_government','刘弘邈到邕州后把政务交给僚佐，日日饮酒祈祷',31,'至镇，','祷鬼神。',[('弘邈','到任后委政僚佐并饮酒祈祷')],when='954年四月赴邕州后、被杀前',place='邕州',note='日饮酒为史书记述，不补未记载的心理诊断。')
add('hongmiao_poisoned','有人诬告刘弘邈谋乱，刘弘熙派林延遇赐毒酒杀他',31,'或上书诬弘邈谋作乱，',None,[('弘邈','受到谋乱诬告并被毒杀'),('南汉主','命人赐毒酒杀刘弘邈'),('林延遇','奉命执行赐毒酒')],when='954年四月戊午',place='邕州',note='原文定性为诬告，不将谋乱写成刘弘邈已经实施的事实。')
sup('hongmiao_poisoned',31,newhan,'晟殺其弟洪邈。','《新五代史》记刘晟杀其弟洪邈。','刘晟复用刘弘熙主体，洪邈对应高王刘弘邈；原字保留，此句无具体日，不凭单句加毒酒细节。')
claim('person',people['刘弘邈'],'death_year','刘弘邈于954年四月戊午被南汉君主派人赐毒酒杀死。',31,span(31,'戊午，'),'死亡时间根据主书明确纪时，人物行留作既有档案，不无守卫覆盖。')
relationship('刘弘熙','刘弘邈','兄长',31,'晟殺其弟洪邈。','新史明称洪邈为刘晟之弟，因此刘弘熙是刘弘邈的兄长；复用同人，保持方向。',source=newhan)
add('chairong_initial_show_force','柴荣最初只命符彦卿等在晋阳城下示威，尚未议定攻取',32,'初，帝遣符彦卿等北征，','未议攻取。',[('帝','最初计划在晋阳城下展示军力'),('符彦卿','受命率军北征示威')],when='954年三月派军北征时的追述',place='晋阳城下',note='初回述本次北征开端，不另造四月才首次派兵事件；与后续转向吞并区分。')
add('han_people_offer_supplies','后周军进入北汉后，当地民众诉说赋役繁重，愿供粮助攻',32,'既入北汉境，','北汉州县继有降者。',[('符彦卿','所领周军进入北汉，受到部分民众迎接')],when='954年三月至四月北进过程中',place='北汉境内',note='保留史书对民众迎军与赋役的叙述，不外推全部北汉居民均支持后周。')
add('chairong_rejects_supply_objection','柴荣产生兼并北汉的意图，诸将以粮草不足请撤，他未接受',32,'帝闻之，','帝不听。',[('帝','与诸将商议并拒绝因缺粮撤兵')],when='954年四月北汉州县陆续归降后',place='后周朝廷与河东军前',note='吞并意图与已成功吞并分开，诸将反映粮草不足并非此时补给已完全断绝。')
add('zhou_looting_alienates_people','后周诸军聚太原城下，士兵抢掠，使北汉民众转入山谷自保',32,'既而诸军数十万','稍稍保山谷自固。',[('帝','所统周军发生抢掠，民众转而自保')],when='954年四月围晋阳过程中',place='太原城下及附近山谷',note='数十万为主书叙述总兵力的概数，不用它覆盖三月符彦卿所领二万人的具体部署。')
add('chairong_bans_looting','柴荣诏令禁止抢掠、安抚农民，只征当年租税',32,'帝闻之，驰诏禁止剽掠，','止征今岁租税，',[('帝','下令止掠安民，只征当年租税')],when='954年四月围晋阳期间',place='河东军前',note='只征当年租税不是当年全部免税，不能把止征译成停止征税。')
sup('chairong_bans_looting',32,april,'詔河東城下諸將，招撫戶口，禁止侵掠，只令征納當年租稅，','《旧五代史》也记禁止侵掠、招抚户口、只征当年租税。','两书税令含义一致，未将只征当年写成一切税赋全免。')
add('grain_donations_awarded_offices','柴荣募民众交粮草，按数量授予出身或官职',32,'及募民入粟拜官有差，','及募民入粟拜官有差，',[('帝','按民众交纳粮草的数量给身份或官职')],when='954年四月军粮不足时',place='后周与河东军前')
sup('grain_donations_awarded_offices',32,april,'及募民入粟五百斛、草五百圍者賜出身，千斛、千圍者授州縣官。','《旧五代史》补记交粟五百斛、草五百围获出身，千斛、千围者授州县官。','斛与围沿原计量，不无证据换算为公斤；授出身与授官分别保留。',relation='adds')
add('chairong_mobilizes_food_transport','柴荣征发泽潞晋绛慈隰及山东近便州民众运粮供军',32,'仍发泽、潞、晋、绛、慈、隰','运粮以馈军。',[('帝','动员各州民众运输军粮')],when='954年四月围晋阳期间',place='泽、潞、晋、绛、慈、隰及山东近便诸州至太原',note='山东是原书当时地域称谓，不直接对应现代山东省辖境。')
add('ligu_assesses_taiyuan_supplies','柴荣派李谷赴太原核算粮草',32,'己未，',None,[('帝','派李谷核算军需'),('李谷','赴太原核算粮草')],when='954年四月己未，《通鉴》纪日',place='太原')
sup('ligu_assesses_taiyuan_supplies',32,april,'丁巳，幸柏谷寺。遣右僕射、平章事、判三司李穀赴河東城下，計度軍儲。','《旧五代史》把派李谷赴河东城下核算军储接在四月丁巳之后。','主书己未与旧史丁巳接续不同，分别保留，不擅自统一日期。',relation='conflicts',field='time_original')
reviews={25:'按原文明示整理逃归路径及杀向导，未把误领推定为故意诱骗，路上传闻与已到追兵分开。',26:'处分七十余将校与何徽赦免讨论分开，未重复记死亡。按原文逐项记录赏功与赵晁获释；赵匡胤任职的宋史叙述先后、旧史李继勋同职名单另存差异，未合并人物。',27:'收兵备战、驻代州、请求援兵与实际出发分别记录；郭崇副符彦卿复用既有关系，白重赞副刘词限定本次随驾部署。',28:'李太后复用刘知远妻的已核主体，死亡在本年三月和四月之间，不造具体日。',29:'攻城失败与之后受降分开，张乙与张汉超的异名待核，田琼与旧史田中不直接合并。',30:'周太祖指郭威，宋太祖指赵匡胤；三月护送遗体、四月乙巳灵驾出发及乙卯下葬区别保留。',31:'拒镇、到镇委政、谋乱诬告与实际赐毒分开，既有齐镇二王死亡不重录为954年。新史刘晟与洪邈沿已核主体补书证，兄长方向明确。',32:'初回述最初示威计划，后续吞并意图不是成功结果；数十万兵力概数不覆盖二万出军令。只征当年并非免税，粮草授官数量及李谷日期差异保留出处。'}
assert not (P/'publication.json').exists()
for n in range(25,33):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],next_volume=291,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷291原105—112行连续八段，从高平战后至围晋阳筹粮；954年跨两卷未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,33)],source_issues_review='保留张汉超与张乙、田琼与田中、赵匡胤任职先后及李谷赴军日期差异，不以自动繁简转换消除异说。纸本及异文待核。',plain_language_review='首次逐条检查标题、人物、角色、关系、时间与事实说明；指责和诬告不当作已证密谋，军令、求援承诺与实际行动分别说明，引用保持底本原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
