# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 924, paragraphs 25–36."""
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
 *[(key,P/'sources/library'/key,'485f4ca3','司马光等') for key in ['tongjian-273-924-selection-shu-revolt','tongjian-273-924-shu-return']],
 *[(key,P/'sources/library'/key,'485f4ca3',author) for key,author in [
 ('jiuwudaishi-031-selection-jiji','薛居正等'),('jiuwudaishi-031-title-chu','薛居正等'),
 ('jiuwudaishi-031-huo-maozhen','薛居正等'),('jiuwudaishi-031-yangli-command','薛居正等'),
 ('jiuwudaishi-074-yangli-revolt','薛居正等'),('jiuwudaishi-094-tingyun-command','薛居正等'),
 ('xinwudaishi-028-selection-review','欧阳修'),('xinwudaishi-026-liyan-shu-date','欧阳修'),
 ('xinwudaishi-026-liyan-return','欧阳修'),('xinwudaishi-037-zhouza-rewards','欧阳修')]],
 ('xinwudaishi-026-liyan-identity',P/'sources/library/xinwudaishi-026-liyan-identity','c71f755c','欧阳修'),
 ('xinwudaishi-005-924-annals',YEAR/'part-01/sources/library/xinwudaishi-005-924-annals','fa5fd41a','欧阳修'),
 ('jiuwudaishi-132-maozhen-submission',YEAR/'part-01/sources/library/jiuwudaishi-132-maozhen-submission','fa5fd41a','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0924-p025-p036',
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
lines = (ROOT / 'resources/derived/tongjian/273.txt').read_text().splitlines()
for n in range(25, 37):
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
people, used, reused, supplements = {}, {}, {'xinwudaishi-005-924-annals','jiuwudaishi-132-maozhen-submission'}, []

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
        citation = f'卷273·同光二年（924）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_273_0924_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'李绍真':'霍彦威','李紹真':'霍彦威','汉主岩':'刘岩','楚王殷':'马殷','廷蕴':'张廷蕴','立':'杨立','匝':'周匝','俊':'陈俊','德源':'储德源','韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'张廷蕴':['張廷蘊'],'张弘祚':['張弘祚'],'杨立':['楊立'],'薛昭文':[],'周匝':[],'陈俊':['陳俊'],'储德源':['儲德源'],'李途':[],'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷273同光二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='924年本段；确日未载', note='', year=924, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_273_0924_' + code
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
        edge = 'participation_zztj_273_0924_' + code + '_' + pk
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
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_273_0924_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quotes preserve the contiguous source paragraph.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('selection_documents_background','追叙唐末以来贩卖告身、紊乱昭穆与选人冒滥现象',25,'自唐末','选人伪滥者众。',[],year=None,when='唐末以来持续背景，确年未载',place='唐梁之际选官',note='告赤疑告敕字，底本不改，依后文告身和新史告敕释为任官文书；舅叔拜甥侄是作者例说，无名对象不建假亲属。')
claim('event',E,'description','新史亦记吏部文书不完、私鬻告敕、乱易昭穆。',25,'而吏部銓文書不完，因緣以為姦利，至有私鬻告敕，亂易昭穆，','释主书疑字用独立出处；后续冬案人物不抢录。',source='xinwudaishi-028-selection-review',relation='corroborates')
E=ev('chongtao_selection_audit','郭崇韬请铨司考核，南郊行事官多被毁告身，主书记选人困顿',25,'郭崇韬欲','馁死逆旅。',[('崇韬','要求精加考核者')],when='924年三月本段；具体考核日未载',place='唐廷铨司、道路逆旅',note='千二百、数十、十之九为主书约数，不能以约数相减生成精确落选人数；号哭馁死为作者描述。')
claim('event',E,'description','旧史三月戊午诏南郊行事官付三铨磨勘，优与处分。',25,'戊午，詔應南郊行事官，並付三銓磨勘，優與處分。','补正式诏令日次，优与处分与主书大量涂毁是不同叙述，不由此取消冲突或造每人结局。',source='jiuwudaishi-031-selection-jiji')
E=ev('litu_inspects_tang_tombs','李途任长安按视唐诸陵使',25,'唐室诸陵','按视诸陵使。',[('李途','工部郎中、受任勘陵者'),('温韬','主书所记此前发陵者')],when='924年三月庚申任命；发陵为此前背景',place='长安及唐诸陵',note='任按视不是陵墓已修复；主书李途、新史李塗名字有异，规范暂沿主书不加确定异文别名。温韬不作本日同时再发陵。')
claim('event',E,'description','新史同庚申以李塗为检视诸陵使。',25,'庚申，工部郎中李塗為檢視諸陵使。','同日同职支持同事，途/塗字不同保留待考，不将二字当繁简对应。',source='xinwudaishi-005-924-annals',relation='conflicts')
E=ev('jiji_six_guard_admin','李继岌代张全义判六军诸卫事',25,'皇子',None,[('继岌','皇子、新任者'),('张全义','被替代该职者')],when='924年三月本段；旧史己未条',place='唐六军诸卫',note='代判一职不等张全义所有官职同时免除。')
claim('event',E,'description','旧史己未条同记李继岌代张全义判六军诸卫。',25,'以皇子繼岌代張全義判六軍諸衛事故也。','记幸军缘由，补任职，不把帝观军行为默认等李继岌已亲阅全部军。',source='jiuwudaishi-031-selection-jiji',relation='corroborates')
E=ev('emperor_receives_honorific','群臣上昭文睿武至德光孝皇帝尊号',26,'夏',None,[('帝','尊号受授者')],when='924年四月己巳朔',place='唐廷',note='实际受册与二月此前上表提出尊号分开，不新建另一皇帝人物。')
claim('event',E,'description','旧史同四月己巳朔在文明殿具衮冕受册尊号。',26,'夏四月己巳朔，帝御文明殿，具袞冕，受冊尊號曰昭文睿武至德光孝皇帝。','补殿所和仪服，名称逐字保留。',source='jiuwudaishi-031-title-chu',relation='corroborates')
E=ev('liyan_mission_shu','唐遣客省使李严使蜀，李严称唐帝威德及统一意向',27,'帝遣','诸侯曾无勤王之举。',[('帝','遣使君主'),('李严','客省使、使蜀者')],when='924年四月本段，出使确日未载；新史传记年异',place='唐廷至前蜀',note='已有李严为912莫州刺史降晋者，与新史原事刘守光后客省使对应；不混李继曮旧史另写李严。篡窃勤王等为使者政治话语。')
claim('person',people['李严'],'description','新史记李严原名让坤、幽州人，原事刘守光为刺史，后为庄宗客省使。',27,'李嚴，幽州人也，初名讓坤。事劉守光為刺史，後事莊宗為客省使。','与912莫州刺史李严降晋的既有主体沿接；不混李继曮旧书同写李严，原名作为出处事实保留。',source='xinwudaishi-026-liyan-identity')
claim('event',E,'time_original','新史李严传将使蜀记同光三年。',27,'同光三年，使于蜀，','主书924、新史传925日期不同，不能抹平或预造同事第二次出使；谈话中前年建号为其书叙法。',source='xinwudaishi-026-liyan-shu-date',relation='conflicts')
ev('zongchou_requests_liyan_execution','王宗俦以使者话侵蜀，请斩李严，王宗衍不从',27,'王宗俦','蜀主不从。',[('王宗俦','提议杀使者者'),('李严','被请求斩的使者'),('蜀主','拒绝杀使者者')],when='924年四月使蜀期间',place='前蜀',note='请斩而未准，不能造本批李严死亡。')
ev('guangbao_defence_proposal','宋光葆建议蜀选将练兵、边戍储粮修舰以备唐',27,'宣徽','以待之。”',[('宋光葆','宣徽北院使、建言者'),('蜀主','受建言君主')],when='924年四月本段',place='前蜀',note='凭陵之志为宋的判断，军舰粮饷是建议，不证明各工程已全部实施。')
ev('guangbao_wude_command','王宗衍以宋光葆为梓州观察使、武德节度留后',27,'蜀主乃',None,[('宋光葆','受任者'),('蜀主','任命者')],when='924年四月本段',place='梓州、武德军')
E=ev('ma_yin_shangshuling','马殷加兼尚书令',28,'乙亥',None,[('楚王殷','受加官者')],when='924年四月乙亥',place='唐廷、楚')
claim('event',E,'description','旧史同乙亥楚王马殷兼尚书令。',28,'乙亥，以天策上將軍、武安等軍節度使、守太師、中書令、楚王馬殷可依前守太師，兼尚書令。','同日加官印证，不把全职名号改成王殷。',source='jiuwudaishi-031-title-chu',relation='corroborates')
E=ev('huo_li_shaozhen_name','霍彦威获赐姓名李绍真',29,'庚辰',None,[('霍彦威','前保义留后、赐名对象')],when='924年四月庚辰',place='唐廷',note='复用霍彦威主体；赐李姓绍真不等从此所有史书只用新名。')
claim('event',E,'description','旧史同庚辰赐霍彦威姓、名绍真。',29,'庚辰，賜霍彥威姓，名曰紹真。','主书完整姓名与旧史省姓赐法对应，不分裂主体。',source='jiuwudaishi-031-huo-maozhen',relation='corroborates')
claim('person',people['霍彦威'],'aliases','李绍真为霍彦威此次赐姓名。',29,Q[29]['text'],'人物UUID延用，别名事实带本段日期。')
E=ev('maozhen_dies','秦忠敬王李茂贞去世',30,'秦忠敬','李茂贞卒，',[('岐王','亡故者')],when='924年四月本段；旧史癸巳条',place='凤翔',note='忠敬为谥号追称，不在去世前另造活着时同日授谥。')
claim('event',E,'description','旧史癸巳条记凤翔节度使秦王李茂贞薨。',30,'鳳翔節度使、秦王李茂貞薨。','源段癸巳马氏加官后承接，无自己换公历。',source='jiuwudaishi-031-huo-maozhen',relation='corroborates')
claim('person',people['李茂贞'],'death_year','旧史亦记同光二年夏四月薨，年六十九，谥忠敬。',30,'同光二年夏四月薨，年六十九。謚曰忠敬。','年龄为史载，不反推生年；已有人死亡字段不覆盖原档案，由事实引用补充。',source='jiuwudaishi-132-maozhen-submission',relation='corroborates')
ev('jiyan_fengxiang_acting','李继曮被奏为权知凤翔军府事',30,'遣奏',None,[('继\ue4be严','李茂贞之子、拟权知军府者')],when='924年四月父卒后本段',place='凤翔',note='遣奏是地方上报安排，与后日正式凤翔节度任命分开；主书缺字编码规范名复用首批李继曮。')
relationship('岐王','继\ue4be严','父亲',30,'其子继\ue4be严','复用既有父亲方向，李茂贞是李继曮父亲。')
ev('yangli_former_patron_background','追叙杨立曾受李继韬宠，李继韬诛后思乱',31,'初','常邑邑思乱。',[('杨立','安义牙将、旧宠者'),('继韬','已诛的旧庇护者')],when='李继韬死前及923末死后至924起事，追叙',year=None,place='安义军、潞州',note='思乱为主书解释，不把旧宠定同924，死后李继韬不作当前活着参与者。')
E=ev('luzhou_border_troops_order','安义兵三千被发戍涿州，杨立劝据城不赴边',31,'会发','不成为群盗耳。”',[('立','动员拒戍者')],when='924年四月潞州起事前',place='潞州至涿州为拟戍地',note='三千为主书发兵数，尚未说已抵涿州；朝廷不欲置潞是杨立猜测，不是已核实诏令动机。')
claim('event',E,'description','旧史杨立传记发潞兵三万人戍涿州。',31,'同光二年四月，有詔以潞兵三萬人戍涿州，','主书三千、旧传三万明显冲突，原字并列，未算入同一总数。',source='jiuwudaishi-074-yangli-revolt',relation='conflicts')
E=ev('yangli_attacks_city','杨立众攻潞州子城东门、焚掠市肆，李继珂张弘祚弃城',31,'因聚噪','弃城走，',[('立','起事攻城者'),('李继珂','节度副使、弃城者'),('张弘祚','主书监军、弃城者')],when='924年四月本段；旧史丙申据城叛',place='潞州子城东门、市肆',note='参与名单按主书，张弘祚与旧史张机祚为姓名异文，不能当确认繁简别名。')
claim('event',E,'description','旧史传作聚徒百余攻东门，副使李继珂与监军张机祚出奔。',31,'副使李繼珂及監軍張機祚出奔。','同事监军弘/机字异，暂沿主书同一角色并附异说，不新建张机祚实体。',source='jiuwudaishi-074-yangli-revolt',relation='conflicts')
ev('yangli_requests_command','杨立自称留后，遣人表求旌节',31,'立自称','表求旌节。',[('立','自称留后、表求者')],when='924年四月据城后',place='潞州至唐廷',note='自称和请求都不是朝廷已经授节度使。')
E=ev('siyuan_xingqin_tingyun_revolt_command','唐以李嗣源招讨、元行钦部署、张廷蕴马步指挥讨杨立',31,'诏以',None,[('嗣源','招讨使'),('李绍荣','武宁节度使、部署'),('张廷蕴','帐前都指挥使、马步都指挥使'),('立','讨伐对象')],when='924年四月起事后；旧史丙申条',place='唐廷至潞州',note='李绍荣复用元行钦；授令不等此刻已平乱。旧本纪副将不同，须分别见证据。')
claim('event',E,'description','旧史本纪丙申记李嗣源招讨、陕州李绍真为副。',31,'丙申，潞州小校楊立據城叛，以李嗣源為招討使，陝州留後李紹真為副，率師以討之。','主书元行钦部署、旧本纪霍彦威李绍真副职不同，不能用赐名归一抹掉不同人。',source='jiuwudaishi-031-yangli-command',relation='conflicts')
claim('event',E,'description','旧史张廷蕴传记明宗招讨、元行钦都部署、廷蕴前锋。',31,'詔遣明宗為招討使，元行欽為都部署，廷蘊為前鋒。','该传与主书部署对应，明宗是后称李嗣源；此处仅补任命，破城后事留下一批。',source='jiuwudaishi-094-tingyun-command',relation='corroborates')
ev('qian_forced_loans_silk','孔谦贷民钱，令以低估丝价偿还，屡檄州县催督',32,'孔谦','屡檄州县督之。',[('谦','贷钱征丝者')],when='924年四月本段，屡行确日未载',place='唐州县',note='低估与催督为主书叙述，无具体本金利率，不造现代百分比。')
ev('luzhi_protests_finance','卢质奏称春霜蚕丝薄，批评称贷重敛，请帝明命，帝不答',32,'翰林',None,[('质','翰林承旨、权知汴州、上言者'),('谦','被批征贷者'),('赵岩','奏文所举已故梁财政人物'),('帝','未回应者')],when='924年四月本段，确日未载',place='汴州、唐廷',note='赵岩复生是修辞非复活；霜害桑、恐流移、政策比较为卢奏内容，不变成另书独立事实；不报与明确驳诏区分。')
ev('han_attacks_min_defeated','刘岩领兵侵闽屯汀漳境，遭闽人反击败走',33,'汉主',None,[('汉主岩','南汉君主、入侵败退者')],when='924年四月本段，确日未载',place='汀、漳边界',note='原文未名闽方将帅，不能自动加王审知现场参与或建立两王单挑关系。')
ev('zhouza_huliu_capture','追叙伶人周匝在胡柳之役被梁军俘获',34,'初','帝每思之；',[('匝','伶人、被俘者'),('帝','被记思念者')],when='胡柳之役追叙，本段未给确年',year=None,place='胡柳',note='此前战役背景，不把胡柳俘虏定924新发生；不把帝思之按年计次数。')
E=ev('zhouza_returns_requests_reward','梁亡入汴时周匝见帝，称陈俊储德源保其生，求二州报之获许',34,'入汴','帝许之。',[('匝','回见与求报者'),('帝','见周及许任者'),('俊','教坊使、被称救护者'),('德源','内园栽接使、被称救护者')],when='923年唐入汴当日追叙',year=923,place='汴州',note='入汴依已完成923灭梁主线衔接，救护出自周自述；当日许诺不等已授刺史。')
claim('event',E,'description','新史亦记周匝入汴见帝、求陈俊储德源二州。',34,'願乞二州以報此兩人。','周的自述仍归人物话语；非另一独立记录救护细节。',source='xinwudaishi-037-zhouza-rewards',relation='corroborates')
ev('chongtao_delays_actors_posts','郭崇韬谏先赏伶人为刺史恐失天下心，使原任命未行',34,'郭崇韬谏','以是不行。',[('崇韬','劝止者'),('帝','所谏君主'),('俊','原许任者'),('德源','原许任者')],when='923年唐入汴后此追叙',year=923,place='唐廷',note='封赏未及一人与恐失天下为郭谏说辞，不作所有将领未受任何赏的统计。')
ev('emperor_insists_actor_promise','伶人再请，李存勖要求郭崇韬兑现周匝许诺',34,'逾年','屈意行之。”',[('帝','要求践诺者'),('崇韬','受要求者'),('匝','原许诺受益人')],when='923入汴后至924五月任职前，原文逾年',year=None,place='唐廷',note='逾年与主线不足整年存在叙事粒度疑点，保留原字不推925；再三请求未名不捏造某次日。')
E=ev('chenjun_jingzhou_governor','陈俊任景州刺史',34,'五月','德源为宪州刺史。',[('俊','新任景州刺史')],when='924年五月壬寅',place='景州',note='旧职教坊使与新刺史是身份变更，不把景州误为荆州。')
claim('event',E,'description','新史亦记卒以陈俊为景州刺史。',34,'卒以俊為景州刺史、德源為憲州刺史。','传未给确日，用主书壬寅；不误称新史日期同证。',source='xinwudaishi-037-zhouza-rewards',relation='corroborates')
E=ev('chudeyuan_xianzhou_governor','储德源任宪州刺史，主书记未获刺史的亲军愤叹',34,'五月',None,[('德源','新任宪州刺史')],when='924年五月壬寅',place='宪州及唐亲军',note='亲军百战愤叹为主书概述，不编具体未获任官人姓名。')
claim('event',E,'description','新史亦记储德源获宪州刺史。',34,'卒以俊為景州刺史、德源為憲州刺史。','官任同事，不把早许诺当成早已履职。',source='xinwudaishi-037-zhouza-rewards',relation='corroborates')
E=ev('xue_zhaowen_policy_petition','薛昭文疏陈征讨、赏军、收抚梁兵、宽赋、省役和护田，帝皆不从',35,'乙巳',None,[('薛昭文','右谏议大夫、上疏者'),('帝','不从建议者')],when='924年五月乙巳',place='唐廷',note='诸道僭窃、兵贫、恐受诱是薛疏说法，六项建议未执行，不造改革已落实。')
for start,end,value in [
 ('诸道僭窃者','未可遽息。','薛昭文建议继续考虑征讨。'),
 ('士卒久从征伐','更加颁赉。','薛昭文建议用四方贡献、南郊羡余增赏士卒。'),
 ('河南诸军','宜加收抚。','薛昭文担心梁旧军受厚利诱，建议收抚。'),
 ('户口流亡者','以安集之。','薛昭文建议宽徭薄赋以安集流民。'),
 ('土木不急','宜加裁省。','薛昭文建议裁省不急土木役。'),
 ('又请择隙地','民田。','薛昭文建议另择空地牧马，免践京畿民田。')]:claim('event',E,'description',value,35,span(35,start,end),'明确为疏中建议，不把未从写为实际实施。')
ev('liyan_dispatched_back','王宗衍遣李严返回唐',36,'戊申','李严还。',[('蜀主','遣还者'),('李严','被遣返使者')],when='924年五月戊申遣还',place='前蜀至唐',note='遣还日不同抵唐复命日，未一日跨越旅程。')
E=ev('liyan_trade_mission_background','追叙李存勖令李严以马换宫中珍玩，蜀禁珍奇外输，仅放粗物称入草物',36,'初，帝','入草物”。',[('帝','命以马换珍玩者'),('李严','受命换货使者')],when='此次使蜀前后背景，出使年份主书924与新史传925有异',year=None,place='唐与前蜀贸易',note='主书禁与低质类称入草物按史书叙述，不外推全部商品对外贸易政策；唐和中国均语境称谓，不套现代国界。')
claim('event',E,'description','新史同记遣李严携名马换珍奇、蜀禁奇货出剑门；补所得金二百两及地衣毛布。',36,'惟得金二百兩、地衣、毛布之類。','其他物品主书未给，新史独立补证；使蜀年异保留，不造二百两为主书同证。',source='xinwudaishi-026-liyan-return')
ev('emperor_angered_by_trade_term','李严返报入草物称谓，李存勖怒言王衍或将成为入草之人',36,'严还，以闻','入草之人乎！”',[('李严','返报者'),('帝','闻报怒言者'),('蜀主','被帝指称者')],when='924年五月遣还之后，复命确日未載',place='唐廷',note='君主怒言，不代表王宗衍此时已被俘或已屈辱献俘。')
E=ev('liyan_shu_vulnerable_report','李严评蜀主及近臣政事，称大兵一至可瓦解，李存勖认同',36,'严因',None,[('李严','评蜀及劝可攻者'),('帝','认同者'),('蜀主','被评价者'),('王宗弼','被评价近臣'),('宋光嗣','被评价近臣')],when='924年五月复命后本段，确日未載',place='唐廷',note='童騃奢淫、大兵即崩为使者评价及军事预测，不当前已征服蜀；被评蜀臣不在唐现场。')
claim('event',E,'description','新史李严传把换货、怒言与决议伐蜀连写。',36,'於是決議伐蜀。','作为该书因果叙法单列，主书本句只记认同，不凭这句提前记录925实际征蜀。',source='xinwudaishi-026-liyan-return')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续25—36段；告赤疑字释告敕、新史补证；约数未精算；李途/李塗字异保留未加确定别名；上尊号与受册衔接旧史；使蜀李严对应912莫州降晋者，不混李继曮，主书924/新史传925并列；霍赐李绍真同主体；李茂贞卒与李继曮权知、后授节度分开；潞兵三千/三万、张弘祚/张机祚、讨副元行钦/霍彦威各书并列，不强归别名；任讨未平；卢奏借赵岩复生为比喻；汉侵闽不加无名将帅；周匝胡柳旧事、923入汴许诺与924授刺史分开，逾年粒度疑点保留；薛疏六项未施行；遣还与抵唐分开、换物怒言及使者品评不等当前蜀亡。'
for n in range(25,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=924,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(25,37)],next_paragraph=Q[37]['id'],supplements=supplements,coverage='卷273第25—36段，原文件30—41行；选官、陵察、尊号、使蜀、楚赐官、霍赐名、岐王卒、潞乱、财政与五月奏议。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(25,37)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
