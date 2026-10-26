import { id, integer, Row, trim, visible, year } from './query-contracts';
import type { EntryReadPort } from './storage-port';
export class GraphRepository {
  constructor(private readonly db: EntryReadPort) {}
  private incidentSql(t: string) {
    const config: Record<string, string[]> = {
      person_relationship: [
        'person_a',
        'person_b',
        'relation_type',
        'r.description',
      ],
      person_event: ['person_id', 'event_id', 'role', 'NULL'],
      event_causality: [
        'cause_event_id',
        'effect_event_id',
        "'causes'",
        'r.description',
      ],
    };
    const [source, target, type, description] = config[t];
    return `SELECT r.id,'${t}' subject_table,r.${source} source,r.${target} target,${type.startsWith("'") ? type : 'r.' + type} type,${description} description FROM \`${t}\` r WHERE ${visible(t)}`;
  }
  async context(a: Row, signal?: AbortSignal) {
    const value = id(a.p_id),
      center = await this.db.entry(value, signal);
    if (!center) return null;
    const size = integer(a.p_limit, 20, 1, 50),
      page = integer(a.p_page, 0, 0, 100000);
    const edges = await this.db.rows(
      `SELECT * FROM (${['person_relationship', 'person_event', 'event_causality'].map((t) => this.incidentSql(t)).join(' UNION ALL ')}) edges WHERE source=? OR target=? ORDER BY subject_table,id LIMIT ${size + 1} OFFSET ${page * size}`,
      [value, value],
      signal,
    );
    const pageEdges = edges.slice(0, size),
      ids = [
        ...new Set<string>(pageEdges.flatMap((e) => [e.source, e.target])),
      ];
    const nodes = await this.nodes(ids, signal, false);
    return { center, nodes, edges: pageEdges, has_more: edges.length > size };
  }
  private async nodes(ids: string[], signal?: AbortSignal, compact = true) {
    if (!ids.length) return [];
    const nodes: Row[] = [];
    for (const t of ['person', 'event'])
      for (const r of await this.db.rows(
        `SELECT r.* FROM \`${t}\` r WHERE ${visible(t)} AND id IN (${ids.map(() => '?').join(',')})`,
        ids,
        signal,
      ))
        nodes.push(
          compact
            ? this.graphNode(r, t)
            : t === 'person'
              ? { ...trim(r), references: r.references, type: t }
              : { ...r, type: t },
        );
    return nodes.sort((x, y) => x.id.localeCompare(y.id));
  }
  private graphNode(r: Row, t: string) {
    return t === 'person'
      ? {
          id: r.id,
          type: t,
          name: r.name,
          era: r.era,
          description: r.description?.slice(0, 600) ?? null,
        }
      : {
          id: r.id,
          type: t,
          title: r.title,
          start_year: r.start_year,
          end_year: r.end_year,
          description: r.description?.slice(0, 600) ?? null,
        };
  }
  async graph(a: Row, signal?: AbortSignal) {
    const value = id(a.p_id),
      entry = await this.db.entry(value, signal);
    if (!entry) return null;
    const depth = integer(a.p_depth, 1, 1, 2),
      mode = a.p_mode || 'people',
      from = year(a.p_from),
      to = year(a.p_to);
    if (
      !['people', 'events'].includes(mode) ||
      (from !== null && to !== null && from > to)
    )
      throw new Error('Invalid graph');
    const visited = new Set([value]),
      seen = new Set<string>(),
      edges: Row[] = [];
    let frontier = [value],
      truncated = false;
    for (let level = 0; level < depth && frontier.length; level++) {
      const t = mode === 'people' ? 'person_relationship' : 'person_event',
        args: any[] = [...frontier, ...frontier];
      let sql = `SELECT * FROM (${this.incidentSql(t)}) edges WHERE (source IN (${frontier.map(() => '?').join(',')}) OR target IN (${frontier.map(() => '?').join(',')}))`;
      if (mode === 'events' && (from !== null || to !== null)) {
        sql += ' AND EXISTS(SELECT 1 FROM event e WHERE e.id=edges.target';
        if (from !== null) {
          sql +=
            ' AND (e.start_year IS NULL OR COALESCE(e.end_year,e.start_year)>=?)';
          args.push(from);
        }
        if (to !== null) {
          sql += ' AND (e.start_year IS NULL OR e.start_year<=?)';
          args.push(to);
        }
        sql += ')';
      }
      if (seen.size) {
        sql += ` AND id NOT IN (${[...seen].map(() => '?').join(',')})`;
        args.push(...seen);
      }
      const candidates = await this.db.rows(
          sql + ' ORDER BY subject_table,id LIMIT 301',
          args,
          signal,
        ),
        next: string[] = [];
      if (candidates.length > 300) truncated = true;
      for (const e of candidates) {
        const fresh = [...new Set<string>([e.source, e.target])].filter(
          (v) => !visited.has(v),
        );
        if (edges.length >= 300 || visited.size + fresh.length > 120) {
          truncated = true;
          continue;
        }
        fresh.forEach((v) => {
          visited.add(v);
          next.push(v);
        });
        seen.add(e.id);
        edges.push(e);
      }
      frontier = next;
    }
    return {
      center: this.graphNode(entry, entry.type),
      nodes: await this.nodes([...visited], signal),
      edges,
      truncated,
      node_limit: 120,
      edge_limit: 300,
    };
  }
}
