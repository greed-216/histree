# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 943 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,43))
COMMIT='0bf9f2cc5934c50fb020b79750ac51ac7d48f541'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

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
main_sources = ['tongjian-283-943-early-a','tongjian-283-943-early-b']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0943-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-early-a':'卷283·后晋天福八年·正月至二月及追述','tongjian-283-943-early-b':'卷283·后晋天福八年·二月至四月及追述','jiuwudaishi-081-943-return':'卷81·晋少帝本纪·天福八年二月','xinwudaishi-009-943-return':'卷9·晋出帝本纪·天福八年','xinwudaishi-062-li-bian-death':'卷62·南唐世家·升元七年李昪去世','xinwudaishi-062-feng-name':'卷62·南唐世家·冯延巳等','xinwudaishi-068-yin-founded':'卷68·闽世家·王延政建殷','xinwudaishi-062-jing-brothers':'卷62·南唐世家·李璟与诸弟'}
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
    labels={'tongjian-283-943-early-a':'卷283·后晋天福八年·正月至二月及追述','tongjian-283-943-early-b':'卷283·后晋天福八年·二月至四月及追述','jiuwudaishi-081-943-return':'卷81·晋少帝本纪·天福八年二月','xinwudaishi-009-943-return':'卷9·晋出帝本纪·天福八年','xinwudaishi-062-li-bian-death':'卷62·南唐世家·升元七年李昪去世','xinwudaishi-062-feng-name':'卷62·南唐世家·冯延巳等','xinwudaishi-068-yin-founded':'卷68·闽世家·王延政建殷','xinwudaishi-062-jing-brothers':'卷62·南唐世家·李璟与诸弟'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月至二月条下及追述'
        citation = f'卷283·后晋天福八年（943；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0943_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=943, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='943年年初条下，具体日期未载'
    key = 'event_zztj_283_0943_' + code
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
        edge = 'participation_zztj_283_0943_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0943_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李昪','烈祖':'李昪','景达':'徐景达','李景达':'徐景达','景逷':'李景逷','宋后':'宋氏（南唐李昪后）','宋皇后':'宋氏（南唐李昪后）','种氏':'种氏（李昪妃）','冯延己':'冯延巳','冯延已':'冯延巳','延己':'冯延巳','延鲁':'冯延鲁','皇后张氏':'张氏（王延政后）'})
NEW_ALIASES={
'田敬全':[],'李景达':['景达','景達','李景達'],'李景逷':['景逷'],'种氏（李昪妃）':['种氏','種氏'],'史守冲':['史守沖'],'王栖霞':['王棲霞'],'冯延巳':['馮延巳','冯延己','馮延己','冯延已'],'魏岑':[],'萧俨':['蕭儼'],'吴廷裕':['吳廷裕'],'李贻业':['李貽業'],'冯延鲁':['馮延魯'],'杨思恭':['楊思恭'],'张氏（王延政后）':['张氏（殷国后）','張氏（王延政后）']}
NEW_DESCRIPTIONS={
'田敬全':'后蜀宦官，任宣徽使兼宫苑使。943年正月癸卯，孟昶任命他兼领永平节度使。史书记载这项任命受到非议。生卒年未载。',
'李景达':'李昪之子，南唐宣城王。李昪曾多次想让他继承帝位，宋齐丘赞扬他的才干，但李昪因李璟年长而放弃这一打算。具体年月及生卒年尚未核。',
'李景逷':'李昪的幼子，母亲为种氏。种氏曾建议让他继承帝位，李昪拒绝了这一建议。具体年月及生卒年尚未核。',
'种氏（李昪妃）':'李昪的妃嫔，李景逷的母亲。史书记载她受到宠爱，曾建议立幼子为继承人；李昪拒绝后，下令将她嫁给他人。具体年月、生卒年和后来配偶未载。',
'史守冲':'向南唐李昪献丹方的方士。史书将李昪的梦境、服丹及此后躁急的表现连叙；梦境为史载叙述，不据此作医学或神异判断。具体年月及生卒年未载。',
'王栖霞':'南唐道士，曾劝李昪先修养自己的心性与行为，再谈治理国家。他拒绝李昪的赏赐，也以国用不足为由拒绝为自己建坛。具体年月及生卒年未载。',
'冯延巳':'南唐官员，曾任驾部郎中、齐王元帅府常书记。《资治通鉴》本段作冯延己及延已，《新五代史》作冯延巳；据同一南唐政局、陈觉及常梦锡等对应关系校核为同人，展示采用冯延巳，原文异体保留。生卒年尚未核。',
'魏岑':'南唐齐王府僚属。李昪在位时，常梦锡曾反对他与陈觉、冯延巳等陪侍李璟。生卒年尚未核。',
'萧俨':'南唐官员，943年开篇记为司门郎中、判大理寺。曾指责陈觉，又反对冯延巳兄弟所草允许卖子女的遗诏，说明李昪先前对此的处理。生卒年尚未核。',
'吴廷裕':'南唐太医。943年二月庚午，李昪病危时，他派亲信召李璟入宫侍疾。生卒年尚未核。',
'李贻业':'南唐翰林学士。李昪去世后，他反对孙晟借遗诏名义让太后临朝的打算，孙晟因此停止。《资治通鉴》还记他是李蔚的从曾孙，具体支系尚未核。生卒年未载。',
'冯延鲁':'冯延巳的弟弟，南唐官员，曾任东都判官、礼部员外郎，与兄长同在元帅府。曾请求允许百姓卖子女；李昪去世后又参与起草包含这一规定的遗诏。生卒年尚未核。',
'杨思恭':'建阳人，王延政属下的节度巡官。943年王延政建殷后任兵部尚书，不久升仆射、录军国事。史书记他加重田亩山泽及鱼盐蔬果税负，记载当时人称他为杨剥皮。生卒年尚未核。',
'张氏（王延政后）':'王延政的妻子。943年王延政在建州称帝建立殷国时，立她为皇后。个人名字与生卒年未载。'}
# 1–2: contemporary appointments and travel; independent annals supplement the same journey.
add('tian_jingquan_yongping','孟昶任命宦官田敬全兼领永平节度使，受到非议',1,'春，',None,[('蜀主','任命田敬全兼领永平节度使'),('田敬全','由宣徽使兼宫苑使兼领永平节度使')],when='943年正月癸卯',place='后蜀',note='引前蜀王承休作比较是任命理由，不将王承休列为本次任命的参与人；国人非之为史书记载的非议，不补具体反对者。')
claim('event',E['tian_jingquan_yongping'],'description','孟昶以此前前蜀任用王承休为例，任命宦官田敬全兼领节度使。',1,'敬全，宦者也，引前蜀王承休为比而命之，国人非之。','王承休是先例，并未在943年参与此事。')
add('shi_leaves_yedu','石重贵听说契丹将入侵，二月己未离开邺都',2,'帝闻','发鄴都；',[('帝','听到契丹将入侵的消息，离开邺都')],when='943年二月己未',place='邺都',note='将入寇是听到的消息，不补此日契丹已开战；鄴展示作邺，原文不改。')
add('shi_arrives_tokyo','石重贵二月乙丑抵达东京',2,'乙丑，','至东京。',[('帝','抵达东京')],when='943年二月乙丑',place='东京')
add('jin_khitan_monthly_gifts','后晋与契丹仍每月互通问候和赠礼',2,'然犹',None,[('帝','在与契丹的关系紧张时仍维持问候和赠礼')],when='943年二月条下，所概述的起止年月未载',year=None,note='无虚月为持续交往概述，不虚构每月使者或每月独立事件。')
old='jiuwudaishi-081-943-return';new='xinwudaishi-009-943-return'
sup('shi_leaves_yedu',2,old,'己未，車駕發鄴都，曲赦都下禁囚。','《旧五代史》也记二月己未离开邺都，并记赦免都下囚犯。','同一行程与干支，赦囚另立补充事件。')
sup('shi_arrives_tokyo',2,old,'乙丑，至東京。','《旧五代史》也记二月乙丑抵达东京。','到达日与通鉴相同。')
sup('shi_leaves_yedu',2,new,'己未，如東京，赦廣晉府囚。','《新五代史》记二月己未往东京，赦广晋府囚犯。','去东京不等于当天到达。')
sup('shi_arrives_tokyo',2,new,'乙丑，至自鄴都。','《新五代史》记二月乙丑自邺都抵达。','段落前文如东京确定到达地；保留原句。')
E['shi_yedu_prisoner_pardon']=event('shi_yedu_prisoner_pardon','石重贵离开邺都时赦免当地囚犯',2,'己未，車駕發鄴都，曲赦都下禁囚。',[('帝','离开邺都时赦免都下囚犯')],when='943年二月己未',place='邺都',source=old,note='旧纪为独立补充，范围限都下囚犯，不写成全国大赦。')
sup('shi_yedu_prisoner_pardon',2,new,'己未，如東京，赦廣晉府囚。','《新五代史》将赦囚范围写作广晋府。','都下与广晋府按各书记载保留，不据简称扩大为全国。')
E['shi_stops_fengqiu']=event('shi_stops_fengqiu','石重贵在封丘停留，百官到行宫参见',2,'甲子，次封丘，文武百官見於行宮。',[('帝','在封丘停留，接受百官参见')],when='943年二月甲子',place='封丘',source=old,note='这是抵达东京前一日的停留；不从旧纪其他任官及死亡记载跳录后文。')
# 3: retrospectively narrated succession proposals, court life and religious practices.
past=dict(year=None,when='李昪在位期间，具体年月未载',place='南唐')
add('bian_considers_jingda','李昪想让李景达继位，因李璟年长而放弃',3,'唐宣城王','而止。',[('唐主','多次想立李景达为继承人，最后因李璟年长而停止'),('景达','得到李昪喜爱，被考虑作为继承人'),('宋齐丘','多次赞扬李景达的才干'),('景通','因年长而成为李昪停止改立的理由')],note='屡欲是多次考虑，非正式立储或传位。刚毅开爽为史书人物评价，保留为描述，不作测评。',**past)
add('jing_resents_qiqiu','李璟因宋齐丘支持李景达而怨恨宋齐丘',3,'璟以是','怨齐丘。',[('景通','因宋齐丘赞扬李景达而怨恨他'),('宋齐丘','受到李璟怨恨')],**past)
add('bian_scolds_jing_music','李昪见李璟亲自调乐器，生气并连日责备他',3,'唐主如璟宫，','诮让者数日。',[('唐主','到李璟住处，见他调乐器而生气责备'),('景通','因亲自调乐器受到父亲责备')],note='璟宫只写李璟住处，不推确定城市或宫名；数日不补天数。',**past)
add('zhong_proposes_jingti','种氏建议让幼子李景逷继承帝位',3,'种氏乘间言，','可以为嗣。',[('种氏','借机提出让李景逷继位'),('景逷','被母亲建议作为继承人')],note='幼而慧为种氏提出建议的评价，不认作独立智力判断。',**past)
add('bian_rejects_zhong','李昪拒绝种氏干预继承人安排，下令将她嫁给他人',3,'唐主怒曰：','即命嫁之。',[('唐主','拒绝种氏建议，并下令将她嫁给他人'),('种氏','建议被拒后，被下令嫁给他人')],note='只载命嫁，没有对方身份和实际成婚日期，不补配偶。妇女不得知国事是李昪的话，非本站规范。',**past)
add('shi_shouchong_elixir','史守冲献丹方，李昪因梦境而相信并服丹',3,'唐主尝梦','浸成躁急。',[('唐主','史书称他梦见吞丹，次日受献丹方并服用'),('史守冲','在李昪梦境次日献丹方')],note='梦境是史载叙述；服丹与此后躁急只记书中叙述，不作医学诊断或确认梦境神效。',**past)
add('bian_ignores_elixir_advice','李昪不听身边人反对服丹的劝告',3,'左右谏，','不听。',[('唐主','没有听从身边人的劝告')],note='劝谏者未具名，不造人物。结合前句知所谏为服丹及变化。',**past)
add('jianxun_reports_elixir_effects','李建勋受赐丹药后，向李昪说服用数日已感到躁热',3,'尝以药赐','朕服之久矣。”',[('唐主','赐李建勋药，并说自己已经服用很久'),('李建勋','说服药数日已感到躁热，提醒多服可能有影响')],note='躁热为李建勋自身陈述；不推病因、药物成分或服用剂量。',**past)
add('bian_court_temper','李昪常在臣下奏事时发怒，但也接受合理的直言',3,'群臣奏事，','而从之。',[('唐主','常因奏事发怒，遇到合理直言时也会收敛并采纳')],note='长期政务行为概述，臣下未具名，不补具体奏章。',**past)
add('wang_qixia_self_cultivation','王栖霞劝李昪先修养自身再谈太平，宋皇后赞同',3,'唐主问道士','以为至言。',[('唐主','询问王栖霞怎样实现太平'),('王栖霞','劝李昪先修养自己的心性和行为再治理国家'),('宋后','在帘后称赞王栖霞的回答')],**past)
add('qixia_refuses_gifts','王栖霞拒绝李昪的赏赐',3,'凡唐主','栖霞皆不受。',[('唐主','向王栖霞赏赐财物'),('王栖霞','拒绝李昪的各项赏赐')],note='各项赏赐的具体财物、次数和金额未载。',**past)
add('qixia_refuses_altar','王栖霞以国用不足为由，拒绝李昪为他建坛',3,'栖霞常为人奏章，',None,[('唐主','想为王栖霞建坛'),('王栖霞','以国用不足为由拒绝建坛')],note='奏章、焚章为此处道教仪式语境，不能改作朝廷奏议；焚章不化为王栖霞所设说法，非已发生的神异现象。',**past)
relationship('唐主','景达','父亲',3,'唐宣城王景达，刚毅开爽，烈祖爱之，屡欲以为嗣；','同段景达与景逷、璟的继承人讨论，父子身份明确；不将继位打算写作已经传位。')
relationship('唐主','景逷','父亲',3,'唐主幼子景逷，母种氏有宠，','唐主为李昪，原文明确幼子。')
relationship('种氏','景逷','母亲',3,'唐主幼子景逷，母种氏有宠，','原文明确母亲；不从命嫁补后来的配偶。')
relationship('宋后','景通','母亲',3,'齐王璟母宋皇后稀得进见。','原文明确齐王李璟的母亲，复用已录宋氏主体。')
claim('person',people['徐景达'],'description','《新五代史》明确宣城王景达是李璟的弟弟。',3,'封弟壽王景遂為燕王，宣城王景達鄂王，','仅用于身份和支系核对，不提前录入本批之后的封王事件。',source='xinwudaishi-062-jing-brothers',relation='adds')
claim('person',people['种氏（李昪妃）'],'description','种氏受宠时，李璟的母亲宋皇后很少得到见李昪的机会。',3,'唐主幼子景逷，母种氏有宠，齐王璟母宋皇后稀得进见。','宠爱与进见频率是史载描述，不推未载的具体冲突或日期。')
# 4: court criticism, illness, death and announced regency.
add('feng_court_connections','冯延巳与宋齐丘、陈觉结交，逐渐排挤齐王府中职位更高的人',4,'驾部郎中','延己稍以计逐之。',[('冯延己','担任齐王府常书记，与宋齐丘、陈觉结交并排挤职位更高的人'),('宋齐丘','与冯延巳结交'),('陈觉','与冯延巳结交')],note='倾巧是史书评价；排挤对象未具名，不猜具体被逐者。在巳上按上下文指在自己之上，保留底本字形。',**past)
claim('person',people['冯延巳'],'description','《新五代史》将南唐的这位官员写作冯延巳。',4,'馮延巳','两书对应陈觉、常梦锡及同一南唐政局，校核为同人。后文其他任命留待连续段落，不提前录入。',source='xinwudaishi-062-feng-name',relation='adds')
add('sun_rebukes_feng','孙晟反驳冯延巳，要求他以仁义辅导李璟',4,'延已尝戏谓','适足为国家之祸耳。”',[('冯延己','戏问孙晟为何能任中书侍郎'),('孙晟','批评冯延巳应以仁义辅导齐王，而不是陪他享乐')],note='对话中的谄诈与祸国是孙晟的批评，不当作本站已证定性。',**past)
add('mengxi_warns_prince_staff','常梦锡反对让陈觉、冯延巳、魏岑陪侍李璟',4,'又有魏岑者，','不宜侍东宫；',[('魏岑','在齐王府任职，受到常梦锡批评'),('常梦锡','多次反对陈觉、冯延巳、魏岑陪侍齐王'),('陈觉','被常梦锡批评不宜陪侍齐王'),('冯延己','被常梦锡批评不宜陪侍齐王')],note='佞邪小人是常梦锡评价，齐王府与东宫为原文不同称谓，不自行推正式册太子日期。',**past)
add('xiao_yan_accuses_chen','萧俨上表指责陈觉乱政，李昪有所醒悟但未罢免',4,'司门郎中','未及去。',[('萧俨','任司门郎中、判大理寺，上表指责陈觉'),('陈觉','受到萧俨指责'),('唐主','有所醒悟，但尚未罢免被指责的人')],note='奸回乱政为萧俨上表指责；未及去不能写作已罢免。',**past)
add('bian_secret_illness','李昪背部长疽，保密医治，仍照常处理政务',4,'会疽发背，','听政如故。',[('唐主','背部长疽，秘密召医治疗，照常听政')],when='943年二月病危前，发病日期未载',place='南唐',note='疽为史书病名，不推现代诊断，医治者此句未具名。')
add('wu_calls_jing','李昪病危，吴廷裕派亲信召李璟入宫侍疾',4,'庚午，','召齐王璟入侍疾。',[('唐主','病情加重'),('吴廷裕','派亲信召齐王入宫侍疾'),('景通','被召入宫侍疾')],when='943年二月庚午',place='南唐',note='二月承接本年开篇行程后叙事；亲信未具名。')
add('bian_warns_jing_elixir','李昪临终劝李璟不要依靠金石药求长寿',4,'唐主谓璟曰：','汝宜戒之！”',[('唐主','说服金石本为延寿却伤生，劝李璟引以为戒'),('景通','听父亲临终劝告')],when='943年二月庚午',place='南唐',note='药物伤生为李昪自述，不据此单独确诊死亡原因。')
add('li_bian_dies','李昪二月庚午夜去世',4,'是夕，','殂。',[('唐主','在病危当晚去世')],when='943年二月庚午夜',place='南唐',note='是夕承接庚午；不把宣布遗诏的丙子误当死亡日。')
add('bian_death_withheld','南唐暂不公开李昪死讯',4,'秘不发丧，','秘不发丧，',[],when='943年二月庚午李昪去世后',place='南唐',note='处置者未具名，不自动认作李昪死后亲自下令。')
add('jing_regency_and_pardon','南唐宣布由李璟监国并实行大赦',4,'下制：',None,[('景通','按公布的制令监国')],when='943年二月庚午李昪去世后',place='南唐',note='监国与随后正式即位区分；此处制令发布者未具名，不据此让李昪死后发令。')
sup('li_bian_dies',4,'xinwudaishi-062-li-bian-death','七年，昪卒，年五十六，','《新五代史》记李昪升元七年去世，年五十六。','升元七年对应943年；年龄按史载保留，不反推精确出生年。',relation='adds')
claim('person',people['李昪'],'death_year','李昪于943年二月庚午夜去世。',4,'庚午，疾亟，太医吴廷裕遣亲信召齐王璟入侍疾。唐主谓璟曰：“吾饵金石，始欲益寿，乃更伤生，汝宜戒之！”是夕，殂。','复用人物基础字段保留原档案，死亡事实以独立引用补充。')
# 5–6: rejected regency proposal and proclamation; comments remain attributed.
add('sun_plans_empress_regency','孙晟担心冯延巳等掌权，想借遗诏名义让太后临朝',5,'孙晟恐','令太后临朝称制。',[('孙晟','因担心冯延巳等掌权，想借遗诏名义让太后临朝')],when='943年二月李昪去世后',place='南唐',note='欲称是未执行的打算，太后所指承接宋氏；不建立已经执政的事件。')
add('liyiye_blocks_regency','李贻业反对太后临朝的提议，孙晟停止这一打算',5,'翰林学士','晟惧而止。',[('李贻业','反对提议，表示若宣布将当着百官驳斥'),('孙晟','因李贻业反对而停止打算')],when='943年二月李昪去世后',place='南唐',note='李贻业引述先帝的话和诈诏指责分别保留为他的说法，不能当作本站性别规范。')
claim('person',people['李贻业'],'description','《资治通鉴》记李贻业为李蔚的从曾孙。',5,'贻业，蔚之从曾孙也。','从曾孙不是直系曾孙，未核支系，暂不建立直系父子链或新建祖先人物。')
add('bian_will_announced','南唐二月丙子正式宣布李昪遗制',6,'丙子，','始宣遗制。',[],when='943年二月丙子',place='南唐',note='原文未具名发布者；公开遗制日与庚午死亡日分别记录。')
add('chen_absence_and_return','陈觉称病数月不入朝，到宣布遗诏时才露面',6,'烈祖末年','乃出。',[('陈觉','称病数月不入朝，到宣布遗诏时才露面')],year=None,when='李昪末年至943年二月丙子，开始日期未载',place='南唐',note='数月为跨度不反推起月；烈祖惩罚近臣是背景，陈觉称疾不等于已确诊患病。')
add('xiao_impeaches_chen_after_death','萧俨请求追究陈觉等待李昪去世的罪责，李璟不批准',6,'萧俨劾奏：',None,[('萧俨','指责陈觉在家等待李昪去世，请求追究'),('陈觉','受到萧俨弹劾'),('景通','拒绝萧俨的请求')],when='943年二月丙子宣布遗诏时',place='南唐',note='等待去世是萧俨弹劾中的指责，不补确证动机。')
# 7: long retrospective passages explicitly receive unknown dates.
add('bian_bans_forced_servitude','李昪任吴国宰相时，禁止强迫良民为奴，要求奴婢交易登记立券',7,'自烈祖相吴，','通官作券。',[('唐主','任吴国宰相时禁止强迫良民为奴，并要求交易登记立券')],year=None,when='李昪任吴国宰相期间，具体年月未载',place='吴国',note='压良为贱是强迫良民成为奴婢，不能简化成全面禁止所有奴婢交易。')
add('feng_brothers_draft_sale_will','冯延巳兄弟起草遗诏，允许百姓卖子女',7,'冯延己及弟','意欲自买姬妾，',[('冯延己','与弟弟起草允许百姓卖子女的遗诏'),('延鲁','与兄长起草允许百姓卖子女的遗诏')],when='943年二月李昪去世后',place='南唐',note='自买姬妾是史书解释的意图，不能写成已购买；草稿规定随后被公布，不是李昪生前同意。')
add('xiao_rejects_sale_will','萧俨反对允许卖子女的遗诏，认为这不是李昪的意思',7,'萧俨驳曰：','非大行之命也。',[('萧俨','反对新规定，认为是冯延巳等所为而非李昪的命令')],when='943年二月宣布遗诏后',place='南唐',note='诈称遗命为萧俨的判断，后续旧奏章作为核对依据，分别记录。')
add('yanlu_prior_sale_request','冯延鲁任东都判官时，曾请求允许百姓卖子女',7,'昔延鲁为','已有此请；',[('延鲁','任东都判官时提出允许卖子女的请求')],year=None,when='李昪在位期间，冯延鲁任东都判官时，具体年月未载',place='南唐',note='这是萧俨回顾的旧请求，不当作943年新请求。')
add('bian_redeems_children','萧俨说李昪任吴国宰相时，曾出府金赎回被卖的子女',7,'陛下昔为吴相，','故远近归心。',[('萧俨','回顾李昪任吴相时出资赎回被卖子女的做法'),('唐主','据萧俨回顾，曾出府金赎回被卖子女，使其归家')],year=None,when='李昪任吴国宰相期间，具体年月未载',place='吴国',note='赎回事实据萧俨的回顾；远近归心为其评价，不补购买人数与支出额。')
add('bian_plans_punish_yanlu','李昪认可萧俨的反对意见，想治冯延鲁的罪，萧俨劝免',7,'今即位而反之，','臣以为延鲁愚，无足责。',[('萧俨','反对允许卖子女，又认为冯延鲁不足以责罚'),('唐主','认可萧俨意见，准备追究冯延鲁')],year=None,when='李昪在位期间，冯延鲁提出旧请求后，具体年月未载',place='南唐',note='将治是准备处罚，原文未载实际定罪；愚为萧俨说法。')
add('bian_marks_yanlu_petition','李昪在冯延鲁的奏章上作标记，将它带入宫中',7,'先帝斜封','持入宫。',[('唐主','在冯延鲁奏章上作标记后带入宫中')],year=None,when='上述旧请求处理时，具体年月未载',place='南唐',note='原文记斜封抹三笔，不据笔迹推具体文字或罪名。')
add('jing_finds_prior_petition','李璟取出先帝留中的奏章，找到冯延鲁旧奏疏',7,'齐王命取','果得延鲁疏。',[('景通','命人查阅先帝留中的一千多道奏章，找到冯延鲁奏疏')],when='943年二月遗诏争议中',place='南唐',note='一千余道是留中奏章数量，不是冯延鲁奏章数量。')
add('jing_keeps_sale_decree','李璟因遗诏已经公布，最终未改允许卖子女的规定',7,'然以遗诏',None,[('景通','因遗诏已经公布而未改规定')],when='943年二月遗诏争议中',place='南唐',note='未改是原文结果；不因此改写李昪生前反对立场。')
relationship('冯延己','延鲁','兄长',7,'冯延己及弟礼部员外郎延鲁，俱在元帅府，','原文明示延鲁为弟，统一按A是B的兄长建立一条有向关系。')
# 8: Yin founding, government and tax practices.
add('yan_founds_yin','王延政在建州称帝，建立大殷',8,'闽富沙王','国号大殷，',[('王延政','在建州称帝，定国号为大殷')],when='943年二月条下，具体日期未载',place='建州',note='承接二月叙事，不补确切日；殷与王延羲的闽政权并列，不写为已经统一闽地。')
add('yin_pardon_tiande','王延政实行大赦，改元天德',8,'大赦，','改元天德。',[('王延政','称帝后大赦并改元天德')],when='943年二月条下，具体日期未载',place='殷国')
add('jiang_le_yongzhou','王延政将将乐县改为镛州',8,'以将乐县','为镛州，',[('王延政','将将乐县改为镛州')],when='943年二月条下，具体日期未载',place='将乐县',note='改行政建制，不据名称推地理坐标。')
add('yanping_tanzhou','王延政将延平镇改为镡州',8,'延平镇','为镡州。',[('王延政','将延平镇改为镡州')],when='943年二月条下，具体日期未载',place='延平镇',note='镡保留史載州名，不以现代行政区替代。')
add('zhang_yin_empress','王延政立张氏为皇后',8,'立皇后','张氏。',[('王延政','立张氏为皇后'),('皇后张氏','被立为殷国皇后')],when='943年二月条下，具体日期未载',place='殷国')
add('pan_libu_shangshu','王延政任潘承祐为吏部尚书',8,'以节度判官','为吏部尚书，',[('王延政','任潘承祐为吏部尚书'),('潘承祐','由节度判官升吏部尚书')],when='943年二月条下，具体日期未载',place='殷国')
add('yang_bingbu_shangshu','王延政任杨思恭为兵部尚书',8,'节度巡官','为兵部尚书。',[('王延政','任杨思恭为兵部尚书'),('杨思恭','由节度巡官升兵部尚书')],when='943年二月条下，具体日期未载',place='殷国')
add('pan_tongpingzhang','潘承祐不久加同平章事',8,'未几，','承祐同平章事，',[('潘承祐','加同平章事')],when='943年建殷任吏部尚书不久，确切月日未载',place='殷国')
add('yang_pushe','杨思恭不久升仆射，录军国事',8,'思恭迁','录军国事。',[('杨思恭','升仆射，录军国事')],when='943年建殷任兵部尚书不久，确切月日未载',place='殷国')
add('yin_court_ritual','王延政穿皇帝赭袍处理政务，但部分朝见与接使仍沿用藩镇礼',8,'延政服','犹如籓镇礼。',[('王延政','穿赭袍处理政务，在牙参及接邻国使者时仍用藩镇礼')],when='943年建殷后的政务概述，具体月日未载',place='殷国',note='区分服饰称帝与礼仪沿用，不推所有礼制均完成改造。')
add('yang_increases_taxes','杨思恭加重田亩山泽及鱼盐蔬果税负，被称为杨剥皮',8,'殷国小民贫，',None,[('杨思恭','因聚敛受到王延政宠信，加重多项税负，被称为杨剥皮'),('王延政','因杨思恭能聚敛而宠信他')],when='943年建殷后的税政概述，具体月日未载',place='殷国',note='倍征保留史载征税程度，不推每项具体税率。杨剥皮为当时人的称呼，不改为姓名，也不作为本站评价。')
sup('yan_founds_yin',8,'xinwudaishi-068-yin-founded','延政乃以建州建國稱殷，改元天德。','《新五代史》也记王延政在建州建国称殷，改元天德。','只支持建国与改元，未给此日。')
sup('yin_pardon_tiande',8,'xinwudaishi-068-yin-founded','延政乃以建州建國稱殷，改元天德。','《新五代史》也记改元天德。','此句没有大赦，补证范围限改元。')
relationship('皇后张氏','王延政','妻子',8,'立皇后张氏。','册皇后确认配偶身份，不推此前婚期或子女。')
reviews={1:'宦官兼领永平及非议，王承休仅为历史先例。',2:'己未出发、乙丑到达分别录；旧新纪补赦囚与旧纪封丘停留。每月问遗为概述不造逐月使者。',3:'追述继承人打算、训斥、种氏建议与命嫁、献丹和身体变化、王栖霞言行，具体年月为空。评价、梦境、医学描述归于史料。亲子方向明确，命嫁未造配偶。',4:'冯己已据新史巳校核同人，不改底本。官员批评保留发言者，病情不作现代诊断。二月庚午召侍、遗劝和夜死与秘丧监国赦分开，后续丙子是遗制公布日。',5:'孙晟欲称遗诏让太后临朝为未执行打算，李贻业反对后停止。从曾孙支系未核，不造直系链。',6:'丙子遗制公布与陈觉称病数月、出现、萧俨弹劾及拒绝分开；等待去世是弹劾中的指责。',7:'吴相时期政策、赎人及旧卖子女请求为追述，日期为空；草遗诏、萧俨反对、查旧奏及未改规定为943年当下。禁压良不等于禁全部奴婢交易，动机与评价归于史书或发言者。',8:'建殷称帝改元大赦、两州建制、立后、四任官、礼仪沿用和税政分别录；未几不补确切日。新史独立补证称殷改元，未推全闽统一或具体税率。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=283,year=943,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=283,next_year=943,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key='xinwudaishi-062-feng-name',note='仅用于姓名异体校核，不将此段所述随后任命与十二月政令提前录入。')],coverage='连续第1—8段，原49—56行；正月至二月及追述；后接第9段三月己卯朔任官。',source_issues_review='冯延己、延已、延巳按职务同人校核；从曾孙支系、原文在巳上等字形及纸本待核。计划与执行、旧事与当年分别标明。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],plain_language_review='首次检查人物介绍、事件标题正文、参与动作、关系方向和对应事实说明。展示用简体白话，原文逐字保留；计划、对话评价与执行分开，未知追述年月为空。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
