# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 51–58."""
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
COMMIT='a2b6b6c94d54b9864bcd3d22174bace805c3e93e'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-948-september-october','xinwudaishi-011-guo-rewards','xinwudaishi-069-gao-renews-tribute']:
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
main_sources = ['tongjian-288-948-september-october']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p051-p058',
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
for n in range(51, 59):
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
        citation = f'卷288·乾祐元年（948年九月至十月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_08_{len(B["claims"])+1:04d}'
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
ALIASES.update({'蜀主':'孟昶','唐主':'李璟','德让':'王德让','怀乂':'赵怀乂','保融':'高保融','陶穀':'陶谷'})
NEW_ALIASES={'王德让':['王德讓'],'赵怀乂':['趙懷乂'],'李彦舜':['李彥舜'],'申贵':['申貴'],'高保融':[],'李屿':['李嶼'],'李㠖':['李嶬'],'陶谷':['陶穀']}
NEW_DESCRIPTIONS={
 '王德让':'王景崇之子。948年十月奉父亲之命到成都见孟昶。生卒年及其他经历未据本段确定。',
 '赵怀乂':'赵思绾之子。948年十月奉父亲之命到成都见孟昶。生卒年及其他经历未据本段确定。',
 '李彦舜':'酸枣人，曾任义成节度使。948年十月王景崇派他等人迎接后蜀援军。生卒年未载。',
 '申贵':'潞州人，后蜀眉州刺史。948年十月奉安思谦命率二千兵前往模壁，在竹林设伏；丁酉早晨用数百兵在宝鸡前列阵，引诱后汉兵追击。后汉兵中伏败退，蜀军追击并攻破宝鸡寨。生卒年未载。',
 '高保融':'高从诲之子，荆南节度副使。948年十月父亲病重时，受命管理内外兵马事务；高从诲去世后，以留后身份暂掌军府。《新五代史》记他是高从诲的第三子。生卒年尚未确定。',
 '李屿':'李崧的弟弟，后汉朝官。李崧旧宅被苏逢吉占有后，李屿与李崧的另一位弟弟李㠖饮酒时曾表达怨言，苏逢吉因此对李崧一方生怨。生卒年及具体官职尚未录入。',
 '李㠖':'李崧的弟弟，后汉朝官，与李屿饮酒时曾对家产被占表达怨言。《旧五代史》同段记㠖，本纪另写嶬；《通鉴》电子底本用山、义的组合占位表示名字。生卒年及具体官职尚未录入。',
 '陶谷':'后汉翰林学士，曾受李崧引荐。《资治通鉴》在李崧遭苏逢吉排挤的背景中记陶谷也加入诬陷。姓名谷、穀按繁简匹配，生卒年尚未录入。'}
october='jiuwudaishi-101-october-948';november='jiuwudaishi-101-november-948';estate='jiuwudaishi-108-li-song-estate';shu='xinwudaishi-064-shu-relief-948';siege='xinwudaishi-053-wang-fengxiang-siege';reward='xinwudaishi-011-guo-rewards';gao='xinwudaishi-069-gao-renews-tribute';a='948年围困河中期间，具体日未载';o='948年十月，具体日未载'
add('li_shouzhen_failed_sorties','李守贞多次出兵突围，均失败而返',51,'李守贞屡出兵','皆败而返。',[('李守贞','多次派兵试图突破长围，均败退')],when=a,place='河中长围',note='多次突围不补次数、参战将领或伤亡总数；尚未攻克河中。')
sup('li_shouzhen_failed_sorties',51,reward,'已而守貞數出兵擊壞連壘，威輒補之，守貞輒復出擊，每出必有亡失。','《新五代史》也记李守贞多次出兵破坏连垒，郭威不断修复，每次出击都有损失。','主书概括败返，新史补修复和反复出击，不将损失解释成明确人数。',relation='adds')
add('li_shouzhen_intercepted_appeals','李守贞向南唐、后蜀和契丹求援，使者被巡逻者捕获',51,'遣人赍','皆为逻者所获。',[('李守贞','用蜡丸传信向三方求援，使者均被捕获')],when=a,place='河中至南唐、后蜀、契丹方向',note='蜡丸用于秘密通信，不记成毒物；求救尚未抵达，不把三方君主全部当实际收到或已答应。')
add('hezhong_food_shortage','河中城内粮食将尽，饿死者日益增多',51,'城中食且尽，','殍死者日众。',[],when=a,place='河中城内',note='粮将尽不写成此时已经完全无粮；没有给出饿死人口数。')
add('zonglun_reassures_li_shouzhen','总伦继续预言李守贞会称帝，李守贞仍然相信',51,'守贞忧形于色，',None,[('李守贞','因忧虑询问总伦，仍接受其预言'),('总伦','用灾异解释危局，宣称李守贞仍将称帝')],when=a,place='河中城内',description='李守贞面露忧色，叫来总伦追问。总伦仍宣称他会成为皇帝，称当前只是星域有灾，要等人马损耗殆尽才会兴起；李守贞仍信以为真。',note='所有称帝和分野灾异说法作为总伦预言，不写成客观天命、真实天文灾害或已经发生的称帝。')
add('wang_sends_de_rang_chengdu','王景崇派儿子王德让到成都见孟昶',52,'冬，十月，','遣其子德让，',[('王景崇','派儿子赴成都'),('王德让','奉父命到成都见孟昶'),('孟昶','成为王德让拜见对象')],when=o,place='凤翔至成都',note='末尾见蜀主于成都同时限定王德让、赵怀乂；未写为人质扣留。')
# Include the shared destination and audience clause for both missions.
for c in B['claims']:c['note']=c['note'].replace('原文：'+span(52,'冬，十月，','遣其子德让，')+'；','原文：'+Q[52]['text']+'；')
add('zhao_sends_huaiyi_chengdu','赵思绾派儿子赵怀乂到成都见孟昶',52,'赵思绾',None,[('赵思绾','派儿子赴成都'),('赵怀乂','奉父命到成都见孟昶'),('孟昶','成为赵怀乂拜见对象')],when=o,place='永兴至成都',note='怀乂是赵思绾之子，以父姓规范姓名，不与王德让合成一人；拜见不推出婚配关系。')
relationship('王景崇','王德让','父亲',52,'王景崇遣其子德让，','王景崇是王德让的父亲，父子方向按明确原文。')
relationship('赵思绾','赵怀乂','父亲',52,'赵思绾遣其子怀乂，','赵思绾是赵怀乂的父亲，不另建重复反向儿子关系。')
add('zhao_hui_takes_fengxiang_west_gate','赵晖击败王景崇从西门派出的军队，攻取西关城',53,'戊寅，','遂取西关城。',[('王景崇','派兵出西门，遭击败'),('赵晖','击破出城兵，夺取西关城')],when='948年十月戊寅',place='凤翔西门、西关城',note='凤翔西关城与上一批河中西关城不同，不合并事件或写成凤翔主城已陷。')
sup('zhao_hui_takes_fengxiang_west_gate',53,october,'戊寅，趙暉奏，破王景崇賊軍於鳳翔城下。','《旧五代史》十月戊寅条记赵晖奏报击败王景崇军。','本纪明确是奏报，《通鉴》记为此日交战；分别保留时间性质，本纪没有独立记夺西关城。',relation='adds')
add('zhao_hui_surrounds_fengxiang','赵晖挖壕围困凤翔主城，多次挑战无人出战',53,'景崇退守','数挑战，不出。',[('王景崇','退守大城，不应赵晖挑战'),('赵晖','挖壕围城，多次挑战')],when='948年十月戊寅交战以后，具体日未载',place='凤翔大城',note='大城是主城，不与已取西关城混合；不出指王景崇不出应战。')
add('zhao_hui_disguises_shu_relief','赵晖用千余人假扮蜀援军，诱王景崇出城',53,'晖潜遣','蜀兵至矣。”',[('赵晖','秘密派千余人模仿蜀旗帜，从南山下来，散布援军到来的说法')],when='948年十月围困凤翔期间，具体日未载',place='凤翔南山一带',note='蜀兵至矣是人为散布的诱敌说法，不记录为真正蜀援军此时到达。')
add('zhao_hui_ambushes_wang_relief_party','王景崇派数千兵迎假援军，被赵晖伏击歼灭',53,'景崇果遣兵',None,[('王景崇','误认蜀援军已至，派数千兵迎接，此后不敢出战'),('赵晖','埋伏截击迎接部队')],when='948年十月假援军诱敌以后，具体日未载',place='凤翔城外',note='数千是概数，尽殪之按史书记载，不补精确死亡数；战后不复出为本次结果。')
sup('zhao_hui_ambushes_wang_relief_party',53,siege,'暉乃令千人潛之城南一舍，偽為蜀兵旗幟，循南山而下，聲言蜀救兵至矣，須臾塵起，景崇以為然，乃令數千人潰圍而出以為應。暉設伏以待之，景崇兵大敗，由是不敢復出。','《新五代史》同记假扮蜀援军引王景崇出城，埋伏击败后使其不敢再出。','新书千人、主书千馀分别保留；新书大败不直接独立确认主书尽殪，也未列十月具体日。')
add('meng_sends_an_shu_relief','孟昶派安思谦率兵救援凤翔',54,'蜀主遣','将兵救凤翔，',[('孟昶','派山南西道节度使安思谦救凤翔'),('安思谦','奉命率军救援凤翔')],when=o,place='后蜀至凤翔',note='出兵命令与后续具体驻地和交战日分开。')
sup('meng_sends_an_shu_relief',54,shu,'乃遣安思謙益兵以東。','《新五代史》也记孟昶增兵派安思谦东进。','传记概述救援过程中多路用兵，不将更早张虔钊、何建、李廷珪等行军全部强定本次十月。')
add('wu_zhaoyi_warns_north_campaign','毋昭裔引用前蜀和后唐教训，劝阻孟昶用兵',54,'左仆射兼','不听，',[('毋昭裔','以左仆射兼门下侍郎、同平章事身份上疏劝阻'),('孟昶','没有采纳劝谏')],when=o,place='后蜀朝廷',description='毋昭裔以李存勖西征和王衍欲北行时不纳群臣劝谏为警戒，劝孟昶慎用兵；孟昶没有听从。',note='两朝旧事作为毋昭裔举例，不在本批另建或重新记作948年事件。')
sup('wu_zhaoyi_warns_north_campaign',54,shu,'昶相毋昭裔切諫，以為不可，然昶志欲窺關中甚銳，','《新五代史》也记毋昭裔极力劝谏，孟昶仍急于图取关中。','该句没有逐字列两朝教训，不作为其完整上疏内容的独立印证。')
add('han_baozhen_qianyang_diversion','孟昶派韩保贞从汧阳出兵，分散后汉兵力',54,'又遣',None,[('孟昶','再派雄武节度使韩保贞出兵分敌'),('韩保贞','领兵从汧阳出击')],when=o,place='汧阳',note='分汉兵之势是行动目的，不当已经成功转移后汉全部兵力；韩保贞沿已有丰德库使主体。')
add('wang_sends_li_yanshun_to_greet','王景崇派李彦舜等迎接蜀军',55,'王景崇遣','逆蜀兵。',[('王景崇','派人迎接援军'),('李彦舜','以前义成节度使身份迎接蜀军')],when='948年十月丙申驻军之前，具体日未载',place='凤翔至蜀军来路',note='逆为迎接，不是抵抗或逆袭蜀军；酸枣是籍贯表述，不误作姓名组成。')
add('an_shu_han_camps_october','安思谦驻右界，后汉兵驻宝鸡',55,'丙申，','汉兵屯宝鸡。',[('安思谦','率蜀军驻右界')],when='948年十月丙申',place='右界、宝鸡',note='后汉兵未列具体将领，不把前文赵晖或郭威无证插入这支驻兵。')
add('shen_gui_sets_bamboo_ambush','申贵率二千兵前往模壁，在竹林设伏',55,'思谦遣','设伏于竹林。',[('安思谦','派眉州刺史申贵出兵'),('申贵','率二千兵前往模壁，设伏竹林')],when='948年十月丙申驻军后、丁酉早晨前',place='模壁、竹林',note='主书直接给二千，不改成数百；数百是下一步出阵诱敌部队。')
claim('person',people['申贵'],'description','申贵是潞州人。',55,'贵，潞州人也。','贵承接本段申贵；籍贯不当本次战场位置。')
add('shen_gui_baoji_ambush_victory','申贵诱后汉追兵中伏，蜀军攻破宝鸡寨',55,'丁酉旦，','破宝鸡寨。',[('申贵','用数百兵列阵诱敌，后汉兵中伏败退后率蜀军追击并攻破宝鸡寨')],when='948年十月丁酉早晨',place='宝鸡、竹林伏地',note='诱敌数百与总兵二千区分；逐北是追败兵，不是向地图正北必然移动。')
add('han_reenters_baoji','蜀军离开后，后汉兵重新进入宝鸡',55,'蜀兵去，','汉兵复入宝鸡。',[],when='948年十月丁酉攻寨后，具体日未载',place='宝鸡',note='复入不等于已经在后续大战击败安思谦；蜀军离开原文未给具体原因。')
add('an_moves_weishui_han_reinforces','安思谦进驻谓水，后汉增兵五千守宝鸡',55,'己亥，','汉益兵五千戍宝鸡。',[('安思谦','进驻底本记作谓水的地点')],when='948年十月己亥',place='谓水、宝鸡',note='底本谓水疑为渭水，保留原载名称及待校说明，不在缺纸核时改地理坐标；后汉增兵将领未具名。')
add('an_withdraws_fengzhou_xingyuan','安思谦因兵粮不足、敌军强大而退驻凤州，随后回兴元',55,'思谦畏之，','贵，潞州人也。',[('安思谦','以粮少敌强为由，辛丑退凤州，随后回兴元')],when='948年十月辛丑退凤州，随后回兴元具体日未载',place='谓水至凤州、兴元',note='畏之及粮少敌强为史书记载和其说辞；不补确切粮额或未载死亡。句末申贵籍贯不作安思谦籍贯。')
add('gao_assigns_baorong_during_illness','高从诲病重，让儿子高保融掌内外兵马',56,'荆南节度使','保融判内外兵马事。',[('高从诲','病重时命高保融掌兵马事务'),('高保融','以节度副使身份判内外兵马事')],when='948年十月癸卯去世前，具体日未载',place='荆南',note='文献为史书追称，不写成生前已获死后谥号；掌兵马不等于此时已获后汉正式节度使任命。')
relationship('高从诲','高保融','父亲',56,'以其子节度副使保融判内外兵马事。','其子承高从诲，高从诲是高保融父亲。')
add('gao_conghui_dies','高从诲病后去世',56,'癸卯，','从诲卒，',[('高从诲','于癸卯去世')],when='948年十月癸卯',place='荆南',note='死日按《通鉴》；旧史十一月辛酉是荆南报告，不直接作为死亡日。')
sup('gao_conghui_dies',56,gao,'乾祐元年十月卒，年五十八，贈尚書令，謚曰文獻。','《新五代史》同记乾祐元年十月高从诲去世，享年五十八，获赠尚书令及文献谥号。','原年与死月相合，未给癸卯；年龄是史载，不机械用现代足岁反推出生年。',relation='adds')
sup('gao_conghui_dies',56,november,'辛酉，荊南奏，節度使高從誨卒。','《旧五代史》十一月辛酉记荆南奏报高从诲去世。','这是消息报告日，与主书十月癸卯去世及新书十月记载可分别记录，不作为同日死亡的独立印证。',relation='adds',field='time_original')
claim('person',people['高从诲'],'death_year','高从诲于948年十月去世。',56,'癸卯，从诲卒，','以当前主书死亡条补充既有主体事实，不改写旧批次档案字段。')
add('gao_baorong_acting_successor','高从诲去世后，高保融以留后身份暂掌军府',56,'保融知留后。',None,[('高保融','在父亲去世后以留后身份暂掌军府')],when='948年十月高从诲去世后，具体任命日未另载',place='荆南',note='知留后是暂掌军府，与后续正式授节度使分开。')
sup('gao_baorong_acting_successor',56,gao,'子保融立。從誨十五子，長曰保勳，次保正，保融第三子也，不知其得立之因。','《新五代史》记高保融继立，并说明他是高从诲第三子，该书不知道为何由他继立。','第三子与继立印证，原因保留未知，不虚构长子失德或父亲遗诏排定。',relation='adds')
add('li_yiyin_aid_then_retreat','李彝殷应李守贞秘密求援出兵，得知河中被围后撤退',57,'彰武节度使','乃退。',[('李彝殷','与高允权不和，受密求援后出兵延丹边境，闻围河中撤退'),('李守贞','暗中向李彝殷求援'),('高允权','与李彝殷不和，其辖境受到屯兵压力')],when='948年十月甲辰奏报之前，出兵及退兵具体日未载',place='延州、丹州边境',note='发兵主语承彝殷，不是李守贞从河中亲自移兵延丹；有隙为背景，不造具体战斗。')
add('gao_reports_li_border_action','高允权报告李彝殷出兵，李彝殷也向朝廷申诉',57,'甲辰，','彝殷亦自诉，',[('高允权','向后汉朝廷报告出兵情况'),('李彝殷','也向朝廷申诉')],when='948年十月甲辰',place='延州、定难军至后汉朝廷',note='以其状闻与自诉是双方陈述，不把后一人的辩词内容自行补出。')
sup('gao_reports_li_border_action',57,october,'甲辰，延州奏，夏州李彜殷先出兵臨州境，欲應接李守貞，今卻抽退。','《旧五代史》同记甲辰延州报告李彝殷先前出兵接应李守贞，如今撤回。','彜殷沿彝殷主体；甲辰为报告，先出兵及撤回日期未载。')
add('han_mediates_gao_li','后汉朝廷调解高允权与李彝殷争端',57,'朝廷和解之。',None,[],when='948年十月甲辰双方报告之后，具体日未另载',place='后汉朝廷、延州、定难军',note='调解不推成双方永久结盟，也不补未具名调解使者。')
add('han_redistributes_feng_li_houses','刘知远进入大梁时，把冯道、李崧的宅第分别赐给苏禹珪、苏逢吉',58,'初，高祖','崧第赐苏逢吉。',[('刘知远','把两名旧臣的宅第赐给苏禹珪和苏逢吉'),('冯道','在真定时，宅第被赐给苏禹珪'),('苏禹珪','获赐冯道宅第'),('李崧','在真定时，宅第被赐给苏逢吉'),('苏逢吉','获赐李崧宅第')],year=947,when='947年刘知远入大梁时的追叙，具体赐宅日未载',place='大梁、真定',note='高祖为刘知远，入大梁在已录947年；当前948年条回述旧事，不记成两名臣子948年仍被留在真定。')
sup('han_redistributes_feng_li_houses',58,estate,'高祖平汴、洛，乃以崧之居第賜蘇逢吉，第中宿藏之物，皆為逢吉所有。','《旧五代史》也记刘知远平汴洛后把李崧宅第赐给苏逢吉，包括宅中埋藏财物。','该句只印证李崧一处，不单独印证冯道宅第给苏禹珪。')
add('su_fengji_takes_li_property','苏逢吉占有李崧宅中藏物和洛阳别业',58,'崧第中','逢吉尽有之。',[('苏逢吉','占有李崧宅中藏物及洛阳别业'),('李崧','宅中藏物及洛阳别业被苏逢吉占有')],year=None,when='947年赐宅以后、李崧归朝前后的追叙，具体占有日期未载',place='李崧宅第、洛阳',note='瘗藏为埋藏之物，不误译成墓葬尸骸；别业为另一处产业，未补面积价值或现代地址。')
add('li_song_cautious_after_return','李崧归朝后谨慎对待后汉权臣，常以病为由闭门',58,'及崧归朝，','多称疾杜门。',[('李崧','认为处境孤立危险，谨慎事权臣，常以病为由闭门')],year=None,when='李崧从真定归朝以后、948年案发以前的追叙，具体日未载',place='后汉朝廷、李崧宅第',note='称疾为本人所称，不作为已诊断疾病；主书没有列他为后汉实际权臣。')
add('li_brothers_complain_estate','李屿和李㠖饮酒时抱怨宅第财产被夺，苏逢吉因此生怨',58,'而二弟屿、','逢吉由是恶之。',[('李屿','与李㠖饮酒时抱怨财产被夺'),('李㠖','与李屿饮酒时抱怨财产被夺'),('苏逢吉','得知怨言后对李崧一方生怨')],year=None,when='李崧归朝后、948年案发前，具体年月未载',place='后汉朝廷，饮宴地点未载',note='原名占位{山义}据旧史同段㠖及本纪嶬显示为李㠖；不改逐字原文，也不误作李嶷。未列苏氏具体子弟姓名。')
sup('li_brothers_complain_estate',58,estate,'崧二弟嶼、㠖，酣酒無識，與楊邠、蘇逢吉子弟杯酒之間，時言及奪我居第，逢吉知之。','《旧五代史》同记李崧二弟李屿、李㠖饮酒时抱怨宅第被夺，苏逢吉得知。','该书名字为㠖，酣酒无识是史书评价，不作为本站定评；另列杨邠子弟但没有具体名字。')
claim('person',people['李㠖'],'aliases','李㠖在《旧五代史》本纪另写嶬。',58,'及其弟司封員外郎嶼、國子博士嶬，','本纪与传记均列李崧的两位弟弟，第二名㠖、嶬为字形差异。当前只核姓名，十一月案发处置待下一连续段录入。',source=november)
relationship('李崧','李屿','兄长',58,'而二弟屿、{山义}，与逢吉子弟俱为朝士，','二弟明示二人均为李崧之弟；李崧是李屿兄长，不另建反向弟弟关系。')
relationship('李崧','李㠖','兄长',58,'而二弟屿、{山义}，与逢吉子弟俱为朝士，','二弟承李崧，占位姓名据旧史校读㠖；不依据列举先后推李屿与李㠖两人的长幼。')
add('li_song_offers_deeds','李崧将两京宅券献给苏逢吉，苏逢吉更加不满',58,'未几，','逢吉愈不悦。',[('李崧','将两京宅券献给苏逢吉'),('苏逢吉','收到宅券后更加不满')],year=None,when='李崧归朝后、948年案发前，具体日期未载',place='大梁、洛阳相关宅产',note='两京为大梁及洛阳，不补宅券确切文本、价格或将献券当正式无争议过户。')
sup('li_song_offers_deeds',58,estate,'嘗以宅券獻蘇逢吉，不悅。','《旧五代史》同记李崧献宅券，苏逢吉不悦。','该书未在此句列两京，情绪及行动相合，不据其后续案发叙述推定献券日。')
add('tao_gu_joins_slander_li','曾受李崧引荐的陶谷也加入对李崧的诬陷',58,'翰林学士',None,[('陶谷','作为翰林学士，虽曾获李崧引荐，仍加入诬陷'),('李崧','曾引荐陶谷，后来受到其诬陷')],year=None,when='李崧归朝后、948年案发前，具体年月未载',place='后汉',note='谮保留为史书定性，不虚构陶谷提交的某份奏章内容或把其等同下一段具体告变仆人。')
reviews={51:'反复突围、求援使被捕、粮将尽饿死增多及总伦预言分录，预言不当事实；新史反复毁垒修垒为补证，不补损失数。',52:'王德让赵怀乂赴成都见孟昶分录，两条父亲关系；末句共同限定，前条引完整段支撑目的地，不推人质。',53:'戊寅出兵战及西关城、围大城、假蜀援军、伏击分录。旧史同日是奏报，时间性质分别保留；新史千人与主千馀、败与尽殪不静默统一。',54:'安思谦救援、毋昭裔劝谏不纳、韩保贞汧阳分敌分录；旧两朝举例不新建948年事件，副书援军不全部强定同日。',55:'迎兵、丙申驻军、二千伏兵、丁酉数百诱敌破寨、汉复入、己亥增兵、辛丑退兵分录。逐北是追败兵，不强地图朝北；谓水疑渭待校，申贵籍贯非安思谦籍贯。',56:'高病时掌兵、癸卯死、保融知留后分录，文献是追称；新史十月龄58不推生年，旧史11月辛酉是消息到达。',57:'李守贞密求援与李彝殷发退兵、甲辰报告及自诉、调解分录，发兵主语李彝殷，未补无名调解者。',58:'赐宅确属947旧事，藏物洛业、李谨事权臣、弟怨言、献券、陶谮各分；㠖/嶬以旧传纪校名，原组合占位保留，下一段案发不提前录。'}
assert not (P/'publication.json').exists()
for n in range(51,59):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(51,59)],next_paragraph=Q[59]['id'],next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷288原57—64行连续八段，本卷58/69；卷287已19段，全年77/88，未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(51,59)],source_issues_review='战日与奏报日、死亡与消息到达分别记录；谓水疑渭水保留待地名校核。李㠖名据旧传㠖和本纪嶬，组合占位原文保留。旧史注陶蒨不作为陶谷确定别名；待下一段继续李案。',plain_language_review='首次逐条核对人物介绍、事件正文、时间说明、参与角色、关系方向及事实说明；明确主语，区分意图、策略、预言与执行及奏报。原文字形保留，未知日期不硬系，追叙赐宅为947年，其他未定年月用null；不追加固定发布后二次全文重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
