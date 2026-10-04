# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 943 paragraphs 17–24."""
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
COMMIT='536806e05eea577781a96322d189bed7fc5e7ec1'
specs=[(d.name,d,COMMIT,'欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-943-april-may','xinwudaishi-065-liu-sheng-accession','xinwudaishi-009-943-return','xinwudaishi-062-jing-brothers']:
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
main_sources = ['tongjian-283-943-april-may']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0943-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-068-wang-tan-grave':'卷68·闽世家·王倓被辱尸','xinwudaishi-068-chen-guangyi':'卷68·闽世家·陈光逸谏死','xinwudaishi-067-wuyue-generals':'卷67·吴越世家·章德安等将领'}
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    for a,b in [('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'xinwudaishi-068-wang-tan-grave':'卷68·闽世家·王倓被辱尸','xinwudaishi-068-chen-guangyi':'卷68·闽世家·陈光逸谏死','xinwudaishi-067-wuyue-generals':'卷67·吴越世家·章德安等将领'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '四月至七月条下及追述'
        citation = f'卷283·后晋天福八年（943；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0943_03_{len(B["claims"])+1:04d}'
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
 E[code]=ev(code,title,n,start,end,actors,**kw)
 return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
ALIASES.update({'帝':'石重贵','唐主':'李璟','汉主':'刘弘熙','弘杲':'刘弘杲','弘昌':'刘弘昌','弘弼':'刘弘弼','曦':'王延羲','康宗':'王继鹏','弘佐':'钱弘佐','景遂':'徐景遂','景达':'徐景达','弘冀':'李弘冀','公鐸':'贾公铎'})
NEW_ALIASES={'王倓':[],'陈光逸':['陳光逸'],'阚璠':['闞璠'],'李文庆':['李文慶'],'胡进思':['胡進思'],'李弘冀':['弘冀','李冀'],'贾匡浩':['賈匡浩']}
NEW_DESCRIPTIONS={
'王倓':'闽国同平章事，曾在王继鹏宴席上说新罗所献宝剑可以斩不忠的人，王延羲听后变色。王倓死后，王延羲在943年条下因又见献剑而命掘墓辱尸。《资治通鉴》后句转录为校冢，据同段前文与《新五代史》王倓明确校核主体，原字保留。生卒年月尚未核。',
'陈光逸':'闽国校书郎。943年条下记他不顾朋友劝阻，上书列王延羲五十项罪恶，随后被鞭打并悬吊致死。《新五代史》作五十余事，鞭打次数也有差异，两书分别保留。出生年未载。',
'阚璠':'明州人，吴越上统军使。钱弘佐初立时，史书说他排斥异己，钱弘佐不能制约；943年章德安、李文庆被贬后，他与胡进思更为专横。人物评价按史书归属保留，生卒年尚未核。',
'李文庆':'睦州人，吴越内牙右都监使。因不依附阚璠，943年七月乙巳被贬到睦州。生卒年未载。',
'胡进思':'湖州人，吴越右统军使。943年条下记章德安与李文庆被贬后，史书称他与阚璠更加专横。生卒年尚未核。',
'李弘冀':'李璟的长子。943年七月条下被立为南昌王。姓名在《资治通鉴》作弘冀，《新五代史》同一册封作冀；沿用同一主体，不因姓名省写再建李冀。生卒年尚未核。',
'贾匡浩':'贾公铎的儿子，南唐百胜节度使。943年张遇贤转向虔州时，史书说他未作防备，部属接连战败，虔州城门白昼也关闭。生卒年未载。'}
# 17: taking the outer western district is distinct from taking Fuzhou itself.
add('chen_attacks_fuzhou','殷将陈望等进攻福州，进入西侧外城',17,'殷将','入其西郛，',[('陈望','率殷军进攻福州，进入西侧外城')],when='943年四月条下，具体日期未载',place='福州',note='入西郛不等于攻克整座福州，其他将领未具名。')
add('chen_retreats_fuzhou','陈望等攻福州后战败退回',17,'既而',None,[('陈望','进攻福州后战败退回')],when='943年四月条下，入西郛之后，具体日期未载',place='福州',note='退回地点与战斗次数未载，不补回到建州或新的军队人数。')
# 18: ten accusations stay attached to the single petition and to its speaker.
add('pan_ten_point_petition','潘承祐向王延政上书，提出十项批评',18,'五月，','十也。”',[('潘承祐','以吏部尚书、同平章事身份上书提出十项批评'),('王延政','收到潘承祐上书批评')],when='943年五月，具体日期未载',place='殷国',note='十事为同一奏疏各项主张，不拆十次上书；各项批评作为潘承祐的说法，未自动视为独立事实已核。')
issues=[('兄弟相攻','一也。','潘承祐批评王延政与兄长相互攻打。'),('赋敛烦重，','二也。','潘承祐批评赋税繁重、劳役没有节制。'),('发民为兵，','三也。','潘承祐批评征百姓为兵，使在外之人愁怨。'),('杨思恭夺','四也。','潘承祐指责杨思恭夺百姓衣食，导致百姓怨恨君主，而臣下不敢说。'),('疆土狭隘，','五也。','潘承祐认为国土狭小却多设州县，会增添官吏、困扰百姓。'),('除道裹粮，','六也。','潘承祐批评准备攻临汀时没有防范南唐与吴越乘虚进攻。'),('括高赀户，','七也。','潘承祐批评按财产征发富户、以财补官，不能缴纳者受刑。'),('延平诸津，','八也。','潘承祐批评在延平渡口向果菜鱼米征税，获利很少而招致很多怨恨。'),('与唐、吴越为邻，','九也。','潘承祐批评王延政即位以来尚未与邻国南唐、吴越通使。'),('宫室台榭，','十也。','潘承祐批评宫室楼台装饰没有节制。')]
for start,end,text in issues:
 claim('event',E['pan_ten_point_petition'],'description',text,18,span(18,start,end),'这是潘承祐上书所述批评，不另外补执行日期、民众数量、具体税额或已发生的南唐吴越袭击。')
add('pan_dismissed','王延政削去潘承祐官爵，命他回家',18,'殷王',None,[('王延政','因上书而生气，削去潘承祐官爵，命其回私宅'),('潘承祐','被削官爵并命回私宅')],when='943年五月，上书之后，具体日期未载',place='殷国',note='勒归私第不改写为处死、流放或囚禁。')
# 19: changed sovereign identity, proposed execution, accusations and actual death.
m=dict(when='943年五月条后，确切月日未载',place='南汉')
add('honggao_requests_assassins_death','刘弘杲请求处死刘思潮等，刘弘熙不接受',19,'汉中宗','汉主不从。',[('弘杲','因新君即位后议论纷纷，请求处死刘思潮等'),('汉主','拒绝刘弘杲请求')],note='汉主已是刘弘熙，即刘晟，不是上批被杀的刘弘度；不把请求斩首记作已执行。',**m)
add('sichao_accuses_honggao','刘思潮等指控刘弘杲谋反，刘弘熙命他们监视他',19,'思潮等闻之，','令思潮等伺之。',[('刘思潮','指控刘弘杲谋反，并受命监视他'),('弘杲','被指控谋反'),('汉主','命刘思潮等监视刘弘杲')],note='谮为史书记载的诬告，不能改成刘弘杲谋反已被证实。',**m)
add('honggao_killed','刘思潮、谭令禋率卫兵闯入宴席，杀死刘弘杲',19,'弘杲方宴客，','斩弘杲。',[('弘杲','在宴客时被杀'),('刘思潮','与谭令禋率卫兵闯入，杀死刘弘杲'),('谭令禋','与刘思潮率卫兵闯入，杀死刘弘杲')],note='未列卫兵人数；此句主书未写君主明确下达斩令，不补精确杀人诏书。',**m)
add('sheng_plans_kill_brothers','刘弘熙打算杀尽弟弟们，尤其猜忌刘弘昌',19,'于是汉主','尤忌之。',[('汉主','打算杀尽弟弟们，尤其猜忌刘弘昌'),('弘昌','因有声望而受到刘弘熙猜忌')],note='谋尽诛是计划，不推所有弟弟已在此段被杀；贤而得众为史书评价。',**m)
add('hongbi_requests_court','刘弘弼害怕受祸，请求入朝，刘弘熙准许',19,'雄武节度使',None,[('弘弼','任雄武节度使、封齐王，因害怕受祸而请求入朝'),('汉主','准许刘弘弼入朝')],note='求与许为请求及批准，本句没有实际抵达日期。',**m)
sheng='xinwudaishi-065-liu-sheng-accession'
sup('honggao_requests_assassins_death',19,sheng,'已而洪杲屢請討賊，陰勸晟誅思潮等以止外議。','《新五代史》记刘弘杲多次请求讨贼，暗劝刘晟诛刘思潮等以止议论。','屡请的次数和日期未载，与当前建议相连。')
sup('honggao_killed',19,sheng,'晟大怒，使使者夜召洪杲。','《新五代史》记刘晟生气，派使者夜召刘弘杲。','与通鉴宴席遭突入场景不同，各记叙述并列，不能用一书细节填成唯一混合场景。',relation='conflicts')
sup('honggao_killed',19,sheng,'然後赴召，至則殺之。','《新五代史》记刘弘杲与家人诀别后赴召，到达后被杀。','主书记在宴客时被刘思潮、谭令禋杀死，死亡场景分别保留。',relation='conflicts')
claim('person',people['刘弘杲'],'death_year','刘弘杲于943年被杀，确切月日未载。',19,'弘杲方宴客，思潮与谭令禋帅卫兵突入，斩弘杲。','复用已有刘弘杲，不从建议被拒误推未死；死亡场景的异说分别引用。')
# 20: earlier banquet and corpse desecration, then contemporary remonstrance.
add('wang_tan_sword_remark','王倓在王继鹏宴席上说宝剑可斩不忠的人，王延羲听后变色',20,'初，','凛然变色。',[('康宗','在宴席上展示新罗献剑，询问王倓用途'),('王倓','回答宝剑可斩不忠之臣'),('曦','听到回答后变色')],year=None,when='王继鹏在位时的一次宴席，具体年月未载',place='闽国',note='初为追述；王延羲已有异志是史书解释，不推当时已发生篡位。')
add('wang_tan_grave_desecrated','王延羲因再见献剑，命掘王倓墓并斩其尸',20,'至是宴群臣，','斩其尸。',[('曦','在又有人献剑时，命人掘王倓墓、斩其尸')],when='943年五月条后，确切月日未载',place='闽国',note='底本作校冢，结合前文王倓与新五代史倓已死、发冢戮尸校核为王倓墓，原字不改。辱尸不是此时新杀王倓，死亡年不推943。')
wt='xinwudaishi-068-wang-tan-grave'
sup('wang_tan_sword_remark',20,wt,'倓曰：「不忠不孝者，斬之。」曦居旁色變。','《新五代史》记王倓说宝剑可斩不忠不孝的人，王延羲在旁变色。','主书只写不忠，所引话语范围有差别，分别保留。',relation='adds')
sup('wang_tan_grave_desecrated',20,wt,'曦既立，而新羅復獻劍，曦思倓前言，而倓已死，命發冢戮其尸，','《新五代史》明确王倓已死，王延羲又见新罗献剑后命掘墓辱尸。','支持校冢人物校读；不把后文面如生血流叙述解释成死者复活，也不补死亡年份。',relation='adds')
add('chen_guangyi_resolves_remonstrance','陈光逸认为王延羲将亡，决心劝谏，不听朋友阻止',20,'校书郎','不从；',[('陈光逸','认为君主失德将亡，打算以死劝谏，拒绝朋友阻止')],when='943年五月条后，上书之前，确切月日未载',place='闽国',note='亡无日矣为陈光逸判断，不提前将闽亡记成已经发生。朋友未具名。')
add('chen_guangyi_petition','陈光逸上书列出王延羲五十项罪恶',20,'上书陈','大恶五十事。',[('陈光逸','上书批评王延羲五十项罪恶'),('曦','受到陈光逸上书批评')],when='943年五月条后，确切月日未载',place='闽国',note='五十事为主书记数，具体全文未载，不自行补出五十条罪目。')
add('chen_guangyi_whipped','王延羲命卫士鞭打陈光逸数百次，陈光逸未死',20,'曦怒，','不死；',[('曦','生气，命卫士鞭打陈光逸'),('陈光逸','遭数百次鞭打后仍未死')],when='943年陈光逸上书后，确切月日未载',place='闽国',note='数百为原记概数，不补精确次数；此阶段明确不死，后句另录死亡。')
add('chen_guangyi_hanged','王延羲命人将陈光逸悬吊在庭树上，陈光逸随后死亡',20,'以绳系',None,[('曦','命人以绳系住陈光逸的颈部，悬吊在庭树上'),('陈光逸','被悬吊后死亡')],when='943年上述鞭打后，确切月日未载',place='闽国庭院',note='久之未给时长，不换算具体小时，未记纸本影印已核。')
cg='xinwudaishi-068-chen-guangyi'
sup('chen_guangyi_petition',20,cg,'校書郎陳光逸上書疏曦過惡五十餘事，','《新五代史》记陈光逸上书列出王延羲五十余项过恶。','主书五十事与新史五十余事分别保留，不擅统一数字。',relation='conflicts')
sup('chen_guangyi_whipped',20,cg,'曦命衞士鞭之百而不死，','《新五代史》记鞭打一百次而未死。','通鉴数百与新史百的次数不同，原文保留，纸本待核。',relation='conflicts')
sup('chen_guangyi_hanged',20,cg,'以繩係頸，掛于木，久而乃絕。','《新五代史》也记以绳系颈、挂树，随后死亡。','不补具体持续时间。')
for x in B['people']:
 if x['name']=='陈光逸':
  x['death_year']=943
  claim('person',x['key'],'death_year','陈光逸于943年上书劝谏后遭悬吊致死。',20,span(20,'曦怒，',None),'死亡明确，确切月日和出生年未载。')
# 21: a July dispatch, with independently dated June requisition kept separate.
add('jin_july_grain_dispatch','后晋因饥荒和国用不足，派六十余名使者征取民间粮食',21,'秋，',None,[('帝','下诏分派六十余使者到各道征取民间粮食')],when='943年七月己丑',place='后晋各道',note='六十余是使者人数，不是征粮数量；括是征取，不能写普通市场购粮。')
ann='xinwudaishi-009-943-return'
E['jin_june_grain_requisition']=event('jin_june_grain_requisition','《新五代史》记后晋六月征借民粮，并杀死藏粮者',21,'辛未，括借民粟，殺藏粟者。',[('帝','征借民间粮食，并杀死藏粮者')],when='943年六月辛未',place='后晋',source=ann,note='六月日期是新史该句所在月份，独立记录，不与主书七月己丑使者出发硬合成同日；人数未载。')
# 22: earlier disputes and two dated demotions; destinations conflict across books.
add('kan_excludes_opponents','钱弘佐初立时，阚璠排斥异己，钱弘佐不能制约他',22,'吴越王','弘佐不能制；',[('弘佐','刚即位时不能制约阚璠'),('阚璠','任上统军使，排斥与他意见不同的人')],year=None,when='钱弘佐初即位时期，具体年月未载',place='吴越',note='初立为941年起的背景，不把持续行为强定某一天；强戾为史书评价。')
add('zhang_dean_contends_kan','章德安多次与阚璠争执，李文庆不依附阚璠',22,'内牙上','不附于璠，',[('章德安','任内牙上都监使，多次与阚璠争执'),('李文庆','任右都监使，不依附阚璠'),('阚璠','与章德安多次争执')],year=None,when='943年七月贬官之前，具体年月未载',place='吴越',note='数争未给次数，不推实际武力斗争或另造结盟关系。')
add('zhang_dean_demoted','章德安被贬到处州',22,'乙巳，','贬德安于处州，',[('章德安','被贬到处州')],when='943年七月乙巳',place='处州',note='主书未具名处分者，新史明确钱弘佐黜将，另作补证；处州与新史明州异说保留。')
add('li_wenqing_demoted','李文庆被贬到睦州',22,'文庆于','睦州。',[('李文庆','被贬到睦州')],when='943年七月乙巳',place='睦州')
add('kan_hu_power','章德安、李文庆被贬后，史书称阚璠与胡进思更加专横',22,'璠与','益专横。',[('阚璠','在两人被贬后，被史书评价为更加专横'),('胡进思','任右统军使，与阚璠被史书评价为更加专横')],when='943年七月两人被贬后，具体日期未载',place='吴越',note='专横是史书评价，不推明确新任命、谋反或已杀钱弘佐。')
wuyue='xinwudaishi-067-wuyue-generals'
sup('zhang_dean_demoted',22,wuyue,'佐乃黜其大將章德安於明州、','《新五代史》记钱弘佐将章德安贬到明州。','通鉴作处州、新史作明州，主语新史明确钱弘佐；地点并列待核，不覆盖主书地点。',relation='conflicts')
sup('li_wenqing_demoted',22,wuyue,'李文慶於睦州，','《新五代史》也记李文庆被贬睦州。','该句未给日期，不擅补成新史也明确乙巳。')
# 23: promises of succession do not become actual transfer of the throne.
tang=dict(when='943年七月条下，具体日期未载',place='南唐')
add('jingsui_qiwang_marshal','李璟任徐景遂为诸道兵马元帅，改封齐王，居东宫',23,'唐主缘','居东宫；',[('唐主','按先帝意愿任景遂为诸道兵马元帅、改齐王、居东宫'),('景遂','由燕王、天雄节度使兼中书令和金陵尹获新任命')],note='缘烈祖意为主书任命理由，东宫与正式册皇太弟区分，不提前后来太弟事件。',**tang)
add('jingda_yanwang_deputy','李璟任李景达为副元帅，改封燕王',23,'天平节度使','徙封燕王；',[('唐主','任景达为副元帅，改封燕王'),('景达','由鄂王、天平节度使、守侍中和东都留守获新任命')],**tang)
add('jing_promises_succession_brothers','李璟向内外宣布，约定以后将帝位传给弟弟',23,'宣告中外，','约以传位。',[('唐主','向内外宣布以弟弟继承帝位的约定')],note='约以传位为未来安排，不记已退位，具体兄弟顺序由新史兄弟世世继立补述。',**tang)
add('hongji_nanchang_wang','李璟立长子李弘冀为南昌王',23,'立长子','为南昌王。',[('唐主','立长子弘冀为南昌王'),('弘冀','被立为南昌王')],**tang)
add('brothers_decline_appointments','徐景遂、李景达坚决辞让，李璟不准',23,'景遂、','不许。',[('景遂','与景达坚决辞让'),('景达','与景遂坚决辞让'),('唐主','不准两人辞让')],note='原文未逐项划分所辞职爵，不把每种任命都虚构一次拒绝。',**tang)
add('jingsui_retreat_name','徐景遂发誓不愿作继承人，改字退身',23,'景遂自誓',None,[('景遂','发誓不敢为继承人，并将字改为退身')],note='退身是字，不是改名或当时已经退官。',**tang)
succ='xinwudaishi-062-jing-brothers'
sup('jingsui_qiwang_marshal',23,succ,'秋，改封景遂齊王、諸道兵馬元帥、太尉、中書令，','《新五代史》也记秋季景遂改封齐王、任诸道兵马元帅，并列太尉、中书令。','补太尉职衔，未给日；只用于同一秋季变动，不覆盖主书既有职衔。',relation='adds')
sup('jingda_yanwang_deputy',23,succ,'景達為燕王、副元帥，','《新五代史》也记景达任燕王、副元帅。','同一改封任官。')
sup('jing_promises_succession_brothers',23,succ,'盟於昪柩前，約兄弟世世繼立。','《新五代史》记在李昪灵柩前盟约，约兄弟世代相继。','补盟约场所与表述，不能自动记作帝位已经转移。',relation='adds')
sup('hongji_nanchang_wang',23,succ,'封其子冀南昌王、江都尹。','《新五代史》将弘冀省写为冀，记封南昌王、江都尹。','冀与长子弘冀同人，补江都尹职衔，不反推出生年龄。',relation='adds')
relationship('唐主','弘冀','父亲',23,'立长子弘冀为南昌王。','唐主为李璟，长子身份明确，方向为李璟是李弘冀的父亲。')
# 24: cult utterances are reports; troops, outcome and fatherhood retain exact support.
add('wan_defeats_zhang_xunzhou','万景忻在循州击败张遇贤',24,'汉指挥使','于循州。',[('万景忻','任南汉指挥使，在循州击败张遇贤'),('张遇贤','在循州被万景忻击败')],when='943年七月条下，具体日期未载',place='循州')
add('zhang_oracle_qianzhou','史书记张遇贤求问神灵，得到夺取虔州的指示',24,'遇贤告','则大事可成。”',[('张遇贤','史书记他求问神灵，得到转攻虔州的指示')],when='943年循州战败后，具体日期未载',place='地点未载',note='神言是史载传闻，不建神灵人物，也不确认占验有效。')
add('zhang_crosses_ridge','张遇贤率部翻越山岭，转向虔州',24,'遇贤帅众','趣虔州。',[('张遇贤','率众翻越山岭，前往虔州')],when='943年循州战败后，具体日期未载',place='前往虔州的途中',note='逾岭未给具体山岭名，不推行军路线、坐标或逐日距离。')
add('zhang_takes_counties','贾匡浩未作防备，张遇贤部众攻陷虔州辖内多县',24,'唐百胜','攻陷诸县，',[('贾匡浩','任百胜节度使，未作防备'),('张遇贤','以史载十余万部众攻陷多县')],when='943年转向虔州后，具体日期未载',place='虔州辖内县名未载',note='十余万为史书记数，不扩展成精确实测军额；诸县未具名不补县城列表。')
add('zhang_twice_defeats_qianzhou','张遇贤两次击败州兵，虔州城门白昼也关闭',24,'再败州兵，','城门昼闭。',[('张遇贤','两次击败虔州州兵')],when='943年上述攻陷诸县后，具体日期未载',place='虔州',note='再败为两次击败，仅有概述，不造两场没有日期和细节的不同战役，也不写虔州州城已被攻克。')
add('zhang_builds_baiyun_base','张遇贤在白云洞修建宫室和军署',24,'遇贤作','于白云洞，',[('张遇贤','在白云洞修建宫室和军署')],when='943年进攻虔州期间，具体日期未载',place='白云洞',note='白云洞只写史载地名，不猜现代具体洞址。')
add('zhang_sends_raids','张遇贤派将领四出抢掠',24,'遣将','四出剽掠。',[('张遇贤','派将领四处抢掠')],when='943年建立白云洞据点期间，具体日期未载',place='虔州周边',note='将领与抢掠具体地名未给，不补人物或民众伤亡数量。')
relationship('公鐸','贾匡浩','父亲',24,'匡浩，公鐸之子也。','同段贾匡浩与贾公铎父子明确，复用已有贾公铎；原文鐸保留。')
reviews={17:'进入西郛与战败退回分开，不等于福州整城被攻克。',18:'单次奏疏十项批评以独立事实说明归于潘承祐，不造十次奏事；削官爵勒归不改为处死。',19:'汉主是刘弘熙，建议杀功臣被拒、诬告、监视、宴中杀弘杲、计划杀诸弟及准弘弼入朝分开。新史夜召赴召与主书宴客死亡场景异说并列。',20:'王倓旧宴为追述，校冢据前文及新史校核王倓墓，辱尸不反推943新死。陈光逸决谏、奏书、鞭打未死及悬吊死分开；五十与五十余、数百与百分别保留。',21:'主书七月己丑六十余使者征粮，新史六月辛未括借杀藏粮者作为独立补充，不合成同日，也不造人数。',22:'吴越初立争执为背景未知日，七月乙巳两贬官分别录。处州明州地点异说保留，新史随后阚璠被杀留后续连续段，不提前。',23:'任元帅改封王居东宫、未来传位约定、弘冀封王与辞让、更字退身分开，不提前册皇太弟。新史独立补太尉、柩前盟与江都尹。',24:'循州败、神言转向虔州、越岭、诸县陷与两败州兵、白云洞建设和抢掠分开。神言为传闻，军额保史数，未写州城被克，贾父子明确。'}
assert not (P/'publication.json').exists()
for n in range(17,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=283,year=943,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=283,next_year=943,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key='xinwudaishi-067-wuyue-generals',note='只引章德安和李文庆被贬地点，随后阚璠杜昭达被杀不提前录。')],coverage='连续第17—24段，原65—72行；四月至七月及追述，后接第25段八月李景逷封王。',source_issues_review='章德安被贬处州与明州、陈光逸奏疏和受鞭次数、刘弘杲被杀场景分别保留；校冢人物按同段及新史校核王倓，原字不改，纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],plain_language_review='首次核对标题正文、人物介绍、参与动作、关系与事实说明；奏疏及史书评价注明来源，神言为传闻，未知旧事日期为空，计划与执行、辱尸与新杀分开。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
