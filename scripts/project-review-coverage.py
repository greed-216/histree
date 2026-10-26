#!/usr/bin/env python3
"""Build a read-only coverage plan from versioned corpus records and verified publication audits."""
import argparse,gzip,hashlib,json
from pathlib import Path

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inside(root,name):
    path=(root/name).resolve()
    if not path.is_relative_to(root.resolve()): raise ValueError('Audit path escaped repository')
    return path

def project(root):
    catalog=json.loads((root/'resources/derived/history-library/catalog.json').read_text())
    books={b['book_key']:b for b in catalog['books']}
    indexes={};rows=[];paragraphs=[];skipped=[]
    for path in sorted((root/'content/books').glob('*/vol-*/from-start/completion-audit.json')):
        audit=json.loads(path.read_text());book=books.get(audit.get('book_key'))
        if not book or not audit.get('publication_verified') or not audit.get('full_volume_source_coverage'):
            skipped.append({'audit':str(path.relative_to(root)),'reason':'No full reviewed and publication-verified proof'});continue
        if audit.get('source_version')!=book['source_version']:
            skipped.append({'audit':str(path.relative_to(root)),'reason':'Reader version differs'});continue
        try:
            batches=audit.get('batches') or ([{'batch_sha256':audit['batch_sha256'],'path':audit['batch']}] if audit.get('batch_sha256') and audit.get('batch') else [])
            if not batches: raise ValueError('Missing batch audit')
            legacy_entries=[]; legacy_source_proof=False
            for batch in batches:
                candidates=[inside(root,audit.get('batch',''))] if len(batches)==1 else list(path.parent.glob('release-*/'+batch['path']))
                candidates=[p for p in candidates if (p/'content-batch.json').is_file() and digest(p/'content-batch.json')==batch['batch_sha256']]
                if len(candidates)!=1: raise ValueError('Cannot uniquely bind batch bytes')
                proof_path=next((candidates[0]/name for name in ['publication-mysql.json','publication.json'] if (candidates[0]/name).exists()),None)
                if not proof_path: raise ValueError('Missing publication proof')
                proof=json.loads(proof_path.read_text())
                if not proof.get('verified') or proof.get('batch_sha256')!=batch['batch_sha256']: raise ValueError('Publication proof differs')
                if not audit.get('paragraph_ledger'):
                    legacy_entries.extend(json.loads((candidates[0]/'paragraphs.json').read_text()))
                    validation=json.loads((candidates[0]/'workbench-validation.json').read_text())
                    if validation.get('batch_sha256')!=batch['batch_sha256'] or validation.get('curation_sha256')!=digest(candidates[0]/'curation.json'): raise ValueError('Legacy curation proof differs')
                    legacy_source_proof=validation.get('source_snapshot_hashes_checked') is True
            if book['book_key'] not in indexes:
                artifact=inside(root,book['paragraph_file'])
                if digest(artifact)!=book['paragraph_sha256']: raise ValueError('Corpus paragraph artifact changed')
                with gzip.open(artifact,'rt',encoding='utf-8') as f:
                    indexes[book['book_key']]={p['id']:p['locator']['raw_excerpt_sha256'] for line in f if (p:=json.loads(line)).get('locator')}
            entries=json.loads(inside(root,audit['paragraph_ledger']).read_text())['paragraphs'] if audit.get('paragraph_ledger') else legacy_entries
            expected=audit['paragraphs'] if isinstance(audit['paragraphs'],int) else len(audit['paragraphs'])
            if len({p['paragraph_id'] for p in entries})!=expected: raise ValueError('Paragraph count is not whole-volume coverage')
            index=indexes[book['book_key']];counts=dict(reviewed=0,published=0,no_new=0,deferred=0);unit=[]
            for entry in entries:
                pid=entry['paragraph_id']
                if pid not in index: raise ValueError('Legacy paragraph has no exact reader match')
                status=entry.get('status','')
                pending=bool(entry.get('pending_items')) or entry.get('editorial_status')=='pending_textual_review' or 'pending' in status or 'deferred' in status
                reviewed=entry.get('editorial_status') in ['reviewed','pending_textual_review'] or legacy_source_proof and status.startswith(('published_','reviewed_'))
                if not reviewed or not (entry.get('source_archive_verified') or legacy_source_proof): raise ValueError('Paragraph review or source proof missing')
                published=entry.get('publication_verified') is True or legacy_source_proof and status.startswith('published_')
                no_new=status in ['reviewed_no_structured_fact_verified','reviewed_structural_verified'] and not entry.get('claim_keys')
                if not (published or no_new or pending): raise ValueError('Unknown paragraph disposition')
                counts['reviewed']+=1;counts['published']+=int(published);counts['no_new']+=int(no_new);counts['deferred']+=int(pending)
                unit.append(dict(paragraph_id=pid,content_sha256=index[pid],disposition='deferred' if pending else 'published' if published else 'no_new',reason=entry.get('note','') or '\n'.join(entry.get('observations',[])),audit_sha256=digest(path)))
            rows.append(dict(book_key=book['book_key'],source_version=book['source_version'],volume=audit['volume'],**counts,audit_sha256=digest(path),audit_path=str(path.relative_to(root))))
            paragraphs.extend(unit)
        except (KeyError,ValueError,FileNotFoundError) as error:skipped.append({'audit':str(path.relative_to(root)),'reason':str(error)})
    return dict(format_version=1,coverage=rows,paragraphs=paragraphs,skipped=skipped,database_writes=0)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=project(args.source_root.resolve());args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'volumes':len(result['coverage']),'paragraphs':len(result['paragraphs']),'unmapped_audits':len(result['skipped']),'database_writes':0}))
