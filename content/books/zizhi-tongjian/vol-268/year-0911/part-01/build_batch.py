"""Curate Tongjian 268, year 911, consecutive paragraphs 1-10."""
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
main1 = 'tongjian-268-911-spring-summer'
new_liu = 'xinwudaishi-065-liuyin-succession'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0911-p001-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, P / 'sources/library' / main1, '34e851bf', '司马光等'),
    (new_liu, P / 'sources/library' / new_liu, '34e851bf', '欧阳修'),
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
for n in range(1, 11):
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
           '王景仁':'王茂章','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
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
    ck = f'claim_zztj_268_0911_01_{len(B["claims"])+1:04d}'
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

event('luo_zhouhan_tianxiong', '后梁任罗周翰为天雄节度使', 1,
      '三月，乙酉朔，以天雄留后罗周翰为节度使。',
      [('罗周翰','由天雄留后获授节度使')],when='911年三月乙酉朔',place='天雄军')

event('liu_yin_succession', '刘隐病重荐弟刘岩，丁亥去世后刘岩承位', 2,
      '清海、静海节度使兼中书令南平襄王刘隐病亟，表其弟节度副使岩权知留后。丁亥卒，岩袭位。',
      [('刘隐','病重荐弟权知留后并于丁亥去世'),('刘岩','受兄举荐并于其死后继位')],
      when='911年三月丁亥刘隐卒；荐弟在此前',place='清海、静海',
      note='刘隐荐弟、去世、刘岩袭位先后分明；不将随后正式授节度使提前到丁亥。')
claim('event','event_zztj_268_0911_liu_yin_succession','description',
      '《新五代史》卷六十五也记刘隐去世后其弟继立。',2,'隱卒，龑代立。',
      '新史以刘龑称其弟，主书此时称刘岩；此处仅作兄亡弟继的补证，异名待进一步核。新史紧接记乾化二年授清海节度使，与主书本年甲辰授职有时间差。',new_liu,'adds')

event('qi_shu_border_mobilization', '岐王聚兵蜀境，王建筹议伐岐', 3,
      '岐王聚兵临蜀东鄙，蜀主谓群臣曰：“自茂贞为硃温所困，吾常振其乏绝，今乃负恩为寇，谁为吾击之？”兼中书令王宗侃请行，蜀主以宗侃为北路行营都统。',
      [('李茂贞','聚兵临蜀东境的岐王'),('王建','召臣议对岐用兵的蜀主'),('王宗侃','请行并获任北路行营都统')],
      when='911年三月后；壬辰出师前',place='蜀东境、成都',
      note='王建引语陈述其立场；此前援岐为其自述，未由本段独立证明。')
event('zhao_wengui_warning', '赵温珪谏阻深入岐地，王建未采纳', 3,
      '司天少监赵温珪谏曰：“茂贞未犯边，诸将贪功深入，粮道阻远，恐非国家之利。”蜀主不听',
      [('赵温珪','谏蜀主勿深入岐境'),('王建','未采纳谏言的蜀主')],
      when='911年壬辰出师前',place='前蜀朝廷',
      note='粮道风险为赵温珪的判断，不推为已经断粮。')
event('shu_expedition_qi', '王建任王宗祐等为招讨使，王宗侃壬辰率军出成都', 3,
      '以兼侍中王宗祐、太子少师王宗贺、山南节度使唐道袭为三招讨使，左金吾大将军王宗绍为宗祐之副，帅步骑十二万伐岐。壬辰，宗侃等发成都，旌旗数百里。',
      [('王建','任命招讨使的蜀主'),('王宗祐','三招讨使之一'),('王宗贺','三招讨使之一'),('唐道袭','三招讨使之一'),('王宗绍','王宗祐之副'),('王宗侃','统军出成都')],
      when='911年壬辰出成都',place='成都、岐方向',
      note='十二万为主书所载步骑规模，未经独立核数；不推定全军在同日抵达岐境。')

event('wen_tao_adopted_command', '李茂贞收温韬为假子并置义胜军', 4,
      '岐王募华原贼帅温韬以为假子，以华原为耀州，美原为鼎州。置义胜军，以韬为节度使，使帅邠、岐兵寇长安。',
      [('李茂贞','收温韬为假子并命其领义胜军的岐王'),('温韬','被岐王收为假子、任义胜节度使')],
      when='911年三月后；己酉前',place='华原、美原、长安方向',
      note='“假子”为拟亲关系，不写生父子；寇长安是温韬率军行动。')
relation('李茂贞','温韬','假父',4,'岐王募华原贼帅温韬以为假子',
         '原文明言温韬为岐王假子，只建立拟亲关系。')
event('liang_repels_wen_tao', '梁遣康怀贞、牛存节讨温韬，己酉于车度击走', 4,
      '诏感化节度使康怀贞、忠武节度使牛存节以同华、河中兵讨之。己酉，怀贞等奏击韬于车度，走之。',
      [('朱温','诏命梁军讨温韬'),('康怀贞','奉诏并奏报车度击走温韬'),('牛存节','参与奉诏讨伐'),('温韬','于车度被梁军击走')],
      when='911年己酉奏报车度战',place='车度',
      note='“怀贞等奏”为梁将奏报，牛存节是否在车度亲自参战未由此句分明。')
event('tang_daoxi_repels_qi', '岐兵寇兴元，唐道袭击退', 4,
      '夏，四月，乙卯朔，岐兵寇蜀兴元，唐道袭击却之。',
      [('唐道袭','在兴元击退岐兵的蜀将')],
      when='911年四月乙卯朔',place='兴元',note='此役为岐兵攻兴元，不与前句梁军车度战混同。')

event('liang_amnesty_illness', '朱温久病，于五月甲申大赦', 5,
      '上以久疾，五月，甲申朔，大赦。',
      [('朱温','因久病而颁大赦的梁帝')],when='911年五月甲申朔',place='后梁',
      note='原文明说久疾与大赦相连，不推断疾病诊断或病愈。')

event('liu_yan_qinghai_appointment', '后梁授刘岩清海节度使', 6,
      '甲辰，以清海留后刘岩为节度使。',
      [('刘岩','由清海留后获授节度使')],when='911年五月甲辰',place='清海军',
      note='与第2段刘隐病卒后刘岩袭位分开；《新五代史》卷六十五记乾化二年授清海节度使，纪年异说待核。')
event('liu_yan_civil_officials', '刘岩延揽中国士人任幕府及刺史', 6,
      '岩多延中国士人置于幕府，出为刺史，刺史无武人。',
      [('刘岩','延揽士人任幕府及刺史')],
      when='911年本段综述；施行起止未详',place='清海军',
      note='这是持续性用人政策概述，不能全定于甲辰当日。')

event('shu_to_lizhou', '王建赴利州，命太子监国，六月癸丑到达', 7,
      '蜀主如利州，命太子监国；六月，癸丑朔，至利州。',
      [('王建','赴利州并命太子监国'),('王宗懿','受命监国的前蜀太子')],
      when='911年六月癸丑朔到利州；起行在此前',place='利州',
      note='太子按910年改名元坦的王宗懿复用同一人，不另建人物。')

event('liu_shouguang_emperor_ambition', '刘守光试探称帝，孙鹤劝其暂缓', 8,
      '燕王守光尝衣赭袍，顾谓将吏曰：“今天下大乱，英雄角逐，吾兵强地险，亦欲自帝，何如？”孙鹤曰：“今内难新平，公私困竭，太原窥吾西，契丹伺吾北，遽谋自帝，未见其可。大王但养士爱民，训兵积谷，德政既修，四方自服矣。”守光不悦。',
      [('刘守光','试探称帝的燕王'),('孙鹤','劝燕王暂缓称帝')],
      when='911年本段追叙；乙卯前，确日未载',place='燕',
      note='原文“尝”为追叙，不将此谈话强定六月或七月；称帝尚未发生。')
event('six_commands_nominate_shouguang', '晋赵等六镇推刘守光为尚书令、尚父', 8,
      '乃与镕及义武王处直、昭义李嗣昭、振武周德威、天德宋瑶六节度使共奉册推守光为尚书令、尚父。',
      [('李存勖','参与六镇推尊的晋王'),('王镕','参与推尊的赵王'),('王处直','参与推尊的义武节度使'),('李嗣昭','参与推尊的昭义节度使'),('周德威','参与推尊的振武节度使'),('宋瑶','参与推尊的天德节度使'),('刘守光','被六镇推尊的燕王')],
      when='911年刘守光求尊之后；确日未载',place='晋、赵、义武、昭义、振武、天德、燕',
      note='六镇推尊是晋方以骄其心的政治举措，不等于梁廷正式授尚父。')
event('liang_invests_shouguang', '朱温授刘守光河北道采访使并遣王瞳、史彦群册命', 8,
      '上亦知其狂愚，乃以守光为河北道采访使，遣阁门使王瞳、受旨史彦群册命之。',
      [('朱温','授采访使并遣使册命的梁帝'),('刘守光','获授河北道采访使'),('王瞳','梁方册命使'),('史彦群','梁方册命使')],
      when='911年六镇推尊之后；确日未载',place='后梁、燕',
      note='梁廷授职为河北道采访使，不误写为梁廷授尚父。')
event('shouguang_rejects_shangfu_only', '刘守光嫌尚父非帝位，令备即位仪并拘梁使', 8,
      '守光怒，投之于地，曰：“我地方二千里，带甲三十万，直作河北天子，谁能禁我！尚父何足为哉！”命趣具即帝位之仪，械系瞳、彦群及诸道使者于狱，既而皆释之。',
      [('刘守光','命备称帝仪式并拘后释诸使'),('王瞳','被刘守光拘禁后释放的梁使'),('史彦群','被刘守光拘禁后释放的梁使')],
      when='911年乙卯后；确日未载',place='燕',
      note='“带甲三十万”是刘守光自夸，不当确凿兵籍；正式称帝见后续段落。')

event('yang_shihou_xingzhou', '朱温命杨师厚率三万兵屯邢州', 9,
      '帝命杨师厚将兵三万屯邢州。',
      [('朱温','命杨师厚赴邢州屯兵的梁帝'),('杨师厚','率三万梁兵屯邢州')],
      when='911年本段条；确日未载',place='邢州',
      note='主书所载三万为此部规模，未换算实到人数。')

event('shu_raids_qi_july', '蜀诸将屡破岐兵，王建秋七月西还', 10,
      '蜀诸将击岐兵，屡破之。秋，七月，蜀主西还，留御营使昌王宗钅岁屯利州。',
      [('王建','秋七月西还的蜀主'),('宗钅岁','被留屯利州的前蜀昌王')],
      when='911年秋七月西还；屡破岐兵起止未详',place='利州、蜀岐边境',
      note='“宗钅岁”为底本拆字，同910年王宗鐬；这里只记其留屯，诸将战果未归给王宗鐬。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 11):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷268乾化元年三月至七月第1—10段连续处理；追叙、拟亲与异名另注。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=268, year=911,
    primary_source_key=main1, primary_source_keys=[main1],
    paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v268-y0911-p011',
    coverage='卷268乾化元年三月至七月第1—10段，刘隐身后继承、蜀岐战事、刘守光称帝筹划。',
    supplements=supplements,status=status,
    textual_reviews=[{'paragraph_id':Q[2]['id'],'note':'《新五代史》刘隐卒后作龑代立，清海节度使任命另作乾化二年；主书刘岩本年甲辰任命保留，异名与纪年待纸本互校。'},
                     {'paragraph_id':Q[8]['id'],'note':'刘守光称帝试探有“尝”，时间只知在正式称帝之前；六镇推尚父和梁授河北道采访使不合并。'},
                     {'paragraph_id':Q[10]['id'],'note':'底本昌王宗钅岁为拆字，按910年同人王宗鐬复用，出处原字保留。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({key:len(value) for key,value in B.items() if isinstance(value,list)})
