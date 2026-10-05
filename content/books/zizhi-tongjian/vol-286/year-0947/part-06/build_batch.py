# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 24–29."""
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
COMMIT='6ff82fc5c6ceef78ebad27a4ff3e3aceb8c67445'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-zhang-nantang']:
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
main_sources = ['tongjian-286-947-zhang-nantang']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p024-p029',
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
for n in range(24, 30):
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
        citation = f'卷286·天福十二年（947年正月至二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_06_{len(B["claims"])+1:04d}'
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
ALIASES.update({'契丹主':'耶律德光','唐主':'李璟','景遂':'徐景遂','景达':'徐景达','弘冀':'李弘冀','冯延己':'冯延巳','延己':'冯延巳','延鲁':'冯延鲁','王建':'王建（后晋棣州刺史）'})
NEW_ALIASES={'张易':['張易'],'王建（后晋棣州刺史）':['王建（後晉棣州刺史）']}
NEW_DESCRIPTIONS={'张易':'元城人，南唐赞善大夫。947年条下记载，他在李景遂宴席上劝谏未被理会，摔碎杯子后，李景遂向他道歉；又劝李景达不要屡次当面斥责其他近臣。两次宴集为追述，具体年份未载；生卒年未知。','王建（后晋棣州刺史）':'后晋棣州刺史。947年契丹占据大梁后，为躲避契丹，与密州刺史皇甫晖率部投奔南唐。与前蜀开国君主王建不是同一人，按时代职务限定主体；生卒年未载。'}
t='947年初，具体日未载';past='947年条下追述宴集，具体年日未载';nw='xinwudaishi-062-947-succession';ls='liaoshi-004-947-february';j='jiuwudaishi-098-zhao-titles'
add('gao_conghui_tribute_khitan','高从诲向契丹进贡，耶律德光派使者赐马回赠',24,'荆南节度使','以马赐之。',[('高从诲','派使者向契丹进贡'),('契丹主','派使者赐马回赠')],when=t,place='荆南至契丹朝廷',note='未给贡物马匹数量，不补估价。')
add('gao_encourages_liu_accession','高从诲另派使者到河东，劝刘知远称帝',24,'从诲亦','劝进。',[('高从诲','派使者赴河东劝进'),('刘知远','受到称帝劝进')],when=t,place='荆南至河东',note='劝进是建议，实际称帝在后续段落，不提前写已经称帝。')
add('jingsui_crown_brother','李璟立李景遂为皇太弟',24,'唐主立','皇太弟。',[('唐主','册立皇太弟'),('景遂','由齐王被立为皇太弟')],when=t,place='南唐朝廷',note='李景遂与网站已有的徐景遂为同一人，沿用原有人物记录。册立皇太弟不表示已经继位。')
sup('jingsui_crown_brother',24,nw,'五年，以景遂為太弟','《新五代史》也在保大五年记立景遂为太弟。','五年对应本年，但未标具体月日；与主书同一主体。')
add('jingda_qi_commander','李璟把李景达改封为齐王，任诸道兵马元帅',24,'徙燕王景达','元帅。',[('唐主','改封并授军职'),('景达','由燕王改齐王，任诸道元帅')],when=t,place='南唐朝廷',note='李景达沿用网站已有的徐景达人物记录。任命为元帅不表示他此时已经指挥某场战役。')
sup('jingda_qi_commander',24,nw,'景達為元帥，封齊王','《新五代史》同记景达为元帅并封齐王。','册封与元帅授职相符。')
add('hongji_yan_deputy','李璟把李弘冀改封为燕王，任副元帅',24,'徙南昌王','为之副。',[('唐主','改封并任副元帅'),('弘冀','由南昌王改燕王，任副元帅')],when=t,place='南唐朝廷',note='李弘冀担任李景达的副手，《新五代史》明确称副元帅；这不是皇太弟的副手或共同继位人。')
sup('hongji_yan_deputy',24,nw,'南昌王冀為副元帥，封燕王','《新五代史》明记弘冀的军职为副元帅。','结合南昌王的封号与上下文，冀指李弘冀，沿用同一人物记录。')
add('zhang_yi_breaks_cup','张易劝谏李景遂未受理会，斥其重宝轻士，摔碎杯子',24,'景遂尝','众皆失色。',[('张易','在宴集上劝谏、斥责并摔杯'),('景遂','传玩器物，未理会劝谏')],when=past,year=None,place='南唐宫僚宴席',note='底本前文写玉怀，后文写取杯，按同段动作理解为杯子，引用仍保留原字，异文待核。史书未载劝谏的具体内容；尝表示追述，不能确定发生在947年。')
add('jingsui_apologizes_to_zhang_yi','李景遂向张易道歉，此后更加礼遇他',24,'景遂敛容','待易益厚。',[('景遂','收敛神色道歉并厚待张易'),('张易','获道歉与更厚礼遇')],when=past,year=None,place='南唐宴席',note='待易益厚是后续礼遇，不推具体赠财、官职。')
add('jingda_rebukes_flattery','李景达多次斥责宴席上的谄媚行为，并劝李璟不要亲近佞臣',24,'景达性刚直，','亲近佞臣。',[('景达','斥责近臣并劝谏皇帝'),('唐主','受到亲近近臣问题的劝谏'),('冯延己','被列为宴席上谄媚者'),('延鲁','被列为宴席上谄媚者'),('魏岑','被列为宴席上谄媚者'),('陈觉','被列为宴席上谄媚者')],when='947年条下追述多次宴饮，具体年日未载',year=None,place='南唐宫廷',note='刚直、谄媚为史家评价；屡为多次，不补各次日期。')
add('feng_claims_credit_jingda_seeks_execution','冯延巳在东宫宴席上假醉向李景达邀功，李景达向李璟请求杀他',24,'延己以二弟','请斩之。',[('冯延己','以假醉举动向景达邀功'),('景达','愤怒离席，入宫请求处死冯延巳'),('唐主','收到处死请求')],when=past,year=None,place='南唐东宫至禁中',note='二弟立指景遂景达册封地位，不译为两人都登基；假醉及邀功动机是史书所述，请斩不是已处决。')
add('li_jing_mediates_feng_dispute','李璟劝解李景达，处死冯延巳的请求遂止',24,'唐主谕解，','乃止。',[('唐主','劝解并停止处死请求'),('景达','接受劝解停止请求'),('冯延己','未因这次请求被处死')],when=past,year=None,place='南唐禁中')
add('zhang_yi_warns_jingda_avoids_banquets','张易提醒李景达当面斥责会让近臣防备，李景达此后多称病不参加宴饮',24,'张易谓',None,[('张易','分析当面斥责近臣的风险'),('景达','此后多以病为由避开宴饮')],when='947年条下追述宴席风波后，具体年日未载',year=None,place='南唐宫廷',note='所述风险是张易意见，不当近臣全部已发动迫害；辞疾为称病，未当确诊疾病。')
add('li_jing_congratulates_khitan_requests_tombs','李璟派使者祝贺契丹灭晋，并请求到长安修复唐朝陵墓',25,'唐主遣使','唐室诸陵。',[('唐主','派使者祝贺并请求修陵'),('契丹主','收到祝贺和请求')],when=t,place='南唐至契丹朝廷；长安（拟修陵地点）',note='唐室是南唐援引的唐朝祖业，未证明实际血缘；请求不作已修复。')
add('khitan_rejects_tomb_request','耶律德光不许李璟修复唐朝陵墓，并派使者回复',25,'契丹不许',None,[('契丹主','拒绝修陵请求并派使答复'),('唐主','请求被拒绝')],when=t,place='契丹朝廷至南唐',note='报之是回复，不推答复具体原因或使者名字。')
add('huangfu_wang_flee_to_nantang','皇甫晖、棣州刺史王建率部避开契丹，投奔南唐',26,'晋密州刺史','帅众奔唐。',[('皇甫晖','以密州刺史身份率众投唐'),('王建','以棣州刺史身份率众投唐')],when=t,place='密州、棣州至南唐',note='王建按时代官职与前蜀王建区分；未载部众人数及确切抵达点。')
add('huaibei_groups_seek_nantang_orders','淮北多名武装首领请求归南唐调遣',26,'淮北贼帅',None,[],when=t,place='淮北至南唐',note='贼帅是史书称谓，展示称武装首领；多请命是请求，不写全部已受任具体官职。')
add('han_xizai_proposes_northern_expansion','韩熙载上疏劝李璟趁中原尚未另立君主向北进取，并提醒契丹北归后机会将更少',27,'唐虞部员外郎','未易图也。”',[('韩熙载','以虞部员外郎史馆修撰身份上疏'),('唐主','受到向北用兵建议')],when=t,place='南唐朝廷',note='恢复祖业是韩熙载奏疏中的政治主张，不据此证明李璟与唐朝皇室的血缘。若契丹北归是对未来的假设，不表示此时已经北归。')
add('nantang_misses_north_opportunity','南唐因仍在福州用兵，未能北上，史书记南唐人遗憾、李璟也后悔',27,'时方连兵',None,[('唐主','因福州战事未北顾，后悔错过时机')],when=t+'及事后回顾',place='南唐朝廷与福州',note='皆恨为史家概述，不当全体南唐民众都已逐一表达意见；后悔具体时点不强定。')
add('khitan_consults_jin_officials_on_ruler','耶律德光召晋臣询问另选谁治理中原，官员两次请求由他执政',28,'契丹主召','如是者再。',[('契丹主','询问另选统治者，得到百官拥戴')],when='947年二月丁巳朔仪式之前，具体日未载',place='大梁宫廷',note='方数万里、君长二十七为自述规模，不转成精确地图或已核名单。百官未名，不虚造参与名单。')
add('officials_advise_amnesty','耶律德光问接下来应先做什么，官员建议颁布大赦',28,'契丹主乃曰：','应大赦。”',[('契丹主','问施政顺序并听取大赦建议')],when='947年二月丁巳朔之前，具体日未载',place='大梁宫廷',note='建议与后续实际大赦分记，不补未名答者。')
add('khitan_february_court_ceremony','耶律德光在二月朔以中原礼服登正殿，设置乐器仪卫，百官按各自服制朝贺',28,'二月，丁巳朔，','文武班中间。',[('契丹主','在正殿举行朝贺仪式')],when='947年二月丁巳朔',place='大梁宫廷正殿',note='华人法服、胡人胡服是原书记礼服排列，不为每个既有官员自动连入朝贺。')
add('liao_name_and_amnesty','耶律德光以大辽名号颁布大赦，通鉴底本称会同十年',28,'下制称','大赦。',[('契丹主','以大辽名号颁制大赦')],when='947年二月丁巳朔',place='大梁',note='当前通鉴底本会同十年与辽史改元大同不同，分别引用不强定唯一年号，也不悄改原字。')
sup('liao_name_and_amnesty',28,ls,'二月丁巳朔，建國號大遼，大赦，改元大同。','《辽史》同记二月丁巳朔建国号大辽、大赦，但记改元大同。','当前《资治通鉴》底本写会同十年，《辽史》写改元大同，分别保留两书记载；纸本及同书不同版本尚待校核。',relation='conflicts')
add('khitan_bans_private_troops_horse_purchase','耶律德光下令节度使、刺史不得设牙兵或购买战马',28,'仍云：',None,[('契丹主','颁布地方长官设牙兵及买马禁令')],when='947年二月丁巳朔',place='大辽所辖各镇州（诏令范围）',note='记诏令内容，不因此断言各地已经全部解散牙兵或无马。')
add('zhao_requests_crown_prince_via_li_song','赵延寿因耶律德光没有兑现承诺而不满，请李崧代为求立皇太子',29,'赵延寿以','崧不得已为言之。',[('赵延寿','请李崧转达皇太子请求'),('李崧','不得已转达'),('契丹主','收到请求')],when='947年二月条下，具体日未载',place='大梁契丹朝廷',note='汉天子不敢望是赵此时说辞，不写他曾真正被立为皇帝；实指未获允诺。')
sup('zhao_requests_crown_prince_via_li_song',29,j,'延壽在汴久之，知契丹主無踐言之意，乃遣李崧達語契丹主，求立為皇太子','《旧五代史》也记赵延寿知承诺无兑现意，请李崧转达立太子请求。','《旧五代史》的久之没有给出具体日期，年份按《资治通鉴》本段确定，月日保留未定。')
add('khitan_rejects_zhao_as_prince','耶律德光以皇太子应由天子儿子担任为由拒绝赵延寿，另令加官',29,'契丹主曰：','为燕王迁官。',[('契丹主','拒绝立赵为太子，改令加官'),('赵延寿','太子请求被拒绝')],when='947年二月条下，具体日未载',place='大梁',note='割肉为耶律德光表达亲厚的譬喻，没有实际割肉或血缘关系。迁官作为替代加官安排。')
add('hengzhou_becomes_central_capital','契丹把恒州设为中京',29,'时契丹以','中京，',[('契丹主','设置中京')],when='947年二月条下，主书未标日',place='恒州（中京）',note='时为背景解释，不据此自换公历日期。')
sup('hengzhou_becomes_central_capital',29,ls,'升鎮州為中京。','《辽史》在二月丁巳朔条下记升镇州为中京。','恒州镇州为同城历史称谓对应，保留各书记日，未补地理坐标。',relation='adds',field='time_original')
add('zhang_proposes_zhao_titles','张砺拟赵延寿为中京留守、大丞相及总领政事军队等官职，保留枢密使',29,'翰林承旨张砺','枢密使如故。',[('张砺','拟定赵延寿加官方案'),('赵延寿','成为拟加官对象')],when='947年二月条下，具体日未载',place='大梁至中京（拟任地）',note='拟录尚书事、都督中外诸军事不当实际获得，后句删去两项；原枢密使如故不新造首次任命。')
add('khitan_removes_zhao_military_power_titles','耶律德光删去录尚书事、都督中外诸军事两项，批准其余加官方案',29,'契丹主取笔',None,[('契丹主','删去两项统领政军权的拟官'),('赵延寿','仅获其余批准官职')],when='947年二月条下，具体日未载',place='大梁',note='涂去后而行的是删项后方案，不在角色中说赵已经有全部军政总权。')
sup('khitan_removes_zhao_military_power_titles',29,j,'契丹主覽狀，索筆圍卻「錄尚書事、都督中外諸軍事」之字，乃付翰林院草制焉。','《旧五代史》也记划去两项官衔，交翰林院草制。','只是对应本段拟官和删项，不提前录传记后续赵被锁及婚配等事。')
sup('khitan_removes_zhao_military_power_titles',29,ls,'以趙延壽為大丞相兼政事令、樞密使、中京留守','《辽史》列赵延寿实际任大丞相兼政事令、枢密使、中京留守。','《辽史》的政事令是本书补充的官衔。被划去的录尚书事、都督中外诸军事不列为赵延寿实际获得的职务。',relation='adds')
reviews={24:'高贡与劝进、南唐三任命分别；景遂景达复用徐氏旧key，冯延己沿巳，玉怀疑杯按同段仍存原字。尝宴和多次谏为追述，不强定年；冯邀功与请斩未执行，辞疾非确诊。',25:'修唐陵是请求被拒，未录完成或虚造理由。',26:'棣州王建与前蜀开国君不同，限定职务分档；淮北首领未名不猜，归唐请求不当已经全体受职。',27:'恢复祖业政治奏疏不证明血缘，北归是假设；福州牵制、遗憾和后悔为史家概述，未补全部民众态度。',28:'另选治中原与拥戴、大赦建议、二月朔朝仪、名号大赦和禁牙兵买马分录；会同十年与辽改元大同并列，命令不等实际全部执行。',29:'求太子转请、拒绝、设中京、拟官和删项分清，割肉譬喻不当实际血缘；辽补实际官衔，未删两项不算实得，传记后续留后段。'}
assert not (P/'publication.json').exists()
for n in range(24,30):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(24,30)],next_paragraph=Q[30]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原29—34行连续六段，累计29/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(24,30)],source_issues_review='景遂达及冯延巳稳定主体复用，王建按职时代分档；玉怀杯异字原文保存；辽大同与通鉴会同十年并列，赵拟官两项删去不当实际获权。',plain_language_review='首次逐条检查展示白话、身份时间、关系方向及原文；追述、建议、表态和实际执行分清，未扩展旧内容全面校改。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
# A person can have two roles in one event; preserve a single participation row.
seen={}
for edge in B['person_events']:
 if edge['key'] in seen:raise AssertionError(('duplicate participation',edge['key']))
 seen[edge['key']]=edge
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
