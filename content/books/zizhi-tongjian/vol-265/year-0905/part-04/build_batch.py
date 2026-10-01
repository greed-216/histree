"""Curate Tongjian 265, year 905, consecutive paragraphs 20–27."""
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
primary_spring = 'tongjian-265-905-spring'
old_dem = 'jiutangshu-020-905-demotions'
old_exec = 'jiutangshu-020-905-executions'
old_li = 'jiuwudaishi-018-lizhen-whitehorse'
new_white = 'xinwudaishi-035-whitehorse'
new_zhang = 'xinwudaishi-035-zhangwenwei'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p020-p027',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_spring, P.parent / 'part-03/sources/library' / primary_spring, 'b7f25c78', '司马光等'),
    (old_dem, P / 'sources/library' / old_dem, '8a4d4e60', '刘昫等'),
    (old_exec, P / 'sources/library' / old_exec, '8a4d4e60', '刘昫等'),
    (old_li, P / 'sources/library' / old_li, '8a4d4e60', '薛居正等'),
    (new_white, P / 'sources/library' / new_white, '8a4d4e60', '欧阳修等'),
    (new_zhang, P / 'sources/library' / new_zhang, '8a4d4e60', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_spring,)}
for n in range(20, 28):
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
    B['claims'].append(dict(key=f'claim_zztj_265_0905_04_{len(B["claims"])+1:04d}',
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
    ck = f'claim_zztj_265_0905_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 20: Allegations and dated demotions. Preserve the main book's destinations.
event('liu_li_urge_purge', '柳璨、李振劝朱全忠逐朝士', 20,
      Q[20]['text'].split('癸酉，')[0],
      [('柳璨','另向朱全忠进言逐人的宰相'),('李振','进言者'),('朱温','采纳进言者')],
      when='905年五月；癸酉前；确日未载',
      note='柳璨与李振的话是史书所录进言，不将指控视为被贬官员的既定罪行；原文硃按本站实体规范作朱。')
event('demote_three_ciyou', '唐廷癸酉贬独孤损、裴枢、崔远', 20,
      '癸酉，贬独孤损为棣州刺史，裴枢为登州刺史，崔远为莱州刺史。',
      [('独孤损','贬棣州刺史'),('裴枢','贬登州刺史'),('崔远','贬莱州刺史')], when='905年五月癸酉',
      note='三人的首次贬官；不与辛巳再贬混为同一道命令。')
event('demote_lu_wang_yihai', '唐廷乙亥贬陆扆、王溥', 20,
      '乙亥，贬吏部尚书陆扆为濮州司户，工部尚书王溥为淄州司户。',
      [('陆扆','贬濮州司户'),('王溥','贬淄州司户')], when='905年五月乙亥')
event('demote_zhao_wang_gengchen', '唐廷庚辰贬赵崇、王赞', 20,
      '庚辰，贬太子太保致仕赵崇为曹州司户，兵部侍郎王赞为潍州司户。',
      [('赵崇','贬曹州司户'),('王赞','贬潍州司户')], when='905年五月庚辰',
      note='《通鉴》王赞作潍州；《旧唐书》卷二十下作濮州，异文并列。')
event('demote_three_xinsi', '唐廷辛巳再贬裴枢、独孤损、崔远', 20,
      '辛巳，再贬裴枢为泷州司户，独孤损为琼州司户，崔远为白州司户。',
      [('裴枢','再贬泷州司户'),('独孤损','再贬琼州司户'),('崔远','再贬白州司户')], when='905年五月辛巳',
      note='《通鉴》作泷州，《旧唐书》作隴州；原字分别保留，不以繁简转换消解地名异说。')

# 21: A diplomatic message, without inferring an alliance.
event('zhao_kuangning_reconciles_wang_jian', '赵匡凝遣使与王建修好', 21,
      '甲申，忠义节度使赵匡凝遣使修好于王建。',
      [('赵匡凝','遣使修好者'),('王建','受遣使者')], when='905年五月甲申',
      note='只录遣使修好，不推定盟约已成或实际出兵。')

# 22–23: Edict, murder and river disposal have distinct scope and evidence.
event('edict_seven_deaths', '唐廷六月戊子敕七名贬官在所在赐自尽', 22,
      '六月，戊子朔，敕裴枢、独孤损、崔远、陆扆、王溥、赵崇、王赞等并所在赐自尽。',
      [(n,'赐死敕令所列者') for n in ('裴枢','独孤损','崔远','陆扆','王溥','赵崇','王赞')],
      when='905年六月戊子朔',
      note='这是七名具名官员的敕令；“所在赐自尽”与实际白马驿遇害分别记录。')
event('whitehorse_massacre', '朱全忠于白马驿杀朝士贬官三十余人', 23,
      '时全忠聚枢等及朝士贬官者三十余人于白马驿，一夕尽杀之，投尸于河。',
      [('朱温','聚杀朝士的掌权者'),('裴枢','遇害者之一')],
      when='905年六月戊子敕后；一夕；确日未载', place='白马驿',
      note='主书称三十余人，只有“枢等”在本句具名；七人敕令与三十余人被杀不可互换。')
event('li_zhen_urges_river_disposal', '李振劝朱全忠投朝士于黄河', 23,
      '言于全忠曰：“此辈常自谓清流，宜投之黄河，使为浊流！”全忠笑而从之。',
      [('李振','进言者'),('朱温','采纳进言者')],
      when='白马驿杀朝士之际；确日未载', place='黄河',
      note='李振“屡举进士，竟不中第”是主书解释其动机；仅记录史书所载进言和采纳。')

# 24–25: Retrospective character reports are not dated to this month.
event('li_zhen_court_intimidation', '李振自汴至洛时屡有朝官被窜逐', 24,
      '振每自汴至洛，朝廷必有窜逐者，时人谓之鸱枭。见朝士皆颐指气使，旁若无人。',
      [('李振','被时人称鸱枭者')], when='追叙屡次往来汴洛；确年未载', year=None,
      note='“每”表惯常行为，鸱枭是时人称谓；不把每一次窜逐逐人虚构。')
event('zhu_willow_cart_hub_killings', '朱全忠因柳木车毂应对杀游客', 25,
      '左右数十人捽言“宜为车毂”者，悉扑杀之。',
      [('朱温','下令扑杀者')], when='追叙旧事；确年未载', year=None,
      note='原文未具名被害游客及确年；不将“左右数十人”误作被害人数。')

# 26–27: Pei Zhi's later death and Zhang Wenwei's plea lack exact days.
event('pei_zhi_demoted', '唐廷己丑贬裴贽为青州司户', 26,
      '己丑，司空致仕裴贽贬青州司户',
      [('裴贽','贬青州司户者')], when='905年六月己丑', place='青州')
event('pei_zhi_ordered_dead', '裴贽被赐死', 26,
      '寻赐死。', [('裴贽','被赐死者')],
      when='己丑贬官后不久；确日未载',
      note='“寻”只表随后，不与贬官同日。')
event('zhang_wenwei_prevents_more_killings', '张文蔚劝解柳璨，停止再牵连朝士', 27,
      '柳璨馀怒所注，犹不啻十数，张文蔚力解之，乃止。',
      [('柳璨','拟继续牵连者'),('张文蔚','力解者')],
      when='白马驿事后；确日未载',
      note='“十数”是柳璨余怒所及概数，未具名也不作实际死亡人数。')

# Parallel books remain separately cited. Their inconsistencies are not normalized away.
extra(old_dem, 'event', 'event_zztj_265_0905_demote_zhao_wang_gengchen', 'description',
      '《旧唐书》卷二十下王赞贬濮州司户；《通鉴》作潍州。',
      '王贊可濮州司戶', 20, 'conflicts', '濮州与潍州是地名异说，不是繁简字形差异。')
extra(old_dem, 'event', 'event_zztj_265_0905_demote_three_xinsi', 'description',
      '《旧唐书》卷二十下裴枢再贬隴州司户；《通鉴》作泷州。',
      '裴樞可隴州司戶', 20, 'conflicts', '隴州与泷州是地名异说，不自动合并。')
extra(old_exec, 'event', 'event_zztj_265_0905_edict_seven_deaths', 'description',
      '《旧唐书》卷二十下亦载六月戊子敕七官赐自尽。',
      '委御史台差人所在州縣各賜自盡', 22, 'corroborates',
      '旧书敕文此前列七名，摘录只证赐死命令；同段另叙白马驿。')
extra(old_exec, 'event', 'event_zztj_265_0905_whitehorse_massacre', 'description',
      '《旧唐书》卷二十下记七人于滑州白马驿遇害并投尸于河。',
      '時樞等七人已至滑州，皆並命于白馬驛，全忠令投屍於河', 23, 'adds',
      '旧书所记七人范围较主书“三十余人”窄；不把两种计数强合。')
extra(new_white, 'event', 'event_zztj_265_0905_whitehorse_massacre', 'description',
      '《新五代史》卷三十五记七名朝官同日赐死白马驿，并总述数百人受贬死。',
      '皆以無罪貶，同日賜死于白馬驛', 23, 'adds',
      '“數百人”是该书对更广范围的总述，不当成本次一夕被杀人数；新书所系年与主书有异。')
extra(old_li, 'event', 'event_zztj_265_0905_li_zhen_urges_river_disposal', 'description',
      '《旧五代史》卷十八亦记李振清流、浊流之言。',
      '此輩自謂清流，宜投於黃河，永為濁流', 23, 'corroborates',
      '同书还记屡举不第；两书言辞略异，保留原句。')
extra(old_li, 'event', 'event_zztj_265_0905_li_zhen_court_intimidation', 'description',
      '《旧五代史》卷十八记李振自汴入洛使朝士被贬，时称鸱鸮。',
      '振每自汴入洛，朝中必有貶竄，故唐朝人士目為「鴟鴞」', 24, 'corroborates',
      '主书简体作鸱枭，旧书原文作鴟鴞；是称谓字形异说，不另建人物。')
extra(old_exec, 'event', 'event_zztj_265_0905_pei_zhi_demoted', 'description',
      '《旧唐书》卷二十下己丑敕裴贽贬青州司户。',
      '可責授青州司戶', 26, 'corroborates',
      '旧书此摘录只证贬官，不证“寻赐死”具体日。')
extra(new_zhang, 'event', 'event_zztj_265_0905_zhang_wenwei_prevents_more_killings', 'description',
      '《新五代史》卷三十五记张文蔚力讲解，朝士多获全活。',
      '文蔚力講解之，朝士多賴以全活', 27, 'adds',
      '新书对张文蔚劝解效果记述较主书具体，不据此推断确数。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(20, 28):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='卷265天祐二年第20—27段连续处理；繁简仅用于实体匹配，原文保留原字；贬官地点与遇害人数异说并列。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=905,
    primary_source_key=primary_spring, primary_source_keys=[primary_spring],
    paragraphs=[Q[n]['id'] for n in range(20, 28)], next_paragraph=Q[28]['id'],
    coverage='卷265天祐二年第20—27段连续处理；五月贬官、六月赐死、白马驿、裴贽与张文蔚。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
