# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 7–12."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 68))
specs=[
 ('tongjian-275-926-accession',P/'sources/library/tongjian-275-926-accession','5c38857d','司马光等'),
 ('jiuwudaishi-036-926-accession',P/'sources/library/jiuwudaishi-036-926-accession','5c38857d','薛居正等'),
 ('jiuwudaishi-036-926-may-offices',P/'sources/library/jiuwudaishi-036-926-may-offices','5c38857d','薛居正等'),
 ('jiuwudaishi-036-926-may-army',P/'sources/library/jiuwudaishi-036-926-may-army','5c38857d','薛居正等'),
 ('xinwudaishi-006-926-may-offices',P/'sources/library/xinwudaishi-006-926-may-offices','5c38857d','欧阳修'),
 ('xinwudaishi-028-renhuan-finance',P/'sources/library/xinwudaishi-028-renhuan-finance','5c38857d','欧阳修'),
 ('xinwudaishi-047-changcongjian',P/'sources/library/xinwudaishi-047-changcongjian','5c38857d','欧阳修'),
 ('xinwudaishi-046-wangyanqiu-family',P/'sources/library/xinwudaishi-046-wangyanqiu-family','5c38857d','欧阳修'),
 ('xinwudaishi-015-mingzong-nephews',P/'sources/library/xinwudaishi-015-mingzong-nephews','5c38857d','欧阳修'),
 ('xinwudaishi-028-zhangxian-critique',P/'sources/library/xinwudaishi-028-zhangxian-critique','5c38857d','欧阳修'),
 ('jiuwudaishi-035-926-regency',YEAR/'part-01/sources/library/jiuwudaishi-035-926-regency','60d249b7','薛居正等'),
 ('jiuwudaishi-035-926-fiscal-and-yuan',YEAR/'part-02/sources/library/jiuwudaishi-035-926-fiscal-and-yuan','0c93a613','薛居正等'),
 ('xinwudaishi-006-926-regency',YEAR/'part-01/sources/library/xinwudaishi-006-926-regency','60d249b7','欧阳修'),
 ('xinwudaishi-014-926-jiji-death',YEAR/'part-02/sources/library/xinwudaishi-014-926-jiji-death','0c93a613','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p013-p024',
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
lines = (ROOT / 'resources/derived/tongjian/275.txt').read_text().splitlines()
for n in range(13, 25):
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
        citation = f'卷275·同光四年（926）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_275_0926_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','监国':'李嗣源','明宗':'李嗣源','庄宗':'李存勖','先帝':'李存勖','武皇':'李克用','献祖':'李国昌','李绍真':'霍彦威','李绍琼':'苌从简','李绍英':'房知温','李绍虔':'杜晏球','王晏球':'杜晏球','李绍奇':'夏鲁奇','李绍能':'米君立','李彦超':'符彦超','圜':'任圜','从温':'李从温','在礼':'赵在礼','金全':'安金全'}
NEW_ALIASES={'苌从简':['萇從簡','李绍琼','李紹瓊'],'米君立':['李绍能','李紹能'],'李从温':['李從溫']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷275同光四年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='926年本段；确日未载', note='', year=926, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_275_0926_' + code
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
        edge = 'participation_zztj_275_0926_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_275_0926_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('kongxun_privy_chief','监国任孔循为枢密使',13,'壬寅',None,[('监国','任命者'),('孔循','受任枢密使')],when='926年四月壬寅',place='洛阳',note='接续此前副使，此处才任正使；当时仍为监国。')
claim('event',E,'description','旧明宗纪也记壬寅由枢密副使孔循升枢密使。',13,'壬寅，以樞密副使孔循為樞密使。','正副职变化逐段录，不将前副职覆盖。',source='jiuwudaishi-035-926-fiscal-and-yuan',relation='corroborates')
E=ev('huyu_kong_propose_new_dynasty_name','霍彦威与孔循在即位礼讨论中提议新建国号',14,'有司议即位礼。','宜自建国号。',[('李绍真','提议者'),('孔循','提议者')],when='926年四月丙午即位前议礼，确日未载',place='洛阳',note='唐运已尽为两人意见；新国号未获采用，不造实际新朝成立。')
claim('event',E,'description','旧明宗纪同载霍彦威、孔循请改国号及德运。',14,'所司議即位儀注，霍彥威、孔循等言：「唐之運數已衰，不如自創新號。」因請改國號，不從土德。','独立保留旧史议礼话语，不把意见当最终国号。',source='jiuwudaishi-035-926-regency',relation='corroborates')
E=ev('siyuan_rejects_new_dynasty_name','李嗣源以曾事三世及基业相承为由，反对同家异国并令执政重议',14,'监国问左右','令执政更议。',[('监国','询问并反对更国号者'),('献祖','讲话所述早年所事者'),('武皇','讲话所述基业前主'),('先帝','讲话所述天下前主')],when='926年四月即位前议礼期间',place='洛阳',note='献祖李国昌、武皇李克用、先帝李存勖复用主体；事三十年二十年是讲话概数不倒推精确起始年。视吾犹子是待遇描述，不仅据此建养父关系。')
claim('event',E,'description','旧明宗纪亦载同宗不应异号的答复。',14,'且同宗異號，出何典禮？曆之衰隆，吾自當之，眾之莠言，吾無取也。','旧所载讲话只作为意见及理由，不据同宗推血缘。',source='jiuwudaishi-035-926-regency',relation='corroborates')
E=ev('liqi_proposes_coffin_succession','李琪主张保留唐号并采用嗣子柩前即位礼，议众接受',14,'吏部尚书李琪曰','众从之。',[('李琪','吏部尚书、议礼建议者'),('监国','议礼所指继位者')],when='926年四月丙午即位前',place='洛阳',note='嗣子为建议礼仪，不等证明李嗣源是李存勖亲生或收养之子。')
claim('event',E,'description','旧史也记李琪举唐代兄弟相继为例，主张柩前即位，群议始定。',14,'請以本朝言之，則睿宗、文宗、武宗皆以弟兄相繼，即位柩前，如儲後之儀可也。」於是群議始定。','所举先例是当时议礼意见，不据此为本段历史人物另建兄弟血缘。',source='jiuwudaishi-035-926-regency',relation='corroborates')
E=ev('siyuan_enthroned_before_coffin','李嗣源自兴圣宫赴西宫，穿斩衰在梓宫前正式即皇帝位',14,'丙午','百官缟素。',[('监国','正式即皇帝位者')],when='926年四月丙午',place='洛阳兴圣宫、西宫',note='与先前甲午受监国班见分开，正式即位保留唐国号。')
claim('event',E,'description','旧明宗纪同记丙午赴西宫、百官缟素及柩前即位。',14,'天成元年夏四月丙午，帝自興聖宮赴西宮，文武百僚縞素於位，帝服斬衰，親奉攢，塗設奠，哭盡哀，乃於柩前即皇帝位。','旧标题用天成回标本年；改元本身另录甲寅。',source='jiuwudaishi-036-926-accession',relation='corroborates')
claim('event',E,'description','新明宗纪也记丙午始奠于西宫。',14,'丙午，始奠于西宮，','正文与夹注分取，不跨夹注拼句。',source='xinwudaishi-006-926-regency',relation='corroborates')
E=ev('siyuan_receives_investiture','李嗣源改穿衮冕受册，百官改吉服称贺',14,'既而御衮冕',None,[('监国','受册皇帝')],when='926年四月丙午，柩前即位之后',place='洛阳西宫',note='分出由丧服到受册的顺序，不把百官缟素与吉服写成同一时刻。')
claim('event',E,'description','旧明宗纪亦记帝御衮冕受册、百官易吉服。',14,'百官易吉服班於位，帝御袞冕受冊訖，百僚稱賀。','两书同礼序补证。',source='jiuwudaishi-036-926-accession',relation='corroborates')
E=ev('siyuan_bans_hawks_curios','李嗣源敕中外臣不得献鹰犬奇玩',15,'戊申',None,[('帝','禁献敕令者')],when='926年四月戊申',place='后唐朝廷及中外诸臣',note='禁令不证此前每臣均有献或此后零违规。')
E=ev('zhangxian_accused_abandoning_taiyuan','有司弹劾太原尹张宪弃守城池',16,'有司劾奏','委城之罪；',[('张宪','被劾太原尹')],when='926年四月庚戌赐死之前，确日未载',place='太原、后唐朝廷',note='委城之罪是有司弹劾内容；与新史对弃城记述的疑议分存，不当无争议道德定论。')
E=ev('zhangxian_executed','张宪被赐死',16,'庚戌',None,[('张宪','被赐死者')],when='926年四月庚戌据主书',place='处决具体地点本段未载',note='主明确赐死；新张传出奔见杀及作者怀疑旧记载不改写主事实。')
claim('person',people['张宪'],'death_year','张宪于926年被赐死，据通鉴本段。',16,'庚戌，赐宪死。','具体处死方式和执行人未名，不补。')
claim('event',E,'description','旧明宗纪记该月张宪以失守故赐死。',16,'是月，北京副留守、知留守事張憲賜死，以其失守故也。','旧为是月概记，主庚戌各存。',source='jiuwudaishi-036-926-accession',relation='corroborates')
claim('event',E,'description','欧阳修对旧史“坐弃城而赐死”的记法表示怀疑，认为张宪死因记述不明。',16,'而舊史書憲坐棄城而賜死，予亦以為不然。','这是新史作者的史料批评，不据此反推确定的替代死因或宣布没有赐死。',source='xinwudaishi-028-zhangxian-critique',relation='conflicts')
E=ev('renhuan_returns_army_to_luoyang','任圜率征蜀兵二万六千至洛阳，明宗慰抚并令各还营',17,'任圜',None,[('圜','率返京征蜀军者'),('明宗','慰抚及令还营者')],when='926年四月主本段无确日；旧明宗纪记壬子入见',place='洛阳',note='主及旧二万六千，新魏王传二万，数量异说各引，不取中间数。还营命令不等逐营已经完成归建。')
claim('event',E,'description','旧明宗纪记壬子任圜率步骑二万六千入见。',17,'壬子，西南面副招討使、工部尚書任圜率步騎二萬六千人入見。','补副招讨使等职称和旧确日；主本段未具日。',source='jiuwudaishi-036-926-accession',relation='adds')
claim('event',E,'description','新魏王传记任圜率征蜀之师二万至京师，明宗抚慰。',17,'明宗已即位，圜率征蜀之師二萬至京師，明宗撫慰久之，','新二万与主二万六千不一致，保留各书计数；不声称精确数量已解决。',source='xinwudaishi-014-926-jiji-death',relation='conflicts')
E=ev('siyuan_amnesty_tiancheng','李嗣源大赦并改元天成',18,'甲寅','改元。',[('帝','大赦及改元者')],when='926年四月甲寅',place='后唐天下',note='主改元未写新年号，天成据旧明宗纪明确补证；不自行换算公历月日。')
claim('event',E,'description','旧明宗纪明确将同光四年改为天成元年。',18,'甲寅，帝御文明殿受朝。製改同光四年為天成元年，大赦天下。','据旧补年号，不改主原文。',source='jiuwudaishi-036-926-accession',relation='adds')
E=ev('siyuan_reduces_palace_staff','朝廷规定后宫、宦官、教坊、鹰坊、御厨留员数，余者任从所适',18,'量留后宫','自馀任从所适。',[('帝','留员及放散发令者')],when='926年四月甲寅政令',place='后唐宫廷',note='分别为后宫百人、宦官三十、教坊百、鹰坊二十、御厨五十；不据限额推此前各类人数或全员已放散。')
claim('event',E,'description','旧史同载五类宫廷留员限额及其他人任从所适。',18,'後宮內職量留一百人，內官三十人，教坊一百人，鷹坊二十人，禦廚五十人，其餘任從所適。','保留旧内职、内官称谓，非同一部门合数。',source='jiuwudaishi-036-926-accession',relation='corroborates')
E=ev('siyuan_abolishes_empty_commissions','朝廷废除有名无实的诸司使务',18,'诸司使务','皆废之。',[('帝','撤废发令者')],when='926年四月甲寅政令',place='后唐中央机构',note='原未列机构名单，不扩大为废所有使职。')
E=ev('siyuan_army_feeds_near_capital','朝廷分遣诸军到近畿就食以减少馈运',18,'分遣诸军','以省馈运。',[('帝','分遣发令者')],when='926年四月甲寅政令',place='洛阳近畿',note='省馈运是政令目的；原未具军额或实际节省数，不推。')
E=ev('siyuan_removes_tax_surcharge','朝廷取消夏秋税省耗附加',18,'除夏','秋税省耗。',[('帝','税制政令者')],when='926年四月甲寅政令',place='后唐征税地区',note='省耗为税额附加，不等取消全部夏秋两税。')
claim('event',E,'description','旧史具体规定每斗先有省耗一升，今后只纳正数。',18,'秋夏稅子，每鬥先有省耗一升，今後隻納正數，其省耗宜停。','附加额度据旧补，不称税本取消。',source='jiuwudaishi-036-926-accession',relation='adds')
E=ev('siyuan_limits_tribute','朝廷限定节度防御使四节贡奉且不得敛民，刺史以下不得贡奉',18,'节度、防御等使','刺史以下不得贡奉。',[('帝','贡奉限制发令者')],when='926年四月甲寅政令',place='后唐诸镇州',note='正至端午降诞四节按原纪；限制与禁敛不等所有州已停止征敛。')
claim('event',E,'description','旧史明确贡奉需州府自行圆融，不能科敛百姓，刺史四节也不贡奉。',18,'自於州府圓融，不得科斂百姓。其刺史雖遇四節，不在貢奉。','补经费来源约束，不添加税名。',source='jiuwudaishi-036-926-accession',relation='adds')
E=ev('siyuan_restores_selection_documents','朝廷命三铨只剔除诈伪，其他选人文书恢复旧规',18,'选入先遭',None,[('帝','铨选恢复发令者')],when='926年四月甲寅政令',place='后唐铨选机构',note='底本选入疑选人，文书涂毁主原保留；不把恢复全部旧规理解为容许诈伪。')
E=ev('zheng_ren_named_chancellors','郑珏与任圜同任中书侍郎、同平章事，任圜仍判三司',19,'五月，丙辰朔','圜仍判三司。',[('帝','任命者'),('郑珏','由太子宾客受任宰相者'),('圜','由工部尚书受任宰相兼判三司者')],when='926年五月丙辰朔',place='后唐朝廷',note='判三司与后来专职三司使有别，不把二职混同。')
claim('event',E,'description','旧史同时记郑珏兼刑部尚书、任圜兼工部尚书及判三司。',19,'以太子賓客鄭玨為中書侍郎兼刑部尚書、同中書門下平章事；以工部尚書任圜為中書侍郎兼工部尚書、同中書門下平章事、判三司。','玨/珏按字形、同原职同任职识别郑珏；不因字形新建人。',source='jiuwudaishi-036-926-may-offices',relation='adds')
claim('event',E,'description','新明宗纪同载五月丙辰朔郑珏与任圜任宰相。',19,'五月丙辰朔，太子賓客鄭珏工部尚書任圜為中書侍郎：同中書門下平章事。','标点冒号为电子原样保留。',source='xinwudaishi-006-926-may-offices',relation='corroborates')
E=ev('renhuan_financial_administration_summary','史书记任圜选拔贤俊、杜绝侥幸，任职约一年间府库军民渐充、朝纲粗立',19,'圜忧公如家','朝纲粗立。',[('圜','书载理财及选贤者')],year=None,when='926年五月任职后约一年期间的概述，成果确年与确日未载',place='后唐财政及官员选任',note='期年之间为一段任职结果；非丙辰朔当日全部完成。忧公如家、军民皆足等为史作者概括评价，不当独立实测普遍事实。')
claim('event',E,'description','新任圜传也概述选辟才俊、抑绝侥幸、公私给足。',19,'是時，明宗新誅孔謙，圜選辟才俊，抑絕僥倖，公私給足，天下便之。','史传评价补证，不将概述转成当日统计数字。',source='xinwudaishi-028-renhuan-finance',relation='corroborates')
E=ev('renhuan_an_tension_report','史书记任圜以天下为己任，安重诲因此忌之',19,'圜每以','安重诲忌之。',[('圜','被史书评价以天下为任者'),('安重诲','书称忌任圜者')],year=None,when='任圜任相判三司期间概述，确年日未载',place='后唐朝廷',note='忌及由是是史作者心理和因果判断，不造互相仇敌关系或未来冲突事件。')
E=ev('six_officers_restore_names','霍彦威、苌从简、房知温、杜晏球、夏鲁奇、米君立请求并获准恢复原姓名，其中晏球复王姓',19,'武宁节度使','许之。',[('帝','准复姓名者'),('李绍真','武宁节度使，复霍彦威姓名'),('李绍琼','忠武节度使，复苌从简姓名'),('李绍英','贝州刺史，复房知温姓名'),('李绍虔','齐州防御使，复王晏球姓名'),('李绍奇','河阳节度使，复夏鲁奇姓名'),('李绍能','洺州刺史，复米君立姓名')],when='926年五月丙辰朔任相后叙次，具体确日主未另载',place='后唐诸镇与朝廷',note='李绍真等为赐姓名，各用既有主体；杜晏球沿已有稳定key，王晏球作为本段恢复之名不建第二个人。主剌吏疑刺史保留原字，不额外造职称。')
for old,canonical in [('李绍真','霍彦威'),('李绍琼','苌从简'),('李绍英','房知温'),('李绍虔','杜晏球'),('李绍奇','夏鲁奇'),('李绍能','米君立')]:
 claim('person',people[canonical],'description',f'本段记赐姓名{old}获准复名，对应本站主体{canonical}。',19,span(19,'武宁节度使','许之。'),'按六人次序逐项对应；晏球实际复姓王，本站杜晏球仅稳定主体名称，不把恢复动作写成杜姓。')
claim('event',E,'description','旧明宗纪载霍彦威、房知温、王晏球、夏鲁奇、米君立五人的复名。',19,'李紹真復曰霍彥威，李紹英復曰房知溫，李紹虔復曰王晏球，李紹奇復曰夏魯奇，李紹能復曰米君立。','旧此名单无苌从简，未以其缺载否定主六人；只补其中五人。',source='jiuwudaishi-036-926-may-offices',relation='corroborates')
claim('person',people['苌从简'],'description','苌从简籍贯陈州。',19,'从简，陈州人也。','籍贯并非本年出生，不填出生年。')
claim('person',people['苌从简'],'description','新传载萇从简为陈州人，早年出身屠羊之家。',19,'萇從簡，陳州人也。世本屠羊。','萇/苌繁简同人；仅补籍贯和家庭职业背景，不提前录全传后事。',source='xinwudaishi-047-changcongjian',relation='adds')
E=ev('yanqiu_wang_birth_du_adoption','史书记晏球本为王氏子，养于杜氏，因此此次请复王姓',19,'晏球本王氏子',None,[('王晏球','王氏出身、曾养于杜氏者')],year=None,when='926年复名条附早年追叙，出生及养育确年未载',place='主未载早年养育地点；新传记杜氏在汴州',note='王氏与杜氏未具个人姓名，不编养父母；复姓获准在前事件，早年背景时间单列。')
claim('person',people['杜晏球'],'description','新王晏球传记字莹之、洛阳人，少时遭掠，汴州杜氏得而养为子、冒杜姓。',19,'王晏球字瑩之，洛陽人也。少遇亂，為盜所掠，汴州富人杜氏得之，養以為子，冒姓杜氏。','同王氏本姓与杜养经历印证同一主体，不猜杜家主姓名。',source='xinwudaishi-046-wangyanqiu-family',relation='adds')
E=ev('officials_five_day_inner_audience','朝廷令百官除正衙常朝外，每五日到内殿起居',20,'丁已',None,[('帝','朝仪发令者')],when='926年五月丁已据主电子本；旧作丁巳',place='后唐正衙与内殿',note='主丁已疑丁巳，保留原字并单引旧异文；五日一度不改成每天。')
claim('event',E,'time_original','旧明宗纪作丁巳，并记五日一度内殿起居。',20,'丁巳，初詔文武百僚正衙常參外，五日一度內殿起居。','主已/旧巳异字未悄改，不取同段嵌入五代会要注作独立新来源。',source='jiuwudaishi-036-926-may-offices',relation='conflicts')
E=ev('eunuchs_flee_to_jinyang','宦官数百窜匿山林或落发为僧，七十余到晋阳',21,'宦官数百人','七十馀人，',[],when='926年庄宗内难后至五月诏诛前的逃亡概述',place='山林及晋阳',note='数百与七十余分别为逃匿总述与到晋阳者，不误作全数到晋阳；原未具人名。')
E=ev('siyuan_orders_congwen_execute_eunuchs','李嗣源诏北都指挥使李从温将到晋阳的宦官全部诛杀',21,'诏北都','悉诛之。',[('帝','诏诛发令者'),('从温','北都指挥使、受令者')],when='926年五月本段叙次，主未具日',place='晋阳北都',note='主是命令，具体执行以旧史独立补证；不将诏令默认作现场实杀。')
claim('event',E,'description','旧明宗纪载李从温奏准诏诛宦官，七十余人尽诛于都亭驿。',21,'北京馬步都指揮使李從溫奏，準詔誅宦官。初，莊宗遇內難，宦者數百人竄匿山谷，落發為僧，奔至太原七十餘人，至是盡誅於都亭驛。','执行结果及都亭驿地点据旧明确补证，主仅诏命；旧段己未赐马驴后叙不擅定本事同日。',source='jiuwudaishi-036-926-may-army',relation='adds')
relationship('从温','帝','侄子',21,'从温，帝之侄也。','从温是李嗣源的侄子，方向从侄至帝；父母未名，不推叔伯长幼。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新家人传列从温为明宗四侄之一。',21,'明宗兄弟皆不見于世家，而有姪四人，曰：從璨、從璋、從溫、從敏。','仅印证本段从温关系，其他三人及未名父系留后续；姪/侄字形保留。',source='xinwudaishi-015-mingzong-nephews',relation='corroborates')
E=ev('anjinquan_zhenwu_appointment','李嗣源以安金全有功于晋阳，任其振武节度使、同平章事',22,'帝以',None,[('帝','任命者'),('金全','前相州刺史、受任者')],when='926年五月壬戌',place='晋阳功事、振武任所与朝廷',note='有功为任命理由，不重建此前晋阳同一作战或推战果数字。')
claim('event',E,'description','旧明宗纪补安金全北京左右厢都指挥使旧职与安北都护任职。',22,'壬戌，以前相州刺史、北京左右廂都指揮使安金全為安北都護、振武節度使、同平章事。','附旧职与兼衔，并非另一次任命。',source='jiuwudaishi-036-926-may-army',relation='adds')
E=ev('zhaozaili_requests_ye_visit','赵在礼请求李嗣源赴邺都',23,'丙寅','幸鄴都。',[('在礼','请幸者'),('帝','请幸所向皇帝')],when='926年五月丙寅',place='邺都',note='请幸不等皇帝已经赴邺都。鄴简体展示邺。')
E=ev('zhaozaili_yicheng_appointment_refused','赵在礼被任义成节度使，以军情未听为辞不赴镇',23,'戊辰',None,[('帝','任命者'),('在礼','受任而不赴镇者')],when='926年五月戊辰',place='义成军镇及邺都',note='军情未听为赵所称理由，不泛化成已证全军不服；主义成/旧滑州名称分引。')
claim('event',E,'description','旧史记赵在礼任滑州节度使，加检校太保，以军情不顺辞不任。',23,'戊辰，以金紫光祿大夫、檢校司空趙在禮為滑州節度使，加檢校太保。製下，在禮以軍情不順為辭，不之任。','旧用滑州名称和军情不顺，与主义成及未听各保留，不把托辞当可独立核实事实。',source='jiuwudaishi-036-926-may-army',relation='adds')
claim('event',E,'description','新明宗纪也记戊辰赵在礼任义成军节度使。',23,'戊辰，趙在禮為義成軍節度使。','只取正文任命，不将后夹注报功判断写作已证政策动机。',source='xinwudaishi-006-926-may-offices',relation='corroborates')
E=ev('fuyanchao_audience_and_reward','符彦超入朝，李嗣源称许其保全河东之功',24,'李彦超入朝','尔之力也。”',[('李彦超','入朝并获称许者'),('帝','称许者')],when='926年五月庚午任留后前叙次，入朝确日未载',place='后唐朝廷',note='李彦超沿前批以两史同北京巡检校符彦超；帝语为称许，不将河东无虞扩成所有时期绝无动乱。')
E=ev('fuyanchao_jianxiong_acting','符彦超被任建雄留后',24,'庚午',None,[('李彦超','受任留后者'),('帝','任命者')],when='926年五月庚午',place='建雄军',note='留后与正式节度使分开，主建雄/旧晋州各存。')
claim('event',E,'description','旧明宗纪记庚午以权知北京军府事、汾州刺史符彦超为晋州留后。',24,'庚午，以權知北京軍府事、汾州刺史符彥超為晉州留後，','补符姓名和原职，与前批识别人一致；不把李彦超另建李姓人。',source='jiuwudaishi-036-926-may-army',relation='adds')

review='连续13—24段逐句回查。监国与帝为李嗣源，献祖李国昌、武皇李克用、先帝李存勖按语境复用；视犹子与嗣子礼不擅建收养血缘。霍孔改号是提议，李琪议定保唐及丙午柩前正式即位、受册礼分阶段，前甲午只监国。张宪委城为有司指控，庚戌赐死与旧是月实记、欧阳修不然史论并列不改主。任军主旧二万六千/新二万分引，旧壬子补纪。甲寅改元天成据旧，宫廷五类留额、废虚职、近畿就食、停省耗、四节贡奉禁敛及三铨恢复逐项政令，不称全部执行。主选入、剌吏疑字留原。郑珏/玨同官同任校同人；判三司不等专职三司使。任圜期年政绩及安忌单列确年未载，不当五月朔日全成，评价与心理判断注明。六将复名按列表次序匹配，苌从简米君立新建，晏球稳定杜主体实际本段复王姓，杜养家未名不造养父母。丁已/旧丁巳分引。宦官逃匿、诏诛与旧都亭驿执行分证；李从温侄子至李嗣源方向，未猜叔伯长幼。安金全旧职兼衔补证；赵请幸非已幸、军情为辞，主义成旧滑州各存。李彦超沿前批校符彦超，主建雄旧晋州任职并引。主体展示简体，原文摘录与快照字形不改，电子本纸本未核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(13,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,25)],next_paragraph=Q[25]['id'],next_volume=275,supplements=supplements,excluded_non_body=[],coverage='卷275第13—24段，原文件18—29行；孔循正使、保唐议礼与明宗即位、张宪赐死、返师、天成初政及任相、六将复名、北都诛宦、方镇任命。926年110正文段累计67，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(13,25)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
