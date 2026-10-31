# coding: utf-8
"""Reuse immutable canonical source metadata in an unpublished history batch.

Default/--check: prints a local plan; no file or database writes, no network.
--apply-local: atomically replaces ONLY the current unpublished manifest after
all provenance checks succeed. Rebuild with the standard workbench afterwards.

Example: python3 scripts/reuse-history-sources.py content/books/BOOK/BATCH --root .
Only verified MySQL receipts qualify, as in the original guarded helper. A
matching receipt without a timezone-aware publication stage needs review.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid
from urllib.parse import unquote, urlsplit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
EDITION='选定电子TXT逐字快照；已核本次上下文，纸本及异文未全面校核。'
RESTORE=('url','snapshot_commit','archived_file','source_title','reviewed_citation')
AUTHORS={'zizhi-tongjian':'司马光等','xu-zizhi-tongjian':'毕沅等','songshi':'脱脱等','liaoshi':'脱脱等','jiu-wudaishi':'薛居正等','xin-wudaishi':'欧阳修'}


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def data(raw):return json.loads(raw)


def encoded(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def unpublished(directory):
    require(not any((directory/f).exists() or (directory/f).is_symlink() for f in ('publication-mysql.json','publication.json')),
            'Current batch has a publication receipt; immutable published manifest cannot be changed')


def read_file(root,path,protected):
    require(path.resolve().is_relative_to(root), 'Protected file escapes root: '+str(path))
    raw=path.read_bytes();protected[str(path.relative_to(root))]=sha(raw);return raw


def pinned_blob(root,url):
    parsed=urlsplit(url)
    m=re.fullmatch(r'/greed-216/histree/blob/([a-f0-9]{40})/(.+)',parsed.path)
    require(parsed.scheme=='https' and parsed.netloc=='github.com' and not parsed.query and not parsed.fragment and m is not None,
            'Canonical source needs a direct full-commit Git snapshot URL; source revision required')
    path=unquote(m[2]);p=Path(path)
    require(not p.is_absolute() and '..' not in p.parts and path.startswith(('content/','resources/')) and path.endswith('.txt') and not any(c in path for c in ('\n','\r','\x00')),
            'Canonical archive path is not an immutable text snapshot')
    result=subprocess.run(['git','show',m[1]+':'+path],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    require(result.returncode==0,'Canonical Git snapshot is not locally available: '+m[1]+':'+path)
    raw=result.stdout;raw.decode('utf-8')
    return m[1],path,raw


def paragraph_map(packet):
    rows=packet['paragraphs']+packet.get('supplementary_paragraphs',[])
    out={p['id']:p for p in rows}
    require(len(out)==len(rows),'Duplicate paragraph in packet')
    return out


def snapshot(root,directory,m,paras,protected,book_key):
    pid=m['paragraph_id'];require(pid in paras,'Manifest paragraph absent from packet')
    p=paras[pid];loc=p['locator'];relative=Path(m['file'])
    require(not relative.is_absolute() and '..' not in relative.parts,'Snapshot path escapes sources')
    raw=read_file(root,directory/'sources'/relative,protected)
    require(p.get('book_key')==book_key and p.get('source_version'),'Wrong source book/version')
    require(m.get('upstream_locator')==loc,'Manifest/packet locator mismatch')
    require(sha(raw)==m['sha256']==loc['raw_excerpt_sha256'],'Raw source snapshot SHA mismatch: '+pid)
    require(type(loc['char_start']) is int and type(loc['char_end']) is int and loc['char_start']>=0 and loc['char_end']-loc['char_start']==len(raw.decode('utf-8')),
            'Snapshot character offsets differ: '+pid)
    # Packet heading text may be normalized. Immutable raw bytes + locator are the
    # provenance authority; no search/rendered text is substituted for this raw.
    return p,raw


def validate_citation(source,m,p):
    note=source.get('note');title=source.get('title');volume=p['volume_candidate'];book=p['book']
    require(isinstance(note,str) and isinstance(title,str) and note and title,
            'Canonical source has missing citation/title; source revision required')
    require(source['url']==m.get('url') and source['note']==m.get('reviewed_citation',p.get('citation')) and source['title']==m.get('source_title',source['title']),
            'Canonical source metadata differs from its published manifest; source revision required')
    require(f'《{book}》' in note and p['id'] in note,
            'Canonical source note has wrong book/volume/paragraph; source revision required')
    volumes={int(x) for x in re.findall(r'卷(\d+)',note)}
    require(not volumes or volumes=={volume},'Canonical citation contains a different volume; source revision required')
    require(book in title and re.search(r'卷'+str(volume)+r'(?!\d)',title),
            'Canonical title has wrong book/volume; source revision required')
    require({int(x) for x in re.findall(r'卷(\d+)',title)}=={volume},'Canonical title contains a different volume; source revision required')
    expected=dict(key=source['key'],title=title,source_type='primary',author=AUTHORS.get(p['book_key']),edition=EDITION,url=source['url'],note=note)
    require(source==expected,'Canonical source cannot be regenerated by standard history workbench; source revision required')


def published_at(proof):
    """Use receipt evidence, never a volume/path name, to order published copies."""
    stages=proof.get('stages',[])
    for stage in ('published_source','anonymous_readback_verified'):
        values=[]
        for row in stages:
            if row.get('stage')!=stage:continue
            try:
                value=datetime.fromisoformat(row['at'].replace('Z','+00:00'))
                require(value.tzinfo is not None,'Publication stage timestamp needs timezone')
                values.append(value.astimezone(timezone.utc))
            except (KeyError,TypeError,ValueError) as exc:
                raise ValueError('Invalid publication stage timestamp') from exc
        if values:return min(values),stage
    raise ValueError('Verified matching source has no publication stage timestamp; source review required')


def prepare(root,directory):
    root=Path(root).resolve();directory=Path(directory)
    if not directory.is_absolute():directory=root/directory
    directory=directory.resolve()
    require(directory.is_relative_to(root/'content/books'),'Batch directory must be inside root/content/books')
    unpublished(directory)
    protected={};manifest_path=directory/'sources/manifest.json'
    before_raw=read_file(root,manifest_path,protected);before=data(before_raw)
    packet=data(read_file(root,directory/'packet.json',protected));paras=paragraph_map(packet)
    book_key=packet['book_key'];volume=packet['volume']
    require(isinstance(book_key,str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*',book_key),'Invalid packet book key')
    book_directory=root/'content/books'/book_key
    require(directory.is_relative_to(book_directory),'Current directory disagrees with packet book key')
    require(type(volume) is int and volume>0,'Invalid packet volume')
    require(len({m['key'] for m in before})==len(before),'Duplicate current source key')
    current={m['key']:m for m in before};matches={};published_batches=[];excluded_operations=[]
    require(all(p.get('book_key')==book_key for p in packet['paragraphs']),'Wrong source book in primary range')
    scope_books=sorted({book_key}|{p['book_key'] for p in paras.values()})
    require(all(re.fullmatch(r'[a-z0-9][a-z0-9-]*',key) for key in scope_books),'Invalid supplementary book key')
    receipts=sorted({p for key in scope_books for p in (root/'content/books'/key).rglob('publication-mysql.json')})
    for receipt_path in receipts:
        old_dir=receipt_path.parent
        if old_dir.resolve()==directory:continue
        proof_raw=read_file(root,receipt_path,protected);proof=data(proof_raw)
        if proof.get('verified') is not True:continue
        require(proof.get('backend')=='mysql','Verified prior receipt is not MySQL')
        if proof.get('operation')=='insert_missing_source_text_only':
            require('batch_sha256' not in proof and not (old_dir/'content-batch.json').exists(), 'Text backfill receipt conflicts with a content batch')
            require(all(type(proof.get(k)) is int and proof[k]==0 for k in ('new_people','new_events','new_relationships','new_participations','new_claims','schema_migrations','application_deployments')), 'Text backfill receipt includes other writes')
            excluded_operations.append(str(receipt_path.relative_to(root)))
            continue
        batch_path=old_dir/'content-batch.json';batch_raw=read_file(root,batch_path,protected)
        require(proof.get('batch_sha256')==sha(batch_raw),'Prior verified batch SHA mismatch: '+str(batch_path.relative_to(root)))
        batch=data(batch_raw);sources={s['key']:s for s in batch['sources']}
        require(len(sources)==len(batch['sources']),'Duplicate published source key')
        keys=set(current)&set(sources)
        published_batches.append(str(old_dir.relative_to(root)))
        if not keys:continue
        publication_time,time_basis=published_at(proof)
        file_hashes={}
        read_file(root,receipt_path,file_hashes);read_file(root,batch_path,file_hashes)
        old_manifest_raw=read_file(root,old_dir/'sources/manifest.json',file_hashes);old_manifest=data(old_manifest_raw)
        old_packet=data(read_file(root,old_dir/'packet.json',file_hashes));old_paras=paragraph_map(old_packet)
        require(old_dir.is_relative_to(root/'content/books'/old_packet['book_key']),'Prior packet book mismatch')
        old_ids=data(read_file(root,old_dir/'sql/key-map.json',file_hashes))
        old_bykey={m['key']:m for m in old_manifest};require(len(old_bykey)==len(old_manifest),'Duplicate prior source key')
        for key in sorted(keys):
            require(key in old_bykey and key in old_ids,'Published source absent from manifest/key-map')
            om=old_bykey[key];p,raw=snapshot(root,old_dir,om,old_paras,file_hashes,paras[current[key]['paragraph_id']]['book_key']);source=sources[key]
            validate_citation(source,om,p)
            commit,archived_path,gitraw=pinned_blob(root,source['url'])
            require(sha(gitraw)==om['sha256'] and gitraw==raw,'Canonical Git blob differs byte-for-byte from published raw snapshot')
            require(om.get('snapshot_commit')==commit and om.get('archived_file')==archived_path,
                    'Canonical archive fields disagree with its immutable URL')
            matches.setdefault(key,[]).append(dict(published_at=publication_time,time_basis=time_basis,directory=str(old_dir.relative_to(root)),source=source,manifest=om,paragraph=p,raw=raw,source_id=old_ids[key],commit=commit,archived_path=archived_path,protected=file_hashes.copy(),batch_sha256=sha(batch_raw),receipt_sha256=sha(proof_raw),manifest_sha256=sha(old_manifest_raw)))
    after=copy.deepcopy(before);changes=[]
    for m in after:
        key=m['key']
        if key not in matches:continue
        copies=sorted(matches[key],key=lambda x:(x['published_at'],x['receipt_sha256']))
        canonical=copies[0];p,raw=snapshot(root,directory,m,paras,protected,paras[m['paragraph_id']]['book_key'])
        require(m.get('citation_review_note','').strip(),'Current citation needs an explicit book/volume/chapter review before canonical reuse')
        cp=canonical['paragraph'];cm=canonical['manifest']
        # An explicitly reviewed current chapter label is also a semantic guard
        # against reusing an old copy/paste note with a different chapter name.
        components=[x for x in str(m.get('source_title','')).split('·') if x and x not in (p['book'],f'《{p["book"]}》',p['id']) and not re.fullmatch(r'卷[0-9〇零一二三四五六七八九十百]+',x)]
        require(bool(components),'Current source needs an explicitly reviewed chapter label before canonical reuse')
        chapter=components[0]
        require(chapter in canonical['source']['title'] and chapter in canonical['source']['note'], 'Canonical note/title does not retain the reviewed chapter label; source revision required: '+key)
        require(str(uuid.UUID(canonical['source_id']))==canonical['source_id'],'Canonical source key-map UUID is invalid')
        require(m['paragraph_id']==cm['paragraph_id']==p['id']==cp['id'],'Shared source key has different paragraph identity')
        require(p['source_version']==cp['source_version'],'Shared source version differs: '+key)
        require(p['book']==cp['book'] and p['locator']==cp['locator'] and p['section_id']==cp['section_id'] and p['volume_candidate']==cp['volume_candidate'],
                'Shared source locator/section/volume differs: '+key)
        require(p['locator']['source_sha256']==cp['locator']['source_sha256'] and m['sha256']==cm['sha256'] and raw==canonical['raw'],
                'Shared source/original excerpt bytes differ: '+key)
        for candidate in copies:
            require(candidate['source']==canonical['source'] and candidate['source_id']==canonical['source_id'] and candidate['paragraph']==cp and candidate['manifest']['sha256']==cm['sha256'],
                    'Verified prior batches disagree about the canonical source; source revision required: '+key)
            protected.update(candidate['protected'])
        restored=dict(url=canonical['source']['url'],snapshot_commit=canonical['commit'],archived_file=canonical['archived_path'],source_title=canonical['source']['title'],reviewed_citation=canonical['source']['note'])
        authored=m.get('authored_claim_citation',m.get('reviewed_citation',p.get('citation')))
        require(isinstance(authored,str) and p['id'] in authored and f'《{p["book"]}》' in authored and re.search(r'卷'+str(p['volume_candidate'])+r'(?!\d)',authored),'New claim citation must retain reviewed book/volume/paragraph')
        original=m.get('original_reviewed_citation',authored)
        require(isinstance(original,str) and p['id'] in original and f'《{p["book"]}》' in original and re.search(r'卷'+str(p['volume_candidate'])+r'(?!\d)',original),
                'Current reviewed citation has lost book/volume/paragraph; correct it before reuse')
        audit=dict(canonical_batch=canonical['directory'],canonical_published_at=canonical['published_at'].isoformat(),canonical_time_basis=canonical['time_basis'],canonical_source_id=canonical['source_id'],canonical_batch_sha256=canonical['batch_sha256'],canonical_receipt_sha256=canonical['receipt_sha256'],canonical_manifest_sha256=canonical['manifest_sha256'],source_key=key,paragraph_id=p['id'],source_version=p['source_version'],source_sha256=p['locator']['source_sha256'],raw_snapshot_sha256=m['sha256'],canonical_git_blob_sha256=sha(canonical['raw']),canonical_commit=canonical['commit'],canonical_archived_file=canonical['archived_path'],verified_prior_copies=[dict(batch=x['directory'],published_at=x['published_at'].isoformat(),time_basis=x['time_basis'],batch_sha256=x['batch_sha256'],receipt_sha256=x['receipt_sha256'],manifest_sha256=x['manifest_sha256']) for x in copies])
        original_row=copy.deepcopy(m);m.update(restored);m['original_reviewed_citation']=original;m['authored_claim_citation']=authored;m['canonical_source_reuse']=audit
        if m!=original_row:changes.append(dict(source_key=key,paragraph_id=p['id'],before={k:original_row.get(k) for k in RESTORE},after=restored,canonical_batch=canonical['directory'],source_id=canonical['source_id']))
    unpublished(directory)
    return dict(format_version=1,kind='reuse_history_sources',book_key=book_key,volume=volume,source_book_keys=scope_books,current_directory=str(directory.relative_to(root)),manifest_path=str(manifest_path.relative_to(root)),manifest_before_sha256=sha(before_raw),manifest_after_sha256=sha(encoded(after)) if changes else sha(before_raw),changes=changes,new_source_keys_unchanged=sorted(set(current)-set(matches)),scanned_verified_batches=published_batches,excluded_non_batch_receipts=excluded_operations,scanned_receipts=[str(p.relative_to(root)) for p in receipts],protected_paths=protected),before_raw,after


def apply_local(root,plan,before_raw,after):
    root=Path(root).resolve();directory=root/plan['current_directory'];unpublished(directory)
    path=root/plan['manifest_path'];require(path==directory/'sources/manifest.json','Unexpected mutation path')
    receipts=sorted({p for key in plan['source_book_keys'] for p in (root/'content/books'/key).rglob('publication-mysql.json')})
    require([str(p.relative_to(root)) for p in receipts]==plan['scanned_receipts'],
            'Published receipt set changed before local write; prepare again')
    for rel,digest in plan['protected_paths'].items():
        require(sha((root/rel).read_bytes())==digest,'Protected source archive changed before local write: '+rel)
    require(path.read_bytes()==before_raw and sha(before_raw)==plan['manifest_before_sha256'],'Current manifest changed concurrently')
    if not plan['changes']:return False
    payload=encoded(after);require(sha(payload)==plan['manifest_after_sha256'],'Local output manifest changed')
    # One-file atomic replacement only; all checks precede creation of the temp file.
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(prefix='.reuse-history-sources-',dir=path.parent,delete=False) as stream:
            tmp=Path(stream.name);stream.write(payload);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,path.stat().st_mode & 0o777)
        unpublished(directory);require(path.read_bytes()==before_raw,'Current manifest changed before atomic replacement')
        os.replace(tmp,path);tmp=None
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)
    return True


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch_directory',type=Path);p.add_argument('--root',type=Path,default=ROOT)
    action=p.add_mutually_exclusive_group();action.add_argument('--check',action='store_true');action.add_argument('--apply-local',action='store_true')
    args=p.parse_args(argv);plan,before,after=prepare(args.root,args.batch_directory)
    if args.apply_local:plan['local_manifest_replaced']=apply_local(args.root,plan,before,after)
    plan['read_only']=not args.apply_local
    print(json.dumps(plan,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
