# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 938 paragraphs 21–29."""
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
specs=[(d.name,d,'15cac06f05420ed79060ede111d9764429048842','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-077-september']:
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
main_sources = ['tongjian-281-938-surrender-and-capital']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0938-p021-p029',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-077-september':'卷77·晋高祖纪·天福三年九月','jiuwudaishi-077-october':'卷77·晋高祖纪·天福三年十月','jiuwudaishi-094-li-yanxun':'卷94·李彦珣传'}
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
for n in range(21, 30):
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
    labels={'jiuwudaishi-077-september':'卷77·晋高祖纪·天福三年九月','jiuwudaishi-077-october':'卷77·晋高祖纪·天福三年十月','jiuwudaishi-094-li-yanxun':'卷94·李彦珣传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '九月条下，含追叙及史论' if n<26 else '十月条下，含追叙'
        citation = f'卷281·后晋天福三年（938；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0938_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'赵可封':'南唐太府卿。938年九月建议徐诰恢复李姓并设立唐朝宗庙。此段只记建议，未记已执行；生卒年未载。',
'孙汉威':'范延光的将佐。938年九月获授地方官职，《旧五代史》记为陇州防御使，并列此前贝州刺史职衔。生卒年未载。',
'薛霸':'范延光的将佐。938年九月获授地方官职，《旧五代史》记为卫州刺史，并列此前天雄军三城都巡检使职衔。生卒年未载。',
'李彦珣母（姓名未详）':'李彦珣的母亲，姓名未载。《资治通鉴》《旧五代史》记载，广晋被围时杨光远将她带到城下招降李彦珣，她被李彦珣射杀；具体年月未载。'}
NEW_ALIASES={'赵可封':['趙可封'],'孙汉威':['孫漢威'],'薛霸':[],'李彦珣母（姓名未详）':[]}

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
    if when is None:when='938年九月条下，具体日期未载' if n<26 else '938年十月条下，具体日期未载'
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



ALIASES.update({'唐主':'李昪','燕国长公主':'兴平公主'})
old='jiuwudaishi-077-september';october='jiuwudaishi-077-october';bio='jiuwudaishi-094-li-yanxun'
add('yan_princess_returns_liao','契丹派使者到洛阳接赵延寿的妻子燕国长公主',21,'契丹遣使',None,[('契丹主','派使者到洛阳接燕国长公主'),('燕国长公主','从洛阳被接往契丹')],place='洛阳',note='公主复用李嗣源女、赵延寿妻兴平公主主体，避免按封号变化再建同人；主书未列此事单独日期，不推途中路线。')
sup('yan_princess_returns_liao',21,old,'庚申，契丹使人往洛京般取趙氏公主。','《旧五代史》补充，契丹在九月庚申派人到洛阳接公主。','此日是派人接取的记载；该书丙寅又记允许归幽州，分别保留，不推为同一日到达。',field='time_original')
sup('yan_princess_returns_liao',21,old,'丙寅，趙延壽進馬謝恩，放燕國長公主歸幽州。','《旧五代史》还记九月丙寅赵延寿进马谢恩，朝廷允许燕国长公主归幽州。','主书归契丹、该书归幽州分别说明；不把允许归还直接当作已于丙寅抵达。')
relationship('燕国长公主','赵延寿','妻子',21,Q[21]['text'],'赵延寿妻明确婚姻方向；公主按既有配偶及李嗣源女身份复用兴平公主，不与宋代同封号公主混同。')
add('zhao_kefeng_proposes_li_ancestry','赵可封建议徐诰恢复李姓、设立唐朝宗庙',22,'壬戌，',None,[('赵可封','以太府卿身份建议恢复李姓和设唐宗庙'),('唐主','收到赵可封恢复李姓及设宗庙的建议')],when='938年九月壬戌',note='这是建议，不写成徐诰已在当日恢复李姓或建立宗庙；徐诰沿用李昪主体。')
add('yang_requests_court_visit','杨光远上表请求入朝',23,'庚午，','表乞入朝；',[('杨光远','上表请求入朝')],when='938年九月庚午',note='上表请求与实际朝见分开，此段没有记到达日。')
add('liu_churang_temporarily_tianxiong','石敬瑭命刘处让暂管天雄军府事务',23,'命刘处让','军府事。',[('帝','命刘处让暂管天雄军府事务'),('刘处让','临时负责天雄军府事务')],when='938年九月庚午条下',place='天雄军府',note='权知表示临时负责，不误作永久天雄节度使。')
sup('liu_churang_temporarily_tianxiong',23,old,'遣宣徽南院使劉處讓權知魏府軍府事。','《旧五代史》也记遣刘处让暂管魏府军府事务。','两书所处纪日上下文不同，该书此句接丙寅条，主书庚午条；只印证临时职责，不强行统一纪日。')
add('fan_tianping_iron_charter','石敬瑭任范延光为天平节度使，并赐铁券',23,'己巳，','仍赐铁券，',[('帝','任范延光为天平节度使，赐铁券'),('范延光','被任为天平节度使，获赐铁券')],when='938年九月己巳',place='天平军',note='铁券按史载名称保留，不外推为任意犯罪或终身不死的无条件保证。')
sup('fan_tianping_iron_charter',23,old,source_span(old,'改授鄆州刺史、','仍令擇日備禮冊命。」'),'《旧五代史》补充范延光改授郓州刺史、天平军节度使，赐铁券，改封高平郡王，并令另择日举行册命礼。','册命礼另择日，不认作己巳当天已举行；原文郓齐之后缺一字，保留缺文，不猜补辖州。')
add('guangjin_general_amnesty','石敬瑭赦免广晋军民此前的罪责及城中逃叛人员',23,'应广晋城中','亦释之。',[('帝','赦免广晋将吏军民及城中逃叛人员此前的罪责')],when='938年九月己巳',place='广晋',description='石敬瑭宣布不再追究广晋城内将吏军民截至当日的罪责；张从宾、符彦饶的余党和从官军逃叛入城者也获赦免。',note='张从宾与符彦饶本人不是此时获赦参与者；赦免截止当日，不扩成未来免责。')
add('fan_officers_local_appointments','范延光的将佐李式、孙汉威、薛霸获授地方官职',23,'延光腹心将佐','刺史，',[('李式（范延光节度副使）','获授地方官职'),('孙汉威','获授地方官职'),('薛霸','获授地方官职')],when='938年九月己巳条下',note='主书只概列防御、团练使和刺史，具体对应由旧五代史独立补证，不按原文顺序硬配职衔。')
for name,start,end,role in [('李式（范延光节度副使）','以天雄軍節度副使、','充亳州團練使；','李式获授检校尚书右仆射、亳州团练使。'),('孙汉威','以貝州刺史孫漢威','隴州防禦使；','孙汉威由贝州刺史获授检校太保、陇州防御使。'),('薛霸','以天雄軍三城都巡檢使薛霸','衛州刺史；','薛霸获授检校司空、卫州刺史，此前职衔为天雄军三城都巡检使。')]:
 sup('fan_officers_local_appointments',23,old,source_span(old,start,end),role,'具体职衔由《旧五代史》帝纪补充，不推原职任命年月。')
 claim('person',people[name],'description',role,23,source_span(old,start,end),'人物职衔与参与事件有同一原文依据，展示写简体，原文保留繁体。',source=old)
add('guangjin_troops_imperial_guard','范延光的牙兵被编入侍卫亲军',23,'牙兵皆升','侍卫亲军。',[],when='938年九月己巳条下',place='广晋',note='这是部队编制调整，不将全体牙兵造作一个人物，也不推个别军官具体新职。')
add('li_yanxun_neglects_parents','李彦珣任河阳行军司马时没有供养留在家乡的父母',23,'初，河阳行军司马','未尝供馈。',[('李彦珣','任河阳行军司马，未向家乡父母供给生活所需')],year=None,when='归降前的生涯追述，具体年月未载',place='河阳、邢州',note='此处身份与旧五代史李彦珣传连续经历相合，复用929年赴东川的通事舍人主体；不因转任军职另建同名人物。')
sup('li_yanxun_neglects_parents',23,bio,source_span(bio,'彥珣素不孝於父母，','清泰中，遷河陽行軍司馬，'),'《旧五代史》李彦珣传也记他断绝供养父母，并补清泰年间迁河阳行军司马。','不孝为史书记述评价，采用明确的断供行为，不将清泰年间作为以后所有行动日期。')
add('li_yanxun_joins_zhang_rebellion','李彦珣参与张从宾叛乱，失败后逃往广晋',23,'后与张从宾同反，','奔广晋，',[('李彦珣','参与张从宾叛乱，失败后逃往广晋'),('张从宾','叛乱失败')],year=None,when='张从宾叛乱及失败后的追叙，主书此处未单列年月',place='广晋',note='不凭938年段落位置将叛乱重新定为938年；不新增两人的私交或结义关系。')
add('fan_appoints_li_city_defense','范延光任李彦珣为步军都监，命他登城守卫',23,'范延光以为步军都监，','登城拒守。',[('范延光','任李彦珣为步军都监，并命其守城'),('李彦珣','被任为步军都监，负责守城')],year=None,when='李彦珣逃往广晋之后、范延光归降之前，具体日期未载',place='广晋')
add('yang_uses_li_mother_to_surrender','杨光远将李彦珣的母亲带到城下，试图招降他',23,'杨光远访获其母，','以招之，',[('杨光远','找到李彦珣母亲，将她带到城下试图招降'),('李彦珣母（姓名未详）','被带到城下用于招降儿子'),('李彦珣','在城上受到招降')],year=None,when='广晋被围、范延光归降之前，具体年月未载',place='广晋城下',note='母亲姓名未载，用子身份限定，不猜姓名或其他家世。')
add('li_yanxun_kills_mother','李彦珣在广晋城上射杀自己的母亲',23,'彦王旬引弓','射杀其母。',[('李彦珣','引弓射杀自己的母亲'),('李彦珣母（姓名未详）','被儿子李彦珣射杀')],year=None,when='广晋被围、范延光归降之前，具体年月未载',place='广晋城上、城下',note='彦王旬是本底本拆字，后句彦珣及旧五代史同一经历均写李彦珣，展示规范化姓名，引文不改。')
sup('li_yanxun_kills_mother',23,bio,source_span(bio,'招討使楊光遠以彥珣見用，','發矢以斃之，'),'《旧五代史》也记杨光远找到李彦珣母亲招降，李彦珣认出她后射杀。','原书能确认主体和行动，但没有给射杀单列年月，不强定938年九月。')
relationship('李彦珣母（姓名未详）','李彦珣','母亲',23,span(23,'杨光远访获其母，','射杀其母。'),'其母承接李彦珣，明确她是李彦珣的母亲；原文拆字不另建人物。')
add('li_yanxun_fangzhou','石敬瑭在范延光归降后任李彦珣为坊州刺史',23,'延光既降，','坊州刺史。',[('帝','任命李彦珣为坊州刺史'),('李彦珣','被任命为坊州刺史')],when='938年范延光归降之后，主书未单列任命日',place='坊州',note='归降后身份与旧五代史帝纪、传记相合，不将未列日期的主书条目直接赋己巳。')
sup('li_yanxun_fangzhou',23,old,'以天雄軍都監、前河陽行軍司馬李彥珣為檢校司空、坊州刺史。','《旧五代史》九月己巳任官条补充，李彦珣以天雄军都监、前河阳行军司马身份被任检校司空、坊州刺史。','帝纪给出的任命日期作为独立补证保留，不改主书未单列日期的表述。')
add('shi_refuses_li_murder_prosecution','石敬瑭以赦令已行为由，不再追究李彦珣杀母',23,'近臣言彦珣杀母，',None,[('帝','以赦令已行、不可更改为由，让李彦珣赴任'),('李彦珣','在近臣提出杀母不可赦后仍获准赴任')],description='近臣指出李彦珣杀母的罪行不应赦免。石敬瑭说赦令已行、不可更改，仍让李彦珣赴任。',note='近臣姓名未载，不造姓名；这是此次处置，不等于网站认可杀母免罪，也不推以后没有受到处罚。')
sup('shi_refuses_li_murder_prosecution',23,bio,source_span(bio,'近臣以彥珣之惡逆','遂令赴郡，'),'《旧五代史》也记近臣提出李彦珣杀母罪行，石敬瑭以赦命已行为由，让他赴任。','该传正文不知其终、夹注转引新史后坐赃诛，后续结局不在本段给出确定死亡年。')
claim('event',E['shi_refuses_li_murder_prosecution'],'historiographical_comment','司马光认为，赦免李彦珣叛乱的罪责后，仍可以追究他杀母的罪行，这并不损害朝廷的信用。',24,Q[24]['text'],'臣光曰是司马光的史论，不作938年朝廷当事人的发言；彦后私用字和旬保持原文，主体由前后正文及旧五代史确认。')
used[24]=[E['shi_refuses_li_murder_prosecution']]
add('yang_tianxiong_appointment','石敬瑭任杨光远为天雄节度使',25,'辛未，',None,[('帝','任杨光远为天雄节度使'),('杨光远','被任命为天雄节度使')],when='938年九月辛未',place='天雄军')
sup('yang_tianxiong_appointment',25,old,'辛未，以魏府招討使楊光遠檢校太師、兼中書令，行廣晉尹，充天雄軍節度使。','《旧五代史》也记九月辛未任杨光远为天雄军节度使，并补检校太师、兼中书令和广晋尹职衔。','复用已合并的杨檀主体；检校和兼官不推多个新的军事辖区。')
add('liao_confers_shi_title','契丹使者为石敬瑭奉册加尊号英武明义皇帝',26,'冬，十月，',None,[('契丹主','派使者奉册为石敬瑭加尊号'),('帝','获加英武明义皇帝尊号')],when='938年十月戊寅',note='奉宝册是加尊号，不误作此年重新即位；匿名使者不从夹注猜姓名。')
sup('liao_confers_shi_title',26,october,source_span(october,'戊寅，','陳列如儀。'),'《旧五代史》也记十月戊寅加英武明义皇帝尊号，并补仪仗及鼓吹出城迎引、在崇元殿前依仪陈列。','只补迎册礼仪，不将书内转引欧阳史的使臣名作为独立采集书证。')
add('shi_designates_eastern_capital','石敬瑭在汴州设东京，并调整洛阳和长安的称名',27,'帝以大梁舟车所会，','晋昌军节度。',[('帝','以漕运便利为由，在汴州设东京并调整其他都城称名')],when='938年十月丙辰',place='汴州、大梁、洛阳、长安',description='石敬瑭认为大梁是舟车汇集之地、漕运便利，于汴州设东京，恢复开封府；原东都改为西京，原西都改为晋昌军节度。',note='汴州与大梁、东都洛阳、西都长安据上下文及旧五代史制文对应；制度变更不写成已新建整座城市。')
sup('shi_designates_eastern_capital',27,october,source_span(october,'庚辰，御劄曰：','其曹州改為防禦州。'),'《旧五代史》将汴州升东京、置开封府及洛京改西京、雍京改晋昌军的制令记为十月庚辰，并补县级调整和保留京兆府。','主书丙辰、旧史庚辰不同，日期分别引用，不凭干支相近擅自改字。',relation='conflicts',field='time_original')
add('wang_quan_refuses_liao_mission','王权以年老患病为由，推辞赴契丹谢尊号的使命',27,'帝遣兵部尚书王权','乃辞以老疾。',[('帝','派王权赴契丹谢尊号'),('王权','以年老患病为由推辞，并向人表示不愿向契丹屈膝')],description='石敬瑭派兵部尚书王权赴契丹谢尊号。王权自称家族世代为将相，以此行感到羞耻，向人表示不愿向契丹屈膝，随后以年老患病为由推辞。',note='家族世代将相与羞耻感是王权自述，不新增未具名祖先，也不据此断定实际患病情况。')
add('wang_quan_suspended','石敬瑭因王权推辞赴契丹而停其官职',27,'帝怒，',None,[('帝','因王权推辞使命而发怒，停其官职'),('王权','被停止官职')],when='938年十月戊子',note='坐停官是停止官职，不误作处死或确定永久罢免。')
event('sang_privy_background','桑维翰兼任枢密使的早期安排',28,span(28,'帝即位，','皆不悦。'),[('桑维翰','以宰相身份兼枢密使')],stable_key='event_zztj_281_0937_sang_shumishi',year=None,when='石敬瑭即位后兼任枢密使的追叙，非938年新任命',note='复用已录937年兼枢密使事件，主书本处概述即位后的安排，不据概述把既有事件改到936或938年。')
event('li_song_privy_background','李崧兼任枢密使的早期安排',28,span(28,'帝即位，','皆不悦。'),[('李崧','以宰相身份兼枢密使')],stable_key='event_zztj_281_0937_li_song_chancellor',year=None,when='石敬瑭即位后兼任枢密使的追叙，非938年新任命',note='复用已录937年出相兼枢密事件，不将本处概述另建为重复任命。')
claim('event','event_zztj_281_0937_sang_shumishi','historical_context','司马光在叙事中说明，郭崇韬去世后宰相兼任枢密使已不多见；石敬瑭让桑维翰、李崧兼任，使刘处让和宦官不满。',28,span(28,'初，','皆不悦。'),'这是官职背景与情绪的追叙，不重新录郭崇韬死亡事件，也不推刘处让与所有宦官组成私人联盟。')
add('sang_limits_yang_requests','桑维翰按法度限制杨光远的过分奏请',28,'杨光远围广晋，','独以法裁折之。',[('刘处让','多次奉命往来处理围攻广晋的军务'),('杨光远','提出史书认为超出本分的奏请'),('帝','对奏请态度犹豫'),('桑维翰','按法度限制杨光远的奏请')],year=None,when='广晋围城期间，具体年月未载',place='广晋',note='逾分是史书评价，帝依违译为态度犹豫，不断定每次都已批准；军事往来不推刘处让在每次奏请中都持相同态度。')
add('yang_blames_chancellors','刘处让将限制归于执政官，杨光远因此怨恨执政官',28,'光远对处让','由是怨执政。',[('杨光远','向刘处让表示不满，随后怨恨执政官'),('刘处让','将相关限制解释为执政官的意思')],year=None,when='广晋围城期间，具体年月未载',description='杨光远向刘处让表达不满。刘处让说相关限制都是执政官的意思，杨光远因而怨恨执政官。',note='这是本段所述言论与反应，不建两人的终身敌对或私人盟友关系。')
add('yang_secretly_accuses_ministers','范延光归降后，杨光远密奏执政官过失',28,'范延光降，','论执政过失；',[('杨光远','密奏执政官的过失')],when='938年范延光归降之后，具体日未载',note='这是杨光远的指控，不自动认定所有过失都已查实。')
add('shi_removes_sang_li_privy','石敬瑭解除桑维翰、李崧的枢密使职务，并加尚书衔',28,'帝知其故','皆罢其枢密使；',[('帝','解除桑维翰、李崧的枢密使职务并加尚书衔'),('桑维翰','加兵部尚书，解除枢密使职务'),('李崧','加工部尚书，解除枢密使职务')],description='石敬瑭知道杨光远指控的缘故，仍给桑维翰加兵部尚书、李崧加工部尚书，并解除两人的枢密使职务。',note='解除枢密使不等于解除宰相全部职权；加尚书与罢枢密同时保留。')
sup('shi_removes_sang_li_privy',28,october,'壬辰，以樞密使、中書侍郎平章事、集賢殿大學士桑維翰兼兵部尚書，皆罷樞密使。','《旧五代史》在十月壬辰记桑维翰兼兵部尚书及罢枢密使。','该书此处缺文，夹注据通鉴考异引实录说明与李崧并罢；只按正文作为桑维翰补证，不把夹注当独立李崧原文。')
add('liu_churang_privy_appointment','石敬瑭任刘处让为枢密使',28,'以处让','为枢密使。',[('帝','任刘处让为枢密使'),('刘处让','被任命为枢密使')],note='此为正式任命，与前段临时负责天雄军府事务分开。')
add('temple_relocation_proposal','太常建议把宗庙和社稷迁往大梁，石敬瑭决定暂留原处',29,'太常奏：',None,[('帝','决定宗庙和社稷暂时仍留原处')],place='西京、大梁',description='太常以东京已设为由，建议将仍在西京的宗庙和社稷迁往大梁。石敬瑭决定暂时维持原状。',note='且仍旧是暂保原状，不写成迁建已执行，也不推永久禁止迁移。')
reviews={21:'公主依配偶复用兴平公主，封号变化不新建同人。旧史九月庚申派接、丙寅许归与主书未列确日分别保留，归幽州不猜路径。',22:'赵可封太府卿身份明确，新建；复姓李及立唐宗庙为建议，徐诰复用李昪，不写为当日实施。',23:'庚午入朝请求、刘处让临管、己巳范延光任官铁券与赦免、将佐任官及牙兵编制分开。旧史具体补李式亳州、孙汉威陇州、薛霸卫州。李彦珣传完整经历证与929年舍人同人；供养、叛乱、守城、招降母亲、杀母追叙日期未知，后任坊州及不追罪分别记。拆字原文保留，母亲以子身份限定，母亲方向明确。',24:'臣光曰作为史家评论附同一赦免事件事实引用，不当938年当事发言或网站无条件结论。底本私用字保留，规范姓名由正文及旧史补证。',25:'杨光远辛未任天雄节度复用杨檀，旧史补同日任职与兼衔。',26:'十月戊寅契丹使奉册加尊号，旧史补迎册仪仗，不改作再次登基。',27:'汴州东京与都城称名变更、王权推辞及戊子停官分录；建都主丙辰旧庚辰异说保留，建都不推新造城。王权家世及羞耻为自述，辞老疾不断实际病情。',28:'早期桑李兼枢密复用937年既有事件；郭崇韬之后少兼与刘处让宦官不悦作背景。围城奏请限制、刘处让解释、杨怨及密奏、桑李加衔罢枢密、刘任枢密分录，未知时日留空。旧史缺文及转引夹注不当李崧独立确证。',29:'太常迁宗庙社稷建议与暂留原处明确，地点无未经核实坐标，不推永久不迁。'}
assert not (P/'publication.json').exists()
for n in range(21,30):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=938,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(21,30)],next_paragraph=Q[30]['id'],next_volume=281,next_year=938,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第21—29段，原87—95行，含第24段司马光史论；公主归契丹、恢复李姓建议、归降后任官赦免、李彦珣杀母追叙、杨光远任天雄、契丹奉册、建东京、枢密调整和宗庙暂留。938年未完成。',source_issues_review='旧五代史卷77及94卷题传主已核；李彦珣规范姓名有同卷正文及旧史支持，原文拆字及私用字保留。建东京丙辰/庚辰、临管军府不同纪日上下文保留，原文快照不变。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,30)],plain_language_review='首次逐条检查所有展示字段，身份及关系方向明确，计划、请求、任命、执行、追述、史论和指控分别标明；原文保留原字。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
