# coding: utf-8
"""Self-contained temporary bare-Git fixtures; mocked transport/HTTP, no DB."""
import copy
from contextlib import ExitStack, redirect_stdout
import importlib.util
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('archive_history',Path(__file__).with_name('archive-history-sources.py'))
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class Tests(unittest.TestCase):
    def rawgit(self,*args,input=None):
        return subprocess.run(['git',*args],cwd=self.root,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
    def write(self,path,obj):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(M.encoded(obj))
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()/'repo';self.root.mkdir()
        self.bare=self.root.parent/'remote.git';self.rawgit('init','-q');self.rawgit('config','user.name','Offline fixture');self.rawgit('config','user.email','offline@example.invalid')
        (self.root/'README').write_text('Initial tree\n');self.rawgit('add','README');self.rawgit('commit','-qm','base')
        self.rawgit('init','--bare','-q',str(self.bare));self.rawgit('push',str(self.bare),'HEAD:refs/heads/main')
        self.rawgit('remote','add','origin','https://github.com/greed-216/histree.git')
        self.parent=self.rawgit('rev-parse','HEAD').decode().strip();self.rawgit('update-ref','refs/remotes/origin/main',self.parent)
        self.batch=self.root/'content/books/songshi/vol-206/from-start/part-01';self.prefix='content/books/songshi/runs/offline/source-archive';self.branch='codex/offline-sources'
        for name in ('history-batch-workbench.py','reuse-history-sources.py'):
            path=self.root/'scripts'/name;path.parent.mkdir(exist_ok=True);path.write_text('# fixed fixture helper\n')
        self.populate(1)
        (self.root/'unrelated.txt').write_text('User staged work\n');self.rawgit('add','unrelated.txt');self.index=(self.root/'.git/index').read_bytes()
        self.pushes=0;self.order=[];self.before_push=None;realgit=M.git
        def transport(root,*args,**kwargs):
            args=list(args)
            if args and args[0] in ('ls-remote','push') and 'origin' in args:
                if args[0]=='push':
                    self.pushes+=1
                    if self.before_push:self.before_push()
                args[args.index('origin')]=str(self.bare)
            return realgit(root,*args,**kwargs)
        def linker(root,batch,commit,prefix):
            self.order.append('link-sources');manifest=M.read(batch/'sources/manifest.json')
            for m in manifest:
                path=prefix+'/'+m['file'];m.update(url=f'https://github.com/{M.REPO}/blob/{commit}/{path}',snapshot_commit=commit,snapshot_status='committed_source_snapshot',archived_file=path)
            self.write(batch/'sources/manifest.json',manifest)
        def reuser(root,batch):self.order.append('reuse-history-sources --apply-local')
        self.stack=ExitStack();self.stack.enter_context(patch.object(M,'git',side_effect=transport));self.stack.enter_context(patch.object(M,'link_sources',side_effect=linker));self.stack.enter_context(patch.object(M,'reuse_sources',side_effect=reuser));self.stack.enter_context(patch.object(M,'verify_url',side_effect=lambda m:dict(key=m['key'],url=m['url'],sha256=m['sha256'],verified=True,method='offline_mock')))
    def tearDown(self):self.stack.close();self.tmp.cleanup()
    def populate(self,count,bom=False):
        paragraphs=[];manifest=[]
        for i in range(count):
            pid=f'songshi-v1-p{i+1:06d}';text=('\ufeff' if bom else '')+f'原文第{i+1}段。\n';raw=text.encode()
            loc=dict(char_start=100*i,char_end=100*i+len(text),source_sha256='a'*64,raw_excerpt_sha256=M.sha(raw),line_start=i+1,line_end=i+1,source_file='resources/originals/songshi.txt')
            p=dict(id=pid,book='宋史',book_key='songshi',source_version='v1',volume_candidate=206,section_id='songshi-s206',locator=loc,text=text)
            paragraphs.append(p);d=self.batch/'sources'/pid;d.mkdir(parents=True,exist_ok=True);(d/'source.txt').write_bytes(raw);self.write(d/'paragraph.json',p)
            manifest.append(dict(key='source-'+pid,paragraph_id=pid,file=pid+'/source.txt',sha256=M.sha(raw),upstream_locator=loc,url='https://github.com/greed-216/histree/blob/'+'b'*40+'/unlinked.txt',source_title='宋史·卷206·'+pid,reviewed_citation='《宋史》卷206·'+pid))
        self.write(self.batch/'packet.json',dict(book_key='songshi',book='宋史',volume=206,paragraphs=paragraphs))
        self.write(self.batch/'curation.json',dict(paragraph_reviews=[dict(paragraph_id=p['id'],status='reviewed') for p in paragraphs]))
        self.write(self.batch/'sources/manifest.json',manifest)
    def prepare(self):return M.prepare(self.root,self.batch,self.branch,self.prefix)
    def archive(self):
        plan,digest=self.prepare();return plan,digest,M.apply(self.root,self.batch,digest)
    def gitobjects(self):return {str(p.relative_to(self.root)):M.sha(p.read_bytes()) for p in (self.root/'.git/objects').rglob('*') if p.is_file()}
    def change_remote(self,branch):
        tree=self.rawgit('rev-parse','HEAD^{tree}').decode().strip();commit=self.rawgit('commit-tree',tree,'-p',self.parent,input=b'Concurrent branch actor\n').decode().strip()
        self.rawgit('push',str(self.bare),commit+':refs/heads/'+branch);return commit
    def test_default_cli_only_writes_plan_no_objects_index_or_manifest(self):
        old=self.gitobjects();manifest=(self.batch/'sources/manifest.json').read_bytes();out=StringIO()
        with redirect_stdout(out):self.assertEqual(M.main([str(self.batch),'--root',str(self.root),'--branch',self.branch,'--archive-prefix',self.prefix,'--base','origin/main']),0)
        result=json.loads(out.getvalue());plan_path=self.batch/'.workflow/source-upload-plan.json'
        self.assertEqual(result['plan_sha256'],M.sha(plan_path.read_bytes()));self.assertTrue(result['read_only_git_and_manifest'])
        self.assertEqual(self.gitobjects(),old);self.assertEqual((self.root/'.git/index').read_bytes(),self.index);self.assertEqual((self.batch/'sources/manifest.json').read_bytes(),manifest);self.assertEqual(self.pushes,0)
        self.assertEqual(list((self.batch/'.workflow').iterdir()),[plan_path])
    def test_apply_has_only_allowlisted_diff_preserves_user_index_and_order(self):
        plan,digest,receipt=self.archive();self.assertEqual(self.pushes,1);self.assertTrue(receipt['anonymous_verified'])
        self.assertEqual((self.root/'.git/index').read_bytes(),self.index);self.assertEqual(self.order,['link-sources','reuse-history-sources --apply-local'])
        diff=self.rawgit('diff','--name-only',self.parent,receipt['commit']).decode().splitlines();self.assertEqual(sorted(diff),plan['changed_paths']);self.assertEqual(len(diff),2)
        self.assertTrue(all(Path(p).name in M.NAMES for p in diff));self.assertNotIn('unrelated.txt',diff)
        self.assertTrue(M.read(self.batch/'.workflow/source-url-verification.json')['verified'])
        M.apply(self.root,self.batch,digest);self.assertEqual(self.pushes,1)
    def test_exact_plan_sha_and_tampering_rejected(self):
        plan,digest=self.prepare();p=self.batch/'.workflow/source-upload-plan.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Exact plan SHA'):M.apply(self.root,self.batch,digest)
        self.assertEqual(self.pushes,0)
    def test_rehashed_nonwhitelisted_file_and_parent_are_rejected(self):
        plan,digest=self.prepare();path=self.batch/'.workflow/source-upload-plan.json'
        plan['files'][0]['path']=self.prefix+'/credentials.env';self.write(path,plan)
        with self.assertRaisesRegex(ValueError,'Non-whitelisted'):M.apply(self.root,self.batch,M.sha(path.read_bytes()))
        plan['files'][0]['path']=self.prefix+'/songshi-v1-p000001/source.txt';plan['parent']='f'*40;self.write(path,plan)
        with self.assertRaisesRegex(ValueError,'Parent differs'):M.apply(self.root,self.batch,M.sha(path.read_bytes()))
    def test_rehashed_whitelist_basename_at_wrong_path_is_rejected(self):
        plan,digest=self.prepare();path=self.batch/'.workflow/source-upload-plan.json';plan['files'][0]['local_path']='private/source.txt';self.write(path,plan)
        with self.assertRaisesRegex(ValueError,'allowlist'):M.apply(self.root,self.batch,M.sha(path.read_bytes()))
        self.assertEqual(self.pushes,0)
    def test_line_injection_and_path_traversal_rejected(self):
        for branch,prefix in [(self.branch+'\nrefs/heads/main',self.prefix),(self.branch,self.prefix+'\t100644 malicious'),(self.branch,'../outside'),(self.branch,'content/books/songshi/../../secrets')]:
            with self.assertRaises((ValueError,subprocess.CalledProcessError)):M.prepare(self.root,self.batch,branch,prefix)
        self.assertEqual(self.pushes,0)
    def test_local_batch_path_with_control_character_rejected(self):
        new=self.batch.parent/'part-with\nnewline';shutil.move(str(self.batch),new)
        with self.assertRaisesRegex(ValueError,'control/line injection'):M.prepare(self.root,new,self.branch,self.prefix)
    def test_wrong_remote_fetch_or_push_url_rejected(self):
        self.rawgit('remote','set-url','origin','https://github.com/attacker/repo.git')
        with self.assertRaisesRegex(ValueError,'Untrusted origin'):self.prepare()
        self.rawgit('remote','set-url','origin','https://github.com/greed-216/histree.git');self.rawgit('remote','set-url','--push','origin','/tmp/other.git')
        with self.assertRaisesRegex(ValueError,'Untrusted origin'):self.prepare()
    def test_inherited_git_dir_and_index_cannot_redirect_repository(self):
        foreign=self.root.parent/'foreign-index';foreign.write_bytes(b'not a Git index')
        with patch.dict(os.environ,dict(GIT_DIR=str(self.bare),GIT_WORK_TREE=str(self.root.parent),GIT_INDEX_FILE=str(foreign))):
            plan,digest=self.prepare()
        self.assertEqual(foreign.read_bytes(),b'not a Git index');self.assertEqual(plan['parent'],self.parent)
    def test_publication_receipts_block_prepare_and_apply(self):
        plan,digest=self.prepare();before=(self.batch/'sources/manifest.json').read_bytes()
        for name in ('publication.json','publication-mysql.json'):
            p=self.batch/name;self.write(p,dict(verified=False))
            with self.assertRaisesRegex(ValueError,'Publication started'):self.prepare()
            with self.assertRaisesRegex(ValueError,'Publication started'):M.apply(self.root,self.batch,digest)
            p.unlink()
        self.assertEqual((self.batch/'sources/manifest.json').read_bytes(),before);self.assertEqual(self.pushes,0)
    def test_changed_input_and_helper_block_apply(self):
        plan,digest=self.prepare();p=self.batch/'sources/songshi-v1-p000001/source.txt';before=p.read_bytes();p.write_bytes(before+b'x')
        with self.assertRaisesRegex(ValueError,'Protected input changed'):M.apply(self.root,self.batch,digest)
        p.write_bytes(before);(self.root/'scripts/reuse-history-sources.py').write_text('# changed helper\n')
        with self.assertRaisesRegex(ValueError,'Protected input changed'):M.apply(self.root,self.batch,digest)
    def test_concurrent_branch_and_base_changes_rejected_before_push(self):
        plan,digest=self.prepare();self.change_remote(self.branch)
        with self.assertRaisesRegex(ValueError,'Concurrent archive branch'):M.apply(self.root,self.batch,digest)
        self.assertEqual(self.pushes,0)
    def test_concurrent_base_change_rejected(self):
        plan,digest=self.prepare();self.change_remote('main')
        with self.assertRaisesRegex(ValueError,'Concurrent remote base'):M.apply(self.root,self.batch,digest)
    def test_atomic_remote_lease_rejects_change_after_preflight(self):
        plan,digest=self.prepare();before=(self.batch/'sources/manifest.json').read_bytes()
        self.before_push=lambda:self.change_remote(self.branch)
        with self.assertRaises(subprocess.CalledProcessError):M.apply(self.root,self.batch,digest)
        self.assertEqual((self.batch/'sources/manifest.json').read_bytes(),before);self.assertEqual(self.order,[])
    def test_existing_archive_different_bytes_rejected_at_preparation(self):
        path=self.root/self.prefix/'songshi-v1-p000001/source.txt';path.parent.mkdir(parents=True);path.write_text('Different ancient text\n')
        self.rawgit('add',str(path));self.rawgit('commit','-qm','conflicting archive');self.rawgit('push',str(self.bare),'HEAD:refs/heads/main')
        with self.assertRaisesRegex(ValueError,'Existing archive bytes differ'):self.prepare()
    def install_archive_in_parent(self):
        target=self.root/self.prefix/'songshi-v1-p000001';target.mkdir(parents=True)
        for name in M.NAMES:shutil.copyfile(self.batch/'sources/songshi-v1-p000001'/name,target/name)
        self.rawgit('add',self.prefix);self.rawgit('commit','-qm','archive fixture')
        return self.rawgit('rev-parse','HEAD').decode().strip()
    def test_identical_old_blobs_are_kept_without_a_new_commit(self):
        parent=self.install_archive_in_parent();self.rawgit('push',str(self.bare),parent+':refs/heads/main')
        index=(self.root/'.git/index').read_bytes();plan,digest,receipt=self.archive()
        self.assertEqual(plan['changed_paths'],[]);self.assertTrue(all(f['old_blob'] for f in plan['files']))
        self.assertEqual(receipt['commit'],parent);self.assertEqual((self.root/'.git/index').read_bytes(),index)
    def test_forged_receipt_commit_with_unrelated_diff_is_rejected(self):
        plan,digest=self.prepare();commit=self.install_archive_in_parent()
        self.write(self.batch/'.workflow/source-archive.json',dict(plan_sha256=digest,commit=commit,pushed=False))
        with self.assertRaisesRegex(ValueError,'unrelated diff'):M.apply(self.root,self.batch,digest)
        self.assertEqual(self.pushes,0)
    def test_old_blob_guard_not_trusted_even_with_rereviewed_plan(self):
        plan,digest=self.prepare();plan['files'][0]['old_blob']=dict(oid='f'*40,sha256='0'*64,bytes=1);path=self.batch/'.workflow/source-upload-plan.json';self.write(path,plan)
        with self.assertRaisesRegex(ValueError,'old blob|Changed-path'):M.apply(self.root,self.batch,M.sha(path.read_bytes()))
        self.assertEqual(self.pushes,0)
    def test_bom_and_paragraph_packet_exactness(self):
        self.populate(1,bom=True);plan,digest,receipt=self.archive()
        first=next(f for f in plan['files'] if f['path'].endswith('/source.txt'));self.assertEqual(self.rawgit('show',receipt['commit']+':'+first['path']),(self.root/first['local_path']).read_bytes())
    def test_wrong_locator_or_paragraph_json_rejected(self):
        p=self.batch/'sources/songshi-v1-p000001/paragraph.json';obj=M.read(p);obj['source_version']='wrong';self.write(p,obj)
        with self.assertRaisesRegex(ValueError,'paragraph.json differs'):self.prepare()
    def test_symlink_source_outside_root_rejected(self):
        path=self.batch/'sources/songshi-v1-p000001/source.txt';outside=self.root.parent/'outside.txt';outside.write_bytes(path.read_bytes());path.unlink();path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError,'escapes root'):self.prepare()
    def test_concurrency_is_bounded_to_six(self):
        self.populate(12);lock=threading.Lock();active=0;maximum=0
        def check(m):
            nonlocal active,maximum
            with lock:active+=1;maximum=max(maximum,active)
            time.sleep(.02)
            with lock:active-=1
            return dict(key=m['key'],sha256=m['sha256'],verified=True)
        with patch.object(M,'verify_url',side_effect=check):self.archive()
        self.assertEqual(maximum,6)
    def test_anonymous_failure_is_recorded_and_can_resume_without_repush(self):
        plan,digest=self.prepare()
        with patch.object(M,'verify_url',side_effect=ValueError('anonymous failed')):
            with self.assertRaisesRegex(ValueError,'anonymous failed'):M.apply(self.root,self.batch,digest)
        self.assertFalse(M.read(self.batch/'.workflow/source-url-verification.json')['verified']);self.assertEqual(self.pushes,1)
        receipt=M.read(self.batch/'.workflow/source-archive.json');self.assertFalse(receipt['anonymous_verified']);self.assertEqual(receipt['status'],'anonymous_verification_failed')
        M.apply(self.root,self.batch,digest);self.assertEqual(self.pushes,1)
    def test_lost_push_ack_resumes_by_exact_verified_commit_without_repush(self):
        plan,digest=self.prepare();transport=M.git
        def ack_lost(root,*args,**kwargs):
            result=transport(root,*args,**kwargs)
            if args[0]=='push':raise OSError('push acknowledgement lost')
            return result
        with patch.object(M,'git',side_effect=ack_lost):
            with self.assertRaisesRegex(OSError,'acknowledgement'):M.apply(self.root,self.batch,digest)
        self.assertFalse(M.read(self.batch/'.workflow/source-archive.json')['pushed'])
        receipt=M.apply(self.root,self.batch,digest);self.assertTrue(receipt['anonymous_verified']);self.assertEqual(self.pushes,1)
    def test_apply_cli_requires_expected_digest_and_matching_options(self):
        plan,digest=self.prepare()
        with self.assertRaisesRegex(ValueError,'requires --expected'):M.main([str(self.batch),'--root',str(self.root),'--apply'])
        with self.assertRaisesRegex(ValueError,'CLI option differs'):M.main([str(self.batch),'--root',str(self.root),'--apply','--expected-plan-sha256',digest,'--branch','codex/different'])
    def test_actual_linker_command_contracts(self):
        # Functions are mocked for the Git pipeline; call their originals here with subprocess mocked.
        with patch.object(M.subprocess,'run') as run:
            self.stack.close()
            M.link_sources(self.root,self.batch,self.parent,self.prefix);M.reuse_sources(self.root,self.batch)
            args=[x.args[0] for x in run.call_args_list]
            self.assertEqual(Path(args[0][1]).name,'history-batch-workbench.py');self.assertIn('link-sources',args[0])
            self.assertEqual(Path(args[1][1]).name,'reuse-history-sources.py');self.assertIn('--apply-local',args[1]);self.assertIn('--root',args[1])
            self.assertEqual(Path(args[0][1]).parent,M.ROOT/'scripts');self.assertEqual(Path(args[1][1]).parent,M.ROOT/'scripts')
            self.assertEqual(args[0][args[0].index('--root')+1],str(self.root))
            self.assertEqual(args[1][args[1].index('--root')+1],str(self.root))


class UrlTests(unittest.TestCase):
    def setUp(self):
        self.raw='\ufeff原文。\n'.encode();self.m=dict(key='s',url='https://github.com/greed-216/histree/blob/'+'a'*40+'/content/books/songshi/s/source.txt',sha256=M.sha(self.raw))
    def test_raw_bytes_are_checked(self):
        with patch.object(M.urllib.request,'urlopen',return_value=BytesIO(self.raw)):
            proof=M.verify_url(self.m)
            self.assertEqual(proof['method'],'anonymous_raw')
            self.assertEqual(proof['url'],self.m['url'])
            self.assertEqual(proof['request_url'],M.fixed_url(self.m['url']))
    def test_raw_failure_uses_only_sha_exact_immutable_rawlines(self):
        html=('<script type="application/json">'+json.dumps(dict(payload=dict(rawLines=['\ufeff原文。'])))+'</script>').encode()
        with patch.object(M.urllib.request,'urlopen',side_effect=[OSError('raw down'),BytesIO(html)]):
            self.assertEqual(M.verify_url(self.m)['method'],'anonymous_immutable_blob_rawLines')
    def test_wrong_raw_and_html_bytes_never_verify(self):
        html=b'<script type="application/json">{"rawLines":["wrong"]}</script>'
        with patch.object(M.urllib.request,'urlopen',side_effect=lambda *a,**k:BytesIO(html)),patch.object(M.time,'sleep'):
            with self.assertRaisesRegex(ValueError,'No exact SHA'):M.verify_url(self.m)
    def test_untrusted_or_nonfixed_url_rejected_before_network(self):
        for url in [self.m['url'].replace('greed-216/histree','other/repo'),self.m['url'].replace('a'*40,'main'),self.m['url']+'?token=x',self.m['url'].replace('/s/source.txt','/%0as/source.txt')]:
            with patch.object(M.urllib.request,'urlopen') as fetch:
                with self.assertRaises(ValueError):M.verify_url(dict(self.m,url=url))
                fetch.assert_not_called()


if __name__=='__main__':unittest.main()
