"""Curate Tongjian 267, year 909, consecutive paragraphs 26–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 61))
main1 = 'tongjian-267-909-summer'
main2 = 'tongjian-267-909-summer-battles'
new_liu_flight = 'xinwudaishi-044-liuzhijun-flight'
new_jiangxi = 'xinwudaishi-061-jiangxi'
new_yuan = 'xinwudaishi-067-yuan-surname'
old_liuqi = 'jiuwudaishi-064-liuqi'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0909-p026-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (main1, P.parent / 'part-01/sources/library' / main1, '8a032ff7', '司马光等'),
    (main2, P / 'sources/library' / main2, 'f23ed514', '司马光等'),
    (new_liu_flight, P / 'sources/library' / new_liu_flight, '528dc5cd', '欧阳修等'),
    (new_jiangxi, P / 'sources/library' / new_jiangxi, 'f23ed514', '欧阳修等'),
    (new_yuan, P / 'sources/library' / new_yuan, 'f23ed514', '欧阳修等'),
    (old_liuqi, P / 'sources/library' / old_liuqi, 'f23ed514', '薛居正等'),
]
source_dirs = {sk: d for sk, d, _, _ in source_specs}
manifest = []
for sk, d, commit, author in source_specs:
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file=os.path.relpath(d / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (main1, main2)}
for n in range(26, 41):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'徐知诰':'李昪', '吕兗':'吕兖', '李继徽':'杨崇本', '王景仁':'王茂章', '硃景':'朱景', '硃全忠':'朱温', '蜀主':'王建', '吴越王镠':'钱镠', '晋王克用':'李克用', '晋王存勖':'李存勖', '济阴王':'唐昭宣帝', '唐哀皇帝':'唐昭宣帝', '存勗':'李存勖', '克寧':'李克宁'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/later-liang-907-923/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json',
                'content/later-liang-907-923/content-batch.json',
                'content/books/zizhi-tongjian/vol-260/year-0895/part-04/content-batch.json',
                'content/books/zizhi-tongjian/vol-263/year-0902/part-02/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_267_0909_02_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷267·开平三年（909）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='五代十国', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷267开平三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=909, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_267_0909_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        if key not in {row['key'] for row in B['events']}:
            row = dict(legacy_events[reuse_key], status='draft')
            B['events'].append(row)
        reused.add(key)
        desc = title + '。'
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '909年本段条；确日未载', dynasty='五代十国', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '909年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_267_0909_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def relation(key, n, quote, note):
    assert quote in Q[n]['text']
    row = legacy_relations[key]
    if key not in {item['key'] for item in B['person_relationships']}:
        B['person_relationships'].append(dict(row, status='draft'))
        reused.add(key)
    claim('person_relationship',key,'description',row['description'],n,quote,note)

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_267_0909_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 26–30: collapse of Liu Zhijun's defenses and Liu Shouguang's declarations.
event('tongguan_taken','刘鄩借已俘伏兵为前导攻克潼关，俘刘知浣',26,
      '刘鄩至潼关东，获刘知俊伏路兵蔺如诲等三十人，释之使为前导。',
      [('刘鄩','利用俘兵为前导的梁军将领')],
      when='909年六月辛亥后；确日未载',place='潼关',
      note='底本先作“蔺如诲”、后作“如海”，疑同人讹字，原文照录；本批不新建两个人物。')
claim('event','event_zztj_267_0909_tongguan_taken','description',
      '梁军乘关门开放攻克潼关，并俘刘知浣。',26,
      '鄩兵乘门开直进，遂克潼关，追及知浣，擒之',
      '刘知浣是前段刘知俊之弟；关吏误纳已俘伏兵后梁军进城，不推定守关者主动归附。')
event('liang_emperor_shanzhou','朱温抵达陕州',27,
      '癸丑，帝至陕。',
      [('朱温','抵达陕州的后梁皇帝')],when='909年六月癸丑',place='陕州',
      note='与上一段潼关得失同在军事背景中，未把朱温记为亲临潼关。')
event('danzhou_mutiny','丹州王行思等作乱，刺史宋知海逃走',28,
      '丹州马军都头王行思等作乱，刺史宋知海逃归。',
      [('王行思','丹州叛乱的马军都头'),('宋知海','丹州刺史，事变后逃走')],
      when='909年六月条；确日未载',place='丹州',
      note='“逃归”未明具体目的地；丹州后来由梁军收复见第34段。')
event('liuzhijun_flight','潼关失守后刘知俊举族奔岐，聂赏开华州城降梁',29,
      '杨师厚等至华州，知俊将聂赏开门降。知俊闻潼关不守，官军继至，苍黄失图，乙卯夜，举族奔岐。',
      [('杨师厚','率梁军至华州'),('聂赏','开华州城门降梁的刘知俊部将'),('刘知俊','乙卯夜携族奔岐')],
      when='909年六月乙卯夜刘知俊出奔；华州降此前',place='华州、岐',
      note='前句刘嗣业持诏招谕和刘知偃劝止赴行在均为事前动作；不将刘知俊想要谢罪写成已归梁。')
claim('event','event_zztj_267_0909_liuzhijun_flight','description',
      '朱温遣刘嗣业招谕刘知俊；刘知俊想轻骑赴行在谢罪，弟刘知偃阻止。',29,
      '帝遣刘知俊侄嗣业持诏指同州招谕知俊，知俊欲轻骑诣行在谢罪，弟知偃止之',
      '“欲”是未实现意图；刘嗣业身份来自“知俊侄”，暂不补父系具体位置。')
extra(new_liu_flight,'event','event_zztj_267_0909_liuzhijun_flight','description',
      '《新五代史》卷四十四亦记刘知俊携族归李茂贞。',
      '知俊遂奔于茂貞',29,'corroborates',
      '新史明言奔李茂贞，主书记“举族奔岐”；新史未明言携族，不把主书细节误引为新史。')
event('yang_shihou_changan','杨师厚沿南山趋长安，自西门入城',29,
      '杨师厚至长安，岐兵已据城，师厚以奇兵并南山急趋，自西门入，遂克之。',
      [('杨师厚','率梁军夺回长安的将领')],
      when='909年刘知俊出奔岐后；确日未载',place='长安',
      note='“已据城”的岐兵未在本段具名；不推定其全部结局。')
event('liu_xun_youguo','刘鄩权任佑国留后，岐王授刘知俊中书令',29,
      '庚申，以刘鄩权佑国留后。岐王厚礼刘知俊，以为中书令。',
      [('刘鄩','权任佑国留后'),('刘知俊','受岐王任中书令')],
      when='909年六月庚申刘鄩任命；岐方授职稍后条',place='长安、岐',
      note='刘鄩“权”任不写成正式长任；刘知俊在岐没有可镇藩镇，主书说只厚给俸禄。')
event('liu_shouguang_messages','刘守光向梁和晋分别上表致书，提出相矛盾的军事承诺',30,
      '刘守光遣使上表告捷，且言“俟沧德事毕，为陛下扫平并寇。”亦致书晋王，云欲与之同破伪梁。',
      [('刘守光','分别向梁、晋传达未来军事承诺'),('李存勖','收到刘守光致书的晋王')],
      when='909年六月后条；确日未载',
      note='两种说法为刘守光对不同对象的许诺，未作为实际出兵或同时结盟的证据。')

# 31–39: Wei Quanfeng's revolt, Zhou Ben's deployment, and other fronts.
event('wei_quanfeng_hongzhou','危全讽自称镇南节度使并率军攻洪州',31,
      '抚州刺史危全讽自称镇南节度使，帅抚、信、袁、吉之兵号十万攻洪州。',
      [('危全讽','自称节度使并进攻洪州')],
      when='909年六月后条；确日未载',place='洪州',
      note='“号十万”是所称兵数，不作核实人数；自称官号不等于受朝廷正式任命。')
event('liu_wei_requests_aid','刘威密报广陵求援，并以宴饮稳定洪州将吏',31,
      '淮南守兵才千人，将吏皆惧，节度使刘威密遣使告急于广陵，日召僚佐宴饮。',
      [('刘威','驻洪州求援的淮南节度使')],
      when='909年危全讽攻洪州时；确日未载',place='洪州、广陵',
      note='主书只说密使告急和宴饮，不推断刘威已击退围军。')
event('chu_gaoan_support','危全讽屯象牙潭求楚援，马殷遣苑玫会彭彦章围高安',31,
      '全讽闻之，屯象牙潭，不敢进，请兵于楚，楚王殷遣指挥使苑玫会袁州刺史彭彦章围高安以助全讽。',
      [('危全讽','屯象牙潭并向楚求援'),('马殷','遣苑玫助危全讽的楚王'),('苑玫','与彭彦章会兵围高安'),('彭彦章','袁州刺史，参与围高安')],
      when='909年危全讽攻洪州后；确日未载',place='象牙潭、高安',
      note='“不敢进”是主书对其驻军的描述；楚兵助围高安不等于楚直接进攻洪州。')
event('zhou_ben_command','严可求荐周本，徐温任其率七千兵救高安',32,
      '徐温问将于严可求，可求荐周本。乃以本为西南面行营招讨应援使，将兵七千救高安。',
      [('徐温','向严可求问将并任周本'),('严可求','推荐周本'),('周本','受任西南面行营招讨应援使')],
      when='909年危全讽进军后；确日未载',place='高安',
      note='周本自称先前苏州败因“主将权轻”，属其解释，不能据此改写已发布苏州战果。')
claim('event','event_zztj_267_0909_zhou_ben_command','description',
      '周本率军疾进象牙潭，途经洪州时未停留受犒。',32,
      '乃疾趣象牙潭。过洪州。刘威欲犒军，本不肯留',
      '其“楚人为声援”是周本的判断，后续战役结果见第40段。')
extra(new_jiangxi,'event','event_zztj_267_0909_zhou_ben_command','description',
      '《新五代史》卷六十一亦记严可求荐周本、周本请兵七千攻危全讽。',
      '可求薦周本，時本方攻蘇州敗歸',32,'corroborates',
      '新史概述出兵和象牙潭战事，主书第32段只记任命与进军。')
event('liu_shouguang_yanwang','后梁封刘守光为燕王',33,
      '秋，七月，甲子，以刘守光为燕王。',
      [('刘守光','获封燕王')],when='909年七月甲子',
      note='封号是梁廷授予，不以此推定其完全服从梁。')
event('danzhou_recovered','梁军收复丹州并擒王行思',34,
      '梁兵克丹州，擒王行思。',
      [('王行思','丹州事变后被梁军所擒')],when='909年七月条；确日未载',place='丹州',
      note='接第28段丹州事变；此段未明实际统兵者。')
event('lizhou_mutiny','商州李稠欲带民西走，被将吏杀，李玫被推主州事',35,
      '商州刺史李稠驱士民西走，将吏追斩之，推都押牙李玫主州事。',
      [('李稠','试图带商州士民西走而被杀'),('李玫','被将吏推主商州')],
      when='909年七月条；确日未载',place='商州',
      note='原文只说将吏追斩，不具名行凶者；“主州事”非正式节度使封授。')
event('youguo_renamed','后梁改佑国军为永平军',36,
      '庚午，改佑国军曰永平。',when='909年七月庚午',
      note='军号更改不等于辖境发生变动。')
event('jin_raids_jinzhou','河东兵袭晋州，抄掠至尧祠后撤离',37,
      '河东兵寇晋州，抄掠至尧祠而去。',
      when='909年七月条；确日未载',place='晋州、尧祠',
      note='主书不具名将领，不能因“河东兵”推定李存勖亲征。')
event('liang_emperor_ill','朱温由陕州返洛阳后卧病',38,
      '癸酉，帝发陕州，乙亥，至洛阳，寝疾。',
      [('朱温','返洛阳后患病的后梁皇帝')],
      when='909年七月癸酉启程、乙亥至洛阳',place='陕州、洛阳',
      note='“寝疾”记当时患病，不凭后见推断病名。')
event('xiangzhou_mutiny','襄州王求等牙兵杀留后王班',39,
      '戊寅，谪求戍西境，是夕，作乱，杀班',
      [('王求','被贬戍后参与襄州军乱'),('王班','被军乱杀害的襄州留后')],
      when='909年七月戊寅夜',place='襄州',
      note='“初”引入王班受任和杨师厚预警的前情，确年未另定；军乱发生于本段戊寅夜。')
event('liu_qi_flees','乱军推刘玘为留后，刘玘佯从后离城',39,
      '推都指挥使雍丘刘玘为留后。玘伪从之，明日，与指挥使王延顺逃诣帝所。',
      [('刘玘','被推为留后，佯从后逃往梁帝处'),('王延顺','随刘玘离开襄州')],
      when='909年七月戊寅翌日',place='襄州',
      note='《旧五代史》刘玘传说其翌日伏甲杀乱将，与《通鉴》“逃诣帝所”不合，两说并列。')
extra(old_liuqi,'event','event_zztj_267_0909_liu_qi_flees','description',
      '《旧五代史》卷六十四记刘玘佯从军乱，翌日伏甲斩乱将。',
      '玘詭從之，翌日受賀，衙庭享士，伏甲幕下，盡斬其亂將',39,'conflicts',
      '主书作刘玘翌日与王延顺逃赴帝所；两种后续不可合成同一行动。')
event('li_hong_xiangzhou','乱军奉李洪为襄州留后并附蜀，房州杨虔亦附蜀',39,
      '乱兵奉平淮指挥使李洪为留后，附于蜀。未几，房州刺史杨虔亦叛附于蜀。',
      [('李洪','被乱军奉为襄州留后并附蜀'),('杨虔','随后以房州附蜀')],
      when='909年七月军乱后及未几；确日未载',place='襄州、房州',
      note='“未几”表后续但未给日数，房州附蜀与襄州军乱分支区别。')

# 40: Xiangyatan and multiple distinct consequences, including an August transition.
event('xiangyatan_battle','周本于象牙潭击溃危全讽军并擒危全讽',40,
      '庚辰，周本隔溪布陈，先使羸兵尝敌。全讽兵涉溪追之，本乘其半济，纵兵击之，全讽兵大溃，自相蹂藉，溺水死者甚众，本分兵断其归路，擒全讽及将士五千人。',
      [('周本','率淮南军于象牙潭破危全讽'),('危全讽','战败被俘')],
      when='909年七月庚辰',place='象牙潭',
      note='“五千人”为主书记载的被俘将士数，死者“甚众”不可另换精确数。')
extra(new_jiangxi,'event','event_zztj_267_0909_xiangyatan_battle','description',
      '《新五代史》卷六十一亦记周本在象牙潭战败危全讽并将其擒获。',
      '戰于象牙潭，敗之，執全諷、彥章',40,'corroborates',
      '新史将危全讽、彭彦章同句概述，主书详细描述先擒危全讽再取袁州执彭彦章。')
event('yuanzhou_taken','周本乘胜攻取袁州、执彭彦章，并进攻吉州',40,
      '乘胜克袁州，执刺史彭彦章，进攻吉州',
      [('周本','乘胜取袁州并进攻吉州'),('彭彦章','袁州刺史，被俘')],
      when='909年七月象牙潭战后；确日未载',place='袁州、吉州',
      note='“进攻吉州”不是已攻克吉州；与象牙潭战事分阶段。')
event('rao_xin_shift','陶雅遣陶敬昭、徐章袭饶信，危仔倡请降、唐宝弃饶州',40,
      '歙州刺史陶雅使其子敬昭及都指挥使徐章将兵袭饶、信，信州刺史危仔倡请降，饶州刺史唐宝弃城走。',
      [('陶雅','遣军袭饶、信的歙州刺史'),('陶敬昭','陶雅之子，率兵袭饶信'),('徐章','与陶敬昭率军袭饶信'),('危仔倡','信州刺史，请降'),('唐宝','饶州刺史，弃城离去')],
      when='909年七月象牙潭战后；确日未载',place='饶州、信州',
      note='危仔倡先请降、后因淮南军将到而逃吴越，不将请降等同于最终留在信州。')
B['person_relationships'].append(dict(key='relationship_person_陶雅_person_陶敬昭_父亲',
    person_a_key=people['陶雅'],person_b_key=people['陶敬昭'],relation_type='父亲',
    description='陶雅是陶敬昭的父亲。',status='draft'))
claim('person_relationship','relationship_person_陶雅_person_陶敬昭_父亲','description',
      '陶雅是陶敬昭的父亲。',40,'陶雅使其子敬昭',
      '“其子”明载父子关系，未另推其政治立场。')
event('shanggao_chu_defeat','米志诚、吕师造在上高击败楚将苑玫',40,
      '行营都指挥使米志诚、都尉吕师造等败苑玫于上高。',
      [('米志诚','淮南将领，于上高击败苑玫'),('吕师造','淮南都尉，参与上高战'),('苑玫','上高战败的楚将')],
      when='909年七月象牙潭战后；确日未载',place='上高',
      note='上高战与象牙潭战为不同交战，不能合写成同一地点。')
event('peng_gan_chu','彭玕率众奔楚，马殷任其郴州刺史并与马希范结姻',40,
      '吉州刺史彭玕帅众数千人奔楚，楚王殷表玕为郴州刺史，为子希范娶其女。',
      [('彭玕','失吉州后率众投楚，获荐郴州刺史'),('马殷','接纳彭玕并安排婚姻的楚王'),('马希范','迎娶彭玕之女')],
      when='909年七月战后；确日未载',place='吉州、楚',
      note='“数千人”为主书记数；彭玕之女未具名，不创空泛人物节点或配偶边。')
event('xinzhou_dispatch_and_flight','淮南任张景思知信州并派骨言送任，危仔倡转投吴越',40,
      '淮南以左先锋指挥使张景思知信州，遣行营都虞候骨言将兵五千送之。危仔倡闻兵至，奔吴越，吴越王镠以仔倡为淮南节度副使，更其姓曰元氏。',
      [('张景思','受淮南任命知信州'),('骨言','领兵护送张景思'),('危仔倡','闻兵至后离信州投吴越，后改元姓'),('钱镠','接纳危仔倡并为其改姓的吴越王')],
      when='909年七月象牙潭战后；确日未载',place='信州、吴越',
      note='危仔倡与改姓后的元氏为同一人；原人稳定key保留，确切新名未给，不另造“元仔倡”实体。')
extra(new_yuan,'event','event_zztj_267_0909_xinzhou_dispatch_and_flight','description',
      '《新五代史》卷六十七亦记危仔倡奔钱镠，钱镠改其姓为元。',
      '信州危仔倡奔於鏐，鏐惡其姓，改曰元',40,'corroborates',
      '新史以“楊渥”概括此役胜方，但杨渥已于908年死；只取其关于危仔倡改姓的书证。')
event('wei_quanfeng_released','危全讽被送广陵，杨隆演念旧德释之',40,
      '危全讽至广陵，弘农王以其尝有德于武忠王，释之，资给甚厚。',
      [('危全讽','被送广陵后获释'),('杨隆演','因危全讽旧德而释放他的弘农王')],
      when='909年七月象牙潭战后；确日未载',place='广陵',
      note='“尝有德于武忠王”为旧事，确年未载；本段只记获释及资给。')
extra(new_jiangxi,'event','event_zztj_267_0909_wei_quanfeng_released','description',
      '《新五代史》卷六十一亦记危全讽昔日资助吴军，故被释而未杀。',
      '昔先王攻趙鍠，全諷屢饟給吳軍。」乃釋不殺',40,'adds',
      '新史说明议释理由，与主书“有德于武忠王”可并列，不把其追叙定为909年新发生。')
event('lu_guangchou_dual_ties','卢光稠八月以虔州附淮南，同时遣使附梁',40,
      '八月，虔州刺史卢光稠以州附于淮南。于是江西之地尽入于杨氏。光稠亦遣使附于梁。',
      [('卢光稠','以虔州归淮南，同时遣使示附梁')],
      when='909年八月',place='虔州',
      note='“江西之地尽入杨氏”为主书概述；卢光稠又遣使附梁，不能解作单一排他归属或精确地图边界。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(26,41):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷267开平三年第26—40段连续处理；刘知俊出奔、襄州军乱和江西战事按阶段拆分，异文原字保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=267,year=909,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(26,41)],next_paragraph=Q[41]['id'],
    coverage='卷267开平三年第26—40段连续处理；潼关长安局势、刘知俊出奔、危全讽起兵与象牙潭战及江西后续。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
