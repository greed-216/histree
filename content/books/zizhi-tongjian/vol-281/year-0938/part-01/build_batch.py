# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,43))
specs=[(d.name,d,'b5136a33bd66e49c58489b48336695f7b1236b9b','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-min-and-year-end','xinwudaishi-062-accession']:
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
main_sources = ['tongjian-281-937-min-and-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0938-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-077-january':'卷77·晋高祖纪·天福三年正月','jiuwudaishi-077-february':'卷77·晋高祖纪·天福三年二月'}
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
lines = (ROOT / 'resources/derived/tongjian/281.txt').read_text().splitlines()
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
    labels={'jiuwudaishi-077-january':'卷77·晋高祖纪·天福三年正月','jiuwudaishi-077-february':'卷77·晋高祖纪·天福三年二月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月条下' if n<5 else '二月条下含未定月的后续记载' if n==5 else '三月条下含追叙' if n<8 else '四月条下'
        citation = f'卷281·后晋天福三年（938；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0938_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'张允':'后晋左散骑常侍。938年二月庚辰向石敬瑭提交《驳赦论》，质疑以大赦消除天灾的做法，得到诏书褒奖。',
'梁文矩':'后晋官员。石敬瑭命他与另外九人设立详定院，审核百官提交的密封奏章，具体设院年月未载。',
'李详（后晋中书舍人）':'后晋中书舍人。938年上疏批评地方荐官过多、名位混乱，提出限制荐官范围和人数，石敬瑭采纳了建议。'}
NEW_ALIASES={'张允':['張允'],'梁文矩':[],'李详（后晋中书舍人）':['李详','李詳']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=938 if name in ['武彦和','王氏（守卫军使王宏之子）'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=938, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='938年正月，具体日期未记载' if n<5 else '938年三月，具体日期未记载'
    key = 'event_zztj_281_0938_' + code
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
        edge = 'participation_zztj_281_0938_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_281_0938_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'唐主':'李昪','蜀主':'孟昶','帝':'石敬瑭','景遂':'徐景遂','李详':'李详（后晋中书舍人）'})
add('january_eclipse','《资治通鉴》记正月己酉发生日食',1,'春，',None,[],when='938年正月己酉',description='《资治通鉴》记正月己酉发生日食。《旧五代史》同日记太史先奏日食，但届时“不亏”，两书记载不同。',note='只录史载，不据电子本计算天文食分或现代公历日期。')
sup('january_eclipse',1,'jiuwudaishi-077-january','己酉，百官守司，以太史先奏日蝕故也。至是不虧，內外稱賀。','《旧五代史》记正月己酉因太史先预报日食，百官守在官署，但届时不亏，朝内外称贺。','不亏与《资治通鉴》有食不同，作为独立异说；不把预报直接等同实际观测。',relation='conflicts')
add('zhou_ben_dies','周本因未能保全吴国而惭愧怨恨，随后去世',2,'唐德胜',None,[('周本','在南唐任德胜节度使兼中书令，以未能保全吴国为憾而去世')],note='以不能存吴愧恨为史书所述心情和原因，不另作医学死因。西平恭烈王是史书称谓，不据此补当日封爵或谥号日期。')
sup('zhou_ben_dies',2,'xinwudaishi-062-accession',source_span('xinwudaishi-062-accession','周本與諸將至金陵勸進，','憤惋而死。'),'《新五代史》记周本劝进后自责未能报答杨氏，愤恨而死。','该书把死亡与受禅后感慨相接，没有独列正月死日；不因此硬定他在937年十月已经死亡。',relation='adds')
claim('person',people['周本'],'death_year','《资治通鉴》将周本去世列于938年正月条下。',2,Q[2]['text'],'据主书所在年份补死亡事实，具体日未载；已有主体和旧档案不覆写。')
add('jing_sui_shangshu_department','徐景遂被任命参判尚书都省',3,'丙寅，',None,[('唐主','任命侍中、吉王徐景遂参判尚书都省'),('景遂','被任命参与主持尚书都省事务')],when='938年正月丙寅',note='侍中、吉王是此前身份，参判尚书都省是本次任命，不重复新建此前的封爵。')
add('zhang_ye_shu_appointments','孟昶任命张业为左仆射等职并兼枢密使',4,'蜀主以','同平章事、枢密使，',[('蜀主','任命张业为左仆射兼中书侍郎、同平章事、枢密使'),('张业','由武信节度使、同平章事获任左仆射等职并兼枢密使')],place='蜀国',note='原任武信节度使、同平章事与新任官衔分开，不把整组官衔当本日全部首次授予。检索新五代史蜀世家未见本次完整同日官衔，不把邻近其他年份任官作直接印证。')
add('wang_chuhui_wuxin','王处回兼任武信节度使、同平章事',4,'武泰节度使',None,[('蜀主','让王处回兼任武信节度使、同平章事'),('王处回','在任武泰节度使的基础上兼武信节度使、同平章事')],place='蜀国、武泰军与武信军',note='兼表示保留原职基础上的兼任，不误记已经卸任武泰。具体日未载，不套上句南唐丙寅。')
add('zhang_yun_refutes_amnesty','张允提交《驳赦论》，质疑用大赦消除天灾',5,'二月，庚辰，','非所以弭灾也。”',[('张允','以左散骑常侍身份提交《驳赦论》'),('帝','收到张允关于大赦与天灾的议论')],when='938年二月庚辰',description='张允提交《驳赦论》，认为大赦可能让有罪者幸免、使受害者含冤，因此未必能够消除天灾。',note='天灾因冤气而起是张允的政治议论，不作为网站认可的自然科学因果；两名囚犯是假设，不新建具体囚犯或案件。')
sup('zhang_yun_refutes_amnesty',5,'jiuwudaishi-077-february','二月庚辰，左散騎常侍張允進《駁赦論》。','《旧五代史》也记二月庚辰张允以左散骑常侍身份提交《驳赦论》。','书名、作者、官职和纪日对应。')
add('shi_praises_zhang_yun','石敬瑭下诏褒奖张允',5,'二月，庚辰，','诏褒之。',[('帝','对张允的《驳赦论》下诏褒奖'),('张允','因提交《驳赦论》受到诏书褒奖')],when='938年二月庚辰条下',note='褒奖不等于同时赐官升迁，也不把大赦制度已完全废除作为结果。')
sup('shi_praises_zhang_yun',5,'jiuwudaishi-077-february','帝覽而嘉之，降詔獎飾，仍付史館。','《旧五代史》补记石敬瑭阅后称赞张允，下诏褒奖，并把论著交给史馆。','交史馆是该书补充的实际安排，与《资治通鉴》诏褒之连接同一事件。',relation='adds')
add('shi_requests_sealed_memorials','石敬瑭要求百官各提交密封奏章',5,'帝乐闻','诏百官各上封事，',[('帝','要求百官各自提交密封奏章')],year=None,when='《资治通鉴》二月条后概述，求封事原诏确切年月未明',description='石敬瑭愿意听取直言，要求百官各提交密封奏章。',note='封事是密封奏章，不译成官爵封赏；与同段庚辰褒奖相邻不等于所有后续命令都在庚辰。')
add('liang_wenju_reviews_memorials','石敬瑭命梁文矩等十人设详定院，审核奏章',5,'命使部尚书','可者行之。',[('帝','命梁文矩等十人设详定院审核奏章'),('梁文矩','与另外九人审核百官奏章，无可采用者留中，可采用者实行')],year=None,when='求百官封事的安排，具体设院年月未明',description='石敬瑭命梁文矩等十人设立详定院，审核百官奏章；没有可采用意见的留在宫中，有可采用意见的实行。',note='电子本使部尚书官名疑讹，保留摘录，展示只称姓名和审核职掌，未据疑字新增使部机构；十人含梁文矩，不补另九人姓名。')
add('shi_urges_memorial_submission','百官上书者不足十人，石敬瑭再次亲笔诏书催促',5,'数月，',None,[('帝','因应诏上书者不足十人而再次亲笔诏书催促')],year=None,when='求百官封事诏后数月的乙未，确切年月未明',description='数月后，应诏上书的人仍不足十人。石敬瑭在乙未再次发出亲笔诏书催促。',note='都无十人是未满十人，不是一个都没有；数月不能直接硬定二月乙未，另列旧本纪的月份定位。')
sup('shi_urges_memorial_submission',5,'jiuwudaishi-077-february',source_span('jiuwudaishi-077-february','乙未，御劄曰：','誰之責也。」'),'《旧五代史》将催上封事的乙未御札列在二月条下，诏书也称下令已过数月、到者未及十人。','《资治通鉴》在数月后记乙未，原始诏令可能早于此段叙述位置；保留两书定位，不从史文排序擅造唯一诏令起日。',relation='conflicts',field='time_original')
add('shi_bans_copper_utensils','石敬瑭禁止民间制作铜器',6,'三月，丁丑，','敕禁民作铜器。',[('帝','下令禁止民间制作铜器')],when='938年三月丁丑',note='禁制铜器不等于禁止铸钱，后续铸币政策另按以后段落处理。')
add('minting_declines_after_wars','战乱后铸钱作坊废弃，铜钱逐渐减少',6,'初，','钱日益耗，',[],year=None,when='唐代以来及战乱后的背景，起止年份未载',description='《资治通鉴》追述唐代曾有三十六处铸钱作坊，战乱以来这些作坊全部废弃，铜钱日益减少。',note='三十六冶是追述的唐代数量，不写成938年仍有三十六处运行，更不倒算废弃起年。')
add('people_melt_coins','民间熔化铜钱制成铜器，朝廷因此下禁令',6,'民多销钱',None,[('帝','因民间熔钱制作铜器的现象而下禁令')],year=None,when='938年三月禁制铜器之前，现象持续起止未载',description='民间多有熔化铜钱制作铜器的情况，《资治通鉴》将它列为朝廷下禁令的原因。',note='主文明示故禁之，可关联原因；不补熔钱人数、数量或未经证实的交易价格。')
add('li_xiang_limits_recommendations','李详建议限制地方荐官范围和人数',7,'中书舍人',None,[('李详','以中书舍人身份建议限制地方荐官范围和人数'),('帝','收到李详的荐官制度建议并采纳')],description='李详批评地方荐官过多，连吏员、优伶、奴仆初次受任也可能得到高阶和服饰。他建议在领兵将校之外，节度州只许推荐硃记大将以上十人，其他州只许推荐都押牙、都虞候、孔目官；其余由本道调整职名。石敬瑭采纳了建议。',note='十年以来是李详的背景概述，不倒算精确开始年；硃记大将保留史载职名，不造人名；建议获采纳不等于全部执行结果已核。')
add('song_qiqiu_seeks_participation','宋齐丘要求参与政务，徐诰以省署未备作答',8,'夏，',None,[('宋齐丘','陈述丞相不应不参与政务'),('唐主','以省署尚未完备为由回答')],when='938年四月甲申',description='宋齐丘认为自己身为丞相，不应被排除在政务之外。徐诰回答说省署尚未完备。',note='皇帝回答是所给理由，不推出宋齐丘当日已经恢复全部实权，也不宣称该理由已由独立史料证实。')
for name,n,quote in [('张允',5,span(5,'二月，庚辰，','诏褒之。')),('梁文矩',5,span(5,'命使部尚书','可者行之。')),('李详（后晋中书舍人）',7,Q[7]['text'])]:
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,quote,'简介只用本段明确职务和行动；未记家世、生卒不补，官名疑字另注。')
reviews={1:'主书有食与旧本纪太史预报、届时不亏保留不同；不据预报宣称实测日食。',2:'周本死列938正月，未记日。新五代史受禅后愤惋死为未列死日概述，不硬归937十月；旧主体补死亡引用，不覆写档案。',3:'正月丙寅景遂参判尚书都省，新职与此前侍中吉王身份区别。',4:'张业和王处回分别任官，前职与兼职保留；蜀事不套南唐丙寅，未见直接同次官衔补证不拼邻年史文。',5:'张允假设囚犯与天灾议论归说话者；褒奖和付史馆、求密封奏章、梁等十人设院、数月乙未催促分开。使部疑官名仅保原字不造机构。不足十人不是零；数月后乙未与旧本纪二月乙未并列，求封事与设院起日未明留null。',6:'三月丁丑禁铜器与唐代铸钱三十六冶、战乱废弃及熔钱现象分录，追叙起止未知留null；制铜器与铸币区分。',7:'李详批评与建议并采纳写清，十年背景不倒算；限制对象、范围和人数按原文，不造已彻底解决滥授的结论。',8:'四月甲申宋请求参与、李昪答省署未备，不推当日权力恢复。'}
assert not (P/'publication.json').exists()
for n in range(1,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=938,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=281,next_year=938,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第1—8段，原文件67—74行；正月至四月及未定日期的追叙和后续，938年未完成。',source_issues_review='年首67行前66行年题已核。全部引用逐字回查。日食与不亏、乙未催奏月份不同保留；使部尚书疑字只保原文不另建机构；新五代史周本死不强定受禅当月。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],plain_language_review='首次逐条自查标题、简介、角色、事件和事实解释，议论归说话者、追叙和后续不硬定日期、引用原字保留。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
