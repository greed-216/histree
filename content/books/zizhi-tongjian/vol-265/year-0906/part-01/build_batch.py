"""Curate Tongjian 265, year 906, consecutive paragraphs 1–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 43))
primary = 'tongjian-265-905-yearend'
old_wei = 'jiuwudaishi-002-wei-guards'
old_wang = 'jiuwudaishi-023-wangmaozhang'
old_tang = 'jiutangshu-020-906-january'
new_wei = 'xinwudaishi-001-906-wei-guards'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0906-p001-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent.parent / 'year-0905/part-09/sources/library' / primary, '49e7efb9', '司马光等'),
    (old_wei, P / 'sources/library' / old_wei, '26e932a5', '薛居正等'),
    (old_wang, P / 'sources/library' / old_wang, '26e932a5', '薛居正等'),
    (old_tang, P / 'sources/library' / old_tang, '26e932a5', '刘昫等'),
    (new_wei, P / 'sources/library' / new_wei, '26e932a5', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary,)}
for n in range(1, 9):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '景仁':'王茂章', '王景仁':'王茂章', '绍威':'罗绍威', '镠':'钱镠', '茂章':'王茂章', '王宗阮':'文武坚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0906_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐三年（906）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷265天祐三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=906, time_quote=None):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0906_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '906年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '906年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0906_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0906_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1: This is Han Xun's report, not independently verified troop movement.
event('han_xun_reports_tubo_at_zonggao', '韩逊奏称吐番骑兵屯宗高谷并拟取凉州', 1,
      '春，正月，壬戌，灵武节度使韩逊奏吐番七千馀骑营于宗高谷，将击嗢末及取凉州。',
      [('韩逊', '奏报者')], when='906年正月壬戌', place='宗高谷',
      note='七千余骑、拟击嗢末及取凉州均为韩逊奏报内容；本段未记实际交战或攻取。')

# 2: The attack sent in 905 reaches Xuanzhou; flight, city stabilization and appointment follow.
event('li_jian_reaches_xuanzhou_wang_flees', '李简兵至宣州，王茂章率众奔两浙', 2,
      '李简兵奄至宣州，王茂章度不能守，帅众奔两浙。',
      [('李简', '所部突至宣州者'), ('王茂章', '率众撤往两浙者')],
      when='906年正月条；确日未载', place='宣州、两浙',
      note='承上年杨渥遣李简事件；不把上年派兵日写成抵达日。')
event('diao_yanneng_stabilizes_xuanzhou', '刁彦能留宣州谕众以安定城中', 2,
      '亲兵上蔡刁彦能辞以母老，不从行，登城谕众曰：“王府命我招谕汝曹，大兵行至矣。”众由是定。',
      [('刁彦能', '留城登城谕众者')],
      when='王茂章出奔后；确日未载', place='宣州',
      note='“王府命我招谕”是刁彦能对众之言，主书未证明王府确有此命。')
event('tao_ya_withdraws_qian_recovers_muzhou', '陶雅还歙州，钱镠复取睦州', 2,
      '陶雅畏茂章断其归路，引兵还歙州，钱镠复取睦州。',
      [('陶雅', '退回歙州者'), ('钱镠', '复取睦州者')],
      when='王茂章出奔后；确日未载', place='歙州、睦州',
      note='“畏茂章断其归路”为主书所述动机，不推断两军发生交战。')
event('qian_appoints_wang_jingren', '钱镠用王茂章为镇东节度副使并改名景仁', 2,
      '镠以茂章为镇东节度副使，更名景仁。',
      [('钱镠', '任用并更名者'), ('王茂章', '受任并改名王景仁者')],
      when='王茂章奔两浙后；确日未载', place='两浙',
      note='王茂章、王景仁为同一人；不新建第二人物。旧五代史亦以王景仁列传，并有本名茂章之注。')

event('qu_chengyu_awarded_chancellor_title', '唐廷乙丑加曲承裕同平章事', 3,
      '乙丑，加静海节度使曲承裕同平章事。',
      [('曲承裕', '加同平章事者')], when='906年正月乙丑',
      note='只记加衔，不自行推断静海军辖境变化。')

# 4: Retrospective origins of Wei's palace guard are deliberately undated.
event('tian_chengsi_recruits_wei_guards', '田承嗣昔年募魏博六州牙军', 4,
      '初，田承嗣镇魏博，选募六州骁勇之士五千人为牙军，厚其给赐以自卫，为腹心。',
      [('田承嗣', '选募牙军者')], when='“初”所叙旧事；确年未载', year=None, place='魏博',
      note='该段追叙牙军起源；五千人为初募数，不等于906年杀戮人数。')
event('luo_seeks_zhu_help_against_guards', '罗绍威两次请朱全忠助诛魏博牙军', 4,
      '硃全忠之围凤翔也，绍威遣军将杨利言密以情告全忠，欲借其兵以诛之。全忠以事方急，未暇如其请，阴许之。及李公佺作乱，绍威益惧，复遣牙将臧延范趣全忠。',
      [('罗绍威', '求朱全忠援兵者'), ('杨利言', '第一次密告者'),
       ('朱温', '先阴许而未立即出兵者'), ('李公佺', '作乱者'), ('臧延范', '再催请者')],
      when='围凤翔时及李公佺作乱后之追叙；确年日另待核', year=None, place='魏博、凤翔',
      note='两次求援与906年诛牙军分开；“李公佺作乱”这里只作为时间参照，不用本句推定叛乱日期。')
event('zhu_disguises_wei_campaign', '朱全忠发兵并以击沧州为名掩护入魏', 4,
      '全忠乃发河南诸镇兵七万，遣其将李思安将之，会魏、镇兵屯深州乐城，声言击沧州，讨其纳李公佺也。',
      [('朱温', '发河南兵并布置行动者'), ('李思安', '领河南军者'),
       ('李公佺', '声言讨伐的对象')],
      when='906年正月庚午前；确日未载', place='深州乐城',
      note='七万人为主书所记发兵数；“击沧州”是对外声言，不把作战目标当唯一真实目的。')
event('ma_sixun_enters_wei_disguised', '马嗣勋借赴丧名义携兵器入魏', 4,
      '全忠遣客将马嗣勋实甲兵于橐中，选长直兵千人为担夫，帅之入魏，诈云会葬，全忠自以大军继其后，云赴行营，牙军皆不之疑。',
      [('朱温', '派马嗣勋并率后军者'), ('马嗣勋', '率兵伪装入魏者')],
      when='906年正月庚午前；确日未载', place='魏州',
      note='借丧事是伪装理由；千人为主书所记随行长直兵，不当成牙军总数。')
event('luo_disables_wei_guards_weapons', '罗绍威庚午暗断牙军弓弦甲襻', 4,
      '庚午，绍威潜遣人入库断弓弦、甲襻。',
      [('罗绍威', '派人破坏军械者')],
      when='906年正月庚午', place='魏州',
      note='军械破坏与夜间杀戮是先后动作，分别记录。')
event('luo_ma_massacre_wei_guards', '罗绍威与马嗣勋夜袭并杀魏博牙军家属', 4,
      '是夕，绍威帅其奴客数百，与嗣勋合击牙军。牙军欲战而弓甲皆不可用，遂阖营殪之，凡八千家，婴孺无遗。',
      [('罗绍威', '率奴客参袭者'), ('马嗣勋', '合兵参袭者')],
      when='《资治通鉴》906年正月庚午夜；《旧唐书》作己巳夜', place='魏州牙军营',
      note='主书作八千家且含婴孺，旧五代史作七千余人、旧唐书作八千人，计量单位和日期均有异，保留原貌。')
event('zhu_enters_wei_after_massacre', '朱全忠次晨率兵入魏城', 4,
      '诘旦，全忠引兵入城。', [('朱温', '次晨引兵入魏者')],
      when='牙军遇袭次晨；确干支随前述异日待核', place='魏州',
      note='“诘旦”承庚午夜，旧唐书记朱全忠戊午入魏，与主书叙述日序不合，待考。')

event('pang_ye_promoted_jiedushi', '唐廷辛未授庞巨昭、叶广略节度使', 5,
      '辛未，以权知宁远留后庞巨昭、岭南西道留后叶广略并为节度使。',
      [('庞巨昭', '由宁远留后授节度使者'), ('叶广略', '由岭南西道留后授节度使者')],
      when='906年正月辛未',
      note='两人由留后转节度使，不推断是否同时就任或赴镇。')
event('qian_miu_visits_muzhou', '钱镠庚辰赴睦州', 6,
      '庚辰，钱镠如睦州。', [('钱镠', '赴睦州者')],
      when='906年正月庚辰', place='睦州')
event('wang_zongruan_takes_han_congshi', '王宗阮攻归州并俘韩从实', 7,
      '西川将王宗阮攻归州，获其将韩从实。',
      [('王宗阮', '攻归州者'), ('韩从实', '被俘将领')],
      when='906年正月后条；确日未载', place='归州',
      note='王宗阮沿既有改名记录复用文武坚；“其将”承归州守方，主书未给州城最终归属，不记为已攻占。')
event('chen_zhang_withdraws_to_quzhou', '陈璋自婺州退守衢州', 8,
      '陈璋闻陶雅归歙，自婺州退保衢州。',
      [('陈璋', '退保衢州者'), ('陶雅', '已退歙州者')],
      when='陶雅退歙州后；确日未载', place='婺州、衢州',
      note='承第2段陶雅还歙；不把陶雅退兵的时间重新记为第8段。')
event('fang_yongzhen_takes_wuzhou', '方永珍等取婺州并攻衢州', 8,
      '两浙将方永珍等取婺州，进攻衢州。',
      [('方永珍', '率两浙兵取婺州、攻衢州者')],
      when='陈璋退衢州后；确日未载', place='婺州、衢州',
      note='婺州已取，衢州在此段仍为进攻中，未录为已陷。')

extra(old_wang, 'event', 'event_zztj_265_0906_li_jian_reaches_xuanzhou_wang_flees', 'description',
      '《旧五代史》卷二十三亦记王茂章弃宣州归钱镠。',
      '景仁棄宛陵，以腹心百人歸吳越王錢鏐', 2, 'corroborates',
      '“景仁”为王茂章改名后称谓；旧书给腹心百人，主书仅称率众，不合并具体人数。')
extra(old_wang, 'event', 'event_zztj_265_0906_qian_appoints_wang_jingren', 'description',
      '《旧五代史》王景仁传与主书共同指向王茂章奔钱镠后受任，但官职叙述不完全相同。',
      '鏐辟為兩府行軍司馬', 2, 'conflicts',
      '主书写镇东节度副使；旧书此处写两府行军司马，可能为不同任次，待纸本与时间核对。')
extra(old_wei, 'event', 'event_zztj_265_0906_ma_sixun_enters_wei_disguised', 'description',
      '《旧五代史》卷二亦记马嗣勋将兵器藏橐，借祭朱全忠之女入魏。',
      '因以兵仗數千事實於橐中，遣客將馬嗣勳領長直軍千人', 4, 'corroborates',
      '旧书称兵仗数千事，不把兵器数量与随行人数混同。')
extra(old_wei, 'event', 'event_zztj_265_0906_luo_ma_massacre_wei_guards', 'time_original',
      '《旧五代史》卷二记庚午夜同攻牙军，死者七千余人。',
      '庚午夜，嗣勳率其眾與羅紹威親軍數百人同攻牙軍，遲明盡殺之，死者七千餘人',
      4, 'conflicts', '主书计八千家、旧书计七千余人，计量单位不同；旧书与主书干支相同。')
extra(old_tang, 'event', 'event_zztj_265_0906_luo_ma_massacre_wei_guards', 'time_original',
      '《旧唐书》卷二十下记己巳夜杀牙内亲军八千人，较《通鉴》庚午夜早一日。',
      '己巳夜，魏博節度使羅紹威殺其衙內親軍八千人',
      4, 'conflicts', '旧书以八千人为单位，主书为八千家；干支差一日，不自行修正。')
extra(new_wei, 'event', 'event_zztj_265_0906_luo_ma_massacre_wei_guards', 'description',
      '《新五代史》卷一亦记罗绍威谋杀牙军，但未给具体杀戮人数。',
      '魏州羅紹威謀殺其牙軍', 4, 'corroborates',
      '新书后文叙外地牙军叛乱，属于主书后续段落，不提前录为第4段已发生。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 9):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='卷265天祐三年第1—8段连续处理；韩逊奏报只记所报，魏博牙军屠杀的干支和人数异文并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=906,
    primary_source_key=primary, primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(1, 9)], next_paragraph=Q[9]['id'],
    coverage='卷265天祐三年第1—8段连续处理；韩逊奏报、宣州王茂章出奔、魏博牙军屠杀、正月任命与浙西战事。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
