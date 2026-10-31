"""Candidate discovery catches year and actor variants without deciding a merge."""
import importlib.util
from pathlib import Path
import unittest
import uuid

spec = importlib.util.spec_from_file_location('candidates', Path(__file__).with_name('history-event-reuse-candidates.py'))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


class Store:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def read(self, table, where, values, selection, order, limit, offset):
        self.calls.append((table, where, values))
        column = next(c for c in ('person_id', 'start_year', 'end_year', 'id') if 'r.' + c + ' IN' in where)
        rows = [r for r in self.rows.get(table, []) if r.get(column) in values and r['status'] == 'published']
        return rows[offset:offset + limit]


class Candidates(unittest.TestCase):
    def curated(self):
        return dict(reused_keys=['event_reused'], items=[
            dict(group='events', row=dict(key='event_new', start_year=-124, end_year=None)),
            dict(group='events', row=dict(key='event_reused', start_year=-123, end_year=None)),
            dict(group='people', row=dict(key='person_actor')),
            dict(group='person_events', row=dict(key='pe_new', event_key='event_new', person_key='person_actor'))])

    def test_same_year_and_undated_shared_actor_are_discovered(self):
        actor = str(uuid.uuid5(M.NS, 'person_actor'))
        store = Store(dict(event=[dict(id='different-name', start_year=-124, end_year=None, status='published'),
                                  dict(id='undated', start_year=None, end_year=None, status='published'),
                                  dict(id='unrelated', start_year=-125, end_year=None, status='published'),
                                  dict(id='hidden', start_year=-124, end_year=None, status='draft')],
                           person_event=[dict(id='pe', person_id=actor, event_id='undated', status='published')]))
        result = M.collect(store, self.curated())
        self.assertEqual({r['id'] for r in result['events']}, {'different-name', 'undated'})
        self.assertEqual(result['review'][0]['decision'], None)
        self.assertEqual({r['id']: r['candidate_basis'] for r in result['review'][0]['candidates']},
                         {'different-name': ['same_known_year'], 'undated': ['shared_actor']})
        self.assertEqual(result['years'], [-124])
        self.assertTrue(all("status='published'" in call[1] for call in store.calls))

    def test_end_year_is_a_candidate_and_same_year_is_not_a_merge(self):
        store = Store(dict(event=[dict(id='duration', start_year=-130, end_year=-124, status='published')]))
        result = M.collect(store, self.curated())
        self.assertEqual(result['review'][0]['candidates'][0]['id'], 'duration')
        self.assertIsNone(result['review'][0]['decision'])
        self.assertIsNone(result['review'][0]['reason'])

    def test_no_new_events_does_not_scan_database(self):
        c = self.curated(); c['reused_keys'].append('event_new')
        store = Store({}); result = M.collect(store, c)
        self.assertEqual(result['events'], [])
        self.assertEqual(store.calls, [])

    def test_invalid_year_rejected(self):
        for year in (0, True, '124'):
            c = self.curated(); c['items'][0]['row']['start_year'] = year
            with self.assertRaises(AssertionError):
                M.select_scope(c)

    def test_candidate_limit_fails_instead_of_truncating(self):
        class Full:
            def read(self, *args): return [{'id': str(n)} for n in range(500)]
        with self.assertRaisesRegex(ValueError, 'truncated'):
            M.bounded_read(Full(), 'event', 'fixed', [], cap=500)


if __name__ == '__main__':
    unittest.main()
