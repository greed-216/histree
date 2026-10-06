# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 291, year 952 paragraphs 41–46."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,47))
COMMIT='1df54f287032ffe638308d6b8b6efe6b4bf86b76'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-291-953-june-december','jiuwudaishi-113-december-953']:
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
main_sources = ['tongjian-291-953-june-december','tongjian-291-953-end-954-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v291-y0953-p041-p046',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-953-june-december':'卷291·广顺三年六月至十二月','tongjian-291-953-end-954-opening':'卷291·广顺三年末至显德元年初及年界','jiuwudaishi-113-december-953':'卷113·太祖本纪四·广顺三年十二月','xinwudaishi-50-wangyin-death':'卷50·杂传第三十八·王殷','songshi-441-xuxuan-shuzhou':'卷441·徐铉传'}
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
for n in range(41, 47):
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
    labels={'tongjian-291-953-june-december':'卷291·广顺三年六月至十二月','tongjian-291-953-end-954-opening':'卷291·广顺三年末至显德元年初及年界','jiuwudaishi-113-december-953':'卷113·太祖本纪四·广顺三年十二月','xinwudaishi-50-wangyin-death':'卷50·杂传第三十八·王殷','songshi-441-xuxuan-shuzhou':'卷441·徐铉传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷291·广顺三年（953年十二月及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_291_0953_05_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=953, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='953年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_291_0953_' + code
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
        edge = 'participation_zztj_291_0953_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_291_0953_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','唐主':'李璟','荣':'柴荣','冯延己':'冯延巳','王殷':'王殷（后汉后周将）'})
NEW_ALIASES={'田敬洙':[],'徐锴':['徐鍇'],'盘崇':['盤崇']}
NEW_DESCRIPTIONS={'田敬洙':'南唐楚州刺史。建议修白水塘灌田充实边地，冯延巳赞成。相关工程后来引发侵扰夺田，白水塘最终未建成。生卒年未载。','徐锴':'徐铉之弟，南唐右拾遗。953年上表反对由冯延鲁巡抚各州，李璟将他贬为校书郎、分司东都。生卒年未载。','盘崇':'道州盘容洞地方首领。953年末条下记其聚众自称盘容州都统，多次进犯郴州、道州。具体族属不按现代民族强定，不与南汉将潘崇彻混同，生卒年未载。'}
olddec='jiuwudaishi-113-december-953';newwang='xinwudaishi-50-wangyin-death';songxu='songshi-441-xuxuan-shuzhou'
add('wangyin_requests_armor','王殷常带数百随从出入，又请求拨给铠甲兵器用于巡逻，郭威犹豫',41,'王殷每出入，','帝难之。',[('王殷','请求拨甲仗巡逻，出入常有数百随从'),('帝','对王殷请求甲仗感到为难')],when='953年十二月王殷留京任巡检后',place='后周京城',note='请求甲仗不等于已获给或已作乱；数百为史書概述随从规模。')
add('guo_detains_wangyin','郭威抱病到滋德殿，王殷入宫问安时被拘捕',41,'壬申，帝力疾','遂执之。',[('帝','抱病到殿并拘捕王殷'),('王殷','入宫问安时被捕')],when='953年十二月壬申，《通鉴》纪日',place='滋德殿',note='主书前述君臣疑忌为背景，不擅添已发现具体谋反证据。')
add('wangyin_falsely_accused_exiled','郭威下制诬称王殷计划在郊祀日作乱，将他流放登州',41,'下制诬殷','流登州，',[('帝','以诬称郊祀谋反的制书流放王殷'),('王殷','被制书指控谋反并流放')],when='953年十二月壬申被捕以后',place='后周京城至登州',note='诬为主书判断，指控不当成王殷真实计划；流放命令与后来出城被杀分开。')
sup('wangyin_falsely_accused_exiled',41,newwang,'是時，太祖臥疾，疑殷有異志，乃力疾御滋德殿，殷入起居，即命執之，削奪在身官爵，長流登州。','《新五代史》同记郭威疑王殷有异志，拘捕后削官流放登州。','该传以怀疑描述，不给无争议谋反事实；不将传记未列日强与主书壬申对齐。')
add('wangyin_killed_after_leaving_city','王殷被押出城后遭杀害',41,'出城，','杀之，',[('王殷','出城后被杀')],when='953年十二月被捕、流放制书下达以后',place='后周京城城外',note='执行者未具名，不写成王殷已抵登州才死亡。')
sup('wangyin_killed_after_leaving_city',41,olddec,'辛未，鄴都留守、侍衛親軍都指揮使王殷削奪在身官爵，長流登州，尋賜死於北郊。','《旧五代史》将削官流放记在十二月辛未，称随后在北郊赐死。','辛未与主书壬申纪日不同，尋表示随后，不硬定死亡和拘捕同日；北郊为旧纪补地点。',relation='conflicts',field='time_original')
add('zheng_sent_to_yedu','郭威命郑仁诲到邺都安抚',41,'命镇宁节度使郑仁诲','诣鄴都安抚。',[('帝','派郑仁诲到邺都安抚'),('郑仁诲','以镇宁节度使身份奉派邺都')],when='953年十二月王殷被杀后',place='邺都')
add('zheng_kills_wangyin_son','郑仁诲贪图王殷家财，擅自杀其子，并将家属迁至登州',41,'仁诲利殷家财，',None,[('郑仁诲','贪图王殷财产，擅杀其子并迁家属')],when='953年十二月郑仁诲赴邺都以后',place='邺都至登州',note='受害儿子未具名，不直接认作已录王承诲；迁家属与朝廷本来的不问罪诏意另作比较。')
sup('zheng_kills_wangyin_son',41,olddec,'其家人骨肉，並不問罪。','《旧五代史》记朝廷对王殷家人骨肉不追究罪责。','这与主書郑仁诲擅杀的行为属于诏意与私行两个层面，不据不问罪推断全部家人事实上都未受害。',relation='adds')
add('xuxuan_pleads_for_examinations','徐铉建议贡举刚设立，不宜骤然废止，南唐恢复贡举',42,'唐祠部朗中、知制诰徐铉',None,[('徐铉','建议保留贡举，建议被采纳而恢复')],when='953年末条下，具体建言与恢复日未载',place='南唐朝廷',note='祠部朗中疑为郎中，展示按通行官名理解，原字不改；不补此前停办贡举的确切日。')
add('tian_requests_baishui_repair','田敬洙请求修白水塘灌溉农田、充实边地，冯延巳认为可行',43,'先是，楚州刺史田敬洙','冯延己以为便。',[('田敬洙','请求修白水塘灌田'),('冯延己','认为兴修有利')],year=None,when='953年末徐铉被贬以前的回述，具体提议年月未载',place='楚州、白水塘',note='请修是建议，不将本句写为工程已经建成。')
add('lideming_proposes_tuntian','李德明随后请求扩荒地作屯田，并修复废弃沟渠池塘',43,'李德明因请','所在渠塘堙废者。',[('李德明','提出扩展屯田与修复渠塘的建议')],year=None,when='田敬洙提议后、953年末徐铉调查前的回述',place='南唐、楚州一带')
add('officials_seize_farmland','官吏借工程侵扰百姓，大兴劳役并夺取大量民田，百姓无处申诉',43,'吏因缘侵扰，','民愁怨无诉。',[],year=None,when='屯田、渠塘工程推进期间，具体起止未载',place='南唐、楚州一带',note='这是实施中已发生的侵扰，不因前句为请求而误写项目从未执行；官吏未具名不指派特定经办者。')
add('li_jing_sends_xuxuan_inspection','徐铉报告屯田侵扰，李璟命他调查',43,'徐铉以白唐主，','唐主命铉按视之，',[('徐铉','报告侵扰并奉命调查'),('唐主','命徐铉调查')],when='953年末条下，屯田侵扰发生以后',place='南唐朝廷至楚州一带')
add('xuxuan_returns_farmland','徐铉登记被夺民田，将其全部归还原主人',43,'铉籍民田', '悉归其主。',[('徐铉','登记民田并归还原主人')],when='953年末条下，受命调查以后',place='南唐、楚州一带',note='悉归其主为主书所记执行，不编归还面积与全部田主名单。')
add('xuxuan_exiled_to_shuzhou','有人诬告徐铉擅权，李璟发怒，将他流放舒州',43,'或谮铉擅作威福，','流铉舒州。',[('徐铉','受诬告后被流放舒州'),('唐主','听到指控后发怒并流放徐铉')],when='953年末条下，归还民田以后',place='南唐至舒州',note='谮为主书对指控的判断，不把擅权写为无争议事实；指控者未具名。')
sup('xuxuan_exiled_to_shuzhou',43,songxu,'鉉至楚州，奏罷屯田，延規等懼，逃罪，鉉捕之急，權近側目。及捕得賊首，即斬之不俟報，坐專殺流舒州。','《宋史》也记徐铉因屯田处置被流放舒州，称他抓到贼首后未经上报即杀，因专杀受罚。','与主书被谮擅权的处分原因不同；该传未列具体年份，按楚州屯田及舒州处分背景并列补证，不强认同一日期，也未提前录后来饶州官职。',relation='conflicts')
add('baishui_project_unfinished','白水塘工程最终没有建成',43,'然白水塘竟不成。',None,[],year=None,when='相关工程与徐铉处分以后的结果概述，具体终止年月未载',place='白水塘',note='竟不成为最后结果，不反推此前没有兴役或夺田。')
add('feng_yanlu_inspects_prefectures','李璟命冯延鲁巡抚各州',44,'唐主又命少府监冯延鲁','巡抚诸州，',[('唐主','派冯延鲁巡抚各州'),('冯延鲁','以少府监身份奉命巡抚')],when='953年末条下，具体派遣日未载',place='南唐诸州')
add('xukai_objects_feng_mission','徐锴上表称冯延鲁无才多罪、不宜奉使，反对派他巡抚',44,'右拾遗徐锴','不宜奉使。',[('徐锴','以右拾遗身份上表反对派冯延鲁'),('冯延鲁','被徐锴批评不适合奉使')],when='953年末李璟派冯延鲁以后',place='南唐朝廷',note='无才多罪为徐锴奏表评价，不写成本站已核全部犯罪清单。')
add('xukai_demoted','李璟因徐锴反对派冯延鲁而发怒，贬他为校书郎、分司东都',44,'唐主怒，','分司东都。',[('唐主','贬徐锴并令分司东都'),('徐锴','被贬校书郎、分司东都')],when='953年末徐锴上表以后',place='南唐东都',note='东都保留当时名称，不直接映射为后周洛阳或南唐金陵。')
relationship('徐铉','徐锴','兄长',44,'锴，铉之弟也。','主书明言徐锴为徐铉弟，方向为徐铉是徐锴的兄长，不将共同任职当作结义。')
add('pan_chong_claims_command','盘崇聚众，自称盘容州都统',45,'道州盘容洞蛮酋盘崇','自称盘容州都统，',[('盘崇','聚众并自称盘容州都统')],when='953年末条下，具体自称日未载',place='道州盘容洞',note='自称不等于后周朝廷正式任命；原族称不映射现代族名。')
add('pan_chong_raids_chen_dao','盘崇所聚部众多次进犯郴州、道州',45,'屡寇郴、道州。',None,[('盘崇','所聚部众多次进犯郴道')],when='953年末条下，屡次进犯的具体起止未载',place='郴州、道州',note='屡寇是多次行为概述，不造同一天的单一战役或未记死伤。')
add('guowei_temple_rite_interrupted','郭威抱病到太庙祭享，近臣扶他登阶，只行一室礼后退下，命柴荣完成仪式',46,'乙亥，','命晋王荣终礼。',[('帝','抱病祭庙，不能完成礼仪而让柴荣代终'),('荣','以晋王身份完成太庙礼仪')],when='953年十二月乙亥',place='大梁太庙',note='被兗冕疑为袞冕衣冠写法，展示用祭礼服饰，不改原字；酌献后不能拜而退不同于已经完整行遍各室。')
sup('guowei_temple_rite_interrupted',46,olddec,'乙亥質明，帝親饗太廟，自齋宮乘步輦至廟庭，被袞冕，令近臣翼侍升階，止及一室行禮，俯首而退，餘命晉王率有司終其禮。','《旧五代史》同日详细记郭威乘步辇到庙庭、扶登阶，仅行一室礼，余由晋王率有司完成。','此处原作袞冕与主本兗冕差异保留；副拜不能行不是已经死亡或即位移交。',relation='adds')
add('guowei_illness_worsens_at_suburb','郭威当晚住在南郊，病情一度危重，半夜略有好转',46,'是夕，',None,[('帝','宿南郊时病势危急，半夜稍缓')],when='953年十二月乙亥夜',place='大梁南郊',note='几不救是危重近不能救，未作当晚死亡；次日已跨954年，另从新年首段继续。')

reviews={41:'甲仗请求、被捕、诬制流放、出城被杀、郑赴邺都及私杀迁家分开。旧纪辛未与主壬申并列，朝廷不问家属罪与郑私行区别，未具名子不硬认王承诲。',42:'徐铉建言与恢复贡举合为有因果的行动，祠部朗中官字疑作郎保底本，不补初设及废停的未知日期。',43:'先是水利屯田建议与实施侵扰、徐报告受命、归田、处分及工程不成分开；宋传专杀原因独立保存，不压为主谮言的同义理由。',44:'冯延鲁出使、徐锴批评与贬职分录，兄弟方向明确；东都不乱配洛阳。',45:'自称职与多次进犯分别记，盘崇与潘崇彻不凭近音合并，不猜现代族属。',46:'乙亥庙礼途中退下、柴荣终礼与当夜病重稍愈分开；明日跨954。旧纪同日翼扶印证，服饰字形异读保存。'}
assert not (P/'publication.json').exists()
for n in range(41,47):
 assert ledger[n-1]['status'] in ('pending','reviewed');ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=291,year=953,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(41,47)],next_paragraph='zztj-v291-y0954-p001',next_volume=291,next_year=954,supplements=supplements,excluded_non_body=[],coverage='卷291原73—78行连续六段，953年末；须核验全年46段、发布哈希与954跨卷范围后标全年完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(41,47)],source_issues_review='王殷拘捕纪日、朝令与擅行、徐铉处分原因等书间差异保留；未具名王殷子不强认承诲，兗冕、朗中等原字保留，纸本异文待核。',plain_language_review='首次逐条检查展示标题、人物、角色、关系方向和事实解释；主语明确，指控与事实、建议与执行、危重与死亡、当年与跨年分清；引用原字不改。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
