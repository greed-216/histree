import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from revision_claim_index import NS, derive_time_revision_claims


class TimeRevisionIndexTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / 'content/revisions/review'
        self.folder.mkdir(parents=True)
        self.books = {'shiji': ('Shiji', ('shiji-',))}
        ids = {str(uuid.uuid5(NS, k)): k for k in ['claim_time', 'shiji-source', 'event_time']}
        rev = {v: k for k, v in ids.items()}
        self.plan = dict(kind='source_scoped_time_revision', target_fingerprint='target', key_map=ids,
                         new_claims=[dict(id=rev['claim_time'], source_id=rev['shiji-source'], subject_id=rev['event_time'],
                                          subject_table='event', citation='Volume 4', status='published')])
        self.path = self.folder / 'plan.json'
        self.path.write_text(json.dumps(self.plan))
        self.receipt = dict(verified=True, plan_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest(),
                            target_fingerprint='target', anonymous_readback_verified=True, inserts={'fact_claim': 1})

    def tearDown(self):
        self.temp.cleanup()

    def publish_receipt(self):
        (self.folder / 'publication-mysql.json').write_text(json.dumps(self.receipt))

    def test_draft_is_invisible(self):
        self.assertEqual(derive_time_revision_claims(self.root, self.books), {})

    def test_verified_rows_keep_stable_keys(self):
        self.publish_receipt()
        rows = derive_time_revision_claims(self.root, self.books)['shiji']
        self.assertEqual(rows['claim_time']['subject_key'], 'event_time')
        self.assertEqual(rows['claim_time']['source_key'], 'shiji-source')

    def test_changed_plan_is_rejected(self):
        self.publish_receipt()
        self.path.write_text(self.path.read_text() + ' ')
        with self.assertRaisesRegex(AssertionError, 'plan changed'):
            derive_time_revision_claims(self.root, self.books)

    def test_incomplete_readback_is_rejected(self):
        self.receipt['anonymous_readback_verified'] = False
        self.publish_receipt()
        with self.assertRaises(AssertionError): derive_time_revision_claims(self.root, self.books)

    def test_ambiguous_book_is_rejected(self):
        self.publish_receipt()
        self.books['duplicate'] = ('Duplicate', ('shiji-',))
        with self.assertRaisesRegex(AssertionError, 'ambiguous'):
            derive_time_revision_claims(self.root, self.books)
