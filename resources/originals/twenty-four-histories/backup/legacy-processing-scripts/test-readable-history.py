"""Check complete source-line coverage and reversible content in reading copies."""
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('readable', ROOT / 'scripts/prepare-readable-history.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# Regression: a page break must not sever a name; header removal is position-limited.
rows, removed = m.pdf_lines('旧五代史 \n1/2 \n李克\n', '旧五代史', 1, 2)
tail, _ = m.pdf_lines('旧五代史 \n2/2 \n用。  \n旧五代史\n', '旧五代史', 2, 2)
blocks = m.make_blocks(rows + tail, 'pdf')
assert blocks[0]['text'] == '李克用。'
assert blocks[1]['text'] == '旧五代史'
assert len(removed) == 2
metadata, rows, _ = m.kanripo_lines('#+PROPERTY: JUAN 卷上\n<pb:TEST_001-1a>¶\n甲乙丙丁戊己庚辛壬¶\n丙丁(小/注)¶\n　注文內容甲乙丙丁戊¶\n')
blocks = m.make_blocks(rows, 'kanripo')
assert metadata['JUAN'] == '卷上'
assert blocks[0]['text'] == '甲乙丙丁戊己庚辛壬丙丁(小/注)'
assert blocks[1]['kind'] == 'indented_block'
assert blocks[0]['source_spans'][0]['leaf'] == 'TEST_001-1a'
assert m.compact('甲 乙， 丙 English words') == '甲乙，丙 English words'

summary = []
for path in sorted(m.OUT.glob('*/index.json')):
    index = json.loads(path.read_text())
    seen, expected = Counter(), Counter()
    originals = {}
    count = 0
    if index['kind'] == 'pdf_bookmark_sections':
        source = ROOT / index['raw_text_file']
        assert m.digest(source) == index['raw_text_sha256']
        assert m.digest(ROOT / index['source_file']) == index['source_sha256']
        for line in source.open():
            page = json.loads(line)
            rows, _ = m.pdf_lines(page['text'], index['book'], page['pdf_page'], index['pdf_pages'])
            expected.update((str(source), page['pdf_page'], r['line']) for r in rows if r['raw'].strip())
            originals.update({(str(source), page['pdf_page'], r['line']): r['raw'] for r in rows})
    for unit in index['units']:
        assert m.digest(ROOT / unit['text_file']) == unit['text_sha256']
        assert m.digest(ROOT / unit['mapped_file']) == unit['mapped_sha256']
        if index['kind'] == 'kanripo_juan_files':
            source = ROOT / unit['source_file']
            assert m.digest(source) == unit['source_sha256']
            _, rows, _ = m.kanripo_lines(source.read_text())
            expected.update((str(source), None, r['line']) for r in rows if r['raw'].strip().removesuffix('¶'))
            originals.update({(str(source), None, r['line']): r['raw'] for r in rows})
        for line in (ROOT / unit['mapped_file']).open():
            block = json.loads(line)
            count += 1
            spans = block['source_spans']
            seen.update((str(ROOT / r['source_file']), r.get('pdf_page'), r['line']) for r in spans)
            for r in spans:
                assert originals[(str(ROOT / r['source_file']), r.get('pdf_page'), r['line'])] == r['raw']
            original = ''.join(r['raw'].strip().removesuffix('¶') for r in spans)
            assert re.sub(r'\s', '', original) == re.sub(r'\s', '', block['text'])
    assert seen == expected, f'Lost/duplicated source lines: {path}'
    summary.append({'book': index['book'], 'units': len(index['units']), 'blocks': count,
                    'source_lines': sum(seen.values()), 'checks': 'hashes, exact line coverage, character conservation'})
print(json.dumps(summary, ensure_ascii=False, indent=2))
