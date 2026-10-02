# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 7–9."""
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
 ('tongjian-272-923-spring',YEAR/'part-01/sources/library/tongjian-272-923-spring','0b0c460a','司马光等'),
 ('tongjian-272-923-offices',P/'sources/library/tongjian-272-923-offices','ca9db7c8','司马光等'),
 ('tongjian-272-923-temples',P/'sources/library/tongjian-272-923-temples','ca9db7c8','司马光等'),
 ('jiuwudaishi-029-923-founding',P/'sources/library/jiuwudaishi-029-923-founding','ca9db7c8','薛居正等'),
 ('jiuwudaishi-029-923-altar',P/'sources/library/jiuwudaishi-029-923-altar','ca9db7c8','薛居正等'),
 ('xinwudaishi-005-923-founding',P/'sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
 ('xinwudaishi-014-cao-liu',P/'sources/library/xinwudaishi-014-cao-liu','ca9db7c8','欧阳修'),
 ('jiuwudaishi-025-ancestry',P/'sources/library/jiuwudaishi-025-ancestry','ca9db7c8','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p007-p009',
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
for n in range(7, 10):
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
people, used, reused, supplements = {}, {}, {'tongjian-272-923-spring'}, []

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
    ck = f'claim_zztj_272_0923_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'曹氏（李存勖母）','太妃':'刘氏（李克用妻）',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦','曹氏':'曹氏（李存勖母）','刘氏':'刘氏（李克用妻）','武皇':'李克用','考晋王':'李克用','上':'李存勖','帝':'李存勖','执宜':'执宜（李存勖曾祖）','国昌':'李国昌','继岌':'李继岌'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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

E=event('build_founding_altar','晋王在魏州牙城南筑即位坛',7,'晋王筑坛于魏州牙城之南，',[('晋王','筑坛的晋王')],when='923年四月即位前；旧史记三月',place='魏州牙城之南',note='主书筑坛在升坛前；具体筹备月由旧史补证，不把四月己巳当筑坛日。')
claim('event',E,'time_original','《旧五代史》记三月筑即位坛。',7,'是月，築即位壇於魏州牙城之南。','前句三月己卯，承三月；非另一次建坛。',source='jiuwudaishi-029-923-altar',relation='adds')
E=event('tang_founding_reuse','李存勖升坛祭告，即皇帝位，国号大唐',7,'夏，四月，己巳，升坛，祭告上帝，遂即皇帝位，国号大唐，大赦，改元。',[('晋王','称帝建立后唐者')],when='923年四月己巳',place='魏州牙城之南',stable_key='event_tang_founded',note='全站后唐建立事件及既有参与UUID复用；大唐是自称，后唐是后世区分，不另建一次称帝。')
claim('event',E,'description','《新五代史》同记四月己巳即位、国号唐、大赦改元。',7,'夏四月己巳，皇帝即位，大赦，改元，國號唐。','同日同事，与主书互证；当时梁尚存。',source='xinwudaishi-005-923-founding',relation='corroborates')
event('founding_amnesty','后唐即位颁大赦并改元',7,'遂即皇帝位，国号大唐，大赦，改元。',[('晋王','即位大赦改元者')],when='923年四月己巳',place='魏州',note='配套措施与称帝主体分别可检索；原句未详赦免范围，不补赦对象名单。')
E=event('honor_cao_liu','李存勖尊曹氏为皇太后、刘氏为皇太妃',7,'尊母晋国太夫人曹氏为皇太后，嫡母秦国夫人刘氏为皇太妃。',[('李存勖','尊母及嫡母者'),('曹氏','被尊皇太后的生母'),('刘氏','被尊皇太妃的嫡母')],when='923年四月即位时',place='后唐',note='曹为生母、刘为嫡母，身份不可混同；曹刘同姓其他人不合并。')
claim('event',E,'description','《新五代史》同记曹氏皇太后、嫡母刘氏皇太妃。',7,'莊宗即位，冊尊曹氏為皇太后，而以嫡母劉氏為皇太妃。','以庄宗为李存勖，同一冊尊，不另生成新事件。',source='xinwudaishi-014-cao-liu',relation='corroborates')
relationship('曹氏','李存勖','母亲',7,'尊母晋国太夫人曹氏为皇太后','母字明示，复用原母子关系方向与key。')
relationship('刘氏','李存勖','嫡母',7,'嫡母秦国夫人刘氏','嫡母区别生母；刘氏是李存勖嫡母，不记录为生母。')
E=event('founding_chancellors','豆卢革任门下侍郎、卢程任中书侍郎，皆同平章事',7,'以豆卢革为门下侍郎，卢程为中书侍郎，并同平章事；',[('李存勖','任命者'),('豆卢革','门下侍郎、同平章事'),('卢程','中书侍郎、同平章事')],when='923年四月即位后',place='后唐',note='与二月行台左右丞相分开阶段；并同平章事修饰两人。')
claim('event',E,'description','《新五代史》同记豆卢革、卢程改授两侍郎、同中书门下平章事。',7,'行臺左丞相豆盧革為門下侍郎，右丞相盧程為中書侍郎：同中書門下平章事；','新史盧程与主书一致，旧史盧澄疑异文保留，不新建盧澄。',source='xinwudaishi-005-923-founding',relation='corroborates')
claim('event',E,'description','《旧五代史》补豆卢革太清宫使、卢程监修国史。',7,'以行台左丞相豆盧革為門下侍郎、同中書門下平章事、太清宮使；以行台右丞相盧澄為中書侍郎平章事、監修國史；','旧史盧澄与本条同官同序，按主书和新史复用卢程；澄非程繁体，不自动转换或纳入正式别名。',source='jiuwudaishi-029-923-founding',relation='adds')
claim('event',E,'description','主书评价两相轻浅，称以衣冠及元僚身份被用。',7,'豆卢革、卢程皆轻浅无它能，上以其衣冠之绪，霸府元僚，故用之。','作者评价单列来源，不当客观能力测定或人物简介定论。')
E=event('founding_privy_councillors','郭崇韬、张居翰任枢密使',7,'郭崇韬、张居翰为枢密使，',[('李存勖','任命者'),('郭崇韬','枢密使'),('张居翰','枢密使')],when='923年四月即位后',place='后唐')
claim('event',E,'description','《新五代史》亦记郭崇韬、张居翰为枢密使。',7,'中門使郭崇韜、昭義監軍張居翰為樞密使。','旧新职衔并列，同一任命，不把括注评论另作制度设立事实。',source='xinwudaishi-005-923-founding',relation='corroborates')
E=event('founding_hanlin','卢质、冯道为翰林学士',7,'卢质、冯道为翰林学士，',[('李存勖','任命者'),('卢质','翰林学士'),('冯道','翰林学士')],when='923年四月即位后',place='后唐')
claim('event',E,'description','《旧五代史》补卢质兵部尚书、翰林学士承旨，冯道户部侍郎、翰林学士。',7,'以河東節度判官盧質為兵部尚書，充翰林學士承旨；以河東掌書記馮道為戶部侍郎，充翰林學士；','主书二月为卢质礼部尚书，旧史四月为兵部；保留不同时段，不篡改二月记录。',source='jiuwudaishi-029-923-founding',relation='adds')
E=event('zhang_xian_fiscal_office','张宪为工部侍郎、租庸使',7,'张宪为工部侍郎、租庸使，',[('李存勖','任命者'),('张宪','工部侍郎、租庸使')],when='923年四月即位后',place='后唐')
claim('event',E,'description','《旧五代史》同记张宪工部侍郎、租庸使。',7,'以魏博、鎮冀觀察判官張憲為工部侍郎，充租庸使；','同一人同职印证。',source='jiuwudaishi-029-923-founding',relation='corroborates')
E=event('li_dexiu_censor','李德休为御史中丞',7,'又以义武掌书记李德休为御史中丞。',[('李存勖','任命者'),('李德休','御史中丞')],when='923年四月即位后',place='后唐',note='后句德林与前李德休不一致；先录李德休，不建李德林及李绛祖孙关系，待异本。')
claim('event',E,'description','《旧五代史》亦作李德休，任御史中丞。',7,'以前定州掌書記李德休為御史中丞；','支持李德休名字；通鉴后句德林疑讹不能由此独断改字。',source='jiuwudaishi-029-923-founding',relation='corroborates')
event('lucheng_invests_mothers','诏卢程到晋阳册太后、太妃',7,'诏卢程诣晋阳册太后、太妃。',[('李存勖','下诏者'),('卢程','奉诏册命使'),('太后','受册的曹氏'),('太妃','受册的刘氏')],when='923年四月即位后；诏令确日未载',place='晋阳',note='诏使赴不直接填抵达日；此处太后太妃是曹刘，不沿用前蜀徐氏称谓。')
E=event('cao_liu_household_background','主书追叙刘氏劝李克用善待曹氏，二人相得',7,'初，太妃无子，性贤，不妒忌；太后为武皇侍姬，太妃常劝武皇善待之，太后亦自谦退，由是相得甚欢。',[('太妃','劝善待曹氏的刘氏'),('太后','李克用侍姬曹氏'),('武皇','受劝的李克用')],when='追叙李克用在世时；确年未载',year=None,place='晋',note='性贤不妒为作者评价，常劝为多次追叙，不全部定923年，也不据无子否定嫡母身份。')
E=event('liu_congratulates_cao','刘太妃往贺曹太后，二人相向歔欷',7,'及受册，太妃诣太后宫贺，有喜色，太后忸怩不自安。',[('太妃','往贺的刘氏'),('太后','受贺的曹氏')],when='923年受册之后；确日未载',place='太后宫',note='忸怩有喜色是史述，非现代心理诊断；不能将喜色解释为争位。')
claim('event',E,'description','刘氏祝愿李存勖享国久长，二人相向歔欷。',7,'太妃曰：“愿吾儿享国久长，吾辈获没于地，园陵有主，馀何足言！”因相向歔欷。','愿辞为刘氏言论，不据祝愿判享国结局；馀展示简化为余时引用仍原字。')
claim('event',E,'description','《新五代史》同记太妃往谢太后及祝愿，言辞稍异。',7,'太妃往謝太后，太后有慚色。太妃曰：「願吾兒享國無窮，使吾獲沒于地以從先君，幸矣，復何言哉！」','往谢/往贺和引语分别保留，基本同事而不拼接成逐字统一引语。',source='xinwudaishi-014-cao-liu',relation='corroborates')
# Paragraph 8: retrospective posts and current reorganizations.
event('shaohong_chongtao_old_posts','李绍宏曾为中门使、郭崇韬为其副',8,'初，李绍宏为中门使，郭崇韬副之。',[('李绍宏','中门使'),('郭崇韬','副中门使')],when='即位前追叙；确年未载',year=None,place='晋',note='初提示前事，不当四月重新任此旧职；副之不推私人亲属或永久主从关系。')
E=event('shaohong_recalled_xuanhui','李绍宏自幽州召还，改为宣徽使',8,'至是，自幽州召还，崇韬恶其旧人位在己上，乃荐张居翰为枢密使，以绍宏为宣徽使，绍宏由是恨之。',[('李绍宏','自幽州召还、任宣徽使'),('郭崇韬','荐张居翰者'),('张居翰','被荐者')],when='923年四月即位本段',place='幽州、后唐',note='与p7张居翰枢密任命同事背景，不第二次创建其任命；恶恨为史述，不能推出可客观验证心理事实。')
claim('event',E,'description','《旧五代史》同记权知幽州军府事李绍宏为宣徽使。',8,'以權知幽州軍府事李紹宏為宣徽使；','补权知军府旧职，与主书召幽一致。',source='jiuwudaishi-029-923-founding',relation='corroborates')
event('chongtao_controls_affairs','主书记军国机政皆由郭崇韬掌理',8,'居翰和谨畏事，军国机政皆崇韬掌之。',[('张居翰','被记和谨畏事的枢密使'),('郭崇韬','掌军国机政者')],when='923年即位后本段所述；持续期未详',place='后唐',note='作者对两枢密实际权任的叙述，不据皆字断后唐全部时期，也不另建上下属关系。')
event('kong_qian_deputy_fiscal','郭崇韬荐张宪为租庸使，孔谦为副',8,'故崇韬荐张宪，以谦副之，谦亦不悦。',[('郭崇韬','推荐张宪者'),('张宪','被荐主使'),('孔谦','租庸副使')],when='923年四月即位后',place='后唐',note='孔谦自谓应任为主观期望，任副才是实际措施；张宪正使任命已p7，仅补荐与副任。')
claim('event',used[8][-1],'description','孔谦自谓应为租庸使，众议以其人微地寒不宜遽任。',8,'支度务使孔谦自谓才能勤效，应为租庸使；众议以谦人微地寒，不当遽总重任，','自谓和众议分别归属；不以门第评议作能力事实。')
E=event('three_capitals_instituted','魏州升兴唐府建东京，太原建西京，镇州改真定府建北都',8,'以魏州为兴唐府，建东京。又于太原府建西京，又以镇州为真定府，建北都。',[],when='923年四月即位后',place='魏州、太原、镇州',note='北都此刻为镇州，与本年十一月太原改北都的后事分开，不用后期都名覆盖当前。')
claim('event',E,'description','《新五代史》亦记魏州东京、太原西京、镇州北都。',8,'以魏州為東京，太原為西京，鎮州為北都。','同月都名印证。',source='xinwudaishi-005-923-founding',relation='corroborates')
claim('event',E,'description','《旧五代史》另补元城县改兴唐县、贵乡县改广晋县。',8,'改元城縣為興唐縣，貴鄉縣為廣晉縣，','附属县名补证；不据此虚填现代坐标。',source='jiuwudaishi-029-923-founding',relation='adds')
E=event('wang_zhengyan_xingtang','王正言为礼部尚书，行兴唐尹',8,'以魏博节度判官王正言为礼部尚书，行兴唐尹；',[('王正言','礼部尚书、行兴唐尹')],when='923年四月即位后',place='兴唐府')
claim('event',E,'description','《旧五代史》同记王正言礼部尚书、行兴唐尹。',8,'以魏博節度判官王正言為禮部尚書，行興唐尹；','行职用原官衔，不改成实授仅有尹。',source='jiuwudaishi-029-923-founding',relation='corroborates')
E=event('meng_zhixiang_taiyuan','孟知祥任太原尹、西京副留守',8,'太原马步都虞候孟知祥为太原尹，充西京副留守；',[('孟知祥','太原尹、西京副留守')],when='923年四月即位后',place='太原、西京')
claim('event',E,'description','《旧五代史》同记孟知祥太原尹、西京副留守，旧职作河东军城都虞候。',8,'以河東軍城都虞候孟知祥為太原尹，充西京副留守；','旧职称谓与通鉴太原马步都虞候并列，不自动判完全等职。',source='jiuwudaishi-029-923-founding',relation='corroborates')
E=event('ren_huan_zhending','任圜任工部尚书、真定尹、北京副留守',8,'潞州观察判官任圜为工部尚书，兼真定尹，充北京副留守；',[('任圜','工部尚书兼真定尹、北京副留守')],when='923年四月即位后',place='真定、北都',note='原文北京与前北都并存，保留官衔；不是现代北京市。')
claim('event',E,'description','《旧五代史》任圓任工部尚书兼真定尹、北京副留守。',8,'以澤潞節度判官任圓為工部尚書兼真定尹，充北京副留守。','任圓与主书任圜同人同官同事；圓非圜繁体，疑转录原样保留而不新建任圆。',source='jiuwudaishi-029-923-founding',relation='corroborates')
event('jiji_northern_capital','皇子李继岌为北都留守、兴圣宫使',8,'皇子继岌为北都留守、兴圣宫使，判不军诸卫事。',[('继岌','北都留守、兴圣宫使')],when='923年四月即位后',place='北都、真定',note='判不军诸卫事疑转录，不释作不军具体官职；只提可确认两职，不更改引用。')
relationship('李存勖','继岌','父亲',8,'皇子继岌','皇子以本纪李存勖为主语，复用原父亲关系。')
event('tang_initial_territorial_count','主书记后唐初有十三节度、五十州',8,'时唐国所有凡十三节度、五十州。',[],when='923年即位时主书总述',place='后唐',note='史载汇总，不等于现代稳定疆界或所有州连续实际控制，未虚造十三节度名单。')
claim('event',used[8][-1],'description','《旧五代史》亦记节度一十三、州五十。',8,'是時，所管節度一十三，州五十。','本纪同阶段同数；非独立地理测绘。',source='jiuwudaishi-029-923-founding',relation='corroborates')
# Paragraph 9: posthumous honors, not deaths in 923.
E=event('honor_ancestor_zhiyi','李存勖追尊曾祖执宜为懿祖昭烈皇帝',9,'闰月，追尊皇曾祖执宜曰懿祖昭烈皇帝，',[('李存勖','追尊者'),('执宜','被追尊的曾祖')],when='923年闰四月',place='后唐',note='闰月承夏四月；追尊事件不是923年死亡或生前即位，执宜姓氏原书未在此具出，暂用带身份规范名。')
claim('event',E,'description','《旧五代史》记执宜为李克用之祖，庄宗即位追谥昭烈、庙号懿祖。',9,'莊宗即位，追諡為昭烈皇帝，廟號懿祖。','旧史本纪首段祖执宜承李克用主体，与主书皇曾祖一致；不把朱耶自动改作朱邪。',source='jiuwudaishi-025-ancestry',relation='corroborates')
E=event('honor_ancestor_guochang','李存勖追尊祖李国昌为献祖文皇帝',9,'祖国昌曰献祖文皇帝，',[('李存勖','追尊者'),('国昌','被追尊的祖父')],when='923年闰四月',place='后唐',note='主书文皇帝、新史文景有差，引用并存，不自动拼成唯一谥号。')
claim('event',E,'description','《新五代史》记国昌及祖妣秦氏谥文景，庙号献祖。',9,'祖國昌、祖妣秦氏皆謚曰文景，廟號獻祖；','与主书文不同谥号文字保留；秦氏姓名未知，不按姓氏合到其他秦氏。',source='xinwudaishi-005-923-founding',relation='conflicts')
claim('event',E,'description','《旧五代史》作庄宗即位，追谥国昌文皇、庙号献祖。',9,'莊宗即位，追諡為文皇，廟號獻祖。','与主书文皇互证，仍保留新史文景异文。',source='jiuwudaishi-025-ancestry',relation='corroborates')
E=event('honor_father_keyong','李存勖追尊父晋王李克用为太祖武皇帝',9,'考晋王曰太祖武皇帝。',[('李存勖','追尊父亲者'),('考晋王','受追尊的李克用')],when='923年闰四月',place='后唐',note='考是亡父李克用，不能与即位前晋王李存勖合并；并非李克用923年去世。')
claim('event',E,'description','《新五代史》同记考谥武、庙号太祖。',9,'考謚曰武，廟號太祖。','此处太祖为李克用，非梁太祖朱温或唐高祖。',source='xinwudaishi-005-923-founding',relation='corroborates')
E=event('seven_chamber_temple','后唐立宗庙于晋阳，共七室',9,'立宗庙于晋阳，以高祖、太宗、懿宗、昭宗洎懿祖以下为七室。',[],when='923年闰四月',place='晋阳',note='四唐帝及李氏本家三代七室，非当前七位统治者；高祖为唐高祖，不能沿用前蜀高祖王建。')
claim('event',E,'description','《新五代史》同记在太原立唐高祖、太宗、懿宗、昭宗等七庙。',9,'立廟于太原，自唐高祖、太宗、懿宗、昭宗為七廟。','晋阳与太原是本段同地指称；七室与七庙按书各存，不据此新增四位帝王生卒履历。',source='xinwudaishi-005-923-founding',relation='corroborates')
relationship('国昌','李克用','父亲',9,'烈考國昌，本名赤心','旧史李克用本纪烈考明确父；姓名赤心另保留引用，既有人物沿用李国昌。',source='jiuwudaishi-025-ancestry')
relationship('李克用','李存勖','父亲',9,'考晋王曰太祖武皇帝。','考晋王为亡父李克用，沿用全站关系方向。')
relationship('执宜','李存勖','曾祖父',9,'追尊皇曾祖执宜','明示皇曾祖，执宜是李存勖曾祖父；不把隔代关系写父亲。')
relationship('国昌','李存勖','祖父',9,'祖国昌曰献祖文皇帝','祖明示祖父，避免与父亲混淆。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7,10):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='连续校核四月建国任官与闰四月宗庙；复用建国事件；曹刘母嫡母区分、旧职追叙年未定、德林与判不军疑字不扩推；文与文景谥号并存。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(7,10)],next_paragraph=Q[10]['id'],supplements=supplements,coverage='卷272正文第7—9段，原文件12—14行；p7及p8开头复用首批快照，其余p8和p9由对应分段导出。',reviewed_questions=[
 {'paragraph_id':Q[7]['id'],'note':'event_tang_founded及原参与key复用；曹氏生母、刘氏嫡母明确，历史太后不错误指前蜀徐氏；李德休旧史证名字，后句德林不建新主体或李绛祖孙关系；作者轻浅评价带归属。'},
 {'paragraph_id':Q[8]['id'],'note':'李绍宏旧中门职及郭副是初追叙年null；恶恨与孔自谓为史述言论；北都此时镇州，北京官名非现代北京；判不军疑字不改释；十三节度五十州仅史载总数。'},
 {'paragraph_id':Q[9]['id'],'note':'闰月承四月；追尊不作死亡日期；执宜姓氏不据朱耶/朱邪自动转；主书献祖文、新史文景异文并列；庙中高祖明确唐高祖，不混王建；父祖曾祖方向各明确。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
