import { useCallback, useEffect, useRef, useState } from "react";

type ArtworkSource = {
  source: string;
  url: string;
  status: "original" | "recovering" | "blob" | "failed";
  bytes?: number;
};

/** Retry unavailable image data through a verified binary fetch, once per mount. */
export function useArtworkSource(source: string, expectedBytes: number) {
  const [replacement, setReplacement] = useState<ArtworkSource | null>(null);
  const recoverRef = useRef<(() => void) | null>(null);
  const recover = useCallback(() => recoverRef.current?.(), []);

  useEffect(() => {
    let disposed = false;
    let attempted = false;
    let objectUrl: string | undefined;
    const controller = new AbortController();
    const probe = new Image();
    async function retry() {
      if (disposed || attempted) return;
      attempted = true;
      setReplacement({ source, url: source, status: "recovering" });
      try {
        const response = await fetch(source, { cache: "reload", signal: controller.signal });
        if (!response.ok) throw new Error("Artwork request failed");
        const blob = await response.blob();
        if (!blob.type.startsWith("image/") || blob.size !== expectedBytes || !blob.size) {
          throw new Error("Artwork response differs from the published image");
        }
        if (disposed) return;
        objectUrl = URL.createObjectURL(blob);
        setReplacement({ source, url: objectUrl, status: "blob", bytes: blob.size });
      } catch {
        if (!disposed) setReplacement({ source, url: source, status: "failed" });
      }
    }
    recoverRef.current = () => { void retry(); };
    probe.onload = () => {
      if (!probe.naturalWidth || !probe.naturalHeight) void retry();
    };
    probe.onerror = () => { void retry(); };
    probe.src = source;
    return () => {
      disposed = true;
      recoverRef.current = null;
      controller.abort();
      probe.onload = null;
      probe.onerror = null;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [source, expectedBytes]);

  return {
    ...(replacement?.source === source ? replacement : { source, url: source, status: "original" as const }),
    recover,
  };
}
