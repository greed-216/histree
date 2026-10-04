# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 935 paragraphs 21–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'53d64599','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-935-middle',YEAR/'part-02/sources/library/tongjian-279-935-middle','0a39d9d7','司马光等'),
 ('jiuwudaishi-047-xinzhou-report',YEAR/'part-02/sources/library/jiuwudaishi-047-xinzhou-report','0a39d9d7','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-935-middle','tongjian-279-935-jinzhou-min']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0935-p021-p028',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
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
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(21, 29):
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
for name,extra in [('杨檀',['杨光远','楊光遠']),('刘延朗',['刘延郎','劉延郎'])]:
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
    labels={'xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '六月条下' if n==21 else '七月条下及附载背景' if n<=25 else '九月条下及附载背景'
        citation = f'卷279·清泰二年（935；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0935_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','吴主':'杨溥','徐知诰':'李昪','闽主':'王延钧','陈后':'陈金凤'}
NEW_ALIASES={'李春燕':['李春鷰'],'徐知谔':['徐知諤'],'全师郁':['全師鬱'],'陈知隐':['陳知隱'],'马全节':['馬全節']}

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

def event(code, title, n, quote, actors, when=None, note='', year=935, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='935年'+('六月' if n==21 else '七月' if n<=25 else '九月')+'条下；确日未独载'
    key = 'event_zztj_279_0935_' + code
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
        edge = 'participation_zztj_279_0935_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_279_0935_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
add('wang_jipeng_chunyan_affair','主书称闽福王王继鹏与宫人李春燕私通',21,'闽福王','李春燕，',[('王继鹏','福王、被记与宫人私通者'),('李春燕','宫人、被记与福王私通者')],place='闽',note='私于是史述，未载开始日或年龄；不由此推正式夫妻关系。')
add('wang_jipeng_requests_chunyan','王继鹏通过陈皇后请求将李春燕赐给自己',21,'继鹏请之','陈后，',[('王继鹏','提出请求者'),('陈后','受请的皇后')],place='闽')
add('chen_reports_min_ruler_grants_chunyan','陈皇后向闽主转达，闽主将李春燕赐给王继鹏',21,'后白','赐之。',[('陈后','转达请求者'),('闽主','赐予者'),('王继鹏','受赐者'),('李春燕','所赐宫人')],place='闽',note='后白闽主而赐之承主语有省略，新闽世家明确鏻与之，核赐予者王延钧；不把赐宫人直接改成册妃。')
sup('chen_reports_min_ruler_grants_chunyan',21,'xinwudaishi-068-chunyan-request','繼鵬因陳氏以求春鷰，鏻怏怏與之。','新闽世家也记王继鹏通过陈氏求春燕，王鏻将其给他。','鏻沿王延钧已核别名；春鷰与主李春燕同人，异体保在摘录与别名。未扩十月宫变。')
add('liu_yanhao_tianxiong','七月刘延皓由枢密使任天雄节度使',22,'秋，七月，',None,[('刘延皓','由枢密使出任天雄节度使者'),('帝','任命者')],place='天雄军')
sup('liu_yanhao_tianxiong',22,'jiuwudaishi-047-xinzhou-report','以樞密使劉延皓為天雄軍節度使。','旧末帝纪七月条也记刘延皓由枢密使任天雄军节度使。','旧条未另具此命日，不能借之前丁酉当任命日。')
add('zhang_jingda_north_deputy','七月乙巳张敬达任北面行营副总管，率兵屯代州以分石敬瑭之权',23,'乙巳，',None,[('张敬达','武宁节度使、北面行营副总管及屯兵者'),('帝','任命者'),('石敬瑭','权力被分者')],when='935年七月乙巳',place='代州',note='分权是主书明示意图，不等于已经撤石总管或此时已交战。')
sup('zhang_jingda_north_deputy',23,'jiuwudaishi-047-xinzhou-report','乙巳，以徐州節度使張敬達充北面行營副總管。','旧末帝纪同记七月乙巳张敬达任北面行营副总管。','旧徐州为地镇名称，主武宁为军号；张敬达沿已有主体，非张敬方。')
add('congke_reproaches_chancellors','李从珂担忧时事，责卢文纪等缺少规劝辅佐',24,'帝深','无所规赞。',[('帝','担忧并责问者'),('卢文纪','被责的宰相')],note='深忧为史述心理；等未名不擅配其他宰相。')
add('lu_petition_private_audience','七月丁巳卢文纪等称五日起居时侍卫满前，不便尽言',24,'丁巳，','不敢敷陈。',[('卢文纪','上言说明议事障碍者')],when='935年七月丁巳',note='记上疏者的理由，不把不敢尽言当所有朝臣的独证心理。')
add('lu_requests_yanying','卢文纪等援引唐延英殿旧例，请恢复秘密召对',24,'窃见前朝','侍侧。”',[('卢文纪','请复延英故事者')],when='935年七月丁巳',note='上元以来与延英旧例是奏中历史参照，不建935唐肃宗等在场人物；请求不等于恢复已经完成。')
sup('lu_requests_yanying',24,'jiuwudaishi-047-yanying-petition','臣等亦依故事，前一日請開延英。當君臣奏議之時，隻請機要臣僚侍立左右。','旧末帝纪所载奏议进一步请求前一日请开延英，议事时只留机要臣僚。','原奏的前一日制度提议与主摘要同义，尚非施行诏。')
add('congke_keeps_five_day_audience','李从珂诏称仍按五日起居，百官退后宰相独奏常事',24,'诏以','自可敷奏。',[('帝','说明沿用制度者')],when='935年七月丁巳奏议后的答诏；独立诏日未载',note='保原制度答复，不称新建延英殿。')
add('congke_private_audience_edict','李从珂允许机密事项另日具榜奏闻、屏退侍臣在便殿面议',24,'或事应严密，',None,[('帝','允许机密奏事另议者')],when='935年七月丁巳奏议后的答诏；独立诏日未载',note='答诏不必袭延英名，不能显示为已恢复延英殿名。')
sup('congke_private_audience_edict',24,'jiuwudaishi-047-yanying-edict','請麵敷揚，即當盡屏侍臣，端居便殿，佇聞高議，以慰虛懷。','旧末帝纪答诏也允许屏退侍臣、在便殿面议。','麵保电子底本原字，展示用面；旧帝性仁恕评价不当制度实际执行证明。')
add('xu_zhie_trade_neglect','主书叙徐知谔游宴废务，在牙城西设市亲自交易',25,'吴润州','躬自贸易。',[('徐知谔','润州团练使、被叙亲自交易者')],year=None,when='935年七月条下所附行为背景；开始年份未载',place='润州牙城西',note='狎昵小人为史家评价；游燕读游宴，底本原字保；不填现代坐标。')
add('xu_zhigao_questions_attendants','徐知诰闻徐知谔废务而怒，召其身边人责问',25,'徐知诰闻之','知谔惧。',[('徐知诰','召左右诘责者'),('徐知谔','书述闻责后惧者')],when='935年七月至九月条间；未独具月日',place='吴',note='左右未名不造人物；不能写徐知诰已亲自召知谔审问。')
add('anonymous_advice_about_xu_zhie','有人以徐温所托及徐知询旧事劝徐知诰厚待徐知谔',25,'或谓知诰曰：','于公何利？”',[('徐知诰','听劝者')],when='935年七月至九月条间；未独具月日',place='吴',note='忠武王为徐温，旧事和假设治有能名只在劝语中，不作935实际政绩或新的徐知询失守事件；匿名劝者不猜身份，不凭最爱推父子。')
add('xu_zhigao_treats_zhie_better','徐知诰听劝后更加厚待徐知谔',25,'知诰感悟，',None,[('徐知诰','转而厚待者'),('徐知谔','受厚待者')],when='935年七月至九月条间；未独具月日',place='吴')
add('wu_tianzuo_amnesty','九月丙申吴大赦并改元天祚',26,'九月，',None,[('吴主','吴主、改元赦令主体')],when='935年九月丙申',place='吴')
sup('wu_tianzuo_amnesty',26,'xinwudaishi-061-935-tianzuo','大赦，改元天祚。','新吴世家也记七年九月大赦、改元天祚。','此七年承大和纪年，后天祚二三年及禅位不在本次范围；新无丙申日，不当独立日证。')
event('yang_pu_added_title_935','新吴世家记杨溥于九月加尊号睿圣文明光孝应天弘道广德皇帝',26,'七年九月，溥加尊號曰睿聖文明光孝應天弘道廣德皇帝，',[('吴主','获加尊号者')],source='xinwudaishi-061-935-tianzuo',when='935年九月；新吴世家未具日',place='吴',note='独补同月尊号，不把主赦改元丙申自动给尊号典礼；徐知诰齐王位留后续主段。')
add('fang_hao_shumi_935','九月己酉房暠由宣徽南院使任刑部尚书、枢密使',27,'己酉，','充枢密使；',[('房暠','获任刑部尚书枢密使者'),('帝','任命者')],when='935年九月己酉',note='主已宣徽疑以，旧明确以宣徽；展示任命，原文已字不悄改。')
sup('fang_hao_shumi_935',27,'jiuwudaishi-047-935-september','以宣徽南院使房暠為刑部尚書，充樞密使；','旧末帝纪九月己酉条也记房暠任刑部尚书、枢密使。','原暠保，不作房皓新实体。')
add('liu_yanlang_south_deputy_935','九月己酉刘延朗由宣徽北院使转南院使，仍兼枢密副使',27,'宣徽北院使','仍兼枢密副使。',[('刘延朗','转南院并仍兼副使者'),('帝','任命者')],when='935年九月己酉',note='与四月任北院是先后转任；仍兼不录成首次任枢密副使。')
sup('liu_yanlang_south_deputy_935',27,'jiuwudaishi-047-935-september','以宣徽北院使、充樞密副使劉延朗為宣徽南院使，充樞密副使。','旧末帝纪也记刘延朗转任宣徽南院使并任枢密副使。','同人沿已应用延郎异名，不新增主体。')
add('liu_xue_control_shumi','主书称刘延朗、薛文遇等居中用事，房暠、赵延寿意见较少被采纳',27,'于是延朗','什不三四。',[('刘延朗','被记居中用事者'),('薛文遇','枢密直学士、被记居中用事者'),('房暠','枢密使、意见较少获用者'),('赵延寿','枢密使、意见较少获用者')],year=None,when='935年九月任命后的概括；起止年月未独载',note='什不三四为史家概述，不能当可核精确采纳率或说己酉首次确切发生。')
add('fang_hao_sleep_during_envoy_discussions','主书叙房暠在枢密议幽并来使时常俯首睡去，醒时使者已离',27,'暠随势','使者去矣。',[('房暠','被叙随势可否、议事睡去者')],year=None,when='任枢密使期间的常态叙述；各次年月未载',note='随势和多为史家判断与概括；幽并使者未具名，不猜石赵本人每次在场。')
add('liu_yanlang_controls_appointments','主书称启奏除授集中由刘延朗掌握',27,'启奏除授，','一归延朗。',[('刘延朗','被记掌启奏除授者')],year=None,when='九月任命后概述；开始年月未载',note='一归为史述概括，不据此推所有官命均由其独自决定。')
add('liu_yanlang_bribery_before_tribute','主书称外来方镇、刺史先贿刘延朗，后议贡献',27,'诸方镇、刺史','后议贡献。',[('刘延朗','被记受外来官员贿赂者')],year=None,when='本段所叙任官常态；具体案件年月未载',note='未名行贿人不造完整名单；不把史家皆与必的概括当逐人案件已独证。')
add('bribe_size_affects_offices','主书称贿赂较厚者先得内地任职，较薄者晚得边陲',27,'赂厚者先，','得边陲。',[('刘延朗','前文所指掌任命者')],year=None,when='任官弊政概述；起止年月未载',note='不编具体金额、官员名单或某人已受贿的案件。')
add('generals_resent_congke_unaware','主书称将帅因任官弊政怨愤，李从珂未能察知',27,'由是诸将帅',None,[('帝','被叙未能察知者')],year=None,when='本段任官弊政后果概述；具体发生年月未载',note='诸将帅未名不新建各人参与；怨愤、不能察、由是为史述与因果判断，未当所有人独证心理。')
add('quan_shiyu_captures_water_stockade','蜀全师郁进攻金州并攻取水寨',28,'蜀金州','拔水寨。',[('全师郁','蜀所称金州防御使、进攻者')],place='金州水寨',note='原蜀金州防御使是蜀方官衔，目标城由后唐马全节守；不把两金州自动分两城或认为蜀已据全城。')
add('chen_zhiyin_flees_with_three_hundred','金州守军仅千人，陈知隐托事率三百人沿流逃走',28,'城中兵','沿流遁去。',[('陈知隐','都监、率兵逃走者')],place='金州',note='千为城兵总额、三百为被带走数，非蜀军总额；河流未名不猜坐标。')
sup('chen_zhiyin_flees_with_three_hundred',28,'jiuwudaishi-090-ma-quanjie','州兵才千人，兵馬都監陳知隱懼，托以他事出城，領三百人順流而逸，','旧马全节传也记千名州兵中陈知隐托事率三百人逃走。','旧补兵马都监职称与惧的叙述；不借旧七月所载另一都监崔处讷合人。')
add('ma_quanjie_pays_soldiers_fights','马全节倾尽私财给军，出奇奋战',28,'防御使马全节','出奇死战，',[('马全节','金州防御使、以私财给军并拒战者')],place='金州',note='死战是奋战，不设935死年；旧传以死继之同样不能解释为此役死亡。')
sup('ma_quanjie_pays_soldiers_fights',28,'jiuwudaishi-090-ma-quanjie','全節乃悉家財以給士，復出奇拒戰，以死繼之。','旧马全节传也记倾家财给士、出奇拒战。','传后仍记历官及开运二年卒，当前以死继之不是卒事；后续授横海任官待主书连续段轮到再录。')
claim('person',people['马全节'],'description','马全节字大雅，魏郡元城人。',28,'馬全節，字大雅，魏郡元城人也。','传首核同人，字籍贯补充；不把籍贯推成生年或现代坐标。',source='jiuwudaishi-090-ma-quanjie')
add('shu_retires_after_jinzhou_defense','马全节守战后蜀兵退去',28,'防御使马全节','蜀兵乃退。',[('马全节','守战使进攻军退者')],place='金州',note='本句退的是蜀兵，不写后唐全线胜利或攻陷蜀地。')
add('congke_orders_chen_execution','九月戊寅诏斩陈知隐',28,'戊寅，',None,[('帝','下处置命者'),('陈知隐','诏令处置对象')],when='935年九月戊寅',note='明确诏命，尚无本句执行证明，不填陈知隐死年或断当日已斩。')
reviews={
21:'主私于、求陈转达、主赐三动作分；新鏻与之核赐主，春鷰异体沿李春燕，不因赐立即造夫妻或册妃。',
22:'刘延皓七月转天雄与四月任枢密分，旧无独日不借邻日。',
23:'乙巳张敬达北面副总管屯代分石权，主武宁军号旧徐州地镇同人，不造936战事。',
24:'责相、丁巳上言阻碍、请延英、答诏常事与机密分。旧奏前一日只是提议，答诏无另日不强定丁巳；唐旧典不建935人物参与。',
25:'徐知谔简繁同人；游燕读游宴原字保。日常失务年null，当前诘责、匿名劝、厚待不强定七月独日。忠武王最爱不凭宠爱造父子，往年知询失守与假设治能不是本年新事实。',
26:'丙申吴赦改元主新同，新未日，尊号独补月不借丙申；齐王封授留后主段。',
27:'己酉房任枢使、刘转南院副使分；主已疑以旧明确以，摘录保已。日常专权、睡议、任官贿赂、将帅怨与帝不察均史述概括，年null不当全发生己酉。',
28:'蜀官金州衔与唐城分，拔水寨不当全城陷；千与300单位分。陈逃、马私财与出奇、蜀退、戊寅诏斩分，以死继之不当马死，诏斩不直接设陈死年。旧六月汉阴、七月奏与本段九月守城是阶段层次不同，不强并一役。'}
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,29):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=935,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(21,29)],next_paragraph='zztj-v279-y0935-p029',next_volume=279,next_year=935,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续935年第21—28正文段，原105—112行；闽李春燕、唐枢密及军政任命、延英奏议、徐知谔、吴改元、枢密任官弊政、金州守战。后9段待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,29)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
