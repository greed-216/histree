"""Run the standard MySQL copy-review guard for this fixed annual plan.
Only three reviewed entries with no actual place name receive the structural exception.
"""
import sys,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('review_copy',ROOT/'scripts/review-public-history-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original_validate=m.validate_changes
m.EDITABLE['event'].add('location_name')
def validate(changes):
 for c in changes:
  if 'location_name' in c['after']:
   assert c['table']=='event' and c['before']['location_name'] in {'李严母子谈话处，史未具地','处决具体地点本段未载','史书未具观测地点'} and c['after']['location_name'] is None
   assert c['baseline']['location_lat'] is None and c['baseline']['location_lng'] is None and c['baseline']['location_precision']=='unknown'
 return original_validate(changes)
m.validate_changes=validate
Base=m.Client
class TargetClient(Base):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  if self.store:
   plan=json.loads(Path(sys.argv[2]).read_text());assert plan['backend']=='mysql' and self.store.target_fingerprint==plan['target_fingerprint'],'MySQL target differs from the reviewed snapshot'
m.Client=TargetClient
if __name__=='__main__':
 from publication_wait import install
 install(json.loads(Path(sys.argv[2]).read_text())['target_fingerprint'])
 m.main()
