# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 930, paragraphs 10–19."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 56))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 key=directory.name;author='司马光等' if key.startswith('tongjian') else '薛居正等' if key.startswith('jiuwudaishi') else '欧阳修'
 specs.append((key,directory,'d5eb21c8',author))
for key in ['tongjian-277-930-spring','jiuwudaishi-041-930-march','xinwudaishi-006-930']:
 specs.append((key,YEAR/'part-01/sources/library'/key,'238471e3','司马光等' if key.startswith('tongjian') else '薛居正等' if key.startswith('jiuwudaishi') else '欧阳修'))

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-spring','tongjian-277-930-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0930-p010-p019',
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
for n in range(10, 20):
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
        citation = f'卷277·长兴元年（930）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0930_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','曹妃':'曹氏（李嗣源后）','王妃':'王德妃（李嗣源妃）','刘后':'刘夫人（李存勖妻）','重诲':'安重诲','从珂':'李从珂','从荣':'李从荣','从厚':'李从厚','璋':'董璋','知祥':'孟知祥','琦':'吕琦'}
NEW_ALIASES={'曹氏（李嗣源后）':['曹淑妃','曹皇后（李嗣源后）','和武宪皇后'],'杨彦温':['楊彥溫'],'索自通':[],'药彦稠':['藥彥稠']}

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

def event(code, title, n, quote, actors, when=None, note='', year=930, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='930年'+('三月' if n<=11 else '五月' if n==19 else '四月')+'本段；确日未载'
    key = 'event_zztj_277_0930_' + code
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
        edge = 'participation_zztj_277_0930_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0930_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive nine paragraphs, chronological facts and independently located supplements.
mar='jiuwudaishi-041-930-march';apr='jiuwudaishi-041-930-april';river='jiuwudaishi-041-930-hezhong';tit='jiuwudaishi-041-930-imperial-title';may='jiuwudaishi-041-930-may';dong='jiuwudaishi-062-dongzhang-imprisons-wu';wang='xinwudaishi-015-wang-introduction';court='xinwudaishi-015-cao-wang-court';an='xinwudaishi-024-an-chonghui-hezhong';meng='xinwudaishi-064-meng-office';lv='xinwudaishi-056-lvqi-office';fu='xinwudaishi-026-fuxi-retirement';cao='jiuwudaishi-049-cao-empress';ann='xinwudaishi-006-930'
E=ev('cao_offers_queen_position_wang_declines','曹淑妃以病烦辞后位，王德妃以中宫匹帝辞让',10,'帝将立','谁敢干之！”',[('曹妃','被拟立后、向王德妃辞让者'),('王妃','拒绝代立者'),('帝','拟立曹妃者')],when='930年三月庚寅立后之前',note='辞让为谈话，不是王氏已当皇后；妹为宫中称呼，未证亲生姐妹。中烦保留为本人病烦陈述，不推医学病名。')
claim('event',E,'description','新王妃传亦记曹氏以多病辞让、王氏以皇后为帝匹辞谢。',10,'曹氏謂王氏曰：「我素多病，而性不耐煩，妹當代我。」王氏曰：「后，帝匹也，至尊之位，誰敢干之！」','新传从明宗即位起概叙，未独具此次庚寅；用于对话印证，不拿段首即位赋此事926。',source=court,relation='corroborates')
E=ev('cao_established_empress','李嗣源立曹淑妃为皇后',10,'庚寅，','立淑妃为皇后。',[('帝','立后者'),('曹妃','被立皇后者')],when='930年三月庚寅',note='主立后与后续择日册命分；不与李存勖之母曹氏混。')
claim('event',E,'description','旧明宗纪同庚寅制曹氏为皇后，令择日册命。',10,'庚寅，製淑妃曹氏可立為皇后，仍令擇日冊命。','三月制立非同日已完成后续册礼。',source=mar,relation='corroborates')
claim('event',E,'time_original','新明宗纪三月庚寅亦记立淑妃曹氏为皇后。',10,'三月庚寅，立淑妃曹氏為皇后。','立后日对读。',source=ann,relation='corroborates')
claim('event',E,'description','旧曹后传辑校引《五代会要》称长兴元年五月十四日册为皇后。',10,'長興元年五月十四日，冊為皇后；','这是旧书编校引书的册命记日，与三月庚寅制立不同环节；未把册礼提前三月，也不把曹传辑文当现存独立原传。五月十四原纪日不换公历。',source=cao,relation='adds')
relationship('曹妃','帝','妻子',10,'后，帝匹也，至尊之位，誰敢干之！','曹氏→李嗣源为妻子，采用新后传所论皇后帝匹及本段曹氏立后语境；不由宫中妹称另建姐妹边。',source=court)
E=ev('wang_treats_empress_respectfully','王德妃恭谨侍奉曹皇后，曹皇后亦怜爱王氏',10,'德妃事后','后亦怜之。',[('王妃','恭谨侍后者'),('曹妃','受侍、怜爱王氏者')],when='930年立曹氏为后后；本句未独载日',note='只记宫中相处，不推终身亲属或联盟关系。')
claim('event',E,'description','新王妃传补记侍奉帝后起居、食毕才退，皇后益爱之。',10,'妃事皇后亦甚謹，每帝晨起，盥櫛服御，皆妃執事左右，及罷朝，帝與皇后食，妃侍，食徹乃退，未嘗少懈，皇后心亦益愛之。','连叙日常非均发生庚寅当日，后续明宗病和杀人事留其年代，不提前录入。',source=court,relation='adds')
E=ev('wang_introduced_through_an','追叙王德妃因安重诲得进，起初感激安氏',10,'初，王德妃','常德之。',[('王妃','因安氏得进、起初感恩者'),('重诲','引进王妃者')],year=None,when='追叙王氏得进之初；本句未纪年',note='初标追叙，不赋930；常德之为感激非王氏以安为德妃，不建姻亲。')
claim('event',E,'description','新王妃传记有人通过安重诲告知明宗王氏，明宗遂纳王氏。',10,'有言王氏於安重誨者，重誨以告明宗而納之。','未名推荐者不造人物；新承夏夫人已卒但未确年。王氏名花见羞仅作来源身份参考，不新增同人。',source=wang,relation='adds')
E=ev('an_remonstrates_palace_spending','追叙李嗣源在位渐久宫中用度渐侈，安重诲屡进规谏',10,'帝性俭约','重诲每规谏。',[('帝','宫中用度由俭渐侈者'),('重诲','规谏者')],year=None,when='追叙在位日久的用度变化；确年未载',note='未写成930年突然全国财政崩溃；每为屡次非本日一次。')
E=ev('an_warns_wang_against_brocade_flooring','王德妃取外库锦作地衣，安重诲以刘皇后为戒进谏，王氏由此怨安',10,'妃取外库锦',None,[('王妃','取锦作地衣、因谏怨安者'),('重诲','以刘后为戒切谏者'),('刘后','被引用为鉴戒的故后')],year=None,when='追叙锦地衣谏争；确年未独载',note='妃承王德妃，刘后沿李存勖后；故后仅被援引，不在场，不新增本年刘后奢侈事件；地衣为铺地织物不是王妃衣服，怨为主书归述。')
E=ev('gaoconghui_breaks_with_wu','高从诲遣使赴吴上表，以先墓在中原、恐唐讨伐而吴救援不及为由谢绝吴',11,'高从诲遣使','谢绝之。',[('高从诲','奉表谢绝吴者')],place='荆南至吴',note='恐与援不及是表文忧虑，不等唐已灭荆南；中国按当时中原语境，不作现代国家边界。使未名不造实名。')
E=ev('wu_attack_jingnan_unsuccessful','吴发兵攻打高从诲，未能取胜',11,'吴遣兵',None,[('高从诲','受吴进攻者')],place='荆南',note='吴兵将领未具，不擅归徐知诰或杨溥亲自出征；不克为此攻未成，非吴政权灭亡。二十四史高传未检同案具体攻战，不硬补先前谢唐奏。')
E=ev('dong_petitions_wu_staff_office','董璋恐武虔裕窥察，表请其兼行军司马',12,'董璋恐','表兼行军司马，',[('璋','表请武氏兼职者'),('武虔裕','绵州刺史、被表请兼职者')],when='930年四月甲午朔',place='东川',note='表兼是上表请兼，不独证朝廷核准；恐窥是董的怀疑，不证武已完成间谍行为。')
E=ev('dong_imprisons_wuqianyu','董璋将绵州刺史武虔裕囚于府廷',12,'董璋恐',None,[('璋','囚禁武氏者'),('武虔裕','被囚者')],when='930年四月甲午朔',place='东川府廷',note='囚不等杀，勿提前后续两川反叛战；表兼和拘禁分录。')
claim('event',E,'description','旧董璋传记董擅追武虔裕、囚于衙署，并说武是安重诲心腹。',12,'璋已擅追綿州刺史武虔裕，囚於衙署。虔裕，安重誨之心腹也，故先囚之。','旧传承荀咸乂增兵前连叙，未独四月朔；旧其后五月檄与主秋事异时，留后续对读，不把整段一并当本日行动。心腹为史家说法，不另造亲属关系。',source=dong,relation='corroborates')
E=ev('fuxi_contends_with_an','追叙符习自恃宿将，议论多抗安重诲',13,'宣武节度使符习','论议多抗安重诲，',[('符习','议论抗安氏者'),('重诲','被抗对象')],year=None,when='符习致仕前一段时期；起年未载',note='自恃为主书描述，议论相抗不等军事谋反。')
E=ev('an_reports_fuxi_faults','安重诲寻求符习过失并奏报',13,'重诲求','奏之，',[('重诲','寻过并奏者'),('符习','被奏对象')],when='930年四月丁酉致仕前',note='只载求失，不推全部罪已经证实。')
claim('event',E,'description','新符习传则说迎合安重诲者举报符习厚敛汴人。',13,'習素為安重誨所不悅，希其旨者上言習厚斂汴人，乃以太子太師致仕，','新所记具体厚敛为举报内容，举报者未名，不独立认定符已犯法或安亲自作出该条举报；与主求失奏之不同详略。',source=fu,relation='adds')
E=ev('fuxi_retires_taizi_taishi','后唐诏符习以太子太师致仕',13,'丁酉，',None,[('符习','受诏以太子太师致仕者')],when='930年四月丁酉',note='前批已制徙李继曮宣武；主称符宣武是此前职衔，旧明确前汴州，不当两人在930本日都实任宣武。')
claim('event',E,'description','旧明宗纪称前汴州节度使符习加太子太师致仕，并进封卫国公。',13,'丁酉，前汴州節度使、檢校太尉、兼侍中符習加太子太師致仕，進封衛國公。','旧前字说明旧任职衔，进封为同诏补充，不把致仕视为处死；符传其后中风卒留后续年代。',source=apr,relation='adds')
E=ev('mengzhixiang_adds_zhongshuling','孟知祥加兼中书令',14,'戊戌，','加孟知祥兼中书令，',[('知祥','加兼中书令者')],when='930年四月戊戌',note='加兼官不等已经成为中央日常宰相；新孟伝系二月南郊，纪时差并列。')
claim('event',E,'time_original','新孟世家把加拜孟知祥中书令系于长兴元年二月南郊。',14,'長興元年二月，明宗有事于南郊，加拜知祥中書令。','主四月戊戌、新二月有纪时差；保留两说，不能悄改主日期或另造重复授职。',source=meng,relation='conflicts')
E=ev('xialuqi_adds_pingzhang','夏鲁奇加同平章事',14,'戊戌，',None,[('夏鲁奇','加同平章事者')],when='930年四月戊戌',note='同平章事兼衔不等赴京任实相。')
claim('event',E,'description','旧明宗纪同戊戌记遂州节度使夏鲁奇加同平章事。',14,'戊戌，遂州節度使夏魯奇加同平章事，','补本职遂州，与主授兼衔对应。',source=apr,relation='corroborates')
E=ev('congke_strikes_an_zhen_ding','追叙李从珂与安重诲在真定饮酒争言，李从珂殴安，安逃免',15,'初，帝在真定','重诲走免；',[('从珂','酒争殴安者'),('重诲','被殴、走免者')],year=None,when='追叙李嗣源在真定时；确年未载',place='真定',note='初不赋930；帝在真定为背景不证帝亲见殴斗；走免不是安已经死亡。')
E=ev('congke_apologizes_an_holds_grudge','李从珂酒醒后悔而谢，安重诲仍衔恨',15,'既醒，','重诲终衔之。',[('从珂','酒醒悔谢者'),('重诲','仍衔恨者')],year=None,when='真定酒争之后；确年未载',place='真定背景',note='心理归述按主书，未造永久仇敌边或臆断930全部事件唯一因果。')
E=ev('princes_respect_an_in_power','安重诲用事，李从荣、李从厚等皇子敬事安氏',15,'至是，','皆敬事不暇。',[('重诲','执政受敬事者'),('从荣','敬事安氏的皇子'),('从厚','敬事安氏的皇子')],when='930年四月本段当时；确日未载',note='至是为当时政治状况，敬事不等认安为父或正式隶属其军。')
E=ev('an_disparages_congke_emperor_ignores','安重诲屡向李嗣源短毁河中节度使李从珂，帝不听',15,'时从珂为','帝不听。',[('重诲','屡短毁者'),('从珂','被短毁的河中节度使'),('帝','未听信者')],when='930年四月河中事变前；反复奏言未独载日',place='后唐朝廷',note='主称李河中节度与同平章事沿已有身份，不造当日新授职；帝不听不等安未曾奏。')
E=ev('an_forges_order_to_yangyanwen','主书记安重诲矫称帝命，使杨彦温驱逐李从珂',15,'重诲乃矫','杨彦温使逐之。',[('重诲','被主书记为矫帝命者'),('杨彦温','受谕逐李者'),('从珂','被拟驱逐者')],when='930年四月戊戌前后；主本句未独载日',place='后唐朝廷至河中',note='主河东牙内疑地名，杨在河中闭门且新河中衙内佐核，展示河中事变，原河东不改；矫命是史书归述，不当现存原诏或已复原秘令。')
claim('event',E,'description','新明宗纪记四月戊戌安重诲使河中衙内指挥使杨彦温逐李从珂。',15,'夏四月戊戌，安重誨使河中衙內指揮使楊彥溫逐其節度使從珂。','主河东与新河中字异并列，新戊戌明确系逐事，不能把后壬寅问奏全赋戊戌；安是否有真实帝命是事件争点。',source=ann,relation='adds')
E=ev('yang_closes_hezhong_gates_congke_outside','李从珂出城阅马时，杨彦温勒兵闭门拒其入城',15,'是日，','彦温勒兵闭门拒之，',[('从珂','出城阅马、被拒入者'),('杨彦温','勒兵闭门者')],when='930年四月，逐从珂当日；旧奏称本月五日',place='河中城、阅马地',note='主是日承驱逐事件，旧五日是从珂奏报的实际日，不自行换成干支或公历；闭门不等从珂已经战败死亡。')
claim('event',E,'description','旧明宗纪壬寅记李从珂奏称本月五日在黄龙庄阅马，杨彦温据城称奉宣命。',15,'臣今月五日，閱馬於黃龍莊，衙內指揮使楊彥溫據城叛，臣尋時詰問，稱奉宣命。','这是奏报引文，黄龙庄补具体阅马地点；壬寅是奏闻并发讨时，不赋实际闭城。',source=apr,relation='adds')
E=ev('yang_claims_privy_council_order','李从珂扣门质问，杨彦温声称受枢密院宣命、请李入朝',15,'从珂使人扣门','请公入朝。”',[('从珂','遣人扣问者'),('杨彦温','声称受枢密院宣者')],when='930年四月逐从珂当日',place='河中城门',note='杨言奉宣是其自述，与安否认并列；未名使者不另造人，不把杨辩称当真实帝诏。')
E=ev('congke_reports_from_yuxiang','李从珂停虞乡，遣使奏报河中事变',15,'从珂止于虞乡','遣使以状闻。',[('从珂','停虞乡、遣使上状者')],when='930年四月事变后、壬寅使者至前',place='虞乡至后唐朝廷',note='虞乡非已回洛阳，不擅算途中耗时。')
E=ev('emperor_questions_an_about_yang_order','李嗣源问安重诲杨彦温何以称奉宣，安否认并请速讨',15,'使者至，壬寅，','宜速讨之。”',[('帝','问宣命来由者'),('重诲','称杨妄言、请讨者'),('杨彦温','被论及者')],when='930年四月壬寅',place='后唐朝廷',note='安称奸人妄言是安的辩词，不推翻主矫命归述；杨仅被论及非到朝面讯。')
E=ev('emperor_offers_yang_jiangzhou_to_inquire','李嗣源疑有内情，授杨彦温绛州刺史以诱致讯问',15,'帝疑之，','除彦温绛州刺史。',[('帝','欲诱致并授官者'),('杨彦温','被授绛州刺史者')],when='930年四月壬寅问奏后',place='后唐朝廷、绛州职',note='授官用于诱致，不等杨已赴任或获免罪。')
claim('event',E,'description','新安传亦记拜杨彦温绛州刺史以诱致。',15,'拜彥溫絳州刺史，以誘致之。','新同案补证，前遣范氲礼物虽存快照，本批不据自动段落扩出无关姓名。',source=an,relation='corroborates')
E=ev('an_insists_emperor_sends_suo_yao','安重诲固请发兵，李嗣源命索自通、药彦稠讨杨彦温',15,'重诲固请','将兵讨之。',[('重诲','固请发兵者'),('帝','命讨者'),('索自通','西都留守、领兵讨者'),('药彦稠','步军都指挥使、领兵讨者'),('杨彦温','受讨对象')],when='930年四月壬寅',place='西都至河中',note='索西都留守旧称西京，同主体新任首次本批；药亦新人物，不与杨彦稠混。杨受讨不当朝廷部将同时指挥。')
claim('event',E,'description','新明宗纪壬寅记西京留守索自通与侍卫步军指挥使药彦稠讨杨。',15,'壬寅，西京留守索自通、侍衞步軍指揮使藥彥稠討之。','官名详略沿各底本；讨之承杨案，不延至吴。',source=ann,relation='corroborates')
E=ev('emperor_orders_yang_captured_alive','李嗣源命药彦稠务必生致杨彦温，拟亲自讯问',15,'帝令彦稠','吾欲面讯之。',[('帝','命生致并欲面讯者'),('药彦稠','受生致命者'),('杨彦温','被要求活捉对象')],when='930年四月发兵时',note='命令不等已活捉或面讯；后续死亡须另录。')
E=ev('congke_summoned_hurries_luoyang','朝廷召李从珂赴洛阳，李认为被安重诲构陷而驰入自明',15,'召从珂诣洛阳',None,[('帝','召入朝者'),('从珂','受召、驰入自明者'),('重诲','被李认为构陷者')],when='930年四月讨杨之后',place='虞乡至洛阳',note='主知为重诲所构归李所知，洛阳实际抵达在下一段；自明不等全部案情已经查清。')
E=ev('an_adds_zhongshuling','安重诲加兼中书令',16,'加安',None,[('重诲','获加兼中书令者')],note='主无独干支，旧同案四月壬寅可补；此加衔非新任枢密使。')
claim('event',E,'time_original','旧明宗纪将安重诲加兼中书令系于四月壬寅，仍任枢密使。',16,'壬寅，以樞密使安重誨為留守、太尉、兼中書令，使如故。','主仅加兼，旧另载留守太尉，保留兼衔与使如故，不推已赴外镇；不把旧壬寅直接抹去主未具日状态。',source=apr,relation='adds')
E=ev('congke_arrives_confined_private_residence','李从珂抵洛阳，李嗣源责之，命归第并断朝请',17,'李从珂至洛阳','绝朝请。',[('从珂','受责、归私第断朝请者'),('帝','责从珂、令归第者')],when='930年四月，辛亥收城前后；抵达确日未载',place='洛阳',note='绝朝请为不得朝见请谒，不写成终身禁足或已被杀；日期不强承上一段壬寅。')
E=ev('suo_captures_hezhong_yang_killed','索自通等攻拔河中，斩杨彦温',17,'辛亥，','斩杨彦温，',[('索自通','攻拔河中将领'),('药彦稠','同案攻城将领'),('杨彦温','被斩者')],when='930年四月辛亥',place='河中',note='主等与后责药、新旧列二将同讨对应；不说李从珂亲自杀杨。死亡日与癸丑献首分。')
claim('event',E,'description','新明宗纪辛亥记索自通执杨彦温而杀，并注违生擒之命故书杀。',17,'辛亥，自通執彥溫殺之。','新注是书法说明，不作现存实物判书。',source=ann,relation='corroborates')
claim('event',E,'description','新安传说药彦稠等攻破河中后迎合安重诲旨意，斩杨以灭口。',17,'彥稠等攻破河中，希重誨旨，斬彥溫以滅口。','灭口动机为新书明确归述；主仅拔斩和违生致，不把这动机悄改成全部史书共同确证。',source=an,relation='adds')
E=ev('yang_head_presented','索自通、药彦稠等传杨彦温首级来献',17,'癸丑，','传首来献。',[('索自通','传首献报的讨军将领'),('药彦稠','传首献报的讨军将领'),('杨彦温','首级被传献者')],when='930年四月癸丑',place='河中至后唐朝廷',note='死者作为被处置对象非本人行动；癸丑献不等癸丑杀。')
claim('event',E,'description','旧明宗纪癸丑记索自通、药彦稠奏收河中、斩杨并传首来献。',17,'癸丑，索自通、藥彥稠等奏，收復河中，斬楊彥溫，傳首來獻。','旧把奏报杀斩合记癸丑，主明确辛亥拔斩、癸丑献报；动作日与报告日分，不立虚假两次死亡。',source=river,relation='adds')
E=ev('emperor_rebukes_yao_failure_alive','李嗣源怒药彦稠未生致杨彦温，深责之',17,'上怒药彦稠','深责之。',[('帝','责将违生致者'),('药彦稠','受责者')],when='930年四月癸丑献首后',note='深责未见该日处死药氏或正式降官，不推已问出杨口供。')
E=ev('an_prompts_chancellors_accuse_congke','安重诲示意冯道、赵凤以李从珂失守为由请求加罪',17,'安重诲讽','宜加罪。',[('重诲','讽相加罪者'),('冯道','受示意奏失守者'),('赵凤','受示意奏失守者'),('从珂','被拟加罪者')],when='930年四月收河中后',note='讽为示意、请求未获准，不当三人已执行处死从珂。')
E=ev('emperor_rejects_chancellors_punishing_congke','李嗣源指李从珂曲直未明、受奸党倾陷，拒冯道赵凤加罪奏',17,'上曰：“吾儿','二人惶恐而退。',[('帝','拒加罪奏者'),('冯道','受斥退者'),('赵凤','受斥退者'),('从珂','帝保护的对象')],when='930年四月首次相奏加罪时',note='奸党为帝说法，不猜完整名单；吾儿为收养父子语境，不推李从珂为亲生。')
E=ev('zhaofeng_repeats_emperor_silent','赵凤另日再言加罪李从珂，李嗣源不回应',17,'它日，','上不应。',[('赵凤','再奏者'),('帝','不回应者'),('从珂','被再奏加罪对象')],when='930年四月首次拒奏之后另日；未具干支',note='不应不是同意，勿自行算次日或公历日。')
E=ev('an_petitions_emperor_defends_congke','安重诲次日自请处置李从珂，李嗣源以从珂昔日助养自述相护，准其私第闲居',17,'明日，重诲自言之','何复言！”',[('重诲','再请处置者'),('帝','以昔助养自述相护者'),('从珂','被保护、准闲居者')],when='930年四月赵凤再奏之明日；未具干支',note='帝追忆从珂拾马粪助养嵌入当日辩词，追忆无年不另赋930拾粪事件；父子语不是新生物学证。')
claim('event',E,'description','新安传帝自述从珂昔年担石灰、拾马粪助养，并说杜门私第。',17,'此兒為我擔石灰，拾馬糞，以相養活，今貴為天子，獨不能庇之邪！使其杜門私第，亦何與公事！','新多担石灰细节为帝话补述，未确年，不独录本年助养；纸本未校。',source=an,relation='adds')
E=ev('suo_appointed_hezhong','索自通受任河中节度使',17,'丙辰，','以索自通为河中节度使。',[('索自通','获任河中节度者')],when='930年四月丙辰',place='河中军镇职',note='任命非当然同日抵镇。')
claim('event',E,'description','旧明宗纪同丙辰记以西京留守索自通任河中节度使。',17,'丙辰，以西京留守、檢校司徒索自通為河中節度使。','同日任职佐证，不把西京与河中当两人。',source=river,relation='corroborates')
E=ev('suo_reports_weapons_as_congke_private','索自通到镇承安重诲旨，登记军府甲仗数量，奏称李从珂私造',17,'自通至镇','以为从珂私造，',[('索自通','籍甲仗并上数者'),('重诲','旨意来源'),('从珂','被指私造者')],when='930年四月丙辰任命后至镇；确日未载',place='河中',note='以为私造是指控，不直接认定从珂非法造兵；籍上为登记数量非没收全军，也不虚填数量。')
E=ev('wang_protects_congke','王德妃在宫中保护李从珂，从珂因此免于加罪',17,'赖王德妃','从珂由是得免。',[('王妃','宫中保护者'),('从珂','受保护而免者')],when='930年四月籍甲仗奏后；确日未载',place='后唐宫中',note='得免关联本案加罪，不是免未来所有处分或王与从珂私通。')
E=ev('lvqi_visits_advises_congke_memorials','士大夫避交李从珂，吕琦因住近时往见，李的每月奏请均先咨询吕',17,'士大夫不敢',None,[('琦','礼部郎中史馆修撰、访从珂并供奏请咨询者'),('从珂','受访、咨询奏请者')],when='930年从珂归第后；时往、每月未独载日',place='洛阳邻居私第',note='时往非每天同居；士大夫无名单，不把所有人建成敌人；先咨为奏请建议，不等代笔全部奏章。吕沿910幸存少年同人。')
claim('event',E,'description','新吕琦传记吕琦后来迁礼部郎中、史馆修撰。',17,'歲餘，遷禮部郎中、史館脩撰。','新本句承前经历未独930，不另造930确日授职；仅印证当时职衔身份。脩/修原字分别留。',source=lv,relation='corroborates')
E=ev('emperor_receives_extended_title','李嗣源加尊号圣明神武文德恭孝皇帝',18,'戊午，',None,[('帝','获加尊号者')],when='930年四月戊午',note='尊号不是改元或另立新帝。')
claim('event',E,'time_original','旧明宗纪记长兴元年四月二十五日戊午御文明殿受册徽号。',18,'戊午，帝御文明殿受冊徽號，冊曰：「維長興元年，歲次庚寅，四月甲午朔，二十五日戊午，','旧册文原纪月日佐核，未自行换公历；后续册文名单只快照未另录诸人。',source=tit,relation='adds')
claim('event',E,'description','新明宗纪同戊午记群臣上圣明神武文德恭孝皇帝尊号。',18,'戊午，羣臣上尊號曰聖明神武文德恭孝皇帝。','主新同尊号原字沿各底本，群臣未名不造具体额外进号者。',source=ann,relation='corroborates')
E=ev('an_accuses_wangjianli_weizhou','安重诲称王建立经过魏州时有摇众之语',19,'安重诲言','有摇众之语，',[('重诲','奏言摇众者'),('王建立','被指摇众的昭义节度使')],when='930年五月丙寅制致仕前；过魏州确日未载',place='魏州、后唐朝廷',note='摇众为安所言不等已证王谋反；王与安素不协背景不自动写敌人边。')
E=ev('wangjianli_retires_taifu','后唐制王建立以太傅致仕',19,'五月，丙寅，',None,[('王建立','受制太傅致仕者')],when='930年五月丙寅',note='致仕非处死或没收家产。')
claim('event',E,'description','旧明宗纪同五月丙寅记潞州节度使王建立为太傅致仕，因安言过邺都扇摇。',19,'丙寅，以少府監韋肅為洺州刺史，以潞州節度使王建立為太傅致仕。建立素與安重誨不協，因其入朝，乃言建立自鎮歸朝過鄴都，日有扇搖之言，以是罪之，故令致仕。','潞州与主昭义、邺都与主魏州为同处职地称法不同；罪由安奏述，不凭此认定叛逆。韦肃只引句上下文未本批新增任职事实。',source=may,relation='corroborates')
reviews={
10:'曹为李嗣源后，不与李存勖母同姓曹混；主三月庚寅立后，旧同日制立择日册、旧后传辑引五月十四册，区分环节。王妹称不证姐妹，拒代不等曾当后；王因安得进与宫锦谏争追叙null，刘故后仅被援引。新明宗即位起概叙不倒赋全部926，后续杀安与从荣未提前。曹妻方向曹→李，王沿旧稳定人。',
11:'高表述恐唐讨、援不及不是唐实际已经发兵灭高；中国为当时中原，非现代国境。吴攻未克独记，将未名不擅给杨或徐当行军者；二十四史高传未检同案具体吴攻，不冒充此前谢唐奏补证。',
12:'甲午朔董表兼武行军司马与囚分；表非已核准、恐窥非已确间谍、囚非杀。旧董段后五月檄与主秋季事差留后续对读，此批只对囚武。原字与旧署廷异称留。',
13:'符抗安是此前反复议论null，安求失奏非既确罪；新举报厚敛是迎合安者之言，未名不造人。丁酉致仕旧明确前汴州职，避免与已徙李继曮都写同时现任宣武；卫国公同诏补，后中风死未提前。',
14:'孟主四月戊戌、新二月南郊加中书令纪时差并列不悄覆盖、不另造重复授职；夏同日平章旧遂州本职佐核。兼衔不等本人新赴京当实相。',
15:'真定醉殴悔谢追叙null；诸皇子敬安政治状况不造亲属。主河东牙内与新河中衙内、旧河中奏异地称保留，展示按同案河中。新戊戌逐、旧奏称四月五日阅黄龙庄，与壬寅问奏发兵区分；主是日不强继上戊戌全段。矫帝命为史述、杨奉宣与安妄言辩词分别归属；诱授绛州非已赴任，命生致非已经审讯；驰洛与下一抵达分。杨彦温不混王彦温或边彦温，药彦稠不混杨彦稠，索按两书同职同案新建。',
16:'主加安中书令无独日，旧壬寅留守太尉中书令使如故补；旧同日其他事务未因此全录。',
17:'洛阳归第绝朝请不等死；辛亥拔斩、癸丑献首奏报分，旧癸丑收斩传首是报告时。新灭口动机是补书归述，不替主共享确证。皇帝责药不证处死或降职。安讽相、赵再奏、安次日自奏分，帝不应非允罪。帝追忆拾粪/新担灰助养不当930当年事件，父子话不证从珂亲生；不另新建生父边。丙辰索任与到镇籍兵器奏指控分，私造未确；王保护免罪非王李私通。吕邻近时访、每月咨奏沿910少年同人，新职衔补，不推另任930确日，不造朋友边。',
18:'戊午加尊号非改元，新同尊号、旧四月二十五原纪日补；引册文其他名单未另录诸人。',
19:'安言摇众归指控不认已反，五月丙寅太傅致仕非处死。旧潞州/主昭义、邺都/魏州同职地称法并列，旧引句韦肃只定位上下文不凭快照跳段新增。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(10,20):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=930,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(10,20)],next_paragraph='zztj-v277-y0930-p020',next_volume=277,next_year=930,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续930年第10—19段、原15—24行；曹氏立后、荆南谢吴、两川官职与囚武、符习致仕、河中事变全过程、加尊号及王建立致仕。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(10,20)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
