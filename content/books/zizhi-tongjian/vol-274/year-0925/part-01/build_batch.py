# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 274, year 925, paragraphs 1–12."""
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
OLD = ROOT/'content/books/zizhi-tongjian/vol-273/year-0925'
specs = [
 ('tongjian-274-925-surrender',P/'sources/library/tongjian-274-925-surrender','7f618e05','司马光等'),
 ('tongjian-274-925-aftermath',P/'sources/library/tongjian-274-925-aftermath','7f618e05','司马光等'),
 ('jiuwudaishi-033-925-november-advance',P/'sources/library/jiuwudaishi-033-925-november-advance','7f618e05','薛居正等'),
 ('jiuwudaishi-033-925-submission',P/'sources/library/jiuwudaishi-033-925-submission','7f618e05','薛居正等'),
 ('jiuwudaishi-033-925-entry',P/'sources/library/jiuwudaishi-033-925-entry','7f618e05','薛居正等'),
 ('jiuwudaishi-074-925-yanxiao',P/'sources/library/jiuwudaishi-074-925-yanxiao','7f618e05','薛居正等'),
 ('jiuwudaishi-136-925-surrender',P/'sources/library/jiuwudaishi-136-925-surrender','7f618e05','薛居正等'),
 ('xinwudaishi-044-925-commanders',P/'sources/library/xinwudaishi-044-925-commanders','7f618e05','欧阳修'),
 ('xinwudaishi-024-925-gifts',P/'sources/library/xinwudaishi-024-925-gifts','7f618e05','欧阳修'),
 ('songshi-479-lihao-origin',P/'sources/library/songshi-479-lihao-origin','7f618e05','脱脱等'),
 ('songshi-479-lihao-shu-offices',P/'sources/library/songshi-479-lihao-shu-offices','7f618e05','脱脱等'),
 ('jiuwudaishi-057-chongtao-conquest',OLD/'part-04/sources/library/jiuwudaishi-057-chongtao-conquest','c80261f8','薛居正等'),
 ('xinwudaishi-014-jiji-conquest',OLD/'part-04/sources/library/xinwudaishi-014-jiji-conquest','c80261f8','欧阳修'),
 ('xinwudaishi-044-yanxiao-conquest',OLD/'part-04/sources/library/xinwudaishi-044-yanxiao-conquest','c80261f8','欧阳修'),
 ('xinwudaishi-063-925-east-tour',OLD/'part-03/sources/library/xinwudaishi-063-925-east-tour','0ae3ec4a','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0925-p001-p012',
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
    ck = f'claim_zztj_274_0925_01_{len(B["claims"])+1:04d}'
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
        row['aliases']={'王承涓':[],'李昊':[],'郭廷诲':['郭廷誨','廷诲','廷誨']}.get(name,row['aliases'])
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
E=ev('shu_ruler_return_chengdu','王宗衍回成都，百官与后宫迎于七里亭',1,'十一月','迎于七里亭。',[('蜀主','返城者')],when='925年十一月丙申',place='成都、七里亭')
E=ev('shu_ruler_huihu_costume_entry','王宗衍在妃嫔中作回鹘队入宫',1,'蜀主入','队入宫。',[('蜀主','作队入宫者')],when='925年十一月丙申',place='成都宫中',note='回鹘队为本句宫廷装扮队列，不据此生成真实回鹘军队参战或族属事实。')
claim('event',E,'description','新史同记王宗衍回成都，杂宫人作回鹘队而入。',1,'衍自緜谷還成都，百官及後宮迎謁七里亭，衍雜宮人作回鶻隊以入。','緜/绵与回鶻/回鹘用于显示匹配；不推族属。',source='xinwudaishi-063-925-east-tour',relation='corroborates')
E=ev('shu_court_silent_weeping','王宗衍在文明殿见群臣流泪，君臣相视无救国之言',1,'丁酉',None,[('蜀主','流泪见群臣者')],when='925年十一月丁酉',place='文明殿',note='无一言为史家叙述，不外推所有臣子此前从未提出办法。')
E=ev('yanxiao_repair_jubai_bridge','康延孝至利州修桔柏浮梁',2,'戊戌','修桔柏浮梁。',[('李绍琛','到达修桥者')],when='925年十一月戊戌',place='利州、桔柏津')
claim('event',E,'description','旧史本纪同记康延孝至利州修吉柏津浮梁。',2,'康延孝至利州，修吉柏津浮梁。','桔柏/吉柏为底本文字差异，事件及将领沿既有主体。',source='jiuwudaishi-033-925-november-advance',relation='corroborates')
E=ev('linsie_abandon_request_surrender','林思谔此前弃城奔阆州，并遣使请降',2,'昭武','遣使请降。',[('林思谔','昭武节度使、弃城及请降者')],when='925年十一月戊戌叙次；先弃城确日未载',place='阆州',note='先字追叙弃城，不能把两个动作均强定戊戌；请降尚非具体授官。')
claim('event',E,'description','旧史本纪同记昭武军节度使林思谔来降。',2,'偽昭武軍節度使林思諤來降。','諤简化谔复用同人；本纪未重复阆州路线，不视为否定。',source='jiuwudaishi-033-925-november-advance',relation='corroborates')
E=ev('jiji_arr_jianzhou','李继岌至剑州',2,'甲辰','至剑州，',[('继岌','到达都统')],when='925年十一月甲辰',place='剑州')
E=ev('zongshou_five_prefectures_surrender','王宗寿以遂合渝泸昌五州降唐',2,'蜀武信',None,[('王宗寿','武信节度使兼中书令、降者')],when='925年十一月甲辰叙次',place='遂州、合州、渝州、泸州、昌州',note='主书第五州昌；旧史作忠，两书名单分别保留，不合为六州。')
claim('event',E,'description','旧史本纪同日记王宗寿以遂合渝泸忠五州来降。',2,'甲辰，魏王至劍州，偽武信軍節度使王宗壽以遂、合、渝、瀘、忠五州來降。','忠/昌是异文而非繁简对应；不猜改底本或坐标。',source='jiuwudaishi-033-925-november-advance',relation='conflicts')
E=ev('zongbi_return_armed_palace_gate','王宗弼回成都登大玄门严兵自卫，蜀主与太后往劳而遭骄慢',3,'王宗弼至','无复臣礼。',[('王宗弼','拥兵者'),('蜀主','前往慰劳者'),('蜀太后','前往慰劳者')],when='925年十一月乙巳前，确日未载',place='成都、大玄门',note='大玄门保留底本；骄慢及无臣礼为主书记述，不新建感情或臣属永久关系。')
claim('event',E,'description','新史写王宗弼归成都登太玄门。',3,'而宗弼亦自緜谷馳歸，登太玄門，','太/大玄门不同，不靠繁简转换覆盖主书。',source='xinwudaishi-063-925-east-tour',relation='conflicts')
E=ev('zongbi_seize_palace_and_treasury','王宗弼劫迁蜀主及太后后宫诸王于西宫，收玺绶并夺内库金帛入家',3,'乙巳','悉归其家。',[('王宗弼','劫迁及收夺者'),('蜀主','被劫迁君主'),('蜀太后','被劫迁太后')],when='925年十一月乙巳',place='成都、西宫、义兴门',note='劫迁和私取财富分别于降唐后的正式授官；未据此认王宗弼合法继位。')
claim('event',E,'description','新史蜀世家写王宗弼迁王宗衍于天启宫。',3,'衍即上表乞降，宗弼遷衍于天啟宮。','天启宫与主书西宫名称分别保留，不未经核实判为不同两次迁宫或同一宫。',source='xinwudaishi-063-925-east-tour',relation='conflicts')
E=ev('chengjuan_seize_palace_consorts','王承涓持剑入宫取王宗衍宠姬数人归家',3,'其子','数人以归。',[('王承涓','王宗弼之子、持剑取人者'),('蜀主','宠姬所属君主')],when='925年十一月乙巳叙次',place='成都宫中',note='其子承涓承王宗弼，数人未具名不捏造人物；不能把强取等作婚姻关系。')
relationship('王宗弼','王承涓','父亲',3,'其子承涓杖剑入宫，取蜀主宠姬数人以归。','王宗弼是王承涓父亲；与后文王承班为两个人，不能自动当异名。')
E=ev('zongbi_claim_acting_xichuan_command','王宗弼自称权西川兵马留后',3,'丙午',None,[('王宗弼','自称留后者')],when='925年十一月丙午',place='成都',note='自称不等唐帝正式任命，后文求西川节度使仍为请求。')
claim('event',E,'description','旧史本纪辛亥收到宗弼报称迁蜀主西宅并权称西川兵马留后。',3,'辛亥，魏王至德陽。偽六軍使王宗弼報，王衍舉家遷於西宅，宗弼權稱西川兵馬留後；','报告日期辛亥不覆盖主书自称丙午；西宅/西宫分别保留。',source='jiuwudaishi-033-925-submission',relation='corroborates')
E=ev('yanxiao_mianzhou_burned_bridge_cut','康延孝进至绵州，见蜀兵已焚仓库民居并断绵江浮梁',4,'李绍琛','无舟楫可渡，',[('李绍琛','到达者')],when='925年十一月丁未前，确日未载',place='绵州、绵江',note='蜀兵未具名不擅指定王宗衍亲自烧毁；既成毁坏与到达不是同一动作时间。')
E=ev('yanxiao_urges_rapid_crossing','康延孝向李严主张乘蜀人破胆迅速渡江，不等修桥',4,'绍琛谓','胜负未可知矣。”',[('李绍琛','提出速进方案者'),('李严','受议者')],when='925年十一月绵江渡前',place='绵江',note='百骑足破关及拖延胜负未定是其军事判断，不录为已发生战果。')
E=ev('yanxiao_liyan_float_mianjiang','康延孝与李严骑马浮渡绵江，从兵仅千人渡成、千余人溺死，进入鹿头关',4,'乃与严','遂入鹿关头；',[('李绍琛','浮渡率军者'),('李严','共同浮渡者')],when='925年十一月丁未前',place='绵江、鹿头关',note='底本句末鹿关头与同段前文及两史鹿头关倒字，展示鹿头关并保留原句；千及千余为史载概数，不反推总参渡数精确值。')
claim('event',E,'description','旧史康延孝传同记与李严浮江，千人渡成、步军千余人溺死，通鹿头。',4,'因與李嚴乘馬浮江，於是得濟者僅千人，步軍溺死者亦千餘人。延孝既濟，長驅通鹿頭，進據漢州。','旧传补溺死者为步军；不把新史省略损失当无损失。',source='jiuwudaishi-074-925-yanxiao',relation='corroborates')
claim('event',E,'description','新史康传亦记与李严浮江，军士千余人渡成，入鹿头关。',4,'因與嚴乘馬浮江，軍士隨之濟者千餘人，遂入鹿頭關，','千余与主书仅千为近似数不同措辞并列，省略溺死记述不等否认损失；鹿头关可佐底本倒字。',source='xinwudaishi-044-yanxiao-conquest',relation='conflicts')
E=ev('yanxiao_arr_hanzhou_rear_follow','康延孝进据汉州，三日后后军始至',4,'丁未',None,[('李绍琛','先抵汉州将领')],when='925年十一月丁未进据；后军三日后到',place='汉州',note='居三日为相对时间，不换算公历确日。')
claim('event',E,'description','旧史康延孝传同记进据汉州后三日后军到。',4,'進據漢州。居三日，部下後軍方至。','同进军阶段。',source='jiuwudaishi-074-925-yanxiao',relation='corroborates')
E=ev('zongbi_reassures_army_invites_liyan','王宗弼遣使以币马牛酒劳唐军，王宗衍致李严书称来则降',5,'王宗弼','吾即降。”',[('王宗弼','遣使劳军者'),('蜀主','致书请李严者'),('李严','受书者')],when='925年十一月唐军抵汉州后',place='成都、唐行营',note='承诺来即降不同于后文正式出降。')
E=ev('liyan_ignores_warning_enters_chengdu','李严不听有人以蜀人怨恨劝阻，驰入成都抚谕吏民并告大军将至',5,'或谓严','后宫皆恸哭。',[('李严','入城抚谕者'),('蜀主','君臣恸哭之君主')],when='925年十一月唐军未正式入成都前',place='成都',note='深怨为匿名劝阻者话，不生成所有蜀人敌视李严的关系。')
claim('event',E,'description','旧史本纪丁未汉州叙次同记王宗衍送牛酒请降，李严先入成都。',5,'康延孝、李嚴至漢州，王衍遣人送牛酒請降，李嚴遂先入成都。','送礼主语在两书分别为王宗弼与王衍，保留各书记法；先入不是军队正式入城。',source='jiuwudaishi-033-925-november-advance',relation='corroborates')
E=ev('shu_ruler_entrusts_family_liyan','王宗衍引李严见太后，以母妻相托',5,'蜀主引','以母妻为托。',[('蜀主','托付者'),('李严','受托者'),('蜀太后','会见及被托付者')],when='925年十一月李严入成都时',place='成都宫中',note='母妻未各具婚配对象；不补成李严保护结果或此前婚姻记录。')
E=ev('liyan_removes_city_defenses','王宗弼仍乘城备守，李严命撤去楼橹',5,'宗弼犹',None,[('王宗弼','仍备守者'),('李严','下撤防命者')],when='925年十一月李严入成都后',place='成都城防')
E=ev('jiji_arr_mianzhou','李继岌至绵州',6,'己酉','至绵州，',[('继岌','到达者')],when='925年十一月己酉',place='绵州')
claim('event',E,'time_original','旧史本纪在十一月己酉同记魏王至绵州。',6,'己酉，魏王至綿州，王衍遣使上箋歸命。','支持十一月纪月。',source='jiuwudaishi-033-925-submission',relation='corroborates')
claim('event',E,'time_original','新史继岌传作十月己酉至绵州。',6,'十月己酉，繼岌至綿州，衍上牋請降。','与主书、旧本纪十一月不同，原字并列待校。',source='xinwudaishi-014-jiji-conquest',relation='conflicts')
E=ev('shu_surrender_documents_envoy','王宗衍命李昊草降表、王锴草降书，遣欧阳彬迎李继岌与郭崇韬',6,'蜀主命',None,[('蜀主','发令者'),('李昊','翰林学士、草降表者'),('王锴','中书待郎同平章事、草降书者'),('欧阳彬','兵部侍郎、奉文迎军使者'),('继岌','迎接对象'),('崇韬','迎接对象')],when='925年十一月己酉叙次',place='成都至唐行营',note='中书待郎为底本，疑侍字待纸本核；不因自动转换改官称。')
claim('person',people['李昊'],'description','宋史记李昊字穹佐，生于关中；自言唐相李绅后裔。',6,'李昊，字穹佐，自言唐相紳之後。祖乾祐，建州刺史。父羔，容管從事。昊生於關中，','穹佐及关中作补充；自言是本人谱系主张，未另建确定李绅血亲边，也不从年龄故事推具体生年。',source='songshi-479-lihao-origin',relation='adds')
claim('person',people['李昊'],'description','宋史记王宗衍袭位后李昊历中书舍人、翰林学士。',6,'王衍襲偽位，授彭州導江令，歷中書舍人、翰林學士。','与主书925翰林身份对应；没有据此新录926以后李昊任职。',source='songshi-479-lihao-shu-offices',relation='corroborates')
E=ev('zongbi_executes_four_officers_blame','王宗弼归罪宋光嗣景润澄李周辂欧阳晃惑主，杀四人并送首给李继岌',7,'王宗弼称','函首送继岌。',[('王宗弼','归责及斩送者'),('宋光嗣','内枢密使、被斩者'),('景润澄','内枢密使、被斩者'),('李周辂','宣徽使、被斩者'),('欧阳晃','宣徽使、被斩者'),('继岌','首级送交对象')],when='925年十一月己酉至辛亥叙次，确日未载',place='成都',note='久欲归命及四人惑主是王宗弼所称，不录为已独立证实的蜀廷一致意愿或亡国唯一原因。')
claim('event',E,'description','旧史蜀世家载十一月二十一日王宗衍致报称处斩四人并送首。',7,'十一月二十一日，魏王至德陽，衍報云：「比與將校謀歸國，偽樞密使宋光嗣、景潤澄，南北院宣徽使李周輅、歐陽晃等四人異謀熒惑，臣各已處斬，今送納首級。」','报告以王衍名义自称，与主书宗弼实际斩送的归责层次分开；报告日不擅认四人同日被斩。',source='jiuwudaishi-136-925-surrender',relation='adds')
E=ev('zongbi_executes_hanzhao','王宗弼责韩昭佞谀，枭于金马坊门',7,'又责','金马坊门。',[('王宗弼','责杀者'),('韩昭','文思殿大学士礼部尚书成都尹、被杀者')],when='925年十一月本段，确日未载',place='成都、金马坊门',note='佞谀是责词；不作现代客观性格诊断。')
E=ev('shu_notables_bribe_zongbi_to_survive','徐延琼潘在迎顾在珣等以金帛妓妾贿赂王宗弼免死',7,'内外马步','仅得免死。',[('徐延琼','内外马步都指挥使兼中书令、行赂免死者'),('潘在迎','果州团练使、行赂免死者'),('顾在珣','嘉州刺史、行赂免死者'),('王宗弼','受贿者')],when='925年十一月本段，确日未载',place='成都',note='不能将交付妓妾推成各人与宗弼妻妾的婚配；诸贵戚未具名不造实体。')
E=ev('zongbi_kills_personal_targets','史载王宗弼杀素来不快之人',7,'凡素所',None,[('王宗弼','杀人者')],when='925年十一月本段，确日未载',place='成都',note='概述未具人数与姓名，不补名单。')
E=ev('jiji_arr_deyang','李继岌至德阳',8,'辛亥','至德阳。',[('继岌','到达者')],when='925年十一月辛亥',place='德阳')
E=ev('zongbi_reports_west_residence','王宗弼奉笺称已迁蜀主于西第并安抚军城待唐军',8,'宗弼遣使','以俟王师。',[('王宗弼','上笺自报者'),('蜀主','被迁者')],when='925年十一月辛亥叙次',place='成都、西第',note='已迁承前乙巳事件，此为报告，不重复计为第二次迁宫；安抚为其所称。')
E=ev('chengban_gifts_for_xichuan_office','王宗弼遣王承班以蜀后宫珍玩赂李继岌郭崇韬求西川节度使，李继岌留物遣还',8,'又使',None,[('王宗弼','派子行赂、求官者'),('王承班','奉物行赂者'),('继岌','收留物并遣使者'),('崇韬','行赂对象')],when='925年十一月辛亥叙次',place='德阳唐行营',note='李继岌认物皆我家物为其回应，留下物不等批准宗弼任西川节度使；与承涓不同。')
relationship('王宗弼','王承班','父亲',8,'又使其子承班以蜀主后宫及珍玩赂继岌及郭崇韬，求西川节度使，','王宗弼是王承班父亲，复用既有同方向关系；不另建儿子反向重复。')
E=ev('yanxiao_wait_hanzhou','康延孝留汉州八日等都统',9,'李绍琛','以俟都统，',[('李绍琛','留待将领')],when='925年十一月丁未至甲寅叙次，主书称八日',place='汉州',note='时长照史载，不另行公历计算。')
E=ev('jiji_hanzhou_zongbi_audience','李继岌至汉州，王宗弼迎谒',9,'甲寅','王宗弼迎谒；',[('继岌','到达者'),('王宗弼','迎谒者')],when='925年十一月甲寅',place='汉州')
E=ev('jiji_arr_chengdu','李继岌至成都',9,'乙卯','至成都。',[('继岌','到达都统')],when='925年十一月乙卯',place='成都',note='至成都与后日正式受降、军队入城分开。')
claim('event',E,'time_original','旧史本纪同乙卯记魏王到西川城北。',9,'乙卯，魏王至西川城北。','支持至城外围的阶段，不强等大军入城。',source='jiuwudaishi-033-925-submission',relation='corroborates')
E=ev('shu_formal_surrender_ritual','李严引王宗衍与百官出降于升迁桥，以白衣衔璧牵羊舆榇等礼候命',9,'丙辰','号哭俟命。',[('李严','引导出降者'),('蜀主','行降礼者')],when='925年十一月丙辰',place='成都、升迁桥（主书）',note='出降礼与此前使者请降区分；升迁桥、升仙桥及其他叙法并列，不强定现代同一坐标。')
claim('event',E,'description','旧史蜀世家记十一月二十七日于成都北五里升仙桥行降礼。',9,'其月二十七日，魏王至成都北五里升仙橋，偽百官班於橋下，衍乘行輿至，素衣白馬，牽羊，草索系首，面縛銜璧，輿櫬於後。','升仙/升迁、素衣白马与主书礼装各存；不擅将阴历27转公历。',source='jiuwudaishi-136-925-surrender',relation='conflicts')
claim('event',E,'time_original','新史继岌传丙辰叙入成都及升仙桥受降。',9,'丙辰，入成都。王衍乘竹輿至昇仙橋，','主书丙辰出降、丁巳大军入城，新史入成都阶段叙法不同；昇仙简体显示升仙但原字留存。',source='xinwudaishi-014-jiji-conquest',relation='conflicts')
claim('event',E,'description','新史蜀世家写王宗衍君臣出降于七里亭。',9,'魏王繼岌至成都，衍君臣面縛輿櫬，出降于七里亭。','与升迁/升仙桥不同叙法，保留各出处，未证实同一地。',source='xinwudaishi-063-925-east-tour',relation='conflicts')
E=ev('jiji_chongtao_accept_release_shu','李继岌受璧，郭崇韬解缚焚榇承制释罪，蜀君臣拜谢',9,'继岌受','向拜谢。',[('继岌','受璧者'),('崇韬','解缚焚榇释罪者'),('蜀主','谢恩者')],when='925年十一月丙辰',place='成都受降处',note='承制释罪为此时行为，不提前推王宗衍926结局。')
claim('event',E,'description','旧史同记魏王受璧、郭解缚焚榇；补魏王郭崇韬李严向蜀君臣答拜。',9,'魏王下馬受其璧，崇韜釋其縛，及燔其櫬，衍率偽百官東北舞蹈謝恩。禮畢，拜，魏王、崇韜、李嚴皆答拜。','礼仪补充，答拜不另建臣属关系。',source='jiuwudaishi-136-925-surrender',relation='adds')
E=ev('tang_army_enters_chengdu_order','唐军入成都，郭崇韬禁侵掠，史载市不改肆',9,'丁巳','市不改肆。',[('崇韬','禁侵掠者')],when='925年十一月丁巳',place='成都',note='市场未改为史载描述，不断言整个征服过程零损失；渡江已有溺死。')
claim('event',E,'time_original','旧史蜀世家记十一月二十八日军队入成都。',9,'二十八日，王師入成都。','旧本纪亦丁巳入城，同阶段；不与先到城北混并。',source='jiuwudaishi-136-925-surrender',relation='corroborates')
claim('event',E,'description','旧史本纪同记丁巳大军入城，法令严峻、市场未变。',9,'丁巳，大軍入成都，法令嚴峻，市不易肆。','保持史家叙述范围。',source='jiuwudaishi-033-925-entry',relation='corroborates')
E=ev('shu_campaign_duration_and_spoils','史载伐蜀至克蜀七十日，得十节度六十四州二百四十九县及兵财',9,'自出师',None,[],when='925年伐蜀至十一月成都归降的统计',place='蜀境',note='兵三万是所得蜀兵，非出师唐军数；财货共千万为综合概数不同品项，不换算币值；七十日与两史七十五日并列。')
claim('event',E,'description','旧史本纪记平蜀七十五日，所得兵士三万、十节度州、六十四郡、二百四十九县。',9,'自興師凡七十五日，蜀平，得兵士三萬、兵仗七百萬、糧三百五十三萬、錢一百九十二萬貫、金銀共二十二萬兩、珠玉犀象二萬、紋錦綾羅五十萬，得節度州十、郡六十四、縣二百四十九。','天数异说保留；逐项只有钱贯、金银两等有明示单位，其他不补单位、不汇为同一价值。',source='jiuwudaishi-033-925-entry',relation='conflicts')
claim('event',E,'description','旧史蜀世家亦记自起师至入蜀城七十五日。',9,'自起師至入蜀城，凡七十五日。','统计端点写入蜀城；不可擅把主书七十当转录已证错。',source='jiuwudaishi-136-925-surrender',relation='conflicts')
claim('event',E,'description','新史继岌传记出师至降王宗衍七十五日，并评兵不血刃。',9,'自出師至降衍，凡七十五日，兵不血刃，自古用兵之易，未有如此。','兵不血刃为概括性评价，不覆盖主书战斗和渡江损失；统计端点各存。',source='xinwudaishi-014-jiji-conquest',relation='conflicts')
E=ev('gaojichang_reacts_shu_fall','高季昌闻蜀亡失匕箸自责，梁震以唐主益骄将亡相慰',10,'高季兴','其不为吾福！”',[('高季兴','闻讯自责者'),('梁震','出言相慰者')],when='925年十一月蜀亡后，确日未载',place='荆南',note='老夫之过为高自责，唐亡将为福是梁预测，不作为已实现因果或预录后唐灭亡。')
E=ev('mayin_requests_retirement_reassured','马殷闻蜀亡，上表称已营衡麓退居地愿还印保余龄，李存勖诏慰',10,'楚王殷',None,[('楚王殷','上表求退者'),('上','慰谕者')],when='925年十一月蜀亡后，确日未载',place='楚、衡麓、后唐朝廷',note='愿交印退居并未实际退位；菟裘为退居之喻。')
E=ev('yanxiao_resent_dong_close_chongtao','康延孝平蜀功多位在董璋上，因郭崇韬亲董多召议军事而不平',11,'平蜀','绍琛心不平，',[('李绍琛','功多、心不平者'),('董璋','位较下、常获召议者'),('崇韬','常召董议事者')],when='925年蜀平后、十二月表董前',place='蜀地唐军',note='功多与心态为史载评价；与郭善仅作此段亲近事实，不新建无期限盟友关系。')
claim('event',E,'description','新史康传同记康功多、董位在下，却独被郭召议而康不获问。',11,'蜀平，延孝功為多。左廂馬步軍都指揮使董璋位在延孝下，然特見重於郭崇韜。崇韜有軍事，獨召璋與計議，而不問延孝，','补董当时军职；不推其所有生涯总排名。',source='xinwudaishi-044-925-commanders',relation='corroborates')
E=ev('yanxiao_threatens_dong_execution','康延孝斥董璋依郭谋害自己，并威胁以军法斩董；董向郭告状',11,'谓璋曰','璋诉于崇韬。',[('李绍琛','责斥及威胁者'),('董璋','被威胁、诉者'),('崇韬','受诉者')],when='925年蜀平后',place='蜀地唐军',note='谋相倾害为康指控、斩公为威胁，不能录为已证密谋或董已死。')
E=ev('dong_dismiss_army_nominate_dongchuan','郭崇韬表董璋为东川节度使并解军职',11,'十二月','解其军职。',[('崇韬','表奏及解军职者'),('董璋','被表为东川帅、解原军职者')],when='925年十二月，主书确日未载',place='东川、后唐行营',note='表奏与朝廷正授分开；旧史另载壬戌正授时间。')
claim('event',E,'time_original','旧史本纪记十二月壬戌授董璋剑南东川节度副大使知节度事。',11,'十二月壬戌，以前雲州節度使李存敬為同州節度使；以同州節度使、檢校太保、同平章事李令德為遂州節度使；以邠州節度使、檢校太保董璋為劍南東川節度副大使、知節度事；','主书表奏未具日，旧本纪是授官，不能把壬戌无说明覆为郭表日；副大使知节度事为诏任原衔。此处连引同日授官以保存董条日期，但其他官职留待主线对应段录入。',source='jiuwudaishi-033-925-entry',relation='adds')
E=ev('yanxiao_nominates_renyuan_rebuked','康延孝不满董璋得东川，向郭提任圜为帅，被质问反邪后惧退',11,'绍琛愈怒',None,[('李绍琛','不满、提议及退者'),('崇韬','斥责者'),('任圜','被举为帅者'),('董璋','被反对的任用对象')],when='925年十二月董被表东川后',place='蜀地唐行营',note='任尚书结合前文工部尚书任圜复用，非新造任尚书；反邪是郭质问，未录康已反，更未提前录926兵变。')
E=ev('jiji_chongtao_office_imbalance','追叙伐蜀军务补署皆出郭崇韬，两府往来悬殊，李从袭等感耻',12,'初','从袭等固耻之。',[('帝','此前遣内官随军者'),('李从袭','随军内官、感耻者'),('继岌','都统府主'),('崇韬','制置补署决事者')],when='925年伐蜀期间追叙，确日未载',place='伐蜀唐军两府',note='初及终日概述为整个军务阶段，不强定十二月一日；任职派遣已见卷273，不重复当另次授官。')
claim('event',E,'description','旧史郭传同记军政皆出郭、继岌承命，李廷安李从袭吕知柔所管都统府冷清而感耻。',12,'其招懷製置，官吏補置，師行籌畫，軍書告諭，皆出於崇韜，繼岌承命而已。莊宗令內官李廷安、李從襲、呂知柔為都統府紀綱，見崇韜幕府繁重，將吏輻輳，降人爭先賂遺，都統府唯大將省謁，牙門索然，由是大為詬恥。','补内官列名但此前已录任职；不建由府门冷热推断的叛乱关系。',source='jiuwudaishi-057-chongtao-conquest',relation='corroborates')
E=ev('shu_gifts_chongtao_son_jiji_resentment','蜀贵臣大将争以宝货妓乐馈郭崇韬与郭廷诲，李继岌所得少使李从袭等更不平',12,'及破蜀',None,[('崇韬','受馈者'),('郭廷诲','郭子、受馈者'),('继岌','得少量物者'),('李从袭','更不平者')],when='925年蜀破后，确日未载',place='成都、唐军',note='不过匹马束帛等为主书相较概述，未核全部资产总账；馈妓乐不等婚配，也不直接作后来杀郭唯一原因。')
relationship('崇韬','郭廷诲','父亲',12,'及破蜀，蜀之贵臣大将争以宝货、妓乐遗崇韬及其子廷诲，','郭崇韬是郭廷诲父亲；廷誨简体廷诲，保留原字别名。')
claim('event',E,'description','新史郭传记王宗弼迁蜀主西宫，取其嫔妓珍宝奉郭崇韬及郭廷诲。',12,'軍至成都，宗弼遷衍于西宮，悉取衍嬪妓、珍寶奉崇韜及其子廷誨。','同父子受馈，补宗弼为具体馈者；该传前句称王衍弟宗弼与其他书亲属叙法需另核，不据其建确定兄弟关系。',source='xinwudaishi-024-925-gifts',relation='adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续1—12段；蜀君主王衍复用王宗衍，蜀太后为徐贤妃；请降、出降、释罪与军队入城分录；王宗弼自称留后及求帅非正式唐诏授官；承涓与承班不自动合并；昌/忠、升迁/升仙、绵州十/十一月及七十/七十五日分书并列；鹿关头据同段前文与旧传展示鹿头关，原字保留；中书待郎、大玄门待纸本；四官惑主为宗弼或降表归责，不作亡国唯因；主书溺死千余不因新史兵不血刃评价取消；李昊自言李绅后裔不立确定血亲；康威胁斩董及郭反邪质问不是已执行或已反；任圜提名不等当选，董表奏与朝授分开；梁震预测、马殷愿退不预录未来结果；两府及受馈为追叙，郭廷诲复用方向父亲关系规范。'
for n in range(1,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=925,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,13)],next_paragraph=Q[13]['id'],next_volume=274,supplements=supplements,coverage='卷274第1—12段，原文件6—17行；925年十一月蜀主返京、各州归降、宗弼夺权、渡绵江、正式降蜀及十二月东川任用和两府受馈失衡。卷273本年37段已完成，卷274尚余17正文段，925年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,13)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
