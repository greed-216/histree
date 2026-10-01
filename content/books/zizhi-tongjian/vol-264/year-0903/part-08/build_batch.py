"""Curate Tongjian 264, year 903, consecutive paragraphs 43–49."""
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
primary = 'tongjian-264-903-september'
october = 'tongjian-264-903-october'
old_qingzhou = 'jiuwudaishi-002-qingzhou'
old_liu = 'jiuwudaishi-023-liu-xun'
new_liu_defense = 'xinwudaishi-022-liu-xun-defense'
new_liu_surrender = 'xinwudaishi-022-liu-xun-surrender'
old_zhao = 'jiuwudaishi-017-zhao-kuangning'
new_yang = 'xinwudaishi-061-yang-xingmi'
B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p043-p049',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-07/sources/library' / primary, '6a1b981', '司马光等'),
    (october, P / 'sources/library' / october, 'a3ad61d', '司马光等'),
    (old_qingzhou, P.parent / 'part-06/sources/library' / old_qingzhou, '33d866a', '薛居正等'),
    (old_liu, P / 'sources/library' / old_liu, 'ddaebc2', '薛居正等'),
    (new_liu_defense, P / 'sources/library' / new_liu_defense, 'ddaebc2', '欧阳修等'),
    (new_liu_surrender, P / 'sources/library' / new_liu_surrender, 'ddaebc2', '欧阳修等'),
    (old_zhao, P / 'sources/library' / old_zhao, 'ddaebc2', '薛居正等'),
    (new_yang, P.parent / 'part-02/sources/library' / new_yang, '71feb52', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, october)}
for n in range(43, 50):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本','硃延寿':'朱延寿','王坛':'王檀','坛':'王檀','硃氏（杨行密夫人）':'朱氏（杨行密夫人）','郭行頵':'郭行悰','侯矩':'王宗矩','硃友伦':'朱友伦','硃全忠':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_08_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_264_0903_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 43: two engagements and the subsequent collapse of Tian Jun's field forces.
event('tian_deploys_wuhu','田頵留郭行悰、王檀与汪建屯芜湖以拒李神福',43,
      '田頵闻台濛将至，自将步骑逆战，留其将郭行頵以精兵二万及王坛、汪建水军屯芜湖，以拒李神福。',
      [('田頵','分兵者'),('郭行悰','留守芜湖者'),('王檀','水军将领'),('汪建','水军将领'),('李神福','被拒之将')],
      when='903年十月戊辰前；确日未载',place='芜湖',
      note='底本先作郭行頵、后作郭行悰，其他版本同句作郭行悰，暂作同一人并记录异文；“王坛”按前段王檀归并。')
event('tian_underestimates_tai','田頵闻台濛营小而轻敌，不召芜湖兵',43,
      '觇者言：“濛营寨褊小，才容二千人。”頵易之，不召外兵。',
      [('田頵','轻敌不召兵者'),('台濛','被估计营寨者')],when='903年十月戊辰前；确日未载',
      note='营寨仅容二千人是觇者所言，“易之”是田頵判断，不能推成台濛实际只有二千兵。')
event('tai_meng_guangde','台濛十月戊辰于广德趁田頵诸将受书时突击得胜',43,
      '冬，十月，戊辰，与頵遇于广德。濛先以杨行密书遍赐頵将，皆下马拜受。濛因其挫伏，纵兵击之，頵兵遂败。',
      [('台濛','突击胜方'),('田頵','败方'),('杨行密','书信发出者')],
      when='903年十月戊辰',place='广德',note='杨行密书信内容未见，不能补写招降条款。')
event('tai_meng_huangchi','台濛在黄池佯退设伏再败田頵',43,
      '又战于黄池，兵交，濛伪走，頵追之，遇伏，大败，奔还宣州城守，濛引兵围之。',
      [('台濛','设伏并围宣州者'),('田頵','败退守城者')],
      when='903年十月戊辰后；确日未载',place='黄池、宣州',
      note='黄池战、退守宣州和围城为连续后果；与广德之战分列。')
event('wuhu_forces_surrender','郭行悰、王檀、汪建及诸戍降杨行密',43,
      '頵亟召芜湖兵还，不得入。郭行悰、王坛、汪建及当涂、广德诸戍皆帅其众降。',
      [('田頵','召兵未果者'),('郭行悰','率部降者'),('王檀','率部降者'),('汪建','率部降者'),('杨行密','受降方')],
      when='903年十月黄池战后；确日未载',place='芜湖、当涂、广德',
      note='原文未列具体受降官员；“杨行密”是阵营主体，不称其亲临现场。')
event('yang_returns_wang_runzhou','杨行密令王茂章复攻润州',43,
      '行密以台濛已破田悰，命王茂章复引兵攻润州。',
      [('杨行密','下令者'),('王茂章','复攻润州者'),('台濛','既有战果者')],
      when='903年十月黄池战后；确日未载',place='润州',
      note='底本作“田悰”，结合本段主语与前后文校读为田頵；原引句不改字。')

# 44: Hou Ju's surrender and the Shu military administration in Kui.
event('hou_ju_returns_kui','侯矩随成汭救鄂州，成汭死后返夔州',44,
      '初，夔州刺史侯矩从成汭救鄂州，汭死，矩奔还。',
      [('王宗矩','当时名侯矩的夔州刺史'),('成汭','战死者')],
      when='“初”追叙；成汭死后，确日未载',year=None,place='鄂州、夔州',
      note='本段稍后明记侯矩更姓名为王宗矩，两名同一人；追叙不直接定为十月。')
event('hou_ju_surrenders_kui','侯矩十月甲戌以夔州降王宗本，王宗本定四州',44,
      '会王宗本兵至，甲戌，矩以州降之，宗本遂定夔、忠、万、施四州。',
      [('王宗矩','以夔州降者'),('谢从本','受降并定四州者')],
      when='903年十月甲戌',place='夔州、忠州、万州、施州',
      note='王宗本按本站已有谢从本／王宗本同一人物记录复用。')
event('hou_ju_renamed','王建复任侯矩为夔州刺史并更名王宗矩',44,
      '王建复以矩为夔州刺史，更其姓名曰王宗矩。宗矩，易州人也。',
      [('王建','任命并赐名者'),('王宗矩','受任且改名者')],
      when='903年十月甲戌后；确日未载',place='夔州',
      note='王宗矩旧名侯矩；“易州人”仅是籍贯，不据改姓推断收养关系。')
event('shu_garrisons_kui','蜀方弃归峡两州并屯军夔州',44,
      '蜀之议者，以瞿唐，蜀之险要，乃弃归、峡，屯军夔州。',
      [],when='903年十月甲戌后；确日未载',place='夔州',
      note='战略理由归于“蜀之议者”，原文没有指名个人提出者。')
event('wutai_moves_to_fu','王建任王宗本武泰留后，准其移镇治涪州',44,
      '建以宗本为武泰留后。武泰军旧治黔州，宗本以其地多瘴疠，清徙治涪州，建许之。',
      [('王建','任命并许可者'),('谢从本','受任并请移治者')],
      when='903年十月甲戌后；确日未载',place='黔州、涪州',
      note='底本“清徙治”疑为“请徙治”讹字；按上下文仅写王宗本请求、王建准许，不改来源快照。')

# 45: Liu Xun's defense, managed surrender, and appointment.
event('liu_xun_ge_mother','刘鄩使葛从周母登兖州城，葛从周因此缓攻',45,
      '葛从周急攻兗州，刘鄩使从周母乘板舆登城，谓从周曰：“刘将军事我不异于汝，新妇辈皆安居，人各为其主，汝可察之。”从周歔欷而退，攻城为之缓。',
      [('葛从周','攻城后缓攻者'),('刘鄩','安排登城者'),('葛从周母','登城劝说者')],
      when='903年十月丁丑前；确日未载',place='兖州',
      note='葛母姓名未载；其发言是守城方所述家属状况。')
event('liu_xun_defends_yan','刘鄩遣出妇孺老疾，与少壮同守兖州并约束军纪',45,
      '鄩悉简妇人及民之老疾不足当敌者出之，独与少壮者同辛苦，分衣食，坚守以扞敌。号令整肃，兵不为暴，民皆安堵',
      [('刘鄩','守城统帅')],when='903年十月丁丑前；确日未载',place='兖州',
      note='“民皆安堵”为史书概括，不假定所有百姓均留城内。')
event('liu_xun_wang_yanwen','王彦温逃降后刘鄩施疑计，葛军斩王彦温',45,
      '节度副使王彦温逾城出降，城上卒多从之，不可遏。鄩遣人从容语彦温曰：“军士非素遣者，勿多与之俱。”又遣人徇于城上曰：“军士非素遣从副使而敢擅往者，族之！”士卒皆惶惑不敢出。敌人果疑彦温，斩之城下，由是众心益固。',
      [('王彦温','逃降后被斩者'),('刘鄩','施疑计者')],
      when='903年十月丁丑前；确日未载',place='兖州',
      note='“非素遣者”是刘鄩制造怀疑的话术，不能当作王彦温实受密令。')
event('liu_xun_waits_for_order','刘鄩坚持待王师范使者到后于丁丑出降',45,
      '鄩曰：“受王公命守此城，一旦见王公失势，不俟其命而降，非所以事上也。”及师范使者至，丁丑，始出降。',
      [('刘鄩','守令并出降者'),('王师范','派使准降者')],
      when='903年十月丁丑',place='兖州',
      note='“丁丑”承十月纪事；《旧五代史》刘鄩传另系天复三年十一月，保留月分异说。')
event('liu_xun_arrives_daliang','葛从周资送刘鄩，刘鄩素服乘驴至大梁',45,
      '从周为具赍装，送鄩诣大梁。鄩曰：“降将未受梁王宽释之命，安敢乘马衣裘乎！”乃素服乘驴至大梁。',
      [('葛从周','资送者'),('刘鄩','降将赴大梁者')],
      when='903年十月丁丑后；确日未载',place='大梁',
      note='素服乘驴与谢绝马裘为刘鄩所述处境，不外推受刑。')
event('zhu_appoints_liu_xun','朱全忠任刘鄩元从都押牙，后表为保大留后',45,
      '以为元从都押牙。是时四镇将吏皆功臣、旧人，鄩一旦以降将居其上，诸将具军礼拜于廷，鄩坐受自如，全忠益奇之。未几，表为保大留后。',
      [('朱温','任命及上表者'),('刘鄩','受任者')],
      when='903年十月丁丑后及“未几”；确日未载',place='大梁',
      note='两项职任有先后，“未几”间隔不可换算；官名按主书原文。')
event('kang_replaces_ge','葛从周久病，朱全忠以康怀英代任泰宁节度使',45,
      '葛从周久病，全忠以康怀英为泰宁节度使代之。',
      [('葛从周','因病被代者'),('朱温','任命者'),('康怀英','新任者')],
      when='903年十月丁丑后；确日未载',place='泰宁军',
      note='“久病”不据此推断疾病起始日。')

# 46–49: court, Jingnan, Wu-Yue reinforcement, and November frontier security.
event('zhu_youlun_polo_death','朱友伦十月辛巳击球坠马身亡',46,
      '辛巳，宿卫都指挥使硃友伦与客击球于左军，坠马而卒。',
      [('朱友伦','坠马身亡者')],when='903年十月辛巳',place='左军',
      note='“硃友伦”按既有人物朱友伦归并；左军为原文场所，不标地理坐标。')
event('zhu_kills_polo_guests','朱全忠疑崔胤致朱友伦之死，杀同戏十余人',46,
      '全忠悲怒，疑崔胤故为之，凡与同戏者十馀人尽杀之',
      [('朱温','猜疑并杀人者'),('崔胤','被怀疑者')],
      when='903年十月辛巳后；确日未载',
      note='崔胤涉事只是朱全忠之疑，原文未证实其谋害；十余人为主书记数。')
event('zhu_youliang_guard','朱全忠遣兄子朱友谅代掌宿卫',46,
      '遣其兄子友谅代典宿卫。',
      [('朱温','遣任者'),('朱友谅','代掌宿卫者')],
      when='903年十月辛巳后；确日未载',
      note='“其兄子”承朱全忠，朱友谅为其兄之子，未据此推定朱友伦与友谅的亲属关系。')
event('zhao_kuangning_jingnan','赵匡凝袭荆南，朗人弃城，表弟赵匡明留后',47,
      '山南东道节度使赵匡凝遣兵袭荆南，朗人弃城走，匡凝表其弟匡明为荆南留后。',
      [('赵匡凝','遣兵并上表者'),('赵匡明','被表荐留后者')],
      when='903年十月；确日未载',place='荆南',
      note='“表”为赵匡凝上奏，不直接写成朝廷正式授命。')
event('zhao_brothers_tribute','赵匡凝兄弟持续向唐廷输送财赋',47,
      '时天子微弱，诸道财赋多不上供，惟匡凝兄弟委输不绝。',
      [('赵匡凝','输贡者'),('赵匡明','其弟兼输贡者')],
      when='903年前后持续；起止未载',year=None,
      note='持续性总述，不定为903年十月单次输贡；“诸道多不上供”属主书概述。')
event('yang_requests_qian_aid','杨行密向钱镠求援，钱镠遣方永珍与钱镒分屯润宣',48,
      '杨行密求兵于钱镠，镠遣方永珍屯润州，从弟镒屯宣州。',
      [('杨行密','求援者'),('钱镠','遣兵者'),('方永珍','屯润州者'),('钱镒','屯宣州者')],
      when='903年十月；确日未载',place='润州、宣州',
      note='“从弟镒”依文脉为钱镠从弟；不将两处驻军写成已交战。')
event('qian_sends_yang_xi_muzhou','钱镠遣杨习攻睦州',48,
      '又遣指挥使杨习攻睦州。',
      [('钱镠','遣军者'),('杨习','攻睦州者')],
      when='903年十月；确日未载',place='睦州',
      note='只录出兵攻城，原文未记此处结果。')
event('zhu_hezhong_cavalry','朱全忠疑凤翔邠州将劫迁天子，十一月遣骑屯河中',49,
      '凤翔、邠州屡出兵近京畿，硃全忠疑其复有劫迁之谋，十一月，发骑兵屯河中。',
      [('朱温','猜疑并遣骑者')],
      when='903年十一月；确日未载',place='河中',
      note='“复有劫迁之谋”仅为朱全忠怀疑；凤翔、邠州出兵近京与其推测分开。')

# Directional relations; names and aliases are verified against earlier batches.
for code,a,b,kind,description,n,quote,note in [
    ('zhu_youliang_nephew','朱友谅','朱温','侄子','朱友谅是朱全忠的兄子。',46,'其兄子友谅','“其”承朱全忠，关系方向为朱友谅相对于朱全忠。'),
    ('zhao_kuangming_younger','赵匡明','赵匡凝','弟弟','赵匡明是赵匡凝的弟弟。',47,'其弟匡明','原文明示“弟”。'),
    ('qian_yi_cousin','钱镒','钱镠','从弟','钱镒是钱镠的从弟。',48,'从弟镒','沿用原文“从弟”，不进一步指定支系。'),
]:
    pa=person(a,n,kind,quote)
    pb=person(b,n,kind,quote)
    key='relationship_zztj_264_0903_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=pa,person_b_key=pb,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)

guo=next(x for x in B['people'] if x['name']=='郭行悰')
guo['aliases']=sorted(set(guo.get('aliases',[])+['郭行頵']))
hou=next(x for x in B['people'] if x['name']=='王宗矩')
hou['aliases']=sorted(set(hou.get('aliases',[])+['侯矩']))

extra(new_yang,'event','event_zztj_264_0903_tai_meng_huangchi','description',
      '《新五代史》杨行密世家概记台濛击败田頵。',
      '行密別遣臺濛擊頵，頵敗死',43,'corroborates',
      '只以“击頵”印证讨伐；“败死”属后续十二月结果，本段未前置为十月。')
extra(old_liu,'event','event_zztj_264_0903_liu_xun_waits_for_order','time_original',
      '《旧五代史》刘鄩传记其出城听命为天复三年十一月。',
      '天復三年十一月，師範告降，且言先差行軍司馬劉鄩領兵入兗州，請釋其罪，亦以告鄩，鄩即出城聽命',45,'conflicts',
      '《通鉴》此处仍在十月，且明书丁丑；两书月份不合，不擅自择一抹去。')
extra(new_liu_defense,'event','event_zztj_264_0903_liu_xun_wang_yanwen','description',
      '《新五代史》刘鄩传也记王彦温出逃、刘鄩扬言使其遭梁军怀疑而被斩。',
      '果疑彥溫非實降者，斬之城下',45,'corroborates',
      '叙事接近《通鉴》，可能依赖同源材料，不当作完全独立的战况确认。')
extra(new_liu_surrender,'event','event_zztj_264_0903_liu_xun_arrives_daliang','description',
      '《新五代史》刘鄩传也记刘鄩素服乘驴赴梁。',
      '乃素服乘驢歸梁',45,'corroborates',
      '与主书叙事相近，保留独立书目索引但不扩大确证强度。')
extra(old_qingzhou,'event','event_zztj_264_0903_zhu_youlun_polo_death','description',
      '《旧五代史》梁太祖纪记朱友伦十月辛巳击鞠坠马，卒于长安。',
      '十月辛巳，護駕都指揮使硃友倫因擊鞠墮馬，卒于長安',46,'corroborates',
      '旧书明载长安，主书只记左军；地点细节保留为旧书补充，不改主书地点字段。')
extra(old_zhao,'event','event_zztj_264_0903_zhao_kuangning_jingnan','description',
      '《旧五代史》赵匡凝传也记成汭败后匡凝表弟匡明为荆南留后。',
      '及成汭敗於鄂州，匡凝表其弟匡明為荊南留後',47,'corroborates',
      '旧书无具体月日；两书记述可能承袭共同材料。')
extra(old_zhao,'event','event_zztj_264_0903_zhao_brothers_tribute','description',
      '《旧五代史》赵匡凝传也称匡凝兄弟贡赋不绝。',
      '貢賦不絕',47,'corroborates',
      '旧书是对兄弟的总评，不能反推某一月的具体贡额或次数。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(43,50):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第43—49段连续处理；人名讹字原文照录，别名归一；追叙、猜疑及书证月份异说分列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary,primary_source_keys=[primary,october],
    paragraphs=[Q[n]['id'] for n in range(43,50)],next_paragraph=Q[50]['id'],
    coverage='卷264天复三年共54个非空段落中的第43—49段连续处理；十月广德黄池、夔州、兖州及十一月河中。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
