/** Local preview only. Uses existing server credentials without writing them to files or client bundles. */
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {randomBytes} from 'node:crypto';
import {parseEnv} from 'node:util';
import {fileURLToPath} from 'node:url';
const root=resolve(fileURLToPath(new URL('..',import.meta.url)));
const require=createRequire(resolve(root,'apps/api/package.json'));
const source=process.env.HISTREE_LOCAL_CONFIG_ROOT || root;
for(const [name,allowed] of [['apps/api/.env',['DEEPSEEK_API_KEY','HISTREE_MODEL']],['.env.migration.local',['MYSQL_HOST','MYSQL_PORT','MYSQL_DATABASE','MYSQL_USER','MYSQL_PASSWORD']]]) {
 const config=parseEnv(readFileSync(resolve(source,name),'utf8'));
 for(const key of allowed)if(config[key])process.env[key]=config[key];
}
process.env.PORT='3008';
process.env.HISTREE_DATABASE='mysql';
process.env.HISTREE_ASK_ENABLED='true';
process.env.HISTREE_GATEWAY_SECRET=randomBytes(32).toString('hex');
process.env.HISTREE_AI_ALLOWED_ORIGINS='http://127.0.0.1:5178';
const {NestFactory}=require('@nestjs/core');
const {AppModule}=require(resolve(root,'apps/api/dist/app.module.js'));
const app=await NestFactory.create(AppModule,{rawBody:true,logger:['warn','error']});
app.enableShutdownHooks();
await app.listen(3008,'127.0.0.1');
const webRequire=createRequire(resolve(root,'apps/web/package.json'));
const {preview}=await import(webRequire.resolve('vite'));
const server=await preview({root:resolve(root,'apps/web'),preview:{host:'127.0.0.1',port:5178,strictPort:true,proxy:{'/api/v1':'http://127.0.0.1:3008'}}});
console.log('Local preview: http://127.0.0.1:5178/people/3ddce59a-2d7a-5a32-8c6e-d09d330d167f');
console.log('Published history reads; local AI entry keeps signed anonymous admission and quotas. No publication or production configuration changes.');
for(const event of ['SIGTERM','SIGINT'])process.once(event,async()=>{await server.httpServer.close();await app.close();process.exit(0);});
