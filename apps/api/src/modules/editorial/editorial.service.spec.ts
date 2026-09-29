import type { SupabaseService } from '../supabase/supabase.service';
import { BadRequestException } from '@nestjs/common';
import { EditorialService } from './editorial.service';
const id = '11111111-1111-1111-1111-111111111008';
function fixture(status = 'published') {
  class Query {
    select = jest.fn((): Query => this);
    eq = jest.fn((): Query => this);
    maybeSingle = jest.fn(() =>
      Promise.resolve({
        data: { id, status } as { id: string; status: string } | null,
        error: null,
      }),
    );
    insert = jest.fn((): Query => this);
    single = jest.fn(() => Promise.resolve({ data: { id }, error: null }));
  }
  const query = new Query();
  const client = { from: jest.fn(() => query) };
  return {
    service: new EditorialService({
      getAdminClient: () => client,
      getClient: () => client,
    } as unknown as SupabaseService),
    query,
    client,
  };
}
describe('Editorial validation', () => {
  it('rejects arbitrary table access', async () => {
    const { service, client } = fixture();
    await expect(service.list('user_roles')).rejects.toBeInstanceOf(
      BadRequestException,
    );
    expect(client.from).not.toHaveBeenCalled();
  });
  it('rejects unsafe source URLs', async () => {
    await expect(
      fixture().service.save('source', {
        title: 'source',
        source_type: 'primary',
        url: 'javascript:alert(1)',
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });
  it('rejects malformed publication status', async () => {
    await expect(
      fixture().service.save('topic', { status: 'public' }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });
  it('rejects publishing a topic linked to a draft', async () => {
    await expect(
      fixture('draft').service.save('topic', {
        title: 'Topic',
        slug: 'test',
        description: 'Intro',
        status: 'published',
        sections: [{ heading: 'Read', body: '', node_ids: [id] }],
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });
  it('allows a draft topic to include a draft node', async () => {
    const { service, query } = fixture('draft');
    await service.save('topic', {
      title: 'Topic',
      slug: 'test',
      description: 'Intro',
      sections: [{ heading: 'Read', body: '', node_ids: [id] }],
    });
    expect(query.insert).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'draft' }),
    );
  });
  it('rejects evidence without a citation locator', async () => {
    const { service, query } = fixture();
    await expect(
      service.save('fact_claim', {
        subject_table: 'person',
        subject_id: id,
        field_path: 'biography',
        claim_text: 'Claim',
        source_id: id,
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
    expect(query.insert).not.toHaveBeenCalled();
  });
  it('rejects a claim attached to a missing subject', async () => {
    const { service, query } = fixture();
    query.maybeSingle.mockResolvedValue({ data: null, error: null });
    await expect(
      service.save('fact_claim', {
        subject_table: 'person',
        subject_id: id,
        field_path: 'biography',
        claim_text: 'Claim',
        source_id: id,
        citation: '卷一',
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });
  it('allows a complete relationship citation and defaults it to draft', async () => {
    const { service, query } = fixture();
    await service.save('fact_claim', {
      subject_table: 'person_relationship',
      subject_id: id,
      field_path: 'description',
      claim_text: 'Claim',
      source_id: id,
      citation: '卷一',
    });
    expect(query.insert).toHaveBeenCalledWith(
      expect.objectContaining({
        subject_table: 'person_relationship',
        status: 'draft',
      }),
    );
  });
});


describe('Public source index', () => {
  it('validates pagination and IDs before querying', async () => {
    const { service, client } = fixture();
    for (const [key, page] of [['bad', 0], [id, -1], [id, 1.5], [id, Infinity]] as const)
      await expect(service.source(key, page)).rejects.toBeInstanceOf(BadRequestException);
    expect(client.from).not.toHaveBeenCalled();
  });
  it('uses the public client and filters draft evidence with stable pagination', async () => {
    const q = { select: jest.fn(), eq: jest.fn(), order: jest.fn(), range: jest.fn(), single: jest.fn() };
    q.select.mockReturnValue(q); q.eq.mockReturnValue(q); q.order.mockReturnValue(q);
    q.single.mockResolvedValue({ data: { id, title: '史料' }, error: null });
    q.range.mockResolvedValue({ data: [{ id: 'claim' }], count: 121, error: null });
    const client = { from: jest.fn(() => q) };
    const admin = jest.fn(() => { throw new Error('must not use service credentials'); });
    const service = new EditorialService({ getClient: () => client, getAdminClient: admin } as unknown as SupabaseService);
    expect((await service.source(id, 1)).count).toBe(121);
    expect(q.eq).toHaveBeenCalledWith('status', 'published');
    expect(q.eq).toHaveBeenCalledWith('source_id', id);
    expect(q.order).toHaveBeenCalledWith('id');
    expect(q.range).toHaveBeenCalledWith(50, 99);
    expect(admin).not.toHaveBeenCalled();
  });
});
