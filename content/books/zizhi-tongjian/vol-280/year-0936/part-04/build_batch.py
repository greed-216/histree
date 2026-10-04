# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 21–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,71))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'d5e5a96e' if directory.name in ['jiuwudaishi-075-936-jinyang','jiuwudaishi-099-936-liu-prisoners'] else '3c08d3ed','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))

specs += [
 ('tongjian-280-936-may-july-revolts',ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-03/sources/library/tongjian-280-936-may-july-revolts','1382703d','司马光等'),
 ('jiuwudaishi-048-936-july-revolts',ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-03/sources/library/jiuwudaishi-048-936-july-revolts','1382703d','薛居正等'),
 ('xinwudaishi-007-936-revolts',ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-03/sources/library/xinwudaishi-007-936-revolts','1382703d','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-may-july-revolts','tongjian-280-936-august-september']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p021-p028',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-099-936-liu-prisoners':'卷99·汉高祖纪（刘知远）','jiuwudaishi-075-936-jinyang':'卷75·晋高祖纪','xinwudaishi-066-xiguang-brother':'卷66·楚世家·马希广','xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/280.txt').read_text().splitlines()
for n in range(21, 29):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-099-936-liu-prisoners':'卷99·汉高祖纪（刘知远）','jiuwudaishi-075-936-jinyang':'卷75·晋高祖纪','xinwudaishi-066-xiguang-brother':'卷66·楚世家·马希广','xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '七月条下' if n<=23 else '八月条下' if n<=27 else '九月条下'
        citation = f'卷280·后唐清泰三年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'何福（石敬瑭使者）':['何福'],'张万迪':['張萬迪'],'董温琪':['董溫琪'],'丁审琦':['丁審琦'],'卢不姑':['盧不姑'],'萧辖里':['蕭轄里'],'的鲁（契丹夷离堇）':['的魯','的鲁']}
ALIASES.update({'契丹主':'耶律德光','唐王':'李从珂','杨光远':'杨檀','其母':'述律平','的鲁':'的鲁（契丹夷离堇）','何福':'何福（石敬瑭使者）'})

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=936, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='936年'+('七月' if n<=23 else '八月' if n<=27 else '九月')+'条下；确日未独载'
    key = 'event_zztj_280_0936_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_280_0936_' + code + '_' + pk
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
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_280_0936_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
add('fan_takes_weizhou','七月丁未范延光攻克魏州',21,'丁未，','拔魏州，',[('范延光','攻克将领')],when='936年七月丁未（主）',place='魏州',note='旧戊申奏称21日收复，新戊申克魏州，主丁未并列；奏日报捷不当已明确是战日。')
sup('fan_takes_weizhou',21,'jiuwudaishi-048-936-july-revolts','戊申，範延光奏，此月二十一日收復鄴都，','旧戊申奏七月21日收复邺都。','主丁未与旧报捷日及实际月日层次分，魏州邺都同府。',relation='adds',field='time_original')
sup('fan_takes_weizhou',21,'xinwudaishi-007-936-revolts','秋七月戊申，克魏州。','新末帝纪七月戊申记克魏州。','主丁未与新戊申差日，不消除。',relation='conflicts',field='time_original')
add('zhang_lingzhao_executed','张令昭兵败被斩',21,'范延光拔魏州，','斩张令昭。',[('范延光','主段攻拔、斩首将领'),('张令昭','被斩者')],when='936年七月丁未条下（主）',place='魏州条下',note='原主同日写斩，旧壬子献首、新壬子伏诛保异说；不据主推已在牙城斩。')
sup('zhang_lingzhao_executed',21,'jiuwudaishi-048-936-july-revolts','追兵遣襲張令昭部下敗兵至邢州沙河，斬首三百級，並獻張令昭、邢立、李貴等首級。','旧接壬子诛党诏后范奏追沙河败兵并献张首。','补追击地点与首级送呈，未强称献首日即斩日，邢立李贵并非主名这次事件全部执行者。',relation='adds')
sup('zhang_lingzhao_executed',21,'xinwudaishi-007-936-revolts','壬子，張令昭伏誅。','新以七月壬子记张令昭伏诛。','主同丁未叙斩、新壬子行刑纪日有别，并列原定位。',relation='conflicts',field='time_original')
add('order_execute_lingzhao_seven_units','朝廷诏悉诛张令昭党部七指挥',21,'诏悉诛',None,[],note='诏命不直接当七指挥每名兵皆已处死；单位指挥不是七个人。')
sup('order_execute_lingzhao_seven_units',21,'jiuwudaishi-048-936-july-revolts','壬子，詔範延光誅張令昭部下五指揮及忠銳、忠肅兩指揮。','旧壬子诏五指挥加忠锐忠肃两指挥，合七单位。','单位数量相合、补名与诏日，不作实际执行人数。',relation='adds')
add('zhang_wandi_deserts','张敬达发彰圣军戍虎北口，张万迪率五百骑奔河东',22,'张敬达发','将五百骑奔河东，',[('张敬达','派彰圣军戍守者'),('张万迪','指挥使、率骑转投者')],place='怀州、虎北口、河东',note='怀州是出发军驻地，虎北口拟戍；五百骑不直接算到九月唐降兵数。')
sup('zhang_wandi_deserts',22,'jiuwudaishi-048-936-july-revolts','彰聖指揮使張萬迪以部下五百騎叛入太原，詔誅家屬於懷州本營。','旧同人同五百骑叛入太原，并记本营诛家诏。','主河东旧太原军府称互补，诏处家与已执行分。')
sup('zhang_wandi_deserts',22,'xinwudaishi-007-936-revolts','癸丑，彰聖指揮使張萬迪叛降于石敬瑭。','新补七月癸丑张万迪转投纪日。','主未具转投日，丙辰为诛家诏日，不能当转投日。',relation='adds',field='time_original')
add('order_execute_wandi_family','七月丙辰诏尽诛张万迪家属',22,'丙辰，',None,[('张万迪','家属处置关联者')],when='936年七月丙辰',place='怀州本营（旧补）',note='家属未具名不造人；诏不是文本确认已经逐人执行。')
add('shi_secret_appeal_khitan','石敬瑭遣间使求契丹救援，令桑维翰草表称臣',23,'石敬瑭遣','草表称臣于契丹主，',[('石敬瑭','遣使、命草表者'),('桑维翰','草表者'),('契丹主','求援受表对象')],note='间使主未具名，辽补两次使者另按书记录，不把草表者等同这次匿名使者。')
sup('shi_secret_appeal_khitan',23,'xinwudaishi-008-936-high-emperor','敬瑭求援於契丹。','新晋高祖纪也记拒命后求援契丹。','同事件简记，不用压缩叙法另造第二次同名求援。')
add('shi_offers_father_and_land','石敬瑭表请以父礼事契丹主，约事成割卢龙一道及雁门关以北诸州',23,'且请以父礼','诸州与之。',[('石敬瑭','提出礼仪、割地承诺者'),('契丹主','拟受礼、受地者')],note='约事捷之日是条件承诺，不提前记录十六州已交；以父礼非血缘父亲关系，割地范围保原两部分。')
add('liu_zhiyuan_opposes_land_promise','刘知远谏称臣可而父礼过，金帛足致兵、不必许土田，担忧后患',23,'刘知远谏曰：','悔之无及。”',[('刘知远','劝谏者'),('石敬瑭','听谏者')],note='中国为古地域政治语境，后患是刘的预测；金帛足致援不是已付款保证有效。')
add('shi_rejects_liu_advice','石敬瑭不听刘知远关于父礼、割地的劝谏',23,'敬瑭不从。','敬瑭不从。',[('石敬瑭','未从者'),('刘知远','未被采纳的谏者')],note='不从不推刘已被处分。')
add('khitan_reacts_to_appeal','表至契丹，耶律德光大喜，告母梦石使已验为天意',23,'表至契丹，','此天意也。”',[('契丹主','述梦、喜受表者'),('其母','听告母亲')],place='契丹',note='梦与天意保当事人所述，不作客观预兆；契丹母沿述律平稳定主体。')
relationship('其母','契丹主','母亲',23,'契丹主大喜，白其母曰：','现契丹主沿耶律德光，母沿既有述律平；复用原母子边而非新祖辈。')
add('khitan_promises_midautumn','耶律德光复书许仲秋倾国赴援',23,'乃为复书，',None,[('契丹主','许援者'),('石敬瑭','承诺受援者')],note='许是回复计划，倾国是主修辞不等已所有人口军队南下；仲秋与实际八月出发九月抵达分。')
# Independent Liao account adds missions and exact calendar, without overwriting the main account.
event('liao_zhao_ying_appeals','辽太宗纪补七月丙申赵莹经卢不姑向契丹求救',23,'丙申，唐河東節度使石敬瑭為其主所討，遣趙瑩因西南路招討盧不姑求救，',[('石敬瑭','遣使者'),('赵莹','求援使者'),('卢不姑','西南路招讨、转达路径人物')],source='liaoshi-003-936-july-appeals',when='辽天显十一年（936）七月丙申',place='河东、契丹',note='辽独补使者与路径，主间使未名，不能认定主每次间使必赵。')
event('liao_emperor_consults_dowager','辽记太宗告太后称应讨李从珂',23,'上白太后曰：「李從珂弒君自立，神人共怒，宜行天討。」',[('契丹主','告太后者'),('其母','受告者')],source='liaoshi-003-936-july-appeals',when='辽天显十一年（936）七月求援条下',note='弑君自立神人共怒是德光的出兵理由表述，非本站统一认定；与主梦说各保。')
event('liao_sang_urgent_appeal','辽记赵德钧亦遣使，河东再遣桑维翰告急，契丹许兴师',23,'時趙德鈞亦遣使至，河東復遣桑維翰來告急，遂許興師。',[('赵德钧','另遣使者'),('桑维翰','河东再告急使者'),('契丹主','许兴师者')],source='liaoshi-003-936-july-appeals',when='辽天显十一年（936）七月求援条下；先后独立日未载',note='主桑草表与辽桑出使为不同动作；赵使所求此句未具，不推其已请帝位。')
event('liao_xiao_reports_schedule','辽补八月己未遣萧辖里报河东师期',23,'八月己未，遣蕭轄里報河東師期。',[('契丹主','遣使者'),('萧辖里','报师期使者')],source='liaoshi-003-936-august-departure',when='辽天显十一年（936）八月己未',note='补许援后的报期行动，不把萧当主书前一次间使。')
add('fan_yanguang_tianxiong','八月己未范延光任天雄节度使',24,'八月，己未，','为天雄节度使，',[('范延光','获任者')],when='936年八月己未',place='天雄军',note='与六月四面招讨使为不同官命。')
sup('fan_yanguang_tianxiong',24,'jiuwudaishi-048-936-august','己未，以汴州節度使範延光為天雄軍節度使、守太傅、兼中書令；','旧同日补守太傅、兼中书令。','汴州前镇为宣武军，不是天雄同城。',relation='adds')
add('li_zhou_xuanwu','八月己未李周任宣武节度使、同平章事',24,'李周为',None,[('李周','获任者')],when='936年八月己未条下',place='宣武军',note='与六月魏博副招讨、西京留守前衔分，不推仍亲留洛阳守府。')
sup('li_zhou_xuanwu',24,'jiuwudaishi-048-936-august','以西京留守李周為汴州節度使、檢校太尉、同平章事。','旧同日补检校太尉、汴州称。','宣武军汴州同府，同命补衔。',relation='adds')
add('yingzhou_reports_attack','八月癸亥应州报契丹三千骑攻城',25,'癸亥，','攻城。',[],when='936年八月癸亥奏报',place='应州',note='报攻城不是已攻克，也不自动把此三千与九月诱敌三千相同部队。')
sup('yingzhou_reports_attack',25,'jiuwudaishi-048-936-august','癸亥，應州奏，契丹三千騎迫城。','旧同日报三千骑迫应州。','主攻城与旧迫城表述各保，非已破城。')
add('jingda_builds_siege','张敬达筑长围攻晋阳',25,'张敬达筑','以攻晋阳。',[('张敬达','围攻者')],place='晋阳',note='建设目的与后未合围、攻城未下分，不推已完全封锁城。')
add('shi_appoints_liu_command','石敬瑭任刘知远为马步都指挥使，安重荣、张万迪降兵归其统辖',25,'石敬瑭以','皆隶焉。',[('石敬瑭','任命者'),('刘知远','统辖受命者'),('安重荣','所属降兵原将领'),('张万迪','所属降兵原将领')],place='晋阳',note='降兵部属归刘，本人是否同列军阶不外推；全集团不造泛统属人物关系。')
add('liu_impartial_military_rule','主书称刘知远用法无私、抚兵如一，众无贰心',25,'知远用法无私，','人无贰心。',[('刘知远','被史书评价者')],year=None,when='收降兵后军中治理概述；各次与起年未具',place='晋阳',note='史书整体评价，未添刑例、人数或证据外实际民意。')
add('shi_on_wall_under_fire','石敬瑭亲上城，坐卧矢石之下',25,'敬瑭亲乘城，','坐卧矢石下，',[('石敬瑭','亲守城者')],place='晋阳',note='未记已负伤或具体天数。')
add('liu_proposes_defense_division','刘知远称敬达无奇策，请石经略外事、自己担守城',25,'知远曰：','知远独能办之。”',[('刘知远','提出守城分工者'),('石敬瑭','受建议者')],place='晋阳',note='不足虑守城至易是刘的判断与自许，不当客观低风险或守城已成功。')
add('shi_praises_liu','石敬瑭执刘知远手、抚背而赏',25,'敬瑭执知远手，',None,[('石敬瑭','抚背赏者'),('刘知远','获赏者')],place='晋阳',note='未明赏物或升官，不添金额。')
add('dong_wenqi_deputy','八月戊寅董温琪任东北面副招讨使，辅佐赵德钧',26,'戊寅，',None,[('董温琪','成德节度使、获副招讨命者'),('赵德钧','被辅佐的卢龙节度使')],when='936年八月戊寅',place='东北面',note='董温琪非华温琪；以佐不是亲属结盟边。')
sup('dong_wenqi_deputy',26,'jiuwudaishi-048-936-august','戊寅，以鎮州節度使董溫琪充東北面副招討使。','旧同日同命，前镇称镇州。','成德军镇州同府，身份无同名异人的迹象。')
add('lv_qi_rewards_camp','李从珂遣吕琦赴河东行营犒军',27,'唐主使','至河东行营犒军，',[('唐主','遣使者'),('吕琦','端明学士、犒军使者')],place='河东行营',note='吕此前御史后复端明主此称，旧七月官命已归旧记录；此次依当前衔，不重造三月御史或未知复任日。')
sup('lv_qi_rewards_camp',27,'jiuwudaishi-048-936-august','詔端明殿學士呂琦往河東忻、代諸屯戍所犒軍。','旧癸亥应州报后记诏吕赴忻代屯戍犒军。','主河东行营与旧具体忻代互补，诏命不硬定到达日。',relation='adds')
add('yang_guangyuan_predicts_victory','杨光远向吕琦请转奏无援可平、有契丹援可纵入一战破',27,'杨光远谓琦曰：','帝甚悦。',[('杨光远','托奏、预测者'),('吕琦','转奏使者'),('帝','闻而悦者')],note='两条件作军事预测，后败与此并列，不把一战破当战果。')
add('congke_urges_attack_jinyang','李从珂闻契丹许仲秋赴援，屡催张敬达急攻，晋阳未下',27,'帝闻契丹许','不能下。',[('帝','催攻者'),('张敬达','被催、未攻下者')],place='晋阳',note='屡督没有逐次确日，不臆造次数。')
add('siege_weather_damage','围城营构屡遇风雨，长围夏被水潦坏，未能合围',27,'每有营构，','竟不能合，',[('张敬达','长围工程相关主将')],when='936年围城期间及夏季水潦；逐次日期未载',place='晋阳城外',note='夏为水潦所坏追前季节，不作八月唯一一次大水已证；保工程未合。')
add('jinyang_food_shortage','晋阳城中渐困，粮储渐乏',27,'晋阳城中',None,[],place='晋阳',note='日窘浸乏是持续趋势，未给粮剩天数、兵民饥亡数。')
add('khitan_marches_south','九月耶律德光率五万骑、号三十万，扬武谷南下，旗延五十余里',28,'九月，','五十馀里。',[('契丹主','南下主帅')],place='扬武谷',note='五万为主记实数，三十万为号称；旗延距离不当军力三十万已核。')
event('liao_emperor_starts_relief','辽补太宗八月庚午亲率军援石敬瑭',28,'庚午，自將以援敬瑭。',[('契丹主','亲率赴援者')],source='liaoshi-003-936-august-departure',when='辽天显十一年（936）八月庚午',note='主九月南下所见与辽八月出师可能阶段不同，分记录不覆盖主日期。')
add('zhang_ding_hold_cities','张朗、丁审琦婴城守代、忻二州，契丹过城未诱胁',28,'代州刺史张朗、','审琦，洺州人也。',[('张朗','守代州刺史'),('丁审琦','守忻州刺史')],place='代州、忻州',note='丁洺州为籍贯；过城不攻或未诱胁非二人降契丹，也不替朝廷侦察实情。')
add('khitan_arrives_hubeikou','九月辛丑耶律德光至晋阳，阵于汾北虎北口',28,'辛丑，','虎北口。',[('契丹主','到达布阵者')],when='936年九月辛丑（主）',place='汾北、虎北口',note='辽记己亥次太原、庚子交战，主辛丑到达战日不同保。')
sup('khitan_arrives_hubeikou',28,'liaoshi-003-936-september-battle','丁酉，入雁門。戊戌，次忻州，祀天地。己亥，次太原。','辽记丁酉雁门、戊戌忻州、己亥太原途程。','补路线与辽日次，主扬武谷及辛丑布阵不改为一致。',relation='adds',field='time_original')
add('khitan_proposes_immediate_battle','耶律德光遣使问石敬瑭可否当天破唐军',28,'先遣人谓','即破贼可乎？”',[('契丹主','询战者'),('石敬瑭','被问者')],when='936年九月辛丑布阵后（主）',note='问可乎是拟战，主贼指南军沿发言立场，显示用唐军。')
add('shi_requests_delay_battle','石敬瑭派人疾告南军厚，建议次日再议战',28,'敬瑭遣人驰告曰：','未晚也。”',[('石敬瑭','请求暂缓者'),('契丹主','驰告对象')],when='936年九月辛丑（主）',note='建议翌日未获实际执行，明日不是已经发生另一战。')
add('khitan_engages_tang_cavalry','石使未至，契丹已与高行周、符彦卿交战，石遣刘知远出助',28,'使者未至，','出兵助之。',[('契丹主','契丹主帅'),('高行周','唐骑将'),('符彦卿','唐骑将'),('石敬瑭','遣援者'),('刘知远','出兵助者')],when='936年九月辛丑（主）',place='晋阳',note='符彦卿≠后屯河阳符彦饶，两个既有兄弟身份不混。')
sup('khitan_engages_tang_cavalry',28,'jiuwudaishi-048-936-september','高行周、符彥卿率左右廂騎軍出鬥，蕃軍引退。','旧同两骑将先出战。','旧九月甲辰报本月15日战，报日与战日分；不在此换算15日干支。')
sup('khitan_engages_tang_cavalry',28,'liaoshi-003-936-september-battle','庚子，遣使諭敬瑭曰：「朕興師遠來，當即與卿破賊。」會唐將高行周、符彥卿以兵來拒，遂勒兵陳于太原。','辽庚子记欲即破敌与同两将拒战。','主辛丑与辽庚子纪日并列，不能只写两书同日。',relation='conflicts',field='time_original')
add('tang_infantry_arrays','张敬达、杨光远、安审琦以步兵阵于晋阳城西北山下',28,'张敬达、杨光远、','以步兵陈于城西北山下，',[('张敬达','列阵主将'),('杨光远','列阵将领'),('安审琦','列阵将领')],when='936年九月辛丑战中（主）',place='晋阳城西北山下',note='步兵陈而不概括全部唐骑将也在此列。')
add('khitan_light_cavalry_feint','契丹以不披甲轻骑三千冲阵，唐追至汾曲，轻骑涉水而去',28,'契丹遣轻骑三千，','契丹涉水而去。',[],when='936年九月辛丑战中（主）',place='汾曲',note='主赢疑羸示弱原保；三千为此诱敌队，不当全军五万皆无甲或此处死三千。')
add('khitan_ambush_splits_tang','唐沿岸进，契丹东北伏兵冲断唐军，北步兵多被杀、南骑兵归寨',28,'唐兵循岸而进，','骑兵在南者引归晋陷寨。',[],when='936年九月辛丑战中（主）',place='汾水岸',note='主涉兵疑步兵、北都多及晋陷寨疑晋安原保，理解步骑分部有后文支撑；不据疑字造晋陷新寨。')
add('tang_defeat_nearly_ten_thousand','契丹乘势进击，唐大败，主记步兵死近万、骑兵全',28,'契丹纵兵乘之，','骑兵独全。',[],when='936年九月辛丑战中（主）',place='晋阳',note='骑兵独全是主整叙，未当每名骑卒均无伤亡；近万保约数。')
sup('tang_defeat_nearly_ten_thousand',28,'liaoshi-003-936-september-battle','敬達、光遠大敗，棄仗如山，斬首數萬級。','辽记斩首数万级、弃仗如山。','与主步兵死近万数字不同，保来源语境及约数，不用较大者作统一伤亡。',relation='conflicts')
sup('tang_defeat_nearly_ten_thousand',28,'jiuwudaishi-048-936-september','王師大敗，投兵仗相藉而死者山積。','旧记王师大败、弃仗与相藉死亡。','旧无可取确数，不把山积折成特定人数。')
add('jingda_retreats_jinan','张敬达等收余军保晋安，契丹收兵回虎北口',28,'敬达等收馀众','归虎北口。',[('张敬达','收余军入寨者'),('契丹主','引兵收回一方主帅')],when='936年九月辛丑战后（主）',place='晋安寨、虎北口',note='保寨不是本人死于此役；此前晋陷疑字沿晋安。')
sup('jingda_retreats_jinan',28,'jiuwudaishi-048-936-september','是夕，收合餘眾，保於晉祠南晉安寨，蕃軍塹而圍之，自是音聞阻絕。','旧补晋祠南晋安寨、当夕围断声闻。','主壬寅围寨与旧夕记阶段不同，不默默统一日期。',relation='adds')
add('liu_urges_kill_tang_surrendered','石敬瑭得唐降兵千余，刘知远劝尽杀',28,'敬瑭得唐降兵','尽杀之。',[('石敬瑭','受降者'),('刘知远','劝杀者')],when='936年九月辛丑战后（主）',note='劝杀尚未记主从谏执行，不记录千余均被杀或确数字。')
add('shi_meets_khitan_emperor','当夕石敬瑭出北门见耶律德光，契丹主执手称相见晚',28,'是夕，','恨相见之晚。',[('石敬瑭','出见者'),('契丹主','接见执手者')],when='936年九月辛丑夕（主）',place='晋阳北门外',note='执手与晚叹不自动建结义兄弟、亲父子边。')
sup('shi_meets_khitan_emperor',28,'xinwudaishi-008-936-high-emperor','敬瑭夜出北門見耶律德光，約為父子。','新晋高祖纪补当夜会面约父子。','约为父子是政治约定，独立补此事件，不称血亲。',relation='adds')
sup('shi_meets_khitan_emperor',28,'liaoshi-003-936-september-battle','敬瑭率官屬來見，上執手撫慰之。','辽补率官属来见与执手抚慰。','无具名官属不猜桑刘都赴营。',relation='adds')
add('shi_asks_victory_reason','石敬瑭问契丹主远来人马疲而速胜的原因',28,'敬瑭问曰：','何也？”',[('石敬瑭','询问者'),('契丹主','被问者')],when='936年九月辛丑夕（主）',note='疲倦为石询问情境，不添医诊或疲劳比例。')
add('khitan_explains_rapid_victory','耶律德光称唐未堵雁门设伏，己军气锐故乘势急战获胜',28,'契丹主曰：','敬瑭甚叹伏。',[('契丹主','说明战胜原因者'),('石敬瑭','闻而叹服者')],when='936年九月辛丑夕（主）',note='侦无阻、气锐气沮、长驱必济及劳逸解释均当事人口述，不统一认作后人因果定论。')
add('shi_khitan_besiege_jinan','九月壬寅石敬瑭会契丹围晋安寨，南营长百余里、厚五十里，设铃索吠犬',28,'壬寅，','人跬步不能过。',[('石敬瑭','引兵合围者'),('契丹主','契丹合围主帅')],when='936年九月壬寅（主）',place='晋安寨南',note='长度厚度按史载范围不做精确GIS；铃索吠犬防行描写不当现代传感器。')
sup('shi_khitan_besiege_jinan',28,'liaoshi-003-936-september-battle','癸卯，圍晉安。','辽九月癸卯围晋安。','主壬寅辽癸卯差日，围困形成可能阶段不同，保各书。',relation='conflicts',field='time_original')
add('jingda_trapped_strength','主记晋安寨内张敬达等尚有士卒五万、马万匹，无处突围',28,'敬达等士卒','四顾无所之。',[('张敬达','被困主将')],when='936年九月壬寅围寨后（主）',place='晋安寨',note='记此阶段存量，不用来倒算此前近万死亡而得唯一初始兵数。')
add('jingda_reports_defeat_isolation','九月甲辰张敬达遣使告败，随后声问不通',28,'甲辰，','自是声问不复通。',[('张敬达','告败、被隔绝者')],when='936年九月甲辰奏败',place='晋安寨',note='告败日非战日；不能把声问不通当此前从未有通信。')
sup('jingda_reports_defeat_isolation',28,'jiuwudaishi-048-936-september','九月甲辰，張敬達奏，此月十五日，與契丹戰於太原城下，王師敗績。','旧同甲辰奏报并记实战十五日。','奏败甲辰同，战日另记15日，未自行换算干支。',relation='adds',field='time_original')
add('fu_yanrao_troops_heyang','李从珂惧，派符彦饶率洛阳步骑驻河阳',28,'唐王大惧，','屯河阳，',[('唐王','遣兵者'),('符彦饶','率兵屯驻者')],when='936年九月甲辰告败后（主）',place='洛阳、河阳',note='主彰圣都指挥使、旧侍卫步军都指挥使职表不同，不混骑将符彦卿。')
sup('fu_yanrao_troops_heyang',28,'jiuwudaishi-048-936-september','是日，遣侍衛步軍都指揮使符彥饒率兵屯河陽，','旧甲辰遣符职称侍卫步军都指挥使。','主彰圣衔与旧侍卫衔分别，不造两个符彦饶。',relation='adds')
add('fan_orders_rescue_route','诏范延光率魏州二万由青山赴榆次救晋安',28,'诏天雄节度使','由青山趣榆次，',[('范延光','受救援命者')],when='936年九月甲辰告败后（主）',place='魏州、青山、榆次',note='诏令不是已到榆次；二万为此受命兵数。')
add('zhao_dejun_orders_rear_route','诏赵德钧率幽州军由悄孤出契丹军后救晋安',28,'卢龙节度使、','出契丹军后，',[('赵德钧','受救援命者')],when='936年九月甲辰告败后（主）',place='幽州、悄孤（疑地名）',note='主悄孤疑飞狐底本保，旧明飞狐供校读，不造悄孤坐标。')
sup('zhao_dejun_orders_rear_route',28,'jiuwudaishi-048-936-september','詔幽州趙德鈞由飛狐路出敵軍後，','旧救援路径写飞狐路。','主悄孤旧飞狐原字异并列，身份同受令将，地名暂未知坐标。',relation='adds')
add('pan_huan_orders_west_route','诏潘环会西路戍兵，经晋绛两乳岭至慈隰救晋安',28,'耀州防御使潘环','共救晋安寨。',[('潘环','受会军救援命者')],when='936年九月甲辰告败后（主）',place='晋州、绛州、两乳岭、慈州、隰州',note='主耀州旧辉州职地异不私改；糺合保原字，引路线而未说已经出岭。')
sup('pan_huan_orders_west_route',28,'jiuwudaishi-048-936-september','輝州防禦使潘環合防戍軍出慈、隰以援張敬達。','旧潘职地记辉州，同救张路线慈隰。','主耀州旧辉州异地文字保，不能凭此改其既有主体身份。',relation='conflicts')
add('khitan_moves_liulin','契丹主移帐柳林，游骑过石会关未见唐军',28,'契丹主移帐',None,[('契丹主','移帐者')],when='936年九月围晋安后（主）',place='柳林、石会关',note='游骑此处未见唐兵不是整个唐朝无兵；未明游骑将不造。')
sup('khitan_moves_liulin',28,'jiuwudaishi-048-936-september','契丹主移帳於柳林。','旧也记移帐柳林。','同阶段记录，不当今日柳林县坐标已核。')
event('liao_delu_dies_jinan','辽补夷离堇的鲁与晋安寨军交战而死',28,'敬達走保晉安寨，夷離菫的魯與戰，死之。',[('的鲁','战死将领')],source='liaoshi-003-936-september-battle',when='辽天显十一年（936）九月晋安战中；独立日未具',place='晋安寨',note='补同役辽方有名死者，不猜其姓、不合过去同音名；上句庚子交战与后癸卯围寨之间无独立死日。')
row=next(x for x in B['people'] if x['name']=='的鲁（契丹夷离堇）');row['death_year']=936
claim('person',row['key'],'death_year','的鲁于936年晋安寨交战中身亡。',28,'夷離菫的魯與戰，死之。','确年承已核辽天显11年界，独立死日未载。',source='liaoshi-003-936-september-battle')
# Published person gets an auditable aliases/field revision rather than changing an old batch.
claim('person',people['张令昭'],'death_year','张令昭于936年兵败遭斩。',21,'丁未，范延光拔魏州，斩张令昭。','前批人物已公开，卒年依本段及新旧记并列另作定向字段修订；不改旧档案。')
sup('liu_urges_kill_tang_surrendered',28,'jiuwudaishi-099-936-liu-prisoners','有降軍千餘人，晉高祖將置之於親衛，帝盡殺之。','旧汉高祖纪记晋高祖拟把降军千余置亲卫，刘知远尽杀。','帝指汉高祖刘知远，回查本纪首本名知远；主只记劝杀，旧补实际执行，不让主未载结果变成否认执行。',relation='adds')
event('jiuwu_liu_executes_prisoners','旧汉高祖纪记石敬瑭欲用千余降兵为亲卫，刘知远尽杀之',28,'有降軍千餘人，晉高祖將置之於親衛，帝盡殺之。',[('石敬瑭','拟置降军为亲卫者'),('刘知远','杀降军者')],source='jiuwudaishi-099-936-liu-prisoners',when='936年九月晋阳战后；旧无独立行刑日',place='晋阳',note='只据旧正文记实际执行，与主刘劝杀分层；未名降兵不造人，千余为约数。')
sup('shi_appoints_liu_command',25,'jiuwudaishi-099-936-liu-prisoners','晉高祖以帝為北京馬步軍都指揮使。','旧汉高祖纪也记刘任北京马步军都指挥使。','帝刘知远以本纪首核，北京太原不当现代北京，旧压缩无独立八月日。')
sup('khitan_arrives_hubeikou',28,'jiuwudaishi-075-936-jinyang','九月辛丑，契丹主率眾自雁門而南，旌騎不絕五十里餘。','旧晋高祖纪正文九月辛丑率众雁门南下、旌骑五十余里。','与主辛丑战日同序，辽己亥太原庚子战另记；本段夹注引辽不当独立第二次印证。',relation='adds',field='time_original')
sup('tang_defeat_nearly_ten_thousand',28,'jiuwudaishi-075-936-jinyang','敬達等步兵大敗，死者萬人。','旧晋高祖纪记步兵死万人。','主近万、旧万人数字表述相近保原约数，不统一成精确10000。')
sup('shi_meets_khitan_emperor',28,'jiuwudaishi-075-936-jinyang','是夜，帝出北門與戎王相見，契丹主執帝手曰：「恨會面之晚。」因論父子之義。','旧晋高祖纪也记夜出北门执手并论父子之义。','正文可用，随后夹注辽与契丹国志依赖不算独立补证；政治称父子不当血缘边。',relation='adds')
event('jiuwu_he_fu_appeal','旧晋高祖纪补石敬瑭受末帝逼迫后遣何福携刀错为信求契丹援',23,'帝與契丹本無結好，自末帝見迫之後，遣心腹何福，以刀錯為信，',[('石敬瑭','遣心腹求援者'),('何福','持信求援使者')],source='jiuwudaishi-075-936-jinyang',when='936年受迫之后、契丹赴援之前；旧追叙未具独立日',note='旧另具何福与刀错信物，主匿名间使、辽赵莹桑多次分记录，不能全合成同一使者；刀错原名物不擅解释材质。')
reviews={21:'主丁未拔魏斩令昭、旧戊申奏月21克城新戊申克壬子斩并列，七指挥为军事单位诏不是七人执行。',22:'张万迪五百骑转投与丙辰诛家诏分；新癸丑转投，未名家属不造，命令不当执行完。',23:'称臣父礼割地为约事成条款，不当已割16州或血亲。刘的预测、石不从、主梦天意归各人；辽赵莹经卢求救、赵德钧使、桑告急及萧报期独立补，同书不能断主每次使皆谁。',24:'范天雄、李宣武两命同己未，军名府名及旧官衔补，未当都已到任。',25:'应州报三千攻城非已克，与九月轻骑三千不合队。筑围、刘任军、常态评价、石亲守、刘自许、石赏分；降军不生泛统属人际关系。',26:'董温琪非华温琪，成德镇州同军府，佐赵官职非结盟。',27:'吕复端明旧7月任命另在旧已公开出处，不重造3月御史。杨条件预测与帝悦、屡催未克、夏潦坏围、日窘浸乏全收，时间季节和话语层次保。',28:'五万骑与号三十万分，主辛丑辽庚子战、旧十五日甲辰奏分。轻骑诱敌、伏击、步骑分退、近万/辽数万、营寨存量与获降不倒算。主刘劝杀、旧汉纪补实际尽杀独立存证，夜见父子新为政治约。主壬寅辽癸卯围，的鲁死日未知。符卿饶分，悄孤飞狐、耀辉、赢涉晋陷疑字原保，三路救援是诏非已成。'}
ctx=P/'sources/context/liaoshi-003-year-eleven/source.txt'
contexts=[dict(file=os.path.relpath(ctx,P/'sources'),sha256=hashlib.sha256(ctx.read_bytes()).hexdigest(),paragraph_id='liaoshi-7cd182a20e67-p000429',purpose='核辽太宗纪天显十一年年界，仅结构项不生成历史事实',url='https://github.com/greed-216/histree/blob/3c08d3ed/'+str(ctx.relative_to(ROOT)))]
ctx2=P/'sources/context/jiuwudaishi-099-liu-heading/source.txt'
contexts.append(dict(file=os.path.relpath(ctx2,P/'sources'),sha256=hashlib.sha256(ctx2.read_bytes()).hexdigest(),paragraph_id='jiu-wudaishi-205deb4a7860-p002421',purpose='核旧卷99本纪首：姓刘、讳暠、本名知远，支持原段帝的主体识别；不扩录族谱',url='https://github.com/greed-216/histree/blob/0fdade40/'+str(ctx2.relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,29):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(21,29)],next_paragraph=Q[29]['id'],next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第21—28段原26—33行：魏州平乱、张万迪、石求契丹援、唐任官、围城、九月会战及晋安围困。后42段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,29)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
