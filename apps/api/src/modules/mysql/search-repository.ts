import { body, integer, pattern, Row, visible, year } from './query-contracts';
import type { SqlReadPort } from './storage-port';
export class SearchRepository {
  constructor(private readonly db: SqlReadPort) {}
  async search(a: Row, signal?: AbortSignal) {
    const q = String(a.p_query || '')
        .trim()
        .toLowerCase(),
      kind = a.p_kind || 'all',
      size = integer(a.p_limit, 20, 1, 50),
      page = integer(a.p_page, 0, 0, 100000);
    if (
      q.length > 200 ||
      !['all', 'person', 'event', 'topic', 'nodes'].includes(kind)
    )
      throw new Error('Invalid search');
    const parts: string[] = [],
      params: any[] = [];
    for (const t of ['person', 'event', 'topic']) {
      if (kind !== t && kind !== 'all' && !(kind === 'nodes' && t !== 'topic'))
        continue;
      const title = t === 'person' ? 'name' : 'title';
      const alias =
        t === 'person'
          ? "WHEN EXISTS(SELECT 1 FROM JSON_TABLE(r.aliases,'$[*]' COLUMNS(alias TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt WHERE LOWER(jt.alias)=?) THEN 1 "
          : '';
      parts.push(
        `SELECT r.id,'${t}' kind,r.${title} title,CASE WHEN LOWER(r.${title})=? THEN 0 ${alias}WHEN LOWER(r.${title}) LIKE ? ESCAPE '!' THEN 2 ELSE 3 END ranking FROM \`${t}\` r WHERE ${visible(t)} AND (?='' OR ${body(t)} LIKE ? ESCAPE '!')`,
      );
      params.push(q, ...(t === 'person' ? [q] : []), pattern(q), q, pattern(q));
    }
    const matches = await this.db.rows(
      `SELECT * FROM (${parts.join(' UNION ALL ')}) matches ORDER BY ranking,title COLLATE utf8mb4_0900_bin,kind,id LIMIT ${size + 1} OFFSET ${size * page}`,
      params,
      signal,
    );
    const items: Row[] = [];
    const details = new Map<string, Row>();
    for (const table of ['person', 'event', 'topic']) {
      const ids = matches
        .slice(0, size)
        .filter((m) => m.kind === table)
        .map((m) => m.id);
      if (!ids.length) continue;
      for (const row of await this.db.rows(
        `SELECT * FROM \`${table}\` r WHERE ${visible(table)} AND id IN (${ids.map(() => '?').join(',')})`,
        ids,
        signal,
      ))
        details.set(table + ':' + row.id, row);
    }
    for (const m of matches.slice(0, size)) {
      const r = details.get(m.kind + ':' + m.id);
      if (!r) continue;
      items.push(
        m.kind === 'person'
          ? {
              id: r.id,
              type: 'person',
              name: r.name,
              era: r.era,
              description: r.description?.slice(0, 300) ?? null,
              image_url: r.image_url,
            }
          : m.kind === 'event'
            ? {
                id: r.id,
                type: 'event',
                title: r.title,
                start_year: r.start_year,
                end_year: r.end_year,
                description: r.description?.slice(0, 300) ?? null,
                image_url: r.image_url,
              }
            : {
                id: r.id,
                type: 'topic',
                title: r.title,
                slug: r.slug,
                description: r.description?.slice(0, 300) ?? null,
              },
      );
    }
    return { items, has_more: matches.length > size };
  }
  async askSearch(a: Row, signal?: AbortSignal) {
    const keywords = a.p_keywords,
      kind = a.p_kind || 'all',
      from = year(a.p_from),
      to = year(a.p_to),
      offset = integer(a.p_offset, 0, 0, 10000);
    if (
      !Array.isArray(keywords) ||
      keywords.length < 1 ||
      keywords.length > 6 ||
      keywords.some(
        (k) => typeof k !== 'string' || !k.trim() || k.trim().length > 40,
      ) ||
      !['all', 'person', 'event', 'topic'].includes(kind) ||
      (from !== null && to !== null && from > to)
    )
      throw new Error('Invalid ask search');
    const terms = keywords.map((k: string) => ({
      term: k.trim().toLowerCase(),
      pattern: pattern(k.trim()),
    }));
    const entries = ['person', 'event', 'topic']
      .filter((t) => kind === 'all' || kind === t)
      .map(
        (t) =>
          `SELECT r.id,'${t}' kind,r.${t === 'person' ? 'name' : 'title'} label,${t === 'person' ? 'r.aliases' : 'NULL'} aliases,${t === 'person' ? 'r.birth_year' : t === 'event' ? 'r.start_year' : 'NULL'} start_year,${t === 'person' ? 'r.death_year' : t === 'event' ? 'COALESCE(r.end_year,r.start_year)' : 'NULL'} end_year,r.description,${body(t, 'r', t === 'person')} body FROM \`${t}\` r WHERE ${visible(t)}`,
      );
    const parameters: any[] = [JSON.stringify(terms)];
    let date = 'TRUE';
    if (from !== null || to !== null)
      date += ' AND (e.start_year IS NOT NULL OR e.end_year IS NOT NULL)';
    if (from !== null) {
      date += ' AND COALESCE(e.end_year,e.start_year)>=?';
      parameters.push(from);
    }
    if (to !== null) {
      date += ' AND COALESCE(e.start_year,e.end_year)<=?';
      parameters.push(to);
    }
    const sql = `WITH terms AS(SELECT term COLLATE utf8mb4_0900_bin term,pattern COLLATE utf8mb4_0900_bin pattern FROM JSON_TABLE(?,'$[*]' COLUMNS(term VARCHAR(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$.term',pattern VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$.pattern')) t), entries AS(${entries.join(' UNION ALL ')}), claim_hits AS(SELECT DISTINCT c.subject_id id,c.subject_table kind,t.term FROM terms t JOIN fact_claim c ON LOWER(CONCAT_WS(' ',c.claim_text,c.note)) LIKE t.pattern ESCAPE '!' WHERE c.status='published' AND c.subject_table IN ('person','event')), scored AS(SELECT e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,LEFT(e.description,1600) description,SUM(CASE WHEN LOWER(e.label)=t.term OR EXISTS(SELECT 1 FROM JSON_TABLE(e.aliases,'$[*]' COLUMNS(alias TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt WHERE LOWER(jt.alias)=t.term) THEN 10 WHEN LOWER(e.label) LIKE t.pattern ESCAPE '!' OR EXISTS(SELECT 1 FROM JSON_TABLE(e.aliases,'$[*]' COLUMNS(alias TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt WHERE LOWER(jt.alias)=t.term) THEN 5 ELSE 1 END) score FROM entries e CROSS JOIN terms t WHERE ${date} AND (e.body LIKE t.pattern ESCAPE '!' OR EXISTS(SELECT 1 FROM claim_hits h WHERE h.id=e.id AND h.kind=e.kind AND h.term=t.term)) GROUP BY e.id,e.kind,e.label,e.aliases,e.start_year,e.end_year,e.description) SELECT * FROM scored ORDER BY score DESC,id LIMIT 13 OFFSET ${offset}`;
    const rs = await this.db.rows(sql, parameters, signal);
    return {
      items: rs.slice(0, 12).map((r) => ({
        id: r.id,
        kind: r.kind,
        label: r.label,
        aliases: r.aliases,
        startYear: r.start_year,
        endYear: r.end_year,
        description: r.description,
        score: Number(r.score),
      })),
      nextOffset: rs.length > 12 ? offset + 12 : null,
      scope:
        '仅搜索已发布条目及其已录入引文；未搜索整部史书。年代筛选排除年代未知条目。',
    };
  }
}
