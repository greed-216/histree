// Actual SQL eligibility, durable research audit and streamed signed HTTP. Disposable DB only.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {randomUUID,randomBytes} from 'node:crypto';
const require=createRequire(new URL('../apps/api/package.json',import.meta.url)); require('reflect-metadata');
const {ConfigService}=require('@nestjs/config'),{Module}=require('@nestjs/common'),{NestFactory}=require('@nestjs/core');
const {MysqlService}=require('./dist/modules/mysql/mysql.service.js');
const {GuessClueResearch,UnsuitableGamePerson}=require('./dist/modules/ask/guess-clue-research.js');
const {GuessClueStore}=require('./dist/modules/ask/guess-clue-store.js');
const {GuessClueSetsService}=require('./dist/modules/ask/guess-clue-sets.service.js');
const {GuessClueGameService}=require('./dist/modules/ask/guess-clue-game.service.js');
const {GuessClueController}=require('./dist/modules/ask/guess-clue.controller.js');
const {GuessGameLibrary}=require('./dist/modules/ask/guess-game-library.js');
const {GuessBankService}=require('./dist/modules/ask/guess-bank.js');
const {GatewayGuard}=require('./dist/common/guards/gateway.guard.js');
const {AiAccessService}=require('./dist/modules/ask/ai-access.service.js');
const {loadClueProfile}=require('./dist/modules/ask/guess-clues.js');
assert.match(process.env.MYSQL_DATABASE||'',/^histree_test_[a-z0-9_]+$/);assert(['127.0.0.1','localhost'].includes(process.env.MYSQL_HOST));
const config=new ConfigService({...process.env,HISTREE_GATEWAY_SECRET:'isolated-research-signing-secret-32-chars',HISTREE_ALLOW_ANONYMOUS:'true'});
const db=new MysqlService(config),ids=[randomUUID(),randomUUID()],source=randomUUID(),claim=randomUUID();
const signal=()=>AbortSignal.timeout(20000),token=()=>randomBytes(32).toString('hex');let checks=0,calls=0,app,ownedLibrary=false;
const quotes=['合成沈甲离开家乡，前往江南。','合成沈甲在地方担任官职。','合成沈甲曾与知名诗人共事。','合成沈甲参与过一次地方防守。','合成沈甲写过描写山川的作品。','合成沈甲的代表作品被后人传读。'];
const texts=['我曾离开家乡，前往江南。','我曾在地方担任官职。','我与一位知名诗人共同任职。','我参与过一次地方防守。','我写过描写山川的作品。','我的代表作品被后人传读。'];
try{
 assert.equal((await db.rows("SELECT COUNT(*) n FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('library_book','library_section','library_paragraph')"))[0].n,0,'Test must own all library fixture tables');
 ownedLibrary=true;
 await db.execute('CREATE TABLE library_book(book_key VARCHAR(100) PRIMARY KEY,title VARCHAR(100),status VARCHAR(20))');
 await db.execute('CREATE TABLE library_section(id VARCHAR(100) PRIMARY KEY,title VARCHAR(100))');
 await db.execute('CREATE TABLE library_paragraph(id VARCHAR(100) PRIMARY KEY,book_key VARCHAR(100),section_id VARCHAR(100),kind VARCHAR(30),content LONGTEXT)');
 await db.execute("INSERT INTO library_book VALUES('research-fixture','合成史书','available')");await db.execute("INSERT INTO library_section VALUES('research-section','测试卷')");
 await db.execute("INSERT INTO library_paragraph VALUES('research-ready','research-fixture','research-section','body',?),('research-reject','research-fixture','research-section','body','合成沈乙曾任某地官职，仅见于一次记载。')",[quotes.join('\n')]);
 await db.execute("INSERT INTO person(id,name,status,aliases,birth_year,death_year) VALUES(?,'合成沈乙','published',JSON_ARRAY(),701,750)",[ids[1]]);
 await db.execute("INSERT INTO source(id,title,source_type) VALUES(?,'测试原文','primary')",[source]);
 await db.execute("INSERT INTO fact_claim(id,subject_table,subject_id,claim_text,source_id,status,field_path,note) VALUES(?,'person',?,'合成沈乙曾任某地官职',?,'published','description','原文：合成沈乙曾任某地官职，仅见于一次记载。')",[claim,ids[1],source]);
 await db.execute("INSERT INTO guess_bank(person_id,difficulty) VALUES(?,'hard')",[ids[1]]);
 for(const [i,id] of ids.entries())await db.execute("INSERT INTO guess_character(id,canonical_person_id,name,aliases,era,birth_year,death_year,description,difficulty,question_difficulty) VALUES(?,?,?,JSON_ARRAY(),'唐',701,750,'测试人物','hard','hard')",[id,i? id:null,i?'合成沈乙':'合成沈甲']);
 const store=new GuessClueStore(db),research=new GuessClueResearch(db);
 const agent={available:()=>true,run:async input=>{
  calls++;
  if(input.task==='clues')return {unavailable:true};
  assert(['research_clues','review_clues'].includes(input.task));
  const r=input.research;
  if(input.person.name==='合成沈甲'){
   const s=r.sources.find(s=>s.id==='library:research-ready');assert(s);
   return {decision:'ready',clues:texts.map((text,i)=>({text,angle:['origin','identity','relationship','experience','work','legacy'][i],explanation:quotes[i],evidence:[{sourceId:s.id,quote:quotes[i]}]}))};
  }
  const s=r.sources.find(s=>s.identityLinked);assert(s);assert(r.complete);
  return {decision:'unsuitable',reason:'仅能核实一次地方任官，没有六项有辨识度的事实。',identity:{sourceId:s.id,quote:'合成沈乙曾任某地官职'},facts:[{sourceId:s.id,quote:'合成沈乙曾任某地官职'}]};
 }};
 const sets=new GuessClueSetsService(store,agent,db,research),library=new GuessGameLibrary(db,new GuessBankService(db),sets);
 const before=await library.catalogue(signal());assert(before.some(p=>p.id===ids[1]));checks++;
 const p=await loadClueProfile(db,ids[0],signal());const progress=[];
 assert.equal((await sets.ensure(p,signal(),m=>progress.push(m))).length,6);assert(progress.some(m=>m.includes('补查')));checks++;
 assert.equal(calls,3);await new GuessClueSetsService(new GuessClueStore(db),agent,db,research).ensure(p,signal());assert.equal(calls,3);checks++;
 const cache=(await db.rows('SELECT status,provenance FROM guess_clue_set WHERE person_id=?',[ids[0]]))[0];assert.equal(cache.status,'ready');assert.equal(cache.provenance.assessment.decision,'ready');assert(cache.provenance.research.sources.some(s=>s.id==='library:research-ready'));checks++;
 const reject=await loadClueProfile(db,ids[1],signal());await assert.rejects(sets.ensure(reject,signal()),e=>e instanceof UnsuitableGamePerson);assert.equal(calls,6);checks++;
 assert.equal((await db.rows('SELECT enabled FROM guess_character WHERE id=?',[ids[1]]))[0].enabled,0);
 assert.equal((await store.candidates({difficulty:'hard'},signal())).some(p=>p.id===ids[1]),false);checks++;
 assert.equal((await library.catalogue(signal())).some(p=>p.id===ids[1]),false);await assert.rejects(library.material(before.find(p=>p.id===ids[1]),signal()),e=>e instanceof UnsuitableGamePerson);checks++;
 assert.equal((await db.rows('SELECT status FROM person WHERE id=?',[ids[1]]))[0].status,'published');assert.equal((await db.rows('SELECT COUNT(*) n FROM guess_bank WHERE person_id=?',[ids[1]]))[0].n,1);checks++;
 const rejected=(await db.rows('SELECT provenance,status,lease_token FROM guess_clue_set WHERE person_id=?',[ids[1]]))[0];assert.equal(rejected.status,'failed');assert.equal(rejected.lease_token,null);assert.equal(rejected.provenance.assessment.decision,'unsuitable');checks++;
 await db.execute('UPDATE guess_character SET knowledge_revision=2 WHERE id=?',[ids[0]]);const changed=await loadClueProfile(db,ids[0],signal()),owned=token();await store.claim(changed,owned,signal());
 assert.equal((await store.disable(changed,token(),{},signal())).affectedRows,0);await db.execute('UPDATE guess_character SET knowledge_revision=3 WHERE id=?',[ids[0]]);assert.equal((await store.disable(changed,owned,{},signal())).affectedRows,0);assert.equal((await db.rows('SELECT enabled FROM guess_character WHERE id=?',[ids[0]]))[0].enabled,1);checks++;
 await db.execute('UPDATE guess_character SET knowledge_revision=1 WHERE id=?',[ids[0]]);
 const access=new AiAccessService(config,db),service=new GuessClueGameService(db,store,sets,agent);
 class TestModule{}Module({controllers:[GuessClueController],providers:[GatewayGuard,{provide:GuessClueGameService,useValue:service},{provide:AiAccessService,useValue:access}]})(TestModule);
 app=await NestFactory.create(TestModule,{logger:false,rawBody:true});await app.listen(0,'127.0.0.1');const base=await app.getUrl(),actor=(await access.issueSession()).token;
 const response=await fetch(base+'/api/v1/ask/guess/clues/start',{method:'POST',headers:{'content-type':'application/json',accept:'application/x-ndjson','x-histree-anonymous':actor},body:JSON.stringify({difficulty:'hard'})});
 assert.match(response.headers.get('content-type'),/application\/x-ndjson/);const events=(await response.text()).trim().split('\n').map(JSON.parse);assert(events.some(e=>e.type==='status'));const result=events.find(e=>e.type==='result');assert.equal(result.state.clues.length,1);assert.equal(result.state.total,6);assert(!result.state.person&&!result.state.evidence);assert(!JSON.stringify(events).includes('合成沈甲'));assert.equal(calls,6);checks++;
 console.log(JSON.stringify({status:'passed',checks,environment:'isolated native MySQL + signed streamed Nest HTTP',syntheticModelCalls:calls,paidCalls:0}));
}finally{
 await app?.close();for(const id of ids)await db.execute('DELETE FROM guess_character WHERE id=?',[id]);await db.execute('DELETE FROM fact_claim WHERE id=?',[claim]);await db.execute('DELETE FROM person WHERE id=?',[ids[1]]);await db.execute('DELETE FROM source WHERE id=?',[source]);
 if(ownedLibrary)for(const name of ['library_paragraph','library_section','library_book'])await db.execute('DROP TABLE IF EXISTS '+name);await db.onModuleDestroy();
}
