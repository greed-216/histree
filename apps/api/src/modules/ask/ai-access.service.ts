import { MysqlService } from '../mysql/mysql.service';
import { ForbiddenException, HttpException, Injectable, ServiceUnavailableException, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';

@Injectable()
export class AiAccessService {
  constructor(private readonly config: ConfigService, private readonly mysql: MysqlService) {}
  ready() { return this.mysql.enabled && (this.config.get<string>('HISTREE_GATEWAY_SECRET') || '').length >= 32; }
  allowsAnonymous() { return this.config.get('HISTREE_ALLOW_ANONYMOUS') !== 'false'; }
  checkOrigin(origin: unknown) {
    const configured = this.config.get<string>('HISTREE_AI_ALLOWED_ORIGINS');
    const origins = (configured || 'https://123.56.189.146,https://histree.wiki')
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
  async consumeQuota(actor: string, operation: 'ask' | 'guess' | 'session') {
    let accepted;
    try { accepted = await this.mysql.consumeQuota(actor, operation); }
    catch { throw new ServiceUnavailableException('调用额度暂不可用，请稍后重试'); }
    if (!accepted) throw new HttpException('已达到调用限额，请稍后再试', 429);
  }
  async issueSession() {
    if (!this.allowsAnonymous()) throw new UnauthorizedException('匿名访问已关闭');
    this.secret();
    const id = randomBytes(32).toString('hex');
    await this.consumeQuota(`anon:${id}`, 'session');
    const expires = Math.floor(Date.now() / 1000) + 86400, payload = `${id}.${expires}`;
    return { token: `${payload}.${this.signature(payload).toString('hex')}`, expires };
  }
}
