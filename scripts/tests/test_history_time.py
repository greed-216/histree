import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('history_time', ROOT / 'scripts/validate-history-time.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TemporalReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'sources').mkdir()
        self.quote = 'Test king year two'
        raw = self.quote.encode()
        (self.root / 'sources/source.txt').write_bytes(raw)
        self.write('sources/manifest.json', [{'key': 'source', 'file': 'source.txt', 'sha256': hashlib.sha256(raw).hexdigest()}])
        self.batch = {'events': [{'key': 'event', 'start_year': -178, 'end_year': -178}], 'claims': [{'subject_key': 'event', 'field_path': 'start_year', 'source_key': 'source'}]}
        self.path = self.root / 'content-batch.json'
        self.write('content-batch.json', self.batch)
        self.review = {'format_version': 1, 'batch_sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(), 'events': [{'key': 'event', 'decision': 'exact', 'year': -178, 'reason': 'Explicit regnal year', 'anchor_note': 'Checked epoch -179; second year is -178', 'source_keys': ['source'], 'quote': self.quote}]}
        self.write('time-review.json', self.review)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value))

    def test_reviewed_year_and_date_claim_pass(self):
        self.assertEqual(module.validate(self.path)['events'], 1)

    def test_missing_review_is_rejected(self):
        (self.root / 'time-review.json').unlink()
        with self.assertRaises(FileNotFoundError): module.validate(self.path)

    def test_batch_change_requires_new_review(self):
        self.batch['events'][0]['start_year'] = -179
        self.write('content-batch.json', self.batch)
        with self.assertRaisesRegex(AssertionError, 'batch changed'): module.validate(self.path)

    def test_unwritten_year_is_rejected(self):
        self.review['events'][0]['year'] = -177
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'not written'): module.validate(self.path)

    def test_every_event_requires_review(self):
        self.review['events'] = []
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'Every event'): module.validate(self.path)

    def test_quote_and_snapshot_are_checked(self):
        self.review['events'][0]['quote'] = 'Unsupported text'
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'not in source'): module.validate(self.path)

    def test_multi_point_material_cannot_claim_a_single_interval(self):
        self.review['events'][0]['decision'] = 'multiple'
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'multi-point'): module.validate(self.path)

    def test_structurally_valid_but_unjustified_date_claim_is_rejected(self):
        self.batch['claims'][0]['field_path'] = 'description'
        self.write('content-batch.json', self.batch)
        self.review['batch_sha256'] = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'date-field claim'): module.validate(self.path)

    def test_authored_curation_builds_bound_review(self):
        value = dict(self.review['events'][0]);value.pop('key');value.pop('source_keys');value.pop('quote')
        self.write('curation.json', {'items': [{'group': 'events', 'row': {'key': 'event'}, 'evidence': [{'paragraph_id': 'p1', 'quote': self.quote}], 'temporal_review': value}]})
        data = json.loads((self.root / 'sources/manifest.json').read_text());data[0]['paragraph_id'] = 'p1';self.write('sources/manifest.json', data)
        module.prepare(self.path, self.root / 'curation.json')
        self.assertEqual(module.validate(self.path)['events'], 1)

    def test_estimated_range_cannot_become_a_duration(self):
        self.review['events'][0]['decision'] = 'range'
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'not an event duration'): module.validate(self.path)

    def test_new_event_cannot_claim_inherited_date(self):
        self.review['events'][0].update(decision='inherited', comparison='consistent')
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'borrow inherited'): module.validate(self.path)

    def test_new_person_date_requires_its_own_claim(self):
        self.batch['people'] = [{'key': 'person', 'death_year': -178}]
        self.write('content-batch.json', self.batch)
        with self.assertRaisesRegex(AssertionError, 'person dates'): module.validate(self.path)

    def test_relative_time_cannot_assert_an_exact_year(self):
        self.review['events'][0]['decision'] = 'relative'
        self.write('time-review.json', self.review)
        with self.assertRaisesRegex(AssertionError, 'multi-point'): module.validate(self.path)
