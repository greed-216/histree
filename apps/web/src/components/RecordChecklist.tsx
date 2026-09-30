import { useState } from "react";
import type { ContentRow, PageResult } from "@histree/shared-types";
import { useDebounced } from "../hooks/useDebounced";
import { useInfiniteResource } from "../hooks/useInfiniteResource";
import { useResource } from "../hooks/useResource";
import { InfiniteScroll } from "./InfiniteScroll";
import { LoadState } from "./Reading";

function SelectedRecords({
  ids,
  onRemove,
}: {
  ids: string[];
  onRemove: (id: string) => void;
}) {
  const selected = useResource<PageResult<ContentRow>>(
    `/editorial/nodes?ids=${ids.join(",")}`,
    true,
  );
  const names = new Map(selected.data?.items.map((n) => [n.id, n.label]));
  return (
    <>
      {ids.map((id) => (
        <li key={id}>
          {names.get(id) ?? id}
          <button
            type="button"
            className="ml-3 underline"
            onClick={() => onRemove(id)}
          >
            移除
          </button>
        </li>
      ))}
    </>
  );
}
export function RecordChecklist({
  value,
  onChange,
}: {
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [shown, setShown] = useState(20);
  const settled = useDebounced(query.trim());
  const result = useInfiniteResource<PageResult<ContentRow>>(
    `/editorial/nodes?${new URLSearchParams({ q: settled })}`,
    true,
  );
  const selectedIds = value.slice(0, shown);
  return (
    <div className="space-y-3">
      <input
        type="search"
        aria-label="搜索关联阅读条目"
        className="reading-input"
        value={query}
        maxLength={200}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索人物或事件…"
      />
      <LoadState {...result} />
      <div className="max-h-48 overflow-auto">
        <div className="grid sm:grid-cols-2 gap-2">
          {query.trim() === settled &&
            result.data?.items.map((node) => (
              <label key={node.id} className="text-sm flex gap-2">
                <input
                  type="checkbox"
                  checked={value.includes(node.id)}
                  onChange={(e) =>
                    onChange(
                      e.target.checked
                        ? [...value, node.id]
                        : value.filter((id) => id !== node.id),
                    )
                  }
                />
                {node.label} · {node.status === "published" ? "已发布" : "草稿"}
              </label>
            ))}
        </div>
        <InfiniteScroll
          {...result}
          count={result.data?.items.length}
          disabled={query.trim() !== settled}
          label="关联阅读候选"
        />
      </div>
      <p className="text-sm">已选 {value.length} 个条目（保持勾选顺序）</p>
      <div className="max-h-48 overflow-auto">
        <ol className="text-sm space-y-1">
          {Array.from(
            { length: Math.ceil(selectedIds.length / 20) },
            (_, i) => (
              <SelectedRecords
                key={i}
                ids={selectedIds.slice(i * 20, i * 20 + 20)}
                onRemove={(id) => onChange(value.filter((v) => v !== id))}
              />
            ),
          )}
        </ol>
        <InfiniteScroll
          count={selectedIds.length}
          hasMore={value.length > shown}
          loadMore={() => setShown((n) => n + 20)}
          label="已选条目"
        />
      </div>
    </div>
  );
}
