# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 8–12."""
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
COMMIT='77bbd325fb94c5e1dfb482972cb6de0b03c635d5'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-opening','xinwudaishi-062-chen-hui-later','jiuwudaishi-102-october-949','jiuwudaishi-100-july-transfers']:
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
main_sources = ['tongjian-289-950-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p008-p012',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-103-february-950':'卷103·隐帝本纪·乾祐三年二月','jiuwudaishi-103-march-950':'卷103·隐帝本纪·乾祐三年三月','jiuwudaishi-105-liu-shenjiao-death':'卷105·刘审交传·去世与汝州民众追念','jiuwudaishi-102-yang-xin-father':'卷102·隐帝本纪·乾祐二年六月杨信奏报'}
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
for n in range(8, 13):
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
    labels={'jiuwudaishi-103-february-950':'卷103·隐帝本纪·乾祐三年二月','jiuwudaishi-103-march-950':'卷103·隐帝本纪·乾祐三年三月','jiuwudaishi-105-liu-shenjiao-death':'卷105·刘审交传·去世与汝州民众追念','jiuwudaishi-102-yang-xin-father':'卷102·隐帝本纪·乾祐二年六月杨信奏报'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年正月、二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_02_{len(B["claims"])+1:04d}'
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


ALIASES.update({'帝':'刘承祐','吴越王':'钱弘俶','越匡赞':'赵匡赞','赵赞':'赵匡赞','杨信':'杨承信','郭瑾':'郭谨'})
NEW_ALIASES={'马先进':['馬先進']}
NEW_DESCRIPTIONS={'马先进':'福州将领。950年南唐进军福州时被陈诲俘获。《资治通鉴》把被俘记在查文徽到达福州之前；《新五代史》叙在查文徽被俘之后，还记李璟把他送回吴越。时序差异保留。生卒年未载。'}
feb='jiuwudaishi-103-february-950';mar='jiuwudaishi-103-march-950';liu='jiuwudaishi-105-liu-shenjiao-death';yang='jiuwudaishi-102-yang-xin-father';october='jiuwudaishi-102-october-949';july='jiuwudaishi-100-july-transfers';fuzhou='xinwudaishi-062-chen-hui-later'
add('guo_wei_returns_border','郭威从北方巡边返回',8,'甲申，','北边还。',[('郭威','从北方巡边返回')],when='950年二月甲申',place='后汉北部边境及朝廷',note='北边返回与此前临边请兵被止是不同记载，不据此补一场对契丹战争。')
sup('guo_wei_returns_border',8,feb,'甲申，樞密使郭威巡邊回。','《旧五代史》同日记枢密使郭威巡边返回。','同一日期和行动，补职务，不造两次返回。')
add('fuzhou_invites_zha','福州来人声称吴越军已离城，邀请查文徽主持福州',8,'福州人或','请文徽为帅。',[('查文徽','接到福州来人关于吴越军已撤离的消息与邀请')],when='950年二月条下，查文徽进军福州以前，具体日未载',place='建州',note='这是诱导消息，不能作为吴越军已真实撤城的事实。来人未具名，不推吴程亲自到建州。')
sup('fuzhou_invites_zha',8,fuzhou,'八年，福州詐言「吳越戍兵亂，殺李仁達而遯」，遣人請建州節度使查文徽，','《新五代史》明确说福州虚报吴越驻军哗变、杀李仁达后离去，邀请查文徽。','这是谎报内容，李仁达已在此前记载死亡，不另建950年被杀事件。查文徽职称留后、节度使在两书不同，分别保留。',relation='adds')
add('zha_sends_chen_down_min','查文徽相信来人，派陈诲率水军沿闽江进军',8,'文徽信之，','步骑继之。',[('查文徽','相信来人消息，率步骑接在水军后出发'),('陈诲','奉命率水军沿闽江先行')],when='950年二月条下，查文徽到达福州以前，具体出发日未载',place='建州、闽江',note='陈诲沿既有剑州刺史主体，但946年同名被杀记载的冲突仍待核，不定死年。')
add('chen_hui_captures_ma','陈诲水军抵达福州城下，击败守军并俘获马先进',8,'会大雨，','马先进等。',[('陈诲','水涨时率水军急进，击败福州兵'),('马先进','被陈诲率领的南唐水军俘获')],when='950年二月条下，查文徽庚寅到达福州之前',place='闽江、福州城下',description='《资治通鉴》记大雨水涨，陈诲一夜行七百里，到福州城下击败守军，俘获马先进等将领。',note='七百里为史书所记行程，不换算现代距离或保证其准确；新史俘马在查被俘后，时序差异保留。')
sup('chen_hui_captures_ma',8,fuzhou,'文徽被擒。誨與越人戰，大敗之，獲其將馬先進。','《新五代史》记陈诲俘获马先进，但把此事叙在查文徽被俘之后。','同一将领与战果，两书先后不同，不强定为两次俘获，也不抹去通鉴先叙水军获胜。',relation='conflicts',field='time_original')
add('wu_cheng_feigned_welcome','查文徽抵达福州，吴程派数百人假意迎接',8,'庚寅，','数百人出迎。',[('查文徽','抵达福州，遇到假意迎接的队伍'),('吴程','主持威武军事务，派数百人假意出迎')],when='950年二月庚寅',place='福州',note='诈遣为诱敌，人数按书中概数，不写真实归附或吴越军已撤。')
add('chen_hui_warns_zha','陈诲劝查文徽先扎营，再逐步谋取福州',8,'诲曰：','宜立寨徐图。”',[('陈诲','提醒来人消息不可信，建议先扎营再行动'),('查文徽','收到陈诲的谨慎进军建议')],when='950年二月庚寅，查文徽进城之前',place='福州城外',note='闽人多诈是陈诲对当前局势的判断，不作为对地区人群的普遍评价。')
sup('chen_hui_warns_zha',8,fuzhou,'誨曰：「閩人多詐難信，宜駐江岸徐圖之。」','《新五代史》也记陈诲主张驻守江岸、逐步行动。','同一意见的不同表述，未将建议写成查文徽已经采纳。')
add('zha_rejects_caution','查文徽担心迟疑生变，率兵直接前进',8,'文徽曰：','因引兵径进。',[('查文徽','认为应趁机占城，率兵直接前进')],when='950年二月庚寅',place='福州城外至进城方向',note='据其城是查文徽的目标，不等于已成功占城。')
add('chen_hui_holds_riverbank','陈诲整顿军队，停在江边',8,'诲整众','止于江湄。',[('陈诲','整顿军队、鸣鼓，停在江边')],when='950年二月庚寅，查文徽前进时',place='福州江边',note='主书写自行停军，新史说文徽留诲屯江口，两种部署表述保留，不补陈诲已奉抗命处分。')
sup('chen_hui_holds_riverbank',8,fuzhou,'留誨屯江口，進至西門，伏兵發，文徽被擒。','《新五代史》记查文徽留下陈诲屯江口，自己进至西门后遭伏击。','主书写陈诲停在江边，是否由查文徽命令留下及驻地名称不同，分别保留。',relation='conflicts')
add('wu_cheng_defeats_zha','吴程率兵出击，击败未作防备的查文徽军',8,'文徽不','唐兵大败。',[('吴程','率兵出击，击败南唐军'),('查文徽','未作防备，所率军队被击败')],when='950年二月庚寅条下',place='福州',note='大败为史书所记战果，未造吴越兵力与双方伤亡比例。')
claim('event',E['wu_cheng_defeats_zha'],'description','《资治通鉴》记此次南唐军士卒死亡上万人。',8,'士卒死者万人。','万人为史书所记数量，没有独立统计校核，不当成现代核实的精确伤亡。')
add('zha_wenhui_captured','查文徽坠马，被福州人俘获',8,'文徽堕马，','为福人所执，',[('查文徽','坠马后被福州人俘获')],when='950年二月庚寅条下',place='福州',note='未列直接捕获者姓名，不将吴程率军出击直接写成亲手俘获。')
sup('zha_wenhui_captured',8,fuzhou,'進至西門，伏兵發，文徽被擒。','《新五代史》也记查文徽在福州西门方向遭伏击被俘。','地点为新史补充，主书另记坠马，不把一书未提某细节算成否定。',relation='adds')
add('chen_returns_jianzhou','陈诲率完整部队退回剑州',8,'诲全军','归剑州。',[('陈诲','率完整部队返回剑州')],when='950年二月福州战事后，具体返回日未载',place='剑州',note='全军为史书概述，未给撤回人数，不把查文徽军死亡数分摊为陈诲部队损失。')
add('wu_cheng_sends_zha_qiantang','吴程将俘虏查文徽送往钱唐',8,'程送文徽','于钱唐，',[('吴程','将查文徽送到钱唐'),('查文徽','被押送到钱唐')],when='950年二月福州战事后，具体日未载',place='福州至钱唐',note='钱唐保留底本地名，未补押送路线、使者和途中待遇。')
add('qian_releases_zha','钱弘俶将查文徽献于祖庙后释放',8,'吴越王弘亻叔',None,[('钱弘俶','将查文徽献于五庙后释放'),('查文徽','被钱弘俶释放')],when='950年福州战事及送至钱唐之后，具体释放日未载',place='钱唐、吴越五庙',note='献于五庙为向祖庙献俘，不写成处死；弘亻叔为既有钱弘俶拆字字形。')
sup('qian_releases_zha',8,fuzhou,'景送先進還越，越亦歸景文徽。','《新五代史》记李璟把马先进送回吴越，吴越也把查文徽送回南唐。','作为释放去向与双方归还俘虏的补充；主书未列马先进被送回，不强定双方交换日或把献庙省略成处死。',relation='adds')
claim('person',people['陈诲'],'description','《资治通鉴》和《新五代史》在950年相关记载中，仍写剑州刺史陈诲率军参加福州战事。',8,'文徽信之，遣剑州刺史陈诲将水军下闽江，','此前946年通鉴条有同名剑州刺史被杀记载，已留冲突；本段按所见主体继续关联，身份与底本文字仍须校核，不确定死亡年。')
add('liu_shenjiao_death','汝州奏报防御使刘审交去世',9,'丁亥，','刘审交卒。',[('刘审交','被汝州奏报已去世')],when='950年二月丁亥奏报，主书未单列实际去世日',place='汝州',note='汝州奏是报告日期，不直接等同死亡日；旧史本纪同日卒，列传另作乾祐二年春。')
sup('liu_shenjiao_death',9,feb,'丁亥，汝州防禦使劉審交卒。','《旧五代史》本纪也在乾祐三年二月丁亥记刘审交去世。','本纪同一日期；主书明确汝州奏报，不自动把其奏报日改成死亡日。')
sup('liu_shenjiao_death',9,liu,'乾祐二年春，卒，年七十四。','《旧五代史》刘审交传把其去世写在乾祐二年春，并记年七十四。','乾祐二年为949年，与本纪及通鉴950年二月条不同；并列保留，不据此反算出生年或确定唯一死亡年。',relation='conflicts',field='time_original')
add('ruz_people_request_burial','汝州吏民请求将刘审交留葬本州',9,'吏民诣阙','其丘垄，',[('刘审交','汝州吏民请求把他留葬本州')],when='950年二月刘审交去世奏报后，具体日未载',place='汝州、后汉朝廷',note='请求理由是吏民认为他有仁政、希望祭扫，不造所有居民皆参与或已获批准。')
add('han_allows_liu_burial','后汉准许汝州吏民留葬刘审交',9,'吏民诣阙','诏许之。',[('刘承祐','准许汝州吏民的留葬请求'),('刘审交','获准留葬汝州')],when='950年二月刘审交去世奏报后，具体日未载',place='后汉朝廷、汝州',note='诏许所指留葬请求，别于旧传另载追赠太尉；不把其异年追赠当本日主书官衔。')
sup('han_allows_liu_burial',9,liu,'郡人聚哭柩前所，列狀乞留葬本州界，立碑起祠，以時致祭。','《旧五代史》刘审交传也记当地居民请求留葬、立碑建祠。','内容印证，列传死亡年与本纪不同，不能作为950年日期独立确证。')
add('ruz_buries_honors_liu','汝州民众哭葬刘审交，并立祠祭祀',9,'州人相与','岁时享之。',[('刘审交','得到汝州民众哭葬、立祠祭祀')],year=None,when='刘审交去世并获准留葬后，始葬与后续祭祀起止未载',place='汝州',note='岁时享之是持续祭祀概述，不把往后所有年度都定在950年二月。')
person('冯道',9,'评论刘审交的公正廉洁与慈爱作风',span(9,'太师冯道曰：'))
claim('person',people['冯道'],'historical_commentary','冯道认为刘审交受百姓爱戴，主要在于公正、廉洁、慈爱地处理政务，值得各地长官效法。',9,span(9,'太师冯道曰：'),'这是冯道的评价，未另造本月公开演讲活动；不把并未减赋徭改写成免税或免役。')
claim('event',E['liu_shenjiao_death'],'historical_commentary','冯道曾担任刘审交的僚佐，认为他的可贵之处是以公正、廉洁、慈爱的态度施政。',9,span(9,'太师冯道曰：'),'此前共事为追述，未单独定年；二千石指地方长官，不作此时所有人官禄二千石的统计。')
add('du_jianhui_death','吴越丞相杜建徽去世',10,'甲午，',None,[('杜建徽','以吴越丞相、昭化节度使、同平章事身份去世')],when='950年二月甲午',place='吴越，具体去世地点未载',note='本句未给年龄、死因与葬地，不从姓名反推他人履历。')
claim('person',people['杜建徽'],'death_year','《资治通鉴》记杜建徽于950年二月甲午去世。',10,Q[10]['text'],'沿既有人物key，不覆盖旧档案；出处支持年和原纪日，不转换公历日期。')
add('zhao_kuangzan_left_general','后汉任命赵匡赞为左骁卫上将军',11,'乙未，',None,[('赵匡赞','以先前永兴节度使身份获任左骁卫上将军')],when='950年二月乙未',place='后汉朝廷',note='电子底本越匡赞疑为赵匡赞讹字；旧史同日同旧任同新职写赵赞，与已有948年永兴主体对照，不新建越姓人物，原文不改。')
sup('zhao_kuangzan_left_general',11,feb,'以前永興軍節度使趙贊為左驍衛上將軍。','《旧五代史》同日记前永兴节度使赵赞任左骁卫上将军。','赵赞为书中省名写法，与通鉴本句旧任、新职及既有赵匡赞一致；越匡赞字形留待底本校读，不录作正式改姓。')
actors=[('高行周','以邺都留守身份入朝'),('慕容彦超','以天平节度使身份入朝'),('符彦卿','以泰宁节度使身份入朝'),('常思','以昭义节度使身份入朝'),('杨信','以安远节度使身份入朝'),('薛怀让','以安国节度使身份入朝'),('武行德','以成德节度使身份入朝'),('郭瑾','以彰德节度使身份入朝'),('王饶','以保大留后身份入朝')]
add('governors_birthday_audience','高行周等藩镇将领为嘉庆节入朝',12,'三月，',None,actors,when='950年三月丙午，嘉庆节',place='后汉京师',note='主书九位名单逐项保存，与旧史八位名单分别对照，不把旧史未列者当成未到。杨信沿杨承信，郭瑾沿郭谨，依据旧任及书证核身份，原字保留。')
sup('governors_birthday_audience',12,mar,'是月，鄴都留守高行周、兗州符彥卿、鄆州慕容彥超、西京留守白文珂、鎮州武行德、安州楊信、潞州常思、府州折從阮皆自鎮來朝，嘉慶節故也。','《旧五代史》也记三月藩镇将领为嘉庆节来朝，名单另列白文珂、折从阮。','主书另有薛怀让、郭瑾、王饶，两书详略不同；旧史未单列来朝日，不套本段丙午补给所有新增姓名，也不提前录后文迁镇。',relation='adds')
claim('person',people['杨承信'],'description','950年入朝名单中的安远节度使杨信，与此前所载杨承信相对应，姓名写法不同。',12,'安远节度使杨信、','旧史947年记杨承信任安州节度使，949年同任杨信称父光远；任地、父子身份和连续记载相合。姓名省写或改名机制未明，不自造改名日期。')
claim('person',people['杨承信'],'description','《旧五代史》记杨承信曾由青州调任安州节度使。',12,'以青州節度使楊承信為安州節度使，加檢校太傅；','947年原任用于950年姓名核对，不重建947年已发布调任。',source=july)
claim('person',people['杨承信'],'description','《旧五代史》949年记安州节度使杨信奏报父亲杨光远神道碑断裂。',12,'戊寅，安州節度使楊信奏，亡父光遠，蒙賜神道碑，鐫勒畢，無故中斷。','仅核同一父亲及安州任职，碑断记载不另建950年事件，不据异象推政治因果。',source=yang)
claim('person',people['郭谨'],'description','《资治通鉴》950年所载彰德节度使郭瑾，与《旧五代史》所载相州郭谨相对应，姓名字形不同。',12,'彰德节度使郭瑾、','既有相州彰德节度任职与旧史郭谨连续可对照；瑾、谨不同字，按同一任地履历识别，不泛化为所有同音名都自动合并。')
claim('person',people['郭谨'],'description','《旧五代史》949年十月仍记相州郭谨获加检校太尉。',12,'丙子，相州郭謹、貝州王繼宏、邢州薛懷讓並加檢校太尉。','原相州彰德节度主体与950年名单对照，只作身份支持，不重建旧加官或新建郭瑾。',source=october)
reviews={8:'巡边返回与福州军务分开。邀请与迎接的欺骗内容不当事实；派军、建议、前进、江边驻军、战败被俘、撤回、押送钱唐、献庙释放逐步分录。俘马先后与江口留军命令两书不同；新史归还马先进、文徽补充保留，万人七百里不当现代统计。陈诲946同名被杀冲突仍待身份底本校核，不定死年。',9:'丁亥奏报与实际去世日区分；旧史本纪乾祐三年、列传二年春冲突并列，年龄不反算出生。请求、准许、哭葬、持续祭祀分开；冯道评价附事实引用，不造本月公开讲话，未免赋徭。',10:'杜建徽官职、死亡年日按原文，不补年龄死因或葬地，沿既有主体。',11:'越匡赞疑字按同日同职旧史赵赞和既有永兴赵匡赞核对，不造新姓主体或改写底本。',12:'九名来朝逐项保存，旧史不同名单只补书证，不提前把未列者套丙午。杨信与杨承信按安州和父光远核同人，郭瑾与郭谨按相州彰德履历核同人，原异字及未知改名机制保留；后文迁镇未提前录。'}
assert not (P/'publication.json').exists()
for n in range(8,13):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(8,13)],next_paragraph=Q[13]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原13—17行连续五段；发布后首12/83正文已录，后续71段待录。当前主书原文快照复用首批固定归档，不代表快照其余正文已录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(8,13)],source_issues_review='陈诲946死亡与950活动冲突继续保留；俘马先后、驻军命令、文徽释放细节两书不同。刘审交旧史本纪950与列传949死亡冲突不裁定。越匡赞、郭瑾及杨信按对应身份核对，底本原字、改名机制仍待核；两书来朝名单不强合单日。纸本及电子转录字误待核。',plain_language_review='首次逐条检查标题、人物介绍、角色、日期地点与核对解释。主语明确，区分谎报、假迎、建议、目标、战斗结果、押送与释放、奏报死亡及持续祭祀。冯道评价归事实引用，不造活动；未知时间保留null，旧主体档案不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
