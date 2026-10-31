"""Prepare continuous source packets and compile curated facts; offline, no publishing.

prepare discovers a book through the catalog and exports exact source snapshots.
build consumes curation.json, produces the existing book-batch format and a review
page. Dates, identities and interpretations must be supplied by the curator.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'resources/derived/history-library/catalog.json'
GROUPS = ('people', 'events', 'person_events', 'person_relationships')
TABLES = dict(zip(GROUPS, ('person', 'event', 'person_event', 'person_relationship')))


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def source_key(book_key, paragraph_id):
    return ('tongjian-' if book_key == 'zizhi-tongjian' else book_key + '-') + paragraph_id


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def records(book_key):
    book = next(b for b in read(CATALOG)['books'] if b['book_key'] == book_key)
    with gzip.open(ROOT / book['paragraph_file'], 'rt', encoding='utf-8') as stream:
        return book, [json.loads(line) for line in stream]


def check_range(packet):
    book, library = records(packet['book_key'])
    assert packet['paragraphs'], 'Empty primary source range'
    ids = [p['id'] for p in packet['paragraphs']]
    positions = {p['id']: i for i, p in enumerate(library)}
    start = positions[ids[0]]
    assert ids == [p['id'] for p in library[start:start + len(ids)]], 'Non-continuous source range'
    assert packet['source_version'] == book['source_version'], 'Source version changed'
    assert packet['paragraphs'] == library[start:start + len(ids)], 'Packet differs from library'
    assert all(p['book_key'] == packet['book_key'] and p['volume_candidate'] == packet['volume']
               for p in packet['paragraphs']), 'Primary source book/volume differs from packet'
    following = library[start + len(ids)]['id'] if start + len(ids) < len(library) else None
    assert packet['next_paragraph'] == following, 'Incorrect next paragraph'
    return book


def guard(directory):
    assert not any((directory / name).exists() for name in ('publication.json', 'publication-mysql.json')), 'Published batches are immutable'


def supplementary_records(packet):
    """Verify optional corroborating records without advancing another book."""
    result = packet.get('supplementary_paragraphs', [])
    primary_ids = {p['id'] for p in packet['paragraphs']}
    assert len({p['id'] for p in result}) == len(result), 'Duplicate supplementary record'
    cache = {}
    for p in result:
        assert p['id'] not in primary_ids, 'Supplement duplicates primary range'
        if p['book_key'] not in cache:
            book, library = records(p['book_key'])
            cache[p['book_key']] = book, {r['id']: r for r in library}
        book, library = cache[p['book_key']]
        assert p['source_version'] == book['source_version'] and library.get(p['id']) == p, 'Supplement differs from library'
    return result


def add_supplement(args):
    """Export a reviewed auxiliary record; fixed snapshot binding is still required."""
    directory = args.directory.resolve()
    guard(directory)
    packet = read(directory / 'packet.json')
    check_range(packet)
    supplementary_records(packet)
    _, library = records(args.book)
    p = next(r for r in library if r['id'] == args.id)
    assert p['id'] not in {r['id'] for r in packet['paragraphs'] + packet.get('supplementary_paragraphs', [])}, 'Record already included'
    spec = importlib.util.spec_from_file_location('history_search', ROOT / 'scripts/search-history-library.py')
    search = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(search)
    loc = p['locator']
    source = search.resolve_source(loc['source_file'], loc['source_sha256'])
    search.resolve_source(loc['original_file'], loc['original_sha256'])
    if loc.get('source_map_file'):
        search.resolve_source(loc['source_map_file'], loc['source_map_sha256'])
    raw = source.read_bytes().decode('utf-8')[loc['char_start']:loc['char_end']].encode('utf-8')
    assert sha(raw) == loc['raw_excerpt_sha256'], 'Supplement snapshot differs'
    folder = directory / 'sources' / p['id']
    assert not folder.exists(), 'Snapshot already exists'
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    m = dict(key=source_key(p['book_key'], p['id']), file=p['id'] + '/source.txt', sha256=sha(raw),
             paragraph_id=p['id'], upstream_locator=loc, source_title=args.title,
             url=f'https://github.com/greed-216/histree/blob/{commit}/{quote(loc["source_file"])}',
             snapshot_status='local_draft_not_committed', purpose='scoped_identity_or_textual_check')
    folder.mkdir(parents=True)
    (folder / 'source.txt').write_bytes(raw)
    write(folder / 'paragraph.json', p)
    manifest = read(directory / 'sources/manifest.json')
    manifest.append(m)
    packet.setdefault('supplementary_paragraphs', []).append(p)
    write(directory / 'sources/manifest.json', manifest)
    write(directory / 'packet.json', packet)
    print(json.dumps(dict(added=p['id'], source_key=m['key'], needs_reviewed_evidence_and_fixed_archive=True), ensure_ascii=False))


def people_registry(exclude=None):
    candidates = {}
    for path in sorted((ROOT / 'content').rglob('content-batch.json')):
        if exclude and path.parent.resolve() == exclude.resolve():
            continue
        for row in read(path)['people']:
            candidates[row['key']] = dict(row=row, batch=str(path.relative_to(ROOT)))
    # Source-scoped splits retain the original batches. Their verified new
    # people must remain reusable without rebuilding those immutable archives.
    for path in sorted((ROOT / 'content/revisions').glob('*/plan.json')):
        plan = read(path)
        if plan.get('kind') not in ('split_cross_era_homonyms', 'split_source_scoped_homonyms', 'reviewed_history_correction'):
            continue
        audit_path = path.parent / 'publication-mysql.json'
        if not audit_path.exists():
            continue
        audit = read(audit_path)
        if not (audit.get('verified') and audit.get('anonymous_readback_verified')
                and audit.get('plan_sha256') == sha(path.read_bytes())):
            continue
        people = ([dict(new=p) for p in plan.get('new_people', [])]
                  if plan.get('kind') == 'reviewed_history_correction' else plan['people'])
        for person in people:
            new = person['new']
            assert new in audit['new_people'], 'Revision person differs from verified publication'
            assert new['status'] == 'published', 'Revision person is not published'
            namespace=uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/greed-216/histree/content')
            assert new['id']==str(uuid.uuid5(namespace,new['key'])), 'Revision person stable UUID differs'
            row = {k: v for k, v in new.items() if k != 'id'}
            prior = candidates.get(row['key'])
            if prior:
                assert dict(prior['row'], status='draft') == dict(row, status='draft'), 'Revision person conflicts with batch'
            else:
                candidates[row['key']] = dict(row=row, batch=str(path.relative_to(ROOT)))
    # Historical batches retain their original fields. Reuse the current values
    # from independently verified field revisions without rewriting those files.
    revisions = defaultdict(list)
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/greed-216/histree/content')
    by_id = {str(uuid.uuid5(namespace, key)): key for key in candidates}
    revision_files = list((ROOT / 'content/revisions').glob('*/plan.json')) + list((ROOT / 'content/revisions').glob('*/aliases.json'))
    for path in sorted(revision_files):
        audit_path = path.parent / 'publication-mysql.json'
        # Verified pre-MySQL alias append archives remain the historical reuse
        # baseline after migration. This never authorizes a database write.
        if not audit_path.exists() and path.name == 'aliases.json':
            audit_path = path.parent / 'publication.json'
        if not audit_path.exists():
            continue
        audit = read(audit_path)
        plan = read(path)
        verified = (audit.get('verified') and audit.get('anonymous_readback_verified')
                    and audit.get('plan_sha256') == sha(path.read_bytes()))
        # revise-person-aliases.py records the same guarded, anonymously read
        # back change with revision_sha256 and a fixed method identifier.
        alias_verified = (audit.get('verified')
                          and audit.get('revision_sha256') == sha(path.read_bytes())
                          and audit.get('method') == 'Guarded alias merge; published claim checks; anonymous readback')
        updates = plan.get('updates', [])
        if alias_verified:
            people = plan.get('people', [])
            assert people and audit.get('count') == len(people), 'Alias revision count differs'
            assert len({p['id'] for p in people}) == len(people), 'Duplicate alias revision person'
            for person in people:
                key = person.get('key', by_id.get(person['id']))
                if key:
                    assert person['id'] == str(uuid.uuid5(namespace, key)), 'Alias revision key differs'
                assert isinstance(person['before'], list) and isinstance(person['after'], list), 'Invalid alias lists'
                assert set(person['before']) <= set(person['after']), 'Alias revision removes existing aliases'
                assert person.get('claim_ids'), 'Alias revision lacks evidence claims'
            expected = [dict(table='person', id=p['id'], before=dict(aliases=p['before']),
                             after=dict(aliases=p['after'])) for p in people]
            if updates:
                assert len(updates) == len(expected), 'Alias revision updates differ'
                for update, person, change in zip(updates, people, expected):
                    assert set(update) <= set(change) | {'key', 'name'}, 'Alias revision updates differ'
                    assert all(update.get(k) == value for k, value in change.items()), 'Alias revision updates differ'
                    key = person.get('key', by_id.get(person['id']))
                    assert update.get('key', key) == key, 'Alias revision key differs'
                    assert update.get('name', person['name']) == person['name'], 'Alias revision name differs'
            updates = expected
        if not (verified or alias_verified):
            continue
        for update in updates:
            if update.get('table') != 'person' or update.get('id') not in by_id:
                continue
            key = by_id[update['id']]
            for field, value in update['after'].items():
                if field not in ('name', 'aliases', 'era', 'birth_year', 'death_year',
                                 'description', 'biography'):
                    continue
                assert field in update['before'], 'Revision lacks old field value'
                revisions[key, field].append((update['before'][field], value))
    for (key, field), chain in revisions.items():
        # Folder names do not establish execution order. Connect verified old/new
        # values; reject divergent branches and cycles instead of guessing.
        original_chain = chain
        changes = []
        for pair in chain:
            if pair[0] != pair[1] and pair not in changes:
                changes.append(pair)  # repeated byte-bound receipts for the same append
        ordered = []
        while changes:
            starts = [pair for pair in changes if not any(other[1] == pair[0] for other in changes)]
            assert len(starts) == 1, ('Person revision chain is discontinuous (ambiguous or cyclic)', key, field)
            first = starts[0]
            if ordered:
                assert ordered[-1][1] == first[0], ('Person revision chain is discontinuous', key, field)
            ordered.append(first)
            changes.remove(first)
        assert ordered or all(pair[0] == original_chain[0][0] for pair in original_chain), 'Conflicting no-op revisions'
        chain = ordered or original_chain
        assert all(any(value == point for edge in chain for point in edge) for pair in original_chain for value in pair), 'No-op revision conflicts with chain'
        row = dict(candidates[key]['row'])
        matches_history = any(row.get(field) == value for pair in chain for value in pair)
        # Some frozen batches predate the first verified alias append. A strict
        # subset is compatible only for monotonic alias lists, never other fields.
        alias_prefix = (field == 'aliases' and isinstance(row.get(field), list)
                        and isinstance(chain[0][0], list)
                        and set(row[field]) <= set(chain[0][0]))
        assert matches_history or alias_prefix, 'Revision conflicts with person batch'
        row[field] = chain[-1][1]
        candidates[key] = dict(candidates[key], row=row)
    # Some seed-era published people predate local content batches. A scoped,
    # hash-bound MySQL read snapshot can supply their immutable reuse fields;
    # the publisher still checks these fields against the live database.
    baseline_path = exclude / 'identity-baseline.json' if exclude else None
    if baseline_path and baseline_path.exists():
        baseline = read(baseline_path)
        assert baseline['kind'] == 'mysql_seed_person_reuse', 'Invalid identity baseline'
        snapshot_path = (ROOT / baseline['snapshot']).resolve()
        assert snapshot_path.is_relative_to(ROOT.resolve()), 'Identity snapshot outside repository'
        assert sha(snapshot_path.read_bytes()) == baseline['snapshot_sha256'], 'Identity snapshot changed'
        snapshot = {p['id']: p for p in read(snapshot_path)['person']}
        fields = ('name', 'aliases', 'era', 'birth_year', 'death_year', 'description', 'biography')
        for row in baseline['people']:
            person_id = str(uuid.uuid5(namespace, row['key']))
            actual = snapshot[person_id]
            assert actual['status'] == 'published', 'Identity baseline person is not published'
            assert all(row[field] == actual[field] for field in fields), 'Identity baseline fields changed'
            prior = candidates.get(row['key'])
            assert not prior or dict(prior['row'], status='draft') == dict(row, status='draft'), 'Identity baseline conflicts with batch'
            candidates[row['key']] = dict(row=row, batch=str(baseline_path.relative_to(ROOT)))
    return list(candidates.values())


def prepare(args):
    out = args.out.resolve()
    assert not out.exists(), 'Choose a new batch directory; existing files are preserved'
    book, library = records(args.book)
    volume = [p for p in library if p.get('volume_candidate') == args.volume]
    assert volume, 'Volume not found'
    start = next(i for i, p in enumerate(volume) if p['id'] == args.start) if args.start else 0
    selected = volume[start:start + args.count]
    assert len(selected) == args.count and args.count > 0, 'Requested range exceeds volume'
    offset = next(i for i, p in enumerate(library) if p['id'] == selected[0]['id'])
    assert selected == library[offset:offset + args.count], 'Volume is not a continuous range'
    # Reuse the source resolver's archive/hash rules, without requiring a search cache.
    spec = importlib.util.spec_from_file_location('history_search', ROOT / 'scripts/search-history-library.py')
    search = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(search)
    commit = subprocess.check_output(['git', 'rev-parse', '--verify',
                                     getattr(args, 'upstream_commit', None) or 'HEAD'], cwd=ROOT, text=True).strip()
    manifests = []
    exports = []
    for p in selected:
        loc = p['locator']
        source = search.resolve_source(loc['source_file'], loc['source_sha256'])
        search.resolve_source(loc['original_file'], loc['original_sha256'])
        if loc.get('source_map_file'):
            assert sha((ROOT / loc['source_map_file']).read_bytes()) == loc['source_map_sha256']
        raw = source.read_bytes().decode('utf-8')[loc['char_start']:loc['char_end']].encode('utf-8')
        assert sha(raw) == loc['raw_excerpt_sha256'], p['id']
        upstream = str(source.relative_to(ROOT))
        committed = subprocess.check_output(['git', 'show', f'{commit}:{upstream}'], cwd=ROOT)
        assert sha(committed) == loc['source_sha256'], 'Upstream source is not archived in HEAD'
        key = source_key(args.book, p['id'])
        manifests.append(dict(key=key, file=p['id'] + '/source.txt', sha256=sha(raw),
                              paragraph_id=p['id'], upstream_locator=loc,
                              url=f'https://github.com/greed-216/histree/blob/{commit}/{quote(upstream)}',
                              upstream_commit=commit, snapshot_status='local_draft_not_committed'))
        exports.append(raw)
    # All source checks happen before creating the directory.
    for p, raw in zip(selected, exports):
        folder = out / 'sources' / p['id']
        folder.mkdir(parents=True)
        (folder / 'source.txt').write_bytes(raw)
        write(folder / 'paragraph.json', p)
    packet = dict(book_key=args.book, book=book['book'], volume=args.volume,
                  source_version=book['source_version'], paragraphs=selected,
                  next_paragraph=library[offset + args.count]['id'] if offset + args.count < len(library) else None,
                  status='prepared_not_reviewed', context_before=library[max(0, offset-1):offset],
                  context_after=library[offset+args.count:offset+args.count+1])
    write(out / 'packet.json', packet)
    write(out / 'sources/manifest.json', manifests)
    # Candidate inventory aids manual identity checks; never merges by name.
    text = ''.join(p['text'] for p in selected)
    candidates = [c for c in people_registry(out)
                  if any(len(name) >= 2 and name in text for name in [c['row']['name']] + c['row'].get('aliases', []))]
    write(out / 'identity-candidates.json', candidates)
    write(out / 'curation.json', dict(batch_key=args.batch_key, claim_namespace=args.batch_key, reused_keys=[], items=[],
          paragraph_reviews=[dict(paragraph_id=p['id'], status='pending', note='', observations=[])
                             for p in selected]))
    print(json.dumps(dict(prepared=str(out), paragraphs=len(selected), next_paragraph=packet['next_paragraph']), ensure_ascii=False))


def compile_batch(directory):
    guard(directory)
    packet, curated = read(directory / 'packet.json'), read(directory / 'curation.json')
    check_range(packet)
    primary_ids = [p['id'] for p in packet['paragraphs']]
    paragraphs = {p['id']: p for p in packet['paragraphs'] + supplementary_records(packet)}
    manifest = read(directory / 'sources/manifest.json')
    assert [m['paragraph_id'] for m in manifest] == list(paragraphs), 'Source range mismatch'
    sources = {}
    for m in manifest:
        raw = (directory / 'sources' / m['file']).read_bytes()
        assert sha(raw) == m['sha256'] == paragraphs[m['paragraph_id']]['locator']['raw_excerpt_sha256']
        sources[m['paragraph_id']] = (m, raw.decode('utf-8'))
    reviews = curated['paragraph_reviews']
    assert [r['paragraph_id'] for r in reviews] == primary_ids, 'Every paragraph needs an ordered review'
    assert all(r['status'] in ('reviewed', 'pending_textual_review') and r['note'] for r in reviews), 'Unreviewed paragraph'
    batch = dict(format_version=1, batch_key=curated['batch_key'],
                 **{g: [] for g in (*GROUPS, 'sources', 'claims', 'topics')})
    evidence_by_paragraph = defaultdict(list)
    for m in manifest:
        p = paragraphs[m['paragraph_id']]
        reviewed_citation = m.get('reviewed_citation')
        claim_citation = m.get('authored_claim_citation', reviewed_citation)
        if m.get('authored_claim_citation') is not None:
            reuse=m.get('canonical_source_reuse',{})
            assert (reuse.get('source_key'),reuse.get('paragraph_id'),reuse.get('raw_snapshot_sha256'))==(m['key'],p['id'],m['sha256']), 'Separate claim citation needs verified canonical source reuse'
        if reviewed_citation is not None:
            assert isinstance(reviewed_citation, str) and reviewed_citation.strip(), 'Invalid reviewed citation'
            assert m.get('citation_review_note', '').strip(), 'Reviewed citation needs review note'
            assert (isinstance(claim_citation,str) and f"《{p['book']}》" in claim_citation
                    and f"卷{p['volume_candidate']}" in claim_citation
                    and p['id'] in claim_citation), 'Reviewed citation must retain book, volume and paragraph'
        batch['sources'].append(dict(key=m['key'], title=m.get('source_title') or f"{p['book']}·卷{p['volume_candidate']}·{p['section_title']}·{p['id']}",
            source_type='primary', author={'zizhi-tongjian': '司马光等', 'xu-zizhi-tongjian': '毕沅等',
                'songshi': '脱脱等', 'liaoshi': '脱脱等', 'jiu-wudaishi': '薛居正等', 'xin-wudaishi': '欧阳修'}.get(p['book_key']),
            edition='选定电子TXT逐字快照；已核本次上下文，纸本及异文未全面校核。', url=m['url'], note=reviewed_citation or p['citation']))
    supplements = []
    for item in curated['items']:
        group = item['group']
        assert group in GROUPS and item['evidence'], 'Fact must have evidence'
        row = dict(item['row'], status='draft')
        batch[group].append(row)
        for i, evidence in enumerate(item['evidence']):
            pid = evidence['paragraph_id']
            m, text = sources[pid]
            assert evidence['quote'] and evidence['quote'] in text, f"Quote mismatch: {row['key']}"
            assert evidence['note'] and evidence['field'] in row, 'Missing explanation or invalid field'
            # Legacy local drafts keep their keys. New packets namespace claims
            # by batch so another source for a reused subject cannot collide.
            prefix = curated.get('claim_namespace')
            claim_key = f"claim_{prefix}_{row['key']}_{i+1:02d}" if prefix else f"claim_{row['key']}_{i+1:02d}"
            claim = dict(key=claim_key, subject_table=TABLES[group], subject_key=row['key'],
                         field_path=evidence['field'], claim_text=evidence['text'], source_key=m['key'],
                         citation=(m.get('authored_claim_citation') or m.get('reviewed_citation') or f"《{paragraphs[pid]['book']}》卷{paragraphs[pid]['volume_candidate']}·{paragraphs[pid]['section_title']}·{pid}") + f"；{evidence['time_context']}",
                         note=f"原文：{evidence['quote']}；核对说明：{evidence['note']}", status='draft')
            batch['claims'].append(claim)
            if pid in primary_ids:
                evidence_by_paragraph[pid].append(claim)
            else:
                anchor = evidence['primary_paragraph_id']
                assert anchor in primary_ids, 'Supplement needs a primary paragraph anchor'
                assert any(e['paragraph_id'] in primary_ids for e in item['evidence']), 'Supplement subject lacks primary evidence'
                assert evidence['relation'] in ('corroborates', 'adds', 'conflicts'), 'Invalid supplement relation'
                supplements.append(dict(claim_key=claim_key, source_book=paragraphs[pid]['book_key'],
                    primary_paragraph_id=anchor, subject_key=row['key'], relation=evidence['relation']))
                evidence_by_paragraph[anchor].append(claim)
    keys = {r['key'] for g in GROUPS for r in batch[g]}
    reused = curated['reused_keys']
    assert len(set(reused)) == len(reused) and set(reused) <= keys, 'Invalid reused keys'
    # Same-name or alias candidates require an explicit identity decision.
    candidates = people_registry(directory)
    for item in curated['items']:
        if item['group'] != 'people':
            continue
        row = item['row']
        names = set([row['name']] + row.get('aliases', []))
        collisions = [c for c in candidates if names.intersection([c['row']['name']] + c['row'].get('aliases', []))]
        for candidate in collisions:
            if candidate['row']['key'] == row['key']:
                assert dict(candidate['row'], status='draft') == dict(row, status='draft'), 'Existing person changed'
        if any(c['row']['key'] != row['key'] for c in collisions):
            assert item.get('identity_note'), f"Identity decision required: {row['name']}"
        if row['key'] in reused:
            assert any(dict(c['row'], status='draft') == dict(row, status='draft') for c in collisions), 'Reused person changed'
    ledger = []
    for review in reviews:
        claims = evidence_by_paragraph[review['paragraph_id']]
        assert claims or review.get('observations'), 'No facts: record an exclusion/reuse reason'
        ledger.append(dict(**review, subject_keys=sorted({c['subject_key'] for c in claims}),
                           claim_keys=[c['key'] for c in claims], publication_status='not_published'))
    coverage = dict(book=packet['book'], book_key=packet['book_key'], volume=packet['volume'], year=None,
                    primary_source_key=manifest[0]['key'], primary_source_keys=[m['key'] for m in manifest if m['paragraph_id'] in primary_ids],
                    paragraphs=primary_ids, next_paragraph=packet['next_paragraph'], supplements=supplements,
                    coverage='连续阅读块逐条整理；追叙、史家评价及待考点见审阅账本。', status='reviewed_local_draft')
    return batch, coverage, ledger, reused, packet


def link_sources(args):
    """Bind local draft snapshots to a verified Git blob; no commit or network."""
    directory = args.directory.resolve()
    guard(directory)
    commit = args.commit.lower()
    assert len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'Use a full commit SHA'
    packet = read(directory / 'packet.json')
    check_range(packet)
    supplementary_records(packet)
    prefix = Path(args.archive_prefix) if args.archive_prefix else (directory / 'sources').relative_to(ROOT)
    assert not prefix.is_absolute() and '..' not in prefix.parts, 'Archive prefix must be repository-relative'
    manifest = read(directory / 'sources/manifest.json')
    for item in manifest:
        relative = Path(item['file'])
        assert not relative.is_absolute() and '..' not in relative.parts, 'Invalid snapshot path'
        local = (directory / 'sources' / relative).read_bytes()
        assert sha(local) == item['sha256'], 'Local source snapshot changed'
        archive_path = (prefix / relative).as_posix()
        archived = subprocess.check_output(['git', 'show', f'{commit}:{archive_path}'], cwd=ROOT)
        assert sha(archived) == item['sha256'], 'Archived snapshot differs from local snapshot'
        item.update(url=f'https://github.com/greed-216/histree/blob/{commit}/{quote(archive_path)}',
                    snapshot_commit=commit, snapshot_status='committed_source_snapshot', archived_file=archive_path)
    # Write only after all blobs pass; no partially linked manifest.
    write(directory / 'sources/manifest.json', manifest)
    print(json.dumps(dict(linked_sources=len(manifest), commit=commit, rebuild_required=True), ensure_ascii=False))


def review_html(batch, ledger, packet, directory):
    esc = html.escape
    rows = {r['key']: r for group in GROUPS for r in batch[group]}
    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>史料录入试点审阅</title>',
        '<style>body{font:16px/1.8 system-ui;max-width:1300px;margin:35px auto;padding:20px;color:#24313b}section{border-top:2px solid #ddd;margin-top:30px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:30px}.source{white-space:pre-wrap;background:#f6f3ed;padding:20px}article{border-bottom:1px solid #ddd;padding:10px}small{color:#576774}code{overflow-wrap:anywhere}h3{margin-bottom:0}@media(max-width:800px){.columns{grid-template-columns:1fr}}</style>',
        f'<h1>《{esc(packet["book"])}》卷{packet["volume"]}：连续录入试点</h1>',
        '<p>本地草稿；尚未发布。左侧为逐字底本快照，右侧为事实与校核说明。阅读块不是原书自然段。未全面校核纸本与异文。</p>',
        '<p>' + esc('；'.join(f'{g}: {len(batch[g])}' for g in (*GROUPS, 'claims'))) + '</p>']
    for p, audit in zip(packet['paragraphs'], ledger):
        claims = [c for c in batch['claims'] if c['key'] in audit['claim_keys']]
        raw = (directory / 'sources' / p['id'] / 'source.txt').read_text()
        parts.append(f'<section><h2>{esc(p["id"])}</h2><p>{esc(audit["note"])}</p><div class="columns"><div class="source">{esc(raw)}</div><div>')
        for key in audit['subject_keys']:
            row = rows[key]
            parts.append(f'<article><h3>{esc(row.get("title", row.get("name", row.get("description", row.get("role", key)))))}</h3><code>{esc(key)}</code><p>{esc(row.get("description", row.get("role", "")))}</p>')
            if 'time_original' in row:
                parts.append(f'<p>时间：{esc(row["time_original"])}；年份：{row.get("start_year")}</p>')
            for claim in claims:
                if claim['subject_key'] == key:
                    parts.append(f'<p><small>{esc(claim["field_path"])}：{esc(claim["note"])}</small></p>')
            parts.append('</article>')
        for observation in audit.get('observations', []):
            parts.append(f'<p><strong>保留说明／待考：</strong>{esc(observation)}</p>')
        parts.append('</div></div></section>')
    parts.append(f'<p>下一阅读块：{esc(packet["next_paragraph"] or "无")}。当前范围未计入已发布进度。</p></html>')
    return '\n'.join(parts)


def build(args):
    directory = args.directory.resolve()
    batch, coverage, ledger, reused, packet = compile_batch(directory)
    # Validate before replacing previous generated outputs.
    with tempfile.TemporaryDirectory(prefix='histree-batch-') as temp:
        staged = Path(temp)
        write(staged / 'content-batch.json', batch)
        write(staged / 'sources/manifest.json', read(directory / 'sources/manifest.json'))
        for m in read(directory / 'sources/manifest.json'):
            target = staged / 'sources' / m['file']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((directory / 'sources' / m['file']).read_bytes())
        result = subprocess.check_output([sys.executable, str(ROOT / 'scripts/validate-content-batch.py'), str(staged / 'content-batch.json')], text=True)
        report = json.loads(result)
    for name, value in [('content-batch.json', batch), ('coverage.json', coverage), ('paragraphs.json', ledger),
                        ('reused-keys.json', reused), ('validation.json', report)]:
        write(directory / name, value)
    write(directory / 'workbench-validation.json', dict(
        packet_sha256=sha((directory / 'packet.json').read_bytes()),
        curation_sha256=sha((directory / 'curation.json').read_bytes()),
        batch_sha256=sha((directory / 'content-batch.json').read_bytes()),
        continuous_range_checked=True, source_snapshot_hashes_checked=True,
        archived_upstream_checked_at_preparation=True, local_identity_registry_checked=True,
        paragraph_reviews=len(ledger),
        pending_textual_review=[r['paragraph_id'] for r in ledger if r['status'] == 'pending_textual_review'],
        online_preflight=False, published=False,
        release_requirements=['Resolve or explicitly isolate pending textual issues.',
                              'Commit new snapshots and verify their fixed source URLs.',
                              'Run online identity preflight before authorized publication.']))
    (directory / 'review.html').write_text(review_html(batch, ledger, packet, directory))
    print(json.dumps(report, ensure_ascii=False, indent=2))


def assemble_source_interval(covered, snapshots, source):
    """Preserve snapshots and explicitly account for whitespace-only split gaps."""
    assert len(covered) == len(snapshots), 'Snapshot count mismatch'
    text = source.decode('utf-8')
    pieces, gaps = [], []
    last_end = covered[0]['locator']['char_start']
    for paragraph, snapshot in zip(covered, snapshots):
        loc = paragraph['locator']
        start, end = loc['char_start'], loc['char_end']
        assert start >= last_end and end >= start, 'Source character overlap'
        if start > last_end:
            gap = text[last_end:start]
            assert gap and gap.isspace(), 'Source character gap contains body text'
            pieces.append(gap.encode('utf-8'))
            gaps.append(dict(char_start=last_end, char_end=start, text=gap,
                             sha256=sha(gap.encode('utf-8')), status='verified_structural_whitespace'))
        assert snapshot.decode('utf-8') == text[start:end], 'Source snapshot interval differs'
        pieces.append(snapshot)
        last_end = end
    raw = b''.join(pieces)
    assert raw.decode('utf-8') == text[covered[0]['locator']['char_start']:last_end], 'Source interval differs'
    return raw, gaps


def volume_source_bounds(book, volume, text):
    """Keep legacy per-volume TXT checks; scope shared TXT to hashed sections."""
    path = ROOT / book['sections_file'] if book.get('sections_file') else None
    if path is None:
        return 0, len(text)
    assert sha(path.read_bytes()) == book['sections_sha256'], 'Section catalog changed'
    sections = [s for s in read(path) if s.get('volume_candidate') == volume]
    assert len(sections) == 1, 'Expected a unique volume section'
    section = sections[0]
    start, end = section['char_start'], section['char_end']
    assert 0 <= start < end <= len(text), 'Invalid volume section bounds'
    return start, end


def audit(args):
    """Audit all local draft batches in one workflow against a complete volume."""
    directory = args.directory.resolve()
    packets = sorted(directory.glob('part-*/packet.json'))
    assert packets, 'No batch packets found'
    first = read(packets[0])
    book, library = records(first['book_key'])
    expected = [p for p in library if p.get('volume_candidate') == first['volume']]
    covered, manifests, pending, details, auxiliary = [], [], [], [], []
    subjects = {g: {} for g in (*GROUPS, 'sources', 'claims')}
    for path in packets:
        packet = read(path)
        assert (packet['book_key'], packet['volume'], packet['source_version']) == (
            first['book_key'], first['volume'], first['source_version']), 'Mixed source or volume'
        batch, _, ledger, reused, _ = compile_batch(path.parent)
        assert read(path.parent / 'content-batch.json') == batch, 'Generated batch is stale; rebuild first'
        subprocess.run([sys.executable, str(ROOT / 'scripts/validate-content-batch.py'),
                        str(path.parent / 'content-batch.json')], check=True, stdout=subprocess.DEVNULL)
        for group in subjects:
            for row in batch[group]:
                old = subjects[group].get(row['key'])
                if old:
                    assert group in GROUPS and row['key'] in reused and old == row, f"Cross-batch key collision: {row['key']}"
                subjects[group][row['key']] = row
        covered.extend(packet['paragraphs'])
        pending.extend(dict(batch=str(path.parent.relative_to(directory)), paragraph_id=r['paragraph_id'],
                            observations=r.get('observations', []))
                       for r in ledger if r['status'] == 'pending_textual_review')
        primary_ids = {p['id'] for p in packet['paragraphs']}
        for m in read(path.parent / 'sources/manifest.json'):
            if m['paragraph_id'] in primary_ids:
                manifests.append((path.parent, m))
            else:
                auxiliary.append(dict(batch=str(path.parent.relative_to(directory)),
                                      paragraph_id=m['paragraph_id'], sha256=m['sha256']))
        details.append(dict(batch=batch['batch_key'], path=str(path.parent.relative_to(directory)),
                            batch_sha256=sha((path.parent / 'content-batch.json').read_bytes()),
                            curation_sha256=sha((path.parent / 'curation.json').read_bytes()),
                            counts={g: len(batch[g]) for g in subjects},
                            paragraphs=[p['id'] for p in packet['paragraphs']]))
    assert covered == expected, 'Volume has a gap, overlap, or out-of-order batch'
    # Every byte of the selected volume body interval is preserved, including
    # source headings and whitespace. Trailing structural whitespace is allowed.
    loc = covered[0]['locator']
    assert all(p['locator']['source_file'] == loc['source_file'] for p in covered), 'Multiple source files: audit not supported'
    snapshots = [(folder / 'sources' / m['file']).read_bytes() for folder, m in manifests]
    source = (ROOT / loc['source_file']).read_bytes()
    assert sha(source) == loc['source_sha256']
    raw, whitespace_gaps = assemble_source_interval(covered, snapshots, source)
    source_text = source.decode('utf-8')
    end = covered[-1]['locator']['char_end']
    assert raw.decode('utf-8') == source_text[loc['char_start']:end], 'Source interval differs'
    # A book may keep every volume in one TXT. In that case require a unique,
    # catalog-bound section interval rather than treating adjacent volumes as gaps.
    interval = volume_source_bounds(book, first['volume'], source_text)
    assert not source_text[interval[0]:loc['char_start']].strip() and not source_text[end:interval[1]].strip(), 'Uncovered source body'
    assert interval[0] <= loc['char_start'] < end <= interval[1], 'Source exceeds volume section'
    report = dict(book_key=book['book_key'], volume=first['volume'], source_version=first['source_version'],
                  status='whole_volume_local_draft_with_pending_review' if pending else 'whole_volume_local_draft_reviewed',
                  full_volume_source_coverage=True, paragraphs=len(covered), source_characters=len(raw.decode('utf-8')),
                  source_interval_sha256=sha(raw), source_whitespace_gaps=whitespace_gaps,
                  snapshot_characters=sum(len(s.decode('utf-8')) for s in snapshots),
                  supplementary_records=auxiliary,
                  unique_counts={g: len(rows) for g, rows in subjects.items()},
                  batches=details, pending_paragraphs=pending, next_paragraph=read(packets[-1])['next_paragraph'],
                  published=False, publication_verified=False,
                  limitations=['Full source coverage does not establish exhaustive fact extraction.',
                               'Pending identities and textual issues remain; this is not published completion.'])
    write(directory / 'volume-audit.json', report)
    links = ''.join(f'<li><a href="{html.escape(d["path"])}/review.html">{html.escape(d["batch"])}</a>：{len(d["paragraphs"])}个连续阅读块</li>' for d in details)
    pending_html = ''.join(f'<li>{html.escape(r["paragraph_id"])}<ul>' + ''.join(f'<li>{html.escape(x)}</li>' for x in r['observations']) + '</ul></li>' for r in pending)
    (directory / 'review.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>史料整卷整理总览</title>'
        '<style>body{max-width:1000px;margin:40px auto;padding:20px;font:17px/1.8 system-ui;color:#24313b}a{color:#17665b}</style>'
        f'<h1>《{html.escape(book["book"])}》卷{first["volume"]}：整卷本地整理</h1><p>全部{len(covered)}个阅读块已连续处理，来源快照共{report["source_characters"]}字。未发布，未标记线上完成。</p>'
        '<p>' + html.escape('；'.join(f'{g}: {len(rows)}' for g, rows in subjects.items())) + '</p>'
        f'<h2>原文与事实对照</h2><ul>{links}</ul><h2>待考清单</h2><ul>{pending_html}</ul>'
        '<p>全卷原文覆盖检查通过，不等于每条潜在事实都已穷尽提取。史论、计划、传闻和未具名者的处理说明见各批审阅页。</p></html>')
    print(json.dumps({k: v for k, v in report.items() if k not in ('batches', 'pending_paragraphs')}, ensure_ascii=False, indent=2))


def main():
    global ROOT, CATALOG
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help='content repository; defaults to script repository')
    subs = parser.add_subparsers(dest='command', required=True)
    prep = subs.add_parser('prepare')
    prep.add_argument('--book', required=True)
    prep.add_argument('--volume', required=True, type=int)
    prep.add_argument('--start')
    prep.add_argument('--count', required=True, type=int)
    prep.add_argument('--batch-key', required=True)
    prep.add_argument('--out', required=True, type=Path)
    prep.add_argument('--upstream-commit', help='archived upstream TXT commit; defaults to HEAD')
    prep.set_defaults(run=prepare)
    compiler = subs.add_parser('build')
    compiler.add_argument('directory', type=Path)
    compiler.set_defaults(run=build)
    supplement = subs.add_parser('add-supplement', help='export one necessary identity or textual check without advancing another book')
    supplement.add_argument('directory', type=Path)
    supplement.add_argument('--book', required=True)
    supplement.add_argument('--id', required=True)
    supplement.add_argument('--title', required=True, help='reviewed book, volume and passage title')
    supplement.set_defaults(run=add_supplement)
    linker = subs.add_parser('link-sources', help='bind draft source URLs to hash-verified archived blobs')
    linker.add_argument('directory', type=Path)
    linker.add_argument('--commit', required=True)
    linker.add_argument('--archive-prefix', help='repository-relative sources directory if archive path differs')
    linker.set_defaults(run=link_sources)
    verifier = subs.add_parser('audit', help='check all draft batches against the full volume source')
    verifier.add_argument('directory', type=Path)
    verifier.set_defaults(run=audit)
    args = parser.parse_args()
    if args.root:
        ROOT = args.root.resolve()
        CATALOG = ROOT / 'resources/derived/history-library/catalog.json'
    args.run(args)


if __name__ == '__main__':
    main()
