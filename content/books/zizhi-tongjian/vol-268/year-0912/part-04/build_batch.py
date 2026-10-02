"""Curate Tongjian 268, year 912, consecutive paragraphs 31-40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
main1 = 'tongjian-268-912-zhu-death'
main2 = 'tongjian-268-912-autumn'
old_yang = 'jiuwudaishi-022-yangshihou'
new_yang = 'xinwudaishi-023-yangshihou'
old_hezhong = 'jiuwudaishi-028-hezhong'
new_youqian = 'xinwudaishi-005-youqian'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0912-p031-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-03/sources/library' / main1, '99be897d', '司马光等'),
    (main2, P / 'sources/library' / main2, '7826e264', '司马光等'),
    (old_yang, P / 'sources/library' / old_yang, '7826e264', '薛居正等'),
    (new_yang, P / 'sources/library' / new_yang, '7826e264', '欧阳修'),
    (old_hezhong, P / 'sources/library' / old_hezhong, '7826e264', '薛居正等'),
    (new_youqian, P / 'sources/library' / new_youqian, '7826e264', '欧阳修'),
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
for n in range(31,41):
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
           '王景仁':'王茂章','张宗奭':'张全义','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化二年（912）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0912_04_{len(B["claims"])+1:04d}'
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
                   description=f'《资治通鉴》卷268乾化二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=912):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0912_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '912年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_268_0912_' + code + '_' + pk
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

event('yougui_july_amnesty', '梁廷七月丁未大赦', 31,
      '秋，七月，丁未，大赦。',
      when='912年七月丁未',place='后梁',
      note='本段仅记大赦，未列赦令范围或颁诏人；不补出未明示参与者。')

event('yang_shihou_seizes_weizhou', '杨师厚杀潘晏、据魏州牙城', 32,
      '师厚馆于铜台驿，潘晏入谒，执而杀之，引兵入牙城，据位视事。',
      [('杨师厚','在铜台驿杀潘晏并据魏州牙城'),('潘晏','入谒杨师厚时被杀的魏州牙内都指挥使')],
      when='912年七月壬子前；确日未载',place='魏州、铜台驿',
      note='主书以师厚“久欲图之”解释动机；旧史卷22另称潘晏等谋变、杨师厚捕杀，动机异说并存。')
claim('event','event_zztj_268_0912_yang_shihou_seizes_weizhou','description',
      '《旧五代史》卷二十二说潘晏等谋变、杨师厚布兵擒杀。',32,
      '魏州衙內都指揮使潘晏與大將臧延範、趙訓謀變，有密告者，師厚布兵擒捕，斬之。',
      '旧书叙事将潘晏列为谋变者，与主书杨师厚主动夺魏州的动机和行动过程有差异；不改写主书。',old_yang,'conflicts')
claim('event','event_zztj_268_0912_yang_shihou_seizes_weizhou','description',
      '《新五代史》卷二十三也记杨师厚趁朱友珪即位夺魏州，并称杀臧延範。',32,
      '友珪自立，師厚乘間殺魏牙將潘晏、臧延範等，逐出節度使羅周翰，友珪因以師厚為天雄軍節度使。',
      '新史与主书同记乘机夺魏州，另列臧延範；与旧书“潘晏等谋变”不可简单合一。',new_yang,'adds')
event('yang_shihou_tianxiong_appointment', '朱友珪任杨师厚天雄节度使，罗周翰转宣义', 32,
      '壬子，制以师厚为天雄节度使，徙周翰为宣义节度使。以侍卫诸军使韩勍领匡国节度使。',
      [('杨师厚','获任天雄节度使'),('罗周翰','由天雄转任宣义节度使'),('韩勍','领匡国节度使'),('朱友珪','签制调整三人军镇的梁帝')],
      when='912年七月壬子',place='魏州、宣义军、匡国军',
      note='潘晏先被杀、杨师厚据位，壬子才有任命；不把受任写成此前攻取魏州的授权。')

event('qian_liu_shangfu', '后梁加钱镠尚父', 33,
      '甲寅，加吴越王镠尚父。',
      [('钱镠','获后梁尚父名号的吴越王')],
      when='912年七月甲寅',place='吴越',
      note='“镠”沿已有人物钱镠；称号不推出实际指挥权。')

event('zhu_youzhen_dongdu', '朱友贞获任开封尹、东都留守', 34,
      '甲子，以均王友贞为开封尹、东都留守。',
      [('朱友贞','获任开封尹、东都留守的均王')],
      when='912年七月甲子',place='开封、东都',
      note='复用已有人物朱友贞，不另建均王。')

event('shu_crown_prince_renamed', '前蜀太子王宗懿由元坦更名元膺', 35,
      '蜀太子元坦更名元膺。',
      [('元坦','由元坦更名元膺的前蜀太子王宗懿')],
      when='912年七月甲子后；确日未载',place='前蜀',
      note='本段明确同一太子更名；元坦、元膺均归入已有王宗懿UUID，保留两个时名。')
next(x for x in B['people'] if x['key']==people['王宗懿'])['aliases']=sorted(set(next(x for x in B['people'] if x['key']==people['王宗懿']).get('aliases',[]))|{'元坦','元膺','王元膺'})

event('zhang_quanyi_state_finance', '后梁废建昌宫使，张全义任国计使掌金谷', 36,
      '丙寅，废建昌宫使，以河南尹张宗奭为国计使，凡天下金谷旧隶建昌宫者悉主之。',
      [('张宗奭','获任国计使、掌原建昌宫金谷的张全义')],
      when='912年七月丙寅',place='河南、后梁',
      note='张宗奭是张全义异名，复用已有UUID；“废建昌宫使”为职司变更，不等于建昌宫建筑被毁。')

event('longxiang_troops_mutiny', '怀州龙骧军三千人溃乱东走并沿途剽掠', 37,
      '八月，龙骧军三千人戍怀州者，溃乱东走，所过剽掠；',
      when='912年八月戊子前；确日未载',place='怀州及东行沿途',
      note='三千为原文所称戍军人数，未见全体参与剽掠的逐人记录。')
event('longxiang_mutiny_suppressed', '霍彦威、杜晏球击破乱军，擒斩刘重遇', 37,
      '戊子，遣东京马步军都指挥使霍彦威、左耀武指挥使杜晏球讨之，庚寅，击破乱军，执其都将刘重遇于鄢陵，甲午，斩之。',
      [('霍彦威','奉命讨龙骧乱军的东京马步军都指挥使'),('杜晏球','奉命讨龙骧乱军的左耀武指挥使'),('刘重遇','被擒于鄢陵并于甲午被斩的乱军都将')],
      when='912年八月戊子出兵、庚寅擒、甲午斩',place='鄢陵',
      note='把遣军、击破及处斩按干支顺序记录，不把甲午当作战斗日。')

event('zhu_youqian_defies_yougui', '朱友谦质疑朱友珪即位，拒绝入朝', 38,
      '友珪加友谦侍中、中书令，以诏书自辨，且征之。友谦谓使者曰：“所立者为谁？先帝晏驾不以理，吾且至洛阳问罪，何以征为！”',
      [('朱友珪','加朱友谦官并遣使征召的梁帝'),('硃友谦','拒召并质疑梁帝继位的河中节度使')],
      when='912年八月戊戌前；确日未载',place='河中、洛阳',
      note='底本段首作“硃友谦”而后作“友谦”，归入已有人物朱友谦；其引语是政治表态，不等于已率军抵洛阳。')
event('zhu_youqian_to_jin', '朱友谦以河中附晋求援，朱友珪遣军讨伐', 38,
      '戊戌，以侍卫诸军使韩勍为西面行营招讨使，督诸军讨之。友谦以河中附于晋以求救，九月，丁未，以感化节度使康怀贞为河中都招讨使，更以韩勍副之。',
      [('韩勍','受命讨朱友谦、后改任河中都招讨副使'),('朱友谦','以河中归附晋并求援'),('康怀贞','九月丁未获任河中都招讨使'),('朱友珪','派兵讨河中朱友谦的梁帝')],
      when='912年八月戊戌及九月丁未',place='河中、晋',
      note='主书记友谦附晋求援；新五代史卷5另称其后复臣梁而暗附晋，属于后续或异说，不将其归附写成永久稳定。')
claim('event','event_zztj_268_0912_zhu_youqian_to_jin','description',
      '《新五代史》卷五记朱友谦河中叛梁来降，但又称其后复臣梁、暗附晋。',38,
      '八月，朱友謙以河中叛于梁來降，梁遣康懷英討友謙，友謙復臣于梁，而亦陰附于晉。',
      '新史概述后续归属，并作康怀英；主书本段为康怀贞。两名可能同人或异文，先不据字形并实体。',new_youqian,'adds')
event('jing_xiang_reassigned', '朱友珪改敬翔为宰相，李振接掌崇政院', 38,
      '庚午，以翔为中书侍郎、同平章事，壬申，以户部尚书李振充崇政院使。翔多称疾不预事。',
      [('朱友珪','调整敬翔、李振职务的梁帝'),('敬翔','离崇政院改宰相、此后多称疾'),('李振','接任崇政院使的户部尚书')],
      when='912年九月庚午、壬申',place='洛阳',
      note='主书说友珪忌敬翔、又恐失人望；敬翔“称疾”不说明真实病情。')

event('jin_relief_hezhong_hubi', '晋军救河中，在胡壁击败梁军', 39,
      '康怀贞等与忠武节度使牛存节合兵五万屯河中城西，攻之甚急。晋王遣其将李存审、李嗣肱、李嗣恩将兵救之，败梁兵于胡壁。',
      [('康怀贞','统梁军攻河中'),('牛存节','与康怀贞合兵攻河中'),('李存勖','遣将救河中的晋王'),('李存审','率晋军援河中的符存审'),('李嗣肱','率晋军援河中'),('李嗣恩','率晋军援河中')],
      when='912年九月丁未后；确日未载',place='河中城西、胡壁',
      note='五万是两支梁军合计，非康怀贞一军；“嗣恩本骆氏子”仅记改姓来源，不补生父姓名。')
claim('event','event_zztj_268_0912_jin_relief_hezhong_hubi','description',
      '《旧五代史》卷二十八亦记梁以五万兵攻河中、晋命符存审救援。',39,
      '朱友珪遣其將韓勍、康懷英、牛存節率兵五萬，急攻河中。朱友謙遣使來求援，帝命李存審率師救之。',
      '旧书作康怀英、并列韩勍；主书作康怀贞且记胡壁之胜。可能异名或行军阶段差别，纸本待核。',old_hezhong,'adds')

event('huang_ne_advises_liu_wei', '黄讷劝刘威轻舟入见徐温以释嫌', 40,
      '威幕客黄讷说威曰：“公受谤虽深，反本无状，若轻舟入觐，则嫌疑皆亡矣。”威从之。',
      [('黄讷','建议刘威入觐以释嫌的幕客'),('刘威','接受黄讷建议的吴将')],
      when='912年九月前后；确日未载',place='广陵',
      note='主书说“反本无状”，不把先前徐温所闻谗言写作刘威真实反叛。')
event('liu_wei_tao_ya_visit_xu_wen', '刘威、陶雅赴广陵见徐温，获礼遇后还镇', 40,
      '陶雅闻李遇败，亦惧，与威偕诣广陵，温待之甚恭，如事武忠王之礼，优加官爵，雅等悦服，由是人皆重温。',
      [('刘威','赴广陵消疑的吴旧将'),('陶雅','随刘威赴广陵的吴旧将'),('徐温','以礼遇消除旧将疑虑的吴执政者')],
      when='912年九月前后；确日未载',place='广陵',
      note='刘威受谗及黄讷建议见本段前文；“悦服”“人皆重温”为史家叙述，不推全体旧将态度。')
event('wu_titles_yang_longyan_xu_wen', '吴将吏请李俨承制加杨隆演吴王，徐温领镇海节度使', 40,
      '温与威、雅帅将吏请于李俨，承制加嗣吴王隆演太师、吴王，以温领镇海节度使、同平章事，淮南行军司马如故。温遣威、雅还镇。',
      [('徐温','领镇海节度使、同平章事并遣旧将还镇'),('刘威','参与请封及回镇的吴将'),('陶雅','参与请封及回镇的吴将'),('李俨','承制加封杨隆演的吴臣'),('杨隆演','获加太师、吴王名号的吴主')],
      when='912年九月前后；确日未载',place='广陵、吴',
      note='承制请封与徐温任官按本段记载，不误认为梁廷直接封吴王。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(31,41):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化二年第31—40段连续处理；杨师厚夺魏州动机、河中归属及人名异文均分源注明。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=912,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(31,41)],next_paragraph='zztj-v268-y0912-p041',
    coverage='卷268乾化二年七月至九月第31—40段，杨师厚据魏州、河中归晋与梁晋交战、吴将赴广陵。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[32]['id'],'note':'旧五代史卷22称潘晏等谋变而被杨师厚捕杀；通鉴及新五代史侧重杨师厚趁梁太祖死夺魏州，动机不同。'},
      {'paragraph_id':Q[35]['id'],'note':'元坦更名元膺，归入既有王宗懿UUID；需后续补线上搜索别名。'},
      {'paragraph_id':Q[38]['id'],'note':'底本硃友谦与朱友谦同人。新五代史卷5另记朱友谦复臣梁而暗附晋，康怀英/康怀贞异名待核。'},
      {'paragraph_id':Q[39]['id'],'note':'旧五代史卷28五万兵攻河中、晋遣李存审救援，与通鉴相关；其康怀英与主书康怀贞未自动合并。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
