# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 941 paragraphs 7–11."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,39))
specs=[(d.name,d,'6a1f52aa71e10dbcefa59b542374cb6f53ccd662','欧阳修') for d in sorted((P/'sources/library').iterdir())]
specs.append(('tongjian-282-941-spring',YEAR/'part-01/sources/library/tongjian-282-941-spring','652233df546823980246fe2d04ddc59b70526578','司马光等'))

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
main_sources = ['tongjian-282-941-spring']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0941-p007-p011',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-282-941-spring':'卷282·天福六年春夏','xinwudaishi-069-an-congjin-aid':'卷69·南平世家·安从进求援','xinwudaishi-069-wang-baoyi':'卷69·南平世家·高季兴宾客'}
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
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(7, 12):
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
    labels={'tongjian-282-941-spring':'卷282·天福六年春夏','xinwudaishi-069-an-congjin-aid':'卷69·南平世家·安从进求援','xinwudaishi-069-wang-baoyi':'卷69·南平世家·高季兴宾客'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '四月条下'
        citation = f'卷282·后晋天福六年（941；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0941_02_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=941, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='941年四月条下，具体日期未载'
    key = 'event_zztj_282_0941_' + code
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
        edge = 'participation_zztj_282_0941_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0941_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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





reused.discard("tongjian-282-941-spring")
ALIASES.update({'唐主':'李昪','蜀主':'孟昶','曦':'王延羲','亚澄':'王亚澄','延喜':'王延喜','延政':'王延政','汉主':'刘岩'})
NEW_DESCRIPTIONS={
'王亚澄':'闽王王延羲的儿子。941年四月被任命为同平章事，主管六军诸卫。生卒年未载。',
'王延喜':'闽王王延羲的弟弟，汀州刺史。941年四月王延羲怀疑他与王延政串通，派许仁钦率兵将他拘捕带回。串通是王延羲的怀疑，原文没有确认。生卒年未载。',
'许仁钦':'闽国将军。941年四月奉王延羲之命，率三千兵前往汀州，拘捕王延喜并带回。生卒年未载。',
'常梦锡':'南唐官员，万年人。941年四月与陈觉一起被李昪任命为宣徽副使。生卒年未据本段确定。',
'白承福':'吐谷浑酋长。941年四月辛巳，北京留守李德珫派牙校带领白承福入朝。原文没有说明他是否就是此前归附后晋的某支未具名部众首领。生卒年未据本段确定。',
'欧阳遇':'南唐通事舍人。941年四月受李昪派遣，向后晋请求借道通往契丹，石敬瑭拒绝请求。生卒年未载。',
'王保义':'荆南行军司马。941年安从进筹划反叛后晋、向荆南求援，王保义劝高从诲向朝廷详报情况，并请求派兵协助朝廷讨伐，高从诲听从。新五代史还记他曾是高季兴的宾客，具体起年未载。生卒年未载。'}
NEW_ALIASES={'王亚澄':['王亞澄'],'王延喜':[],'许仁钦':['許仁欽'],'常梦锡':['常夢錫'],'白承福':[],'欧阳遇':['歐陽遇'],'王保义':['王保義']}
add('xi_promotes_yacheng','王延羲任儿子王亚澄为同平章事，并主管六军诸卫',7,'夏，四月，','判六军诸卫。',[('曦','任命儿子掌管六军诸卫'),('亚澄','获任同平章事并主管六军诸卫')],place='闽国')
relationship('曦','亚澄','父亲',7,'闽王曦以其子亚澄同平章事、判六军诸卫。','其子明确指王亚澄是王延羲的儿子；关系方向为王延羲是王亚澄的父亲。')
relationship('延喜','曦','弟弟',7,'曦疑其弟汀州刺史延喜与延政通谋，','其弟明确指王延喜是王延羲的弟弟，不补其他未明亲属。')
add('xi_suspects_yanxi','王延羲怀疑王延喜与王延政串通',7,'曦疑其弟','通谋，',[('曦','怀疑弟弟与王延政串通'),('延喜','受到王延羲怀疑'),('延政','被怀疑与王延喜串通')],place='闽国',note='疑是王延羲的判断，不录成已经查实的谋反，也不建立两人的盟友关系。')
add('xu_arrests_yanxi','许仁钦率三千兵赴汀州，拘捕王延喜并带回',7,'遣将军许仁钦',None,[('曦','派兵拘捕王延喜'),('许仁钦','率三千兵赴汀州拘捕并带回王延喜'),('延喜','在汀州被拘捕并带回')],place='汀州',note='主语承接王延羲；三千为出兵人数，带回目的地及后续处置未载。')
add('li_bian_appoints_deputies','李昪任陈觉、常梦锡为宣徽副使',8,'唐主',None,[('唐主','任命两名宣徽副使'),('陈觉','获任宣徽副使'),('常梦锡','获任宣徽副使')],place='南唐',note='万年是常梦锡的籍贯，不是姓名组成部分。')
claim('person','person_常梦锡','biography','常梦锡是万年人。',8,'万年常梦锡','万年是籍贯名称，保留史载名称，不补现代坐标。')
add('bai_chengfu_court','李德珫派牙校带领吐谷浑酋长白承福入朝',9,'辛巳，',None,[('李德珫','派牙校带白承福入朝'),('白承福','由北京留守所派牙校带领入朝')],when='941年四月辛巳',place='后晋',note='未具名牙校不建立主体；不补接见、赏赐或归附部众数量，北京为后晋地名。')
add('li_bian_requests_passage','李昪派欧阳遇向后晋请求借道通往契丹',10,'唐主遣','以通契丹，',[('唐主','派通事舍人提出借道请求'),('欧阳遇','向后晋请求借道通往契丹')],place='后晋',note='请求借道不等于已抵达契丹或缔结联盟。')
add('shi_refuses_passage','石敬瑭拒绝南唐借道通往契丹的请求',10,'帝不许。','帝不许。',[('帝','拒绝借道请求')],place='后晋',note='拒绝的对象承接欧阳遇的借道请求，不补拒绝原因。')
claim('person',person('唐主',10,'即位后，史书记其境内江淮连年丰收','及唐主即位，江、淮比年丰稔，兵食有馀，'),'biography','《资治通鉴》概述，李昪即位后，江淮连年丰收，军粮充足。',10,'及唐主即位，江、淮比年丰稔，兵食有馀，','这是即位以来的一段概述，未给每年产量，不造一场941年单日丰收事件。')
add('ministers_urge_northern_campaign','南唐群臣建议李昪趁北方多难，出兵恢复旧疆',10,'群臣争言','宜出兵恢复旧疆。”',[('唐主','收到群臣出兵恢复旧疆的建议')],description='南唐群臣以江淮丰收、军粮充足和北方多难为由，建议李昪出兵恢复旧疆。',note='群臣没有具名，建议不当作实际北伐命令，原文没有具体目标城镇。')
add('li_bian_rejects_war','李昪以亲见战乱伤害百姓为由，拒绝群臣出兵建议',10,'唐主曰：','又何求焉！”',[('唐主','以战争伤害百姓为由拒绝出兵建议')],description='李昪说，自己从小在军旅中成长，深知战争对百姓的伤害，不愿再提战争；如果北方百姓安定，南唐百姓也能安定。',note='这是李昪解释拒绝出兵的言论，不作为天下百姓已全部安定的事实。')
add('liu_yan_proposes_chu_attack','刘岩派使者向南唐提议联合攻楚，瓜分楚地',10,'汉主遣使如唐，','分其地；',[('汉主','派使者提议联合攻楚并分地'),('唐主','收到南汉联合攻楚的提议')],place='南唐',note='汉主为南汉刘岩，不是尚未建立的后汉；未具名使者不建主体，计划不当作战争已开始。')
add('li_bian_rejects_chu_attack','李昪拒绝南汉联合攻楚的提议',10,'唐主不许。','唐主不许。',[('唐主','拒绝联合攻楚提议')],place='南唐',note='拒绝的是前句刘岩联合攻楚分地的提议，不补具体拒绝原因。')
add('an_asks_shu_aid','安从进筹划反叛后晋，派使者向后蜀请求出兵金州、商州',11,'山南东道节度使','以为声援；',[('安从进','筹划反叛，向后蜀请求军事声援')],place='金州、商州',note='本段是筹划与求援，不提前记成已经起兵；金、商是请求后蜀出兵的目标，不是已经占领的地点。')
add('an_envoy_reaches_chengdu','安从进的使者到达成都',11,'丁亥，','使者至成都。',[],when='941年四月丁亥',place='成都',note='丁亥用于使者抵达，不套给此前筹谋、出发或其他求援行动。')
add('meng_consults_shu_aid','孟昶与群臣商议安从进的求援，群臣认为出兵难以持续',11,'蜀主与群臣','多则漕輓不继。”',[('蜀主','与群臣商议是否援助安从进')],place='成都',description='孟昶与群臣商议安从进的求援。群臣认为金州、商州险远，少派兵不足以制敌，多派兵又难以持续运输粮食。',note='这是议论出兵困难，不写成后蜀已经出征后断粮。')
add('meng_refuses_an_aid','孟昶拒绝安从进的军事求援',11,'蜀主乃辞之。','蜀主乃辞之。',[('蜀主','拒绝向安从进提供军事援助')],place='成都')
add('an_asks_jingnan_aid','安从进又向荆南求援',11,'又求援于荆南，','又求援于荆南，',[('安从进','向荆南求援')],place='荆南',note='求援主语承接安从进，未补使者姓名、兵数或承诺。')
add('gao_warns_an','高从诲写信向安从进说明反叛的祸福',11,'高从诲遗从进书，','谕以祸福；',[('高从诲','写信说明反叛的祸福'),('安从进','收到高从诲的告诫')],place='荆南',note='按主书保留劝止；传记所载暗中往来作为异说补充，不据此建立已核盟友关系。')
sup('gao_warns_an',11,'xinwudaishi-069-an-congjin-aid','襄州安從進反，結從誨為援，從誨外為拒絕，陰與之通。','《新五代史》还记，安从进反叛时寻求高从诲援助，高从诲表面拒绝，暗中与他往来。','《资治通鉴》侧重告诫及助朝廷的建议，《新五代史》另有暗中往来的记载；不能据此裁定本次书信是伪装，也不把传记概括强定为四月丁亥当天。',relation='conflicts')
add('an_accuses_gao','安从进因高从诲的信发怒，向朝廷诬告高从诲',11,'从进怒，','反诬奏从诲。',[('安从进','因告诫发怒，反向朝廷诬告高从诲'),('高从诲','受到安从进诬告')],note='诬告的具体罪名未载，不补其奏章内容。')
add('wang_baoyi_advises','王保义劝高从诲详报安从进的情况，并建议派兵助朝廷讨伐',11,'荆南行军司马王保义','且请发兵助朝廷讨之；',[('王保义','建议详细上报并派兵助朝廷讨伐'),('高从诲','收到行军司马的建议')],place='荆南',note='这里明确的是建议，不能单凭请发兵就记部队已出发。')
add('gao_accepts_baoyi_advice','高从诲接受王保义上报情况并协助朝廷的建议',11,'从诲从之。','从诲从之。',[('高从诲','接受王保义的建议'),('王保义','提出的建议获接受')],place='荆南',note='接受建议与后来实际出兵分期；本批未提前录入安从进败亡和后续出兵。')
claim('person','person_王保义','biography','《新五代史》记，王保义曾是高季兴的宾客。',11,'梁震、司空薰、王保義等為賓客。','同为荆南人物，与941年行军司马身份相承；具体成为宾客的年份未载，不套本次四月日期。',source='xinwudaishi-069-wang-baoyi')
# This part of paragraph 10 summarizes Li Bian's reign after his accession.
for code in ['ministers_urge_northern_campaign','li_bian_rejects_war','liu_yan_proposes_chu_attack','li_bian_rejects_chu_attack']:
 key=E[code];row=next(x for x in B['events'] if x['key']==key)
 row.update(start_year=None,end_year=None,time_original='李昪即位后，具体年月未载（见941年条）')
 for c in B['claims']:
  if c['subject_key']==key and c['field_path']=='time_original':
   c['claim_text']=row['time_original'];quote=c['note'].split('；核对说明：')[0]
   c['note']=quote+'；核对说明：本段从唐末战乱转入李昪即位后的概述，未明确这次建议、言论或外交提议发生在941年四月，保留未知年。'

reviews={7:'王亚澄父子及王延喜弟弟关系有明文，方向明确；通谋只是王延羲的怀疑，许仁钦实际拘捕与带回另录，归处未载。',8:'陈觉复用南唐主体，万年为常梦锡籍贯，任宣徽副使不混后来的礼部尚书职。',9:'白承福以具名吐谷浑酋长录入；李德珫沿既有别名字形，不与此前未具名部众首领强合，北京非现代北京。',10:'请求借道、拒绝、群臣建议、李昪解释、南汉合攻楚计划与拒绝分别记录。数十年战争概述保留为原文上下文；即位后丰收为人物事实补充，群臣北伐建议及合攻楚提议的具体年月未载，均不强定941年四月。',11:'反叛筹划、使者四月丁亥到成都、后蜀讨论与拒绝、荆南求援及双方书信、王保义建议与高从诲接受分别记录。暗中往来作为新五代史补充异说，不当永久盟友或套同一天；没有提前录入后续实际出兵与败亡。'}
assert not (P/'publication.json').exists()
for n in range(7,12):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=941,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(7,12)],next_paragraph=Q[12]['id'],next_volume=282,next_year=941,supplements=supplements,source_contexts=[dict(paragraph_id=Q[10]['id'],source_key=main_sources[0],text=Q[10]['text'],note='唐末以来数十年战乱及割据形成的概述作为原文上下文保留，不虚构一场941年新事件。')],excluded_non_body=[],coverage='连续第7—11段，原92—96行；四月记载。全年38段，累计11段，剩余27段待录。',source_issues_review='高从诲对安从进求援的态度，通鉴侧重告诫、新史另记暗中往来；分别保留。纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(7,12)],plain_language_review='首次逐条检查新增人物介绍、事件标题与说明、参与角色、关系方向、时间和事实引用；拒绝、计划、怀疑和实际行动区分。旧主体保留线上已有字段，以新增出处补充当前身份，未扩大旧内容改写。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
