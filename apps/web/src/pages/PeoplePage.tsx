import {
  personReading,
  type PageResult,
  type Person,
} from "@histree/shared-types";
import { Link, useSearchParams } from "react-router-dom";
import { InfiniteScroll } from "../components/InfiniteScroll";
import { LoadState } from "../components/Reading";
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { useResource } from "../hooks/useResource";
import { formatDisplayYear } from "../lib/content";
import "../styles/directory.css";
type Facets = {
  eras: string[];
  factions: string[];
  books: Array<{ book_key: string; title: string }>;
};
export function PeoplePage() {
  const [params, setParams] = useSearchParams();
  const filters = new URLSearchParams(params);
  filters.delete("page");
  filters.delete("cursor");
  const result = useInfiniteResource<
    PageResult<Person & { sort_year?: number }>
  >("/people?" + filters);
  const facets = useResource<Facets>("/people/facets");
  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete("page");
    next.delete("cursor");
    setParams(next);
  }
  return (
    <div className="space-y-6">
      <header>
        <p className="eyebrow">沿着人物，认识时代</p>
        <h1 className="text-3xl font-serif mt-3">历史人物</h1>
      </header>
      <form
        className="reading-card people-directory-filters"
        aria-label="人物筛选"
        onSubmit={(e) => {
          e.preventDefault();
          const data = new FormData(e.currentTarget);
          update("q", String(data.get("q") ?? "").trim());
        }}
      >
        <label>
          姓名或别名
          <input
            key={params.get("q") ?? ""}
            name="q"
            type="search"
            maxLength={200}
            defaultValue={params.get("q") ?? ""}
            className="reading-input block"
          />
        </label>
        <label>
          时代
          <select
            aria-label="时代"
            value={params.get("era") ?? ""}
            onChange={(e) => update("era", e.target.value)}
            className="reading-input block"
          >
            <option value="">全部时代</option>
            {facets.data?.eras.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label>
          政权与所属
          <select
            aria-label="政权与所属"
            value={params.get("faction") ?? ""}
            onChange={(e) => update("faction", e.target.value)}
            className="reading-input block"
          >
            <option value="">全部所属</option>
            {facets.data?.factions.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        <label>
          来源书籍
          <select
            aria-label="来源书籍"
            value={params.get("book") ?? ""}
            onChange={(e) => update("book", e.target.value)}
            className="reading-input block"
          >
            <option value="">全部史书</option>
            {facets.data?.books.map((x) => (
              <option key={x.book_key} value={x.book_key}>
                {x.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          年代信息
          <select
            aria-label="年代信息"
            value={params.get("dating") ?? ""}
            onChange={(e) => update("dating", e.target.value)}
            className="reading-input block"
          >
            <option value="">不限</option>
            <option value="known">有已知年代</option>
            <option value="unknown">年代待补</option>
          </select>
        </label>
        <label>
          排列方式
          <select
            aria-label="排列方式"
            value={params.get("sort") ?? "activity"}
            onChange={(e) => update("sort", e.target.value)}
            className="reading-input block"
          >
            <option value="activity">按已知年代</option>
            <option value="name">按姓名</option>
            <option value="recent">最近录入</option>
          </select>
        </label>
        <div className="col-span-full flex justify-end items-center gap-4">
          <button className="timeline-button" type="submit">
            搜索
          </button>
          <button
            className="text-sm underline"
            type="button"
            onClick={() => setParams({})}
          >
            重置筛选
          </button>
        </div>
      </form>
      <p className="text-sm text-stone-500">
        已知年代优先采用已关联史事的最早年份，无记录时参考已知生卒年；这不表示完整生平。来源书籍筛选仅使用已核对的原文定位。待考身份保留在各人物的“身份辨析与待考”中。
      </p>
      <LoadState {...result} />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {result.data?.items.map((person) => {
          const reading = person.reading ?? personReading(person.description);
          return (
            <article className="reading-card directory-card" key={person.id}>
              <Link to={`/people/${person.id}`} className="block">
                <p className="eyebrow">
                  {person.era || "时代待补充"}
                  {person.sort_year != null
                    ? ` · ${formatDisplayYear(person.sort_year)}`
                    : ""}
                </p>
                <h2 className="text-xl font-serif mt-2">{person.name}</h2>
                <p className="text-sm text-stone-500 mt-2">
                  {[person.faction, person.native_place]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                <p className="text-sm leading-7 mt-3 line-clamp-3">
                  {reading.summary || "人物简介待整理。"}
                </p>
                <span className="text-sm text-teal-700 mt-3 block">
                  阅读人物 →
                </span>
              </Link>
              {reading.identity_notes.length > 0 && (
                <details className="border-t mt-4 pt-3 text-sm">
                  <summary className="cursor-pointer text-amber-800">
                    身份待考 · 展开辨析
                  </summary>
                  {reading.identity_notes.map((note, index) => (
                    <p key={index} className="mt-2 leading-7">
                      {note}
                    </p>
                  ))}
                </details>
              )}
            </article>
          );
        })}
      </div>
      {result.data?.items.length === 0 && (
        <p className="reading-card">
          暂无符合这些条件的已发布人物，可以调整筛选。
        </p>
      )}
      <InfiniteScroll
        {...result}
        count={result.data?.items.length}
        label="人物"
      />
    </div>
  );
}
