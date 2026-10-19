#!/usr/bin/env python3
"""Prepare lossless DB reading records from the existing catalog; never change ingestion ledgers."""
import argparse
from collections import defaultdict
from functools import lru_cache
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote
import source_texts

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'resources/derived/history-library/catalog.json'
SCHEMA = ROOT / 'apps/api/mysql/migrations/20261019_library.sql'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


spec = importlib.util.spec_from_file_location('history_search', ROOT / 'scripts/search-history-library.py')
search = importlib.util.module_from_spec(spec)
spec.loader.exec_module(search)


@lru_cache(maxsize=400)
def asset_text(filename, checksum):
    path = search.resolve_source(filename, checksum)
    return path.read_bytes().decode('utf-8')


def prepare(output, selected=None):
    output.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(CATALOG.read_text())
    books = [b for b in catalog['books'] if b.get('ingestion_role') in ('foundation', 'chronological_primary', 'chronological_primary_continuation') and (not selected or b['book_key'] in selected)]
    if selected and set(selected) != {b['book_key'] for b in books}:
        raise ValueError('Unknown or out-of-scope book')
    plan = {'format_version': 1, 'catalog_sha256': sha(CATALOG.read_bytes()), 'schema_sha256': sha(SCHEMA.read_bytes()), 'books': []}
    by_id = {}
    by_hash = defaultdict(list)
    for order, book in enumerate(books):
        for field in ('paragraph', 'sections'):
            if sha((ROOT / book[field + '_file']).read_bytes()) != book[field + '_sha256']:
                raise ValueError('Library artifact hash changed: ' + book['book_key'])
        sections = json.loads((ROOT / book['sections_file']).read_text())
        section_ids = {s['id'] for s in sections}
        path = output / (book['book_key'] + '.jsonl.gz')
        counts = defaultdict(int)
        raw_digest = hashlib.sha256()
        seen_assets = set()
        ordinal = 0
        content_digest = hashlib.sha256()
        with gzip.open(path, 'wt', encoding='utf-8', newline='') as target:
            def emit(table, row):
                line = canonical({'table': table, 'row': row}) + '\n'
                raw_digest.update(line.encode())
                target.write(line)
                counts[table] += 1
            for i, section in enumerate(sections):
                emit('library_section', dict(id=section['id'], book_key=book['book_key'], sort_order=i,
                    title=section['title'][:255], volume=section.get('volume_candidate'), kind=section['kind'],
                    has_issues=int(bool(section.get('source_issues'))), metadata=canonical({'source_issues': section.get('source_issues', []), 'volume_verified': section.get('volume_verified', False)})))
            with gzip.open(ROOT / book['paragraph_file'], 'rt', encoding='utf-8') as source:
                for line in source:
                    p = json.loads(line)
                    if p['section_id'] not in section_ids:
                        raise ValueError('Paragraph section missing')
                    if 'editorial_navigation_heading' in p.get('flags', []):
                        continue
                    loc = p['locator']
                    text = asset_text(loc['source_file'], loc['source_sha256'])[loc['char_start']:loc['char_end']]
                    checksum = sha(text.encode())
                    if checksum != loc['raw_excerpt_sha256']:
                        raise ValueError('Original excerpt hash mismatch: ' + p['id'])
                    aid = sha((loc['source_file'] + '\0' + loc['source_sha256']).encode())
                    if aid not in seen_assets:
                        emit('library_asset', dict(id=aid, source_file=loc['source_file'], source_sha256=loc['source_sha256']))
                        seen_assets.add(aid)
                    row = dict(id=p['id'], book_key=book['book_key'], section_id=p['section_id'], ordinal=ordinal,
                               kind=p['kind'], content=text, content_sha256=checksum, asset_id=aid,
                               char_start=loc['char_start'], char_end=loc['char_end'], flags=canonical(p.get('flags', [])))
                    emit('library_paragraph', row)
                    content_digest.update((row['id'] + '\0' + checksum + '\n').encode())
                    by_id[p['id']] = checksum
                    by_hash[checksum].append(p['id'])
                    ordinal += 1
        plan['books'].append(dict(book_key=book['book_key'], title=book['book'], source_version=book['source_version'], sort_order=order,
            section_count=len(sections), paragraph_count=ordinal, dataset_sha256=raw_digest.hexdigest(),
            content_digest=content_digest.hexdigest(), file=path.name, file_sha256=sha(path.read_bytes()), counts=dict(counts),
            metadata=canonical({'inputs': book['inputs'], 'paragraph_sha256': book['paragraph_sha256'], 'sections_sha256': book['sections_sha256']})))
        asset_text.cache_clear()
        print(canonical({'prepared': book['book'], 'sections': len(sections), 'paragraphs': ordinal}), flush=True)
    source_rows = source_texts.published_texts([])
    # Identical prose can occur in several books. A hash alone cannot establish book identity.
    source_titles = {}
    for path in (ROOT / 'content').rglob('content-batch.json'):
        audits = [json.loads(p.read_text()) for name in ('publication-mysql.json', 'publication.json') if (p := path.parent / name).exists()]
        if not any(a.get('verified') and a.get('batch_sha256') == sha(path.read_bytes()) for a in audits):
            continue
        batch = json.loads(path.read_text())
        ids = json.loads((path.parent / 'sql/key-map.json').read_text())
        source_titles.update({ids[s['key']]: s['title'] for s in batch['sources']})
    for path in (ROOT / 'content/revisions').rglob('plan.json'):
        audit = path.parent / 'publication-mysql.json'
        if audit.exists():
            proof = json.loads(audit.read_text())
            if proof.get('verified') and proof.get('plan_sha256') == sha(path.read_bytes()):
                source_titles.update({s['id']: s['title'] for s in json.loads(path.read_text()).get('sources', []) if s.get('id')})
    book_names = sorted(books, key=lambda b: len(b['book']), reverse=True)
    links = []
    unmatched = []
    for row in source_rows:
        title = source_titles.get(row['source_id'], '').replace('《', '').replace('》', '')
        source_book = next((b['book_key'] for b in book_names if title.startswith(b['book'])), None)
        candidates = re.findall(r'[a-z][a-z0-9-]*-p\d{6}', unquote(row['archive_url']))
        matched = [pid for pid in candidates if by_id.get(pid) == row['content_sha256']]
        if not matched and len(by_hash.get(row['content_sha256'], [])) == 1:
            matched = by_hash[row['content_sha256']]
        matched = [pid for pid in matched if source_book and pid.startswith(source_book + '-')]
        if len(set(matched)) == 1:
            links.append(dict(source_id=row['source_id'], archive_url_sha256=row['archive_url_sha256'], snapshot_sha256=row['content_sha256'], paragraph_id=matched[0]))
        else:
            unmatched.append({'source_id': row['source_id'], 'reason': 'No unique identical paragraph in this catalog version'})
    (output / 'source-links.json').write_text(canonical(links) + '\n')
    plan.update(source_links_file='source-links.json', source_links_sha256=sha((output / 'source-links.json').read_bytes()), source_links=len(links), unmatched_sources=unmatched)
    (output / 'manifest.json').write_text(canonical(plan) + '\n')
    print(canonical({'books': len(books), 'paragraphs': sum(b['paragraph_count'] for b in plan['books']), 'source_links': len(links), 'unmatched_sources': len(unmatched), 'database_writes': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--book', action='append')
    args = parser.parse_args()
    prepare(args.output, args.book)
