"""Curate consecutive Tongjian volume 271, year 922, paragraphs 8–12."""
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
 ('jiuwudaishi-029-922-zhen-siege',YEAR/'part-01/sources/library/jiuwudaishi-029-922-zhen-siege','16b51066','薛居正等'),
 ('jiuwudaishi-052-sizhao-death',P/'sources/library/jiuwudaishi-052-sizhao-death','805422d7','薛居正等'),
 ('jiuwudaishi-052-sizhao-sons',P/'sources/library/jiuwudaishi-052-sizhao-sons','805422d7','薛居正等'),
 ('jiuwudaishi-052-jitao-coup',P/'sources/library/jiuwudaishi-052-jitao-coup','805422d7','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0922-p008-p012',
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
for n in range(8, 13):
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
people, used, reused, supplements = {}, {}, {'tongjian-271-922-spring','jiuwudaishi-029-922-zhen-siege'}, []

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
    ck = f'claim_zztj_271_0922_02_{len(B["claims"])+1:04d}'
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
            '敬塘':'石敬瑭','李绍荣':'元行钦','汉主岩':'刘岩','岩':'刘岩','继俦':'李继俦','继韬':'李继韬','继达':'李继达','继忠':'李继忠','继能':'李继能','继袭':'李继袭','继远':'李继远','存渥':'李存渥','圜':'任圜','承纲':'王承纲','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'李继俦':['李繼儔'],'李继韬':['李繼韜'],'李继达':['李繼達'],'李继能':['李繼能'],'李继袭':['李繼襲'],'李存渥':[],'王承纲':['王承綱'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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
event('shu_takes_wang_daughter','王宗衍将待嫁的王承纲女取入宫',8,'夏，四月，蜀军使王承纲女将嫁，蜀主取之入宫。',[('王承纲','待嫁女之父'),('王承纲女','待嫁而被取入宫者'),('蜀主','取女入宫的王宗衍')],when='922年四月',place='蜀',note='将嫁尚未成婚，未具名未婚夫不创建；取入宫不推已授某妃位。')
relationship('王承纲','王承纲女','父亲',8,'蜀军使王承纲女将嫁','父亲关系方向王承纲→其女；女子未具名，用父名限定身份。')
event('wang_chenggang_exiled','王承纲请求放女，王宗衍怒而流其于茂州',8,'承纲请之，蜀主怒，流于茂州。',[('承纲','请求女、被流放者'),('蜀主','命流放者')],when='922年四月取女后',place='茂州')
event('wang_daughter_suicide','王承纲女闻父获罪，自杀',8,'女闻父得罪，自杀。',[('王承纲女','闻父罪而自杀者')],when='922年四月父流放后；确日未载',place='蜀',note='联系本段父女上下文，未虚构自杀地点、方法或未婚夫。')
event('sizhao_ambushes_supply_troops','张处瑾遣千人迎粮九门，李嗣昭伏击',8,'甲戌，张处瑾遣兵千人迎粮于九门，李嗣昭设伏于故营，邀击之，杀获殆尽，馀五人匿于墙墟间，',[('张处瑾','遣迎粮军者'),('李嗣昭','设伏邀击者')],when='922年四月甲戌',place='九门、镇州故营',note='通鉴记千人及余五人；旧史传另记王处球军、余三人、七月二十四日，并列待考，不覆盖主线。')
claim('event',used[8][-1],'description','《旧五代史》李嗣昭传记王处球军出九门，余三人；并记七月二十四日。',8,'七月二十四日，王處球之兵出自九門，','与主书遣军归张处瑾、四月甲戌及余五人不同；传首莊守亦疑电子本文字，未自动改字。旧史本纪另作四月，三者并列校核。',source='jiuwudaishi-052-sizhao-death',relation='conflicts')
event('sizhao_arrow_injury','李嗣昭环马射残敌，中箭后拔箭还射',8,'镇兵发矢中其脑，',[('李嗣昭','中箭仍射敌者')],when='922年四月甲戌伏击后',place='镇州墙墟',note='通鉴箙处为私用字形，快照不改；展示只述明确动作，不将缺字解释为未经核实器械。')
claim('event',used[8][-1],'description','李嗣昭箭尽，拔脑上敌矢还射，一发射杀敌人。',8,'拔矢于脑以射之，一发而殪。','行为据本句，不据电子字形猜补装备名称。')
claim('event',used[8][-1],'description','《旧五代史》亦记脑部中箭，箙中矢尽，拔敌矢还射。',8,'為賊矢中腦，嗣昭箙中矢盡，拔賊矢於腦射賊，一發而殪之。','旧史明确箙字，可供私用字形对读；不修改主书快照。',source='jiuwudaishi-052-sizhao-death',relation='corroborates')
event('sizhao_dies_in_camp','李嗣昭夜间因箭伤流血不止而卒',8,'会日暮，还营，创流血不止。是夕卒。',[('李嗣昭','还营后当夜去世者')],when='922年四月甲戌当夜；旧史传日期异说',place='镇州行营',note='死亡为当夜，与主书甲戌连续；旧史本纪支持四月，列传有七月二十四日异说，精确日期仍待纸本校。')
claim('event',used[8][-1],'time_original','《旧五代史》本纪记夏四月李嗣昭中流矢、卒于师。',8,'夏四月，嗣昭為流矢所中，卒於師。','与通鉴四月相合，本纪未列日；同书列传七月二十四日另存冲突。',source='jiuwudaishi-029-922-zhen-siege',relation='corroborates')
claim('event',used[8][-1],'time_original','《旧五代史》列传将受伤系七月二十四日，记是夜卒。',8,'嗣昭日暮還營，所傷血流不止，是夜卒。','联系本段前句七月二十四日，与通鉴及旧史本纪四月冲突；不强换公历日期。',source='jiuwudaishi-052-sizhao-death',relation='conflicts')
claim('person',people['李嗣昭'],'death_year','李嗣昭于922年战中负伤去世。',8,'是夕卒。','年承主书龙德二年，日期异说分别引用。')
event('jin_mourns_sizhao','李存勖闻李嗣昭死，累日不御酒肉',8,'晋王闻之，不御酒肉者累日。',[('晋王','闻死禁酒肉者')],when='922年李嗣昭死后',place='晋')
event('ren_huan_commands_sizhao_troops','李嗣昭遗命泽潞兵授任圜，任圜督军攻镇州',8,'嗣昭遗命：悉以泽、潞兵授节度判官任圜，使督诸军攻镇州，号令如一，镇人不知嗣昭之死。圜，三原人也。',[('李嗣昭','作遗命者'),('任圜','受命督泽潞兵攻镇者')],when='922年李嗣昭临终遗命及卒后',place='泽州、潞州、镇州',note='遗命和执行连续合录；镇人不知死为原书叙述，不推一直隐瞒至镇降。')
claim('person',people['任圜'],'description','任圜为三原人，本段任节度判官。',8,'圜，三原人也。','史载籍贯不填未经核实坐标。')
event('li_cunjin_appointed_commander','晋王以李存进为北面招讨使',9,'晋王以天雄马步都指挥使、振武节度使李存进为北面招讨使。',[('晋王','任招讨使者'),('李存进','继任招讨使者')],when='922年李嗣昭卒后',place='镇州')
event('jinn_orders_sizhao_burial','晋王命李嗣昭诸子护丧归晋阳',9,'命嗣昭诸子护丧归葬晋阳；',[('晋王','命归葬者'),('李嗣昭','被护丧者')],when='922年李嗣昭卒后',place='晋阳',note='命令与执行分录，未把晋阳写成实际葬地。')
event('ji_neng_returns_luzhou','李继能不受命，拥父丧与牙兵归潞州',9,'其子继能不受命，帅父牙兵数千，自行营拥丧归潞州。',[('继能','拥丧归潞违命者'),('李嗣昭','被护送之父')],when='922年李嗣昭卒后',place='镇州行营、潞州')
event('cunwo_flees_sizhao_sons','李存渥奉命追谕，李嗣昭诸子欲杀之，存渥逃归',9,'晋王遣母弟存渥驰骑追谕之，兄弟俱忿，欲杀存渥，存渥逃归。',[('晋王','遣母弟追谕者'),('存渥','受追谕命、逃归者')],when='922年拥丧归潞途中',place='归潞路',note='未具名全部参与欲杀诸子，不把七子逐个建行凶参与；欲杀未遂与实际逃归分清。')
relationship('晋王','存渥','兄长',9,'晋王遣母弟存渥','母弟明确同母且年幼；李存勖是李存渥的兄长。')
sons=['李继俦','李继韬','李继达','李继忠','李继能','李继袭','李继远']
for name in sons:
 relationship('李嗣昭',name,'父亲',9,'嗣昭七子、继俦、继韬、继达、继忠、继能、继袭、继远。','主书明确七子名，统一补姓；父亲方向嗣昭→子，不据列名先后推全部长幼。')
relationship('李继俦','李继韬','兄长',9,'繼韜兄繼儔，嗣昭長嫡也。','旧史明示继俦为继韬兄、嗣昭长嫡；只建明确这一对长幼。',source='jiuwudaishi-052-jitao-coup')
event('jitao_imprisons_jichou','李继韬囚李继俦，诈令士卒劫己为留后',9,'继韬凶狡，囚继俦于别室，诈令士卒劫己为留后，继韬阳让，以事白晋王。',[('继韬','囚兄并请留后者'),('继俦','被囚、原当袭爵者'),('晋王','受奏者')],when='922年李嗣昭卒后',place='潞州',note='凶狡是史书评价，不写成心理诊断；诈劫非真实被迫。')
claim('event',used[9][-1],'description','《旧五代史》亦记李继俦当袭爵，继韬诈令三军劫己并囚兄。',9,'繼韜詐令三軍劫己為留後，囚繼儔於別室，以事奏聞。','与主书相合，尚在嗣昭死后接任阶段，未提前记923投梁。',source='jiuwudaishi-052-jitao-coup',relation='corroborates')
event('jitao_made_anyijun_successor','晋王改昭义为安义军，以李继韬为留后',9,'晋王以用兵方殷，不得已，改昭义军曰安义，以继韬为留后。',[('晋王','批准者'),('继韬','任安义留后者')],when='922年继韬奏请后',place='昭义军、安义军')
claim('event',used[9][-1],'description','《旧五代史》称李继韬为安义军兵马留后。',9,'莊宗不得已，命為安義軍兵馬留後。','保留具体职称，不提升为已获正式节度使。',source='jiuwudaishi-052-jitao-coup',relation='adds')
claim('person',people['李继俦'],'description','《旧五代史》称李继俦为长子、泽州刺史。',9,'嗣昭有子七人，長曰繼儔，澤州刺史；','旧史此段虽称七人，实际列六名、漏继达；不由缺列否定通鉴七子，母氏范围不从此推满七人。',source='jiuwudaishi-052-sizhao-sons',relation='adds')
event('yan_bao_death','阎宝背疽发作而卒',10,Q[10]['text'],[('阎宝','惭愤背疽后去世者')],when='922年四月甲戌；旧史记己卯',place='晋',note='主书惭愤与疽发连续叙述，未转成现代医学因果；四月承前条，旧史己卯另保留。')
claim('event',used[10][-1],'time_original','《旧五代史》本纪记夏四月己卯阎宝卒。',10,'己卯，天平節度使閻寶卒。','主书甲戌与旧史己卯日次不同，年与月相合；不随意择日。',source='jiuwudaishi-029-922-zhen-siege',relation='conflicts')
claim('person',people['阎宝'],'death_year','阎宝于922年去世。',10,'甲戌卒。','确日异说另存。')
event('liu_yan_visits_meikou','刘岩听术者言，赴梅口镇避灾',11,'汉主岩用术者言，游梅口镇避灾。',[('汉主岩','听术者赴梅口者')],when='通鉴922年本段；确月日未载',place='梅口镇',note='避灾为目的，未把术者预言当已证灾情；不配现代同名地坐标。')
event('wang_yanmei_attacks_liu_yan','王延美率闽兵袭刘岩，刘岩闻侦报遁免',11,'其地近闽之西鄙，闽将王延美将兵袭之，未至数十里，侦者告之，岩遁逃仅免。',[('王延美','率兵袭者'),('岩','闻侦报逃免的刘岩')],when='922年刘岩游梅口期间',place='梅口镇、闽西鄙',note='未至数十里指袭兵距离，非交战伤亡；未记双方正式大战。')
event('li_cunjin_camps_dongyuan','李存进至镇州，夹滹沱水营东垣渡',12,Q[12]['text'],[('李存进','营东垣渡者')],when='922年五月乙酉',place='镇州、东垣渡、滹沱水')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8,13):
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='连续五段校核，李嗣昭传纪月和迎粮主将、残敌人数异说并列；七子方向与继俦长嫡关系有原文；阎宝卒日保留甲戌己卯差异。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=271,year=922,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(8,13)],next_paragraph=Q[13]['id'],supplements=supplements,coverage='卷271第8—12段，原文件76—80行连续覆盖。',reviewed_questions=[
 {'paragraph_id':Q[8]['id'],'note':'王承纲女未婚待嫁，父亲流茂州后女自杀；李嗣昭通鉴四月甲戌，旧史本纪四月、传七月二十四日，遣军主将与余五余三不同；私用字对照旧史箙而不改原文。'},
 {'paragraph_id':Q[9]['id'],'note':'七子父亲关系皆主书有名；旧史列子缺继达不强补母氏范围；继俦为继韬兄有明确补证；晋阳命令未实现，与实际归潞分开；本段不提前记923投梁。'},
 {'paragraph_id':Q[10]['id'],'note':'阎宝主书甲戌、旧史己卯，年与月同而确日待考；惭愤不作现代医学因果。'},
 {'paragraph_id':Q[11]['id'],'note':'避灾术者言是刘岩目的，不建已证灾情；王延美与王延彬不能因近名混合。'},
 {'paragraph_id':Q[12]['id'],'note':'五月乙酉为李存进至镇州营东垣渡日，不外推确切现代渡口坐标。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
