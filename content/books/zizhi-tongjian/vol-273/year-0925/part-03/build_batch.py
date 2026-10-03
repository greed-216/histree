# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 925, paragraphs 25–31."""
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
 ('tongjian-273-925-summer',YEAR/'part-02/sources/library/tongjian-273-925-summer','b76f75cc','司马光等'),
 ('tongjian-273-925-shu-campaign',P/'sources/library/tongjian-273-925-shu-campaign','0ae3ec4a','司马光等'),
 ('xinwudaishi-063-wang-jian-burial',ROOT/'content/books/zizhi-tongjian/vol-270/year-0918/part-08/sources/library/xinwudaishi-063-wang-jian-burial','d87e4170','欧阳修'),
 *[(key,P/'sources/library'/key,'0ae3ec4a',author) for key,author in [
 ('jiuwudaishi-033-925-september-opening','薛居正等'),('jiuwudaishi-033-925-campaign-edict','薛居正等'),('jiuwudaishi-033-925-staff-departure','薛居正等'),('jiuwudaishi-067-liyu-campaign','薛居正等'),('jiuwudaishi-068-chenyi','薛居正等'),('xinwudaishi-024-925-campaign-command','欧阳修'),('xinwudaishi-063-925-east-tour','欧阳修')]],
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0925-p025-p031',
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
for n in range(25, 32):
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
people, used, reused, supplements = {}, {}, {'tongjian-273-925-summer','xinwudaishi-063-wang-jian-burial'}, []

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
    ck = f'claim_zztj_273_0925_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
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
E=ev('shu_september_mountain_tour','王宗衍与徐太后、徐太妃游青城山，经彭州汉州而还',25,'九月',None,[('蜀主','巡游蜀主'),('蜀太后','同游太后'),('蜀太妃','同游太妃')],when='925年九月，确日未载',place='青城山、丈人观、上清宫、彭州阳平化、汉州三学山',note='蜀太后、太妃分别为徐贤妃、徐淑妃；不误接后唐曹氏刘氏。')
claim('person',people['徐贤妃'],'description','新史记王宗衍尊母徐氏为皇太后，母妹淑妃为皇太妃。',25,'衍因尊其母徐氏為皇太后，后妹淑妃為皇太妃。','回查已发布918年出处，既有人物徐贤妃、徐淑妃复用；不在925年重复新建尊封事件。',source='xinwudaishi-063-wang-jian-burial',relation='adds')
claim('event',E,'description','新史925年叙次亦记幸彭州阳平化、汉州三学山。',25,'是歲，又幸彭州陽平化、漢州三學山。','印证地名，不把其后十月拟幸秦州并成此次九月游。',source='xinwudaishi-063-925-east-tour',relation='corroborates')
E=ev('jiji_prince_wei_investiture','皇子李继岌封魏王',26,'乙未',None,[('继岌','受封皇子'),('帝','封王君主')],when='925年九月乙未',place='后唐宫廷',note='继岌封魏王与后来伐蜀都统分阶段，不把储副评价等同另立皇太子。')
relationship('帝','继岌','父亲',26,'立皇子继岌为魏王。','李存勖是李继岌的父亲，沿既有关系key/UUID，反向不新建重复关系。')
claim('event',E,'description','旧史同乙未封第三子、邺都留守李继岌为魏王。',26,'乙未，製封第三子鄴都留守、興聖宮使、檢校太尉、同平章事、判六軍諸衛事繼岌為魏王。','补排行与既有官职；第三子依旧史，不推其他子排序。',source='jiuwudaishi-033-925-september-opening',relation='adds')
E=ev('shu_command_shaohong_recommends_ning','议伐蜀时李绍宏荐段凝，郭崇韬反对',27,'丁酉','不可信也。”',[('帝','议伐蜀君主'),('李绍宏','宣徽使、荐将者'),('李绍钦','威胜节度使、被荐者'),('崇韬','反对者')],when='925年九月丁酉',place='后唐宫廷',note='李绍钦同段凝；盖世奇才和奸谄绝伦分别是李绍宏与郭评价，不作已验证客观能力。')
E=ev('shu_command_siyuan_jiji_proposal','众举李嗣源，郭崇韬主张其守河朔而以李继岌为伐蜀都统',27,'众举','成其威名。”',[('嗣源','被举将领、拟留河朔者'),('崇韬','主张继岌都统者'),('继岌','拟任伐蜀都统者')],when='925年九月丁酉议将',place='后唐宫廷、河朔',note='储副是郭建议中的地位评价，不另造立太子事件；契丹方炽为留守理由。')
claim('event',E,'description','新史郭崇韬也以契丹北患需总管为由，提出魏王按唐亲王元帅故事领军。',27,'契丹為患北邊，非總管不可禦。魏王繼岌，國之儲副，而大功未立；且親王為元帥，唐故事也。','本段开头明年电子校注已标误，按主书925连续叙次，不误录926；人物评价与原因是郭的话。',source='xinwudaishi-024-925-campaign-command',relation='corroborates')
E=ev('shu_command_chongtao_deputy_selected','李存勖认为继岌年幼需副将，选郭崇韬',27,'帝曰：“儿幼','无以易卿。”',[('帝','择副将者'),('继岌','被认为需副将者'),('崇韬','被选副将者')],when='925年九月丁酉议将',place='后唐宫廷',note='评价年幼不倒算生年；选副与庚子正式任命分开。')
claim('event',E,'description','新史亦记庄宗选郭崇韬，并说无以易卿。',27,'莊宗曰：「吾得之矣，無以易卿也。」','印证择副话语，正式职权另以主书任命句录。',source='xinwudaishi-024-925-campaign-command',relation='corroborates')
E=ev('shu_campaign_high_command','后唐任命李继岌为伐蜀都统、郭崇韬掌军事',27,'庚子','军事悉以委之。',[('继岌','西川四面行营都统'),('崇韬','东北面行营都招讨制置等使、掌军事者')],when='925年九月庚子',place='后唐伐蜀行营',note='军政主郭，不能仅看亲王都统名义推所有战术决策由继岌作出。')
claim('event',E,'description','旧史诏书记李继岌西川四面都统、郭崇韬西川东北面招讨制置使。',27,'今命興聖宮使、魏王繼岌充西川四面行營都統，命侍中、樞密使郭崇韜充西川東北面行營都招討製置等使，','补诏书全称，主书省西川前缀不作另一支军。',source='jiuwudaishi-033-925-campaign-edict',relation='corroborates')
claim('event',E,'description','新史称继岌为西南面行营都统。',27,'乃以繼岌為西南面行營都統，','西南面与主书旧史西川四面称谓不同，保留原字，不擅统一职衔。',source='xinwudaishi-024-925-campaign-command',relation='conflicts')
E=ev('shu_campaign_regional_staff','后唐任命伐蜀各路招讨、供军、安抚与虞候诸使',27,'又以','客省使李严充西川管内招抚使，',[
 ('高季兴','荆南节度使、东南面行营都招讨使'),('李继\ue4be严','凤翔节度使、都供军转运应接等使'),('李令德','同州节度使、行营副招讨使'),('李绍琛','陕州节度使、蕃汉马步军都排陈斩斫使兼马步军都指挥使'),('张筠','西京留守、西川管内安抚应接使'),('毛璋','华州节度使、左厢马步都虞候'),('董璋','邠州节度使、右厢马步都虞候'),('李严','客省使、西川管内招抚使')],when='925年九月庚子伐蜀任命',place='荆南、凤翔、同州、陕州、西京、华州、邠州',note='赐名同主体：高季兴为高季昌，李绍琛为康延孝，李令德为朱令德；李继编码严依此前旧新史校核李继曮，不与客省李严混为一人。')
claim('event',E,'description','旧史诏書所见副招讨、都虞候、安抚招抚等人职与主书相应。',27,'同州節度使李令德充行營招討副使，陝府節度使李紹琛充行營蕃漢馬步軍都排陣斬斫使，西京留守張筠充西川管內安撫應接使，華州節度使毛璋充行營左廂馬步都虞候，邠州節度使董璋充行營右廂馬步都虞候，客省使李嚴充西川管內招撫使，','职位细节原书有省称，不复制一套赐名人物。',source='jiuwudaishi-033-925-campaign-edict',relation='corroborates')
claim('event',E,'description','旧史诏书凤翔供军转运应接使处记李严，与主书李继编码严不同。',27,'鳳翔節度使李嚴充供軍轉運應接等使，','同诏另有客省李严；此处疑缺赐名字符，原文保留，主体依凤翔任职及此前校核为李继曮，不将两职合一；纸本待核。',source='jiuwudaishi-033-925-campaign-edict',relation='conflicts')
E=ev('shu_campaign_force_and_jingnan_order','伐蜀军数六万，高季昌受诏取夔忠万三州为巡属',27,'将兵六万','为巡属。',[('继岌','都统、所领行营'),('崇韬','招讨主军事者'),('高季兴','受命取三州者')],when='925年九月庚子任命及诏令',place='伐蜀行营、夔州、忠州、万州',note='六万按史载，不另加各支兵数；受诏不是三州已经归其所有，后续实战按序录。')
E=ev('shu_campaign_central_command_staff','都统中军任李从袭监押，李廷安吕知柔为魏王府通谒',27,'都统置中军','吕知柔充魏王府通谒。',[('李从袭','供奉官、中军马步都指挥监押'),('李廷安','高品、魏王府通谒'),('吕知柔','高品、魏王府通谒'),('继岌','设置中军的都统')],when='925年九月伐蜀中军设置，确日未载',place='魏王行营',note='官职带同军人物未必互为私人关系，不建统属或同僚边。')
claim('event',E,'description','旧史记李从袭为中军马步军都监，李廷安吕知柔为魏王衙通谒。',27,'供奉官李從襲充中軍馬步軍都監，高品李廷安、呂知柔充魏王衙通謁。','主书都指挥监押、旧史都监分书保留，魏王府/衙是用语差异。',source='jiuwudaishi-033-925-staff-departure',relation='corroborates')
E=ev('shu_campaign_yuan_yu_military_council','任圜、李愚受命参预都统军机',27,'辛丑',None,[('圜','工部尚书、军机参预者'),('李愚','翰林学士、军机参预者')],when='925年九月辛丑',place='魏王伐蜀行营')
claim('event',E,'description','旧史同记任圜李愚参魏王军事。',27,'詔工部尚書任圜、翰林學士李愚參魏王軍事。','同辛丑段官职人名印证。',source='jiuwudaishi-033-925-staff-departure',relation='corroborates')
claim('person',people['李愚'],'description','旧史李愚传记继岌征蜀时请其为都统判官，带翰林本职从军。',27,'三年，魏王繼岌征蜀，請為都統判官，仍帶本職從軍。','补判官身份，不把其后蜀平中书舍人任命提前到出征前。',source='jiuwudaishi-067-liyu-campaign',relation='adds')
E=ev('seventy_five_days_rain_ends','史书记连雨七十五日后始晴，江河百川泛溢',28,'自六月',None,[],when='主书记自925年六月甲午雨，凡七十五日乃霁',place='江河百川，原文未限定具体全域',note='不据概括认全国每一地每一天皆雨；与先前六月壬申始雨叙次保留，不擅改日干支。')
claim('event',E,'time_original','旧史司天奏称自七月三日大雨，至九月十八日后方晴，三辰行度不见。',28,'司天上言：「自七月三日大雨，至九月十八日後方晴，三辰行度不見。」','与主书六月甲午起雨不同，可能统计范围或底本问题，分书保留不强行推同起日。',source='jiuwudaishi-033-925-staff-departure',relation='conflicts')
E=ev('chongtao_recommends_meng_and_xian','郭崇韬将行荐孟知祥为得蜀后帅，荐张宪可为相',29,'郭崇韬','可为相，',[('崇韬','荐举者'),('孟知祥','北都留守、被荐作未来蜀帅者'),('宪','邺都副留守、被荐作相者'),('帝','受荐君主')],when='925年九月戊申出征前，确日未载',place='后唐宫廷',note='若得西川的条件任帅与可为相皆建议，不能记此日已任两职；荐引旧恩为背景不锁定发生于925。')
E=ev('shu_campaign_departure_west','后唐伐蜀大军西行',29,'戊申',None,[('继岌','都统'),('崇韬','招讨使、领军事者')],when='925年九月戊申',place='后唐至蜀方向',note='人物参与由本年任命及旧史具名出征句补足，不以西行等到成都或蜀已平。')
claim('event',E,'description','旧史同戊申记魏王继岌、郭崇韬进发西征。',29,'戊申，魏王繼岌、樞密使侍中郭崇韜進發西征。','同日具名印证；前诏取九月十八日进发与实际出征句均保留其原纪时。',source='jiuwudaishi-033-925-staff-departure',relation='corroborates')
E=ev('anchongba_promotes_qin_tour','安重霸劝王承休请王宗衍东游秦州',30,'蜀安','东游秦州。',[('安重霸','劝邀游者'),('王承休','拟邀君主者'),('蜀主','拟受邀者')],when='925年九月至十月秦州游拟议，确日未载',place='秦州',note='请游而未出行，不能当成已经到秦州。')
E=ev('chengxiu_palace_and_forced_dancers','追叙王承休到官毁府署作行宫，兴役并强取女子教歌舞',30,'承休到官','图形遗韩昭，',[('王承休','营宫征役及强取女子者'),('韩昭','接受图形者')],year=None,when='王承休到官后、925年秦州游以前，确年未载',place='秦州',note='图形语境承所取女子，不捏造留存画像；强取女子未名不建具名人物。')
E=ev('chengxiu_qin_flower_landscape_promotion','王承休托韩昭邀蜀主，献花木图盛称秦州景物',30,'使言于蜀主','山川土风之美。',[('王承休','献图称美者'),('韩昭','受托向蜀主进言者'),('蜀主','被邀者')],year=None,when='925年拟秦州游前，确日未载',place='秦州、蜀廷',note='赞美是王承休劝说，不当现代旅游或地理评价。')
E=ev('shu_qin_tour_remonstrances_rejected','王宗衍欲往秦州，拒群臣及王宗弼谏，徐太后哭泣不食亦未能阻止',30,'蜀主将如','亦不能得。',[('蜀主','坚持拟游者'),('王宗弼','上表谏者'),('蜀太后','涕泣不食、劝止者')],when='925年秦州游拟议，确日未载',place='蜀廷、拟往秦州',note='投表不是杀王宗弼；劝止无效不等已经到达目的地。')
claim('event',E,'description','新史记十月因王承休妻严氏拟幸秦州，群臣切谏不听。',30,'以王承休妻嚴氏故，十月，幸秦州，羣臣切諫，衍不聽。','新史概述幸秦州，主书后续写出成都到利州转还；此处只补拟行月份及拒谏，不认已实际到秦州。',source='xinwudaishi-063-925-east-tour',relation='corroborates')
E=ev('pu_yuqing_long_memorial','蒲禹卿上表近二千言劝阻秦州游，陈述劳役与内外风险',30,'前秦州','不足凭恃。”',[('蒲禹卿','前秦州节度判官、上表者'),('蜀主','受谏君主')],when='925年秦州游前，确日未载',place='蜀廷、秦州相关',note='近二千为史载表篇幅，非现有节录完整二千字；表中疾病、盗贼、唐凤翔疑虑及古人败亡为奏者意见，不另造本年已发生战争事件。')
claim('event',E,'description','蒲禹卿以凤翔旧仇、唐蜀新通好可能生疑为劝阻理由。',30,'凤翔久为仇雠，必生衅隙；唐国方通欢好，恐怀疑贰。','对风险的预警，不当外交已断绝或两边已经开战。')
claim('event',E,'description','蒲禹卿以李势刘禅的败亡说明山河险固不足凭恃。',30,'昔李势屈于桓温，刘禅降于邓艾，山河险固，不足凭恃。','历史类比留作引文，不将四位古人列为925事件参与者。')
E=ev('han_zhao_threatens_pu_yuqing','韩昭声称收蒲禹卿表，待蜀主归来令狱吏逐字问罪',30,'韩昭谓','字字问汝！”',[('韩昭','威胁者'),('蒲禹卿','被威胁上表者')],when='925年秦州游前，确日未载',place='蜀廷',note='当使狱吏是未来威胁，主书未记已拘捕刑讯蒲，不创建已下狱事件。')
E=ev('shu_ruler_chengxiu_wife_affair','史书记王宗衍与王承休妻严氏私通，因此锐意出游',30,'王承休妻',None,[('蜀主','私通及欲行者'),('严氏','王承休妻、所涉对象'),('王承休','严氏之夫')],year=None,when='925年出游以前，私通确年未载',place='原文未载私通地点',note='美与出游动机为主书叙述；不外推严氏主动诱导或王承休知情。')
relationship('严氏','王承休','妻子',30,'王承休妻严氏美，蜀主私焉，故锐意欲行。','严氏是王承休妻子，端点方向明确；不因新史称王承休宦者而否定其明载婚姻。')
claim('event',E,'description','新史亦记王承休妻严氏、王宗衍与其通。',30,'承休妻嚴氏，有絕色，衍通之。','印证妻子及私通叙述，非现代审判认定。',source='xinwudaishi-063-925-east-tour',relation='corroborates')
E=ev('shu_campaign_vanguard_force','康延孝与李严率骁骑三千步兵万人为前锋',31,'冬','为前锋，',[('李绍琛','排陈斩斫使、前锋领将'),('李严','前锋同行领将')],when='925年十月，确日未载',place='伐蜀进军途中',note='三千骑、万人步是前锋分兵，不与总六万相加制造七万三千总数。')
E=ev('chen_yi_illness_request_baoji','招讨判官陈乂到宝鸡称疾请求留下',31,'招讨判官','称疾乞留。',[('陈乂','招讨判官、称疾乞留者')],when='925年十月前锋西进时，确日未载',place='宝鸡',note='称疾为陈说法，不自行判真病或诈病。')
claim('person',people['陈乂'],'description','主书陈乂为蓟州人。',31,'乂，蓟州人也。','籍贯史载，不填现代出生地坐标。')
claim('person',people['陈乂'],'description','旧史记陈乂为蓟门人。',31,'陳乂，薊門人也。','蓟门与主书蓟州相应；其他晚年任官与死不提前录。',source='jiuwudaishi-068-chenyi',relation='corroborates')
claim('person',people['陈乂'],'description','旧史记郭崇韬从李继岌伐蜀时署陈乂为招讨判官。',31,'崇韜從魏王繼岌伐蜀，署為招討判官。','同次征蜀官职补证；不把前后追叙未明确年份的任官并为925年同日。',source='jiuwudaishi-068-chenyi',relation='corroborates')
E=ev('li_yu_threatens_execution_chen_yi','李愚指陈乂畏难，提出斩以徇，军中无人敢迟留',31,'李愚厉声','由是军中无敢顾望者。',[('李愚','斥责及主张行军纪律者'),('陈乂','被斥责者')],when='925年十月宝鸡乞留后，确日未载',place='宝鸡军中',note='宜斩是李愚主张，不是陈乂实际被杀；旧史陈传明确其后任官，可防误读。')
claim('event',E,'description','旧史李愚传亦记陈乂宝鸡称疾，李愚称正可斩以徇，军人无迟留。',31,'招討判官陳乂至寶雞，稱疾乞留在後。愚厲聲曰：「陳乂見利則進，懼難則止。今大軍涉險，人心易惑，正可斬之以徇。」由是軍人無遲留者。','同言行印证，句中无已斩陈乂结果。',source='jiuwudaishi-067-liyu-campaign',relation='corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续25—31段；蜀太后太妃合徐贤妃徐淑妃不串曹刘；封魏王非立太子；赐名段凝康延孝高季昌朱令德李继曮复用，旧诏凤翔李严疑缺字不并客省李严；都统职衔四面/西南面分书保留，新史明年校注不认926；任命及三州诏令非已得地；中军与前锋兵数不叠加；主六月甲午、旧七月三日起连雨分书记；郭荐蜀帅相位未任；秦州游未实际到秦州，蒲上表类比不造古人925参与；韩昭威胁非蒲已下狱；严氏妻关系按明文；李愚宜斩陈乂非陈被杀。'
for n in range(25,32):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=925,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(25,32)],next_paragraph=Q[32]['id'],supplements=supplements,coverage='卷273第25—31段，原文件108—114行；925年九月至十月，蜀游山、封魏王、伐蜀议将及任命、连雨、荐帅及西行、秦州游劝阻、前锋与宝鸡军纪。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(25,32)],supplement_search_gaps=[dict(paragraph_id=Q[30]['id'],note='新史蒲禹卿检索未得其长表直接补证，依主书节录；专门史籍暂缓。')]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
