# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 926, paragraphs 61–67."""
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
 ('jiuwudaishi-037-926-december-offices',P/'sources/library/jiuwudaishi-037-926-december-offices','d0d4d8bd','薛居正等'),
 ('jiuwudaishi-136-liyan-monitor',P/'sources/library/jiuwudaishi-136-liyan-monitor','d0d4d8bd','薛居正等'),
 ('tongjian-275-926-yearend-and-927-opening',P/'sources/library/tongjian-275-926-yearend-and-927-opening','d0d4d8bd','司马光等'),
 ('xinwudaishi-027-zhuhongzhao',P/'sources/library/xinwudaishi-027-zhuhongzhao','d0d4d8bd','欧阳修'),
 ('xinwudaishi-064-926-monitor',P/'sources/library/xinwudaishi-064-926-monitor','d0d4d8bd','欧阳修'),
 ('xinwudaishi-064-926-shu-fiscal',P/'sources/library/xinwudaishi-064-926-shu-fiscal','d0d4d8bd','欧阳修'),
 ('xinwudaishi-068-926-min-succession',P/'sources/library/xinwudaishi-068-926-min-succession','d0d4d8bd','欧阳修'),
 ('xinwudaishi-068-yanhan-cuishi',P/'sources/library/xinwudaishi-068-yanhan-cuishi','d0d4d8bd','欧阳修'),
 ('tongjian-275-926-autumn-offices',YEAR/'part-07/sources/library/tongjian-275-926-autumn-offices','b987ace4','司马光等'),
 ('jiuwudaishi-032-cunxian-report',ROOT/'content/books/zizhi-tongjian/vol-273/year-0924/part-06/sources/library/jiuwudaishi-032-cunxian-report','f4a1df9b','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-926-autumn-offices','tongjian-275-926-yearend-and-927-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0926-p061-p067',
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
for n in range(61, 68):
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
    ck = f'claim_zztj_275_0926_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','魏王继岌':'李继岌','知祥':'孟知祥','季良':'赵季良','严':'李严','硃弘昭':'朱弘昭','延翰':'王延翰','延钧':'王延钧','延禀':'王延禀','审知':'王审知','陈陶':'陈陶（福州指挥使）','崔氏':'崔氏（王延翰妻）','从荣':'李从荣','镠':'钱镠'}
NEW_ALIASES={'朱弘昭':['硃弘昭'],'王延禀':['王延稟'],'陈陶（福州指挥使）':[],'崔氏（王延翰妻）':[],'李从荣':['李從榮','从荣']}
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
E=ev('jiji_chongtao_shu_reward_collection','追叙李继岌郭崇韬令蜀富民输犒赏钱五百万缗，准用金银缯帛充数',61,'初，魏王继岌','听以金银缯帛充，',[('魏王继岌','犒赏征收者'),('郭崇韬','犒赏征收者')],year=None,when='926年十月转运条追叙此前平蜀犒军征收，确年未具',place='蜀中',note='初追叙，不强归本年十月；钱缗为折计口径、金银缯帛为充数物，不当五百万枚现钱实物。')
claim('event',E,'description','新蜀世家称魏王班师时孟知祥率富人与王氏故臣家，得钱六百万缗犒军。',61,'初，魏王之班師也，知祥率成都富人及王氏故臣家，得錢六百萬緡以犒軍，其餘者猶二百萬。','新六百万及知祥募主体与主魏郭五百万不同，各存不合为一千一百万征收。',source='xinwudaishi-064-926-shu-fiscal',relation='conflicts')
E=ev('shu_rich_people_pressed_suicides','史书记犒军钱昼夜督责，出现自杀者',61,'昼夜督责','有自杀者，',[('魏王继岌','前句征收所归魏王'),('郭崇韬','前句征收所归郭')],year=None,when='前事犒军征收期间，具体年月和次数未载',place='蜀中富民征收',note='有自杀者没有具名和人数，不生成一位虚构受害者或精确死者总数；由征收语境关联督责，未造每人死亡原因细节。')
E=ev('shu_reward_money_remainder','犒军后所征钱仍余二百万缗',61,'给军之馀','犹二百万缗。',[],year=None,when='前事犒军给付之后至此次转运之前，确日未载',place='蜀府库',note='剩余账面口径，不据五百万减二百万得实际现金军费三百万，因为允许其他财物充数且时段不同。')
claim('event',E,'description','新蜀世家也记犒军后剩余二百万。',61,'其餘者猶二百萬。','新募总六百万与主五百万有异，剩余额近同不能单独证明总征数一致。',source='xinwudaishi-064-926-shu-fiscal',relation='corroborates')
E=ev('renyuan_dispatches_zhaojiliang_shu','任圜遣赵季良为孟知祥官告国信兼三川都制置转运使',61,'至是，任圜','兼三川都制置转运使。',[('任圜','判三司、派遣者'),('赵季良','盐铁判官太仆卿、受派者'),('孟知祥','官告国信所往节度使')],when='926年十月甲辰到成都前，派遣确日未载',place='后唐朝廷至成都',note='官告国信与转运两种任务皆保留，素知成都富饶是史述认识，不推有实时财务数据库。')
claim('event',E,'description','新蜀世家称是冬孟知祥拜侍中，以太仆卿赵季良赍官告，兼三川制置使督余钱及两川征赋。',61,'是冬，知祥拜侍中，乃以太僕卿趙季良賷官告賜之，因以為三川制置使，督蜀犒軍餘錢送京師，且制置兩川征賦，','新称制置而主都制置转运完整称，两任务相关但未偷改为同名官署，冬未提供甲辰派遣确日。',source='xinwudaishi-064-926-shu-fiscal',relation='adds')
E=ev('zhaojiliang_arrives_chengdu','赵季良抵达成都',61,'甲辰','季良至成都。',[('季良','到访使者')],when='926年十月甲辰',place='成都',note='前段庚子与本段甲辰仍承十月编次，不换算公历日期；到访与之后载财到洛阳分事件。')
E=ev('meng_permits_store_refuses_tax','蜀人欲不给财物，孟知祥表示可输府库积存，但不许取州县税养兵之钱',61,'蜀人欲皆不与','决不可得。”',[('知祥','区分府库与州县租税的答话者'),('季良','本次取财任务的使者')],when='926年十月甲辰到成都后，谈话确日未载',place='成都',note='知祥称镇兵十万是答话的用财理由，不当独立核定全蜀战兵数；蜀人欲拒是概述，不把每一民户视作已拒缴法定税。')
E=ev('zhaojiliang_only_remits_store_goods','赵季良仅发府库物，不再谈制置转运职事',61,'季良但发库物','职事矣。',[('季良','调发库物、未再谈职事者'),('知祥','府库税收争执的节度使')],when='926年十月成都交涉后，执行确日未载',place='成都府库',note='不敢复言为史叙，不推三川转运制度已正式废除。')
claim('event',E,'description','新蜀世家作孟知祥怒而不奉诏，因与季良有旧而留之。',61,'知祥怒，不奉詔。然知祥與季良有舊，遂留之。','新概说拒诏与主允许府库拒州税的细分口径不同，各存不视为主全拒或新已证全输。',source='xinwudaishi-064-926-shu-fiscal',relation='conflicts')
E=ev('anchonghui_fears_two_shu_commands','史书记安重诲忧孟知祥董璋据险拥兵难制，因知祥近姻而欲图之',61,'安重诲以知祥','阴欲图之。',[('安重诲','书述忧惧和图谋者'),('知祥','被忧制的西川节度使'),('董璋','被忧制的东川节度使')],year=None,when='926年监军派任前背景概述，具体始日未载',place='后唐朝廷及两川',note='恐和阴欲为史作者心理判断，不自动生成已发动征蜀战役、谋杀行动或模糊姻亲边；知祥与庄宗亲属已有具体证据另处保留。')
E=ev('liyan_volunteers_shu_monitor','李严自请为西川监军，称必能制孟知祥',61,'客省使','必能制知祥；',[('严','客省使泗州防御使、请任者'),('知祥','所声称可制对象')],when='926年十月己酉任命前',place='后唐朝廷',note='必能是李严自许，不能写后来确已控制知祥；客省使身份区别凤翔李继曮。')
claim('event',E,'description','旧蜀传也记李严献谋请求为西川监军以制知祥，朝廷许可。',61,'因獻謀於重誨，請以己為西川監軍，庶效方略，以制知祥，朝廷可之。','旧天成中未具日，仅补请任及获准；后段927已杀不提前录为926死。',source='jiuwudaishi-136-liyan-monitor',relation='corroborates')
E=ev('liyan_appointed_xichuan_monitor','朝廷任李严为西川都监',61,'己酉','以严为西川都监，',[('帝','任命所归朝廷皇帝'),('严','获任西川都监者')],when='926年十月己酉',place='后唐朝廷及西川',note='任命不等己酉已到成都，主后927才抵监受杀，不搬后事到本年。')
claim('event',E,'description','新蜀世家记明宗先罢各道监军，安重诲再以李严为西川监军。',61,'明宗入立，悉誅宦者，罷諸道監軍。彥賓已罷，重誨復以客省使李嚴為監軍。','补先罢后置的制度背景，焦彦宾未在本批新建，主旧称都监/监军各沿书称；后927实际杀李严只作为定位上下文不入本批事。',source='xinwudaishi-064-926-monitor',relation='adds')
E=ev('zhuhongzhao_appointed_dongchuan_deputy','文思使朱弘昭任东川副使',61,'文思使太原硃弘昭','为东川副使。',[('帝','任副使所归朝廷皇帝'),('硃弘昭','太原人文思使、任东川副使')],when='926年十月己酉条，未单列别日',place='后唐朝廷至东川',note='硃/朱规范化展示同人；任命不等同日已入东川，未提前记录其逃归。')
claim('person',people['朱弘昭'],'description','新朱传称朱弘昭太原人，明宗即位为文思使，董璋东川时以之为副使。',61,'朱弘昭，太原人也。少事明宗為客將，明宗即位，為文思使。與安重誨有隙，故常使于外。董璋為東川節度使，乃以弘昭為副使。','同籍贯同官同董任地校硃弘昭为朱弘昭，保留原字；新与安有隙为其书解释，不作为主监军全部出使原因已证。',source='xinwudaishi-027-zhuhongzhao',relation='adds')
E=ev('liyan_mother_warns_fate','李严母亲告诫他再赴蜀或以死报蜀人',61,'李严母贤明',None,[('严','受母亲告诫者')],year=None,when='李严再赴蜀前，具体说话日未载',place='李严母子谈话处，史未具地',note='母未名不造女性姓名；必以死为预言警告，不认此时李严已死；贤明为史作者评价。')
E=ev('old_office_certificate_fee_and_poverty','追叙告身旧须输朱胶绫轴钱，丧乱后贫官多仅受敕牒',62,'旧制','多不取告身。',[],year=None,when='926年十一月改革以前的旧制与丧乱背景，确年未具',place='后唐吏部及受官者',note='告身与敕牒不同凭证；贫者多不取为概述，不写所有官员都一直缴钱而此前没有免缴。硃胶保原字。')
claim('event',E,'description','旧庄宗纪已有特恩授官及侍卫内司等告身官给、停朱胶和台省礼钱的部分减免。',62,'詔：「起今後特恩授官及侍衛諸軍將校、內諸司等官，其告身官給，舊例朱膠錢、台省禮錢並停，','旧此前部分减免可与主改革并存，不把926改革当历史上首次任何官员免缴。此前诏不是本年新令，独立补旧制例外。',source='jiuwudaishi-032-cunxian-report',relation='adds')
E=ev('liuyue_petitions_certificate_reading','刘岳上言告身有褒贬训戒之辞，不应让受官者从未见到',62,'十一月','岂可使其人初不之睹！”',[('刘岳','吏部侍郎、上言者')],when='926年十一月甲戌',place='后唐朝廷',note='上言论证与后敕分开，不能写只凭奏已全部发官告。')
E=ev('court_grants_certificates_ranked_officials','朝廷令文班丞郎给谏及武班大将军以上赐告身',62,'敕文班','宜赐告身。',[('帝','发敕者')],when='926年十一月甲戌刘岳奏后条，敕日未另列',place='后唐官员授官',note='此时范围有职阶限制，不误写此敕已普及卒伍胥史。')
E=ev('ministers_extend_free_certificates','执政随后奏请所有除官者不再输钱、皆赐告身',62,'其后执政议','皆赐告身。”',[],year=None,when='甲戌改革之后，具体批准及实施日期未载',place='后唐朝廷',note='奏为建议，主此句未单具批准日期，不能强说所有受官者在甲戌当天实际领证；不给未名执政安上任圜或冯道名字。')
E=ev('certificate_honorary_titles_background','史书记当时正员外试衔帖号用于宠激军中将校',62,'当是时','将校而已，',[],year=None,when='本段制度背景，当时具体起止未载',place='后唐军队及授衔制度',note='只记试衔帖号与正员之别，不把所有荣誉衔当实任台省官。')
E=ev('changxing_later_certificate_expansion','史书追述长兴以后授衔扩及卒伍胥史，岁赐告身以万数',62,'及长兴以后',None,[],year=None,when='长兴以后（后时延叙），具体每年及范围未具',place='后唐军、州、镇、戍及官告制度',note='明确后时延叙，不写926已有岁万数或十万；不按编年段年份污染起止时间，不造逐年具体数量。')
E=ev('yanjun_sent_quanzhou_after_succession','追叙王延翰袭位一月余，将弟王延钧任泉州刺史',63,'闽王延翰','为泉州刺史。',[('延翰','出弟任刺史者'),('延钧','泉州刺史、弟')],year=None,when='王延翰袭位才逾月；926年十二月内乱条追叙背景，确日未载',place='闽、泉州',note='不能把逾月背景固定在本年十二月，也不把兄弟疏远当已开始内战；主蔑弃为评价。')
claim('event',E,'description','新闽世家也记延翰立后以弟延钧为泉州刺史，延钧怒。',63,'延翰立，以其弟延鈞為泉州刺史，延鈞怒。','怒为新所述心理，未具出任确日，与主后因采女谏隙分别。',source='xinwudaishi-068-926-min-succession',relation='corroborates')
relationship('延翰','延钧','兄长',63,'出其弟延钧为泉州刺史。','明确延钧为弟，延翰是兄长，不用无方向兄弟代替，不另建弟弟逆边。')
E=ev('yanhan_selects_women_yanjun_remonstrates','王延翰持续采民女充后庭，王延钧上书谏，被延翰愤怒而生隙',63,'延翰多取','由是有隙。',[('延翰','采女与不悦者'),('延钧','上书极谏者')],year=None,when='十二月内乱之前背景，各次采女与谏书确日未载',place='闽境内及泉州书奏',note='父死袭位以后的背景，人数未具；不引新妻八十四死数套本次或视所有被选女性均死。')
E=ev('yanbing_refuses_women_selection_letter','王延翰令建州刺史王延禀采女，王延禀复书不逊，二人有隙',63,'父审知养子','亦有隙。',[('延翰','下采女书令者'),('延禀','建州刺史、回信不逊者')],year=None,when='926年十二月内乱以前背景，书来往确日未载',place='闽、建州',note='不逊为书述评价，不补失传书全文；本姓周由新补，不单凭姓不同另造主体。')
claim('person',people['王延禀'],'description','新闽世家称建州刺史延稟为王审知养子、本姓周。',63,'審知養子建州刺史延稟，本姓周氏，','同职同养父同袭福州校延禀/延稟字形同人；未具原全名，不自动添加周彦琛等未核别名。',source='xinwudaishi-068-926-min-succession',relation='adds')
relationship('审知','延禀','养父',63,'父审知养子延禀为建州刺史，','审知是延禀养父，养与生分别；不能因审知为延翰父便自动推所有兄弟具体长幼。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新闽世家亦明确王审知养子延稟。',63,'審知養子建州刺史延稟，本姓周氏，','只补养父身份，不把周姓自动建同名养父另一人。',source='xinwudaishi-068-926-min-succession',relation='corroborates')
E=ev('yanbing_yanjun_attack_fuzhou','王延禀王延钧合兵袭福州',63,'十二月','合兵袭福州。',[('延禀','建州出兵者'),('延钧','泉州出兵者')],when='926年十二月辛卯之前',place='福州',note='合兵是本次协同行动，不由此自动新增终身盟友边或全部兵额。')
claim('event',E,'description','新闽世家亦记十二月延稟延钧皆以兵入，执杀延翰。',63,'十二月，延稟、延鈞皆以兵入，執延翰殺之。','新概叙两人参与，主延禀先到执杀、延钧当日后至差异，不能把主两人都直接执行处斩写成确定。',source='xinwudaishi-068-926-min-succession',relation='adds')
E=ev('fuzhou_chentao_defeated_suicide','王延禀顺流先抵福州，指挥使陈陶出战败后自杀',63,'延禀顺流','陶自杀。',[('延禀','先到攻城者'),('陈陶','福州指挥使、战败自杀者')],when='926年十二月辛卯前夜以前，战日未单列',place='福州',note='本陈陶为福州指挥使，既有人物陈陶是陈敬瑄子雅州刺史；无同人确证故加限定名分开，不把仅同名跨地区强合。')
claim('person',people['陈陶（福州指挥使）'],'death_year','福州指挥使陈陶于926年战败后自杀。',63,'福州指挥使陈陶帅众拒之，兵败，陶自杀。','主实际死事，区别891雅州陈陶，未把两人死亡互相覆盖。')
E=ev('yanbing_enters_west_gate_arsenal','王延禀当夜率壮士百余人由西门梯城入，执守门者、开库取兵仗',63,'是夜','发库取兵仗。',[('延禀','率壮士夜入者')],when='926年十二月辛卯前夜据主本段',place='福州西门及军库',note='百余仅此入城队，不当建泉两军合计；执守门者不等所有守门者已被斩。')
E=ev('yanhan_hides_captured_at_dawn','王延禀抵寝门，王延翰躲入别室，次日辛卯旦被捕',63,'及寝门','延禀执之，',[('延禀','捕获者'),('延翰','隐匿后被捕者')],when='926年十二月辛卯旦，隐匿在此前夜',place='福州王延翰寝门及别室',note='隐匿不是已成功逃城；捕获与之后指控处斩分事件。')
E=ev('yanbing_accuses_yanhan_cui_regicide','王延禀向吏民公布罪状，声称王延翰与妻崔氏共弑先王',63,'暴其罪恶','告谕吏民，',[('延禀','指控公布者'),('延翰','被指控杀父者'),('崔氏','王延翰妻、被指控者')],when='926年十二月辛卯旦',place='福州',note='且称为指控内容，不将夫妇确弑王审知写成已核史实；崔氏主未名，限定夫名建主体不与其他崔氏合。')
claim('person',people['崔氏（王延翰妻）'],'description','新闽世家称王延翰妻为崔氏。',63,'其妻崔氏陋而淫，延翰不能制。','只补配偶姓氏及身份，不将新评价当已核具体犯罪；新后崔病死未具确年，不据本指控认为她此日尚在世或被杀。',source='xinwudaishi-068-yanhan-cuishi',relation='adds')
relationship('崔氏','延翰','妻子',63,'延翰与妻崔氏共弑先王，','主妻称足证婚姻，弑先王只是延禀指控，婚姻证据与罪行真实性分开。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新闽世家独立称王延翰之妻为崔氏。',63,'其妻崔氏','妻身份印证，不新建丈夫逆边。',source='xinwudaishi-068-yanhan-cuishi',relation='corroborates')
E=ev('yanbing_executes_yanhan_zichen','王延禀斩王延翰于紫宸门外',63,'斩于','紫宸门外。',[('延禀','处斩者'),('延翰','被处斩者')],when='926年十二月辛卯旦',place='福州紫宸门外',note='主处斩客体承延翰；妻是否被斩未记，不扩大执行范围或以被斩倒证所有指控为真。')
claim('person',people['王延翰'],'death_year','王延翰于926年十二月辛卯被王延禀处斩。',63,span(63,'辛卯旦','斩于紫宸门外。'),'捕至斩的连续原文足证王延翰实际死亡；未把婚姻中的崔氏也写为同日死。')
E=ev('yanjun_admitted_appointed_weiwu_acting','王延钧同日抵城南，被延禀迎入并推为威武留后',63,'是日，延钧',None,[('延钧','获推威武留后者'),('延禀','开门迎入并推立者')],when='926年十二月辛卯',place='福州城南及城内',note='主成南疑城南原字留；威武留后是地方推举，未说后唐同日正式册闽王；新其后更名鏻不凭此条强日录入。')
E=ev('luwenjin_appointed_yicheng','卢文进任义成节度使、同平章事',64,'癸已',None,[('帝','任命者'),('卢文进','获任义成者')],when='926年十二月癸已据底本，已疑巳；旧纪甲午',place='义成军、滑州及后唐朝廷',note='主癸已原字非标准干支，记疑巳不静默改；主旧异日而军名州名同职同人，不造两次任命。')
claim('event',E,'description','旧明宗纪甲午授卢文进检校太尉、同平章事、滑州节度使。',64,'甲午，以契丹盧龍軍節度使盧文進為檢校太尉、同平章事，充滑州節度使。','军州同任可互证，甲午与主癸已日期不同，待纸本。',source='jiuwudaishi-037-926-december-offices',relation='conflicts')
E=ev('licongrong_appointed_tianxiong','皇子李从荣任天雄节度使、同平章事',65,'庚子',None,[('帝','任子所归李嗣源'),('从荣','皇子、天雄受任者')],when='926年十二月庚子',place='天雄军、魏博及朝廷',note='新人物从荣为本年明宗皇子，同旧皇第二子身份校，不预设为当年太子或储君。')
claim('person',people['李从荣'],'description','旧明宗纪称皇第二子从荣任检校太保、同平章事、天雄节度使、邺都留守。',65,'庚子，皇第二子金紫光祿大夫、檢校司徒從榮可檢校太保、同平章事、天雄軍節度使、鄴都留守。','补子次与留守，未反推精确生年或当年已册太子。',source='jiuwudaishi-037-926-december-offices',relation='adds')
relationship('李嗣源','从荣','父亲',65,'以皇子从荣为天雄节度使、同平章事。','帝为明宗李嗣源，皇子明确父子，父至子，不另建儿子逆边。')
E=ev('zhaojiliang_shu_goods_reach_luoyang','赵季良等运蜀金帛至洛阳，史书记数量十亿',66,'赵季良','至洛阳，',[('季良','输运蜀金帛者')],when='926年十二月年末条，抵达确日未载',place='蜀至洛阳',note='十亿原文未明单位，金帛不能自动换为十亿缗银两或现代货币；同前余二百万缗不是等量可直接换算数。')
E=ev('court_shortage_alleviated_shu_goods','史书称朝廷匮乏，依赖蜀金帛来济',66,'时朝迁',None,[],when='926年年末转运到洛阳之后，具体日未载',place='后唐朝廷、洛阳',note='主朝迁疑朝廷原字保留；财政济用是书作者因果概述，不证明此后财政长期充裕。')
E=ev('qianliu_era_baozheng','钱镠在朝命不通期间改元宝正',67,'是岁','改元宝正；',[('镠','吴越王、改元者')],when='926年本年概记，改元具体日未载',place='吴越',note='主本年直记而不是王自号皇帝，改元与外交不通因果为史叙；二十四史本次检索未获明确补证，不用范围外专书顶替。')
E=ev('wuyue_later_omits_baozheng_era','史书追述吴越后复通中原，讳而不称宝正年号',67,'其后',None,[('镠','本段吴越王、后时省称主体')],year=None,when='改元宝正后重新通中原时，确年未载',place='吴越及中原交聘',note='其后不强定926同年，不自动算翌年就弃年号；讳为史述态度，未造双方已经签特定条约。')

review='连续61—67段逐句校核。魏郭平蜀犒钱初追叙未具确年置null，主五百万缗/新孟六百万缗及募者有差，金银缯帛充数非全现金，不用总减余定已核军费；督责自杀未具姓名人数。主新余二百万同而非独立确证总数。任派赵官告国信及转运、甲辰到成都、孟可府库不可州税与赵只发库物分事；镇兵十万是孟答话不当精确军额，新拒诏留赵与主细分财物拒税差异并存。安惧两川和近姻阴图属书心理判断不推已战或含糊姻亲边。李请任必制是自许，己酉任监不提前927到成都被杀，新旧先罢监再置背景只补本阶段。朱弘昭硃朱同太原文思同东川校人，母李未名不造姓名且死报预言不是现死。告身旧制费用与贫者不取、甲戌刘奏、限定赐官告、后执政普及建议、当时试衔军将与长兴以后扩卒胥岁万数区分；旧庄宗部分官告免钱提示此前非全员都收费，后时不强926。闽袭位逾月出弟是背景未强十二月，延翰兄延钧方向，审知养父延禀本姓周仅新补姓不猜原名，采女及谏书争执未取新妻八十四死数套此事。十二月合兵、延禀先至陈陶败自杀、百余夜入西门执守取库、隐匿捕延翰、延禀弑父指控、斩延翰、延钧同日入留后各分。陈陶福州军使与旧陈敬瑄子雅州刺史同名无同人证，限定陈陶（福州指挥使）另建、无别名陈陶碰撞；不把旧父子归他。崔氏限定延翰妻，妻边确而共弑王为指控，不写史实，主未言妻同日死；新妻死无确年不强此日活死。延钧成南疑城南原字留，主时序其后至/新概两军共同执杀各存。主卢癸已疑巳/旧甲午授滑州义成同职留日异不造双任。李从荣本年皇子/旧第二子父李嗣源明确，未太子。蜀金帛十亿未明单位不添缗，朝迁疑廷原字，济财政不推长期富。钱本年改宝正与后复通讳称两阶段，后年未知null，不引范围外专书代替二十四史。927年标题与分隔不生成926史事，下一卷年未处理不标完；简体展示、底本逐字保留，纸本待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(61,68):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=926,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(61,68)],next_paragraph='zztj-v275-y0927-p001',next_volume=275,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷275第61—67段，原文件66—72行；蜀财赋监军、官告改革、闽内乱、卢与从荣任官、金帛转运及吴越年号。926年110正文段末7段，全年完成须联合13批审计。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(61,68)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
