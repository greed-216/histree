"""Self-contained contract tests; temporary synthetic books only, no network/DB."""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
import uuid
import sys
from pathlib import Path

MODULE = Path(__file__).with_name('history_claim_revision_projection.py')
SPEC = importlib.util.spec_from_file_location('claim_projection_under_test', MODULE)
P = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(P)


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.books = {'alpha': ('甲书', ('alpha-',)), 'beta': ('乙书', ('beta-',))}
        self.keys = {self.ident(k): k for k in [
            'claim_one', 'claim_two', 'claim_ghost', 'alpha-source', 'beta-source',
            'person_one', 'person_two', 'event_two']}
        self.row = dict(id=self.ident('claim_one'), subject_table='person',
                        subject_id=self.ident('person_one'), field_path='description',
                        claim_text='合成事实', source_id=self.ident('alpha-source'),
                        citation='甲书一', note='原文：甲；核对说明：合成测试',
                        confidence=None, status='published', created_at='2026-01-01')
        self.indexes = {'alpha': {'claim_one': dict(
            claim_key='claim_one', source_key='alpha-source', subject_key='person_one',
            subject_table='person', citation='甲书一', batch_files=['frozen/a.json'],
            extra={'nested': [1, {'keep': True}]})}, 'beta': {
                'untouched': {'claim_key': 'untouched', 'extra': ['keep other book']}}}
        for name in ['frozen/a.json', 'content/books/alpha/progress.json', 'content/books/beta/progress.json']:
            f = self.root / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('{"sentinel":true}\n')

    def ident(self, key):
        return str(uuid.uuid5(P.NS, key))

    def update(self, full=None, **after):
        full = copy.deepcopy(self.row if full is None else full)
        return dict(table='fact_claim', id=full['id'], key=self.keys[full['id']],
                    before={k: full[k] for k in after}, after=after, full_before=full)

    def write(self, name='one', updates=None, new=None, kind=P.KIND, verified=True,
              anonymous=True, plan_patch=None, receipt_patch=None):
        plan = dict(kind=kind, target_fingerprint='a'*64, updates=updates or [],
                    key_map=copy.deepcopy(self.keys), new_claims=new or [])
        plan.update(plan_patch or {})
        path = self.root / 'content/revisions' / name / 'plan.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = (json.dumps(plan, ensure_ascii=False, indent=2)+'\n').encode()
        path.write_bytes(raw)
        receipt = dict(verified=verified, anonymous_readback_verified=anonymous,
                       target_fingerprint=plan['target_fingerprint'],
                       plan_sha256=hashlib.sha256(raw).hexdigest(),
                       audit=dict(inserts=dict(fact_claim=len(plan['new_claims']))))
        receipt.update(receipt_patch or {})
        self.save_receipt(path, receipt)
        return path

    def save_receipt(self, path, receipt):
        path.with_name('publication-mysql.json').write_text(json.dumps(receipt)+'\n')

    def project(self, indexes=None, books=None):
        return P.project_claim_revisions(self.root, self.indexes if indexes is None else indexes,
                                         self.books if books is None else books)

    def new(self):
        return dict(self.row, id=self.ident('claim_two'), source_id=self.ident('beta-source'))

    def test_no_revisions_returns_deep_copy(self):
        result = self.project()
        self.assertEqual(result, self.indexes)
        result['alpha']['claim_one']['extra']['nested'].append(2)
        self.assertEqual(len(self.indexes['alpha']['claim_one']['extra']['nested']), 2)

    def test_citation_projection_preserves_original_and_extras(self):
        path = self.write(updates=[self.update(citation='甲书校核')])
        before = copy.deepcopy(self.indexes)
        out = self.project(); row = out['alpha']['claim_one']
        self.assertEqual(self.indexes, before)
        self.assertEqual(row['citation'], '甲书校核')
        self.assertEqual(row['batch_files'], ['frozen/a.json'])
        self.assertEqual(row['extra'], before['alpha']['claim_one']['extra'])
        ref = str(path.relative_to(self.root))
        self.assertIn(ref, row['revision_files'])
        self.assertEqual(row['revision_plan_sha256s'][ref], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(out['beta'], before['beta'])

    def test_source_change_migrates_only_claim(self):
        self.write(updates=[self.update(source_id=self.ident('beta-source'))])
        out = self.project()
        self.assertNotIn('claim_one', out['alpha'])
        self.assertEqual(out['beta']['claim_one']['source_key'], 'beta-source')
        self.assertEqual(out['beta']['claim_one']['batch_files'], ['frozen/a.json'])
        self.assertEqual(out['beta']['untouched'], self.indexes['beta']['untouched'])

    def test_subject_uuid_and_table_project(self):
        self.write(updates=[self.update(subject_id=self.ident('event_two'), subject_table='event')])
        r = self.project()['alpha']['claim_one']
        self.assertEqual((r['subject_key'], r['subject_table']), ('event_two', 'event'))

    def test_new_claim_goes_to_its_source_book(self):
        self.write(new=[self.new()])
        out = self.project()
        self.assertEqual(out['beta']['claim_two']['subject_key'], 'person_one')
        self.assertEqual(out['beta']['claim_two']['batch_files'], [])
        self.assertEqual(out['alpha'], self.indexes['alpha'])

    def test_chain_order_comes_from_values_not_directory_names(self):
        first = self.update(citation='中间')
        second_row = dict(self.row, citation='中间')
        self.write('z-earlier', [first])
        self.write('a-later', [self.update(second_row, source_id=self.ident('beta-source'), citation='末值')])
        out = self.project()['beta']['claim_one']
        self.assertEqual(out['citation'], '末值')
        self.assertEqual(out['revision_files'], ['content/revisions/z-earlier/plan.json', 'content/revisions/a-later/plan.json'])

    def test_text_only_chain_is_valid_without_discarding_extras(self):
        self.write('z-first', [self.update(claim_text='甲')])
        self.write('a-second', [self.update(dict(self.row, claim_text='甲'), note='原文：乙；核对说明：复核')])
        out = self.project()['alpha']['claim_one']
        self.assertEqual(out['citation'], '甲书一')
        self.assertEqual(out['extra'], self.indexes['alpha']['claim_one']['extra'])
        self.assertEqual(len(out['revision_files']), 2)

    def test_new_claim_then_later_update(self):
        row = self.new()
        self.write('z-create', new=[row])
        self.write('a-update', updates=[self.update(row, source_id=self.ident('alpha-source'), citation='迁回甲')])
        self.assertEqual(self.project()['alpha']['claim_two']['citation'], '迁回甲')

    def test_projection_is_idempotent_with_verified_provenance(self):
        self.write(updates=[self.update(source_id=self.ident('beta-source'))], new=[self.new()])
        first = self.project()
        self.assertEqual(self.project(first), first)

    def test_old_revision_metadata_is_preserved(self):
        row = self.indexes['alpha']['claim_one']
        row.update(revision_files=['old/plan.json'], revision_plan_sha256='old-digest',
                   revision_plan_sha256s={'old/plan.json': 'old-digest'}, custom_extra={'x': [2]})
        self.write(updates=[self.update(citation='改')])
        out = self.project()['alpha']['claim_one']
        self.assertEqual(out['revision_plan_sha256'], 'old-digest')
        self.assertEqual(out['revision_plan_sha256s']['old/plan.json'], 'old-digest')
        self.assertEqual(out['custom_extra'], {'x': [2]})

    def test_unsupported_kind_is_ignored(self):
        self.write(kind='source_scoped_time_revision', receipt_patch={'plan_sha256': 'wrong'})
        self.assertEqual(self.project(), self.indexes)

    def test_no_receipt_is_ignored(self):
        p = self.write(updates=[self.update(citation='不可见')])
        p.with_name('publication-mysql.json').unlink()
        self.assertEqual(self.project(), self.indexes)

    def test_unverified_draft_is_ignored_even_with_invalid_keys(self):
        self.write(updates=[self.update(citation='不可见')], verified=False, anonymous=False,
                   plan_patch={'key_map': {'unknown': 'bad'}}, receipt_patch={'plan_sha256': 'wrong'})
        self.assertEqual(self.project(), self.indexes)

    def test_false_anonymous_acceptance_fails(self):
        self.write(updates=[self.update(citation='改')], anonymous=False)
        with self.assertRaisesRegex(ValueError, 'anonymous'): self.project()

    def test_missing_anonymous_acceptance_fails(self):
        p = self.write(); r = json.loads(p.with_name('publication-mysql.json').read_text());r.pop('anonymous_readback_verified');self.save_receipt(p,r)
        with self.assertRaisesRegex(ValueError, 'anonymous'): self.project()

    def test_plan_byte_tampering_fails(self):
        p = self.write(updates=[self.update(citation='改')]);p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'hash'): self.project()

    def test_target_mismatch_fails(self):
        self.write(receipt_patch={'target_fingerprint': 'b'*64})
        with self.assertRaisesRegex(ValueError, 'target'): self.project()

    def test_missing_target_cannot_match_two_nones(self):
        self.write(plan_patch={'target_fingerprint': None}, receipt_patch={'target_fingerprint': None})
        with self.assertRaisesRegex(ValueError, 'target'): self.project()

    def test_audit_insert_count_mismatch_fails(self):
        self.write(new=[self.new()], receipt_patch={'audit': {'inserts': {'fact_claim': 0}}})
        with self.assertRaisesRegex(ValueError, 'audit'): self.project()

    def test_missing_insert_audit_fails_even_for_updates_only(self):
        self.write(receipt_patch={'audit': {}})
        with self.assertRaisesRegex(ValueError, 'audit'): self.project()

    def test_boolean_insert_audit_fails(self):
        self.write(new=[self.new()], receipt_patch={'audit': {'inserts': {'fact_claim': True}}})
        with self.assertRaisesRegex(ValueError, 'audit'): self.project()

    def test_malformed_insert_audit_fails(self):
        self.write(receipt_patch={'audit': None})
        with self.assertRaisesRegex(ValueError, 'audit'): self.project()

    def test_uuid_key_mismatch_fails(self):
        keys = dict(self.keys);keys[self.ident('person_one')] = 'person_bad'
        self.write(plan_patch={'key_map':keys})
        with self.assertRaisesRegex(ValueError, 'stable UUID'): self.project()

    def test_unknown_after_source_uuid_fails(self):
        self.write(updates=[self.update(source_id=self.ident('absent-source'))])
        with self.assertRaisesRegex(ValueError, 'unknown UUID'): self.project()

    def test_unknown_before_subject_uuid_fails(self):
        row = dict(self.row, subject_id=self.ident('absent-person'))
        self.write(updates=[self.update(row,citation='改')])
        with self.assertRaisesRegex(ValueError, 'unknown UUID'): self.project()

    def test_update_key_mismatch_fails(self):
        u=self.update(citation='改');u['key']='claim_two';self.write(updates=[u])
        with self.assertRaisesRegex(ValueError, 'UUID/key'): self.project()

    def test_omitted_update_key_uses_bound_validated_uuid_map(self):
        u=self.update(subject_id=self.ident('person_two'));u.pop('key')
        path=self.write(updates=[u]);out=self.project()
        self.assertEqual(out['alpha']['claim_one']['subject_key'],'person_two')
        self.assertIn(str(path.relative_to(self.root)),out['alpha']['claim_one']['revision_files'])

    def test_omitted_update_key_cannot_invent_missing_uuid_mapping(self):
        u=self.update(citation='改');u.pop('key');keys=dict(self.keys);keys.pop(u['id'])
        self.write(updates=[u],plan_patch={'key_map':keys})
        with self.assertRaisesRegex(ValueError,'UUID/key'):self.project()

    def test_full_before_identity_mismatch_fails(self):
        u=self.update(citation='改');u['full_before']['id']=self.ident('claim_two');self.write(updates=[u])
        with self.assertRaisesRegex(ValueError, 'UUID/key'): self.project()

    def test_full_before_changed_field_mismatch_fails(self):
        u=self.update(citation='改');u['before']['citation']='错误旧值';self.write(updates=[u])
        with self.assertRaisesRegex(ValueError, 'full_before'): self.project()

    def test_before_after_field_sets_must_match(self):
        u=self.update(citation='改');u['after']['source_id']=self.ident('beta-source');self.write(updates=[u])
        with self.assertRaisesRegex(ValueError, 'changed fields'): self.project()

    def test_claim_uuid_cannot_change(self):
        self.write(updates=[self.update(id=self.ident('claim_two'))])
        with self.assertRaisesRegex(ValueError, 'cannot change'): self.project()

    def test_unknown_index_claim_fails(self):
        row=dict(self.row,id=self.ident('claim_ghost'));self.write(updates=[self.update(row,citation='改')])
        with self.assertRaisesRegex(ValueError, 'unknown indexed claim'): self.project()

    def test_index_before_projection_mismatch_fails(self):
        self.indexes['alpha']['claim_one']['citation']='非链中值';self.write(updates=[self.update(citation='改')])
        with self.assertRaisesRegex(ValueError, 'does not match correction'): self.project()

    def test_branch_fails(self):
        self.write('one',[self.update(citation='甲')]);self.write('two',[self.update(citation='乙')])
        with self.assertRaisesRegex(ValueError, 'branches'): self.project()

    def test_cycle_fails(self):
        self.write('one',[self.update(citation='甲')]);self.write('two',[self.update(dict(self.row,citation='甲'),citation='甲书一')])
        with self.assertRaisesRegex(ValueError, 'cycle'): self.project()

    def test_self_cycle_fails(self):
        self.write(updates=[self.update(citation='甲书一')])
        with self.assertRaisesRegex(ValueError, 'self cycle'): self.project()

    def test_disconnected_chains_fail(self):
        self.write('one',[self.update(citation='甲')]);self.write('two',[self.update(dict(self.row,citation='丙'),citation='丁')])
        with self.assertRaisesRegex(ValueError, 'disconnected'): self.project()

    def test_converging_chains_fail(self):
        self.write('one',[self.update(citation='乙')]);self.write('two',[self.update(dict(self.row,citation='丙'),citation='乙')])
        with self.assertRaisesRegex(ValueError, 'converges'): self.project()

    def test_duplicate_edge_fails(self):
        self.write('one',[self.update(citation='改')]);self.write('two',[self.update(citation='改')])
        with self.assertRaisesRegex(ValueError, 'repeats'): self.project()

    def test_new_claim_wrong_status_fails(self):
        self.write(new=[dict(self.new(),status='draft')])
        with self.assertRaisesRegex(ValueError, 'not published'): self.project()

    def test_new_claim_duplicate_across_plans_fails(self):
        self.write('one',new=[self.new()]);self.write('two',new=[self.new()])
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.project()

    def test_new_claim_collision_with_frozen_index_fails(self):
        self.write(new=[self.row])
        with self.assertRaisesRegex(ValueError, 'collides'): self.project()

    def test_new_claim_not_connected_to_later_update_fails(self):
        row=self.new();self.write('one',new=[row]);self.write('two',[self.update(dict(row,citation='异值'),citation='改')])
        with self.assertRaisesRegex(ValueError, 'does not connect'): self.project()

    def test_new_claim_missing_body_fails(self):
        row=self.new();row.pop('claim_text');self.write(new=[row])
        with self.assertRaisesRegex(ValueError, 'incomplete'): self.project()

    def test_ambiguous_source_book_fails(self):
        self.write(updates=[self.update(citation='改')]);books=dict(self.books,gamma=('丙书',('alpha-',)))
        with self.assertRaisesRegex(ValueError, 'ambiguous'): self.project(books=books)

    def test_unknown_source_book_fails(self):
        key='unconfigured-source';self.keys[self.ident(key)]=key;self.write(updates=[self.update(source_id=self.ident(key))])
        with self.assertRaisesRegex(ValueError, 'unknown or ambiguous'): self.project()

    def test_duplicate_input_claim_in_two_books_fails(self):
        self.indexes['beta']['claim_one']=copy.deepcopy(self.indexes['alpha']['claim_one']);self.write(updates=[self.update(citation='改')])
        with self.assertRaisesRegex(ValueError, 'multiple book'): self.project()

    def test_projected_values_without_provenance_fail(self):
        self.write(updates=[self.update(citation='改')]);self.indexes['alpha']['claim_one']['citation']='改'
        with self.assertRaisesRegex(ValueError, 'provenance'): self.project()

    def test_changed_index_revision_hash_fails(self):
        self.write(updates=[self.update(citation='改')]);out=self.project();r=out['alpha']['claim_one'];r['revision_plan_sha256s'][r['revision_files'][0]]='wrong'
        with self.assertRaisesRegex(ValueError, 'provenance'): self.project(out)

    def test_changed_singular_index_revision_hash_fails(self):
        self.write(updates=[self.update(citation='改')]);out=self.project();out['alpha']['claim_one']['revision_plan_sha256']='wrong'
        with self.assertRaisesRegex(ValueError, 'singular revision hash'): self.project(out)

    def test_no_files_or_progress_are_written(self):
        self.write(updates=[self.update(source_id=self.ident('beta-source'))])
        before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.project()
        after={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(after,before)

    def test_other_table_updates_are_not_projected(self):
        self.write(updates=[dict(table='person',id=self.ident('person_one'),after={'name':'别名'})])
        self.assertEqual(self.project(),self.indexes)

    def legacy_index(self):
        row = self.new()
        path = self.write('legacy', new=[row], kind='guarded_person_era_revision')
        # Actual older append-only formats have no UUID->key map or insert audit.
        plan = json.loads(path.read_text());plan.pop('key_map');path.write_text(json.dumps(plan,ensure_ascii=False))
        receipt = json.loads(path.with_name('publication-mysql.json').read_text())
        receipt.pop('audit');receipt['plan_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.save_receipt(path,receipt)
        record = dict(claim_key='claim_two', source_key='beta-source', subject_key='person_one',
                      subject_table='person', citation=row['citation'], batch_files=['frozen/independent.json'],
                      revision_files=[str(path.relative_to(self.root))],
                      revision_plan_sha256=receipt['plan_sha256'],extra={'keep':[1,{'deep':2}]})
        self.save_index(record)
        return path, record

    def save_index(self, record, book='beta'):
        p=self.root/'content/books'/book/'source-index.json';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(dict(book=self.books[book][0],claims=[record]),ensure_ascii=False))
        return p

    def retain(self, indexes=None, selected=('beta',)):
        return P.retain_verified_existing_claims(self.root,self.indexes if indexes is None else indexes,self.books,selected)

    def test_retain_verified_legacy_without_key_map_or_new_kind_audit(self):
        path,record=self.legacy_index();original=copy.deepcopy(self.indexes)
        out=self.retain();kept=out['beta']['claim_two']
        for k,v in record.items():self.assertEqual(kept[k],v)
        self.assertEqual(kept['revision_plan_sha256s'][str(path.relative_to(self.root))],record['revision_plan_sha256'])
        self.assertEqual(self.indexes,original)
        kept['extra']['keep'].append(3);self.assertEqual(len(record['extra']['keep']),2)

    def test_retain_skips_claim_already_in_any_other_book(self):
        path,record=self.legacy_index();receipt=json.loads(path.with_name('publication-mysql.json').read_text());receipt['verified']=False;self.save_receipt(path,receipt)
        indexes=copy.deepcopy(self.indexes);indexes['alpha']['claim_two']=dict(record,source_key='alpha-source')
        self.assertEqual(self.retain(indexes),indexes)
        self.assertNotIn('claim_two',self.retain(indexes)['beta'])

    def test_retain_only_selected_books_and_no_writes(self):
        self.legacy_index();bad=self.root/'content/books/alpha/source-index.json';bad.write_text('unrelated malformed index')
        before={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertIn('claim_two',self.retain()['beta'])
        after={str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)

    def test_retain_missing_index_returns_deep_copy(self):
        out=self.retain();self.assertEqual(out,self.indexes);self.assertIsNot(out,self.indexes)

    def test_retain_unverified_or_bad_acceptance_fails_closed(self):
        for patch in [{'verified':False},{'anonymous_readback_verified':False},
                      {'target_fingerprint':'b'*64},{'plan_sha256':'bad'}]:
            with self.subTest(patch=patch):
                path,_=self.legacy_index();r=json.loads(path.with_name('publication-mysql.json').read_text());r.update(patch);self.save_receipt(path,r)
                with self.assertRaises(ValueError):self.retain()

    def test_retain_changed_plan_bytes_fail(self):
        path,_=self.legacy_index();path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'hash'):self.retain()

    def test_retain_index_hash_and_missing_provenance_fail(self):
        for patch in [{'revision_plan_sha256':'wrong'}, {'revision_plan_sha256':None},
                      {'revision_files':[]}, {'revision_files':['../escape/plan.json']},
                      {'revision_plan_sha256s':{'content/revisions/legacy/plan.json':'wrong'}}]:
            with self.subTest(patch=patch):
                _,record=self.legacy_index();record.update(patch);self.save_index(record)
                with self.assertRaises(ValueError):self.retain()

    def test_retain_append_row_identity_fields_and_status_must_match(self):
        for field,value in [('source_id',self.ident('alpha-source')),('subject_id',self.ident('person_two')),
                            ('subject_table','event'),('citation','other citation'),('status','draft')]:
            with self.subTest(field=field):
                path,_=self.legacy_index();plan=json.loads(path.read_text());plan['new_claims'][0][field]=value;path.write_text(json.dumps(plan))
                r=json.loads(path.with_name('publication-mysql.json').read_text());r['plan_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.save_receipt(path,r)
                record=json.loads((self.root/'content/books/beta/source-index.json').read_text())['claims'][0];record['revision_plan_sha256']=r['plan_sha256'];self.save_index(record)
                with self.assertRaisesRegex(ValueError,'append-only claim row'):self.retain()

    def test_retain_unknown_key_source_book_and_uuid_fail(self):
        for patch in [{'claim_key':'claim_ghost'},{'source_key':'alpha-source'}, {'id':self.ident('claim_ghost')}]:
            with self.subTest(patch=patch):
                _,record=self.legacy_index();record.update(patch);self.save_index(record)
                with self.assertRaises(ValueError):self.retain()

    def test_retain_proof_must_have_exactly_one_append_row(self):
        for newrows in [[],[self.new(),self.new()]]:
            with self.subTest(count=len(newrows)):
                path,record=self.legacy_index();plan=json.loads(path.read_text());plan['new_claims']=newrows;path.write_text(json.dumps(plan));r=json.loads(path.with_name('publication-mysql.json').read_text());r['plan_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.save_receipt(path,r);record['revision_plan_sha256']=r['plan_sha256'];self.save_index(record)
                with self.assertRaisesRegex(ValueError,'append-only claim row'):self.retain()

    def test_retain_does_not_interpret_existing_claim_updates(self):
        path,record=self.legacy_index();plan=json.loads(path.read_text());plan['updates']=[self.update(self.new(),citation='update')];path.write_text(json.dumps(plan));r=json.loads(path.with_name('publication-mysql.json').read_text());r['plan_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.save_receipt(path,r);record['revision_plan_sha256']=r['plan_sha256'];self.save_index(record)
        with self.assertRaisesRegex(ValueError,'not append-only'):self.retain()

    def test_retain_every_cited_plan_needs_individual_proof(self):
        path,record=self.legacy_index();second=self.write('second',new=[self.new()],kind='another_append_kind',plan_patch={'reason':'second independent proof'})
        refs=record['revision_files']+[str(second.relative_to(self.root))];record['revision_files']=refs;record['revision_plan_sha256s']={ref:hashlib.sha256((self.root/ref).read_bytes()).hexdigest() for ref in refs};self.save_index(record)
        self.assertIn('claim_two',self.retain()['beta'])
        r=json.loads(second.with_name('publication-mysql.json').read_text());r['anonymous_readback_verified']=False;self.save_receipt(second,r)
        with self.assertRaisesRegex(ValueError,'acceptance'):self.retain()

    def test_retain_map_hash_without_singular_is_accepted(self):
        _,record=self.legacy_index();record['revision_plan_sha256s']={record['revision_files'][0]:record.pop('revision_plan_sha256')};self.save_index(record)
        self.assertIn('claim_two',self.retain()['beta'])

    def test_retain_can_precede_new_kind_projection_without_collision(self):
        _,record=self.legacy_index();path=self.write('new-kind',new=[self.new()]);record['revision_files']=[str(path.relative_to(self.root))];record['revision_plan_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();self.save_index(record)
        retained=self.retain();projected=self.project(retained)
        self.assertEqual(projected['beta']['claim_two']['extra'],record['extra'])
        self.assertEqual(projected,retained)


if __name__ == '__main__':
    unittest.main()
