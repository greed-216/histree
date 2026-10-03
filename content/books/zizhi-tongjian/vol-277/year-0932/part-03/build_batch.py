# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 932 paragraphs 16–21."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 24))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'0a9c7504','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
specs += [('tongjian-277-932-april',YEAR/'part-02/sources/library/tongjian-277-932-april','e9aa70e4','司马光等'),('jiuwudaishi-043-932-april',YEAR/'part-02/sources/library/jiuwudaishi-043-932-april','e9aa70e4','薛居正等'),('jiuwudaishi-043-932-qian-report',YEAR/'part-02/sources/library/jiuwudaishi-043-932-qian-report','e9aa70e4','薛居正等'),('jiuwudaishi-043-932-princess-report',YEAR/'part-01/sources/library/jiuwudaishi-043-932-princess-report','585a188b','薛居正等'),('xinwudaishi-064-meng-dong-dissent',YEAR.parent/'year-0931/part-05/sources/library/xinwudaishi-064-meng-dong-dissent','b9e535ed','欧阳修'),('xinwudaishi-068-baohuang',YEAR.parent/'year-0931/part-04/sources/library/xinwudaishi-068-baohuang','077b3114','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-932-april','tongjian-277-932-june']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0932-p016-p021',
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
lines = (ROOT / 'resources/derived/tongjian/277.txt').read_text().splitlines()
for n in range(16, 22):
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
        citation = f'卷277·长兴三年（932）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0932_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','廷隐':'赵廷隐','季良':'赵季良','知祥':'孟知祥','璋':'董璋','肇':'李肇','昊':'李昊','仁罕':'李仁罕','晖':'王晖','光嗣':'董光嗣','延浩':'董延浩','李瑭':'李瑭（西川）','廷钧':'王延钧','延钧':'王延钧','守元':'陈守元','延光':'范延光','思同':'王思同','存瑰':'李存瑰','克宁':'李克宁'}
NEW_ALIASES={'张公铎':['張公鐸','张公鐸'],'张守进':['張守進'],'李瑭（西川）':[],'元璝':[],'董光演':[],'董光嗣':[],'董延浩':[],'潘稠':[],'迭罗卿':['迭羅卿'],'荝骨舍利':['則骨舍利','则骨舍利'],'李存瑰':['李瓌','李瑰']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=932, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='932年五月本段；确日未独载' if n<=20 else '932年本段；月日未独载'
    key = 'event_zztj_277_0932_' + code
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
        edge = 'participation_zztj_277_0932_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0932_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive six body paragraphs and two verified empty-line records.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
old='jiuwudaishi-043-932-april';june='jiuwudaishi-043-932-june';dong='jiuwudaishi-062-dong-death';report='jiuwudaishi-043-932-princess-report';peace='xinwudaishi-064-meng-peace';meng='xinwudaishi-064-meng-dong-dissent';minbook='xinwudaishi-068-baohuang';qianreport='jiuwudaishi-043-932-qian-report'
ev('tingyin_bids_departure','五月壬午朔赵廷隐入辞孟知祥',16,'五月，壬午朔，','廷隐入辞。',[('廷隐','出军前入辞者'),('知祥','受辞的主帅')],when='932年五月壬午朔',place='成都')
ev('dong_sends_divisive_letters','董璋檄书及给赵季良、赵廷隐、李肇的书信到达，诬称赵等邀其来攻',16,'董璋檄书至，','召己令来。',[('璋','发送檄书及信者'),('季良','被诬与董通谋者'),('廷隐','被诬与董通谋者'),('肇','收到董信者')],place='东川至西川',note='通谋为董书诬称，原文明诬，不造赵董实际联盟；主诬句列季良廷隐，不扩大李肇也被明确诬通谋。')
ev('tingyin_rejects_letter','孟知祥交信给赵廷隐；廷隐弃信，认为董欲用反间使孟杀赵等',16,'知祥以书授廷隐，','知祥曰：“事必济矣。”',[('知祥','交信并判断可成者'),('廷隐','弃信称其为反间并出军者')],place='成都',note='欲杀为廷隐解释敌方计策，不造孟已要杀部属事件；知祥事济是期望判断。')
ev('lizhao_detains_dong_envoy','李肇看董信后囚其使者，并拥众自保',16,'肇素不知书，','自全计。',[('肇','囚使且拥众自保者'),('璋','被囚使所属主帅')],place='西川李肇所部，具体镇未独载',note='不知书为史述，不推其现代教育程度；自全不是已叛孟。')
E=ev('dong_takes_hanzhou_pan_captured','董璋至汉州，在赤水击败潘仁嗣并俘之，遂克汉州',16,'璋兵至汉州，','璋遂克汉州。',[('璋','战胜俘将及克汉州者'),('潘仁嗣','赤水败被俘者')],place='汉州、赤水',note='本段具体战日未独载，排癸未孟出军之前，未套四月潘侦日期。')
claim('event',E,'description','新孟世家同记董先袭破汉州。',16,'而璋先襲破知祥漢州，','新传概叙不独载赤水潘被俘，不混同源支持范围。',source=meng,relation='corroborates')
ev('meng_leaves_chengdu_eight_thousand','癸未孟知祥留赵季良、高敬柔守成都，亲率八千赴汉州至弥牟镇，廷隐陈镇北',16,'癸未，','赵廷隐陈于镇北。',[('知祥','留守安排并亲率八千者'),('季良','留守成都者'),('高敬柔','留守成都者'),('廷隐','在弥牟镇北布阵者')],when='932年五月癸未',place='成都至汉州弥牟镇',note='八千为孟亲率，不凭此前廷隐三万把总军数算为38000；镇北与后桥阵分。')
ev('tingyin_zhang_bridge_positions','甲申迟明赵廷隐陈鸡踪桥，张公铎陈其后',16,'甲申，迟明，','张公鐸陈于其后。',[('廷隐','鸡踪桥布阵者'),('张公铎','义胜定元都知兵马使、后阵者')],when='932年五月甲申迟明',place='鸡踪桥',note='鐸展示铎；主鸡踪桥、新鷄距桥、旧夹注鸡纵留各字，不猜现代桥坐标；新未给张职，定元底本保留未静改定远。')
ev('dong_retreats_wuhou_position','董璋见西川兵盛退阵武侯庙下，骁卒催战，董乃上马',16,'俄而璋望西川兵盛，','璋乃上马。',[('璋','退阵且应部下催战上马者')],when='932年五月甲申，迟明布阵后；具体时刻未独载',place='武侯庙下',note='日中为部下催战引语，不用日中反算前后精确时分。')
ev('zhang_shoujin_surrenders','前锋交战时张守进投降孟知祥，并称董兵无后继应急击',16,'前锋始交，','当急击之。”',[('张守进','东川右厢马步都指挥使、降孟并报军情者'),('知祥','受降及报者'),('璋','被部将离弃者')],when='932年五月甲申交战开始',place='鸡踪桥一带',note='董兵无后继为降将所报，不据此静改全部东川兵籍。')
ev('meng_supervises_bridge_mao_li_killed','孟知祥登高冢督战，守鸡踪桥的毛重威、李瑭被东川兵杀',16,'知祥登高冢督战，','皆为东川兵所杀。',[('知祥','高冢督战者'),('毛重威','左明义指挥使、守桥战死者'),('李瑭','左冲山指挥使、守桥战死者')],when='932年五月甲申交战中',place='鸡踪桥',note='李瑭为932西川左冲山指挥使，与901已斩汾州刺史同名异人，建限定主体李瑭（西川）；未改旧档案。毛由先赴蜀屯同职军系列识，非凭姓造复活。')
ev('tingyin_hou_setbacks','赵廷隐三战不利、侯弘实军亦退；孟知祥以马棰指向后阵',16,'赵廷隐三战不利，','以马棰指后陈。',[('廷隐','三战不利者'),('侯弘实','牙内都指挥副使、兵退者'),('知祥','惧而指示后阵者')],when='932年五月甲申交战中',place='鸡踪桥一带',note='未据不利称三场全军覆没；指棰是动作，未擅解释具体口头军令。')
E=ev('zhang_gongduo_victory_captives','张公铎率众呼进，东川兵败死数千，元璝、董光演等八十余人被俘',16,'张公鐸帅众大呼而进，','董光演等八十馀人。',[('张公铎','后阵呼进者'),('知祥','西川主帅'),('元璝','东川中都指挥使、被俘者'),('董光演','牙内副指挥使、被俘者'),('璋','军败主帅')],when='932年五月甲申',place='鸡踪桥一带',note='数千战死和八十余俘将不互换统计；董光演不并已洛阳被杀光业或此后自杀光嗣。元璝与后元瑰可能异体或异人暂待核，后事件不另建元瑰人物以免制造重复。')
claim('event',E,'description','旧明宗纪九月记录孟知祥奏五月三日于汉州大破董璋。',16,'又奏五月三日，大破東川董璋之眾於漢州，收下東川。','九月是奏闻时间，战役仍五月；主五月壬午朔、甲申为第三日，与旧五月三日叙法相合，不自行换算公历。收下东川为该段战果合述非本日同时已入梓。',source=report,relation='corroborates')
claim('event',E,'description','旧董传正文记孟知祥诸将拒战汉州弥牟镇，董军败返东川。',16,'知祥與諸將率師拒之，戰於漢州之彌牟鎮。璋軍大敗，得數十騎，復奔於東川。','正文只记弥牟镇；同段夹注九国志鸡纵桥战法暂不新增为基础出处，不能把其佯遁计伪装旧正文。四月率袭与五月交战分别，非把败日改四月。',source=dong,relation='adds')
ev('dong_flees_seven_thousand_surrender','董璋数骑遁去，余众七千降，潘仁嗣获释归西川',16,'璋拊膺曰：','复得潘仁嗣。',[('璋','拊膺后数骑逃者'),('潘仁嗣','西川复得的先被俘将'),('知祥','受降及复得潘的主帅')],when='932年五月甲申败后',place='汉州一带',note='亲兵皆尽是董叹语，不作所有部曲战死事实；余众七千投降不是死数。复得潘不等潘刚从另一场被俘。')
ev('meng_pursues_wuhou_yuan_surrenders','孟知祥追董至五侯津，史称东川马步都指挥使元瑰降',16,'知祥引兵追璋至','元瑰降。',[('知祥','追击并受降者')],when='932年五月甲申败后',place='五侯津',note='保留底本元瑰；与前被俘元璝字形及衔有差，同人未定不另建第二个元姓人物，也不回写前被俘者已经脱逃或再次投降。')
ev('soldiers_loot_dong_escapes','西川兵入汉州府第寻董不得，史书以争军资解释董得免',16,'西川兵入汉州府第，','故璋走得免。',[('璋','因军争资而得逃的主帅')],when='932年五月甲申败后',place='汉州府第',note='因果归史书叙述，不造士兵故意放走董的阴谋。')
ev('tingyin_accepts_three_thousand','赵廷隐追至赤水，又受降东川卒三千',16,'赵廷隐追至赤水，','又降其卒三千人。',[('廷隐','赤水追击受降者')],when='932年五月甲申败后',place='赤水',note='又三千为史载另次受降，不自动与余众七千/各批俘将合计去重出总兵力。')
ev('meng_stays_luo_lihao_drafts','孟知祥当夕宿雒县，命李昊草榜谕东川吏民，并写信慰问董及说明拟赴梓问责',16,'是夕，知祥宿雒县，','请见伐之罪。',[('知祥','宿雒及命草文书者'),('昊','奉命草榜及书者'),('璋','慰问及问责信对象')],when='932年五月甲申夕',place='雒县',note='将如梓州为后续打算，此夕不是已赴梓；请见伐之罪为反讽问责书法，不写孟正式认罪。')
ev('meng_meets_tingyin_orders_zi_attack','乙酉孟知祥会廷隐于赤水后西还，命廷隐攻梓州',16,'乙酉，','命廷隐将兵攻梓州。',[('知祥','会师西还及下令者'),('廷隐','受命攻梓者')],when='932年五月乙酉',place='赤水至西川；拟攻梓州',note='攻命与后入梓封库分别，不硬令已攻陷同一时刻。')
ev('dong_returns_zi_questioned','董璋逃至梓州肩舆入城，王晖问全军何以还不足十人，董泣不能对',16,'璋至梓州，','璋涕泣不能对。',[('璋','败返哭泣者'),('晖','前陵州刺史、问败状者')],when='932年五月败后，乙酉前后叙；到城确日未独载',place='梓州',note='不足十为王问返随人，不与新数骑/旧数十骑/荆南报告二十余强归同计数。')
ev('wang_dong_yanhao_mutiny','董璋方食时，王晖与董从子董延浩率三百兵入府',16,'至府第，方食，','帅兵三百大嗓而入。',[('晖','率兵入董府者'),('延浩','董从子、牙内都虞侯、同率入府者'),('璋','府中遭变者')],when='932年五月董败返后；确日未独载',place='梓州府第',note='董从子只录从子，未推父名；三百为王董合率，不每人三百。大嗓为底本字不静改噪，展示仅称率入。')
ev('dong_family_flees_guangsi_suicide','董璋携妻子登城，子董光嗣自杀',16,'璋引妻子登城，','子光嗣自杀。',[('璋','携家属登城者'),('光嗣','董之子、自杀者')],when='932年五月梓州变时；确日未独载',place='梓州城',note='妻子按家属合称、不造未名妻；光嗣不并光业或光演，原仅自杀未独方法。')
claim('event',used[16][-1],'description','新孟世家记董败走时劝子光嗣降以保家，光嗣拒并同走，董梓州见杀后光嗣自缢。',16,'璋走至梓州見殺，光嗣自縊死，','新先董死再光嗣自缢、主光嗣先自杀后董被斩顺序差并列；方法自缢仅新补，不伪装主载。',source=meng,relation='conflicts')
E=ev('pan_chou_kills_dong','董璋召潘稠讨乱兵，潘稠率十卒登城斩董，并取董光嗣首给王晖',16,'璋至北门楼，','以授王晖，',[('璋','求平乱而被杀者'),('潘稠','指挥使、率十卒斩董者'),('光嗣','此前自杀后被取首者'),('晖','受二首者')],when='932年五月梓州变时；确日未独载',place='梓州北门楼',note='授王晖为交首，不写潘又杀已自杀光嗣；十卒是潘带兵，不把指挥使额算进兵数。')
claim('event',E,'description','旧董传正文合述王晖乘董败率众害之，并传首西川。',16,'至是因璋之敗，率眾以害之，傳其首於西川。','旧将集体主导归王晖、主具体执行潘稠分层留；不能凭概叙写王亲手持刀。旧夹注九国志未入本批事实。',source=dong,relation='adds')
claim('event',E,'time_original','旧明宗纪六月戊午记录荆南奏董败走东川，寻为王晖所杀。',16,'戊午，荊南奏：「東川董璋領兵至漢州，西川孟知祥出兵逆戰，璋大敗，得部下人二十餘，走入東川城，尋為前陵州刺史王暉所殺，孟知祥已入梓州。」','戊午奏报不等杀董日，不将主五月变乱移到六月；二十余、主数骑及入城不足十、新旧数骑各阶段书法差保留。',source=june,relation='adds')
relationship('延浩','璋','从子',16,'晖与璋从子牙内都虞侯延浩','董延浩→董璋从子；不推亲侄排行、父母或等同光嗣。')
relationship('璋','光嗣','父亲',16,'璋引妻子登城，子光嗣自杀。','董璋→董光嗣父亲，姓名与近邻子句对应；已死光业与被俘光演分，不反向重复建儿子边。')
ev('wang_surrenders_zi_tingyin_seals','王晖举梓州迎降，赵廷隐入城封府库待孟知祥',16,'晖举城迎降。','封府库以待知祥。',[('晖','举城降者'),('廷隐','入城封库者'),('知祥','待入城的主帅')],when='932年五月董死后；确日未独载',place='梓州')
ev('lizhao_kills_dong_envoy','李肇闻董败，才斩其先前所囚使者并报告',16,'李肇闻璋败，','始斩其使以闻。',[('肇','闻败后斩使上报者'),('璋','被斩使所奉主帅')],when='932年五月董败后；确日未独载',place='西川李肇所部',note='先囚后杀两阶段明确，不能写李接信即斩；使未名不造人。')
ev('meng_returns_chengdu','丙戌孟知祥入成都',16,'丙戌，','知祥入成都，',[('知祥','入成都者')],when='932年五月丙戌',place='成都')
ev('meng_starts_zi_again','丁亥孟知祥再率八千赴梓州，至新都，廷隐献董首',16,'丁亥，','赵廷隐献董璋首。',[('知祥','复率八千赴梓者'),('廷隐','献首者'),('璋','被献首的已死主帅')],when='932年五月丁亥出发；至新都献首确日未独载',place='成都至新都',note='献首非再次斩董，八千为此次亲率不加前亲率军。')
ev('meng_departs_xuanwu_greeted','己丑孟知祥发玄武，赵廷隐率东川将吏迎接',16,'己丑，',None,[('知祥','发玄武者'),('廷隐','率东川将吏迎者')],when='932年五月己丑',place='玄武至梓州途',note='发玄武不等本句已入梓；入梓主后丁酉明载。')
# May continuation; the library paragraph name is archival and is not a chronology header.
ev('kang_reports_dangxiang_submission','康福奏称党项钞盗者已伏诛，其余均降附',17,'康福奏',None,[('康福','奏报讨党项后续者')],place='党项活动地，奏后唐',note='为康奏报，不把皆字当逐人核验；主未独日，不套前己丑。')
ev('meng_ill_wang_reassures','壬辰孟知祥有疾，癸巳加重，王处回侍侧并以空食器示众安众心',18,'壬辰，','以安众心。',[('知祥','病重者'),('王处回','中门副使、侍侧安众者')],when='932年五月壬辰始疾、癸巳疾甚',place='赴梓途中，确处未独载',note='空器只是安众办法，未据此认孟实际吃尽每餐或王伪造病愈；不推具体病名。')
ev('renhan_insults_tingyin','李仁罕从遂州来，廷隐板桥相迎；仁罕不称功反侵侮，廷隐怒',18,'李仁罕自遂州来，','廷隐大怒。',[('仁罕','遂州来并侵侮廷隐者'),('廷隐','板桥迎并因侮怒者')],place='板桥',note='此次争功分歧不造终身仇敌或已武斗关系。')
ev('meng_recovers_enters_zi','乙未孟知祥病愈，丁酉进入梓州',18,'乙未，','入梓州。',[('知祥','病愈后入梓者')],when='932年五月乙未病愈，丁酉入梓州',place='梓州',note='两个明确日期同事件分phase文字不换公历，不把前沿途迎等同入梓。')
ev('meng_rewards_asks_zi_governor','戊戌犒赏后孟问李仁罕、赵廷隐谁应镇东川；仁罕回应、廷隐不答',18,'戊戌，','廷隐不对。',[('知祥','犒军并问镇主者'),('仁罕','以再与蜀州亦行回答者'),('廷隐','未答者')],when='932年五月戊戌',place='梓州',note='仁罕答语原留不擅替换为已接受东川任；廷不答不是其已正式辞任。')
ev('meng_orders_lihao_pending_document','孟知祥令李昊草牒，拟等二将推让后任一人为留后',18,'知祥愕然，','命一人为留后，',[('知祥','命草待定任命者'),('昊','奉命拟草牒者'),('仁罕','未定推让的候任将'),('廷隐','未定推让的候任将')],place='梓州',note='俟推则命为待定条件，不造两个留后均已任职。')
ev('lihao_proposes_meng_dual_command','李昊以二将不让为由，劝孟自领东川并速回与赵季良商议',18,'昊曰：',None,[('昊','劝孟自领者'),('知祥','受劝者'),('季良','拟回商议对象')],place='梓州',note='梁祖庄宗兼四镇为李引例不在932新建旧帝任四镇；赵仆射按同僚赵季良识，当前仍建议未获允。')
E=ev('dieluoqing_returns_with_captive','己亥迭罗卿辞归；李嗣源以安边为由遣荝骨舍利随使归国',19,'己亥，','与之俱归。',[('迭罗卿','契丹使者、辞归者'),('上','放归部分俘者'),('荝骨舍利','本次获归的被留者')],when='932年五月己亥',place='后唐至契丹',note='荝骨舍利与前荝剌求归不同称名，不因舍利相同并作同一人；主未具体何时何战被俘不造其俘获。')
claim('event',E,'description','旧明宗纪在四月俘将争议后记只遣则骨舍利随来使归蕃。',19,'既而隻遣則骨舍利隨來使歸蕃，不欲全拒其請也。','同部分放归背景主荝骨旧则骨异字、舍利限定称名合核；旧四月段既而无独日与主五月己亥叙法分，不改主为四月。',source=old,relation='corroborates')
ev('khitan_raids_after_shala_retained','史书称契丹因荝剌未获返，此后数寇云州及振武',19,'契丹以不得荝剌，',None,[('荝剌','未获遣返的俘将')],year=None,when='五月己亥放荝骨舍利后，此后数次；各次年份未独载',place='云州、振武',note='归因与数次为史书合述，不能拆猜几次战役或都当932五月。')
ev('meng_assigns_renhan_tingyin_lihao','孟令李仁罕回遂州，留廷隐东川巡检，拟李昊行梓州军府事',20,'孟知祥命李仁罕','行梓州军府事。',[('知祥','分派者'),('仁罕','受命回遂州者'),('廷隐','留东川巡检者'),('昊','拟行军府事者')],place='梓州至遂州',note='李昊随即拒绝，拟任不能等已实际接任；仁罕回命具体到州时间未知。')
ev('lihao_declines_wang_monitor','李昊以二将相争拒行军府事，愿随孟还；孟改任王彦铢为东川监押',20,'昊曰：“二虎方争，','为东川监押。',[('昊','拒拟命者'),('知祥','改任监押者'),('王彦铢','都押牙、受任东川监押者')],place='梓州',note='二虎是李比喻二将，不造真实虎类主体；监押不等东川节度使。')
ev('meng_returns_tingyin_later_returns','癸卯孟知祥至成都，赵廷隐不久也引兵西还',20,'癸卯，','引兵西还。',[('知祥','归成都者'),('廷隐','寻后引兵西归者')],when='932年五月癸卯孟至成都；廷隐西还确日未独载',place='梓州至成都',note='寻未必与癸卯同日，分保相对时序。')
ev('meng_reports_seven_renhan_letters','孟对李昊说得东川患更深，述李仁罕七状请自领及廷隐因仁罕不让而起争心',20,'知祥谓李昊曰：','遂有争心耳。’',[('知祥','向李说明将领矛盾者'),('昊','询问并受述者'),('仁罕','被孟引七状者'),('廷隐','被孟引说明争心者')],place='成都',note='七状为孟报告数量，不造七个未知递送日期；仁罕称诸将不服为书中声称，不当所有将领确已反。')
ev('meng_plans_baoning_for_tingyin','孟令李昊说服廷隐赴保宁，拟复阆州军并增果蓬渠开四州，自己领东川',20,'君为我晓廷隐，','以绝仁罕之望。”',[('知祥','提出军镇安排者'),('昊','受命说服者'),('廷隐','拟往镇保宁者'),('仁罕','孟称欲绝其东川之望的将领')],place='成都；拟保宁阆、果、蓬、渠、开五州',note='此为拟安排，正式留后六月另录；四新增州加阆为五州，未画成确定现代疆界。')
ev('tingyin_requests_duel_lihao_dissuades','廷隐请求与仁罕决斗以定东川，李昊深加劝解后廷隐受命',20,'廷隐犹不平，','乃受命。',[('廷隐','请求斗而最终受命者'),('仁罕','拟决斗对象'),('昊','劝解者')],place='西川',note='请斗不等决斗已举行，胜者东川为条件不造胜负。')
E=ev('tingyin_baoning_liuhou','六月赵廷隐任保宁留后',20,'六月，','以廷隐为保宁留后。',[('廷隐','受保宁留后任者'),('知祥','西川主帅、任命者')],when='932年六月；确日未独载',place='保宁军',note='地方留后任命不等已获后唐朝廷正授节度使；不得提前九月请正节钺。')
claim('event',E,'description','新孟世家记知祥兼据两川，以赵廷隐为保宁军留后。',20,'趙廷隱保寧軍留後','同官补，所列其他四镇留后由后主连续段再录，不把整份新传任官名单提前整包新增。',source=peace,relation='corroborates')
ev('jiliang_requests_dual_command','六月戊午赵季良率将吏请求孟兼镇东川，孟允',20,'戊午，','许之。',[('季良','率将吏请兼镇者'),('知祥','允自兼东川者')],when='932年六月戊午',place='成都、东川',note='许之是孟自允辖区主帅之请，不等同朝廷正式授节钺。')
ev('meng_rejects_kingship_edicts','赵季良等又请孟称王、权行制书赏功臣，孟不许',20,'季良等又请','不许。',[('季良','请称王制书者'),('知祥','拒绝者')],when='932年六月戊午本段，兼镇请后；确日未独载',place='西川',note='拒这次请求不等此后永不称王；新议未决与主不许不同概叙保留，不提前934称帝。')
claim('event',used[20][-1],'description','新孟世家记季良等请称王、行墨制，议未决而李瓌到蜀。',20,'季良等因請知祥稱王，以墨制行事，議未決而瓌至蜀。','主当前不许，新概叙议未决时使至，时段覆盖或书法异说未硬等同一次条件；不写孟已经称王。',source=peace,relation='adds')
ev('wang_sitong_reports_dong_attack','董起兵攻孟时，山南西道节度使王思同奏闻朝廷',20,'董璋之起兵攻知祥也，','王思同以闻，',[('璋','起兵攻孟者'),('知祥','受攻者'),('思同','山南西道节度使、奏报者')],when='追述932年四月至五月两川交战期间；确日未载',place='山南西道至后唐朝廷',note='当前六月段追述四五月已主独载，不把起兵复建六月新战。')
ev('fan_proposes_attack_during_rivalry','范延光以两川合一将难取为由，建议趁孟董相争早图',20,'范延光言于上曰：','早图之。”',[('延光','建议趁两川交争进取者'),('上','听建议者'),('知祥','被视为未来兼两川的攻取对象'),('璋','交争另一方')],when='932年董孟交战期间追述；确日未载',place='后唐朝廷',note='一贼为范政治书法，恐难取是未来判断，不当朝廷已失败新役。')
ev('emperor_orders_sitong_plan','李嗣源命王思同以兴元兵秘密筹划进取两川',20,'上命思同','密规进取。',[('上','密令者'),('思同','受命用兴元兵筹划者')],when='932年董孟交战期间追述；确日未载',place='兴元，拟两川',note='密规是筹划指令，不能写兵已攻入两川。')
E=ev('fan_proposes_meng_reconciliation','董败死闻后，范延光分析孟欲借朝廷威众，建议屈意招抚；帝以故人回应',20,'未几，闻璋败死，','何屈意之有！”',[('延光','建议招抚且解释军心者'),('上','同意抚故人者'),('知祥','拟招抚对象')],when='932年董败死后；旧六月辛酉载此议',place='后唐朝廷',note='孟恐思归及欲倚朝廷是范分析，不造部众已经谋反；离间为帝解释历史关系。')
claim('event',E,'description','旧明宗纪六月辛酉同载范建议屈意招携，帝称故人因间谍阻隔而应抚。',20,'辛酉，範延光奏曰：「孟知祥兼有兩川，彼之軍眾皆我之將士，料其外假朝廷形勢以製之，然陛下苟不能屈意招攜，彼亦無由革麵。」帝曰：「知祥予故人也，以賊臣間諜，故茲阻隔，今因而撫之，何屈意之有！」','完整范奏与帝答支持补证；范分析为其判断，不当已发生军变。',source=june,relation='corroborates')
claim('event',E,'description','新孟世家同载范分析需朝廷之势，明宗答故人因间谍而危疑。',20,'知祥，吾故人也，本因間諜致此危疑，撫吾故人，何屈意之有？','新引帝发言，陈因是帝立场；不确证只有安重诲一人造成一切分歧。',source=peace,relation='corroborates')
E=ev('li_cungui_envoy_meng','李嗣源遣供奉官李存瑰赐孟诏，申明其在京亲属安全并要求守君臣之节',20,'乃遣供奉官李存瑰','守君臣之大节。”',[('上','遣使赐诏者'),('存瑰','供奉官、赴西川赐诏者'),('知祥','受诏招抚对象')],when='932年六月本段；旧同议辛酉后遣；使到蜀确日未独载',place='后唐朝廷至西川',note='诏自贻族灭等为朝廷评价，不推董所有远亲已死；使遣不等即时到成都。李存瑰与新瓌旧瑰按同亲缘同职同使识。')
claim('event',E,'description','旧明宗纪记遣供奉官李瑰使西川赐诏。',20,'由是遣供奉官李瑰使西川，齎詔以賜知祥。','旧李瑰、新李瓌与主李存瑰同招抚任务及孟甥母在蜀关系；不凭瑰字与东川元瑰合并。',source=june,relation='corroborates')
claim('event',E,'description','新孟世家记使李瓌归省母，因赐知祥诏招慰。',20,'明宗即遣瓌歸省其母，因賜知祥詔書招慰之。','新补省亲目的，未把后到蜀倨慢或九月返表提前作为已完成动作。',source=peace,relation='adds')
relationship('克宁','存瑰','父亲',20,'存瑰，克宁之子，知祥之甥也。','李克宁→李存瑰父亲；只是过去父子身份补，父已故不生成932复生参与。')
relationship('存瑰','知祥','外甥',20,'存瑰，克宁之子，知祥之甥也。','李存瑰→孟知祥甥，补新克宁妻孟氏是孟知祥妹，明确母系外甥，未因甥字猜未名母亲名字。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新孟世家记李克宁妻孟氏为孟知祥妹，其子李瓌留事唐为供奉官。',20,'先是，克寧妻孟氏，知祥妹也。莊宗已殺克寧，孟氏歸于知祥，其子瓌，留事唐為供奉官。','新明母系关系核外甥；孟氏只姓不另造她名，克宁遇杀为追叙不当932新杀。',source=peace,relation='adds')
ev('yanjun_asks_future_baohuang','闽王王延钧令陈守元问所谓宝皇，六十年天子后将如何',21,'闽王廷钧谓陈守元曰：','后当何如？”',[('延钧','要求卜问者'),('守元','受托问宝皇的道士')],when='932年本段；确月日未独载',place='闽',note='廷钧与后同段延钧、既有王延钧同主，疑字不静改TXT；宝皇为所称神灵不造历史真人，六十年为宗教预言不是实际在位长度。')
E=ev('shouyuan_reports_immortal_prediction','次日陈守元称得宝皇旨，王将为大罗仙主；徐彦等附和',21,'明日，守元入曰：','其言与守元同。”',[('守元','传称神旨者'),('徐彦','附和称崇顺王见宝皇者'),('延钧','听取预言者')],when='上述卜问次日；确月日未载',place='闽',note='其言归道士及巫者，非确认神灵真实授旨；崇顺王为北庙神号不凭此造在世君主。')
claim('event',E,'description','新闽世家亦记陈守元转述六十年后为大罗仙人。',21,'守元傳寶皇語曰：「六十年後，當為大羅仙人。」','主仙主、新仙人字面差保留，皆传称；新紧接称帝的概述不提前933登基。',source=minbook,relation='corroborates')
ev('yanjun_plans_emperorship','王延钧更自负，开始谋称帝',21,'延钧益自负，','始谋称帝。',[('延钧','开始谋帝号者')],when='932年本段，听预言后；确月日未独载',place='闽',note='谋不是已即帝位、改龙启或更名璘，未来连续段再录。')
E=ev('yanjun_requests_qian_ma_offices','王延钧因钱镠、马殷已卒，上表请授吴越王及尚书令，朝廷不报',21,'表朝廷云：','朝廷不报，',[('延钧','上表索吴越王及尚书令者')],when='932年本段；旧明纪七月乙未记上表',place='闽至后唐',note='请封而不报，不写已经取得吴越疆域或接管楚；不把钱、马死亡再建一次。')
claim('event',E,'time_original','旧明宗纪七月乙未记福建节度使王延钧进绢表求吴越王、尚书令而未报。',21,'乙未，福建節度使王延鈞進絹表云：「吳越王錢鏐薨，乞封臣為吳越王。湖南馬殷官是尚書令，殷薨，請授臣尚書令。」不報。','主在六月段后未独月日，旧七月乙未具体记表；不硬把主所有宗教问答也移到此日。',source=qianreport,relation='adds')
ev('min_stops_tribute','史书称朝廷不答王延钧请封之后，闽对后唐职贡遂绝',21,'自是职贡遂绝。',None,[('延钧','职贡中止时的闽王')],year=None,when='不报请封后，持续状态起止未独确年',place='闽与后唐',note='自是为相对趋势，无每次贡期证据，不录某日永绝所有外交来往。')
reviews={16:'五月壬午辞、董檄诬反间、李囚使自保；潘赤水败俘及汉州失、癸未孟八千出军、甲申桥阵交战、张守进降报、毛及西川李瑭战死、廷侯不利与张进取胜、数千死八十余俘、七千降潘复、五侯元瑰降、士争资董逃、赤水再三千降、夕雒草榜、乙酉会及攻命、梓州王董延浩变、董光嗣自杀与董被潘斩、迎降封库、李后斩使、丙戌归丁亥再出献首己丑发玄武逐动作分。西川李瑭与901死汾州同名异人，限定主体。张鐸展示铎，主定元军衔保留。鸡踪/新鸡距及旧弥牟位置叙法并列，旧夹注九国志不新增。元璝被俘与元瑰降疑异体或异人待核，后不建重复元人。董光演、光嗣、先死光业分。兵数不擅合去重，主董子先死与新后自缢次序留。旧六月及九月是奏闻，五月战死不移月；潘执行与王主导集体书法分。',17:'康报伏诛及其余降为奏述，不当逐人确定事实，日期承五月未独日，前己丑不强套。',18:'五月壬辰病癸巳加重、王空食器安众、李来廷迎争功、乙未愈丁酉入梓、戊戌犒问镇主、拟草牒、李劝孟自领分。不给疾病诊断，空器不证孟实进食；争功不建终身仇边，待定留后未实际任，蜀州答语不硬等于允东川。',19:'五月己亥迭罗卿辞及荝骨舍利放归；旧四月段既而则骨与主有同案异字叙差，未把荝剌当获归。其后数寇主合述yearnull，归因属史叙，不猜次数与每战日。',20:'五月留巡检与拟李军府、李拒王监押、癸卯孟归与廷后还、七状及争心报告、拟保宁及孟自领、求斗李劝、六月保宁留后、戊午允兼镇与拒王制分。复阆加四州为五州，不建未举行决斗。追叙交战期间王报范密谋只筹划未攻；董死后转招抚论据归范。主存瑰新瓌旧瑰同孟甥供奉同使，父已亡只父亲关系补，母系新孟妹明证外甥。新传其他四镇任及九月表待后连续段，不提前。',21:'闽廷钧与延钧同人疑字保留；宝皇及北庙崇顺王为宗教神号不造在世人物。六十年及仙主仙人为转述不记真实在位。谋帝不等已帝，旧七月乙未上表补不把卜问同日；不报不等允封，占位吴越楚不成立。自是贡绝持续各期未确yearnull。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(16,22):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
excluded=[]
for n in [22,23]:
 assert not Q[n]['text'].strip() and not Q[n]['event_keys']
 reason='原TXT卷尾空行，无历史正文；保留既有ID、原字和行号，不生成事实。'
 ledger[n-1].update(kind='separator',status='excluded_non_body_verified',event_keys=[],review=reason)
 excluded.append(dict(paragraph_id=Q[n]['id'],source_line=Q[n]['source_line'],text=Q[n]['text'],reason=reason))
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=932,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(16,22)],next_paragraph='zztj-v278-y0932-p001',next_volume=278,next_year=932,supplements=supplements,source_contexts=[],excluded_non_body=excluded,coverage='卷277连续932年第16—21正文段、原130—135行；136—137两空行已核结构排除，保留ID。董败死汉州战、康党项奏、孟病及东川争任、部分遣俘、孟兼两川与唐招抚、闽预言谋帝请封。下一卷278同年首段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(16,22)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
