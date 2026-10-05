# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 39–46."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,83))
COMMIT='148dffeabd6a27b31ce24bf25fa5203d0cd91ab7'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-290-951-march-policies','xinwudaishi-067-qian-zong-succession']:
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
main_sources = ['tongjian-290-951-march-policies']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p039-p046',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-111-april-grain':'卷111·太祖本纪二·广顺元年四月','jiuwudaishi-111-may-envoys':'卷111·太祖本纪二·广顺元年五月','songshi-479-yi-shenzheng':'卷479·世家二·西蜀孟氏·伊审徵','xinwudaishi-070-zheng-gong':'卷70·东汉世家·郑珙出使与去世'}
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
lines = (ROOT / 'resources/derived/tongjian/290.txt').read_text().splitlines()
for n in range(39, 47):
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
    labels={'jiuwudaishi-111-april-grain':'卷111·太祖本纪二·广顺元年四月','jiuwudaishi-111-may-envoys':'卷111·太祖本纪二·广顺元年五月','songshi-479-yi-shenzheng':'卷479·世家二·西蜀孟氏·伊审徵','xinwudaishi-070-zheng-gong':'卷70·东汉世家·郑珙出使与去世'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年三月至五月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_06_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=951, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='951年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0951_' + code
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
        edge = 'participation_zztj_290_0951_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0951_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','吴越王':'钱弘俶','弘亻叔':'钱弘俶','弘倧':'钱弘倧','蜀主':'孟昶','蜀高祖':'孟知祥','契丹主':'耶律阮','北汉主':'刘崇（刘知远弟）'})
NEW_ALIASES={'伊审征':['伊審徵','伊审徵'],'褒国公主（孟知祥妹）':['褒国公主'],'姚汉英':['姚漢英'],'华光裔':['華光裔']}
NEW_DESCRIPTIONS={'伊审征':'后蜀官员，太原人，《宋史》称伊审徵、字申图，记为并州人。951年由前云安榷盐使任通奏使、知枢密院事。关于母亲及其父婚配，两书叙述不同，具体对应仍待校核。生卒年尚未录入。','褒国公主（孟知祥妹）':'《资治通鉴》记为孟知祥的妹妹、伊审征的母亲。《宋史》另记伊审征之父娶孟知祥之女崇华公主，未将两位公主合并，亲属叙述仍待进一步校核。生卒年未载。','姚汉英':'后周左金吾将军，《旧五代史》称左金吾卫将军。951年五月奉命与华光裔出使契丹，《资治通鉴》记使团被契丹扣留。生卒年未载。','华光裔':'后周前右神武将军。《旧五代史》记他于951年五月己巳与姚汉英一同奉命出使契丹。生卒年未载。'}
april='jiuwudaishi-111-april-grain';may='jiuwudaishi-111-may-envoys';yi='songshi-479-yi-shenzheng';zheng='xinwudaishi-070-zheng-gong';wuyue='xinwudaishi-067-qian-zong-succession'
add('qian_hongchu_marshal','郭威加授钱弘俶诸道兵马都元帅',39,'加吴越王',None,[('帝','加授吴越王诸道兵马都元帅'),('吴越王','获加授诸道兵马都元帅')],when='951年三月己卯赐遣俘虏之后条下，具体加授日未载',place='后周与吴越',note='沿已核钱弘俶主体；弘亻叔是底本拆字写法，不建立新人物。加号不推定实际指挥各地兵马。')
add('huainan_hunger_report','沿淮州镇报告淮南饥民渡淮买粮',40,'夏，四月，','未敢禁止。”',[],when='951年四月壬辰朔',place='淮河沿岸',note='州镇报告未敢禁止，不改写为地方已经禁止过河，也不补造具名奏报者。')
add('guo_allows_grain_purchase','郭威允许淮南饥民到淮北买粮，命州县渡口不得阻止',40,'诏曰：',None,[('帝','要求州县渡口不要阻止淮南饥民买粮')],when='951年四月壬辰朔',place='淮河沿岸',description='郭威回应沿淮州镇报告，表示淮南百姓与后周百姓一样，命州县和渡口不得阻止他们渡淮买粮。',note='这是跨境买粮许可，不等于朝廷免费发粮或已经消除饥荒。')
sup('guo_allows_grain_purchase',40,april,'夏四月壬辰朔，詔沿淮州縣，許淮南人就淮北糴易糇糧，時淮南饑故也。','《旧五代史》同日记允许淮南人到淮北买粮，并说明当时淮南饥荒。','同日同政策印证，买粮不译成无偿赈济。')
add('gao_yanzhao_resigns','高延昭坚决请求辞去后蜀枢密事务',41,'蜀通奏使高延昭','固辞知枢密院，',[('高延昭','以通奏使身份坚决请求辞去知枢密院事务')],when='951年四月伊审征任职以前，具体请辞日未载',place='后蜀',note='请辞与替任分开；原文未提供高延昭请辞的具体原因。')
sup('gao_yanzhao_resigns',41,yi,'廣政十四年，高延昭求解機務，','《宋史》记后蜀广政十四年高延昭请求解除机务。','广政十四年对应951年，与《资治通鉴》任职背景相合，不提前录入后文秦凤军事。')
add('yi_shenzheng_appointed','孟昶任命伊审征为通奏使、知枢密院事',41,'丁未，','知枢密院事。',[('蜀主','任命伊审征掌枢密事务'),('伊审征','由前云安榷盐使获任通奏使、知枢密院事')],when='951年四月丁未',place='后蜀',note='太原为籍贯而非此次任职地点，云安榷盐使是此前职务。')
sup('yi_shenzheng_appointed',41,yi,'急召為通奏使、知樞密院事。','《宋史》也记高延昭请辞以后，伊审徵被急召任通奏使、知枢密院事。','伊审徵与伊审征按同一前云安榷盐使、同年替任高延昭履历对应；徵征字形原文分别保留。')
claim('person',people['伊审征'],'description','《宋史》记伊审徵字申图，是并州人。',41,'伊審徵，字申圖，并州人。','太原与并州为两书籍贯用语，未据文字不同建立另一主体；此前任职由同段其他句另行引用。',source=yi)
claim('person',people['伊审征'],'description','伊审徵此前历任蜀州刺史、云安榷盐使。',41,'以父任，歷蜀州刺史、雲安榷鹽使。','补充早年任职，原文没有给两次任职的具体年份。',source=yi)
relationship('褒国公主（孟知祥妹）','伊审征','母亲',41,'审征，蜀高祖妹褒国公主之子也，','《资治通鉴》明确记母子关系；《宋史》另记其父娶孟知祥之女崇华公主，没有明确说明两位公主是否涉及不同婚次，关系仍保留待核说明。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《宋史》记伊审徵之父延瓌娶孟知祥之女崇华公主。',41,'父延瓌，隨知祥入蜀。知祥僭位，以女妻延瓌，僭封崇華公主。','这与《资治通鉴》所记褒国公主及其辈分不同；本句未直接说伊审徵生母为崇华公主，不据此覆盖母子关系，也不把两位公主合并。',source=yi,relation='conflicts')
add('yi_meng_early_closeness','伊审征年少时与孟昶亲近',41,'少与蜀主相亲狎，','少与蜀主相亲狎，',[('伊审征','年少时与孟昶亲近'),('蜀主','与年少时的伊审征亲近')],year=None,when='伊审征年少时期的追述，具体年份未载',place='后蜀',note='亲狎按亲近解释，不推断性关系或具体共同活动。')
add('meng_consults_yi','伊审征掌枢密后，孟昶向他询问大小政务',41,'及知枢密，','政之大小悉以咨之。',[('伊审征','掌枢密后成为孟昶咨询政务的对象'),('蜀主','向伊审征询问大小政务')],year=None,when='951年任职之后的概述，起止年份未载',place='后蜀',note='长期概述不当成丁未当天一次会议；《宋史》也有相同记述，但相邻升官条跨后续时期。')
sup('meng_consults_yi',41,yi,'昶事無大小，一以咨之。','《宋史》也记孟昶事无大小，都向伊审徵咨询。','该传将此句置于后续任职叙述之后，只印证长期咨询，不用它给每次咨询定951年日期。')
add('yi_wang_evaluation','史书评价伊审征与王昭远相互勾连，后蜀政务逐渐衰败',41,'审征亦以经济为己任，',None,[('伊审征','被史书评价为自任经世济民，却贪侈邪曲'),('王昭远','被史书评价为与伊审征相互勾连')],year=None,when='伊审征掌枢密之后的长期评价，起止年份未载',place='后蜀',note='经济在此为经世济民，不译成现代经济部门职务；蜀政由是浸衰是史家因果评价，不另建无独立证据的确定因果关系。')
add('qian_zong_east_residence','钱弘俶把被废的钱弘倧迁到东府居住',42,'吴越王弘亻叔','居东府，',[('吴越王','迁钱弘倧到东府居住'),('弘倧','被废后迁居东府')],when='951年四月条下，具体迁居日未载',place='东府',note='不把迁居写成重新废立。')
sup('qian_zong_east_residence',42,wuyue,'迎俶立之，遷倧于東府。','《新五代史》也记钱俶即位后，钱倧迁往东府。','《新五代史》把迁居紧接在废立叙述之后，未另列951年日期；只印证迁居地点，不据此改变《资治通鉴》的编年位置。')
add('qian_zong_palace_garden','钱弘俶为钱弘倧建宫室、整治园圃',42,'为筑宫室，','娱悦之，',[('吴越王','为钱弘倧建宫室和整治园圃'),('弘倧','迁居后获建宫室与园圃')],when='951年迁居东府前后，具体施工日未载',place='东府',note='娱悦之是照顾安排的目的，不推断钱弘倧实际情绪。')
add('qian_zong_regular_support','钱弘俶按时节厚赠钱弘倧生活物资',42,'岁时供馈甚厚。',None,[('吴越王','按时节厚赠生活物资给钱弘倧'),('弘倧','获得按时节送来的丰厚供给')],year=None,when='钱弘倧居东府后的长期供给，起止年份未载',place='东府',note='岁时供馈是长期安排，不虚构具体金额与每次馈赠日。')
add('khitan_reports_zhou_offer','契丹派使者向北汉提及田敏来访，并提出岁输十万缗的约定',43,'契丹主遣使如北汉，','约岁输钱十万缗。',[('契丹主','派使者向北汉传达后周使者来访消息及岁输约定'),('北汉主','收到契丹来使传达的信息')],when='951年四月条下，具体使者到达日未载',place='契丹至北汉',note='本句在契丹向北汉遣使之后记岁输十万缗，付款方及约定执行情况未在此展开；不认定后周或北汉已经支付，不称田敏为北汉使者。')
add('liu_chong_zheng_gifts','刘崇派郑珙携厚礼向契丹致谢',43,'北汉主使郑珙','以厚赂谢契丹，',[('北汉主','派郑珙携厚礼致谢契丹'),('郑珙','受命向契丹致谢')],when='951年四月条下、五月辛未郑珙去世以前',place='北汉至契丹',note='使者派遣不推定同日已经到达；厚赂未给金额，不自行换算。')
add('liu_chong_requests_investiture','刘崇以侄皇帝称呼自己，向契丹请求册礼',43,'自称“侄皇帝',None,[('北汉主','以侄皇帝名义致书叔天授皇帝，请求册礼'),('郑珙','携带北汉对契丹的致谢及请求')],when='951年四月出使条下，具体递书日未载',place='北汉与契丹',note='叔侄是外交称谓，不建立血缘叔侄关系；请求册礼不提前写成已获册封。')
sup('liu_chong_requests_investiture',43,zheng,'旻乃遣宰相鄭珙致書兀欲，稱姪皇帝，以叔父事之而已。','《新五代史》也记刘旻派郑珙致书耶律阮，自称侄皇帝、以叔父称对方。','刘旻沿刘崇主体，兀欲沿耶律阮主体；只补外交称谓，不提前录入同段后面的册封。')
add('yao_hanying_khitan','郭威派姚汉英等出使契丹',44,'五月，己巳，','使于契丹，',[('帝','派姚汉英等出使契丹'),('姚汉英','以左金吾将军身份奉命出使')],when='951年五月己巳',place='后周至契丹',note='派遣者由后周本纪上下文及《旧五代史》确认，不把姚汉英当成刘崇的使者。')
sup('yao_hanying_khitan',44,may,'己巳，遣左金吾衛將軍姚漢英、前右神武將軍華光裔使於契丹。','《旧五代史》补记姚汉英的同行使者为前右神武将军华光裔。','同日同出使印证，只补同行者及职务，不外推其后被扣时间。',relation='adds')
pk=person('华光裔',44,'以前右神武将军身份与姚汉英一同奉命出使契丹','己巳，遣左金吾衛將軍姚漢英、前右神武將軍華光裔使於契丹。',source=may)
edge='participation_zztj_290_0951_yao_hanying_khitan_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['yao_hanying_khitan'],role='以前右神武将军身份与姚汉英一同奉命出使契丹',status='draft'))
claim('person_event',edge,'role','华光裔以前右神武将军身份，与姚汉英一同奉命出使契丹。',44,'己巳，遣左金吾衛將軍姚漢英、前右神武將軍華光裔使於契丹。','同行者明确来自《旧五代史》，不补无证据的使团任务。',source=may)
add('khitan_detains_yao','契丹扣留姚汉英等后周使者',44,'遣左金吾将军姚汉英','契丹留之。',[('姚汉英','出使契丹后被扣留')],when='951年五月己巳派遣之后，具体扣留日未载',place='契丹',note='“留之”按扣留使团解释；主书未逐一具名被留者，不额外为华光裔创建确定扣留参与，也不编造扣留原因。')
add('zheng_gong_dies','北汉宰相郑珙在契丹去世',44,'辛未，',None,[('郑珙','以礼部侍郎、同平章事身份出使，在契丹去世')],when='951年五月辛未',place='契丹',note='死亡纪日与姚汉英派遣日分开，不误译为郑珙五月己巳去世。')
sup('zheng_gong_dies',44,zheng,'珙素有疾，兀欲彊之飲，一夕而以醉卒。','《新五代史》记郑珙原有疾病，耶律阮强令他饮酒，郑珙一夜因醉去世。','《资治通鉴》此句只记录死亡地点与日期，饮酒经过作为《新五代史》的独立补充记载，不扩写成有预谋谋杀。',relation='adds')
claim('person',people['郑珙'],'death_year','郑珙于951年五月辛未在契丹去世。',44,'辛未，北汉礼部侍郎、同平章事郑珙卒于契丹。','死亡年来自明确编年日期，旧档案保留，通过事实引用补充。')
add('sun_fangjian_renamed','孙方简为避郭威父亲名讳，更名孙方谏',45,'甲戌，',None,[('孙方简','因避皇考名讳，由方简更名方谏')],when='951年五月甲戌',place='义武军',note='皇考指郭威之父，未展开未经本段核实的父亲姓名；孙方谏沿已有主体及别名，不建立重复人物。')
claim('person',people['孙方简'],'name','孙方简在951年五月甲戌更名孙方谏。',45,'甲戌，义武节度使孙方简避皇考讳，更名方谏。','沿已有孙方简及孙方谏别名，不变更稳定key。')
add('li_yiyin_northern_han_memorial','定难节度使李彝殷派使者向北汉奉表',46,'定难节度使',None,[('李彝殷','派使者向北汉递交表章')],when='951年五月甲戌更名条之后，具体出使日未载',place='定难军至北汉',note='奉表为外交行动，本句未提供表章全文，不据此认定军事结盟或已经出兵。')
reviews={39:'弘亻叔按已核钱弘俶主体复用；加元帅号不等于实际全域指挥。',40:'州镇奏报与诏令分开，未敢禁止不写成已经禁止；旧本纪同日允许淮南人赴淮北买粮印证。',41:'请辞、丁未任命、早年亲近、长期咨询与史家评价分别登记；伊审征和伊审徵按同场履历对应。褒国公主母子关系按通鉴保存，宋史其父娶崇华公主为另项叙述，不合并两位公主；未提前录入后续秦凤战事或宋灭蜀。',42:'迁居、建宫整园及岁时供给分开，新书迁居接在废立后且未单列年，未据此覆盖通鉴951位置。',43:'契丹来使提及田敏及岁输约定，本段未展开付款方与执行，不补成已付款。厚礼出使与请求册礼分开；外交叔侄不建血缘关系，实际册封留待后续段落。',44:'姚汉英出使、扣留和郑珙去世分开；旧史补同行华光裔；新史补郑珙患病及被强令饮酒经过，不扩大为预谋杀害。',45:'方简与方谏已为同一主体；皇考指郭威之父，不误认孙氏之父。',46:'奉表内容未载，不外推结盟及军事承诺。'}
assert not (P/'publication.json').exists()
for n in range(39,47):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(39,47)],next_paragraph=Q[47]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原44—51行连续八段；本年后续正文仍待录入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(39,47)],source_issues_review='原文逐字保留，纸本未核；伊审征亲属叙述差异不强合公主，吴越迁居叙述时间按各书保留。契丹岁输约定不证明实际付款；郑珙饮酒死亡经过标为新五代史补充。',plain_language_review='已逐条核对标题、人物、事件、角色、关系方向、时间与事实说明。引用外使用白话，命令与实际结果、政治称谓与血缘、评价与确定史实分清，不额外安排旧内容重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
