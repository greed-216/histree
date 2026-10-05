# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 948 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,20))
COMMIT='8eeb68b9bcfa77ac7f52d7d2904b62c7ff052191'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-948-january-february','jiuwudaishi-100-january-948','songshi-480-xue-wen-protection']:
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
main_sources = ['tongjian-287-948-january-february']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0948-p009-p016',
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
        citation = f'卷287·乾祐元年（948年正月至二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0948_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=948, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='948年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_287_0948_' + code
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
        edge = 'participation_zztj_287_0948_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_287_0948_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','刘信':'刘信（刘知远从弟）','弘亻叔':'钱弘俶','弘倧':'钱弘倧'})
NEW_ALIASES={'刘承祐':['劉承祐','后汉隐帝'],'杜弘璋':['杜宏璋'],'杜弘璨':['杜宏璨'],'方安':[]}
NEW_BIRTH_YEARS={'刘承祐':931}
NEW_DEATH_YEARS={'杜弘璋':948,'杜弘璨':948,'方安':948}
NEW_DESCRIPTIONS={
 '刘承祐':'刘知远第二子，母亲为李氏。《旧五代史》记他生于931年三月七日的邺都旧宅，曾任左卫大将军和大内都点检。948年二月先封周王，随后依据公布的遗制继承后汉皇位。《资治通鉴》记其即位时十八岁。',
 '杜弘璋':'杜重威之子。948年正月，后汉在刘知远去世后下诏处死杜重威父子，杜弘璋在被处斩者之列。《旧五代史》写作宏璋。出生年未载。',
 '杜弘璨':'《资治通鉴》记为杜重威之子，948年正月与父亲及兄弟被后汉下诏处斩。《旧五代史》所列第三名儿子为宏杰，与弘璨是否同人尚待核，未直接合并。出生年未载。',
 '方安':'胡进思的党羽。948年吴越政变后的记载中，与另一名未具姓名的人奉胡进思之命夜间越墙刺杀被废的钱弘倧，遭薛温率众杀死。行动的具体月日未载。'}
j='jiuwudaishi-100-january-948';origin='jiuwudaishi-101-liu-chengyou-origin';feb='jiuwudaishi-101-february-948';du='jiuwudaishi-109-du-execution';song='songshi-480-xue-wen-protection'
add('yang_sends_liu_xin_away','杨邠在刘知远病危时遣刘信赴镇',9,'丁丑，',None,[('杨邠','因忌惮刘信，立即遣他赴镇'),('刘信','未获准辞别病危的皇帝，哭泣离去'),('刘知远','当时病危，刘信未能向他辞别')],when='948年正月丁丑',place='后汉朝廷至忠武军',description='刘知远病危时，杨邠忌惮侍卫马军都指挥使、忠武节度使刘信，立即遣他赴镇。刘信未能辞别皇帝，哭泣离去。',note='刘信沿用刘知远从弟主体，与吴国同名将领分开；遣赴镇不等于已经抵达。杨邠是派遣者，不把该决定写成皇帝的命令。')
add('liu_deathbed_entrustment','刘知远召四臣受顾命，托付刘承祐和后事',10,'帝召','后事托在卿辈。”',[('刘知远','临终召四臣，托付年幼的刘承祐和后事'),('苏逢吉','受召接受临终托付'),('杨邠','受召接受临终托付'),('史弘肇','受召接受临终托付'),('郭威','受召接受临终托付'),('刘承祐','成为临终托付的皇子')],when='948年正月丁丑',place='后汉宫廷',description='刘知远召苏逢吉、杨邠、史弘肇、郭威接受顾命，表示自己气息微弱，不能多言，将年幼的刘承祐和后事托付给他们。')
claim('person',people['刘承祐'],'birth_year','刘承祐生于931年，史载原纪年为唐长兴二年三月七日。',10,'以唐長興二年，歲在辛卯，三月七日，生帝於鄴都之舊第。','出生年依据明确纪年，不从即位年龄倒推；三月七日保持传统纪日，未换算公历月日。',source=origin,relation='adds')
relationship('刘知远','刘承祐','父亲',10,'隱皇帝，諱承祐，高祖第二子也。','本纪传主为刘承祐，高祖指刘知远，明确第二子身份。方向为刘知远是刘承祐的父亲。',source=origin)
relationship('李氏（刘知远妻）','刘承祐','母亲',10,'隱皇帝，諱承祐，高祖第二子也。母曰李太后，','李太后沿用刘知远妻李氏的已存主体，不因后来的太后称号新建人物。',source=origin)
add('liu_warns_du','刘知远临终要求防备杜重威',10,'又曰：','善防重威。”',[('刘知远','要求顾命臣防备杜重威'),('杜重威','成为被要求防备的对象')],when='948年正月丁丑',place='后汉宫廷',note='防备指示与后来处刑诏令分别记录，不扩写为临终明确命令杀死父子。')
add('liu_zhiyuan_death','刘知远在万岁殿去世',10,'是日，殂','殂于万岁殿，',[('刘知远','在万岁殿去世')],when='948年正月丁丑',place='万岁殿',note='是日承接丁丑；二月辛巳只是公布丧讯与继位日，不作为死亡日。')
sup('liu_zhiyuan_death',10,j,'二十七日丁丑，帝崩於萬歲殿，時年五十四。','《旧五代史》明确记刘知远在正月二十七日丁丑死于万岁殿，时年五十四。','本纪正文是独立补证；不从年龄反推生年，未将其所附《契丹国志》夹注另算独立确证。',relation='adds')
add('han_conceals_death','苏逢吉等在刘知远死后暂不公布丧讯',10,'逢吉等','秘不发丧。',[('苏逢吉','与其他顾命臣暂不公布丧讯'),('刘知远','其死亡暂未公布')],when='948年正月丁丑刘知远去世后',place='后汉宫廷',note='等字未逐一列明此行动的执行者，只具名苏逢吉，不把全部顾命臣的个人执行当作已知。')
sup('han_conceals_death',10,feb,'乾祐元年正月二十七日，高祖崩，秘不發喪。','《旧五代史》同记正月二十七日刘知远去世，暂不公布丧讯。','与二月公布遗制的先后分清。')
add('du_execution_edict','后汉在刘知远死后下诏处斩杜重威父子',10,'庚辰，下诏，','一切不问。”',[('杜重威','与三个儿子被诏令处斩'),('杜弘璋','被列入处斩诏令'),('杜弘琏','被列入处斩诏令'),('杜弘璨','被列入处斩诏令'),('乐平长公主（杜重威妻）','作为晋公主被诏令豁免追究')],when='948年正月庚辰',place='后汉朝廷',description='刘知远去世、丧讯尚未公布时，后汉下诏称杜重威父子在皇帝小病期间诽谤朝廷、动摇人心，命处斩杜重威及弘璋、弘琏、弘璨，并不追究晋公主和内外亲族。',note='诽谤摇众是诏书的指控，不作独立查实结论；诏令虽使用皇帝第一人称，却在刘知远死后发布，不写成其生前亲发。公主沿已核杜重威妻主体。')
sup('du_execution_edict',10,du,'帝崩，遂收重威，重威子宏璋、宏璉、宏傑誅之。','《旧五代史》也将逮捕处死放在刘知远死后，但列儿子为宏璋、宏琏、宏杰。','弘璋与宏璋、弘琏与宏琏作为字形异写保留；弘璨与宏杰存在姓名差异，未将宏杰加入弘璨的确定别名。',relation='adds')
add('du_family_execution','杜重威父子被处死',10,'庚辰，下诏，','一切不问。”',[('杜重威','被后汉处死'),('杜弘璋','与父亲一同被处死'),('杜弘琏','与父亲一同被处死'),('杜弘璨','《资治通鉴》列为被处死者')],when='948年正月庚辰，执行据《旧五代史》补证',place='后汉京师',description='杜重威及其儿子被处死。《通鉴》列弘璋、弘琏、弘璨，《旧五代史》列宏璋、宏琏、宏杰，第三人的姓名差异尚待核。',note='实际执行依据本纪伏诛和杜重威传父子已诛，区别于单纯命令；处刑地点没有更精确定位。')
sup('du_family_execution',10,j,'庚辰，太傅杜重威伏誅。','《旧五代史》本纪明确记杜重威在庚辰被处死。','该句证明杜重威实际死亡；子名另据杜重威传并列，不依本句补造。')
sup('du_family_execution',10,du,'重威父子已誅，陳屍於通衢，','《旧五代史》杜重威传明确写父子已被处死，尸体陈列于道路。','第三子姓名差异仍保留，不将两份不同名单说成逐名完全相同。')
for child in ['杜弘璋','杜弘璨']:
 relationship('杜重威',child,'父亲',10,span(10,'庚辰，下诏，','一切不问。”'),'诏文所列父子明确支持父亲方向；弘璨与《旧五代史》宏杰姓名差异待核，不增加无证兄弟长幼。')
add('du_corpse_public_desecration','杜重威尸体被陈列于市，遭市民争相撕食',10,'磔重威尸','斯须而尽。',[('杜重威','死后尸体被陈列并遭毁损')],when='948年正月庚辰处刑之后',place='后汉京师市中',description='杜重威的尸体被肢解陈列于市，市民争相食其肉，官吏无法制止，很快便被毁尽。',note='这是处死后的尸体处置，不另造第二次活体处刑。市民和官吏未具姓名，不建虚构人物。')
sup('du_corpse_public_desecration',10,du,'陳屍於通衢，都人聚觀者詬罵蹴擊，軍吏不能禁，屍首狼籍，斯須而盡。','《旧五代史》记尸体在通衢遭围观者辱骂踢打，军吏无法制止，尸首很快毁损殆尽。','《旧五代史》这句没有直接写食肉，保留两书细节区别。',relation='adds')
add('liu_chengyou_prince','刘承祐被封为周王、同平章事',11,'二月，','同平章事。',[('刘承祐','以皇子、左卫大将军、大内都点检身份受封')],when='948年二月辛巳朔',place='后汉朝廷',note='先封王，再公布遗制继位；不误认为此前已称帝。')
sup('liu_chengyou_prince',11,feb,'二月辛巳，授特進、檢校太尉、同平章事，封周王。','《旧五代史》同记二月辛巳封周王，并补授特进、检校太尉。','只补同次任官的官衔，不从这个段落的后文提前录入三月任官。',relation='adds')
add('liu_chengyou_succession','后汉公布刘知远丧讯与遗制，刘承祐继位',11,'有顷，',None,[('刘知远','其丧讯和遗制在死后公布'),('刘承祐','依遗制继承皇位，史载十八岁')],when='948年二月辛巳朔',place='后汉宫廷',description='刘承祐受封周王后不久，朝廷公布刘知远丧讯和遗制，命刘承祐即皇帝位。《资治通鉴》记刘承祐时年十八。',note='十八岁是史书记载的年龄，不用现代周岁算法反推出生年月。')
sup('liu_chengyou_succession',11,feb,'召文武百僚赴萬歲殿內，降大行皇帝遺制，云：「周王承祐，可於柩前即皇帝位。服紀日月，一依舊制。」是日，內外發哀成服。','《旧五代史》补记文武百官到万岁殿，遗制命刘承祐在灵柩前即位，并按旧制服丧，当天内外举哀。','遗制公开日与刘知远死亡日分开。',relation='adds')
add('han_baozhen_returns_longzhou','韩保贞、庞福诚从陇州撤军，要求何重建一同西返',12,'蜀韩保贞','要何重建俱西。',[('韩保贞','与庞福诚自陇州撤军'),('庞福诚','共同引兵西返'),('何重建','被要求一同西返')],when='948年二月，抵秦州前，出发日未载',place='陇州至秦州',note='这是撤军和邀请同行，不是首次三州归蜀；不把抵秦州当天强作从陇州出发日。')
add('shu_controls_qinzhou','韩保贞等抵达秦州，分兵守门和道路，何重建入蜀',12,'是日，',None,[('韩保贞','抵秦州后分兵控制城门和道路'),('庞福诚','与韩保贞共同抵秦州'),('何重建','随后离开秦州进入蜀地')],when='948年二月辛巳抵秦州，何重建入蜀具体日未另载',place='秦州至蜀地',description='韩保贞等抵秦州，分兵守城门和道路，何重建随后进入蜀地。',note='是日承接前段二月辛巳。随后入蜀的到达日未另载，未强作同日；不补何重建已被杀或被正式免职。')
add('li_empress_dowager','刘承祐的母亲李氏被尊为皇太后',13,'丁亥，',None,[('李氏（刘知远妻）','由皇后被尊为皇太后'),('刘承祐','尊母亲为皇太后')],when='948年二月丁亥',place='后汉朝廷',note='皇后沿刘知远妻李氏，与其他朝代李太后分开。')
sup('li_empress_dowager',13,feb,'丁亥，帝於萬歲殿門東廡下見群臣，尊母後為皇太后。','《旧五代史》同记刘承祐于丁亥尊母为太后，并补记在万岁殿门东廊见群臣。','帝在此处已指刘承祐，不沿用前面病逝的刘知远。',relation='adds')
add('liu_zaiming_replaces_bai','后汉任命刘在明代替白再荣任成德留后',14,'朝廷知',None,[('白再荣','被朝廷认为不具将帅才能，遭替换'),('刘在明','由前建雄留后被任命替代白再荣')],when='948年二月庚寅',place='成德军、镇州',note='不具将帅才能是史书记载的朝廷判断，不写成无争议的人物本质评价；尚未记白再荣此时被处刑。')
sup('liu_zaiming_replaces_bai',14,feb,'庚寅，以前晉州留後劉在明為鎮州留後、幽州馬步軍都部署，加檢校太尉。','《旧五代史》同记庚寅任命刘在明，写前职为晋州留后，新任镇州留后兼幽州马步军都部署，加检校太尉。','晋州、镇州为州名，建雄、成德为军号；补明本纪任职表述，不增新的同名刘在明。',relation='adds')
add('liu_chengyou_amnesty','刘承祐朝廷颁行大赦',15,'癸巳，',None,[('刘承祐','即位后颁行大赦')],when='948年二月癸巳',place='后汉朝廷',note='这是二月的新赦令，与刘知远正月乙卯改元赦令分开；实际逐人获释情况未载。')
sup('liu_chengyou_amnesty',15,feb,'癸巳，制「大赦天下，自乾祐元年二月十三日昧爽已前，所犯罪人，已結正未結正、已發覺未發覺、常赦所不原者咸赦除之。中外文武臣僚並與加恩，馬步將士各賜優給。唐、晉兩朝求訪子孫，立為二王後」云。','《旧五代史》补记赦令以二月十三日黎明前为界，涵盖通常不赦者，并给文武臣僚加恩、将士优给，访求唐晋后人承继祭祀。','这些是诏令规定，不推所有给赏及访求行动已经完成。',relation='adds')
add('he_chengxun_requests_kill_hu','何承训再次请求诛杀胡进思及其党羽',16,'吴越内牙','诛胡进思及其党。',[('何承训','再次请求诛胡进思及其党'),('胡进思','成为处刑提议的对象')],when='948年二月乙未之前，具体日未载',place='吴越',note='这是请求，钱弘俶没有执行这项请求；何承训与后汉皇子刘承训分开。')
add('qian_executes_he_chengxun','钱弘俶因何承训反复改变态度，将他处斩',16,'吴越王弘亻叔恶','斩之。',[('钱弘俶','不满何承训反复，担忧招祸，下令拘捕处斩'),('何承训','被拘捕并处斩')],when='948年二月乙未',place='吴越',note='不满反复和怕招祸为史家所述动机；乙未只系何承训处刑，不覆盖后续全部刺杀活动。')
add('qian_refuses_kill_brother','胡进思屡请杀钱弘倧，钱弘俶拒绝',16,'进思屡请','弘亻叔不许。',[('胡进思','屡次请求杀故王以消除后患'),('钱弘俶','拒绝杀害兄长'),('钱弘倧','被提议杀害，但请求未获准')],when='948年吴越政变后的叙述，具体月日未载',place='吴越',note='以绝后患为胡进思的理由，不当作史实判决。')
sup('qian_refuses_kill_brother',16,song,'進思屢請除之，恐為後患，俶泣曰：「若殺吾兄，吾終不忍，汝欲行其志，吾當退避賢路。」進思慚而退。','《宋史》也记胡进思屡请杀钱弘倧，钱俶表示不忍杀兄，甚至愿退位，胡进思惭愧退下。','钱俶即钱弘俶；拒绝行为与假传王命分别记录。',relation='adds')
add('hu_forges_order_xue_refuses','胡进思假传王命命薛温杀钱弘倧，薛温拒绝',16,'进思诈','不敢妄发。”',[('胡进思','假传王命暗令杀故王'),('薛温','指出受命时没有这项命令，拒绝擅动'),('钱弘倧','被伪造命令指为杀害对象')],when='948年吴越政变后的叙述，具体月日未载',place='吴越故王住处',note='假令不能成为钱弘俶真实授权杀兄的证据，薛温拒绝而未执行。')
add('fang_an_attempts_assassination','胡进思派方安等越墙刺杀，钱弘倧闭门求救',16,'进思乃夜遣','大呼求救；',[('胡进思','夜间派两名党羽刺杀'),('方安','与另一人越墙进入'),('钱弘倧','关门拒绝刺客，呼救')],when='948年吴越政变后的夜间，具体月日未载',place='钱弘倧住处',note='底本私用字与俞旁组合保留原文，展示解释为越墙；两人仅一人具名，不虚构另一人。刺杀未成功。')
add('xue_wen_saves_qian_zong','薛温率众杀死方安等，救下钱弘倧',16,'温闻之，','毙安等于庭中。',[('薛温','听到求救，率众进入并杀死两名刺客'),('方安','与另一名刺客在庭中被杀'),('钱弘倧','获救，没有被刺客杀害')],when='948年吴越政变后的夜间，具体月日未载',place='钱弘倧住处庭院',note='两名刺客死亡，不误为故王遇害；方安出生年和精确死日未载。')
sup('xue_wen_saves_qian_zong',16,song,'溫至越旬餘，有二卒夜持刃逾垣入，倧闔戶拒之，呼聲達於外，溫領徒而入，斃二卒於庭中，乃進思之所遣也。','《宋史》同记薛温到越地十多天后，两名持刃者越墙进入，被薛温率人杀死，并明确为胡进思所派。','宋史未列方安姓名；十多天是到越地后的间隔，不换算具体日期。',relation='adds')
add('qian_thanks_xue_wen','钱弘俶得知刺杀，称薛温救了自己的兄长',16,'入告弘亻叔，','汝之力也。”',[('薛温','入告刺杀及救援经过'),('钱弘俶','惊讶得知，称赞薛温保全兄长'),('钱弘倧','成为被称已保全的兄长')],when='948年救援之后，具体月日未载',place='吴越宫廷',note='全吾兄确认救援结果，兄弟长幼沿既存关系，不重复反建关系。')
add('qian_defers_to_hu','钱弘俶畏忌胡进思，曲意迁就',16,'弘亻叔畏忌','曲意下之。',[('钱弘俶','畏忌胡进思而迁就'),('胡进思','受到钱弘俶迁就')],when='948年吴越政变后的叙述，具体月日未载',place='吴越',note='这是史家所述心理与行为，不推为允许杀兄或终身固定盟友关系。')
add('hu_death_after_failed_assassination','胡进思忧惧，背部生疽后去世，钱弘倧得以保全',16,'进思亦内忧惧，',None,[('胡进思','刺杀失败后忧惧，背部生疽，随后去世'),('钱弘倧','因此得以保全')],year=None,when='刺杀失败后不久，确切死亡年月未载',place='吴越',note='未几是相对间隔，两份所引原文都未独立给出卒年，暂不强定948年，不作现代病因诊断。')
sup('hu_death_after_failed_assassination',16,song,'進思因憂懼，疽發背，卒。','《宋史》也记胡进思因忧惧而背部生疽，随后去世。','这句仍无明确死亡年月；紧接钱弘倧在越二十余年后死的记载不作为本次事件死亡。')
reviews={9:'杨邠遣赴镇、未辞刘知远、哭离分别明确。刘信复用从弟身份；去镇不作已到。',10:'顾命四人、托皇子、防杜、丁丑死亡、秘不发丧、庚辰死后诏令、实杀、亲族豁免与尸体受辱分别记录。诏书罪名仅为指控。弘璨与宏杰异文保留，未无证合并。刘承祐父母和931生年补本纪明确原文，不依年龄推算。',11:'封周王在前，公布丧讯与遗制及即位在后，二月辛巳非皇帝死亡日。年龄保持史载十八，不强换周岁。',12:'从陇州撤回与辛巳到秦州分录；守门路与何重建本人入蜀，不作三州首次归附或何死亡。',13:'皇后为李氏，太后与刘承祐母亲对应；丁亥见群臣据本纪补。',14:'朝廷非将帅才是评价，替换任命与惩处区别。州名军号及幽州都部署职据本纪分别说明。',15:'二月癸巳新赦令与正月改元赦分开，所载加恩、给赏、访求为规定，不宣称已逐项执行。',16:'何提议杀胡与本人被斩、胡请杀故王被拒、伪令薛拒、两刺客越墙、故王拒户、薛杀刺客救王、钱谢、迁就胡、胡疽卒分录。乙未只系何被斩，其他行动不强套；胡卒确年未知null，匿名刺客不建虚构人。'}
assert not (P/'publication.json').exists()
for n in range(9,17):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=287,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷287原91—98行连续八段，本卷累计16/19，948年跨卷287、288累计16/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],source_issues_review='弘璨与宏杰姓名差异未合并；胡进思卒年暂null；公主沿杜重威妻主体。未把死后诏令当生前亲发，未把秦州控制当第一次归蜀。',plain_language_review='首次逐条核对人物、事件、角色、关系、日期、出处与事实说明的现代白话及主语；命令、请求、假令、指控、评价、实际执行与尸体处置分清，引用原字保留。不设发布后固定文案二次审阅。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
