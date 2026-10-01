"""Validate correction replay, preserved glyphs, and local PDF deletion evidence."""
import argparse
from difflib import SequenceMatcher
import importlib.util
import json
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location('repair', Path(__file__).with_name('repair-history-txt.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pdf-cache', type=Path, required=True)
args = parser.parse_args()
catalog = json.loads((m.OUT / 'catalog.json').read_text())
report = []
for entry in catalog:
    text = m.verify_replay(entry)
    raw = (m.ROOT / entry['source_file']).read_bytes().decode('gb18030', errors='surrogateescape')
    assert len(raw.splitlines()) == len(text.splitlines())
    # Private glyphs must never disappear as a side effect of PDF extraction.
    private = lambda t: ''.join(c for c in t if 0xe000 <= ord(c) <= 0xf8ff)
    changes = [json.loads(row) for row in (m.ROOT / entry['edits_file']).read_text().splitlines()]
    expected_private = private(raw)
    if not entry.get('reference'):
        # Site prefixes can themselves include a private glyph. Only that
        # redundant prefix may disappear; the retained name stays verbatim.
        for edit in changes:
            before, after = edit['before'], edit['after']
            if edit['reason'] == 'paired_web_watermark':
                assert before[:2] == before[2:4]
                assert after == before[2:].rstrip('\r\n')[:-1] + re.search(r'[\r\n]*$', before)[0]
            elif edit['reason'] == 'paired_parenthetical_web_watermark':
                assert before[0] == '（' and before[1] == before[2]
                assert after == before[:1] + before[2:].rstrip('\r\n')[:-1] + re.search(r'[\r\n]*$', before)[0]
            else:
                assert private(before) == private(after)
        # Private glyph identity remains for all occurrences outside duplication.
        reconstructed = raw.splitlines(keepends=True)
        for edit in changes:
            reconstructed[edit['line'] - 1] = edit['after']
        expected_private = private(''.join(reconstructed))
    assert expected_private == private(text)
    if entry.get('reference'):
        ref = entry['reference']
        assert m.sha(m.ROOT / ref['source_file']) == ref['source_sha256']
        cache = args.pdf_cache / (Path(entry['source_file']).stem + '.jsonl')
        assert m.sha(cache) == ref['extraction_cache_sha256']
        pages = {r['pdf_page']: r['text'] for r in map(json.loads, cache.read_text().splitlines())}
        for edit in changes:
            if edit['reason'] == 'local_pdf_compared_text':
                evidence = edit['evidence']
                passage = m.norm(''.join(pages[i] for i in range(evidence['pdf_page_start'], evidence['pdf_page_end'] + 1)))
                # Strip page headers using the same independently cached pages.
                clean = []
                for i in range(evidence['pdf_page_start'], evidence['pdf_page_end'] + 1):
                    rows = pages[i].splitlines()
                    for n, row in enumerate(rows):
                        s = m.norm(row)
                        if n < 4 and (s == Path(ref['source_file']).stem[2:] or re.fullmatch(r'\d+/\d+', s)):
                            continue
                        clean.append(s)
                assert evidence['excerpt'] in ''.join(clean)
                before, after = m.norm(edit['before']), m.norm(edit['after'])
                ops = SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
                assert all(op[0] in ('equal', 'delete') for op in ops)
                deleted = [before[a:b] for op,a,b,_,_ in ops if op == 'delete']
                assert deleted and all(chunk not in evidence['excerpt'] for chunk in deleted if len(chunk) > 12)
            elif edit['reason'] == 'invalid_byte_explicit_missing_glyph':
                expected = ''.join(f'〔缺字：原字节{ord(c)-0xdc00:02X}〕' if 0xdc80 <= ord(c) <= 0xdcff else c for c in edit['before'])
                assert expected == edit['after']
    report.append({'file': Path(entry['source_file']).name, 'changes': len(changes),
                   'remaining_review_items': len(entry['unresolved']),
                   'corrected_sha256': entry['corrected_sha256'], 'status': 'verified'})
(m.OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
