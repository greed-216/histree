# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 942 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,41))
specs=[(d.name,d,'d7e9f7a7ea4b22cbbe6d05277dd5c16ed51a9e06','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-098-zongcheng','xinwudaishi-051-zongcheng']:
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
main_sources = ['tongjian-283-942-spring']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0942-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-942-spring':'卷283·天福七年春季','jiuwudaishi-080-942-january':'卷80·晋高祖本纪·天福七年正月','xinwudaishi-068-min-li-empress':'卷68·闽世家·王延羲妻李氏','xinwudaishi-074-chen-yanhui':'卷74·四夷附录·陈延晖赴凉州'}
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
for n in range(1, 9):
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
    labels={'tongjian-283-942-spring':'卷283·天福七年春季','jiuwudaishi-080-942-january':'卷80·晋高祖本纪·天福七年正月','xinwudaishi-068-min-li-empress':'卷68·闽世家·王延羲妻李氏','xinwudaishi-074-chen-yanhui':'卷74·四夷附录·陈延晖赴凉州'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月至三月条下及追述'
        citation = f'卷283·后晋天福七年（942；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0942_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=942, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='942年年初条下，具体日期未载'
    key = 'event_zztj_283_0942_' + code
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
        edge = 'participation_zztj_283_0942_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0942_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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

ALIASES.update({'唐主':'李昪','帝':'石敬瑭','曦':'王延羲','真':'李真','璟':'李璟','寿王景遂':'徐景遂','景遂':'徐景遂','丁审琪':'丁审琦'})
NEW_DESCRIPTIONS={
'王瑜':'范阳人，后晋卫尉少卿。942年杜重威奏请让他任副使；《资治通鉴》记他为杜重威向恒州百姓重征赋税。生卒年未载。',
'张铎':'后晋张式的父亲。942年到朝廷为儿子申冤。生卒年未载。',
'李氏（王延羲后）':'闽国同平章事李真的女儿，王延羲的妻子。942年被立为皇后。《资治通鉴》和《新五代史》都记她嗜酒，性格强硬。姓名及生卒年未载。',
'贺行政':'延州军校。942年年初与胡人联合作乱，进攻延州。生卒年未载。',
'何重建':'后晋曹州防御使，云州、朔州一带胡人。942年受命援救延州，二月被任命为彰武留后。生卒年未载。',
'夏昌图':'宋齐丘身边的亲近吏员。《资治通鉴》942年条下记他盗用官钱三千缗，宋齐丘准免死刑，李昪愤怒并杀死他。生卒年月未载。',
'陈延晖':'泾州押牙。《资治通鉴》942年条下记他持敕书前往凉州，当地将吏请求让他任节度使。《新五代史》记他被留下并立为刺史，连叙纪年有异。生卒年未载。'}
NEW_ALIASES={'王瑜':[],'张铎':['張鐸'],'李氏（王延羲后）':[],'贺行政':['賀行政'],'何重建':[],'夏昌图':['夏昌圖'],'陈延晖':['陳延暉','陈延暉']}
old='jiuwudaishi-098-zongcheng';new='xinwudaishi-051-zongcheng';ann='jiuwudaishi-080-942-january';minsrc='xinwudaishi-068-min-li-empress';west='xinwudaishi-074-chen-yanhui'
add('zhenzhou_gate_open','镇州牙将从西郭水碾门引官军进城',1,'春，正月，','导官军入城，',[],when='942年正月丁巳',place='镇州',note='牙将未具名，不因旧史提立功王温便认定是同一导军者。')
add('jin_kills_zhenzhou_defenders','官军入镇州后，史书记杀死守城百姓两万人',1,'杀守陴民','二万人，',[],when='942年正月丁巳',place='镇州',note='数字为史书记载，《旧五代史》人数不同，分别引用，不与941年战死冻死者相加。')
sup('jin_kills_zhenzhou_defenders',1,old,'殺守陴百姓萬餘人，','《旧五代史》记入镇州后杀死守城百姓一万多人。','两万人与一万多人存在差异，保留各书记载，不取平均数或相加。',relation='conflicts')
add('an_captured_executed','官军捕获安重荣并将他斩首',1,'执安重荣，','斩之。',[('安重荣','被捕后遭斩首'),('杜重威','所率官军捕杀安重荣')],when='942年正月丁巳',place='镇州')
sup('an_captured_executed',1,old,'重榮擁吐渾數百，匿於牙城，重威使人襲而得之，斬首以進。','《旧五代史》补记安重荣与数百吐谷浑部众藏在牙城，杜重威派人袭击并捕获他，斩首呈报。','与同次攻镇州相连，牙城藏匿和捕获细节独立注明。',relation='adds')
sup('an_captured_executed',1,ann,'北面招討使杜重威奏，今月二日收復鎮州，斬安重榮，傳首闕下。','《旧五代史》本纪记杜重威奏报正月初二收复镇州，斩安重荣并传首朝廷。','本纪将奏报列在戊午条下，今月二日为战事发生日，不把奏报日当捕杀日。')
sup('an_captured_executed',1,new,'重榮以吐渾數百騎守牙城，重威使人擒之，斬首以獻，','《新五代史》也记安重荣与数百吐谷浑骑兵守牙城，杜重威派人捕获他并献首。','捕获处死为同一事件，不另造第二次死亡。')
add('du_kills_gate_guide','杜重威杀死引军进城的人，把攻城功劳归于自己',1,'杜重威杀导者，','自以为功。',[('杜重威','杀死导军者并独占功劳')],when='942年正月镇州被攻克后，具体日期未载',place='镇州',note='导军者未具名，杀人理由按史书记述，不建立未经证实的私人仇怨。')
add('an_head_reaches_yedu','安重荣首级送到邺都，石敬瑭命涂漆装匣送往契丹',1,'庚申，',None,[('帝','命把首级涂漆装匣送往契丹'),('安重荣','死后首级被送到邺都并转送契丹')],when='942年正月庚申',place='邺都',note='此日是首级到邺都和帝命发送，不等于已到契丹。')
add('rename_zhenzhou_hengzhou','后晋将镇州改称恒州，成德军改称顺国军',2,'癸亥，',None,[],when='942年正月癸亥',place='恒州')
sup('rename_zhenzhou_hengzhou',2,ann,'癸亥，改鎮州為恒州，成德軍為順國軍。','《旧五代史》同记正月癸亥改州名和军名。','同一更名，繁简字形保留在摘录中。')
sup('rename_zhenzhou_hengzhou',2,new,'改成德軍為順德，鎮州曰恆州，常山曰恆山云。','《新五代史》记镇州改恒州，常山改恒山，成德军改称顺德。','军号顺德与通鉴、旧史顺国有异，独立保留，不把同日更名拆成两次；常山更名是新史补充。',relation='conflicts')
add('zhao_ying_shizhong','石敬瑭任赵莹为侍中',3,'丙寅，','赵莹为侍中，',[('帝','任赵莹为侍中'),('赵莹','由门下侍郎、同平章事升侍中')],when='942年正月丙寅')
add('du_shunguo_commission','石敬瑭任杜重威为顺国节度使兼侍中',3,'以杜重威','兼侍中。',[('帝','任杜重威为顺国节度使兼侍中'),('杜重威','获任顺国节度使兼侍中')],when='942年正月丙寅',place='恒州')
add('du_takes_an_assets','杜重威占有安重荣私财和恒州府库，石敬瑭知道却不追问',3,'安重荣私财','帝知而不问。',[('杜重威','占有安重荣私财及恒州府库'),('帝','知情而不追问')],when='942年正月恒州授职条下，具体日期未载',place='恒州',note='占有范围为史书记述，不补具体财物金额。')
add('du_recommends_wang_yu','杜重威奏请让王瑜担任副使',3,'又表卫尉','为副使，',[('杜重威','奏请王瑜任副使'),('王瑜','获杜重威奏请任副使')],when='942年正月条下，具体日期未载',place='恒州',note='表为奏请，不补同日已有正式授官诏令。')
add('wang_yu_heavy_taxes','王瑜为杜重威向恒州百姓重征赋税，百姓难以承受',3,'瑜为之',None,[('王瑜','为杜重威重征赋税'),('杜重威','王瑜为其向百姓重征')],when='942年恒州授职后，具体日期未载',place='恒州',note='百姓不堪其苦为史书描述，不补税率或所有户数。')
add('zhang_duo_appeals','张铎到朝廷为儿子张式申冤',4,'张式父','讼冤。',[('张铎','到朝廷为儿子申冤'),('张式','父亲为其向朝廷申冤')],when='942年正月条下，具体日期未载',note='父名铎承接张式姓氏，不误认张式本人到朝廷。')
relationship('张铎','张式','父亲',4,'张式父鐸诣阙讼冤。','张铎是张式的父亲；父名铎及姓氏依据本句。')
add('wang_zhou_zhangyi','石敬瑭任王周为彰义节度使，接替张彦泽',4,'壬午，',None,[('帝','调王周接替张彦泽'),('王周','由河阳节度使调任彰义节度使'),('张彦泽','彰义节度使职位被王周接替')],when='942年正月壬午',place='泾州',note='彰义军在泾州；旧史同日写泾州节度使，保留职名。')
sup('wang_zhou_zhangyi',4,ann,'壬午，以河陽節度使王周為涇州節度使，','《旧五代史》同记壬午把王周从河阳调到泾州。','军号与州名表达不同，没有另造第二次调任。')
add('min_li_empress','王延羲立李氏为皇后',5,'闽主曦','同平章事真之女也；',[('曦','立李氏为皇后'),('李氏（王延羲后）','被立为闽皇后')],when='942年正月条下，具体日期未载',place='闽国')
relationship('真','李氏（王延羲后）','父亲',5,'闽主曦立皇后李氏，同平章事真之女也；','真承接同平章事李真，李真是皇后李氏的父亲。')
relationship('李氏（王延羲后）','曦','妻子',5,'闽主曦立皇后李氏，同平章事真之女也；','李氏是王延羲的妻子；不与王继鹏元妃李氏合并。')
claim('person',people['李氏（王延羲后）'],'biography','《资治通鉴》记李皇后嗜酒、性格强硬，王延羲宠爱她，也有所畏惧。',5,'嗜酒刚愎，曦宠而惮之。','这是史书的人物描述，不扩为诊断或虚构具体冲突。')
claim('person',people['李氏（王延羲后）'],'biography','《新五代史》也记王延羲的妻子李氏性格强硬、嗜酒。',5,'曦性既淫虐，而妻李氏悍而酗酒，','只引用妻李氏的描述，后续政变叙事尚未处理，不提前定死亡年。',source=minsrc,relation='corroborates')
add('ding_retinue_abuse','丁审琦养部众千人，纵容他们在辖境作恶',6,'彰武节度使','为暴于境内；',[('丁审琪','养部众千人并纵容其作恶')],year=None,when='丁审琦任彰武节度使期间，延州受攻前，具体年月未载',place='延州',note='部众千人为史载数量；丁审琪与已有丁审琦按旧史同时期延州职务及姓名异字对应，不新建同人。')
claim('person',people['丁审琦'],'description','《旧五代史》942年正月本纪称延州节度使丁审琦。',6,'壬申，延州節度使丁審琦加爵邑，','该职务与通鉴彰武节度使对应，琦与琪的字形差异保留，复用既有人物。',source=ann)
add('he_xingzheng_attacks','贺行政与胡人联合作乱，进攻延州',6,'军校贺行政','攻延州，',[('贺行政','与胡人联合起兵进攻延州')],when='942年二月任留后以前，具体日期未载',place='延州',note='胡人未具名，不推具体族群或盟约。')
add('he_chongjian_rescue','石敬瑭派何重建援救延州，同州和鄜州援兵随后到达',6,'帝遣曹州','乃得免。',[('帝','派何重建援救延州'),('何重建','率军援救延州')],when='942年二月任留后以前，具体日期未载',place='延州',note='援军到达后延州解围，不补未载战损与援兵人数。')
add('he_chongjian_stays_ding_recalled','石敬瑭任何重建为彰武留后，召丁审琦回朝',6,'二月，','召审琪归朝。',[('帝','任何重建留后并召丁审琦回朝'),('何重建','获任彰武留后'),('丁审琪','被召回朝廷')],when='942年二月癸已',place='延州',note='底本癸已疑已巳字误，保留原字并等待版本核对，不伪称已校定干支。')
claim('person',people['何重建'],'biography','《资治通鉴》称何重建是云州、朔州一带的胡人。',6,'重建，云、朔间胡人也。','保留原文族属概称，不自行细分民族。')
add('song_enters_zhongshu','宋齐丘坚持请求参与政务，李昪准许他进中书省',6,'唐左丞相','唐主听入中书；',[('宋齐丘','坚持请求参与政务'),('唐主','准许宋齐丘进入中书省')],when='942年二月条下，具体日期未载',place='南唐')
add('song_heads_shangshu','宋齐丘请求主管尚书省，李昪调整李景遂分工并任宋齐丘主管',6,'又求领尚书省，','以齐丘知尚书省事；',[('宋齐丘','请求并获准主管尚书省'),('唐主','调整三省主管分工'),('寿王景遂','不再主管尚书省，改主管中书门下省')],when='942年宋齐丘进入中书省后，具体日期未载',place='南唐',note='复用已有徐景遂稳定人物，时期称李景遂；改姓不另建人物。')
add('li_jing_reviews_three_departments','李昪让齐王李璟参与决定三省事务',6,'其三省事', '取齐王璟参决。',[('唐主','规定三省事务由李璟参与决定'),('璟','参与决定三省事务')],when='942年三省分工调整时，具体日期未载',place='南唐')
add('xia_steals_public_money','夏昌图盗用官钱三千缗',6,'齐丘视事数月，','盗官钱三千缗，',[('夏昌图','盗用官钱三千缗')],year=None,when='宋齐丘主管尚书省数月后，确切年月未载',place='南唐',note='数月后不继续写作二月同日；三千缗为原文金额，不换算现代货币。')
add('song_spares_xia','宋齐丘裁定免去夏昌图死刑',6,'齐丘判','贷其死；',[('宋齐丘','裁定免夏昌图死刑'),('夏昌图','得到宋齐丘免死裁定')],year=None,when='夏昌图盗官钱被处理时，确切年月未载',place='南唐')
add('li_bian_executes_xia','李昪愤怒，处死夏昌图',6,'唐主大怒，','斩昌图。',[('唐主','因宋齐丘免死裁定愤怒并处死夏昌图'),('夏昌图','被李昪处死')],year=None,when='宋齐丘裁定免死后，确切年月未载',place='南唐',note='记录死亡事实而不强填942年死亡字段。')
add('song_resigns_department','宋齐丘称病请求卸去尚书省事务，李昪同意',6,'齐丘称疾，',None,[('宋齐丘','称病请求卸去尚书省事务'),('唐主','准许宋齐丘辞去省务')],year=None,when='夏昌图被处死后，确切年月未载',place='南唐',note='称疾为宋齐丘的说法，不独立证明疾病或推已离开全部政务。')
add('chen_yanhui_goes_liangzhou','泾州奏报派陈延晖持敕书前往凉州',7,'泾州奏遣','诣凉州，',[('陈延晖','以泾州押牙身份持敕书前往凉州')],when='942年二月条下，具体派遣及奏报日期未载',place='凉州',note='奏为泾州报告，未补报告人姓名或宣称已获中央节度使任命。')
add('liangzhou_requests_chen','凉州将吏请求让陈延晖任节度使',7,'州中将吏',None,[('陈延晖','被凉州将吏请求任节度使')],when='942年陈延晖到凉州后，具体日期未载',place='凉州',note='地方请求与朝廷正式授官不同，未载本次批准。')
sup('liangzhou_requests_chen',7,west,'明年，晉高祖遣涇州押牙陳延暉賫詔書安撫涼州，涼州人共劫留延暉，立以為刺史。','《新五代史》记陈延晖持诏书安抚凉州，被当地人强留下来，立为刺史。','新五代史先列天福七年、继称明年，却仍称晋高祖；与通鉴942年条下时间不合，保留连叙问题。刺史与主书节度使请求分别引用，不擅改原文或另造同名人物。',relation='conflicts')
add('wang_yacheng_min_king','王延羲将长乐王王亚澄改封为闽王',8,'三月，',None,[('曦','改封王亚澄为闽王'),('王亚澄','由长乐王改封闽王')],when='942年三月，具体日期未载',place='闽国',note='闽王封号不等于继位为闽皇帝，不提前后续政治结果。')
claim('person',people['安重荣'],'death_year','安重荣于942年正月丁巳在镇州被捕后斩首。',1,'春，正月，丁巳，镇州牙将自西郭水碾门导官军入城，杀守陴民二万人，执安重荣，斩之。','死亡事实独立引用；既有主体基础字段本批不覆盖。')
reviews={1:'镇州导军、杀守城百姓、捕杀安重荣、杜重威杀导军者及首级转送分开；通鉴两万人与旧史一万多人保留；旧纪奏报与事日分开。',2:'癸亥州名军名改变有旧纪补证，不虚构迁城或军队人数。',3:'丙寅两任命与财产占有、奏荐王瑜、重征赋税分录，奏荐不当明确诏准。',4:'张铎申冤及父亲方向明确；壬午王周彰义与旧泾州同次调任，不提前张彦泽后罪。',5:'李氏为李真女、王延羲妻，独立限定主体；人物评价分别引用，不提前新史后续政变。',6:'丁部众暴行为前背景；贺行政攻延、何援兵及癸已任留后分开；琪与琦复用已存人物，癸已保原字待核。宋齐丘进中书、三省分工及李璟参决与数月后盗钱、免死、处死、辞省分期，后追叙年月未明为空。',7:'陈延晖持敕与凉州将吏请任分开，未写朝廷已批准；新史连叙纪年及刺史与节度使请求差异保留。',8:'三月王亚澄由长乐王改封闽王，不作皇帝继位。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=283,year=942,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第1—8段，原6—13行；正月至三月及相关追述。后接本年张彦泽在泾州行为第9段，全年40正文尚未完成。',source_issues_review='镇州守城百姓死亡人数、癸已字形、陈延晖赴凉州连叙纪年及职衔有异，原文保留；所用电子本纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],plain_language_review='首次逐条核对标题、人物身份、参与动作、亲属方向、时间及引用解释，展示现代白话；追述与数月后事件不硬定同一月日。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
