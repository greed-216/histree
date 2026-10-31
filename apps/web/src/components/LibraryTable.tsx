import type { LibraryParagraph } from "@histree/shared-types";
import type { ReactNode } from "react";

/** Use code points: rare CJK characters must not shift any later cell boundary. */
function Fragment({
  paragraph,
  start,
  end,
  query,
}: {
  paragraph: LibraryParagraph;
  start: number;
  end: number;
  query: string;
}) {
  const points = Array.from(paragraph.content);
  const ranges: Array<[number, number]> = [];
  if (query)
    for (let offset = 0; offset < paragraph.content.length; ) {
      const found = paragraph.content.indexOf(query, offset);
      if (found < 0) break;
      const left = Array.from(paragraph.content.slice(0, found)).length;
      const right = left + Array.from(query).length;
      if (left < end && right > start)
        ranges.push([Math.max(left, start), Math.min(right, end)]);
      offset = found + query.length;
    }
  const output: ReactNode[] = [];
  let cursor = start;
  for (const [left, right] of ranges) {
    output.push(points.slice(cursor, left).join(""));
    output.push(<mark key={left}>{points.slice(left, right).join("")}</mark>);
    cursor = right;
  }
  output.push(points.slice(cursor, end).join(""));
  return <>{output}</>;
}

export function LibraryTable({
  paragraphs,
  headers,
  target,
  quote,
  query,
  renderLinks,
}: {
  paragraphs: LibraryParagraph[];
  headers: LibraryParagraph[];
  target: string;
  quote: string;
  query: string;
  renderLinks: (paragraph: LibraryParagraph) => ReactNode;
}) {
  const table = paragraphs[0].table_row!;
  const actual = new Map(paragraphs.map((p) => [p.id, p]));
  const headerRows = headers.map((p) => actual.get(p.id) || p);
  const bodyRows = paragraphs.filter((p) => !p.table_row!.is_header);
  function rows(items: LibraryParagraph[], heading: boolean) {
    const grouped = new Map<number, LibraryParagraph[]>();
    for (const p of items) {
      const row = p.table_row!.row_index;
      grouped.set(row, [...(grouped.get(row) || []), p]);
    }
    const anchors = new Set<string>();
    const occupied = new Map<number, number>();
    return [...grouped].map(([rowIndex, parts], order) => {
      const layout = parts[0].table_row!;
      const cells: ReactNode[] = [];
      let column = 0;
      for (const [
        index,
        [at, colspan, rowspan, header],
      ] of layout.cells.entries()) {
        while (column < at) {
          if ((occupied.get(column) ?? -1) < rowIndex)
            cells.push(<td key={`empty-${column}`} />);
          column++;
        }
        const Tag = heading || header ? "th" : "td";
        cells.push(
          <Tag
            key={index}
            colSpan={colspan}
            rowSpan={rowspan}
            scope={heading ? "col" : header ? "row" : undefined}
            className={at === 0 ? "library-table-first" : undefined}
          >
            {parts.flatMap((p) =>
              p
                .table_row!.fragments.filter(([cell]) => cell === index)
                .map(([, start, end], i) => {
                  const needle =
                    target === p.id && quote && p.content.includes(quote)
                      ? quote
                      : query;
                  const found = needle ? p.content.indexOf(needle) : -1;
                  const focus =
                    found >= 0
                      ? Array.from(p.content.slice(0, found)).length
                      : p.table_row!.fragments[0][1];
                  const focusFragment = p.table_row!.fragments.find(
                    ([, , right]) => right > focus,
                  );
                  const anchor =
                    actual.has(p.id) &&
                    !anchors.has(p.id) &&
                    start === focusFragment?.[1];
                  if (anchor) anchors.add(p.id);
                  return (
                    <span
                      key={`${p.id}-${i}`}
                      id={anchor ? `paragraph-${p.id}` : undefined}
                      className={`library-table-fragment ${p.id === target ? "is-target" : ""}`}
                    >
                      <Fragment
                        paragraph={p}
                        start={start}
                        end={end}
                        query={
                          target === p.id && quote && p.content.includes(quote)
                            ? quote
                            : query
                        }
                      />
                    </span>
                  );
                }),
            )}
          </Tag>,
        );
        for (let c = at; c < at + colspan; c++)
          occupied.set(c, rowIndex + rowspan - 1);
        column = at + colspan;
      }
      while (column < table.columns) {
        if ((occupied.get(column) ?? -1) < rowIndex)
          cells.push(<td key={`empty-${column}`} />);
        column++;
      }
      if (!heading)
        cells.push(
          <td key="original" className="library-table-original">
            <details>
              <summary>
                原文与关联
                {parts.some((p) => p.review?.disposition === "deferred") && (
                  <span> · 待考</span>
                )}
              </summary>
              {parts.map((p) => (
                <div key={p.id}>
                  <pre>{p.content}</pre>
                  {p.review?.disposition === "deferred" && (
                    <p>{p.review.reason}</p>
                  )}
                  {renderLinks(p)}
                </div>
              ))}
            </details>
          </td>,
        );
      else if (order === 0)
        cells.push(
          <th key="original" rowSpan={grouped.size} scope="col">
            原文与关联
          </th>,
        );
      return (
        <tr
          key={rowIndex}
          className={
            parts.some((p) => p.id === target) ? "is-target" : undefined
          }
        >
          {cells}
        </tr>
      );
    });
  }
  return (
    <section className="library-table-block" aria-label={table.caption}>
      <p className="library-table-hint">
        左右滑动对照各列；点“原文与关联”查看逐字原文和相关条目。
      </p>
      <div
        className="library-table-scroll"
        tabIndex={0}
        role="region"
        aria-label={`${table.caption}，可横向滚动`}
      >
        <table
          className="library-table"
          style={{
            minWidth: table.columns > 2 ? `${table.columns * 10}rem` : "100%",
          }}
        >
          <caption>{table.caption}</caption>
          {headerRows.length > 0 && <thead>{rows(headerRows, true)}</thead>}
          <tbody>{rows(bodyRows, false)}</tbody>
        </table>
      </div>
    </section>
  );
}
