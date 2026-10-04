# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 48–53."""
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
 specs.append((directory.name,directory,'d2115d00','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))
specs += [('tongjian-280-936-defeat-retreat',YEAR/'part-07/sources/library/tongjian-280-936-defeat-retreat','660186cb','司马光等'),('jiuwudaishi-098-zhao-surrender',YEAR/'part-07/sources/library/jiuwudaishi-098-zhao-surrender','660186cb','薛居正等'),('jiuwudaishi-076-jin-advance',YEAR/'part-07/sources/library/jiuwudaishi-076-jin-advance','660186cb','薛居正等'),('liaoshi-003-relief-defeat',YEAR/'part-07/sources/library/liaoshi-003-relief-defeat','660186cb','脱脱等'),('xinwudaishi-072-dejun-shaobin',ROOT/'content/books/zizhi-tongjian/vol-272/year-0923/part-05/sources/library/xinwudaishi-072-dejun-shaobin','d77c4a74','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-defeat-retreat','tongjian-280-936-tang-fall']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p048-p053',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-048-final-return':'卷48·唐末帝纪（李从珂）','jiuwudaishi-094-gao-hanjun':'卷94·高汉筠传','xinwudaishi-016-chongmei-fire':'卷16·李重美传','xinwudaishi-015-queen-flight':'卷15·明宗家人传·曹氏与王淑妃','liaoshi-072-bei-killing':'卷72·义宗倍传','jiuwudaishi-098-zhao-surrender':'卷98·赵德钧传','jiuwudaishi-076-jin-advance':'卷76·晋高祖纪（石敬瑭）','liaoshi-003-relief-defeat':'卷3·太宗纪','xinwudaishi-072-dejun-shaobin':'卷72·四夷附录·赵德钧'}
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
# Reused source metadata remains exactly the already published record.
prior_sources={x['key']:x for f in [YEAR/'part-07/content-batch.json',ROOT/'content/books/zizhi-tongjian/vol-272/year-0923/part-05/content-batch.json'] for x in json.loads(f.read_text())['sources']}
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/280.txt').read_text().splitlines()
for n in range(48, 54):
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
    labels={'jiuwudaishi-048-final-return':'卷48·唐末帝纪（李从珂）','jiuwudaishi-094-gao-hanjun':'卷94·高汉筠传','xinwudaishi-016-chongmei-fire':'卷16·李重美传','xinwudaishi-015-queen-flight':'卷15·明宗家人传·曹氏与王淑妃','liaoshi-072-bei-killing':'卷72·义宗倍传','jiuwudaishi-098-zhao-surrender':'卷98·赵德钧传','jiuwudaishi-076-jin-advance':'卷76·晋高祖纪（石敬瑭）','liaoshi-003-relief-defeat':'卷3·太宗纪','xinwudaishi-072-dejun-shaobin':'卷72·四夷附录·赵德钧'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '闰十一月条下'
        citation = f'卷280·后唐清泰三年／后晋天福元年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'太相温（契丹将）':['太相温','太相溫','大相温','大相溫'],'高汉筠':['高漢筠'],'田承肇':[],'秦继旻':['秦繼旻'],'李彦绅':['李彥紳']}

ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

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
    if when is None:when='936年闰十一月条下；确日未独载'
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

add('dejun_offers_property_shulv','赵德钧见述律，献所携宝货和田宅籍',48,'德钧见述律太后，','田宅献之，',[('赵德钧','献宝货田籍者'),('述律平','受献一方')],when='936年赵被锁送契丹后追叙；到达见太后独立日未载',note='回述北送后遭遇，未强系潞州甲戌同日，献田籍与真拥有幽州治权分。')
sup('dejun_offers_property_shulv',48,'jiuwudaishi-098-zhao-surrender','及見國母述律氏，盡以一行財寶及幽州田宅籍而獻之，','旧赵传也记见述律献财宝田籍。','此为旧正文，不用紧后夹引通鉴论太原段当独立印证。')
add('shulv_confronts_dejun_throne_bid','述律问赴太原，赵称奉唐命；太后斥其曾求为帝、不可欺',48,'太后问曰：','此不可欺也。”',[('述律平','质问斥责者'),('赵德钧','以奉唐命回答者')],when='赵北送见述律时追叙；独立日未载',year=None,note='奉唐命为赵答辞不等唯一行动动机已证；亡语疑妄语原保。')
sup('shulv_confronts_dejun_throne_bid',48,'xinwudaishi-072-dejun-shaobin','德光母述律見之，問曰：「汝父子自求為天子何邪？」德鈞慚不能對，','新四夷附录同问求天子、赵不能答。','问对象同赵，不用新压缩对话当主每个长句逐字独证。')
add('shulv_recounts_warning_criticizes_dejun','述律称曾戒德光防赵北攻，又责赵负主无力拒敌而邀利',48,'又曰：“吾儿将行，','德钧俯首不能对。',[('述律平','追述告诫与斥责者'),('赵德钧','俯首无答者')],year=None,when='北送见太后时追述出军前告诫；原不独载日',note='其告诫为她自述，非本段另已核的出军诏文；主太原可救疑少不，依赖引文异写另保，不悄悄改原。')
sup('shulv_recounts_warning_criticizes_dejun',48,'jiuwudaishi-098-zhao-surrender','趙大王若引兵北向榆關，亟須引歸，太原不可救也。','旧赵传夹引《通鉴》作太原不可救、榆关。','明确是旧夹引同书，用于版本校异，不能计为独立事件确证。主可救及渝关保原字。',relation='conflicts')
add('shulv_rejects_ghost_property_offer','述律问田宅所在及幽州属谁，赵答属太后，太后反问何献，赵更惭',48,'又问：“器玩在此，','德钧益惭。',[('述律平','反问田籍属地者'),('赵德钧','答幽州归属且惭者')],year=None,when='北送见述律时追叙；日未载',place='契丹（会见地点未详）',note='幽州是对话中田宅地非会见地点，事件地点仅记契丹未详；属太后为赵回答，不等对每块房产权完成现代登记证明。')
sup('shulv_rejects_ghost_property_offer',48,'jiuwudaishi-098-zhao-surrender','又問：「田宅何在？」曰：「俱在幽州。」國母曰：「屬我矣，又何獻也？」','旧正文同幽州属我反问何献。','避夹引通鉴对話，当前独取正文后半明确对话。')
add('dejun_dies_after_capture','主追述赵德钧此后郁郁少食，逾年卒',48,'自是郁郁','逾年而卒。',[('赵德钧','被俘后去世者')],year=937,when='主追述逾年；旧赵传天福二年夏（937）',note='卒发生后年，不为936所有事件定年；937据旧明确天福二年，而非仅拿逾年机械加一，少食不诊断病名。')
sup('dejun_dies_after_capture',48,'jiuwudaishi-098-zhao-surrender','至天福二年夏，德鈞卒於契丹。','旧正文明确天福二年夏卒契丹。','主逾年追述与旧纪年定位并列，天福二年937；具体日未载。',relation='adds',field='time_original')
claim('person',people['赵德钧'],'death_year','赵德钧卒于937年，旧传记天福二年夏。',48,'至天福二年夏，德鈞卒於契丹。','后年追述据明确旧纪年，不把本段年度936当卒年。',source='jiuwudaishi-098-zhao-surrender')
add('zhang_li_khitan_academician','张砺与赵延寿入契丹，德光复任张翰林学士',48,'张厉与延寿',None,[('张砺','入契丹、再任翰林者'),('赵延寿','同入契丹者'),('耶律德光','复任官者')],when='936年被送契丹后追叙；确日未载',note='私用拆件字沿旧张砺，复以主承张非为赵也任翰林；不用邻句赵937卒年影响张936入契丹。')
add('deguang_instructs_shi_south','德光告别称石宜率汉兵南下，自己留待定洛后北返并可急援',49,'帝将发上党，','吾即北返矣。”',[('耶律德光','陈军队安排者'),('帝','受告别安排者')],when='936年闰十一月甲戌至潞州后、石南下前',place='上党',note='南行民必不惧是预测，洛既定北返是条件计划，不能当已经全军返北。')
add('xiang_wen_escort_order','德光命太相温率五千骑护石敬瑭至河梁',49,'我令太相温','欲与之渡河者多少随意，',[('耶律德光','护送令一方'),('太相温','获护送任务将领'),('帝','受护送者')],when='936年闰十一月甲戌潞州告别后',place='上党至河梁',note='太相温沿本段明确名、旧大相温异写；不擅合辽另一名迪离毕。护送命与后确到哪地分。')
sup('xiang_wen_escort_order',49,'jiuwudaishi-048-final-return','甲戌，晉高祖與契丹至潞州，契丹遣蕃將大相溫率五千騎送晉高祖南行。','旧唐紀同甲戌至潞后遣大相温五千护送。','太/大可能名衔写差，结合五千同护石任务核为同将，作为别名；不是把太相解释成唐宰相。')
sup('xiang_wen_escort_order',49,'liaoshi-003-relief-defeat','命迪離畢將五千騎送入洛。','辽记护送将为迪离毕、终点入洛。','主及旧唐为太/大相温至河梁；名和任务终点叙法异，证据不足不合姓名。',relation='conflicts')
add('deguang_shi_farewell_gifts','德光与石泣别，授白貂裘，赠良马二十、战马一千二百并嘱后代相记',49,'与帝执手相泣，','世世子孙勿相忘！”',[('耶律德光','赠衣马告别者'),('帝','受赠告别者')],when='936年闰十一月甲戌上党离别条下',place='上党',note='马数是赠物史载，非两军总骑数，政治子孙相记不造生父边。')
sup('deguang_shi_farewell_gifts',49,'jiuwudaishi-076-jin-advance','脫白貂裘以衣帝，贈細馬二十匹，戰馬一千二百匹，仍誡曰：「子子孫孫，各無相忘。」','旧晋纪同白裘二十细马、一千二百战马赠别。','主良、旧细原称并列，不定品种；旧甲戌语境同告别。')
add('deguang_recommends_keep_founders','德光称刘知远赵莹桑维翰为创业功臣，劝无大故勿弃',49,'又曰：“刘知远',None,[('耶律德光','建议保用者'),('帝','受建议者'),('刘知远','引语中的功臣对象'),('赵莹','引语中的功臣对象'),('桑维翰','引语中的功臣对象')],note='后三人是引语对象未证都在告别席；大故为条件未具体定义，不创他们互盟或永不罢官已完成事实。')
add('gao_hanjun_tang_garrison','追述张敬达出师后，李从珂遣左金吾大将军高汉筠守晋州',50,'初，张敬达既出师，','守晋州。',[('唐主','遣守者'),('高汉筠','受遣守晋州者')],when='936年张敬达出师之后、死亡之前；遣守日未载',place='晋州',note='历山为高籍非另叫历山高的人，晋州与晋阳不同；当前晋帝不是派出者。')
add('tian_attacks_gao_office','张敬达死后，田承肇率众攻高汉筠府署',50,'敬达死，','攻汉筠于府署，',[('田承肇','率众攻府署者'),('高汉筠','被攻者')],when='936年闰十一月甲子张敬达死后',place='晋州府署',note='此田原主建雄节度，与旧节度副职异文另保；不像按高龄就把高当晋州节度正使。')
sup('tian_attacks_gao_office',50,'jiuwudaishi-094-gao-hanjun','及敬達遇害，節度副使田承肇率部兵攻漢筠於府署，','旧田职为节度副使，同攻府署。','主建雄节度、旧节度副使不合，保职衔异说，未核任免链不选其一覆盖。',relation='conflicts')
add('gao_tian_refuses_rebellion','高汉筠开门邀田，问受朝命为何相迫；田称欲拥高为节度，高以老拒为乱首',50,'汉筠开门','死生惟公所处。”',[('高汉筠','开门、拒乱首者'),('田承肇','称欲奉高为节度者')],when='936年敬达死后晋州危变时',note='欲奉为田说辞，不当高已经被实际立为新节度，死生惟公亦非自杀。')
sup('gao_tian_refuses_rebellion',50,'jiuwudaishi-094-gao-hanjun','承肇曰：「我欲扶公為節度使。」澤筠曰：「老夫耄矣，不敢首為亂階，死生系子籌之。」','旧同田拟拥、高拒。','澤筠疑漢筠讹字据本传主体校，不另造泽筠人物。')
add('tian_signals_kill_soldiers_refuse','田承肇示意欲杀高，兵士投刃称宿德不当害，田改称戏言',50,'承肇目左右','与公戏耳。”',[('田承肇','欲杀后以戏言退者'),('高汉筠','被拟杀且获军众维护者')],when='936年敬达死后晋州危变时',note='欲杀未实行，宿德为兵众评价不等现代人格评分；匿名左右军士不造名。')
add('gao_returns_luoyang_meets_shi','田许高汉筠返洛，石途中相见称忧其被乱兵害而喜',50,'听汉筠归洛阳。',None,[('高汉筠','获准归洛、会见者'),('帝','途中见高者')],when='936年乱后归洛期间追叙；相会确日未载',note='主帝石，旧说入洛后飞诏征高遇途，叙时差另列，不强按当前段排序相会必早于丁丑。')
sup('gao_returns_luoyang_meets_shi',50,'jiuwudaishi-094-gao-hanjun','漢筠促騎以還。高祖入洛，飛詔征之，遇諸途，乃入覲，','旧说石入洛后征高、相遇入觐。','主仅途中相遇列南下段，旧明确入洛后阶段；保具体时序补，不为对齐让石二次在同日入洛。',relation='adds',field='time_original')
add('fu_zhang_warn_heyang','符彦饶、张彦琪到河阳，密言胡兵南下水浅人离不可守',51,'符彦饶、张彦琪','此不可守。”',[('符彦饶','密陈不可守者'),('张彦琪','密陈不可守者'),('唐主','受陈者')],when='936年闰十一月丁丑撤退前议；旧唐纪有到京后陈奏异序',place='河阳',note='张彦琪沿合并后较早UUID，北军、水、人心是两将意见；不把不可守当已试所有战术确定结果。')
sup('fu_zhang_warn_heyang',51,'jiuwudaishi-048-final-return','丁丑，車駕至自河陽。時左右勸帝固守河陽。居數日，符彥饒、張彥琪至，奏帝不可城守。','旧先丁丑归、数日后符张至陈不可守。','主两将河阳先陈再丁丑归，旧次序异，不能删居数日强统一。',relation='conflicts',field='time_original')
claim('person',person('张彦琪',51,'河阳回陈将领','符彦饶、张彦琪至河阳，密言于唐主曰：'),'aliases','主第43段张彦琦与此张彦琪按同军同伴同返河阳及旧军职核为同人。',51,'符彦饶、张彦琪至河阳，密言于唐主曰：','独立同人revision已迁旧参与与人物引用，复用较早张彦琪，不再启用张彦琦重复主体。')
add('congke_heyang_south_guards','丁丑李从珂命苌从简、刘在明守河阳南城',51,'丁丑，','守河阳南城，',[('唐主','留守令者'),('苌从简','河阳节度、留守者'),('刘在明','赵州刺史、留守者')],when='936年闰十一月丁丑',place='河阳南城',note='张河阳节度与苌河阳节度先后两人职务原保，不合主体。')
add('congke_cuts_bridge_returns_luo','丁丑李从珂断浮桥返洛阳',51,'遂断浮梁，','归洛阳。',[('唐主','断桥归洛者')],when='936年闰十一月丁丑条下',place='河阳至洛阳',note='断浮梁是军事撤离动作，不擅认为所有永久桥梁已毁。')
add('congke_orders_bei_killing','李从珂遣秦继旻、李彦绅杀李赞华于其第',51,'遣宦者秦继旻',None,[('唐主','遣杀者'),('秦继旻','受遣宦者'),('李彦绅','皇城使、受遣者'),('李赞华','在府被杀者')],when='936年闰十一月丁丑归洛条下；辽无独日，另记召同死遭拒',place='洛阳李赞华第',note='沿耶律倍既有李赞华别名，派遣与完成杀主合述；没有依据将秦李认作后唐此时共同自焚者。')
sup('congke_orders_bei_killing',51,'liaoshi-072-bei-killing','從珂欲自焚，召倍與俱，倍不從，遣壯士李彥紳害之，時年三十八。','辽倍传补召同死、拒后遣李彦绅害，年龄三十八。','主宦者秦也受遣、辽仅李，不意味着否认秦；辽独记召俱自焚缘由，无日不替主丁丑补同日。',relation='adds')
sup('congke_orders_bei_killing',51,'liaoshi-003-relief-defeat','辛巳，晉帝至河陽，李從珂窮蹙，召人皇王倍同死，不從，遣人殺之，乃舉族自焚。','辽太宗纪将倍被召害和从珂自焚连系辛巳。','主丁丑条杀倍与辽辛巳连记异时序，保两书而非强定倍一定跟从珂同一时刻死。',relation='conflicts',field='time_original')
add('shi_arrives_heyang_chang_surrenders','己卯石至河阳，苌从简迎降且舟楫已备',52,'己卯，','舟楫已具。',[('帝','抵河阳者'),('苌从简','迎降者')],when='936年闰十一月己卯（主），旧唐纪庚辰、辽辛巳异日',place='河阳',note='己卯不是之前唐丁丑回洛日，舟备与断浮桥能先后成立，不猜舟数。')
sup('shi_arrives_heyang_chang_surrenders',52,'jiuwudaishi-076-jin-advance','己卯，至河陽北，節度使萇從簡來降，舟楫已具。','旧晋同己卯北岸苌降舟备。','补北岸，不把后来渡河位置统一为南岸；苌萇繁简同人。')
sup('shi_arrives_heyang_chang_surrenders',52,'jiuwudaishi-048-final-return','庚辰，晉高祖至河陽。','旧唐纪记庚辰至河阳。','与主、旧晋己卯异日，不互覆盖。',relation='conflicts',field='time_original')
sup('shi_arrives_heyang_chang_surrenders',52,'liaoshi-003-relief-defeat','辛巳，晉帝至河陽，','辽纪作辛巳至河阳。','与己卯、庚辰不同，原文保，需纸本进一步校日。',relation='conflicts',field='time_original')
add('zhangsheng_captures_liu_shi_releases','彰圣军执刘在明降晋，石释放并令复位',52,'彰圣军执',None,[('刘在明','被军众执后获释复位者'),('帝','释并令复位者')],when='936年闰十一月己卯到河阳条下',note='军名彰圣不是个人姓名，复其所具体职务主未展开，不能猜必立刻重回赵州已经掌全州。')
add('tang_four_commanders_whitehorse_recon','李从珂命宋审虔等四将领千余骑赴白马阪察战地',53,'唐主命马军','行战地，',[('唐主','遣察者'),('宋审虔','马军都指挥使、领察者'),('符彦饶','步军都指挥使、领察者'),('张彦琪','河阳节度、领察者'),('刘延朗','宣徽南院使、领察者')],when='936年闰十一月庚辰前；旧唐纪己卯',place='白马阪',note='行战地指察战地，原各职保，四将是前八重返河阳议的同四将，不凭领察推每人真发动会战。')
sup('tang_four_commanders_whitehorse_recon',53,'jiuwudaishi-048-final-return','己卯，帝遣馬軍都指揮使宋審虔率千餘騎至白馬坡，言踏陣地，','旧同宋率千余踏阵，记己卯，地作白马坡。','主阪旧坡古地称保，无现代坐标，不对两职省记当互否四将。',relation='adds',field='time_original')
add('fifty_riders_desert_whitehorse','察战地队伍中五十余骑渡河投北军',53,'有五十馀骑','奔于北军。',[],when='936年闰十一月白马阪察战地时',place='白马阪、河',note='只部分五十余人，不硬录四将当时一并降；北军语境晋契丹一方无个人接受名单。')
add('tang_generals_reject_battle_site','诸将问宋何处不能战、谁肯在此，队伍遂还',53,'诸将谓审虔曰：','乃还。',[('宋审虔','被问且回军一方')],note='诸将原没逐一署名发话，不给四人皆说同一句；乃还没有具体胜败大战。')
add('congke_reconsiders_heyang_secret_submissions','庚辰李从珂与四将再议赴河阳，将校已飞书迎晋帝',53,'庚辰，','飞状迎帝。',[('唐主','再议者'),('宋审虔','四将议者'),('符彦饶','四将议者'),('张彦琪','四将议者'),('刘延朗','四将议者')],when='936年闰十一月庚辰',note='将校笼统与四将未一一同名，不能说每名四将亲签飞书；所迎帝石不是重向唐请归洛。')
add('shi_blocks_mianchi_route','石忧李从珂西逃，遣契丹千骑扼渑池',53,'帝虑唐主西奔，','扼渑池。',[('帝','遣扼者')],when='936年闰十一月庚辰条下、辛巳前',place='渑池',note='虑可能逃不当已逃西川，千骑为派阻部队不是全部随石北骑数。')
add('liu_queen_chongmei_abandon_palace_burning','刘皇后拟积薪烧宫，李重美劝新帝仍需宫居、勿后世劳民，皇后遂止',53,'皇后积薪欲烧宫室，','乃止。',[('刘皇后','欲烧后止者'),('李重美','劝留宫室者')],when='936年辛巳举族自焚之前插述；独立时辰未载',place='洛阳宫室',note='前句自焚之后插述此前计划，不能认已死后重美又劝。烧楼自焚和欲烧全部宫室两对象不同。')
sup('liu_queen_chongmei_abandon_palace_burning',53,'xinwudaishi-016-chongmei-fire','及晉兵將至，劉皇后積薪于地，將焚其宮室，重美曰：「新天子至，必不露坐，但佗日重勞民力，取怨身後耳！」后以為然。','新李重美传明确晋兵将至时皇后拟烧、重美止。','独立正文支持插述在自焚前，而不是同意后没烧那座自焚楼；不改主原顺序。')
add('wang_urges_cao_hide_cao_refuses','王淑妃劝曹太后藏避待姑夫，太后不忍独活，令王自求生',53,'王淑妃谓太后曰：','妹自勉之。”',[('王淑妃','劝躲避者'),('曹太后','拒独生者')],when='936年辛巳自焚前插述',place='洛阳宫',note='妹为称呼非亲姐妹已证，姑夫语境晋帝石，未据此新造王或曹母族亲属边。')
sup('wang_urges_cao_hide_cao_refuses',53,'xinwudaishi-015-queen-flight','妃謂太后曰：「事急矣，宜少回避，以俟姑夫。」太后曰：「我家至此，何忍獨生，妹自勉之！」','新明宗家人传同王劝、曹拒。','以传首曹后及淑妃王氏明确两人，太后非述律，淑妃非本年唐贤妃李春燕。')
add('wang_congyi_hide_survive','王淑妃与许王李从益藏球场得免',53,'淑妃乃与', '获免。',[('王淑妃','藏避存活者'),('李从益','许王、藏避存活者')],when='936年辛巳自焚时插述',place='洛阳球场',note='获免为本次逃生，不提前加947将来死；球场与新鞠院古地名保。')
sup('wang_congyi_hide_survive',53,'xinwudaishi-015-queen-flight','而妃與許王從益及其妹匿於鞠院以免。','新补从益妹也藏鞠院获免。','其妹原不具名，不造具体公主姓名；没有因此把王淑妃当从益生母。',relation='adds')
add('later_tang_fall_self_immolation','闰十一月辛巳李从珂与曹太后、刘皇后、李重美、宋审虔等携传国宝登楼自焚，后唐灭亡',53,'辛巳，唐主与','登玄武楼自焚，',[('唐主','自焚的后唐末帝'),('曹太后','同登楼自焚者'),('刘皇后','同登楼自焚者'),('李重美','同登楼自焚者'),('宋审虔','同登楼自焚者')],when='936年闰十一月辛巳',place='洛阳玄武楼',note='灭亡是末帝自焚、晋入洛所构成政权终结，非孤立医学；原玄武旧元武异写保，传国宝名物不推真伪与后流转。')
sup('later_tang_fall_self_immolation',53,'jiuwudaishi-048-final-return','辛巳辰時，帝舉族與皇太后曹氏自燔於元武樓。','旧唐帝纪同辛巳，补辰时、楼作元武。','辰时保史载时辰不换公历；帝明确末帝从珂，非新晋石。',relation='adds')
sup('later_tang_fall_self_immolation',53,'jiuwudaishi-076-jin-advance','辛巳，唐末帝聚其族，與親將宋審虔等登元武樓，縱火自焚而死。','旧晋纪同日末帝、宋审虔等自焚死。','宋明确同死，不把秦继旻李彦绅也加入死者；等不猜所有家族名单。')
sup('later_tang_fall_self_immolation',53,'xinwudaishi-016-chongmei-fire','廢帝自焚，后及重美與俱死。','新明皇后和重美俱死。','后沿前刘皇后，非曹或其他后身份被混。')
add('shi_enters_luoyang','辛巳晚石敬瑭入洛阳住旧宅',53,'是日晚，','止于旧第。',[('帝','入京止旧宅者')],when='936年闰十一月辛巳晚',place='洛阳、石敬瑭旧第',note='旧第不是当晚已经进宫，后甲申车驾入宫另段处理。')
sup('shi_enters_luoyang',53,'jiuwudaishi-076-jin-advance','至晚，車駕入洛。唐兵解甲待罪，皆慰而舍之。帝止潛龍舊第，百官稍稍見焉。','旧同晚入洛止旧第，补百官逐渐见。','下文甲申入内未提前加到今夜，源全篇后续留下一段。',relation='adds')
add('shi_releases_tang_soldiers','唐兵解甲待罪，石敬瑭慰而释放',53,'唐兵皆解甲','帝慰而释之。',[('帝','释唐兵者')],when='936年闰十一月辛巳晚入洛后',place='洛阳',note='免唐兵并非后来全部旧朝臣皆无处分，后张刘等另段。')
add('liu_zhiyuan_orders_city_billets','石命刘知远布京，刘令汉军归营、契丹住天宫寺，城中肃然',53,'帝命刘知远','无敢犯令。',[('帝','命部署京者'),('刘知远','分营驻兵者')],when='936年闰十一月辛巳入洛后',place='洛阳、天宫寺',note='馆契丹是驻军安排、肃然为主概述，不证明本年始终全城零犯罪；不画坐标。')
add('luoyang_residents_resume_work','逃难民众数日回乡复业',53,'士民避乱',None,[],when='936年辛巳入洛后数日；各人回日未载',place='洛阳',note='数日不换成精确三日，皆为史家整体叙述非已逐人普查。')
# Reused people retain immutable batch fields; their evidence-backed years receive guarded revisions.
for name,quote in [('李从珂','辛巳，唐主与曹太后、刘皇后、雍王重美及宋审虔等携传国宝登玄武楼自焚，'),('曹太后','辛巳，唐主与曹太后、刘皇后、雍王重美及宋审虔等携传国宝登玄武楼自焚，'),('刘皇后','辛巳，唐主与曹太后、刘皇后、雍王重美及宋审虔等携传国宝登玄武楼自焚，'),('李重美','辛巳，唐主与曹太后、刘皇后、雍王重美及宋审虔等携传国宝登玄武楼自焚，'),('宋审虔','辛巳，唐主与曹太后、刘皇后、雍王重美及宋审虔等携传国宝登玄武楼自焚，')]:
 can=ALIASES.get(name,name);claim('person',people[can],'death_year',can+'于936年后唐亡国自焚时去世。',53,quote,'主明列同登楼自焚；旧新对应传记、帝纪校身份，不扩充等的匿名死者。')
claim('person',people['耶律倍'],'death_year','耶律倍（李赞华）于936年被李从珂遣人害死。',51,'遣宦者秦继旻、皇城使李彦绅杀昭信节度使李赞华于其第。','主本年明被杀，辽同被害；主丁丑条下与辽辛巳连記日异保，不改统一卒年936。')

reviews={48:'北送见述律对话追叙不硬系潞甲戌；主太原可救与旧引通鉴不可救版本异，夹引非独证。幽州只田宅对话地。赵卒937据旧天福二夏，不用逾年猜年；张入契丹与赵后年卒句分。',49:'告别安排条件与已遣太相温护送分；太/大温同五千护石核名，不同辽迪离毕未经身份依据不合。赠良马20、战马1200与总骑数分，建议勿弃功臣对象非必在席。',50:'初遣守晋州与张死后田攻分，主田建雄节度与旧副使异职保，旧澤筠疑汉筠沿本传；杀高未实行，兵宿德评价归说者。高遇石旧入洛后征、主途中编序分，不按段号硬定见日。',51:'张彦琪/琦同人纠正复用较早UUID。主先两将河阳陈再丁丑回、旧回后数日再陈序异。秦李杀倍，辽召倍同死不从及辛巳连記补异，不把倍与从珂同刻死。',52:'主和旧晋己卯河阳、旧唐庚辰、辽辛巳三日原保；苌迎舟备、彰圣执刘降、石释复位分，復其所不猜已赵州到任。',53:'察白马地四将与五十余骑投北非四将皆立即降，飞书者无明名单。刘后止焚全部宫、王曹话及王从益匿为自焚前插述，不出现死后又谈话。辛巳同死身份5明确，倍另杀；石晚入旧第、释兵、刘布营、民返分。'}
contexts=[]
for d in sorted((P/'sources/context').iterdir()):
 rec=json.loads((d/'paragraph.json').read_text());f=d/'source.txt'
 contexts.append(dict(file=os.path.relpath(f,P/'sources'),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),paragraph_id=rec['id'],purpose='确认倍、曹后王淑妃及李重美传主，不扩录全年外生平',url='https://github.com/greed-216/histree/blob/d2115d00/'+str(f.relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(48,54):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(48,54)],next_paragraph=Q[54]['id'],next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第48—53段原53—58行：赵北送遭遇、告别南下、晋州危变、唐退洛杀倍、晋河阳受降、末帝自焚唐亡与晋入洛。后17段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(48,54)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
