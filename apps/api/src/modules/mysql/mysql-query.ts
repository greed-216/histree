import { integer, MysqlResult, tables, visible } from './query-contracts';
import type { StructuredReadPort } from './storage-port';
/** Bounded read adapter for the few remaining fluent public queries. No write methods. */
export class MysqlQuery {
  private selection = '*';
  private conditions: string[] = [];
  private params: any[] = [];
  private orderings: string[] = [];
  private offset = 0;
  private size = 50;
  private cardinality = 'many';
  private counted = false;
  private signal?: AbortSignal;
  constructor(
    private db: StructuredReadPort,
    private table: string,
  ) {
    if (!tables.includes(table)) throw new Error('Invalid table');
  }
  select(selection = '*', options?: { count?: string }) {
    if (
      selection !== '*' &&
      selection !== '*, source:source_id(*)' &&
      !/^[a-z_]+(,[a-z_]+)*$/.test(selection)
    )
      throw new Error('Invalid selection');
    this.selection = selection;
    this.counted = options?.count === 'exact';
    return this;
  }
  private column(c: string) {
    if (!/^[a-z_]+$/.test(c)) throw new Error('Invalid column');
    return `r.\`${c}\``;
  }
  eq(c: string, v: any) {
    this.conditions.push(this.column(c) + '=?');
    this.params.push(v);
    return this;
  }
  lte(c: string, v: any) {
    this.conditions.push(this.column(c) + '<=?');
    this.params.push(v);
    return this;
  }
  or(expression: string) {
    const m = expression.match(
      /^end_year\.gte\.(-?\d+),and\(end_year\.is\.null,start_year\.eq\.(-?\d+)\)$/,
    );
    if (!m || m[1] !== m[2]) throw new Error('Unsupported filter');
    this.conditions.push(
      '(r.end_year>=? OR (r.end_year IS NULL AND r.start_year=?))',
    );
    this.params.push(Number(m[1]), Number(m[1]));
    return this;
  }
  order(c: string, options?: { ascending?: boolean }) {
    this.orderings.push(
      this.column(c) + (options?.ascending === false ? ' DESC' : ' ASC'),
    );
    return this;
  }
  range(start: number, end: number) {
    this.offset = integer(start, 0, 0, 5000000);
    this.size = integer(end - start + 1, 20, 1, 51);
    return this;
  }
  single() {
    this.cardinality = 'single';
    return this;
  }
  maybeSingle() {
    this.cardinality = 'maybe';
    return this;
  }
  abortSignal(s: AbortSignal) {
    this.signal = s;
    return this;
  }
  then<TResult1 = MysqlResult, TResult2 = never>(
    resolve?: ((value: MysqlResult) => TResult1 | PromiseLike<TResult1>) | null,
    reject?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | null,
  ): Promise<TResult1 | TResult2> {
    return this.run().then(resolve, reject);
  }
  private async run(): Promise<MysqlResult> {
    try {
      const projection = this.selection.includes('source:')
        ? 'r.*'
        : this.selection === '*'
          ? 'r.*'
          : this.selection
              .split(',')
              .map((c) => this.column(c))
              .join(',');
      const condition = [visible(this.table), ...this.conditions].join(' AND '),
        order = this.orderings.length ? this.orderings.join(',') : 'r.id';
      const rows = await this.db.rows(
        `SELECT ${projection} FROM \`${this.table}\` r WHERE ${condition} ORDER BY ${order} LIMIT ${this.size} OFFSET ${this.offset}`,
        this.params,
        this.signal,
      );
      if (this.selection.includes('source:') && rows.length) {
        const ids = [...new Set(rows.map((r) => r.source_id).filter(Boolean))];
        const sources = ids.length
          ? await this.db.rows(
              `SELECT * FROM source WHERE id IN (${ids.map(() => '?').join(',')})`,
              ids,
              this.signal,
            )
          : [];
        for (const r of rows)
          r.source = sources.find((s) => s.id === r.source_id) ?? null;
      }
      const count = this.counted
        ? Number(
            (
              await this.db.rows(
                `SELECT COUNT(*) count FROM \`${this.table}\` r WHERE ${condition}`,
                this.params,
                this.signal,
              )
            )[0].count,
          )
        : null;
      if (
        this.cardinality !== 'many' &&
        (rows.length > 1 || (this.cardinality === 'single' && !rows.length))
      )
        throw new Error('Unexpected cardinality');
      return {
        data:
          this.cardinality === 'many'
            ? await this.db.structure.enrich(rows, this.table)
            : (await this.db.structure.enrich(rows, this.table))[0] || null,
        error: null,
        count,
      };
    } catch {
      return { data: null, error: new Error('公开资料查询失败'), count: null };
    }
  }
}
