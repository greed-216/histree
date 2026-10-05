# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 25–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,70))
COMMIT='5047247441ba8ca5148602bf0116a6c308eb295b'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-948-april-august','jiuwudaishi-101-june-948']:
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
main_sources = ['tongjian-288-948-april-august']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(25, 33):
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
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐元年（948年六月至七月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_05_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_288_0948_' + code
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
        edge = 'participation_zztj_288_0948_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0948_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
def extra_actor(code,n,name,role,source,quote):
 pk=person(name,n,role,quote,source=source);edge='participation_zztj_288_0948_'+code+'_'+pk
 assert not any(x['key']==edge for x in B['person_events'])
 B['person_events'].append(dict(key=edge,person_key=pk,event_key=E[code],role=role,status='draft'))
 claim('person_event',edge,'role',name+'：'+role+'。',n,quote,'补充史书明确记载该人物的行动；不把主书未具名人物自动合并。',source=source)
ALIASES.update({'蜀主':'孟昶','蜀高祖':'孟知祥','继昭':'张继昭','德钧':'王德钧','汉帝':'刘承祐'})
NEW_ALIASES={'张继昭':['張繼昭'],'归信':['歸信'],'王德钧':['王德鈞'],'高延昭':[],'王昭远':['王昭遠'],'智諲':['智𬤊'],'刘扶':['劉扶']}
NEW_DESCRIPTIONS={
 '张继昭':'后蜀张业之子，史书记为检校左仆射，喜好击剑，曾与僧人归信寻找擅长剑术的人。孙汉韶向孟昶指控父子谋反；本段没有证实这项指控。生卒年未载，本段没有明确记载张继昭被杀。',
 '归信':'《资治通鉴》记载的僧人，曾与后蜀张继昭寻找擅长剑术的人。史书没有说明他是否参与谋反。生卒年及其他身份未载。',
 '王德钧':'后蜀王处回之子。《资治通鉴》在948年条追述他骄横，但没有列明具体行为和发生日期。生卒年未载。',
 '高延昭':'后蜀官员。948年任普丰库使，孟昶原想任命他与王昭远为枢密使，因二人资历和地位较低，改任通奏使、知枢密院事。生卒年未载。',
 '王昭远':'成都人，后蜀官员。年少时跟随僧人智諲进入孟知祥府中，后来被留下侍奉孟昶；《新五代史》《宋史》记当时十三岁。948年由茶酒库使任通奏使、知枢密院事，获委机务和府库财物支配。没有据十三岁反推出生年。',
 '智諲':'成都东郭僧人。《新五代史》《宋史》在追述王昭远早年经历时记载，王昭远曾作为童子跟随智諲进入孟知祥府中。具体发生年及智諲生卒年未载。',
 '刘扶':'荆南牙将。948年高从诲请求恢复与后汉往来时，派刘扶到后汉朝廷请罪，《旧五代史》六月条记载这次出使。生卒年未载。'}
# An uncommon character in a monk's name is retained rather than inventing an alias.
NEW_ALIASES['智諲']=[]
june='jiuwudaishi-101-june-948';july='jiuwudaishi-101-july-948';zhang='xinwudaishi-064-zhang-ye-fall';newwang='xinwudaishi-064-wang-zhaoyuan-early';songwang='songshi-479-wang-zhaoyuan-early';gao='xinwudaishi-069-gao-renews-tribute'
j='948年六月，具体日未载';after='948年七月张业被杀以后，具体日未载'
add('wang_requests_shu_surrender','王景崇派使者向后蜀请降',25,'乙酉，','请降于蜀，',[('王景崇','派使者向孟昶请降'),('孟昶','成为王景崇请降的对象')],when='948年六月乙酉',place='凤翔、后蜀',note='请降是已派使者提出归附请求，未写成此日蜀军已接管凤翔。')
add('wang_accepts_li_titles','王景崇接受李守贞授予的官爵',25,'亦受','李守贞官爵。',[('王景崇','接受李守贞授予的官爵'),('李守贞','向王景崇授予官爵')],when='948年六月条所载，具体授受日未载',place='凤翔、河中',note='本句没有列明官爵名称，也未独立注明乙酉；不补具体官名或据此建立血亲关系。')
add('gao_trade_disrupted','高从诲与后汉断交后，荆南缺少北方商旅往来',25,'高从诲既与汉绝，','境内贫乏，',[('高从诲','与后汉断交，治下被记为贫乏')],year=None,when='948年六月恢复往来之前，断交及商旅停往具体年月未载',place='荆南',description='《资治通鉴》记载，高从诲与后汉断交后，北方商旅不再前往荆南，境内贫乏。',note='这是恢复往来前的背景，未将断交起点强定为六月，也未补经济统计或断交全部原因。')
add('gao_apologizes_renews_tribute','高从诲上表谢罪，请求恢复向后汉朝贡',25,'乃遣使','乞修职贡。',[('高从诲','派使者上表谢罪，请求恢复朝贡')],when=j,place='荆南至后汉朝廷',note='请求恢复朝贡与朝廷后续答复分开；没有据此把高从诲本人记作亲自到京。')
sup('gao_apologizes_renews_tribute',25,june,'荊南節度使高從誨上表歸命，從誨嘗拒朝命，至是方遣牙將劉扶詣闕請罪。','《旧五代史》六月条同记高从诲上表，并补充使者是荆南牙将刘扶。','这句接在辛卯奏报以后，没有另标高从诲上表之日；不将前一奏报日当作独立确认的出使日。',relation='adds')
extra_actor('gao_apologizes_renews_tribute',25,'刘扶','奉高从诲之命赴后汉朝廷请罪',june,'至是方遣牙將劉扶詣闕請罪。')
sup('gao_apologizes_renews_tribute',25,gao,'從誨自求郢州不得，遂自絕於漢。逾年，復通朝貢。','《新五代史》也记高从诲断绝与后汉往来后，跨年恢复朝贡。','逾年不机械解释为恰好一年；该书没有给出恢复往来的月日，不以死亡所在十月作为恢复日期。')
add('han_envoy_comforts_gao','后汉下诏派使者慰抚高从诲',25,'诏遣使',None,[('刘承祐','下诏派使者慰抚高从诲'),('高从诲','成为慰抚对象')],when=j,place='后汉朝廷、荆南',note='诏令下达与使者完成行程分开；使者未具姓名，不与刘扶合并。')
sup('han_envoy_comforts_gao',25,june,'壬寅，荊南高從誨入貢謝恩，釋罪。','《旧五代史》六月壬寅条补记高从诲入贡谢恩，获释罪。','该句是后续朝贡及释罪，不把壬寅强定为主书慰抚诏令的日期，也不写成高从诲本人到京。',relation='adds')
add('shang_wounded_dies_changan','尚洪迁攻打长安，受重伤后去世',26,'西面行营',None,[('尚洪迁','任西面行营都虞候，攻城受重伤后去世')],when='948年六月条所载，具体日未载',place='长安',note='受伤和死亡按此句记载；没有把此前任官乙未或后续九月追赠日期当死亡日。')
claim('person',people['尚洪迁'],'death_year','尚洪迁于948年攻打长安时受重伤后去世。',26,Q[26]['text'],'死亡记载列为新增出处；沿用已发布人物，不重建人物，也不直接改写此前批次的空生卒字段。')
add('li_gu_campaign_transport','李谷任西南面行营都转运使',27,'秋，',None,[('李谷','由工部侍郎任西南面行营都转运使')],when='948年七月壬子，据《旧五代史》；《资治通鉴》只记七月',place='西南面行营',note='职务及日期分别据两书；任命不等于粮草运输已经完成。')
sup('li_gu_campaign_transport',27,july,'壬子，以工部侍郎李穀充西南面行營都轉運使。','《旧五代史》明确记七月壬子任命李谷为西南面行营都转运使。','穀沿谷的既有规范主体，两书官职一致；主书未载干支，作为补充日期。',relation='adds')
add('guo_wei_added_chancellor','后汉给枢密使郭威加同平章事',28,'庚申，',None,[('郭威','在枢密使职务之外加同平章事')],when='948年七月庚申',place='后汉朝廷',note='加衔与此后奉命统率各路行营分开，不提前记录八月出征。')
sup('guo_wei_added_chancellor',28,july,'庚申，樞密使郭威加同平章事。','《旧五代史》同记七月庚申郭威加同平章事。','这里只印证加衔，不补尚未录入的军事任命。')
add('zhang_ye_private_prison','史书记载张业强买田宅，并在家中私设牢狱',29,'蜀司空','有瘐死者。',[('张业','被记载强买田宅、藏匿逃亡者并拘禁欠债者')],year=None,when='948年七月张业被杀之前的追叙，具体发生年月未载',place='后蜀、张业私宅',description='《资治通鉴》追述张业强行购买他人的田宅，在私宅藏匿逃亡者，又设牢狱拘禁欠债者；有的人被关多年，甚至死在狱中。',note='豪侈和罪恶来自史书评价及记载，不把历年行为全部放在948年七月。原文未具欠债者姓名，不新增虚构人物。')
sup('zhang_ye_private_prison',29,zhang,'業兼判度支，置獄于家，務以酷法厚斂蜀人，蜀人大怨。','《新五代史》也记张业兼判度支，在家中设狱，以严酷手段向蜀人敛财。','补充财政职务和敛财记载；没有以此独立证明后来谋反指控属实。',relation='adds')
add('zhang_jizhao_seeks_swordsmen','张继昭与僧人归信寻找擅长剑术的人',29,'其子检校','访善剑者，',[('张继昭','任检校左仆射，喜好击剑，与归信访求善剑者'),('归信','与张继昭一同寻找擅长剑术的人')],year=None,when='948年七月张业被杀前的追叙，具体年月未载',place='后蜀，具体地点未载',note='喜好剑术和访求剑客不自动等于已发动谋反；父亲在前句是张业。')
relationship('张业','张继昭','父亲',29,'其子检校左仆射继昭，好击剑，','其承接张业；张业是张继昭的父亲，不另建反向儿子关系。')
add('sun_accuses_zhang_family','孙汉韶密告张业和张继昭谋反',29,'右匡圣','密告业、继昭谋反。',[('孙汉韶','与张业有嫌隙，密告父子谋反'),('张业','受到谋反指控'),('张继昭','与父亲一同受到谋反指控')],year=None,when='948年七月甲子处置张业之前，告发具体年月未载',place='后蜀朝廷',note='原文明示孙汉韶与张业有嫌隙；记录密告行为和指控，未将指控内容当成已证实谋反。')
add('li_an_join_accusation','李昊和安思谦跟随孙汉韶指控张业',29,'翰林承旨','复从而谮之。',[('李昊','以翰林承旨身份跟随提出指控'),('安思谦','以奉圣控鹤马步都指挥使身份跟随提出指控'),('张业','受到李昊、安思谦进一步指控')],year=None,when='948年七月甲子处置之前，具体年月未载',place='后蜀朝廷',note='谮是史书对这些指控的定性，不列他们为已被证实谋反案的调查者；原文没有写归信参加告发。')
add('meng_kills_zhang_ye','孟昶命壮士在都堂杀死张业',29,'甲子，','就都堂击杀之，',[('张业','入朝后在都堂被杀'),('孟昶','下令壮士杀张业')],when='948年七月甲子',place='后蜀都堂',note='张业是被杀对象，不能把前句张继昭、归信也列作本次明确被杀者。')
sup('meng_kills_zhang_ye',29,zhang,'十一年，昶與匡聖指揮使安思謙謀，執而殺之。','《新五代史》广政十一年条也记孟昶杀张业，并补充孟昶曾与安思谦谋划。','广政十一年与948年相对应；该句没有给出七月甲子，也未列张继昭被杀。',relation='adds')
extra_actor('meng_kills_zhang_ye',29,'安思谦','据《新五代史》与孟昶商议处置张业',zhang,'十一年，昶與匡聖指揮使安思謙謀，執而殺之。')
claim('person',people['张业'],'death_year','張业于948年七月甲子被孟昶下令杀死。'.replace('張','张'),29,'甲子，业入朝，蜀主命壮士就都堂击杀之，','新增死亡证据沿既有主体，旧批次的原始字段和来源快照保持不变。')
add('meng_confiscates_zhang_property','孟昶下诏公布张业罪状，并没收其家产',29,'下诏',None,[('孟昶','下诏公布张业罪状并籍没其家'),('张业','被公布罪状并没收家产')],when='948年七月甲子处置前后，诏令具体日未另载',place='后蜀',note='公布罪状是政治处置，没收家产不自动等于杀尽全家；未补名单或没收数额。')
add('wang_chuhui_abuses_power','史书记载王处回卖官、干预诉讼并收取馈赠',30,'枢密使','家赀巨万。',[('王处回','任枢密使、保宁节度使兼侍中，被记载卖官和收取馈赠')],year=None,when='948年七月离职前的追叙，具体行为年月未载',place='后蜀',description='《资治通鉴》记载王处回专权贪纵，卖官并以诉讼取利，各地馈赠先交给他，再交内府，积累巨额家财。',note='家赀巨万不转换为现代金额；保留史书评价，不把所有行为都记作七月同一天发生。')
add('wang_dejun_arrogance','史书追述王处回之子王德钧骄横',30,'子德钧，','亦骄横。',[('王德钧','被史书评价为骄横')],year=None,when='948年七月王处回离职前的追叙，具体年月未载',place='后蜀，具体地点未载',description='《资治通鉴》追述王处回的儿子王德钧也很骄横，没有在本句列举他的具体行为。',note='德钧承接王处回之子，不与赵德钧混同；评价不变成具体犯罪记录。')
relationship('王处回','王德钧','父亲',30,'子德钧，亦骄横。','前句传主为王处回，因此王处回是王德钧的父亲；不与赵德钧及其家族合并。')
add('meng_spares_wang_chuhui','张业被杀后，孟昶让王处回回到私宅',30,'张业既死，','听归私第。',[('孟昶','不忍杀王处回，准许他回私宅'),('王处回','获准回私宅')],when=after,place='后蜀',note='不忍杀是史书解释，并不是已经签署死刑后正式赦免；回宅与后续辞位分开。')
add('wang_chuhui_leaves_privy_office','王处回辞去枢密职务，改任武德节度使兼中书令',30,'处回惶恐',None,[('王处回','因惶恐辞位，改任武德节度使兼中书令'),('孟昶','改授王处回武德节度使兼中书令')],when=after,place='后蜀、武德军',note='辞位所指枢密职务；不是辞去一切官职。外任和致仕表述按各书分别保留。')
sup('wang_chuhui_leaves_privy_office',30,zhang,'王處回、趙廷隱相次致仕，','《新五代史》把王处回、赵廷隐离开权力中心概括为相继致仕。','该书用致仕，主书同时记改任武德节度使兼中书令，独立表述保留；不将赵廷隐离职也强定为本次同一天。',relation='adds')
add('meng_considers_privy_appointment','孟昶想任命高延昭和王昭远为枢密使',31,'蜀主欲以','名位素轻，',[('孟昶','考虑任命二人为枢密使'),('高延昭','以普丰库使身份成为拟任人选'),('王昭远','以茶酒库使身份成为拟任人选')],when=after,place='后蜀朝廷',note='欲是任命设想，后文因名位较低改授另一职；不记为二人已经正式担任枢密使。')
add('gao_wang_manage_privy_council','高延昭和王昭远任通奏使，知枢密院事',31,'乃授','知枢密院事。',[('孟昶','因二人名位较低，改授通奏使并令掌枢密院事务'),('高延昭','任通奏使、知枢密院事'),('王昭远','任通奏使、知枢密院事')],when=after,place='后蜀枢密院',note='实际官职是通奏使、知枢密院事，不沿前句拟任称其已正式为枢密使。')
sup('gao_wang_manage_privy_council',31,songwang,'會樞密使王處回出知梓州，昶以樞密事權太重，乃以昭遠及普豐庫使高延昭為通奏使、知樞密院事，','《宋史》同记王昭远与高延昭任通奏使、知枢密院事，解释孟昶认为枢密事权过重。','《宋史》记王处回出知梓州，主书写武德节度使；保留各书职务表述，不无证添加一次具体日期的调任。',relation='adds')
sup('gao_wang_manage_privy_council',31,newwang,'樞密使王處回致仕，昶以樞密使權重難制，乃以昭遠為通奏使知樞密使事，','《新五代史》也记王处回离职后，王昭远改任通奏使掌枢密事务。','该句只写王昭远，不作为高延昭同任的独立印证；王处回致仕用语与另书外任分别保留。')
add('wang_zhaoyuan_early_service','王昭远年少时随僧入府，被留下侍奉孟昶',31,'昭远，成都人，','令给事蜀主左右。',[('王昭远','年少时作为僧童入府，因敏慧被留下侍奉孟昶'),('孟知祥','欣赏王昭远敏慧，令其侍奉孟昶'),('孟昶','得到王昭远随侍')],year=None,when='孟知祥在世、孟昶尚年少时的追叙，具体年月未载',place='成都、孟知祥府',note='蜀高祖为孟知祥，蜀主为孟昶；追叙不是948年发生，也不据十三岁推算出生年。')
sup('wang_zhaoyuan_early_service',31,newwang,'昭遠，成都人也，年十三，事東郭禪師智諲為童子。知祥嘗飯僧於府，昭遠執巾履從智諲以入，','《新五代史》补记王昭远十三岁时为东郭禅师智諲的童子，随智諲进入孟知祥府中。','补充师名与年龄，未载具体年月；新史在宋灭蜀段追述，不能以段落年代作为早年时间。',relation='adds')
extra_actor('wang_zhaoyuan_early_service',31,'智諲','作为僧人带童子王昭远进入孟知祥府中',newwang,'昭遠，成都人也，年十三，事東郭禪師智諲為童子。知祥嘗飯僧於府，昭遠執巾履從智諲以入，')
sup('wang_zhaoyuan_early_service',31,songwang,'王昭遠，益州成都人。幼孤貧。年十三，依東郭僧智諲為童子。','《宋史》同记成都出身、十三岁依僧智諲为童子，并补充年幼时孤苦贫穷。','孤贫是该书所记早年背景，未据此确定父母死亡时间或姓名。',relation='adds')
add('wang_zhaoyuan_controls_treasury','孟昶将机务交给王昭远，允许他自由支取府库财物',31,'至是，',None,[('孟昶','把机务委交王昭远，放任府库财物支取'),('王昭远','获委机务，府库金帛支取不再逐项核算')],when=after,place='后蜀府库',note='不复会计指此处财物支取不再核算，不写成蜀国所有税收和财政账簿被彻底废除。')
sup('wang_zhaoyuan_controls_treasury',31,newwang,'然事無大小，一以委之，府庫金帛恣其所取不問。','《新五代史》也记孟昶将事务委给王昭远，并放任他取用府库金帛。','原文仅在王昭远叙事中说委任及财物支取，不无证扩大到高延昭也有完全相同权限。')
sup('wang_zhaoyuan_controls_treasury',31,songwang,'機務一以委之，府庫財帛恣其取不問。','《宋史》也记机务交付王昭远，府库财帛任其支取。','同一史事的不同书证保留独立出处，不宣称其记载相互完全独立。')
add('guo_congyi_yongxing_governor','郭从义任永兴节度使',32,'戊辰，','永兴节度使，',[('郭从义','任永兴节度使')],when='948年七月戊辰',place='永兴军',note='正式节度使任命与前面的行营都部署分开，沿用郭从义主体。')
sup('guo_congyi_yongxing_governor',32,july,'以澶州節度使郭從義為永興軍節度使兼行營都部署。','《旧五代史》七月戊辰条同记郭从义任永兴军节度使，并兼行营都部署。','该书补兼职，不创建另一郭从义，也不把军号不同当作两次任命。',relation='adds')
add('bai_wenke_hezhong_acting_office','白文珂兼管河中行府事务',32,'白文珂',None,[('白文珂','兼知河中行府事')],when='948年七月戊辰',place='河中行府',note='兼知行府事务是本次任命，不与早先河中行营都部署混为同一条，也不表示已攻克河中。')
reviews={
25:'王景崇请降与受李守贞官爵分录；高从诲断交商旅背景不强定六月。旧史补使者刘扶及壬寅朝贡释罪，不把刘扶当后汉慰抚使者。',
26:'尚洪迁沿用上批主体，攻城重伤死亡据原文；既有档案不改，新增死亡事实出处，不拿九月追赠作死亡日。',
27:'李谷沿既有主体，旧史补七月壬子日期。',
28:'郭威加同平章事为七月庚申，不提前八月军事命令。',
29:'张业历年侵占及私狱、张继昭访剑、孙汉韶密告、李昊安思谦指控、甲子杀张业与籍没分录；谋反指控不当已证事实，未推定张继昭归信同被杀。',
30:'王处回贪纵与王德钧骄横为未定年月追述；孟昶听归、辞位外任分录。新史致仕与主书改任官职并列保留。',
31:'拟任枢密使与实际通奏使知院事分开；王昭远童年追叙未定年月，师名智諲据新史及宋史，十三岁未反推生年。蜀高祖为孟知祥，蜀主为孟昶。',
32:'戊辰郭从义永兴节度、白文珂兼知行府分录，旧史补郭兼行营部署，不提前攻克结局。'}
assert not (P/'publication.json').exists()
for n in range(25,33):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷288原31—38行连续八段，本卷32/69；卷287已19段，全年51/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,33)],source_issues_review='王处回致仕及外任表述并列。张业谋反仅作指控，杀死者只明确张业。王昭远追叙区分孟知祥和孟昶，不推算童年年份；智諲保留姓名原字。',plain_language_review='首次逐条检查人物介绍、事件标题正文、时间说明、角色、关系方向及事实说明；明确主语，区分请求、任命设想、实际任官、谋反指控与执行处置。原文摘录保持底本字形，追述未定年月用null。不安排固定发布后二次全文重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
