export interface LibraryDivision {
  id: string;
  title: string;
  start_volume: number;
  end_volume: number;
}
export interface LibraryBook {
  book_key: string;
  title: string;
  source_version?: string;
  section_count?: number;
  paragraph_count?: number;
  divisions?: LibraryDivision[];
}
export interface LibrarySection {
  id: string;
  title: string;
  display_title?: string;
  division?: string;
  volume: number | null;
  kind?: string;
  has_issues?: number;
}
export interface LibraryLocation {
  book_key: string;
  section_id: string;
  paragraph_id: string;
}
/** Coordinates are Unicode code points in the unchanged original paragraph. */
export interface LibraryTableRow {
  table_id: string;
  caption: string;
  columns: number;
  row_index: number;
  is_header: boolean;
  cells: Array<
    [column: number, colspan: number, rowspan: number, header: boolean]
  >;
  fragments: Array<[cell: number, start: number, end: number]>;
}
export interface LibraryParagraph {
  id: string;
  kind: string;
  content: string;
  ordinal: number;
  review?: { disposition: string; reason: string } | null;
  table_row?: LibraryTableRow;
}
export interface LibraryReading {
  book: LibraryBook;
  section: LibrarySection;
  paragraphs: LibraryParagraph[];
  table_headers?: Record<string, LibraryParagraph[]>;
  page: number;
  has_more: boolean;
  previous: LibrarySection | null;
  next: LibrarySection | null;
}
