# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 30–35."""
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
 ('tongjian-272-923-zhongdu',YEAR/'part-06/sources/library/tongjian-272-923-zhongdu','460d5032','司马光等'),
 ('tongjian-272-923-liang-last-court',P/'sources/library/tongjian-272-923-liang-last-court','89e35e02','司马光等'),
 ('jiuwudaishi-010-liang-fall',P/'sources/library/jiuwudaishi-010-liang-fall','89e35e02','薛居正等'),
 ('jiuwudaishi-030-entry-daliang',P/'sources/library/jiuwudaishi-030-entry-daliang','89e35e02','薛居正等'),
 ('xinwudaishi-032-yanzhang-death',P/'sources/library/xinwudaishi-032-yanzhang-death','89e35e02','欧阳修'),
 ('xinwudaishi-013-liang-princes',P/'sources/library/xinwudaishi-013-liang-princes','89e35e02','欧阳修'),
 ('jiuwudaishi-012-youhui',P/'sources/library/jiuwudaishi-012-youhui','89e35e02','薛居正等'),
 ('jiuwudaishi-030-923-zhongdu',YEAR/'part-06/sources/library/jiuwudaishi-030-923-zhongdu','460d5032','薛居正等'),
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p030-p035',
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
for n in range(30, 36):
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
people, used, reused, supplements = {}, {}, {'jiuwudaishi-030-923-zhongdu','xinwudaishi-005-923-founding'}, []

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
    ck = f'claim_zztj_272_0923_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'曹氏（李存勖母）','太妃':'刘氏（李克用妻）',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦','曹氏':'曹氏（李存勖母）','刘氏':'刘氏（李克用妻）','武皇':'李克用','考晋王':'李克用','上':'李存勖','帝':'李存勖','执宜':'执宜（李存勖曾祖）','国昌':'李国昌','继岌':'李继岌','硃守殷':'朱守殷','硃安殷':'朱守殷','守殷':'朱守殷','王铁枪':'王彦章','彦章':'王彦章','翔':'敬翔','顺密':'卢顺密','嗣源':'李嗣源','遂严':'刘遂严','颙':'燕颙','梁末帝':'朱友贞','崇韬':'郭崇韬','延孝':'康延孝','延光':'范延光','宗侃':'王宗侃','赵':'赵岩','张':'张汉杰','任团':'任团','圜':'任圜','团':'任团','绍斌':'赵德钧','李绍斌':'赵德钧','凝':'段凝','在珣':'顾在珣','彦朗':'顾彦朗','嘉王宗寿':'王宗寿','魏国夫人刘氏':'刘夫人（李存勖妻）','李绍奇':'夏鲁奇','廷隐':'赵廷隐','嗣彬':'刘嗣彬','知俊':'刘知俊','振':'李振','张宗奭':'张全义'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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

# Each span is a contiguous, verbatim part of its chronicle paragraph.
def span(n,start,end=None):
 t=Q[n]['text']; a=t.index(start); b=t.index(end,a)+len(end) if end else len(t); return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('yanzhang_treatment_refusal','李存勖命为王彦章治伤并招降，王彦章拒绝',30,'帝惜彦章之材','此我所不为也。”',[('帝','赐药招降者'),('彦章','拒绝归唐者')],when='923年十月甲戌中都战后',place='中都',note='招降与拒绝是本段动作；昔日轻侮和天命言论为当事表述，不作独立因果。')
E=ev('siyuan_persuades_yanzhang','李嗣源奉命劝降王彦章，彦章以其小名相称',30,'帝复遣李嗣源','故以小名呼之。',[('帝','遣劝降者'),('李嗣源','奉命劝降者'),('彦章','以小名相称者')],when='923年十月甲戌战后',place='中都')
claim('person',people['李嗣源'],'aliases','主书记李嗣源小名邈佶烈。',30,'汝非邈佶烈乎？”彦章素轻嗣源，故以小名呼之。','保留出处支持的小名，不新建邈佶烈人物；不改写旧批档案。')
ev('cunxu_credits_victory','李存勖称中都之功出于李嗣源与郭崇韬',30,'于是诸将称贺','大事去矣。”',[('帝','称功者'),('李嗣源','受称功者'),('崇韬','受称功者'),('绍宏','被回顾先前建议者')],when='923年十月甲戌战后',place='中都',note='功劳归属是帝的评价；绍宏未必当场在场，只是被言及。')
ev('daliang_strategy_choice','康延孝李嗣源主张速取大梁，李存勖采纳',30,'帝又谓诸将曰','诸军皆踊跃愿行。',[('帝','问策并采纳者'),('延孝','请速取大梁者'),('李嗣源','请千骑前驱者'),('凝','被讨论的梁将')],when='923年十月甲戌战后',place='中都、大梁',note='诸将先广地为未采方案；段凝知情、渡河困难和数日估计均为议策判断，千骑是请率兵数，不虚造实际战果。')
ev('siyuan_rapid_march','李嗣源率前军倍道进趋大梁',31,'是夕','趣大梁。',[('嗣源','前军主将')],when='923年十月甲戌夕',place='中都至大梁')
E=ev('yanzhang_execution','李存勖离中都后下令斩王彦章',31,'乙亥','遂斩之。',[('帝','命斩者'),('彦章','被处斩者'),('凝','彦章回答所言及的梁将')],when='923年十月乙亥',place='中都出发途中；旧史记任城',note='段凝精兵六万为彦章答语，不当独立清点结果。中使未具名；彦章被俘与此处处斩区分。')
claim('person',people['王彦章'],'death_year','王彦章于923年十月乙亥被斩。',31,'帝知其终不为用，遂斩之。','乙亥承本段，不以中都战甲戌为死亡日。')
claim('event',E,'location_name','《旧五代史》记王彦章翌日死于任城。',31,'翌日，彥章死於任城。','翌日承甲戌，地点作为旧史补充，保留与主书行军语境。',source='jiuwudaishi-010-liang-fall')
E=ev('caozhou_surrender','唐军至曹州，梁守将投降',32,'丁丑','梁守将降。',[('帝','率唐军至曹州者')],when='923年十月丁丑',place='曹州',note='帝主语承前文；守将未名，不把已俘李知节当此次守将。')
# Royal court responses, proposals and actual acts are kept distinct.
ev('liang_defeat_report','大梁接到中都败讯，朱友贞聚族哭并问计',33,'王彦章败卒','皆莫能对。',[('梁主','接报问计者'),('彦章','败讯所涉及者')],when='923年十月甲戌后、戊寅前',place='大梁',note='王彦章不是大梁报告者，败卒未名；运祚尽为朱友贞言语。')
ev('jing_xiang_last_advice','敬翔述失策与援军受阻，向朱友贞请死',33,'梁主谓敬翔曰','相向恸哭。',[('梁主','问计者'),('敬翔','陈言请死者'),('凝','陈言中的梁将')],when='923年十月灭梁前',place='大梁',note='愿先赐死为请求，本段未记敬翔死亡；出居避敌及合战均未执行，良平典故不建923年参与者。')
E=ev('hanlun_failed_messenger','张汉伦赴段凝军，在滑州坠马伤足又被水阻',33,'梁主遣张汉伦','不能进。',[('梁主','遣使者'),('张汉伦','受伤受阻的使者'),('凝','拟送达对象')],when='923年十月灭梁前',place='滑州',note='段凝是拟送达对象，未确认接到此使；受阻不等军队战败。')
claim('event',E,'description','《旧五代史》同记张汉伦坠马伤足、水潦阻行。',33,'漢倫墜馬傷足，復限水潦，不能進。','同事补证。',source='jiuwudaishi-010-liang-fall',relation='corroborates')
ev('zhu_gui_rejected_sortie','朱珪请率控鹤军出战，朱友贞未准，王瓒奉命驱市民守城',33,'时城中尚有控鹤军','乘城为备。',[('硃珪','请战者'),('梁主','未准请战并命守城者'),('王瓚','驱市民守城者')],when='923年十月灭梁前',place='大梁',note='硃珪复用朱珪；请战未获准，不作实际出击。主书数千与旧史四千分别保留。')
E=ev('youhui_recalled_imprisoned','朱友诲遭谋乱举报被召回，与朱友谅朱友能幽禁',33,'初，梁陕州','并幽于别第。',[('友诲','被举报召回幽禁者'),('梁主','召回者'),('友谅','被幽禁的兄长'),('友能','被幽禁的兄长')],when='主书追叙；召回和幽禁确年未载',year=None,place='陕州、大梁',note='或言谋乱是举报，不等经独立证实的叛乱。新史述欲以州兵为乱，表述差异保留。')
claim('event',E,'description','《新五代史》记欲以州兵为乱、召还及幽囚。',33,'友誨為陝州節度使，欲以州兵為亂，末帝召還京師，與友諒、友能皆被幽囚。','主书或言禁军，新史州兵且直述欲乱，不把两种表述混成确证。',source='xinwudaishi-013-liang-princes',relation='conflicts')
qt='邵王友诲，全昱之子也，'
relationship('全昱','友诲','父亲',33,qt,'A朱全昱是B朱友诲的父亲。')
qt='梁主召还，与其兄友谅、友能并幽于别第。'
for name in ['友谅','友能']:relationship(name,'友诲','兄长',33,qt,'其兄明示相对友诲长幼，不据并列顺序推友谅与友能谁年长。')
E=ev('liang_princes_killed_disputed','《通鉴》记朱友贞疑宗室谋乱并杀五名诸王',33,'及唐师将至','尽杀之。',[('梁主','主书所记命杀者'),('友诲','主书所记被杀者'),('友谅','主书所记被杀者'),('友能','主书所记被杀者'),('友雍','主书所记被杀者'),('友徽','主书所记被杀者')],when='923年十月唐军入大梁前；他书记遇害时间和施害方有异',place='大梁',note='前文被幽三人与皇弟二人承接；不把疑谋乱写成确定反叛。与旧新五代史死亡记载冲突，分别引用待考。')
claim('event',E,'description','《新五代史》记梁亡、庄宗入汴后朱友诲朱友谅朱友能皆见杀。',33,'梁亡，莊宗入汴，皆見殺。','与主书入城前梁主杀三人不同；被动见杀未具名凶手，不推出庄宗亲自下令。',source='xinwudaishi-013-liang-princes',relation='conflicts')
claim('event',E,'description','《旧五代史》朱友诲传称其后为唐兵所杀。',33,'坐友能反廢，後為唐兵所殺。','施害方与通鉴梁主不同，不能繁简转换消解异文；三人死亡争议并列，不改五人统一死于唐军。',source='jiuwudaishi-012-youhui',relation='conflicts')
for name in ['友雍','友徽']:relationship('梁主',name,'兄长',33,'并皇弟贺王友雍、建王友徽尽杀之。','皇弟相对于朱友贞，A是B兄长；未据封号排序推两弟长幼。')
ev('liang_secret_edicts_fail','朱友贞遣亲信持蜡诏催段凝军，受命者逃匿',33,'梁主登建国楼','皆亡匿。',[('梁主','择亲信催军者'),('凝','诏令拟送达者')],when='923年十月灭梁前',place='建国楼',note='使者未名，诏未确认到达；逃匿是主书记结果。')
ev('liang_escape_options_rejected','皇甫麟赵岩反对逃往段凝军等方案，朱友贞停行',33,'或请幸洛阳','梁主乃止。',[('梁主','未采外逃者'),('皇甫麟','质疑段凝能力者'),('赵岩','反对下楼者'),('凝','拟投军及评价对象')],when='923年十月灭梁前',place='大梁、洛阳和段凝军为方案目的地',note='洛阳和赴军是未实行方案；官由幸进、胆破与尽节判断是皇甫麟话，不作已核实心理。')
ev('zheng_jue_false_surrender_plan','郑珏提出携传国宝诈降，自承未能保全局面',33,'复召宰相谋之','左右皆缩颈而笑。',[('郑珏','提出未执行策略者'),('梁主','询问者')],when='923年十月灭梁前',place='大梁',note='未真实诈降，不建立郑珏此时已降唐的关系。')
ev('seal_stolen_to_tang','朱友贞卧内传国宝被左右窃走迎唐军',33,'梁主日夜涕泣',None,[('梁主','失宝者')],when='923年十月灭梁前',place='大梁',note='左右未名，不把郑珏诈降提议者当盗宝人。')
ev('zhao_yan_flees_xuzhou','赵岩闻唐军过曹州后逃奔许州',34,'戊寅','遂奔许州。',[('赵岩','奔许州者')],when='923年十月戊寅',place='大梁至许州',note='温许州指温韬，必不负为赵岩预期，不当温韬确已接纳。')
E=ev('youzhen_huangfu_deaths','朱友贞命皇甫麟杀己，皇甫麟最终杀梁主后自杀',34,'梁主谓皇甫麟曰','因自杀。',[('梁主','请求杀己并被杀的末帝'),('皇甫麟','杀梁主后自杀者')],when='923年十月戊寅；旧史补夕',place='大梁建国楼',note='不把皇甫麟初拒命当最后拒绝；俱死为原话，后行动分别记录。')
claim('event',E,'time_original','《旧五代史》记戊寅夕于建国楼廊下，麟进刃、随即自刭。',34,'戊寅夕，麟進刃於建國樓之廊下，帝崩。','补夜间和地点，未换公历。',source='jiuwudaishi-010-liang-fall')
for name in ['朱友贞','皇甫麟']:claim('person',people[name],'death_year',name+'卒于923年十月戊寅。',34,'麟遂弑梁主，因自杀。','主语承梁主与麟，保留两人分别死亡。')
ev('youzhen_chronicle_evaluation','《通鉴》评朱友贞俭约但宠信赵张、疏弃旧臣',34,'梁主为人',None,[('梁主','主书评价对象')],when='朱友贞生前的总结性评价；确年未定',year=None,place='后梁朝廷',note='作者评价附来源，不作现代独立研究结论，不因总结出现在戊寅而当日才开始宠信。')
E=ev('liang_falls','唐军入大梁，王瓒出降，后梁灭亡',35,'己卯旦','使各复其位。',[('李嗣源','commander'),('帝','commander'),('王瓚','开封门出降者')],when='923年十月己卯',place='大梁封丘门、梁门',stable_key='event_liang_falls',note='复用既有后梁灭亡稳定事件及两主将参与key；此段记入城，前日梁主死亡另有具体事件，不再建另一梁亡节点。')
used[34].append(E)
claim('event',E,'description','后梁末帝死于唐军入城前一日。',34,'麟遂弑梁主，因自杀。','作为已存在梁亡事件的连续前日补证，不改档案key。')
claim('event',E,'description','《新五代史》庄宗本纪记十月己卯灭梁。',35,'己卯，滅梁。','本纪日序互证，不把唐入城日当梁主死亡日。',source='xinwudaishi-005-923-founding',relation='corroborates')
ev('cunxu_credits_siyuan_daliang','入城后李存勖称李嗣源父子有功并言共天下',35,'李嗣源迎贺','天下与尔共之。”',[('帝','称功者'),('李嗣源','受称功者')],when='923年十月己卯',place='大梁',note='父子未具名子，不添此句未载的参与者；共天下是话语，不建土地封赏行为。')
ev('liang_emperor_head_presented','李存勖求访梁主，有人献其首级',35,'帝命访求梁主',None,[('帝','求访者'),('梁主','所求访并被献首的死者')],when='923年十月己卯',place='大梁',note='献者未名，不指作皇甫麟或王瓒；朱友贞已于戊寅死。')

claim('event','event_zztj_272_0923_yanzhang_treatment_refusal','description','《新五代史》同记赐药封创、招降而拒。',30,'莊宗惻然，賜藥以封其創。','同事补证；保留新史原称莊宗，实体仍为李存勖。',source='xinwudaishi-032-yanzhang-death',relation='corroborates')
claim('event','event_zztj_272_0923_yanzhang_execution','description','《新五代史》记王彦章被杀，年六十一。',31,'遂見殺，年六十一。','新史未给此句确日，乙亥据通鉴；不反算出生年。',source='xinwudaishi-032-yanzhang-death',relation='adds')
claim('event','event_zztj_272_0923_caozhou_surrender','description','《旧五代史》同记丁丑曹州郡将出降。',32,'丁丑，次曹州，郡將出降。','互证日期，郡将仍未具名。',source='jiuwudaishi-030-923-zhongdu',relation='corroborates')
claim('event','event_liang_falls','description','《旧五代史》同记己卯前军攻封丘门、王瓒降、帝入大梁门。',35,'己卯遲明，前軍至汴城，嗣源令左右捉生攻封丘門，梁開封尹王瓚請以城降。俄而帝與大軍繼至，王瓚迎帝自大梁門入。','梁门与大梁门分别保留书名用字；随后末帝名朱鍠疑异字，未据此另造人物或确定新别名。周匝等后续补叙留待对应主线段落。',source='jiuwudaishi-030-entry-daliang',relation='corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续录至梁亡；药伤招降与处斩分开；策略不当执行，言及人物非在场；兄长父亲方向按原文；宗室遇害施害方和时间的通鉴与旧新史异说并列；皇甫麟与朱友贞戊寅死、己卯入城分日；梁亡旧key复用；展示简体，快照原字不改。'
for n in range(30,36):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(30,36)],next_paragraph=Q[36]['id'],supplements=supplements,coverage='卷272第30—35段，原文件35—40行；至己卯唐军入大梁、后梁灭亡。923年仍有后续段落。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(30,36)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
