"""Curate consecutive Tongjian volume 272, year 923, paragraphs 1–6."""
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
 ('tongjian-272-923-spring',P/'sources/library/tongjian-272-923-spring','0b0c460a','司马光等'),
 ('jiuwudaishi-029-923-preparation',P/'sources/library/jiuwudaishi-029-923-preparation','0b0c460a','薛居正等'),
 ('jiuwudaishi-010-jitao-defection',P/'sources/library/jiuwudaishi-010-jitao-defection','0b0c460a','薛居正等'),
 ('xinwudaishi-005-jitao-defection',P/'sources/library/xinwudaishi-005-jitao-defection','0b0c460a','欧阳修'),
 ('jiuwudaishi-110-guowei-youth',P/'sources/library/jiuwudaishi-110-guowei-youth','0b0c460a','薛居正等'),
 ('xinwudaishi-067-wuyue-court',P/'sources/library/xinwudaishi-067-wuyue-court','0b0c460a','欧阳修'),
 ('jiuwudaishi-056-cunshen-lulong',P/'sources/library/jiuwudaishi-056-cunshen-lulong','0b0c460a','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p001-p006',
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
for n in range(1, 7):
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
        citation = f'卷272·同光元年（923）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_272_0923_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','高祖':'王建','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷272同光元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='923年本段；确日未载', note='', year=923, place='五代十国', source=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_272_0923_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_272_0923_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
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
event('jin_prepares_bureaucracy','晋王下教置百官，欲选前朝士族为相',1,'春，二月，晋王下教置百官，于四镇判官中选前朝士族，欲以为相。',[('晋王','下教置百官者')],when='923年二月',place='晋',note='尚未四月称帝，下教与后来即位分开；选前朝士族为拟任规则。')
claim('event',used[1][-1],'description','《旧五代史》记诸镇劝进后制置百官省寺、仗卫法物，拟四月行即位礼。',1,'乃命有司製置百官省寺仗衛法物，期以四月行即位之禮，','本段承二月；期是筹备计划，实际即位另按主书后续段落。',source='jiuwudaishi-029-923-preparation',relation='adds')
event('lu_zhi_declines_chancellorship','卢质固辞为相，推荐豆卢革、卢程',1,'河东节度判官卢质为之首，质固辞，请以义武节度判官豆卢革、河东观察判官卢程为之；',[('卢质','辞相并荐二人者'),('豆卢革','被荐的义武节度判官'),('卢程','被荐的河东观察判官')],when='923年二月',place='晋')
event('doulu_lucheng_appointed','豆卢革、卢程任行台左右丞相，卢质为礼部尚书',1,'王即召革、程拜行台左、右丞相，以质为礼部尚书。',[('晋王','召拜者'),('豆卢革','任行台左丞相者'),('卢程','任行台右丞相者'),('卢质','改任礼部尚书者')],when='923年二月',place='晋行台',note='左右按革程先后对应，不提前混成四月门下中书侍郎。')
event('lu_zhi_ritual_preparation','旧史记卢质任大礼使，筹备即位礼',1,'以河東節度判官廬質為大禮使。',[('卢质','筹备即位礼的大礼使')],when='923年二月条筹备阶段；确日未载',place='晋',source='jiuwudaishi-029-923-preparation',note='旧史廬質与主书卢质同职同筹礼背景对读；廬非简单盧繁体，疑字保留而不新建廬质，不填独立日期。')
event('li_sigong_dies','旧史补李嗣肱于二月去世',1,'二月，新州團練使李嗣肱卒。',[('李嗣肱','去世的新州团练使')],when='923年二月；确日未载',place='新州',source='jiuwudaishi-029-923-preparation',note='同月本纪补既有主体末期，与前一年代州山北任职不同阶段；不混李嗣弼。')
claim('person',people['李嗣肱'],'death_year','李嗣肱于923年二月去世。',1,'二月，新州團練使李嗣肱卒。','来自旧史本纪独立补证，未冒充通鉴本段明文。',source='jiuwudaishi-029-923-preparation')
event('liang_invests_wuyue_king','朱友贞遣崔协册钱镠为吴越国王',2,'梁主遣兵部侍郎崔协等册命吴越王镠为吴越国王。',[('梁主','遣册使的朱友贞'),('崔协','奉册的兵部侍郎'),('吴越王镠','受吴越国王册命者')],when='923年二月本段；确日未载',place='梁、吴越',note='与907吴越王、后来唐玉册各是不同册命阶段，不合成一次。')
event('wuyue_establishes_court','钱镠建国，采用宫殿朝廷称臣等制度',2,'丁卯，镠始建国，仪卫名称多如天子之制，谓所居曰宫殿，府署曰朝廷，教令下统内曰制敕，将吏皆称臣，惟不改元，表疏称吴越国而不言军。',[('镠','采用国号礼仪而未改元者')],when='923年二月丁卯；主书纪时',place='吴越',note='始建国为本段制度与称谓，不能删掉此前吴越政权记录；不改元明确，不推正式称帝。')
claim('event',used[2][-1],'description','《新五代史》亦记宫殿、府朝、官属称臣，但将之连于后唐玉册金印之后。',2,'自稱吳越國王，更名所居曰宮殿、府曰朝，官屬皆稱臣，','同类制度记载，叙次不同：新史前句唐莊宗入洛并授玉册，主书本条为梁册命后；不移主书丁卯到后唐授玉册日。',source='xinwudaishi-067-wuyue-court',relation='conflicts')
event('qian_chuanguan_takes_administration','钱传瓘任镇海镇东留后，总军府事',2,'以清海节度使兼侍中传瓘为镇海、镇东留后，总军府事。',[('传瓘','任两镇留后、总军府者')],when='923年二月吴越建国本段',place='镇海、镇东',note='本时史载名传瓘，与新史元瓘同人；留后不直接写成已继吴越王位。')
claim('person',people['钱传瓘'],'description','《新五代史》称钱镠子元瓘，受镇海等军节度。',2,'鏐因以鎮海等軍節度授其子元瓘，','钱传瓘既有主体，元瓘是另一阶段史载名，不重复建人；新史授军叙次与主书不同，不合成同日任职。',source='xinwudaishi-067-wuyue-court',relation='adds')
event('wuyue_officials_created','吴越置丞相侍郎郎中等百官',2,'置百官，有丞相、侍郎、郎中、员外郎、客省等使。',[],when='923年二月本段吴越建国后',place='吴越',note='仅建立明确制度事件，未名官员不虚构姓名或任命名单。')
event('wei_shen_persuade_jitao','魏琢、申蒙以晋将被梁并劝李继韬',3,'李继韬虽受晋王命为安义留后，终不自安，幕僚魏琢、牙将申蒙复从而间之曰：“晋朝无人，终为梁所并耳。”',[('继韬','受劝的安义留后'),('魏琢','游说的幕僚'),('申蒙','游说的牙将')],when='923年春本段，三月遣弟投梁前',place='安义军、潞州',note='终为梁并为游说意见，未当历史结局；安义留后任命已录922，不重复新建任命事件。')
event('jinn_recalls_zhang_ren','晋王召张居翰、任圜赴魏州',3,'会晋王置百官，三月，召监军张居翰、节度判官任圜赴魏州，',[('晋王','召官者'),('张居翰','被召的监军'),('任圜','被召的节度判官')],when='923年三月',place='魏州',note='召赴不能直接推实际到达日；召二人不代表已下令讨李继韬。')
event('jiyuan_urges_liang_submission','魏琢、申蒙再游说，李继远亦劝兄依梁',3,'琢、蒙复说继韬曰：“王急召二人，情可知矣。”继韬弟继远亦劝继韬自托于梁，',[('魏琢','再游说者'),('申蒙','再游说者'),('继远','劝兄投梁者'),('继韬','受劝者')],when='923年三月召二人后',place='潞州',note='所谓急召含意是琢蒙推断，不说晋王实际计划诛继韬。')
relationship('继韬','继远','兄长',3,'继韬弟继远','弟字明确；李继韬是李继远兄长。')
event('jitao_sends_brother_to_liang','李继韬遣李继远至大梁，以泽潞降梁',3,'继韬乃使继远诣大梁，请以泽潞为梁臣。',[('继韬','以泽潞降梁、遣弟者'),('继远','奉使大梁者')],when='923年三月',place='泽州、潞州、大梁',note='泽州旧将裴约不从另录，不把请以泽潞等同全境已交割。')
claim('event',used[3][-1],'time_original','《新五代史》记同光元年春三月李继韬以潞州叛附梁。',3,'同光元年春三月，李繼韜以潞州叛附于梁。','同月补证，叛是新史立场用字，展示用投梁降梁。',source='xinwudaishi-005-jitao-defection',relation='corroborates')
claim('event',used[3][-1],'description','《旧五代史》记龙德三年三月李继韬遣使以城归梁。',3,'龍德三年春三月，晉潞州節度留後李繼韜遣使以城歸順。','龙德三年与同光元年同923，归顺是梁本纪叙述视角，不改晋方背叛描述。',source='jiuwudaishi-010-jitao-defection',relation='corroborates')
event('liang_appoints_jitao_kuangyi','梁改安义为匡义，以李继韬为节度使同平章事',3,'梁主大喜，更命安义军曰匡义，以继韬为节度使、同平章事。',[('梁主','改军、授官者'),('继韬','获匡义节度同平章事者')],when='923年三月投梁后',place='匡义军、潞州')
event('jitao_sends_two_sons_hostages','李继韬以二子为质',3,'继韬以二子为质。',[('继韬','以二子为质者')],when='923年三月投梁时',place='梁、潞州',note='二子未具名，不虚构个名或并其他已有人物。')
claim('event',used[3][-1],'description','《旧五代史》亦记以二幼子为质。',3,'仍以二幼子為質。','补幼子年龄阶段，不据幼填精确年龄。',source='jiuwudaishi-010-jitao-defection',relation='adds')
event('pei_yue_holds_zezhou','裴约不从李继韬投梁，据泽州自守',4,'安义旧将裴约戍泽州，泣谕其众曰：',[('裴约','不从投梁、据泽州守者')],when='923年三月李继韬投梁后',place='泽州',note='逾二纪为裴约自述服事故使时长，不据此推准确从军年；故使为李嗣昭。')
claim('event',used[4][-1],'description','裴约以李嗣昭分财享士、志灭仇雠及未葬为由，拒从李继韬。',4,'遂据州自守。','言论理由及实际守城分清，未说此刻泽州已被梁取。')
event('dong_zhang_attacks_zezhou','梁任董璋泽州刺史，命攻裴约',4,'梁主以其骁将董璋为泽州刺史，将兵攻之。',[('梁主','任命遣攻者'),('董璋','任刺史、攻泽州者'),('裴约','受攻守城者')],when='923年三月投梁后',place='泽州',note='梁任命与实际据城分清，不把授刺史填为城已攻克。')
claim('event',used[4][-1],'description','《旧五代史》亦记裴约不从，梁帝命董璋为泽州刺史率兵攻之。',4,'澤州刺史裴約不從繼韜之謀，帝命董璋為澤州刺史，令將兵攻之。','旧史称裴约刺史而主书安义旧将，分别保留；帝在梁本纪指朱友贞。',source='jiuwudaishi-010-jitao-defection',relation='corroborates')
event('guo_wei_joins_jitao','郭威应李继韬募士',5,'继韬散财募士，尧山人郭威往应募。',[('继韬','散财募士者'),('郭威','应募者')],when='通鉴附923年春；李继韬募兵阶段，确年未定',year=None,place='潞州',note='旧史记入募十八、平梁时二十一，年龄与父卒子接任叙次有疑；不强推入募年或生年。')
claim('person',people['郭威'],'description','本段郭威为尧山人，当前记早年应募。',5,'尧山人郭威往应募。','籍贯据本句；旧史周太祖本纪回查同一人，不提前创建称帝事件或生年。')
claim('event',used[5][-1],'description','《旧五代史》记郭威避吏壶关、依常氏后应募，称时年十八。',5,'帝時年十八，避吏壺關，依故人常氏，遂往應募。','该史后句平梁时年二十一，与前文李嗣昭战殁后募士顺序难合，年龄仅作原书说法，不作出生年推算。',source='jiuwudaishi-110-guowei-youth',relation='adds')
event('guo_wei_kills_and_is_imprisoned','郭威使气杀人，被拘入狱',5,'威使气杀人，系狱，',[('威','杀人而被拘者')],when='李继韬募兵后郭威早年；确年未载',year=None,place='潞州',note='使气为作者叙述；受害者未名，不建立虚构人物。')
claim('event',used[5][-1],'description','《旧五代史》记郭威因醉与上党市屠者冲突，市人执之交吏。',5,'市人執之屬吏，','该段此前事刂其腹疑电子字形，不静默改字；主书直接记杀人，旧史补市屠和交吏过程，无名屠者不虚建。',source='jiuwudaishi-110-guowei-youth',relation='adds')
event('jitao_releases_guo_wei','李继韬惜郭威才勇，令其逃脱',5,'继韬惜其才勇而逸之。',[('继韬','令其脱拘者'),('郭威','获放逃脱者')],when='郭威被拘后；确年未载',year=None,place='潞州',note='逸之不等同合法赦免，不生成后梁皇帝赦郭威事件。')
event('khitan_attacks_youzhou_923','契丹入寇幽州',6,'契丹寇幽州，',[],when='923年春，己卯调帅前；确日未载',place='幽州',note='主书未具名此次率军者，不把阿保机默认作亲自领军。')
event('guo_recommends_cunshen','郭崇韬向晋王荐符存审镇守幽州',6,'晋王问帅子郭崇韬，崇韬荐横海节度使李存审。',[('晋王','询将者'),('郭崇韬','推荐者'),('李存审','被荐的符存审')],when='923年春契丹入寇后',place='晋、幽州',note='问帅子疑子为于或其他转录，保留快照，不把郭崇韬读成晋王之子。')
claim('event',used[6][-1],'description','《旧五代史》记郭崇韬认为汴寇未平、继韬背叛，北边防御非符存审不可。',6,'韜奏曰：「汴寇未平，繼韜背叛，北邊捍禦，非存審不可。」','此段人物为符存审传，韬指郭崇韬；观点归属奏者，非客观排他性能力结论。',source='jiuwudaishi-056-cunshen-lulong',relation='adds')
event('cunshen_transferred_lulong','符存审卧病，改任卢龙节度，舆疾赴镇',6,'时存审卧病，己卯，徙存审为卢龙节度使，舆疾赴镇，',[('李存审','带病任卢龙赴镇者')],when='923年三月己卯；四月即位前',place='卢龙、幽州',note='三月承此前三月条，未换算公历；病未具体名不设现代诊断。')
claim('event',used[6][-1],'description','《旧五代史》亦记符存审陈病、受幽州卢龙节度命，自镇州赴任。',6,'既而詔存審以本官充幽州盧龍節度使，自鎮州之任。','补出发地，不将同段后续同光初加官混成己卯已获。',source='jiuwudaishi-056-cunshen-lulong',relation='corroborates')
event('siyuan_leads_henghai','李嗣源领横海节度使',6,'以蕃汉马步副总管李嗣源领横海节度使。',[('李嗣源','领横海节度使者')],when='923年三月己卯调帅本段',place='横海军',note='领职不推本人当天实驻横海治所。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,7):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='923春首六段连续校核；筹备与称帝分开，吴越制度新史叙次不同，李继韬弟及泽潞抵抗分别录；郭威年龄不推出生年、入募时未定；问帅子不作亲子关系。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph=Q[7]['id'],supplements=supplements,coverage='卷272正文第1—6段，原文件6—11行；导出快照含结构和后续片段，正文账本范围仅本批六段。',reviewed_questions=[
 {'paragraph_id':Q[1]['id'],'note':'二月置官尚未称帝；旧史筹备即位与大礼使独立补证，廬質疑字不作自动繁简转换；李嗣肱二月卒补既有主体。'},
 {'paragraph_id':Q[2]['id'],'note':'梁册命、丁卯制度，与新史庄宗入洛玉册后相关制度叙次分别呈现；不改元未称帝；传瓘与元瓘同人，任留后未继王位。'},
 {'paragraph_id':Q[3]['id'],'note':'琢蒙以召两人推诛是游说判断；新旧史同三月投梁，弟继远长幼明确；二幼子未具名不虚建；泽州裴约不从不推全境交割。'},
 {'paragraph_id':Q[4]['id'],'note':'裴约主书旧将与旧史刺史不同身份措辞保留；梁授董璋刺史不当已据城。'},
 {'paragraph_id':Q[5]['id'],'note':'旧史入募十八、平梁二十一与嗣昭卒后叙次存在疑点，郭威本段早年年null；受害市屠未名，事刂字形不改；逸非皇帝赦。'},
 {'paragraph_id':Q[6]['id'],'note':'问帅子疑转录，不建立郭崇韬为晋王之子；符存审病不诊断，带病赴幽州有旧史补证，领横海不推驻地。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
