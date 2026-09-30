import { useState } from "react";
import type { ContentRow, PageResult } from "@histree/shared-types";
import { useResource } from "../hooks/useResource";
import { useDebounced } from "../hooks/useDebounced";
import { usePageState } from "../hooks/usePageState";
import { Pagination } from "./Pagination";
import { LoadState } from "./Reading";

export function RecordPicker({
  table,
  value,
  onChange,
  label,
  admin = true,
}: {
  table: string;
  value?: string;
  onChange: (id: string, label: string) => void;
  label: string;
  admin?: boolean;
}) {
  const [query, setQuery] = useState("");
  const settled = useDebounced(query.trim());
  const [page, setPage] = usePageState(`${table}:${settled}`);
  const root = admin ? "/editorial" : "/catalog";
  const result = useResource<PageResult<ContentRow>>(
    `${root}/${table}?${new URLSearchParams({ q: settled, page: String(page), limit: "20" })}`,
    admin,
  );
  const selected = useResource<PageResult<ContentRow>>(
    value ? `${root}/${table}?ids=${value}` : undefined,
    admin,
  );
  return (
    <div className="space-y-2">
      <p className="text-sm">
        {label}
        {value && (
          <span className="ml-2 text-teal-800">
            已选：{selected.data?.items[0]?.label ?? value}
          </span>
        )}
      </p>
      <input
        type="search"
        aria-label={`搜索${label}`}
        className="reading-input"
        maxLength={200}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={`搜索${label}…`}
      />
      <LoadState {...result} />
      {value && (
        <button
          type="button"
          className="text-xs underline"
          onClick={() => onChange("", "")}
        >
          清除选择
        </button>
      )}
      <div
        role="group"
        aria-label={`${label}候选`}
        className="flex flex-wrap gap-2 max-h-40 overflow-auto"
      >
        {query.trim() === settled &&
          result.data?.items.map((row) => (
            <button
              type="button"
              key={row.id}
              aria-pressed={value === row.id}
              className="rounded border bg-white px-2 py-1 text-sm"
              onClick={() => onChange(row.id, row.label ?? row.id)}
            >
              {row.label ?? row.id}
              {row.status === "draft" ? " · 草稿" : ""}
            </button>
          ))}
      </div>
      <Pagination
        page={page}
        hasMore={result.data?.has_more ?? false}
        loading={result.loading || query.trim() !== settled}
        onPage={setPage}
      />
    </div>
  );
}
