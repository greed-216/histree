# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 290, year 951 paragraphs 8–15."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,83))
COMMIT='82a6e88e766f7337f28566c6d64678bb760b98b8'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
specs.append(('tongjian-290-951-january-court',YEAR/'part-01/sources/library/tongjian-290-951-january-court',COMMIT,'司马光等'))
for key in ['tongjian-290-951-accession-policy','xinwudaishi-011-first-year-951','xinwudaishi-011-december-950']:
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
main_sources = ['tongjian-290-951-accession-policy','tongjian-290-951-january-court']
B = {'format_version': 1, 'batch_key': 'zztj-v290-y0951-p008-p015',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-290-951-january-court':'卷290·广顺元年·正月北汉与宋州事','jiuwudaishi-110-january-yun-letter':'卷110·太祖本纪·归藩书与契丹使','jiuwudaishi-110-yedu-funeral':'卷110·太祖本纪·邺都任命与隐帝发丧','jiuwudaishi-135-liu-chong-background':'卷135·刘崇传·汉末求子归藩','jiuwudaishi-135-liu-min-accession':'卷135·刘崇传·改名与北汉初政','xinwudaishi-070-li-xiang-counsel':'卷70·东汉世家·李骧劝谏与被杀'}
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
lines = (ROOT / 'resources/derived/tongjian/290.txt').read_text().splitlines()
for n in range(8, 16):
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
    labels={'tongjian-290-951-january-court':'卷290·广顺元年·正月北汉与宋州事','jiuwudaishi-110-january-yun-letter':'卷110·太祖本纪·归藩书与契丹使','jiuwudaishi-110-yedu-funeral':'卷110·太祖本纪·邺都任命与隐帝发丧','jiuwudaishi-135-liu-chong-background':'卷135·刘崇传·汉末求子归藩','jiuwudaishi-135-liu-min-accession':'卷135·刘崇传·改名与北汉初政','xinwudaishi-070-li-xiang-counsel':'卷70·东汉世家·李骧劝谏与被杀'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷290·广顺元年（951年正月及此前追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_290_0951_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=951, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='951年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_290_0951_' + code
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
        edge = 'participation_zztj_290_0951_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_290_0951_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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










ALIASES.update({'帝':'郭威','刘崇':'刘崇（刘知远弟）','北汉主':'刘崇（刘知远弟）','赟':'刘赟','巩廷美':'巩延美','王殷':'王殷（后汉后周将）','契丹主':'耶律阮','硃宪':'朱宪（后周使者）','承钧':'刘承钧','董氏':'董氏（刘赟妻）'})
NEW_ALIASES={'朱宪（后周使者）':[],'董氏（刘赟妻）':[],'赵华':['趙華'],'刘承钧':['劉承鈞'],'张元徽':['張元徽'],'陈光裕':['陳光裕'],'李光美':[]}
NEW_DESCRIPTIONS={'朱宪（后周使者）':'后周左千牛卫将军。951年受郭威派遣出使契丹，说明改朝原因，并赠金器玉带。与938年后晋内职官朱宪暂无连续履历证据，暂不合并，生卒年未载。','董氏（刘赟妻）':'刘赟的妃子。刘赟被废后，巩延美、杨温奉她据守徐州，等待河东援兵。与郭威妻子董氏等同姓人物分别建档，生卒年未载。','赵华':'荥阳人，刘崇的观察判官。951年北汉建立时任户部侍郎、同平章事。生卒年未载。','刘承钧':'刘崇的次子。951年父亲在晋阳称帝时，任侍卫亲军都指挥使、太原尹。《旧五代史》也记他是刘崇之子并任两职。生卒年本批未录。','张元徽':'武安人，刘崇的裨将。951年北汉建立时任马步军都指挥使。生卒年未载。','陈光裕':'951年北汉建立时获任宣徽使。生卒年未载。','李光美':'河南人，北汉客省使，曾任直省官，熟悉典章。史书将北汉朝廷制度归于他的安排。生卒年未载。'}
letter='jiuwudaishi-110-january-yun-letter';funeral='jiuwudaishi-110-yedu-funeral';bg='jiuwudaishi-135-liu-chong-background';access='jiuwudaishi-135-liu-min-accession';counsel='xinwudaishi-070-li-xiang-counsel';new='xinwudaishi-011-first-year-951';dec='xinwudaishi-011-december-950'
add('liu_chong_halts_march','刘崇听说将立刘赟，停止南下出兵计划',8,'初，河东节度使','吾又何求！”',[('刘崇','听闻刘承祐遇害后欲南下，得知拟立儿子刘赟便停止计划'),('赟','被拟立嗣君的消息使父亲停止出兵计划')],year=950,when='950年十一月刘承祐死后、刘赟被废以前的追述',place='河东',note='拟出兵与停止计划，不说实际已率军出河东；吾儿为帝是刘崇喜悦话语，刘赟未正式即位。')
sup('liu_chong_halts_march',8,counsel,'當是時，人皆知太祖之非實意也，旻獨喜曰：「吾兒為帝矣，何患！」乃罷兵，遣人至京師。','《新五代史》也记刘崇闻拟立其子而喜，停止出兵并派人到京师。','人皆知郭非实意是作者判断，不当已验证所有人的心理；旻沿刘崇后改名，不提前当其已在950年改名。')
add('li_xiang_proposes_mengjin','李骧劝刘崇率兵越太行据孟津，等刘赟即位再撤',8,'太原少尹李骧','且为所卖。”',[('李骧','提议以驻兵孟津保全刘赟继位'),('刘崇','收到出兵劝谏'),('郭威','被李骧判断将自行夺位')],year=950,when='950年十一月拟迎立刘赟期间的追述',place='太原，拟往太行与孟津',note='郭终自取与不然被骗是李骧判断，驻兵越山未实施；经济之才下文意治国，不译现代经济学。')
sup('li_xiang_proposes_mengjin',8,counsel,'因勸旻以兵下太行，控孟津以俟變，庶幾贇得立，贇立而罷兵可也。','《新五代史》也记李骧提议出兵控制孟津，等待刘赟即位后罢兵。','同一建议，未记实际出兵，不把拟路线当已走路线。')
add('liu_chong_kills_li_xiang','刘崇怒斥李骧离间父子，命人将他斩首',8,'崇怒曰：','命左右曳出斩之。',[('刘崇','将李骧劝谏视作离间父子，命人斩首'),('李骧','因劝谏被拖出斩首')],year=950,when='950年十一月拟迎立刘赟时，具体被杀日未载',place='太原',note='左右未具名不造执行人；父子指刘崇刘赟，不是刘崇郭威。')
claim('person',people['李骧'],'death_year','李骧于950年刘赟拟被迎立时，因劝谏刘崇被杀。',8,'崇怒曰：“腐儒，欲离间吾父子！”命左右曳出斩之。','从刘承祐遇害和迎嗣前后确定950年，不系951年条头。')
add('liu_chong_kills_li_wife','李骧临刑求与妻同死，刘崇杀其妻并奏报朝廷',8,'骧呼曰：','示无二心。',[('李骧','临刑求与老妻一同死'),('刘崇','连李骧妻一并杀死，向朝廷奏报表明忠诚')],year=950,when='950年十一月李骧被杀时，具体日未载',place='太原',note='妻无姓名不造姓名实体；奏报示忠是刘崇意图，不证明政治忠诚事实。')
sup('liu_chong_kills_li_wife',8,counsel,'然吾妻病，不可獨存，願與之俱死。」旻聞之，即并戮其妻于市，以其事白漢，以明無佗。','《新五代史》补记李骧说妻子患病，求一同死，刘崇杀其妻于市并奏报后汉。','通鉴称老妻，新史补病；都不具姓名，不猜疾病种类。',relation='adds')
add('liu_chong_requests_yun_home','刘崇得知刘赟被废，派使者请求让儿子回晋阳',8,'及赟废，','请赟归晋阳。',[('刘崇','派使者请求刘赟回晋阳'),('赟','成为请求归藩的对象')],when='950年十二月刘赟被废后至951年正月死亡以前的追述',year=None,place='河东至后周朝廷',note='及赟废只定相对先后，不强定请求是在950或951；两书认为书信到达在死后者另列。')
sup('liu_chong_requests_yun_home',8,bg,'崇乃遣牙將李奉書求赟歸藩，會赟已死，唯以優辭答之。','《旧五代史》记刘崇派牙将奉书求刘赟归藩，时刘赟已死，朝廷只以好言答复。','与通鉴将请求和答书放在刘赟死亡以前的叙述不同；牙将姓名含私用字，保留原字但不猜名建人。',relation='conflicts')
sup('liu_chong_requests_yun_home',8,letter,'北京留守劉崇遣押牙鞏廷美致書，求劉赟歸藩。','《旧五代史》太祖本纪另记刘崇派押牙巩廷美求刘赟归藩。','与同书刘崇传派牙将、且刘赟已死的写法不同；巩廷美与同时守徐州巩将是否同人未定，不按同名新增本人的出使参与。',relation='conflicts')
add('guo_assures_liu_chong','朝廷答刘崇称将取刘赟入京，并承诺封王永镇河东',8,'诏报以','永镇河东。”',[('郭威','以朝廷答书安抚刘崇，提出封王永镇河东的承诺'),('刘崇','收到取子入京及封王承诺'),('赟','被答书称将自宋州取入京')],when='刘赟被废后、951年正月死亡前条下，具体答书日未载',year=None,place='后周朝廷与河东',note='答书承诺不等于刘赟已返京、封王和永久镇守已兑现；书信时序与旧传死后答并列。')
sup('guo_assures_liu_chong',8,letter,'即當便封王爵，永鎮北門，鐵券丹書，必無愛惜。','《旧五代史》答书还承诺封王永镇北门并给铁券。','北门在河东语境，承诺铁券不当已实际颁发；不编物件样式。',relation='adds')
add('xuzhou_refuses_yun_deposition','巩延美、杨温奉刘赟妃董氏守徐州，等待河东援军',8,'巩廷美、杨温','以俟河东援兵，',[('巩廷美','奉董氏守徐州，等待援军'),('杨温','奉董氏守徐州，等待援军'),('董氏','被奉为刘赟家属，随军据守徐州'),('赟','其妃和留守将领因其被废拒守徐州')],when='950年十二月刘赟被废后至951年正月拒守期间，起始日未载',year=None,place='徐州',note='巩廷美沿已核巩延美别名；据城拒守与河东援军实际到来区分，不写援军已至。')
relationship('董氏','刘赟','妻子',8,'奉赟妃董氏据徐州拒守，','董氏是刘赟的妻子，妃为该嗣君配偶称谓；不与郭威董氏合并，也不推婚期。')
sup('xuzhou_refuses_yun_deposition',8,funeral,'是日，湘陰公元從右都押衙鞏廷美、教練使楊溫等，據徐州以拒命。','《旧五代史》将巩廷美、杨温据徐州拒命的记载列在正月丙子。','通鉴追述废嗣后的拒守，旧本纪提供丙子记事节点，不以其推拒守必始于当日。',relation='adds',field='time_original')
add('guo_yun_letter_to_xuzhou','郭威让刘赟写信劝谕徐州守将',8,'帝使赟','以书谕之。',[('郭威','让刘赟致信徐州守将'),('赟','奉命用信劝谕守将'),('巩廷美','成为劝谕对象'),('杨温','成为劝谕对象')],when='951年正月王彦超获命暂任武宁后、刘赟死前，具体书信日未载',place='宋州与徐州',note='让写信有行动记载，未写二将收到信后立即投降。')
add('guo_promises_xuzhou_posts','郭威得知徐州二将怕死，致刘赟书承诺授刺史',8,'廷美、温欲降','公可更以委曲示之。”',[('郭威','致刘赟书，承诺新节度使入城后给二将刺史职'),('赟','受托继续向徐州守将说明保证'),('巩廷美','欲降而担心被杀'),('杨温','欲降而担心被杀')],when='951年正月劝谕徐州阶段、刘赟死前，具体书信日未载',place='后周朝廷、宋州、徐州',note='刺史任命有条件，未实际履行；尽心于主与忠义为郭威答书评价，不改成本站无条件评语。')
add('khitan_withdraws_neiqiu','契丹君主因内丘伤亡与军中忧惧退兵，派使求和',9,'契丹之攻内丘也，','遣使请和于汉。',[('契丹主','内丘战后因忧惧退兵，派使向后汉求和')],year=950,when='950年内丘之役后、后汉亡前的追述，具体撤兵日未载',place='内丘及北还途中',description='史书记内丘战中契丹军伤亡较多，又遇月食与所谓军中异常现象，契丹君主害怕，不再深入，撤兵并派使向后汉求和。',note='月食为史载现象，妖异为军中所见叙述，不当超自然现象已验证；不换算天文日期。')
add('liu_ci_sends_khitan_envoy','后汉灭亡之际，刘词把契丹使者送往大梁',9,'会汉亡，','诣大梁，',[('刘词','以安国节度使身份送契丹使者到大梁')],when='后汉至后周更替期间、951年正月，送达日未载',place='安国至大梁',note='沿既有刘词，不把送使解为主动捕获；使者未具名不建人。')
sup('liu_ci_sends_khitan_envoy',9,letter,'使至境上，會朝廷有蕭墻之變，帝定京城，回至澶州，遇蕃使至，遂與入朝。','《旧五代史》另记使者到边境时遇朝廷内乱，郭威回澶州时遇使者，随后一同入朝。','主书刘词送使与旧本纪郭威遇使细节不完全相同，保留各书记载，不凭省文断两次独立出使。',relation='adds')
add('zhu_xian_khitan_mission','郭威派朱宪出使契丹，说明改朝原因并赠金器玉带',9,'帝遣左千牛卫将军',None,[('郭威','派朱宪回聘，解释改朝原因并赠礼'),('硃宪','以左千牛卫将军身份出使契丹'),('契丹主','成为出使及赠礼对象')],when='951年正月后周建立后，具体出发日未载',place='后周至契丹',note='革命为改朝易代，非现代革命运动；与后晋朱宪无连续履历证据，暂建限定身份。')
sup('zhu_xian_khitan_mission',9,letter,'至是，遣朱憲伴送來使歸蕃，兼致書敘革命之由，仍以金酒器一副、玉帶一遺兀裕。','《旧五代史》也记朱宪陪使者返回，送书说明改朝原因，礼物为金酒器一副、玉带一条。','本段前行写未宪疑转录字，后文朱宪和主书硃宪同一职务任务；保留原文，不建立未宪人物。',relation='adds')
add('wang_yin_yedu_appointment','郭威于乙亥任王殷为邺都留守、天雄节度使，加同平章事',10,'帝以鄴都','仍以侍卫司从赴镇。',[('郭威','选择亲信王殷镇抚河北，任其留守节度并保留统军职'),('王殷','受任邺都留守、天雄节度使、同平章事，仍领军，带侍卫司赴镇')],when='951年正月乙亥',place='邺都',note='原侍卫统军职保留，不把新镇守当辞去军职；腹心为郭威选择亲信的考虑，不造血缘关系。')
sup('wang_yin_yedu_appointment',10,funeral,'夔州節度使、侍衛親軍馬步軍都指揮使、檢校太傅王殷加同平章事，充鄴都留守，典軍如故。','《旧五代史》也记乙亥王殷任邺都留守、加同平章事，并仍统军；原职写夔州节度使。','主书原宁江节度使与旧本纪夔州节度使称法保留，不据官号差异拆同人；旧句未明列新天雄节度使，不补进引文。')
add('guo_mourns_han_emperor','郭威于丙子率百官为刘承祐举哀，采用天子礼',11,'丙子，',None,[('郭威','率百官去西宫为汉隐帝举哀，穿丧服'),('刘承祐','死后获按天子礼举哀')],when='951年正月丙子',place='西宫',note='成服为穿丧服完成礼仪，非现代制服；正式下葬未发生。')
sup('guo_mourns_han_emperor',11,funeral,'丙子，帝赴太平宮，為漢隱帝發喪，百官陪位如儀。','《旧五代史》也记丙子郭威与百官为刘承祐发丧，地点写太平宫。','通鉴西宫、旧太平宫名称不同，保留各书地点称呼，不造已核同一建筑坐标。',relation='conflicts')
add('murong_pays_guo_tribute','慕容彦超派使者向郭威进贡，郭威下诏安抚',12,'慕容彦超',None,[('慕容彦超','派使者进贡，收到郭威安抚诏'),('郭威','担心慕容彦超疑惧，诏称兄弟请求扶持')],when='951年正月丙子礼后条下，具体遣使日未载',place='慕容彦超镇与后周朝廷',note='诏称兄弟是政治称呼，不建立郭威慕容血亲；担心疑惧为郭威考量，不断言其已反叛。')
add('liu_yun_killed_songzhou','刘赟于戊寅在宋州被杀',13,'戊寅，',None,[('赟','在宋州被杀')],when='951年正月戊寅',place='宋州',note='底本湘阳公与前后湘阴公身份、宋州上下文对应刘赟，原字保留，不另建湘阳公；句未写具体执行者，不补郭崇威亲手杀。')
claim('person',people['刘赟'],'death_year','《资治通鉴》记刘赟于951年正月戊寅在宋州被杀。',13,Q[13]['text'],'明确主书死亡年，其他书950年十二月死的写法并列。')
sup('liu_yun_killed_songzhou',13,funeral,'戊寅，湘陰公殂。','《旧五代史》也记正月戊寅湘阴公刘赟去世。','旧本纪用殂，不明杀害执行者；与主书被杀措辞差异保留，不从殂推自然死亡。',field='time_original')
sup('liu_yun_killed_songzhou',13,dec,'王峻遣郭崇以騎七百逆劉贇于宋州，殺之，','《新五代史》周本纪把郭崇在宋州杀刘赟列在950年十二月。','与通鉴及旧周本纪951年正月戊寅不同，保留时间和执行主体差异；不造两次刘赟死亡。',relation='conflicts',field='time_original')
add('liu_chong_northern_han_accession','刘崇于戊寅在晋阳称帝，仍用乾祐年号',14,'是日，','仍用乾祐年号，',[('刘崇','在晋阳称帝，继续用乾祐年号')],when='951年正月戊寅',place='晋阳',note='是日承前戊寅。国称汉、站内称北汉区分后汉，不写此时复活刘承祐。')
sup('liu_chong_northern_han_accession',14,new,'戊寅，漢劉崇自立于太原。','《新五代史》也记戊寅刘崇在太原自立。','太原与晋阳按史载名称保留，未经地理校核不填坐标。',field='time_original')
sup('liu_chong_northern_han_accession',14,access,'周廣順元年正月，崇僭號於河東，稱漢，改名旻，仍以乾祐為年號。','《旧五代史》还记刘崇称汉并改名刘旻，继续使用乾祐年号。','僭号为史家评价，不作为本站中立称谓；刘旻为既有刘崇主体别名，不新建人。',relation='adds')
claim('person',people['刘崇（刘知远弟）'],'name','刘崇称帝后改名刘旻。',14,'周廣順元年正月，崇僭號於河東，稱漢，改名旻，仍以乾祐為年號。','沿既有规范主体与别名保存改名事实；旧传称刘知远从弟，与主书弟说法保留，不静默改成堂弟。',source=access)
claim('person',people['刘崇（刘知远弟）'],'description','《旧五代史》称刘崇为刘知远的从弟。',14,'劉崇，太原人，漢高祖之從弟也。','主书及既有主体称弟，旧传从弟是亲属异说，未创建同胞或堂兄弟新关系。',source=bg,relation='conflicts')
add('northern_han_twelve_prefectures','北汉建立时据有并州等十二州',14,'所有者','十二州之地。',[('刘崇','建立的北汉据有十二州')],when='951年正月刘崇称帝时的疆域记述',place='并、汾、忻、代、岚、宪、隆、蔚、沁、辽、麟、石十二州',note='州名保留史载，不将古州边界等同现代行政区；本批不绘制未经证据核定疆界。')
for code,name,title,start,end in [('zheng_gong_minister','郑珙','中书侍郎、同平章事','以节度判官郑珙','并同平章事。'),('zhao_hua_minister','赵华','户部侍郎、同平章事','观察判官荥阳赵华','并同平章事。'),('liu_chengjun_guard','承钧','侍卫亲军都指挥使、太原尹','以次子承钧','太原尹，'),('li_cungui_daizhou','李存瑰','代州防御使','以节度副使李存瑰','为代州防御使，'),('zhang_yuanhui_guard','张元徽','马步军都指挥使','裨将武安张元徽','为马步军都指挥使，'),('chen_guangyu_xuanhui','陈光裕','宣徽使','陈光裕','为宣徽使。')]:
 add(code,'刘崇任命'+ALIASES.get(name,name)+'为'+title,14,start,end,[('刘崇','称帝后任命官员'),(name,'受任'+title)],when='951年正月戊寅称帝后的任命，具体授职日未另列',place='北汉朝廷',note='任命句中的“并”表明郑珙、赵华都获同平章事衔。李存瑰复用947年任河东副留守的人物档案；任职内容依原文登记，没有推定实际到任日期。')
# Zheng's joint chancellor rank requires the full shared appointment sentence.
claim('event',E['zheng_gong_minister'],'description','郑珙与赵华都获同平章事衔。',14,'以节度判官郑珙为中书侍郎，观察判官荥阳赵华为户部侍郎，并同平章事。','“并”指郑珙和赵华二人，共同任命句明确支持两人都获同平章事衔。')
sup('zheng_gong_minister',14,access,'以判官鄭拱、趙華為宰相，','《旧五代史》也记两判官为宰相，郑珙写作郑拱。','同判官、同伴赵华和同次任命场景对应；保留拱珙异字，不猜另一个新宰相。')
sup('liu_chengjun_guard',14,access,'署其子承鈞為侍衛親軍都指揮使、太原尹，','《旧五代史》也记刘承钧是刘崇之子，任侍卫亲军都指挥使、太原尹。','两书父子与职务相符，次子排行只由主书支持，不算旧传独立证明次序。')
relationship('刘崇','刘承钧','父亲',14,'以次子承钧为侍卫亲军都指挥使、太原尹，','刘崇是刘承钧父亲，次子指排行，不据此补母亲或兄弟名单。')
add('liu_chong_laments_han_fall','刘崇向李存瑰、张元徽感叹汉业倾覆，称即位不得已',15,'北汉主谓','汝曹是何节度使邪！”',[('北汉主','感叹刘知远事业倾覆，称帝为不得已'),('李存瑰','听刘崇表达对新位号的感慨'),('张元徽','听刘崇表达对新位号的感慨')],when='951年正月北汉建立后，具体谈话日未载',place='北汉朝廷',note='不得已是刘崇自述，不当验证其动机；何节度使是感叹，未给张新增节度任命。')
add('northern_han_no_ancestral_temple','北汉初不建宗庙，祭祀采用家族方式',15,'由是不建宗庙，','祭祀如家人，',[('北汉主','未建宗庙，按家族方式祭祀')],when='北汉建立后的初期制度概述，具体起止年日未载',year=None,place='北汉',note='制度概述不强当951年某日颁诏，也不推国家从未祭祖。')
add('northern_han_low_salaries','北汉宰相月俸百缗、节度使三十缗，史书称官吏少廉洁',15,'宰相俸钱','故其国中少廉吏。',[],when='北汉初期官俸与吏治概述，具体实施年月未载',year=None,place='北汉',description='史书记北汉宰相月俸只有百缗，节度使三十缗，其他官员俸给也不多，并据此评价北汉官吏少有廉洁者。',note='缗保留古货币单位，节度三十承前月俸语境；少廉吏是史家评价，不推出每位具名官员贪污。')
add('li_guangmei_former_direct','李光美此前曾任直省官，熟悉典章制度',15,'客省使河南李光美','颇谙故事，',[('李光美','河南人、客省使，曾任直省官，熟悉旧制')],when='北汉建立以前或初期的履历概述，具体任直省年未载',year=None,place='河南籍贯、任职地点未详',note='故事为旧制成例，不译传说故事；河南是籍贯不直接当当前工作地点。')
add('li_guangmei_court_institutions','李光美为北汉朝廷安排制度',15,'北汉朝廷制度，','皆出于光美。',[('李光美','参与安排北汉朝廷制度')],when='北汉建立后的制度概述，具体安排年日未载',year=None,place='北汉朝廷',note='皆是史家概括，未列制度清单不虚构各机构；不把安排制度与直省旧任混为同日。')
add('liu_chong_mourns_yun','刘崇得知刘赟死亡，哭泣并后悔未听李骧建议',15,'北汉主闻','以至于此！”',[('北汉主','得知儿子死讯，哭泣并后悔未听忠臣建议'),('赟','其死讯引起父亲哀哭')],when='951年正月戊寅刘赟死后，具体闻讯日未载',place='北汉',note='不用忠臣之言承前李骧劝谏，但不补未载消息使者或到达日。')
add('liu_chong_li_xiang_shrine','刘崇为李骧立祠，按时祭祀',15,'为李骧',None,[('北汉主','为李骧立祠并按时祭祀'),('李骧','死后获立祠祭祀')],when='951年北汉建立、得知刘赟死后，具体立祠日未载',place='北汉',note='岁时为按时节例行，不算祭次数或猜祠址。')
sup('liu_chong_li_xiang_shrine',15,counsel,'旻慟哭，為李驤立祠，歲時祠之。','《新五代史》也记刘崇哀哭并为李骧立祠，按时祭祀。','《新五代史》把立祠放在刘崇请求儿子归藩、得知儿子已死之后；与《资治通鉴》的叙述顺序分别保留。')
reviews={8:'追述刘承祐死后拟出兵、李骧劝、杀李及妻属950；废赟后求归和拒徐州跨年起始未定，年null。新旧请求使者名单及刘已死时序异说并列，私用姓名字不猜。答书封王刺史承诺未兑现，董妻方向明，巩廷美按守徐同场别名沿巩延美，旧从河东出使同名不强认。',9:'契丹内丘后退军求和属950追述，月食妖异保留史载不作超自然确证。刘词送使和郭遇使细节并列。朱宪无连续身份履历，与后晋同名暂分限定主体；旧本纪未宪异字不新建人。',10:'乙亥王殷留守天雄同平章事仍统军，沿后汉后周将；主宁江与旧夔州原职称法保留。',11:'丙子哀服为实际礼仪，西宫与旧太平宫地点异称不强合，尚未下葬。',12:'进贡与诏安抚政治称兄弟，不造血亲也不写已经反叛。',13:'湘阳公与湘阴公同一刘赟，原字留校核；主旧951戊寅与新周本纪950十二月死亡不同并列，未据新书创造二次死亡或未载执行者。',14:'戊寅即位、保乾祐、旧改名旻与十二州、六任官分录。郑拱珙同官同伴场景对应但不静默改引；李存瑰沿947河东副留守，次子承钧与父关系明确，旧从弟主弟亲属异说并列。',15:'权位感叹为刘自述，无宗庙、官俸及吏治概述、李光美旧任和制度安排年日未定年null，不把所有制度强系某日；闻子死和立祠在死后，不强套同日。'}
assert not (P/'publication.json').exists()
for n in range(8,16):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=290,year=951,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(8,16)],next_paragraph=Q[16]['id'],next_volume=290,next_year=951,supplements=supplements,excluded_non_body=[],coverage='卷290原13—20行连续八段；发布后首15/82正文完成，余67段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(8,16)],source_issues_review='求归书信使者及死前死后时序、新周本纪与主旧刘赟死年、刘崇弟从弟亲属异说并列。私用字与未宪湘阳郑拱等底本异字保留，未作无证据姓名改写。朱宪与晋内职同人待核；王殷原官号和丧礼地点异称保留。身份、时间、原文和卷题已逐段核对，纸本与转录异文待核。',plain_language_review='首次检查全部展示标题说明、人物介绍、关系参与动作及事实说明，现代白话且引文原字保留。计划、评价、自述、承诺、旧履历与执行区分；未知年月为null，不安排固定二次文案review。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
