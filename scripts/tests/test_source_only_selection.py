import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import source_texts as S

class SourceOnly(unittest.TestCase):
 def setUp(self):
  self.sid='11111111-1111-1111-1111-111111111111'
  self.batch=dict(sources=[dict(key='source_fixture',url='https://github.com/greed-216/histree/blob/'+'a'*40+'/content/source.txt')],claims=[],people=[],events=[],person_events=[],person_relationships=[],topics=[])
 def test_default_does_not_select_unreferenced_sources(self):
  with patch.object(S,'fill_content',side_effect=lambda rows:rows):
   self.assertEqual(S.batch_texts(self.batch,{'source_fixture':self.sid}),[])
 def test_explicit_source_only_mode_selects_exact_existing_source_ids(self):
  with patch.object(S,'fill_content',side_effect=lambda rows:rows):
   self.assertEqual(S.batch_texts(self.batch,{'source_fixture':self.sid},True),[dict(source_id=self.sid,archive_url=self.batch['sources'][0]['url'])])
 def test_source_only_mode_cannot_hide_facts_or_accept_a_truthy_string(self):
  for kind in ('people','events','person_events','person_relationships','claims','topics'):
   batch=dict(self.batch,**{kind:[dict(key='fact')]})
   with self.assertRaises(ValueError):S.batch_texts(batch,{'source_fixture':self.sid},True)
  with self.assertRaises(ValueError):S.batch_texts(self.batch,{'source_fixture':self.sid},'yes')

if __name__=='__main__':unittest.main()
