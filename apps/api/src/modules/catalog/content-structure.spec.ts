import {
  legacyEvidence,
  personReading,
  validateDating,
  type EventDating,
} from '@histree/shared-types';
import type { MysqlService } from '../mysql/mysql.service';
import { claimFingerprint } from '../mysql/query-contracts';
import { RevisionCache } from '../mysql/revision-cache';
import { SearchRepository } from '../mysql/search-repository';
import { PersonDirectory } from '../person/person-directory';
describe('Historical structure compatibility', () => {
  it('losslessly separates explicit notes and preserves unrecognized legacy text', () => {
    expect(legacyEvidence('原文：甲。；核对说明：身份待考')).toMatchObject({
      quote: '甲。',
      review: '身份待考',
      review_state: 'deferred',
    });
    expect(legacyEvidence('仅有旧说明')).toMatchObject({
      quote: '',
      review: '仅有旧说明',
      review_state: 'unparsed',
    });
  });
  it('separates explicit identity cautions without deleting uncertain material', () => {
    const reading = personReading(
      '元知枢密，1368年战死，未与御史大夫同名者强合。',
    );
    expect(reading.summary).toBe('元知枢密，1368年战死。');
    expect(reading.identity_notes.join('')).toContain('未与御史大夫同名者强合');
    expect(personReading('未与明军交战，退守城内。').identity_notes).toEqual(
      [],
    );
  });
  it('separates legacy identity bridge cautions without hiding historical bridge events', () => {
    expect(
      personReading('1288年西逃被擒送京，与早库春子无明确桥暂分。'),
    ).toMatchObject({
      summary: '1288年西逃被擒送京。',
      identity_notes: ['与早库春子无明确桥暂分。'],
      review_state: 'deferred',
    });
    expect(personReading('1357年任官守济宁，未证1355同名亲王。')).toMatchObject(
      {
        summary: '1357年任官守济宁。',
        identity_notes: ['未证1355同名亲王。'],
        review_state: 'deferred',
      },
    );
    expect(
      personReading('元知枢密，与1366平章转台官缺桥先分。').identity_notes,
    ).toHaveLength(1);
    expect(personReading('与敌军交战，因河道缺桥无法渡河。')).toMatchObject({
      summary: '与敌军交战，因河道缺桥无法渡河。',
      identity_notes: [],
    });
  });
  const estimate: EventDating = {
    id: '11111111-1111-4111-8111-111111111111',
    event_id: '22222222-2222-4222-8222-222222222222',
    claim_id: '33333333-3333-4333-8333-333333333333',
    earliest_year: 900,
    latest_year: 910,
    precision: 'range',
    basis: '同一条原文明示的界限',
    review_state: 'reviewed',
  };
  it('keeps dating bounds separate from event duration and requires evidence', () => {
    expect(validateDating(estimate)).toEqual(estimate);
    for (const changed of [
      { earliest_year: 0 },
      { latest_year: 899 },
      { basis: '' },
      { claim_id: '' },
      { precision: 'year' },
      { earliest_year: null },
    ])
      expect(() =>
        validateDating({ ...estimate, ...changed } as EventDating),
      ).toThrow();
  });
  it('invalidates derived interpretations when exact evidence or source changes', () => {
    const basis = {
      subject_table: 'event',
      subject_id: 'event',
      claim_text: '原义',
      source_id: 'source',
      citation: '卷一',
      note: '原文：\ufeff甲。',
      archive_url: 'https://example.test/fixed',
    };
    const fingerprint = claimFingerprint(basis);
    for (const key of Object.keys(basis))
      expect(
        claimFingerprint({
          ...basis,
          [key]: basis[key as keyof typeof basis] + '变更',
        }),
      ).not.toBe(fingerprint);
    expect(claimFingerprint({ ...basis })).toBe(fingerprint);
  });
  it('coalesces versioned reads and invalidates after a committed revision', async () => {
    let revision = 1;
    const db = {
      rows: jest.fn(async () => [{ revision }]),
    } as unknown as MysqlService;
    const cache = new RevisionCache(db),
      load = jest.fn(async () => ({ count: revision }));
    expect(
      await Promise.all([
        cache.read('overview', load),
        cache.read('overview', load),
      ]),
    ).toEqual([{ count: 1 }, { count: 1 }]);
    expect(load).toHaveBeenCalledTimes(1);
    revision++;
    expect(await cache.read('overview', load)).toEqual({ count: 2 });
    expect(load).toHaveBeenCalledTimes(2);
    const fail = jest.fn(async () => {
      throw new Error('unavailable');
    });
    await expect(cache.read('broken', fail)).rejects.toThrow();
    await expect(cache.read('broken', fail)).rejects.toThrow();
    expect(fail).toHaveBeenCalledTimes(2);
  });
  it('rejects malformed directory filters and cursors', async () => {
    const db = {
        cache: { revision: async () => '1' },
        rows: jest.fn(),
      } as unknown as MysqlService,
      dir = new PersonDirectory(db);
    for (const query of [
      { sort: 'bad' },
      { book: '../../x' },
      { page: '-1' },
      { cursor: 'not-json' },
    ])
      await expect(dir.list(query)).rejects.toMatchObject({ status: 400 });
    expect(db.rows).not.toHaveBeenCalled();
  });
  it('loads matched search details per kind rather than per result', async () => {
    const matches = Array.from({ length: 20 }, (_, i) => ({
      id: String(i),
      kind: 'person',
    }));
    const rows = jest
      .fn()
      .mockResolvedValueOnce(matches)
      .mockResolvedValueOnce(matches.map((m) => ({ ...m, name: '人物' })));
    const result = await new SearchRepository({
      rows,
    } as unknown as MysqlService).search({ p_query: '人物' });
    expect(result.items).toHaveLength(20);
    expect(rows).toHaveBeenCalledTimes(2);
    expect(rows.mock.calls[1][0]).toContain('id IN');
  });
});
