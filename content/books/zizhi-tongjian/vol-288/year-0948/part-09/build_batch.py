# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 59–69."""
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
COMMIT='b8ce7838037279cfbdd88a95bcd6fb9f26236396'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-101-november-948','jiuwudaishi-108-li-song-estate']:
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
main_sources = ['tongjian-288-948-li-song-case','tongjian-288-948-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p059-p069',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'songshi-265-li-fang-origin':'卷265·李昉传·籍贯与早年任职','songshi-269-tao-gu-origin':'卷269·陶谷传·姓氏与籍贯','jiuwudaishi-107-shi-punishments':'卷107·史弘肇传·刑杀与军狱','jiuwudaishi-107-yang-yi-collections':'卷107·史弘肇传·杨乙征钱','jiuwudaishi-101-december-948':'卷101·隐帝本纪·乾祐元年十二月','xinwudaishi-010-li-song-burial':'卷10·汉本纪·乾祐元年','xinwudaishi-062-li-jinquan-relief':'卷62·南唐世家·援救李守贞','xinwudaishi-065-hezhou-traps':'卷65·南汉世家·贺州陷阱','tongjian-288-948-li-song-case':'卷288·乾祐元年·李崧案','tongjian-288-948-year-end':'卷288·乾祐元年·年末记载'}
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
for n in range(59, 70):
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
    labels={'songshi-265-li-fang-origin':'卷265·李昉传·籍贯与早年任职','songshi-269-tao-gu-origin':'卷269·陶谷传·姓氏与籍贯','jiuwudaishi-107-shi-punishments':'卷107·史弘肇传·刑杀与军狱','jiuwudaishi-107-yang-yi-collections':'卷107·史弘肇传·杨乙征钱','jiuwudaishi-101-december-948':'卷101·隐帝本纪·乾祐元年十二月','xinwudaishi-010-li-song-burial':'卷10·汉本纪·乾祐元年','xinwudaishi-062-li-jinquan-relief':'卷62·南唐世家·援救李守贞','xinwudaishi-065-hezhou-traps':'卷65·南汉世家·贺州陷阱','tongjian-288-948-li-song-case':'卷288·乾祐元年·李崧案','tongjian-288-948-year-end':'卷288·乾祐元年·年末记载'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐元年（948年十一月至十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_09_{len(B["claims"])+1:04d}'
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
 pk=person(name,n,role,quote,source=source)
 key='participation_zztj_288_0948_'+code+'_'+pk
 assert not any(x['key']==key for x in B['person_events'])
 B['person_events'].append(dict(key=key,person_key=pk,event_key=E[code],role=role,status='draft'))
 claim('person_event',key,'role',name+'：'+role+'。',n,quote,'该人物及行动由这条补充史料明示，未补入《资治通鉴》原文。',source=source)
ALIASES.update({'帝':'刘承祐','唐主':'李璟','蜀主':'孟昶','南汉主':'刘弘熙','楚王希广':'马希广','史宏肇':'史弘肇','{山义}':'李㠖','王凝':'王凝（李屿外甥）'})
NEW_ALIASES={'解晖':['解暉'],'葛延遇':[],'李澄':[],'王凝（李屿外甥）':['王凝'],'李昉':[],'杨乙':['楊乙'],'舒元':['朱元','硃元'],'杨讷':['楊訥','李平'],'徐知新':[],'周光逊':['周光遜'],'王继勋（李守贞将）':['王继勋','王繼勳'],'聂知遇':['聶知遇'],'安康长公主':['安康長公主'],'吴珣':['吳珣']}
NEW_DESCRIPTIONS={
 '解晖':'后汉军司孔目官。史书记载，史弘肇信任他，他在军狱中滥用酷刑，逼受审者作虚假供述。生卒年尚未确定。',
 '葛延遇':'李屿的仆人，替李屿经营贩卖事务。948年与苏逢吉的仆人李澄合谋告发李屿谋反，李崧家族随后遭到诛杀。史书将此案记为冤案。生卒年尚未确定。',
 '李澄':'苏逢吉的仆人。948年与葛延遇合谋告发李屿谋反，史书记载二人因此获赏，并将李崧家族遭诛记为冤案。生卒年尚未确定。',
 '王凝（李屿外甥）':'李崧案供述中被提及的人物，称为李屿的外甥。供述被《资治通鉴》记为李屿受逼自诬，不能据此认定王凝确曾谋反。与晚唐其他同名人物的联系尚未确认，单独建档。生卒年未载。',
 '李昉':'后汉秘书郎，李崧的族侄。李崧案后拜访陶谷，听陶谷自称在此案中出了力而惊惧。《资治通鉴》称真定李昉，《宋史》记深州饶阳人、字明远，籍贯写法分别保留。生卒年尚未录入。',
 '杨乙':'史弘肇的亲信属吏，受命征收归德军府收入。史书记载他仗势骄横，每月征钱一万缗交给史弘肇，当地民众深受其害。生卒年未载。',
 '舒元':'沈丘人，早先以游士身份投靠李守贞。李守贞被后汉围攻后，让他改姓朱，赴南唐求援。《新五代史》记求援者为朱元。生卒年尚未确定。',
 '杨讷':'嵩山道士，早先以游士身份投靠李守贞。李守贞被后汉围攻后，让他改姓李、名平，与舒元通过隐秘道路到南唐求援。生卒年未载。',
 '徐知新':'楚国决胜指挥使。948年十二月奉马希广之命率军救援贺州，救兵在攻城时落入南汉军设置的陷阱，败退后被马希广处死。其他经历尚未确定。',
 '周光逊':'李守贞的副使。948年十二月在河中与王继勋、聂知遇守城西。生卒年尚未确定。',
 '王继勋（李守贞将）':'李守贞的裨将。948年十二月与周光逊、聂知遇守河中城西。与闽国泉州的同名人物没有确认联系，单独建档。生卒年尚未确定。',
 '聂知遇':'李守贞的裨将。948年十二月与周光逊、王继勋守河中城西。生卒年未载。',
 '安康长公主':'前蜀长公主，姓名和具体亲属关系尚未据当前史料确定。948年十二月，徐光溥因用艳辞挑逗她而被罢去宰相职务。',
 '吴珣':'南汉巨象指挥使。《新五代史》记他与吴怀恩攻克贺州，并在城下设置陷阱，击败赶来救援的楚军。生卒年尚未确定。'}
NEW_DEATH_YEARS={'徐知新':948}
oldcase='jiuwudaishi-101-november-948';estate='jiuwudaishi-108-li-song-estate';punish='jiuwudaishi-107-shi-punishments';yang='jiuwudaishi-107-yang-yi-collections';dec='jiuwudaishi-101-december-948';newhan='xinwudaishi-010-li-song-burial';tang='xinwudaishi-062-li-jinquan-relief';hezhou='xinwudaishi-065-hezhou-traps';tao='songshi-269-tao-gu-origin';fang='songshi-265-li-fang-origin'
precase='后汉初年史弘肇掌禁军期间的追叙，具体年月未载'
add('xie_hui_forces_false_confessions','史弘肇任用解晖，军狱受审者被逼作虚假供述',59,'汉法既严，','无不自诬。',[('史弘肇','信任孔目官解晖，任其在军狱中审讯'),('解晖','滥用刑讯，逼受审者作虚假供述')],year=None,when=precase,place='后汉京城军狱',note='锻炼指罗织罪状及刑讯，不按现代训练解释；自诬是被逼承认虚假罪名，不据供词认定受审者确实犯罪。')
sup('xie_hui_forces_false_confessions',59,punish,'軍司孔目吏解暉，性狡而酷，凡有推劾，隨意鍛煉。人有抵軍禁者，被其苦楚，無不自誣以求死所，都人遇之，莫敢仰視。','《旧五代史》也记解晖任军司孔目吏，在军狱中酷刑审讯，受审者作虚假供述。','这是对军狱审讯方式的补证；后文何福殷案不因此提前并入李崧案。')
add('han_three_rebellions_rumors','三处叛乱使人心不安，京城出现惊扰民众的谣言',59,'及三叛连兵，','民间或讹言相惊骇。',[],when='948年河中、永兴、凤翔叛乱期间，具体日未载',place='后汉京城',note='三叛承此前河中、永兴、凤翔；史书没有列出谣言内容，不新造消息。')
add('shi_hongzhao_arbitrary_punishments','史弘肇巡逻京城，擅自施刑杀人，冤死者很多',59,'弘肇掌部禁兵，','莫敢辨诉。',[('史弘肇','掌禁军巡逻京城，不按罪情轻重擅自施刑杀人')],when='948年三处叛乱期间，具体日未载',place='后汉京城',description='史弘肇掌禁军巡逻京城，抓到被指为犯罪的人后，不按罪情轻重和法律规定处置，擅自杀人，或施加残酷刑罚。史书记载，虽盗贼减少，冤死者很多，却无人敢申辩。',note='把盗贼减少与冤死者多同时记录；不把每个被捕者都认作已查明犯罪，也不补死亡人数。')
sup('shi_hongzhao_arbitrary_punishments',59,punish,'然而不問罪之輕重，理之所在，但雲有犯，便處極刑，枉濫之家，莫敢上訴。','《旧五代史》也记史弘肇不问罪情轻重，听说有人犯法就处以极刑，蒙冤家庭不敢上诉。','两书都记滥刑，不由此认定具体死者所涉罪名属实。')
add('li_yu_punishes_ge_for_debts','葛延遇隐瞒经营所得，李屿鞭打并催索欠款',59,'李屿仆夫葛延遇，','督其负甚急，',[('葛延遇','替李屿贩卖经营，多次隐瞒所得'),('李屿','鞭打葛延遇，急催所欠款项')],year=None,when='948年十一月李崧案发生前，经营及追债具体年月未载',place='地点未载',note='经营欺匿、受罚和追债是告变背景，欠款金额未载。')
sup('li_yu_punishes_ge_for_debts',59,estate,'有部曲葛延遇者，逋李嶼船傭，嶼撻之，督其所負，','《旧五代史》记葛延遇拖欠李屿船佣，受到鞭打和催索。','船佣为该书补充，不能把《通鉴》经营欺匿概括为已经给出某项船租契约。',relation='adds')
add('ge_li_cheng_plan_false_report','葛延遇与李澄合谋告发李屿谋反',59,'延遇与苏逢吉之仆','谋上变告屿谋反。',[('葛延遇','与李澄合谋告变'),('李澄','作为苏逢吉的仆人，与葛延遇合谋告变'),('李屿','成为谋反告发的对象')],when='948年十一月甲寅诛杀前，具体告发日未载',place='地点未载',note='这是告发行为，不是真实谋反事件；后文明确记李屿自诬及李氏蒙冤。')
sup('ge_li_cheng_plan_false_report',59,estate,'遇有同輩李澄亦事逢吉，葛延遇夜寄宿於澄家，以嶼見督情告，遂一夕同謀告變。','《旧五代史》记葛延遇在李澄家过夜，诉说被催债的事，二人当夜合谋告变。','该书记告变谋议地点为李澄家；未确定公历日。',relation='adds')
relationship('葛延遇','李屿','仆人',59,'李屿仆夫葛延遇，为屿贩鬻，多所欺匿，','原文明确葛延遇是李屿的仆人，保留这一方向。')
relationship('李澄','苏逢吉','仆人',59,'延遇与苏逢吉之仆李澄谋上变告屿谋反。','原文明确李澄是苏逢吉的仆人，不因与葛延遇同谋推定二人亲属关系。')
add('su_fengji_sends_li_song_to_prison','苏逢吉召来李崧，将他送入侍卫狱',59,'逢吉闻而诱致之，','收送侍卫狱。',[('苏逢吉','得知告变后召来李崧，送入侍卫狱'),('李崧','被苏逢吉召来并送入侍卫狱')],when='948年十一月甲寅诛杀前，具体收押日未载',place='苏逢吉宅第、侍卫狱',note='诱致之承接告变者；召崧明确是李崧。收押与之后诛杀分开记录。')
sup('su_fengji_sends_li_song_to_prison',59,estate,'逢吉覽狀示史宏肇，其日逢吉遣吏召崧至第，從容語及葛延遇告變之事，崧以幼女為托，逢吉遣吏送於侍衛獄。','《旧五代史》还记苏逢吉把告状给史弘肇看，当日召李崧谈告变，李崧托付幼女后被送入侍卫狱。','宏肇与弘肇沿同一既有主体；托付幼女不推出具体姓名或已经获得保护。',relation='adds')
add('li_yu_false_conspiracy_confession','李屿被逼作供述，称家人与李守贞、契丹勾结',59,'屿自诬云：','又遣人召契丹兵。”',[('李屿','作虚假供述，声称亲属与家僮共二十人谋乱'),('李崧','被虚假供述指为参与者'),('李㠖','被虚假供述指为参与者'),('王凝','在虚假供述中被称为李屿外甥和参与者'),('李守贞','被虚假供述指为秘密联系的对象')],when='948年十一月甲寅诛杀前，具体供述日未载',place='侍卫狱',description='《资治通鉴》记李屿受逼作虚假供述，称自己与李崧、李㠖、外甥王凝及家僮共二十人，计划在皇帝灵柩送葬时纵火作乱，秘密联系李守贞并召契丹兵。这些是供述中的指控，不能认作已经发生的谋反。',note='原文明示自诬，计划、联系和召兵都属于虚假供述；不建立真实谋反、结盟或军事合作关系。王凝另建同名区别主体。')
relationship('李屿','王凝','舅父',59,'屿自诬云：“与兄崧、弟{山义}、甥王凝及家僮合二十人，','供述称王凝为李屿的甥，此处仅登记该史料所示亲属称谓；供述被记为自诬，不因此认定二人共同谋反。')
add('su_fengji_alters_accused_count','苏逢吉把案卷中的二十人改成五十人',59,'及具狱上，','“五十”字。',[('苏逢吉','在案卷呈上后把人数由二十改为五十')],when='948年十一月甲寅诛杀前，具体日未载',place='后汉京城',note='二十和五十都是案卷涉及人数，不认作两次已查明的叛军数量，也不是已核死者总数。')
add('han_executes_li_song_family','后汉诛杀李崧兄弟、家属及供词牵连者',59,'十一月，甲寅，','皆陈尸于市。',[('刘承祐','后汉在其在位时下诏诛杀李崧家族及牵连者'),('李崧','被诛杀并陈尸于市'),('李屿','被诛杀并陈尸于市'),('李㠖','被诛杀并陈尸于市')],when='948年十一月甲寅',place='后汉京城市场',note='按诛崧兄弟及二书明确姓名识别三人；不根据前文五十字样补出总死亡人数。王凝被供词提及，但死者名单没有单列他，不单独断定其死亡。')
sup('han_executes_li_song_family',59,oldcase,'十一月甲寅，誅太子太傅李崧及其弟司封員外郎嶼、國子博士嶬，夷其族，為部曲誣告故也。','《旧五代史》同记十一月甲寅诛李崧、李屿、李㠖及其家族，明确归因为部曲诬告；李屿任司封员外郎，李㠖任国子博士。','嶬按此前已核字形复用李㠖；后附诏书是官方罪名，不覆盖叙述所记诬告。',relation='adds')
sup('han_executes_li_song_family',59,newhan,'十一月甲寅，殺太子太傅李崧，滅其族。','《新五代史》也记十一月甲寅杀李崧并灭族。','本纪简记处置及纪日，不独立证明诏书指控为真。')
for name in ['李崧','李屿','李㠖']:
 claim('person',people[name],'death_year',name+'于948年十一月甲寅被诛杀。',59,'十一月，甲寅，下诏诛崧兄弟、家属及辞所连及者，皆陈尸于市。','姓名承接前文李崧及两位弟弟，并由《旧五代史》本纪补充确证；复用人物以事实引用补充，不改旧批次字段。')
add('han_rewards_accusers_public_injustice','葛延遇等因告变获厚赏，时人认为李氏蒙冤',59,'仍厚赏葛延遇等，','时人无不冤之。',[('葛延遇','因告变得到厚赏'),('李澄','作为同谋告变者属于获赏者')],when='948年十一月甲寅诛杀后，具体赏赐日未载',place='后汉京城',note='等承接此前合谋告变者；未给赏赐金额。时人认为冤案按史书记载保留，不虚构具体评论者。')
add('households_fear_servant_accusations','李崧案后，官民家庭担忧被仆役告发和胁迫',59,'自是士民家',None,[],when='948年十一月李崧案后的概括记载，持续时间未载',place='后汉境内',note='往往为所胁制是史书概述，不补出每个家庭和威胁事件，也不推成所有仆役都参与告变。')
# Later conversations and early life facts keep separate dates.
add('li_fang_visits_tao_gu','李昉拜访陶谷，陶谷自称在李崧案中出了力',60,'他日，','昉闻之，汗出。',[('李昉','以秘书郎身份拜访陶谷，听其说法后惊惧出汗'),('陶谷','自称在李崧遭祸一事中出了力')],year=None,when='948年十一月李崧案后的他日，具体年月未载',place='拜访地点未载',note='他日不强定为甲寅当天；陶谷自述不补他具体参与哪些刑讯、案卷或告状。')
relationship('李崧','李昉','族叔父',60,'谷曰：“君于李侍中近远？”昉曰：“族叔父。”','李侍中承接李崧。族叔父是族中叔辈，不写成亲生父亲或亲叔父。')
claim('person',people['李昉'],'description','《宋史》记李昉字明远，深州饶阳人。',60,'李昉，字明遠，深州饒陽人。', '《通鉴》称真定李昉，《宋史》称深州饶阳人；两书籍贯表述分别保留，不把真定二字直接当出生地点。',source=fang)
claim('person',people['李昉'],'description','《宋史》记李昉在后汉乾祐年间中进士并任秘书郎。',60,'漢乾祐舉進士，為秘書郎。','乾祐为948—950年范围；不单由这句话定为948年某日中进士。',source=fang)
add('tao_gu_changes_surname_taboo','陶谷原姓唐，为避石敬瑭名讳改姓陶',60,'谷，邠州人也，',None,[('陶谷','原姓唐，为避后晋高祖石敬瑭的名讳改姓')],year=None,when='后晋石敬瑭在位时期的追叙，改姓具体年月未载',place='邠州',note='讳涉及石敬瑭之瑭字，与唐同音；不定改姓的具体年月，邠州为籍贯，不认作改姓时所在地。')
sup('tao_gu_changes_surname_taboo',60,tao,'陶穀，字秀實，邠州新平人。本姓唐，避晉祖諱改焉。','《宋史》同记陶谷原姓唐，避后晋高祖名讳改姓，并补字秀实、邠州新平人。','穀与谷按此前主体复用；这一段只补姓氏、字号和籍贯，后续父祖故事没有据此全录到948年。',relation='adds')
claim('person',people['陶谷'],'aliases','陶谷改姓前名唐谷。',60,'谷，邠州人也，本姓唐，避晋高祖讳改焉。','原文明确本姓唐，名字谷承传主；以事实引用补充异名，旧主体元数据暂不覆盖。')
add('shi_hongzhao_dislikes_scholars','史弘肇厌恶文士，抱怨他们把武人当作士卒',61,'史弘肇尤恶文士，','每谓吾辈为卒。”',[('史弘肇','说文士轻视自己等人，把他们当作士卒')],year=None,when='后汉初年史弘肇掌禁军期间，具体发言年月未载',place='地点未载',note='轻视之说属于史弘肇本人的抱怨，不认作所有文士确曾这样评价他。')
add('shi_assigns_yang_yi_collections','史弘肇让亲信杨乙征收归德军府收入',61,'弘肇领归德节度使，','委亲吏杨乙收属府公利。',[('史弘肇','兼领归德节度使，让杨乙征收军府收入'),('杨乙','受命征收归德军府收入')],year=None,when='史弘肇兼领归德节度使期间，委派具体年月未载',place='归德军府',note='原文公利作为军府收入记录，不直接说成现代税种或史弘肇私人合法收入。')
add('yang_yi_intimidates_local_officials','杨乙仗势骄横，归德官员和民众畏惧他',61,'乙依势骄横，','乙皆下视之。',[('杨乙','仗史弘肇的权势轻视当地官员，令官民畏惧')],year=None,when='杨乙受命征收归德军府收入期间，具体年月未载',place='归德军辖境',note='副使以下的畏惧不转成自愿臣服或民众支持。')
add('yang_yi_remits_ten_thousand_strings','杨乙每月征钱一万缗交给史弘肇，民众不堪负担',61,'月率钱万缗',None,[('杨乙','每月征钱一万缗交给史弘肇'),('史弘肇','收取杨乙按月送来的钱')],year=None,when='杨乙征收期间的按月记载，起止年月未载',place='归德军辖境',note='月额为一万缗，不当全年收入，也不换算现代币值。')
sup('yang_yi_remits_ten_thousand_strings',61,yang,'聚劍刻剝，無所不至，月率萬緡，以輸宏肇，一境之內，嫉之如仇。','《旧五代史》也记杨乙每月征一万缗交给史弘肇，辖境民众深恶其害。','电子底本聚劍可能为聚敛字形问题，原文保留，不在当前引用中静默改字；金额和月份单位相合。')
# Relief request and deployment; the retrospective first sentence is not assigned to 948.
add('shu_yang_join_li_shouzhen','舒元和杨讷早先以游士身份投靠李守贞',62,'初，','俱以游客干李守贞。',[('舒元','沈丘人，以游士身份投靠李守贞'),('杨讷','嵩山道士，以游士身份投靠李守贞'),('李守贞','接受游士舒元、杨讷投靠')],year=None,when='李守贞受后汉围攻之前的追叙，具体年月未载',place='投靠地点未载',note='游客是游士，不是现代旅游者；沈丘和嵩山分别是人物籍贯及身份地望，不作为投靠地点。')
add('li_shouzhen_sends_disguised_envoys','李守贞让舒元、杨讷改姓名，秘密赴南唐求援',62,'守贞为汉所攻，','间道奉表求救于唐。',[('李守贞','派舒元、杨讷改姓名，通过隐秘道路赴南唐求援'),('舒元','改姓朱，奉表向南唐求援'),('杨讷','改姓李、名平，奉表向南唐求援')],when='948年李守贞受围攻后、南唐退兵前，求援具体月日未载',place='河中至南唐',note='硃按繁简规范作朱，舒元与朱元、杨讷与李平为原文明示改名；与此前被捕的匿名使者分开，不假定全部求援失败。')
add('cha_wei_request_relief_army','查文徽和魏岑请求南唐出兵响应李守贞',62,'唐谏议大夫',None,[('查文徽','以谏议大夫身份请求出兵'),('魏岑','以兵部侍郎身份请求出兵')],when='948年李守贞使者求援后，具体日未载',place='南唐朝廷',note='此处是请求，下一段才记录李璟命令，不能合并成两臣自行发兵。')
add('li_jing_deploys_hezhong_relief','李璟任命李金全等统领救援河中的军队',63,'唐主命','军于沂州之境。',[('李璟','命李金全领军、刘彦贞为副，查文徽监军、魏岑沿淮巡检'),('李金全','以北面行营招讨使身份率军救河中，驻沂州境'),('刘彦贞','以清淮节度使身份担任副帅'),('查文徽','担任监军使'),('魏岑','担任沿淮巡检使')],when='948年十一月丙寅退兵以前，出兵命令具体日未载',place='南唐至沂州境',note='救援目标是河中，驻兵地是沂州境，不写为已经抵达河中。招讨与他书招抚职名差异并列。')
sup('li_jing_deploys_hezhong_relief',63,tang,'六年，漢李守貞反河中，遣其客將朱元來求援，景以潤州節度使李金全為北面行營招撫使，兵攻沭陽，','《新五代史》同记朱元向李璟求援，李金全任北面行营招抚使，并记兵攻沭阳。','该书职名为招抚，《通鉴》为招讨；沭阳行动作为该书补充，不与沂州地名直接合并，未给具体日。',relation='adds')
add('li_jinquan_refuses_stream_attack','侦骑请求攻击涧北后汉兵，李金全禁止越涧',63,'金全与诸将方会食，','敢言过涧者斩！”',[('李金全','拒绝侦骑攻击涧北汉兵的建议，禁止越涧')],when='948年十一月丙寅退兵之前，具体日未载',place='沂州境内涧边',note='数百羸弱后汉兵是侦骑所报；拒绝攻击尚不是已打胜仗。涧名和侦骑姓名未载。')
add('li_jinquan_ambush_revealed_evening','入夜伏兵四起，李金全提醒诸将贸然进攻的危险',63,'及暮，','曏可与之战乎？”',[('李金全','听到伏兵发动后，反问此前是否能贸然交战')],when='948年十一月丙寅退兵前同日傍晚，具体日未载',place='沂州境内涧边',note='金鼓是军事声响，不说成南唐军遭全歼；伏兵将领未具名，不添加郭威等人。')
add('southern_tang_withdraws_haizhou','南唐军缺乏斗志，救援难以抵达河中，退保海州',63,'时唐士卒厌兵，','唐兵退保海州。',[('李金全','所领南唐军退保海州')],when='948年十一月丙寅',place='沂州境至海州',description='《资治通鉴》记南唐士卒厌战、缺乏斗志，河中又太远，难以救援。十一月丙寅，南唐军退保海州。',note='记录士气和距离为主书记载；当前河中仍在围困中，不能把后续949年李守贞败亡倒填为此次退军原因。与《新五代史》闻守贞已败才撤军的记载分别保留。')
sup('southern_tang_withdraws_haizhou',63,tang,'兵攻沭陽，聞守貞已敗，乃還。','《新五代史》记南唐军攻沭阳，听说李守贞已经失败后撤回。','该书撤军原因与《通鉴》948年十一月因厌战、路远退军的记载不同；李守贞最终败亡在后续949年，不能用这一概述把主书当前退军改定949年。',relation='conflicts')
sup('southern_tang_withdraws_haizhou',63,dec,'兗州奏，淮賊先於沂州界立柵，前月十七日已歸海州，為李守貞牽制也。','《旧五代史》十二月条记兖州奏报南唐军曾在沂州境筑寨，前月十七日退回海州，为李守贞牵制后汉军。','前月按十二月上下文为十一月；这是十二月奏报，不把撤军写成十二月发生。贬称按原文保留，不用于本站主体名称。',relation='adds')
add('li_jing_requests_trade_and_pardon','李璟致书后汉请恢复商旅往来、赦免李守贞，未获答复',63,'唐主遗帝书谢，',None,[('李璟','送信致歉，请求恢复商旅往来并赦免李守贞'),('刘承祐','其朝廷收到南唐请求后没有答复'),('李守贞','成为请求赦免的对象')],when='948年十一月南唐退兵后，送信及接收具体日未载',place='南唐至后汉朝廷',note='不报是未答复，不说成已经恢复贸易、批准赦免或拒绝使者入境。')
sup('li_jing_requests_trade_and_pardon',63,dec,'淮南偽主李璟奉書於帝，云：「先因河府李守貞求援，又聞大國沿淮屯軍，當國亦於境上防備。昨聞大朝收軍，當國尋已徹備，其商旅請依舊日通行。」朝廷不報。','《旧五代史》十二月条保留李璟书信，称因李守贞求援及沿淮屯兵而戒备，请恢复商旅往来，后汉未答复。','这是李璟在信中的解释，不直接认定后汉确已全面收兵；所引信文未写请赦李守贞，不能由该书独立印证这一请求。',relation='adds')
add('liu_zhiyuan_buried_ruiling','刘知远葬于睿陵，庙号高祖',64,'壬申，',None,[('刘知远','身后葬于睿陵，庙号高祖')],when='948年十一月壬申',place='睿陵',note='葬礼与此前死亡分开，睿文圣武昭肃孝皇帝为刘知远的身后称号；不重新记一次死亡。')
sup('liu_zhiyuan_buried_ruiling',64,newhan,'壬申，葬睿文聖武昭肅孝皇帝于睿陵。〈在河南告成縣。〉','《新五代史》同记十一月壬申葬刘知远于睿陵，并注睿陵在河南告成县。','县名是历史地名补充，没有据此添加现代坐标。',relation='adds')
# December appointments and southern campaigns.
add('gao_baorong_formal_governor','后汉任命高保融为荆南节度使、同平章事',65,'十二月，',None,[('刘承祐','在位朝廷任命高保融'),('高保融','获正式任命为荆南节度使、同平章事')],when='948年十二月丁丑',place='荆南、后汉朝廷',note='正式任命与此前暂掌军府分开；同平章事为所授官衔，不说明他已入京实际主持中央政务。')
sup('gao_baorong_formal_governor',65,dec,'十二月丁丑，荊南節度副使、檢校太傅、行峽州刺史高保融起復，授荊南節度使、檢校太尉、同平章事、渤海郡侯。','《旧五代史》同记十二月丁丑高保融起复，任荆南节度使，并加检校太尉、同平章事、渤海郡侯。','所授衔爵为该书补充；起复按父丧背景记录，不推出葬父具体日。',relation='adds')
add('wu_huaien_ordered_attack_chu','刘弘熙任命吴怀恩领军攻楚、进攻贺州',66,'辛巳，','攻贺州。',[('刘弘熙','任吴怀恩开府仪同三司、西北面招讨使，命其攻楚'),('吴怀恩','由内常侍受任招讨使，率军攻贺州')],when='948年十二月辛巳',place='南汉至贺州',note='南汉主沿既有刘弘熙主体，任命与后续破城、楚援兵失败分开。')
add('ma_xiguang_sends_xu_relief','马希广派徐知新等率五千兵救贺州',66,'楚王希广遣','将兵五千救之。',[('马希广','派决胜指挥使徐知新等救贺州'),('徐知新','率五千兵赶往贺州救援')],when='948年十二月南汉攻贺州后，出兵具体日未载',place='楚国至贺州',note='五千是出援总兵，不作为后续死亡人数；不补其他未具名指挥官。')
add('southern_han_captures_hezhou_sets_traps','南汉先攻克贺州，在城外设置可启动的陷阱',66,'未至，','自堑中穿穴通阱中。',[],when='948年十二月楚援军到达前，具体日未载',place='贺州城外',description='楚援军到达前，南汉已攻克贺州。南汉军在城外挖大坑，覆盖竹箔和泥土，设置机关，并从壕沟挖洞通入坑中，以便启动陷阱。',note='挖坑、机关和暗穴按主书记载；不补现代工程尺寸，也不把吴怀恩记作亲手操作机关者。')
extra_actor('southern_han_captures_hezhou_sets_traps',66,'吴珣','《新五代史》记他参与攻克贺州并主持挖设陷阱',hezhou,'晟乃遣巨象指揮使吳珣、內侍吳懷恩攻賀州，已克之，楚人來救，珣鑿大穽於城下，覆箔於上，以土傳之，')
sup('southern_han_captures_hezhou_sets_traps',66,hezhou,'晟乃遣巨象指揮使吳珣、內侍吳懷恩攻賀州，已克之，楚人來救，珣鑿大穽於城下，覆箔於上，以土傳之，','《新五代史》还列巨象指挥使吴珣参与攻贺州，并把挖设陷阱的行动记在吴珣名下。','该书补充具名将领；主书未列吴珣，不改写主书原文，也不把后文数州全部定为这次同日攻陷。',relation='adds')
add('chu_relief_falls_hezhou_traps','楚援军攻城落入陷阱，南汉出击，楚军死者数以千计',66,'知新等至，','楚兵死者以千数，',[('徐知新','率楚援军攻城，军队陷坑后遭南汉进攻')],when='948年十二月楚援军到贺州后，具体日未载',place='贺州城外',note='悉陷和死者以千数按史书概括，未精确给出全军死亡数；不能把出援五千直接写成全部战死。')
sup('chu_relief_falls_hezhou_traps',66,hezhou,'楚兵迫城，悉陷穽中，死者數千，楚人皆走。','《新五代史》也记楚军逼近城墙后陷坑，死亡数千，其余逃走。','数千为概数，不能反推出具体存活和逃归人数。')
add('ma_xiguang_executes_xu_zhixin','徐知新等败退回国，被马希广处死',66,'知新等遁归，','希广斩之。',[('徐知新','败退回楚后被处死'),('马希广','处死败退的徐知新等人')],when='948年十二月贺州战败以后，具体处死日未载',place='楚国，处死地点未载',note='斩之承接徐知新等，其他被斩者姓名未载，不补进出征或死亡名册。')
add('southern_han_captures_zhaozhou','南汉军随后攻陷昭州',66,'南汉兵复陷昭州。',None,[],when='948年十二月贺州交战后，具体日未载',place='昭州',note='原文未列攻昭州主将，不把吴珣或吴怀恩直接当作已明示主将。')
# Second Shu relief and Guo Wei's interrupted journey.
add('wang_requests_shu_relief_again','王景崇多次告急，孟昶再次命安思谦救援',67,'王景崇累表','再出兵救之。',[('王景崇','多次向后蜀上表告急'),('孟昶','再次命安思谦救凤翔'),('安思谦','再次奉命率军救援')],when='948年十二月壬午驻凤州之前，命令具体日未载',place='凤翔至后蜀朝廷',note='第二次出兵与十月第一次援军分别记录；累表不给出确切次数。')
add('an_requests_four_hundred_thousand_grain','安思谦从兴元驻凤州，请先运粮四十万斛再出境',67,'壬午，','乃可出境。',[('安思谦','从兴元进驻凤州，请求先运四十万斛粮食才出境')],when='948年十二月壬午',place='兴元至凤州',note='四十万斛是请求数量，不是已得到的粮食，也不换算现代重量。')
add('meng_doubts_an_sends_grain','孟昶怀疑安思谦进军意愿，仍拨米数万斛支援',67,'蜀主曰：','以馈之。',[('孟昶','对安思谦进军意愿表示怀疑，仍从兴州、兴元拨米支援'),('安思谦','所部获拨数万斛米')],when='948年十二月壬午请求之后、戊子进军之前，具体日未载',place='兴州、兴元至安思谦军',note='四十万请求与数万拨发分开；原文没有说明粮食全部送达的确切日，孟昶质疑是其判断。')
add('shu_captures_jiankuo_andu_fort','安思谦驻散关，派高彦俦、申贵攻破箭筈安都寨',67,'戊子，','破之。',[('安思谦','进驻散关，派高彦俦、申贵攻后汉寨'),('高彦俦','以马步使身份攻寨'),('申贵','以眉州刺史身份攻寨')],when='948年十二月戊子',place='散关、箭筈安都寨',note='箭筈安都寨保持底本名称，不无证拆为两个不同寨；地理位置待核。')
add('an_defeats_han_yunutan_moves_mobi','安思谦在玉女潭击败后汉军，进驻模壁',67,'庚寅，','思谦进屯模壁。',[('安思谦','击败后汉军，使其退驻宝鸡，自己进驻模壁')],when='948年十二月庚寅',place='玉女潭、宝鸡、模壁',note='击败后的双方驻地分别记录，后汉将领没有具名，不无证添加赵晖作为亲战者。')
add('han_baozhen_halts_shenqian','韩保贞出新关驻陇州神前，双方都未推进交战',67,'韩保贞出新关，',None,[('韩保贞','出新关后驻陇州神前，后汉军不出战，他也不敢前进')],when='948年十二月壬辰驻军，出新关具体日未另载',place='新关、陇州神前',note='双方不出不进不建为已交战或蜀军攻克陇州；神前保留待地名校核。')
add('zhao_hui_asks_guo_wei_relief','赵晖向郭威告急，郭威亲自前往救援',68,'赵晖告急','威自往赴之。',[('赵晖','因蜀军来援向郭威告急'),('郭威','亲自出发前往救援赵晖')],when='948年十二月蜀军再次来援期间，具体出发日未载',place='河中至凤翔方向',note='赴援是已出发，并不表示已抵达凤翔或与安思谦交战。')
add('li_shouzhen_posts_west_defenders','李守贞派周光逊、王继勋和聂知遇守河中城西',68,'时李守贞遣','守城西，',[('李守贞','派副使及两名裨将守城西'),('周光逊','以副使身份守城西'),('王继勋（李守贞将）','以裨将身份守城西'),('聂知遇','以裨将身份守城西')],when='948年十二月郭威赴援期间，具体布防日未载',place='河中城西',note='王继勋是河中李守贞部将，与此前闽国泉州同名人物没有确证联系，使用独立稳定key。')
add('guo_warns_bai_liu_breakout','郭威提醒白文珂、刘词严防李守贞趁机突围',68,'威戒白文珂、','尔曹谨备之！”',[('郭威','离开前提醒城西精兵可能趁他离开突围'),('白文珂','受命严防突围'),('刘词','受命严防突围')],when='948年十二月郭威赴援期间，具体日未载',place='河中围城军',note='郭威对突围的判断是戒备预期，不记成此时已发生突围。后续949年实际袭寨另录。')
add('guo_returns_after_shu_grain_exhaustion','郭威到华州，听说蜀军粮尽撤去，于是返回',68,'威至华州，','威乃还。',[('郭威','到华州后因听说蜀军粮尽撤去而返回'),('安思谦','所领蜀军被报告因粮尽撤去')],when='948年十二月郭威赴援途中，具体日未载',place='华州、返回河中方向',note='闻为郭威收到的消息；不说郭威亲眼见蜀军退走，也不虚构双方战斗。下年安思谦退凤州另有纪日，不能并作本段同日。')
add('han_baozhen_retires_gongchuan','韩保贞听说安思谦撤军，也退保弓川寨',68,'韩保贞闻',None,[('韩保贞','得知安思谦撤军后，退保弓川寨'),('安思谦','撤军消息使韩保贞随后退兵')],when='948年十二月安思谦撤军消息传来后，具体日未载',place='陇州神前至弓川寨',note='依据原文的消息与退兵先后，不将二人写成同路撤军。')
add('xu_guangpu_dismissed_princess','徐光溥因用艳辞挑逗安康长公主，被罢去宰相职务',69,'蜀中书侍郎',None,[('徐光溥','因用艳辞挑逗前蜀安康长公主，被罢去宰相职务'),('安康长公主','成为徐光溥用艳辞挑逗的对象')],when='948年十二月丁酉',place='后蜀朝廷',description='徐光溥因用艳辞挑逗前蜀安康长公主，在十二月丁酉被罢去宰相职务，保留本官。',note='罢守本官是罢相而保留本官，不写成全部官职被夺或处死；未推定双方恋爱、婚姻或公主接受挑逗。')
reviews={
59:'区分军狱酷刑、告变谋议、被捕、自诬供词、改卷、诛杀及获赏。谋反指控不是已核事实；李氏三兄弟身份及诛日以新旧五代史校核，王凝仅为供词中具名者，未单独认定死亡。',
60:'李昉与陶谷对话为案后的他日，不强定年月；族叔父按宗族辈分登记。真定与深州饶阳籍贯写法并列，陶谷避讳改姓为后晋旧事，字号由宋史补充。',
61:'史弘肇对文士的抱怨、委派杨乙、杨乙骄横及每月征钱分别记录，委派年月未知；新旧字形不影响主体识别，月额不能外推年度总额。',
62:'游士投靠属于旧事；改名和向南唐求援在后汉围攻期间。舒元与朱元、杨讷与李平按原文明示改名识别，查文徽魏岑请求与实际出兵分开。',
63:'南唐出兵、侦骑请战、李金全禁攻、伏兵出现、退海州及致书分录。沂州与沭阳、招讨与招抚分别记；新五代史闻守贞败后撤军与通鉴厌战路远的记载保留差异，旧本纪补奏报和信文。',
64:'刘知远葬礼不重新记为死亡；与新旧本纪十一月壬申对照。新五代史注告成县为历史地名，没有补现代坐标。',
65:'丁丑正式授节度使与此前高保融暂掌军府分开，旧本纪补起复与所加衔爵，不推实际入京执政。',
66:'南汉发兵、楚军救援、先陷贺州与设坑、楚兵中伏、败将被斩、再陷昭州分录；吴珣由新五代史独立补充。五千出援与数千战死不是同一统计，后续其他州不强定当日。',
67:'再次蜀援与十月援军分开；四十万斛是请求、数万斛是拨发。壬午戊子庚寅壬辰逐日分录，箭筈安都寨及神前等保留原载地名待核。',
68:'郭威赴援尚未到凤翔，守城西将领及防突围预警分别记录。河中王继勋与泉州同名者分开，郭威在华州收到退军消息后返回；下一年实际袭寨不提前录入。',
69:'徐光溥罢相保留本官，不写成全部罢官；安康长公主姓名和具体亲支尚未确认，不凭封号推父亲、婚配或两人恋爱。'}
assert not (P/'publication.json').exists()
for n in range(59,70):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(59,70)],next_paragraph='zztj-v288-y0949-p001',next_volume=288,next_year=949,supplements=supplements,excluded_non_body=[],coverage='卷288原65—75行连续十一段，处理至948年最后一段；年度完成须等本批发布及跨卷88段审计。下一年正文从原79行开始，76—78行为结构项。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(59,70)],source_issues_review='李崧案供述明确是自诬；《旧五代史》本纪李鳷等字形不作新增别名。旧传注陶蒨仍不直接合并别名。南唐退军原因与时间概述保留异说，李昉地望写法并列；旧传聚劍疑字、安康公主亲支与数处地名保留待核。',plain_language_review='首次逐条检查新增人物介绍、事件标题正文、时间地点解释、参与角色、关系方向与事实说明。引用保持原字；对自诬、侦骑报告、本人说辞、命令与实际行动分别说明。追叙及未确定年月使用null；未改写复用人物的已发布元数据，不安排固定发布后二次全文重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
