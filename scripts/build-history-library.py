"""Normalize selected EPUB-derived TXT sources and rebuild the local history index.

Does not modify sources, content batches, published excerpts or ingestion cursors.
Only one active normalized edition is kept; the SQLite index is rebuildable.
"""
import argparse
import bisect
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'resources/derived/history-library'
STAGE = OUT.with_name('history-library.build')
RULES = 'history-epub-paragraph-v3'
BOOKS = list(zip('shiji hanshu hou-hanshu sanguozhi jinshu songshu nan-qishu liangshu chenshu weishu bei-qishu zhoushu suishu nanshi beishi jiu-tangshu xin-tangshu jiu-wudaishi xin-wudaishi songshi liaoshi jinshi yuanshi mingshi qing-shigao'.split(),
                 '史记 汉书 后汉书 三国志 晋书 宋书 南齐书 梁书 陈书 魏书 北齐书 周书 隋书 南史 北史 旧唐书 新唐书 旧五代史 新五代史 宋史 辽史 金史 元史 明史 清史稿'.split()))
CJK = '\u3400-\u9fff\uf900-\ufaff\ue000-\uf8ff\U00020000-\U0003134f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def nonspace(text):
    return re.sub(r'\s+', '', text)


def normalize(text, kind):
    value = text.strip()
    if kind != 'table_row':
        value = re.sub(f'(?<=[{CJK}]) +(?=[{CJK}])', '', value)
    assert nonspace(value) == nonspace(text)
    return value


def split_ranges(text, a, b, kind):
    """Retain source paragraphs; only long prose receives marked reading splits."""
    if kind in ('body', 'annotation', 'appendix'):
        while b - a > 1200:
            cuts = list(re.finditer(r'[。！？；](?:[”」』])?', text[a + 400:min(a + 1000, b)]))
            cut = a + 400 + cuts[-1].end() if cuts else a + 800
            yield a, cut, 'sentence_size_split' if cuts else 'character_size_split'
            a = cut
    if text[a:b].strip():
        yield a, b, 'epub_source_paragraph'


def decode_record(raw):
    return json.loads(zlib.decompress(raw) if isinstance(raw, bytes) else raw)


class Writer:
    def __init__(self, key, title, version, db):
        self.key, self.title, self.version, self.db = key, title, version, db
        self.folder = STAGE / key
        self.folder.mkdir()
        self.counts = Counter()
        self.total = 0
        self.gz_file = (self.folder / 'paragraphs.jsonl.gz').open('wb')
        self.gz = gzip.GzipFile(fileobj=self.gz_file, mode='wb', filename='', mtime=0)
        self.reading = (self.folder / 'reading.txt').open('w', encoding='utf-8')

    def add(self, record):
        payload = json.dumps(record, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        self.gz.write(payload + b'\n')
        self.reading.write(record['text'] + '\n\n')
        self.db.execute('INSERT INTO paragraphs VALUES (?,?,?,?,?,?,?,?,?)',
                        (record['id'], self.key, self.title, record['section_id'], record['section_title'],
                         record['volume_candidate'], record['kind'], record['text'], zlib.compress(payload)))
        self.total += 1
        self.counts[record['kind']] += 1

    def finish(self, inputs, sections, warnings, rules=RULES, role='foundation'):
        self.gz.close()
        self.gz_file.close()
        self.reading.close()
        save(self.folder / 'sections.json', sections)
        prefix = str((OUT / self.key).relative_to(ROOT))
        index = {'book_key': self.key, 'book': self.title, 'source_version': self.version,
                 'rules': rules, 'inputs': inputs, 'sections': len(sections), 'paragraphs': self.total,
                 'kind_counts': dict(self.counts), 'paragraph_file': prefix + '/paragraphs.jsonl.gz',
                 'paragraph_sha256': sha(self.folder / 'paragraphs.jsonl.gz'),
                 'sections_file': prefix + '/sections.json', 'sections_sha256': sha(self.folder / 'sections.json'),
                 'reading_file': prefix + '/reading.txt', 'reading_sha256': sha(self.folder / 'reading.txt'),
                 'warnings': warnings, 'ingestion_role': role,
                 'status': 'normalized_candidates_pending_editorial_review'}
        save(self.folder / 'index.json', index)
        print(f'{self.title}: {self.total}段，{len(sections)}卷/分部及附录', flush=True)
        return index


def build_epub(key, title, book, db):
    conversion = ROOT / 'resources/derived/epub-txt' / f'{book["book_number"]:02d}{title}'
    source = ROOT / book['txt_file']
    assert sha(source) == book['txt_sha256']
    assert sha(ROOT / book['epub_file']) == book['epub_sha256']
    for name, h in book['outputs'].items():
        assert sha(conversion / name) == h, name
    text = source.read_text(encoding='utf-8')
    line_starts = [0] + [m.end() for m in re.finditer('\n', text)]
    source_sections = json.loads((conversion / 'sections.json').read_text())
    groups = defaultdict(list)
    with gzip.open(conversion / 'paragraphs.jsonl.gz', 'rt', encoding='utf-8') as handle:
        for line in handle:
            row = json.loads(line)
            groups[row['section']].append(row)
    defects = defaultdict(list)
    for issue in json.loads((conversion / 'issues.json').read_text()):
        defects[issue['section']].append(issue)
    version = text_sha(RULES + book['txt_sha256'] + book['outputs']['paragraphs.jsonl.gz'] + book['outputs']['sections.json'])[:12]
    writer = Writer(key, title, version, db)
    sections, cursor = [], 0
    for section in source_sections:
        a, b = section['full_txt_char_start'], section['full_txt_char_end']
        assert a == cursor
        section_id = f'{key}-{version}-s{section["section"]:04d}'
        info = {'id': section_id, 'title': section['title'], 'kind': section['section_kind'],
                'volume_candidate': section['volume'], 'volume_part': section['part'],
                'volume_verified': False, 'structural_volume_verified': section['volume'] is not None,
                'source_file': book['txt_file'], 'char_start': a, 'char_end': b,
                'epub_member': section['epub_member'], 'member_sha256': section['member_sha256'],
                'source_issues': defects[section['section']], 'paragraphs': 0}
        sections.append(info)
        mapped = groups[section['section']]
        header_end = mapped[0]['char_start'] if mapped else b
        ranges = [{'char_start': a, 'char_end': header_end, 'kind': 'heading', 'element_paths': [],
                   'editorial_heading': True}] + mapped
        local_cursor = a
        for row in ranges:
            first, last = row['char_start'], row['char_end']
            assert local_cursor <= first < last <= b
            assert not text[local_cursor:first].strip(), 'Omitted source content'
            local_cursor = last
            if row.get('text_sha256'):
                assert text_sha(text[first:last]) == row['text_sha256']
            category = row['kind']
            if category == 'source_heading':
                category = 'heading'
            if category == 'body' and section['section_kind'] != 'volume':
                category = 'table_of_contents' if re.match(r'^卷[一二三四五六七八九十百0-9]', text[first:last]) else section['section_kind']
            if re.fullmatch(r'[（(]?表(?:格)?略[）)]?', text[first:last].strip()):
                category = 'source_gap'
            for start, end, basis in split_ranges(text, first, last, category):
                raw = text[start:end]
                normalized = normalize(raw, category)
                flags = []
                if row.get('editorial_heading'):
                    flags.append('editorial_navigation_heading')
                if basis.endswith('size_split'):
                    flags.append('not_original_paragraph')
                if re.search(r'[\ue000-\uf8ff]', raw):
                    flags.append('private_glyph_requires_review')
                if '\ufffd' in raw:
                    flags.append('source_replacement_character')
                if '⿰' in raw or '⿱' in raw or '〈土周〉' in raw:
                    flags.append('image_glyph_description_requires_review')
                if category not in ('body', 'table_row', 'annotation', 'appendix'):
                    flags.append('not_historical_body')
                if defects[section['section']]:
                    flags.append('section_has_source_issues')
                pid = f'{key}-{version}-p{writer.total + 1:06d}'
                record = {'id': pid, 'book_key': key, 'book': title, 'source_version': version,
                          'section_id': section_id, 'section_title': section['title'],
                          'section_kind': section['section_kind'], 'volume_candidate': section['volume'],
                          'volume_part': section['part'], 'volume_verified': False,
                          'structural_volume_verified': section['volume'] is not None,
                          'kind': category, 'text': normalized, 'boundary_basis': basis,
                          'review_status': 'pending', 'flags': flags,
                          'locator': {'source_file': book['txt_file'], 'source_sha256': book['txt_sha256'],
                                      'original_file': book['epub_file'], 'original_sha256': book['epub_sha256'],
                                      'char_start': start, 'char_end': end,
                                      'line_start': bisect.bisect_right(line_starts, start),
                                      'line_end': bisect.bisect_right(line_starts, max(start, end - 1)),
                                      'raw_excerpt_sha256': text_sha(raw),
                                      'epub_member': section['epub_member'], 'member_sha256': section['member_sha256'],
                                      'element_paths': row['element_paths'],
                                      'conversion_manifest': str((conversion / 'manifest.json').relative_to(ROOT))},
                          'citation': f'《{title}》{section["title"]}，段落 {pid}；EPUB电子本，纸本及异文待核'}
                writer.add(record)
                info['paragraphs'] += 1
        assert not text[local_cursor:b].strip(), 'Omitted section tail'
        cursor = b
    assert cursor == len(text)
    inp = {'source_file': book['epub_file'], 'source_sha256': book['epub_sha256'],
           'mapped_source_file': book['txt_file'], 'mapped_source_sha256': book['txt_sha256'],
           'conversion_manifest': str((conversion / 'manifest.json').relative_to(ROOT))}
    warnings = ['采用当前目录中选定的EPUB转换TXT；按原卷号和分部建索引。',
                '所有非空白字符顺序覆盖一次；卷前资料、标题、注文、附录及缺漏提示均独立标记。',
                '卷目齐全不代表正文齐全；缺表、外部子页、图片字、私用字等见sections.json.source_issues。',
                '结构核验不替代史料校勘；自动段落不标为已录入。']
    role = 'prepared_deferred' if title == '清史稿' else 'foundation'
    return writer.finish([inp], sections, warnings, role=role)


def preserve_tongjian(db):
    # Preserve all existing Tongjian IDs and exact record contents.
    index = json.loads((OUT / 'zizhi-tongjian/index.json').read_text())
    writer = Writer('zizhi-tongjian', '资治通鉴', index['source_version'], db)
    path = ROOT / index['paragraph_file']
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8') as handle:
        for line in handle:
            writer.add(json.loads(line))
    sections = json.loads((ROOT / index['sections_file']).read_text())
    return writer.finish(index['inputs'], sections, index['warnings'], rules=index['rules'], role='chronological_primary')


def rebuild_search(base=OUT):
    """Rebuild only the ignored cache from versioned records, preserving all IDs."""
    catalog_file = base / 'catalog.json'
    catalog_hash = sha(catalog_file)
    catalog = json.loads(catalog_file.read_text())
    with tempfile.TemporaryDirectory(prefix='histree-search-') as tmp:
        target = Path(tmp) / 'search.sqlite'
        with sqlite3.connect(target) as db:
            db.execute('CREATE TABLE paragraphs(id TEXT PRIMARY KEY,book_key TEXT,book TEXT,section_id TEXT,section_title TEXT,volume INTEGER,kind TEXT,text TEXT,record_json BLOB)')
            db.execute('CREATE INDEX book_kind ON paragraphs(book_key,kind)')
            db.execute("CREATE VIRTUAL TABLE search USING fts5(text,content='paragraphs',content_rowid='rowid',tokenize='trigram')")
            total = 0
            for book in catalog['books']:
                path = ROOT / book['paragraph_file']
                assert sha(path) == book['paragraph_sha256'], path
                count = 0
                with gzip.open(path, 'rt', encoding='utf-8') as handle:
                    for line in handle:
                        p = json.loads(line)
                        assert p['book_key'] == book['book_key']
                        payload = json.dumps(p, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                        db.execute('INSERT INTO paragraphs VALUES (?,?,?,?,?,?,?,?,?)',
                                   (p['id'], p['book_key'], p['book'], p['section_id'], p['section_title'],
                                    p['volume_candidate'], p['kind'], p['text'], zlib.compress(payload)))
                        count += 1
                assert count == book['paragraphs']
                total += count
                print(f'{book["book"]}: {count}段已载入', flush=True)
            print('构建全文检索缓存…', flush=True)
            db.execute("INSERT INTO search(search) VALUES('rebuild')")
            db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
            db.executemany('INSERT INTO metadata VALUES (?,?)',
                           [('catalog_sha256', catalog_hash), ('record_encoding', 'zlib-json-v1')])
            assert db.execute('SELECT count(*) FROM paragraphs').fetchone()[0] == total
            assert sha(catalog_file) == catalog_hash, 'Catalog changed during rebuilding'
        db.close()
        # Copy beside the active cache before replacing it, including across filesystems.
        staged = base / 'search.sqlite.build'
        try:
            shutil.copyfile(target, staged)
            staged.replace(base / 'search.sqlite')
        finally:
            staged.unlink(missing_ok=True)
    print(f'检索缓存重建完成：{total}段；原文、分段与ID未改写。', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rebuild-search', action='store_true',
                        help='rebuild only the local SQLite cache from versioned JSONL; use after cloning')
    args = parser.parse_args()
    if args.rebuild_search:
        rebuild_search()
        return
    assert not STAGE.exists(), 'Unfinished staging folder exists; inspect before rebuilding'
    STAGE.mkdir(parents=True)
    db = sqlite3.connect(STAGE / 'search.sqlite')
    db.execute('CREATE TABLE paragraphs(id TEXT PRIMARY KEY,book_key TEXT,book TEXT,section_id TEXT,section_title TEXT,volume INTEGER,kind TEXT,text TEXT,record_json BLOB)')
    db.execute('CREATE INDEX book_kind ON paragraphs(book_key,kind)')
    db.execute("CREATE VIRTUAL TABLE search USING fts5(text,content='paragraphs',content_rowid='rowid',tokenize='trigram')")
    converted = json.loads((ROOT / 'resources/derived/epub-txt/catalog.json').read_text())['books']
    assert len(converted) == 25
    catalog = []
    for (key, title), book in zip(BOOKS, converted):
        assert title == book['book']
        catalog.append(build_epub(key, title, book, db))
    catalog.append(preserve_tongjian(db))
    print('构建全文检索缓存…', flush=True)
    db.execute("INSERT INTO search(search) VALUES('rebuild')")
    db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)')
    save(STAGE / 'catalog.json', {'format_version': RULES, 'record_encoding': 'zlib-json-v1',
                                'books': catalog, 'note': '清史稿仅本地预处理；既定录入范围、已发布来源与通鉴游标不变。'})
    db.execute('INSERT INTO metadata VALUES (?,?)', ('catalog_sha256', sha(STAGE / 'catalog.json')))
    db.execute('INSERT INTO metadata VALUES (?,?)', ('record_encoding', 'zlib-json-v1'))
    db.commit()
    assert db.execute('SELECT count(*) FROM paragraphs').fetchone()[0] == sum(b['paragraphs'] for b in catalog)
    db.close()
    readme = '# 统一史料分段与检索\n\n二十四史及《清史稿》的选定EPUB转换TXT已分段规范化；《资治通鉴》保留原段落ID。清史稿仅预处理，史料录入范围与游标不变。每书只有一套reading.txt、paragraphs.jsonl.gz、sections.json和index.json，SQLite为可重建缓存。\n\n首次克隆或SQLite缓存缺失时，在仓库根目录运行 `python3 scripts/build-history-library.py --rebuild-search`。此命令只重建检索缓存，保留已提交的分段与ID。\n\n[检索和引用说明](../../../docs/HISTORY_LIBRARY.md) · [规范化规则](../../../docs/HISTORY_TEXT_NORMALIZATION.md)\n\n| 书名 | 阅读文本 | 分段记录数 | 索引 |\n| --- | --- | ---: | --- |\n'
    for book in catalog:
        key = book['book_key']
        readme += f'| {book["book"]} | [规范化TXT]({key}/reading.txt) | {book["paragraphs"]} | [卷界与段落]({key}/index.json) |\n'
    (STAGE / 'README.md').write_text(readme, encoding='utf-8')
    previous = OUT.with_name('history-library.previous')
    assert not previous.exists()
    OUT.rename(previous)
    STAGE.rename(OUT)
    print('新分段库已切换；上一版临时保留，待全量校验后清理。', flush=True)


if __name__ == '__main__':
    main()
