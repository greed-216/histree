import { BadRequestException, ConflictException, NotFoundException } from '@nestjs/common';
import { RelationshipService } from './relationship.service';

type TableRows = Record<string, Array<Record<string, any>>>;

function createService(seed: TableRows) {
  const rows = structuredClone(seed);
  const client = {
    from: jest.fn((table: string) => createQuery(table, rows)),
  };
  const service = new RelationshipService({
    getClient: () => client,
    getAdminClient: () => client,
  } as any);

  return { service, client, rows };
}

function createQuery(table: string, rows: TableRows) {
  const state = {
    filters: [] as Array<{ column: string; value: any }>,
    payload: undefined as Record<string, any> | undefined,
    op: 'select' as 'select' | 'insert' | 'update' | 'delete',
  };

  const currentRows = () =>
    (rows[table] ?? []).filter((row) => state.filters.every((filter) => row[filter.column] === filter.value));

  const query: any = {
    select: jest.fn(() => query),
    order: jest.fn(() => Promise.resolve({ data: currentRows(), error: null })),
    eq: jest.fn((column: string, value: any) => {
      state.filters.push({ column, value });
      return query;
    }),
    maybeSingle: jest.fn(() => Promise.resolve({ data: currentRows()[0] ?? null, error: null })),
    single: jest.fn(() => {
      if (state.op === 'insert') {
        const row = { id: `${table}-${rows[table]?.length ?? 0}`, ...state.payload };
        rows[table] = [...(rows[table] ?? []), row];
        return Promise.resolve({ data: row, error: null });
      }

      if (state.op === 'update') {
        const existing = currentRows()[0];
        if (!existing) {
          return Promise.resolve({ data: null, error: { message: 'not found' } });
        }
        Object.assign(existing, state.payload);
        return Promise.resolve({ data: existing, error: null });
      }

      return Promise.resolve({ data: currentRows()[0] ?? null, error: null });
    }),
    insert: jest.fn((payload: Record<string, any>) => {
      state.op = 'insert';
      state.payload = payload;
      return query;
    }),
    update: jest.fn((payload: Record<string, any>) => {
      state.op = 'update';
      state.payload = payload;
      return query;
    }),
    delete: jest.fn(() => {
      state.op = 'delete';
      return query;
    }),
  };

  return query;
}

const baseRows: TableRows = {
  person: [
    { id: 'person-a', name: '管仲' },
    { id: 'person-b', name: '齐桓公' },
  ],
  event: [
    { id: 'event-a', title: '管仲改革' },
    { id: 'event-b', title: '葵丘会盟' },
  ],
  person_relationship: [],
  person_event: [],
  event_causality: [],
};

describe('RelationshipService', () => {
  it.each([
    ['父亲', '儿子'], ['儿子', '父亲'], ['母亲', '女儿'],
    ['养父', '养子'], ['兄长', '弟弟'], ['姐姐', '弟弟'],
    ['丈夫', '妻子'], ['主君', '臣属'], ['兄弟', '兄弟'], ['姻亲', '姻亲'],
  ])('rejects reversed duplicate %s / %s', async (existingType, relation_type) => {
    const { service, rows } = createService({
      ...baseRows,
      person_relationship: [{id: 'rel-1', person_a: 'person-a', person_b: 'person-b', relation_type: existingType}],
    });
    await expect(service.createPersonRelationship({
      person_a: 'person-b', person_b: 'person-a', relation_type,
    })).rejects.toBeInstanceOf(ConflictException);
    expect(rows.person_relationship).toHaveLength(1);
  });

  it('allows rewriting the same edge from the other endpoint', async () => {
    const { service, rows } = createService({
      ...baseRows,
      person_relationship: [{id: 'rel-1', person_a: 'person-a', person_b: 'person-b', relation_type: '父亲'}],
    });
    const updated = await service.updatePersonRelationship('rel-1', {
      person_a: 'person-b', person_b: 'person-a', relation_type: '儿子',
    });
    expect(updated).toMatchObject({id: 'rel-1', relation_type: '儿子'});
    expect(rows.person_relationship).toHaveLength(1);
  });

  it('keeps different facts between the same people', async () => {
    const { service } = createService({
      ...baseRows,
      person_relationship: [{id: 'rel-1', person_a: 'person-a', person_b: 'person-b', relation_type: '父亲'}],
    });
    await expect(service.createPersonRelationship({
      person_a: 'person-b', person_b: 'person-a', relation_type: '臣属',
    })).resolves.toMatchObject({relation_type: '臣属'});
  });

  it.each(['父子', '母子', '统属'])('rejects ambiguous role %s before writing', async relation_type => {
    const { service, client } = createService(baseRows);
    await expect(service.createPersonRelationship({person_a: 'person-a', person_b: 'person-b', relation_type})).rejects.toBeInstanceOf(BadRequestException);
    expect(client.from).not.toHaveBeenCalled();
  });

  it.each(['父亲', '儿子', '兄长', '弟弟', '丈夫', '妻子', '兄弟', '夫妻'])('preserves the submitted direction for %s', async relation_type => {
    const { service } = createService(baseRows);
    const row = await service.createPersonRelationship({person_a: 'person-a', person_b: 'person-b', relation_type});
    expect(row).toMatchObject({person_a: 'person-a', person_b: 'person-b', relation_type});
  });

  it('rejects duplicate person relationships', async () => {
    const { service } = createService({
      ...baseRows,
      person_relationship: [
        { id: 'rel-1', person_a: 'person-a', person_b: 'person-b', relation_type: '君臣' },
      ],
    });

    await expect(
      service.createPersonRelationship({
        person_a: 'person-a',
        person_b: 'person-b',
        relation_type: '君臣',
      }),
    ).rejects.toBeInstanceOf(ConflictException);
  });

  it('rejects event causality from an event to itself', async () => {
    const { service } = createService(baseRows);

    await expect(
      service.createEventCausality({
        cause_event_id: 'event-a',
        effect_event_id: 'event-a',
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('rejects person-event rows with dangling person ids', async () => {
    const { service } = createService(baseRows);

    await expect(
      service.createPersonEvent({
        person_id: 'missing-person',
        event_id: 'event-a',
        role: '主持改革',
      }),
    ).rejects.toBeInstanceOf(NotFoundException);
  });
});
