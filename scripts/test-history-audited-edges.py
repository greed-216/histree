"""Only verified, unchanged and claim-free archived duplicates are reusable exceptions."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from history_identity import audited_hidden_edge


class Store:
    target_fingerprint='a'*64
    def __init__(self,rows):self.rows=rows;self.calls=[]
    def read(self,table,where,params,selection,order,limit,offset):
        self.calls.append((table,where,params))
        if where=='r.id=%s':rows=[r for r in self.rows.get(table,[]) if r['id']==params[0]]
        elif where.startswith('r.id IN'):rows=[r for r in self.rows['fact_claim'] if r['id'] in params]
        else:rows=[r for r in self.rows['fact_claim'] if (r['subject_table'],r['subject_id'])==tuple(params)]
        return copy.deepcopy(rows[:limit])


class Audited(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.directory=self.root/'content/revisions/fixture';self.directory.mkdir(parents=True)
        self.shadow=dict(id='shadow',person_a='parent',person_b='child',relation_type='父亲',description='旧存根',status='draft')
        self.canonical=dict(self.shadow,id='canonical',description='规范关系',status='published')
        self.claim=dict(id='claim',subject_table='person_relationship',subject_id='canonical',source_id='source',status='published')
        before=dict(self.shadow,person_b='old-child',status='published');oldclaim=dict(self.claim,subject_id='shadow')
        self.plan=dict(kind='reviewed_history_correction',target_fingerprint=Store.target_fingerprint,updates=[dict(table='person_relationship',id='shadow',full_before=before,before=dict(person_b='old-child',status='published'),after=dict(person_b='child',status='draft')),dict(table='fact_claim',id='claim',full_before=oldclaim,before=dict(subject_id='shadow'),after=dict(subject_id='canonical'))],protected_rows=[dict(table='person_relationship',full_before=self.canonical)])
        self.receipt=dict(verified=True,anonymous_readback_verified=True,target_fingerprint=Store.target_fingerprint,after_rows=[dict(table='person_relationship',full_after=self.shadow),dict(table='person_relationship',full_after=self.canonical),dict(table='fact_claim',full_after=self.claim)])
        self.store=Store(dict(person_relationship=[self.shadow,self.canonical],fact_claim=[self.claim],person=[dict(id='parent',status='published'),dict(id='child',status='published')]));self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self):
        raw=json.dumps(self.plan).encode();(self.directory/'plan.json').write_bytes(raw);self.receipt['plan_sha256']=hashlib.sha256(raw).hexdigest();(self.directory/'publication-mysql.json').write_text(json.dumps(self.receipt))
    def check(self):return audited_hidden_edge(self.root,self.store,'person_relationship',dict(id='shadow',person_a='parent',person_b='child',relation_type='父亲'),'canonical')
    def test_verified_shadow_and_canonical_proofs_allow_existing_uuid_reuse(self):self.assertTrue(self.check())
    def test_active_or_unaudited_duplicate_is_still_blocked(self):
        self.shadow['status']='published';self.assertFalse(self.check());self.shadow['status']='draft';self.receipt['verified']=False;self.save();self.assertFalse(self.check())
    def test_target_and_plan_hash_must_match(self):
        self.store.target_fingerprint='b'*64;self.assertFalse(self.check());self.store.target_fingerprint='a'*64
        (self.directory/'plan.json').write_bytes((self.directory/'plan.json').read_bytes()+b' ');self.assertFalse(self.check())
    def test_shadow_and_canonical_full_rows_cannot_drift(self):
        self.shadow['description']='unreviewed';self.assertFalse(self.check());self.shadow['description']='旧存根'
        self.canonical['description']='unreviewed';self.assertFalse(self.check())
    def test_remaining_even_unpublished_claim_blocks_exception(self):
        self.store.rows['fact_claim'].append(dict(self.claim,id='left',subject_id='shadow',status='draft'));self.assertFalse(self.check())
    def test_transferred_claim_must_still_exist_on_the_canonical_edge(self):
        self.store.rows['fact_claim']=[];self.assertFalse(self.check())
        self.store.rows['fact_claim']=[dict(self.claim,subject_id='other')];self.assertFalse(self.check())
    def test_missing_receipt_transfer_or_role_rewrite_is_not_accepted(self):
        self.receipt['after_rows']=[r for r in self.receipt['after_rows'] if r['table']!='fact_claim'];self.save();self.assertFalse(self.check())
        self.receipt['after_rows'].append(dict(table='fact_claim',full_after=self.claim));self.plan['updates'][0]['full_before']['relation_type']='老师';self.save();self.assertFalse(self.check())
    def test_wrong_canonical_or_non_edge_table_never_exempted(self):
        self.assertFalse(audited_hidden_edge(self.root,self.store,'person_relationship',self.shadow,'other'))
        self.assertFalse(audited_hidden_edge(self.root,self.store,'person',self.shadow,'canonical'))
    def test_canonical_endpoint_must_be_public(self):
        self.store.rows['person'][0]['status']='draft';self.assertFalse(self.check())
    def test_claim_transfer_must_stay_in_the_same_subject_table(self):
        self.plan['updates'][1]['after']['subject_table']='person'
        self.receipt['after_rows'][-1]['full_after']=dict(self.claim,subject_table='person')
        self.save();self.assertFalse(self.check())
    def test_full_before_claim_owner_must_match_its_old_value_guard(self):
        self.plan['updates'][1]['full_before']['subject_id']='unrelated-edge'
        self.save();self.assertFalse(self.check())
    def test_shadow_before_must_match_its_full_before(self):
        self.plan['updates'][0]['before']['person_b']='unrelated-child'
        self.save();self.assertFalse(self.check())
    def test_older_receipt_binds_identity_without_inventing_a_canonical_prose_snapshot(self):
        self.plan['protected_rows']=[];self.receipt['after_rows']=[r for r in self.receipt['after_rows'] if not (r['table']=='person_relationship' and r['full_after']['id']=='canonical')];self.save();self.assertTrue(self.check())
        self.canonical['person_b']='other-child';self.assertFalse(self.check())


if __name__=='__main__':unittest.main()
