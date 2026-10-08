import { Test } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import type { NestExpressApplication } from '@nestjs/platform-express';
import { createClient } from '@supabase/supabase-js';
import request from 'supertest';
import { AskController } from './ask.controller';
import { AskService } from './ask.service';
import { AiAccessService } from './ai-access.service';
import { GatewayGuard } from '../../common/guards/gateway.guard';
import { SupabaseService } from '../supabase/supabase.service';
jest.mock('@supabase/supabase-js', () => ({createClient:jest.fn()}));
describe('direct ECS AI HTTP admission and streaming',()=>{
  let app:NestExpressApplication, service:AskService, run:jest.SpyInstance, debit:jest.Mock;
  const origin='https://123.56.189.146';
  beforeEach(async()=>{
    debit=jest.fn().mockResolvedValue({data:true,error:null});
    (createClient as jest.Mock).mockImplementation((_url,key)=>key==='quota'
      ? {rpc:(name: string,args: unknown)=>({abortSignal:()=>debit(name,args)})}
      : {auth:{getClaims:jest.fn().mockResolvedValue({data:null,error:{name:'AuthInvalidJwtError'}})}});
    const config=new ConfigService({SUPABASE_URL:'https://project.supabase.co',SUPABASE_ANON_KEY:'public',HISTREE_QUOTA_KEY:'quota',HISTREE_GATEWAY_SECRET:'a'.repeat(64),HISTREE_ASK_ENABLED:'true',DEEPSEEK_API_KEY:'fixture'});
    service=new AskService(config,{} as SupabaseService);
    run=jest.spyOn(service,'run').mockImplementation(async(ticket,_signal,emit)=>{
      emit({type:'conversation',conversation:ticket.token});
      emit({type:'result',answer:'fixture answer',citations:[],insufficientEvidence:true});
      ticket.session.busy=false;
    });
    const module=await Test.createTestingModule({controllers:[AskController],providers:[GatewayGuard,AiAccessService,{provide:ConfigService,useValue:config},{provide:AskService,useValue:service}]}).compile();
    app=module.createNestApplication<NestExpressApplication>({rawBody:true});await app.init();
  });
  afterEach(async()=>{await app.close();});
  const post=()=>request(app.getHttpServer()).post('/api/v1/ask').set('Origin',origin);
  async function session(){return(await request(app.getHttpServer()).post('/api/v1/ask/session').set('Origin',origin).expect(201)).body.token as string;}
  it('returns local status without calling database or model',async()=>{
    await request(app.getHttpServer()).get('/api/v1/ask/status').expect(200).expect('Cache-Control','no-store');
    expect(debit).not.toHaveBeenCalled();expect(run).not.toHaveBeenCalled();
  });
  it('issues local signed sessions and streams an actor-bound answer without a service key in the browser',async()=>{
    const token=await session();
    const response=await post().set('x-histree-anonymous',token).send({question:'fixture question'}).expect(200).expect('Content-Type',/application\/x-ndjson/);
    const events=response.text.trim().split('\n').map((s:string)=>JSON.parse(s));
    expect(events.map((e:{type:string})=>e.type)).toEqual(['conversation','result']);
    expect(run).toHaveBeenCalledTimes(1);expect(debit).toHaveBeenCalledTimes(2);
    const other=await session();
    await post().set('x-histree-anonymous',other).set('x-histree-actor','anon:'+token.split('.')[0]).send({question:'followup fixture',conversation:events[0].conversation}).expect(403);
    expect(run).toHaveBeenCalledTimes(1);
  });
  it('uses the ask quota even when Express matches a mixed-case URL',async()=>{
    const token=await session();
    await request(app.getHttpServer()).post('/API/V1/ASK/').set('Origin',origin).set('x-histree-anonymous',token).send({question:'fixture question'}).expect(200);
    expect(debit).toHaveBeenLastCalledWith('consume_ai_gateway_quota',expect.objectContaining({p_operation:'ask'}));
  });
  it('rejects unauthenticated/spoofed, malformed and oversized requests without invoking a model',async()=>{
    await post().set('x-histree-actor','user:forged').send({question:'fixture'}).expect(401);
    const token=await session();
    await post().set('x-histree-anonymous',token).set('Authorization','Bearer forged').send({question:'fixture'}).expect(401);
    await post().set('x-histree-anonymous',token).send({question:'a'.repeat(17000)}).expect(413);
    await post().set('x-histree-anonymous',token).set('Content-Type','application/json').send('{broken').expect(400);
    await request(app.getHttpServer()).post('/api/v1/ask/session').set('Origin','https://attacker.example').expect(403);
    expect(run).not.toHaveBeenCalled();expect(debit).toHaveBeenCalledTimes(1);
  });
  it('refuses model admission when quota rejects or the database is unavailable',async()=>{
    const token=await session();
    debit.mockResolvedValue({data:false,error:null});await post().set('x-histree-anonymous',token).send({question:'fixture'}).expect(429);
    debit.mockResolvedValue({data:null,error:{message:'unavailable'}});await post().set('x-histree-anonymous',token).send({question:'fixture'}).expect(503);
    expect(run).not.toHaveBeenCalled();
  });
});
