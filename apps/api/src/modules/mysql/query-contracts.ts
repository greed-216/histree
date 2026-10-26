export type Row = Record<string, any>;
export type MysqlResult = {
  data: any;
  error: Error | null;
  count?: number | null;
};
export interface MysqlRequest extends PromiseLike<MysqlResult> {
  abortSignal(signal: AbortSignal): MysqlRequest;
}
export const tables = [
  'person',
  'event',
  'topic',
  'source',
  'fact_claim',
  'person_relationship',
  'person_event',
  'event_causality',
];
export const uuid =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export const id = (value: unknown) => {
  if (typeof value !== 'string' || !uuid.test(value))
    throw new Error('Invalid identifier');
  return value;
};
export const integer = (
  value: unknown,
  fallback: number,
  min: number,
  max: number,
) => {
  const n = value == null ? fallback : Number(value);
  if (!Number.isInteger(n) || n < min || n > max)
    throw new Error('Invalid number');
  return n;
};
export const year = (v: unknown) => {
  if (v == null) return null;
  const n = integer(v, 0, -10000, 10000);
  if (!n) throw new Error('No year zero');
  return n;
};
export const fields: Record<string, string[]> = {
  person: ['name', 'aliases', 'era', 'faction', 'tags', 'description'],
  event: ['title', 'dynasty', 'tags', 'description'],
  topic: ['title', 'description'],
};
export const body = (table: string, alias = 'r', biography = false) => {
  const text = [
    ...(fields[table] || []),
    ...(biography ? ['biography'] : []),
  ].map((f) =>
    ['aliases', 'tags'].includes(f)
      ? `COALESCE((SELECT GROUP_CONCAT(jt.value ORDER BY jt.ordinality SEPARATOR ' ') FROM JSON_TABLE(${alias}.\`${f}\`,'$[*]' COLUMNS(ordinality FOR ORDINALITY,value TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin PATH '$')) jt),'')`
      : `COALESCE(${alias}.\`${f}\`,'')`,
  );
  return `LOWER(CONCAT_WS(' ',${text.join(',')}))`;
};
export const pattern = (s: string) =>
  `%${s.toLowerCase().replace(/[!%_]/g, (c) => '!' + c)}%`;
export function visible(table: string, alias = 'r'): string {
  if (table === 'source') return 'TRUE';
  const base = `${alias}.status='published'`;
  const parent = (t: string, column: string) =>
    `EXISTS (SELECT 1 FROM \`${t}\` v WHERE v.id=${alias}.\`${column}\` AND v.status='published')`;
  if (table === 'person_relationship')
    return `${base} AND ${parent('person', 'person_a')} AND ${parent('person', 'person_b')}`;
  if (table === 'person_event')
    return `${base} AND ${parent('person', 'person_id')} AND ${parent('event', 'event_id')}`;
  if (table === 'event_causality')
    return `${base} AND ${parent('event', 'cause_event_id')} AND ${parent('event', 'effect_event_id')}`;
  if (table === 'fact_claim')
    return `${base} AND (${['person', 'event', 'person_relationship', 'person_event', 'event_causality'].map((t) => `(${alias}.subject_table='${t}' AND EXISTS(SELECT 1 FROM \`${t}\` subject WHERE subject.id=${alias}.subject_id AND ${visible(t, 'subject')}))`).join(' OR ')})`;
  return base;
}
export const trim = (r: Row, kind?: string, length = 600) => {
  const result = { ...r };
  for (const k of [
    'biography',
    'historical_evaluation',
    'family',
    'social_relations',
    'references',
  ])
    delete result[k];
  if (['person', 'event', 'topic'].includes(kind || ''))
    result.description =
      r.description == null ? null : r.description.slice(0, length);
  if (kind === 'topic') {
    delete result.sections;
    result.section_count = r.sections?.length || 0;
  }
  if (kind === 'person' || kind === 'event') result.type = kind;
  return result;
};
