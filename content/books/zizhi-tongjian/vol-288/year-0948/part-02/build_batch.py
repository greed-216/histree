# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 4–8."""
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
COMMIT='53735e0f01570085514ad3900423782c4965fd11'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-948-march','jiuwudaishi-109-zhao-siwan-origin','songshi-253-sun-xingyou','jiuwudaishi-101-march-948']:
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
main_sources = ['tongjian-288-948-march']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p004-p008',
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(4, 9):
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
        citation = f'卷288·乾祐元年（948年三月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_02_{len(B["claims"])+1:04d}'
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
ALIASES.update({'王益':'王益（后汉供奉官）','邪律忠':'耶律忠','麻荅':'麻答'})
NEW_ALIASES={'时知化':['時知化'],'王益（后汉供奉官）':['王益（供奉官）'],'常彦卿':['常彥卿'],'安友规':['安友規'],'乔守温':['喬守溫'],'靖边庭':['靖邊庭'],'田令方':[],'耶律忠':['邪律忠'],'孙方遇':['孫方遇'],'田钦祚':['田欽祚']}
NEW_DEATH_YEARS={'田令方':948}
NEW_DESCRIPTIONS={
 '时知化':'后汉供奉官。《旧五代史》记948年与王益共同将赵匡赞部下三百余牙兵从凤翔部署赴京，这批牙兵后来在长安起事。生卒年未载。',
 '王益（后汉供奉官）':'后汉供奉官。948年奉诏赴凤翔，将赵匡赞牙兵调往京师，到长安受安友规、乔守温迎接。《通鉴》《旧五代史》记赵思绾在这个过程中夺城，《新五代史》则记为随侯益东归时起事，两种记载保留。与其他年代同名王益分开，生卒年未载。',
 '常彦卿':'赵思绾党羽。948年部队被召赴京时，赵思绾向其表达忧惧，常彦卿建议临机应变，不要再说。生卒年未载。',
 '安友规':'948年任永兴节度副使，与乔守温迎接王益，并允许赵思绾部下入城携家眷。赵思绾夺城后，安友规等逃离。《新五代史》把迎接对象写为侯益，异说保留。生卒年未载。',
 '乔守温':'948年任永兴巡检，与安友规迎接奉诏调兵的王益；赵思绾部下获准入城后起事，乔守温等逃离。生卒年未载。',
 '靖边庭':'虢州伶人。948年杀团练使田令方，驱掠州民投赵思绾，经过潼关时遭守军击败，部众溃散。《宋史》补称他因田令方与其妻有私情而愤怒，率数人夜入州署杀人，细节归于该书。生卒年未载。',
 '田令方':'后汉虢州团练使，田钦祚的父亲。948年被伶人靖边庭杀害。《宋史》将此事与田令方和靖边庭妻的私情联系，史书动机叙述与死亡事实分开。出生年未载。',
 '耶律忠':'契丹将领，曾以义武节度副使身份代孙方简任定州节度使。《通鉴》将任命放在契丹皇帝北归时，《旧五代史》记在耶律阮继位后。948年与麻答等焚掠定州、驱走居民并北返，任命次序差异保留。生卒年未载。',
 '孙方遇':'《资治通鉴》记为孙方简奏请任泰州刺史者，与孙氏诸人共同抵御契丹。《宋史》在相应任职处写作行义，是否同人尚待核，没有直接合并。与孙方简、孙行友的具体长幼未据省略称谓确定，生卒年未载。',
 '田钦祚':'《宋史》记田令方之子，田令方任后汉虢州团练使，被靖边庭杀害。传记随后记朝廷录田钦祚为殿直、改供奉官，但具体年月未载。生卒年尚未录入。'}
old='jiuwudaishi-109-zhao-siwan-origin';march='jiuwudaishi-101-march-948';close='jiuwudaishi-101-march-close-948';apr='jiuwudaishi-101-april-dingzhou-948';new='xinwudaishi-053-siwan-seizes-changan';sun='songshi-253-sun-xingyou';transfer='xinwudaishi-049-sun-transfer';back='xinwudaishi-049-sun-reoccupies-dingzhou';tian='songshi-274-tian-lingfang-death';t='948年三月，具体日未载'
add('hou_denigrates_wang','侯益在朝廷指责王景崇恣意横行',4,'侯益盛毁','言其恣横。',[('侯益','在朝廷强烈诋毁王景崇'),('王景崇','遭侯益指责恣意横行')],when=t,place='后汉朝廷',note='恣横归侯益的指控，不当作已独立查实的人物评价。')
add('wang_resentment_hou_promotion','王景崇得知侯益任开封尹，感到不安并怨朝廷',4,'景崇闻益','且怨朝廷。',[('王景崇','因侯益任职而不安、怨恨朝廷'),('侯益','其开封尹任命成为史述背景')],when=t,place='凤翔',note='内心状态是史书记述，不据此直接判定此刻已经公开叛乱。')
add('wang_yi_summons_zhao_troops','后汉派王益赴凤翔，征赵匡赞牙兵入京',4,'会诏遣','征赵匡赞牙兵诣阙，',[('王益','奉诏赴凤翔部署牙兵入京'),('赵匡赞','其牙兵被征召入京')],when=t,place='后汉朝廷、凤翔',note='王益限定后汉供奉官，与宋代同名王益分开。征召命令不等于这些牙兵已到京师。')
sup('wang_yi_summons_zhao_troops',4,apr,'時供奉官時知化、王益，自鳳翔部署前永興節度使趙贊部下牙兵趙思綰等三百餘人赴闕，','《旧五代史》补列时知化与王益共同部署赵匡赞部下三百余牙兵赴京。','只补同次部署的人数与同僚姓名；此段本纪属于四月追述，不把部署改为四月才发生。时知化依该书明确姓名、官职和同次行动建立参与关系，不补其在夺城时的具体遭遇。',relation='adds')
sq='時供奉官時知化、王益，自鳳翔部署前永興節度使趙贊部下牙兵趙思綰等三百餘人赴闕，'
pk=person('时知化',4,'与王益共同部署赵匡赞牙兵赴京',sq,source=apr)
edge='participation_zztj_288_0948_wang_yi_summons_zhao_troops_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=E['wang_yi_summons_zhao_troops'],role='与王益共同部署赵匡赞牙兵赴京',status='draft'))
claim('person_event',edge,'role','时知化与王益共同部署赵匡赞牙兵赴京。',4,sq,'《旧五代史》明确列两名供奉官；补到主书同一调兵事件，不新建重复事件。',source=apr,relation='adds')
add('wang_stirs_zhao_fear','赵思绾等害怕入京，王景崇用言语激动他们',4,'赵思绾等甚惧，','景崇因以言激之。',[('赵思绾','对牙兵被召入京感到恐惧'),('王景崇','利用恐惧用言语刺激牙兵')],when=t,place='凤翔',note='未载具体激动言辞，不补命他们夺城的明确指令。')
add('zhao_chang_discuss_danger','赵思绾担忧到京被杀，常彦卿劝临机应变',4,'思绾途中',None,[('赵思绾','担忧赵匡赞已落朝廷手中，牙兵赴京会被杀'),('常彦卿','劝临机应变，不要继续说')],when='948年三月牙兵东行途中，具体日未载',place='凤翔至长安途中',description='赵思绾向常彦卿说，小太尉赵匡赞已落入朝廷手中，担心自己和部下到京师后都会被杀。常彦卿回答说应临机应变，不要再说。',note='被杀是赵思绾的担忧，不表示朝廷已经下达灭口命令；赵匡赞只是谈话所提背景，不记在场。')
sup('zhao_chang_discuss_danger',4,old,'小太尉蓋謂趙贊也。','《旧五代史》明确解释小太尉指赵贊，即赵匡赞。','赵贊已核沿用赵匡赞，既不误作赵思绾，也不新造小太尉人物。',relation='adds')
sup('wang_yi_summons_zhao_troops',4,new,'高祖遣使者召思綰等，是時侯益來朝，思綰以兵從益東歸。','《新五代史》记召赵思绾部下者为高祖，并写赵思绾随侯益东归。','《通鉴》《旧五代史》这里记王益部署牙兵东行，《新五代史》同行对象与召命阶段不同，保留异说，不将王益、侯益合并。',relation='conflicts')
add('changan_welcomes_wang_yi','安友规、乔守温在长安迎王益，于客亭置酒',5,'癸酉，','置酒于客亭。',[('安友规','以永兴节度副使身份出迎置酒'),('乔守温','以巡检身份出迎王益'),('王益','到长安受两官迎接')],when='948年三月癸酉',place='长安客亭',note='到长安与迎接有明确癸酉；《旧五代史》说明赵思绾据城日为三月二十四，不自行换算公历。')
sup('changan_welcomes_wang_yi',5,new,'益行至永興，永興副使安友規出迎益，飲于郊亭，','《新五代史》记永兴副使安友规在郊亭迎接的是侯益。','迎接对象与《通鉴》的王益不同，各书分别保留，不以新史改掉主书人物。',relation='conflicts')
add('zhao_obtains_entry_permission','赵思绾以带家眷到城东宿为由，请准牙兵入城',5,'思绾前白曰：','友规等然之。',[('赵思绾','请求牙兵入城携家眷到城东住'),('安友规','同意入城请求'),('乔守温','与安友规等同意入城请求')],when='948年三月癸酉',place='长安城外',note='城东已定住处和家属在城中是赵思绾请求中的说辞，不能当作已经逐户核实的事实。')
add('zhao_kills_gate_officer','赵思绾入长安西门，夺州校佩剑将其杀死',5,'时思绾等皆无','思绾遽夺其剑斩之。',[('赵思绾','原无铠甲兵器，入门夺剑杀州校')],when='948年三月癸酉',place='长安西门',note='被杀州校未具姓名，不虚构人；夺剑杀人是实际执行，不仅是威胁。')
add('zhao_followers_kill_guards','赵思绾部众杀十余守门者，分守城门',5,'其徒因','分遣其党守诸门。',[('赵思绾','其部众起事并分守城门')],when='948年三月癸酉',place='长安诸门',note='十余是守门被杀人数，白梃为木棍，不写成此前已持全套铠甲兵器。')
add('zhao_loots_arsenal_occupies_city','赵思绾开库取武器，占据长安；安友规等逃走',5,'思绾入府，','思绾遂据城，',[('赵思绾','入军府劫库取铠仗给部众，占据长安'),('安友规','赵思绾夺城后逃走'),('乔守温','与安友规等逃走')],when='948年三月癸酉',place='长安军府、府库',note='友规等的逃离与夺城结果分别说清，不记为被杀。')
sup('zhao_loots_arsenal_occupies_city',5,old,'思綰劫庫兵以授之，遂據其城，時乾祐元年三月二十四日也。','《旧五代史》明确记赵思绾劫库据城发生在乾祐元年三月二十四日。','保留传统月日；主书癸酉与本纪三月二十四分别记录，不换算现代日期。',relation='adds')
add('zhao_recruits_and_fortifies','赵思绾募集四千余人，十来天内备好守城设施',5,'集城中少年，','战守之具皆备。',[('赵思绾','招集城中少年，修城壕和楼堞、备战守')],when='948年三月据城之后，募集与修备分阶段进行',place='长安',description='赵思绾据城后招集四千余少年，整修城壕、城楼和城墙垛口，十来天内备齐攻守用具。',note='四千余是招集人数，不等于原牙兵或全部居民数。旬日是过程时长，不把所有整备记在夺城当天。')
sup('zhao_recruits_and_fortifies',5,old,'翌日，集城中丁壯得四千餘人，浚池隍，修樓櫓，旬浹之間，戰守皆備。','《旧五代史》补记募集在据城次日进行，称丁壮四千余；修备持续十来天。','次日仅用于募集起点，不推整备全部同日完成；主书少年和旧书丁壮称谓分别保留。',relation='adds')
add('wang_requests_fengxiang_command','王景崇暗示凤翔吏民上表，请他主持军府',5,'王景崇讽','朝廷患之。',[('王景崇','示意吏民上表让自己主持凤翔军府')],when='948年三月，甲戌调整任命之前',place='凤翔、后汉朝廷',note='上表请命和朝廷担忧不等于已经获准凤翔节度使任命。')
add('wang_shouen_yongxing_appointment','后汉调王守恩任永兴节度使，加同平章事',5,'甲戌，','徙保义节度使赵晖为凤翔节度使，并同平章事。',[('王守恩','从静难调永兴节度使，加同平章事')],when='948年三月甲戌',place='静难军至永兴军',note='这是任命，不据此声称王守恩已入被赵思绾占据的长安城。')
sup('wang_shouen_yongxing_appointment',5,march,'甲戌，以邠州節度使、檢校太尉、同平章事王守恩為永興軍節度使，加檢校太師；','《旧五代史》同记甲戌调王守恩到永兴，列前职为邠州，并记加检校太师。','邠州与静难为州名军号；旧书列王原有同平章事，不独立支持这是初次获得该衔。',relation='adds')
add('zhao_hui_fengxiang_appointment','后汉调赵晖任凤翔节度使，加同平章事',5,'甲戌，','并同平章事。',[('赵晖','从保义军调任凤翔节度使，加同平章事')],when='948年三月甲戌',place='保义军至凤翔',note='任命与真正接管凤翔不同，不能把王景崇抵抗忽略成顺利交接。')
sup('zhao_hui_fengxiang_appointment',5,march,'以陜州節度使、檢校太尉、同平章事趙暉為鳳翔節度使；','《旧五代史》同记赵晖由陕州调凤翔，列其原有同平章事。','保义军与陕州同军州称呼；此独立段没重复甲戌，不自行补一个新日期。')
add('wang_ordered_binzhou','后汉任王景崇为邠州留后，令就近赴任',5,'以景崇为','令便道之官。',[('王景崇','被任命邠州留后，受命就近赴任')],when='948年三月甲戌任官段，具体日未另载',place='凤翔至邠州',note='便道之官是命令，就近赴任不等于王景崇已经离开凤翔。')
add('jing_kills_tian_lingfang','靖边庭杀害虢州团练使田令方',5,'虢州伶人','杀团练使田令方，',[('靖边庭','作为虢州伶人杀害团练使'),('田令方','被靖边庭杀害')],when=t,place='虢州',note='未另载杀人干支，不直接套甲戌任官日。')
sup('jing_kills_tian_lingfang',5,tian,'帳下伶人靖邊庭妻有美色，令方私之，邊庭不勝忿。會陝西三叛連衡，關輔間人情大擾。邊庭率其徒數人夜縋入州廨，害令方，','《宋史》补称田令方与靖边庭妻有私情，靖边庭愤怒，率数人夜间越墙入州署杀死田令方。','私情和愤怒是宋史所述动机，不补妻子姓名，也不把陕西三叛连衡背景换算成精确杀人日。',relation='adds')
relationship('田令方','田钦祚','父亲',5,'田欽祚，潁州汝陰人。父令方，漢虢州團練使。','田钦祚传明确父亲身份，引用保持原字；田钦祚未被记为杀人现场参与者。',source=tian)
add('jing_abducts_civilians_joins_zhao','靖边庭驱掠虢州居民，前往投奔赵思绾',5,'驱掠州民，','奔赵思绾。',[('靖边庭','劫持驱赶州民前往投赵思绾'),('赵思绾','成为其准备投奔的对象')],when='948年三月田令方遇害后，具体日未载',place='虢州至长安方向',note='投奔是出发目标，后在潼关溃散，不能说已成功入城加入赵军。')
add('jing_defeated_tongguan','潼关守军击败靖边庭，部众溃散',5,'至潼关，',None,[('靖边庭','在潼关被击败，部众溃散')],when='948年三月，具体日未载',place='潼关',note='守将未具姓名，溃散不等于靖边庭已死或全部部众被杀。')
sup('jing_defeated_tongguan',5,tian,'因掠郡民投趙思綰，至潼關，與守關使者戰，遂敗散。','《宋史》也记靖边庭掠民投赵思绾，到潼关与守军交战后败散。','不将败散推定为本人死亡。')
add('khitan_replaces_sun_with_zhong','契丹以耶律忠代孙方简任义武节度使',6,'初，契丹主北归，','以义武节度副使邪律忠为节度使，',[('耶律德光','主书记其北归到定州时任耶律忠'),('耶律忠','由义武节度副使升任节度使'),('孙方简','原义武节度使被取代')],year=947,when='947年契丹北归时的追叙；任命所属皇帝两书不同',place='定州',note='契丹德光北归属947年背景，不套当前948三月。《旧五代史》将换帅记为耶律阮继位后，独立异说另录，不消除时间冲突。')
sup('khitan_replaces_sun_with_zhong',6,apr,'契丹主死，永康王嗣位，即以蕃將耶律忠代之，','《旧五代史》记契丹皇帝去世、永康王耶律阮继位后，由耶律忠取代孙方简。','与主书把任命放在契丹皇帝北归时不同，任命者及次序存在差异，不将耶律阮与德光合并。',relation='conflicts')
add('sun_ordered_datong','契丹调孙方简任大同节度使',6,'徙故节度使','大同节度使。',[('孙方简','被下令调任大同节度使')],year=947,when='947年定州换帅时的追叙，具体月日未载',place='定州至大同',note='调令不是实际到任；大同、云中、云州书写并列保留。')
sup('sun_ordered_datong',6,transfer,'已而徙方諫於雲中，方諫不受命，率其徒復入狼山。','《新五代史》也记孙方谏被调云中，不受命而回狼山。','方谏沿孙方简；云中是该书表述，不强补精确到任日。')
add('sun_refuses_returns_langshan','孙方简不受调令，率三千人守狼山旧寨',6,'方简怨恚，','控守要害。',[('孙方简','怨恨且担忧被契丹扣留，不受命，退守狼山')],year=947,when='947年契丹调镇之后的追叙，具体月日未载',place='狼山故寨',note='三千是主书记部众约数，担忧入朝被留为孙方简心理，不等于已发生扣押。')
add('khitan_fails_langshan_attack','契丹攻狼山寨未能攻克',6,'契丹攻之，','不克。',[('孙方简','据寨抵御契丹进攻，未被攻克')],year=None,when='孙方简退守狼山之后，具体年、月、日未载',place='狼山',note='承接早年退守的过程，没有独立日期，不将全部围攻强定为当前948年三月。')
add('sun_sends_submission_han','孙方简派使者向后汉请降',6,'未几，','遣使请降，',[('孙方简','在狼山受攻后派人请降后汉')],year=None,when='退守狼山受攻后不久，确切年月未载',place='狼山至后汉朝廷',note='未几只表示相对间隔，不由当前年标题反推确年或使者姓名。')
add('han_restores_sun_command','后汉恢复孙方简旧职，令其抵御契丹',6,'帝复其旧官，','以扞契丹。',[('孙方简','获复义武旧职，承担抵御契丹任务')],year=None,when='孙方简请降后，确切恢复官职年月未载',place='后汉朝廷、定州',note='帝的所指及复职先后两书不同；主书本年刘承祐与新旧史明确高祖刘知远表述不能静默合成同次无争议皇命，未添加无证参与皇帝。')
sup('han_restores_sun_command',6,back,'方諫聞之，自狼山入，據之以歸漢，高祖嘉之，即拜方諫義武軍節度使。','《新五代史》将孙方简归汉受职放在返回定州之后，并明确皇帝为汉高祖刘知远。','与主书先请降复职、再记定州撤军返回的次序不同；主书帝的承接与他书高祖指代差异保留，复职确年暂不硬定。',relation='conflicts')
add('zhong_fears_dingzhou_revolt','耶律忠得知邺都已平，担忧汉人起事',6,'邪律忠闻','常惧华人为变。',[('耶律忠','得知邺都已平后，担忧汉人起事')],year=None,when='后汉平定邺都之后，具体月日未载',place='定州',note='邺都平定为947年末背景，但此担忧持续期不独立给出发生年。')
add('liu_zaiming_ordered_dingzhou_campaign','后汉命刘在明经略定州',6,'诏以成德留后','使出兵经略定州。',[('刘在明','受任幽州道马步都部署，奉命出兵经略定州')],when='948年，定州三月撤军之前，具体下诏日未载',place='成德军、定州',note='这是征讨命令，主书后文明说尚未行军；此前二月任命副职记载保留，不能把同职重复授任推成已获胜。')
add('khitan_burns_abandons_dingzhou','耶律忠、麻答焚掠定州，驱走居民北返',6,'未行，','弃城北去。',[('刘在明','尚未出兵，契丹已撤'),('耶律忠','与麻答等焚掠定州并驱民北返'),('麻答','与耶律忠等撤离定州')],when='948年三月二十七日，确日据《旧五代史》',place='定州至契丹方向',description='刘在明尚未出兵，耶律忠、麻答等已焚掠定州，驱走居民，弃城北返。《旧五代史》补记撤离发生在三月二十七日。',note='事件日三月二十七与四月辛巳收到孙方简奏报分开；不把奏报日当撤军日。')
sup('khitan_burns_abandons_dingzhou',6,apr,'定州孫方簡奏，三月二十七日，契丹棄定州遁去。','《旧五代史》四月辛巳条记录孙方简奏报，契丹在三月二十七日撤离定州。','奏报在四月，撤军在三月，不混淆。',relation='adds')
sup('khitan_burns_abandons_dingzhou',6,apr,'是歲三月二十七日，契丹棄定州，隳城壁，焚室廬，盡驅人民入蕃，惟余空城瓦礫而已。','《旧五代史》再述撤军时破坏城墙、烧毁住宅、驱民北去，城中只剩瓦砾。','该书所说尽驱为史载范围，不另造精确被迁人数。',relation='adds')
add('sun_returns_reoccupies_dingzhou','孙方简从狼山率数百人回据定州',6,'孙方简自狼山','还据定州，',[('孙方简','率数百部众从狼山返回，重新占据定州')],when='948年三月撤军后；《旧五代史》四月乙巳收到返回奏报',place='狼山至定州',note='数百为返回队伍数，不认为此前三千全部死亡；乙巳是奏报日，实际返回未给具体日。')
sup('sun_returns_reoccupies_dingzhou',6,apr,'乙巳，定州節度使孫方簡奏，復入於本州。','《旧五代史》记四月乙巳收到孙方简重新入据定州的奏报。','不据报告日在四月就把实际返回日也定为乙巳。',relation='adds')
add('sun_recommends_xingyou_yizhou','孙方简奏请孙行友任易州刺史',6,'又奏以弟行友','易州刺史，',[('孙方简','奏请孙行友担任易州刺史'),('孙行友','成为奏请任官的对象')],when='948年返回定州后，具体日未载',place='定州、易州',note='奏请任命与朝廷最后授任的明文区分；亲属称谓另记两书异说。')
relationship('孙方简','孙行友','兄长',6,'又奏以弟行友为易州刺史，','复用已有稳定关系；主书明确孙方简称行友为弟，宋史却称孙方简为行友兄子，关系仍有异说，不称已独立定论。')
rkey=B['person_relationships'][-1]['key']
claim('person_relationship',rkey,'description','《宋史》记孙方简为孙行友的兄子，与《资治通鉴》所记兄弟关系不同。',6,'行友兄子方諫名之為姑帥，','方谏沿孙方简，兄子表示兄长之子；既存关系说明已保异说，本次只补独立引用，不覆盖端点。',source=sun,relation='conflicts')
add('sun_recommends_fangyu_taizhou','孙方简奏请孙方遇任泰州刺史',6,'又奏以弟行友','方遇为泰州刺史。',[('孙方简','奏请泰州刺史任职'),('孙方遇','成为奏请泰州刺史的对象')],when='948年返回定州后，具体日未载',place='定州、泰州',note='弟字明确修饰行友，不机械外推方遇具体长幼；与宋史行义姓名不同，未自动合并。')
sup('sun_recommends_fangyu_taizhou',6,sun,'授行友易州刺史，行義泰州刺史。','《宋史》相应位置记授行友易州刺史、行义泰州刺史，与主书方遇姓名不同。','行义与方遇是否同人待核，不将行义加入孙方遇确定别名。宋书写授官，主书写奏请，两种动作表述分别保留。',relation='conflicts')
add('sun_family_defends_border','孙氏诸人往来应敌，契丹有所畏惧',6,'每契丹入寇，','契丹颇畏之。',[('孙方简','与孙氏诸人共同应对契丹入侵'),('孙行友','与孙氏诸人往来应敌'),('孙方遇','作为前述孙氏诸人参与边境抵御')],year=None,when='孙氏分别据守后持续发生，具体战役年份及月日未载',place='定州、易州、泰州一带',note='兄弟奔命指互相赶赴应敌，不是逃亡；契丹畏惧为史家概述，不补每次战役地点、胜负或伤亡。')
add('han_recovers_jin_prefectures','《通鉴》概述晋末陷契丹州县重新归后汉',6,'于是晋末',None,[],when='948年定州恢复后的形势概述，未逐县载日',place='晋末陷契丹的相关州县',note='这是一段所述州县恢复的概述，不扩写成燕云十六州或契丹全部领土都已收回；没有逐县名单，不造名单和疆域。')
add('liu_zaiming_chengde_governor','刘在明正式任成德节度使',7,'丙子，',None,[('刘在明','由成德留后被任命为节度使')],when='948年三月丙子',place='成德军、镇州',note='正式授节度使与此前留后、部署分别记录，不新造同名主体。')
sup('liu_zaiming_chengde_governor',7,close,'以鎮州留後兼幽州一行馬步軍都部署、檢校太傅劉在明為鎮州節度使，加檢校太師，部署如故；','《旧五代史》记刘在明由镇州留后任镇州节度使，加检校太师，幽州部署仍兼任。','镇州、成德为州名军号；该续段未重写丙子，日期依据主书，不臆造新任命日。',relation='adds')
add('ruan_questions_mada','麻答返国，耶律阮责问其失守',8,'麻荅至其国，','责以失守。',[('麻答','北返契丹后受到失守责问'),('耶律阮','以契丹皇帝身份责问麻答')],when='948年定州撤军北返后，具体日未载',place='契丹',note='此时契丹主为947年继位的耶律阮，不沿用先前追叙北归的耶律德光；不造责问具体宫殿。')
add('mada_blames_han_official_summons','麻答辩称征召汉官导致混乱',8,'麻荅服，','致乱耳。”',[('麻答','服罪时把混乱归因于朝廷征召汉官')],when='948年返国受责之后，具体日未载',place='契丹',note='导致混乱是麻答辩解，不直接写成独立确认的唯一因果。')
add('ruan_poison_kills_mada','耶律阮以毒酒杀死麻答',8,'契丹主鸩杀',None,[('耶律阮','用毒酒处死麻答'),('麻答','被契丹皇帝毒杀')],when='948年返国受责后，具体月日未载',place='契丹',note='鸩杀指毒杀，原文明确实际执行；此人沿已有麻答主体，麻荅是字形异写，不另建人物。')
reviews={4:'侯益指责归说话者，王不安为史述；征牙军命令与实际赴京不同，王益限定后汉身份。小太尉据旧史明指赵匡赞，担忧被杀非已下杀令。新史高祖召命、随侯益东归，与主旧王益部署不同，保留。',5:'癸酉到长安、获入城、夺剑杀校、木棍杀门兵、守门、劫库、逃官、据城、次日招集与旬日修备分录。旧补三月24日据城，不换算公历。新史迎侯益异说保留。甲戌调二镇、邠留后命令非顺利赴任。靖杀田、驱掠投赵、潼关败分；宋补动机与父子，不造妻名或靖卒。',6:'初北归换帅是947追叙；主书契丹北归时与旧史阮继位后任命差异保留，没将两帝合并。狼山相对年未明用null；复职帝指代与新旧高祖、先后异说保留。三月27撤定州和四月辛巳/乙巳奏报区别，数百返回非三千全死。孙行友兄弟与宋兄子复用关系并补独立冲突；方遇与行义不无证合并。应敌与州县恢复为概述，不扩成燕云全复。',7:'三月丙子正式节度使区别此前留后，旧补检校太师、部署仍旧，续段未复干支不造日。',8:'返国、皇帝责问、麻答辩解、鸩杀分录。契丹主耶律阮与追叙北归德光区别；杀为执行，麻荅沿麻答，不推实际年月日或唯一混乱因。'}
assert not (P/'publication.json').exists()
for n in range(4,9):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(4,9)],next_paragraph=Q[9]['id'],next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷288原10—14行连续五段，本卷8/69；卷287已有19段，全年27/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(4,9)],source_issues_review='王益与侯益同行记载、契丹换帅所属皇帝及次序、孙复官次序与帝指代、孙氏亲属和方遇/行义姓名异说均保留。三月事件与四月奏报分开，既存主体不因异字重建。',plain_language_review='首次逐条核对人物、事件、日期、角色、关系、出处及事实说明；主语明确，担忧辩解、计划命令与执行分清，引用原字保留。未具名者不造姓名，旧事确年不明null，不固定做发布后二次文案改写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
