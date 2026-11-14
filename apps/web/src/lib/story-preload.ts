/** Opening: first image plus five ahead. Comics: five after the current panel. */
export function storyPreloadUrls(panels: readonly { image: { url: string } }[], page: number, ahead = 5) {
  const start = Math.max(0, page);
  return panels.slice(start, start + ahead + (page === 0 ? 1 : 0)).map(panel => panel.image.url);
}

/** Keep background downloads bounded, deduplicated, and limited to the latest window. */
export function createStoryPreloader(load: (url: string) => Promise<void>, concurrency = 2) {
  const loaded = new Set<string>(), active = new Set<string>();
  let pending: string[] = [], stopped = false;
  function pump() {
    while (!stopped && active.size < concurrency && pending.length) {
      const url = pending.shift()!;
      active.add(url);
      Promise.resolve().then(() => load(url)).then(() => { loaded.add(url); }, () => {
        // A speculative error must not block the reader; normal display can retry.
      }).finally(() => { active.delete(url); pump(); });
    }
  }
  return {
    warm(urls: readonly string[]) {
      pending = [...new Set(urls)].filter(url => !loaded.has(url) && !active.has(url));
      pump();
    },
    dispose() { stopped = true; pending = []; },
  };
}
