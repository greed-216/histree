"""Curate Tongjian 266, year 908, consecutive paragraphs 25–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 41))
main1 = 'tongjian-266-908-luzhou-aftermath'
main2 = 'tongjian-266-908-coup-conclusion'
main3 = 'tongjian-266-908-summer'
new1 = 'xinwudaishi-061-huainan-murder'
new2 = 'xinwudaishi-061-huainan-succession'
new3 = 'xinwudaishi-061-huainan-countercoup'
newtea = 'xinwudaishi-066-chu-tea'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0908-p025-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (main1, P.parent / 'part-02/sources/library' / main1, 'f6893bfc', '司马光等'),
    (main2, P / 'sources/library' / main2, 'fe35a4a6', '司马光等'),
    (main3, P / 'sources/library' / main3, 'fe35a4a6', '司马光等'),
    (new1, P / 'sources/library' / new1, 'fe35a4a6', '欧阳修等'),
    (new2, P / 'sources/library' / new2, 'fe35a4a6', '欧阳修等'),
    (new3, P / 'sources/library' / new3, 'fe35a4a6', '欧阳修等'),
    (newtea, P / 'sources/library' / newtea, 'fe35a4a6', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (main1, main2, main3)}
for n in range(25, 41):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '蜀主':'王建', '吴越王镠':'钱镠', '晋王克用':'李克用', '晋王存勖':'李存勖', '济阴王':'唐昭宣帝', '唐哀皇帝':'唐昭宣帝', '存勗':'李存勖', '克寧':'李克宁'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/later-liang-907-923/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json',
                'content/later-liang-907-923/content-batch.json',
                'content/books/zizhi-tongjian/vol-263/year-0902/part-02/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0908_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷266·开平二年（908）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷266开平二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=908, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_266_0908_' + code)
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
                                time_original=when or '908年本段条；确日未载', dynasty='五代十国', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '908年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_266_0908_' + code + '_' + pk
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
    ck = f'claim_zztj_266_0908_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 25–27: Chu succession, Liang command names, and the Ezhou raid.
event('li_qiong_dies','静江节度使李琼去世，马殷令弟马存知桂州事',25,
      '李琼卒，楚王殷以其弟永州刺史存知桂州事。',
      [('李琼','去世的静江节度使'),('马殷','命弟知桂州事的楚王'),('马存','知桂州事的马殷之弟')],
      when='908年五月后条；确日未载',place='桂州',
      note='“其弟”明确马存为马殷之弟；不据任事推定正式节度使职名。')
B['person_relationships'].append(dict(key='relationship_person_马殷_person_马存_兄长',
    person_a_key=people['马殷'],person_b_key=people['马存'],relation_type='兄长',
    description='马殷是马存的兄长。',status='draft'))
claim('person_relationship','relationship_person_马殷_person_马存_兄长','description',
      '马殷是马存的兄长。',25,'楚王殷以其弟永州刺史存知桂州事',
      '“其弟”明确长幼；马殷与马存沿用站内简体展示，原文原字保留。')
event('liang_army_renames','后梁更改许、同、陕三州军号',26,
      '壬申，更以许州忠武军为匡国军，同州匡国军为忠武军，陕州保义军为镇国军。',
      when='908年壬申',place='许州、同州、陕州',
      note='同段三项军号变更属一次诏令；不是三州疆域变化。')
event('chu_ezhou_raid','楚军进攻鄂州，被淮南秦裴击破',27,
      '乙亥，楚兵寇鄂州，淮南所署知州秦裴击破之。',
      [('秦裴','淮南所署鄂州知州，击败楚军')],when='908年乙亥',place='鄂州',
      note='只记此役，不推定楚与淮南此后持续敌对的年限。')

# 28–30: Murder, succession, countercoup, and Huainan administration.
event('yang_wo_murder','张颢、徐温共谋弑杨渥，张颢遣纪祥等行凶',28,
      '二人不自安，共谋弑王，分其地以臣于梁。戊寅，颢遣其党纪祥等弑王于寝室，诈云暴薨。',
      [('张颢','与徐温共谋、遣纪祥等弑王'),('徐温','参与弑王谋划'),('杨渥','被弑的弘农王'),('纪祥','受张颢指使行凶')],
      when='908年戊寅',place='淮南王府寝室',
      note='分地臣梁仅为谋划，未作为已实施外交行为；“暴薨”是凶手的伪称。')
extra(new1,'event','event_zztj_266_0908_yang_wo_murder','description',
      '《新五代史》卷六十一亦记徐温、张颢共遣盗杀杨渥，纪祥亲手缢杀，并作五月。',
      '溫、顥共遣盜入寢中殺渥',28,'adds',
      '新史明确五月与行凶方式，主书只在此段记戊寅；繁体原字保持，不据后代追谥改当时称谓。')
event('yang_longyan_succeeds','严可求宣史太夫人教，杨隆演继为淮南留后',29,
      '遂奉威王弟隆演称淮南留后、东面诸道行营都统。',
      [('严可求','拟立杨隆演并宣读史太夫人教'),('张颢','谋自立而未遂'),('杨隆演','受奉为淮南留后'),('史氏','以其教书支持杨隆演继立')],
      when='908年己卯',place='淮南军府',
      note='史太夫人教由严可求急书宣读；不推定其事先亲笔。朱瑾“以兄事之”是礼敬，不建血缘关系。')
B['person_relationships'].append(dict(key='relationship_person_杨渥_person_杨隆演_兄长',
    person_a_key=people['杨渥'],person_b_key=people['杨隆演'],relation_type='兄长',
    description='杨渥是杨隆演的兄长。',status='draft'))
claim('person_relationship','relationship_person_杨渥_person_杨隆演_兄长','description',
      '杨渥是杨隆演的兄长。',29,'遂奉威王弟隆演称淮南留后',
      '“威王弟”明确长幼；威王承第28段杨渥。')
extra(new2,'event','event_zztj_266_0908_yang_longyan_succeeds','description',
      '《新五代史》卷六十一也记严可求阻张颢自立、宣史氏教，使杨隆演得立。',
      '隆演乃得立',29,'corroborates',
      '新史为另一编纂文本；书证独立登记，不把原文繁体转换进摘录。')
event('xu_wen_remains','严可求阻止徐温外放润州，张颢刺严可求未遂',30,
      '由是不行。颢知可求阴附温，夜，遣盗刺之',
      [('严可求','阻止徐温外放并遇刺未死'),('徐温','原拟赴润州而未行'),('张颢','遣盗刺严可求')],
      when='908年杨隆演继立后、丁亥前',place='扬州',
      note='外放浙西观察使未实际赴任；刺客放过严可求，不能写作遇害。')
event('zhang_hao_killed','钟泰章率壮士斩张颢，徐温处死纪祥等',30,
      '泰章闻之喜，密结壮士三十人，夜，刺血相饮为誓。丁亥旦，直入斩颢于牙堂，并其亲近。温始暴颢弑君之罪，轘纪祥等于市。',
      [('钟泰章','率三十壮士杀张颢'),('张颢','于牙堂被斩'),('徐温','公布张颢弑君罪并处死纪祥等'),('纪祥','因弑杨渥被处死')],
      when='908年丁亥旦',place='淮南牙堂、市场',
      note='徐温自身参与弑杨渥谋划另有主书追叙，不因其清算张颢而抹去。')
claim('event','event_zztj_266_0908_zhang_hao_killed','description',
      '《通鉴》追叙徐温先与张颢共谋弑杨渥，后来仅清算左牙兵，使时人以为徐温不知谋。',30,
      '由是人以温为实不知谋也',
      '“人以为”是当时舆论，主书此前明载徐温参与谋划；两层叙事不能混同。')
extra(new3,'event','event_zztj_266_0908_zhang_hao_killed','description',
      '《新五代史》卷六十一亦记徐温与严可求谋斩张颢。',
      '可求詣溫，謀先殺顥',30,'corroborates',
      '新史所称“鍾章”与主书“钟泰章”字形及名异，暂不以繁简转换强行合并为同名。')
event('huainan_administration','杨隆演任徐温、严可求，徐温分掌淮南军政财赋',30,
      '隆演以温为左、右牙都指挥使，军府事咸取决焉。以严可求为扬州司马。',
      [('杨隆演','任命徐温、严可求的淮南主君'),('徐温','领左右牙并主军府'),('严可求','受任扬州司马')],
      when='908年张颢被诛后；确日未载',place='扬州',
      note='徐温后续法度和分工属本段叙述，未把长时段成效强定于丁亥。')
claim('event','event_zztj_266_0908_huainan_administration','description',
      '徐温委严可求办理军旅，委骆知祥办理财赋。',30,
      '温以军旅委可求，以财赋委支计官骆知祥',
      '分工按主书记载；不推定两人为血缘或正式宰相。')

# 31–40: diplomacy, warfare, executions, tea finance and later reward.
event('khitan_embassy','阿保机遣使入梁求册命，朱温提出共灭沙陀后封册',31,
      '契丹王阿保机遣使随高颀入贡，且求册命。帝复遣司农卿浑特赐以手诏，约共灭沙陀，乃行封册。',
      [('阿保机','遣使求册命的契丹王'),('高颀','与契丹使同行入贡'),('朱温','遣浑特答复册命条件'),('浑特','奉手诏出使契丹')],
      when='908年己丑',note='“乃行封册”是条件约定，非册封已经举行；共灭沙陀亦非已成事实。')
event('liang_generals_amnesty','后梁赦夹寨败将并任牛存节六军马步都指挥使',32,
      '夹寨诸将诣阙待罪，皆赦之。帝赏牛存节全泽州之功，以为六军马步都指挥使。',
      [('朱温','赦败将并任命牛存节'),('牛存节','因保全泽州而受任')],
      when='908年壬辰',note='赦败将与赏牛存节同日条，牛存节保泽州据前第21段。')
event('chu_takes_lang_li','秦彦晖攻取朗州，雷彦恭逃广陵，澧州亦降楚',33,
      '彦恭轻舟奔广陵。彦晖虏其弟彦雄，送于大梁。淮南以彦恭为节度副使。',
      [('秦彦晖','攻取朗州的楚将'),('雷彦恭','弃朗州赴广陵'),('雷彦雄','被俘并送梁')],
      when='908年六月前条；围城月余',place='朗州、澧州',
      note='澧州向瑰降楚见同段后句；“先是”描述此前与雷彦恭相表里，不另定为908年新结盟。')
claim('event','event_zztj_266_0908_chu_takes_lang_li','description',
      '澧州刺史向瑰降楚，楚始取得澧、朗两州。',33,
      '至是亦降于楚，楚始得澧、朗二州',
      '将“始得”作为主书所述结果，不据此绘精确边界。')
event('shu_qi_jin_yongzhou','蜀、岐军攻雍州，晋张承业响应；梁命刘知俊迎敌',34,
      '蜀主遣将将兵会岐兵五万攻雍州，晋张承业亦将兵应之。六月，壬寅，以刘知俊为西路行营都招讨使以拒之。',
      [('王建','遣军会岐的蜀主'),('张承业','率晋军响应'),('刘知俊','受命为梁西路招讨使')],
      when='908年六月壬寅任刘知俊；进军确日未载',place='雍州',
      note='五万是主书所记蜀岐兵数，不能视为精确统计；任命与实际交战分开。')
event('wang_shifan_clan_executed','朱温下令于洛阳族诛王师范宗族',35,
      '已酉，遣使就洛阳族之。',
      [('朱温','下令族诛王师范'),('王师范','在洛阳被族诛')],
      when='908年六月已酉；日字待校',place='洛阳',
      note='底本作“已酉”，疑“己酉”；朱友宁妻的陈诉属促发此令的主书记述。死者二百是史书记数。')
claim('event','event_zztj_266_0908_wang_shifan_clan_executed','description',
      '《通鉴》记王师范宗族遇害者约二百人。',35,
      '死者凡二百人',
      '沿用史书记数，不视为现代逐名核定人数。')
event('mugu_battle','刘知俊、王重师在幕谷击败岐兵，晋蜀军撤退',36,
      '丙辰，刘知俊及佑国节度使王重师大破岐兵于幕谷，晋、蜀兵皆引归。',
      [('刘知俊','梁军将领，于幕谷击败岐兵'),('王重师','梁军将领，与刘知俊并战')],
      when='908年六月丙辰',place='幕谷',
      note='主书说晋蜀军撤退，不推定联军全歼。')
event('shu_heir_zongyi','前蜀立遂王王宗懿为太子',37,
      '蜀立遂王宗懿为太子。',
      [('王宗懿','被立为前蜀太子')],
      when='908年六月至七月间；确日未载',place='蜀',
      note='主书此处仅记立储，不用后见结局倒填。')
event('liang_luzhou_assembly','朱温拟亲攻潞州并诏集诸道兵',37,
      '帝欲自将击潞州，丁卯，诏会诸道兵。',
      [('朱温','拟亲攻潞州并召集军队')],
      when='908年丁卯',place='潞州',
      note='“欲自将”为计划，诏会兵已发生；不写成已亲征。')
event('chu_tea_trade','马殷采纳高郁茶税建议，设置回图务经营茶贸',38,
      '秋，七月，殷奏于汴、荆、襄、唐、郢、复州置回图务，运茶于河南、北，卖之以易缯纩、战马而归，仍岁贡茶二十五万斤，诏许之。',
      [('高郁','建议民采茶交易并征税的湖南判官'),('马殷','奏设回图务的楚王'),('朱温','准许楚回图务与贡茶安排的梁帝')],
      when='908年七月',place='汴、荆、襄、唐、郢、复州',
      note='奏请与诏许明确，史家“富赡”是后来成效概述；不推断具体商税收入。')
extra(newtea,'event','event_zztj_266_0908_chu_tea_trade','description',
      '《新五代史》卷六十六亦记高郁议茶贸、楚设邸务及征算。',
      '又令民自造茶以通商旅，而收其算',38,'adds',
      '新史叙事未以本年精确断代，只作制度补证；“其利十倍”不当作已核现代收益。')
event('yang_longyan_titles','淮南将吏请李俨承制授杨隆演节度使、同平章事等',39,
      '淮南将吏请于李俨，承制授杨隆演淮南节度使、东面诸道行营都统、同平章事、弘农王。',
      [('李俨','受请承制授杨隆演官爵'),('杨隆演','受授淮南节度使等官爵')],
      when='908年壬申',place='淮南',
      note='与第29段初奉留后分开；这里才出现弘农王及节度使等正式名号。')
event('zhong_taizhang_promoted_later','钟泰章因旧功赏薄逾年后升滁州刺史',40,
      '后逾年，因醉与诸将争言而及之。或告徐温，以泰章怨望，请诛之，温曰：“是吾过也。”擢为滁州刺史。',
      [('钟泰章','逾年后升滁州刺史'),('徐温','承认旧赏失当并升钟泰章')],
      when='908年张颢伏诛后逾年；确年未载',place='滁州',year=None,
      note='“后逾年”明确非908年当下事件，确年不明，故公历年留空。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,41):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平二年第25—40段连续处理；淮南弑君与清算分开，计划与结果、追叙与本年分开，繁简实体统一而原文保字。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=908,
    primary_source_key=main1,primary_source_keys=[main1,main2,main3],
    paragraphs=[Q[n]['id'] for n in range(25,41)],next_paragraph='zztj-v267-y0908-p001',
    coverage='卷266开平二年第25—40段连续处理；淮南政变、楚占澧朗、梁岐幕谷战、楚茶贸及跨年追叙。卷267续本年。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
