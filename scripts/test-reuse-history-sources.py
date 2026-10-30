# coding: utf-8
"""Offline temporary Git fixtures only; no existing batch or database writes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from io import StringIO

SPEC=importlib.util.spec_from_file_location('reuse_history',Path(__file__).with_name('reuse-history-sources.py'))
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class Tests(unittest.TestCase):
    book_key="shiji"
    book="史记"
    volume=17
    def git(self,*args):
        p=subprocess.run(['git',*args],cwd=self.root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        return p.stdout.decode().strip()
    def write(self,path,obj):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(M.encoded(obj))
    def read(self,path):return json.loads(path.read_bytes())
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
        self.git('init','-q');self.old=self.root/f'content/books/{self.book_key}/vol-011/from-start/part-01';self.cur=self.root/f'content/books/{self.book_key}/vol-{self.volume:03d}/from-start/part-01'
        self.pid=self.book_key+'-version1-p001860';self.key=self.book_key+'-'+self.pid;self.sid=str(uuid.uuid5(uuid.NAMESPACE_URL,self.key))
        self.text=getattr(self,'bom','')+'156\t孝景元年';raw=self.text.encode();sh=M.sha(raw)
        self.archive=f'content/books/{self.book_key}/runs/offline/source-archive/'+self.pid+'/source.txt'
        path=self.root/self.archive;path.parent.mkdir(parents=True);path.write_bytes(raw)
        self.git('add','content');self.git('-c','user.name=Offline Tests','-c','user.email=offline@example.invalid','commit','-qm','snapshot')
        self.commit=self.git('rev-parse','HEAD');url='https://github.com/greed-216/histree/blob/'+self.commit+'/'+self.archive
        self.para=dict(id=self.pid,book_key=self.book_key,book=self.book,source_version='version1',volume_candidate=self.volume,section_id=self.book_key+'-version1-s0018',text=self.text,kind='table_row',locator=dict(source_file=f'resources/originals/{self.book_key}.txt',source_sha256='d'*64,original_file=f'backup/{self.book_key}.epub',original_sha256='e'*64,char_start=100,char_end=100+len(self.text),line_start=5,line_end=5,raw_excerpt_sha256=sh),citation=f'《{self.book}》卷{self.volume}·汉兴以来诸侯王年表·'+self.pid)
        self.title=f'{self.book}·卷{self.volume}·汉兴以来诸侯王年表·景帝元年'
        self.note=f'《{self.book}》卷{self.volume}·汉兴以来诸侯王年表·景帝元年·'+self.pid
        self.source=dict(key=self.key,title=self.title,source_type='primary',author=M.AUTHORS.get(self.book_key),edition=M.EDITION,url=url,note=self.note)
        old_m=dict(key=self.key,paragraph_id=self.pid,file=self.pid+'/source.txt',sha256=sh,upstream_locator=copy.deepcopy(self.para['locator']),url=url,source_title=self.title,reviewed_citation=self.note,citation_review_note='篇名及纪年已核',snapshot_commit=self.commit,archived_file=self.archive,snapshot_status='committed_source_snapshot')
        self.write(self.old/'packet.json',dict(book_key=self.book_key,volume=11,paragraphs=[],supplementary_paragraphs=[self.para]))
        self.write(self.old/'sources/manifest.json',[old_m]);(self.old/'sources'/self.pid).mkdir();(self.old/'sources'/self.pid/'source.txt').write_bytes(raw)
        self.write(self.old/'content-batch.json',dict(batch_key='old',sources=[self.source],claims=[]));self.write(self.old/'sql/key-map.json',{self.key:self.sid});self.refresh_receipt()
        current=copy.deepcopy(old_m);current.update(url='https://github.com/greed-216/histree/blob/'+'b'*40+'/'+self.archive,snapshot_commit='b'*40,source_title=f'{self.book}·卷{self.volume}·汉兴以来诸侯王年表·'+self.pid,reviewed_citation=self.para['citation'])
        newp=copy.deepcopy(self.para);newp.update(id=self.book_key+'-version1-p001861',text='155\t二');newp['locator'].update(char_start=200,char_end=205,raw_excerpt_sha256=M.sha('155\t二'.encode()))
        newkey=self.book_key+'-'+newp['id'];newm=copy.deepcopy(current);newm.update(key=newkey,paragraph_id=newp['id'],file=newp['id']+'/source.txt',sha256=newp['locator']['raw_excerpt_sha256'],upstream_locator=copy.deepcopy(newp['locator']),source_title=f'{self.book}·卷{self.volume}·汉兴以来诸侯王年表·'+newp['id'],reviewed_citation=f'《{self.book}》卷{self.volume}·汉兴以来诸侯王年表·'+newp['id'])
        self.write(self.cur/'packet.json',dict(book_key=self.book_key,volume=self.volume,paragraphs=[self.para,newp]))
        self.write(self.cur/'sources/manifest.json',[current,newm])
        for p,rawtxt in [(self.para,self.text),(newp,newp['text'])]:
            path=self.cur/'sources'/p['id']/'source.txt';path.parent.mkdir();path.write_bytes(rawtxt.encode())
        self.current_before=(self.cur/'sources/manifest.json').read_bytes()
    def refresh_receipt(self):
        self.write(self.old/'publication-mysql.json',dict(backend='mysql',verified=True,batch_sha256=M.sha((self.old/'content-batch.json').read_bytes()),stages=[dict(stage='published_source',at='2026-10-20T01:00:00+00:00')]))
    def tearDown(self):self.tmp.cleanup()
    def test_check_restores_same_paragraph_across_two_volumes_without_writes(self):
        plan,before,after=M.prepare(self.root,self.cur)
        self.assertEqual(len(plan['changes']),1);self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)
        self.assertEqual(after[0]['url'],self.source['url']);self.assertEqual(after[0]['source_title'],self.source['title']);self.assertEqual(after[0]['reviewed_citation'],self.source['note'])
        self.assertEqual(after[0]['original_reviewed_citation'],self.para['citation'])
        self.assertEqual(after[0]['canonical_source_reuse']['canonical_batch_sha256'],M.sha((self.old/'content-batch.json').read_bytes()))
        self.assertEqual(after[1],json.loads(self.current_before)[1])
        regenerated=dict(key=after[0]['key'],title=after[0]['source_title'],source_type='primary',author=M.AUTHORS.get(self.book_key),edition=M.EDITION,url=after[0]['url'],note=after[0]['reviewed_citation'])
        self.assertEqual(regenerated,self.source)
    def test_apply_local_is_single_manifest_atomic_and_idempotent(self):
        old_protected={p:M.sha((self.root/p).read_bytes()) for p in [str((self.old/'sources/manifest.json').relative_to(self.root)),str((self.old/'content-batch.json').relative_to(self.root)),str((self.old/'publication-mysql.json').relative_to(self.root))]}
        plan,before,after=M.prepare(self.root,self.cur);self.assertTrue(M.apply_local(self.root,plan,before,after))
        plan2,before2,after2=M.prepare(self.root,self.cur);self.assertEqual(plan2['changes'],[]);self.assertFalse(M.apply_local(self.root,plan2,before2,after2))
        for p,digest in old_protected.items():self.assertEqual(M.sha((self.root/p).read_bytes()),digest)
        self.assertFalse(list((self.cur/'sources').glob('.reuse-history-sources-*')))
    def test_any_changed_snapshot_byte_is_rejected(self):
        p=self.cur/'sources'/self.pid/'source.txt';p.write_bytes(p.read_bytes()+b'!')
        with self.assertRaisesRegex(ValueError,'snapshot SHA'):M.prepare(self.root,self.cur)
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)
    def test_consistently_rehashed_different_excerpt_still_rejected(self):
        raw='156\t孝景二年'.encode();self.cur.joinpath('sources',self.pid,'source.txt').write_bytes(raw)
        packet=self.read(self.cur/'packet.json');p=packet['paragraphs'][0];p['text']=raw.decode();p['locator']['raw_excerpt_sha256']=M.sha(raw)
        ms=self.read(self.cur/'sources/manifest.json');ms[0]['sha256']=M.sha(raw);ms[0]['upstream_locator']=copy.deepcopy(p['locator']);self.write(self.cur/'packet.json',packet);self.write(self.cur/'sources/manifest.json',ms)
        with self.assertRaisesRegex(ValueError,'locator|bytes differ'):M.prepare(self.root,self.cur)
    def test_source_version_mismatch_rejected(self):
        packet=self.read(self.cur/'packet.json');packet['paragraphs'][0]['source_version']='other-version';self.write(self.cur/'packet.json',packet)
        with self.assertRaisesRegex(ValueError,'source version'):M.prepare(self.root,self.cur)
    def test_source_hash_or_locator_change_rejected(self):
        for field,value in [('source_sha256','f'*64),('char_start',101)]:
            packet=self.read(self.cur/'packet.json');p=packet['paragraphs'][0];p['locator'][field]=value
            if field=='char_start':p['locator']['char_end']=101+len(self.text)
            self.write(self.cur/'packet.json',packet);ms=self.read(self.cur/'sources/manifest.json');ms[0]['upstream_locator']=copy.deepcopy(p['locator']);self.write(self.cur/'sources/manifest.json',ms)
            with self.assertRaisesRegex(ValueError,'locator|bytes differ'):M.prepare(self.root,self.cur)
    def test_verified_old_batch_sha_mismatch_is_not_silently_ignored(self):
        proof=self.read(self.old/'publication-mysql.json');proof['batch_sha256']='0'*64;self.write(self.old/'publication-mysql.json',proof)
        with self.assertRaisesRegex(ValueError,'Prior verified batch SHA mismatch'):M.prepare(self.root,self.cur)
    def test_wrong_old_note_requires_source_revision(self):
        batch=self.read(self.old/'content-batch.json');batch['sources'][0]['note']=self.note.replace('卷17','卷18');self.write(self.old/'content-batch.json',batch);self.refresh_receipt()
        ms=self.read(self.old/'sources/manifest.json');ms[0]['reviewed_citation']=batch['sources'][0]['note'];self.write(self.old/'sources/manifest.json',ms)
        with self.assertRaisesRegex(ValueError,'source revision required'):M.prepare(self.root,self.cur)
    def test_wrong_old_chapter_note_is_not_reused_even_if_book_volume_pid_match(self):
        batch=self.read(self.old/'content-batch.json');batch['sources'][0]['note']=self.note.replace('汉兴以来诸侯王年表','樊郦滕灌列传');self.write(self.old/'content-batch.json',batch);self.refresh_receipt()
        ms=self.read(self.old/'sources/manifest.json');ms[0]['reviewed_citation']=batch['sources'][0]['note'];self.write(self.old/'sources/manifest.json',ms)
        with self.assertRaisesRegex(ValueError,'reviewed chapter label.*source revision required'):M.prepare(self.root,self.cur)
    def test_existing_current_publication_receipt_blocks_check_and_apply(self):
        self.write(self.cur/'publication-mysql.json',dict(verified=False))
        with self.assertRaisesRegex(ValueError,'publication receipt'):M.prepare(self.root,self.cur)
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)
    def test_receipt_created_after_preparation_blocks_atomic_write(self):
        plan,before,after=M.prepare(self.root,self.cur);self.write(self.cur/'publication-mysql.json',dict(verified=False))
        with self.assertRaisesRegex(ValueError,'publication receipt'):M.apply_local(self.root,plan,before,after)
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)
    def test_concurrent_current_or_old_manifest_change_blocks_write(self):
        plan,before,after=M.prepare(self.root,self.cur);p=self.old/'sources/manifest.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'Protected source archive changed'):M.apply_local(self.root,plan,before,after)
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)
    def test_different_committed_old_blob_is_rejected_even_with_valid_git_url(self):
        (self.root/self.archive).write_text('156\t孝景二年',encoding='utf-8')
        self.git('add',self.archive);self.git('-c','user.name=Offline Tests','-c','user.email=offline@example.invalid','commit','-qm','different snapshot')
        wrong_commit=self.git('rev-parse','HEAD')
        batch=self.read(self.old/'content-batch.json');batch['sources'][0]['url']=self.source['url'].replace(self.commit,wrong_commit);self.write(self.old/'content-batch.json',batch);self.refresh_receipt()
        ms=self.read(self.old/'sources/manifest.json');ms[0].update(url=batch['sources'][0]['url'],snapshot_commit=wrong_commit);self.write(self.old/'sources/manifest.json',ms)
        with self.assertRaisesRegex(ValueError,'Canonical Git blob differs byte-for-byte'):M.prepare(self.root,self.cur)
    def test_new_sources_are_not_rewritten_when_there_is_no_shared_key(self):
        # A previous verified batch with no matching key provides no restoration candidate.
        batch=self.read(self.old/'content-batch.json');batch['sources'][0]['key']='different-key';self.write(self.old/'content-batch.json',batch);self.refresh_receipt()
        plan,before,after=M.prepare(self.root,self.cur)
        self.assertEqual(plan['changes'],[]);self.assertEqual(after,json.loads(self.current_before))
        self.assertFalse(M.apply_local(self.root,plan,before,after))
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)
    def test_missing_old_git_blob_rejected(self):
        batch=self.read(self.old/'content-batch.json');batch['sources'][0]['url']=self.source['url'].replace(self.commit,'f'*40);self.write(self.old/'content-batch.json',batch);self.refresh_receipt()
        ms=self.read(self.old/'sources/manifest.json');ms[0].update(url=batch['sources'][0]['url'],snapshot_commit='f'*40);self.write(self.old/'sources/manifest.json',ms)
        with self.assertRaisesRegex(ValueError,'not locally available'):M.prepare(self.root,self.cur)

    def copy_published(self,name,at):
        other=self.root/'content/books'/self.book_key/name/'part-01'
        shutil.copytree(self.old,other)
        proof=self.read(other/'publication-mysql.json')
        proof['stages']=[dict(stage='published_source',at=at)]
        self.write(other/'publication-mysql.json',proof)
        return other

    def test_prior_metadata_conflict_rejected_instead_of_choosing_one(self):
        other=self.copy_published('zzz-other','2026-10-21T00:00:00+00:00')
        batch=self.read(other/'content-batch.json');batch['sources'][0]['note']+='·另一版出处'
        self.write(other/'content-batch.json',batch)
        manifest=self.read(other/'sources/manifest.json');manifest[0]['reviewed_citation']=batch['sources'][0]['note']
        self.write(other/'sources/manifest.json',manifest)
        proof=self.read(other/'publication-mysql.json');proof['batch_sha256']=M.sha((other/'content-batch.json').read_bytes())
        self.write(other/'publication-mysql.json',proof)
        with self.assertRaisesRegex(ValueError,'prior batches disagree'):M.prepare(self.root,self.cur)
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)

    def test_published_manifest_url_conflicting_with_batch_is_rejected(self):
        manifest=self.read(self.old/'sources/manifest.json')
        manifest[0]['url']=manifest[0]['url'].replace(self.commit,'b'*40)
        self.write(self.old/'sources/manifest.json',manifest)
        with self.assertRaisesRegex(ValueError,'metadata differs.*published manifest'):M.prepare(self.root,self.cur)

    def test_earliest_published_copy_wins_even_with_later_directory_or_volume(self):
        other=self.copy_published('vol-999/zzz-earliest','2026-10-19T17:00:00-07:00')
        plan,before,after=M.prepare(self.root,self.cur)
        audit=after[0]['canonical_source_reuse']
        self.assertEqual(audit['canonical_batch'],str(other.relative_to(self.root)))
        self.assertEqual(audit['canonical_published_at'],'2026-10-20T00:00:00+00:00')
        # Make the original later so chronological choice cannot use a path tie.
        proof=self.read(self.old/'publication-mysql.json');proof['stages'][0]['at']='2026-10-22T00:00:00+00:00'
        self.write(self.old/'publication-mysql.json',proof)
        self.assertEqual(M.prepare(self.root,self.cur)[2][0]['canonical_source_reuse']['canonical_batch'],str(other.relative_to(self.root)))

    def test_timestamp_required_and_timezone_checked(self):
        for stages in [[],[dict(stage='published_source',at='2026-10-20T01:00:00')]]:
            proof=self.read(self.old/'publication-mysql.json');proof['stages']=stages
            self.write(self.old/'publication-mysql.json',proof)
            with self.assertRaisesRegex(ValueError,'timestamp'):M.prepare(self.root,self.cur)

    def test_wrong_book_in_paragraph_or_old_packet_rejected(self):
        packet=self.read(self.cur/'packet.json');packet['paragraphs'][0]['book_key']='another-book'
        self.write(self.cur/'packet.json',packet)
        with self.assertRaisesRegex(ValueError,'Wrong source book'):M.prepare(self.root,self.cur)
        packet['paragraphs'][0]['book_key']=self.book_key;self.write(self.cur/'packet.json',packet)
        packet=self.read(self.old/'packet.json');packet['book_key']='another-book';self.write(self.old/'packet.json',packet)
        with self.assertRaisesRegex(ValueError,'Prior packet book mismatch'):M.prepare(self.root,self.cur)

    def test_another_books_invalid_matching_receipt_is_not_consulted(self):
        other=self.root/'content/books/unrelated/vol-001/part-01'
        self.write(other/'publication-mysql.json',dict(verified=True,backend='invalid',batch_sha256='0'*64))
        plan,before,after=M.prepare(self.root,self.cur)
        self.assertEqual(len(plan['changes']),1)
        self.assertTrue(all('/unrelated/' not in p for p in plan['scanned_verified_batches']))

    def test_bom_is_hashed_and_preserved_as_a_real_character(self):
        self.tearDown();self.bom='\ufeff';self.setUp()
        plan,before,after=M.prepare(self.root,self.cur)
        self.assertEqual(after[0]['sha256'],M.sha(self.text.encode('utf-8')))
        self.assertNotEqual(after[0]['sha256'],M.sha(self.text.lstrip('\ufeff').encode('utf-8')))
        self.assertTrue(M.apply_local(self.root,plan,before,after))
        self.assertEqual((self.cur/'sources'/self.pid/'source.txt').read_bytes(),self.text.encode('utf-8'))

    def test_legacy_publication_receipt_also_blocks_local_change(self):
        plan,before,after=M.prepare(self.root,self.cur)
        self.write(self.cur/'publication.json',dict(verified=False))
        with self.assertRaisesRegex(ValueError,'publication receipt'):M.apply_local(self.root,plan,before,after)
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)

    def test_default_cli_and_explicit_check_write_nothing(self):
        def hashes():return {str(p.relative_to(self.root)):M.sha(p.read_bytes()) for p in self.root.rglob('*') if p.is_file()}
        old=hashes()
        for flag in [[],['--check']]:
            out=StringIO()
            with redirect_stdout(out):self.assertEqual(M.main([str(self.cur.relative_to(self.root)),'--root',str(self.root),*flag]),0)
            self.assertTrue(json.loads(out.getvalue())['read_only'])
            self.assertEqual(hashes(),old)

    def test_new_same_book_receipt_blocks_prepared_local_write(self):
        plan,before,after=M.prepare(self.root,self.cur)
        self.copy_published('new-publication','2026-10-22T00:00:00+00:00')
        with self.assertRaisesRegex(ValueError,'receipt set changed'):M.apply_local(self.root,plan,before,after)
        self.assertEqual((self.cur/'sources/manifest.json').read_bytes(),self.current_before)

    def test_current_volume_outside_original_group_is_supported(self):
        self.tearDown();self.volume=206;self.setUp()
        plan,before,after=M.prepare(self.root,self.cur)
        self.assertEqual(plan['volume'],206)
        self.assertEqual(plan['book_key'],self.book_key)
        self.assertIn('卷206',after[0]['reviewed_citation'])
        self.assertEqual(len(plan['changes']),1)


class SongshiTests(Tests):
    """Run every provenance/immutability test with another book and author."""
    book_key='songshi'
    book='宋史'


if __name__=='__main__':unittest.main()
