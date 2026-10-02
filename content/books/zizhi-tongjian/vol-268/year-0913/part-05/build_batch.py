"""Curate Tongjian 268, year 913, consecutive paragraphs 41-49."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 50))
main4 = 'tongjian-268-913-autumn'
old_autumn = 'jiuwudaishi-028-yan-autumn'
old_fall = 'jiuwudaishi-028-yan-fall'
new_succession = 'xinwudaishi-063-wang-zongyan'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0913-p041-p049',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main4, P.parent / 'part-04/sources/library' / main4, 'b8693d0e', '司马光等'),
    (old_autumn, P / 'sources/library' / old_autumn, 'e822361c', '薛居正等'),
    (old_fall, P / 'sources/library' / old_fall, 'e822361c', '薛居正等'),
    (new_succession, P / 'sources/library' / new_succession, 'e822361c', '欧阳修'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main4,)}
for n in range(41,50):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line']-1]
    assert any(row['text'] in text for text in primary_texts.values()),n

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
           '王景仁':'王茂章','张宗奭':'张全义','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
aliases.update({'元膺':'王宗懿','蜀主':'王建','帝':'朱友贞','硃友谦':'朱友谦',
                '鄴王':'杨师厚','晋王':'李存勖','守光':'刘守光',
                '行珪':'高行珪','行周':'高行周','嗣源':'李嗣源',
                '存矩':'李存矩','传瓘':'钱传瓘','传璙':'钱传璙',
                '吴越王镠':'钱镠','从珂':'李从珂','魏氏':'魏氏（李从珂母）'})
aliases.update({'刘光浚':'刘光濬','光浚':'刘光濬','李存审':'符存审',
                '王德明':'张文礼','赵王':'王镕','传瓘':'钱传瓘',
                '师厚':'杨师厚','守奇':'刘守奇','万进':'张万进'})
aliases.update({'元膺':'王宗懿','太子':'王宗懿','蜀主':'王建',
                '道袭':'唐道袭','宗翰':'王宗翰','宗侃':'王宗侃',
                '宗贺':'王宗贺','宗黯':'王宗黯','赵王镕':'王镕',
                '晋王':'李存勖','高季兴':'高季昌'})
aliases.update({'吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘',
                '传璙':'钱传璙','传瑛':'钱传瑛','蜀主':'王建',
                '宗衍':'王宗衍','宗辂':'王宗辂','宗杰':'王宗杰',
                '宗侃':'王宗侃','晋王':'李存勖','守光':'刘守光',
                '朱温':'朱温','王景仁':'王茂章'})
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main4,) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main4,):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化三年（913）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0913_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main4,):
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
                   description=f'《资治通鉴》卷268乾化三年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=913):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0913_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '913年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_268_0913_' + code + '_' + pk
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

event('yao_ji_chancellor', '姚洎由御史大夫任中书侍郎、同平章事', 41,
      '九月，甲辰，以御史大夫姚洎为中书侍郎，同平章事。',
      [('姚洎','由御史大夫升中书侍郎、同平章事')],
      when='913年九月甲辰',place='后梁')
event('liu_shouguang_shunzhou', '刘守光夜出复取顺州', 42,
      '燕主守光引兵夜出，复取顺州。',
      [('刘守光','率燕军夜出复取顺州')],
      when='913年九月；确日未载',place='顺州',
      note='顺州在本年正月已为晋取；“复取”指燕重新占据，不推定长期固守。')
claim('event','event_zztj_268_0913_liu_shouguang_shunzhou','description',
      '《旧五代史》卷二十八也记九月刘守光夜出陷顺州。',42,
      '九月，劉守光率眾夜出，遂陷順州。',
      '与主书年月、人物、地点一致。',old_autumn,'corroborates')
event('qian_attack_changzhou', '钱镠遣钱传瓘、传璙、传瑛攻吴常州并营潘葑', 43,
      '吴越王镠遣其子传瓘、传璙及大同节度使传瑛攻吴常州，营于潘葑。',
      [('钱镠','派三子率吴越军攻常州的吴越王'),('钱传瓘','受父钱镠派遣进攻常州'),('钱传璙','受父钱镠派遣进攻常州'),('钱传瑛','以大同节度使身份参与攻常州')],
      when='913年九月；确日未载',place='常州、潘葑',
      note='“其子”统领传瓘、传璙、传瑛；大同节度使为传瑛官号。')
event('xu_wen_counterattack_wuxi', '徐温急赴无锡，陈祐提议迂回，吴军夹击吴越军获胜', 43,
      '徐温曰：“浙人轻而怯。”帅诸将倍道赴之。至无锡，黑云都将陈祐言于温曰：“彼谓吾远来罢倦，未能战，请以所部乘其无备击之。”乃自他道出敌后，温以大军当其前，夹攻之，吴越大败，斩获甚众。',
      [('徐温','率吴军急赴无锡并正面夹击吴越军'),('陈祐','提出迂回并率黑云都从敌后攻击')],
      when='913年九月；确日未载',place='无锡、潘葑',
      note='“浙人轻而怯”是徐温战前判断，不作吴越军客观属性；原文仅称斩获甚众，未给人数。')
event('gao_jichang_fortifies_jingnan', '高季昌造战舰、修城堑并招聚亡命', 44,
      '高季昌造战舰五百艘，治城堑，缮器械，为攻守之具，招聚亡命，交通吴、蜀，朝廷浸不能制。',
      [('高季昌','在荆南造舰修城并与吴、蜀往来的将领')],
      when='913年前后持续举措；确日未载',place='荆南',
      note='“五百艘”为主书所记战舰数；“交通”只说明往来，不能推定已立正式同盟或签订条约。')
event('liu_shouguang_tanzhou_sortie', '刘守光率众夜出欲入檀州', 45,
      '冬，十月，己巳朔，燕主守光帅众五千夜出，将入檀州。',
      [('刘守光','率众夜出欲入檀州的燕主')],
      when='913年十月己巳朔',place='檀州',
      note='“将入”表示目的，不把抵达檀州视为主书已证实；旧书卷28作七百骑加五千步兵，人数口径不同。')
claim('event','event_zztj_268_0913_liu_shouguang_tanzhou_sortie','description',
      '《旧五代史》卷二十八作七百骑、步军五千夜入檀州。',45,
      '冬十月己巳朔，守光率七百騎、步軍五千夜入檀州。',
      '主书只作“众五千”，旧书细列骑与步军且谓已入檀州，人数及进程异说并列。',old_autumn,'conflicts')
event('zhou_dewei_defeats_sortie', '周德威迎击大败燕军，刘守光百余骑逃回幽州', 45,
      '庚午，周德威自涿州引兵邀击，大破之。守光以百馀骑逃归幽州，其将卒降者相继。',
      [('周德威','自涿州引兵邀击并大败燕军'),('刘守光','率百余骑逃回幽州的燕主')],
      when='913年十月庚午及其后',place='涿州、幽州',
      note='主书没有战亡具体人数；逃归幽州与其后部众陆续投降分开理解。')
claim('event','event_zztj_268_0913_zhou_dewei_defeats_sortie','description',
      '《旧五代史》卷二十八记周德威追击，并列八百五十名将吏、百五十匹马被获。',45,
      '德威追及，大敗之，獲大將李劉、張景紹及將吏八百五十人，馬一百五十匹。',
      '旧书具体俘获数作补证；主书未给数字，不并成阵亡数。',old_autumn,'adds')
event('pan_kang_succession_advice', '潘炕屡请再立前蜀太子，王建在王宗辂、王宗杰间权衡', 46,
      '蜀潘炕屡请立太子，蜀主以雅王宗辂类己，信王宗杰才敏，欲择一人立之。',
      [('潘炕','多次请王建立太子'),('王建','考虑王宗辂或王宗杰为储君'),('王宗辂','被王建考虑的雅王'),('王宗杰','被王建考虑的信王')],
      when='913年十月甲午前；具体起始待考',place='前蜀宫廷',
      note='“类己”“才敏”为王建或主书评价，不推成现代能力判断；这里只记录候选状态。')
event('xu_fei_lobbies_zongyan', '徐贤妃欲立王宗衍，遣唐文扆劝张格上表', 46,
      '郑王宗衍最幼，其母徐贤妃有宠，欲立其子，使飞龙使唐文扆讽张格上表请立宗衍。',
      [('王宗衍','受母徐贤妃支持的郑王'),('徐贤妃','推动其子王宗衍为太子的王建妃'),('唐文扆','奉徐贤妃意劝张格上表的飞龙使'),('张格','被劝上表请立王宗衍的官员')],
      when='913年十月甲午前；确日未载',place='前蜀宫廷',
      note='“有宠”是主书对王建喜爱的描述；立储游说是文本所载行动。')
relation('徐贤妃','王宗衍','母亲',46,'其母徐贤妃有宠，欲立其子，',
         '明确徐贤妃是王宗衍之母；关系方向为徐贤妃是王宗衍的母亲。')
event('zhang_ge_collects_signatures', '张格称有密旨向王宗侃等示表，众功臣署名', 46,
      '格夜以表示功臣王宗侃等，诈云受密旨，众皆署名。',
      [('张格','夜示请立王宗衍表并诈称密旨'),('王宗侃','在功臣中被展示表章者')],
      when='913年十月甲午前；确日未载',place='前蜀宫廷',
      note='“诈云受密旨”是主书断言；“众皆署名”不等于各功臣知情同谋。')
event('wang_jian_zongyan_crown', '王建在相者进言后立王宗衍为太子', 46,
      '蜀主令相者视诸子，亦希旨言郑王相最贵。蜀主以为众人实欲立宗衍，不得已许之，曰：“宗衍幼懦，能堪其任乎？”甲午，立宗衍为太子。',
      [('王建','在多方进言后册立王宗衍的蜀主'),('王宗衍','甲午受立的前蜀太子')],
      when='913年十月甲午',place='前蜀宫廷',
      note='相者“郑王相最贵”是占相言辞，不作为客观预测；“不得已”是主书对王建处境的叙述。')
claim('event','event_zztj_268_0913_wang_jian_zongyan_crown','description',
      '《新五代史》卷六十三亦记王建曾欲在王宗辂、王宗杰间择立，徐妃与唐文扆、张格推动王宗衍受立。',46,
      '元膺死，建以豳王宗輅貌類己，而信王宗傑於諸子最材賢，欲於兩人擇立之。而徐妃專寵，建老昏耄，妃與宦者唐文扆教相者上言衍相最貴，又諷宰相張格贊成之，衍由是得為太子。',
      '新书称“豳王宗辂”，主书作“雅王宗辂”；王爵异文及评价语分开保留。',new_succession,'conflicts')
event('pan_kang_retires', '潘炕再请致仕，王建许其退休并遇大疑仍咨询', 46,
      '受册华，潘炕以朝廷无事，称疾请老，蜀主不许，涕泣固请，乃许之。国有大疑，常遣使就第问之。',
      [('潘炕','因称疾请老获准退居第宅'),('王建','准潘炕请老，国有大疑仍遣使咨询')],
      when='913年十月甲午后；确日未载',place='前蜀',
      note='“受册华”底本文字疑讹，不能据此增添册礼细节；“常遣使”是后续持续行为。')
event('liu_yan_chu_marriage_proposal', '刘岩向楚求婚，楚王马殷允以女嫁之', 47,
      '岭南节度使刘岩求昏于楚，楚王许以女妻之。',
      [('刘岩','向楚王求婚的岭南节度使'),('马殷','同意以女儿许嫁刘岩的楚王')],
      when='913年十月至十一月前；确日未载',place='岭南、楚',
      note='主书只载允婚，未记女儿姓名、婚礼完成或确日；“昏”为底本通婚用字。')
event('liu_shouguang_khitan_no_aid', '卢龙诸属归晋，刘守光求契丹援而未获救', 48,
      '卢龙巡属皆入于晋，燕主守光独守幽州城，求援于契丹；契丹以其无信，竟不救。守光屡请降于晋，晋人疑其诈，终不许。',
      [('刘守光','独守幽州并向契丹求援、向晋请降的燕主')],
      when='913年十月至十一月前；持续经过',place='幽州、卢龙巡属',
      note='“契丹以其无信”是主书给出的拒援理由，未见契丹自述；晋方多次不许降，并非守光从未请降。')
event('liu_shouguang_promises_surrender', '刘守光称待晋王至幽州再开门投降，周德威转报', 48,
      '至是，守光登城谓周德威曰：“俟晋王至，吾则开门泥首听命。”德威使白晋王。',
      [('刘守光','向周德威作待晋王到来便开城的口头承诺'),('周德威','把刘守光口头承诺转报晋王')],
      when='913年十一月甲辰前；确日未载',place='幽州城',
      note='承诺不等于已投降，后续仍有交涉和攻城。')
event('jin_king_to_youzhou', '晋王命张承业权知军府并亲赴幽州', 48,
      '十一月，甲辰，晋王以监军张承业权知军府事，自诣幽州，辛酉，单骑抵城下，',
      [('李存勖','亲赴幽州并单骑抵城下的晋王'),('张承业','受命暂知晋军府事的监军')],
      when='913年十一月甲辰赴幽州、辛酉抵城下',place='幽州',
      note='“甲辰”记晋王赴幽州安排，“辛酉”记单骑抵城下；未自行换算公历日。')
event('jin_king_surrender_parley', '晋王李存勖与刘守光城下交涉并折弓矢为誓', 48,
      '谓守光曰：“硃温篡逆，余本欲与公合河朔五镇之兵兴复唐祚。公谋之不臧，乃效彼狂僭。镇、定二帅皆俯首事公，而公曾不之恤，是以有今日之役。丈夫成败须决所向，公将何如？”守光曰：“今日俎上肉耳，惟王所裁。”王悯之，与折弓矢为誓，曰：“但出相见，保无它也。”守光辞以它日。',
      [('李存勖','城下劝降并折弓矢为誓的晋王'),('刘守光','称听晋王裁处却推迟出城的燕主')],
      when='913年十一月辛酉',place='幽州城下',
      note='晋王引语含对朱温及刘守光的政治评价，按引语处理；刘守光仍未实际出降。')
event('li_xiaoxi_blocks_and_defects', '李小喜先阻刘守光出降，后越城归晋报城中力竭', 48,
      '先是，守光爱将李小喜多赞成守光之恶。言听计从，权倾境内。至是，守光将出降，小喜止之。是夕，小喜逾城诣晋军降，且言城中力竭。',
      [('李小喜','先阻燕主出降、当晚越城降晋的燕将'),('刘守光','被李小喜劝阻而未出降的燕主')],
      when='913年十一月辛酉晚',place='幽州城',
      note='“多赞成守光之恶”是主书追评；“城中力竭”为李小喜向晋军报告，不另作独立实测兵力事实。')
claim('event','event_zztj_268_0913_li_xiaoxi_blocks_and_defects','description',
      '《旧五代史》卷二十八也记李小喜阻刘守光当日出城，后当晚来归晋。',48,
      '帝單騎臨城邀守光，辭以他日，蓋為其親將李小喜所扼也。是夕，小喜來奔，',
      '旧书“盖为”是解释性口吻，主书作“小喜止之”；两书都记小喜当晚奔晋。',old_fall,'corroborates')
event('jin_takes_youzhou', '晋王四面攻克幽州并擒刘仁恭，刘守光携家逃离', 48,
      '壬戌，晋王督诸军四面攻城，克之，擒刘仁恭及其妻妾，守光帅妻子亡去。癸亥，晋王入幽州。',
      [('李存勖','督军攻克幽州并于癸亥入城的晋王'),('刘仁恭','幽州失守时被晋军擒获'),('刘守光','幽州失守后携妻儿逃离的燕主')],
      when='913年十一月壬戌攻克、癸亥入城',place='幽州',
      note='“妻子”古文指妻儿；主书此时刘守光逃走，尚未被擒，不能提前录入其被捕。')
claim('event','event_zztj_268_0913_jin_takes_youzhou','description',
      '《旧五代史》卷二十八同记壬戌攻城、擒刘仁恭，癸亥晋王入城。',48,
      '壬戌，梯童並進，軍士畢登，帝登燕丹塚以觀之。有頃，擒劉仁恭以獻。癸亥，帝入燕城，諸將畢賀。',
      '旧书“梯童”疑转录讹字，按攻城经过引用，不改写原字；主书“四面攻城”独立保留。',old_fall,'corroborates')
event('wang_jingren_lu_shou', '梁命王景仁领万余兵侵庐州、寿州', 49,
      '以宁国节度使王景仁为淮南西北行营招讨应接使，将兵万馀侵庐、寿。',
      [('王茂章','以王景仁之名领梁军万余侵庐、寿的宁国节度使')],
      when='913年十一月后、十二月前；确日未载',place='庐州、寿州',
      note='王景仁沿既有王茂章主体；万余为主书兵力估数。此段只有出兵，战斗见卷269下一段。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,50):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化三年九月至十一月第41—49段连续处理；梁楚蜀立储、晋燕幽州攻守及吴越吴战事分录。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=913,
    primary_source_key=main4,primary_source_keys=[main4],
    paragraphs=[Q[n]['id'] for n in range(41,50)],next_paragraph='zztj-v269-y0913-p001',
    coverage='卷268乾化三年九月至十一月第41—49段，梁蜀任官与立储、吴越吴常州战事、燕晋幽州终局及梁淮南出兵。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[45]['id'],'note':'刘守光夜出人数：通鉴作五千，旧五代史卷28作七百骑、五千步军；是否已入檀州进程措辞也不同。'},
      {'paragraph_id':Q[46]['id'],'note':'王宗辂王爵：通鉴作雅王，新五代史卷63作豳王；王宗衍相貌预言为史书中相者言辞，不作事实。底本“受册华”疑讹待核。'},
      {'paragraph_id':Q[48]['id'],'note':'十一月幽州攻守拆成六事：请降口头承诺、晋王赴城、城下交涉、小喜奔晋、攻城擒刘仁恭、刘守光逃。刘守光此段未被擒。'},
      {'paragraph_id':Q[49]['id'],'note':'王景仁复用既有王茂章主体；卷269第1段再记战斗，不前置战果。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
