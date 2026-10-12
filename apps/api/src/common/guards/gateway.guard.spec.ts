import type { ExecutionContext } from '@nestjs/common';
import { GatewayGuard } from './gateway.guard';
import { AiAccessService } from '../../modules/ask/ai-access.service';
describe('signed anonymous AI request authentication', () => {
  const secret='a'.repeat(64), actor='anon:'+'b'.repeat(64);
  const request = (headers = {}, extra = {}) => ({headers,method:'POST',path:'/api/v1/ask',query:{},body:{question:'fixture'},...extra});
  const context = (req: unknown, destroyed=false) => ({ switchToHttp:()=>({ getRequest:()=>req,getResponse:()=>({setHeader:jest.fn(),destroyed}) }) }) as ExecutionContext;
  let access: {checkOrigin:jest.Mock;allowsAnonymous:jest.Mock;anonymousActor:jest.Mock;consumeQuota:jest.Mock}, guard:GatewayGuard;
  beforeEach(()=>{
    access={checkOrigin:jest.fn(),allowsAnonymous:jest.fn().mockReturnValue(true),anonymousActor:jest.fn().mockReturnValue(actor),consumeQuota:jest.fn().mockResolvedValue(undefined)};
    guard=new GatewayGuard(access as unknown as AiAccessService);
  });
  it('lets public status reads through without quota or identity network requests',async()=>{
    expect(await guard.canActivate(context(request({}, {method:'GET',path:'/api/v1/ask/status'})))).toBe(true);
    expect(access.consumeQuota).not.toHaveBeenCalled();
  });
  it('derives direct actor from the signed session and ignores browser identity headers',async()=>{
    const req=request({'content-type':'application/json','x-histree-anonymous':'signed','x-histree-actor':'user:forged'}) as ReturnType<typeof request>&{gatewayActor?:string};
    await guard.canActivate(context(req));expect(req.gatewayActor).toBe(actor);
    expect(access.consumeQuota).toHaveBeenCalledWith(actor,'ask');
  });
  it('rejects retired login even with a valid anonymous token',async()=>{
    await expect(guard.canActivate(context(request({'authorization':'Bearer bad','x-histree-anonymous':'valid','content-type':'application/json'})))).rejects.toMatchObject({status:401});
    expect(access.anonymousActor).not.toHaveBeenCalled();expect(access.consumeQuota).not.toHaveBeenCalled();
  });
  it('rejects forged service credentials and trusted calls without valid actor',async()=>{
    for(const headers of [{'x-histree-gateway-key':'bad'},{'x-histree-gateway-key':secret},{'x-histree-gateway-key':secret,'x-histree-actor':'user:forged'}])
      await expect(guard.canActivate(context(request(headers)))).rejects.toThrow();
  });
  it('rejects oversized raw bodies, invalid payloads, query strings and non-JSON business calls before debit',async()=>{
    for(const req of [request({'content-type':'application/json'},{rawBody:Buffer.alloc(16385)}),request({'content-type':'application/json'},{body:[]}),request({'content-type':'text/plain'}),request({}, {query:{upstream:'evil'}})])
      await expect(guard.canActivate(context(req))).rejects.toThrow();
    expect(access.consumeQuota).not.toHaveBeenCalled();
  });
  it('checks anonymous policy for the session route and refuses cancelled requests before model execution',async()=>{
    access.allowsAnonymous.mockReturnValue(false);
    await expect(guard.canActivate(context(request({}, {path:'/api/v1/ask/session'})))).rejects.toThrow('匿名访问');
    access.allowsAnonymous.mockReturnValue(true);
    await expect(guard.canActivate(context(request({'content-type':'application/json'}),true))).rejects.toMatchObject({status:408});
  });
});
