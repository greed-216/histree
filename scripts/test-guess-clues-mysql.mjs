/** Actual MySQL lease/cache and Nest HTTP regression. Disposable database only. */
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {randomUUID,randomBytes} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
const require=createRequire(new URL('../apps/api/package.json',import.meta.url));require('reflect-metadata');
const {ConfigService}=require('@nestjs/config'),{Module}=require('@nestjs/common'),{NestFactory}=require('@nestjs/core');
const {createConnection}=require('mysql2/promise');
const {MysqlService}=require('./dist/modules/mysql/mysql.service.js');
const {GuessService}=require('./dist/modules/ask/guess.service.js');
const {GuessController}=require('./dist/modules/ask/guess.controller.js');
const {GuessBankService}=require('./dist/modules/ask/guess-bank.js');
const {GuessGameLibrary}=require('./dist/modules/ask/guess-game-library.js');
const {GuessClueStore}=require('./dist/modules/ask/guess-clue-store.js');
const {GuessClueSetsService}=require('./dist/modules/ask/guess-clue-sets.service.js');
const {GuessClueGameService}=require('./dist/modules/ask/guess-clue-game.service.js');
const {GuessClueController}=require('./dist/modules/ask/guess-clue.controller.js');
const {AiAccessService}=require('./dist/modules/ask/ai-access.service.js');
const {GatewayGuard}=require('./dist/common/guards/gateway.guard.js');
const {loadClueProfile}=require('./dist/modules/ask/guess-clues.js');
const env=process.env;assert.match(env.MYSQL_DATABASE||'',/^histree_test_[a-z0-9_]+$/);assert(['127.0.0.1','localhost'].includes(env.MYSQL_HOST));
const config=new ConfigService({...env,HISTREE_GATEWAY_SECRET:'test-only-clue-game-signing-secret-32-chars',HISTREE_ALLOW_ANONYMOUS:'true'});
const db=new MysqlService(config),conn=await createConnection({host:env.MYSQL_HOST,port:Number(env.MYSQL_PORT||3306),user:env.MYSQL_USER,password:env.MYSQL_PASSWORD,database:env.MYSQL_DATABASE,charset:'utf8mb4'});
const a={id:randomUUID(),name:'合成甲'},b={id:randomUUID(),name:'合成乙'};
let modelCalls=0,checks=0,app,sharedApp;
const imported=[];
const clues=['我曾远离家乡，前往另一座城市。','我在地方任职，后来整理过文献。','我与友人共同经历过一次会面。','我留下过后人继续阅读的作品。','我的作品写过河流与山川。','我的代表作记录了故乡的风物。'].map(text=>({text,explanation:'仅用于独立测试的合成通识解释。'}));
const agent={available:()=>true,run:async()=>{modelCalls++;await new Promise(r=>setTimeout(r,40));return {clues}}};
try{
 const [existing]=await conn.execute('SELECT COUNT(*) n FROM person');assert.equal(Number(existing[0].n),0);
 // One canonical person with NO fact claims; one game-only person with NO canonical record.
 await conn.execute("INSERT INTO person(id,name,status,aliases,birth_year,death_year) VALUES(?,?,'published',JSON_ARRAY(?),701,762)",[a.id,a.name,'测试别名']);
 await conn.execute("INSERT INTO guess_bank(person_id,difficulty) VALUES(?,'easy')",[a.id]);
 for(const p of [a,b])await conn.execute('INSERT INTO guess_character(id,canonical_person_id,name,aliases,era,birth_year,death_year,description,difficulty) VALUES(?,?,?,JSON_ARRAY(),?,?,?,?,?)',[p.id,p===a?a.id:null,p.name,'唐',701,762,'',p===a?'easy':'hard']);
 const store=new GuessClueStore(db),sets=new GuessClueSetsService(store,agent,db),service=new GuessClueGameService(db,store,sets,agent);
 const pa=await loadClueProfile(db,a.id,AbortSignal.timeout(10000));assert.equal(pa.person.canonical_person_id,a.id);checks++;
 const pb=await loadClueProfile(db,b.id,AbortSignal.timeout(10000));assert.equal(pb.person.canonical_person_id,null);checks++;
 assert.equal((await db.rows('SELECT COUNT(*) n FROM fact_claim'))[0].n,0);checks++;
 assert.equal((await store.candidates({difficulty:'easy',from:600,to:900},AbortSignal.timeout(10000))).length,1);
 assert.equal((await store.candidates({difficulty:'easy',from:960,to:1279},AbortSignal.timeout(10000))).length,0);checks++;
 await sets.ensure(pa,AbortSignal.timeout(10000));assert.equal(modelCalls,1);checks++;
 const access=new AiAccessService(config,db);
 class TestModule{}Module({controllers:[GuessClueController],providers:[GatewayGuard,{provide:GuessClueGameService,useValue:service},{provide:AiAccessService,useValue:access}]})(TestModule);
 app=await NestFactory.create(TestModule,{logger:false,rawBody:true});await app.listen(0,'127.0.0.1');const base=await app.getUrl();
 const actor=(await access.issueSession()).token,other=(await access.issueSession()).token;
 async function post(path,body,owner=actor,expected=201){const res=await fetch(base+'/api/v1/ask/guess/clues/'+path,{method:'POST',headers:{'content-type':'application/json','x-histree-anonymous':owner},body:JSON.stringify(body)});const result=await res.json();assert.equal(res.status,expected,JSON.stringify(result));return result;}
 const first=await post('start',{difficulty:'easy'});assert.equal(first.clues.length,1);assert(!first.person&&!first.evidence);assert(!JSON.stringify(first).includes(a.id));checks++;
 await post('feedback',{token:first.token,rating:'hard'},actor,400);
 await post('start',{difficulty:'easy',person_id:a.id},actor,400);await post('act',{token:first.token,action:'state'},other,403);checks++;
 const wrong=await post('act',{token:first.token,action:'guess',text:'另一个名字'});assert.equal(wrong.outcome,null);assert.equal(wrong.unlocked,1);checks++;
 const hint={token:first.token,action:'hint',expectedUnlocked:1};assert.equal((await post('act',hint)).clues.length,2);assert.equal((await post('act',hint)).clues.length,2);checks++;
 const won=await post('act',{token:first.token,action:'guess',text:'测试别名'});assert.equal(won.outcome,'won');assert.equal(won.unlocked,2);assert.equal(won.clues.length,6);assert.equal(won.person.id,a.id);checks++;
 const rated=await post('feedback',{token:first.token,rating:'right'});assert.equal(rated.rating,'right');
 assert.equal((await post('feedback',{token:first.token,rating:'hard'})).rating,'right');
 const duplicate=await post('start',{difficulty:'easy'});await post('act',{token:duplicate.token,action:'guess',text:'另一个人'});await post('act',{token:duplicate.token,action:'reveal'});
 assert.equal((await post('feedback',{token:duplicate.token,rating:'hard'})).rating,'right');
 const [votes]=await conn.execute('SELECT * FROM guess_clue_feedback WHERE person_id=?',[a.id]);assert.equal(votes.length,1);checks++;
 const hash=v=>createHash('sha256').update(v).digest('hex');
 const rate=(revision,who,rating)=>db.rateGuessClue({person_id:a.id,revision,knowledge_revision:1,clue_revision:votes[0].clue_revision,game_hash:hash('game:'+who+':'+revision),actor_hash:hash('actor:'+who),rating,guesses:1,unlocked:2,outcome:'revealed'},AbortSignal.timeout(15000));
 await Promise.all([...Array.from({length:9},(_,i)=>rate(1,'hard-'+i,'hard')),...Array.from({length:2},(_,i)=>rate(1,'right-'+i,'right'))]);
 let [level]=await conn.execute('SELECT difficulty,difficulty_revision,easy_votes,right_votes,hard_votes FROM guess_character WHERE id=?',[a.id]);assert.equal(level[0].difficulty,'hard');assert.equal(level[0].difficulty_revision,2);assert.equal(level[0].hard_votes,0);checks++;
 assert.equal((await db.rows('SELECT difficulty FROM guess_bank WHERE person_id=?',[a.id]))[0].difficulty,'easy');checks++;
 await rate(1,'late','hard');assert.equal((await db.rows('SELECT hard_votes FROM guess_character WHERE id=?',[a.id]))[0].hard_votes,0);checks++;
 await Promise.all(Array.from({length:12},(_,i)=>rate(2,'hard-'+i,'easy')));
 [level]=await conn.execute('SELECT difficulty,difficulty_revision FROM guess_character WHERE id=?',[a.id]);assert.equal(level[0].difficulty,'easy');assert.equal(level[0].difficulty_revision,3);checks++;

 const samples=[];
 for(let i=0;i<12;i++){const start=performance.now();const g=await post('start',{difficulty:'easy'});samples.push(performance.now()-start);await post('act',{token:g.token,action:'reveal'});}
 assert.equal(modelCalls,1);checks++;
 const freshSets=new GuessClueSetsService(new GuessClueStore(db),agent,db);await freshSets.ensure(pa,AbortSignal.timeout(10000));assert.equal(modelCalls,1);checks++;
 await Promise.all([sets.ensure(pb,AbortSignal.timeout(10000)),freshSets.ensure(pb,AbortSignal.timeout(10000))]);assert.equal(modelCalls,2);checks++;
 const hard=await post('start',{difficulty:'hard'});await post('act',{token:hard.token,action:'hint',expectedUnlocked:1});const reveal=await post('act',{token:hard.token,action:'reveal'});assert.equal(reveal.person.id,null);assert.equal(reveal.person.name,b.name);assert.equal(modelCalls,2);assert.equal(reveal.evidence[0].kind,'general_knowledge');assert(!reveal.evidence[0].id);assert.equal((await post('feedback',{token:hard.token,rating:'hard'})).rating,'hard');checks++;
 const oldToken=randomBytes(32).toString('hex'),nextToken=randomBytes(32).toString('hex');
 await conn.execute("UPDATE guess_clue_set SET status='generating',clues=NULL,lease_token=?,lease_until=DATE_SUB(UTC_TIMESTAMP(6),INTERVAL 1 SECOND) WHERE person_id=?",[oldToken,b.id]);
 assert.equal((await store.claim(pb,nextToken,AbortSignal.timeout(10000))).lease_token,nextToken);
 assert.equal((await store.complete(pb,oldToken,clues,AbortSignal.timeout(10000))).affectedRows,0);assert.equal((await store.complete(pb,nextToken,clues,AbortSignal.timeout(10000))).affectedRows,1);checks++;
 const active=await post('start',{difficulty:'easy'});await conn.execute('UPDATE guess_character SET knowledge_revision=knowledge_revision+1 WHERE id=?',[a.id]);
 const updated=await loadClueProfile(db,a.id,AbortSignal.timeout(10000));assert.notEqual(updated.revision,pa.revision);assert.equal(await sets.ready(updated,AbortSignal.timeout(10000)),null);await post('act',{token:active.token,action:'state'},actor,410);checks++;
 await store.claim(updated,oldToken,AbortSignal.timeout(10000));await store.fail(updated,oldToken,AbortSignal.timeout(10000));assert.equal((await store.claim(updated,nextToken,AbortSignal.timeout(10000))).status,'failed');checks++;
 // Question-mode ratings cannot overwrite clue-mode classification.
 await conn.execute("UPDATE guess_bank SET difficulty='hard' WHERE person_id=?",[a.id]);assert.equal((await store.candidates({difficulty:'easy'},AbortSignal.timeout(10000))).length,1);checks++;
 await conn.execute("UPDATE person SET status='draft' WHERE id=?",[a.id]);assert.equal((await store.candidates({difficulty:'hard'},AbortSignal.timeout(10000))).length,1);await assert.rejects(loadClueProfile(db,a.id,AbortSignal.timeout(10000)));checks++;

 const starter=JSON.parse(readFileSync(new URL('../games/guess/starter-clues.json',import.meta.url),'utf8'));
 for(const p of starter.characters.filter(p=>p.canonical_person_id)){
  imported.push(p);
  await conn.execute("INSERT INTO person(id,name,aliases,courtesy_name,era,birth_year,death_year,description,status) VALUES(?,?,?,?,?,?,?,?,'published')",[p.id,p.name,JSON.stringify(p.aliases||[]),p.courtesy_name||null,p.era,p.birth_year??null,p.death_year??null,p.description||'']);
  await conn.execute('INSERT INTO guess_bank(person_id,difficulty) VALUES(?,?)',[p.id,p.difficulty]);
 }
 const runImport=()=>execFileSync(process.execPath,[new URL('./prepare-guess-clues.mjs',import.meta.url).pathname,'--apply','--import',new URL('../games/guess/characters.json',import.meta.url).pathname,'--seed',new URL('../games/guess/starter-clues.json',import.meta.url).pathname,'--limit','1'],{env:{...process.env,HISTREE_ASK_ENABLED:'false'},maxBuffer:4*1024*1024});
 // Remove the synthetic easy person from the batch, so --limit never selects an intentionally stale profile.
 await conn.execute('UPDATE guess_character SET enabled=0 WHERE id=?',[a.id]);
 runImport();
 assert.equal((await db.rows("SELECT COUNT(*) n FROM guess_clue_set WHERE status='ready' AND person_id IN ("+starter.characters.map(()=>'?').join(',')+')',starter.characters.map(p=>p.id)))[0].n,starter.characters.length);checks++;

 const library=new GuessGameLibrary(db,new GuessBankService(db),sets),sharedCatalogue=await library.catalogue(AbortSignal.timeout(30000));
 const cluePeople=[...await store.candidates({difficulty:'easy'},AbortSignal.timeout(10000)),...await store.candidates({difficulty:'hard'},AbortSignal.timeout(10000))];
 assert.deepEqual(sharedCatalogue.map(p=>p.id).sort(),cluePeople.map(p=>p.id).sort());checks++;
 let judgedPerson,questionCalls=0;
 const questionAgent={available:()=>true,run:async input=>{questionCalls++;judgedPerson=input.person;assert(input.claims.some(c=>c.kind==='general_knowledge'&&c.id.startsWith('knowledge:')));return {verdict:'unknown',claims:[]}}};
 const sharedQuestion=new GuessService(db,questionAgent,new GuessBankService(db),library);
 class SharedModule{}Module({controllers:[GuessController],providers:[GatewayGuard,{provide:GuessService,useValue:sharedQuestion},{provide:AiAccessService,useValue:access}]})(SharedModule);
 sharedApp=await NestFactory.create(SharedModule,{logger:false,rawBody:true});await sharedApp.listen(0,'127.0.0.1');const sharedBase=await sharedApp.getUrl(),sharedActor=(await access.issueSession()).token;
 const postQuestion=async(path,body)=>{const res=await fetch(sharedBase+'/api/v1/ask/guess/'+path,{method:'POST',headers:{'content-type':'application/json','x-histree-anonymous':sharedActor},body:JSON.stringify(body)});const data=await res.json();assert.equal(res.status,201,JSON.stringify(data));return data};
 const q=await postQuestion('start',{difficulty:'easy',from:1368,to:1912});assert.equal(questionCalls,0);assert(!q.person&&!q.evidence);checks++;
 const answer=await postQuestion('act',{token:q.token,action:'question',text:'你有过官场或科举方面的经历吗？'});assert.equal(answer.turns[0].answer,'不清楚');assert.equal(questionCalls,1);checks++;
 const complete=await postQuestion('act',{token:q.token,action:'guess',text:judgedPerson.name});assert.equal(complete.outcome,'won');assert.equal(complete.person.id,null);assert(complete.evidence.every(e=>e.kind==='general_knowledge'));checks++;
 assert.equal((await postQuestion('feedback',{token:q.token,rating:'right'})).rating,'right');
 assert.equal((await postQuestion('feedback',{token:q.token,rating:'hard'})).rating,'right');
 const qVotes=await db.rows('SELECT * FROM guess_question_feedback WHERE person_id=?',[judgedPerson.id]);assert.equal(qVotes.length,1);assert.equal((await db.rows('SELECT COUNT(*) n FROM guess_clue_feedback WHERE person_id=?',[judgedPerson.id]))[0].n,0);checks++;
 await Promise.all(Array.from({length:12},(_,i)=>db.rateGuessCharacterQuestion({person_id:judgedPerson.id,revision:1,knowledge_revision:1,clue_revision:qVotes[0].clue_revision,actor_hash:hash('q-actor:'+i),game_hash:hash('q-game:'+i),rating:'hard',guesses:1,unlocked:1,outcome:'revealed'},AbortSignal.timeout(15000))));
 const questionLevel=(await db.rows('SELECT difficulty,question_difficulty,question_revision FROM guess_character WHERE id=?',[judgedPerson.id]))[0];assert.equal(questionLevel.difficulty,'easy');assert.equal(questionLevel.question_difficulty,'hard');assert.equal(questionLevel.question_revision,2);checks++;
 await sharedApp.close();sharedApp=undefined;
 const preserve=starter.characters.find(p=>p.difficulty==='easy');
 await conn.execute("UPDATE guess_character SET difficulty='hard',difficulty_revision=2,vote_clue_revision=? WHERE id=?",[hash('preserve-player-classification'),preserve.id]);
 runImport();assert.equal((await db.rows('SELECT difficulty FROM guess_character WHERE id=?',[preserve.id]))[0].difficulty,'hard');checks++;
 for(const p of starter.characters)await conn.execute('DELETE FROM guess_character WHERE id=?',[p.id]);
 samples.sort((a,b)=>a-b);console.log(JSON.stringify({status:'passed',environment:'isolated native MySQL 8 / signed Nest HTTP / no historical facts required',checks,modelCalls,easyWarmStarts:samples.length,p50Ms:Math.round(samples[5]),p95Ms:Math.round(samples[11])}));
}finally{
 await sharedApp?.close();
 await app?.close();
 const starterPath=new URL('../games/guess/starter-clues.json',import.meta.url);
 for(const p of JSON.parse(readFileSync(starterPath,'utf8')).characters)await conn.execute('DELETE FROM guess_character WHERE id=?',[p.id]);
 for(const p of imported)await conn.execute('DELETE FROM person WHERE id=?',[p.id]);
 for(const p of [a,b])await conn.execute('DELETE FROM guess_character WHERE id=?',[p.id]);
 await conn.execute('DELETE FROM person WHERE id=?',[a.id]);await conn.end();await db.onModuleDestroy();
}
