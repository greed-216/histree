# -*- coding: utf-8 -*-
"""Original publication builder; retrospective dates subsequently corrected in content/revisions/2026-10-05-tuyuhun-retrospective-dates. Published archives must not be rebuilt."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,36))
specs=[(d.name,d,'c3ae4917b03ca0346efedf03bafabb5e360d93ab','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-940-summer','xinwudaishi-008-tianfu-five']:
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
main_sources = ['tongjian-282-940-summer','tongjian-282-940-autumn-winter']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0940-p021-p035',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-282-940-autumn-winter':'卷282·天福五年秋冬','jiuwudaishi-079-august-autumn':'卷79·晋高祖纪·天福五年八月及后续条目','jiuwudaishi-079-october':'卷79·晋高祖纪·天福五年十月','jiuwudaishi-079-november':'卷79·晋高祖纪·天福五年十一月','xinwudaishi-051-an-chongrong-tuyuhun':'卷51·安重荣传·吐谷浑归附','xinwudaishi-051-fan-yanguang-death':'卷51·范延光传·遇害异说','songshi-262-li-huan-career':'卷262·李涛附李澣传·任官','songshi-262-li-tao-age':'卷262·李涛传·年龄消歧'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(21, 36):
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
    labels={'tongjian-282-940-autumn-winter':'卷282·天福五年秋冬','jiuwudaishi-079-august-autumn':'卷79·晋高祖纪·天福五年八月及后续条目','jiuwudaishi-079-october':'卷79·晋高祖纪·天福五年十月','jiuwudaishi-079-november':'卷79·晋高祖纪·天福五年十一月','xinwudaishi-051-an-chongrong-tuyuhun':'卷51·安重荣传·吐谷浑归附','xinwudaishi-051-fan-yanguang-death':'卷51·范延光传·遇害异说','songshi-262-li-huan-career':'卷262·李涛附李澣传·任官','songshi-262-li-tao-age':'卷262·李涛传·年龄消歧'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '八月条下（月据新旧本纪）' if n==21 else '九月条下' if n<=27 else '十月条下' if n<=30 else '十一月' if n==31 else '十二月条下' if n<=33 else '岁末总结'
        citation = f'卷282·后晋天福五年（940；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0940_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=940, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='940年'+('八月' if n==21 else '九月' if n<=27 else '十月' if n<=30 else '十一月' if n==31 else '十二月' if n<=33 else '年末')+'条下，具体日期未载'
    key = 'event_zztj_282_0940_' + code
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
        edge = 'participation_zztj_282_0940_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0940_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})




ALIASES.update({'唐主':'李昪','曦':'王延羲','闽王':'王延羲','璟':'李璟','元瓘':'钱传瓘','赵损':'赵损（南汉宰相）','李浣':'李澣','李涛':'李涛（后晋宋初官员）'})
NEW_DESCRIPTIONS={
'杨承贵':'杨光远之子。940年受父亲派遣围范延光私宅，逼其自尽，随后把范延光推入河中。《新五代史》相关执行者写杨承勋，姓名异说未裁定，不自动合并。生卒年未载。',
'李澣':'李涛的弟弟，后晋翰林学士。《资治通鉴》说他多次酒后失当，石敬瑭不喜欢他；940年九月翰林学士职务被撤销、事务归中书舍人。《旧五代史》同期学士名写李浣，另记他调吏部员外郎，保留字形说明。生卒年未载。',
'孙智永':'为南唐李昪提出占星建议的术士。940年以四星聚斗、相关分野有灾为由，劝李昪巡行东都。灾祸属于他的占星判断，不当作已发生灾害。生卒年未载。',
'褚仁规':'南唐泰州刺史。940年因陈觉奏称其贪残，被调任随驾职务。《资治通鉴》说陈觉奏报出于私怨，未记正式查明贪残罪行。生卒年未载。',
'王定保':'南汉宁远节度使，籍贯南昌。940年赵损去世后任中书侍郎、同平章事，史书接记不逾年也去世；本处未给明确死亡年，不强定为940年。出生年未载。'}
NEW_ALIASES={'杨承贵':['楊承貴'],'李澣':['李浣'],'孙智永':['孫智永'],'褚仁规':['褚仁規'],'王定保':[]}
NEW_DESCRIPTIONS['李涛（后晋宋初官员）']='李澣的兄长，后晋至宋初官员。《宋史》记他宋初任兵部尚书，去世时六十四岁，年代与887年已在杨行密军中的同名李涛不相容，本批单独建档。生卒年不凭年龄反推，后续旧库记录需逐条核对。'
NEW_ALIASES['李涛（后晋宋初官员）']=['李濤']
autumn='jiuwudaishi-079-august-autumn';october='jiuwudaishi-079-october';nov='jiuwudaishi-079-november';fan='xinwudaishi-051-fan-yanguang-death';an='xinwudaishi-051-an-chongrong-tuyuhun';ann='xinwudaishi-008-tianfu-five'
add('fan_requests_home','范延光请求回河阳私宅，石敬瑭批准',21,'太子太师','延光重载而行。',[('范延光','请求回河阳，带大量行李出发'),('帝','批准范延光回私宅')],when='940年范延光遇害以前，具体月日未载',place='河阳',note='此前太子太师退休为已取得身份，不重造一次退休申请；重载未给数量和价值。')
sup('fan_requests_home',21,fan,'歲餘，使宣徽使劉處讓載酒夜過延光，','《新五代史》另记石敬瑭派刘处让夜访范延光，随后谈及契丹要求、劝他离京避使。','离京背景与《通鉴》请归获准的简记不同；传记的岁余没有据本处换算具体年。',relation='adds')
# A fuller independent account of the conversation, without asserting the envoy's claim as fact.
E['liu_churang_advises_fan']=event('liu_churang_advises_fan','刘处让以契丹追索的说法劝范延光离京',21,source_span(fan,'歲餘，使宣徽使劉處讓','乃挈其帑歸河陽，'),[('刘处让','夜访范延光，转述契丹追索并建议离京'),('范延光','听到追索说法后询问可否去河阳')],source=fan,year=None,when='范延光退休后离京以前，《新五代史》未给明确年月',description='《新五代史》记刘处让载酒夜访范延光，称契丹使者要求后晋交出他，劝其离京避使。范延光担心洛阳的杨光远，请问可否去河阳，刘处让表示可以。',note='追索是刘处让转述的话，不直接据此新增一条已经独立证实的契丹诏令；不重造此前退休事件。')
add('yang_requests_fan_death','杨光远贪图范延光财货，请求除掉他，石敬瑭拒绝',21,'西京留守','帝不许。',[('杨光远','以范延光可能逃敌为由请求除掉他'),('帝','拒绝杨光远的请求'),('范延光','成为杨光远奏请除掉的对象')],when='940年范延光遇害以前，具体月日未载',description='《资治通鉴》说，杨光远贪图范延光的财货，又担心他成为子孙的隐患，奏称范延光可能逃入敌国，应及早除掉。石敬瑭没有批准。',note='逃入敌国是杨光远的指控与猜测，不写范延光已经逃敌；动机明示归史书记述。')
add('yang_restricts_fan_residence','杨光远请求让范延光住西京，石敬瑭同意',21,'光远请敕','从之。',[('杨光远','请求限制范延光居住地点'),('帝','同意使范延光居西京'),('范延光','被要求居住西京')],when='940年范延光遇害以前，具体月日未载',place='西京')
add('yang_besieges_fan_house','杨光远派杨承贵围范延光宅第，逼他自杀',21,'光远使','尔父子何得如此？”',[('杨光远','派儿子带武装士卒逼迫范延光'),('杨承贵','率甲士围宅、逼范延光自杀'),('范延光','以皇帝所赐铁券与免死承诺抗辩')],when='940年范延光被推入河以前，具体日期未载',description='杨光远派儿子杨承贵带武装士卒围住范延光宅第，逼他自杀。范延光以皇帝所赐铁券及免死承诺质问杨氏父子。',note='主书杨承贵与新史杨承勋未裁定，不将两名直接合并；抗辩属于范延光本人言论。')
relationship('杨光远','杨承贵','父亲',21,'光远使其子承贵','其子明确对应杨光远；不同史书执行者姓名另作异说，不借此合并兄弟。')
add('fan_pushed_into_river','杨承贵强迫范延光上马，至浮梁把他推入河中',21,'己未，','挤于河。',[('杨承贵','持刃逼范延光上马，把他推入河中'),('范延光','被强迫到浮梁，推入河中死亡')],when='940年八月己未；月份据新旧五代史本纪',place='河阳浮梁',description='杨承贵持刃逼范延光上马，到浮梁后把他推入河中，导致死亡。《新五代史》范延光传写执行者为杨承勋，姓名异说保留。',note='主书接下来谎报赴水自尽，与实际被推区分；本处没有明确桥址现代坐标。')
sup('fan_pushed_into_river',21,ann,'秋八月丁酉，閱稼于西郊。己未，西京留守楊光遠殺太子太師范延光。','《新五代史》晋本纪明确把范延光被杀记在八月己未，并归责杨光远。','补月份；本纪简述责任人与通鉴具体执行者是不同叙事层次，不造两次死亡。',relation='adds',field='time_original')
sup('fan_pushed_into_river',21,fan,'其子承勳知州事，乃遣承勳以兵脅之使自裁。','《新五代史》范延光传把派兵逼迫及推河的执行者写为杨承勋，《资治通鉴》写杨承贵。','姓名有异，未改主书、未将承勋登记为承贵的已核别名，也未裁定哪一说准确。',relation='conflicts')
add('yang_false_suicide_report','杨光远谎报范延光自行投水，石敬瑭知情而未追究',21,'光远奏','不敢诘；',[('杨光远','把推河死亡报成自行投水'),('帝','知道实情，因畏惧杨光远势力而未追究')],when='940年八月范延光死亡以后，具体日期未载',description='杨光远上奏称范延光自行投水。《资治通鉴》记石敬瑭知道实情，但畏惧杨光远的强势，不敢追究。',note='帝知其故惮强属于主书解释；新史对皇帝动机另有说法，不能把不同解释合成确定心理诊断。')
sup('yang_false_suicide_report',21,fan,'高祖以適會其意，不問，','《新五代史》认为范延光被杀符合石敬瑭的心意，所以没有追问。','与通鉴知道实情但畏惧杨光远的解释不同，分书保留。',relation='conflicts')
add('shi_mourns_fan','石敬瑭为范延光停朝，追赠太师',21,'为延光',None,[('帝','停朝并追赠范延光'),('范延光','死后获追赠太师')],when='940年八月范延光死亡以后，具体日期未载',note='旧史太师与新传太傅有异，分别引用；停朝日数由旧史补，不推每书都有两日。')
sup('shi_mourns_fan',21,autumn,'己未，太子太師致仕範延光卒於河陽，廢朝二日，贈太師。','《旧五代史》记八月己未范延光死于河阳，停朝两日、赠太师。','旧史本纪简记卒，未在此条说明推河细节，不用卒字否认主书谋杀记载。',relation='adds')
sup('shi_mourns_fan',21,fan,'為之輟朝，贈太傅。','《新五代史》范延光传记停朝后赠太傅，《通鉴》及《旧五代史》本纪记太师。','追赠官衔异说保留，未强行统一太师与太傅。',relation='conflicts')
add('li_jing_refuses_crown_prince','李璟坚持辞去太子，李昪准许，仍按太子礼致笺',22,'唐齐王',None,[('璟','坚持辞去太子身份'),('唐主','准许辞太子，并令中外仍依太子礼致笺')],when='940年九月乙丑',description='李璟坚持辞去太子，李昪在乙丑准许，并命朝内外致笺仍按太子礼。',note='衔接七月立太子，辞去正式身份与保留礼遇区分，不写为当日再次册立。')
add('he_ning_chancellor','石敬瑭任和凝为中书侍郎、同平章事',23,'丁卯，',None,[('帝','任命和凝入相'),('和凝','由翰林学士承旨、户部侍郎任中书侍郎、同平章事')],when='940年九月丁卯')
sup('he_ning_chancellor',23,ann,'九月丁卯，翰林學士承旨、戶部侍郎和凝為中書侍郎、同中書門下平章事。','《新五代史》晋本纪也记九月丁卯和凝入相。','月份与主书相合；旧史连续段的中间月题未见，未据开头八月将此任命改记八月。')
sup('he_ning_chancellor',23,autumn,'丁卯，宰臣李崧加集賢殿大學士，以翰林學士承旨、戶部侍郎和凝為中書侍郎、平章事。','《旧五代史》同记丁卯和凝入相，并补记李崧加集贤殿大学士。','该电子段起八月，后续未见九月标题；具体月份依通鉴及新史，不把缺月题当作已经裁定的书间纪月冲突。',relation='adds')
E['li_song_jixian']=event('li_song_jixian','石敬瑭加李崧集贤殿大学士',23,'丁卯，宰臣李崧加集賢殿大學士，',[('帝','加授李崧官职'),('李崧','加集贤殿大学士')],source=autumn,when='940年九月丁卯；月份据同日和凝任命对照',note='独立出处补同日任官；旧史电子段缺中间月题，月份借主书与新史相同任命定位。')
add('liu_zhiyuan_audience','刘知远入朝',24,'己巳，',None,[('刘知远','以邺都留守身份入朝')],when='940年九月己巳')
add('li_song_reports_surplus','李崧报告各州仓粮账外结余较多',25,'辛未，','所馀颇多。”',[('李崧','报告各州仓粮账外结余')],when='940年九月辛未',note='计帐之外余粮按上奏事实记，未补粮仓名单、粮数或审计报告。')
add('shi_punishes_granary_officials','石敬瑭将非法征税等同枉法，免仓吏死罪而严惩',25,'上曰：',None,[('帝','规定法外征税同枉法，免仓吏死罪但严惩')],when='940年九月辛未',description='石敬瑭说，法外向百姓征税的罪责等同枉法；仓吏特别免死，但须各自严惩。',note='记录皇帝处置指示，未补具体刑种与仓吏名单，也不把账外结余全部据此断为已逐笔查实的非法征税。')
add('li_huan_disliked','史书记李澣屡有酒后失当，石敬瑭不喜欢他',26,'翰林学士','上恶之，',[('李澣','被史书记为屡有酒后失当'),('帝','不喜欢李澣的作风')],year=None,when='940年九月撤销学士职务以前的作风概述，具体起止年月未载',description='《资治通鉴》评价李澣轻薄，并说他多次酒后失当，石敬瑭不喜欢他。',note='轻薄为史书评价，未给具体酒后行为，不造轶事。')
add('shi_abolishes_hanlin','石敬瑭撤销翰林学士，将事务并入中书舍人',26,'丙子，','中书舍人，',[('帝','撤销翰林学士职务并合并其事务'),('李澣','所任学士职务随调整撤销')],when='940年九月丙子',description='石敬瑭撤销翰林学士，将相关事务并入中书舍人。',note='主书官职与旧史学士院机构表述分别保留，不扩大成永久禁止未来设置学士。')
sup('shi_abolishes_hanlin',26,autumn,'丙子，廢翰林學士院，其公事並歸中書舍人。','《旧五代史》同记丙子废翰林学士院，事务归中书舍人。','具体月份依通鉴，本电子段中间九月标题未见。')
relationship('李澣','李涛','弟弟',26,'澣，涛之弟也。','原文明示李澣是李涛之弟，主书上下文为同朝李涛；李浣字形另作职务对照。')
E['li_huan_libu']=event('li_huan_libu','李澣调任吏部员外郎',26,'以翰林學士、左右補闕李浣為吏部員外郎，',[('李澣','由翰林学士、左右补阙调任吏部员外郎')],source=autumn,when='940年九月丁丑条下；月份依前后主书官制调整对照',description='《旧五代史》记，撤销翰林学士院后，李浣调任吏部员外郎。本批按同期翰林学士职务与任官顺序识别为《资治通鉴》的李澣，保留字形说明。',note='澣、浣字形不同，官职与紧接撤院的调任用于身份对照；原文不改字，不声称只是自动繁简转换。')
sup('li_huan_libu',26,'songshi-262-li-huan-career','晉天福中，拜右拾遺，俄召為翰林學士。會廢學士院，出為吏部員外郎，','《宋史》也记李澣在后晋天福年间任翰林学士，撤院后调吏部员外郎。','姓名、撤院与调吏部的连续履历对照旧史李浣，支持主体识别；不提前录入传记后续重置学士院。')
claim('person_relationship',next(x['key'] for x in B['person_relationships'] if x['person_a_key']=='person_李澣'),'description','《宋史》同样记李澣是李涛的弟弟。',26,'濤弟澣，字日新。','同卷李涛附弟澣传明确亲属关系；此兄长使用后晋宋初李涛独立主体，未复用887年军将。',source='songshi-262-li-huan-career',relation='corroborates')
claim('person',people['李涛（后晋宋初官员）'],'description','《宋史》记此李涛宋初任兵部尚书，去世时六十四岁，用于与887年已参与杨行密军务的同名者区分。',26,'宋初，拜兵部尚書。','宋初与去世年六十四的同段记载共同用于身份消歧；不把后世任职提前记为940年行为，也不据年龄反推精确出生年。',source='songshi-262-li-tao-age')
claim('person',people['李涛（后晋宋初官员）'],'description','《宋史》记李澣的兄长李涛去世时六十四岁。',26,'濤卒，年六十四，贈右僕射。','年龄只用于核对同名人物的年代，不在本年生成其死亡事件。',source='songshi-262-li-tao-age')
add('yang_audience_and_rewards','杨光远入朝，石敬瑭以酬功为由任其将校为刺史',27,'杨光远入朝，','数人为刺史。',[('杨光远','入朝，麾下数名将校获任刺史'),('帝','准备调任杨光远，以围魏有功为由任其将校为刺史')],when='940年九月甲申调任以前，具体日期未载',description='杨光远入朝，石敬瑭打算把他调到别镇，称围魏时其部下有功未赏，应各给一州，随后任其数名将校为刺史。',note='原文未列将校姓名，不猜任命名单；酬功言辞和调镇意图都明示出处。')
add('yang_moves_pinglu','石敬瑭调杨光远为平卢节度使，封东平王',27,'甲申，',None,[('帝','调任杨光远并进封'),('杨光远','调任平卢节度使、东平王')],when='940年九月甲申',place='平卢')
sup('yang_moves_pinglu',27,autumn,'甲申，西京留守楊光遠加守太尉、兼中書令，充平盧軍節度使，封東平王。','《旧五代史》同记甲申调杨光远到平卢，封东平王，并加守太尉、兼中书令。','月份依主书九月；同日旧史补官衔，不用段首八月硬改后续官命月份。',relation='adds')
add('qian_grand_marshal','石敬瑭加钱传瓘天下兵马都元帅、尚书令',28,'冬，',None,[('帝','加授吴越王官衔'),('元瓘','加天下兵马都元帅、尚书令')],when='940年十月丁酉',note='主书尚书令与旧史守中书令官衔不同，分别保留。')
sup('qian_grand_marshal',28,october,'吳越王錢元瓘加守中書令，充天下兵馬都元帥。','《旧五代史》同记十月丁酉钱传瓘任天下兵马都元帅，加官写守中书令；《资治通鉴》写尚书令。','任元帅对应，加官有异；元瓘沿已有钱传瓘主体，不另建人物。',relation='conflicts')
add('tang_amnesty_and_titles','南唐大赦，并禁止奏章使用睿、圣称颂',29,'壬寅，',None,[('唐主','颁大赦并禁止奏章使用特定尊称')],when='940年十月壬寅',description='南唐大赦。李昪下诏，朝内外奏章不得使用睿、圣二字，违者按不敬论。',note='禁令范围为奏章，不扩成全社会禁字；未记实际追罚对象。')
add('sun_astrology_advice','孙智永以占星灾祸判断，劝李昪巡行东都',30,'术士孙智永','巡东都，',[('孙智永','按四星聚斗作灾祸判断并建议巡东都'),('唐主','收到占星与巡行建议')],when='940年十月巡行以前，具体日期未载',description='孙智永以四星聚于斗宿、对应分野将有灾为由，劝李昪巡行东都。',note='分野有灾是术士的占星判断，不据此新增实际发生天灾，不补四星具体星名。')
add('li_jing_regent','李昪命李璟监国',30,'乙巳，','齐王璟监国。',[('唐主','命齐王监国'),('璟','受命留守处理国事')],when='940年十月乙巳',note='九月已辞太子，此处仍齐王身份，不误写太子监国或已经即位。')
add('chen_accuses_chu','陈觉因私怨奏称褚仁规贪残',30,'光政副使','褚仁规贪残；',[('陈觉','因私怨奏报褚仁规贪残'),('褚仁规','遭陈觉奏报指控')],when='940年十月丙午处置以前，具体日期未载',description='《资治通鉴》说，光政副使、太仆少卿陈觉因私怨，奏称泰州刺史褚仁规贪婪残暴。',note='贪残是奏报指控，私憾为主书解释；未写已经查实的审判结论。')
add('chu_assigned_escort','褚仁规被调离泰州，改任随驾职务，陈觉开始掌权',30,'丙午，','觉始用事。',[('唐主','调动褚仁规的职务'),('褚仁规','调离泰州，改任随驾职务'),('陈觉','被史书记为从此开始掌权')],when='940年十月丙午',description='褚仁规被调离泰州，改任随驾职务。《资治通鉴》写官名为扈驾都部置，并说从此陈觉开始掌权。',note='都部置字形沿电子底本保留待核，不擅校为都部署；不写褚仁规原任随驾职务被罢，也不推陈觉已升其他未载官职。')
add('li_leaves_jinling','李昪离开金陵，前往江都',30,'庚戌，','唐主发金陵；',[('唐主','离开金陵巡行')],when='940年十月庚戌',place='金陵')
add('li_reaches_jiangdu','李昪抵达江都',30,'甲寅，',None,[('唐主','抵达江都')],when='940年十月甲寅',place='江都',note='甲寅为原纪日，不自行推算公历；与离开金陵分日记录。')
add('min_petitions_via_merchants','王延羲通过商人向后晋递表自辩',31,'闽王曦','自理；',[('曦','借商人递表向后晋自辩')],when='940年十一月册封以前，具体月日未载',note='表文具体辩解内容未载，商人姓名未知，不编写奏表或使者身份。')
add('shi_enfeoffs_min','石敬瑭任王延羲威武节度使、兼中书令，封闽国王',31,'十一月，',None,[('帝','授予王延羲军镇官职及闽国王封号'),('曦','获后晋正式授官册封')],when='940年十一月甲申',place='福州威武军',note='王延羲此前自称闽国王与本次后晋册封分阶段；未把册封当本人首次掌权。')
sup('shi_enfeoffs_min',31,nov,'甲申，制授閩國王延羲檢校太師、兼中書令、福州威武軍節度使，封閩國王。','《旧五代史》同记十一月甲申王延羲获封闽国王，授福州威武军节度使、兼中书令，并补检校太师。','主书闽王曦对应王延羲已核别名，官命日期相合。',relation='adds')
add('li_returns_due_to_ice','李昪想留居江都，因结冰影响漕运而返回',32,'唐主欲','乃还；',[('唐主','原想留居江都，因供给不足返回')],when='940年巡江都以后、十二月返金陵以前，具体日期未载',place='江都',description='李昪原想留在江都，但河水结冰，漕运供给不足，于是返回。',note='欲居是原先意图，不记录为已正式迁都；结冰与供给不足沿主书因果，不补冰期长度。')
add('li_returns_jinling','李昪回到金陵',32,'十二月，',None,[('唐主','结束巡行回到金陵')],when='940年十二月丙申',place='金陵')
add('zhang_yanhan_dies','南唐宰相张延翰去世',33,'唐右仆射',None,[('张延翰','任右仆射兼门下侍郎、同平章事时去世')],note='接十二月条下，无单独纪日，不补死因。')
add('zhao_sun_dies','南汉宰相赵损去世',34,'是岁，','赵损卒；',[('赵损','作为南汉宰相去世')],when='940年，具体月日未载',note='是岁明确本年，补此前939年延伸后事未确定的赵损死亡年；不推其父赵光裔死亡年。')
add('wang_dingbao_chancellor','南汉任王定保为中书侍郎、同平章事',34,'以宁远节度使','同平章事，',[('汉主','在赵损去世后任命王定保入相'),('王定保','由宁远节度使任中书侍郎、同平章事')],when='940年赵损去世以后，具体月日未载',description='赵损去世后，南汉任宁远节度使、南昌人王定保为中书侍郎、同平章事。',note='南昌是籍贯与王姓连接，不切成南昌王封号。汉主沿已有刘岩主体，不补未载诏书形式。')
add('wang_dingbao_dies','王定保入相后不逾年去世',34,'不逾年',None,[('王定保','在入相后不逾年去世')],year=None,when='王定保入相以后不逾年，具体死亡年份待核',description='《资治通鉴》接着记，王定保入相后不逾年也去世。此处没有另列明确死亡年，保留相对时间。',note='不逾年可能涉及跨年界，未单凭编在940年条下强定死亡年；不改成已经考定的精确一年内日期。')
add('tuyuhun_discontent','史书记吐谷浑部众归属契丹后受其侵扰，想转归中原',35,'初，','思归中国；',[],year=None,when='940年归附前的背景追述，具体起止年月未载',description='《资治通鉴》追述，石敬瑭割雁门以北之地给契丹后，吐谷浑部众归属契丹，因苦于贪虐，想转归中原。',note='此前割地已有主体事件，本条仅记录背景处境与意愿；中国在此是史书的中原政权语境，不套现代国界和民族身份。')
add('an_attracts_tuyuhun','安重荣招引吐谷浑部众，千余帐从五台归附',35,'成德节度使','自五台来奔。',[('安重荣','招引吐谷浑部众归附')],when='940年年末条下，具体归附月日未载',place='五台',description='安重荣再次招引吐谷浑部众。一千多帐部众从五台前来归附。',note='帐是原书部落户帐计数，不当一千多人；帅部落在本句可作率领动词，未列首领姓名，不补白承福或赫连功德。')
sup('an_attracts_tuyuhun',35,an,'是時，吐渾白氏役屬契丹，苦其暴虐，重榮誘之入塞。','《新五代史》也记吐谷浑白氏归属契丹、苦于暴虐，安重荣诱其入塞。','传记的白氏为所述族属，未据此把主书未名首领直接定为后来白承福；传记后续逐出发生在下一年，不提前录入。')
add('khitan_rebukes_shi','契丹派使者责问石敬瑭收容叛人',35,'契丹大怒，',None,[('帝','收到契丹关于收容归附者的责问')],when='940年吐谷浑归附以后，具体月日未载',description='契丹对部众归附不满，派使者责问石敬瑭收容其所称的叛人。',note='叛人是契丹指责的身份标签，不当网站对归附者的判断；使者姓名未载。')
sup('khitan_rebukes_shi',35,an,'契丹數遣使責高祖，并求使者，高祖對使者鞠躬俯首，受責愈謹，多為好辭以自解，而姑息重榮不能詰。','《新五代史》补记契丹多次遣使责问，石敬瑭谨慎答复，却未追究安重荣。','传记概述外交压力与应对，未据此补每次出使日期；与他书存在叙事依赖，不作完全独立确证。',relation='adds')
for name,n,quote in [('范延光',21,'挤于河'),('张延翰',33,'张延翰卒'),('赵损（南汉宰相）',34,'赵损卒')]:
 row=next(x for x in B['people'] if x['name']==name)
 if row['key'] not in reused:row['death_year']=940
 claim('person',row['key'],'death_year',f'{name}在940年去世。',n,quote,'本年死亡有明确编年或本纪补证；未知月日不补，复用主体的发布档案不改写。')
reviews={21:'范延光获准回河阳、杨光远奏请杀人被拒、限居获准、围宅逼死、铁券抗辩、己未推河、谎报自尽与皇帝不追究、停朝追赠分录。八月由新旧本纪补；新传承勋/主承贵、太傅/太师及皇帝动机各保留，未合并二人。刘处让劝离京及所称契丹追索作为独立传记补证，不当已确诏命。',22:'九月乙丑允许李璟辞太子，致笺仍依太子礼；衔接此前立太子，不误作再次册立。',23:'九月丁卯和凝入相，旧史补李崧集贤殿大学士；旧史长段缺中间九月题，月份依主与新史，不宣称已裁定纪月冲突。',24:'刘知远九月己巳入朝，无具体会谈内容不补。',25:'李崧奏账外余粮与皇帝非法征税同枉法、免死严惩指示区分；未给全部仓吏姓名、刑种或逐笔非法税账。',26:'李澣作风评价作为背景，九月丙子撤学士并事务至中书舍人；旧史机构名称及翌日李浣任吏部员外郎分别引用。澣/浣按同期官职动作对应，字形说明保留，不作自动繁简；弟弟关系明确。李涛按宋史年龄、宋初职务及附传身份新建后晋宋初主体，不复用887年杨行密将领。',27:'调杨光远前以酬功为由任其将校刺史，无名者不补。甲申平卢与东平王官命，旧史补守太尉、兼中书令；旧史中间月题缺失保留。',28:'十月丁酉天下兵马都元帅，两书加官尚书令/守中书令有异。',29:'南唐壬寅大赦及奏章禁睿圣，未扩成全社会禁字或补实际处罚名单。',30:'孙智永占星判断不是确实天灾；监国、陈觉私怨奏报、褚仁规改随驾职务、陈觉用事及巡行两日分别录。贪残为指控，扈驾都部置底本字形待核。',31:'王延羲借商人递表自辩，十一月甲申获正式册封；自称与册封不是同一阶段，旧史补检校太师。',32:'拟留江都与因结冰漕运不足而返、十二月丙申抵金陵区分，不记已迁都。',33:'张延翰死亡在十二月条下，确日及死因未载。',34:'赵损是岁明确940年去世；王定保宁远任相与不逾年死亡分别录，后者未强定年。南昌为籍贯，王是姓。赵光裔死亡年仍未知。',35:'割雁门以北是此前背景，不重复建割地事件；安重荣招引及千余帐五台归附、契丹责问分别录。帐不当人数，未名领袖不猜白承福。新史以后逐出不提前录入。'}
assert not (P/'publication.json').exists()
for n in range(21,36):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=940,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(21,36)],next_paragraph='zztj-v282-y0941-p001',next_volume=282,next_year=941,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第21—35段，原69—83行；八月至年末。940年末批，尚需发布及全年核验后才记年度完成。',source_issues_review='范延光执行者承贵/承勋、追赠太师/太傅、皇帝动机各书有异；旧史本纪秋季连续段缺中间九月题；钱传瓘尚书令/守中书令、李澣/李浣、扈驾都部置字形保留待核。王定保死亡年、赵光裔死亡年未硬系；电子本纸本仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,36)],plain_language_review='首次检查各展示字段、身份、时间、关系方向与引用。指控、占星判断、计划与实际行动区分，史书评价和人物话语注明归属；未知年与姓名异说保持待核，原文不改字。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
