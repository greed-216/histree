"""Index legacy and current evidence by book without changing public entity/source IDs."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
books={'zizhi-tongjian':('资治通鉴',('tongjian-',)),'jiuwudaishi':('旧五代史',('jiuwudaishi-',)),'xinwudaishi':('新五代史',('xinwudaishi-','new-wudaishi-')),'wuyue-beishi':('吴越备史',('KR2i0019-',)),'shu-taowu':('蜀梼杌',('KR2i0016-',))}
books.update({'jiutangshu':('旧唐书',('jiutangshu-',)), 'shiguochunqiu':('十国春秋',('shiguochunqiu-',))})
books.update({'beimeng-suoyan':('北梦琐言',('beimeng-suoyan-',))})
books['xintangshu']=('新唐书',('xintangshu-',))
books['liaoshi']=('辽史',('liaoshi-',))
books['songshi']=('宋史',('songshi-',))
books['hanshu']=('汉书',('hanshu-',))
books['houhanshu']=('后汉书',('houhanshu-',))
books['wuyue-beishi']=('吴越备史',('KR2i0019-','wuyuebeishi-'))
indexes={k:{} for k in books}
subject_remap={}
citation_revisions={}
for plan_path in sorted((ROOT/'content/revisions').glob('*/plan.json')):
 plan=json.loads(plan_path.read_text())
 audit_path=plan_path.parent/'publication.json'
 if audit_path.exists():
  audit=json.loads(audit_path.read_text())
  citation_changes=[c for c in plan.get('changes',[]) if c.get('table')=='fact_claim' and 'citation' in c.get('after',{})]
  if citation_changes and audit.get('verified'):
   assert audit.get('plan_sha256')==hashlib.sha256(plan_path.read_bytes()).hexdigest(), 'Citation revision plan changed'
   for change in citation_changes:
    assert change.get('key') and set(change['before'])==set(change['after'])=={'citation'}
    citation_revisions.setdefault(change['key'],[]).append((change['before']['citation'],change['after']['citation']))
 for claim_key, subject_key in plan.get('claim_subject_remap',{}).items():
  assert claim_key not in subject_remap or subject_remap[claim_key]==subject_key, claim_key
  subject_remap[claim_key]=subject_key
batch_paths=list((ROOT/'content').rglob('content-batch.json'))
revision_paths=list((ROOT/'content/revisions').glob('*/additional-claims.json'))
for path in sorted(batch_paths+revision_paths):
 batch=json.loads(path.read_text())
 if path.name=='additional-claims.json':
  assert batch.get('format_version')==1, 'Unsupported revision claim schema'
  audit_name=batch['publication_audit']
  assert Path(audit_name).name==audit_name, 'Invalid revision audit path'
  audit_path=path.parent/audit_name
  if audit_path.exists():
   audit=json.loads(audit_path.read_text())
   if audit.get('verified'):
    assert audit.get('additional_claims_sha256')==hashlib.sha256(path.read_bytes()).hexdigest(), 'Published revision claims changed'
 for c in batch['claims']:
  matches=[k for k,(_,prefixes) in books.items() if c['source_key'].startswith(prefixes)]
  assert len(matches)==1, c['source_key']
  book=matches[0]
  subject_key=subject_remap.get(c['key'],c['subject_key'])
  citation=c['citation']
  for before,after in citation_revisions.get(c['key'],[]):
   assert citation==before, 'Citation revision does not match archived original: '+c['key']
   citation=after
  record=indexes[book].setdefault(c['key'],{'claim_key':c['key'],'source_key':c['source_key'],'subject_table':c['subject_table'],'subject_key':subject_key,'citation':citation,'batch_files':[]})
  assert record['source_key']==c['source_key'] and record['subject_key']==subject_key,'Conflicting claim identity'
  record['batch_files'].append(str(path.relative_to(ROOT)))
assert citation_revisions.keys() <= {claim for rows in indexes.values() for claim in rows}, 'Citation revision cites unknown claim'
assert subject_remap.keys() <= {claim for rows in indexes.values() for claim in rows}, 'Revision cites unknown claim'
for key,(name,_) in books.items():
 out=ROOT/'content/books'/key;out.mkdir(parents=True,exist_ok=True)
 (out/'source-index.json').write_text(json.dumps({'book':name,'scope':'按书索引引用；是否已发布以各批 publication/release-verification 及数据库为准。','claims':list(indexes[key].values())},ensure_ascii=False,indent=2)+'\n')
print({books[k][0]:len(v) for k,v in indexes.items()})
