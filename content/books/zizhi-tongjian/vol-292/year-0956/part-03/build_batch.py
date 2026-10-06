# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 292, year 955 paragraphs 15–22."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,29))
COMMIT='5b7d39c10017d28c66750d6a92a9b6db748131ef'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-956-shouzhou-chuzhou','jiuwudaishi-116-february-956','xinwudaishi-49-huangfu-captured']:
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
main_sources = ['tongjian-292-956-shouzhou-chuzhou','tongjian-292-956-yangzhou-diplomacy']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0956-p015-p022',
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
lines = (ROOT / 'resources/derived/tongjian/292.txt').read_text().splitlines()
for n in range(15, 23):
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
        citation = f'卷292·显德三年（956年二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_292_0956_03_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_292_0956_' + code
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
        edge = 'participation_zztj_292_0956_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_292_0956_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','太祖皇帝':'赵匡胤','吴越王':'钱弘俶','弘亻叔':'钱弘俶'})
NEW_ALIASES={'王知朗':[],'陈满':['陳滿'],'罗晟':['羅晟'],'陈泽':['陳澤'],'耿谦':['耿謙']}
NEW_DESCRIPTIONS={
'王知朗':'南唐泗州牙将。956年二月奉李璟命携书求和，《通鉴》记送到徐州，《旧五代史》记到滁州，两种地点保留。生卒年未载。',
'陈满':'吴越苏州营田指挥使，《新五代史》称苏州候吏。956年建议吴程进攻常州，声称后周诏书已到；新史解释他误认了李璟派来的安抚使。两书解释及职名详略保留，未把报告直接当周诏真实送达。',
'罗晟':'吴越中直都指挥使。956年二月钱弘俶派吴程督鲍修让、罗晟赴常州。生卒年未载。',
'陈泽':'南唐鄂州长山寨将领。956年二月王逵奏报攻取该寨，将陈泽等俘获并献送。生卒年未载。',
'耿谦':'南唐天长制置使。956年二月，赵匡胤奏报其归降。《通鉴》与《旧五代史》对所得粮草记二十余万、二千余万，数量及单位待核，未据差数另造两次归降。'}
feb='jiuwudaishi-116-february-956';nw='xinwudaishi-12-huainan-956';wh='xinwudaishi-49-huangfu-captured';wm='xinwudaishi-67-chenman-misidentifies'
add('wangzhilang_delivers_peace_letter','李璟派王知朗送信，请停战修好，并愿奉柴荣为兄长、岁输财物',15,'唐主遣','以助军费。”',[('唐主','派使送信提出停战和输财条件'),('王知朗','以泗州牙将身份携信求和')],when='956年二月甲戌奏报以前，具体使行日未载',place='南唐至徐州；旧史记滁州',description='李璟以唐皇帝身份致书大周皇帝，派王知朗送信，提出停战修好、把柴荣视作兄长来侍奉，并每年输送财物助军费。《通鉴》记书信到徐州，旧史记到滁州。兄事是求和条件，不是两人已结为血亲或已达成外交约定。')
sup('wangzhilang_delivers_peace_letter',15,feb,'甲戌，江南國主李景遣泗州牙將王知朗賫書一函至滁州，本州以聞，書稱唐皇帝奉書於大周皇帝，','《旧五代史》记甲戌王知朗携书到滁州，本州奏报。','主书徐州与旧史滁州为送达地点差异，分别保留，不把一个字差异当作已核同地。',relation='conflicts')
sup('wangzhilang_delivers_peace_letter',15,feb,'願陳兄事，永奉鄰歡，','《旧五代史》所录书信也提出兄事柴荣、维持友好。','双方皇帝称号和兄事愿望都是书信措辞，未获答复前不建已成立的政治兄弟关系。')
add('chairong_leaves_letter_unanswered','徐州奏报南唐求和信，柴荣没有答复',15,'甲戌，','帝不答。',[('帝','对求和信不作答复')],when='956年二月甲戌奏报，未答复的具体处置时点未另载',place='徐州至后周行在',note='甲戌用于奏报，不反推送书或起草日。')
sup('chairong_leaves_letter_unanswered',15,nw,'甲戌，李景來求成，不答。','《新五代史》同记甲戌李璟来求和而未获答复。','本纪未单列使者与地点，详略不擅补入摘录。')
add('houzhang_attacks_water_forts','柴荣命侯章等攻击寿州水寨，将壕水引入淝水',15,'戊寅，',None,[('帝','命攻击水寨并安排决壕导水'),('侯章','以前武胜节度使身份参与攻击')],when='956年二月戊寅',place='寿州水寨、壕西北隅至淝水',note='史载壕水引向淝水，不新增淹死民众或未载伤亡数字。')

add('huangfuhui_presented','赵匡胤遣使献送皇甫晖等，皇甫晖重伤卧见柴荣',16,'太祖皇帝遣使','卧而言曰：',[('太祖皇帝','派使者献送被俘者'),('皇甫晖','重伤后卧见柴荣'),('上','接见被俘的皇甫晖')],when='956年二月滁州夺取之后，献见具体日未载',place='后周行在',note='等未逐一点名，本句不自动断定所有同俘人员都同时卧病；受伤非此时已死。')
sup('huangfuhui_presented',16,feb,'乙亥，今上縶送所獲江南二將皇甫暉、姚鳳至行在，詔釋之。','《旧五代史》记二月乙亥赵匡胤将皇甫晖、姚凤送至行在，柴荣命释放。','旧书献送日单列，主书未列；今上为宋太祖赵匡胤，不是后周柴荣。',relation='adds')
add('huangfuhui_defends_loyalty','皇甫晖向柴荣说明自己并非不忠，并称赞周兵精锐、赵匡胤勇猛',16,'“臣非不忠','之勇。',[('皇甫晖','陈述忠于南唐的立场并赞周军和赵匡胤'),('上','听取皇甫晖陈述')],when='956年二月献见时',place='后周行在',note='未尝见如此精锐是皇甫晖比较往日契丹战经历的说辞，不当本站对所有军队的量化排名。')
add('huangfuhui_released','柴荣释放皇甫晖',16,'上释之，','上释之，',[('上','释放皇甫晖'),('皇甫晖','在被俘献见后获释')],when='956年二月献见之后，旧史乙亥条附释放',place='后周行在')
sup('huangfuhui_released',16,wh,'世宗召見，暉金瘡被體，哀之，賜以金帶、鞍馬，','《新五代史》补记柴荣召见后怜其满身伤口，赐金带和鞍马。','物品待遇独立补证，不推定伤口数量或完整治伤过程。',relation='adds')
add('huangfuhui_dies_after_release','皇甫晖获释数日后去世',16,'后数日卒。',None,[('皇甫晖','重伤献见获释后数日去世')],when='956年二月献见获释后数日，具体死亡日未载',place='获释后具体地点未载',note='后数日不是可精确换算的天数，不强定乙亥为死日。')
sup('huangfuhui_dies_after_release',16,wh,'後數日卒。','《新五代史》也记皇甫晖召见后数日去世。','伤俘、获释和死亡分阶段，未将其改成清流战阵当场死亡。')
claim('person',people['皇甫晖'],'death_year','皇甫晖于956年二月被俘献见后数日去世。',16,'上释之，后数日卒。','保存有出处的死亡事实；具体日未载，旧人物其他字段不覆盖。')

add('yangzhou_raid_order','柴荣命韩令坤等突袭扬州，禁止残害百姓',17,'帝诇知','戒以毋得残民；',[('帝','获知扬州疏于防守后下令袭城并保护百姓'),('韩令坤','奉命率军袭扬州')],when='956年二月己卯',place='扬州',note='获知无备为史书所记情报，不代表掌握现代完整军事部署；禁令不等于已经证明所有军人始终没有违法。')
add('li_family_tombs_protected','柴荣派人与李氏族人共同看守陵寝',17,'其李氏陵寝，',None,[('帝','安排与李氏族人共同守护陵寝')],when='956年二月己卯袭扬州部署所附，具体守护起日未载',place='南唐李氏陵寝，具体地点未载',note='沿原书李氏，不虚构是哪一位君主的墓、族人名单或现代陵址。')

add('tang_sends_zhong_li_peace_mission','李璟派钟谟、李德明奉表称臣求和，并送礼物和犒军物资',18,'唐主兵屡败，','酒二千斛，',[('唐主','因屡败派两名使者奉表求和'),('钟谟','以翰林学士、户部侍郎身份出使'),('李德明','以工部侍郎、文理院学士身份出使')],when='956年二月壬午到寿州以前，具体派遣日未载',place='南唐至寿州',description='李璟派钟谟、李德明奉表称臣请求停战，送御服、茶药、金器千两、银器五千两、缯锦二千匹及犒军牛五百头、酒二千斛。数字按主书保存，旧史详略另列，不当作已经订立和约。')
sup('tang_sends_zhong_li_peace_mission',18,feb,'壬午，江南國主李景遣其臣偽翰林學士戶部侍郎鐘謨、偽工部侍郎文理院學士李德明等奉表來上，敘願依大國稱臣納貢之意，','《旧五代史》同记壬午钟谟、李德明奉表表达称臣纳贡意愿。','伪为该书政治立场下称号，展示不额外沿用；壬午按主书为到达日，不反推南唐最初遣使日。')
sup('tang_sends_zhong_li_peace_mission',18,feb,'仍進金器千兩，錦綺綾羅二千匹及禦衣、犀帶、茶茗、藥物等，又進犒軍牛五百頭，酒二千石。','《旧五代史》也列金器千两、衣帛二千匹和牛五百头、酒二千石等礼物。','主书银器五千两此处旧史未列，斛与石按各书字面保存，不直接换算现代体积。',relation='adds')
add('peace_envoys_arrive_shouzhou','钟谟、李德明到寿州城下，柴荣展示军容接见',18,'壬午，','盛陈甲兵而见之，',[('钟谟','到寿州求见'),('李德明','与钟谟到寿州'),('上','展示军容接见南唐使者')],when='956年二月壬午',place='寿州城下',note='盛陈甲兵为接见情景，不编造装备型号和未载人数。')
sup('peace_envoys_arrive_shouzhou',18,nw,'壬午，景使其臣鍾謨來奉表。','《新五代史》同日记李璟使臣钟谟来奉表。','鍾与鐘谟字形沿既有钟谟主体，未单列李德明不表示否定共同出使。')
add('chairong_rejects_envoy_persuasion','柴荣拒绝使者游说罢兵，要求李璟亲自谢罪，并以攻金陵施压',18,'曰：“尔主自谓',None,[('上','批评南唐外交并提出亲见谢罪条件'),('钟谟','听取回应后惧怕不敢言'),('李德明','与钟谟听取回应')],when='956年二月壬午接见时',place='寿州行在',description='柴荣指责李璟从海路联络契丹而未与后周修好，要求李璟亲自来见并谢罪，否则威胁进军金陵、取府库劳军。钟谟、李德明惧怕不敢答辩。这是接见中的责难、要求和威胁，不是当时已经攻陷金陵或取得其府库。',note='唐室苗裔是李璟自称及柴荣责问中的说法，舍华事夷等属于讲话立场，不用作本站族群评价。')

add('wuyue_waits_at_border','钱弘俶派兵屯边，等待后周命令',19,'吴越王','以俟周命。',[('吴越王','屯兵边境等待命令')],when='956年二月进常州之前，具体屯兵日未载',place='吴越边境',note='等待命令与癸未实际遣军分开。')
add('chenman_proposes_changzhou_attack','陈满向吴程建议乘南唐受惊、常州无备时出兵',19,'苏州营田指挥使陈满','易取也。”',[('陈满','向吴程提出攻常州的机会判断'),('吴程','听取陈满建议')],when='956年二月吴越出军之前',place='吴越苏州及朝廷',note='易取是陈满判断，不当常州当时已被攻取或保证一定获胜。')
add('chenman_reports_zhou_edict','陈满声称周诏已到，吴程据此向钱弘俶请求出兵',19,'会唐主有诏','请亟发兵从其策。',[('陈满','报告周诏已至'),('吴程','请求钱弘俶立即采纳出兵建议'),('吴越王','听取出兵请求')],when='956年二月癸未出军以前',place='江阴、吴越朝廷',description='当时李璟派诏安抚江阴吏民，陈满却告吴程“周诏已至”，吴程据此请求钱弘俶立即出兵。《新五代史》解释为陈满未识别李璟的使者而误认，报告不能当作后周诏书实际到达的证明。')
sup('chenman_reports_zhou_edict',19,wm,'蘇州候吏陳滿不知景使，以謂朝廷已克諸州，遣使安撫矣，亟言於俶，請舉兵以應。','《新五代史》记陈满误认南唐安抚使，以为周朝已经攻取诸州、派使安抚，并请求响应出兵。','与主书告周诏已至的叙述并列，身份候吏与营田指挥使详略保存；不直接断定陈满蓄意伪造诏书。',relation='adds')
add('yuandezhao_opposes_early_attack','元德昭担心孤军入境，主张暂等，吴程坚持出兵，钱弘俶采纳吴程',19,'丞相元德昭曰：','卒从程议。',[('元德昭','担心没有周军配合，建议暂缓'),('吴程','认为机会难得，坚持立即出兵'),('吴越王','最终采纳吴程意见')],when='956年二月癸未出军以前',place='吴越朝廷',description='元德昭认为南唐不可轻视，若吴越进入南唐而周军不到，将无人协力，宜先等候。吴程坚持时机不可失，钱弘俶最终决定出兵。这里只记录意见分歧，不据此建两人的终身敌对关系。')
sup('yuandezhao_opposes_early_attack',19,wm,'俶相國吳程遽調兵以出，相國元德昭以為王師必未渡淮，與程爭於俶前，不可奪。','《新五代史》同记吴程主张出军、元德昭以周军尚未渡淮反对。','新史王师未渡淮的整体时序与主书此时周军已过淮不同，两书层次保留，不因此改写本批日期。',relation='conflicts')
add('wuyue_changzhou_dispatch','钱弘俶派吴程督鲍修让、罗晟进军常州',19,'癸未，','趣常州。',[('吴越王','派出进常州部队'),('吴程','督率出军'),('鲍修让','以衢州刺史身份受督赴常州'),('罗晟','以中直都指挥使身份受督赴常州')],when='956年二月癸未',place='吴越至常州',note='趣为向常州进军，未写成当天已攻克常州。')
add('wuyue_protects_yuandezhao','吴程称元德昭反对出师引发士卒怒言，钱弘俶藏护元德昭并捕议论者',19,'程谓将士曰：',None,[('吴程','向将士说元德昭不愿出师'),('元德昭','遭士卒扬言攻击，获钱弘俶保护'),('吴越王','将元德昭藏于府中，命捕扬言者')],when='956年二月出军之际，具体日未另载',place='吴越府中及军队',note='流言欲击是威胁，不直接写成士卒已经动手打伤丞相；不凭此推定吴程策划杀人。')

add('yangzhou_captured','韩令坤派白延遇骑兵先入扬州，随后率军到达',20,'乙酉，','令坤继至，',[('韩令坤','率军突然到扬州'),('白延遇','率数百骑在清晨先入城')],when='956年二月乙酉',place='扬州',note='清晨先入城主书说城中未察觉，后文守将逃走俘获分阶段记录。')
sup('yangzhou_captured',20,feb,'丙戌，侍衛馬軍指揮韓令坤奏，收下揚州。','《旧五代史》记丙戌韩令坤奏报取得扬州。','主书乙酉为突袭到城日，旧丙戌为奏报日，分别保留。')
sup('yangzhou_captured',20,nw,'丙戌，取揚州。','《新五代史》本纪记丙戌取扬州。','简本记取与主书乙酉进城有一天纪日差，不能直接替新史断定必只是奏报，保留未决。',relation='conflicts')
add('jiachong_burns_flees','贾崇焚烧扬州官府民舍，弃城南逃',20,'唐东都营屯使贾崇','弃城南走，',[('贾崇','以东都营屯使身份焚毁房舍后弃城逃走')],when='956年二月乙酉周军入城时',place='扬州',note='火烧范围为史书所述官府民舍，未说全城所有建筑全毁，也未载具体死亡人数。')
add('fengyanlu_captured_disguised','冯延鲁剃发穿僧服躲入佛寺，被周军捕获',20,'副留守工部侍郎冯延鲁','军士执之。',[('冯延鲁','以副留守、工部侍郎身份在弃城时伪装躲藏，被俘')],when='956年二月乙酉扬州入城后',place='扬州佛寺，具体寺名未载',note='军士未具名，不将韩令坤或白延遇写成亲手抓捕者。')
add('hanlingkun_reassures_yangzhou','韩令坤安抚扬州民众，使其留居安定',20,'令坤慰抚其民，',None,[('韩令坤','慰抚扬州民众')],when='956年二月扬州入城之后',place='扬州',note='安堵是主书对民众得以安居的概述，不据此保证此前焚毁没有损害或所有人毫无损失。')
sup('hanlingkun_reassures_yangzhou',20,feb,'令坤整眾而入，市不易肆，人甚悅。','《旧五代史》所引《东都事略·韩令坤传》也记入城后军队整齐、商铺照常、民众欣悦。','这是旧史引另一书的叙述，明确出处依赖，不当作另查到的独立原本；与焚舍事件并存，不能抹去灾害。',relation='adds')
add('changshan_fort_report','王逵奏报攻取鄂州长山寨，俘获陈泽等',21,Q[21]['text'],None,[('王逵','奏报攻寨并献俘'),('陈泽','作为寨将被俘')],when='956年二月庚寅奏报，具体攻取日未载',place='鄂州长山寨')
sup('changshan_fort_report',21,feb,'庚寅，朗州節度使王進逵上言領兵入鄂州界，攻長山寨，殺賊軍三千餘眾。','《旧五代史》同日记王进逵进入鄂州界、攻长山寨，并记杀敌三千余人。','王进逵沿已核王逵主体；旧史杀敌数为额外战报，不与主书所俘人员相加，也不改写成陈泽已被杀。',relation='adds')
add('gengqian_tianchang_surrender','赵匡胤奏报天长制置使耿谦归降，并取得粮草',22,Q[22]['text'],None,[('太祖皇帝','奏报天长归降及物资所得'),('耿谦','以天长制置使身份归降')],when='956年二月辛卯奏报，具体归降日未另列',place='天长',description='赵匡胤奏报南唐天长制置使耿谦归降，取得刍粮二十余万。旧史同日记粮草二千余万，两者差异很大，数字与计量单位待校，不相加、不擅自换成现代粮食重量。')
sup('gengqian_tianchang_surrender',22,feb,'辛卯，今上表偽命天長軍制置使耿謙以本軍降，獲糧草二千餘萬。','《旧五代史》同日记耿谦带本军归降，并记粮草二千余万。','今上为赵匡胤；主书二十余万与旧二千余万并列，原文都保留，不默改成同数，不强定单位为石。',relation='conflicts')

reviews={15:'王知朗送信徐州与旧滁州地点差保留，甲戌为奏报日；兄事为请求而非已结外交兄弟，柴荣未答。戊寅侯章攻水寨导壕水独立处理。',16:'献俘、重伤陈词、获释赐物和后数日卒分开；旧乙亥献见与主未列日期并列，死亡不当乙亥当日。',17:'己卯袭扬州命令及保护民众、守护李氏陵寝分录，不提前城陷或给未载陵主名单。',18:'遣使奉表与壬午到达、展示軍容、责问及亲见条件分阶段。礼品数字按各书列，斛石不换算；称臣请求不是已成和约，威胁取金陵不当实现。',19:'屯边、陈满建议与周诏报告、吴程请求、元德昭风险意见、王采纳及癸未遣三将、士卒扬言和藏护捕言完整处理。新史解释误认安抚使及周军未渡淮叙次独立保留，不判造诏或终身敌对。',20:'乙酉骑兵先入、韩后到、贾焚舍逃、冯僧装被俘、韩安抚分开。旧丙戌奏报与新本纪丙戌取城分别说明，不抹除主乙酉；军纪好评不消灭焚毁事实。',21:'庚寅奏报与实际攻寨日分开，主陈泽被俘与旧杀敌三千余并列不同范围，不互替。',22:'辛卯是奏报日，耿谦同人同次归降；刍粮二十余万和二千余万原字保留，不加数不擅换单位，待后续版本校核。'}
assert not (P/'publication.json').exists()
for n in range(15,23):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(15,23)],next_paragraph=Q[23]['id'],next_volume=292,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原88—95行连续八段，从王知朗求和至天长归降；源快照含以后事务但不计覆盖。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(15,23)],source_issues_review='王知朗徐州滁州、扬州乙酉丙戌、天长物资二十余万二千余万差异保留；吴越陈满误认及主新时序分别说明。书信政治称谓、夷华言论为原讲话立场，纸本及异文待核。',plain_language_review='首次逐条自查人物与事件、角色、时间、物资和核对说明，明确主语；请求与已成约、威胁与已执行、进城与报捷、建议与判断、被俘与阵亡分开，引用不改字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
