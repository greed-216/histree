import { MysqlReadController } from './mysql.controller';
import { MysqlService } from './mysql.service';
import { AiAccessService } from '../ask/ai-access.service';
import { ConfigService } from '@nestjs/config';
describe('MySQL public worker boundary', () => {
  const id = '11111111-1111-4111-8111-111111111111';
  it('restricts read operations and refuses admin scope, unknown keys and excessive input', async () => {
    const rpc = jest.fn().mockResolvedValue({ items: [] });
    const controller = new MysqlReadController({
      enabled: true,
      rpc,
    } as unknown as MysqlService);
    await controller.read('entry_detail', { p_id: id });
    expect(rpc).toHaveBeenCalledWith(
      'entry_detail',
      { p_id: id },
      expect.any(AbortSignal),
    );
    for (const [name, args] of [
      ['consume_ai_gateway_quota', {}],
      ['content_page', { p_table: 'source' }],
      ['content_page', { p_table: 'person', p_admin: true }],
      ['entry_detail', { p_id: id, sql: 'SELECT *' }],
      ['ask_search', { p_keywords: ['x'.repeat(41)] }],
      ['ask_search', { p_keywords: ['秦'], p_from: 1, p_to: -1 }],
    ] as const)
      await expect(controller.read(name, args)).rejects.toThrow();
    expect(rpc).toHaveBeenCalledTimes(1);
  });
  it('uses only the MySQL quota service, rejects login and fails closed', async () => {
    const consumeQuota = jest.fn().mockResolvedValue(true);
    const service = new AiAccessService(
      new ConfigService({
        HISTREE_DATABASE: 'mysql',
        HISTREE_GATEWAY_SECRET: 'a'.repeat(64),
      }),
      { enabled: true, consumeQuota } as unknown as MysqlService,
    );
    expect(service.ready()).toBe(true);
    await service.consumeQuota('anon:' + 'b'.repeat(64), 'ask');
    expect(consumeQuota).toHaveBeenCalledTimes(1);
    consumeQuota.mockResolvedValue(false);
    await expect(
      service.consumeQuota('anon:' + 'b'.repeat(64), 'ask'),
    ).rejects.toMatchObject({ status: 429 });
    consumeQuota.mockRejectedValue(new Error('unavailable'));
    await expect(
      service.consumeQuota('anon:' + 'b'.repeat(64), 'ask'),
    ).rejects.toMatchObject({ status: 503 });
  });
});
