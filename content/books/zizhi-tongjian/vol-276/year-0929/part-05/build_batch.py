# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 929, paragraphs 28–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 37))
specs=[
 ('tongjian-276-929-autumn',YEAR/'part-04/sources/library/tongjian-276-929-autumn','824c0b81','司马光等'),
 ('tongjian-276-929-wu-power',P/'sources/library/tongjian-276-929-wu-power','fce44f4b','司马光等'),
 ('tongjian-276-929-winter-end',P/'sources/library/tongjian-276-929-winter-end','fce44f4b','司马光等'),
 ('jiuwudaishi-040-929-october',P/'sources/library/jiuwudaishi-040-929-october','fce44f4b','薛居正等'),
 ('xinwudaishi-046-kangfu-court',P/'sources/library/xinwudaishi-046-kangfu-court','fce44f4b','欧阳修'),
 ('xinwudaishi-046-kangfu-appointment',P/'sources/library/xinwudaishi-046-kangfu-appointment','fce44f4b','欧阳修'),
 ('xinwudaishi-040-hancheng',P/'sources/library/xinwudaishi-040-hancheng','fce44f4b','欧阳修'),
 ('xinwudaishi-061-929-wu-change',P/'sources/library/xinwudaishi-061-929-wu-change','fce44f4b','欧阳修'),
 ('xinwudaishi-051-lirenju-dongzhang',YEAR/'part-03/sources/library/xinwudaishi-051-lirenju-dongzhang','0a803f54','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-929-autumn','tongjian-276-929-wu-power','tongjian-276-929-winter-end']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0929-p028-p032',
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
lines = (ROOT / 'resources/derived/tongjian/276.txt').read_text().splitlines()
for n in range(28, 33):
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
        citation = f'卷276·天成四年（929）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0929_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','福':'康福','重诲':'安重诲','澄':'韩澄','洙':'韩洙','知祥':'孟知祥','仁矩':'李仁矩','知询':'徐知询','知诰':'李昪','温':'徐温','镠':'钱镠','廷望':'周廷望','吴主':'杨溥'}
NEW_ALIASES={'韩澄':['韓澄'],'李匡宾':['李匡賓'],'牛知柔':[],'卫审𡷣':['衛審𡷣'],'周廷望':[]}

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

def event(code, title, n, quote, actors, when=None, note='', year=929, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='929年'+('十月' if n<=30 else '十一月')+'本段；确日未载'
    key = 'event_zztj_276_0929_' + code
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
        edge = 'participation_zztj_276_0929_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0929_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Consecutive source paragraphs, with competing kinship and personal names explicit.
oct='jiuwudaishi-040-929-october';court='xinwudaishi-046-kangfu-court';kf='xinwudaishi-046-kangfu-appointment';han='xinwudaishi-040-hancheng';wu='xinwudaishi-061-929-wu-change';dong='xinwudaishi-051-lirenju-dongzhang'
def past(code,title,n,start,end,actors,**kw):return ev(code,title,n,start,end,actors,year=None,when='背景或追叙；本句确年日未载',**kw)
E=ev('hanzhu_dies','朔方节度使韩洙去世',28,'初，','韩洙卒，',[('洙','去世的朔方节度使')],when='主书初追叙；新韩氏传记天成四年（929），确日未载',place='朔方',note='主初不独具年，新韩氏传明确天成四年作为纪年补证；不猜具体月份或死因。')
claim('event',E,'time_original','新韩氏传将韩洙卒系天成四年。',28,'天成四年，洙卒，','依补书929纪年，不当主十月丁酉死亡日。',source=han,relation='adds')
E=ev('hancheng_interim_shuofang','韩洙卒后，韩澄为朔方留后',28,'弟澄','弟澄为留后。',[('澄','接任留后者')],when='韩洙天成四年卒后；确日未载',place='朔方',note='主与新康福传称弟，新韩氏传称子，亲属冲突先作事实引用，不建确定父亲或弟弟边；留后非正式节度使全称。')
claim('person',people['韩澄'],'description','新韩氏传称韩澄为韩洙之子，而主书及新康福传称弟。',28,'即以洙子澄為朔方軍留後。','同书内部亲属口径也有差，保留未定，不据单句构建两套相互冲突亲属关系。',source=han,relation='conflicts')
claim('person',people['韩澄'],'description','新康福传称韩洙死、其弟澄立。',28,'靈武韓洙死，其弟澄立，','与主弟同口径，但与新韩氏传子不同，纸本待核。',source=kf,relation='corroborates')
E=past('likuangbin_rebels_baojing','定远军使李匡宾聚党据保静镇作乱，朔方不安',28,'未几，','朔方不安；',[('李匡宾','据保静镇作乱的定远军使')],place='保静镇、朔方',note='未几为韩洙卒及韩澄立后的相对次序，主未独定作乱日；李匡宾主规范，新康作李从宾、新韩作李宾未直接合正式别名或造第二次叛乱。')
claim('event',E,'description','新康福传称同一请帅背景为偏将李从宾作乱。',28,'而偏將李從賓作亂。','主定远军使李匡宾与新李从宾职名和人名差保留，暂对应同案补证，不外推其他同名人物身份。',source=kf,relation='conflicts')
claim('event',E,'description','新韩氏传记其将李宾作乱。',28,'其將李賓作亂，','李宾与李匡宾、李从宾差不等单纯繁简转换；定位同案但不增确定告发或亲属。',source=han,relation='conflicts')
E=ev('hancheng_asks_court_commander','韩澄遣使持绢表，请朝廷任命朔方主帅',28,'冬，十月，丁酉','乞朝廷命帅。',[('澄','上表请帅者')],when='929年十月丁酉',place='朔方至后唐朝廷',note='使者未名；请帅不等当天康福已经到镇。')
E=past('kangfu_answers_emperor_hu_language','李嗣源常召康福入便殿问时事，康福以胡语回答',28,'前磁州刺史','福以胡语对；',[('帝','召问时事者'),('福','善胡语、以胡语答者')],note='多召为往事习惯，未具每次年月，不作为929新任磁州刺史；胡语未明确语言种类。')
claim('event',E,'description','新康福传同记福善诸戎语，明宗召入便殿访外事，福以蕃语答。',28,'善諸戎語，明宗嘗召入便殿，訪以外事，福輒為蕃語以對。','新诸戎语、蕃语与主胡语称法并存，不据此定民族血统。',source=court,relation='corroborates')
E=past('anchonghui_threatens_kangfu','安重诲厌康福，常以妄奏将被斩警告他',28,'安重诲恶之','会当斩汝！”',[('重诲','发出警告者'),('福','被警告者')],note='会当斩为威胁，不记录康福已被杀或已判死。')
E=past('kangfu_requests_external_post','康福惧安重诲警告，请求外任',28,'福惧，','求外补。',[('福','请求外任者')],note='惧因果为史述，求外补不等已取得特定军镇。')
claim('event',E,'description','新康福传同记安重诲威胁，福惧而求外任。',28,'樞密使安重誨惡之，常戒福曰：「無妄奏事，當斬汝！」福懼，求外任。','威胁未实际斩，求任与授任分录。',source=court,relation='corroborates')
E=ev('kangfu_appointed_shuofang_hexi','后唐授康福朔方、河西节度使',28,'重诲以灵州','以福为朔方、河西节度使。',[('福','获任朔方河西节度使'),('重诲','主导此任命者')],when='929年十月戊戌',place='朔方、河西',note='灵州深入胡境、帅多遇害是安的判断，不推每位帅都死；授任非康福已到灵州。')
claim('event',E,'description','旧明宗纪十月戊戌补康福原襄州兵马都监、守磁州刺史，并授灵威雄警凉等州观察使。',28,'戊戌，以襄州兵馬都監、守磁州刺史康福為朔方、河西等節度使，靈、威、雄、警、涼等州觀察使。','补原职和兼观察辖区，与主前磁州称法不同不改旧原字；不造逐州新任刺史。',source=oct,relation='adds')
E=ev('kangfu_tearfully_refuses_shuofang','康福见李嗣源，哭辞朔方任命',28,'福见上，','涕泣辞之；',[('福','哭辞任命者'),('帝','接受陈诉者')],when='929年十月戊戌任命后；确日未载',note='辞是请求，未表示任命最终撤销。')
E=ev('emperor_orders_kangfu_post_changed','李嗣源命安重诲为康福更换他镇',28,'上命重诲','为福更他镇，',[('帝','要求更换者'),('重诲','受命更换者'),('福','拟更镇对象')],when='929年十月任命后；确日未载',note='是皇帝要求，后安拒，不能写已成功移任他镇。')
E=ev('anchonghui_refuses_kangfu_transfer','安重诲以康福无功建节、成命已行为由拒绝换镇',28,'重诲曰：“福自','难以复改。”',[('重诲','拒绝换镇者'),('福','被拒更镇者')],when='929年十月任命后；确日未载',note='无功为安发言，不等本人物从未任何功劳；成命难改为其理由。')
E=ev('emperor_disclaims_kangfu_post_choice','李嗣源对康福称安重诲不肯换镇，并非己意',28,'上不得已','非朕意也。”',[('帝','向康福解释者'),('福','受解释者')],when='929年十月任命后；确日未载',note='非朕意为帝说法，任命仍执行；不把此事推为皇帝完全无行政权。')
claim('event',E,'description','新康福传同记明宗称重诲遣汝非吾意，许遣兵护送；新另称明宗怒。',28,'明宗怒，謂福曰：「重誨遣汝，非吾意也。吾當遣兵護汝，可無憂。」','帝怒补叙与主不得已概括不同，均保留，不更改客观任命结果。',source=kf,relation='adds')
E=ev('kangfu_escorted_ten_thousand','康福辞行，李嗣源遣牛知柔、卫审𡷣等率兵万人护送',28,'福辞行，','将兵万人卫送之。',[('帝','遣护送兵者'),('福','赴镇受护送者'),('牛知柔','率护送兵的将军'),('卫审𡷣','河中都指挥使、率护送兵者')],when='929年十月赴镇；确日未载',place='后唐至朔方',note='万人为共同兵额，不是二将各万人。底本姓名卫审私用区符号余，参考同卷电子平行文本作衛審𡷣规范显示；原摘录不改，不与梁将卫审符或旧審餘径合，详字形校核记录。')
claim('person',people['卫审𡷣'],'description','本段称卫审𡷣为徐州人。',28,'审\ue4c1余，徐州人也。','底本字形保留；展示字𡷣为同卷电子平行文本对照，纸本尚待核，不抹去罕见字。')
claim('event',E,'description','旧明宗纪记诏康福率兵万人赴镇。',28,'詔新授朔方節度使康福將兵萬人赴鎮。','支持兵额，句承癸卯段但未独日，主也无护送确日不强定戊戌同日。',source=oct,relation='corroborates')
claim('event',E,'description','新康福传明确将军牛知柔以兵护福。',28,'乃令將軍牛知柔以兵衞福。','新省略卫将和兵额不算否认主，未把下一段方渠战提前录入本批。',source=kf,relation='corroborates')
E=ev('baoning_army_established','后唐割阆、果二州置保宁军',29,'辛亥，','置保宁军，',[],when='929年十月辛亥',place='阆州、果州',note='调整军镇，不将两州视为当天新建城池；旧只升阆州口径保留，果州由主明载。')
claim('event',E,'description','旧明宗纪同日称升阆州为保宁军。',29,'辛亥，升閬州為保寧軍。','同日军镇设立不同详略，新主补辖果州，不补现代地理边界。',source=oct,relation='corroborates')
E=ev('lirenju_appointed_baoning','后唐以李仁矩为保宁军节度使',29,'壬子，',None,[('仁矩','内客省使、获保宁军节度任者')],when='929年十月壬子',place='保宁军、阆州',note='军名承上句，不跟此前五月传诏出使重复；新董段后姚洪千人等留后相应主段补。')
claim('event',E,'description','旧明宗纪补李仁矩左卫大将军衔，记为阆州节度使。',29,'壬子，以內客省使、左衛大將軍李仁矩為閬州節度使。','阆州节度与保宁军称法同地官职，未另造一日两镇任命。',source=oct,relation='adds')
claim('event',E,'description','新董璋传记分阆州置保宁军，以仁矩为节度使。',29,'又分閬州置保寧軍，以仁矩為節度使，','新只阆州略述，不以之覆盖主阆果；后续军谋留相应主段。',source=dong,relation='corroborates')
E=past('sichuan_supplies_xialu_background','西川此前常发草料粮食供给峡路',30,'先是，','西川常发刍粮馈峡路，',[],place='西川至峡路',note='常发是既往供给习惯，没有具体粮额、运输批次或军名。')
E=past('mengzhixiang_asks_stop_xialu_supplies','孟知祥以本镇兵多、难奉他镇为由请免峡路馈粮',30,'孟知祥辞','难以奉它镇，',[('知祥','提出免馈理由者')],place='西川',note='兵多及困难是孟所陈理由，不等已完成财力审计；请辞非获免。')
E=past('court_rejects_stop_supplies_demands','朝廷不许免馈粮，多次催督西川',30,'诏不许，','屡督之；',[],place='后唐对西川',note='屡督没有具体次数，不构造几次独立诏令及匿名督使。')
E=ev('mengzhixiang_refuses_supply_edict','孟知祥上奏称财力不足，不奉馈粮诏',30,'甲寅，',None,[('知祥','奏称财乏、不奉诏者')],when='929年十月甲寅',place='西川至后唐',note='此句确年承十月，拒诏为实际行为；不等当日已宣布独立、已与董起兵。')
E=past('xu_brothers_rivalry_background','徐知询握兵据上流，轻徐知诰，二人屡争权并相猜忌',31,'吴诸道','知诰患之，',[('知询','镇海宁国节度、握兵争权者'),('知诰','遭轻、争权对象')],place='吴',note='节使底本疑节度使略或脱字留原；徐知诰沿李昪同人，此为十一月入朝前背景，不强每次都929十一月。')
E=past('wanglingmou_advises_xuzhigao','王令谋对徐知诰称其辅政日久、可挟天子令境内，认为徐知询恩信未洽',31,'内枢密使王令谋','无能为也。”',[('王令谋','内枢密使、进言者'),('知诰','受进言者'),('知询','进言评价对象')],note='谁敢不从及无能为是王评语，不当现代民心统计或已实施全部政治措施。')
E=past('xuzhixun_treats_brothers_thinly','徐知询待诸弟薄，诸弟怨之',31,'知询待诸弟','诸弟皆怨之。',[('知询','薄待诸弟者')],note='诸弟没有逐个实名，不据前人物列表推每一人均在场；仅保留史述，不增一组敌对关系。')
E=past('xujie_switches_support','徐玠认为徐知询不可辅，转持其短依附徐知诰',31,'徐玠知','以附知诰。',[('徐玠','转附、指陈短处者'),('知询','被指短者'),('知诰','受附者')],note='徐玠原辅知询的背景与本转向分，不泛化为永远盟友或敌人关系。')
E=past('qianliu_gives_xuzhixun_dragon_items','钱镠赠徐知询饰龙凤的金玉鞍勒、器皿',31,'吴越王镠','皆饰以龙凤；',[('镠','赠物者'),('知询','受赠者')],note='物装饰不等吴越授帝位，未具件数与价值；此句后使用在分段下一快照，不跨快照拼摘录。')
E=past('xuzhixun_uses_dragon_items','徐知询不避嫌，乘用所获龙凤饰物',31,'知询不以','乘用之。',[('知询','使用龙凤饰物者')],note='承前钱赠，非新建宫殿或已经称帝。')
E=past('zhoutingwang_advises_gifts','典客周廷望劝徐知询以宝物结朝中勋旧',31,'知询典客','则彼谁与处！”',[('廷望','提出结交方案的典客'),('知询','受劝者')],note='公诚能为条件建议，不证明已将全部宝物分完、所有勋旧归心。')
E=past('xuzhixun_sends_zhoutingwang','徐知询从周廷望言，遣其赴江都传意',31,'知询从之','如江都谕意。',[('知询','遣传意者'),('廷望','赴江都传意者')],place='金陵至江都',note='谕意未具给各人礼物清单，不能写已完成收买所有官员。')
E=past('zhoutingwang_secretly_informs_both','周廷望与周宗相善，密向徐知诰输款，又向徐知询告知徐知诰阴谋',31,'廷望与','阴谋告知询。',[('廷望','向两方传消息者'),('周宗','徐知诰亲吏、周的交好对象'),('知诰','受密告者'),('知询','受转告者')],note='相善不自动生成终身盟友，阴谋为主书称法未具内容，不猜暗杀计划。')
E=past('xuzhixun_invites_mourning','徐知询召徐知诰赴金陵除徐温丧，徐知诰称吴主不许',31,'知询召','吴主之命不许，',[('知询','召行除父丧者'),('知诰','以吴主命为由不往者')],place='金陵、吴',note='召为请求未实际会面；父温为既往已亡，不新造929徐温去世。吴主之命为徐所称，未独证杨溥另有同日诏。')
E=past('zhouzong_warns_seven_accusations','周宗向周廷望转称徐知询被指有不臣七事，劝其入朝谢罪',31,'周宗谓','宜亟入谢！”',[('周宗','转称指控并劝入谢者'),('廷望','受传话者'),('知询','话中被指者')],note='人言是不具名指控，七事未列；不当徐已犯七项确证罪名。')
E=past('zhoutingwang_reports_warning','周廷望返回，将周宗言告徐知询',31,'廷望还，','以告知询。',[('廷望','回告者'),('知询','获告者')],place='江都至金陵',note='前话转告与入朝执行分，不补返程日期。')
E=ev('xuzhixun_enters_wu_court','徐知询入吴朝',31,'十一月，','知询入朝，',[('知询','从金陵入朝者')],when='929年十一月',place='金陵至江都',note='原未载日，不把随后壬辰一概倒赋全部动作。')
claim('event',E,'time_original','新吴世家同记三年十一月金陵尹徐知询来朝。',31,'三年十一月，金陵尹徐知詢來朝，','本书三年承乾贞，依相邻二年段及原前文纪年回查对应929；不当长兴三年932。',source=wu,relation='corroborates')
E=ev('xuzhigao_detains_xuzhixun_assigns_command','徐知诰留徐知询为统军，领镇海节度使',31,'知诰留','领镇海节度使，',[('知诰','留任安排者'),('知询','被留为统军、仍领镇海者')],when='929年十一月入朝后；确日未载',place='江都',note='领镇海与军实际被征回分，不写所有职衔一律撤销；不是徐知诰自己新领镇海。')
claim('event',E,'description','新吴世家称徐知诰诬其有反状，留之不遣，任为左统军。',31,'知誥誣其有反狀，留之不遣，以為左統軍，','诬为本书明示，不作为徐知询实际谋反事实；左统军补主统军，不造二次任。',source=wu,relation='adds')
E=ev('kehou_recalls_jinling_troops','徐知诰遣柯厚征金陵兵还江都',31,'遣右雄武','征金陵兵还江都，',[('知诰','命收回金陵兵者'),('柯厚','右雄武都指挥使、执行者')],when='929年十一月',place='金陵至江都',note='未具兵数，不与前二千李简亲兵等同或全部金陵居民被迁。')
E=ev('xuzhigao_exclusive_wu_power','金陵兵征回后，徐知诰开始独专吴政',31,'知诰自是','始专吴政。',[('知诰','开始独专政者')],when='929年十一月金陵兵征回后',place='吴',note='始专政为主述实际权力集中，不提前称南唐皇帝或吴已亡。')
E=ev('xu_brothers_exchange_accusations','徐知询责兄不临父丧，徐知诰反问其挺剑待己和畜乘舆服物',31,'知询责','亦可乎！”',[('知询','责兄未临丧者'),('知诰','答称不敢往、反责服物者')],when='929年十一月入朝后；确日未载',note='挺剑待我为徐知诰说法，不造已发生刺杀事件；兄弟为发言用称，收养背景已有，不重建血缘兄长关系。')
E=ev('xu_brothers_expose_zhoutingwang','徐知询述周廷望所言，徐知诰揭周也向己告知徐知询所为',31,'知询又以','亦廷望也。”',[('知询','提周传话者'),('知诰','揭周两面传话者'),('廷望','被双方揭出消息来源者')],when='929年十一月入朝后；确日未载',note='本句主诰知诰疑告字，摘录留原，展示述告；不把周两面传话改为正式谍官任命。')
E=ev('zhoutingwang_executed','徐知诰遂斩周廷望',31,'遂斩廷望。',None,[('知诰','下令斩周者'),('廷望','被斩者')],when='929年十一月入朝后；确日未载',note='主句前行为主语知诰，新亦接知诰留之斩其客将，支持归责；未记行刑者姓名。')
claim('event',E,'description','新吴世家同记斩徐知询客将周廷望。',31,'斬其客將周廷望。','主典客、新客将职称口径均保留，未径称周正式都指挥使或造两次死亡。',source=wu,relation='corroborates')
E=ev('yangpu_honorific_amnesty_taihe','吴主杨溥加睿圣文明光孝皇帝尊号，大赦，改元大和',32,'壬辰，',None,[('吴主','加尊号、赦、改元者')],when='929年十一月壬辰',place='吴',note='改元大和保留本字，不自动改太和；加尊号不同927初称帝，不第二次即位。')
claim('event',E,'description','新吴世家同记加尊号、大赦境内、改元大和，尊号作睿圣文明孝皇帝。',32,'溥加尊號睿聖文明孝皇帝，大赦境內，改元大和，','新尊号少光字，与主有光存异，不改变主字段或推两个不同帝号；新同段中书令另在主十二月留下一批处理。',source=wu,relation='conflicts')
review='卷276连续929年第28—32段、原114—118行。繁简仅规范展示，摘录原字。韩洙卒主初，新韩氏明确天成4支持929年但不赋十月日；韩澄留后主和新康弟、新韩子冲突，不建确定亲属边。李匡宾主与新康李从宾、新韩李宾同案名异，暂不合正式别名或新建两叛。康福便殿胡语、安威胁、求外任为背景年null；胡语不定民族，威胁非已斩。十月丁酉请帅、戊戌授、哭辞、帝令更镇安拒、帝称非己意、万人护送分，未写成功换镇。牛卫共万人非各万人，卫原私用字经同卷电子平行对照暂规范卫审𡷣，不与卫审符、旧卫审余直接混；徐州籍有主明确，纸本待核。新康后方渠峡战留下一主段。辛亥保宁阆果、壬子仁矩授与旧升阆州、左卫大将军补相应，不造两次授。西川常供峡路、请辞被拒催督前事null，甲寅奏称财乏不奉诏不是已起兵。吴徐争权及周计礼父丧背景null，王挟天子无能为是判断，诸弟不猜具体名单，钱赠龙凤非封帝，周宝物建议不证明已收买全部朝臣。周双告及与周宗善不建永盟；七不臣为人言非实罪，吴主不许为徐所称。十一月入朝、留统军仍领镇海、柯厚征兵、徐专政与兄弟指责周暴露斩分。新知诰诬反明归本书记述，不当知询确谋反；新左统军和客将补口径。主诰知诰疑告保留不悄改源；徐知诰沿李昪，不新同人。壬辰吴加号赦改大和非927重即位，新尊号少光异文留；新同段中书令提前概记而主十二月，留下一批。选定新卷40校勘注p001457也指出洙子澄恐误，并引新康和薛史弟说，已导出为编校上下文而非独立本传正文；暂不据注替换原传或补亲属边。第33—36段仍pending，全年未完成。'
contexts=[json.loads((P/'sources/wei-shenyu-glyph-review.json').read_text()),json.loads((P/'sources/editorial/hancheng-kinship-note/context.json').read_text())]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(28,33):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=929,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(28,33)],next_paragraph='zztj-v276-y0929-p033',next_volume=276,next_year=929,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续929年第28—32段、原114—118行；朔方请帅康福赴镇、保宁设军、西川馈粮与吴徐争权改元。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(28,33)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
