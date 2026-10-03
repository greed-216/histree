# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 929, paragraphs 9–16."""
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
 ('tongjian-276-929-spring-summer',P/'sources/library/tongjian-276-929-spring-summer','04953b74','司马光等'),
 ('jiuwudaishi-040-929-april',P/'sources/library/jiuwudaishi-040-929-april','04953b74','薛居正等'),
 ('jiuwudaishi-040-929-may',P/'sources/library/jiuwudaishi-040-929-may','04953b74','薛居正等'),
 ('xinwudaishi-066-maxisheng',P/'sources/library/xinwudaishi-066-maxisheng','04953b74','欧阳修'),
 ('xinwudaishi-015-congrong-offices',P/'sources/library/xinwudaishi-015-congrong-offices','88412ac4','欧阳修'),
 ('xinwudaishi-066-chu-offices',YEAR.parent/'year-0927/part-02/sources/library/xinwudaishi-066-chu-offices','e2f62270','欧阳修'),
 ('xinwudaishi-006-929',YEAR/'part-01/sources/library/xinwudaishi-006-929','ea985438','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-929-spring-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0929-p009-p016',
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
for n in range(9, 17):
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
    ck = f'claim_zztj_276_0929_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'殷':'马殷','希声':'马希声','从荣':'李从荣','从厚':'李从厚','哀帝':'李祚','帝':'李嗣源','梅里':'捺括梅里'}
NEW_ALIASES={'马希声':['馬希聲'],'捺括梅里':['捺括梅裏','撩括梅里']}

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
    if when is None:when='929年'+('三月' if n==9 else '四月' if n<=15 else '五月')+'本段；确日未载'
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
a='jiuwudaishi-040-929-april';may='jiuwudaishi-040-929-may';ms='xinwudaishi-066-maxisheng';chu='xinwudaishi-066-chu-offices';ann='xinwudaishi-006-929';co='xinwudaishi-015-congrong-offices'
E=ev('maxisheng_assigned_political_military_affairs','马殷命马希声知政事，总录内外军事',9,'楚王','诸军事，',[('殷','楚王、委子知政者'),('希声','武安节度副使判长沙府、获委知政总军者')],place='楚、长沙',note='知政和总军不是继王位，马殷仍在，未提前其卒与希声继立。')
relationship('殷','希声','父亲',9,span(9,'楚王','诸军事，'),'原其子希声明父关系，马殷→马希声，不与陆希声同名合并；不建反向儿子重复。')
claim('person',people['马希声'],'description','新楚世家记马希声字若讷，为马殷次子。',9,'希聲字若訥，殷次子也。','补字与次子身份，未由次子补推其他未明兄弟；新传后文高郁案留待主线下一批。',source=ms)
claim('event',E,'description','新楚世家记马殷建国时已以次子希声判内外诸军事。',9,'殷以潭州為長沙府，建國承制，自置官屬，以其弟賨為靜江軍節度使，子希振武順軍節度使，次子希聲判內外諸軍事，','复用927楚建国出处，判军为此前职务背景，主929知政总军为本次委托，不强两段一定是同一次授官，也不重录927建国。',source=chu,relation='adds')
E=ev('chu_affairs_first_processed_maxisheng','此后楚国政事先由马希声处理，才上报马殷',9,'自是',None,[('希声','先处理国政者'),('殷','听取其后报告者')],place='楚',note='自是叙述处理顺序的改变，不等马殷完全失权或不再知任何政事。')
E=ev('ban_iron_tin_coins','后唐禁铁锡钱',10,'夏','禁铁锡钱。',[],when='929年四月庚子朔',place='后唐',note='币材禁令不扩大为废除所有钱币；旧铁鑞钱与主铁锡钱材字不同，保留异文不把鑞繁简成锡。')
claim('event',E,'description','旧明宗纪同月庚子朔记禁铁镴钱（底本作鑞）。',10,'夏四月庚子朔，禁鐵鑞錢。','鑞简体镴，非锡的繁体；标题循主铁锡，旧材字异说保留，不静默改原字。',source=a,relation='conflicts')
E=ev('hunan_tin_currency_copper_ratio','当时湖南专用锡钱，铜钱一枚值锡钱百枚',10,'时湖南','锡钱百，',[],place='湖南',note='一直为价值相当之意；一比百是史载钱值，未转现代汇率、金属含量或币重；时背景无独始年，本文年条显示当时状态。')
E=ev('tin_coins_flow_central_area_despite_ban','湖南锡钱流入中原，禁法难以阻止',10,'流入',None,[],place='湖南至中原',note='中国按此时代文义作中原，不套现代国界或跨境法规；不能由法不能禁猜特定官员走私。')
E=ev('wanghuan_defeats_jingnan_shishou','楚六军副使王环在石首击败荆南军',11,'丙午',None,[('王环','楚六军副使、击败荆南军者')],when='929年四月丙午',place='石首',note='复用楚将王环，不与后蜀同名将合并；未具荆南直接将名、兵数和死伤，不猜高从诲亲战。')
claim('event',E,'description','旧明宗纪同月记湖南奏在石首镇败荆南军。',11,'湖南奏，敗荊南賊軍於石首鎮。','旧奏报没有独记本句日，前壬寅殿成项不强赋战日；贼军是旧称，展示为荆南军。',source=a,relation='corroborates')
E=ev('border_markets_buy_dangxiang_horses','朝廷首次令边境置马市，购买党项马，不许其直接赴阙',12,'初令','不令诣阙。',[],place='后唐边境',note='初令意首次下新政策，不是初字追叙；四月承前同月，确日未独载；置场命令非所有场已建成，未猜场名坐标。')
claim('event',E,'description','旧明宗纪同记诏沿边置场买马，不许蕃部直至阙下。',12,'詔沿邊置場買馬，不許蕃部直至闕下。','政策互证，不扩成完全停止买马或所有党项朝贡禁绝。',source=a,relation='corroborates')
E=ev('prior_dangxiang_tribute_horses_paid_lodged_rewarded','此前党项赴阙以贡马为名，朝廷按价酬付并给予馆食、赏赐',12,'先是','馆谷赐与，',[],year=None,when='先是：四月置马市政策之前，始年日未独载',place='党项至阙下',note='是旧制度追叙，不强928或929新发生一次进贡；按价酬马与额外供食赏赐分别解释。')
claim('event',E,'description','旧明宗纪补党项来马不论驽良皆称进贡，国家按价给付并负担馆谷锡赉。',12,'先是，党項諸蕃凡將到馬，無駑良並雲上進，國家雖約其價以給之，及計其館穀錫賚，所費不可勝紀。','锡赉为赏赐用词，不把锡字当给锡钱材料；云进贡是所称身份不等所有马皆良马。',source=a,relation='adds')
E=ev('prior_annual_horse_visit_cost','主书记上述赴阙买马接待旧制每年花费五十余万缗',12,'岁费','五十馀万缗。',[],year=None,when='先是旧制度的年度开支概数；具体预算年度未独载',place='后唐财政',note='为史载岁费，不错成买马单价、每次使团费或本年单独账目；不换现代币值。')
E=ev('officials_stop_direct_horse_visits_cost','有司以旧制费用耗蠹为苦，故停止直接赴阙买马方式',12,'有司',None,[],note='止之承旧直接赴阙方式，新仍边市买马；主有司旧计司，未具官员名，不造人及现代财务测算结论。')
E=ev('licongrong_henan_and_six_guards','李从荣任河南尹、判六军诸卫事',13,'壬子','诸卫事，',[('从荣','河南尹、判六军诸卫事获任者')],when='929年四月壬子',place='河南府',note='新唐家人传系长兴元年即930，保留任职纪年分歧，不新增另一次任命或提前秦王封号。')
claim('event',E,'description','旧明宗纪同日记李从荣由北京留守、河东节度使任河南尹，判六军诸卫事。',13,'壬子，以皇子北京留守、河東節度使從榮為河南尹，判六軍諸衛事；','旧主当年同日互证，从荣与从厚任职对象不交换写错。',source=a,relation='corroborates')
claim('event',E,'time_original','新唐家人传将李从荣拜河南尹、兼判六军诸卫事系于长兴元年。',13,'長興元年，拜河南尹，兼判六軍諸衞事。','长兴元年为930，与主旧929四月相差年；原段秦王为后爵回称，不写929已封秦王；电子底本待纸本核。',source=co,relation='conflicts')
E=ev('liconghou_hedong_northern_capital','李从厚任河东节度使、北都留守',13,'从厚',None,[('从厚','河东节度、北都留守获任者')],when='929年四月壬子',place='河东、北都',note='主任命承壬子，北都当时太原，不推现代坐标；并非从荣仍留河东兼任此两职。')
claim('event',E,'description','旧明宗纪同项记皇子李从厚为北京留守，称其原河南尹、判六军诸卫事。',13,'以皇子河南尹、判六軍諸衛事從厚為北京留守；','主同时明河东节度，旧略；旧原河南尹与此前宣武职叙法并列，不据此另造取消宣武职事件。',source=a,relation='adds')
E=ev('khitan_attacks_yunzhou_april','契丹侵扰云州',14,'契丹',None,[],place='云州',note='本次四月条与后五月再次云州记分开，不提前后一段或猜将名死伤；旧同月寇云州互证。')
claim('event',E,'description','旧明宗纪四月同记契丹寇云州。',14,'契丹寇雲州。','原文月内位置在壬子后，未独具确日，不强壬子当天。',source=a,relation='corroborates')
E=event('khitan_envoy_nakuomeili_requests_bones','旧明宗纪补契丹遣捺括梅里等来朝贡，称取秃馁等骸骨',14,'癸丑，契丹遣捺括梅裏等來朝貢，稱取禿餒等骸骨，',[('梅里','契丹来使、请求骸骨者')],source=a,when='929年四月癸丑',place='后唐朝廷',note='独立补证同月外交，不造与云州战事的必然因果；请求不等已交还骸骨，等从者未名不造实体。')
claim('person',people['捺括梅里'],'description','新明宗纪同日将该契丹使写为撩括梅里，记其来求秃馁。',14,'癸丑，契丹使撩括梅里來求禿餒，殺之。','同日同案匹配捺括/撩括姓名异写，保留来源；旧取骸骨与新求秃馁不同表述，新杀之省略宾语不独释为明确取人或杀使。',source=ann,relation='conflicts')
E=event('nakuomeili_envoy_group_executed','旧明宗纪记捺括梅里等契丹使被斩于北市',14,'癸丑，契丹遣捺括梅裏等來朝貢，稱取禿餒等骸骨，並斬於北市。',[('梅里','被处死契丹使者')],source=a,when='929年四月癸丑',place='北市',note='依旧并斩承梅里等使者记录；与二月秃馁处刑不同，不新增秃馁第二次死亡。新杀之所指简略，原引并列不借其再证所有对象。')
E=ev('zhaofeng_chancellor','赵凤任门下侍郎、同平章事',15,'甲寅',None,[('赵凤','由端明殿学士兵部侍郎任宰相者')],when='929年四月甲寅',place='后唐朝廷',note='任相及门下官，不推成为枢密使；补衔工部尚书与主列衔详略保留。')
claim('event',E,'description','新明宗纪同日记赵凤门下侍郎兼工部尚书、同中书门下平章事。',15,'甲寅，端明殿學士、尚書兵部侍郎趙鳳為門下侍郎兼工部尚書、同中書門下平章事。','补兼工部尚书与全称同平章，主旧新同日，不当先后两次任相。',source=ann,relation='adds')
E=ev('taichang_proposes_aidi_title_jingzong','太常为唐哀帝改谥昭宣光烈孝皇帝，定庙号景宗',16,'太常','庙号景宗。',[('哀帝','唐哀帝、所议谥号庙号对象')],year=None,when='929年五月乙酉中书奏议所述太常定号；原议确年日未独载',place='后唐朝廷',note='哀帝沿李祚主体，景宗非另一人；日疑曰字底本保留，不把景宗号已最终确定强写。')
E=ev('zhongshu_questions_aidi_temple_name','中书指出称宗应入太庙，在别庙则不应称宗',16,'五月','不应称宗。”',[],when='929年五月乙酉',place='后唐朝廷',note='为中书制度意见，不是哀帝本朝当政所颁诏；别庙来自此前立庙背景，不补新入太庙。')
E=ev('aidi_jingzong_temple_name_removed','朝廷去除唐哀帝景宗庙号',16,'乃去',None,[],when='929年五月乙酉',place='后唐朝廷',note='取消是庙号而非谥号或曹州庙，不能写取消所有身后尊称。')
claim('event',E,'description','旧明宗纪同月载太常定少帝谥昭宣光烈孝皇帝、景宗庙号，中书以不入庙请仅保留谥号，朝廷从之。',16,'中書奏：「太常寺定少帝諡昭宣光烈孝皇帝，廟號景宗。伏以少帝今不入廟，難以言宗，隻雲昭宣光烈孝皇帝。」從之。','旧少帝与主哀帝同人；本句列乙酉任命后未独加日，乙酉据主，保留谥号不再建第二被尊人物。',source=may,relation='corroborates')
review='卷276连续929年第9—16段、原95—102行。马希声新主体与陆希声别，父马殷明确；主知政总军、国政先历后闻分，未提前继王位。新字若讷次子补，927建国判军职为旧背景不强与929知政同一次任命；高郁后事待主下一段。四月庚子禁铁锡，旧铁鑞材字非锡繁简，异文保留；湖南专锡、铜1直锡100为史载值不现代汇率，锡流中国作中原，禁法难禁不猜官吏走私。丙午楚王环石首败荆南，楚将沿已有不混后蜀王环，旧湖南奏无独日不强前壬寅战日。初令边场买马为本次新政策；先是党项贡名酬价馆谷赐旧制及岁50余万年null，不当单次马价或929独账；有司停直接赴阙，不等全面禁止购马或所有朝贡，旧锡赉为赏赐非锡币。壬子从荣河南六卫、从厚河东北都分，旧当年同日互证，新从荣传长兴元年930不同年并列，秦王后爵回称不提前封王；旧从厚原河南尹与此前宣武叙法并存不补取消职。四月云州寇不同五月再寇，不猜统将人数。独補同月癸丑捺括梅里等使朝贡请求秃馁骨，旧并斩北市，非新让主明载外交或再杀秃馁；新名撩括梅里同案匹配，求秃馁与取骸骨叙法不同，新杀之省略所指不独确定杀使证明。甲寅赵相、新兼工部尚书详衔补不造第二授相。五月乙酉太常定谥和景宗提案、中书庙制意见、去庙号分，哀帝李祚同人不新建景宗，日疑曰字原留；谥保留别庙未毁未入太庙。展示简体原TXT逐字定位不改；纸本异文待核；未读源快照后续诸段不算完成。'
review=review.replace('独補','独补')
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=929,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph='zztj-v276-y0929-p017',next_volume=276,next_year=929,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续929年第9—16段、原95—102行；楚知政、币禁、石首战、党项马市、两皇子官调、云州寇与使、赵相及哀帝号议。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(9,17)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
