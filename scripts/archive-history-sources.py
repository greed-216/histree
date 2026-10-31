# coding: utf-8
"""Plan a source-only archive; --apply requires the exact saved plan SHA-256.

Preparation writes only BATCH/.workflow/source-upload-plan.json: no Git objects,
index, manifest, push or database writes. Fetch missing parent objects separately.
Only greed-216/histree is trusted. Tests replace transport, never this policy.
Apply writes .workflow/source-archive.json and source-url-verification.json;
an anonymous verification failure can resume with the same fixed plan/hash.
"""
import argparse
import concurrent.futures
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import quote, unquote, urlsplit

ROOT=Path(__file__).resolve().parent.parent
REPO='greed-216/histree'
NAMES=('source.txt','paragraph.json')


def require(value,message):
    if not value:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def read(path):
    require(path.is_file() and not path.is_symlink(),'JSON input must be a regular file: '+str(path))
    return json.loads(path.read_bytes())


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    require(not path.is_symlink() and path.parent.resolve()==path.parent,'Workflow output symlink rejected')
    temp=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.archive-plan-',delete=False) as f:
            temp=Path(f.name);f.write(encoded(value));f.flush();os.fsync(f.fileno())
        os.replace(temp,path);temp=None
    finally:
        if temp is not None:temp.unlink(missing_ok=True)


def relative(value):
    require(isinstance(value,str) and value and not any(ord(c)<32 or ord(c)==127 for c in value),'Path control/line injection rejected')
    p=PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '.' not in p.parts and '\\' not in value and p.as_posix()==value,'Path traversal/noncanonical path rejected')
    return value


def inside(root,path):
    require(path.resolve().is_relative_to(root) and not path.is_symlink(),'Path escapes root or is a symlink: '+str(path))
    return path


def batch_directory(root,batch):
    batch=Path(batch);batch=inside(root,(batch if batch.is_absolute() else root/batch).resolve())
    require(batch.is_relative_to(root/'content/books'),'Batch directory must stay inside root/content/books')
    relative(str(batch.relative_to(root)))
    return batch


def unpublished(batch):
    require(not any((batch/n).exists() or (batch/n).is_symlink() for n in ('publication.json','publication-mysql.json')),'Publication started; manifest is immutable')


def git(root,*args,input=None,env=None):
    clean=dict(os.environ if env is None else env)
    for key in ('GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_PREFIX'):clean.pop(key,None)
    if env is not None and 'GIT_INDEX_FILE' in env:clean['GIT_INDEX_FILE']=env['GIT_INDEX_FILE']
    return subprocess.run(['git',*args],cwd=root,input=input,env=clean,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout


def trusted_remote(root):
    require(Path(git(root,'rev-parse','--show-toplevel').decode().strip()).resolve()==root,'Root is not the selected Git worktree')
    allowed={f'https://github.com/{REPO}',f'https://github.com/{REPO}.git',f'git@github.com:{REPO}',f'git@github.com:{REPO}.git',f'ssh://git@github.com/{REPO}',f'ssh://git@github.com/{REPO}.git'}
    fetch=git(root,'remote','get-url','--all','origin').decode().splitlines()
    push=git(root,'remote','get-url','--push','--all','origin').decode().splitlines()
    require(len(fetch)==len(push)==1 and fetch[0] in allowed and push[0] in allowed,'Untrusted origin fetch/push remote')
    return dict(fetch=fetch[0],push=push[0])


def branch_ref(root,branch):
    require(isinstance(branch,str) and branch.startswith('codex/') and re.fullmatch(r'[A-Za-z0-9._/-]+',branch),'Branch must be a safe codex/... ref')
    git(root,'check-ref-format','refs/heads/'+branch)
    return 'refs/heads/'+branch


def remote_head(root,ref):
    raw=git(root,'ls-remote','--refs','origin',ref).decode().splitlines()
    if not raw:return None
    require(len(raw)==1,'Ambiguous remote ref')
    fields=raw[0].split('\t');require(len(fields)==2 and fields[1]==ref and re.fullmatch(r'[a-f0-9]{40}',fields[0]),'Invalid remote head')
    return fields[0]


def parent_blob(root,parent,path):
    tree=git(root,'ls-tree','-z',parent,'--',path)
    if not tree:return None
    rows=tree.split(b'\0');require(len(rows)==2 and rows[-1]==b'','Ambiguous archive tree entry')
    meta,name=rows[0].split(b'\t',1);mode,kind,oid=meta.decode().split()
    require(name.decode()==path and mode=='100644' and kind=='blob','Archive target is not a regular source blob')
    raw=git(root,'cat-file','blob',oid)
    return dict(oid=oid,sha256=sha(raw),bytes=len(raw))


def source_inputs(root,batch,prefix):
    unpublished(batch);protected={}
    def load(path):
        inside(root,path);require(path.is_file(),'Source input must be a regular file');raw=path.read_bytes();protected[str(path.relative_to(root))]=sha(raw);return raw
    packet=json.loads(load(batch/'packet.json'));manifest=json.loads(load(batch/'sources/manifest.json'))
    curation=json.loads(load(batch/'curation.json'))
    book=packet['book_key'];require(re.fullmatch(r'[a-z0-9][a-z0-9-]*',book or ''),'Invalid packet book key')
    require(batch.is_relative_to(root/'content/books'/book),'Batch/packet book mismatch')
    relative(prefix);require(prefix.startswith('content/books/'+book+'/'),'Archive prefix must stay within the selected book')
    rows=packet['paragraphs']+packet.get('supplementary_paragraphs',[]);paras={p['id']:p for p in rows}
    require(len(paras)==len(rows),'Duplicate packet paragraph')
    reviews=curation['paragraph_reviews'];require(reviews and all(r['status'] in ('reviewed','pending_textual_review') for r in reviews),'Unreviewed paragraph ledger')
    audit_path=batch.parent/'volume-audit.json'
    if audit_path.exists():
        audit=json.loads(load(audit_path));require(audit['full_volume_source_coverage'] and not audit['publication_verified'],'Volume source/publication audit is not ready')
    files=[];seen=set();paragraph_ids=set()
    for m in manifest:
        pid=m['paragraph_id'];require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',pid or '') and pid in paras,'Invalid manifest paragraph identity')
        require(m['key'] not in seen and pid not in paragraph_ids,'Duplicate manifest source/paragraph');seen.add(m['key']);paragraph_ids.add(pid)
        require(m['file']==pid+'/source.txt','Non-whitelisted manifest file')
        p=paras[pid];require(p.get('source_version') and p.get('book_key'),'Missing source identity/version')
        raw=load(batch/'sources'/pid/'source.txt');loc=p['locator']
        require(m['upstream_locator']==loc and sha(raw)==m['sha256']==loc['raw_excerpt_sha256'],'Snapshot bytes/locator SHA mismatch')
        require(type(loc['char_start']) is int and type(loc['char_end']) is int and loc['char_start']>=0 and loc['char_end']-loc['char_start']==len(raw.decode('utf-8')),'Raw character offsets mismatch (BOM is a character)')
        for name in NAMES:
            local=batch/'sources'/pid/name;value=raw if name=='source.txt' else load(local)
            if name=='paragraph.json':require(json.loads(value)==p,'paragraph.json differs from the packet record')
            files.append(dict(path=relative(prefix+'/'+pid+'/'+name),local_path=relative(str(local.relative_to(root))),sha256=sha(value),bytes=len(value)))
    require(files,'Empty source manifest')
    for name in ('history-batch-workbench.py','reuse-history-sources.py'):load(root/'scripts'/name)
    return packet,manifest,files,protected


def prepare(root,batch,branch,prefix,base='origin/main'):
    root=Path(root).resolve();batch=batch_directory(root,batch)
    unpublished(batch);workflow=inside(root,batch/'.workflow')
    require(not (workflow/'source-archive.json').exists(),'Archive execution already started; use its fixed plan')
    remote=trusted_remote(root);ref=branch_ref(root,branch)
    require(isinstance(base,str) and base.startswith('origin/'),'Base must be an origin branch')
    base_branch=base[len('origin/'):];require(re.fullmatch(r'[A-Za-z0-9._/-]+',base_branch or ''),'Unsafe base ref')
    base_ref='refs/heads/'+base_branch;git(root,'check-ref-format',base_ref)
    previous=remote_head(root,ref);base_head=remote_head(root,base_ref) if previous is None else None
    parent=previous or base_head;require(parent,'Remote base branch is absent')
    try:kind=git(root,'cat-file','-t',parent).strip()
    except subprocess.CalledProcessError as exc:raise ValueError('Parent commit unavailable locally; fetch explicitly before preparing') from exc
    require(kind==b'commit','Parent must be a locally available commit')
    packet,manifest,files,protected=source_inputs(root,batch,prefix)
    for f in files:
        f['old_blob']=parent_blob(root,parent,f['path'])
        require(f['old_blob'] is None or f['old_blob']['sha256']==f['sha256'],'Existing archive bytes differ; immutable path cannot be overwritten')
    plan=dict(format_version=1,kind='history_source_archive',trusted_repo=REPO,batch_directory=str(batch.relative_to(root)),book_key=packet['book_key'],volume=packet['volume'],branch=branch,archive_prefix=prefix,base=base,remote=remote,remote_before=previous,base_head=base_head,parent=parent,files=files,protected_paths=protected,file_count=len(files),total_bytes=sum(f['bytes'] for f in files),changed_paths=sorted(f['path'] for f in files if f['old_blob'] is None))
    unpublished(batch);require(not (workflow/'source-archive.json').exists(),'Archive execution started while preparing')
    save(workflow/'source-upload-plan.json',plan)
    return plan,sha(encoded(plan))


def check_plan(root,batch,plan):
    require(plan['format_version']==1 and plan['kind']=='history_source_archive' and plan['trusted_repo']==REPO,'Wrong archive plan format/repository')
    require(plan['batch_directory']==str(batch.relative_to(root)),'Plan batch mismatch')
    ref=branch_ref(root,plan['branch']);relative(plan['archive_prefix'])
    require(re.fullmatch(r'[a-f0-9]{40}',plan['parent'] or ''),'Invalid planned parent')
    require(plan['parent']==(plan['remote_before'] or plan['base_head']),'Parent differs from the planned remote/base head')
    require(isinstance(plan['base'],str) and plan['base'].startswith('origin/') and re.fullmatch(r'[A-Za-z0-9._/-]+',plan['base'][7:]),'Unsafe planned base')
    git(root,'check-ref-format','refs/heads/'+plan['base'][7:])
    for f in plan['files']:
        relative(f['path']);relative(f['local_path'])
        require(PurePosixPath(f['path']).name in NAMES and PurePosixPath(f['local_path']).name in NAMES,'Non-whitelisted archive file')
        old=parent_blob(root,plan['parent'],f['path'])
        require(old==f['old_blob'],'Parent old blob differs from fixed plan')
        require(old is None or old['sha256']==f['sha256'],'Immutable old archive bytes cannot be replaced')
    require(plan['changed_paths']==sorted(f['path'] for f in plan['files'] if f['old_blob'] is None),'Changed-path plan differs')
    require(plan['file_count']==len(plan['files']) and plan['total_bytes']==sum(f['bytes'] for f in plan['files']),'Plan counts differ')
    require(plan['remote']==trusted_remote(root),'Origin remote changed since preparation')
    return ref


def verify_commit(root,plan,commit):
    require(re.fullmatch(r'[a-f0-9]{40}',commit or ''),'Invalid archive commit')
    for f in plan['files']:
        actual=parent_blob(root,commit,f['path']);require(actual and actual['sha256']==f['sha256'] and actual['bytes']==f['bytes'],'Committed blob differs from plan')
    paths=git(root,'diff','--name-only','-z',plan['parent'],commit).split(b'\0')[:-1]
    require(sorted(x.decode() for x in paths)==plan['changed_paths'],'Commit contains an unrelated diff')
    if commit!=plan['parent']:
        require(git(root,'rev-list','--parents','-n','1',commit).decode().split()==[commit,plan['parent']],'Commit parent is not the fixed parent')


def make_commit(root,plan):
    changed=sorted(f['path'] for f in plan['files'] if f['old_blob'] is None)
    require(changed==plan['changed_paths'],'Changed-path plan differs')
    with tempfile.TemporaryDirectory(prefix='histree-source-index-') as td:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(td)/'index'))
        git(root,'read-tree',plan['parent'],env=env);lines=[]
        for f in plan['files']:
            old=parent_blob(root,plan['parent'],f['path']);require(old==f['old_blob'],'Parent old blob changed')
            require(old is None or old['sha256']==f['sha256'],'Immutable old archive bytes cannot be replaced')
            raw=inside(root,root/f['local_path']).read_bytes()
            require(sha(raw)==f['sha256'] and len(raw)==f['bytes'],'Source changed before Git object creation')
            oid=git(root,'hash-object','-w','--stdin',input=raw).decode().strip()
            require(sha(git(root,'cat-file','blob',oid))==f['sha256'],'Written Git blob differs')
            lines.append('100644 '+oid+'\t'+f['path']+'\n')
        git(root,'update-index','--index-info',env=env,input=''.join(lines).encode())
        diff=git(root,'diff','--cached','--name-only','-z',plan['parent'],env=env).split(b'\0')[:-1]
        require(sorted(x.decode() for x in diff)==changed,'Temporary index contains unrelated changes')
        tree=git(root,'write-tree',env=env).decode().strip()
        commit=git(root,'commit-tree',tree,'-p',plan['parent'],input=b'Archive reviewed history source and paragraph snapshots\n').decode().strip() if changed else plan['parent']
    verify_commit(root,plan,commit);return commit


def link_sources(root,batch,commit,prefix):
    subprocess.run([sys.executable,str(ROOT/'scripts/history-batch-workbench.py'),'--root',str(root),'link-sources',str(batch),'--commit',commit,'--archive-prefix',prefix],cwd=root,check=True)


def reuse_sources(root,batch):
    subprocess.run([sys.executable,str(ROOT/'scripts/reuse-history-sources.py'),str(batch),'--root',str(root),'--apply-local'],cwd=root,check=True,stdout=subprocess.PIPE)


def fixed_url(url):
    parsed=urlsplit(url);m=re.fullmatch(r'/'+REPO+r'/blob/([a-f0-9]{40})/(.+)',parsed.path)
    require(parsed.scheme=='https' and parsed.netloc=='github.com' and not parsed.query and not parsed.fragment and m,'Untrusted/non-fixed source URL')
    path=relative(unquote(m[2]));require(path.startswith(('content/','resources/')) and path.endswith('.txt'),'Non-source fixed URL')
    return f'https://raw.githubusercontent.com/{REPO}/{m[1]}/{quote(path)}'


def raw_lines(value):
    if isinstance(value,dict):
        if isinstance(value.get('rawLines'),list) and all(isinstance(x,str) for x in value['rawLines']):yield value['rawLines']
        for child in value.values():yield from raw_lines(child)
    elif isinstance(value,list):
        for child in value:yield from raw_lines(child)


def verify_url(m):
    url=fixed_url(m['url'])
    def get(target,timeout):
        with urllib.request.urlopen(urllib.request.Request(target,headers={'User-Agent':'Histree-source-verification'}),timeout=timeout) as response:return response.read()
    try:
        require(sha(get(url,15))==m['sha256'],'Anonymous raw SHA mismatch')
        return dict(key=m['key'],url=m['url'],request_url=url,sha256=m['sha256'],verified=True,method='anonymous_raw')
    except Exception:pass
    for attempt in range(3):
        try:
            html=get(m['url'],25).decode('utf-8')
            for block in re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>',html,re.S):
                for lines in raw_lines(json.loads(block)):
                    text='\n'.join(lines)
                    for ending in ('','\n','\n\n'):
                        if sha((text+ending).encode())==m['sha256']:
                            return dict(key=m['key'],url=m['url'],sha256=m['sha256'],verified=True,method='anonymous_immutable_blob_rawLines')
            raise ValueError('No exact SHA in anonymous immutable blob page: '+m['key'])
        except Exception:
            if attempt==2:raise
            time.sleep(1)


def apply(root,batch,expected):
    root=Path(root).resolve();batch=batch_directory(root,batch);unpublished(batch)
    workflow=inside(root,batch/'.workflow');plan_path=workflow/'source-upload-plan.json';raw=inside(root,plan_path).read_bytes()
    require(expected==sha(raw),'Exact plan SHA-256 required; plan changed or not reviewed')
    plan=json.loads(raw);ref=check_plan(root,batch,plan);receipt_path=workflow/'source-archive.json'
    receipt=read(inside(root,receipt_path)) if receipt_path.exists() or receipt_path.is_symlink() else None
    if receipt:require(receipt['plan_sha256']==expected,'Archive receipt belongs to another plan')
    manifest_path=batch/'sources/manifest.json';current_sha=sha(manifest_path.read_bytes())
    allowed={plan['protected_paths'][str(manifest_path.relative_to(root))]}
    if receipt:allowed|={receipt.get('linked_manifest_sha256'),receipt.get('manifest_after_sha256')}
    require(current_sha in allowed,'Manifest changed outside the fixed archive workflow')
    for path,digest in plan['protected_paths'].items():
        if path!=str(manifest_path.relative_to(root)):require(sha(inside(root,root/relative(path)).read_bytes())==digest,'Protected input changed: '+path)
    packet,manifest,files,protected=source_inputs(root,batch,plan['archive_prefix'])
    require(packet['book_key']==plan['book_key'] and packet['volume']==plan['volume'],'Packet identity changed')
    require([{k:v for k,v in f.items() if k!='old_blob'} for f in plan['files']]==files,'Plan file allowlist changed')
    manifest_rel=str(manifest_path.relative_to(root))
    require({k:v for k,v in protected.items() if k!=manifest_rel}=={k:v for k,v in plan['protected_paths'].items() if k!=manifest_rel},'Protected input set changed')
    if receipt:
        commit=receipt['commit'];verify_commit(root,plan,commit)
    else:
        commit=None
    head=remote_head(root,ref)
    if receipt and head==commit:
        receipt.update(pushed=True,status='pushed');save(receipt_path,receipt)
    else:
        require(head==plan['remote_before'],'Concurrent archive branch change; replan')
        if head is None:require(remote_head(root,'refs/heads/'+plan['base'][len('origin/'):])==plan['base_head'],'Concurrent remote base change; replan')
        if commit is None:commit=make_commit(root,plan)
        verify_commit(root,plan,commit)
        receipt=dict(plan_sha256=expected,commit=commit,parent=plan['parent'],branch=plan['branch'],files=plan['file_count'],bytes=plan['total_bytes'],status='local_verified',pushed=False)
        save(receipt_path,receipt);unpublished(batch);require(trusted_remote(root)==plan['remote'],'Origin changed before push')
        require(sha(plan_path.read_bytes())==expected,'Plan changed during execution')
        for path,digest in protected.items():require(sha(inside(root,root/path).read_bytes())==digest,'Protected input changed before push: '+path)
        require(remote_head(root,ref)==plan['remote_before'],'Concurrent branch change immediately before push')
        git(root,'push','--no-verify','--no-follow-tags','--no-mirror','--recurse-submodules=no','--force-with-lease='+ref+':'+(plan['remote_before'] or ''),'origin',commit+':'+ref)
        require(remote_head(root,ref)==commit,'Remote head differs after push')
        receipt.update(pushed=True,status='pushed');save(receipt_path,receipt)
    unpublished(batch)
    require(sha(plan_path.read_bytes())==expected,'Plan changed before manifest linking')
    if not receipt.get('manifest_after_sha256'):
        manifest=read(manifest_path);linked=copy.deepcopy(manifest)
        for m in linked:
            path=plan['archive_prefix']+'/'+m['file']
            m.update(url=f'https://github.com/{REPO}/blob/{commit}/{quote(path)}',snapshot_commit=commit,snapshot_status='committed_source_snapshot',archived_file=path)
        receipt['linked_manifest_sha256']=sha(encoded(linked));save(receipt_path,receipt)
        link_sources(root,batch,commit,plan['archive_prefix'])
        require(sha(manifest_path.read_bytes())==receipt['linked_manifest_sha256'],'link-sources produced unexpected metadata')
        unpublished(batch);reuse_sources(root,batch)
        receipt['manifest_after_sha256']=sha(manifest_path.read_bytes());receipt['status']='linked_and_canonical_reused';save(receipt_path,receipt)
    manifest=read(manifest_path)
    receipt.update(status='anonymous_verification_pending',anonymous_verified=False);save(receipt_path,receipt)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:checks=list(pool.map(verify_url,manifest))
        require(len(checks)==len(manifest) and all(c.get('verified') is True and c.get('key')==m['key'] and c.get('sha256')==m['sha256'] for c,m in zip(checks,manifest)),'Incomplete anonymous verification results')
    except Exception as exc:
        save(workflow/'source-url-verification.json',dict(verified=False,commit=commit,plan_sha256=expected,error=str(exc)))
        receipt.update(status='anonymous_verification_failed',anonymous_verified=False);save(receipt_path,receipt);raise
    unpublished(batch);require(sha(plan_path.read_bytes())==expected,'Plan changed during verification')
    require(sha(manifest_path.read_bytes())==receipt['manifest_after_sha256'],'Manifest changed during anonymous verification')
    save(workflow/'source-url-verification.json',dict(verified=True,commit=commit,plan_sha256=expected,sources=checks))
    receipt.update(status='pushed_anonymously_verified',anonymous_verified=True);save(receipt_path,receipt)
    return receipt


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('batch_directory',type=Path);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--branch');p.add_argument('--archive-prefix');p.add_argument('--base');p.add_argument('--apply',action='store_true');p.add_argument('--expected-plan-sha256')
    args=p.parse_args(argv)
    if args.apply:
        require(args.expected_plan_sha256,'--apply requires --expected-plan-sha256')
        saved=read(inside(args.root.resolve(),batch_directory(args.root.resolve(),args.batch_directory)/'.workflow/source-upload-plan.json'))
        for name in ('branch','archive_prefix','base'):
            require(getattr(args,name) is None or getattr(args,name)==saved[name],'CLI option differs from fixed plan: '+name)
        result=apply(args.root,args.batch_directory,args.expected_plan_sha256)
    else:
        require(args.branch and args.archive_prefix,'Preparation requires --branch and --archive-prefix')
        plan,digest=prepare(args.root,args.batch_directory,args.branch,args.archive_prefix,args.base or 'origin/main')
        result=dict(plan_path=plan['batch_directory']+'/.workflow/source-upload-plan.json',plan_sha256=digest,read_only_git_and_manifest=True,file_count=plan['file_count'],changed_paths=plan['changed_paths'])
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
