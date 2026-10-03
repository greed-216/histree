# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 925, paragraphs 32–31."""
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
 ('tongjian-273-925-shu-campaign',YEAR/'part-03/sources/library/tongjian-273-925-shu-campaign','0ae3ec4a','司马光等'),
 ('tongjian-273-925-volume-end',P/'sources/library/tongjian-273-925-volume-end','c80261f8','司马光等'),
 ('xinwudaishi-063-925-east-tour',YEAR/'part-03/sources/library/xinwudaishi-063-925-east-tour','0ae3ec4a','欧阳修'),
 ('xinwudaishi-005-925-annals',YEAR/'part-01/sources/library/xinwudaishi-005-925-annals','7c2351be','欧阳修'),
 ('jiuwudaishi-033-925-october-campaign',P/'sources/library/jiuwudaishi-033-925-october-campaign','c80261f8','薛居正等'),
 ('jiuwudaishi-051-jiji-conquest',P/'sources/library/jiuwudaishi-051-jiji-conquest','c80261f8','薛居正等'),
 ('jiuwudaishi-057-chongtao-conquest',P/'sources/library/jiuwudaishi-057-chongtao-conquest','c80261f8','薛居正等'),
 ('jiuwudaishi-061-anchongba-retreat',P/'sources/library/jiuwudaishi-061-anchongba-retreat','c80261f8','薛居正等'),
 ('xinwudaishi-014-jiji-conquest',P/'sources/library/xinwudaishi-014-jiji-conquest','c80261f8','欧阳修'),
 ('xinwudaishi-044-yanxiao-conquest',P/'sources/library/xinwudaishi-044-yanxiao-conquest','c80261f8','欧阳修'),
 ('xinwudaishi-046-anchongba-departure',P/'sources/library/xinwudaishi-046-anchongba-departure','c80261f8','欧阳修'),
 ('xinwudaishi-046-anchongba-surrender',P/'sources/library/xinwudaishi-046-anchongba-surrender','c80261f8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0925-p032-p037',
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
for n in range(32, 38):
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
people, used, reused, supplements = {}, {}, {'tongjian-273-925-shu-campaign','xinwudaishi-063-925-east-tour','xinwudaishi-005-925-annals'}, []

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
    ck = f'claim_zztj_273_0925_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
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
                   description=f'《资治通鉴》卷273同光三年条所见人物：{name}。',
                   biography=None, status='draft')
    if name not in registry:
        row['aliases']={'唐景思':[],'周彦禋':['周彥禋'],'王承捷':[],'王宗勋':['王宗勳'],'程奉琏':['程奉璉'],'王承鉴':['王承鑒'],'王承朴':['王承樸'],'王承肇':[],'王宗威':[],'王承岳':['王承嶽'],'王宗汭':[],'高从诲':['高從誨']}.get(name,row['aliases'])
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
E=ev('shu_ruler_dep_chengdu','王宗衍率兵数万离成都',32,'癸亥','发成都，',[('蜀主','率兵出行者')],when='925年十月癸亥',place='成都',note='数万按史载概数，出行尚非抵秦州。')
E=ev('shu_ruler_arr_hanzhou','王宗衍至汉州',32,'甲子','至汉州。',[('蜀主','到达者')],when='925年十月甲子',place='汉州')
E=ev('shu_ruler_dismisses_warning','王承捷告唐兵西上，王宗衍怀疑群臣阻游而不信，继续东行',32,'武兴',None,[('王承捷','武兴节度使、告警者'),('蜀主','不信告警、东行赋诗者')],when='925年十月东游途中，确日未载',place='汉州以东途中',note='群臣同谋是蜀主猜疑，不是已证实共谋；耀武是君主的话。')
E=ev('weiwu_city_surrender','康延孝攻威武城，唐景思率兵及城使周彦禋等降',33,'丁丑','亦降。',[('李绍琛','攻城者'),('唐景思','蜀指挥使、率兵降者'),('周彦禋','城使、降者')],when='925年十月丁丑',place='威武城',note='周彦禋等其余人无名不造实体；康延孝复用李绍琛赐名前主体。')
claim('person',people['唐景思'],'description','主书记唐景思为秦州人。',33,'景思，秦州人也。','秦州籍贯不填现代精确出生点。')
claim('event',E,'description','旧史郭传记故镇屯驻指挥使唐景思以城降，得兵四千。',33,'次至故鎮，偽命屯駐指揮使唐景思亦以城降，得兵四千。','主书威武城与旧史故镇各保留原地名，未另有地理证据前不强认全同；四千是该降兵记数。',source='jiuwudaishi-057-chongtao-conquest',relation='adds')
E=ev('weiwu_grain_release_and_fengzhou_advance','唐军得威武粮二十万斛，康延孝放败兵万余后倍道往凤州，李严致书王承捷',33,'得城中粮','以谕王承捷。',[('李绍琛','放败兵、进军者'),('李严','致书招谕者'),('王承捷','受招谕者')],when='925年十月丁丑克威武后',place='威武城至凤州',note='万余败兵放走与已降兵统计不同，不相加推总俘虏数。')
E=ev('fengxiang_supplies_exhausted','李继曮竭凤翔蓄积馈军仍不足，人情忧恐',33,'李继','人情忧恐。',[('李继\ue4be严','凤翔供军者')],when='925年十月进军期间，确日未载',place='凤翔、伐蜀行营',note='私用缺字沿此前校核为李继曮，不能并客省使李严；忧恐为主书概述。')
E=ev('chongtao_sanguan_fengzhou_plan','郭崇韬入散关，提出先取凤州粮以济将竭馈运',33,'郭崇韬入','因其粮。”',[('崇韬','入关、提出取粮计划者')],when='925年十月威武后凤州降前叙次，确日未载',place='散关、拟取凤州',note='进无成功不复得还是激励语，不能造已经封死退路事件。')
claim('event',E,'description','旧史郭传记十月十九日入大散关。',33,'軍發，十月十九日入大散關，','补该传纪日，主书段落叙次与本纪戊寅入关分别保留，不强并为同一日。',source='jiuwudaishi-057-chongtao-conquest',relation='adds')
claim('event',E,'description','旧史郭传记凤翔转运只支旬日，郭主张取凤州储积。',33,'今岐下飛挽，才支旬日，必須先取鳳州，收其儲積，方濟吾事。','是郭对补给的说法，不据此计算全军真实每天消耗。',source='jiuwudaishi-057-chongtao-conquest',relation='corroborates')
E=ev('liyu_fast_advance_advice','诸将欲按兵，郭问李愚；李愚主张乘蜀人离心快速进军',33,'诸将','兵势不可缓也。”',[('崇韬','问策者'),('李愚','主张速进者')],when='925年十月进散关阶段，确日未载',place='伐蜀行营',note='蜀人苦君及破胆是李愚判断，不当全体蜀人统一态度；诸将未名不臆定具名反对者。')
E=ev('yanxiao_report_fast_march','康延孝奏报，郭崇韬称李愚料敌得当并倍道推进',33,'是日','乃倍道而进。',[('李绍琛','奏报者'),('崇韬','称许、加速者'),('李愚','受称许者')],when='925年十月入散关问策之日，未独立纪干支',place='伐蜀行营',note='底本告秉疑字，不擅改告捷；依后接喜、料敌及推进仅录奏报，不补未明报文；是日承本段问策，不能独立锁定丁丑。')
E=ev('chengjie_four_prefectures_surrender','王承捷以凤兴文扶四州印节降，唐得兵八千粮四十万斛',33,'戊寅','粮四十万斛。',[('王承捷','四州降者'),('崇韬','招讨受降方')],when='925年十月戊寅',place='凤州、兴州、文州、扶州',note='主书此处四州印节降与之后兴州守将再降、弃城并存，不能推四州各城此前均已驻唐军。')
claim('event',E,'description','旧史郭传记王承捷以城降，兵八千军储四十万。',33,'承捷果以城降，得兵八千，軍儲四十萬。','同数印证，但旧史未在此句写斛单位，保留主书单位。',source='jiuwudaishi-057-chongtao-conquest',relation='corroborates')
claim('event',E,'description','旧史本纪合记王承捷与唐景思次第降，共兵一万二千、军储四十万。',33,'偽命鳳州節度使王承捷、故鎮屯駐指揮使唐景思次第迎降，得兵一萬二千、軍儲四十萬。','一万二千为合记，不能替换王承捷一人八千；与列传八千加四千计法相应但不外推独立确证。',source='jiuwudaishi-033-925-october-campaign',relation='adds')
E=ev('chengjie_acting_wuxing','郭崇韬以都统牒令王承捷摄武兴节度使',33,'崇韬曰：“平蜀','摄武兴节度使。',[('崇韬','下牒任命者'),('王承捷','摄任节度使者')],when='925年十月戊寅降后',place='武兴军',note='平蜀必矣是郭信心评价，蜀国尚未正式灭亡；摄为代理，不替换朝廷最终任命。')
E=ev('shu_ruler_arr_lizhou_believes_warning','王宗衍到利州，见威武败卒才信唐兵来',33,'己卯','始信唐兵之来。',[('蜀主','到达、改变判断者')],when='925年十月己卯',place='利州')
E=ev('lizhou_defense_advice_accepted','王宗弼宋光嗣劝扼利州，王宗衍从之',33,'王宗弼','从之。',[('王宗弼','建议者'),('光嗣','建议者'),('蜀主','采纳者')],when='925年十月己卯到利州后',place='利州',note='东川山南兵力尚完及唐不敢深入为建议者判断，不当战争已获胜。')
claim('event',E,'description','旧史本纪记王宗衍兵五万屯利州。',33,'時王衍將幸秦州，以其軍五萬屯於利州。','主书未在到利州句定人数，按旧史另存，不能与出成都数万或逆战三万混成同数。',source='jiuwudaishi-033-925-october-campaign',relation='adds')
claim('event',E,'description','新史继岌传记王宗衍兵万人屯利州。',33,'王衍將兵萬人屯利州，','与旧史五万不同，分别保留；不取平均或自行择一个人数。',source='xinwudaishi-014-jiji-conquest',relation='conflicts')
E=ev('shu_three_commanders_counterattack','蜀任王宗勋王宗俨王宗昱为三招讨，率兵三万迎战',33,'庚辰','将兵三万逆战。',[('蜀主','任命者'),('王宗勋','随驾清道指挥使、招讨'),('王宗俨','随驾清道指挥使、招讨'),('王宗昱','兼侍中、招讨')],when='925年十月庚辰',place='利州至迎战方向',note='三万人是出战队伍，不再加到驻利州军得总兵力。')
claim('event',E,'description','新史蜀世家亦记王宗勋宗俨宗昱率兵拒唐。',33,'遣王宗勳、宗儼、宗昱率兵以拒唐師。','同人任务印证；未给数不填主书兵数为新史原数。',source='xinwudaishi-063-925-east-tour',relation='corroborates')
E=ev('shu_army_pay_grievance','蜀从驾兵绵汉至深渡，抱怨龙武军粮赐倍于他军',33,'从驾兵','它军安能御敌！”',[],when='925年十月三招讨出战叙次，确日未载',place='绵州、汉州至深渡',note='怨语体现主书所叙军情，不造所有士卒参与的具体叛乱事件。')
E=ev('cheng_fenglian_surrender_bridge_work','程奉琏率五百兵降，请先修桥栈供唐军通行',33,'李绍琛等过','无险阻之虞。',[('李绍琛','率唐军通过者'),('程奉琏','兴州都指挥使、降及请修桥者')],when='925年十月，辛巳克兴州以前',place='长举至兴州桥栈',note='主书五百兵未定骑种，请先治桥栈与作者无险阻描述区别。')
claim('event',E,'description','新史继岌传记程奉琏以五百骑降，用其兵修阁道以过唐军。',33,'至興州，蜀將程奉璉以五百騎降，因以其兵修閣道，以過唐軍。','补骑种与实际修道叙述，主书长举途中、新史至兴州地名范围分别保留。',source='xinwudaishi-014-jiji-conquest',relation='adds')
E=ev('xingzhou_capture_chengjian_flight','王承鉴弃兴州，康延孝等克城',33,'辛巳','克兴州，',[('王承鉴','兴州刺史、弃城者'),('李绍琛','克城者')],when='925年十月辛巳',place='兴州')
claim('event',E,'time_original','旧史继岌传将康延孝收兴州放在甲申至故镇叙次。',33,'甲申，至故鎮，康延孝收興州。','与主书辛巳不同，可能行程/战报编次差异，保留待核。',source='jiuwudaishi-051-jiji-conquest',relation='conflicts')
E=ev('jing_si_acting_xingzhou','郭崇韬令唐景思摄兴州刺史',33,'郭崇韬以唐', '摄兴州刺史。',[('崇韬','任命者'),('唐景思','摄任刺史者')],when='925年十月辛巳克兴州后',place='兴州',note='摄任非此前蜀指挥使职位的简单更名。')
E=ev('chengzhou_chengpu_flight','成州刺史王承朴弃城逃走',33,'乙酉','弃城走。',[('王承朴','弃城刺史')],when='925年十月乙酉',place='成州')
claim('event',E,'time_original','旧史本纪将王承鉴、王承朴两人弃城同记辛巳。',33,'辛巳，偽興州刺史王承鑒、成州刺史王承樸棄城遁去，','主书成州乙酉、兴州辛巳分日，旧史合日保留，不擅挪主书日期。',source='jiuwudaishi-033-925-october-campaign',relation='conflicts')
E=ev('sanquan_battle','康延孝等在三泉击败蜀三招讨，史载斩首五千级',33,'李绍琛等与','馀众溃走。',[('李绍琛','唐方作战将领'),('王宗勋','蜀招讨'),('王宗俨','蜀招讨'),('王宗昱','蜀招讨')],when='925年十月乙酉本段叙次，战日未另载',place='三泉',note='主书战接成州乙酉句，不强定另明书同日；五千级为史载战果非现代伤亡核验。')
claim('event',E,'description','旧史本纪记康延孝与李严以三千劲骑击蜀三万步骑，斩首五千。',33,'聞我師至，遣步騎三萬逆戰於三泉，延孝與李嚴以勁騎三千擊之，蜀軍大敗，斬首五千級，餘眾奔潰。','补李严和战术兵种数；与主书同五千，但不同总兵数书证不可混用。',source='jiuwudaishi-033-925-october-campaign',relation='adds')
claim('event',E,'time_original','旧史本纪三泉胜战承辛巳叙次。',33,'康延孝大破蜀軍於三泉。','原句紧接辛巳弃城，不强等作已证明精确战日；主书乙酉后叙次不同。',source='jiuwudaishi-033-925-october-campaign',relation='conflicts')
claim('event',E,'description','新史蜀世家记三招讨至三泉望风退走。',33,'宗勳等至三泉，望風退走。','与主书实战大败叙述不同，保留叙法，不改主书为未发生战斗。',source='xinwudaishi-063-925-east-tour',relation='conflicts')
claim('event',E,'description','新史康传同记康延孝与王宗衍方战三泉，蜀败走。',33,'與王衍戰三泉，衍敗走，','王衍代表蜀方，未据传概称推定其亲自持兵临三泉阵；上下文主书君主仍在利州。',source='xinwudaishi-044-yanxiao-conquest',relation='corroborates')
E=ev('sanquan_grain_capture','唐军在三泉得粮十五万斛，军食由此充足',33,'又得粮',None,[('李绍琛','唐方取粮将领')],when='925年十月三泉战后',place='三泉',note='主书十五万斛；不与威武二十万、凤州四十万未核统计合成单个取粮点数。')
claim('event',E,'description','旧史本纪记下三泉得军储三十余万。',33,'又下三泉，得軍儲三十餘萬。','与主书十五万斛不同，旧句无单位；单独保存，不自行取倍数或判笔误。',source='jiuwudaishi-033-925-october-campaign',relation='conflicts')
E=ev('cao_dowager_burial_kunling','葬贞简太后于坤陵',34,'戊子',None,[('贞简太后','被葬后唐太后')],when='925年十月戊子',place='坤陵',note='复用李存勖母曹氏，与蜀徐太后不同；葬日不作死亡日期。')
claim('event',E,'time_original','旧史本纪同记戊子葬贞简太后于坤陵。',34,'戊子，葬貞簡太后於坤陵。','同日地印证。',source='jiuwudaishi-033-925-october-campaign',relation='corroborates')
claim('event',E,'time_original','新史本纪同十月戊子记葬贞简太后。',34,'戊子，葬貞簡太后於坤陵。','本纪同年十月句，注意不与七月壬寅死亡混淆。',source='xinwudaishi-005-925-annals',relation='corroborates')
E=ev('shu_ruler_retreat_cuts_jubai_bridge','王宗衍闻败离利州西逃，断桔柏津浮梁',35,'蜀主','断桔柏津浮梁；',[('蜀主','撤退、令断桥者')],when='925年十月三泉战败后，确日未载',place='利州、桔柏津',note='主书桔柏、旧史吉柏原地名异字保留，未核现代坐标。')
claim('event',E,'description','旧史本纪亦记王宗衍闻败奔成都并断吉柏津浮梁。',35,'王衍聞敗，自利州奔歸成都，斷吉柏津，浮梁而去。','补目的地，不等本句日期已经到成都；吉柏/桔柏保留。',source='jiuwudaishi-033-925-october-campaign',relation='corroborates')
E=ev('zongbi_lizhou_guard_execution_order','王宗衍令王宗弼守利州并杀三招讨',35,'使中书令','等三招讨。',[('蜀主','下令者'),('王宗弼','中书令、判六军诸卫事、受命守城者'),('王宗勋','拟斩招讨'),('王宗俨','拟斩招讨'),('王宗昱','拟斩招讨')],when='925年十月三泉败后，确日未载',place='利州',note='命杀不是三人已经被杀，卷末三人仍与宗弼相遇；避免生成错误死亡事实。')
claim('event',E,'description','新史蜀世家亦记令宗弼诛三招讨，宗弼反与其送款。',35,'衍詔宗弼誅宗勳等，宗弼反與宗勳等合謀，送款於唐師。','补命未执行结果，同人归款后续主书第37段另录。',source='xinwudaishi-063-925-east-tour',relation='corroborates')
E=ev('yanxiao_rushes_lizhou','康延孝昼夜兼行赶往利州',35,'李绍琛','趣利州。',[('李绍琛','加速进军者')],when='925年十月三泉败后，确日未载',place='三泉至利州',note='趣为趋往，不是此刻已到利州。')
E=ev('song_guangbao_conditional_offer','宋光葆致郭崇韬书，要求唐军不入境则举巡属附唐，否则背城决战；郭复书抚纳',35,'蜀武德','崇韬复书抚纳之。',[('宋光葆','武德留后、提出条件者'),('崇韬','复书受纳者')],when='925年十月，己丑归降前',place='东川、唐行营',note='条件威胁不是已决战；郭复书抚纳不等所有具体条件随后绝对遵守。')
E=ev('jiji_arr_xingzhou','李继岌至兴州',35,'己丑','至兴州，',[('继岌','到达都统')],when='925年十月己丑',place='兴州')
claim('event',E,'time_original','旧史本纪同己丑记魏王继岌至兴州。',35,'己丑，魏王繼岌至興州，','同日行程印证。',source='jiuwudaishi-033-925-october-campaign',relation='corroborates')
E=ev('song_guangbao_five_prefectures_surrender','宋光葆以梓绵剑龙普五州降唐',35,'光葆以','龙、普五州，',[('宋光葆','五州降者'),('继岌','唐方都统')],when='925年十月己丑叙次',place='梓州、绵州、剑州、龙州、普州',note='皆降在本段后文统摄各句，摘录联合保留；不把宋所部与王宗威所部重复合并。')
claim('event',E,'description','本段各辖州句后总记皆降。',35,'阶州刺史王承岳以阶州，皆降。','皆降统摄前列宋光葆及各帅，非仅阶州。')
claim('event',E,'description','旧史继岌传宋光葆降地写梓潼剑龙普，主书和旧本纪写梓绵剑龙普。',35,'偽蜀東川節度使宋光葆以梓、潼、劍、龍、普等州來降；','潼/绵不同原字分别保存，不偷偷统一州名。',source='jiuwudaishi-051-jiji-conquest',relation='conflicts')
E=ev('chengzhao_three_prefectures_surrender','王承肇以洋蓬壁三州降唐',35,'武定节度使','壁三州，',[('王承肇','武定节度使、三州降者')],when='925年十月己丑叙次',place='洋州、蓬州、壁州',note='本段皆降统摄此句，主书壁字保留，未核改璧。')
claim('event',E,'description','旧史本纪记王承肇降地为达蓬璧三州。',35,'武定軍使王承肇以達、蓬、璧三州來降；','达/洋与璧/壁差异保留，不能把两组独立累计为更多州。',source='jiuwudaishi-033-925-october-campaign',relation='conflicts')
claim('event',E,'description','旧史继岌传记王承肇以洋蓬壁三州符印降。',35,'武定軍節度使王承肇以洋、蓬、壁三州符印降；','列传与主书相应，同书本纪不同，不把列传视为完全独立证据。',source='jiuwudaishi-051-jiji-conquest',relation='corroborates')
E=ev('zongwei_five_prefectures_surrender','王宗威以梁开通渠麟五州降唐',35,'山南节度使','麟五州，',[('王宗威','山南节度使、兼侍中、五州降者')],when='925年十月己丑叙次',place='梁州、开州、通州、渠州、麟州',note='主书麟字保留，不能按北方同名麟州安坐标；待地理文献校核。')
claim('event',E,'description','旧史本纪记兴元节度使王宗威以梁开通渠麟五州降。',35,'興元節度使王宗威以梁、開、通、渠、麟五州來降；','兴元与主书山南为所任军名表达，不新建第二同名帅。',source='jiuwudaishi-033-925-october-campaign',relation='corroborates')
E=ev('chengyue_jiezhou_surrender','王承岳以阶州降唐',35,'阶州刺史','皆降。',[('王承岳','阶州刺史、降者')],when='925年十月己丑叙次',place='阶州')
claim('event',E,'description','旧史本纪记阶州王承岳纳符印请命。',35,'階州刺史王承嶽納符印請命；','嶽简化岳，同主体，不新造王承嶽。',source='jiuwudaishi-033-925-october-campaign',relation='corroborates')
relationship('宗侃','承肇','父亲',35,'承肇，宗侃之子也。','王宗侃是王承肇父亲，方向具体；不因承字辈推定其他王氏将皆同家。')
E=ev('other_shu_towns_submit','史载其他城镇望风款附唐',35,'自馀城镇',None,[],when='925年十月上述归降叙次',place='蜀境其他未名城镇',note='概述不是逐城名单，未名城镇不补造。')
E=ev('anchongba_diverts_ambush_plan','王承休与安重霸议袭唐，安以剑门险及赴国难劝西归',36,'天雄','以为然。',[('王承休','天雄节度使、议袭及听劝者'),('重霸','副使、主张西归者')],when='925年十月唐兵入蜀后，确日未载',place='秦州、拟回蜀',note='蜀精兵十万及唐不能直度剑门是安的劝说，不当实际核定兵力；未发生伏击战。')
claim('event',E,'description','新史安传同记安重霸以剑门险、受国恩应赴难劝承休西归。',36,'然公受國恩，聞難不可不赴，願與公俱西。','同劝说印证，不证明安后来真正同行。',source='xinwudaishi-046-anchongba-departure',relation='corroborates')
E=ev('chengxiu_buys_route_departure_force','王承休采安建议赂羌买文扶州路，令安领龙武及募兵万二千随归',36,'重霸请','以从。',[('重霸','提买路及拟领兵者'),('王承休','同意、命领兵者')],when='925年十月回蜀准备，确日未载',place='秦州、文州扶州路',note='万人二千主书记数，不能与安口称蜀中十万累加；后续安辞行未随全路。')
claim('event',E,'description','旧史安传记承休拥龙武及招置兵近万人从行。',36,'承休擁龍武軍及招置僅萬人從行，令重霸權握部署，','近万人与主书万二千不同统计保留；该传开篇同光二年十月与伐蜀925纪年不合，原字待纸本；旧注王氏见闻家口及生还数不作本阶段新增主证。',source='jiuwudaishi-061-anchongba-retreat',relation='conflicts')
E=ev('anchongba_stays_qin_after_sendoff','承休上道后安重霸临马前称留守秦陇，承休无可奈何',36,'将行','无如之何，',[('王承休','被送行、接受安留守者'),('重霸','辞不同行、请留守者')],when='925年十月承休离秦州时',place='秦州城外',note='请为公留守是安说法，不能推另有蜀廷正式留守任命。')
claim('event',E,'description','新史安传同记承休上道后安称秦陇不可失、愿留守，承休无如之何。',36,'酒罷，承休上道，重霸立承休馬前，辭曰：「秦、隴不可失，願留為公守。」承休業已上道，無如之何。','与此前愿俱西形成实际反转，不据作者狡诈评语另建可验证阴谋关系。',source='xinwudaishi-046-anchongba-departure',relation='corroborates')
E=ev('chengxiu_retreat_maozhou_losses','王承休王宗汭由文扶南行，遭羌抄掠且士卒冻饿，至茂州仅余二千',36,'遂与','馀众二千而已。',[('王承休','归蜀将领'),('王宗汭','招讨副使、同行者')],when='925年十月叙次，抵达确日未载',place='文州、扶州至茂州',note='不毛是作者地貌概述，不认整片地区永无农业；二千余众非现代清点，不直接反算均已死亡的一万人数。')
E=ev('anchongba_qin_long_surrender','安重霸以秦陇降唐',36,'重霸遂',None,[('重霸','归降者')],when='主书925年十月叙次，确日未载',place='秦、陇',note='旧史闻明宗起河北才降、新史唐已破蜀才降，年阶段不同保留；不提前录明宗授团练官。')
claim('event',E,'description','旧史安传记闻明宗起河北才遣使以秦成等州降。',36,'承休既去，重霸在秦州，聞明宗起河北，即時遣使以秦、成等州來降。','与主书925叙次及秦陇范围不同，不能无说明移动主线到926。',source='jiuwudaishi-061-anchongba-retreat',relation='conflicts')
claim('event',E,'description','新史安传记唐军已破蜀，安以秦成阶三州降。',36,'唐軍已破蜀，重霸亦以秦、成、階三州降唐，','范围与主书秦陇不同；本段后接明宗授官留待后年，不混为本年即授。',source='xinwudaishi-046-anchongba-surrender',relation='conflicts')
E=ev('gaojichang_prior_fear_zhangwu','追叙高季昌欲取三峡而畏张武威名不进',37,'高季兴常','不敢进。',[('高季兴','欲取而未进者'),('张武','蜀峡路招讨使、威名所指者')],year=None,when='925年伐蜀前此前，确年未载',place='三峡',note='畏威名是主书所叙，不等此前已有交战。')
E=ev('gaoconghui_acting_command','高季昌出兵前命子高从诲权军府事',37,'至是','权军府事，',[('高季兴','委代理者'),('从诲','行军司马、权军府者')],when='925年十月乘唐兵势时，确日未载',place='荆南',note='权军府为出征期间代理，不提前记高从诲继任君主。')
relationship('高季兴','从诲','父亲',37,'使其子行军司马从诲权军府事，','高季昌是高从诲父亲；高季兴为既有更名同主体，不建逆向重复边。')
E=ev('gaojichang_naval_attack_shizhou','高季昌率水军上峡攻施州，张武以铁锁断江，荆南勇士斫锁',37,'自将水军','乘舟斫之。',[('高季兴','水军进攻者'),('张武','以铁锁阻江者')],when='925年十月伐蜀中，确日未载',place='峡江、施州方向',note='取施州是进攻目的，后文战败不能写成已克施州。')
E=ev('gaojichang_naval_defeat_escape','荆南船受风挂锁遭矢石损坏，高季昌轻舟逃去',37,'会风','轻舟遁去。',[('高季兴','败退者'),('张武','设锁守江方')],when='925年十月攻峡时，确日未载',place='峡江铁锁处',note='风大为叙述因素，不作天意；所毁战舰未给艘数不补。')
E=ev('xia_three_prefectures_surrender_unstated_subject','蜀方闻北路败后以夔忠万三州遣使向魏王降，主书此句省主语',37,'既而闻','诣魏王降。',[('继岌','魏王、受降对象')],when='925年十月北路陷败后，确日未载',place='夔州、忠州、万州',note='不能承最近高季昌而把已唐属的荆南主记成降唐者；语境似承张武蜀方但无直接补证，不建确定张武归降参与或三州归高的事实，待校本。')
E=ev('chongtao_letter_zongbi','郭崇韬致王宗弼等书陈利害',37,'郭崇韬遗','为陈利害；',[('崇韬','致书者'),('王宗弼','受书者')],when='925年十月康延孝未至利州前',place='唐行营、利州',note='未给书全文，不编造具体条件。')
E=ev('zongbi_abandons_lizhou','康延孝未到利州，王宗弼弃城引兵西归',37,'李绍琛未','引兵西归。',[('李绍琛','尚未到利州的唐将'),('王宗弼','弃城西归者')],when='925年十月，确日未载',place='利州向西',note='李绍琛身份仅作叙次参照，不认其在此与宗弼交战。')
E=ev('zongbi_three_commanders_submit_plan','三招讨在白芀追及王宗弼，宗弼出示杀令，双方哭泣后谋向唐送款',37,'王宗勋等',None,[('王宗弼','出示诏、合谋者'),('王宗勋','追及合谋者'),('王宗俨','三招讨、合谋者'),('王宗昱','三招讨、合谋者')],when='925年十月利州弃守后，确日未载',place='白芀（底本字待核）',note='白芀疑地名字误，原字保留不设坐标；宋光嗣令杀是宗弼归责话语，不作已确认宋独自下帝诏；谋送款不等成都已降。')
claim('event',E,'description','新史蜀世家亦记宗弼与三招讨合谋向唐送款。',37,'宗弼反與宗勳等合謀，送款於唐師。','同人共同归款印证；后杀宋及成都正式降等事件留待下一卷主线。',source='xinwudaishi-063-925-east-tour',relation='corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续32—37段；告秉、白芀疑字保留待校；兵粮分地点和统计对象，两史三泉数量日次分书，不累计为单一总数；蜀方斩将令未执行，三招讨仍活着谋款；摄任与正授分开；各地皆降总摄，洋/达、壁/璧、绵/潼、麟各原字不强改坐标；安归唐主925叙次旧926明宗起兵后、新蜀破后并列；三州降句省主语不错误归高；张武同名沿此前主体不混未来他人；高从诲代理非继位；宋光嗣下杀令为宗弼话，不作直接帝诏事实。'
for n in range(32,38):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
next_ledger=json.loads((YEAR.parent.parent/'vol-274/year-0925/paragraphs.json').read_text())
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=925,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(32,38)],next_paragraph=next_ledger[0]['id'],next_volume=274,supplements=supplements,coverage='卷273第32—37段，原文件115—120行；925年十月蜀出游、唐军攻城三泉取粮、曹太后葬、诸地降、承休撤退安归唐及荆南峡战、宗弼谋款。卷273正文已到末段；925年还须卷274全部30段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(32,38)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
