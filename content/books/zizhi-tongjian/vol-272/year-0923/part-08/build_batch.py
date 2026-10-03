# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 36–46."""
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
 ('tongjian-272-923-after-liang',P/'sources/library/tongjian-272-923-after-liang','c7344d4b','司马光等'),
 ('jiuwudaishi-030-liang-officials',P/'sources/library/jiuwudaishi-030-liang-officials','c7344d4b','薛居正等'),
 ('jiuwudaishi-030-liang-punishment-1',P/'sources/library/jiuwudaishi-030-liang-punishment-1','c7344d4b','薛居正等'),
 ('jiuwudaishi-030-liang-punishment-2',P/'sources/library/jiuwudaishi-030-liang-punishment-2','c7344d4b','薛居正等'),
 ('jiuwudaishi-030-renaming',P/'sources/library/jiuwudaishi-030-renaming','c7344d4b','薛居正等'),
 ('jiuwudaishi-030-tomb-pardon',P/'sources/library/jiuwudaishi-030-tomb-pardon','c7344d4b','薛居正等'),
 ('jiuwudaishi-090-lu-siduo',P/'sources/library/jiuwudaishi-090-lu-siduo','c7344d4b','薛居正等'),
 ('jiuwudaishi-092-wang-quan',P/'sources/library/jiuwudaishi-092-wang-quan','c7344d4b','薛居正等'),
 ('xinwudaishi-021-jingxiang-death',P/'sources/library/xinwudaishi-021-jingxiang-death','c7344d4b','欧阳修'),
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p036-p046',
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
lines = (ROOT / 'resources/derived/tongjian/272.txt').read_text().splitlines()
for n in range(36, 47):
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
people, used, reused, supplements = {}, {}, {'xinwudaishi-005-923-founding'}, []

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
        citation = f'卷272·同光元年（923）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_272_0923_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷272同光元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='923年本段；确日未载', note='', year=923, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_272_0923_' + code
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
        edge = 'participation_zztj_272_0923_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
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
        row=dict(key=f'relationship_zztj_272_0923_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)


# Contiguous source spans; quotations preserve original glyphs.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('jingxiang_refuses_new_court','李振邀敬翔朝见新君，敬翔拒绝并自缢',36,'李振谓敬翔曰',None,[('李振','邀朝新君者'),('敬翔','拒绝朝新君并自缢者')],when='923年十月己卯入城后之夕、次日未曙',place='大梁',note='死者是敬翔；此处李振入朝尚生，不与后续族诛混同。夕未曙保留原纪时，未武断定公历。')
claim('person',people['敬翔'],'death_year','敬翔在923年唐入汴后自缢。',36,'乃缢而死。','翔为承接主语，本段不是被唐军处斩。')
claim('event',E,'description','《新五代史》同记李振邀朝、敬翔自经；补夜止高头车坊。',36,'翔夜止高頭車坊，將旦，左右報曰：「崇政李公入朝矣！」','高头车坊为新史补地点，庄宗入汴后自经，不把后来族诛诏改为敬翔个人处死原因。',source='xinwudaishi-021-jingxiang-death')
E=ev('former_liang_officials_pardoned','李存勖赦梁百官待罪',37,'庚辰','帝宣敕赦之。',[('帝','宣赦者')],when='923年十月庚辰',place='大梁朝堂',note='这是当次赦免，不宣称以后永不追罪或人人同日皆得相同官。')
claim('event',E,'description','《旧五代史》同记庚辰百官待罪获释，补御元德殿。',37,'庚辰，帝御元德殿，梁百官於朝堂待罪，詔釋之。','同日互证，殿名为补充定位。',source='jiuwudaishi-030-liang-officials',relation='corroborates')
E=ev('wentao_kills_zhaoyan','温昭图迎赵岩入许州后斩杀献首，没其财货',37,'赵岩至许州','所赍之货。',[('赵岩','许州被杀者'),('温昭图','杀赵岩并献首没货者')],when='923年十月庚辰条',place='许州',note='主书庚辰条下记事；温昭图与温韬同人，不把赵岩先前预期必不负我当结果。')
claim('person',people['赵岩'],'death_year','赵岩于923年许州被温韬杀死。',37,'赵岩至许州，温昭图迎谒归第，斩首来献，','死时在许州，后续族诛诏不当本人又被杀一次。')
ev('wentao_resumes_name','温昭图恢复温韬旧名',37,'昭图复名韬。',None,[('昭图','恢复旧名者')],when='923年十月庚辰条',place='许州',note='同一稳定人物；复名记为事实引用，不另建温昭图主体。')
E=ev('youzhen_remains_order','诏王瓒收殓朱友贞尸、殡于佛寺并处理首级',38,'辛巳',None,[('帝','下诏者'),('王瓚','奉诏处理者'),('硃友贞','已故末帝')],when='923年十月辛巳',place='佛寺、太社；寺名未载',note='诏令与葬处名称以原书为据，未据此推正式帝陵、佛寺坐标或首级新发现。')
E=ev('duyanqiu_surrenders','杜晏球率梁前锋遇李从珂并先降',39,'段凝自滑州','晏球先降。',[('段凝','渡河入援的梁军主将'),('杜晏球','排陈使前锋，先降者'),('李从珂','封丘相遇唐将')],when='923年十月壬午前；确日未单列',place='滑州、封丘',note='杜先降和段凝壬午降分开；相遇不虚构战斗阵亡。')
E=ev('duanning_army_surrenders','段凝率众五万至封丘解甲请降',39,'壬午','解甲请降。',[('凝','率军投降者')],when='923年十月壬午',place='封丘',note='五万为主书记众数，不与别处议策六万或十万强行合一。')
claim('event',E,'description','《旧五代史》同记壬午五万马步军解甲封丘。',39,'壬午，段凝所部馬步軍五萬解甲於封丘。','本役同数互证，仍为史载口径非现代点验。',source='jiuwudaishi-030-liang-officials',relation='corroborates')
ev('cunxu_rewards_surrendered_army','李存勖赐劳段凝诸将，安慰降军使各复所',39,'凝帅诸大将','使各复其所。',[('凝','诣阙待罪的降将'),('帝','劳赐慰谕者')],when='923年十月壬午降后',place='唐廷、降军营地',note='待罪与劳赐分别成立；不把受赏推为所有降军对唐长期忠诚。')
ev('duanning_chronicle_criticism','主书记段凝自得、梁旧臣愤恨',39,'凝出入公卿间',None,[('凝','主书评价对象')],when='923年投降后；确日未载',place='唐廷',note='皆欲龁面抉心为夸张情绪描写，不建立实际咬伤或剖心事件。')
# Eleven independently indexed demotions in the single continuous paragraph.
items=[('郑珏','莱州司户'),('萧顷','登州司户'),('刘岳','均州司马'),('任赞','房州司马'),('姚顗','复州司马'),('封翘','唐州司马'),('李怿','怀州司马'),('窦梦征','沂州司马'),('刘光素','密州司户'),('陆崇','安州司户'),('王权','随州司户')]
quote=span(40,'丙戌','仕梁贵显故也。');demotions=[]
for name,office in items:
 E=event('demote_'+name,f'李存勖贬{name}为{office}',40,quote,[(name,'被贬官员'),('帝','下诏者')],when='923年十月丙戌',place=office[:2],note='以世受唐恩仕梁为诏书及主书解释，不当现代独立道德结论；贬授不等同日到任。');demotions.append(E)
claim('event',demotions[0],'description','《旧五代史》同列十一人的贬职；补均员外置同正员。',40,'並員外置同正員。','承该段完整十一人贬职，郑玨/郑珏是繁体字形及同职同名单匹配，不另建。',source='jiuwudaishi-030-liang-officials')
relationship('岳','崇龟','从子',40,'岳，崇龟之从子；','从子按原称，未擅改亲子或以父系某支推确定叔侄。')
relationship('敖','翘','祖父',40,'翘，敖之孙；','封翘承前列名单，敖作同姓封敖；祖父明确，不虚补中间一代姓名。')
relationship('龟','权','祖父',40,'权，龟之孙也。','王权之祖龟经旧史王权传身份回查，不与别姓同名龟合并。')
claim('person',people['王权'],'description','《旧五代史》王权传记字秀山、太原人、祖龟浙东观察使。',40,'王權，字秀山，太原人，積世衣冠。','用于核实本段权的同一身份；传记后续事迹留待对应年份，不预录清泰天福。',source='jiuwudaishi-092-wang-quan')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《旧五代史》王权传同记祖龟。',40,'祖龜，浙東觀察使。','同一王权传，祖孙身份互证。',source='jiuwudaishi-092-wang-quan',relation='corroborates')
for name,qt,value in [('姚顗','顗，万年人；','姚顗籍贯万年。'),('李怿','怿，亦兆人；','主书李怿籍贯“亦兆”，原字疑误待考。')]:
 claim('person',people[name],'description',value,40,qt,'万年用史载地名；亦兆疑京兆，但底本无另证，此次不静默改字或定位坐标。')
# Accusation, edict and subsequent narratives do not assert repeated deaths.
ev('duan_du_petition_punishment','段凝杜晏球上言请求诛梁朝要人',41,'段凝、杜晏球上言','不可不诛。”',[('段凝','上言者'),('杜晏球','上言者')]+[(x,'被奏指控对象') for x in ['赵岩','赵鹄','张希逸','张汉伦','张汉杰','张汉融','硃珪']],when='923年十月丙戌后文；奏确日未单列',place='唐廷',note='窃弄威福等是奏章指控，需保留言语归属；请诛不是本句所有人已被杀。')
E=ev('liang_ministers_clan_execution_edict','李存勖下诏族诛梁要人及撒剌阿拨，对其他文武不问',41,'诏：“敬翔','一切不问。”',[('帝','下诏者'),('敬翔','已死而被诏及族的梁相'),('李振','诏令对象'),('撒刺阿拨','被诏处置者')],when='923年十月丙戌条后文；新史列丙戌',place='大梁市',note='岩等承上名单，敬翔已自缢、赵岩已死许州，族诛不是两人再次生前被杀。诏中叛兄弃母负恩等为官方指控，未以此补未经证实亲属关系。')
claim('event',E,'description','《旧五代史》诏称敬翔虽闻自尽仍与李振并族于市。',41,'敬翔雖聞自盡，未豁幽冤，宜與李振並族於市。','明确区分敬翔先自尽与后族刑；不造匿名族属姓名或人数。',source='jiuwudaishi-030-liang-punishment-2',relation='adds')
claim('event',E,'description','《旧五代史》诏称张汉杰中都俘获后曾得哀矜，今因奏请定刑。',41,'其張漢傑昨於中都與王彥章同時俘獲，此際未詳行止，偶示哀矜。','补捕后处置变化，未把中都被俘当斩日。',source='jiuwudaishi-030-liang-punishment-1')
claim('event',E,'description','《新五代史》丙戌列杀李振赵岩张汉杰朱珪、灭族。',41,'殺李振、趙巖、張漢傑、朱珪，滅其族。','本纪压缩叙述赵岩之死于丙戌族刑条，通鉴庚辰许州已死分开；不合成唯一一致死亡日。',source='xinwudaishi-005-923-founding',relation='conflicts')
claim('event',E,'description','《旧五代史》另述多人并妻孥斩于汴桥下。',41,'並其妻孥，皆斬於汴橋下。','该段名单还列先自尽敬翔及已死许州赵严，可能合叙尸首/族刑或记载差异；只呈原书说法，不增第二死亡事件。',source='jiuwudaishi-030-tomb-pardon',relation='conflicts')
ev('liang_rulers_posthumous_degradation','朱温朱友贞被追废为庶人，梁宗庙神主被命毁',41,'又诏',None,[('帝','下诏者'),('朱温','已故梁太祖、追废对象'),('硃友贞','已故梁末帝、追废对象')],when='923年十月灭梁后',place='梁宗庙',note='追废为身后政治处分，不是923年两人新即位或当日新死。')
E=ev('lu_siduo_arrow_backstory','陆思铎河上战中射中李存勖马鞍，帝留箭',42,'帝之与梁战','藏之。',[('帝','被射马鞍并留箭者'),('陆思鐸','梁射手')],when='923年之前河上梁唐战争；确年未载',year=None,place='河上',note='追叙非923新战；中鞍不改射伤帝本人，姓名自镂按原记。')
E=ev('lu_siduo_pardoned_promoted','陆思铎降唐获释，后授龙武右厢都指挥使',42,'至是','都指挥使。',[('帝','示箭释罪并授职者'),('思鐸','降将受任者')],when='923年灭梁后；授职为寻，确日未载',place='唐廷',note='展示名陆思铎，原文思鐸保留；拱宸/旧史拱辰军名异字存，不强断一切机构相同。')
claim('event',E,'description','《旧五代史》同记出箭、释罪、授龙武右厢都指挥使，补检校太保。',42,'莊宗慰而釋之。尋授龍武右廂都指揮使，加檢校太保。','只补对应段事迹；传末天福卒年及后朝任职不抢先录。',source='jiuwudaishi-090-lu-siduo')
ev('chongtao_acts_chancellery','豆卢革尚在魏，郭崇韬被命权行中书事',42,'以豆卢革',None,[('豆卢革','尚在魏的宰相'),('郭崇韬','权行中书事者')],when='923年十月灭梁后、豆卢革庚寅到来前',place='魏州、唐廷',note='豆卢革并未被此句罢相，权行事务不是正式新宰相任命。')
ev('liang_governors_come_to_court','梁藩镇陆续朝见待罪，袁象先霍彦威先后来朝',43,'梁诸籓镇','次之。',[('帝','慰释者'),('袁象先','宋州节度使首来者'),('霍彦威','陕州留后次来者')],when='923年十月灭梁后；先后来朝无确日',place='大梁唐廷',note='稍稍不当所有同一天，先后是两人相对顺序。')
ev('yuan_xiangxian_bribes','主书记袁象先带珍货遍赂刘夫人及权贵，旬日受誉恩宠',43,'象先辇珍货','恩宠隆异。',[('袁象先','被述行赂者'),('魏国夫人刘氏','被述受贿的刘夫人')],when='923年十月来朝后旬日',place='唐廷',note='数十万货单位未知，未推钱贯；刘夫人按上下文为李存勖妻，非李克用妻；争誉动机与恩宠归属作者描写。')
ev('liang_local_offices_retained','李存勖诏梁藩镇及诸将校职不改，先奔梁者不问',43,'己丑',None,[('帝','下诏者')],when='923年十月己丑',place='后梁原藩镇及唐廷',note='不议改更为这道诏的范围，未推永不调整或给无名官员捏造身份。')
ev('doulu_ge_arrives','豆卢革自魏至唐廷',44,'庚寅','至自魏。',[('豆卢革','自魏到来者')],when='923年十月庚寅',place='魏州至唐廷')
E=ev('chongtao_shizhong_chengde','郭崇韬加守侍中、领成德节度使',44,'甲午','领成德节度使。',[('崇韬','加官兼领者')],when='923年十月甲午',place='唐廷、成德军',note='兼领不等当日赴任镇州；不作侍中与枢密使两不同人物。')
claim('event',E,'description','《旧五代史》同甲午记郭崇韬守侍中兼成德节度使，仍为枢密使。',44,'依前樞密使、太原郡侯，仍賜鐵券。','补同时依前职及铁券，避免将旧职误当全罢。',source='jiuwudaishi-030-renaming')
ev('chongtao_doulu_evaluation','主书评郭崇韬兼权荐人、豆卢革受成',44,'崇韬权兼',None,[('崇韬','政治评价对象'),('豆卢革','政治评价对象')],when='923年此段总结；起始确年未载',year=None,place='唐廷',note='竭忠无隐与无所裁正是主书评论，非新增每一荐人个案。')
E=ev('duan_du_granted_li_names','段凝杜晏球赐姓名李绍钦李绍虔',45,'丙申',None,[('凝','获赐姓名李绍钦者'),('杜晏球','获赐姓名李绍虔者')],when='923年十月丙申',place='唐廷',note='两人稳定key保留，姓名赐予作为事实附来源；杜晏球耀州/旧史辉州原字待考，未因地名差异新建两人。')
for name,alias in [('段凝','李绍钦'),('杜晏球','李绍虔')]:claim('person',people[name],'aliases',name+'在本段获赐姓名'+alias+'。',45,Q[45]['text'],'同一人前后称名，不改发布档案UUID。')
claim('event',E,'description','《旧五代史》同记丙申赐名，并称杜晏球为辉州刺史。',45,'守輝州刺史杜晏球為檢校司徒，依前輝州刺史，仍賜姓，名紹虔。','主书耀州、旧史辉州字形与官名有异，分别保留，待另核行政地名。',source='jiuwudaishi-030-renaming',relation='conflicts')
ev('zhang_quanyi_comes_resumes_name','张宗奭来朝献币马，恢复张全义名',46,'乙酉','献币马千计；',[('张宗奭','河南尹来朝者')],when='923年十月乙酉',place='洛阳至唐廷',note='币马千计未分单位，不把每类都写千匹；张宗奭/张全义同人。')
ev('princes_treat_quanyi_as_elder','李存勖命李继岌李存纪等以兄礼事张全义',46,'帝命皇子','等兄事之。',[('帝','下令者'),('继岌','皇子奉命者'),('存纪','皇弟奉命者'),('张宗奭','兄礼所事对象')],when='923年十月乙酉',place='唐廷',note='兄事是政治礼遇，不构造皇子与张全义血缘兄弟或结义关系。')
relationship('帝','存纪','兄长',46,'帝命皇子继岌、皇弟存纪等兄事之。','皇弟存纪是帝李存勖之弟；A为B兄长，区别于对张全义的兄事礼。')
E=ev('quanyi_stops_tomb_destruction','张全义谏止李存勖发朱温墓焚尸，帝仅削其阙室封树',46,'帝欲发梁太祖墓',None,[('帝','欲毁墓后纳谏者'),('张宗奭','谏止者'),('朱温','已故墓主')],when='923年十月乙酉条；旧史灭梁后诏刑段另叙',place='朱温墓；墓址未核',note='欲焚并未执行；原话屠灭其家是劝谏陈说，不当新列全部家属名单。主书仅铲阙室削封树，非墓全毁。')
claim('event',E,'description','《旧五代史》同记欲发墓、张全义上章而帝止，只剗阙室。',46,'帝乃止，令剗去闕室而已。','旧史该段夹有引用通鉴注文，不能把注文算第三独立书证；正文同事但纪事位置早于主书乙酉，确日异置保留。',source='jiuwudaishi-030-tomb-pardon',relation='corroborates')

for row in B['people']:
 if row['key'] not in reused and row['name'] in ['王龟','封敖']:row['era']='唐'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续36—46段；敬翔先自缢、赵岩先死许州与族诛诏分开；诏刑和请刑非全部已执行；世受唐恩等是诏评；陆射帝中鞍为追叙年null；从子祖父具体关系；兄事张全义非血缘；耀/辉州及亦兆疑字保留待考；墓焚欲为未执行；原文保留，展示简体。'
for n in range(36,47):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(36,47)],next_paragraph=Q[47]['id'],supplements=supplements,coverage='卷272第36—46段，原文件41—51行；接梁亡后唐朝处置与赐名、谏墓。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(36,47)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
