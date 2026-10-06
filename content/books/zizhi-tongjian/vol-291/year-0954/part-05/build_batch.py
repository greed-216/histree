# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 954 paragraphs 33–35."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,39))
COMMIT='0fddebfec5def5d44c0a7f66cf1411a98ac3bde3'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-114-april-supply-954','xinwudaishi-12-chairong-accession']:
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
main_sources = ['tongjian-291-954-fengdao-commentaries']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0954-p033-p035',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
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
lines = (ROOT / 'resources/derived/tongjian/291.txt').read_text().splitlines()
for n in range(33, 36):
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
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·显德元年（954年四月及史论所含追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0954_05_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0954_' + code
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
        edge = 'participation_zztj_291_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'柴荣','王凝':'王凝（虢州司户参军）','李氏':'李氏（王凝妻）'})
NEW_ALIASES={'王凝（虢州司户参军）':[],'李氏（王凝妻）':[]}
NEW_DESCRIPTIONS={'王凝（虢州司户参军）':'欧阳修所述五代人物，家在青齐之间，曾任虢州司户参军，因病死于任上。其妻李氏携幼子和遗骸返乡的故事见《新五代史》，并被《资治通鉴》引入史论。具体生卒年未载；未与李崧案中的同名人合并。','李氏（王凝妻）':'欧阳修记述的虢州司户参军王凝之妻，姓名未详。丈夫死后，她携幼子和遗骸归乡，在开封旅舍遭拒宿并被拉扯，随后自断手臂，得到官府救助。该故事源于欧阳修所见五代笔记，具体发生年未载，保留转述性质。'}
old='jiuwudaishi-126-fengdao-death';new='xinwudaishi-12-chairong-accession';april='jiuwudaishi-114-april-supply-954';wang='xinwudaishi-54-wangning-wife'
add('fengdao_dies','冯道去世',33,'庚申，','瀛文懿王冯道卒。',[('冯道','以太师、中书令身份去世')],when='954年四月庚申，《通鉴》纪日',place='冯道居所，主书未载具体地点',note='死亡叙述与随后史论分开；旧传记四月十七日，本纪报丧与实际死亡不能混为一日。')
sup('fengdao_dies',33,old,'及山陵禮畢，奉神主歸舊宮，未及祔廟，一夕薨於其第，時顯德元年四月十七日也，享年七十有三。','《旧五代史》冯道传记他完成山陵礼、奉郭威神主回旧宫后，于显德元年四月十七日在私第去世，享年七十三。','保留原纪年月日和年龄，不自行换算公历或由享年推算精确出生年。',relation='adds')
sup('fengdao_dies',33,april,'乙丑，東京奏，太師、中書令馮道薨。','《旧五代史》本纪记四月乙丑东京奏报冯道去世。','乙丑是东京奏报日期，不据此改写实际死亡日。',relation='adds',field='time_original')
sup('fengdao_dies',33,new,'乙丑，馮道薨。','《新五代史》本纪把冯道去世记在四月乙丑。','与《通鉴》庚申及《旧五代史》传记四月十七日分列，未把本纪的简写纪日统一成主书死亡日。',relation='conflicts',field='time_original')
claim('person',people['冯道'],'death_year','冯道于954年去世；各书对死亡日与报丧日的写法另列。',33,'庚申，太师、中书令瀛文懿王冯道卒。','死亡年明确，人物既有行不无守卫覆盖；日差保留来源。')
add('fengdao_returns_spirit_tablet','冯道完成郭威山陵礼后，奉神主回旧宫',33,'及山陵禮畢，奉神主歸舊宮，未及祔廟，','及山陵禮畢，奉神主歸舊宮，未及祔廟，',[('冯道','完成山陵礼，奉郭威神主归旧宫'),('郭威','神主由冯道奉回旧宫')],when='954年四月郭威下葬后、冯道去世前',place='嵩陵至旧宫',source=old,note='此处归旧宫不等于已祔太庙，原文明确未及祔庙。')
add('chairong_honors_fengdao_after_death','柴荣为冯道停朝三日，赠尚书令、追封瀛王并谥文懿',33,'世宗聞之，','謚曰文懿。',[('柴荣','停朝并追赠冯道'),('冯道','死后获追赠、封号与谥号')],when='954年四月柴荣得知冯道去世后',place='后周朝廷',source=old)
claim('person',people['冯道'],'description','《通鉴》称冯道年轻时以孝顺谨慎闻名，从后唐庄宗时期起显贵，长期历任将相与三公三师。',33,'道少以孝谨知名，唐庄宗世始贵显，自是累朝不离将、相、三公、三师之位，','这是跨朝生平概述，不能把所有仕宦经历都定为954年。')
claim('person',people['冯道'],'evaluation','《通鉴》概述冯道清俭宽厚、机智，善于在政局变动中顺应时势；其情绪不易被人察知。',33,'为人清俭宽弘，人莫测其喜愠，滑稽多智，浮沉取容，','这是主书对性格及处世的概括，作为来源评价保存，不写成无争议的心理事实。')
add('fengdao_writes_changle','冯道曾写《长乐老叙》，自述历朝待遇与经历',33,'尝著《长乐老叙》，','自述累朝荣遇之状，',[('冯道','写《长乐老叙》，叙述历朝荣遇')],year=None,when='冯道生前，具体写作年未载',place='未载',note='尝著为此前著作，不把写作定在954年去世当天。')
claim('person',people['冯道'],'evaluation','《通鉴》说当时有人赞赏冯道的德行和器量。',33,'时人往往以德量推之。','保留当时人的赞誉，与后文欧阳修、司马光的批评分别呈现。')
claim('person',people['冯道'],'evaluation','欧阳修读《长乐老叙》后，批评冯道把历朝荣遇引以为荣，认为他缺乏廉耻。',34,span(34,'予读冯道《长乐老叙》','则天下国家可从而知也。'),'这段是欧阳修的史论，不是954年发生的行为，也不把其价值判断当作本站定论。')
claim('person',people['冯道'],'evaluation','欧阳修认为礼义廉耻维系国家，尤其要求大臣守住廉耻；他以此论证对冯道的批评。',34,span(34,'欧阳修论曰：','天下其有不乱、国家其有不亡者乎！'),'引述古代作者的政治伦理观点，不把礼义廉耻与国家存亡的论说写成已验证因果。')
claim('person',people['冯道'],'evaluation','欧阳修说自己在五代史中找到三位保全节操者、十五位为事死难者，借此质问儒者为何缺少同样的忠义事迹。',34,span(34,'予于五代得全节之士三，','而莫能致之欤？'),'三与十五是作者在其史书中选录的数量，不当作五代全部忠义人物总数；两种可能原因是作者设问。')
add('wangning_dies_in_office','欧阳修转述王凝任虢州司户参军时因病去世',34,'予尝闻五代时有王凝者，','以疾卒于官。',[('王凝','在虢州司户参军任上病故')],year=None,when='五代时期，欧阳修转述旧事，具体年份未载',place='虢州',note='与李崧案的同名王凝分开；故事在史论中被援引，不发生于954年本条。')
sup('wangning_dies_in_office',34,wang,'予嘗得五代時小說一篇，載王凝妻李氏事，','《新五代史》说明欧阳修曾见一篇五代时笔记，记载王凝妻李氏的故事。','古代小说一词在此指笔记叙事；主书转引与这篇书证存在依赖关系，不算两项独立确证。',relation='adds')
claim('person',people['王凝（虢州司户参军）'],'description','欧阳修所述王凝家在青齐之间，家境贫困，有一个年幼的儿子。',34,span(34,'予尝闻五代时有王凝者，','凝家素贫，一子尚幼，'),'摘录包含家居地、职务及家庭贫困和幼子，不推孩子姓名或生日。')
add('li_widow_returns_home','李氏携幼子和丈夫王凝遗骸归乡，经过开封遭旅舍拒宿',34,'凝家素贫，','主人不纳。',[('李氏','携子和丈夫遗骸归乡，遭拒宿'),('王凝','遗骸由妻子带回乡里')],year=None,when='五代时期王凝去世后，具体年未载',place='开封旅舍',note='家青齐、经过开封是史载路线，未补现代坐标或旅店名称。')
add('li_widow_severs_arm','欧阳修转述李氏遭旅舍主人拉扯后，自断手臂',34,'李氏顾天已暮，','见者为之嗟泣。',[('李氏','被旅舍主人拉扯后，用斧自断手臂')],year=None,when='五代时期归乡途中的转述，具体年份未载',place='开封旅舍',description='欧阳修转述李氏天晚不肯离开旅舍，主人拉住她的手臂把她往外赶。她把被人触碰视为有损守节，用斧自断手臂，旁观者为之叹息哭泣。',note='保存古代叙事和当事人所述理由，不把这种守节观念写成本站赞许或行为建议。')
add('kaifeng_official_aids_li','开封尹上报李氏遭遇，朝廷救助李氏并责打旅舍主人',34,'开封尹闻之，','厚恤李氏而笞其主人。',[('李氏','得到官府救助')],year=None,when='五代时期，李氏自断手臂之后，具体年份未载',place='开封',note='开封尹此段未具姓名，不以某年府尹名单强行补人。')
sup('kaifeng_official_aids_li',34,wang,'開封尹聞之，白其事于朝，官為賜藥封瘡，厚卹李氏，而笞其主人者。','《新五代史》还记官府给李氏药物处理伤口，予以救助，责打旅舍主人。','补救治细节；主书此故事由欧阳修转引，仍属同一叙事来源。',relation='adds')
relationship('李氏','王凝','妻子',34,'妻李氏，携其子，负其遗骸以归，','原文明称妻李氏；李氏是虢州司户参军王凝的妻子，不接李屿外甥王凝。')
claim('person',people['李氏（王凝妻）'],'evaluation','欧阳修用李氏的故事批评那些忍受耻辱以保全自身的士人。',34,'呜呼！士不自爱其身而忍耻以偷生者，闻李氏之风，宜少知愧哉！','这是作者以守节故事作的道德比较，不把它变成本站对自伤行为的肯定。')
# Commentary is indexed as sourced evaluations, without dated story events.
claim('person',people['冯道'],'evaluation','司马光主张君臣、夫妇关系应保持终身忠贞，用这一伦理标准批评冯道。',35,span(35,'臣光曰：','乱莫大焉！'),'臣光指《通鉴》作者司马光；保存古代史论观点，不作为当代普遍规范，也不记录为954年当年事件。')
fp=person('范质',35,'被司马光引述曾赞赏冯道德行与器量','范质称冯道厚德稽古，宏才伟量，虽朝代迁贸，人无间言，屹若巨山，不可转也。')
claim('person',people['冯道'],'evaluation','司马光引述范质赞冯道德厚学古、才识器量宏大，历朝变迁而少受非议。',35,'范质称冯道厚德稽古，宏才伟量，虽朝代迁贸，人无间言，屹若巨山，不可转也。','将范质赞语与司马光反驳分列；未确定赞语写作日期，不套用954年。')
claim('person',fp,'evaluation','范质的冯道赞语被《通鉴》引述，随后受到司马光批评。',35,'范质称冯道厚德稽古，宏才伟量，虽朝代迁贸，人无间言，屹若巨山，不可转也。','所述称赞内容仅据此引文，不重建为954年范质当面发言的事件。')
claim('person',people['冯道'],'evaluation','司马光认为忠节比才智与治理能力更重要，批评冯道历事五朝八姓而不以为愧。',35,span(35,'臣愚以为正女不从二夫，','庸足称乎！'),'五朝八姓是司马光论述中的计法，随评价原义保存，不据此重算或替换已录任职史实。')
claim('person',people['冯道'],'evaluation','司马光针对乱世中多人失节、不能独责冯道的辩解，认为臣子应直谏赴难或退隐，批评冯道随兴亡保有富贵。',35,span(35,'或以为自唐室之亡，','安得与他人为比哉！'),'或以为是史论设立的辩论意见，没有具名发言者；不新造人物或把所有指责当独立确证。')
claim('person',people['冯道'],'evaluation','司马光反对只以全身避祸评定贤德，用杀身成仁的标准批评冯道。',35,span(35,'或谓道能全身远害于乱世，','果谁贤乎？'),'盗跖与子路是论证中的古代例子，不给他们建立954年事件或临时人物。')
claim('person',people['冯道'],'evaluation','司马光认为责任也在于各朝君主：他们重用曾转事敌国的人，不应期待其尽忠。',35,span(35,'抑此非特道之愆也，',None),'这是作者对君臣任用的论断，作为评价保存，不把假设性问句当实际行动。')
reviews={33:'冯道死亡纪日、旧传四月十七日与享年、旧本纪乙丑奏报、新本纪乙丑死亡分别保留。生平著述不强定本年，完成山陵礼与身后赠谥据旧传补充。',34:'评论与内含故事分别处理。王凝限定虢州职务，不接李崧案同名者；妻子故事留未知年和转述性质。新史明载所见五代笔记，不能把主书转引算独立确证。匿名官员不造姓名。',35:'纯史论不创建事件。逐项保存司马光观点、范质赞语及司马光反驳，引用原字；古代伦理不是本站判断，历史举例不混入954年人物事件。'}
assert not (P/'publication.json').exists()
for n in range(33,36):
 keys=[x['key'] for x in B['claims'] if Q[n]['id'] in x['citation'] or any(y['claim_key']==x['key'] and y['primary_paragraph_id']==Q[n]['id'] for y in supplements)]
 assert keys
 ledger[n-1].update(event_keys=used.get(n,[]),fact_claim_keys=keys,batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,36)],next_paragraph=Q[36]['id'],next_volume=291,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷291原113—115行连续三段，包含冯道死亡及两段史家评论；纯评论按带出处的人物评价保存，内含五代旧事未知年。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,36)],source_issues_review='冯道死亡与报丧纪日分开；王凝妻故事保留欧阳修转述性质及来源依赖，未知发生年不填954。纸本及异文待核。',plain_language_review='首次逐条检查标题、介绍、角色、关系、时间、评价及核对说明。评价明确作者，原文保留底本；古代伦理不当本站结论，纯史论不建伪当年事件。',commentary_handling=[dict(paragraph_id=Q[34]['id'],method='保存欧阳修评价，另录未知年份的转述故事'),dict(paragraph_id=Q[35]['id'],method='仅保存人物评价与引用，event_keys为空，以fact_claim_keys逐条定位')])
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
