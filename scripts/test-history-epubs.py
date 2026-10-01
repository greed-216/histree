"""Verify conversion edge cases and all generated source maps against local sources."""
import importlib.util
import json
import gzip
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('converter', ROOT / 'scripts/prepare-history-epubs.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def fixture():
    # Exercise tails, empty glyph spans, table cells, notes and header provenance.
    raw = '''<html xmlns="http://www.w3.org/1999/xhtml"><body>
    <div id="headerContainer-1"><table><tr><td>上一卷</td><td style="width:50%">補列傳</td><td>下一卷</td></tr></table></div>
    <p>甲<span data-mw-variant='{"disabled":{"t":"后"}}'/>乙<span data-mw-variant='{"twoway":[{"l":"zh-hans","t":"发"},{"l":"zh-hant","t":"發"}]}'/>丙<br/>丁<img alt="鉉" src="glyph.png"/>戊</p>
    <table><tr><td>壹</td><td>貳</td></tr></table>
    <ol class="references"><li>注文<span>內容</span></li></ol>
    <div class="licenseContainer">Public domainPublic domain</div>尾
    </body></html>'''.encode()
    headers, rows, removed, variants, issues = c.extract(raw)
    assert [h['text'] for h in headers] == ['補列傳']
    assert [r['text'] for r in rows] == ['甲后乙發丙', '丁鉉戊', '壹\t貳', '注文內容', '尾']
    assert rows[3]['kind'] == 'annotation'
    assert any(r['action'] == 'restore_image_alt' for r in variants)
    assert len(removed) == 2
    assert any(r['kind'] == 'nontext_image' for r in issues)
    assert c.chinese(4) == '四' and c.chinese(120) == '一百二十' and c.chinese(529) == '五百二十九'


def main():
    fixture()
    catalog = json.loads((c.OUT / 'catalog.json').read_text())
    assert len(catalog['books']) == 25
    total = 0
    for p, expected_hash in catalog['original_source_hashes_preserved'].items():
        assert c.sha((ROOT / p).read_bytes()) == expected_hash, p
    for book in catalog['books']:
        folder = c.OUT / f'{book["book_number"]:02d}{book["book"]}'
        target = ROOT / book['txt_file']
        raw = target.read_bytes()
        assert c.sha(raw) == book['txt_sha256']
        text = raw.decode('utf-8')
        assert '\r' not in text and 'data-mw-variant=' not in text
        assert c.sha((ROOT / book['epub_file']).read_bytes()) == book['epub_sha256']
        for name, h in book['outputs'].items():
            assert c.sha((folder / name).read_bytes()) == h, name
        for archive in book['previous_conversion_archives']:
            assert c.sha((ROOT / archive['file']).read_bytes()) == archive['sha256']
        sections = json.loads((folder / 'sections.json').read_text())
        assert {s['volume'] for s in sections if s['volume']} == set(range(1, book['expected_volumes'] + 1))
        volumes = [(s['volume'], c.PARTS[s['part']][0]) for s in sections if s['volume']]
        assert volumes == sorted(volumes)
        assert len(volumes) == len(set(volumes)), 'Duplicate volume subdivision'
        with gzip.open(folder / 'paragraphs.jsonl.gz', 'rt', encoding='utf-8') as handle:
            mappings = [json.loads(line) for line in handle]
        groups = {}
        for record in mappings:
            groups.setdefault(record['section'], []).append(record)
        assert len(mappings) == book['mapped_paragraphs_including_headings']
        newline_offsets = [-1] + [i for i, char in enumerate(text) if char == '\n']
        import bisect
        for m in mappings:
            fragment = text[m['char_start']:m['char_end']]
            assert c.sha(fragment.encode()) == m['text_sha256']
            assert m['line_start'] == bisect.bisect_left(newline_offsets, m['char_start'])
            assert m['line_end'] == m['line_start'] + fragment.count('\n')
        # Every source member is re-read; compare headings and ordered content to
        # their mapped fragments, including restored inline glyphs and notes.
        with zipfile.ZipFile(ROOT / book['epub_file']) as epub:
            for s in sections:
                source = epub.read(s['epub_member'])
                assert c.sha(source) == s['member_sha256']
                headers, rows, _, _, _ = c.extract(source)
                group = groups.get(s['section'], [])
                expected = [h['text'] for h in headers] + [r['text'] for r in rows]
                assert [text[m['char_start']:m['char_end']] for m in group] == expected
                segment = text[s['full_txt_char_start']:s['full_txt_char_end']]
                assert c.sha(segment.encode()) == s['text_sha256']
                assert sum(len(c.norm(r['text'])) for r in rows) == s['body_non_whitespace_characters']
        total += len(mappings)
        print(f'{book["book"]}：源文件、卷序、逐段文字、行号和字符定位通过', flush=True)
    # Known omissions remain visible, rather than fabricated or silently dropped.
    qing = (c.ORIGINALS / '25清史稿-EPUB全文.txt').read_text()
    assert '（表略）' in qing
    bei = (c.ORIGINALS / '11北齐书-EPUB全文.txt').read_text()
    assert '補列傳第三一' in bei
    zhou = (c.ORIGINALS / '12周书-EPUB全文.txt').read_text()
    assert '周书卷四（' in zhou
    print(f'PASS: 25 books, {total} mapped paragraphs/headings; original sources preserved')


if __name__ == '__main__':
    main()
