"""Index legacy and current evidence by book without changing public entity/source IDs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
books={'zizhi-tongjian':('资治通鉴',('tongjian-',)),'jiuwudaishi':('旧五代史',('jiuwudaishi-',)),'xinwudaishi':('新五代史',('xinwudaishi-',)),'wuyue-beishi':('吴越备史',('KR2i0019-',)),'shu-taowu':('蜀梼杌',('KR2i0016-',))}
books.update({'jiutangshu':('旧唐书',('jiutangshu-',)), 'shiguochunqiu':('十国春秋',('shiguochunqiu-',))})
books.update({'beimeng-suoyan':('北梦琐言',('beimeng-suoyan-',))})
indexes={k:{} for k in books}
for path in sorted((ROOT/'content').rglob('content-batch.json')):
 batch=json.loads(path.read_text())
 for c in batch['claims']:
  matches=[k for k,(_,prefixes) in books.items() if c['source_key'].startswith(prefixes)]
  assert len(matches)==1, c['source_key']
  book=matches[0]
  record=indexes[book].setdefault(c['key'],{'claim_key':c['key'],'source_key':c['source_key'],'subject_table':c['subject_table'],'subject_key':c['subject_key'],'citation':c['citation'],'batch_files':[]})
  assert record['source_key']==c['source_key'] and record['subject_key']==c['subject_key'],'Conflicting claim identity'
  record['batch_files'].append(str(path.relative_to(ROOT)))
for key,(name,_) in books.items():
 out=ROOT/'content/books'/key;out.mkdir(parents=True,exist_ok=True)
 (out/'source-index.json').write_text(json.dumps({'book':name,'scope':'按书索引引用；是否已发布以各批 publication/release-verification 及数据库为准。','claims':list(indexes[key].values())},ensure_ascii=False,indent=2)+'\n')
print({books[k][0]:len(v) for k,v in indexes.items()})
