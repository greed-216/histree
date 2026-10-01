"""Validate normalized text, complete source coverage, search and exact exports."""
import bisect
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'resources/derived/history-library'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nonspace(text):
    return re.sub(r'\s+', '', text)


def main():
    spec = importlib.util.spec_from_file_location('normalizer', ROOT / 'scripts/build-history-library.py')
    normalizer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(normalizer)
    assert normalizer.normalize('  黃 帝 A B  ', 'body') == '黃帝 A B'
    assert normalizer.normalize('甲\t乙', 'table_row') == '甲\t乙'
    assert list(normalizer.split_ranges('甲' * 1250, 0, 1250, 'body')) == [
        (0, 800, 'character_size_split'), (800, 1250, 'epub_source_paragraph')]
    # Cache reconstruction works without an existing SQLite file and never rewrites records.
    with tempfile.TemporaryDirectory(prefix='histree-cache-test-') as tmp:
        folder = Path(tmp)
        sample = {'id': 'fixture-p1', 'book_key': 'fixture', 'book': '测试书',
                  'section_id': 'fixture-s1', 'section_title': '卷一', 'volume_candidate': 1,
                  'kind': 'body', 'text': '明皇帝即位。'}
        records = folder / 'paragraphs.jsonl.gz'
        with gzip.open(records, 'wt', encoding='utf-8') as handle:
            handle.write(json.dumps(sample, ensure_ascii=False) + '\n')
        fixture_catalog = {'books': [{'book_key': 'fixture', 'book': '测试书',
                                     'paragraph_file': str(records), 'paragraph_sha256': sha(records), 'paragraphs': 1}]}
        (folder / 'catalog.json').write_text(json.dumps(fixture_catalog))
        before = sha(records)
        normalizer.rebuild_search(folder)
        with sqlite3.connect(folder / 'search.sqlite') as cache:
            assert json.loads(zlib.decompress(cache.execute('SELECT record_json FROM paragraphs').fetchone()[0])) == sample
            assert cache.execute('SELECT count(*) FROM search WHERE search MATCH ?', ('"明皇帝"',)).fetchone()[0] == 1
        assert sha(records) == before
        good_cache = sha(folder / 'search.sqlite')
        fixture_catalog['books'][0]['paragraph_sha256'] = 'invalid'
        (folder / 'catalog.json').write_text(json.dumps(fixture_catalog))
        try:
            normalizer.rebuild_search(folder)
        except AssertionError:
            pass
        else:
            raise AssertionError('Changed records must fail reconstruction')
        assert sha(folder / 'search.sqlite') == good_cache, 'Failed build replaced the working cache'
    catalog = json.loads((BASE / 'catalog.json').read_text())
    assert len(catalog['books']) == 26
    db = sqlite3.connect('file:' + str(BASE / 'search.sqlite') + '?mode=ro', uri=True)
    assert db.execute('SELECT value FROM metadata WHERE key=?', ('catalog_sha256',)).fetchone()[0] == sha(BASE / 'catalog.json')
    report, samples = [], []
    for book in catalog['books']:
        for field in ('paragraph', 'sections', 'reading'):
            assert sha(ROOT / book[field + '_file']) == book[field + '_sha256']
        inputs = {}
        for inp in book['inputs']:
            assert sha(ROOT / inp['source_file']) == inp['source_sha256']
            assert sha(ROOT / inp['mapped_source_file']) == inp['mapped_source_sha256']
            path = inp['mapped_source_file']
            text = (ROOT / path).read_text(encoding='utf-8')
            inputs[path] = {'text': text, 'cursor': 0,
                            'line_starts': [0] + [m.end() for m in re.finditer('\n', text)]}
        sql_rows = iter(db.execute('SELECT record_json FROM paragraphs WHERE book_key=? ORDER BY rowid', (book['book_key'],)))
        counts, section_counts, normalized_parts = Counter(), Counter(), []
        first_body = None
        ids = set()
        with gzip.open(ROOT / book['paragraph_file'], 'rt', encoding='utf-8') as handle:
            for line in handle:
                p = json.loads(line)
                assert p == json.loads(zlib.decompress(next(sql_rows)[0]))
                assert p['id'] not in ids
                ids.add(p['id'])
                loc = p['locator']
                data = inputs[loc['source_file']]
                a, b = loc['char_start'], loc['char_end']
                assert data['cursor'] <= a < b <= len(data['text']), p['id']
                assert not data['text'][data['cursor']:a].strip(), 'Omitted prose'
                excerpt = data['text'][a:b]
                assert hashlib.sha256(excerpt.encode()).hexdigest() == loc['raw_excerpt_sha256']
                assert nonspace(excerpt) == nonspace(p['text'])
                assert loc['line_start'] == bisect.bisect_right(data['line_starts'], a)
                assert loc['line_end'] == bisect.bisect_right(data['line_starts'], max(a, b - 1))
                data['cursor'] = b
                counts[p['kind']] += 1
                section_counts[p['section_id']] += 1
                normalized_parts.append(p['text'] + '\n\n')
                if p['kind'] == 'body' and first_body is None and re.search(r'[\u3400-\u9fff]{4,}', p['text']):
                    first_body = p
        assert next(sql_rows, None) is None
        assert len(ids) == book['paragraphs']
        assert dict(counts) == book['kind_counts']
        for data in inputs.values():
            assert not data['text'][data['cursor']:].strip(), 'Omitted source tail'
        assert (ROOT / book['reading_file']).read_text() == ''.join(normalized_parts)
        sections = json.loads((ROOT / book['sections_file']).read_text())
        assert all(section_counts[s['id']] == s['paragraphs'] for s in sections)
        if book['book_key'] != 'zizhi-tongjian':
            conversion = json.loads((ROOT / book['inputs'][0]['conversion_manifest']).read_text())
            volumes = [(s['volume_candidate'], s['volume_part']) for s in sections if s['volume_candidate']]
            assert {v for v, _ in volumes} == set(range(1, conversion['expected_volumes'] + 1))
            # Reading copies conserve every non-whitespace source character, once.
            assert nonspace(''.join(normalized_parts)) == nonspace(next(iter(inputs.values()))['text'])
        assert first_body is not None
        token = re.search(r'[\u3400-\u9fff]{4,}', first_body['text'])[0][:3]
        assert db.execute('SELECT 1 FROM paragraphs p JOIN search s ON p.rowid=s.rowid WHERE p.id=? AND search MATCH ?',
                          (first_body['id'], '"' + token + '"')).fetchone()
        samples.append(first_body)
        report.append({'book': book['book'], 'paragraphs': len(ids), 'source_coverage': 'passed'})
        print(book['book'], len(ids), '源文件、字符守恒、行段定位与FTS通过', flush=True)
    assert db.execute('SELECT count(*) FROM paragraphs').fetchone()[0] == sum(b['paragraphs'] for b in catalog['books'])
    # Regression: previously missing volumes are now searchable.
    for query, title, volume in [('石敬瑭', '旧五代史', 75), ('王昕', '北齐书', 31), ('明皇帝', '周书', 4)]:
        result = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/search-history-library.py'), query,
                                                     '--book', title, '--volume', str(volume)], text=True))
        assert result['returned'] > 0, (query, title, volume)
    two = json.loads(subprocess.check_output([sys.executable, str(ROOT / 'scripts/search-history-library.py'), '李克', '--book', '旧五代史'], text=True))
    assert two['returned'] > 0
    with tempfile.TemporaryDirectory(prefix='histree-source-test-') as tmp:
        for sample in (samples[17], samples[-1]):
            destination = Path(tmp) / sample['book_key']
            subprocess.check_output([sys.executable, str(ROOT / 'scripts/search-history-library.py'), '--id', sample['id'], '--export', str(destination)])
            loc = sample['locator']
            assert (destination / 'source.txt').read_text() == (ROOT / loc['source_file']).read_text()[loc['char_start']:loc['char_end']]
    # The primary chronological library retained every existing paragraph ID.
    old = BASE.with_name('history-library.previous') / 'zizhi-tongjian/index.json'
    if old.exists():
        prior = json.loads(old.read_text())
        path = BASE.with_name('history-library.previous') / 'zizhi-tongjian' / Path(prior['paragraph_file']).name
        opener = gzip.open if path.suffix == '.gz' else open
        with opener(path, 'rt', encoding='utf-8') as handle:
            original_ids = [json.loads(line)['id'] for line in handle]
        current = next(b for b in catalog['books'] if b['book_key'] == 'zizhi-tongjian')
        with gzip.open(ROOT / current['paragraph_file'], 'rt', encoding='utf-8') as handle:
            assert original_ids == [json.loads(line)['id'] for line in handle]
    result = {'status': 'verified', 'books': 26, 'records': sum(b['paragraphs'] for b in catalog['books']), 'results': report,
              'checks': ['source hashes', 'complete non-whitespace coverage', 'no overlap', 'exact locators',
                         'SQLite equality', 'FTS per book', 'short queries', 'missing-volume regressions', 'exact exports', 'Tongjian IDs']}
    original_dir = ROOT / 'resources/originals/twenty-four-histories'
    assert len(list(original_dir.glob('*-EPUB全文.txt'))) == 25
    assert all(p.name == 'backup' or p.name.endswith('-EPUB全文.txt') for p in original_dir.iterdir())
    aliases = json.loads((ROOT / 'resources/catalog/source-replacements.json').read_text())
    for alias in aliases['aliases']:
        assert sha(ROOT / alias['backup_file']) == alias['sha256']
    cleanup = json.loads((ROOT / 'resources/catalog/history-text-cleanup.json').read_text())
    for path, h in cleanup['protected_files'].items():
        assert sha(ROOT / path) == h
    for path, h in cleanup.get('local_unversioned_protected_files', {}).items():
        if (ROOT / path).exists():
            assert sha(ROOT / path) == h
    (BASE / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'books', 'records')}))


if __name__ == '__main__':
    main()
