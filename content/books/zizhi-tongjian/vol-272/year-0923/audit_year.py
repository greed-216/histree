"""Audit all 923 body paragraphs and anonymous visibility of all eleven batches."""
import hashlib
import http.client
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'scripts/publish-book-batch.py').exists())
ledger = json.loads((HERE / 'paragraphs.json').read_text())
lines = (ROOT / 'resources/derived/tongjian/272.txt').read_text().splitlines()
assert len(ledger) == 76
assert [r['source_line'] for r in ledger] == list(range(6, 82))
assert all(r['text'] == lines[r['source_line'] - 1] for r in ledger)
assert all(r['status'] == 'published_verified' for r in ledger)
assert lines[4]=='同光元年癸未，公元九二三年'
assert len(lines)==81 or not any(t.strip() for t in lines[81:])
next_lines=(ROOT/'resources/derived/tongjian/273.txt').read_text().splitlines()
assert next_lines[4]=='同光二年甲申，公元九二四年'
assert next_lines[5].startswith('春，正月，甲辰，幽州奏契丹入寇')
next_ledger=json.loads((HERE.parent.parent/'vol-273/year-0924/paragraphs.json').read_text())
assert len(next_ledger)==76 and next_lines[81]=='◎' and next_lines[82]=='同光三年乙酉，公元九二五年'
assert [r['source_line'] for r in next_ledger]==list(range(6,82))
assert all(r['text']==next_lines[r['source_line']-1] for r in next_ledger)

groups = [('sources', 'source'), ('people', 'person'), ('events', 'event'),
          ('person_relationships', 'person_relationship'), ('person_events', 'person_event'),
          ('claims', 'fact_claim')]
ids_by_table = {table: set() for _, table in groups}
sha_by_batch = {}
covered = []
for part in sorted(HERE.glob('part-*')):
    data_path = part / 'content-batch.json'
    batch = json.loads(data_path.read_text())
    audit = json.loads((part / 'publication.json').read_text())
    sha = hashlib.sha256(data_path.read_bytes()).hexdigest()
    assert audit['verified'] and audit['batch_sha256'] == sha
    sha_by_batch[batch['batch_key']] = sha
    coverage = json.loads((part / 'coverage.json').read_text())
    covered.extend(coverage['paragraphs'])
    assert {key for r in ledger if r['id'] in coverage['paragraphs'] for key in r['event_keys']} == {r['key'] for r in batch['events']}
    assert all(next(r for r in ledger if r['id'] == pid)['batch_key'] == batch['batch_key']
               for pid in coverage['paragraphs'])
    mapping = json.loads((part / 'sql/key-map.json').read_text())
    for group, table in groups:
        ids_by_table[table].update(mapping[r['key']] for r in batch[group])
    for snapshot in json.loads((part / 'sources/manifest.json').read_text()):
        assert hashlib.sha256((part / 'sources' / snapshot['file']).read_bytes()).hexdigest() == snapshot['sha256']
assert len(sha_by_batch) == 11
assert covered == [r['id'] for r in ledger]

env = dict(s.split('=', 1) for s in (ROOT / 'apps/api/.env').read_text().splitlines()
           if '=' in s and not s.startswith('#'))
headers = {'apikey': env['SUPABASE_ANON_KEY'], 'Authorization': 'Bearer ' + env['SUPABASE_ANON_KEY']}
counts = {}
for table, row_ids in ids_by_table.items():
    expected = sorted(row_ids)
    actual = {}
    for offset in range(0, len(expected), 80):
        chunk = expected[offset:offset + 80]
        query = 'id=in.(' + ','.join(chunk) + ')&select=id'
        if table != 'source':
            query += ',status'
        if table == 'fact_claim':
            query += ',source:source_id(id,url)'
        request = urllib.request.Request(env['SUPABASE_URL'] + '/rest/v1/' + table + '?' + query,
                                         headers=headers)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=40) as response:
                    rows = json.load(response)
                break
            except (urllib.error.URLError, TimeoutError, http.client.RemoteDisconnected):
                if attempt == 2:
                    raise
                time.sleep(1)
        assert {r['id'] for r in rows} == set(chunk), table
        if table != 'source':
            assert all(r['status'] == 'published' for r in rows), table
        if table == 'fact_claim':
            assert all(r['source'] and r['source']['url'].startswith('https://github.com/greed-216/histree/blob/')
                       for r in rows)
        actual.update((r['id'], r) for r in rows)
    assert len(actual) == len(expected)
    counts[table] = len(actual)
result = dict(verified=True, at=datetime.now(timezone.utc).isoformat(), volume=272, year=923,
              body_paragraphs=76, excluded_non_body=0, body_source_lines=[6, 81], next_volume=273,
              next_year_header_line=5, next_body_source_line=6,
              batch_sha256=sha_by_batch, unique_public_counts=counts, anonymous_readback_verified=True)
(HERE / 'year-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(result)
