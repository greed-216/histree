# coding: utf-8
"""Mark the fully published 906 year complete and open the 907 cursor."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'content/yearly-progress.json').exists())
YEAR = P.parent
batch_path = str(P.relative_to(ROOT))
audit = json.loads((P / 'publication.json').read_text())
assert audit['verified'] and audit['batch_sha256'] == hashlib.sha256((P / 'content-batch.json').read_bytes()).hexdigest()
correction = json.loads((ROOT / 'content/revisions/2026-10-02-wang-maozhang-jingren/publication.json').read_text())
assert correction['verified'] and correction['anonymous_readback_verified']

ledger_file = YEAR / 'paragraphs.json'
ledger = json.loads(ledger_file.read_text())
assert len(ledger) == 42
assert all(row['status'] == 'published_verified' for row in ledger[:32])
assert all(row['status'] in ('reviewed', 'published_verified') for row in ledger[32:])
for row in ledger[32:]:
    row['status'] = 'published_verified'
ledger_file.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')

coverage_file = P / 'coverage.json'
coverage = json.loads(coverage_file.read_text())
coverage['status'] = 'published_verified'
coverage_file.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n')

next_year_dir = ROOT / 'content/books/zizhi-tongjian/vol-266/year-0907'
next_year_dir.mkdir(parents=True, exist_ok=True)
next_ledger_file = next_year_dir / 'paragraphs.json'
raw_lines = (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()
assert '公元九零七年' in raw_lines[4] and '公元九零八年' in raw_lines[67]
new_ledger = [dict(id=f'zztj-v266-y0907-p{i:03d}', source_line=line_no,
                   text=raw_lines[line_no - 1], status='pending', event_keys=[],
                   batch_key=None, review=None)
              for i, line_no in enumerate(range(6, 67), 1)]
assert len(new_ledger) == 61 and new_ledger[0]['text'].startswith('春，正月，辛巳')
if next_ledger_file.exists():
    assert json.loads(next_ledger_file.read_text()) == new_ledger
else:
    next_ledger_file.write_text(json.dumps(new_ledger, ensure_ascii=False, indent=2) + '\n')

progress_file = ROOT / 'content/yearly-progress.json'
progress = json.loads(progress_file.read_text())
year = next(row for row in progress['year_coverage'] if row['year'] == 906)
if batch_path not in year['batches']:
    year['batches'].append(batch_path)
year.update(status='complete_published_verified', completed_volumes=[265],
            note='卷265天祐三年第1—42段已连续发布并匿名读回；第35段王茂章改名景仁的身份勘误另见 content/revisions。')
if not any(row['year'] == 907 and row.get('volumes') == [266] for row in progress['year_coverage']):
    progress['year_coverage'].append(dict(year=907, status='pending', volumes=[266],
                                         batches=[], completed_volumes=[],
                                         note='卷266开平元年共61段，待从第1段连续录入。'))
progress['active_cursor'] = dict(volume=266, year=907,
                                 last_reviewed_paragraph=None,
                                 next_paragraph=new_ledger[0]['id'],
                                 next_paragraph_opening=new_ledger[0]['text'],
                                 batch=batch_path, status='pending',
                                 last_published_paragraph=ledger[-1]['id'])
progress_file.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')

index_file = ROOT / 'content/books/zizhi-tongjian/index.json'
index = json.loads(index_file.read_text())
index.update(current_year=907, current_volumes=[266], current_volume=266,
             current_batch=batch_path, next_paragraph=new_ledger[0]['id'])
index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')

(P / 'review.md').write_text('''# 卷265·天祐三年第33—42段校核

- 十段连续对应《资治通鉴》原文件第124—133行；18个事件、80条事实引用和一条明确父子关系。批次哈希及匿名读回见 `publication.json`。
- 第33段《通鉴》写康怀贞，第32段及《旧五代史》相近战事写康怀英；两人已在站内分别建档，暂不因“乘胜”合并。旧书只确记鄜州，不独立证明五州全数。
- 第34段“子澧”明确高彦与高澧父子关系。第38段“初”所述丁会为昭宗哀悼属于追叙，事件年份保留未定；《旧五代史》丁会传对潞州归晋纪时作十二月，主书作闰月条。
- 第35段王景仁即本年第2段王茂章改名后的人物。首次发布时误建独立人物，已按 `content/revisions/2026-10-02-wang-maozhang-jingren/` 归并线上参与边与人物引用，原批次保留审计。
- 第40段《旧五代史》卷二“案”后引述不当作旧书主叙独立证据；本批留粮事实仅据《通鉴》主文。第42段“本”提示钟传任彭玕的记载是追叙，确年未载。
- 906年卷265第1—42段已全部发布并匿名读回；下一段为卷266开平元年 `zztj-v266-y0907-p001`。电子底本仍待纸本逐字核校。
''')
print(new_ledger[0]['id'])
