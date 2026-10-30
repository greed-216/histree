import gzip,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('coverage_projection',Path(__file__).resolve().parents[1]/'project-review-coverage.py');MODULE=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MODULE)
class ReviewCoverageTests(unittest.TestCase):
 def fixture(self,root,pending=True):
  def put(name,value):
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return p
  sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
  records=root/'resources/derived/history-library/fixture/paragraphs.jsonl.gz';records.parent.mkdir(parents=True)
  with gzip.open(records,'wt') as f:f.write(json.dumps({'id':'fixture-p000001','locator':{'raw_excerpt_sha256':'a'*64}})+'\n')
  put('resources/derived/history-library/catalog.json',{'books':[{'book_key':'fixture','source_version':'v1','paragraph_file':str(records.relative_to(root)),'paragraph_sha256':sha(records)}]})
  base='content/books/fixture/vol-001/from-start/';batch=put(base+'release-test/part-01/content-batch.json',{'sources':[]})
  put(base+'release-test/part-01/publication-mysql.json',{'verified':True,'batch_sha256':sha(batch)})
  put(base+'published-paragraphs.json',{'paragraphs':[{'paragraph_id':'fixture-p000001','status':'published_fact_subset_verified','editorial_status':'pending_textual_review' if pending else 'reviewed','publication_verified':True,'source_archive_verified':True,'pending_items':[{'reason':'Identity unresolved'}] if pending else [],'note':'Reviewed, uncertainty retained'}]})
  put(base+'completion-audit.json',{'book_key':'fixture','source_version':'v1','volume':1,'paragraphs':1,'publication_verified':True,'full_volume_source_coverage':True,'batch':str(batch.parent.relative_to(root)),'batches':[{'batch_sha256':sha(batch)}],'paragraph_ledger':base+'published-paragraphs.json'})
  return batch
 def test_published_subset_can_still_retain_pending_identity(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);self.fixture(root);result=MODULE.project(root)
   self.assertEqual(result['coverage'][0]['published'],1);self.assertEqual(result['coverage'][0]['deferred'],1);self.assertEqual(result['paragraphs'][0]['disposition'],'deferred');self.assertEqual(result['database_writes'],0)
 def test_navigation_heading_does_not_require_a_reader_paragraph(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);self.fixture(root)
   records=root/'resources/derived/history-library/fixture/paragraphs.jsonl.gz'
   with gzip.open(records,'at') as f:f.write(json.dumps({'id':'fixture-p000002','flags':['editorial_navigation_heading'],'locator':{'raw_excerpt_sha256':'b'*64}})+'\n')
   catalog=root/'resources/derived/history-library/catalog.json';value=json.loads(catalog.read_text());value['books'][0]['paragraph_sha256']=hashlib.sha256(records.read_bytes()).hexdigest();catalog.write_text(json.dumps(value))
   base=root/'content/books/fixture/vol-001/from-start'
   ledger=base/'published-paragraphs.json';value=json.loads(ledger.read_text());value['paragraphs'].append({'paragraph_id':'fixture-p000002','status':'reviewed_structural_verified','editorial_status':'reviewed','source_archive_verified':True});ledger.write_text(json.dumps(value))
   audit=base/'completion-audit.json';value=json.loads(audit.read_text());value['paragraphs']=2;audit.write_text(json.dumps(value))
   result=MODULE.project(root)
   self.assertEqual(result['coverage'][0]['reviewed'],1);self.assertEqual(len(result['paragraphs']),1);self.assertEqual(result['skipped'],[])
 def test_changed_batch_never_becomes_completed_coverage(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);batch=self.fixture(root);batch.write_text('{}');result=MODULE.project(root);self.assertEqual(result['coverage'],[]);self.assertEqual(len(result['skipped']),1)
 def test_scope_filters_leave_other_books_and_volumes_out(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);self.fixture(root)
   self.assertEqual(len(MODULE.project(root,book_key='fixture',volumes=[1])['coverage']),1)
   self.assertEqual(MODULE.project(root,book_key='other')['coverage'],[])
   self.assertEqual(MODULE.project(root,book_key='fixture',volumes=[2])['coverage'],[])
if __name__=='__main__':unittest.main()
