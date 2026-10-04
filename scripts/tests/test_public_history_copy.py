"""Protect original quotations, relation endpoints and row-level concurrency guards."""
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('copy_review',Path(__file__).parents[1]/'review-public-history-copy.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class ReviewGuards(unittest.TestCase):
 def change(self,table='fact_claim',field='note'):
  return dict(table=table,id='known-id',before={field:'原文：繁體原文；核对说明：主所记。'},after={field:'原文：繁體原文；核对说明：《资治通鉴》的记载。'},baseline=dict(id='known-id',**{field:'原文：繁體原文；核对说明：主所记。'}),review='Explain internal abbreviation')
 def test_missing_baseline_is_rejected(self):
  c=self.change();c.pop('baseline')
  with self.assertRaises(AssertionError):mod.validate_changes([c])
 def test_quote_is_preserved(self):self.assertTrue(mod.validate_changes([self.change()]))
 def test_quote_rewrite_is_rejected(self):
  c=self.change();c['after']['note']='原文：繁体原文；核对说明：白话说明。'
  with self.assertRaises(AssertionError):mod.validate_changes([c])
 def test_relation_endpoint_is_rejected(self):
  c=self.change('person_relationship','person_a')
  with self.assertRaises(AssertionError):mod.validate_changes([c])
 def test_duplicate_row_plan_is_rejected(self):
  c=self.change()
  with self.assertRaises(AssertionError):mod.validate_changes([c,c])
 def test_dates_require_preservation_review(self):
  c=self.change('event','time_original')
  with self.assertRaises(AssertionError):mod.validate_changes([c])
 def test_concurrent_write_is_rejected(self):
  class Client:
   def request(self,*args):return [dict(id='known-id',note='Changed by another editor')]
  with self.assertRaises(AssertionError):mod.apply_change(Client(),self.change(),True)
 def test_successful_write_checks_full_protected_row(self):
  c=self.change();c['baseline']=dict(id='known-id',note=c['before']['note'],source_id='source',subject_id='original-subject')
  class Client:
   def request(self,table,query,payload=None):
    if payload is not None:return [dict(id='known-id',**payload)]
    if query['select']=='*':return [dict(c['baseline'],note=c['after']['note'],subject_id='wrong-subject')]
    return [dict(id='known-id',note=c['before']['note'])]
  with self.assertRaises(AssertionError):mod.apply_change(Client(),c,True)
 def test_old_value_guard_and_anonymous_readback(self):
  c=self.change();calls=[]
  class Client:
   def request(self,table,query,payload=None):
    calls.append((query,payload))
    if payload is not None:
     assert query['note']=='eq.'+c['before']['note']
     return [dict(id=c['id'],**payload)]
    return [dict(c['baseline'],**c['after'])]
  self.assertTrue(mod.apply_change(Client(),c,True)['verified'])
  self.assertEqual(len(calls),2)
  self.assertIsNotNone(calls[0][1]);self.assertIsNone(calls[1][1])
  self.assertEqual(calls[1][0]['select'],'*')
 def test_already_applied_empty_patch_needs_full_readback(self):
  c=self.change();calls=[]
  class Client:
   def request(self,table,query,payload=None):
    calls.append(payload)
    return [] if payload is not None else [dict(c['baseline'],**c['after'])]
  self.assertTrue(mod.apply_change(Client(),c,True)['verified'])
  self.assertEqual(len(calls),2)
 def test_uncertain_write_is_inspected_without_retry(self):
  c=self.change();calls=[]
  class Client:
   def request(self,table,query,payload=None):
    calls.append(payload)
    if payload is not None:raise TimeoutError('response lost after commit')
    return [dict(c['baseline'],**c['after'])]
  self.assertTrue(mod.apply_change(Client(),c,True)['verified'])
  self.assertEqual(sum(x is not None for x in calls),1)
 def test_empty_patch_with_concurrent_value_is_rejected(self):
  c=self.change()
  class Client:
   def request(self,table,query,payload=None):return [] if payload is not None else [dict(c['baseline'],note='Changed by another editor')]
  with self.assertRaises(AssertionError):mod.apply_change(Client(),c,True)
if __name__=='__main__':unittest.main()
