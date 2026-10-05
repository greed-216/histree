# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 42–47."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='e13dd68e0caa3222d6fb3adad85c0ad8d6bd39d8'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-li-wuyue','jiuwudaishi-099-imperial-title','xinwudaishi-010-accession']:
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
main_sources = ['tongjian-286-947-li-wuyue']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p042-p047',
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
for n in range(42, 48):
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
        citation = f'卷286·天福十二年（947年二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_09_{len(B["claims"])+1:04d}'
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
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','契丹主':'耶律德光','耶律郎五':'郎五','王晖':'王晖（947年代州刺史）','赵晖':'赵晖（后汉将领）','晖':'赵晖（后汉将领）','高模翰':'高谟翰','王琼':'王琼（947年澶州首领）','超':'王超（王琼弟）','药可俦':'药可俦','李万超':'李万超','张乙':'张乙（夏津首领）'})
NEW_ALIASES={'王晖（947年代州刺史）':['王暉（947年代州刺史）'],'骆从朗':['駱從朗'],'张晏洪':['張晏洪'],'药可俦':['藥可儔'],'赵熙':['趙熙'],'赵矩':['趙矩'],'李万超':['李萬超'],'王琼（947年澶州首领）':['王瓊（947年澶州首領）'],'王超（王琼弟）':['王超（王瓊弟）'],'张乙（夏津首领）':['張乙（夏津首領）']}
NEW_DEATH_YEARS={'王晖（947年代州刺史）':947,'骆从朗':947,'赵熙':947,'王琼（947年澶州首领）':947}
NEW_DESCRIPTIONS={
'王晖（947年代州刺史）':'947年代州刺史，归附契丹后，被史弘肇攻破城池并杀死。不与此前前陵州刺史等同名人物自动合并，生年未载。',
'骆从朗':'晋州节度副使。947年刘在明去朝契丹时，负责州务，囚禁刘知远派来的张晏洪等使者，随后被药可俦杀死。生年未载。',
'张晏洪':'947年受刘知远命令出使晋州，宣告即位，被骆从朗囚禁。药可俦杀骆从朗后，推他暂任留后。生卒年未载。',
'药可俦':'晋州大将。947年杀死骆从朗，推张晏洪暂任留后；具体日未载，庚辰是派使报告的日期。生卒年未载。',
'赵熙':'右谏议大夫。947年受契丹派遣到晋州征钱帛，催征急迫，骆从朗死后被州民杀死。具体日与生年未载。',
'赵矩':'河间人，陕州支使。947年受赵晖派遣，到晋阳向刘知远上表，并劝刘知远早日率兵南下。生卒年未载。',
'李万超':'晋军出身的指挥使。947年驻潞州时，率众入府杀死契丹委任的赵行迁，推王守恩为主帅。《宋史》李万超传补证这一行动。生卒年暂未录入。',

'王琼（947年澶州首领）':'947年澶州武装首领，率一千余人攻取南城，围困契丹节度使，后向刘知远求救。最终兵败被杀，具体死亡日各书记述范围不同。与其他同名官员暂不合并，生年未载。',
'王超（王琼弟）':'947年澶州首领王琼的弟弟，被派往刘知远处求救。二月癸未得到赏赐后被遣回。与晚唐邠岐判官王超区分，生卒年未载。',
'张乙（夏津首领）':'夏津武装首领。《旧五代史》记947年与澶州水运什长王琼联络，聚集千余人反抗契丹。生卒年未载。'}
j='jiuwudaishi-099-imperial-title';nw='xinwudaishi-010-accession';zh='jiuwudaishi-125-zhao-hui';ss='songshi-261-li-wanchao'
add('shi_captures_daizhou','史弘肇攻取代州，杀死刺史王晖',42,'武节',None,[('史弘肇','以武节都指挥使身份攻取代州'),('王晖','代州被攻破后被杀')],when='947年二月，主书未标具体日',place='代州',note='代州王晖按时代职务单独识别，不与前陵州等同名人物自动合并。《旧五代史》给出己卯，分别引用。')
sup('shi_captures_daizhou',42,j,'己卯，帝遣都將史宏肇率兵討代州，平之。初，代州刺史王暉叛歸契丹，宏肇一鼓而拔之，斬暉以徇。','《旧五代史》在二月己卯记史宏肇取代州，并补王晖此前归附契丹。','史宏肇与史弘肇沿既有同一主体；己卯来自补书，主书此句未标日。',relation='adds',field='time_original')
sup('shi_captures_daizhou',42,nw,'武節都指揮使史弘肇取代州，殺其刺史王暉。','《新五代史》也记史弘肇取代州、杀刺史王晖。','对应同一事件，原文没有给出独立具体日。')
add('liu_zaiming_leaves_luo_in_charge','刘在明前往契丹朝见，留骆从朗管理晋州',43,'建雄留后','知州事。',[('刘在明','以建雄留后身份朝见契丹'),('骆从朗','以节度副使身份管理州务')],when='947年二月，具体日未载',place='晋州至契丹朝廷',note='知州事是暂管州务，不等于已正式任命为节度使。')
add('jinzhou_imprisons_liu_envoys','刘知远派张晏洪等到晋州告知即位，骆从朗将使者囚禁',43,'帝遣使者','从朗皆囚之。',[('帝','派使者宣告自己即位'),('张晏洪','奉命出使晋州后被囚'),('骆从朗','囚禁张晏洪等使者')],when='947年二月庚辰之前，具体日未载',place='晋阳至晋州',note='使者还有他人，但主书未逐名列出，不补出未见姓名。')
add('yao_kills_luo_elevates_zhang','药可俦杀死骆从朗，推张晏洪暂任晋州留后',43,'大将药','推晏洪权留后，',[('药可俦','杀死骆从朗并推张晏洪'),('骆从朗','被药可俦杀死'),('张晏洪','获推暂任晋州留后')],when='947年二月庚辰奏报前，具体日未载',place='晋州',note='庚辰是后文派使报告日，不能直接当作杀人日；权留后为暂任。')
sup('yao_kills_luo_elevates_zhang',43,j,'大將藥可儔殺從朗於理所','《旧五代史》补记药可俦在骆从朗办公处杀他。','补充行凶地点，仍不把庚辰奏报日当作行动日。',relation='adds')
add('jinzhou_reports_change','晋州于庚辰派使者向刘知远报告州内变动',43,'庚辰，',None,[],when='947年二月庚辰',place='晋州至刘知远朝廷',note='本句未点名报告使者，不把此前张晏洪自动写作亲自出使人；庚辰只用于奏报。')
add('zhao_xi_collects_levies','耶律德光派赵熙到晋州征收钱帛，赵熙催征急迫',44,'契丹主遣','征督甚急。',[('契丹主','派赵熙征钱帛'),('赵熙','以右谏议大夫身份到晋州催征')],when='947年二月，骆从朗死前后具体日期未载',place='晋州',note='原文未给征收总额，不推每户征收或已完成金额。')
add('jinzhou_people_kill_zhao_xi','骆从朗死后，晋州百姓聚众杀死赵熙',44,'从朗既死，','共杀熙。',[('赵熙','被晋州百姓杀死')],when='947年二月骆从朗死后，具体日未载',place='晋州',note='州民没有姓名，不能写成药可俦亲手杀赵熙；《新五代史》简略连叙，两书行动主语的范围分别保留。')
sup('jinzhou_people_kill_zhao_xi',44,j,'州民相率害趙熙','《旧五代史》同记州民聚众杀赵熙。','补书明确州民为行动方，未列姓名。')
add('khitan_decree_zhao_hui_liuhou','耶律德光颁诏授赵晖为保义留后',44,'契丹主赐','以为保义留后。',[('契丹主','下诏授赵晖保义留后'),('赵晖','收到契丹任命诏书')],when='947年二月辛巳之前，具体日未载',place='契丹朝廷至陕州',note='收到任命不等于接受；此前补书记三人拒契丹授职，此处主书补出具体斩使、焚诏行动，不另建重复拒任概述。')
add('zhao_hui_kills_envoy_burns_decree','赵晖杀死契丹使者，烧毁契丹任命诏书',44,'晖斩契丹','焚其诏，',[('赵晖','杀契丹使者并烧毁任命诏书')],when='947年二月辛巳之前，具体日未载',place='陕州',note='使者未名，不建立猜测主体；该具体行为补充此前已经记录的拒受契丹任命。')
add('zhao_ju_submits_to_liu','赵晖派河间支使赵矩到晋阳，向刘知远上表',44,'遣支使河间','奉表诣晋阳。',[('赵晖','派赵矩向刘知远上表'),('赵矩','以支使身份赴晋阳上表')],when='947年二月辛巳之前，具体日未载',place='陕州至晋阳',note='赵矩的河间籍贯与支使身份按此句确认；上表未给全文，不补具体承诺。')
add('gao_mohan_fails_at_shaan','契丹派高谟翰进攻赵晖，未能攻下陕州',44,'契丹遣其将','不克。',[('高模翰','受派进攻赵晖，未能取城'),('赵晖','所据陕州未被攻下')],when='947年二月，具体日未载',place='陕州',note='高模翰为已有高谟翰的别名，沿原主体。原文未记战损及兵数；不克不等于将领被俘或阵亡。')
add('liu_receives_zhao_ju','刘知远接见赵矩，称陕州归附有助于平定天下',44,'帝见矩，','天下不足定也！”',[('帝','接见赵矩并评价陕州归附'),('赵矩','得到刘知远接见')],when='947年二月，具体日未载',place='晋阳',note='咽喉之地及足以定天下是刘知远的评价，不写成天下已经平定。')
add('zhao_ju_urges_southward_campaign','赵矩劝刘知远尽早率兵南下，刘知远赞同',44,'矩因劝',None,[('赵矩','建议早日率兵南下'),('帝','赞同南下建议')],when='947年二月，接见赵矩时',place='晋阳',note='赞同不等于当日已经率兵出发；南向是方向，不能补出明确路线。')
add('liu_appoints_zhao_hui_baoyi','刘知远任赵晖为保义节度使',45,'辛巳，','保义节度使，',[('帝','任赵晖为保义节度使'),('赵晖','获任保义节度使')],when='947年二月辛巳',place='陕州保义军',note='本次授职来自刘知远，与契丹保义留后诏书不同，不能合并为接受契丹任命。')
sup('liu_appoints_zhao_hui_baoyi',45,zh,'漢祖乃命暉為保義軍節度、陜虢等州觀察處置等使。','《旧五代史》赵晖传也记汉祖任他为保义节度，并补陕虢等州观察处置职务。','采用传记正文任职记载；同段括注中转引《通鉴》的斩使焚诏不算独立确证。',relation='adds')
add('liu_appoints_hou_zhang','刘知远任侯章为镇国节度使、保义军马步都指挥使',45,'侯章为','保义军马步都指挥使，',[('帝','任侯章两项职务'),('侯章','获任镇国节度使并掌保义军马步军')],when='947年二月辛巳',place='镇国军、保义军（任职范围）',note='镇国节度与保义军军职分别保留，不写成一个军镇的同一职位。')
add('liu_appoints_wang_yan','刘知远任王晏为绛州防御使、保义军马步副指挥使',45,'王晏为',None,[('帝','任王晏两项职务'),('王晏','获任绛州防御使及保义军马步副指挥使')],when='947年二月辛巳',place='绛州、保义军（任职范围）')
add('gao_wang_plan_zhaoyi_revolt','高防与王守恩谋划，派李万超入府反抗赵行迁',46,'高防与','遣指挥使李万超',[('高防','与王守恩谋划行动'),('王守恩','与高防共同谋划'),('李万超','被派率众入府')],when='947年二月，具体日未载',place='昭义潞州',note='本事件记计划与派遣；实际入府及斩赵另行记录。')
add('li_wanchao_kills_zhao_xingqian','李万超白昼率众大喊入府，杀死赵行迁',46,'遣指挥使','斩赵行迁，',[('李万超','以指挥使身份率众入府杀赵行迁'),('赵行迁','被李万超率众杀死')],when='947年二月白昼，具体日未载',place='潞州府署',note='白昼是行动时段，未载干支日；赵行迁沿前批契丹所置留后主体。')
sup('li_wanchao_kills_zhao_xingqian',46,ss,'遂率所部大噪入府署，殺其使，推守恩為帥，列狀以聞。','《宋史》李万超传也记率所部入府，杀契丹使者，推王守恩并上报。','宋史本句未点名被杀者，姓名由《通鉴》支持；不能把传记后段史弘肇欲杀守恩的谈话提前为本日事件。')
add('wang_shouen_chosen_zhaoyi_liuhou','潞州反抗军推王守恩暂管昭义留后事务',46,'推守恩','权知昭义留后。',[('王守恩','获推暂管昭义留后事务')],when='947年二月赵行迁被杀后，具体日未载',place='昭义潞州',note='权知为暂时管理，不等于已经收到正式节度使任命；推举者不在本句逐名列出。')
add('wang_shouen_submits_zhaoyi','王守恩杀契丹使者，率昭义归附刘知远',46,'守恩杀',None,[('王守恩','杀契丹使者并举镇归附刘知远')],when='947年二月，具体日未载',place='昭义至刘知远朝廷',note='本句所说契丹使者是否指已被杀的赵行迁或另一使者未能确定，不另设姓名、数量或另一次杀人日期。')
sup('wang_shouen_submits_zhaoyi',46,j,'辛巳，權陜州留後趙暉、權潞州留後王守恩，並上表歸順。','《旧五代史》二月辛巳记王守恩与赵晖上表归顺。','辛巳适用于上表归顺，不直接用作前述府署袭击的日期。',relation='adds',field='time_original')
add('langwu_governs_chan_violently','史书记澶州人苦于耶律郎五的残虐统治',47,'镇宁节度使','澶州人苦之。',[('耶律郎五','任镇宁节度使，统治被史书评为残虐')],when='947年二月澶州反抗前，具体日未载',place='澶州镇宁军',note='残虐是史家评价，不能据此补出未载的具体杀戮名单。旧史同一事件姓名异文另在补引中保留。')
add('wang_qiong_attacks_chan','王琼率千余人夜取澶州南城，渡浮桥大掠，围耶律郎五于牙城',47,'贼帅王琼','牙城。',[('王琼','率千余人夜袭并围困牙城'),('耶律郎五','被围于牙城')],when='947年二月癸未以前，具体起事日未载',place='澶州南城、浮桥、牙城',note='原文同时记大掠，不能只写为取城而略去掠夺；千余人是概数。')
sup('wang_qiong_attacks_chan',47,j,'瓊為水運什長，乃構夏津賊帥張乙，得千餘人，沿河而上，中夜竊發，自南城殺守將，絕浮航，入北城，朗悟據牙城以拒之。','《旧五代史》补王琼为水运什长、联络夏津张乙，并记杀南城守将、断浮桥后入北城。','主书写北渡浮桥，旧史写断浮桥，行动次序与细节分别保留；旧史姓名在同段作朗鄂、朗悟，未覆盖主书耶律郎五。',relation='adds')
# Supplemental identity and alliance activity are tied to the same primary paragraph.
E['wang_qiong_recruits_zhang_yi']=event('wang_qiong_recruits_zhang_yi','王琼联络夏津首领张乙，聚集千余人反抗契丹',47,'瓊為水運什長，乃構夏津賊帥張乙，得千餘人',[('王琼','以水运什长身份联络张乙'),('张乙','作为夏津武装首领被联络')],when='947年澶州反抗之前，具体日未载',place='澶州、夏津',source=j,note='活动由《旧五代史》补充，不据此建立终身盟友关系；得千余人未给双方各自人数。')
add('khitan_returns_li_du_to_commands','耶律德光听说澶州反抗后担忧，遣李守贞、杜重威返回军镇',47,'契丹主闻之，','无久留河南之意。',[('契丹主','因澶州变动担忧，遣两节度使归镇'),('李守贞','被遣返回天平军'),('杜重威','被遣返回天雄军')],when='947年二月澶州反抗后，具体日未载',place='契丹朝廷至天平军、天雄军',note='无久留河南之意是史家所述意向，不表示已经北归或撤完军队。')
add('khitan_relief_wang_qiong_retires','契丹派兵救澶州，王琼退屯近郊，派弟弟王超向刘知远求救',47,'遣兵救澶州，','奉表来求救。',[('王琼','退屯近郊并遣弟求救'),('超','奉表向刘知远求救')],when='947年二月癸未之前，具体日未载',place='澶州近郊至晋阳',note='契丹救兵未载将领姓名，不指定耶律德光亲自率领；弟超按王姓与亲属限定，不能误用晚唐判官王超。')
relationship('王琼（947年澶州首领）','王超（王琼弟）','兄长',47,span(47,'琼退屯','奉表来求救。'),'其弟超明确长幼，方向为王琼是王超的兄长；未补同母、年龄差等信息。')
add('liu_rewards_wang_chao_sends_back','刘知远厚赏王超，遣他返回',47,'癸未，','遣还。',[('帝','厚赏王超并遣回'),('超','获赏后被遣回')],when='947年二月癸未',place='晋阳至澶州方向',note='只记赐赏与遣还，未载刘知远派救兵，不将求救自动写成获得军事援助。')
add('wang_qiong_defeated_killed','王琼兵败，被契丹杀死',47,'琼兵败，',None,[('王琼','兵败后被杀')],when='947年二月癸未条下续述，具体死亡日未定',place='澶州一带',note='癸未明确用于赐王超，《通鉴》后句死亡未独立标日；旧史癸未条连记败亡，两书记事范围分别保留。')
sup('wang_qiong_defeated_killed',47,j,'癸未，澶州賊帥王瓊與其眾斷本州浮橋，瓊敗，死之。','《旧五代史》在癸未条记王琼断桥、兵败死亡。','保留补书癸未条的范围，不覆盖主书对王超受赏与王琼后续败亡的叙述次序。',relation='adds',field='time_original')
reviews={42:'代州王晖暂按职务限定，与前陵州及安州同名人分开；补书记己卯，主书无日。',43:'刘在明赴契丹、骆代管、使者被囚、药杀骆与张获推留后、庚辰报告分别记录；奏报不是杀人日。',44:'征钱帛与州民杀赵熙、契丹授职、赵晖斩使焚诏、上表归刘及南下建议分清；高模翰复用高谟翰。',45:'刘知远辛巳三项任命分记，区别此前契丹授职；旧赵传正文补职务，转引通鉴不当独立确证。',46:'高防王守恩谋、李万超入府杀赵、推留后与归附分记；后句杀使是否重复赵行迁未明，保留疑问，不虚加受害者。',47:'王琼按澶州首领限定，弟王超与晚唐判官分开；浮桥动作及郎五姓名各书有异文；赐赏不等派援兵，败亡日期不强定。'}
assert not (P/'publication.json').exists()
for n in range(42,48):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(42,48)],next_paragraph=Q[48]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原47—52行连续六段，累计47/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(42,48)],source_issues_review='代州王晖单列待核，澶州郎五姓名与浮桥、败亡纪日分别保留；潞州后句杀使是否同赵行迁未定，不补未明姓名。',plain_language_review='首次核对全部展示字段、参与角色与引用说明，明确任命方、奏报与行动日期、建议与出兵结果，原文保持底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
