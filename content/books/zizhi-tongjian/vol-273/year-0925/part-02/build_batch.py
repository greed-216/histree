# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 925, paragraphs 13–24."""
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
 ('tongjian-273-925-return',YEAR/'part-01/sources/library/tongjian-273-925-return','7c2351be','司马光等'),
 ('tongjian-273-925-summer',P/'sources/library/tongjian-273-925-summer','b76f75cc','司马光等'),
 ('xinwudaishi-005-925-annals',YEAR/'part-01/sources/library/xinwudaishi-005-925-annals','7c2351be','欧阳修'),
 *[(key,P/'sources/library'/key.replace('-925-','-'),'b76f75cc',author) for key,author in [
 ('jiuwudaishi-032-925-april','薛居正等'),('jiuwudaishi-032-925-may','薛居正等'),('jiuwudaishi-032-925-june','薛居正等'),('jiuwudaishi-033-july','薛居正等'),('jiuwudaishi-033-august','薛居正等'),('jiuwudaishi-071-luoguan','薛居正等'),('xinwudaishi-014-chenghui','欧阳修'),('xinwudaishi-024-luoguan','欧阳修'),('xinwudaishi-068-yanhan','欧阳修')]],
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0925-p013-p024',
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
people, used, reused, supplements = {}, {}, {'tongjian-273-925-return','xinwudaishi-005-925-annals'}, []

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
    ck = f'claim_zztj_273_0925_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'延翰':'王延翰','彦谦':'陈彦谦','审知':'王审知','苻习':'符习','少帝':'李祚','昭宗':'李杰','从珂':'李从珂','词':'何词','朱全忠':'朱温','令德':'朱令德','令锡':'李令锡','全义':'张全义','后':'刘夫人（李存勖妻）','格':'张格','温':'徐温','虔':'翟虔','宗俦':'王宗俦','宗弼':'王宗弼','承班':'王承班','光嗣':'宋光嗣','承休':'王承休','重霸':'安重霸','循':'孔循','赵殷衡':'孔循','刘后':'刘夫人（李存勖妻）','李绍真':'霍彦威','李紹真':'霍彦威','汉主岩':'刘岩','楚王殷':'马殷','廷蕴':'张廷蕴','立':'杨立','匝':'周匝','俊':'陈俊','德源':'储德源','韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'诚惠':['誠惠'],'罗贯':['羅貫'],'王延翰':[],'何词':['何詞'],'王允平':[],'李令锡':['李令錫'],'翟虔':[],'欧阳彬':['歐陽彬'],'关宏业':['關宏業'],'刘潜':['劉潛'],'王承骞':['王承騫'],'王鲁柔':['王魯柔'],'徐延琼':['徐延瓊'],'王宗锷':['王宗鍔'],'李彦稠':['李彥稠'],'何泽':['何澤'],'景润澄':['景潤澄'],'王承班':[],'王承休':[],'安重霸':[],'曹义金':['曹義金'],'许寂':['許寂'],'娄继英':['婁繼英'],'张廷蕴':['張廷蘊'],'张弘祚':['張弘祚'],'杨立':['楊立'],'薛昭文':[],'周匝':[],'陈俊':['陳俊'],'储德源':['儲德源'],'李途':[],'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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
E=ev('april_solar_eclipse','史书记四月初一日食',13,'夏',None,[],when='925年四月癸亥朔',place='原文未载观测地',note='仅录史载天象，不附加天罚或现代计算的日食参数。')
claim('event',E,'description','旧史同记四月癸亥朔日食。',13,'夏四月癸亥朔，日有蝕之。','同月日印证；未经现代天文核算。',source='jiuwudaishi-032-925-april',relation='corroborates')
E=ev('chenghui_supernatural_claim','追叙五台僧诚惠自称能降伏天龙、命风召雨',14,'初','命风召雨；',[('诚惠','自称有神异能力者')],year=None,when='925年四月叙及的前事，确年未载',place='五台',note='原书妖妄是作者判断，能力只是诚惠自称，不录为真实能力。')
claim('event',E,'description','新史亦记诚惠自称能降龙。',14,'又有僧誠惠，自言能降龍。','与前一胡僧分开，不能把于阗来僧的身份套给诚惠。',source='xinwudaishi-014-chenghui',relation='corroborates')
E=ev('chenghui_imperial_bowing','李存勖率后妃及皇族拜诚惠，郭崇韬不拜',14,'帝尊信之','独郭崇韬不拜。',[('帝','尊信、领拜者'),('诚惠','端坐受拜者'),('崇韬','不拜者')],year=None,when='925年四月叙及的前事，确日未载',place='原文未明确拜礼地点',note='后妃与皇弟皇子未逐一具名，不推定所有已知亲属都出席；群臣莫敢不拜与郭例外同录。')
claim('event',E,'description','新史记庄宗及后率诸子诸妃拜诚惠，独郭崇韬不拜。',14,'莊宗及后率諸子、諸妃拜之，誠惠端坐不起，由是士無貴賤皆拜之，獨郭崇韜不拜也。','同受拜场面；两书可能同源，不当独立确证。',source='xinwudaishi-014-chenghui',relation='corroborates')
E=ev('chenghui_prayer_fails','大旱中李存勖从邺都迎诚惠到洛阳祈雨，数旬不雨',14,'时大旱','数旬不雨。',[('帝','迎僧命祈雨者'),('诚惠','祈雨者')],when='925年四月本段，数旬而不雨，起止日未载',place='邺都至洛阳',note='迎送与祈雨结果同阶段；士民瞻仰不等所有人证实神异。')
E=ev('chenghui_flight_death','诚惠闻有人称祈雨无效将被焚，逃走后惭惧而死',14,'或谓',None,[('诚惠','闻言逃走、死亡者')],when='925年四月叙次，确日未载',place='原文未载逃亡及死亡地点',note='将焚是或人告知，不能认作皇帝已下焚僧令；惭惧而卒按主书叙述，不能推断医学死因。')
claim('person',people['诚惠'],'death_year','《通鉴》925年四月叙次记诚惠逃去后卒；确日未载。',14,'诚惠逃去，惭惧而卒。','只随本年叙次保留，不换算寿数。')
E=ev('zhao_guangyin_death','中书侍郎同平章事赵光胤卒',15,'庚寅',None,[('光胤','去世宰相')],when='925年四月庚寅',place='原文未载死亡地点')
claim('event',E,'description','旧史同日记赵光胤兼工部尚书、平章事卒，废朝三日。',15,'庚寅，中書侍郎兼工部尚書、平章事趙光胤卒，廢朝三日。','补兼官与废朝天数，不修改既有主体。',source='jiuwudaishi-032-925-april',relation='adds')
E=ev('empress_dowagers_separation_sorrow','曹太后与刘太妃分别后忧郁，太妃生病，太后相继遣送医药',16,'太后自','闻疾稍加，辄不食，',[('太后','忧念、遣医药者'),('太妃','患病者')],year=None,when='此前两人分别至925年五月太妃死前，起日未載',place='洛阳至北都途中',note='悲忧与成疾为作者叙述，不自行诊断心理疾病；不把情同兄弟变成血缘兄妹。')
E=ev('dowager_visit_refused_son_sent','曹太后欲探望太妃，李存勖劝止，遣李存渥等迎侍',16,'又谓帝曰','等往迎侍。',[('太后','请求往省者'),('帝','劝止、遣弟者'),('存渥','奉遣迎侍者'),('太妃','拟迎侍对象')],year=None,when='925年五月丁酉以前，确日未载',place='洛阳、北都间',note='迎侍命不等太妃已到洛阳，其他皇弟无名不造人；恩如兄弟是太后比喻。')
E=ev('liu_taifei_death_report','北都奏刘太妃薨',16,'五月','北都奏太妃薨。',[('太妃','去世太妃')],when='925年五月丁酉奏报',place='北都',note='主书以奏报纪日；旧史同日明确薨于晋阳，两种表述保留。')
claim('event',E,'description','旧史同丁酉记刘太妃薨于晋阳，李存勖废朝五日并在兴安殿行服。',16,'丁酉，皇太妃劉氏薨於晉陽，廢朝五日，帝於興安殿行服。','补死地、帝服丧；废朝五日不能与太后之后五日方食混用。',source='jiuwudaishi-032-925-may',relation='adds')
E=ev('cao_dowager_grief_illness_funeral_stop','曹太后闻太妃死悲哀不食并生病，欲赴葬再遭劝止',16,'太后悲哀',None,[('太后','悲哀、患病及欲赴葬者'),('帝','宽慰、劝止者')],when='925年五月太妃死后，确日未载',place='洛阳，拟赴北都',note='相随起居为帝宽慰，不把未成行探望或赴葬记成实际旅程。')
claim('event',E,'description','旧史记太后欲奔丧晋阳，百官上表请留而止。',16,'時皇太后欲奔喪於晉陽，百官上表請留，乃止。','补百官请留，与主书帝力谏并列。',source='jiuwudaishi-032-925-may',relation='adds')
E=ev('min_shenzhi_ill_yanhan_acting','王审知病重，命王延翰权知军府事',17,'闽王',None,[('审知','患病闽王、下命者'),('延翰','节度副使、权知军府者')],when='925年五月本段，确日未载',place='闽军府',note='权知军府是代理权责，此段王审知尚在，不提前记子已经称王。')
relationship('审知','延翰','父亲',17,'命其子节度副使延翰权知军府事。','A王审知是B王延翰父亲，不另建逆向儿子边。')
claim('person',people['王延翰'],'description','新史记王延翰字子逸，为王审知长子。',17,'延翰字子逸，審知長子也。','身份补证；同段926年受节度使及称王的后事留待主书按年继续。',source='xinwudaishi-068-yanhan',relation='adds')
E=ev('june_rain_after_drought','春夏大旱后六月壬申始雨',18,'自春夏',None,[],when='925年六月壬申',place='主书未明确地域，旧史记京师',note='不是全国所有地区同日起雨，也不把降雨归因诚惠祈雨。')
claim('event',E,'description','旧史同六月壬申记京师雨足，后转大雨水灾。',18,'壬申，京師雨足。自是大雨，至於九月，晝夜陰晦，未嘗澄霽，江河漂溢，堤防壞決，天下皆訴水災。','补雨足地点与后续灾害；后续长雨在主书九月仍会按序处理，不以旱后即丰收概括。',source='jiuwudaishi-032-925-june',relation='adds')
E=ev('summer_tower_plan','李存勖苦暑，听宦者劝说命王允平别建避暑楼',19,'帝苦','别建一楼以清暑。',[('帝','命建楼者'),('王允平','宫苑使、受命者')],when='925年六月本段，确日未载',place='禁中',note='宦者夸说唐宫楼观与公卿第舍是其话语，不当作已核建筑清单。')
E=ev('tower_internal_funds_reply','宦者称郭崇韬与孔谦担心用度，李存勖说将用内府钱',19,'宦者曰：“郭','遣中使语之曰：',[('帝','声称用内府钱者'),('崇韬','宦者话语中的阻建者'),('谦','宦者话语中的用度议论者')],when='925年六月营楼拟议阶段，确日未载',place='禁中',note='不把宦者评价认作郭孔实际同谋阻拦，也不推全部楼费确由内库支付。')
E=ev('chongtao_reminds_past_hardship','李存勖遣中使询暑，郭崇韬劝不忘河上艰难',19,'今岁盛暑','帝默然。',[('帝','传话、听后沉默者'),('崇韬','劝谏者')],when='925年六月拟建避暑楼时，确日未载',place='洛阳宫廷',note='昔河上梁战是对话中的前事，不新增925年梁军对峙；暑气自消为劝喻非气象结论。')
E=ev('tower_works_ten_thousand_laborers','李存勖终命王允平营楼，史载日役万人、所费巨万',19,'宦者曰：“崇韬之第','所费巨万。',[('帝','坚持营楼者'),('王允平','主持营建者')],when='925年六月本段，确日未载',place='禁中避暑楼',note='人数与费用为原书概数；巨万无明确单位，不造银两金额；日役不是整个工程仅一万人次。')
E=ev('tower_work_suspension_rejected','郭崇韬以两河灾害军食不足请暂停营楼，李存勖不听',19,'崇韬谏曰',None,[('崇韬','请息役者'),('帝','拒绝者')],when='925年六月营楼本段，确日未载',place='宫廷、两河',note='军食不充据郭所言保留；拒谏不等楼已竣工。')
E=ev('horse_requisition_for_shu','李存勖为伐蜀诏天下括市战马',20,'帝将',None,[('帝','颁诏者')],when='925年六月辛卯',place='诏令天下',note='将伐是筹备，不是本日已攻蜀；括市同时有征集和购买语义，不一概改成无偿没收。')
claim('event',E,'description','旧史同辛卯诏括天下私马。',20,'辛卯，詔括天下私馬，','只引旧史正文；五代会要及三楚新录夹注非本阶段新增来源。',source='jiuwudaishi-032-925-june',relation='corroborates')
E=ev('chen_yanqian_illness_xu_gifts','陈彦谦患病，徐知诰担心其遗言涉及继嗣，相继赠医药金帛',21,'吴镇海','相属于道。',[('彦谦','镇海判官、楚州团练使、患病者'),('徐知诰','担心继嗣并送礼者')],when='925年六月本段，确日未载',place='吴，楚州及往来途中',note='徐知诰复用李昪；恐遗言及继嗣是主书所叙担心，不说已经改立其人。')
E=ev('chen_yanqian_final_succession_letter','陈彦谦临终密遗徐温，请以亲生子为嗣',21,'彦谦临终',None,[('彦谦','临终建言者'),('温','接受建言、被劝用所生子者')],when='925年六月叙次，确日未载',place='吴',note='底本密留中遗徐温的中字疑有转录问题，保留原字待纸本，不擅改书字；遗言与请求内容明确。所生子指徐温子，未名不擅填徐知询或徐知训，只是请求，不是继嗣已获改变。')
E=ev('siyuan_dowager_visit_denied','李嗣源以边事稍弭请入朝省曹太后，李存勖不许',22,'太后疾甚','帝不许。',[('太后','病重的拟探视对象'),('嗣源','成德节度使、请省者'),('帝','拒绝者')],when='925年七月甲午',place='成德至洛阳拟议',note='边事稍弭是表求理由，不推契丹战争全面结束；未实际入朝。')
E=ev('cao_dowager_death','曹太后殂，李存勖哀毁过甚五日才进食',22,'壬寅',None,[('太后','去世者'),('帝','居丧者')],when='925年七月壬寅',place='主书未载，旧史长寿宫',note='五日方食不是太妃五月废朝五日；哀毁过甚是主书评价。')
claim('event',E,'description','旧史同壬寅记皇太后崩于长寿宫，出遗令。',22,'壬寅，皇太后崩於長壽宮，帝執喪於內，出遺令以示於外。','补死地及遗令，不补未见遗令内容。',source='jiuwudaishi-033-july',relation='adds')
claim('event',E,'time_original','新史同七月壬寅记皇太后崩。',22,'秋七月壬寅，皇太后崩。','三书同纪时；注语不当另一事实。',source='xinwudaishi-005-925-annals',relation='corroborates')
E=ev('luoguan_appointment_retrospect','追叙罗贯由礼部员外郎为河南令，得到郭崇韬赏识',23,'初','用为河南令。',[('罗贯','受用为县令者'),('崇韬','赏识者')],year=None,when='925年八月罗贯被杀之前，确年未载',place='河南县',note='县河南与河南府、今河南省区别，不因同名合并职权。')
claim('person',people['罗贯'],'description','旧史记罗贯籍贯不知，进士及第，累历台省，礼部员外郎出为河南令。',23,'羅貫，不知何許人。進士及第，累曆台省官，自禮部員外郎為河南令。','籍贯保持未知，不因任河南令填河南出生。',source='jiuwudaishi-071-luoguan',relation='adds')
E=ev('luoguan_rejects_solicitations','罗贯不避权豪，拒伶宦请托，将书交郭崇韬奏报',23,'为政','由是伶宦切齿。',[('罗贯','拒绝请托者'),('崇韬','收书奏报者')],year=None,when='任河南令后至925年八月案前，确日未载',place='河南县、宫廷',note='伶宦没有具名，不套景进或王允平；切齿指作者所叙怨恨。')
claim('event',E,'description','新史亦记罗贯不报宦官伶人求请之书，交郭崇韬，郭数次奏言。',23,'宦官、伶人有所求請，書積几案，一不以報，皆以示崇韜。崇韜數以為言，','同过程印证，不把所有请托具体内容补造。',source='xinwudaishi-024-luoguan',relation='corroborates')
E=ev('quanyi_empress_slanders_luoguan','张全义恶罗贯高伉，遣婢诉皇后，皇后与伶宦共同毁谤',23,'河南尹','帝含怒未发。',[('全义','河南尹、使婢诉者'),('后','参与毁谤皇后'),('罗贯','受毁谤者'),('帝','含怒者')],year=None,when='925年八月下狱以前，确日未载',place='河南府、宫廷',note='女使未名不造人物；高伉与毁是原书评价，不推不可见全部动机。')
claim('event',E,'description','旧史记罗贯不循府尹庇护，张全义经女使向刘皇后进言，宦官又说其短。',23,'全義怒，因令女使告劉皇后從容白於莊宗，宦官又言其短，莊宗深怒之。','与主书相应，刘皇后复用既有人物。',source='jiuwudaishi-071-luoguan',relation='corroborates')
E=ev('luoguan_arrest_torture','李存勖视坤陵遇泥泞坏桥，问责河南令罗贯，下狱拷掠',23,'会帝','体无完肤，',[('帝','查问并令下狱者'),('罗贯','被捕受刑者')],when='925年八月癸未杀罗贯前一日，原文未写干支',place='寿安坤陵道路、河南狱',note='根据明日关联保留前一日，旧史庚辰幸陵另记在前不混为捕日；狱吏未名。')
claim('event',E,'description','旧史列传补罗贯辩称未奉命、请求查明受命主者，府吏拷笞促其伏款。',23,'奏曰：「臣初不奉命，請詰稟命者。」','是罗贯答辩，不当全部责任已经裁定；旧史主者稟命与新史詰主者异文保留。',source='jiuwudaishi-071-luoguan',relation='adds')
E=ev('luoguan_death_order_chongtao_remonstrance','李存勖传诏杀罗贯，郭崇韬以罪不至死及用法不平谏阻无效',23,'明日','崇韬不得入。',[('帝','下死命、拒谏者'),('罗贯','受死命者'),('崇韬','劝谏者')],when='925年八月癸未，承明日杀令',place='宫廷、河南狱',note='任公裁之不是实际授予无条件赦免；随后闭门及贯死表明谏未救，不造郭任意裁决已生效。')
claim('event',E,'description','旧史列传补郭崇韬请俟款状上奏，由所司议谳依朝典处理。',23,'貫縱有死罪，俟款狀上奏，所司議讞，以朝典行之，死當未晚。','郭请求司法程序，不能表示既已查有死罪。',source='jiuwudaishi-071-luoguan',relation='adds')
claim('event',E,'description','新史亦记郭崇韬请求具狱行法于有司，闭门不得再谏。',23,'貫雖有罪，當具獄行法于有司。','同程序性劝谏，条件语非既判有罪。',source='xinwudaishi-024-luoguan',relation='corroborates')
E=ev('luoguan_execution_body_exposed','罗贯终被杖杀、暴尸府门，史载远近称冤',23,'贯竟死',None,[('罗贯','被杀、暴尸者')],when='925年八月癸未',place='河南府门',note='杖杀日期据本段开句，远近冤之为史书记载舆情，不补现代司法结论。')
claim('event',E,'time_original','本段以八月癸未杖杀河南令罗贯纪时。',23,'八月，癸未，杖杀河南令罗贯。','追叙在其后，保持结果日期与追叙开始日期不同。')
claim('event',E,'description','旧史本纪记先长流崖州，旋委河南府决杖处死，及死称冤。',23,'癸未，河南縣令羅貫長流崖州，尋委河南府決痛杖一頓，處死，坐部內橋道不修故也。及死，人皆冤之。','补先流后死命令，不把罗贯已抵崖州录为旅行事件。',source='jiuwudaishi-033-august',relation='adds')
claim('event',E,'description','旧史列传亦记伏法曝尸府门，远近有冤痛之声。',23,'即令伏法，曝屍於府門，冤痛之聲，聞於遠邇。','本纪列传属同书不是独立两证。',source='jiuwudaishi-071-luoguan',relation='corroborates')
claim('event',E,'time_original','新史亦记八月癸未杀河南县令罗贯。',23,'八月癸未，殺河南縣令羅貫。','同日印证。',source='xinwudaishi-005-925-annals',relation='corroborates')
E=ev('wuyue_investiture_envoy','李德休等奉遣赐吴越王玉册金印及红袍御衣',24,'丁亥',None,[('李德休','吏部侍郎、奉遣使者'),('镠','吴越王、受赐对象')],when='925年八月丁亥',place='后唐至吴越',note='遣使不等本日已经抵吴越完成册礼；其余使者无名不造人。')
claim('event',E,'description','旧史六月丁丑先诏吴越王册礼改用玉册，郭崇韬以为不可，段徊赞成。',24,'丁丑，詔吳越王錢鏐將行冊禮，準禮文合用竹冊，宜令所司修製玉冊。時郭崇韜秉政，以為不可，樞密承旨段徊讚其事，故有是命。','补此前玉册筹备，仅正文；八月派使与六月制册是两个阶段，不把前事当八月决定。',source='jiuwudaishi-032-925-june',relation='adds')
claim('event',E,'description','旧史八月本纪诏以黄金铸吴越王印，文为吴越国王之印。',24,'詔有司，吳越王印宜以黃金鑄成，其文曰「吳越國王之印」。','补制印规格，承八月本纪叙次；不推印已送达。',source='jiuwudaishi-033-august',relation='adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续13—24段；日食仅史载不作天罚；诚惠自称与能力验证分开，或人将焚非已下诏；太后、太妃复用曹氏刘氏，情同兄弟非血亲，欲省及奔丧均未成行；太妃死以奏日、旧史死地并列；王延翰代理军府不提前称王；降雨不归僧功，日役万人所费巨万保留概数；内府钱是帝所言不推实付；陈彦谦请徐温所生子继嗣不指定未名儿子；李嗣源省太后遭拒非入朝；罗贯追叙不强定925任命，不把流崖州命令认实际到达；郭请程序非既判有罪；吴越玉册金印分筹备与遣使，不记送达。'
for n in range(13,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=925,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,25)],next_paragraph=Q[25]['id'],supplements=supplements,coverage='卷273第13—24段，原文件96—107行；925年四月至八月，日食、诚惠祈雨、赵光胤卒、太妃太后病逝、王延翰代理、旱雨、营楼、括马、吴继嗣遗言、罗贯案、吴越册赐。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(13,25)],supplement_search_gaps=[dict(paragraph_id=Q[21]['id'],note='检索两五代史陈彦谦/陳彥謙等字形未得直接补证，仅主书引文；未扩大到暂缓专门史籍。')]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
