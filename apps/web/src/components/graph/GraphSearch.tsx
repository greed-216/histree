import { useState } from "react";
import type { SearchResponse, Person, Event } from "@histree/shared-types";
import { useDebounced } from "../../hooks/useDebounced";
import { useResource } from "../../hooks/useResource";
import { LoadState } from "../Reading";
import { entryTitle } from "../../lib/reading";

export function GraphSearch({
  peopleOnly,
  browse,
  onOpen,
}: {
  peopleOnly: boolean;
  browse: boolean;
  onOpen: (node: Person | Event) => void;
}) {
  const [query, setQuery] = useState("");
  const settled = useDebounced(query.trim());
  const result = useResource<SearchResponse>(
    browse || settled
      ? `/search?${new URLSearchParams({ q: settled, kind: peopleOnly ? "person" : "nodes", limit: "20" })}`
      : undefined,
  );
  const pending = query.trim() !== settled;
  return (
    <div className="space-y-3">
      <input
        type="search"
        aria-label="查找图谱节点"
        className="reading-input"
        value={query}
        maxLength={200}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={
          peopleOnly ? "搜索全库人物，展开他的关系…" : "搜索全库人物或事件…"
        }
      />
      {(browse || query.trim()) && (
        <>
          {pending ? <p role="status">正在搜索…</p> : <LoadState {...result} />}
          {!pending && !result.loading && !result.error && (
            <div className="flex flex-wrap gap-2" aria-label="图谱搜索结果">
              {result.data?.items.map(
                (n) =>
                  n.type !== "topic" && (
                    <button
                      key={n.id}
                      className="rounded-lg border bg-white px-3 py-2 text-sm"
                      onClick={() => {
                        onOpen(n);
                        setQuery("");
                      }}
                    >
                      {entryTitle(n)}
                      {n.type === "event"
                        ? " · 事件"
                        : n.era
                          ? ` · ${n.era}`
                          : ""}
                    </button>
                  ),
              )}
              {result.data?.items.length === 0 && <p>没有找到匹配的条目。</p>}
              {result.data?.has_more && (
                <p className="text-sm text-stone-500">
                  仅显示前 20 项，请缩小关键词范围。
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
