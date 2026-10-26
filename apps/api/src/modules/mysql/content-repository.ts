import {
  body,
  claimFingerprintSql,
  fields,
  id,
  integer,
  pattern,
  Row,
  tables,
  trim,
  visible,
  year,
} from './query-contracts';
import type { StructuredReadPort } from './storage-port';
export class ContentRepository {
  constructor(private readonly db: StructuredReadPort) {}
  async entry(value: string, signal?: AbortSignal) {
    for (const t of ['person', 'event']) {
      const r = await this.db.rows(
        `SELECT r.* FROM \`${t}\` r WHERE ${visible(t)} AND id=?`,
        [value],
        signal,
      );
      if (r.length)
        return { ...(await this.db.structure.enrich(r, t))[0], type: t };
    }
    return null;
  }
  async labels(items: Row[], table: string, signal?: AbortSignal) {
    const ids = new Set<string>();
    for (const r of items)
      for (const f of [
        'person_a',
        'person_b',
        'person_id',
        'event_id',
        'cause_event_id',
        'effect_event_id',
        'source_id',
        'subject_id',
      ])
        if (r[f]) ids.add(r[f]);
    const labels: Row = {};
    if (!ids.size) return labels;
    for (const t of tables.filter((t) => t !== 'fact_claim' && t !== 'topic')) {
      const rs = await this.db.rows(
        `SELECT r.* FROM \`${t}\` r WHERE ${visible(t)} AND id IN (${[...ids].map(() => '?').join(',')})`,
        [...ids],
        signal,
      );
      for (const r of rs)
        if (r.name || r.title) labels[r.id] = r.name || r.title;
      if (t === 'person_relationship')
        for (const r of rs)
          labels[r.id] =
            `${labels[r.person_a] || '人物'} —${r.relation_type}→ ${labels[r.person_b] || '人物'}`;
      if (t === 'person_event')
        for (const r of rs)
          labels[r.id] =
            `${labels[r.person_id] || '人物'} —${r.role}→ ${labels[r.event_id] || '事件'}`;
      if (t === 'event_causality')
        for (const r of rs)
          labels[r.id] =
            `${labels[r.cause_event_id] || '事件'} → ${labels[r.effect_event_id] || '事件'}`;
    }
    return labels;
  }
  async content(a: Row, signal?: AbortSignal) {
    const t = a.p_table,
      size = integer(a.p_limit, 20, 1, 50),
      page = integer(a.p_page, 0, 0, 100000);
    if (![...tables, 'nodes'].includes(t) || a.p_admin)
      throw new Error('Invalid public table');
    const q = String(a.p_query || '').trim();
    if (q.length > 200) throw new Error('Invalid query');
    const from = year(a.p_from),
      to = year(a.p_to);
    if (from !== null && to !== null && from > to)
      throw new Error('Invalid years');
    if (a.p_ids != null && (!Array.isArray(a.p_ids) || a.p_ids.length > 200))
      throw new Error('Invalid ids');
    if (t === 'source' && a.p_ids == null)
      throw new Error('Source list requires explicit ids');
    if (t === 'nodes') {
      const params: any[] = [],
        conditions = ["r.status='published'"];
      if (a.p_ids != null) {
        const ids = a.p_ids.map(id);
        conditions.push(
          ids.length ? `r.id IN (${ids.map(() => '?').join(',')})` : 'FALSE',
        );
        params.push(...ids);
      }
      let scope: string[] | null = null;
      if (a.p_topic != null) {
        if (typeof a.p_topic !== 'string' || a.p_topic.length > 200)
          throw new Error('Invalid topic');
        const topic = (
          await this.db.rows(
            "SELECT sections FROM topic WHERE slug=? AND status='published'",
            [a.p_topic],
            signal,
          )
        )[0];
        const sections = topic?.sections || [];
        scope =
          a.p_section == null
            ? [
                ...new Set<string>(
                  sections.flatMap((s: Row) => s.node_ids || []),
                ),
              ]
            : sections[integer(a.p_section, 0, 0, 100000)]?.node_ids || [];
        conditions.push(
          scope!.length
            ? `r.id IN (${scope!.map(() => '?').join(',')})`
            : 'FALSE',
        );
        params.push(...scope!);
      }
      if (q) {
        conditions.push(
          "LOWER(CONCAT_WS(' ',r.label,r.description,CAST(r.aliases AS CHAR),CAST(r.tags AS CHAR))) LIKE ? ESCAPE '!'",
        );
        params.push(pattern(q));
      }
      let order = 'r.created_at DESC,r.id';
      if (scope?.length && a.p_section != null) {
        order = `FIELD(r.id,${scope.map(() => '?').join(',')}),r.id`;
        params.push(...scope);
      }
      const matches = await this.db.rows(
        `SELECT r.id,r.kind FROM (SELECT id,status,created_at,'person' kind,name label,description,aliases,tags FROM person UNION ALL SELECT id,status,created_at,'event' kind,title label,description,NULL aliases,tags FROM event) r WHERE ${conditions.join(' AND ')} ORDER BY ${order} LIMIT ${size + 1} OFFSET ${size * page}`,
        params,
        signal,
      );
      const items: Row[] = [];
      for (const match of matches.slice(0, size)) {
        const r = (
          await this.db.rows(
            `SELECT * FROM \`${match.kind}\` WHERE id=? AND status='published'`,
            [match.id],
            signal,
          )
        )[0];
        if (r) items.push({ ...trim(r, match.kind), label: r.name || r.title });
      }
      return { items, has_more: matches.length > size, labels: {} };
    }
    const cond = [visible(t)],
      params: any[] = [];
    const add = (s: string, ...v: any[]) => {
      cond.push(s);
      params.push(...v);
    };
    if (a.p_ids != null) {
      const ids = a.p_ids.map(id);
      add(
        ids.length ? `r.id IN (${ids.map(() => '?').join(',')})` : 'FALSE',
        ...ids,
      );
    }
    let scope: string[] | null = null;
    if (a.p_topic != null) {
      if (typeof a.p_topic !== 'string' || a.p_topic.length > 200)
        throw new Error('Invalid topic');
      const topic = (
        await this.db.rows(
          "SELECT sections FROM topic WHERE slug=? AND status='published'",
          [a.p_topic],
          signal,
        )
      )[0];
      const sections = topic?.sections || [];
      scope =
        a.p_section == null
          ? [...new Set<string>(sections.flatMap((s: Row) => s.node_ids || []))]
          : sections[integer(a.p_section, 0, 0, 100000)]?.node_ids || [];
      add(
        scope!.length
          ? `r.id IN (${scope!.map(() => '?').join(',')})`
          : 'FALSE',
        ...scope!,
      );
    }
    if (t === 'topic' && a.p_node)
      add(
        "EXISTS(SELECT 1 FROM JSON_TABLE(r.sections,'$[*].node_ids[*]' COLUMNS(node CHAR(36) PATH '$')) jt WHERE jt.node=?)",
        id(a.p_node),
      );
    if (t === 'event') {
      if (a.p_dating === 'dated') add('r.start_year IS NOT NULL');
      if (a.p_dating === 'undated') add('r.start_year IS NULL');
      if (a.p_dating === 'estimated' || a.p_era) {
        const bounds = [
          'd.event_id=r.id',
          "d.review_state='reviewed'",
          `d.claim_sha256=${claimFingerprintSql('c', 'dating_source')}`,
          "c.subject_table='event'",
          'c.subject_id=r.id',
          visible('fact_claim', 'c'),
        ];
        const values: unknown[] = [];
        if (a.p_dating === 'estimated') {
          add('r.start_year IS NULL');
          bounds.push("d.precision_kind<>'unknown'");
        }
        if (from !== null || to !== null)
          bounds.push('(d.earliest_year IS NOT NULL OR d.latest_year IS NOT NULL)');
        if (from !== null) {
          bounds.push('(d.latest_year IS NULL OR d.latest_year>=?)');
          values.push(from);
        }
        if (to !== null) {
          bounds.push('(d.earliest_year IS NULL OR d.earliest_year<=?)');
          values.push(to);
        }
        if (a.p_era) {
          bounds.push('d.era_key=?');
          values.push(a.p_era);
        }
        add(
          `EXISTS(SELECT 1 FROM event_dating d JOIN fact_claim c ON c.id=d.claim_id JOIN source dating_source ON dating_source.id=c.source_id WHERE ${bounds.join(' AND ')})`,
          ...values,
        );
      }
      if (a.p_person)
        add(
          "EXISTS(SELECT 1 FROM person_event pe JOIN person p ON p.id=pe.person_id AND p.status='published' WHERE pe.event_id=r.id AND pe.person_id=? AND pe.status='published')",
          id(a.p_person),
        );
      if (from !== null)
        add(
          '(r.start_year IS NULL OR COALESCE(r.end_year,r.start_year)>=?)',
          from,
        );
      if (to !== null) add('(r.start_year IS NULL OR r.start_year<=?)', to);
    }
    if (t === 'fact_claim')
      for (const [arg, column] of [
        ['p_subject', 'subject_table'],
        ['p_subject_id', 'subject_id'],
        ['p_source', 'source_id'],
        ['p_claim', 'id'],
      ])
        if (a[arg] != null)
          add(
            `r.\`${column}\`=?`,
            arg === 'p_subject' ? String(a[arg]) : id(a[arg]),
          );
    if (q) {
      if (fields[t]) add(`${body(t)} LIKE ? ESCAPE '!'`, pattern(q));
      else if (t === 'fact_claim')
        add(
          "LOWER(CONCAT_WS(' ',LEFT(r.claim_text,120),r.citation)) LIKE ? ESCAPE '!'",
          pattern(q),
        );
      else if (t === 'source')
        add("LOWER(CONCAT_WS(' ',r.title)) LIKE ? ESCAPE '!'", pattern(q));
      else {
        const endpoints: Record<string, string[]> = {
          person_relationship: [
            'person',
            'person_a',
            'person',
            'person_b',
            'relation_type',
          ],
          person_event: ['person', 'person_id', 'event', 'event_id', 'role'],
          event_causality: [
            'event',
            'cause_event_id',
            'event',
            'effect_event_id',
            '',
          ],
        };
        const [left, lc, right, rc, role] = endpoints[t];
        const label = `CONCAT_WS(' ',(SELECT ${left === 'person' ? 'name' : 'title'} FROM \`${left}\` WHERE id=r.\`${lc}\`),${role ? 'r.' + role : "''"},(SELECT ${right === 'person' ? 'name' : 'title'} FROM \`${right}\` WHERE id=r.\`${rc}\`),r.description)`;
        add(`LOWER(${label}) LIKE ? ESCAPE '!'`, pattern(q));
      }
    }
    let order =
      t === 'event'
        ? 'r.start_year IS NULL,r.start_year,r.id'
        : 'r.created_at DESC,r.id';
    if (t !== 'event' && scope && a.p_section != null && scope.length) {
      order = `FIELD(r.id,${scope.map(() => '?').join(',')}),r.id`;
      params.push(...scope);
    }
    const items = await this.db.rows(
      `SELECT r.* FROM \`${t}\` r WHERE ${cond.join(' AND ')} ORDER BY ${order} LIMIT ${size + 1} OFFSET ${page * size}`,
      params,
      signal,
    );
    const labels = await this.labels(items, t, signal);
    if (t === 'fact_claim' && items.length) {
      const sourceIds = [...new Set(items.map((r) => r.source_id))];
      const sources = await this.db.rows(
        `SELECT * FROM source WHERE id IN (${sourceIds.map(() => '?').join(',')})`,
        sourceIds,
        signal,
      );
      for (const r of items)
        r.source = sources.find((s) => s.id === r.source_id) || null;
    }
    return {
      items: (await this.db.structure.enrich(items.slice(0, size), t)).map(
        (r) => ({
          ...trim(r, t),
          label:
            r.name ||
            r.title ||
            (t === 'fact_claim'
              ? r.claim_text.slice(0, 120)
              : t === 'person_relationship'
                ? `${labels[r.person_a] || '人物'} —${r.relation_type}→ ${labels[r.person_b] || '人物'}`
                : t === 'person_event'
                  ? `${labels[r.person_id] || '人物'} —${r.role}→ ${labels[r.event_id] || '事件'}`
                  : `${labels[r.cause_event_id] || '事件'} → ${labels[r.effect_event_id] || '事件'}`),
        }),
      ),
      has_more: items.length > size,
      labels,
    };
  }
}
