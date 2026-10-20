// Local authoring preview: actual compiled controller/game, public snapshots and a durable FILE cache.
// Production always uses GuessClueStore/MySQL; this adapter is never included in the application image.
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,renameSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {randomBytes} from 'node:crypto';
import {execFile} from 'node:child_process';
const require=createRequire(new URL('../apps/api/package.json',import.meta.url));require('reflect-metadata');
const {Module,ServiceUnavailableException}=require('@nestjs/common'),{ConfigService}=require('@nestjs/config'),{NestFactory}=require('@nestjs/core');
const {AskController}=require('./dist/modules/ask/ask.controller.js'),{AskService}=require('./dist/modules/ask/ask.service.js');
const {AiAccessService}=require('./dist/modules/ask/ai-access.service.js'),{GatewayGuard}=require('./dist/common/guards/gateway.guard.js');
const {GuessClueController}=require('./dist/modules/ask/guess-clue.controller.js');
const {GuessClueGameService}=require('./dist/modules/ask/guess-clue-game.service.js');
const {GuessClueSetsService}=require('./dist/modules/ask/guess-clue-sets.service.js');
const {makeClueProfile,validateCachedClues,CLUE_VERSION}=require('./dist/modules/ask/guess-clues.js');
const {applyDifficultyRating}=require('./dist/modules/ask/guess-difficulty.js');
const {matchesGuessYears}=require('./dist/modules/ask/guess-catalogue.js');
const port=Number(process.env.PORT||5197),base=`http://127.0.0.1:${port}`;
const seedPath=process.env.HISTREE_CLUE_PREVIEW_SEED||resolve(new URL('../games/guess/starter-clues.json',import.meta.url).pathname);
const cachePath=process.env.HISTREE_CLUE_PREVIEW_CACHE||'/private/tmp/histree-general-clue-preview-cache.json';
const key=p=>`${p.person.id}:${p.revision}:${CLUE_VERSION}`;
const feedbackPath=process.env.HISTREE_CLUE_PREVIEW_FEEDBACK||'/private/tmp/histree-clue-preview-feedback.json';
const feedback=existsSync(feedbackPath)?JSON.parse(readFileSync(feedbackPath,'utf8')):{rounds:{},games:{},actors:{}};
const secretPath='/private/tmp/histree-clue-preview-secret';
if(!existsSync(secretPath))writeFileSync(secretPath,randomBytes(32).toString('hex'),{mode:0o600});
const localSecret=readFileSync(secretPath,'utf8').trim();
let profiles=[],eligible=[];
const rows=existsSync(cachePath)?JSON.parse(readFileSync(cachePath,'utf8')):{};
const flush=()=>{writeFileSync(cachePath+'.tmp',JSON.stringify(rows));renameSync(cachePath+'.tmp',cachePath)};
function refresh(){
 const seed=JSON.parse(readFileSync(seedPath,'utf8'));
 profiles=seed.characters.map(c=>{const round=feedback.rounds[c.id],difficulty=round?.difficulty||c.difficulty;
  return {...makeClueProfile({...c,game_difficulty:difficulty,difficulty_revision:round?.revision||1}),difficulty};});
 for(const entry of seed.entries){
  const profile=profiles.find(p=>p.person.id===entry.person_id&&p.revision===entry.profile_revision);
  if(profile&&entry.generator_version===CLUE_VERSION){validateCachedClues(entry.clues,profile);rows[key(profile)]={status:'ready',lease_token:null,clues:entry.clues};}
 }
 eligible=profiles.filter(p=>rows[key(p)]?.status==='ready');flush();
}
refresh();
const store={
 rate:async input=>{
  const person=profiles.find(p=>p.person.id===input.person_id)?.person;if(!person)throw Error('Unknown preview person');
  const current=feedback.rounds[input.person_id]||{difficulty:person.game_difficulty,revision:1,scope:null,counts:{easy:0,right:0,hard:0}};
  const actorKey=[input.person_id,input.clue_revision,input.revision,input.actor_hash].join(':');
  const existing=feedback.games[input.game_hash]||feedback.actors[actorKey];
  if(existing)return {rating:existing,difficulty:current.difficulty,revision:current.revision,moved:false};
  feedback.games[input.game_hash]=input.rating;feedback.actors[actorKey]=input.rating;
  let moved=false;
  if(current.revision===input.revision&&(person.knowledge_revision||1)===input.knowledge_revision){
    const counts=current.scope===input.clue_revision?current.counts:{easy:0,right:0,hard:0};
    const change=applyDifficultyRating(current.difficulty,counts,input.rating);moved=change.moved;
    current.difficulty=change.difficulty;current.counts=change.counts;current.scope=input.clue_revision;
    if(moved)current.revision++;
  }
  feedback.rounds[input.person_id]=current;
  writeFileSync(feedbackPath+'.tmp',JSON.stringify(feedback));renameSync(feedbackPath+'.tmp',feedbackPath);
  return {rating:input.rating,difficulty:current.difficulty,revision:current.revision,moved};
 },
 candidates:async filters=>{refresh();return eligible.filter(p=>p.difficulty===filters.difficulty&&matchesGuessYears({...p.person,activity:[...(p.person.activity||[]),...(p.person.period_from!=null&&p.person.period_to!=null?[{from:p.person.period_from,to:p.person.period_to}]:[])]},filters)).map(p=>({id:p.person.id}))},
 readyPeople:async()=>new Set(eligible.map(p=>p.person.id)),
 find:async p=>rows[key(p)]||null,
 claim:async(p,token)=>{const k=key(p);if(!rows[k])rows[k]={status:'generating',lease_token:token,clues:null};return rows[k]},
 complete:async(p,token,clues)=>{const k=key(p);if(rows[k]?.lease_token!==token)return {affectedRows:0};rows[k]={status:'ready',lease_token:null,clues};flush();return {affectedRows:1}},
 fail:async(p,token)=>{const k=key(p);if(rows[k]?.lease_token===token){rows[k]={status:'failed',lease_token:null,clues:null};flush()}},
};
const db={enabled:true,consumeQuota:async()=>true,rows:async(sql,args)=>{
 if(sql.includes('FROM guess_character c')){const p=profiles.find(p=>p.person.id===args?.[0]);return p?[p.person]:[];}
 throw Error('Preview adapter cannot execute arbitrary SQL');
}};
const agent={available:()=>true,run:async()=>{throw new ServiceUnavailableException('本地试玩仅使用已准备的通识线索。正式服务支持困难题首次生成。')}};
const sets=new GuessClueSetsService(store,agent,db),service=new GuessClueGameService(db,store,sets,agent);
const access=new AiAccessService(new ConfigService({HISTREE_GATEWAY_SECRET:localSecret,HISTREE_ALLOW_ANONYMOUS:'true',HISTREE_AI_ALLOWED_ORIGINS:base}),db);
class PreviewModule{}
Module({controllers:[GuessClueController,AskController],providers:[GatewayGuard,{provide:GuessClueGameService,useValue:service},{provide:AiAccessService,useValue:access},{provide:AskService,useValue:{status:()=>({available:false}),reserve:()=>{throw new ServiceUnavailableException('本地试玩未连接问史料模型。')}}}]})(PreviewModule);
const app=await NestFactory.create(PreviewModule,{logger:false,rawBody:true});
const express=app.getHttpAdapter().getInstance();
express.get('/api/v1/ask/guess/status',(_req,res)=>res.json({available:false}));
// Only public historical GET/read operations may be proxied. Never proxy model/game writes.
express.use((req,res,next)=>{
 if(!req.url.startsWith('/api/v1/')||req.url.startsWith('/api/v1/ask/'))return next();
 if(req.method!=='GET'&&!(req.method==='POST'&&req.url.startsWith('/api/v1/read/')))return next();
 const args=['--silent','--show-error','--max-time','20','--request',req.method,'--write-out','\n%{http_code}',new URL(req.url,'https://histree.wiki').href];
 if(req.method==='POST')args.push('--header','content-type: application/json','--data-binary','@-');
 const child=execFile('curl',args,{maxBuffer:16*1024*1024},(err,out)=>{if(res.destroyed)return;if(err){res.status(502).json({message:'公开资料暂时无法连接'});return}const split=out.lastIndexOf('\n');res.status(Number(out.slice(split+1))).type('json').send(out.slice(0,split))});
 child.stdin.on('error',()=>{});if(req.method==='POST')req.pipe(child.stdin);else child.stdin.end();
 res.on('close',()=>{if(!res.writableEnded)child.kill()});
});
const webRoot=resolve(new URL('../apps/web/dist/',import.meta.url).pathname);
const renderIndex=()=>readFileSync(resolve(webRoot,'index.html'),'utf8').replace('<body>',`<body><div style="padding:8px 16px;background:#ecefe7;color:#57695c;text-align:center;font:12px/1.8 sans-serif">本地试玩 · 通识题库（已缓存题目） · 正式服务尚未部署</div>`);
app.useStaticAssets(webRoot,{index:false});express.get(/^(?!\/api\/).*/,(_req,res)=>res.type('html').send(renderIndex()));
await app.listen(port,'127.0.0.1');console.log(`Clue mode preview: ${base}/ask?mode=guess`);
