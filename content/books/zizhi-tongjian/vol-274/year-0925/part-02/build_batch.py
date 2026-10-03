# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 274, year 925, paragraphs 13–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 31))
OLD=ROOT/'content/books/zizhi-tongjian/vol-273/year-0925'
specs = [
 ('tongjian-274-925-aftermath',YEAR/'part-01/sources/library/tongjian-274-925-aftermath','7f618e05','司马光等'),
 ('tongjian-274-925-winter',P/'sources/library/tongjian-274-925-winter','44b6be0e','司马光等'),
 ('jiuwudaishi-033-925-winter-hunt',P/'sources/library/jiuwudaishi-033-925-winter-hunt','44b6be0e','薛居正等'),
 ('jiuwudaishi-033-925-famine',P/'sources/library/jiuwudaishi-033-925-famine','44b6be0e','薛居正等'),
 ('jiuwudaishi-034-925-yedu-command',P/'sources/library/jiuwudaishi-034-925-yedu-command','44b6be0e','薛居正等'),
 ('xinwudaishi-068-925-shenzhi-death',P/'sources/library/xinwudaishi-068-925-shenzhi-death','44b6be0e','欧阳修'),
 ('xinwudaishi-065-bailong-rename',P/'sources/library/xinwudaishi-065-bailong-rename','44b6be0e','欧阳修'),
 ('jiuwudaishi-033-925-entry',YEAR/'part-01/sources/library/jiuwudaishi-033-925-entry','7f618e05','薛居正等'),
 ('jiuwudaishi-057-chongtao-conquest',OLD/'part-04/sources/library/jiuwudaishi-057-chongtao-conquest','c80261f8','薛居正等'),
 ('xinwudaishi-024-925-gifts',YEAR/'part-01/sources/library/xinwudaishi-024-925-gifts','7f618e05','欧阳修'),
 ('xinwudaishi-005-925-annals',OLD/'part-01/sources/library/xinwudaishi-005-925-annals','7c2351be','欧阳修'),
 ('xinwudaishi-068-yanhan',OLD/'part-02/sources/library/xinwudaishi-068-yanhan','b76f75cc','欧阳修'),
 ('xinwudaishi-065-heci',OLD/'part-01/sources/library/xinwudaishi-065-heci','7c2351be','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0925-p013-p024',
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷274·同光三年（925）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_274_0925_02_{len(B["claims"])+1:04d}'
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
                   description=f'《资治通鉴》卷274同光三年条所见人物：{name}。',
                   biography=None, status='draft')
    if name not in registry:
        row['aliases']={'陈本':['陳本'],'柳邕':[],'史彦琼':['史彥瓊'],'郑旻':['鄭旻'],'郑昭淳':['鄭昭淳'],'增城公主':['增城县主','增城縣主'],'高允韬':['高允韜']}.get(name,row['aliases'])
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='925年本段；确日未载', note='', year=925, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_274_0925_' + code
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
        edge = 'participation_zztj_274_0925_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_274_0925_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quotes preserve the contiguous source paragraph.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('chongtao_promises_zongbi_office','追叙王宗弼赂求西川节度使，郭崇韬表面答应',13,'王宗弼之','崇韬阳许之。',[('王宗弼','求帅者'),('崇韬','表面答应者')],when='925年十一月宗弼自为留后之后追叙',place='成都、唐行营',note='此录郭的回应，行赂请任已见第8段；阳许为主书记法，不等唐帝正式授官。')
claim('event',E,'description','旧史郭传同记宗弼求蜀帅，郭崇韬许之。',13,'宗弼選王衍之妓妾珍玩以奉崇韜，求為蜀帥，崇韜許之。','许诺不等后唐诏授。',source='jiuwudaishi-057-chongtao-conquest',relation='corroborates')
E=ev('zongbi_petitions_chongtao_stay','王宗弼久未得官，率蜀人列状向李继岌请留郭崇韬镇蜀',13,'既而久','请留崇韬镇蜀。',[('王宗弼','率人请留者'),('继岌','受请者'),('崇韬','被请留镇者')],when='925年蜀平后、己巳前',place='成都',note='请留镇与实际委任分开。')
claim('event',E,'description','旧史郭传补王宗弼与郭廷诲谋让蜀人列状，请郭留蜀。',13,'又與崇韜子廷誨謀，令蜀人列狀見魏王，請奏崇韜為蜀帥。','补廷诲参与，主书未具此共同谋状细节；不立长期同盟。',source='jiuwudaishi-057-chongtao-conquest',relation='adds')
E=ev('congxi_warns_jiji_chongtao','李从袭等以郭父子专横、志难测劝李继岌防备',13,'从袭等因','王不可不为备。”',[('李从袭','劝防者'),('继岌','受劝者'),('崇韬','指控对象')],when='925年请郭留蜀后',place='成都',note='专横与志难测为从袭话，未认郭已有叛谋。')
E=ev('jiji_declines_chongtao_stay_mutual_doubt','李继岌以郭为朝廷元臣、自己不敢决定请留而令蜀人诣阙，双方互疑',13,'继岌谓','互相疑。',[('继岌','拒自决请留者'),('崇韬','回应对象及互疑者')],when='925年请留郭镇蜀后',place='成都',note='互疑是主书心理叙述，不将被疑等作叛变。')
claim('event',E,'description','新史郭传同记继岌疑郭、郭难自明。',13,'繼岌頗疑崇韜，崇韜無以自明，','与主书互疑叙法同一阶段；该传宗弼血亲称法另外待核。',source='xinwudaishi-024-925-gifts',relation='corroborates')
E=ev('songguangbao_accuses_zongbi_kill','宋光葆从梓州来，诉王宗弼诬杀宋光嗣等',13,'会宋光葆','诬杀宋光嗣等。',[('宋光葆','申诉者'),('王宗弼','被指诬杀者'),('宋光嗣','申诉涉及死者')],when='925年蜀平后、己巳前',place='梓州至成都',note='诬杀为宋申诉，未核其全部司法事实；宋光葆、光嗣不同人，不因同姓推血亲。')
E=ev('chongtao_requisition_zongbi_soldiers_fire','郭崇韬征王宗弼犒军钱数万缗，宗弼吝给，士卒怨怒夜纵火喧噪',13,'又，崇韬','纵火喧噪。',[('崇韬','征钱者'),('王宗弼','不肯足给者')],when='925年十二月己巳前，确夜未载',place='成都唐军',note='数万缗为原书概数，不用九国志编者注的数千万代替；纵火未具处所或损失，不外推全城焚毁。')
E=ev('zongbi_zongxun_zongwo_clan_execution','郭崇韬报李继岌后收王宗弼王宗勋王宗渥，数不忠罪族诛并没家产',13,'崇韬欲','籍没其家。',[('崇韬','白报及收诛者'),('继岌','受报都统'),('王宗弼','被族诛者'),('王宗勋','被族诛者'),('王宗渥','被族诛者')],when='925年十二月己巳',place='成都',note='以自明为主书动机说明；罪名与族诛记载保留，未断言指控已独立证实。蜀方之前未执行的斩将令不同此次族诛。')
claim('event',E,'description','新史郭传同记郭斩宗弼宗渥宗勋并没家财，蜀人大恐。',13,'因以事斬宗弼及其弟宗渥、宗勳，沒其家財。蜀人大恐。','三人名与主书对应；弟是该传亲属称法，未在本批确立血亲边。',source='xinwudaishi-024-925-gifts',relation='corroborates')
claim('event',E,'time_original','新史本纪将郭杀宗弼宗渥宗训族诛记在十一月归降叙次。',13,'郭崇韜殺王宗弼及其弟宗渥、宗訓，滅其族。','原文紧承十一月、下起十二月；与主书十二月己巳不同；宗训/宗勋字异不新造宗训实体，亦不无校核覆盖规范名。',source='xinwudaishi-005-925-annals',relation='conflicts')
E=ev('shu_people_eat_zongbi_flesh_report','史载蜀人争食王宗弼之肉',13,'蜀人争食',None,[('王宗弼','史载被食遗体者')],when='925年十二月己巳族诛之后',place='成都',note='保留史家所记暴行，不据“蜀人”概称外推所有蜀民参与。')
E=ev('wangshenzhi_death','闽王王审知卒',14,'辛未','王审知卒，',[('审知','去世闽王')],when='925年十二月辛未',place='闽',note='忠懿为史书追称，卒日不等后唐追谥颁日。')
claim('event',E,'description','新史同记王审知同光三年卒，年六十四，谥忠懿。',14,'審知同光三年卒，年六十四，謚日忠懿。','史载年龄保留不自行按虚岁反推准确出生年；謚日疑曰底本保留，不改摘录。',source='xinwudaishi-068-925-shenzhi-death',relation='corroborates')
claim('person',people['王审知'],'death_year','主书记王审知于925年十二月辛未去世。',14,'辛未，闽忠懿王审知卒，','作为卒年与日期出处，不改变既有其他时期事实。')
E=ev('yanhan_claims_weiwu_acting_successor','王延翰在父王审知卒后自称威武留后',14,'子延翰','自称威武留后。',[('延翰','自称留后者')],when='925年十二月辛未叙次',place='闽、威武军',note='自称不是唐诏正授，更不提前为926建国称王事件。')
relationship('审知','延翰','父亲',14,'闽忠懿王审知卒，子延翰自称威武留后。','王审知是王延翰父亲，沿用既有稳定关系。')
claim('person',people['王延翰'],'description','新史记王延翰字子逸，为王审知长子。',14,'延翰字子逸，審知長子也。','仅补字与长子身份；该传同光四年唐拜及十月称王留待926主线。',source='xinwudaishi-068-yanhan',relation='adds')
E=ev('chenben_siege_tingzhou','汀州民陈本聚众三万围汀州',14,'汀州民','围汀州，',[('陈本','聚众围城者')],when='925年十二月本段，确日未载',place='汀州',note='三万为史载概数；不强定辛未当天起事，未给结局不补胜败。')
E=ev('yanhan_sends_liuyong_against_chenben','王延翰遣柳邕等率二万兵讨陈本',14,'延翰遣',None,[('延翰','派军者'),('柳邕','右军都监、率军者'),('陈本','讨伐对象')],when='925年十二月陈本围汀州后',place='汀州方向',note='出讨非已平叛；两史检索未找到此事同段补证，主书直接引用保留。')
E=ev('chengxiu_zongrui_return_interrogation','王承休王宗汭抵成都，被李继岌追问不拒战不降及撤军损失',15,'癸酉','二千人。”',[('王承休','抵达受诘者'),('王宗汭','抵达受诘者'),('继岌','问讯者')],when='925年十二月癸酉',place='成都',note='畏神武、王师未入境及一万二千/二千为当事人答语；不将差值全作已核死亡数。')
E=ev('chengxiu_zongrui_sons_execution','李继岌以偿万人之死为由斩王承休王宗汭，并杀其子',15,'曰：“可以',None,[('继岌','命斩者'),('王承休','被斩者'),('王宗汭','被斩者')],when='925年十二月癸酉',place='成都',note='万人之死是继岌问讯结论；其子未具姓名和人数，不捏造子女实体，也不自动推其妻严氏已死。')
E=ev('mengzhixiang_xichuan_appointment_summon','后唐任孟知祥为西川节度使同平章事，并促召赴洛阳',16,'丙子','促召赴洛阳。',[('孟知祥','任命及受召者')],when='925年十二月丙子',place='后唐朝廷、西川',note='此次任命不等孟已到成都，抵洛在第20段，赴蜀为以后事件。')
claim('event',E,'description','旧史本纪同丙子授孟成都尹及剑南西川节度副大使知节度事等衔。',16,'丙子，以北京副留守、太原尹孟知祥為檢校太傅、同平章事、成都尹、劍南西川節度副大使、知節度事、西山八國雲南都招撫等使；','主书概称节度使，旧衔副大使知节度事分别保留。',source='jiuwudaishi-033-925-entry',relation='adds')
E=ev('duanhui_urges_zhangxian_northern_capital','李存勖议北都留守，段徊等因恶张宪、不欲其在朝而称北都非张不可',16,'帝议选','不为重也。”',[('帝','议选者'),('段徊','枢密承旨、荐张北都者'),('宪','被荐者')],when='925年十二月丙子叙次',place='后唐朝廷',note='恶张及不欲其在朝为主书叙法；荐言宰相才器不等实际任宰相。')
E=ev('zhangxian_taiyuan_northern_capital_transfer','张宪改任太原尹知北都留守事',16,'乃徙宪','知北都留守事。',[('宪','被调北都者')],when='925年十二月丙子叙次',place='太原、北都')
claim('event',E,'description','旧史本纪同记张宪由邺都副留守兴唐尹改太原尹、北京副留守知留守事。',16,'以鄴都副留守、興唐尹張憲檢校吏部尚書、太原尹，充北京副留守、知留守事。','北京/北都名称同任职表达，地点不是现代北京；不设现代城市坐标。',source='jiuwudaishi-033-925-entry',relation='corroborates')
E=ev('wangzhengyan_xingtang_yedu_appointment','王正言由户部尚书任兴唐尹知邺都留守事',16,'以户部','知鄴都留守事。',[('正言','受任者')],when='925年十二月丙子叙次',place='邺都、兴唐府')
claim('event',E,'description','旧史本纪同记王正言改兴唐尹充邺都副留守。',16,'以戶部尚書王正言為檢校吏部尚書、守興唐尹，充鄴都副留守；','副留守与主书知留守事原衔分别保留。',source='jiuwudaishi-033-925-entry',relation='corroborates')
E=ev('shiyanqiong_yedu_supervisor_dominates','李存勖任史彦琼为邺都监军，史掌魏博六州军旅金谷、陵忽将佐，王正言等谄事',16,'正言昏耄',None,[('帝','任命者'),('史彦琼','武德使、邺都监军'),('正言','受制留守')],when='925年十二月本段，确日未载',place='邺都、魏博六州',note='昏耄与谄事是史家评价；史为伶人得宠，不能据监军惯例自动分类为宦官。')
claim('event',E,'description','旧史926本纪追叙十二月王正言留守，史彦琼以伶官得幸并操府权。',16,'十二月，以戶部尚書王正言為興唐尹、知留守事。正言年耄風病，事多忽忘，比無經治之才。武德使史彥瓊者，以伶官得幸，帝待以腹心之任，都府之中，威福自我，正言以下，皆脅肩低首，曲事不暇。','与主书925十二月对应追叙；此快照后半926兵变及讹言留待主线，不据讹言记录继岌被郭杀或刘后弑帝。',source='jiuwudaishi-034-925-yedu-command',relation='corroborates')
E=ev('silver_lance_background_recruitment','追叙李存勖收魏州银枪效节都近八千人为亲军',17,'初','皆恿悍无敌。',[('帝','收亲军者')],year=None,when='925年前追叙；本句未具年，卷269对应收编在915年',place='魏州',stable_key='event_zztj_269_0915_jin_reforms_silver_spear_guard',note='复用卷269既有收编事件及915年，不另造925收编；本段近八千补不同计数，恿字疑勇保留不靠简化改字。')
E=ev('silver_lance_rewards_grievance_background','追叙银枪军夹河立功获灭梁赏诺，河南平后仍因恃功而怨望',17,'夹河之战','更成怨望。',[('帝','此前许赏者')],year=None,when='925年前夹河战至灭梁之后追叙，确时未载',place='夹河战场及后唐军中',note='已赏非一与继续怨望并列，不说灭梁后从未赏；此处无具名士卒，不捏造军团人物。')
E=ev('famine_transport_empty_luoyang_grain','925年大饥流亡、租赋不足、道路积水运输难，东都粮仓空竭',17,'是岁','无以给军士。',[],when='925年年度灾荒与军粮状况',place='后唐境、东都',note='主书是岁年度概述，不全强定十二月某日；空竭为当时军需描述。')
claim('event',E,'description','旧史同记两河水灾、流亡约十之四五，运输泥泞艰难而京师缺粮。',17,'是時，兩河大水，戶口流亡者十四五，都下供饋不充，軍士乏食，','十四五保留原字，说明旧史比例式叙法，不误读十四五户或精准人口普查。',source='jiuwudaishi-033-925-famine',relation='corroborates')
E=ev('kongqian_waits_transport_distributes','孔谦每日于上东门外等诸州漕运，到即给军',17,'租唐使','至者随以给之。',[('谦','等运、分军粮者')],when='925年灾荒军粮短缺时，确日未载',place='洛阳、上东门外',note='底本租唐使疑租庸使，旧史明确租庸使；人沿既有孔谦，原文不改字。')
claim('event',E,'description','旧史同记租庸使孔谦于上东门等漕运并随到给之。',17,'州郡飛挽，旋給京師，租庸使孔謙日於上東門外佇望其來，算而給之。','可核其租庸使称法，不能用自动繁简转换解释主书租唐字误。',source='jiuwudaishi-033-925-famine',relation='corroborates')
E=ev('soldiers_families_famine_and_foraging','军士乏食，有雇妻鬻子，老弱群采野蔬且有饿死者',17,'军士乏食','而帝游畋不息。',[('帝','仍游畋的君主')],when='925年军粮不足时',place='东都军士及近郊',note='有字表示所见个案，非所有军士均卖子；百十为群为概数；不同因果陈述保持来源层次。')
claim('event',E,'description','旧史同记军士鬻子去妻、老弱野采并倒毙道路。',17,'軍士乏食，乃有鬻子去妻，老弱采拾於野，殍踣於行路者。','去妻与主书雇妻各存，未推精确死亡数。',source='jiuwudaishi-033-925-famine',relation='corroborates')
E=ev('cunxu_hunts_baisha_with_court','李存勖猎白沙，皇后皇子后宫皆随',17,'己卯','后宫毕从。',[('帝','出猎者'),('后','随猎皇后')],when='925年十二月己卯',place='白沙')
claim('event',E,'time_original','旧史同己卯记以腊辰猎白沙，皇后皇子宫人皆随。',17,'己卯，以臘辰狩於白沙，皇后、皇子、宮人畢從。','同出猎日与随从。',source='jiuwudaishi-033-925-winter-hunt',relation='corroborates')
claim('event',E,'time_original','新史本纪同十二月己卯畋白沙。',17,'十二月己卯，畋于白沙。','同月日。',source='xinwudaishi-005-925-annals',relation='corroborates')
E=ev('cunxu_hunt_itinerary_yique_tanbo_kanjian','李存勖猎后依次宿伊阙潭泊龛涧，癸未还宫',17,'庚辰','癸未，还宫。',[('帝','行猎住宿返宫者')],when='925年十二月庚辰伊阙、辛巳潭泊、壬午龛涧、癸未还宫',place='伊阙、潭泊、龛涧、洛阳',note='按日次连录行程，未据地名猜现代坐标。')
claim('event',E,'time_original','旧史同记四日行次和还宫。',17,'庚辰，次伊闕。辛巳，次潭泊。壬午，次龕澗。癸未，還宮。','次与宿为两书用词，原文皆保留。',source='jiuwudaishi-033-925-winter-hunt',relation='corroborates')
E=ev('hunt_snow_freezing_and_supply_plunder','猎途中大雪有从行者僵仆，卫兵在饥困伊汝强索供饷并毁屋器为薪，县吏躲山谷',17,'时大雪','县吏皆窜匿山谷。',[('帝','猎行君主')],when='925年十二月白沙猎行期间',place='伊水、汝水之间及行猎道路',note='吏座疑吏士，展示用从行者避免静默改字；卫兵未具名，不归罪某已知将领。甚于寇盗为史家比较。')
claim('event',E,'description','旧史同记大雪苦寒吏士冻踣、卫兵毁器庐取薪及县吏避山谷。',17,'是時大雪苦寒，吏士有凍踣於路者。伊、汝之民，饑乏尤甚，衛兵所至，責其供餉，既不能給，因壞其什器，撤其廬舍而焚之，甚於剽劫。縣吏畏恐，竄避於山谷間。','同记，吏士可供主书吏座校核但不修改原始TXT。',source='jiuwudaishi-033-925-winter-hunt',relation='corroborates')
E=ev('han_white_dragon_report_era_and_name','史载汉宫白龙出现，刘岩改元白龙并更名龚',17,'有白龙',None,[('汉主岩','改元更名者')],when='925年本段年末叙次，确日未载',place='汉宫',note='白龙是史书记载的祥瑞报告，不作现代动物存在确证；刘龚为刘岩阶段名，不新建人。')
claim('event',E,'description','新史记乾亨九年白龙见南宫三清殿、改元白龙并更名龚。',17,'九年，白龍見南宮三清殿，改元曰白龍，又更名龔，以應龍見之祥。','补宫殿位置与年号九年；九年为上下文乾亨，未自动推后句龑更名亦当日。',source='xinwudaishi-065-bailong-rename',relation='adds')
claim('person',people['刘岩'],'aliases','本段记刘岩改名刘龚。',17,'汉主改元白龙，更名曰龚。','复用汉主刘岩，龔/龚为字形转换，不另建主体。')
E=ev('zhengmin_sends_zhengzhaochun_marriage_envoy','长和郑旻遣布燮郑昭淳向汉求婚',18,'长和骠信','求婚于汉，',[('郑旻','长和骠信、派使求婚者'),('郑昭淳','布燮、求婚使者')],when='主书925年末叙次，确日未载',place='长和至汉',note='主书以长和说明唐之南诏，保留政权历史称法，不将唐代南诏名直接作925不变国号。')
claim('event',E,'description','新史补郑昭淳使衔、自称皇亲母弟，送朱鬃白马求婚。',18,'是歲，雲南驃信鄭旻遣使致朱鬃白馬以求婚，使者自稱皇親母弟、清容布燮兼理、賜金錦袍虎綾紋攀金裝刀、封歸仁慶侯、食邑一千戶、持節鄭昭淳。','自称使衔与皇亲母弟保留话语属性，不推确定郑旻弟弟血缘；同传七年叙次与主书925不同。',source='xinwudaishi-065-heci',relation='adds')
claim('event',E,'time_original','新史将求婚置于七年唐庄宗入汴后的同段是岁叙次。',18,'七年，唐莊宗入汴，龑懼，遣宮苑使何詞入詢中國虛實，','相应快照后文是岁郑旻求婚，七年即该传乾亨七年，923叙次；与主书925分年保留，不改主线。',source='xinwudaishi-065-heci',relation='conflicts')
E=ev('zengcheng_princess_marriage_zhengmin','汉主将增城公主嫁给长和郑旻',18,'汉主以女','妻之。',[('汉主岩','安排婚配汉主'),('增城公主','被嫁公主'),('郑旻','长和求婚君主')],when='主书925年末叙次，确日未载',place='汉、长和',note='主书妻之省对象，以同段派使求婚语境及新史妻旻定婚配郑旻，不误配郑昭淳；以女不据此单独立刘岩亲女关系。')
claim('event',E,'description','新史明确以刘隐之女增城县主妻郑旻。',18,'遂以隱女增城縣主妻旻。','主书增城公主、新史县主爵称各存；隱指该传前述刘隐，父系与主书汉主以女的可能理解不同，未新建确定父亲边。',source='xinwudaishi-065-heci',relation='conflicts')
relationship('增城公主','郑旻','妻子',18,'遂以隱女增城縣主妻旻。','婚配对象由新史明确妻旻，关系增城公主是郑旻妻子；对应主书925段但婚期两书不同，无确年新填。',source='xinwudaishi-065-heci')
E=ev('lisiyuan_visits_court_year_end','成德节度使李嗣源入朝',19,'成德',None,[('嗣源','入朝节度使')],when='925年十二月叙次，确日未载',place='后唐朝廷',note='主书未具来路与接见内容，不补。')
E=ev('mengzhixiang_arrives_luoyang_welcomed','孟知祥抵洛阳，李存勖宠待甚厚',20,'闰月',None,[('孟知祥','到达者'),('帝','宠待者')],when='925年闰月己丑朔',place='洛阳',note='主书未明闰几月，不自行公历换算；与12月任西川分开。')
E=ev('cunxu_consults_grain_funds_court','李存勖因军储不足问群臣，豆卢革以下无计',21,'帝以军储','皆莫知为计。',[('帝','问计者'),('革','宰相、无计者')],when='925年闰月叙次，确日未载',place='后唐朝廷',note='无计为主书叙法，不代表群臣此前从未上疏。')
claim('event',E,'description','旧史补段徊建议朱书访宰臣，帝命学士草词；宰相以蜀宝可给军、水旱常道回应。',21,'樞密承旨段徊奏曰：「臣見本朝時或遇歲時災歉，國費不足，天子將求經濟之要，則內出朱書御劄，以訪宰臣，請陛下依此故事行之。」即命學士草詞，帝親劄以訪宰臣，非帝憂民之實也。時宰相豆盧革等依阿徇旨，竟無所陳，但云：「陛下威德冠天下，今西蜀平定，珍寶甚多，可以給軍。水旱作沴，天之常道，不足以貽聖憂。」','非真忧民为旧史评价，未独立证明帝内心；宰相回应为其言，不当已落实给军。',source='jiuwudaishi-033-925-famine',relation='adds')
E=ev('liqi_petitions_tax_conversion_relief','李琪上疏主张量入为出、农兵相依，提出免折纳纽配以稍宽农负',21,'吏部尚书','农亦可以小休矣。”',[('李琪','吏部尚书、上疏者')],when='925年闰月军储不足问计后',place='后唐朝廷',note='李琪政策主张非现代已验证因果；不是建议完全免征一切租税。')
claim('event',E,'description','旧史同记李琪引古田租和权宜救弊上疏，帝诏嘉奖。',21,'唯吏部尚書李琪引古田租之法，從權救弊之道，上疏言之，帝優詔以獎之。','补诏嘉奖；未据此认政策已经成功实施。',source='jiuwudaishi-033-925-famine',relation='corroborates')
E=ev('tax_reform_order_not_implemented','李存勖敕按李琪建议办理，主书记最终未能施行',21,'帝即敕',None,[('帝','下敕者'),('李琪','方案提出者')],when='925年闰月该疏后',place='后唐财政',note='敕与实际落实分开，不将发布命令当改革成功。')
E=ev('shu_officials_downgrade_release_reward_edict','后唐诏蜀官四品以上分等降授、五品以下无才地者归田，先降有功者由郭奖任',22,'丁酉','随事奖任。',[('崇韬','受委奖任者')],when='925年闰月丁酉',place='后唐朝廷、蜀',note='五品以下不是一概罢官，限制条件才地无取；未具个别任命名单，不造授官人名。')
E=ev('cunxu_promises_wangzongyan_safe_enfeoffment','李存勖诏王宗衍承诺袭土而封并不乘险薄待',22,'又赐',None,[('帝','发诏承诺者'),('蜀主','受诏者')],when='925年闰月丁酉叙次',place='后唐朝廷至蜀',note='承诺记为当时诏书，不推后来兑现，更不提前省略926被杀事实。')
E=ev('gaowanxing_death','彰武保大节度使高万兴卒',23,'庚子','高万兴卒，',[('高万兴','去世节度使')],when='925年闰月庚子',place='彰武、保大辖地',note='兼史书令疑中书令，原字保留待核；未具卒地不设具体城址。')
claim('person',people['高万兴'],'death_year','本段记高万兴925年闰月庚子卒。',23,'庚子，彰武、保大节度使兼史书令高万兴卒，','卒年由主线年条，官名疑字不影响人物既有身份。')
E=ev('gaoyuntao_zhangwu_acting_command','高万兴之子高允韬由保大留后任彰武留后',23,'以其子',None,[('高允韬','原保大留后、任彰武留后者')],when='925年闰月庚子叙次',place='彰武',note='留后非节度使正授，不提前用926延州节度使官衔。')
relationship('高万兴','高允韬','父亲',23,'高万兴卒，以其子保大留后允韬为彰武留后。','高万兴是高允韬父亲；允韬承其子，繁体允韜同人。')
E=ev('cunxu_proposes_bianzhou_for_grain','李存勖因军储不足想去汴州',24,'帝以军储','欲如汴州，',[('帝','拟赴汴者')],when='925年闰月叙次，确日未载',place='后唐朝廷、拟汴州',note='欲如非已到汴，不能将其后926东行混入。')
claim('event',E,'description','旧史补李绍宏建议魏王回军后兵额多、运输难给时暂幸汴便漕运。',24,'中官李紹宏奏曰：「俟魏王旋軍之後，若兵額漸多，饋挽難給，請且幸汴州，以便漕挽。」','补建议者与条件，不认魏王此时已回；主书未具发议人。',source='jiuwudaishi-033-925-famine',relation='adds')
E=ev('remonstrators_stop_bianzhou_plan','谏官劝节俭足用、不向吴示虚实，李存勖停止赴汴计划',24,'谏官上言',None,[('帝','听谏止行者')],when='925年闰月欲赴汴之后',place='后唐朝廷',note='杨氏指吴政权；建议为谏官话，未知姓名不造人物，也不生成与吴实际交战。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续13—24段；王宗弼阳许求帅与正式诏任分开，蜀人留郭请状与从袭指控不能当郭确有反志；族诛主十二月己巳、新本纪十一月叙次并列，宗训/宗勋保留原字不另造；王审知死与延翰自称、926正授建国区分；承休汭受诘及斩子不推子女名、人数或严氏死亡；孟任西川、到洛、未来到蜀分开；史彦琼为伶官不自动判宦官；银枪亲军收编复用915事件，背景许赏怨望追叙不强定925；军荒年概述、孔谦日等粮、猎行分层，租唐/吏座/恿悍/史书令疑字保留；白龙只作祥瑞报告，更名龚不新建刘龚；增城妻郑旻据新史，不误配郑昭淳，父系刘隐及公主/县主和七年/925叙次分别保留，不立父女边；李琪上疏敕行但未落实；蜀官五品以下有条件归田，降王封土诏仅承诺；高万兴卒、高允韬留后与926正授分开；赴汴只是拟议而因谏停止。'
for n in range(13,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=925,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,25)],next_paragraph=Q[25]['id'],next_volume=274,supplements=supplements,coverage='卷274第13—24段，原文件18—29行；925年十二月宗弼族诛、闽继承及汀州围城、承休受诘斩杀、两都及西川任官、年荒猎行、汉改元更名与长和婚姻、闰月孟抵洛及军储政策、蜀官处分与降王诏、高万兴卒子任留后、拟赴汴而止。尚余第25—29五正文段；第30项已核为926章节标题。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(13,25)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
