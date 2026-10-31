#!/usr/bin/env python3
"""Native MySQL 8 sidecar regression, after `pnpm test:mysql` schema bootstrap.

Only process MYSQL_* variables are accepted; no repository/production env is read.
Requires PyMySQL. Run with MYSQL_HOST=127.0.0.1 and MYSQL_DATABASE=histree_test_*.
No schema changes, HTTP, paid models, TRUNCATE or database-wide DELETE. The fixed
fixtures are deleted only by their own exact IDs; all preexisting table PK sets
must be unchanged afterward. content_revision's normal trigger increments remain.
`--check-safety` exercises the connection allowlist without opening any socket.
"""
import copy
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid
from unittest import mock

import history_sidecars as S

NAMESPACE = uuid.UUID('cb40290f-d1f3-55f7-9985-81b30d87a226')
UID = lambda name: str(uuid.uuid5(NAMESPACE, name))
BOOK = 'sidecars-mysql-fixture-v1'
VERSION = 'native-fixture-v1'
VOLUME = 37
SECTION = BOOK + '-s0037'
ASSET = S.sha(b'history-sidecars-mysql-fixture-asset-v1')
PEOPLE = [UID('person'), UID('unrelated-sentinel')]
PERSON_KEY = 'person_mysql_sidecars_fixture'
EVENT_KEYS = ['event_many', 'event_range', 'event_inherited']
EVENT_IDS = [UID(key) for key in EVENT_KEYS]
SOURCE_IDS = [UID('source' + str(i)) for i in range(1, 5)]
CLAIM_KEYS = ['person_fact', 'many_first', 'many_second', 'range_fact', 'inherited_fact']
CLAIM_IDS = [UID(key) for key in CLAIM_KEYS]
PARAGRAPHS = [BOOK + '-p' + str(i).zfill(6) for i in range(1, 5)]
TABLE_KEYS = {
    'person': ('id',), 'event': ('id',), 'source': ('id',),
    'fact_claim': ('id',), 'source_text': ('source_id', 'archive_url_sha256'),
    'library_book': ('book_key',), 'library_asset': ('id',),
    'library_section': ('id',), 'library_paragraph': ('id',),
    'library_source_link': ('source_id', 'archive_url_sha256'),
    'claim_structure': ('claim_id',), 'event_dating': ('id',),
}


def test_environment(values):
    """Validate before reading credentials into a file or constructing a DB store."""
    host = values.get('MYSQL_HOST', '')
    name = values.get('MYSQL_DATABASE', '')
    S.require(host in ('localhost', '127.0.0.1'), 'Only localhost/127.0.0.1 test MySQL is accepted')
    S.require(re.fullmatch(r'histree_test_[a-z0-9_]+', name) is not None,
              'Only explicitly named histree_test_* databases are accepted')
    port = str(values.get('MYSQL_PORT', '3306'))
    S.require(port.isdecimal() and 1 <= int(port) <= 65535, 'Invalid test MySQL port')
    S.require(bool(values.get('MYSQL_USER')), 'MYSQL_USER is required')
    result = dict(MYSQL_HOST=host, MYSQL_PORT=port, MYSQL_DATABASE=name,
                  MYSQL_USER=values['MYSQL_USER'], MYSQL_PASSWORD=values.get('MYSQL_PASSWORD', ''),
                  MYSQL_SSL_MODE=values.get('MYSQL_SSL_MODE', 'disabled'))
    S.require(all(isinstance(v,str) and '\n' not in v and '\r' not in v for v in result.values()), 'Multiline test environment value is unsupported')
    return result


def safety_checks():
    base = dict(MYSQL_HOST='127.0.0.1', MYSQL_DATABASE='histree_test_sidecars', MYSQL_USER='test')
    for host in ('localhost', '127.0.0.1'):
        assert test_environment(dict(base, MYSQL_HOST=host))['MYSQL_HOST'] == host
    for host in ('production.invalid', '127.0.0.1.example', '::1', '', 'localhost '):
        try: test_environment(dict(base, MYSQL_HOST=host))
        except ValueError: pass
        else: raise AssertionError('Unsafe host accepted')
    for database in ('histree', 'histree_test_', 'histree_test_a;DROP', 'histree_test_A', ''):
        try: test_environment(dict(base, MYSQL_DATABASE=database))
        except ValueError: pass
        else: raise AssertionError('Unsafe database accepted')
    print('PASS: local host/database allowlist, sockets=0, env files read=0')


def connection_identity(connection, env):
    # Also reject a misconfigured localhost resolver returning a non-loopback peer.
    peer = connection._sock.getpeername()[0]
    S.require(ipaddress.ip_address(peer).is_loopback, 'MySQL peer is not loopback')
    with connection.cursor() as cursor:
        cursor.execute('SELECT DATABASE(),VERSION()')
        name, version = cursor.fetchone()
        S.require(name == env['MYSQL_DATABASE'] and version.startswith('8.'), 'Wrong test database/MySQL major version')
        cursor.execute('SET SESSION MAX_EXECUTION_TIME=5000')
        cursor.execute('SET SESSION innodb_lock_wait_timeout=5')


def primary_keys(connection):
    result = {}
    with connection.cursor() as cursor:
        for table, columns in TABLE_KEYS.items():
            cursor.execute('SELECT ' + ','.join('`' + c + '`' for c in columns) + ' FROM `' + table + '`')
            result[table] = set(cursor.fetchall())
    return result


def insert(connection, table, row):
    # Tables and keys come exclusively from the fixed fixture declarations below.
    with connection.cursor() as cursor:
        columns = list(row)
        cursor.execute('INSERT INTO `' + table + '` (' + ','.join('`' + c + '`' for c in columns) +
                       ') VALUES (' + ','.join(['%s'] * len(columns)) + ')', list(row.values()))


def fixtures(root, target_fingerprint):
    directory = root / 'content/books' / BOOK / 'vol-037/from-start/part-01'
    directory.mkdir(parents=True)
    envfile = root / 'local-test-only.env'
    raw_texts = ['\n甲于九百年作甲事。\n', '次年，甲再作乙事。', '九百二年至九百五年之间，甲居此。', '合成 结构 标题']
    display = [raw_texts[0].strip(), raw_texts[1], raw_texts[2], '合成结构标题']
    bottom = ''.join(raw_texts)
    source_file = 'resources/mysql-sidecars-fixture.txt'
    (root/'resources').mkdir(); (root/source_file).write_text(bottom)
    bottom_sha = S.sha(bottom.encode('utf-8'))
    ids = {PERSON_KEY:PEOPLE[0], **dict(zip(EVENT_KEYS, EVENT_IDS))}
    sources = []; manifest = []; paras = []; source_texts = []; library = []; offset = 0
    for index, (raw, text) in enumerate(zip(raw_texts, display), 1):
        pid = PARAGRAPHS[index-1]; sk = 'source' + str(index); sid = SOURCE_IDS[index-1]; ids[sk] = sid
        url = 'https://github.com/greed-216/histree/blob/' + 'a'*40 + '/content/native-sidecars-fixture/source' + str(index) + '.txt'
        digest = S.sha(raw.encode('utf-8'))
        locator = dict(source_file=source_file, source_sha256=bottom_sha, char_start=offset,
                       char_end=offset+len(raw), raw_excerpt_sha256=digest)
        para = dict(id=pid, book_key=BOOK, source_version=VERSION, section_id=SECTION,
                    volume_candidate=VOLUME, kind='body' if index<4 else 'heading',
                    flags=[] if index<4 else ['editorial_navigation_heading','not_historical_body'],
                    text=text, locator=locator)
        paras.append(para); offset += len(raw)
        source = dict(key=sk,title='合成来源'+str(index),source_type='primary',url=url); sources.append(source)
        m = dict(paragraph_id=pid,key=sk,file=pid+'/source.txt',sha256=digest,url=url,
                 upstream_locator=copy.deepcopy(locator)); manifest.append(m)
        path=directory/'sources'/m['file'];path.parent.mkdir(parents=True);path.write_bytes(raw.encode('utf-8'))
        source_texts.append(dict(source_id=sid,archive_url_sha256=S.sha(url.encode('utf-8')),archive_url=url,
                                 content=raw,content_sha256=digest,archive_blob_sha256=digest,archive_commit='a'*40))
        library.append(dict(id=pid,book_key=BOOK,section_id=SECTION,ordinal=index,kind=para['kind'],content=text,
                            content_sha256=S.sha(text.encode('utf-8')),asset_id=ASSET,char_start=locator['char_start'],
                            char_end=locator['char_end'],flags=json.dumps(para['flags'])))
    event_rows = [
        dict(key=EVENT_KEYS[0],title='甲先后作事',description='甲先后作甲乙两事。',dynasty='合成时代',start_year=900,end_year=900,time_original='九百年及次年'),
        dict(key=EVENT_KEYS[1],title='甲居此',description='甲曾居此。',dynasty='合成时代',start_year=None,end_year=None,time_original='九百二年至九百五年之间'),
        dict(key=EVENT_KEYS[2],title='仅继承旧年',description='旧事件补证。',dynasty='合成时代',start_year=888,end_year=888,time_original='旧日期'),
    ]
    reviews = [
        dict(decision='inherited',reason='逐段独立纪年',anchor_note='两段分别有年份',source_dating_assertions=[
            dict(paragraph_id=PARAGRAPHS[0],year=900,basis='第一段记九百年'),
            dict(paragraph_id=PARAGRAPHS[1],year=901,basis='第二段为次年，人工已核对照')]),
        dict(decision='range',earliest_year=902,latest_year=905,reason='原文明示上下界',anchor_note='第三段原文'),
        dict(decision='inherited',reason='仅沿旧888年，不据本段重新确年',anchor_note='本段没有独立确年结论'),
    ]
    claims=[]; evidence={k:[] for k in EVENT_KEYS}
    definitions=[('person_fact','person',PERSON_KEY,1,'description','甲曾作事。'),
                 ('many_first','event',EVENT_KEYS[0],1,'description','甲在九百年作甲事。'),
                 ('many_second','event',EVENT_KEYS[0],2,'description','甲在次年作乙事。'),
                 ('range_fact','event',EVENT_KEYS[1],3,'time_original','九百二年至九百五年之间'),
                 ('inherited_fact','event',EVENT_KEYS[2],3,'description','本段作为旧事件补证。')]
    for key, table, subject, index, field, text in definitions:
        ids[key]=UID(key);quote=display[index-1]
        c=dict(key=key,subject_table=table,subject_key=subject,source_key='source'+str(index),
               field_path=field,claim_text=text,citation='合成测试卷37，'+PARAGRAPHS[index-1],
               note='原文：'+quote+'；核对说明：合成样本，逐字绑定。',status='draft');claims.append(c)
        if table=='event':evidence[subject].append(dict(paragraph_id=PARAGRAPHS[index-1],field=field,text=text,quote=quote))
    person_row=dict(key=PERSON_KEY,name='合成甲',description='甲曾作事。',era='合成时代')
    batch=dict(format_version=1,batch_key='native-sidecars-fixture-v1',people=[person_row],events=event_rows,
               person_events=[],person_relationships=[],event_causalities=[],topics=[],sources=sources,claims=claims)
    items=[dict(group='events',row=row,evidence=evidence[row['key']],temporal_review=review) for row,review in zip(event_rows,reviews)]
    items.insert(0,dict(group='people',row=person_row,evidence=[dict(paragraph_id=PARAGRAPHS[0],field='description',text='甲曾作事。',quote=display[0])]))
    def write(name,value):
        p=directory/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(S.dump(value))
    write('content-batch.json',batch)
    digest=S.sha((directory/'content-batch.json').read_bytes())
    write('curation.json',dict(batch_key=batch['batch_key'],claim_namespace=batch['batch_key'],items=items,
                              paragraph_reviews=[dict(paragraph_id=p,status='reviewed') for p in PARAGRAPHS]))
    write('packet.json',dict(book_key=BOOK,source_version=VERSION,volume=VOLUME,paragraphs=paras))
    write('sources/manifest.json',manifest);write('sql/key-map.json',ids)
    write('publication-mysql.json',dict(backend='mysql',verified=True,target_fingerprint=target_fingerprint,batch_sha256=digest))
    write('time-review.json',dict(batch_sha256=digest,events=[dict(key=k,**r) for k,r in zip(EVENT_KEYS,reviews)]))
    seed={
        'library_book':[dict(book_key=BOOK,title='合成侧表测试书',source_version=VERSION,sort_order=0,section_count=1,paragraph_count=4,dataset_sha256=bottom_sha,metadata='{}',status='available')],
        'library_asset':[dict(id=ASSET,source_file=source_file,source_sha256=bottom_sha)],
        'library_section':[dict(id=SECTION,book_key=BOOK,sort_order=0,title='卷37',volume=VOLUME,kind='volume',has_issues=0,metadata='{}')],
        'library_paragraph':library,
        'person':[dict(id=PEOPLE[0],**{k:v for k,v in person_row.items() if k!='key'},status='published'),dict(id=PEOPLE[1],name='独立保留哨兵',description='不在批次内，必须保持原样。',status='published')],
        'event':[dict(id=ids[r['key']],**{k:v for k,v in r.items() if k!='key'},status='published') for r in event_rows],
        'source':[dict(id=ids[r['key']],**{k:v for k,v in r.items() if k!='key'}) for r in sources],
        'source_text':source_texts,
        'fact_claim':[S.normalized_claim(c,ids) for c in claims],
    }
    return directory,envfile,seed,ids


def count_sidecars(db):
    result={}
    with db.connection.cursor() as c:
        for table,column,values in [('event_dating','event_id',EVENT_IDS),('claim_structure','claim_id',CLAIM_IDS),('library_source_link','source_id',SOURCE_IDS)]:
            c.execute('SELECT COUNT(*) FROM `'+table+'` WHERE `'+column+'` IN ('+','.join(['%s']*len(values))+')',values)
            result[table]=c.fetchone()[0]
    return result


def cleanup(connection):
    # Exact own IDs only. No discovery-based deletion, foreign-key disabling or DDL.
    owned=[('event_dating','event_id',EVENT_IDS),('claim_structure','claim_id',CLAIM_IDS),
           ('library_source_link','source_id',SOURCE_IDS),('fact_claim','id',CLAIM_IDS),
           ('source_text','source_id',SOURCE_IDS),('source','id',SOURCE_IDS),
           ('event','id',EVENT_IDS),('person','id',PEOPLE),('library_paragraph','id',PARAGRAPHS),
           ('library_section','id',[SECTION]),('library_asset','id',[ASSET]),('library_book','book_key',[BOOK])]
    connection.rollback();connection.begin()
    try:
        with connection.cursor() as c:
            for table,column,values in owned:
                c.execute('DELETE FROM `'+table+'` WHERE `'+column+'` IN ('+','.join(['%s']*len(values))+')',values)
                S.require(0<=c.rowcount<=max(len(values),5),'Unexpected own-fixture cleanup count')
        connection.commit()
    except BaseException:connection.rollback();raise


def run(env):
    import pymysql
    from mysql_content_store import _preflight as local
    fp=S.sha(json.dumps([env['MYSQL_HOST'],int(env['MYSQL_PORT']),env['MYSQL_DATABASE']],separators=(',',':')).encode())
    conn=local.connect_mysql(env,True);connection_identity(conn,env)
    seeded=False;db=None;baseline=None;checks=0
    try:
        baseline=primary_keys(conn)  # CI schema must already exist; never bootstrapped here.
        with tempfile.TemporaryDirectory(prefix='histree-sidecars-mysql-') as temp:
            root=Path(temp);directory,envfile,seed,ids=fixtures(root,fp)
            for table,rows in seed.items():
                columns=TABLE_KEYS[table]
                S.require(not any(tuple(r[k] for k in columns) in baseline[table] for r in rows),'Fixed fixture IDs already exist; refusing to adopt/delete them')
            S.require(not any(key[0] in SOURCE_IDS for key in baseline['library_source_link']), 'Existing orphan/source link overlaps fixture IDs; refusing cleanup ownership')
            # Database() reads only this mode-0600 disposable file, never production env.
            # read_env strips only outer quotes; preserve embedded quotes/backslashes literally.
            envfile.write_text('\n'.join(k+'=\"'+v+'\"' for k,v in env.items())+'\n');envfile.chmod(0o600)
            for table,rows in seed.items():
                for row in rows:insert(conn,table,row)
            conn.commit();seeded=True
            bundle=S.load_bundle(root,directory)
            readonly=S.Database(root,envfile,writable=False);connection_identity(readonly.connection,env)
            try:
                plan=S.prepare(bundle,readonly);counts=S.guard_plan(plan,root,readonly)
                assert {t:v['new'] for t,v in counts.items()}==dict(event_dating=3,claim_structure=5,library_source_link=3)
                assert count_sidecars(readonly)==dict(event_dating=0,claim_structure=0,library_source_link=0)
                assert len(plan['skipped_independent_dates'])==1 and plan['excluded_structural_headings']==[PARAGRAPHS[3]]
                readonly.connection.rollback();checks+=1
            finally:readonly.connection.close()
            db=S.Database(root,envfile,writable=True);connection_identity(db.connection,env);db.assert_publish_lock()
            sentinel_before=db.get('event',dict(id=EVENT_IDS[0]));outside_before=db.store.read('person','r.id=%s',[PEOPLE[1]],'*','r.id',1,0)[0]
            real_insert_many=db.insert_many
            for conflict in ('canonical','sidecar'):
                def late(table,rows):
                    real_insert_many(table,rows)
                    if table=='event_dating':
                        with db.connection.cursor() as c:
                            if conflict=='canonical':c.execute('UPDATE event SET description=%s WHERE id=%s',('late conflict',EVENT_IDS[0]))
                            else:c.execute('UPDATE event_dating SET basis=%s WHERE id=%s',('late conflict',plan['inserts']['event_dating'][0]['id']))
                with mock.patch.object(db,'insert_many',side_effect=late):
                    try:S.apply_plan(plan,root,db)
                    except ValueError as error:
                        assert 'old value changed' in str(error) if conflict=='canonical' else 'identity conflict' in str(error)
                    else:raise AssertionError('Late conflict did not abort the real MySQL transaction')
                assert count_sidecars(db)==dict(event_dating=0,claim_structure=0,library_source_link=0)
                assert db.get('event',dict(id=EVENT_IDS[0]))==sentinel_before
                assert db.store.read('person','r.id=%s',[PEOPLE[1]],'*','r.id',1,0)[0]==outside_before
                checks+=1
            first=S.apply_plan(plan,root,db)
            assert first['actual_inserted']==dict(event_dating=3,claim_structure=5,library_source_link=3)
            assert count_sidecars(db)==first['actual_inserted'];checks+=1
            second=S.apply_plan(plan,root,db)
            assert all(n==0 for n in second['actual_inserted'].values())
            assert all(v['new']==0 for v in S.guard_plan(plan,root,db).values());checks+=1
            for protected in plan['protected_rows']:
                assert db.get(protected['table'],protected['identity'])==protected['row']
            assert db.get('event',dict(id=EVENT_IDS[0]))['start_year']==900
            assert db.get('event',dict(id=EVENT_IDS[1]))['start_year'] is None
            assert db.get('event',dict(id=EVENT_IDS[2]))['start_year']==888
            assert db.store.read('person','r.id=%s',[PEOPLE[1]],'*','r.id',1,0)[0]==outside_before;checks+=1
            for row in plan['inserts']['event_dating']:
                assert all(db.get('event_dating',dict(id=row['id']))[k]==v for k,v in row.items())
                claim=db.get('fact_claim',dict(id=row['claim_id']));source=db.get('source',dict(id=claim['source_id']))
                assert row['claim_sha256']==S.claim_fingerprint(claim,source['url'])
            assert sorted((r['earliest_year'],r['latest_year']) for r in plan['inserts']['event_dating'])==[(900,900),(901,901),(902,905)]
            for row in plan['inserts']['claim_structure']:
                actual=db.get('claim_structure',dict(claim_id=row['claim_id']))
                assert all(actual[k]==v for k,v in row.items())
                assert actual['review_state']=='recorded' and actual['quote_text'] in ''.join(p['text'] for p in bundle['paras'].values())
            for link in plan['inserts']['library_source_link']:
                actual=db.get('library_source_link',{k:link[k] for k in S.IDENTITY['library_source_link']})
                assert actual==link
                text=db.get('source_text',dict(source_id=link['source_id'],archive_url_sha256=link['archive_url_sha256']))
                para=db.get('library_paragraph',dict(id=link['paragraph_id']));book=db.get('library_book',dict(book_key=para['book_key']))
                assert link['snapshot_sha256']==S.sha(text['content'].encode('utf-8')) and S.exact_text_with_structural_edges(text['content'],para['content'])
                assert book['source_version']==VERSION and para['book_key']==BOOK
                assert (para['char_start'],para['char_end'])==(bundle['paras'][para['id']]['locator']['char_start'],bundle['paras'][para['id']]['locator']['char_end'])
            assert PARAGRAPHS[3] not in {r['paragraph_id'] for r in plan['inserts']['library_source_link']};checks+=1
            first_link=next(r for r in plan['inserts']['library_source_link'] if r['paragraph_id']==PARAGRAPHS[0])
            assert first_link['snapshot_sha256']!=db.get('library_paragraph',dict(id=PARAGRAPHS[0]))['content_sha256'];checks+=1
            # A provenance-only package publishes real source links without inventing claims.
            source_only_dir=directory.parent.parent/'source-only/part-01'
            shutil.copytree(directory,source_only_dir)
            b=json.loads((source_only_dir/'content-batch.json').read_bytes())
            for field in ('people','events','person_events','person_relationships','claims','topics'):b[field]=[]
            b['batch_key']='native-source-only';(source_only_dir/'content-batch.json').write_bytes(S.dump(b))
            cur=json.loads((source_only_dir/'curation.json').read_bytes());cur.update(batch_key=b['batch_key'],claim_namespace=b['batch_key'],items=[]);(source_only_dir/'curation.json').write_bytes(S.dump(cur))
            proof=json.loads((source_only_dir/'publication-mysql.json').read_bytes());proof.update(source_only_evidence=True,batch_sha256=S.sha((source_only_dir/'content-batch.json').read_bytes()));(source_only_dir/'publication-mysql.json').write_bytes(S.dump(proof))
            (source_only_dir/'time-review.json').write_bytes(S.dump(dict(batch_sha256=proof['batch_sha256'],events=[])))
            source_plan=S.prepare(S.load_bundle(root,source_only_dir),db)
            assert len(source_plan['inserts']['library_source_link'])==3 and not source_plan['inserts']['claim_structure'] and not source_plan['inserts']['event_dating']
            linked=S.apply_plan(source_plan,root,db);assert all(n==0 for n in linked['actual_inserted'].values());checks+=1
            print(json.dumps(dict(passed=checks,native_mysql=True,model_calls=0,ddl=0,bulk_statistics=db.bulk_statistics,late_conflict_rollbacks=2),sort_keys=True))
    finally:
        if db is not None:db.connection.close()  # releases the global publication lock
        try:
            conn.rollback()
            if seeded:
                cleanup(conn)
                assert primary_keys(conn)==baseline,'Cleanup changed preexisting rows or left owned fixture rows behind'
                print('PASS: own fixture IDs cleaned; every preexisting business/library primary key preserved')
        finally:conn.close()
    return 0


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if args==['--check-safety']:safety_checks();return 0
    S.require(not args,'No options accepted except --check-safety; configure isolated MySQL via process environment')
    return run(test_environment(os.environ))


if __name__=='__main__':raise SystemExit(main())
