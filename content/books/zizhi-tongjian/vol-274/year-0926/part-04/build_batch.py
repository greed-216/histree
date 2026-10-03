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
PREV=YEAR/'part-03'
specs=[
 ('tongjian-274-926-capture-and-monitors',PREV/'sources/library/tongjian-274-926-capture-and-monitors','8ecc7ee3','司马光等'),
 ('tongjian-274-926-treasury-and-jijing',P/'sources/library/tongjian-274-926-treasury-and-jijing','378d632d','司马光等'),
 ('tongjian-274-926-march-and-wangyan',P/'sources/library/tongjian-274-926-march-and-wangyan','378d632d','司马光等'),
 ('jiuwudaishi-051-926-congjing',P/'sources/library/jiuwudaishi-051-926-congjing','378d632d','薛居正等'),
 ('xinwudaishi-015-926-congjing',P/'sources/library/xinwudaishi-015-926-congjing','378d632d','欧阳修'),
 ('xinwudaishi-027-926-kangyicheng',P/'sources/library/xinwudaishi-027-926-kangyicheng','378d632d','欧阳修'),
 ('xinwudaishi-038-926-zhangjuhan',P/'sources/library/xinwudaishi-038-926-zhangjuhan','378d632d','欧阳修'),
 ('xinwudaishi-063-926-wangyan',P/'sources/library/xinwudaishi-063-926-wangyan','378d632d','欧阳修'),
 ('jiuwudaishi-034-926-treasury',P/'sources/library/jiuwudaishi-034-926-treasury','378d632d','薛居正等'),
 ('xinwudaishi-005-926-annals',YEAR/'part-01/sources/library/xinwudaishi-005-926-annals','91a1ec5d','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0926-p037-p040',
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
for n in range(37, 41):
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
    ck = f'claim_zztj_274_0926_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'从审':'李从璟','李继璟':'李从璟','李从审':'李从璟','李绍英':'房知温','房知温':'房知温','绍英':'房知温','从璋':'李从璋','建立':'王建立','义诚':'康义诚','审通':'安审通','金全':'安金全','衽母徐氏':'徐贤妃'}.get(name,name)
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
    if name not in registry:
        row['aliases']={'李从璟':['李從璟','李从审','李從審','李继璟','李繼璟'],'康义诚':['康義誠'],'房知温':['房知溫','李绍英','李紹英'],'安审通':['安審通'],'王建立':[],'李从璋':['李從璋'],'白从晖':['白從暉'],'翟建':[],'刘氏（王宗衍妾）':['劉氏（王宗衍妾）']}.get(name,row['aliases'])
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
E=ev('treasury_rations_cut_and_petition','租庸使因仓储不足减军粮，宰相百官请求用内库财救军',37,'租庸使','其财复集。”',[],when='926年三月军粮危机时',place='洛阳',note='租庸使本句未具姓名不擅置孔谦为实际裁令者；内库有余是上表主张，不当已实地核查库存。离心为所忧未来。')
claim('event',E,'description','旧本纪记壬戌豆卢革率百官请出内府金帛，不报。',37,'壬戌，宰臣豆盧革率百官上表，以魏博軍變，請出內府金帛優給將士。不報。','旧补领表者与日期，不报与主皇帝欲从后受阻叙法有别，不把已经上表等同成功筹款。',source='jiuwudaishi-034-926-treasury',relation='adds')
E=ev('liu_claims_heavenly_mandate_rejects_treasury','李存勖欲采上表，刘后以天命说回应',37,'上即欲','人如我何！”',[('帝','欲接受筹款请求者'),('刘后','以天命说回应者')],when='926年三月百官请出内库时',place='洛阳宫廷',note='天命与人如我何为皇后自述，不当超自然事实；欲从是态度，非已执行。')
E=ev('liu_displays_basins_children_to_chancellors','宰相再议筹款，刘后出妆具银盆与三幼子，声称仅余这些，请卖赡军，宰相惧退',37,'宰相又于','宰相惶惧而退。',[('刘后','展示财物与幼子并陈述者')],when='926年三月便殿再议内库时',place='洛阳便殿',note='主段跨两个阅读块，此从第二块取引，不拼快照；说宫财仅此为后话，未核财库，也未真卖皇子；三幼子不补姓名。')
claim('event',E,'description','旧本纪作妆奁、银盆各二，与主三银盆不同，均称皇子三人。',37,'皇后出宮中妝奩銀盆各二，並皇子滿哥三人，','各二与主三盆差异保留；满哥三人语不据此造三位同名满哥，也不认银盆成唯一实物盘点。',source='jiuwudaishi-034-926-treasury',relation='conflicts')
E=ev('yuanxingqin_accuses_siyuan_siyuan_appeals','元行钦退卫州奏李嗣源叛并合贼，李嗣源屡遣使上章自辩',37,'李绍荣自','一日数辈。',[('李绍荣','退军上奏指控者'),('嗣源','使者上章自理者')],when='926年三月鄴军变后',place='卫州、李嗣源军与朝廷',note='已叛与贼合为元上奏定性，与主被逼过程分别，不自动生成同谋边；使者次数为数辈概数。')
E=ev('congjing_sent_reassure_siyuan','李存勖令李嗣源长子李从璟前往传话，称信其父忠厚、勿自疑',37,'嗣源长子','勿使自疑。”',[('李从璟','原名从审、金枪指挥使、使者'),('帝','派遣者'),('嗣源','传谕对象')],when='926年三月鄴乱后',place='朝廷至卫州及魏地',note='从审、从璟、继璟据两史同长子同职同派使复用一个新主体；未据此说传谕实际到达父军。')
relationship('嗣源','李从璟','父亲',37,'嗣源长子从审为金枪指挥使','李嗣源是从审即李从璟的父亲；长子为主说明，不推母亲身份。')
claim('event',E,'description','新家人传明言从璟初名从审，同为金枪指挥使，庄宗命其宣旨。',37,'從璟初名從審，為人驍勇善戰，而謙退謹敕。從莊宗戰，數有功，為金槍指揮使。','姓名校核三名同人，有两书同长子、同职、同事件佐证，不把从审当另一子。',source='xinwudaishi-015-926-congjing',relation='adds')
E=ev('congjing_detained_released_by_yuan','李从璟到卫州被元行钦囚禁欲杀，请求还卫天子后获释',37,'从审至卫州','乃释之。',[('李从璟','被囚、请求返宿卫者'),('李绍荣','囚禁拟杀后释放者')],when='926年三月首次使父途中',place='卫州',note='欲杀与后来真杀区分，此段先获释，未提前录死亡；不亮父为李自己的解释。')
claim('event',E,'description','新家人传同记卫州被执将杀、请求归卫天子后获释。',37,'從璟馳至衞州，為元行欽所執，將殺之，','此引文为被执阶段，后文行钦释之确在同快照，不误记此时已死。',source='xinwudaishi-015-926-congjing',relation='corroborates')
E=ev('cunxu_renames_congjing_jijing','李存勖怜李从璟，赐名李继璟、待如子',37,'帝怜从审','待之如子。',[('帝','赐名优待者'),('李从璟','获名继璟者')],when='926年三月首次使父返还后',place='后唐朝廷',note='主待之如子仅待遇语；两史以为己子进一步支持养父，关系用补证独立引用，不因赐姓当生父。')
relationship('帝','李从璟','养父',37,'莊宗憐其言，賜名繼璟，以為己子。','新家人传明确以为己子，李存勖是李从璟的养父；生父李嗣源另边，不相互覆盖。',source='xinwudaishi-015-926-congjing')
claim('event',E,'description','旧宗室传也记庄宗改名继璟、以为己子。',37,'莊宗改其名為繼璟，以為己子，','旧原从璟与主从审同人，后文被杀尚未移到此赐名事件。',source='jiuwudaishi-051-926-congjing',relation='corroborates')
E=ev('yuan_blocks_siyuan_memorials','李嗣源奏章此后被元行钦阻隔，李因此疑惧',37,'是后嗣源','嗣源由是疑惧。',[('嗣源','奏章受阻者'),('李绍荣','阻奏者')],when='926年三月李从璟赐名后叙次',place='李嗣源军、卫州与朝廷联络路',note='主作者说皆为所遏，留为主记，不夸大成所有其他交通永远断绝。')
E=ev('shijingtang_proposes_capture_daliang','石敬瑭劝李嗣源果断，求三百骑先取大梁、成功则引大军',37,'石敬瑭曰','如此始可自全。”',[('石敬瑭','提出先取汴策略者'),('嗣源','受建议者')],when='926年三月上奏受阻后',place='李嗣源军中',note='求三百及若得是假设策略，不等此段已经派骑、攻入大梁；实施留下一段。')
E=ev('kangyicheng_urges_siyuan_follow_army','康义诚以军民怨怒为由劝李嗣源从众，称守节必死',37,'突骑都指挥使','守节必死。”',[('康义诚','突骑都指挥使、劝者'),('嗣源','受劝者')],when='926年三月上奏受阻后',place='李嗣源军中',note='从众则生守节必死为康的判断，不作客观必然；代北胡人依据原文不扩成具体部族。')
claim('event',E,'description','新康传同记魏军变后，康向李嗣源陈庄宗过失、劝其南向。',37,'從明宗討趙在禮，至魏而軍變，義誠前陳莊宗過失，勸明宗南嚮。','明宗是追称，康对帝过失的评价归属于康，不作独立审判。',source='xinwudaishi-027-926-kangyicheng',relation='corroborates')
E=ev('siyuan_orders_anzhonghui_gather_troops','李嗣源命安重诲发檄会兵',37,'嗣源乃令','移檄会兵。',[('嗣源','发令者'),('安重诲','移檄者')],when='926年三月听石、康建议后',place='李嗣源军与会兵诸镇',note='发檄为行为，尚不把被召各将都已经会合的后续动作提前。')
E=ev('siyuan_summons_four_commanders','李嗣源遣使召瓦桥杜晏球、段凝、房知温及奉化军安审通',38,'时齐州防御使','遣使召之。',[('嗣源','遣召者'),('李绍虔','齐州防御使、瓦桥被召者'),('李绍钦','泰宁节度使、瓦桥被召者'),('李绍英','贝州刺史、瓦桥被召者'),('安审通','北京右厢马军都指挥使、奉化军被召者')],when='926年三月檄会兵时',place='瓦桥、奉化军',note='绍虔为杜晏球、绍钦为段凝沿旧主体；绍英主自明房知温，新建规范房名并赐名别名。召不等已归队。安审通不擅并安审琦。')
E=ev('fangzhiwen_and_anshentong_identity','本段明示李绍英本姓房名知温，安审通为安金全之侄',38,'绍英，瑕丘人','金全之侄也。',[('李绍英','本房知温、瑕丘人'),('安审通','安金全侄'),('金全','被述侄系的安金全')],year=None,when='人物姓名、籍贯及家系说明，发生年不适用',place='瑕丘及家系背景',note='本姓姓名说明不当926恰好改名事件；侄未定叔伯长幼，事实保留不强建叔父方向。')
E=ev('wangjianli_saves_siyuan_household','李嗣源家在真定，王建立先杀监军，主称使家获全',38,'嗣源家在真定','建立，辽州人也。',[('嗣源','家属在真定者'),('王建立','虞候将、辽州人、杀监军者')],when='926年三月李嗣源会军前后叙次',place='真定',note='監军未名不创建人物；由是获全为主书归因，不说李嗣源自己同在真定遇刺。')
E=ev('congke_joins_wangjianli_then_siyuan','李从珂由横水经盂县赴镇州，与王建立军合后倍道从李嗣源',38,'李从珂自横水','倍道从嗣源。',[('从珂','率军来会者'),('王建立','合军者'),('嗣源','会军对象')],when='926年三月李嗣源檄会兵后',place='横水、盂县、镇州至李嗣源军',note='只依史载路线，不补未经核实的现代坐标或倍道具体速度。')
E=ev('siyuan_assigns_shi_vanguard_congke_rear','李嗣源谋白皋渡河，实际分三百骑给石敬瑭前驱，李从珂殿后',38,'嗣源以李绍荣','军势大盛。',[('嗣源','谋渡及分派者'),('石敬瑭','三百骑前驱统率者'),('从珂','后军统率者')],when='926年三月诸军会合后',place='白皋方向',note='分兵是前段提议后的实施；谋济不等本句已经渡河。军势大盛为史叙不量化。')
E=ev('congzhang_elected_xingzhou_liuhou','李从璋自镇州引军南行，过邢州被奉为留后',38,'嗣源从子',None,[('李从璋','主称李嗣源从子、南行被奉者')],when='926年三月会军南行时',place='镇州至邢州',note='从子为主家系说，未定叔伯细系不建叔父边；邢人奉留后不等帝正式任命。')
E=ev('baiconghui_guards_heyang_bridge','朝廷诏白从晖率骑扼守河阳桥',39,'癸酉','扼河阳桥，',[('白从晖','怀远指挥使、守桥者')],when='926年三月癸酉据主书',place='河阳桥',note='将骑扼为诏部署，不自行合并其与内官白从训。')
E=ev('cunxu_distributes_money_officials_contribute','李存勖出金帛给诸军，枢密宣徽内使及景进等献资协助',39,'帝乃出金帛','以助给赐。',[('帝','颁给者'),('景进','献助金帛者')],when='926年三月癸酉后叙次据主书',place='洛阳军中',note='献钱是具体行动，不认全体内使始终拒筹；主未列数额，不加总后来西川四十万。')
claim('event',E,'time_original','旧本纪记癸亥出钱帛给军，两枢密及宋唐玉、景进等各贡助。',39,'是日，出錢帛給賜諸軍，兩樞密使及宋唐玉、景進等各貢助軍錢幣。','是日承旧癸亥，与主癸酉不同。宋唐玉只旧补名单，未无据替换主宣徽使名。',source='jiuwudaishi-034-926-treasury',relation='adds')
E=ev('soldiers_reject_late_reward','军士领财后怨家属已经饿死，称给赐太迟',39,'军士负物','得此何为！”',[],when='926年三月给赐军财时',place='洛阳诸军',note='为军士话语，不当各军所有妻子都已死亡的总人口统计。')
claim('event',E,'description','旧本纪同记军士家乏食、妇女掇蔬，军士负物责給赐已晚。',39,'是時，軍士之家乏食，婦女掇蔬於野，及優給軍人，皆負物而詬曰：「吾妻子已殍矣，用此奚為！」','皆为史家概述不推全国人数，言妻子殍不造未名家庭死亡实体。',source='jiuwudaishi-034-926-treasury',relation='corroborates')
E=ev('yuanxingqin_returns_cunxu_rewards','元行钦由卫州至洛阳，李存勖赴鹞店慰劳',39,'甲戌','劳之。',[('李绍荣','还京受劳者'),('帝','往劳者')],when='926年三月甲戌据主书',place='卫州、洛阳、鹞店',note='旧甲子耀店异日异字另证保留，勿自动校成确定同日。')
claim('event',E,'time_original','旧本纪记甲子元行钦率部归、帝幸耀店劳之。',39,'甲子，元行欽自衛州率部下兵士歸，帝幸耀店以勞之。','主甲戌/鹞店与旧甲子/耀店不强统一。',source='jiuwudaishi-034-926-treasury',relation='conflicts')
E=ev('yuanxingqin_reports_bozhou_and_urges_east','元行钦称乱兵遣党据博州欲渡河，并请皇帝赴关东招抚，帝从',39,'绍荣曰',None,[('李绍荣','提出报告和建议者'),('帝','采纳建议者'),('翟建','其报告中博州据守者')],when='926年三月元还洛后',place='洛阳朝廷、博州与关东方向',note='主翟建白疑翟建自，按新本纪同博州守将校翟建，原字保留；乱兵派党与将袭是元陈述，不自动当已渡河实际袭城。晖、汴疑字未擅校具体第一州。')
claim('event',E,'description','新本纪明记博州守将翟建自称刺史，可核本段人名。',39,'博州守將翟建自稱刺史。','同年同博州据守者核主翟建白疑字，不把白作为真实别名，也不凭新记断元报告全部属实。',source='xinwudaishi-005-926-annals',relation='adds')
E=ev('jingjin_urges_kill_wangyan_group','景进等因帝将东征，称西南未安、王宗衍族党可能生变，劝除之',40,'景进等','不若除之。”',[('景进','建议杀降者'),('帝','受建议者'),('王衍','被建议处置者')],when='926年三月帝东征前',place='洛阳朝廷',note='恐为变是景进等预测，不建王宗衍实际谋反事件；李继岌未至、康初平为其论据。')
E=ev('cunxu_orders_xiangyansi_execute_wangyan','李存勖遣向延嗣持敕诛王宗衍一行',40,'帝乃遣','并从杀戳。”',[('帝','敕杀降者'),('向延嗣','赍敕使者'),('王衍','敕令对象')],when='926年三月帝东征前下敕，主未具执行日',place='洛阳至长安',note='主杀戳疑戮保留；此为原杀令，随从全部死亡不据此建既成事实，下一阶段张改字缩小范围。')
claim('event',E,'description','旧本纪同记元请幸汴、帝将发京时遣向延嗣诛王衍并夷族。',40,'元行欽請車駕幸汴州，帝將發京師，遣中官向延嗣馳詔所在誅蜀主王衍，仍夷其族。','旧诏范围已夷族叙法与主原一行、后改家分阶段不同，不覆盖主原敕改字。',source='jiuwudaishi-034-926-treasury',relation='corroborates')
E=ev('zhangjuhan_changes_edict_saves_followers','张居翰审已印敕，将一行改一家，使蜀百官仆役千余免死',40,'已印画','获免者千馀人。',[('张居翰','枢密使、改字者')],when='926年王宗衍诛令发出前审敕时',place='洛阳宫殿柱旁',note='千余为史载概数，不造逐名存活清单；原一行与一家指范围改变，尚非整个王氏免死。')
claim('event',E,'description','新宦者传同记张以诏傅柱，揩行改家，千余蜀降人获免。',40,'詔書言「誅衍一行」，居翰以謂殺降不祥，乃以詔傅柱，揩去「行」字，改為一「家」。時蜀降人與衍俱東者千餘人，皆獲免。','新传称杀降不祥为张理由，独立出书定位；不把传称遣诏魏王与主向延嗣混成同一送达路线。',source='xinwudaishi-038-926-zhangjuhan',relation='corroborates')
E=ev('wangyan_family_executed_qinchuan','向延嗣至长安，在秦川驿杀王宗衍宗族',40,'延嗣至长安','于秦川驿。',[('向延嗣','持敕行杀者'),('王衍','被杀者')],when='926年长安秦川驿遇害，主置三月条下未记确日',place='长安秦川驿',note='新蜀世家作同光四年四月、新本纪三月甲子，具体月日异说保留；不将同书各传各纪差异硬择一。')
claim('event',E,'time_original','新蜀世家将秦川驿诛王衍族记为同光四年四月。',40,'同光四年四月，行至秦川驛，莊宗用伶人景進計，遣宦者向延嗣誅其族。','主三月叙次、新本纪三月甲子与新世家四月异说待纸本；年926相同，不自动改主或按次序倒推日。',source='xinwudaishi-063-926-wangyan',relation='conflicts')
claim('event',E,'time_original','新本纪记三月甲子杀王衍、灭族。',40,'甲子，殺王衍，滅其族。','该段甲子列三月条，和新世家四月不同，同书两处仍分别引用。',source='xinwudaishi-005-926-annals',relation='adds')
E=ev('xuxianfei_final_protest','徐贤妃临刑指后唐弃信义，并预言对方将受祸',40,'衍母徐氏',None,[('徐贤妃','王宗衍母、临刑言者')],when='926年秦川驿王宗衍宗族遇害时',place='秦川驿',note='衍母徐氏沿已核徐贤妃主体；将受祸为临刑预测，不当此段已经发生庄宗死亡。')
E=event('wangyan_concubine_liu_refuses_pardon','新蜀世家补王宗衍妾刘氏拒行刑者免死之意，选择就死',40,'衍妾劉氏，鬒髮如雲而有色，行刑者將免之，劉氏曰：「家國喪亡，義不受辱！」遂就死。',[('刘氏（王宗衍妾）','被拟免、拒而就死者')],when='926年秦川驿行刑时，具体日期依新蜀世家四月叙次',place='秦川驿',source='xinwudaishi-063-926-wangyan',note='新世家补同事件，刘氏本名未载，不与李存勖刘后或其他刘氏合并；美貌为书载形容不作现代外貌复原事实。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续37—40段逐字回查，第37段跨两阅读块分别取引。内库有余是表言、天命及宫财仅此是后话，未当实盘；出幼子卖财为说辞未真售子，三盆/旧各二保留。李从审从璟继璟两史同长子同职同事确同人，生父李嗣源与新明确收为己子的养父李存勖分边；被囚获释不提前录死。石求三百是建议，次段派三百为实施；各军被召不等已会，房知温本名主自明，安审通不并审琦，侄未定叔伯长幼不强边。从璋主从子，群众奉邢留后不等帝任。军士称妻子殍非人口统计，给财主癸酉/旧癸亥、元回朝甲戌/旧甲子、鹞店/耀店各存。翟建白据新同博州校疑名，晖汴不擅校第一地。景进王族恐变为预测，帝原诛一行、张改一家、向实杀宗族分阶段；新张传敕魏王与主遣向不同，王遇害新世家四月、新本纪三月甲子、主三月条无日异说各存，徐临刑祸语为预测；新王妾刘氏补证独立主体不混刘后。'
for n in range(37,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(37,41)],next_paragraph=Q[41]['id'],next_volume=274,supplements=supplements,excluded_non_body=[],coverage='卷274第37—40段，原文件74—77行；军粮内库争议、李从璟传谕与收养赐名、李嗣源檄会兵、朝廷晚给军财、元劝关东、张改敕免从人及蜀王宗族遇害。926年共110正文段累计40，全年与本卷均未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(37,41)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
