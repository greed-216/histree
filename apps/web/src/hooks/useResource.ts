import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
const cache = new Map<string, { data: unknown; expires: number }>();
const cacheable = (path: string) => path.startsWith('/graph-slice/') || path.startsWith('/entry/') || path === '/timeline/overview';
export function useResource<T>(path: string | undefined, auth = false) {
  const [state, setState] = useState<{
    path: string | undefined;
    revision: number;
    data?: T;
    error?: string;
    loading: boolean;
  }>({ path, revision: 0, loading: true });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!path) return;
    let active = true;
    const controller = new AbortController();
    const candidate = !auth && revision === 0 && cacheable(path) ? cache.get(path) : undefined;
    const saved = candidate && candidate.expires > Date.now() ? candidate : undefined;
    const request = saved && saved.expires > Date.now() ? Promise.resolve(saved.data as T) : apiFetch<T>(path, { auth, signal: controller.signal });
    request
      .then((data) => {
        if (active) {
          if (!auth && cacheable(path) && !saved) {
            cache.set(path, { data, expires: Date.now()+20000 });
            if(cache.size > 32)cache.delete(cache.keys().next().value!);
          }
          setState({ path, revision, data, loading: false });
        }
      })
      .catch((e) => {
        if (active)
          setState({
            path,
            revision,
            error: e instanceof Error ? e.message : "加载失败",
            loading: false,
          });
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [path, revision, auth]);
  const retry = useCallback(() => { if(path)cache.delete(path); setRevision(v=>v+1); },[path]);
  return {
    ...(!path ? { loading: false, data: undefined, error: undefined } : state.path === path && state.revision === revision
      ? state
      : { loading: true, data: undefined, error: undefined }),
    retry,
  };
}
