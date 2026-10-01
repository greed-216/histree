# coding: utf-8
"""Advance local progress after the verified public readback."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'content/yearly-progress.json').exists())
YEAR = P.parent
audit = json.loads((P / 'publication.json').read_text())
assert audit['verified']
assert audit['batch_sha256'] == hashlib.sha256((P / 'content-batch.json').read_bytes()).hexdigest()

ledger_file = YEAR / 'paragraphs.json'
ledger = json.loads(ledger_file.read_text())
assert all(row['status'] in ('reviewed', 'published_verified') for row in ledger[24:32])
assert ledger[32]['status'] == 'pending'
for row in ledger[24:32]:
    row['status'] = 'published_verified'
ledger_file.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')

coverage_file = P / 'coverage.json'
coverage = json.loads(coverage_file.read_text())
coverage['status'] = 'published_verified'
coverage_file.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n')

progress_file = ROOT / 'content/yearly-progress.json'
progress = json.loads(progress_file.read_text())
batch_path = str(P.relative_to(ROOT))
progress['active_cursor'].update(
    last_reviewed_paragraph=ledger[31]['id'],
    next_paragraph=ledger[32]['id'],
    next_paragraph_opening=ledger[32]['text'],
    batch=batch_path,
    status='partial_published_verified',
    last_published_paragraph=ledger[31]['id'],
)
year = next(row for row in progress['year_coverage'] if row['year'] == 906)
if batch_path not in year['batches']:
    year['batches'].append(batch_path)
year['note'] = '卷265天祐三年第1—32段已连续发布并匿名读回；下一段第33段。'
progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')

index_file = ROOT / 'content/books/zizhi-tongjian/index.json'
index = json.loads(index_file.read_text())
index['current_batch'] = batch_path
index['next_paragraph'] = ledger[32]['id']
index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')

(P / 'review.md').write_text('''# 卷265·天祐三年第25—32段校核

- 八段连续对应《资治通鉴》原文件第116—123行；20个事件、108条事实引用。批次哈希与匿名读回见 `publication.json`。
- 站内主体使用规范简体名称：原文“硃全忠”映射既有“朱温／朱全忠”，其他繁体书证亦按同一实体匹配；所有来源快照和逐字摘录保持底本原字。
- 第25段朱全忠到长芦与第29段沧州围城分记；围城句未直书朱全忠本人，不单凭该句建立其围城事件参与边。第29段“缓攻”不等于解围。
- 第26段秦裴取洪州；《新五代史》同记九月克城及俘钟匡时、陈象，但未独立证实《通鉴》的五千人。
- 第28段刘仁恭征兵，《资治通鉴》作十万，《新五代史》作二十万，作为异说并列。
- 第31段李存勖对天下势力的估计是奏对话语，不作为量化事实。《旧五代史》补记马郁参与遣使。
- 第32段《通鉴》作戊戌遣救夏州；《旧五代史》十月辛巳所记可能对应杨崇本来寇，未合为同一日。电子底本“朗兵”疑字保留原文，待纸本校核。
- 下一段 `zztj-v265-y0906-p033`；906年尚余第33—42段。
''')
print(ledger[32]['id'])
