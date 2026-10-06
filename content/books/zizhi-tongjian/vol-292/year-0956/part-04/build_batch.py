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
assert list(Q)==list(range(1,29))
COMMIT='521cc8b13f7fb2df02cb842716b80438a03573b1'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-292-956-yangzhou-diplomacy','jiuwudaishi-116-february-956','xinwudaishi-66-zhou-xingfeng-954']:
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
main_sources = ['tongjian-292-956-yangzhou-diplomacy','tongjian-292-956-pan-zhou-conclusion']
B = {'format_version': 1, 'batch_key': 'zztj-v292-y0956-p023-p028',
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
for n in range(23, 29):
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
    ck = f'claim_zztj_292_0956_04_{len(B["claims"])+1:04d}'
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










ALIASES.update({'上':'柴荣','帝':'柴荣','唐主':'李璟','太祖皇帝':'赵匡胤','吴越王':'钱弘俶','李简':'李简（岳州团练判官）'})
NEW_ALIASES={'尹延范':['尹延範'],'方讷':['方訥'],'何继先':['何繼先'],'路彦铢':['路彥銖'],'姚彦洪':['姚彥洪'],'李简（岳州团练判官）':[],'莫弘万':['莫弘萬']}
NEW_DESCRIPTIONS={
'尹延范':'南唐园苑使。956年奉李璟命到泰州，将吴让皇杨溥的族人迁至润州；因路途困难且担忧杨氏生变，杀死该族六十名男子，返报后被李璟处死。生年未载。',
'方讷':'南唐泰州刺史。956年二月后周韩令坤攻取泰州时，逃往金陵。生卒年未载。',
'何继先':'后周静安军使。956年二月壬辰截获南唐以蜡丸传送的求救信息，并献送朝廷。生卒年未载。',
'路彦铢':'吴越上直都指挥使。956年二月癸巳奉钱弘俶命进攻南唐宣州。生卒年未载。',
'姚彦洪':'南唐静海制置使。956年二月率兵民万人投奔吴越。生卒年未载。',
'李简（岳州团练判官）':'岳州团练判官。956年潘叔嗣杀王逵后，派他率朗州将吏迎接潭州的周行逢。《新五代史》称其为潘叔嗣客将。与早年其他同名李简缺少同人证据，分档保存。',
'莫弘万':'湖南衡州刺史。956年周行逢进入朗州、接管武平武安事务时，命其暂掌潭州。生卒年未载。'}
feb='jiuwudaishi-116-february-956';wp='xinwudaishi-66-wangkui-pan-death';zp='xinwudaishi-66-zhou-xingfeng-954';wy='songshi-480-wuyue-956-dispatch'
add('yin_moves_yang_clan','李璟派尹延范将杨溥族人从泰州迁往润州',23,'唐主遣','于润州。',[('唐主','命尹延范迁移杨氏族人'),('尹延范','以园苑使身份奉命前往泰州')],when='956年二月泰州战事期间，具体派遣日未载',place='泰州至润州',note='吴让皇沿此前已核杨溥称号，迁族人不是杨溥本人仍在世同行；族人名单未载。')
add('yin_kills_yang_men','尹延范在迁徙途中杀死六十名杨氏男子',23,'延范以道路艰难，','还报，',[('尹延范','以路途困难和担忧生变为由杀死杨氏男子，返朝奏报')],when='956年二月迁族途中，具体杀害日未载',place='泰州至润州途中，具体地点未载',description='《通鉴》记尹延范因道路艰难，担心杨氏族人发生变乱，杀死该族六十名男子，之后返报。六十名男子是原书明确范围，不能改成全部男女族人被杀；生变是他的担忧，未证明被害者实际发动叛乱。')
add('lijing_executes_yinyanfan','李璟得知杀害杨氏男子后，处死尹延范',23,'唐主怒，',None,[('唐主','在返报后发怒并下令处死'),('尹延范','因杀害杨氏族人而被腰斩')],when='956年二月迁族返报后，具体处死日未载',place='南唐朝廷，具体行刑地点未载',note='迁徙命令没有包含杀害命令，尹延范杀人与李璟随后惩罚分开。')
claim('person',people['尹延范'],'death_year','尹延范于956年迁移杨氏族人后，因杀害族中男子而被李璟处死。',23,span(23,'延范以道路艰难，'),'死亡时点按该年上下文，未添加精确纪日。')
add('taizhou_capture','韩令坤攻取泰州，方讷逃往金陵',24,Q[24]['text'],None,[('韩令坤','率后周军攻取泰州'),('方讷','以泰州刺史身份弃守逃往金陵')],when='956年二月辛卯报泰州归降前后，主书未单列夺城日',place='泰州至金陵',note='旧本纪辛卯上言泰州降是奏报，不能仅据本句叙次反推确定战日。')
sup('taizhou_capture',24,feb,'侍衛馬軍都指揮使韓令坤上言，泰州降。','《旧五代史》在辛卯条记韩令坤奏报泰州归降。','主书攻拔及刺史逃亡与旧书简记归降的过程详略并列，不造一次攻下和另一次同城归降。')
add('tang_wax_message','李璟派人以蜡丸传信向契丹求援',25,'唐主遣人','求救于契丹。',[('唐主','派人携蜡丸求援信息')],when='956年二月壬辰截获以前，具体送信日未载',place='南唐至契丹',note='使者姓名未载，蜡丸为隐秘传书方式，不造地图上确定路线。')
add('hejixian_intercepts_message','何继先截获南唐求援蜡丸并献送',25,'壬辰，',None,[('何继先','以静安军使身份截获并献送求援信息')],when='956年二月壬辰',place='静安军相关截获地点未载',note='获而献之是拦获行动，不意味着契丹已接到信并答应出兵。')
add('gaofang_governs_taizhou','柴荣命高防暂掌泰州',26,Q[26]['text'],None,[('帝','任高防暂掌泰州'),('高防','以给事中身份权知泰州')],when='956年二月泰州攻取后，具体任命日未单列',place='泰州',note='权为暂任；不把前段壬辰自动当作该任命独立纪日。')
add('wuyue_xuanzhou_jiangyin','钱弘俶派路彦铢攻宣州，罗晟率战舰屯江阴',27,'癸巳，','屯江阴。',[('吴越王','派吴越军分路进取'),('路彦铢','以上直都指挥使身份进攻宣州'),('罗晟','率战舰屯江阴')],when='956年二月癸巳',place='宣州及江阴',note='进攻与屯兵明确，未当本段已攻克宣州。')
sup('wuyue_xuanzhou_jiangyin',27,wy,'顯德三年，世宗征淮南，令俶以所部分路進討。','《宋史》钱俶传同记显德三年奉柴荣命分路进讨南唐。','同年部署印证，后文战败撤军及958年事务不在本批提前导入。')
sup('wuyue_xuanzhou_jiangyin',27,wy,'路彥銖圍宣城。','《宋史》也记路彦铢围攻宣城。','宣城与主书宣州保存各书称法，不赋未经核实的坐标；传记未列癸巳日。')
add('yaoyanhong_joins_wuyue','姚彦洪率一万兵民投奔吴越',27,'唐静海制置使',None,[('姚彦洪','以南唐静海制置使身份率兵民投吴越')],when='956年二月吴越分路进兵时，具体投奔日未单列',place='南唐至吴越',note='万人包括兵与民，不译为整整一万战斗兵，也不分配虚构军民比例。')

add('pan_rallies_troops','潘叔嗣称王逵将因谗言杀他，问将士是否愿一同西行',28,'潘叔嗣属将士','汝辈能与我俱西乎？”',[('潘叔嗣','向将士解释自己担忧并请求共同西行')],when='956年二月王逵出征时，具体讲话日未载',place='岳州',description='潘叔嗣告诉将士，自己侍奉王逵已尽力，但王逵信谗生疑，回军后可能杀他，因此不愿坐等死亡，询问将士是否愿一同西行。这是潘叔嗣的判断和动员说辞，不把王逵当时已下杀令写成确定事实。')
add('pan_attacks_langzhou','将士同意西行，潘叔嗣率军袭击朗州',28,'众愤怒，','西袭朗州。',[('潘叔嗣','率愿随行的将士袭击朗州')],when='956年二月西行动员之后，具体进兵日未载',place='岳州至朗州')
sup('pan_attacks_langzhou',28,wp,'進逵入鄂州，方攻下長山，叔嗣以兵襲武陵。','《新五代史》也记王进逵攻下长山时，潘叔嗣袭击武陵。','武陵与主书朗州并列古称；主书王逵沿既有王进逵同人，行动次序不按同段世宗南征概述另定日。')
add('wangkui_killed_wuling','王逵回军追击潘叔嗣，在武陵城外战败被杀',28,'逵闻之，','逵败死，',[('王逵','回军追击，在武陵城外战败而死'),('潘叔嗣','与王逵交战并获胜')],when='956年二月潘叔嗣袭朗州之后，具体战日未载',place='武陵城外',note='死亡是此场交战的结果，不推定王逵此前已到朗州城内。')
sup('wangkui_killed_wuling',28,wp,'進逵聞之，輕舟而歸，與叔嗣戰武陵城外，進逵敗，見殺。','《新五代史》补记王进逵乘轻舟返回，在武陵城外被杀。','两书回军与轻舟详略保存，不给未載河段坐标。')
sup('wangkui_killed_wuling',28,feb,'癸巳，荊南上言，朗州節度使王進逵為部將潘叔嗣所殺。','《旧五代史》记癸巳荆南奏报王进逵被潘叔嗣杀死。','癸巳用于奏报，不直接作为武陵城外交战日；后附九国志的去长沙澧陵及城外说法另保在原快照。')
claim('person',people['王逵'],'death_year','王逵即王进逵于956年武陵城外交战时被潘叔嗣杀死。',28,span(28,'逵闻之，','逵败死，'),'主书与新旧史同一事件补证，具体战日未载，不用荆南报告日强代。')
add('pan_declines_rule_langzhou','潘叔嗣拒绝占据朗州，表示愿迎周行逢并期待获授武安',28,'或劝叔嗣遂据朗州，','以武安见处乎！”',[('潘叔嗣','拒绝自据朗州，提出迎周行逢并期待获得武安')],when='956年武陵交战之后',place='朗州及武陵',note='吾救死是潘叔嗣自述动机，武安是期待的报酬，不能在此记其已成为武安节度使。')
add('lijian_welcomes_zhouxingfeng','潘叔嗣返回岳州，派李简率朗州将吏迎周行逢',28,'乃归岳州，','武安节度使周行逢。',[('潘叔嗣','返回岳州并派李简迎接'),('李简','以团练判官身份率朗州将吏迎接'),('周行逢','以武安节度使身份被迎接')],when='956年武陵交战之后，具体迎接日未载',place='岳州、朗州至潭州',note='新建岳州团练判官李简，与早年同名李简分别保存，不按姓名直接合并。')
sup('lijian_welcomes_zhouxingfeng',28,zp,'乃還岳州，遣其客將李簡率武陵人迎行逢於潭州。','《新五代史》也记潘叔嗣回岳州，派李简到潭州迎周行逢，称其为客将。','同书段首显德元年是周行逢旧任的背景，本次迎接在王逵死后，不能强定954；身份称法差别保留。')
add('zhou_explains_pan_appointment','周行逢担心被视为与潘叔嗣同谋，打算先授行军司马',28,'众谓行逢：','授以节钺可也。”',[('周行逢','拒绝立即授潘叔嗣武安，提出先授行军司马')],when='956年受迎接之后，具体讲话日未载',place='潭州至朗州',description='有人建议把潭州给潘叔嗣，周行逢称潘杀主帅应受重罚，但因他迎接自己而暂缓；若立即授节度使，恐被外界看成共同谋杀王逵。因此主张先任行军司马，等跨年后再考虑节度。此处跨年是计划，不表示后来真正等了一年。')
add('mohongwan_tanzhou','周行逢命衡州刺史莫弘万暂掌潭州',28,'乃以衡州刺史','权知潭州，',[('周行逢','安排莫弘万暂管潭州'),('莫弘万','以衡州刺史身份权知潭州')],when='956年周行逢转赴朗州时，具体日未载',place='潭州')
add('zhou_claims_two_commands','周行逢入朗州，自称武平、武安留后并告知朝廷',28,'帅众入朗州，','告于朝廷，',[('周行逢','入朗州，自称两军留后并报朝廷')],when='956年迎入朗州之后，具体日未载',place='朗州及后周朝廷',note='自称并报朝廷，不写成同日已获柴荣正式任命。')
add('pan_refuses_staff_post','周行逢任潘叔嗣为行军司马，潘叔嗣称病不来',28,'以叔嗣为行军司马。','称疾不至。',[('周行逢','给潘叔嗣行军司马职务'),('潘叔嗣','不满意任命，称病不来')],when='956年周行逢接管朗州以后',place='朗州至岳州',note='称疾不是确证身体患病，原书同时记其愤怒；未提前赋节度使实职。')
sup('pan_refuses_staff_post',28,zp,'召以為行軍司馬。叔嗣怒，稱疾不至，','《新五代史》同记召潘叔嗣任行军司马，而潘愤怒称病不来。','任命、召见与实际到任分清，此段并未到任。')
add('zhou_suspects_pan','周行逢认为潘叔嗣拒绝任命是不满，并怀疑他要谋害自己',28,'行逢曰：“行军司马，','更欲图我邪！”',[('周行逢','以潘叔嗣不满拒命为由怀疑其谋害')],when='956年潘叔嗣称病不至后',place='朗州',note='更欲图我是周行逢的猜疑，不证明潘当时已安排刺杀。')
add('zhou_entices_pan_with_wuan','周行逢采纳他人建议，以授武安节度使诱潘叔嗣到府',28,'或说行逢：','行逢从之。',[('周行逢','采纳以职务诱召潘叔嗣的建议')],when='956年拒任争议之后，具体日未载',place='朗州至岳州',note='以授职诱召的建议及采纳已明，不把诱饵写成真正正式授任。')
add('pan_trusts_zhou_and_goes','近人劝潘叔嗣不要前往，潘因素来亲善而不疑赴约',28,'叔嗣将行，','遂行不疑。',[('潘叔嗣','因敬周行逢如兄长、双方亲善而信任前往')],when='周行逢诱召之后，具体出发日未载',place='岳州至朗州',note='所亲身份未载，不造妻儿父母名单；兄事为敬如兄长，非已证血缘或正式结拜。')
claim('person',people['潘叔嗣'],'social_relations','潘叔嗣素来把周行逢当兄长敬事，两人曾亲善。',28,'叔嗣自恃素以兄事行逢，相亲善，','保存礼敬及交情的原述，不建血缘兄弟关系，不以赴约信任倒推两人始终未有矛盾。')
add('zhou_receives_pan','周行逢沿路遣使迎候潘叔嗣，到府后亲自慰劳',28,'行逢遣使迎候，','相见甚欢。',[('周行逢','安排沿路迎候并亲自接待'),('潘叔嗣','到府后受接待')],when='潘叔嗣赴约到达时，具体日未载',place='赴朗州道路及府中',note='表面相见欢喜不等于此前诱召阴谋不存在，未替匿名使者补名。')
add('zhou_seizes_pan','周行逢拘押来谒的潘叔嗣，责其杀主帅并拒命',28,'叔嗣入谒，','乃敢违拒吾命而不受乎！”',[('周行逢','命人拘潘叔嗣并责问'),('潘叔嗣','尚未到厅堂即被拘押')],when='赴府受迎接之后，具体日未载',place='朗州府庭',description='潘叔嗣入谒未到厅堂就被拘押，周行逢责他无大功却杀王逵，又说自己因旧交暂不杀、只任行军司马，而潘拒绝任命。责问属于周行逢的辩解，不将无功等评价当成独立已证结论。')
add('zhou_executes_pan','潘叔嗣请求顾全宗族，随后被周行逢处死',28,'叔嗣知不免，',None,[('潘叔嗣','知道难免一死，请求顾全宗族'),('周行逢','随后命处死潘叔嗣')],year=None,when='956年王逵死后、诱召赴府之后，具体死亡年日未另载',place='朗州府中',note='相接的是连续政变后续叙事，未由逾年计划推定实际跨了一年；末段处死确年不独立明示留null，家族最后是否获免未载。')
sup('zhou_executes_pan',28,zp,'乃陽以武安與之，召使至府受命，至則殺之。','《新五代史》也记周行逢假称给武安，召潘到府后杀害。','同段先记954旧任、后叙王逵死后事，不以段首年份强定此处死；诱召与实任分清。')
sup('zhou_executes_pan',28,feb,'遣人詣潭州，請周行逢為帥，行逢至朗州，斬叔嗣於市。','《旧五代史》在荆南奏报王进逵死后接记迎周行逢、在朗州市中斩潘叔嗣。','旧书市中与主书府庭拘押后处死的场所详略分别保存；其为附述后续，没有独立死日，不把癸巳奏报日自动用于潘死亡。',relation='adds')

reviews={23:'迁族命令、尹杀六十男子、返报李璟怒而处死分开；六十仅男子，不扩全男女族，杨溥本人不参与其族迁移。',24:'泰州攻取与方讷奔金陵、旧辛卯奏报归降并列，未将报告日强当交战日。',25:'蜡丸求救派人、壬辰截获献送分开，不造已到契丹和出兵援唐。',26:'高防权知泰州明确暂任，独立日未载不沿前壬辰。',27:'癸巳路彦铢攻宣、罗晟屯江阴分路；宋钱俶传同年路线印证。姚彦洪万人含兵民，不当万人兵或各一万。',28:'跨p003473及p003474两份快照按原101行连续处理；动员判断、袭朗、王回军战死、潘拒自据迎周、周任莫与自称留后、给潘行军司马被拒、猜疑诱召、近人劝止及信任、迎候拘问请求宗族及杀害分阶段。李简限定名；兄事为礼敬非血缘。逾年是设想非已过一年，潘末死确年未独立列留null，王死用956但癸巳是荆南报日。'}
assert not (P/'publication.json').exists()
for n in range(23,29):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=292,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(23,29)],next_paragraph='zztj-v293-y0956-p001',next_volume=293,next_year=956,supplements=supplements,excluded_non_body=[],coverage='原96—101行最后六段全部处理，含跨两份检索片段的完整101行；卷293同年三月仍待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(23,29)],source_issues_review='旧史附述潘处死与新史段首954旧任不强套时日；府庭拘押和市中行刑分别保存。李简同名分档，吴让皇族迁不等杨溥本人参与；纸本与异文待核。',plain_language_review='首次逐条自查主语、行动、人物角色和时间说明，王逵与潘叔嗣死亡阶段分清；怀疑与事实、自称与正式授任、职务诱饵与真任、礼敬兄长与血缘、族人男女范围明确，摘录保持原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
