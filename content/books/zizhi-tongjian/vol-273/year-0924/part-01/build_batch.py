# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 924, paragraphs 1–12."""
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
 ('tongjian-273-924-january',P/'sources/library/tongjian-273-924-january','fa5fd41a','司马光等'),
 *[(key,P/'sources/library'/key,'fa5fd41a',author) for key,author in [
 ('jiuwudaishi-031-border-jiyan','薛居正等'),('jiuwudaishi-031-eunuchs-finance','薛居正等'),
 ('jiuwudaishi-031-taihou-arrival','薛居正等'),('jiuwudaishi-031-suburban-rite','薛居正等'),
 ('jiuwudaishi-132-maozhen-submission','薛居正等'),('jiuwudaishi-132-congyan','薛居正等'),
 ('xinwudaishi-026-kongqian-finance','欧阳修'),('xinwudaishi-040-jiyan-visit','欧阳修'),
 ('xinwudaishi-024-chongtao-donations','欧阳修'),('xinwudaishi-005-924-annals','欧阳修')]],
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0924-p001-p012',
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
people, used, reused, supplements = {}, {}, set(), []

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
    ck = f'claim_zztj_273_0924_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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
E=ev('khitan_wuqiao_report','幽州奏契丹入寇至瓦桥',1,'春，正月','至瓦桥。',[],when='924年正月甲辰奏报',place='幽州、瓦桥',note='甲辰为奏报日，不断定契丹抵达恰同一日。')
claim('event',E,'description','旧史同甲辰记幽州奏契丹寇至瓦桥。',1,'甲辰，幽州上言，契丹入寇至瓦橋。','同一奏报补证；不录注引契丹国志为另一独立来源。',source='jiuwudaishi-031-border-jiyan',relation='corroborates')
E=ev('siyuan_huoyanwei_rescue','李嗣源任北面招讨使，霍彦威副之，李绍宏监军救幽州',1,'以天平',None,[('嗣源','北面行营都招讨使'),('霍彦威','陕州留后、招讨副使'),('绍宏','宣徽使、监军')],when='924年正月甲辰奏报后任命',place='唐廷至幽州',note='授职将兵救援不证明同日援军已到幽州；三人身份分开。')
claim('event',E,'description','旧史同记李嗣源为招讨使，霍彦威副之率军援幽州。',1,'以天平軍節度使李嗣源為北面行營都招討使，陝州留後霍彥威為副，率軍援幽州。','旧史未于此句记李绍宏监军，不能假称三项全部同证。',source='jiuwudaishi-031-border-jiyan',relation='corroborates')
ev('qian_criticises_finance_delays','孔谦向郭崇韬批评豆卢革财政文簿留滞，要求另图人选',2,'孔谦复','宜更图之。”',[('谦','批评及建议者'),('崇韬','受建议者'),('革','被称首座相公者')],when='924年正月本段，确日未载',place='唐廷',note='万机繁、居远、留滞为孔谦陈说，不作独立绩效核定。')
E=ev('doulu_borrowed_treasury','追叙豆卢革借省库钱，孔谦向郭崇韬出示手书，郭讽革',2,'豆卢革尝','崇韬微以讽革。',[('革','被记借钱者'),('谦','出示借钱手书者'),('崇韬','讽劝豆卢革者')],when='豆卢革判租庸后至924正月，原借钱确年未载',year=None,place='唐省库',note='尝借的确年不锁924；主书数十万、新史十万并列，假为借贷不直接判为盗取。')
claim('event',E,'description','新史记豆卢革手书借租庸钱十万，孔谦示书并微泄其事。',2,'而革嘗以手書假租庸錢十萬，謙因以書示崇韜，而微泄其事，使革聞之。','主书数十万、新史十万数字不同，完整保留；不能自动转换成现代钱额。',source='xinwudaishi-026-kongqian-finance',relation='conflicts')
ev('doulu_offers_finance_chongtao','豆卢革请郭崇韬专判租庸，郭固辞',2,'革惧','崇韬固辞。',[('革','提议让财政职者'),('崇韬','拒任者')],when='924年正月本段',place='唐廷',note='惧是主书所记情绪；拒任意味着本次未成任命。')
E=ev('zhangxian_recalled_finance','李存勖问财政人选，郭崇韬荐复用张宪，帝令召之',2,'上曰',None,[('上','问人选、下令召宪者'),('崇韬','推荐者'),('宪','被召者'),('谦','被议暂不委任者')],when='924年正月本段',place='唐廷、东京',note='召回为命令，张宪尚未在此句实际抵朝或重新任租庸；物望为郭评价。')
claim('event',E,'description','新史同记郭崇韬荐张宪并召，孔谦未获大任。',2,'孔謙雖長於金穀，而物議未可居大任，不若復用張憲。','保持建议与实际任职差别，后续留张宪另录。',source='xinwudaishi-026-kongqian-finance',relation='corroborates')
E=ev('maozhen_jiyan_tribute','李茂贞闻帝入洛，遣子李继曮入贡并上表称臣',3,'岐王闻','始上表称臣。',[('岐王','遣子、称臣者'),('继\ue4be严','彰义节度使、岐王子及使者')],when='923年帝入洛后至924年正月；遣贡确日未载',year=None,place='凤翔至唐廷',note='入洛为923十二月已录；本段跨前后背景，遣贡不能强锁正月庚戌。继私用编码严保留原文，规范名以新史从曮和旧史继严、从严对应，同父入朝加官一致。')
claim('person',people['李继曮'],'aliases','主书含缺字编码的李继曮，对应新史从曮，旧史继严、从严。',3,'遣其子從曮來朝。','同李茂贞之子入朝事结合旧史卷132父子入觐加中书令校核；从字为后称，不提前记录926改名行为。',source='xinwudaishi-040-jiyan-visit')
claim('event',E,'description','旧史亦记茂贞闻入洛后称臣、遣子继严来朝。',3,'及聞莊宗入洛，懼不自安，方上表稱臣，尋遣其子繼嚴來朝，','旧史直接写继严字形，原文各自保留；不拿后续夏四月卒事填本批。',source='jiuwudaishi-132-maozhen-submission',relation='corroborates')
relationship('岐王','继\ue4be严','父亲',3,'遣其子行军司马彰义节度使兼侍中继\ue4be严入贡','A李茂贞是B李继曮父亲；姓名缺字另书校核。')
E=ev('maozhen_named_qiwang_rites','李存勖优礼李茂贞，赐诏称岐王而不名',3,'帝以','不名。',[('帝','施优礼者'),('岐王','受礼者'),('李克用','被比肩的已故唐太祖')],when='924年正月本段，赐诏优例',place='唐廷至凤翔',note='太祖指后唐李克用，非梁朱温；比肩是政治资望说明，不造血缘季父关系。')
E=ev('jiyan_zhongshuling_returns','李继曮加兼中书令后遣还',3,'庚戌',None,[('继\ue4be严','加官、被遣还者')],when='924年正月庚戌',place='唐廷至凤翔',note='旧史本纪此时记从严，旧史传后载926加从字；主体合并，称名异文与追称分清。')
claim('event',E,'description','旧史同庚戌加李从严兼中书令。',3,'庚戌，以涇原節度使、充秦王府諸道行軍司馬、開府儀同三司、檢校太尉、兼侍中李從嚴為檢校太尉、兼中書令，','官号旧史泾原、主书彰义为同军州关联称谓，原字与从严追称保留，不造此日改从字。',source='jiuwudaishi-031-border-jiyan',relation='corroborates')
claim('person',people['李继曮'],'description','旧史列李从严为李茂贞长子，并载平梁后奉命入觐加中书令。',3,'從嚴，茂貞之長子也。','长子序由旧史明示；本批未录其后任凤翔及后年征蜀。',source='jiuwudaishi-132-congyan')
E=ev('eunuchs_ordered_capital','唐廷敕前朝、监军及私家内官一并赴阙',4,'敕','并遣诣阙。”',[('帝','敕令者')],when='924年正月本段；旧史置庚戌是日',place='唐诸道至洛阳',note='敕令不保证全员当日完成迁入；新史己酉求宦者可能不同环节，不能硬作同一确日。')
claim('event',E,'description','旧史此敕要求诸道内官连家口赴阙，不得停滞。',4,'詔諸道應有內官，不計高低，並仰逐處並家口發遣赴闕，不得輒有停滯。','旧史前段庚戌后是日承接；新史己酉求唐宦者另日期与动作，并列不抹平。',source='jiuwudaishi-031-eunuchs-finance',relation='corroborates')
claim('event',E,'time_original','新史正月己酉记求唐宦者。',4,'己酉，求唐宦者。','求与敕诸道发遣可分环节，主书未列日；不将己酉和庚戌假成同日。',source='xinwudaishi-005-924-annals')
ev('eunuch_numbers_favoured','主书记内官由约五百增近千人，优给并委任',4,'时在上左右','以为腹心。',[('帝','被记优给任用内官者')],when='原在左右为此前，至924正月叙增员',place='唐宫',note='五百与殆千是史载约数，不登记千人名单；腹心为任用描写。')
E=ev('eunuchs_bureaus_monitors_restored','内诸司使复用宦者，随后复置诸道监军，主书记藩镇怨怒',4,'内诸司',None,[('帝','在位时复置制度的君主')],when='天祐以来为背景，至是及既而复置；确日未载',year=None,place='唐廷、诸道军府',note='制度改变与监军决政为主书概述，既而后续未给确年；皆愤怒是作者归纳，不量化全体民意。')
claim('event',E,'description','旧史亦评论重新任宦官诸司监军，称复兴旧弊。',4,'唐時宦官為內諸司使務、諸鎮監軍，出納王命，造作威福，昭宗以此亡國。及帝奄有天下，當知戒彼前車，以為殷鑒，一朝復興茲弊，議者惜之。','议者惜之为书中论述，非独立统计或明确所有监军同日就任。',source='jiuwudaishi-031-eunuchs-finance',relation='corroborates')
E=ev('khitan_retires_siyuan_recalled','契丹出塞，唐召李嗣源班师',5,'契丹出塞','旋师，',[('嗣源','奉召班师者')],when='924年正月本段；旧史癸丑条编排',place='幽州至塞外、唐军',note='出塞是契丹撤出，不误作入塞；召归不等全部兵已同日归驻地。')
claim('event',E,'description','旧史记北面奏契丹还塞，诏李嗣源班师。',5,'幽州北面軍前奏，契丹還塞，詔李嗣源班師。','旧史位癸丑条，主书本段未单列日，不自行定日。',source='jiuwudaishi-031-eunuchs-finance',relation='corroborates')
ev('shaokin_dongzhang_wuqiao_garrison','唐命段凝与董璋戍瓦桥',5,'命泰宁',None,[('李绍钦','泰宁节度使、戍守者'),('董璋','泽州刺史、戍守者')],when='924年正月契丹出塞后本段',place='瓦桥',note='李绍钦为923赐名段凝，复用主体；李嗣源班师与留守不同职责。')
ev('jiyan_tells_maozhen_army','李继曮归告唐甲兵之盛，李茂贞益惧',6,'李继','岐王益惧。',[('李继\ue4be严','返报者'),('岐王','闻报者')],when='924年正月庚戌遣还后、癸丑表请前',place='凤翔',note='盛、惧为主书陈述，不造具体装备数量与兵力。')
E=ev('maozhen_vassal_rites_request','李茂贞请求正式行藩臣之礼，唐优诏不许',6,'癸丑',None,[('岐王','表请者'),('帝','优诏拒其请者')],when='924年正月癸丑',place='凤翔、唐廷',note='不许是礼遇下拒具体礼节，不等撤销其称臣关系或双方宣战。')
claim('event',E,'description','旧史癸丑条同记李茂贞请行藩臣礼，帝优报。',6,'鳳翔節度使、秦王李茂貞上表，請行藩臣之禮，帝優報之。','旧史称秦王与主书后段才进封的记序不同；不把当前另建提前封秦事件。',source='jiuwudaishi-031-eunuchs-finance',relation='corroborates')
E=ev('qian_retains_zhangxian_tokyo','孔谦称魏都需重人、建议王正言理财政，豆卢革转告郭崇韬后奏留张宪东京',7,'孔谦恶','于东京。',[('谦','提出方案者'),('革','转告者'),('崇韬','奏留张宪者'),('宪','被奏留东京者'),('王正言','被建议改任者')],when='924年正月甲寅任王前',place='唐廷、东京兴唐府',note='操守智力、易制等为孔说与作者评价；不将东京误为已改名汴州。')
claim('event',E,'description','新史同记孔谦劝换人，郭崇韬罢召张宪，用兴唐尹王正言。',7,'革以語崇韜，崇韜罷憲不召，以興唐尹王正言為租庸使。','与前召张宪令的后续取消对应，不能把两个任命都当已到朝就职。',source='xinwudaishi-026-kongqian-finance',relation='corroborates')
E=ev('wang_zhengyan_fiscal_commissioner','王正言任租庸使',7,'甲寅',None,[('正方','新任租庸使王正言')],when='924年正月甲寅',place='唐廷',note='主书此句正方与上下文正言不一，旧史同日明确王正言、新史同故事同名，规范展示据二书，疑字不加入确定别名。')
claim('event',E,'description','旧史同甲寅以礼部尚书兴唐尹王正言充租庸使，仍礼部尚书。',7,'以禮部尚書、興唐尹王正言依前禮部尚書，充租庸使。','证明主书疑字正方对应已有人王正言，不造新人物。',source='jiuwudaishi-031-eunuchs-finance',relation='corroborates')
E=ev('cunshen_reports_xinzhou_recovered','符存审奏契丹去，复得新州',8,'李存审',None,[('李存审','幽州主帅奏报者')],when='924年正月本段，确日未载',place='幽州、新州',note='李存审复用符存审，主书奏为报告；未列攻取战斗和亲自冲阵，不虚构战役。')
claim('event',E,'description','旧史乙卯条记妫州山后十三寨百姓复新州。',8,'幽州奏，媯州山後十三寨百姓卻復新州。','补参与者集体与出处编排，主书并未名诸百姓；未造十三寨逐寨名单或坐标。',source='jiuwudaishi-031-taihou-arrival')
E=ev('three_finance_bureaus_under_commissioner','唐敕盐铁度支户部三司归租庸使管辖',9,'戊午',None,[('帝','敕令者')],when='924年正月戊午',place='唐廷财政三司',note='并隶为管辖关系，不自动等三司机构全部裁撤。')
claim('event',E,'description','旧史同戊午诏盐铁度支户部委租庸使管辖。',9,'詔鹽鐵、度支、戶部並委租庸使管轄。','同日同制度动作印证。',source='jiuwudaishi-031-taihou-arrival',relation='corroborates')
ev('cunwo_jiji_receive_mothers','李存勖遣李存渥与李继岌赴晋阳迎太后太妃',10,'上遣','于晋阳，',[('帝','遣迎者'),('存渥','皇弟、奉命迎者'),('继岌','皇子、奉命迎者'),('太后','拟迎的曹氏'),('太妃','拟迎的李克用妻刘氏')],when='924年正月庚申前；遣使确日未载',place='晋阳',note='帝妻刘夫人与嫡母太妃刘氏不同实体；遣迎不是两位同时实际赴洛。')
relationship('帝','存渥','兄长',10,'皇弟存渥','复用已有明确关系方向，李存勖是李存渥兄长。')
relationship('帝','继岌','父亲',10,'皇子继岌','复用已有父亲关系，李存勖是李继岌父亲，不重复建反向边。')
ev('tai_fei_stays_jinyang','太妃刘氏以陵庙祭祀为由留晋阳不赴洛',10,'太妃曰','遂留不来。',[('太妃','选择留晋阳者')],when='924年正月此次迎接时',place='晋阳',note='祭祀理由为太妃原话，留下不等被禁止出行。')
E=ev('emperor_receives_cao_heyang','李存勖到河阳迎曹太后',10,'太后至','于河阳；',[('帝','亲迎者'),('太后','被迎者')],when='924年正月庚申',place='河阳')
claim('event',E,'description','旧史同记庚申车驾幸河阳奉迎太后。',10,'車駕幸河陽，奉迎皇太后。','不把原议怀州/银台门计划写为实际行程。',source='jiuwudaishi-031-taihou-arrival',relation='corroborates')
claim('event',E,'description','旧史补有司先议宫门迎，帝欲赴怀州，中书以散斋期劝阻后改河阳。',10,'詔親至懷州奉迎。中書奏：「自二十三日後散齋內，車駕不合遠出。」詔改至河陽奉迎。','此为地点计划改变，未发生怀州实际迎接；不得从计划另造已成行事件。',source='jiuwudaishi-031-eunuchs-finance')
E=ev('emperor_cao_enter_luoyang','李存勖侍曹太后入洛阳',10,'辛酉',None,[('帝','随太后入洛者'),('太后','入洛者')],when='924年正月辛酉',place='洛阳')
claim('event',E,'description','旧史同辛酉太后抵，百僚迎于上东门。',10,'辛酉，帝侍皇太后至，文武百僚迎於上東門。','补入城迎接位置，未加现代坐标。',source='jiuwudaishi-031-taihou-arrival',relation='corroborates')
claim('event',E,'description','新史同庚申河阳、辛酉返回，编校注明迎曹太后。',10,'辛酉，至自河陽。','正文行程与注解性质区分；曹氏身份已由主书太后规范关联，不取注中其他未定册月填日期。',source='xinwudaishi-005-924-annals',relation='corroborates')
E=ev('suburban_rite_amnesty','李存勖祀南郊并大赦',11,'二月','大赦。',[('上','祀郊及大赦者')],when='924年二月己巳朔',place='洛阳南郊',note='923准备仪物、决定赴洛与此924实际礼成分开。')
claim('event',E,'description','新史同记二月己巳朔南郊大赦。',11,'二月己巳朔，有事于南郊，大赦。','实际礼成同日印证，非筹备。',source='xinwudaishi-005-924-annals',relation='corroborates')
claim('event',E,'description','旧史记圜丘祀昊天上帝，并列赦令及例外罪项。',11,'十惡五逆、屠牛鑄錢、故意殺人、合造毒藥、持杖行劫、官典犯贓，不在此限。','大赦有明确例外，不说所有罪一律免；旧史例外清单独立出处。',source='jiuwudaishi-031-suburban-rite')
E=ev('kongqian_ignores_amnesty_remission','主书记孔谦仍征赦文蠲免之项，引发对诏令不信和百姓怨情',11,'孔谦',None,[('谦','被记复征者')],when='924年二月大赦后本段，后续概述确日未载',place='唐诸州县',note='求媚及皆不信为主书动机与归纳，不能当独立调查；未具税项数额不编造。')
claim('event',E,'description','旧史亦记孔谦不行赦文所原，称大失人心。',11,'赦文之所原放，謙復刻剝不行，大失人心，始於此矣。','仍属另一史书评价性叙述，非统计证据。',source='jiuwudaishi-031-suburban-rite',relation='corroborates')
E=ev('chongtao_receives_gifts_explains','郭崇韬初至汴洛受藩镇馈遗，回应劝者称代国家收藏',12,'郭崇韬初','吾特为国家藏之私室耳。”',[('崇韬','受馈及自辩者')],when='923年末至汴洛期间的追叙；确日未载',year=None,place='汴州、洛阳',note='为国家藏是郭氏自辩，不直接认定全部合法公款；馈遗与后献分开。')
claim('event',E,'description','新史同记入洛受四方赂遗，解释藏私家如公帑。',12,'且藏于私家，何異公帑？','新史郭氏辩词，不能作为法律定性。',source='xinwudaishi-024-chongtao-donations',relation='corroborates')
E=ev('chongtao_donates_army_money','郭崇韬为南郊先献劳军钱十万缗',12,'及将祀','十万缗。',[('崇韬','献钱者')],when='924年二月南郊前',place='唐廷',note='数字与货币单位按主书，未算现代购买力。')
claim('event',E,'description','新史同记明年南郊献藏财以佐赏给。',12,'明年，天子有事南郊，乃悉獻其所藏，以佐賞給。','其前入洛属923，明年924；别书未列十万数，不能假称同数确证。',source='xinwudaishi-024-chongtao-donations',relation='corroborates')
ev('inner_outer_treasuries_background','追叙宦官劝分内外府，州县上供作经费、方镇贡献入内府供宴游给赐',12,'先是，宦官','充宴游及给赐左右。',[('帝','受建议者、内府供用对象')],when='924年南郊前先是追叙，确年未载',year=None,place='唐廷内外府',note='分府建议背景确年不明；匿名宦官不造姓名，不把经费不足外推所有预算量。')
ev('outer_treasury_shortage','主书记外府常虚而内府财积，郊祀有司缺劳军钱',12,'于是外府','乏劳军钱，',[],when='924年郊祀前，常态背景未给起日',place='唐廷内外府',note='常虚、山积为叙述，未给库存数字，不能生成具体余额。')
ev('chongtao_requests_inner_funds','郭崇韬请出内府财助礼，李存勖称取晋阳储积',12,'崇韬言于上','以相助。”',[('崇韬','请内府财者'),('上','答以晋阳储积者')],when='924年二月南郊前',place='唐廷、晋阳为所称资金地',note='倾家为郭自述；帝说可辇取为安排意见，不等已实取全部晋阳钱。')
ev('chongtao_private_funds_soldier_discontent','主书记取郭崇韬私第金帛数十万补益，军士不满赏给',12,'于是取',None,[('崇韬','被记私第金帛来源者')],when='924年南郊赏给期间',place='郭崇韬私第、唐军',note='电子本此处李崇韬疑姓，与整段郭同事、新史献藏财对应，规范主体郭崇韬，不建立李崇韬别名；十万劳军钱与金帛数十万不能简单相加，后者原文无单位；皆有离心是作者概述。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续1—12段；救幽州任职与军撤分开；豆卢革借省库数十万/新史十万保留，尝借确年null；李继私用编码严据新史从曮及旧史继严从严校核为李继曮，后称别名不提前录926改名；正方据上下文、旧史同日王正言和新史同事规范，不建别名；太祖为后唐李克用；集内官诏与新史己酉求宦者分环节，既而监军确年未给；李绍钦段凝、李存审符存审同主体；太后曹与太妃刘区别，实际河阳迎后赴洛，怀州仅计划；二月郊祀礼成与923准备分开；赦文例外与孔谦复征有旧史补证；郭受馈自辩和内外府先是背景不锁924，李崇韬疑字不另建；银钱金帛不跨单位相加。'
for n in range(1,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=924,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,13)],next_paragraph=Q[13]['id'],supplements=supplements,coverage='卷273同光二年前12段，原文件6—17行；北边救援、财政人事、岐王称臣、内官、太后入洛及郊祀赏给。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(1,13)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
