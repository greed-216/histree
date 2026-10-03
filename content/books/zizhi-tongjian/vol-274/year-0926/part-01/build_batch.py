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
specs = [
 ('tongjian-274-925-year-end',OLD/'part-03/sources/library/tongjian-274-925-year-end','3ebe2df2','司马光等'),
 ('tongjian-274-926-crisis',P/'sources/library/tongjian-274-926-crisis','91a1ec5d','司马光等'),
 ('tongjian-274-926-beizhou',P/'sources/library/tongjian-274-926-beizhou','91a1ec5d','司马光等'),
 ('tongjian-274-926-yedu',P/'sources/library/tongjian-274-926-yedu','91a1ec5d','司马光等'),
 ('jiuwudaishi-034-926-january',P/'sources/library/jiuwudaishi-034-926-january','91a1ec5d','薛居正等'),
 ('xinwudaishi-005-926-annals',P/'sources/library/xinwudaishi-005-926-annals','91a1ec5d','欧阳修'),
 ('xinwudaishi-045-926-youqian',P/'sources/library/xinwudaishi-045-926-youqian','91a1ec5d','欧阳修'),
 ('xinwudaishi-045-926-shiwu',P/'sources/library/xinwudaishi-045-926-shiwu','91a1ec5d','欧阳修'),
 ('jiuwudaishi-098-926-zhangli',P/'sources/library/jiuwudaishi-098-926-zhangli','91a1ec5d','薛居正等'),
 ('xinwudaishi-014-925-delayed-return',OLD/'part-03/sources/library/xinwudaishi-014-925-delayed-return','3ebe2df2','欧阳修'),
 ('jiuwudaishi-034-925-yedu-command',OLD/'part-02/sources/library/jiuwudaishi-034-925-yedu-command','44b6be0e','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:4]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0926-p001-p012',
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
    ck = f'claim_zztj_274_0926_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
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
E=ev('jiyan_escort_wangyan','李继岌遣李继曮、李严押送王宗衍及宗族百官赴洛阳',1,'春，正月',None,[('继岌','派遣者'),('李继\ue4be严','押送者'),('李严','押送者'),('王衍','被押送者')],when='926年正月庚申',place='成都至洛阳',note='底本李继拆字严复用既核李继曮；李严为另一人；数千为史载概数，押送不等本段已抵京或被杀。')
E=ev('youqian_rejects_eunuch_demands','朱友谦拒绝伶宦无厌索求',2,'河中节度使','遂拒不与。',[('李继麟','拒索者'),('帝','与朱旧交、厚待者')],year=None,when='朱友谦入朝前背景，确年未载',place='河中',note='作为背景单录；厚待与伶宦索求分开，不能强定首次拒绝在926。')
E=ev('youqian_reviews_troops_for_shu','追叙伐蜀时朱友谦阅兵并遣朱令德率兵从征',2,'大军之征蜀也','以从。',[('李继麟','阅兵派子者'),('令德','率军从征者')],year=925,when='925年后唐征蜀时追叙',place='河中',note='与下文景进指自卫的谗言区别，明确征蜀背景非926新征。')
E=ev('jingjin_accuses_youqian_guo_collusion','景进与宦官指朱友谦阅兵自卫、与郭崇韬内外相应',2,'景进与宦官','故也。”',[('景进','指控者'),('李继麟','被指控者'),('崇韬','被指与朱阴谋者')],when='926年朱友谦入朝前',place='后唐朝廷',note='主书明称谮，谋反及内外相应不作已证实的行动或关系。')
claim('event',E,'description','新史同记景进与伶宦将阅兵、征蜀及郭氏案说成朱友谦谋反。',2,'又言：「與崇韜謀反。」','新传保留为景进指控。',source='xinwudaishi-045-926-youqian',relation='corroborates')
E=ev('youqian_enters_court_despite_warning','朱友谦不听亲近劝阻，入朝求当面自明',2,'继麟闻之惧',None,[('李继麟','入朝求自明者')],when='926年正月癸亥',place='河中至后唐朝廷',note='朱认为面陈可使谗人获罪为其预期，未记录这一预期已实现。')
claim('event',E,'description','旧史本纪同载癸亥李继麟来朝。',2,'癸亥，河中節度使李繼麟來朝。','李继麟复用朱友谦主体。',source='jiuwudaishi-034-926-january',relation='corroborates')
E=ev('jiji_leaves_renhuan_for_meng','李继岌将班师，令任圜权知留事等待孟知祥',3,'魏王继岌将发成都','诸军部署已定，',[('继岌','部署留守者'),('任圜','权知留事者'),('孟知祥','待到任者')],when='926年正月班师前',place='成都',note='将发不等本日已离城；孟待至不等已经到成都。')
E=ev('jiji_rejects_liu_order_then_yields','马彦珪出示刘后教令，李继岌以无帝敕拒杀郭，经李从袭力争后同意',3,'是日，马彦珪至','不得已从之。',[('马彦珪','带教令至蜀者'),('继岌','先拒后从者'),('李从袭','以危险力劝者'),('刘后','教令作者'),('崇韬','拟杀对象')],when='926年正月杀郭前一日叙次',place='成都',note='皇后教不等皇帝敕；李从袭称郭闻之会中途变为预测，不录郭谋反已实。')
claim('event',E,'description','新史继岌传同记上无诏书、只有皇后手教，继岌先拒后从。',3,'繼岌曰：「上無詔書，但皇后手教，安能殺招討使？」','从袭所称密敕是说辞；引用不是确认皇帝有敕。',source='xinwudaishi-014-925-delayed-return',relation='corroborates')
E=ev('guo_chongtao_killed_in_chengdu','李从袭召郭崇韬计事，李环击杀郭并杀郭廷诲、郭廷信',3,'甲子旦','外人犹未之知。',[('李从袭','借魏王命召郭者'),('继岌','下命并避楼者'),('李环','击杀郭者'),('崇韬','遇害者'),('郭廷诲','同时被杀者'),('郭廷信','同时被杀者')],when='926年正月甲子旦',place='成都',note='郭从楼阶升，李环击其首；同场二子被杀未指定李环亲杀二子，演员角色分别；后教与皇帝敕区分，未将其误录为925。')
claim('event',E,'description','旧本纪与新本纪均记甲子魏王继岌在蜀杀郭；新本纪另记二子。',3,'甲子，魏王繼岌殺樞密使郭崇韜於西川，夷其族。','旧本纪以统率者表述责任，主书李环为实际击杀者。',source='jiuwudaishi-034-926-january',relation='corroborates')
claim('event',E,'description','新本纪记甲子杀郭及二子，注文说明后教非天子命。',3,'甲子，魏王繼岌殺郭崇韜及其二子于蜀。','不把后教改成帝敕。',source='xinwudaishi-005-926-annals',relation='corroborates')
for son in ['郭廷诲','郭廷信']:
 relationship('崇韬',son,'父亲',3,'并杀其子廷诲、廷信。','其子承郭崇韬；复用已有儿子主体及同向关系，不建反向重复。')
E=ev('lisong_forges_edict_after_guo_death','李崧责问擅杀后，为稳定军中伪造敕书并用蜡印宣示',3,'都统推官','军中粗定。',[('李崧','先责问后伪造敕书者'),('继岌','承认悔不及者')],when='926年正月甲子郭死后',place='成都',note='矫为敕书发生在杀后，不是帝原来下令的凭证；李崧职都统推官籍饶阳，粗定不夸大为全军长久稳定。')
E=ev('zhangli_mourns_guo','郭左右窜匿，张砺独到魏王府恸哭',3,'崇韬左右','恸哭久之。',[('张砺','掌书记、赴府恸哭者')],when='926年正月郭遇害后',place='成都魏王府',note='主书张拆字厉据旧史卷98滏阳、掌军书、府第恸哭同事校为张砺；原字保留，不创建张厉另一人。')
claim('event',E,'description','旧史张砺传同记郭亲信奔逃，张砺独诣魏王府第恸哭。',3,'蜀平，崇韜為魏王繼岌所誅，時崇韜左右親信皆懼禍奔逃，惟礪詣魏王府第，慟哭久之，時人皆服其高義。','同籍贯军书职及同事核身份；高义为旧史评价。',source='jiuwudaishi-098-926-zhangli',relation='corroborates')
E=ev('renhuan_replaces_guo_military','李继岌令任圜代郭崇韬总军政',3,'继岌命任圜','总军政。',[('继岌','任命者'),('任圜','代总军政者')],when='926年正月甲子后叙次',place='成都',note='与此前权知留事为不同阶段。')
E=ev('litingan_presents_shu_musicians','李廷安献蜀乐工，李存勖赞严旭歌唱并许恢复蓬州刺史',3,'魏王通谒李廷安',None,[('李廷安','献乐工者'),('严旭','以歌得刺史者'),('帝','问歌、许复任者')],when='926年正月本段朝廷叙次，确日未载',place='后唐朝廷',note='献二百余人与严旭同段；许复不等已有赴蓬州到任证明。严旭复用前批，主与旧本纪乐人数不同并列，不精确相加。')
claim('event',E,'description','旧本纪记李廷安进西川乐官二百九十八人。',3,'西川行營都監李廷安進西川樂官二百九十八人。','与主书二百余为不同记数及表述，保留各自证据；旧本纪职都监与主通谒有别。',source='jiuwudaishi-034-926-january',relation='adds')
E=ev('meng_arrives_chengdu_pacifies','孟知祥到成都，慰抚吏民并犒赐将卒',4,'戊辰',None,[('孟知祥','到任安抚者')],when='926年正月戊辰',place='成都',note='去留帖然为主书局部安定叙述，不推后续四川全境无叛乱。')
E=ev('chenben_defeated_killed','闽军击败陈本并将其斩杀',5,'闽人',None,[('陈本','被击败斩杀者')],when='926年正月本段，确日未载',place='闽地，确地本段未明',note='延续925围汀州陈本主体，主书此次仅闽人，不擅指定柳邕为斩者。')
E=ev('abaoji_attacks_jurchen_bohai','阿保机攻女真、渤海',6,'契丹主','及勃海，',[('契丹主','攻伐者')],when='926年正月本段，确日未载',place='女真及渤海',note='勃海与渤海为同地表述；本段攻而未灭，不能提前录渤海灭亡结果。')
claim('event',E,'description','旧本纪亦载契丹寇女真、渤海。',6,'契丹寇女真、渤海。','攻伐对应，不扩为本段已经灭国。',source='jiuwudaishi-034-926-january',relation='corroborates')
E=ev('khitan_sends_envoy_for_peace','契丹恐后唐乘虚来袭，派梅老鞋里来修好',6,'恐唐乘虚',None,[('契丹主','派使者')],when='926年正月戊寅',place='契丹至后唐',note='梅老鞋里断名尚待核，留在事件文本暂不新建个人；恐乘虚袭为主书叙述的动机，未录唐真的已袭。')
claim('event',E,'description','旧本纪记阿保机戊寅遣使贡良马；新本纪记梅老鞋里来。',6,'戊寅，契丹阿保機遣使貢良馬。','主未载礼品，旧补良马，不能由贡马认无修好目的。',source='jiuwudaishi-034-926-january',relation='adds')
claim('event',E,'description','新本纪同载戊寅契丹使梅老鞋里来。',6,'戊寅，契丹使梅老鞋里來。','两书无分隔，尚不决是一名、两名或译名职称组合，勿拆造实体。',source='xinwudaishi-005-926-annals',relation='corroborates')
E=ev('guo_three_sons_killed_luoyang','马彦珪还洛阳后，朝廷公布郭罪名并杀郭廷说、郭廷让、郭廷议',7,'马彦珪还','廷议，',[('马彦珪','回报者'),('帝','朝廷处置者'),('郭廷说','被杀者'),('郭廷让','被杀者'),('郭廷议','被杀者')],when='926年正月马彦珪回洛后',place='洛阳',note='公开罪名是朝廷公布内容，不等独立查明郭罪；与成都另二子同日遇害分录，本句未给三子被杀确日。')
for son in ['郭廷说','郭廷让','郭廷议']:
 relationship('崇韬',son,'父亲',7,'并杀其子廷说、廷让、廷议，','其子承郭崇韬，父亲方向明确。')
E=ev('cunxu_secretly_monitors_guo_discussion','郭案使朝野骇惋、议论纷纷，李存勖遣宦者秘密察议',7,'于是朝野','潜察之。',[('帝','遣密察者')],when='926年正月公布郭案后',place='后唐朝廷',note='记录舆情与监视动作，未把群议一致解释为全朝支持郭。')
E=ev('cunyi_detained_then_killed','宦官指李存乂为郭称冤怨望，李存乂被幽禁后杀害',7,'保大节度使',None,[('李存乂','郭女婿、被幽后杀者'),('崇韬','姻亲背景者')],when='926年正月庚辰幽禁，寻杀',place='李存乂第宅',note='称冤怨望为宦官告言，不确证反谋；郭之婿单列事实，不创造未知郭女；主书庚辰是幽、寻杀，旧本纪庚辰伏诛为日期叙法异同。')
claim('event',E,'description','旧本纪记庚辰帝异母弟存乂伏诛，并说明其为郭崇韬子婿。',7,'庚辰，帝異母弟鄜州節度使存乂伏誅。存乂，郭崇韜之子婿也，故亦及於禍。','旧记当日诛，主记当日幽后寻杀，保留叙次差别，兄弟边已925明确不重复。',source='jiuwudaishi-034-926-january',relation='adds')
E=ev('jingjin_renews_youqian_accusation','景进声称朱友谦与郭谋反、郭死又与李存乂连谋，宦官劝速除',8,'景进言','速除之，',[('景进','转述告变者'),('李继麟','被指谋反者'),('崇韬','指控所涉者'),('李存乂','被指连谋者'),('帝','被劝除朱者')],when='926年正月郭死后',place='后唐朝廷',note='言河中人告变是二手指控，未录真实谋反事实或同谋关系。')
claim('event',E,'description','新传补景进使人伪造告变书，庄宗受其惑。',8,'景進使人詐為變書，告友謙反。','新史指告变书系伪造为补证，主书未明此细节；不是朱确实反。',source='xinwudaishi-045-926-youqian',relation='adds')
E=ev('youqian_transferred_then_killed','李存勖徙朱友谦为义成节度使，遣朱守殷围第、驱出徽安门杀之并复旧姓名',8,'帝乃徙','曰硃友谦。',[('帝','徙镇及遣杀者'),('李继麟','被徙、被杀及恢复姓名者'),('硃守殷','围第驱杀者')],when='926年正月庚辰据旧本纪，主书是夜',place='洛阳徽安门外',note='义成/滑州是同军镇称谓，徙任与杀害同事件保留阶段；姓名朱友谦复用，不新建李继麟。')
claim('event',E,'description','旧本纪同载庚辰李继麟徙滑州，随即朱守殷围第诛之。',8,'是日，以河中節度使、守太師、兼尚書令、西平王李繼麟為滑州節度使，尋令朱守殷以兵圍其第，誅之，夷其族。','是日承庚辰；主徽安门外地点用主书。',source='jiuwudaishi-034-926-january',relation='corroborates')
E=ev('orders_to_kill_youqian_sons_household','朝廷分别命李继岌、王思同、夏鲁奇诛朱令德、李令锡及朱家',8,'友谦二子','家人于河中。',[('令德','武信节度使、诏令对象'),('令锡','忠武节度使、诏令对象'),('继岌','被命诛令德者'),('王思同','郑州刺史、被命诛令锡者'),('李绍奇','河阳节度使、被命诛家属者')],when='926年正月朱遇害后诏令',place='遂州、许州、河中',note='诏令与实际执行分别，本段未具令德、令锡实际被杀日；令锡沿用本站李令锡，夏鲁奇与李绍奇据既有赐姓名核同主体。')
claim('event',E,'description','新朱传同载三路诛杀诏令，并明确夏鲁奇负责河中家属。',8,'詔魏王繼岌殺令德於遂州，王思同殺令錫於許州，夏魯奇族其家屬于河中。','主赐名李绍奇对应夏鲁奇，非不同人。',source='xinwudaishi-045-926-youqian',relation='corroborates')
for son in ['令德','令锡']:
 relationship('李继麟',son,'父亲',8,'友谦二子，令德为武信节度使，令锡为忠武节度使；','明确朱友谦二子，沿已有规范名与同向关系。')
E=ev('zhangshi_separates_servants_shows_iron_charter','朱友谦妻张氏请求不滥及婢仆，宗族就刑，并出示铁券',8,'绍奇至其家','亦为之惭。',[('张氏（朱友谦妻）','分辨婢仆、族人及出示铁券者'),('李绍奇','执行河中诛族者')],when='926年正月朱遇害后，确日未载',place='河中朱友谦家',note='二百余、婢仆百、族百为主书概数，勿机械计算精确死亡总数；主未直接写释放婢仆，不超出别其婢仆。去年赐铁券为张氏话，既有925背景不新造926赐券。')
claim('event',E,'description','新朱传同记张氏请求不滥及平人、别婢仆而族百口就刑，并出示铁券。',8,'乃別其婢僕百人，以其族百口就刑。','史载数量保持概数语境，族诛与婢仆分离不合并全数都死。',source='xinwudaishi-045-926-youqian',relation='corroborates')
relationship('张氏（朱友谦妻）','李继麟','妻子',8,'友谦妻张氏','张氏是朱友谦的妻子；明确单向妻子关系，未知本名不杜撰。')
E=ev('youqian_old_officers_family_execution','朱友谦旧将史武等七名刺史因朱案被族诛',8,'友谦旧将','皆坐族诛。',[('史武','旧将、刺史、被族诛者')],when='926年正月丁亥据两史，主段未记日',place='后唐诸州，具体行刑处未明',note='主吏武据两史同旧将七刺史族诛校为史武，保留底本字；旧本纪称无罪族诛为书评，主坐不等谋反事实。')
claim('event',E,'description','旧本纪载丁亥史武等七人籍没、并称无罪族诛。',8,'丁亥，詔朱友謙同惡人史武等七人，已當國法，並籍沒家產。武等友謙舊將，時皆為刺史，並以無罪族誅。','同恶为诏罪名，与史书无罪评论并列；不是独立核定同恶。',source='jiuwudaishi-034-926-january',relation='adds')
claim('event',E,'description','新本纪列七人：史武、薛敬容、周唐殷、杨师太、王景、来仁、白奉国。',8,'丁亥，殺李繼麟之將史武、薛敬容、周唐殷、楊師太、王景、來仁、白奉國，皆滅其族。','主仅列一名其余六名作为新史同案补证，暂保留文本并非另假设交往关系。',source='xinwudaishi-005-926-annals',relation='adds')
claim('event',E,'description','新朱传也记史武等七人因朱案族诛，并称天下冤之。',8,'友謙死，其將史武等七人皆坐友謙族誅，天下冤之。','天下冤之为史家评价，非现代全体舆论统计；与新本纪同书并非完全独立证据。',source='xinwudaishi-045-926-shiwu',relation='corroborates')
E=ev('luoyang_hungry_army_rumors','洛阳诸军饥窘造谣，伶官采报，主书将郭、朱之祸与此联系',8,'时洛中诸军','皆及于祸。',[],when='926年郭、朱案背景概述',place='洛阳',note='主书作者因果叙述保留为归因，不认谣言内容为真或量化饥饿程度。')
E=ev('zhu_shouyin_investigates_warns_siyuan','李嗣源受谣言牵涉，朱守殷奉帝命察看并私劝归藩避祸',8,'成都节度使','皆委之于命耳。”',[('嗣源','被察并回应者'),('帝','遣察者'),('硃守殷','奉察私劝者')],when='926年正月郭朱案后',place='洛阳，李嗣源入朝期间',note='主成都节度使据925入朝段成德及新本纪926成德李嗣源校其职名，非李嗣源镇成都；只录察及建议，不录其已经离京归镇。')
claim('event',E,'description','新本纪同年记李嗣源官成德军节度使，可核主书成都为疑字。',8,'甲辰，成德軍節度使李嗣源討趙在禮。','引用后续甲辰条仅核同年官镇身份，不把讨赵事件提前生成在当前正月段。',source='xinwudaishi-005-926-annals',relation='adds')
E=ev('lishaohong_protects_siyuan','主书称李嗣源屡处险境，赖李绍宏营护得全',8,'时伶宦用事',None,[('嗣源','获营护者'),('绍宏','宣徽使、营护者')],year=None,when='同光末伶宦用事时期概述，具体起讫未明',place='后唐朝廷',note='数四为概述，未建四次各有具体日期的事件；有营护不自动推成固定盟友关系。')
E=ev('jiji_assigns_six_chengdu_commanders','李继岌留李仁罕等六将戍成都',9,'魏王继岌留','戍成都。',[(x,r) for x,r in [('李仁罕','陈留人、马步都指挥使'),('潘仁嗣','东光人、马军都指挥使'),('赵廷隐','左厢都指挥使'),('张业','浚仪人、右厢都指挥使'),('武漳','文水人、牙内指挥使'),('李廷厚','平恩人、骁锐指挥使'),('继岌','派留戍将者')]],when='926年正月甲申离成都前部署',place='成都',note='籍贯及职名依据主句逐人分列，不能推为六人亲属或互相盟友。')
E=ev('jiji_departs_kang_rearguard','李继岌离成都，命康延孝率一万二千人为后军，距中军一舍',9,'甲申',None,[('继岌','班师者'),('李绍琛','后军统率者')],when='926年正月甲申',place='成都及东归路',note='一舍不自行换算现代公里；只记初始命令，康后叛待连续后段处理。')
E=ev('lishaohong_appointed_shumishi','李绍宏由宣徽南院使任枢密使',10,'二月',None,[('绍宏','受任者')],when='926年二月己丑朔',place='后唐朝廷',note='与前段宣徽使营护时期区分。')
claim('event',E,'description','新本纪同记二月己丑李绍宏任枢密使。',10,'二月己丑，宣徽南院使李紹宏為樞密使。','同日同职印证。',source='xinwudaishi-005-926-annals',relation='corroborates')
E=ev('yangrenzhen_troops_retained_beizhou','杨仁晸所部戍瓦桥逾年轮替归来，被令留屯贝州',11,'魏博指挥使','敕留屯贝州。',[('杨仁晸','魏博指挥使、率戍归兵者')],when='926年二月贝州兵变前',place='瓦桥至贝州',note='戍逾年为跨年背景，不反推出戍开始确日；恐鄴空兵变是朝廷理由，未等已有兵变。')
E=ev('rumor_guo_killed_jiji','民间传播郭已杀李继岌并自王蜀的讹言',11,'时天下莫知','故族其家。”',[],when='926年郭遇害后、贝州兵变前',place='后唐民间',note='明确讹言，不建立李继岌本时死亡事件或郭称蜀王的任职事实。')
E=ev('secret_order_shiyanqiong_kill_jianhui','李存勖密敕史彦琼杀澶州刺史朱建徽',11,'硃友谦子','史彦琼杀之。',[('帝','密敕者'),('史彦琼','受敕者'),('朱建徽','澶州刺史、命杀对象')],when='926年二月贝州乱前叙次，确日未载',place='鄴都、澶州',note='主密敕为命令，不强断本句已完成杀害或确行刑日。')
relationship('李继麟','朱建徽','父亲',11,'硃友谦子建徽为澶州刺史','朱友谦是朱建徽的父亲；不因称建徽与令德令锡不同而并为同一子。')
claim('event',E,'description','旧本纪同记密诏令史彦琼杀朱友谦子、澶州刺史建徽。',11,'先是，有密詔令史彥瓊殺朱友謙之子澶州刺史建徽。','记命令先是，无另补精确执行日。',source='jiuwudaishi-034-925-yedu-command',relation='corroborates')
E=ev('shiyanqiong_night_departure_and_regicide_rumor','史彦琼夜半出城去向未告，民间又传刘后因继岌死而弑帝',11,'门者白留守','人情愈骇。',[('史彦琼','夜出者'),('正言','门者报告接收者')],when='926年二月贝州乱前',place='鄴都',note='传闻明确标讹言，刘后及帝未因虚假死亡作为死者演员；史夜出为门者报告，不无据确定其彼时实际去澶州。')
E=ev('huangfuhui_gambling_revolt_coerces_yang','皇甫晖赌败后乘军心不安作乱，胁迫杨仁晸率兵归乡',11,'杨仁晸部兵','吾魏军力也；',[('皇甫晖','魏博部兵、起乱胁迫者'),('杨仁晸','被劫迫者')],when='926年二月贝州兵变之夜',place='贝州',note='主段横跨两个阅读块，第一引文到吾魏军力也；后一段威胁说辞另引原块，不拼造快照。')
claim('event',E,'description','皇甫晖续称长期戍守、代归不得见家属，并以弑逆传闻与可拒朝廷劝杨归。',11,span(11,'魏军甲不去体','富贵之资乎？”'),'此段为皇甫说辞，弑逆非真、富贵是设想，不作实绩；续句来自第二阅读块。')
E=ev('huangfuhui_kills_yang_and_officer','杨仁晸与另一未名小校拒从，被皇甫晖杀害',11,'仁晸不从','又杀之。',[('杨仁晸','拒从被杀者'),('皇甫晖','杀拒从者')],when='926年二月贝州兵变之夜',place='贝州',note='小校未名，不虚构实体名；主称晖杀，旧史记军人杀为统率与群体叙法差异。')
claim('event',E,'description','旧本纪记军人斩杨仁晸，印证拒从遇害。',11,'軍人即斬仁晸。','执行群体旧写军人，主具晖，不据差异另造第二次死。',source='jiuwudaishi-034-925-yedu-command',relation='corroborates')
E=ev('zhaozaili_coerced_beizhou_plunder','皇甫晖追及逃走的赵在礼，以两首威胁，使其为帅并焚掠贝州',11,'效节指挥使','涿州人也。',[('皇甫晖','胁迫拥帅者、魏州人'),('赵在礼','被胁为帅者、效节指挥使、涿州人')],when='926年二月贝州兵变之夜',place='贝州',note='被胁与后续主动控制区分，未把在礼列为本次最初发起者。')
claim('event',E,'description','旧本纪同记在礼逃跑，被乱兵追及逼为帅，中夜焚掠。',11,'在禮懼，即曰：「吾能為之。」眾遂呼噪，中夜燔劫貝郡。','同被迫过程，未建立此前二人同谋。',source='jiuwudaishi-034-925-yedu-command',relation='corroborates')
E=ev('beizhou_rebels_march_south','乱兵拥赵在礼南行，经临清、永济、馆陶剽掠',11,'诘旦','所过剽掠。',[('皇甫晖','拥行者'),('赵在礼','被奉帅者')],when='926年二月贝州乱次晨',place='临清、永济、馆陶',note='逐地名字保留，不无据补现代点或路线坐标。')
E=ev('sunduo_proposes_defense_rejected','孙铎请发甲守城并募千兵王莽河逆击，史彦琼疑其异志拒绝',11,'壬辰晚','何必逆战！”',[('孙铎','都巡检使、请预防伏击者'),('史彦琼','拒提议者')],when='926年二月壬辰晚',place='鄴都、拟伏王莽河',note='千人伏击是建议，未录已实际部署或打败叛军；史预计六日晚到不是叛兵实际行程。')
E=ev('shiyanqiong_flees_yedu_gate','乱兵夜攻鄴都北门，史彦琼所部溃散，史单骑逃洛阳',11,'是夜，贼前锋',None,[('史彦琼','北门守军统率、逃往洛阳者')],when='926年二月壬辰夜',place='鄴都北门至洛阳',note='奔洛阳未认已经当天抵京；实际到洛后段另记。')
E=ev('zhaozaili_occupies_yedu','乱兵入鄴都，孙铎拒战失利逃走，赵在礼据宫城并任皇甫晖、赵进、纵兵掠',12,'癸巳',None,[('孙铎','拒战失利逃走者'),('赵在礼','据宫任将者'),('皇甫晖','被署马步都指挥使者'),('赵进','军校、被署马步都指挥使、定州人')],when='926年二月癸巳',place='鄴都宫城',note='任将主书马步都指挥使，旧书都虞候斩斫使为异说，不改主；新本纪癸巳反贝州、甲午陷鄴都与主癸巳入鄴不同，分别保留。')
claim('event',E,'description','旧本纪同记次晨入城、孙铎巷战逃、傍晚赵据宫城，署皇甫晖等都虞候、斩斫使。',12,'晡晚，趙在禮引諸軍據宮城，署皇甫暉等為都虞候、斬斫使，諸軍大掠。','官名与主书马步都指挥使不同，并列待纸本。',source='jiuwudaishi-034-925-yedu-command',relation='conflicts')
claim('event',E,'description','新本纪癸巳记在礼反贝州、甲午条后记陷鄴都，与主书癸巳入城日期叙法不同。',12,'甲午，畋于冷泉。趙在禮陷鄴都，武寧軍節度使李紹榮討之。','甲午为相邻日期叙次，未自行解释成确定不含省日；保留异说，本批不提前生成主书后段讨伐。',source='xinwudaishi-005-926-annals',relation='conflicts')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续1—12段原文逐字回查；主书与新旧五代史分立引证。郭朱谋反、刘后弑帝均依原文告言/谮/讹言记录，未作事实关系。李继拆字严复用李继曮，李严另一人；张拆字厉据旧张砺传校名，吏武据两史校史武，成都李嗣源据成德职核，原文不改。后教、先拒后从、李环杀郭、李崧杀后矫敕分阶段；郭成都二子与洛阳三子分录。朱徙镇围杀、对二子诛令、河中家属实际就刑区别；史武七将补名保留文本。梅老鞋里断名未决不造实体；乐人数、李存乂幽/杀日、鄴入城叙日和皇甫官名异说并列。追叙伐蜀925、伶宦拒索及营护未知年不强926。展示简体，来源保持原字。'
for n in range(1,13): ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,13)],next_paragraph=Q[13]['id'],next_volume=274,supplements=supplements,excluded_non_body=[],coverage='卷274第1—12段，原文件38—49行，926正月至二月鄴都陷落；原段11被阅读块拆开，分别逐字引用。926全110正文段本批处理12段，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,13)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
