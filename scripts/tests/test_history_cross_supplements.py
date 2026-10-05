import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from history_cross_supplements import validate_cross_supplement

class CrossSupplementTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.year=self.root/'content/books/zizhi-tongjian/vol-290/year-0952';self.part=self.year/'part-04';self.part.mkdir(parents=True)
  self.batch={'batch_key':'old','people':[{'key':'person'}],'events':[],'person_relationships':[],'person_events':[]}
  self.write(self.part/'content-batch.json',self.batch)
  self.write(self.part/'publication.json',{'verified':True,'batch_sha256':hashlib.sha256((self.part/'content-batch.json').read_bytes()).hexdigest()})
  self.write(self.part/'coverage.json',{'paragraphs':['p032']})
  self.write(self.year/'paragraphs.json',[{'id':'p032','status':'published_verified','batch_key':'old'}])
  self.declared=[{'primary_paragraph_id':'p032','subject_key':'person'}]
 def write(self,path,data):path.write_text(json.dumps(data))
 def check(self):validate_cross_supplement(self.root,'p032','person',self.declared)
 def test_verified_reference(self):self.check()
 def test_undeclared(self):
  self.declared=[]
  with self.assertRaisesRegex(AssertionError,'Undeclared'):self.check()
 def test_unpublished(self):
  self.write(self.year/'paragraphs.json',[{'id':'p032','status':'reviewed','batch_key':'old'}])
  with self.assertRaisesRegex(AssertionError,'not published'):self.check()
 def test_subject_not_in_prior_batch(self):
  self.batch['people']=[];self.write(self.part/'content-batch.json',self.batch)
  self.write(self.part/'publication.json',{'verified':True,'batch_sha256':hashlib.sha256((self.part/'content-batch.json').read_bytes()).hexdigest()})
  with self.assertRaisesRegex(AssertionError,'subject is absent'):self.check()
 def test_modified_archive(self):
  self.write(self.part/'content-batch.json',dict(self.batch,changed=True))
  with self.assertRaisesRegex(AssertionError,'audit mismatch'):self.check()
 def test_incorrect_coverage(self):
  self.write(self.part/'coverage.json',{'paragraphs':['p033']})
  with self.assertRaisesRegex(AssertionError,'absent from previous coverage'):self.check()

if __name__=='__main__':unittest.main()
