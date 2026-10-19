import { MysqlService } from '../mysql/mysql.service';

export type GuessPerson = {
  id: string;
  name: string;
  aliases?: string[];
  courtesy_name?: string;
  era?: string;
  birth_year?: number | null;
  death_year?: number | null;
  description?: string;
  biography?: string;
  tags?: string[];
  activity?: Array<{ from: number; to: number }>;
};

// Internal game index: published people with a retrievable original-text claim only.
// Keyset reads avoid OFFSET drift and a fixed corpus-size ceiling. Each query is
// bounded to 1,000 people; the caller bounds the whole refresh with an abort signal.
export async function loadGuessCatalogue(
  db: MysqlService,
  signal: AbortSignal,
) {
  const people: GuessPerson[] = [];
  let cursor = '';
  while (true) {
    signal.throwIfAborted();
    const page = (await db.rows(
      `SELECT p.id,p.name,p.aliases,p.courtesy_name,p.era,p.birth_year,p.death_year,
        LEFT(p.description,600) description,p.tags
       FROM person p WHERE p.status='published' AND p.id>?
       AND EXISTS(SELECT 1 FROM fact_claim c JOIN source s ON s.id=c.source_id
         WHERE c.subject_table='person' AND c.subject_id=p.id AND c.status='published'
         AND c.note LIKE '原文：%' AND CHAR_LENGTH(TRIM(s.title))>0)
       ORDER BY p.id LIMIT 1000`,
      [cursor],
      signal,
    )) as GuessPerson[];
    if (!page.length) return people;
    const activity = (await db.rows(
      `SELECT DISTINCT pe.person_id,COALESCE(e.start_year,e.end_year) start_year,
        COALESCE(e.end_year,e.start_year) end_year
       FROM person_event pe JOIN event e ON e.id=pe.event_id
       WHERE pe.status='published' AND e.status='published'
       AND (e.start_year IS NOT NULL OR e.end_year IS NOT NULL)
       AND pe.person_id IN (${page.map(() => '?').join(',')})`,
      page.map((p) => p.id),
      signal,
    )) as Array<{ person_id: string; start_year: number; end_year: number }>;
    const dates = new Map<string, Array<{ from: number; to: number }>>();
    for (const row of activity) {
      const ranges = dates.get(row.person_id) || [];
      ranges.push({ from: row.start_year, to: row.end_year });
      dates.set(row.person_id, ranges);
    }
    for (const person of page) person.activity = dates.get(person.id) || [];
    people.push(...page);
    const next = page[page.length - 1].id;
    if (next <= cursor) throw new Error('Invalid game catalogue cursor');
    cursor = next;
    if (page.length < 1000) return people;
  }
}

export function matchesGuessYears(
  person: GuessPerson,
  filters: { from?: number; to?: number },
) {
  if (filters.from === undefined && filters.to === undefined) return true;
  const ranges = [...(person.activity || [])];
  // null means unknown, never year zero. A single known endpoint proves that year
  // only; event ranges stay separate so a gap is not invented as continuous life.
  const from = person.birth_year ?? person.death_year;
  const to = person.death_year ?? person.birth_year;
  if (from != null && to != null) ranges.push({ from, to });
  return ranges.some(
    (range) =>
      (filters.from === undefined || range.to >= filters.from) &&
      (filters.to === undefined || range.from <= filters.to),
  );
}
