# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 21–30."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 58))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'6e2476a2' if directory.name.endswith('-collation') else '8df19907','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))

specs += [('tongjian-278-933-may-july',YEAR/'part-02/sources/library/tongjian-278-933-may-july','0f922712','司马光等'),('xinwudaishi-068-baohuang',ROOT/'content/books/zizhi-tongjian/vol-277/year-0931/part-04/sources/library/xinwudaishi-068-baohuang','077b3114','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-may-july','tongjian-278-933-september-october']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0933-p021-p030',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(21, 31):
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
        citation = f'卷278·长兴四年（933）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0933_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','上':'李嗣源','璘':'王延钧','文杰':'薛文杰','光':'吴光','文纪':'卢文纪','知祥':'孟知祥','简求':'卢简求','从荣':'李从荣','延光':'范延光','延寿':'赵延寿','吴主':'杨溥','德妃王氏':'王氏（吴皇后）','赟':'冯赟','齐国公主':'兴平公主','硃弘昭':'朱弘昭','弘昭':'朱弘昭','文宝':'张文宝'}
NEW_ALIASES={'薛文杰':['薛文傑'],'吴光':['吳光'],'卢文纪':['盧文紀'],'卢简求':['盧簡求'],'卢嗣业':['盧嗣業'],'王氏（吴皇后）':['吴德妃王氏','吳德妃王氏'],'冯章':['馮章','冯璋','馮璋'],'张文宝':['張文寶'],'张绚':['張絢'],'张顗':['張顗']}

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

def event(code, title, n, quote, actors, when=None, note='', year=933, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='933年七月条后八月条前；确日未独载' if n<=22 else '933年八月条下；原纪时另见校核' if n<=24 else '933年九月条下；确日未独载'
    key = 'event_zztj_278_0933_' + code
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
        edge = 'participation_zztj_278_0933_' + code + '_' + pk
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
    corrections={}
    import uuid
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
    people_ids={str(uuid.uuid5(namespace,x['key'])):x['key'] for x in registry.values()}
    for revision in sorted((ROOT/'content/revisions').glob('*/relations.json')):
        if not (revision.parent/'publication.json').exists():continue
        for revision_row in json.loads(revision.read_text()).get('relations',[]):corrections[revision_row['key']]=revision_row['after']
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if x['key'] in corrections:
                c=corrections[x['key']];x=dict(x,person_a_key=people_ids[c['person_a']],person_b_key=people_ids[c['person_b']],relation_type=c['relation_type'])
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_278_0933_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive paragraphs; primary chronology and independently cited supplements.
aug='jiuwudaishi-044-933-august';sep='jiuwudaishi-044-933-september';zhang='jiuwudaishi-068-zhang-wenbao';lu='xinwudaishi-055-lu-wenji';qin='xinwudaishi-015-qin-marshal';minsrc='xinwudaishi-068-baohuang'
ev('min_resume_after_quake','七月戊子王延钧复位',21,'戊子，','复位。',[('璘','地震后复位的闽主')],when='933年七月戊子',place='闽',note='承前七月，接五月庚辰地震避位；不是此前931宗教遜位复位同一事件，不新造一次即皇帝位。')
E=ev('xue_state_finance','王延钧任薛文杰为国计使并亲任之',21,'初，','亲任之。',[('璘','任用国计使的闽主'),('文杰','福建中军使、为迎合闽主聚财而获任者')],year=None,when='初，追叙国计使任用；确年、月、日未独载',place='闽',note='聚使用疑聚财文义但原字保留；初不强定933七月，巧佞为史书评价而非可量品性。')
claim('event',E,'description','新闽世家亦记因国用不足，以中军使薛文杰为国计使。',21,'而閩地狹，國用不足，以中軍使薛文傑為國計使。','同任官补动因，书证并列，不把新书按即帝位后排列转成确定任命日。',source=minsrc,relation='corroborates')
E=ev('xue_confiscation_torture','薛文杰寻富民之罪籍没财产，并施以榜捶火熨',21,'文杰阴求','仍以铜斗火熨之。',[('文杰','以罪没产及施刑的国计使')],year=None,when='初条追叙任国计使后的概述；确年月日未知',place='闽',note='概述多次做法，不编每一富户实名、次数或刑法制度；保史载刑具但不扩写施刑细节。')
claim('event',E,'description','新书记薛文杰察民隐事，以罪籍没富人之财佐国用，闽人怨之。',21,'文傑多察民間陰事，致富人以罪，而籍沒其貲以佐用，閩人皆怨。','佐用及民怨补证，皆怨为史叙概括，不推全体民户调查。',source=minsrc,relation='corroborates')
ev('wu_guang_framed','建州吴光入朝，薛文杰图其财欲治罪',21,'建州土豪','将治之；',[('光','入朝的建州土豪、被图财求罪者'),('文杰','图财欲治罪者')],year=None,when='初条追叙吴光入朝及求罪；确年月日未知',place='建州、闽朝廷',note='将治是拟治罪，不能写已刑杀吴光；入朝不是进入吴国朝廷。')
ev('wu_guang_defects_wu','吴光率众近万人叛奔吴',21,'光怨怒，','叛奔吴。',[('光','率众奔吴者')],year=None,when='初条追叙求罪后奔吴；确年月日未知',place='闽建州至吴',note='且万人为近万概数，未独纪时不套七月戊子；不推已战败或已入吴官职，吴主没有本句亲自接纳证，不加参与。')
E=ev('shu_investiture_envoys','后唐任卢文纪、吕琦为蜀王册礼使，并赐孟知祥一品朝服',22,'帝以工部','一品朝服。',[('帝','任册礼使、赐朝服者'),('文纪','工部尚书、蜀王册礼使'),('吕琦','礼部郎中、蜀王册礼使'),('知祥','受朝服的蜀王')],place='后唐朝廷至蜀',note='主并列册礼使不自行拆使副职，二人职务沿同名同朝识别；赐一品服不是又授皇帝位。')
ev('shu_royal_insignia','孟知祥自制九旒冕、九章衣，车服旌旗拟王者',22,'知祥自作','皆拟王者。',[('知祥','自行准备王者仪制者')],place='蜀',note='九旒九章照数，拟天子仪制与934称帝分；制造时无独日不套八月戊申。')
ev('shu_envoys_arrive','八月乙巳朔卢文纪等至成都',22,'八月，','等至成都。',[('文纪','抵成都的册礼使'),('吕琦','同行册礼使')],when='933年八月乙巳朔',place='成都',note='等沿本段前列两使，抵达与受册戊申分。')
ev('shu_receives_investiture','八月戊申孟知祥备仪卫北面受册，乘玉辂步辇归府',22,'戊申，','乘步辇而归。',[('知祥','受蜀王册命者'),('文纪','册礼使'),('吕琦','册礼使')],when='933年八月戊申',place='成都驿、蜀王府',note='主服痛冕疑衮字，快照及引文保字，展示概称冕服不猜病痛；北面受册王爵不是蜀独立称帝。')
relationship('简求','文纪','祖父',22,'文纪，简求之孙也。','卢简求→卢文纪表示祖父，主孙、新同祖名互核；未推祖仍在933任节度。')
claim('person',people['卢文纪'],'description','新书记卢文纪字子持，祖简求曾为唐太原节度使，父嗣业官至右补阙。',22,'盧文紀字子持，其祖簡求，為唐太原節度使，父嗣業，官至右補闕。','姓名与祖父印证主末句；过往履历只补人物字段，不把祖父任职当933新事件。',source=lu,relation='adds')
relationship('卢嗣业','文纪','父亲',22,'父嗣業，官至右補闕。','卢嗣业→卢文纪为父亲，摘录位于文纪传首，不猜是否仍生或官至该年。',source=lu)
E=ev('mingzong_honor_title','八月戊申群臣为明宗上尊号',23,'戊申，','恭孝皇帝，',[('帝','受尊号者')],when='933年八月戊申',place='后唐朝廷',note='主尊号圣明神武广道法天文德恭孝皇帝，群臣未名不猜冯道为具体提案人。')
claim('event',E,'description','旧明宗纪记八月戊申御明堂殿受册，尊号作圣明神武广运法天文德恭孝皇帝。',23,'八月戊申，帝被袞冕，禦明堂殿受冊，徽號曰聖明神武廣運法天文德恭孝皇帝。','主广道与旧广运异字保留；同日同尊号大部相合，补仪礼地点，不悄换底本。',source=aug,relation='conflicts')
E=ev('mingzong_title_amnesty','明宗受尊号时大赦',23,'戊申，','大赦。',[('帝','大赦君主')],when='933年八月戊申',place='后唐',note='承尊号戊申条，下属赦令未给条目不自行列免罪名单。')
claim('event',E,'description','旧书记受册礼毕大赦，常赦所不原者亦赦除。',23,'禮畢，製大赦天下，常赦所不原者咸赦除之。','补赦范围沿旧文，不推未列出的具体罪目。',source=aug,relation='adds')
E=ev('mingzong_title_army_gifts','在京与诸道将士优给，月内两次颁给令支度更窘',23,'在京及','月度益窘。',[('帝','朝廷颁给君主')],when='933年八月戊申条附记；旧史京军优给纪己酉',place='后唐京师及诸道',note='主未为优给独载日，旧己酉京军与主广及诸道保范围，月度益窘与月度为军财政语不推确数；前批七月乙酉给为前次不重复同事。')
claim('event',E,'description','旧史八月己酉记侍卫诸军优给有差，月内再颁使府藏无余积。',23,'己酉，賜侍衛諸軍優給有差。時月內再有頒給，自茲府藏無餘積矣。','月内及府藏耗竭为旧史措辞，主月度益窘分层，不编余额为零现代统计。',source=aug,relation='adds')
E=ev('he_ze_petitions_crown_prince','何泽表请立李从荣为太子，意图重获进用',24,'太仆少卿','表请立从荣为太子。',[('何泽','太仆少卿致仕、上表者'),('从荣','被请立为太子者'),('上','寝疾、收表的君主')],note='主冀复进用为史叙动机，不写已成功复任；表请不等已立储。')
claim('event',E,'description','新唐家人传亦记明宗病时何泽上书请立从荣为皇太子。',24,'太僕少卿何澤上書，請立從榮為皇太子。是時明宗已病，','同人同申请补证，不把未受立的秦王题作太子。',source=qin,relation='corroborates')
ev('mingzong_reacts_prince_petition','明宗览立太子表泣下，私称将归老太原',24,'上览表','太原旧第耳。”',[('上','览表及私下发言者')],note='将归老为发言，不是已退位、已迁太原。')
ev('mingzong_orders_prince_deliberation','丙戌明宗诏宰相、枢密使议立太子',24,'不得已，','议之。',[('上','下诏商议君主')],when='933年八月条后主文丙戌；音注张校作壬戌，待核',note='底本丙戌至后丁卯日次排列需版本校核，不擅改丙辰或推公历。宰相枢密集体本句未点名，不把后见范赵当全体名单。')
ev('congrong_declines_crown_prince','丁卯李从荣见明宗，自称幼小愿学治军民而不愿太子名',24,'丁卯，','群臣所欲也。”',[('从荣','自陈不愿太子名的秦王'),('上','回应群臣所欲的君主')],when='933年八月条下丁卯',note='幼小是自陈说辞，不据此推未成年生年；与上一诏日次如原文保留。')
ev('congrong_blames_chancellors','李从荣对范延光、赵延寿称立太子是夺兵柄幽东宫',24,'从荣退，','幽之东宫耳。”',[('从荣','向执政表不满者'),('延光','听秦王指责的枢密使'),('延寿','听秦王指责的枢密使')],note='秦王认为幽禁为观点，不写宰执已夺兵柄或已幽东宫。')
ev('fan_zhao_report_prince_speech','范延光、赵延寿具白明宗秦王之言',24,'延光等知','即具以白上；',[('延光','奏报秦王言论者'),('延寿','奏报秦王言论者'),('上','受奏君主')],note='知上意及惧为史叙，不扩大为已经秘密废储联盟。')
E=ev('congrong_all_armies_marshal','八月辛未李从荣受命天下兵马大元帅',24,'辛未，','天下兵马大元帅。',[('上','制命者'),('从荣','获天下兵马大元帅者')],when='933年八月辛未',note='元帅不是皇太子，本批请立储无正式立储完成事实。')
claim('event',E,'description','旧明宗纪八月辛未记秦王以本官充天下兵马大元帅，加食邑万户、实封三千户。',24,'辛未，秦王從榮以本官充天下兵馬大元帥，加食邑萬戶，實封三千戶；','同日授元帅，食邑实封补字段，不当实际全国兵数。',source=aug,relation='adds')
claim('event',E,'description','新书亦将天下兵马大元帅任命记于从荣拒太子、疑夺兵柄之后。',24,'延光等患之，乃加從榮天下兵馬大元帥。','独立书目并列，是否史源相依未判，不算双书独立确证。',source=qin,relation='corroborates')
ev('wu_wang_empress','九月甲戌朔杨溥立德妃王氏为皇后',25,'九月，','为皇后。',[('吴主','立后者'),('德妃王氏','由德妃立皇后者')],when='933年九月甲戌朔',place='吴',note='王氏未名，以吴皇后限定，不合并他朝同姓王氏；未见二十四史对应此立后语，本条依据主书。')
relationship('德妃王氏','吴主','妻子',25,'吴主立德妃王氏为皇后。','王氏（吴皇后）→杨溥为妻子，原文妃、皇后身份明示；不猜其是否王戎女、是否某王子生母。')
for name,label in [('延光','范延光'),('延寿','赵延寿')]:
 E=ev('attendant_'+label,label+'于九月戊寅加兼侍中',26,'戊寅，','兼侍中。',[(name,'加兼侍中者'),('帝','加官君主')],when='933年九月戊寅',note='两人加官逐主体分录，兼侍中不是免枢密原职。')
 claim('event',E,'description','旧明宗纪同九月戊寅记范延光、赵延寿加兼侍中，依前充使。',26,'戊寅，樞密使範延光、趙延壽並加兼侍中，依前充使。','旧範与主范仅字形同人，依前充使补说明。',source=sep,relation='corroborates')
E=ev('marshal_audience_protocol','九月癸未准节度使见元帅按军礼廷参',27,'癸未，','从之。',[('从荣','受元帅朝见礼的秦王'),('帝','准中书所奏君主')],when='933年九月癸未',note='中书本句未名，平章事兼衔也从军礼；礼规则不是某节度使已行一次具体见礼。')
claim('event',E,'description','旧书载带兵权者阶下具军礼参见，使相初见亦展公礼，元帅府天下军务用帖、六军诸卫事用公牒。',27,'中書奏：「元帥儀注，諸道節度使以下帶兵權者，階下具軍禮參見；其帶使相者，初見亦展一度公禮。天下軍務公事，元帥府行帖指揮，其判六軍諸衛事則公牒往來，其官屬軍職，委元帥府奏請。」從之。','旧本本句无癸未独日，主纪日保；军务文书补礼仪程序，不据此写实际攻吴。',source=sep,relation='adds')
claim('event',E,'description','新书记兼平章事者初见军礼，其后许客礼。',27,'其兼同中書門下平章事者，初見亦如之，其後許如客禮。','补初次与后次之别，不能概为以后每次都军礼。',source=qin,relation='adds')
ev('feng_yun_chancellor_proposed','明宗欲加宣徽使判三司冯赟同平章事',28,'帝欲加','同平章事；',[('帝','提出加衔者'),('赟','拟加同平章事者')],note='欲加是方案，实际后授同二品另录，不直接写此方案已授。')
relationship('冯章','赟','父亲',28,'赟父名章。','冯章→冯赟父亲；旧纪记亡父，死年不明，不能做933卒事件。')
claim('person',people['冯章'],'description','旧明宗纪记冯赟亡父名章，故改平章事为同二品。',28,'贇亡父名章，故改平章事為同二品。','亡仅表此时已故，不推具体卒年；名章沿父子同姓标准名。',source=sep,relation='adds')
E=ev('feng_yun_second_rank','九月庚寅冯赟加同中书门下二品并充三司使',28,'执政误引','充三司使。',[('赟','加同二品、受三司使者'),('帝','加官君主')],when='933年九月庚寅（主）；旧同事列戊子',note='为父名章避讳，主评误引故事；二品为衔名，不改为现代品级二品普通官。主庚寅与旧戊子两日不同并列。')
claim('event',E,'description','旧明宗纪在九月戊子条载宣徽南院使判三司冯赟同中书门下二品充三司使。',28,'宣徽南院使、判三司馮贇依前檢校太傅、同中書門下二品，充三司使。','同职同事补旧南院及检校，时间主庚寅旧戊子不合待核，不能悄改主日。',source=sep,relation='conflicts')
E=ev('congrong_requests_guards','李从荣请严卫、捧圣步骑两指挥为牙兵',29,'秦王从荣请','为牙兵。',[('从荣','申请两指挥作牙兵的秦王')],when='933年九月条下；确日未载',note='请兵与实际每日朝入阵仗分；指挥为军单位不推两个个人名。')
claim('event',E,'description','新书记从荣又请严卫、捧圣千人为牙兵。',29,'又請嚴衞、捧聖千人為牙兵，','主两指挥、新千人单位差别保留，均为请，不当已点验实际兵数。',source=qin,relation='adds')
ev('congrong_armed_processions','李从荣入朝时常率数百骑持弓矢驰骋道路',29,'每入朝，','驰骋衢路；',[('从荣','率武装骑从入朝者')],year=None,when='每入朝，惯常行为概述；起讫年月未知',note='每为惯常概述，未独次不全硬定933九月某日；未载实战不当已宫变。')
E=ev('congrong_tests_huainan_proclamation','李从荣令文士试草檄淮南书，表达廓清海内意向',29,'令文士','海内之意。',[('从荣','命试草檄书、表志向者')],when='933年九月条下；确日未载',note='草拟、试作与志向不等出师攻吴，文士未名不套刘赞或任赞。')
claim('event',E,'description','新书记从荣命寮属及四方游士试作征淮檄。',29,'從榮又命其寮屬及四方游士試作征淮檄，陳己所以平一天下之意。','写作对象补寮属四方游士，未名不造具体作者。',source=qin,relation='adds')
ev('congrong_threatens_chancellors','李从荣私言即位后必族执政',29,'从荣不快','必族之！”',[('从荣','向亲近者发出条件性威胁者')],when='933年九月条下；确日未载',note='一旦南面为未然条件，不写已经即帝位、已族诛范延光赵延寿。所亲未名不猜府僚。')
ev('fan_zhao_seek_external_posts','范延光、赵延寿因惧李从荣屡求外补',29,'范延光、','屡求外补以避之。',[('延光','惧秦王而求外任的枢密使'),('延寿','惧秦王而求外任的枢密使')],when='933年九月条下屡求；起日未知',note='屡求为连续多次概述，未每次日不造每次独事件。')
ev('mingzong_angry_external_requests','明宗因范赵求去而怒，称欲去自去',29,'以上为','奚用表为！”',[('上','对请求表示怒意者'),('延光','求外任者'),('延寿','求外任者')],note='为见己病而求去是帝的理解，不取代前文两臣惧秦王解释，保两种叙事层次。')
E=ev('princess_pleads_zhao_health','齐国公主在禁中为赵延寿陈病不堪机务',29,'齐国公主复','不堪机务。”',[('齐国公主','为延寿陈病的公主'),('延寿','被陈病不堪机务者')],place='后唐禁中',note='陈病为公主所言，不能据此诊病；旧兴平进封齐国印证沿既有兴平公主，不造新女。')
claim('person',people['兴平公主'],'aliases','旧史记兴平公主赵氏进封齐国公主，沿同一公主主体。',29,'興平公主趙氏進封齊國公主；','赵氏在石氏赵氏并列可按夫家称，勿强替本姓李；只补齐国公主称号，不改既有亲缘。',source=sep,relation='adds')
ev('fan_zhao_offer_one_departure','九月丙申范延光、赵延寿请轮与勋旧任事，愿先出一人，明宗许之',29,'丙申，','上乃许之。',[('延光','请求轮任、先出一人者'),('延寿','请求轮任、先出一人者'),('上','许先出一人的君主')],when='933年九月丙申',note='愿听一人先出、若新人不称可召回为承诺，不写已经同时解任或已召回。')
E=ev('zhao_yanshou_xuanwu','九月戊戌赵延寿任宣武节度使',29,'戊戌，','宣武节度使；',[('延寿','出任宣武节度使者'),('上','任命者')],when='933年九月戊戌',place='后唐朝廷、宣武军',note='宣武治汴州由旧同日同事补证，受任不等当日已抵镇。')
claim('event',E,'description','旧明宗纪同戊戌记枢密使赵延寿任汴州节度使。',29,'戊戌，以樞密使趙延壽為汴州節度使，','主军名旧治名同任，沿宣武汴州不要另造两个镇职。',source=sep,relation='corroborates')
E=ev('zhu_hongzhao_pivot','九月戊戌朱弘昭任枢密使、同平章事',29,'以山南节道','同平章事。',[('硃弘昭','由原镇转枢密使、加同平章事者'),('上','任命者')],when='933年九月戊戌',place='后唐朝廷、襄州',note='主山南节道疑东道误字保底本，旧明确襄州；硃弘昭沿朱弘昭，旧宏昭异写同人，不造朱宏昭另一人。')
claim('event',E,'description','旧史同日记襄州节度使朱宏昭任检校太尉、同平章事、枢密使。',29,'以襄州節度使朱宏昭為檢校太尉、同平章事，充樞密使。','补原镇襄州及检校，宏弘同任识别，非简繁自动映射。',source=sep,relation='adds')
ev('zhu_hongzhao_declines_rebuked','朱弘昭复辞枢密任命，遭明宗叱责后不敢再言',29,'制下，','乃不敢言。',[('弘昭','辞命遭叱后止言者'),('上','叱责近臣君主')],note='拒任意向被叱后不再言，不记录正式免去新职。')
E=ev('zhang_wenbao_shipwreck','张文宝泛海使杭州遇船坏，水工小舟救其至天长',30,'吏部侍郎','所存者五人。',[('文宝','奉使杭州而遇海难者')],year=None,when='主置933年九月条后未独日；旧传记长兴初，确年待核',place='海路至天长',note='主从二百仅存五为概数沿文，不把旧传长兴初强改933；水工未名不造人。')
claim('event',E,'description','旧张文宝传记长兴初奉使浙中海船坏，水工小舟救；副使吏部郎中张绚同至淮南界。',30,'長興初，奉使浙中，泛海船壞，水工以小舟救，文寶與副使吏部郎中張絢信風至淮南界，','主置933条下与旧长兴初时间差保；张绚同场副使是原文明示，可补同事件参与，不凭副使衔猜父子。',source=zhang,relation='conflicts')
# Supplementary named participant on the same voyage.
pk=person('张绚',30,'吏部郎中、副使，与张文宝同至淮南界','文寶與副使吏部郎中張絢信風至淮南界，',source=zhang)
edge='participation_zztj_278_0933_zhang_wenbao_shipwreck_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=E,role='吏部郎中、副使，同至淮南界',status='draft'))
claim('person_event',edge,'role','张绚为副使，与张文宝同至淮南界。',30,'文寶與副使吏部郎中張絢信風至淮南界，','旧传明确副使名，主未名，不另造第二次海难。',source=zhang,relation='adds')
E=ev('wu_aids_tang_envoy','杨溥厚礼海难唐使，备仪服钱币并牒钱氏境上迎接',30,'吴主厚礼','境上迎侯。',[('吴主','礼待援助及发牒者'),('文宝','受礼援的唐使')],year=None,when='主置933年九月条后未独日；旧传长兴初海难续事',place='吴境、至吴越边境',note='钱氏为统治集团泛称，未确由钱镠或钱元瓘受牒不强造具体君主参与；牒令迎不等已经迎完成。')
claim('event',E,'description','旧传亦记杨溥礼待甚厚，并赠钱币食物。',30,'偽吳楊溥禮待甚至，兼厚遺錢幣、食物。','旧偽吴为史家称谓展示用吴，原字保；不当唐吴正式恢复国交。',source=zhang,relation='corroborates')
E=ev('zhang_accepts_food_only','张文宝仅受饮食，辞其他馈赠并述外交理由',30,'文宝独受','何辞以谢！”',[('文宝','辞钱物、陈君臣宾主理由者')],year=None,when='海难礼待后；主置933条下，旧传长兴初续事',place='吴',note='不通问为使者发言层次，与既有吴使往来事实可异，不能据发言删旧使事件。辞礼不是拒食。')
claim('event',E,'description','旧传记文宝受食物，退钱币，吴人善之。',30,'文寶受其食物，反其錢幣，吳人善之，','同受食拒钱补证，不夸为绝不接受援助。',source=zhang,relation='corroborates')
E=ev('zhang_reaches_hangzhou_returns','张文宝最终达命杭州而还',30,'吴主嘉之，','而还。',[('文宝','达命杭州并返还者'),('吴主','嘉许使者者')],year=None,when='海难礼待后达命返还；确年、月、日待核',place='吴至杭州、返程',note='主而还未名归处，旧还青州补；完成达命不等唐吴已正式通好。')
claim('event',E,'description','旧传记送文宝等复至杭州宣国命，后还青州。',30,'送文寶等復至杭州宣國命，還青州，','旧句末卒接人生终局，死亡不能据此认作返回当日。',source=zhang,relation='adds')
relationship('张顗','文宝','父亲',30,'張文寶，昭宗朝諫議大夫顗之子也。','张顗→张文宝父亲，传首明示；父职为昭宗朝不当933在任，不与张颢混。',source=zhang)
claim('person',people['张文宝'],'death_year','旧明宗纪九月条记吏部侍郎张文宝卒，933。',30,'吏部侍郎張文寶卒。','卷44长兴四年九月内明载卒；主本段使行乃追叙，时间差保，旧未独干支不推戊戌卒日。',source=sep,relation='adds')
next(x for x in B['people'] if x['key']==people['张文宝'])['death_year']=933
collation='tongjian-278-933-ceremony-collation'
events={x['key']:x for x in B['events']}
def eventkey(code):return 'event_zztj_278_0933_'+code
claim('event',eventkey('shu_royal_insignia'),'description','通鉴音注解释车服旌旗拟王者，是拟天子仪制。',22,'所謂「車服旌旗皆擬王者」，是擬天子也。','补同书注释的礼制解读；不把八月受蜀王册命改为已经称帝。',source=collation,relation='adds')
claim('event',eventkey('shu_receives_investiture'),'description','音注版正文该字作兗冕，明载在成都驿舍行册礼。',22,'知祥服兗冕，備儀衞詣驛，{{*|時館盧文紀等於成都驛舍。}}','原TXT痛冕与同书兗冕异字保留，展示概述冕服，未按痛字推疾病；不是繁简直接替换。',source=collation,relation='conflicts')
claim('event',eventkey('mingzong_orders_prince_deliberation'),'time_original','主书正文丙戌，固定音注版张校记丙作壬，即壬戌。',24,'丙{{*|【張：「丙」作「壬」。】}}戌','保原字及张校说明，不采此前无据猜测丙辰；主正文日次仍列异文，纸本待核。',source=collation,relation='conflicts')
claim('person',people['冯章'],'aliases','冯赟之父正文作冯章，音注称璋，保为同一父亲姓名异字。',28,'贇父名章，{{*|贇父璋事帝於潛躍，爲閽者。}}','章璋不是繁简对应字，正文与注在同父语境，附异名检索而不造第二父亲。',source=collation,relation='conflicts')
claim('event',eventkey('zhang_wenbao_shipwreck'),'location_name','主书海难舟至天长，通鉴音注疑此地，提出海中天赐盐场之说。',30,'天長縣在揚州西一百一十里，其地北不至淮，東不至海，豈小舟隨風所能至！','注有地理疑问，未独证定位，仍保主天长及unknown坐标；不把注猜说改为确定现代位置。',source=collation,relation='conflicts')
events[eventkey('zhang_wenbao_shipwreck')]['location_note']='主史载天长，通鉴音注质疑舟行可达并提出海中盐场之说，地理待核；不填坐标。'
reviews={
21:'七月戊子复位承五月地震避位，不混931宗教复位。初追叙薛任用与掠财及吴光奔吴年null，不把每个动作套当日；聚使用疑字保，拟治罪非已杀，近万概数。新闽世家补国用任官与民怨，不抢录后徐彦巫视杀吴英。',
22:'任册使赐服、自制礼制、八月乙巳到成都、戊申受册分，主痛冕疑衮不编疾病。两使不猜使副分职；受蜀王册非称帝。卢文纪新字子持、祖简求及父嗣业补身份，祖父父亲有向，不把祖官当933任命。',
23:'八月戊申尊号、大赦、军优给分；广道主广运旧留异字。旧明堂与册礼、己酉京军给补，主诸道范围保，不把上一批七月给重建；窘及无余积为史叙不造余额精数。',
24:'何泽表请、帝泣与归老言、丙戌议诏、丁卯秦辞、对范赵疑话、范赵奏、辛未元帅分。丙戌日次与音注张校壬戌异文保留，不改正文或推公历月日；请储未立储、南面非已即位、归老非已退休、幼小非生年；旧辛未任与食邑实封、新同因果叙补。',
25:'九月甲戌朔吴德妃王氏立后，本条主书明确，无二十四史对应语不虚增补证。吴皇后限定防同姓错合并、妻子方向，未名不猜父王戎或王子生母。',
26:'九月戊寅范延光赵延寿逐主体兼侍中，旧依前枢使补非免职；范範同人仅字形。',
27:'九月癸未元帅见礼奏准是制度非已发生某镇见礼；旧详带兵、使相公礼与军务帖、公牒分；新初见军礼后次客礼，不能说永久每次军礼。',
28:'欲加平章方案与同二品实授分，亡父冯章父亲关系但卒年未知；同书音注父名璋与正文章留姓名异字，附冯璋别名。主庚寅旧戊子异日并列，不把同二品等普通官品；执政误引故事为主评价，旧补避父章。',
29:'请牙兵、每入朝惯常阵仗年null、试草檄、南面后族执政条件威胁、范赵屡求、帝怒、公主陈病、丙申先出一人获许、戊戌赵宣武与朱枢密、朱辞被叱分；不当已攻吴、已即位、已族诛。新千人主两指挥保请数；旧兴平进封齐国识既有人、赵氏称不改姓。主山南节道旧襄州及宏弘异字校，宣武汴州同镇不当已到。',
30:'海难及生还数、吴援礼牒、辞钱受食、达命返还分。主附933九月旧传长兴初时间冲突年null，不硬全933；副使张绚及父张顗旧原明补，勿与颢混。主从二百存五不扩精名；同书音注疑天长地理并提出盐场说，不定现代坐标。钱氏未名不凭时点猜钱镠钱元瓘；外交发言不当否定已录吴使。旧九月张文宝卒人物death_year补，未独日，不说使还当日卒。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,31):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=933,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(21,31)],next_paragraph='zztj-v278-y0933-p031',next_volume=278,next_year=933,supplements=supplements,source_contexts=[dict(file=os.path.relpath(ROOT/'content/books/zizhi-tongjian/vol-278/year-0933/part-02/sources/context/qian-yuanliao-name/response.json',P/'sources'),sha256=hashlib.sha256((ROOT/'content/books/zizhi-tongjian/vol-278/year-0933/part-02/sources/context/qian-yuanliao-name/response.json').read_bytes()).hexdigest(),note='同书固定音注版2115814原始API响应沿part-02已归档快照。')],excluded_non_body=[],coverage='卷278连续933年第21—30段、原56—65行；闽复位与国计旧事、蜀王册礼、明宗尊号与军给、立储议与元帅任、吴立后、侍中礼仪与冯赟避讳、秦王军府及枢密换任、唐使海难追叙。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,31)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
