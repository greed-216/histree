# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 56–66."""
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
 ('jiuwudaishi-030-office-reduction',P/'sources/library/jiuwudaishi-030-office-reduction','39562804','薛居正等'),
 ('jiuwudaishi-030-chancellors',P/'sources/library/jiuwudaishi-030-chancellors','39562804','薛居正等'),
 ('jiuwudaishi-058-zhao-door',P/'sources/library/jiuwudaishi-058-zhao-door','39562804','薛居正等'),
 ('jiuwudaishi-058-zhao-name',P/'sources/library/jiuwudaishi-058-zhao-name','39562804','薛居正等'),
 ('xinwudaishi-028-weis-hiring',P/'sources/library/xinwudaishi-028-weis-hiring','39562804','欧阳修'),
 ('jiuwudaishi-030-fan-governors',YEAR/'part-09/sources/library/jiuwudaishi-030-fan-governors','83be3260','薛居正等'),
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p056-p066',
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
for n in range(56, 67):
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
people, used, reused, supplements = {}, {}, {'tongjian-272-923-luoyang-move','jiuwudaishi-030-fan-governors','xinwudaishi-005-923-founding'}, []

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
    ck = f'claim_zztj_272_0923_10_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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
E=ev('youqian_li_jilin_name','朱友谦获赐李继麟姓名，李继岌奉命以兄礼事之',56,'己巳',None,[('硃友谦','赐姓名对象'),('继岌','奉命兄事者')],when='923年十一月己巳；旧史乙巳有异',place='唐廷',note='朱友谦李继麟复用主体；兄事是礼遇，不建李继岌与朱友谦血缘。')
claim('event',E,'time_original','《旧五代史》该事记乙巳。',56,'乙巳，賜友謙姓，改名繼麟，帝令皇子繼岌兄事之。','主书己巳与旧史乙巳不同，不能繁简归一或强换公历消除。',source='jiuwudaishi-030-fan-governors',relation='conflicts')
claim('person',people['朱友谦'],'aliases','朱友谦获赐姓名李继麟。',56,Q[56]['text'],'原key保留，不建李继麟新人物。')
E=ev('kang_zhengzhou_new_name','康延孝授郑州防御使，赐姓名李绍琛',57,'以康延孝',None,[('康延孝','授职赐名者')],when='923年十一月本段；确日主书未列',place='郑州',note='授职不等此刻已到镇；沿用康延孝主体。')
claim('event',E,'description','《旧五代史》同记郑州防御使，赐名继琛。',57,'以捧日都指揮使、博州刺史康延孝為鄭州防禦使、檢校太保，賜姓，名繼琛。','主书绍琛、旧史继琛并列，未擅定一方为讹或直接加确定别名。',source='jiuwudaishi-030-fan-governors',relation='conflicts')
claim('person',people['康延孝'],'aliases','主书康延孝获赐李绍琛姓名；旧史继琛有异。',57,Q[57]['text'],'姓名异文待考，不另建同事人物。')
E=ev('beidu_chengde_restored','北都名号撤销，复称成德军',58,'废北都',None,[],when='923年十一月本段；确日主书未列',place='原北都镇州、成德军',note='撤名号不是毁城或人口迁空；不混太原北都后称。')
claim('event',E,'description','《新五代史》十一月乙巳记复北都为镇州、太原为北都。',58,'十一月乙巳，復北都為鎮州，太原為北都。','书间行政表述粒度不同，镇州和成德军区别府州与军镇，不硬定此主书短句同时含全部改名。',source='xinwudaishi-005-923-founding')
ev('yuan_li_shaoan_name','袁象先获赐李绍安姓名',59,'赐宣武','李绍安。',[('袁象先','宣武节度使、赐名者')],when='923年十一月本段；确日未列',place='唐廷',note='同一人物，不建李绍安副本；原职称谓保留，后续军名另录。')
ev('wentao_shaochong_visit','温韬入朝获赐李绍冲姓名',59,'匡国节度使','李绍冲。',[('温韬','匡国节度使入朝者')],when='923年十一月本段；确日未列',place='唐廷',note='温昭图、温韬、李绍冲为同人前后称名。')
ev('wentao_bribes_returns','主书记温韬贿刘夫人等，旬日遣还镇',59,'绍冲多赍','复遣还镇。',[('绍冲','被记行赂后还镇者'),('魏国夫人刘氏','被记受货的李存勖妻')],when='923年来朝后旬日',place='唐廷至匡国军',note='金帛未具数量，刘夫人非李克用妻；贿与恩宠为主书叙述，不给匿名权贵捏名。')
ev('chongtao_opposes_wentao','郭崇韬以盗唐陵反对温韬还镇，李存勖称已赦而遣之',59,'郭崇韬曰',None,[('郭崇韬','反对者'),('温韬','批评与遣还对象'),('上','坚持原赦者'),('朱温','被用作罪责比较的已故人')],when='923年十一月温韬遣还前',place='唐廷',note='其罪相埒为郭陈说，不将比较人物朱温作现场参与者；发陵旧事不新定923每陵事件。')
E=ev('office_reduction_25_months','中书请减官，留任满二十五月后依次替补，李存勖接受',60,'戊申',None,[('帝','接受减官方案者')],when='923年十一月戊申',place='唐廷三省寺监、枢密院',note='二十五月是未来轮换条件，不造已于本日满期或全部官一律罢。人颇咨怨为作者概述。')
claim('event',E,'description','《旧五代史》补寺监员额和太常大理例外，轮候二十五个月。',60,'候見任官滿二十五個月，並據資品，卻與除官。','据资品轮候，未把所有停官实际复职日算为925年某日。',source='jiuwudaishi-030-office-reduction')
claim('event',E,'description','旧史请太常大理另置丞，常侍等减半。',60,'唯太常寺事關大禮，大理寺事關刑法，除太常博士外，許更置丞一員，','补方案分项，未把主书量留误作全部寺监机构被废。',source='jiuwudaishi-030-office-reduction')
ev('liang_suburban_ritual_aborted','追叙朱友贞闻杨刘陷，停止洛阳南郊仪式，仪物尚存',61,'初，梁均王','其仪物具在。',[('梁主','拟祀而止的朱友贞')],when='923年或此前追叙；此段未给原仪物准备确日',year=None,place='洛阳',note='原称梁均王与已故末帝同人；已逝不再作当前亲自行动，欲祀非已礼成。')
ev('quanyi_proposes_luoyang_ritual','张全义请李存勖速至洛阳谒庙后南郊，获接受',61,'张全义请',None,[('张全义','请行礼者'),('上','接受者')],when='923年十一月本段',place='洛阳为拟赴地',note='提议获准不是本日已到或已郊礼。')
E=ev('bianzhou_xuanwu_restored','开封府改回汴州宣武军',62,'丙辰','宣下军汴州。',[],when='923年十一月丙辰',place='开封府、汴州',note='主书宣下军疑字，展示宣武由新史同日明确，快照仍原字。')
claim('event',E,'description','《新五代史》同丙辰记汴州复宣武军。',62,'丙辰，復汴州為宣武軍。','作为规范展示宣武军依据，疑字说明不静默替换底本。',source='xinwudaishi-005-923-founding',relation='corroborates')
ev('songzhou_guide_name','宋州原梁宣武军改名归德军',62,'梁以宋州',None,[],when='923年十一月丙辰',place='宋州',note='区别汴州宣武军恢复与宋州归德改名，不将二州合一。')
ev('officials_ordered_luoyang','文武官奉诏先赴洛阳',63,'诏文武官',None,[('帝','下诏者')],when='923年十一月丙辰后本段；确日未列',place='唐廷至洛阳',note='先赴是诏令，不保证每个官员当日已抵。')
ev('chancellor_candidates_debate','主书记薛廷珪李琪被荐，郭崇韬不取并推赵光胤，豆卢革荐韦说',64,'议者以','谙练朝章。',[('郭崇韬','被议并提出人选者'),('薛廷珪','被荐未用者'),('李琪','被荐未用者'),('赵光胤','主书被推人选'),('豆卢革','荐韦说者'),('韦说','被荐者')],when='923年十一月丁巳任相前',place='唐廷',note='浮华倾险、廉洁方正等分别是郭评与书中论述，非独立人格认证；无名推荐者不造姓名。')
E=ev('zhao_wei_chancellors','赵光胤与韦说任同平章事',64,'丁巳','并同平章事。',[('光胤','主书任中书侍郎同平章事者'),('说','礼部侍郎同平章事者')],when='923年十一月丁巳',place='唐廷',note='赵光胤主书名保留；旧史赵光允且有光裔编校，不作简单繁简等同或加入确定别名。')
claim('event',E,'description','《旧五代史》同日载赵光允中书侍郎平章事、韦说同平章事。',64,'丁巳，以銀青光祿大夫、尚書左丞趙光允為中書侍郎、平章事、集賢殿大學士；','日期官职对应，但名字不同为身份异文，未另造赵光允同事件人物。',source='jiuwudaishi-030-chancellors',relation='conflicts')
claim('event',E,'description','《旧五代史》赵氏传编校称为相者光允，并辨原本光裔。',64,'為後唐相者，光允也。原本作光裔，係誤。','属该底本编校注而非正文原句，提示存在赵氏诸子身份异说；不替换主书光胤或宣称已纸本校定。',source='jiuwudaishi-058-zhao-name',relation='conflicts')
claim('person',people['赵光胤'],'description','本条赵光胤的任相记载与旧史赵光允、光裔校注有异，身份用名待考。',64,'同光元年十一月，光允與韋說並拜平章事。','主体暂按通鉴名组织，旧史仅附异说，不把赵光允加入已核实别名。',source='jiuwudaishi-058-zhao-name',relation='conflicts')
claim('event',E,'description','《新五代史》记豆卢革荐韦说以佐己。',64,'革以說能知前朝事，故引以佐己，','另书对知前朝事的评价及荐任，只补过程，不当纸本异名问题已解决。',source='xinwudaishi-028-weis-hiring')
relationship('光逢','光胤','兄长',64,'光胤，光逢之弟；','按主书明确长幼，A赵光逢是B赵光胤兄长；旧史此处光允名异待考。')
relationship('岫','说','父亲',64,'说，岫之子；','韦说之父韦岫，不补无名中间亲属。')
relationship('逢','廷珪','父亲',64,'廷珪，逢之子也。','薛廷珪父薛逢，规范同姓由主书承接，不混赵光逢。')
ev('chancellors_chronicle_characterisation','主书评赵光胤轻率自矜、韦说谨重守常',64,'光胤性轻率',None,[('光胤','作者评价对象'),('说','作者评价对象')],when='本段人物总结，确年未定',year=None,place='唐廷',note='作者评价独立呈现，不把前荐相评价与后来批评混成矛盾的客观测量。')
E=ev('zhao_guangfeng_door_notice','赵光逢闭门避政，弟谈政后署门请不言中书事',65,'赵光逢',None,[('赵光逢','闭门署告者'),('光胤','主书访兄谈政者')],when='同光任相后追叙，确日未载；梁罢相为此前背景',year=None,place='赵光逢私第',note='时往是习惯，不把每次访问都定923同日；主书光胤旧史光允异名并列。')
claim('event',E,'description','《旧五代史》同记署户，请不言中书事，来访弟记光允。',65,'同光初，弟光允為平章事，時謁問於私第，嘗語及政事，他日，光逢署其戶曰「請不言中書事」，','同故事人物用名有异，未直接把两名合成已核别名；后文女冠金等无对应主段事迹不抢录。',source='jiuwudaishi-058-zhao-door',relation='conflicts')
ev('kongqian_recommends_zhangxian','孔谦荐张宪镇东京，郭崇韬奏宪任东京副留守知事',66,'租庸副使','知留守事。',[('孔谦','荐张宪者'),('张宪','受奏任职者'),('郭崇韬','奏任者')],when='923年十一月戊午前本段',place='唐廷、东京',note='畏公正欲专务是主书动机解释，非独立核实心理；建议与奏任保留，未造诬陷定罪事件。')
E=ev('doulu_ge_finance_assignment','豆卢革判租庸兼盐铁转运，主书记孔谦失望',66,'戊午',None,[('豆卢革','新财政兼任者'),('谦','主书失望描写对象')],when='923年十一月戊午',place='唐廷诸道财政',note='兼职不等当日取消宰相本职；孔谦失望为主书记情绪。')
claim('event',E,'description','《旧五代史》同戊午记豆卢革判租庸兼盐铁转运。',66,'戊午，以中書侍郎、平章事豆盧革判租庸使，兼諸道鹽鐵、轉運等使。','同时原宰相职名保留。',source='jiuwudaishi-030-chancellors',relation='corroborates')
for row in B['people']:
 if row['key'] not in reused and row['name'] in ['韦岫','薛逢']:row['era']='唐'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续56—66段；己巳/乙巳赐名日异，康延孝绍琛/继琛异文并列；兄事非血缘；宣下疑字以新史宣武补证；减官25月为未来条件非已满期；梁南郊旧事年null；赵光胤/旧史光允与光裔编校属身份异说，不确定加别名；韦岫薛逢父子方向与赵光逢兄长清楚；动机及品评归作者；迁都诏令与实际到达另录。'
for n in range(56,67):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(56,67)],next_paragraph=Q[67]['id'],supplements=supplements,coverage='卷272第56—66段，原文件61—71行；赐姓名、官署减员、迁都准备、任相和财政职务。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(56,67)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
