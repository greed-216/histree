# coding: utf-8
"""Advance the 907 chronological cursor after verified public readback."""
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
assert all(x['status'] == 'published_verified' for x in ledger[:7])
assert all(x['status'] in ('reviewed', 'published_verified') for x in ledger[7:15])
assert ledger[15]['status'] == 'pending'
for row in ledger[7:15]:
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
year['note'] = '卷266开平元年第1—15段已连续发布并匿名读回；后续从第16段按原文继续。'
progress['active_cursor'].update(volume=266, year=907,
    last_reviewed_paragraph=ledger[14]['id'], next_paragraph=ledger[15]['id'],
    next_paragraph_opening=ledger[15]['text'], batch=batch_path,
    status='partial_published_verified', last_published_paragraph=ledger[14]['id'])
progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')

index_file = ROOT / 'content/books/zizhi-tongjian/index.json'
index = json.loads(index_file.read_text())
index['current_batch'] = batch_path
index['next_paragraph'] = ledger[15]['id']
index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')

(P / 'review.md').write_text('''# 卷266·开平元年第8—15段校核

- 八段连续对应《资治通鉴》卷266原文件第13—20行；12个事件、54条事实引用。发布哈希与匿名读回见 `publication.json`。
- 幽州出兵、刘守光囚父、避难者归河东、温州战事及禅位交涉复用旧907档案事件 UUID。钱镠与两子、杨涉与杨凝式、刘仁恭与刘守光、刘守光与刘守奇五条关系均复用原有方向。
- 第11段唐廷降御札并派册礼使，尚不等于朱温已称帝；杨凝式劝父辞送玺之事单列为细分事件，不能写成杨涉已辞职。
- 第12段刘仁恭筑馆、敛钱与茶禁是时间不明的追述，事件年份留空。第13段与罗氏相关的家事亦为前情；仅有姓氏，不另造具名人物。
- 第13段电子底本的“银胡录”含未识字；不据此补写王思同官名。第13段《新五代史》卷三十九印证李思安退兵后刘守光自称节度使、囚父，但后续兄弟争战没有倒填本段。
- 第15段钱传瓘绕青澳、温州陷落、卢佶被杀与吴璋任命按原文次序留在既有温州事件中。下一段 `zztj-v266-y0907-p016`。
''')
print(ledger[15]['id'])
