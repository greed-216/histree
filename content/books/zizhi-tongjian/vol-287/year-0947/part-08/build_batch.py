# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 57–64."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,76))
COMMIT='0f1d6c9bd1b9ff16f38ede170b876175e94606eb'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-september-siege','jiuwudaishi-100-october-siege','xinwudaishi-067-qian-zong-succession']:
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
main_sources = ['tongjian-287-947-september-siege']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p057-p064',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/287.txt').read_text().splitlines()
for n in range(57, 65):
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
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷287·天福十二年（947年十月至十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_08_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_287_0947_' + code
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
        edge = 'participation_zztj_287_0947_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_287_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','重威':'杜重威','彦超':'慕容彦超','行周':'高行周','张琏':'张琏（幽州军指挥使）','弘琏':'杜弘琏','石氏':'乐平长公主（杜重威妻）','弘倧':'钱弘倧','弘踧':'钱弘倧','蜀主':'孟昶'})
NEW_ALIASES={'陈观':['陳觀'],'韩训':['韓訓'],'王敏（杜重威判官）':['王敏（金乡）'],'杜弘琏':['杜弘璉'],'吴崇恽':['吳崇惲'],'李廷珪':[]}
NEW_DESCRIPTIONS={'陈观':'后汉给事中。947年十月刘知远亲征邺都时，派他入城向杜重威宣谕归降，杜重威闭门拒绝。生卒年未载。','韩训':'后汉内殿直。947年十一月向刘知远献攻城器具，刘知远回应城池依赖众人之心，认为器具不是关键。生卒年未载。','王敏（杜重威判官）':'金乡人，杜重威的观察判官。947年杜重威叛乱时屡次哭谏，未获听从；邺都粮尽后奉杜重威表出城请降。《旧五代史》职名作节度判官。生卒年未载。','杜弘琏':'杜重威之子。947年十一月乙亥出邺都见刘知远，参与父亲出降前的接洽。对应接洽在《旧五代史》杜重威传中写作宏遂，姓名差异保留；不与已录质子杜弘璲直接合并。生卒年尚未录入。','吴崇恽':'后蜀将领。947年以雄武都押牙身份带王处回书信招侯益归蜀。《宋史》侯益传记他为侯益旧属、秦州押衙，后任绵州刺史，受孟昶派遣厚赠侯益；职名按出处分别保留。生卒年未载。','李廷珪':'后蜀将领。947年十二月任奉銮肃卫都虞候，率二万兵出子午谷援长安。生卒年尚未录入。'}
ALIASES['王敏']='王敏（杜重威判官）'
du='jiuwudaishi-109-du-surrender';wife='jiuwudaishi-109-du-wife';nov='jiuwudaishi-100-november-surrender';dec='jiuwudaishi-100-december-return';october='jiuwudaishi-100-october-siege';qian='xinwudaishi-067-qian-zong-succession';hou='songshi-254-hou-yi-shu';han='songshi-479-han-baozhen-campaign'
t='947年十月，具体日未载';n='947年十一月，具体日未载';z='947年十二月，具体日未载'
add('du_refuses_chen_guan','杜重威曾称刘知远到来就投降，却闭门拒绝陈观宣谕',57,'杜重威声言','重威复闭门拒之。',[('重威','先声称车驾至即降，后闭门拒绝使者'),('帝','派陈观前往宣谕'),('陈观','以给事中身份前往宣谕')],when=t,place='邺都',note='声言投降与实际拒使分别表明，不能把此阶段写成已归降。')
sup('du_refuses_chen_guan',57,du,'十月，高祖親征，車駕至鄴城之下，遣給事中陳觀等賫詔入城，許其歸命，重威不納。','《旧五代史》杜重威传同记十月刘知远派陈观等携诏宣谕，杜重威不接受。','独立传记补明携诏，未明载此次使者被杀，不造死亡事件。')
add('ye_food_dwindles_desertions','邺都粮食渐尽，许多将士出城归降',57,'城中食浸竭，','将士多出降者。',[],when=t,place='邺都',note='多为概数，未具名；此阶段部分人出降不等于杜重威本人已降。')
add('murong_wins_assault_order','慕容彦超坚持攻城，刘知远同意',57,'慕容彦超固请','帝从之。',[('彦超','坚持请求攻城'),('帝','同意攻城')],when='947年十月丙午攻城之前，具体请求日未载',place='邺都军营')
add('liu_failed_assault_ye','刘知远督军攻邺都失败，伤者万余、死者千余',57,'丙午，','彦超乃不敢复言。',[('帝','亲督诸将攻城，未克后停止'),('彦超','攻城失败后不敢再主张急攻')],when='947年十月丙午，自寅至辰',place='邺都城下',note='万余伤者和千余死者为通鉴分别列出的约数，不当精确统计；只记寅至辰，不换算现代时长。')
sup('liu_failed_assault_ye',57,october,'丙午，詔都部署高行周督眾攻城，帝登高阜以觀之，時眾議未欲攻擊，副部署慕容彥超堅請攻之。是日，王師傷夷者萬餘人，不克而退。','《旧五代史》本纪同记丙午攻城失败，记刘知远登高观看、高行周督众、慕容彦超坚请攻城，伤夷万余。','伤夷的死伤范围不能直接当作通鉴单列伤者的独立精确确证；该句未列死者千余，保留两书表述范围。',relation='adds')
add('khitan_leaves_youzhou_garrison','契丹曾留一千五百名幽州兵驻守大梁',58,'初，契丹留','戍大梁。',[],when='947年契丹占据大梁期间，具体驻留日未载',place='大梁',note='初为前事，数量为史载兵数；与邺都二千幽州兵是不同部队，不合并统计。')
add('liu_kills_youzhou_garrison','刘知远入大梁后，因谋变告发杀尽一千五百名幽州兵',58,'帝入大梁，','帝尽杀之于繁台之下。',[('帝','闻告发后在繁台下杀尽驻大梁幽州兵')],when='947年六月刘知远入大梁后，具体日未载',place='大梁繁台',note='将为变是匿名告发内容，不视为兵变已发生；尽杀是实际处置，人数依前句一千五百。')
sup('liu_kills_youzhou_garrison',58,du,'時亦有燕軍一千五百人在京師，會高祖至闕，有上變者，言燕軍謀亂，盡誅於繁臺之下，咸稱其冤。','《旧五代史》同记京师燕军一千五百人因谋乱告发被尽诛繁台，并记时人称冤。','谋乱为告发，不证明其确有预谋；称冤保留为记载的评价。')
add('zhang_lian_refuses_promised_amnesty','刘知远屡许张琏免死，张琏因繁台杀兵拒绝归降',58,'乃围鄴都，','由是城久不下。',[('帝','屡派人招降并承诺不杀'),('张琏','率二千幽州兵助守，不信免死承诺，决意死守'),('重威','得到幽州兵协助守城')],when='947年围邺都期间，十一月出降前，具体各次日未载',place='邺都',note='张琏沿已核幽州指挥使，不误用895年同名者；繁台何罪是张琏的反问，相关无辜评价在司马光史评另录。')
sup('zhang_lian_refuses_promised_amnesty',58,du,'高祖亦悔其前失，累令宣諭，許以不死。璉等於城上揚言曰：「繁臺之誅，燕軍何罪？既無生理，以死為期。」','《旧五代史》也记刘知远后悔前事，屡次宣谕免死，张琏等以繁台遭杀为由决意死守。','后悔为该书心理叙述；此前免死许诺与最终出降前归乡承诺是不同阶段。',relation='adds')
add('han_xun_siege_devices','韩训献攻城器具，刘知远认为守城关键在众心',58,'十一月，丙辰，',None,[('韩训','以内殿直身份献攻城器具'),('帝','以众心维系城池作回应')],when='947年十一月丙辰',place='邺都军营',note='刘知远的政治判断作为当事人言论，不据此推攻城器械全未使用或器具类型。')
add('wang_min_admonishes_du','王敏屡次哭谏杜重威不要叛乱，未获听从',59,'杜重威之叛，','不听。',[('王敏','以观察判官身份屡次哭谏'),('重威','没有听从判官劝谏')],when='947年杜重威叛乱之际，具体各次日未载',place='邺都',note='金乡为王敏籍贯，非此时劝谏地点；未载劝谏原话，不虚构内容。')
add('du_sends_wang_min_submission','杜重威粮尽力竭，派王敏奉表请降',59,'及食竭力尽，','遣敏奉表出降。',[('重威','派王敏奉表出降'),('王敏','携降表出城')],when='947年十一月甲戌',place='邺都至刘知远行营',note='甲戌为遣王敏出表日，不当杜重威本人开城日。')
sup('du_sends_wang_min_submission',59,du,'復遣節度判官王敏奉表請罪，賜優詔敦勉，許其如初。','《旧五代史》杜重威传也记王敏奉表请罪，并获优诏。','该书职名作节度判官，通鉴作观察判官；同一奉表情节沿同人保留职名差异。',relation='adds')
sup('du_sends_wang_min_submission',59,nov,'壬申，杜重威上表請命。','《旧五代史》本纪将杜重威上表请命记在十一月壬申。','与通鉴甲戌遣王敏奉表纪时不同，可能指先后表章，未有证据便不合并成同一日或覆盖任一记载。',relation='conflicts')
add('du_honglian_meets_liu','杜弘琏出城见刘知远',59,'乙亥，','重威子弘琏来见；',[('弘琏','以杜重威之子身份来见刘知远'),('帝','接见杜重威之子')],when='947年十一月乙亥',place='刘知远邺都行营')
relationship('重威','弘琏','父亲',59,span(59,'乙亥，','重威子弘琏来见；'),'其子弘琏明确父子，方向表示杜重威是杜弘琏的父亲。旧传出候之子宏遂与既有质子弘璲姓名不一致，未强并。')
sup('du_honglian_meets_liu',59,du,'重威即遣其子宏遂、妻石氏出候高祖，','《旧五代史》杜重威传记遣其子宏遂、妻石氏出候刘知远。','与通鉴乙亥弘琏、丙子妻石氏分日记载不同；宏遂姓名异说只附对应出候事件，不认定与弘琏或弘璲为同一人。',relation='conflicts')
add('du_wife_meets_liu_returns','杜重威妻石氏出见刘知远，又被遣回城',59,'丙子，','帝复遣入城。',[('石氏','以杜重威妻、晋宋国长公主身份出见，再被遣回城'),('帝','接见石氏后遣她回城')],when='947年十一月丙子',place='邺都至刘知远行营',note='沿既有乐平长公主（杜重威妻），《旧五代史》杜重威传明确同一妻石氏累封宋国，不因封号变化新建人。')
relationship('重威','石氏','丈夫',59,span(59,'丙子，','帝复遣入城。'),'妻石氏沿已核公主主体，复用杜重威丈夫方向关系，不新建反向妻子边。')
sup('du_wife_meets_liu_returns',59,wife,'其妻即晉高祖妹也，累封宋國大長公主。','《旧五代史》明确杜重威妻为石敬瑭之妹，历次封号中有宋国大长公主。','与既有乐平长公主妻的身份相合，封号变化保留；通鉴宋国长公主与旧史宋国大长公主称谓分别引用。',relation='adds')
add('du_opens_ye_surrenders','杜重威开城出降，城内饥死严重',59,'丁丑，','存者皆尪瘠无人状。',[('重威','开门出降')],when='947年十一月丁丑',place='邺都',note='什七八为通鉴约七八成的描述，不作精确人口统计；死亡是围城累积，未把全部归入丁丑单日。')
sup('du_opens_ye_surrenders',59,nov,'丁丑，杜重威素服出降，待罪於宮門，詔釋其罪。','《旧五代史》本纪同记丁丑杜重威穿素服出降，待罪后获赦。','与此前上表、子妻接洽区别，正式出降日相合。',relation='adds')
sup('du_opens_ye_surrenders',59,du,'鄴城士庶，殍殕者十之六七。','《旧五代史》杜重威传记邺城饥死者约六七成。','与通鉴什七八有约数差异，死亡范围与统计依据未载，分别保留，不求平均或算精确人数。',relation='conflicts')
add('zhang_lian_requests_home_promise','张琏出降前要求朝廷立誓，获准返回家乡',59,'张琏先邀','诏许以归乡里。',[('张琏','出降前要求朝廷信誓'),('帝','朝廷诏准张琏等回乡')],when='947年十一月张琏出降前，具体日未载',place='邺都',note='这是归乡承诺，不能等同后来实际允许张琏本人回乡。')
add('zhang_lian_officers_killed','张琏等数十名将校出降后被杀，士卒获放北归',59,'及出降，','纵其士卒北归。',[('张琏','出降后与数十将校被杀')],when='947年十一月出降之后，具体日未载',place='邺都',note='与此前许归乡里并列，明确承诺与处置相反；数十为将校约数，未具名者不建虚构人物。')
sup('zhang_lian_officers_killed',59,du,'及出降，盡誅璉等將數十人，其什長已下放歸幽州，','《旧五代史》同记杀张琏等将数十人，将什长以下放归幽州。','补书明确获放的军职范围；不是所有幽州军都被杀，也不将将校数十与士兵二千累加为全部死者。',relation='adds')
add('released_soldiers_plunder','获放幽州兵在离开后汉境前大肆劫掠',59,'将出境，','大掠而去。',[],when='947年十一月放归北行之际，具体日未载',place='后汉境内北归沿途',note='集体未名，不把已遭杀害的张琏写成参与后续劫掠者。')
add('guo_proposes_punishment_confiscation','郭威建议杀杜重威百余牙将、籍没家财赏军，刘知远同意',59,'郭威请杀','从之。',[('郭威','提出诛牙将与没家财赏军'),('帝','同意建议'),('重威','其牙将与家财成为处置对象')],when='947年十一月杜重威出降后，具体日未载',place='邺都',note='主书写建议与同意，百余为牙将约数；实际清查杀将及财产分配据《旧五代史》杜重威传另录。')
E['du_officers_executed_assets_distributed']=event('du_officers_executed_assets_distributed','刘知远派王章、郭威清查并杀杜重威部下将吏，将财产分给军士',59,'高祖遣三司使王章、樞密副使郭威，錄重威部下將吏盡誅之，籍其財產與重威私帑，分給將士。',[('帝','派王章、郭威清查诛杀并分财赏军'),('王章','受命清查、诛将及分发财产'),('郭威','受命清查、诛将及分发财产'),('重威','部下将吏被诛，私帑被籍没')],when='947年十一月杜重威出降后，具体日未载',place='邺都',source=du,note='《旧五代史》杜重威传明确执行与分发财产，范围作部下将吏，通鉴作牙将百余；保留范围差异，不能推为城中所有军民尽杀。')
add('du_receives_high_offices','杜重威获授太傅兼中书令、楚国公',59,'以重威为','楚国公。',[('重威','获授高官与楚国公爵')],when='947年十一月出降后，具体授任日未由通鉴另列',place='后汉朝廷、邺都',note='不能将杜重威获授官爵写成其部下也都获赦。')
sup('du_receives_high_offices',59,nov,'以杜重威為檢校太師、守太傅、兼中書令、楚國公。','《旧五代史》丁丑出降条同记杜重威获检校太师、守太傅、兼中书令、楚国公。','本纪补明检校太师并接在丁丑赦罪之后；不把这些名衔当作已出镇任节度使。',relation='adds')
add('du_reviled_by_passersby','杜重威出入时遭路人投瓦砾辱骂',59,'重威每出入，',None,[('重威','出入时被路人投瓦砾辱骂')],when='947年出降获官之后开始，具体各次日未载',place='后汉',note='往往为多次概述，未载具体路段，不虚构每次地点和伤势。')
add('sima_guang_critiques_han','司马光批评刘知远杀无辜、失信杀降，却赦杜重威',60,'臣光曰：',None,[],year=None,when='司马光编撰《资治通鉴》时的史评，具体写作年未载',place='史家评论',note='这是后世作者评论，不是947年现场事件。无辜、非仁非信非刑及国祚不延因果为司马光论断，与当时各行动独立。',description='司马光认为，刘知远杀一千五百名无辜幽州兵违背仁，招降后杀张琏违背信，赦免罪重的杜重威违背刑。他以此批评后汉的治理，并解释其国祚短促。此为后世史评，保留为评论内容。')
add('gao_declines_yedu','高行周因慕容彦超在澶州，坚辞邺都职任',61,'高行周以','固辞鄴都。',[('行周','因慕容彦超在邻近澶州而坚辞邺都职任'),('彦超','其驻澶州成为高行周辞职背景')],when=n,place='邺都、澶州',note='固辞不等于此句已获准辞任；后句调整彦超镇地，与主帅之间嫌隙相联系，不另造已辞官结果。')
add('shi_liu_murong_commands','史弘肇、刘信调镇兼领禁军，慕容彦超移天平军',61,'己卯，',None,[('史弘肇','领归德节度使兼侍卫马步都指挥使'),('刘信','领忠武节度使兼侍卫马步副都指挥使'),('彦超','移任天平节度使，获加同平章事')],when='947年十一月己卯',place='归德军、忠武军、天平军',description='十一月己卯，史弘肇领归德节度使兼侍卫马步都指挥使，刘信领忠武节度使兼侍卫马步副都指挥使，慕容彦超移任天平节度使，三人均加同平章事。',note='领与兼职原意保留，三人同平章事是加衔，不能据此写成三人都入中书日常理政。')
sup('shi_liu_murong_commands',61,nov,'己卯，以許州節度使兼侍衛步軍都指揮使史宏肇為宋州節度使、同平章事，充侍衛親軍馬步軍都指揮使；以滑州節度使兼侍衛馬軍都指揮使劉信為許州節度使、同平章事，充侍衛親軍馬步軍副都指揮；以澶州節度使慕容彥超為鄆州節度使、同平章事；','《旧五代史》也记己卯史弘肇、刘信、慕容彦超的调镇与禁军职任，并加同平章事。','宋州归德、许州忠武、郓州天平为州名军号对应；宏弘字形保留，不新建史宏肇。')
add('qian_reviews_navy_generous_rewards','钱弘倧大阅水军，赏赐比往常增加一倍',62,'吴越王弘踧','赏赐倍于旧。',[('弘倧','检阅水军，增加赏赐')],when='947年十一月至十二月间，具体日未载',place='吴越水军',note='原弘踧与同段弘倧为字形问题，沿钱弘倧；倍于旧为史载相对量，不造货币总额。')
add('qian_rejects_hu_reward_advice','胡进思劝减少赏赐，钱弘倧怒投笔并称财物与士卒共享',62,'胡进思固谏，',None,[('胡进思','坚劝减少赏赐'),('弘倧','投笔入水，表示财物与士卒共享')],when='947年大阅水军时，具体日未载',place='吴越',note='陈述共财为钱弘倧当事人言论，不转为全体财产已被平均分配。')
sup('qian_rejects_hu_reward_advice',62,qian,'倧大閱兵於碧波亭，方第賞，進思前諫以賞太厚，倧怒擲筆水中曰：「以物與軍士，吾豈私之，何見咎也。」進思大懼。','《新五代史》也记胡进思认为赏太厚、钱弘倧投笔水中，并补地点为碧波亭、胡进思大惧。','同段后载岁除废倧等后续，暂不提前录成此刻已发动政变。',relation='adds')
add('liu_leaves_yedu','刘知远从邺都启程回京',63,'十二月，',None,[('帝','从邺都启程')],when='947年十二月丙戌',place='邺都',note='启程与后段到大梁分录，未把回京到达日设为丙戌。')
sup('liu_leaves_yedu',63,dec,'丙戌，車駕發鄴都歸京。','《旧五代史》同记丙戌从邺都启程回京。','该书后句癸巳至自邺都为到京日，后段再录，不与启程合并。')
add('shu_sends_wu_to_hou','孟昶派吴崇恽携王处回书信，招侯益归蜀',64,'蜀主遣','招凤翔节度使侯益。',[('蜀主','派吴崇恽招侯益'),('吴崇恽','以雄武都押牙身份携书赴凤翔'),('王处回','作为枢密使提供招降书信'),('侯益','受后蜀招降')],when=z,place='后蜀至凤翔',note='派遣与招降不等于侯益已实际归蜀，实际回应后段继续核对。')
sup('shu_sends_wu_to_hou',64,hou,'孟昶遣益所親掌樞密王處回賫書招益，復遣綿州刺史吳崇惲厚遺之。','《宋史》侯益传记孟昶派与侯益亲近的王处回携书招他，又派绵州刺史吴崇恽厚赠。','通鉴写吴携王书，宋传写王处回携书及又遣吴；职名亦雄武都押牙与绵州刺史不同。并列保留，不把招降与全部后续事件定在同一天。',relation='adds')
add('shu_appoints_northern_command','孟昶任张虔钊、何重建、韩保贞统率北上兵马',64,'庚寅，','共将兵五万，',[('蜀主','组织北面行营统帅'),('张虔钊','任北面行营招讨安抚使'),('何重建','任副使'),('韩保贞','以宣徽使身份任都虞候')],when='947年十二月庚寅',place='后蜀北面行营',note='共五万为三将部队总数，不是各率五万；与另李廷珪二万分清。')
sup('shu_appoints_northern_command',64,han,'會鳳翔侯益歸款，以保正為北路行營都監，以圖岐陽。','《宋史》韩保正传记侯益归款时，任保正为北路行营都监，谋取岐阳。','对应主书记宣徽使韩保贞为都虞候；同一侯益归款北行背景及既有丰德库使职经历相合，保留贞正字形、都监都虞候职名差异。该传未列庚寅，不单独证明任命日。',relation='adds')
add('zhang_he_attack_fengxiang_routes','张虔钊出散关、何重建出陇州，进攻凤翔',64,'虔钊出散关，','以击凤翔。',[('张虔钊','从散关出兵'),('何重建','从陇州出兵')],when='947年十二月庚寅任命后，具体出关日未载',place='散关、陇州至凤翔',note='出军为实际动作，未记凤翔已被攻占；不能因同段并列将两路同日出关作已知事实。')
add('li_tinggui_ziwu_aid_changan','李廷珪率二万兵出子午谷援长安',64,'奉銮肃卫都虞候','以援长安。',[('李廷珪','以奉銮肃卫都虞候身份率兵经子午谷援长安')],when='947年十二月，具体出军日未载',place='子午谷至长安',note='二万为史载兵数；出谷援长安不等于已经控制长安或与前五万合成单一路军。')
add('shu_armies_depart_chengdu','后蜀诸军从成都出发，史书记旌旗绵延数十里',64,'诸军发成都，',None,[],when='947年十二月，具体出发日未载',place='成都',note='旌旗数十里为史书概述，不反推士兵精确密度与人数。')
reviews={57:'声言降与拒陈观、部分出降、彦超请求与丙午实际攻城分录，伤万余死千余为主书约数；旧伤夷范围未定不简单等同伤者。',58:'繁台杀兵为六月入大梁后追叙，谋变为告发；两个幽州部队1500与2000不同，不累加死亡。张琏因前杀拒免死承诺与最终许归乡阶段区别；韩训献器与帝言论分清。',59:'王敏判官籍贯与官称保留；甲戌奉表与旧壬申表可能先后，不强定同日。主弘琏旧宏遂未合质子弘璲。妻石氏沿已核乐平公主并复用丈夫关系，宋国封号变化不新建人。丁丑实际降、饥死七八与旧六七比例异说、归乡誓与杀将校放士卒、沿途掠、郭议与旧明确执行、杜获官和被骂分录。',60:'司马光史评属于后世评论，年份null，不当947年现场人物行动；道德因果归属作者。',61:'高固辞不是此句已批准辞官；己卯三将州军号与禁军职相合，加同平章不证明入朝理政。',62:'弘踧疑字沿钱弘倧，水军大阅厚赏与胡谏投笔分录，新史补碧波亭与胡惧，未提前岁除废立。',63:'十二月丙戌发邺与后段归大梁区别。',64:'吴携王书招侯、北行任命、张何两路、李子午二万、诸军出成都分录，五万二万各部不重复；宋侯传使者职名分列，韩贞正与都虞候都监异文保留，后续失败未前移。'}
assert not (P/'publication.json').exists()
for n in range(57,65):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(57,65)],next_paragraph=Q[65]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原62—69行连续八段，本卷累计64/75；947年跨卷累计156/167，尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(57,65)],source_issues_review='王敏请命表日期、出候之子弘琏宏遂、饥死什七八与十之六七、韩保贞正字形及职名异文保留；伤夷与伤死分列不等同，招降承诺与实际处置分清。',plain_language_review='首次校核全体展示及事实说明，主语明确，计划、指控、言论、评论与实际执行分开；未明年份留null，逐字摘录保留底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
