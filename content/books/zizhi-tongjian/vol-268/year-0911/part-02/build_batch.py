"""Curate Tongjian 268, year 911, consecutive paragraphs 11-20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 34))
main1 = 'tongjian-268-911-summer-autumn'
main2 = 'tongjian-268-911-autumn-winter'
old_zhang = 'jiuwudaishi-006-zhang-estate'
new_yan = 'xinwudaishi-039-yan-emperor'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0911-p011-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, P / 'sources/library' / main1, '71e96ea8', '司马光等'),
    (main2, P / 'sources/library' / main2, '71e96ea8', '司马光等'),
    (old_zhang, P / 'sources/library' / old_zhang, '71e96ea8', '薛居正等'),
    (new_yan, P / 'sources/library' / new_yan, '71e96ea8', '欧阳修'),
]
source_dirs = {key: path for key, path, _, _ in specs}
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
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {key: (source_dirs[key] / 'source.txt').read_text() for key in (main1, main2)}
for n in range(11, 21):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in primary_texts[main1 if n <= 18 else main2], n

registry = {}
existing_relation_keys = set()
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    archived = json.loads(path.read_text())
    existing_relation_keys.update(row['key'] for row in archived['person_relationships'])
    for row in archived['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (path, row['name'])
        registry[row['name']] = row
aliases = {'吴越王镠':'钱镠','楚王殷':'马殷','蜀主':'王建',
           '王景仁':'王茂章','张宗奭':'张全义','王寂侃':'王宗侃','王宗播':'许存','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1, main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1, main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化元年（911）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0911_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1, main2):
        book = json.loads((source_dirs[source] / 'paragraph.json').read_text())['book']
        supplements.append(dict(claim_key=ck, source_book=book, primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=supplement_relation))
    return ck

def person(name, n, role, quote):
    name = aliases.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷268乾化元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=911):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0911_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '911年本段条；确日未载', dynasty='五代十国',
               description=title + '。', phases=[], location_name=place,
               location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown',
               location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',
               status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote,
          note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', row['time_original'], n, quote,
          '段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_268_0911_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key,
                                       role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key

def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    if key in existing_relation_keys:
        reused.add(key)
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

event('zhu_wen_zhang_estate_abuse', '朱温在张宗奭宅侵害其家妇女', 11,
      '辛丑，帝避暑于张宗奭第，乱其妇女殆遍。',
      [('朱温','在张宗奭宅侵害家眷的梁帝'),('张宗奭','宅第被梁帝占用的臣下')],
      when='911年七月辛丑起',place='张宗奭宅',
      note='“乱其妇女殆遍”为主书所载性侵害；受害者未具名，不虚构身份。张宗奭即张全义，复用已校实体。')
claim('event','event_zztj_268_0911_zhu_wen_zhang_estate_abuse','description',
      '《旧五代史》卷六也记梁帝辛丑至甲辰驻张宗奭私第，但未记侵害妇女情节。',11,
      '自辛丑幸會節坊張宗奭私第',
      '只印证驻宅时间地点；旧书对此事件的性侵害情节无记载，不用沉默当否证。',old_zhang,'corroborates')
event('zhang_jizuo_plot_stopped', '张继祚欲弑朱温，张全义劝止', 11,
      '宗奭子继祚不胜愤耻，欲弑之。宗奭止之曰：“吾家顷在河阳，为李罕之所围，啖木屑以度朝夕，赖其救我，得有今日，此恩不可忘也。”乃止。',
      [('张继祚','因家眷受害欲弑朱温'),('张宗奭','以旧恩劝止其子的张全义'),('朱温','张继祚意欲刺杀但未遂的梁帝')],
      when='911年七月辛丑至甲辰间',place='张宗奭宅',
      note='谋杀被劝止，没有实施；张全义所说往事为其引语，不定为当年事件。')
relation('张全义','张继祚','父亲',11,'宗奭子继祚不胜愤耻',
         '“宗奭”是张全义赐名，原文明示继祚为其子。')
event('zhu_wen_palace_return', '朱温甲辰离张宅返宫', 11,
      '甲辰，还宫。', [('朱温','从张宅返宫的梁帝')],
      when='911年七月甲辰',place='后梁宫',note='接前文张宗奭宅居留。')

event('jin_zhao_chengtian_meeting', '王镕因梁军驻邢州忧惧，与李存勖会承天军', 12,
      '赵王镕以杨师厚在邢州，甚惧，会晋王于承天军。晋王谓镕父友也，事之甚恭。',
      [('王镕','与晋王会谈的赵王'),('李存勖','恭敬接待王镕的晋王'),('杨师厚','驻邢州令赵王忧惧的梁将')],
      when='911年七月后；确日未载',place='承天军',
      note='“父友”指王镕是晋王父亲的旧友，不推成宗亲。')
event('jin_zhao_betrothal', '李存勖与王镕结盟，许以女嫁其幼子昭诲', 12,
      '镕捧卮为寿，谓晋王为四十六舅。镕幼子昭诲从行，晋王断衿为盟，许妻以女。由是晋、赵之交遂固。',
      [('王镕','与晋王结盟并带幼子同行'),('李存勖','断衿结盟并许女于昭诲'),('王昭诲','被允诺婚配的赵王幼子')],
      when='911年承天军会见时',place='承天军',
      note='原文仅“许妻以女”，属订婚允诺，不记录已经成婚；“四十六舅”为当场称谓，不建实际舅甥关系。')
relation('王镕','王昭诲','父亲',12,'镕幼子昭诲从行',
         '原文明言昭诲是王镕幼子；长幼相对其他子未详。')

event('wang_jian_chengdu_return', '王建八月庚申回成都', 13,
      '八月，庚申，蜀主至成都。',
      [('王建','从西行路线返成都的蜀主')],when='911年八月庚申',place='成都')

event('sun_he_executed', '孙鹤反对刘守光称帝，被处死', 14,
      '孙鹤曰：“沧州之破，鹤分当死，蒙王生全，以至今日，敢爱死而忘恩乎！窃以为今日之帝未可也。”守光怒，伏诸质上，令军士C061而啖之。',
      [('孙鹤','谏止称帝而遭刘守光处死'),('刘守光','因谏言处死孙鹤的燕王')],
      when='911年八月甲子称帝前',place='燕',
      note='底本C061是疑似损字编码，不据此复原具体刑法；后文明记“寸斩之”，死亡可确认。')
claim('event','event_zztj_268_0911_sun_he_executed','description',
      '主书续记刘守光命堵孙鹤口后寸斩。',14,
      '守光命以土窒其口，寸斩之。',
      '该句确认孙鹤被杀；具体损字C061仍待纸本校。')
event('yan_emperor_foundation', '刘守光甲子称帝，国号大燕、改元应天', 14,
      '甲子，守光即皇帝位。国号大燕，改元应天。',
      [('刘守光','自立为大燕皇帝')],when='911年八月甲子',place='燕',
      note='与第8段谋称帝区分；此处才是正式即位。')
claim('event','event_zztj_268_0911_yan_emperor_foundation','description',
      '《新五代史》卷三十九也记刘守光乾化元年八月自号大燕皇帝、改元应天。',14,
      '守光遂以梁乾化元年八月，自號大燕皇帝，改元曰應天',
      '新史只到月份，主书给甲子日；两书记时精度不同。',new_yan,'corroborates')
event('yan_first_ministers', '刘守光任王瞳、刘涉、史彦群为燕廷官员', 14,
      '以梁使王瞳为左相，卢龙判官刘涉为右相，史彦群为御使大夫。',
      [('刘守光','任命燕廷官员'),('王瞳','梁使获任燕左相'),('刘涉','获任燕右相的卢龙判官'),('史彦群','获任燕御使大夫')],
      when='911年八月甲子即位后',place='燕',
      note='《新五代史》作右相“齐涉”，与主书刘涉姓名不同，不自动合并；两书分别保留。')
claim('event','event_zztj_268_0911_yan_first_ministers','description',
      '《新五代史》卷三十九作王瞳、齐涉为左右相。',14,
      '以王瞳、齊涉為左右相。',
      '“齐涉”与主书“刘涉”姓名冲突，先并列异说，不用繁简转换强并。',new_yan,'conflicts')
event('khitan_pingzhou', '刘守光受册当日契丹攻陷平州', 14,
      '受册之日，契丹陷平州，燕人惊扰。',
      [('刘守光','受册时平州失陷的燕主')],
      when='911年八月甲子受册之日',place='平州',
      note='主书称契丹陷平州，未记具名统帅；不推定刘守光个人守城。')

event('qingni_ridge_defeat', '岐军在青泥岭大败蜀军，王宗浩逃亡溺死', 15,
      '岐王使刘知俊、李继崇将兵击蜀，乙亥，王宗侃、王宗贺、唐道袭、王宗绍与之战于青泥岭，蜀兵大败，马步使王宗浩奔兴州，溺死于江，道袭奔兴元。',
      [('李茂贞','遣刘知俊、李继崇攻蜀'),('刘知俊','率岐军于青泥岭胜蜀'),('李继崇','率岐军于青泥岭胜蜀'),('王宗侃','率蜀军战败'),('王宗贺','率蜀军战败'),('唐道袭','败后奔兴元'),('王宗绍','参与蜀军战斗'),('王宗浩','败后奔兴州并溺死')],
      when='911年八月乙亥',place='青泥岭、兴州',
      note='王宗浩死于逃亡渡江，不记作战场直接被杀。')
event('anyuan_siege', '蜀军收兵守安远，岐将刘知俊、李继崇围城', 15,
      '先是，步军都指挥使王宗绾城西县，号安远军，宗侃、宗贺等收散兵走保之，短俊、继崇追围之。',
      [('王宗绾','此前筑西县为安远军'),('王宗侃','收败兵守安远'),('王宗贺','收败兵守安远'),('刘知俊','率岐军追围安远'),('李继崇','率岐军追围安远')],
      when='911年青泥岭败后；筑城为更早前事',place='西县、安远军',
      note='“先是”筑城不定在本日；底本“短俊”据前文刘知俊及《通鉴》音注本校为同人，原字保留。')
event('shu_relief_anyuan', '王建遣王宗鐬、王宗播救安远，蜀军于明珠曲及凫口胜岐', 15,
      '蜀主以昌王宗钅岁为应援招讨使，定戎团练使王宗播为四招讨马步都指挥使，将兵救安远军，壁于廉、让之间，与唐道袭合击岐兵，大破之于明珠曲。明日又战于凫口，斩其成州刺史李彦琛。',
      [('王建','任命援军统帅的蜀主'),('宗钅岁','以昌王身份率援军的王宗鐬'),('王宗播','任援军马步都指挥使'),('唐道袭','与援军合击岐军'),('李彦琛','次日在凫口战死的岐方成州刺史')],
      when='911年八月乙亥后；明珠曲战次日凫口战',place='安远军、明珠曲、凫口',
      note='先明珠曲、后次日凫口；宗钅岁为底本拆字，复用王宗鐬。')

event('zhu_wen_northern_march', '朱温九月病稍缓后北巡，至相州因晋兵未出而止', 16,
      '九月，帝疾稍愈，闻晋、赵谋入寇，自将拒之。戊戌，以张宗奭为西都留守。庚子，帝发洛阳。甲辰，至卫州，方食，军前奏晋军已出井陉。帝遽命辇北趣邢洺，昼夜倍道兼行。丙午，至相州，闻晋兵不出，乃止。',
      [('朱温','病稍缓后率军北行'),('张宗奭','获任西都留守')],
      when='911年九月庚子离洛、丙午抵相州',place='洛阳、卫州、相州',
      note='“晋军已出井陉”出自军前奏报，后又闻晋兵不出；两种消息保留，不当实际晋军已出井陉。')
event('li_sian_demotion', '朱温削李思安官爵', 16,
      '相州刺史李思安不意帝猝至，落然无具，坐削官爵。',
      [('李思安','因未备接驾被削官爵的相州刺史'),('朱温','下令削官爵的梁帝')],
      when='911年九月丙午后',place='相州',note='处罚原因按主书所载，未推为军事败绩。')

event('qian_biao_flees_wu', '钱镖杀潘长、钟安德后奔吴', 17,
      '湖州刺史钱镖酗酒杀人，恐吴越王镠罪之，冬，十月，辛亥朔，杀都监潘长、推官钟安德，奔于吴。',
      [('钱镖','杀都监、推官后逃吴的湖州刺史'),('潘长','被钱镖杀的都监'),('钟安德','被钱镖杀的推官'),('钱镠','钱镖畏其治罪的吴越王')],
      when='911年十月辛亥朔',place='湖州、吴',
      note='此前“酗酒杀人”未具名，不虚构死者；本日两位具名遇害者分明。')

event('li_chengxun_to_yan', '李存勖遣李承勋贺燕，李承勋拒称臣', 18,
      '张承业请遣使致贺以骄之，晋王遣太原少尹李承勋往。承勋至幽州，用邻籓通使之礼。',
      [('张承业','建议遣使贺燕'),('李存勖','遣李承勋出使燕'),('李承勋','以邻藩礼赴幽州')],
      when='911年十月燕称帝后',place='幽州',
      note='晋方出使意图“以骄之”是张承业所议，李承勋实际坚持邻藩礼。')
claim('event','event_zztj_268_0911_li_chengxun_to_yan','description',
      '李承勋拒绝对燕称臣，刘守光终不能迫其屈服。',18,
      '承勋曰：“燕王能臣我王，则我请为臣，不然，有死而已！”守光竟不能屈。',
      '主书只说明未屈，不交代最终生死。')
claim('event','event_zztj_268_0911_li_chengxun_to_yan','description',
      '《新五代史》卷三十九另记刘守光杀李承勋。',18,
      '守光怒，殺之。',
      '主书在本段止于“不屈”，不明言杀；新史补记其死，待与其他二十四史互核。',new_yan,'adds')

event('shu_wang_cong_victory', '王琮败岐军擒李彦太，彭君集又破二寨', 19,
      '决云军虞候王琮败岐兵，执其将李彦太，俘斩三千五百级。乙卯，捉生将彭君集破岐二寨，俘斩三千级。',
      [('王琮','率蜀军败岐兵、擒李彦太'),('李彦太','被蜀军俘虏的岐将'),('彭君集','乙卯破岐二寨的蜀将')],
      when='911年十月乙卯及此前',place='蜀岐边境',
      note='三千五百、三千分别为两场战果，不能相加为同日一战；具体战场未载。')
event('shu_urgent_relief_xiegu', '王宗侃遣林思谔告急，王宗弼斜谷败刘知俊', 19,
      '王寂侃遣裨将林思谔自中巴间行至泥溪，见蜀主告急，蜀主命开道都指挥使王宗弼将兵救安远，及刘知俊战于斜谷，破之。',
      [('王寂侃','遣将告急的王宗侃'),('林思谔','间道赴泥溪向蜀主告急'),('王建','命王宗弼援安远'),('王宗弼','率援军在斜谷败刘知俊'),('刘知俊','在斜谷为蜀援军所败')],
      when='911年十月乙卯后；确日未载',place='中巴、泥溪、斜谷、安远',
      note='底本作“王寂侃”，《通鉴》另一电子本作“王宗侃”，与前文同一北路都统；复用王宗侃并留原字，纸本待核。')

event('liang_weixian_panic', '朱温北巡至魏县，闻晋赵南下传言引发军中逃亡', 20,
      '甲寅夜，帝发相州，乙卯，至洹水。是夜，边吏言晋、赵兵南下，帝即时进军，丙辰，至魏县。或告云：“沙陀至矣！”士卒恟惧，多逃亡，严刑不能禁。即而复告云无寇，上下始定。',
      [('朱温','接边报后进军魏县的梁帝')],
      when='911年十月甲寅至丙辰',place='相州、洹水、魏县',
      note='“晋赵兵南下”“沙陀至矣”均为当时军报或传言，后报无寇；不写成晋赵实际进攻魏县。')
event('liang_northern_return', '朱温北巡未遇晋赵主力，十一月壬午南还', 20,
      '帝以夹寨、柏乡屡失利，故力疾北巡，思一雪其耻，意郁郁，多躁忿，功臣宿将往往以小过被诛，众心益惧。既而晋、赵兵竟不出。十一月，壬午，帝南还。',
      [('朱温','因前败强行北巡、未遇晋赵主力而南还')],
      when='911年十一月壬午南还',place='魏县、洛阳方向',
      note='“屡失利”为主书回顾；本次晋赵主力未出，不能另造一场会战。')
event('feng_dao_escapes_yan', '冯道谏刘守光攻易定被囚，获释后奔晋任掌书记', 20,
      '燕主守光集将吏谋攻易定，幽州参军景城冯道以为未可，守光怒，系狱，或救之，得免。道亡奔晋，张承业荐于晋王，以为掌书记。',
      [('刘守光','因冯道反对攻易定而囚之'),('冯道','反对攻易定、获释后奔晋任掌书记'),('张承业','向晋王荐冯道'),('李存勖','任冯道为掌书记的晋王')],
      when='911年十一月壬午后、丁亥前',place='幽州、晋',
      note='攻易定为燕方筹划，本句尚未实际出兵。')
event('wang_chuzhi_requests_aid', '王处直丁亥向晋告难', 20,
      '丁亥，王处直告难于晋。',
      [('王处直','向晋告急的义武王')],when='911年十一月丁亥',place='易定、晋',
      note='告难与燕之后攻易定相接；本段未记晋军已抵。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11, 21):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷268乾化元年七月至十一月第11—20段连续处理；燕称帝、蜀岐战事及梁北巡分录。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=268, year=911,
    primary_source_key=main1, primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v268-y0911-p021',
    coverage='卷268乾化元年七月至十一月第11—20段，朱温张宅、晋赵盟约、燕称帝与蜀岐战。',
    supplements=supplements,status=status,
    textual_reviews=[{'paragraph_id':Q[14]['id'],'note':'燕右相主书刘涉，《新五代史》作齐涉，未合并；底本C061损字保留。新史另记李承勋出使后被杀，主书止于未屈。'},
                     {'paragraph_id':Q[15]['id'],'note':'“短俊”据本段前后文校识为刘知俊，原文不改。'},
                     {'paragraph_id':Q[19]['id'],'review_url':'https://zh.wikisource.org/zh-hans/資治通鑑_(胡三省音注)/卷268','note':'底本“王寂侃”，另一《通鉴》电子本作王宗侃，按同一北路都统复用；纸本待核。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({key:len(value) for key,value in B.items() if isinstance(value,list)})
