# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 939 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,42))
specs=[(d.name,d,'d0ce37b98c182cdb5c5cd2ee909baa3b407a4785','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修、宋祁' if d.name.startswith('xintangshu') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-july-aftermath']:
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
main_sources = ['tongjian-282-939-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0939-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-078-january':'卷78·晋高祖纪·天福四年正月','jiuwudaishi-078-march':'卷78·晋高祖纪·天福四年三月','xinwudaishi-062-ancestry':'卷62·南唐世家','xintangshu-080-li-yi':'卷80·宗室·李祎附传','xintangshu-080-li-yi-sons':'卷80·宗室·李祎附传','jiuwudaishi-125-feng-hui':'卷125·冯晖传'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(1, 9):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-078-january':'卷78·晋高祖纪·天福四年正月','jiuwudaishi-078-march':'卷78·晋高祖纪·天福四年三月','xinwudaishi-062-ancestry':'卷62·南唐世家','xintangshu-080-li-yi':'卷80·宗室·李祎附传','xintangshu-080-li-yi-sons':'卷80·宗室·李祎附传','jiuwudaishi-125-feng-hui':'卷125·冯晖传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月条下' if n<=3 else '二月条下' if n<=6 else '三月条下'
        citation = f'卷282·后晋天福四年（939；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0939_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'张从恩':'太原人，曾任澶州防御使。939年正月任后晋枢密副使。生卒年未载。',
'拓跋彦超':'党项首领。939年冯晖接任朔方节度使后，拓跋彦超前往祝贺，受到优待并被留在城中。生卒年未载。',
'宋氏（南唐李昪后）':'李昪的皇后。937年被立为皇后，939年与李昪为李氏父母服丧。个人名字及生卒年本次未核。',
'广德长公主（李建勋妻）':'李建勋的妻子，封广德长公主。939年李昪为李氏父母服丧时，她借来丧服入内哭祭。个人名字及生卒年未载。',
'李恪（唐吴王）':'唐朝吴王。939年李昪选择追认他为祖先，并追尊为定宗孝静皇帝。《资治通鉴》说明相连世系部分出自官员编撰，不能据此确认李昪的远祖血缘。',
'李祎（唐信安郡王）':'唐代宗室。《新唐书》记他在开元年间改封信安郡王。939年南唐讨论祖系时提到吴王的孙子李祎及其子李岘。',
'李岘（唐代宰相）':'唐代宰相，李祎的儿子。939年南唐官员讨论李昪祖系时提到他；李昪与他的后续世系被《资治通鉴》指出多由官员编撰。生卒年本次未核。',
'李荣（李昪父）':'李昪的父亲。939年李昪恢复李姓并讨论宗庙祖系时，史书提到李荣。生卒年本次未核。',
'郑元弼':'闽国礼部员外郎。939年奉王继恭的表章，随卢损前往后晋进贡。生卒年未载。',
'林省邹':'闽国士人。939年私下向卢损批评王继鹏的行为，表示计划扮作僧人向北逃走。是否实际逃走本段未载。'}
NEW_ALIASES={'张从恩':['張從恩'],'拓跋彦超':['拓跋彥超'],'宋氏（南唐李昪后）':['宋氏（李昪后）'],'广德长公主（李建勋妻）':['广德长公主','廣德長公主'],'李恪（唐吴王）':['李恪','吴王恪'],'李祎（唐信安郡王）':['李祎（吴王孙）','李祎（唐代宗室）'],'李岘（唐代宰相）':['李岘','李峴'],'李荣（李昪父）':['李荣','李榮'],'郑元弼':['鄭元弼'],'林省邹':['林省鄒']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name in ['李恪（唐吴王）','李祎（唐信安郡王）','李岘（唐代宰相）'] else '五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=939, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='939年'+('正月' if n<=3 else '二月' if n<=6 else '三月')+'条下，具体日期未载'
    key = 'event_zztj_282_0939_' + code
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
        edge = 'participation_zztj_282_0939_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'与{a}存在原文明示的亲属关系',quote,source=source)
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
        row=dict(key=f'relationship_zztj_282_0939_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})




ALIASES.update({'唐主':'李昪','皇后':'宋氏（南唐李昪后）','知证':'徐知证','知谔':'徐知谔','义祖':'徐温','广德长公主':'广德长公主（李建勋妻）','吴王恪':'李恪（唐吴王）','祎':'李祎（唐信安郡王）','岘':'李岘（唐代宰相）','荣':'李荣（李昪父）','齐王璟':'李璟','闽主':'王继鹏','卢损':'卢损（后晋册礼使）'})
jan='jiuwudaishi-078-january';mar='jiuwudaishi-078-march';nt='xinwudaishi-062-ancestry';ty='xintangshu-080-li-yi';tys='xintangshu-080-li-yi-sons';old='tongjian-281-937-july-aftermath'
add('zhang_congen_privy','石敬瑭任张从恩为枢密副使',1,'春，正月，',None,[('帝','任张从恩为枢密副使'),('张从恩','从澶州防御使任枢密副使')],when='939年正月辛亥')
sup('zhang_congen_privy',1,jan,'以澶州防禦使張從恩為樞密副使。','《旧五代史》也记张从恩由澶州防御使任枢密副使。','该句接己酉条，未单列辛亥；主书明确辛亥，日期依各书分别保留。',field='time_original',relation='adds')
add('zhang_xichong_dies','朔方节度使张希崇去世',2,'朔方节度使','张希崇卒，',[('张希崇','以朔方节度使身份去世')],place='朔方')
sup('zhang_xichong_dies',2,jan,'己酉，朔方軍節度使張希崇卒，贈太師。','《旧五代史》补记张希崇正月己酉去世，追赠太师。','主书未单列死亡日；追赠职衔不改为生前任太师。',field='time_original')
claim('person',people['张希崇'],'death_year','《资治通鉴》在939年正月条记张希崇去世。',2,'朔方节度使张希崇卒，','沿既有人物提供死亡出处，不改写此前已发布人物档案。')
add('shuofang_raids_after_zhang','张希崇去世后，朔方遭羌胡劫掠',2,'羌胡寇钞，','无复畏惮。',[],place='朔方',description='张希崇去世后，史书所称羌胡在朔方劫掠，不再有所顾忌。',note='羌胡沿用史料用语，未将所有族群都视为参与者，不造匿名首领或伤亡数字。')
add('feng_hui_shuofang','石敬瑭任冯晖为朔方节度使',2,'甲寅，','朔方节度使。',[('帝','任冯晖为朔方节度使'),('冯晖','从义成节度使任朔方节度使')],when='939年正月甲寅',place='朔方')
sup('feng_hui_shuofang',2,jan,'以義成軍節度使馮暉為朔方軍節度使。','《旧五代史》也记正月甲寅冯晖由义成军调任朔方军节度使。','此句承甲寅条，不把同时调任义成的景延广当作冯晖别名。')
add('tuoba_visits_feng','拓跋彦超前往祝贺冯晖，冯晖优待并将他留在城中',2,'党项酋长','留之不遣，',[('冯晖','厚待拓跋彦超，为他修建宅第、提供服饰器物并留在城中'),('拓跋彦超','前往祝贺冯晖，受到优待后被留在城中')],place='朔方',description='史书称拓跋彦超是势力最强的党项首领。冯晖到任后，拓跋彦超前往祝贺。冯晖优待他，在城中修建住宅、供给服饰器物，并留下他，不让他离去。',note='厚遇与留之不遣并存，不简化为普通自愿来访；未据此编造扣押家属或赎金。')
add('shuofang_restores_order','史书记述冯晖留下拓跋彦超后，辖境恢复安定',2,'封内遂安。',None,[('冯晖','治理朔方，被史书记述辖境恢复安定')],place='朔方',note='这是书中对治理效果的概述，不推边境所有争端永久结束。')
add('li_surname_petitions','徐知证等多次请求李昪恢复李姓、建立唐朝宗庙',3,'唐群臣','立唐宗庙，',[('知证','与群臣多次请求李昪恢复李姓、建立唐朝宗庙'),('唐主','收到恢复李姓和建立宗庙的请求')],note='请求与乙丑批准分别记录，不把请求次数改为一次。')
add('li_surname_approved','李昪批准恢复李姓和建立唐朝宗庙',3,'乙丑，','唐主许之。',[('唐主','批准恢复李姓及建立唐朝宗庙的请求')],when='939年正月乙丑',note='原书本月尚称唐主，统一人物沿李昪；二月改名昪另作事件，不将恢复姓氏与改名压成同日。')
sup('li_surname_approved',3,nt,source_span(nt,'徐氏諸子請昪復姓','改名曰昪。'),'《新五代史》也记徐氏诸子和百官请求恢复李姓，李昪随后恢复姓氏并改名。','该书合记复姓改名，主书分列正月复姓和二月改名；不把合记当作同一天的证明。')
add('li_refuses_honorific','李昪拒绝群臣请求添加尊号',3,'群臣又请','遂不受。',[('唐主','认为尊号虚美、不合古制，拒绝群臣的请求')],description='群臣请求为李昪添加尊号。李昪认为尊号只是虚美之辞，也不符合古制，因此拒绝接受。',note='尊号与皇帝身份、庙号、谥号不同，不误写为李昪拒绝称帝。')
add('nantang_later_practices','史书记述南唐后代沿用不受尊号等做法',3,'其后子孙',None,[],year=None,when='李昪之后子孙的追述，具体年月未载',description='《资治通鉴》记李昪后来的子孙继续不接受尊号，也不让外戚辅政、宦官参与政事，并评价这些做法优于其他国家。',note='其后为跨年追述，日期留空；比较评价归史书，不作网站对所有时期制度的无条件结论。')
add('xu_wen_yizu','李昪将徐温的庙号由太祖改为义祖',4,'二月，','曰义祖。',[('唐主','将徐温的庙号改为义祖'),('义祖','死后的庙号由太祖改为义祖')],when='939年二月乙亥',note='前文南唐以徐温为太祖，本条改庙号沿同一徐温主体；不与后晋太祖或唐高祖混淆。')
add('li_parents_mourning','李昪和皇后为李氏父母服丧，朝夕哭祭五十四天',4,'己卯，','朝夕临凡五十四日。',[('唐主','为李氏父母发哀，与皇后服丧、居丧庐并朝夕哭祭'),('皇后','与李昪一同服丧和哭祭')],when='939年二月己卯开始，朝夕哭祭五十四天',description='李昪为李氏父母发哀，与皇后穿斩衰丧服、居丧庐，按刚去世时的礼仪服丧，早晚哭祭，共五十四天。',note='如初丧礼是补行丧礼，不是父母同时于己卯去世；不自行计算公历结束日。')
claim('person',people['宋氏（南唐李昪后）'],'description','李昪的皇后为宋氏，937年被立为皇后。',4,'乙巳，立王后宋氏为皇后。','回查937年既有原文确认皇后姓氏，不据其他未经核实材料补个人名字。',source=old)
add('xu_brothers_mourning_refused','李昪拒绝徐知证和徐知谔一同服斩衰的请求',4,'江王知证','不许。',[('知证','请求为李氏父母服斩衰，未获准'),('知谔','请求为李氏父母服斩衰，未获准'),('唐主','拒绝二人的服丧请求')],note='徐知证、徐知谔为既有徐氏宗室主体；不写成已经服斩衰或因拒绝而遭惩罚。')
add('guangde_mourns','广德长公主借来丧服，入内哭祭李氏父母',4,'李建勋之妻',None,[('广德长公主','借来丧服入内哭祭，哀痛如丧父母')],description='李建勋的妻子广德长公主借来丧服，入内尽情哭祭，表现得如同自己的父母去世。',note='假衰绖是借丧服，不是装作悲伤；如父母之丧不能推她是李昪亲生姐妹。')
relationship('李建勋','广德长公主','丈夫',4,'李建勋之妻广德长公主','原文明示李建勋是广德长公主的丈夫；未据公主称号推未载父亲。')
add('li_jing_administers','李昪命李璟处理国事，军事仍须报告',5,'辛巳，','惟军旅以闻。',[('唐主','将国事交李璟处理，军事仍须报告'),('齐王璟','受命处理国事，军事须报告李昪')],when='939年二月辛巳',note='详决国事不是正式让位，军旅仍需上报，不改李璟当时为皇帝。')
add('li_bian_new_name','李昪改用昪作为名字',5,'庚寅，','唐主更名昪。',[('唐主','改名为昪')],when='939年二月庚寅',note='前名徐诰、徐知诰沿同一人物，不因改姓改名新增主体。')
sup('li_bian_new_name',5,nt,'然後復姓李氏，改名曰昪。','《新五代史》也记恢复李姓后改名昪。','本句未列具体日期，只印证改名行动，不与主书二月庚寅强行比对日。')
add('li_joint_ritual_debate','李昪命百官讨论李氏与徐氏两套宗庙合祭礼仪',5,'诏百官','合享礼。',[('唐主','命百官讨论两套宗庙合祭礼仪')],note='二祚指李氏唐朝帝统及徐温功业所形成的宗庙安排，不是两位皇帝共同执政。')
add('song_qiqiu_yizu_seat','宋齐丘等提议将徐温安排在七室东侧',5,'辛卯，','七室之东。',[('宋齐丘','与群臣提议将义祖徐温安排在七室东侧'),('义祖','在宗庙安排中被建议放在七室东侧')],when='939年二月辛卯',note='是礼制提议，后面李昪的安排另录，不把提议当最终已经执行。')
add('li_temples_order','李昪命唐高祖、唐太宗和徐温按次序设置不祧之主',5,'唐主命居','皆为不祧之主。',[('唐主','命唐高祖居西室，唐太宗和义祖徐温依次排列，均长期保留祭祀'),('义祖','被安排与唐高祖、唐太宗依次祭祀')],description='李昪命唐高祖居西室，唐太宗次之，义祖徐温再次之，三者都作为不随世代迁除的祭祀对象。',note='不祧之主按宗庙永久保留解释；唐高祖、唐太宗不误作当时在位人物。')
add('officials_separate_xu_temple','群臣提议另设徐温祠庙，李昪以受恩于徐温回应',5,'群臣言：','群臣乃不敢言。',[('唐主','以自幼受徐温养育及其对吴国的功劳回应另建庙的建议'),('义祖','宗庙待遇受到讨论，其恩养和功劳被李昪强调')],description='群臣认为徐温原为诸侯，不应与唐高祖、唐太宗同享祭祀，建议在太庙正殿后另建庙。李昪强调自己自幼依托徐温，且徐温有功于吴，群臣随后不敢再议。',note='另建庙为提议，原文未记最终照议另建；李昪的话是自己说明的恩义，不补一条未经核对的血缘关系。')
add('li_considers_ancestry','李昪打算追认吴王李恪为祖先，有人建议改认郑王',5,'唐主欲祖','郑王无懿。”',[('唐主','打算追认吴王李恪为祖先'),('吴王恪','被李昪考虑追认为祖先')],description='李昪打算追认吴王李恪为祖先。有人以李恪遭诛为由，建议改认郑王；所用《资治通鉴》电子本将这位郑王的名字写作“无懿”，仍待版本校核。',note='这是一项选择祖系的意图和他人建议，不直接建立李昪与唐朝宗室的确定祖孙关系；疑名不新建确定人物。')
add('li_commissions_ancestry','李昪命官员考查祖系，选择吴王李恪并接受官员编写的世系',5,'唐主命有司','其名率皆有司所撰。',[('唐主','命官员考查二王后裔，决定追认吴王，并接受所编世系'),('吴王恪','在编祖系过程中被选为李昪的祖先'),('祎','以吴王之孙身份被祖系讨论引用'),('岘','以李祎之子、唐代宰相身份被祖系讨论引用'),('荣','以李昪父亲身份被所编世系提到')],description='官员以吴王的孙子李祎有功、李祎之子李岘曾任宰相为依据，选择吴王李恪，称从李岘下传五世到李昪父亲李荣。《资治通鉴》指出，其中的名字大多由官员编撰。',note='记录当时如何构造祖系，不将李昪与李岘之间的五代世系做成已证实亲属链。李祎为唐代宗室，与既有晚唐同名人物区别。')
sup('li_commissions_ancestry',5,nt,source_span(nt,'自言唐憲宗子','改國號曰唐。'),'《新五代史》另记李昪自称唐宪宗子建王恪的四世孙，并列恪、超、志、荣的世系。','该书所称建王、帝系及代数，与主书吴王李恪、李祎李岘链不同，分别保留为祖系说法，不合并为确定血缘。',relation='conflicts')
claim('person',people['李祎（唐信安郡王）'],'description','《新唐书》记李祎在开元年间改封信安郡王，曾任礼部尚书、朔方节度使。',5,source_span(ty,'開元時，','朔方節度使。'),'唐代任职及纪年用来区分晚唐同名人物，不在939年另录这些旧任官事件。',source=ty)
relationship('祎','岘','父亲',5,'祎子岘为宰相，','此处明确李祎是李岘的父亲，只录两位唐代人物之间的亲属关系，不向李昪延伸。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《新唐书》在李祎传末记其教子有法，峘、嶧、峴都有成就。',5,'祎治家嚴，教子有法度，故峘、嶧、峴皆顯。','附传上下文和教子句确认李岘为李祎之子，摘录保持繁体。',source=tys,relation='corroborates')
add('li_questions_generations','李昪质疑祖系代数，听取每三十年一代的解释后接受',5,'唐主又以',None,[('唐主','认为三百年十世过少，听取官员解释后接受')],description='李昪认为唐朝经历十九位皇帝、三百年，而所列十代祖系显得太少。官员以三十年为一代，并以李昪生于文德年间、距今约五十年来解释，李昪于是接受。',note='这些年数是当时的辩解，不据此反推人物精确生日或确认虚构祖系。')
add('min_receives_lu_sun','卢损到福州，王继鹏称病不见，命王继恭接待',6,'卢损至','命弟继恭主之。',[('卢损','到福州出使，但未获王继鹏接见'),('闽主','称病不见卢损，命王继恭接待'),('王继恭','受命接待卢损')],place='福州',note='称疾不见只说明托病拒见，未确诊疾病；原文弟与既有亲属异说并列，不重写已发布关系。')
add('zheng_yuanbi_tribute','郑元弼奉王继恭表章，随卢损前往后晋进贡',6,'遗其礼部','随损入贡。',[('郑元弼','以礼部员外郎身份，奉王继恭表章随卢损进贡'),('王继恭','表章由郑元弼携带入贡'),('卢损','与郑元弼同行返回后晋')],place='福州、后晋',note='底本遗字保留，依行动语境理解为派遣；未扩写表章内容或进贡物品。')
add('lin_shengzou_criticizes','林省邹私下批评王继鹏，并向卢损表示计划北逃',6,'闽主不礼',None,[('林省邹','私下向卢损批评王继鹏，并表示计划扮作僧人北逃'),('卢损','受到王继鹏失礼对待，听到林省邹的批评与北逃计划'),('闽主','被林省邹批评不善待君主、亲人、百姓、神祇、邻国和宾客')],place='福州',description='王继鹏对卢损失礼。林省邹私下向卢损批评王继鹏不敬君主、不爱亲人、不体恤百姓、不敬神祇、不睦邻、不礼宾客，认为他难以长久维持统治。林省邹表示计划穿僧服北逃，期待以后在后晋相见。',note='批评与预测归林省邹，北逃是计划，不录为已经逃到后晋。')
add('li_ke_posthumous','李昪追尊吴王李恪为定宗孝静皇帝',7,'三月，','定宗孝静皇帝，',[('唐主','追尊吴王李恪为定宗孝静皇帝'),('吴王恪','被南唐追尊为定宗孝静皇帝')],when='939年三月庚戌',note='这是南唐事后追尊，不是李恪在939年即位；追尊不等于祖系血缘得到证实。')
sup('li_ke_posthumous',7,nt,'追尊四代祖恪為孝靜皇帝，廟號定宗；','《新五代史》也记追尊所认祖先恪为孝静皇帝、庙号定宗。','名号可以对照，但同段祖系为建王恪说，与主书吴王李恪不同，不能只因追尊名号相同就认定远祖身份。',relation='conflicts')
add('li_ancestors_posthumous','李昪为所认曾祖以下祖先追尊庙号和谥号',7,'自曾祖',None,[('唐主','为所认曾祖以下祖先追尊庙号和谥号')],when='939年三月庚戌',note='主书没有在本句列出全部个人名号，不据此新建未证实世系链。')
sup('li_ancestors_posthumous',7,nt,source_span(nt,'曾祖超為','廟號慶宗。'),'《新五代史》具体列出所认曾祖超为孝平皇帝、成宗，祖志为孝安皇帝、惠宗，父荣为孝德皇帝、庆宗。','这是南唐祖先追尊名号的独立记载，不用追尊名号证明各代生物学血缘或统一两书祖系。')
add('liu_du_chancellors','石敬瑭同时给刘知远、杜重威加同平章事',8,'己未，','并加同平章事。',[('帝','给刘知远、杜重威加同平章事'),('刘知远','以归德节度使身份获加同平章事'),('杜重威','以忠武节度使身份获加同平章事')],when='939年三月己未')
sup('liu_du_chancellors',8,mar,source_span(mar,'己未，','並加同中書門下平章事。'),'《旧五代史》也记三月己未刘知远、杜重威加同中书门下平章事，并将郑王石重贵列为同时获加者。','石重贵属于同次任命的补充；仅补对应行动，不因主书省略就判其不在任命中。')
add('liu_refuses_du_equivalence','刘知远不愿与杜重威同受任命，闭门四次上表推辞',8,'知远自以','杜门四表辞不受。',[('刘知远','认为自己有扶立功劳，不愿与杜重威同受任命，四次上表推辞'),('杜重威','因外戚身份获任，在刘知远的意见中功劳不足')],description='刘知远认为自己有扶立石敬瑭的功劳，而杜重威主要凭外戚身份起用、没有大功，不愿与他同受任命。诏令下达几天后，刘知远闭门，四次上表推辞。',note='无大功是此处刘知远的看法，不作网站对杜重威全部生涯的定论；数日不换算确切日期。')
add('shi_threatens_liu_removal','石敬瑭因刘知远拒命发怒，提出解除其军权',8,'帝怒，','令归私第！”',[('帝','向赵莹提出解除刘知远军权、让其归家的意见'),('赵莹','听到石敬瑭因刘知远拒命而发怒的意见'),('刘知远','因拒绝任命而受到解除军权的威胁')],description='石敬瑭发怒，向赵莹强调杜重威是自己的妹夫，责问刘知远为何坚拒诏令，并提出解除刘知远军权、让他回私人住宅。',note='这是皇帝发怒时的意见，后文接受劝解，不录成军权已实际解除；妹夫沿既有亲属记录，不猜新增妻子姓名。')
add('zhao_ying_defends_liu','赵莹以晋阳起兵时的功劳劝石敬瑭宽容刘知远',8,'莹拜请曰：','帝意乃解，',[('赵莹','以刘知远在晋阳危局中的功劳劝谏，担忧皇帝显得不够宽容'),('帝','接受赵莹的劝解，不再坚持解除刘知远军权'),('刘知远','此前扶立功劳被赵莹用来劝谏')],description='赵莹提到石敬瑭在晋阳只有约五千兵、面对十余万唐军时，刘知远坚定相助，认为不应因小过弃用他，也担忧这些话传出去影响皇帝宽容的形象。石敬瑭听后怒意缓解。',note='兵数是赵莹话中对旧事的概述，不新建939年晋阳战役；原话危于朝露用白话解释为处境危险。')
add('he_ning_persuades_liu','和凝奉命到刘知远家传达旨意，刘知远接受任命',8,'命端明',None,[('帝','派和凝到刘知远家传达旨意'),('和凝','以端明殿学士身份前往刘知远家传达旨意'),('刘知远','听到旨意后惶恐，起身接受任命')],note='从拒命到受命按原文先后录，不保留一条已经罢免的虚构结果。')
fh='jiuwudaishi-125-feng-hui'
claim('person',people['冯晖'],'description','《旧五代史》记冯晖为魏州人，曾任兴州刺史；参与范延光叛乱，归降后任滑州节度使，后来调到灵武。',2,source_span(fh,'長興中，','鄴平，移鎮靈武。'),'934年兴州、937年范延光军及938年归降任义成的经历相连，沿既有后唐后晋主体；902年同名记录另列身份核查，不作为本次同人依据。',source=fh)
sup('tuoba_visits_feng',2,fh,source_span(fh,'党項拓拔彥昭者，','因留之不令歸部。'),'《旧五代史》也记党项首领到访后受到厚待、获建宅第并被留在城中，但姓名写作拓拔彦昭。','待遇和行动相合，主书为拓跋彦超，另一书为拓拔彦昭；姓名差异保留，不因字形不同直接再建一个参加同次行动的人。',relation='conflicts')
reviews={1:'主书正月辛亥任张从恩，旧史同职任命接己酉条而未单列辛亥，纪日精度分别保留。',2:'张希崇死亡、辖地劫掠、冯晖甲寅调任、拓跋彦超来贺被留及安定评价分录；未猜劫掠者姓名、家属或现代坐标。',3:'请求复姓、正月乙丑批准、拒尊号及后代制度追述分开，后代年份留空，新史合记复姓改名不压成同日。',4:'徐温庙号与皇后宋氏回查937年原文；补行父母丧礼不写成本年父母去世；广德借服按借用读，李建勋丈夫方向明确。',5:'委李璟国事非让位，二月庚寅改名，宗庙提议与决定区分。李昪编祖系不建确定远祖链；主吴王李祎李岘、新史建王世系不同，唐代李祎与晚唐同名区分，父子关系有新唐书补证。郑王无懿疑名暂不建人。',6:'卢损到福州实际执行，闽拒见和王继恭接待、郑元弼入贡、林省邹批评与北逃计划分开，未强定亲属异说或实际北逃。',7:'追尊是南唐礼制行为，非唐吴王本年即位或血缘确证；新史祖名号与帝系差异保留。',8:'同平章事加衔、刘知远闭门四次辞命、石敬瑭罢权意见、赵莹劝解、和凝谕旨与接受分录，未写罢权已执行；晋阳旧事只是劝谏中的追述。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=939,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=282,next_year=939,supplements=supplements,source_contexts=[dict(source_key=old,note='937年已发布片段只用于核对皇后姓宋，不重新录入937年立后事件。')],excluded_non_body=[dict(source_lines=[1,5],reason='卷题、范围题、帝纪标题、分隔符和939年题，只保留于原文快照，不生成事件。')],coverage='连续第1—8段，原6—13行；正月至三月，939年41段尚未完成。',source_issues_review='主书吴王祖系与新史建王祖系不同，不建立确定远祖链；郑王无懿姓名待版本校核；张从恩任命纪日差异保留。原文保持字形，纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],plain_language_review='首次逐条检查人物、事件、参与、关系及事实与出处解释；请求与行动、计划与结果、旧事追述与本年事件、史书判断与人物自述分别表述，摘录原字不改。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
