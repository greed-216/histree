# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 10–13."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 77))
specs = [
 ('tongjian-272-923-temples',YEAR/'part-02/sources/library/tongjian-272-923-temples','ca9db7c8','司马光等'),
 ('jiuwudaishi-029-yunzhou',P/'sources/library/jiuwudaishi-029-yunzhou','c8d197bd','薛居正等'),
 ('jiuwudaishi-029-923-desheng',P/'sources/library/jiuwudaishi-029-desheng','c8d197bd','薛居正等'),
 ('xinwudaishi-032-yanzhang-command',P/'sources/library/xinwudaishi-032-yanzhang-command','c8d197bd','欧阳修'),
 ('xinwudaishi-032-desheng',P/'sources/library/xinwudaishi-032-desheng','c8d197bd','欧阳修'),
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p010-p013',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/272.txt').read_text().splitlines()
for n in range(10, 14):
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
people, used, reused, supplements = {}, {}, {'tongjian-272-923-temples','xinwudaishi-005-923-founding'}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷272·同光元年（923）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_272_0923_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'曹氏（李存勖母）','太妃':'刘氏（李克用妻）',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦','曹氏':'曹氏（李存勖母）','刘氏':'刘氏（李克用妻）','武皇':'李克用','考晋王':'李克用','上':'李存勖','帝':'李存勖','执宜':'执宜（李存勖曾祖）','国昌':'李国昌','继岌':'李继岌','硃守殷':'朱守殷','硃安殷':'朱守殷','守殷':'朱守殷','王铁枪':'王彦章','彦章':'王彦章','翔':'敬翔','顺密':'卢顺密','嗣源':'李嗣源','遂严':'刘遂严','颙':'燕颙','梁末帝':'朱友贞'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷272同光元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='923年本段；确日未载', note='', year=923, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_272_0923_' + code
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
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_272_0923_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。',source=source)
    return key

def relationship(a,b,kind,n,quote,note,source=None):
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
    a=next(x['name'] for x in B['people'] if x['key']==pa); b=next(x['name'] for x in B['people'] if x['key']==pb)
    matches={}
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_272_0923_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)

# Paragraph 10, leap April, campaign against Yunzhou.
E=event('khitan_you_yiding','契丹入寇幽州，至易州定州而还',10,'甲午，契丹寇幽州，至易定而还。',[],when='923年闰四月甲午',place='幽州、易州、定州',note='承闰月；此役主书未署领军人，不默认阿保机亲临；与春攻幽分开。')
claim('event',E,'description','《旧五代史》同记甲午契丹至易定而还。',10,'甲午，契丹寇幽州，至易、定而還。','同闰月本纪印证；易定两州并非现代一个地名。',source='jiuwudaishi-029-yunzhou',relation='corroborates')
event('tang_spring_supply_crisis','契丹屡掠馈运，幽州粮食不足半年，后唐面临压力',10,'时契丹屡入寇，钞掠馈运，幽州食不支半年，卫州为梁所取，潞州内叛，人情岌岌，以为梁未可取，帝患之。',[('帝','被记忧虑的李存勖')],when='923年闰四月本段形势总述；各项开始日未详',place='幽州、卫州、潞州',note='卫州取、潞州叛已有此前事件，此为汇总背景；不重复认作甲午攻占；以为梁未可取为当时判断。')
event('dai_yunzhou_deployment','戴思远屯杨村，留卢顺密等守郓州',10,'先是，梁天平节度使戴思远屯杨村，留顺密与巡检使刘遂严、都指挥使燕颙守郓州。',[('戴思远','屯杨村并留守者'),('顺密','郓州留守将'),('刘遂严','郓州巡检使'),('燕颙','郓州都指挥使')],when='袭郓前部署，先是追叙；确年日未载',year=None,place='杨村、郓州',note='先是背景不强定923年甲午部署；未推三将血缘。')
event('lu_shunmi_defects','卢顺密奔后唐，陈说郓州可袭取',10,'会郓州将卢顺密来奔。',[('卢顺密','自郓来奔者')],when='923年闰四月壬寅出兵前；确日未载',place='郓州、后唐')
claim('event',used[10][-1],'description','卢顺密称郓州守兵不满千人、刘遂严和燕颙失众心，可袭取。',10,'顺密言于帝曰：“郓州守兵不满千人，遂严、颙皆失众心，可袭取也。”','守兵及人心是来奔将所报，明确归属，不当已核实普查。')
E=event('debate_yunzhou_raid','郭崇韬等反对远袭，李存勖与李嗣源密议出奇取郓',10,'郭崇韬等皆以为“悬军远袭，万一不利，虚弃数千人，顺密不可从。”帝密召李嗣源于帐中谋之曰：',[('郭崇韬','反对远袭者'),('帝','召李嗣源议袭郓者'),('李嗣源','请独当袭郓之役者')],when='923年闰四月壬寅前',place='后唐军帐',note='所议计划不是已经占领郓州；嗣源胡柳渡河之惭为作者追述，不另重复胡柳战。')
claim('event',E,'description','郭崇韬等认为悬军远袭风险过大，不赞成卢顺密之说。',10,'郭崇韬等皆以为“悬军远袭，万一不利，虚弃数千人，顺密不可从。”','不同作战判断带说话人；非断二人永久敌对。')
person('郭崇韬',10,'反对远袭者','郭崇韬等皆以为“悬军远袭，万一不利，虚弃数千人，顺密不可从。”')
claim('event',E,'description','李存勖认为梁志在泽潞、东方无备；李嗣源愿独当此役。',10,'臣愿独当此役，必有以报。','请战话语只归李嗣源，期待不是结局预报。')
claim('event',E,'description','《旧五代史》亦记李存勖召李嗣源，议利用梁攻泽潞、汶阳无备。',10,'帝召李嗣源謀曰：「昭義阻命，梁將董璋攻迫澤州，梁志在澤、潞，不慮別有事生，汶陽無備，不可失也。」嗣源以為然。','同一计划的独立出处，不将地方无人守的情报认实际无一兵。',source='jiuwudaishi-029-yunzhou',relation='corroborates')
E=event('siyuan_marches_yunzhou','李存勖遣李嗣源率精兵五千自德胜趋郓州',10,'壬寅，遣嗣源将所部精兵五千自德胜趣郓州。',[('帝','遣军者'),('嗣源','率兵袭郓者')],when='923年闰四月壬寅',place='德胜、郓州',note='趣为趋，不改快照；五千为史载兵数，未做精确统计。')
claim('event',E,'description','《旧五代史》记壬寅率步骑五千，自河趋郓。',10,'壬寅，命嗣源率步騎五千，箝枚自河趨鄆。','同日出兵、兵数互证；旧史当夜入城和主书次日牙城拔分别保留。',source='jiuwudaishi-029-yunzhou',relation='corroborates')
event('gao_urges_night_advance','阴雨夜行，李嗣源军在杨刘遇阻，高行周劝进',10,'比及杨刘，日已暮，阴雨道黑，将士皆不欲进，高行周曰：“此天赞我也，彼必无备。”',[('嗣源','进军主将'),('高行周','劝夜行者')],when='923年闰四月壬寅夜',place='杨刘、郓州途中',note='天赞我为高行周判断，不作天意事实；彼必无备不是已核守兵配置。')
event('congke_opens_yunzhou_gate','李从珂先登郓州城，杀守卒，开关纳军',10,'夜，渡河至城下，郓人不知，李从珂先登，杀守卒，启关纳外兵，进攻牙城，城中大扰。',[('李从珂','先登开关者')],when='923年闰四月壬寅夜',place='郓州城、牙城',note='夜入外城与癸卯旦拔牙城拆分；无名守卒不虚建人物。')
E=event('yunzhou_captured','李嗣源军拔郓州牙城，刘遂严、燕颙奔大梁',10,'癸卯旦，嗣源兵尽入，遂拔牙城，刘遂严、燕颙奔大梁。',[('嗣源','取郓主将'),('刘遂严','失守后奔大梁者'),('燕颙','失守后奔大梁者')],when='923年闰四月癸卯旦；主书纪时',place='郓州、牙城、大梁',note='主书分壬寅出发夜入、癸卯旦拔牙；新旧史简记取城壬寅，日次不强统一。')
claim('event',E,'time_original','《新五代史》取郓州记壬寅。',10,'壬寅，李嗣源取鄆州。','主书癸卯旦、旧史壬寅当夜入城，细分环节或日界仍待纸本校核，保留异说。',source='xinwudaishi-005-923-founding',relation='conflicts')
claim('event',E,'description','《旧五代史》记壬寅当夜阴雨，乘城而入，郓州平。',10,'是夜陰雨，我師至城下，鄆人不覺，遂乘城而入，鄆州平。','旧史一笔平城与主书次晨牙城完结分清，未改主书时间。',source='jiuwudaishi-029-yunzhou',relation='corroborates')
event('siyuan_protects_yunzhou','李嗣源禁焚掠，抚吏民，将崔筜赵凤送兴唐',10,'嗣源禁焚掠，抚吏民，执知州事节度副使崔筜、判官赵凤送兴唐。',[('嗣源','禁焚掠并执送者'),('崔筜','被执送的知州事节度副使'),('赵凤','被执送的判官')],when='923年闰四月取郓之后',place='郓州、兴唐府',note='禁焚掠为命令，不据此断实际无任何劫掠；送兴唐不当两人此时已获新任。')
E=event('siyuan_tianping_appointment','李存勖以李嗣源为天平节度使',10,'即以嗣源为天平节度使。',[('帝','任命者'),('嗣源','新天平节度使')],when='923年闰四月取郓之后',place='天平军、郓州',note='李嗣源先前领横海与此次天平分阶段；李存勖赞语作为言论。')
claim('event',E,'description','《旧五代史》同记李嗣源任天平军节度使。',10,'製以李嗣源為天平軍節度使。','取郓后任新镇。',source='jiuwudaishi-029-yunzhou',relation='corroborates')
# Paragraph 11, Liang's response.
event('liang_executes_yunzhou_commanders','朱友贞处斩刘遂严、燕颙',11,'梁主闻郓州失守，大惧，斩刘遂严、燕颙于市，',[('梁主','处斩者'),('刘遂严','被斩的失守将'),('燕颙','被斩的失守将')],when='923年闰四月郓州失守后；确日未载',place='梁都市',note='于市地名未具不强填具体市坊；此为斩首，不推谋叛罪正式判文。')
for n in ['刘遂严','燕颙']:claim('person',people[n],'death_year',n+'于923年郓州失守后被朱友贞斩杀。',11,'斩刘遂严、燕颙于市，','主书明示，同年；不推生日或年龄。')
event('dai_demoted_xuanhua','朱友贞罢戴思远招讨使，降授宣化留后',11,'罢戴思远招讨使，降授宣化留后，',[('梁主','罢降者'),('戴思远','被罢招讨、降留后者')],when='923年闰四月郓州失守后',place='后梁、宣化军',note='留后与节度使不直接等同，不写处决。')
event('liang_reproaches_commanders','朱友贞责段凝、王彦章等，令进战',11,'遣使诘让北面诸将段凝、王彦章等，趣令进战。',[('梁主','遣使责战者'),('段凝','受责将'),('王彦章','受责将')],when='923年郓州失守后',place='后梁北面军',note='使者未具名不虚建；趣令为催促，不推各将实际按令开战时间。')
E=event('jing_xiang_remonstrates','敬翔持绳入见拟自缢，朱友贞止之并问言',11,'引绳将自经。梁主止之，問所欲言，'.replace('問','问'),[('敬翔','以将自经劝谏者'),('梁主','止其自经并询问者')],when='923年郓州失守后、任王彦章前',place='后梁朝廷',note='将自经被止，本段不是敬翔自杀死亡；其实际死亡是后续梁亡时。')
claim('event',E,'description','《新五代史》同记敬翔持绳拟自经，末帝使人止之。',11,'乃引繩將自經。末帝使人止之，問所欲言。','未遂与本年末实际死严格分开。',source='xinwudaishi-032-yanzhang-command',relation='corroborates')
E=event('yanzhang_becomes_commander','敬翔荐王彦章，朱友贞以其代戴思远，段凝为副',11,'翔曰：“事急矣，非用王彦章为大将，不可救也。”梁主从之，以彦章代思远为北面招讨使，仍以段凝为副。',[('敬翔','荐王彦章者'),('梁主','任命者'),('彦章','北面招讨使'),('段凝','招讨副使')],when='923年郓州失守后，五月辛酉前',place='后梁北面军',note='仍以段凝为副是本次军职，未推出永久君臣关系；敬翔荐言另作引用。')
claim('event',E,'description','敬翔建议不用王彦章为大将即不可救梁。',11,'翔曰：“事急矣，非用王彦章为大将，不可救也。”','为敬翔急议，不作能力排名客观结论。')
claim('event',E,'description','《新五代史》亦记召王彦章为招讨、段凝为副。',11,'末帝乃召彥章為招討使，以段凝為副。','同事印证，末帝为朱友贞。',source='xinwudaishi-032-yanzhang-command',relation='corroborates')
# Paragraph 12, Tang-Wu diplomacy.
E=event('cunxu_chanzhou_guard_desheng','李存勖屯澶州，命朱守殷守德胜，戒备王彦章',12,'帝闻之，自将亲军屯澶州，命蕃汉马步都虞候硃守殷守德胜，戒之曰：',[('帝','亲屯澶州并戒备者'),('硃守殷','德胜守将')],when='923年王彦章受命后、五月辛酉前',place='澶州、德胜',note='硃守殷规范展示朱守殷；守地与帝屯澶州分明。')
claim('event',E,'description','《旧五代史》记朱守殷守德胜南城，李存勖因惧王彦章而幸澶州。',12,'時朱守殷守德勝南城，帝懼彥章奔衝，遂幸澶州。','旧史同事，在下一段决战中需另存新史救援过程差异。',source='jiuwudaishi-029-yunzhou',relation='corroborates')
claim('person',people['朱守殷'],'description','主书记朱守殷曾是李存勖幼时所役苍头。',12,'守殷，王幼时所役苍头也。','旧事只记来源身份；不将奴仆身份强定923年，也不生成终身统属关系。')
event('tang_requests_wu_attack_liang','李存勖遣书吴王，告取郓并请共同击梁',12,'又遣使遗吴王书，告以已克郓州，请同举兵击梁。',[('帝','遣书邀击梁者'),('吴王','书函对象杨溥')],when='923年取郓后；五月使者至吴',place='后唐、吴',note='请同举兵不等实际联军或盟约达成，使者未名不虚建。')
event('xu_wen_seaborne_plan_abandoned','使者至吴，徐温拟舟师待胜负，严可求劝止',12,'五月，使者至吴，徐温欲持两端，将舟师循海而北，助其胜者。严可求曰：“若梁人邀我登陆为援，何以拒之？”温乃止。',[('徐温','拟两端援胜后停止者'),('严可求','以登陆难拒劝止者')],when='923年五月；确日未载',place='吴、海路',note='欲与乃止明确未执行，不建立吴舟师已北上的军事行动，也不推吴唐结盟。')
# Paragraph 13, Desheng south fort.
E=event('yanzhang_three_day_promise','王彦章答朱友贞称三日破敌，驰两日至滑州',13,'梁主召问王彦章以破敌之期，彦章对曰：“三日。”左右皆失笑。彦章出，两日，驰至滑州。',[('梁主','问破敌期者'),('王彦章','答三日并驰滑州者')],when='923年五月辛酉前；相对日数依主书',place='梁廷、滑州',note='三日为应答计划，是否实现据后续战事；相对两日不换公历日。')
claim('event',E,'description','《新五代史》同记答三日、驰两日至滑州。',13,'末帝問破敵之期，彥章對曰：「三日。」左右皆失笑。','新史独立传记互证答期。',source='xinwudaishi-032-yanzhang-command',relation='corroborates')
event('yanzhang_secret_boat_preparation','王彦章置酒，暗备舟兵斧炭，沿河南岸夜袭',13,'辛酉，置酒大会，阴遣人具舟于杨村；夜，命甲士六百，皆持巨斧，载冶者，具鞴炭，乘流而下。',[('彦章','备舟夜袭指挥者')],when='923年五月辛酉夜',place='滑州、杨村、德胜',note='冶者未具名不建人；六百为舟兵史载，与陆上精兵数千分开。')
claim('event',used[13][-1],'description','《新五代史》同记六百斧兵与冶者鞴炭。',13,'命甲士六百人皆持巨斧，載冶者，具鞴炭，乘流而下。','繁体引用保留；数目作为史载，而非独立统计。',source='xinwudaishi-032-desheng',relation='corroborates')
E=event('desheng_bridge_destroyed','梁舟兵烧断铁锁，斩浮桥，王彦章急击德胜南城',13,'舟中兵举锁烧断之，因以巨斧斩浮桥，而彦章引兵急击南城。',[('彦章','攻德胜南城主将')],when='923年五月辛酉夜',place='德胜浮桥、南城',note='烧锁斩桥明确军动作，不造具体工匠姓名或器械设计参数。')
claim('event',E,'description','《旧五代史》记五月辛酉王彦章夜率舟师断浮桥、陷南城。',13,'五月辛酉，彥章夜率舟師自楊村浮河而下，斷德勝之浮橋，攻南城，陷之。','同日同动作互证。',source='jiuwudaishi-029-923-desheng',relation='corroborates')
E=event('desheng_south_falls','德胜南城陷，朱守殷渡河救援不及',13,'浮桥断，南城遂破，斩首数千级。时受命适三日矣。守殷以小舟载甲士济河救之，不及。',[('王彦章','取南城者'),('守殷','渡救不及者')],when='923年五月辛酉；受命三日据主书',place='德胜南城、河渡',note='同段硃安殷疑为硃守殷转录，按前后守殷和两史同事确认同人，不新建朱安殷；斩数千为史载。')
claim('event',E,'description','《新五代史》同记断桥破南城三日，但称庄宗驰援到时城已破。',13,'即馳騎救之，行二十里，而得夾寨報者曰：「彥章兵已至。」比至，而南城破矣。','主书本段朱守殷小舟救不及，新史庄宗自魏驰救；前段主书帝屯澶州，记程不同，各按书保留，不合成唯一路线。',source='xinwudaishi-032-desheng',relation='conflicts')
event('yanzhang_takes_river_forts','王彦章连拔潘张、麻家口、景店诸寨',13,'彦章进攻潘张、麻家口、景店诸寨，皆拔之，声势大振。',[('彦章','攻拔诸寨者')],when='923年五月德胜南城破后；确日未载',place='潘张、麻家口、景店',note='主书麻家口与后续马家口可能地名异写，先原字保留不擅作现代定位；攻拔范围仅列诸寨。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(10,14):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='连续校核闰四月至五月袭郓和德胜；取郓壬寅/癸卯分存、所报兵数带归属、敬翔自经未遂非死亡、吴舟师计划未执行、硃安殷疑字不另建，救援过程异说保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(10,14)],next_paragraph=Q[14]['id'],supplements=supplements,coverage='卷272正文第10—13段，原文件15—18行；主书来源复用第二批分段快照。',reviewed_questions=[
 {'paragraph_id':Q[10]['id'],'note':'闰四月甲午契丹未署主将；先是戴思远部署年null；卢顺密兵数和失众心为来报；壬寅夜入与癸卯晨取牙区分；新史取郓壬寅不同存；禁掠不推无掠。'},
 {'paragraph_id':Q[11]['id'],'note':'刘遂严燕颙死亡年明确；敬翔将自经被止，不是实际死亡；王彦章任北面、段凝副，不建私人敌对或未名使者。'},
 {'paragraph_id':Q[12]['id'],'note':'朱守殷硃字规范统一，苍头旧身份不定本年；吴王杨溥，遣书不等盟约；徐温拟两端与严可求劝止明确未出舟师。'},
 {'paragraph_id':Q[13]['id'],'note':'辛酉承五月、三日是主书相对记日；六百舟兵与数千陆兵区分；硃安殷疑字复用朱守殷；新史庄宗自魏驰援与主书澶州/小舟救不及过程并列；麻家口原地名待校。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
