import {
  CanActivate,
  ExecutionContext,
  Injectable,
  ServiceUnavailableException,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { timingSafeEqual } from 'node:crypto';
import type { Request } from 'express';
export type GatewayRequest = Request & { gatewayActor: string };
@Injectable()
export class GatewayGuard implements CanActivate {
  constructor(private readonly config: ConfigService) {}
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest<GatewayRequest>();
    const secret = this.config.get<string>('HISTREE_GATEWAY_SECRET');
    if (!secret || secret.length < 32)
      throw new ServiceUnavailableException('业务入口尚未配置');
    const supplied = request.headers['x-histree-gateway-key'];
    if (
      typeof supplied !== 'string' ||
      Buffer.byteLength(supplied) !== Buffer.byteLength(secret) ||
      !timingSafeEqual(Buffer.from(supplied), Buffer.from(secret))
    )
      throw new UnauthorizedException('请通过网站业务入口访问');
    if (request.method !== 'GET') {
      const actor = request.headers['x-histree-actor'];
      if (
        typeof actor !== 'string' ||
        !/^(anon:[a-f0-9]{64}|user:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i.test(
          actor,
        )
      )
        throw new UnauthorizedException('缺少有效调用身份');
      request.gatewayActor = actor;
    }
    return true;
  }
}
