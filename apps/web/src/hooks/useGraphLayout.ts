import { useEffect, useMemo, useState } from "react";
import type { GraphResponse } from "@histree/shared-types";
import { sortedEvents, type Point } from "../lib/graph";

export function useGraphLayout(
  data: GraphResponse,
  mode: "timeline" | "network",
) {
  const seed = useMemo<Record<string, Point>>(
    () =>
      mode === "timeline"
        ? Object.fromEntries([
            ...data.nodes
              .filter((n) => n.type === "person")
              .map((n, i) => [n.id, { x: 100, y: 245 + i * 94 }]),
            ...sortedEvents(data.nodes).map((n, i) => [
              n.id,
              { x: 325 + i * 220, y: 112 },
            ]),
          ])
        : Object.fromEntries(
            data.nodes.map((n, i) => [
              n.id,
              { x: 180 + (i % 4) * 260, y: 100 + Math.floor(i / 4) * 160 },
            ]),
          ),
    [data, mode],
  );
  const [computed, setComputed] = useState<{
    seed: typeof seed;
    positions: typeof seed;
  }>();
  const [failed, setFailed] = useState<typeof seed>();
  useEffect(() => {
    if (mode === "timeline" || !data.nodes.length) return;
    let worker: Worker;
    try {
      worker = new Worker(
        new URL("../workers/graphLayout.worker.ts", import.meta.url),
        { type: "module" },
      );
    } catch {
      const timer = setTimeout(() => setFailed(seed), 0);
      return () => clearTimeout(timer);
    }
    worker.onmessage = (event: MessageEvent<Record<string, Point>>) => {
      setComputed({ seed, positions: event.data });
      worker.terminate();
    };
    worker.onerror = () => {
      setFailed(seed);
      worker.terminate();
    };
    worker.postMessage({
      ids: data.nodes.map((n) => n.id),
      edges: data.edges.map((e) => ({ source: e.source, target: e.target })),
    });
    return () => {
      worker.onmessage = null;
      worker.onerror = null;
      worker.terminate();
    };
  }, [data, mode, seed]);
  return {
    positions: computed?.seed === seed ? computed.positions : seed,
    pending: mode === "network" && computed?.seed !== seed && failed !== seed,
    failed: failed === seed,
  };
}
