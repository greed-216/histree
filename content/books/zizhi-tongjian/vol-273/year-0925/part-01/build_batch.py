# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 924, paragraphs 1–12."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 38))
specs = [
 ('tongjian-273-924-year-end',YEAR.parent/'year-0924/part-06/sources/library/tongjian-273-924-year-end','f4a1df9b','司马光等'),
 *[(key,P/'sources/library'/key,'7c2351be','司马光等') for key in ['tongjian-273-925-command','tongjian-273-925-return']],
 *[(key,P/'sources/library'/key,'7c2351be',author) for key,author in [
 ('jiuwudaishi-032-february','薛居正等'),('jiuwudaishi-032-return','薛居正等'),('xinwudaishi-028-altar','欧阳修'),('xinwudaishi-028-armour','欧阳修'),('xinwudaishi-065-heci','欧阳修'),('xinwudaishi-007-congke-post','欧阳修'),('xinwudaishi-007-congke-adoption','欧阳修'),('xinwudaishi-005-925-annals','欧阳修')]],
 ('jiuwudaishi-032-cunxian-report',YEAR.parent/'year-0924/part-06/sources/library/jiuwudaishi-032-cunxian-report','f4a1df9b','薛居正等'),
 ('jiutangshu-020-ai-identity',P/'sources/library/jiutangshu-020-ai-identity','ca812387','刘昫等'),
 ('xintangshu-010-zhaozong-identity',P/'sources/library/xintangshu-010-zhaozong-identity','ca812387','欧阳修、宋祁等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0925-p001-p012',
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
for n in range(1, 13):
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
people, used, reused, supplements = {}, {}, {'tongjian-273-924-year-end','jiuwudaishi-032-cunxian-report'}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷273·同光三年（925）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_273_0925_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'苻习':'符习','少帝':'李祚','昭宗':'李杰','从珂':'李从珂','词':'何词','朱全忠':'朱温','令德':'朱令德','令锡':'李令锡','全义':'张全义','后':'刘夫人（李存勖妻）','格':'张格','温':'徐温','虔':'翟虔','宗俦':'王宗俦','宗弼':'王宗弼','承班':'王承班','光嗣':'宋光嗣','承休':'王承休','重霸':'安重霸','循':'孔循','赵殷衡':'孔循','刘后':'刘夫人（李存勖妻）','李绍真':'霍彦威','李紹真':'霍彦威','汉主岩':'刘岩','楚王殷':'马殷','廷蕴':'张廷蕴','立':'杨立','匝':'周匝','俊':'陈俊','德源':'储德源','韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'何词':['何詞'],'王允平':[],'李令锡':['李令錫'],'翟虔':[],'欧阳彬':['歐陽彬'],'关宏业':['關宏業'],'刘潜':['劉潛'],'王承骞':['王承騫'],'王鲁柔':['王魯柔'],'徐延琼':['徐延瓊'],'王宗锷':['王宗鍔'],'李彦稠':['李彥稠'],'何泽':['何澤'],'景润澄':['景潤澄'],'王承班':[],'王承休':[],'安重霸':[],'曹义金':['曹義金'],'许寂':['許寂'],'娄继英':['婁繼英'],'张廷蕴':['張廷蘊'],'张弘祚':['張弘祚'],'杨立':['楊立'],'薛昭文':[],'周匝':[],'陈俊':['陳俊'],'储德源':['儲德源'],'李途':[],'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷273同光三年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='925年本段；确日未载', note='', year=925, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_273_0925_' + code
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
        edge = 'participation_zztj_273_0925_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_273_0925_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quotes preserve the contiguous source paragraph.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
ev('shu_new_year_amnesty','前蜀正月初一大赦',1,'春',None,[('蜀主','大赦君主')],when='925年正月甲午朔',place='前蜀',note='赦令范围未详，不自动赦全部刑罪。')
E=ev('tang_reburial_order_halted','李存勖命改葬唐昭宗及少帝，因用度不足停止',2,'丙申',None,[('帝','下令君主'),('昭宗','拟改葬已故唐帝'),('少帝','拟改葬已故唐帝')],when='925年正月丙申命令，停止确日未载',place='唐皇陵',note='少帝复用李祚（后名李柷），命与止同事，不作两帝当年在世；停止不等已经完成改葬。')
claim('person',people['李祚'],'description','旧唐书记哀帝名柷、早封辉王名祚，与既有李祚主体合一。',2,'哀皇帝諱柷，昭宗第九子，母曰積善太后何氏。','卷二十下本纪开篇对应名祚，少帝引用依新五代史本纪少帝济阴王注；沿已有人物，不新建李柷。',source='jiutangshu-020-ai-identity')
claim('person',people['李杰'],'description','新唐书记昭宗讳晔，复用既有唐昭宗李杰主体。',2,'昭宗聖穆景文孝皇帝諱曄，懿宗第七子也。','已有李杰主体别名唐昭宗；本证补名晔对应，后改名不另建人物。',source='xintangshu-010-zhaozong-identity')
claim('event',E,'description','旧史同丙申记山陵未备、别选园陵改葬，旋因年饥财匮而止。',2,'丙申，詔以昭宗、少帝山陵未備，宜令有司別選園陵改葬，尋以年饑財匱而止。','补未备缘由与止，六月新史改卜另后续阶段留待按序读。',source='jiuwudaishi-032-cunxian-report',relation='corroborates')
E=ev('khitan_youzhou_january','契丹寇幽州',3,'契丹',None,[],when='925年正月本段，确日未载',place='幽州',note='未名将帅与战果，不与924各次告警合并成一次。')
claim('event',E,'description','旧史同正月段记契丹寇幽州。',3,'契丹寇幽州。','同地同月印证，未提供兵数。',source='jiuwudaishi-032-cunxian-report',relation='corroborates')
E=ev('emperor_dep_luoyang','李存勖离洛阳巡兴唐',4,'庚子','帝发洛阳；',[('帝','离京君主')],when='925年正月庚子',place='洛阳至兴唐')
claim('event',E,'description','旧史同庚子车驾发京幸邺。',4,'庚子，車駕發京師幸鄴。','目的地旧史邺与当时兴唐同城语境，不将兴唐误到唐州。',source='jiuwudaishi-032-cunxian-report',relation='corroborates')
E=ev('emperor_arr_xingtang','李存勖到兴唐',4,'庚戌',None,[('帝','到达君主')],when='925年正月庚戌',place='兴唐')
claim('event',E,'description','旧史同庚戌记车驾至邺。',4,'庚戌，車駕至鄴。','到达和出发分别录，不倒推具体行军速度。',source='jiuwudaishi-032-cunxian-report',relation='corroborates')
E=ev('fuxi_repair_suanzao_order','符习奉诏治理酸枣遥堤以御决河',5,'诏',None,[('苻习','平卢节度使、受命修堤者')],when='925年正月庚戌到兴唐后本段，诏确日未载',place='酸枣遥堤',note='苻习与既有符习为本段字异，同职对应旧史符习；仅受命不是已完成堤。')
claim('event',E,'description','旧史庚戌后记青州节度使符习修酸枣河堤，补此前梁决河东注郓濮以限唐军。',5,'命青州節度使符習修酸棗河堤。','职地同平卢；遥堤与河堤为各书用语并列，旧决背景不另造925梁君在世。',source='jiuwudaishi-032-cunxian-report',relation='corroborates')
E=ev('siyuan_armour_request','追叙李嗣源北征过兴唐向张宪取细铠五百领，张宪未奏而给',6,'初','奏而给之；',[('嗣源','请求军铠者'),('宪','副留守、给铠者')],year=None,when='北征途经兴唐、925正月皇帝责问以前，确日未载',place='兴唐东京库',note='衔接924末命北征背景，初不强定本年正月取铠日；五百为史載领数。')
claim('event',E,'description','新史亦记明宗北伐取魏库细铠五百，张宪不闻而给。',6,'初，明宗北伐契丹，取魏鎧仗以給軍，有細鎧五百，憲遂給之而不以聞。','明宗后称指李嗣源，不把魏地当他朝人；数量印证不证明两书完全独立。',source='xinwudaishi-028-armour',relation='corroborates')
E=ev('xian_armour_penalty','李存勖怒张宪擅给军铠，罚俸一月并令自去军中取回',6,'帝怒','令自往军中取之。',[('帝','责罚君主'),('宪','受罚者'),('嗣源','所涉给铠军将')],when='925年正月到兴唐后责问，确日未载',place='兴唐至北征军中',note='帝疑问何意仅话语，不作张宪谋叛事实；令取回未主书已取回结果。')
claim('event',E,'description','新史记庄宗责张宪自取，左右谏乃止。',6,'莊宗至魏，大怒，責憲馳自取之，左右諫之乃止。','补谏止结果，主书只令取回；未将新史未述罚俸当否定主书一月。',source='xinwudaishi-028-armour')
E=ev('xian_alternative_ball_ground','李存勖欲为王都入朝辟球场，张宪请留即位坛改辟宫西',6,'帝以','于宫西。”',[('帝','欲辟球场君主'),('王都','将入朝、拟陪球者'),('宪','请留壇改场者')],when='925年正月巡兴唐时计划，确日未载',place='兴唐即位坛、行宫西',note='欲辟和王都将入朝是此句计划，不定两人已经在新球场对击。')
claim('event',E,'description','新史同记张宪以即位坛不可毁，另治宫西球场。',6,'乃別治宮西為鞠場，場未成，','同替代工程印证，场未成非完工。',source='xinwudaishi-028-altar',relation='corroborates')
E=ev('altar_demolition_order','宫西球场数日未成，李存勖命两虞候毁即位坛，张宪郭崇韬劝谏未止',6,'数日','立命两虞候毁之。',[('帝','命毁壇者'),('宪','谏及向郭言者'),('崇韬','从容转谏者')],when='925年正月巡兴唐本段，确日未载',place='兴唐即位坛',note='两虞候未名不造实体；主书两次命令同事不算两坛。')
claim('event',E,'description','新史亦記庄宗命两虞候亟毁坛为场。',6,'莊宗怒，命兩虞候亟毀壇以為場。','同命令印证，不推整工程当天完工。',source='xinwudaishi-028-altar',relation='corroborates')
claim('event',E,'description','新史本纪正月记毁即位坛为鞠场、二月己巳聚鞠新场。',6,'三年春正月庚子，如東京，毀即位壇為鞠場。二月己巳，聚鞠于新場。','毁坛条承正月记次不强定庚子出发日同日已毁；二月聚鞠为后续使用补证，不重复新增节点。',source='xinwudaishi-005-925-annals',relation='corroborates')
ev('xian_altar_omen_assessment','张宪私向郭崇韬评价毁即位坛为忘天背本不祥',6,'宪私',None,[('宪','私评者'),('崇韬','听者')],when='925年正月毁坛命后本段',place='兴唐',note='不祥是张宪评价，不作超自然灾祸证据。')
E=ev('dejun_lulong_appointment','赵德钧由横海任卢龙节度使',7,'二月',None,[('李绍斌','受任者')],when='925年二月甲戌',place='卢龙军、幽州',note='李绍斌复用赵德钧，此任独立于前期东北招讨。')
claim('event',E,'description','旧史同甲戌任李绍斌由沧州改幽州节度使。',7,'甲戌，以滄州節度使李紹斌為幽州節度使，依前檢校太保；','沧州横海、幽州卢龙是军州称谓对应，不建重名人物。',source='jiuwudaishi-032-february',relation='corroborates')
E=ev('siyuan_zhuozhou_victory_report','李嗣源奏败契丹于涿州',8,'丙子',None,[('嗣源','胜报军将')],when='925年二月丙子奏报，战斗具体日未载',place='涿州',note='上奏日不当然等战斗日，不加未名契丹将。')
claim('event',E,'description','旧史同丙子记涿州东南杀败契丹、生擒首领三十。',8,'丙子，李嗣源奏，涿州東南殺敗契丹，生擒首領三十人。','补方位与被擒三十首领，未名不建人，不用数字推总战损。',source='jiuwudaishi-032-february',relation='corroborates')
ev('siyuan_zhending_plan','李存勖与郭崇韬议徙李嗣源镇真定以援赵德钧',9,'上以','崇韬深以为便。',[('帝','议调者'),('崇韬','同议赞同者'),('嗣源','拟调将'),('李绍斌','拟获声援幽州将')],when='925年二月本段，确日未载',place='唐廷、真定幽州拟部署',note='宿将殆尽与李绍斌位望轻为史书判断，谋议不是已到镇。')
E=ev('chongtao_declines_bian_command','郭崇韬辞兼汴州，陈权位已重与不至治所之弊，帝再许其辞',9,'时崇韬','上乃许之。',[('崇韬','辞兼镇者'),('帝','原欲移镇而准辞者')],when='925年二月本段议任期间',place='唐廷、汴州拟任地',note='自称无汗马劳与帝称大功为各方发言，不录成互相覆盖客观功勋；未赴治所不等汴州无人治。')
claim('event',E,'description','旧史亦记郭崇韬懇辞兼领汴州。',9,'移郭崇韜兼領汴州。召崇韜議之，崇韜奏以為當，因懇辭兼領。','同兼镇辞拒，未将拟任写为已任节度。',source='jiuwudaishi-032-february',relation='corroborates')
E=ev('siyuan_chengde_appointment','李嗣源移成德节度使',9,'庚辰','为成德节度使。',[('嗣源','由宣武受移者')],when='925年二月庚辰',place='成德军、真定')
claim('event',E,'description','旧史同庚辰宣武李嗣源为镇州节度使。',9,'庚辰，以宣武軍節度使李嗣源為鎮州節度使。','军州对应补证，不另建镇州任职第二事件。',source='jiuwudaishi-032-february',relation='corroborates')
ev('heci_han_mission','刘岩因唐灭梁惧，遣宫苑使何词贡唐并觇强弱',9,'汉主闻','且觇中国强弱。',[('汉主岩','南汉遣使君主'),('何词','宫苑使、贡探者')],year=None,when='923梁亡之后、925二月抵魏之前，遣使确年日未载',place='南汉至唐',note='起因与目的为主书记；中国为史书唐辖境称谓，不套现代国界。')
E=ev('heci_arrives_wei','何词抵魏奉南汉书',9,'甲申','词至魏。',[('词','到达贡使')],when='925年二月甲申',place='魏、兴唐')
claim('event',E,'description','旧史同甲申段记刘岩使者奉书，称大汉国王致大唐皇帝。',9,'廣南劉岩遣使奉書於帝，稱「大漢國王致書上大唐皇帝」。','旧史未名何词，本段使者主书相合；名称国王与新史国主字异保留。',source='jiuwudaishi-032-february',relation='corroborates')
claim('event',E,'time_original','新史南汉世家将何词入询中国虚实编乾亨七年。',9,'七年，唐莊宗入汴，龑懼，遣宮苑使何詞入詢中國虛實，稱大漢國主致書大唐皇帝。','乾亨七年对应923建年起算语境，主书925到魏；可能遣与到差、世家叙次差，并列不强判同日同年。',source='xinwudaishi-065-heci',relation='conflicts')
ev('heci_returns_han_assessment','何词返报李存勖骄淫无政不足畏，刘岩大悦并不复通唐',9,'及还','自是不复通中国。',[('词','回报使者'),('汉主岩','听报决定君主'),('帝','被评价君主')],when='925年二月到魏之后，返报确日未载',place='南汉',note='骄淫无政是何词回报，非独立现代评价；不复通为叙述范围，不外推永远绝一切贸易。')
ev('emperor_distrusts_generals_background','主书追叙李存勖入洛后信伶宦而疏忌宿将',9,'帝性','颇疏忌宿将。',[('帝','被述疏忌君主')],year=None,when='923入洛以后至本段的背景',place='唐廷',note='刚好胜及信谗为主书解释，未名每位宦者不自动加景进行为。')
E=ev('siyuan_congke_post_petition','李嗣源请李从珂任北京内牙马步指挥以便家',9,'李嗣源家','以便其家，',[('嗣源','请官军将'),('从珂','卫州刺史、拟授对象')],when='925年三月丁酉',place='北京太原、唐廷',note='奏请不是已批准；北京指太原不是今北京。')
claim('person',people['李从珂'],'description','新史记李嗣源掠得魏氏，养其子阿三为子、名从珂。',9,'魏氏有子阿三，已十餘歲，明宗養以為子，名曰從珂。','明确养子关系，不把主书其子误为亲生；早年确年未载，不把收养日期定925。',source='xinwudaishi-007-congke-adoption')
relationship('嗣源','从珂','继父',9,'魏氏有子阿三，已十餘歲，明宗養以為子，名曰從珂。','沿已有继父关系稳定key，补养为子证；不建重复父亲或另一养父边；发生为早年背景非925当年收养。',source='xinwudaishi-007-congke-adoption')
E=ev('congke_demoted_shimen','李存勖怒李嗣源为子奏官，降李从珂突骑指挥戍石门',9,'帝怒','戍石门镇。',[('帝','怒拒及降官君主'),('嗣源','所责奏请者'),('从珂','降官、率数百戍镇者')],when='925年三月丁酉奏请后，处分确日未载',place='石门镇',note='数百为主書約数，不给兵数精值；否奏与降官后果分明。')
claim('event',E,'time_original','新史记同光二年李从珂为卫州刺史突骑指挥、戍石门。',9,'同光二年，為衞州刺史突騎指揮使，戍于石門。','主书同光三年925，新史二年924不同记次并列，不另建924重复降职事件。',source='xinwudaishi-007-congke-post',relation='conflicts')
ev('siyuan_petition_fear_resolved','李嗣源忧恐上章申理，久之才解',9,'嗣源忧恐','久之方解。',[('嗣源','上章申理者')],when='925年三月降从珂后至久之，确日未载',place='李嗣源任所至唐廷',note='方解未给具体复职赦令，不直接认李从珂升回原职。')
ev('siyuan_denied_audience','李嗣源请至东京朝觐被拒',9,'辛丑','不许。',[('嗣源','乞朝者'),('帝','不许者')],when='925年三月辛丑',place='东京兴唐拟朝地',note='乞而不许，不写实际进宫会面。')
ev('chongtao_siyuan_private_suspicion','郭崇韬私评李嗣源非久居人下、皇子不及',9,'郭崇韬以','皆不及也。”',[('崇韬','私评者'),('嗣源','被评将领')],when='925年三月本段，确日未载',place='唐廷',note='不是李嗣源本人宣叛；帝子未名不造逐个竞位关系。')
ev('chongtao_siyuan_disarm_kill_rejected','郭崇韬劝召李嗣源宿卫夺兵权又劝除之，帝不从',9,'密劝',None,[('崇韬','建议者'),('帝','拒建议君主'),('嗣源','建议所针对将领')],when='925年三月本段，确日未载',place='唐廷',note='拒绝建议，不能生成嗣源已被杀或罢兵权。')
E=ev('emperor_returns_battlefields','李存勖离兴唐渡德胜，历杨村戚城观旧战场示群臣',10,'己酉',None,[('帝','巡旧战地君主')],when='925年三月己酉发兴唐，途行确日未载',place='德胜、杨村、戚城',note='旧战场回顾不是本年再打那些战役，未绘无据路线。')
claim('event',E,'description','旧史同己酉发邺，辛亥到德胜登城观旧址，至杨村沿河到戚城饮乐。',10,'己酉，車駕發鄴宮。辛亥，至德勝城。','补途中确日不把己酉出发定辛亥；旧城等即主线地。',source='jiuwudaishi-032-return',relation='corroborates')
ev('palace_ghost_pretext','宦官欲增嫔御诈称夜见鬼，借宫空应采女子，李存勖原欲符咒攘之',11,'洛阳宫殿','故鬼物游之耳。”',[('帝','受诈言及欲攘君主')],when='925年三月返洛前后追述，具体日未载',place='洛阳宫',note='鬼见为主书明确诈言，咸通乾符万人是宦者声称，不作真实人口统计，无名者不造人物。')
E=ev('women_selection_palace','王允平景进奉命广采民女充宫，主书记不啻三千、不问来历',11,'上乃命','不问所从来。',[('帝','命采君主'),('王允平','宦者、采择者'),('进','伶人、采择者')],when='925年三月返洛前后本段，确日未载',place='太原、幽州、镇州至洛阳后庭',note='不啻三千为下限叙数，不造一人一个节点；未名民女不补后妃名单。')
claim('event',E,'description','旧史同记王允平景进采宫人，不择良家委巷，殆千余。',11,'時宮苑使王允平、伶人景進為帝廣采宮人，不擇良家委巷，殆千餘人，','主书不啻三千、旧史殆千余不同数字并列，不求平均，不认必是完全同批次人数。',source='jiuwudaishi-032-return',relation='conflicts')
ev('women_ox_carts','李存勖从兴唐返洛时民女被牛车载行，连绵满路',11,'上还','累累盈路。',[('帝','返行君主')],when='925年三月兴唐返洛途中',place='兴唐至洛阳',note='牛车载宫人是前句承接，未给总车辆数。')
E=ev('xian_missing_women_report','张宪奏营妇女逃失千余疑军挟匿，主书指皆入宫',11,'张宪奏',None,[('宪','奏报者')],when='925年三月返洛本段，确日未载',place='东京兴唐营及洛阳宫',note='军挟匿是张宪疑虑，不当定案；皆入宫为作者纠正，叙事层次分别保留。')
claim('event',E,'description','旧史记营家口一千二百逃亡，奏称因艰食。',11,'東京副留守張憲奏，諸營家口一千二百人逃亡，以艱食故也。','主书妇女千余疑军挟、旧史家口1200因艰食对象缘由不同，并列不归同一个精确人数。',source='jiuwudaishi-032-return',relation='conflicts')
E=ev('emperor_arr_luoyang','李存勖返回洛阳',12,'庚辰','帝至洛阳；',[('帝','归京君主')],when='925年三月庚辰',place='洛阳')
claim('event',E,'time_original','旧史亦记庚辰至自邺。',12,'庚辰，車駕至自鄴。','同返回日印证。',source='jiuwudaishi-032-return',relation='corroborates')
claim('event',E,'time_original','新史本纪记三月庚申至自东京。',12,'庚申，至自東京。','主书旧史庚辰与新史庚申日次不同，保留待纸本。',source='xinwudaishi-005-925-annals',relation='conflicts')
E=ev('capital_names_restored','唐恢复洛阳东都、兴唐府改邺都',12,'辛酉',None,[('帝','颁诏君主')],when='925年三月辛酉',place='洛阳、兴唐府',note='京都称谓变更，不认两城地理迁移；邺字展示简体，引用原鄴字。')
claim('event',E,'description','旧史同辛酉洛京东都、魏州邺都，并记与北都并为次府。',12,'宜依舊以洛京為東都，魏州改為鄴都，與北都並為次府。','补府级语，东京在此诏前指兴唐，诏后洛阳东都，不能一律当现代东京。',source='jiuwudaishi-032-return',relation='corroborates')
claim('event',E,'description','新史亦记辛酉改东京为邺都、洛京东都。',12,'辛酉，改東京為鄴都，以洛京為東都。','同日称谓印证。',source='xinwudaishi-005-925-annals',relation='corroborates')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续1—12段；改葬命后止非完成；符习苻字异同职旧书对照；初军铠五百不强定925取日，令取与新史谏止分开；即位坛毁命与二月新场球事分层，张宪不祥是评价；赵德钧赐名李绍斌同主体；胜报与战日区别，旧史补擒三十；兼镇拟议、辞与实授分开；何词遣年未知925到魏，新史七年世家叙次保留；从珂既有继父关系与新史养为子不混亲生，戍石门主925新924并列；忧恐申理解不推复职；郭私评劝除帝不从不造嗣源叛或已死；鬼物为诈言，采女主不啻三千旧殆千余、营妇千余旧家口1200不同统计并列；归洛主旧庚辰新庚申，京都改名同辛酉，东京北京按当时城别。'
for n in range(1,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=925,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,13)],next_paragraph=Q[13]['id'],supplements=supplements,coverage='卷273第1—12段，原文件84—95行；925年正月至三月，改葬、巡兴唐、修堤、给铠毁坛、北面任职胜报、南汉使者、从珂戍石门、归洛采女及京都改名。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,13)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
