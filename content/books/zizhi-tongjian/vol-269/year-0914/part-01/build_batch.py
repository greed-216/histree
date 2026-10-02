"""Curate Tongjian 269, year 914, consecutive paragraphs 1-4."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 17))
main1 = 'tongjian-269-913-december'
main2 = 'tongjian-269-914-spring'
old_annals = 'jiuwudaishi-028-liu-execution'
old_bio = 'jiuwudaishi-135-liu-end'
new_shu = 'xinwudaishi-063-gao-jichang'
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0914-p001-p004',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0913/part-01/sources/library' / main1, '8eb6cf39', '司马光等'),
    (main2, P / 'sources/library' / main2, '98ce861b', '司马光等'),
    (old_annals, P / 'sources/library' / old_annals, '98ce861b', '薛居正等'),
    (old_bio, P / 'sources/library' / old_bio, '98ce861b', '薛居正等'),
    (new_shu, P / 'sources/library' / new_shu, '98ce861b', '欧阳修'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main1,main2)}
for n in range(1,5):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line']-1]
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
aliases.update({'硃瑾':'朱瑾','硃景浮':'朱景浮','王景仁':'王茂章',
                '景仁':'王茂章','守光':'刘守光','晋王':'李存勖',
                '越王镕':'王镕','赵王镕':'王镕','仁恭':'刘仁恭'})
aliases.update({'镕':'王镕','晋王':'李存勖','守光':'刘守光',
                '仁恭':'刘仁恭','小喜':'李小喜','蜀主':'王建',
                '太子':'王宗衍','宗寿':'王宗寿','季昌':'高季昌',
                '成先':'王成先','张武':'张武'})
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·乾化四年（914）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_269_0914_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,main2):
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
                   description=f'《资治通鉴》卷269乾化四年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=914):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0914_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '914年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_269_0914_' + code + '_' + pk
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

event('wang_rong_banquet_liu', '王镕为晋王置宴，刘仁恭、刘守光暂脱械同席', 1,
      '春，正月，戊戌朔，赵王镕诣晋王行帐上寿置酒。镕愿识刘太师面，晋王命吏脱刘仁恭及守光械，引就席同宴。镕答其拜，又以衣服、鞍马、酒馔赠之，',
      [('王镕','赴晋王行帐祝寿设宴并赠刘仁恭父子衣马酒食'),('李存勖','命暂脱刘仁恭父子枷械同宴的晋王'),('刘仁恭','以刘太师身份暂脱械同宴'),('刘守光','暂脱械与晋王赵王同宴')],
      when='914年正月戊戌朔',place='晋王行帐',
      note='“脱械”是宴席时暂时解械，不记作释放或赦免；旧五代史卷28补王镕二子在场。')
claim('event','event_zztj_269_0914_wang_rong_banquet_liu','description',
      '《旧五代史》卷二十八亦记正月戊戌王镕上寿、刘仁恭与刘守光暂脱械同宴。',1,
      '王鎔以履新之日，與其子昭祚、昭誨奉觴上壽置宴。鎔啟曰：「燕主劉太師頃為鄰國，今欲挹其風儀，可乎？」帝即命主者破械，引仁恭、守光至，與之同宴，',
      '旧书补王镕二子姓名，主书未具名；后称帝指此时晋王李存勖。',old_annals,'adds')
event('jin_wang_rong_hunt', '晋王与王镕行唐西畋猎，王镕送至境上', 1,
      '己亥，晋王与镕畋于行唐之西，镕送至境上而别。',
      [('李存勖','与王镕行唐西畋猎的晋王'),('王镕','同行畋猎并送晋王至境上')],
      when='914年正月己亥',place='行唐之西',
      note='只据原文记畋猎和送别，不推定军事联盟新条款。')
event('shu_prince_commands_armies', '王建命太子王宗衍判六军，开崇勋府置僚属', 2,
      '丙子，蜀主命太子判六军，开崇勋府，置僚属，后更谓之天策府。',
      [('王建','命太子判六军并设府属的前蜀皇帝'),('王宗衍','受命判六军、开崇勋府的前蜀太子')],
      when='914年正月丙子；府后来改称天策府年月未载',place='前蜀',
      note='“后更谓之天策府”为后续改称，未给年份，不录作丙子当日改名。')
event('jin_returns_jinyang', '晋王押刘仁恭父子回晋阳，丙辰献于太庙', 3,
      '壬子，晋王以练纟斥刘仁恭父子，凯歌入于晋阳。丙辰，献于太庙。',
      [('李存勖','押刘仁恭父子回晋阳并于太庙献俘的晋王'),('刘仁恭','被押至晋阳太庙的俘虏'),('刘守光','被押至晋阳太庙的俘虏')],
      when='914年正月壬子入晋阳、丙辰献太庙',place='晋阳、太庙',
      note='底本“练纟斥”含残缺字部件，保留原文，不推定具体束缚器具；旧五代史卷28将守光被诛写在壬子。')
claim('event','event_zztj_269_0914_jin_returns_jinyang','description',
      '《旧五代史》卷二十八记壬子抵晋阳并当日诛刘守光。',3,
      '壬子，至晉陽，以組練繫仁恭、守光，號令而入。是日，誅守光。',
      '主书将壬子入城与丙辰献太庙、斩守光分开，旧书本纪作壬子当日，日期差异待核。',old_annals,'conflicts')
event('li_xiaoxi_executed', '刘守光归责李小喜，李小喜反驳后先被晋王斩', 3,
      '自临斩刘守光。守光呼曰：“守光死不恨，然教守光不降者，李小喜也！”王召小喜证之，小喜瞋目叱守光曰：“汝内乱禽兽行，亦我教邪！”王怒其无礼，先斩之。',
      [('李存勖','召李小喜对证并下令先斩的晋王'),('刘守光','临刑时归责李小喜的燕主'),('李小喜','反驳刘守光后先被斩的旧部')],
      when='914年正月丙辰；随献俘后',place='晋阳',
      note='双方互相指责是当事人言辞，不作为独立事实；“先斩之”主语为晋王命斩李小喜。')
claim('event','event_zztj_269_0914_li_xiaoxi_executed','description',
      '《旧五代史》卷一百三十五也记刘守光与李小喜互责、李小喜先被斩。',3,
      '莊宗急召小喜至，令證辯。小喜瞋目叱守光曰：「囚父殺兄，烝淫骨肉，亦我教耶！」莊宗怒小喜失禮，先斬之。',
      '旧书后称庄宗指李存勖；引语细节与主书不同，不作为指控真实性证明。',old_bio,'corroborates')
event('liu_shouguang_wives_executed', '刘守光两妻李氏、祝氏就戮，刘守光随后被斩', 3,
      '守光曰：“守光善骑射，王欲成霸业，何不留之使自效！”其二妻李氏、祝氏让之曰：“皇帝，事已如此，生亦何益！妾请先死。”即伸颈就戮。守光至死号泣哀祈不已。',
      [('刘守光','求留自效后被斩的燕主'),('李氏（刘守光妻）','刘守光临刑时先就戮的妻'),('祝氏（刘守光妻）','刘守光临刑时先就戮的妻')],
      when='914年正月丙辰；据主书叙事顺序',place='晋阳',
      note='“即伸颈就戮”指李氏、祝氏应先死；刘守光“至死”哀祈，未据此定两妻与其确切执行间隔。')
relation('刘守光','李氏（刘守光妻）','丈夫',3,'其二妻李氏、祝氏让之曰：',
         '原文明言李氏为刘守光妻；关系方向刘守光为李氏丈夫。')
relation('刘守光','祝氏（刘守光妻）','丈夫',3,'其二妻李氏、祝氏让之曰：',
         '原文明言祝氏为刘守光妻；关系方向刘守光为祝氏丈夫。')
event('liu_rengong_executed_daizhou', '晋王命卢汝弼押刘仁恭至代州祭先王墓后斩之', 3,
      '王命节度副使卢汝弼等械仁恭至代州，刺其心血以祭先王墓，然后斩之。',
      [('李存勖','命押刘仁恭至代州处死的晋王'),('卢汝弼','奉命押刘仁恭至代州的节度副使'),('刘仁恭','在代州被取心血祭墓后处斩的俘虏')],
      when='914年正月丙辰后；确日未载',place='代州、先王墓',
      note='主书写卢汝弼“等”，旧书卷28补李存霸；不把祭墓与斩首换成单一执行动作。')
claim('event','event_zztj_269_0914_liu_rengong_executed_daizhou','description',
      '《旧五代史》卷一百三十五记卢汝弼、李存霸共同押刘仁恭至代州并诛之。',3,
      '令副使盧汝弼、李存霸拘送仁恭至代州，於武皇靈前刺心血以祭，誅於雁門山下。',
      '旧书补同行者李存霸及雁门山下地点；主书仅作卢汝弼等与代州。',old_bio,'adds')
event('jin_wang_shangshu_ling', '王镕、王处直遣使推晋王为尚书令，李存勖三让后受', 3,
      '或说赵王镕曰：“大王所称尚书令，乃梁官也，大王既与梁为仇，不当称其官。且自太宗践祚已来，无敢当其名者。今晋王为盟主，勋高位卑，不若以尚书令让之。”镕曰：“善！”乃与王处直各遣使推晋王为尚书令，晋王三让，然后受之，始开府置行台如太宗故事。',
      [('王镕','与王处直遣使推晋王为尚书令的赵王'),('王处直','同遣使推晋王为尚书令的定州将领'),('李存勖','三让后接受尚书令并开府置行台的晋王')],
      when='914年正月；确日未载',place='晋阳、镇定',
      note='游说者“或”未具名，不建人物；“三让”按主书所记，旧五代史卷28称使三至，保留程序差异。')
claim('event','event_zztj_269_0914_jin_wang_shangshu_ling','description',
      '《旧五代史》卷二十八称镇、定遣使三至，晋王让后受尚书令。',3,
      '是月，鎮州王鎔、定州王處直遣使推帝為尚書令。初，王鎔稱藩於梁，梁以鎔為尚書令，至是鎮、定以帝南破梁軍，北定幽、薊，乃共推崇焉。使三至，帝讓乃從之，遂選日受冊，開霸府，建行台，如武德故事。',
      '旧书“使三至”与通鉴“三让”有侧重差异，受册日期亦不明。',old_annals,'adds')
event('gao_jichang_attacks_kuizhou', '高季昌欲取原属荆南四州，先以水军攻前蜀夔州', 4,
      '高季昌以蜀夔、万、忠、涪四州旧隶荆南，兴兵取之，先以水军攻夔州。',
      [('高季昌','以旧隶荆南为由兴兵攻前蜀夔州')],
      when='914年春；确日未载',place='夔州',
      note='“旧隶荆南”是高季昌用兵理由，不代表本年四州已归其所有。')
claim('event','event_zztj_269_0914_gao_jichang_attacks_kuizhou','description',
      '《新五代史》卷六十三亦记高季昌914年侵蜀巫山，王宗寿迎击。',4,
      '四年，荊南高季昌侵蜀巫山，遣嘉王宗壽敗之于瞿唐。',
      '新书概述地点作巫山、瞿唐，主书详记夔州攻守；不可简单以地名等同。',new_shu,'adds')
event('wang_zongshou_denies_armor', '王成先请甲，王宗寿仅给白布袍', 4,
      '时镇江节度使兼侍中嘉王宗寿镇忠州，夔州刺史王成先请甲，宗寿但以白布袍给之。',
      [('王宗寿','镇忠州并只给王成先白布袍的嘉王'),('王成先','向王宗寿请甲未获的夔州刺史')],
      when='914年春夔州战前；确日未载',place='忠州、夔州',
      note='“请甲”与“白布袍”照原文区分；不推断王宗寿拒给兵甲的动机。')
event('kuizhou_fire_ship_battle', '高季昌火船攻蜀浮桥，张武以铁絙拒之，荆南兵反受风火', 4,
      '成先帅之逆战，季昌纵火船焚蜀浮桥，招讨副使张武举铁絙拒之，船不得进。会风反，荆南兵焚溺死者甚众。',
      [('王成先','率蜀军迎击荆南军'),('高季昌','纵火船攻蜀浮桥的荆南主将'),('张武','以铁絙阻火船前进的蜀招讨副使')],
      when='914年春；确日未载',place='夔州、蜀浮桥',
      note='张武沿既有904年蜀军使用铁絙者主体复用；“甚众”未给精确溺亡人数。')
event('gao_jichang_defeated_kuizhou', '高季昌战舰中石改乘小舟逃，荆南兵败', 4,
      '季昌乘战舰，蒙以牛革，飞石中之，折其尾，季昌易小舟以遁。荆南兵大败，俘斩五千级。',
      [('高季昌','战舰中石后改乘小舟逃离的荆南主将')],
      when='914年春；确日未载',place='夔州',
      note='“俘斩五千级”是合并俘虏及斩首的史书口径，不等同纯死亡人数。')
event('wang_chengxian_executed', '王成先密告王宗寿不给甲，王宗寿获奏后召而斩之', 4,
      '成先密遣人奏宗寿不给甲之状，宗寿获之，召成先，斩之。',
      [('王成先','密奏王宗寿不给甲后被召杀的夔州刺史'),('王宗寿','截获奏报后召杀王成先的嘉王')],
      when='914年夔州战后；确日未载',place='忠州、夔州',
      note='本段只记奏报被截获与处斩，未记正式审判或罪名。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,5):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269乾化四年正月至春第1—4段连续处理；刘守光与李小喜处死、尚书令推举、夔州战事拆分，旧书日期异文并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=914,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(1,5)],next_paragraph='zztj-v269-y0914-p005',
    coverage='卷269乾化四年正月至春第1—4段，晋王回朝处置燕俘、晋王受尚书令、前蜀夔州拒荆南。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[3]['id'],'note':'底本“练纟斥”为字部件残缺，原样引用；通鉴壬子入晋阳、丙辰献太庙斩刘守光，旧五代史卷28记壬子即诛，卷135无精日。日期保留异说。'},
      {'paragraph_id':Q[3]['id'],'note':'刘守光与李小喜互责均为当事人言辞；两妻先就戮。旧五代史卷135补李存霸同押刘仁恭，通鉴作卢汝弼等。'},
      {'paragraph_id':Q[4]['id'],'note':'新五代史概述巫山瞿唐，主书详记夔州火船、铁絙与高季昌退走；王成先战后被王宗寿处斩另列。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
