"""Validate a curated draft batch and its local source evidence; never writes to a database."""
import hashlib
import json
import math
from pathlib import Path
import sys

path = Path(sys.argv[1])
batch = json.loads(path.read_text())
assert batch['format_version'] == 1
required = {
    'people': ['key', 'name', 'description'],
    'events': ['key', 'title', 'description'],
    'person_events': ['key', 'person_key', 'event_key', 'role'],
    'person_relationships': ['key', 'person_a_key', 'person_b_key', 'relation_type', 'description'],
    'sources': ['key', 'title', 'source_type', 'edition', 'url'],
    'claims': ['key', 'subject_table', 'subject_key', 'field_path', 'claim_text', 'source_key', 'citation', 'note'],
    'topics': ['key', 'slug', 'title', 'description', 'sections'],
}
all_keys = set()
index = {}
for table, fields in required.items():
    assert isinstance(batch[table], list), table
    index[table] = {}
    for row in batch[table]:
        for field in fields:
            assert row.get(field), f'{table}: missing {field}'
        key = row['key']
        assert key not in all_keys, f'duplicate key: {key}'
        all_keys.add(key)
        index[table][key] = row
        if table != 'sources':
            assert row['status'] == 'draft', f'{key}: must remain draft'
for row in batch['people'] + batch['events']:
    for field in ['birth_year', 'death_year', 'start_year', 'end_year']:
        value = row.get(field)
        assert value is None or (type(value) is int and value != 0), (row['key'], field)
for row in batch['events']:
    start, end = row.get('start_year'), row.get('end_year')
    assert start is None or end is None or start <= end, row['key']
    lat, lng = row.get('location_lat'), row.get('location_lng')
    assert (lat is None) == (lng is None), row['key']
    if lat is not None:
        assert type(lat) in (int,float) and type(lng) in (int,float)
        assert math.isfinite(lat) and math.isfinite(lng)
        assert -90 <= lat <= 90 and -180 <= lng <= 180
    assert row['location_precision'] in ['site', 'approximate', 'region', 'unknown']
for row in batch['person_events']:
    assert row['person_key'] in index['people'] and row['event_key'] in index['events'], row['key']
for row in batch['person_relationships']:
    assert row['person_a_key'] in index['people'] and row['person_b_key'] in index['people'], row['key']
    assert row['person_a_key'] != row['person_b_key']
for row in batch['topics']:
    for section in row['sections']:
        assert section['heading'] and section['body']
        for key in section['node_keys']:
            assert key in index['people'] or key in index['events'], key
manifest = json.loads((path.parent / 'sources/manifest.json').read_text())
source_texts = {}
for item in manifest:
    raw = (path.parent / 'sources' / item['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256'], item['file']
    source_texts[item['key']] = raw.decode()
subjects = {'person':'people', 'event':'events', 'person_event':'person_events', 'person_relationship':'person_relationships'}
covered = set()
for row in batch['claims']:
    assert row['subject_table'] in subjects
    assert row['subject_key'] in index[subjects[row['subject_table']]], row['key']
    assert row['source_key'] in index['sources'] and row['source_key'] in source_texts, row['key']
    assert row['note'].startswith('原文：') and '；核对说明：' in row['note']
    quotation = row['note'][3:].split('；核对说明：', 1)[0]
    assert quotation and quotation in source_texts[row['source_key']], f'quote mismatch: {row["key"]}'
    covered.add(row['subject_key'])
for table in subjects.values():
    assert set(index[table]) <= covered, f'missing evidence: {table}'
for source in batch['sources']:
    assert source['url'].startswith('https://')
report = {'batch_key':batch['batch_key'], 'counts':{t:len(batch[t]) for t in required}, 'checks':['unique keys','valid references','all draft','valid years and coordinate pairs','source SHA-256','verbatim excerpts present','evidence for every entity and relation'], 'limitations':['Structural checks do not prove historical accuracy.','Human editorial review and geographical verification remain required.']}
print(json.dumps(report, ensure_ascii=False, indent=2))
