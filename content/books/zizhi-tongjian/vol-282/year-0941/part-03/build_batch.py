# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 941 paragraphs 12–15."""
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
specs=[(d.name,d,'a7c62fad39b7b2dadda562d9e710f8d8f62f5bdf','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
prior=next(x for f in (ROOT/'content').rglob('content-batch.json') for x in json.loads(f.read_text())['sources'] if x['key']=='tongjian-282-941-spring')
commit,relative=prior['url'].split('/blob/')[1].split('/',1)
specs.append((prior['key'],(ROOT/relative).parent,commit,prior['author']))

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
main_sources = ['tongjian-282-941-spring','tongjian-282-941-summer-autumn','tongjian-282-941-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0941-p012-p015',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-282-941-summer-autumn':'卷282·天福六年六月','tongjian-282-941-autumn':'卷282·天福六年七月至九月','jiuwudaishi-098-an-envoys':'卷98·安重荣传·侵辱契丹使者','jiuwudaishi-098-an-memorial':'卷98·安重荣传·奏表','xinwudaishi-051-an-memorial':'卷51·安重荣传·奏表','xinwudaishi-068-min-finance':'卷68·闽世家·黄峻进谏与陈匡范财政','jiuwudaishi-089-sang-reply':'卷89·桑维翰传·石敬瑭答复'}
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
for n in range(12, 16):
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
    labels={'tongjian-282-941-summer-autumn':'卷282·天福六年六月','tongjian-282-941-autumn':'卷282·天福六年七月至九月','jiuwudaishi-098-an-envoys':'卷98·安重荣传·侵辱契丹使者','jiuwudaishi-098-an-memorial':'卷98·安重荣传·奏表','xinwudaishi-051-an-memorial':'卷51·安重荣传·奏表','xinwudaishi-068-min-finance':'卷68·闽世家·黄峻进谏与陈匡范财政','jiuwudaishi-089-sang-reply':'卷89·桑维翰传·石敬瑭答复'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '六月条下' if n<=13 else '七月条下'
        citation = f'卷282·后晋天福六年（941；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0941_03_{len(B["claims"])+1:04d}'
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
    if when is None:when='941年'+('六月' if n<=13 else '七月')+'条下，具体日期未载'
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






ALIASES.update({'唐主':'李昪','蜀主':'孟昶','曦':'王延羲','赵崇':'赵崇（朔州节度副使）','拽剌':'拽剌（941年契丹使者）','匡范':'陈匡范'})
NEW_DESCRIPTIONS={
'拽剌（941年契丹使者）':'契丹使者。941年六月戊午被成德节度使安重荣拘捕。暂未确认他是否与早期记载中获名原知感的荝剌为同一人，使用身份限定主体，等待校核。生卒年未载。',
'赵崇（朔州节度副使）':'朔州节度副使。941年安重荣的奏表声称赵崇驱逐契丹节度使刘山、请求归附后晋；新旧五代史表文写作杀刘山。各说保留，不与905年已遇害的唐朝官员赵崇合并。生卒年未载。',
'刘山':'安重荣941年奏表中的朔州契丹节度使。资治通鉴表文记赵崇驱逐刘山，新旧五代史表文记赵崇杀刘山；保留分别引用，不据奏报裁定确切死亡年。生卒年待核。',
'赫连公德':'吐谷浑首领。《旧五代史》所载安重荣奏表称，赫连公德与白承福等率本族部众从应州归来；新五代史对应表文写赫連功德，姓名异说保留，尚未登记功德为正式别名。生卒年未载。',
'杨沂丰':'闽国官员，曾任王继业治汀州时的士曹参军，与王继业交好，后任司徒兼门下侍郎、同平章事。资治通鉴记他被告与王继业串通，在宴席上被捕，次日被斩并遭灭族，时年八十多岁；具体年月未载。杨涉的族弟，原文称从弟，具体支系未载。',
'黄峻':'闽国谏议大夫。王延羲接连诛杀宗族旧臣后，黄峻抬着棺材到朝堂极力劝谏，被贬为漳州司户。新五代史也记此事，记职名为司户参军。具体年月及生卒年未载。',
'陈匡范':'闽国国计使。四部丛刊本电子转录记为南安人，原电子底本此处写国安，地名字形经同书版本校读，影印及纸本待核。向王延羲提出每日进献万金，获加礼部侍郎，并提高商人税额；收入不足后借款补足，忧惧而死，后被王延羲毁棺毁尸。通鉴记借诸省务钱，新五代史记借于民，分别保留。具体年月及生卒年未确定。',
'黄绍颇':'闽国官员，连江人。陈匡范借款补额一事暴露后，王延羲任黄绍颇为国计使。黄绍颇建议对不属荫补的求官者按条件收钱授官，王延羲接受。具体年月和生卒年未载。'}
NEW_ALIASES={'拽剌（941年契丹使者）':['拽剌'],'赵崇（朔州节度副使）':['趙崇'],'刘山':['劉山'],'赫连公德':['赫連公德'],'杨沂丰':['楊沂豐'],'黄峻':['黃峻'],'陈匡范':['陳匡範','陈匡範'],'黄绍颇':['黃紹頗']}
old='jiuwudaishi-098-an-memorial';new='xinwudaishi-051-an-memorial';minbook='xinwudaishi-068-min-finance'
add('an_insults_envoys','安重荣此前多次轻慢辱骂契丹使者',12,'成德节度使安重荣','箕踞慢骂，',[('安重荣','轻慢辱骂经过其辖境的契丹使者')],year=None,when='941年六月拘捕拽剌以前，具体年月未载',note='此前反复发生的行为未载起年，不把箕踞慢骂强定六月戊午。')
add('an_kills_envoys','安重荣此前曾暗中派人杀死经过辖境的契丹使者',12,'使过其境，','或潜遣人杀之；',[('安重荣','暗中派人杀死契丹使者')],year=None,when='941年六月以前，具体年月未载',note='使者未具名；不把此事同已具名的拽剌拘捕混为杀拽剌。')
sup('an_kills_envoys',12,'jiuwudaishi-098-an-envoys','會有美棱數十騎由其境內，交言不遜，因盡殺之，契丹主大怒，責讓朝廷。','《旧五代史》补记，数十骑契丹美棱经过安重荣辖境，言语冲突后被尽数杀害，契丹主向后晋朝廷责问。','美棱按底本保留，职称字形及具体人数待核；不把数十骑套给被捕的拽剌。',relation='adds')
add('khitan_rebukes_envoy_killings','契丹因安重荣侵害使者，向石敬瑭责问',12,'契丹以让帝，','契丹以让帝，',[('帝','因安重荣侵害使者受到契丹责问')],year=None,when='941年六月以前，具体年月未载')
add('shi_apologizes_for_an','石敬瑭因安重荣侵害使者，向契丹谦辞赔礼',12,'帝为之逊谢。','帝为之逊谢。',[('帝','向契丹谦辞赔礼')],year=None,when='941年六月以前，具体年月未载')
add('an_seizes_zhuaila','安重荣拘捕契丹使者拽剌',12,'六月，戊午，','重荣执契丹使拽剌，',[('安重荣','拘捕契丹使者'),('拽剌','作为契丹使者被拘捕')],when='941年六月戊午',place='成德军')
sup('an_seizes_zhuaila',12,new,'天福六年夏，契丹使者拽剌過鎮，重榮侵辱之，拽剌言不遜，重榮怒，執拽剌，','《新五代史》记，拽剌经过镇州，被安重荣侵辱，言语冲突后被拘捕。','具体冲突经过由传记补充；夏与主书六月相容，不自行换算日期。',relation='adds')
add('an_raids_youzhou','安重荣派骑兵掠夺幽州南部边境',12,'遣骑掠','幽州南境，',[('安重荣','派骑兵掠夺幽州南部边境')],when='941年六月戊午条下',place='幽州南境')
add('an_stations_boye','安重荣在博野驻军',12,'军于博野，','军于博野，',[('安重荣','在博野驻军')],when='941年六月戊午条下',place='博野',note='主书军于博野与新史掠边民而处博野表述不同，分别保留。')
sup('an_stations_boye',12,new,'以輕騎掠幽州南境之民，處之博野。','《新五代史》记，安重荣以轻骑掠取幽州南境的百姓，将他们安置在博野。','主书记在博野驻军，传记记安置被掠百姓；不合并为完全相同的动作，也不补被掠人数。',relation='adds')
add('an_reports_tribal_defections','安重荣上表声称各部归附，愿出十万兵共同攻击契丹',12,'上表称：','与晋共击契丹。',[('安重荣','上表声称各部归附，并愿共同攻击契丹')],when='941年六月戊午条下',description='安重荣上表称，吐谷浑、两突厥、浑、契苾、沙陀等部率众归附，党项等也送来契丹授予的官告职牒。据其转述，各部不满契丹压迫，担忧秋季南侵失败后家族灭亡，愿自备十万兵，与后晋共同攻击契丹。',note='归附规模、压迫说法、契丹准备南侵及十万人皆为奏表中的报告与意愿，不记成独立查实的兵力或已经开战。')
sup('an_reports_tribal_defections',12,old,'臣昨據熟吐渾節度使白承福、赫連公德等，各領本族三萬餘帳，自應州地界奔歸王化。','《旧五代史》表文补列白承福、赫连公德，称各领本族三万多帐从应州归来。','这是表文声称的部众规模，帐不换算成人数，旧史各领与新史合述领本族措辞分别保留。',relation='adds')
person('赫连公德',12,'被旧五代史表文列为与白承福等率众归来的吐谷浑首领','臣昨據熟吐渾節度使白承福、赫連公德等，各領本族三萬餘帳，自應州地界奔歸王化。',source=old)
claim('person',people['赫连公德'],'biography','《新五代史》对应表文写赫连功德，与旧史赫连公德的姓名字形有差异，尚待校核。',12,'臣昨據熟吐渾白承福、赫連功德等領本族三萬餘帳自應州來奔，','同次表文的人名差异保留，暂不把功德登记为已经核实的别名。',source=new,relation='conflicts')
claim('person',person('白承福',12,'被旧五代史表文列为率吐谷浑部众归来的首领','臣昨據熟吐渾節度使白承福、赫連公德等，各領本族三萬餘帳，自應州地界奔歸王化。',source=old),'biography','《旧五代史》安重荣表文称白承福等率吐谷浑部众从应州归来。',12,'臣昨據熟吐渾節度使白承福、赫連公德等，各領本族三萬餘帳，自應州地界奔歸王化。','沿已录941年入朝的白承福主体，保留表文声称及原文字形。',source=old)
add('an_reports_zhao_chong','安重荣奏报赵崇驱逐刘山，并请求归附后晋',12,'又朔州节度副使','臣相继以闻。',[('安重荣','奏报朔州归附的消息'),('赵崇','在奏报中被记为驱逐刘山并请求归附'),('刘山','在奏报中被记为遭赵崇驱逐的契丹节度使')],when='941年六月戊午条下，所报行动具体日期未载',place='朔州',note='事件为奏报，驱逐与归附是奏报内容；与已死唐朝宰相赵崇分开，不按同名复用。')
sup('an_reports_zhao_chong',12,old,'續又朔州節度副使趙崇與本城將校殺偽節度使劉山，尋已安撫軍城，乞歸朝廷。','《旧五代史》表文写赵崇与本城将校杀刘山、安抚军城并请求归附朝廷。','主书表文为逐，旧史及新史表文为杀；并列引用，未独立查实刘山死讯，死亡年保留未知。',relation='conflicts')
sup('an_reports_zhao_chong',12,new,'又據朔州節度副使趙崇殺節度使劉山，以城來歸。','《新五代史》表文同样写赵崇杀刘山、以城归附。','两传记都保留表文语气，与主书驱逐说法并列，不因文字相同就裁定唯一事实。',relation='conflicts')
add('an_urges_war','安重荣上表要求石敬瑭改变对契丹的政策，尽早决定出兵',12,'陛下屡敕臣','愿早决计。”',[('安重荣','要求改变对契丹的政策并决计出兵'),('帝','收到要求改变政策的奏表')],when='941年六月戊午条下',note='陷于契丹的节度使盼王师属于安重荣的劝说，不能当作他们具名发来的请援。')
add('an_sends_war_letters','安重荣向朝廷官员及各藩镇发信，声称已整军并将与契丹决战',12,'又以此意','必与契丹决战。',[('安重荣','向朝廷官员及藩镇传播出兵主张')],when='941年六月条下，具体日期未载',note='云已勒兵为信中声称；必决战是表态，不记成已经发生会战。')
add('shi_worries_about_an','石敬瑭因安重荣掌握强兵、难以控制而忧虑',12,'帝以重荣',None,[('帝','忧虑难以控制安重荣'),('安重荣','掌握强兵，使朝廷难以控制')],note='主书记皇帝忧虑，不提前记作镇压已开始。')
add('sang_urges_restraint','桑维翰秘密上疏，反对接受安重荣攻击契丹的主张',13,'泰宁节度使桑维翰','不可听也。',[('桑维翰','秘密上疏反对攻击契丹的主张')],description='桑维翰担心安重荣已在筹划反叛，也担心朝廷难以拒绝他的意见，秘密上疏劝石敬瑭不要接受攻击契丹的主张。',note='本段刘知远在大梁是现状，不重复建立一次入朝事件；反对政策来自桑维翰奏疏。')
claim('event',E['sang_urges_restraint'],'description','桑维翰认为契丹兵马精强、内部和睦，后晋新败，暂不能与之为敌。',13,span(13,'臣窃观契丹','其势相去甚远。'),'这是桑维翰对敌我实力的判断，不替史书保证契丹每战必胜。')
claim('event',E['sang_urges_restraint'],'description','桑维翰担心断绝和约后需要守边，少兵不足抵御，多兵难以持续运输粮食。',13,span(13,'又，和亲既绝','馈运无以继之。'),'守边与断粮是对决裂后形势的推测，不作为已经发生的军队断粮。')
claim('event',E['sang_urges_restraint'],'description','桑维翰认为频繁战争比输送缯帛更耗财力，也可能让武将与地方藩镇更难控制。',13,span(13,'议者以岁输缯帛','屈辱孰大焉！'),'保存奏疏中的比较与判断，不当成另一次已经发生的财政灾难。')
add('sang_advises_recovery','桑维翰建议发展农业、训练军队、让百姓休养，再等待时机',13,'臣愿陛下训农','则动必有成矣。',[('桑维翰','建议恢复民力与军备后再择机行动')],note='这是建议，不把训农习战写成此日已完成的政绩。')
add('sang_advises_ye_visit','桑维翰建议石敬瑭巡视邺都，以防军府空虚招致异谋',13,'又，鄴都富盛','以杜奸谋。”',[('桑维翰','建议皇帝巡视邺都')],place='邺都',note='巡视为请求，石敬瑭实际北行在后续段落处理。')
add('shi_accepts_sang_counsel','石敬瑭告诉使者，桑维翰的奏疏使自己如醉初醒',13,'帝谓使者曰：','卿勿以为忧。”',[('帝','向使者表示接受桑维翰的劝告')],description='石敬瑭告诉送来奏疏的使者，自己近日烦闷犹豫，读了桑维翰的奏疏如醉初醒，让桑维翰不必忧虑。',note='使者未具名，不建立人物；原文是皇帝回应奏疏，不补实际出兵命令。')
sup('shi_accepts_sang_counsel',13,'jiuwudaishi-089-sang-reply','疏奏，留中不出。高祖召使人於內寢，傳密旨於維翰曰：','《旧五代史》还记桑维翰奏疏留中不公开，石敬瑭在内寝召使者，向桑维翰传达密旨。','主书与传记都记通过使者回应；留中不出及内寝为传记补充，不改原文。',relation='adds')
add('xi_kills_jiye','王延羲召回王继业，在郊外赐死，并杀王继业之子',13,'闽王曦闻','杀其子于泉州。',[('曦','因听说王延政招揽王继业而召回赐死'),('王继业','被召回并在郊外赐死'),('王延政','被王延羲听说曾致书招揽王继业')],place='闽国郊外、泉州',description='王延羲听说王延政写信招揽泉州刺史王继业，召王继业返回，在郊外赐死，又在泉州杀死王继业的儿子。',note='招揽消息为王延羲听闻，不能据此确认王继业已归附王延政；儿子未具名不造人物，郊外所属城市未载。')
add('yang_jiye_friendship','杨沂丰曾在王继业任汀州刺史时担任士曹参军，两人交好',13,'初，继业','与之亲善。',[('杨沂丰','任士曹参军时与王继业交好'),('王继业','任汀州刺史时与杨沂丰交好')],year=None,when='王继业任汀州刺史期间，具体年月未载',place='汀州',note='初引出此前往事；杨沂丰司徒等为后来官职，不推该段任参军时已为宰相。')
add('yang_yifeng_arrest','杨沂丰被告与王继业串通，在宴席上被捕入狱',13,'或告沂丰','即收下狱，',[('杨沂丰','因被告串通，在侍宴时被捕')],year=None,when='王延羲在位期间，具体年月未载（见941年条）',note='通谋是告发内容，不写成查实；告发者未具名。')
add('yang_yifeng_killed','杨沂丰被捕次日遭斩杀，并被灭族',13,'明日斩之，','夷其族。',[('杨沂丰','被捕次日遭斩杀并灭族')],year=None,when='杨沂丰被捕的次日，具体年月未载（见941年条）',note='明日是相对次日，不能套六月戊午；原文未给具体被诛族人名单。')
relationship('杨沂丰','杨涉','族弟',13,'沂丰，涉之从弟也，','从弟保留为族弟关系，说明杨沂丰比杨涉辈内年幼，具体支系未载，不补两人父亲。')
claim('person','person_杨沂丰','biography','杨沂丰被杀时八十多岁，闽国人哀悼他。',13,'时年八十馀，国人哀之，','八十馀是史载概数，具体死亡年月未载，不反推精确出生年。')
add('huang_jun_remonstrates','黄峻抬棺到朝堂，劝阻王延羲接连诛杀旧臣',13,'自是宗族勋旧','舁榇诣朝堂极谏，',[('黄峻','抬棺到朝堂极力劝谏'),('曦','面对黄峻对接连诛杀的劝谏')],year=None,when='杨沂丰遇害以后，具体年月未载（见941年条）',description='杨沂丰遇害后，闽国宗族旧臣接连被杀，人人担忧自身安全。谏议大夫黄峻抬着棺材到朝堂，极力劝谏王延羲。')
add('xi_demotes_huang_jun','王延羲责骂黄峻，将他贬为漳州司户',13,'曦曰：“老物','贬漳州司户。',[('曦','责骂并贬黄峻'),('黄峻','因劝谏被贬为漳州司户')],year=None,when='黄峻抬棺进谏后，具体年月未载（见941年条）',place='漳州')
sup('xi_demotes_huang_jun',13,minbook,'諫議大夫黃峻舁櫬詣朝堂極諫，曦怒，貶峻漳州司戶參軍。','《新五代史》也记黄峻抬棺进谏，王延羲发怒，将他贬为漳州司户参军。','主书司户与新史司户参军的职名详略保留；不提前录入本片段中的陈光逸遇害。')
add('chen_promises_gold','王延羲支出不足，陈匡范提出每天进献万金',13,'曦淫侈无度，','匡范请日进万金；',[('曦','因支出不足向国计使询策'),('匡范','提出每日进献万金')],year=None,when='王延羲在位期间，具体年月未载（见941年条）',note='万金按原文保留，不换算现代货币；承诺不表示每天均已筹足。')
add('xi_promotes_chen','王延羲因陈匡范的筹款建议，给他加礼部侍郎',13,'曦悦，','加匡范礼部侍郎，',[('曦','给陈匡范加礼部侍郎'),('匡范','获加礼部侍郎')],year=None,when='陈匡范提出筹款建议后，具体年月未载（见941年条）')
add('chen_raises_commercial_tax','陈匡范将商人税额增加数倍',13,'匡范增算','商贾数倍。',[('匡范','增加商人税额以筹款')],year=None,when='陈匡范任国计使期间，具体年月未载（见941年条）',note='数倍是史载概数，不补税率。')
sup('chen_raises_commercial_tax',13,minbook,'國計使陳匡範增算商之法以獻，曦曰：「匡範人中寶也。」','《新五代史》也记陈匡范提出提高商人税额的办法，并获王延羲称赞。','官职、税制及称赞对应；範与范在展示名称中统一为范，原文字形保留。')
add('xi_praises_chen','王延羲在宴会上称赞陈匡范为人中之宝',13,'曦宴群臣，','不可得也。”',[('曦','在宴会上称赞陈匡范'),('匡范','受到王延羲称赞')],year=None,when='陈匡范提高商人税额后，具体年月未载（见941年条）',note='这是王延羲的评价，不作为网站对陈匡范的评价。')
add('chen_borrows_to_fill_quota','商税不足每日进献额，陈匡范借各官署的钱补足',13,'未几，商贾之算','贷诸省务钱以足之，',[('匡范','借各官署的钱补足每日进献额')],year=None,when='商税提高后不久，具体年月未载（见941年条）',note='未几是相对时间，诸省务为官署；不能据此写成向百姓借钱。')
sup('chen_borrows_to_fill_quota',13,minbook,'已而歲入不登其數，乃借於民以足之，','《新五代史》记收入未达原定数额，陈匡范向百姓借款补足。','主书记诸省务钱，新史记借于民；借款来源有差异，不互相替换。',relation='conflicts')
add('chen_kuangfan_dies','陈匡范害怕借款补额的事暴露，忧惧而死',13,'恐事觉，','忧悸而卒，',[('匡范','因担忧事情暴露而忧惧去世')],year=None,when='陈匡范借款补额之后，具体年月未载（见941年条）',note='死亡原因按史书归因保留，不作医学诊断或反推精确死亡年。')
add('xi_honors_chen','王延羲厚祭陈匡范，并给予追赠',13,'曦祭赠甚厚。','曦祭赠甚厚。',[('曦','厚祭并追赠陈匡范')],year=None,when='陈匡范去世后，具体年月未载（见941年条）',note='追赠具体职名未载。')
add('xi_destroys_chen_corpse','借款事情上报后，王延羲毁陈匡范的棺木与尸体，弃入水中',13,'诸省务以匡范','断其尸弃水中，',[('曦','得知借款后毁棺毁尸并弃尸于水中'),('匡范','死后遭毁棺毁尸')],year=None,when='陈匡范去世并获祭赠后，具体年月未载（见941年条）',note='毁尸与死亡分开，不写成陈匡范被杀而死。')
sup('xi_destroys_chen_corpse',13,minbook,'匡範以憂死。其後知其借於民也，剖棺斷尸，棄之水中。','《新五代史》也记陈匡范忧死后，借款事情被知晓，遭剖棺毁尸弃水。','同记先死后毁尸；借款来源仍依各书分别引用。')
add('huang_shaopo_appointed','王延羲任连江人黄绍颇为国计使',13,'以连江人','代为国计使。',[('曦','任命黄绍颇接任国计使'),('黄绍颇','接任国计使')],year=None,when='陈匡范借款事件暴露后，具体年月未载（见941年条）')
add('huang_shaopo_sells_offices','黄绍颇建议不属荫补的求官者交钱授官，王延羲同意',13,'绍颇请',None,[('黄绍颇','提出按条件收费授官的建议'),('曦','接受收费授官建议')],year=None,when='黄绍颇任国计使后，具体年月未载（见941年条）',description='黄绍颇建议，除依荫补资格入仕者外，求官者可交钱获官，价额按资历声望、州县户口等条件，从一百缗到一千缗不等。王延羲接受。',note='荫补是凭先人官爵获得入仕资格；建议和接受明确，未给已售官职名单，不造实际买官者。')
add('li_jianxun_memorial','李建勋上疏议事，李昪交主管官署施行',14,'会建勋上疏','下有司施行。',[('李建勋','上疏议事，本期待奏疏留中'),('唐主','将李建勋奏疏交主管官署施行')],when='941年七月戊辰罢李建勋以前，具体日期未载',note='意其留中是李建勋的期望，不表示奏疏实际已被留中；原文未给奏疏具体议题。')
add('li_jianxun_changes_memorial','李建勋秘密取回奏疏并改动',14,'建勋自知','密取所奏改之；',[('李建勋','秘密取回奏疏并修改')],when='941年七月戊辰罢官以前，具体日期未载',note='不猜改动内容，主书挟爱憎为其行为背景，保留原文说明。')
add('li_bian_removes_jianxun','李昪罢免李建勋，令其回私宅',14,'秋，七月，',None,[('唐主','罢免李建勋'),('李建勋','被罢官并回私宅')],when='941年七月戊辰',note='主语承接李昪，罢官不写成杀害。')
claim('person',person('唐主',14,'担心宰相权力过重，打算罢免执政多年的李建勋',span(14,'唐主自以','欲罢之。')),'biography','李昪因自己曾以专权取得吴国政权，尤其忌惮宰相权力过重，打算罢免长期执政的李建勋。',14,span(14,'唐主自以','欲罢之。'),'政治动机按史书叙述保留，不新增一次941年取吴事件。')
add('liu_zhi_yuan_beijing','石敬瑭任刘知远为北京留守、河东节度使',15,'帝忧安重荣','河东节度使，',[('帝','为防安重荣跋扈而调整河东任官'),('刘知远','获任北京留守、河东节度使')],when='941年七月己巳',place='河东')
add('liao_qin_returns_hedong','石敬瑭将辽州、沁州重新划归河东',15,'复以辽、沁','隶河东；',[('帝','将辽州和沁州重新划归河东')],when='941年七月己巳',place='辽州、沁州',note='行政隶属调整不当作疆界坐标已核。')
add('li_dechong_yedu','石敬瑭将李德珫调为邺都留守',15,'以北京留守', '为鄴都留守。',[('帝','调任李德珫'),('李德珫','从北京留守调为邺都留守')],when='941年七月己巳',place='邺都')
add('liu_zhi_yuan_early_marriage','刘知远早年入赘晋阳李家',15,'知远微时，','为晋阳李氏赘婿，',[('刘知远','早年入赘晋阳李家')],year=None,when='刘知远早年，具体年月未载',place='晋阳',note='李氏是家族称谓，本段没有给妻子姓名，未凭本句补具名妻子和岳父。')
add('liu_zhi_yuan_monk_beating','刘知远早年放牧的马侵入僧人田地，被僧人拘住鞭打',15,'尝牧马，','僧执而笞之。',[('刘知远','因牧马侵田，被僧人拘住鞭打')],year=None,when='刘知远早年，具体年月未载',place='晋阳',note='僧人未具名，不能另建姓名主体。')
add('liu_zhi_yuan_forgives_monk','刘知远到晋阳后，召见曾鞭打他的僧人，安慰并赠送财物',15,'知远至晋阳，',None,[('刘知远','召见曾鞭打自己的僧人，安慰并赠送财物')],when='941年七月任北京留守后，具体日期未载',place='晋阳',note='到任后的实际行为，不套己巳任命日；众心大悦是史书记述的反应，不补具体受赠财物数额。')
claim('person','person_陈匡范','biography','《资治通鉴》四部丛刊本电子转录写陈匡范为南安人。',13,'國計使南安陳匡範','原电子底本写国安，同书第155页固定修订1471331写南安；展示按另一版本校读，不改原始TXT，影印字形及纸本待核。',source='tongjian-282-941-min-collation',relation='conflicts')
reviews={12:'此前轻慢及杀使、契丹问责和皇帝赔礼年月未知；六月戊午拘捕、掠边及博野驻军分录。归附规模与十万众保留奏表语气；赵崇与905年遇害的唐臣消歧，逐刘山与杀刘山异说并列；拽剌身份与荝剌待核，赫连公德与功德人名异文保留。',13:'桑维翰奏疏跨两个原始检索段，分段引用保留论证和建议，敌我强弱及财政判断不当客观确证。闽国被杀、告发、抬棺劝谏、税制筹款、忧死与死后毁尸分开；初引交好往事及未明年月的财政追述用null；商税借款来源诸省务与民有书间差异；陈匡范籍贯底本国安据同书固定电子版本南安校读，原字保留，影印字形待核。',14:'取吴与忌相为李昪背景，奏疏留中是李建勋期待，实际下有司；秘密改疏、七月戊辰罢官分录，未补具体奏疏内容。',15:'七月己巳任官与辽沁回归河东分别录；刘知远早年赘婿和僧人鞭打为未知年，到晋阳后慰赠为任命后行动，不套同日，未补妻僧姓名。'}
assert not (P/'publication.json').exists()
for n in range(12,16):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=941,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(12,16)],next_paragraph=Q[16]['id'],next_volume=282,next_year=941,supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第12—15段，原97—100行；六月至七月记载及相关追述。全年38段，累计15段，剩余23段待录。',source_issues_review='安重荣奏表中的逐刘山与杀刘山、赫连公德与功德字形，闽国借款诸省务与民等差异独立引用；拽剌与旧荝剌身份尚待核。未把表文声称裁成独立查实。纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(12,16)],plain_language_review='首次检查新增人物介绍、事件说明、参与角色、关系方向、时间及事实说明；明确表文声称、建议、告发、追述与实际动作。已有主体字段保留，旧内容不扩大回改；逐字引用保持底本。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
