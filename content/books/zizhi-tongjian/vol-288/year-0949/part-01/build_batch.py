# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 1–11."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
COMMIT='74625032a86ac7faa4033ef6a6ab3a883887537c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-107-shi-punishments']:
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
main_sources = ['tongjian-288-949-january-may']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0949-p001-p011',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-288-949-january-may':'卷288·乾祐二年·正月至五月','jiuwudaishi-102-january-949':'卷102·隐帝本纪·乾祐二年正月','jiuwudaishi-102-february-949':'卷102·隐帝本纪·乾祐二年二月','jiuwudaishi-102-may-949':'卷102·隐帝本纪·乾祐二年五月','jiuwudaishi-110-guo-hezhong-949':'卷110·周太祖纪·河中之役','jiuwudaishi-107-shi-dechong':'卷107·史弘肇传附史德充','xinwudaishi-017-jin-jianzhou-949':'卷17·晋家人传·出帝迁建州','xinwudaishi-017-an-taifei':'卷17·晋家人传·安太妃','xinwudaishi-017-li-empress-identity':'卷17·晋家人传·高祖李皇后','liaoshi-006-jing-shulu-identity':'卷6·穆宗纪·姓名亲支','songshi-271-li-tao-hezhong':'卷271·李韬传·河中交战','songshi-274-wang-jixun-hezhong':'卷274·王继勋传·河中交战'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
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
    for a,b in [('主書','《资治通鉴》'),('補','补'),('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-288-949-january-may':'卷288·乾祐二年·正月至五月','jiuwudaishi-102-january-949':'卷102·隐帝本纪·乾祐二年正月','jiuwudaishi-102-february-949':'卷102·隐帝本纪·乾祐二年二月','jiuwudaishi-102-may-949':'卷102·隐帝本纪·乾祐二年五月','jiuwudaishi-110-guo-hezhong-949':'卷110·周太祖纪·河中之役','jiuwudaishi-107-shi-dechong':'卷107·史弘肇传附史德充','xinwudaishi-017-jin-jianzhou-949':'卷17·晋家人传·出帝迁建州','xinwudaishi-017-an-taifei':'卷17·晋家人传·安太妃','xinwudaishi-017-li-empress-identity':'卷17·晋家人传·高祖李皇后','liaoshi-006-jing-shulu-identity':'卷6·穆宗纪·姓名亲支','songshi-271-li-tao-hezhong':'卷271·李韬传·河中交战','songshi-274-wang-jixun-hezhong':'卷274·王继勋传·河中交战'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐元年（949年正月至五月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0949_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=949, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='949年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0949_' + code
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
        edge = 'participation_zztj_288_0949_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0949_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘承祐','唐主':'李璟','蜀主':'孟昶','晋主':'石重贵','晋李太后':'永宁公主（石敬瑭妻）','李太后':'永宁公主（石敬瑭妻）','安太妃':'安氏（石重贵母）','契丹主':'耶律阮','述律王':'耶律璟','王继勋':'王继勋（李守贞将）','赵氏':'赵氏（石重贵宠姬）','聂氏':'聂氏（石重贵宠姬）'})
NEW_ALIASES={'阎晋卿':['閻晉卿'],'李韬':['李韜'],'李审':['李審'],'吴虔裕':['吳虔裕'],'咸师朗':['咸師朗'],'成德钦':['成德欽'],'耶律璟':['耶律述律','述律王','寿安王','壽安王'],'赵氏（石重贵宠姬）':['趙氏（石重貴寵姬）'],'聂氏（石重贵宠姬）':['聶氏（石重貴寵姬）'],'史德珫':['史德充'],'徐进':['徐進'],'魏延朗':[],'郑宾':['鄭賓']}
NEW_DESCRIPTIONS={
 '阎晋卿':'忻州人，后汉客省使。949年正月河中军夜袭后汉营寨时，提醒将士可以凭黄纸甲在火光下辨认敌军。生卒年尚未录入。',
 '李韬':'后汉裨将。949年正月河中军夜袭营寨时，持槊率先迎战，众人跟随。《宋史》记河朔人、善用槊，所记交战过程也有更详细的内容。生卒年尚未录入。',
 '李审':'郭威的亲近将领。郭威禁止军中私下饮酒后，李审因早晨饮少量酒违反军令，被处死示众。949年条下记载此事，具体日未载。其他经历尚未确认。',
 '吴虔裕':'后汉河中行营都监。949年四月奉郭威之命，率兵从侧面攻击李守贞出城部队，击败对方并夺取攻城器具。生卒年尚未确定。',
 '咸师朗':'蒙城镇将。949年南唐派皇甫晖到海州、泗州招纳淮北势力时，向皇甫晖投降。生卒年与其他经历未载。',
 '成德钦':'后汉徐州将领。949年二月击败南唐军，《旧五代史》称徐州巡检使，并载其奏报；战果人数和战场地名的字形与《通鉴》略有不同，分别保留。生卒年未载。',
 '耶律璟':'耶律德光的长子，小字述律，封寿安王。《资治通鉴》949年条称述律王，记他派骑兵带走石重贵的宠姬赵氏、聂氏；《辽史》穆宗纪可核对姓名和亲支。949年时仍以述律王身份见于记载。',
 '赵氏（石重贵宠姬）':'石重贵的宠姬，个人名字与生卒年未载。949年石重贵迁到建州后不久，被述律王耶律璟派骑兵带走。没有据此认定她与耶律璟建立婚姻关系。',
 '聂氏（石重贵宠姬）':'石重贵的宠姬，个人名字与生卒年未载。949年石重贵迁到建州后不久，与赵氏一起被述律王耶律璟派骑兵带走。没有据此认定她与耶律璟建立婚姻关系。',
 '史德珫':'史弘肇的儿子，归德牙内指挥使。949年三月己未领忠州刺史。史书记他读过一些书，常不赞同父亲的做法，并劝父亲释放被送到侍卫司的举人。《旧五代史》写史德充，按父子身份、官职和同一事件对应识别。生卒年未载。',
 '徐进':'楚国将领。949年《通鉴》三月条记他在风阳山击败南方部族武装，《旧五代史》五月条记湖南奏报，称他为大将军并记援贺州。生卒年及族属未载。',
 '魏延朗':'李守贞的部将。949年五月李守贞再次出兵失败时，与郑宾一起被后汉军擒获。生卒年及被俘后的处置尚未确定。',
 '郑宾':'李守贞的部将。949年五月李守贞再次出兵失败时，与魏延朗一起被后汉军擒获。生卒年及被俘后的处置尚未确定。'}
NEW_DEATH_YEARS={'李审':949}
jan='jiuwudaishi-102-january-949';guo='jiuwudaishi-110-guo-hezhong-949';feb='jiuwudaishi-102-february-949';may='jiuwudaishi-102-may-949';dechong='jiuwudaishi-107-shi-dechong';jian='xinwudaishi-017-jin-jianzhou-949';an='xinwudaishi-017-an-taifei';li='xinwudaishi-017-li-empress-identity';jing='liaoshi-006-jing-shulu-identity';litao='songshi-271-li-tao-hezhong';wang='songshi-274-wang-jixun-hezhong';punish='jiuwudaishi-107-shi-punishments'
add('han_new_year_amnesty','后汉在正月初一大赦',1,'春，',None,[('刘承祐','在位朝廷于正月初一大赦')],when='949年正月乙巳朔',place='后汉境内',note='朔为月初一，不自行换算公历日期；原文未列赦免例外或对象数量。')
add('bai_wenke_greets_guo_at_hezhong','郭威即将返回河中，白文珂出迎',2,'郭威',None,[('郭威','即将到河中'),('白文珂','出迎郭威')],when='949年正月郭威返回河中前，具体日未载',place='河中附近',note='与上一年郭威到华州后返回的行程衔接；将至不是已抵达。')
add('wang_jixun_night_raid_han_camp','王继勋率千余精兵夜袭后汉营寨，入寨纵火',3,'戊申夜，','军中狼狈不知所为。',[('李守贞','派王继勋等夜袭后汉营寨'),('王继勋','率千余精兵沿河南下，挖岸登寨后纵火')],when='949年正月戊申夜',place='河中城外后汉营寨',note='主书叙戊申夜，旧隐帝本纪记正月四日夜、周太祖纪记五日夜，分别保留，不静默统一；入寨不等于最终突破整个围城。')
sup('wang_jixun_night_raid_han_camp',3,jan,'賊城內偵知郭威西行，於正月四日夜，遣賊將王三鐵等，','《旧五代史》隐帝本纪记夜袭在正月四日夜，王三铁领兵。','王三铁按该段宋史注与王继勋对应；主书保留戊申夜，不由本纪把袭寨写成此前已经攻克后汉全营。',relation='adds',field='time_original')
sup('wang_jixun_night_raid_han_camp',3,guo,'二年正月五日夜，李守貞遣將王三鐵領千餘人，夜突河西呰，果為劉詞等力戰敗之。','《旧五代史》周太祖纪记此役在正月五日夜，王三铁领千余人袭河西寨，被刘词等击败。','同书隐帝本纪记四日夜，周太祖纪记五日夜，日期不一致；以各篇具体定位保留差异，不据此新建第二次夜袭。',relation='conflicts',field='time_original')
claim('person',people['王继勋（李守贞将）'],'aliases','王继勋在军中被称为王三铁。',3,'繼勛有武勇，在軍陣常用鐵鞭、鐵槊、鐵楇，軍中目為「王三鐵」。','引自《旧五代史》本纪所附《宋史》注；对应河中将领王继勋，不并入闽国或其他宋代同名人，注引不当同书独立确证。',source=jan)
add('liu_ci_counterattacks_raid','刘词在营寨遭袭时镇定下令，率军反击',3,'刘词神色自若，','帅众击之。',[('刘词','镇定下令，亲率将士反击来袭军队')],when='949年正月戊申夜',place='河中城外后汉营寨',note='小盗为刘词安定军心的说法，不用作本站对来袭者的身份名称。')
add('yan_jinqing_identifies_paper_armor','阎晋卿提醒将士，可用火光辨认来袭军队的黄纸甲',3,'客省使阎晋卿曰：','奈众无斗志何！”',[('阎晋卿','指出对方黄纸甲在火光下易辨，担忧己方士气')],when='949年正月戊申夜',place='河中城外后汉营寨',note='可辨甲色是阎晋卿的战场判断，不补甲胄厚度或真实防护性能。')
claim('person',people['阎晋卿'],'description','阎晋卿是忻州人。',3,'晋卿，忻州人也。','晋卿承接本段客省使阎晋卿，籍贯不作为此战发生地。')
add('li_tao_leads_spear_counterattack','李韬持槊率先反击，众人跟随',3,'裨将李韬曰：','众从之。',[('李韬','反问将士为何不为国力战，持槊率先迎敌')],when='949年正月戊申夜',place='河中城外后汉营寨',note='援槊是持长槊作战，不是申请外部援军；未由众从之补出精确跟随人数。')
sup('li_tao_leads_spear_counterattack',3,litao,'韜憤怒曰：「豈有食君祿而不為國致死耶！」即援槊而進，軍中死士十餘輩隨韜犯賊鋒。','《宋史》同记李韬持槊出战，另记十余名敢死士跟随。','人数是该传补充，主书没有列；该传交战细节较多，但没有在这句独立提供戊申纪日。',relation='adds')
claim('person',people['李韬'],'description','《宋史》记李韬是河朔人，善用槊，曾任禁军队长。',3,'李韜，河朔人。有勇力膽氣，善用槊，為禁軍隊長。','与主书同次河中袭寨所见裨将对应；不把传记后续官职和卒年提前归到949年。',source=litao)
add('hezhong_raiders_defeated_wang_wounded','河中袭寨军退败，七百人死亡，王继勋重伤逃回',3,'河中兵退走，','仅以身免。',[('王继勋','所部退败，本人重伤但逃得性命')],when='949年正月戊申夜反击之后',place='河中城外后汉营寨',note='七百是主书所记战死数，不当两军总伤亡；王继勋重伤未死亡，不录死亡年。')
sup('hezhong_raiders_defeated_wang_wounded',3,jan,'乙卯，河府軍前奏，今月四日夜，賊軍偷斫河西寨，捕斬七百餘級。','《旧五代史》正月乙卯奏报夜袭河西寨，捕斩七百余。','主书记死者七百，本纪记捕斩七百余，数量和统计口径各自保留；乙卯是奏报日，不是夜袭日。',relation='adds')
sup('hezhong_raiders_defeated_wang_wounded',3,wang,'守貞又遣繼勳與其愛將聶知遇夜出攻河西砦，復為漢兵所敗，被創而遁。','《宋史》同记王继勋夜攻河西寨失败，受伤逃回，另列聂知遇同攻。','补充同攻将领，但没有在该句列七百战死或具体日；不因两书次序概述把此战重复建档。',relation='adds')
add('guo_rewards_liu_ci_after_raid','郭威到河中，刘词请罪，郭威厚赏他的反击之功',3,'己酉，','然虏伎殚于此矣。”',[('郭威','到河中后厚赏刘词，肯定其抵御夜袭'),('刘词','迎接郭威并请罪，受到赏赐')],when='949年正月己酉',place='河中围城军',note='赏赐内容和数额未载；郭威说敌方手段已尽是其判断，不当作后来再无出兵。')
add('li_shouzhen_supplies_wine_to_patrols','李守贞派人在村野供酒，巡逻骑兵多醉，河中军趁机入寨',4,'守贞之欲','几至不守。',[('李守贞','攻寨前派人供酒，使所部趁巡逻骑兵醉酒潜入军寨')],year=None,when='949年正月戊申夜袭之前的追叙，具体供酒年月日未载',place='河中围城军附近村野',note='酤酒结合赊与、不责其直理解为提供酒；不是此段又记一次独立夜袭，赊送给酒的方式不确定为现代商业买卖。')
add('guo_wei_bans_private_drinking','郭威禁止将士在犒宴之外私下饮酒',4,'郭威乃下令：','毋得私饮！”',[('郭威','下令将士除犒宴外不得私下饮酒')],when='949年正月郭威返回河中后，具体下令日未载',place='河中围城军',note='军令有犒宴例外，不写成任何场合一律禁酒；下令与违反军令后的处置分开。')
add('guo_executes_li_shen_drinking','李审违反禁酒令，郭威将他处死示众',4,'爱将李审，',None,[('李审','早晨私饮少量酒，违反军令'),('郭威','因李审先违军令，将其处死示众')],when='949年正月禁酒令下达后，具体日未载',place='河中围城军',note='郭威是帐下主将，此处不是皇帝判决；酒量只记少酒，不推醉酒失职或酒精数值。')
sup('guo_executes_li_shen_drinking',4,guo,'先是，軍中禁酒，帝有愛將李審犯令，斬之以徇。','《旧五代史》也记郭威在军中禁酒，亲近将领李审犯令后被处死示众。','帝是周太祖纪对郭威的追称，949年郭威尚未称帝；该句先是未给具体处罚日。')
add('an_retires_fengzhou_requests_punishment','安思谦退驻凤州并上表请罪，孟昶没有追究',5,'甲寅，','蜀主释不问。',[('安思谦','退驻凤州，上表请罪'),('孟昶','没有追究安思谦此次退兵')],when='949年正月甲寅',place='凤州、后蜀朝廷',note='释不问是未追究此次退兵，不当以后任何处置都获赦免；与上年撤军消息分开。')
add('han_assigns_jingzhou_dingnan','后汉将静州划归定难军',5,'诏以静州','隶定难军，',[('刘承祐','在位朝廷下诏将静州划归定难军'),('李彝殷','作为定难军节度使成为静州隶属变更的受命者')],when='949年正月安思谦退兵条后、二月辛未谢表前，具体下诏日未载',place='静州、定难军',note='静州与荆州字形不同，保留史载名称，不无证赋现代坐标；这句没有给出甲寅作为下诏日期。')
add('li_yiyin_thanks_jingzhou_assignment','李彝殷上表感谢静州划归定难军',5,'二月，','李彝殷上表谢。',[('李彝殷','向后汉朝廷上表谢恩')],when='949年二月辛未',place='定难军至后汉朝廷',note='谢表承接前句静州隶属变更，不虚构谢表全文或其他赏赐。')
add('li_yiyin_secret_aid_for_payments','史书记李彝殷常暗助叛乱者，索取厚赂',5,'彝殷以中原多故，','邀其重赂。',[('李彝殷','因中原多事而自恃，暗助叛乱者并索取厚赂')],year=None,when='李彝殷在中原多事期间的概括追叙，具体起止年月未载',place='定难军及有关藩镇，具体地点未载',note='每常等词为史家概述，不新造具体每次援助、赂数或收钱日期；态度评价按史书注明。')
add('han_keeps_li_yiyin_with_favors','后汉朝廷知道李彝殷暗助叛乱，仍以恩赏维系他',5,'朝廷知其事，',None,[('李彝殷','在朝廷知其暗助叛乱后仍受恩赏维系')],year=None,when='后汉朝廷处理李彝殷时的概括记载，具体年月未载',place='后汉朝廷、定难军',note='未具名具体恩赏，不将静州划归必然解释为此次暗助叛乱的交换。')
add('huai_groups_seek_southern_tang','淮北多支武装向南唐请求归附',6,'淮北群盗','多请命于唐，',[],when='949年二月条下，具体日未载',place='淮北至南唐',note='群盗是史书记载的称呼；具体组织与人数未列，归附请求不等于所有组织已被招纳。')
add('li_jing_sends_huangfu_recruitment','李璟派皇甫晖等率万人到海州、泗州招纳淮北武装',6,'唐主遣','以招纳之。',[('李璟','派皇甫晖等率万人招纳淮北武装'),('皇甫晖','以神卫都虞候身份率兵万人出海州、泗州')],when='949年二月条下，具体日未载',place='海州、泗州',note='出海、泗是出兵至海州泗州，不是出海航行；万人为率军数量，不当归降武装人数。')
add('xian_shilang_surrenders_huangfu','蒙城镇将咸师朗等向皇甫晖投降',6,'蒙城镇将','等降于晖。',[('咸师朗','以蒙城镇将身份向皇甫晖投降'),('皇甫晖','接受咸师朗等投降')],when='949年二月南唐招纳期间，具体日未载',place='蒙城及南唐军，具体受降地点未载',note='等未列其他降将，不补归降名单或已获新任命。')
add('cheng_deqin_defeats_tang_dongwu','成德钦在峒峿镇击败南唐兵，俘斩六百',6,'徐州将成德钦','俘斩六百级，',[('成德钦','击败南唐兵，获俘斩战果六百')],when='949年二月条下，具体交战日未载',place='峒峿镇',note='俘斩是综合战果，不能全写成战死；具体日与人数按不同书证分别记录。')
sup('cheng_deqin_defeats_tang_dongwu',6,feb,'庚寅，徐州巡檢使成德欽奏，至峒吾鎮遇淮賊，破之，殺五百人，生擒一百二十人。','《旧五代史》二月庚寅记成德钦奏报在峒吾镇击败南唐军，杀五百、生擒一百二十。','庚寅为奏报日，主书未列交战日；峒吾与峒峿字形、五百加一百二十与俘斩六百的统计差异保留，未强行凑成同数。',relation='conflicts')
add('huangfu_hui_withdraws_after_defeat','皇甫晖等在南唐军被击败后撤回',6,'晖等引归。',None,[('皇甫晖','所部交战失利后撤回')],when='949年二月成德钦击败南唐军之后，具体日未载',place='峒峿镇至南唐方向',note='原文未给回到哪座城和确切归期，不补行军路线。')
add('jin_li_dowager_requests_farmland','后晋李太后向耶律阮请求迁居和赐田',7,'晋李太后','给田以耕桑自赡。',[('李太后','向耶律阮请求靠近汉人城寨，并给田以自给'),('契丹主','成为李太后请求的对象')],when='949年二月迁建州以前，具体请求日未载',place='契丹境内，请求地点未载',note='自赡为耕桑自给，不指帝王恢复统治；李太后复用后晋石敬瑭妻的永宁公主主体，不与后汉李三娘合并。')
claim('person',people['永宁公主（石敬瑭妻）'],'description','后晋李太后是原永宁公主、石敬瑭的皇后。',7,'高祖皇后李氏，唐明宗皇帝女也。后初號永寧公主，','引文的高祖为后晋石敬瑭，女儿为后唐李嗣源之女；以书内晋家人传与当前身份对应复用既有主体。',source=li)
add('khitan_moves_jin_household_jianzhou','耶律阮准许请求，把李太后和石重贵迁到建州',7,'契丹主许之，','并晋主迁于建州。',[('契丹主','准许李太后请求，把她与石重贵迁建州'),('李太后','与石重贵一同迁往建州'),('晋主','被迁往建州')],when='949年二月，具体迁移日未载',place='契丹境内至建州',note='建州为当时契丹境内地名，不直接对应现代同名行政区。')
sup('khitan_moves_jin_household_jianzhou',7,jian,'明年乃漢乾祐二年，其二月，徙帝、太后于建州。自遼陽東南行千二百里至建州，節度使趙延暉避正寢以館之。','《新五代史》明确记乾祐二年二月从辽阳迁到建州，赵延晖腾出正寝安置石重贵一行。','千二百里保留古距离，不作现代公里或坐标；当前只补行程与安置，不凭该句建立未出现于主线的具体交往关系。',relation='adds')
add('an_taifei_dies_on_journey','安太妃在迁建州途中去世',7,'未至，','安太妃卒于路。',[('安太妃','在尚未到建州时于途中去世')],when='949年二月迁建州途中，具体日未载',place='迁建州途中',note='安太妃复用石重贵亲生母亲安氏；没有给出具体死亡地点和年龄。')
sup('an_taifei_dies_on_journey',7,an,'妃老而失明，從出帝北遷，自遼陽徙建州，卒於道中。','《新五代史》同记安太妃从辽阳迁建州途中去世，并记她年老失明。','她的身体状况为该书补充，未据年老推算生年。',relation='adds')
claim('person',people['安氏（石重贵母）'],'death_year','安氏于949年迁建州途中去世。',7,'未至，安太妃卒于路。','安太妃与石重贵母亲的身份由新五代史安太妃传相互核对，死亡年按当前迁徙年，不覆盖旧批次字段。')
add('an_taifei_last_wishes_cremation','安太妃遗愿火化遗骨向南撒扬，希望魂魄归乡',7,'遗令：','庶几魂魄归达于汉。”',[('安太妃','留下火化遗骨并向南撒扬的遗愿')],when='949年迁建州途中临终时，具体日未载',place='迁建州途中',note='汉指汉地和故乡方向，不写成政治支持后汉；遗愿与实际实行分开。')
sup('an_taifei_last_wishes_cremation',7,an,'既卒，砂磧中無草木，乃毀奚車而焚之，載其燼骨至建州。','《新五代史》另记安太妃去世后，因沙地缺少草木，拆车火化并把骨灰遗骨带到建州。','该书实际处理记为带到建州，与遗愿向南撒扬分别保留，不说遗愿已经全部完成；后文李太后死亡未据此定为949年。',relation='adds')
add('shi_chonggui_farmland_self_support','石重贵到建州后获五十余顷田，让随从耕种供食',7,'既至建州，','以给食。',[('晋主','得到五十余顷田，让随从耕种供食')],when='949年二月迁到建州以后，具体日未载',place='建州及所赐田地',note='五十余顷是概数及历史面积单位，不换算现代面积；从者未列姓名与户数。')
sup('shi_chonggui_farmland_self_support',7,jian,'去建州數十里外得地五十餘頃，帝遣從行者耕而食之。','《新五代史》同记得到五十余顷田，并记田地在距建州数十里外。','主书未列城外距离，该书补地望，不据此赋坐标。',relation='adds')
add('shulu_takes_jin_favored_women','述律王派骑兵带走石重贵的宠姬赵氏、聂氏',7,'顷之，','契丹主德光之子也。',[('述律王','派骑兵带走石重贵两位宠姬'),('晋主','宠姬赵氏、聂氏被带走'),('赵氏','被述律王派骑兵带走'),('聂氏','被述律王派骑兵带走')],when='949年迁到建州后不久，具体日未载',place='建州至去向未载',note='原文取而去，未述两位女子同意或婚姻结果，不建她们与述律王的夫妻关系。')
claim('person',people['耶律璟'],'aliases','《辽史》记耶律璟小字述律，是耶律德光长子、寿安王。',7,'穆宗孝安敬正皇帝，諱璟，小字述律。太宗皇帝長子，母曰靖安皇后蕭氏。會同二年，封壽安王。','穆宗是此书对他后来的帝号；当前只用该段核对述律王姓名亲支，不把即位提前到949年。',source=jing)
relationship('耶律德光','述律王','父亲',7,'述律王者，契丹主德光之子也。','德光是述律王的父亲；辽史小字与亲支对应，述律王复用新建耶律璟，不误合罨撒葛。')
relationship('赵氏','晋主','宠姬',7,'晋主宠姬赵氏、聂氏','原文明示赵氏是石重贵的宠姬，采用具体称谓，不推个人姓名或封位。')
relationship('聂氏','晋主','宠姬',7,'晋主宠姬赵氏、聂氏','原文明示聂氏是石重贵的宠姬，不据被带走推后续婚姻关系。')
add('shi_dechong_gets_zhongzhou_title','史德珫由归德牙内指挥使领忠州刺史',8,'三月，','领忠州刺史。',[('刘承祐','在位朝廷任命史德珫领忠州刺史'),('史德珫','由归德牙内指挥使领忠州刺史')],when='949年三月己未',place='后汉朝廷、归德军',note='领为兼领刺史衔，不无证认作已经赴忠州上任；名称珫与旧史充以父子官职及事件核对。')
claim('person',people['史德珫'],'description','史德珫读过一些书，常不赞同父亲史弘肇的做法。',8,'德珫，弘肇之子也，颇读书，常不乐父之所为。','读书和态度是史书记载，不据颇读书推成某个科举功名。')
claim('person',people['史德珫'],'aliases','《旧五代史》把史德珫写作史德充。',8,'宏肇子德充，乾祐中，授檢校司空，領忠州刺史。','两书父亲、忠州职名及释放举人事件对应，作为同人异名；旧史乾祐中没有列己未。',source=dechong)
relationship('史弘肇','史德珫','父亲',8,'德珫，弘肇之子也，','史弘肇是史德珫的父亲，不与此前李德珫或李德充合并。')
add('su_fengji_requests_scholar_punishment','举人在贡院门喧哗，苏逢吉命送侍卫司，要求重打刺面',8,'有举人呼譟','欲其痛棰而黥之。',[('苏逢吉','把喧哗举人送往侍卫司，要求重打并刺面')],year=None,when='史德珫劝父释放举人的追叙，具体年月未载',place='贡院门、侍卫司',note='欲是要求实施的刑罚，后文举人获释放，不写成已经被打或刺面。举人姓名未载。')
add('shi_dechong_asks_release_scholar','史德珫劝父亲，举人无礼应由地方司法机关处理',8,'德珫言于父曰：','此乃公卿欲彰大人之过耳。”',[('史德珫','劝父亲将举人的无礼行为交由府县御史机构处理'),('史弘肇','听取儿子对军务与普通司法的区分')],year=None,when='举人被送侍卫司之后的追叙，具体年月未载',place='侍卫司，劝谏具体地点未载',note='公卿欲彰父过是史德珫的判断，不认作已查明苏逢吉有此真实动机。')
sup('shi_dechong_asks_release_scholar',8,dechong,'德充聞之，白父曰：「書生無禮，有府縣御史臺，非軍務治也。公卿如此，蓋欲彰大人之過。」宏肇深以爲然，即破械放之。','《旧五代史》同记史德充劝父亲将书生无礼交府县御史台处理，史弘肇认可并释放举人。','两书话语对应，不把书生身份推为已任官；该传未给具体年月日。')
add('shi_hongzhao_releases_scholar','史弘肇采纳儿子的劝告，去掉拘具放走举人',8,'弘肇大然之，',None,[('史弘肇','认可史德珫意见，去掉拘具释放举人')],year=None,when='史德珫劝谏之后的追叙，具体年月未载',place='侍卫司',note='破械为解除拘具，不是破坏监狱或释放全部在押者；与上一年史弘肇滥刑事件并存，不能概括成全面停止滥刑。')
add('xu_jin_wins_fengyangshan','楚将徐进在风阳山击败部族武装，史载斩首五千',9,'楚将',None,[('徐进','在风阳山击败史书称为蛮的部族武装')],when='949年三月条下，具体交战日未载',place='风阳山',note='蛮为史书泛称，未确定具体族属；五千级是史载战果，不当现代核实统计，也不等同上年贺州南汉与楚军之战。')
sup('xu_jin_wins_fengyangshan',9,may,'己巳，湖南奏，蠻寇賀州，遣大將軍徐進率兵援之，戰於風陽山下，大敗蠻獠，斬首五千級。','《旧五代史》五月己巳记湖南奏报，称徐进以大将军身份援贺州，在风阳山下击败部族武装，斩首五千。','己巳是五月奏报日，主书三月条未列交战日，不把战斗移作五月己巳发生；援贺州目标为该书补充。',relation='adds')
add('venus_visible_daytime','史书记四月壬午金星在白天可见',10,'夏，四月，','太白昼见，',[],when='949年四月壬午',place='观测地点未载',note='太白为金星；只录史书观测，不解释为必然预示政变或灾难。')
add('shi_executes_man_looking_at_venus','有人抬头看金星，被巡卒抓走后遭史弘肇腰斩',10,'民有仰视之者，',None,[('史弘肇','把被巡卒抓来的仰观者腰斩')],when='949年四月壬午',place='后汉京城',note='抬头观看不是史料证明的犯罪行为；巡卒和受害者未具姓名，不补其政治身份或谣言言论。')
sup('shi_executes_man_looking_at_venus',10,punish,'時太白晝見，民有仰觀者，爲坊正所拘，立斷其腰領。','《旧五代史》也记有人白天看金星，被坊正拘捕后遭处死。','该书拘捕者为坊正，主书为逻卒，身份称谓分别保留；该传没有壬午纪日，不单由传记重新定日。',relation='adds')
add('hezhong_starvation_high_death_share','河中粮食将尽，史书记百姓饿死者达五六成',11,'河中城中食且尽，','民饿死者什五六。',[],when='949年四月癸卯出兵之前，具体统计时点未载',place='河中城内',note='什五六按原文比例释为五六成，属于史书记载，未给人口基数或现代调查依据；不反推绝对死亡人数。')
add('li_shouzhen_five_route_assault','李守贞派五千余兵携梯桥，分五路攻围垒西北角',11,'癸卯，','长围之西北隅。',[('李守贞','派五千余人携攻具，分五路攻击围垒西北角')],when='949年四月癸卯',place='河中围垒西北角',note='五千余为此役出兵，不与正月千余夜袭合并；梯桥为攻城器具，未给具体结构尺寸。')
add('wu_qianyu_flanks_hezhong_attack','郭威派吴虔裕横击，河中军败走，攻具被夺',11,'郭威遣','夺其攻具。',[('郭威','派都监吴虔裕从侧面截击'),('吴虔裕','率军横击，击退河中兵并夺攻具')],when='949年四月癸卯',place='河中围垒西北角',note='杀伤太半指死伤过半，不写成过半全部战死；无精确数，不用五千余算出固定死伤总数。')
add('li_shouzhen_may_assault_captured_generals','李守贞再次出兵失败，魏延朗和郑宾被擒',11,'五月，','擒其将魏延朗、郑宾。',[('李守贞','再次出兵，被后汉军击败'),('魏延朗','作为李守贞部将被擒'),('郑宾','作为李守贞部将被擒')],when='949年五月丙午',place='河中围城军附近',note='又败之的后汉执行将领此句未具名，不将吴虔裕无证补为本次擒将者；被擒不等于已经被杀。')
add('zhou_wang_nie_surrender','周光逊、王继勋和聂知遇率千余人投降',11,'壬子，','来降。',[('周光逊','与王继勋、聂知遇率千余人投降'),('王继勋','与周光逊、聂知遇率众投降'),('聂知遇','与周光逊、王继勋率众投降'),('郭威','其围城军接受降兵')],when='949年五月壬子',place='河中城西及后汉围城军',note='三将沿已有稳定主体；千余为随三将投降部众，不自动等于军府全体人员。')
sup('zhou_wang_nie_surrender',11,may,'乙卯，河府軍前奏，今月九日，河中節度副使周光遜棄賊河西寨，與將士一千一百三十人來奔。','《旧五代史》五月乙卯奏报周光逊于本月九日带一千一百三十名将士投降。','主书五月壬子记三将千余人来降，旧书奏报只具名周光逊并列精确人数；分别保留行动日与乙卯奏报日，不替换主书概数。',relation='adds')
add('hezhong_more_surrenders','李守贞的将士接连投降，守军逐渐离散',11,'守贞将士降者相继，','威乘其离散，',[],when='949年五月壬子投降后、庚申攻城前',place='河中围城军',note='只录将士接连投降，没有具体每批姓名人数；离散不意味着此时城已攻克。')
add('guo_orders_many_pronged_hezhong_assault','郭威趁守军离散，督促各军从多处攻城',11,'庚申，',None,[('郭威','督促各军趁守军离散从多处攻城')],when='949年五月庚申',place='河中城',note='百道按多处进攻理解，不虚构一百条已测路线；此时是发起攻城，七月破城尚未录到。')
sup('guo_orders_many_pronged_hezhong_assault',11,guo,'十七日，下令攻城，會西北大風，揚沙晦冥，帝令禱河伯祠，奠訖而風止，自是晝夜攻之。','《旧五代史》周太祖纪记五月十七日下令攻城，此后昼夜进攻，另叙大风、祈祷和风停。','天气与祈祷按该书记载补充，不把祈祷认作风停的已证自然原因；主书保留庚申，七月破城另待后续。',relation='adds')
reviews={
1:'正月乙巳朔大赦，朔按月初一解释，不自行换公历日。',
2:'郭威将至与白文珂出迎分清，未把将至写成已到。',
3:'夜袭、刘词反击、辨甲、李韬领先、战败重伤及郭威奖赏分录；旧本纪正月四日、周本纪五日与主书戊申分别保留。捕斩与战死口径不同，王三铁名有具体注引，仍与同名其他人物分开。',
4:'供酒为袭寨前的追叙，具体年月未定；郭威禁酒有犒宴例外，李审违令被斩，周本纪帝为郭威追称，不倒填他949年已称帝。',
5:'安思谦甲寅退凤州获不究、静州隶定难与李彝殷二月辛未谢表分开。暗援求赂和恩赏维系是概括，不给每次行为硬定年月。',
6:'淮北请求、皇甫晖率万人招纳、咸师朗投降、成德钦击败与撤军分录。海泗是州名，不是出海；旧本纪奏报日、峒吾字形及五百加一百二十与主书六百的战果分别保留。',
7:'后晋李太后与后汉太后分开，复用永宁公主；安太妃复用石重贵母。迁建州、死亡、遗愿与实际火化、耕种及宠姬被带走分录。述律王据辽史对应耶律璟，不误合罨撒葛；被带走不建新婚姻。',
8:'史德珫与旧史德充按父子、官职及同事校名，不合李德珫。苏逢吉希望施刑不是实际已打黥；儿子劝告与父亲释放分录，释放举人是插入追叙，年月未知；揣测苏逢吉动机仍为说话者判断。',
9:'徐进击败的武装族属未知，不合上年南汉贺州战；三月条与五月己巳奏报区分，史载五千不作现代核实数字。',
10:'太白昼见与民众被处死分别记录，不把天象推成灾变因果；旧传坊正与主书逻卒的称谓分别保留。',
11:'粮将尽与史载五六成饿死、四月五千余兵进攻、吴虔裕横击、五月再败擒将、壬子三将降、连续降兵与庚申攻城分录，仍未到七月破城。旧史人数、奏报日及攻城细节单列补证。'}
assert not (P/'publication.json').exists()
for n in range(1,12):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=949,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,12)],next_paragraph=Q[12]['id'],next_volume=288,next_year=949,supplements=supplements,excluded_non_body=[],coverage='卷288原79—89行连续十一段，949年前11/37正文；未到七月城破，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,12)],source_issues_review='河中袭寨的同书不同篇日期、伤亡统计、峒峿/峒吾地名与数字差异并列；史德珫/史德充及述律王身份已据具体原文校核。安太妃遗愿与实际骨灰去向分别记录，李太后后续死亡不提前录。静州等地理与纸本异文尚待核。',plain_language_review='首次逐条检查人物介绍、事件正文、时间地点解释、参与角色、关系与事实说明，明确姓名主语。区分发令、请求、侦察判断、奏报、实际结果及追叙；原文保持底本字形，未知年月用null，异说不静默合并。复用主体不改旧档案元数据，不安排固定发布后二次重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
