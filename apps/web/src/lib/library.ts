export interface LibraryBook {
  book_key: string;
  title: string;
  section_count?: number;
  paragraph_count?: number;
}
export interface LibrarySection {
  id: string;
  title: string;
  volume: number | null;
  kind?: string;
  has_issues?: number;
}
export interface LibraryLocation {
  book_key: string;
  section_id: string;
  paragraph_id: string;
}
export interface LibraryReading {
  book: LibraryBook;
  section: LibrarySection;
  paragraphs: Array<{
    id: string;
    kind: string;
    content: string;
    ordinal: number;
    review?: { disposition: string; reason: string } | null;
  }>;
  coverage?: import("@histree/shared-types").ReviewCoverage[];
  page: number;
  has_more: boolean;
  previous: LibrarySection | null;
  next: LibrarySection | null;
}
export function sectionTitle(section: LibrarySection) {
  return section.volume != null && !/^卷/.test(section.title)
    ? `卷${section.volume} · ${section.title}`
    : section.title;
}
export function libraryPath(
  location: LibraryLocation,
  claim?: string,
  query?: string,
) {
  const params = new URLSearchParams({ paragraph: location.paragraph_id });
  if (claim) params.set("claim", claim);
  if (query) params.set("q", query);
  return `/library/${location.book_key}/${location.section_id}?${params}#paragraph-${location.paragraph_id}`;
}
