# coding: utf-8
"""Portable workbench regression: synthetic gzip/catalog/TXT, no pilot artifacts.

compile_batch/build/audit and the real structural validator run offline. Git
preparation and publication are outside this test; no database or network client.
"""
from contextlib import ExitStack, redirect_stdout
import copy
import gzip
import hashlib
import importlib.util
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
import uuid

SCRIPTS=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('portable_workbench',SCRIPTS/'history-batch-workbench.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
NS=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
sid=lambda key:str(uuid.uuid5(NS,key))


class Workbench(unittest.TestCase):
    def write(self,path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    def read(self,path):return json.loads(path.read_bytes())
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.batch=self.root/'content/books/synthetic-alpha/vol-001/from-start/part-01'
        self.catalog=self.root/'resources/derived/history-library/catalog.json';self.book_key='synthetic-alpha';self.make_library()
        scripts=self.root/'scripts';scripts.mkdir();shutil.copyfile(SCRIPTS/'validate-content-batch.py',scripts/'validate-content-batch.py')
        self.stack=ExitStack();self.stack.enter_context(patch.object(M,'ROOT',self.root));self.stack.enter_context(patch.object(M,'CATALOG',self.catalog))
        original=M.subprocess.check_output
        self.stack.enter_context(patch.object(M.subprocess,'check_output',side_effect=lambda *a,**k:original(*a,**dict(k,stderr=subprocess.PIPE))))
    def tearDown(self):self.stack.close();self.tmp.cleanup()
    def make_library(self,bom=False):
        texts=[('\ufeff' if bom else '')+'甲授乙为弟子。','乙奉命修城。','下一卷正文。'];full=texts[0]+'\n\n'+texts[1]+'\n'+texts[2]
        source=self.root/'resources/originals/synthetic-alpha.txt';source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(full.encode());whole=M.sha(source.read_bytes())
        starts=[0,len(texts[0])+2,len(texts[0])+2+len(texts[1])+1];ps=[]
        for i,(text,start) in enumerate(zip(texts,starts),1):
            ps.append(dict(id=f'synthetic-alpha-v1-p{i:06d}',book_key='synthetic-alpha',book='合成甲书',source_version='v1',volume_candidate=1 if i<3 else 2,section_id='synthetic-alpha-s1' if i<3 else 'synthetic-alpha-s2',section_title='合成本纪',kind='paragraph',text=text,citation=f'《合成甲书》卷{1 if i<3 else 2}·synthetic-alpha-v1-p{i:06d}',locator=dict(source_file=str(source.relative_to(self.root)),source_sha256=whole,char_start=start,char_end=start+len(text),line_start=i,line_end=i,raw_excerpt_sha256=M.sha(text.encode()))))
        self.ps=ps;derived=self.root/'resources/derived/history-library/synthetic-alpha/paragraphs.jsonl.gz';derived.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(derived,'wt',encoding='utf-8') as f:
            for p in ps:f.write(json.dumps(p,ensure_ascii=False)+'\n')
        sections=self.root/'resources/derived/history-library/synthetic-alpha/sections.json';self.write(sections,[dict(volume_candidate=1,char_start=0,char_end=starts[2]),dict(volume_candidate=2,char_start=starts[2],char_end=len(full))])
        self.book=dict(book_key='synthetic-alpha',book='合成甲书',source_version='v1',paragraph_file=str(derived.relative_to(self.root)),sections_file=str(sections.relative_to(self.root)),sections_sha256=M.sha(sections.read_bytes()))
        self.write(self.catalog,dict(books=[self.book]));self.write(self.batch/'packet.json',dict(book_key='synthetic-alpha',book='合成甲书',volume=1,source_version='v1',paragraphs=ps[:2],next_paragraph=ps[2]['id']))
        self.write(self.batch/'sources/manifest.json',[self.export(p) for p in ps[:2]])
        a=dict(key='person_synthetic_a',name='合成甲',aliases=[],era='合成旧世',birth_year=None,death_year=None,description='合成甲教授乙。',biography=None)
        b=dict(key='person_synthetic_b',name='合成乙',aliases=[],era='合成旧世',birth_year=None,death_year=None,description='合成乙从甲学习，奉命修城。',biography=None)
        event=dict(key='event_synthetic_wall',title='合成乙修城',description='公元100年，合成乙奉命修城。',start_year=100,end_year=100,dynasty='合成时代',time_original='合成元年',time_precision='exact',location_precision='unknown',location_lat=None,location_lng=None)
        pe=dict(key='pe_synthetic_b_wall',person_key=b['key'],event_key=event['key'],role='奉命修城')
        rel=dict(key='rel_synthetic_a_b',person_a_key=a['key'],person_b_key=b['key'],relation_type='teacher_of',description='甲教授乙，乙为甲的弟子。')
        def item(group,row,p,field):return dict(group=group,row=row,evidence=[dict(paragraph_id=p['id'],quote=p['text'].lstrip('\ufeff'),field=field,text=row[field],note='合成fixture人工已核主语和关系方向',time_context='合成元年对应公元100年；非自动推年')])
        self.write(self.batch/'curation.json',dict(batch_key='portable-v001-p01',claim_namespace='portable-v001-p01',reused_keys=[],items=[item('people',a,ps[0],'description'),item('people',b,ps[0],'description'),item('events',event,ps[1],'description'),item('person_events',pe,ps[1],'role'),item('person_relationships',rel,ps[0],'description')],paragraph_reviews=[dict(paragraph_id=p['id'],status='reviewed',note='完整阅读本段',observations=['未据同场出现补建关系'],relationship_audit=[dict(quote=ps[0]['text'].lstrip('\ufeff'),person_a_key=a['key'],person_b_key=b['key'],relationship_key=rel['key'],decision='new',reason='原文明示授业')]) for p in ps[:2]]))
    def export(self,p):
        d=self.batch/'sources'/p['id'];d.mkdir(parents=True,exist_ok=True);(d/'source.txt').write_bytes(p['text'].encode());self.write(d/'paragraph.json',p)
        return dict(key=p['book_key']+'-'+p['id'],paragraph_id=p['id'],file=p['id']+'/source.txt',sha256=p['locator']['raw_excerpt_sha256'],upstream_locator=p['locator'],url='https://github.com/greed-216/histree/blob/'+'a'*40+'/content/source/'+p['id']+'/source.txt',reviewed_citation=f'《{p["book"]}》卷{p["volume_candidate"]}·合成本纪·'+p['id'],citation_review_note='逐字和篇名已核',source_title=f'{p["book"]}·卷{p["volume_candidate"]}·合成本纪·'+p['id'])
    def curation(self,fn):
        p=self.batch/'curation.json';value=self.read(p);fn(value);self.write(p,value)
    def packet(self,fn):
        p=self.batch/'packet.json';value=self.read(p);fn(value);self.write(p,value)
    def compile(self):return M.compile_batch(self.batch)
    def build(self):
        with redirect_stdout(StringIO()):M.build(types.SimpleNamespace(directory=self.batch))
    def prior(self,row=None):
        row=copy.deepcopy(row or self.read(self.batch/'curation.json')['items'][0]['row']);row['status']='published'
        path=self.root/'content/books/synthetic-alpha/vol-000/old/content-batch.json';self.write(path,dict(people=[row]));return path,row
    def revision(self,name,before,after,key='person_synthetic_a',verified=True):
        path=self.root/'content/revisions'/name/'plan.json';self.write(path,dict(kind='guarded_person_era_revision',updates=[dict(table='person',key=key,id=sid(key),before=before,after=after)]))
        self.write(path.parent/'publication-mysql.json',dict(verified=verified,anonymous_readback_verified=verified,plan_sha256=M.sha(path.read_bytes())));return path
    def test_complete_build_and_claim_namespace_are_portable(self):
        self.build();batch=self.read(self.batch/'content-batch.json');self.assertEqual(len(batch['people']),2);self.assertEqual(len(batch['claims']),5)
        self.assertTrue(all(c['key'].startswith('claim_portable-v001-p01_') for c in batch['claims']))
        self.assertEqual(self.read(self.batch/'coverage.json')['next_paragraph'],self.ps[2]['id']);self.assertTrue(self.read(self.batch/'workbench-validation.json')['continuous_range_checked'])
        ledger=self.read(self.batch/'paragraphs.json');self.assertEqual(ledger[0]['relationship_audit'][0]['decision'],'new');self.assertIn('逐字底本快照',(self.batch/'review.html').read_text())
    def new_person_revision(self):
        row=copy.deepcopy(self.read(self.batch/'curation.json')['items'][0]['row']);row.update(key='person_revision_new',id=sid('person_revision_new'),name='合成新增人物',status='published',aliases=[])
        path=self.root/'content/revisions/verified-new-person/plan.json';self.write(path,dict(kind='reviewed_history_correction',new_people=[row],updates=[]))
        receipt=path.parent/'publication-mysql.json';self.write(receipt,dict(verified=True,anonymous_readback_verified=True,plan_sha256=M.sha(path.read_bytes()),new_people=[row]))
        return path,receipt,row
    def test_new_people_in_verified_correction_are_reusable(self):
        path,receipt,row=self.new_person_revision();registry={x['row']['key']:x for x in M.people_registry(exclude=self.batch)}
        self.assertEqual(registry[row['key']]['row']['name'],row['name'])
        receipt.write_text('{}');self.assertNotIn(row['key'],{x['row']['key'] for x in M.people_registry(exclude=self.batch)})
    def test_new_revision_person_requires_matching_receipt_and_stable_uuid(self):
        path,receipt,row=self.new_person_revision();audit=self.read(receipt);audit['new_people'][0]['name']='被篡改';self.write(receipt,audit)
        with self.assertRaisesRegex(AssertionError,'differs'):M.people_registry(exclude=self.batch)
        value=self.read(path);value['new_people'][0]['id']=sid('wrong');self.write(path,value);audit.update(new_people=value['new_people'],plan_sha256=M.sha(path.read_bytes()));self.write(receipt,audit)
        with self.assertRaisesRegex(AssertionError,'UUID'):M.people_registry(exclude=self.batch)
    def test_noncontinuous_or_reordered_range_rejected(self):
        for paragraphs in [[self.ps[0],self.ps[2]],[self.ps[1],self.ps[0]]]:
            self.packet(lambda p:p.update(paragraphs=paragraphs))
            with self.assertRaisesRegex(AssertionError,'Non-continuous'):self.compile()
    def test_next_pointer_and_source_version_rejected(self):
        self.packet(lambda p:p.update(next_paragraph='wrong'))
        with self.assertRaisesRegex(AssertionError,'next paragraph'):self.compile()
        self.packet(lambda p:p.update(next_paragraph=self.ps[2]['id'],source_version='changed'))
        with self.assertRaisesRegex(AssertionError,'Source version'):self.compile()
    def test_packet_original_text_mutation_rejected(self):
        self.packet(lambda p:p['paragraphs'][0].update(text='改变后的原文'))
        with self.assertRaisesRegex(AssertionError,'Packet differs'):self.compile()
    def test_wrong_packet_volume_must_not_be_accepted(self):
        self.packet(lambda p:p.update(volume=2))
        with self.assertRaises(AssertionError):self.compile()
    def test_snapshot_byte_change_and_nonverbatim_quote_rejected(self):
        path=self.batch/'sources'/self.ps[0]['id']/'source.txt';raw=path.read_bytes();path.write_bytes(raw+b'!')
        with self.assertRaises(AssertionError):self.compile()
        path.write_bytes(raw);self.curation(lambda c:c['items'][0]['evidence'][0].update(quote='原书没有这句话'))
        with self.assertRaisesRegex(AssertionError,'Quote mismatch'):self.compile()
    def test_bom_is_retained_as_raw_bytes(self):
        self.make_library(bom=True);batch,*_=self.compile();self.assertEqual(len(batch['claims']),5)
        raw=(self.batch/'sources'/self.ps[0]['id']/'source.txt').read_bytes();self.assertTrue(raw.startswith(b'\xef\xbb\xbf'));self.assertEqual(M.sha(raw),self.ps[0]['locator']['raw_excerpt_sha256'])
    def test_every_paragraph_needs_ordered_completed_review(self):
        c=self.read(self.batch/'curation.json');original=copy.deepcopy(c)
        for reviews in [c['paragraph_reviews'][::-1],c['paragraph_reviews'][:1],[dict(r,status='pending') for r in c['paragraph_reviews']]]:
            self.write(self.batch/'curation.json',dict(original,paragraph_reviews=reviews))
            with self.assertRaises(AssertionError):self.compile()
    def test_empty_fact_paragraph_requires_explicit_observation(self):
        self.curation(lambda c:c.update(items=[],paragraph_reviews=[dict(r,observations=[]) for r in c['paragraph_reviews']]))
        with self.assertRaisesRegex(AssertionError,'No facts'):self.compile()
        self.curation(lambda c:c.update(paragraph_reviews=[dict(r,observations=['论说，无可确定的新事件']) for r in c['paragraph_reviews']]))
        batch,coverage,ledger,*_=self.compile();self.assertEqual(batch['events'],[]);self.assertTrue(all(not r['claim_keys'] for r in ledger))
    def test_orphan_relationship_and_participation_rejected_before_output_replacement(self):
        old=b'{"keep":"previous generated output"}\n';(self.batch/'content-batch.json').write_bytes(old);cur=self.read(self.batch/'curation.json')
        for group,field in [('person_relationships','person_b_key'),('person_events','event_key')]:
            changed=copy.deepcopy(cur);next(i for i in changed['items'] if i['group']==group)['row'][field]='missing-reference';self.write(self.batch/'curation.json',changed)
            with self.assertRaises(subprocess.CalledProcessError):self.build()
            self.assertEqual((self.batch/'content-batch.json').read_bytes(),old)
    def test_no_missing_evidence_note_or_invalid_field(self):
        cur=self.read(self.batch/'curation.json')
        for delta in [dict(note=''),dict(field='not-a-row-field')]:
            changed=copy.deepcopy(cur);changed['items'][0]['evidence'][0].update(delta);self.write(self.batch/'curation.json',changed)
            with self.assertRaises(AssertionError):self.compile()
    def test_started_publications_cannot_compile_build_or_relink(self):
        for name in ['publication.json','publication-mysql.json']:
            path=self.batch/name;self.write(path,dict(verified=False))
            with self.assertRaisesRegex(AssertionError,'immutable'):self.compile()
            with self.assertRaisesRegex(AssertionError,'immutable'):self.build()
            with patch.object(M.subprocess,'check_output') as call:
                with self.assertRaisesRegex(AssertionError,'immutable'):M.link_sources(types.SimpleNamespace(directory=self.batch,commit='a'*40,archive_prefix='content/archive'))
                call.assert_not_called()
            path.unlink()
    def test_homonym_requires_explicit_identity_decision(self):
        row=copy.deepcopy(self.read(self.batch/'curation.json')['items'][0]['row']);row['key']='person_other_identity';self.prior(row)
        with self.assertRaisesRegex(AssertionError,'Identity decision'):self.compile()
        self.curation(lambda c:c['items'][0].update(identity_note='合成同名，时代和父子链不同，明确分开'))
        self.assertEqual(len(self.compile()[0]['people']),2)
    def test_reused_person_profile_is_immutable_and_gets_independent_claim(self):
        prior,row=self.prior();digest=M.sha(prior.read_bytes());self.curation(lambda c:c.update(reused_keys=[row['key']]))
        batch,coverage,ledger,reused,*_=self.compile();self.assertEqual(reused,[row['key']]);self.assertTrue(any(c['subject_key']==row['key'] for c in batch['claims']))
        self.curation(lambda c:c['items'][0]['row'].update(era='擅自改变时代'))
        with self.assertRaisesRegex(AssertionError,'Existing person changed'):self.compile()
        self.assertEqual(M.sha(prior.read_bytes()),digest)
    def test_hash_bound_verified_field_revision_reused_without_rewriting_prior(self):
        prior,row=self.prior();digest=M.sha(prior.read_bytes());self.revision('era-change',dict(era='合成旧世'),dict(era='合成新世'))
        self.curation(lambda c:(c.update(reused_keys=[row['key']]),c['items'][0]['row'].update(era='合成新世')))
        self.assertEqual(self.compile()[0]['people'][0]['era'],'合成新世');self.assertEqual(M.sha(prior.read_bytes()),digest)
    def test_unverified_or_hash_mismatched_revision_cannot_supply_profile(self):
        self.prior();path=self.revision('unverified',dict(era='合成旧世'),dict(era='合成新世'),verified=False)
        self.curation(lambda c:(c.update(reused_keys=['person_synthetic_a']),c['items'][0]['row'].update(era='合成新世')))
        with self.assertRaisesRegex(AssertionError,'Existing person changed'):self.compile()
        proof=self.read(path.parent/'publication-mysql.json');proof.update(verified=True,anonymous_readback_verified=True,plan_sha256='0'*64);self.write(path.parent/'publication-mysql.json',proof)
        with self.assertRaisesRegex(AssertionError,'Existing person changed'):self.compile()
    def test_verified_revisions_follow_value_chain_not_directory_order(self):
        self.prior();self.revision('zzz-first',dict(era='合成旧世'),dict(era='合成中世'));self.revision('aaa-second',dict(era='合成中世'),dict(era='合成新世'))
        self.curation(lambda c:(c.update(reused_keys=['person_synthetic_a']),c['items'][0]['row'].update(era='合成新世')))
        self.assertEqual(self.compile()[0]['people'][0]['era'],'合成新世')
    def test_revision_branch_and_cycle_are_rejected(self):
        self.prior();self.revision('first',dict(era='合成旧世'),dict(era='合成中世'));second=self.revision('branch',dict(era='合成旧世'),dict(era='合成新世'))
        with self.assertRaisesRegex(AssertionError,'ambiguous|discontinuous'):M.people_registry(self.batch)
        shutil.rmtree(second.parent);self.revision('cycle',dict(era='合成中世'),dict(era='合成旧世'))
        with self.assertRaisesRegex(AssertionError,'ambiguous|discontinuous'):M.people_registry(self.batch)
    def test_legacy_hash_bound_monotonic_alias_append_is_reusable(self):
        prior,row=self.prior();path=self.root/'content/revisions/legacy-aliases/aliases.json'
        self.write(path,dict(people=[dict(id=sid(row['key']),key=row['key'],name=row['name'],before=['甲字'],after=['甲字','甲号'],claim_ids=['evidence-claim'])]))
        self.write(path.parent/'publication.json',dict(verified=True,revision_sha256=M.sha(path.read_bytes()),method='Guarded alias merge; published claim checks; anonymous readback',count=1))
        self.curation(lambda c:(c.update(reused_keys=[row['key']]),c['items'][0]['row'].update(aliases=['甲字','甲号'])))
        self.assertEqual(self.compile()[0]['people'][0]['aliases'],['甲字','甲号'])
    def test_seed_identity_snapshot_requires_hash_bound_published_rows(self):
        row=self.read(self.batch/'curation.json')['items'][0]['row'];snap=self.root/'content/fixtures/identity-snapshot.json';self.write(snap,dict(person=[dict(row,id=sid(row['key']),status='published')]))
        baseline=dict(kind='mysql_seed_person_reuse',snapshot=str(snap.relative_to(self.root)),snapshot_sha256=M.sha(snap.read_bytes()),people=[row]);self.write(self.batch/'identity-baseline.json',baseline)
        self.curation(lambda c:c.update(reused_keys=[row['key']]))
        self.assertEqual(self.compile()[3],[row['key']]);snap.write_bytes(snap.read_bytes()+b' ')
        with self.assertRaisesRegex(AssertionError,'snapshot changed'):self.compile()
    def add_other_book_supplement(self):
        p=copy.deepcopy(self.ps[0]);p.update(id='synthetic-beta-v2-p000001',book_key='synthetic-beta',book='合成乙书',source_version='v2',section_id='synthetic-beta-s1',text='乙书记甲授乙为弟子。')
        p['locator']=dict(p['locator'],raw_excerpt_sha256=M.sha(p['text'].encode()),char_start=0,char_end=len(p['text']))
        rel='resources/derived/history-library/synthetic-beta/paragraphs.jsonl.gz';path=self.root/rel;path.parent.mkdir(parents=True)
        with gzip.open(path,'wt',encoding='utf-8') as f:f.write(json.dumps(p,ensure_ascii=False)+'\n')
        catalog=self.read(self.catalog);catalog['books'].append(dict(book_key=p['book_key'],book=p['book'],source_version='v2',paragraph_file=rel));self.write(self.catalog,catalog)
        self.packet(lambda q:q.update(supplementary_paragraphs=[p]));manifest=self.read(self.batch/'sources/manifest.json');manifest.append(self.export(p));self.write(self.batch/'sources/manifest.json',manifest)
        def add(c):c['items'][0]['evidence'].append(dict(paragraph_id=p['id'],primary_paragraph_id=self.ps[0]['id'],relation='corroborates',quote=p['text'],field='description',text='合成乙书独立补证授业',note='独立来源同人补证',time_context='不推进乙书工作线'))
        self.curation(add);return p
    def test_other_book_supplement_keeps_primary_cursor_and_other_progress(self):
        other=self.root/'content/books/synthetic-beta/progress.json';self.write(other,dict(book_key='synthetic-beta',active_cursor=dict(volume=9,next_paragraph='untouched')));before=other.read_bytes()
        p=self.add_other_book_supplement();batch,coverage,*_=self.compile()
        self.build()
        self.assertEqual(coverage['next_paragraph'],self.ps[2]['id']);self.assertEqual(coverage['supplements'][0]['source_book'],'synthetic-beta');self.assertEqual(other.read_bytes(),before)
    def test_supplement_requires_primary_evidence_anchor_and_library_identity(self):
        p=self.add_other_book_supplement();self.curation(lambda c:c['items'][0]['evidence'][1].update(primary_paragraph_id='wrong'))
        with self.assertRaisesRegex(AssertionError,'primary paragraph anchor'):self.compile()
        self.curation(lambda c:c['items'][0]['evidence'][1].update(primary_paragraph_id=self.ps[0]['id']))
        self.packet(lambda q:q['supplementary_paragraphs'][0].update(text='篡改补证原文'))
        with self.assertRaisesRegex(AssertionError,'Supplement differs'):self.compile()
    def test_whitespace_gap_and_shared_txt_volume_bounds_are_audited(self):
        self.build()
        with redirect_stdout(StringIO()):M.audit(types.SimpleNamespace(directory=self.batch.parent))
        report=self.read(self.batch.parent/'volume-audit.json');self.assertTrue(report['full_volume_source_coverage']);self.assertEqual(len(report['source_whitespace_gaps']),1);self.assertEqual(report['source_whitespace_gaps'][0]['text'],'\n\n')
    def test_nonwhitespace_body_gap_and_overlapping_intervals_are_rejected(self):
        ps=copy.deepcopy(self.ps[:2]);source='甲授乙为弟子。正文乙奉命修城。'.encode()
        ps[1]['locator'].update(char_start=len(ps[0]['text'])+2,char_end=len(ps[0]['text'])+2+len(ps[1]['text']))
        with self.assertRaisesRegex(AssertionError,'gap contains body'):M.assemble_source_interval(ps,[p['text'].encode() for p in ps],source)
        ps[1]['locator'].update(char_start=0,char_end=len(ps[1]['text']))
        with self.assertRaisesRegex(AssertionError,'overlap'):M.assemble_source_interval(ps,[p['text'].encode() for p in ps],source)


if __name__=='__main__':unittest.main()
