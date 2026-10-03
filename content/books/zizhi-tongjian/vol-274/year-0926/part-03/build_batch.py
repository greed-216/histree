# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 274, year 926, paragraphs 1–12."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 44))
PREV=YEAR/'part-02'
specs=[
 ('tongjian-274-926-palace-guard',PREV/'sources/library/tongjian-274-926-palace-guard','0291ff48','司马光等'),
 ('tongjian-274-926-yedu-mutiny',P/'sources/library/tongjian-274-926-yedu-mutiny','8ecc7ee3','司马光等'),
 ('tongjian-274-926-capture-and-monitors',P/'sources/library/tongjian-274-926-capture-and-monitors','8ecc7ee3','司马光等'),
 ('jiuwudaishi-034-926-siyuan-command',P/'sources/library/jiuwudaishi-034-926-siyuan-command','8ecc7ee3','薛居正等'),
 ('jiuwudaishi-034-926-march',P/'sources/library/jiuwudaishi-034-926-march','8ecc7ee3','薛居正等'),
 ('jiuwudaishi-035-926-mutiny',P/'sources/library/jiuwudaishi-035-926-mutiny','8ecc7ee3','薛居正等'),
 ('jiuwudaishi-074-926-kang-capture',P/'sources/library/jiuwudaishi-074-926-kang-capture','8ecc7ee3','薛居正等'),
 ('xinwudaishi-046-926-huoyanwei',P/'sources/library/xinwudaishi-046-926-huoyanwei','8ecc7ee3','欧阳修'),
 ('xinwudaishi-045-926-quanyi',P/'sources/library/xinwudaishi-045-926-quanyi','8ecc7ee3','欧阳修'),
 ('jiuwudaishi-037-926-qingzhou',P/'sources/library/jiuwudaishi-037-926-qingzhou','8ecc7ee3','薛居正等'),
 ('jiuwudaishi-064-926-kongqing',P/'sources/library/jiuwudaishi-064-926-kongqing','8ecc7ee3','薛居正等'),
 ('jiuwudaishi-074-926-kang-rebellion',PREV/'sources/library/jiuwudaishi-074-926-kang-rebellion','0291ff48','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0926-p025-p036',
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
lines = (ROOT / 'resources/derived/tongjian/274.txt').read_text().splitlines()
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷274·同光四年（926）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_274_0926_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'王廷翰':'王延翰'}.get(name,name)
    name = {'李延安':'李廷安'}.get(name,name)
    name = {'王衍':'王宗衍','张\ue47f厉':'张砺','孙鐸':'孙铎','建徽':'朱建徽'}.get(name,name)
    name = {'从诲':'高从诲','贞简太后':'曹氏（李存勖母）','承肇':'王承肇','宗勋':'王宗勋','宗俨':'王宗俨','宗昱':'王宗昱','重霸':'安重霸','承休':'王承休','王承嶽':'王承岳','王承鑒':'王承鉴','程奉璉':'程奉琏','王承樸':'王承朴','景思':'唐景思'}.get(name,name)
    name = {'李令德':'朱令德','蜀太后':'徐贤妃','蜀太妃':'徐淑妃','王承休妻严氏':'严氏（王承休妻）','严氏':'严氏（王承休妻）','延翰':'王延翰','彦谦':'陈彦谦','审知':'王审知','苻习':'符习','少帝':'李祚','昭宗':'李杰','从珂':'李从珂','词':'何词','朱全忠':'朱温','令德':'朱令德','令锡':'李令锡','全义':'张全义','后':'刘夫人（李存勖妻）','格':'张格','温':'徐温','虔':'翟虔','宗俦':'王宗俦','宗弼':'王宗弼','承班':'王承班','光嗣':'宋光嗣','承休':'王承休','重霸':'安重霸','循':'孔循','赵殷衡':'孔循','刘后':'刘夫人（李存勖妻）','李绍真':'霍彦威','李紹真':'霍彦威','汉主岩':'刘岩','楚王殷':'马殷','廷蕴':'张廷蕴','立':'杨立','匝':'周匝','俊':'陈俊','德源':'储德源','韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'李从袭':['李從襲'],'李廷安':[],'吕知柔':['呂知柔'],'陈乂':['陳乂'],'严氏（王承休妻）':['嚴氏（王承休妻）'],'诚惠':['誠惠'],'罗贯':['羅貫'],'王延翰':[],'何词':['何詞'],'王允平':[],'李令锡':['李令錫'],'翟虔':[],'欧阳彬':['歐陽彬'],'关宏业':['關宏業'],'刘潜':['劉潛'],'王承骞':['王承騫'],'王鲁柔':['王魯柔'],'徐延琼':['徐延瓊'],'王宗锷':['王宗鍔'],'李彦稠':['李彥稠'],'何泽':['何澤'],'景润澄':['景潤澄'],'王承班':[],'王承休':[],'安重霸':[],'曹义金':['曹義金'],'许寂':['許寂'],'娄继英':['婁繼英'],'张廷蕴':['張廷蘊'],'张弘祚':['張弘祚'],'杨立':['楊立'],'薛昭文':[],'周匝':[],'陈俊':['陳俊'],'储德源':['儲德源'],'李途':[],'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷274同光四年条所见人物：{name}。',
                   biography=None, status='draft')
    if name not in registry:
        row['aliases']={'李存美':[],'李存礼':['李存禮'],'李存乂':[],'李存确':['李存確'],'向延嗣':[],'马彦珪':['馬彥珪'],'沈瑫':[]}.get(name,row['aliases'])
    if name not in registry:
        row['aliases']={'李环':['李環'],'郭廷信':[],'李崧':[],'张砺':['張礪'],'郭廷说':['郭廷說'],'郭廷让':['郭廷讓'],'郭廷议':['郭廷議'],'张氏（朱友谦妻）':['張氏（朱友謙妻）'],'史武':[],'李仁罕':[],'潘仁嗣':[],'张业':['張業'],'武漳':[],'李廷厚':[],'杨仁晸':['楊仁晸'],'朱建徽':['硃建徽'],'皇甫晖':['皇甫暉'],'赵在礼':['趙在禮'],'孙铎':['孫鐸','孙鐸'],'赵进':['趙進']}.get(name,row['aliases'])
    if name not in registry:
        row['aliases']={'焦武':[],'柴重厚':[],'梁汉颙':['梁漢顒'],'赵太':['趙太'],'何建崇':[],'王温':['王溫'],'郭从谦':['郭從謙','郭门高','郭門高'],'杨重霸':['楊重霸']}.get(name,row['aliases'])
    if name not in registry:
        row['aliases']={'王景戡':[],'崔延琛':[],'张破败':['張破敗'],'李肇':[],'侯弘实':['侯弘實'],'张虔钊':['張虔釗'],'康福':[],'杨希望':['楊希望'],'王公俨':['王公儼'],'杨继源':['楊繼源'],'淳于晏':['淳於晏']}.get(name,row['aliases'])
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='926年本段；确日未载', note='', year=926, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_274_0926_' + code
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
        edge = 'participation_zztj_274_0926_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_274_0926_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quotes preserve the contiguous source paragraph.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('wangjingkan_cangzhou_liuhou','沧州军乱，王景戡讨平后自任留后，河朔州县相继告乱',25,'李绍荣讨','告乱者相继。',[('王景戡','小校、平乱自为留后者')],when='926年二月鄴都战事期间，确日未载',place='沧州、河朔',note='自任不等朝廷正式授任；元行钦讨赵无功与赵太未下为当时背景，不重复此前事件。')
E=ev('cunxu_considers_personal_yedu_campaign','李存勖欲亲征鄴都，宰相枢密使以京师根本劝止并荐李嗣源',25,'帝欲自征','皆曰：“他人无可者。”',[('帝','拟亲征、疑惜李嗣源者'),('嗣源','被推荐出征者')],when='926年二月朝廷议将时',place='洛阳',note='欲亲征及推荐不是本段已亲征；帝心忌是主书作者叙述，吾惜是帝话，层次分别。')
E=ev('siyuan_ordered_yedu_campaign','张全义、李绍宏屡荐，李存勖命李嗣源率亲军讨鄴',25,'忠武节度使',None,[('全义','推荐者'),('绍宏','屡荐者'),('帝','命将者'),('嗣源','率亲军奉命出征者')],when='926年二月甲寅据主书',place='洛阳至鄴都',note='旧本纪甲辰、新本纪亦甲辰与主甲寅有日期异说，分别定位保留，不自行择成无差异。')
claim('event',E,'time_original','旧本纪将李嗣源赴鄴讨赵记为甲辰。',25,'甲辰，命蕃漢總管李嗣源統親軍赴鄴都，以討趙在禮。','主甲寅与旧甲辰不同，待纸本，不按叙次自动改干支。',source='jiuwudaishi-034-926-siyuan-command',relation='conflicts')
claim('event',E,'description','新张全义传也记群臣固请，最后全义力言使庄宗同意遣明宗。',25,'羣臣固請，不從；最後全義力以為言，莊宗乃從。','明宗是史家追称李嗣源，当前未即帝位。',source='xinwudaishi-045-926-quanyi',relation='corroborates')
E=ev('suiyin_troops_plunder_report','延州奏报绥、银军乱并掠州城',26,'延州言',None,[],when='926年二月本段，确日未载',place='绥州、银州及所掠州城',note='州城确指主书未明，不自动将两州各建被攻城或补造领兵人。')
claim('event',E,'description','旧本纪补报告人为延州知州白彦琛，并于甲辰日叙其奏。',26,'是日，延州知州白彥琛奏，綏、銀兵士剽州城謀叛。','报告日不等兵乱发生确日；白彦琛先保留补证文本，未凭同姓并崔延琛。',source='jiuwudaishi-034-926-siyuan-command',relation='adds')
E=ev('dongzhang_station_mianzhou','董璋率二万兵屯绵州，会合任圜讨康延孝',27,'董璋将兵','讨李绍琛。',[('董璋','会讨者'),('任圜','共同追讨统率者'),('李绍琛','追讨对象')],when='926年二月康返蜀后',place='绵州',note='二万为主书兵数，不与孟军统计合成独立精确总兵力。')
E=ev('cuiyanchen_promises_kang_then_warns_meng','崔延琛赴成都途中向康称召孟、缓兵可得蜀，到成都却劝孟备战',27,'帝遣中使','为战守备。',[('帝','派中使者'),('崔延琛','对康作承诺、对孟劝备者'),('李绍琛','听其声称者'),('孟知祥','被劝备战者')],when='926年二月康返蜀后',place='康军至成都',note='原书绍之曰有疑，展示只述其两处言语；奉诏召孟与缓兵得蜀是使者声称，不当真授康蜀或孟已被召回。')
E=ev('meng_fortifies_and_sends_troops','孟知祥浚壕立栅，遣李仁罕四万军及骁锐使李延厚二千讨康',27,'知祥浚壕','讨绍琛。',[('孟知祥','备城遣将者'),('李仁罕','马步都指挥使、讨康者')],when='926年二月备战时',place='成都至康军',note='李延厚原名留在事件，与第9段同职李廷厚是否同人未决，暂不另建或合并人物；四万与二千为派遣数，后选七百另阶段。')
E=ev('liyanhou_selects_seven_hundred','李延厚问军士勇怯愿行，选七百人出征',27,'延厚集其众','以行。',[],when='926年二月讨康出师前',place='蜀地',note='原职骁锐、原名李延厚待与李廷厚核身份，先作为事件文字可检索；分东、西是招募分类，不等有东西两军。')
claim('event',E,'description','旧康传夹注引九国志亦记李延厚率二千、选愿行者七百。',27,'得請行者七百人，逐延孝西寨，斬首百餘級，竟拔其城。','引文是旧史夹注转引，不另注册专门史；本批只用于选兵七百补证，后面的战绩不提前移入当前出师事件。',source='jiuwudaishi-074-926-kang-rebellion',relation='corroborates')
E=ev('zhangli_ambush_kang_hanzhou','张砺建议伏精兵，以董璋弱兵诱追，任圜在汉州败康，康退闭城',27,'是日，任圜军',None,[('任圜','采策统率者'),('李绍琛','迎战追弱兵、败退者'),('张砺','掌书记、伏击建议者'),('董璋','以东川兵诱退者')],when='926年二月汉州初战，旧康传记甲寅',place='汉州',note='主赢兵疑羸，展示弱兵而原字不改；斩数千为史载概数，不把战略归因当量化实验。初战与三月金雁桥败擒不同。')
claim('event',E,'time_original','旧康传记甲寅任圜到汉州，董璋懦卒诱追，伏击败康。',27,'甲寅，圜以大軍至漢州，延孝來逆戰，圜令董璋以東川懦卒當其鋒，伏精兵於其後，延孝擊退東川之兵，急追之，遇伏兵起，延孝敗，馳入漢州，閉壁不出。','主是日无确干支，旧甲寅为独立日期补证，不硬改主。',source='jiuwudaishi-074-926-kang-rebellion',relation='corroborates')
E=ev('huoyanwei_captures_and_executes_zhaotai','霍彦威奏克邢州擒赵太等，到鄴城西北营，徇示后杀赵太',28,'三月',None,[('李绍真','克城擒杀者'),('赵太','被擒徇杀者')],when='926年三月朔奏克，庚申至鄴徇杀；主朔原字丁已',place='邢州、鄴都西北',note='主刑州据前后同城校展示邢州，丁已疑丁巳保留原字；旧丁未朔、庚戌到鄴与主纪日不同并列。')
claim('event',E,'description','旧本纪记三月丁未朔克邢，赵太等二十一被徇并磔于军门。',28,'三月丁未朔，李紹真奏，收復邢州，擒賊首趙太等二十一人，徇於鄴都城下，皆磔於軍門。','二十一为旧补；主庚申徇杀与旧朔条包含徇磔的叙次有异，保留不把奏克日一律当杀日。',source='jiuwudaishi-034-926-march',relation='adds')
E=ev('wangyanhan_appointed_we i wu'.replace(' ',''),'王延翰由威武节度副使升节度使',29,'辛酉',None,[('王廷翰','受任者')],when='926年三月辛酉据主书',place='闽、威武军',note='主王廷翰据同职同任旧王延翰校匹配，不另造王廷翰；旧辛亥授福建节度与主辛酉有干支异文。')
claim('event',E,'description','旧本纪记辛亥威武副使王延翰为福建节度，列福建都指挥等职。',29,'辛亥，以威武軍節度副使、福建管內都指揮使、檢校太傅、守江州刺史王延翰為福建節度使，依前檢校太傅。','同职位序列校名字；辛酉/辛亥不同不自动修订主。',source='jiuwudaishi-034-926-march',relation='adds')
E=ev('siyuan_arrives_yedu_southwest','李嗣源到鄴都，营城西南',30,'壬戌','营于城西南；',[('嗣源','奉命到鄴驻营者')],when='926年三月壬戌据主书',place='鄴都西南',note='主第30段被阅读块拆开，首句从上一块引用，其余动作各用下一块，不拼源。旧本纪壬子另日期。')
claim('event',E,'time_original','旧本纪记壬子李嗣源领军至鄴，营西南。',30,'壬子，李嗣源領軍至鄴都，營於西南隅。','主壬戌与旧壬子不同，旧明纪另三月六日，均不自换公历。',source='jiuwudaishi-034-926-march',relation='conflicts')
E=ev('siyuan_orders_attack_next_morning','李嗣源命次晨攻鄴城',30,'甲子','诘旦攻城。',[('嗣源','下令者')],when='926年三月甲子据主书',place='鄴都营中',note='命次晨攻不等实际依命完成攻城，夜里兵乱另录。')
E=ev('zhangpobai_military_mutiny','张破败领从马直兵哗变，杀都将焚营，次晨逼中军，李嗣源拒战不敌',30,'是夜，从马直','乱兵益炽。',[('张破败','从马直兵、起乱者'),('嗣源','率亲军拒战者')],when='926年三月甲子夜至次晨据主书',place='鄴都城外营地',note='都将未名不虚构；这里李嗣源先拒乱兵，未将其本来奉命征讨等同预谋哗变。')
claim('event',E,'description','旧明宗纪记三月八日夜张破败号令诸军杀将焚营、五鼓逼营，亲军伤者近半。',30,'八日夜，軍亂。從馬直軍士有張破敗者，號令諸軍，各殺都將，縱火焚營，歡噪雷動。','旧军乱日用其原月日，别强与主干支同；伤近半仅旧叙述，不精算伤数。',source='jiuwudaishi-035-926-mutiny',relation='corroborates')
E=ev('mutineers_demand_siyuan_rule_hebei','乱兵称畏被坑杀，要求合城内军击退诸道、庄宗帝河南与李嗣源帝河北，李泣谕不从',30,'嗣源叱而问','嗣源泣谕之，不从。',[('嗣源','询问、泣谕者')],when='926年鄴外营兵乱次晨',place='鄴都城外',note='坑军与初无叛心为乱兵自陈，不能当真实清洗诏或独立动机证成；帝河北是要求，李未在此即位。')
E=ev('siyuan_huoyanwei_forced_into_yedu','李嗣源欲返京，乱兵持刃环迫，将其与霍彦威拥入鄴都',30,'嗣源曰：“尔不用','等入城，',[('嗣源','被持刃逼入者'),('李绍真','主书记同被拥入者')],when='926年鄴外营兵乱次晨',place='鄴都',note='主强迫入城与两史不同角度保留；不能据入城自动建与乱兵同谋关系。')
claim('event',E,'description','新霍传称霍彦威与安重诲劝李嗣源暂允，霍独未入城。',30,'彥威與安重誨勸明宗許之，乃擁兵入城，與在禮合，彥威獨不入。','与主嗣源及李绍真俱入、新霍独不入冲突；不把霍同时确在城内城外，出处分立待核。',source='xinwudaishi-046-926-huoyanwei',relation='conflicts')
E=ev('huangfuhui_kills_zhangpobai','鄴城不纳外兵，皇甫晖击杀张破败，外兵溃散',30,'城中不受外兵','外兵皆溃。',[('皇甫晖','逆击斩张者'),('张破败','被斩者')],when='926年乱兵拥李嗣源入鄴时',place='鄴都城门',note='两股乱兵有冲突，不能因一同参与哗变推为稳定同盟；旧明纪夹注转引主书不能当独立复证。')
E=ev('zhaozaili_greets_siyuan','赵在礼率诸校迎李嗣源并谢罪，称愿惟命是听',30,'赵在礼帅','惟命是听！”',[('赵在礼','迎拜谢罪者'),('嗣源','被迎者')],when='926年李嗣源入鄴后',place='鄴都',note='愿听是赵表态，不生成未知将校全体从属边。')
E=ev('siyuan_exits_yedu_to_weixian','李嗣源借收外散兵说服赵在礼放行，与霍彦威出城宿魏县',30,'嗣源诡说',None,[('嗣源','借口收兵出城者'),('赵在礼','准出城者'),('李绍真','主书记同出城者')],when='926年李嗣源入鄴后',place='鄴都至魏县',note='主诡说是史家定性；新霍传独不入、居二日李出与主同出不同，各存不硬统一住宿时长。')
claim('event',E,'description','新霍传记李嗣源居二日出城，得霍五千兵而之魏县。',30,'居二日，明宗復出，得彥威兵，乃之魏縣，謀欲還鎮州，彥威、重誨勸明宗以兵南向。','与主同宿魏县语句时间叙法有别，保留两日为新叙，不直接添加主当夜两日兼容解释。',source='xinwudaishi-046-926-huoyanwei',relation='adds')
E=ev('kang_defeated_captured_jinyan_bridge','任圜焚汉州栅，康延孝金雁桥战败，十余骑逃后被擒',31,'汉州无城堑','追擒之。',[('任圜','攻栅击败康者'),('李绍琛','败逃被擒者')],when='926年三月乙丑',place='汉州、金雁桥至绵竹据主书',note='主逃绵竹、旧逃绵州区别；本句擒后尚未诛，不先录其死。')
claim('event',E,'description','旧康传记乙丑康十数骑奔绵州，何建崇追擒，任圜命入槛车。',31,'以十數騎奔綿州；何建崇追及，擒之，任圜命載以檻車。','主绵竹与旧绵州为地点异说；旧补追擒将名，未覆盖主。',source='jiuwudaishi-074-926-kang-capture',relation='adds')
E=ev('meng_feasts_captured_kang','孟知祥至汉州犒军，与任圜董璋宴并引康槛车饮酒，康称畏郭案不敢还朝',31,'孟知祥自至','不敢归朝耳。”',[('孟知祥','犒军宴会及问康者'),('任圜','宴会者'),('董璋','宴会者'),('李绍琛','囚车中饮酒陈述者')],when='926年三月康被擒后',place='汉州',note='郭无罪、畏及己为康的自述，非这里独立审判结论；不把酒宴当已经释放康。')
claim('event',E,'description','旧康传同载孟手酌饮康、康以郭案解释不敢归朝。',31,'以此思慮，不敢歸朝，天道相違，一旦至此，亦其命也，夫復何言！','康说天道命运属其归因，未录为客观因果事实。',source='jiuwudaishi-074-926-kang-capture',relation='corroborates')
E=ev('jiji_marches_east_after_kang_capture','李继岌获康后率军倍道东归',31,'魏王继岌','倍道而东。',[('继岌','东归者')],when='926年三月康被擒后',place='蜀至东归路',note='获为统率责任，不与任圜战场擒人另作第二次康被擒；倍道不换现代速度。')
E=ev('meng_appoints_lizhao_houhongshi','孟知祥获得李肇、侯弘实，任李肇为牙内马步都指挥使、侯为副',31,'孟知祥获陕虢','弘实副之。',[('孟知祥','收用任命者'),('李肇','陕虢都指挥使、汝阴人、改任者'),('侯弘实','河中都指挥使、千乘人、受副职者')],when='926年三月康败后',place='蜀地',note='获与任用按主字，不能无据断二人同因叛变才获罪；籍贯不当现职驻地。')
E=ev('meng_relieves_taxes_settles_refugees','孟知祥选廉吏、除横赋、安集流散并下宽大令',31,'蜀中群盗','与民更始。',[('孟知祥','施行政措施者')],when='926年三月平康后',place='蜀州县',note='这是施政记载，不据宽大令推全部税取消或所有难民已安置。')
E=ev('zhaotingyin_zhangye_suppress_bandits','孟知祥遣赵廷隐、张业分兵讨蜀群盗，主书称悉诛',31,'遣左厢',None,[('孟知祥','派遣者'),('赵廷隐','左厢都指挥使、讨盗者'),('张业','右厢都指挥使、讨盗者')],when='926年三月平康后',place='蜀地',note='悉诛为书中概述，未给各战日期、地点、人数，不虚构每支盗军，也不据此认全蜀以后永久无盗。')
E=ev('siyuan_calls_yuanxingqin_rejected','李嗣源被逼时遣张虔钊、高行周等召元行钦共平乱，元疑诈扣使拒应并后撤',32,'李嗣源之为','遂引兵去。',[('嗣源','求同讨乱者'),('李绍荣','疑拒、扣使、撤军者'),('张虔钊','牙将、使者'),('高行周','牙将、使者')],when='926年三月鄴外营兵变期间追叙',place='鄴都城南',note='七使只具二名，不补造其余；元疑诈是其判断，未认李诈已证。')
E=ev('huoyanwei_troops_join_siyuan','李嗣源在魏县不足百人无兵仗，霍彦威镇兵五千闻其出城归附',32,'嗣源在魏县','嗣兵稍振。',[('嗣源','收部兵者'),('李绍真','镇兵统率者')],when='926年李嗣源出鄴到魏县后',place='魏县',note='不足百和五千为主书兵数，稍振不自行计算战斗力比例。')
claim('event',E,'description','旧明纪同记霍彦威五千镇州兵独不乱、闻李出城相率归之。',32,'時霍彥威所將鎮州兵五千人獨不亂，聞帝既出，相率歸帝。','帝为追称李嗣源，不指庄宗；镇州籍军旧补。',source='jiuwudaishi-035-926-mutiny',relation='corroborates')
E=ev('siyuan_advised_appeal_at_capital','李嗣源欲归藩待罪，霍彦威与安重诲劝疾赴京自明，李采纳',32,'嗣源泣谓','嗣源曰：“善！”',[('嗣源','拟归藩、改采入朝建议者'),('李绍真','劝入京者'),('安重诲','中门使、劝入京者')],when='926年魏县聚军后',place='魏县',note='归朝必藉口、归藩坐邀君为劝者预测，不当朝廷已作正式定罪；善不是本句已到京。')
E=ev('siyuan_gets_kangfu_horses','李嗣源由魏县南向相州，遇马坊使康福获数千马，始能成军',32,'丁卯',None,[('嗣源','南行得马者'),('康福','马坊使、蔚州人')],when='926年三月丁卯',place='魏县至相州',note='数千主书概数，旧明纪十一日获官马二千独立补，不能将两数相加。')
claim('event',E,'description','旧明纪记十一日发魏县至相州，获官马二千匹成军。',32,'十一日，發魏縣，至相州，獲官馬二千匹，始得成軍。','主数千与旧二千为不同精度，旧原月日另存不擅换成主丁卯确同日。',source='jiuwudaishi-035-926-mutiny',relation='adds')
E=ev('fuxi_retreat_blocked_yangxiwang','符习闻李嗣源军溃从鄴回军，淄州遇杨希望遣兵拦击后再西行',33,'平卢节度使','引兵而西。',[('符习','回军再转西者'),('杨希望','监军、遣兵拦击者')],when='926年三月鄴兵变后',place='鄴都、淄州及西行路',note='再西走不能即认已归李嗣源或其本镇永撤，后续归向留后段。')
E=ev('wanggongyan_kills_yangxiwang','王公俨攻杀杨希望，控制青州城',33,'青州指挥使',None,[('王公俨','青州指挥使、杀监军据城者'),('杨希望','被攻杀者')],when='926年三月鄴兵变后',place='青州',note='据城不等正式节度使任命，旧后授登州及后被杀是未来段不提前录。')
claim('event',E,'description','旧本纪追叙王公俨先受杨奖爱，乘其无备围第擒杀。',33,'公儼乘其無備，圍希望之第，擒而殺之。','旧补过程，非将后续王被霍诛提前到本次。',source='jiuwudaishi-037-926-qingzhou',relation='adds')
E=ev('provincial_eunuch_monitors_killed_overview','鄴军变后诸道多杀恃恩与节度争权的近侍监军',34,'时近侍','所在多杀之。',[],when='926年鄴兵变后各地概述',place='后唐诸道',note='多杀不是所有监军皆死，不把叙述群体实体化为全体已清除的确定名单。')
E=ev('kongqing_kills_yangjiyuan','杨继源谋杀孔勍，孔先诱杀监军',34,'安义监军','先诱而杀之。',[('杨继源','安义监军、被杀者'),('孔勍','节度使、先杀监军者')],when='926年鄴兵变后，本段确日未载',place='安义军、潞州',note='谋杀与实际先被杀区别；不合并杨继源与原名李继源或杨希望。')
claim('event',E,'description','旧孔传称监军杨继源与都将谋据潞州，事泄被诛。',34,'同光季年，監軍楊繼源與都將謀據潞州，事泄，誅之。','主谋杀节度、旧谋据州为不同范围叙法；同光季年不补精确日。',source='jiuwudaishi-064-926-kongqing',relation='adds')
E=ev('chunyuyan_kills_wuning_monitor','武宁监军谋杀霍彦威旧部据城，淳于晏率诸将先杀监军',34,'武宁监军',None,[('李绍真','已随李嗣源的节度背景者'),('淳于晏','权知留后、登州人、先杀监军者')],when='926年鄴军变后',place='武宁军',note='监军未名不造人物；元从为旧部，不认某个姓名或族属；淳于复姓不拆成姓淳。')
E=ev('cunxu_orders_advance_summer_autumn_taxes','因军食不足，朝廷令河南尹预借夏秋税，主书称民不聊生',35,'戊辰',None,[('帝','朝廷敕令主体')],when='926年三月戊辰',place='河南府',note='预借是提前征税非地方向朝廷借款；具体河南尹此句未名，不把已兼他职张全义强放执行角色。民不聊生是作者概述。')
E=ev('zhangquanyi_dies_luoyang','张全义闻李嗣源入鄴忧惧不食，卒于洛阳',36,'忠武节度使',None,[('全义','齐王、尚书令、去世者')],when='926年三月辛未',place='洛阳',note='闻后忧惧与死的叙事关联保留，不等现代医学确诊死因。')
claim('person',person('全义',36,'去世者',Q[36]['text']),'death_year','926年卒于洛阳。',36,Q[36]['text'],'同光四年三月辛未，未补未经换算的公历日。')
claim('event',E,'description','新全义传记因忧而卒，年七十五，谥忠肃。',36,'已而明宗至魏果反，全義以憂卒，年七十五，謚曰忠肅。','明宗至魏果反是新史叙法；年七十五为书载年龄不强算出生年，谥号授日未明，不同日强造授谥事件。',source='xinwudaishi-045-926-quanyi',relation='adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续25—36段原文逐字回查，主第30段两阅读块分别引用。两史对李嗣源受命、到鄴及兵变干支原月日有异，不强统一；主丁已朔/刑州留原字，以三月朔及邢州展示。王廷翰据旧同职同任校王延翰；李延厚与第9段李廷厚同职但身份未决，事件可检索，暂不造或合并人。崔向康称召孟缓兵得蜀为其话，不真授；主赢兵疑羸展示弱兵。军士坑军畏死为自陈，李先拒战后受逼入城，不简化成早已预谋。新霍独不入与主同入、出城时长各存。康金雁桥败擒非已诛，绵竹/绵州异说；旧补何建崇追擒。孟除横赋不等全免税，悉诛为概述。元扣使拒援及安霍入京劝说为行动/预测分开，康福马数千/旧二千分别。各地杀监军具体与概述区分，未名监军不造人；预借夏秋税为提前征，张全义忧卒不造医学死因，年龄不强算生日。'
for n in range(25,37):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(25,37)],next_paragraph=Q[37]['id'],next_volume=274,supplements=supplements,excluded_non_body=[],coverage='卷274第25—36段，原文件62—73行；李嗣源征鄴与被逼军变、汉州金雁桥康败擒、孟施政、魏县会军、地方诛监军、预借税及张全义卒。全110段累计36正文段，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(25,37)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
