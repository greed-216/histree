# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 924, paragraphs 49–60."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 77))
specs = [
 ('tongjian-273-924-shu-return',YEAR/'part-03/sources/library/tongjian-273-924-shu-return','485f4ca3','司马光等'),
 ('tongjian-273-924-autumn',P/'sources/library/tongjian-273-924-autumn','03a59b27','司马光等'),
 *[(key,P/'sources/library'/key,'03a59b27',author) for key,author in [
 ('jiuwudaishi-032-august','薛居正等'),('jiuwudaishi-061-anzhongba','薛居正等'),('jiuwudaishi-133-qian-jade','薛居正等'),('xinwudaishi-056-heze','欧阳修'),('xinwudaishi-067-qian-jade','欧阳修')]],
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0924-p049-p060',
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
for n in range(49, 61):
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
people, used, reused, supplements = {}, {}, {'tongjian-273-924-shu-return'}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷273·同光二年（924）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_273_0924_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'宗俦':'王宗俦','宗弼':'王宗弼','承班':'王承班','光嗣':'宋光嗣','承休':'王承休','重霸':'安重霸','循':'孔循','赵殷衡':'孔循','刘后':'刘夫人（李存勖妻）','李绍真':'霍彦威','李紹真':'霍彦威','汉主岩':'刘岩','楚王殷':'马殷','廷蕴':'张廷蕴','立':'杨立','匝':'周匝','俊':'陈俊','德源':'储德源','韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'王宗锷':['王宗鍔'],'李彦稠':['李彥稠'],'何泽':['何澤'],'景润澄':['景潤澄'],'王承班':[],'王承休':[],'安重霸':[],'曹义金':['曹義金'],'许寂':['許寂'],'娄继英':['婁繼英'],'张廷蕴':['張廷蘊'],'张弘祚':['張弘祚'],'杨立':['楊立'],'薛昭文':[],'周匝':[],'陈俊':['陳俊'],'储德源':['儲德源'],'李途':[],'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷273同光二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='924年本段；确日未载', note='', year=924, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_273_0924_' + code
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
        edge = 'participation_zztj_273_0924_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_273_0924_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quotes preserve the contiguous source paragraph.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('zonge_yangzhou_command','王宗衍以王宗锷为招讨马步使，率二十一军屯洋州',49,'八月','屯洋州；',[('蜀主','任命君主'),('王宗锷','右定远军使、招讨马步使')],when='924年八月戊辰',place='洋州',note='二十一军为军的编制数量，不推士兵总数或现代师团规模。')
ev('linsi_zhaowu_defence','林思谔任昭武节度使，戍利州以备唐',49,'乙亥',None,[('林思谔','长直马军使、新任节度')],when='924年八月乙亥',place='利州、昭武军',note='防备唐军不等唐已发动925征蜀，既有林思谔主体复用。')
ev('zhengyan_illness_report','王正言患风疾不能治事，景进多次向帝报告',50,'租庸使','屡以为言。',[('正言','租庸使、被记患病者'),('进','报告者')],when='924年八月改任前背景，确日未载',year=None,place='唐廷',note='病风为古书记病，不转换现代医学诊断；屡言不造次数。')
E=ev('qian_rent_director','孔谦由租庸副使、卫尉卿任租庸使',50,'癸酉','孔循为副使。',[('谦','受任者'),('循','同日受任副使')],when='924年八月癸酉',place='唐租庸使司',note='副职孔循复用旧主体，赵殷衡不是另造一人。')
claim('event',E,'description','旧史同八月癸酉任孔谦租庸使、孔循副使。',50,'癸酉，以租庸副使、守衛尉卿孔謙為租庸使，以右威衛上將軍孔循為租庸副使。','旧史上将军与主书大将军职名不同保留，未强合官阶。',source='jiuwudaishi-032-august',relation='corroborates')
claim('event',E,'description','旧史另记戊寅王正言罢使、守本官。',50,'戊寅，租庸使、守禮部尚書王正言罷使，守本官。','补前任罢使条；不把罢使日改成新任癸酉。',source='jiuwudaishi-032-august')
ev('kongxun_restores_name','追叙梁亡后赵殷衡恢复姓名孔循',50,'循即','复其姓名。',[('循','复名者')],year=923,when='923年梁亡之后，确日未载',place='梁唐之际',note='梁亡接已完成923主线，孔循既有赵殷衡别名；不再新建此人。')
E=ev('qian_heavy_levies','孔谦掌租庸后重敛急征供帝欲，主书记民不聊生',50,'谦自是','民不聊生。',[('谦','被记重敛者'),('帝','主书所述供欲对象')],when='924年八月受任之后的概述，确日未载',place='唐辖境',note='民不聊生是史书整体评价，不造户数、征收金额或现代税率。')
E=ev('qian_honor_finance','孔谦获丰财赡国功臣号',50,'癸未',None,[('谦','赐号对象')],when='924年八月癸未',place='唐廷')
claim('event',E,'description','旧史同癸未并记孔谦进封会稽县男。',50,'癸未，租庸使孔謙進封會稽縣男，仍賜豐財贍國功臣。','增封来自旧史独立书证；原文赡字繁体保留。',source='jiuwudaishi-032-august',relation='corroborates')
ev('yanchou_shu_mission','李存勖再遣李彦稠入蜀，九月抵成都',51,'帝复',None,[('帝','遣使君主'),('李彦稠','出使并到成都者')],when='924年九月己亥抵成都，遣使确日未载',place='唐至成都',note='抵达日不等遣使日；没有交换条件，不能补条约签署。')
ev('emperor_hunting_crop_damage','李存勖癸卯近郊狩猎，主书追记屡猎践禾',52,'癸卯','伤民禾稼，',[('帝','近郊猎者')],when='924年九月癸卯近郊猎，屡猎为前后概述',place='洛阳近郊',note='实际猎与持续背景同句分明，不把所有田损定一日；未推受害面积。')
E=ev('heze_hunting_remonstrance','何泽伏丛薄拦马劝谏赋敛与践禾，李存勖慰遣',52,'洛阳令','帝慰而遣之。',[('何泽','洛阳令、拦马谏者'),('帝','受谏慰遣者')],when='924年九月癸卯近郊猎时',place='洛阳近郊',note='请先赐死是劝谏话语，何泽没有当日被杀。')
claim('person',people['何泽'],'description','何泽为广州人。',52,'泽，广州人也。','籍贯为主书明示，不据籍贯定位出生坐标。')
claim('person',people['何泽'],'description','新史亦记何泽广州人、举进士为洛阳令。',52,'何澤，廣州人也。','同籍贯印证，新史此段本年未载进士举年。',source='xinwudaishi-056-heze',relation='corroborates')
claim('event',E,'description','新史何泽传记庄宗大笑，为之止猎，后拜仓部郎中。',52,'莊宗大笑，為之止獵。拜倉部郎中。','止猎与拜官为新史明确补叙，主书只慰遣；后拜未给确年，不生成924九月同日升官。',source='xinwudaishi-056-heze')
ev('khitan_bohai_no_gain','契丹攻渤海无功而返回',53,'契丹',None,[],when='924年九月本段，确日未载',place='渤海至契丹',note='接前批先攻辽东，无功不推确切战损，不等926灭渤海。')
ev('zongchou_zongbi_deposition_plot','王宗俦与王宗弼谋废立，王宗弼犹豫未决',54,'蜀前','未决。',[('宗俦','前山南节度兼中书令、谋议者'),('宗弼','参与谋议未决者'),('蜀主','被评失德及拟废君主')],when='924年九月王宗俦去世前，确日未载',place='前蜀',note='谋废立未决不能写成政变成功，失德属主书评价，不捏继位候选。')
ev('zongchou_dies','王宗俦忧愤而卒',54,'庚戌','忧愤而卒。',[('宗俦','亡故者')],when='924年九月庚戌',place='前蜀',note='忧愤为作者死因解释，未给医学原因或年龄。')
ev('zongbi_assures_eunuchs','王宗弼向宋光嗣景润澄等说王宗俦欲杀他们且已无患，众泣谢',54,'宗弼谓','俯伏泣谢。',[('宗弼','说话者'),('光嗣','枢密使、泣谢者'),('景润澄','枢密使、泣谢者'),('宗俦','王宗弼话语所指已故谋议者')],when='924年九月王宗俦卒后',place='前蜀',note='教杀语出王宗弼陈说，不另造宗俦已实施暗杀事件；故宗俦只是话语对象不在场。')
ev('chengban_fears_family','王承班听王宗弼告宦官言而忧自家难免',54,'宗弼子',None,[('承班','王宗弼子、评忧者')],when='924年九月王宗俦卒后本段',place='前蜀',note='难免为王承班预感，不是当年全家已遇害。')
relationship('宗弼','承班','父亲',54,'宗弼子承班','原文明示：王宗弼是王承班的父亲，未给母亲身份。')
ev('zhangwu_xialu_support','王宗衍任张武为峡路应援招讨使',55,'乙卯',None,[('蜀主','任命者'),('张武','前镇江节度使、受任者')],when='924年九月乙卯',place='前蜀峡路',note='任应援招讨不等已经在某战取胜。')
ev('youzhou_reports_khitan_sept','幽州上报契丹入寇',56,'丁巳',None,[],when='924年九月丁巳',place='幽州',note='独立告警，未名将帅、兵数及战果，不混前批五月围营。')
ev('provincial_finance_complaint','李存霸符习奏称租庸直指属州、使司不知而紊乱规程',57,'冬','有紊规程。”',[('李存霸','天平节度使、奏陈者'),('习','平卢节度使、奏陈者')],when='924年十月辛未',place='天平、平卢及唐廷',note='所奏属州称奉贴为奏章所陈，未造具体无名州守。')
ev('rent_direct_orders_defence','租庸使奏称近例皆直下属州',57,'租庸使奏','近例皆直下。',[('谦','本时租庸使、奏答者')],when='924年十月辛未奏陈后',place='唐租庸使司',note='官职依据前段八月已任孔谦，近例为租庸解释，不认皇帝已批准全政策。')
E=ev('provincial_routing_edict_unenforced','唐诏属州经本道奏、租庸征催牒观察使，主书记最终未行',57,'敕：',None,[('帝','改规诏令君主')],when='924年十月奏陈后下诏，确日未载',place='唐诸道与属州',note='本朝旧规及伪廷近事为诏书政治表述；敕虽发未行，不能画成实际行政流程已改。')
for start,end,value in [('自今支郡','本道腾奏，','诏令支郡非进奉须经本道转奏。'),('租庸征催','观察使。','诏令租庸征催须牒观察使。')]:claim('event',E,'description',value,57,span(57,start,end),'明确诏令内容，后句竟不行限制实际效果。')
ev('yiding_reports_khitan_oct','易定上报契丹入寇',58,'易定',None,[],when='924年十月本段，确日未载',place='易定',note='此段未名王都现场，不为地域主将自动加参战。')
E=ev('chengxiu_longwu_creation','王承休请选一万二千骁勇置四十军，任龙武都指挥使、安重霸副',59,'蜀宣徽','旧将无不愤耻。',[('承休','宣徽北院使、请置与新任指挥'),('重霸','裨将、新任副指挥')],when='924年十月本段，确日未载',place='前蜀驾下龙武军',note='一万二千、四十军为史载编制；优给、旧将愤耻为作者概述，未造具体愤耻者姓名。')
claim('event',E,'description','旧史安重霸传记选山东骁果数千、号龙武都，承休帅重霸副，俱在天水。',59,'仍於軍中選山東驍果，得數千人，號龍武都，以承休為軍帥，重霸副焉，俱在天水。','主书万二千四十军与旧传数千龙武都地点天水粒度不同，保留各书，未合计两支军；天水求镇是传记另顺序，不强当前已全移秦州。',source='jiuwudaishi-061-anzhongba',relation='conflicts')
E=ev('anzhongba_flatters_chengxiu','追叙安重霸以狡佞贿赂事王承休而获喜',59,'重霸，',None,[('重霸','被记事承休者'),('承休','受事并悦之者')],year=None,when='任龙武副之前背景，确日未载',place='前蜀',note='狡佞为作者评价，未编贿赂金额；主书去州疑字待核，不当繁简可解。')
claim('person',people['安重霸'],'description','旧史安重霸传记云州人，谄事王承休特见委信。',59,'安重霸，雲州人也。','主书去州、旧史云州字异并列，不凭自动转换改原字或新增同名实体。',source='jiuwudaishi-061-anzhongba',relation='conflicts')
claim('event',E,'description','旧史同记重霸谄事承休而被委信。',59,'重霸諂事承休，特見委信。','同人物关系背景印证，不建永久盟友关系。',source='jiuwudaishi-061-anzhongba',relation='corroborates')
ev('qian_tribute_title_continuation','钱镠恢复本朝职贡，唐沿梁官爵任命',60,'吴越王','而命之。',[('镠','吴越王、贡任对象'),('帝','任命者')],when='924年十月壬午任命，复贡确日未载',place='吴越与唐廷',note='因梁官爵不等925玉册已送达，贡复为前后背景。')
E=ev('qian_seeks_jade_privileges','钱镠厚贡并赂权要，求金印玉册与诏不名称国王，帝从其意',60,'镠厚',None,[('镠','请求者'),('帝','允请求君主')],when='924年十月本段议请，确日未载',place='唐廷、吴越',note='有司讲故事属于当时议论，不作普遍跨朝制度结论；曲从为批准不强定玉册金印实际交付日。')
claim('event',E,'description','新史亦记群臣反对玉册、郭崇韬尤不可，既而许之。',60,'莊宗下其議於有司，羣臣皆以謂非天子不得用玉冊，郭崇韜尤為不可，既而許之，乃賜鏐玉冊、金印。','传记连续写许与赐，未给确年交付；本批补议论，不抢后续正式册命。',source='xinwudaishi-067-qian-jade',relation='corroborates')
claim('event',E,'description','旧史补郭崇韬不容其僭、段徊为钱镠陈情后崇韬勉从。',60,'郭崇韜尤不容其僭，而樞密承旨段徊，奸幸用事，能移崇韜之意，曲為镠陳情，崇韜黽勉從之。','身份与过程来自旧史，奸幸僭为史书评语；不造金额或接受贿赂的确证链。',source='jiuwudaishi-133-qian-jade')
for name,role,quote in [('崇韬','初反对玉册国王封请，后勉从者','郭崇韜尤不容其僭'),('段徊','枢密承旨、为钱镠陈情者','曲為镠陳情')]:
 pk=person(name,60,role,quote,source='jiuwudaishi-133-qian-jade');ek='participation_zztj_273_0924_qian_jade_'+pk
 B['person_events'].append(dict(key=ek,person_key=pk,event_key=E,role=role,status='draft'))
 claim('person_event',ek,'role',next(x['name'] for x in B['people'] if x['key']==pk)+'：'+role+'。',60,quote,'旧史独立补证，主书未名该反对者，不当主书直接引用。',source='jiuwudaishi-133-qian-jade')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续49—60段；前蜀防唐非已征蜀；孔谦孔循受任同旧史癸酉，孔循赵殷衡复名同既有主体；重敛评价未造税率；王正言病风不现代诊断；何泽主书慰遣、新史止猎与后拜官分别补证未定同日；渤海无功还非灭国；谋废立未决、王承班忧惧非家亡；父亲方向明确；租庸规程诏竟未行；龙武主书万二千四十军旧史数千龙武都天水不同叙法，安重霸去州/云州待核；钱镠请求获允与后续交付册印分开，旧史段徊陈情补证不造赂金额。'
for n in range(49,61):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=924,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(49,61)],next_paragraph=Q[61]['id'],supplements=supplements,coverage='卷273第49—60段，原文件54—65行；前蜀备唐、租庸任官、使蜀谏猎、谋废立、契丹告警、征催规程、龙武建军与吴越册命请求。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(49,61)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
