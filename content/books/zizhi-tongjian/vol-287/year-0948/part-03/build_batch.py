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
COMMIT='f3618bc94c6d669e34d763bb33178fe9befba23a'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-948-january-february','songshi-254-hou-yi-shu']:
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
main_sources = ['tongjian-287-948-january-february','tongjian-287-948-volume-end']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0948-p017-p019',
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
for n in range(17, 20):
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
        citation = f'卷287·乾祐元年（948年二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0948_03_{len(B["claims"])+1:04d}'
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
NEW_ALIASES={'程渥':[]}
NEW_DESCRIPTIONS={'程渥':'侯益的从事，与王景崇同乡且有旧交。948年王景崇考虑杀侯益时，程渥前去劝阻。《新五代史》记王景崇因此有所动摇，《宋史》却记王景崇怒斥并威胁程渥，两个版本分别保留。生卒年未载。'}
new='xinwudaishi-053-cheng-wo-remonstrance';song='songshi-254-hou-yi-shu';t='948年二月，具体日未载'
add('wang_fengxiang_inspector','后汉任命王景崇兼凤翔巡检使',17,'诏以','凤翔巡检使。',[('王景崇','奉诏兼任凤翔巡检使')],when=t,place='凤翔',note='未另载任命干支，不套本段末侯益入朝的戊戌。')
add('wang_guards_fengxiang_gates','王景崇抵凤翔，分派禁军守城门',17,'景崇引兵至','分守诸门。',[('王景崇','抵达凤翔并分禁军守门'),('侯益','此时尚未离开凤翔')],when=t,place='凤翔',note='控制城门不等于已杀侯益，也不写成已经占城公开叛变。')
add('wang_hesitates_kill_hou','有人劝杀侯益，王景崇因新帝不知密旨而犹豫',17,'或劝景崇','犹豫未决。',[('王景崇','担忧新帝不知先帝密旨，杀人会被疑为擅杀'),('侯益','成为被提议杀害的对象')],when=t,place='凤翔',description='有人劝王景崇杀侯益。王景崇想到密旨由先帝刘知远单独授予，继位的刘承祐不知其事，担忧自己被认为擅杀，因此犹豫未决。',note='匿名劝说者不建人物。刘承祐不知密旨是王景崇犹豫的叙述背景，不表示刘承祐曾在凤翔参与讨论。')
sup('wang_hesitates_kill_hou',17,new,'景崇念獨受命先帝而少主莫知，猶豫未決。','《新五代史》也记王景崇独受先帝密令，担心少主不知而犹豫。','先帝为刘知远，少主为刘承祐，未扩写成新帝准许杀侯益。')
quote='益從事程渥，與景崇同鄉里，有舊，往說景崇曰：「吾與子為故人，吾位不過賓佐，而子已貴矣，奈何欲以陰狡害人而取之乎？侯公父子爪牙數百，子毋妄發，禍行及矣！非吾，誰為子言之。」於是景崇頗不欲殺益，'
E['cheng_wo_remonstrance']=event('cheng_wo_remonstrance','程渥劝王景崇不要杀侯益，两书记其结果不同',17,quote,[('程渥','以同乡旧交身份劝阻王景崇'),('王景崇','接受劝说时的反应，两书记载不同'),('侯益','其从事出面劝阻对自己的杀人计划')],when=t,place='凤翔',source=new,description='侯益从事程渥与王景崇同乡且有旧交，前去劝王景崇不要杀侯益。《新五代史》记王景崇有所动摇，《宋史》却记他怒斥并威胁程渥，暂保留两种记载。',note='亲戚党羽数百是程渥劝说中的估量，不作为独立兵数统计；有旧不另造结义或终身盟友关系。')
sup('cheng_wo_remonstrance',17,song,'景崇怒曰：「子去，勿為遊說，吾將族爾！」益知不用渥言，即率數十騎奔入朝。','《宋史》记王景崇怒斥程渥，威胁杀其一家；侯益得知劝说不被接受，率数十骑奔入朝。','与《新五代史》王景崇有所动摇不同，冲突分别保留；族尔是威胁，未记已经诛族。',relation='conflicts')
add('hou_leaves_without_notice','侯益得知杀人议论，未告王景崇便离开',17,'益闻之，','不告景崇而去，',[('侯益','得知杀人议论，不通知王景崇就离开'),('王景崇','未获侯益离开的事先通知')],when='948年二月戊戌入朝之前，离开具体日未载',place='凤翔至后汉朝廷',note='离开与入朝不是同一日；不写王景崇亲自放行。')
sup('hou_leaves_without_notice',17,new,'益乃亡去，景崇大悔失不殺之。','《新五代史》也记侯益离去、王景崇后悔未杀。','只印证离去与后悔，离开具体日未载。')
add('wang_regrets_hou_departure','王景崇后悔未杀侯益，责骂自己',17,'景崇悔，','自诟。',[('王景崇','因侯益离去而后悔、自责')],when='948年二月侯益离去之后，具体日未载',place='凤翔',note='自诟为责骂自己，不误读成王景崇当场辱骂侯益本人。')
add('hou_defends_shu_invitation','侯益入朝，声称召蜀军是为诱来杀掉，刘承祐笑之',17,'戊戌，',None,[('侯益','入朝，对召蜀军问题作诱杀辩解'),('刘承祐','询问召蜀军原因，对回答发笑')],when='948年二月戊戌',place='后汉朝廷',description='侯益入朝，刘承祐问他为何召蜀军。侯益回答说是想诱来杀掉，刘承祐听后发笑。',note='诱杀是侯益本人解释，不据此将此前求蜀援兵改写成已查实的诱敌计。哂之不推为赦免、认可或下令杀蜀兵。')
sup('hou_defends_shu_invitation',17,song,'隱帝遣侍臣問益結連蜀軍之由，益對曰：「臣欲誘之出關，掩殺之耳。」隱帝笑之。','《宋史》也记侯益以诱出关掩杀作回答，但记询问由隐帝派侍臣传达。','主书写隐帝问，宋史补传问方式；两书都只记侯益的回答，不证明有真实诱杀计划。',relation='adds')
add('zhang_regrets_no_achievement','张虔钊因出兵无功而懊恼',18,'蜀张虔钊','自恨无功。',[('张虔钊','因没有战功而懊恼')],when='948年二月癸卯之前，具体日未载',place='蜀军撤回途中',note='这是史家记述的心理，不作现代医学诊断。')
add('zhang_qianzhao_death_xingzhou','张虔钊到兴州，惭愤去世',18,'癸卯，',None,[('张虔钊','抵达兴州后去世')],when='948年二月癸卯',place='兴州',note='癸卯承本年二月，不套后卷三月；惭忿而卒为史书所述，未载详细病名、年龄或医学死因。')
add('shi_hongzhao_mother_death','史弘肇的母亲去世',19,'侍卫马步','遭母丧，',[('史弘肇','任侍卫马步都指挥使、同平章事时遭母丧')],when='948年二月末相关叙述，具体日未载',place='后汉',note='母亲未具姓名，不新造姓名或生卒年。遭母丧不意味着史弘肇本人死亡。')
add('shi_hongzhao_resumes_court','史弘肇遭母丧后不到几天，重新参加朝会',19,'侍卫马步',None,[('史弘肇','母亲去世后不到几天便重新参加朝会')],when='948年母丧后数日内，具体日未载',place='后汉朝廷',note='恢复参加朝会和后卷三月丙辰正式起复任官分别记录；不自行推算母亲死亡日。')
reviews={17:'兼巡检任命、禁军守门、杀议犹豫、程渥劝阻、侯离、王悔自骂、戊戌入朝辩解分录。程渥反应两书不同，冲突保留；诱杀为侯本人辩解，未证事实。少主刘承祐未在凤翔，匿名劝说者不造人物。',18:'先无功懊恼，癸卯到兴州死，不套后卷三月。史载心理不转现代死因；主体复用张虔钊。',19:'母亲死亡与史弘肇复朝分录，未具名母亲不虚造，未误为史弘肇死；后卷正式起复另录，数日不反算具体日。'}
assert not (P/'publication.json').exists()
for n in range(17,20):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,20)],next_paragraph='zztj-v288-y0948-p001',next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷287原99—101行连续三段。本卷948年19/19正文完成，全年跨卷287、288共88段，仅19/88，不将卷末当全年完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,20)],source_issues_review='程渥劝说结果两书不同，宋史补侍臣传问；侯辩解非事实认证。张死亡只据主书具体癸卯，心理不作医学病因。',plain_language_review='首次逐条核对全部人物介绍、事件、时间、角色与事实说明，主语明确；提议、威胁、辩解与实际行动分清。摘录原字不改，未知月日不外推，不固定再做文案二次复核。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
