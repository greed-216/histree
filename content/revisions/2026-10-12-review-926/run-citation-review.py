"""Run the standard MySQL copy-review guard for this fixed annual plan.
Only the reviewed year-label substitution is allowed; original quotes and locators remain protected.
"""
import sys,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('review_copy',ROOT/'scripts/review-public-history-copy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original_validate=m.validate_changes
m.EDITABLE['fact_claim'].add('citation')
def validate(changes):
 for c in changes:
  assert c['table']=='fact_claim' and set(c['after'])=={'citation'}
  assert '天成元年（926）' in c['before']['citation']
  assert c['after']['citation']==c['before']['citation'].replace('天成元年（926）','同光四年／天成元年（926）')
  assert c['before']['citation'].startswith('《资治通鉴》卷')
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
