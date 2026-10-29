"""Check authored temporal review coverage; never infer historical dates."""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(batch_path, curation_path):
    path = Path(batch_path)
    curation = json.loads(Path(curation_path).read_text())
    manifest = {m['paragraph_id']: m for m in json.loads((path.parent / 'sources/manifest.json').read_text())}
    items = [item for item in curation['items'] if item['group'] == 'events']
    rows = []
    for item in items:
        review = dict(item['temporal_review'], key=item['row']['key'])
        evidence = item['evidence'][0]
        review.setdefault('source_keys', [manifest[evidence['paragraph_id']]['key']])
        review.setdefault('quote', evidence['quote'])
        rows.append(review)
    result = {'format_version': 1, 'batch_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'events': rows}
    target = path.parent / 'time-review.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


def validate(batch_path):
    batch_path = Path(batch_path)
    batch = json.loads(batch_path.read_text())
    directory = batch_path.parent
    reused_path = directory / 'reused-keys.json'
    reused = set(json.loads(reused_path.read_text())) if reused_path.exists() else set()
    for person in batch.get('people', []):
        if person['key'] in reused:
            continue
        for field in ['birth_year', 'death_year']:
            if person.get(field) is not None:
                assert any(c['subject_key'] == person['key'] and c['field_path'] == field for c in batch['claims']), 'New person dates need date-field evidence'
    events = {row['key']: row for row in batch['events']}
    if not events:
        return {'events': 0}
    review = json.loads((directory / 'time-review.json').read_text())
    assert review['format_version'] == 1
    assert review['batch_sha256'] == hashlib.sha256(batch_path.read_bytes()).hexdigest(), 'Time review batch changed'
    rows = review['events']
    assert len(rows) == len(events) and {row['key'] for row in rows} == set(events), 'Every event needs one time review'
    manifest = {row['key']: row for row in json.loads((directory / 'sources/manifest.json').read_text())}
    claims = batch['claims']
    for item in rows:
        event = events[item['key']]
        assert item['decision'] in {'exact', 'range', 'relative', 'era', 'unknown', 'multiple', 'inherited', 'conflicting'}
        assert item.get('reason', '').strip() and item.get('anchor_note', '').strip(), 'Time review needs a specific explanation'
        assert item.get('quote') and item.get('source_keys'), 'Time review needs verbatim evidence'
        for key in item['source_keys']:
            m = manifest[key]
            raw = (directory / 'sources' / m['file']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == m['sha256'], 'Time source changed'
            assert item['quote'] in raw.decode('utf-8-sig'), 'Time quote is not in source'
        if item['decision'] == 'exact':
            year = item['year']
            assert isinstance(year, int) and not isinstance(year, bool) and year != 0 and abs(year) <= 10000
            assert event.get('start_year') == event.get('end_year') == year, 'Reviewed year not written to event'
            assert any(c['subject_key'] == item['key'] and c['field_path'] in {'start_year', 'end_year', 'time_original'} and c['source_key'] in item['source_keys'] for c in claims), 'Exact year needs a date-field claim'
        elif item['decision'] in {'era', 'unknown', 'multiple', 'conflicting', 'relative'}:
            assert event.get('start_year') is None and event.get('end_year') is None, 'Uncertain or multi-point material cannot assert one exact event interval'
        elif item['decision'] == 'range':
            if event.get('start_year') is not None or event.get('end_year') is not None:
                assert item.get('interval_kind') == 'duration', 'An estimated range is not an event duration'
                assert item.get('start_year') == event.get('start_year') and item.get('end_year') == event.get('end_year'), 'Duration review differs from event'
        elif item['decision'] == 'inherited':
            assert item['key'] in reused, 'A new event cannot borrow inherited status'
            assert item.get('comparison') in {'consistent', 'additional_detail', 'unresolved', 'conflicting'}, 'Compare inherited dates against the current source'
    return {'events': len(rows), 'batch_sha256': review['batch_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch')
    parser.add_argument('--from-curation', help='Build the bound review from authored item.temporal_review fields')
    args = parser.parse_args()
    if args.from_curation:
        prepare(args.batch, args.from_curation)
    print(json.dumps(validate(args.batch), ensure_ascii=False))
