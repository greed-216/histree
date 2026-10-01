"""Curate Tongjian 265, year 905, consecutive paragraphs 1–6."""
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
primary = 'tongjian-265-905-early'
old_campaign = 'jiuwudaishi-002-905-campaign'
new_an = 'xinwudaishi-061-anrenyi'
old_li = 'jiuwudaishi-018-lizhen'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p001-p006',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P / 'sources/library' / primary, 'aaf3df65', '司马光等'),
    (old_campaign, P / 'sources/library' / old_campaign, '73b6d918', '薛居正等'),
    (new_an, P / 'sources/library' / new_an, 'aaf3df65', '欧阳修等'),
    (old_li, P / 'sources/library' / old_li, '00ec13ec', '薛居正等'),
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
for n in range(1, 7):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '茂章':'王茂章', '仁义':'安仁义', '镒':'钱镒', '振':'李振', '师范':'王师范'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_01_{len(B["claims"])+1:04d}',
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
                   death_year=None, description=f'《资治通鉴》卷265天祐元年条所见人物：{canonical}。',
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
    ck = f'claim_zztj_265_0905_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1: The campaign order is not itself the fall of Shouzhou.
event('zhu_orders_shouzhou', '朱全忠遣诸将进兵逼寿州', 1,
      '春，正月，硃全忠遣诸将进兵逼寿州。',
      [('朱温','遣军者')], when='905年正月；确日未载', place='寿州',
      note='只记进兵逼城，不写攻克。')

# 2: The long siege and the final capture are separate moments.
event('wang_sieges_runzhou', '王茂章围攻安仁义所守润州逾年未克', 2,
      '润州团练安仁义勇决得士心，故淮南将王茂章攻之，逾年不克。',
      [('安仁义','守城者'),('王茂章','围攻者')],
      when='905年前已开始，逾年；起日未载', place='润州', year=None,
      note='“逾年不克”表示长期围攻，此前起年未由本句确定。')
event('yang_offers_an_surrender', '杨行密许安仁义自归任行军副使而安仁义不从', 2,
      '杨行密使谓之曰：“汝之功，吾不忘也，能束身自归，当以汝为行军副使，但不掌兵耳。”仁义不从。',
      [('杨行密','遣使许官者'),('安仁义','拒绝归降者')],
      when='润州围城期间；确年未载', place='润州', year=None,
      note='条件是“不掌兵”，未形成任命。')
event('wang_tunnels_runzhou', '王茂章掘地道攻克润州', 2,
      '茂章为地道入城，遂克之。', [('王茂章','掘地道入城者')],
      when='905年正月条；确日未载', place='润州',
      note='“克之”承润州；原文未给具体攻城日。')
event('an_surrenders_to_li', '安仁义将攻克之功归李德诚并随其下楼', 2,
      '惟李德诚不然，至是仁义召德诚登楼，谓曰：“汝有礼，吾今以为汝功。”且以爱妾赠之。乃掷弓于地，德诚掖之而下',
      [('安仁义','掷弓归降者'),('李德诚','扶其下楼者')],
      when='润州失守时；确日未载', place='润州',
      note='不把赠妾描写为李德诚主动索取。')
event('an_and_son_executed', '安仁义及其子在广陵市被斩', 2,
      '并其子斩于广陵市。', [('安仁义','被斩者')],
      when='润州失守后；确日未载', place='广陵市',
      note='子姓名未载，不擅造人物或确日。')

# 3: Army panic, defense, battle and captures follow the text in order.
event('liangzhe_besieges_chen_xun', '两浙兵围陈询于睦州', 3,
      '两浙兵围陈询于睦州', [('陈询','被围者')],
      when='905年正月条；确日未载', place='睦州',
      note='两浙兵将领本小句未明，不直接指定钱镠本人在围城现场。')
event('yang_sends_tao_ya', '杨行密遣陶雅率兵救陈询', 3,
      '杨行密遣西南招讨使陶雅将兵救之。',
      [('杨行密','遣军者'),('陶雅','领救兵者'),('陈询','被救援者')],
      when='905年正月条；确日未载', place='睦州',
      note='“之”承陈询，救援是否成功须看后文。')
event('tao_camp_panic', '陶雅军夜惊外逃后复归', 3,
      '军中夜惊，士卒多逾垒亡去，左右及裨将韩球奔告之，雅安卧不应，须臾自定，亡者皆还。',
      [('陶雅','军队主将'),('韩球','报夜惊者')],
      when='陶雅救睦州途中某夜；确日未载',
      note='“须臾自定，亡者皆还”仅说明军中骚动平息。')
event('tao_defeats_qian_force', '陶雅败钱镠所遣钱镒等并俘钱镒、王球', 3,
      '钱镠遣其从弟镒及指挥使顾全武、王球御之，为雅所败，虏镒及球以归。',
      [('钱镠','遣军者'),('钱镒','出战并被俘者'),('顾全武','出战者'),('王球','出战并被俘者'),('陶雅','击败并俘人者')],
      when='905年正月条；确日未载',
      note='“虏镒及球”明指钱镒、王球，不能扩张为顾全武也被俘；从弟关系已在旧批次登记。')

# 4–6: Li Zhen's assignment, the Shouzhou withdrawal, and Wang Shifan's transfer.
event('li_zhen_replaces_wang', '朱全忠命李振代王师范知青州事', 4,
      '庚午，硃全忠命李振知青州事，代王师范。',
      [('朱温','任命者'),('李振','受命知青州事者'),('王师范','被替代者')],
      when='905年正月庚午', place='青州',
      note='本句为命令，李振到青州在第6段。')
event('zhu_besieges_shouzhou', '朱全忠围寿州，守军闭壁不出', 5,
      '全忠围寿州，州人闭壁不出。', [('朱温','围城者')],
      when='905年正月；确日未载', place='寿州',
      note='本段只记守军拒出，不记城陷。')
event('zhu_withdraws_huoqiu', '朱全忠自霍丘撤军', 5,
      '全忠乃自霍丘引归', [('朱温','撤军者')],
      when='905年正月后；确日未载', place='霍丘',
      note='《旧五代史》系丁亥班师，作为补证保留其确日。')
event('zhu_returns_daliang', '朱全忠二月辛卯回到大梁', 5,
      '二月，辛卯，至大梁。', [('朱温','抵达者')],
      when='905年二月辛卯', place='大梁',
      note='“至大梁”主语承朱全忠；不将撤军日强定为辛卯。')
event('wang_shifan_relocates', '王师范举族西迁至大梁，朱全忠以宾礼待之', 6,
      '王师范举族西迁，至濮阳，素服乘驴而进。至大梁，全忠客之。',
      [('王师范','举族西迁者'),('朱温','以宾礼待之者')],
      when='李振到青州后；确日未载', place='青州、濮阳、大梁',
      note='“素服乘驴”是到濮阳后的姿态，未记家族每人交通方式。')
event('li_zhen_qingzhou_liuhou', '朱全忠表李振为青州留后', 6,
      '表李振为青州留后。', [('朱温','表荐者'),('李振','获表荐者')],
      when='王师范迁大梁后；确日未载', place='青州',
      note='仅据此句登记表荐，不等同已见朝廷制书。')

extra(old_campaign, 'event', 'event_zztj_265_0905_zhu_besieges_shouzhou', 'time_original',
      '《旧五代史》卷二记正月庚申进攻寿州。',
      '二年正月庚申，進攻壽州，壽人堅壁不出。', 5, 'corroborates',
      '主书未记进攻确日；旧书“二年”承天祐二年。')
extra(old_campaign, 'event', 'event_zztj_265_0905_zhu_withdraws_huoqiu', 'time_original',
      '《旧五代史》卷二记丁亥自霍丘班师。',
      '丁亥，帝自霍丘班師。', 5, 'adds',
      '另书确日；主书仅给二月辛卯回大梁。')
extra(old_campaign, 'event', 'event_zztj_265_0905_zhu_returns_daliang', 'time_original',
      '《旧五代史》卷二亦记二月辛卯朱全忠南征归来。',
      '二月辛卯，帝至自南征。', 5, 'corroborates',
      '“帝”是旧五代史以梁太祖身份追称，不误作唐昭宣帝。')
extra(new_an, 'event', 'event_zztj_265_0905_wang_tunnels_runzhou', 'description',
      '《新五代史》卷六十一亦记王茂章穴地道入润州。',
      '茂章乘其怠，穴地道而入，執仁義，斬于廣陵。', 2, 'corroborates',
      '新书径记执斩，主书多记李德诚扶其下楼；过程差异并列。')
extra(new_an, 'event', 'event_zztj_265_0905_an_and_son_executed', 'description',
      '《新五代史》卷六十一记安仁义被执斩于广陵。',
      '執仁義，斬于廣陵。', 2, 'corroborates',
      '新书不记其子同斩，不能用其独证儿子。')
extra(old_li, 'event', 'event_zztj_265_0905_li_zhen_replaces_wang', 'description',
      '《旧五代史》卷十八记朱全忠于天祐二年春正月遣李振赴青州。',
      '天祐二年春正月，太祖召振', 4, 'corroborates',
      '旧书没有与主书庚午逐日对应，不据此定同一天。')
extra(old_li, 'event', 'event_zztj_265_0905_wang_shifan_relocates', 'description',
      '《旧五代史》卷十八亦记王师范率族迁移。',
      '翌日，以其族遷。', 6, 'corroborates',
      '旧书称翌日，主书未给相同相对日；不强定。')
extra(old_li, 'event', 'event_zztj_265_0905_li_zhen_qingzhou_liuhou', 'description',
      '《旧五代史》卷十八记朱全忠表李振为青州留后。',
      '太祖乃表振為青州留後', 6, 'corroborates',
      '两书均仅记表荐。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 7):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
        review='卷265天祐二年第1—6段连续处理；围城、劝降、攻克、转任与返程按原文先后分录；旧五代史与新五代史独立补证。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=265, year=905,
    primary_source_key=primary, primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(1, 7)], next_paragraph=Q[7]['id'],
    coverage='卷265天祐二年第1—6段连续处理：寿州围攻、润州攻克、睦州救援及青州易任。',
    supplements=supplements, status=status), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
