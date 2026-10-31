import type {
  EvidenceClaim,
  LibraryParagraph,
  PageResult,
  ReadingLink,
} from "@histree/shared-types";
import { useEffect, useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { FeedbackButton } from "../components/FeedbackButton";
import { InfiniteScroll } from "../components/InfiniteScroll";
import { LoadState } from "../components/Reading";
import { LibraryContents } from "../components/LibraryContents";
import { LibraryTable } from "../components/LibraryTable";
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { useResource } from "../hooks/useResource";
import { splitEvidenceNote } from "../lib/evidence";
import type {
  LibraryBook,
  LibraryReading,
  LibrarySection,
} from "../lib/library";
import { libraryPath, sectionTitle } from "../lib/library";
import "../styles/library.css";

function SearchForm({
  books,
  bookKey,
}: {
  books: LibraryBook[];
  bookKey?: string;
}) {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  return (
    <form
      className="library-search"
      role="search"
      aria-label="检索史料原文"
      onSubmit={(event) => {
        event.preventDefault();
        const fields = new FormData(event.currentTarget);
        const query = new URLSearchParams({
          q: String(fields.get("q") || "").trim(),
        });
        if (fields.get("book")) query.set("book", String(fields.get("book")));
        navigate("/library?" + query);
      }}
    >
      <label>
        <span className="sr-only">搜索范围</span>
        <select name="book" defaultValue={params.get("book") || bookKey || ""}>
          <option value="">全部史书</option>
          {books.map((book) => (
            <option key={book.book_key} value={book.book_key}>
              {book.title}
            </option>
          ))}
        </select>
      </label>
      <label className="library-search-input">
        <span className="sr-only">原文关键词</span>
        <input
          type="search"
          name="q"
          required
          minLength={2}
          maxLength={80}
          defaultValue={params.get("q") || ""}
          placeholder="输入原文中的字句，如：郦商"
        />
      </label>
      <button type="submit">搜索原文</button>
    </form>
  );
}

function Marked({ text, query }: { text: string; query?: string }) {
  if (!query || !text.includes(query)) return <>{text}</>;
  const parts = text.split(query);
  return (
    <>
      {parts.map((part, i) => (
        <span key={i}>
          {i > 0 && <mark>{query}</mark>}
          {part}
        </span>
      ))}
    </>
  );
}

type SearchResults = {
  query: string;
  page: number;
  has_more: boolean;
  items: Array<{
    id: string;
    book_key: string;
    section_id: string;
    book_title: string;
    section_title: string;
    volume: number | null;
    snippet: string;
  }>;
};
export function LibraryPage() {
  const [params, setParams] = useSearchParams();
  const books = useResource<{ items: LibraryBook[] }>("/library");
  const query = params.get("q")?.trim() || "";
  const request = new URLSearchParams({
    q: query,
    page: params.get("page") || "0",
  });
  if (params.get("book")) request.set("book", params.get("book")!);
  const results = useResource<SearchResults>(
    query.length >= 2 ? "/library/search?" + request : undefined,
  );
  const page = results.data?.page || 0;
  function changePage(next: number) {
    const updated = new URLSearchParams(params);
    updated.set("page", String(next));
    setParams(updated);
  }
  return (
    <div className="library-home">
      <header className="library-hero">
        <p className="eyebrow">循着文字，回到史书</p>
        <h1>史料库</h1>
        <p>按书、卷章阅读，也可以检索原文中的字句。</p>
      </header>
      <LoadState {...books} />
      {books.data && (
        <SearchForm key={params.toString()} books={books.data.items} />
      )}
      {query ? (
        <section className="library-results" aria-label="原文搜索结果">
          <div className="library-results-heading">
            <h2>“{query}”的原文</h2>
            <Link to="/library">返回书目</Link>
          </div>
          <p className="library-hint">
            按原文用字检索，繁简、异体字请分别尝试。
          </p>
          {query.length < 2 ? (
            <p>请输入至少两个字进行检索。</p>
          ) : (
            <LoadState {...results} />
          )}
          {results.data?.items.map((item) => (
            <Link
              className="library-result"
              key={item.id}
              to={libraryPath(
                {
                  book_key: item.book_key,
                  section_id: item.section_id,
                  paragraph_id: item.id,
                },
                undefined,
                query,
              )}
            >
              <h3>
                《{item.book_title}》 ·{" "}
                {sectionTitle({
                  id: item.section_id,
                  title: item.section_title,
                  volume: item.volume,
                })}
              </h3>
              <p>
                <Marked text={item.snippet} query={query} />
              </p>
              <span>在书中阅读 →</span>
            </Link>
          ))}
          {results.data?.items.length === 0 && (
            <p className="library-empty">
              未找到这段文字，可以缩短关键词或更换原文用字。
            </p>
          )}
          {results.data && (
            <nav className="library-pager" aria-label="搜索结果翻页">
              <button
                disabled={page === 0}
                onClick={() => changePage(page - 1)}
              >
                上一页
              </button>
              <span>第 {page + 1} 页</span>
              <button
                disabled={!results.data.has_more}
                onClick={() => changePage(page + 1)}
              >
                下一页
              </button>
            </nav>
          )}
        </section>
      ) : (
        books.data && (
          <>
            <div className="library-shelf-heading">
              <h2>选择一部史书</h2>
              <span>{books.data.items.length} 部</span>
            </div>
            <div className="library-shelf">
              {books.data.items.map((book, i) => (
                <Link
                  to={`/library/${book.book_key}`}
                  key={book.book_key}
                  className="library-book"
                >
                  <span className="library-book-order">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <h3>{book.title}</h3>
                  <p>{book.section_count} 卷章</p>
                  <span className="library-book-open">翻开阅读 →</span>
                </Link>
              ))}
            </div>
          </>
        )
      )}
    </div>
  );
}

export function LibraryBookPage() {
  const { book = "" } = useParams();
  const result = useResource<{
    book: LibraryBook;
    sections: LibrarySection[];
  }>(`/library/${book}`);
  return (
    <div className="library-home">
      <Link className="library-back" to="/library">
        ← 史料库
      </Link>
      <LoadState {...result} />
      {result.data && (
        <>
          <header className="library-hero">
            <p className="eyebrow">史书原文</p>
            <h1>{result.data.book.title}</h1>
            <p>
              {result.data.book.divisions
                ? "按本纪、表、书、世家、列传查找篇目。"
                : "选择卷章，开始阅读。"}
            </p>
          </header>
          <SearchForm books={[result.data.book]} bookKey={book} />
          <LibraryContents
            book={result.data.book}
            sections={result.data.sections}
          />
        </>
      )}
    </div>
  );
}

export function LibraryReaderPage() {
  const { book = "", section = "" } = useParams();
  const [params] = useSearchParams();
  const location = useLocation();
  const target = params.get("paragraph") || "";
  const query = params.get("q") || "";
  const claimId = params.get("claim");
  const [tableView, setTableView] = useState(true);
  const lookup = new URLSearchParams();
  if (target) lookup.set("paragraph", target);
  else if (params.has("page")) lookup.set("page", params.get("page")!);
  const result = useResource<LibraryReading>(
    `/library/${book}/sections/${section}?${lookup}`,
  );
  const contents = useResource<{
    book: LibraryBook;
    sections: LibrarySection[];
  }>(`/library/${book}`);
  const evidence = useResource<{ items: EvidenceClaim[] }>(
    claimId && /^[a-f0-9-]{36}$/i.test(claimId)
      ? `/catalog/fact_claim?claim=${claimId}`
      : undefined,
  );
  const quote = evidence.data?.items[0]
    ? (
        evidence.data.items[0].evidence ??
        splitEvidenceNote(evidence.data.items[0].note)
      ).quote.trim()
    : "";
  useEffect(() => {
    if (result.loading || !target) return;
    const paragraph = document.getElementById("paragraph-" + target);
    paragraph?.scrollIntoView({ block: "start", inline: "nearest" });
    // Keep the table's own sticky headers on screen after scrolling to a cell.
    paragraph
      ?.closest(".library-table-block")
      ?.scrollIntoView({ block: "start", inline: "nearest" });
  }, [result.loading, result.data, target, quote, location.key, tableView]);
  const data = result.data;
  const blocks: Array<
    | { kind: "table"; paragraphs: LibraryParagraph[] }
    | { kind: "paragraph"; paragraph: LibraryParagraph }
  > = [];
  for (const p of data?.paragraphs || []) {
    const previous = blocks[blocks.length - 1];
    if (tableView && p.table_row) {
      if (
        previous?.kind === "table" &&
        previous.paragraphs[0].table_row!.table_id === p.table_row.table_id
      )
        previous.paragraphs.push(p);
      else blocks.push({ kind: "table", paragraphs: [p] });
    } else blocks.push({ kind: "paragraph", paragraph: p });
  }
  const pagePath = (page: number) =>
    `/library/${book}/${section}?page=${page}${query ? "&q=" + encodeURIComponent(query) : ""}`;
  const paging = data && (
    <nav className="library-pager" aria-label="原文段落翻页">
      {data.page > 0 ? (
        <Link to={pagePath(data.page - 1)}>前 40 段</Link>
      ) : (
        <span />
      )}
      {(data.page > 0 || data.has_more) && <span>第 {data.page + 1} 页</span>}
      {data.has_more ? (
        <Link to={pagePath(data.page + 1)}>后 40 段 →</Link>
      ) : (
        <span />
      )}
    </nav>
  );
  return (
    <div className="library-reader">
      <nav className="library-breadcrumb">
        <Link to="/library">史料库</Link>
        <span>/</span>
        <Link to={`/library/${book}`}>
          {data?.book.title || contents.data?.book.title || "卷章目录"}
        </Link>
      </nav>
      <LoadState {...result} />
      {data && (
        <div className="library-reading-layout">
          <aside>
            <details className="library-contents" open>
              <summary>卷章目录</summary>
              {contents.data && (
                <LibraryContents
                  book={contents.data.book}
                  sections={contents.data.sections}
                  selected={section}
                  compact
                />
              )}
            </details>
          </aside>
          <div>
            <header className="library-reading-heading">
              <p className="eyebrow">{data.book.title}</p>
              <h1>{sectionTitle(data.section)}</h1>
              <nav className="library-volume-nav" aria-label="前后卷章">
                {data.previous ? (
                  <Link to={`/library/${book}/${data.previous.id}`}>
                    ← 上一卷章
                  </Link>
                ) : (
                  <span />
                )}
                <Link to={`/library/${book}`}>目录</Link>
                {data.next ? (
                  <Link to={`/library/${book}/${data.next.id}`}>
                    下一卷章 →
                  </Link>
                ) : (
                  <span />
                )}
              </nav>
            </header>
            {Boolean(data.section.has_issues) && (
              <p className="library-hint">本卷部分文字或图表可能缺失。</p>
            )}
            {paging}
            {data.paragraphs.some((p) => p.table_row) && (
              <div
                className="library-reading-tools"
                role="group"
                aria-label="原文显示方式"
              >
                <button
                  aria-pressed={tableView}
                  onClick={() => setTableView(true)}
                >
                  表格阅读
                </button>
                <button
                  aria-pressed={!tableView}
                  onClick={() => setTableView(false)}
                >
                  逐段原文
                </button>
              </div>
            )}
            <article className="library-original" aria-label="史料原文">
              {blocks.map((block) => {
                if (block.kind === "table")
                  return (
                    <LibraryTable
                      key={block.paragraphs[0].id}
                      paragraphs={block.paragraphs}
                      headers={
                        data.table_headers?.[
                          block.paragraphs[0].table_row!.table_id
                        ] || []
                      }
                      target={target}
                      quote={quote}
                      query={query}
                      renderLinks={(p) => (
                        <ParagraphLinks
                          book={book}
                          section={section}
                          paragraph={p.id}
                        />
                      )}
                    />
                  );
                const p = block.paragraph;
                return (
                  <div
                    key={p.id}
                    id={"paragraph-" + p.id}
                    className={`library-paragraph library-kind-${p.kind} ${target === p.id ? "is-target" : ""}`}
                  >
                    {p.kind === "editorial_notice" && (
                      <span className="library-notice-label">资料说明</span>
                    )}
                    {p.review && (
                      <details className="text-sm mb-3 text-stone-600">
                        <summary>
                          {p.review.disposition === "deferred"
                            ? "本段有待考事项"
                            : p.review.disposition === "no_new"
                              ? "已校核 · 无新增事实"
                              : "已发布事实"}
                        </summary>
                        <p>{p.review.reason}</p>
                      </details>
                    )}
                    <Marked
                      text={p.content}
                      query={
                        target === p.id && quote && p.content.includes(quote)
                          ? quote
                          : query
                      }
                    />
                    <ParagraphLinks
                      book={book}
                      section={section}
                      paragraph={p.id}
                    />
                  </div>
                );
              })}
            </article>
            {paging}
            <nav
              className="library-volume-nav library-ending"
              aria-label="继续阅读"
            >
              {data.previous ? (
                <Link to={`/library/${book}/${data.previous.id}`}>
                  ← {sectionTitle(data.previous)}
                </Link>
              ) : (
                <span />
              )}
              {data.next ? (
                <Link to={`/library/${book}/${data.next.id}`}>
                  {sectionTitle(data.next)} →
                </Link>
              ) : (
                <span>本书已到末篇</span>
              )}
            </nav>
            <FeedbackButton
              claimId={evidence.data?.items[0]?.id}
              sourceId={evidence.data?.items[0]?.source_id || undefined}
              context={`${data.book.title} · ${sectionTitle(data.section)}`}
            />
          </div>
        </div>
      )}
    </div>
  );
}

const paragraphPages = {
  merge: (a: PageResult<ReadingLink>, b: PageResult<ReadingLink>) => ({
    ...b,
    items: [
      ...new Map([...a.items, ...b.items].map((i) => [i.claim_id, i])).values(),
    ],
  }),
};
function ParagraphLinks({
  book,
  section,
  paragraph,
}: {
  book: string;
  section: string;
  paragraph: string;
}) {
  const [open, setOpen] = useState(false);
  const result = useInfiniteResource<PageResult<ReadingLink>>(
    open
      ? `/library/${book}/sections/${section}/links?paragraph=${paragraph}`
      : undefined,
    paragraphPages,
  );
  return (
    <details
      className="text-sm mt-3"
      onToggle={(e) => setOpen(e.currentTarget.open)}
    >
      <summary className="cursor-pointer text-teal-800">
        本段相关史事与人物
      </summary>
      {open && (
        <div className="mt-3">
          <LoadState {...result} />
          {result.data?.items.map((link) => (
            <p key={link.claim_id} className="mt-2">
              <Link
                className="text-teal-800"
                to={
                  link.subject_table === "person"
                    ? `/people/${link.subject_id}#evidence`
                    : link.subject_table === "event"
                      ? `/events/${link.subject_id}#evidence`
                      : `/evidence/${link.subject_table}/${link.subject_id}#claim-${link.claim_id}`
                }
              >
                {link.label} →
              </Link>
              <span className="block text-stone-500">{link.claim_text}</span>
            </p>
          ))}
          {result.data?.items.length === 0 && (
            <p>暂无可核对关联的已发布条目。</p>
          )}
          <InfiniteScroll
            {...result}
            count={result.data?.items.length}
            label="段落关联"
          />
        </div>
      )}
    </details>
  );
}
