import {
  pageNumber,
  personReading,
  classifyPersonEra,
  personEraPeriods,
  isPersonEraPeriod,
} from '@histree/shared-types';
import { BadRequestException, ConflictException } from '@nestjs/common';
import { createHash } from 'node:crypto';
import type { Row } from '../mysql/query-contracts';
import { pattern } from '../mysql/query-contracts';
import type { ReadModelPort } from '../mysql/storage-port';
export class PersonDirectory {
  constructor(private readonly db: ReadModelPort) {}
  private async facetData() {
    return this.db.cache.read('person-facets-v2', async () => {
      const items = await this.db.rows(
        "SELECT era,faction,COUNT(*) count FROM person WHERE status='published' GROUP BY era,faction ORDER BY era,faction",
      );
      const books = await this.db.structure.optional(
        "SELECT book_key,title FROM library_book WHERE status='available' ORDER BY sort_order,book_key",
      );
      const periods = personEraPeriods.map((period) => ({
        ...period,
        count: 0,
        values: [] as Array<string | null>,
      }));
      for (const row of items) {
        for (const key of classifyPersonEra(row.era)) {
          const period = periods.find((period) => period.key === key)!;
          period.count += Number(row.count);
          if (!period.values.includes(row.era ?? null))
            period.values.push(row.era ?? null);
        }
      }
      return {
        periods,
        eras: [...new Set(items.map((r) => r.era).filter(Boolean))],
        factions: [...new Set(items.map((r) => r.faction).filter(Boolean))],
        books,
      };
    });
  }
  async facets() {
    const data = await this.facetData();
    return {
      ...data,
      periods: data.periods
        .filter((period) => period.count > 0)
        .map(({ values: _values, ...period }) => period),
    };
  }
  async list(query: Record<string, string> = {}) {
    const {
      era = '',
      period = '',
      faction = '',
      book = '',
      q = '',
      dating = '',
      sort = 'activity',
    } = query;
    if (
      [era, faction, book, period].some(
        (s) => typeof s !== 'string' || s.length > 128,
      ) ||
      (period && (!isPersonEraPeriod(period) || era)) ||
      q.length > 200 ||
      !['activity', 'name', 'recent'].includes(sort) ||
      !['', 'unknown', 'known'].includes(dating) ||
      (book && !/^[a-z0-9-]+$/.test(book))
    )
      throw new BadRequestException('无效的人物筛选');
    let page: number, limit: number;
    try {
      page = pageNumber(query.page);
      limit = pageNumber(query.limit, 20, 50);
      if (limit < 1) throw new Error();
    } catch {
      throw new BadRequestException('无效的人物分页');
    }
    const scope = createHash('sha256')
      .update(JSON.stringify({ era, period, faction, book, q, dating, sort }))
      .digest('hex');
    const revision = await this.db.cache.revision();
    const conditions = ["r.status='published'"],
      args: unknown[] = [];
    for (const [column, value] of [
      ['era', era],
      ['faction', faction],
    ])
      if (value) {
        conditions.push(`r.${column}=?`);
        args.push(value);
      }
    if (period) {
      const selected = (await this.facetData()).periods.find(
        (item) => item.key === period,
      )!;
      const values = selected.values.filter(
        (value): value is string => value !== null,
      );
      const tests = [];
      if (values.length) {
        tests.push(`r.era IN (${values.map(() => '?').join(',')})`);
        args.push(...values);
      }
      if (selected.values.includes(null)) tests.push('r.era IS NULL');
      conditions.push(tests.length ? '(' + tests.join(' OR ') + ')' : 'FALSE');
    }
    if (q) {
      conditions.push(
        "(r.name LIKE ? ESCAPE '!' OR CAST(r.aliases AS CHAR) LIKE ? ESCAPE '!')",
      );
      args.push(pattern(q), pattern(q));
    }
    if (book) {
      conditions.push(
        `EXISTS(SELECT 1 FROM fact_claim c JOIN library_source_link l ON l.source_id=c.source_id JOIN library_paragraph p ON p.id=l.paragraph_id JOIN source s ON s.id=c.source_id JOIN source_text st ON st.source_id=s.id AND st.archive_url=s.url AND st.archive_url_sha256=l.archive_url_sha256 AND st.content_sha256=l.snapshot_sha256 WHERE c.subject_table='person' AND c.subject_id=r.id AND c.status='published' AND p.book_key=?)`,
      );
      args.push(book);
    }
    const known = 'COALESCE(a.active_year,r.birth_year,r.death_year)';
    if (dating)
      conditions.push(`${known} IS ${dating === 'known' ? 'NOT ' : ''}NULL`);
    let cursor: Row | undefined;
    if (query.cursor) {
      try {
        if (query.cursor.length > 2048) throw new Error();
        cursor = JSON.parse(
          Buffer.from(query.cursor, 'base64url').toString('utf8'),
        );
        if (
          cursor?.scope !== scope ||
          typeof cursor?.id !== 'string' ||
          !/^[a-f0-9-]{36}$/.test(cursor.id) ||
          typeof cursor?.name !== 'string'
        )
          throw new Error();
      } catch {
        throw new BadRequestException('人物目录游标已失效');
      }
      if (cursor!.revision !== revision)
        throw new ConflictException('资料已更新，请刷新人物目录');
      if (sort === 'name') {
        conditions.push('(r.name,r.id)>(?,?)');
        args.push(cursor!.name, cursor!.id);
      } else if (sort === 'recent') {
        if (
          typeof cursor!.created_at !== 'string' ||
          !/^\d{4}-\d\d-\d\d[ T]/.test(cursor!.created_at)
        )
          throw new BadRequestException('无效的目录游标');
        conditions.push('(r.created_at<? OR (r.created_at=? AND r.id>?))');
        const at = cursor!.created_at.replace('T', ' ').replace(/\+00:00$/, '');
        args.push(at, at, cursor!.id);
      } else {
        if (
          ![0, 1].includes(cursor!.unknown) ||
          !Number.isInteger(cursor!.year)
        )
          throw new BadRequestException('无效的目录游标');
        conditions.push(
          `((${known} IS NULL),COALESCE(${known},0),r.name,r.id)>(?,?,?,?)`,
        );
        args.push(cursor!.unknown, cursor!.year, cursor!.name, cursor!.id);
      }
    }
    const order =
      sort === 'name'
        ? 'r.name,r.id'
        : sort === 'recent'
          ? 'r.created_at DESC,r.id'
          : `${known} IS NULL,COALESCE(${known},0),r.name,r.id`;
    const rows = await this.db.rows(
      `SELECT r.id,r.name,r.aliases,r.era,r.faction,r.native_place,r.birth_year,r.death_year,r.description,r.tags,r.image_url,r.created_at,${known} sort_year,CASE WHEN a.active_year IS NOT NULL THEN 'event' WHEN r.birth_year IS NOT NULL THEN 'birth' WHEN r.death_year IS NOT NULL THEN 'death' ELSE NULL END sort_year_basis
    FROM person r LEFT JOIN (SELECT pe.person_id,MIN(e.start_year) active_year FROM person_event pe JOIN event e ON e.id=pe.event_id AND e.status='published' WHERE pe.status='published' GROUP BY pe.person_id) a ON a.person_id=r.id
    WHERE ${conditions.join(' AND ')} ORDER BY ${order} LIMIT ${limit + 1} OFFSET ${cursor ? 0 : page * limit}`,
      args,
    );
    const items = rows.slice(0, limit).map((r) => ({
      ...r,
      id: String(r.id),
      name: String(r.name),
      sort_year: r.sort_year,
      created_at: r.created_at,
      type: 'person' as const,
      reading: personReading(r.description),
    }));
    const last = items.at(-1),
      has_more = rows.length > limit;
    const next_cursor =
      has_more && last
        ? Buffer.from(
            JSON.stringify({
              scope,
              revision,
              id: last.id,
              name: last.name,
              created_at: last.created_at,
              unknown: last.sort_year === null ? 1 : 0,
              year: last.sort_year ?? 0,
            }),
          ).toString('base64url')
        : null;
    return { items, has_more, next_cursor, revision };
  }
}
