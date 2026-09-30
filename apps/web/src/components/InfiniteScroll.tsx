import { useEffect, useRef } from "react";

function scrollRoot(element: HTMLElement) {
  let parent = element.parentElement;
  while (parent) {
    if (/(auto|scroll)/.test(getComputedStyle(parent).overflowY)) return parent;
    parent = parent.parentElement;
  }
  return null;
}
export function InfiniteScroll({
  hasMore,
  loading,
  loadingMore = false,
  moreError,
  loadMore,
  count,
  disabled = false,
  scope = "",
  label = "列表",
}: {
  hasMore: boolean;
  loading?: boolean;
  loadingMore?: boolean;
  moreError?: string;
  loadMore: () => void;
  count?: number;
  disabled?: boolean;
  scope?: string;
  label?: string;
}) {
  const sentinel = useRef<HTMLDivElement>(null);
  const previous = useRef(scope);
  useEffect(() => {
    if (previous.current !== scope && sentinel.current) {
      scrollRoot(sentinel.current)?.scrollTo(0, 0);
      previous.current = scope;
    }
  }, [scope]);
  useEffect(() => {
    if (
      !sentinel.current ||
      !hasMore ||
      loading ||
      loadingMore ||
      moreError ||
      disabled ||
      !window.IntersectionObserver
    )
      return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) loadMore();
      },
      { root: scrollRoot(sentinel.current), rootMargin: "120px 0px" },
    );
    observer.observe(sentinel.current);
    return () => observer.disconnect();
  }, [hasMore, loading, loadingMore, moreError, disabled, loadMore, count]);
  return (
    <div
      ref={sentinel}
      data-feed={label}
      aria-label={`${label}连续加载`}
      className="w-full flex flex-wrap items-center justify-center gap-3 py-4 text-sm text-slate-500"
    >
      {!loading && count !== undefined && count > 0 && (
        <span role="status">
          已加载 {count} 条{!hasMore && " · 已全部显示"}
        </span>
      )}
      {loadingMore && <span role="status">正在加载更多…</span>}
      {moreError && <span role="alert">追加内容暂时无法加载。</span>}
      {hasMore && !loading && !loadingMore && (
        <button
          type="button"
          disabled={disabled}
          onClick={loadMore}
          className="rounded-lg border px-4 py-2 disabled:opacity-40"
        >
          {moreError ? "重试加载更多" : "加载更多"}
        </button>
      )}
    </div>
  );
}
