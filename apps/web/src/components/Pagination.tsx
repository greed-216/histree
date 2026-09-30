export function Pagination({
  page,
  hasMore,
  onPage,
  loading = false,
}: {
  page: number;
  hasMore: boolean;
  onPage: (page: number) => void;
  loading?: boolean;
}) {
  return (
    <nav aria-label="列表分页" className="flex items-center gap-4 py-3">
      <button
        className="rounded-lg border px-4 py-2 disabled:opacity-40"
        disabled={loading || page === 0}
        onClick={() => onPage(page - 1)}
      >
        上一页
      </button>
      <span className="text-sm text-stone-500">第 {page + 1} 页</span>
      <button
        className="rounded-lg border px-4 py-2 disabled:opacity-40"
        disabled={loading || !hasMore}
        onClick={() => onPage(page + 1)}
      >
        下一页
      </button>
    </nav>
  );
}
