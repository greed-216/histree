# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 274, year 925, paragraphs 25–29."""
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
 ('tongjian-274-925-winter',YEAR/'part-02/sources/library/tongjian-274-925-winter','44b6be0e','司马光等'),
 ('tongjian-274-925-suspicion-continuation',P/'sources/library/tongjian-274-925-suspicion-continuation','3ebe2df2','司马光等'),
 ('tongjian-274-925-year-end',P/'sources/library/tongjian-274-925-year-end','3ebe2df2','司马光等'),
 ('jiuwudaishi-033-925-princes',P/'sources/library/jiuwudaishi-033-925-princes','3ebe2df2','薛居正等'),
 ('jiuwudaishi-051-cunmei-cunli',P/'sources/library/jiuwudaishi-051-cunmei-cunli','3ebe2df2','薛居正等'),
 ('jiuwudaishi-057-925-suspicions',P/'sources/library/jiuwudaishi-057-925-suspicions','3ebe2df2','薛居正等'),
 ('xinwudaishi-014-925-delayed-return',P/'sources/library/xinwudaishi-014-925-delayed-return','3ebe2df2','欧阳修'),
 ('xinwudaishi-024-925-treasury-accusation',P/'sources/library/xinwudaishi-024-925-treasury-accusation','3ebe2df2','欧阳修'),
 ('xinwudaishi-005-925-annals',OLD/'part-01/sources/library/xinwudaishi-005-925-annals','7c2351be','欧阳修'),
 ('xinwudaishi-066-chu-tea',ROOT/'content/books/zizhi-tongjian/vol-266/year-0908/part-03/sources/library/xinwudaishi-066-chu-tea','fe35a4a6','欧阳修等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v274-y0925-p025-p029',
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
for n in range(25, 30):
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
        citation = f'卷274·同光三年（925）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_274_0925_03_{len(B["claims"])+1:04d}'
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
        row['aliases']={'李存美':[],'李存礼':['李存禮'],'李存乂':[],'李存确':['李存確'],'向延嗣':[],'马彦珪':['馬彥珪'],'沈瑫':[]}.get(name,row['aliases'])
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
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
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
brothers=[('李存美','邕王'),('李存霸','永王'),('李存礼','薛王'),('李存渥','申王'),('李存乂','睦王'),('李存确','通王'),('李存纪','雅王')]
E=event('cunxu_enfeoffs_seven_brothers','李存勖封七位皇弟为王',25,Q[25]['text'],[('帝','册封者')]+[(name,'受封'+title) for name,title in brothers],when='925年闰月辛亥',place='后唐朝廷',note='主书存又，两史同日同睦王作存乂，校核显示李存乂而不改摘录；未据此推母系或具体出生年。')
claim('event',E,'description','新史本纪同闰月辛亥封七弟，睦王写存乂。',25,'閏月辛亥，封弟存美為邕王，存霸永王，存禮薛王，存渥申王，存乂睦王，存確通王，存紀雅王。','同七爵与日期，存又/存乂并列字校，非改名或繁简关系。',source='xinwudaishi-005-925-annals',relation='corroborates')
claim('event',E,'description','旧史本纪同辛亥封六位皇弟，未列薛王存礼，并记皇弟次序。',25,'辛亥，製皇第二弟存霸可封永王，第三弟存美可封邕王，第四弟存渥可封申王，第五弟存乂可封睦王，第六弟存確可封通王，第七弟存紀可封雅王。','本纪未列存礼不等断言其未封；列传另同年薛王可补，两层原文独立。',source='jiuwudaishi-033-925-princes',relation='conflicts')
claim('person',people['李存礼'],'description','旧史宗室传同记李存礼为李克用之子，同光三年封薛王。',25,'薛王存禮，武皇子，同光三年封。','补本纪遗漏，武皇指李克用；后续结局未知不提前填生死。',source='jiuwudaishi-051-cunmei-cunli',relation='corroborates')
for name,title in brothers:relationship('帝',name,'兄长',25,Q[25]['text'],'皇弟明确为李存勖之弟，方向李存勖是此人的兄长；不另建逆向弟弟重复边。存又按两史同爵校作存乂。')
E=ev('chongtao_anti_eunuch_advice','追叙郭崇韬向李继岌建议将来去宦官用士人，吕知柔窃听而内官愤恨',26,'郭崇韬素','宦官皆切齿。',[('崇韬','劝去宦官者'),('继岌','受劝者'),('吕知柔','窃听者')],year=None,when='925年末叙及此前私语，确年日未载',place='伐蜀行营',note='他日得天下为郭的将来建议，未证明继岌已即位或册立太子；騬马为去势马的比喻，不新增军马事件。')
claim('event',E,'description','新史郭传同记郭论以后继位当去宦官，李从袭等闻言切齿。',26,'崇韜素嫉宦官，嘗謂繼岌曰：「王有破蜀功，師旋，必為太子，俟主上千秋萬歲後，當盡去宦官，至於扇馬，亦不可騎。」繼岌監軍李從襲等見崇韜專任軍事，心已不平，及聞此言，遂皆切齒，思有以圖之。','必为太子为说话者预期，仍未作已册太子；扇/騬字分别保留，非正常繁简对应。',source='xinwudaishi-024-925-treasury-accusation',relation='corroborates')
E=ev('chongtao_sends_renyuan_zhangyun_bandits','蜀平后山林盗贼起，郭崇韬命任圜张筠分道招讨，因而留军未还',26,'时成都虽下','淹留未还。',[('崇韬','命分道招讨者'),('圜','受命招讨者'),('张筠','受命招讨者')],when='925年成都归降后、年末',place='蜀中山林、唐军',note='恐留后患为主书所述判断；盗贼未具名不造人物，招讨未等全部平定。')
claim('event',E,'description','旧史同记山林多盗、孟未至，郭令任圜张筠招抚而归期稍缓。',26,'時蜀土初平，山林多盜，孟知祥未至，崇韜令任圜、張筠分道招撫，慮師還後，部曲不寧，故歸期稍緩。','招抚/招讨用词各存，说明延迟的军政理由，不据内官指控认定此就是谋反。',source='jiuwudaishi-057-925-suspicions',relation='corroborates')
E=ev('xiangyansi_sent_urge_return_reception','李存勖遣向延嗣促还军，郭崇韬未郊迎且礼倨，使者发怒',26,'帝遣宦者','延嗣怒。',[('帝','遣使者'),('向延嗣','宦者、催军使者'),('崇韬','未郊迎者')],when='925年蜀平后催班师时',place='后唐朝廷至成都',note='未郊迎与使者发怒是此阶段，不能把班师迟延直接视为抗命叛国已证。')
claim('event',E,'description','新史郭传称向延嗣奉命劳军，非此句所称促班师。',26,'莊宗聞破蜀，遣宦官向延嗣勞軍，崇韜不郊迎，延嗣大怒，因與從襲等共構之。','同人任务叙法不同，新史继岌传又作促班师；保留各传，不据一个角色标签生成两名向延嗣。',source='xinwudaishi-024-925-treasury-accusation',relation='conflicts')
claim('event',E,'description','新史继岌传同记向延嗣催继岌班师，郭不迎而礼慢。',26,'遣宦者向延嗣趣繼岌班師。延嗣至成都，崇韜不出迎，及見，禮益慢，延嗣怒，','与主书促军一致，叙述视角写促继岌。',source='xinwudaishi-014-925-delayed-return',relation='corroborates')
E=ev('congxi_accuses_chongtao_tinghui_ambition','李从袭向向延嗣指郭专权、郭廷诲结交军将土豪并求蜀帅',26,'李从袭谓','大人宜善自为谋。',[('李从袭','提出指控者'),('向延嗣','听指控者'),('崇韬','被指专权者'),('郭廷诲','被指求帅者')],when='925年向延嗣至蜀后',place='成都',note='全部为李从袭陈述，近闻及转述不当郭廷诲已经真实密谋；魏王太子也为从袭所称，不填已册太子。原段被阅读块拆开，此摘录到前块末，后半另引用其原定位。')
E=ev('congxi_claims_army_guo_party_weep','李从袭续称诸将皆郭党、魏王身险，并与向延嗣相向垂泪',26,'今诸军将校','因相向垂涕。',[('李从袭','续述危惧者'),('向延嗣','共同垂泪者')],when='925年向延嗣至蜀时',place='成都',note='本句承连续原段李从袭向延嗣说话，阅读块首为闭引号；郭党及性命之忧是其指控与预测，不建立诸将为郭党实体关系。')
claim('event',E,'description','旧史同記李从袭言诸将皆郭党、魏王孤弱恐班师生乱，二人垂泪。',26,'今諸軍將校，無非郭氏之黨，魏王懸軍孤弱，一朝班師，必恐紛亂，吾屬莫知暴骨之所！」因相向垂涕。','郭党是从袭话，不确证全军派系；旧史上下文有从袭谓之，连续回查。',source='jiuwudaishi-057-925-suspicions',relation='corroborates')
E=ev('xiangyansi_returns_reports_liu_cunxu','向延嗣回报刘后，刘后泣诉求救继岌，李存勖因先后报告疑郭',26,'延嗣归','不能无疑。',[('向延嗣','还报者'),('刘后','泣诉者'),('帝','闻报疑郭者'),('崇韬','被疑者')],when='925年向延嗣还朝后',place='后唐朝廷',note='请救继岌之死是所忧未来危险，未作继岌已死；被疑不等郭反已证。')
E=ev('cunxu_reviews_shu_inventory','李存勖阅蜀府库簿，质问所获珍货为何少',26,'帝阅蜀府库','之微也？”',[('帝','阅簿质问者')],when='925年向延嗣回报后',place='后唐朝廷',note='人言无算及何微为帝基于传聞的质问，不等实际蜀财富总值已清点。')
claim('event',E,'description','新史郭传列向延嗣上蜀簿所得兵三十万、马九千五百、粮二百五十三万石等。',26,'延嗣還，上蜀簿，得兵三十萬，馬九千五百匹，兵器七百萬，糧二百五十三萬石，錢一百九十二萬緡，金銀二十二萬兩，珠玉犀象二萬，文錦綾羅五十萬匹。','此为新郭传簿数，前批主书及旧本纪兵三万、旧粮三百五十三万不同；统计对象、转录及单位差异待纸本，不混成总数或覆盖已有事实。',source='xinwudaishi-024-925-treasury-accusation',relation='conflicts')
E=ev('xiangyansi_accuses_guo_treasures_cunxu_angry','向延嗣声称郭父子收蜀珍货，报郭金银钱马数量，李存勖发怒',26,'延嗣曰：“臣闻','帝遂怒形于色。',[('向延嗣','报告及指控者'),('崇韬','被指收财者'),('郭廷诲','被指另收财者'),('帝','闻报发怒者')],when='925年阅蜀簿时',place='后唐朝廷',note='臣闻及数量均报告层次：金万两、银四十万两、钱百万缗、名马千匹不能当已核赃物清单。')
claim('event',E,'description','旧史同载向延嗣称金万两银四十万马千匹，另有王衍爱妓六十乐工百、廷诲金银十万两等。',26,'延嗣奏曰：「臣問蜀人，知蜀中寶貨皆入崇韜之門，言崇韜得金萬兩，銀四十萬，名馬千匹，王衍愛妓六十，樂工百，犀玉帶百。廷誨自有金銀十萬兩，犀玉帶五十，藝色絕妓七十，樂工七十，他財稱是。','旧句银四十万未明单位，未强补两；差异作报告清单分书，不并为更大精确数，未造未名女子实体。',source='jiuwudaishi-057-925-suspicions',relation='adds')
E=ev('cunxu_orders_meng_kill_guo_meng_requests_inquiry','李存勖嘱孟知祥到蜀诛郭，孟以国勋应先察，无异志则遣还，帝同意',26,'及孟知祥将行',None,[('帝','先令诛、后许察者'),('孟知祥','请先核察者'),('崇韬','拟处置对象')],when='925年孟知祥赴蜀前',place='洛阳',note='先命诛而同意先察的转折保留，未简化成无条件立即杀郭，也未录郭本年被杀。')
E=ev('meng_departs_luoyang_for_xichuan','孟知祥离洛阳赴蜀',27,'壬子','知祥发洛阳。',[('孟知祥','离京赴镇者')],when='925年闰月壬子',place='洛阳至蜀',note='与925前任命、抵洛及926到成都分别记录。')
E=ev('mayangui_sent_inspect_guo_return','李存勖遣马彦珪驰成都观察郭去就，若班师则止，否则与李继岌图处置',27,'帝寻复遣','则与继岌图之。',[('帝','派遣者'),('马彦珪','衣甲库使、使者'),('崇韬','察看对象'),('继岌','被要求协同者')],when='925年闰月孟发洛后，确日未载',place='后唐朝廷至成都',note='条件处置不是无条件已诛；衣甲库使为主书职名，新旧史中官说法另补。')
claim('event',E,'description','旧史同记派中官马彦珪视郭去就，归军则止、迟留则与继岌图。',27,'即令中官馬彥珪馳入蜀視崇韜去就，如班師則已，如實遲留，則與繼岌圖之。','同条件任务，没有此时已执行杀令。',source='jiuwudaishi-057-925-suspicions',relation='corroborates')
E=ev('mayangui_urges_liu_emergency_action','马彦珪向刘后称危急不能三千里外等回报，请决断',27,'彦珪见皇后','三千里外乎！”',[('马彦珪','劝立即处置者'),('刘后','受劝者')],when='925年闰月马使行前',place='后唐宫廷',note='危险在朝夕为使者转述判断，不当郭真实即将起兵已证。')
E=ev('cunxu_declines_immediate_guo_execution','刘后再次请李存勖决断，帝以传闻真假未明拒贸然果决',27,'皇后复言','岂可遽尔果决？”',[('刘后','再请者'),('帝','以传聞未實拒绝者')],when='925年闰月马使行前',place='后唐宫廷',note='与前段令孟察后决定以及遣马条件处理相连，不误称帝已正式无条件敕郭立即死。')
claim('event',E,'description','新史继岌传同记庄宗以传言未审拒便令果决。',27,'莊宗曰：「傳言未審，豈可便令果決？」','同拒绝阶段。',source='xinwudaishi-014-925-delayed-return',relation='corroborates')
E=ev('liu_independent_order_jiji_kill_guo','刘后未获帝同意，自写教给李继岌令杀郭',27,'皇后不得请','令杀崇韬。',[('刘后','自下教令者'),('继岌','教令接收对象'),('崇韬','拟杀对象')],when='925年闰月马使行前',place='后唐宫廷发往成都',note='皇后教令与皇帝敕不同，不在此提前录926正月实际杀郭；受命对象不等已接令执行。')
claim('event',E,'description','旧史同记皇后自为教与继岌令杀郭。',27,'皇后乃自為教與繼岌，令殺崇韜。','同教令性质。',source='jiuwudaishi-057-925-suspicions',relation='corroborates')
claim('event',E,'description','新史郭传写刘后教马彦珪矫诏魏王杀郭。',27,'彥珪以告劉皇后，劉皇后教彥珪矯詔魏王殺之。','郭传矫诏与主书/继岌传自为教叙法不同，保留差异；不直接覆盖成帝确有正式诏书。',source='xinwudaishi-024-925-treasury-accusation',relation='conflicts')
E=ev('mayangui_night_urges_meng_shihao','孟知祥到石壕，马彦珪夜宣诏催赴镇，孟叹乱将作并日夜兼行',27,'知祥行至',None,[('孟知祥','闻催、感叹及疾行者'),('马彦珪','夜叩门宣诏催赴者')],when='925年闰月赴蜀途中，确夜未载',place='石壕、赴蜀路',note='乱将作是孟预测，未当此时实际兵变；宣诏促孟赴镇与刘后杀郭教令分开。')
E=ev('chu_no_merchants_tax_background','追叙马殷得湖南后不征商旅，吸引四方商旅',28,'初','四方商旅辐氵奏。',[('楚王殷','施商旅政策者')],year=None,when='马殷据湖南以后追叙，确年未载',place='湖南',note='辐氵奏为底本拆字疑讹，展示吸引商旅不静默改原文；初不强定925。主书不征商旅与新史茶算税目不同并列。')
E=ev('chu_lead_iron_money_trade_background','马殷用高郁策铸铅铁钱，出境商旅换货，史载楚以余物易百货而富',28,'湖南地多','国以富饶。',[('楚王殷','用策铸钱者'),('高郁','军都判官、策者')],year=None,when='马殷据湖南以后追叙，确年未载',place='湖南',note='富饶与机制为主书政策叙述，不计算未经证据支持的经济增长率。')
claim('event',E,'description','新史楚世家补高郁劝铸铅铁钱，十枚当铜钱一枚。',28,'郁又諷殷鑄鉛鐵錢，以十當銅錢一。','新史比值补证独立，未认主书已说明比值；该段殷初背景无确年，不标925。',source='xinwudaishi-066-chu-tea',relation='adds')
claim('event',E,'description','新史同段又记令民造茶通商，收茶算税而岁入万计。',28,'又令民自造茶以通商旅，而收其算，歲入萬計。','与主书不征商旅涉及不同可能税目及叙次，保留并列，不无据认绝对零税或完全矛盾已解；万计未明单位不补货币单位。',source='xinwudaishi-066-chu-tea',relation='adds')
E=ev('chu_silk_tax_weaving_background','高郁令湖南民输税以帛代钱，史载未几织机大盛',28,'湖南民不事',None,[('高郁','以帛代钱纳税政策者')],year=None,when='马殷据湖南后政策追叙，确年未载',place='湖南',note='不事桑蚕与机杼大盛为作者概述，不认此前湖南绝无桑蚕，更不据未几推出具体间隔。')
E=ev('qianliu_sends_shentao_wuyue_title','钱镠遣沈瑫致吴书，告受玉册封吴越国王',29,'吴越王镠','告于吴。',[('镠','派使告号者'),('沈瑫','致书使者')],when='925年年末叙次，确日未载',place='吴越至吴',note='受玉册既有册封背景，本事件为告书，不另造925新一轮册封；两史未找到沈瑫此使直接补证。')
E=ev('wu_rejects_wuyue_letter_expels_envoy','吴以国名与己同而拒钱镠书，遣沈瑫还',29,'吴人以其','遣瑫还。',[('沈瑫','被遣还使者')],when='925年吴接吴越告号书后',place='吴朝廷',note='国号争议是吴方理由，未认两个政权都正式名吴越；主书未具拒函个人，不擅指定杨溥亲口下令。')
E=ev('wu_bans_wuyue_envoys_merchants','吴命边境不得通吴越使者及商旅',29,'仍戒境上',None,[],when='925年拒吴越书后',place='吴与吴越边境',note='禁令与实际贸易是否完全断绝分开；不延伸为925已开战。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续25—29正文段，保留第30结构标题不生成事件；存又据两史同日同睦王校作李存乂，旧本纪未列存礼用旧宗室传补；皇弟为李存勖弟，兄长方向具体，不推母系；郭去内官私语确年未知，郭说必为太子和从袭太子称谓不录继岌已经册立；招讨延军与内官指反并列，不以传聞认叛；主第26段横跨两个阅读块分别引用，不拼造底本；向报告财货数量不当已核赃物，新郭蜀簿兵粮数与旧本纪差异待核；帝令孟诛后许先察、遣马条件处理、拒贸杀与刘后自教分开，自教/矫诏异说并列，郭实际遇害留926；楚初追叙不强年，茶算与不征商旅税目并列，辐氵奏原字保留；钱受玉册背景已有，仅录告吴，吴拒函退使禁通商不等实际开战。'
for n in range(25,30):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
assert Q[30]['status']=='excluded_non_body_verified' and not Q[30]['event_keys']
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=274,year=925,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(25,30)],next_paragraph='zztj-v274-y0926-p001',next_volume=274,supplements=supplements,excluded_non_body=[dict(paragraph_id=Q[30]['id'],source_line=Q[30]['source_line'],text=Q[30]['text'],reason=Q[30]['review'])],coverage='卷274第25—29正文段，原文件30—34行；925年闰月七王封爵、郭受疑与帝后分别处置、孟赴蜀、楚商旅铅铁币帛税追叙、吴越告吴与吴拒禁。第30项为926帝纪标题已核排除，925两卷共66正文段，需完成全年公开审计后才标年完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(25,30)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
