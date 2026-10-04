import sys,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from history_identity import NAMESPACE,merged_identity_target
class MergeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.plan={'canonical_key':'person_existing','duplicate_key':'person_variant'}
        self.can=str(uuid.uuid5(NAMESPACE,self.plan['canonical_key']))
        self.dup=str(uuid.uuid5(NAMESPACE,self.plan['duplicate_key']))
        self.audit={'verified':True,'anonymous_readback_verified':True,'canonical_person_id':self.can,'hidden_duplicate_person_id':self.dup}
        self.people={self.can:{'status':'published'},self.dup:{'status':'draft'}}
    def test_completed_merge_allows_only_its_canonical_target(self):
        self.assertEqual(merged_identity_target(self.plan,self.audit,self.people),(self.dup,self.can))
    def test_unverified_merge_cannot_bypass_collision(self):
        self.audit['anonymous_readback_verified']=False
        self.assertIsNone(merged_identity_target(self.plan,self.audit,self.people))
    def test_wrong_ids_cannot_bypass_collision(self):
        self.audit['canonical_person_id']=self.dup
        with self.assertRaises(ValueError):merged_identity_target(self.plan,self.audit,self.people)
    def test_still_published_duplicate_cannot_bypass_collision(self):
        self.people[self.dup]['status']='published'
        with self.assertRaises(ValueError):merged_identity_target(self.plan,self.audit,self.people)
    def test_hidden_canonical_cannot_bypass_collision(self):
        self.people[self.can]['status']='draft'
        with self.assertRaises(ValueError):merged_identity_target(self.plan,self.audit,self.people)
if __name__=='__main__':unittest.main()
