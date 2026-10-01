"""Curate Tongjian 264, year 903, consecutive paragraphs 37–42."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 55))
primary = 'tongjian-264-903-august'
september = 'tongjian-264-903-september'
old_zhu = 'jiuwudaishi-017-tian-zhu'
old_wang = 'jiuwudaishi-017-wang-wife'
new_xu = 'xinwudaishi-061-xu-wen'
new_annals = 'xinwudaishi-061-yang-xingmi'
B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p037-p042',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-05/sources/library' / primary, 'e36b962', '司马光等'),
    (september, P / 'sources/library' / september, '6a1b981', '司马光等'),
    (old_zhu, P / 'sources/library' / old_zhu, '6a1b981', '薛居正等'),
    (old_wang, P / 'sources/library' / old_wang, '6a1b981', '薛居正等'),
    (new_xu, P / 'sources/library' / new_xu, '6a1b981', '欧阳修等'),
    (new_annals, P.parent / 'part-02/sources/library' / new_annals, '71feb52', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, september)}
for n in range(37, 43):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本','硃延寿':'朱延寿','王坛':'王檀','坛':'王檀','硃氏（杨行密夫人）':'朱氏（杨行密夫人）'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_07_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷264·天复三年（903）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷264天复三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=903):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_264_0903_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '903年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '903年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_264_0903_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_264_0903_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 37: Zhu Yanshou's execution, the Wang wife's death, and a retrospective anecdote.
event('yang_fakes_blindness','杨行密诈称失明，借授军府之名召朱延寿',37,
      '杨行密诈为目疾，对延寿使者多错乱所见，或触柱仆地。谓夫人曰：“吾不幸失明，诸子皆幼，军府事当悉以授三舅。”夫人屡以书报延寿，行密又自遣召之，阴令徐温为之备。',
      [('杨行密','设计召人者'),('朱氏（杨行密夫人）','向弟传书者'),('朱延寿','受召者'),('徐温','预备者')],
      when='903年九月；确日未载',place='广陵',note='目疾为杨行密佯装；“三舅”指其妻弟朱延寿，军府交付只是诱召的话术。')
event('zhu_yanshou_executed','朱延寿抵广陵后被杨行密执杀',37,
      '延寿至广陵，行密迎及寝门，执而杀之。',
      [('朱延寿','被杀者'),('杨行密','执杀者')],when='903年九月；确日未载',place='广陵',
      note='主书记广陵寝门；旧五代史卷17记“邇揚州一舍”被杀，地点异说并存。')
event('xu_wen_quiets_zhu_troops','徐温安抚朱延寿部兵，朱延寿兄弟被斩、朱夫人被黜',37,
      '部兵惊扰，徐温谕之，皆听命，遂斩延寿兄弟，黜硃夫人。',
      [('徐温','安抚部兵者'),('朱延寿','兄弟被斩者'),('朱氏（杨行密夫人）','被黜者')],
      when='朱延寿被杀后；903年九月',place='广陵',
      note='原文未列被斩兄弟姓名，不把朱延寿再次算作此次斩杀；“硃夫人”按已确认身份复用。')
event('wang_wife_self_immolates','朱延寿妻王氏获知失联后焚府自尽',37,
      '一日，使不至，王氏曰：“事可知矣！”部分僮仆，授兵阖门，捕骑至，乃集家人，聚宝货，发百燎焚府舍，曰：“妾誓不以皎然之躯为仇人所辱。”赴火而死。',
      [('王氏（朱延寿妻）','组织守门并投火者'),('朱延寿','失联丈夫')],
      when='朱延寿赴召后；903年九月',place='寿州',
      note='王氏此前要求每日遣使报平安；“事可知”是她的判断，死因与家人结局依原文分别理解。')
event('zhu_yanshou_strict_discipline','朱延寿旧时因违命斩请战士卒',37,
      '延寿用法严，好以寡击众，尝遣二百人与汴兵战，有一人应留者，请行，延寿以违命，立斩之。',
      [('朱延寿','下令斩士卒者')],when='“尝”追叙；确年未载',year=None,
      note='此为生前用法轶事，不系于903年九月。')

# 38: the hostage episode, two naval battles, and Xu Wan's delivery.
event('tian_takes_li_family','田頵袭升州，得李神福妻子并以之要挟',38,
      '田頵袭升州，得李神福妻子，善遇之。神福自鄂州东下，頵遣使谓之曰：“公见机，与公分地而王；不然，妻子无遗！”',
      [('田頵','袭城并遣使者'),('李神福','家属被获者')],when='903年九月；确日未载',place='升州',
      note='“善遇”与后续威胁均按史书记；分地而王是田頵的提议，并非已实现。')
event('li_shenfu_refuses_tian','李神福拒田頵诱降并斩其使',38,
      '神福曰：“吾以卒伍事吴王，今为上将，义不以妻子易其志。頵有老母，不顾而反，三纲且不知，乌足与言乎！”斩使者而进，士卒皆感励。',
      [('李神福','拒降并斩使者'),('田頵','诱降者')],when='903年九月；确日未载',
      note='引语是李神福的立场和对田頵的评语；不把三纲评语转作客观事实。')
event('jiyangji_battle','李神福丁未于吉阳矶击败王檀、汪建水军',38,
      '丁未，神福至吉阳矶，与坛、建遇。坛、建执其子承鼎示之，神福命左右射之。',
      [('李神福','战胜方统帅'),('王檀','败方将领'),('汪建','败方将领'),('李承鼎','被作为人质出示者')],
      when='903年九月丁未',place='吉阳矶',
      note='原段首作王檀，后作“坛”，按同一将领归并；神福下令射向人质，不推定承鼎死亡。')
event('jiyangji_fire_attack','李神福佯败诱敌后顺流纵火破楼船',38,
      '神福阳败，引舟溯流而上。坛、建追之，神福复还，顺流击之。坛、建楼船大列火炬，神福令军中曰：“望火炬则击之。”坛、建军皆灭火，旗帜交杂，神福因风纵火，焚其舰，坛、建大败，士卒焚溺死者甚众。',
      [('李神福','用计并纵火者'),('王檀','败方将领'),('汪建','败方将领')],
      when='903年九月丁未',place='吉阳矶',note='单录战术及结果；“甚众”不折算人数。')
event('wankou_battle','李神福戊申再战皖口，王檀与汪建仅身免',38,
      '戊申，又战于皖口，坛、建仅以身免。',
      [('李神福','胜方统帅'),('王檀','败方将领'),('汪建','败方将领')],
      when='903年九月戊申',place='皖口',note='与前日吉阳矶之战分开。')
event('xu_wan_returned_qian','徐绾被杨行密送交钱镠，钱镠剖心祭高渭',38,
      '获徐绾，行密以槛车载之，遗钱镠。镠剖其心以祭高渭。',
      [('徐绾','被获并送交者'),('杨行密','移交者'),('钱镠','处死并祭祀者'),('高渭','被祭者')],
      when='903年九月；确日未载',note='先前徐绾叛乱与高渭遇害已在902年录入，此处仅记移交处置。')

# 39: converging forces against Tian Jun.
event('li_shenfu_holds_tian','田頵亲率水军迎战，李神福坚壁并请断其归路',39,
      '頵闻坛、建败，自将水军逆战，神福曰：“贼弃城而来，此天亡也！”临江坚壁不战，遣行告行密，请发步兵断其归路。',
      [('田頵','亲率水军者'),('李神福','坚壁并请援者'),('杨行密','受请者')],
      when='903年九月；确日未载',place='江边',note='“天亡也”只是李神福的判断，未将双方写成已经交战。')
event('yang_sends_tai_meng','杨行密遣台濛应李神福，并召王茂章会师',39,
      '行密遣涟水制置使台濛将兵应之。王茂章攻润州，久未下，行密命茂章引兵会濛击頵。',
      [('杨行密','遣军并调兵者'),('台濛','率步兵者'),('王茂章','受命会师者'),('田頵','讨伐目标')],
      when='903年九月；确日未载',place='涟水、润州',note='王茂章此前攻润州未下，改令会师；后续战果留待下段。')

# 40–42: short chronological notices and Wang Shifan's surrender.
event('liu_chongba_di','刘重霸辛亥攻克棣州并杀刺史邵播',40,
      '辛亥，汴将刘重霸拔棣州，执刺史邵播，杀之。',
      [('刘重霸','攻城并杀刺史者'),('邵播','被杀刺史')],when='903年九月辛亥',place='棣州')
event('zhu_luoyang_ill','朱全忠甲寅赴洛阳遇疾，返大梁',41,
      '甲寅，硃全忠如洛阳，遇疾，复还大梁。',
      [('朱温','赴洛阳后返还者')],when='903年九月甲寅',place='洛阳、大梁',
      note='“硃”按既有朱温实体归并，原文保留本字。')
event('wang_shifan_surrenders','王师范遣李嗣业与弟王师悦向杨师厚请降',42,
      '戊午，王师范遣副使李嗣业及弟师悦请降于杨师厚',
      [('王师范','遣使请降者'),('李嗣业','请降副使'),('王师悦','请降之弟'),('杨师厚','受降者')],
      when='903年九月戊午',place='青州附近',
      note='王师范随后关于被迫举兵的说辞作为其自述，不据此认定御札真伪。')
event('wang_shifan_explains_revolt','王师范自述韩全诲、李茂贞曾持朱书御札令其举兵',42,
      '师范非敢背德，韩全诲、李茂贞以硃书御札使之举兵，师范不敢违。',
      [('王师范','陈述者'),('韩全诲','被陈述的持札者'),('李茂贞','被陈述的持札者')],
      when='903年九月戊午请降时',
      note='全句为王师范请降说辞；不能凭此段确认朱书御札真实，也不将举兵重记为此日。')
event('wang_offers_shilu_hostage','王师范请求以弟王师鲁为质',42,
      '仍请以其弟师鲁为质。',
      [('王师范','提出人质者'),('王师鲁','被提议为人质者')],
      when='903年九月戊午请降时',
      note='“请”仅表提议；原文未写王师鲁已经交出。')
event('zhu_accepts_wang_surrender','朱全忠虑京畿生变而受王师范降，派将守诸州',42,
      '乃受师范降，选诸将使守登、莱、淄、棣等州，即以师范权淄青留后。',
      [('朱温','决定受降并布置守军者'),('王师范','受任权留后者')],
      when='903年九月戊午后；确日未载',place='登、莱、淄、棣',
      note='前文李茂贞、杨崇本可能逼京是朱全忠担忧，并非本段证实已举兵。')
event('wang_shifan_liu_xun_plea','王师范请释刘鄩据兖州之罪并遣使告知',42,
      '师范仍言先遣行军司马刘鄩将兵五千据兗州，非其自专，愿释其罪。亦遣使语鄩。',
      [('王师范','请释罪并遣使者'),('刘鄩','兖州驻将')],
      when='903年九月戊午后；确日未载',place='兖州',
      note='“非其自专”为王师范所言；原文只见请求赦免，未见朱全忠已答应。')

# Explicit family relations only; unnamed kin receive no fabricated names.
for code,a,b,kind,description,n,quote,note in [
    ('zhu_wang_wife','王氏（朱延寿妻）','朱延寿','妻子','王氏是朱延寿的妻子。',37,'其妻王氏','“其”承上文朱延寿，王氏本名未载。'),
    ('li_chengding_son','李承鼎','李神福','儿子','李承鼎是李神福的儿子。',38,'其子承鼎','“其”承上文李神福。'),
    ('wang_shiyue_younger','王师悦','王师范','弟弟','王师悦是王师范的弟弟。',42,'弟师悦','原文明示弟。'),
    ('wang_shilu_younger','王师鲁','王师范','弟弟','王师鲁是王师范的弟弟。',42,'其弟师鲁','原文明示弟。'),
]:
    pa=person(a,n,kind,quote)
    pb=person(b,n,kind,quote)
    key='relationship_zztj_264_0903_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=pa,person_b_key=pb,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)

extra(old_zhu,'event','event_zztj_264_0903_zhu_yanshou_executed','description',
      '《旧五代史》卷十七记朱延寿赴召近扬州一舍时被杀。',
      '延壽飛騎赴命，邇揚州一舍，行密使人殺之',37,'conflicts',
      '与《通鉴》“至广陵，迎及寝门”地点不同；保留双方原说，不折衷地点。')
extra(old_wang,'event','event_zztj_264_0903_wang_wife_self_immolates','description',
      '《旧五代史》卷十七另记王氏因每日使者中断而焚府自尽。',
      '一日，介不至，王氏曰：「事可知矣！」',37,'corroborates',
      '只引卷十七正文；后接《五代史补》转引作为注，不当作本次独立确证。')
extra(new_xu,'event','event_zztj_264_0903_yang_fakes_blindness','description',
      '《新五代史》徐温传称佯目疾之计由严可求所谋，徐温转教杨行密。',
      '溫用其客嚴可求謀，教行密陽為目疾',37,'adds',
      '《通鉴》只记徐温预备；严可求策源作为新五代史独立归属说法，不改主书叙述。')
extra(new_annals,'event','event_zztj_264_0903_jiyangji_battle','description',
      '《新五代史》杨行密世家记李神福在吉阳矶败王坛兵。',
      '遂敗壇兵于吉陽',38,'corroborates',
      '新五代史作王壇，与通鉴段首王檀字形不同；视为同将，异文保留。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(37,43):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第37—42段连续处理；繁简与异体字归一实体，原文照录；地点异说、言辞与追叙分列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary,september],
    paragraphs=[Q[n]['id'] for n in range(37,43)],next_paragraph=Q[43]['id'],
    coverage='卷264天复三年共54个非空段落中的第37—42段连续处理；朱延寿之死、吉阳矶及皖口之战与王师范请降。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
