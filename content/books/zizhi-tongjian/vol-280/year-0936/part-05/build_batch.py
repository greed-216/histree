# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 29–36."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,71))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'4db2cb5d','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))

specs += [('jiuwudaishi-048-936-september',ROOT/'content/books/zizhi-tongjian/vol-280/year-0936/part-04/sources/library/jiuwudaishi-048-936-september','3c08d3ed','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-emperor-northern-campaign','tongjian-280-936-november-commands']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p029-p036',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-108-long-min-plans':'卷108·龙敏传','liaoshi-076-zhang-li-command':'卷76·张砺传','xinwudaishi-047-liu-jingyan-revolt':'卷47·刘景岩传','xinwudaishi-065-liu-jun-family':'卷65·南汉世家·唐臣后裔入岭','jiuwudaishi-099-936-liu-prisoners':'卷99·汉高祖纪（刘知远）','jiuwudaishi-075-936-jinyang':'卷75·晋高祖纪','xinwudaishi-066-xiguang-brother':'卷66·楚世家·马希广','xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/280.txt').read_text().splitlines()
for n in range(29, 37):
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
    labels={'jiuwudaishi-108-long-min-plans':'卷108·龙敏传','liaoshi-076-zhang-li-command':'卷76·张砺传','xinwudaishi-047-liu-jingyan-revolt':'卷47·刘景岩传','xinwudaishi-065-liu-jun-family':'卷65·南汉世家·唐臣后裔入岭','jiuwudaishi-099-936-liu-prisoners':'卷99·汉高祖纪（刘知远）','jiuwudaishi-075-936-jinyang':'卷75·晋高祖纪','xinwudaishi-066-xiguang-brother':'卷66·楚世家·马希广','xinwudaishi-056-lv-qi-peace':'卷56·吕琦传（对契丹和议）','xinwudaishi-055-sikong-duties':'卷55·马胤孙传（司空职掌议论）','songshi-483-sun-guangxian':'卷483·孙光宪传','xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '九月条下' if n<=30 else '十月条下及追叙' if n<=33 else '十一月条下'
        citation = f'卷280·后唐清泰三年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'刘遂凝':['劉遂凝'],'和凝':[],'龙敏':['龍敏'],'郎万金':['郎萬金'],'刘在明':['劉在明'],'刘浚':['劉浚','劉濬','刘濬'],'刘景岩':['劉景巖','刘景严','劉景嚴'],'杨汉章':['楊漢章'],'李懿（后唐亲将）':['李懿']}
ALIASES.update({'汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=936, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='936年'+('九月' if n<=30 else '十月' if n<=33 else '十一月')+'条下；确日未独载'
    key = 'event_zztj_280_0936_' + code
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
        edge = 'participation_zztj_280_0936_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_280_0936_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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

add('congke_announces_campaign','九月丁未李从珂诏亲征',29,'丁未，','下诏亲征。',[('唐主','下诏者')],when='936年九月丁未',note='诏与次日启程分，原本无强制自己实际亲临太原。')
add('chongmei_offers_substitute','李重美以父目疾未平，自请代北行',29,'雍正重美曰：','愿代陛下北行。”',[('李重美','代征请行者'),('帝','被劝暂缓者')],note='雍正疑雍王原字保，沿本年正月已封雍王的李重美，不合清雍正；目疾是儿子所述，不添病名。')
add('congke_pleased_alternative','李从珂本不愿行，闻儿请代而悦',29,'帝意本','闻之颇悦。',[('帝','闻而悦者')],note='本不欲行主叙内心，未记批准儿子代征。')
add('three_counselors_urge_campaign','张延朗、刘延皓、刘延朗均劝帝行',29,'张延朗、','皆劝帝行，',[('张延朗','劝行者'),('刘延皓','劝行者'),('刘延朗','宣徽南院使、劝行者'),('帝','被劝者')],note='两个刘名分人，刘延皓此前削官与此对话不合成延朗；即使疑字也保主。')
add('congke_leaves_luoyang','九月戊申李从珂发洛阳',29,'帝不得已，','发洛阳，',[('帝','启程者')],when='936年九月戊申',place='洛阳',note='不得已主叙，被劝启程不意味着未有亲征诏。')
sup('congke_leaves_luoyang',29,'jiuwudaishi-048-936-september','戊申，帝發京師，路經徽陵，帝親行謁奠。夕次河陽，','旧同戊申出京、补途经徽陵谒奠及当夕河阳。','同启程补途程，不用后地点替换出发城。',relation='adds')
add('congke_challenges_lu_wenji','李从珂质问卢文纪此前自称相业却无嘉谋，卢拜谢不能答',29,'谓卢文纪曰：','不能对。',[('帝','质问者'),('卢文纪','拜谢不能答者')],note='朕雅闻卿有相业是帝说法，不当史家已证此前任相是众议唯一错误。')
add('liuyanlang_monitors_fuyanrao','九月己酉遣刘延朗监符彦饶军赴潞州为后援',29,'己酉，','为大军后援。',[('刘延朗','军监者'),('符彦饶','步军都指挥使、领军者')],when='936年九月己酉',place='潞州',note='遣赴目的不推已抵城；监军不是私人主从关系。')
add('fu_troops_insubordinate','主述军自凤翔推戴以来骄悍，符彦饶惧乱不敢严束',29,'诸军自凤翔',None,[('符彦饶','惧军乱、未严法束者')],year=None,when='自凤翔推戴以来持续状态；主未逐次具年月',note='含934以来背景与当次后援约束，不硬把全部骄悍行为定936，未名军卒不造人。')
add('congke_consults_heyang','李从珂至河阳惮北行，召宰相枢密商议',30,'帝至河阳，','议进取方略，',[('帝','召议者')],place='河阳',note='至河阳承戊申出行，召议未另具日；不擅名未明枢密全员都在场。')
add('lu_wenji_recommends_stay','卢文纪劝车驾留河阳，先遣近臣督战，不能解围再进',30,'卢文纪希帝旨，','进亦未晚。”',[('卢文纪','提出留河阳方案者'),('帝','听建议者')],place='河阳',note='晋安固、三道救、契丹不久留是卢论证，不把它们当保证；希旨为史家评述。')
sup('lu_wenji_recommends_stay',30,'jiuwudaishi-048-936-september','召群臣議進取，盧文紀勸帝駐河橋。','旧也记召议、卢劝驻河桥。','主河阳、旧河桥情境相关不作现代地名坐标同一已核。')
add('zhang_supports_zhao_departure','张延朗欲使赵延寿脱枢务，赞同卢言；帝问其他人无异言',30,'张延朗欲因事','无敢异言者。',[('张延朗','赞同并被史书指有安排赵外出动机者'),('帝','再问者')],note='欲因事动机由主叙，不推赵已经被正式免枢密或每名臣皆真赞同。')
add('liusui_secret_contact','泽州刺史刘遂凝暗通石敬瑭，上表称帝不可越太行',30,'泽州刺史刘遂凝','不可逾太行。',[('刘遂凝','秘密联系、上表者'),('石敬瑭','联系对象')],place='泽州、太行',note='上表不可逾是建议，暗通无具信全文不添盟约；本人不是现父刘鄩。')
relationship('刘鄩','刘遂凝','父亲',30,'泽州刺史刘遂凝，鄩之子也，','鄩沿既有梁将刘鄩，主明之子；不把已故父亲连本年在场行动。')
add('zhang_he_recommend_zhao','张延朗、和凝建议赵延寿北行会父赵德钧卢龙军',30,'帝议近臣可使','宜遣延寿会之。”',[('张延朗','建议者'),('和凝','翰林学士、建议者'),('帝','受议者'),('赵延寿','拟北行者')],note='须昌为和凝籍贯非此次奏地；父关系主明且旧既有赵德钧养父沿原边，不新造亲父。')
add('zhaoyanshou_moves_luzhou','九月庚戌赵延寿率兵二万赴潞州',30,'庚戌，','将兵二万如潞州。',[('赵延寿','枢密忠武随驾诸军都部署兼侍中、领军者')],when='936年九月庚戌',place='潞州',note='各官衔原句保，二万为所率本队，不直接加到赵德钧后来合兵总数。')
sup('zhaoyanshou_moves_luzhou',30,'jiuwudaishi-048-936-september','庚戌，樞密使趙延壽先赴潞州。','旧同日赵先赴潞州。','旧简记不独立支撑二万数字；主具数另源。')
add('congke_visits_huaizhou','九月辛亥李从珂至怀州',30,'辛亥，','帝如怀州。',[('帝','至怀州者')],when='936年九月辛亥',place='怀州')
sup('congke_visits_huaizhou',30,'jiuwudaishi-048-936-september','辛亥，幸懷州。','旧同日幸怀州。','帝主沿本卷末帝，不变晋高祖。')
add('kang_sili_cavalry_command','康思立任北面行营马军都指挥使，率扈从骑兵赴团柏谷',30,'以右神武统军康思立','思立，晋阳胡人也。',[('康思立','获任、领扈从骑兵者')],place='团柏谷',note='辛亥条下无独日；晋阳胡人身份原书表述，不猜具体族属，晋阳为籍贯非该营已驻太原。')
add('long_min_proposes_zanhua','龙敏建议立李赞华为契丹主，由天雄卢龙分兵送幽州西楼并露檄，牵制德光后顾后选锐击',30,'帝以晋安为忧，','此亦解围之一策也。”',[('帝','问策者'),('龙敏','吏部侍郎、提出策者'),('李赞华','计划拟立者')],note='李赞华沿耶律倍，拟立不是已成为契丹主、未出幽州或已送回；内顾解围是龙预测，永清为籍贯。')
sup('long_min_proposes_zanhua',30,'jiuwudaishi-048-936-september','敏勸帝立東丹王讚華為契丹主，以兵援送入蕃，則契丹主有後顧之患，不能久駐漢地矣。','旧末帝纪也记立赞华、援送以迫后顾策。','正文独证，夹注辽义宗传谈倍邀讨属于引用不再计独立证据。')
sup('long_min_proposes_zanhua',30,'jiuwudaishi-108-long-min-plans','請以援兵從東丹王李贊華取幽州路趨西樓，契丹主必有北顧之患。','旧龙敏传也记援赞华经幽州西楼。','同旧史不同纪传互照，不能把同书重复当两种完全独立底本。',relation='adds')
add('long_plan_not_implemented','李从珂赞龙敏方案，执政惧不成，议不决',30,'帝深以为然，','议竟不决。',[('帝','赞策者'),('龙敏','策未落实的建议者')],note='此处主明确议不决、旧明确不能用，区别于上一批主只劝杀而旧明确执行的案例。')
sup('long_plan_not_implemented',30,'jiuwudaishi-108-long-min-plans','末帝然之，而不能用。','旧龙传明确认可而未能用。','可支持不实施此方案，不泛说所有龙策均无人执行。')
add('congke_drinks_fears_campaign','主述李从珂忧沮，日夕酣饮悲歌，群臣劝北行时称石使其心胆堕地',30,'帝忧沮形于神色，',None,[('帝','忧沮及答劝者')],note='主所述情绪与原话，不作医学心理诊断；无名劝者不臆定卢等。')
sup('congke_drinks_fears_campaign',30,'jiuwudaishi-048-936-september','帝自是酣飲悲歌，形神慘沮。','旧也记酣饮悲歌、形神惨沮。','史家描述保自书，不改成人格标签。')
# A second plan in the biography is relevant supplementation, with its own actors and uncertainty.
event('long_min_discusses_li_yi','旧龙敏传补龙与帝亲将李懿论赵德钧难胜契丹',30,source_span('jiuwudaishi-108-long-min-plans','敏又謂末帝親將李懿曰：','況名位震主，奸以謀身乎！'),[('龙敏','谋议者'),('李懿','帝亲将、受议者')],source='jiuwudaishi-108-long-min-plans',when='清泰末（936）怀州救寨谋议；具体日未载',note='同一救寨场景扩补，不擅将李懿与他朝同名人合；批评赵是龙观点，没新造赵已被罢。')
event('long_min_thousand_horse_plan','旧龙敏传补拟与郎万金领精骑千人夜入晋安，取半能济以振困军',30,source_span('jiuwudaishi-108-long-min-plans','請於其間選壯馬精甲健夫千人，','況敵騎乎！'),[('龙敏','拟领队者'),('郎万金','被提议共同领队者'),('李懿','讨论对象')],source='jiuwudaishi-108-long-min-plans',when='清泰末（936）怀州谋议；具体日未载',note='选千、半能济为方案和预计，不是已入寨。摘录连有夹注，但方案只据正文；夹引通鉴胡注郎官及勇将不计独立证，主31具郎现官。')
# Preserve the rest of the plan as a separate verbatim proof.
claim('event',B['events'][-1]['key'],'description','龙敏计划夜冒敌骑循山入寨，并希望困军得知援军近况。',30,'路出山，夜冒敵騎，循山入大寨，千騎之內，得其半濟，則寨無虞矣。','此处正文直接续前夹注，分开逐字摘录不拼装假原句；寨无虞是其估计。',source='jiuwudaishi-108-long-min-plans')
add('order_collect_horses','十月壬戌诏括天下将吏、民间马',31,'冬，十月，','及民间马，',[],when='936年十月壬戌',note='括取命令非全部马已收齐，原人员类别两种全部收。')
add('order_recruit_seven_households','十月壬戌诏每七户出义军一人、自备铠仗，限十一月集',31,'又发民为兵，','以十一月俱集，',[],when='936年十月壬戌',note='七户为主定额，义军名物原；限十一月是未来集合期，不当已全员在九月到军。')
sup('order_recruit_seven_households',31,'jiuwudaishi-048-936-october','壬戌，詔天下括馬，又詔民十戶出兵一人，器甲自備。','旧正文同壬戌征取写十户一人。','主七户与旧十户并列。旧夹注引契丹国志七户为依赖引用，当前不另当二十四史独立确证。',relation='conflicts')
sup('order_recruit_seven_households',31,'xinwudaishi-047-liu-jingyan-revolt','唐廢帝調民七戶出一卒為義兵。','新刘景岩传正文也记七户一卒。','本传为另一书正文补主标准；未载壬戌日，不替主确日添独证。')
add('lang_wanjin_trains_conscription','朝廷命陈州刺史郎万金教义军战阵，主称用张延朗谋',31,'命陈州刺史','用张延朗之谋也。',[('郎万金','被命教战者'),('张延朗','主称方案提出者')],when='936年十月壬戌条下',note='原陈写战陈，展示战阵语义、原引保；教令不补实际课程内容。')
add('recruitment_totals_disruption','主记征马二千余匹、征夫五千人，评无益军用而扰民',31,'凡得马',None,[],when='936年十月征取后概述；统计日未载',note='实无益于用为主评价，二千余与五千为史书统计，未用以计算现代动员率。')
add('zhaodejun_ambition_background','主追述赵德钧阴蓄异志，欲因乱取中原而请救晋安',32,'初，','自请救晋安寨；',[('赵德钧','请求出援、被史家叙动机者')],year=None,when='初，原救晋安之前追述；蓄意起年未载',note='阴蓄异志为主史评述，不凭此给已定年篡位行动；自请救与真正推进分。')
add('zhaodejun_changes_route','赵德钧请率银鞍契丹直三千骑改由土门西入，帝准',32,'唐主命','帝许之。',[('唐主','命后袭与准新路线者'),('赵德钧','请改变路线者')],when='936年九月甲辰救援命之后、十月癸酉西行之前；请求获准独立日未载',place='飞狐、土门',note='原飞狐后袭命已在第28段记录，本事件记改土门路线申请获准；时段由前九月命与本段十月行程限定。银鞍契丹直是赵属军号。')
add('liu_zaiming_garrison_yizhou','追述赵州刺史刘在明此前率兵戍易州',32,'赵州刺史、','先将兵戍易州，',[('刘在明','原戍易州将领')],year=None,when='先戍易州，赵过易之前；戍始年未载',place='易州',note='赵州为官衔，易州戍所，幽州籍贯在后句，不合三个地名。')
add('zhao_takes_liu_zaiming_troops','赵德钧经过易州，命刘在明率其众随军',32,'德钧过易州，','在明，幽州人也。',[('赵德钧','并队命令者'),('刘在明','被令率军随行者')],when='936年十月癸酉到乱柳前行军；过易独立日未载',place='易州',note='先戍始年未具另记空年，当前过易并军属本次救援行程；无兵数不猜三千外加多少。')
add('zhaodejun_joins_dong','赵德钧到镇州，令董温琪领副招讨、邀同往，又表兵少需合泽潞',32,'德钧至镇州，','须合泽潞兵；',[('赵德钧','邀合、奏合军者'),('董温琪','被邀同行、现副招讨者')],place='镇州、泽州、潞州',note='领副使承前八月获任，与此赵安排同行分，不另造首次朝廷任命；兵少为赵所表。')
add('zhaodejun_arrives_luanliu','十月癸酉赵德钧由吴儿谷赴潞州至乱柳',32,'乃自吴儿谷','至乱柳。',[('赵德钧','行军者')],when='936年十月癸酉',place='吴儿谷、潞州、乱柳')
sup('zhaodejun_arrives_luanliu',32,'jiuwudaishi-048-936-october','癸酉，幽州趙德鈞以本軍三千騎與鎮州董溫琪由吳兒穀趨潞州。','旧同癸酉补赵本军三千与董同路潞州。','主记到乱柳，旧记趋潞州，行程层次相容不擅抵城日。',relation='adds')
add('fan_yanguang_liaozhou_deployment','范延光按诏率部兵二万屯辽州',32,'时范延光受诏','二万屯辽州，',[('范延光','受命屯军者')],place='辽州',note='和前诏由青山趋榆次为不同阶段或路线上命，原未独日不造第二支二万。')
add('zhaodejun_requests_weibo_merger','赵德钧再请并魏博军，范表兵入敌境不宜南回数百里，合议遂止',32,'德钧又请',None,[('赵德钧','请求合魏博军者'),('范延光','以军已入境拒合者')],note='范知志趣难测为主叙，入贼境是其表述；乃止是合军停止，非魏博军全撤。')
add('liu_jun_southern_han_chancellor','汉主任刘浚为中书侍郎、同平章事',33,'汉主以','同平章事。',[('汉主','任命者'),('刘浚','宗正卿兼工部侍郎、获相命者')],place='南汉',note='汉主沿刘岩，本年十月条下无确日，非后汉帝；前职两衔全保，刘浚非他朝宋同名。')
relationship('刘崇望','刘浚','父亲',33,'浚，崇望之子也。','父沿既有唐相刘崇望，主明之子；不把父加入936任命在场。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新南汉世家也记刘濬为刘崇望之子、避乱南下。',33,'濬崇望之子，以避亂往；','与主同父及南汉人物群核刘浚/濬异写，源段所属刘隐招士背景，不提前录具体避乱年。',source='xinwudaishi-065-liu-jun-family',relation='corroborates')
claim('person',people['刘浚'],'aliases','刘浚在新南汉世家作刘濬，繁体底本作劉濬。',33,'王定保、倪曙、劉濬、李衡、周傑、楊洞潛、趙光裔之徒，','结合后句濬崇望之子、南汉同人物群核身份，保异写不混宋刘浚。',source='xinwudaishi-065-liu-jun-family')
add('zhaodejun_all_armies_command','十一月戊子赵德钧任诸道行营都统，仍东北面招讨',34,'十一月，戊子','依前东北面行营招讨使。',[('赵德钧','获都统命者')],when='936年十一月戊子')
sup('zhaodejun_all_armies_command',34,'jiuwudaishi-048-936-november','十一月戊子，以趙德鈞為諸道行營都統，','旧同日记都统命。','当前赵奏并军动机与朝廷任命分，不等取得帝位。')
add('zhaoyanshou_south_campaign','十一月戊子条下赵延寿任河东南面招讨使',34,'以赵延寿为','河东道南面行营招讨使，',[('赵延寿','获任者')],when='936年十一月戊子条下',place='河东道南面')
add('zhang_li_campaign_judge','翰林学士张砺任南面行营判官',34,'以翰林学士','为判官。',[('张砺','获任判官者')],when='936年十一月戊子条下',note='主名含私用字拆件，沿既有張礪别名张砺；不据部件猜另一石姓人。')
sup('zhang_li_campaign_judge',34,'liaoshi-076-zhang-li-command','會石敬瑭起兵，唐主以礪為招討判官，從趙德鈞援張敬達於河東。','辽张砺传记起兵后任招讨判官，从赵德钧援张。','主接赵延寿命，辽称从赵德钧同行，两层军队父子合指挥可能；不改主官命时间。',relation='adds')
add('fan_yanguang_southeast_campaign','十一月庚寅范延光任河东东南面招讨使',34,'庚寅，','为河东道东南面行营招讨使，',[('范延光','获任者')],when='936年十一月庚寅',place='河东道东南面')
add('li_zhou_southeast_deputy','十一月庚寅李周任范延光副使',34,'以宣牙节度使、','副之。',[('李周','现节度同平章事、获副使命者')],when='936年十一月庚寅条下',place='河东道东南面',note='宣牙疑宣武，前批八月宣武有独立旧命，原宣牙不造新军名。')
sup('li_zhou_southeast_deputy',34,'jiuwudaishi-048-936-november','庚寅，以範延光為河東道東南面行營招討使，以李周副之。','旧同日范任招讨李副。','能补同命，旧不具宣武前职，本批依前八月已记录。')
add('liuyanlang_south_deputy','十一月辛卯刘延朗任河东南面副招讨使',34,'辛卯，','为河东道南面行营招讨副使。',[('刘延郎','获任者')],when='936年十一月辛卯（主）',place='河东道南面',note='刘延郎沿已应用刘延朗别名，非刘延皓。')
sup('liuyanlang_south_deputy',34,'jiuwudaishi-048-936-november','以趙延壽為河東道南面行營招討使，以劉延朗副之。','旧把刘副接戊子赵命压缩连书。','主独立辛卯、旧无刘独立日，保叙法层次，不强断旧也辛卯。',relation='adds',field='time_original')
add('zhaoyanshou_joins_father_xitang','赵延寿与赵德钧会西汤，悉属兵于父',34,'赵延寿遇','悉以兵属德钧。',[('赵延寿','交兵者'),('赵德钧','合领者')],place='西汤',note='主父子沿已存养父子身份，军隶不另造私人人格统属关系；悉兵无独立总数。')
add('lv_qi_brings_commission_rewards','李从珂遣吕琦赐赵德钧敕告并犒军',34,'唐主遣吕琦','且犒军。',[('唐主','遣使者'),('吕琦','送敕犒军者'),('赵德钧','受敕一方')],note='与前八月吕赴河东犒军为不同此次任务，不能直接复用成同一未定日事件。')
sup('lv_qi_brings_commission_rewards',34,'jiuwudaishi-048-936-november','帝以呂琦嘗佐幽州幕，乃命齎都統官告以賜德鈞，兼犒軍士。','旧补曾佐幽州幕缘由及都统官告。','历史曾佐未定年不造本年首次入幕；送敕与任命颁令分阶段。',relation='adds')
event('jiuwu_zhaodejun_receives_lv','旧补吕琦宣委任之意，赵德钧称既委兵岂敢惜死',34,'琦至，從容宣帝委任之意，德鈞曰：「既以兵相委，焉敢惜死！」',[('吕琦','宣帝意者'),('赵德钧','答不惜死者')],source='jiuwudaishi-048-936-november',when='936年十一月送都统告时；独立日未载',note='承当前送告补对话，赵自言并非已经殉国。')
add('zhaodejun_delays_bolstered','赵德钧欲并范军而迟进，诏屡催，才屯团柏谷口',34,'德钧志在',None,[('赵德钧','逗留、后屯军者')],place='团柏谷口',note='欲并为主叙，反复催次数无数不猜；屯谷口仍不当已解晋安围。')
sup('zhaodejun_delays_bolstered',34,'jiuwudaishi-048-936-november','德鈞志在並範延光軍，奏請與延光會合。帝以詔諭延光，延光不從。','旧补朝廷曾诏范合、范不从。','当前不合方案与前十月范拒合为延续，补具体朝廷诏阶段，非新造范反叛称帝。',relation='adds')
add('wu_authorizes_qi_officials','十一月癸巳杨溥诏徐知诰置百官，以金陵府为西都',35,'癸巳，',None,[('吴主','颁授权诏者'),('徐知诰','齐主、获置官西都授权者')],when='936年十一月癸巳',place='金陵府',note='齐主是本年吴内齐封国，置百官西都不提前认937南唐建国；主仍吴帝杨溥，知诰沿李昪。')
add('liujingyan_background','主述刘景岩多财喜侠、交豪杰，家有丁夫兵仗、势倾州县',36,'前坊州刺史刘景岩','势倾州县。',[('刘景岩','前坊州刺史、被史书描述者')],year=None,when='兵变前身世与社会势力背景；各事起年未载',place='延州',note='延州籍贯，家有兵仗不当已称帝；人报其强疑人服语底本保，不擅更改。')
sup('liujingyan_background',36,'xinwudaishi-047-liu-jingyan-revolt','劉景巖，延州人也。其家素富，能以貲交游豪俊。事高萬金為部曲，其後為丹州刺史。','新记同人延州、素富交豪俊，前职丹州刺史并曾事高万金。','主前坊、旧前坊、新丹州有异说，保原；高万金≠郎万金，不因万金同名造亲属或并入。',relation='adds')
claim('person',people['刘景岩'],'aliases','主刘景岩与旧刘景严、新刘景巖按同地籍、同杨汉章兵变识别同人。',36,'以前坊州刺史劉景嚴為延州留後。','岩严非繁简，依据同事件同官前坊身份核异名；新丹州前职差异另外说明。',source='jiuwudaishi-048-936-november')
add('yang_hanzhang_bad_governance','主称杨汉章无政，失夷夏人心',36,'彰武节度使杨汉章','失夷、夏心，',[('杨汉章','被史书批评者')],year=None,when='义军兵变前在镇背景；失心起年未载',place='彰武军',note='无政失心为主整体评价，未给具体违法案或所有族群民意统计。')
add('yang_hanzhang_musters_militia','括马义军期间杨汉章领步骑数千拟赴军期，在野检阅',36,'会括马及义军，','阅之于野。',[('杨汉章','阅兵、拟带军者')],when='936年十一月军期前，主丁酉留后命前',place='彰武军郊野',note='将赴表示未赴到京或其他行营，数千为约数，野未具体地名。')
add('liujingyan_incites_troops','刘景岩潜遣人向军众称契丹强、去无归以搅动',36,'景岩潜使人挠之曰：','汝曹有去无归。”',[('刘景岩','遣人煽动者')],note='威胁为其所遣人话，不当北行军皆必死；匿名煽动者不猜高万金。')
add('troops_kill_yang_hanzhang','军众惧而杀杨汉章，奉刘景岩留后',36,'众惧，','奉景岩为留后。',[('杨汉章','被军众杀害者'),('刘景岩','被推留后者')],when='936年十一月丁酉朝命前；确日未载',place='彰武军',note='推奉与朝廷命留后分，未具执行者不认定刘本人持刀。')
sup('troops_kill_yang_hanzhang',36,'xinwudaishi-047-liu-jingyan-revolt','景巖遣人激怒之，義兵亂，殺漢章，迎景巖為留後。','新同记遣人激怒、义兵乱杀杨、迎刘留后。','同动作独立另一书补，不提前录后晋拜节度。')
add('liujingyan_appointed_acting','十一月丁酉李从珂任刘景岩彰武留后',36,'唐主不获已，',None,[('唐主','承认留后命者'),('刘景岩','获朝命者')],when='936年十一月丁酉',place='彰武军',note='不获已主叙；留后非此时已后晋节度使，丁酉朝命与前杀杨日分。')
sup('liujingyan_appointed_acting',36,'jiuwudaishi-048-936-november','丁酉，延州上言，節度使楊漢章為部眾所殺，以前坊州刺史劉景嚴為延州留後。','旧同日延州奏杨被杀，任刘景严留后。','彰武军延州同府，旧奏日不一定杀日；同旧前坊同事姓名异有充分要素沿一人。')
row=next(x for x in B['people'] if x['name']=='杨汉章');assert row['key'] not in reused;row['death_year']=936
claim('person',row['key'],'death_year','杨汉章于936年义军兵变中被杀。',36,'众惧，杀汉章，奉景岩为留后。','主旧新都明本年被杀，独立死日未载，丁酉为报告或授留后命日。')
reviews={29:'雍正重美疑雍王沿原封雍李重美，目疾为儿所述，代征未批准。三个劝行臣张与二刘分；亲征诏、戊申出洛、己酉监军后援、934以来军骄常态分。',30:'卢留河阳策与帝惮、张欲赵解枢动机、刘遂凝暗通及父鄩、张和议赵出、赵2万、康赴、龙立赞华策与未决、帝情绪分。旧龙另千骑入寨计划尚未执行；父亲不参加当前行动，籍贯不作奏地。',31:'主7户、新刘传7户、旧正文10户并列，旧夹引契丹国志不当本书独立确证。征命、十一月限期、郎教战、马2千余夫5千统计与扰民评价层次保。',32:'初蓄异志未知年，救命飞狐与改土门西路分。银鞍契丹直赵属军非德光军，刘在明赵州职易戍幽籍三地分。董前任副使与现同行分，赵合范、范表拒不当两军已合。',33:'汉主刘岩非后汉，刘浚与新劉濬同南汉同父，复用唐相刘崇望父边，不混宋同名。新隐招士只作身份补，不造确年避乱。',34:'赵两代军官命、张砺私用字回辽同任、范李同庚寅、刘延郎沿延朗辛卯旧连戊子叙法分。宣牙疑宣武原保，赵兵交父沿既有养亲不造血亲。此次吕送官告与8月犒军分，诏催仍未解围。',35:'齐是吴内封国，置百官西都仍936不当937已立南唐，杨溥和李昪身份分别。',36:'主刘景岩旧刘景严新刘景巖按同杨同地同官同事一人，新前丹州与主旧前坊异职保。高万金非郎万金，匿名煽动者军卒不造；推留后、丁酉奏授与未来后晋授节度分。杨卒年明确936，死日未具。'}
ctx=P/'sources/context/jiuwudaishi-108-long-heading/source.txt'
contexts=[dict(file=os.path.relpath(ctx,P/'sources'),sha256=hashlib.sha256(ctx.read_bytes()).hexdigest(),paragraph_id='jiu-wudaishi-205deb4a7860-p002598',purpose='核旧卷108龙敏传首，后段敏与千骑救寨策主体，不扩录生平',url='https://github.com/greed-216/histree/blob/4db2cb5d/'+str(ctx.relative_to(ROOT)))]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(29,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(29,37)],next_paragraph=Q[37]['id'],next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第29—36段原34—41行：末帝亲征、留河阳、救寨策、括马义军、赵合军、汉相、行营任官、吴西都、延州兵变。后34段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(29,37)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
