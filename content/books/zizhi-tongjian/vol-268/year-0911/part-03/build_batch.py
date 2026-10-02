"""Curate Tongjian 268, year 911, consecutive paragraphs 21-33."""
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
main1 = 'tongjian-268-911-autumn-winter'
old_salt = 'jiuwudaishi-006-yanzhou-salt'
new_lingnan = 'xinwudaishi-065-lingnan-expansion'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0911-p021-p033',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-02/sources/library' / main1, '71e96ea8', '司马光等'),
    (old_salt, P / 'sources/library' / old_salt, '51d80c73', '薛居正等'),
    (new_lingnan, P / 'sources/library' / new_lingnan, '51d80c73', '欧阳修'),
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
primary_texts = {key: (source_dirs[key] / 'source.txt').read_text() for key in (main1,)}
for n in range(21, 34):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in primary_texts[main1], n

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
           '王景仁':'王茂章','张宗奭':'张全义','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化元年（911）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0911_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,):
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

event('duan_mingyuan_gifts', '朱温至获嘉，段明远馈献丰备', 21,
      '怀州刺史开封段明远妹为美人。戊子，帝至获嘉，明远馈献丰备，帝悦。',
      [('段明远','因妹妹为梁帝美人而馈献丰备的怀州刺史'),('朱温','至获嘉并受馈献的梁帝')],
      when='911年十一月戊子',place='获嘉',
      note='段明远之妹未具姓名，不另造人物；“帝悦”是主书描写，不推官职赏赐。')

event('gaowanjin_saltzhou', '高万金攻盐州，高行存降', 22,
      '庚寅，保塞节度使高万兴奏遣都指挥使高万金将兵攻盐州，刺史高行存降。',
      [('高万兴','奏报遣将攻盐州的节度使'),('高万金','率兵攻盐州的都指挥使'),('高行存','向梁方投降的盐州刺史')],
      when='911年十一月庚寅奏报',place='盐州',
      note='“庚寅”为奏报日；旧五代史另称本月五日收盐州，不强定攻城当日为庚寅。')
claim('event','event_zztj_268_0911_gaowanjin_saltzhou','description',
      '《旧五代史》卷六记高万金收盐州、高行存降，系为该月五日。',22,
      '高萬金統領兵士，今月五日收鹽州，偽刺史高行存泥首來降。',
      '“今月五日”为旧书奏报中的日期；与主书庚寅奏报日保留不同精度。',old_salt,'adds')

event('zhu_wen_relapse_luoyang', '朱温壬辰抵洛阳，疾病复发', 23,
      '壬辰，帝至洛阳，疾复作。',
      [('朱温','返洛阳后病情复作的梁帝')],
      when='911年十一月壬辰',place='洛阳',note='疾病性质主书未说明。')

event('shu_jinniu_victory', '王宗弼金牛败岐军、拔十六寨并擒郭存', 24,
      '蜀王宗弼败岐兵于金牛，拔十六寨，俘斩六千馀级，擒其将郭存等。',
      [('王宗弼','率蜀军在金牛击败岐军'),('郭存','被蜀军擒获的岐将')],
      when='911年十一月丙申前；确日未载',place='金牛',
      note='俘斩六千余级为主书战果；“蜀王宗弼”指蜀将王宗弼，不误作蜀主王建。')
event('shu_huangniuchuan_victory', '王宗鐬与许存（王宗播）于黄牛川败岐军', 24,
      '丙申，王宗钅岁、王宗播败岐兵于黄牛川，擒其将苏厚等。',
      [('王宗钅岁','率蜀军在黄牛川胜岐的王宗鐬'),('王宗播','率蜀军在黄牛川胜岐的许存'),('苏厚','被蜀军擒获的岐将')],
      when='911年十一月丙申',place='黄牛川',
      note='底本“宗钅岁”为拆字，复用王宗鐬；王宗播是已发布许存的别名，复用其UUID。')
event('shu_anyuan_relief', '王建至兴元，蜀援军与安远守军夹击岐军解围', 24,
      '丁酉，蜀主自利州如兴元，援军既集，安远军望其旗，王宗侃等鼓噪而出，与援军夹攻岐兵，大破之，拔二十一寨，斩其将李廷志等。己亥，岐兵解围遁去。',
      [('王建','率蜀援军赴兴元'),('王宗侃','率安远守军出城夹击岐军'),('李廷志','被蜀军斩杀的岐将')],
      when='911年十一月丁酉夹击、己亥岐军解围',place='兴元、安远军',
      note='二十一寨与斩李廷志为主书战果；己亥才明确记岐军解围遁去。')
event('tang_daoxi_xiegu_ambush', '唐道袭预伏斜谷再次破岐兵', 24,
      '唐道袭先伏兵于斜谷邀击，又破之。庚子，蜀主西还。',
      [('唐道袭','预伏斜谷截击岐军'),('王建','庚子西还的蜀主')],
      when='911年十一月己亥前后伏击、庚子蜀主西还',place='斜谷、兴元',
      note='“先伏兵”为事前布置，具体截击日未载；不与前一段斜谷救援战擅自合并。')

event('qi_liu_zhijun_reassigned', '石简颙谗刘知俊，李茂贞夺其兵后杀石简颙', 25,
      '岐王左右石简颙谗刘知俊于岐王，王夺其兵。李继崇言于王曰：“知俊壮士，穷来归我，不宜以谗废之。”王为之诛简颙以安之。',
      [('石简颙','谗刘知俊后被岐王杀'),('刘知俊','被岐王夺兵后获安抚'),('李茂贞','夺兵并处死石简颙的岐王'),('李继崇','为刘知俊进言的岐将')],
      when='911年十一月庚子后；确日未载',place='岐',
      note='岐王先夺兵、后杀进谗者；不把刘知俊写作被杀。')
event('liu_zhijun_qinzhou', '李继崇召刘知俊举家居秦州', 25,
      '继崇召知俊举族居于秦州。',
      [('李继崇','招刘知俊举家迁秦州'),('刘知俊','举家迁秦州的岐将')],
      when='911年石简颙被杀后；确日未载',place='秦州')

event('yan_attacks_rongcheng', '刘守光率二万兵攻易定容城，王处直向晋告急', 26,
      '戊申，燕主守光将兵二万寇易定，攻容城。王处直告急于晋。',
      [('刘守光','率燕兵进攻容城'),('王处直','向晋告急的义武王')],
      when='911年十一月戊申',place='易定、容城',
      note='二万为主书燕兵数；“告急”不等于晋援兵已到。')

event('ma_cong_yongshun', '后梁任马賨为永顺节度使、同平章事', 27,
      '十二月，乙卯，以朗州留后马賨为永顺节度使、同平章事。',
      when='911年十二月乙卯',place='朗州、永顺军',
      note='马賨与904年已发布人物及910年误拆人物同一身份；待合并既有UUID后补人物参与关系，本批不再新增第三条人物。')

event('lu_yanchang_killed', '黎球杀卢延昌并自立，谭全播称疾得免', 28,
      '镇南留后卢延昌游猎无度，百胜军指挥使黎球杀之，自立；将杀谭全播，全播称疾请老，乃免。',
      [('卢延昌','被黎球杀害的镇南留后'),('黎球','杀卢延昌并自立的百胜军指挥使'),('谭全播','称疾请老而免遭黎球杀害')],
      when='911年十二月丙辰前；确日未载',place='虔州',
      note='“游猎无度”为主书评价；全播未被杀。')
event('li_qiu_appointment_death', '梁授黎球虔州防御使，黎球旋卒、李彦图代知州', 28,
      '丙辰，以球为虔州防御使。未几，球卒，牙将李彦图代知州事，全播愈称疾笃。',
      [('黎球','获授防御使后不久去世'),('李彦图','代知虔州事的牙将'),('谭全播','继续称病的虔州旧臣')],
      when='911年十二月丙辰任命；黎球卒于未几',place='虔州',
      note='“未几”不换算确日；李彦图为代知州事，不写已正式受梁节度使。')
event('liu_yan_takes_shaozhou', '刘岩攻下韶州，廖爽奔楚获任永州刺史', 28,
      '刘岩闻全播病，发兵攻韶州，破之，刺史廖爽奔楚，楚王殷表为永州刺史。',
      [('刘岩','派兵攻取韶州'),('廖爽','失韶州后奔楚、获马殷表任'),('马殷','表廖爽为永州刺史')],
      when='911年十二月丙辰后；确日未载',place='韶州、楚、永州',
      note='“表为”是马殷奏表，不擅改为朝廷已批准任命。')

event('shu_to_chengdu_december', '王建丁巳到成都', 29,
      '丁巳，蜀主至成都。', [('王建','返回成都的前蜀君主')],
      when='911年十二月丁巳',place='成都')

event('qu_mei_jinghai', '后梁任曲美为静海节度使', 30,
      '戊午，以静海留后曲美为节度使。',
      [('曲美','由静海留后获授节度使')],when='911年十二月戊午',place='静海军')

event('yao_yanzhang_ningyuan', '后梁依马殷请任姚彦章为宁远副使、权知容州', 31,
      '癸亥，以静江行军司马姚彦章为宁远节度副使，权知容州，从楚王殷之请也。',
      [('姚彦章','获任宁远节度副使、权知容州'),('马殷','请授姚彦章的楚王')],
      when='911年十二月癸亥',place='容州',
      note='“从楚王殷之请”说明梁廷依马殷请授，姚彦章原职为静江行军司马。')
event('liu_yan_takes_rongguan', '刘岩攻容州，姚彦章迁民携府藏奔长沙，刘岩取容管高州', 31,
      '刘岩遣兵攻容州，殷遣都指挥使许德勋以桂州兵救之；彦章不能守，乃迁容州士民及其府藏奔长沙，岩遂取容管及高州。',
      [('刘岩','派兵攻容州并取得容管、高州'),('马殷','遣许德勋救容州'),('许德勋','率桂州兵救援'),('姚彦章','不能守容州，迁士民及府藏往长沙')],
      when='911年十二月癸亥后；确日未载',place='容州、容管、高州、长沙',
      note='先楚救援、再姚彦章迁撤、刘岩取得两地；不把迁民写作全城人口皆迁。')
claim('event','event_zztj_268_0911_liu_yan_takes_rongguan','description',
      '《新五代史》卷六十五也概述刘岩（该书作龑）夺取容管。',31,
      '龑取容管，逐巨昭',
      '新史是宽泛综述，称逐庞巨昭而主书本段记姚彦章弃守；属叙述重心及前后阶段差异，不据其改写主书本段人物。新史又称杀刘昌鲁，与主书910年刘昌鲁归楚相冲，另待考。',new_lingnan,'adds')

event('jin_attacks_yan_relief', '李存勖遣周德威率三万兵攻燕救易定', 32,
      '甲子，晋王遣蕃汉马步总管周德威将兵三万攻燕，以救易定。',
      [('李存勖','命周德威攻燕以救易定'),('周德威','率三万晋军攻燕')],
      when='911年十二月甲子',place='燕、易定',
      note='本段是遣军出攻，战果属于912年后续段落；三万为主书所载兵数。')

event('shu_pan_appointments', '王建任潘炕武泰节度使、潘峭内枢密使', 33,
      '是岁，蜀主以内枢密使潘炕为武泰节度使，炕从弟宣徽南院使峭为内枢密使。',
      [('王建','任命潘炕与潘峭的蜀主'),('潘炕','由内枢密使转武泰节度使'),('潘峭','由宣徽南院使转内枢密使')],
      when='911年是岁；确月日未载',place='前蜀',
      note='“从弟”只确认宗族晚辈同辈，不直接推为同胞弟。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21, 34):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷268乾化元年十一月至岁末第21—33段连续处理；马賨旧重复人物待合并，未新增。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=268, year=911,
    primary_source_key=main1, primary_source_keys=[main1],
    paragraphs=[Q[n]['id'] for n in range(21,34)],next_paragraph='zztj-v268-y0912-p001',
    coverage='卷268乾化元年十一月至岁末第21—33段，蜀岐收兵、燕晋攻守、虔韶容州变局。',
    supplements=supplements,status=status,
    textual_reviews=[{'paragraph_id':Q[27]['id'],'note':'马賨在904与910旧批次有两个公开UUID，实为同一人；本段先录事件与原文，不增第三个实体，待审计合并后补参与边。'},
                     {'paragraph_id':Q[31]['id'],'note':'《新五代史》卷65宽泛记刘龑取容管、逐庞巨昭，并称杀刘昌鲁，与《通鉴》910刘昌鲁归楚异；时间/身份待纸本核。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({key:len(value) for key,value in B.items() if isinstance(value,list)})
