import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";

export function uniqueRows<T extends { id: string }>(rows: T[]): T[] {
  return [...new Map(rows.map((row) => [row.id, row])).values()];
}
type Page = {
  items: Array<{ id: string }>;
  has_more: boolean;
  labels?: Record<string, string>;
};
function appendItems<T>(before: T, next: T): T {
  const a = before as Page,
    b = next as Page;
  return {
    ...b,
    items: uniqueRows([...a.items, ...b.items]),
    labels: { ...a.labels, ...b.labels },
  } as T;
}
const moreItems = <T>(data: T) => Boolean((data as Page).has_more);
type State<T> = {
  scope: string;
  data?: T;
  page: number;
  hasMore: boolean;
  loading: boolean;
  loadingMore: boolean;
  error?: string;
  moreError?: string;
};
type Request<T> = {
  state: State<T>;
  path: string;
  controller: AbortController;
  live: boolean;
  pending: boolean;
};
const cache = new Map<string, { state: State<unknown>; expires: number }>();
function initial<T>(scope: string): State<T> {
  const saved = cache.get(scope);
  if (saved && saved.expires > Date.now()) return saved.state as State<T>;
  if (saved) cache.delete(scope);
  return {
    scope,
    page: -1,
    hasMore: false,
    loading: Boolean(scope),
    loadingMore: false,
  };
}

/** Fetch one bounded batch at a time. Scope changes cancel requests and reset the feed. */
export function useInfiniteResource<T>(
  path: string | undefined,
  auth = false,
  options: {
    merge?: (before: T, next: T) => T;
    hasMore?: (data: T, page: number) => boolean;
  } = {},
) {
  const scope = path ? `${auth ? "admin" : "public"}:${path}` : "";
  const merge = options.merge ?? appendItems<T>,
    hasMore = options.hasMore ?? moreItems<T>;
  const [state, setState] = useState<State<T>>(() => initial<T>(scope));
  const current = useRef<Request<T> | null>(null);
  const request = useCallback(
    async (session: Request<T>, append: boolean) => {
      if (!session.live || session.pending) return;
      session.pending = true;
      const page = append ? session.state.page + 1 : 0;
      const url = new URL(session.path, "https://histree.local");
      url.searchParams.set("page", String(page));
      session.state = {
        ...session.state,
        loading: !session.state.data,
        loadingMore: Boolean(session.state.data),
        error: undefined,
        moreError: undefined,
      };
      setState(session.state);
      try {
        const next = await apiFetch<T>(url.pathname + url.search, {
          auth,
          signal: session.controller.signal,
        });
        if (!session.live) return;
        session.state = {
          scope: session.state.scope,
          page,
          data:
            append && session.state.data
              ? merge(session.state.data, next)
              : next,
          hasMore: hasMore(next, page),
          loading: false,
          loadingMore: false,
        };
        if (!auth) {
          cache.delete(session.state.scope);
          cache.set(session.state.scope, {
            state: session.state,
            expires: Date.now() + 300000,
          });
          if (cache.size > 10) cache.delete(cache.keys().next().value!);
        }
      } catch (e) {
        if (!session.live) return;
        const message = e instanceof Error ? e.message : "加载失败";
        session.state = {
          ...session.state,
          loading: false,
          loadingMore: false,
          ...(session.state.data ? { moreError: message } : { error: message }),
        };
      } finally {
        session.pending = false;
        if (session.live) setState(session.state);
      }
    },
    [auth, merge, hasMore],
  );
  useEffect(() => {
    if (!path) return;
    const session: Request<T> = {
      path,
      state: initial<T>(scope),
      controller: new AbortController(),
      live: true,
      pending: false,
    };
    current.current = session;
    if (!session.state.data) void request(session, false);
    return () => {
      session.live = false;
      session.controller.abort();
      const latest = current.current;
      if (latest?.state.scope === scope) {
        latest.live = false;
        latest.controller.abort();
      }
    };
  }, [path, scope, request]);
  const loadMore = useCallback(() => {
    const session = current.current;
    if (session?.state.scope === scope && session.state.hasMore)
      void request(session, true);
  }, [scope, request]);
  const retry = useCallback(() => {
    const old = current.current;
    if (!path || old?.state.scope !== scope) return;
    old.live = false;
    old.controller.abort();
    cache.delete(scope);
    const session: Request<T> = {
      path,
      state: initial<T>(scope),
      controller: new AbortController(),
      live: true,
      pending: false,
    };
    current.current = session;
    void request(session, false);
  }, [path, scope, request]);
  // A changed scope never exposes the preceding filter's data, even before the effect runs.
  return {
    ...(state.scope === scope ? state : initial<T>(scope)),
    loadMore,
    retry,
  };
}
