import { ConfigService } from '@nestjs/config';
import type { ExecutionContext } from '@nestjs/common';
import { GatewayGuard } from './gateway.guard';
describe('Gateway service authentication', () => {
  const secret = 'a'.repeat(64);
  const context = (headers: Record<string, string>, method = 'POST') =>
    ({
      switchToHttp: () => ({ getRequest: () => ({ headers, method }) }),
    }) as ExecutionContext;
  it('fails closed when the server is unconfigured or a caller bypasses the gateway', () => {
    expect(() =>
      new GatewayGuard(new ConfigService()).canActivate(context({})),
    ).toThrow('尚未配置');
    const guard = new GatewayGuard(
      new ConfigService({ HISTREE_GATEWAY_SECRET: secret }),
    );
    for (const headers of [
      {},
      { 'x-histree-gateway-key': 'wrong' },
      { 'x-histree-gateway-key': secret },
      { 'x-histree-gateway-key': secret, 'x-histree-actor': 'user:forged' },
    ])
      expect(() => guard.canActivate(context(headers))).toThrow();
  });
  it('accepts service-authenticated status and actor-bound business requests', () => {
    const guard = new GatewayGuard(
      new ConfigService({ HISTREE_GATEWAY_SECRET: secret }),
    );
    expect(
      guard.canActivate(context({ 'x-histree-gateway-key': secret }, 'GET')),
    ).toBe(true);
    expect(
      guard.canActivate(
        context({
          'x-histree-gateway-key': secret,
          'x-histree-actor': 'anon:' + 'b'.repeat(64),
        }),
      ),
    ).toBe(true);
  });
});
