import { ConfigService } from '@nestjs/config';
import { createHmac } from 'node:crypto';
import { AiAccessService } from './ai-access.service';
import { MysqlService } from '../mysql/mysql.service';
describe('signed anonymous admission with MySQL quota',()=>{
  const secret='a'.repeat(64),id='b'.repeat(64);
  let service:AiAccessService,debit:jest.Mock;
  const config=(extra={})=>new ConfigService({HISTREE_GATEWAY_SECRET:secret,...extra});
  const token=(expiry=Math.floor(Date.now()/1000)+3600,key=secret)=>{const p=`${id}.${expiry}`;return `${p}.${createHmac('sha256',key).update(`histree-anonymous:${p}`).digest('hex')}`;};
  beforeEach(()=>{debit=jest.fn().mockResolvedValue(true);service=new AiAccessService(config(),{enabled:true,consumeQuota:debit} as unknown as MysqlService);});
  it('rejects forged, expired, future and rotated-key sessions',()=>{
    expect(service.anonymousActor(token())).toBe(`anon:${id}`);
    for(const value of [undefined,'spoofed',token().replace(/^b/,'c'),token(Math.floor(Date.now()/1000)-1),token(Math.floor(Date.now()/1000)+90000),token(undefined,'c'.repeat(64))])expect(()=>service.anonymousActor(value)).toThrow('匿名会话');
  });
  it('issues a session only after transactional quota succeeds',async()=>{
    const issued=await service.issueSession();expect(service.anonymousActor(issued.token)).toMatch(/^anon:[a-f0-9]{64}$/);
    expect(debit).toHaveBeenCalledWith(expect.stringMatching(/^anon:/),'session');
    debit.mockResolvedValue(false);await expect(service.issueSession()).rejects.toMatchObject({status:429});
  });
  it('fails closed on quota failure and signing misconfiguration',async()=>{
    debit.mockRejectedValue(new Error('database outage'));await expect(service.consumeQuota(`anon:${id}`,'ask')).rejects.toMatchObject({status:503});
    const missing=new AiAccessService(config({HISTREE_GATEWAY_SECRET:''}),{enabled:true} as MysqlService);expect(missing.ready()).toBe(false);await expect(missing.issueSession()).rejects.toMatchObject({status:503});
  });
  it('restricts origins and allows operators to disable anonymous access',async()=>{
    service.checkOrigin('https://123.56.189.146');expect(()=>service.checkOrigin('https://attacker.example')).toThrow('来源');
    const disabled=new AiAccessService(config({HISTREE_ALLOW_ANONYMOUS:'false'}),{enabled:true} as MysqlService);await expect(disabled.issueSession()).rejects.toMatchObject({status:401});expect(debit).not.toHaveBeenCalled();
  });
});
