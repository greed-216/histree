# coding: utf-8
"""Offline fixtures only: no credentials, sockets, actual DB, or --apply invocation."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import types
from unittest import mock
import contextlib
import io
import uuid

SPEC=importlib.util.spec_from_file_location('sidecars',Path(__file__).with_name('history_sidecars.py'))
S=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(S)
U=lambda name:str(uuid.uuid5(uuid.NAMESPACE_URL,'offline-sidecar/'+name))


class PlainDatabase:
    def __init__(self,rows,writable=False):
        self.rows=copy.deepcopy(rows);self.writable=writable;self.target_fingerprint='target';self.connection=self
        self.operations=[];self.snapshot=None
    def schema(self):pass
    def get(self,table,identity,lock=False):
        if lock and not self.writable:raise ValueError('read-only lock')
        rows=[r for r in self.rows.get(table,[]) if all(r.get(k)==v for k,v in identity.items())]
        S.require(len(rows)<=1,'duplicate fixture identity')
        return copy.deepcopy(rows[0]) if rows else None
    def assert_publish_lock(self):S.require(self.writable,'missing lock')
    def begin(self):self.snapshot=copy.deepcopy(self.rows);self.operations.append('begin')
    def commit(self):self.operations.append('commit')
    def rollback(self):
        if self.snapshot is not None:self.rows=self.snapshot
        self.operations.append('rollback')
    def insert(self,table,row):
        S.require(self.writable and table in S.FIELDS and set(row)==set(S.FIELDS[table]),'forbidden insertion')
        self.rows.setdefault(table,[]).append(copy.deepcopy(row));self.operations.append(('insert',table))


class FakeDatabase(S.Database):
    def __init__(self,rows,writable=False):
        self.rows=copy.deepcopy(rows);self.writable=writable;self.target_fingerprint='target';self.connection=self
        cols={t:set().union(*(set(r) for r in rs)) for t,rs in self.rows.items()}
        cols.update({t:set(fields) for t,fields in S.FIELDS.items()})
        self.store=types.SimpleNamespace(columns=cols)
        self._phase=None;self.bulk_statistics=dict(select_batches=0,insert_batches=0,rows_requested=0)
        self.select_calls=[];self.insert_calls=[];self.operations=[];self.saved=None;self.after_insert=None;self.duplicate_return=False
    def schema(self):pass
    def close(self):pass
    def _select_many(self,table,identities,lock):
        self.select_calls.append((table,copy.deepcopy(identities),lock));self.bulk_statistics['select_batches']+=1
        rows=[copy.deepcopy(r) for r in self.rows.get(table,[]) if any(all(r.get(k)==v for k,v in ident.items()) for ident in identities)]
        if self.duplicate_return and rows:rows.append(copy.deepcopy(rows[0]))
        return rows
    def get(self,table,identity,lock=False):
        if self._phase is not None:return super().get(table,identity,lock)
        rows=[r for r in self.rows.get(table,[]) if all(r.get(k)==v for k,v in identity.items())]
        S.require(len(rows)<=1,'nonunique fake identity');return copy.deepcopy(rows[0]) if rows else None
    def assert_publish_lock(self):S.require(self.writable,'global lock missing')
    def begin(self):self.saved=copy.deepcopy(self.rows);self.operations.append('begin')
    def commit(self):self.operations.append('commit')
    def rollback(self):
        if self.saved is not None:self.rows=self.saved
        self.operations.append('rollback')
    def _insert_many(self,table,rows):
        self.insert_calls.append((table,copy.deepcopy(rows)));self.bulk_statistics['insert_batches']+=1
        for row in rows:
            ident={k:row[k] for k in S.IDENTITY[table]}
            S.require(not any(all(r.get(k)==v for k,v in ident.items()) for r in self.rows.get(table,[])),'fake duplicate key')
            self.rows.setdefault(table,[]).append(copy.deepcopy(row))
        if self.after_insert:self.after_insert(self,table)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.book_key=getattr(self,'book_key','test-history');self.volume=getattr(self,'volume',31)
        self.b=self.root/'content/books'/self.book_key/f'vol-{self.volume:03}'/'from-start/part-01';self.b.mkdir(parents=True)
        self.rows={};ids={};sources=[];claims=[];paras=[];manifest=[]
        def put(table,row):self.rows.setdefault(table,[]).append(row)
        def write(name,obj):
            path=self.b/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(S.dump(obj))
        for n,text in [(1,'甲年，甲事。'),(2,'乙年，乙事。'),(3,'丙年，丙事。')]:
            pid=f'{self.book_key}-version-p{n:06}';sk='source'+str(n);sid=U(sk);ids[sk]=sid
            url='https://github.com/greed-216/histree/blob/'+'a'*40+'/content/source'+str(n)+'.txt'
            raw=text.encode('utf-8');sh=S.sha(raw);section=self.book_key+'-version-section';asset='b'*64
            para=dict(id=pid,book_key=self.book_key,source_version='version',section_id=section,text=text,
                      locator=dict(char_start=n*100,char_end=n*100+len(text),source_file='resources/source.txt',source_sha256='d'*64,raw_excerpt_sha256=sh))
            paras.append(para);m=dict(paragraph_id=pid,key=sk,file=pid+'/source.txt',sha256=sh,url=url,upstream_locator=copy.deepcopy(para['locator']));manifest.append(m)
            path=self.b/'sources'/m['file'];path.parent.mkdir(parents=True);path.write_bytes(raw)
            source=dict(key=sk,title='离线测试书',url=url,source_type='primary');sources.append(source)
            put('source',dict(id=sid,**{k:v for k,v in source.items() if k!='key'}))
            put('source_text',dict(source_id=sid,archive_url_sha256=S.sha(url.encode()),archive_url=url,content=text,content_sha256=sh,archive_blob_sha256=sh,archive_commit='a'*40))
            put('library_paragraph',dict(id=pid,book_key=self.book_key,section_id=section,content=text,content_sha256=sh,asset_id=asset,char_start=n*100,char_end=n*100+len(text)))
        put('library_asset',dict(id='b'*64,source_file='resources/source.txt',source_sha256='d'*64,raw_excerpt_sha256=sh))
        put('library_book',dict(book_key=self.book_key,source_version='version',status='available'))
        events=[];items=[]
        for ek,ns,rev in [
            ('event_many',[1,2],dict(decision='inherited',reason='各段独立',anchor_note='原表年界',source_dating_assertions=[dict(paragraph_id=paras[0]['id'],year=-209,basis='甲年对照'),dict(paragraph_id=paras[1]['id'],year=-208,basis='乙年对照')])),
            ('event_exact',[3],dict(decision='exact',year=-180,reason='丙年对照',anchor_note='明确纪年')),
            ('event_inherited_no_year',[3],dict(decision='inherited',comparison='consistent',reason='旧日期前180年，仅复用',anchor_note='未独立核年'))]:
            ids[ek]=U(ek);row=dict(key=ek,title=ek,description='事件',start_year=-180,end_year=-180,time_original='原纪年',dynasty='汉',status='draft')
            events.append(row);put('event',dict(id=ids[ek],**{k:v for k,v in row.items() if k not in ('key','status')},status='published'))
            evs=[]
            for n in ns:
                pid=paras[n-1]['id'];ck=ek+'_claim'+str(n);ids[ck]=U(ck);quote=paras[n-1]['text'];claim=dict(key=ck,subject_table='event',subject_key=ek,field_path='description',claim_text=ek+'白话',source_key='source'+str(n),citation=pid,note='原文：'+quote+'；核对说明：逐字已核',status='draft')
                claims.append(claim);put('fact_claim',S.normalized_claim(claim,ids));evs.append(dict(paragraph_id=pid,quote=quote,field='description',text=claim['claim_text']))
            items.append(dict(group='events',row={k:v for k,v in row.items() if k!='status'},evidence=evs,temporal_review=rev))
        batch=dict(batch_key='fixture',people=[],events=events,person_events=[],person_relationships=[],sources=sources,claims=claims,topics=[])
        write('content-batch.json',batch);write('curation.json',dict(batch_key='fixture',claim_namespace='fixture',items=items,paragraph_reviews=[dict(paragraph_id=p['id'],status='reviewed') for p in paras]))
        write('packet.json',dict(book_key=self.book_key,volume=self.volume,paragraphs=paras,source_version='version'))
        write('sources/manifest.json',manifest);write('sql/key-map.json',ids)
        write('publication-mysql.json',dict(backend='mysql',verified=True,target_fingerprint='target',batch_sha256=S.sha((self.b/'content-batch.json').read_bytes())))
        write('time-review.json',dict(batch_sha256=S.sha((self.b/'content-batch.json').read_bytes()),events=[dict(key=it['row']['key'],**it['temporal_review']) for it in items]))
        self.bundle=S.load_bundle(self.root,self.b);self.db=FakeDatabase(self.rows);self.plan=S.prepare(self.bundle,self.db)
    def tearDown(self):self.tmp.cleanup()
    def test_source_only_evidence_links_all_sources_without_fact_inserts(self):
        batch=json.loads((self.b/'content-batch.json').read_bytes())
        for field in ('people','events','person_events','person_relationships','claims','topics'):batch[field]=[]
        (self.b/'content-batch.json').write_bytes(S.dump(batch))
        cur=json.loads((self.b/'curation.json').read_bytes());cur['items']=[];(self.b/'curation.json').write_bytes(S.dump(cur))
        proof=json.loads((self.b/'publication-mysql.json').read_bytes());proof.update(source_only_evidence=True,batch_sha256=S.sha((self.b/'content-batch.json').read_bytes()));(self.b/'publication-mysql.json').write_bytes(S.dump(proof))
        (self.b/'time-review.json').write_bytes(S.dump(dict(batch_sha256=proof['batch_sha256'],events=[])))
        result=S.prepare(S.load_bundle(self.root,self.b),FakeDatabase(self.rows))
        self.assertEqual(len(result['inserts']['library_source_link']),3)
        self.assertEqual(result['inserts']['claim_structure'],[]);self.assertEqual(result['inserts']['event_dating'],[])
    def test_source_only_receipt_rejects_a_batch_containing_facts(self):
        proof=json.loads((self.b/'publication-mysql.json').read_bytes());proof['source_only_evidence']=True;(self.b/'publication-mysql.json').write_bytes(S.dump(proof))
        with self.assertRaisesRegex(ValueError,'cannot contain fact'):S.load_bundle(self.root,self.b)
    def test_accumulates_each_source_year_without_last_call_overwrite(self):
        ds=self.plan['inserts']['event_dating'];self.assertEqual(sorted(d['earliest_year'] for d in ds),[-209,-208,-180])
        many=[d for d in ds if d['event_id']==U('event_many')];self.assertEqual(len({d['claim_id'] for d in many}),2)
        self.assertEqual(len(self.plan['skipped_independent_dates']),1)
        self.assertNotIn('insert',str(self.db.operations))
    def test_prose_and_canonical_date_do_not_create_authored_year(self):
        item=self.bundle['cur']['items'][2];a,reason=S.authored_assertions(item,self.bundle['manifest'])
        self.assertEqual(a,[]);self.assertIn('canonical date',reason)
    def test_exact_range_relative_era_preserved_and_invalid_year_rejected(self):
        self.assertEqual(S.dating_shape('range',dict(start_year=-200,end_year=-190))['precision_kind'],'range')
        self.assertEqual(S.dating_shape('relative',{})['earliest_year'],None)
        self.assertEqual(S.dating_shape('era',{},'汉')['era_key'],'汉')
        for value in [0,True,'-180']:
            with self.assertRaises(ValueError):S.dating_shape('exact',dict(year=value))
        with self.assertRaises(ValueError):S.dating_shape('range',dict(start_year=-180,end_year=-190))
    def add_normalized_heading_fixture(self,used=False,flags=None):
        pid=self.book_key+'-version-p000004';sk='source4';sid=U(sk);raw='结构 标题'.encode();text='结构标题'
        loc=dict(char_start=900,char_end=900+len(raw.decode()),source_file='resources/source.txt',source_sha256='d'*64,raw_excerpt_sha256=S.sha(raw))
        packet=json.loads((self.b/'packet.json').read_bytes());packet['paragraphs'].append(dict(id=pid,book_key=self.book_key,source_version='version',section_id=self.book_key+'-version-section',text=text,kind='heading',flags=['not_historical_body'] if flags is None else flags,locator=loc))
        url='https://github.com/greed-216/histree/blob/'+'a'*40+'/content/source4.txt'
        batch=json.loads((self.b/'content-batch.json').read_bytes());batch['sources'].append(dict(key=sk,title='结构标题',url=url,source_type='primary'))
        ids=json.loads((self.b/'sql/key-map.json').read_bytes());ids[sk]=sid
        manifest=json.loads((self.b/'sources/manifest.json').read_bytes());manifest.append(dict(paragraph_id=pid,key=sk,file=pid+'/source.txt',sha256=S.sha(raw),url=url,upstream_locator=copy.deepcopy(loc)))
        (self.b/'sources'/pid).mkdir();(self.b/'sources'/pid/'source.txt').write_bytes(raw)
        if used:
            ck='heading_claim';ids[ck]=U(ck);batch['claims'].append(dict(key=ck,subject_table='event',subject_key='event_exact',field_path='description',claim_text='标题引用',source_key=sk,citation=pid,note='原文：'+raw.decode()+'；核对说明：标题',status='draft'))
        for name,obj in [('packet.json',packet),('content-batch.json',batch),('sql/key-map.json',ids),('sources/manifest.json',manifest)]:
            (self.b/name).write_bytes(S.dump(obj))
        digest=S.sha((self.b/'content-batch.json').read_bytes())
        for name in ['publication-mysql.json','time-review.json']:
            obj=json.loads((self.b/name).read_bytes());obj['batch_sha256']=digest;(self.b/name).write_bytes(S.dump(obj))
        return pid,sid
    def test_unused_normalized_structural_heading_loads_without_any_sidecar(self):
        pid,sid=self.add_normalized_heading_fixture()
        bundle=S.load_bundle(self.root,self.b);plan=S.prepare(bundle,self.db);S.guard_plan(plan,self.root,self.db)
        self.assertIn(pid,bundle['excluded_structural_headings'])
        self.assertNotIn(sid,{r['source_id'] for r in plan['inserts']['library_source_link']})
        self.assertEqual(len(plan['inserts']['claim_structure']),len(self.plan['inserts']['claim_structure']))
        self.assertEqual([{k:v for k,v in r.items() if k!='id'} for r in plan['inserts']['event_dating']],[{k:v for k,v in r.items() if k!='id'} for r in self.plan['inserts']['event_dating']])
    def test_claimed_normalized_heading_internal_space_difference_is_rejected(self):
        self.add_normalized_heading_fixture(used=True)
        with self.assertRaisesRegex(ValueError,'snapshot text differ'):S.load_bundle(self.root,self.b)
    def test_unflagged_heading_gets_no_structural_normalization_exception(self):
        self.add_normalized_heading_fixture(flags=[])
        with self.assertRaisesRegex(ValueError,'snapshot text differ'):S.load_bundle(self.root,self.b)
    def test_only_extra_structural_edge_whitespace_is_allowed(self):
        self.assertTrue(S.exact_text_with_structural_edges('\n\t甲年，甲事。 \n','甲年，甲事。'))
        self.assertTrue(S.exact_text_with_structural_edges('甲年，甲事。','甲年，甲事。'))
        self.assertFalse(S.exact_text_with_structural_edges('甲年， 甲事。','甲年，甲事。'))
        self.assertFalse(S.exact_text_with_structural_edges('甲年，乙事。','甲年，甲事。'))
        self.assertFalse(S.exact_text_with_structural_edges('甲年，甲事。正文','甲年，甲事。'))
    def rewrite_first_raw_fixture(self,text):
        packet=json.loads((self.b/'packet.json').read_bytes());para=packet['paragraphs'][0];pid=para['id']
        manifest=json.loads((self.b/'sources/manifest.json').read_bytes());m=next(x for x in manifest if x['paragraph_id']==pid)
        raw=text.encode('utf-8');m['sha256']=S.sha(raw);(self.b/'sources'/m['file']).write_bytes(raw)
        para['locator']['char_end']=para['locator']['char_start']+len(text)
        para['locator']['raw_excerpt_sha256']=S.sha(raw);m['upstream_locator']=copy.deepcopy(para['locator'])
        (self.b/'packet.json').write_bytes(S.dump(packet));(self.b/'sources/manifest.json').write_bytes(S.dump(manifest))
        dbrows=copy.deepcopy(self.rows)
        source=next(x for x in dbrows['source_text'] if x['source_id']==U('source1'))
        source.update(content=text,content_sha256=S.sha(raw),archive_blob_sha256=S.sha(raw))
        next(x for x in dbrows['library_paragraph'] if x['id']==pid)['char_end']=para['locator']['char_end']
        return dbrows
    def test_edge_whitespace_survives_bundle_prepare_and_plan_link_guard(self):
        rows=self.rewrite_first_raw_fixture('\n甲年，甲事。\n\n')
        bundle=S.load_bundle(self.root,self.b);db=FakeDatabase(rows);plan=S.prepare(bundle,db)
        S.guard_plan(plan,self.root,db)
        link=next(x for x in plan['inserts']['library_source_link'] if x['source_id']==U('source1'))
        lib=rows['library_paragraph'][0]
        self.assertNotEqual(link['snapshot_sha256'],lib['content_sha256'])
        self.assertEqual(link['snapshot_sha256'],S.sha('\n甲年，甲事。\n\n'.encode()))
    def test_interior_whitespace_or_body_glyph_change_rejected_even_with_new_raw_hash(self):
        for text in ['甲年， 甲事。','甲年，乙事。']:
            self.rewrite_first_raw_fixture(text)
            with self.assertRaisesRegex(ValueError,'snapshot text differ'):S.load_bundle(self.root,self.b)
    def test_published_binding_and_snapshot_bytes_fail_closed(self):
        file=self.b/'sources'/self.bundle['manifest'][next(iter(self.bundle['manifest']))]['file'];file.write_bytes(file.read_bytes()+b'!')
        with self.assertRaisesRegex(ValueError,'SHA mismatch'):S.load_bundle(self.root,self.b)
    def test_unverified_volume_rejected_before_database(self):
        p=self.b/'publication-mysql.json';r=json.loads(p.read_bytes());r['verified']=False;p.write_bytes(S.dump(r))
        with self.assertRaisesRegex(ValueError,'verified MySQL'):S.load_bundle(self.root,self.b)
    def test_source_text_library_version_mismatch_rejected(self):
        self.rows['library_book'][0]['source_version']='wrong'
        with self.assertRaisesRegex(ValueError,'book/version'):S.prepare(self.bundle,FakeDatabase(self.rows))
    def test_claim_fingerprint_hex_vector_and_source_url_change(self):
        c=dict(subject_table='e',subject_id='1',claim_text='汉|A',source_id=None,citation='',note='')
        literal='65|31|E6B1897C41||||' # HEX(NULL) is empty, then source URL empty
        self.assertEqual(S.claim_fingerprint(c,''),hashlib.sha256(literal.encode()).hexdigest())
        self.assertNotEqual(S.claim_fingerprint(c,'a'),S.claim_fingerprint(c,'b'))
    def test_tampered_claim_or_wrong_sidecar_owner_rejected(self):
        bad=copy.deepcopy(self.rows);bad['fact_claim'][0]['note']+='变'
        with self.assertRaisesRegex(ValueError,'old value changed'):S.guard_plan(self.plan,self.root,FakeDatabase(bad))
        plan=copy.deepcopy(self.plan);plan['inserts']['event_dating'][0]['claim_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'fingerprint'):S.guard_plan(plan,self.root,self.db)
        plan=copy.deepcopy(self.plan);plan['inserts']['library_source_link'][0]['snapshot_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'snapshot hash'):S.guard_plan(plan,self.root,self.db)
    def test_fake_transaction_insert_only_idempotence_and_rollback(self):
        db=FakeDatabase(self.rows,writable=True);before=copy.deepcopy(db.rows)
        first=S.apply_plan(self.plan,self.root,db);self.assertEqual(first['actual_inserted']['event_dating'],3)
        second=S.apply_plan(self.plan,self.root,db);self.assertTrue(all(v==0 for v in second['actual_inserted'].values()))
        for table in before:self.assertEqual(db.rows[table],before[table])
        self.assertTrue(all(op in ['begin','commit'] or op[0]=='insert' and op[1] in S.FIELDS for op in db.operations))
        # An existing different row must fail before any sidecar is inserted.
        conflict=FakeDatabase(self.rows,writable=True);row=copy.deepcopy(self.plan['inserts']['event_dating'][0]);row['basis']='different';conflict.rows['event_dating']=[row]
        with self.assertRaisesRegex(ValueError,'identity conflict'):S.apply_plan(self.plan,self.root,conflict)
        self.assertEqual(conflict.operations,['begin','rollback'])
    def test_public_acceptance_checks_rich_datings_and_original_location(self):
        ds=self.plan['inserts']['event_dating'];ss={x['claim_id']:x for x in self.plan['inserts']['claim_structure']}
        def getter(url):
            if '/entry/' in url:
                eid=url.rsplit('/',1)[1];event=copy.deepcopy(next(r for r in self.rows['event'] if r['id']==eid));event['type']='event';event['datings']=[{**{k:v for k,v in d.items() if k not in ('claim_sha256','precision_kind')},'precision':d['precision_kind']} for d in ds if d['event_id']==eid];return event
            query=__import__('urllib.parse',fromlist=['parse_qs']).parse_qs(__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(url).query);requested=query['ids'][0].split(',');items=[]
            for c in self.rows['fact_claim']:
                if c['id'] not in requested:continue
                row=copy.deepcopy(c);st=ss[c['id']];row['evidence']=dict(origin='structured',quote=st['quote_text'],review=st['review_note'],review_state=st['review_state'],location=self.plan['source_locations'][c['source_id']]);items.append(row)
            return dict(items=items,has_more=False)
        good=S.verify_public(self.plan,'https://example.test/api/v1',getter);self.assertEqual(good['reviewed_datings'],3)
        def wrong(url):
            result=getter(url)
            if '/catalog/' in url:result['items'][0]['evidence'].pop('location')
            return result
        with self.assertRaisesRegex(ValueError,'location missing'):S.verify_public(self.plan,'https://example.test/api/v1',wrong)



class BulkTests(unittest.TestCase):
    def setUp(self):
        self.fixture=SourceTests(methodName='test_accumulates_each_source_year_without_last_call_overwrite');self.fixture.setUp()
        self.root=self.fixture.root.resolve();self.directory=self.fixture.b
        self.rows=copy.deepcopy(self.fixture.rows);self.bundle=S.load_bundle(self.root,self.directory)
        self.db=FakeDatabase(self.rows);self.plan=S.prepare(self.bundle,self.db)
    def tearDown(self):self.fixture.tearDown()
    def test_prepare_is_identical_to_row_engine_except_explicit_bulk_binding(self):
        plain=PlainDatabase(self.rows);expected=S._prepare_rows(self.bundle,plain)
        actual=copy.deepcopy(self.plan);binding=actual.pop('bulk_execution')
        self.assertEqual(actual,expected);self.assertEqual(binding['batch_size'],100)
        self.assertEqual(S._guard_rows(expected,self.root,PlainDatabase(self.rows)),S.guard_plan(self.plan,self.root,self.db))
    def test_queries_and_inserts_are_bounded_at_100(self):
        db=FakeDatabase(self.rows,writable=True)
        db.rows['event']=[dict(id=str(i),status='published') for i in range(251)]
        got=db.select_many('event',[dict(id=str(i)) for i in range(251)],lock=True)
        self.assertEqual(len(got),251);self.assertEqual([len(x[1]) for x in db.select_calls],[100,100,51]);self.assertTrue(all(x[2] for x in db.select_calls))
        template=self.plan['inserts']['event_dating'][0]
        rows=[dict(template,id=str(i)) for i in range(251)]
        db.insert_many('event_dating',rows)
        self.assertEqual([len(x[1]) for x in db.insert_calls],[100,100,51])
    def test_actual_sql_adapter_uses_bounded_selects_and_executemany_only(self):
        class Cursor:
            def __init__(self,connection):self.c=connection;self.rows=[]
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def execute(self,sql,params):
                self.c.selects.append((sql,list(params)))
                self.rows=[dict(id=x,status='published') for x in params]
            def fetchall(self):return self.rows
            def executemany(self,sql,values):self.c.inserts.append((sql,copy.deepcopy(values)))
        class Connection:
            def __init__(self):self.selects=[];self.inserts=[]
            def cursor(self,*args):return Cursor(self)
        db=S.Database.__new__(S.Database);db.writable=True;db.connection=Connection();db._phase=None
        columns={'event':{'id','status'},**{t:set(f) for t,f in S.FIELDS.items()}}
        db.store=types.SimpleNamespace(columns=columns,column=lambda t,k:'`'+k+'`',value=lambda t,k,v:v,normalize=lambda t,r:r)
        db.bulk_statistics=dict(select_batches=0,insert_batches=0,rows_requested=0)
        result=db.select_many('event',[dict(id=str(i)) for i in range(251)],lock=True)
        self.assertEqual(len(result),251);self.assertEqual([len(p) for _,p in db.connection.selects],[100,100,51])
        self.assertTrue(all(sql.startswith('SELECT * FROM `event` WHERE ') and sql.endswith(' FOR UPDATE') for sql,_ in db.connection.selects))
        template=self.plan['inserts']['event_dating'][0];db.insert_many('event_dating',[dict(template,id=str(i)) for i in range(251)])
        self.assertEqual([len(v) for _,v in db.connection.inserts],[100,100,51])
        self.assertTrue(all(sql.startswith('INSERT INTO `event_dating` ') and 'UPDATE' not in sql and 'DELETE' not in sql for sql,_ in db.connection.inserts))
    def test_prepare_reduces_get_roundtrips_without_changing_plan(self):
        class CountingPlain(PlainDatabase):
            def __init__(self,rows):super().__init__(rows);self.calls=0
            def get(self,*args,**kwargs):self.calls+=1;return super().get(*args,**kwargs)
        plain=CountingPlain(self.rows);expected=S._prepare_rows(self.bundle,plain)
        db=FakeDatabase(self.rows);actual=S.prepare(self.bundle,db);actual.pop('bulk_execution')
        self.assertEqual(actual,expected);self.assertLess(len(db.select_calls),plain.calls)
    def test_missing_protected_row_refuses_prepare(self):
        rows=copy.deepcopy(self.rows);rows['fact_claim'].pop()
        with self.assertRaisesRegex(ValueError,'Missing published'):S.prepare(self.bundle,FakeDatabase(rows))
    def test_tampered_full_old_value_refuses_guard(self):
        db=FakeDatabase(self.rows);db.rows['event'][0]['description']='changed'
        with self.assertRaisesRegex(ValueError,'old value changed'):S.guard_plan(self.plan,self.root,db)
    def test_duplicate_requested_and_returned_identities_are_rejected(self):
        ident=dict(id=self.rows['event'][0]['id'])
        with self.assertRaisesRegex(ValueError,'Duplicate bulk read'):self.db.select_many('event',[ident,ident])
        self.db.duplicate_return=True
        with self.assertRaisesRegex(ValueError,'Duplicate row returned'):self.db.select_many('event',[ident])
    def test_duplicate_planned_sidecar_rejected_before_mutation(self):
        plan=copy.deepcopy(self.plan);plan['inserts']['event_dating'].append(copy.deepcopy(plan['inserts']['event_dating'][0]));db=FakeDatabase(self.rows,writable=True)
        with self.assertRaisesRegex(ValueError,'Duplicate planned sidecar'):S.apply_plan(plan,self.root,db)
        self.assertEqual(db.insert_calls,[]);self.assertEqual(db.operations,['begin','rollback'])
    def test_same_id_different_existing_sidecar_value_rejected(self):
        rows=copy.deepcopy(self.rows);row=copy.deepcopy(self.plan['inserts']['event_dating'][0]);row['basis']='conflict';rows['event_dating']=[row];db=FakeDatabase(rows,writable=True)
        with self.assertRaisesRegex(ValueError,'identity conflict'):S.apply_plan(self.plan,self.root,db)
        self.assertEqual(db.insert_calls,[]);self.assertEqual(db.operations,['begin','rollback'])
    def test_identical_existing_rows_are_reused_and_apply_is_idempotent(self):
        db=FakeDatabase(self.rows,writable=True);before=copy.deepcopy(db.rows)
        first=S.apply_plan(self.plan,self.root,db);self.assertEqual(first['actual_inserted']['event_dating'],3)
        count=len(db.insert_calls);second=S.apply_plan(self.plan,self.root,db)
        self.assertTrue(all(v==0 for v in second['actual_inserted'].values()));self.assertEqual(len(db.insert_calls),count)
        for t,rows in before.items():self.assertEqual(db.rows[t],rows)
        self.assertTrue(all(lock for _,_,lock in db.select_calls))
    def test_late_canonical_conflict_rolls_back_all_insert_batches(self):
        db=FakeDatabase(self.rows,writable=True);before=copy.deepcopy(db.rows)
        def late(db,table):
            if table=='event_dating':db.rows['event'][0]['description']='late change'
        db.after_insert=late
        with self.assertRaisesRegex(ValueError,'old value changed'):S.apply_plan(self.plan,self.root,db)
        self.assertEqual(db.rows,before);self.assertEqual(db.operations,['begin','rollback']);self.assertGreater(len(db.insert_calls),0)
    def test_late_inserted_sidecar_conflict_rolls_back(self):
        db=FakeDatabase(self.rows,writable=True);before=copy.deepcopy(db.rows)
        def late(db,table):
            if table=='event_dating':db.rows['event_dating'][0]['basis']='changed after insertion'
        db.after_insert=late
        with self.assertRaisesRegex(ValueError,'identity conflict'):S.apply_plan(self.plan,self.root,db)
        self.assertEqual(db.rows,before);self.assertEqual(db.operations,['begin','rollback'])
    def test_each_guard_phase_requeries_and_never_reuses_prepare_results(self):
        self.assertIsNone(self.db._phase);before=len(self.db.select_calls);S.guard_plan(self.plan,self.root,self.db);self.assertGreater(len(self.db.select_calls),before)
        before=len(self.db.select_calls);self.db.rows['fact_claim'][0]['note']='tampered after prior guard'
        with self.assertRaisesRegex(ValueError,'old value changed'):S.guard_plan(self.plan,self.root,self.db)
        self.assertGreater(len(self.db.select_calls),before);self.assertIsNone(self.db._phase)
    def test_materialized_read_gap_lock_mismatch_and_mutation_are_rejected(self):
        db=FakeDatabase(self.rows,writable=True);event=dict(id=self.rows['event'][0]['id'])
        with db.phase(lock=True):
            db.preload({'event':[event]})
            with self.assertRaisesRegex(ValueError,'lock mode mismatch'):db.get('event',event)
            with self.assertRaisesRegex(ValueError,'Missing explicit bulk'):db.get('event',dict(id='absent'),lock=True)
            with self.assertRaisesRegex(ValueError,'Do not mutate'):db.insert_many('event_dating',[])
        self.assertIsNone(db._phase)
    def test_bulk_engine_binding_cannot_be_changed(self):
        plan=copy.deepcopy(self.plan);plan['bulk_execution']['implementation_sha256']='bad'
        with self.assertRaisesRegex(ValueError,'implementation'):S.guard_plan(plan,self.root,self.db)
        plan=copy.deepcopy(self.plan);plan['implementation_sha256']='bad'
        with self.assertRaisesRegex(ValueError,'implementation'):S.guard_plan(plan,self.root,self.db)
    def test_insert_validation_rejects_unexpected_fields_or_duplicate_ids(self):
        db=FakeDatabase(self.rows,writable=True);row=copy.deepcopy(self.plan['inserts']['event_dating'][0])
        with self.assertRaisesRegex(ValueError,'Unexpected bulk sidecar'):db.insert_many('event_dating',[dict(row,extra=1)])
        with self.assertRaisesRegex(ValueError,'Duplicate bulk insert'):db.insert_many('event_dating',[row,row])
        self.assertEqual(db.insert_calls,[])




class GenericTests(unittest.TestCase):
    def test_two_independent_books_and_unrestricted_volume_are_bound(self):
        for book,volume in [('alpha-history',1),('beta-history',87)]:
            fixture=SourceTests(methodName='test_accumulates_each_source_year_without_last_call_overwrite')
            fixture.book_key=book;fixture.volume=volume;fixture.setUp()
            try:
                p=fixture.plan
                self.assertEqual((p['book_key'],p['source_version'],p['volume']),(book,'version',volume))
                self.assertEqual(p['batch_dir'],str(fixture.b.relative_to(fixture.root)))
                S.guard_plan(p,fixture.root,fixture.db)
                wrong=copy.deepcopy(p);wrong['book_key']='unrelated'
                with self.assertRaisesRegex(ValueError,'book/version/volume mismatch'):S.guard_plan(wrong,fixture.root,fixture.db)
                wrong=copy.deepcopy(p);wrong['source_version']='other-version'
                with self.assertRaisesRegex(ValueError,'book/version/volume mismatch'):S.guard_plan(wrong,fixture.root,fixture.db)
                wrong=copy.deepcopy(p);wrong['volume']+=1
                with self.assertRaisesRegex(ValueError,'book/version/volume mismatch'):S.guard_plan(wrong,fixture.root,fixture.db)
            finally:fixture.tearDown()
    def test_packet_primary_version_and_directory_escape_fail_closed(self):
        fixture=SourceTests(methodName='test_accumulates_each_source_year_without_last_call_overwrite');fixture.setUp()
        try:
            path=fixture.b/'packet.json';packet=json.loads(path.read_bytes());packet['paragraphs'][0]['source_version']='foreign'
            path.write_bytes(S.dump(packet))
            with self.assertRaisesRegex(ValueError,'Primary paragraph book/version'):S.load_bundle(fixture.root,fixture.b)
            with self.assertRaisesRegex(ValueError,'inside --root'):S.load_bundle(fixture.root,fixture.root.parent)
        finally:fixture.tearDown()
    def test_default_cli_is_readonly_and_exact_sha_required_before_connect(self):
        fixture=SourceTests(methodName='test_accumulates_each_source_year_without_last_call_overwrite');fixture.setUp()
        try:
            db=FakeDatabase(fixture.rows);before=copy.deepcopy(db.rows)
            with mock.patch.object(S,'Database',return_value=db) as factory,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(S.main([str(fixture.b),'--root',str(fixture.root)]),0)
            self.assertFalse(factory.call_args.kwargs['writable']);self.assertEqual(db.rows,before)
            planpath=fixture.b/'.workflow/sidecars-plan.json';self.assertTrue(planpath.is_file())
            self.assertFalse((fixture.b/'.workflow/sidecars-receipt.json').exists())
            with mock.patch.object(S,'Database',side_effect=AssertionError('Database must not open')) as factory:
                with self.assertRaisesRegex(ValueError,'exact --expected-plan-sha256'):
                    S.main([str(fixture.b),'--root',str(fixture.root),'--apply','--expected-plan-sha256','wrong'])
                factory.assert_not_called()
            receipt=fixture.b/'.workflow/sidecars-receipt.json';receipt.write_bytes(S.dump(dict(plan_sha256=S.sha(planpath.read_bytes()),committed=True)))
            with mock.patch.object(S,'Database',side_effect=AssertionError('Database must not open')) as factory:
                with self.assertRaisesRegex(ValueError,'existing receipt'):
                    S.main([str(fixture.b),'--root',str(fixture.root),'--refresh-plan'])
                factory.assert_not_called()
        finally:fixture.tearDown()
    def test_unverified_publication_and_external_plan_rejected_before_connect(self):
        fixture=SourceTests(methodName='test_accumulates_each_source_year_without_last_call_overwrite');fixture.setUp()
        try:
            with mock.patch.object(S,'Database',side_effect=AssertionError('Database must not open')) as factory:
                with self.assertRaisesRegex(ValueError,'this batch directory/.workflow'):
                    S.main([str(fixture.b),'--root',str(fixture.root),'--plan',str(fixture.root/'elsewhere.json')])
                path=fixture.b/'publication-mysql.json';row=json.loads(path.read_bytes());row['verified']=False;path.write_bytes(S.dump(row))
                with self.assertRaisesRegex(ValueError,'verified MySQL'):
                    S.main([str(fixture.b),'--root',str(fixture.root)])
                factory.assert_not_called()
        finally:fixture.tearDown()


class FullAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture=SourceTests(methodName='test_accumulates_each_source_year_without_last_call_overwrite');self.fixture.setUp()
    def tearDown(self):self.fixture.tearDown()
    def test_anonymous_acceptance_checks_every_claim_across_multiple_batches(self):
        plan=copy.deepcopy(self.fixture.plan);template=copy.deepcopy(self.fixture.rows['fact_claim'][0]);structure=copy.deepcopy(plan['inserts']['claim_structure'][0])
        claims={};structures=[]
        for i in range(125):
            cid=U('public-full-'+str(i));claims[cid]=dict(template,id=cid)
            structures.append(dict(structure,claim_id=cid))
        plan['inserts']['claim_structure']=structures
        plan['protected_rows']=[p for p in plan['protected_rows'] if p['table']!='fact_claim']+[dict(table='fact_claim',identity=dict(id=c['id']),row=c) for c in claims.values()]
        byid={s['claim_id']:s for s in structures};groups=[]
        def getter(url):
            if '/entry/' in url:
                eid=url.rsplit('/',1)[1];event=copy.deepcopy(next(r for r in self.fixture.rows['event'] if r['id']==eid));event['type']='event'
                event['datings']=[{**{k:v for k,v in d.items() if k not in ('claim_sha256','precision_kind')},'precision':d['precision_kind']} for d in plan['inserts']['event_dating'] if d['event_id']==eid]
                return event
            requested=__import__('urllib.parse',fromlist=['parse_qs']).parse_qs(__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(url).query)['ids'][0].split(',');groups.append(requested);rows=[]
            for cid in requested:
                c=claims[cid];st=byid[cid]
                rows.append(dict(c,evidence=dict(origin='structured',quote=st['quote_text'],review=st['review_note'],review_state=st['review_state'],location=plan['source_locations'][c['source_id']])))
            return dict(items=rows,has_more=False)
        result=S.verify_public(plan,'https://offline.test/api/v1',getter)
        self.assertEqual(result['claims_with_original_locations'],125);self.assertEqual([len(g) for g in groups],[50,50,25]);self.assertEqual(len({c for g in groups for c in g}),125)
        def omitted(url):
            result=getter(url)
            if '/catalog/' in url:result['items']=result['items'][:-1]
            return result
        with self.assertRaisesRegex(ValueError,'missing/extra IDs'):S.verify_public(plan,'https://offline.test/api/v1',omitted)
    def test_missing_global_lock_prevents_any_transaction_or_mutation(self):
        db=FakeDatabase(self.fixture.rows,writable=True)
        with mock.patch.object(db,'assert_publish_lock',side_effect=ValueError('Global content publisher lock is not held')):
            with self.assertRaisesRegex(ValueError,'Global content publisher lock'):S.apply_plan(self.fixture.plan,self.fixture.root,db)
        self.assertEqual(db.operations,[]);self.assertEqual(db.insert_calls,[])

if __name__=='__main__':unittest.main()
