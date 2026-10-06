# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 1–10."""
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
COMMIT='3ba4c15f89bc0e4a416ae35be0615a8c443b7f49'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-291-953-end-954-opening']:
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
main_sources = ['tongjian-291-953-end-954-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0954-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-953-end-954-opening':'卷291·广顺三年末至显德元年初及年界','jiuwudaishi-113-january-954':'卷113·太祖本纪四·显德元年正月','jiuwudaishi-113-guowei-death-954':'卷113·太祖本纪四·郭威遗命与去世','jiuwudaishi-114-chairong-accession':'卷114·世宗本纪一·柴荣即位','xinwudaishi-12-chairong-accession':'卷12·周本纪第十二·柴荣即位','songshi-260-caohan-early':'卷260·曹翰传早年'}
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
lines = (ROOT / 'resources/derived/tongjian/291.txt').read_text().splitlines()
for n in range(1, 11):
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if key in prior_source_registry}, []

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
    labels={'tongjian-291-953-end-954-opening':'卷291·广顺三年末至显德元年初及年界','jiuwudaishi-113-january-954':'卷113·太祖本纪四·显德元年正月','jiuwudaishi-113-guowei-death-954':'卷113·太祖本纪四·郭威遗命与去世','jiuwudaishi-114-chairong-accession':'卷114·世宗本纪一·柴荣即位','xinwudaishi-12-chairong-accession':'卷12·周本纪第十二·柴荣即位','songshi-260-caohan-early':'卷260·曹翰传早年'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·显德元年（954年正月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0954_01_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=954, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='954年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0954_' + code
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
        edge = 'participation_zztj_291_0954_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0954_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','荣':'柴荣','王溥':'王溥（后周宋初）'})
NEW_ALIASES={'曹翰':[],'韩通':['韓通'],'周训':['周訓'],'樊爱能':['樊愛能']}
NEW_DESCRIPTIONS={'曹翰':'大名人，曾为郡中小吏，受郭威知遇后随柴荣，任澶州牙将。郭威病中，劝柴荣入宫侍疾，《宋史》还记柴荣让他总理府务。生卒年暂未核定。','韩通':'太原人，后周保义军留后。954年正月正式任保义节度使，《旧五代史》以陕州留后称其前职。生卒年暂未核定。','周训':'前登州刺史。954年正月受命与其他使者处理黄河八处决口。生卒年未载。','樊爱能':'后周马军将领。954年正月获领武定节度使，旧纪同时记其军职与洋州节度职衔。生卒年暂未核定。'}
oldjan='jiuwudaishi-113-january-954';olddeath='jiuwudaishi-113-guowei-death-954';oldaccess='jiuwudaishi-114-chairong-accession';newaccess='xinwudaishi-12-chairong-accession';songcao='songshi-260-caohan-early'
add('guowei_sick_circle_rite','郭威抱病祭圜丘，仅能瞻仰致敬，进爵奠币由有司代行',1,'春，正月，丙子朔，','进爵奠币皆有司代之。',[('帝','抱病祭圜丘，部分仪节由有司代行')],when='954年正月丙子朔',place='大梁圜丘',note='病中有限度参与与完整亲自行遍仪式不同，不把祭祀代行解释为当天已去世。')
sup('guowei_sick_circle_rite',1,oldjan,'時帝郊祀，禦樓受冊，有司多略其禮，以帝不豫故也。','《旧五代史》同记因郭威患病，郊祀及受册礼多有省略。','该书前文概述礼毕，此句明确省礼，保留病中仪式实际范围，不误读为毫无省略。')
add('guowei_amnesty_xiande','郭威颁布大赦，改年号为显德',1,'大赦，改元。','大赦，改元。',[('帝','颁布大赦并改元显德')],when='954年正月丙子朔',place='后周',note='此时仍为郭威，显德改元不错误归为柴荣即位当日。')
sup('guowei_amnesty_xiande',1,oldjan,'大赦天下，改廣順四年為顯德元年。','《旧五代史》明确记改广顺四年为显德元年并大赦。','纪年改称与君主更替分开，不能因显德通常联系世宗就倒换发布者。')
add('shu_border_trade_allowed','后周准许与蜀境通商',1,'听蜀境通商。',None,[('帝','准许蜀境贸易')],when='954年正月丙子朔',place='后周与后蜀边境',note='准通商不是两国全面结盟或军事边界撤销。')
add('yedu_status_abolished','郭威撤销邺都地位，仍保留天雄军',2,'戊寅，',None,[('帝','撤销邺都称号并保留天雄军')],when='954年正月戊寅',place='邺都、天雄军')
sup('yedu_status_abolished',2,oldjan,'戊寅，詔廢鄴都依舊為天雄軍，大名府在京兆府之下。','《旧五代史》同记废邺都、仍为天雄军，并补大名府序位在京兆府下。','都号撤销与撤去全部城池或军镇不同。',relation='adds')
add('rong_controls_armies','郭威加柴荣兼侍中，任其统管内外兵马，朝野稍安',3,'庚辰，',None,[('帝','授柴荣兼侍中及内外兵马事务'),('荣','以晋王身份掌兵，使朝野稍安')],when='954年正月庚辰',place='后周朝廷',note='人心稍安为史书概述，非民意统计；当前晋王尚未即位。')
sup('rong_controls_armies',3,newaccess,'顯德元年正月丙子，郊，僅而成禮，即以王判內外兵馬事。','《新五代史》在正月丙子郊祀概述后紧接记晋王判内外兵马。','该书合叙未单列庚辰，与主书分日记述不同，保留叙事粒度，不能据即字把全部授职改到丙子。',relation='adds',field='time_original')
add('soldiers_complain_ritual_rewards','军士流言称郊祀赏赐比唐明宗时薄',4,'军士有流言','唐明宗时者，',[],when='954年正月壬午以前',place='后周军中',note='这是军士所说，不当作已核实的两朝赏额比较。')
add('guowei_rebukes_generals_rewards','郭威召诸将责问纵容流言，称自己节俭主要为供军，诸将惶恐谢罪',4,'帝闻之，壬午，','皆惶恐谢罪，',[('帝','召诸将说明财政与供军处境并责问流言')],when='954年正月壬午',place='后周寝殿',note='财政解释为郭威当时陈述，不自编账册数额。')
add('rumor_instigators_executed','诸将退下后搜捕挑事者并处死，流言平息',4,'退，',None,[],when='954年正月壬午训诫后',place='后周军中',note='不逞者未具名，不给未载名单；未据流言把全军写成叛乱。')
add('guowei_assigns_cao_to_rong','郭威在邺都时看重曹翰才能，让他跟随柴荣',5,'初，帝在鄴都，','使之事晋王荣。',[('帝','看重曹翰并让他跟随柴荣'),('曹翰','由小吏受郭威知遇后随柴荣')],year=None,when='郭威在邺都时期的回述，具体安排年月未载',place='邺都',note='初引前事，晋王为后称，不能把邺都时已称晋王当作确定当年职衔。')
sup('guowei_assigns_cao_to_rong',5,songcao,'曹翰，大名人。少為郡小吏，好使氣陵人，不為鄉里所譽。乾祐初，周太祖鎮鄴，與語，奇之，以隸世宗帳下。','《宋史》补曹翰籍贯大名，并把郭威镇邺知遇概述在乾祐初。','该传概述时期与主书未列年分开保留；乡里评价为传记所述，不写成无争议终身品德。',relation='adds')
add('cao_becomes_chanzhou_officer','柴荣镇守澶州时任曹翰为牙将',5,'荣镇澶州，','以为牙将。',[('荣','任曹翰为澶州牙将'),('曹翰','获任牙将')],year=None,when='柴荣镇澶州期间、953年入为开封尹以前的回述',place='澶州')
add('cao_advises_rong_attend_sick_guo','曹翰未等召命来到柴荣身边，劝其入宫侍奉病中的郭威，柴荣当天入宫',5,'荣入为开封尹，','即日入止禁中。',[('曹翰','主动来到柴荣身边并劝其入宫侍疾'),('荣','听从建议，当天入宫留侍')],year=None,when='953年柴荣任开封尹后至954年正月郭威病笃以前，具体劝谏日未载',place='开封宫廷',note='即日指劝谏后当天，不因下一句丙戌就把谈话强定丙戌。')
sup('cao_advises_rong_attend_sick_guo',5,songcao,'世宗悟，即入侍，以府事屬翰總決。','《宋史》同记柴荣入宫侍疾，并补他把府务交曹翰总理。','该句世宗是后称，仍为晋王阶段；补府事托付不提前录其即位后官职。',relation='adds')
add('rong_handles_major_affairs','郭威病情严重，停止诸司细务奏报，大事由柴荣请示后执行',5,'丙戌，帝疾笃，',None,[('帝','病笃后停止细务奏报'),('荣','承办大事，请示郭威后执行')],when='954年正月丙戌',place='后周朝廷',note='禀进止为请示后执行，不等同郭威已去世或柴荣已独立即位。')
add('zheng_renhui_privy_chief','郭威任郑仁诲为枢密使，加同平章事',6,'以镇宁节度使郑仁诲',None,[('郑仁诲','由镇宁节度使获任枢密使、同平章事')],when='954年正月丙戌条后，主书未单列日',place='后周朝廷')
sup('zheng_renhui_privy_chief',6,oldjan,'丙戌，以澶州節度使鄭仁誨為樞密使，加同平章事；','《旧五代史》明确将郑仁诲授职记在正月丙戌。','澶州与镇宁军称谓对应同一前职，旧纪为独立日期补证。',relation='adds',field='time_original')
for code,name,office,start,end in [('sun_xingyou_full_commission','孙行友','义武节度使','戊子，以义武留后孙行友','孙行友、'),('han_tong_full_commission','韩通','保义节度使','保义留后韩通','韩通、'),('feng_jiye_full_commission','冯继业','朔方节度使','朔方留后冯继业','皆为节度使。')]:
 add(code,'郭威正式任命'+name+'为'+office,7,'戊子，','皆为节度使。',[(name,'由留后正式获任'+office)],when='954年正月戊子',place=office.replace('节度使','军'),note='皆为节度使承同句诏令，留后与正授区别，未写为第一次接触军府。')
sup('han_tong_full_commission',7,oldjan,'定州留後孫行友、邢州留後田景鹹、陜州留後韓通、靈武留後馮繼業並正授節度使。','《旧五代史》同日列孙行友、田景咸、韩通、冯继业均正授节度使。','主书省略田景咸，旧书作为同批任命补充；韩通的陕州与保义名称分别保留，未给新派任日。',relation='adds')
claim('person',people['韩通'],'description','韩通籍贯太原。',7,'通，太原人也。','太原是本段明载籍贯，不当作保义军治所。')
add('guowei_orders_paper_clothes_pottery','郭威反复嘱柴荣薄葬，死后用纸衣、瓦棺，速葬且以砖代墓中石材',8,'帝屡戒晋王曰：','以甓代之；',[('帝','嘱咐薄葬、速葬及棺衣材质'),('荣','承接郭威薄葬遗命')],when='954年正月病中屡次遗命，具体各次告诫日未载',place='后周宫廷',note='唐陵遭盗为郭威自述解释，葬法为遗命，不写成此日已建陵埋葬。')
add('guowei_orders_paid_burial_labor','郭威要求陵工雇佣给酬，不烦百姓，葬后募三十户免杂徭守陵',8,'工人役徒皆和雇，','使之守视；',[('帝','要求雇工修陵并安排守陵户待遇'),('荣','承接陵工和守陵户安排')],when='954年正月病中遗命',place='后周宫廷、预定陵区',note='三十户为拟募守陵户数，不是当时已确认的人户名册；免杂徭不等于免一切赋税。')
add('guowei_bans_luxurious_tomb_features','郭威禁止修下宫、置守陵宫人和石像，仅留碑说明俭葬遗命',8,'勿修下宫，','吾不福汝！”',[('帝','禁止奢侈墓制并要求碑记俭葬'),('荣','被要求遵从俭葬遗命')],when='954年正月病中遗命',place='后周宫廷、预定陵区',note='下宫为陵寝相关设施，未现代化解释为地下宫殿全部工程；遗命不等于每一条都已有实施审计。')
sup('guowei_bans_luxurious_tomb_features',8,olddeath,'勿修下宮，不要守陵宮人，亦不得用石人石獸，只立一石記子，','《旧五代史》也保存不设守陵宫人、石人石兽，只立碑记的遗命。','引传记正文作为独立文本，不把后世已执行状况从遗命自动推出。')
add('guowei_last_personnel_advice','郭威嘱柴荣给李洪义节钺，并让魏仁浦留在枢密院',8,'又曰：',None,[('帝','给出李洪义与魏仁浦的人事遗命'),('荣','承接两项人事遗命'),('李洪义','被郭威嘱授节钺'),('魏仁浦','被郭威嘱留枢密院')],when='954年正月病中遗命',place='后周宫廷',note='当与、勿离为遗命和建议，不提前记录两人后续授职已经执行。')
add('eight_yellow_river_breaches','黄河此前在灵河、鱼池等八处决口',9,'先是，河决','凡八口。',[],year=None,when='954年正月庚寅修塞令以前的决河概述，起止未载',place='灵河、鱼池、酸枣、阳武、常乐驿、河阴、六明镇、原武',note='八处是原书所列河口，不自行给现代坐标或水深。')
add('zhou_xun_orders_river_repairs','郭威命周训等分赴各处堵塞黄河八口',9,'庚寅，',None,[('帝','分派使者处理八处决口'),('周训','以前登州刺史身份奉命修塞')],when='954年正月庚寅',place='黄河八处决口',note='诏塞与分遣是部署，不写成八口当日全堵完。')
add('wangpu_chancellor_last_decree','郭威催制书任王溥为中书侍郎、同平章事，壬辰听到宣制完毕后称无憾',10,'帝命趣草制，','吾无恨矣！”',[('帝','催任王溥的制书，宣制后表示无憾'),('王溥','由端明殿学士、户部侍郎获任宰相')],when='954年正月壬辰宣制，此前催拟',place='后周宫廷',note='复用后周宋初王溥，与901年同名者分开；无恨是当时语句，不作为后世全部评价。')
sup('wangpu_chancellor_last_decree',10,olddeath,'以端明殿學士、尚書戶部侍郎王溥為中書侍郎、平章事。','《旧五代史》同日也记王溥任中书侍郎、平章事。','旧纪同一壬辰条提供授职印证，其后《东都事略》注文与正文层次分清。')
for code,name,office,start,end in [('wang_rengao_yongxing','王仁镐','永兴节度使','以枢密副使王仁镐','为永兴节度使，'),('li_zhongjin_wuxin','李重进','武信节度使','以殿前都指挥使李重进','领武信节度使，'),('fan_aineng_wuding','樊爱能','武定节度使','马军都指挥使樊爱能','领武定节度使，'),('he_hui_zhaowu','何徽','昭武节度使','步军都指挥使何徽','领昭武节度使。')]:
 add(code,name+'获任'+office,10,start,end,[(name,'获任或兼领'+office)],when='954年正月壬辰',place='后周相关军镇',note='任领职衔不自动等于当天离开禁军实际赴镇；原名与职衔分别保留。')
sup('fan_aineng_wuding',10,olddeath,'以龍捷左廂都指揮使、睦州防禦使樊愛能為侍衛馬軍都指揮使、洋州節度使，加檢校太保；','《旧五代史》同日列樊爱能前职、任侍卫马军都指挥使及洋州节度使。','军名武定与州名洋州分别保留，不将两种职衔名称当新人物或两次异时上任。',relation='adds')
sup('he_hui_zhaowu',10,olddeath,'以虎捷左廂都指揮使、果州防禦使何徽為侍衛步軍都指揮使、利州節度使，加檢校太保；','《旧五代史》同日列何徽前职及步军都指挥使、利州节度使。','主书昭武与旧纪利州称谓分别保留，兼领与禁军职位并行，不编离京时间。',relation='adds')
add('li_zhongjin_bows_rong','郭威托李重进辅佐后事，命他向柴荣行拜礼，以确定君臣名分',10,'重进年长于晋王荣，','以定君臣之分。',[('帝','托李重进以后事并命其拜柴荣'),('李重进','受托后事并向柴荣行拜礼'),('荣','接受李重进拜礼确定继位后的君臣名分')],when='954年正月郭威去世以前',place='后周禁中',note='年长为比较年龄，不推具体生年，也不把两人的表亲关系误称兄弟；此礼不是郭威已退位。')
add('guowei_dies_zide','郭威在滋德殿去世，朝廷暂不公布死讯',10,'是日，','秘不发丧。',[('帝','在滋德殿去世，死讯暂未宣布')],when='954年正月壬辰',place='滋德殿')
sup('guowei_dies_zide',10,olddeath,'是日巳時，帝崩於滋德殿，聖壽五十一。秘不發喪。','《旧五代史》同日补记巳时、年龄五十一，且秘不发丧。','年龄按原书保存，不据虚岁自动反推生年；死亡与公开发丧不是同一步。',relation='adds')
claim('person',people['郭威'],'death_year','郭威于954年正月壬辰在滋德殿去世。',10,span(10,'是日，','秘不发丧。'),'壬辰由本段此前明确纪日承接；人物死亡年有主书及旧纪同日依据，不用年龄反推生年。')
add('guowei_will_announced','朝廷宣布郭威遗制，指定晋王柴荣继位',10,'乙未，','宣遗制。',[],when='954年正月乙未，《通鉴》纪日',place='后周宫廷',note='遗制内容由旧纪全文印证；遗制宣告与次日登位分开。')
sup('guowei_will_announced',10,olddeath,'乙未，遷神柩於萬歲殿，召文武百官班於殿廷，宣遺制：「晉王榮可於柩前即皇帝位，服紀月日一如舊制」云。','《旧五代史》太祖本纪在乙未记迁神柩及宣制，指定晋王荣在柩前即位。','该处把遗制内容与即位连写，世宗本纪另明确丙申；两种记述分别引用，不据一处合叙删去主书记日。',relation='adds')
add('chairong_accession','晋王柴荣即皇帝位',10,'丙申，',None,[('荣','以晋王身份继位为后周皇帝')],when='954年正月丙申',place='后周宫廷')
sup('chairong_accession',10,oldaccess,'丙申，內出太祖遺制：「晉王榮可於柩前即位。」群臣奉帝即皇帝位。','《旧五代史》世宗本纪明确记丙申出遗制、群臣奉柴荣即位。','遗制宣告细节与太祖纪乙未条有所不同，但丙申即位与主书相合，保留本纪层次。')
sup('chairong_accession',10,newaccess,'丙申，發喪，皇帝即位于柩前。','《新五代史》也记丙申发丧、柩前即位。','此处皇帝为柴荣，非郭威复位；发丧与壬辰死亡分开。')

reviews={1:'仍为郭威，病中省礼、大赦显德改元与蜀境通商分别录，不将显德改元归柴荣。',2:'邺都地位撤销与军镇存续区别，旧纪同日大名府序位补证。',3:'兼侍中、判兵马及人心反应为庚辰，旧新合叙不同，不把即以王判强改丙子。',4:'军士赏额流言、郭威壬午责诸将及诸将捕杀挑事者分开，不把流言当真实财务统计。',5:'曹翰受郭知遇、澶州牙将、953至954劝入侍与丙戌大事由柴荣执行分开；宋传大名及府事托付补证，初不强定本年。',6:'郑仁诲任枢密使，旧纪明确丙戌，主书承前未列日，保存补证。',7:'三留后正授分录，旧纪同批含田景咸未当主书原句；韩通太原为籍贯。',8:'薄葬遗命拆棺衣速葬、雇工与守陵户、禁奢墓制及两项人事指示；遗命不提前当执行，唐陵盗掘为郭威自述。',9:'此前八口决河与庚寅分遣修塞分开，不伪写工程当日已完成。',10:'王溥复用后周宋初主体；壬辰末次任职、李拜柴、郭死、乙未遗制及丙申即位分开，旧本纪合叙与世宗纪细日分别保留；俸兵领镇不编赴镇。'}
assert not (P/'publication.json').exists()
for n in range(1,11):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=954,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph=Q[11]['id'],next_volume=291,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷291原81—90行连续十段；954年跨卷291、292共63段，尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)],source_issues_review='君主在丙申柴荣即位处切换，此前帝均郭威；即位和遗制纪日不同本纪保留。史书注文非独立文本，军名州名不同称谓不乱造人物。紙本异文待核。',plain_language_review='首次逐条核对标题、人物、角色、时间地点及事实解释，主语明确；病中礼仪、遗命与执行、临终任命、死亡与发丧、旧事与当前年分别说明。原文保底本。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
