# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 69–77."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,78))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'82c9d42c','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-934-meng-name-decree',YEAR/'part-08/sources/library/tongjian-279-934-meng-name-decree','5f4233fa','司马光等'),
 ('xinwudaishi-061-jinling-fire',YEAR/'part-01/sources/library/xinwudaishi-061-jinling-fire','570df7a6','欧阳修'),
 ('xinwudaishi-062-jing-name',ROOT/'content/books/zizhi-tongjian/vol-272/year-0923/part-09/sources/library/xinwudaishi-062-jing-name','83be3260','欧阳修'),
 ('xinwudaishi-065-ma-empress',ROOT/'content/books/zizhi-tongjian/vol-270/year-0919/part-01/sources/library/xinwudaishi-065-ma-empress','2605ed0c','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-meng-name-decree','tongjian-279-934-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p069-p077',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key=='xinwudaishi-048-an-shuqian':record=dict(record,section_title='卷48·安叔千传',citation='《新五代史》卷48·安叔千传，段落 '+record['id']+'；已核传首，纸本及异文待核。')
    if key in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[key]
        record=dict(record,section_title=label,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(69, 78):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    if source=='xinwudaishi-048-an-shuqian':record=dict(record,citation='《新五代史》卷48·安叔千传，段落 '+record['id']+'；已核传首，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[source]
        record=dict(record,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '十月条下' if n==69 else '十一月条下' if n==70 else '十二月条下' if n<=75 else '本年秋冬' if n==76 else '年末追叙；部分动作具体年未载'
        citation = f'卷279·清泰元年（934；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_10_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','徐知诰':'李昪','景通':'李璟','景迁':'徐景迁','汉主':'刘岩','弘度':'刘弘度','马氏':'越国夫人马氏','鄂王':'李从厚'}
NEW_ALIASES={'郭知琼':['郭知瓊'],'范延晖':['范延暉'],'徐景迁':['徐景遷'],'安叔千':[]}

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

def event(code, title, n, quote, actors, when=None, note='', year=934, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='934年'+('十月' if n==69 else '十一月' if n==70 else '十二月')+'条下；确日未独载'
    key = 'event_zztj_279_0934_' + code
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
        edge = 'participation_zztj_279_0934_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_279_0934_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
E['wen']=ev('zhang_yanlang_besieges_wenzhou','张延朗率兵围攻文州',69,'雄武节度使','围文州，',[('张延朗','雄武节度使、率兵围文州者')],place='文州',note='主先写延郎后写延朗，旧纪同月同任官用张延朗，沿已有主体，属于异写而非繁简；围攻不等于攻克。')
ev('guo_zhiqiong_captures_jianshi','阶州刺史郭知琼攻下尖石寨',69,'阶州刺史','拔尖石寨。',[('郭知琼','阶州刺史、攻取尖石寨者')],place='尖石寨',note='只录攻拔，不编寨将、兵数、精确坐标或围文州已经胜利。')
ev('li_yanhou_garrison_xingzhou','李延厚率果州兵驻兴州',69,'蜀李延厚','屯兴州，',[('李延厚','率果州兵驻兴州者')],place='兴州')
ev('li_yanhou_sends_fan_relief','李延厚派先登指挥使范延晖率兵救文州',69,'遣先登指挥使','救文州，',[('李延厚','派救兵者'),('范延晖','先登指挥使、率救兵者')],place='文州',note='范延晖不与范延光合并，原文明示不同名字与官职；派救不等于已击败围军。')
ev('zhang_yanlang_lifts_siege_returns','张延朗解文州之围而归',69,'延朗解围','而归。',[('张延朗','解围归军者')],place='文州',note='解围而归明示撤围，不补战败、撤回地点及追击损失。')
ev('feng_hui_returns_from_qianqu','兴州刺史冯晖自乾渠领戍兵归凤翔',69,'兴州刺史','归凤翔。',[('冯晖','兴州刺史、率戍兵归凤翔者')],place='乾渠、凤翔',note='沿既有冯晖主体，与后唐泸州刺史同名主体分别保留；乾渠未校坐标，不从地名字形猜现代地点。')
E['jing_return']=ev('xu_calls_jing_back_jinling','十一月徐知诰召景通回金陵',70,'十一月，','还金陵，',[('徐知诰','召子回金陵者'),('景通','原司徒同平章事、被召回者')],place='金陵',note='景通沿既有李璟主体，本时仍以徐景通称呼；规范名不表示934年已改名李璟。')
E['jing_office']=ev('jing_town_armies_vice_command','景通任镇海宁国节度副大使、诸道副都统并判中外诸军事',70,'为镇海、','判中外诸军事；',[('景通','三项军政职掌获任者')],place='金陵',note='两镇副大使及诸道副都统、判中外诸军事依主句并录；不能简化为两镇正节度使。')
E['qian']=ev('xu_jingqian_jiangdu_government','徐景迁任左右军都军使、左仆射、参政事，留江都辅政',70,'以次子','留江都辅政。',[('徐知诰','授命次子留辅者'),('景迁','原牙内马步都指挥使海州团练使、留江都辅政者')],place='江都',note='当前这组官职据主；新吴世家太保平章事为跨年压缩记载，主935年才另加同平章事，不覆盖934任职或前移授命。')
relationship('徐知诰','景通','父亲',70,'徐知诰召其子司徒、同平章事景通还金陵，','主其子明示父子；沿全站李昪与李璟，不反建子边。')
relationship('徐知诰','景迁','父亲',70,'以次子牙内马步都指挥使、海州团练使景迁为左右军都军使、左仆射、参政事，留江都辅政。','次子承徐知诰，登记李昪是徐景迁的父亲，不因徐李姓不同拒绝明示关系。')
claim('event',E['jing_return'],'description','新吴世家亦记知诰召景通还金陵，并任镇海军节度副使。',70,'知誥召景通還金陵，為鎮海軍節度副使，','独立印证回召与副职；新省宁国等官，不伪称全部官衔同载。',source='xinwudaishi-061-jinling-fire',relation='corroborates')
claim('event',E['jing_office'],'description','新南唐世家记李昪篡国前召景归金陵为副都统。',70,'昪將篡國，召景歸金陵為副都統。','新不具十一月和全部官衔，印证回召任副都统，不以将篡国判断取代当年具体事件。',source='xinwudaishi-062-jing-name',relation='corroborates')
claim('person',people['李璟'],'aliases','新南唐世家记景初名景通，是李昪长子，后改名璟。',70,'景，初名景通，昪長子也。既立，又改名璟。','身份核对用于同人复用，既立后改名不前移934。',source='xinwudaishi-062-jing-name')
claim('event',E['qian'],'description','新吴世家在天祚六年一段内称景迁为太保、平章事，与王令谋等执政。',70,'以其子景遷為太保、平章事，與令謀等執政。','新记官衔与主934不同，主935三月另加同平章事；保压缩时间及官衔差异，不能当934十一月同授的独立确证。',source='xinwudaishi-061-jinling-fire',relation='conflicts')
E['an']=ev('an_shuqian_zhenwu_appointment','十二月己巳安叔千由易州刺史任振武节度使',71,'十二月，己巳，','为振武节度使，',[('安叔千','原易州刺史、振武节度使获任者'),('帝','任命者')],when='934年十二月己巳')
E['yin']=ev('yin_hui_zhangguo_appointment','十二月己巳尹晖由齐州防御使任彰国节度使',71,'齐州防御使','为彰国节度使。',[('尹晖','原齐州防御使、彰国节度使获任者'),('帝','任命者')],when='934年十二月己巳')
claim('person',people['安叔千'],'description','安叔千是沙陀人。',71,'叔千，沙陀人也。','族属根据主句，不当沙陀为出生城市，不推生年。')
claim('person',people['安叔千'],'description','新安叔千传称其字胤宗，是沙陀三部落人。',71,'安叔千字胤宗，沙陀三部落人也。','传首核对安叔千，卷48；字号补充、族属互证；不因同传后列四镇将所有历任放在934。',source='xinwudaishi-048-an-shuqian',relation='corroborates')
claim('event',E['an'],'description','旧末帝纪同记十二月己巳安叔千任安北都护、振武节度使，原为北面马军都指挥使及易州刺史。',71,'己巳，以北面馬軍都指揮使、易州刺史安叔千為安北都護、振武節度使；','同日同新职；安北都护和前北面马军都指挥使为旧纪独补，不编原官起任年份。',source='jiuwudaishi-046-934-december',relation='corroborates')
claim('event',E['yin'],'description','旧末帝纪同记尹晖由齐州防御使任彰国军节度使。',71,'以齊州防禦使尹暉為彰國軍節度使。','承旧己巳，尹暉繁体沿尹晖已有主体。',source='jiuwudaishi-046-934-december',relation='corroborates')
ev('shi_reports_khitan_withdraws','十二月壬申石敬瑭奏契丹撤去，罢兵归',72,'壬申，','罢兵归。',[('石敬瑭','奏报及罢兵归者')],when='934年十二月壬申奏报；契丹撤去确日未独载',note='壬申为奏日，不将契丹撤兵日自动等同；主未列所归地，不补太原实际到达日。')
E['zhang']=ev('zhang_yanlang_chancellor_three_commissions','十二月乙亥征张延朗任中书侍郎、同平章事、判三司',73,'乙亥，','判三司。',[('张延朗','原雄武节度使、征入任相并判三司者'),('帝','征召任命者')],when='934年十二月乙亥',note='主张延郎沿已核张延朗；姓名异写与官军号分别说明，不新造张延郎。')
claim('event',E['zhang'],'description','旧末帝纪同记乙亥以秦州节度使张延朗为中书侍郎、同平章事、判三司。',73,'乙亥，以秦州節度使張延朗為中書侍郎、同平章事、判三司；','旧秦州与主雄武军号写法不同，官与日期相同；嵌注次年三月的押班奏请不录成934事件。',source='jiuwudaishi-046-934-december',relation='corroborates')
E['ma']=ev('southern_han_empress_ma_dies','十二月辛巳南汉马皇后去世',74,'辛巳，','汉皇后马氏殂。',[('马氏','南汉皇后、去世者')],when='934年十二月辛巳',place='南汉',note='复用越国夫人马氏主体；新书既记册后及马殷女身份，死亡日期本次只主具，不伪造多书互证。')
claim('person',people['越国夫人马氏'],'death_year','南汉马皇后于934年十二月辛巳去世。',74,'辛巳，汉皇后马氏殂。','殂明示死亡，当年当月顺叙，未换算公历日。')
claim('person',people['越国夫人马氏'],'description','新南汉世家记越国夫人马氏曾被册为皇后，是楚王马殷的女儿。',74,'三年，冊越國夫人馬氏為皇后。馬氏，楚王殷女也。','该书三年为此前乾亨三年919身份，不是934册后，也不印证本次死日。',source='xinwudaishi-065-ma-empress')
E['meng']=ev('meng_zhixiang_buried_heling','十二月甲申孟知祥葬和陵，庙号高祖',75,'甲申，','庙号高祖。',[('孟知祥','后蜀高祖、被葬者')],when='934年十二月甲申',place='和陵',note='文武圣德英烈明孝皇帝为所葬孟知祥，不将身后的葬日设为七月死日，也不指现在孟昶。')
E['e']=ev('li_conghou_buried_huiling_south','十二月乙酉李从厚葬徽陵城南，坟高仅数尺',75,'乙酉，','观者悲之。',[('鄂王','被葬者')],when='934年十二月乙酉',place='徽陵城南',note='鄂王是本年四月由帝降封的李从厚，已发布主第21段明示；与秦王李从荣不同。封为坟土，不译加封王爵；观者悲为书述。旧相近庚午命葬却写从荣，列异文待考，不强作同人互证。')
claim('event',E['e'],'description','旧末帝纪十二月庚午条写诏葬庶人从荣，并准以公礼葬；与本条鄂王李从厚的对象不能直接等同。',75,'庚午，詔葬庶人從榮。有司上言：「依貞觀中庶人承乾，以公禮葬。」從之。','保留旧底本从荣异文，不据此给李从荣造乙酉葬事，也不擅改从荣为从厚；诏命日与执行日即使同事也不能混为一日，纸本待核。',source='jiuwudaishi-046-934-december',relation='conflicts')
E['dry']=ev('autumn_winter_drought_migration','934年秋冬干旱，民众多流亡，同华蒲绛尤严重',76,'是岁秋、','尤甚。',[],when='934年秋、冬；各地具体起止日未载',place='同、华、蒲、绛',note='旱情及流亡均据主叙，无数量不编人口统计，州名先保史名、未核坐标。')
claim('event',E['dry'],'description','旧末帝纪称自九月至十二月无雨雪，十二月庚寅帝到龙门祈雪。',76,'庚寅，幸龍門祈雪，自九月至是無雨雪故也。','旧记无雨雪及祈雪，为旱情背景独补；主秋冬与旧九月至此范围分别保，不倒算开始日或称两书同具流亡四州。',source='jiuwudaishi-046-934-december',relation='corroborates')
ev('liu_orders_hongdu_guard_recruitment','南汉刘岩命秦王刘弘度招募宿卫兵一千人',77,'汉主命','募宿卫兵千人，',[('汉主','命募兵者'),('弘度','判六军秦王、受命招兵者')],when='934年年末条下；月日未载',place='南汉',note='千人为主数量；沿刘岩与刘弘度主体，不因后改刘龑另建人。')
ev('hongdu_close_to_recruits','刘弘度亲近所招募的市井子弟',77,'皆市井无赖子弟，','弘度昵之。',[('弘度','亲近新招子弟者')],when='934年年末条下；月日未载',place='南汉',note='无赖是史书的评价，展示中性市井子弟，保逐字引文；不以出身直接认定所有人犯罪。')
ev('yang_advises_hongdu_upbringing','杨洞潜谏刘岩：秦王应亲近端士，不宜治军并亲近群小',77,'同平章事杨洞潜','况昵群小乎！”',[('杨洞潜','同平章事、提出谏言者'),('汉主','受谏者'),('弘度','被议论的秦王')],when='934年年末条下；月日未载',place='南汉',note='谏言与其治军评价作为杨的意见，不变成现代确定的违法事实；冢嫡为书中身份用语。')
ev('liu_declines_warning_hongdu','刘岩以教儿戎事回应杨洞潜，最终未告诫刘弘度',77,'汉主曰：','终不戒弘度。',[('汉主','回应并未戒者'),('杨洞潜','受回应的谏者'),('弘度','未被告诫者')],when='934年年末条下；月日未载',place='南汉',note='终不戒为作者所叙结果，非没有收到谏言；不编处罚或后来政治因果。')
ev('yang_witnesses_guard_looting','杨洞潜出后见卫士抢商人金帛，商人不敢投诉',77,'洞潜出，','商人不敢诉，',[('杨洞潜','出而目睹者')],when='934年年末条下；月日未载',place='南汉',note='卫士与商人未具名，不造个体和人数；不必所有抢者都是前招千人，主未逐一明示。')
ev('yang_retires_claiming_illness','杨洞潜以病为由归家',77,'因谢病','归第；',[('杨洞潜','谢病归第者')],when='934年年末叙事条下；归第确日未载',place='南汉',note='前汉曰“政乱如此...”的汉字及说话主语有疑，不作为确定杨或刘发言事实；谢病为本人理由，不确诊身体疾病。')
ev('yang_not_summoned_then_dies','追记杨洞潜归家后长期未被召用，后来去世',77,'久之，','遂卒。',[('杨洞潜','久未被召、后来去世者')],year=None,when='杨洞潜谢病归第后久之；去世具体年份未载',place='南汉',note='久之是后续追述，没有明确死年，不将杨死年硬填934，也不补无人赡养、赐死等因果。')
reviews={69:'围文、拔寨、屯兴、派救、解围归与冯领戍归六动作分；延郎/延朗是异写沿旧主体，范延晖不混范延光；冯兴州与泸州同名分别保。',70:'景通回金陵和新职、景迁留江都分；沿李璟/李昪规范主体，当时名徐不前移改名。两条父亲关系方向明确；新吴世家景迁太保平章事与主934、935授职时序并列待核。',71:'己巳安与尹两命；主沙陀和新安传字胤宗族属互核，不推生年；旧补安北都护及前马军职。',72:'壬申石奏日与契丹撤去确日分，不补回屯地。',73:'乙亥张任相判三司主旧同，延郎与延朗、雄武与秦州保持独立字样沿同人；旧嵌注次年三月不提前录。',74:'马后死据主辛巳；新乾亨三年册后与马殷女只身份补证，死未假多书确证。',75:'甲申孟知祥葬和陵非死日，乙酉鄂王是李从厚而非秦王从荣；封数尺为坟土；旧从荣及庚午命葬异文单列，不改原字不强同事。',76:'秋冬旱流亡四州，无数无坐标；旧九月以来无雨雪祈雪独补，不说旧也具四州流亡。',77:'募兵千、亲近、谏言与回应、见卫掠、不敢诉、谢病归、久之未召而死分。主汉曰疑字未强定杨或刘发言，不造该发言参与。杨死年null；无赖为史评，展示中性。'}
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(69,78):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(69,78)],next_paragraph='zztj-v279-y0935-p001',next_volume=279,next_year=935,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续934年第69—77正文段，原74—82行；文州攻守、吴兄弟军政任职、唐任免与契丹奏报、南汉马后去世、孟知祥与鄂王李从厚葬礼、秋冬旱情、杨洞潜谏与退居后续。发布核验后934年跨卷278、279的89正文全部完成；935年待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(69,78)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
