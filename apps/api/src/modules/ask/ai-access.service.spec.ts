import { ConfigService } from '@nestjs/config';
import { createHmac } from 'node:crypto';
import { createClient } from '@supabase/supabase-js';
import { AiAccessService } from './ai-access.service';
jest.mock('@supabase/supabase-js', () => ({ createClient: jest.fn() }));
describe('direct ECS AI identity and shared quota', () => {
  const secret = 'a'.repeat(64), id = 'b'.repeat(64), user = '11111111-1111-4111-8111-111111111111';
  let claims: jest.Mock, debit: jest.Mock, service: AiAccessService;
  const config = (extra = {}) => new ConfigService({ SUPABASE_URL: 'https://project.supabase.co', SUPABASE_ANON_KEY: 'public', HISTREE_QUOTA_KEY: 'quota', HISTREE_GATEWAY_SECRET: secret, ...extra });
  const token = (expiry = Math.floor(Date.now()/1000)+3600, key = secret) => {
    const payload = `${id}.${expiry}`;
    return `${payload}.${createHmac('sha256',key).update(`histree-anonymous:${payload}`).digest('hex')}`;
  };
  beforeEach(() => {
    claims = jest.fn().mockResolvedValue({ data: { claims: { sub: user, role: 'authenticated', exp: Math.floor(Date.now()/1000)+3600 } }, error: null });
    debit = jest.fn().mockResolvedValue({ data: true, error: null });
    (createClient as jest.Mock).mockImplementation((_url, key) => key === 'quota'
      ? { rpc: jest.fn((name, args) => ({ abortSignal: () => debit(name,args) })) }
      : { auth: { getClaims: claims } });
    service = new AiAccessService(config());
  });
  it('preserves the Edge signed-token format and rejects tampering, expiry and key rotation', () => {
    expect(service.anonymousActor(token())).toBe(`anon:${id}`);
    for (const invalid of [undefined, 'spoofed', token().replace(/^b/,'c'),token(Math.floor(Date.now()/1000)-1),token(Math.floor(Date.now()/1000)+90000),token(undefined,'c'.repeat(64))])
      expect(() => service.anonymousActor(invalid)).toThrow('匿名会话');
  });
  it('issues bounded signed sessions only after the shared session quota succeeds', async () => {
    const issued = await service.issueSession();
    expect(service.anonymousActor(issued.token)).toMatch(/^anon:[a-f0-9]{64}$/);
    expect(debit).toHaveBeenCalledWith('consume_ai_gateway_quota', expect.objectContaining({p_operation:'session'}));
    debit.mockResolvedValue({ data: false, error: null });
    await expect(service.issueSession()).rejects.toMatchObject({status:429});
  });
  it('fails closed on quota outage and when its dedicated server credential is missing', async () => {
    debit.mockResolvedValue({ data: null, error: {message:'database unavailable'} });
    await expect(service.consumeQuota(`anon:${id}`,'ask')).rejects.toMatchObject({status:503});
    const unconfigured = new AiAccessService(config({HISTREE_QUOTA_KEY:undefined}));
    expect(unconfigured.ready()).toBe(false);
    await expect(unconfigured.consumeQuota(`anon:${id}`,'ask')).rejects.toMatchObject({status:503});
  });
  it('validates Supabase JWT claims, caches briefly and never treats invalid user credentials as anonymous', async () => {
    expect(await service.userActor('Bearer valid')).toBe(`user:${user}`);
    expect(await service.userActor('Bearer valid')).toBe(`user:${user}`);
    expect(claims).toHaveBeenCalledTimes(1);
    claims.mockResolvedValue({ data:null,error:{name:'AuthInvalidJwtError'} });
    await expect(service.userActor('Bearer forged')).rejects.toMatchObject({status:401});
    await expect(service.userActor('Basic invalid')).rejects.toMatchObject({status:401});
  });
  it('bounds token cache lifetime by JWT expiry and rejects service-role/expired tokens', async () => {
    claims.mockResolvedValue({data:{claims:{sub:user,role:'service_role',exp:Date.now()/1000+3600}},error:null});
    await expect(service.userActor('Bearer service-key')).rejects.toMatchObject({status:401});
    claims.mockResolvedValue({data:{claims:{sub:user,role:'authenticated',exp:Date.now()/1000-1}},error:null});
    await expect(service.userActor('Bearer expired')).rejects.toMatchObject({status:401});
  });
  it('revalidates login claims after the short cache window', async () => {
    const now = Date.now(), clock = jest.spyOn(Date, 'now').mockReturnValue(now);
    try {
      await service.userActor('Bearer cached');
      clock.mockReturnValue(now + 61000);
      await service.userActor('Bearer cached');
      expect(claims).toHaveBeenCalledTimes(2);
    } finally { clock.mockRestore(); }
  });
  it('retains login-only mode and restricts browser origins', async () => {
    const loginOnly = new AiAccessService(config({HISTREE_ALLOW_ANONYMOUS:'false'}));
    await expect(loginOnly.issueSession()).rejects.toMatchObject({status:401});
    service.checkOrigin('https://123.56.189.146');
    expect(() => service.checkOrigin('https://attacker.example')).toThrow('来源');
  });
});
