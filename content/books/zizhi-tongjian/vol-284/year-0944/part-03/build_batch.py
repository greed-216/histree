# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,45))
COMMIT='bffff83c141adc9ef801434ad426164254e8ca01'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-284-944-march-april','jiuwudaishi-082-944-april','xinwudaishi-009-944-january','xinwudaishi-065-liu-sons']:
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
main_sources = ['tongjian-284-944-march-april','tongjian-284-944-may-august']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0944-p017-p024',
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
lines = (ROOT / 'resources/derived/tongjian/284.txt').read_text().splitlines()
for n in range(17, 25):
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
    for a,b in [('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        month = '四月条下及追述' if n==17 else '条目未另列月份，补证或追述另说明' if n<=21 else '六月条下' 
        citation = f'卷284·后晋天福九年、后称开运元年（944；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0944_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=944, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='944年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_284_0944_' + code
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
        edge = 'participation_zztj_284_0944_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_284_0944_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
def extra(code,title,n,source,quote,actors,**kw):
 E[code]=event(code,title,n,quote,actors,source=source,**kw);return E[code]

ALIASES.update({'帝':'石重贵','汉主':'刘弘熙','唐主':'李璟','硃文进':'朱文进','杨光远':'杨檀','弘弼':'刘弘弼','刘翰':'刘翰（淄州刺史）'})
NEW_ALIASES={'梁进':['梁進'],'卢亿':['盧億'],'张仁愿':['張仁願'],'薛可言':[],'刘翰（淄州刺史）':['刘翰','劉翰']}
NEW_DESCRIPTIONS={
'梁进':'后晋沿河巡检使。944年四月丁未率乡社兵收复德州，《新五代史》也记其击败契丹、取回德州。尚无证据将他与梁进超合并。生卒年未载。',
'卢亿':'后晋河南留守判官，河南人。944年劝景延广停止借军费征收增加民众负担。《宋史》卢多逊传记载其父卢亿同一劝谏，补充其字子元。生卒年本次引文未载。',
'张仁愿':'后晋大理卿，944年任征收民财的使者，前往兖州征钱十万缗，从安审信私藏中取钱完成征收。具体生卒年本段未载。',
'薛可言':'堂阳人，后晋齐州防御使。944年拦截并击败援救青州的契丹军。生卒年本段未载。',
'刘翰（淄州刺史）':'杨光远任命的淄州刺史，944年六月后晋军攻克淄州后被杀。《资治通鉴》记辛酉，《旧五代史》记辛丑朔，两书日期异说保留。与早期梁将刘捍分开。出生年未载。'}
apr='jiuwudaishi-082-944-april';may='jiuwudaishi-082-944-may';jun='jiuwudaishi-082-944-june';ann='xinwudaishi-009-944-january';rem='xinwudaishi-029-jing-removal';drink='xinwudaishi-029-jing-drinking';lu='songshi-264-lu-yi-advice';sons='xinwudaishi-065-liu-sons'

# 17: recapture, return journey, command changes and wartime exactions.
add('liang_recaptures_dezhou','梁进率乡社兵收复德州',17,'夏，四月，丁未，','复取德州。',[('梁进','以沿河巡检使身份率乡社兵收复德州')],when='944年四月丁未',place='德州')
sup('liang_recaptures_dezhou',17,ann,'夏四月，契丹陷德州，沿河巡檢使梁進敗之，取德州。','《新五代史》记四月梁进击败契丹，收复德州。','沿河与缘河职衔用字分别保留；该书未列收复的具体日。')
add('gao_wang_stay_chanzhou','后晋命高行周、王周留镇澶州',17,'己酉，','留镇澶州。',[('帝','命高行周、王周留守澶州'),('高行周','受命留镇澶州'),('王周','受命留镇澶州')],when='944年四月己酉',place='澶州')
sup('gao_wang_stay_chanzhou',17,apr,'己酉，詔取今月八日車駕還京，令高行周、王周留鎮澶淵，近地兵馬委便宜制置。','《旧五代史》也记己酉命高行周、王周留守澶州，允许他们处理附近军队事务。','诏令安排皇帝本月八日还京与实际抵京分别记录，不把命令日当抵达日。',relation='adds')
add('emperor_leaves_chanzhou','石重贵离开澶州',17,'庚戌，','帝发澶州；',[('帝','离开澶州')],when='944年四月庚戌',place='澶州')
add('emperor_returns_daliang','石重贵抵达大梁',17,'甲寅，','至大梁。',[('帝','从澶州返回大梁')],when='944年四月甲寅',place='大梁')
sup('emperor_returns_daliang',17,apr,'甲寅，至自澶州，曲赦京城大辟以下罪人。','《旧五代史》同样记甲寅皇帝从澶州回京，并赦免京城死罪及以下罪人。','赦免范围为京城，不能扩大为全国大赦。',relation='adds')
extra('capital_pardon_after_return','后晋皇帝回京后赦免京城死罪及以下罪人',17,apr,'甲寅，至自澶州，曲赦京城大辟以下罪人。',[('帝','回京后赦免京城死罪及以下罪人')],when='944年四月甲寅',place='京城大梁',note='大辟是死罪；保留京城范围，不扩展为天下赦免。')
add('sang_accuses_jing_failure','桑维翰指出景延广不救戚城的过失',17,'桑维翰引','不救戚城之罪，',[('桑维翰','指出景延广没有救援戚城的过失'),('景延广','被桑维翰指出未救戚城的过失')],when='944年四月景延广调任前，具体日期未载',place='后晋朝廷',note='记录桑维翰提出的理由；救援战事已有前批事件，不再次建立同一场战斗。')
add('jing_removed_to_west_capital','后晋授景延广兼侍中，调任西京留守',17,'辛酉，加延广','西京留守。',[('帝','授景延广兼侍中，调任西京留守'),('景延广','获兼侍中职衔，调任西京留守')],when='944年四月辛酉',place='西京洛阳')
sup('jing_removed_to_west_capital',17,apr,'辛酉，以鄆州節度使、侍衛親軍都指揮使景延廣為西京留守；','《旧五代史》也记四月辛酉景延广由郓州节度使、侍卫亲军都指挥使转任西京留守。','各书保留职衔表述；调任不另建景延广同名主体。')
sup('jing_removed_to_west_capital',17,rem,'契丹去，出帝還京師，乃出延廣為河南尹，留守西京。','《新五代史》记契丹退去、皇帝回京后，景延广出任河南尹、留守西京。','本传补河南尹职衔；同段末尾明年再随北征属于后续，不提前录入。',relation='adds')
add('gao_takes_guard_command','高行周接任侍卫马步都指挥使',17,'以归德节度使','为侍卫马步都指挥使。',[('高行周','由归德节度使兼侍中接任侍卫马步都指挥使')],when='944年四月辛酉景延广调任时',place='后晋')
sup('gao_takes_guard_command',17,apr,'以宋州節度使高行周為侍衛親軍都指揮使；','《旧五代史》也记高行周接任侍卫亲军都指挥使。','归德军所在宋州与宋州节度职衔对应；不把府镇与人名分成两个将领。')
add('jing_drinks_after_removal','景延广调任后忧惧国破身危，日夜饮酒',17,'延广郁郁','遂日夜纵酒。',[('景延广','调任后忧惧国破身危，日夜饮酒')],when='944年四月调任西京后开始，持续时间未载',place='西京洛阳',note='失意、忧惧是史书记述的心理，不写成独立测量事实；不由饮酒推死亡或病名。')
sup('jing_drinks_after_removal',17,drink,'延廣居洛陽，鬱鬱不得志。見晉日削，度必不能支契丹，乃為長夜之飲，大治第宅，園置妓樂，惟意所為。','《新五代史》还记景延广居洛阳后夜饮、扩建宅院，并在园中设置歌舞娱乐。','本传补生活细节，持续期间未载；后文议和及中渡军败不提前录入。',relation='adds')
add('court_sends_exaction_agents','后晋派三十六名使者持剑分路征收民财',17,'朝廷因契丹入寇，','各封剑以授之。',[('帝','派三十六名使者分路征收民财，授予封装的剑')],when='944年四月，主书未列具体日；旧史记辛酉',place='后晋各地',note='史书将征收与战后军费紧缺联系起来；使者三十六人未逐个具名，不造人物。')
sup('court_sends_exaction_agents',17,apr,'是日，分命文武臣僚三十六人往諸道州府括率錢帛，以次軍用。','《旧五代史》将三十六人分路征收钱帛记在四月辛酉，说明用于军费。','是日承接景延广调任辛酉，作为该书纪日保存；文武臣僚与主书携吏卒的实施者分清。',relation='adds',field='time_original')
sup('court_sends_exaction_agents',17,ann,'辛酉，率借民財。','《新五代史》也记四月辛酉征借民财。','该书没有在这句话给出人数、持剑或征收总额，不据其单句补这些细节。')
add('agents_coerce_households','征财使者携吏卒和刑具进入民家，民众惊惧',17,'使者多从吏卒，','求死无地。',[],when='944年四月分路征财期间',place='后晋各地民家',note='锁械、刀仗及惊惧依原文记录；不补每户征额或死亡总数。')
add('local_officials_abuse_exactions','州县官吏借征收民财之机作奸牟利',17,'州县吏复','因缘为奸。',[],when='944年四月征收民财期间',place='后晋州县',note='原文没有列举全部具体违法手法，不自行补刑罚和涉案官员姓名。')
add('henan_twenty_wan_quota','河南府承担二十万缗征款',17,'河南府出','二十万，',[],when='944年四月征收民财期间',place='河南府',note='出二十万结合宋史计出视为核定额，不断言已全部向民众实收。')
sup('henan_twenty_wan_quota',17,lu,'河南府計出二十萬緡，','《宋史》也记河南府核定征收二十万缗。','卢多逊传中叙述其父卢亿事迹，核对传主后引用；该句不保证征款全部缴纳。')
add('jing_increases_henan_quota','景延广将河南府征款增加到三十七万缗',17,'景延广率','三十七万。',[('景延广','把河南府征款增加到三十七万缗')],when='944年四月征收民财期间',place='河南府',note='不写三十七万在原二十万之外另加；是否实收全部不明确。')
sup('jing_increases_henan_quota',17,lu,'延廣欲並緣以圖羨利，增為三十七萬緡。','《宋史》明确景延广借征款牟利，将二十万增加为三十七万缗。','补增加额度与牟利的书证说明，不将多征部分全部写成已进私库的完成结果。',relation='adds')
add('lu_yi_advises_jing','卢亿劝景延广停止借军费征收牟利',17,'留守判官河南卢亿','为子孙之累乎！”',[('卢亿','以留守判官身份劝景延广不要借征款牟利'),('景延广','受到卢亿劝谏')],when='944年四月河南府加征民财时',place='河南府',note='这是卢亿的劝谏，所说为子孙之累不写成后代已经获罪。')
sup('lu_yi_advises_jing',17,lu,'億諫曰：“公位兼將相，既富且貴。今國帑空竭，不得已而取貲於民，公何忍利之乎？”延廣慚而止。','《宋史》也记卢亿劝景延广不要从军费征款中牟利，景延广惭愧后停止。','此处父亿承接开头卢多逊之父，沿用同一卢亿主体。')
claim('person',people['卢亿'],'description','《宋史》卢多逊传称其父卢亿字子元，并记卢亿在景延广留守西洛时任判官。',17,'父億，字子元，少篤學，以孝悌聞。','父亿在传主卢多逊开头，可确定为卢亿；不将其父辈名字误作另一传主。',source=lu,relation='adds')
claim('person',people['卢亿'],'description','《宋史》记景延广留守西洛时再次推荐卢亿任判官。',17,'留守西洛，又表為判官。','上下文景延广推荐卢亿；职衔支持当前留守判官，不提前其后周朝任官。',source=lu,relation='adds')
add('jing_stops_excess_exaction','景延广听从卢亿劝谏，停止额外加征牟利',17,'延广惭','而止。',[('景延广','听取卢亿劝谏后停止借征款牟利')],when='944年四月卢亿劝谏后',place='河南府',note='止承接借征款牟利，不等于后晋撤销全部军费征收；不虚造已退还全部款项。')
add('yanzhou_defense_order','后晋因杨光远叛乱，命兖州修整防御设施',17,'先是，诏','命兗州修守备。',[('帝','因杨光远叛乱命兖州修整防御设施')],year=None,when='杨光远943年末叛乱后、944年征财前的追述，确切年月未载',place='兖州',note='先是追述不强定为四月；诏令和安审信实际筹款分别处理。')
add('an_shenxin_private_exaction','安审信借修城防之名征收民财，放入私库',17,'泰宁节度使安审信，','以实私藏。',[('安审信','以修城楼女墙为名征收民财，充实私库')],year=None,when='上述兖州修备诏之后、944年张仁愿征款前，确切年月未载',place='兖州',note='楼堞是城楼及女墙；私藏依原文明确，不补总额或库房坐标。')
add('zhang_renyuan_yanzhou_quota','张仁愿到兖州征收十万缗',17,'大理卿张仁愿','赋缗钱十万。',[('张仁愿','以征款使者身份到兖州，核征十万缗')],when='944年四月分路征款期间',place='兖州',note='括率使是此次使职，不变成新的终身官职。')
add('zhang_seizes_an_private_money','张仁愿拘押安审信的守库吏，从私藏取足征款',17,'值审信不在，',None,[('张仁愿','在安审信不在时拘押守库吏，从库中取足十万缗'),('安审信','私藏被张仁愿取作征款，当时不在场')],when='944年四月张仁愿征款期间',place='兖州安审信私库',note='一囷取钱已满十万，原文不记私库全部财产总额；守藏吏没有姓名，不补人物。')
extra('jing_receives_imperial_clothes','石重贵在宫中宴请景延广，赐御衣和宝带',17,apr,'癸亥，以西京留守安彥威為晉昌軍節度使，以晉昌軍節度使趙瑩為華州節度使，以左龍武統軍皇甫遇為滑州節度使。是日，置酒宮中，召景延廣謂之曰：「卿有佐命之功，命保釐伊、洛，非酬勛之地也。」因解禦衣、寶帶以賜之。',[('帝','宴请景延广，说明调任理由并赐御衣宝带'),('景延广','受皇帝宴请，获御衣和宝带')],when='944年四月癸亥',place='后晋宫中',note='是日承接癸亥；前句其他调任仅作为纪日上下文，不在此事件加入其参与者。')

# 18–20: May dating comes from separately cited annals; the Tongjian month heading is absent.
add('li_shouzhen_qingzhou_campaign_order','后晋命李守贞率两万步骑讨伐青州杨光远',18,'戊寅，','于青州，',[('帝','命李守贞率两万步骑讨伐杨光远'),('李守贞','受命率两万步骑讨伐青州杨光远'),('杨光远','成为青州讨伐行动的对象')],when='944年戊寅；新旧五代史明确为五月戊寅',place='青州',note='此处主书未另列五月标题；依新旧本纪保留五月补证，不将其误系四月。命率兵与青州后来陷落分别录。')
sup('li_shouzhen_qingzhou_campaign_order',18,may,'戊寅，遣侍衛親軍都虞候李守貞率步騎二萬，討楊光遠於青州。','《旧五代史》五月条同样记戊寅李守贞率两万步骑讨杨光远。','原段五月壬申朔给出月份，补主书月标题省略问题，人物杨光远复用杨檀。',relation='adds',field='time_original')
sup('li_shouzhen_qingzhou_campaign_order',18,ann,'五月戊寅，李守貞討楊光遠。','《新五代史》也明确记五月戊寅李守贞讨杨光远。','该书简述未写两万，不单独据此补兵数。')
claim('person',people['李守贞'],'description','《旧五代史》记四月辛酉李守贞改任兖州节度使，仍主管原来的军职。',18,'以侍衛親軍都虞候、義成軍節度使李守貞為兗州節度使，典軍如故。','补泰宁节度使来历，任命日依同段辛酉；不覆盖既有主体档案。',source=apr,relation='adds')
add('pan_zhang_garrison_chanzhou','后晋派潘环、张彦泽等驻澶州防备契丹',18,'又遣神武统军','以备契丹。',[('帝','派潘环、张彦泽等驻澶州'),('潘环','奉命率兵驻澶州防备契丹'),('张彦泽','奉命率兵驻澶州防备契丹')],when='944年李守贞出兵前后；主书未另列本项具体日',place='澶州',note='潘环为洛阳籍神武统军，复用已录主体；不将青州两万兵数分配给驻澶州部队。')
add('khitan_sends_qingzhou_relief','契丹派兵援救青州',18,'契丹遣兵','救青州，',[],when='944年李守贞讨青州期间，具体日期未载',place='青州方向',note='契丹援军领将与兵数未载，不补耶律德光亲自领兵。')
add('xue_intercepts_khitan_relief','薛可言拦截并击败契丹援军',18,'齐州防御使','败之。',[('薛可言','以齐州防御使身份拦截并击败援青州契丹军')],when='944年上述青州救援期间，具体日期未载',place='援青州途中，具体交战地点未载',note='堂阳是薛可言籍贯，齐州是职务所在地；不据此强定战场在堂阳或齐州。')
add('wuding_army_proclamation','后晋将已登记乡兵命名为武定军，共七万余人',19,'丙戌，','七万馀人。',[('帝','下诏将已登记乡兵命名为武定军，记总数七万余人')],when='944年丙戌，此条主书未另列月份',place='后晋各州',note='三月旧纪已提武定军号，主书此处是另一条公布命名与登记总数的记载，不覆盖三月引用或虚构两支军队。')
claim('event',E['wuding_army_proclamation'],'time_original','《新五代史》在三月癸巳已经记载登记民众为武定军。',19,'癸巳，籍民為武定軍。','同一军号在不同编年位置分别保存；这句无七万数字，不用于独立确证总数。',source=ann,relation='adds')
add('rural_recruitment_hardship','史书记战乱之后再征乡兵，民众难以维生',19,'时兵荒之馀，',None,[],when='944年乡兵征集期间',place='后晋各州',note='民不聊生为史书对生计状况的概述，不换算为确定死亡人口或全国收入。')
add('zhang_requests_attack_beizhou','张从恩建议迅速进攻贝州，称赵延照部众思归',20,'丁亥，','宜速进军攻之。”',[('张从恩','建议迅速攻贝州，称守军久客思归'),('赵延照','其部众被张从恩描述为久客思归')],when='944年丁亥；旧史本纪将张从恩受命记在五月丁亥',place='贝州',note='部众思归为张从恩在奏议中的判断，不写成本站独立证实的全体士兵心理。')
add('zhang_beizhou_campaign_command','后晋任命张从恩为贝州行营都部署',20,'诏以从恩','督诸将击之。',[('帝','任命张从恩统率诸将攻贝州'),('张从恩','受任贝州行营都部署，督诸将进攻')],when='944年丁亥；新旧五代史明确五月丁亥',place='贝州',note='任命与实际军队攻入贝州的结果分开，不补未载战斗过程。')
sup('zhang_beizhou_campaign_command',20,ann,'丁亥，鄴都留守張從恩為貝州行營都部署。','《新五代史》五月条也记丁亥张从恩任贝州行营都部署。','丁亥承接五月戊寅，明确同一五月任命。',relation='adds',field='time_original')
extra('beizhou_campaign_officer_appointments','后晋任皇甫遇、潘环、张彦泽参与贝州行营',20,may,'以滑州節度使皇甫遇為行營都虞候，以左神武統軍潘環掌騎兵，右神武統軍張彥澤掌步兵。',[('皇甫遇','受任行营都虞候'),('潘环','在行营主管骑兵'),('张彦泽','在行营主管步兵')],when='944年五月丁亥任张从恩的同条记载',place='贝州行营',note='官职任命属于张从恩行营，不把潘骑张步当作前段驻澶州所有部队的固定结构。')
add('zhao_burns_abandons_beizhou','张从恩奏报赵延照焚掠贝州后弃城逃走',20,'辛卯，','弃城而遁，',[('张从恩','奏报赵延照焚掠并弃城逃走'),('赵延照','据奏报焚掠贝州后弃城逃走')],when='944年辛卯是奏报日；旧史记五月辛卯，行动具体日未载',place='贝州',note='奏报日与焚掠弃城发生日分开；未写晋军经战斗攻克，不另造围攻成功场面。')
sup('zhao_burns_abandons_beizhou',20,may,'辛卯，張從恩奏，貝州賊將趙延昭縱火大掠，棄城而遁。','《旧五代史》五月条同样记辛卯张从恩奏报赵延昭焚掠弃城。','正文支持报告；紧随的通鉴注文是引同书，不能算独立第三层证据。',relation='adds',field='time_original')
add('zhao_entrenches_yingmo','据张从恩奏报，赵延照退驻瀛州、莫州，依水自守',20,'辛卯，从恩奏','阻水自固。',[('张从恩','报告赵延照退驻瀛莫、依水自守'),('赵延照','据报告退驻瀛莫，依水自守')],when='944年五月辛卯奏报所述，实际驻屯日未载',place='瀛州、莫州',note='记入奏报来源，不把瀛莫两地精确扎营坐标或退却路线绘成已核实。')
extra('li_fu_qingzhou_campaign_appointments','后晋任李守贞为青州行营都部署，符彦卿为副',20,may,'以李守貞為青州行營都部署，以河陽節度使符彥卿副之。',[('李守贞','受任青州行营都部署'),('符彦卿','受任青州行营副职')],when='944年五月辛卯条下',place='青州行营',note='正式行营职衔与此前戊寅派军命令分别记录；副之未给完整副职名称，不强补他书官号。')

# 21–24: an unrealized campaign, a city seizure, cabinet change and confinement.
add('zhu_sends_envoy_to_tang','朱文进派使者前往南唐',21,'硃文进遣使','如唐，',[('硃文进','派使者前往南唐')],when='944年六月记载之前，具体月日未载',place='闽国至南唐',note='使者姓名和使命细节未载，不虚构与李璟的会谈或获得正式承认。')
add('tang_detains_zhu_envoy','李璟囚禁朱文进的使者',21,'唐主囚','其使，',[('唐主','囚禁朱文进派来的使者')],when='944年朱文进遣使之后，具体月日未载',place='南唐',note='不补囚禁地点、时长、使者死亡或受刑。')
add('tang_plans_attack_zhu','李璟准备讨伐朱文进',21,'唐主囚其使，','将伐之，',[('唐主','准备讨伐朱文进'),('硃文进','成为南唐拟讨伐的对象')],when='944年上述扣使之后，具体月日未载',place='南唐至闽国方向',note='将伐是准备，不能提前记为实际攻下福州或建州。')
add('tang_stops_campaign_heat_epidemic','南唐因暑热和疫病停止讨伐朱文进的计划',21,'会天暑、',None,[('唐主','因暑热和疫病停止当前讨伐计划')],when='944年上述拟征期间，具体月日未载',place='南唐',note='不补疫情名称、死亡人数或具体军队已到哪里；后续唐兵攻建州另按主线录入。')
add('jin_captures_zizhou','后晋军攻克淄州',22,'六月，辛酉，','官军拔淄州，',[],when='944年六月辛酉；旧史异记辛丑朔',place='淄州',note='官军将领本句未具名，不直接用附近李守贞任命补成他亲自领攻。')
sup('jin_captures_zizhou',22,jun,'六月辛丑朔，王師拔淄州，斬楊光遠偽署刺史劉翰。','《旧五代史》记六月辛丑朔后晋军攻取淄州，斩杨光远任命的刺史刘翰。','辛丑朔与主书辛酉不同，保存纪日异说，不改原字或自动换算。',relation='conflicts',field='time_original')
sup('jin_captures_zizhou',22,ann,'六月，克淄州。','《新五代史》也记六月攻克淄州。','本纪未列具体日，不能据其证明辛酉或辛丑朔孰是。')
add('jin_executes_zizhou_liu_han','后晋军攻克淄州后杀死刺史刘翰',22,'六月，辛酉，',None,[('刘翰','淄州被攻克后被后晋军杀死')],when='944年六月辛酉；旧史异记辛丑朔',place='淄州',note='本次杨光远任命的刺史与早期刘捍分开；不把其名改为翰林官或未载亲属。')
sup('jin_executes_zizhou_liu_han',22,jun,'斬楊光遠偽署刺史劉翰。','《旧五代史》明确刘翰是杨光远任命的淄州刺史。','支持任官来源和死亡，完整同段纪日异说已另列。',relation='adds')
claim('person',people['刘翰（淄州刺史）'],'death_year','淄州刺史刘翰在944年六月被后晋军杀死，两书记日不同。',22,'六月，辛酉，官军拔淄州，斩其刺史刘翰。','死亡年份明确，辛酉与旧史辛丑朔异说分别保留，不同名合并。')
add('feng_daos_indecision','史书记冯道任首相时态度含糊，未作决断',23,'太尉、侍中冯道','无所操决。',[('冯道','被史书描述为首相但缺少决断')],when='944年六月调任前的描述',place='后晋朝廷',note='这是史书对其执政表现的评价，不写成所有事项均无人处理或永久人格结论。')
add('anonymous_criticizes_feng','有人向石重贵批评冯道不适合处理危局',23,'或谓帝曰：','飞鹰耳。”',[('帝','听取对冯道难以应对危局的批评'),('冯道','被不具名者批评不适合处理危局')],when='944年六月冯道调任之前，具体日期未载',place='后晋朝廷',note='禅僧飞鹰是批评者比喻；批评者无名，不猜为桑维翰或景延广。')
add('feng_transferred_kuangguo','后晋调冯道任匡国节度使，兼侍中',23,'癸卯，',None,[('帝','调冯道任匡国节度使，兼侍中'),('冯道','调任匡国节度使，保留兼侍中职衔')],when='944年六月癸卯',place='匡国军')
sup('feng_transferred_kuangguo',23,jun,'癸卯，以太尉、兼侍中馮道為檢校太師、兼侍中，充同州節度使。','《旧五代史》也记六月癸卯冯道任同州节度使，补检校太师职衔。','同州为匡国军所在，按同一任命保留职衔表述，不新增同名实体。',relation='adds')
add('han_confines_hongbi','刘弘熙将齐王刘弘弼囚禁在私宅',24,'乙巳，',None,[('汉主','将齐王刘弘弼囚禁在私宅'),('弘弼','被刘弘熙囚禁在私宅')],when='944年六月乙巳',place='私宅，具体位置未载',note='幽为囚禁，不记为死亡；新史后文五年同日杀诸弟属于947年，留待后续。')
claim('person',people['刘弘弼'],'description','《新五代史》封王记载中，刘洪弼受封齐王。',24,'洪弼齊王，','仅补同一人物齐王称号；原段属早年封王，不新建944年封王事件。',source=sons,relation='corroborates')

reviews={17:'逐项录入德州收复、驻防、皇帝离开与抵达、景延广与高行周调任、饮酒、征款、卢亿劝止、兖州私藏及宫中赐衣。未知年月追述保持null；命令、核定额、实取款与牟利区分。宋史卢多逊传父亿核为卢亿，不混传主。',18:'五月戊寅由新旧史本纪补证；主书未另列月份，不误系四月。青州讨伐、澶州驻防、契丹救援及薛拦截分别记录。堂阳为籍贯不强作战场。',19:'武定军号与七万余统计依本条；三月已记军号作为独立书证并列，不凭此再造两支同名军。民生困难按史书评价记录。',20:'张从恩奏议与任命、赵延照弃城及驻屯分开；五月辛卯是报告日，不强定行动日。旧史引用通鉴的注文不算独立补证。补行营军职与青州副职不造未载具体作战。',21:'朱文进使者赴唐、被囚、南唐准备征伐、因暑疾停止分开；不把计划写成已经攻陷闽国。',22:'淄州攻克与刘翰被斩，主书辛酉、旧史辛丑朔并列；将领无名不强配李守贞。刘翰与早期梁将刘捍分开。',23:'冯道执政评价、不具名者批评与正式调任分开；禅僧飞鹰作为批评者比喻，不猜发言者。匡国军与同州对应。',24:'囚禁刘弘弼不等于死亡；洪弘字沿用主体，早年封齐王只补称号，947年杀诸弟留后续。'}
assert not (P/'publication.json').exists()
for n in range(17,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=944,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],next_volume=284,next_year=944,supplements=supplements,excluded_non_body=[],coverage='卷284原22—29行连续第17—24段，四月至六月及追述；下接第25段恢复枢密院，944全年尚未完成。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'复用原文，仅处理末尾四月长段，前面已发布内容不再新建。'),(main_sources[1],'当前仅处理第18—24段；后续恢复枢密院、水灾、翰林与八月军职留待后续主线。'),(drink,'只补洛阳饮酒生活细节，不提前后续议和与中渡军败。'),(jun,'仅补淄州、冯道调任，后续水灾和学士任命未提前。'),(may,'注引通鉴的内容不算独立证据，只引用本纪正文的五月行动与军职。'),(lu,'核为卷264卢多逊传中的父卢亿，不作为卢多逊现场参与依据。')]],source_issues_review='主书五月月标题省略及淄州辛酉辛丑朔异日保留；未知年追述与新史未来叙事未提前。梁进与梁进超不强合并，刘翰与刘捍分开。电子文本纸本异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,25)],plain_language_review='首次逐项核对标题、说明、人物、参与角色、关系与事实说明；主语与动作明确，命令、意图、报告、评价和实际行动分别处理。引用保留底本原字，时间异说独立展示。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})



