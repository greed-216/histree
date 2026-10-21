import { CanActivate, ExecutionContext, HttpException, Injectable, NotFoundException, UnauthorizedException } from '@nestjs/common';
import { randomUUID } from 'node:crypto';
import type { Request, Response } from 'express';
import { AiAccessService } from '../../modules/ask/ai-access.service';
export type GatewayRequest = Request & { gatewayActor: string; rawBody?: Buffer };
@Injectable()
export class GatewayGuard implements CanActivate {
  constructor(private readonly access: AiAccessService) {}
  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<GatewayRequest>();
    const response = context.switchToHttp().getResponse<Response>();
    response.setHeader('Cache-Control', 'no-store');
    response.setHeader('X-Histree-Request-Id', randomUUID());
    this.access.checkOrigin(request.headers.origin);
    if (Object.keys(request.query || {}).length) throw new NotFoundException('接口不存在');
    if (request.headers['x-histree-gateway-key'] !== undefined || request.headers.authorization !== undefined)
      throw new UnauthorizedException('旧网关和登录入口已关闭');
    if (request.method === 'GET') return true; // Status never invokes a model.
    const bytes = request.rawBody?.length ?? Buffer.byteLength(JSON.stringify(request.body ?? {}));
    const declared = Number(request.headers['content-length'] || 0);
    if (bytes > 16384 || declared > 16384) throw new HttpException('请求过长', 413);
    const path = request.path.toLowerCase().replace(/\/$/, '');
    const session = path === '/api/v1/ask/session';
    let actor: string | undefined;
    if (session) {
      if (!this.access.allowsAnonymous()) throw new UnauthorizedException('匿名访问已关闭');
      return true;
    }
    if (!actor) {
      if (!this.access.allowsAnonymous()) throw new UnauthorizedException('匿名访问已关闭');
      actor = this.access.anonymousActor(request.headers['x-histree-anonymous']);
    }
    if (!(request.headers['content-type'] || '').toLowerCase().startsWith('application/json'))
      throw new HttpException('请使用 JSON 请求', 415);
    if (!request.body || typeof request.body !== 'object' || Array.isArray(request.body))
      throw new HttpException('无效请求', 400);
    // These clue routes only read prepared sets or save feedback; they never invoke a model.
    // Keep the exemption explicit so other game endpoints retain their AI cost limits.
    const cachedClueRequest = request.method === 'POST' && [
      '/api/v1/ask/guess/clues/start',
      '/api/v1/ask/guess/clues/act',
      '/api/v1/ask/guess/clues/feedback',
    ].includes(path);
    if (!cachedClueRequest)
      await this.access.consumeQuota(actor, path === '/api/v1/ask' ? 'ask' : 'guess');
    if (request.aborted || response.destroyed) throw new HttpException('请求已取消', 408);
    request.gatewayActor = actor;
    return true;
  }
}
