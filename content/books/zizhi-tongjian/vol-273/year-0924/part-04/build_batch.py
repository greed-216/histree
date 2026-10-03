# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 924, paragraphs 37–48."""
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
 ('tongjian-273-924-shu-return',YEAR/'part-03/sources/library/tongjian-273-924-shu-return','485f4ca3','司马光等'),
 *[(key,P/'sources/library'/key,'4ab203a5',author) for key,author in [
 ('jiuwudaishi-032-defence-north','薛居正等'),('jiuwudaishi-032-may','薛居正等'),('jiuwudaishi-032-june','薛居正等'),('jiuwudaishi-032-july','薛居正等'),('xinwudaishi-025-cunshen-final','欧阳修')]],
 ('jiuwudaishi-094-tingyun-command',YEAR/'part-03/sources/library/jiuwudaishi-094-tingyun-command','485f4ca3','薛居正等'),
 ('xinwudaishi-005-924-annals',YEAR/'part-01/sources/library/xinwudaishi-005-924-annals','fa5fd41a','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0924-p037-p048',
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
for n in range(37, 49):
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
people, used, reused, supplements = {}, {}, {'tongjian-273-924-shu-return','xinwudaishi-005-924-annals','jiuwudaishi-094-tingyun-command'}, []

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
    ck = f'claim_zztj_273_0924_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'刘后':'刘夫人（李存勖妻）','李绍真':'霍彦威','李紹真':'霍彦威','汉主岩':'刘岩','楚王殷':'马殷','廷蕴':'张廷蕴','立':'杨立','匝':'周匝','俊':'陈俊','德源':'储德源','韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'曹义金':['曹義金'],'许寂':['許寂'],'娄继英':['婁繼英'],'张廷蕴':['張廷蘊'],'张弘祚':['張弘祚'],'杨立':['楊立'],'薛昭文':[],'周匝':[],'陈俊':['陳俊'],'储德源':['儲德源'],'李途':[],'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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
E=ev('demolish_defence_order','李存勖因潞州叛乱禁止州镇修城浚隍并毁防城设施',37,'帝以',None,[('帝','下诏者')],when='924年五月庚戌',place='唐各州镇',note='记诏令，不证明各地已经全部拆除；与后文夷潞州城分开。')
claim('event',E,'time_original','旧史记同项拆防城、禁修浚池隍诏令为五月己酉。',37,'己酉，詔天下收拆防城之具，不得修浚池隍。','主书庚戌、旧史己酉日次不同，保留异说。',source='jiuwudaishi-032-defence-north',relation='conflicts')
E=ev('cunshen_dies','符存审任新宣武节度使后卒于幽州',38,'壬子','卒于幽州。',[('李存审','兼中书令、蕃汉马步总管、亡故者')],when='924年五月壬子',place='幽州',note='李存审为已有符存审赐名；新授宣武但卒于幽州，不能改死亡地点为汴州。')
claim('event',E,'description','旧史丙寅条记幽州上报新授宣武节度使李存审卒。',38,'幽州上言，新授宣武軍節度使李存審卒。','丙寅是记上报的本纪段，不据此覆盖主书壬子卒日。',source='jiuwudaishi-032-may',relation='corroborates')
claim('event',E,'description','新史传记亦记徙宣武、卒于幽州。',38,'徙存審宣武軍節度使，卒于幽州。','官任及死亡地印证，传未载壬子确日。',source='xinwudaishi-025-cunshen-final',relation='corroborates')
E=ev('cunshen_arrows_admonition','追叙符存审向诸子讲述起家艰难并授所出箭镞命收藏',38,'存审出于',None,[('存审','教诫诸子者')],when='符存审生前常戒诸子，确日未载',year=None,place='符存审家庭',note='四十年、百余均史载约数，未反推起家确年；诸子未名，不由群体另造人物。')
claim('event',E,'description','新史将示百余箭镞教子故事记于临终。',38,'臨終，戒其子曰：','主书常戒、新史临终叙事定位不同；同故事不计两次独立确证，不凭传末子名强建全体本次在场。',source='xinwudaishi-025-cunshen-final',relation='conflicts')
claim('event',E,'description','新史记展示平生中矢箭镞百余并劝子努力。',38,'因出其平生身所中矢鏃百餘而示之曰：「爾其勉哉！」','对应示镞主题，引用原字；数目为史载，不作医学统计。',source='xinwudaishi-025-cunshen-final',relation='corroborates')
E=ev('dejun_northeast_command','幽州报契丹将入寇，赵德钧任东北招讨率大军渡河北上',39,'幽州言','渡河而北。',[('李绍斌','横海节度使、招讨使')],when='924年五月甲寅',place='幽州、黄河以北',note='李绍斌复用赵德钧；渡河北上不等已经解除围城。')
claim('event',E,'description','旧史同甲寅任李绍斌招讨，并补段凝为副、李绍宏为都监。',39,'以兗州節度李紹欽為副招討使，以宣徽使李紹宏為招討都監，','补证角色分别属于段凝、李绍宏；不混李绍真霍彦威。',source='jiuwudaishi-032-defence-north')
for name,role,quote in [('段凝','副招讨使','以兗州節度李紹欽為副招討使'),('李绍宏','招讨都监','以宣徽使李紹宏為招討都監')]:
 pk=person(name,39,role,quote,source='jiuwudaishi-032-defence-north');ek='participation_zztj_273_0924_northeast_'+pk
 B['person_events'].append(dict(key=ek,person_key=pk,event_key=E,role=role,status='draft'))
 claim('person_event',ek,'role',name+'：'+role+'。',39,quote,'独立旧史补证，不冒充主书明示。',source='jiuwudaishi-032-defence-north')
E=ev('khitan_youzhou_supply_raids','契丹屯幽州东南城门外，骑兵掠夺馈运',39,'契丹屯',None,[],when='924年五月幽州告警本段',place='幽州东南城门外及馈运途径',note='未名将帅不自动建阿保机现场参与，馈运多失不变全军断粮。')
claim('event',E,'description','旧史亦记幽州上报契丹营于州东南。',39,'幽州上言，契丹營於州東南。','营地印证，旧史本句未说所有粮运被掠。',source='jiuwudaishi-032-may',relation='corroborates')
E=ev('jiyan_formal_fengxiang','李继曮正式任凤翔节度使',40,'壬戌',None,[('李继\ue4be严','受任者')],when='924年五月壬戌',place='凤翔',note='承接父卒后权知，正式授任不是四月已经授节度；缺字名依已核主体。')
claim('event',E,'description','旧史同壬戌以权知凤翔军府事李严充凤翔节度使。',40,'以權知鳳翔軍府事、涇州節度使李嚴為起復雲麾將軍、右金吾大將軍同正，依前檢校太尉、兼中書令，充鳳翔節度使。','此李严为岐王子李继曮，不是客省使李严；父卒权知上下文及同日职任相合。',source='jiuwudaishi-032-may',relation='corroborates')
E=ev('cao_tribute_background','瓜沙与吐蕃杂居，曹义金遣使间道入贡',41,'时瓜',None,[('曹义金','归义留后、贡使派遣者')],when='924年五月授节度之前，贡使确日未载',year=None,place='瓜州、沙州至唐廷',note='主书和旧史均作曹义金，沿本次来源建立主体；杂居不等单一民族国界，间道不绘无据路线。')
E=ev('cao_guiyi_command','曹义金由权知归义留后任归义节度使',41,'乙丑','为节度使。',[('曹义金','受任者')],when='924年五月乙丑',place='归义军、沙州')
claim('event',E,'description','旧史同乙丑授曹义金归义节度使、沙州刺史、检校司空。',41,'乙丑，以權知歸義軍留後曹義金為歸義軍節度使、沙州刺史、檢校司空。','补并授职，不从称谓异字另造曹义金实体。',source='jiuwudaishi-032-may',relation='corroborates')
E=ev('tingyun_luzhou_capture','张廷蕴率百余壮士夜登潞州城、斩关引诸军入城',42,'李嗣源大军','城已下矣，',[('张廷蕴','前锋登城破关者'),('嗣源','率大军、天明到者'),('李绍荣','天明到者')],when='924年五月奏平之前夜至天明，确日未载',place='潞州',note='百余为约数；不把后日丙寅上奏定为登城之夜；复用元行钦。')
claim('event',E,'description','旧史张廷蕴传亦记百余劲兵登城斩关，明宗与元行钦天明才到。',42,'明宗、行欽達明而始至，其城已下，明宗甚慊之。','明宗为李嗣源后称，不改发生时王朝；不悦是传记叙述，不推新叛乱。',source='jiuwudaishi-094-tingyun-command',relation='corroborates')
ev('siyuan_displeased_capture','李嗣源等见潞州已被张廷蕴攻下而不悦',42,'嗣源等','不悦。',[('嗣源','被记不悦者'),('李绍荣','等字承接到城诸将')],when='924年五月天明入潞城后',place='潞州',note='仅作者情绪记载，不外推争功处分。')
E=ev('luzhou_pacified_report','李嗣源上奏潞州平定',42,'丙寅','潞州平。',[('嗣源','奏报者')],when='924年五月丙寅',place='潞州至唐廷')
claim('event',E,'description','旧史同丙寅记李嗣源奏收复潞州。',42,'丙寅，李嗣源奏收復潞州。','奏报日与破城未载日分开。',source='jiuwudaishi-032-may',relation='corroborates')
claim('event',E,'description','新史本纪同五月丙寅记李嗣源克潞州。',42,'丙寅，李嗣源克潞州。','本纪克字与通鉴奏平粒度不同，不另造第二破城事件。',source='xinwudaishi-005-924-annals',relation='corroborates')
E=ev('yangli_executed','杨立及其党在镇国桥被磔杀',42,'六月','镇国桥。',[('立','被处死叛将')],when='924年六月丙子',place='镇国桥',note='已跨到六月，不能沿段首记五月；匿名党徒不造人数。')
claim('event',E,'description','旧史同丙子记李嗣源送杨立等到阙，并磔于市。',42,'丙子，李嗣源遣使部送潞州叛將楊立等到闕，並磔於市。','补送阙环节；主书镇国桥、旧史于市地点叙法不同，保留而不强同。',source='jiuwudaishi-032-june',relation='conflicts')
claim('event',E,'description','新史同六月丙子记杨立伏诛。',42,'六月丙子，楊立伏誅。','死亡日印证，未给镇国桥详细地点。',source='xinwudaishi-005-924-annals',relation='corroborates')
E=ev('luzhou_walls_level_order','李存勖命削平潞州高城深池',42,'潞州城池',None,[('帝','下令夷城者')],when='924年六月平叛后本段，确日未载',place='潞州',note='命令不等工程完工，和五月天下拆防城诏分别录。')
claim('event',E,'description','旧史亦记帝命铲平潞州城隍，并叙因诏诸方镇撤防城之备。',42,'潞州城峻而隍深，至是帝命剗平之，因詔諸方鎮撤防城之備焉。','旧史把普遍拆防诏附于六月此事后，主书五月已有诏，纪时顺序差别并列。',source='jiuwudaishi-032-june',relation='conflicts')
ev('xingqin_guide_suwei','元行钦由武宁改归德节度使、同平章事，留宿卫受厚宠',43,'丙戌','宠遇甚厚。',[('李绍荣','受任留宿卫者')],when='924年六月丙戌',place='归德军、唐宫宿卫',note='官任与留宿卫分别可见，不把任归德等实际长期到宋州驻镇。')
ev('emperor_family_visit_xingqin','李存勖有时与太后、皇后同至元行钦家',43,'帝或','同至其家。',[('帝','来访者'),('太后','同访者'),('刘后','同访者'),('李绍荣','受访者')],when='元行钦受宠期间有时，确日未载',year=None,place='元行钦家',note='时常性背景不全锁定丙戌一日；太后曹氏、刘后复用。')
ev('xingqin_gift_consort','元行钦丧妻后，刘后促李存勖将有子幸姬赐元行钦并令拜谢',43,'帝有幸姬','已肩舆出宫矣。',[('帝','微许赐姬君主'),('刘后','妒姬并促成者'),('李绍荣','丧妻、受赐者')],when='此次任官前后宫廷追叙，确日未载',year=None,place='唐宫',note='幸姬、子与亡妻皆未名，不拼接其他后妃姓名或新建无证亲属；丧妻非六月丙戌确定死亡。')
ev('emperor_grief_consort','幸姬出宫后李存勖托疾数日不食',43,'帝为之',None,[('帝','被记托疾不食者')],when='赐姬出宫后累日，确日未载',year=None,place='唐宫',note='累日无精确天数，托疾不作医学疾病诊断。')
ev('siyuan_xuanwu_general','李嗣源任宣武节度使，代符存审统蕃汉内外马步军',44,'壬辰',None,[('嗣源','天平节度使、受任总管'),('李存审','已故前任')],when='924年六月壬辰',place='宣武军、唐蕃汉诸军',note='前任已故身份不是共同履职。')
ev('xuji_shu_chancellor','许寂任前蜀中书侍郎、同平章事',45,'秋',None,[('许寂','礼部书所记原职、受任宰相')],when='924年七月壬寅',place='前蜀',note='礼部书疑缺尚字，保留源字并注明，不以繁简转换掩饰脱字。')
ev('qian_requests_rent_office','孔谦贬王正言并贿赂伶宦，求租庸使未获',46,'孔谦','意怏怏，',[('谦','求官者'),('正言','被贬短者'),('崇韬','听孔贬短者')],when='924年七月本段，确日未载',place='唐廷',note='作者所叙贿赂，不编金额与无名受赂人；求官未成。')
ev('qian_resignation_saved','孔谦表求解职惹帝怒拟法办，景进救免',46,'癸卯','得免。',[('谦','求解职及被拟处罚者'),('帝','拟置法者'),('进','救免者')],when='924年七月癸卯及随后，救免确日未载',place='唐廷',note='将置法后得免不等已经被执行死刑；得免并未载租庸使终于授予。')
ev('liang_river_break_background','梁决河造成曹濮连年水患',46,'梁所','曹、濮患，',[],when='梁时决河以来连年，确起讫未载',year=None,place='曹州、濮州',note='历史背景不重新给梁君本年在世参与。')
ev('lou_river_repair','娄继英受命督汴滑兵堵塞梁所决河，未几复坏',46,'甲辰',None,[('娄继英','右监门上将军、督塞者')],when='924年七月甲辰命督塞，复坏在随后未几',place='曹濮水患河段、汴滑兵',note='命令与不久坏均录，未给坏确日；不凭未几计算天数。')
E=ev('xinzhou_weisai','新州设置威塞军',47,'庚申',None,[],when='924年七月庚申',place='新州')
claim('event',E,'description','旧史同庚申升新州为威塞军节度，并辖妫、儒、武等州。',47,'升新州為威塞軍節度使，以媯、儒、武等州為屬郡。','行政辖州补证；并无具体经纬度或稳定疆界图。',source='jiuwudaishi-032-july',relation='corroborates')
ev('khitan_requests_youzhou','契丹遣使向李存勖求幽州安置卢文进',48,'契丹恃','卢文进。',[('帝','受请求唐君主'),('卢文进','拟安置对象')],when='924年七月本段，确日未载',place='唐廷、幽州为所求地',note='遣使求地不等唐已割让幽州，未名使者不造人，卢是对象不等亲自出使。')
E=ev('khitan_attacks_bohai_liaodong','阿保机为免攻唐时被渤海掎后，先攻渤海辽东',48,'时东北','渤海之辽东，',[('契丹主','拟攻唐而先攻辽东者')],when='924年七月本段，确日未载',place='渤海之辽东',note='东北役属与谋虑是主书叙述，不表示渤海924已灭；灭渤海后事不提前录。')
claim('event',E,'description','旧史七月段记幽州奏契丹安巴坚东攻渤海。',48,'幽州奏，契丹安巴堅東攻渤海。','安巴坚为已有阿保机字形对应，此处行动方向印证不推全部辽东已占。',source='jiuwudaishi-032-july',relation='corroborates')
ev('tunnei_luwenjin_yan_raids','契丹遣秃馁及卢文进据营平等州扰燕',48,'遣其将',None,[('秃馁','据州扰燕将领'),('卢文进','据州扰燕将领')],when='924年七月本段，确日未载',place='营州、平州及燕地',note='据州不画永久边界，卢文进与秃馁不因同征建立亲属盟友边。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续37—48段；主书五月庚戌拆防与旧史己酉日异，旧史六月夷城后又叙撤防令顺序异保留；符存审死亡与奏报日分开，生前常戒与新史临终示镞异叙；李绍斌复用赵德钧，旧史补段凝及李绍宏分职；李继曮正式授节度接前批权知，不混客省李严；曹义金按主书与旧史同名建立，未凭知识记忆改名；破城、奏平、六月磔杀分时，镇国桥与于市并列；幸姬与子不强定后妃，宫廷追叙年月不详；许寂礼部书疑脱字保留；孔谦求官未获、求解救免不造死刑；河患背景及复坏未几不补确日；契丹求幽未授，先攻渤海不等灭国。'
for n in range(37,49):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=924,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(37,49)],next_paragraph=Q[49]['id'],supplements=supplements,coverage='卷273第37—48段，原文件42—53行；撤防、符存审卒、幽州防务、凤翔归义任命、潞州平叛、宫廷与官任、治河及契丹。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(37,49)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
