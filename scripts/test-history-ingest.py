# coding: utf-8
"""Forward contract tests: synthetic books, real StageRunner, fake engines/DB/HTTP.

No pilot data, credentials, production URL, Git push or actual database is used.
Failures are desired guard assertions, not expectedFailure exemptions: they expose
pipeline gaps for the owner to fix without weakening the contract.
"""
from collections import Counter
from contextlib import ExitStack, redirect_stdout
import copy
import importlib.util
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SCRIPTS=Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:sys.path.insert(0,str(SCRIPTS))
import history_ingest_preflight as P
SPEC=importlib.util.spec_from_file_location('portable_ingest',SCRIPTS/'history-ingest.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class Pipeline(unittest.TestCase):
    def write(self,path,value):P._write_json(path,value)
    def read(self,path):return json.loads(path.read_bytes())
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.book=self.root/'content/books/synthetic-alpha'
        self.batch=self.book/'vol-001/from-start/part-01';self.batch.mkdir(parents=True)
        self.tools=self.root/'scripts';self.tools.mkdir();self.calls=Counter();self.commands=[];self.fail_once=set();self.hide_timeline=False;self.sql=[];self.live={};self.edge_rows=[];self.target_fingerprint='offline-target';self.extra_batch=False
        names={p.name for p in M.engines()}|{'reuse-history-sources.py','archive-history-sources.py'}
        for name in names:
            source=SCRIPTS/name;(self.tools/name).write_bytes(source.read_bytes() if source.exists() else b'# synthetic engine\n')
        self.write(self.root/'apps/web/src/data/history-scroll.json',dict(periods=[dict(label='合成时代',from_year=1,to_year=200)]))
        self.args=types.SimpleNamespace(root=self.root,apply=False,mysql_env=self.root/'offline-mysql.env',api='https://offline.invalid/api/v1',expected_freeze_sha256=None,progress=self.book/'from-start/progress.json',web_proof=self.batch/'.workflow/ui-proof.json')
        self.args.mysql_env.write_text('# no credentials; in-memory fake only\n')
        ps=[];manifest=[]
        for i,text in enumerate(['甲于元年修城。','论曰：此事待考。'],1):
            pid=f'synthetic-alpha-v1-p{i:06d}';raw=text.encode();loc=dict(source_file='resources/synthetic.txt',source_sha256='a'*64,char_start=(i-1)*20,char_end=(i-1)*20+len(text),raw_excerpt_sha256=P.hashlib.sha256(raw).hexdigest())
            p=dict(id=pid,book_key='synthetic-alpha',book='合成甲书',source_version='v1',volume_candidate=1,section_id='synthetic-alpha-s1',section_title='卷一',text=text,locator=loc);ps.append(p)
            d=self.batch/'sources'/pid;d.mkdir(parents=True);(d/'source.txt').write_bytes(raw);self.write(d/'paragraph.json',p)
            manifest.append(dict(key='source-'+pid,paragraph_id=pid,file=pid+'/source.txt',sha256=loc['raw_excerpt_sha256'],upstream_locator=loc,reviewed_citation='《合成甲书》卷1·'+pid,citation_review_note='合成测试逐字已核',source_title='合成甲书·卷1·'+pid,url='https://github.com/greed-216/histree/blob/'+'c'*40+'/content/books/synthetic-alpha/archive/'+pid+'/source.txt',snapshot_commit='c'*40,archived_file='content/books/synthetic-alpha/archive/'+pid+'/source.txt',snapshot_status='committed_source_snapshot'))
        self.write(self.batch/'packet.json',dict(book_key='synthetic-alpha',book='合成甲书',volume=1,source_version='v1',paragraphs=ps,next_paragraph='synthetic-alpha-v1-p000003'))
        self.write(self.batch/'sources/manifest.json',manifest)
        def item(group,row,field,text):return dict(group=group,row=row,evidence=[dict(paragraph_id=ps[0]['id'],field=field,text=text,quote=ps[0]['text'],note='合成fixture已人工核对动作与主语',time_context='元年对应公元100年')])
        person=dict(key='person_synthetic_a',name='合成甲',aliases=[],era='合成时代',birth_year=None,death_year=None,description='合成甲主持修城。',biography=None)
        event=dict(key='event_synthetic_wall',title='合成甲修城',description='公元100年，合成甲主持修城。',start_year=100,end_year=100,dynasty='合成时代',time_original='元年',time_precision='exact',location_precision='unknown',location_lat=None,location_lng=None)
        edge=dict(key='pe_synthetic_a_wall',person_key=person['key'],event_key=event['key'],role='主持修城')
        curated=dict(batch_key='synthetic-alpha-v001',claim_namespace='synthetic-alpha-v001',reused_keys=[],items=[item('people',person,'description',person['description']),item('events',event,'description',event['description']),item('person_events',edge,'role',edge['role'])],paragraph_reviews=[dict(paragraph_id=p['id'],status='reviewed' if i==0 else 'pending_textual_review',note='逐段完成合成审阅',observations=[] if i==0 else ['论说待考，未强制建事件']) for i,p in enumerate(ps)],editorial_checklist=dict(status='complete',reviewer='synthetic-human',events={event['key']:dict(participation=dict(status='complete',required_person_keys=[person['key']],reason='原文明确甲主持'))}))
        self.write(self.batch/'curation.json',curated)
        self.build_outputs()
        plan=dict(kind='synthetic_source_upload',files=[dict(key=m['key'],sha256=m['sha256']) for m in manifest]);self.write(self.batch/'.workflow/source-upload-plan.json',plan)
        plan_sha=M.sha(self.batch/'.workflow/source-upload-plan.json')
        self.write(self.batch/'.workflow/source-archive.json',dict(plan_sha256=plan_sha,commit='c'*40,status='pushed_anonymously_verified',pushed=True,anonymous_verified=True,manifest_after_sha256=M.sha(self.batch/'sources/manifest.json')))
        self.write(self.batch/'.workflow/source-url-verification.json',dict(verified=True,commit='c'*40,plan_sha256=plan_sha,sources=[dict(key=m['key'],url=m['url'],sha256=m['sha256'],verified=True,method='anonymous_immutable_blob_rawLines') for m in manifest]))
        self.write(self.args.progress,dict(book_key='synthetic-alpha',active_cursor=dict(volume=1,next_paragraph=ps[0]['id']),completed_volumes=[],pending_items=[],last_published_paragraph=None))
        self.write(self.args.progress.parent/'index.json',dict(book_key='synthetic-alpha',status='in_progress'))
        self.write(self.args.progress.parent/'source-index.json',dict(book_key='synthetic-alpha',claims=[]))
        self.other=self.root/'content/books/synthetic-beta/from-start/progress.json';self.write(self.other,dict(book_key='synthetic-beta',active_cursor=dict(volume=99,next_paragraph='beta-p1'),completed_volumes=[]));self.other_before=self.other.read_bytes()
        owner=self
        class Cursor:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def execute(self,sql,values=None):owner.sql.append(sql)
            def fetchall(self):return owner.edge_rows
        class Conn:
            def rollback(self):pass
            def begin(self):pass
            def close(self):pass
            def cursor(self,*a,**k):return Cursor()
        class Store:
            def __init__(self,*a,**k):self.connection=Conn();self.target_fingerprint=owner.target_fingerprint
            def request(self,table,*a,**k):return owner.live.get(table,[])
            def normalize(self,table,row):return row
        self.stack=ExitStack();self.stack.enter_context(patch.object(M,'TOOL_ROOT',self.root));self.stack.enter_context(patch.object(P,'__file__',str(self.tools/'history_ingest_preflight.py')))
        self.stack.enter_context(patch.object(P.subprocess,'run',side_effect=self.execute));self.stack.enter_context(patch.object(M,'get',side_effect=self.http));self.stack.enter_context(patch.object(M.urllib.request,'urlopen',side_effect=AssertionError('Unexpected real network')))
        self.stack.enter_context(patch.dict(sys.modules,dict(mysql_content_store=types.SimpleNamespace(MysqlContentStore=Store),pymysql=types.SimpleNamespace(cursors=types.SimpleNamespace(DictCursor=object())))))
    def tearDown(self):self.stack.close();self.tmp.cleanup()
    def build_outputs(self):
        c=self.read(self.batch/'curation.json');packet=self.read(self.batch/'packet.json');manifest=self.read(self.batch/'sources/manifest.json')
        b=dict(format_version=1,batch_key=c['batch_key'],people=[],events=[],person_events=[],person_relationships=[],sources=[],claims=[],topics=[])
        for m in manifest:b['sources'].append(dict(key=m['key'],title=m['source_title'],url=m['url'],source_type='primary',edition='synthetic',note=m['reviewed_citation']))
        table={'people':'person','events':'event','person_events':'person_event','person_relationships':'person_relationship'};claims_by={p['id']:[] for p in packet['paragraphs']}
        for item in c['items']:
            row=dict(item['row'],status='draft');b[item['group']].append(row)
            for j,e in enumerate(item['evidence']):
                m=next(x for x in manifest if x['paragraph_id']==e['paragraph_id']);key=f'claim_{c["batch_key"]}_{row["key"]}_{j}'
                b['claims'].append(dict(key=key,subject_key=row['key'],subject_table=table[item['group']],source_key=m['key'],field_path=e['field'],claim_text=e['text'],citation=m['reviewed_citation'],note='原文：'+e['quote']+'；核对说明：'+e['note'],status='draft'));claims_by[e['paragraph_id']].append(key)
        self.write(self.batch/'content-batch.json',b);self.write(self.batch/'reused-keys.json',c['reused_keys']);self.write(self.batch/'coverage.json',dict(book_key=packet['book_key'],volume=1,paragraphs=list(claims_by)))
        self.write(self.batch/'paragraphs.json',[dict(r,claim_keys=claims_by[r['paragraph_id']],subject_keys=[],publication_status='not_published') for r in c['paragraph_reviews']]);self.write(self.batch/'workbench-validation.json',dict(batch_sha256=M.sha(self.batch/'content-batch.json'),continuous_range_checked=True))
    def execute(self,command,**kwargs):
        command=[str(x) for x in command];self.commands.append(command);program=Path(command[1]).name
        if program=='history-batch-workbench.py':name='build' if 'build' in command else 'volume-audit'
        elif program=='publish-book-batch.py':name='mysql-publish' if '--apply' in command else 'mysql-preflight'
        elif program=='history_sidecars.py':name='sidecars-verify' if '--verify-public' in command else 'sidecars-apply' if '--apply' in command else 'sidecars-plan'
        elif program=='upgrade-content-structure.mjs':name='coverage-apply' if '--apply' in command else 'coverage-plan'
        else:name={'reuse-history-sources.py':'source-reuse','history_ingest_preflight.py':'editorial','validate-history-time.py':'time-review','prepare-book-import.py':'prepare-import','project-review-coverage.py':'coverage-project'}[program]
        self.calls[name]+=1
        if name in self.fail_once:self.fail_once.remove(name);return subprocess.CompletedProcess(command,1)
        if name=='build':self.build_outputs()
        elif name=='editorial':self.write(self.batch/'.workflow/editorial-report.json',dict(ready_to_freeze=True,issues=[]))
        elif name=='time-review':self.write(self.batch/'time-review.json',dict(verified=True,batch_sha256=M.sha(self.batch/'content-batch.json')))
        elif name=='volume-audit':
            packet=self.read(self.batch/'packet.json');parts=[dict(path='part-01',batch_sha256=M.sha(self.batch/'content-batch.json'),paragraphs=[p['id'] for p in packet['paragraphs']])]
            if self.extra_batch:parts.append(dict(path='part-02',batch_sha256='f'*64,paragraphs=['unpublished-third']))
            self.write(self.batch.parent/'volume-audit.json',dict(book_key='synthetic-alpha',source_version='v1',volume=1,full_volume_source_coverage=True,publication_verified=False,paragraphs=3 if self.extra_batch else 2,next_paragraph=packet['next_paragraph'],batches=parts))
        elif name=='prepare-import':
            b=self.read(self.batch/'content-batch.json');self.write(self.batch/'sql/key-map.json',{r['key']:M.sid(r['key']) for g in ('people','events','person_events','person_relationships','claims','sources') for r in b[g]})
        elif name=='mysql-publish':
            b=self.read(self.batch/'content-batch.json');counts={table:len(b[group]) for group,table in [('people','person'),('events','event'),('sources','source'),('person_events','person_event'),('person_relationships','person_relationship'),('claims','fact_claim')]};counts['source_text']=len(b['sources'])
            self.write(self.batch/'publication-mysql.json',dict(verified=True,batch_sha256=M.sha(self.batch/'content-batch.json'),target_fingerprint='offline-target',public_counts=counts,backend='mysql',stages=[dict(stage='anonymous_readback_verified',at='2026-01-01T00:00:00+00:00')]))
        elif name=='sidecars-plan':self.write(self.batch/'.workflow/sidecars-plan.json',dict(batch_sha256=M.sha(self.batch/'content-batch.json'),updates=[]))
        elif name in ('sidecars-apply','sidecars-verify'):self.write(self.batch/'.workflow/sidecars-receipt.json',dict(verified=True,committed=True,batch_sha256=M.sha(self.batch/'content-batch.json'),plan_sha256=M.sha(self.batch/'.workflow/sidecars-plan.json'),target_fingerprint='offline-target'))
        elif name=='coverage-project':self.write(self.batch/'.workflow/coverage.json',dict(coverage=[dict(book_key='synthetic-alpha',volume=1,status='published_fact_subset_verified')],skipped=[],paragraphs=['p1','p2']))
        elif name=='coverage-plan':self.write(self.batch/'.workflow/coverage-structure-plan.json',dict(target_fingerprint=self.target_fingerprint,claim_structure=[],event_dating=[],claim_relations=[],coverage=self.read(self.batch/'.workflow/coverage.json')['coverage']))
        return subprocess.CompletedProcess(command,0)
    def http(self,base,path):
        self.assertEqual(base,self.args.api)
        if path.startswith('/timeline?'):return dict(items=[] if self.hide_timeline else [dict(id=M.sid('event_synthetic_wall'))],has_more=False)
        if path.endswith('/location'):return dict(book_key='synthetic-alpha',section_id='synthetic-alpha-s1',paragraph_id='synthetic-alpha-v1-p000001')
        if '/links?' in path:return dict(items=[dict(claim_id=M.sid(c['key'])) for c in self.read(self.batch/'content-batch.json')['claims']],has_more=False)
        if path=='/library/synthetic-alpha':return dict(coverage=self.read(self.batch/'.workflow/coverage.json')['coverage'])
        raise AssertionError('Unexpected mock HTTP path '+path)
    def ready(self):
        with redirect_stdout(StringIO()):M.ready(self.args,self.batch)
        self.args.expected_freeze_sha256=M.sha(self.batch/'.workflow/freeze.json')
    def published(self):
        self.ready();self.args.apply=True
        with redirect_stdout(StringIO()):M.publish(self.args,self.batch)
        samples=self.read(self.batch/'.workflow/web-samples.json')
        self.write(self.args.web_proof,dict(verified=True,batch_sha256=M.sha(self.batch/'content-batch.json'),book_key='synthetic-alpha',volume=1,quote_expansion_verified=True,observations=[dict(r,book_key='synthetic-alpha',volume=1,observation='实际页面正文、人物连接及卷1原文展开已核') for r in samples['samples']]))
    def accept(self):
        with redirect_stdout(StringIO()):M.accept(self.args,self.batch)
    def test_full_ready_publish_accept_only_moves_selected_book(self):
        authored=(self.batch/'curation.json').read_bytes();self.published();self.accept();p=self.read(self.args.progress)
        self.assertEqual(p['active_cursor'],dict(volume=2,next_paragraph='synthetic-alpha-v1-p000003'));self.assertEqual(p['completed_volumes'],[1]);self.assertEqual(len(p['pending_items']),1)
        self.assertEqual(self.other.read_bytes(),self.other_before);self.assertEqual(self.calls['editorial'],1);self.assertEqual(self.calls['mysql-publish'],1)
        self.assertEqual((self.batch/'curation.json').read_bytes(),authored)
        self.assertTrue(any(sql=='SET TRANSACTION READ ONLY' for sql in self.sql));self.assertTrue(self.read(self.batch/'.workflow/coverage-receipt.json')['verified'])
        before=self.args.progress.read_bytes();self.accept();self.assertEqual(self.args.progress.read_bytes(),before)
    def test_ready_is_read_only_to_mysql_and_requires_source_archive_proof(self):
        (self.batch/'.workflow/source-url-verification.json').unlink()
        with self.assertRaises(FileNotFoundError):self.ready()
        self.assertEqual(self.calls['mysql-publish'],0)
    def test_failed_ready_resumes_without_repeating_editorial(self):
        self.fail_once.add('time-review')
        with self.assertRaises(P.StageExecutionError):self.ready()
        self.ready();self.assertEqual(self.calls['editorial'],1);self.assertEqual(self.calls['build'],1);self.assertEqual(self.calls['time-review'],2);self.assertEqual(self.calls['mysql-preflight'],1)
    def test_failed_sidecar_resumes_without_republishing_mysql(self):
        self.ready();self.args.apply=True;self.fail_once.add('sidecars-apply')
        with self.assertRaises(P.StageExecutionError),redirect_stdout(StringIO()):M.publish(self.args,self.batch)
        with redirect_stdout(StringIO()):M.publish(self.args,self.batch)
        self.assertEqual(self.calls['mysql-publish'],1);self.assertEqual(self.calls['sidecars-apply'],2)
    def test_committed_sidecar_resumes_public_verification_only(self):
        self.published();side=self.batch/'.workflow/sidecars-receipt.json';value=self.read(side);value['verified']=False;self.write(side,value)
        with redirect_stdout(StringIO()):M.publish(self.args,self.batch)
        self.assertEqual(self.calls['sidecars-verify'],1);self.assertEqual(self.calls['sidecars-apply'],1);self.assertEqual(self.calls['mysql-publish'],1)
    def test_unpublished_sibling_batch_blocks_whole_volume_pipeline(self):
        self.extra_batch=True
        with self.assertRaisesRegex(AssertionError,'complete-volume|Multiple batches'):self.ready()
        self.assertEqual(self.calls['mysql-preflight'],0);self.assertFalse((self.batch/'.workflow/freeze.json').exists())
    def test_target_and_public_api_changes_are_blocked_before_write(self):
        self.ready();self.args.apply=True;self.target_fingerprint='other-target'
        with self.assertRaisesRegex(AssertionError,'target database'):M.publish(self.args,self.batch)
        self.target_fingerprint='offline-target';self.args.api='https://other.invalid/api/v1'
        with self.assertRaisesRegex(AssertionError,'public API'):M.publish(self.args,self.batch)
        self.assertEqual(self.calls['mysql-publish'],0)
    def test_period_change_invalidates_editorial_cache_before_freeze(self):
        self.fail_once.add('time-review')
        with self.assertRaises(P.StageExecutionError):self.ready()
        scroll=self.root/'apps/web/src/data/history-scroll.json';value=self.read(scroll);value['periods'][0]['to_year']=201;self.write(scroll,value)
        self.ready();self.assertEqual(self.calls['editorial'],2)
    def test_period_change_after_freeze_blocks_publish(self):
        self.ready();self.args.apply=True;scroll=self.root/'apps/web/src/data/history-scroll.json';scroll.write_bytes(scroll.read_bytes()+b' ')
        with self.assertRaisesRegex(AssertionError,'period data'):M.publish(self.args,self.batch)
        self.assertEqual(self.calls['mysql-publish'],0)

    def test_field_source_and_tool_mutation_block_frozen_publish(self):
        self.ready();self.args.apply=True
        for path in [self.batch/'curation.json',self.batch/'sources/synthetic-alpha-v1-p000001/source.txt',self.tools/'history-batch-workbench.py']:
            old=path.read_bytes()
            if path.name=='curation.json':
                value=self.read(path);value['items'][1]['row']['description']='未经授权改写事件字段';self.write(path,value)
            else:path.write_bytes(old+b' ')
            with self.assertRaises(AssertionError):M.publish(self.args,self.batch)
            path.write_bytes(old)
        self.assertEqual(self.calls['mysql-publish'],0)
    def test_reuse_engine_change_must_invalidate_freeze(self):
        self.ready();self.args.apply=True;path=self.tools/'reuse-history-sources.py';path.write_bytes(path.read_bytes()+b'\n# changed source selection\n')
        with self.assertRaises(AssertionError):M.frozen(self.args,self.batch)
    def test_stale_source_proof_must_not_freeze(self):
        proof=self.read(self.batch/'.workflow/source-url-verification.json');proof['sources'][0]['sha256']='0'*64;self.write(self.batch/'.workflow/source-url-verification.json',proof)
        with self.assertRaises((AssertionError,ValueError)):self.ready()
    def test_online_existing_new_key_and_duplicate_edge_block(self):
        self.live['person']=[dict(id=M.sid('person_synthetic_a'),status='published')]
        with self.assertRaises(AssertionError):self.ready()
        self.assertEqual(self.calls['mysql-preflight'],0)
        self.live={};self.edge_rows=[dict(id='different-edge-id',person_id=M.sid('person_synthetic_a'),event_id=M.sid('event_synthetic_wall'),role='主持修城')]
        with self.assertRaises(AssertionError):M.online_check(self.args,self.batch)
    def test_publish_requires_apply_and_exact_freeze(self):
        self.ready()
        with self.assertRaises(AssertionError):M.publish(self.args,self.batch)
        self.args.apply=True;self.args.expected_freeze_sha256='0'*64
        with self.assertRaises(AssertionError):M.publish(self.args,self.batch)
    def test_wrong_ui_volume_or_path_must_block_progress(self):
        self.published();ui=self.read(self.args.web_proof);ui['volume']=99
        for r in ui['observations']:r['volume']=99;r['path']='/library/synthetic-alpha/wrong-volume'
        self.write(self.args.web_proof,ui);old=self.args.progress.read_bytes()
        with self.assertRaises(AssertionError):self.accept()
        self.assertEqual(self.args.progress.read_bytes(),old)
    def test_ui_missing_samples_or_empty_observation_blocks(self):
        self.published();ui=self.read(self.args.web_proof);old=copy.deepcopy(ui)
        for altered in [dict(ui,observations=[]),dict(ui,observations=[dict(r,observation='') for r in ui['observations']])]:
            self.write(self.args.web_proof,altered)
            with self.assertRaises(AssertionError):self.accept()
        self.write(self.args.web_proof,old)
    def test_wrong_book_progress_and_cursor_do_not_advance(self):
        self.published();progress=self.read(self.args.progress)
        for changed in [dict(progress,book_key='synthetic-beta'),dict(progress,active_cursor=dict(volume=1,next_paragraph='wrong-start'))]:
            self.write(self.args.progress,changed);old=self.args.progress.read_bytes()
            with self.assertRaises(AssertionError):self.accept()
            self.assertEqual(self.args.progress.read_bytes(),old)
    def test_other_book_cannot_use_already_accepted_shortcut(self):
        self.published();self.accept();p=self.read(self.args.progress);p['book_key']='synthetic-beta';self.write(self.other,p);self.args.progress=self.other
        with self.assertRaises(AssertionError):self.accept()
    def test_empty_public_counts_must_block_acceptance(self):
        self.published();receipt=self.batch/'publication-mysql.json';a=self.read(receipt);a['public_counts']={};self.write(receipt,a)
        with self.assertRaises(AssertionError):self.accept()
    def test_anonymous_proof_from_another_api_or_target_cannot_advance(self):
        self.published();path=self.batch/'.workflow/public-acceptance.json';old=self.read(path)
        for changes in [dict(public_api_url='https://wrong.invalid/api/v1'),dict(target_fingerprint='other-target')]:
            self.write(path,dict(old,**changes))
            with self.assertRaises(AssertionError):self.accept()

    def test_missing_publication_component_blocks_progress(self):
        self.published();old=self.args.progress.read_bytes()
        for path in [self.batch/'publication-mysql.json',self.batch/'.workflow/sidecars-receipt.json',self.batch/'.workflow/public-acceptance.json']:
            value=self.read(path);self.write(path,dict(value,verified=False))
            with self.assertRaises(AssertionError):self.accept()
            self.write(path,value)
        self.assertEqual(self.args.progress.read_bytes(),old)
    def test_missing_annual_event_does_not_create_acceptance(self):
        self.ready();self.args.apply=True;self.hide_timeline=True
        with self.assertRaises(AssertionError),redirect_stdout(StringIO()):M.publish(self.args,self.batch)
        self.assertFalse((self.batch/'.workflow/public-acceptance.json').exists())


if __name__=='__main__':unittest.main()
