# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 62–68."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,84))
COMMIT='92e50fd2e637679a259045dd4484586b57ae2038'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-capital-disorder','xinwudaishi-011-guo-march','xinwudaishi-066-pushezhou']:
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
main_sources = ['tongjian-289-950-capital-disorder','tongjian-289-950-chu-north-capital','tongjian-289-950-regency-chu-defense']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p062-p068',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-289-950-chu-north-capital':'卷289·乾祐三年·楚围城前后','tongjian-289-950-regency-chu-defense':'卷289·乾祐三年·临朝与楚军防御','jiuwudaishi-103-succession-regency':'卷103·隐帝本纪·迎嗣与临朝','songshi-255-zhang-yongde-marriage':'卷255·张永德传·婚姻与押班','songshi-255-zhang-yongde-detained':'卷255·张永德传·受诏拘留','tongjian-289-950-battle-deaths':'卷289·乾祐三年·刘子陂交战与帝死','tongjian-289-950-capital-disorder':'卷289·乾祐三年·京师劫掠与禁止','jiuwudaishi-103-liuzi-battle':'卷103·隐帝本纪·刘子陂交战','jiuwudaishi-103-han-emperor-death':'卷103·隐帝本纪·帝死与京师劫掠','jiuwudaishi-108-zhang-yun-death':'卷108·张允传·仕宦与墜屋','xinwudaishi-045-yuan-sons':'卷45·袁象先传·二子','songshi-261-liu-chongjin-interpreter':'卷261·刘重进传·契丹通事','songshi-261-liu-chongjin-dengzhou':'卷261·刘重进传·汉初邓州','songshi-261-liu-chongjin-han-general':'卷261·刘重进传·乾祐末拒郭威','jiuwudaishi-103-guo-march':'卷103·隐帝本纪·郭威起兵与滑州','xinwudaishi-011-guo-march':'卷11·周本纪·郭威南下','songshi-461-zhao-xiuji-career':'卷461·赵修己传·离开李守贞至翰林天文','tongjian-289-950-guo-march':'卷289·乾祐三年·南下与禁军赏赐','jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
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
lines = (ROOT / 'resources/derived/tongjian/289.txt').read_text().splitlines()
for n in range(62, 69):
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
    labels={'tongjian-289-950-chu-north-capital':'卷289·乾祐三年·楚围城前后','tongjian-289-950-regency-chu-defense':'卷289·乾祐三年·临朝与楚军防御','jiuwudaishi-103-succession-regency':'卷103·隐帝本纪·迎嗣与临朝','songshi-255-zhang-yongde-marriage':'卷255·张永德传·婚姻与押班','songshi-255-zhang-yongde-detained':'卷255·张永德传·受诏拘留','tongjian-289-950-battle-deaths':'卷289·乾祐三年·刘子陂交战与帝死','tongjian-289-950-capital-disorder':'卷289·乾祐三年·京师劫掠与禁止','jiuwudaishi-103-liuzi-battle':'卷103·隐帝本纪·刘子陂交战','jiuwudaishi-103-han-emperor-death':'卷103·隐帝本纪·帝死与京师劫掠','jiuwudaishi-108-zhang-yun-death':'卷108·张允传·仕宦与墜屋','xinwudaishi-045-yuan-sons':'卷45·袁象先传·二子','songshi-261-liu-chongjin-interpreter':'卷261·刘重进传·契丹通事','songshi-261-liu-chongjin-dengzhou':'卷261·刘重进传·汉初邓州','songshi-261-liu-chongjin-han-general':'卷261·刘重进传·乾祐末拒郭威','jiuwudaishi-103-guo-march':'卷103·隐帝本纪·郭威起兵与滑州','xinwudaishi-011-guo-march':'卷11·周本纪·郭威南下','songshi-461-zhao-xiuji-career':'卷461·赵修己传·离开李守贞至翰林天文','tongjian-289-950-guo-march':'卷289·乾祐三年·南下与禁军赏赐','jiuwudaishi-107-wang-zhang-finance':'卷107·王章传·财政措施','xinwudaishi-010-han-court-killings':'卷10·汉本纪·乾祐三年十一月','tongjian-289-950-ministers-conspiracy':'卷289·乾祐三年·诛杀计划及追述','tongjian-289-950-assassination-orders':'卷289·乾祐三年·丙子诛杀与密诏','jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十一月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_10_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=950, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='950年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_289_0950_' + code
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
        edge = 'participation_zztj_289_0950_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_289_0950_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'太后':'李氏（刘知远妻）','刘崇':'刘崇（刘知远弟）','刘信':'刘信（刘知远从弟）','勋':'刘承勋','赟':'刘赟','赵上交':'赵远','袁{山义}':'袁嶬','王殷':'王殷（后汉后周将）','王赟':'王赟（楚岳州刺史）','崔洪琏':'崔洪琏','硃进忠':'朱进忠','後匡赞':'后匡赞'})
NEW_ALIASES={'王度':[],'张永德':['張永德'],'许可琼':['許可瓊'],'李彦温':['李彥溫'],'韩礼':['韓禮'],'李洪信':['李洪信（保义节度使）']}
NEW_DESCRIPTIONS={
'王度':'后汉枢密直学士。950年与冯道、赵上交奉郭威奏请之命，到徐州迎接被选为嗣君的刘赟。是否与同名人物有关尚无证据，生卒年未载。',
'张永德':'阳曲人，郭威的女婿。950年任供奉官押班，奉命给昭义节度使常思送生日礼物；常思接到杀他的密诏后拘留观望，郭威取京师后释放并道歉。生卒年本批未录。',
'许可琼':'许德勋的儿子，楚国水军指挥使。950年受马希广命率五百艘战舰屯城北津，水军接连南津，由马希崇监军。生卒年未载。',
'李彦温':'楚国马军指挥使。950年受马希广命率骑兵屯驼口，控制湘阴道路。生卒年未载。',
'韩礼':'楚国步军指挥使。950年受马希广命率二千人屯杨柳桥，控制栅路。生卒年未载。',
'李洪信':'李业的兄长，950年任保义节度使。李业逃到陕州时，他不敢把李业藏在自己家中。生卒年未载。'}
old='jiuwudaishi-103-succession-regency';new='xinwudaishi-011-guo-march';chu='xinwudaishi-066-pushezhou';mar='songshi-255-zhang-yongde-marriage';det='songshi-255-zhang-yongde-detained'
add('dou_su_restored','郭威找到逃归的窦贞固、苏禹珪，恢复其职位',62,'窦贞固、苏禹珪','寻复其位。',[('窦贞固','自七里寨逃归后被找到并复位'),('苏禹珪','自七里寨逃归后被找到并复位'),('郭威','寻得二人，恢复职位')],when='950年十一月郭威入京后，具体复位日未载',place='京师',note='寻为随后，不虚构同日；未写二人此前已正式免官。')
claim('person',people['窦贞固'],'description','《资治通鉴》评价窦贞固在权臣及近侍作乱时，靠沉稳保全自己。',62,span(62,'贞固为相，','自全而已。'),'为史书评价，不能作为他从未参与政务的全面判断。')
add('han_coffin_moved','郭威命将刘承祐灵柩迁西宫',62,'郭威命有司','于西宫。',[('郭威','命主管部门迁灵柩'),('刘承祐','灵柩被迁西宫')],when='950年十一月郭威入京后，具体迁移日未载',place='西宫',note='梓宫为皇帝灵柩；本句未给西宫坐标。')
add('guo_refuses_lower_funeral','有人建议降格葬刘承祐，郭威拒绝',62,'或请如魏高贵乡公','况敢贬君乎！”',[('郭威','拒绝将葬礼降为公爵礼'),('刘承祐','成为所议葬礼的对象')],when='950年十一月，迁灵柩前后，具体日未载',place='京师',note='魏高贵乡公是类比旧例，不建立950年曹髦事件；拒绝降礼不等于本段已举行葬礼。')
add('feng_dao_guo_meet','冯道率百官见郭威，郭威仍向他行拜礼',62,'太师冯道','侍中此行不易！”',[('冯道','率百官来见，照平常接受拜礼'),('郭威','仍向冯道行拜礼')],when='950年十一月入京后、丁亥朝太后之前，具体日未载',place='京师',note='此行不易为话语，未猜讽刺或另立密谋关系。')
add('guo_petitions_successor','郭威丁亥率百官朝见李太后，请早立嗣君',62,'丁亥，','请早立嗣君。”',[('郭威','率百官见太后，请早立继承人'),('太后','收到立嗣请求')],when='950年十一月丁亥',place='明德门',note='起居为问安朝见，不写起床；本次未即选定具体人。')
add('lady_lists_candidates','李太后列刘崇、刘信、刘赟、刘承勋供百官议选',62,'太后诰称：','议择所宜。”',[('太后','下诰令百官议选四位宗室'),('刘崇','以河东节度使身份被列为候选'),('刘信','以忠武节度使身份被列为候选'),('赟','以武宁节度使身份被列为候选'),('勋','以开封尹身份被列为候选')],when='950年十一月丁亥朝见后至己丑定嗣前，具体诰下日未载',place='后汉朝廷',note='诰中称郭允明弑逆是诰令的罪名说法，与前段乱兵版本并存；称刘信为高祖弟与旧从弟身份不静默改为同胞。刘赟称子是高祖养视如子，亲生父亲刘崇另明记。')
family='赟，崇之子也，高祖爱之，养视如子。'
relationship('刘崇（刘知远弟）','刘赟','父亲',62,family,'刘崇是刘赟生父，复用已发表关系；崇沿后汉宗室，不与萧县同名合并。')
relationship('刘知远','刘赟','养父',62,family,'刘知远养视刘赟如子，复用养父关系，未取代亲生父亲；不虚构具体收养礼日期。')
add('chengxun_rejected_illness','郭威、王峻先请立刘承勋，太后展示其病重状况',62,'郭威、王峻入见','诸将乃信之。',[('郭威','请立刘承勋，向将领转达病情'),('王峻','共同请立刘承勋'),('太后','称刘承勋久病，令抬卧榻给诸将看'),('勋','因久病不能起，被抬示诸将')],when='950年十一月丁亥至己丑之间，具体议见日未载',place='万岁宫',note='久赢疾按久病虚弱解释，不诊断具体疾病；未写刘承勋已死。')
sup('chengxun_rejected_illness',62,old,'太后告以承勛羸病日久，不能自舉。周太祖與諸將請視承勛起居，及視之，方信，','《旧五代史》也记承勋久病不能起，郭威及诸将查看后相信。','双方关于议立、病情和查看相符，不补具体疾病。')
add('guo_wang_choose_yun','郭威与王峻转而商议立刘赟',62,'于是郭威','与峻议立赟。',[('郭威','与王峻议立刘赟'),('王峻','共同议定刘赟'),('赟','成为拟立嗣君')],when='950年十一月，查看刘承勋病情后、己丑表请前',place='后汉朝廷',note='议立阶段与表请下诰分开，未写刘赟已即位。')
add('lady_orders_yun_welcome','郭威己丑表请立刘赟，太后下诰择日备法驾迎立',62,'己丑，','迎赟即皇帝位。',[('郭威','率百官表请刘赟继位'),('太后','令择日备法驾迎刘赟'),('赟','获选为将迎来的嗣君')],when='950年十一月己丑',place='后汉朝廷、拟迎徐州',note='迎即位是诰令计划，此时刘赟未抵京，不能当已正式即位。')
sup('lady_orders_yun_welcome',62,old,'宜令所司擇日備法駕奉迎即皇帝位。','《旧五代史》己丑诰也命备法驾奉迎刘赟。','所司为主管部门，诰命不是实际即位完成。')
add('feng_wang_zhao_sent_xu','郭威奏派冯道、王度和赵上交到徐州迎刘赟',62,'郭威奏遣太师冯道','诣徐州奉迎。',[('郭威','奏请派三名使者迎嗣'),('冯道','以太师身份奉命迎接'),('王度','以枢密直学士身份奉命迎接'),('赵上交','以秘书监身份奉命迎接'),('赟','成为迎接对象')],when='950年十一月己丑迎立诰后，具体三使出发日未单列',place='京师至徐州',note='赵上交沿已有赵远改名主体，王度不因字近并为王溥；奉迎不是已接到人返京。')
sup('feng_wang_zhao_sent_xu',62,new,'庚寅，威率百官詣明德門，請立武寧軍節度使贇為嗣。遣太師馮道迎贇于徐州。','《新五代史》将表请与派冯道迎刘赟系于庚寅。','主书己丑表请后派三使，新史庚寅派冯道；时间与使者名单按各书保留，不强拆成两次同样迎接。',relation='conflicts',field='time_original')
add('guo_admires_fan_edicts','郭威讨三叛时得知诏书出自范质，称有宰相才',62,'郭威之讨三叛也，','宰相器也。”',[('郭威','赞赏军事诏令，向使者询问起草者'),('范质','被使者称为诏书起草人')],year=None,when='郭威讨三叛时期的追述，具体问答日未载',place='征军中，具体地点未载',note='使者未具名不建人物；宰相器是郭威评价，未当此次即正式拜相。')
add('guo_fan_robe_documents','郭威入京找到范质，赠紫袍并令草迎嗣文书',62,'入城，',None,[('郭威','寻得范质，解紫袍给他，委托起草诰令仪注'),('范质','起草太后诰令和迎新君仪注')],when='950年十一月郭威入京后，具体日未载',place='京师',note='大雪与给袍为原载，不反算气温；皆得其宜为史书评价，不说所有礼制细节已获现代核验。')
add('zhang_delivers_birthday','刘承祐派张永德给常思送生日礼物',63,'初，','常思生辰物。',[('刘承祐','派张永德送生辰礼'),('张永德','以供奉官押班身份赴昭义送礼'),('常思','成为生辰物受赠对象')],year=None,when='950年十一月杨邠等被杀之前的追述，具体出使起始未载',place='京师至昭义',note='初为此前出使，未给出发年；阳曲为张籍贯，不当作常思生辰地点。')
relationship('郭威','张永德','岳父',63,'永德，郭威之婿也，','郭威是张永德岳父；原文没有此女姓名，不补女儿人物或婚期。')
claim('person',people['张永德'],'description','《宋史》记郭威把女儿嫁给张永德，后来为其请授供奉官押班。',63,(sources[mar]/'source.txt').read_text().strip(),'郭威婚姻与张永德押班身份衔接，原文周祖指郭威；早期婚期未定，不强写950。',source=mar)
add('chang_detains_zhang','常思收到杀张永德的密诏，将张囚禁观望',63,'会杨邠等诛，','囚永德以观变，',[('常思','受杀人密诏后选择囚禁观望'),('张永德','因密诏被囚，未被立即杀害')],when='950年十一月杨邠等被杀之后、郭威入京之前',place='昭义',note='素闻多奇异为常思所闻背景，不当神迹事实；囚禁不等于密诏执行成功。')
sup('chang_detains_zhang',63,det,'遇以爲然，止令壯士嚴衛，然所以饋之甚厚。','《宋史》也记只派壮士严加看守并厚供饮食，所用潞帅姓名写常遇。','主书常思与宋传常遇按同一潞帅、张永德送生日礼及杀人密诏场景对应，字差保留，未将常遇另建同场人物。')
add('chang_releases_zhang','郭威占京师后，常思释放张永德并道歉',63,'及威克大梁，','释永德而谢之。',[('常思','释放张永德并致歉'),('张永德','获释')],when='950年十一月郭威入大梁以后，具体释放日未载',place='昭义',note='及克大梁是条件时序，不套郭威进城同日；未补郭威直接发释放令。')
add('guo_requests_lady_regency','郭威庚寅表请李太后在嗣君未至时临朝',63,'庚寅，',None,[('郭威','以嗣君抵京尚需时日为由，请太后临朝'),('太后','收到临朝请求')],when='950年十一月庚寅',place='后汉朝廷',note='浃旬是需时估计，不当作刘赟实际十日后即到；此是请求，壬辰始临朝另记。')
add('chu_siege_yutan','马希萼先派各族军围玉潭，朱进忠率兵会合',64,'先是，','引兵会之。',[('马希萼','派兵围玉潭'),('朱进忠','率兵与围军会合')],when='950年十一月辛卯至湘阴以前，具体围城起始未载',place='玉潭',note='先是为此前行动，未套辛卯起兵；相关各族未指现代民族。')
add('cui_defeated_returns_changsha','崔洪琏在玉潭战败，逃回长沙',64,'崔洪琏兵败，','奔还长沙。',[('崔洪琏','战败逃回长沙')],when='950年十一月辛卯以前，围玉潭后，具体日未载',place='玉潭至长沙',note='未记崔死，不推全军覆没或伤亡人数。')
add('ma_xie_attack_yuezhou','马希萼进攻岳州，王赟抵抗五日未被攻破',64,'希萼引兵继进，','五日不克。',[('马希萼','率兵攻岳州'),('王赟','以刺史身份抵抗')],when='950年十一月辛卯前，具体开始日未载，历五日不克',place='岳州',note='五日为攻而未克的时长，不据此反算起讫干支。')
add('wang_yun_urges_brothers_peace','王赟回应马希萼责问，劝马氏兄弟停止内斗',64,'希萼使人谓赟曰：','引兵去。',[('马希萼','遣人责王赟有二心，听其答复后撤兵'),('王赟','以父亲抗淮南经历为据，劝止兄弟争战')],when='950年十一月辛卯前，岳州攻五日未克之后',place='岳州',note='父亲在本句未具名，不猜父名；六破淮南为王赟陈述，不造六次独立战役。淮南坐收其利是其担忧，不是已发生占领。')
sup('wang_yun_urges_brothers_peace',64,chu,'願君王入長沙，不傷同氣，臣不敢不盡節。','《新五代史》也记王赟劝不要伤害兄弟，表示愿尽忠。','该传对话更简短，未据其沉默否定主书记父亲与淮南的细节。')
add('ma_xie_burns_xiangyin','马希萼辛卯到湘阴，焚烧抢掠后经过',64,'辛卯，','焚掠而过。',[('马希萼','率军经过湘阴并焚掠')],when='950年十一月辛卯',place='湘阴',note='未给房屋、财物或死伤数，不添城被完全焚毁。')
add('ma_xie_tun_xiangxi','马希萼到长沙屯湘西，步兵驻岳麓，朱进忠会合',64,'至长沙，',None,[('马希萼','军队在长沙湘江西侧驻扎'),('朱进忠','从玉潭率兵来会')],when='950年十一月辛卯过湘阴后，具体到达日未单列',place='长沙、湘西、岳麓',note='湘西是长沙湘江西侧语境，不套现代湘西自治州；军于驻扎未说此时已陷城。')
sup('ma_xie_tun_xiangxi',64,chu,'止長沙，[4]屯水西。','《新五代史》也记到长沙屯水西。','原注标记[4]保留，水西与主书湘西作同一驻军方向对照，未给坐标。')
add('xu_keqiong_water_defense','马希广命许可琼率五百艘战舰屯北津，并由马希崇监军',65,'马希广遣刘彦瑫','以马希崇为监军。',[('马希广','命召许可琼布置水军并设监军'),('刘彦瑫','奉命召水军指挥使'),('许可琼','率五百艘战舰屯城北津、连属南津'),('马希崇','受任监军')],when='950年十一月马希萼驻长沙后，具体部署日未载',place='长沙城北津至南津',note='五百为书载舰数，属于为接连，不译行政隶属于南津。')
add('li_yanwen_defends_tuokou','马希广命李彦温率骑兵屯驼口，扼守湘阴路',65,'又遣马军指挥使','扼湘阴路，',[('马希广','派骑兵守湘阴路'),('李彦温','率骑兵驻驼口')],when='950年十一月长沙部署防御时，具体日未载',place='驼口、湘阴路',note='骑兵数未载，不从水军舰数推人数。')
add('han_li_defends_bridge','马希广命韩礼率二千人守杨柳桥，控制栅路',65,'步军指挥使韩礼','扼栅路。',[('马希广','派步军守栅路'),('韩礼','率二千人屯杨柳桥')],when='950年十一月长沙部署防御时，具体日未载',place='杨柳桥、栅路',note='栅路沿史载称呼，不造现代坐标；二千为书载。')
relationship('许德勋','许可琼','父亲',65,'可琼，德勋之子也。','许德勋是许可琼父亲，德勋沿已有楚将主体；不据此新增母亲或生年。')
add('lady_begins_regency','李太后于壬辰开始临朝听政',66,'壬辰，','太后始临朝，',[('太后','开始临朝听政')],when='950年十一月壬辰',place='后汉朝廷',note='始临朝为实际开始，与前批庚寅请临朝分开。')
# Distinct appointments on the same day, with provisional authority kept explicit.
for code,name,title,start,end in [('wang_jun_privy','王峻','枢密使','以王峻','为枢密使，'),('yuan_xuanhui','袁嶬','宣徽南院使','袁{山义}','为宣徽南院使，'),('wang_yin_guard_all','王殷','侍卫马步军都指挥使','王殷','为侍卫马步军都指挥使，'),('guo_cavalry_command','郭崇威','侍卫马军都指挥使','郭崇威','为侍卫马军都指挥使，'),('cao_infantry_command','曹威','侍卫步军都指挥使','曹威','为侍卫步军都指挥使，'),('li_gu_three_offices','李谷','暂管三司','陈州刺史李谷','权判三司。')]:
 add(code,'李太后临朝后'+('令李谷暂管三司' if name=='李谷' else '任'+name+'为'+title),66,start,end,[('太后','临朝后作出职务安排'),(name,'受任'+title)],when='950年十一月壬辰',place='后汉朝廷',note='临朝后的任命由该段主语太后统摄；李谷权判是临时职掌，其他官号照书，不填现代军衔。')
sup('wang_jun_privy',66,old,'以宣徽南院使王峻為樞密使，','《旧五代史》也记王峻由宣徽南院使任枢密使。','旧本纪接在临朝诰后，未另写壬辰，不取上下其他日来替换主书壬辰。')
sup('li_gu_three_offices',66,old,'陳州刺史李穀權判三司，','《旧五代史》也记李谷暂管三司。','穀与谷沿既有同人规范，权判不写永久实任三司使。')
add('liu_li_executed_family_spared','刘铢与李洪建等被斩首示众，家属获赦免',67,'刘铢、李洪建','而赦其家。',[('刘铢','被斩首示众，家属获赦免'),('李洪建','被斩首示众，家属获赦免')],when='950年十一月壬辰临朝后条下，具体处决日未单列',place='京师市中',note='党未具名不造名单；处决与此前捕囚分开，家属获赦不推回恢复所有财产。')
for name in ['刘铢','李洪建']:
 claim('person',people[name],'death_year',name+'于950年十一月在市中被斩首示众。',67,'刘铢、李洪建及其党皆枭首于市，而赦其家。','具体处决日未单列，不把壬辰相邻日期强套。')
add('guo_refuses_family_revenge','郭威拒绝杀刘铢家属报仇，数家免遭杀害',67,'郭威谓公卿曰：','由是数家获免。',[('郭威','向公卿表示不应反复以灭家报仇')],when='950年十一月壬辰临朝后的善后阶段，具体发言日未载',place='京师',note='数家未具体列名，不把史书数家扩成所有涉案者完全赦免。')
add('wang_yin_pleads_li_failed','王殷多次请免李洪建死罪，郭威不许',67,'王殷屡为洪建','郭威不许。',[('王殷','为李洪建请免死'),('李洪建','成为求赦对象'),('郭威','不许免死')],when='950年十一月善后处决前的补述，具体请赦日未载',place='京师',note='虽然写在处决之后，求免死逻辑上属于处决前，不倒写死后再处死；主书没有把原因明说为前批救家报恩。')
add('murong_delivers_hou_kuangzan','后匡赞到兖州后被慕容彦超抓获并送交',67,'後匡赞至兗州，','执而献之。',[('后匡赞','到兖州被抓获'),('慕容彦超','抓获后匡赞并送交')],when='950年十一月后匡赞逃兖州之后，具体抓获日未载',place='兖州',note='献之承朝廷或郭威方面语境，未明具体收领官与交接日，不提前造后匡赞死亡。')
add('li_hongxin_refuses_hiding','李业到陕州，兄长李洪信不敢藏匿他',67,'李业至陕州，','不敢匿于家。',[('李业','逃到陕州，希望藏身'),('李洪信','以保义节度使身份不敢将弟弟藏家')],when='950年十一月李业逃离京师后，具体到达日未载',place='陕州',note='原文只说不敢匿于家，未写兄长告发或派人杀他。')
relationship('李洪信','李业','兄长',67,'其兄保义节度使洪信不敢匿于家。','其兄指李业兄长，方向明确，不据此推李洪信与其他李氏兄弟的出生先后。')
add('li_ye_killed_jiangzhou','李业带金欲逃晋阳，到绛州被盗贼杀死',67,'业怀金',None,[('李业','带金欲逃晋阳，途中被盗贼杀死抢金')],when='950年十一月逃到陕州后，具体被杀日未载',place='绛州',note='晋阳是目标未到；盗贼未具名，不补派遣者或数额。')
claim('person',people['李业'],'death_year','李业于950年逃到绛州时被盗贼杀死并抢走金钱。',67,'业怀金将奔晋阳，至绛州，盗杀之而取其金。','死亡地点为绛州，不是拟逃晋阳；确日未载。')
add('tian_returns_shu_executed','田行皋逃荆南，被高保融送回后蜀处死',68,'蜀施州刺史',None,[('田行皋','逃荆南，被送回后蜀处死'),('高保融','认为田不忠，抓获送回后蜀')],when='950年十一月条下，具体逃亡与处决日未载',place='施州、荆南、后蜀',note='高保融所言为对田忠诚的判断，不单据话语推现代罪名；伏诛是被处死，未具名后蜀执行者不补。')
claim('person',people['田行皋'],'death_year','田行皋于950年逃荆南后被送回后蜀处死。',68,Q[68]['text'],'具体日未载，沿既有施州刺史主体；不把高保融送回写成亲手处决。')
reviews={62:'两相逃归复位、帝棺及礼议、冯见、丁亥朝太后、候选诰、勋病议弃、己丑定赟和迎使、范追述与赠袍草令分开。刘赟未实际即位，亲生与养父复用；刘信诰称弟与既有从弟不强改同胞。新本纪庚寅迎赟时序并列。',63:'张永德先前送礼、密诏囚与取京后释放分开，初出使起始未知年null。郭岳父有原婿证，宋传常遇与主常思同场异字保留。庚寅请临朝不是已临朝。',64:'先前围玉潭、崔敗归、岳州五日不克、王答话撤军、辛卯湘阴焚掠、长沙西岸驻军分录。王父未具名不造主体，六破为其陈述不造六役，湘西不套现代自治州。',65:'水军、骑兵、步兵三路部署分别记，五百舰与二千兵不混单位，监军实际任命、属于水路接连明确。许德勋父亲方向清楚。',66:'壬辰始临朝与庚寅请临朝分开，六职分录，李谷权判为临时；旧史用郭崇曹英等异名不新合并，袁仍复用前批嶬。',67:'处决与获赦分开，王求免死为处决前补述。郭拒灭家不是所有党人赦免；后匡赞擒献不造死亡，李业陕州避藏与绛州被盗杀分开，晋阳未到。',68:'田行皋逃荆南、被执送蜀、伏诛连载，未点后蜀执行人，高保融判断为话语。'}
assert not (P/'publication.json').exists()
for n in range(62,69):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(62,69)],next_paragraph=Q[69]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原67—73行连续七段；发布后首68/83正文已录，余15段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(62,69)],source_issues_review='定赟与迎使日旧新并列，临朝实际壬辰沿主书；宋张传常遇与主常思异字，同一职务与生日礼诏杀场景对应。太后诰称郭允明弑逆属声明，前条乱兵版本不改。刘信从弟称谓、郭崇曹英异名保留既有主体，未静默并人。纸本及转录异文待核。',plain_language_review='首次检查现代白话、明确主体、职掌与亲属方向、时间和原文。继承拟议、奉迎、请求临朝与实际临朝分开；复仇言辞与执行结果分开。原文原字保留，展示使用可读规范名。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
