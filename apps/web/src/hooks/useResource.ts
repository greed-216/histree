import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
export function useResource<T>(path: string) {
  const [state, setState] = useState<{
    path: string;
    revision: number;
    data?: T;
    error?: string;
    loading: boolean;
  }>({ path, revision: 0, loading: true });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    apiFetch<T>(path)
      .then((data) => {
        if (active) setState({ path, revision, data, loading: false });
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
    };
  }, [path, revision]);
  return {
    ...(state.path === path && state.revision === revision
      ? state
      : { loading: true, data: undefined, error: undefined }),
    retry: () => setRevision((v) => v + 1),
  };
}
