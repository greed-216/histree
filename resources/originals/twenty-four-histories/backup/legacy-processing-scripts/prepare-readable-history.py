"""Build reversible reading copies; never modify sources or publication batches.

Run with the bundled Python (pypdf). PDF bookmarks are sections, NOT volume IDs.
Kanripo JUAN is preserved literally. Blocks are reading aids, not edited paragraphs.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'resources/derived/readable'
PDF_BOOKS = {'jiuwudaishi': '18旧五代史', 'xinwudaishi': '19新五代史',
             'jiutangshu': '16旧唐书'}
KANRIPO_BOOKS = {'shiguochunqiu': 'KR2i0021', 'wuyue-beishi': 'KR2i0019',
                 'shu-taowu': 'KR2i0016', 'beimeng-suoyan': 'KR3l0023',
                 'wudai-huiyao': 'KR2m0003', 'nantangshu-ma': 'KR2i0017',
                 'nantangshu-lu': 'KR2i0018'}
VERSION = 'readable-v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def compact(text):
    # Preserve spaces between Latin words/digits; only collapse CJK layout spaces.
    text = re.sub(r'\s+', ' ', text).strip()
    cjk = r'\u3400-\u9fff\U00020000-\U000323af'
    text = re.sub(fr'(?<=[{cjk}]) +(?=[{cjk}，。；：！？、（）《》“”])', '', text)
    return re.sub(fr'(?<=[，。；：！？、（）《》“”]) +(?=[{cjk}])', '', text)


def pdf_lines(text, title, page, total):
    rows, excluded = [], []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        # Exact matching and source position prevent deleting prose mentions.
        if n <= 3 and (line == title or line == f'{page}/{total}'):
            excluded.append({'line': n, 'raw': raw, 'reason': 'running_header'})
        else:
            rows.append({'line': n, 'raw': raw})
    return rows, excluded


def kanripo_lines(text):
    metadata, rows, excluded = {}, [], []
    leaf = None
    for n, raw in enumerate(text.splitlines(), 1):
        if raw.startswith('#'):
            if raw.startswith('#+PROPERTY: '):
                key, _, value = raw[12:].partition(' ')
                metadata[key] = value.strip()
            elif raw.startswith('#+TITLE: '):
                metadata['TITLE'] = raw[9:].strip()
            excluded.append({'line': n, 'raw': raw, 'reason': 'metadata'})
            continue
        match = re.fullmatch(r'<pb:([^>]+)>¶?\s*', raw)
        if match:
            leaf = match[1]
            excluded.append({'line': n, 'raw': raw, 'reason': 'leaf_marker'})
            continue
        rows.append({'line': n, 'raw': raw, 'leaf': leaf})
    return metadata, rows, excluded


def make_blocks(rows, mode, section=None):
    """Remove mechanical wraps; preserve blank lines/indented notes/headings.

    PDF trailing double spaces are this edition's paragraph-layout signal.
    Kanripo indentation is ambiguous: preserve it as an indented block, not a note.
    A size break is explicitly marked and never treated as a natural paragraph.
    """
    blocks, pending = [], []
    pending_kind = 'reading_block'
    def flush(boundary):
        nonlocal pending
        if not pending:
            return
        joined = ''.join(r['raw'].strip().removesuffix('¶') for r in pending)
        # Slash within a Chinese double-line gloss is layout; keep in this first
        # version because a slash can also represent a genuine editorial variant.
        clean = compact(joined)
        if clean:
            blocks.append({'kind': pending_kind, 'boundary': boundary,
                           'section': section, 'text': clean, 'source_spans': pending})
        pending = []
    for row in rows:
        raw = row['raw']
        line = raw.strip().removesuffix('¶')
        if not line:
            flush('blank_line')
            continue
        if mode == 'kanripo':
            kind = 'indented_block' if raw.startswith((' ', '\u3000', '\t')) else 'reading_block'
            if len(line) <= 8 and not re.search(r'[，。；：！？（）()]', line):
                flush('short_line')
                pending_kind = 'short_line_block'
                pending.append(row)
                flush('short_line')
                continue
            # Only use explicit formatting, never infer paragraph starts from names.
            if pending and kind != pending_kind:
                flush('indent_change')
            pending_kind = kind
        pending.append(row)
        if mode == 'pdf' and raw.endswith('  '):
            flush('layout_paragraph_candidate')
        elif sum(len(r['raw']) for r in pending) >= 800:
            flush('size_limit')
    flush('section_end')
    return blocks


def emit_unit(book_dir, slug, title, blocks):
    path = book_dir / (slug + '.jsonl')
    txt = book_dir / (slug + '.txt')
    with path.open('w') as f:
        for i, block in enumerate(blocks, 1):
            block['id'] = f'{book_dir.name}-{VERSION}-{slug}-b{i:05d}'
            # Require exact recovery of every non-whitespace source character.
            raw = ''.join(r['raw'].strip().removesuffix('¶') for r in block['source_spans'])
            assert re.sub(r'\s', '', raw) == re.sub(r'\s', '', block['text'])
            f.write(json.dumps(block, ensure_ascii=False) + '\n')
    display = blocks[1:] if blocks and blocks[0]['text'] == title else blocks
    txt.write_text(title + '\n\n' + '\n\n'.join(b['text'] for b in display) + '\n')
    return {'title': title, 'blocks': len(blocks), 'text_file': relative(txt),
            'mapped_file': relative(path), 'text_sha256': digest(txt),
            'mapped_sha256': digest(path)}


def pdf_book(key, stem):
    from pypdf import PdfReader
    source = ROOT / 'resources/originals/twenty-four-histories' / (stem + '.pdf')
    before = digest(source)
    reader = PdfReader(source)
    book_dir = OUT / key
    book_dir.mkdir(parents=True, exist_ok=True)
    existing = ROOT / 'resources/derived/twenty-four-histories' / (stem + '.jsonl')
    cached_index = book_dir / 'index.json'
    cached = book_dir / 'raw-pages.jsonl'
    if not existing.exists() and cached_index.exists() and cached.exists():
        old = json.loads(cached_index.read_text())
        if old.get('source_sha256') == before and old.get('raw_text_sha256') == digest(cached):
            existing = cached
    if existing.exists():
        pages = [json.loads(line) for line in existing.open()]
        raw_source = existing
    else:
        raw_source = book_dir / 'raw-pages.jsonl'
        # New extraction stays under this isolated output, not the old evidence tree.
        pages = []
        with raw_source.open('w') as f:
            for i, page in enumerate(reader.pages, 1):
                row = {'pdf_page': i, 'text': page.extract_text() or ''}
                pages.append(row)
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
                if i % 1000 == 0:
                    print(f'{key}: extracted {i}/{len(reader.pages)}', flush=True)
    assert [p['pdf_page'] for p in pages] == list(range(1, len(reader.pages) + 1))
    raw_before = digest(raw_source)
    starts = {}
    outline_entries = []
    def visit(items):
        for item in items:
            if isinstance(item, list):
                visit(item)
            else:
                title = compact(str(item.get('/Title', '')))
                if title:
                    page = reader.get_destination_page_number(item) + 1
                    outline_entries.append({'title': title, 'pdf_page': page})
                    starts.setdefault(page, []).append(title)
    visit(reader.outline)
    starts.setdefault(1, [stem[2:]])
    ordered = sorted(starts)
    units, excluded, warnings = [], [], []
    if not reader.outline:
        warnings.append('PDF没有书签；只有全书导航，不能推定卷界。')
    for i, first in enumerate(ordered):
        end = ordered[i + 1] - 1 if i + 1 < len(ordered) else len(pages)
        title = ' / '.join(starts[first])
        rows = []
        for page in pages[first - 1:end]:
            parsed, removed = pdf_lines(page['text'], stem[2:], page['pdf_page'], len(pages))
            for row in parsed:
                row.update(pdf_page=page['pdf_page'], source_file=relative(raw_source))
            rows.extend(parsed)
            excluded.extend(dict(r, pdf_page=page['pdf_page']) for r in removed)
        blocks = make_blocks(rows, 'pdf', title)
        unit = emit_unit(book_dir, f'section-{i+1:03d}', title, blocks)
        unit.update(pdf_page_start=first, pdf_page_end=end,
                    boundary_basis='PDF书签页；同页书签合组，不推定史书卷号')
        units.append(unit)
    assert digest(source) == before and digest(raw_source) == raw_before
    index = {'format_version': VERSION, 'book': stem[2:], 'kind': 'pdf_bookmark_sections',
             'source_file': relative(source), 'source_sha256': before,
             'raw_text_file': relative(raw_source), 'raw_text_sha256': raw_before,
             'pdf_pages': len(pages), 'outline_entries': outline_entries,
             'warnings': warnings + ['书签不等于完整卷目；PDF抽取字序、缺字及小注仍需人工校核。'],
             'units': units, 'excluded_lines_file': relative(book_dir / 'excluded.json')}
    write_json(book_dir / 'excluded.json', excluded)
    write_json(book_dir / 'index.json', index)
    return index


def kanripo_book(key, code):
    base = ROOT / 'resources/originals/kanripo' / code
    book_dir = OUT / key
    book_dir.mkdir(parents=True, exist_ok=True)
    units = []
    for source in sorted(base.glob(code + '_*.txt')):
        before = digest(source)
        metadata, rows, excluded = kanripo_lines(source.read_text())
        for row in rows:
            row['source_file'] = relative(source)
        section = metadata.get('JUAN', source.stem)
        unit = emit_unit(book_dir, source.stem, metadata.get('TITLE', code) + ' · ' + section,
                         make_blocks(rows, 'kanripo', section))
        unit.update(juan=section, edition=metadata.get('BASEEDITION'),
                    source_file=relative(source), source_sha256=before,
                    metadata=metadata, boundary_basis='上游分卷文件与JUAN字段')
        unit['excluded_lines_file'] = relative(book_dir / (source.stem + '-excluded.json'))
        write_json(book_dir / (source.stem + '-excluded.json'), excluded)
        units.append(unit)
        assert digest(source) == before
    assert units, f'No sources: {base}'
    index = {'format_version': VERSION, 'book': units[0]['metadata'].get('TITLE', code),
             'kind': 'kanripo_juan_files', 'units': units,
             'warnings': ['阅读块不是自然段；缩进块不自动认作注文；双行小注斜杠保留，未加标点。']}
    write_json(book_dir / 'index.json', index)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--books', nargs='+', choices=sorted(PDF_BOOKS.keys() | KANRIPO_BOOKS.keys()),
                        default=list(PDF_BOOKS) + list(KANRIPO_BOOKS))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for key in args.books:
        index = pdf_book(key, PDF_BOOKS[key]) if key in PDF_BOOKS else kanripo_book(key, KANRIPO_BOOKS[key])
        print(f'{key}: {len(index["units"])} navigation units', flush=True)
    # Include every built book so a selective rerun does not remove other navigation.
    paths = sorted(OUT.glob('*/index.json'))
    overview = '# 史料阅读副本\n\n原件与既有引文保留；阅读块尚未经过史料分段校核。\n\n'
    for p in paths:
        index = json.loads(p.read_text())
        overview += f'- [{index["book"]}]({p.parent.name}/index.json)（{len(index["units"])} 个导航单元）\n'
    overview += '\n规则、局限与引用方式见 [处理说明](../../../docs/HISTORY_TEXT_NORMALIZATION.md)。\n'
    (OUT / 'README.md').write_text(overview)


if __name__ == '__main__':
    main()
