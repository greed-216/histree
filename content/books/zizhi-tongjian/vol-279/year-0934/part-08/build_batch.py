# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 47–58."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,78))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'5f4233fa','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-934-may-towns',YEAR/'part-07/sources/library/tongjian-279-934-may-towns','651c7870','司马光等'),
 ('xinwudaishi-007-934-may',YEAR/'part-07/sources/library/xinwudaishi-007-934-may','651c7870','欧阳修'),
 ('xinwudaishi-064-two-towns-join-shu',YEAR/'part-05/sources/library/xinwudaishi-064-two-towns-join-shu','8468a699','欧阳修'),
 ('xinwudaishi-061-jinling-fire',YEAR/'part-01/sources/library/xinwudaishi-061-jinling-fire','570df7a6','欧阳修'),
 ('jiuwudaishi-136-mengchang-parentage',YEAR.parent.parent/'vol-275/year-0927/part-05/sources/library/jiuwudaishi-136-mengchang-parentage','4b8f7b80','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-may-towns','tongjian-279-934-shu-succession','tongjian-279-934-meng-name-decree']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p047-p058',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[key]
        record=dict(record,section_title=label,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(47, 59):
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
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[source]
        record=dict(record,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '六月条下' if n<=49 else '六月至七月' if n==50 else '七月条下'
        citation = f'卷279·清泰元年（934；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','蜀主':'孟知祥','仁赞':'孟昶','李什罕':'李仁罕','徐知诰':'李昪','太后':'曹氏（李嗣源后）','刘后':'刘氏（李从珂后）'}
NEW_ALIASES={'李重美':[],'成延龟':['成延龜'],'王宏':['王宏（吴控鹤军使）'],'崔居俭':['崔居儉'],'崔荛':['崔蕘'],'刘氏（李从珂后）':['劉氏（李從珂后）','刘皇后（李从珂妻）','沛国夫人（李从珂妻）'],'刘茂威':['劉茂威']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=934, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='934年'+('六月' if n<=49 else '七月')+'条下；确日未独载'
    key = 'event_zztj_279_0934_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_279_0934_' + code + '_' + pk
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
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_279_0934_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
E['zhongmei']=ev('zhongmei_chengde_henan','六月甲戌李重美领成德节度使、同平章事，兼河南尹并判六军诸卫事',47,'六月，甲戌，','判六军诸卫事。',[('李重美','成德节度使等官获任者'),('帝','任命皇子者')],when='934年六月甲戌',place='成德军、河南府',note='同一命列多兼衔，不当其亲赴镇州或各官分别在不同日获得。')
relationship('帝','李重美','父亲',47,span(47,'以皇子','判六军诸卫事。'),'皇子重美且新家人传明示废帝二子；A父亲→B为从珂是重美父亲，生母未知。')
claim('event',E['zhongmei'],'description','旧末帝纪同六月甲戌记重美加检校太保、同平章事，充镇州节度使兼河南尹、判六军诸卫事。',47,'甲戌，皇子左衛上將軍重美加檢校太保、同平章事，充鎮州節度使兼河南尹，判六軍諸衛事。','镇州与主成德为州名及军号，旧加检校太保为同一命补衔。',source='jiuwudaishi-046-934-zhongmei-post',relation='corroborates')
claim('event',E['zhongmei'],'description','新重美传记废帝即位后重美由左卫上将军领成德节度使，兼河南尹、判六军诸卫事。',47,'廢帝即位，自左衞上將軍領成德軍節度使、兼河南尹、判六軍諸衞事，','独立同职补证，不具甲戌；后改领天雄、封雍王不前移本次成德任命。',source='xinwudaishi-016-zhongmei-post',relation='corroborates')
claim('person',people['李重美'],'description','新家人传记李从珂有重吉、重美二子和为尼的幼澄一女，均不知所生。',47,'廢帝二子，曰重吉、重美，一女為尼，號幼澄，皆不知其所生。','所生为生母未明；不能把刘皇后自动设为重美母亲，也不因排行列表创建年龄已证的兄弟边。',source='xinwudaishi-016-congke-children')
ev('cheng_yangui_wenzhou_shu','文州都指挥使成延龟举州归附蜀',48,'文州','举州附蜀。',[('成延龟','举文州附蜀者')],place='文州',note='六月条下无日，举州附非无证已被攻破；二十四史未检出同事独立补文，不编人数和对方将领。')
claim('person',person('徐知诰',49,'谋受禅并忌杨濛者',span(49,'吴徐知诰','王濛，')),'description','主书叙徐知诰将受禅，对临川王杨濛有所忌惮。',49,span(49,'吴徐知诰','王濛，'),'受禅是当时打算，不当已经完成；徐知诰复用李昪主体，934展示事实保当时名。')
E['accuse']=ev('xu_accuses_yang_meng','徐知诰遣人指控杨濛藏匿亡命、私造兵器',49,'遣人告濛','擅造兵器；',[('徐知诰','遣人提出指控者'),('杨濛','被指控者')],note='告是指控，不能将未核指控写为杨濛确实藏匿及造兵；未名使者不造人物。')
E['demote']=ev('yang_meng_demoted_liyang','六月丙子杨濛降封历阳公',49,'丙子，','降封历阳公，。',[('杨濛','由临川王降封者')],when='934年六月丙子',note='吴廷降封原句主语省略，不把徐独立拥有皇帝册封权当事实；原逗句号并列为转录标点保原。')
ev('yang_meng_confined_hezhou','杨濛被幽禁和州',49,'幽于和州，','幽于和州，',[('杨濛','被幽禁者')],when='934年六月丙子条下',place='和州',note='降封与幽禁分，未载罪审过程，不能认为指控已证实。')
E['guard']=ev('wang_hong_two_hundred_guards_meng','命控鹤军使王宏领二百兵看守杨濛',49,'命控鹤军使','二百卫之。',[('王宏','奉命带二百兵看守者'),('杨濛','被看守者')],when='934年六月丙子条下',place='和州',note='卫之承前幽禁语境为监守；不写成杨濛自己的护卫军或诛杀命令。')
claim('event',E['demote'],'description','新吴世家太和六年条亦记废临川王濛为历阳公。',49,'六年閏正月，金陵火，罷建都，廢臨川王濛為歷陽公，','该段从闰正月火起连记后事，降封无独日，不将整段每事均定闰正月；主六月丙子保。',source='xinwudaishi-061-jinling-fire',relation='corroborates')
claim('event',E['guard'],'description','新吴世家记徐知诰遣亲信王宏以兵守杨濛。',49,'知誥遣親信王宏以兵守之。','同人同事独证王宏身份；未具二百或和州，此细节仍由主书支持。',source='xinwudaishi-061-jinling-fire',relation='corroborates')
relationship('刘昫','冯道','姻亲',50,'刘昫与冯道婚姻。','明言婚姻、引语称亲家；未载哪名子女嫁娶，保姻亲对称关系，不猜岳父、女婿及婚期。')
claim('person',people['刘昫'],'description','本段史书称刘昫性苛察，冯道出镇后与李愚论议常不合。',50,'蚼性苛察，李愚刚褊；道既出镇，二人论议多不合，','蚼为同段刘昫疑写，主先明刘昫且旧末帝纪同李愚争政事作刘煦，沿已核刘昫主体；评价归史书，不当现代人格诊断。')
E['quarrel']=ev('liu_xu_li_yu_court_quarrels','冯道出镇后刘昫、李愚在政事中争执并相互责骂',50,'道既出镇，','至相诟骂，',[('刘昫','与李愚争执者'),('李愚','与刘昫争执者')],when='934年五月冯道出镇后至七月换相前的概述；主未独载日',place='洛阳',note='愚讥贤亲家所为、昫恨为主描述；不把后任姚顗日提前，也不推争执只一次。')
claim('event',E['quarrel'],'description','旧末帝纪七月丁未记李愚、刘煦在政事堂因公事相诟，帝命刘延朗宣谕制止。',50,'是日，宰臣李愚、劉煦因論公事，於政事堂相詬，辭甚鄙惡，帝令樞密副使劉延朗宣諭曰：「卿等輔弼之臣，不宜如是，今後不得更然。」','旧是日承上丁未，仅补该日一例与制止；刘煦已有合并主体，不把主全部争执都定丁未。',source='jiuwudaishi-046-934-july-court')
ev('liu_li_seek_irregular_audiences','刘昫、李愚各想非时求见，政事多停滞',50,'各欲非时','事多凝滞。',[('刘昫','欲非时求见者'),('李愚','欲非时求见者')],when='934年冯道出镇后的争执期间；主未独载月日',note='欲为求见意向，不当皇帝每次均已接见；停滞为史书叙述，未编件数。')
ev('congke_seeks_new_chancellors','李从珂想更换宰相，向亲信询问合适人选',50,'帝患之，','宜为相者，',[('帝','拟换相、询问者')],when='934年七月辛亥任卢以前；具体询问日未载',note='询问与任命分，未名亲信不指某枢密使；不将候选当已任。',place='洛阳')
ev('advisers_recommend_three_candidates','亲信推荐姚顗、卢文纪、崔居俭，议论才行各有优劣',50,'皆以尚书','互有优劣。',[('姚顗','尚书左丞、被推荐候选'),('卢文纪','太常卿、被推荐候选'),('崔居俭','秘书监、被推荐候选'),('帝','听取推荐者')],when='934年七月辛亥任卢以前；确日未载',note='候选三人前职照主，未载优劣具体内容不编评价；三人均不是同时已任宰相。',place='洛阳')
E['lottery']=ev('congke_lottery_selects_lu_yao','李从珂焚香祝天，以筷夹取瓶中姓名，先得卢文纪、次得姚顗',50,'帝不能决，','次得顗。',[('帝','以夹取姓名择相者'),('卢文纪','首先被夹得姓名者'),('姚顗','其次被夹得姓名者')],when='934年七月辛亥任卢以前；夜间，确日未载',note='主筋字疑筯，显示按新传筯校读为筷；保主引文筋。不视为神意证明，夹得名与实际任官分。',place='洛阳')
claim('event',E['lottery'],'description','新卢文纪传也记废帝将清望官姓名置琉璃瓶，夜焚香祝天以筯夹取，首得卢文纪。',50,'廢帝因悉書清望官姓名內琉璃瓶中，夜焚香呪天，以筯挾之，首得文紀，欣然相之，','新悉书清望官、主置所荐之名叙范围略不同；新仅首卢，不独立补次姚，原筯支持校读主筋。',source='xinwudaishi-055-lu-lottery',relation='corroborates')
E['lu']=ev('lu_wenji_chancellor','七月辛亥卢文纪受任中书侍郎、同平章事',50,'秋，七月，辛亥，','同平章事。',[('卢文纪','中书侍郎、同平章事获任者'),('帝','任命者')],when='934年七月辛亥',place='洛阳',note='本段仅卢实际任官；姚实际任相在后第60段八月辛未，不提前。')
for source,quote in [('jiuwudaishi-046-934-july-court','辛亥，以太常卿盧文紀為中書侍郎、平章事。'),('xinwudaishi-007-934-may','秋七月辛亥，太常卿盧文紀為中書侍郎、同中書門下平章事。')]:
 claim('event',E['lu'],'description','旧新废帝纪均记七月辛亥卢文纪由太常卿任中书侍郎、平章事。',50,quote,'两书分别保独立source；主同平章事与各书官衔原字对照。',source=source,relation='corroborates')
relationship('崔荛','崔居俭','父亲',50,'居俭，荛之子也。','本段主明确荛父，姓随崔，旧未已有同主体；新父蕘为繁简对应，不因蕘另建人。')
claim('person',people['崔居俭'],'description','新崔居俭传记他是清河人，父蕘、祖蠡为唐名臣。',50,'崔居儉，清河人也。祖蠡、父蕘皆為唐名臣。','籍贯及父与主荛之子互核；蕘简化荛。祖父本批只作人物补述，不扩未校同名祖父实体。',source='xinwudaishi-055-cui-jujian')
claim('person',people['崔荛'],'description','新崔居俭传所称父蕘对应主父荛，为唐名臣。',50,'祖蠡、父蕘皆為唐名臣。','同主明确父子关系，规范简体荛，不能借此定具体官职生卒。',source='xinwudaishi-055-cui-jujian',relation='corroborates')
ev('congke_wants_chu_execution','李从珂欲杀楚匡祚',51,'帝欲杀','楚匡祚，',[('帝','拟杀者'),('楚匡祚','拟被杀者')],when='934年七月乙卯流放前；确日未载',note='欲为意向，后来长流，不当实际执行诛杀。')
ev('han_pleads_for_chu','韩昭胤以奉诏检校家财为由，劝李从珂不要族诛楚匡祚',51,'韩昭胤曰：','恐不厌众心。”',[('韩昭胤','劝止族诛者'),('帝','被劝者'),('楚匡祚','被劝保全者'),('李重吉','引语中家财被检校的已故人物')],when='934年七月乙卯流放前；确日未载',note='受诏检校为韩辩护引语，不重建已录取财旧事件；为天下父子是政治比喻，不造全人物亲属边。')
ev('chu_long_exile_dengzhou','七月乙卯楚匡祚被长流登州',51,'乙卯，','长流匡祚于登州。',[('楚匡祚','被长流者'),('帝','下流放命者')],when='934年七月乙卯',place='登州',note='长流为长期流放，不写处死；只载流放地无实际到达日。')
E['empress']=ev('liu_installed_empress','七月丁巳沛国夫人刘氏被立为皇后',52,'丁巳，','刘氏为皇后。',[('刘后','皇后受立者'),('帝','册立者')],when='934年七月丁巳',place='洛阳',note='为李从珂皇后，区别庄宗刘皇后、秦王妃及其他刘氏；姓未载名不填刘玉娘。')
relationship('帝','刘后','丈夫',52,'丁巳，立沛国夫人刘氏为皇后。','本帝李从珂立后；A丈夫→B表示李是刘氏丈夫，不再创建反向妻子重复边。')
for source,quote in [('jiuwudaishi-046-934-july-court','丁巳，製立沛國夫人劉氏為皇后。'),('xinwudaishi-007-934-may','丁巳，立沛國夫人劉氏為皇后。')]:
 claim('event',E['empress'],'description','旧新末帝纪也记七月丁巳立沛国夫人刘氏为皇后。',52,quote,'同日、封号、身份交叉验证，旧新同主体不别造后。',source=source,relation='corroborates')
claim('person',people['刘氏（李从珂后）'],'description','旧后传记李从珂刘皇后为应州人，天成中封沛国夫人，清泰初百官三次请立中宫后受立。',52,'末帝劉皇后，應州人也。天成中，封為沛國夫人。清泰初，百官三上表，請立中宮，遂立為皇后。','已有封号与本次册后不同阶段，天成中未独年不擅定926；不提前其弟后任及936焚亡。',source='jiuwudaishi-049-liu-empress')
claim('person',people['刘氏（李从珂后）'],'description','新后传记刘氏父茂威，为应州浑元人；刘氏初封沛国夫人。',52,'廢帝皇后劉氏，父茂威，應州渾元人也。','父名和籍贯为新传补证，渾元底字保留，不猜现代坐标及生年。',source='xinwudaishi-016-liu-empress')
relationship('刘茂威','刘后','父亲',52,'廢帝皇后劉氏，父茂威，應州渾元人也。','新传明确后父茂威，按刘氏父姓识别；无官职或生卒依据不补。',source='xinwudaishi-016-liu-empress')
ev('huihu_tributaries_robbed','回鹘入贡者多被河西武装劫掠',53,'回鹘入贡者','河西杂虏所掠，',[],place='河西',note='主称杂虏为史料用语，展示以未具体命名河西武装概括；回鹘使者未具名，不补族群、数量、年份起点。')
ev('niu_ordered_escort_and_campaign','诏牛知柔领兵护送入贡者，并会同邠州兵讨劫掠者',53,'诏将军牛知柔','与邠州兵共讨之。',[('牛知柔','奉命护送及会兵讨者'),('帝','下诏者')],place='河西、邠州',note='主帅禁后衛疑写，前牛已为将军可复用；仅录诏令，不当已会兵获胜。其旧灵州护送康福是929另一事，不能补本次已执行。')
ev('xu_recalls_song_jinling','徐知诰召宋齐丘还金陵',54,'吴徐知诰召','宋齐丘还金陵，',[('徐知诰','召还者'),('宋齐丘','被召还者')],place='金陵',note='主右仆谢疑射，旧已知右仆射主体；此处只召还，不能认为主动辞职已批。')
ev('song_titled_commander_adviser','宋齐丘被任为诸道都统判官并加司空',54,'以为诸道','加司空，',[('宋齐丘','诸道都统判官、司空获任者'),('徐知诰','任职者')],place='金陵',note='加司空与差判官同命分官差；下无关预说明职权，不把司空当实际控制各政。')
claim('person',people['宋齐丘'],'description','主书记宋齐丘受任后对政事没有参与权。',54,'于事皆无所关预，','史书描述其实际地位，不能反向断言本来所有职务均无权或追溯到此前。')
ev('song_repeated_retirement_requests','宋齐丘屡请退居',54,'齐丘屡请','退居，',[('宋齐丘','屡请退居者')],place='金陵',note='屡为多次未列次数，请与获给住处不同；不把后九华山退隐事前移。')
ev('xu_grants_song_south_garden','徐知诰以南园供宋齐丘退居',54,'知诰以','南园给之。',[('徐知诰','给南园者'),('宋齐丘','获南园者')],place='金陵、南园',note='南园在本次召还金陵语境，不标现代位置；未得基础书独立同事补记，保主证。')
claim('person',people['宋齐丘'],'description','新吴世家太和六年条亦记宋齐丘获司空衔。',54,'拜令謀司徒，宋齊丘司空。','压缩年段不具本次召还日与南园；只补同年司空，不把段首闰正月套全段。',source='xinwudaishi-061-jinling-fire',relation='corroborates')
ev('congzhang_congmin_leave_commands','洋王李从璋、泾王李从敏罢镇后居洛阳私第',55,'护国节度使','皆罢镇居洛阳私第，',[('李从璋','护国节度使洋王、罢镇居私第者'),('李从敏','归德节度使泾王、罢镇居私第者')],place='洛阳',note='主七月条下背景，未具罢镇命日，不把皇族王爵同时废除。')
claim('person',people['李从敏'],'description','主书说李从珂薄待二王，尤恶李从敏，因他曾在宋州参与杀李重吉。',55,'帝待之甚薄；从敏在宋州预杀重吉，帝尤恶之。','预为参与，不另造934七月第二次重吉死亡事件；皇帝态度及其理由按主书叙述保。')
ev('congke_drunken_rebuke_two_princes','李从珂宴中酒酣，责辱李从璋、李从敏据雄藩，二王害怕',55,'尝侍宴禁中，','二王大惧，',[('帝','酒酣责二王者'),('李从璋','被责而惧者'),('李从敏','被责而惧者')],when='934年七月条下所叙禁中宴；确日未载',place='洛阳宫中',note='尝侍宴未独日，不推永久敌对；何物为引语不当现代叙述者辱称。')
ev('cao_tells_princes_leave_banquet','曹太后称皇帝醉了，让二王速离',55,'太后叱之曰：','尔曹速去！”',[('太后','令二王离去者'),('李从璋','被令离去者'),('李从敏','被令离去者')],when='934年七月条下所叙禁中宴；确日未载',place='洛阳宫中',note='令其去是命令，未另写实际离宫过程，不推太后与二王结盟。')
ev('shu_yongping_army_ya','蜀在雅州设置永平军',56,'蜀置永平军','于雅州，',[],place='雅州',note='主七月条下无日，永平与后唐永宁等军号不同，不新建同名人或现代边界。')
ev('sun_hanshao_yongping_post','孙汉韶受任永平军节度使',56,'以孙汉韶','为节度使。',[('孙汉韶','永平军节度使获任者')],place='雅州、永平军',note='承前置军，任命不等于已实际到镇。')
ev('zhang_reappointed_shannan','蜀复任张虔钊为山南西道节度使、同平章事',56,'复以张虔钊','同平章事；',[('张虔钊','山南西道节度使复任对象')],place='山南西道',note='旧原唐官与今蜀复命不同任次；下文固辞，不能写已在镇任职。')
ev('zhang_declines_shannan_assignment','张虔钊坚持辞任山南西道、不赴任',56,'虔钊固辞','不行。',[('张虔钊','固辞不行者')],place='蜀',note='固辞不行未记惩罚原因，不猜恐惧、衰老或健康理由。')
ev('meng_illness_worsens','孟知祥已有逾年的风疾加重',57,'蜀主得风疾逾年，','至是增剧。',[('蜀主','风疾加重者')],note='得病逾年为背景时长，不倒算开始年，也不把风疾确诊为某现代病名。',place='成都')
E['crown']=ev('meng_renzan_crown_regent','七月甲子孟知祥立孟仁赞为太子并令监国',57,'甲子，','仍监国。',[('蜀主','立储命监国者'),('仁赞','东川节度使等前职、太子监国者')],when='934年七月甲子',place='成都',note='孟仁赞复用孟昶，改名在丙寅另记；亲卫等为前职，不在此次都新授。')
relationship('蜀主','仁赞','父亲',57,'立子东川节度使、同平章事、亲卫马步都指挥使仁赞为太子，仍监国。','明确立子为太子，复用已发布孟知祥父亲→孟昶，保同key。')
E['regents']=ev('meng_summons_six_regents','孟知祥召赵季良等六臣受诏辅政',57,'召司空、','受遣诏辅政。',[('蜀主','召六臣辅政者'),('赵季良','司空同平章事、被召辅政者'),('李仁罕','武信节度使、被召辅政者'),('赵廷隐','保宁节度使、被召辅政者'),('王处回','枢密使、被召辅政者'),('张公铎','捧圣控鹤都指挥使、被召辅政者'),('侯弘实','奉銮肃卫指挥副使、被召辅政者')],when='934年七月甲子',place='成都',note='主受遣诏疑遗字，保底字；只记召受命辅政，不说每人已到场。侯弘实区别朱弘实，張公鐸沿张公铎。')
E['death']=ev('meng_zhixiang_dies','七月甲子夜孟知祥去世',57,'是夕殂，','是夕殂，',[('蜀主','去世者')],when='934年七月甲子夜',place='成都',note='是夕承甲子，本段死亡与秘不发丧分；病因史称风疾不作现代诊断。')
claim('person',people['孟知祥'],'death_year','孟知祥于934年七月甲子夜去世。',57,'是夕殂，','年由本年七月顺叙、日承甲子，保原人物档案只增事实。')
E['secret']=ev('shu_conceals_meng_death','孟知祥去世后暂不发丧',57,'秘不发丧。','秘不发丧。',[],when='934年七月甲子夜之后，丙寅宣遗制之前',place='成都',note='秘不发丧为状态，未指定单一决策者，后王传消息不等于已向所有人公开。')
E['news']=ev('wang_chuhui_tells_zhao_death','王处回夜启义兴门，向赵季良告知孟知祥死讯并哭泣',57,'王处回夜启','处回泣不已，',[('王处回','启门告死讯并哭者'),('赵季良','听闻死讯者')],when='934年七月甲子夜之后；夜间，确日未独载',place='成都、义兴门',note='主述处回泣，新述相对泣，按各书保不同叙述范围；不推赵在本段也一直泣。')
E['zhao_advice']=ev('zhao_urges_quick_succession','赵季良告诫王处回，须速立嗣君以防强将觊觎',57,'季良正色曰：','岂可但相泣邪！”',[('赵季良','劝速立嗣君者'),('王处回','受劝者')],when='934年七月甲子夜之后的秘密告讯时；确日未独载',place='成都',note='强将伺时是赵判断，不当所有将领已有具体反叛行动，也不把警言当继位已完成。')
ev('wang_stops_crying_thanks_zhao','王处回收泪向赵季良致谢',57,'处回收泪','谢之。',[('王处回','收泪致谢者'),('赵季良','受谢者')],when='934年七月甲子夜之后的告讯时；确日未独载',place='成都')
ev('zhao_instructs_wang_sound_renhan','赵季良教王处回见李仁罕，先察其言辞再告死讯',57,'季良教处回','然后告之。',[('赵季良','教先试探者'),('王处回','受教者'),('李仁罕','拟先审言辞对象')],when='934年七月孟知祥死后、公开遗制前；确日未载',place='成都',note='主李什罕与紧接仁罕第、前武信李仁罕对应，什为疑写；审词旨是建议，不代表已经宣布。')
ev('li_renhan_prepared_meets_wang','王处回至李仁罕宅，李仁罕有所准备而出',57,'处回至仁罕第，','仁罕设备而出，',[('王处回','到宅者'),('李仁罕','设备而出者')],when='934年七月孟知祥死后、公开遗制前；确日未载',place='成都、李仁罕宅',note='设备含义不充分，不臆造确切兵器数量、兵变或已谋弑。')
ev('wang_withholds_truth_from_renhan','王处回没有把孟知祥死讯实情告李仁罕',57,'遂不以','实告。',[('王处回','未告实情者'),('李仁罕','未获实告者')],when='934年七月孟知祥死后、公开遗制前；确日未载',place='成都、李仁罕宅',note='遂承见其设备，记录未告，不编谎话具体内容。')
claim('event',E['crown'],'description','新孟世家连记孟知祥病、以其子昶为皇太子监国。',57,'遂病，以其子昶為皇太子監國。','新用后名昶，主此时仁赞；六月宴劳后连叙病立储，不独载甲子，不能把主立储日改为六月。',source='xinwudaishi-064-two-towns-join-shu',relation='corroborates')
claim('event',E['death'],'description','旧孟传记孟知祥七月去世，年六十一。',57,'七月卒，年六十一。','旧卷136附注说明孟传大典原阙、采册府僭伪部补梗概；如实标辑补层，七月互核，不作完整原薛史或精确甲子独证。',source='jiuwudaishi-136-meng-death',relation='corroborates')
claim('event',E['death'],'description','新孟世家在六月宴劳、患病与立储叙述后连记孟知祥去世，未另列确日。',57,'知祥卒，謚為文武聖德英烈明孝皇帝，廟號高祖，陵曰和陵。','新以压缩叙事连记，主及旧明确七月；保此来源叙事范围，不套六月宴劳条成死亡日。谥庙陵为后事补称，不认为甲子夜已办毕。',source='xinwudaishi-064-two-towns-join-shu')
claim('event',E['secret'],'description','新孟昶传也记孟知祥已卒而秘密未发。',57,'知祥已卒而祕未發，','独立同状态补证，不添秘丧负责人的姓名。',source='xinwudaishi-064-meng-secret-succession',relation='corroborates')
claim('event',E['news'],'description','新孟昶传记王处回夜过赵季良，两人相对哭泣。',57,'王處回夜過趙季良，相對泣涕不已，','新相对泣范围与主仅叙处回泣不同，保两书独立描述；不把义兴门伪称为新也具。',source='xinwudaishi-064-meng-secret-succession')
claim('event',E['zhao_advice'],'description','新孟昶传也记赵季良劝当速立嗣君以绝非望，哭无益。',57,'季良正色曰：「今疆侯握兵，專伺時變，當速立嗣君以絕非望，泣無益也。」','疆侯及非望为新原字，独立印证劝速继位主旨，不作强将具体犯罪证明。',source='xinwudaishi-064-meng-secret-succession',relation='corroborates')
ev('shu_announces_death_decree','七月丙寅蜀宣布孟知祥遗制',58,'丙寅，','宣遗制，',[],when='934年七月丙寅',place='成都',note='由秘丧转公开遗制；未具宣读者不写王处回亲宣或另造正文。')
E['rename']=ev('meng_renzan_renamed_chang','遗制命太子孟仁赞改名孟昶',58,'命太子仁赞','更名昶，',[('仁赞','受遗制改名者')],when='934年七月丙寅',place='成都',note='使用同人稳定主体孟昶，改名有明确命，不把后名书写证明此前已改。')
E['accession']=ev('meng_chang_accession','七月丁卯孟昶即皇帝位',58,'丁卯，','即皇帝位。',[('仁赞','蜀皇帝即位者')],when='934年七月丁卯',place='成都',note='丙寅改名与丁卯即位分；本段没改元，不写即位即改广政。')
claim('event',E['accession'],'description','新孟昶传记王处回、赵季良立昶，然后发丧；孟昶即位后仍称明德。',58,'處回遂與季良立昶，而後發喪。昶立，不改元，仍稱明德，','新明确二臣参与与不改元，主本段无独立二臣即位行动角色可补事实；不提前新后至五年改广政。',source='xinwudaishi-064-meng-secret-succession')
claim('person',people['孟昶'],'aliases','太子仁赞改名昶，为同一孟昶主体。',58,'命太子仁赞更名昶，','主有明确改名，沿既有孟仁赞别名，不分新人物。')
claim('event',E['accession'],'description','旧孟昶传记知祥死后孟昶继位，时年十六，仍称明德元年。',58,'知祥卒，遂襲其偽位，時年十六，尚稱明德元年。','年龄按旧记不再逆算出生年；伪字为史家立场保引文、展示中性；该句正文与前宋朝事实初名仁赞辑注区分。',source='jiuwudaishi-136-mengchang-parentage',relation='corroborates')

reviews={47:'六月甲戌重美领成德旧镇州同军州，加衔与领差一命；新家传补同职，父从珂明确，生母皆不知不能设刘。',48:'成延龟文州举州附，未得基础史独立同事补记；无日不编战争过程。',49:'受禅计划忌惮与告罪分，藏亡造兵仅指控；丙子降封、幽和、王宏二百监守分。新吴年段闰正月火后连记废濛不套全段闰月，王宏亲信独证；王濛为临川王杨濛，不造姓王人物。',50:'刘冯姻亲无子女名单婚期，不猜岳婿。蚼主上下文与旧刘煦同李愚争执匹配昫。争执、求见政滞、帝问、候选、夜瓶夹名、实际卢七月辛亥任分；姚任八月在后不提前。旧丁未一例及谕止补，不能套全段争执该日。主筋新筯保原校读，夹取为史叙非神意。崔父荛新蕘为繁简，新籍清河补。',51:'帝欲杀与韩劝及乙卯长流分，族诛意向不是已杀；天下父子是比喻不造关系，检校家财为韩引语。',52:'主旧新丁巳沛国立后互证，末帝刘不同庄宗刘玉娘。旧应州天成封与新父茂威浑元补，亲属有证；生母重美不明不推刘。',53:'入贡被掠和诏牛领兵护送共讨分，河西族群兵数未名；禁后卫疑字原保，诏非已执行获胜，929护康为另事。',54:'宋召还、受判官加司空、无权、屡请退居、给南园分；谢射疑字原保沿既有右仆射，基础补书仅同年司空无南园，九华后事不混。',55:'二王罢镇居私第未定命日，帝薄尤恶从敏为史叙；宋州重吉死亡已有不重建。酒宴责辱、太后令离分，不造敌对或盟友关系。',56:'雅州置永平与孙受命、张复命及拒不行分，未名任命执行者不猜；新947鳳州战事不支持934任官。',57:'风疾逾年不倒算始年，甲子立储监国、召六臣、是夕殂秘分。受遣诏疑字保；李什罕上下李仁罕校读保原。王夜告泣、赵劝、王谢、教先审词、李设备、未告实分，不视诸将均已叛。旧传七月死六十一补且大典原阙册府辑补标层；新六月宴劳压缩后立储死亡未独日，不套六月死亡。新相对泣较主仅处回泣范围不同保。',58:'丙寅宣遗制改名、丁卯即位分，孟仁赞孟昶同人；新二臣立后发丧不改元及旧16岁补，未前移广政年。'}
contexts=[]
for directory in sorted((P/'sources/context').iterdir()):
 r=json.loads((directory/'paragraph.json').read_text());contexts.append(dict(file=os.path.relpath(directory/'source.txt',P/'sources'),sha256=hashlib.sha256((directory/'source.txt').read_bytes()).hexdigest(),paragraph_id=r['id'],purpose='新卷55卢文纪传首及父祖核对；不自动新增传中前后史事',url='https://github.com/greed-216/histree/blob/5f4233fa/'+str((directory/'source.txt').relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(47,59):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(47,59)],next_paragraph='zztj-v279-y0934-p059',next_volume=279,next_year=934,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续934年第47—58正文段，原52—63行；皇子授职、文附蜀、吴降濛监守、后唐宰相争执择卢及立后、诏护贡与宋退居、二王宴、蜀授职和孟死继位。第59段税逋核免待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(47,59)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
