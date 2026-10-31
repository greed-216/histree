import type { LibrarySection, LibraryLocation } from "@histree/shared-types";
export type {
  LibraryBook,
  LibrarySection,
  LibraryLocation,
  LibraryReading,
} from "@histree/shared-types";
export function sectionTitle(section: LibrarySection) {
  if (section.display_title)
    return `卷${section.volume} · ${section.display_title}`;
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
