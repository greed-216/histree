import { Test } from '@nestjs/testing';
import { ConfigService } from '@nestjs/config';
import type { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { AppModule } from './app.module';
import { MysqlService } from './modules/mysql/mysql.service';
describe('current application HTTP boundary',()=>{
 let app:INestApplication;
 const rows=jest.fn().mockResolvedValue([{alive:1}]);
 beforeAll(async()=>{
  const module=await Test.createTestingModule({imports:[AppModule]})
   .overrideProvider(ConfigService).useValue(new ConfigService({HISTREE_ASK_ENABLED:'false',HISTREE_GATEWAY_SECRET:'a'.repeat(64)}))
   .overrideProvider(MysqlService).useValue({enabled:true,rows,rpc:jest.fn(),getClient:()=>({rpc:async()=>({data:{items:[],has_more:false},error:null})})}).compile();
  app=module.createNestApplication();await app.init();
 });
 afterAll(async()=>{await app.close();});
 it('serves public bounded reads and reports readiness while AI is disabled',async()=>{
  await request(app.getHttpServer()).get('/api/v1/health').expect(200).expect({status:'ok',database:'mysql'});
  await request(app.getHttpServer()).get('/api/v1/people').expect(200).expect({items:[],has_more:false});
  await request(app.getHttpServer()).get('/api/v1/ask/status').expect(200).expect(r=>expect(r.body.available).toBe(false));
 });
 it('does not register removed administration or mutation endpoints',async()=>{
  for(const path of ['/api/v1/editorial/person','/api/v1/upload'])await request(app.getHttpServer()).get(path).expect(404);
  for(const path of ['/api/v1/people','/api/v1/event','/api/v1/relationships/person-relationships','/api/v1/upload'])await request(app.getHttpServer()).post(path).send({}).expect(404);
  await request(app.getHttpServer()).patch('/api/v1/event/11111111-1111-4111-8111-111111111111').send({}).expect(404);
  await request(app.getHttpServer()).delete('/api/v1/people/11111111-1111-4111-8111-111111111111').expect(404);
  await request(app.getHttpServer()).post('/api/v1/read/consume_ai_gateway_quota').send({}).expect(404);
 });
 it('returns sanitized 503 when the database fails',async()=>{
  rows.mockRejectedValueOnce(new Error('private details'));
  const response=await request(app.getHttpServer()).get('/api/v1/health').expect(503);expect(response.text).not.toContain('private details');
 });
});
