import { useState } from "react";
/** A filter change resets the derived page immediately, before any request. */
export function usePageState(scope: string) {
  const [state, setState] = useState({ scope, page: 0 });
  return [
    state.scope === scope ? state.page : 0,
    (page: number) => setState({ scope, page }),
  ] as const;
}
