import { ForbiddenException, HttpException, Injectable, ServiceUnavailableException, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { createHash, createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
@Injectable()
export class AiAccessService {
  private readonly auth: SupabaseClient;
  private readonly quota: SupabaseClient | null;
  private readonly verified = new Map<string, { actor: string; expires: number }>();
  constructor(private readonly config: ConfigService) {
    const url = config.get<string>('SUPABASE_URL') || 'http://127.0.0.1:54321';
    const options = {
      auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false },
      global: { fetch: (input: RequestInfo | URL, init?: RequestInit) => fetch(input, {
        ...init, signal: init?.signal ? AbortSignal.any([init.signal, AbortSignal.timeout(10000)]) : AbortSignal.timeout(10000),
      }) },
    };
    this.auth = createClient(url, config.get<string>('SUPABASE_ANON_KEY') || 'unconfigured', options);
    const key = config.get<string>('HISTREE_QUOTA_KEY');
    this.quota = key ? createClient(url, key, options) : null;
  }
  ready() { return !!this.quota && (this.config.get<string>('HISTREE_GATEWAY_SECRET') || '').length >= 32; }
  allowsAnonymous() { return this.config.get('HISTREE_ALLOW_ANONYMOUS') !== 'false'; }
  checkOrigin(origin: unknown) {
    const configured = this.config.get<string>('HISTREE_AI_ALLOWED_ORIGINS');
    const origins = (configured || 'https://123.56.189.146,https://histree.wiki,https://greed-216.github.io')
      .split(',').map(s => s.trim()).filter(Boolean);
    if (origin !== undefined && (typeof origin !== 'string' || !origins.includes(origin)))
      throw new ForbiddenException('不允许此来源访问');
  }
  private secret() {
    const secret = this.config.get<string>('HISTREE_GATEWAY_SECRET') || '';
    if (secret.length < 32) throw new ServiceUnavailableException('业务入口尚未配置');
    return secret;
  }
  private signature(payload: string) {
    return createHmac('sha256', this.secret()).update(`histree-anonymous:${payload}`).digest();
  }
  anonymousActor(token: unknown) {
    if (typeof token !== 'string' || !/^[a-f0-9]{64}\.[0-9]{10}\.[a-f0-9]{64}$/.test(token))
      throw new UnauthorizedException('匿名会话已过期，请刷新后重试');
    const [id, expiry, signature] = token.split('.');
    const now = Date.now() / 1000;
    if (Number(expiry) <= now || Number(expiry) > now + 86460
      || !timingSafeEqual(this.signature(`${id}.${expiry}`), Buffer.from(signature, 'hex')))
      throw new UnauthorizedException('匿名会话已过期，请刷新后重试');
    return `anon:${id}`;
  }
  async userActor(authorization: unknown) {
    if (typeof authorization !== 'string' || !/^Bearer \S+$/.test(authorization))
      throw new UnauthorizedException('登录凭据无效');
    const token = authorization.slice(7), cacheKey = createHash('sha256').update(token).digest('hex');
    const now = Date.now();
    for (const [key, value] of this.verified) if (value.expires <= now) this.verified.delete(key);
    const cached = this.verified.get(cacheKey);
    if (cached) return cached.actor;
    let result;
    try { result = await this.auth.auth.getClaims(token); }
    catch { throw new ServiceUnavailableException('登录验证暂不可用，请稍后重试'); }
    if (result.error && ((result.error.status || 0) >= 500 || result.error.name.includes('Retryable')))
      throw new ServiceUnavailableException('登录验证暂不可用，请稍后重试');
    const claims = result.data?.claims;
    if (result.error || !claims || !uuid.test(claims.sub) || claims.role !== 'authenticated'
      || !Number.isFinite(claims.exp) || claims.exp * 1000 <= Date.now())
      throw new UnauthorizedException('登录已过期，请重新登录');
    const actor = `user:${claims.sub}`;
    if (this.verified.size < 2048) this.verified.set(cacheKey, { actor, expires: Math.min(claims.exp * 1000, now + 60000) });
    return actor;
  }
  async consumeQuota(actor: string, operation: 'ask' | 'guess' | 'session') {
    if (!this.quota) throw new ServiceUnavailableException('调用额度尚未配置');
    let result;
    try {
      result = await this.quota.rpc('consume_ai_gateway_quota', { p_actor: actor, p_operation: operation })
        .abortSignal(AbortSignal.timeout(10000));
    } catch { throw new ServiceUnavailableException('调用额度暂不可用，请稍后重试'); }
    if (result.error) throw new ServiceUnavailableException('调用额度暂不可用，请稍后重试');
    if (result.data !== true) throw new HttpException('已达到调用限额，请稍后再试', 429);
  }
  async issueSession() {
    if (!this.allowsAnonymous()) throw new UnauthorizedException('请先登录');
    this.secret();
    const id = randomBytes(32).toString('hex');
    await this.consumeQuota(`anon:${id}`, 'session');
    const expires = Math.floor(Date.now() / 1000) + 86400, payload = `${id}.${expires}`;
    return { token: `${payload}.${this.signature(payload).toString('hex')}`, expires };
  }
}
