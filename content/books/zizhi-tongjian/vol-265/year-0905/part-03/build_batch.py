"""Curate Tongjian 265, year 905, consecutive paragraphs 12–19."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 61))
primary_early = 'tongjian-265-905-early'
primary_spring = 'tongjian-265-905-spring'
old_court = 'jiutangshu-020-905-march'
new_court = 'xintangshu-010-905-court'
old_gai = 'jiuwudaishi-055-905-gai-yu'
old_comet_april = 'jiutangshu-020-comet-march'
old_comet_may = 'jiutangshu-020-comet-may'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p012-p019',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_early, P.parent / 'part-01/sources/library' / primary_early, 'aaf3df65', '司马光等'),
    (primary_spring, P / 'sources/library' / primary_spring, 'b7f25c78', '司马光等'),
    (old_court, P.parent / 'part-02/sources/library' / old_court, '91cdc112', '刘昫等'),
    (new_court, P / 'sources/library' / new_court, 'b7f25c78', '欧阳修等'),
    (old_gai, P / 'sources/library' / old_gai, 'a4b16b69', '薛居正等'),
    (old_comet_april, P / 'sources/library' / old_comet_april, 'b7f25c78', '刘昫等'),
    (old_comet_may, P / 'sources/library' / old_comet_may, 'b7f25c78', '刘昫等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_early, primary_spring)}
for n in range(12, 20):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '收':'杨收', '涉':'杨涉', '凝式':'杨凝式', '镖':'钱镖', '璨':'柳璨', '枢':'裴枢', '远':'崔远', '损':'独孤损'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐二年（905）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷265天祐二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=905):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0905_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '905年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '905年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0905_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0905_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 12: Four appointments/removals, two dates; do not conflate the ministers.
event('dugu_jinghai', '唐廷以独孤损充静海节度使', 12,
      '戊寅，以门下侍郎、同平章事独孤损同平章事，充静海节度使',
      [('独孤损','受任者')], when='905年三月戊寅', place='静海',
      note='《新唐书》卷十记同日独孤损罢相而出镇；“同平章事”是所带衔，不等于仍在朝执政。')
event('zhang_wenwei_chancellor', '唐廷以张文蔚同平章事', 12,
      '以礼部侍郎河间张文蔚同平章事。',
      [('张文蔚','受任宰相者')], when='905年三月戊寅',
      note='日期承同段前置戊寅；《新唐书》卷十同系戊寅。')
event('pei_shu_left_pushe', '唐廷以裴枢为左仆射并罢政事', 12,
      '甲申，以门下侍郎、同平章事裴枢为左仆射',
      [('裴枢','改任左仆射、罢政事者')], when='905年三月甲申',
      note='“并罢政事”承裴枢和崔远；《新唐书》卷十将裴枢罢相系于甲子，分列异说。')
event('cui_yuan_right_pushe', '唐廷以崔远为右仆射并罢政事', 12,
      '崔远为右仆射，并罢政事。',
      [('崔远','改任右仆射、罢政事者')], when='905年三月甲申',
      note='甲申承前半句；《新唐书》卷十同记甲申崔远罢相。')

# 13: Earlier resentment explains, but does not share, the precise day of removal.
event('zhang_tingfan_taichang_dispute', '张廷范被奏为太常卿，裴枢阻止', 13,
      '和王傅张廷范，本优人，有宠于全忠，奏以为太常卿。枢曰：“廷范勋臣，幸有方镇，何籍乐卿！恐非元帅之旨。”持之不下。',
      [('张廷范','被奏任太常卿者'),('裴枢','持奏不下者')],
      when='裴枢罢政事前；确日未载', year=None,
      note='本段“初”起追叙；“有宠于全忠”是原文，不据此虚构奏荐人或确年。')
event('liu_can_slanders_ministers', '柳璨向朱全忠谮裴枢、崔远、独孤损', 13,
      '璨因此并远、损谮于全忠，故三人皆罢。',
      [('柳璨','进谮者'),('朱温','受谮者'),('裴枢','被谮者'),('崔远','被谮者'),('独孤损','被谮者')],
      when='三人罢政事前；确日未载', year=None,
      note='主书把谮言与三人罢相相连；不把柳璨的心态评价当独立事实。')

# 14: Appointment, family response and explicit kinship; avoid dating a retrospective exam.
event('yang_she_chancellor', '唐廷以杨涉同平章事', 14,
      '以吏部侍郎杨涉同平章事。',
      [('杨涉','受任宰相者')], when='905年三月甲申后条；确日未载',
      note='本段未另载确日；《旧唐书》卷二十下列于三月甲子制文，纪日不强合。')
event('yang_she_fears_chancellorship', '杨涉闻拜相与家人相泣并告诫子杨凝式', 14,
      '闻当为相，与家人相泣，谓其子凝式曰：“此吾家之不幸也，必为汝累。”',
      [('杨涉','言说者'),('杨凝式','受告诫之子')],
      when='杨涉闻拜相时；确日未载',
      note='只记杨涉当时所言，不据其忧虑断定后来实际牵累。')

yang_shou = person('杨收', 14, '杨涉祖父', '涉，收之孙也')
yang_she = people['杨涉']
rel_key = 'relationship_zztj_265_0905_yang_shou_grandfather_yang_she'
B['person_relationships'].append(dict(key=rel_key, person_a_key=yang_shou,
    person_b_key=yang_she, relation_type='祖父', description='杨收是杨涉的祖父。', status='draft'))
claim('person_relationship', rel_key, 'description', '杨收是杨涉的祖父。', 14,
      '涉，收之孙也', '“孙”明示祖孙；杨涉与杨凝式父子关系旧批已登记。')

# 15–16: One honorary title, a death/last counsel, and the recorded comet.
event('liu_yin_tong_pingzhang', '唐廷加清海节度使刘隐同平章事', 15,
      '为清海节度使刘隐同平章事。',
      [('刘隐','加同平章事者')], when='905年三月后条；确日未载', place='清海',
      note='同平章事是授衔，不能据此认定刘隐到朝廷执政。')
event('gai_yu_dies', '河东都押牙盖寓去世', 16,
      '壬辰，河东都押牙盖寓卒',
      [('盖寓','去世者')], when='905年三月壬辰', place='河东',
      note='《旧五代史》卷五十五记天祐二年三月病笃而卒；主书确日不换算公历日。')
event('gai_yu_last_letter', '盖寓遗书劝李克用省营缮、薄赋敛、求贤俊', 16,
      '遗书劝李克用省营缮，薄赋敛，求贤俊。',
      [('盖寓','遗书劝谏者'),('李克用','受遗书劝谏者')],
      when='盖寓去世前后；确日未载', place='河东',
      note='劝谏内容逐字拆读；不把李克用后来是否采纳写为既成事实。')
event('comet_april_gengzi', '唐天祐二年四月庚子史载西北彗星', 16,
      '夏，四月，庚子，有彗星出西北。',
      when='905年四月庚子',
      note='仅录史书观测记载；《旧唐书》另记四月甲辰夜北河彗星，日期和描述不同，未判为同一次观测。')

# 17–19: Wuzhou campaign, planned suburban rite, and a later comet report.
event('tao_ya_attacks_wuzhou', '陶雅会衢、睦兵攻婺州', 17,
      '淮南将陶雅会衢、睦兵攻婺州',
      [('陶雅','率军会合并进攻者')], when='905年四月后条；确日未载', place='婺州',
      note='衢、睦兵是来源地，不据此虚构具名指挥者或已攻克。')
event('qian_biao_aids_wuzhou', '钱镠遣弟钱镖率军救婺州', 17,
      '钱镠遣其弟镖将兵救之。',
      [('钱镠','遣军者'),('钱镖','率军救援者')],
      when='陶雅进攻婺州后；确日未载', place='婺州',
      note='“其弟”承钱镠，所救“之”承婺州；不写救援结果。')

qian_biao = people['钱镖']
qian_liu = people['钱镠']
rel_biao = 'relationship_zztj_265_0905_qian_biao_younger_brother_qian_liu'
B['person_relationships'].append(dict(key=rel_biao, person_a_key=qian_biao,
    person_b_key=qian_liu, relation_type='弟弟', description='钱镖是钱镠的弟弟。', status='draft'))
claim('person_relationship', rel_biao, 'description', '钱镖是钱镠的弟弟。', 17,
      '钱镠遣其弟镖', '弟弟方向为钱镖→钱镠，繁简统一名称，原文保持字形。')

event('court_plans_southern_rite', '唐廷据礼院奏拟十月甲午祀南郊', 18,
      '五月，礼院奏，皇帝登位应祀南郊，敕用十月甲午行之。',
      when='905年五月奏定；拟十月甲午举行', place='南郊',
      note='这是五月作出的未来祭礼安排，不能登记为十月已经举行。')
event('comet_may_yichou', '唐天祐二年五月乙丑史载彗星长竟天', 19,
      '乙丑，彗星长竟天。', when='905年五月乙丑',
      note='仅录本书天象叙述；《旧唐书》另记五月乙酉夜彗星长竟天，不强并为同日观测。')

# Independently transcribed books keep their own dates and narrative scope.
extra(new_court, 'event', 'event_zztj_265_0905_dugu_jinghai', 'time_original',
      '《新唐书》卷十将独孤损罢相出镇系于三月戊寅。',
      '戊寅，獨孤損罷。禮部侍郎張文蔚同中書門下平章事。', 12, 'corroborates',
      '新书本纪未在此摘录明列静海职名，只印证出朝与张文蔚任相日期。')
extra(new_court, 'event', 'event_zztj_265_0905_pei_shu_left_pushe', 'time_original',
      '《新唐书》卷十将裴枢罢相系于三月甲子，与《通鉴》甲申不同。',
      '三月甲子，裴樞罷。', 12, 'conflicts',
      '只按本纪确定罢相日异说，左仆射职名仍据主书及旧唐书。')
extra(new_court, 'event', 'event_zztj_265_0905_cui_yuan_right_pushe', 'time_original',
      '《新唐书》卷十同将崔远罢相系于三月甲申。',
      '甲申，崔遠罷。', 12, 'corroborates',
      '本句仅证罢相日，不单独证右仆射职名。')
extra(old_court, 'event', 'event_zztj_265_0905_zhang_wenwei_chancellor', 'description',
      '《旧唐书》卷二十下记张文蔚为中书侍郎、同平章事。',
      '張文蔚為中書侍郎、同平章事', 12, 'corroborates',
      '旧书制文所列官职较主书详细，所在长段系于甲子，日分与主书戊寅不强合。')
extra(old_court, 'event', 'event_zztj_265_0905_yang_she_chancellor', 'description',
      '《旧唐书》卷二十下亦记杨涉同平章事。',
      '楊涉為中書侍郎、同平章事', 14, 'corroborates',
      '旧书长段有甲子起日，主书本段无确日；另留书际日分。')
extra(old_gai, 'event', 'event_zztj_265_0905_gai_yu_dies', 'time_original',
      '《旧五代史》卷五十五记天祐二年三月盖寓病笃、其后去世。',
      '天祐二年三月，寓病篤', 16, 'corroborates',
      '同段后文记“及其卒也”，此摘录仅给三月病笃，不据此证明主书壬辰确日。')
extra(old_comet_april, 'event', 'event_zztj_265_0905_comet_april_gengzi', 'description',
      '《旧唐书》卷二十下另记四月甲辰夜彗星起北河、贯文昌。',
      '甲辰夜，彗起北河，貫文昌，其長三丈，在西北方。', 16, 'adds',
      '与主书四月庚子记载日期不同；可能为另次观测，不以它改写主书日分。')
extra(old_comet_may, 'event', 'event_zztj_265_0905_comet_may_yichou', 'description',
      '《旧唐书》卷二十下另记五月乙酉夜彗星长竟天。',
      '乙酉夜，西北彗星長六七十丈，自軒轅大角及天市西垣，光輝猛怒，其長竟天。', 19, 'adds',
      '主书作五月乙丑；是否同一彗星的不同观测未核。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(12, 20):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='卷265天祐二年第12—19段连续处理；朝廷任免分日、追叙不倒填、礼院仅拟郊祀、彗星异日记录并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=905,
    primary_source_key=primary_early, primary_source_keys=[primary_early, primary_spring],
    paragraphs=[Q[n]['id'] for n in range(12, 20)], next_paragraph=Q[20]['id'],
    coverage='卷265天祐二年第12—19段连续处理；朝廷任免、人物追叙、盖寓卒、婺州战事与彗星记录。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
