/** Disposable native MySQL contracts. Never accepts a production database name. */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {randomUUID,randomBytes} from 'node:crypto';
const require=createRequire(new URL('../apps/api/package.json',import.meta.url));
const {ConfigService}=require('@nestjs/config');
const {MysqlService}=require('./dist/modules/mysql/mysql.service.js');
const {loadGuessCatalogue,matchesGuessYears}=require('./dist/modules/ask/guess-catalogue.js');
const {createConnection}=require('mysql2/promise');
const env=process.env;
assert.match(env.MYSQL_DATABASE || '', /^histree_test_[a-z0-9_]+$/, 'Only an explicitly named disposable test database is accepted');
assert.ok(['127.0.0.1','localhost'].includes(env.MYSQL_HOST),'Tests require a local MySQL service');
const config={...env,HISTREE_DATABASE:'mysql'};
const db=new MysqlService(new ConfigService(config));
const connection=await createConnection({host:env.MYSQL_HOST,port:Number(env.MYSQL_PORT||3306),user:env.MYSQL_USER,password:env.MYSQL_PASSWORD,database:env.MYSQL_DATABASE,charset:'utf8mb4',timezone:'Z',dateStrings:true,decimalNumbers:true});
let checks=0;const originalRows=db.rows.bind(db);
try {
  const [existing]=await connection.query('SHOW TABLES');
  assert.equal(existing.length,0,'Schema initialization requires an empty disposable database');
  const ddl=await readFile(new URL('../database/mysql/001-content.sql',import.meta.url),'utf8');
  for(const statement of ddl.replace(/^DELIMITER .*$/gm,'').split('$$').map(s=>s.trim()).filter(Boolean))await connection.query(statement);
  await connection.query(await readFile(new URL('../database/mysql/002-ai-quota.sql',import.meta.url),'utf8'));
  for(const statement of (await readFile(new URL('../database/mysql/003-guess-bank.sql',import.meta.url),'utf8')).split(';').map(s=>s.trim()).filter(Boolean))await connection.query(statement);
  for(const statement of (await readFile(new URL('../database/mysql/004-guess-clues.sql',import.meta.url),'utf8')).split(';').map(s=>s.trim()).filter(Boolean))await connection.query(statement);
  await connection.beginTransaction();
  const [published,hidden,source,relation,claim,hiddenClaim]=Array.from({length:6},()=>randomUUID());
  await connection.execute('INSERT INTO person(id,name,status,aliases) VALUES(?,?,?,JSON_ARRAY(?)),(?,?,?,JSON_ARRAY())',[published,'测试%_','published','A"B\\C',hidden,'秘密草稿','draft']);
  await connection.execute('INSERT INTO source(id,title,source_type,url) VALUES(?,?,?,?)',[source,'测试来源','primary','https://example.org']);
  await connection.execute('INSERT INTO person_relationship(id,person_a,person_b,relation_type,status) VALUES(?,?,?,?,?)',[relation,published,hidden,'父亲','published']);
  for(const [cid,table,sid,text] of [[claim,'person',published,'公开引文%_'],[hiddenClaim,'person_relationship',relation,'秘密关系引文']])await connection.execute('INSERT INTO fact_claim(id,subject_table,subject_id,claim_text,source_id,status,field_path) VALUES(?,?,?,?,?,?,?)',[cid,table,sid,text,source,'published','description']);
  db.rows=async(sql,args=[])=>{const [rows]=await connection.execute(sql,args);return rows;};
  assert.equal(await db.rpc('entry_detail',{p_id:hidden}),null);checks++;
  for(const [table,rid] of [['person_relationship',relation],['fact_claim',hiddenClaim]]){assert.equal((await db.rpc('content_page',{p_table:table,p_ids:[rid]})).items.length,0);checks++;}
  assert.equal((await db.rpc('content_page',{p_table:'fact_claim',p_ids:[claim]})).items[0].source.id,source);checks++;
  assert.ok(!(await db.rpc('entry_context',{p_id:published})).edges.some(e=>e.id===relation));checks++;
  assert.ok(!(await db.rpc('graph_slice',{p_id:published,p_mode:'people',p_depth:2})).nodes.some(n=>n.id===hidden));checks++;
  assert.equal((await db.rpc('search_entries',{p_query:'测试%_'})).items[0].id,published);checks++;
  assert.equal((await db.rpc('search_entries',{p_query:'A"B\\C'})).items[0].id,published);checks++;
  assert.ok(!(await db.rpc('ask_search',{p_keywords:['秘密关系引文']})).items.length);checks++;
  for(let offset=0;offset<1205;offset+=100){
    const rows=Array.from({length:Math.min(100,1205-offset)},()=>[randomUUID(),'年代测试',900,'published']);
    await connection.query('INSERT INTO event(id,title,start_year,status) VALUES ?', [rows]);
  }
  await connection.execute('INSERT INTO event(id,title,start_year,end_year,status) VALUES(?,?,?,?,?),(?,?,?,?,?),(?,?,?,?,?)',[randomUUID(),'公元前',-403,-400,'published',randomUUID(),'待考',null,null,'published',randomUUID(),'隐藏事件',2000,2000,'draft']);
  const overview=await db.rpc('timeline_overview',{});assert.equal(overview.total,1207);assert.equal(overview.undated,1);assert.equal(overview.years.find(y=>y.year===900).count,1205);assert.equal(overview.from,-403);checks++;
  const first=await db.rpc('content_page',{p_table:'event',p_limit:20});const second=await db.rpc('content_page',{p_table:'event',p_page:1,p_limit:20});assert.equal(first.items.length,20);assert.equal(first.has_more,true);assert.ok(!second.items.some(r=>first.items.some(p=>p.id===r.id)));checks++;
  await assert.rejects(db.rpc('content_page',{p_table:'person',p_admin:true}));await assert.rejects(db.rpc('unsupported',{}));checks++;
  // Game eligibility uses published original-text evidence and published event dates.
  const testSignal=AbortSignal.timeout(60000);
  assert.equal((await loadGuessCatalogue(db,testSignal)).length,0);checks++;
  await connection.execute('UPDATE fact_claim SET note=? WHERE id=?',['原文：可回溯测试原文。',claim]);
  const [datedEvent,draftEvent,emptySource]=Array.from({length:3},()=>randomUUID());
  await connection.execute('INSERT INTO event(id,title,start_year,end_year,status) VALUES(?,?,?,?,?),(?,?,?,?,?)',[datedEvent,'公开活动',900,907,'published',draftEvent,'隐藏活动',1900,1900,'draft']);
  await connection.execute('INSERT INTO person_event(id,person_id,event_id,role,status) VALUES(?,?,?,?,?),(?,?,?,?,?),(?,?,?,?,?)',[randomUUID(),published,datedEvent,'参与','published',randomUUID(),published,draftEvent,'参与','published',randomUUID(),published,datedEvent,'参与','draft']);
  await connection.execute('INSERT INTO source(id,title,source_type) VALUES(?,?,?)',[emptySource,'','primary']);
  for(const [name,status,sourceId,note] of [['未发布人物','draft',source,'原文：草稿'],['无原文人物','published',source,'转述'],['无来源人物','published',null,'原文：无来源'],['空来源人物','published',emptySource,'原文：来源无标题']]){
    const pid=randomUUID();
    await connection.execute('INSERT INTO person(id,name,status) VALUES(?,?,?)',[pid,name,status]);
    await connection.execute('INSERT INTO fact_claim(id,subject_table,subject_id,claim_text,source_id,status,field_path,note) VALUES(?,?,?,?,?,?,?,?)',[randomUUID(),'person',pid,'测试事实',sourceId,'published','description',note]);
  }
  const playable=await loadGuessCatalogue(db,testSignal);
  assert.deepEqual(playable.map(p=>p.id),[published]);checks++;
  assert.deepEqual(playable[0].activity,[{from:900,to:907}]);checks++;
  assert.ok(matchesGuessYears(playable[0],{from:900,to:960}));
  assert.ok(!matchesGuessYears(playable[0],{from:1800,to:2000}));checks++;
  // A growing corpus beyond 10,000 must not block all game starts.
  for(let offset=0;offset<15022;offset+=250){
    const persons=Array.from({length:Math.min(250,15022-offset)},()=>[randomUUID(),'容量回归人物','published']);
    await connection.query('INSERT INTO person(id,name,status) VALUES ?',[persons]);
    await connection.query('INSERT INTO fact_claim(id,subject_table,subject_id,claim_text,source_id,status,field_path,note) VALUES ?',[persons.map(([pid])=>[randomUUID(),'person',pid,'容量回归事实',source,'published','description','原文：容量回归。'])]);
  }
  const largeCatalogue=await loadGuessCatalogue(db,AbortSignal.timeout(60000));
  assert.equal(largeCatalogue.length,15023);assert.equal(new Set(largeCatalogue.map(p=>p.id)).size,15023);checks++;
  // Database constraints protect stable IDs/endpoints and publication state even for offline tools.
  await assert.rejects(connection.execute('INSERT INTO person(id,name,status) VALUES(?,?,?)',[randomUUID(),'无效状态','invalid']));checks++;
  await assert.rejects(connection.execute('INSERT INTO person_event(id,person_id,event_id,role) VALUES(?,?,?,?)',[randomUUID(),published,randomUUID(),'参与']));checks++;
  await connection.rollback();db.rows=originalRows;
  assert.equal((await db.rows('SELECT COUNT(*) count FROM person'))[0].count,0);checks++;
  const actor='anon:'+randomBytes(32).toString('hex');
  const accepted=await Promise.all(Array.from({length:14},()=>db.consumeQuota(actor,'ask')));assert.equal(accepted.filter(Boolean).length,10);checks++;
  assert.equal(await db.consumeQuota(actor,'ask'),false);assert.equal((await db.rows("SELECT SUM(used) used FROM ai_gateway_quota WHERE actor='global' AND operation='ask'"))[0].used,10);checks++;
  await assert.rejects(db.consumeQuota('forged','ask'));checks++;
  console.log(`PASS: ${checks} native MySQL contracts; business fixtures rolled back; model calls=0`);
}finally{db.rows=originalRows;await connection.rollback();await connection.end();await db.onModuleDestroy();}
