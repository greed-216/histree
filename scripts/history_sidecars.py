# coding: utf-8
"""Source-scoped dating and reading links for any verified history-workbench batch.

Usage: history_sidecars.py BATCH_DIR [--root REPOSITORY] [--mysql-env FILE]
       [--public-api-url HTTPS_URL] [--plan BATCH_DIR/.workflow/NAME.json]
Default: read-only DB preparation/preflight; writes only a local immutable plan.
The default outputs are BATCH_DIR/.workflow/sidecars-plan.json and
BATCH_DIR/.workflow/sidecars-receipt.json. A receipt prevents plan refresh.
--apply requires an existing plan's exact SHA and acquires the publisher's global
lock. It inserts three additive sidecar tables only. No DDL or canonical updates.
--verify-public resumes the separate anonymous acceptance phase after commit.
"""
import argparse
import concurrent.futures
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import re
import sys
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NS = uuid.UUID('85a50c7a-72ae-5c87-9949-0690b7fd3763')
FIELDS = {
    'event_dating': ('id', 'event_id', 'claim_id', 'claim_sha256', 'earliest_year',
                     'latest_year', 'precision_kind', 'era_key', 'basis', 'review_state'),
    'claim_structure': ('claim_id', 'note_sha256', 'quote_text', 'review_note', 'review_state'),
    'library_source_link': ('source_id', 'archive_url_sha256', 'snapshot_sha256', 'paragraph_id'),
}
IDENTITY = {'event_dating': ('id',), 'claim_structure': ('claim_id',),
            'library_source_link': ('source_id', 'archive_url_sha256')}
READ_TABLES = {'event', 'fact_claim', 'source', 'source_text', 'library_book',
               'library_paragraph', 'library_asset', *FIELDS}
FINGERPRINT_FIELDS = ('subject_table', 'subject_id', 'claim_text', 'source_id', 'citation', 'note')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def exact_text_with_structural_edges(snapshot_text, paragraph_text):
    """Only extra edge whitespace is structural; the paragraph remains one exact span.

    Do not normalize interior spaces, punctuation, glyphs, BOMs or line endings.
    Snapshot bytes/SHA and source offsets are checked separately and remain raw.
    """
    require(isinstance(snapshot_text,str) and isinstance(paragraph_text,str) and bool(paragraph_text.strip()), 'Empty/non-text paragraph')
    return re.fullmatch(r'\s*'+re.escape(paragraph_text)+r'\s*',snapshot_text) is not None


def packet_text_matches_snapshot(snapshot_text, para):
    """Separate legacy reading layout from immutable evidence bytes, never table cells."""
    display=para['text']
    exact=snapshot_text[1:] if snapshot_text.startswith('\ufeff') else snapshot_text
    if exact_text_with_structural_edges(exact,display):return True
    legacy=(para.get('book_key')=='zizhi-tongjian' and para.get('source_version')=='a63549944a71'
            and para.get('kind')=='body' and re.fullmatch(r'zizhi-tongjian-a63549944a71-p\d{6}',para.get('id','')))
    if not legacy or any(c in snapshot_text or c in display for c in ('\t','\r','\ufeff')):return False
    return snapshot_text.replace('\n◎\n',' ◎ ').replace('\n','').strip()==display


def claim_fingerprint(claim, source_url):
    # Exactly the deployed query-contracts.ts HEX(COALESCE(...,'')) SQL contract.
    vals = [claim.get(k) for k in FINGERPRINT_FIELDS] + [source_url]
    encoded = '|'.join(str(v if v is not None else '').encode('utf-8').hex().upper() for v in vals)
    return sha(encoded.encode('ascii'))


def parse_note(note):
    require(isinstance(note, str) and note.startswith('原文：'), 'Unstructured claim note')
    body, marker, review = note[3:].partition('；核对说明：')
    require(bool(marker) and bool(body) and bool(review), 'Missing quote/review delimiter')
    return body, review


def year(value):
    require(value is None or type(value) is int and value != 0 and -10000 <= value <= 10000,
            'Invalid authored year (including bool/year zero)')
    return value


def dating_shape(decision, data, era=None):
    """No extraction of numbers from prose and no inheritance of canonical event years."""
    if data.get('year') is not None:
        y = year(data['year'])
        return dict(earliest_year=y, latest_year=y, precision_kind='year', era_key=None)
    if decision == 'exact':
        raise ValueError('Exact decision has no explicitly authored integer year')
    lo = data.get('earliest_year', data.get('start_year'))
    hi = data.get('latest_year', data.get('end_year'))
    year(lo); year(hi)
    require(lo is None or hi is None or lo <= hi, 'Reversed authored interval')
    if decision == 'range':
        require(lo is not None and hi is not None, 'Range needs both authored bounds')
        return dict(earliest_year=lo, latest_year=hi, precision_kind='range', era_key=None)
    if decision == 'relative':
        return dict(earliest_year=lo, latest_year=hi, precision_kind='relative', era_key=None)
    if decision == 'era':
        era = data.get('era_key') or era
        require(isinstance(era, str) and era.strip(), 'Era decision needs authored era')
        return dict(earliest_year=lo, latest_year=hi, precision_kind='era', era_key=era)
    if decision == 'unknown':
        require(lo is None and hi is None, 'Unknown decision unexpectedly has numerical bounds')
        return dict(earliest_year=None, latest_year=None, precision_kind='unknown', era_key=None)
    # Explicit bounded fields are valid even on a source-scoped inherited/conflicting review.
    # They are numerical author input, never recovered by parsing prose or canonical dates.
    if lo is not None or hi is not None:
        require(lo is not None and hi is not None, 'Unclassified source bounds need both explicit ends')
        return dict(earliest_year=lo, latest_year=hi, precision_kind='range', era_key=None)
    # inherited/conflicting/multiple do not acquire a guessed year from prose.
    return None


def authored_assertions(item, manifest):
    """One independently bound assertion per authored paragraph/year, not last-call wins."""
    review = item['temporal_review']
    require(review.get('reason') and review.get('anchor_note'), 'Missing authored temporal audit')
    evidence = item['evidence']
    rows = review.get('source_dating_assertions', [])
    require(isinstance(rows, list), 'source_dating_assertions must be a list')
    result = []
    for assertion in rows:
        pid = assertion.get('paragraph_id')
        require(pid in manifest, 'Authored assertion paragraph missing from this manifest')
        require(any(e['paragraph_id'] == pid for e in evidence),
                'Authored assertion has no actual event evidence in that paragraph')
        shape = dating_shape(assertion.get('decision', review['decision']), assertion,
                             item['row'].get('dynasty'))
        if shape is None:
            # A null year is not independently exact; report it and retain no invented row.
            continue
        basis = assertion.get('basis') or review['reason']
        require(isinstance(basis, str) and basis.strip(), 'Missing assertion basis')
        result.append(dict(paragraph_id=pid, shape=shape, basis=basis))
    if result:
        # Same paragraph/year can occur in several evidence fields; preserve all basis notes.
        merged = {}
        for a in result:
            k = (a['paragraph_id'], json.dumps(a['shape'], sort_keys=True))
            if k not in merged:
                merged[k] = a
            elif a['basis'] not in merged[k]['basis']:
                merged[k]['basis'] += ' ' + a['basis']
        return list(merged.values()), None
    if rows:
        return [], 'Authored source assertions contain no numerical/range/relative/era conclusion'
    shape = dating_shape(review['decision'], review, item['row'].get('dynasty'))
    if shape is None:
        return [], 'No explicitly authored source year/bounds; canonical date and reason prose were not parsed'
    requested = review.get('source_keys') or []
    candidates = [e for e in evidence if manifest[e['paragraph_id']]['key'] in requested] if requested else evidence
    require(bool(candidates), 'Review source_keys do not refer to this event evidence')
    # Prefer an event fact over a supplementary calendar heading; the authored audit can
    # still cite the independent calendar anchors in its basis without making them actions.
    ev = next((e for e in candidates if e['field'] == 'start_year'),
              next((e for e in candidates if e['field'] == 'description'), candidates[0]))
    return [dict(paragraph_id=ev['paragraph_id'], shape=shape,
                 basis=review['reason'] + ' ' + review['anchor_note'])], None


def load_bundle(root, batch_dir):
    root = root.resolve()
    batch_dir = Path(batch_dir).resolve()
    require(root in batch_dir.parents, 'Batch directory must be inside --root')
    names = ['content-batch.json', 'curation.json', 'packet.json', 'sources/manifest.json',
             'sql/key-map.json', 'publication-mysql.json', 'time-review.json']
    files = {}
    objects = {}
    for name in names:
        path = batch_dir / name
        require(path.is_file(), 'Required published archive missing: ' + str(path))
        raw = path.read_bytes()
        files[str(path.relative_to(root))] = sha(raw)
        objects[name] = json.loads(raw)
    batch = objects['content-batch.json']; cur = objects['curation.json']
    packet = objects['packet.json']; publication = objects['publication-mysql.json']
    require(publication.get('backend') == 'mysql' and publication.get('verified') is True,
            'Volume needs verified MySQL publication before sidecar preparation')
    require(publication.get('batch_sha256') == files[str((batch_dir/'content-batch.json').relative_to(root))],
            'Published batch SHA mismatch')
    require(batch['batch_key'] == cur['batch_key'] == cur['claim_namespace'], 'Curation/batch namespace mismatch')
    if publication.get('source_only_evidence') is True:
        require(not any(batch[k] for k in ('people','events','person_events','person_relationships','claims','topics')),'Source-only evidence cannot contain fact rows')
    require(isinstance(packet.get('book_key'),str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*',packet['book_key']), 'Invalid packet book key')
    require(isinstance(packet.get('source_version'),str) and bool(packet['source_version'].strip()), 'Missing packet source version')
    require(type(packet.get('volume')) is int and packet['volume'] > 0, 'Invalid packet volume')
    require(bool(packet.get('paragraphs')), 'Empty primary packet')
    for para in packet['paragraphs']:
        require(para['book_key']==packet['book_key'] and para['source_version']==packet['source_version'], 'Primary paragraph book/version differs from packet')
        if para.get('volume_candidate') is not None:
            require(para['volume_candidate']==packet['volume'], 'Primary paragraph volume differs from packet')
    timer=objects['time-review.json']
    require(timer.get('batch_sha256')==publication['batch_sha256'], 'Time audit is not bound to the published batch')
    audited={r['key']:r for r in timer['events']}
    authored={it['row']['key']:it for it in cur['items'] if it['group']=='events'}
    require(set(audited)==set(authored), 'Curation/time-audit event set mismatch')
    for key,item in authored.items():
        require(all(audited[key].get(k)==v for k,v in item['temporal_review'].items()), 'Published time audit differs from authored curation: '+key)
    for item in cur['items']:
        frozen=next((row for row in batch[item['group']] if row['key']==item['row']['key']),None)
        require(frozen is not None and all(frozen.get(k)==v for k,v in item['row'].items() if k!='status'), 'Curation row differs from frozen batch: '+item['row']['key'])
    ids = objects['sql/key-map.json']
    require(len(set(ids.values())) == len(ids), 'Key map contains duplicate UUIDs')
    for value in ids.values():
        require(str(uuid.UUID(value)) == value, 'Invalid canonical UUID in key map')
    paras = {p['id']: p for p in packet['paragraphs'] + packet.get('supplementary_paragraphs', [])}
    require(len(paras)==len(packet['paragraphs'])+len(packet.get('supplementary_paragraphs',[])), 'Duplicate packet paragraph ID')
    manifest = {m['paragraph_id']: m for m in objects['sources/manifest.json']}
    require(len(manifest) == len(objects['sources/manifest.json']), 'Duplicate manifest paragraph')
    snapshots = {}
    used_source_keys={claim['source_key'] for claim in batch['claims']}
    excluded_structural_headings=[]
    for pid, m in manifest.items():
        require(pid in paras, 'Manifest paragraph absent from bound packet')
        path = (batch_dir/'sources'/m['file']).resolve()
        require((batch_dir/'sources').resolve() in path.parents, 'Snapshot escaped sources directory')
        raw = path.read_bytes()
        require(sha(raw) == m['sha256'], 'Manifest snapshot SHA mismatch: ' + pid)
        locator=paras[pid]['locator']
        require(m.get('upstream_locator')==locator and locator.get('raw_excerpt_sha256')==m['sha256'], 'Manifest/packet archived locator differs: '+pid)
        require(type(locator['char_start']) is int and type(locator['char_end']) is int and locator['char_start']>=0 and locator['char_end']-locator['char_start']==len(raw.decode('utf-8')), 'Raw snapshot/source character offsets differ: '+pid)
        para=paras[pid]
        unused_structural_heading=(m['key'] not in used_source_keys and para.get('kind')=='heading' and bool(set(para.get('flags',[])) & {'not_historical_body','editorial_navigation_heading'}))
        if unused_structural_heading:
            # The segmentation library normalizes display headings. The immutable raw
            # archive and offsets remain authoritative; this unused title is not a fact.
            excluded_structural_headings.append(pid)
        else:
            require(packet_text_matches_snapshot(raw.decode('utf-8'),para), 'Packet and exact snapshot text differ: ' + pid)
        files[str(path.relative_to(root))] = sha(raw)
        snapshots[pid] = raw
    sources = {s['key']: s for s in batch['sources']}
    for m in manifest.values():
        require(m['key'] in sources and m['key'] in ids, 'Manifest/source/key-map mismatch')
        require(sources[m['key']]['url'] == m['url'], 'Manifest/batch source URL mismatch')
    for c in batch['claims']:
        require(c['key'] in ids and c['subject_key'] in ids and c['source_key'] in ids,
                'Claim absent from key map')
    return dict(root=root, batch_dir=batch_dir, batch=batch, cur=cur, packet=packet, ids=ids,
                publication=publication, manifest=manifest, paras=paras,
                snapshots=snapshots, files=files, sources=sources, excluded_structural_headings=excluded_structural_headings)


class _RowDatabase:
    def __init__(self, root, env, writable=False):
        sys.path.insert(0, str(root/'scripts'))
        from mysql_content_store import MysqlContentStore
        self.store = MysqlContentStore(env, writable=writable)
        self.connection = self.store.connection
        self.target_fingerprint = self.store.target_fingerprint
        self.writable = writable  # store obtains histree-content-publish before any write

    def schema(self):
        required = {**FIELDS,
                    'source_text': ('source_id','archive_url_sha256','archive_url','content',
                                    'content_sha256','archive_blob_sha256','archive_commit'),
                    'library_paragraph': ('id','book_key','section_id','content','content_sha256',
                                          'asset_id','char_start','char_end'),
                    'library_asset': ('id','source_file','source_sha256'),
                    'library_book': ('book_key','source_version','status')}
        for table, fields in required.items():
            require(set(fields) <= self.store.columns.get(table, set()), 'Missing table/columns: ' + table)
        with self.connection.cursor() as cursor:
            for table in required:
                cursor.execute('SELECT ENGINE FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name=%s', (table,))
                require(cursor.fetchone() == ('InnoDB',), 'Non-transactional table: ' + table)
            cursor.execute("SELECT column_type FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='claim_structure' AND column_name='review_state'")
            require(cursor.fetchone()[0] == "enum('recorded','deferred','unparsed')", 'Unexpected claim_structure review enum')
            cursor.execute("SELECT column_type FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='event_dating' AND column_name='review_state'")
            require(cursor.fetchone()[0] == "enum('proposed','reviewed')", 'Unexpected event_dating review enum')
            cursor.execute("SELECT column_type FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='event_dating' AND column_name='precision_kind'")
            require(cursor.fetchone()[0] == "enum('year','approximate','range','relative','era','unknown')", 'Unexpected dating precision enum')
            expected_fks={('event_dating','event_id','event','id'),('event_dating','claim_id','fact_claim','id'),('claim_structure','claim_id','fact_claim','id'),('library_source_link','paragraph_id','library_paragraph','id')}
            cursor.execute("SELECT table_name,column_name,referenced_table_name,referenced_column_name FROM information_schema.key_column_usage WHERE table_schema=DATABASE() AND referenced_table_name IS NOT NULL AND table_name IN ('event_dating','claim_structure','library_source_link')")
            require(expected_fks <= set(cursor.fetchall()), 'Required sidecar foreign-key constraint is missing')
            for table, identity in IDENTITY.items():
                cursor.execute('SELECT column_name FROM information_schema.statistics WHERE table_schema=DATABASE() AND table_name=%s AND index_name=%s ORDER BY seq_in_index', (table, 'PRIMARY'))
                require(tuple(r[0] for r in cursor.fetchall()) == identity, 'Unexpected sidecar primary key: ' + table)

    def get(self, table, identity, lock=False):
        require(table in READ_TABLES, 'Table outside bounded read set')
        require(bool(identity) and all(k in self.store.columns.get(table, ()) for k in identity), 'Invalid read identity')
        require(not lock or self.writable, 'Read-only preparation must not lock rows')
        import pymysql
        sql = 'SELECT * FROM `' + table + '` WHERE ' + ' AND '.join(self.store.column(table, k)+'=%s' for k in identity)
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql + (' FOR UPDATE' if lock else ''), list(identity.values()))
            rows = cursor.fetchall()
        require(len(rows) <= 1, 'Nonunique protected identity: '+table)
        return self.store.normalize(table, rows[0]) if rows else None

    def assert_publish_lock(self):
        require(self.writable, 'Publisher lock requires writable store')
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT IS_USED_LOCK('histree-content-publish')=CONNECTION_ID()")
            require(cursor.fetchone()[0] == 1, 'Global content publisher lock is not held')

    def insert(self, table, row):
        require(self.writable and table in FIELDS and set(row) == set(FIELDS[table]),
                'Only complete allowed sidecar INSERT rows are permitted')
        cols = list(FIELDS[table])
        with self.connection.cursor() as cursor:
            cursor.execute('INSERT INTO `'+table+'` ('+','.join(self.store.column(table,k) for k in cols)+') VALUES ('+','.join('%s' for _ in cols)+')',
                           [self.store.value(table,k,row[k]) for k in cols])


def normalized_claim(c, ids):
    return {**{k:v for k,v in c.items() if k not in ('key','subject_key','source_key','status')},
            'id':ids[c['key']], 'subject_id':ids[c['subject_key']],
            'source_id':ids[c['source_key']], 'status':'published'}


def used_sources(bundle):
    return ({m['key'] for pid,m in bundle['manifest'].items() if pid not in bundle['excluded_structural_headings']} if bundle['publication'].get('source_only_evidence') is True else {c['source_key'] for c in bundle['batch']['claims']})


def _prepare_rows(bundle, db):
    db.schema()
    require(db.target_fingerprint == bundle['publication']['target_fingerprint'], 'Publication target changed')
    protected = {}; inserts = {t: {} for t in FIELDS}; skipped = []
    def protect(table, identity):
        row = db.get(table, identity)
        require(row is not None, 'Missing published/provenance row: '+table+'/'+str(identity))
        key = (table, tuple(identity.items()))
        protected[key] = dict(table=table, identity=identity, row=row)
        return row
    ids = bundle['ids']; batch = bundle['batch']; manifest = bundle['manifest']
    source_by_key = {}; source_meta = {}; claim_by_key = {}; claims_by_subject = {}
    reviews = {r['paragraph_id']: r for r in bundle['cur']['paragraph_reviews']}
    for c in batch['claims']:
        expected = normalized_claim(c, ids); live = protect('fact_claim', {'id':expected['id']})
        require(all(live.get(k) == v for k,v in expected.items()), 'Published claim/key-map binding changed: '+c['key'])
        require(live['status'] == 'published', 'Claim is not public')
        claim_by_key[c['key']] = live
        claims_by_subject.setdefault(c['subject_key'], []).append((c, live))
    used = used_sources(bundle)
    by_source = {m['key']:pid for pid,m in manifest.items()}
    for sk in sorted(used):
        require(sk in by_source, 'Used source has no exact manifest paragraph')
        pid = by_source[sk]; m = manifest[pid]; expected = bundle['sources'][sk]
        source = protect('source', {'id':ids[sk]})
        require(all(source.get(k) == v for k,v in expected.items() if k != 'key'), 'Published source changed: '+sk)
        url = source['url']; uh = sha(url.encode('utf-8'))
        match = re.search(r'^https://github\.com/greed-216/histree/blob/([a-f0-9]{40})/', url)
        require(match is not None, 'Source is not pinned to a full fixed Git commit')
        text = protect('source_text', {'source_id':source['id'], 'archive_url_sha256':uh})
        raw = bundle['snapshots'][pid]; para = bundle['paras'][pid]
        require(text['archive_url'] == url and text['archive_commit'] == match[1], 'Snapshot archive URL/commit mismatch')
        require(text['content'].encode('utf-8') == raw and text['content_sha256'] == sha(raw), 'Published source_text differs from manifest bytes: '+pid)
        require(re.fullmatch('[a-f0-9]{64}', text['archive_blob_sha256']) is not None, 'Missing archived blob hash')
        library = protect('library_paragraph', {'id':pid})
        book = protect('library_book', {'book_key':para['book_key']})
        asset = protect('library_asset', {'id':library['asset_id']})
        require(book['source_version'] == para['source_version'] and book['status'] == 'available', 'Library book/version is not the bound available source')
        require(library['book_key'] == para['book_key'] and library['section_id'] == para['section_id'], 'Library paragraph belongs to another book/section')
        require(exact_text_with_structural_edges(text['content'],library['content']) and library['content_sha256'] == sha(library['content'].encode('utf-8')), 'Library/source snapshot content mismatch')
        loc = para['locator']
        require(library['char_start'] == loc['char_start'] and library['char_end'] == loc['char_end'], 'Library paragraph source offsets differ')
        require(asset['source_file'] == loc['source_file'] and asset['source_sha256'] == loc['source_sha256'], 'Library asset/bottom-text hash mismatch')
        link = dict(source_id=source['id'], archive_url_sha256=uh, snapshot_sha256=sha(raw), paragraph_id=pid)
        inserts['library_source_link'][(source['id'],uh)] = link
        source_by_key[sk] = source
        source_meta[source['id']] = dict(paragraph_id=pid, book_key=para['book_key'], section_id=para['section_id'], source_version=para['source_version'])
    # Structure ALL this batch's claims for readable quotes and original-text links.
    for c in batch['claims']:
        live = claim_by_key[c['key']]; quote, review = parse_note(live['note']); pid = by_source[c['source_key']]
        require(quote in bundle['snapshots'][pid].decode('utf-8-sig'), 'Claim quote not in the bound exact snapshot')
        state = 'deferred' if reviews.get(pid,{}).get('status') == 'pending_textual_review' else 'recorded'
        inserts['claim_structure'][(live['id'],)] = dict(claim_id=live['id'], note_sha256=sha(live['note'].encode('utf-8')), quote_text=quote, review_note=review, review_state=state)
    for item in bundle['cur']['items']:
        if item['group'] != 'events':
            continue
        key = item['row']['key']; require(key in ids, 'Event absent from key map')
        event = protect('event', {'id':ids[key]})
        require(event['status'] == 'published', 'Event is not published')
        batch_event = next((e for e in batch['events'] if e['key'] == key), None)
        require(batch_event is not None, 'Curated event absent from frozen batch')
        require(all(event.get(k) == v for k,v in batch_event.items() if k not in ('key','status')),
                'Frozen canonical event old values differ: '+key)
        assertions, reason = authored_assertions(item, manifest)
        if reason:
            skipped.append(dict(event_key=key, decision=item['temporal_review']['decision'], reason=reason))
        for a in assertions:
            pid = a['paragraph_id']; sk = manifest[pid]['key']
            require(pid not in bundle['excluded_structural_headings'], 'Unused structural heading cannot be a dating basis')
            evs = [ev for ev in item['evidence'] if ev['paragraph_id'] == pid]
            candidates = []
            for c, live in claims_by_subject.get(key, []):
                if c['source_key'] != sk:
                    continue
                quote, _ = parse_note(live['note'])
                if any(ev['quote'] == quote and ev['field'] == c['field_path'] and ev['text'] == c['claim_text'] for ev in evs):
                    candidates.append((c, live))
            require(bool(candidates), 'No actually published claim for authored paragraph/year: '+key+'/'+pid)
            _, claim = next((pair for pair in candidates if pair[0]['field_path'] in ('start_year','end_year','time_original')), candidates[0])
            require(claim['subject_table'] == 'event' and claim['subject_id'] == event['id'], 'Dating claim subject mismatch')
            quote, _ = parse_note(claim['note'])
            require(quote in bundle['snapshots'][pid].decode('utf-8-sig'), 'Dating quote/source mismatch')
            fp = claim_fingerprint(claim, source_by_key[sk]['url']); shape = a['shape']
            ident = '|'.join([bundle['publication']['batch_sha256'],event['id'],claim['id'],fp,json.dumps(shape,sort_keys=True)])
            row = dict(id=str(uuid.uuid5(NS,ident)), event_id=event['id'], claim_id=claim['id'], claim_sha256=fp,
                       **shape, basis=a['basis'], review_state='reviewed')
            inserts['event_dating'][(row['id'],)] = row
    return dict(format_version=1, kind='history_source_scoped_sidecars', implementation_sha256=sha(Path(__file__).read_bytes()), volume=bundle['packet']['volume'], book_key=bundle['packet']['book_key'], source_version=bundle['packet']['source_version'], batch_dir=str(bundle['batch_dir'].relative_to(bundle['root'])),
                batch_key=batch['batch_key'], batch_sha256=bundle['publication']['batch_sha256'],
                target_fingerprint=db.target_fingerprint, protected_paths=bundle['files'],
                protected_rows=list(protected.values()),
                inserts={t:list(rows.values()) for t,rows in inserts.items()},
                source_locations=source_meta, skipped_independent_dates=skipped, excluded_structural_headings=bundle['excluded_structural_headings'],
                constraints=dict(canonical_updates=False, ddl=False, claim_structure_review_state='recorded/deferred: actual schema enum', event_dating_review_state='reviewed'))


def _guard_rows(plan, root, db, lock=False):
    require(plan.get('format_version') == 1 and plan.get('kind') == 'history_source_scoped_sidecars', 'Wrong plan kind/version')
    require(plan.get('implementation_sha256') == sha(Path(__file__).read_bytes()), 'Sidecar implementation changed after plan preparation')
    require(plan['target_fingerprint'] == db.target_fingerprint, 'Target fingerprint changed')
    require(set(plan['inserts']) == set(FIELDS), 'Unexpected insert table')
    bundle=load_bundle(root,root/plan['batch_dir'])
    require(all(plan[k]==bundle['packet'][k] for k in ('book_key','source_version','volume')), 'Plan packet book/version/volume mismatch')
    require(bundle['files']==plan['protected_paths'] and bundle['batch']['batch_key']==plan['batch_key'] and bundle['publication']['batch_sha256']==plan['batch_sha256'], 'Plan is not completely bound to current verified volume archives')
    require(plan['excluded_structural_headings']==bundle['excluded_structural_headings'], 'Unused structural heading exclusion changed')
    db.schema()
    for relative, digest in plan['protected_paths'].items():
        path = (root/relative).resolve()
        require(root.resolve() in path.parents and sha(path.read_bytes()) == digest, 'Protected archive changed: '+relative)
    for p in plan['protected_rows']:
        require(p['table'] not in FIELDS, 'Sidecar row cannot serve as a canonical guard')
        require(db.get(p['table'], p['identity'], lock=lock) == p['row'], 'Protected old value changed: '+p['table']+'/'+str(p['identity']))
    counts = {t:dict(new=0, existing=0) for t in FIELDS}
    for table, rows in plan['inserts'].items():
        seen = set()
        for row in rows:
            require(set(row) == set(FIELDS[table]), 'Unexpected sidecar columns: '+table)
            identity = {k:row[k] for k in IDENTITY[table]}; token = tuple(identity.values())
            require(token not in seen, 'Duplicate planned sidecar identity'); seen.add(token)
            old = db.get(table,identity,lock=lock)
            require(old is None or all(old.get(k) == v for k,v in row.items()), 'Insert-only identity conflict: '+table+'/'+str(identity))
            counts[table]['existing' if old else 'new'] += 1
    # Fingerprints are recomputed from the guarded live published claims and source URLs.
    claims = {p['row']['id']:p['row'] for p in plan['protected_rows'] if p['table']=='fact_claim'}
    sources = {p['row']['id']:p['row'] for p in plan['protected_rows'] if p['table']=='source'}
    events = {p['row']['id']:p['row'] for p in plan['protected_rows'] if p['table']=='event'}
    for row in plan['inserts']['event_dating']:
        require(row['event_id'] in events and events[row['event_id']]['status']=='published', 'Dating event lacks immutable published old-value guard')
        claim = claims[row['claim_id']]
        require(claim['subject_table']=='event' and claim['subject_id']==row['event_id'], 'Wrong dating owner')
        require(row['claim_sha256']==claim_fingerprint(claim,sources[claim['source_id']]['url']), 'Stale claim fingerprint')
        require(row['review_state']=='reviewed', 'Dating was not reviewed')
        require(row['precision_kind'] in ('year','approximate','range','relative','era','unknown') and isinstance(row['basis'],str) and row['basis'].strip(), 'Invalid dating precision/basis')
        if row['precision_kind']=='era':require(isinstance(row['era_key'],str) and bool(row['era_key'].strip()), 'Era dating lacks authored era')
        for y in (row['earliest_year'],row['latest_year']):year(y)
        require(row['earliest_year'] is None or row['latest_year'] is None or row['earliest_year']<=row['latest_year'], 'Reversed planned dating')
        if row['precision_kind'] in ('year','range','approximate'):
            require(row['earliest_year'] is not None and row['latest_year'] is not None, 'Missing planned numerical bounds')
        if row['precision_kind']=='year':require(row['earliest_year']==row['latest_year'],'Year bounds disagree')
    for row in plan['inserts']['claim_structure']:
        require(row['claim_id'] in claims, 'Structure lacks published claim guard')
        claim=claims[row['claim_id']]; quote,review=parse_note(claim['note'])
        require(row['note_sha256']==sha(claim['note'].encode('utf-8')) and row['quote_text']==quote and row['review_note']==review, 'Structure is not bound to exact published note')
        require(row['review_state'] in ('recorded','deferred'), 'Unsupported authored structure state')
    texts={(p['row']['source_id'],p['row']['archive_url_sha256']):p['row'] for p in plan['protected_rows'] if p['table']=='source_text'}
    paragraphs={p['row']['id']:p['row'] for p in plan['protected_rows'] if p['table']=='library_paragraph'}
    books={p['row']['book_key']:p['row'] for p in plan['protected_rows'] if p['table']=='library_book'}
    for row in plan['inserts']['library_source_link']:
        require(row['source_id'] in sources, 'Link lacks published source guard')
        token=(row['source_id'],row['archive_url_sha256']);require(token in texts, 'Link lacks exact source_text guard')
        text=texts[token]; source=sources[row['source_id']]
        require(row['archive_url_sha256']==sha(source['url'].encode('utf-8')) and text['archive_url']==source['url'], 'Link URL fingerprint mismatch')
        require(row['snapshot_sha256']==text['content_sha256']==sha(text['content'].encode('utf-8')), 'Link snapshot hash mismatch')
        require(row['paragraph_id'] in paragraphs,'Link lacks bound library paragraph guard')
        para=paragraphs[row['paragraph_id']];book=books[para['book_key']]
        loc=plan['source_locations'][row['source_id']]
        require(exact_text_with_structural_edges(text['content'],para['content']) and para['content_sha256']==sha(para['content'].encode('utf-8')), 'Link paragraph bytes differ')
        require(book['status']=='available' and loc==dict(paragraph_id=para['id'],book_key=para['book_key'],section_id=para['section_id'],source_version=book['source_version']), 'Link book/version provenance mismatch')
    return counts


def http_json(url):
    request=urllib.request.Request(url,headers={'Accept':'application/json'})
    with urllib.request.urlopen(request,timeout=40) as response:
        return json.load(response)


def verify_public(plan, base, getter=http_json):
    require(base.startswith('https://'), 'Anonymous verification requires HTTPS')
    base=base.rstrip('/'); checks={}; dates={}
    for row in plan['inserts']['event_dating']:dates.setdefault(row['event_id'],[]).append(row)
    protected_events={p['row']['id']:p['row'] for p in plan['protected_rows'] if p['table']=='event'}
    def entry_check(eid):
        entry=getter(base+'/entry/'+eid)
        # Controller/service returns the entry itself, not an admin/SQL projection.
        require(entry.get('id')==eid and entry.get('type')=='event', 'Anonymous event entry missing')
        for k in ('start_year','end_year','time_original'):
            require(entry.get(k)==protected_events[eid].get(k),'Canonical public date unexpectedly changed')
        actual={r['id']:r for r in entry.get('datings',[])}
        for row in dates[eid]:
            expected={k:v for k,v in row.items() if k not in ('claim_sha256','precision_kind')}
            expected['precision']=row['precision_kind']
            require(row['id'] in actual and all(actual[row['id']].get(k)==v for k,v in expected.items()),'Reviewed dating absent or changed in anonymous entry: '+row['id'])
        return eid
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        checks['event_entries']=len(list(pool.map(entry_check,sorted(dates))))
    structures={r['claim_id']:r for r in plan['inserts']['claim_structure']}
    claims={p['row']['id']:p['row'] for p in plan['protected_rows'] if p['table']=='fact_claim'}
    verified=set(); claim_ids=sorted(structures)
    for offset in range(0,len(claim_ids),50):
        group=claim_ids[offset:offset+50]; found={}
        for page in range(30):
            query=urllib.parse.urlencode({'ids':','.join(group),'limit':50,'page':page})
            result=getter(base+'/catalog/fact_claim?'+query)
            for row in result['items']:found[row['id']]=row
            if not result.get('has_more'):break
        require(set(found)==set(group),'Anonymous claim readback missing/extra IDs')
        for cid,row in found.items():
            claim=claims[cid]; structure=structures[cid]; ev=row.get('evidence',{})
            require(ev.get('origin')=='structured' and ev.get('quote')==structure['quote_text'] and ev.get('review')==structure['review_note'] and ev.get('review_state')==structure['review_state'],'Anonymous structured evidence mismatch: '+cid)
            require(all(row.get(k)==claim[k] for k in FINGERPRINT_FIELDS),'Anonymous claim content changed')
            loc=plan['source_locations'][claim['source_id']]
            require(all(ev.get('location',{}).get(k)==v for k,v in loc.items()),'Original-text evidence location missing: '+cid)
            verified.add(cid)
    checks['claims_with_original_locations']=len(verified)
    checks['reviewed_datings']=sum(map(len,dates.values()))
    checks['canonical_public_dates_unchanged']=True
    return checks



BATCH_SIZE=100


def token(identity):
    require(isinstance(identity,dict) and bool(identity),'Empty bulk identity')
    return tuple(sorted(identity.items()))


def unique_read_set(pairs):
    """Deduplicate intended shared guards (e.g. one book for many paragraphs).

    Planned insert identities are still separately checked by _guard_rows;
    this read-set normalization never drops a planned row or validation.
    """
    result={}
    for table,identity in pairs:
        result.setdefault(table,{})[token(identity)]=dict(identity)
    return {t:list(rows.values()) for t,rows in result.items()}


class Database(_RowDatabase):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._phase=None
        self.bulk_statistics=dict(select_batches=0,insert_batches=0,rows_requested=0)

    def _select_many(self,table,identities,lock):
        import pymysql
        columns=tuple(sorted(identities[0]))
        require(all(tuple(sorted(x))==columns for x in identities),'Mixed bulk identity columns')
        where=' OR '.join('('+' AND '.join(self.store.column(table,k)+'=%s' for k in columns)+')' for _ in identities)
        params=[identity[k] for identity in identities for k in columns]
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM `'+table+'` WHERE '+where+(' FOR UPDATE' if lock else ''),params)
            rows=cursor.fetchall()
        self.bulk_statistics['select_batches']+=1
        return [self.store.normalize(table,row) for row in rows]

    def select_many(self,table,identities,lock=False):
        require(table in READ_TABLES,'Table outside bounded bulk read set')
        require(not lock or self.writable,'Read-only bulk preparation cannot lock rows')
        identities=[dict(x) for x in identities]
        wanted={token(x):x for x in identities}
        require(len(wanted)==len(identities),'Duplicate bulk read identity')
        for identity in identities:
            require(all(k in self.store.columns.get(table,()) for k in identity),'Invalid bulk identity column')
        out={key:None for key in wanted}
        ordered=sorted(identities,key=lambda x:repr(token(x)))
        self.bulk_statistics['rows_requested']+=len(ordered)
        for start in range(0,len(ordered),BATCH_SIZE):
            group=ordered[start:start+BATCH_SIZE]
            columns=tuple(group[0])
            group_keys={token(x) for x in group};found=set()
            for row in self._select_many(table,group,lock):
                identity={k:row[k] for k in columns};key=token(identity)
                require(key in group_keys,'Unrequested row returned by bounded bulk read')
                require(key not in found,'Duplicate row returned for bulk identity')
                found.add(key);out[key]=row
        return out

    @contextmanager
    def phase(self,lock=False):
        require(self._phase is None,'Nested materialized read phases are not allowed')
        self._phase=dict(lock=lock,rows={})
        try:yield self
        finally:self._phase=None  # never retain stale or negative results for another phase

    def preload(self,read_set):
        require(self._phase is not None,'Bulk preloading requires an explicit read phase')
        for table in sorted(read_set):
            identities=read_set[table]
            rows=self.select_many(table,identities,self._phase['lock'])
            for ident,row in rows.items():
                key=(table,ident)
                require(key not in self._phase['rows'],'Identity was loaded twice in one materialized phase')
                self._phase['rows'][key]=copy.deepcopy(row)

    def get(self,table,identity,lock=False):
        if self._phase is None:
            return super().get(table,identity,lock=lock)
        require(lock==self._phase['lock'],'Materialized phase lock mode mismatch')
        key=(table,token(identity))
        require(key in self._phase['rows'],'Missing explicit bulk read-set identity: '+table+'/'+str(identity))
        return copy.deepcopy(self._phase['rows'][key])

    def _insert_many(self,table,rows):
        cols=list(FIELDS[table])
        sql='INSERT INTO `'+table+'` ('+','.join(self.store.column(table,k) for k in cols)+') VALUES ('+','.join('%s' for _ in cols)+')'
        values=[[self.store.value(table,k,row[k]) for k in cols] for row in rows]
        with self.connection.cursor() as cursor:cursor.executemany(sql,values)
        self.bulk_statistics['insert_batches']+=1

    def insert_many(self,table,rows):
        require(self.writable and table in FIELDS,'Only allowed sidecar INSERT batches are permitted')
        require(self._phase is None,'Do not mutate while holding materialized read results')
        seen=set()
        for row in rows:
            require(set(row)==set(FIELDS[table]),'Unexpected bulk sidecar columns')
            identity=token({k:row[k] for k in IDENTITY[table]})
            require(identity not in seen,'Duplicate bulk insert identity');seen.add(identity)
        for start in range(0,len(rows),BATCH_SIZE):self._insert_many(table,rows[start:start+BATCH_SIZE])


def preload_prepare(bundle,db):
    """Known IDs come only from the bound batch; assets are a second dependent read."""
    ids=bundle['ids'];batch=bundle['batch'];used=used_sources(bundle)
    by_source={m['key']:pid for pid,m in bundle['manifest'].items()}
    pairs=[]
    pairs += [('fact_claim',dict(id=ids[c['key']])) for c in batch['claims']]
    pairs += [('event',dict(id=ids[x['row']['key']])) for x in bundle['cur']['items'] if x['group']=='events']
    for sk in sorted(used):
        require(sk in by_source,'Used source has no exact manifest paragraph')
        pid=by_source[sk];para=bundle['paras'][pid];url=bundle['sources'][sk]['url']
        pairs += [('source',dict(id=ids[sk])),('source_text',dict(source_id=ids[sk],archive_url_sha256=sha(url.encode('utf-8')))),('library_paragraph',dict(id=pid)),('library_book',dict(book_key=para['book_key']))]
    db.preload(unique_read_set(pairs))
    assets=[]
    for sk in sorted(used):
        pid=by_source[sk];row=db.get('library_paragraph',dict(id=pid))
        if row is not None:assets.append(('library_asset',dict(id=row['asset_id'])))
    db.preload(unique_read_set(assets))


def prepare(bundle,db):
    db.schema()
    with db.phase(lock=False):
        preload_prepare(bundle,db)
        plan=_prepare_rows(bundle,db)
    plan['bulk_execution']=dict(mode='bounded-materialized-phases',batch_size=BATCH_SIZE,
                                implementation_sha256=sha(Path(__file__).read_bytes()))
    return plan


def plan_read_set(plan):
    pairs=[(p['table'],p['identity']) for p in plan['protected_rows']]
    for table,rows in plan['inserts'].items():
        require(table in FIELDS,'Unexpected insert table')
        for row in rows:pairs.append((table,{k:row[k] for k in IDENTITY[table]}))
    return unique_read_set(pairs)


def engine_guard(plan):
    expected=dict(mode='bounded-materialized-phases',batch_size=BATCH_SIZE,
                  implementation_sha256=sha(Path(__file__).read_bytes()))
    require(plan.get('bulk_execution')==expected,'Sidecar bulk implementation changed after plan preparation')
    require(plan['implementation_sha256']==expected['implementation_sha256'],'Sidecar implementation binding differs')


def guard_plan(plan,root,db,lock=False,with_missing=False):
    engine_guard(plan)
    with db.phase(lock=lock):
        db.preload(plan_read_set(plan))
        counts=_guard_rows(plan,root,db,lock=lock)
        if with_missing:
            pending={table:[row for row in rows if db.get(table,{k:row[k] for k in IDENTITY[table]},lock=lock) is None] for table,rows in plan['inserts'].items()}
            return counts,pending
        return counts


def apply_plan(plan,root,db):
    """Same guarded transaction boundary and row guards, with bounded SQL round trips."""
    require(db.writable,'Apply requires the global publisher lock')
    engine_guard(plan);db.assert_publish_lock();db.connection.begin()
    try:
        before,pending=guard_plan(plan,root,db,lock=True,with_missing=True)
        inserted={t:0 for t in FIELDS}
        for table in ('library_source_link','claim_structure','event_dating'):
            db.insert_many(table,pending[table]);inserted[table]=len(pending[table])
        # A fresh locking read phase, never the pre-insert materialized values.
        after=guard_plan(plan,root,db,lock=True)
        require(all(x['new']==0 for x in after.values()),'Inserted rows did not read back exactly')
        db.connection.commit()
        return dict(before=before,actual_inserted=inserted,after=after,committed=True)
    except BaseException:
        db.connection.rollback();raise



def atomic_write(path, raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    require(not path.is_symlink(),'Workflow output cannot be a symlink')
    tmp=path.with_name(path.name+'.tmp')
    require(not tmp.exists(),'Workflow temporary file already exists')
    try:
        with tmp.open('xb') as stream:stream.write(raw)
        tmp.replace(path)
    finally:
        if tmp.exists():tmp.unlink()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch_dir',type=Path)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--mysql-env',type=Path)
    parser.add_argument('--public-api-url',default='https://histree.wiki/api/v1')
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--refresh-plan',action='store_true')
    action=parser.add_mutually_exclusive_group()
    action.add_argument('--apply',action='store_true')
    action.add_argument('--verify-public',action='store_true')
    parser.add_argument('--expected-plan-sha256')
    parser.add_argument('--expected-target-fingerprint')
    args=parser.parse_args(argv);root=args.root.resolve();batch_dir=args.batch_dir.resolve()
    require(root in batch_dir.parents,'Batch directory must be inside --root')
    out=batch_dir/'.workflow'
    require(not out.is_symlink(),'Workflow directory cannot be a symlink')
    planpath=(args.plan or out/'sidecars-plan.json').resolve()
    require(planpath.parent==out.resolve(),'Plan must be in this batch directory/.workflow')
    receiptpath=out/'sidecars-receipt.json'
    require(planpath!=receiptpath.resolve(),'Plan and receipt paths must differ')
    # Every action validates frozen publication/packet binding before connecting.
    bundle=load_bundle(root,batch_dir)
    prior=json.loads(receiptpath.read_bytes()) if receiptpath.exists() else None
    if args.apply or args.verify_public:
        require(planpath.is_file(),'Prepare an immutable sidecar plan first')
        raw=planpath.read_bytes();digest=sha(raw);plan=json.loads(raw);engine_guard(plan)
        require(plan['batch_dir']==str(batch_dir.relative_to(root)),'Plan batch directory mismatch')
        require(all(plan[k]==bundle['packet'][k] for k in ('book_key','source_version','volume')),'Plan packet book/version/volume mismatch')
        require(not args.refresh_plan,'Cannot refresh while applying/verifying')
        if args.apply:require(args.expected_plan_sha256==digest,'--apply requires exact --expected-plan-sha256')
        if prior:require(prior['plan_sha256']==digest and prior['batch_sha256']==plan['batch_sha256'],'Receipt/plan/batch mismatch')
    else:
        require(not prior or not args.refresh_plan,'Cannot replace a plan with an existing receipt')
    db=Database(root,args.mysql_env or root/'.env.migration.local',writable=args.apply)
    try:
        require(not args.expected_target_fingerprint or db.target_fingerprint==args.expected_target_fingerprint,'Target differs from frozen review')
        if args.apply:
            result=apply_plan(plan,root,db)
            receipt=dict(plan_sha256=digest,target_fingerprint=db.target_fingerprint,
                         batch_sha256=plan['batch_sha256'],batch_dir=plan['batch_dir'],
                         book_key=plan['book_key'],source_version=plan['source_version'],volume=plan['volume'],
                         status='committed_pending_anonymous_verification',verified=False,**result)
            atomic_write(receiptpath,dump(receipt))
        elif args.verify_public:
            require(prior is not None,'No committed receipt to verify');receipt=prior
            require(receipt.get('committed') and receipt['plan_sha256']==digest and receipt['target_fingerprint']==db.target_fingerprint,'Receipt/plan/target mismatch')
            guard_plan(plan,root,db)
        else:
            plan=prepare(bundle,db);raw=dump(plan);digest=sha(raw)
            if planpath.exists() and not args.refresh_plan:
                require(planpath.read_bytes()==raw,'Existing plan differs; review or explicitly --refresh-plan before any commit')
            counts=guard_plan(plan,root,db);db.connection.rollback()
            atomic_write(planpath,raw)
            print(json.dumps(dict(read_only=True,batch_dir=str(batch_dir),book_key=plan['book_key'],source_version=plan['source_version'],volume=plan['volume'],plan=str(planpath),plan_sha256=digest,counts=counts,skipped_independent_dates=len(plan['skipped_independent_dates']),bulk_statistics=db.bulk_statistics),ensure_ascii=False))
            return 0
    finally:db.connection.close()
    try:
        receipt['anonymous_checks']=verify_public(plan,args.public_api_url)
        receipt.update(status='complete',verified=True,anonymous_readback_verified=True)
    except Exception as error:
        receipt.update(status='committed_anonymous_verification_failed',verified=False,anonymous_error=str(error))
        atomic_write(receiptpath,dump(receipt));raise
    atomic_write(receiptpath,dump(receipt))
    print(json.dumps(dict(batch_dir=plan['batch_dir'],plan_sha256=digest,receipt=str(receiptpath),verified=True,anonymous_checks=receipt['anonymous_checks']),ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
