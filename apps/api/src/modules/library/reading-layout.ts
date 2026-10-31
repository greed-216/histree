import { createHash } from 'node:crypto';
import type { LibraryDivision, LibraryTableRow } from '@histree/shared-types';
import shiji from '../../data/shiji-reading-layout.json';

type Paragraph = Record<string, unknown>;
type Table = {
  id: string;
  section_id: string;
  caption: string;
  columns: number;
  rows: LibraryTableRow['cells'][];
  header_paragraph_ids: string[];
};
type Layout = {
  book_key: string;
  source_version: string;
  divisions: LibraryDivision[];
  chapters: {
    section_id: string;
    volume: number;
    title: string;
    division: string;
  }[];
  tables: Record<string, Table>;
  paragraphs: Record<
    string,
    {
      content_sha256: string;
      table_id: string;
      row_index: number;
      fragments: LibraryTableRow['fragments'];
    }
  >;
};
const layout = shiji as unknown as Layout;

export function readingLayout(book: string, version: string): Layout | null {
  return book === layout.book_key && version === layout.source_version
    ? layout
    : null;
}

export function readingSection<T extends Record<string, unknown>>(
  section: T,
  data: Layout | null,
) {
  const chapter = data?.chapters.find(
    (c) => c.section_id === section.id && c.volume === section.volume,
  );
  return chapter
    ? { ...section, display_title: chapter.title, division: chapter.division }
    : section;
}

export function readingRow(
  paragraph: Paragraph,
  data: Layout | null,
  sectionId?: string,
): LibraryTableRow | undefined {
  if (typeof paragraph.id !== 'string' || typeof paragraph.content !== 'string')
    return;
  const row = data?.paragraphs[paragraph.id];
  if (
    !row ||
    paragraph.kind !== 'table_row' ||
    createHash('sha256').update(paragraph.content).digest('hex') !==
      row.content_sha256
  )
    return;
  const table = data!.tables[row.table_id];
  if (sectionId && table.section_id !== sectionId) return;
  const cells = table.rows[row.row_index];
  return {
    table_id: table.id,
    caption: table.caption,
    columns: table.columns,
    row_index: row.row_index,
    cells,
    fragments: row.fragments,
    is_header: table.header_paragraph_ids.includes(paragraph.id),
  };
}

/** A changed or missing original header disables layout for its whole table. */
export function verifiedHeaders(
  data: Layout,
  tableIds: string[],
  headers: Paragraph[],
) {
  const result: Record<
    string,
    Array<Paragraph & { table_row: LibraryTableRow }>
  > = {};
  for (const id of tableIds) {
    const table = data.tables[id];
    const rows = table.header_paragraph_ids.map((pid) =>
      headers.find((p) => p.id === pid),
    );
    if (rows.some((p) => !p || !readingRow(p, data))) continue;
    result[id] = rows.map((p) => ({ ...p!, table_row: readingRow(p!, data)! }));
  }
  return result;
}
