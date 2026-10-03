# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 67–76."""
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
 ('tongjian-272-923-luoyang-move',YEAR/'part-09/sources/library/tongjian-272-923-luoyang-move','83be3260','司马光等'),
 ('tongjian-272-923-year-end',P/'sources/library/tongjian-272-923-year-end','b88b07ee','司马光等'),
 *[(key,P/'sources/library'/key,'b88b07ee',author) for key,author in [
 ('jiuwudaishi-030-luoyang-entry','薛居正等'),('jiuwudaishi-030-law-jitao','薛居正等'),
 ('jiuwudaishi-052-jitao-pardon','薛居正等'),('jiuwudaishi-052-jida-death','薛居正等'),
 ('xinwudaishi-036-jitao','欧阳修'),('xinwudaishi-036-jida','欧阳修'),
 ('xinwudaishi-061-luping','欧阳修'),('xinwudaishi-069-gao-departure','欧阳修')]],
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p067-p076',
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
for n in range(67, 77):
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
people, used, reused, supplements = {}, {}, {'tongjian-272-923-luoyang-move','xinwudaishi-005-923-founding'}, []

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
    ck = f'claim_zztj_272_0923_11_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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




# Quotes preserve the contiguous source paragraph.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('quanyi_jixing_honours','张全义加守尚书令，高季兴加守中书令',67,'己未','高季兴守中书令。',[('张全义','加官者'),('高季兴','加官者')],when='923年十一月己未',place='唐廷',note='高季兴沿用高季昌稳定主体，非另人。')
E=ev('jixing_suggests_shu_first','李存勖问吴蜀征讨次序，高季兴建议先取蜀再顺流攻吴',67,'时季兴',None,[('高季兴','建议者'),('上','问策并称善者')],when='923年十一月入朝期间；问答确日未明',place='唐廷',note='吴贫蜀富、蜀主荒怨、必克为高氏陈说，先蜀是建议，未记录此时战争已执行。')
claim('event',E,'description','《新五代史》同记高季兴建议先蜀，并请本道兵先进。',67,'季興曰：「宜先蜀，臣請以本道兵先進。」','同一建议补具体请兵，不能提前录成已出兵。',source='xinwudaishi-069-gao-departure',relation='corroborates')
E=ev('jingzhao_xijing_restored','永平军大安府复称西京京兆府',68,'辛酉',None,[],when='923年十一月辛酉',place='大安府、京兆府',note='府军名号恢复，不等本日迁都至京兆；洛阳另记。')
old=(sources['jiuwudaishi-030-luoyang-entry']/'source.txt').read_text()
# The annal groups restorations differently from Tongjian.
needle='詔改偽梁永平軍大安府復為西京京兆府'
claim('event',E,'description','旧史亦记大安府复西京京兆府，编排在十二月戊寅条后。',68,needle,'主书辛酉十一月与旧史编排月份存在差异，保留而不强行同日。',source='jiuwudaishi-030-luoyang-entry',relation='conflicts')
E=ev('emperor_leaves_daliang','李存勖从大梁出发',69,'甲子','帝发大梁',[('帝','出发者')],when='923年十一月甲子',place='大梁',note='前批决策与诏文武先赴洛阳不是本次实际出发。')
claim('event',E,'description','旧史同记甲子车驾发汴州。',69,'甲子，車駕發汴州。','大梁、汴州指本次出发地，不据此推断全部百官同日同行。',source='jiuwudaishi-030-luoyang-entry',relation='corroborates')
E=ev('emperor_arrives_luoyang','李存勖抵达洛阳',69,'十二月',None,[('帝','抵达者')],when='923年十二月庚午',place='洛阳')
claim('event',E,'description','旧史补庚午朔抵西京，由石桥设仪仗迎入大内。',69,'十二月庚午朔，車駕至西京。是日，有司自石橋具儀仗法物，迎引入於大內。','此西京为洛阳，与京兆府西京称名应依地理上下文区分。',source='jiuwudaishi-030-luoyang-entry',relation='corroborates')
ev('du_jianhui_left_chancellor','钱镠以行军司马杜建徽为左丞相',70,'吴越王',None,[('吴越王镠','任命者'),('杜建徽','受任者')],when='923年十二月本段；确日未载',place='吴越')
ev('bianzhou_detached_palace','唐廷诏以汴州宫苑为行宫',71,'壬申',None,[('帝','诏令者')],when='923年十二月壬申',place='汴州宫苑',note='规定行宫用途，非本日焚毁或弃置。')
for code,start,end,title,place in [
 ('yaozhou_shunyi','以耀州','为顺义军','耀州改为顺义军','耀州'),
 ('yanzhou_zhangwu','延州','为彰武军','延州改为彰武军','延州'),
 ('dengzhou_weisheng','邓州','为威胜军','邓州改为威胜军','邓州'),
 ('jinzhou_jianxiong','晋州','为建雄军','晋州改为建雄军','晋州'),
 ('anzhou_anyuan','安州','为安远军','安州改为安远军','安州')]:
 E=ev(code,title,72,start,end,[],when='923年十二月本段；主书未单列日次',place=place,note='不能将前段壬申自动沿用为确日；仅录军名变更。')
 exact={'耀州':'耀州靜勝軍復為順義軍','延州':'延州為彰武軍','邓州':'鄧州為威勝軍','晋州':'晉州為建雄軍','安州':'安州為安遠軍'}[place]
 claim('event',E,'description','旧史亦记此军名恢复。',72,exact,'旧史集中在戊寅条后，主书本句未列日期；日序待考。',source='jiuwudaishi-030-luoyang-entry',relation='corroborates')
ev('other_fan_old_names','其余藩镇恢复唐时旧名',72,'自馀',None,[],when='923年十二月本段；确日未载',place='唐诸藩镇',note='自余概述，不据此虚构所有军镇完整名单。')
E=ev('dingzhou_law_copy_request','御史台请求定州录进唐律令格式，李存勖准奏',73,'庚辰',None,[('帝','准奏者'),('朱温','奏文指称删焚旧法的已故人')],when='923年十二月庚辰',place='唐廷、定州敕库',note='删改焚本、伪廷之法是奏文陈述；闻独有为听闻，不证明全国仅一套；准录进不是副本已交付。')
claim('event',E,'description','旧史同庚辰请求定州写副本进纳获准。',73,'請行用本朝律令格式，今訪聞唯定州有本朝法書，望下本州寫副本進納。','访闻性质、请求与完成交付区别保留。',source='jiuwudaishi-030-law-jitao',relation='corroborates')
E=ev('jitao_summoned_debate','李继韬闻梁亡欲走契丹，奉诏入朝前李继远劝据城自守',74,'李继韬闻','往必无虞。”',[('继韬','被征者、拟逃者'),('继远','劝不入朝者')],when='923年梁亡后、十一月入朝前；确日未载',place='上党至唐廷',note='欲北走是未遂设想；匿名季父称谓与安慰话语不新建血缘关系。')
E=ev('yang_jitao_bribes','李继韬随母杨氏入朝，携银四十万两及他货行赂',74,'继韬母杨氏','不可无后。”',[('继韬','随母入朝行赂者'),('杨氏','母亲、偕行者'),('李嗣昭','求情话语所举的已故功臣')],when='923年梁亡后入朝期间；确日未载',place='唐廷',note='百万为家赀概述，四十万两是主书携银数；无邪谋为伶宦辩词，不作无罪结论。')
claim('event',E,'description','新史称携银数十万两，以行贩积财为背景。',74,'乃齎銀數十萬兩至京師，厚賂宦官、伶人，','主书四十万两、新史数十万两粒度不同；不换算现代重量，积财背景未给确年。',source='xinwudaishi-036-jitao')
relationship('杨氏','继韬','母亲',74,'继韬母杨氏，','A杨氏是B李继韬母亲，不能据此给全部李氏兄弟推同母。')
E=ev('yang_liu_intercession','杨氏入宫求哀，刘夫人为李继韬进言',74,'杨氏复','刘夫人亦为之言。',[('杨氏','入宫求哀者'),('魏国夫人刘氏','进言者'),('帝','受求哀者')],when='923年李继韬入见待罪前',place='唐宫',note='主书泣请其死用语保留，结合求哀与获释语境记录求情，不解作请求杀子；刘夫人为帝妻，与太妃刘氏区别。')
claim('event',E,'description','旧史载杨夫人向刘皇后哀祈，刘氏言先人之功，李继韬获原。',74,'楊夫人亦於宮中哀祈劉皇后，後每於莊宗前泣言先人之功，以動聖情，由是原之。','旧史用刘皇后称谓，可能叙传以后号追称；本站当前阶段沿用刘夫人主体，不提前立册后事件。',source='jiuwudaishi-052-jitao-pardon',relation='corroborates')
E=ev('jitao_pardoned_hunts','李存勖释放待罪的李继韬，留月余并屡同游畋',74,'及继韬入见','宠待如故。',[('继韬','获释、留京游畋者'),('上','释放者')],when='923年入朝后月余至十二月再得罪前',place='唐廷',note='月余为历时，不把全部行动压在十二月辛巳一天。')
claim('event',E,'description','新史亦记释李继韬、从猎获宠。',74,'由是莊宗釋繼韜。嘗從獵，寵倖無間。','嘗为不定次，不能虚构每次猎期。',source='xinwudaishi-036-jitao',relation='corroborates')
ev('cunwo_reproaches_jitao','李存渥诋责李继韬，李继韬行赂求还镇被拒',74,'皇弟','上不许。',[('存渥','责李继韬者'),('继韬','求还镇者'),('上','不准还镇者')],when='923年在京获释后',place='唐廷',note='心不自安为主书叙述；再行赂与求归皆记，未把想法造为已还镇。')
relationship('帝','存渥','兄长',74,'皇弟义成节度使、同平章事存渥','复用922已有关系，A李存勖是B李存渥兄长。')
E=ev('jitao_secret_fire_letter','李继韬秘密致书李继远，教军士纵火以图获遣还镇，事情泄露',74,'继韬潜','事泄，',[('继韬','策划及致书者'),('继远','收信者')],when='923年在京求还镇不获准后',place='唐廷至上党',note='教纵火为指令，不能认定军士已经点火或帝已遣其抚安。')
claim('event',E,'description','新史亦记阴告继远令军中起变以求安缉，事泄。',74,'繼韜陰使人告繼遠，令起變於軍中，冀天子遣己往安緝之，事泄，','两书策划范围不同，主书明确纵火；都未证明已执行。',source='xinwudaishi-036-jitao',relation='corroborates')
E=ev('jitao_demoted','李继韬贬登州长史',74,'辛巳','贬登州长史，',[('继韬','贬职者')],when='923年十二月辛巳',place='唐廷',note='授贬职不是已赴登州任事。')
claim('event',E,'description','旧史亦同辛巳诏贬安义军节度使李继韬为登州长史。',74,'辛巳，詔貶安義軍節度使李繼韜為登州長史，','对应贬职，不将寻斩硬锁同一时刻。',source='jiuwudaishi-030-law-jitao',relation='corroborates')
E=ev('jitao_two_sons_executed','李继韬随后在天津桥南被斩，二子亦被杀',74,'寻斩','并其二子。',[('继韬','被处斩者')],when='923年十二月辛巳贬职后不久；主书作寻',place='洛阳天津桥南',note='二子未名，不造人物名字；新史本纪合记辛巳伏诛，传记未给另日。')
claim('event',E,'time_original','新史本纪辛巳记李继韬伏诛。',74,'辛巳，李繼韜伏誅。','主书贬后寻斩，新史本纪辛巳伏诛，日期粒度并列。',source='xinwudaishi-005-923-founding',relation='corroborates')
claim('event',E,'description','旧史补二子此前质于汴，梁亡被唐得，至此同被诛。',74,'二子齠年質於汴，莊宗收城得之，','旧事作为此次遇害背景，未知姓名与年龄不生成假资料。',source='jiuwudaishi-052-jitao-pardon')
ev('jiyuan_executed_jida_patrol','唐遣使上党斩李继远，任李继达为军城巡检',74,'遣使','军城巡检。',[('继远','被处斩者'),('继达','受任巡检者')],when='923年十二月李继韬被斩后；确日未列',place='上党',note='李继远单独遣使诛，不默认在天津桥同时死；巡检不等节度使。')
relationship('继韬','继远','兄长',74,'其弟继远曰：','复用已有明确方向关系；A李继韬是B李继远兄长。')
ev('jichou_retains_property','李继俦奉召入朝，却留取李继韬室家财物，迟不上路',74,'召权知','不时即路。',[('继俦','权知军州事、奉召未行者'),('继韬','被取室家财物的已故人')],when='923年十二月李继韬死后',place='上党',note='据室、料妓妾、搜货财为原文动作；不能捏造未名妇人的新婚关系。')
E=ev('jida_kills_jichou','李继达着衰服率百骑攻牙宅，杀李继俦',74,'继达怒曰','斩继俦。',[('继达','起事杀兄者'),('继俦','被杀者')],when='923年十二月甲申',place='上党牙宅',note='大兄表示李继俦年长；主书百骑，旧新史数百骑，不精确合成。')
claim('event',E,'description','新史记李继达引数百骑，遣人入杀李继俦。',74,'引數百騎坐戟門，使人入殺繼儔。','兵数主书百骑、别书数百骑；动作主书攻宅，别书使人入杀并列。',source='xinwudaishi-036-jida',relation='conflicts')
relationship('继俦','继达','兄长',74,'大兄曾无骨肉之情','称大兄与杀继俦上下文明确，A李继俦是B李继达兄长。')
E=ev('jike_city_people_counterattack','节度副使李继珂募市人千余，攻李继达所在子城',74,'节度副使','攻子城。',[('李继珂','募人攻城者'),('继达','受攻者')],when='923年十二月甲申李继俦被杀后',place='上党子城',note='市人千余与李继达百骑是不同人群，不相加当同支军队总数。')
claim('event',E,'description','旧史同记副使李继珂募市人千余反攻。',74,'副使李繼珂聞其亂也，募市人千餘攻於城門。','主书子城、旧史城门位置表述并列，无坐标。',source='jiuwudaishi-052-jida-death',relation='corroborates')
E=ev('jida_family_killed_suicide','李继达杀妻子后欲奔契丹，出城从骑散，遂自刭',74,'继达知',None,[('继达','杀家属后出城自杀者')],when='923年十二月甲申反攻后',place='上党城外',note='妻子指妻与子女，原文皆未名；将奔非已到契丹；数里是叙事约数不生成坐标。')
claim('event',E,'description','旧史亦记杀其孥、拟奔契丹，骑散后自刭路隅；旧史作不十里。',74,'行不十里，麾下奔潰，自剄於路隅。','主书数里、旧史不十里保持各自表述，未作精确里程。',source='jiuwudaishi-052-jida-death',relation='corroborates')
E=ev('luping_wu_mission','杨溥遣司农卿卢苹使唐，严可求预教应答',75,'甲申','皆如可求所料。',[('吴王','遣使者'),('卢蘋','司农卿使者'),('严可求','预教应对者'),('帝','问使者者')],when='923年十二月甲申遣使；到洛阳问答确日未另载',place='吴至唐洛阳',note='卢蘋简体展示卢苹，原文蘋保留别名；不将往返全定在甲申日。')
claim('event',E,'description','新史亦记灭梁年遣卢蘋，严可求密授数事，问对皆合。',75,'遣司農卿盧蘋使于唐，嚴可求密條數事授蘋以行。','吴顺义三年条对应923灭梁，独立出处；未改原文用名。',source='xinwudaishi-061-luping',relation='corroborates')
ev('luping_return_report','卢苹返吴，报告唐主游畋、吝财拒谏及内外怨情',75,'蘋还',None,[('蘋','返吴报告者'),('帝','使者评价对象')],when='923年此次使唐返回后；确日未列',place='吴',note='荒、啬、内外皆怨为使者报告观点，不能当民意统计或独立人格事实。')
ev('jixing_eunuch_demands','高季兴在洛阳被伶宦索货，感到愤怒',76,'高季兴','季兴忿之。',[('高季兴','受索货者')],when='923年入朝在洛阳期间',place='洛阳',note='无厌与忿是主书叙述；匿名伶宦不捏名，不默认每人实际受货。')
E=ev('jixing_released_chongtao','李存勖欲留高季兴，郭崇韬以示信诸侯劝阻，高得遣返',76,'帝欲留','乃遣之。',[('帝','拟留后遣返者'),('高季兴','获遣返者'),('郭崇韬','谏留者')],when='923年高季兴在洛阳时、丁酉至江陵前',place='洛阳',note='欲留与最终遣返分清，没有长期已拘留结论；劝言是郭的政治判断。')
claim('event',E,'description','新史亦记郭崇韬谏留，高季兴被厚礼遣返。',76,'莊宗乃止，厚禮而遣之。','新史对谏言同叙，但其入朝与唐入洛先后编排不同，不能当具体日次证据。',source='xinwudaishi-069-gao-departure',relation='corroborates')
ev('jixing_xuzhou_statement','高季兴倍道至许州，称来朝与放还皆为失策',76,'季兴倍道','纵我去一失。”',[('高季兴','返程陈说者')],when='923年十二月返程中；确日未载',place='许州',note='两失为高季兴说辞，不由编辑判为事实性错误。')
E=ev('jixing_xiangzhou_break_gate','高季兴途经襄州，孔勍留宴，高中夜斩关离去',76,'过襄州','斩关而去。',[('高季兴','斩关离去者'),('孔勍','节度使留宴者')],when='923年十二月丁酉到江陵前；确日未载',place='襄州',note='留宴、斩关不能推成孔勍已奉诏捕杀；新史另记密诏刘训图之，不把孔勍刘训合并。')
claim('event',E,'description','新史另称庄宗悔遣，密诏襄州刘训图之，高夜斩关后诏书才至。',76,'季興已去，莊宗心悔遣之，密詔襄州劉訓圖之。','另书补密诏图谋，主书孔勍留宴与新史刘训受令是不同记述，身份不互换；图之未等已杀。',source='xinwudaishi-069-gao-departure')
E=ev('jixing_jiangling_return','高季兴抵江陵，向梁震称此行几不免，批评唐主自矜游畋',76,'丁酉','吾无忧矣。”',[('高季兴','返江陵及批评唐主者'),('梁震','受高氏谈话者'),('帝','高氏评论对象')],when='923年十二月丁酉抵江陵；谈话此时',place='江陵',note='不能把主上自夸、何能久长等高氏转述判断写成当年后唐已崩溃；李存勖不是现场同行。')
claim('event',E,'description','新史亦记高氏归后向梁震称不听其言几不免，并批评主上自矜。',76,'季興歸而謂梁震曰：「不聽子言，幾不免。」','同一归后陈说补证；后来蜀物截留属于后年，不提前录入。',source='xinwudaishi-069-gao-departure',relation='corroborates')
ev('jixing_defence_preparation','高季兴缮城积粟、招纳梁旧兵，准备战守',76,'乃缮城',None,[('高季兴','备战者')],when='923年返江陵后；确日未载',place='江陵',note='准备防守不等已经起兵攻唐；未名梁旧兵不造全员名录。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续67—76段至卷年末；吴蜀先后为建议；京兆恢复日次书间不同；迁都出发抵达分录；军名恢复未沿用上段日次；法书录进为准请非完成交付；李继韬来朝月余与再诛分清，泣请其死原字保留、求哀语境有旧史补证；银数四十万/数十万、百骑/数百骑并列；无名二子、妻子不造姓名；将奔契丹未遂；卢蘋统一简体卢苹但引文原字不动；高返襄州孔勍留宴与新史刘训受密诏分开，不作别名；后年蜀物截留不提前录。'
for n in range(67,77):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(67,77)],next_paragraph='zztj-v273-y0924-p001',supplements=supplements,coverage='卷272第67—76段，原文件72—81行至卷末；实际赴洛、军名法书、李氏家族事件、吴使及高季兴返江陵。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(67,77)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
