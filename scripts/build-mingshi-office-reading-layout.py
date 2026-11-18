"""Build the reviewed coordinates for Ming History volumes 110 through 112.

The selected EPUB/TXT remains immutable. Seven-minister coordinates come from
the separately reviewed source grid, since this EPUB has lost empty/merged
positions. Every rendered fragment still addresses the exact selected text.
"""
import argparse
from collections import defaultdict, deque
import gzip
import hashlib
import json
from pathlib import Path
import re
import zipfile
from build_shiji_layout_loader import load_layout_builder

M = load_layout_builder()
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'apps/api/src/data/mingshi-office-reading-layout.json'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def build():
    manifest = json.loads((ROOT / 'resources/derived/epub-txt/24明史/manifest.json').read_text())
    original = (ROOT / manifest['txt_file']).read_text()
    assert sha(original.encode()) == manifest['txt_sha256']
    assert sha((ROOT / manifest['epub_file']).read_bytes()) == manifest['epub_sha256']
    with gzip.open(ROOT / 'resources/derived/history-library/mingshi/paragraphs.jsonl.gz', 'rt') as f:
        paragraphs = [p for line in f if (p := json.loads(line)).get('volume_candidate') in (110, 111, 112)]
    tables, layouts = {}, {}
    with zipfile.ZipFile(ROOT / manifest['epub_file']) as archive:
        for volume in (110, 111, 112):
            review = json.loads((ROOT / f'content/books/mingshi/vol-{volume}/table-first/structure-review.json').read_text())
            assert review['source_sha256'] == manifest['txt_sha256']
            assert review['epub_sha256'] == manifest['epub_sha256']
            selected = [p for p in paragraphs if p['volume_candidate'] == volume and p['kind'] == 'table_row']
            reviewed = {r['paragraph_id']: r for r in review['rows']}
            assert set(reviewed) == {p['id'] for p in selected}
            member = selected[0]['locator']['epub_member']
            raw = archive.read(member)
            assert sha(raw) == selected[0]['locator']['member_sha256']
            lookup = defaultdict(deque)
            for extracted in M.EPUB.extract(raw, capture_layout=True)[1]:
                if extracted['kind'] == 'table_row':
                    lookup[(tuple(extracted['element_paths']), extracted['text'])].append(extracted)
            tid = f'mingshi-reviewed-office-v{volume}'
            table = {
                'id': tid, 'section_id': selected[0]['section_id'],
                'caption': {110: '宰辅年表二', 111: '七卿年表一', 112: '七卿年表二'}[volume],
                'columns': len(review['column_labels']), 'column_labels': review['column_labels'],
                'epub_member': member, 'rows': [], 'header_paragraph_ids': [],
            }
            tables[tid] = table
            owners = []
            for ri, p in enumerate(selected):
                loc = p['locator']
                content = original[loc['char_start']:loc['char_end']]
                r = reviewed[p['id']]
                assert r['decision'] == 'reviewed'
                assert sha(content.encode()) == loc['raw_excerpt_sha256'] == r['raw_excerpt_sha256']
                key = (tuple(loc['element_paths']), content)
                assert lookup[key], p['id']
                extracted = lookup[key].popleft()
                cells = content.split('\t')
                ranges, cursor = [], 0
                for ci, text in enumerate(cells):
                    ranges.append((ci, cursor, cursor + len(text)))
                    cursor += len(text) + 1
                positions = []
                by_raw = {}
                for position in r['cells']:
                    ci = position['raw_cell_index']
                    assert cells[ci].strip() == position['quote']
                    by_raw[ci] = len(positions)
                    positions.append([position['column'], position['colspan'], 1,
                                      r['role'] in ('header', 'office_header', 'reign_label')])
                fragments, covered = [], set()
                for f in extracted['cell_fragments']:
                    left, right = f['start'], f['end']
                    if not content[left:right].strip():
                        continue
                    matches = [ci for ci, a, b in ranges if left < b and right > a and ci in by_raw]
                    assert len(matches) == 1, (p['id'], f, matches)
                    fragments.append([by_raw[matches[0]], left, right])
                    covered.update(range(left, right))
                assert all(c.isspace() or i in covered for i, c in enumerate(content)), p['id']
                table['rows'].append(positions)
                layout = {'content_sha256': loc['raw_excerpt_sha256'], 'table_id': tid,
                          'row_index': ri, 'fragments': fragments}
                y = r['year_context']
                if y and r['role'] == 'entry':
                    layout['calendar_year'] = y['year']
                    layout['calendar_note'] = '公元年为原表年号的对照年；月日保留原历，年底事项可能跨入下一公元年。'
                    issue = next((x for x in review['issues'] if x['paragraph_id'] == y['source_paragraph_id']), None)
                    if issue:
                        layout['calendar_note'] += f"原栏干支作{issue['source']}，按年号换算应为{issue['expected']}；原字保留。"
                layouts[p['id']] = layout
                if r['role'] in ('header', 'office_header') and len(table['header_paragraph_ids']) < (1 if volume == 110 else 2):
                    table['header_paragraph_ids'].append(p['id'])
                if r['role'] == 'entry' and y:
                    date_cells = [index for index, cell in enumerate(positions) if cell[0] == 0]
                    if date_cells:
                        assert len(date_cells) == 1
                        ci = date_cells[0]
                        spans = [f for f in fragments if f[0] == ci]
                        assert spans
                        owners.append((ri, p['id'], ci, min(f[1] for f in spans), max(f[2] for f in spans)))
            # Keep a year column visible when pagination starts in the middle of
            # its source group. Empty source placeholders never become cells.
            for oi, (start, pid, ci, left, right) in enumerate(owners):
                end = owners[oi + 1][0] if oi + 1 < len(owners) else len(selected)
                breaks = [j for j in range(start + 1, end) if reviewed[selected[j]['id']]['role'] == 'reign_label']
                if breaks:
                    end = breaks[0]
                table['rows'][start][ci][2] = end - start
                for ri in range(start + 1, end):
                    assert all(cell[0] != 0 for cell in table['rows'][ri])
                    layouts[selected[ri]['id']]['context_cells'] = [
                        {'column': 0, 'colspan': 1, 'rowspan': end - ri,
                         'paragraph_id': pid, 'start': left, 'end': right}
                    ]
    assert len(layouts) == 1826
    return {
        'format_version': 1, 'book_key': 'mingshi', 'source_version': '2f603db3d81e',
        'source_sha256': manifest['txt_sha256'], 'epub_sha256': manifest['epub_sha256'],
        'offset_unit': 'unicode-codepoints', 'divisions': [], 'chapters': [],
        'tables': tables, 'paragraphs': layouts, 'annotations': {},
        'calendar_groups': {}, 'calendar_paragraphs': {},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = build()
    value = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    if args.check:
        assert OUTPUT.read_bytes() == value
    else:
        OUTPUT.write_bytes(value)
    print(json.dumps({'tables': len(data['tables']), 'rows': len(data['paragraphs'])}))
