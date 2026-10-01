import { BadRequestException } from '@nestjs/common';
import { TimelineService } from './timeline.service';
import { SupabaseService } from '../supabase/supabase.service';

describe('TimelineService', () => {
  const calls: Record<string, unknown[]> = {};
  let response = { data: [] as Array<{ id: string }>, error: null };
  const query = {
    select: jest.fn().mockReturnThis(), eq: jest.fn().mockReturnThis(),
    lte: jest.fn().mockReturnThis(), or: jest.fn().mockReturnThis(),
    order: jest.fn().mockReturnThis(),
    range: jest.fn((...args: unknown[]) => { calls.range = args; return Promise.resolve(response); }),
  };
  const client = { from: jest.fn(() => query), rpc: jest.fn() };
  const service = new TimelineService({ getClient: () => client } as unknown as SupabaseService);
  beforeEach(() => { jest.clearAllMocks(); response = { data: [], error: null }; });
  it('uses a published-only overlap query and bounded page with a lookahead row', async () => {
    response.data = Array.from({ length: 21 }, (_, i) => ({ id: String(i) }));
    const result = await service.getTimeline({ year: '-1', page: '2' });
    expect(query.eq).toHaveBeenCalledWith('status', 'published');
    expect(query.lte).toHaveBeenCalledWith('start_year', -1);
    expect(query.or).toHaveBeenCalledWith('end_year.gte.-1,and(end_year.is.null,start_year.eq.-1)');
    expect(calls.range).toEqual([40, 60]);
    expect(result.items).toHaveLength(20);
    expect(result.has_more).toBe(true);
  });
  it.each(['0','NaN','900.5','10001','900,end_year.is.null'])('rejects invalid year %s before querying', async year => {
    await expect(service.getTimeline({ year })).rejects.toBeInstanceOf(BadRequestException);
    expect(client.from).not.toHaveBeenCalled();
  });
  it('rejects invalid pagination', async () => {
    await expect(service.getTimeline({ year: '900', page: '-1' })).rejects.toBeInstanceOf(BadRequestException);
  });
  it('returns the shared database aggregation contract', async () => {
    client.rpc.mockResolvedValue({ data: { years: [] }, error: null });
    await expect(service.getOverview()).resolves.toEqual({ years: [] });
    expect(client.rpc).toHaveBeenCalledWith('timeline_overview');
  });
});
