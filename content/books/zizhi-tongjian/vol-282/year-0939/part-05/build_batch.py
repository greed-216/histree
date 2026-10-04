# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 939 paragraphs 33–41."""
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
specs=[(d.name,d,'37303c8175d575410e0f8940236014136161b5a6','脱脱等' if d.name.startswith('songshi') else '司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-939-autumn','xinwudaishi-065-dayue-founding']:
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
main_sources = ['tongjian-282-939-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0939-p033-p041',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-078-late-august':'卷78·晋高祖纪·天福四年八月后续','jiuwudaishi-078-december':'卷78·晋高祖纪·天福四年十二月','songshi-480-qian-chu':'卷480·钱俶传'}
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
for n in range(33, 42):
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
    labels={'jiuwudaishi-078-late-august':'卷78·晋高祖纪·天福四年八月后续','jiuwudaishi-078-december':'卷78·晋高祖纪·天福四年十二月','songshi-480-qian-chu':'卷480·钱俶传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '九月条下' if n==33 else '十月条下' if n<=35 else '十一月条下' if n<=38 else '十二月条下' if n<=40 else '本年总述及延伸记事'
        citation = f'卷282·后晋天福四年（939；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0939_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'李知损':'后晋兵部员外郎。939年主张扣留闽国使者并没收货物，随后郑元弼、林恩被投入监狱。生卒年未载。',
'马氏（钱传瓘妻）':'吴越王钱传瓘的妻子，雄武节度使马绰之女，称恭穆夫人。她曾为钱传瓘向钱镠请求纳妾，待各妾所生子女慈爱如一。939年去世，生年未载。',
'鹿氏（钱传瓘妾）':'钱传瓘的妾，钱弘僔、钱弘倧之母。个人名字及生卒年未载。',
'许氏（钱传瓘妾）':'钱传瓘的妾，钱弘佐之母。个人名字及生卒年未载。',
'吴氏（钱传瓘妾）':'钱传瓘的妾，钱弘俶之母。《宋史》称其为吴越国恭懿夫人吴氏。个人名字及生卒年暂未核实。',
'钱弘倧':'钱传瓘之子，母亲鹿氏。939年条下的王室家属追述提及他，出生年份本句未载。',
'钱弘佐':'钱传瓘之子，母亲许氏。939年条下的王室家属追述提及他，出生年份本句未载。',
'钱弘俶':'钱传瓘之子，母亲吴氏。《宋史》本传明确本名弘俶，后名钱俶；《资治通鉴》所用电子本在王室家属追述中把俶写作拆分字形。生卒年暂未录全。',
'钱弘偡':'钱传瓘之子，母亲姓名本句未载。939年条下的王室家属追述提及他，出生年份未载。',
'钱弘亿':'钱传瓘之子，母亲姓名本句未载。939年条下的王室家属追述提及他，出生年份未载。',
'钱弘仪':'钱传瓘之子，母亲姓名本句未载。939年条下的王室家属追述提及他，出生年份未载。',
'钱弘偓':'钱传瓘之子，母亲姓名本句未载。939年条下的王室家属追述提及他，出生年份未载。',
'钱弘仰':'钱传瓘之子，母亲姓名本句未载。939年条下的王室家属追述提及他，出生年份未载。',
'钱弘信':'钱传瓘之子，母亲姓名本句未载。939年条下的王室家属追述提及他，出生年份未载。',
'遥折（契丹使者）':'契丹臣属。939年十一月奉使后晋，随后前往吴越。姓名字形及具体官职尚待其他版本核对，生卒年未载。',
'李弘皋':'楚王马希范的幕僚，939年天策府开府时获任学士。生卒年未载。',
'廖匡图':'楚王马希范的幕僚，939年天策府开府时获任学士。与廖匡齐是否有亲属关系本段未载，不因近名建立关系。生卒年未载。',
'徐仲雅':'楚王马希范的幕僚，939年天策府开府时获任学士。生卒年未载。',
'李纾（南汉谏议大夫）':'南汉谏议大夫。939年受赵光裔推荐，奉刘岩命前往楚国恢复使节往来。与他国同名官员的关系尚未核定，生卒年未载。',
'赵损（南汉宰相）':'赵光裔之子，曾任南汉翰林学士承旨、尚书左丞。赵光裔去世后，刘岩任他为门下侍郎、同平章事；本段未列任官确年。生卒年未载。'}
NEW_ALIASES={'李知损':['李知損'],'马氏（钱传瓘妻）':['恭穆夫人马氏'],'鹿氏（钱传瓘妾）':[],'许氏（钱传瓘妾）':[],'吴氏（钱传瓘妾）':['恭懿夫人吴氏'],'钱弘倧':['錢弘倧'],'钱弘佐':['錢弘佐'],'钱弘俶':['钱俶','錢俶','錢弘俶'],'钱弘偡':['錢弘偡'],'钱弘亿':['錢弘億'],'钱弘仪':['錢弘儀'],'钱弘偓':['錢弘偓'],'钱弘仰':['錢弘仰'],'钱弘信':['錢弘信'],'遥折（契丹使者）':['遥折'],'李弘皋':[],'廖匡图':['廖匡圖'],'徐仲雅':[],'李纾（南汉谏议大夫）':['李纾','李紓'],'赵损（南汉宰相）':['赵损','趙損']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=939 if name=='马氏（钱传瓘妻）' else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=939, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='939年'+('九月条下' if n==33 else '十月条下' if n<=35 else '十一月条下' if n<=38 else '十二月条下' if n<=40 else '，月份未载')+'，具体日期未载'
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




ALIASES.update({'李后':'永宁公主（石敬瑭妻）','从益':'李从益','康宗':'王继鹏','林恩':'林恩（闽进奏官）','元瓘':'钱传瓘','元璟':'钱传瓘','镠':'钱镠','马夫人':'马氏（钱传瓘妻）','鹿氏':'鹿氏（钱传瓘妾）','许氏':'许氏（钱传瓘妾）','吴氏':'吴氏（钱传瓘妾）','遥折':'遥折（契丹使者）','楚王希范':'马希范','闽王':'王延羲','汉主':'刘岩','马后':'越国夫人马氏','李纾':'李纾（南汉谏议大夫）','损':'赵损（南汉宰相）'})
aug='jiuwudaishi-078-late-august';dec='jiuwudaishi-078-december';song='songshi-480-qian-chu';zhao='xinwudaishi-065-dayue-founding'
add('li_congyi_xungong','石敬瑭封李从益为郇国公，令他奉后唐祭祀',33,'癸未，','奉唐祀。',[('帝','封后唐许王李从益为郇国公，令其奉后唐祭祀'),('从益','由后唐许王改封郇国公，奉后唐祭祀')],when='939年九月条下癸未；《旧五代史》本纪列于八月',note='唐许王指后唐宗室李从益，不是南唐封王；两书月份和旧史所附五代会要九月引文分别保留，未自行裁定。')
sup('li_congyi_xungong',33,aug,source_span(aug,'癸未，封唐許王','牲幣器服悉從官給。'),'《旧五代史》本纪在八月后续记李从益封郇国公，并补以西京至德宫为庙，祭祀物品由官府供给。','本纪所在月份与通鉴九月条下有异；官供祭物和旧制服色旌旗分别按该书补证，不补实际费用。',relation='conflicts')
sup('li_congyi_xungong',33,aug,source_span(aug,'〈（《五代會要》：九月，','云。）〉'),'《旧五代史》所附《五代会要》引文称九月封郇国三千户。','这是旧史中的转引，不作为直接查核《五代会要》的独立书证；保留本纪八月与转引九月的差异。',relation='adds')
add('jin_queen_raises_congyi','后晋李皇后在宫中抚养年幼的李从益',33,'从益尚幼，','于宫中，',[('李后','在宫中抚养年幼的李从益'),('从益','年幼时得到后晋李皇后的抚养')],year=None,when='李从益年幼时的抚养概述，起止年份未载',description='李从益年幼，后晋李皇后在宫中抚养他。这里的李皇后是石敬瑭的妻子、永宁公主。',note='养指抚养行为，本句没有法定收养或生母记载，不新增母亲、养母关系；不与闽国李春燕混淆。')
add('jin_queen_respects_shufei','后晋李皇后像侍奉母亲一样侍奉王淑妃',33,'李后养',None,[('李后','像侍奉母亲一样侍奉王淑妃'),('王淑妃','受到后晋李皇后如母亲般侍奉')],year=None,when='后晋宫中礼遇的概述，起止年份未载',description='后晋李皇后在宫中抚养李从益，并像侍奉母亲一样侍奉王淑妃。',note='奉王淑妃的主语承李后；如事母是礼遇方式，不证明王淑妃是李皇后的生母。')
add('zheng_arrives_daliang','郑元弼带着王继鹏的使命抵达大梁',34,'冬，','至大梁。',[('郑元弼','以王继鹏派遣的闽国使者身份抵达大梁'),('康宗','此前派郑元弼出使，使命延续到他死后')],when='939年十月庚戌',place='大梁',note='王继鹏已在本年闰七月政变中被杀；本条是此前使者此时到达，不把已故王继鹏写成十月仍在位亲自遣使。')
add('min_letter_equal_diplomacy','王继鹏给后晋执政者的书信要求两国以对等礼节往来',34,'康宗遗执政','致书往来。',[('康宗','向后晋执政者致书，要求按对等国家礼节通信'),('郑元弼','带来王继鹏要求对等往来的使命')],year=None,when='郑元弼十月抵达前的使节使命，书信写作确日未载',description='王继鹏给后晋执政者的书信称，中原帝位多次变更，使闽国海路往来受阻，并要求按对等国家的礼节互通书信。',note='敌国在这里指地位对等的国家，不翻成双方已经交战；帝位变更与航路受阻是书信说法，不外推具体断航次数。')
add('shi_returns_min_tribute','石敬瑭因闽书信失礼，退还贡物并命使者归国',34,'帝怒其','部送速归。',[('帝','认为闽国书信失礼，命退还贡物和福建诸州纲运并送使者归国'),('郑元弼','被命令尽快归国'),('林恩','以闽进奏官身份被命令随同归国')],when='939年十月壬子',description='石敬瑭认为闽国书信不逊，下诏退还贡物及福州、建州等地运来的物资，并命将郑元弼和进奏官林恩尽快送回。',note='命归国是此阶段的命令；随后转为扣押，不录为已经顺利回到闽国。纲运按成批运送的物资解释，不补具体品类和数量。')
add('li_zhisun_proposes_detention','李知损建议扣留闽使，并没收货物',34,'兵部员外郎','籍没其货。”',[('李知损','以兵部员外郎身份建议扣留闽国使者并没收货物')],when='939年十月壬子退贡命令后，具体日期未载',note='建议与执行分别记；王昶指王继鹏，不将李知损视作赵光裔之子赵损。')
add('min_envoys_imprisoned','郑元弼、林恩被投入监狱',34,'乃下元弼、',None,[('郑元弼','在李知损建言后被投入监狱'),('林恩','在李知损建言后被投入监狱')],when='939年十月退贡及建言后，具体日期未载',note='入狱有明文，本句未明说货物已经没收，不把前面没收建议视作已执行。')
add('wuyue_ma_dies','吴越恭穆夫人马氏去世',35,'吴越恭穆夫人','马氏卒。',[('马夫人','以吴越恭穆夫人身份去世')],when='939年十月条下，具体日期未载',note='死亡在本年顺叙，未列干支；没有补谥号颁赐日期、病名或葬地。')
relationship('马绰','马夫人','父亲',35,'夫人，雄武节度使绰之女也。','马绰是恭穆夫人马氏的父亲，沿用已有马绰主体；不与南汉皇后马氏的父亲马殷混淆。')
relationship('马夫人','钱传瓘','妻子',35,Q[35]['text'],'妻子身份依据整段恭穆夫人与钱传瓘纳妾、抚养其子叙述，方向为马氏是钱传瓘的妻子；未反向重复建立丈夫关系。')
add('qian_liu_music_ban','钱镠曾禁止内外蓄养声妓',35,'初，','畜声妓，',[('镠','禁止宫内外蓄养歌舞艺人')],year=None,when='钱镠在位期间的追述，具体日期未载',description='钱镠曾禁止宫内外蓄养声妓。这里的声妓指当时的歌舞艺人。',note='声妓作为时代称谓保留并解释，不自动等同现代性交易；中外的具体机构名单未载。')
add('ma_requests_concubines','马氏为钱传瓘请求纳妾，钱镠同意',35,'文穆王元瓘','听元璟纳妾。',[('马夫人','为三十多岁仍无子的丈夫钱传瓘向钱镠请求纳妾'),('钱传瓘','三十多岁尚无子，获准纳妾'),('镠','赞许马氏为家族祭祀考虑，允许钱传瓘纳妾')],year=None,when='钱传瓘三十多岁、钱镠在位期间，具体年份未载',description='钱传瓘三十多岁尚无儿子，马氏为他向钱镠请求纳妾。钱镠认为她顾及家族祭祀，赞许后允许钱传瓘纳妾。',note='本段追述未给确年，不用年龄倒推。元璟字形沿前批旧史钱元瓘官命核对为钱传瓘，原字保留。')
# Individual parentage is a lasting relation; births are not all assigned to 939.
children=[('钱弘僔','鹿氏','鹿氏，生弘僔、弘倧；'),('钱弘倧','鹿氏','鹿氏，生弘僔、弘倧；'),('钱弘佐','许氏','许氏，生弘佐；'),('钱弘俶','吴氏','吴氏，生弘亻叔；')]+[(x,None,'众妾生弘偡，弘亿、弘仪、弘偓、弘仰、弘信；') for x in ['钱弘偡','钱弘亿','钱弘仪','钱弘偓','钱弘仰','钱弘信']]
for child,mother,quote in children:
 person(child,35,'是钱传瓘之子',quote)
 relationship('钱传瓘',child,'父亲',35,Q[35]['text'],'整段围绕钱传瓘获准纳妾及所生诸子展开，父亲指向儿子；具体出生年未载，不推兄弟排行。')
 if mother:relationship(mother,child,'母亲',35,quote,'生明确该妾为孩子母亲；关系为母亲指向孩子，未补个人名字或出生年。')
claim('person',people['钱弘俶'],'aliases','钱弘俶后来改名钱俶，《宋史》明确记本名弘俶。',35,'吳越錢俶，字文德，杭州臨安人。本名弘俶，以犯宣祖偏諱，去之。','本名、后名来自宋史；这里只补姓名证据，后来的改名未当939年发生。',source=song)
claim('person',people['钱弘俶'],'description','《宋史》记钱俶为钱元瓘第九子，母亲为吴越国恭懿夫人吴氏。',35,'俶即元瓘之第九子也，母吳越國恭懿夫人吳氏。','与通鉴父母及拆分字形弘亻叔对应，展示使用钱弘俶；不据第九子为其余儿子补出完整排行。',source=song)
add('ma_treats_sons_equally','马氏慈爱对待钱传瓘各妾所生子女，常逗他们玩耍',35,'夫人抚视慈爱',None,[('马夫人','慈爱对待各妾所生子女，并用帐前银鹿逗他们玩耍')],year=None,when='马氏生前抚育钱氏子女的概述，起止年份未载',description='马氏慈爱对待各妾所生子女，一视同仁。她常把银鹿摆在帐前，让孩子坐在上面，逗他们玩耍。',note='抚育与生育区分，未把所有孩子都记为马氏亲生；银鹿的材质以银名物保留，不补尺寸与工艺。')
add('yaozhe_mission','契丹派遥折出使后晋，随后前往吴越',36,'十一月，',None,[('契丹主','派臣属遥折出使'),('遥折','到后晋出使后前往吴越')],when='939年十一月戊子',place='后晋、吴越',note='遂如吴越为随后前往，没补两国具体会见和行程日；遥折姓名字形待校，不猜契丹氏族和官职。')
add('ma_opens_tiance','马希范正式开天策府，任弟弟及将校为官',37,'楚王希范','及将校为之。',[('楚王希范','开天策府，任诸弟及将校为护军都尉、领军司马等官')],description='马希范正式开设天策府，设置护军都尉、领军司马等官，由他的弟弟们和将校担任。',note='与此前五月获准开府不同，此处明确始开；诸弟及将校未逐一具名，不补具体官员名单。')
add('ma_eighteen_scholars','马希范任拓跋恒、李弘皋、廖匡图、徐仲雅等十八人为学士',37,'又以幕僚',None,[('楚王希范','任幕僚十八人为天策府学士'),('拓跋恒','以幕僚身份获任学士'),('李弘皋','以幕僚身份获任学士'),('廖匡图','以幕僚身份获任学士'),('徐仲雅','以幕僚身份获任学士')],note='主书只列四人，共十八人；未据等字补足其余十四人，也不因廖匡图与廖匡齐近名造兄弟关系。')
add('liu_takes_xizhou','刘勍等进攻溪州，彭士愁战败退守山寨',38,'刘勍等','走保山寨；',[('刘勍','与其他将领进攻溪州'),('彭士愁','战败后放弃溪州，退守山寨')],place='溪州、山寨',note='与九月出兵是后续战况；弃州不等于已向楚投降。')
add('liu_ladder_siege','刘勍搭设梯栈，登上四面险崖围攻彭士愁山寨',38,'石崖四绝，','上围之。',[('刘勍','搭设梯栈登崖围攻山寨'),('彭士愁','据守山寨遭围攻')],place='溪州山寨',note='本句围之是围攻，尚未记攻破，不能提前把下一年火攻、投降结果录入939年。')
add('liao_kuangqi_dies','廖匡齐在溪州战事中战死',38,'廖匡齐战死，','廖匡齐战死，',[('廖匡齐','在楚军讨伐彭士愁的战事中战死')],place='溪州战场',note='战死明确在本年顺叙，具体死法、死地点位与日期未载。')
claim('person',people['廖匡齐'],'death_year','939年楚军溪州战事中，廖匡齐战死。',38,'廖匡齐战死，','新增死亡出处，不覆盖既有原始人物档案或猜阵亡细节。')
add('ma_consoles_liao_mother','马希范派人慰问廖匡齐母亲，她表示全族愿报答楚王',38,'楚王希范遣吊','愿王无以为念。”',[('楚王希范','派使者慰问廖匡齐母亲'),('廖匡齐','战死后，母亲得到楚王派人慰问')],description='马希范派人慰问廖匡齐母亲。她没有哭，告诉使者，廖氏三百口受楚王温饱之赐，全族效死仍不足报答，何况一个儿子，请楚王不必挂念。',note='三百口和报恩是母亲对使者的言论，不当作已核户籍统计。母亲及使者未具名，不新建猜测人物。')
add('ma_supports_liao_family','马希范认为廖匡齐母亲贤德，厚加抚恤其家',38,'王以其母',None,[('楚王希范','认为廖匡齐母亲贤德，厚加抚恤廖家')],description='马希范认为廖匡齐母亲贤德，对廖家给予优厚抚恤。',note='贤是马希范的评价；抚恤具体财物和数量未载，不补数额。')
add('shi_bans_new_monasteries','石敬瑭禁止新建佛教寺院',39,'十二月，',None,[('帝','下令禁止新建佛教寺院')],when='939年十二月丙戌；《旧五代史》另记丙辰',description='石敬瑭禁止新建佛教寺院。《资治通鉴》记十二月丙戌，《旧五代史》记丙辰，两书纪日不同。',note='主语承后晋帝纪；禁止新建不等于拆毁既有寺院或全面禁止佛教活动。')
sup('shi_bans_new_monasteries',39,dec,'丙辰，詔今後城郭村坊，不得創造僧尼院舍。','《旧五代史》将禁新建僧尼院舍的诏令记在十二月丙辰，并明确范围为城郭村坊。','政策内容相近，干支与通鉴丙戌有异；不另造第二道确定诏令，不扩大为强拆已有寺院。',relation='conflicts')
add('min_yanxi_new_palace','王延羲建新宫并迁入居住',40,'闽王作',None,[('闽王','建新宫并迁入居住')],note='闽王为本年政变后即位的王延羲，宫名与工程费用未载，未补遗址或建筑形制。')
add('zhao_restores_chu_relations','赵光裔劝刘岩恢复与楚国的使节往来，并推荐李纾',41,'是岁，','可以将命，',[('赵光裔','以门下侍郎、同平章事身份劝刘岩恢复与楚国往来'),('汉主','听取赵光裔有关楚国旧好的建议'),('李纾','被推荐承担出使楚国的使命'),('马后','去世后南汉与楚国使节往来一度中断')],when='939年，具体月日未载',description='赵光裔告诉刘岩，自马皇后去世后，南汉不再向楚国派使者；亲邻的旧好不应忘记。他推荐谏议大夫李纾出使楚国。',note='马后复用南汉越国夫人马氏，已在934年记录去世，不与本年去世的吴越马氏混淆；中断是赵光裔陈述，不补每年交往次数。')
add('han_chu_exchange_envoys','刘岩采用赵光裔建议派李纾出使，楚国派使者回访',41,'汉主从之；','楚亦遣使报聘。',[('汉主','同意建议并派李纾出使楚国'),('李纾','承担南汉出使楚国的使命'),('楚王希范','楚国在本年派使者回访南汉')],when='939年，具体月日未载',note='从之前所荐使人识别李纾；楚亦遣使未具名，不添加无名使者，也不推已经缔结军事同盟。')
add('zhao_long_chancellorship','史书记述赵光裔辅佐南汉二十多年，府库充实、边境平安',41,'光裔相汉','边境无虞。',[('赵光裔','被史书记为长期辅佐南汉、使府库充实边境平安')],year=None,when='赵光裔辅佐南汉二十多年的概述，非939年单日事件',description='《资治通鉴》记，赵光裔辅佐南汉二十多年，府库充实，边境没有忧患。',note='这是多年经历的史书概述，未把二十多年倒算为确切任官年，亦不把无虞扩大为所有地区从未发生冲突。')
add('zhao_guangyi_dies','赵光裔去世',41,'及卒，','及卒，',[('赵光裔','去世后，其子赵损得到任官')],year=None,when='赵光裔长期辅佐南汉之后，本句未列死亡确年',note='及卒是从本年建议延伸的后事，没有确年补证，未强定为939年死亡。')
add('zhao_sun_chancellor','赵光裔去世后，刘岩任赵损为门下侍郎、同平章事',41,'汉主复以',None,[('汉主','在赵光裔去世后任赵损为门下侍郎、同平章事'),('损','由翰林学士承旨、尚书左丞获任门下侍郎、同平章事')],year=None,when='赵光裔去世后，本句未列任官确年',note='其子指赵光裔之子赵损；不是后晋兵部员外郎李知损，不因损字相同合并。')
relationship('赵光裔','损','父亲',41,'汉主复以其子翰林学士承旨、尚书左丞损为门下侍郎、同平章事。','其子承赵光裔，父亲指向儿子赵损；任官和死亡确年未知，不借本年标题强定。')
claim('person',people['赵损（南汉宰相）'],'description','《新五代史》南汉世家也记南汉宰相有二子损、益，但该段称父亲为赵光胤，与《资治通鉴》的赵光裔姓名有异。',41,'龑乃習為光胤手書，遣使間道至洛陽，召其二子損、益并其家屬皆至。','原已发布917年补证保留光胤字形异说；本次沿通鉴的赵光裔、赵损主体，不新增赵光胤别名或赵益人物，也不把旧事搬为939年事件。',source=zhao,relation='conflicts')
reviews={33:'李从益郇国公、奉后唐祭祀与宫中抚養礼遇分别录；主书九月、旧史本纪八月及所附会要九月异说保留，转引不当独立原书。李后指后晋皇后，养不强作法定收养，如事母不推生母关系。',34:'郑元弼十月抵大梁、书信要求对等往来、退贡命归国、李知损建议扣留没货、实际郑林下狱分录；王继鹏已死，使节使命来自此前，敌国不是已开战，建议没货未当已执行。',35:'吴越恭穆夫人马氏死与南汉马皇后分开。纳妾前无子、夫人请父王及王室家属为此前追述，所有孩子出生年未知。钱弘亻叔依据宋史本名弘俶、父元瓘母吴氏校展示，原字保留；母亲未名的六子不猜母。马氏抚育非所有孩子亲生。',36:'遥折十一月戊子奉使后晋后往吴越，字形与官职待校，不补未载会见。',37:'天策府此前五月仅获许可，此时始开并置官。诸弟将校未名不补；十八学士只列原文四名，廖匡图不因近名与廖匡齐造兄弟关系。',38:'进攻溪州、彭败退山寨、搭梯栈围攻、廖匡齐战死、母言与楚王厚恤分别录；未提前940年火攻投降结果，廖母和使者姓名未知，三百口是母言不当户籍统计。',39:'禁新建佛寺，主十二月丙戌旧丙辰纪日有异，僧尼院舍及范围补证，不扩大成毁寺或禁止全部佛教。',40:'王延羲建新宫迁居，宫名、地址和费用未载。',41:'赵光裔本年劝刘岩恢复楚使节、李纾出使及楚回访属939；二十多年为经历概述，及卒和赵损继任是后事延伸未具确年。复用南汉马皇后，赵损与李知损分开。新史宰相写光胤、主光裔姓名异说保留，未新增未经核别名。'}
assert not (P/'publication.json').exists()
for n in range(33,42):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=939,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,42)],next_paragraph='zztj-v282-y0940-p001',next_volume=282,next_year=940,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第33—41段，原38—46行，九月至年末及延伸记事；939年全部41正文段已整理，待本批发布后做全年覆盖审计。',source_issues_review='李从益封爵月份、禁建寺院干支、弘亻叔拆分字形、遥折字形、赵光裔/光胤姓名异说分别保留；赵光裔死亡及赵损继任未强定本年，纸本异文仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,42)],plain_language_review='首次逐条检查全部展示字段，主语和行动明确；抚养与亲生、计划建言与执行、亲属名单与出生年、使节使命与已故君主、对等国礼与交战、往事及延伸后事与当前年分别表述。引用底本原字保持，异说与未定年保留。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
