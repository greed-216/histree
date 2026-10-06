# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 23–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,58))
COMMIT='32533eed18a7fca71281bc84f91c0f9a586b003c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

for key in ['tongjian-293-956-li-deming-changzhou','xinwudaishi-062-947-succession']:
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
main_sources = ['tongjian-293-956-li-deming-changzhou','tongjian-293-956-april-yangzhou-liuhe']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0956-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
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
lines = (ROOT / 'resources/derived/tongjian/293.txt').read_text().splitlines()
for n in range(17, 25):
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
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷293·显德三年（956年三月至四月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0956_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'王环（后蜀凤州节度使）':'镇州真定人，早年以勇力为孟知祥御者，后掌后蜀宿卫。开运末秦凤等地入蜀后，孟昶任其为凤州节度使。955年十一月凤州陷落时被后周军俘获。与914—929年楚水军将领王环分别保存，无同人证据。生卒年未载。','王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
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

def event(code, title, n, quote, actors, when=None, note='', year=956, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='956年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_293_0956_' + code
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
        edge = 'participation_zztj_293_0956_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_293_0956_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 if kw.get('source'):
  t=(sources[kw['source']]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);quote=t[a:b]
 else:quote=span(n,start,end)
 E[code]=event(code,title,n,quote,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)










ALIASES.update({'上':'柴荣','帝':'柴荣','蜀主':'孟昶','唐主':'李璟','太祖皇帝':'赵匡胤','景达':'徐景达','李景达':'徐景达','陆孟俊':'陆孟俊'})
NEW_ALIASES={'吕彦琦':['呂彥琦'],'陈德诚':['陳德誠'],'郑彦华':['鄭彥華'],'林仁肇':[],'杨昭恽':['楊昭惲'],'杨氏（杨昭恽族女）':[]}
NEW_DESCRIPTIONS={
'吕彦琦':'后蜀武定节度使。956年三月孟昶整编卫圣、匡圣步骑为左右十军时，任命吕彦琦等为军使，李廷珪统领。与已录李彦琦、张彦琦姓氏不同，不直接合并。生卒年未载。',
'陈德诚':'静江指挥使。956年南唐潘承祐在泉建募兵时举荐，随后陆孟俊恢复泰州，派其戍守。生卒年未载。',
'郑彦华':'建州人。956年潘承祐荐其骁勇，李璟任为将，参与南唐应对后周的军务。生卒年未载。',
'林仁肇':'建州人，林仁翰的弟弟。956年由潘承祐荐任南唐将领。生卒年及后续军务待按编年续录。',
'杨昭恽':'曾任舒州刺史。《通鉴》追述951年陆孟俊参与废马希萼、立马希崇时，灭其家族并取财。与已有杨昭遂、杨昭俭名字不同，未因相似字形合并。生卒年未载。',
'杨氏（杨昭恽族女）':'杨昭恽家族的女子，姓名未载。951年家族遭陆孟俊杀害后，被送给马希崇；956年又被马转送韩令坤。陆孟俊被俘后，她请求复仇，称家中二百口被杀。保留称谓与本人说辞，不编造实名或将二百口当独立精确清点。'}
old='jiuwudaishi-116-april-yangzhou-liuhe';song='songshi-1-liuhe-battle-956';succ='xinwudaishi-062-947-succession'
add('shu_ten_armies','孟昶任李廷珪统左右卫圣诸军，分步骑为左右十军',17,Q[17]['text'],None,[('蜀主','整编军队并任命军官'),('李廷珪','任左右卫圣诸军马步都指挥使，总领十军'),('吕彦琦','以武定节度使身份任军使')],when='956年三月甲寅',place='后蜀',note='如赵廷隐之任为职务类比，不写成赵廷隐此时也参加新任命；等未列完整十军军使名单。')
add('chaikehong_repairs_xuanzhou','柴克宏任宣州巡检使时，驳斥不修城的理由，补齐城防器械',18,'初，柴克宏','悉缮完之。',[('柴克宏','在宣州修复城堑、补齐器械')],year=None,when='956年宣州战事以前的任巡检使旧事，具体任年未载',place='宣州',description='柴克宏初到宣州时，城堑失修、器械缺乏。当地官吏以田頵、王茂章、李遇先后叛乱后无人敢修为理由，柴认为时势已经改变，随后修缮完备。前人叛乱是官吏的解释，不在此重建956年三场叛乱。')
add('luyanzhu_withdraws','路彦铢攻宣州未克，闻吴程战败后撤兵',18,'由是路彦铢','乙卯，引归。',[('路彦铢','未攻下宣州，在闻吴程兵败后撤回')],when='956年三月乙卯撤回，攻城起日未载',place='宣州至吴越',note='由是是主书将此前修城与守住宣州联系的解释，未给现代攻防统计。')
add('chai_promoted_requests_shouzhou','李璟任柴克宏为奉化节度使，柴再请领军救寿州',18,'唐主以克宏','救寿州，',[('唐主','任柴克宏为奉化节度使'),('柴克宏','获任后再次请求领军救寿州')],when='956年三月常宣战事之后，具体任命日未载',place='南唐至寿州',note='请救与实际到达分开，本段后句明确未到就去世。')
add('chaikehong_dies_before_arrival','柴克宏未到寿州即去世',18,'未至而卒。',None,[('柴克宏','救寿州未抵达即去世')],year=None,when='956年常宣战事后请救寿州之后，具体死亡年日未单列',place='赴寿州途中或出军前，具体地点未载',note='未至仅证明未到寿州，不能据此指定死亡路段；后续死日缺乏独立纪时，保留不确定。')

add('baichongzan_prepares_heyang','白重赞担心北汉乘南征入侵，加强河阳守备并向西京求兵',19,'河阳节度使白重赞','且请兵于西京。',[('白重赞','修备河阳并请求西京援军')],when='956年柴荣南征期间，具体日未载',place='河阳及西京',note='担心入侵不等北汉此时已经攻入河阳。')
add('wangyan_self_sends_relief','王晏先未给兵，后担忧意外而亲领军到河阳',19,'西京留守王晏','乃自将兵赴之。',[('王晏','先拒援，随后自行领军前往')],when='956年白重赞求援之后，具体日未载',place='西京至河阳',note='自行前往与持朝廷正式诏令有区别。')
add('baichongzan_refuses_wangyan','白重赞以王晏没有诏命拒纳，王晏返还，孟洛民众受扰',19,'重赞以晏',None,[('白重赞','不接纳王晏军并遣人婉拒'),('王晏','被拒后惭愧返还')],when='956年王晏到河阳时，具体日未载',place='河阳、孟洛',note='数日惊扰是史载民众感受概述，不给未载民损数量。')
gd=person('景达',20,'南唐齐王、诸道兵马元帅',span(20,'唐主命','前武安节度使边镐为应援都军使。'))
claim('person',gd,'description','《新五代史》记南唐景达为元帅、封齐王。',20,'景達為元帥，封齊王；','《新五代史》南唐世家在保大五年记景达为元帅、封齐王，与既有徐诰子徐景达同一谱系，姓名改姓背景沿此前李昪恢复李姓记录。',source=succ,relation='adds')
add('tang_qiwang_chenjue_bianhao','李璟命齐王景达领兵拒周，陈觉监军，边镐应援',20,'唐主命','前武安节度使边镐为应援都军使。',[('唐主','安排拒周主军和监军应援'),('景达','以齐王和诸道元帅身份领军'),('陈觉','任监军使'),('边镐','以前武安节度使身份任应援都军使')],when='956年三月常州战事之后，具体任命日未载',place='南唐至淮南',note='景达复用早年徐景达，不因省姓和改姓再分人。')
add('hanxizai_opposes_monitor','韩熙载认为亲王元帅已足可信，反对另设监军，李璟不听',20,'中书舍人韩熙载','唐主不从。',[('韩熙载','上书反对设置监军'),('唐主','没有采纳反对意见')],when='956年南唐拒周部署时，具体上书日未载',place='南唐朝廷',note='亲王元帅可信为韩熙载观点，不表明本段已经废除监军。')
add('pan_recruits_recommends_generals','李璟派潘承祐到泉建募兵，潘举荐许文稹等四人',20,'遣鸿胪卿潘承祐','郑彦华、林仁肇。',[('唐主','派潘承祐召募骁勇'),('潘承祐','到泉建募兵并举荐四人'),('许文稹','以前永安节度使身份被荐'),('陈德诚','以静江指挥使身份被荐'),('郑彦华','以建州人身份被荐'),('林仁肇','以建州人身份被荐')],when='956年三月南唐扩充兵力期间，具体日未载',place='泉州、建州',note='被荐和实际任将分开，后句只明确许及郑林获任，不自动给陈德诚同一将号。')
add('xu_zheng_lin_appointed','李璟任许文稹为西面行营应援使，郑彦华、林仁肇为将',20,'唐主以文稹','皆为将。',[('唐主','任命应援使和将领'),('许文稹','任西面行营应援使'),('郑彦华','获任将领'),('林仁肇','获任将领')],when='956年三月潘承祐举荐之后，具体日未载',place='南唐')
relationship('林仁翰','林仁肇','兄长',20,'仁肇，仁翰之弟也。','原文明示林仁肇为林仁翰之弟，按方向约定林仁翰是林仁肇的兄长。')
add('zhou_april_commands','柴荣任李重进为庐寿招讨使、武行德为濠州城下都部署',21,Q[21]['text'],None,[('帝','调整淮南行营职务'),('李重进','以侍卫新军都指挥使、归德节度使身份任庐寿招讨使'),('武行德','以武宁节度使身份任濠州城下都部署')],when='956年四月甲子',place='庐寿及濠州战区')
sup('zhou_april_commands',21,old,'夏四月甲子，以徐州節度使武行德為濠州城下行營都部署，','《旧五代史》同日记武行德任濠州行营都部署，称徐州节度使。','徐州与武宁地名军额详略保留；旧句未列李重进，不擅自补入。')
add('lumengjun_recovers_taizhou','陆孟俊率万余兵从常州赴泰州，周军退去，陆复城并派陈德诚守',22,'唐右卫将军','遣陈德诚戍泰州。',[('陆孟俊','以南唐右卫将军身份领兵恢复泰州'),('陈德诚','被派戍守泰州')],when='956年四月淮南反攻时，具体日未载',place='常州至泰州',note='本段追述陆孟俊在951年废立楚王的经历，确认他与早年楚将为同一人；此次夺回与二月韩令坤初取泰州是不同阶段。')
sup('lumengjun_recovers_taizhou',22,old,'時李景乘常州之捷，遣陸孟俊領兵迫泰州，王師不守，','《旧五代史》同记南唐乘常州获胜派陆孟俊逼泰州，周军未能守住。','同一人和同次反攻补证；旧书将常州获胜归于陆，主书此前详叙柴，两书归功差别保留，不另造第二场常州战。')
add('han_reenters_yangzhou_with_relief','陆孟俊进扬州，韩令坤弃城出走，张永德援军使韩回城',22,'孟俊进攻扬州，','令坤复入扬州。',[('陆孟俊','进攻扬州、屯蜀冈'),('韩令坤','出走后回到扬州'),('帝','派张永德救援'),('张永德','奉命领兵援韩')],when='956年四月泰州恢复之后',place='扬州、蜀冈',note='出走与重返分开，不写成韩从此永久失城。')
add('zhaokuangyin_det ers_retreat'.replace(' ',''),'柴荣派赵匡胤屯六合，赵下令禁止扬州兵越六合退走',22,'帝又遣太祖皇帝','始有固守之志。',[('帝','派兵屯六合'),('太祖皇帝','以越过六合则折足的命令阻止退兵'),('韩令坤','受到约束后形成固守意志')],when='956年四月扬州受到反攻时',place='六合与扬州',note='折足是威胁性的军令，本段没有具名执行案件，不新增实际断足伤亡。')
sup('zhaokuangyin_deters_retreat',22,song,'太祖下令曰：「揚州兵敢有過六合者，斷其足。」令坤始固守。','《宋史》同记断足军令及韩令坤开始固守。','虽叙结果，不等于已经对全部逃兵执行断足，保留命令与实际执行证据的区别。')
add('shouchun_rain_logistics_crisis','寿州久攻不下，大雨使军营受淹、损失增多、粮运中断，周军议回师',22,'帝自至寿春以来，','乃议旋师。',[('帝','因攻城和后勤困境商议回师')],when='956年四月己巳离寿春之前',place='寿春周军营',description='周军昼夜攻城仍未取寿州，又遇大雨、营水数尺，攻具和士卒失亡较多、粮运不继，李德明也未按期回报，因此商议回师。失亡包含丢失、失散或死亡的概述，未直接等同精确阵亡数，李德明失期不至不写为他故意失约。')
add('chairong_moves_to_haozhou','柴荣采纳去濠州并声称寿州已破的建议，沿淮东行',22,'或劝帝东幸濠州，',None,[('帝','采纳东移建议，离寿春到濠州')],when='956年四月己巳离寿春，乙亥到濠州',place='寿春循淮至濠州',note='寿州已破是建议中的对外说辞，当时实际尚未攻下，不能在事件标题写周军已攻寿州。')
sup('chairong_moves_to_haozhou',22,old,'己巳，車駕發壽春，循淮而東。','《旧五代史》同记己巳沿淮东行离寿春。','出发和到濠州是两日，不合并作当天抵达。')
sup('chairong_moves_to_haozhou',22,old,'乙亥，駐蹕於濠州城下。','《旧五代史》同记乙亥驻濠州城下。','称驻城下不是已经取得城池。')

add('lumengjun_captured_yangzhou','韩令坤在扬州城东击败南唐军，俘陆孟俊',23,'韩令坤败唐兵','擒陆孟俊。',[('韩令坤','在扬州城东获胜并俘主将'),('陆孟俊','被韩令坤俘获')],when='956年四月，主书未单列战日，旧史丁丑奏报',place='扬州城东')
sup('lumengjun_captured_yangzhou',23,old,'丁丑，揚州韓令坤破江南賊軍於州之東境，獲大將陸孟俊。','《旧五代史》记丁丑韩令坤奏报扬州东境获胜、俘陆孟俊。','纪日为本纪记录战果，未强代主书实际交战日；同人合并证据由本段追述衔接951既往。')
add('lumengjun_yang_family_old_crime','《通鉴》追述陆孟俊参与废立时杀杨昭恽家族、夺财并献族女',23,'初，孟俊之废','献于希崇。',[('陆孟俊','参与旧楚废立时杀家族取财，并把族女献马希崇'),('杨昭恽','曾任舒州刺史，家族被害'),('杨氏（杨昭恽族女）','家族遭害后被献给马希崇'),('马希崇','接收杨氏族女')],year=951,when='951年楚国废马希萼、立马希崇之际的追述，具体日未载',place='潭州',note='主段将当时南唐陆与951楚将经历明确衔接，构成同人证据。这里记录此前未入库的灭族夺财，不重建已发布废立事件。')
add('ma_gives_yang_to_han','韩令坤入扬州后，马希崇把杨氏送给韩令坤，韩宠爱她',23,'令坤入扬州，','令坤嬖之。',[('马希崇','将杨氏送给韩令坤'),('韩令坤','接收并宠爱杨氏'),('杨氏（杨昭恽族女）','在扬州被转送韩令坤')],when='956年二月扬州入城之后的追述，具体日未载',place='扬州',note='遗在此是给予而非遗弃死亡，不擅定法定婚姻名分。')
add('yang_requests_revenge','陆孟俊被俘将送行在时，杨氏哭诉家仇，请韩令坤复仇',23,'既获孟俊，','请复其冤。”',[('陆孟俊','原拟被押送柴荣行在'),('杨氏（杨昭恽族女）','哭诉家族二百口被杀，请求复仇'),('韩令坤','询问并听取哭诉')],when='956年四月扬州俘陆以后',place='扬州',note='二百口是杨氏陈述，不记成已独立验证的精确家族人口；计划械送不等陆已到柴荣处。')
add('han_executes_lumengjun','韩令坤听取杨氏哭诉后杀死陆孟俊',23,'令坤乃杀之。',None,[('韩令坤','在听取哭诉后杀陆孟俊'),('陆孟俊','被俘后遭杀害')],when='956年四月扬州俘获后，具体处死日未载',place='扬州',note='由韩令坤处死，不写成柴荣已经审案下诏处死；同人稳定key沿951原档。')
claim('person',people['陆孟俊'],'death_year','陆孟俊于956年扬州战败被俘后，被韩令坤杀死。',23,'令坤乃杀之。','死亡承接同人及本段上下文，未强定丁丑为死日，原档案其他字段不覆盖。')
add('qiwang_camps_near_liuhe','南唐齐王景达率二万兵渡江，在六合二十余里处筑栅不进',24,'唐齐王景达','设栅不进。',[('景达','领兵渡江后设栅驻军')],when='956年四月六合战前，具体渡江日未载',place='瓜步济江至六合附近',note='二十余里为史载相对距离，不确定现代营地坐标。')
add('zhaokuangyin_waits_for_attack','赵匡胤因兵不满二千，主张等待南唐军出栅来攻',24,'诸将欲击之，','破之必矣！”',[('太祖皇帝','拒立即攻栅，决定等待来攻')],when='956年四月两军相对时',place='六合',note='惧我及破之必矣是赵匡胤判断，不作对方恐惧已被测量或战果保证。')
add('liuhe_victory','南唐军数日后来攻六合，赵匡胤反击获胜，败军渡江多人溺亡',24,'居数日，',None,[('太祖皇帝','击败来攻的南唐军')],when='956年四月设栅对峙数日后，具体战日未列',place='六合至渡江处',description='南唐兵数日后出栅攻六合，赵匡胤奋击取胜。《通鉴》记杀俘近五千，余众万余逃江争舟，多人溺亡，并以精卒尽作败势概述。旧史记斩首五千，《宋史》记斩首万余，杀俘与斩首口径不同且人数有差，不加总，也不推定南唐从此完全没有军队。')
sup('liuhe_victory',24,old,'今上表大破江南軍於六合，斬首五千級。','《旧五代史》记赵匡胤奏报六合获胜、斩首五千。','今上为宋太祖，主书记杀获近五千，斩首与杀俘统计范围不同，保留各书措辞。')
sup('liuhe_victory',24,song,'太祖尋敗齊王景達於六合東，斬首萬餘級。','《宋史》记六合东击败齐王景达，斩首万余。','与旧五千及主杀俘近五千人数口径并列，未据后出史改原主书。',relation='conflicts')

reviews={17:'甲寅后蜀十军组织、李廷珪总领吕彦琦为使，赵廷隐为旧任类比非当日新任人；姓氏李吕张不混。',18:'宣巡旧修城year null，三人旧叛为官吏借口，乙卯路退、柴升奉化请救与未至卒分开，死时地点无独立细记不虚补。',19:'忧北汉是白判断，修守求援、王先拒后自行到、白以无诏拒纳、孟洛受扰分阶段，不写北汉已攻河阳。',20:'齐王景达复徐景达同谱系，不新建李景达；陈监军和韩反对、潘招募荐四人、实际许郑林任职分开，林仁翰兄长方向明确，陈未同句获将号。',21:'四月甲子两军职任命，旧徐州武宁称法保留，侯章其他补书信息不强当主已列任命。',22:'陆孟俊同人合并有本段下一段951经历衔接，泰复城陈守、扬州韩退与张援、赵屯六合禁退军令、寿雨粮断与议撤、己巳走乙亥到濠分开。已破寿州是说辞非战果。',23:'同人明确追述951废立，旧犯罪未在前批录到故补当前主体事实；杨氏称谓不实名，二百口为哭诉，不造精数。俘陆、拟送、诉冤与韩杀分开，不写帝诏杀。',24:'两万敌军与不足两千周兵为史载，设栅等待与数日后来攻胜败分阶段。近五千杀获、旧斩五千、宋斩万余及溺死口径分别保留，精卒尽为败势概述非全唐零兵。'}
assert not (P/'publication.json').exists()
for n in range(17,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=293,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原22—29行连续八段，从蜀十军至六合战，含旧事和无独立死时的后续；以后段落不计。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],source_issues_review='陆孟俊同人已修订合并，证据、守卫、匿名回查见content/revisions/2026-10-06-lu-mengjun-identity；景达同人复用徐景达。六合三书人数口径并列，柴未至卒无确时不虚定地。杨昭恽与类似姓名不强合，女子姓名未载用称谓。',plain_language_review='首次逐条检查动作、人物、时间和解释，军令威胁与执行、寿州已破说辞与真实战果、家仇哭诉与清点、同人复用及兄弟方向明确，原文不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
