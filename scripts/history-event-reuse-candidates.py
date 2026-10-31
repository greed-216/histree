"""Read-only existing-event candidates for newly curated events; never infer a merge."""
import argparse
import hashlib
import json
from pathlib import Path
import uuid

NS = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/greed-216/histree/content')


def select_scope(curation):
    reused = set(curation['reused_keys'])
    events = [i['row'] for i in curation['items']
              if i['group'] == 'events' and i['row']['key'] not in reused]
    keys = {r['key'] for r in events}
    years = set()
    for row in events:
        for field in ('start_year', 'end_year'):
            year = row.get(field)
            if year is not None:
                assert type(year) is int and year != 0, 'Invalid historical year'
                years.add(year)
    actors = {}
    for item in curation['items']:
        row = item['row']
        if item['group'] == 'person_events' and row['event_key'] in keys:
            actors.setdefault(row['event_key'], set()).add(str(uuid.uuid5(NS, row['person_key'])))
    return events, sorted(years), actors


def bounded_read(store, table, where, params, cap=5000):
    rows = []
    for offset in range(0, cap, 500):
        page = store.read(table, where, params, '*', 'r.id', 500, offset)
        rows.extend(page)
        if len(page) < 500:
            return rows
    raise ValueError('Candidate bound reached; narrow the batch instead of accepting a truncated review')


def collect(store, curation):
    events, years, actors = select_scope(curation)
    all_actors = sorted(set().union(*actors.values())) if actors else []
    memberships = []
    for offset in range(0, len(all_actors), 100):
        ids = all_actors[offset:offset + 100]
        memberships.extend(bounded_read(store, 'person_event',
            "r.status='published' AND r.person_id IN (" + ','.join('%s' for _ in ids) + ')', ids))
    actor_events = sorted({r['event_id'] for r in memberships})
    candidates = {}
    for column, values in [('start_year', years), ('end_year', years), ('id', actor_events)]:
        for offset in range(0, len(values), 100):
            chunk = values[offset:offset + 100]
            rows = bounded_read(store, 'event', "r.status='published' AND r." + column +
                                ' IN (' + ','.join('%s' for _ in chunk) + ')', chunk)
            candidates.update({r['id']: r for r in rows})
    by_event = {}
    for row in memberships:
        by_event.setdefault(row['event_id'], set()).add(row['person_id'])
    reviews = []
    for event in events:
        dates = {event.get('start_year'), event.get('end_year')} - {None}
        matches = []
        for row in candidates.values():
            basis = []
            if dates.intersection({row.get('start_year'), row.get('end_year')}):
                basis.append('same_known_year')
            if actors.get(event['key'], set()).intersection(by_event.get(row['id'], set())):
                basis.append('shared_actor')
            if basis:
                matches.append(dict(id=row['id'], candidate_basis=basis))
        reviews.append(dict(new_event_key=event['key'], candidates=matches,
                            decision=None, reason=None))
    return dict(new_events=events, years=years, events=list(candidates.values()),
                person_events=memberships, review=reviews,
                limitations=['Candidate selection is not identity or event adjudication.',
                             'Same year or actor does not imply the same action.',
                             'Undated events without a known shared actor require source/text review.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mysql-env', type=Path, required=True)
    parser.add_argument('--expected-target-fingerprint', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root, batch = args.root.resolve(), args.batch.resolve()
    assert root in batch.parents, 'Batch must be inside the explicit content root'
    path = batch / 'curation.json'
    raw = path.read_bytes()
    curated = json.loads(raw)
    select_scope(curated)  # Fail invalid years before opening any connection.
    output = (args.output or batch / '.workflow/event-reuse-candidates.json').resolve()
    assert batch in output.parents and not output.exists(), 'Use a new batch-local audit path; prior reviews are preserved'
    from mysql_content_store import MysqlContentStore
    store = MysqlContentStore(args.mysql_env)
    try:
        assert store.target_fingerprint == args.expected_target_fingerprint, 'Wrong database target'
        store.connection.rollback()
        with store.connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
        store.connection.begin()
        report = collect(store, curated)
        assert path.read_bytes() == raw, 'Curation changed during candidate lookup; rerun against the completed draft'
        report.update(read_only=True, target_fingerprint=store.target_fingerprint,
                      curation_sha256=hashlib.sha256(raw).hexdigest())
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(dict(new_events=len(report['new_events']), candidates=len(report['events']),
                              output=str(output), read_only=True)))
    finally:
        store.connection.rollback()
        store.connection.close()


if __name__ == '__main__':
    main()
