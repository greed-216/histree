# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 48–52."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 53))
specs=[
 ('tongjian-276-year-end',YEAR/'part-08/sources/library/tongjian-276-year-end','38a68a4c','司马光等'),
 ('jiuwudaishi-039-december',P/'sources/library/jiuwudaishi-039-december','b2d57128','薛居正等'),
 ('jiuwudaishi-133-gaojixing-death',P/'sources/library/jiuwudaishi-133-gaojixing-death','b2d57128','薛居正等'),
 ('xinwudaishi-069-gaojixing-death',P/'sources/library/xinwudaishi-069-gaojixing-death','b2d57128','欧阳修'),
 ('xinwudaishi-069-gaoconghui-accession',P/'sources/library/xinwudaishi-069-gaoconghui-accession','b2d57128','欧阳修'),
 ('xinwudaishi-015-licongrong-learning',P/'sources/library/xinwudaishi-015-licongrong-learning','b2d57128','欧阳修'),
 ('songshi-263-926-zhangzhao-name',ROOT/'content/books/zizhi-tongjian/vol-275/year-0926/part-01/sources/library/songshi-263-926-zhangzhao-name','60d249b7','脱脱等'),
 ('jiuwudaishi-039-november',YEAR/'part-07/sources/library/jiuwudaishi-039-november','72e54c9a','薛居正等'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p048-p052',
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
for n in range(48, 53):
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
        citation = f'卷276·天成三年（928）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0928_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','季兴':'高季昌','高季兴':'高季昌','从诲':'高从诲','吴主':'杨溥','张昭远':'张昭（五代宋初）','延钧':'王延钧','从荣':'李从荣','从厚':'李从厚','思权':'杨思权','赟':'冯赟'}
NEW_ALIASES={}

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

def event(code, title, n, quote, actors, when=None, note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='928年十二月本段；确日未载'
    key = 'event_zztj_276_0928_' + code
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
        edge = 'participation_zztj_276_0928_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0928_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
dec='jiuwudaishi-039-december';gold='jiuwudaishi-133-gaojixing-death';gnew='xinwudaishi-069-gaojixing-death';gh='xinwudaishi-069-gaoconghui-accession';cr='xinwudaishi-015-licongrong-learning';sz='songshi-263-926-zhangzhao-name';nov='jiuwudaishi-039-november'
E=ev('lijingzhou_reports_qingzhou_capture','李敬周奏报攻取庆州',48,'十二月','庆州，',[('李敬周','奏报收庆州者')],when='928年十二月甲辰奏报；实际攻城日未独载',place='庆州',note='甲辰为奏报定位，不强把攻克执行日与奏到日当同一天；与十月讨令分别。')
claim('event',E,'description','旧明宗纪同月同日记邠州节度使李敬周奏收庆州。',48,'甲辰，邠州節度使李敬周奏，收下慶州，刺史竇廷琬族誅。','与主同奏报定位，邠州静难同军治州，不重造同一克城事件。',source=dec,relation='corroborates')
E=ev('doutingwan_family_executed_qingzhou','庆州被攻取后窦廷琬遭族诛',48,'李敬周',None,[('李敬周','报庆州战果者'),('窦廷琬','族诛对象')],when='928年十二月甲辰奏报所述族诛；实际执行日未独载',place='庆州',note='族诛原语保留，范围人数未具，不能扩成史文明示九族或全庆城人口；不据此猜具体奉行杀人者姓名。')
claim('event',E,'description','旧明宗纪同奏报明确刺史窦廷琬族诛。',48,'甲辰，邠州節度使李敬周奏，收下慶州，刺史竇廷琬族誅。','印证实际已族诛的报告，区别此前仅命讨；执行确日及家族名单不详。',source=dec,relation='corroborates')
E=ev('gaojixing_ill_delegates_gaoconghui','高季兴患病，命其子高从诲暂掌荆南军府事',49,'荆南','权知军府事；',[('季兴','患病并授子暂掌军府者'),('从诲','行军司马等、权知军府事者')],when='928年十二月丙辰卒前；委任确日未独载',place='荆南',note='权知与后来吴授节度职分动作；原子行军司马、忠义节度、同平章衔保留，不猜具体病起日。')
relationship('季兴','从诲','父亲',49,span(49,'荆南','权知军府事；'),'高季兴沿高季昌、从诲沿高从诲；原其子明父方向，复用925既有父边，不新增反向重复。')
E=ev('gaojixing_dies','高季兴去世',49,'丙辰','季兴卒。',[('季兴','荆南节度使、去世者')],when='928年十二月丙辰',place='荆南',note='主确记十二月丙辰；旧帝纪十一月已奏卒与主月份不同，作为异说并列，不把两条报告平均成新日期。')
claim('event',E,'description','旧荆南传记天成三年冬高季兴病脚气而卒。',49,'三年冬，季興病腳氣而卒。','脚气是古书病名，不直接诊断为现代足癣；旧冬纪年与主年相合，具体死日从主另引。',source=gold,relation='corroborates')
claim('event',E,'description','新荆南世家记天成三年冬卒，年七十一，谥武信。',49,'天成三年冬卒，年七十一，謚曰武信。','荆南世家高季兴传承前主语；卒龄照录不倒生年，武信是身后谥，不强同日授谥。',source=gnew,relation='adds')
claim('event',E,'time_original','旧明宗纪十一月壬午记房知温奏高季兴卒，与主十二月丙辰记卒不同。',49,'壬午，房知溫奏，荊南高季興卒。','旧同年十一月奏报早于主卒月份，保留两书纪时矛盾，不能用报告与实际一般差来掩盖时间倒置；纸本待核。',source=nov,relation='conflicts')
E=ev('wu_appoints_gaoconghui_jingnan','吴主授高从诲荆南节度使兼侍中',49,'吴主',None,[('吴主','授荆南军职者'),('从诲','吴授节度兼侍中者')],when='928年十二月高季兴卒后；授职确日未独载',place='吴与荆南',note='吴授与后唐后续复归授职不同，不提前930后唐任命或后来封南平王；杨溥是当前吴主沿已有人。')
claim('event',E,'description','新荆南世家同记季兴卒后，吴以从诲为荆南节度使。',49,'季興卒，吳以從誨為荊南節度使。','只互证吴授节度，侍中衔从主，未用后文入唐申请或长兴任职充当本年已完成。',source=gh,relation='corroborates')
claim('person',people['高从诲'],'description','新荆南世家记高季兴有九子，高从诲为长子继立。',49,'季興子九人，長子從誨立。','本引文补父子与长子继立，字遵圣另引同书下一段，不按九子猜其余姓名和长幼边。',source=gnew)
claim('person',people['高从诲'],'description','新荆南世家记高从诲字遵圣。',49,'從誨字遵聖。','仅补字，不根据后文归唐与后爵倒定本次吴任职日期。',source=gh)
E=ev('zhangzhaoyuan_memorial_on_princely_habits','张昭远上言，批评先朝皇弟、皇子耽于俳优、姬妾和仆马',50,'史馆','何道能贤！',[('张昭远','史馆修撰、上言者')],note='臣窃见是张的奏章观察和评价，整理明确归于其言；先朝背景非新造928皇子一概同日游乐事件。')
claim('person',people['张昭（五代宋初）'],'description','《宋史》记张昭字潜夫，本名昭远，后来避汉祖讳而简称昭。',50,'張昭，字潛夫，本名昭遠，避漢祖諱，止稱昭。','此为同人姓名补证，不写成928年已经改名，也不与许昭远、王昭远合并；复用926已发布出处。',source=sz,relation='corroborates')
E=ev('zhang_proposes_teachers_for_princes','张昭远建议精选皇子师傅，令皇子以师礼学习礼义及治乱之理',50,'诸皇子宜','论安危之理。',[('张昭远','建议师傅和学习礼义者')],note='为建议，不写皇子已经获任全部教师或教育制度已实施。')
E=ev('zhang_disclaims_succession_discussion','张昭远引古制说明太子区分嫡庶、防止乱源，并称当前建储不敢轻议',50,'古者','臣未敢轻议。',[('张昭远','论古制且表明不轻议现建储者')],note='不能概括为请求立某皇子为太子或朝廷已建储；没有点名继位人选，不补。')
E=ev('zhang_proposes_distinctions_in_princely_treatment','张昭远建议皇子恩赐、婚姻、省侍依嫡庶长幼区分等威，杜绝非分之望',50,'至于恩泽','绝其侥冀。”',[('张昭远','建议按嫡庶长幼区分礼遇者')],note='保留原嫡庶长幼建议，不用后续局势推本句专指某个皇子或已实施待遇表。')
E=ev('emperor_praises_zhang_but_does_not_adopt','李嗣源赞叹张昭远建议，却未能采用',50,'帝赏',None,[('帝','赞叹但未采用者')],note='赏叹不等颁给具体钱物赏赐，也不等已施行建议。')
E=ev('wangyanjun_ordains_twenty_thousand','闽王王延钧度民二万为僧，闽中因而多僧',51,'闽王',None,[('延钧','度民为僧的闽王')],place='闽',note='主书记二万照录不改精确查实人数，未找到二十四史同案独立补证；度为出家，不等处死或征兵；不推寺名、具体被度名单。')
E=ev('licongrong_neglect_government_emperor_sends_companion','主书记李从荣年少骄悍、不亲政务，李嗣源遣其熟识左右陪处并委婉劝导',52,'河东','使从容讽导之。',[('从荣','河东节度兼北都留守、被遣人劝导者'),('帝','派熟识左右劝导者')],place='河东、北都',note='左右不具名，不造姓名；骄很原字保留，展示按骄悍，史书评语不扩成心理诊断；遣往命令非具体已经改革政务。')
claim('person',people['李从荣'],'description','新唐家人传称李从荣喜儒，学作诗，多招文学之士赋诗饮酒。',52,'頗喜儒，學為歌詩，多招文學之士，賦詩飲酒，','本段生平概叙作为补充，不强所有活动发生928十二月；不得据此覆盖主书记不亲政务或猜现代学历。',source=cr)
E=ev('companion_urges_congrong_emulate_conghou','受遣左右私劝李从荣学习李从厚恭谨亲贤，勿因年长而声望落后',52,'其人私','河南之下。”',[('从荣','听取劝励并被拿与弟比较者'),('从厚','左右赞誉的比较对象')],place='河东、北都',note='河南相公是对话称谓沿李从厚，不据其再新增当前河南尹授职；从厚只是比较对象不当在场发言。')
relationship('从荣','从厚','兄长',52,span(52,'其人私','河南之下。”'),'齿长及后文兄弟对举明确从荣年长，复用927兄长边，方向从荣→从厚，不新增反向重复。')
E=ev('licongrong_fears_being_displaced','李从荣不悦，向杨思权称朝廷推崇李从厚而贬己，担心遭废',52,'从荣不悦','我其废乎！”',[('从荣','不悦并表达遭废忧惧者'),('思权','步军都指挥使、听诉者')],place='河东、北都',note='我其废乎为担忧，不是朝廷已经罢废或正式决定立从厚；朝廷皆推短亦为从荣自己的说法。')
E=ev('yangsiquan_reassures_congrong_with_troops','杨思权以李从荣握强兵及自身可助相劝，称无须担忧',52,'思权曰','何忧？”',[('思权','以兵力安慰并自许助力者'),('从荣','获安慰者')],place='河东、北都',note='相公有强兵是杨原话，没有新增具体兵数或已经发生叛乱。')
E=ev('yangsiquan_proposes_muster_armour_secret_defence','杨思权劝李从荣增募部曲、修治甲兵，暗备自固',52,'因劝','自固之备。',[('思权','劝募兵修甲以自固者'),('从荣','被建议增兵备武者')],place='河东、北都',note='劝字记录建议，不独立证明募兵已完成或兵力已增加到某数，更非已经向朝廷进攻。')
E=ev('yangsiquan_warns_companion_brothers_comparison','杨思权责问受遣左右为何赞弟抑兄，称己方能够帮助李从荣',52,'又谓','助之邪！”',[('思权','向左右发言者')],place='河东、北都',note='是杨的言语，助之未具具体叛谋行动；弟兄承从厚从荣，未添加匿名左右人物。')
E=ev('companion_tells_fengyun_yang_statements','受遣左右恐惧，将杨思权之言告副留守冯赟',52,'其人惧','副留守冯赟，',[('赟','副留守、获告者')],place='河东、北都',note='告知与下一密奏分步骤，未推冯本人偷听前话。')
E=ev('fengyun_secretly_reports_yangsiquan','冯赟将该事秘密上奏',52,'赟密', '奏之。',[('赟','密奏者')],place='河东至后唐朝廷',note='之承杨言语及从荣忧惧案，未虚构奏疏全文、具体送达日。')
E=ev('emperor_summons_yangsiquan_spares_him','李嗣源召杨思权入朝，因李从荣之故而未治其罪',52,'帝召',None,[('帝','召而不罪者'),('思权','被召入朝且未治罪者'),('从荣','帝不罪所顾及者')],place='河东至阙',note='不罪是本案结果，不扩成杨终身绝不被问责；以从荣故保留史述原因，不猜私下赦免交换。')
review='卷276连续928年第48—52段、原80—84行。甲辰李敬周报庆州克与窦族诛分，奏日非必实际克城执行同日，族诛不臆造九族人数。高季兴沿高季昌，寝疾委从诲权府、丙辰卒、吴杨溥授从诲节度兼侍中分；父边复用925。旧荆南传三年冬脚气卒是古病名不现代诊断；新冬71龄不倒生年、九子长从诲与字遵圣分出处，身后谥非同日定封。旧明宗十一壬午已报高卒与主十二丙辰有时间倒置，明确异说待纸本核不以报告差解释掉；不提前929归唐申请、930后唐授职与后封。张昭远沿张昭（五代宋初），复用926宋史本名避汉祖讳同人说明，改名非928事。张奏批先朝爱俳优姬妾仆马是其评价，精选师傅、古太子制及不敢轻议现建储、恩婚省侍依嫡长区分建议分，帝赞而未用；不写已建太子或已实施。闽延钧二万度僧主独证人数照录不当现代核实精数，未具寺名名单。主从荣不亲政务为史评；帝遣亲善左右讽导、左右私誉从厚、从荣不悦告杨忧废、杨自许强兵安慰、劝募修甲自固、责左右、左右惧告冯、冯密奏、召杨不罪分，担忧非已废，劝备非已完募或已反。河南相公沿从厚对话称谓不新授河南尹，从厚比较非在场，杨陈情不建终身盟友边；兄边复用927从荣→从厚。新传喜儒作诗为生平补充不强本月，不掩主不政。展示简体，原TXT逐字摘录定位保留；纸本异文待考。全年最后5正文，不将快照中929段计已读。'
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(48,53):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(48,53)],next_paragraph='zztj-v276-y0929-p001',next_volume=276,next_year=929,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续928年第48—52段、原文件80—84行；庆州克与窦族诛、高氏交接、张皇子教导奏、闽度僧、从荣及杨冯奏报案。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(48,53)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
