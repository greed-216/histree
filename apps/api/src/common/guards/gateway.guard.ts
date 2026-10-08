import { CanActivate, ExecutionContext, HttpException, Injectable, NotFoundException, ServiceUnavailableException, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { randomUUID, timingSafeEqual } from 'node:crypto';
import type { Request, Response } from 'express';
import { AiAccessService } from '../../modules/ask/ai-access.service';
export type GatewayRequest = Request & { gatewayActor: string; rawBody?: Buffer };
@Injectable()
export class GatewayGuard implements CanActivate {
  constructor(private readonly config: ConfigService, private readonly access: AiAccessService) {}
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<GatewayRequest>();
    const response = context.switchToHttp().getResponse<Response>();
    response.setHeader('Cache-Control', 'no-store');
    response.setHeader('X-Histree-Request-Id', randomUUID());
    this.access.checkOrigin(request.headers.origin);
    if (Object.keys(request.query || {}).length) throw new NotFoundException('接口不存在');
    const supplied = request.headers['x-histree-gateway-key'];
    // Compatibility for the old trusted Edge gateway during rollout; never trust browser actor headers.
    if (supplied !== undefined) {
      const secret = this.config.get<string>('HISTREE_GATEWAY_SECRET');
      if (!secret || secret.length < 32) throw new ServiceUnavailableException('业务入口尚未配置');
      if (typeof supplied !== 'string' || Buffer.byteLength(supplied) !== Buffer.byteLength(secret)
        || !timingSafeEqual(Buffer.from(supplied), Buffer.from(secret)))
        throw new UnauthorizedException('服务凭据无效');
      const legacyId = request.headers['x-histree-request-id'];
      if (typeof legacyId === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(legacyId))
        response.setHeader('X-Histree-Request-Id', legacyId);
      if (request.method !== 'GET') {
        const actor = request.headers['x-histree-actor'];
        if (typeof actor !== 'string' || !/^(anon:[a-f0-9]{64}|user:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i.test(actor))
          throw new UnauthorizedException('缺少有效调用身份');
        request.gatewayActor = actor;
      }
      return true; // Legacy Edge already consumed the same shared quota.
    }
    if (request.method === 'GET') return true; // Status never invokes a model.
    const bytes = request.rawBody?.length ?? Buffer.byteLength(JSON.stringify(request.body ?? {}));
    const declared = Number(request.headers['content-length'] || 0);
    if (bytes > 16384 || declared > 16384) throw new HttpException('请求过长', 413);
    const path = request.path.toLowerCase().replace(/\/$/, '');
    const session = path === '/api/v1/ask/session';
    let actor: string | undefined;
    if (request.headers.authorization !== undefined) actor = await this.access.userActor(request.headers.authorization);
    if (session) {
      if (!this.access.allowsAnonymous()) throw new UnauthorizedException('请先登录');
      return true;
    }
    if (!actor) {
      if (!this.access.allowsAnonymous()) throw new UnauthorizedException('请先登录');
      actor = this.access.anonymousActor(request.headers['x-histree-anonymous']);
    }
    if (!(request.headers['content-type'] || '').toLowerCase().startsWith('application/json'))
      throw new HttpException('请使用 JSON 请求', 415);
    if (!request.body || typeof request.body !== 'object' || Array.isArray(request.body))
      throw new HttpException('无效请求', 400);
    await this.access.consumeQuota(actor, path === '/api/v1/ask' ? 'ask' : 'guess');
    if (request.aborted || response.destroyed) throw new HttpException('请求已取消', 408);
    request.gatewayActor = actor;
    return true;
  }
}
