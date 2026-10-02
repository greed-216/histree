"""Curate consecutive Tongjian volume 271, year 922, paragraphs 13–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 21))
specs = [
 ('tongjian-271-922-spring',YEAR/'part-01/sources/library/tongjian-271-922-spring','16b51066','司马光等'),
 ('tongjian-271-922-yearend',P/'sources/library/tongjian-271-922-yearend','62141563','司马光等'),
 ('jiuwudaishi-029-922-wei',P/'sources/library/jiuwudaishi-029-922-wei','62141563','薛居正等'),
 ('jiuwudaishi-029-922-zhen-fall',P/'sources/library/jiuwudaishi-029-922-zhen-fall','62141563','薛居正等'),
 ('jiuwudaishi-029-922-yearend',P/'sources/library/jiuwudaishi-029-922-yearend','62141563','薛居正等'),
 ('xinwudaishi-028-he-zan',P/'sources/library/xinwudaishi-028-he-zan','62141563','欧阳修'),
 ('xinwudaishi-074-goryeo-wang-jian',P/'sources/library/xinwudaishi-074-goryeo-wang-jian','62141563','欧阳修'),
 ('liaoshi-002-tianzan',P/'sources/library/liaoshi-002-tianzan','62141563','脱脱等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0922-p013-p020',
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
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(13, 21):
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
people, used, reused, supplements = {}, {}, {'tongjian-271-922-spring'}, []

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
        citation = f'卷271·龙德二年（922）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0922_03_{len(B["claims"])+1:04d}'
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
            '敬塘':'石敬瑭','李绍荣':'元行钦','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271龙德二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='922年本段；确日未载', note='', year=922, place='五代十国', source=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0922_' + code
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
        edge = 'participation_zztj_271_0922_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_271_0922_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)
event('li_cunru_renamed_and_promoted','李存勖赐杨婆儿名李存儒，以为卫州刺史',13,'晋卫州刺史李存儒，本姓杨，名婆儿，以俳优得幸于晋王。颇有膂力，晋王赐姓名，以为刺史；',[('李存儒','以俳优受宠、赐姓名任刺史者'),('晋王','赐姓名任刺史者')],when='卫州陷落前的追叙；确年未载',year=None,place='卫州',note='赐姓改名主体一人，杨婆儿为别名；非按922八月授任。')
event('li_cunru_taxes_defenders','李存儒向防城卒征月课，准其归家',13,'志事掊敛，防城卒皆征月课纵归。',[('李存儒','征月课纵卒归者')],when='卫州陷落前任刺史期间；确年未载',year=None,place='卫州',note='职守时期背景，不虚构实际收款数或单次命令日期。')
event('liang_takes_weizhou','段凝、张朗夜渡河袭卫州，擒李存儒',13,'八月，庄宅使段凝与步军都指挥使张朗引兵夜渡河袭之，诘旦登城，执存儒，遂克卫州。',[('段凝','率军袭卫州者'),('张朗','共同袭城者'),('存儒','被擒的卫州刺史')],when='922年八月，夜渡河、翌晨登城',place='河、卫州',note='被俘不记死亡，未名河段不擅定具体渡口。')
claim('event',used[13][-1],'description','《旧五代史》亦记八月段凝陷卫州、李存儒被擒。',13,'八月，梁將段凝陷衛州，刺史李存儒被擒。','同月同俘获事实；旧史未列张朗，不因省略否认共同参与。',source='jiuwudaishi-029-922-wei',relation='corroborates')
event('liang_takes_qimen_three_places','戴思远与段凝攻陷淇门、共城、新乡',13,'戴思远又与凝攻陷淇门、共城、新乡，',[('戴思远','与段凝攻三处者'),('段凝','共同攻取者')],when='922年八月卫州陷后',place='淇门、共城、新乡')
event('jin_loses_western_supply','梁据澶州以西、相州以南，晋失军储三分之一',13,'于是澶州之西，相州之南，皆为梁有；晋人失军储三之一，梁军复振。',[],when='922年八月梁攻取诸地后',place='澶州以西、相州以南',note='三之一为史载约比，不推全军粮草绝对数，复振为史书叙述。')
event('zhang_lang_made_prefect','朱友贞以张朗为卫州刺史',13,'帝以张朗为卫州刺史。朗，徐州人也。',[('梁帝','任刺史的朱友贞'),('张朗','获任卫州刺史者')],when='922年八月取卫州后',place='卫州')
claim('person',people['张朗'],'description','张朗为徐州人，本段为梁步军都指挥使后任卫州刺史。',13,'朗，徐州人也。','地望不虚配坐标。')
event('chuqiu_attacks_dongyuan','张处球率七千兵突袭李存进营东垣渡',14,'九月，戊寅朔，张处瑾使其弟处球乘李存进无备，将兵七千人奄至东垣渡。',[('张处瑾','遣弟突袭者'),('处球','率兵突袭者'),('李存进','被突袭者')],when='922年九月戊寅朔',place='东垣渡')
relationship('张处瑾','处球','兄长',14,'张处瑾使其弟处球','明确其弟；处球不同于处琪，旧史本纪列三人，分别建主体。')
event('li_cunjin_killed_dongyuan','李存进桥上力战，晋骑夹击镇兵，存进战死',14,'镇兵及存进营门，存进狼狈引十馀人斗于桥上，镇兵退，晋骑兵断其后，夹击之，镇兵殆尽，存进亦战没。',[('李存进','桥上力战、战没者')],when='922年九月戊寅朔',place='东垣渡桥',note='镇兵殆尽非全军精确零生还；未把七千均记被杀。')
claim('person',people['李存进'],'death_year','李存进于922年九月戊寅朔战死。',14,'存进亦战没。','明确战没，年日依本段开头。')
event('fu_cunshen_commands_zhen','晋王以符存审为北面招讨使',14,'晋王以蕃汉马步总管李存审为北面招讨使。',[('晋王','任命者'),('李存审','继任北面招讨使的符存审')],when='922年九月李存进战没后',place='镇州')
event('chujin_requests_surrender','镇州粮力尽，张处瑾遣使请降，尚未答复符存审已至',14,'镇州食竭力尽，处瑾遣使诣行台请降，未报，存审兵至城下。',[('处瑾','遣使求降者'),('李存审','率军至城下者')],when='922年九月丙午前',place='镇州、行台',note='请降未报，不写已受降或主动交城。')
event('li_zaifeng_opens_zhenzhou','李再丰为内应，夜缒纳晋兵，天明入城',14,'丙午夜，城中将李再丰为内应，密投缒以纳晋兵，比明毕登，',[('李再丰','城中内应者')],when='922年九月丙午夜至翌晨',place='镇州',note='主书李再丰为内应，旧史具体投缒者为其子冲，父子角色分别补入。')
claim('event',used[14][-1],'description','《旧五代史》记投缒接晋军者为李再丰之子冲。',14,'丙午夜，趙將李再豐之子衝投縋以接王師，','补具体执行者，不把父子误作同人；冲仅见单名，暂用李冲（李再丰子）限定，勿并李克用养子李存信原李信等他人。',source='jiuwudaishi-029-922-zhen-fall',relation='adds')
pk=person('李冲（李再丰子）',14,'投缒接晋军的李再丰子','趙將李再豐之子衝投縋以接王師',source='jiuwudaishi-029-922-zhen-fall')
ek=used[14][-1];edge='participation_zztj_271_0922_li_chong_receives_jin'
B['person_events'].append(dict(key=edge,person_key=pk,event_key=ek,role='旧史明确投缒接晋军者',status='draft'))
claim('person_event',edge,'role','李冲（李再丰子）投缒接晋军。',14,'趙將李再豐之子衝投縋以接王師','父与子角色不同，旧史补充执行者。',source='jiuwudaishi-029-922-zhen-fall')
relationship('李再丰','李冲（李再丰子）','父亲',14,'趙將李再豐之子衝','明确之子；父亲方向李再丰→其子，单名限定身份。',source='jiuwudaishi-029-922-zhen-fall')
event('zhen_rebels_captured_and_executed','晋军俘张处瑾等，送行台后赵人请加酷刑',14,'执处瑾兄弟家人及其党高濛、李翥、齐俭送行台，赵人皆请而食之，',[('处瑾','被俘送行台者'),('高濛','被俘的张文礼党羽'),('李翥','被俘党羽'),('齐俭','被俘党羽')],when='922年九月丙午镇州入城后',place='镇州、行台',note='原书记食之为极端行刑叙述，未扩写人数、具体方法与细节；处瑾兄弟在旧史具名补证。')
claim('event',used[14][-1],'description','《旧五代史》明确俘处球、处瑾、处琪及其母，与高濛、李翥、齐俭等。',14,'獲處球、處瑾、處琪並其母，及同惡高濛李翥、齊儉等，','三兄弟分别具名，母未名不推另一女名；此时在922，未把张文礼已死重新当现场活俘。',source='jiuwudaishi-029-922-zhen-fall',relation='adds')
for name in ['张处球','张处琪']:
 pk=person(name,14,'旧史明确镇州陷后被俘者','獲處球、處瑾、處琪並其母，',source='jiuwudaishi-029-922-zhen-fall')
 edge='participation_zztj_271_0922_zhen_captured_'+pk
 B['person_events'].append(dict(key=edge,person_key=pk,event_key=used[14][-1],role='旧史列名被俘者',status='draft'))
 claim('person_event',edge,'role',name+'为旧史列名被俘者。',14,'獲處球、處瑾、處琪並其母，','不将处球与处琪合并。',source='jiuwudaishi-029-922-zhen-fall')
event('zhang_wenli_corpse_punished','赵人在市中磔张文礼尸',14,'磔张文礼尸于市。',[('张文礼','已死后尸受刑者')],when='922年九月镇州陷后',place='镇州市',note='尸说明921已卒，本次不再生成922死亡事实。')
event('wang_rong_remains_buried','晋王命祭葬从灰烬中找到的王镕遗骸',14,'赵王故侍者得赵王遗骸于灰烬中，晋王命祭而葬之。',[('赵王','被祭葬的王镕'),('晋王','命祭葬者')],when='922年九月镇州陷后',place='镇州',note='未名故侍者不虚建姓名；王镕死于921，祭葬非死亡日。')
event('fu_xi_chengde_appointment','晋以符习为成德节度使',14,'以赵将符习为成德节度使，',[('符习','任成德节度使者')],when='922年九月镇州陷后',place='成德、镇州',note='随后辞任见下一段，任命与辞任分录。')
event('zhao_prefectures_reassigned','乌震、赵仁贞、李再丰分别任赵深冀州刺史',14,'乌震为赵州刺史，赵仁贞为深州刺史，李再丰为冀州刺史。震，信都人也。',[('乌震','任赵州刺史者'),('赵仁贞','任深州刺史者'),('李再丰','任冀州刺史者')],when='922年九月镇州陷后',place='赵州、深州、冀州')
claim('person',people['乌震'],'description','乌震为信都人。',14,'震，信都人也。','史载籍贯不直接指定现代地理坐标。')
event('fu_xi_declines_for_mourning','符习辞成德任，称先葬王镕，再赴行台听命',15,'符习不敢当成德，辞曰：“故使无后而未葬，习当斩衰以葬之，俟礼毕听命。”既葬，即诣行台。',[('符习','辞任、葬故使后听命者')],when='922年镇州陷、成德任命后',place='镇州、行台',note='无后为符习当时言论；既有补证王昭诲获救，不据此删除王镕后裔；斩衰不代表亲生父子。')
event('jin_king_takes_chengde','赵人请晋王兼领成德节度使，晋王从之',15,'赵人请晋王兼领成德节度使，从之。',[('晋王','兼领成德者')],when='922年符习辞任后',place='成德')
event('yining_army_proposed','晋王割相卫置义宁军，以符习为节度使',15,'晋王割相、卫二州置义宁军，以习为节度使。',[('晋王','设军任官者'),('符习','获义宁任命者')],when='922年本段成德安排后',place='相州、卫州、义宁军',note='八月卫州为梁所据，本句为割军任官安排，未推相卫实际皆已收复；随后符习辞任。')
event('fu_xi_requests_henan_command','符习辞割魏博，愿取河南一镇，获天平及东南招讨任',15,'习辞曰：“魏博霸府，不可分也，愿得河南一镇，习自取之。”乃以为天平节度使、东南面招讨使。',[('符习','请求取河南一镇、获任天平招讨者')],when='922年义宁任命后',place='魏博、天平军',note='愿自取为计划，天平旧史称遥领，不写此时已从梁夺郓州。')
claim('event',used[15][-1],'description','《旧五代史》明确符习遥领天平军节度使。',15,'乃以符習遙領天平軍節度使。','遥领表示任职安排，不当已经据有治所。',source='jiuwudaishi-029-922-zhen-fall',relation='adds')
event('fu_cunshen_appointed_shizhong','符存审加兼侍中',15,'加李存审兼侍中。',[('李存审','加兼侍中的符存审')],when='922年镇州陷后任官本段',place='晋')
event('zhang_chengye_dies','张承业卒，曹太夫人为其行服',16,'十一月，戊寅，晋特进、河东监军使张承业卒，曹太夫人诣其第，为之行服，如子侄之礼。',[('张承业','去世的河东监军'),('曹太夫人','至其第行服者')],when='922年十一月戊寅',place='河东',note='如子侄之礼为行服比拟，不创建曹氏与张承业血缘亲属关系。')
claim('person',people['张承业'],'death_year','张承业于922年十一月戊寅去世。',16,'十一月，戊寅，晋特进、河东监军使张承业卒，','本年确月日，不外推病因。')
claim('event',used[16][-1],'time_original','《旧五代史》亦记十一月河东监军张承业卒。',16,'十一月，河東監軍張承業卒。','同月补证，旧史此段未列日。',source='jiuwudaishi-029-922-yearend',relation='corroborates')
event('jin_mourns_chengye','李存勖闻张承业丧，累日不食',16,'晋王闻其丧，不食者累日。',[('晋王','闻丧不食者')],when='922年十一月张承业死后',place='晋')
event('he_zan_controls_hedong','何瓒代知河东军府事',16,'命河东留守判官何瓚代知河东军府事。',[('何瓚','代知河东军府事者')],when='922年十一月张承业死后',place='河东')
claim('person',people['何瓒'],'description','《新五代史》记何瓒为闽人，唐末进士；承业卒后代知留守事。',16,'何瓚，閩人也，唐末舉進士及第。','何瓚规范为何瓒，出生年未载不反推；唐末进士与后段代知分开定位。',source='xinwudaishi-028-he-zan',relation='adds')
claim('event',used[16][-1],'description','《新五代史》亦记承业卒、何瓒代知留守事。',16,'承業卒，瓚代知留守事。','明确承业后接任，不补不存在的正式节度使任命。',source='xinwudaishi-028-he-zan',relation='corroborates')
event('zhang_xian_controls_zhen','张宪兼镇冀观察判官，权镇州军府事',17,Q[17]['text'],[('晋王','命兼权者'),('张宪','兼判官、权镇州军府事者')],when='922年十二月',place='魏博、镇冀、镇州')
claim('person',people['张宪'],'description','张宪为晋阳人，本为魏博观察判官。',17,'魏博观察判官晋阳张宪','籍贯非新任所在地，不混成晋阳观察判官。')
claim('event',used[17][-1],'time_original','《旧五代史》亦记十二月张宪权知镇州军州事。',17,'十二月，以魏州觀察判官張憲權知鎮州軍州事。','两书魏博、魏州职名与军府、军州措辞并列，同月任职相合。',source='jiuwudaishi-029-922-yearend',relation='corroborates')
event('zhao_jiliang_advises_tax_relief','赵季良因税逋负受责，劝李存勖爱民以保河北',18,Q[18]['text'],[('晋王','责税后采纳劝谏者'),('赵季良','以民心劝谏的济阴司录')],when='通鉴922年末本段；确日未载',place='魏州',note='若民心变恐河北不保为赵季良警告，未记已发生起义；旧史夹引九国志不是另一本已校原本。')
event('zhao_jiliang_enters_council','李存勖谢赵季良，自此令预谋议',18,'王悦，谢之。自是重之，每预谋议。',[('晋王','谢且重用者'),('赵季良','参与谋议者')],when='赵季良税务劝谏后；起止未载',year=None,place='魏州')
event('khitan_tianzan_era','契丹改元天赞',19,Q[19]['text'],[('契丹主','当时契丹主阿保机')],when='922年是岁；辽史补二月癸酉',place='契丹',note='主书只记是岁；辽史具体月日作为独立补证，不填年末十二月。')
claim('event',used[19][-1],'time_original','《辽史》天赞元年春二月癸酉诏改元，赦军前殊死以下。',19,'天贊元年春二月庚申，復徇幽、薊地。癸酉，詔改元，赦軍前殊死以下。','癸酉为诏改元日，庚申是另一出征日，未混用；本段只引用改元和赦免。',source='liaoshi-002-tianzan',relation='adds')
event('goryeo_wang_jian_overthrows_gungye','高丽王建杀大封王躬乂而自立',20,'大封王躬乂，性残忍，海军统帅王建杀之，自立，复称高丽王，',[('躬乂','被杀的大封王'),('王建（高丽）','杀躬乂自立、复称高丽王的海军统帅')],when='通鉴附922年末；本句未明发生年，待考',year=None,place='大封、高丽',note='大封王为头衔，未认定躬乂姓王；王建限定高丽，绝不并前蜀王建。编年附载不直接当922即位。')
claim('person',people['王建（高丽）'],'description','《新五代史》另记权知国事王建、高丽大族及长兴三年受封。',20,'建，高麗大族也。','新史此段长兴三年为中原授封记录，不证明本段自立发生于922或932；只补身份，未提前另录长兴授封事件。',source='xinwudaishi-074-goryeo-wang-jian',relation='adds')
event('goryeo_capital_designation','高丽王建以开州为东京、平壤为西京',20,'以开州为东京，平壤为西京。建俭约宽厚，国人安之。',[('王建（高丽）','设两京者')],when='王建自立后本段；确年未载',year=None,place='开州、平壤',note='开州、平壤保留史载名称，未配现代开城坐标；俭约宽厚与国人安为史书评价，不推全民调查。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(13,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='年末八段连续校核；处球处琪分人、投缒父子区分、同名高丽王建限定；追叙与高丽年未定保持null；辽史补改元月日。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=271,year=922,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,21)],next_paragraph='zztj-v272-y0923-p001',supplements=supplements,coverage='卷271第13—20段，原文件81—88行连续覆盖；89—90空白、91后唐纪不作本年正文。',reviewed_questions=[
 {'paragraph_id':Q[13]['id'],'note':'杨婆儿赐名李存儒为同一人，俳优与任职为前事追叙；被俘不记死，晋失军储比保留史数。'},
 {'paragraph_id':Q[14]['id'],'note':'旧史明确处球处瑾处琪三人；李再丰内应与其子冲投缒分别记录，父亲方向明确。张文礼尸刑及王镕葬非新死亡。高蒙别名高濛，异体匹配原引不改。'},
 {'paragraph_id':Q[15]['id'],'note':'符习称故使无后为言论，已有王昭诲获救补证不删除；义宁军安排不推卫州已克复，天平遥领不当已据郓州。'},
 {'paragraph_id':Q[16]['id'],'note':'曹氏如子侄礼不建与张承业血缘；何瓚规范何瓒，新史独立补代知留守与闽人进士。'},
 {'paragraph_id':Q[17]['id'],'note':'晋阳为张宪籍贯，任职为魏博观察判官兼镇冀，权军府与本纪军州措辞分别保留。'},
 {'paragraph_id':Q[18]['id'],'note':'民心离为谏者预测，未写已失河北；旧史九国志夹注未计独立原书。'},
 {'paragraph_id':Q[19]['id'],'note':'辽史二月癸酉诏改元补本书是岁，不混同庚申出征日。'},
 {'paragraph_id':Q[20]['id'],'note':'躬乂之前王为头衔，未虚设王姓；王建限定高丽与前蜀分人。所在922条不证明政变与两京设置实际年，事件年份null待考；新史長興三年是后续授封非本次自立年。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
