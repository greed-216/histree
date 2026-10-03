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
OLD=ROOT/'content/books/zizhi-tongjian/vol-274/year-0925'
PREV=YEAR/'part-01'
specs=[
 ('tongjian-274-926-yedu',PREV/'sources/library/tongjian-274-926-yedu','91a1ec5d','司马光等'),
 ('tongjian-274-926-palace-guard',P/'sources/library/tongjian-274-926-palace-guard','0291ff48','司马光等'),
 ('jiuwudaishi-034-926-suppression',P/'sources/library/jiuwudaishi-034-926-suppression','0291ff48','薛居正等'),
 ('jiuwudaishi-074-926-kang-rebellion',P/'sources/library/jiuwudaishi-074-926-kang-rebellion','0291ff48','薛居正等'),
 ('xinwudaishi-044-926-kang-rebellion',P/'sources/library/xinwudaishi-044-926-kang-rebellion','0291ff48','欧阳修'),
 ('xinwudaishi-037-926-guocongqian',P/'sources/library/xinwudaishi-037-926-guocongqian','0291ff48','欧阳修'),
 ('jiuwudaishi-034-925-yedu-command',OLD/'part-02/sources/library/jiuwudaishi-034-925-yedu-command','44b6be0e','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0926-p013-p024',
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
for n in range(13, 25):
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
    ck = f'claim_zztj_274_0926_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
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
E=ev('wangzhengyan_meets_zhaozaili','王正言得知乱兵入城后步行见赵在礼请罪，赵慰谕遣还',13,'王正言方据按','慰谕遣之。',[('正言','留守、谒见请罪者'),('赵在礼','慰谕遣还者')],when='926年二月鄴都陷落后',place='鄴都',note='据按、士座为底本疑字，展示只概述行动不造词；赵称思归为其话，非确认全军无其他诉求。')
E=ev('zhaozaili_elected_weibo_liuhou','众推赵在礼为魏博留后并向朝廷奏报',13,'众推在礼','具奏其状。',[('赵在礼','被推留后者')],when='926年二月鄴都陷落后',place='鄴都',note='兵众推立不是已获皇帝正式任命。')
claim('event',E,'description','旧本纪同记众推在礼为兵马留后、草奏以闻。',13,'是日，眾推在禮為兵馬留後，草奏以聞。','兵马与魏博职名表述保留。',source='jiuwudaishi-034-925-yedu-command',relation='corroborates')
E=ev('zhangxian_rejects_zhaozaili_letter','赵在礼抚张宪家属并以书招诱，张宪不开封斩使奏报',13,'北京留守张宪',None,[('张宪','北京留守、拒招诱者'),('赵在礼','抚家属遣使招诱者')],when='926年二月鄴陷后，确日未载',place='鄴都及北京留守驻地',note='使者未名不造人物；抚家属与张宪不受招诱分开，不作结盟。')
E=ev('jingjin_promoted','景进加银青光禄大夫等官爵',14,'甲午',None,[('景进','受加官者')],when='926年二月甲午',place='后唐朝廷',note='底本御吏大夫疑御史大夫，原字留存；只按本句列任官不无据解释赏功原因。')
E=ev('shiyanqiong_arrives_luoyang','史彦琼到洛阳',15,'丙申','史彦琼至洛阳。',[('史彦琼','抵京者')],when='926年二月丙申',place='洛阳',note='与壬辰夜奔洛阳分别，不能当天即抵。')
E=ev('duanning_plan_rejected','李绍宏荐段凝，李存勖初许，因段凝所请皆亲善梁将而疑止',15,'帝问可为','疑之而止。',[('帝','问将、许后止者'),('绍宏','推荐者'),('李绍钦','拟将、提请偏裨者')],when='926年二月丙申后朝廷议将',place='洛阳',note='李绍钦复用段凝，不同于拟定任命已成；荐故将导致疑为主书述，不认偏裨确谋反。')
E=ev('yuanxingqin_sent_pacify_yedu','刘后荐元行钦，李存勖令其率三千骑招抚鄴都并征诸道兵',15,'皇后曰',None,[('刘后','推荐者'),('帝','派遣征兵者'),('李绍荣','归德节度使、招抚者')],when='926年二月丙申后',place='洛阳至鄴都',note='本次兼招抚并备不服，不等已赦乱兵；三千为史載兵数不反推实际到达率。')
claim('event',E,'description','旧本纪亦载命宋州节度使元行钦率骑三千赴鄴招抚、征诸道师。',15,'帝怒，命宋州節度使元行欽率騎三千赴鄴都招撫，詔征諸道之師進討。','旧本纪编于入鄴段，主编于丙申后；宋州与归德军镇表述相应。',source='jiuwudaishi-034-925-yedu-command',relation='corroborates')
E=ev('kang_taunts_dong_after_guo_death','郭崇韬死后，康延孝讥董璋依附，董惧谢罪',16,'郭崇韬之死也','谢罪。',[('李绍琛','讥问者'),('董璋','谢罪者')],when='926年正月郭死后追叙，确日未载',place='蜀地',note='呫嗫为康讥问，未作董与某人实际密谋的证据；郭死为背景不重复新死事件。')
E=ev('dongzhang_ordered_kill_lingde','李继岌到武连遇使，获知朱遇害，朝廷命董璋赴遂州诛朱令德',16,'魏王继岌军还','诛硃令德。',[('继岌','受使传诏者'),('董璋','被命率兵诛者'),('令德','命诛对象')],when='926年二月班师至武连时，旧史记癸巳',place='武连、遂州',note='传诏阶段，未录本句令德已被执行；前批诏魏王诛子与本段落实董将兵为不同阶段。')
claim('event',E,'time_original','旧康传将中军到武连闻诏记为二月癸巳。',16,'二月癸巳，中軍次武連，中使詔至，諭以西平王朱友謙有罪伏誅，命繼岌殺其子遂州節度使令德，延孝大驚。','有罪为使者诏书定性，与康自称无罪区分；主本段无癸巳，补他书日期不改主定位。',source='jiuwudaishi-074-926-kang-rebellion',relation='adds')
E=ev('kang_fears_execution_after_dong_passage','董璋过康延孝军不谒，康因不获诛令德任务而惊疑，酒后称将遭郭朱同祸',16,'时绍琛将后军','奈何！”',[('李绍琛','因任命及不谒生疑、陈述忧惧者'),('董璋','经过不谒者')],when='926年二月班师途中',place='魏城及后军',note='战功自称与将及我预测分别，未确认朝廷已有杀康密令。')
claim('event',E,'description','新康传同记董过军不谒、康恐郭朱之祸及己。',16,'繼岌不遣延孝，而遣董璋，延孝已自疑，及璋過延孝軍，又不謁，延孝大怒，','主记帝不委己与新继岌不遣用不同责任叙法保留，实际部署相应。',source='xinwudaishi-044-926-kang-rebellion',relation='corroborates')
E=ev('jiaowu_hezhong_soldiers_refuse_return','焦武等河中将哭诉朱案并称不再东归，康向李继岌报告军心欲乱',16,'绍琛所将多河中兵','欲为乱。”',[('焦武','河中将、哭诉拒东归者'),('李绍琛','向魏王报告者'),('继岌','泥溪、接报者')],when='926年二月丙申附近据旧康传，主曰是日',place='后军军门、剑州及泥溪',note='归则同诛为军将推测，欲乱为报语，不作其均已经叛逃；旧史所称二百口是焦武话不独立人口核验。')
claim('event',E,'description','旧康传同记焦武等号哭，康在丙申次剑州并报将士欲乱。',16,'時魏王繼岌到泥溪，延孝報繼岌云：「河中兵士號哭，欲為亂。」','同报告层次，主是日承叙次，日期仅补旧传不硬改主。',source='jiuwudaishi-074-926-kang-rebellion',relation='corroborates')
E=ev('kang_rebels_claims_xichuan_command','康延孝拥兵返蜀，自称西川节度等使，檄称奉诏代孟，三日众至五万',16,'丁酉',None,[('李绍琛','返蜀自称使职者'),('孟知祥','被其声称代任者')],when='926年二月丁酉起，三日间扩众',place='剑州至成都方向',note='奉诏为康檄声称，不认朝廷真任命康代孟；五万为史载概数，三日与新数日差别保留。')
claim('event',E,'description','新康传同记返蜀自称西川节度等使，数日众至五万。',16,'延孝遂擁其眾自劍州返入蜀，自稱西川節度、三川制置等使。馳檄蜀人，數日之間，眾至五萬。','主三日，新数日；不强算各日新增兵量。',source='xinwudaishi-044-926-kang-rebellion',relation='corroborates')
E=ev('jiyan_denied_fengxiang_seal','李继曮到凤翔，柴重厚拒交符印并催其入朝',17,'戊戌',None,[('李继\ue4be严','赴凤翔者'),('柴重厚','监军、拒符印者')],when='926年二月戊戌',place='凤翔',note='原文拆字名复用既核李继曮；催入朝不是已经入朝，符印拒交不等职任永撤。')
E=ev('kang_orders_cut_jubaijin','李继岌到利州，康延孝遣人断桔柏津',18,'己亥','桔柏津。',[('继岌','到利州者'),('李绍琛','遣断津者')],when='926年二月己亥',place='利州、桔柏津',note='主写遣人断，旧记守津使获康命令及魏王派兵控制；不能把诏与实际桥毁已证混为一谈。')
claim('event',E,'description','旧康传记守吉柏津使报康令断浮梁，魏王命梁汉颙控津。',18,'是夜，守吉柏津使密告魏王曰：「得紹琛文字，令斷吉柏浮梁。」繼岌懼，乃令梁漢顒以兵控吉柏津。','桔柏/吉柏同关津称写差异保留；旧为密报断桥令，不独立证成桥已毁。',source='jiuwudaishi-074-926-kang-rebellion',relation='adds')
E=ev('renhuan_commissioned_pursue_kang','李继岌任任圜为副招讨使，率七千步骑与梁汉颙、李廷安追康',18,'继岌闻之',None,[('继岌','任命者'),('任圜','副招讨使、追讨统率者'),('梁汉颙','都指挥使、追讨者'),('李延安','监军、追讨者')],when='926年二月己亥',place='利州至蜀追讨路',note='主李延安据旧同职同场李廷安校匹配，原名不改；旧七千骑、主步骑七千，军种不同记录。')
claim('event',E,'description','旧康传记任圜率七千骑，与梁汉颙、监军李廷安追讨。',18,'令圜率兵七千騎，與都指揮使梁漢顒、監軍李廷安討之。','同参与队伍核李延安为李廷安疑讹；七千骑与主七千步骑兵种差异待核。',source='jiuwudaishi-074-926-kang-rebellion',relation='adds')
E=ev('zhaotai_seizes_xingzhou','赵太等四百军士据邢州，自称安国留后，朝廷命霍彦威讨之',19,'庚子',None,[('赵太','邢州左右步直兵、据城者'),('李绍真','东北面招讨副使、奉命讨者')],when='926年二月庚子',place='邢州',note='赵自称留后不等正式任命；李绍真复用霍彦威。')
claim('event',E,'description','旧本纪同载左右步直四百据城，推赵太为留后、令李绍真讨。',19,'邢州左右步直軍四百人據城叛，推軍校趙太為留後，詔東北面副招討使李紹真率兵討之。','自称与众推为叙法差异，不造两人。',source='jiuwudaishi-034-926-suppression',relation='corroborates')
E=ev('hejianchong_captures_jianmen','任圜先遣何建崇攻下剑门关',20,'辛丑',None,[('任圜','遣将者'),('何建崇','别将、攻关者')],when='926年二月辛丑',place='剑门关',note='何建崇不无据合并后晋李建崇；本批只录关下，不提前录康败擒。')
claim('event',E,'description','旧康传同记辛丑令何建崇攻下剑门。',20,'辛丑，先令都將何建崇擊劍門，下之。','同日同战印证。',source='jiuwudaishi-074-926-kang-rebellion',relation='corroborates')
E=ev('yuanxingqin_attacks_and_offers_edict','元行钦攻鄴南门并招谕，赵在礼以羊酒劳军、请求代奏免死',21,'李绍荣至','遍谕军士。',[('李绍荣','攻南门与招谕者'),('赵在礼','城上犒师请求免死者')],when='926年二月辛丑据旧本纪',place='鄴都南门',note='请求免死不是已获赦；元宣敕不等乱兵已经归顺。')
claim('event',E,'description','旧本纪补元行钦说军士有社稷功，朝廷必赦，并宣诏。',21,'行欽曰：「上以汝輩有社稷功，必行赦宥。」因以詔書諭之。','必赦为元的话，不当皇帝实际已经赦免。',source='jiuwudaishi-034-926-suppression',relation='adds')
E=ev('huangfuhui_tears_edict_after_shi_threat','史彦琼辱骂威胁，皇甫晖称上不赦并鼓噪毁敕，乱军守城拒战',21,'史彦琼戟手','以状闻，',[('史彦琼','威胁辱骂者'),('皇甫晖','以不赦号召毁敕者'),('李绍荣','攻不利并上报者')],when='926年二月鄴南门招谕时',place='鄴都',note='底本胃其众疑谓，展示为称而原字保留；不赦先为皇甫推断，帝下一阶段言另录。')
E=ev('cunxu_orders_no_survivors_yuan_retreats','李存勖闻攻城不利，称克城勿留活口并增兵，元行钦退澶州',21,'帝怒曰',None,[('帝','下灭口命及征军者'),('李绍荣','退屯者')],when='926年二月壬寅退澶州；下令在前',place='后唐朝廷、澶州',note='勿遣噍类底本疑遗，灭口为命令未当城破已经杀尽；本段尚未攻克鄴都。')
claim('event',E,'description','旧本纪同记帝怒言勿遗噍类、壬寅退保澶州。',21,'行欽以聞，帝怒曰：「收城之日，勿遺噍類！」壬寅，行欽自鄴退軍，保澶州。','同命令与退军，未把预期收城当既成事实。',source='jiuwudaishi-034-926-suppression',relation='corroborates')
E=ev('wangwen_palace_revolt_execution','王温等五从马直军士杀军使谋乱，被擒斩',22,'甲辰夜','擒斩之。',[('王温','从马直军士、谋乱被处决者')],when='926年二月甲辰夜据主书',place='后唐宿卫军中',note='其余四人及军使未名不造人物；与旧甲午夜乱、磔门异说分别存。')
claim('event',E,'time_original','旧本纪记王温等五人夜乱为甲午，处刑写磔本军门。',22,'甲午，從馬直宿衛軍士王溫等五人夜半謀亂，殺本軍使，為衛兵所擒，磔於本軍之門。','主甲辰、旧甲午是日期差异；主擒斩、旧磔是刑法用字差异，待纸本，不无据互改。',source='jiuwudaishi-034-926-suppression',relation='conflicts')
E=ev('guocongqian_military_background','追叙优人郭从谦曾在得胜应募俘斩敌军，积功为从马直指挥使',22,'从马直指挥使','积功至指挥使。',[('郭从谦','优名郭门高、有军功的指挥使'),('帝','募勇士、设置亲军者')],year=None,when='庄宗与梁相拒得胜及亲军建设期间，确年未载',place='得胜及后唐亲军',note='本优人不等从无军功；郭门高为优名非另一人物；战于得胜及升迁追叙不强926。')
E=ev('guocongqian_adoptive_ties','郭从谦以叔父事郭崇韬，李存乂收郭从谦为假子',22,'郭崇韬方用事','为假子。',[('郭从谦','认叔、被收假子者'),('崇韬','被以叔父礼事者'),('李存乂','收假子者')],year=None,when='郭崇韬用事时期，确年未载',place='后唐朝廷',note='以叔父事并非血缘父系证明；假子为养子，不能写郭谦为李存乂亲生子。')
claim('event',E,'description','新伶官传明确称因同郭姓而拜郭崇韬为叔、李存乂收其养子。',22,'從謙以姓郭，拜崇韜為叔父，而皇弟存乂又以從謙為養子。','义认而非本宗叔侄；养子与假子对读。',source='xinwudaishi-037-926-guocongqian',relation='adds')
relationship('李存乂','郭从谦','养父',22,'睦王存乂以从谦为假子。','李存乂是郭从谦的养父；时间未明且非生父。')
E=ev('guocongqian_feasts_officers_mourns_guo','郭从谦以私财屡宴从马直诸校并哭诉郭崇韬冤',22,'及崇韬、存乂','崇韬之冤。',[('郭从谦','出私财宴校、称冤者')],when='926年郭、李存乂案后',place='从马直军中',note='冤为郭从谦所说；并非宴诸校就能推成人人同谋关系。')
E=ev('cunxu_jokes_accuses_guocongqian','李存勖戏言郭从谦附郭、存乂并教王温反，郭因此更惧',22,'及王温作乱','从谦益惧。',[('帝','戏言指责者'),('郭从谦','受指责而惧者')],when='926年王温乱被平后',place='后唐朝廷',note='戏言为主书语气；教王温反不独立确证郭实际教唆。')
E=ev('guocongqian_spreads_future_purge_rumor','郭从谦向诸校称鄴平后皇帝将尽坑亲军，劝尽财酒肉，使军心不安',22,'既退',None,[('郭从谦','传播坑军说、鼓动者')],when='926年王温案后',place='从马直军中',note='未来尽坑为郭向军士所说，未作真实帝诏或已执行屠杀。')
claim('event',E,'description','新伶官传同记郭以坑军说激军士，军士信而欲乱。',22,'軍士問其故，從謙因曰：「上以王溫故，俟破鄴，盡阬爾曹。」軍士信之，皆欲為亂。','信传言与朝廷真有清洗计划区别。',source='xinwudaishi-037-926-guocongqian',relation='corroborates')
E=ev('wangyan_halted_changan','王宗衍到长安，被诏令停留',23,'乙巳',None,[('王衍','被押送至长安、奉诏止留者')],when='926年二月乙巳',place='长安',note='仅止行，不提前录其三月被杀。')
E=ev('princes_remain_capital_background','追叙李存勖诸弟领节度却留京食俸',24,'先是','但食其俸。',[('帝','诸弟为帝弟的背景主体')],year=None,when='926年命皇弟赴镇之前背景，起始未明',place='后唐京师',note='不无据认此前所有节度使均不赴任，限帝诸弟。')
E=ev('cunba_ordered_hezhong','朝廷始命永王李存霸赴河中任护国节度',24,'戊申','至河中。',[('李存霸','护国节度使、被命赴镇者')],when='926年二月戊申',place='洛阳至河中',note='命赴镇与实际抵镇区别；原段戊申先于丁未叙述，保留原序及各干支不改写。')
claim('event',E,'description','旧本纪亦载河中永王存霸归藩之诏。',24,'詔河中節度使、永王存霸歸藩。','旧于戊申职任条后记归藩，主明戊申始命；不自行换公历。',source='jiuwudaishi-034-926-suppression',relation='corroborates')
E=ev('yuanxingqin_second_assault_yangzhongba_dies','元行钦率诸道兵再攻鄴都，杨重霸等数百登城无援而皆死',24,'丁未','无降意。',[('李绍荣','再攻统率者'),('杨重霸','裨将、登城战死者')],when='926年二月丁未再攻、庚戌登城',place='鄴都',note='数百史载概数；未认杨重霸与安重霸、刘重霸同人。无继指援军未继，不认叛变。')
claim('event',E,'time_original','旧本纪同记丁未元行钦率诸道再攻鄴都。',24,'丁未，鄴都行營招撫使元行欽率諸道之師再攻鄴都。','同日同战。',source='jiuwudaishi-034-926-suppression',relation='corroborates')
E=ev('jiji_delays_return_waiting_renhuan','朝廷不断遣使催李继岌东还，继岌因精兵随任圜讨康而留利州等待',24,'朝廷患之',None,[('继岌','留利州候军者'),('任圜','率中军精兵追讨者'),('李绍琛','追讨对象')],when='926年二月鄴战不利后',place='后唐朝廷、利州',note='不能东还为军兵处置背景，不无据归因为李继岌有叛志。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续13—24段逐字回查；主书与两五代史独立定位。赵在礼被推留后不等朝廷正式授；段凝初许后疑止与元行钦招抚分别，赦免承诺不等已赦，帝灭口命不等既行。康功劳/将及我属本人陈述，奉诏代孟为其檄说，未真授。李继拆字严复用李继曮；李延安据旧同职同队李廷安校疑，步骑七千与旧七千骑分别。王温主甲辰旧甲午、主斩旧磔保留；郭门高是优名，亲軍与得胜功追叙不强926，认叔非血亲，李存乂养父关系明确。郭称尽坑为其传播，不当真实帝诏。王衍长安止不先录死；皇弟留京追叙未定年，戊申与丁未按底本叙次分别，杨重霸不并他重霸。展示简体，原文疑字原样保留。'
for n in range(13,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,25)],next_paragraph=Q[25]['id'],next_volume=274,supplements=supplements,excluded_non_body=[],coverage='卷274第13—24段，原文件50—61行；鄴乱后招抚与攻城、康延孝返蜀、郭从谦与亲军危机背景、王衍止长安及皇弟赴镇。926年全110正文段，本批后累计24段，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(13,25)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
