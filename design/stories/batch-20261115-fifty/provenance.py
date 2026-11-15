"""Audit reuse of existing published batches; does not write facts or progress."""
import hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
HISTORY=Path('/Users/liushuang/project/histree')
stories=json.loads((BASE/'scripts.json').read_text())['stories']
result=[]
for s in stories:
    records=[]
    for p in s['sourceParagraphs']:
        batch=HISTORY/f'content/books/shiji/vol-{p["volume_candidate"]:03}/part-01'
        # Early volumes have a separate from-start workflow.
        if not batch.exists():
            candidates=list((HISTORY/f'content/books/shiji/vol-{p["volume_candidate"]:03}').rglob('curation.json'))
            assert len(candidates)==1,(s['slug'],candidates)
            batch=candidates[0].parent
        c=json.loads((batch/'curation.json').read_text())
        relevant=[item for item in c['items'] if any(e.get('paragraph_id')==p['id'] for e in item.get('evidence',[]))]
        pub=json.loads((batch/'publication-mysql.json').read_text())
        stages=[x['stage'] for x in pub['stages']]
        assert any('published' in x for x in stages),(s['slug'],stages)
        assert relevant,(s['slug'],p['id'])
        records.append(dict(paragraphId=p['id'],batch=str(batch.relative_to(HISTORY)),
            batchSha256=hashlib.sha256((batch/'content-batch.json').read_bytes()).hexdigest(),
            publicationBatchSha256=pub['batch_sha256'],publicationStages=stages,
            facts=[dict(group=x['group'],key=x['row']['key'],title=x['row'].get('title',x['row'].get('name',''))) for x in relevant]))
    result.append(dict(slug=s['slug'],existingIngestion=records))
(BASE/'existing-ingestion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('Verified existing published ingestion for',len(result),'stories')
