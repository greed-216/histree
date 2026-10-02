# coding: utf-8
"""Advance the 907 cursor after accession batch public readback."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'content/yearly-progress.json').exists())
audit = json.loads((P / 'publication.json').read_text())
assert audit['verified'] and audit['batch_sha256'] == hashlib.sha256((P / 'content-batch.json').read_bytes()).hexdigest()

ledger_file = P.parent / 'paragraphs.json'
ledger = json.loads(ledger_file.read_text())
assert len(ledger) == 61
assert all(x['status'] == 'published_verified' for x in ledger[:15])
assert all(x['status'] in ('reviewed', 'published_verified') for x in ledger[15:22])
assert ledger[22]['status'] == 'pending'
for row in ledger[15:22]:
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
year['note'] = '卷266开平元年第1—22段连续发布并匿名读回；第16—22段涵盖后梁即位、改元及初期制度变化。'
progress['active_cursor'].update(volume=266, year=907,
    last_reviewed_paragraph=ledger[21]['id'], next_paragraph=ledger[22]['id'],
    next_paragraph_opening=ledger[22]['text'], batch=batch_path,
    status='partial_published_verified', last_published_paragraph=ledger[21]['id'])
progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')

index_file = ROOT / 'content/books/zizhi-tongjian/index.json'
index = json.loads(index_file.read_text())
index['current_batch'] = batch_path
index['next_paragraph'] = ledger[22]['id']
index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')

(P / 'review.md').write_text('''# 卷266·开平元年第16—22段校核

- 七段连续对应《资治通鉴》卷266原文件第21—27行；10个事件、39条事实引用。发布哈希与匿名读回见 `publication.json`。
- 第16段朱温更名“晃”，未新建人物；朱全昱为其兄长复用既有关系。第17段甲子即位，戊辰大赦改元、定国号；济阴王迁曹州与京府军名调整另录，避免埋入单一建国事件。
- 《通鉴》第17段跨两个检索分段，原文快照分别保留前后部分。《旧五代史》卷三一段称帝叙述明示转引《通鉴》，未作为独立确证；另用所载诏文印证“开平”“大梁”和“开封府、东都”政令，其受命修辞只视为政权自述。
- 第19段只确认敬翔“知崇政院事”；枢密院并入为后续段落。第20段朱诚、朱温母王氏与第21段朱友文的亲属、收养关系均复用既有方向。
- 第22段蜀王“各帝一方”为书信建议，李克用回书拒绝，不作同盟既成事实。下一段 `zztj-v266-y0907-p023`。
''')
print(ledger[22]['id'])
