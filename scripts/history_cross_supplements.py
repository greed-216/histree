"""Guard supplemental evidence that points to an already published paragraph."""
import hashlib,json

def validate_cross_supplement(root, paragraph_id, subject_key, declared):
 assert any(x['primary_paragraph_id']==paragraph_id and x['subject_key']==subject_key for x in declared), 'Undeclared cross-volume supplement'
 matches=[]
 for ledger in (root/'content/books/zizhi-tongjian').glob('vol-*/year-*/paragraphs.json'):
  matches.extend(x for x in json.loads(ledger.read_text()) if x['id']==paragraph_id)
 assert len(matches)==1 and matches[0]['status']=='published_verified', 'Cross-volume paragraph is not published'
 old_batch_key=matches[0]['batch_key']
 previous=[f for f in (root/'content/books/zizhi-tongjian').glob('vol-*/year-*/part-*/content-batch.json') if json.loads(f.read_text())['batch_key']==old_batch_key]
 assert len(previous)==1, 'Missing previous paragraph batch'
 previous_path=previous[0];previous_batch=json.loads(previous_path.read_text());previous_audit=json.loads((previous_path.parent/'publication.json').read_text())
 assert paragraph_id in json.loads((previous_path.parent/'coverage.json').read_text())['paragraphs'], 'Paragraph absent from previous coverage'
 assert previous_audit.get('verified') and previous_audit['batch_sha256']==hashlib.sha256(previous_path.read_bytes()).hexdigest(), 'Previous batch audit mismatch'
 assert any(x['key']==subject_key for group in ['people','events','person_relationships','person_events'] for x in previous_batch[group]), 'Cross-volume subject is absent from previous batch'
