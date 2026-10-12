import unittest
from publication_wait import queueing_factory
class FakeStore:
 target_fingerprint='reviewed'
 def __init__(self,env,writable,url):
  assert not writable
  self.writable=False;self.connection=self;self.closed=False;self.result=FakeStore.result;self.queries=[];FakeStore.last=self
 def cursor(self):return self
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def execute(self,sql):self.queries.append(sql)
 def fetchone(self):return (self.result,)
 def close(self):self.closed=True
class PublicationQueueTests(unittest.TestCase):
 def setUp(self):FakeStore.result=1
 def test_reads_stay_read_only(self):
  s=queueing_factory(FakeStore,'reviewed')('ignored',False);self.assertFalse(s.writable);self.assertEqual(s.queries,[])
 def test_same_connection_must_own_lock_before_writing(self):
  s=queueing_factory(FakeStore,'reviewed')('ignored',True);self.assertTrue(s.writable);self.assertIn("GET_LOCK('histree-content-publish',30)",s.queries[0]);self.assertFalse(s.closed)
 def test_timeout_or_wrong_target_disable_writes(self):
  for target,result in [('reviewed',0),('other',1)]:
   FakeStore.result=result
   with self.assertRaises(AssertionError):queueing_factory(FakeStore,target)('ignored',True)
   self.assertFalse(FakeStore.last.writable);self.assertTrue(FakeStore.last.closed)
if __name__=='__main__':unittest.main()
