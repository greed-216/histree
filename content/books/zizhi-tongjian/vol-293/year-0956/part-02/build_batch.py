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
COMMIT='d5d9d3447be330d5f5331703b94bb9b504dea8b6'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

for key in ['tongjian-293-956-march-opening','jiuwudaishi-116-march-956','xinwudaishi-67-chenman-misidentifies']:
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
main_sources = ['tongjian-293-956-march-opening','tongjian-293-956-li-deming-changzhou']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0956-p009-p016',
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
for n in range(9, 17):
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
        citation = f'卷293·显德三年（956年三月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0956_02_{len(B["claims"])+1:04d}'
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','吴越王':'钱弘俶','弘冀':'李弘冀','赵鐸':'赵铎','硃匡业':'朱匡业','陆孟俊':'陆孟俊（南唐袁州刺史）'})
NEW_ALIASES={'王继沂':['王繼沂'],'安弘道':[],'李征古':['李徵古'],'赵仁泽':['趙仁澤'],'赵铎':['趙鐸'],'柴克宏':[],'柴克宏母（姓名未载）':[],'陆孟俊（南唐袁州刺史）':[],'朱匡业':['硃匡業','朱匡業'],'乔匡舜':['喬匡舜']}
NEW_DESCRIPTIONS={
'王继沂':'王延政之子。956年三月与马希崇都在扬州，柴荣下诏抚慰存问。此段未载官职和生卒年。',
'安弘道':'后周供奉官。956年三月奉柴荣命护送李德明、王崇质回金陵，并携致李璟的诏书。生卒年未载。',
'李征古':'南唐枢密副使。《通鉴》记956年参与指控李德明卖国，后来在常州救援部署中给柴克宏朽损装备、召其回朝并拟用朱匡业替代。指控与能力评价保留来源立场，不认作李德明确实卖国。',
'赵仁泽':'南唐常州团练使。956年被吴程俘获送到钱唐，因不向钱弘俶行拜礼并责其违约而受伤；元德昭为他敷药，得以活命。生卒年未载。',
'赵铎':'南唐燕王李弘冀的部将。956年吴越军攻常州时，劝李弘冀不要离开军府回金陵，以免动摇军心。生卒年未载。',
'柴克宏':'南唐龙武都虞候，柴再用之子。956年请求出战，其母亦上表荐子，李璟任其为右武卫将军赴常州救援。虽然装备劣、被召还，仍进军，在常州击败吴越军。生卒年待后续段落。',
'柴克宏母（姓名未载）':'史书未记姓名。956年柴克宏请求出战时，上表称儿子有父亲遗风、可为将，并愿承担举荐不当的责任。用亲属称谓识别此位确有行动的人物，不编造姓名、生卒年或其他身世。',
'陆孟俊（南唐袁州刺史）':'南唐袁州刺史。956年获命与柴克宏会兵救常州。与951年楚牙内侍卫指挥使陆孟俊暂无完整连续履历证据，暂分档保存，后续再核是否同人。',
'朱匡业':'南唐神卫统军。956年李征古拟让其代柴克宏，随后到达常州行营，柴克宏谨慎事奉。史书字形硃沿原文，主体用朱；生卒年未载。',
'乔匡舜':'南唐中书舍人。956年赴吴越出使，柴克宏进常州时声称船队是迎接他，以掩护登岸突袭。生卒年未载。'}
old='jiuwudaishi-116-march-956';six='jiuwudaishi-116-six-prefecture-negotiation';ns='xinwudaishi-33-huainan-peace-negotiation';cw='xinwudaishi-67-chenman-misidentifies'
add('chairong_cares_ma_wang','柴荣下诏抚慰在扬州的马希崇和王继沂',9,Q[9]['text'],None,[('帝','下诏抚慰存问两名在扬州者'),('马希崇','在扬州获存问'),('王继沂','作为王延政之子，在扬州获存问')],when='956年三月条所记，具体诏日未载',place='扬州')
relationship('王延政','王继沂','父亲',9,Q[9]['text'],'王延政是王继沂的父亲，原书明记之子，不因王延政未在场就把他作为本次抚慰行动者。')
add('sunsheng_envoys_arrive','孙晟等抵达柴荣行在',10,'丙午，','孙晟等至上所。',[('孙晟','奉南唐表章到达行在'),('上','接收来使')],when='956年三月丙午',place='后周行在',note='与此前遣使分开，这里才是到达日；等未逐一点名，王崇质同使身份见前批。')
sup('sunsheng_envoys_arrive',10,old,'丙午，江南國主李景遣其臣偽司空孫晟、偽禮部尚書王崇質等奉表來上，','《旧五代史》同日记孙晟、王崇质奉表到行在。','对未在主书此句单列的王崇质保留补书说明，不改摘录。')
add('sunsheng_shown_at_shouchun','柴荣派中使带孙晟到寿春城下招谕刘仁赡',10,'庚戌，','且招谕之。',[('上','安排以南唐使臣招谕守将'),('孙晟','被中使带到寿春城下'),('刘仁赡','成为招谕对象')],when='956年三月庚戌',place='寿春城下',note='招谕意图与守将实际是否降城分清，本段未降。')
add('sunsheng_urges_renzhan_loyalty','刘仁赡在城上行礼，孙晟劝他守住对南唐的忠诚',10,'仁赡见晟，','不可开门纳寇。”',[('刘仁赡','身着戎服在城上向孙晟行礼'),('孙晟','劝刘仁赡不要开城纳敌')],when='956年三月庚戌招谕时',place='寿春城上与城下',note='寇为孙晟讲话中对周军的称谓，展示为敌军，不作本站政治评价；拜为见使臣行礼，不是已经向后周投降。')
add('chairong_releases_sun_after_rebuke','柴荣因孙晟劝守而生气，孙晟申明职责后获释',10,'上闻之，',None,[('上','听说劝守后愤怒，听辩后释孙晟'),('孙晟','以南唐宰相职责说明不能劝守将背叛')],when='956年三月庚戌城下对话之后，具体处置日未另列',place='后周行在',note='释之不等于准他立即回国，后文他仍留在行在。')

add('tang_six_prefecture_offer','李璟请使臣提出去帝号、割六州和岁输金帛条件以求停战',11,'唐主使','以求罢兵。',[('唐主','提出去帝号和割地输财的议和方案'),('李德明','向柴荣陈述条件'),('孙晟','参与陈述条件')],when='956年三月议和期间，具体议条件日未载',place='南唐至后周行在',description='李璟经李德明、孙晟提出放弃帝号、割寿濠泗楚光海六州，每年输金帛百万以求停战。百万沿史书未独立列清计量，不作现代货币换算；这是方案，未写作已完成交地和付款。')
sup('tang_six_prefecture_offer',11,six,'本國主願割壽、濠、泗、楚、光、海六州之地，歸於大朝。','《旧五代史》也记南唐愿献六州。','叙述为使臣面奏国主愿望，不误记六州此时都已归周。')
sup('tang_six_prefecture_offer',11,ns,'謨與晟等皆言景願割壽、濠、泗、楚、光、海六州之地，歲貢百萬以佐軍。','《新五代史》记钟谟、孙晟等也曾陈述六州与岁贡百万条件。','主书此处具名李德明孙晟，新书包括钟谟的使团概述，保留详略，不把多次表章全合成同一天。')
add('chairong_rejects_partial_land','柴荣要求尽得江北，拒绝南唐只割六州的方案',11,'上以淮南之地','不许。',[('上','认为战果已大，欲尽取江北而拒绝')],when='956年三月议和期间',place='后周行在',note='淮南已半为周有为主书概述，当时全部江北尚未得到；不要将军事目标写成完成。')
add('lideming_requests_return','李德明请求宽限五日，回南唐劝李璟献全部江北，柴荣准许',11,'德明见周兵','上乃许之。',[('李德明','请求回国取尽献江北的表章'),('上','准许李德明回返')],when='956年三月拒六州方案之后，具体请返日未载',place='后周行在',note='宽五日为请求的期限，不指使臣已被判死刑或实际五日全部完成，献江北仍是拟劝告方案。')
sup('lideming_requests_return',11,six,'願陛下寬臣數日之誅，容臣自往江南，取本國表，盡獻江北之地。','《旧五代史》也记李德明求数日宽限、回江南取尽献江北表。','数日与主书五日详略保留，之诛为使臣谨慎请命措辞，不直接创建周朝已决定处死他事件。')
add('an_hongdao_escorts_envoys','孙晟请求王崇质同返，柴荣派安弘道护送两使回金陵',11,'晟因奏遣','赐唐主诏，其略曰：',[('孙晟','请求王崇质同李德明回返'),('王崇质','与李德明同返'),('李德明','获准回国劝献地'),('上','派供奉官护送并付诏书'),('安弘道','作为供奉官护送使臣')],when='956年三月准返之后，具体启程日未载',place='后周行在至金陵')
sup('an_hongdao_escorts_envoys',11,ns,'世宗許之，遣供奉官安弘道押德明、崇質南還，而謨與晟皆見留。','《新五代史》同记安弘道护送李德明王崇质回国，钟谟孙晟仍被留。','押为护送兼约束的使行，不凭此推定两名回使都戴枷；未将孙晟此前释之误解成已返唐。',relation='adds')
add('chairong_land_before_ceasefire','柴荣在诏书中允许保留帝号，要求诸郡归附后才立即停兵',11,'“但存帝号，','请从兹绝。”',[('上','以诏书提出交地后停战条件')],when='956年三月遣回使者时',place='后周至南唐',description='柴荣告诉李璟可以保留帝号，若坚心事大则不会逼入险地；须等诸郡全来归附才立即停兵，否则交往断绝。此为诏书条件，不把帝号自动记为已取消，也不认为此时已正式停止战事。')
add('tang_receives_letters_and_thanks','柴荣致书南唐将相要求商议，李璟上表致谢',11,'又赐其将相书，',None,[('上','致书南唐将相要求商议回复'),('唐主','上表致谢')],when='956年三月交涉期间，具体来往日未载',place='后周至南唐',note='上表谢是答复礼节，不等于李璟已履行交地条件。')

add('lideming_urges_all_jiangbei','李德明称赞周军强盛，劝李璟献江北，李璟不悦',12,'李德明盛称','唐主不悦。',[('李德明','返国后劝献江北'),('唐主','不悦于割地劝告')],when='956年三月使臣返金陵之后',place='金陵')
add('songqiqiu_opposes_land','宋齐丘认为割地无益，李德明的言论不被信任',12,'宋齐丘以','国人亦不之信。',[('宋齐丘','认为割地无益'),('李德明','其言论被认为夸大，不获信任')],when='956年三月返国议和争论时',place='南唐朝廷',note='轻佻、过实为史家与当时反对者的评价，国人不信为概述，不确认所有李德明报告均虚假。')
add('chen_li_use_wang_to_accuse','陈觉、李征古让王崇质作不同陈述，并指控李德明卖国',12,'枢密使陈觉','德明卖国求利。”',[('陈觉','与李征古安排反对陈述并指控'),('李征古','与陈觉指控李德明'),('王崇质','被要求作与李德明不同的陈述'),('李德明','被指控卖国求利')],when='956年三月使臣返国后',place='南唐朝廷',note='素恶是主书对既有关系的说明，指控不当卖国已查实，不造真实获利金额。')
add('lijing_executes_lideming','李璟因指控发怒，在市中处死李德明',12,'唐主大怒，',None,[('唐主','发怒后命处死李德明'),('李德明','在市中被处死')],when='956年三月返国后，具体死日未载',place='金陵市中',note='死亡原因是君主因指控动怒的记载，不把构陷说法当罪名已证。')
claim('person',people['李德明'],'death_year','李德明于956年三月返国议和时被李璟处死。',12,'唐主大怒，斩德明于市。','结合该段三月编年与返国上下文，死日未载，已有主体其他字段不覆盖。')

add('wucheng_takes_changzhou_outer','吴程攻破常州外城，俘赵仁泽并送至钱唐',13,'吴程攻常州，','送于钱唐，',[('吴程','攻破外城并押送被俘守将'),('赵仁泽','以常州团练使身份被俘')],when='956年三月吴越进攻常州时，具体日未载',place='常州外郭至钱唐',note='外郭明确，不扩大成全常州城已稳固占领。')
add('zhaorenze_defies_wuyue','赵仁泽拒向钱弘俶行拜礼、责其违约，遭钱弘俶伤害',13,'仁泽见吴越王','抉其口至耳。',[('赵仁泽','拒拜并指责吴越违约'),('吴越王','愤怒后使赵仁泽受伤')],when='956年常州守将送达钱唐之后',place='钱唐',note='负约为赵仁泽责问，不据此编造未在此载的条约全文；不添加具体行刑者姓名。')
add('yuandezhao_treats_zhaorenze','元德昭怜赵仁泽忠诚，为其敷药使其活命',13,'元德昭怜其忠，',None,[('元德昭','为赵仁泽敷药'),('赵仁泽','伤后得以活命')],when='956年在钱唐受伤之后，具体日未载',place='钱唐',note='得不死明确未当场死亡，不凭严重伤势填写死亡年956。')

add('lijing_recalls_lihongji','李璟担忧吴越逼近润州，命李弘冀回金陵',14,'唐主以','征还金陵。',[('唐主','担忧李弘冀年少不会用兵，命其回朝'),('弘冀','以宣润大都督、燕王身份被召回')],when='956年三月吴越在常州时',place='宣润军府至金陵',note='年少不习兵是李璟的担忧，本段没有李弘冀确切年龄。')
add('zhaoduo_urges_hongji_stay','赵铎劝李弘冀留守，李弘冀拒绝召还并安排战守',14,'部将赵鐸','为战守之备。',[('赵铎','劝李弘冀不要回朝，以免动摇军心'),('弘冀','不就征召，部署战守')],when='956年三月接到召还命令后',place='宣润军府',note='所部必乱为部将预判，不写成已经发生全军叛乱。')
cp=person('柴克宏',14,'南唐龙武都虞候、柴再用之子，本段记其平日生活及他人评判',span(14,'龙武都虞候柴克宏','非将帅才。'))
claim('person',cp,'evaluation','《通鉴》记柴克宏沉默好施，不置家产，平日与宾客饮酒博弈，未谈军务，时人因此认为他不是将帅之才。',14,span(14,'龙武都虞候柴克宏','非将帅才。'),'他人印象与其后实际指挥能力分开，不以平日娱乐直接判军事才能。')
relationship('柴再用','柴克宏','父亲',14,span(14,'龙武都虞候柴克宏','再用之子也，'),'原文明记柴克宏为再用之子，沿既有柴再用主体。')
add('chaikehong_fuzhou_appointment','李璟因有人反映柴克宏久不升迁，任其为抚州刺史',14,'至是，有言','抚州刺史。',[('唐主','任柴克宏为抚州刺史'),('柴克宏','获任抚州刺史')],when='956年三月常州救援之前',place='南唐朝廷及抚州',note='匿名建议者不造姓名，任官不等已去抚州。')
add('chai_requests_battle','柴克宏请求上阵，其母上表称儿子可为将并愿担责',14,'克宏请效死行陈，','分甘孥戮。',[('柴克宏','自请出战'),('柴克宏母（姓名未载）','上表荐儿子有父风，愿承担不称职责任')],when='956年三月常州救援部署时',place='南唐朝廷',note='自请效死与母亲愿承担重罚是表态，不记实际全家被处死；母亲以真实亲属称谓识别，未编姓名。')
relationship('柴克宏母（姓名未载）','柴克宏','母亲',14,span(14,'克宏请效死行陈，','分甘孥戮。'),'其母指柴克宏的母亲，姓名未载，称谓不当实名。')
add('chaikehong_lumengjun_relief_order','李璟任柴克宏为右武卫将军，命与陆孟俊会军救常州',14,'唐主乃以',None,[('唐主','任将并安排常州救援'),('柴克宏','任右武卫将军领军救援'),('陆孟俊','以袁州刺史身份与柴克宏会军')],when='956年三月自请荐子之后',place='南唐至常州',note='袁州陆孟俊与951楚国同名将暂无完整履历桥接，暂分档。')

add('chaikehong_poor_equipment','柴克宏所领兵老弱，李征古又给朽损装备，柴请求后遭斥骂',15,'时唐精兵','克宏怡然。',[('柴克宏','领老弱兵，因装备朽损向枢密使提出意见'),('李征古','给朽损装备并斥骂柴克宏')],when='956年三月赴常州前',place='南唐军队',description='《通鉴》称南唐精兵在江北，柴克宏领的数千人老弱，李征古又给朽损装备。柴提出意见遭斥骂，部众愤怒而柴保持平静。这是当时处境及史书评判，不推导未载装备损坏比例或军费数额。')
add('li_recalls_chai_names_zhu','李征古在柴克宏至润州时召其回朝，拟用朱匡业替代',15,'至润州，','硃匡业代之。',[('李征古','派使召回并拟另换主将'),('柴克宏','在润州收到召还安排'),('硃匡业','以神卫统军身份拟作替代主将')],when='956年三月常州救援行军中',place='润州',note='拟替换与后段朱实际到行营分开，不在此强记柴已回朝、战事已由朱接管。')
add('hongji_backs_chai','李弘冀支持柴克宏继续作战，并上表反对中途换将',15,'燕王弘冀','不宜中易主将。',[('弘冀','鼓励柴继续前战，上表主张不换将'),('柴克宏','得到李弘冀支持')],when='956年三月润州救援部署时',place='润州至南唐朝廷',note='可以成功与危在旦莫为奏中的判断，未把常州救援结果提前写成已经获胜。')
add('chai_executes_recall_messenger','柴克宏进军常州，面对再次召还，命处死使者',15,'克宏引兵',None,[('柴克宏','不从召还，认为使者干扰军务而命处死')],when='956年三月继续进军常州时',place='赴常州途中',description='柴克宏继续赶往常州，李征古再次遣使召他回去。柴声称使者必是奸人，命将其斩杀；使者申明受枢密命令，柴仍说李征古亲来也会斩。奸人是柴的判断，不据此确认使者身份造假，也不写成柴已杀李征古。')

claim('person',people['吴程'],'social_relations','《通鉴》回述吴程与鲍修让、罗晟在福州时已有嫌隙，后来压抑两人，使其怨恨。',16,span(16,'初，鲍修让、','二人皆怨。'),'福州时期为旧事，未给确年，不造956年新福州战役，也不直接建立终身仇敌关系。')
add('qiaokuangshun_wuyue_mission','李璟先派乔匡舜出使吴越',16,'先是，','使于吴越，',[('唐主','派中书舍人赴吴越'),('乔匡舜','以中书舍人身份出使')],year=None,when='956年三月柴克宏突袭常州之前，具体使行年日未载',place='南唐至吴越',note='出使是后文伪装迎接船队的背景，不与实际战舰行动合成外交使团袭击。')
add('chai_disguises_boats','柴克宏到常州，以船幕藏兵，声称迎乔匡舜，吴程未疑',16,'壬子，','不可妄以为疑。”',[('柴克宏','以迎使船队为名隐藏甲士'),('吴程','听取巡逻报告后未认定为袭击')],when='956年三月壬子',place='常州',note='迎使为柴对外声称，不写作船内确是纯外交人员。')
add('chaikehong_defeats_wuyue','柴克宏军登岸突击吴越营，吴程逃脱，吴越军大败',16,'唐兵登岸，','斩首万级。',[('柴克宏','突袭吴越营并获胜'),('吴程','仅脱身逃走'),('罗晟','不积极抵抗，放对方趋吴程营帐')],when='956年三月壬子突袭时',place='常州吴越军营',note='不力战是主书对罗晟行为的记载，放任往吴帐不推定他已正式投降南唐。斩首万级为史载数字，未作为现代实测。')
sup('chaikehong_defeats_wuyue',16,cw,'程等攻常州，果為景將柴克宏所敗，','《新五代史》也记吴程攻常州时被柴克宏击败。','同段从周军未渡淮至后续水军概述时序不同，不能改主书壬子记录；原段后续邵可迁父子和大规模舰队另待相关材料。')
add('zhukuangye_arrives','朱匡业来到行营，柴克宏谨慎事奉',16,'硃匡业至','事之甚谨。',[('硃匡业','到达行营'),('柴克宏','谨慎事奉朱匡业')],when='956年三月常州获胜之后，具体日未载',place='常州行营',note='李征古拟换将和朱实际到场分开，柴对朱礼敬不等于已确认全军指挥权正式交接。')
add('wucheng_dismissed','吴程回钱唐后，钱弘俶撤去其所有官职',16,'吴程至钱唐，',None,[('吴程','兵败回钱唐后被撤官'),('吴越王','撤去吴程官职')],when='956年三月常州兵败回钱唐之后，具体日未载',place='钱唐')

reviews={9:'马希崇和王延政之子在扬州获抚存，王继沂具姓规范化，父亲王延政不作为当场受诏者。',10:'丙午到使与前段派遣分开，庚戌城下招谕、守将行礼、孙劝忠与帝怒释分阶段，行礼非投降，释非已经返国。',11:'六州去帝号岁百万方案、周要江北拒绝、李德明宽五日请求、两使返国安护、保帝号交郡停兵、将相书及唐谢表完整处理。金帛单位未明不换算，五日不是已被周判死。',12:'返国劝割与君不悦、宋齐丘反对、陈觉李征古安排王崇质异言并指控、李璟处死分开；卖国为指控而非既证事实。',13:'常州仅外郭被破、赵送钱唐拒拜受伤、元药救活分开，不因伤重改死亡，不虚构旧约全文。',14:'召李弘冀与赵铎劝留、柴再用父子、柴克宏平日评价、抚州任命、自请母荐及转将救援分别录。母仅称谓不编名，陆袁州与楚同名履历待桥接分档。',15:'数千老弱与旧装备、柴诉受骂、李召拟朱替、弘冀奏保、柴继续行軍并斩召使分开，不把奸人指控当真，也不当李征古被杀。',16:'福州旧嫌隙不套本年，乔先使与柴假迎使藏军、壬子登岸胜斩万、朱到与柴事奉、吴回被夺官分层。罗不力战不等正式降唐，新吴越史胜败印证但先后叙次独立。'}
assert not (P/'publication.json').exists()
for n in range(9,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=293,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原14—21行连续八段，割地议和至常州解围及吴程失官，后续不计完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],source_issues_review='新孙晟传使团具名钟谟与主此处李德明详略并列；新吴越史战事整体时序不同不覆盖壬子。陆孟俊同名分档，匿名母亲以亲属称谓不编造实名。硃字原摘录保留，主体朱；纸本待核。',plain_language_review='首次逐条自查人名、动作、角色、议和方案与君主回应；拒绝、许可和交地未执行分别说明。指控、猜疑、预判与史事实行分清；父母关系方向明确，原文保持底本。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
