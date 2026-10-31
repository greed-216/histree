import type { LibraryBook, LibrarySection } from "@histree/shared-types";
import { Link } from "react-router-dom";
import { sectionTitle } from "../lib/library";

export function LibraryContents({
  book,
  sections,
  selected,
  compact = false,
}: {
  book: LibraryBook;
  sections: LibrarySection[];
  selected?: string;
  compact?: boolean;
}) {
  const divisions = book.divisions || [];
  function links(rows: LibrarySection[]) {
    return rows.map((section) => (
      <Link
        key={section.id}
        aria-current={selected === section.id ? "page" : undefined}
        to={`/library/${book.book_key}/${section.id}`}
      >
        {sectionTitle(section)}
      </Link>
    ));
  }
  if (!divisions.length)
    return (
      <nav
        className={compact ? undefined : "library-section-grid"}
        aria-label={compact ? "阅读卷章目录" : "卷章目录"}
      >
        {links(sections)}
      </nav>
    );
  return (
    <div
      className={compact ? "library-divisions-compact" : "library-divisions"}
    >
      {!compact && (
        <nav className="library-division-jumps" aria-label="篇目分类">
          {divisions.map((division) => (
            <a key={division.id} href={`#division-${division.id}`}>
              {division.title}
            </a>
          ))}
        </nav>
      )}
      <nav
        className={
          compact ? "library-preface" : "library-section-grid library-preface"
        }
        aria-label="卷前资料"
      >
        {links(sections.filter((s) => !s.division))}
      </nav>
      {divisions.map((division) => {
        const rows = sections.filter((s) => s.division === division.id);
        if (!rows.length) return null;
        if (compact)
          return (
            <details
              key={`${division.id}-${selected}`}
              open={rows.some((s) => s.id === selected)}
            >
              <summary>
                {division.title}
                <span>
                  卷{division.start_volume}—{division.end_volume}
                </span>
              </summary>
              <nav aria-label={division.title}>{links(rows)}</nav>
            </details>
          );
        return (
          <section
            key={division.id}
            id={`division-${division.id}`}
            className="library-division"
          >
            <h2>
              {division.title}
              <span>
                卷{division.start_volume}—{division.end_volume}
              </span>
            </h2>
            <nav className="library-section-grid" aria-label={division.title}>
              {links(rows)}
            </nav>
          </section>
        );
      })}
    </div>
  );
}
