# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 924, paragraphs 61–76."""
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
 ('tongjian-273-924-autumn',YEAR/'part-05/sources/library/tongjian-273-924-autumn','03a59b27','司马光等'),
 ('tongjian-273-924-year-end',P/'sources/library/tongjian-273-924-year-end','f4a1df9b','司马光等'),
 *[(key,P/'sources/library'/key,'f4a1df9b',author) for key,author in [
 ('jiuwudaishi-032-yique-hunt','薛居正等'),('jiuwudaishi-032-december','薛居正等'),('jiuwudaishi-032-cunxian-report','薛居正等'),('jiuwudaishi-053-cunxian-final','薛居正等'),('jiuwudaishi-032-lingxi-office','薛居正等'),('xinwudaishi-014-adopted-father','欧阳修'),('xinwudaishi-045-youqian-privileges','欧阳修')]],
 ('jiuwudaishi-061-anzhongba',YEAR/'part-05/sources/library/jiuwudaishi-061-anzhongba','03a59b27','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0924-p061-p076',
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
for n in range(61, 77):
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
people, used, reused, supplements = {}, {}, {'tongjian-273-924-autumn','jiuwudaishi-061-anzhongba'}, []

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
    ck = f'claim_zztj_273_0924_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'朱全忠':'朱温','令德':'朱令德','令锡':'李令锡','全义':'张全义','后':'刘夫人（李存勖妻）','格':'张格','温':'徐温','虔':'翟虔','宗俦':'王宗俦','宗弼':'王宗弼','承班':'王承班','光嗣':'宋光嗣','承休':'王承休','重霸':'安重霸','循':'孔循','赵殷衡':'孔循','刘后':'刘夫人（李存勖妻）','李绍真':'霍彦威','李紹真':'霍彦威','汉主岩':'刘岩','楚王殷':'马殷','廷蕴':'张廷蕴','立':'杨立','匝':'周匝','俊':'陈俊','德源':'储德源','韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'李令锡':['李令錫'],'翟虔':[],'欧阳彬':['歐陽彬'],'关宏业':['關宏業'],'刘潜':['劉潛'],'王承骞':['王承騫'],'王鲁柔':['王魯柔'],'徐延琼':['徐延瓊'],'王宗锷':['王宗鍔'],'李彦稠':['李彥稠'],'何泽':['何澤'],'景润澄':['景潤澄'],'王承班':[],'王承休':[],'安重霸':[],'曹义金':['曹義金'],'许寂':['許寂'],'娄继英':['婁繼英'],'张廷蕴':['張廷蘊'],'张弘祚':['張弘祚'],'杨立':['楊立'],'薛昭文':[],'周匝':[],'陈俊':['陳俊'],'储德源':['儲德源'],'李途':[],'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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
ev('wu_white_sand_review','杨溥至白沙观楼船，改白沙名迎銮镇',61,'吴王','曰迎銮镇。',[('吴王','吴君主、观船改名者')],when='924年十月本段，确日未载',place='白沙、迎銮镇',note='观楼船不等发动战役；镇名改称有原文，未核具体坐标。')
ev('xuwen_visits_wu','徐温从金陵来朝杨溥',61,'徐温自','来朝，',[('温','来朝者'),('吴王','吴君主受朝者')],when='924年十月本段，确日未载',place='金陵至吴朝',note='未记具体抵达城，不按观船地点自动定位整个宫廷。')
ev('zhai_surveillance_background','追叙徐温任翟虔为阁门宫城武备等使监控杨溥起居',61,'先是','防制王甚急。',[('温','任亲吏者'),('虔','监控者'),('吴王','受防制君主')],year=None,when='此次来朝前的背景，确年未载',place='吴宫',note='不把先是强定924任职日，防制为主书描述。')
ev('wupu_zhai_complaint','杨溥以避翟虔父名的雨水说法向徐温诉限制宫宗所需',61,'至是','多不获。”',[('吴王','陈诉者'),('温','受诉者'),('虔','被指无礼者')],when='924年十月徐温来朝时',place='吴朝',note='翟父雨是王说明的避讳话语，未给父完整名，不凭雨一字建人。')
ev('zhai_exile_fuzhou','徐温请斩翟虔，杨溥认为过重，翟虔改徙抚州',61,'温顿首',None,[('温','谢罪请斩者'),('吴王','改准远徙者'),('虔','被徙者')],when='924年十月本段',place='抚州',note='请斩未施行，不能记录翟虔924被杀。')
ev('ouyang_bin_tang_visit','王宗衍遣翰林学士欧阳彬聘唐，并遣李彦稠东还',62,'十一月',None,[('蜀主','遣使君主'),('欧阳彬','翰林学士、来聘使者'),('李彦稠','唐使、被遣还者')],when='924年十一月本段，确日未载',place='前蜀至唐',note='遣还不是当日已抵洛阳；来聘亦未给抵达确日。')
claim('person',people['欧阳彬'],'description','欧阳彬是衡山人。',62,'彬，衡山人也。','史载籍贯，未核现代坐标。')
E=ev('yique_hunt_taizu_tomb','李存勖率亲军猎伊阙，命从官拜朱温墓',63,'癸卯','梁太祖墓。',[('帝','猎及命拜者'),('朱全忠','被拜已故梁太祖墓主')],when='924年十一月癸卯',place='伊阙、梁太祖墓',note='朱全忠、梁太祖复用朱温，本事件为墓主对象非死人现场参与；未自动画墓坐标。')
claim('event',E,'description','旧史同癸卯记畋伊阙、侍卫万余骑从、命拜梁祖陵。',63,'癸卯，帝畋於伊闕，侍衛金槍馬萬餘騎從，帝一發中大鹿。是日，命從官拜梁祖之陵，物議非之。','补万余为史载约数，一发中鹿为旧史叙事；物议非之属旧史评价。',source='jiuwudaishi-032-yique-hunt',relation='corroborates')
E=ev('hunt_cliff_casualties','伊阙连日险地围猎致士卒坠谷死亡折伤甚众',63,'涉历','甚众。',[('帝','连续围猎君主')],when='924年十一月癸卯至丙午围猎期间',place='伊阙附近山崖谷',note='甚众未给数，不造死亡数量；连续猎不能简化为一夜同一点。')
claim('event',E,'description','旧史亦记骑士围山入夜，坠崖谷死伤甚众。',63,'時騎士圍山，會夜，顛墜崖穀，死傷甚眾。','同叙死伤，不推伤亡比例。',source='jiuwudaishi-032-yique-hunt',relation='corroborates')
E=ev('yique_hunt_returns','李存勖丙午返宫',63,'丙午',None,[('帝','还宫者')],when='924年十一月丙午',place='洛阳宫')
claim('event',E,'description','旧史记丙午再令卫兵分猎，当夜归京、六街火炬如昼。',63,'是夜，方歸京城，六街火炬如晝。','补归京夜间景象，不推行政宵禁解除。',source='jiuwudaishi-032-yique-hunt',relation='corroborates')
ev('guan_wuwei_garrison_recall','前蜀因唐修好罢威武城戍，召关宏业等二十四军回成都',64,'蜀以','还成都。',[('蜀主','罢戍召还君主'),('关宏业','被召还军将')],when='924年十一月本段，确日未载',place='威武城至成都',note='二十四军为编制，未算人数；修好因果按主书记，不认两国永久结盟。')
ev('liu_wuding_wuxing_recall','前蜀罢武定武兴招讨，召刘潜等三十七军',64,'戊申',None,[('蜀主','罢招讨君主'),('刘潜','被罢招讨军将')],when='924年十一月戊申',place='武定、武兴',note='主书仅载罢而未该句明示抵成都，标题不填实际归到日期。')
E=ev('youqian_iron_charter','朱友谦获赐铁券，诸子胜衣即拜官，主书记宠冠列藩',65,'丁巳',None,[('李继麟','护国节度使、受铁券者'),('令德','被记节度使之子'),('令锡','被记节度使之子')],when='924年十一月丁巳赐铁券，诸子任官为本段概述',place='唐廷、护国军',note='胜衣仅年龄描述不推具体年岁；子官概述不等此日第一次授令德节度，前批已录其同州任职。')
claim('event',E,'description','新史记明年赐朱友谦铁券恕死，子令德遂州、令锡忠武，诸子将校刺史十余。',65,'明年，加守太師、尚書令，賜鐵券恕死罪。以其子令德為遂州節度使，令錫忠武軍節度使，諸子及其將校為刺史者十餘人，恩寵之盛，時無與比。','明年承923入洛是924；官任为该传综合，不把925实移遂州提前生成924到镇事件；十余为传约数不新增匿名人。',source='xinwudaishi-045-youqian-privileges',relation='corroborates')
claim('person',people['李令锡'],'description','旧史六月丙戌李令锡由顺义军节度移许州节度。',65,'丙戌，以順義軍節度使李令錫為許州節度使','既有任官补身份，非本批同十一月新任；李令锡全名据旧史，不造无出处的朱姓改名过程。',source='jiuwudaishi-032-lingxi-office')
relationship('李继麟','令德','父亲',65,'以其子令德、令锡','朱友谦是朱令德父亲，沿已有关系；赐姓名李继麟复用。')
relationship('李继麟','令锡','父亲',65,'以其子令德、令锡','朱友谦是李令锡父亲；不因父姓原朱擅加子之原名。')
ev('weizhou_khitan_report','蔚州上报契丹入寇',66,'庚申',None,[],when='924年十一月庚申',place='蔚州',note='未名将帅、战损，不填自动地域人物。')
ev('chengqian_tianxiong_recall','前蜀罢天雄招讨，召王承骞等二十九军回成都',67,'辛酉',None,[('蜀主','罢招讨召还君主'),('王承骞','被召还军将')],when='924年十一月辛酉',place='天雄至成都',note='罢招讨与随后任节度分开，不把同称天雄误同一个指挥已先授。')
ev('zhangge_chancellor_again','张格以右仆射兼中书侍郎同平章事',68,'十二月','同平章事。',[('蜀主','任命者'),('格','再次用相者')],when='924年十二月乙丑朔',place='前蜀')
ev('lurou_oppresses_zhang_background','追叙张格得罪时中书吏王鲁柔乘危困窘之',68,'初','乘危窘之；',[('格','先前得罪者'),('王鲁柔','被记乘危者')],year=None,when='张格先前得罪期间，确年未载',place='前蜀',note='初背景不重定924，未明具体受罚内容。')
ev('zhangge_kills_lurou','张格再为相用事后杖杀王鲁柔',68,'及再','杖杀之。',[('格','杖杀者'),('王鲁柔','被杀者')],when='924年十二月再次拜相后，确日未载',place='前蜀',note='已实施杖杀，与许寂预测后祸分开。')
ev('xuji_warns_zhangge','许寂批评张格才高识浅，认为杀鲁柔将引祸',68,'许寂',None,[('许寂','评议者'),('格','所评对象'),('王鲁柔','已死所举对象')],when='924年十二月王鲁柔被杀后',place='前蜀',note='预测不是当前张格已遭报复，话语对象不等在场共议。')
ev('chengxun_jinzhou_recall','前蜀罢金州屯戍，召王承勋等七军回成都',69,'蜀主',None,[('蜀主','撤戍召还君主'),('王承勋','被召还军将')],when='924年十二月本段，确日未载',place='金州至成都',note='七军不推兵员总数。')
E=ev('siyuan_guard_troops_north','李嗣源奉命率宿卫兵三万七千赴汴州继往幽州御契丹',70,'己巳',None,[('嗣源','宣武节度使、率兵北征者')],when='924年十二月己巳奉命',place='汴州至幽州',note='命令与计划行军，不能定己巳已同日抵幽；三万七千照史载未外推军额。')
claim('event',E,'description','旧史同己巳正文记诏李嗣源归镇，另戊子记奏部署大军自宣武北征。',70,'己巳，詔汴州節度使李嗣源歸鎮。','补归镇诏；夹注引通鉴不能作独立三万七千确证，北征奏报另日期。',source='jiuwudaishi-032-december',relation='corroborates')
claim('event',E,'description','旧史戊子记李嗣源奏部署军由宣武北征。',70,'戊子，李嗣源奏，部署大軍自宣武軍北征。','区分己巳命与戊子奏，不替换主书命日。',source='jiuwudaishi-032-december')
ev('emperor_queen_visit_quanyi','李存勖与刘皇后访张全义，张全义陈献',71,'庚午','大陈贡献；',[('帝','来访君主'),('后','来访皇后'),('全义','设献主人')],when='924年十二月庚午',place='张全义第')
E=ev('queen_adopts_quanyi','刘皇后请父事张全义，获帝许可并拜养父，全义复贡谢恩',71,'酒酣','复贡献谢恩。',[('后','请拜父者'),('全义','辞而受拜者'),('帝','许可者')],when='924年十二月庚午',place='张全义第',note='妾幼失父母是刘后的自述，本条不作其亲父已死独立事实；养父不同亲父。')
claim('event',E,'description','旧史同庚午记帝命皇后拜张全义为养父。',71,'帝命皇后拜全義為養父，全義惶恐致謝，復出珍貨貢獻。','主书后请帝许、旧史帝命侧重不同，养父身份有明文。',source='jiuwudaishi-032-december',relation='corroborates')
relationship('全义','后','养父',71,'请父事全义。','礼仪认拜的养父关系，不写为亲生父亲；主书实际拜受已明示。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新史亦记张全义被命认作刘皇后养父。',71,'命后拜全義為養父。','独立原文印证养父用词，不合并其亲生父刘叟。',source='xinwudaishi-014-adopted-father',relation='corroborates')
E=ev('zhaofeng_protests_adopted_father','刘后命赵凤草谢全义书，赵凤密谏国母拜臣为父，帝嘉直而仍行',71,'明日','然卒行之。',[('后','命草谢书者'),('赵凤','翰林学士、密谏者'),('帝','嘉谏仍行者'),('全义','谢书对象')],when='924年十二月庚午翌日',place='唐廷',note='翌日保留相对日未换干支，赵谏礼制是其论，不认跨朝从无例的数据库事实。')
claim('event',E,'description','旧史同记翌日命学士谢书、赵凤密疏反对，帝竟不能已。',71,'學士趙鳳密疏，陳國後無拜人臣為父之禮，帝雖嘉之，竟不能已其事。','同结果，密奏不等全义当场参与。',source='jiuwudaishi-032-december',relation='corroborates')
ev('queen_quanyi_gifts','认养父后刘皇后与张全义日遣使往来问遗',71,'自是',None,[('后','问遗者'),('全义','往来者')],when='924年十二月拜父以后持续交往，终日未载',place='唐宫与张全义第',note='不列无名使者，不造每天固定贡额。')
ev('tang_eunuch_governorship_background','追叙唐僖昭时宦官虽盛而未有建节者',72,'初','未尝有建节者。',[],year=None,when='唐僖宗昭宗之世追叙',place='唐朝',note='史书概括，未新造僖昭在924在世行动。')
E=ev('chengxiu_requests_qinzhou','安重霸劝王承休求秦州节度，王承休称可选美妇献蜀主获准',72,'蜀安','蜀主许之，',[('重霸','劝求镇者'),('承休','请镇者'),('蜀主','准请者')],when='924年十二月正式任命之前，确日未载',place='前蜀、秦州',note='请采美妇是承休请辞内容，不强造采集已发生及无名女子。')
claim('event',E,'description','旧史安重霸传亦记重霸说承休求镇秦州，继记岁余再求旄钺。',72,'重霸說承休求鎮秦州。','该传先置军俱天水后岁余求节，主书十月置军十二月授节，叙事间隔异保留，不硬按岁余推925授节。',source='jiuwudaishi-061-anzhongba',relation='conflicts')
ev('chengxiu_tianxiong_governor','王承休任天雄节度使封鲁国公，龙武军改其牙兵',72,'庚午',None,[('承休','新节度使鲁国公'),('蜀主','任命君主')],when='924年十二月庚午',place='天雄军、秦州',note='天雄秦州依据本段求秦州上下文，不等唐魏博天雄；军转牙兵不推总数变动。')
ev('yanqiong_capital_command','徐延琼任前蜀京城内外马步都指挥使',73,'乙亥','都指挥使。',[('徐延琼','前武德节度兼中书令、受任者'),('蜀主','任命者')],when='924年十二月乙亥',place='成都',note='原职与当前新职分明，外戚未明此句具体姻亲端点不造亲属关系。')
ev('yanqiong_replaces_zongbi_discontent','徐延琼以外戚代王宗弼居旧将之上，众不平',73,'延琼以','众皆不平。',[('徐延琼','取代旧将者'),('宗弼','被代者')],when='924年十二月任职后本段',place='前蜀',note='旧将之右是位次，不作现代左右翼兵团；无名众不平未推起兵。')
E=ev('beijing_lanzhou_report','北京上报契丹寇岚州',73,'壬午',None,[],when='924年十二月壬午',place='北京奏报、岚州',note='北京为唐北都太原语境，不映成现代北京。')
claim('event',E,'description','旧史同壬午记契丹寇岚州。',73,'壬午，契丹寇嵐州。','同日地印证，不造卢文进现场名。',source='jiuwudaishi-032-december',relation='corroborates')
ev('shu_next_year_xiankang','王宗衍宣布明年改元咸康',74,'辛卯',None,[('蜀主','改元宣布者')],when='924年十二月辛卯宣布，925年生效',place='前蜀',note='宣布在924，不能把924年号整体改咸康；明年生效是计划日期。')
E=ev('cunxian_dies','卢龙节度使李存贤去世',75,'卢龙',None,[('李存贤','亡故节度使')],when='924年末本段，确日未载',place='幽州',note='主书924年末编次，死亡地依旧史传；旧史925正月奏卒是上报另时，不自动改成两次死。')
claim('event',E,'description','旧史传记李存贤忧劳成疾卒于幽州、时年六十五，赠太傅。',75,'以至憂勞成疾，卒於幽州，時年六十五。詔贈太傅。','病因是该传解释，年龄不反推生年；传此句未给确日。',source='jiuwudaishi-053-cunxian-final',relation='corroborates')
claim('event',E,'time_original','旧史本纪925年正月丙辰记幽州上报李存贤卒。',75,'丙辰，幽州上言，節度使李存賢卒。','编年上报日与主书924末去世条并列，不能从单句认定确切死亡日就是丙辰。',source='jiuwudaishi-032-cunxian-report')
for code,name,old,new in [('zongren','王宗仁','普王','卫王'),('zonglu','王宗辂','雅王','幽王'),('zongji','王宗纪','褒王','赵王'),('zongzhi','王宗智','荣王','韩王'),('zongze','王宗泽','兴王','宋王'),('zongding','王宗鼎','彭王','鲁王'),('zongping','王宗平','忠王','薛王'),('zongte','王宗特','资王','莒王')]:
 ev(code+'_title_924',name+'由'+old+'改封'+new,76,'是岁',None,[(name,'改封者'),('蜀主','改封君主')],when='924年是岁综录，具体月日未载',place='前蜀',note='国王名爵改封不等实际迁居到封号所借古国；未凭宗字自动建父子关系。')
ev('shu_princes_relieve_commands','王宗辂王宗智王宗平皆罢军使',76,'宗辂、',None,[('王宗辂','被罢军使者'),('王宗智','被罢军使者'),('王宗平','被罢军使者')],when='924年是岁综录，具体月日未载',place='前蜀',note='军使具体职未给，不造罢黜所有官爵或被杀。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续61—76段至924年末；吴王杨溥监控追叙及翟虔远徙非斩；伊阙逐日猎与死伤约数旧史补证；四次蜀撤戍编制不换兵员；朱友谦李继麟与朱令德李令锡同主体血亲，铁券本日任官概述不重造前任；张格旧事杖杀与许寂预测分开；李嗣源命赴汴与后奏北征分日，旧史夹注通鉴非独证；张全义刘后养父非亲父，自述失父母非独立生父死亡；赵凤谏不施行；王承休求秦与龙武牙军及旧史岁余叙次异；徐延琼外戚不造具体端点；北京奏岚州非现代北京；924宣布925咸康；李存贤924末死与旧史925正月上报并列；八王改封军使罢为年度综录不锁定十二月。'
for n in range(61,77):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=924,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(61,77)],next_paragraph='zztj-v273-y0925-p001',supplements=supplements,coverage='卷273第61—76段，原文件66—81行；吴监控、使聘伊阙猎、蜀撤戍、朱氏铁券、张格复相、张全义养父、王承休秦州、改元与八王改封，924年正文至此结束。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(61,77)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
