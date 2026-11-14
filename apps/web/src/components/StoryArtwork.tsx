import { useState } from "react";
import type { StoryImage } from "../lib/stories";

/** Display only the derivative needed here; full original sheets are opt-in. */
export function StoryArtwork({ artwork, alt, lazy = false }: { artwork: StoryImage; alt: string; lazy?: boolean }) {
  const [failed, setFailed] = useState<string>();
  const [attempt, setAttempt] = useState(0);
  if (failed === artwork.url) return <div className="story-image-error" role="status">
    <p>图片暂时没能翻开。</p>
    <button type="button" onClick={(event) => { event.preventDefault(); event.stopPropagation(); setAttempt(value => value + 1); setFailed(undefined); }}>再试一下</button>
  </div>;
  return <img className="story-artwork" key={`${artwork.url}:${attempt}`} src={artwork.url}
    alt={alt} width={artwork.width} height={artwork.height} loading={lazy ? "lazy" : "eager"}
    decoding="async" fetchPriority={lazy ? "low" : "high"} onError={() => setFailed(artwork.url)} />;
}
