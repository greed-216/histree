# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 36–41."""
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
COMMIT='c55e23db2fe30e33712619797f5300a286a58c03'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-accession','jiuwudaishi-099-imperial-title','jiuwudaishi-085-947-january']:
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
main_sources = ['tongjian-286-947-accession','tongjian-286-947-li-wuyue']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p036-p041',
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
for n in range(36, 42):
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
        citation = f'卷286·天福十二年（947年二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_08_{len(B["claims"])+1:04d}'
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
def existing(code,key,n,quote,text,note):
 rows=[x for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for x in json.loads(f.read_text())['events'] if x['key']==key]
 assert rows,key
 B['events'].append(dict(rows[0],status='draft'));reused.add(key);used.setdefault(n,[]).append(key);E[code]=key
 claim('event',key,'description',text,n,quote,note)
ALIASES.update({'帝':'刘知远','晋主':'石重贵','太后':'永宁公主（石敬瑭妻）','冯后':'冯氏（石重贵后）','契丹主':'耶律德光','弘佐':'钱弘佐','李氏':'李氏（刘知远妻）'})
NEW_ALIASES={'高唐英':[],'梁晖':['梁暉'],'李氏（刘知远妻）':['李氏（後漢高祖后）'],'储温':['儲溫']}
NEW_DESCRIPTIONS={
'高唐英':'契丹所任地方长官。947年二月刘知远即位后，被任命为彰德节度使；梁晖袭取相州时，他尚未到任。《旧五代史》同记相州節度使，《辽史》官号另作昭德，分别保留。生卒年未载。',
'梁晖':'滏阳武装首领，率数百人向刘知远请求效力，受李谷指示袭击相州。947年二月丁丑夜攻入相州，守将突围离开，梁晖自称留后并上报。生卒年暂未录入。',
'李氏（刘知远妻）':'晋阳人，刘知远的妻子。947年二月劝丈夫停止征民财劳军，改用宫中积蓄，建议获采纳。《旧五代史》称高祖皇后李氏，此时《通鉴》称夫人李氏，正式册后另在后续时间录入。名字与生卒年暂未录入。',
'储温':'吴越内牙指挥使。947年二月受钱弘佐命令，等待程昭悦回宅后拘捕他，送往东府。生卒年未载。'}
j='jiuwudaishi-099-imperial-title';ex='jiuwudaishi-085-947-january';f='xinwudaishi-017-feng-poison';li='jiuwudaishi-104-li-advice'
add('liu_goes_east_to_rescue_jin','刘知远亲率兵东行，迎接石重贵和太后',36,'甲戌，','晋主及太后。',[('帝','亲率兵东行迎接晋帝及太后'),('晋主','成为迎接对象'),('太后','成为迎接对象')],when='947年二月甲戌',place='河东向东',note='本段帝为已即位的刘知远，晋主为石重贵，太后为石敬瑭妻李氏，不能与下一段刘知远的李夫人混同。出发不等于已经迎回。')
sup('liu_goes_east_to_rescue_jin',36,j,'甲戌，帝以晉帝舉族北遷，憤惋久之。是日，率親兵趨土門路，邀迎晉帝至壽陽','《旧五代史》同记甲戌率亲兵经土门路往寿阳迎接晋帝。','汉高祖本纪的帝指刘知远，保留土门路这一补充路线。',relation='adds')
add('liu_leaves_chengtian_garrison_returns','刘知远到寿阳得知石重贵已过恒州，留兵守承天军后返回',36,'至寿阳，',None,[('帝','得知已错过晋帝行程，留兵守承天军并返回')],when='947年二月甲戌出行后，具体日未载',place='寿阳、承天军至河东',note='甲戌是出行记日，不把到寿阳及返回各行动全部硬定为同一天。闻已过恒州数日是所得消息，不推算过境日。')
sup('liu_leaves_chengtian_garrison_returns',36,j,'聞其已過，乃還。','《旧五代史》也记得知晋帝已过而返回。','该书未在此句给留兵细节，由主书单独支持；不扩大旧史摘录范围。')
add('jin_exiles_forage_after_supply_cut','契丹停止供给石重贵北迁队伍，随行官员和宫女采果实草叶充饥',37,'晋主既出寨，','而食之。',[('晋主','北迁队伍失去契丹供给')],when='947年北迁途中，离寨之后，具体月日未载',place='石重贵北迁沿途',note='官员宫女没有逐一姓名，不自动关联所有前晋官员；未载具体死亡人数。')
sup('jin_exiles_forage_after_supply_cut',37,ex,'至榆關沙塞之地，略無供給，每至宿頓，無非路次，一行乏食，宮女、從官但采木實野蔬，以救饑弊。','《旧五代史》记至榆关沙塞一带缺乏供给，宫女从官采木实野蔬充饥。','补充缺粮的地点与行程，依各书原文保留，不换算具体日期。',relation='adds')
add('jin_forced_honor_abaoji','契丹迫石重贵及后妃在锦州礼拜阿保机墓',37,'至锦州，','阿保机墓。',[('晋主','被迫在锦州礼拜阿保机墓')],when='947年北迁至锦州时，具体月日未载',place='锦州',note='契丹是此处行动方，没有点名具体执行者，不能直接加耶律德光为亲自押送者。后妃没有逐一名单，不补所有人的参与。')
sup('jin_forced_honor_abaoji',37,ex,'又行七八日至錦州，契丹迫帝與妃後往拜安巴堅遺像','《旧五代史》记锦州受迫礼拜安巴坚遗像。','《通鉴》写拜阿保机墓，《旧五代史》写拜遗像，保留对象表述差异；七八日为该书途中相对时长，不换算为公历日期。',relation='adds')
add('shi_blames_xue_for_survival','石重贵因受辱而哭泣，责怪薛超曾阻止自己自尽',37,'晋主不胜','薛超误我！”',[('晋主','哭泣并责怪薛超阻止自尽'),('薛超','受到石重贵责怪')],when='947年在锦州受辱之后，具体日未载',place='锦州',note='薛超的阻止行为已在946年录入；本事件记录947年的言论，不重复建立一次新的阻止行为，也不把指责当作史家定论。')
sup('shi_blames_xue_for_survival',37,ex,'帝不勝屈辱，泣曰：「薛超誤我，不令我死，以至今日也。」','《旧五代史》补出石重贵所说的不令我死、以至今日。','结合已录946年薛超拦阻投火的事件解释此话；言论仍归石重贵本人。',relation='adds')
add('feng_seeks_poison_without_success','冯皇后秘密命左右寻找毒药，想与石重贵一同自尽，未能实现',37,'冯后阴令',None,[('冯后','秘密求毒药，计划与晋帝一同自尽'),('晋主','成为冯皇后计划一同自尽的对象')],when='947年北迁锦州受辱之后，具体日未载',place='石重贵北迁沿途',note='不果表示未能实现，不能写为服毒或死亡。计划是冯皇后提出，不推石重贵已明确同意。')
sup('feng_seeks_poison_without_success',37,f,'后隨帝北遷，哀帝之辱，數求毒藥，欲與帝俱飲以死，而藥不可得。','《新五代史》记冯后多次求毒药，但未能取得。','该传概述北迁期间的多次求药，没有把每次都定位锦州同一日；保留其补充范围。',relation='adds')
add('khitan_appoints_geng_zhaoyi','耶律德光听说刘知远即位，任耿崇美为昭义节度使',38,'契丹主闻','昭义节度使，',[('契丹主','因刘知远即位部署控制要地'),('耿崇美','获任昭义节度使')],when='947年二月刘知远即位后，具体日未载',place='昭义（任职地）',note='授职不等于已经抵达所任地点；官职按主书保留。')
sup('khitan_appoints_geng_zhaoyi',38,j,'以通事耿崇美為潞州節度使','《旧五代史》同记耿崇美获任潞州节度使。','潞州为昭义治所，保留书中各自官职写法，不补抵达日。',relation='adds')
add('khitan_appoints_gao_tangying','耶律德光任高唐英为彰德节度使',38,'高唐英','彰德节度使，',[('契丹主','任高唐英控制彰德'),('高唐英','获任彰德节度使')],when='947年二月刘知远即位后，具体日未载',place='相州彰德（任职地）',note='任命与后文尚未到任分清。《辽史》写昭德，《通鉴》写彰德，不覆盖原书字形。')
sup('khitan_appoints_gao_tangying',38,j,'高唐英為相州節度使','《旧五代史》记高唐英任相州节度使。','相州为彰德治所，沿同一人物识别，不补已经到任。',relation='adds')
add('khitan_appoints_cui_heyang','耶律德光任崔廷勋为河阳节度使',38,'崔廷勋',None,[('契丹主','任崔廷勋控制河阳'),('崔廷勋','获任河阳节度使')],when='947年二月刘知远即位后，具体日未载',place='河阳（任职地）',note='以控扼要害是史书所述部署目的，授职不自动表示军队已经驻守成功。')
sup('khitan_appoints_cui_heyang',38,j,'崔廷勛為河陽節度使，以扼要害之地。','《旧五代史》同记崔廷勋为河阳节度使，以控制要地。','对应主书同一部署，具体任命日未载。')
add('jin_raises_then_dismisses_tianwei_militia','后晋曾设天威乡兵，训练一年多未成战力，随后解散',39,'初，晋置','悉罢之，',[],when='947年条下追述后晋乡兵，具体起止年未载',year=None,place='后晋乡兵征集地区，具体范围未载',note='初为追述，训练一年多不据此反算建立年份；不可用为史书记述，不推每个村民的能力。')
add('jin_militia_replaced_by_payments','后晋解散乡兵后，改令每七户交钱一万，铠甲武器交官',39,'但令','悉输官。',[],when='后晋解散天威乡兵之后，具体年日未载',year=None,place='后晋相关征集地区',note='十千按原文表示一万钱，未补币制、重量或现代金额；缴纳制度不表示所有户都已交纳。')
add('former_militia_join_banditry','史书追述部分乡兵子弟不肯回务农，山林盗匪因而增多',39,'而无赖子弟，','自是而繁。',[],when='后晋解散乡兵之后，具体起止年未载',year=None,place='山林地区，具体范围未载',note='无赖是史书评价，展示写部分子弟；因而增多是该书的因果解释，不当逐一证明全部乡兵变为盗匪。')
existing('looting_background','event_zztj_286_0947_khitan_rotates_looting_grass_grain',39,span(39,'及契丹入汴，','纵胡骑打草谷。'),'《资治通鉴》在后续背景叙述中再次记契丹入汴后纵骑兵打草谷。','复用此前已经建立的打草谷事件，本条补充后续原文引用，不重复新建同一事件。')
add('khitan_local_appointees_exploit_people','史书概述契丹多任亲近者治理州镇，依附者教其滥权敛财，百姓不堪负担',39,'又多以其子弟','民不堪命。',[],when='947年契丹入汴后的背景概述，具体起止日未载',place='契丹控制的州镇',note='本段为史家概述，没有列具体官员和受害者，不自动套用到已录每一名契丹任命者。')
add('armed_groups_attack_prefectures','史书记各地武装聚众，从千百人至数万人不等，攻州县并杀掠吏民',39,'于是所在相聚','杀掠吏民。',[],when='947年契丹入汴后，各次行动具体日未载',place='相关州县，具体范围未载',note='人数是概述中的规模范围，不转成一支军队的精确兵数；杀掠吏民为原书所记，不能只写为无代价的起义胜利。')
add('liang_hui_requests_service','梁晖率数百人向晋阳请求为刘知远效力，刘知远同意',39,'滏阳贼帅','帝许之。',[('梁晖','向刘知远请求效力'),('帝','接受梁晖请求')],when='947年二月丁丑之前，具体日未载',place='滏阳至晋阳',note='贼帅是史书称谓，展示用武装首领；数百不推具体数，效力不是已经获得节度使官职。')
add('li_gu_directs_liang_hui','李谷秘密上表刘知远，令梁晖袭击相州',39,'磁州刺史','令晖袭相州。',[('李谷','以磁州刺史身份秘密上表并指示袭相州'),('帝','收到秘密上表'),('梁晖','受指示袭相州')],when='947年二月丁丑之前，具体日未载',place='磁州、晋阳、相州',note='李谷复用已有人物李穀；不是相同场合出现即新建盟友关系。')
add('liang_hui_reconnoiters_xiangzhou','梁晖侦知高唐英尚未到任，相州存有兵器但缺乏守备',39,'晖侦知','无守备。',[('梁晖','侦察相州守备'),('高唐英','尚未抵达相州')],when='947年二月丁丑前',place='相州',note='侦知是梁晖所得情报。无守备表示防守薄弱，后文仍有守将，不能解释为城内完全无人。')
add('liang_hui_captures_xiangzhou','梁晖派壮士夜间越城开门，攻入相州，杀契丹数百，守将突围逃走',39,'丁丑夜，','其守将突围走，',[('梁晖','派壮士开城门，率众攻入相州')],when='947年二月丁丑夜',place='相州',note='杀契丹数百是主书记数，不推具体整数；守将未名且高唐英尚未至，不能把逃走的守将写成高唐英。')
add('liang_hui_claims_liuhou_reports','梁晖据相州自称留后，上表报告取城情况',39,'晖据州',None,[('梁晖','自称相州留后并上表')],when='947年二月丁丑取城之后，具体日未载',place='相州至刘知远朝廷',note='自称留后不等于已经获正式节度使任命。')
sup('liang_hui_claims_liuhou_reports',39,j,'丁丑，磁州賊帥梁暉據相州。','《旧五代史》同记丁丑梁晖据相州。','该书称磁州贼帅，《通鉴》称滏阳贼帅，沿同一人物，不据此另建同名人。')
add('liu_returns_jinyang','刘知远返回晋阳',40,'戊寅，','帝还至晋阳，',[('帝','东行后返回晋阳')],when='947年二月戊寅',place='晋阳',note='戊寅是返回记日，与甲戌出行及途中寿阳分别记录。')
add('li_advises_against_requisition','刘知远拟征民财赏军，李夫人劝阻，建议使用宫中积蓄',40,'议率民财','人无怨言。”',[('帝','提出征民财赏军的计划'),('李氏','劝阻征民财，建议出宫中积蓄')],when='947年二月戊寅',place='晋阳',note='此处李氏为刘知远妻，与石敬瑭妻李太后不是同一人；不提前写本段已经册立皇后。百姓无怨言是她的劝说，不当逐户调查结果。')
sup('li_advises_against_requisition',40,li,'高祖建義於太原，欲行頒賚於軍士，以公帑不足，議率井邑，助成其事。','《旧五代史》补记因公帑不足而拟征民财劳军。','卷104汉高祖皇后李氏传，传主夫君为刘知远；不能误认卷86晋高祖皇后同姓者。',relation='adds')
add('liu_uses_palace_savings_for_army','刘知远接受李夫人建议，停止征民财，改用内府积蓄赏军',40,'帝曰：','中外闻之，大悦。',[('帝','停止征民财，拿出内府积蓄赏军'),('李氏','建议被采纳')],when='947年二月戊寅',place='晋阳',note='中外大悦是史家概述，不虚造民众名单或统计。未载赏钱数量，不补金额。')
sup('liu_uses_palace_savings_for_army',40,li,'遂停斂貸之議。後傾內府以助之，中外聞者，無不感悅。','《旧五代史》也记停止敛财计划，后来倾内府积蓄相助。','本段为李皇后传，底本後在上下文中也用于指皇后，此句应结合传主理解，不能机械译成后来。引用保留原字，时间以《通鉴》本段为依据。')
relationship('李氏（刘知远妻）','刘知远','妻子',40,span(40,'夫人李氏谏曰：','人无怨言。”'),'夫人李氏为刘知远妻，《旧五代史》汉高祖皇后李氏传可核其身份。妻子方向为李氏是刘知远的妻子，正式册后不是本日事件。')
claim('person',people['李氏（刘知远妻）'],'description','李氏（刘知远妻）是晋阳人。',40,span(40,'李氏，晋阳人也。'),'籍贯按段末明确记载，未补名字或现代坐标。')
add('qian_plans_night_siege_cheng','钱弘佐因程昭悦聚宾客、藏兵器等行为，命水丘昭券当夜率千名甲士围宅',41,'吴越内都监','围昭悦第。”',[('程昭悦','聚集宾客、藏兵器并与术士来往'),('弘佐','拟处死程昭悦并命夜间围宅'),('水丘昭券','收到率千名甲士围宅的命令')],when='947年二月己卯之前，具体日未载',place='吴越程昭悦宅',note='聚客藏器不自动认定已谋反；围宅是原命令，随后改用拘捕，不能写为千人夜围已实际发生。')
add('shuiqiu_opposes_night_attack','水丘昭券劝钱弘佐公开处理程昭悦，不宜夜间动兵，钱弘佐接受',41,'昭券曰：','弘佐曰：“善！”',[('水丘昭券','建议有罪公开惩处，不在夜间动兵'),('弘佐','接受改变处置方式的建议')],when='947年二月己卯之前，具体日未载',place='吴越朝廷',note='有罪当显戮是水丘昭券对处置方式的建议，不据此补出完整罪名或审判过程。')
add('chu_arrests_cheng','钱弘佐命储温等程昭悦归宅后拘捕，将他押送东府',41,'命内牙','执送东府，',[('弘佐','下令改用拘捕'),('储温','等待程昭悦归宅后拘捕并押送'),('程昭悦','被捕送东府')],when='947年二月己卯前',place='程昭悦宅至东府',note='伺为等待机会，不译作侍奉；不补东府现代位置和拘捕具体时辰。')
add('cheng_executed','钱弘佐处死程昭悦',41,'己卯，','斩之。',[('弘佐','处死程昭悦'),('程昭悦','被处死')],when='947年二月己卯',place='吴越（具体刑场未载）',note='斩之承接程昭悦，不是储温或水丘昭券；原文未载具体刑场。')
add('qian_renjun_released','钱弘佐释放被囚的钱仁俊',41,'释钱',None,[('弘佐','释放钱仁俊'),('钱仁俊','获释')],when='947年二月己卯条下，具体日未独立注明',place='吴越',note='释放本身不等于恢复原职或赔偿；此前被囚已在旧批录入。')
reviews={36:'刘知远、晋帝石重贵及晋太后身份分清；出行、途中消息与返回分记，旧史补土门路线。',37:'失去供给、锦州拜墓或遗像、责薛超及冯后求毒未遂分别记录；薛超阻止自尽属于946年，不再新建同一旧事。',38:'三项任命分记，官号依各书；授职与到任分开，高唐英尚未至相州。',39:'天威军的建立、解散及征钱为追述，未定年；打草谷复用旧事并补引。史家背景概述不自动套到每个官员；梁晖请求、侦察、取城、自称留后按次序。',40:'刘知远妻与晋太后同姓分开，魏国夫人此时未正式册后；征民财计划、劝阻、停止及内府赏军分清。旧史後结合皇后传主理解，不机械译为后来。',41:'千甲士夜围是未执行的原计划，水丘谏后改由储温拘捕；己卯斩程昭悦、释放钱仁俊不混同，不补复职。'}
assert not (P/'publication.json').exists()
for n in range(36,42):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(36,42)],next_paragraph=Q[42]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原41—46行连续六段，累计41/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(36,42)],source_issues_review='锦州拜墓与拜遗像分别保留；乡兵叙述不强定年；同姓李氏分清，昭义潞州、彰德相州任官写法分别保留。',plain_language_review='首次逐条检查全部展示字段、参与角色及事实说明；保持计划、诏令、行动与史家评价的区别，原文不改写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
