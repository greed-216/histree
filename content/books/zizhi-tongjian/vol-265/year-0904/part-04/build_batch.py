"""Curate Tongjian 265, year 904, consecutive paragraphs 17–21."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 22))
primary = 'tongjian-265-904-late'
new_chen = 'xintangshu-010-chenzhang'
new_ma = 'xinwudaishi-066-macong'
new_liu = 'xinwudaishi-065-liuyin'
new_tang_liu = 'xintangshu-190-liuyin'
old_campaign = 'jiuwudaishi-002-campaign'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0904-p017-p021',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-02/sources/library' / primary, '40fd2522', '司马光等'),
    (old_campaign, P.parent / 'part-03/sources/library' / old_campaign, '8732e6a2', '薛居正等'),
    (new_chen, P / 'sources/library' / new_chen, '0f5ea5c5', '欧阳修等'),
    (new_ma, P / 'sources/library' / new_ma, '0f5ea5c5', '欧阳修等'),
    (new_liu, P / 'sources/library' / new_liu, '0f5ea5c5', '欧阳修等'),
    (new_tang_liu, P / 'sources/library' / new_tang_liu, '0f5ea5c5', '欧阳修等'),
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
for n in range(17, 22):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '殷':'马殷', '賨':'马賨', '行密':'杨行密', '璋':'陈璋', '隐':'刘隐'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0904_04_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐元年（904）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷265天祐元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=904):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0904_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '904年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '904年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0904_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0904_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 17: Keep the corrupt clause out of claims. The surrounding clauses remain legible.
event('guangzhou_switches_zhu', '光州叛杨行密而降朱全忠', 17,
      '光州叛杨行密，降硃全忠', [('杨行密','被叛离者'),('朱温','接受归降者')],
      when='904年十一月前条；确日未载', place='光州')
event('yang_besieges_guangzhou', '杨行密遣军围光州，光州与鄂州向朱全忠告急', 17,
      '行密遣兵围之，与鄂州皆告急于全忠',
      [('杨行密','遣军围城者'),('朱温','受求援者')],
      when='904年十一月前条；确日未载', place='光州、鄂州',
      note='“皆告急”指光州与鄂州；围城的“之”承光州。')
event('zhu_crosses_huai_huoqiu', '朱全忠率五万兵自颍州渡淮驻霍丘并分兵救鄂州', 17,
      '十一月，戊辰，全忠自将兵五万自颍州济淮，军于霍丘，分兵救鄂州。',
      [('朱温','率军渡淮者')], when='904年十一月戊辰', place='颍州、霍丘、鄂州',
      note='《旧五代史》记戊寅南征渡淮，干支异说并列；原文没有写鄂州已解围。')
event('zhu_raids_huainan', '朱全忠分遣诸将掠淮南', 17,
      '全忠分命诸将大掠淮南以困之。', [('朱温','下令者')],
      when='904年十一月戊辰后；确日未载', place='淮南',
      note='此前一句含乱码，不以乱码补足淮南兵行动；此处仅录可辨字句。')

# 18: New Tang History places Chen's defection under August; preserve the conflict.
event('qian_sends_ye_kill_chen', '钱镠密遣叶让刺杀衢州刺史陈璋而事泄', 18,
      '钱镠潜遣衢州罗城使叶让杀刺史陈璋，事泄。',
      [('钱镠','密遣刺杀者'),('叶让','奉命行刺者'),('陈璋','被刺杀目标')],
      when='904年十二月前条；确日未载', place='衢州',
      note='仅记刺杀图谋败露；陈璋并未因此句被杀。')
event('chen_executes_ye', '陈璋斩叶让', 18,
      '十二月，璋斩让而叛', [('陈璋','斩杀者'),('叶让','被斩者')],
      when='904年十二月；确日未载', place='衢州')
event('chen_defects_yang', '陈璋叛钱镠而降杨行密', 18,
      '璋斩让而叛，降于杨行密。',
      [('陈璋','归降者'),('杨行密','接受归降者'),('钱镠','被叛离者')],
      when='904年十二月；确日未载', place='衢州',
      note='《新唐书》卷十将陈璋叛附系于八月，月份异说并列。')

# 19–20: Biography reaches back before 904; only “是岁” fixes Ma Cong's return.
event('ma_cong_serves_sun_ru', '马賨曾事孙儒任百胜指挥使', 19,
      '初，马殷弟賨，性沉重，事孙儒，为百胜指挥使。',
      [('马賨','百胜指挥使'),('孙儒','旧主')],
      when='追叙孙儒在世时；确年未载', year=None,
      note='“初”为追叙，不系于904年。')
event('ma_cong_serves_yang', '孙儒死后马賨事杨行密并任黑云指挥使', 19,
      '儒死，事杨行密，屡有功，迁黑云指挥使。',
      [('马賨','黑云指挥使'),('杨行密','受其效力者')],
      when='孙儒死后、904年前；确年未载', year=None,
      note='只保留原文先后次序，不把履历都系于904年。')
event('yang_returns_ma_cong', '杨行密得知马賨为马殷弟后遣其归长沙', 19,
      '是岁，賨归长沙，行密亲饯之郊。',
      [('马賨','返长沙者'),('杨行密','郊外饯行者')],
      when='904年；确月日未载', place='长沙',
      note='“是岁”只明确归长沙之年；此前问答时间不另换算。')
event('ma_yin_appoints_cong', '马殷表弟马賨为节度副使', 20,
      '賨至长沙，殷表賨为节度副使。',
      [('马殷','表荐者'),('马賨','受荐者')],
      when='马賨归长沙后；确年未载', place='长沙', year=None,
      note='紧接“是岁”叙述，但本句没有独立纪年，保留相对时间。')
event('ma_cong_proposes_yang_trade', '马賨建议马殷与杨行密结好通商，马殷拒绝', 20,
      '它日，殷议入贡天子，賨曰：“杨王地广兵强，与吾邻接，不若与之结好，大可以为缓急之授，小可通商旅之利。”殷作色曰：“杨王不事天子，一旦朝廷致讨，罪将及吾。汝置此论，勿为吾祸！”',
      [('马賨','提议者'),('马殷','拒绝者')],
      when='马賨归长沙后某日；确年未载', place='长沙', year=None,
      note='“它日”不能换算为904年确日；杨王为谈话所论人物，未参与此事。')

# 21: Retrospective Guangzhou succession, with divergent chronology.
event('xu_recommends_liu', '徐彦若遗表荐刘隐权知清海留后', 21,
      '初，清海节度使徐彦若遗表荐副使刘隐权留后',
      [('徐彦若','遗表荐举者'),('刘隐','被荐者')],
      when='徐彦若去世前；确年未载', place='清海', year=None,
      note='“初”表示追叙；《新唐书》作天复初徐彦若死，不能系于904年。')
event('court_appoints_cui_qinghai', '唐廷任崔远为清海节度使', 21,
      '朝廷以兵部尚书崔远为清海节度使。',
      [('崔远','受命者')], when='徐彦若遗表后；确年未载', place='清海', year=None,
      note='主书不载此任命确年，不能仅据段落所在年定为904年。')
event('cui_returns_jiangling', '崔远到江陵后未赴岭南，唐廷召还', 21,
      '远至江陵，闻岭南多盗，且畏隐不受代，不敢前，朝廷召远还。',
      [('崔远','停于江陵并被召还者'),('刘隐','崔远所畏可能不受代者')],
      when='受命后；确年未载', place='江陵', year=None,
      note='畏刘隐不受代是原文所述崔远顾虑，不能据此断定刘隐实际拒命。')
event('liu_petitions_zhu_qinghai', '刘隐结朱全忠请奏清海节度使', 21,
      '隐遣使以重赂结硃全忠，乃奏以隐为清海节度使。',
      [('刘隐','遣使结交并获奏荐者'),('朱温','受重赂并上奏者')],
      when='崔远被召还后；确年未载', place='清海', year=None,
      note='《新五代史》卷六十五作天祐二年拜刘隐节度使；本句先后与正式任命时间分开。')

# A→B means A is B's relation; keep Ma Cong/Ma Yin as stable subjects.
ma_cong, ma_yin = people['马賨'], people['马殷']
rel_key = 'relationship_zztj_265_0904_ma_cong_younger_brother_ma_yin'
B['person_relationships'].append(dict(key=rel_key, person_a_key=ma_cong,
    person_b_key=ma_yin, relation_type='弟弟', description='马賨是马殷的弟弟。', status='draft'))
claim('person_relationship', rel_key, 'description', '马賨是马殷的弟弟。', 19,
      '马殷弟賨', '“弟”明示长幼；主键以马賨指向马殷。')

extra(old_campaign, 'event', 'event_zztj_265_0904_zhu_crosses_huai_huoqiu', 'time_original',
      '《旧五代史》卷二记朱全忠戊寅南征渡淮、次霍丘，与《通鉴》戊辰不同。',
      '戊寅，帝南征渡淮，次於霍丘', 17, 'conflicts',
      '干支异说；同书接记淮人弃光州，旁证乱码处可能有关解围，但不代替主书损坏引文。')
extra(new_chen, 'event', 'event_zztj_265_0904_chen_defects_yang', 'time_original',
      '《新唐书》卷十将陈璋叛附杨行密系于八月，与《通鉴》十二月不同。',
      '衢州刺史陳璋、睦州刺史陳詢叛附于楊行密。', 18, 'conflicts',
      '本段在天祐元年八月丙午条下；书中未详叶让事件。')
extra(new_ma, 'person_relationship', rel_key, 'description',
      '《新五代史》卷六十六亦称马賨为马殷弟。', '殷弟賨', 19, 'corroborates',
      '繁体“馬”与主书简体“马”只规范主体名称，摘录保持底本字形。')
extra(new_ma, 'event', 'event_zztj_265_0904_yang_returns_ma_cong', 'description',
      '《新五代史》记杨行密厚礼遣马賨归。', '乃厚禮遣賨歸。', 19, 'corroborates',
      '新书亦载黑云都与兄弟身份；未明载归年，不独证904年。')
extra(new_ma, 'event', 'event_zztj_265_0904_ma_yin_appoints_cong', 'description',
      '《新五代史》记马殷表马賨节度副使。', '殷大喜，表賨節度副使。', 20, 'corroborates',
      '仅印证表荐，原文未给确年。')
extra(new_tang_liu, 'event', 'event_zztj_265_0904_xu_recommends_liu', 'time_original',
      '《新唐书》卷一百九十将徐彦若死与刘隐自称留后系于天复初。',
      '天復初，節度徐彥若死，隱自稱留後。', 21, 'adds',
      '该书说“自称留后”，与《通鉴》遗表推荐并存，不推成完全一致。')
extra(new_liu, 'event', 'event_zztj_265_0904_liu_petitions_zhu_qinghai', 'time_original',
      '《新五代史》卷六十五记天祐二年拜刘隐为节度使。',
      '天祐二年，拜隱節度使。', 21, 'adds',
      '此处正式拜任为905年；主书叙述的结交奏荐先后不等于当年拜任。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17, 22):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='第17—21段连续校核；第17段底本乱码未用于引文；追叙不系本年，繁简统一实体而引文保留原字。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=904,
    primary_source_key=primary, primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(17, 22)], next_paragraph=None,
    coverage='卷265天祐元年第17—21段连续处理；第17段损坏字串未录为事实，其他可辨内容与独立书证并列。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
