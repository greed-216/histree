# coding: utf-8
"""Mark the first 907 chronological batch verified and preserve the next cursor."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'content/yearly-progress.json').exists())
YEAR = P.parent
audit = json.loads((P / 'publication.json').read_text())
assert audit['verified'] and audit['batch_sha256'] == hashlib.sha256((P / 'content-batch.json').read_bytes()).hexdigest()
prior_ids = json.loads((ROOT / 'content/year-0907/sql/key-map.json').read_text())
current_ids = json.loads((P / 'sql/key-map.json').read_text())
bridges = ['event_0907_beizhou', 'event_0907_huainan_coup', 'event_0907_persuade',
           'event_0907_jinzhou_defense', 'event_0907_abdication_petitions']
assert all(prior_ids[key] == current_ids[key] for key in bridges)

ledger_file = YEAR / 'paragraphs.json'
ledger = json.loads(ledger_file.read_text())
assert len(ledger) == 61
assert all(row['status'] in ('reviewed', 'published_verified') for row in ledger[:7])
assert ledger[7]['status'] == 'pending'
for row in ledger[:7]:
    row['status'] = 'published_verified'
ledger_file.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')

coverage_file = P / 'coverage.json'
coverage = json.loads(coverage_file.read_text())
coverage['status'] = 'published_verified'
coverage_file.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n')

batch_path = str(P.relative_to(ROOT))
progress_file = ROOT / 'content/yearly-progress.json'
progress = json.loads(progress_file.read_text())
year = next(row for row in progress['year_coverage'] if row['year'] == 907 and row.get('volumes') == [266])
if batch_path not in year['batches']:
    year['batches'].append(batch_path)
year['status'] = 'partial_published_verified'
year['note'] = '卷266开平元年第1—7段已发布并匿名读回；五个事件复用此前907年档案的相同UUID，编年主线已接续。余第8—61段保留待后续逐段核查。'
progress['active_cursor'].update(volume=266, year=907,
    last_reviewed_paragraph=ledger[6]['id'], next_paragraph=ledger[7]['id'],
    next_paragraph_opening=ledger[7]['text'], batch=batch_path,
    status='partial_published_verified', last_published_paragraph=ledger[6]['id'])
progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')

index_file = ROOT / 'content/books/zizhi-tongjian/index.json'
index = json.loads(index_file.read_text())
index['current_batch'] = batch_path
index['next_paragraph'] = ledger[7]['id']
index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')

(P / 'review.md').write_text('''# 卷266·开平元年第1—7段校核

- 七段连续对应《资治通鉴》卷266原文件第6—12行；10个事件、48条事实引用。《新五代史》卷六十一另证杨渥杀周隐。批次哈希和匿名读回见 `publication.json`。
- 贝州休兵、淮南兵谏、罗绍威与薛贻矩的禅代交涉、晋州防备及劝进，均复用 `content/year-0907` 已发布事件的稳定 key 和 UUID。第1段是编年主线与旧907档案的直接接点。
- 另立周隐被杀、吕师周出奔与其家属脱离、张颢徐温劝谏、三将受诬被杀五个原档案未单列事件。三将姓名按本段“硃思勍、范思从、陈璠”逐字回查，站内规范名用“朱思勍”。
- 第4段电子底本作“丙戍”，保留原字并待历日与纸本核校。第5段“罗绍威恐王袭之”是主书对人物心理的叙述，未据此推定朱温真的计划袭魏。
- 本阶段已按用户要求接续到旧907年档案。907年共61段，本批仅第1—7段连续发布，第8—61段仍待后续整理；下一段 `zztj-v266-y0907-p008`。
''')
print(ledger[7]['id'], len(bridges))
