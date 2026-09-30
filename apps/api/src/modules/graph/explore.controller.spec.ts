import { BadRequestException, NotFoundException } from '@nestjs/common';
import { ExploreController } from './explore.controller';
import { SupabaseService } from '../supabase/supabase.service';

describe('ExploreController', () => {
  const id = '11111111-1111-1111-1111-111111111111';
  let rpc: jest.Mock;
  let controller: ExploreController;
  beforeEach(() => {
    rpc = jest
      .fn()
      .mockResolvedValue({ data: { items: [], has_more: false }, error: null });
    controller = new ExploreController({
      getClient: () => ({ rpc }),
    } as unknown as SupabaseService);
  });
  it('uses the anonymous RPC and the same normalized search contract as the static site', async () => {
    await controller.search({ q: ' 李弘茂 ', kind: 'person', page: '2' });
    expect(rpc).toHaveBeenCalledWith('search_entries', {
      p_query: '李弘茂',
      p_kind: 'person',
      p_page: 2,
      p_limit: 20,
    });
  });
  it('passes depth and years to bounded graph queries', async () => {
    await controller.graph(id, {
      mode: 'events',
      depth: '2',
      from: '900',
      to: '910',
    });
    expect(rpc).toHaveBeenCalledWith('graph_slice', {
      p_id: id,
      p_mode: 'events',
      p_depth: 2,
      p_from: 900,
      p_to: 910,
    });
  });
  it('fetches only the selected entry detail', async () => {
    await controller.entry(id);
    expect(rpc).toHaveBeenCalledWith('entry_detail', { p_id: id });
  });
  it('rejects malformed IDs, excessive budgets, and invalid filters before querying', async () => {
    await expect(controller.graph('bad', {})).rejects.toBeInstanceOf(
      BadRequestException,
    );
    await expect(controller.graph(id, { depth: '3' })).rejects.toBeInstanceOf(
      BadRequestException,
    );
    await expect(
      controller.graph(id, { from: '910', to: '900' }),
    ).rejects.toBeInstanceOf(BadRequestException);
    await expect(controller.search({ limit: '1000' })).rejects.toBeInstanceOf(
      BadRequestException,
    );
    expect(rpc).not.toHaveBeenCalled();
  });
  it('reports a missing or unpublished entry without silently substituting an empty graph', async () => {
    rpc.mockResolvedValueOnce({ data: null, error: null });
    await expect(controller.entry(id)).rejects.toBeInstanceOf(
      NotFoundException,
    );
  });
  it('propagates database failures', async () => {
    const error = new Error('query failed');
    rpc.mockResolvedValueOnce({ data: null, error });
    await expect(controller.search({})).rejects.toBe(error);
  });
});
