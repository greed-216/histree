"""Verify emitted TXT outputs against user source bytes, lines, and characters."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('txt_reader', ROOT / 'scripts/prepare-history-txt.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.heading('    ●卷一·五帝本纪第一') == '卷一·五帝本纪第一'
assert m.heading('********四夷附录第一') == '四夷附录第一'
assert m.heading('贞观初，有益州人阴弘道，又执孝通旧说以驳之。') is None
assert m.decode('甲乙'.encode('gb18030')) == ('甲乙', 'gb18030')
try:
    m.decode(b'\xff')
    raise AssertionError('Invalid bytes must not be silently replaced')
except UnicodeDecodeError:
    pass

catalog = json.loads((m.OUT / 'catalog.json').read_text())
report = []
for entry in catalog['files']:
    source = ROOT / entry['source_file']
    assert m.reader.digest(source) == entry['source_sha256']
    if entry.get('supplemented_reading_file'):
        assert m.reader.digest(ROOT/entry['supplemented_reading_file'])==entry['supplemented_reading_sha256']
    if entry['status'] == 'blocked_decoding':
        try:
            m.decode(source.read_bytes())
            raise AssertionError(f'Unexpected blocked source: {source}')
        except UnicodeDecodeError:
            report.append({'file': source.name, 'status': 'blocked_decoding_verified'})
        continue
    if entry.get('corrections_manifest'):
        manifest = ROOT / entry['corrections_manifest']
        assert m.reader.digest(manifest) == entry['corrections_manifest_sha256']
        text = m.repairs.verify_replay(json.loads(manifest.read_text()))
        assert m.reader.digest(ROOT / entry['corrected_source_file']) == entry['corrected_source_sha256']
    else:
        text = source.read_bytes().decode(entry['encoding'])
    lines = text.splitlines()
    assert (m.OUT / source.stem / 'decoded-source.txt').read_bytes().decode('utf-8') == text
    seen, texts = [], []
    for unit in entry['units']:
        assert m.reader.digest(ROOT / unit['mapped_file']) == unit['mapped_sha256']
        assert m.reader.digest(ROOT / unit['text_file']) == unit['text_sha256']
        rendered = []
        for line in (ROOT / unit['mapped_file']).open():
            block = json.loads(line)
            rendered.append(block['text'])
            texts.append(block['text'])
            for span in block['source_spans']:
                i, start, end = span['line'], span['char_start'], span['char_end']
                assert lines[i-1][start:end] == span['raw']
                seen.append((i, start, end))
        assert (ROOT / unit['text_file']).read_text() == '\n\n'.join(rendered) + '\n'
    expected = [(i+1, start, min(start+1600, len(line))) for i, line in enumerate(lines)
                if line.strip() for start in range(0, len(line), 1600)]
    assert seen == expected
    assert re.sub(r'\s', '', ''.join(texts)) == re.sub(r'\s', '', text)
    report.append({'file': source.name, 'status': 'verified', 'navigation_units': len(entry['units']),
                   'blocks': len(texts), 'checks': 'source hashes, strict decoding, exact source mapping, character conservation'})
print(json.dumps(report, ensure_ascii=False, indent=2))
(m.OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
